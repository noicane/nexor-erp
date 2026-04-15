# -*- coding: utf-8 -*-
"""
NEXOR ERP - Verimlilik Analizi Modulu (Brand System)
=====================================================
4 Tab: Hat Verimliligi, Cevrim Suresi Sapmasi, Darbogaz Tespiti, Bara Bazli Analiz.
Ortak kazan destekli analiz motoru. Tum stiller core.nexor_brand uzerinden.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QPushButton, QFrame, QTabWidget, QHeaderView,
    QMessageBox, QSplitter, QDateEdit,
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QFont, QColor, QBrush, QPainter, QPen
from datetime import datetime, timedelta
from core.database import get_db_connection, get_plc_connection
from core.nexor_brand import brand
from .verimlilik_helpers import (
    BANYO_GRUPLARI_SEED, get_hat_from_tank,
    build_combined_groups, build_tank_to_group_map
)


# =============================================================================
# BRAND ICON
# =============================================================================

class BrandIcon(QLabel):
    def __init__(self, kind: str, color: str = None, size: int = None, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.color = color or brand.TEXT
        self.size_px = size or brand.ICON_MD
        self.setFixedSize(self.size_px, self.size_px)
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(self.color))
        pen.setWidthF(max(1.4, self.size_px / 12))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        s = self.size_px
        m = s * 0.18
        k = self.kind

        if k == "chart":
            p.drawLine(int(m), int(s - m), int(s - m), int(s - m))
            p.drawLine(int(m), int(s - m), int(m), int(m))
            p.drawLine(int(m * 1.8), int(s * 0.7), int(m * 1.8), int(s - m))
            p.drawLine(int(s * 0.42), int(s * 0.55), int(s * 0.42), int(s - m))
            p.drawLine(int(s * 0.62), int(s * 0.4), int(s * 0.62), int(s - m))
            p.drawLine(int(s * 0.82), int(s * 0.25), int(s * 0.82), int(s - m))
        elif k == "trending-up":
            p.drawLine(int(m), int(s - m * 1.5), int(s * 0.42), int(s * 0.6))
            p.drawLine(int(s * 0.42), int(s * 0.6), int(s * 0.62), int(s * 0.75))
            p.drawLine(int(s * 0.62), int(s * 0.75), int(s - m), int(m * 1.5))
            p.drawLine(int(s - m), int(m * 1.5), int(s * 0.7), int(m * 1.5))
            p.drawLine(int(s - m), int(m * 1.5), int(s - m), int(s * 0.42))
        elif k == "factory":
            p.drawLine(int(m), int(s - m), int(m), int(s * 0.45))
            p.drawLine(int(m), int(s * 0.45), int(s * 0.45), int(s * 0.6))
            p.drawLine(int(s * 0.45), int(s * 0.6), int(s * 0.45), int(s * 0.3))
            p.drawLine(int(s * 0.45), int(s * 0.3), int(s - m), int(s * 0.45))
            p.drawLine(int(s - m), int(s * 0.45), int(s - m), int(s - m))
            p.drawLine(int(m), int(s - m), int(s - m), int(s - m))
        elif k == "alert":
            p.drawLine(int(s * 0.5), int(m), int(s - m), int(s - m))
            p.drawLine(int(s - m), int(s - m), int(m), int(s - m))
            p.drawLine(int(m), int(s - m), int(s * 0.5), int(m))
            p.drawLine(int(s * 0.5), int(s * 0.38), int(s * 0.5), int(s * 0.62))
        elif k == "refresh":
            from PySide6.QtCore import QRectF
            rect = QRectF(m, m, s - 2 * m, s - 2 * m)
            p.drawArc(rect, 45 * 16, 270 * 16)
            p.drawLine(int(s - m * 1.2), int(m), int(s - m * 1.2), int(m * 2.2))
            p.drawLine(int(s - m * 1.2), int(m * 2.2), int(s - m * 2.4), int(m * 2.2))
        elif k == "search":
            p.drawEllipse(int(m), int(m), int(s * 0.55), int(s * 0.55))
            p.drawLine(int(s * 0.6), int(s * 0.6), int(s - m), int(s - m))
        p.end()


def _soft(color_hex: str, alpha: float = 0.12) -> str:
    c = QColor(color_hex)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


class VerimlilikAnalizPage(QWidget):
    """Verimlilik Analizi Sayfasi - 4 Tab"""

    def __init__(self, page_id=None, theme: dict = None):
        super().__init__()
        self.page_id = page_id
        self.plc_conn = None
        self.erp_conn = None
        self.pozisyon_tanimlari = {}
        self.bara_data = []

        # Brand alias'lari — mevcut _load_* metotlari self.error/self.success vb.
        # ile QColor uretiyor; brand degerlerine atanir, lokal renk referansi bozulmaz.
        self.bg         = brand.BG_MAIN
        self.bg_card    = brand.BG_CARD
        self.bg_input   = brand.BG_INPUT
        self.primary    = brand.PRIMARY
        self.success    = brand.SUCCESS
        self.warning    = brand.WARNING
        self.error      = brand.ERROR
        self.info       = brand.INFO
        self.text       = brand.TEXT
        self.text_muted = brand.TEXT_MUTED
        self.border     = brand.BORDER

        # Ortak kazan gruplari (ilk yuklemede guncellenir)
        self.ortak_gruplar = {}
        self.tank_grup_map = {}

        self._init_ui()
        self._load_pozisyon_tanimlari()

    def _ensure_plc(self):
        """PLC bağlantısını sağla"""
        if self.plc_conn:
            return True
        try:
            self.plc_conn = get_plc_connection()
            # Ortak kazan gruplarını oluştur
            self.ortak_gruplar = build_combined_groups(self.plc_conn, days=7)
            self.tank_grup_map = build_tank_to_group_map(self.ortak_gruplar)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"PLC bağlantısı kurulamadı: {e}")
            return False

    def _init_ui(self):
        """Arayuzu olustur"""
        self.setStyleSheet(f"""
            QWidget {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT};
                font-family: {brand.FONT_FAMILY};
                font-size: {brand.FS_BODY}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # Baslik
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)

        icon_box = QFrame()
        icon_box.setFixedSize(brand.sp(40), brand.sp(40))
        icon_box.setStyleSheet(
            f"background: {_soft(brand.PRIMARY, 0.12)}; "
            f"border: 1px solid {_soft(brand.PRIMARY, 0.35)}; "
            f"border-radius: {brand.R_SM}px;"
        )
        ib = QVBoxLayout(icon_box)
        ib.setContentsMargins(0, 0, 0, 0)
        ib.addWidget(BrandIcon("chart", brand.PRIMARY, brand.sp(20)), 0, Qt.AlignCenter)
        header.addWidget(icon_box)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        title = QLabel("Verimlilik Analizi")
        title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_TITLE}px; "
            f"font-weight: {brand.FW_BOLD}; letter-spacing: -0.4px;"
        )
        title_col.addWidget(title)

        subtitle = QLabel("Hat verimliligi, cevrim sapmasi, darbogaz ve bara bazli analiz")
        subtitle.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px;"
        )
        title_col.addWidget(subtitle)
        header.addLayout(title_col)

        header.addStretch()

        btn_refresh = QPushButton("Yenile")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: 1px solid {brand.PRIMARY};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_5}px;
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QPushButton:hover {{
                background: {brand.PRIMARY_HOVER};
                border-color: {brand.PRIMARY_HOVER};
            }}
        """)
        btn_refresh.clicked.connect(self._refresh_all)
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                background: {brand.BG_CARD};
                top: -1px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_6}px;
                margin-right: {brand.SP_1}px;
                border: 1px solid transparent;
                border-top-left-radius: {brand.R_SM}px;
                border-top-right-radius: {brand.R_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QTabBar::tab:selected {{
                background: {brand.BG_CARD};
                color: {brand.PRIMARY};
                border: 1px solid {brand.BORDER};
                border-bottom: 2px solid {brand.PRIMARY};
            }}
            QTabBar::tab:hover:!selected {{
                color: {brand.TEXT};
                background: {brand.BG_HOVER};
            }}
        """)

        self._create_hat_verimlilik_tab()
        self._create_cevrim_sapma_tab()
        self._create_darbogaz_tab()
        self._create_bara_analiz_tab()

        layout.addWidget(self.tabs)

    # ─── Tab 1: Hat Verimliliği (Kazan Kullanım) ───

    def _create_hat_verimlilik_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_4)

        # Filtreler
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(brand.SP_3)
        filter_layout.addWidget(self._mini_label("Donem"))
        self.cmb_hat_tarih = QComboBox()
        self.cmb_hat_tarih.setStyleSheet(self._combo_style())
        self.cmb_hat_tarih.addItem("Bugun (Vardiya)", "bugun")
        self.cmb_hat_tarih.addItem("Dun", "dun")
        self.cmb_hat_tarih.addItem("Son 7 Gun", "hafta")
        self.cmb_hat_tarih.addItem("Tarih Araligi", "aralik")
        filter_layout.addWidget(self.cmb_hat_tarih)

        self.date_hat_bas, self.date_hat_bit = self._create_date_range_widgets(filter_layout, self.cmb_hat_tarih)

        filter_layout.addWidget(self._mini_label("Hat"))
        self.cmb_hat_filtre = QComboBox()
        self.cmb_hat_filtre.setStyleSheet(self._combo_style())
        self.cmb_hat_filtre.addItem("Tum Hatlar", None)
        self.cmb_hat_filtre.addItem("KTL", "KTL")
        self.cmb_hat_filtre.addItem("CINKO", "CINKO")
        self.cmb_hat_filtre.addItem("ORTAK", "ORTAK")
        filter_layout.addWidget(self.cmb_hat_filtre)

        btn = QPushButton("Hesapla")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._cta_button_style(brand.SUCCESS))
        btn.clicked.connect(self._load_hat_verimlilik)
        filter_layout.addWidget(btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Kartlar
        cards = QHBoxLayout()
        cards.setSpacing(brand.SP_3)
        self.card_hat_kapasite = self._create_card("TOPLAM KAPASITE", "0 dk", brand.PRIMARY)
        self.card_hat_kullanim = self._create_card("KULLANIM ORANI", "%0",   brand.SUCCESS)
        self.card_hat_yogun    = self._create_card("EN YOGUN GRUP", "—",     brand.WARNING)
        self.card_hat_bos      = self._create_card("EN BOS GRUP",   "—",     brand.ERROR)
        cards.addWidget(self.card_hat_kapasite)
        cards.addWidget(self.card_hat_kullanim)
        cards.addWidget(self.card_hat_yogun)
        cards.addWidget(self.card_hat_bos)
        layout.addLayout(cards)

        # Splitter - ust: grup tablo, alt: kazan doluluk detay
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(brand.sp(4))
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {brand.BORDER}; }}
            QSplitter::handle:hover {{ background: {brand.BORDER_HARD}; }}
        """)

        # Ust: Grup tablosu
        grup_widget = self._section_wrapper("GRUP / KAZAN KULLANIM")
        self.tbl_hat_verimlilik = QTableWidget()
        self.tbl_hat_verimlilik.setColumnCount(8)
        self.tbl_hat_verimlilik.setHorizontalHeaderLabels([
            "GRUP/KAZAN", "HAT", "KAZAN ADET", "ISLEM SAYISI",
            "DOLU (DK)", "BOS (DK)", "KULLANIM %", "DURUM"
        ])
        self._style_table(self.tbl_hat_verimlilik)
        self.tbl_hat_verimlilik.itemSelectionChanged.connect(self._on_kazan_grup_selected)
        grup_widget.layout().addWidget(self.tbl_hat_verimlilik)
        splitter.addWidget(grup_widget)

        # Alt: Kazan doluluk detay
        detay_widget = self._section_wrapper("KAZAN DOLULUK DETAYI")
        self.tbl_kazan_doluluk = QTableWidget()
        self.tbl_kazan_doluluk.setColumnCount(8)
        self.tbl_kazan_doluluk.setHorizontalHeaderLabels([
            "KAZAN", "POZISYON ADI", "BARA NO", "RECETE",
            "DOLDURMA", "BOSALTMA", "KALIS (DK)", "DURUM"
        ])
        self._style_table(self.tbl_kazan_doluluk)
        detay_widget.layout().addWidget(self.tbl_kazan_doluluk)
        splitter.addWidget(detay_widget)

        splitter.setSizes([brand.sp(320), brand.sp(220)])
        layout.addWidget(splitter)

        self.tabs.addTab(tab, "Hat Verimliligi")

    # ─── Tab 2: Çevrim Süresi Sapması ───

    def _create_cevrim_sapma_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_4)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(brand.SP_3)
        filter_layout.addWidget(self._mini_label("Donem"))
        self.cmb_sapma_tarih = QComboBox()
        self.cmb_sapma_tarih.setStyleSheet(self._combo_style())
        self.cmb_sapma_tarih.addItem("Bugun (Vardiya)", "bugun")
        self.cmb_sapma_tarih.addItem("Dun", "dun")
        self.cmb_sapma_tarih.addItem("Son 7 Gun", "hafta")
        self.cmb_sapma_tarih.addItem("Tarih Araligi", "aralik")
        filter_layout.addWidget(self.cmb_sapma_tarih)

        self.date_sapma_bas, self.date_sapma_bit = self._create_date_range_widgets(filter_layout, self.cmb_sapma_tarih)

        filter_layout.addWidget(self._mini_label("Sapma Tipi"))
        self.cmb_sapma_tipi = QComboBox()
        self.cmb_sapma_tipi.setStyleSheet(self._combo_style())
        self.cmb_sapma_tipi.addItem("Tumu", None)
        self.cmb_sapma_tipi.addItem("Sadece Gecikmeler (+)", "pozitif")
        self.cmb_sapma_tipi.addItem("Sadece Hizlilar (-)", "negatif")
        filter_layout.addWidget(self.cmb_sapma_tipi)

        btn = QPushButton("Analiz Et")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._cta_button_style(brand.SUCCESS))
        btn.clicked.connect(self._load_cevrim_sapma)
        filter_layout.addWidget(btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Kartlar
        cards = QHBoxLayout()
        cards.setSpacing(brand.SP_3)
        self.card_sapma_toplam  = self._create_card("TOPLAM SAPMA",      "0 dk", brand.WARNING)
        self.card_sapma_ort     = self._create_card("ORT. SAPMA",        "0 sn", brand.PRIMARY)
        self.card_sapma_geciken = self._create_card("EN GECIKEN ADIM",   "—",    brand.ERROR)
        self.card_sapma_hizli   = self._create_card("EN HIZLI ADIM",     "—",    brand.SUCCESS)
        cards.addWidget(self.card_sapma_toplam)
        cards.addWidget(self.card_sapma_ort)
        cards.addWidget(self.card_sapma_geciken)
        cards.addWidget(self.card_sapma_hizli)
        layout.addLayout(cards)

        # Tablo
        self.tbl_cevrim_sapma = QTableWidget()
        self.tbl_cevrim_sapma.setColumnCount(9)
        self.tbl_cevrim_sapma.setHorizontalHeaderLabels([
            "RECETE", "ADIM", "KAZAN(LAR)", "ISLEM ADI",
            "RECETE SURE (SN)", "GERCEK SURE (SN)", "SAPMA (SN)", "SAPMA %", "DURUM"
        ])
        self._style_table(self.tbl_cevrim_sapma)
        layout.addWidget(self.tbl_cevrim_sapma)

        self.tabs.addTab(tab, "Cevrim Sapmasi")

    # ─── Tab 3: Darboğaz Tespiti ───

    def _create_darbogaz_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_4)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(brand.SP_3)
        filter_layout.addWidget(self._mini_label("Donem"))
        self.cmb_darbogaz_tarih = QComboBox()
        self.cmb_darbogaz_tarih.setStyleSheet(self._combo_style())
        self.cmb_darbogaz_tarih.addItem("Bugun (Vardiya)", "bugun")
        self.cmb_darbogaz_tarih.addItem("Dun", "dun")
        self.cmb_darbogaz_tarih.addItem("Son 7 Gun", "hafta")
        self.cmb_darbogaz_tarih.addItem("Tarih Araligi", "aralik")
        filter_layout.addWidget(self.cmb_darbogaz_tarih)

        self.date_darbogaz_bas, self.date_darbogaz_bit = self._create_date_range_widgets(filter_layout, self.cmb_darbogaz_tarih)

        btn = QPushButton("Tespit Et")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._cta_button_style(brand.SUCCESS))
        btn.clicked.connect(self._load_darbogaz)
        filter_layout.addWidget(btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Kartlar
        cards = QHBoxLayout()
        cards.setSpacing(brand.SP_3)
        self.card_db_sayi    = self._create_card("DARBOGAZ SAYISI", "0",    brand.ERROR)
        self.card_db_bekleme = self._create_card("TOPLAM BEKLEME",  "0 dk", brand.WARNING)
        self.card_db_kritik  = self._create_card("EN KRITIK GRUP",  "—",    brand.ERROR)
        self.card_db_kuyruk  = self._create_card("ORT. KUYRUK",     "0",    brand.PRIMARY)
        cards.addWidget(self.card_db_sayi)
        cards.addWidget(self.card_db_bekleme)
        cards.addWidget(self.card_db_kritik)
        cards.addWidget(self.card_db_kuyruk)
        layout.addLayout(cards)

        # Tablo
        self.tbl_darbogaz = QTableWidget()
        self.tbl_darbogaz.setColumnCount(9)
        self.tbl_darbogaz.setHorizontalHeaderLabels([
            "GRUP", "KAZANLAR", "HAT", "ISLEM ADI",
            "ORT. BOS ARALIK (SN)", "KULLANIM %", "KUYRUK OLAYI", "BEKLEME (DK)", "SIDDET"
        ])
        self._style_table(self.tbl_darbogaz)
        layout.addWidget(self.tbl_darbogaz)

        self.tabs.addTab(tab, "Darbogaz Tespiti")

    # ─── Tab 4: Bara Bazlı Analiz ───

    def _create_bara_analiz_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_4)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(brand.SP_3)
        filter_layout.addWidget(self._mini_label("Donem"))
        self.cmb_bara_tarih = QComboBox()
        self.cmb_bara_tarih.setStyleSheet(self._combo_style())
        self.cmb_bara_tarih.addItem("Bugun (Vardiya)", "bugun")
        self.cmb_bara_tarih.addItem("Dun", "dun")
        self.cmb_bara_tarih.addItem("Son 2 Saat", "2saat")
        self.cmb_bara_tarih.addItem("Tarih Araligi", "aralik")
        filter_layout.addWidget(self.cmb_bara_tarih)

        self.date_bara_bas, self.date_bara_bit = self._create_date_range_widgets(filter_layout, self.cmb_bara_tarih)

        filter_layout.addWidget(self._mini_label("Hat"))
        self.cmb_bara_hat = QComboBox()
        self.cmb_bara_hat.setStyleSheet(self._combo_style())
        self.cmb_bara_hat.addItem("KTL (118 → 101)", "KTL")
        self.cmb_bara_hat.addItem("CINKO (236 → 201)", "CINKO")
        filter_layout.addWidget(self.cmb_bara_hat)

        btn = QPushButton("Ara")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._cta_button_style(brand.SUCCESS))
        btn.clicked.connect(self._load_bara_analiz)
        filter_layout.addWidget(btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Splitter - ust bara listesi, alt detay
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(brand.sp(4))
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {brand.BORDER}; }}
            QSplitter::handle:hover {{ background: {brand.BORDER_HARD}; }}
        """)

        # Ust: Bara listesi
        bara_widget = self._section_wrapper("BARA LISTESI")
        self.tbl_bara_listesi = QTableWidget()
        self.tbl_bara_listesi.setColumnCount(9)
        self.tbl_bara_listesi.setHorizontalHeaderLabels([
            "BARA NO", "RECETE", "CEVRIM #", "GIRIS SAATI", "CIKIS SAATI",
            "TOPLAM (DK)", "RECETE (DK)", "SAPMA (DK)", "BEKLEME (DK)"
        ])
        self._style_table(self.tbl_bara_listesi)
        self.tbl_bara_listesi.itemSelectionChanged.connect(self._on_bara_selected)
        bara_widget.layout().addWidget(self.tbl_bara_listesi)
        splitter.addWidget(bara_widget)

        # Alt: Bara detay
        detay_widget = self._section_wrapper("BARA DETAY (POZISYON GECISLERI)")
        self.tbl_bara_detay = QTableWidget()
        self.tbl_bara_detay.setColumnCount(10)
        self.tbl_bara_detay.setHorizontalHeaderLabels([
            "SIRA", "ADIM", "KAZAN", "POZISYON ADI", "GIRIS",
            "CIKIS", "KALIS (SN)", "RECETE (SN)", "SAPMA", "ORTAK?"
        ])
        self._style_table(self.tbl_bara_detay)
        detay_widget.layout().addWidget(self.tbl_bara_detay)
        splitter.addWidget(detay_widget)

        splitter.setSizes([brand.sp(320), brand.sp(220)])
        layout.addWidget(splitter)

        self.tabs.addTab(tab, "Bara Analiz")

    # ─── Ortak Yardımcılar ───

    def _mini_label(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; letter-spacing: 0.6px; "
            f"background: transparent;"
        )
        return lbl

    def _section_wrapper(self, title: str) -> QWidget:
        """Tablo bolumu icin baslik + container."""
        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(brand.SP_2)

        t = QLabel(title)
        t.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_CAPTION}px; padding: {brand.SP_1}px 0; "
            f"letter-spacing: 0.8px;"
        )
        wl.addWidget(t)
        return wrapper

    def _cta_button_style(self, accent: str) -> str:
        hover = "#059669" if accent == brand.SUCCESS else brand.PRIMARY_HOVER
        return f"""
            QPushButton {{
                background: {accent};
                color: white;
                border: 1px solid {accent};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_5}px;
                font-weight: {brand.FW_BOLD};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QPushButton:hover {{
                background: {hover};
                border-color: {hover};
            }}
        """

    def _create_card(self, title, value, color):
        card = QFrame()
        card.setFixedHeight(brand.sp(88))
        card.setMinimumWidth(brand.sp(200))
        card.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-left: 3px solid {color};
                border-radius: {brand.R_MD}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)
        layout.setSpacing(brand.SP_1)

        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; letter-spacing: 0.6px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(lbl_title)

        lbl_value = QLabel(value)
        lbl_value.setObjectName("val")
        lbl_value.setStyleSheet(
            f"color: {color}; font-size: {brand.FS_HEADING_LG}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(lbl_value)

        return card

    def _combo_style(self):
        return f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                min-width: {brand.sp(150)}px;
                font-size: {brand.FS_BODY_SM}px;
            }}
            QComboBox:hover {{ border-color: {brand.BORDER_HARD}; }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
            QComboBox::drop-down {{ border: none; width: {brand.sp(24)}px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_ELEVATED};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                selection-background-color: {brand.PRIMARY};
                selection-color: white;
            }}
        """

    def _date_edit_style(self):
        return f"""
            QDateEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                min-width: {brand.sp(130)}px;
                font-size: {brand.FS_BODY_SM}px;
            }}
            QDateEdit:hover {{ border-color: {brand.BORDER_HARD}; }}
            QDateEdit:focus {{ border-color: {brand.PRIMARY}; }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding; subcontrol-position: top right;
                width: {brand.sp(22)}px;
                border-left: 1px solid {brand.BORDER};
            }}
        """

    def _create_date_range_widgets(self, layout, combo):
        """Tarih araligi secici widget'lari olustur ve layout'a ekle"""
        lbl_bas = self._mini_label("Baslangic")
        date_bas = QDateEdit()
        date_bas.setCalendarPopup(True)
        date_bas.setDate(QDate.currentDate().addDays(-7))
        date_bas.setDisplayFormat("dd.MM.yyyy")
        date_bas.setStyleSheet(self._date_edit_style())

        lbl_bit = self._mini_label("Bitis")
        date_bit = QDateEdit()
        date_bit.setCalendarPopup(True)
        date_bit.setDate(QDate.currentDate())
        date_bit.setDisplayFormat("dd.MM.yyyy")
        date_bit.setStyleSheet(self._date_edit_style())

        lbl_bas.setVisible(False)
        date_bas.setVisible(False)
        lbl_bit.setVisible(False)
        date_bit.setVisible(False)

        layout.addWidget(lbl_bas)
        layout.addWidget(date_bas)
        layout.addWidget(lbl_bit)
        layout.addWidget(date_bit)

        def on_combo_changed():
            is_aralik = combo.currentData() == "aralik"
            lbl_bas.setVisible(is_aralik)
            date_bas.setVisible(is_aralik)
            lbl_bit.setVisible(is_aralik)
            date_bit.setVisible(is_aralik)

        combo.currentIndexChanged.connect(on_combo_changed)

        return date_bas, date_bit

    def _style_table(self, table):
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_MD}px;
                gridline-color: transparent;
                font-size: {brand.FS_BODY_SM}px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_2}px {brand.SP_3}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
            }}
            QTableWidget::item:selected {{
                background: {_soft(brand.PRIMARY, 0.18)};
                color: {brand.TEXT};
            }}
            QTableWidget::item:hover {{
                background: {brand.BG_HOVER};
            }}
            QHeaderView::section {{
                background: {brand.BG_CARD};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_2}px {brand.SP_3}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_CAPTION}px;
                letter-spacing: 0.5px;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: {brand.sp(8)}px;
            }}
            QScrollBar::handle:vertical {{
                background: {brand.BORDER_HARD};
                border-radius: {brand.sp(4)}px;
                min-height: {brand.sp(30)}px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        table.setShowGrid(False)
        table.setFrameShape(QFrame.NoFrame)
        table.setAlternatingRowColors(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setHighlightSections(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setDefaultSectionSize(brand.sp(38))

    def _load_pozisyon_tanimlari(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    p.pozisyon_no,
                    p.ad,
                    h.kod as hat_kodu,
                    h.ad as hat_adi
                FROM tanim.hat_pozisyonlar p
                JOIN tanim.uretim_hatlari h ON p.hat_id = h.id
                WHERE p.aktif_mi = 1 AND p.silindi_mi = 0 AND h.aktif_mi = 1 AND h.silindi_mi = 0
            """)
            for row in cursor.fetchall():
                self.pozisyon_tanimlari[row[0]] = {
                    'pozisyon_adi': row[1],
                    'hat_kodu': row[2],
                    'hat_adi': row[3]
                }
            conn.close()
        except Exception as e:
            print(f"Pozisyon tanımları yüklenemedi: {e}")

    def _get_tarih_aralik(self, tarih_secim, date_bas=None, date_bit=None):
        now = datetime.now()

        if tarih_secim == "aralik" and date_bas and date_bit:
            baslangic = datetime(date_bas.date().year(), date_bas.date().month(), date_bas.date().day(), 0, 0, 0)
            bitis = datetime(date_bit.date().year(), date_bit.date().month(), date_bit.date().day(), 23, 59, 59)
        elif tarih_secim == "bugun":
            if now.hour < 7 or (now.hour == 7 and now.minute < 30):
                baslangic = now.replace(hour=7, minute=30, second=0, microsecond=0) - timedelta(days=1)
            else:
                baslangic = now.replace(hour=7, minute=30, second=0, microsecond=0)
            bitis = now
        elif tarih_secim == "dun":
            dun = now - timedelta(days=1)
            baslangic = dun.replace(hour=7, minute=30, second=0, microsecond=0)
            bitis = baslangic + timedelta(days=1)
        elif tarih_secim == "2saat":
            baslangic = now - timedelta(hours=2)
            bitis = now
        else:  # hafta
            baslangic = now - timedelta(days=7)
            bitis = now

        return baslangic, bitis

    def _get_poz_adi(self, kzn_no):
        tanim = self.pozisyon_tanimlari.get(kzn_no, {})
        return tanim.get('pozisyon_adi', f'K{kzn_no}')

    def _refresh_all(self):
        current_tab = self.tabs.currentIndex()
        if current_tab == 0:
            self._load_hat_verimlilik()
        elif current_tab == 1:
            self._load_cevrim_sapma()
        elif current_tab == 2:
            self._load_darbogaz()
        elif current_tab == 3:
            self._load_bara_analiz()

    # ─── Tab 1: Hat Verimliliği - Veri Yükleme ───

    def _load_hat_verimlilik(self):
        if not self._ensure_plc():
            return

        tarih_secim = self.cmb_hat_tarih.currentData()
        hat_secim = self.cmb_hat_filtre.currentData()
        baslangic, bitis = self._get_tarih_aralik(tarih_secim, self.date_hat_bas, self.date_hat_bit)
        periyot_dk = (bitis - baslangic).total_seconds() / 60

        try:
            cursor = self.plc_conn.cursor()

            # Her kazan için dolu/boş süre hesabı
            cursor.execute("""
                SELECT
                    KznNo,
                    COUNT(*) as islem_sayisi,
                    SUM(DATEDIFF(SECOND, TarihDoldurma, ISNULL(TarihBosaltma, GETDATE()))) / 60.0 as dolu_dk
                FROM dbo.data
                WHERE TarihDoldurma >= ? AND TarihDoldurma <= ?
                  AND TarihDoldurma IS NOT NULL
                GROUP BY KznNo
            """, (baslangic, bitis))
            rows = cursor.fetchall()

            # Grup bazlı toplama
            grup_data = {}

            for row in rows:
                kzn_no, islem_sayisi, dolu_dk = row
                dolu_dk = float(dolu_dk) if dolu_dk else 0

                # Grup belirleme
                grup_adi = self.tank_grup_map.get(kzn_no)
                if grup_adi:
                    grup_info = self.ortak_gruplar[grup_adi]
                    hat = grup_info['hat']
                else:
                    hat = get_hat_from_tank(kzn_no)
                    grup_adi = self._get_poz_adi(kzn_no)

                # Hat filtresi
                if hat_secim and hat != hat_secim:
                    continue

                if grup_adi not in grup_data:
                    grup_data[grup_adi] = {
                        'kazanlar': set(),
                        'hat': hat,
                        'toplam_islem': 0,
                        'toplam_dolu_dk': 0,
                    }

                grup_data[grup_adi]['kazanlar'].add(kzn_no)
                grup_data[grup_adi]['toplam_islem'] += islem_sayisi
                grup_data[grup_adi]['toplam_dolu_dk'] += dolu_dk

            # Verimlilik hesapla
            result = []
            toplam_kapasite = 0
            toplam_kullanim = 0
            max_kullanim = ('', 0)
            min_kullanim = ('', 100)

            for grup_adi, data in grup_data.items():
                kazan_adet = len(data['kazanlar'])
                musait_dk = kazan_adet * periyot_dk
                dolu_dk = data['toplam_dolu_dk']
                bos_dk = max(0, musait_dk - dolu_dk)
                kullanim_pct = (dolu_dk / musait_dk * 100) if musait_dk > 0 else 0

                toplam_kapasite += musait_dk
                toplam_kullanim += dolu_dk

                if kullanim_pct > max_kullanim[1]:
                    max_kullanim = (grup_adi, kullanim_pct)
                if kullanim_pct < min_kullanim[1]:
                    min_kullanim = (grup_adi, kullanim_pct)

                result.append({
                    'grup': grup_adi,
                    'hat': data['hat'],
                    'kazan_adet': kazan_adet,
                    'islem': data['toplam_islem'],
                    'dolu_dk': dolu_dk,
                    'bos_dk': bos_dk,
                    'kullanim_pct': kullanim_pct,
                    'kazanlar': sorted(data['kazanlar']),
                })

            result.sort(key=lambda x: -x['kullanim_pct'])
            self.hat_verimlilik_data = result

            # Kartları güncelle
            self.card_hat_kapasite.findChild(QLabel, "val").setText(f"{toplam_kapasite:.0f} dk")
            ort_kull = (toplam_kullanim / toplam_kapasite * 100) if toplam_kapasite > 0 else 0
            self.card_hat_kullanim.findChild(QLabel, "val").setText(f"%{ort_kull:.1f}")
            self.card_hat_yogun.findChild(QLabel, "val").setText(max_kullanim[0][:15] if max_kullanim[0] else "-")
            self.card_hat_bos.findChild(QLabel, "val").setText(min_kullanim[0][:15] if min_kullanim[0] else "-")

            # Tabloya aktar
            self.tbl_hat_verimlilik.setRowCount(len(result))
            for i, d in enumerate(result):
                self.tbl_hat_verimlilik.setItem(i, 0, QTableWidgetItem(d['grup']))
                self.tbl_hat_verimlilik.setItem(i, 1, QTableWidgetItem(d['hat']))
                self.tbl_hat_verimlilik.setItem(i, 2, QTableWidgetItem(str(d['kazan_adet'])))
                self.tbl_hat_verimlilik.setItem(i, 3, QTableWidgetItem(f"{d['islem']:,}"))
                self.tbl_hat_verimlilik.setItem(i, 4, QTableWidgetItem(f"{d['dolu_dk']:.0f}"))
                self.tbl_hat_verimlilik.setItem(i, 5, QTableWidgetItem(f"{d['bos_dk']:.0f}"))

                pct_item = QTableWidgetItem(f"%{d['kullanim_pct']:.1f}")
                if d['kullanim_pct'] > 90:
                    pct_item.setForeground(QBrush(QColor(self.error)))
                    pct_item.setFont(QFont("", -1, QFont.Bold))
                elif d['kullanim_pct'] >= 60:
                    pct_item.setForeground(QBrush(QColor(self.success)))
                elif d['kullanim_pct'] >= 30:
                    pct_item.setForeground(QBrush(QColor(self.warning)))
                else:
                    pct_item.setForeground(QBrush(QColor(self.text_muted)))
                self.tbl_hat_verimlilik.setItem(i, 6, pct_item)

                if d['kullanim_pct'] > 90:
                    durum = "YOGUN"
                elif d['kullanim_pct'] >= 60:
                    durum = "NORMAL"
                elif d['kullanim_pct'] >= 30:
                    durum = "🟡 Düşük"
                else:
                    durum = "BOS"
                self.tbl_hat_verimlilik.setItem(i, 7, QTableWidgetItem(durum))

        except Exception as e:
            print(f"Hat verimlilik hatası: {e}")
            QMessageBox.warning(self, "Hata", f"Veri yüklenirken hata: {e}")

    # ─── Tab 2: Çevrim Süresi Sapması - Veri Yükleme ───

    def _load_cevrim_sapma(self):
        """Reçete adım bazlı sapma analizi - doğru JOIN ile"""
        if not self._ensure_plc():
            return

        tarih_secim = self.cmb_sapma_tarih.currentData()
        sapma_tipi = self.cmb_sapma_tipi.currentData()
        baslangic, bitis = self._get_tarih_aralik(tarih_secim, self.date_sapma_bas, self.date_sapma_bit)

        try:
            cursor = self.plc_conn.cursor()

            # KRITIK DUZELTME: AdimNo = ReceteAdim ile JOIN
            cursor.execute("""
                WITH SiraliData AS (
                    SELECT
                        BaraNo, ReceteNo, KznNo, ReceteAdim, TarihDoldurma,
                        LEAD(TarihDoldurma) OVER (
                            PARTITION BY BaraNo, ReceteNo ORDER BY TarihDoldurma
                        ) as sonraki_doldurma
                    FROM dbo.data
                    WHERE TarihDoldurma >= ? AND TarihDoldurma <= ?
                      AND ReceteAdim > 0
                )
                SELECT
                    d.ReceteNo,
                    d.ReceteAdim,
                    d.KznNo,
                    COUNT(*) as islem_sayisi,
                    AVG(CAST(ISNULL(ra.Zamanlar, 0) + ISNULL(ra.Suzulme_Zamanlari, 0) AS FLOAT)) as ort_recete_sn,
                    AVG(CAST(DATEDIFF(SECOND, d.TarihDoldurma, d.sonraki_doldurma) AS FLOAT)) as ort_gercek_sn
                FROM SiraliData d
                LEFT JOIN ReceteAdimlar ra
                    ON ra.Panel_Recete_No = d.ReceteNo
                    AND ra.AdimNo = d.ReceteAdim
                WHERE d.sonraki_doldurma IS NOT NULL
                GROUP BY d.ReceteNo, d.ReceteAdim, d.KznNo
                HAVING COUNT(*) >= 3
                ORDER BY d.ReceteNo, d.ReceteAdim
            """, (baslangic, bitis))

            rows = cursor.fetchall()

            # Recete-Adım bazlı toplama (ortak kazanları birleştir)
            adim_key_data = {}

            for row in rows:
                recete_no, adim_no, kzn_no, islem, ort_recete, ort_gercek = row
                ort_recete = float(ort_recete) if ort_recete else 0
                ort_gercek = float(ort_gercek) if ort_gercek else 0
                sapma = ort_gercek - ort_recete

                if sapma_tipi == "pozitif" and sapma <= 0:
                    continue
                if sapma_tipi == "negatif" and sapma >= 0:
                    continue

                key = (recete_no, adim_no)
                if key not in adim_key_data:
                    adim_key_data[key] = {
                        'kazanlar': set(),
                        'islem': 0,
                        'recete_sn': ort_recete,
                        'toplam_gercek': 0,
                    }
                adim_key_data[key]['kazanlar'].add(kzn_no)
                adim_key_data[key]['islem'] += islem
                adim_key_data[key]['toplam_gercek'] += ort_gercek * islem

            # Sonuç hesapla
            result = []
            toplam_sapma = 0
            en_geciken = None
            en_hizli = None

            for (recete_no, adim_no), data in adim_key_data.items():
                islem = data['islem']
                if islem == 0:
                    continue
                ort_gercek = data['toplam_gercek'] / islem
                ort_recete = data['recete_sn']
                sapma = ort_gercek - ort_recete
                sapma_pct = (sapma / ort_recete * 100) if ort_recete > 0 else 0

                toplam_sapma += abs(sapma) * islem

                kazanlar = sorted(data['kazanlar'])
                kazan_str = ','.join(f'K{k}' for k in kazanlar[:4])
                if len(kazanlar) > 4:
                    kazan_str += '...'

                # İşlem adı
                islem_adi = self._get_poz_adi(kazanlar[0])

                item = {
                    'recete': recete_no,
                    'adim': adim_no,
                    'kazanlar': kazan_str,
                    'islem_adi': islem_adi,
                    'recete_sn': ort_recete,
                    'gercek_sn': ort_gercek,
                    'sapma': sapma,
                    'sapma_pct': sapma_pct
                }
                result.append(item)

                if en_geciken is None or sapma > en_geciken['sapma']:
                    en_geciken = item
                if en_hizli is None or sapma < en_hizli['sapma']:
                    en_hizli = item

            result.sort(key=lambda x: x['sapma'], reverse=True)

            # Kartlar
            self.card_sapma_toplam.findChild(QLabel, "val").setText(f"{toplam_sapma / 60:.0f} dk")
            if result:
                ort = sum(d['sapma'] for d in result) / len(result)
                self.card_sapma_ort.findChild(QLabel, "val").setText(f"{ort:+.0f} sn")
            if en_geciken:
                self.card_sapma_geciken.findChild(QLabel, "val").setText(f"R{en_geciken['recete']}A{en_geciken['adim']}")
            if en_hizli:
                self.card_sapma_hizli.findChild(QLabel, "val").setText(f"R{en_hizli['recete']}A{en_hizli['adim']}")

            # Tablo
            self.tbl_cevrim_sapma.setRowCount(len(result))
            for i, d in enumerate(result):
                self.tbl_cevrim_sapma.setItem(i, 0, QTableWidgetItem(str(d['recete'])))
                self.tbl_cevrim_sapma.setItem(i, 1, QTableWidgetItem(str(d['adim'])))
                self.tbl_cevrim_sapma.setItem(i, 2, QTableWidgetItem(d['kazanlar']))
                self.tbl_cevrim_sapma.setItem(i, 3, QTableWidgetItem(d['islem_adi']))
                self.tbl_cevrim_sapma.setItem(i, 4, QTableWidgetItem(f"{d['recete_sn']:.0f}"))
                self.tbl_cevrim_sapma.setItem(i, 5, QTableWidgetItem(f"{d['gercek_sn']:.0f}"))

                sapma_item = QTableWidgetItem(f"{d['sapma']:+.0f}")
                if d['sapma'] > 60:
                    sapma_item.setForeground(QBrush(QColor(self.error)))
                    sapma_item.setFont(QFont("", -1, QFont.Bold))
                elif d['sapma'] < -30:
                    sapma_item.setForeground(QBrush(QColor(self.success)))
                else:
                    sapma_item.setForeground(QBrush(QColor(self.warning)))
                self.tbl_cevrim_sapma.setItem(i, 6, sapma_item)

                pct_item = QTableWidgetItem(f"{d['sapma_pct']:+.1f}%")
                if d['sapma_pct'] > 50:
                    pct_item.setForeground(QBrush(QColor(self.error)))
                elif d['sapma_pct'] < -20:
                    pct_item.setForeground(QBrush(QColor(self.success)))
                self.tbl_cevrim_sapma.setItem(i, 7, pct_item)

                if d['sapma'] > 60:
                    durum = "GECIKME"
                elif d['sapma'] < -30:
                    durum = "HIZLI"
                else:
                    durum = "🟡 Normal"
                self.tbl_cevrim_sapma.setItem(i, 8, QTableWidgetItem(durum))

        except Exception as e:
            print(f"Çevrim sapma hatası: {e}")
            QMessageBox.warning(self, "Hata", f"Veri yüklenirken hata: {e}")

    # ─── Tab 3: Darboğaz Tespiti - Veri Yükleme ───

    def _load_darbogaz(self):
        """Ortak kazanlarda kuyruk/bekleme tespiti"""
        if not self._ensure_plc():
            return

        tarih_secim = self.cmb_darbogaz_tarih.currentData()
        baslangic, bitis = self._get_tarih_aralik(tarih_secim, self.date_darbogaz_bas, self.date_darbogaz_bit)
        periyot_dk = (bitis - baslangic).total_seconds() / 60

        try:
            cursor = self.plc_conn.cursor()

            result = []

            for grup_adi, grup_info in self.ortak_gruplar.items():
                tanks = grup_info['tanks']
                hat = grup_info['hat']
                if len(tanks) < 2:
                    continue

                # Her kazanın ardışık işlemleri arasındaki boş aralıkları hesapla
                placeholders = ','.join('?' for _ in tanks)
                cursor.execute(f"""
                    WITH Sirali AS (
                        SELECT
                            KznNo,
                            TarihDoldurma,
                            TarihBosaltma,
                            LAG(TarihBosaltma) OVER (PARTITION BY KznNo ORDER BY TarihDoldurma) as onceki_bosaltma
                        FROM dbo.data
                        WHERE KznNo IN ({placeholders})
                          AND TarihDoldurma >= ? AND TarihDoldurma <= ?
                          AND TarihBosaltma IS NOT NULL
                    )
                    SELECT
                        COUNT(*) as islem_sayisi,
                        SUM(DATEDIFF(SECOND, TarihDoldurma, TarihBosaltma)) / 60.0 as toplam_dolu_dk,
                        AVG(CASE
                            WHEN onceki_bosaltma IS NOT NULL
                            THEN DATEDIFF(SECOND, onceki_bosaltma, TarihDoldurma)
                            ELSE NULL
                        END) as ort_bos_aralik_sn,
                        SUM(CASE
                            WHEN onceki_bosaltma IS NOT NULL
                                AND DATEDIFF(SECOND, onceki_bosaltma, TarihDoldurma) < 30
                            THEN 1 ELSE 0
                        END) as kuyruk_olayi,
                        SUM(CASE
                            WHEN onceki_bosaltma IS NOT NULL
                                AND DATEDIFF(SECOND, onceki_bosaltma, TarihDoldurma) < 30
                            THEN DATEDIFF(SECOND, onceki_bosaltma, TarihDoldurma)
                            ELSE 0
                        END) / 60.0 as kuyruk_bekleme_dk
                    FROM Sirali
                    WHERE onceki_bosaltma IS NOT NULL
                """, (*tanks, baslangic, bitis))

                row = cursor.fetchone()
                if not row or not row[0]:
                    continue

                islem_sayisi, dolu_dk, ort_bos_sn, kuyruk_olayi, kuyruk_bekleme_dk = row
                dolu_dk = float(dolu_dk) if dolu_dk else 0
                ort_bos_sn = float(ort_bos_sn) if ort_bos_sn else 0
                kuyruk_olayi = int(kuyruk_olayi) if kuyruk_olayi else 0
                kuyruk_bekleme_dk = float(kuyruk_bekleme_dk) if kuyruk_bekleme_dk else 0

                musait_dk = len(tanks) * periyot_dk
                kullanim_pct = (dolu_dk / musait_dk * 100) if musait_dk > 0 else 0

                # Darboğaz tespiti: avg_gap < 30sn VE kullanım > 90%
                is_darbogaz = ort_bos_sn < 30 and kullanim_pct > 90
                siddet = kuyruk_olayi * ort_bos_sn if is_darbogaz else 0

                # Pozisyon adı
                islem_adi = self._get_poz_adi(tanks[0])

                kazanlar_str = ','.join(f'K{t}' for t in tanks[:5])
                if len(tanks) > 5:
                    kazanlar_str += '...'

                result.append({
                    'grup': grup_adi,
                    'kazanlar': kazanlar_str,
                    'hat': hat,
                    'islem_adi': islem_adi,
                    'ort_bos_sn': ort_bos_sn,
                    'kullanim_pct': kullanim_pct,
                    'kuyruk_olayi': kuyruk_olayi,
                    'bekleme_dk': kuyruk_bekleme_dk,
                    'siddet': siddet,
                    'is_darbogaz': is_darbogaz,
                })

            # Darboğazlar önce, sonra şiddete göre sırala
            result.sort(key=lambda x: (-int(x['is_darbogaz']), -x['siddet']))

            # Kartlar
            db_count = sum(1 for r in result if r['is_darbogaz'])
            self.card_db_sayi.findChild(QLabel, "val").setText(str(db_count))
            toplam_bekleme = sum(r['bekleme_dk'] for r in result)
            self.card_db_bekleme.findChild(QLabel, "val").setText(f"{toplam_bekleme:.0f} dk")
            if result and result[0]['is_darbogaz']:
                self.card_db_kritik.findChild(QLabel, "val").setText(result[0]['grup'][:15])
            else:
                self.card_db_kritik.findChild(QLabel, "val").setText("-")
            ort_kuyruk = sum(r['kuyruk_olayi'] for r in result) / len(result) if result else 0
            self.card_db_kuyruk.findChild(QLabel, "val").setText(f"{ort_kuyruk:.0f}")

            # Tablo
            self.tbl_darbogaz.setRowCount(len(result))
            for i, d in enumerate(result):
                self.tbl_darbogaz.setItem(i, 0, QTableWidgetItem(d['grup']))
                self.tbl_darbogaz.setItem(i, 1, QTableWidgetItem(d['kazanlar']))
                self.tbl_darbogaz.setItem(i, 2, QTableWidgetItem(d['hat']))
                self.tbl_darbogaz.setItem(i, 3, QTableWidgetItem(d['islem_adi']))
                self.tbl_darbogaz.setItem(i, 4, QTableWidgetItem(f"{d['ort_bos_sn']:.0f}"))

                kull_item = QTableWidgetItem(f"%{d['kullanim_pct']:.1f}")
                if d['kullanim_pct'] > 90:
                    kull_item.setForeground(QBrush(QColor(self.error)))
                    kull_item.setFont(QFont("", -1, QFont.Bold))
                elif d['kullanim_pct'] >= 60:
                    kull_item.setForeground(QBrush(QColor(self.success)))
                self.tbl_darbogaz.setItem(i, 5, kull_item)

                self.tbl_darbogaz.setItem(i, 6, QTableWidgetItem(str(d['kuyruk_olayi'])))
                self.tbl_darbogaz.setItem(i, 7, QTableWidgetItem(f"{d['bekleme_dk']:.1f}"))

                siddet_item = QTableWidgetItem(f"{d['siddet']:.0f}")
                if d['is_darbogaz']:
                    siddet_item.setForeground(QBrush(QColor(self.error)))
                    siddet_item.setFont(QFont("", -1, QFont.Bold))

                    # Satır arka planını vurgula
                    for col in range(9):
                        item = self.tbl_darbogaz.item(i, col)
                        if item:
                            item.setBackground(QBrush(QColor(_soft(brand.ERROR, 0.15))))
                else:
                    siddet_item.setForeground(QBrush(QColor(self.text_muted)))
                self.tbl_darbogaz.setItem(i, 8, siddet_item)

        except Exception as e:
            print(f"Darboğaz tespiti hatası: {e}")
            QMessageBox.warning(self, "Hata", f"Veri yüklenirken hata: {e}")

    # ─── Tab 4: Bara Bazlı Analiz - Veri Yükleme ───

    def _load_bara_analiz(self):
        if not self._ensure_plc():
            return

        tarih_secim = self.cmb_bara_tarih.currentData()
        hat_secim = self.cmb_bara_hat.currentData()
        baslangic, bitis = self._get_tarih_aralik(tarih_secim, self.date_bara_bas, self.date_bara_bit)

        # Giriş/çıkış pozisyonları
        if hat_secim == "KTL":
            giris_poz = 118
        else:
            giris_poz = 236

        try:
            cursor = self.plc_conn.cursor()

            # Tüm bara hareketlerini çek ve çevrimleri tespit et
            cursor.execute("""
                SELECT
                    BaraNo, ReceteNo, KznNo, ReceteAdim,
                    TarihDoldurma, TarihBosaltma
                FROM dbo.data
                WHERE TarihDoldurma >= ? AND TarihDoldurma <= ?
                ORDER BY BaraNo, TarihDoldurma
            """, (baslangic, bitis))
            all_rows = cursor.fetchall()

            # Reçete toplam süreleri
            recete_sureleri = {}
            cursor.execute("""
                SELECT Panel_Recete_No, SUM(Zamanlar + Suzulme_Zamanlari) / 60.0 as toplam_dk
                FROM ReceteAdimlar
                GROUP BY Panel_Recete_No
            """)
            for row in cursor.fetchall():
                recete_sureleri[row[0]] = float(row[1]) if row[1] else 0

            # Çevrim tespiti: giris_poz'a her geliş yeni çevrim
            bara_cevrimler = {}  # {(bara_no, cevrim_idx): [rows...]}

            current_bara = None
            current_cevrim = 0
            for row in all_rows:
                bara_no, recete_no, kzn_no = row[0], row[1], row[2]

                if bara_no != current_bara:
                    current_bara = bara_no
                    current_cevrim = 0

                if kzn_no == giris_poz:
                    current_cevrim += 1

                if current_cevrim == 0:
                    current_cevrim = 1

                key = (bara_no, recete_no, current_cevrim)
                if key not in bara_cevrimler:
                    bara_cevrimler[key] = []
                bara_cevrimler[key].append(row)

            # Bara listesi oluştur
            self.bara_data = []
            for (bara_no, recete_no, cevrim_no), rows in bara_cevrimler.items():
                if len(rows) < 2:
                    continue

                giris_zaman = rows[0][4]  # TarihDoldurma
                cikis_zaman = rows[-1][5] or rows[-1][4]  # TarihBosaltma or TarihDoldurma
                toplam_dk = (cikis_zaman - giris_zaman).total_seconds() / 60 if giris_zaman and cikis_zaman else 0
                recete_dk = recete_sureleri.get(recete_no, 0)
                sapma_dk = toplam_dk - recete_dk if recete_dk > 0 else 0

                # Bekleme: toplam - dolu sürelerin toplamı
                toplam_dolu = 0
                for r in rows:
                    if r[4] and r[5]:
                        toplam_dolu += (r[5] - r[4]).total_seconds() / 60
                bekleme_dk = max(0, toplam_dk - toplam_dolu) if toplam_dk > 0 else 0

                self.bara_data.append({
                    'bara_no': bara_no,
                    'recete_no': recete_no,
                    'cevrim': cevrim_no,
                    'giris': giris_zaman,
                    'cikis': cikis_zaman,
                    'toplam_dk': toplam_dk,
                    'recete_dk': recete_dk,
                    'sapma_dk': sapma_dk,
                    'bekleme_dk': bekleme_dk,
                    'rows': rows,
                })

            # Sıralama: son giriş zamanına göre
            self.bara_data.sort(key=lambda x: x['giris'], reverse=True)

            # Tabloya aktar
            self.tbl_bara_listesi.setRowCount(len(self.bara_data))
            for i, d in enumerate(self.bara_data):
                self.tbl_bara_listesi.setItem(i, 0, QTableWidgetItem(str(d['bara_no'])))
                self.tbl_bara_listesi.setItem(i, 1, QTableWidgetItem(str(d['recete_no'])))
                self.tbl_bara_listesi.setItem(i, 2, QTableWidgetItem(str(d['cevrim'])))
                self.tbl_bara_listesi.setItem(i, 3, QTableWidgetItem(d['giris'].strftime("%H:%M:%S") if d['giris'] else "-"))
                self.tbl_bara_listesi.setItem(i, 4, QTableWidgetItem(d['cikis'].strftime("%H:%M:%S") if d['cikis'] else "-"))
                self.tbl_bara_listesi.setItem(i, 5, QTableWidgetItem(f"{d['toplam_dk']:.0f}"))
                self.tbl_bara_listesi.setItem(i, 6, QTableWidgetItem(f"{d['recete_dk']:.0f}"))

                sapma_item = QTableWidgetItem(f"{d['sapma_dk']:+.0f}")
                if d['sapma_dk'] > 10:
                    sapma_item.setForeground(QBrush(QColor(self.error)))
                elif d['sapma_dk'] < -5:
                    sapma_item.setForeground(QBrush(QColor(self.success)))
                else:
                    sapma_item.setForeground(QBrush(QColor(self.warning)))
                self.tbl_bara_listesi.setItem(i, 7, sapma_item)

                self.tbl_bara_listesi.setItem(i, 8, QTableWidgetItem(f"{d['bekleme_dk']:.1f}"))

        except Exception as e:
            print(f"Bara analiz hatası: {e}")
            QMessageBox.warning(self, "Hata", f"Veri yüklenirken hata: {e}")

    def _on_bara_selected(self):
        """Bara seçildiğinde detayları göster"""
        selected = self.tbl_bara_listesi.selectedItems()
        if not selected:
            return

        row_idx = selected[0].row()
        if row_idx >= len(self.bara_data):
            return

        bara = self.bara_data[row_idx]
        rows = bara['rows']

        try:
            # Reçete adım sürelerini al
            cursor = self.plc_conn.cursor()
            cursor.execute("""
                SELECT AdimNo, Zamanlar, Suzulme_Zamanlari
                FROM ReceteAdimlar
                WHERE Panel_Recete_No = ?
            """, (bara['recete_no'],))

            adim_sureleri = {}
            for r in cursor.fetchall():
                adim_sureleri[r[0]] = (float(r[1] or 0) + float(r[2] or 0))

            self.tbl_bara_detay.setRowCount(len(rows))

            for i, row in enumerate(rows):
                bara_no, recete_no, kzn_no, adim_no, doldurma, bosaltma = row

                kalis_sn = (bosaltma - doldurma).total_seconds() if doldurma and bosaltma else 0
                recete_sn = adim_sureleri.get(adim_no, 0)
                sapma = kalis_sn - recete_sn if recete_sn > 0 else 0

                poz_adi = self._get_poz_adi(kzn_no)
                is_ortak = kzn_no in self.tank_grup_map

                self.tbl_bara_detay.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.tbl_bara_detay.setItem(i, 1, QTableWidgetItem(str(adim_no) if adim_no else "-"))
                self.tbl_bara_detay.setItem(i, 2, QTableWidgetItem(f"K{kzn_no}"))
                self.tbl_bara_detay.setItem(i, 3, QTableWidgetItem(poz_adi))
                self.tbl_bara_detay.setItem(i, 4, QTableWidgetItem(doldurma.strftime("%H:%M:%S") if doldurma else "-"))
                self.tbl_bara_detay.setItem(i, 5, QTableWidgetItem(bosaltma.strftime("%H:%M:%S") if bosaltma else "-"))
                self.tbl_bara_detay.setItem(i, 6, QTableWidgetItem(f"{kalis_sn:.0f}" if kalis_sn > 0 else "-"))
                self.tbl_bara_detay.setItem(i, 7, QTableWidgetItem(f"{recete_sn:.0f}" if recete_sn > 0 else "-"))

                # Sapma renklendirme
                if recete_sn > 0:
                    sapma_item = QTableWidgetItem(f"{sapma:+.0f}")
                    if sapma > 60:
                        sapma_item.setForeground(QBrush(QColor(self.error)))
                    elif sapma < -30:
                        sapma_item.setForeground(QBrush(QColor(self.success)))
                    else:
                        sapma_item.setForeground(QBrush(QColor(self.text_muted)))
                    self.tbl_bara_detay.setItem(i, 8, sapma_item)
                else:
                    self.tbl_bara_detay.setItem(i, 8, QTableWidgetItem("-"))

                # Ortak kazan işareti
                ortak_item = QTableWidgetItem("✓" if is_ortak else "")
                if is_ortak:
                    ortak_item.setForeground(QBrush(QColor(self.warning)))
                    ortak_item.setFont(QFont("", -1, QFont.Bold))
                self.tbl_bara_detay.setItem(i, 9, ortak_item)

        except Exception as e:
            print(f"Bara detay hatası: {e}")

    # ─── Tab 1: Kazan Doluluk Detay ───

    def _on_kazan_grup_selected(self):
        """Grup/kazan seçildiğinde doluluk detaylarını göster"""
        selected = self.tbl_hat_verimlilik.selectedItems()
        if not selected:
            return

        row_idx = selected[0].row()
        if not hasattr(self, 'hat_verimlilik_data') or row_idx >= len(self.hat_verimlilik_data):
            return

        data = self.hat_verimlilik_data[row_idx]
        kazanlar = data['kazanlar']

        if not kazanlar or not self.plc_conn:
            return

        tarih_secim = self.cmb_hat_tarih.currentData()
        baslangic, bitis = self._get_tarih_aralik(tarih_secim, self.date_hat_bas, self.date_hat_bit)

        try:
            cursor = self.plc_conn.cursor()
            placeholders = ','.join('?' for _ in kazanlar)
            cursor.execute(f"""
                SELECT
                    KznNo, BaraNo, ReceteNo,
                    TarihDoldurma, TarihBosaltma,
                    DATEDIFF(SECOND, TarihDoldurma, ISNULL(TarihBosaltma, GETDATE())) / 60.0 as kalis_dk
                FROM dbo.data
                WHERE KznNo IN ({placeholders})
                  AND TarihDoldurma >= ? AND TarihDoldurma <= ?
                ORDER BY TarihDoldurma DESC
            """, (*kazanlar, baslangic, bitis))

            rows = cursor.fetchall()

            self.tbl_kazan_doluluk.setRowCount(len(rows))

            for i, row in enumerate(rows):
                kzn_no, bara_no, recete_no, doldurma, bosaltma, kalis_dk = row
                kalis_dk = float(kalis_dk) if kalis_dk else 0
                poz_adi = self._get_poz_adi(kzn_no)

                self.tbl_kazan_doluluk.setItem(i, 0, QTableWidgetItem(f"K{kzn_no}"))
                self.tbl_kazan_doluluk.setItem(i, 1, QTableWidgetItem(poz_adi))
                self.tbl_kazan_doluluk.setItem(i, 2, QTableWidgetItem(str(bara_no) if bara_no else "-"))
                self.tbl_kazan_doluluk.setItem(i, 3, QTableWidgetItem(str(recete_no) if recete_no else "-"))
                self.tbl_kazan_doluluk.setItem(i, 4, QTableWidgetItem(doldurma.strftime("%H:%M:%S") if doldurma else "-"))
                self.tbl_kazan_doluluk.setItem(i, 5, QTableWidgetItem(bosaltma.strftime("%H:%M:%S") if bosaltma else "Devam"))

                kalis_item = QTableWidgetItem(f"{kalis_dk:.1f}")
                self.tbl_kazan_doluluk.setItem(i, 6, kalis_item)

                # Durum: boşaltılmamışsa hala dolu
                if bosaltma is None:
                    durum_item = QTableWidgetItem("DOLU")
                    durum_item.setForeground(QBrush(QColor(self.success)))
                else:
                    durum_item = QTableWidgetItem("BOS")
                    durum_item.setForeground(QBrush(QColor(self.text_muted)))
                self.tbl_kazan_doluluk.setItem(i, 7, durum_item)

        except Exception as e:
            print(f"Kazan doluluk detay hatası: {e}")

    def closeEvent(self, event):
        if self.plc_conn:
            try:
                self.plc_conn.close()
            except Exception:
                pass
        super().closeEvent(event)
