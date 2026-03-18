# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - PDKS Reader Service
ZK ve diğer PDKS cihazlarından otomatik veri okuma servisi
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from threading import Lock

from PySide6.QtCore import QThread, Signal, QTimer, QMutex

# ZK kütüphanesi (opsiyonel)
try:
    from zk import ZK
    from zk.exception import ZKError, ZKErrorConnection, ZKErrorResponse
    ZK_AVAILABLE = True
except ImportError:
    ZK_AVAILABLE = False
    ZKError = Exception
    ZKErrorConnection = Exception
    ZKErrorResponse = Exception

# Logging
logger = logging.getLogger('PDKSReaderService')


class DeviceReaderThread(QThread):
    """
    Tek bir PDKS cihazı için okuma thread'i
    """
    # Signals
    reading_started = Signal(int)  # cihaz_id
    reading_completed = Signal(int, int, int)  # cihaz_id, toplam_kayit, yeni_kayit
    reading_failed = Signal(int, str)  # cihaz_id, hata_mesaji
    status_changed = Signal(int, str)  # cihaz_id, durum
    
    def __init__(self, cihaz_data: dict, manual: bool = False):
        super().__init__()
        self.cihaz_data = cihaz_data
        self.manual = manual
        self.is_running = True
        self._mutex = QMutex()
    
    def stop(self):
        """Thread'i durdur"""
        self._mutex.lock()
        self.is_running = False
        self._mutex.unlock()
    
    def run(self):
        """Ana okuma işlemi"""
        cihaz_id = self.cihaz_data['id']
        ip = self.cihaz_data['ip_adresi']
        port = int(self.cihaz_data.get('port', 4370))
        cihaz_tipi = self.cihaz_data.get('cihaz_tipi', 'ZK')
        
        start_time = datetime.now()
        
        try:
            logger.info(f"[Cihaz {cihaz_id}] Okuma başlatılıyor: {ip}:{port}")
            self.reading_started.emit(cihaz_id)
            self.status_changed.emit(cihaz_id, 'BAGLANTIYOR')
            
            if not ZK_AVAILABLE:
                raise Exception("pyzk kütüphanesi yüklü değil!")
            
            if cihaz_tipi != 'ZK':
                raise Exception(f"'{cihaz_tipi}' tipi henüz desteklenmiyor, sadece ZK")
            
            # ZK cihaza bağlan
            zk = ZK(ip, port=port, timeout=15, password=0, force_udp=False, ommit_ping=False)
            conn = zk.connect()
            
            logger.info(f"[Cihaz {cihaz_id}] Bağlantı kuruldu")
            self.status_changed.emit(cihaz_id, 'BAGLI')
            
            # Cihaz bilgilerini al
            try:
                device_name = conn.get_device_name()
                mac = conn.get_mac()
                logger.info(f"[Cihaz {cihaz_id}] {device_name} ({mac})")
            except Exception:
                pass
            
            # Cihazı devre dışı bırak (okuma sırasında)
            conn.disable_device()
            
            try:
                # Kullanıcı listesini çek (user_id → kart eşleştirmesi için)
                card_map = {}
                try:
                    users = conn.get_users()
                    if users:
                        for u in users:
                            uid = str(u.user_id).strip()
                            card = getattr(u, 'card', 0) or 0
                            name = getattr(u, 'name', '') or ''
                            if card and int(card) > 0:
                                card_map[uid] = str(int(card))
                            logger.debug(f"  ZK User: id={uid}, card={card}, name={name}")
                        logger.info(f"[Cihaz {cihaz_id}] {len(users)} kullanıcı, {len(card_map)} kart eşleştirmesi")
                except Exception as e:
                    logger.warning(f"[Cihaz {cihaz_id}] Kullanıcı listesi alınamadı: {e}")

                # Attendance kayıtlarını çek
                attendances = conn.get_attendance()
                toplam_kayit = len(attendances) if attendances else 0

                logger.info(f"[Cihaz {cihaz_id}] {toplam_kayit} kayıt okundu")

                # Kayıtları işle
                yeni_kayit = self._process_attendances(cihaz_id, attendances, card_map)
                
                # Başarı
                sure_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                self._log_okuma(cihaz_id, toplam_kayit, yeni_kayit, True, None, sure_ms)
                
                self.status_changed.emit(cihaz_id, 'AKTIF')
                self.reading_completed.emit(cihaz_id, toplam_kayit, yeni_kayit)
                
                logger.info(f"[Cihaz {cihaz_id}] Okuma tamamlandı: {yeni_kayit} yeni kayıt")
                
            finally:
                # Cihazı tekrar etkinleştir
                conn.enable_device()
                conn.disconnect()
        
        except (ZKErrorConnection, ConnectionError) as e:
            hata = f"Bağlantı hatası: {str(e)}"
            logger.error(f"[Cihaz {cihaz_id}] {hata}")
            self._log_okuma(cihaz_id, 0, 0, False, hata, None)
            self.status_changed.emit(cihaz_id, 'HATA')
            self.reading_failed.emit(cihaz_id, hata)
        
        except Exception as e:
            hata = f"Genel hata: {str(e)}"
            logger.error(f"[Cihaz {cihaz_id}] {hata}")
            self._log_okuma(cihaz_id, 0, 0, False, hata, None)
            self.status_changed.emit(cihaz_id, 'HATA')
            self.reading_failed.emit(cihaz_id, hata)
    
    def _process_attendances(self, cihaz_id: int, attendances: list, card_map: dict = None) -> int:
        """Attendance kayıtlarını işle ve veritabanına kaydet"""
        if not attendances:
            return 0

        if card_map is None:
            card_map = {}

        from core.database import get_db_connection

        yeni_kayit = 0
        conn = None

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # ── DİAGNOSTİK: Tablo yapısını ve kart değerlerini keşfet ──
            db_kart_map = {}  # kart_id → personel_id
            db_kart_map_lower = {}  # lowercase/trimmed → personel_id
            db_kart_map_numeric = {}  # sadece rakamlar → personel_id

            # 1) Tablo sütunlarını keşfet
            try:
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = 'ik' AND TABLE_NAME = 'personeller'
                    ORDER BY ORDINAL_POSITION
                """)
                columns_info = cursor.fetchall()
                logger.warning(f"[Cihaz {cihaz_id}] === ik.personeller TABLO YAPISI ({len(columns_info)} sütun) ===")
                kart_columns = []
                for col_name, col_type in columns_info:
                    col_lower = col_name.lower()
                    if any(k in col_lower for k in ['kart', 'card', 'rfid', 'pdks', 'badge']):
                        kart_columns.append(col_name)
                        logger.warning(f"  >>> KART SÜTUNU: {col_name} ({col_type})")
                    else:
                        logger.info(f"  sütun: {col_name} ({col_type})")

                if not kart_columns:
                    logger.warning(f"[Cihaz {cihaz_id}] !!! HİÇ KART SÜTUNU BULUNAMADI !!!")
                    # Tüm sütunları WARNING seviyesinde göster
                    for col_name, col_type in columns_info:
                        logger.warning(f"  sütun: {col_name} ({col_type})")
            except Exception as e:
                logger.warning(f"[Cihaz {cihaz_id}] Tablo yapısı sorgu hatası: {e}")
                kart_columns = ['kart_id']  # fallback

            # 2) İlk 10 personeli TÜM sütunlarla çek (veri yapısını anlamak için)
            try:
                cursor.execute("SELECT TOP 10 * FROM ik.personeller WHERE aktif_mi = 1")
                sample_rows = cursor.fetchall()
                col_names = [d[0] for d in cursor.description]
                logger.warning(f"[Cihaz {cihaz_id}] === ÖRNEK PERSONEL VERİSİ (ilk {len(sample_rows)}) ===")
                for sr in sample_rows:
                    row_dict = dict(zip(col_names, sr))
                    # Kart ile ilgili alanları ve kimlik bilgilerini göster
                    display_parts = []
                    for key in col_names:
                        kl = key.lower()
                        if any(k in kl for k in ['id', 'ad', 'soyad', 'sicil', 'kart', 'card', 'rfid', 'pdks', 'badge', 'numara', 'no']):
                            display_parts.append(f"{key}='{row_dict[key]}'")
                    logger.warning(f"  PERSONEL: {', '.join(display_parts)}")
            except Exception as e:
                logger.warning(f"[Cihaz {cihaz_id}] Örnek veri sorgu hatası: {e}")

            # 3) Kart sütunlarındaki değerleri haritaya al
            if not kart_columns:
                kart_columns = ['kart_id']  # en azından dene

            for kart_col in kart_columns:
                try:
                    cursor.execute(f"""
                        SELECT id, ad, soyad, sicil_no, [{kart_col}]
                        FROM ik.personeller
                        WHERE aktif_mi = 1 AND [{kart_col}] IS NOT NULL AND CAST([{kart_col}] AS NVARCHAR(MAX)) != ''
                    """)
                    db_rows = cursor.fetchall()
                    logger.warning(f"[Cihaz {cihaz_id}] === {kart_col} DEĞERLERİ ({len(db_rows)} personel) ===")
                    for dr in db_rows:
                        p_id, p_ad, p_soyad, p_sicil, p_kart = dr
                        p_kart_str = str(p_kart).strip() if p_kart else ''
                        logger.warning(f"  DB: id={p_id}, {p_ad} {p_soyad}, sicil={p_sicil}, {kart_col}='{p_kart_str}'")
                        if p_kart_str:
                            db_kart_map[p_kart_str] = p_id
                            db_kart_map_lower[p_kart_str.lower().strip()] = p_id
                            numeric_only = ''.join(c for c in p_kart_str if c.isdigit())
                            if numeric_only:
                                db_kart_map_numeric[numeric_only] = p_id
                                try:
                                    db_kart_map_numeric[str(int(numeric_only))] = p_id
                                except ValueError:
                                    pass
                except Exception as e:
                    logger.warning(f"[Cihaz {cihaz_id}] {kart_col} sorgu hatası: {e}")

            logger.warning(f"[Cihaz {cihaz_id}] === ZK CİHAZ KART HARİTASI ({len(card_map)} kayıt) ===")
            for uid, card in card_map.items():
                logger.warning(f"  ZK: user_id={uid} → kart={card}")

            logger.warning(f"[Cihaz {cihaz_id}] DB kart haritası: {len(db_kart_map)} tam, {len(db_kart_map_numeric)} numerik")

            # ── Eşleşme sayacı ──
            matched_count = 0
            unmatched_count = 0
            unmatched_set = set()  # Tekrar eden logları önle

            for att in attendances:
                try:
                    zk_user_id = str(att.user_id).strip()
                    timestamp = att.timestamp
                    punch = att.punch  # 0: Giriş, 1: Çıkış, vb.

                    # ZK user_id'den gerçek kart numarasını bul
                    kart_no = card_map.get(zk_user_id, zk_user_id)

                    # Personeli bul - birden fazla yöntemle dene
                    personel_id = None

                    # Yöntem 1: Bellek içi eşleştirme (tam eşleşme)
                    if kart_no in db_kart_map:
                        personel_id = db_kart_map[kart_no]

                    # Yöntem 2: ZK user_id ile eşleştir
                    if not personel_id and zk_user_id in db_kart_map:
                        personel_id = db_kart_map[zk_user_id]

                    # Yöntem 3: Numerik eşleştirme (sadece rakamlar)
                    if not personel_id:
                        kart_numeric = ''.join(c for c in kart_no if c.isdigit())
                        if kart_numeric and kart_numeric in db_kart_map_numeric:
                            personel_id = db_kart_map_numeric[kart_numeric]

                    # Yöntem 4: ZK user_id numerik eşleştirme
                    if not personel_id:
                        zk_numeric = ''.join(c for c in zk_user_id if c.isdigit())
                        if zk_numeric and zk_numeric in db_kart_map_numeric:
                            personel_id = db_kart_map_numeric[zk_numeric]

                    # Yöntem 5: Son 4-6 haneli kısmi eşleştirme
                    if not personel_id:
                        kart_numeric = ''.join(c for c in kart_no if c.isdigit())
                        for digit_count in [6, 5, 4]:
                            if len(kart_numeric) >= digit_count:
                                suffix = kart_numeric[-digit_count:]
                                for db_kart, db_pid in db_kart_map.items():
                                    db_numeric = ''.join(c for c in db_kart if c.isdigit())
                                    if len(db_numeric) >= digit_count and db_numeric[-digit_count:] == suffix:
                                        personel_id = db_pid
                                        break
                            if personel_id:
                                break

                    # Yöntem 6: SQL ile sicil_no eşleştirme
                    if not personel_id:
                        cursor.execute("""
                            SELECT id FROM ik.personeller
                            WHERE sicil_no = ? AND aktif_mi = 1
                        """, (zk_user_id,))
                        row = cursor.fetchone()
                        if row:
                            personel_id = row[0]

                    # Yöntem 7: SQL LIKE ile kısmi eşleştirme
                    if not personel_id:
                        try:
                            cursor.execute("""
                                SELECT id FROM ik.personeller
                                WHERE aktif_mi = 1
                                  AND (kart_id LIKE ? OR kart_id LIKE ? OR ? LIKE '%' + kart_id + '%')
                            """, (f'%{kart_no}%', f'%{zk_user_id}%', kart_no))
                            row = cursor.fetchone()
                            if row:
                                personel_id = row[0]
                        except Exception:
                            pass

                    if personel_id:
                        matched_count += 1
                    else:
                        unmatched_count += 1
                        unmatched_key = f"{zk_user_id}|{kart_no}"
                        if unmatched_key not in unmatched_set:
                            unmatched_set.add(unmatched_key)
                            logger.warning(f"[Cihaz {cihaz_id}] Personel bulunamadı: zk_user={zk_user_id}, kart={kart_no}")

                    # Hareket tipi belirle
                    hareket_tipi = 'GIRIS' if punch == 0 else 'CIKIS'

                    # Daha önce kaydedilmiş mi kontrol et
                    cursor.execute("""
                        SELECT COUNT(*) FROM ik.pdks_hareketler
                        WHERE cihaz_id = ?
                          AND kart_no = ?
                          AND ABS(DATEDIFF(SECOND, hareket_zamani, ?)) < 3
                    """, (cihaz_id, kart_no, timestamp))

                    if cursor.fetchone()[0] > 0:
                        continue  # Zaten var, atla

                    # Yeni kayıt ekle
                    cursor.execute("""
                        INSERT INTO ik.pdks_hareketler (
                            cihaz_id, personel_id, kart_no,
                            hareket_zamani, hareket_tipi, islendi_mi
                        )
                        VALUES (?, ?, ?, ?, ?, 0)
                    """, (cihaz_id, personel_id, kart_no, timestamp, hareket_tipi))

                    yeni_kayit += 1

                except Exception as e:
                    logger.warning(f"[Cihaz {cihaz_id}] Kayıt işleme hatası: {e}")
                    continue

            conn.commit()

            # ── Eşleşme istatistikleri ──
            logger.info(f"[Cihaz {cihaz_id}] === EŞLEŞME SONUÇLARI ===")
            logger.info(f"  Toplam kayıt: {len(attendances)}")
            logger.info(f"  Eşleşen: {matched_count}")
            logger.info(f"  Eşleşmeyen: {unmatched_count}")
            logger.info(f"  Yeni kayıt: {yeni_kayit}")
            if unmatched_set:
                logger.info(f"  Eşleşmeyen benzersiz kart sayısı: {len(unmatched_set)}")

        except Exception as e:
            logger.error(f"[Cihaz {cihaz_id}] Veritabanı hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

        return yeni_kayit
    
    def _log_okuma(self, cihaz_id: int, kayit_sayisi: int, yeni_kayit: int,
                   basarili: bool, hata_mesaji: Optional[str], sure_ms: Optional[int]):
        """Okuma işlemini logla"""
        from core.database import get_db_connection

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            okuma_tipi = 'MANUEL' if self.manual else 'OTOMATIK'

            cursor.execute("""
                EXEC ik.sp_pdks_okuma_log_ekle
                    @cihaz_id = ?,
                    @okuma_tipi = ?,
                    @kayit_sayisi = ?,
                    @yeni_kayit_sayisi = ?,
                    @basarili = ?,
                    @hata_mesaji = ?,
                    @sure_ms = ?
            """, (cihaz_id, okuma_tipi, kayit_sayisi, yeni_kayit,
                  basarili, hata_mesaji, sure_ms))

            conn.commit()

        except Exception as e:
            logger.error(f"[Cihaz {cihaz_id}] Log kaydetme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass


class PDKSReaderService(QThread):
    """
    Ana PDKS okuma servisi
    Tüm aktif cihazları periyodik olarak okur
    """
    # Signals
    service_started = Signal()
    service_stopped = Signal()
    device_read_started = Signal(int)  # cihaz_id
    device_read_completed = Signal(int, int, int)  # cihaz_id, toplam, yeni
    device_read_failed = Signal(int, str)  # cihaz_id, hata
    device_status_changed = Signal(int, str, str)  # cihaz_id, durum, mesaj
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.device_threads: Dict[int, DeviceReaderThread] = {}
        self.device_timers: Dict[int, QTimer] = {}
        self._mutex = Lock()
        
        # Config
        self.default_interval = 10  # dakika
        self.max_retry = 3
        self.retry_delay = 5  # saniye
    
    def start_service(self):
        """Servisi başlat"""
        if self.is_running:
            logger.warning("Servis zaten çalışıyor")
            return
        
        logger.info("PDKS Reader Service başlatılıyor...")
        self.is_running = True
        self.start()
    
    def stop_service(self):
        """Servisi durdur"""
        if not self.is_running:
            return
        
        logger.info("PDKS Reader Service durduruluyor...")
        self.is_running = False
        
        # Tüm thread'leri durdur
        with self._mutex:
            for thread in self.device_threads.values():
                thread.stop()
                thread.wait()
            self.device_threads.clear()
            
            # Timer'ları durdur
            for timer in self.device_timers.values():
                timer.stop()
            self.device_timers.clear()
        
        self.quit()
        self.wait()
        self.service_stopped.emit()
    
    def run(self):
        """Ana servis loop"""
        try:
            logger.info("PDKS Reader Service çalışıyor")
            self.service_started.emit()
            
            # Aktif cihazları yükle
            cihazlar = self._load_active_devices()
            
            if not cihazlar:
                logger.warning("Aktif cihaz bulunamadı")
                return
            
            logger.info(f"{len(cihazlar)} aktif cihaz bulundu")
            
            # Her cihaz için timer kur
            for cihaz in cihazlar:
                self._setup_device_timer(cihaz)
            
            # İlk okumayı hemen başlat
            for cihaz in cihazlar:
                self.read_device(cihaz['id'], manual=False)
            
            # Event loop
            self.exec()
            
        except Exception as e:
            logger.error(f"Servis hatası: {e}")
        finally:
            logger.info("PDKS Reader Service durduruldu")
    
    def _load_active_devices(self) -> List[dict]:
        """Aktif cihazları yükle"""
        from core.database import get_db_connection

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, cihaz_kodu, cihaz_adi, ip_adresi, port,
                       cihaz_tipi, okuma_periyodu
                FROM ik.pdks_cihazlari
                WHERE aktif_mi = 1
                ORDER BY cihaz_kodu
            """)

            columns = [col[0] for col in cursor.description]
            cihazlar = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return cihazlar

        except Exception as e:
            logger.error(f"Cihaz yükleme hatası: {e}")
            return []
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _setup_device_timer(self, cihaz: dict):
        """Cihaz için periyodik okuma timer'ı kur"""
        cihaz_id = cihaz['id']
        interval = cihaz.get('okuma_periyodu', self.default_interval) * 60 * 1000  # ms
        
        timer = QTimer()
        timer.timeout.connect(lambda: self.read_device(cihaz_id, manual=False))
        timer.start(interval)
        
        with self._mutex:
            self.device_timers[cihaz_id] = timer
        
        logger.info(f"[Cihaz {cihaz_id}] Timer kuruldu: {interval/1000/60:.0f} dakika")
    
    def read_device(self, cihaz_id: int, manual: bool = False):
        """Tek bir cihazı oku"""
        if not self.is_running and not manual:
            return
        
        # Cihaz verilerini yükle
        cihaz = self._get_device(cihaz_id)
        if not cihaz:
            logger.error(f"[Cihaz {cihaz_id}] Bulunamadı")
            return
        
        # Zaten okuma yapılıyor mu?
        with self._mutex:
            if cihaz_id in self.device_threads:
                if self.device_threads[cihaz_id].isRunning():
                    logger.warning(f"[Cihaz {cihaz_id}] Zaten okuma yapılıyor")
                    return
        
        # Yeni thread başlat
        thread = DeviceReaderThread(cihaz, manual=manual)
        
        # Signal bağlantıları
        thread.reading_started.connect(self.device_read_started)
        thread.reading_completed.connect(self._on_device_read_completed)
        thread.reading_failed.connect(self._on_device_read_failed)
        thread.status_changed.connect(self._on_device_status_changed)
        
        with self._mutex:
            self.device_threads[cihaz_id] = thread
        
        thread.start()
    
    def read_all_devices(self, manual: bool = True):
        """Tüm aktif cihazları oku"""
        cihazlar = self._load_active_devices()
        for cihaz in cihazlar:
            self.read_device(cihaz['id'], manual=manual)
    
    def _get_device(self, cihaz_id: int) -> Optional[dict]:
        """Cihaz bilgilerini getir"""
        from core.database import get_db_connection

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, cihaz_kodu, cihaz_adi, ip_adresi, port,
                       cihaz_tipi, okuma_periyodu
                FROM ik.pdks_cihazlari
                WHERE id = ? AND aktif_mi = 1
            """, (cihaz_id,))

            row = cursor.fetchone()

            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None

        except Exception as e:
            logger.error(f"Cihaz getirme hatası: {e}")
            return None
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _on_device_read_completed(self, cihaz_id: int, toplam: int, yeni: int):
        """Okuma tamamlandı"""
        self.device_read_completed.emit(cihaz_id, toplam, yeni)
        
        # Thread'i temizle
        with self._mutex:
            if cihaz_id in self.device_threads:
                self.device_threads[cihaz_id].wait()
                del self.device_threads[cihaz_id]
    
    def _on_device_read_failed(self, cihaz_id: int, hata: str):
        """Okuma başarısız"""
        self.device_read_failed.emit(cihaz_id, hata)
        
        # Thread'i temizle
        with self._mutex:
            if cihaz_id in self.device_threads:
                self.device_threads[cihaz_id].wait()
                del self.device_threads[cihaz_id]
    
    def _on_device_status_changed(self, cihaz_id: int, durum: str):
        """Cihaz durumu değişti"""
        from core.database import get_db_connection

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                EXEC ik.sp_pdks_cihaz_durum_guncelle
                    @cihaz_id = ?,
                    @durum = ?
            """, (cihaz_id, durum))

            conn.commit()

            self.device_status_changed.emit(cihaz_id, durum, '')

        except Exception as e:
            logger.error(f"Durum güncelleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass


# Global instance (singleton)
_service_instance: Optional[PDKSReaderService] = None
_service_lock = Lock()


def get_pdks_service() -> PDKSReaderService:
    """Global PDKS service instance'ı al (singleton)"""
    global _service_instance
    
    with _service_lock:
        if _service_instance is None:
            _service_instance = PDKSReaderService()
        return _service_instance


def start_pdks_service():
    """PDKS servisini başlat"""
    service = get_pdks_service()
    service.start_service()


def stop_pdks_service():
    """PDKS servisini durdur"""
    service = get_pdks_service()
    service.stop_service()


def is_service_running() -> bool:
    """Servis çalışıyor mu?"""
    global _service_instance
    return _service_instance is not None and _service_instance.is_running
