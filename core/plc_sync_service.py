# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - PLC Senkronizasyon Servisi
============================================
KAPLAMA veritabanından PLC verilerini çekerek local cache'e yazar.
UI bu cache'den okuyarak hızlı yanıt alır.

Iki modda calisir:
    1) QThread modu: MainWindow icinden arka planda calisir (varsayilan)
    2) Konsol modu:  python plc_sync_service.py [once|init|status]

Kullanım (program icinden):
    from core.plc_sync_service import get_plc_sync_service, stop_plc_sync_service

    # Servisi baslat (MainWindow.__init__ icinde)
    service = get_plc_sync_service()

    # Programdan cikarken
    stop_plc_sync_service()

Kullanım (konsol):
    python plc_sync_service.py              # Surekli calistir
    python plc_sync_service.py once         # Tek sefer
    python plc_sync_service.py init         # 30 gunluk veri yukle
    python plc_sync_service.py status       # Durum goster
"""

import pyodbc
import time
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any

# QThread import (opsiyonel - konsol modunda gerek yok)
try:
    from PySide6.QtCore import QThread, Signal, QMutex
    QTHREAD_AVAILABLE = True
except ImportError:
    QTHREAD_AVAILABLE = False

# ============================================================================
# YAPILANDIRMA
# ============================================================================

# Senkronizasyon ayarları
SYNC_INTERVAL = 10  # saniye
BATCH_SIZE = 1000   # tek seferde çekilecek kayıt sayısı
MAX_RETRY = 3       # bağlantı hatası durumunda tekrar deneme

# Merkezi baglanti sistemi (database.py / database_manager.py)
USE_CENTRAL_DB = False
try:
    from core.database import get_db_connection, get_plc_connection
    USE_CENTRAL_DB = True
except ImportError:
    pass

# Fallback: Kendi baglanti ayarlari (sadece konsol modunda)
try:
    from config import DB_CONFIG
    ERP_CONFIG = DB_CONFIG.copy()
except ImportError:
    ERP_CONFIG = {
        'driver': 'ODBC Driver 17 for SQL Server',
        'server': r'192.168.1.66\SQLEXPRESS',
        'database': 'AtmoLogicERP',
        'user': 'MERP',
        'password': 'mamkpbrs00880072',
        'timeout': 30
    }

try:
    from config import PLC_DB_CONFIG
    PLC_CONFIG = PLC_DB_CONFIG.copy()
except ImportError:
    PLC_CONFIG = {
        'driver': 'ODBC Driver 17 for SQL Server',
        'server': r'KAPLAMA\SQLEXPRESS',
        'database': 'KAPLAMA',
        'user': 'sa',
        'password': '100',
        'timeout': 30
    }

# Loglama
LOG_FILE = os.path.join(os.path.dirname(__file__), 'plc_sync.log')
LOG_LEVEL = logging.INFO

# ============================================================================
# LOGLAMA AYARLARI
# ============================================================================

def setup_logging():
    """Loglama yapılandırması"""
    _logger = logging.getLogger("plc_sync")
    if not _logger.handlers:
        _logger.setLevel(LOG_LEVEL)
        fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        try:
            fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
            fh.setFormatter(fmt)
            _logger.addHandler(fh)
        except Exception:
            pass
        # Konsol modunda stdout'a da yaz
        if not QTHREAD_AVAILABLE or __name__ == "__main__":
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(fmt)
            _logger.addHandler(sh)
    return _logger

logger = setup_logging()

# ============================================================================
# VERİTABANI BAĞLANTILARI
# ============================================================================

def get_connection_string(config: dict) -> str:
    """Bağlantı string'i oluştur"""
    return (
        f"DRIVER={{{config['driver']}}};"
        f"SERVER={config['server']};"
        f"DATABASE={config['database']};"
        f"UID={config['user']};PWD={config['password']};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )

def connect_erp():
    """ERP veritabanına bağlan (merkezi pool veya dogrudan)"""
    try:
        if USE_CENTRAL_DB:
            return get_db_connection()
        else:
            conn = pyodbc.connect(
                get_connection_string(ERP_CONFIG),
                timeout=ERP_CONFIG['timeout'],
                autocommit=False
            )
            return conn
    except Exception as e:
        logger.error(f"ERP bağlantı hatası: {e}")
        return None

def connect_plc():
    """PLC veritabanına bağlan (merkezi pool veya dogrudan)"""
    try:
        if USE_CENTRAL_DB:
            return get_plc_connection()
        else:
            conn = pyodbc.connect(
                get_connection_string(PLC_CONFIG),
                timeout=PLC_CONFIG['timeout'],
                autocommit=False
            )
            return conn
    except Exception as e:
        logger.error(f"PLC bağlantı hatası: {e}")
        return None

# ============================================================================
# SENKRONİZASYON FONKSİYONLARI
# ============================================================================

def get_last_sync_id(erp_conn: pyodbc.Connection) -> int:
    """Son senkronize edilen kaynak ID'yi al"""
    try:
        cursor = erp_conn.cursor()
        cursor.execute("SELECT ISNULL(son_kaynak_id, 0) FROM uretim.plc_sync_durum WHERE id = 1")
        row = cursor.fetchone()
        return row[0] if row else 0
    except Exception as e:
        logger.error(f"Son sync ID alma hatası: {e}")
        return 0

def update_sync_status(erp_conn, son_id: int, aktarim_sayisi: int,
                       durum: str = 'CALISIYOR', hata: str = None):
    """Senkronizasyon durumunu güncelle (son_id=0 ise mevcut ID korunur)"""
    try:
        cursor = erp_conn.cursor()

        if hata:
            if son_id > 0:
                cursor.execute("""
                    UPDATE uretim.plc_sync_durum
                    SET son_sync_tarihi = GETDATE(),
                        son_kaynak_id = ?,
                        toplam_aktarim = toplam_aktarim + ?,
                        servis_durumu = ?,
                        son_hata = ?,
                        son_hata_tarihi = GETDATE()
                    WHERE id = 1
                """, (son_id, aktarim_sayisi, durum, hata[:500]))
            else:
                cursor.execute("""
                    UPDATE uretim.plc_sync_durum
                    SET son_sync_tarihi = GETDATE(),
                        toplam_aktarim = toplam_aktarim + ?,
                        servis_durumu = ?,
                        son_hata = ?,
                        son_hata_tarihi = GETDATE()
                    WHERE id = 1
                """, (aktarim_sayisi, durum, hata[:500]))
        else:
            if son_id > 0:
                cursor.execute("""
                    UPDATE uretim.plc_sync_durum
                    SET son_sync_tarihi = GETDATE(),
                        son_kaynak_id = ?,
                        toplam_aktarim = toplam_aktarim + ?,
                        servis_durumu = ?
                    WHERE id = 1
                """, (son_id, aktarim_sayisi, durum))
            else:
                cursor.execute("""
                    UPDATE uretim.plc_sync_durum
                    SET son_sync_tarihi = GETDATE(),
                        toplam_aktarim = toplam_aktarim + ?,
                        servis_durumu = ?
                    WHERE id = 1
                """, (aktarim_sayisi, durum))

        erp_conn.commit()
    except Exception as e:
        logger.error(f"Sync durum güncelleme hatası: {e}")

def fetch_plc_data(plc_conn: pyodbc.Connection, last_id: int) -> List[Dict[str, Any]]:
    """PLC'den yeni verileri çek"""
    try:
        cursor = plc_conn.cursor()
        
        # Son ID'den sonraki kayıtları çek
        cursor.execute("""
            SELECT TOP (?)
                id,
                KznNo,
                BaraNo,
                ReceteNo,
                CASE WHEN Sicaklik BETWEEN -50 AND 3000 THEN Sicaklik ELSE NULL END as Sicaklik,
                CASE WHEN Ort_Redresor_Akim BETWEEN 0 AND 99999 THEN Ort_Redresor_Akim ELSE NULL END as Akim,
                CASE WHEN Ort_Redresor_Voltaj BETWEEN 0 AND 99999 THEN Ort_Redresor_Voltaj ELSE NULL END as Voltaj,
                Miktar,
                BirimMiktar,
                Recete_Zamani,
                TarihDoldurma,
                TarihBosaltma,
                ReceteAdim,
                RedresorAkimYog,
                OTO_Manual_Doldurma,
                OTO_Manual_Bosaltma
            FROM dbo.data
            WHERE id > ?
            ORDER BY id
        """, (BATCH_SIZE, last_id))
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in rows]
        
    except Exception as e:
        logger.error(f"PLC veri çekme hatası: {e}")
        return []

def determine_hat_kodu(kazan_no: int) -> str:
    """Kazan numarasına göre hat kodunu belirle"""
    if 101 <= kazan_no <= 143:
        return 'KTL'
    elif 201 <= kazan_no <= 247:
        return 'CINKO'
    else:
        return 'DIGER'

def insert_to_tarihce(erp_conn: pyodbc.Connection, data_list: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Verileri plc_tarihce tablosuna ekle"""
    if not data_list:
        return 0, 0
    
    try:
        cursor = erp_conn.cursor()
        
        inserted = 0
        last_id = 0
        
        for data in data_list:
            kaynak_id = data.get('id')

            # Duplicate kontrolü - aynı kaynak_id zaten varsa atla
            cursor.execute(
                "SELECT COUNT(*) FROM uretim.plc_tarihce WHERE kaynak_id = ?",
                (kaynak_id,)
            )
            if cursor.fetchone()[0] > 0:
                last_id = max(last_id, kaynak_id or 0)
                continue

            hat_kodu = determine_hat_kodu(data.get('KznNo', 0))

            # PLC sıcaklık değeri 10x büyük gelir, 10'a böl
            raw_sicaklik = data.get('Sicaklik')
            sicaklik = round(raw_sicaklik / 10.0, 1) if raw_sicaklik is not None else None

            cursor.execute("""
                INSERT INTO uretim.plc_tarihce (
                    kaynak_id, kazan_no, hat_kodu, bara_no, recete_no,
                    sicaklik, akim, voltaj, miktar, birim_miktar,
                    recete_zamani, tarih_doldurma, tarih_bosaltma,
                    recete_adim, akim_yogunlugu, oto_manual_doldurma, oto_manual_bosaltma
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                kaynak_id,
                data.get('KznNo'),
                hat_kodu,
                data.get('BaraNo'),
                data.get('ReceteNo'),
                sicaklik,
                data.get('Akim'),
                data.get('Voltaj'),
                data.get('Miktar'),
                data.get('BirimMiktar'),
                data.get('Recete_Zamani'),
                data.get('TarihDoldurma'),
                data.get('TarihBosaltma'),
                data.get('ReceteAdim'),
                data.get('RedresorAkimYog'),
                data.get('OTO_Manual_Doldurma'),
                data.get('OTO_Manual_Bosaltma')
            ))
            
            inserted += 1
            last_id = max(last_id, data.get('id', 0))
        
        erp_conn.commit()
        return inserted, last_id
        
    except Exception as e:
        erp_conn.rollback()
        logger.error(f"Tarihçe ekleme hatası: {e}")
        return 0, 0

def update_cache(erp_conn: pyodbc.Connection):
    """Cache tablosunu güncelle (stored procedure çağır)"""
    try:
        cursor = erp_conn.cursor()
        cursor.execute("EXEC uretim.sp_plc_cache_guncelle")
        erp_conn.commit()
        logger.debug("Cache güncellendi")
    except Exception as e:
        logger.error(f"Cache güncelleme hatası: {e}")

# ============================================================================
# ANA SENKRONİZASYON DÖNGÜSÜ
# ============================================================================

def sync_once() -> bool:
    """Tek seferlik senkronizasyon yap"""
    erp_conn = None
    plc_conn = None

    try:
        # Bağlantıları aç
        erp_conn = connect_erp()
        if not erp_conn:
            logger.error("ERP bağlantısı kurulamadı")
            return False

        # ÖNCE son sync ID'yi al (status update'den once!)
        last_id = get_last_sync_id(erp_conn)

        # Tarihçedeki max kaynak_id ile karşılaştır - geri kalmışsa düzelt
        try:
            cursor_check = erp_conn.cursor()
            cursor_check.execute("SELECT ISNULL(MAX(kaynak_id), 0) FROM uretim.plc_tarihce")
            max_tarihce_id = cursor_check.fetchone()[0]
            if max_tarihce_id > last_id:
                logger.warning(f"son_kaynak_id ({last_id}) tarihçe max'ından ({max_tarihce_id}) küçük! Düzeltiliyor...")
                last_id = max_tarihce_id
                update_sync_status(erp_conn, last_id, 0, 'CALISIYOR')
        except Exception as e:
            logger.warning(f"Tarihçe kontrol hatası: {e}")

        logger.debug(f"Son sync ID: {last_id}")

        plc_conn = connect_plc()
        if not plc_conn:
            logger.error("PLC bağlantısı kurulamadı")
            update_sync_status(erp_conn, last_id, 0, 'HATA', 'PLC bağlantısı kurulamadı')
            return False

        # Eğer çok gerideyse bugünün başına atla
        try:
            pc = plc_conn.cursor()
            pc.execute("SELECT ISNULL(MIN(id), 0) - 1 FROM dbo.data WHERE TarihDoldurma >= CAST(GETDATE() AS DATE)")
            bugun_baslangic = pc.fetchone()[0]
            if bugun_baslangic > 0 and last_id < bugun_baslangic:
                logger.warning(f"son_kaynak_id ({last_id}) bugünün verilerinden ({bugun_baslangic}) çok geride! Bugüne atlanıyor...")
                last_id = bugun_baslangic
                update_sync_status(erp_conn, last_id, 0, 'CALISIYOR')
        except Exception as e:
            logger.warning(f"PLC bugün kontrolü hatası: {e}")

        logger.info(f"Sync başlıyor, son ID: {last_id}")

        # PLC'den yeni verileri çek
        plc_data = fetch_plc_data(plc_conn, last_id)
        
        if plc_data:
            logger.info(f"{len(plc_data)} yeni kayıt bulundu")
            
            # Tarihçeye ekle
            inserted, new_last_id = insert_to_tarihce(erp_conn, plc_data)
            
            if inserted > 0:
                logger.info(f"{inserted} kayıt tarihçeye eklendi (son ID: {new_last_id})")
                
                # Sync durumunu güncelle
                update_sync_status(erp_conn, new_last_id, inserted, 'CALISIYOR')
                
                # Cache'i güncelle
                update_cache(erp_conn)
        else:
            logger.debug("Yeni kayıt yok")
            # Cache'i yine de güncelle (durum hesaplamaları için)
            update_cache(erp_conn)
        
        return True
        
    except Exception as e:
        logger.error(f"Senkronizasyon hatası: {e}")
        if erp_conn:
            update_sync_status(erp_conn, 0, 0, 'HATA', str(e))
        return False
        
    finally:
        # Bağlantıları kapat
        if plc_conn:
            try:
                plc_conn.close()
            except:
                pass
        if erp_conn:
            try:
                erp_conn.close()
            except:
                pass

def run_continuous():
    """Sürekli çalışan senkronizasyon döngüsü"""
    logger.info("=" * 60)
    logger.info("PLC Senkronizasyon Servisi başlatıldı")
    logger.info(f"Senkronizasyon aralığı: {SYNC_INTERVAL} saniye")
    logger.info(f"Batch boyutu: {BATCH_SIZE}")
    logger.info("=" * 60)
    
    retry_count = 0
    
    while True:
        try:
            success = sync_once()
            
            if success:
                retry_count = 0
            else:
                retry_count += 1
                if retry_count >= MAX_RETRY:
                    logger.warning(f"Ardışık {MAX_RETRY} başarısız deneme, bekleme süresi artırılıyor")
                    time.sleep(SYNC_INTERVAL * 3)
                    retry_count = 0
                    continue
            
            time.sleep(SYNC_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Servis durduruldu (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"Beklenmeyen hata: {e}")
            time.sleep(SYNC_INTERVAL)

# ============================================================================
# İLK VERİ YÜKLEME (Geçmiş veriler için)
# ============================================================================

def initial_load(days: int = 30):
    """
    İlk kurulumda geçmiş verileri yükle
    
    Args:
        days: Kaç günlük veri yüklenecek (varsayılan: 30)
    """
    logger.info(f"İlk veri yükleme başlıyor ({days} günlük veri)")
    
    erp_conn = connect_erp()
    plc_conn = connect_plc()
    
    if not erp_conn or not plc_conn:
        logger.error("Bağlantı kurulamadı")
        return
    
    try:
        # Tarih aralığını belirle
        start_date = datetime.now() - timedelta(days=days)
        
        cursor = plc_conn.cursor()
        
        # Toplam kayıt sayısını öğren
        cursor.execute("""
            SELECT COUNT(*) FROM dbo.data 
            WHERE TarihDoldurma >= ?
        """, (start_date,))
        total = cursor.fetchone()[0]
        logger.info(f"Toplam {total:,} kayıt yüklenecek")
        
        # Batch halinde yükle
        offset = 0
        loaded = 0
        
        while offset < total:
            cursor.execute("""
                SELECT 
                    id, KznNo, BaraNo, ReceteNo,
                    CASE WHEN Sicaklik BETWEEN 0 AND 500 THEN Sicaklik ELSE NULL END as Sicaklik,
                    CASE WHEN Ort_Redresor_Akim BETWEEN 0 AND 9999 THEN Ort_Redresor_Akim ELSE NULL END as Akim,
                    CASE WHEN Ort_Redresor_Voltaj BETWEEN 0 AND 9999 THEN Ort_Redresor_Voltaj ELSE NULL END as Voltaj,
                    Miktar, BirimMiktar, Recete_Zamani,
                    TarihDoldurma, TarihBosaltma, ReceteAdim,
                    RedresorAkimYog, OTO_Manual_Doldurma, OTO_Manual_Bosaltma
                FROM dbo.data
                WHERE TarihDoldurma >= ?
                ORDER BY id
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (start_date, offset, BATCH_SIZE))
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            if not rows:
                break
            
            data_list = [dict(zip(columns, row)) for row in rows]
            inserted, last_id = insert_to_tarihce(erp_conn, data_list)
            
            loaded += inserted
            offset += BATCH_SIZE
            
            # İlerleme göster
            progress = min(100, (loaded / total) * 100)
            logger.info(f"İlerleme: {progress:.1f}% ({loaded:,}/{total:,})")
        
        # Son sync ID'yi güncelle
        cursor.execute("SELECT MAX(id) FROM dbo.data WHERE TarihDoldurma >= ?", (start_date,))
        max_id = cursor.fetchone()[0] or 0
        update_sync_status(erp_conn, max_id, loaded, 'CALISIYOR')
        
        # Cache'i güncelle
        update_cache(erp_conn)
        
        logger.info(f"İlk veri yükleme tamamlandı: {loaded:,} kayıt")
        
    except Exception as e:
        logger.error(f"İlk veri yükleme hatası: {e}")
        
    finally:
        plc_conn.close()
        erp_conn.close()

# ============================================================================
# KOMUT SATIRI ARAYÜZÜ
# ============================================================================

def print_usage():
    """Kullanım bilgisi"""
    print("""
PLC Senkronizasyon Servisi
==========================

Kullanım:
    python plc_sync_service.py [komut]

Komutlar:
    (boş)       Sürekli çalışan servis modunda başlat
    once        Tek seferlik senkronizasyon yap
    init        İlk kurulum - 30 günlük geçmiş veriyi yükle
    init N      İlk kurulum - N günlük geçmiş veriyi yükle
    status      Senkronizasyon durumunu göster
    help        Bu yardım mesajını göster

Örnekler:
    python plc_sync_service.py              # Sürekli çalıştır
    python plc_sync_service.py once         # Tek sefer çalıştır
    python plc_sync_service.py init 7       # Son 7 günü yükle
    """)

def show_status():
    """Senkronizasyon durumunu göster"""
    erp_conn = connect_erp()
    if not erp_conn:
        print("ERP bağlantısı kurulamadı")
        return
    
    try:
        cursor = erp_conn.cursor()
        cursor.execute("""
            SELECT 
                son_sync_tarihi,
                son_kaynak_id,
                toplam_aktarim,
                servis_durumu,
                son_hata,
                son_hata_tarihi
            FROM uretim.plc_sync_durum
            WHERE id = 1
        """)
        row = cursor.fetchone()
        
        if row:
            print("\n" + "=" * 50)
            print("PLC SENKRONİZASYON DURUMU")
            print("=" * 50)
            print(f"Son Sync Tarihi  : {row[0] or '-'}")
            print(f"Son Kaynak ID    : {row[1]:,}" if row[1] else "Son Kaynak ID    : -")
            print(f"Toplam Aktarım   : {row[2]:,}" if row[2] else "Toplam Aktarım   : 0")
            print(f"Servis Durumu    : {row[3] or '-'}")
            if row[4]:
                print(f"Son Hata         : {row[4]}")
                print(f"Hata Tarihi      : {row[5]}")
            print("=" * 50)
            
            # Cache durumu
            cursor.execute("""
                SELECT 
                    COUNT(*) as toplam,
                    SUM(CASE WHEN durum = 'AKTIF' THEN 1 ELSE 0 END) as aktif,
                    SUM(CASE WHEN durum = 'BEKLIYOR' THEN 1 ELSE 0 END) as bekliyor,
                    SUM(CASE WHEN durum = 'DURDU' THEN 1 ELSE 0 END) as durdu
                FROM uretim.plc_cache
            """)
            cache = cursor.fetchone()
            
            print(f"\nCache Durumu:")
            print(f"  Toplam Kazan   : {cache[0]}")
            print(f"  🟢 Aktif       : {cache[1]}")
            print(f"  🟡 Bekliyor    : {cache[2]}")
            print(f"  🔴 Durdu       : {cache[3]}")
            
            # Tarihçe durumu
            cursor.execute("SELECT COUNT(*), MIN(tarih_doldurma), MAX(tarih_doldurma) FROM uretim.plc_tarihce")
            tarihce = cursor.fetchone()
            
            print(f"\nTarihçe:")
            print(f"  Toplam Kayıt   : {tarihce[0]:,}")
            print(f"  İlk Kayıt      : {tarihce[1] or '-'}")
            print(f"  Son Kayıt      : {tarihce[2] or '-'}")
            print()
        else:
            print("Sync durumu bulunamadı")
            
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        erp_conn.close()

# ============================================================================
# QTHREAD TABANLI ARKA PLAN SERVİSİ
# ============================================================================

if QTHREAD_AVAILABLE:

    class PlcSyncThread(QThread):
        """
        PLC senkronizasyonu icin arka plan thread'i.
        MainWindow acildiginda baslar, kapandiginda durur.
        UI'yi bloke etmez.
        """

        # Sinyaller (opsiyonel - UI'den dinlenebilir)
        sync_completed = Signal(int)    # aktarilan kayit sayisi
        sync_error = Signal(str)        # hata mesaji
        status_changed = Signal(str)    # CALISIYOR / HATA / DURDURULDU

        def __init__(self, interval: int = SYNC_INTERVAL, parent=None):
            super().__init__(parent)
            self._interval = interval
            self._running = False
            self._mutex = QMutex()

        def run(self):
            """Thread ana dongusu (UI thread'inden bagimsiz calisir)"""
            self._running = True
            retry_count = 0

            logger.info("PLC Sync Thread baslatildi (aralik: %d sn)", self._interval)
            self.status_changed.emit("CALISIYOR")

            while self._running:
                try:
                    success = sync_once()

                    if success:
                        retry_count = 0
                        # Son sync'te kac kayit aktarildi bilgisini yayinla
                        self.sync_completed.emit(0)
                    else:
                        retry_count += 1
                        self.sync_error.emit("Senkronizasyon basarisiz")

                        if retry_count >= MAX_RETRY:
                            logger.warning("Ardisik %d basarisiz, bekleme artirildi", MAX_RETRY)
                            self.status_changed.emit("HATA")
                            # Uzun bekleme (parcalara bol - stop kontrol icin)
                            for _ in range(self._interval * 3):
                                if not self._running:
                                    break
                                time.sleep(1)
                            retry_count = 0
                            continue

                except Exception as e:
                    logger.error("Sync thread hatasi: %s", e)
                    self.sync_error.emit(str(e))

                # Normal bekleme (1 saniye parcalar halinde - hizli stop icin)
                for _ in range(self._interval):
                    if not self._running:
                        break
                    time.sleep(1)

            logger.info("PLC Sync Thread durduruldu")
            self.status_changed.emit("DURDURULDU")

        def stop(self):
            """Thread'i guvenli durdur"""
            self._running = False
            # Thread'in bitmesini bekle (max 5 sn)
            if self.isRunning():
                self.wait(5000)


# ============================================================================
# GLOBAL SERVİS YÖNETİMİ (PDKS pattern ile ayni)
# ============================================================================

_plc_sync_service: Optional[any] = None


def get_plc_sync_service(interval: int = SYNC_INTERVAL):
    """
    PLC sync servisini baslat ve dondur (singleton).
    Birden fazla cagri ayni instance'i dondurur.

    Kullanim:
        service = get_plc_sync_service()
    """
    global _plc_sync_service

    if not QTHREAD_AVAILABLE:
        logger.warning("QThread mevcut degil, PLC sync devre disi")
        return None

    if _plc_sync_service is None or not _plc_sync_service.isRunning():
        _plc_sync_service = PlcSyncThread(interval=interval)
        _plc_sync_service.start()
        logger.info("PLC Sync servisi baslatildi")

    return _plc_sync_service


def stop_plc_sync_service():
    """PLC sync servisini durdur."""
    global _plc_sync_service

    if _plc_sync_service is not None:
        _plc_sync_service.stop()
        _plc_sync_service = None
        logger.info("PLC Sync servisi durduruldu")


def is_plc_sync_running() -> bool:
    """Servis calisiyor mu?"""
    return _plc_sync_service is not None and _plc_sync_service.isRunning()


# ============================================================================
# ANA GİRİŞ NOKTASI (konsol modu)
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Varsayılan: sürekli çalış
        run_continuous()
    else:
        cmd = sys.argv[1].lower()

        if cmd == 'help':
            print_usage()
        elif cmd == 'once':
            sync_once()
        elif cmd == 'init':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            initial_load(days)
        elif cmd == 'status':
            show_status()
        else:
            print(f"Bilinmeyen komut: {cmd}")
            print_usage()
