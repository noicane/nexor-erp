# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Final Kalite Kontrol Sayfası (v3)
=====================================================
Yeni akış:
- Personel kart/barkod/sicil ile giriş yapar
- Yetki kontrolü (Polivelans: "Finak Kalite", seviye >= 3)
- FKK deposundaki bekleyen ürünleri görür
- Ürün seçip kontrole başlar
- Sağlam → SEVK, Hatalı → RED depoya
- Etiket yazdırma (Godex EZPL)
"""
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QSpinBox, QWidget, QGridLayout, QStackedWidget,
    QSplitter, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer, QTime, QEvent
from PySide6.QtGui import QColor, QFont, QPixmap

from components.base_page import BasePage
from core.database import get_db_connection
from core.rfid_reader import RFIDCardReader
from config import NAS_PATHS

ETIKET_YAZICI = "Godex G500"


class EtiketOnizlemeDialog(QDialog):
    def __init__(self, theme: dict, etiket_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.etiket_data = etiket_data
        self.setWindowTitle("Etiket Önizleme")
        self.setMinimumSize(450, 350)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main')}; }} QLabel {{ color: {self.theme.get('text')}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        etiket_frame = QFrame()
        etiket_frame.setFixedSize(400, 200)
        etiket_frame.setStyleSheet(f"QFrame {{ background: white; border: 2px solid {self.theme.get('border')}; border-radius: 8px; }}")

        etiket_layout = QVBoxLayout(etiket_frame)
        etiket_layout.setContentsMargins(15, 10, 15, 10)
        etiket_layout.setSpacing(4)

        musteri_lbl = QLabel(self.etiket_data.get('musteri', '')[:35])
        musteri_lbl.setStyleSheet("color: #000; font-size: 16px; font-weight: bold;")
        musteri_lbl.setAlignment(Qt.AlignCenter)
        etiket_layout.addWidget(musteri_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #333;")
        line.setFixedHeight(1)
        etiket_layout.addWidget(line)

        urun_lbl = QLabel(f"Ürün: {self.etiket_data.get('urun', '')[:30]}")
        urun_lbl.setStyleSheet("color: #000; font-size: 12px;")
        etiket_layout.addWidget(urun_lbl)

        lot_lbl = QLabel(f"Lot: {self.etiket_data.get('lot_no', '')}")
        lot_lbl.setStyleSheet("color: #000; font-size: 12px; font-weight: bold;")
        etiket_layout.addWidget(lot_lbl)

        info_layout = QHBoxLayout()
        adet_lbl = QLabel(f"Adet: {self.etiket_data.get('adet', 0)}")
        adet_lbl.setStyleSheet("color: #000; font-size: 12px;")
        info_layout.addWidget(adet_lbl)
        tarih_lbl = QLabel(f"Tarih: {self.etiket_data.get('tarih', '')}")
        tarih_lbl.setStyleSheet("color: #000; font-size: 12px;")
        info_layout.addWidget(tarih_lbl)
        etiket_layout.addLayout(info_layout)

        kontrol_lbl = QLabel(f"Kontrol: {self.etiket_data.get('kontrolcu', '')[:20]}")
        kontrol_lbl.setStyleSheet("color: #000; font-size: 11px;")
        etiket_layout.addWidget(kontrol_lbl)

        barkod_lbl = QLabel("|||||||||||||||||||||||||||||||||||")
        barkod_lbl.setStyleSheet("color: #000; font-size: 20px; font-family: monospace;")
        barkod_lbl.setAlignment(Qt.AlignCenter)
        etiket_layout.addWidget(barkod_lbl)

        barkod_text = QLabel(self.etiket_data.get('lot_no', ''))
        barkod_text.setStyleSheet("color: #000; font-size: 10px;")
        barkod_text.setAlignment(Qt.AlignCenter)
        etiket_layout.addWidget(barkod_text)

        layout.addWidget(etiket_frame, alignment=Qt.AlignCenter)

        info = QLabel("100 x 50 mm")
        info.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 11px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 20px;")
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)
        yazdir_btn = QPushButton("Yazdır")
        yazdir_btn.setStyleSheet(f"background: {self.theme.get('success')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        yazdir_btn.clicked.connect(self.accept)
        btn_layout.addWidget(yazdir_btn)
        layout.addLayout(btn_layout)


class FinalKontrolDialog(QDialog):
    def __init__(self, gorev_data, personel_data, theme, parent=None):
        super().__init__(parent)
        self.gorev = gorev_data
        self.personel = personel_data
        self.theme = theme
        self.result_data = None
        self.baslangic_zamani = datetime.now()
        self.hata_listesi = []
        self.hata_turleri = []
        self.setWindowTitle(f"Kontrol - {gorev_data.get('is_emri_no', '')}")
        self.setMinimumSize(700, 620)
        self._load_hata_turleri()
        self._setup_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_sure)
        self.timer.start(1000)

    def _load_hata_turleri(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.hata_turleri WHERE aktif_mi = 1 ORDER BY sira_no, kod")
            self.hata_turleri = [{'id': r[0], 'kod': r[1], 'ad': r[2]} for r in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"Hata türleri yükleme hatası: {e}")
            self.hata_turleri = []

    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main')}; }} QLabel {{ color: {self.theme.get('text')}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        input_style = f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;"

        header = QHBoxLayout()
        title = QLabel("Final Kalite Kontrol")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme.get('primary')};")
        header.addWidget(title)
        header.addStretch()
        self.sure_label = QLabel("00:00")
        self.sure_label.setStyleSheet(f"color: {self.theme.get('text')}; font-size: 18px; font-weight: bold; background: {self.theme.get('bg_card')}; padding: 6px 12px; border-radius: 6px;")
        header.addWidget(self.sure_label)
        layout.addLayout(header)

        info_frame = QFrame()
        info_frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; padding: 10px; }}")
        info_grid = QGridLayout(info_frame)
        info_grid.addWidget(QLabel("İş Emri:"), 0, 0)
        info_grid.addWidget(QLabel(f"<b>{self.gorev.get('is_emri_no', '')}</b>"), 0, 1)
        info_grid.addWidget(QLabel("Kontrol Eden:"), 0, 2)
        info_grid.addWidget(QLabel(f"<b>{self.personel.get('ad_soyad', '')}</b>"), 0, 3)
        info_grid.addWidget(QLabel("Lot:"), 1, 0)
        info_grid.addWidget(QLabel(self.gorev.get('lot_no', '')), 1, 1)
        info_grid.addWidget(QLabel("Müşteri:"), 1, 2)
        info_grid.addWidget(QLabel((self.gorev.get('cari_unvani', '') or '')[:25]), 1, 3)
        layout.addWidget(info_frame)

        kontrol_frame = QFrame()
        kontrol_frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; padding: 12px; }}")
        kontrol_layout = QGridLayout(kontrol_frame)
        kontrol_layout.setSpacing(10)
        kontrol_adet = self.gorev.get('kontrol_adet', 0) or self.gorev.get('miktar', 0)

        kontrol_layout.addWidget(QLabel("Kontrol Edilecek:"), 0, 0)
        toplam_lbl = QLabel(f"<b>{kontrol_adet:,}</b> adet")
        toplam_lbl.setStyleSheet(f"color: {self.theme.get('primary')};")
        kontrol_layout.addWidget(toplam_lbl, 0, 1)

        kontrol_layout.addWidget(QLabel("Kontrol Edilen:"), 1, 0)
        self.kontrol_spin = QSpinBox()
        self.kontrol_spin.setRange(0, int(kontrol_adet))
        self.kontrol_spin.setValue(int(kontrol_adet))
        self.kontrol_spin.setStyleSheet(f"QSpinBox {{ {input_style} }}")
        self.kontrol_spin.valueChanged.connect(self._update_hesap)
        kontrol_layout.addWidget(self.kontrol_spin, 1, 1)

        kontrol_layout.addWidget(QLabel("Sağlam Adet:"), 2, 0)
        self.saglam_spin = QSpinBox()
        self.saglam_spin.setRange(0, int(kontrol_adet))
        self.saglam_spin.setValue(int(kontrol_adet))
        self.saglam_spin.setStyleSheet(f"QSpinBox {{ {input_style} }}")
        self.saglam_spin.valueChanged.connect(self._update_hesap)
        kontrol_layout.addWidget(self.saglam_spin, 2, 1)

        kontrol_layout.addWidget(QLabel("Hatalı Adet:"), 3, 0)
        self.hatali_lbl = QLabel("0")
        self.hatali_lbl.setStyleSheet(f"color: {self.theme.get('error')}; font-size: 16px; font-weight: bold;")
        kontrol_layout.addWidget(self.hatali_lbl, 3, 1)
        layout.addWidget(kontrol_frame)

        hata_frame = QFrame()
        hata_frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; padding: 10px; }}")
        hata_layout = QVBoxLayout(hata_frame)
        hata_header = QHBoxLayout()
        hata_header.addWidget(QLabel("Red Sebepleri:"))
        hata_header.addStretch()
        self.hata_combo = QComboBox()
        self.hata_combo.setMinimumWidth(200)
        self.hata_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        for hata in self.hata_turleri:
            self.hata_combo.addItem(f"{hata['kod']} - {hata['ad']}", hata['id'])
        hata_header.addWidget(self.hata_combo)
        self.hata_adet_spin = QSpinBox()
        self.hata_adet_spin.setRange(1, 99999)
        self.hata_adet_spin.setValue(1)
        self.hata_adet_spin.setStyleSheet(f"QSpinBox {{ {input_style} min-width: 70px; }}")
        hata_header.addWidget(self.hata_adet_spin)
        hata_ekle_btn = QPushButton("+ Ekle")
        hata_ekle_btn.setStyleSheet(f"QPushButton {{ background: {self.theme.get('warning')}; color: white; border: none; border-radius: 6px; padding: 8px 14px; font-weight: bold; }}")
        hata_ekle_btn.clicked.connect(self._hata_ekle)
        hata_header.addWidget(hata_ekle_btn)
        hata_layout.addLayout(hata_header)

        self.hata_list = QListWidget()
        self.hata_list.setMaximumHeight(80)
        self.hata_list.setStyleSheet(f"QListWidget {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; }}")
        hata_layout.addWidget(self.hata_list)

        hata_sil_btn = QPushButton("Seçili Hatayı Sil")
        hata_sil_btn.setStyleSheet(f"QPushButton {{ background: {self.theme.get('error')}; color: white; border: none; border-radius: 6px; padding: 6px 12px; }}")
        hata_sil_btn.clicked.connect(self._hata_sil)
        hata_layout.addWidget(hata_sil_btn)
        layout.addWidget(hata_frame)

        not_layout = QHBoxLayout()
        not_layout.addWidget(QLabel("Not:"))
        self.not_input = QLineEdit()
        self.not_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        not_layout.addWidget(self.not_input)
        layout.addLayout(not_layout)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"QPushButton {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; padding: 12px 20px; }}")
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)
        kaydet_btn = QPushButton("Kaydet ve Etiket Bas")
        kaydet_btn.setStyleSheet(f"QPushButton {{ background: {self.theme.get('success')}; color: white; border: none; border-radius: 8px; padding: 12px 20px; font-weight: bold; }}")
        kaydet_btn.clicked.connect(self._save)
        btn_layout.addWidget(kaydet_btn)
        layout.addLayout(btn_layout)

    def _update_sure(self):
        gecen = datetime.now() - self.baslangic_zamani
        dk = int(gecen.total_seconds() // 60)
        sn = int(gecen.total_seconds() % 60)
        self.sure_label.setText(f"{dk:02d}:{sn:02d}")

    def _update_hesap(self):
        kontrol = self.kontrol_spin.value()
        saglam = self.saglam_spin.value()
        if saglam > kontrol:
            self.saglam_spin.setValue(kontrol)
            saglam = kontrol
        self.hatali_lbl.setText(str(kontrol - saglam))

    def _hata_ekle(self):
        hata_id = self.hata_combo.currentData()
        hata_adi = self.hata_combo.currentText()
        adet = self.hata_adet_spin.value()
        self.hata_listesi.append({'hata_turu_id': hata_id, 'hata_adi': hata_adi, 'adet': adet})
        self.hata_list.addItem(QListWidgetItem(f"{hata_adi} - {adet} adet"))
        toplam_hata = sum(h['adet'] for h in self.hata_listesi)
        kontrol = self.kontrol_spin.value()
        self.saglam_spin.setValue(max(0, kontrol - toplam_hata))

    def _hata_sil(self):
        current = self.hata_list.currentRow()
        if current >= 0:
            self.hata_list.takeItem(current)
            self.hata_listesi.pop(current)
            toplam_hata = sum(h['adet'] for h in self.hata_listesi)
            kontrol = self.kontrol_spin.value()
            self.saglam_spin.setValue(max(0, kontrol - toplam_hata))

    def _save(self):
        self.timer.stop()
        gecen = datetime.now() - self.baslangic_zamani
        kontrol = self.kontrol_spin.value()
        saglam = self.saglam_spin.value()
        hatali = kontrol - saglam
        if hatali > 0:
            hata_toplam = sum(h['adet'] for h in self.hata_listesi)
            if hata_toplam != hatali:
                QMessageBox.warning(self, "Uyarı", f"Hata adetleri toplamı ({hata_toplam}) ile hatalı adet ({hatali}) eşleşmiyor!")
                self.timer.start(1000)
                return
        self.result_data = {
            'kontrol_miktar': kontrol, 'saglam_miktar': saglam, 'hatali_miktar': hatali,
            'kontrolcu_id': self.personel.get('uuid'), 'kontrolcu_ad': self.personel.get('ad_soyad'),
            'not': self.not_input.text(), 'sure_saniye': int(gecen.total_seconds()), 'hata_listesi': self.hata_listesi
        }
        self.accept()


# =============================================================================
# ANA SAYFA
# =============================================================================

class KaliteFinalKontrolPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.personel_data = None
        self._products = []
        self._selected_product = None
        self._ambalaj_full_paths = [None, None, None]

        # RFID kart okuyucu (lokal - global servis yoksa fallback)
        self._rfid_reader = RFIDCardReader(self)
        self._rfid_reader.card_detected.connect(self._on_card_detected)

        # Global RFID servisine bağlan (lazy load nedeniyle showEvent'te de denenecek)
        self._global_rfid_connected = False
        self._try_connect_global_rfid()

        self._setup_ui()

        # Timerlar
        self.saat_timer = QTimer()
        self.saat_timer.timeout.connect(self._update_time)
        self.saat_timer.start(1000)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(30000)

    # =========================================================================
    # UI SETUP
    # =========================================================================

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stacked = QStackedWidget()
        layout.addWidget(self.stacked)

        # Sayfa 0: Giriş Paneli
        self._setup_login_page()
        # Sayfa 1: Ana Ekran
        self._setup_main_page()

        self.stacked.setCurrentIndex(0)

    # -------------------------------------------------------------------------
    # Sayfa 0 - Giriş Paneli
    # -------------------------------------------------------------------------

    def _setup_login_page(self):
        login_page = QWidget()
        login_layout = QVBoxLayout(login_page)
        login_layout.setContentsMargins(0, 0, 0, 0)

        # Ortala
        login_layout.addStretch(2)

        center_frame = QFrame()
        center_frame.setFixedWidth(460)
        center_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 16px;
            }}
        """)
        center_layout = QVBoxLayout(center_frame)
        center_layout.setContentsMargins(40, 40, 40, 40)
        center_layout.setSpacing(20)

        # Başlık
        title = QLabel("Final Kalite Kontrol")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {self.theme.get('primary')}; border: none;")
        title.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(title)

        desc = QLabel("Kartınızı okutun veya sicil numaranızı girin")
        desc.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 13px; border: none;")
        desc.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(desc)

        # Ayırıcı çizgi
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {self.theme.get('border')}; border: none;")
        sep.setFixedHeight(1)
        center_layout.addWidget(sep)

        # Sicil input
        self.sicil_input = QLineEdit()
        self.sicil_input.setPlaceholderText("Sicil No / Kart ID")
        self.sicil_input.setStyleSheet(f"""
            QLineEdit {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 2px solid {self.theme.get('border')};
                border-radius: 10px;
                padding: 14px 18px;
                font-size: 16px;
            }}
            QLineEdit:focus {{
                border-color: {self.theme.get('primary')};
            }}
        """)
        self.sicil_input.returnPressed.connect(self._login)
        self.sicil_input.installEventFilter(self)
        center_layout.addWidget(self.sicil_input)

        # Giriş butonu
        giris_btn = QPushButton("Giriş Yap")
        giris_btn.setCursor(Qt.PointingHandCursor)
        giris_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {self.theme.get('primary_hover', self.theme.get('primary'))};
            }}
        """)
        giris_btn.clicked.connect(self._login)
        center_layout.addWidget(giris_btn)

        # Durum mesajı
        self.login_status = QLabel("")
        self.login_status.setStyleSheet(f"color: {self.theme.get('error')}; font-size: 12px; border: none;")
        self.login_status.setAlignment(Qt.AlignCenter)
        self.login_status.setWordWrap(True)
        center_layout.addWidget(self.login_status)

        login_layout.addWidget(center_frame, alignment=Qt.AlignCenter)
        login_layout.addStretch(3)

        self.stacked.addWidget(login_page)

    # -------------------------------------------------------------------------
    # Sayfa 1 - Ana Ekran
    # -------------------------------------------------------------------------

    def _setup_main_page(self):
        main_page = QWidget()
        main_layout = QVBoxLayout(main_page)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # --- Header ---
        header = QHBoxLayout()
        header.setSpacing(12)

        self.personel_label = QLabel("")
        self.personel_label.setStyleSheet(f"""
            color: {self.theme.get('text')};
            font-size: 14px;
            font-weight: 600;
            background: {self.theme.get('bg_card')};
            border: 1px solid {self.theme.get('border')};
            border-radius: 8px;
            padding: 8px 14px;
        """)
        header.addWidget(self.personel_label)

        header.addStretch()

        self.saat_label = QLabel()
        self.saat_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 15px; font-weight: bold;")
        header.addWidget(self.saat_label)

        refresh_btn = QPushButton("Yenile")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_card')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {self.theme.get('bg_hover')}; }}
        """)
        refresh_btn.clicked.connect(self._load_products)
        header.addWidget(refresh_btn)

        cikis_btn = QPushButton("Çıkış")
        cikis_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('error')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {self.theme.get('error_dark', self.theme.get('error'))}; }}
        """)
        cikis_btn.clicked.connect(self._logout)
        header.addWidget(cikis_btn)

        main_layout.addLayout(header)

        # --- İstatistik Kartları ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        self.stat_bekleyen = self._create_stat_card_ui("Bekleyen", "0", "#3b82f6")
        self.stat_bugun = self._create_stat_card_ui("Bugün Kontrol", "0", "#22c55e")
        self.stat_saglam = self._create_stat_card_ui("Sağlam %", "-", "#10b981")
        self.stat_ret = self._create_stat_card_ui("Ret %", "-", "#ef4444")
        stats_layout.addWidget(self.stat_bekleyen)
        stats_layout.addWidget(self.stat_bugun)
        stats_layout.addWidget(self.stat_saglam)
        stats_layout.addWidget(self.stat_ret)
        main_layout.addLayout(stats_layout)

        # --- Filtreler ---
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara... (İş Emri, Lot, Ürün)")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {self.theme.get('primary')}; }}
        """)
        self.search_input.textChanged.connect(self._filter_products)
        filter_layout.addWidget(self.search_input, 1)

        self.musteri_filter = QComboBox()
        self.musteri_filter.setMinimumWidth(200)
        self.musteri_filter.addItem("Tüm Müşteriler", None)
        self.musteri_filter.currentIndexChanged.connect(self._filter_products)
        filter_layout.addWidget(self.musteri_filter)

        main_layout.addLayout(filter_layout)

        # --- Splitter: Tablo + Detay ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {self.theme.get('border')}; width: 2px; }}")

        # Sol: Ürün Tablosu
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        self.product_table = QTableWidget()
        self.product_table.setColumnCount(8)
        self.product_table.setHorizontalHeaderLabels([
            "ID", "İş Emri", "Lot No", "Müşteri", "Ürün", "Miktar", "Bekleme", "urun_id"
        ])
        self.product_table.setColumnHidden(0, True)   # is_emri_id
        self.product_table.setColumnHidden(7, True)    # urun_id
        self.product_table.setColumnWidth(1, 110)
        self.product_table.setColumnWidth(2, 120)
        self.product_table.setColumnWidth(3, 140)
        self.product_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.product_table.setColumnWidth(5, 80)
        self.product_table.setColumnWidth(6, 80)
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.product_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.setAlternatingRowColors(True)
        self.product_table.currentCellChanged.connect(self._on_product_selected)
        table_layout.addWidget(self.product_table)

        splitter.addWidget(table_frame)

        # Sağ: Detay Paneli
        self.detail_frame = QFrame()
        self.detail_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 12px;
            }}
        """)
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(10)

        # Ürün Resmi
        self.image_label = QLabel("Ürün seçin")
        self.image_label.setFixedSize(300, 220)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(f"""
            background: {self.theme.get('bg_input')};
            border: 1px solid {self.theme.get('border')};
            border-radius: 8px;
            color: {self.theme.get('text_muted')};
            font-size: 13px;
        """)
        detail_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        # Detay bilgileri
        self.detail_grid = QGridLayout()
        self.detail_grid.setSpacing(6)

        detail_labels = [
            ("Müşteri:", "detail_musteri"),
            ("Stok Kodu:", "detail_stok_kodu"),
            ("Teknik Resim:", "detail_teknik_resim"),
            ("Boyut:", "detail_boyut"),
            ("Ağırlık:", "detail_agirlik"),
            ("Kaplama:", "detail_kaplama"),
            ("Kalınlık:", "detail_kalinlik"),
            ("Renk:", "detail_renk"),
            ("Yüzey Alanı:", "detail_yuzey"),
            ("Kontrol Miktarı:", "detail_miktar"),
        ]

        for i, (label_text, obj_name) in enumerate(detail_labels):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px; border: none;")
            val = QLabel("-")
            val.setObjectName(obj_name)
            val.setStyleSheet(f"color: {self.theme.get('text')}; font-size: 12px; font-weight: 600; border: none;")
            val.setWordWrap(True)
            self.detail_grid.addWidget(lbl, i, 0)
            self.detail_grid.addWidget(val, i, 1)

        detail_layout.addLayout(self.detail_grid)

        # Ambalajlama Talimatları
        ambalaj_header = QLabel("📦 Ambalajlama Talimatları")
        ambalaj_header.setStyleSheet(f"color: {self.theme.get('primary')}; font-size: 12px; font-weight: bold; border: none; margin-top: 6px;")
        detail_layout.addWidget(ambalaj_header)

        ambalaj_row = QHBoxLayout()
        ambalaj_row.setSpacing(6)
        self.ambalaj_thumbs = []
        for i in range(3):
            thumb = QLabel()
            thumb.setFixedSize(95, 70)
            thumb.setAlignment(Qt.AlignCenter)
            thumb.setStyleSheet(f"""
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 4px;
                color: {self.theme.get('text_muted')};
                font-size: 10px;
            """)
            thumb.setText(f"{i + 1}")
            thumb.setCursor(Qt.PointingHandCursor)
            thumb.mousePressEvent = lambda event, idx=i: self._show_ambalaj_buyuk(idx)
            ambalaj_row.addWidget(thumb)
            self.ambalaj_thumbs.append(thumb)
        ambalaj_row.addStretch()
        detail_layout.addLayout(ambalaj_row)

        detail_layout.addStretch()

        # Kontrole Başla butonu
        self.basla_btn = QPushButton("KONTROLE BAŞLA")
        self.basla_btn.setEnabled(False)
        self.basla_btn.setCursor(Qt.PointingHandCursor)
        self.basla_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px;
                font-size: 15px;
                font-weight: bold;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background: {self.theme.get('primary_hover', self.theme.get('primary'))};
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_disabled', self.theme.get('text_muted'))};
            }}
        """)
        self.basla_btn.clicked.connect(self._basla_kontrol)
        detail_layout.addWidget(self.basla_btn)

        splitter.addWidget(self.detail_frame)

        splitter.setSizes([550, 350])
        main_layout.addWidget(splitter, 1)

        # --- Son İşlemler Barı ---
        self.son_islem_label = QLabel("")
        self.son_islem_label.setStyleSheet(f"""
            color: {self.theme.get('text_muted')};
            font-size: 12px;
            background: {self.theme.get('bg_card')};
            border: 1px solid {self.theme.get('border')};
            border-radius: 6px;
            padding: 6px 12px;
        """)
        main_layout.addWidget(self.son_islem_label)

        self.stacked.addWidget(main_page)

    # -------------------------------------------------------------------------
    # İstatistik kartı helper
    # -------------------------------------------------------------------------

    def _create_stat_card_ui(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-left: 4px solid {color};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 11px; border: none;")
        layout.addWidget(title_lbl)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("stat_value")
        val_lbl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold; border: none;")
        layout.addWidget(val_lbl)

        return card

    # =========================================================================
    # GLOBAL RFID BAĞLANTISI
    # =========================================================================

    def _try_connect_global_rfid(self):
        """Global RFID servisine bağlanmaya çalış."""
        if self._global_rfid_connected:
            return
        try:
            from core.rfid_service import RFIDService
            svc = RFIDService.instance()
            svc.card_detected.connect(self._on_card_detected_global)
            self._global_rfid_connected = True
            print("[KALITE] Global RFID servisine bağlandı")
        except Exception as e:
            print(f"[KALITE] Global RFID bağlantı hatası: {e}")

    def showEvent(self, event):
        """Sayfa gösterildiğinde global RFID bağlantısını kontrol et."""
        super().showEvent(event)
        self._try_connect_global_rfid()

    # =========================================================================
    # EVENT FILTER - RFID / Barkod
    # =========================================================================

    def eventFilter(self, watched, event):
        # Global servis aktifse lokal reader'a gerek yok (Enter zaten global tarafından tüketiliyor)
        if not self._global_rfid_connected and event.type() == QEvent.Type.KeyPress:
            if self._rfid_reader.process_key(event):
                return True
        return super().eventFilter(watched, event)

    def _on_card_detected_global(self, card_id):
        """Global RFID servisinden kart algılandığında."""
        # Sadece bu sayfa görünürse işle
        if self.isVisible():
            print(f"[KALITE] Global RFID kart: {card_id}")
            self._on_card_detected(card_id)

    def _on_card_detected(self, card_id):
        """RFID/barkod kart okunduğunda"""
        if self.stacked.currentIndex() == 0:
            # Giriş ekranında - otomatik giriş
            self.sicil_input.clear()
            self._do_login(card_id)
        # Ana ekrandaysa bir şey yapma (zaten giriş yapılmış)

    # =========================================================================
    # GİRİŞ / ÇIKIŞ
    # =========================================================================

    def _login(self):
        """Manuel giriş (Enter veya buton ile)"""
        sicil = self.sicil_input.text().strip()
        if not sicil:
            self.login_status.setText("Sicil numarası veya kart ID giriniz!")
            return
        self._do_login(sicil)

    def _do_login(self, sicil_or_card):
        """Personel doğrulama ve yetki kontrolü"""
        self.login_status.setText("")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Personel bul (sicil_no, kart_no veya kart_id ile)
            cursor.execute("""
                SELECT id, uuid, ad, soyad, sicil_no, departman_id, kart_no
                FROM ik.personeller
                WHERE (sicil_no = ? OR kart_no = ? OR kart_id = ?) AND aktif_mi = 1
            """, (sicil_or_card, sicil_or_card, sicil_or_card))
            personel = cursor.fetchone()

            if not personel:
                self.login_status.setText("Personel bulunamadı!")
                conn.close()
                return

            personel_id = personel[0]

            # Yetki kontrolü (Polivelans: "Finak Kalite" seviye >= 3)
            cursor.execute("""
                SELECT MAX(py.seviye) as max_seviye
                FROM ik.personel_yetkinlikler py
                INNER JOIN ik.yetkinlikler y ON py.yetkinlik_id = y.id
                WHERE py.personel_id = ? AND y.kategori = 'Finak Kalite' AND py.seviye >= 3
            """, (personel_id,))
            yetki = cursor.fetchone()

            if not yetki or not yetki[0]:
                self.login_status.setText(
                    f"{personel[2]} {personel[3]} - Final Kalite yetkisi yok!\n(Polivelans seviye 3+ gerekli)"
                )
                conn.close()
                return

            conn.close()

            # Başarılı giriş
            self.personel_data = {
                'id': personel_id,
                'uuid': str(personel[1]),
                'ad': personel[2],
                'soyad': personel[3],
                'sicil_no': personel[4],
                'ad_soyad': f"{personel[2]} {personel[3]}"
            }

            self.personel_label.setText(f"{self.personel_data['ad_soyad']}")
            self.sicil_input.clear()

            # Ana ekrana geç
            self.stacked.setCurrentIndex(1)
            self._load_products()
            self._load_stats()
            self._load_filters()
            self._load_son_islemler()

        except Exception as e:
            self.login_status.setText(f"Giriş hatası: {e}")

    def _logout(self):
        """Çıkış - giriş ekranına dön"""
        self.personel_data = None
        self._selected_product = None
        self._products = []
        self.product_table.setRowCount(0)
        self._clear_detail_panel()
        self.stacked.setCurrentIndex(0)
        self.sicil_input.setFocus()

    # =========================================================================
    # VERİ YÜKLEME
    # =========================================================================

    def _load_products(self):
        """FKK deposundaki bekleyen ürünleri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT
                    ie.id as is_emri_id, ie.is_emri_no, sb.lot_no,
                    ie.cari_unvani, ie.stok_kodu, ie.stok_adi,
                    sb.miktar as kalan_miktar, sb.son_hareket_tarihi, sb.urun_id
                FROM stok.stok_bakiye sb
                INNER JOIN tanim.depolar d ON sb.depo_id = d.id
                LEFT JOIN siparis.is_emirleri ie ON (sb.lot_no = ie.lot_no OR sb.parent_lot_no = ie.lot_no)
                WHERE d.kod = 'FKK'
                  AND sb.miktar > 0
                  AND sb.durum_kodu = 'FKK_BEKLIYOR'
                  AND sb.kalite_durumu IN ('KONTROL_BEKLIYOR', 'BEKLIYOR', 'OK')
                ORDER BY sb.son_hareket_tarihi ASC
            """)
            rows = cursor.fetchall()
            conn.close()

            self._products = []
            for row in rows:
                self._products.append({
                    'is_emri_id': row[0],
                    'is_emri_no': row[1] or '',
                    'lot_no': row[2] or '',
                    'cari_unvani': row[3] or '',
                    'stok_kodu': row[4] or '',
                    'stok_adi': row[5] or '',
                    'miktar': float(row[6] or 0),
                    'son_hareket_tarihi': row[7],
                    'urun_id': row[8],
                })

            self._display_products(self._products)
            self._load_stats()

        except Exception as e:
            print(f"Ürün yükleme hatası: {e}")
            import traceback
            traceback.print_exc()

    def _display_products(self, products):
        """Ürünleri tabloda göster"""
        self.product_table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.product_table.setItem(i, 0, QTableWidgetItem(str(p['is_emri_id'] or '')))

            ie_item = QTableWidgetItem(p['is_emri_no'])
            ie_item.setForeground(QColor(self.theme.get('primary')))
            ie_item.setFont(QFont("", -1, QFont.Bold))
            self.product_table.setItem(i, 1, ie_item)

            self.product_table.setItem(i, 2, QTableWidgetItem(p['lot_no']))
            self.product_table.setItem(i, 3, QTableWidgetItem(p['cari_unvani'][:25]))

            urun = f"{p['stok_kodu']} - {p['stok_adi']}" if p['stok_kodu'] else p['stok_adi']
            self.product_table.setItem(i, 4, QTableWidgetItem(urun[:40]))

            miktar_item = QTableWidgetItem(f"{p['miktar']:,.0f}")
            miktar_item.setTextAlignment(Qt.AlignCenter)
            self.product_table.setItem(i, 5, miktar_item)

            # Bekleme süresi
            if p['son_hareket_tarihi']:
                delta = datetime.now() - p['son_hareket_tarihi']
                h = int(delta.total_seconds() // 3600)
                m = int((delta.total_seconds() % 3600) // 60)
                bekleme_text = f"{h}s {m}dk"
                if h >= 24:
                    color = self.theme.get('error')
                elif h >= 8:
                    color = self.theme.get('warning')
                else:
                    color = self.theme.get('text_muted')
            else:
                bekleme_text = '-'
                color = self.theme.get('text_muted')

            bekleme_item = QTableWidgetItem(bekleme_text)
            bekleme_item.setForeground(QColor(color))
            bekleme_item.setTextAlignment(Qt.AlignCenter)
            self.product_table.setItem(i, 6, bekleme_item)

            self.product_table.setItem(i, 7, QTableWidgetItem(str(p.get('urun_id', '') or '')))

            self.product_table.setRowHeight(i, 40)

    def _load_stats(self):
        """İstatistik kartlarını güncelle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Bekleyen sayısı
            cursor.execute("""
                SELECT COUNT(*), ISNULL(SUM(sb.miktar), 0)
                FROM stok.stok_bakiye sb
                INNER JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE d.kod = 'FKK' AND sb.miktar > 0 AND sb.durum_kodu = 'FKK_BEKLIYOR'
            """)
            bek_row = cursor.fetchone()
            bekleyen_count = bek_row[0] or 0

            # Bugün tamamlanan
            cursor.execute("""
                SELECT COUNT(*), ISNULL(SUM(saglam_adet), 0), ISNULL(SUM(hatali_adet), 0)
                FROM kalite.final_kontrol
                WHERE CAST(kontrol_tarihi AS DATE) = CAST(GETDATE() AS DATE)
            """)
            tam_row = cursor.fetchone()
            bugun_count = tam_row[0] or 0
            bugun_saglam = tam_row[1] or 0
            bugun_hatali = tam_row[2] or 0

            conn.close()

            # Kartları güncelle
            self.stat_bekleyen.findChild(QLabel, "stat_value").setText(str(bekleyen_count))
            self.stat_bugun.findChild(QLabel, "stat_value").setText(str(bugun_count))

            toplam = bugun_saglam + bugun_hatali
            if toplam > 0:
                saglam_pct = (bugun_saglam / toplam) * 100
                ret_pct = (bugun_hatali / toplam) * 100
                self.stat_saglam.findChild(QLabel, "stat_value").setText(f"{saglam_pct:.1f}%")
                self.stat_ret.findChild(QLabel, "stat_value").setText(f"{ret_pct:.1f}%")
            else:
                self.stat_saglam.findChild(QLabel, "stat_value").setText("-")
                self.stat_ret.findChild(QLabel, "stat_value").setText("-")

        except Exception as e:
            print(f"İstatistik yükleme hatası: {e}")

    def _load_filters(self):
        """Müşteri filtresini yükle"""
        try:
            if self.musteri_filter.count() > 1:
                return  # Zaten yüklü

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT ie.cari_unvani
                FROM stok.stok_bakiye sb
                INNER JOIN tanim.depolar d ON sb.depo_id = d.id
                LEFT JOIN siparis.is_emirleri ie ON (sb.lot_no = ie.lot_no OR sb.parent_lot_no = ie.lot_no)
                WHERE d.kod = 'FKK'
                  AND sb.miktar > 0
                  AND ie.cari_unvani IS NOT NULL
                ORDER BY ie.cari_unvani
            """)
            for row in cursor.fetchall():
                if row[0]:
                    self.musteri_filter.addItem(row[0][:30], row[0])
            conn.close()
        except Exception as e:
            print(f"Filtre yükleme hatası: {e}")

    def _load_son_islemler(self):
        """Son işlemleri göster"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 3
                    fk.lot_no, fk.saglam_adet, fk.hatali_adet, fk.sonuc
                FROM kalite.final_kontrol fk
                WHERE CAST(fk.kontrol_tarihi AS DATE) = CAST(GETDATE() AS DATE)
                ORDER BY fk.kontrol_tarihi DESC
            """)
            rows = cursor.fetchall()
            conn.close()

            if rows:
                parts = []
                for row in rows:
                    lot = row[0] or ''
                    saglam = row[1] or 0
                    hatali = row[2] or 0
                    sonuc = row[3] or ''
                    if sonuc == 'ONAY':
                        parts.append(f"{lot} - {saglam} adet sağlam")
                    elif sonuc == 'RED':
                        parts.append(f"{lot} - {hatali} ret")
                    else:
                        parts.append(f"{lot} - {saglam} sağlam, {hatali} ret")
                self.son_islem_label.setText("Son: " + " | ".join(parts))
            else:
                self.son_islem_label.setText("Bugün henüz kontrol yapılmadı")
        except Exception as e:
            self.son_islem_label.setText("")
            print(f"Son işlem yükleme hatası: {e}")

    # =========================================================================
    # ÜRÜN SEÇİMİ VE DETAY
    # =========================================================================

    def _on_product_selected(self, row, col, prev_row, prev_col):
        """Tablo satırı seçildiğinde detay panelini doldur"""
        if row < 0 or row >= self.product_table.rowCount():
            self._clear_detail_panel()
            return

        # Tablodaki veriden ürün bilgisini al
        is_emri_id_item = self.product_table.item(row, 0)
        urun_id_item = self.product_table.item(row, 7)
        lot_no_item = self.product_table.item(row, 2)
        musteri_item = self.product_table.item(row, 3)
        stok_kodu_item = self.product_table.item(row, 4)
        miktar_item = self.product_table.item(row, 5)

        if not is_emri_id_item:
            return

        # _products listesinden bul
        is_emri_id_text = is_emri_id_item.text()
        lot_no_text = lot_no_item.text() if lot_no_item else ''

        selected = None
        for p in self._products:
            if str(p.get('is_emri_id', '')) == is_emri_id_text and p.get('lot_no', '') == lot_no_text:
                selected = p
                break

        if not selected:
            self._clear_detail_panel()
            return

        self._selected_product = selected
        self.basla_btn.setEnabled(True)

        # Detay bilgilerini doldur
        self._find_detail("detail_musteri").setText(selected.get('cari_unvani', '-'))
        self._find_detail("detail_stok_kodu").setText(selected.get('stok_kodu', '-'))
        self._find_detail("detail_miktar").setText(f"{selected.get('miktar', 0):,.0f} adet")

        # Ürün detaylarını DB'den çek
        urun_id = selected.get('urun_id')
        # Ambalaj fotoğraflarını yükle
        self._load_ambalaj_images(selected.get('stok_kodu', ''), selected.get('cari_unvani', ''))

        if urun_id:
            self._load_product_detail(urun_id)
            self._load_product_image(selected.get('stok_kodu', ''))
        else:
            self._find_detail("detail_teknik_resim").setText("-")
            self._find_detail("detail_boyut").setText("-")
            self._find_detail("detail_agirlik").setText("-")
            self._find_detail("detail_kaplama").setText("-")
            self._find_detail("detail_kalinlik").setText("-")
            self._find_detail("detail_renk").setText("-")
            self._find_detail("detail_yuzey").setText("-")
            self.image_label.setText("Resim bulunamadı")

    def _load_product_detail(self, urun_id):
        """Ürün detay bilgilerini DB'den yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    u.urun_kodu, u.urun_adi, u.teknik_resim_no,
                    u.en_mm, u.boy_mm, u.yukseklik_mm, u.agirlik_kg,
                    u.yuzey_alani_m2, u.renk_kodu, u.ral_kodu,
                    u.kalinlik_min_um, u.kalinlik_hedef_um, u.kalinlik_max_um,
                    kt.ad as kaplama_turu_adi,
                    u.resim_yolu
                FROM stok.urunler u
                LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                WHERE u.id = ?
            """, (urun_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                self._find_detail("detail_teknik_resim").setText(row[2] or '-')

                # Boyut
                parts = []
                if row[3]: parts.append(f"{row[3]}")
                if row[4]: parts.append(f"{row[4]}")
                if row[5]: parts.append(f"{row[5]}")
                boyut = " x ".join(parts) + " mm" if parts else "-"
                self._find_detail("detail_boyut").setText(boyut)

                self._find_detail("detail_agirlik").setText(f"{row[6]} kg" if row[6] else "-")
                self._find_detail("detail_kaplama").setText(row[13] or '-')

                # Kalınlık
                kal_parts = []
                if row[10]: kal_parts.append(str(row[10]))
                if row[11]: kal_parts.append(str(row[11]))
                if row[12]: kal_parts.append(str(row[12]))
                kalinlik = "/".join(kal_parts) + " µm" if kal_parts else "-"
                self._find_detail("detail_kalinlik").setText(kalinlik)

                # Renk
                renk_parts = []
                if row[8]: renk_parts.append(row[8])
                if row[9]: renk_parts.append(f"RAL {row[9]}")
                renk = " / ".join(renk_parts) if renk_parts else "-"
                self._find_detail("detail_renk").setText(renk)

                self._find_detail("detail_yuzey").setText(f"{row[7]} m²" if row[7] else "-")
            else:
                for name in ["detail_teknik_resim", "detail_boyut", "detail_agirlik",
                             "detail_kaplama", "detail_kalinlik", "detail_renk", "detail_yuzey"]:
                    self._find_detail(name).setText("-")
        except Exception as e:
            print(f"Ürün detay yükleme hatası: {e}")

    def _load_product_image(self, stok_kodu):
        """NAS'tan ürün resmini yükle"""
        if not stok_kodu:
            self.image_label.setText("Resim bulunamadı")
            return

        base = NAS_PATHS.get("image_path", "")
        for ext in ['.jpg', '.JPG', '.jpeg', '.png', '.PNG']:
            path = os.path.join(base, f"{stok_kodu}{ext}")
            if os.path.exists(path):
                pixmap = QPixmap(path).scaled(
                    300, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.image_label.setPixmap(pixmap)
                return
        self.image_label.setText("Resim bulunamadı")

    def _find_detail(self, obj_name):
        """Detay panelindeki label'ı bul"""
        lbl = self.detail_frame.findChild(QLabel, obj_name)
        if not lbl:
            lbl = QLabel("-")
        return lbl

    def _clear_detail_panel(self):
        """Detay panelini temizle"""
        self._selected_product = None
        self.basla_btn.setEnabled(False)
        self.image_label.clear()
        self.image_label.setText("Ürün seçin")
        for name in ["detail_musteri", "detail_stok_kodu", "detail_teknik_resim",
                      "detail_boyut", "detail_agirlik", "detail_kaplama",
                      "detail_kalinlik", "detail_renk", "detail_yuzey", "detail_miktar"]:
            self._find_detail(name).setText("-")
        # Ambalaj thumbnail'larını temizle
        if hasattr(self, 'ambalaj_thumbs'):
            for i, thumb in enumerate(self.ambalaj_thumbs):
                thumb.clear()
                thumb.setText(f"{i + 1}")
            self._ambalaj_full_paths = [None, None, None]

    def _load_ambalaj_images(self, stok_kodu: str, cari_unvani: str):
        """NAS'tan ambalaj talimat fotoğraflarını thumbnail olarak yükle"""
        self._ambalaj_full_paths = [None, None, None]

        if not stok_kodu or not cari_unvani:
            return

        # Geçersiz karakterleri temizle
        cari_temiz = cari_unvani
        kod_temiz = stok_kodu
        for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            cari_temiz = cari_temiz.replace(char, '_') if cari_temiz else 'Genel'
            kod_temiz = kod_temiz.replace(char, '_') if kod_temiz else ''

        base = NAS_PATHS.get("product_path", "")
        klasor = os.path.join(base, cari_temiz, kod_temiz, '10_Ambalajlama_Talimatlari')

        for i in range(3):
            found = False
            for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.JPG', '.JPEG', '.PNG', '.BMP']:
                dosya = os.path.join(klasor, f"ambalaj_{i + 1}{ext}")
                if os.path.exists(dosya):
                    try:
                        pixmap = QPixmap(dosya)
                        if not pixmap.isNull():
                            scaled = pixmap.scaled(95, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            self.ambalaj_thumbs[i].setPixmap(scaled)
                            self.ambalaj_thumbs[i].setStyleSheet(f"""
                                background: {self.theme.get('bg_input')};
                                border: 1px solid {self.theme.get('success', '#10B981')};
                                border-radius: 4px;
                            """)
                            self._ambalaj_full_paths[i] = dosya
                            found = True
                            break
                    except Exception:
                        pass

            if not found:
                self.ambalaj_thumbs[i].clear()
                self.ambalaj_thumbs[i].setText(f"{i + 1}")
                self.ambalaj_thumbs[i].setStyleSheet(f"""
                    background: {self.theme.get('bg_input')};
                    border: 1px solid {self.theme.get('border')};
                    border-radius: 4px;
                    color: {self.theme.get('text_muted')};
                    font-size: 10px;
                """)

    def _show_ambalaj_buyuk(self, index: int):
        """Ambalaj fotoğrafını büyük göster"""
        if not hasattr(self, '_ambalaj_full_paths') or not self._ambalaj_full_paths[index]:
            return

        dosya = self._ambalaj_full_paths[index]
        pixmap = QPixmap(dosya)
        if pixmap.isNull():
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ambalajlama - Adım {index + 1}")
        dialog.setMinimumSize(700, 520)
        dialog.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main')}; }}")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        scaled = pixmap.scaled(660, 460, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_label.setPixmap(scaled)
        layout.addWidget(img_label)

        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: bold;")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        dialog.exec()

    # =========================================================================
    # FİLTRELEME
    # =========================================================================

    def _filter_products(self):
        """Arama ve müşteri filtresi"""
        search = self.search_input.text().strip().lower()
        musteri = self.musteri_filter.currentData()

        filtered = []
        for p in self._products:
            # Müşteri filtresi
            if musteri and p.get('cari_unvani', '') != musteri:
                continue
            # Arama filtresi
            if search:
                searchable = f"{p.get('is_emri_no', '')} {p.get('lot_no', '')} {p.get('stok_kodu', '')} {p.get('stok_adi', '')} {p.get('cari_unvani', '')}".lower()
                if search not in searchable:
                    continue
            filtered.append(p)

        self._display_products(filtered)

    # =========================================================================
    # KONTROL İŞLEMİ
    # =========================================================================

    def _basla_kontrol(self):
        """Seçili ürün için kontrol başlat"""
        if not self._selected_product or not self.personel_data:
            return

        p = self._selected_product

        # gorev_data oluştur (eski formata uyumlu)
        gorev_data = {
            'is_emri_id': p.get('is_emri_id'),
            'is_emri_no': p.get('is_emri_no', ''),
            'lot_no': p.get('lot_no', ''),
            'cari_unvani': p.get('cari_unvani', ''),
            'stok_kodu': p.get('stok_kodu', ''),
            'stok_adi': p.get('stok_adi', ''),
            'miktar': p.get('miktar', 0),
            'kontrol_adet': p.get('miktar', 0),
            'urun_id': p.get('urun_id'),
        }

        kontrol_dlg = FinalKontrolDialog(gorev_data, self.personel_data, self.theme, self)
        if kontrol_dlg.exec() == QDialog.Accepted and kontrol_dlg.result_data:
            self._kaydet_kontrol(gorev_data, kontrol_dlg.result_data)

    def _kaydet_kontrol(self, gorev_data, result):
        """Kontrol sonucunu kaydet - kontrol_is_emirleri bağımlılığı kaldırıldı"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            from core.hareket_motoru import HareketMotoru
            motor = HareketMotoru(conn)

            saglam = result['saglam_miktar']
            hatali = result['hatali_miktar']
            kontrol = result['kontrol_miktar']
            sure_dk = result['sure_saniye'] // 60

            if hatali == 0:
                sonuc = 'ONAY'
            elif saglam == 0:
                sonuc = 'RED'
            else:
                sonuc = 'KISMI'

            # 1. kalite.final_kontrol tablosuna kayıt ekle
            kontrol_id = None
            try:
                cursor.execute("""
                    INSERT INTO kalite.final_kontrol
                    (is_emri_id, lot_no, kontrol_miktar, saglam_adet, hatali_adet,
                     kontrol_eden_id, kontrol_tarihi, sonuc, aciklama, olusturma_tarihi)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?, ?, GETDATE())
                """, (
                    gorev_data['is_emri_id'],
                    gorev_data.get('lot_no', ''),
                    kontrol,
                    saglam,
                    hatali,
                    self.personel_data['id'],
                    sonuc,
                    result.get('not', '')
                ))
                kontrol_id = cursor.fetchone()[0]
            except Exception as fc_err:
                print(f"final_kontrol kayıt hatası: {fc_err}")

            is_emri_id = gorev_data['is_emri_id']
            lot_no = gorev_data.get('lot_no', '')
            stok_kodu = gorev_data.get('stok_kodu', '')
            stok_adi = gorev_data.get('stok_adi', '')

            # Toplam tamamlanmış miktarı hesapla (final_kontrol'den)
            cursor.execute("""
                SELECT ISNULL(SUM(kontrol_miktar), 0)
                FROM kalite.final_kontrol
                WHERE is_emri_id = ?
            """, (is_emri_id,))
            tamamlanan_toplam = cursor.fetchone()[0] or 0

            # Orijinal toplam miktarı al
            cursor.execute(
                "SELECT ISNULL(uretilen_miktar, toplam_miktar) FROM siparis.is_emirleri WHERE id = ?",
                (is_emri_id,)
            )
            orijinal_toplam = cursor.fetchone()[0] or 0
            kalan = orijinal_toplam - tamamlanan_toplam

            # 2. Hata kayıtları (kontrol_id = final_kontrol'den dönen id)
            if kontrol_id:
                for hata in result.get('hata_listesi', []):
                    try:
                        cursor.execute("""
                            INSERT INTO kalite.kontrol_hatalar (kontrol_id, hata_turu_id, adet)
                            VALUES (?, ?, ?)
                        """, (kontrol_id, hata.get('hata_turu_id'), hata.get('adet')))
                    except Exception as he:
                        print(f"Hata kaydı eklenemedi: {he}")

            # 3. Depo ID'lerini bul (SEVK ve RED)
            sevk_depo_id = motor.get_depo_by_tip('SEVK')
            if not sevk_depo_id:
                cursor.execute("""
                    SELECT id FROM tanim.depolar
                    WHERE kod IN ('SEVK', 'MAMUL') AND aktif_mi = 1
                    ORDER BY CASE WHEN kod = 'SEVK' THEN 0 ELSE 1 END
                """)
                row = cursor.fetchone()
                sevk_depo_id = row[0] if row else 11

            red_depo_id = motor.get_depo_by_tip('RED')
            if not red_depo_id:
                cursor.execute("SELECT id FROM tanim.depolar WHERE kod = 'RED' AND aktif_mi = 1")
                row = cursor.fetchone()
                red_depo_id = row[0] if row else 12

            # 4. urun_id bul
            urun_id = gorev_data.get('urun_id')
            if not urun_id and stok_kodu:
                cursor.execute("SELECT id FROM stok.urunler WHERE urun_kodu = ?", (stok_kodu,))
                urun_row = cursor.fetchone()
                if urun_row:
                    urun_id = urun_row[0]

            if not urun_id:
                cursor.execute("""
                    INSERT INTO stok.urunler (uuid, urun_kodu, urun_adi, urun_tipi, birim_id, aktif_mi,
                                             olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                    OUTPUT INSERTED.id
                    VALUES (NEWID(), ?, ?, 'MAMUL', 1, 1, GETDATE(), GETDATE(), 0)
                """, (stok_kodu or f"URN-{is_emri_id}", stok_adi or f"Ürün {is_emri_id}"))
                urun_id = cursor.fetchone()[0]

            # 5. İş emri durumunu güncelle
            if kalan <= 0:
                if hatali == 0:
                    ie_durum = 'ONAYLANDI'
                elif saglam == 0:
                    ie_durum = 'REDDEDILDI'
                else:
                    ie_durum = 'KISMI_RED'
                cursor.execute("""
                    UPDATE siparis.is_emirleri
                    SET durum = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (ie_durum, is_emri_id))
            else:
                cursor.execute("""
                    UPDATE siparis.is_emirleri
                    SET guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (is_emri_id,))

            # 6. STOK HAREKETLERİ
            if lot_no:
                # FKK deposunun ID'sini al
                cursor.execute("SELECT id FROM tanim.depolar WHERE kod = 'FKK'")
                fkk_row = cursor.fetchone()
                fkk_depo_id = fkk_row[0] if fkk_row else 10

                # Mevcut bakiyeyi kontrol et
                cursor.execute("""
                    SELECT miktar, depo_id FROM stok.stok_bakiye
                    WHERE lot_no = ? AND depo_id = ?
                """, (lot_no, fkk_depo_id))
                bakiye_row = cursor.fetchone()
                mevcut_miktar = float(bakiye_row[0]) if bakiye_row else 0

                kontrol_toplam = saglam + hatali

                # Sağlam -> SEVK DEPO
                if saglam > 0 and sevk_depo_id:
                    sevk_lot = f"{lot_no}-SEV"
                    sevk_sonuc = motor.stok_giris(
                        urun_id=urun_id,
                        miktar=saglam,
                        lot_no=sevk_lot,
                        depo_id=sevk_depo_id,
                        urun_kodu=stok_kodu,
                        urun_adi=stok_adi,
                        kalite_durumu='ONAYLANDI',
                        durum_kodu='SEVK_HAZIR',
                        aciklama=f"Final kalite onay - Sağlam: {saglam}"
                    )
                    if not sevk_sonuc.basarili:
                        print(f"Sevk giriş hatası: {sevk_sonuc.mesaj}")

                # Hatalı -> RED DEPO
                if hatali > 0 and red_depo_id:
                    lot_prefix = '-'.join(lot_no.split('-')[:3]) if lot_no else ''
                    red_lot = f"{lot_prefix}-RED" if lot_prefix else f"RED-{is_emri_id}"
                    red_sonuc = motor.stok_giris(
                        urun_id=urun_id,
                        miktar=hatali,
                        lot_no=red_lot,
                        depo_id=red_depo_id,
                        urun_kodu=stok_kodu,
                        urun_adi=stok_adi,
                        kalite_durumu='REDDEDILDI',
                        durum_kodu='RED',
                        aciklama=f"Final kalite red - Hatalı: {hatali}"
                    )
                    if not red_sonuc.basarili:
                        print(f"Red stok girişi hatası: {red_sonuc.mesaj}")

                # Orijinal lot bakiyesini güncelle
                kalan_bakiye = mevcut_miktar - kontrol_toplam

                if kalan_bakiye > 0:
                    cursor.execute("""
                        UPDATE stok.stok_bakiye
                        SET miktar = ?,
                            kalite_durumu = 'KONTROL_BEKLIYOR',
                            durum_kodu = 'FKK_BEKLIYOR'
                        WHERE lot_no = ? AND depo_id = ?
                    """, (kalan_bakiye, lot_no, fkk_depo_id))
                else:
                    cursor.execute("""
                        UPDATE stok.stok_bakiye
                        SET miktar = 0,
                            kalite_durumu = 'TAMAMLANDI',
                            durum_kodu = 'SEVK_EDILDI'
                        WHERE lot_no = ? AND depo_id = ?
                    """, (lot_no, fkk_depo_id))

                    # kalite.uretim_redler tablosuna kayıt
                    if hatali > 0:
                        try:
                            hata_listesi = result.get('hata_listesi', [])
                            ilk_hata_turu_id = hata_listesi[0].get('hata_turu_id') if hata_listesi else None

                            cursor.execute("""
                                INSERT INTO kalite.uretim_redler
                                (is_emri_id, lot_no, red_miktar, kontrol_id, red_tarihi,
                                 kontrol_eden_id, durum, aciklama, hata_turu_id, olusturma_tarihi)
                                VALUES (?, ?, ?, ?, GETDATE(), ?, 'BEKLIYOR', ?, ?, GETDATE())
                            """, (is_emri_id, lot_no, hatali, kontrol_id,
                                  self.personel_data['id'], result.get('not', ''), ilk_hata_turu_id))
                        except Exception as red_err:
                            print(f"Üretim red kaydı hatası: {red_err}")

            conn.commit()
            conn.close()

            # Etiket bas
            if saglam > 0:
                self._bas_etiket(gorev_data, result)

            # Sonuç mesajı
            msg = f"Kontrol Tamamlandı!\n\nKontrol: {kontrol:,} adet\nSağlam: {saglam:,} -> SEVK DEPO\n"
            if hatali > 0:
                msg += f"Hatalı: {hatali:,} -> RED DEPO\n"
            if kalan > 0:
                msg += f"\nKalan Bakiye: {kalan:,} adet (Beklemede)"
            QMessageBox.information(self, "Başarılı", msg)

            # Verileri yenile
            self._load_products()
            self._load_son_islemler()
            self._clear_detail_panel()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")

    # =========================================================================
    # ETİKET BASIMI
    # =========================================================================

    def _bas_etiket(self, gorev_data, result):
        try:
            etiket_data = {
                'musteri': gorev_data.get('cari_unvani', '') or '',
                'urun': gorev_data.get('stok_adi', '') or '',
                'lot_no': gorev_data.get('lot_no', '') or '',
                'adet': result['saglam_miktar'],
                'tarih': datetime.now().strftime('%d.%m.%Y'),
                'kontrolcu': result.get('kontrolcu_ad', ''),
                'stok_kodu': gorev_data.get('stok_kodu', '') or ''
            }
            dlg = EtiketOnizlemeDialog(self.theme, etiket_data, self)
            if dlg.exec() != QDialog.Accepted:
                return
            ezpl = f"""
^Q50,3
^W100
^H10
^P1
^S3
^AD
^C1
^R0
~Q+0
^O0
^D0
^E18
~R200
^L
Dy2-me-dd
Th:m:s
AE,48,36,1,1,0,0,{etiket_data['musteri'][:30]}
AE,48,26,1,1,0,3,Urun: {etiket_data['urun'][:25]}
AE,48,18,1,1,0,3,Lot: {etiket_data['lot_no']}
AE,48,12,1,1,0,3,Adet: {etiket_data['adet']}
AE,48,6,1,1,0,3,Tarih: {etiket_data['tarih']}
AE,48,0,1,1,0,3,Kontrol: {etiket_data['kontrolcu'][:15]}
BE,10,40,1,3,70,0,2,{etiket_data['lot_no']}
E
"""
            lot_safe = (etiket_data['lot_no'] or 'etiket').replace('/', '-').replace('\\', '-')
            etiket_dosya = os.path.join(os.path.expanduser("~"), "Desktop", f"etiket_{lot_safe}.prn")
            with open(etiket_dosya, 'w', encoding='utf-8') as f:
                f.write(ezpl)
            print(f"Etiket: {etiket_dosya}")
        except Exception as e:
            print(f"Etiket hatası: {e}")

    # =========================================================================
    # TIMER / OTOMATİK YENİLEME
    # =========================================================================

    def _update_time(self):
        self.saat_label.setText(QTime.currentTime().toString("HH:mm:ss"))

    def _auto_refresh(self):
        """Sadece ana ekrandaysa otomatik yenile"""
        if self.stacked.currentIndex() == 1 and self.personel_data:
            self._load_products()
            self._load_son_islemler()

    def closeEvent(self, event):
        self.saat_timer.stop()
        self.refresh_timer.stop()
        super().closeEvent(event)
