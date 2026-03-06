# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - PDKS Cihaz Ayarları (Güncellenmiş)
ZK kart okuma cihazları tanımlama, test etme ve servis yönetimi
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QSpinBox, QFrame, QGroupBox, QTextEdit,
    QSplitter, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection

# PDKS Reader Service (opsiyonel)
try:
    from core.pdks_reader_service import get_pdks_service, is_service_running
    PDKS_SERVICE_AVAILABLE = True
except ImportError:
    PDKS_SERVICE_AVAILABLE = False
    # Dummy fonksiyonlar
    def get_pdks_service():
        return None
    def is_service_running():
        return False

# ZK kütüphanesi opsiyonel
try:
    from zk import ZK
    ZK_AVAILABLE = True
except ImportError:
    ZK_AVAILABLE = False


class CihazTestThread(QThread):
    """Cihaz bağlantı testi için thread"""
    finished = Signal(bool, str)
    
    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = int(port)
    
    def run(self):
        if not ZK_AVAILABLE:
            self.finished.emit(False, "❌ 'pyzk' kütüphanesi yüklü değil!\n\npip install pyzk")
            return
        
        try:
            zk = ZK(self.ip, port=self.port, timeout=10)
            conn = zk.connect()
            
            device_name = conn.get_device_name()
            mac = conn.get_mac()
            
            conn.disable_device()
            try:
                users = conn.get_users()
                user_count = len(users)
            except:
                user_count = "Okunamadı"
            conn.enable_device()
            conn.disconnect()
            
            self.finished.emit(True, f"✅ BAĞLANTI BAŞARILI\n\n"
                                     f"Cihaz: {device_name}\n"
                                     f"MAC: {mac}\n"
                                     f"Kayıtlı Personel: {user_count}")
        except Exception as e:
            self.finished.emit(False, f"❌ BAĞLANTI HATASI\n\n{str(e)}")


class CihazDurumKarti(QFrame):
    """Cihaz durum özet kartı"""
    
    def __init__(self, cihaz_data: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.cihaz_data = cihaz_data
        self.theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        durum = self.cihaz_data.get('durum', 'PASIF')
        
        # Durum renkler
        durum_colors = {
            'AKTIF': ('#22c55e', 'rgba(34, 197, 94, 0.1)'),
            'BAGLI': ('#3b82f6', 'rgba(59, 130, 246, 0.1)'),
            'BAGLANTIYOR': ('#f59e0b', 'rgba(245, 158, 11, 0.1)'),
            'HATA': ('#ef4444', 'rgba(239, 68, 68, 0.1)'),
            'PASIF': ('#6b7280', 'rgba(107, 114, 128, 0.1)')
        }
        
        border_color, bg_color = durum_colors.get(durum, durum_colors['PASIF'])
        
        self.setStyleSheet(f"""
            CihazDurumKarti {{
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Başlık
        header = QHBoxLayout()
        
        kod_label = QLabel(self.cihaz_data.get('cihaz_kodu', ''))
        kod_label.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold; font-size: 14px;")
        header.addWidget(kod_label)
        
        header.addStretch()
        
        # Durum badge
        durum_label = QLabel(durum)
        durum_label.setStyleSheet(f"""
            background: {border_color};
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        """)
        header.addWidget(durum_label)
        
        layout.addLayout(header)
        
        # Ad
        ad_label = QLabel(self.cihaz_data.get('cihaz_adi', ''))
        ad_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px;")
        layout.addWidget(ad_label)
        
        # IP
        ip = self.cihaz_data.get('ip_adresi', '')
        port = self.cihaz_data.get('port', '4370')
        ip_label = QLabel(f"📡 {ip}:{port}")
        ip_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 11px;")
        layout.addWidget(ip_label)
        
        # İstatistikler
        stats_layout = QGridLayout()
        stats_layout.setSpacing(4)
        
        # Son okuma
        son_okuma = self.cihaz_data.get('son_okuma_zamani')
        if son_okuma:
            son_okuma_str = son_okuma.strftime('%d.%m %H:%M')
        else:
            son_okuma_str = 'Hiç'
        
        stats_layout.addWidget(QLabel("Son Okuma:"), 0, 0)
        son_okuma_label = QLabel(son_okuma_str)
        son_okuma_label.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold;")
        stats_layout.addWidget(son_okuma_label, 0, 1)
        
        # Toplam okuma
        toplam = self.cihaz_data.get('toplam_okuma', 0)
        basarili = self.cihaz_data.get('basarili_okuma', 0)
        
        stats_layout.addWidget(QLabel("Okuma:"), 1, 0)
        okuma_label = QLabel(f"{basarili}/{toplam}")
        okuma_label.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold;")
        stats_layout.addWidget(okuma_label, 1, 1)
        
        # Son kayıt
        son_kayit = self.cihaz_data.get('son_kayit_sayisi', 0)
        stats_layout.addWidget(QLabel("Kayıt:"), 2, 0)
        kayit_label = QLabel(str(son_kayit))
        kayit_label.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold;")
        stats_layout.addWidget(kayit_label, 2, 1)
        
        layout.addLayout(stats_layout)


class ServisKontrolPanel(QFrame):
    """PDKS Servis kontrol paneli"""
    
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.service = get_pdks_service() if PDKS_SERVICE_AVAILABLE else None
        self._setup_ui()
        
        if self.service:
            self._connect_signals()
        
        self._update_status()
        
        # Status update timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(2000)  # 2 saniyede bir
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            ServisKontrolPanel {{
                background: {self.theme.get('bg_card')};
                border: 2px solid {self.theme.get('primary')};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Başlık
        title = QLabel("🤖 PDKS Otomatik Okuma Servisi")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)
        
        # Durum
        status_layout = QHBoxLayout()
        
        self.status_indicator = QLabel("🔴")
        self.status_indicator.setFixedSize(24, 24)
        self.status_indicator.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel("Servis Durdu")
        self.status_label.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶️ Başlat")
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #16a34a; }}
        """)
        self.btn_start.clicked.connect(self._start_service)
        btn_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏸️ Durdur")
        self.btn_stop.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('danger')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #dc2626; }}
        """)
        self.btn_stop.clicked.connect(self._stop_service)
        btn_layout.addWidget(self.btn_stop)
        
        self.btn_read_all = QPushButton("🔄 Tümünü Oku")
        self.btn_read_all.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('info')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #0284c7; }}
        """)
        self.btn_read_all.clicked.connect(self._read_all)
        btn_layout.addWidget(self.btn_read_all)
        
        layout.addLayout(btn_layout)
        
        # Bilgi
        info = QLabel("ℹ️ Servis aktif cihazları otomatik olarak periyodik okur")
        info.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)
    
    def _connect_signals(self):
        """Servis signal'lerini bağla"""
        self.service.service_started.connect(self._on_service_started)
        self.service.service_stopped.connect(self._on_service_stopped)
        self.service.device_read_completed.connect(self._on_device_read_completed)
        self.service.device_read_failed.connect(self._on_device_read_failed)
    
    def _update_status(self):
        """Durum göstergesini güncelle"""
        running = is_service_running()
        
        if running:
            self.status_indicator.setText("🟢")
            self.status_label.setText("Servis Çalışıyor")
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
        else:
            self.status_indicator.setText("🔴")
            self.status_label.setText("Servis Durdu")
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
    
    def _start_service(self):
        """Servisi başlat"""
        try:
            self.service.start_service()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Servis başlatma hatası:\n{e}")
    
    def _stop_service(self):
        """Servisi durdur"""
        reply = QMessageBox.question(
            self, "Onay",
            "PDKS okuma servisini durdurmak istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.service.stop_service()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Servis durdurma hatası:\n{e}")
    
    def _read_all(self):
        """Tüm cihazları manuel oku"""
        try:
            self.service.read_all_devices(manual=True)
            QMessageBox.information(self, "Bilgi", "Tüm cihazlar için okuma başlatıldı")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Okuma başlatma hatası:\n{e}")
    
    def _on_service_started(self):
        """Servis başladı"""
        self._update_status()
    
    def _on_service_stopped(self):
        """Servis durdu"""
        self._update_status()
    
    def _on_device_read_completed(self, cihaz_id: int, toplam: int, yeni: int):
        """Cihaz okuma tamamlandı"""
        # Parent sayfayı güncelle
        if hasattr(self.parent(), '_load_data'):
            self.parent()._load_data()
    
    def _on_device_read_failed(self, cihaz_id: int, hata: str):
        """Cihaz okuma başarısız"""
        # Parent sayfayı güncelle
        if hasattr(self.parent(), '_load_data'):
            self.parent()._load_data()


class CihazDialog(QDialog):
    """Cihaz ekleme/düzenleme dialogu"""
    
    def __init__(self, theme: dict, parent=None, cihaz_id=None):
        super().__init__(parent)
        self.theme = theme
        self.cihaz_id = cihaz_id
        self.test_thread = None
        self.setWindowTitle("Cihaz Ekle" if not cihaz_id else "Cihaz Düzenle")
        self.setMinimumSize(500, 550)
        self.setModal(True)
        self._setup_ui()
        
        if cihaz_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QSpinBox, QComboBox {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
            QGroupBox {{
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Form
        form_group = QGroupBox("Cihaz Bilgileri")
        form_layout = QFormLayout()
        
        # Cihaz kodu
        self.txt_kod = QLineEdit()
        self.txt_kod.setMaxLength(20)
        self.txt_kod.setPlaceholderText("Örn: PDKS01, GIRIS01")
        form_layout.addRow("Cihaz Kodu*:", self.txt_kod)
        
        # Cihaz adı
        self.txt_ad = QLineEdit()
        self.txt_ad.setMaxLength(100)
        self.txt_ad.setPlaceholderText("Örn: Ana Giriş PDKS")
        form_layout.addRow("Cihaz Adı*:", self.txt_ad)
        
        # IP Adresi
        self.txt_ip = QLineEdit()
        self.txt_ip.setPlaceholderText("Örn: 192.168.1.148")
        form_layout.addRow("IP Adresi*:", self.txt_ip)
        
        # Port
        self.spin_port = QSpinBox()
        self.spin_port.setRange(1, 65535)
        self.spin_port.setValue(4370)
        form_layout.addRow("Port:", self.spin_port)
        
        # Cihaz tipi
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["ZK", "ANVIZ", "SUPREMA", "DIGER"])
        form_layout.addRow("Cihaz Tipi:", self.cmb_tip)
        
        # Lokasyon
        self.txt_lokasyon = QLineEdit()
        self.txt_lokasyon.setPlaceholderText("Örn: Ana Bina Giriş")
        form_layout.addRow("Lokasyon:", self.txt_lokasyon)
        
        # Okuma periyodu
        self.spin_periyot = QSpinBox()
        self.spin_periyot.setRange(1, 1440)  # 1-1440 dakika (24 saat)
        self.spin_periyot.setValue(10)
        self.spin_periyot.setSuffix(" dakika")
        form_layout.addRow("Okuma Periyodu:", self.spin_periyot)
        
        # Aktif
        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        self.chk_aktif.setStyleSheet(f"color: {self.theme.get('text')};")
        form_layout.addRow("", self.chk_aktif)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Test butonu
        test_layout = QHBoxLayout()
        self.btn_test = QPushButton("🔌 Bağlantıyı Test Et")
        self.btn_test.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('info')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
        """)
        self.btn_test.clicked.connect(self._test_connection)
        test_layout.addWidget(self.btn_test)
        test_layout.addStretch()
        layout.addLayout(test_layout)
        
        # Test sonucu
        self.lbl_test_result = QLabel("")
        self.lbl_test_result.setWordWrap(True)
        self.lbl_test_result.setStyleSheet(f"color: {self.theme.get('text_muted')}; padding: 10px;")
        layout.addWidget(self.lbl_test_result)
        
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 24px; border-radius: 6px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        """Mevcut cihaz verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cihaz_kodu, cihaz_adi, ip_adresi, port, cihaz_tipi, 
                       lokasyon, okuma_periyodu, aktif_mi
                FROM ik.pdks_cihazlari WHERE id = ?
            """, (self.cihaz_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_kod.setText(row[0] or "")
                self.txt_kod.setEnabled(False)
                self.txt_ad.setText(row[1] or "")
                self.txt_ip.setText(row[2] or "")
                self.spin_port.setValue(int(row[3]) if row[3] else 4370)
                
                idx = self.cmb_tip.findText(row[4] or "ZK")
                if idx >= 0:
                    self.cmb_tip.setCurrentIndex(idx)
                
                self.txt_lokasyon.setText(row[5] or "")
                self.spin_periyot.setValue(int(row[6]) if row[6] else 10)
                self.chk_aktif.setChecked(bool(row[7]))
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yükleme hatası: {str(e)}")
    
    def _test_connection(self):
        """Bağlantıyı test et"""
        ip = self.txt_ip.text().strip()
        port = self.spin_port.value()
        
        if not ip:
            QMessageBox.warning(self, "Uyarı", "Lütfen IP adresi girin!")
            return
        
        self.btn_test.setEnabled(False)
        self.lbl_test_result.setText("⏳ Test ediliyor...")
        
        self.test_thread = CihazTestThread(ip, port)
        self.test_thread.finished.connect(self._on_test_finished)
        self.test_thread.start()
    
    def _on_test_finished(self, success: bool, message: str):
        """Test tamamlandı"""
        self.btn_test.setEnabled(True)
        self.lbl_test_result.setText(message)
        
        if success:
            self.lbl_test_result.setStyleSheet(f"color: {self.theme.get('success')}; padding: 10px;")
        else:
            self.lbl_test_result.setStyleSheet(f"color: {self.theme.get('danger')}; padding: 10px;")
    
    def _save(self):
        """Kaydet"""
        kod = self.txt_kod.text().strip()
        ad = self.txt_ad.text().strip()
        ip = self.txt_ip.text().strip()
        port = self.spin_port.value()
        tip = self.cmb_tip.currentText()
        lokasyon = self.txt_lokasyon.text().strip()
        periyot = self.spin_periyot.value()
        aktif = self.chk_aktif.isChecked()
        
        if not kod or not ad or not ip:
            QMessageBox.warning(self, "Uyarı", "Zorunlu alanları doldurun!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.cihaz_id:
                # Güncelle
                cursor.execute("""
                    UPDATE ik.pdks_cihazlari
                    SET cihaz_adi = ?, ip_adresi = ?, port = ?, cihaz_tipi = ?,
                        lokasyon = ?, okuma_periyodu = ?, aktif_mi = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (ad, ip, port, tip, lokasyon, periyot, aktif, self.cihaz_id))
            else:
                # Ekle
                cursor.execute("""
                    INSERT INTO ik.pdks_cihazlari (
                        cihaz_kodu, cihaz_adi, ip_adresi, port, cihaz_tipi,
                        lokasyon, okuma_periyodu, aktif_mi
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (kod, ad, ip, port, tip, lokasyon, periyot, aktif))
            
            conn.commit()
            conn.close()
            
            self.accept()
            QMessageBox.information(self, "Başarılı", "Cihaz kaydedildi.")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class PDKSCihazAyarlariPage(BasePage):
    """PDKS Cihaz Ayarları Sayfası (Güncellenmiş)"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
        
        # Auto refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_data)
        self.refresh_timer.start(5000)  # 5 saniyede bir
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🔌 PDKS Cihaz Ayarları")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        header.addWidget(title)
        
        header.addStretch()
        
        # ZK kütüphane durumu
        if ZK_AVAILABLE:
            status = QLabel("✅ pyzk kütüphanesi yüklü")
            status.setStyleSheet(f"color: {self.theme.get('success')};")
        else:
            status = QLabel("⚠️ pyzk kütüphanesi yüklü değil (pip install pyzk)")
            status.setStyleSheet(f"color: {self.theme.get('warning')};")
        header.addWidget(status)
        
        layout.addLayout(header)
        
        # Servis Kontrol Paneli
        self.servis_panel = ServisKontrolPanel(self.theme, self)
        layout.addWidget(self.servis_panel)
        
        # Cihaz Durumu Kartları
        kartlar_frame = QFrame()
        kartlar_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        kartlar_layout = QVBoxLayout(kartlar_frame)
        kartlar_layout.setContentsMargins(12, 12, 12, 12)
        
        kartlar_title = QLabel("📊 Cihaz Durumu")
        kartlar_title.setStyleSheet(f"font-weight: bold; color: {self.theme.get('text')}; font-size: 14px;")
        kartlar_layout.addWidget(kartlar_title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        kartlar_container = QWidget()
        self.kartlar_layout = QHBoxLayout(kartlar_container)
        self.kartlar_layout.setSpacing(12)
        self.kartlar_layout.addStretch()
        
        scroll.setWidget(kartlar_container)
        kartlar_layout.addWidget(scroll)
        
        layout.addWidget(kartlar_frame)
        
        # Toolbar
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(16, 12, 16, 12)
        
        btn_ekle = QPushButton("➕ Yeni Cihaz")
        btn_ekle.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_ekle.clicked.connect(self._yeni_cihaz)
        toolbar.addWidget(btn_ekle)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._sil)
        toolbar.addWidget(btn_sil)
        
        toolbar.addStretch()
        
        btn_test = QPushButton("🔌 Seçiliyi Test Et")
        btn_test.setStyleSheet(f"background: {self.theme.get('info')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_test.clicked.connect(self._test_secili)
        toolbar.addWidget(btn_test)
        
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_yenile.clicked.connect(self._load_data)
        toolbar.addWidget(btn_yenile)
        
        layout.addWidget(toolbar_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kod", "Cihaz Adı", "IP Adresi", "Port", "Tip", "Lokasyon", 
            "Periyot", "Durum", "Aktif"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background: {self.theme.get('primary')};
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary')};
                font-weight: bold;
            }}
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(7, 80)
        self.table.setColumnWidth(8, 100)
        self.table.setColumnWidth(9, 60)
        
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
    
    def _load_data(self):
        """Cihaz listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, cihaz_kodu, cihaz_adi, ip_adresi, port, cihaz_tipi, lokasyon, 
                       okuma_periyodu, durum, aktif_mi, son_okuma_zamani, 
                       toplam_okuma, basarili_okuma, son_kayit_sayisi
                FROM ik.pdks_cihazlari
                ORDER BY cihaz_kodu
            """)
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            
            # Kartları temizle
            while self.kartlar_layout.count() > 1:  # Son stretch'i tut
                item = self.kartlar_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or ""))
                self.table.setItem(i, 4, QTableWidgetItem(str(row[4]) if row[4] else "4370"))
                self.table.setItem(i, 5, QTableWidgetItem(row[5] or ""))
                self.table.setItem(i, 6, QTableWidgetItem(row[6] or ""))
                self.table.setItem(i, 7, QTableWidgetItem(f"{row[7]} dk" if row[7] else "10 dk"))
                
                # Durum
                durum = row[8] or 'PASIF'
                durum_item = QTableWidgetItem(durum)
                durum_colors = {
                    'AKTIF': self.theme.get('success'),
                    'BAGLI': self.theme.get('info'),
                    'BAGLANTIYOR': self.theme.get('warning'),
                    'HATA': self.theme.get('danger'),
                    'PASIF': self.theme.get('text_muted')
                }
                durum_item.setForeground(QColor(durum_colors.get(durum, self.theme.get('text_muted'))))
                self.table.setItem(i, 8, durum_item)
                
                # Aktif
                aktif_item = QTableWidgetItem("✓" if row[9] else "✗")
                aktif_item.setForeground(QColor(self.theme.get('success') if row[9] else self.theme.get('danger')))
                self.table.setItem(i, 9, aktif_item)
                
                # Durum kartı (sadece aktif cihazlar için)
                if row[9]:  # aktif_mi
                    cihaz_data = {
                        'id': row[0],
                        'cihaz_kodu': row[1],
                        'cihaz_adi': row[2],
                        'ip_adresi': row[3],
                        'port': row[4],
                        'durum': durum,
                        'son_okuma_zamani': row[10],
                        'toplam_okuma': row[11] or 0,
                        'basarili_okuma': row[12] or 0,
                        'son_kayit_sayisi': row[13] or 0
                    }
                    kart = CihazDurumKarti(cihaz_data, self.theme)
                    self.kartlar_layout.insertWidget(self.kartlar_layout.count() - 1, kart)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _yeni_cihaz(self):
        """Yeni cihaz ekle"""
        dialog = CihazDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        """Seçili cihazı düzenle"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir cihaz seçin!")
            return
        
        cihaz_id = int(self.table.item(row, 0).text())
        dialog = CihazDialog(self.theme, self, cihaz_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _sil(self):
        """Seçili cihazı sil"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir cihaz seçin!")
            return
        
        cihaz_id = int(self.table.item(row, 0).text())
        kod = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Onay",
            f"'{kod}' cihazını silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ik.pdks_cihazlari WHERE id = ?", (cihaz_id,))
                conn.commit()
                conn.close()
                self._load_data()
                QMessageBox.information(self, "Başarılı", "Cihaz silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
    
    def _test_secili(self):
        """Seçili cihazı test et"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir cihaz seçin!")
            return
        
        cihaz_id = int(self.table.item(row, 0).text())
        dialog = CihazDialog(self.theme, self, cihaz_id)
        dialog._test_connection()
        dialog.exec()
