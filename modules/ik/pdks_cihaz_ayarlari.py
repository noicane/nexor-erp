# -*- coding: utf-8 -*-
"""
NEXOR ERP - PDKS Cihaz Ayarlari
=================================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
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
from core.nexor_brand import brand

# PDKS Reader Service (opsiyonel)
try:
    from core.pdks_reader_service import get_pdks_service, is_service_running
    PDKS_SERVICE_AVAILABLE = True
except ImportError:
    PDKS_SERVICE_AVAILABLE = False
    def get_pdks_service():
        return None
    def is_service_running():
        return False

# ZK kutuphanesi opsiyonel
try:
    from zk import ZK
    ZK_AVAILABLE = True
except ImportError:
    ZK_AVAILABLE = False


class CihazTestThread(QThread):
    """Cihaz baglanti testi icin thread"""
    finished = Signal(bool, str)

    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = int(port)

    def run(self):
        if not ZK_AVAILABLE:
            self.finished.emit(False, "'pyzk' kutuphanesi yuklu degil!\n\npip install pyzk")
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
            except Exception:
                user_count = "Okunamadi"
            conn.enable_device()
            conn.disconnect()

            self.finished.emit(True, f"BAGLANTI BASARILI\n\n"
                                     f"Cihaz: {device_name}\n"
                                     f"MAC: {mac}\n"
                                     f"Kayitli Personel: {user_count}")
        except Exception as e:
            self.finished.emit(False, f"BAGLANTI HATASI\n\n{str(e)}")


class CihazDurumKarti(QFrame):
    """Cihaz durum ozet karti"""

    def __init__(self, cihaz_data: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.cihaz_data = cihaz_data
        self.theme = theme
        self._setup_ui()

    def _setup_ui(self):
        durum = self.cihaz_data.get('durum', 'PASIF')

        # Durum renkler
        durum_colors = {
            'AKTIF': (brand.SUCCESS, brand.SUCCESS_SOFT),
            'BAGLI': (brand.INFO, brand.INFO_SOFT),
            'BAGLANTIYOR': (brand.WARNING, brand.WARNING_SOFT),
            'HATA': (brand.ERROR, brand.ERROR_SOFT),
            'PASIF': (brand.TEXT_MUTED, brand.BG_HOVER)
        }

        border_color, bg_color = durum_colors.get(durum, durum_colors['PASIF'])

        self.setStyleSheet(f"""
            CihazDurumKarti {{
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: {brand.R_LG}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_3, brand.SP_3, brand.SP_3, brand.SP_3)
        layout.setSpacing(brand.SP_2)

        # Baslik
        header = QHBoxLayout()

        kod_label = QLabel(self.cihaz_data.get('cihaz_kodu', ''))
        kod_label.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY_LG}px;"
        )
        header.addWidget(kod_label)

        header.addStretch()

        # Durum badge
        durum_label = QLabel(durum)
        durum_label.setStyleSheet(f"""
            background: {border_color};
            color: white;
            padding: {brand.SP_1}px {brand.SP_2}px;
            border-radius: {brand.R_SM}px;
            font-size: {brand.fs(10)}px;
            font-weight: {brand.FW_BOLD};
        """)
        header.addWidget(durum_label)

        layout.addLayout(header)

        # Ad
        ad_label = QLabel(self.cihaz_data.get('cihaz_adi', ''))
        ad_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;"
        )
        layout.addWidget(ad_label)

        # IP
        ip = self.cihaz_data.get('ip_adresi', '')
        port = self.cihaz_data.get('port', '4370')
        ip_label = QLabel(f"{ip}:{port}")
        ip_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px;"
        )
        layout.addWidget(ip_label)

        # Istatistikler
        stats_layout = QGridLayout()
        stats_layout.setSpacing(brand.SP_1)

        stat_label_css = f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"
        stat_value_css = f"color: {brand.TEXT}; font-weight: {brand.FW_BOLD}; font-size: {brand.FS_CAPTION}px;"

        # Son okuma
        son_okuma = self.cihaz_data.get('son_okuma_zamani')
        son_okuma_str = son_okuma.strftime('%d.%m %H:%M') if son_okuma else 'Hic'

        lbl_son = QLabel("Son Okuma:")
        lbl_son.setStyleSheet(stat_label_css)
        stats_layout.addWidget(lbl_son, 0, 0)
        son_okuma_label = QLabel(son_okuma_str)
        son_okuma_label.setStyleSheet(stat_value_css)
        stats_layout.addWidget(son_okuma_label, 0, 1)

        # Toplam okuma
        toplam = self.cihaz_data.get('toplam_okuma', 0)
        basarili = self.cihaz_data.get('basarili_okuma', 0)

        lbl_okuma = QLabel("Okuma:")
        lbl_okuma.setStyleSheet(stat_label_css)
        stats_layout.addWidget(lbl_okuma, 1, 0)
        okuma_label = QLabel(f"{basarili}/{toplam}")
        okuma_label.setStyleSheet(stat_value_css)
        stats_layout.addWidget(okuma_label, 1, 1)

        # Son kayit
        son_kayit = self.cihaz_data.get('son_kayit_sayisi', 0)
        lbl_kayit = QLabel("Kayit:")
        lbl_kayit.setStyleSheet(stat_label_css)
        stats_layout.addWidget(lbl_kayit, 2, 0)
        kayit_label = QLabel(str(son_kayit))
        kayit_label.setStyleSheet(stat_value_css)
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
        self.status_timer.start(2000)

    def _setup_ui(self):
        self.setStyleSheet(f"""
            ServisKontrolPanel {{
                background: {brand.BG_CARD};
                border: 2px solid {brand.PRIMARY};
                border-radius: {brand.R_LG}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_3)

        # Baslik
        title = QLabel("PDKS Otomatik Okuma Servisi")
        title.setStyleSheet(
            f"font-size: {brand.FS_HEADING_SM}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"color: {brand.PRIMARY};"
        )
        layout.addWidget(title)

        # Durum
        status_layout = QHBoxLayout()

        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(brand.sp(12), brand.sp(12))
        self.status_indicator.setStyleSheet(f"""
            background: {brand.ERROR};
            border-radius: {brand.sp(6)}px;
        """)
        status_layout.addWidget(self.status_indicator)

        self.status_label = QLabel("Servis Durdu")
        self.status_label.setStyleSheet(
            f"color: {brand.TEXT}; font-weight: {brand.FW_BOLD}; font-size: {brand.FS_BODY}px;"
        )
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)

        self.btn_start = QPushButton("Baslat")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFixedHeight(brand.sp(38))
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        self.btn_start.clicked.connect(self._start_service)
        btn_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Durdur")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setFixedHeight(brand.sp(38))
        self.btn_stop.setStyleSheet(f"""
            QPushButton {{
                background: {brand.ERROR};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QPushButton:hover {{ background: #DC2626; }}
        """)
        self.btn_stop.clicked.connect(self._stop_service)
        btn_layout.addWidget(self.btn_stop)

        self.btn_read_all = QPushButton("Tumunu Oku")
        self.btn_read_all.setCursor(Qt.PointingHandCursor)
        self.btn_read_all.setFixedHeight(brand.sp(38))
        self.btn_read_all.setStyleSheet(f"""
            QPushButton {{
                background: {brand.INFO};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QPushButton:hover {{ background: #2563EB; }}
        """)
        self.btn_read_all.clicked.connect(self._read_all)
        btn_layout.addWidget(self.btn_read_all)

        layout.addLayout(btn_layout)

        # Bilgi
        info = QLabel("Servis aktif cihazlari otomatik olarak periyodik okur")
        info.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px;"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

    def _connect_signals(self):
        """Servis signal'lerini bagla"""
        self.service.service_started.connect(self._on_service_started)
        self.service.service_stopped.connect(self._on_service_stopped)
        self.service.device_read_completed.connect(self._on_device_read_completed)
        self.service.device_read_failed.connect(self._on_device_read_failed)

    def _update_status(self):
        """Durum gostergesini guncelle"""
        running = is_service_running()

        if running:
            self.status_indicator.setStyleSheet(f"""
                background: {brand.SUCCESS};
                border-radius: {brand.sp(6)}px;
            """)
            self.status_label.setText("Servis Calisiyor")
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
        else:
            self.status_indicator.setStyleSheet(f"""
                background: {brand.ERROR};
                border-radius: {brand.sp(6)}px;
            """)
            self.status_label.setText("Servis Durdu")
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)

    def _start_service(self):
        """Servisi baslat"""
        try:
            self.service.start_service()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Servis baslatma hatasi:\n{e}")

    def _stop_service(self):
        """Servisi durdur"""
        reply = QMessageBox.question(
            self, "Onay",
            "PDKS okuma servisini durdurmak istediginize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.service.stop_service()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Servis durdurma hatasi:\n{e}")

    def _read_all(self):
        """Tum cihazlari manuel oku"""
        try:
            self.service.read_all_devices(manual=True)
            QMessageBox.information(self, "Bilgi", "Tum cihazlar icin okuma baslatildi")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Okuma baslatma hatasi:\n{e}")

    def _on_service_started(self):
        self._update_status()

    def _on_service_stopped(self):
        self._update_status()

    def _on_device_read_completed(self, cihaz_id: int, toplam: int, yeni: int):
        if hasattr(self.parent(), '_load_data'):
            self.parent()._load_data()

    def _on_device_read_failed(self, cihaz_id: int, hata: str):
        if hasattr(self.parent(), '_load_data'):
            self.parent()._load_data()


class CihazDialog(QDialog):
    """Cihaz ekleme/duzenleme dialogu — el kitabi uyumlu"""

    def __init__(self, theme: dict, parent=None, cihaz_id=None):
        super().__init__(parent)
        self.theme = theme
        self.cihaz_id = cihaz_id
        self.test_thread = None
        self.setWindowTitle("Cihaz Ekle" if not cihaz_id else "Cihaz Duzenle")
        self.setMinimumSize(brand.sp(500), brand.sp(550))
        self.setModal(True)
        self._setup_ui()

        if cihaz_id:
            self._load_data()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QSpinBox, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {brand.PRIMARY};
            }}
            QGroupBox {{
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                margin-top: {brand.SP_5}px;
                padding: {brand.SP_5}px;
                padding-top: {brand.SP_8}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {brand.SP_4}px;
                top: {brand.SP_2}px;
                padding: 0 {brand.SP_2}px;
                color: {brand.TEXT_MUTED};
                background: {brand.BG_MAIN};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_4)

        # Form
        form_group = QGroupBox("Cihaz Bilgileri")
        form_layout = QFormLayout()
        form_layout.setSpacing(brand.SP_2)

        # Cihaz kodu
        self.txt_kod = QLineEdit()
        self.txt_kod.setMaxLength(20)
        self.txt_kod.setPlaceholderText("Orn: PDKS01, GIRIS01")
        form_layout.addRow("Cihaz Kodu*:", self.txt_kod)

        # Cihaz adi
        self.txt_ad = QLineEdit()
        self.txt_ad.setMaxLength(100)
        self.txt_ad.setPlaceholderText("Orn: Ana Giris PDKS")
        form_layout.addRow("Cihaz Adi*:", self.txt_ad)

        # IP Adresi
        self.txt_ip = QLineEdit()
        self.txt_ip.setPlaceholderText("Orn: 192.168.1.148")
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
        self.txt_lokasyon.setPlaceholderText("Orn: Ana Bina Giris")
        form_layout.addRow("Lokasyon:", self.txt_lokasyon)

        # Okuma periyodu
        self.spin_periyot = QSpinBox()
        self.spin_periyot.setRange(1, 1440)
        self.spin_periyot.setValue(10)
        self.spin_periyot.setSuffix(" dakika")
        form_layout.addRow("Okuma Periyodu:", self.spin_periyot)

        # Aktif
        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        self.chk_aktif.setStyleSheet(f"color: {brand.TEXT};")
        form_layout.addRow("", self.chk_aktif)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Test butonu
        test_layout = QHBoxLayout()
        self.btn_test = QPushButton("Baglantiyi Test Et")
        self.btn_test.setCursor(Qt.PointingHandCursor)
        self.btn_test.setFixedHeight(brand.sp(38))
        self.btn_test.setStyleSheet(f"""
            QPushButton {{
                background: {brand.INFO};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QPushButton:hover {{ background: #2563EB; }}
        """)
        self.btn_test.clicked.connect(self._test_connection)
        test_layout.addWidget(self.btn_test)
        test_layout.addStretch()
        layout.addLayout(test_layout)

        # Test sonucu
        self.lbl_test_result = QLabel("")
        self.lbl_test_result.setWordWrap(True)
        self.lbl_test_result.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"padding: {brand.SP_3}px; "
            f"font-size: {brand.FS_BODY_SM}px;"
        )
        layout.addWidget(self.lbl_test_result)

        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_iptal = QPushButton("Iptal")
        btn_iptal.setCursor(Qt.PointingHandCursor)
        btn_iptal.setFixedHeight(brand.sp(38))
        btn_iptal.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
        """)
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)

        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setCursor(Qt.PointingHandCursor)
        btn_kaydet.setFixedHeight(brand.sp(38))
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)

        layout.addLayout(btn_layout)

    def _load_data(self):
        """Mevcut cihaz verilerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cihaz_kodu, cihaz_adi, ip_adresi, port, cihaz_tipi,
                       lokasyon, okuma_periyodu, aktif_mi
                FROM ik.pdks_cihazlari WHERE id = ?
            """, (self.cihaz_id,))
            row = cursor.fetchone()

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
            QMessageBox.critical(self, "Hata", f"Veri yukleme hatasi: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _test_connection(self):
        """Baglantiyi test et"""
        ip = self.txt_ip.text().strip()
        port = self.spin_port.value()

        if not ip:
            QMessageBox.warning(self, "Uyari", "Lutfen IP adresi girin!")
            return

        self.btn_test.setEnabled(False)
        self.lbl_test_result.setText("Test ediliyor...")
        self.lbl_test_result.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; padding: {brand.SP_3}px; font-size: {brand.FS_BODY_SM}px;"
        )

        self.test_thread = CihazTestThread(ip, port)
        self.test_thread.finished.connect(self._on_test_finished)
        self.test_thread.start()

    def _on_test_finished(self, success: bool, message: str):
        """Test tamamlandi"""
        self.btn_test.setEnabled(True)
        self.lbl_test_result.setText(message)

        if success:
            self.lbl_test_result.setStyleSheet(
                f"color: {brand.SUCCESS}; padding: {brand.SP_3}px; font-size: {brand.FS_BODY_SM}px;"
            )
        else:
            self.lbl_test_result.setStyleSheet(
                f"color: {brand.ERROR}; padding: {brand.SP_3}px; font-size: {brand.FS_BODY_SM}px;"
            )

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
            QMessageBox.warning(self, "Uyari", "Zorunlu alanlari doldurun!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            if self.cihaz_id:
                cursor.execute("""
                    UPDATE ik.pdks_cihazlari
                    SET cihaz_adi = ?, ip_adresi = ?, port = ?, cihaz_tipi = ?,
                        lokasyon = ?, okuma_periyodu = ?, aktif_mi = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (ad, ip, port, tip, lokasyon, periyot, aktif, self.cihaz_id))
            else:
                cursor.execute("""
                    INSERT INTO ik.pdks_cihazlari (
                        cihaz_kodu, cihaz_adi, ip_adresi, port, cihaz_tipi,
                        lokasyon, okuma_periyodu, aktif_mi
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (kod, ad, ip, port, tip, lokasyon, periyot, aktif))

            conn.commit()

            self.accept()
            QMessageBox.information(self, "Basarili", "Cihaz kaydedildi.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatasi: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class PDKSCihazAyarlariPage(BasePage):
    """PDKS Cihaz Ayarlari Sayfasi — el kitabi uyumlu"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()

        # Auto refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_data)
        self.refresh_timer.start(5000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # Header
        header = self.create_page_header(
            "PDKS Cihaz Ayarlari",
            "ZK kart okuma cihazlari tanimlama ve yonetim"
        )

        # ZK kutuphane durumu
        if ZK_AVAILABLE:
            status = QLabel("pyzk yuklu")
            status.setStyleSheet(
                f"color: {brand.SUCCESS}; font-size: {brand.FS_BODY_SM}px;"
            )
        else:
            status = QLabel("pyzk yuklu degil (pip install pyzk)")
            status.setStyleSheet(
                f"color: {brand.WARNING}; font-size: {brand.FS_BODY_SM}px;"
            )
        header.addWidget(status)

        layout.addLayout(header)

        # Servis Kontrol Paneli
        self.servis_panel = ServisKontrolPanel(self.theme, self)
        layout.addWidget(self.servis_panel)

        # Cihaz Durumu Kartlari
        kartlar_frame = QFrame()
        kartlar_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        kartlar_layout = QVBoxLayout(kartlar_frame)
        kartlar_layout.setContentsMargins(brand.SP_3, brand.SP_3, brand.SP_3, brand.SP_3)

        kartlar_title = QLabel("Cihaz Durumu")
        kartlar_title.setStyleSheet(
            f"font-weight: {brand.FW_BOLD}; "
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_BODY_LG}px;"
        )
        kartlar_layout.addWidget(kartlar_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        kartlar_container = QWidget()
        self.kartlar_layout = QHBoxLayout(kartlar_container)
        self.kartlar_layout.setSpacing(brand.SP_3)
        self.kartlar_layout.addStretch()

        scroll.setWidget(kartlar_container)
        kartlar_layout.addWidget(scroll)

        layout.addWidget(kartlar_frame)

        # Toolbar
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)
        toolbar.setSpacing(brand.SP_3)

        btn_ekle = self.create_success_button("Yeni Cihaz")
        btn_ekle.clicked.connect(self._yeni_cihaz)
        toolbar.addWidget(btn_ekle)

        btn_duzenle = QPushButton("Duzenle")
        btn_duzenle.setCursor(Qt.PointingHandCursor)
        btn_duzenle.setFixedHeight(brand.sp(38))
        btn_duzenle.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
        """)
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar.addWidget(btn_duzenle)

        btn_sil = self.create_danger_button("Sil")
        btn_sil.clicked.connect(self._sil)
        toolbar.addWidget(btn_sil)

        toolbar.addStretch()

        btn_test = QPushButton("Seciliyi Test Et")
        btn_test.setCursor(Qt.PointingHandCursor)
        btn_test.setFixedHeight(brand.sp(38))
        btn_test.setStyleSheet(f"""
            QPushButton {{
                background: {brand.INFO};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #2563EB; }}
        """)
        btn_test.clicked.connect(self._test_secili)
        toolbar.addWidget(btn_test)

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        toolbar.addWidget(btn_yenile)

        layout.addWidget(toolbar_frame)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kod", "Cihaz Adi", "IP Adresi", "Port", "Tip", "Lokasyon",
            "Periyot", "Durum", "Aktif"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_3}px {brand.SP_4}px;
                border-bottom: 1px solid {brand.BORDER};
                color: {brand.TEXT};
            }}
            QTableWidget::item:alternate {{ background: {brand.BG_MAIN}; }}
            QTableWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_4}px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.setColumnWidth(1, brand.sp(80))
        self.table.setColumnWidth(3, brand.sp(120))
        self.table.setColumnWidth(4, brand.sp(60))
        self.table.setColumnWidth(5, brand.sp(80))
        self.table.setColumnWidth(7, brand.sp(80))
        self.table.setColumnWidth(8, brand.sp(100))
        self.table.setColumnWidth(9, brand.sp(60))

        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)

    def _load_data(self):
        """Cihaz listesini yukle"""
        conn = None
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

            self.table.setRowCount(len(rows))

            # Kartlari temizle
            while self.kartlar_layout.count() > 1:
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
                    'AKTIF': brand.SUCCESS,
                    'BAGLI': brand.INFO,
                    'BAGLANTIYOR': brand.WARNING,
                    'HATA': brand.ERROR,
                    'PASIF': brand.TEXT_MUTED
                }
                durum_item.setForeground(QColor(durum_colors.get(durum, brand.TEXT_MUTED)))
                self.table.setItem(i, 8, durum_item)

                # Aktif
                aktif_item = QTableWidgetItem("Evet" if row[9] else "Hayir")
                aktif_item.setForeground(QColor(brand.SUCCESS if row[9] else brand.ERROR))
                self.table.setItem(i, 9, aktif_item)

                # Durum karti (sadece aktif cihazlar icin)
                if row[9]:
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
            QMessageBox.critical(self, "Hata", f"Veri yuklenirken hata: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _yeni_cihaz(self):
        """Yeni cihaz ekle"""
        dialog = CihazDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _duzenle(self):
        """Secili cihazi duzenle"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir cihaz secin!")
            return

        cihaz_id = int(self.table.item(row, 0).text())
        dialog = CihazDialog(self.theme, self, cihaz_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _sil(self):
        """Secili cihazi sil"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir cihaz secin!")
            return

        cihaz_id = int(self.table.item(row, 0).text())
        kod = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Onay",
            f"'{kod}' cihazini silmek istediginize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ik.pdks_cihazlari WHERE id = ?", (cihaz_id,))
                conn.commit()
                self._load_data()
                QMessageBox.information(self, "Basarili", "Cihaz silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatasi: {str(e)}")
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    def _test_secili(self):
        """Secili cihazi test et"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir cihaz secin!")
            return

        cihaz_id = int(self.table.item(row, 0).text())
        dialog = CihazDialog(self.theme, self, cihaz_id)
        dialog._test_connection()
        dialog.exec()
