# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Veritabanı Bağlantı Yöneticisi v3
Merkezi, Dinamik, Güvenli Bağlantı Yönetimi

Özellikler:
- Veritabanından bağlantı ayarları okuma
- Şifre encryption/decryption (double layer)
- Dinamik connection pool yönetimi
- Fallback mekanizması (config.py → .env → hardcoded)
- Health check ve monitoring
- Graceful degradation

Kullanım:
    from core.database_manager import db_manager
    
    # ERP bağlantısı
    with db_manager.get_connection('ERP') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ...")
    
    # PLC bağlantısı (hata durumunda graceful)
    try:
        with db_manager.get_connection('PLC') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM MDURUM")
    except ConnectionError:
        # PLC bağlanamadı, manuel moda geç
        logging.warning("PLC bağlantısı yok, manuel mod aktif")

Tarih: 2026-01-23
"""

import pyodbc
import threading
import logging
import time
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from queue import Queue, Empty
from contextlib import contextmanager

# Harici config manager (ÖNCELİKLİ)
try:
    from core.external_config import config_manager as ext_config_manager, _UDL_FILE, parse_udl_file
    EXTERNAL_CONFIG_AVAILABLE = True
except ImportError:
    try:
        from external_config import config_manager as ext_config_manager, _UDL_FILE, parse_udl_file
        EXTERNAL_CONFIG_AVAILABLE = True
    except ImportError:
        EXTERNAL_CONFIG_AVAILABLE = False
        ext_config_manager = None
        _UDL_FILE = None
        parse_udl_file = None

# Fallback için mevcut modüller (config.py)
try:
    from config import DB_CONFIG
except ImportError:
    DB_CONFIG = None

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# ŞİFRE YÖNETİCİSİ (Sadece UI Maskeleme İçin)
# =============================================================================

class PasswordManager:
    """
    Basitleştirilmiş şifre yöneticisi
    - Veritabanında plain text saklama
    - Sadece UI'da maskeleme (*** gösterimi)
    """
    
    def __init__(self):
        """Artık şifreleme yok, sadece placeholder"""
        pass
    
    def mask_password(self, password: str) -> str:
        """UI için şifreyi maskele"""
        if not password:
            return ""
        return "•" * len(password)


# =============================================================================
# CONNECTION POOL (Mevcut yapı - değişmedi)
# =============================================================================

class ConnectionPool:
    """Thread-safe Connection Pool - Önceki implementasyon"""
    
    def __init__(self, conn_string: str, max_connections: int = 20, timeout: int = 30):
        self._conn_string = conn_string
        self._pool: Queue = Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._created_count = 0
        self._max_connections = max_connections
        self._timeout = timeout
        
        self._stats = {
            'total_requests': 0,
            'pool_hits': 0,
            'new_connections': 0,
            'failed_connections': 0,
            'recovered_connections': 0
        }
    
    def _create_connection(self) -> pyodbc.Connection:
        """Yeni connection oluştur"""
        try:
            conn = pyodbc.connect(
                self._conn_string,
                timeout=self._timeout,
                autocommit=False
            )
            return conn
        except Exception as e:
            self._stats['failed_connections'] += 1
            raise ConnectionError(f"Bağlantı kurulamadı: {e}")
    
    def _is_connection_valid(self, conn: pyodbc.Connection) -> bool:
        """Connection geçerli mi?"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception:
            return False
    
    def get_connection(self) -> pyodbc.Connection:
        """Pool'dan connection al"""
        self._stats['total_requests'] += 1
        
        # Pool'dan dene
        try:
            conn = self._pool.get_nowait()
            if self._is_connection_valid(conn):
                self._stats['pool_hits'] += 1
                return conn
            else:
                self._stats['recovered_connections'] += 1
                with self._lock:
                    self._created_count -= 1
                try:
                    conn.close()
                except Exception:
                    pass
        except Empty:
            pass
        
        # Yeni oluştur
        with self._lock:
            if self._created_count < self._max_connections:
                self._created_count += 1
                self._stats['new_connections'] += 1
                try:
                    return self._create_connection()
                except Exception:
                    self._created_count -= 1
                    raise
        
        # Bekle
        try:
            conn = self._pool.get(timeout=self._timeout)
            if self._is_connection_valid(conn):
                self._stats['pool_hits'] += 1
                return conn
            else:
                try:
                    conn.close()
                except Exception:
                    pass
                return self._create_connection()
        except Empty:
            raise TimeoutError(f"Connection pool timeout ({self._timeout}s)")
    
    def return_connection(self, conn: pyodbc.Connection) -> None:
        """Connection'ı pool'a geri ver"""
        if conn is None:
            return
        
        try:
            try:
                conn.rollback()
            except Exception:
                pass
            
            if self._is_connection_valid(conn):
                try:
                    self._pool.put_nowait(conn)
                except Exception:
                    try:
                        conn.close()
                    except Exception:
                        pass
                    with self._lock:
                        self._created_count -= 1
            else:
                try:
                    conn.close()
                except Exception:
                    pass
                with self._lock:
                    self._created_count -= 1
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            with self._lock:
                self._created_count -= 1
    
    def get_stats(self) -> dict:
        """İstatistikler"""
        return {
            **self._stats,
            'pool_size': self._pool.qsize(),
            'active_connections': self._created_count - self._pool.qsize(),
            'total_connections': self._created_count,
            'max_connections': self._max_connections
        }
    
    def close_all(self) -> None:
        """Tüm connection'ları kapat"""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Exception:
                pass
        with self._lock:
            self._created_count = 0


# =============================================================================
# POOLED CONNECTION WRAPPER
# =============================================================================

class PooledConnection:
    """Pool'a otomatik dönen connection wrapper"""
    
    def __init__(self, pool: ConnectionPool, conn: pyodbc.Connection):
        self._pool = pool
        self._conn = conn
        self._closed = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._pool.return_connection(self._conn)
    
    def cursor(self):
        return self._conn.cursor()
    
    def commit(self) -> None:
        self._conn.commit()
    
    def rollback(self) -> None:
        self._conn.rollback()
    
    def execute(self, sql: str, params=None):
        cursor = self._conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor
    
    def __getattr__(self, name):
        return getattr(self._conn, name)


# =============================================================================
# DATABASE CONNECTION MANAGER (YENİ!)
# =============================================================================

class DatabaseConnectionManager:
    """
    Merkezi Veritabanı Bağlantı Yöneticisi
    
    Bootstrap Stratejisi:
    1. İlk çalıştırmada config.py kullan
    2. Veritabanına bağlan ve ayarları oku
    3. Sonraki çalıştırmalarda veritabanından oku
    4. Veritabanı bağlanamazsa config.py fallback
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize manager"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._pools: Dict[str, ConnectionPool] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._password_manager = PasswordManager()
        self._bootstrap_conn = None
        self._last_config_reload = None
        self._config_cache_ttl = 300  # 5 dakika
        
        logger.info("DatabaseConnectionManager başlatılıyor...")
        self._bootstrap()
    
    def _bootstrap(self) -> None:
        """
        Bootstrap süreci:
        1. config.py ile ilk bağlantı
        2. Veritabanından ayarları yükle
        3. Pool'ları oluştur
        """
        try:
            # Step 1: config.py ile bootstrap connection
            logger.info("Bootstrap: config.py ile ilk bağlantı kuruluyor...")
            self._create_bootstrap_connection()
            
            # Step 2: Veritabanından ayarları yükle
            logger.info("Bootstrap: Veritabanından bağlantı ayarları yükleniyor...")
            self._load_configs_from_db()
            
            # Step 3: Pool'ları oluştur
            logger.info("Bootstrap: Connection pool'ları oluşturuluyor...")
            self._initialize_pools()
            
            logger.info("✓ DatabaseConnectionManager başarıyla başlatıldı")
            logger.info(f"✓ Yüklenen bağlantılar: {list(self._configs.keys())}")
            
        except Exception as e:
            logger.error(f"✗ Bootstrap hatası: {e}")
            logger.warning("Fallback: config.py kullanılacak")
            self._fallback_to_config()
    
    def _create_bootstrap_connection(self) -> None:
        """
        Ilk baglanti icin config kaynaklarini kullan
        Oncelik: 1) Harici config (C:/NEXOR/config.json)
                 2) config.py
        """
        conn_str = None
        timeout = 10
        
        # 1. Harici config'i dene (ÖNCELİKLİ)
        if EXTERNAL_CONFIG_AVAILABLE and ext_config_manager:
            if ext_config_manager.config_exists() and not ext_config_manager.needs_setup():
                try:
                    conn_str = ext_config_manager.get_connection_string()
                    timeout = ext_config_manager.get('database.timeout', 10)
                    logger.info("Bootstrap: Harici config kullaniliyor (C:/NEXOR/config.json)")
                except Exception as e:
                    logger.warning(f"Harici config okunamadı: {e}")
                    conn_str = None
        
        # 2. config.py'ye fallback
        if conn_str is None:
            if DB_CONFIG is None:
                raise RuntimeError("Hicbir config kaynagi bulunamadi! config.py veya C:/NEXOR/config.json gerekli.")
            
            logger.info("Bootstrap: config.py kullanılıyor")
            
            if DB_CONFIG.get('trusted_connection'):
                conn_str = (
                    f"DRIVER={{{DB_CONFIG['driver']}}};"
                    f"SERVER={DB_CONFIG['server']};"
                    f"DATABASE={DB_CONFIG['database']};"
                    "Trusted_Connection=yes;"
                    "Encrypt=no;TrustServerCertificate=yes;"
                )
            else:
                conn_str = (
                    f"DRIVER={{{DB_CONFIG['driver']}}};"
                    f"SERVER={DB_CONFIG['server']};"
                    f"DATABASE={DB_CONFIG['database']};"
                    f"UID={DB_CONFIG['user']};"
                    f"PWD={DB_CONFIG['password']};"
                    "Encrypt=no;TrustServerCertificate=yes;"
                )
            timeout = DB_CONFIG.get('timeout', 10)
        
        try:
            self._bootstrap_conn = pyodbc.connect(conn_str, timeout=timeout)
            logger.info("✓ Bootstrap connection başarılı")
        except Exception as e:
            raise ConnectionError(f"Bootstrap bağlantısı kurulamadı: {e}")
    
    def _load_configs_from_db(self) -> None:
        """Veritabanından bağlantı ayarlarını yükle"""
        if not self._bootstrap_conn:
            raise RuntimeError("Bootstrap connection yok!")
        
        try:
            cursor = self._bootstrap_conn.cursor()
            
            # Aktif bağlantıları çek (şifre plain text)
            query = """
            SELECT 
                baglanti_adi,
                aciklama,
                baglanti_tipi,
                server,
                database_name,
                kullanici_adi,
                sifre,
                driver,
                timeout,
                max_connections,
                connection_string_extra,
                test_query
            FROM sistem_veritabani_baglantilari
            WHERE aktif = 1 
              AND silinme_tarihi IS NULL
            ORDER BY baglanti_adi
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                logger.warning("Veritabanında aktif bağlantı bulunamadı!")
                return
            
            for row in rows:
                baglanti_adi = row.baglanti_adi
                
                config = {
                    'name': baglanti_adi,
                    'description': row.aciklama,
                    'type': row.baglanti_tipi,
                    'server': row.server,
                    'database': row.database_name,
                    'user': row.kullanici_adi,
                    'password': row.sifre,  # Plain text
                    'driver': row.driver,
                    'timeout': row.timeout or 10,
                    'max_connections': row.max_connections or 20,
                    'extra_params': row.connection_string_extra or '',
                    'test_query': row.test_query or 'SELECT 1'
                }
                
                self._configs[baglanti_adi] = config
                logger.info(f"  ✓ {baglanti_adi}: {row.server}/{row.database_name}")
            
            cursor.close()

            # ERP baglantisini harici kaynaklardan override et
            # Oncelik: 1) UDL dosyasi  2) config.json (external_config)
            if 'ERP' in self._configs:
                override_applied = False
                old_server = self._configs['ERP']['server']

                # 1. UDL dosyasi
                if _UDL_FILE and parse_udl_file:
                    udl_data = parse_udl_file(_UDL_FILE)
                    if udl_data:
                        self._configs['ERP']['server'] = udl_data['server']
                        self._configs['ERP']['database'] = udl_data['database']
                        if udl_data.get('user'):
                            self._configs['ERP']['user'] = udl_data['user']
                            self._configs['ERP']['password'] = udl_data['password']
                        override_applied = True
                        logger.info(f"  UDL override ERP: {old_server} -> {udl_data['server']}")

                # 2. config.json (external_config) - UDL yoksa bunu kullan
                if not override_applied and EXTERNAL_CONFIG_AVAILABLE and ext_config_manager:
                    try:
                        ext_db = ext_config_manager.get_db_config()
                        if ext_db.get('server'):
                            self._configs['ERP']['server'] = ext_db['server']
                            self._configs['ERP']['database'] = ext_db['database']
                            if ext_db.get('user'):
                                self._configs['ERP']['user'] = ext_db['user']
                                self._configs['ERP']['password'] = ext_db.get('password', '')
                            override_applied = True
                            logger.info(f"  Config override ERP: {old_server} -> {ext_db['server']}")
                    except Exception as e:
                        logger.warning(f"  Config override hatasi: {e}")

            self._last_config_reload = datetime.now()

        except Exception as e:
            logger.error(f"Veritabanından config yükleme hatası: {e}")
            raise
    
    def _initialize_pools(self) -> None:
        """Her bağlantı için pool oluştur"""
        for name, config in self._configs.items():
            try:
                conn_str = self._build_connection_string(config)
                pool = ConnectionPool(
                    conn_str,  # İlk parametre (positional)
                    config['max_connections'],
                    config['timeout']
                )
                self._pools[name] = pool
                logger.info(f"  ✓ Pool oluşturuldu: {name} (max: {config['max_connections']})")
            except Exception as e:
                logger.error(f"  ✗ Pool oluşturma hatası [{name}]: {e}")
    
    def _build_connection_string(self, config: Dict[str, Any]) -> str:
        """Connection string oluştur (Windows Auth desteği ile)"""
        
        # Trusted Connection (Windows Auth) kontrolü
        if config.get('trusted_connection'):
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                "Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"UID={config['user']};"
                f"PWD={config['password']};"
            )
        
        # Extra parametreler
        if config.get('extra_params'):
            conn_str += config['extra_params']
        else:
            conn_str += "Encrypt=no;TrustServerCertificate=yes;"
        
        return conn_str
    
    def _fallback_to_config(self) -> None:
        """
        Fallback: Harici config veya config.py kullan
        Oncelik: 1) Harici config (C:/NEXOR/config.json)
                 2) config.py
        """
        config_source = None
        db_config = None
        
        # 1. Harici config'i dene
        if EXTERNAL_CONFIG_AVAILABLE and ext_config_manager:
            if ext_config_manager.config_exists() and not ext_config_manager.needs_setup():
                try:
                    db_config = ext_config_manager.get_db_config()
                    config_source = "harici config (C:/NEXOR/config.json)"
                    logger.info(f"Fallback: Harici config okundu: {db_config.get('server')}/{db_config.get('database')}")
                except Exception as e:
                    logger.warning(f"Harici config fallback hatası: {e}")
                    db_config = None
        
        # 2. config.py'ye fallback
        if db_config is None and DB_CONFIG:
            db_config = {
                'server': DB_CONFIG['server'],
                'database': DB_CONFIG['database'],
                'user': DB_CONFIG.get('user', ''),
                'password': DB_CONFIG.get('password', ''),
                'driver': DB_CONFIG['driver'],
                'timeout': DB_CONFIG.get('timeout', 10),
                'max_connections': 20,
                'trusted_connection': DB_CONFIG.get('trusted_connection', False)
            }
            config_source = "config.py"
        
        if db_config:
            try:
                logger.info(f"Fallback: {config_source} bağlantısı oluşturuluyor...")
                
                self._configs['ERP'] = {
                    'name': 'ERP',
                    'description': f'Fallback from {config_source}',
                    'type': 'SQLSERVER',
                    'server': db_config['server'],
                    'database': db_config['database'],
                    'user': db_config.get('user', ''),
                    'password': db_config.get('password', ''),
                    'driver': db_config['driver'],
                    'timeout': db_config.get('timeout', 10),
                    'max_connections': db_config.get('max_connections', 20),
                    'extra_params': 'Encrypt=no;TrustServerCertificate=yes;',
                    'test_query': 'SELECT 1',
                    'trusted_connection': db_config.get('trusted_connection', False)
                }
                
                conn_str = self._build_connection_string(self._configs['ERP'])
                logger.info(f"Fallback: Connection string oluşturuldu (server: {db_config['server']})")
                
                self._pools['ERP'] = ConnectionPool(conn_str, db_config.get('max_connections', 20), db_config.get('timeout', 10))
                self._last_config_reload = datetime.now()  # Fallback için de set et
                logger.info("✓ Fallback ERP pool oluşturuldu")
            except Exception as e:
                logger.error(f"✗ Fallback pool oluşturma hatası: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.error("Hiçbir config kaynağı bulunamadı!")
    
    def get_connection(self, baglanti_adi: str = 'ERP') -> PooledConnection:
        """
        Belirtilen veritabanına bağlantı döndür
        
        Args:
            baglanti_adi: 'ERP', 'PLC', 'ZIRVE' vs
        
        Returns:
            PooledConnection
        
        Raises:
            ConnectionError: Bağlantı kurulamazsa
        """
        # Config cache refresh kontrolü
        self._check_config_refresh()
        
        # Pool var mı?
        if baglanti_adi not in self._pools:
            raise ConnectionError(
                f"Bağlantı tanımlı değil: {baglanti_adi}. "
                f"Mevcut: {list(self._pools.keys())}"
            )
        
        pool = self._pools[baglanti_adi]
        
        try:
            conn = pool.get_connection()
            return PooledConnection(pool, conn)
        except Exception as e:
            logger.error(f"Bağlantı hatası [{baglanti_adi}]: {e}")
            
            # PLC için graceful degradation
            if baglanti_adi == 'PLC':
                logger.warning("PLC bağlantısı başarısız, manuel mod aktif")
            
            raise ConnectionError(f"[{baglanti_adi}] bağlantı kurulamadı: {e}")
    
    def test_connection(self, baglanti_adi: str) -> Dict[str, Any]:
        """
        Bağlantıyı test et
        
        Returns:
            {
                'success': bool,
                'message': str,
                'duration_ms': int,
                'error': str (opsiyonel)
            }
        """
        start_time = time.time()
        result = {
            'success': False,
            'message': '',
            'duration_ms': 0,
            'error': None
        }
        
        try:
            with self.get_connection(baglanti_adi) as conn:
                config = self._configs.get(baglanti_adi, {})
                test_query = config.get('test_query', 'SELECT 1')
                
                cursor = conn.cursor()
                cursor.execute(test_query)
                cursor.fetchone()
                cursor.close()
                
                result['success'] = True
                result['message'] = 'Bağlantı başarılı'
                
        except Exception as e:
            result['success'] = False
            result['message'] = 'Bağlantı başarısız'
            result['error'] = str(e)
            logger.error(f"Test hatası [{baglanti_adi}]: {e}")
        
        finally:
            result['duration_ms'] = int((time.time() - start_time) * 1000)
        
        # Test sonucunu veritabanına kaydet
        self._save_test_result(baglanti_adi, result)
        
        return result
    
    def _save_test_result(self, baglanti_adi: str, result: Dict[str, Any]) -> None:
        """Test sonucunu veritabanına kaydet"""
        try:
            if not self._bootstrap_conn:
                return
            
            cursor = self._bootstrap_conn.cursor()
            query = """
            UPDATE sistem_veritabani_baglantilari
            SET 
                son_test_tarihi = GETDATE(),
                son_test_basarili = ?,
                son_test_mesaji = ?,
                son_test_suresi_ms = ?
            WHERE baglanti_adi = ?
            """
            
            cursor.execute(query, (
                result['success'],
                result['message'],
                result['duration_ms'],
                baglanti_adi
            ))
            self._bootstrap_conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Test sonucu kaydetme hatası: {e}")
    
    def _check_config_refresh(self) -> None:
        """Config cache TTL kontrolü"""
        if self._last_config_reload:
            elapsed = (datetime.now() - self._last_config_reload).total_seconds()
            if elapsed > self._config_cache_ttl:
                logger.info("Config cache expired, yeniden yükleniyor...")
                try:
                    self.reload_configs()
                except Exception as e:
                    logger.error(f"Config reload hatası: {e}")
                    # Hata durumunda da timestamp güncelle - sonsuz döngüyü önle
                    # Bir sonraki deneme TTL kadar bekleyecek
                    self._last_config_reload = datetime.now()
    
    def reload_configs(self) -> None:
        """Ayarları yeniden yükle (runtime'da)"""
        logger.info("Bağlantı ayarları yeniden yükleniyor...")

        try:
            # Bootstrap bağlantısı kopmuş olabilir, kontrol et
            if self._bootstrap_conn:
                try:
                    cursor = self._bootstrap_conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    cursor.close()
                except Exception:
                    logger.warning("Bootstrap bağlantısı kopmuş, yeniden kuruluyor...")
                    try:
                        self._bootstrap_conn.close()
                    except Exception:
                        pass
                    self._bootstrap_conn = None
                    self._create_bootstrap_connection()

            # Yeni config'leri yükle
            old_configs = self._configs.copy()
            self._configs.clear()
            self._load_configs_from_db()

            # Değişen pool'ları güncelle
            for name in list(self._pools.keys()):
                if name not in self._configs:
                    # Artık yok, kapat
                    logger.info(f"Pool kapatılıyor: {name}")
                    self._pools[name].close_all()
                    del self._pools[name]

            # Yeni pool'lar oluştur
            for name, config in self._configs.items():
                if name not in self._pools:
                    logger.info(f"Yeni pool oluşturuluyor: {name}")
                    conn_str = self._build_connection_string(config)
                    self._pools[name] = ConnectionPool(
                        conn_str,
                        config['max_connections'],
                        config['timeout']
                    )

            logger.info("✓ Ayarlar yeniden yüklendi")

        except Exception as e:
            logger.error(f"Reload hatası: {e}")
            # Eski config'e dön
            if old_configs:
                self._configs = old_configs
    
    def get_available_connections(self) -> list:
        """Mevcut bağlantı listesi"""
        return list(self._configs.keys())
    
    def get_connection_info(self, baglanti_adi: str) -> Optional[Dict[str, Any]]:
        """Bağlantı bilgisi (şifresiz)"""
        config = self._configs.get(baglanti_adi)
        if not config:
            return None
        
        return {
            'name': config['name'],
            'description': config['description'],
            'server': config['server'],
            'database': config['database'],
            'driver': config['driver'],
            'timeout': config['timeout'],
            'max_connections': config['max_connections']
        }
    
    def get_pool_stats(self, baglanti_adi: str = None) -> Dict[str, Any]:
        """Pool istatistikleri"""
        if baglanti_adi:
            pool = self._pools.get(baglanti_adi)
            return pool.get_stats() if pool else {}
        
        return {name: pool.get_stats() for name, pool in self._pools.items()}
    
    def close_all(self) -> None:
        """Tüm pool'ları kapat"""
        logger.info("Tüm connection pool'ları kapatılıyor...")
        
        for name, pool in self._pools.items():
            try:
                pool.close_all()
                logger.info(f"  ✓ {name} pool kapatıldı")
            except Exception as e:
                logger.error(f"  ✗ {name} pool kapatma hatası: {e}")
        
        self._pools.clear()
        
        if self._bootstrap_conn:
            try:
                self._bootstrap_conn.close()
                logger.info("  ✓ Bootstrap connection kapatıldı")
            except Exception:
                pass


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

# Singleton instance
db_manager = DatabaseConnectionManager()


# =============================================================================
# BACKWARD COMPATIBILITY (Geriye Uyumlu API)
# =============================================================================

def get_db_connection() -> PooledConnection:
    """
    Eski API - ERP bağlantısı döndür
    Geriye uyumluluk için
    """
    return db_manager.get_connection('ERP')


def get_plc_connection() -> PooledConnection:
    """
    Eski API - PLC bağlantısı döndür
    Geriye uyumluluk için
    """
    return db_manager.get_connection('PLC')


def execute_query(query: str, params: list = None) -> list:
    """Eski API - ERP'de SELECT çalıştır"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


def execute_non_query(query: str, params: list = None) -> int:
    """Eski API - ERP'de INSERT/UPDATE/DELETE"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rowcount = cursor.rowcount
        conn.commit()
        return rowcount


def execute_plc_query(query: str, params: list = None) -> list:
    """Eski API - PLC'de SELECT"""
    with get_plc_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


def get_pool_stats() -> dict:
    """Eski API - Pool istatistikleri"""
    return db_manager.get_pool_stats()


def close_all_pools() -> None:
    """Eski API - Tüm pool'ları kapat"""
    db_manager.close_all()


# =============================================================================
# TRANSACTION HELPER
# =============================================================================

@contextmanager
def transaction(baglanti_adi: str = 'ERP'):
    """
    Transaction context manager
    
    Kullanım:
        with transaction('ERP') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT ...")
            # Otomatik commit/rollback
    """
    conn = db_manager.get_connection(baglanti_adi)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# CLEANUP
# =============================================================================

import atexit
atexit.register(close_all_pools)


# =============================================================================
# TEST & DEBUG
# =============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("DATABASE CONNECTION MANAGER - TEST")
    print("=" * 80)
    
    print("\n1. Mevcut Bağlantılar:")
    for name in db_manager.get_available_connections():
        info = db_manager.get_connection_info(name)
        print(f"   {name}: {info['server']}/{info['database']}")
    
    print("\n2. ERP Bağlantı Testi:")
    result = db_manager.test_connection('ERP')
    print(f"   Sonuç: {'✓' if result['success'] else '✗'} {result['message']}")
    print(f"   Süre: {result['duration_ms']}ms")
    
    print("\n3. PLC Bağlantı Testi:")
    try:
        result = db_manager.test_connection('PLC')
        print(f"   Sonuç: {'✓' if result['success'] else '✗'} {result['message']}")
        print(f"   Süre: {result['duration_ms']}ms")
    except Exception as e:
        print(f"   Hata: {e}")
    
    print("\n4. Pool İstatistikleri:")
    stats = db_manager.get_pool_stats()
    for name, stat in stats.items():
        print(f"   {name}:")
        print(f"      Total requests: {stat['total_requests']}")
        print(f"      Pool hits: {stat['pool_hits']}")
        print(f"      Active connections: {stat['active_connections']}")
    
    print("\n" + "=" * 80)
