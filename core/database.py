# -*- coding: utf-8 -*-
"""
ATMO LOGIC ERP - Veritabanı Bağlantısı v3
Merkezi, Dinamik, Veritabanı-Tabanlı Bağlantı Yönetimi

⚠️ ÖNEMLİ: Bu dosya artık database_manager.py'yi kullanıyor!
Bağlantı bilgileri veritabanından okunuyor: sistem_veritabani_baglantilari

Değişiklikler v3:
- Merkezi DatabaseConnectionManager (database_manager.py)
- Veritabanı tablosundan bağlantı yönetimi
- Şifre encryption (double layer)
- Graceful fallback (config.py → veritabanı)
- Health check & monitoring
- GERİYE UYUMLU: Tüm eski kodlar çalışmaya devam eder!

Kullanım:
    # ESKİ API (hala çalışır) - BACKWARD COMPATIBLE
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ...")
    
    # YENİ API (önerilen)
    from core.database_manager import db_manager
    
    with db_manager.get_connection('ERP') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ...")
    
    with db_manager.get_connection('PLC') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM MDURUM")
    
    # Bağlantı testi
    result = db_manager.test_connection('ERP')
    if result['success']:
        print("Bağlantı OK")

Migration:
    1. SQL script çalıştır: database_migrations/001_create_baglanti_yonetimi.sql
    2. Bu dosya otomatik olarak yeni sistemi kullanır
    3. Eski kodlar değişiklik gerektirmez

Tarih: 2026-01-23
"""
import pyodbc
import threading
import time
from queue import Queue, Empty
from contextlib import contextmanager
from typing import Optional

# YENİ: Merkezi database manager
try:
    from core.database_manager import (
        db_manager,
        PasswordManager,
        ConnectionPool,
        PooledConnection,
        transaction as new_transaction
    )
    MANAGER_AVAILABLE = True
except ImportError:
    MANAGER_AVAILABLE = False
    print("⚠️ WARNING: database_manager.py bulunamadı, fallback mode aktif")

# Fallback için eski config
try:
    from config import DB_CONFIG
except ImportError:
    DB_CONFIG = None


# =============================================================================
# CONNECTION POOL
# =============================================================================

class ConnectionPool:
    """
    Thread-safe Connection Pool
    
    - Maksimum connection sayısı sınırlı
    - Bozuk connection'ları otomatik yeniler
    - Bekleyen istekler için timeout
    """
    
    def __init__(self, max_connections: int = 20, connection_timeout: int = 30, custom_config: dict = None):
        """
        Args:
            max_connections: Maksimum connection sayısı (default: 20)
            connection_timeout: Connection beklerken timeout süresi (saniye)
            custom_config: Özel bağlantı ayarları (PLC için)
        """
        self._pool: Queue = Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._created_count = 0
        self._max_connections = max_connections
        self._connection_timeout = connection_timeout
        self._custom_config = custom_config
        self._conn_str = self._build_connection_string()
        
        # İstatistikler
        self._stats = {
            'total_requests': 0,
            'pool_hits': 0,
            'new_connections': 0,
            'failed_connections': 0,
            'recovered_connections': 0
        }
    
    def _build_connection_string(self) -> str:
        """Connection string oluştur"""
        config = self._custom_config if self._custom_config else DB_CONFIG
        return (
            f"DRIVER={{{config['driver']}}};"
            f"SERVER={config['server']};"
            f"DATABASE={config['database']};"
            f"UID={config['user']};PWD={config['password']};"
            "Encrypt=no;TrustServerCertificate=yes;"
        )
    
    def _create_connection(self) -> pyodbc.Connection:
        """Yeni connection oluştur"""
        config = self._custom_config if self._custom_config else DB_CONFIG
        try:
            conn = pyodbc.connect(
                self._conn_str, 
                timeout=config.get('timeout', 10),
                autocommit=False
            )
            return conn
        except Exception as e:
            self._stats['failed_connections'] += 1
            raise ConnectionError(f"Veritabanı bağlantısı kurulamadı: {e}")
    
    def _is_connection_valid(self, conn: pyodbc.Connection) -> bool:
        """Connection'ın hala geçerli olup olmadığını kontrol et"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception:
            return False
    
    def get_connection(self) -> pyodbc.Connection:
        """
        Pool'dan connection al
        
        Returns:
            pyodbc.Connection
            
        Raises:
            ConnectionError: Bağlantı kurulamazsa
            TimeoutError: Pool dolu ve timeout aşılırsa
        """
        self._stats['total_requests'] += 1
        
        # Önce pool'dan almayı dene
        try:
            conn = self._pool.get_nowait()
            
            # Connection geçerli mi kontrol et
            if self._is_connection_valid(conn):
                self._stats['pool_hits'] += 1
                return conn
            else:
                # Bozuk connection, yenisini oluştur
                self._stats['recovered_connections'] += 1
                with self._lock:
                    self._created_count -= 1
                try:
                    conn.close()
                except Exception:
                    pass
                # Devam et, aşağıda yeni oluşturulacak
                
        except Empty:
            pass  # Pool boş, yeni oluşturmayı dene
        
        # Yeni connection oluşturabilir miyiz?
        with self._lock:
            if self._created_count < self._max_connections:
                self._created_count += 1
                self._stats['new_connections'] += 1
                try:
                    return self._create_connection()
                except Exception:
                    self._created_count -= 1
                    raise
        
        # Pool dolu, bekle
        try:
            conn = self._pool.get(timeout=self._connection_timeout)
            
            if self._is_connection_valid(conn):
                self._stats['pool_hits'] += 1
                return conn
            else:
                # Bozuk, yenisini oluştur
                self._stats['recovered_connections'] += 1
                try:
                    conn.close()
                except Exception:
                    pass
                return self._create_connection()
                
        except Empty:
            raise TimeoutError(
                f"Connection pool timeout ({self._connection_timeout}s). "
                f"Tüm {self._max_connections} connection kullanımda."
            )
    
    def return_connection(self, conn: pyodbc.Connection) -> None:
        """
        Connection'ı pool'a geri ver
        
        Args:
            conn: Geri verilecek connection
        """
        if conn is None:
            return
            
        try:
            # Bekleyen transaction varsa rollback yap
            try:
                conn.rollback()
            except Exception:
                pass
            
            # Connection hala geçerli mi?
            if self._is_connection_valid(conn):
                try:
                    self._pool.put_nowait(conn)
                except Exception:
                    # Pool dolu, connection'ı kapat
                    try:
                        conn.close()
                    except Exception:
                        pass
                    with self._lock:
                        self._created_count -= 1
            else:
                # Bozuk connection, kapat
                try:
                    conn.close()
                except Exception:
                    pass
                with self._lock:
                    self._created_count -= 1
                    
        except Exception as e:
            # Herhangi bir hata durumunda güvenli kapat
            try:
                conn.close()
            except Exception:
                pass
            with self._lock:
                self._created_count -= 1
    
    def get_stats(self) -> dict:
        """Pool istatistiklerini döndür"""
        return {
            **self._stats,
            'pool_size': self._pool.qsize(),
            'active_connections': self._created_count - self._pool.qsize(),
            'total_connections': self._created_count,
            'max_connections': self._max_connections
        }
    
    def close_all(self) -> None:
        """Tüm connection'ları kapat (uygulama kapanırken)"""
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
    """
    Connection wrapper - pool'a otomatik dönüş için
    
    Bu sınıf sayesinde:
    - with kullanımı desteklenir
    - close() çağrıldığında pool'a döner
    - Hata durumunda otomatik temizlik
    """
    
    def __init__(self, pool: ConnectionPool, conn: pyodbc.Connection):
        self._pool = pool
        self._conn = conn
        self._closed = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # Exception'ı yutma
    
    def close(self) -> None:
        """Connection'ı pool'a geri ver"""
        if not self._closed:
            self._closed = True
            self._pool.return_connection(self._conn)
    
    def cursor(self):
        """Cursor oluştur"""
        return self._conn.cursor()
    
    def commit(self) -> None:
        """Transaction'ı commit et"""
        self._conn.commit()
    
    def rollback(self) -> None:
        """Transaction'ı rollback et"""
        self._conn.rollback()
    
    def execute(self, sql: str, params=None):
        """Direkt SQL çalıştır (kısa sorgular için)"""
        cursor = self._conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor
    
    # pyodbc.Connection attribute'larına proxy
    def __getattr__(self, name):
        return getattr(self._conn, name)


# =============================================================================
# GLOBAL POOL INSTANCES
# =============================================================================

# Ana ERP veritabanı pool'u
_erp_pool: Optional[ConnectionPool] = None
_erp_pool_lock = threading.Lock()

# PLC veritabanı pool'u
_plc_pool: Optional[ConnectionPool] = None
_plc_pool_lock = threading.Lock()

# PLC Bağlantı Ayarları - external_config'den okunur
def _get_plc_config() -> dict:
    """PLC config'ini güvenli kaynaklardan al"""
    try:
        from core.external_config import config_manager as _ext_cfg
        plc_cfg = _ext_cfg.get_plc_config()
        if plc_cfg:
            return plc_cfg
    except Exception:
        pass
    # Fallback: config.py'deki PLC_DB_CONFIG
    try:
        from config import PLC_DB_CONFIG
        return PLC_DB_CONFIG
    except ImportError:
        pass
    # Son çare: boş config (bağlantı hatası verecek)
    return {
        'driver': 'ODBC Driver 18 for SQL Server',
        'server': '', 'database': '', 'user': '', 'password': '',
        'timeout': 5
    }

PLC_CONFIG = _get_plc_config()


def _get_erp_pool() -> ConnectionPool:
    """ERP pool'unu lazy initialize et"""
    global _erp_pool
    if _erp_pool is None:
        with _erp_pool_lock:
            if _erp_pool is None:
                _erp_pool = ConnectionPool(max_connections=20)
    return _erp_pool


def _get_plc_pool() -> ConnectionPool:
    """PLC pool'unu lazy initialize et"""
    global _plc_pool
    if _plc_pool is None:
        with _plc_pool_lock:
            if _plc_pool is None:
                _plc_pool = ConnectionPool(max_connections=10, custom_config=PLC_CONFIG)
    return _plc_pool


# =============================================================================
# PUBLIC API (Geriye Uyumlu)
# =============================================================================

def get_db_connection(max_retries: int = 2, retry_delay: float = 1.0) -> PooledConnection:
    """
    AtmoLogicERP veritabanına bağlantı döndür (retry destekli)

    Kullanım:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")

    Args:
        max_retries: Başarısız olursa kaç kez daha denenecek (varsayılan: 2)
        retry_delay: Denemeler arası bekleme süresi (saniye)

    Returns:
        PooledConnection: Pool'a otomatik dönen connection wrapper

    Raises:
        ConnectionError: Tüm denemeler başarısız olursa
    """
    last_error = None

    for attempt in range(1 + max_retries):
        try:
            if MANAGER_AVAILABLE:
                result = db_manager.get_connection('ERP')
                if not hasattr(result, 'cursor'):
                    raise TypeError(f"Beklenmeyen bağlantı tipi: {type(result)}")
                return result
            else:
                pool = _get_erp_pool()
                conn = pool.get_connection()
                return PooledConnection(pool, conn)
        except (ConnectionError, TimeoutError, TypeError) as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(retry_delay * (attempt + 1))  # Artan bekleme
            continue
        except Exception as e:
            last_error = e
            break

    # Tüm denemeler başarısız
    raise ConnectionError(
        f"Veritabanına bağlanılamadı ({max_retries + 1} deneme sonrası).\n"
        f"Sunucu erişilebilir olduğundan emin olun.\n"
        f"Detay: {last_error}"
    )


def get_plc_connection() -> PooledConnection:
    """
    PLC/KAPLAMA veritabanına bağlantı döndür.
    PLC bağlanamıyorsa graceful degradation aktif.

    Returns:
        PooledConnection

    Raises:
        ConnectionError: Bağlantı kurulamazsa
    """
    import logging
    try:
        if MANAGER_AVAILABLE:
            return db_manager.get_connection('PLC')
        else:
            pool = _get_plc_pool()
            conn = pool.get_connection()
            return PooledConnection(pool, conn)
    except (ConnectionError, TimeoutError) as e:
        logging.warning(f"PLC bağlantısı başarısız (manuel mod aktif): {e}")
        raise ConnectionError(
            f"PLC veritabanına bağlanılamadı.\n"
            f"PLC verisi olmadan devam edilebilir.\n"
            f"Detay: {e}"
        )


def execute_query(query: str, params: list = None) -> list:
    """
    SELECT sorgusu çalıştır ve sonuçları döndür

    Args:
        query: SQL sorgusu
        params: Parametre listesi

    Returns:
        list[dict]: Sonuçlar (boş liste sorgu sonuç dönmezse)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        if not cursor.description:
            return []
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


def execute_non_query(query: str, params: list = None) -> int:
    """
    INSERT/UPDATE/DELETE sorgusu çalıştır

    Args:
        query: SQL sorgusu
        params: Parametre listesi

    Returns:
        int: Etkilenen satır sayısı
    """
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
    """
    PLC veritabanından SELECT sorgusu çalıştır

    Args:
        query: SQL sorgusu
        params: Parametre listesi

    Returns:
        list[dict]: Sonuçlar (boş liste PLC erişilemezse)
    """
    with get_plc_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        if not cursor.description:
            return []
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


def get_pool_stats() -> dict:
    """
    Connection pool istatistiklerini döndür (debug için)
    
    v3: database_manager'dan istatistikleri al
    
    Returns:
        dict: Pool istatistikleri
    """
    if MANAGER_AVAILABLE:
        # YENİ: Tüm bağlantıların istatistiklerini al
        return db_manager.get_pool_stats()
    else:
        # FALLBACK: Eski sistem
        stats = {'erp': None, 'plc': None}
        if _erp_pool:
            stats['erp'] = _erp_pool.get_stats()
        if _plc_pool:
            stats['plc'] = _plc_pool.get_stats()
        return stats


def close_all_pools() -> None:
    """
    Tüm connection pool'larını kapat (uygulama kapanırken çağır)
    
    v3: database_manager'ı kullan
    """
    if MANAGER_AVAILABLE:
        # YENİ: Manager'ı kapat
        db_manager.close_all()
    else:
        # FALLBACK: Eski pool'ları kapat
        global _erp_pool, _plc_pool
        
        if _erp_pool:
            _erp_pool.close_all()
            _erp_pool = None
        
        if _plc_pool:
            _plc_pool.close_all()
            _plc_pool = None


# =============================================================================
# TRANSACTION HELPER
# =============================================================================

@contextmanager
def transaction():
    """
    Transaction context manager
    
    v3: Artık database_manager kullanıyor
    
    Kullanım:
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT ...")
            cursor.execute("UPDATE ...")
            # Otomatik commit (hata yoksa)
            # Hata varsa otomatik rollback
    """
    if MANAGER_AVAILABLE:
        # YENİ: Manager'dan transaction al
        with new_transaction('ERP') as conn:
            yield conn
    else:
        # FALLBACK: Eski sistem
        conn = get_db_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# =============================================================================
# MODÜLLER İÇİN YARDIMCI FONKSİYONLAR
# =============================================================================

def safe_execute_query(query: str, params: list = None, default=None):
    """
    Güvenli SELECT - hata olursa exception fırlatmaz, default döner.
    Modüllerde veri yükleme işlemlerinde kullanılır.

    Args:
        query: SQL sorgusu
        params: Parametre listesi
        default: Hata durumunda dönecek değer (varsayılan: boş liste)

    Returns:
        list[dict] veya default değer
    """
    if default is None:
        default = []
    try:
        return execute_query(query, params)
    except (ConnectionError, TimeoutError) as e:
        import logging
        logging.warning(f"Veritabanı bağlantı hatası (sorgu atlandı): {e}")
        return default
    except Exception as e:
        import logging
        logging.error(f"Sorgu hatası: {e}\nSQL: {query[:200]}")
        return default


def safe_execute_non_query(query: str, params: list = None) -> tuple:
    """
    Güvenli INSERT/UPDATE/DELETE - hata olursa (False, hata_mesajı) döner.

    Returns:
        (True, rowcount) veya (False, hata_mesajı)
    """
    try:
        rowcount = execute_non_query(query, params)
        return True, rowcount
    except (ConnectionError, TimeoutError) as e:
        import logging
        logging.warning(f"Veritabanı bağlantı hatası (yazma atlandı): {e}")
        return False, f"Bağlantı hatası: {e}"
    except Exception as e:
        import logging
        logging.error(f"Yazma hatası: {e}\nSQL: {query[:200]}")
        return False, str(e)


@contextmanager
def safe_connection():
    """
    Güvenli bağlantı context manager.
    Modüllerdeki karmaşık işlemler için önerilir.

    Kullanım:
        with safe_connection() as conn:
            if conn is None:
                QMessageBox.warning(self, "Hata", "Veritabanına bağlanılamadı!")
                return
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
            conn.commit()
    """
    conn = None
    try:
        conn = get_db_connection()
        yield conn
    except (ConnectionError, TimeoutError):
        yield None
    except Exception:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        yield None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


# =============================================================================
# UYGULAMA KAPANIŞI
# =============================================================================

import atexit
atexit.register(close_all_pools)
