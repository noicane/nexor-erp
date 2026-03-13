# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Hat Takip Sayfası (Birleştirilmiş)
[MODERNIZED UI - v3.0]

ERP Tanımları + PLC Canlı Veri
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QComboBox, QGridLayout, QWidget, QScrollArea,
    QProgressBar, QTabWidget, QMessageBox, QSplitter, QCheckBox, QDialog,
    QDateEdit
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QBrush, QFont
from datetime import datetime, timedelta
from components.base_page import BasePage
from core.database import get_db_connection


def get_modern_style(theme: dict) -> dict:
    """Modern tema renkleri - TÜM MODÜLLERDE AYNI"""
    t = theme or {}
    return {
        'card_bg': t.get('bg_card', '#151B23'),
        'input_bg': t.get('bg_input', '#232C3B'),
        'border': t.get('border', '#1E2736'),
        'text': t.get('text', '#E8ECF1'),
        'text_secondary': t.get('text_secondary', '#8896A6'),
        'text_muted': t.get('text_muted', '#5C6878'),
        'primary': t.get('primary', '#DC2626'),
        'primary_hover': t.get('primary_hover', '#9B1818'),
        'success': t.get('success', '#10B981'),
        'warning': t.get('warning', '#F59E0B'),
        'error': t.get('error', '#EF4444'),
        'danger': t.get('error', '#EF4444'),
        'info': t.get('info', '#3B82F6'),
        'bg_main': t.get('bg_main', '#0F1419'),
        'bg_hover': t.get('bg_hover', '#1C2430'),
        'bg_selected': t.get('bg_selected', '#1E1215'),
        'border_light': t.get('border_light', '#2A3545'),
        'border_input': t.get('border_input', '#1E2736'),
        'card_solid': t.get('bg_card_solid', '#151B23'),
        'gradient': t.get('gradient_css', ''),
    }


class UretimHatPage(BasePage):
    """Hat Takip Sayfası - ERP Tanımları + PLC Canlı Veri"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.erp_conn = None
        self.pozisyon_tanimlari = {}
        self.plc_data = {}
        
        # Tema değişkenleri (eski kod uyumluluğu için)
        self.bg_card = self.s['card_bg']
        self.bg_input = self.s['input_bg']
        self.bg_main = self.s['card_bg']
        self.text = self.s['text']
        self.text_muted = self.s['text_muted']
        self.border = self.s['border']
        self.primary = self.s['primary']
        self.success = self.s['success']
        self.warning = self.s['warning']
        self.error = self.s['error']
        
        self._setup_ui()
        QTimer.singleShot(100, self._load_initial)
        
        # Otomatik yenileme - 5 saniye
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_plc_data)
        self.refresh_timer.start(5000)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        header = QFrame()
        header.setStyleSheet(f"QFrame{{background:{self.bg_card};border-radius:8px;padding:16px;}}")
        hl = QHBoxLayout(header)
        
        title = QLabel("🏭 Hat Takip - Canlı Üretim Verileri")
        title.setStyleSheet(f"font-size:20px;font-weight:bold;color:{self.text};")
        hl.addWidget(title)
        
        hl.addStretch()
        
        # Bağlantı durumları
        self.lbl_erp_status = QLabel("⚪ ERP")
        self.lbl_erp_status.setStyleSheet(f"color:{self.text_muted};")
        hl.addWidget(self.lbl_erp_status)
        
        self.lbl_plc_status = QLabel("⚪ PLC")
        self.lbl_plc_status.setStyleSheet(f"color:{self.text_muted};margin-left:10px;")
        hl.addWidget(self.lbl_plc_status)
        
        # Son güncelleme
        self.lbl_update = QLabel("Son: -")
        self.lbl_update.setStyleSheet(f"color:{self.text_muted};margin-left:20px;")
        hl.addWidget(self.lbl_update)
        
        btn_ref = QPushButton("🔄 Yenile")
        btn_ref.setCursor(Qt.PointingHandCursor)
        btn_ref.clicked.connect(self._refresh_plc_data)
        btn_ref.setStyleSheet(f"QPushButton{{background:{self.primary};color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:bold;}}QPushButton:hover{{background:#06b6d4;}}")
        hl.addWidget(btn_ref)
        
        layout.addWidget(header)
        
        # Özet Kartları
        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_aktif = self._card("🟢 AKTİF POZİSYON", "0", self.success)
        self.card_uretim = self._card("📦 GÜNLÜK ÜRETİM", "0", self.primary)
        self.card_bara = self._card("🔲 TOPLAM BARA", "0", self.warning)
        self.card_uyari = self._card("⚠️ UYARI", "0", self.error)
        cards.addWidget(self.card_aktif)
        cards.addWidget(self.card_uretim)
        cards.addWidget(self.card_bara)
        cards.addWidget(self.card_uyari)
        layout.addLayout(cards)
        
        # Ana içerik - Tab
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane{{border:none;background:{self.bg_card};border-radius:8px;}}
            QTabBar::tab{{background:{self.bg_main};color:{self.text_muted};padding:10px 20px;margin-right:2px;border-radius:4px 4px 0 0;}}
            QTabBar::tab:selected{{background:{self.bg_card};color:{self.primary};font-weight:bold;}}
        """)
        
        # Tab 1: Birleşik Görünüm
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.setContentsMargins(0, 8, 0, 0)
        
        # Filtreler
        filt = QHBoxLayout()
        filt.addWidget(QLabel("Hat:", styleSheet=f"color:{self.text};"))
        self.cmb_hat = QComboBox()
        self.cmb_hat.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:150px;}}")
        self.cmb_hat.addItem("Tüm Hatlar", None)
        # Signal bağlantısı _load_initial sonrasında yapılacak
        filt.addWidget(self.cmb_hat)
        
        filt.addWidget(QLabel("Durum:", styleSheet=f"color:{self.text};margin-left:15px;"))
        self.cmb_durum = QComboBox()
        self.cmb_durum.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:120px;}}")
        self.cmb_durum.addItem("Tümü", None)
        self.cmb_durum.addItem("🟢 Aktif", "aktif")
        self.cmb_durum.addItem("🟡 Bekliyor", "bekliyor")
        self.cmb_durum.addItem("🔴 Durdu", "durdu")
        self.cmb_durum.addItem("⚠️ Uyarı", "uyari")
        # Signal bağlantısı _load_initial sonrasında yapılacak
        filt.addWidget(self.cmb_durum)
        
        self.chk_tanimsiz = QCheckBox("Tanımsız Pozisyonları Göster")
        self.chk_tanimsiz.setStyleSheet(f"color:{self.text};margin-left:15px;")
        self.chk_tanimsiz.setChecked(True)
        # Signal bağlantısı _load_initial sonrasında yapılacak
        filt.addWidget(self.chk_tanimsiz)
        
        filt.addStretch()
        tab1_layout.addLayout(filt)
        
        # Birleşik tablo
        self.tbl_main = QTableWidget()
        self.tbl_main.setColumnCount(14)
        self.tbl_main.setHorizontalHeaderLabels([
            "Poz No", "Hat", "Pozisyon Adı", "Tip", "Banyo", 
            "Durum", "Bara", "Reçete", 
            "Sıcaklık", "Hedef", "Limit",
            "Akım", "Miktar", "Son İşlem"
        ])
        col_widths = [60, 70, 180, 80, 100, 80, 60, 60, 70, 70, 90, 70, 80, 130]
        for i, w in enumerate(col_widths):
            self.tbl_main.setColumnWidth(i, w)
        self.tbl_main.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_main.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_main.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_main)
        tab1_layout.addWidget(self.tbl_main)
        
        self.tabs.addTab(tab1, "📊 Birleşik Görünüm")
        
        # Tab 2: Hat Şeması (Görsel)
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.setContentsMargins(8, 8, 8, 8)
        
        # Hat seçimi
        hat_select = QHBoxLayout()
        hat_select.addWidget(QLabel("Hat Seçin:", styleSheet=f"color:{self.text};"))
        self.cmb_schema_hat = QComboBox()
        self.cmb_schema_hat.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:200px;}}")
        self.cmb_schema_hat.currentIndexChanged.connect(self._update_schema)
        hat_select.addWidget(self.cmb_schema_hat)
        hat_select.addStretch()
        tab2_layout.addLayout(hat_select)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{border:none;background:{self.bg_card};}}")
        
        self.schema_widget = QWidget()
        self.schema_layout = QGridLayout(self.schema_widget)
        self.schema_layout.setSpacing(8)
        scroll.setWidget(self.schema_widget)
        tab2_layout.addWidget(scroll)
        
        self.tabs.addTab(tab2, "🗺️ Hat Şeması")
        
        # Tab 3: Günlük İstatistik
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        tab3_layout.setContentsMargins(0, 8, 0, 0)
        
        self.tbl_istatistik = QTableWidget()
        self.tbl_istatistik.setColumnCount(9)
        self.tbl_istatistik.setHorizontalHeaderLabels([
            "Hat", "Poz No", "Pozisyon Adı", "Toplam İşlem", "Toplam Bara", 
            "Toplam Miktar", "Ort. Sıcaklık", "İlk İşlem", "Son İşlem"
        ])
        for i, w in enumerate([70, 60, 180, 90, 90, 100, 90, 120, 120]):
            self.tbl_istatistik.setColumnWidth(i, w)
        self.tbl_istatistik.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_istatistik.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_istatistik.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_istatistik)
        tab3_layout.addWidget(self.tbl_istatistik)
        
        self.tabs.addTab(tab3, "📈 Günlük İstatistik")
        
        # Tab 4: Tanımsız Pozisyonlar
        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        tab4_layout.setContentsMargins(0, 8, 0, 0)
        
        info_label = QLabel("⚠️ PLC'de veri gönderen ancak ERP'de tanımı olmayan pozisyonlar:")
        info_label.setStyleSheet(f"color:{self.warning};font-weight:bold;padding:10px;")
        tab4_layout.addWidget(info_label)
        
        self.tbl_tanimsiz = QTableWidget()
        self.tbl_tanimsiz.setColumnCount(7)
        self.tbl_tanimsiz.setHorizontalHeaderLabels([
            "Poz No (KznNo)", "İşlem Sayısı", "Son Bara", "Reçete", 
            "Sıcaklık", "Miktar", "Son İşlem"
        ])
        for i, w in enumerate([100, 100, 80, 80, 80, 100, 150]):
            self.tbl_tanimsiz.setColumnWidth(i, w)
        self.tbl_tanimsiz.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_tanimsiz.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_tanimsiz)
        tab4_layout.addWidget(self.tbl_tanimsiz)
        
        self.tabs.addTab(tab4, "❓ Tanımsız Pozisyonlar")
        
        # Tab 5: Boş Kalma Analizi
        tab5 = QWidget()
        tab5_layout = QVBoxLayout(tab5)
        tab5_layout.setContentsMargins(0, 8, 0, 0)
        
        # Filtre
        bos_filt = QHBoxLayout()
        
        # Tarih seçimi
        bos_filt.addWidget(QLabel("Dönem:", styleSheet=f"color:{self.text};"))
        self.cmb_bos_tarih = QComboBox()
        self.cmb_bos_tarih.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:140px;}}")
        self.cmb_bos_tarih.addItem("Bugün (Vardiya)", "bugun")
        self.cmb_bos_tarih.addItem("Dün", "dun")
        self.cmb_bos_tarih.addItem("Son 7 Gün", "hafta")
        self.cmb_bos_tarih.addItem("Son 24 Saat", "24saat")
        bos_filt.addWidget(self.cmb_bos_tarih)
        
        # Hat seçimi
        bos_filt.addWidget(QLabel("Hat:", styleSheet=f"color:{self.text};margin-left:15px;"))
        self.cmb_bos_hat = QComboBox()
        self.cmb_bos_hat.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:120px;}}")
        self.cmb_bos_hat.addItem("Tüm Hatlar", None)
        self.cmb_bos_hat.addItem("KTL (101-143)", "KTL")
        self.cmb_bos_hat.addItem("CINKO (201-247)", "CINKO")
        bos_filt.addWidget(self.cmb_bos_hat)
        
        bos_filt.addWidget(QLabel("Eşik:", styleSheet=f"color:{self.text};margin-left:15px;"))
        self.cmb_bos_esik = QComboBox()
        self.cmb_bos_esik.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:100px;}}")
        self.cmb_bos_esik.addItem("5 dakika", 5)
        self.cmb_bos_esik.addItem("10 dakika", 10)
        self.cmb_bos_esik.addItem("15 dakika", 15)
        self.cmb_bos_esik.addItem("30 dakika", 30)
        self.cmb_bos_esik.setCurrentIndex(1)  # Default 10 dk
        bos_filt.addWidget(self.cmb_bos_esik)
        
        bos_filt.addWidget(QLabel("Sırala:", styleSheet=f"color:{self.text};margin-left:15px;"))
        self.cmb_bos_sirala = QComboBox()
        self.cmb_bos_sirala.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:150px;}}")
        self.cmb_bos_sirala.addItem("Boş Kalma (Azalan)", "bos_desc")
        self.cmb_bos_sirala.addItem("Boş Kalma (Artan)", "bos_asc")
        self.cmb_bos_sirala.addItem("Pozisyon No", "poz")
        bos_filt.addWidget(self.cmb_bos_sirala)
        
        btn_bos_hesapla = QPushButton("🔄 Hesapla")
        btn_bos_hesapla.setStyleSheet(f"QPushButton{{background:{self.primary};color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:bold;}}")
        btn_bos_hesapla.clicked.connect(self._load_bos_kalma_analizi)
        bos_filt.addWidget(btn_bos_hesapla)
        bos_filt.addStretch()
        tab5_layout.addLayout(bos_filt)
        
        self.tbl_bos_kalma = QTableWidget()
        self.tbl_bos_kalma.setColumnCount(10)
        self.tbl_bos_kalma.setHorizontalHeaderLabels([
            "Poz No", "Hat", "Pozisyon Adı", "Toplam İşlem", "Çalışma (dk)",
            "Boş Kalma (dk)", "Boş %", "En Uzun Boşluk", "İlk İşlem", "Son İşlem"
        ])
        for i, w in enumerate([60, 70, 160, 80, 90, 100, 70, 100, 100, 100]):
            self.tbl_bos_kalma.setColumnWidth(i, w)
        self.tbl_bos_kalma.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_bos_kalma.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_bos_kalma.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_bos_kalma)
        tab5_layout.addWidget(self.tbl_bos_kalma)
        
        self.tabs.addTab(tab5, "⏱️ Boş Kalma Analizi")
        
        # Tab 6: Reçete Analizi
        tab6 = QWidget()
        tab6_layout = QVBoxLayout(tab6)
        tab6_layout.setContentsMargins(0, 8, 0, 0)
        
        rec_filt = QHBoxLayout()
        rec_filt.addWidget(QLabel("Görünüm:", styleSheet=f"color:{self.text};"))
        self.cmb_recete_gorunum = QComboBox()
        self.cmb_recete_gorunum.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:150px;}}")
        self.cmb_recete_gorunum.addItem("Reçete Özet", "ozet")
        self.cmb_recete_gorunum.addItem("Reçete-Pozisyon Detay", "detay")
        self.cmb_recete_gorunum.addItem("Reçete Süreleri", "sureler")
        self.cmb_recete_gorunum.currentIndexChanged.connect(self._load_recete_analizi)
        rec_filt.addWidget(self.cmb_recete_gorunum)

        rec_filt.addWidget(QLabel("Hat:", styleSheet=f"color:{self.text};margin-left:15px;"))
        self.cmb_recete_hat = QComboBox()
        self.cmb_recete_hat.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:120px;}}")
        self.cmb_recete_hat.addItem("Tümü", None)
        self.cmb_recete_hat.addItem("KTL", "KTL")
        self.cmb_recete_hat.addItem("ZNNI (Çinko-Nikel)", "ZNNI")
        self.cmb_recete_hat.addItem("ON (Ön İşlem)", "ON")
        self.cmb_recete_hat.currentIndexChanged.connect(self._load_recete_analizi)
        rec_filt.addWidget(self.cmb_recete_hat)

        rec_filt.addStretch()
        tab6_layout.addLayout(rec_filt)

        self.tbl_recete = QTableWidget()
        self.tbl_recete.setColumnCount(8)
        self.tbl_recete.setHorizontalHeaderLabels([
            "Reçete No", "Toplam İşlem", "Toplam Miktar", "Kullanılan Poz.",
            "En Yoğun Poz.", "En Az Poz.", "Ort. Sıcaklık", "Ort. Akım"
        ])
        for i, w in enumerate([80, 100, 100, 120, 100, 100, 90, 90]):
            self.tbl_recete.setColumnWidth(i, w)
        self.tbl_recete.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tbl_recete.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_recete.verticalHeader().setVisible(False)
        self.tbl_recete.doubleClicked.connect(self._on_recete_double_click)
        self._tbl_style(self.tbl_recete)
        tab6_layout.addWidget(self.tbl_recete)

        self.tabs.addTab(tab6, "📋 Reçete Analizi")
        
        # Tab 7: Vardiya Özet (ERP'den)
        tab7 = QWidget()
        tab7_layout = QVBoxLayout(tab7)
        tab7_layout.setContentsMargins(0, 8, 0, 0)
        
        # Vardiya kartları
        vardiya_cards = QHBoxLayout()
        vardiya_cards.setSpacing(12)
        self.card_ktl_giren = self._card("🔵 KTL GİREN", "0", self.primary)
        self.card_ktl_cikan = self._card("🔵 KTL ÇIKAN", "0", self.success)
        self.card_cinko_giren = self._card("🟡 ÇİNKO GİREN", "0", self.warning)
        self.card_cinko_cikan = self._card("🟡 ÇİNKO ÇIKAN", "0", self.success)
        vardiya_cards.addWidget(self.card_ktl_giren)
        vardiya_cards.addWidget(self.card_ktl_cikan)
        vardiya_cards.addWidget(self.card_cinko_giren)
        vardiya_cards.addWidget(self.card_cinko_cikan)
        tab7_layout.addLayout(vardiya_cards)
        
        self.tbl_vardiya = QTableWidget()
        self.tbl_vardiya.setColumnCount(10)
        self.tbl_vardiya.setHorizontalHeaderLabels([
            "Tarih", "Hat", "Giren Bara", "Çıkan Bara", "Hedef",
            "Kalan", "Verimlilik %", "Geçen (dk)", "Kalan (dk)", "Durum"
        ])
        for i, w in enumerate([90, 80, 80, 80, 70, 70, 90, 80, 80, 100]):
            self.tbl_vardiya.setColumnWidth(i, w)
        self.tbl_vardiya.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_vardiya.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_vardiya)
        tab7_layout.addWidget(self.tbl_vardiya)
        
        self.tabs.addTab(tab7, "📊 Vardiya Özet")
        
        # Tab 8: Dar Boğaz Analizi
        tab8 = QWidget()
        tab8_layout = QVBoxLayout(tab8)
        tab8_layout.setContentsMargins(0, 8, 0, 0)
        
        # Filtre
        dar_filt = QHBoxLayout()
        dar_filt.addWidget(QLabel("Dönem:", styleSheet=f"color:{self.text};"))
        self.cmb_dar_tarih = QComboBox()
        self.cmb_dar_tarih.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:140px;}}")
        self.cmb_dar_tarih.addItem("Bugün (Vardiya)", "bugun")
        self.cmb_dar_tarih.addItem("Dün", "dun")
        self.cmb_dar_tarih.addItem("Son 7 Gün", "hafta")
        dar_filt.addWidget(self.cmb_dar_tarih)
        
        dar_filt.addWidget(QLabel("Hat:", styleSheet=f"color:{self.text};margin-left:15px;"))
        self.cmb_dar_hat = QComboBox()
        self.cmb_dar_hat.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:120px;}}")
        self.cmb_dar_hat.addItem("Tüm Hatlar", None)
        self.cmb_dar_hat.addItem("KTL (101-143)", "KTL")
        self.cmb_dar_hat.addItem("CINKO (201-247)", "CINKO")
        dar_filt.addWidget(self.cmb_dar_hat)
        
        btn_dar_hesapla = QPushButton("🔄 Analiz Et")
        btn_dar_hesapla.setStyleSheet(f"QPushButton{{background:{self.primary};color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:bold;}}")
        btn_dar_hesapla.clicked.connect(self._load_darbogaz_analizi)
        dar_filt.addWidget(btn_dar_hesapla)
        dar_filt.addStretch()
        tab8_layout.addLayout(dar_filt)
        
        # Özet kartları
        dar_cards = QHBoxLayout()
        dar_cards.setSpacing(12)
        self.card_darbogaz = self._card("🚨 KRİTİK DAR BOĞAZ", "-", self.error)
        self.card_kayip_sure = self._card("⏱️ TOPLAM KAYIP", "0 dk", self.warning)
        self.card_verimlilik = self._card("📊 HAT VERİMLİLİĞİ", "-%", self.success)
        self.card_oneri = self._card("💡 ÖNCELİK", "-", self.primary)
        dar_cards.addWidget(self.card_darbogaz)
        dar_cards.addWidget(self.card_kayip_sure)
        dar_cards.addWidget(self.card_verimlilik)
        dar_cards.addWidget(self.card_oneri)
        tab8_layout.addLayout(dar_cards)
        
        # Öneri label
        self.lbl_darbogaz_oneri = QLabel("")
        self.lbl_darbogaz_oneri.setStyleSheet(f"color:{self.warning};font-size:13px;padding:10px;background:{self.bg_card};border-radius:8px;margin:5px 0;")
        self.lbl_darbogaz_oneri.setWordWrap(True)
        tab8_layout.addWidget(self.lbl_darbogaz_oneri)
        
        # Dar boğaz tablosu
        self.tbl_darbogaz = QTableWidget()
        self.tbl_darbogaz.setColumnCount(11)
        self.tbl_darbogaz.setHorizontalHeaderLabels([
            "Sıra", "Poz No", "Hat", "Pozisyon Adı", "Boş %", "Boş (dk)",
            "İşlem Sayısı", "Ort. İşlem Süresi", "Darboğaz Skoru", "Durum", "Öneri"
        ])
        for i, w in enumerate([40, 60, 60, 160, 70, 80, 90, 100, 100, 80, 150]):
            self.tbl_darbogaz.setColumnWidth(i, w)
        self.tbl_darbogaz.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tbl_darbogaz.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_darbogaz.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_darbogaz)
        tab8_layout.addWidget(self.tbl_darbogaz)
        
        self.tabs.addTab(tab8, "🚨 Dar Boğaz Analizi")

        # Tab 9: Akım Takip
        tab9 = QWidget()
        tab9_layout = QVBoxLayout(tab9)
        tab9_layout.setContentsMargins(0, 8, 0, 0)

        # Filtre
        akim_filt = QHBoxLayout()
        akim_filt.addWidget(QLabel("Hat:", styleSheet=f"color:{self.text};"))
        self.cmb_akim_hat = QComboBox()
        self.cmb_akim_hat.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:140px;}}")
        self.cmb_akim_hat.addItem("Tüm Hatlar", None)
        self.cmb_akim_hat.addItem("KTL (101-143)", "KTL")
        self.cmb_akim_hat.addItem("ZNNI (201-247)", "ZNNI")
        self.cmb_akim_hat.addItem("ON (1-23)", "ON")
        self.cmb_akim_hat.currentIndexChanged.connect(self._update_akim_table)
        akim_filt.addWidget(self.cmb_akim_hat)

        self.chk_sadece_aktif_akim = QCheckBox("Son 24 Saat")
        self.chk_sadece_aktif_akim.setStyleSheet(f"color:{self.text};")
        self.chk_sadece_aktif_akim.setChecked(False)
        self.chk_sadece_aktif_akim.stateChanged.connect(self._update_akim_table)
        akim_filt.addWidget(self.chk_sadece_aktif_akim)

        self.chk_sadece_uyari_akim = QCheckBox("Sadece Uyarılar")
        self.chk_sadece_uyari_akim.setStyleSheet(f"color:{self.text};")
        self.chk_sadece_uyari_akim.stateChanged.connect(self._update_akim_table)
        akim_filt.addWidget(self.chk_sadece_uyari_akim)

        akim_filt.addStretch()

        # Akım özet kartları
        self.lbl_akim_ozet = QLabel("")
        self.lbl_akim_ozet.setStyleSheet(f"color:{self.text};font-size:13px;padding:8px 12px;background:{self.bg_card};border-radius:8px;")
        akim_filt.addWidget(self.lbl_akim_ozet)

        tab9_layout.addLayout(akim_filt)

        # Akım tablosu
        self.tbl_akim = QTableWidget()
        self.tbl_akim.setColumnCount(10)
        self.tbl_akim.setHorizontalHeaderLabels([
            "Poz No", "Hat", "Pozisyon Adı", "Banyo",
            "Anlık Akım", "Hedef", "Min", "Max", "Sapma %", "Durum"
        ])
        akim_col_widths = [60, 60, 180, 100, 100, 80, 80, 80, 80, 160]
        for i, w in enumerate(akim_col_widths):
            self.tbl_akim.setColumnWidth(i, w)
        self.tbl_akim.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_akim.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_akim.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_akim)
        tab9_layout.addWidget(self.tbl_akim)

        self.tabs.addTab(tab9, "⚡ Akım Takip")

        # Tab 10: Vardiya Üretim Raporu
        tab10 = QWidget()
        tab10_layout = QVBoxLayout(tab10)
        tab10_layout.setContentsMargins(0, 8, 0, 0)

        # Filtreler
        vr_filt = QHBoxLayout()
        vr_filt.addWidget(QLabel("Tarih:", styleSheet=f"color:{self.text};"))
        self.de_vr_tarih = QDateEdit()
        self.de_vr_tarih.setDate(QDate.currentDate())
        self.de_vr_tarih.setCalendarPopup(True)
        self.de_vr_tarih.setDisplayFormat("dd.MM.yyyy")
        self.de_vr_tarih.setStyleSheet(f"QDateEdit{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:120px;}}")
        vr_filt.addWidget(self.de_vr_tarih)

        vr_filt.addWidget(QLabel("Vardiya:", styleSheet=f"color:{self.text};margin-left:15px;"))
        self.cmb_vr_vardiya = QComboBox()
        self.cmb_vr_vardiya.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:160px;}}")
        self._load_vardiya_combo()
        vr_filt.addWidget(self.cmb_vr_vardiya)

        vr_filt.addWidget(QLabel("Hat:", styleSheet=f"color:{self.text};margin-left:15px;"))
        self.cmb_vr_hat = QComboBox()
        self.cmb_vr_hat.setStyleSheet(f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;min-width:120px;}}")
        self.cmb_vr_hat.addItem("Tümü", None)
        self.cmb_vr_hat.addItem("KTL", "KTL")
        self.cmb_vr_hat.addItem("CINKO (ZNNI)", "CINKO")
        vr_filt.addWidget(self.cmb_vr_hat)

        btn_vr = QPushButton("Rapor Al")
        btn_vr.setStyleSheet(f"QPushButton{{background:{self.primary};color:white;border:none;border-radius:6px;padding:8px 20px;font-weight:bold;}}QPushButton:hover{{background:#06b6d4;}}")
        btn_vr.setCursor(Qt.PointingHandCursor)
        btn_vr.clicked.connect(self._load_vardiya_raporu)
        vr_filt.addWidget(btn_vr)
        vr_filt.addStretch()
        tab10_layout.addLayout(vr_filt)

        # Özet kartları
        vr_cards = QHBoxLayout()
        vr_cards.setSpacing(12)
        self.card_vr_bara = self._card("TOPLAM BARA", "0", self.primary)
        self.card_vr_ktl = self._card("KTL BARA", "0", self.success)
        self.card_vr_cinko = self._card("CINKO BARA", "0", self.warning)
        self.card_vr_sapma = self._card("ORT. SÜRE SAPMA", "-", self.error)
        vr_cards.addWidget(self.card_vr_bara)
        vr_cards.addWidget(self.card_vr_ktl)
        vr_cards.addWidget(self.card_vr_cinko)
        vr_cards.addWidget(self.card_vr_sapma)
        tab10_layout.addLayout(vr_cards)

        # Rapor tablosu
        self.tbl_vr = QTableWidget()
        self.tbl_vr.setColumnCount(12)
        self.tbl_vr.setHorizontalHeaderLabels([
            "Sıra", "Hat", "Reçete", "Giriş", "Çıkış",
            "Gerçek Süre", "Beklenen Süre", "Süre Sapma",
            "Ort. Akım", "Ort. Sıcaklık", "Adım", "Kazan"
        ])
        vr_widths = [50, 60, 60, 80, 80, 90, 90, 90, 80, 80, 50, 50]
        for i, w in enumerate(vr_widths):
            self.tbl_vr.setColumnWidth(i, w)
        self.tbl_vr.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.tbl_vr.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_vr.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_vr)
        self.tbl_vr.doubleClicked.connect(self._show_bara_detay)
        tab10_layout.addWidget(self.tbl_vr)

        self.tabs.addTab(tab10, "📋 Vardiya Raporu")

        # Tab değiştiğinde akım tabını güncelle
        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tabs, 1)
    
    def _card(self, title, val, color):
        c = QFrame()
        c.setFixedHeight(85)
        c.setMinimumWidth(180)
        c.setStyleSheet(f"QFrame{{background:{self.bg_card};border-radius:10px;border-left:4px solid {color};}}")
        l = QVBoxLayout(c)
        l.setContentsMargins(12, 10, 12, 10)
        l.setSpacing(4)
        l.addWidget(QLabel(title, styleSheet=f"color:{self.text_muted};font-size:11px;font-weight:bold;"))
        lv = QLabel(val)
        lv.setObjectName("val")
        lv.setStyleSheet(f"color:{color};font-size:26px;font-weight:bold;")
        l.addWidget(lv)
        l.addStretch()
        return c
    
    def _tbl_style(self, t):
        t.setStyleSheet(f"""
            QTableWidget{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;gridline-color:{self.border};}}
            QTableWidget::item{{padding:6px;color:{self.text};}}
            QTableWidget::item:selected{{background:{self.primary};color:white;}}
            QHeaderView::section{{background:{self.bg_card};color:{self.text};padding:8px;border:none;font-weight:bold;border-bottom:2px solid {self.primary};}}
        """)
        t.verticalHeader().setDefaultSectionSize(36)
    
    def _load_initial(self):
        """İlk yükleme - önce ERP tanımları, sonra PLC"""
        self._ensure_recete_table()
        self._load_erp_tanimlari()
        self._connect_plc()
        self._refresh_plc_data()
        
        # Veriler yüklendikten sonra filtreleri bağla
        self.cmb_hat.currentIndexChanged.connect(self._filter_table)
        self.cmb_durum.currentIndexChanged.connect(self._filter_table)
        self.chk_tanimsiz.stateChanged.connect(self._filter_table)
        
        # Yeni tab verilerini yükle
        self._load_vardiya_ozet()
        self._load_recete_analizi()
    
    def _ensure_recete_table(self):
        """plc_recete_tanimlari tablosunu olustur ve seed et"""
        try:
            from modules.kaplama_planlama import db_operations as kp_db
            kp_db.ensure_tables()
            kp_db.seed_recete_tanimlari()
            kp_db.sync_recete_sureleri()
        except Exception as e:
            print(f"Recete tablo olusturma hatasi: {e}")

    def _load_erp_tanimlari(self):
        """ERP'den hat ve pozisyon tanımlarını yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Hat listesi
            cursor.execute("""
                SELECT id, kod, ad FROM tanim.uretim_hatlari 
                WHERE aktif_mi=1 AND silindi_mi=0 
                ORDER BY sira_no, kod
            """)
            hatlar = cursor.fetchall()
            
            self.cmb_hat.clear()
            self.cmb_hat.addItem("Tüm Hatlar", None)
            self.cmb_schema_hat.clear()
            
            for hat in hatlar:
                self.cmb_hat.addItem(f"{hat[1]} - {hat[2]}", hat[0])
                self.cmb_schema_hat.addItem(f"{hat[1]} - {hat[2]}", hat[0])
            
            # Pozisyon tanımları
            cursor.execute("""
                SELECT 
                    p.pozisyon_no,
                    h.id as hat_id,
                    h.kod as hat_kodu,
                    h.ad as hat_adi,
                    p.ad as pozisyon_adi,
                    p.kisa_ad,
                    pt.ad as pozisyon_tipi,
                    bt.ad as banyo_tipi,
                    p.sicaklik_min,
                    p.sicaklik_max,
                    p.sicaklik_hedef,
                    p.akim_min,
                    p.akim_max,
                    p.akim_hedef,
                    p.hacim_lt,
                    p.sira_no
                FROM tanim.hat_pozisyonlar p
                JOIN tanim.uretim_hatlari h ON p.hat_id = h.id
                JOIN tanim.pozisyon_tipleri pt ON p.pozisyon_tipi_id = pt.id
                LEFT JOIN tanim.banyo_tipleri bt ON p.banyo_tipi_id = bt.id
                WHERE p.aktif_mi = 1 AND p.silindi_mi = 0 AND h.aktif_mi = 1 AND h.silindi_mi = 0
                ORDER BY h.sira_no, p.sira_no
            """)
            
            self.pozisyon_tanimlari = {}
            for row in cursor.fetchall():
                poz_no = row[0]
                self.pozisyon_tanimlari[poz_no] = {
                    'hat_id': row[1],
                    'hat_kodu': row[2],
                    'hat_adi': row[3],
                    'pozisyon_adi': row[4],
                    'kisa_ad': row[5],
                    'pozisyon_tipi': row[6],
                    'banyo_tipi': row[7],
                    'sicaklik_min': row[8],
                    'sicaklik_max': row[9],
                    'sicaklik_hedef': row[10],
                    'akim_min': row[11],
                    'akim_max': row[12],
                    'akim_hedef': row[13],
                    'hacim_lt': row[14],
                    'sira_no': row[15]
                }
            
            conn.close()
            
            self.lbl_erp_status.setText(f"🟢 ERP ({len(self.pozisyon_tanimlari)} poz)")
            self.lbl_erp_status.setStyleSheet(f"color:{self.success};font-weight:bold;")
            
        except Exception as e:
            self.lbl_erp_status.setText("🔴 ERP Hata")
            self.lbl_erp_status.setStyleSheet(f"color:{self.error};font-weight:bold;")
            print(f"ERP tanım hatası: {e}")
    
    def _connect_plc(self):
        """PLC cache durumunu kontrol et"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Sync servisinin durumunu kontrol et
            cursor.execute("""
                SELECT servis_durumu, son_sync_tarihi, 
                       DATEDIFF(SECOND, son_sync_tarihi, GETDATE()) as gecen_sure
                FROM uretim.plc_sync_durum WHERE id = 1
            """)
            row = cursor.fetchone()
            conn.close()
            
            if row:
                durum, son_sync, gecen_sure = row
                if durum == 'CALISIYOR' and gecen_sure and gecen_sure < 60:
                    self.lbl_plc_status.setText("🟢 CACHE")
                    self.lbl_plc_status.setStyleSheet(f"color:{self.success};font-weight:bold;")
                elif durum == 'CALISIYOR':
                    self.lbl_plc_status.setText("🟡 CACHE")
                    self.lbl_plc_status.setStyleSheet(f"color:{self.warning};font-weight:bold;")
                else:
                    self.lbl_plc_status.setText("🔴 CACHE")
                    self.lbl_plc_status.setStyleSheet(f"color:{self.error};font-weight:bold;")
            else:
                self.lbl_plc_status.setText("⚪ CACHE")
                self.lbl_plc_status.setStyleSheet(f"color:{self.text_muted};")
                
        except Exception as e:
            self.lbl_plc_status.setText("🔴 HATA")
            self.lbl_plc_status.setStyleSheet(f"color:{self.error};font-weight:bold;")
            print(f"Cache durum hatası: {e}")
    
    def _refresh_plc_data(self):
        """Cache'den PLC verilerini yükle ve tablolara aktar"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Cache tablosundan oku - ÇOK HIZLI!
            cursor.execute("""
                SELECT 
                    kazan_no,
                    islem_sayisi_24s,
                    son_bara,
                    recete_no,
                    ort_sicaklik,
                    ort_akim,
                    toplam_miktar_24s,
                    son_islem,
                    ilk_islem_24s,
                    durum,
                    durum_dakika
                FROM uretim.plc_cache
                ORDER BY kazan_no
            """)
            cache_rows = cursor.fetchall()
            conn.close()
            
            # PLC verilerini dict'e çevir
            self.plc_data = {}
            for row in cache_rows:
                kzn_no = row[0]
                self.plc_data[kzn_no] = {
                    'islem_sayisi': row[1] or 0,
                    'son_bara': row[2],
                    'recete': row[3],
                    'ort_sicaklik': row[4],
                    'ort_akim': row[5],
                    'toplam_miktar': row[6] or 0,
                    'son_islem': row[7],
                    'ilk_islem': row[8],
                    'durum': row[9],
                    'durum_dakika': row[10]
                }
            
            # Tabloları güncelle
            self._update_main_table()
            self._update_istatistik_table()
            self._update_tanimsiz_table()
            self._update_cards()
            # Akım tabı sadece aktif tab ise güncelle (ağır sorgu)
            if hasattr(self, 'tabs') and self.tabs.currentIndex() == 8:
                self._update_akim_table()
            
            # ERP vardiya tablosunu PLC verileriyle senkronize et
            self._sync_vardiya_to_erp()
            
            self.lbl_update.setText(f"Son: {datetime.now().strftime('%H:%M:%S')}")
            
            # Cache durumunu kontrol et
            self._connect_plc()
            
        except Exception as e:
            print(f"Cache veri hatası: {e}")
            self.lbl_plc_status.setText("🔴 HATA")
            self.lbl_plc_status.setStyleSheet(f"color:{self.error};font-weight:bold;")
    
    def _update_main_table(self):
        """Ana birleşik tabloyu güncelle"""
        # Veri yoksa çık
        if not self.pozisyon_tanimlari and not self.plc_data:
            return
        
        now = datetime.now()
        
        # Tüm pozisyonları birleştir (tanımlı + PLC)
        all_positions = set(self.pozisyon_tanimlari.keys()) | set(self.plc_data.keys())
        
        # Filtreler
        hat_filter = self.cmb_hat.currentData()
        durum_filter = self.cmb_durum.currentData()
        show_tanimsiz = self.chk_tanimsiz.isChecked()
        
        rows_data = []
        
        for poz_no in sorted(all_positions):
            tanim = self.pozisyon_tanimlari.get(poz_no)
            plc = self.plc_data.get(poz_no)
            
            # Tanımsız kontrolü
            if not tanim and not show_tanimsiz:
                continue
            
            # Hat filtresi
            if hat_filter and tanim and tanim['hat_id'] != hat_filter:
                continue
            
            # Durum hesapla
            durum = "⚪ Veri Yok"
            durum_key = None
            durum_color = self.text_muted
            uyari = False
            
            if plc and plc['son_islem']:
                delta = now - plc['son_islem']
                dakika = int(delta.total_seconds() / 60)
                
                if dakika < 5:
                    durum = "🟢 Aktif"
                    durum_key = "aktif"
                    durum_color = self.success
                elif dakika < 30:
                    durum = "🟡 Bekliyor"
                    durum_key = "bekliyor"
                    durum_color = self.warning
                else:
                    durum = "🔴 Durdu"
                    durum_key = "durdu"
                    durum_color = self.error
                
                # Sıcaklık uyarı kontrolü
                if tanim and plc['ort_sicaklik']:
                    sic = plc['ort_sicaklik']
                    sic_min = tanim.get('sicaklik_min')
                    sic_max = tanim.get('sicaklik_max')
                    if sic_min and sic < sic_min:
                        uyari = True
                    if sic_max and sic > sic_max:
                        uyari = True
            
            if uyari:
                durum_key = "uyari"
            
            # Durum filtresi
            if durum_filter and durum_key != durum_filter:
                continue
            
            rows_data.append({
                'poz_no': poz_no,
                'tanim': tanim,
                'plc': plc,
                'durum': durum,
                'durum_color': durum_color,
                'uyari': uyari
            })
        
        # Tabloya aktar
        self.tbl_main.setRowCount(len(rows_data))
        
        for i, data in enumerate(rows_data):
            poz_no = data['poz_no']
            tanim = data['tanim']
            plc = data['plc']
            
            # Poz No
            item = QTableWidgetItem(str(poz_no))
            if not tanim:
                item.setForeground(QBrush(QColor(self.warning)))
                item.setToolTip("⚠️ Tanımsız pozisyon")
            self.tbl_main.setItem(i, 0, item)
            
            # Hat
            hat_kodu = tanim['hat_kodu'] if tanim else "-"
            self.tbl_main.setItem(i, 1, QTableWidgetItem(hat_kodu))
            
            # Pozisyon Adı
            poz_adi = tanim['pozisyon_adi'] if tanim else f"Tanımsız ({poz_no})"
            item = QTableWidgetItem(poz_adi)
            if not tanim:
                item.setForeground(QBrush(QColor(self.warning)))
            self.tbl_main.setItem(i, 2, item)
            
            # Tip
            tip = tanim['pozisyon_tipi'] if tanim else "-"
            self.tbl_main.setItem(i, 3, QTableWidgetItem(tip))
            
            # Banyo
            banyo = tanim['banyo_tipi'] if tanim else "-"
            self.tbl_main.setItem(i, 4, QTableWidgetItem(banyo or "-"))
            
            # Durum
            item = QTableWidgetItem(data['durum'])
            item.setForeground(QBrush(QColor(data['durum_color'])))
            item.setFont(QFont("", -1, QFont.Bold))
            self.tbl_main.setItem(i, 5, item)
            
            # Bara
            bara = str(plc['son_bara']) if plc and plc['son_bara'] else "-"
            self.tbl_main.setItem(i, 6, QTableWidgetItem(bara))
            
            # Reçete
            recete = str(plc['recete']) if plc and plc['recete'] else "-"
            self.tbl_main.setItem(i, 7, QTableWidgetItem(recete))
            
            # Sıcaklık
            if plc and plc['ort_sicaklik']:
                sic = plc['ort_sicaklik']
                item = QTableWidgetItem(f"{sic:.1f}°C")
                
                # Limit kontrolü
                if tanim:
                    sic_min = tanim.get('sicaklik_min')
                    sic_max = tanim.get('sicaklik_max')
                    if (sic_min and sic < sic_min) or (sic_max and sic > sic_max):
                        item.setForeground(QBrush(QColor(self.error)))
                        item.setFont(QFont("", -1, QFont.Bold))
            else:
                item = QTableWidgetItem("-")
            self.tbl_main.setItem(i, 8, item)
            
            # Hedef Sıcaklık
            hedef = f"{tanim['sicaklik_hedef']:.0f}°C" if tanim and tanim.get('sicaklik_hedef') else "-"
            self.tbl_main.setItem(i, 9, QTableWidgetItem(hedef))
            
            # Limit
            if tanim and (tanim.get('sicaklik_min') or tanim.get('sicaklik_max')):
                sic_min = tanim.get('sicaklik_min') or 0
                sic_max = tanim.get('sicaklik_max') or 999
                limit = f"{sic_min:.0f}-{sic_max:.0f}°C"
            else:
                limit = "-"
            self.tbl_main.setItem(i, 10, QTableWidgetItem(limit))
            
            # Akım (limit kontrolü ile)
            if plc and plc['ort_akim']:
                akim = plc['ort_akim']
                item = QTableWidgetItem(f"{akim:.1f} A")
                if tanim:
                    akim_min = tanim.get('akim_min')
                    akim_max = tanim.get('akim_max')
                    akim_hedef = tanim.get('akim_hedef')
                    if (akim_min and akim < akim_min) or (akim_max and akim > akim_max):
                        item.setForeground(QBrush(QColor(self.error)))
                        item.setFont(QFont("", -1, QFont.Bold))
                    elif akim_hedef and abs(akim - akim_hedef) <= akim_hedef * 0.1:
                        item.setForeground(QBrush(QColor(self.success)))
            else:
                item = QTableWidgetItem("-")
            self.tbl_main.setItem(i, 11, item)
            
            # Miktar
            miktar = f"{plc['toplam_miktar']:,.0f}" if plc and plc['toplam_miktar'] else "0"
            self.tbl_main.setItem(i, 12, QTableWidgetItem(miktar))
            
            # Son İşlem
            son = plc['son_islem'].strftime("%d.%m %H:%M:%S") if plc and plc['son_islem'] else "-"
            self.tbl_main.setItem(i, 13, QTableWidgetItem(son))
    
    def _update_istatistik_table(self):
        """Günlük istatistik tablosu"""
        rows_data = []
        
        for poz_no in sorted(self.plc_data.keys()):
            tanim = self.pozisyon_tanimlari.get(poz_no)
            plc = self.plc_data[poz_no]
            
            rows_data.append({
                'poz_no': poz_no,
                'hat_kodu': tanim['hat_kodu'] if tanim else "-",
                'pozisyon_adi': tanim['pozisyon_adi'] if tanim else f"Tanımsız ({poz_no})",
                'plc': plc
            })
        
        self.tbl_istatistik.setRowCount(len(rows_data))
        
        for i, data in enumerate(rows_data):
            plc = data['plc']
            
            self.tbl_istatistik.setItem(i, 0, QTableWidgetItem(data['hat_kodu']))
            self.tbl_istatistik.setItem(i, 1, QTableWidgetItem(str(data['poz_no'])))
            self.tbl_istatistik.setItem(i, 2, QTableWidgetItem(data['pozisyon_adi']))
            self.tbl_istatistik.setItem(i, 3, QTableWidgetItem(f"{plc['islem_sayisi']:,}"))
            self.tbl_istatistik.setItem(i, 4, QTableWidgetItem(str(plc['son_bara'] or 0)))
            self.tbl_istatistik.setItem(i, 5, QTableWidgetItem(f"{plc['toplam_miktar']:,.0f}" if plc['toplam_miktar'] else "0"))
            self.tbl_istatistik.setItem(i, 6, QTableWidgetItem(f"{plc['ort_sicaklik']:.1f}°C" if plc['ort_sicaklik'] else "-"))
            self.tbl_istatistik.setItem(i, 7, QTableWidgetItem(plc['ilk_islem'].strftime("%H:%M") if plc['ilk_islem'] else "-"))
            self.tbl_istatistik.setItem(i, 8, QTableWidgetItem(plc['son_islem'].strftime("%H:%M") if plc['son_islem'] else "-"))
    
    def _update_tanimsiz_table(self):
        """Tanımsız pozisyonlar tablosu"""
        tanimsiz = []
        
        for poz_no, plc in self.plc_data.items():
            if poz_no not in self.pozisyon_tanimlari:
                tanimsiz.append((poz_no, plc))
        
        self.tbl_tanimsiz.setRowCount(len(tanimsiz))
        
        for i, (poz_no, plc) in enumerate(sorted(tanimsiz)):
            self.tbl_tanimsiz.setItem(i, 0, QTableWidgetItem(str(poz_no)))
            self.tbl_tanimsiz.setItem(i, 1, QTableWidgetItem(f"{plc['islem_sayisi']:,}"))
            self.tbl_tanimsiz.setItem(i, 2, QTableWidgetItem(str(plc['son_bara'] or "-")))
            self.tbl_tanimsiz.setItem(i, 3, QTableWidgetItem(str(plc['recete'] or "-")))
            self.tbl_tanimsiz.setItem(i, 4, QTableWidgetItem(f"{plc['ort_sicaklik']:.1f}°C" if plc['ort_sicaklik'] else "-"))
            self.tbl_tanimsiz.setItem(i, 5, QTableWidgetItem(f"{plc['toplam_miktar']:,.0f}" if plc['toplam_miktar'] else "0"))
            self.tbl_tanimsiz.setItem(i, 6, QTableWidgetItem(plc['son_islem'].strftime("%d.%m %H:%M") if plc['son_islem'] else "-"))
        
        # Tab başlığını güncelle
        tanimsiz_count = len(tanimsiz)
        if tanimsiz_count > 0:
            self.tabs.setTabText(3, f"❓ Tanımsız ({tanimsiz_count})")
        else:
            self.tabs.setTabText(3, "❓ Tanımsız Pozisyonlar")
    
    def _update_schema(self):
        """Hat şeması görselini güncelle"""
        # Önce temizle
        while self.schema_layout.count():
            item = self.schema_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        hat_id = self.cmb_schema_hat.currentData()
        if not hat_id:
            return
        
        now = datetime.now()
        col = 0
        row_idx = 0
        max_col = 8
        
        # Bu hattaki pozisyonları sırala
        hat_pozisyonlari = [
            (poz_no, tanim) for poz_no, tanim in self.pozisyon_tanimlari.items()
            if tanim['hat_id'] == hat_id
        ]
        hat_pozisyonlari.sort(key=lambda x: x[1]['sira_no'])
        
        for poz_no, tanim in hat_pozisyonlari:
            plc = self.plc_data.get(poz_no)
            
            # Durum belirleme
            if plc and plc['son_islem']:
                delta = now - plc['son_islem']
                dakika = int(delta.total_seconds() / 60)
                if dakika < 5:
                    color = self.success
                    status = "AKTİF"
                elif dakika < 30:
                    color = self.warning
                    status = "BEKLİYOR"
                else:
                    color = self.error
                    status = "DURDU"
            else:
                color = self.text_muted
                status = "VERİ YOK"
            
            # Sıcaklık uyarı
            sic_uyari = False
            if plc and plc['ort_sicaklik'] and tanim:
                sic = plc['ort_sicaklik']
                if (tanim.get('sicaklik_min') and sic < tanim['sicaklik_min']) or \
                   (tanim.get('sicaklik_max') and sic > tanim['sicaklik_max']):
                    sic_uyari = True
                    color = self.error
            
            # Pozisyon kartı
            card = QFrame()
            card.setFixedSize(130, 110)
            card.setStyleSheet(f"""
                QFrame{{
                    background:{self.bg_input};
                    border:2px solid {color};
                    border-radius:8px;
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 6, 8, 6)
            cl.setSpacing(2)
            
            # Pozisyon no ve kısa ad
            lbl_poz = QLabel(f"P{poz_no}")
            lbl_poz.setStyleSheet(f"color:{self.text};font-weight:bold;font-size:12px;")
            lbl_poz.setAlignment(Qt.AlignCenter)
            cl.addWidget(lbl_poz)
            
            lbl_ad = QLabel(tanim.get('kisa_ad') or tanim['pozisyon_adi'][:12])
            lbl_ad.setStyleSheet(f"color:{self.text_muted};font-size:9px;")
            lbl_ad.setAlignment(Qt.AlignCenter)
            cl.addWidget(lbl_ad)
            
            lbl_status = QLabel(status)
            lbl_status.setStyleSheet(f"color:{color};font-size:10px;font-weight:bold;")
            lbl_status.setAlignment(Qt.AlignCenter)
            cl.addWidget(lbl_status)
            
            if plc and plc['ort_sicaklik']:
                sic_color = self.error if sic_uyari else self.text_muted
                lbl_temp = QLabel(f"🌡️ {plc['ort_sicaklik']:.0f}°C")
                lbl_temp.setStyleSheet(f"color:{sic_color};font-size:10px;")
                lbl_temp.setAlignment(Qt.AlignCenter)
                cl.addWidget(lbl_temp)
            
            if plc and plc['toplam_miktar']:
                lbl_miktar = QLabel(f"📦 {plc['toplam_miktar']:,.0f}")
                lbl_miktar.setStyleSheet(f"color:{self.text_muted};font-size:10px;")
                lbl_miktar.setAlignment(Qt.AlignCenter)
                cl.addWidget(lbl_miktar)
            
            self.schema_layout.addWidget(card, row_idx, col)
            
            col += 1
            if col >= max_col:
                col = 0
                row_idx += 1
    
    def _update_cards(self):
        """Özet kartlarını güncelle"""
        now = datetime.now()
        aktif = 0
        toplam_miktar = 0
        toplam_bara = 0
        uyari_sayisi = 0
        
        for poz_no, plc in self.plc_data.items():
            tanim = self.pozisyon_tanimlari.get(poz_no)
            
            # Aktif sayısı
            if plc['son_islem']:
                delta = now - plc['son_islem']
                if delta.total_seconds() < 300:  # 5 dakika
                    aktif += 1
            
            toplam_miktar += plc['toplam_miktar'] or 0
            toplam_bara += plc['son_bara'] or 0
            
            # Uyarı kontrolü - Sıcaklık
            if tanim and plc['ort_sicaklik']:
                sic = plc['ort_sicaklik']
                if (tanim.get('sicaklik_min') and sic < tanim['sicaklik_min']) or \
                   (tanim.get('sicaklik_max') and sic > tanim['sicaklik_max']):
                    uyari_sayisi += 1

            # Uyarı kontrolü - Akım
            if tanim and plc['ort_akim']:
                akim = plc['ort_akim']
                if (tanim.get('akim_min') and akim < tanim['akim_min']) or \
                   (tanim.get('akim_max') and akim > tanim['akim_max']):
                    uyari_sayisi += 1
        
        # Tanımsız pozisyonları da uyarıya ekle
        tanimsiz_count = len([p for p in self.plc_data.keys() if p not in self.pozisyon_tanimlari])
        uyari_sayisi += tanimsiz_count
        
        self.card_aktif.findChild(QLabel, "val").setText(str(aktif))
        self.card_uretim.findChild(QLabel, "val").setText(f"{toplam_miktar:,.0f}")
        self.card_bara.findChild(QLabel, "val").setText(f"{toplam_bara:,}")
        self.card_uyari.findChild(QLabel, "val").setText(str(uyari_sayisi))
    
    def _update_akim_table(self):
        """Akım takip tablosunu güncelle - plc_tarihce'den son akım verilerini çeker"""
        if not hasattr(self, 'tbl_akim'):
            return

        hat_filtre = self.cmb_akim_hat.currentData()
        sadece_aktif = self.chk_sadece_aktif_akim.isChecked()
        sadece_uyari = self.chk_sadece_uyari_akim.isChecked()

        # plc_tarihce'den her kazan için son akım değerini çek
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                WITH son_akim AS (
                    SELECT
                        kazan_no,
                        akim,
                        akim_yogunlugu,
                        tarih_doldurma,
                        ROW_NUMBER() OVER (PARTITION BY kazan_no ORDER BY tarih_doldurma DESC) as rn
                    FROM uretim.plc_tarihce
                    WHERE akim IS NOT NULL AND akim > 0
                )
                SELECT kazan_no, akim, akim_yogunlugu, tarih_doldurma
                FROM son_akim WHERE rn = 1
                ORDER BY kazan_no
            """)
            tarihce_rows = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"Akım tarihçe hatası: {e}")
            tarihce_rows = []

        # Dict'e çevir
        akim_data = {}
        for row in tarihce_rows:
            akim_data[row[0]] = {
                'akim': float(row[1]),
                'akim_yogunlugu': float(row[2]) if row[2] else None,
                'son_tarih': row[3]
            }

        rows = []
        toplam_akim = 0
        akim_sayisi = 0
        uyari_sayisi = 0
        now = datetime.now()

        for poz_no in sorted(akim_data.keys()):
            ad = akim_data[poz_no]
            tanim = self.pozisyon_tanimlari.get(poz_no)

            # Hat filtresi
            if hat_filtre and tanim:
                if tanim.get('hat_kodu') != hat_filtre:
                    continue
            elif hat_filtre and not tanim:
                # Hat kodu olmayan pozisyonları hat numarasından belirle
                if hat_filtre == 'KTL' and not (101 <= poz_no <= 143):
                    continue
                elif hat_filtre == 'ZNNI' and not (201 <= poz_no <= 247):
                    continue
                elif hat_filtre == 'ON' and not (1 <= poz_no <= 23):
                    continue

            # Aktif filtresi - son 24 saat içinde akım verisi olanlar
            if sadece_aktif:
                delta = now - ad['son_tarih']
                if delta.total_seconds() > 86400:  # 24 saat
                    continue

            akim = ad['akim']

            # Limit bilgileri
            akim_min = tanim.get('akim_min') if tanim else None
            akim_max = tanim.get('akim_max') if tanim else None
            akim_hedef = tanim.get('akim_hedef') if tanim else None

            # Durum hesapla
            durum = "Normal"
            is_uyari = False
            if akim_min and akim < akim_min:
                durum = "DÜŞÜK"
                is_uyari = True
            elif akim_max and akim > akim_max:
                durum = "YÜKSEK"
                is_uyari = True
            elif akim_hedef and abs(akim - akim_hedef) <= akim_hedef * 0.1:
                durum = "Hedefte"

            # Sapma hesapla
            sapma = None
            if akim_hedef and akim_hedef > 0:
                sapma = ((akim - akim_hedef) / akim_hedef) * 100

            if is_uyari:
                uyari_sayisi += 1

            if sadece_uyari and not is_uyari:
                continue

            # Geçen süre
            gecen = now - ad['son_tarih']
            if gecen.total_seconds() < 60:
                gecen_str = f"{int(gecen.total_seconds())} sn önce"
            elif gecen.total_seconds() < 3600:
                gecen_str = f"{int(gecen.total_seconds() / 60)} dk önce"
            elif gecen.total_seconds() < 86400:
                gecen_str = f"{int(gecen.total_seconds() / 3600)} sa önce"
            else:
                gecen_str = ad['son_tarih'].strftime("%d.%m %H:%M")

            toplam_akim += akim
            akim_sayisi += 1

            rows.append({
                'poz_no': poz_no,
                'hat_kodu': tanim['hat_kodu'] if tanim else "-",
                'pozisyon_adi': tanim['pozisyon_adi'] if tanim else f"Tanımsız ({poz_no})",
                'banyo_tipi': tanim.get('banyo_tipi', '-') if tanim else '-',
                'akim': akim,
                'akim_yogunlugu': ad.get('akim_yogunlugu'),
                'hedef': akim_hedef,
                'akim_min': akim_min,
                'akim_max': akim_max,
                'sapma': sapma,
                'durum': durum,
                'is_uyari': is_uyari,
                'gecen_str': gecen_str
            })

        # Tablo doldur
        self.tbl_akim.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.tbl_akim.setItem(i, 0, QTableWidgetItem(str(r['poz_no'])))
            self.tbl_akim.setItem(i, 1, QTableWidgetItem(r['hat_kodu']))
            self.tbl_akim.setItem(i, 2, QTableWidgetItem(r['pozisyon_adi']))
            self.tbl_akim.setItem(i, 3, QTableWidgetItem(r['banyo_tipi'] or '-'))

            # Anlık Akım - büyük ve renkli
            akim_item = QTableWidgetItem(f"{r['akim']:.0f} A")
            akim_item.setFont(QFont("", 11, QFont.Bold))
            if r['is_uyari']:
                akim_item.setForeground(QBrush(QColor(self.error)))
            elif r['durum'] == "Hedefte":
                akim_item.setForeground(QBrush(QColor(self.success)))
            else:
                akim_item.setForeground(QBrush(QColor(self.text)))
            akim_item.setTextAlignment(Qt.AlignCenter)
            self.tbl_akim.setItem(i, 4, akim_item)

            # Hedef
            hedef_txt = f"{r['hedef']:.0f} A" if r['hedef'] else "-"
            self.tbl_akim.setItem(i, 5, QTableWidgetItem(hedef_txt))

            # Min
            min_txt = f"{r['akim_min']:.0f}" if r['akim_min'] else "-"
            self.tbl_akim.setItem(i, 6, QTableWidgetItem(min_txt))

            # Max
            max_txt = f"{r['akim_max']:.0f}" if r['akim_max'] else "-"
            self.tbl_akim.setItem(i, 7, QTableWidgetItem(max_txt))

            # Sapma %
            if r['sapma'] is not None:
                sapma_item = QTableWidgetItem(f"{r['sapma']:+.1f}%")
                if abs(r['sapma']) > 20:
                    sapma_item.setForeground(QBrush(QColor(self.error)))
                elif abs(r['sapma']) > 10:
                    sapma_item.setForeground(QBrush(QColor(self.warning)))
                sapma_item.setTextAlignment(Qt.AlignCenter)
            else:
                sapma_item = QTableWidgetItem("-")
            self.tbl_akim.setItem(i, 8, sapma_item)

            # Durum + süre
            durum_txt = f"{r['durum']} ({r['gecen_str']})"
            durum_item = QTableWidgetItem(durum_txt)
            durum_item.setFont(QFont("", -1, QFont.Bold))
            if r['durum'] == "DÜŞÜK":
                durum_item.setForeground(QBrush(QColor("#F59E0B")))
            elif r['durum'] == "YÜKSEK":
                durum_item.setForeground(QBrush(QColor(self.error)))
            elif r['durum'] == "Hedefte":
                durum_item.setForeground(QBrush(QColor(self.success)))
            durum_item.setTextAlignment(Qt.AlignCenter)
            self.tbl_akim.setItem(i, 9, durum_item)

        # Özet bilgisi
        ort_akim = toplam_akim / akim_sayisi if akim_sayisi > 0 else 0
        self.lbl_akim_ozet.setText(
            f"Toplam: {akim_sayisi} banyo  |  Ort: {ort_akim:.0f} A  |  Uyarı: {uyari_sayisi}"
        )

    def _on_tab_changed(self, index):
        """Tab değiştiğinde ilgili tabı güncelle"""
        if index == 8:  # Akım Takip tabı
            self._update_akim_table()

    def _load_vardiya_combo(self):
        """Vardiya tanımlarını DB'den yükle (beyaz yaka hariç)"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad, baslangic_saati, bitis_saati
                FROM tanim.vardiyalar
                WHERE aktif_mi = 1 AND kod NOT LIKE '%BY%'
                ORDER BY baslangic_saati
            """)
            for row in cursor.fetchall():
                # baslangic/bitis saatlerini dakikaya çevir (datetime.time objesi)
                bas = row[3]
                bit = row[4]
                bas_dk = bas.hour * 60 + bas.minute
                bit_dk = bit.hour * 60 + bit.minute
                label = f"{row[2]} ({bas.strftime('%H:%M')} - {bit.strftime('%H:%M')})"
                self.cmb_vr_vardiya.addItem(label, {'id': row[0], 'kod': row[1], 'bas_dk': bas_dk, 'bit_dk': bit_dk})
            # 3 Vardiya Toplam seçeneği (00:00 - 00:00 tam gün)
            self.cmb_vr_vardiya.addItem("3 Vardiya Toplam (00:00 - 00:00)", {'id': 0, 'kod': 'TOPLAM', 'bas_dk': 0, 'bit_dk': 0})
            conn.close()
        except Exception as e:
            print(f"Vardiya yükleme hatası: {e}")
            # Fallback
            self.cmb_vr_vardiya.addItem("V1 - Sabah (07:30-15:30)", {'id': 1, 'kod': 'V1', 'bas_dk': 450, 'bit_dk': 930})
            self.cmb_vr_vardiya.addItem("V2 - Akşam (15:30-23:30)", {'id': 2, 'kod': 'V2', 'bas_dk': 930, 'bit_dk': 1410})
            self.cmb_vr_vardiya.addItem("V3 - Gece (23:30-07:30)", {'id': 3, 'kod': 'V3', 'bas_dk': 1410, 'bit_dk': 450})
            self.cmb_vr_vardiya.addItem("3 Vardiya Toplam (00:00 - 00:00)", {'id': 0, 'kod': 'TOPLAM', 'bas_dk': 0, 'bit_dk': 0})

    def _load_vardiya_raporu(self):
        """Vardiya bazlı üretim raporu yükle
        Bara sayımı: Bara Dashboard mantığı ile giriş kazanları (K101/K118=KTL, K201=CINKO)
        Her giriş kaydı = 1 bara. Reçete adımlarından sıralı takiple gerçek süre hesaplanır.
        """
        vardiya = self.cmb_vr_vardiya.currentData()
        if not vardiya:
            return

        hat_filtre = self.cmb_vr_hat.currentData()
        secilen_tarih = self.de_vr_tarih.date().toPython()

        bas_dk = vardiya['bas_dk']
        bit_dk = vardiya['bit_dk']

        if vardiya['kod'] == 'TOPLAM':
            vardiya_bas = "CAST(? AS DATETIME)"
            vardiya_bit = "DATEADD(DAY, 1, CAST(? AS DATETIME))"
            params = [secilen_tarih, secilen_tarih]
        elif bas_dk < bit_dk:
            vardiya_bas = f"DATEADD(MINUTE, {bas_dk}, CAST(? AS DATETIME))"
            vardiya_bit = f"DATEADD(MINUTE, {bit_dk}, CAST(? AS DATETIME))"
            params = [secilen_tarih, secilen_tarih]
        else:
            vardiya_bas = f"DATEADD(MINUTE, {bas_dk}, CAST(? AS DATETIME))"
            vardiya_bit = f"DATEADD(MINUTE, {bit_dk}, DATEADD(DAY, 1, CAST(? AS DATETIME)))"
            params = [secilen_tarih, secilen_tarih]

        if hat_filtre == 'KTL':
            giris_where = "AND g.kazan_no IN (101, 118)"
        elif hat_filtre == 'CINKO':
            giris_where = "AND g.kazan_no = 201"
        else:
            giris_where = ""

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1) Giriş kayıtlarını al
            cursor.execute(f"""
                SELECT g.id, g.kazan_no, g.recete_no, g.recete_adim, g.tarih_doldurma,
                    CASE WHEN g.kazan_no IN (101, 118) THEN 'KTL'
                         WHEN g.kazan_no = 201 THEN 'CINKO' END as hat
                FROM uretim.plc_tarihce g
                WHERE g.kazan_no IN (101, 118, 201)
                  AND g.recete_no > 0
                  AND g.tarih_doldurma >= {vardiya_bas}
                  AND g.tarih_doldurma < {vardiya_bit}
                  {giris_where}
                ORDER BY g.tarih_doldurma
            """, params)
            girisler = cursor.fetchall()

            # 2) PLC'den reçete adım tanımlarını al (cache)
            from core.database import get_plc_connection
            plc_conn = get_plc_connection()
            pc = plc_conn.cursor()
            pc.execute("SELECT Panel_Recete_No, AdimNo, Kazan_No, Zamanlar FROM dbo.ReceteAdimlar WHERE Kazan_No != 129 ORDER BY Panel_Recete_No, AdimNo")
            recete_cache = {}
            for r in pc.fetchall():
                recete_cache.setdefault(r[0], []).append((r[1], r[2], r[3]))
            plc_conn.close()

            # 3) Her bara için sıralı adım takibi ile gerçek süre hesapla
            rows_data = []
            ktl_sira = 0
            cinko_sira = 0

            for giris_row in girisler:
                giris_id, giris_kazan, recete_no, giris_adim, giris_zamani, hat_kodu = giris_row

                if hat_kodu == 'KTL':
                    ktl_sira += 1
                    sira = ktl_sira
                else:
                    cinko_sira += 1
                    sira = cinko_sira

                adimlar = recete_cache.get(recete_no, [])
                # Giriş adımından itibaren adımları filtrele
                adimlar = [(a, k, s) for a, k, s in adimlar if a >= (giris_adim or 1)]

                # Beklenen süre: reçete adımlarının toplam süresi (giriş adımından itibaren)
                beklenen_sn_toplam = sum(s for _, _, s in adimlar)
                beklenen_dk = round(beklenen_sn_toplam / 60) if beklenen_sn_toplam > 0 else None

                if not adimlar:
                    rows_data.append((sira, hat_kodu, recete_no, giris_zamani, None, None, beklenen_dk, 0, 0, None, None, giris_adim or 1))
                    continue

                # Sıralı adım takibi
                son_zaman = giris_zamani
                cikis_zamani = giris_zamani
                toplam_akim = 0
                akim_sayisi = 0
                toplam_sic = 0
                sic_sayisi = 0
                kazan_set = set()

                for adim_no, kazan_no, beklenen_sn in adimlar:
                    cursor.execute("""
                        SELECT TOP 1 tarih_doldurma, tarih_bosaltma, akim, sicaklik
                        FROM uretim.plc_tarihce
                        WHERE recete_no = ? AND recete_adim = ? AND kazan_no = ?
                          AND tarih_doldurma >= ? AND tarih_doldurma < DATEADD(HOUR, 4, ?)
                        ORDER BY tarih_doldurma
                    """, [recete_no, adim_no, kazan_no, son_zaman, giris_zamani])
                    r = cursor.fetchone()
                    if r:
                        son_zaman = r[0]
                        if r[1] and r[1] > cikis_zamani:
                            cikis_zamani = r[1]
                        elif r[0] > cikis_zamani:
                            cikis_zamani = r[0]
                        kazan_set.add(kazan_no)
                        if r[2] and r[2] > 0:
                            toplam_akim += r[2]
                            akim_sayisi += 1
                        if r[3] and r[3] > 0:
                            toplam_sic += r[3]
                            sic_sayisi += 1

                gercek_dk = int((cikis_zamani - giris_zamani).total_seconds() / 60) if cikis_zamani > giris_zamani else None
                ort_akim = toplam_akim / akim_sayisi if akim_sayisi > 0 else None
                ort_sic = toplam_sic / sic_sayisi if sic_sayisi > 0 else None

                rows_data.append((sira, hat_kodu, recete_no, giris_zamani, cikis_zamani,
                                  gercek_dk, beklenen_dk, len(kazan_set), max((a for a, _, _ in adimlar), default=0),
                                  ort_akim, ort_sic, giris_adim or 1))

            conn.close()

            # Tabloya yaz
            self.tbl_vr.setRowCount(len(rows_data))
            self._vr_row_data = []
            toplam_sapma = 0
            sapma_sayisi = 0
            ktl_count = 0
            cinko_count = 0

            for i, rd in enumerate(rows_data):
                sira, hat_kodu, recete_no, giris, cikis, gercek_dk, beklenen_dk, kazan_say, adim_say, ort_akim, ort_sic, g_adim = rd
                self._vr_row_data.append({
                    'hat': hat_kodu, 'recete_no': recete_no, 'giris': giris, 'cikis': cikis,
                    'gercek_dk': gercek_dk, 'beklenen_dk': beklenen_dk, 'giris_adim': g_adim
                })

                if hat_kodu == 'KTL':
                    ktl_count += 1
                elif hat_kodu == 'CINKO':
                    cinko_count += 1

                self.tbl_vr.setItem(i, 0, QTableWidgetItem(str(sira)))
                self.tbl_vr.setItem(i, 1, QTableWidgetItem(hat_kodu or "-"))
                self.tbl_vr.setItem(i, 2, QTableWidgetItem(f"R{recete_no}"))
                self.tbl_vr.setItem(i, 3, QTableWidgetItem(giris.strftime("%H:%M") if giris else "-"))
                self.tbl_vr.setItem(i, 4, QTableWidgetItem(cikis.strftime("%H:%M") if cikis else "-"))

                gercek_item = QTableWidgetItem(f"{gercek_dk} dk" if gercek_dk is not None else "-")
                gercek_item.setTextAlignment(Qt.AlignCenter)
                self.tbl_vr.setItem(i, 5, gercek_item)

                beklenen_item = QTableWidgetItem(f"{beklenen_dk} dk" if beklenen_dk else "-")
                beklenen_item.setTextAlignment(Qt.AlignCenter)
                self.tbl_vr.setItem(i, 6, beklenen_item)

                if gercek_dk is not None and beklenen_dk and beklenen_dk > 0:
                    sapma_pct = ((gercek_dk - beklenen_dk) / beklenen_dk) * 100
                    sapma_item = QTableWidgetItem(f"{sapma_pct:+.0f}%")
                    sapma_item.setFont(QFont("", -1, QFont.Bold))
                    if abs(sapma_pct) > 50:
                        sapma_item.setForeground(QBrush(QColor(self.error)))
                    elif abs(sapma_pct) > 20:
                        sapma_item.setForeground(QBrush(QColor(self.warning)))
                    elif abs(sapma_pct) <= 10:
                        sapma_item.setForeground(QBrush(QColor(self.success)))
                    sapma_item.setTextAlignment(Qt.AlignCenter)
                    toplam_sapma += sapma_pct
                    sapma_sayisi += 1
                else:
                    sapma_item = QTableWidgetItem("-")
                self.tbl_vr.setItem(i, 7, sapma_item)

                if ort_akim:
                    akim_item = QTableWidgetItem(f"{ort_akim:.0f} A")
                    akim_item.setFont(QFont("", -1, QFont.Bold))
                    akim_item.setForeground(QBrush(QColor(self.primary)))
                else:
                    akim_item = QTableWidgetItem("-")
                akim_item.setTextAlignment(Qt.AlignCenter)
                self.tbl_vr.setItem(i, 8, akim_item)

                sic_item = QTableWidgetItem(f"{ort_sic:.1f}°C" if ort_sic else "-")
                sic_item.setTextAlignment(Qt.AlignCenter)
                self.tbl_vr.setItem(i, 9, sic_item)

                self.tbl_vr.setItem(i, 10, QTableWidgetItem(str(adim_say or "-")))
                self.tbl_vr.setItem(i, 11, QTableWidgetItem(str(kazan_say or "-")))

            self.card_vr_bara.findChild(QLabel, "val").setText(str(len(rows_data)))
            self.card_vr_ktl.findChild(QLabel, "val").setText(str(ktl_count))
            self.card_vr_cinko.findChild(QLabel, "val").setText(str(cinko_count))
            ort_sapma = toplam_sapma / sapma_sayisi if sapma_sayisi > 0 else 0
            self.card_vr_sapma.findChild(QLabel, "val").setText(f"{ort_sapma:+.0f}%")

        except Exception as e:
            print(f"Vardiya raporu hatası: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Hata", f"Rapor yüklenirken hata:\n{str(e)}")

    def _show_bara_detay(self, index):
        """Seçilen baranın adım detaylarını göster - reçete adımlarından sıralı takip"""
        row = index.row()
        if not hasattr(self, '_vr_row_data') or row >= len(self._vr_row_data):
            return

        data = self._vr_row_data[row]
        hat = data['hat']
        recete_no = data['recete_no']
        giris = data['giris']
        cikis = data['cikis']
        giris_adim = data.get('giris_adim', 1)

        if not giris:
            return

        try:
            from core.database import get_plc_connection

            # 1) PLC'den reçete adım tanımlarını al (giriş adımından itibaren)
            plc_conn = get_plc_connection()
            pc = plc_conn.cursor()
            pc.execute("""
                SELECT AdimNo, Kazan_No, Zamanlar
                FROM dbo.ReceteAdimlar
                WHERE Panel_Recete_No = ? AND AdimNo >= ? AND Kazan_No != 129
                ORDER BY AdimNo
            """, [recete_no, giris_adim])
            recete_adimlari = [(r[0], r[1], r[2]) for r in pc.fetchall()]
            plc_conn.close()

            if not recete_adimlari:
                QMessageBox.information(self, "Bilgi", f"R{recete_no} için reçete adımı bulunamadı")
                return

            # 2) ERP tarihçesinden her adım için sıralı kayıt bul
            conn = get_db_connection()
            cursor = conn.cursor()

            adimlar = []
            son_zaman = giris  # Her adım bir öncekinin zamanından sonra olmalı

            for adim_no, kazan_no, beklenen_sn in recete_adimlari:
                cursor.execute("""
                    SELECT TOP 1
                        t.kazan_no, t.recete_adim, t.tarih_doldurma, t.tarih_bosaltma,
                        DATEDIFF(SECOND, t.tarih_doldurma, ISNULL(t.tarih_bosaltma, GETDATE())) as sure_sn,
                        t.akim, t.sicaklik
                    FROM uretim.plc_tarihce t
                    WHERE t.recete_no = ? AND t.recete_adim = ? AND t.kazan_no = ?
                      AND t.tarih_doldurma >= ?
                      AND t.tarih_doldurma < DATEADD(HOUR, 4, ?)
                    ORDER BY t.tarih_doldurma
                """, [recete_no, adim_no, kazan_no, son_zaman, giris])

                r = cursor.fetchone()
                if r:
                    adimlar.append((r[0], r[1], r[2], r[3], r[4], beklenen_sn, r[5], r[6], f"K{kazan_no}"))
                    # Sonraki adımı bu adımın doldurma zamanından sonra ara
                    son_zaman = r[2]
                else:
                    # Kayıt bulunamadı - atlanan adım
                    adimlar.append((kazan_no, adim_no, None, None, None, beklenen_sn, None, None, f"K{kazan_no}"))

            conn.close()

            # Dialog oluştur
            dlg = QDialog(self)
            dlg.setWindowTitle(f"Bara Detay - {hat} R{recete_no} ({giris.strftime('%H:%M')})")
            dlg.setMinimumSize(900, 500)
            dlg.setStyleSheet(f"QDialog{{background:{self.bg_main};}}")
            lay = QVBoxLayout(dlg)

            # Özet bilgi
            ozet = QLabel(f"Hat: {hat}  |  Reçete: R{recete_no}  |  Giriş: {giris.strftime('%H:%M:%S')}  |  "
                          f"Çıkış: {cikis.strftime('%H:%M:%S') if cikis else 'Devam'}  |  "
                          f"Gerçek: {data['gercek_dk']} dk  |  Beklenen: {data['beklenen_dk']} dk")
            ozet.setStyleSheet(f"color:{self.text};font-size:13px;padding:8px;background:{self.bg_card};border-radius:6px;")
            lay.addWidget(ozet)

            # Adım tablosu
            tbl = QTableWidget()
            tbl.setColumnCount(9)
            tbl.setHorizontalHeaderLabels([
                "Adım", "Kazan", "Banyo", "Doldurma", "Boşaltma",
                "Gerçek (sn)", "Beklenen (sn)", "Fark (sn)", "Akım"
            ])
            tbl.setRowCount(len(adimlar))
            tbl.setSelectionBehavior(QTableWidget.SelectRows)
            tbl.verticalHeader().setVisible(False)
            self._tbl_style(tbl)
            tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

            toplam_fazla = 0
            for i, a in enumerate(adimlar):
                kazan, adim, dol, bos, sure_sn, beklenen_sn, akim, sic, banyo = a

                tbl.setItem(i, 0, QTableWidgetItem(str(adim or "-")))
                tbl.setItem(i, 1, QTableWidgetItem(f"K{kazan}"))
                tbl.setItem(i, 2, QTableWidgetItem(banyo or f"Kazan {kazan}"))
                tbl.setItem(i, 3, QTableWidgetItem(dol.strftime("%H:%M:%S") if dol else "-"))
                tbl.setItem(i, 4, QTableWidgetItem(bos.strftime("%H:%M:%S") if bos else "-"))

                sure_item = QTableWidgetItem(str(sure_sn) if sure_sn is not None else "-")
                sure_item.setTextAlignment(Qt.AlignCenter)
                tbl.setItem(i, 5, sure_item)

                beklenen_item = QTableWidgetItem(str(beklenen_sn) if beklenen_sn else "-")
                beklenen_item.setTextAlignment(Qt.AlignCenter)
                tbl.setItem(i, 6, beklenen_item)

                # Fark hesapla
                if sure_sn is not None and beklenen_sn and beklenen_sn > 0:
                    fark = sure_sn - beklenen_sn
                    fark_item = QTableWidgetItem(f"{fark:+d}")
                    fark_item.setTextAlignment(Qt.AlignCenter)
                    fark_item.setFont(QFont("", -1, QFont.Bold))
                    if fark > 60:
                        fark_item.setForeground(QBrush(QColor(self.error)))
                        toplam_fazla += fark
                    elif fark > 20:
                        fark_item.setForeground(QBrush(QColor(self.warning)))
                        toplam_fazla += fark
                    elif fark <= 5:
                        fark_item.setForeground(QBrush(QColor(self.success)))
                elif sure_sn is not None and (not beklenen_sn or beklenen_sn == 0) and sure_sn > 30:
                    fark_item = QTableWidgetItem(f"+{sure_sn} (bekleme)")
                    fark_item.setTextAlignment(Qt.AlignCenter)
                    fark_item.setFont(QFont("", -1, QFont.Bold))
                    fark_item.setForeground(QBrush(QColor(self.warning)))
                    toplam_fazla += sure_sn
                else:
                    fark_item = QTableWidgetItem("-")
                tbl.setItem(i, 7, fark_item)

                akim_item = QTableWidgetItem(f"{akim:.0f} A" if akim and akim > 0 else "-")
                akim_item.setTextAlignment(Qt.AlignCenter)
                tbl.setItem(i, 8, akim_item)

            lay.addWidget(tbl)

            # Alt özet
            if toplam_fazla > 0:
                alt = QLabel(f"Toplam fazla bekleme: {toplam_fazla} sn ({toplam_fazla//60} dk {toplam_fazla%60} sn)")
                alt.setStyleSheet(f"color:{self.error};font-size:13px;font-weight:bold;padding:8px;")
                lay.addWidget(alt)

            dlg.exec()

        except Exception as e:
            print(f"Bara detay hatası: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Hata", f"Detay yüklenirken hata:\n{str(e)}")

    def _filter_table(self):
        """Tablo filtreleme"""
        self._update_main_table()
    
    def _sync_vardiya_to_erp(self):
        """Cache verilerinden giren/çıkan bara sayılarını hesapla ve ERP'ye yaz"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Bugünün vardiya saatini hesapla (07:30 baz)
            now = datetime.now()
            if now.hour < 7 or (now.hour == 7 and now.minute < 30):
                # Dünün vardiyası
                vardiya_baslangic = now.replace(hour=7, minute=30, second=0, microsecond=0) - timedelta(days=1)
            else:
                vardiya_baslangic = now.replace(hour=7, minute=30, second=0, microsecond=0)
            
            # KTL Giriş: Pozisyon 118 (plc_tarihce'den)
            cursor.execute("""
                SELECT COUNT(*) FROM uretim.plc_tarihce 
                WHERE kazan_no = 118 AND tarih_doldurma >= ?
            """, (vardiya_baslangic,))
            ktl_giren = cursor.fetchone()[0] or 0
            
            # KTL Çıkış: Pozisyon 101
            cursor.execute("""
                SELECT COUNT(*) FROM uretim.plc_tarihce 
                WHERE kazan_no = 101 AND tarih_doldurma >= ?
            """, (vardiya_baslangic,))
            ktl_cikan = cursor.fetchone()[0] or 0
            
            # CINKO Giriş: Pozisyon 236
            cursor.execute("""
                SELECT COUNT(*) FROM uretim.plc_tarihce 
                WHERE kazan_no = 236 AND tarih_doldurma >= ?
            """, (vardiya_baslangic,))
            cinko_giren = cursor.fetchone()[0] or 0
            
            # CINKO Çıkış: Pozisyon 201
            cursor.execute("""
                SELECT COUNT(*) FROM uretim.plc_tarihce 
                WHERE kazan_no = 201 AND tarih_doldurma >= ?
            """, (vardiya_baslangic,))
            cinko_cikan = cursor.fetchone()[0] or 0
            
            bugun = vardiya_baslangic.date()
            
            # KTL güncelle
            cursor.execute("""
                UPDATE uretim.vardiya_uretim 
                SET giren_bara = ?, cikan_bara = ?, guncelleme_tarihi = GETDATE()
                WHERE vardiya_tarihi = ? AND hat_tipi = 'KTL'
            """, (ktl_giren, ktl_cikan, bugun))
            
            # Eğer kayıt yoksa oluştur
            if cursor.rowcount == 0:
                vardiya_bitis = vardiya_baslangic + timedelta(days=1)
                cursor.execute("""
                    INSERT INTO uretim.vardiya_uretim (vardiya_tarihi, vardiya_baslangic, vardiya_bitis, hat_tipi, giren_bara, cikan_bara)
                    VALUES (?, ?, ?, 'KTL', ?, ?)
                """, (bugun, vardiya_baslangic, vardiya_bitis, ktl_giren, ktl_cikan))
            
            # CINKO güncelle
            cursor.execute("""
                UPDATE uretim.vardiya_uretim 
                SET giren_bara = ?, cikan_bara = ?, guncelleme_tarihi = GETDATE()
                WHERE vardiya_tarihi = ? AND hat_tipi = 'CINKO'
            """, (cinko_giren, cinko_cikan, bugun))
            
            # Eğer kayıt yoksa oluştur
            if cursor.rowcount == 0:
                vardiya_bitis = vardiya_baslangic + timedelta(days=1)
                cursor.execute("""
                    INSERT INTO uretim.vardiya_uretim (vardiya_tarihi, vardiya_baslangic, vardiya_bitis, hat_tipi, giren_bara, cikan_bara)
                    VALUES (?, ?, ?, 'CINKO', ?, ?)
                """, (bugun, vardiya_baslangic, vardiya_bitis, cinko_giren, cinko_cikan))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Vardiya senkronizasyon hatası: {e}")
    
    def _load_bos_kalma_analizi(self):
        """Boş kalma analizi - Her pozisyonun ne kadar süre boş kaldığını hesapla"""
        esik_dk = self.cmb_bos_esik.currentData()
        siralama = self.cmb_bos_sirala.currentData()
        tarih_secim = self.cmb_bos_tarih.currentData()
        hat_secim = self.cmb_bos_hat.currentData()
        
        # Tarih aralığını hesapla
        now = datetime.now()
        if tarih_secim == "bugun":
            # Bugünün vardiyası (07:30'dan itibaren)
            if now.hour < 7 or (now.hour == 7 and now.minute < 30):
                baslangic = now.replace(hour=7, minute=30, second=0, microsecond=0) - timedelta(days=1)
            else:
                baslangic = now.replace(hour=7, minute=30, second=0, microsecond=0)
            bitis = now
        elif tarih_secim == "dun":
            # Dünün vardiyası
            dun = now - timedelta(days=1)
            baslangic = dun.replace(hour=7, minute=30, second=0, microsecond=0)
            bitis = baslangic + timedelta(days=1)
        elif tarih_secim == "hafta":
            baslangic = now - timedelta(days=7)
            bitis = now
        else:  # 24saat
            baslangic = now - timedelta(hours=24)
            bitis = now
        
        # Hat filtresi için pozisyon aralığı
        hat_kosul = ""
        if hat_secim == "KTL":
            hat_kosul = "AND kazan_no BETWEEN 101 AND 143"
        elif hat_secim == "CINKO":
            hat_kosul = "AND kazan_no BETWEEN 201 AND 247"
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Her pozisyon için detaylı işlem zamanlarını al (plc_tarihce'den)
            cursor.execute(f"""
                SELECT 
                    kazan_no,
                    tarih_doldurma
                FROM uretim.plc_tarihce
                WHERE tarih_doldurma >= ? AND tarih_doldurma <= ?
                {hat_kosul}
                ORDER BY kazan_no, tarih_doldurma
            """, (baslangic, bitis))
            rows = cursor.fetchall()
            conn.close()
            
            # Pozisyon bazlı gruplama ve boş kalma hesaplama
            poz_islemler = {}
            for kzn_no, tarih in rows:
                if kzn_no not in poz_islemler:
                    poz_islemler[kzn_no] = []
                poz_islemler[kzn_no].append(tarih)
            
            # Boş kalma hesapla
            bos_kalma_data = []
            now = datetime.now()
            
            for poz_no, islemler in poz_islemler.items():
                if len(islemler) < 1:
                    continue
                
                islemler.sort()
                ilk_islem = islemler[0]
                son_islem = islemler[-1]
                toplam_islem = len(islemler)
                
                # İşlemler arası boşlukları hesapla
                bos_sureler = []
                en_uzun_bosluk = 0
                
                for i in range(1, len(islemler)):
                    fark = (islemler[i] - islemler[i-1]).total_seconds() / 60  # dakika
                    if fark > esik_dk:
                        bos_sureler.append(fark)
                        if fark > en_uzun_bosluk:
                            en_uzun_bosluk = fark
                
                # Son işlemden şimdiye kadar boşluk
                son_bosluk = (now - son_islem).total_seconds() / 60
                if son_bosluk > esik_dk:
                    bos_sureler.append(son_bosluk)
                    if son_bosluk > en_uzun_bosluk:
                        en_uzun_bosluk = son_bosluk
                
                toplam_bos = sum(bos_sureler)
                toplam_sure = (now - ilk_islem).total_seconds() / 60
                calisma_sure = toplam_sure - toplam_bos
                bos_yuzde = (toplam_bos / toplam_sure * 100) if toplam_sure > 0 else 0
                
                tanim = self.pozisyon_tanimlari.get(poz_no)
                
                bos_kalma_data.append({
                    'poz_no': poz_no,
                    'hat_kodu': tanim['hat_kodu'] if tanim else '-',
                    'pozisyon_adi': tanim['pozisyon_adi'] if tanim else f'Tanımsız ({poz_no})',
                    'toplam_islem': toplam_islem,
                    'calisma_dk': calisma_sure,
                    'bos_dk': toplam_bos,
                    'bos_yuzde': bos_yuzde,
                    'en_uzun_bosluk': en_uzun_bosluk,
                    'ilk_islem': ilk_islem,
                    'son_islem': son_islem
                })
            
            # Sıralama
            if siralama == "bos_desc":
                bos_kalma_data.sort(key=lambda x: x['bos_dk'], reverse=True)
            elif siralama == "bos_asc":
                bos_kalma_data.sort(key=lambda x: x['bos_dk'])
            else:
                bos_kalma_data.sort(key=lambda x: x['poz_no'])
            
            # Tabloya aktar
            self.tbl_bos_kalma.setRowCount(len(bos_kalma_data))
            
            for i, data in enumerate(bos_kalma_data):
                self.tbl_bos_kalma.setItem(i, 0, QTableWidgetItem(str(data['poz_no'])))
                self.tbl_bos_kalma.setItem(i, 1, QTableWidgetItem(data['hat_kodu']))
                self.tbl_bos_kalma.setItem(i, 2, QTableWidgetItem(data['pozisyon_adi']))
                self.tbl_bos_kalma.setItem(i, 3, QTableWidgetItem(f"{data['toplam_islem']:,}"))
                self.tbl_bos_kalma.setItem(i, 4, QTableWidgetItem(f"{data['calisma_dk']:.0f}"))
                
                # Boş kalma - renklendirme
                bos_item = QTableWidgetItem(f"{data['bos_dk']:.0f}")
                if data['bos_yuzde'] > 50:
                    bos_item.setForeground(QBrush(QColor(self.error)))
                    bos_item.setFont(QFont("", -1, QFont.Bold))
                elif data['bos_yuzde'] > 25:
                    bos_item.setForeground(QBrush(QColor(self.warning)))
                self.tbl_bos_kalma.setItem(i, 5, bos_item)
                
                # Boş yüzde
                yuzde_item = QTableWidgetItem(f"{data['bos_yuzde']:.1f}%")
                if data['bos_yuzde'] > 50:
                    yuzde_item.setForeground(QBrush(QColor(self.error)))
                    yuzde_item.setFont(QFont("", -1, QFont.Bold))
                elif data['bos_yuzde'] > 25:
                    yuzde_item.setForeground(QBrush(QColor(self.warning)))
                self.tbl_bos_kalma.setItem(i, 6, yuzde_item)
                
                # En uzun boşluk
                uzun_item = QTableWidgetItem(f"{data['en_uzun_bosluk']:.0f} dk")
                if data['en_uzun_bosluk'] > 60:
                    uzun_item.setForeground(QBrush(QColor(self.error)))
                self.tbl_bos_kalma.setItem(i, 7, uzun_item)
                
                self.tbl_bos_kalma.setItem(i, 8, QTableWidgetItem(data['ilk_islem'].strftime("%H:%M")))
                self.tbl_bos_kalma.setItem(i, 9, QTableWidgetItem(data['son_islem'].strftime("%H:%M")))
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Boş kalma analizi hatası: {e}")
    
    def _load_recete_analizi(self):
        """Reçete bazlı analiz"""
        gorunum = self.cmb_recete_gorunum.currentData()
        hat_filtre = self.cmb_recete_hat.currentData()

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            if gorunum == "sureler":
                self._load_recete_sureleri(cursor, hat_filtre)
                conn.close()
                return

            # Hat filtresi icin kazan araligi
            hat_kosul = ""
            if hat_filtre == "KTL":
                hat_kosul = "AND kazan_no BETWEEN 101 AND 143"
            elif hat_filtre == "ZNNI":
                hat_kosul = "AND kazan_no BETWEEN 201 AND 247"
            elif hat_filtre == "ON":
                hat_kosul = "AND kazan_no BETWEEN 1 AND 23"

            if gorunum == "ozet":
                cursor.execute(f"""
                    SELECT
                        t.recete_no,
                        COUNT(*) as islem_sayisi,
                        SUM(ISNULL(t.miktar, 0)) as toplam_miktar,
                        COUNT(DISTINCT t.kazan_no) as pozisyon_sayisi,
                        AVG(t.sicaklik) as ort_sicaklik,
                        AVG(t.akim) as ort_akim,
                        rt.recete_adi,
                        rt.recete_aciklama,
                        rt.hat_tipi,
                        rt.toplam_sure_dk,
                        AVG(CASE WHEN t.recete_zamani > 0 THEN t.recete_zamani END) as ort_plc_sure_sn
                    FROM uretim.plc_tarihce t
                    LEFT JOIN kaplama.plc_recete_tanimlari rt ON t.recete_no = rt.recete_no
                    WHERE t.tarih_doldurma >= DATEADD(hour, -24, GETDATE())
                      AND t.recete_no IS NOT NULL
                      {hat_kosul}
                    GROUP BY t.recete_no, rt.recete_adi, rt.recete_aciklama, rt.hat_tipi, rt.toplam_sure_dk
                    ORDER BY islem_sayisi DESC
                """)
                rows = cursor.fetchall()
                conn.close()

                self.tbl_recete.setColumnCount(11)
                self.tbl_recete.setHorizontalHeaderLabels([
                    "No", "Reçete Adı", "Açıklama", "Hat",
                    "Çevrim (dk)", "PLC Süre (dk)",
                    "İşlem", "Miktar", "Poz.",
                    "Ort. Sıcaklık", "Ort. Akım"
                ])
                col_widths = [50, 120, 150, 60, 85, 95, 70, 80, 50, 85, 75]
                for ci, w in enumerate(col_widths):
                    self.tbl_recete.setColumnWidth(ci, w)
                self.tbl_recete.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

                self.tbl_recete.setRowCount(len(rows))

                for i, row in enumerate(rows):
                    rec_no = row[0]
                    islem, miktar, poz_say = row[1], row[2], row[3]
                    sic, akim = row[4], row[5]
                    r_adi = row[6] or "-"
                    r_acik = row[7] or "-"
                    r_hat = row[8] or "-"
                    r_sure_dk = row[9]
                    plc_sure_sn = row[10]

                    plc_sure_dk = f"{plc_sure_sn / 60:.1f}" if plc_sure_sn else "-"
                    sure_str = f"{r_sure_dk}" if r_sure_dk else "-"

                    self.tbl_recete.setItem(i, 0, QTableWidgetItem(str(rec_no)))
                    self.tbl_recete.setItem(i, 1, QTableWidgetItem(r_adi))
                    self.tbl_recete.setItem(i, 2, QTableWidgetItem(r_acik))
                    self.tbl_recete.setItem(i, 3, QTableWidgetItem(r_hat))
                    self.tbl_recete.setItem(i, 4, QTableWidgetItem(sure_str))
                    self.tbl_recete.setItem(i, 5, QTableWidgetItem(plc_sure_dk))
                    self.tbl_recete.setItem(i, 6, QTableWidgetItem(f"{islem:,}"))
                    self.tbl_recete.setItem(i, 7, QTableWidgetItem(f"{miktar:,.0f}" if miktar else "0"))
                    self.tbl_recete.setItem(i, 8, QTableWidgetItem(str(poz_say)))
                    self.tbl_recete.setItem(i, 9, QTableWidgetItem(f"{sic:.1f}°C" if sic else "-"))
                    self.tbl_recete.setItem(i, 10, QTableWidgetItem(f"{akim:.1f} A" if akim else "-"))

                    # Hat tipine gore satir rengi
                    hat_renk = {"KTL": "#1E3A5F", "ZNNI": "#3A2F0F", "ON": "#1F2F1F"}.get(r_hat, None)
                    if hat_renk:
                        for ci in range(11):
                            item = self.tbl_recete.item(i, ci)
                            if item:
                                item.setBackground(QBrush(QColor(hat_renk)))

            elif gorunum == "detay":
                cursor.execute(f"""
                    SELECT
                        t.recete_no,
                        t.kazan_no,
                        COUNT(*) as islem_sayisi,
                        SUM(ISNULL(t.miktar, 0)) as toplam_miktar,
                        AVG(t.sicaklik) as ort_sicaklik,
                        rt.recete_adi,
                        rt.recete_aciklama
                    FROM uretim.plc_tarihce t
                    LEFT JOIN kaplama.plc_recete_tanimlari rt ON t.recete_no = rt.recete_no
                    WHERE t.tarih_doldurma >= DATEADD(hour, -24, GETDATE())
                      AND t.recete_no IS NOT NULL
                      {hat_kosul}
                    GROUP BY t.recete_no, t.kazan_no, rt.recete_adi, rt.recete_aciklama
                    ORDER BY t.recete_no, islem_sayisi DESC
                """)
                rows = cursor.fetchall()
                conn.close()

                self.tbl_recete.setColumnCount(8)
                self.tbl_recete.setHorizontalHeaderLabels([
                    "Reçete No", "Reçete Adı", "Pozisyon", "Pozisyon Adı",
                    "İşlem Sayısı", "Miktar", "Ort. Sıcaklık", "Açıklama"
                ])
                col_widths = [70, 120, 70, 160, 85, 80, 90, 150]
                for ci, w in enumerate(col_widths):
                    self.tbl_recete.setColumnWidth(ci, w)
                self.tbl_recete.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

                self.tbl_recete.setRowCount(len(rows))

                for i, row in enumerate(rows):
                    rec_no, kzn, islem, miktar, sic, r_adi, r_acik = row
                    tanim = self.pozisyon_tanimlari.get(kzn)

                    self.tbl_recete.setItem(i, 0, QTableWidgetItem(str(rec_no)))
                    self.tbl_recete.setItem(i, 1, QTableWidgetItem(r_adi or "-"))
                    self.tbl_recete.setItem(i, 2, QTableWidgetItem(str(kzn)))
                    self.tbl_recete.setItem(i, 3, QTableWidgetItem(tanim['pozisyon_adi'] if tanim else f'Tanımsız ({kzn})'))
                    self.tbl_recete.setItem(i, 4, QTableWidgetItem(f"{islem:,}"))
                    self.tbl_recete.setItem(i, 5, QTableWidgetItem(f"{miktar:,.0f}" if miktar else "0"))
                    self.tbl_recete.setItem(i, 6, QTableWidgetItem(f"{sic:.1f}°C" if sic else "-"))
                    self.tbl_recete.setItem(i, 7, QTableWidgetItem(r_acik or "-"))

        except Exception as e:
            print(f"Reçete analizi hatası: {e}")

    def _load_recete_sureleri(self, cursor, hat_filtre):
        """Recete surelerini goster - tanim + PLC gercek sure karsilastirmasi"""
        hat_kosul = ""
        params = []
        if hat_filtre:
            hat_kosul = "WHERE rt.hat_tipi = ?"
            params.append(hat_filtre)

        cursor.execute(f"""
            SELECT
                rt.recete_no,
                rt.recete_adi,
                rt.recete_aciklama,
                rt.hat_tipi,
                rt.toplam_sure_dk,
                (SELECT AVG(CASE WHEN t.recete_zamani > 0 THEN t.recete_zamani END)
                 FROM uretim.plc_tarihce t
                 WHERE t.recete_no = rt.recete_no
                   AND t.tarih_doldurma >= DATEADD(DAY, -30, GETDATE())) as ort_plc_sure_sn,
                (SELECT AVG(CASE WHEN t.tarih_doldurma IS NOT NULL AND t.tarih_bosaltma IS NOT NULL
                            THEN DATEDIFF(SECOND, t.tarih_doldurma, t.tarih_bosaltma) END)
                 FROM uretim.plc_tarihce t
                 WHERE t.recete_no = rt.recete_no
                   AND t.tarih_doldurma >= DATEADD(DAY, -30, GETDATE())) as ort_cevrim_sn,
                (SELECT COUNT(*)
                 FROM uretim.plc_tarihce t
                 WHERE t.recete_no = rt.recete_no
                   AND t.tarih_doldurma >= DATEADD(DAY, -30, GETDATE())) as kayit_sayisi,
                (SELECT MIN(t.tarih_doldurma)
                 FROM uretim.plc_tarihce t
                 WHERE t.recete_no = rt.recete_no
                   AND t.tarih_doldurma >= DATEADD(DAY, -30, GETDATE())) as ilk_kullanim,
                (SELECT MAX(t.tarih_doldurma)
                 FROM uretim.plc_tarihce t
                 WHERE t.recete_no = rt.recete_no
                   AND t.tarih_doldurma >= DATEADD(DAY, -30, GETDATE())) as son_kullanim
            FROM kaplama.plc_recete_tanimlari rt
            {hat_kosul}
            ORDER BY rt.hat_tipi, rt.recete_no
        """, params)
        rows = cursor.fetchall()

        self.tbl_recete.setColumnCount(10)
        self.tbl_recete.setHorizontalHeaderLabels([
            "No", "Reçete Adı", "Açıklama", "Hat",
            "Tanımlı Süre (dk)", "PLC Süre (dk)", "Çevrim Süre (dk)",
            "Kayıt (30gün)", "İlk Kullanım", "Son Kullanım"
        ])
        col_widths = [50, 120, 150, 60, 105, 95, 105, 90, 110, 110]
        for ci, w in enumerate(col_widths):
            self.tbl_recete.setColumnWidth(ci, w)
        self.tbl_recete.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        self.tbl_recete.setRowCount(len(rows))

        for i, row in enumerate(rows):
            rec_no = row[0]
            r_adi, r_acik, r_hat = row[1] or "-", row[2] or "-", row[3] or "-"
            tanim_sure = row[4]
            plc_sure_sn = row[5]
            cevrim_sn = row[6]
            kayit = row[7] or 0
            ilk_kul = row[8]
            son_kul = row[9]

            tanim_str = f"{tanim_sure}" if tanim_sure else "-"
            plc_str = f"{plc_sure_sn / 60:.1f}" if plc_sure_sn else "-"
            cevrim_str = f"{cevrim_sn / 60:.1f}" if cevrim_sn else "-"
            ilk_str = ilk_kul.strftime("%d.%m %H:%M") if ilk_kul else "-"
            son_str = son_kul.strftime("%d.%m %H:%M") if son_kul else "-"

            self.tbl_recete.setItem(i, 0, QTableWidgetItem(str(rec_no)))
            self.tbl_recete.setItem(i, 1, QTableWidgetItem(r_adi))
            self.tbl_recete.setItem(i, 2, QTableWidgetItem(r_acik))
            self.tbl_recete.setItem(i, 3, QTableWidgetItem(r_hat))
            self.tbl_recete.setItem(i, 4, QTableWidgetItem(tanim_str))
            self.tbl_recete.setItem(i, 5, QTableWidgetItem(plc_str))
            self.tbl_recete.setItem(i, 6, QTableWidgetItem(cevrim_str))
            self.tbl_recete.setItem(i, 7, QTableWidgetItem(f"{kayit:,}"))
            self.tbl_recete.setItem(i, 8, QTableWidgetItem(ilk_str))
            self.tbl_recete.setItem(i, 9, QTableWidgetItem(son_str))

            # Hat tipine gore satir rengi
            hat_renk = {"KTL": "#1E3A5F", "ZNNI": "#3A2F0F", "ON": "#1F2F1F"}.get(r_hat, None)
            if hat_renk:
                for ci in range(10):
                    item = self.tbl_recete.item(i, ci)
                    if item:
                        item.setBackground(QBrush(QColor(hat_renk)))

            # Sure uyumsuzlugu varsa vurgula
            if tanim_sure and plc_sure_sn:
                plc_dk = plc_sure_sn / 60
                fark = abs(plc_dk - tanim_sure) / tanim_sure
                if fark > 0.2:  # %20'den fazla fark
                    for ci in [4, 5]:
                        item = self.tbl_recete.item(i, ci)
                        if item:
                            item.setForeground(QBrush(QColor("#EF4444")))
    
    def _on_recete_double_click(self, index):
        """Recete satirina cift tiklayinca detay dialogu ac"""
        row = index.row()
        rec_item = self.tbl_recete.item(row, 0)
        if not rec_item:
            return
        try:
            recete_no = int(rec_item.text())
        except (ValueError, TypeError):
            return

        from modules.kaplama_planlama import db_operations as kp_db

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Reçete #{recete_no} - Detay")
        dlg.setMinimumSize(850, 550)
        dlg.setStyleSheet(f"QDialog{{background:{self.bg_card};}}")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Baslik
        lbl_title = QLabel(f"Reçete #{recete_no}")
        lbl_title.setStyleSheet(f"color:{self.text};font-size:18px;font-weight:bold;")
        layout.addWidget(lbl_title)

        # Recete tanimi
        tanim = kp_db.get_recete_by_no(recete_no)
        if tanim:
            lbl_title.setText(f"Reçete #{recete_no} - {tanim.get('recete_adi', '')} / {tanim.get('recete_aciklama', '')}")
            hat_str = tanim.get('hat_tipi') or "-"
            sure_dk = tanim.get('toplam_sure_dk')
            sure_str = f"{sure_dk} dk" if sure_dk else "Hesaplanmadı"
        else:
            hat_str, sure_str = "-", "-"

        # Ozet kartlari
        info_bar = QHBoxLayout()
        for label, value, color in [
            ("Hat", hat_str, self.s['info']),
            ("Çevrim Süresi", sure_str, self.s['success']),
        ]:
            card = QFrame()
            card.setStyleSheet(f"QFrame{{background:{color}22;border:1px solid {color}44;border-radius:6px;padding:8px;}}")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 4, 8, 4)
            cl.addWidget(QLabel(label, styleSheet=f"color:{self.s['text_muted']};font-size:10px;"))
            cl.addWidget(QLabel(value, styleSheet=f"color:{self.text};font-size:14px;font-weight:bold;"))
            info_bar.addWidget(card)
        info_bar.addStretch()
        layout.addLayout(info_bar)

        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane{{border:none;background:{self.bg_card};}}
            QTabBar::tab{{background:{self.s['input_bg']};color:{self.s['text_muted']};padding:8px 16px;margin-right:2px;border-radius:4px 4px 0 0;}}
            QTabBar::tab:selected{{background:{self.bg_card};color:{self.s['primary']};font-weight:bold;}}
        """)
        layout.addWidget(tabs)

        # --- Tab 1: Recete Adimlari ---
        tab1 = QWidget()
        t1_layout = QVBoxLayout(tab1)
        t1_layout.setContentsMargins(0, 8, 0, 0)

        tbl_adim = QTableWidget()
        tbl_adim.setSelectionBehavior(QTableWidget.SelectRows)
        tbl_adim.verticalHeader().setVisible(False)
        self._tbl_style(tbl_adim)
        t1_layout.addWidget(tbl_adim)

        adimlar = kp_db.get_recete_adimlari(recete_no)

        # Adim bazli gruplama (bir adimda birden fazla kazan olabilir - alternatif)
        adim_groups = {}
        for a in adimlar:
            adim_no = a['adim']
            if adim_no not in adim_groups:
                adim_groups[adim_no] = []
            adim_groups[adim_no].append(a)

        tbl_adim.setColumnCount(7)
        tbl_adim.setHorizontalHeaderLabels([
            "Adım", "Kazan", "Pozisyon Adı", "Süre (dk)", "Sıcaklık", "Akım", "Ortak"
        ])
        col_w = [50, 60, 200, 75, 75, 65, 60]
        for ci, w in enumerate(col_w):
            tbl_adim.setColumnWidth(ci, w)
        tbl_adim.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        # Her adimin en cok kullanilan kazanini ana satir, digerleri alternatif
        flat_rows = []
        toplam_sure_sn = 0
        for adim_no in sorted(adim_groups.keys()):
            grp = sorted(adim_groups[adim_no], key=lambda x: -x['kayit'])
            ana = grp[0]
            toplam_sure_sn += ana['sure_sn']
            alternatif_count = len(grp) - 1
            flat_rows.append((adim_no, ana, alternatif_count, True))
            for alt in grp[1:]:
                flat_rows.append((adim_no, alt, 0, False))

        tbl_adim.setRowCount(len(flat_rows))
        for i, (adim_no, a, alt_count, is_ana) in enumerate(flat_rows):
            sure_dk = a['sure_sn'] / 60 if a['sure_sn'] else 0

            adim_str = str(adim_no) if is_ana else ""
            tbl_adim.setItem(i, 0, QTableWidgetItem(adim_str))
            tbl_adim.setItem(i, 1, QTableWidgetItem(str(a['kazan_no'])))
            tbl_adim.setItem(i, 2, QTableWidgetItem(a['pozisyon_adi']))
            tbl_adim.setItem(i, 3, QTableWidgetItem(f"{sure_dk:.1f}"))
            tbl_adim.setItem(i, 4, QTableWidgetItem(f"{a['sicaklik']:.1f}°C" if a['sicaklik'] else "-"))
            tbl_adim.setItem(i, 5, QTableWidgetItem(f"{a['akim']:.1f} A" if a['akim'] else "-"))
            tbl_adim.setItem(i, 6, QTableWidgetItem(f"+{alt_count}" if alt_count > 0 and is_ana else ("alt" if not is_ana else "")))

            # Alternatif kazanlar icin soluk renk
            if not is_ana:
                for ci in range(7):
                    item = tbl_adim.item(i, ci)
                    if item:
                        item.setForeground(QBrush(QColor(self.s['text_muted'])))

        # Toplam satiri
        lbl_toplam = QLabel(f"Toplam Çevrim: {len(adim_groups)} adım, {toplam_sure_sn/60:.1f} dk ({toplam_sure_sn:.0f} sn)")
        lbl_toplam.setStyleSheet(f"color:{self.s['success']};font-size:13px;font-weight:bold;padding:6px;")
        t1_layout.addWidget(lbl_toplam)

        tabs.addTab(tab1, f"Reçete Adımları ({len(adim_groups)})")

        # --- Tab 2: Ortak Kazanlar ---
        tab2 = QWidget()
        t2_layout = QVBoxLayout(tab2)
        t2_layout.setContentsMargins(0, 8, 0, 0)

        tbl_ortak = QTableWidget()
        tbl_ortak.setSelectionBehavior(QTableWidget.SelectRows)
        tbl_ortak.verticalHeader().setVisible(False)
        self._tbl_style(tbl_ortak)
        t2_layout.addWidget(tbl_ortak)

        # Bu recetenin kazanlarini bul
        recete_kazanlar = set(a['kazan_no'] for a in adimlar)
        ortak_kazanlar = kp_db.get_ortak_kazanlar()

        # Sadece bu recetenin kazanlarini filtrele
        ilgili = [ok for ok in ortak_kazanlar if ok['kazan_no'] in recete_kazanlar]

        tbl_ortak.setColumnCount(4)
        tbl_ortak.setHorizontalHeaderLabels(["Kazan", "Pozisyon Adı", "Reçete Sayısı", "Paylaşan Reçeteler"])
        tbl_ortak.setColumnWidth(0, 60)
        tbl_ortak.setColumnWidth(1, 180)
        tbl_ortak.setColumnWidth(2, 90)
        tbl_ortak.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        tbl_ortak.setRowCount(len(ilgili))
        for i, ok in enumerate(ilgili):
            rec_list = [f"R{r['recete_no']}" for r in ok['receteler'] if r['recete_no'] != recete_no]
            tbl_ortak.setItem(i, 0, QTableWidgetItem(str(ok['kazan_no'])))
            tbl_ortak.setItem(i, 1, QTableWidgetItem(ok['pozisyon_adi']))
            tbl_ortak.setItem(i, 2, QTableWidgetItem(str(ok['recete_sayisi'])))
            tbl_ortak.setItem(i, 3, QTableWidgetItem(", ".join(rec_list)))

            # Cok paylasilan kazanlar icin renk
            if ok['recete_sayisi'] >= 15:
                for ci in range(4):
                    item = tbl_ortak.item(i, ci)
                    if item:
                        item.setBackground(QBrush(QColor("#3A1515")))
            elif ok['recete_sayisi'] >= 8:
                for ci in range(4):
                    item = tbl_ortak.item(i, ci)
                    if item:
                        item.setBackground(QBrush(QColor("#3A2F0F")))

        tabs.addTab(tab2, f"Ortak Kazanlar ({len(ilgili)})")

        # Kapat butonu
        btn_kapat = QPushButton("Kapat")
        btn_kapat.setStyleSheet(f"QPushButton{{background:{self.s['border']};color:{self.text};border:none;border-radius:6px;padding:8px 24px;}}")
        btn_kapat.clicked.connect(dlg.close)
        layout.addWidget(btn_kapat, alignment=Qt.AlignRight)

        dlg.exec()

    def _load_vardiya_ozet(self):
        """ERP'den vardiya özet bilgilerini yükle - Bulunduğumuz haftanın verileri"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Bugünün tarihini ve haftanın başlangıcını hesapla (Pazartesi)
            bugun = datetime.now().date()
            hafta_basi = bugun - timedelta(days=bugun.weekday())  # Pazartesi
            
            # Bulunduğumuz haftanın verilerini çek (Pazartesi'den bugüne kadar)
            cursor.execute("""
                SELECT 
                    vardiya_tarihi,
                    hat_tipi,
                    giren_bara,
                    cikan_bara,
                    COALESCE(hedef_bara, 0) as hedef_bara,
                    CASE 
                        WHEN CAST(vardiya_tarihi AS DATE) = CAST(GETDATE() AS DATE) THEN
                            DATEDIFF(MINUTE, vardiya_baslangic, GETDATE())
                        ELSE 1440  -- Geçmiş günler için tam gün
                    END as gecen_dakika,
                    CASE 
                        WHEN CAST(vardiya_tarihi AS DATE) = CAST(GETDATE() AS DATE) THEN
                            DATEDIFF(MINUTE, GETDATE(), vardiya_bitis)
                        ELSE 0  -- Geçmiş günler için kalan yok
                    END as kalan_dakika
                FROM uretim.vardiya_uretim
                WHERE vardiya_tarihi >= ? AND vardiya_tarihi <= ?
                ORDER BY vardiya_tarihi DESC, hat_tipi
            """, (hafta_basi, bugun))
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            # Bugünün verilerini kartlara yansıt
            for row in rows:
                data = dict(zip(columns, row))
                vardiya_tarihi = data.get('vardiya_tarihi')
                
                # Sadece bugünün verilerini kartlara yaz
                if vardiya_tarihi and (isinstance(vardiya_tarihi, datetime) and vardiya_tarihi.date() == bugun or vardiya_tarihi == bugun):
                    hat_tipi = data.get('hat_tipi')
                    giren = data.get('giren_bara', 0) or 0
                    cikan = data.get('cikan_bara', 0) or 0
                    
                    if hat_tipi == 'KTL':
                        self.card_ktl_giren.findChild(QLabel, "val").setText(str(giren))
                        self.card_ktl_cikan.findChild(QLabel, "val").setText(str(cikan))
                    elif hat_tipi == 'CINKO':
                        self.card_cinko_giren.findChild(QLabel, "val").setText(str(giren))
                        self.card_cinko_cikan.findChild(QLabel, "val").setText(str(cikan))
            
            # Tabloya aktar
            self.tbl_vardiya.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                data = dict(zip(columns, row))
                
                # Tarih formatını düzenle
                vardiya_tarihi = data.get('vardiya_tarihi', '')
                if isinstance(vardiya_tarihi, datetime):
                    tarih_str = vardiya_tarihi.strftime('%Y-%m-%d')
                else:
                    tarih_str = str(vardiya_tarihi)
                
                self.tbl_vardiya.setItem(i, 0, QTableWidgetItem(tarih_str))
                self.tbl_vardiya.setItem(i, 1, QTableWidgetItem(data.get('hat_tipi', '')))
                self.tbl_vardiya.setItem(i, 2, QTableWidgetItem(str(data.get('giren_bara', 0) or 0)))
                self.tbl_vardiya.setItem(i, 3, QTableWidgetItem(str(data.get('cikan_bara', 0) or 0)))
                self.tbl_vardiya.setItem(i, 4, QTableWidgetItem(str(data.get('hedef_bara', 0) or 0)))
                
                # Kalan hesapla
                cikan_bara = data.get('cikan_bara', 0) or 0
                hedef_bara = data.get('hedef_bara', 0) or 0
                kalan = hedef_bara - cikan_bara if hedef_bara > 0 else 0
                self.tbl_vardiya.setItem(i, 5, QTableWidgetItem(str(kalan)))
                
                # Verimlilik hesapla
                if hedef_bara > 0:
                    verim = (cikan_bara / hedef_bara) * 100
                    verim_item = QTableWidgetItem(f"{verim:.1f}%")
                    if verim >= 100:
                        verim_item.setForeground(QBrush(QColor(self.success)))
                        verim_item.setFont(QFont("", -1, QFont.Bold))
                    elif verim < 80:
                        verim_item.setForeground(QBrush(QColor(self.error)))
                else:
                    verim_item = QTableWidgetItem("-")
                self.tbl_vardiya.setItem(i, 6, verim_item)
                
                self.tbl_vardiya.setItem(i, 7, QTableWidgetItem(str(data.get('gecen_dakika', 0) or 0)))
                self.tbl_vardiya.setItem(i, 8, QTableWidgetItem(str(data.get('kalan_dakika', 0) or 0)))
                
                # Durum
                if hedef_bara > 0:
                    oran = cikan_bara / hedef_bara * 100
                    if oran >= 100:
                        durum = "✅ Hedef Tamam"
                        durum_color = self.success
                    elif oran >= 80:
                        durum = "🟢 İyi"
                        durum_color = self.success
                    elif oran >= 50:
                        durum = "🟡 Orta"
                        durum_color = self.warning
                    else:
                        durum = "🔴 Düşük"
                        durum_color = self.error
                else:
                    durum = "⚪ Hedef Yok"
                    durum_color = self.text_muted
                
                durum_item = QTableWidgetItem(durum)
                durum_item.setForeground(QBrush(QColor(durum_color)))
                self.tbl_vardiya.setItem(i, 9, durum_item)
                
        except Exception as e:
            print(f"Vardiya özet hatası: {e}")
    
    def _load_darbogaz_analizi(self):
        """Dar boğaz analizi - reçete sürelerine ve banyo gruplarına göre verimlilik hesapla"""
        tarih_secim = self.cmb_dar_tarih.currentData()
        hat_secim = self.cmb_dar_hat.currentData()
        
        # Banyo grupları tanımı (paralel çalışan banyolar)
        BANYO_GRUPLARI = {
            'AYA': ([14, 15], 2),
            'SYA': ([5, 6, 7, 8], 4),
            'FIRIN': ([114, 115, 116, 117], 4),
            'YUKLEME_KTL': ([131, 132, 133, 134, 135, 136, 137, 138, 139, 140], 10),
            'ALKALI_CINKO': ([210, 211, 212, 213, 214], 5),
            'KURUTMA': ([235, 237], 2),
            'YUKLEME_CINKO': ([238, 239, 240, 241, 242, 243, 244, 245, 246, 247], 10),
        }
        
        # Tank -> Grup eşleştirmesi
        tank_grup = {}
        for grup_adi, (tanklar, adet) in BANYO_GRUPLARI.items():
            for tank in tanklar:
                tank_grup[tank] = (grup_adi, adet)
        
        # Tarih aralığını hesapla
        now = datetime.now()
        if tarih_secim == "bugun":
            if now.hour < 7 or (now.hour == 7 and now.minute < 30):
                baslangic = now.replace(hour=7, minute=30, second=0, microsecond=0) - timedelta(days=1)
            else:
                baslangic = now.replace(hour=7, minute=30, second=0, microsecond=0)
            bitis = now
        elif tarih_secim == "dun":
            dun = now - timedelta(days=1)
            baslangic = dun.replace(hour=7, minute=30, second=0, microsecond=0)
            bitis = baslangic + timedelta(days=1)
        else:
            baslangic = now - timedelta(days=7)
            bitis = now
        
        vardiya_sure = (bitis - baslangic).total_seconds() / 60
        
        hat_kosul = ""
        if hat_secim == "KTL":
            hat_kosul = "AND t.kazan_no BETWEEN 101 AND 143"
        elif hat_secim == "CINKO":
            hat_kosul = "AND t.kazan_no BETWEEN 201 AND 247"
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # plc_tarihce'den veri çek, recete süreleri için PLC DB'deki ReceteAdimlar'a bağlan
            cursor.execute(f"""
                SELECT 
                    t.kazan_no,
                    t.recete_no,
                    COUNT(*) as islem_sayisi,
                    MIN(t.tarih_doldurma) as ilk_islem,
                    MAX(t.tarih_doldurma) as son_islem,
                    DATEDIFF(MINUTE, MIN(t.tarih_doldurma), MAX(t.tarih_doldurma)) as aktif_sure_dk,
                    ISNULL(t.recete_zamani, 0) as zamanlar_sn
                FROM uretim.plc_tarihce t
                WHERE t.tarih_doldurma >= ? AND t.tarih_doldurma <= ?
                {hat_kosul}
                GROUP BY t.kazan_no, t.recete_no, t.recete_zamani
                HAVING COUNT(*) > 1
                ORDER BY t.kazan_no
            """, (baslangic, bitis))
            rows = cursor.fetchall()
            conn.close()
            
            # Pozisyon bazlı toplama
            poz_data = {}
            
            for row in rows:
                kzn_no, recete_no, islem_sayisi, ilk_islem, son_islem, aktif_sure, zamanlar_sn = row
                
                aktif_sure = float(aktif_sure) if aktif_sure else 0
                zamanlar_sn = float(zamanlar_sn) if zamanlar_sn else 0
                
                recete_sure_dk = zamanlar_sn / 60
                
                if recete_sure_dk == 0 and islem_sayisi > 1 and aktif_sure > 0:
                    recete_sure_dk = aktif_sure / (islem_sayisi - 1)
                
                beklenen_calisma = recete_sure_dk * islem_sayisi
                
                if kzn_no not in poz_data:
                    poz_data[kzn_no] = {
                        'toplam_islem': 0, 'toplam_beklenen': 0, 'aktif_sure': 0,
                        'ilk_islem': ilk_islem, 'son_islem': son_islem, 'recete_sureler': []
                    }
                
                poz_data[kzn_no]['toplam_islem'] += islem_sayisi
                poz_data[kzn_no]['toplam_beklenen'] += beklenen_calisma
                if recete_sure_dk > 0:
                    poz_data[kzn_no]['recete_sureler'].append(recete_sure_dk)
                
                if aktif_sure > poz_data[kzn_no]['aktif_sure']:
                    poz_data[kzn_no]['aktif_sure'] = aktif_sure
            
            # Grup bazlı toplama
            grup_data = {}
            
            for poz_no, data in poz_data.items():
                if poz_no in tank_grup:
                    grup_adi, grup_adet = tank_grup[poz_no]
                else:
                    grup_adi = f"POZ_{poz_no}"
                    grup_adet = 1
                
                if grup_adi not in grup_data:
                    grup_data[grup_adi] = {
                        'pozisyonlar': [], 'grup_adet': grup_adet, 'toplam_islem': 0,
                        'toplam_beklenen': 0, 'aktif_sure': 0, 'recete_sureler': []
                    }
                
                grup_data[grup_adi]['pozisyonlar'].append(poz_no)
                grup_data[grup_adi]['toplam_islem'] += data['toplam_islem']
                grup_data[grup_adi]['toplam_beklenen'] += data['toplam_beklenen']
                grup_data[grup_adi]['recete_sureler'].extend(data['recete_sureler'])
                
                if data['aktif_sure'] > grup_data[grup_adi]['aktif_sure']:
                    grup_data[grup_adi]['aktif_sure'] = data['aktif_sure']
            
            # Verimlilik hesapla
            darbogaz_data = []
            
            for grup_adi, data in grup_data.items():
                aktif_sure = data['aktif_sure']
                beklenen = data['toplam_beklenen']
                islem_sayisi = data['toplam_islem']
                grup_adet = data['grup_adet']
                
                if aktif_sure <= 0:
                    continue
                
                # Grup kapasitesi = Banyo Adedi × Aktif Süre
                grup_kapasitesi = grup_adet * aktif_sure
                
                # Verimlilik = Beklenen Çalışma / Grup Kapasitesi × 100
                verimlilik = (beklenen / grup_kapasitesi * 100) if grup_kapasitesi > 0 else 0
                verimlilik = min(verimlilik, 100)
                
                bos_dk = max(0, grup_kapasitesi - beklenen)
                bos_yuzde = (bos_dk / grup_kapasitesi * 100) if grup_kapasitesi > 0 else 0
                
                ort_recete_sure = sum(data['recete_sureler']) / len(data['recete_sureler']) if data['recete_sureler'] else 0
                
                darbogaz_skoru = 100 - verimlilik + (bos_dk / 100)
                
                if grup_adi.startswith('POZ_'):
                    poz_no = int(grup_adi.split('_')[1])
                    tanim = self.pozisyon_tanimlari.get(poz_no)
                    pozisyon_adi = tanim['pozisyon_adi'] if tanim else f'Tanımsız ({poz_no})'
                else:
                    pozisyon_adi = grup_adi.replace('_', ' ')
                
                poz_listesi = data['pozisyonlar']
                ornek_poz = poz_listesi[0] if poz_listesi else 0
                if 101 <= ornek_poz <= 143:
                    hat = "KTL"
                elif 201 <= ornek_poz <= 247:
                    hat = "CINKO"
                else:
                    hat = "ORTAK"
                
                darbogaz_data.append({
                    'grup_adi': grup_adi, 'pozisyonlar': data['pozisyonlar'], 'hat': hat,
                    'pozisyon_adi': pozisyon_adi, 'grup_adet': grup_adet, 'islem_sayisi': islem_sayisi,
                    'recete_sure': ort_recete_sure, 'beklenen_dk': beklenen, 'kapasite_dk': grup_kapasitesi,
                    'aktif_sure': aktif_sure, 'bos_dk': bos_dk, 'bos_yuzde': bos_yuzde,
                    'verimlilik': verimlilik, 'darbogaz_skoru': darbogaz_skoru
                })
            
            darbogaz_data.sort(key=lambda x: x['darbogaz_skoru'], reverse=True)
            
            if darbogaz_data:
                en_kritik = darbogaz_data[0]
                self.card_darbogaz.findChild(QLabel, "val").setText(en_kritik['pozisyon_adi'][:12])
                
                toplam_kayip = sum(d['bos_dk'] for d in darbogaz_data)
                self.card_kayip_sure.findChild(QLabel, "val").setText(f"{toplam_kayip:.0f} dk")
                
                ort_verimlilik = sum(d['verimlilik'] for d in darbogaz_data) / len(darbogaz_data)
                self.card_verimlilik.findChild(QLabel, "val").setText(f"%{ort_verimlilik:.1f}")
                
                if en_kritik['verimlilik'] < 30:
                    oncelik = "KRİTİK"
                elif en_kritik['verimlilik'] < 50:
                    oncelik = "YÜKSEK"
                elif en_kritik['verimlilik'] < 70:
                    oncelik = "ORTA"
                else:
                    oncelik = "DÜŞÜK"
                self.card_oneri.findChild(QLabel, "val").setText(oncelik)
                
                oneri_metin = f"⚠️ En kritik: {en_kritik['pozisyon_adi']} ({en_kritik['grup_adet']} banyo) - "
                oneri_metin += f"Kapasite {en_kritik['kapasite_dk']:.0f} dk, Kullanılan {en_kritik['beklenen_dk']:.0f} dk, "
                oneri_metin += f"Verimlilik %{en_kritik['verimlilik']:.1f}"
                self.lbl_darbogaz_oneri.setText(oneri_metin)
            
            self.tbl_darbogaz.setColumnCount(11)
            self.tbl_darbogaz.setHorizontalHeaderLabels([
                "Sıra", "Pozisyonlar", "Hat", "Banyo Adı", "Adet", "İşlem",
                "Reçete (dk)", "Kapasite (dk)", "Kullanılan (dk)", "Verimlilik %", "Durum"
            ])
            
            self.tbl_darbogaz.setRowCount(len(darbogaz_data))
            
            for i, data in enumerate(darbogaz_data):
                sira_item = QTableWidgetItem(str(i + 1))
                if i < 3:
                    sira_item.setForeground(QBrush(QColor(self.error)))
                    sira_item.setFont(QFont("", -1, QFont.Bold))
                self.tbl_darbogaz.setItem(i, 0, sira_item)
                
                poz_str = ','.join(str(p) for p in data['pozisyonlar'][:3])
                if len(data['pozisyonlar']) > 3:
                    poz_str += '...'
                self.tbl_darbogaz.setItem(i, 1, QTableWidgetItem(poz_str))
                self.tbl_darbogaz.setItem(i, 2, QTableWidgetItem(data['hat']))
                self.tbl_darbogaz.setItem(i, 3, QTableWidgetItem(data['pozisyon_adi']))
                self.tbl_darbogaz.setItem(i, 4, QTableWidgetItem(str(data['grup_adet'])))
                self.tbl_darbogaz.setItem(i, 5, QTableWidgetItem(f"{data['islem_sayisi']:,}"))
                self.tbl_darbogaz.setItem(i, 6, QTableWidgetItem(f"{data['recete_sure']:.1f}"))
                self.tbl_darbogaz.setItem(i, 7, QTableWidgetItem(f"{data['kapasite_dk']:.0f}"))
                self.tbl_darbogaz.setItem(i, 8, QTableWidgetItem(f"{data['beklenen_dk']:.0f}"))
                
                verim_item = QTableWidgetItem(f"%{data['verimlilik']:.1f}")
                if data['verimlilik'] >= 70:
                    verim_item.setForeground(QBrush(QColor(self.success)))
                elif data['verimlilik'] >= 50:
                    verim_item.setForeground(QBrush(QColor(self.warning)))
                else:
                    verim_item.setForeground(QBrush(QColor(self.error)))
                    verim_item.setFont(QFont("", -1, QFont.Bold))
                self.tbl_darbogaz.setItem(i, 9, verim_item)
                
                if data['verimlilik'] >= 70:
                    durum, durum_color = "🟢 Verimli", self.success
                elif data['verimlilik'] >= 50:
                    durum, durum_color = "🟡 Orta", self.warning
                else:
                    durum, durum_color = "🔴 Düşük", self.error
                durum_item = QTableWidgetItem(durum)
                durum_item.setForeground(QBrush(QColor(durum_color)))
                self.tbl_darbogaz.setItem(i, 10, durum_item)
                
        except Exception as e:
            print(f"Darboğaz analizi hatası: {e}")
            QMessageBox.warning(self, "Hata", f"Analiz hatası: {e}")
    
    def closeEvent(self, event):
        """Sayfa kapatılırken"""
        self.refresh_timer.stop()
        super().closeEvent(event)
