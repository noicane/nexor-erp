# -*- coding: utf-8 -*-
"""
NEXOR ERP - Vardiya Raporu Sayfasi (Brand System)
==================================================
Vardiya bazli uretim kayitlari + gunluk trend raporu.
Tum stiller core.nexor_brand uzerinden gelir; sabit px/hex yazilmaz.
"""
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QDateEdit,
    QWidget, QSplitter, QTabWidget,
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


# =============================================================================
# BRAND ICON - bu dosyaya ozel
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

        if k == "factory":
            p.drawLine(int(m), int(s - m), int(m), int(s * 0.45))
            p.drawLine(int(m), int(s * 0.45), int(s * 0.45), int(s * 0.6))
            p.drawLine(int(s * 0.45), int(s * 0.6), int(s * 0.45), int(s * 0.3))
            p.drawLine(int(s * 0.45), int(s * 0.3), int(s - m), int(s * 0.45))
            p.drawLine(int(s - m), int(s * 0.45), int(s - m), int(s - m))
            p.drawLine(int(m), int(s - m), int(s - m), int(s - m))
        elif k == "chart":
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
        elif k == "trending-down":
            p.drawLine(int(m), int(m * 1.5), int(s * 0.42), int(s * 0.42))
            p.drawLine(int(s * 0.42), int(s * 0.42), int(s * 0.62), int(s * 0.28))
            p.drawLine(int(s * 0.62), int(s * 0.28), int(s - m), int(s - m * 1.5))
            p.drawLine(int(s - m), int(s - m * 1.5), int(s * 0.7), int(s - m * 1.5))
            p.drawLine(int(s - m), int(s - m * 1.5), int(s - m), int(s * 0.58))
        elif k == "box":
            p.drawRect(int(m), int(m), int(s - 2 * m), int(s - 2 * m))
            p.drawLine(int(m), int(s * 0.42), int(s - m), int(s * 0.42))
        elif k == "clock":
            p.drawEllipse(int(m), int(m), int(s - 2 * m), int(s - 2 * m))
            p.drawLine(int(s * 0.5), int(s * 0.5), int(s * 0.5), int(s * 0.28))
            p.drawLine(int(s * 0.5), int(s * 0.5), int(s * 0.7), int(s * 0.5))
        elif k == "calendar":
            p.drawRect(int(m), int(m * 1.5), int(s - 2 * m), int(s - m * 2))
            p.drawLine(int(m), int(s * 0.38), int(s - m), int(s * 0.38))
            p.drawLine(int(s * 0.32), int(m * 0.6), int(s * 0.32), int(m * 1.8))
            p.drawLine(int(s * 0.68), int(m * 0.6), int(s * 0.68), int(m * 1.8))
        elif k == "file":
            p.drawRect(int(s * 0.25), int(m), int(s * 0.5), int(s - 2 * m))
            p.drawLine(int(s * 0.35), int(s * 0.35), int(s * 0.65), int(s * 0.35))
            p.drawLine(int(s * 0.35), int(s * 0.5), int(s * 0.65), int(s * 0.5))
            p.drawLine(int(s * 0.35), int(s * 0.65), int(s * 0.55), int(s * 0.65))
        elif k == "refresh":
            from PySide6.QtCore import QRectF
            rect = QRectF(m, m, s - 2 * m, s - 2 * m)
            p.drawArc(rect, 45 * 16, 270 * 16)
            p.drawLine(int(s - m * 1.2), int(m), int(s - m * 1.2), int(m * 2.2))
            p.drawLine(int(s - m * 1.2), int(m * 2.2), int(s - m * 2.4), int(m * 2.2))
        p.end()


def _soft(color_hex: str, alpha: float = 0.12) -> str:
    c = QColor(color_hex)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


class UretimVardiyaPage(BasePage):
    """Vardiya Raporu Sayfasi"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

        # Otomatik yenileme (30 saniye)
        self.auto_refresh = QTimer()
        self.auto_refresh.timeout.connect(self._load_data)
        self.auto_refresh.start(30000)

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT};
                font-family: {brand.FONT_FAMILY};
                font-size: {brand.FS_BODY}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_4, brand.SP_6, brand.SP_4)
        layout.setSpacing(brand.SP_3)

        # ===== HEADER (kompakt tek satir) =====
        header_frame = QFrame()
        header_frame.setFixedHeight(brand.sp(56))
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_MD}px;
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(brand.SP_4, 0, brand.SP_4, 0)
        header_layout.setSpacing(brand.SP_3)

        icon_box = QFrame()
        icon_box.setFixedSize(brand.sp(32), brand.sp(32))
        icon_box.setStyleSheet(
            f"background: {_soft(brand.PRIMARY, 0.12)}; "
            f"border: 1px solid {_soft(brand.PRIMARY, 0.35)}; "
            f"border-radius: {brand.R_SM}px;"
        )
        ib = QVBoxLayout(icon_box)
        ib.setContentsMargins(0, 0, 0, 0)
        ib.addWidget(BrandIcon("factory", brand.PRIMARY, brand.sp(18)), 0, Qt.AlignCenter)
        header_layout.addWidget(icon_box)

        title = QLabel("Vardiya Raporu")
        title.setStyleSheet(
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"color: {brand.TEXT}; letter-spacing: -0.3px;"
        )
        header_layout.addWidget(title)

        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(brand.sp(24))
        sep.setStyleSheet(f"background: {brand.BORDER};")
        header_layout.addWidget(sep)

        def _mini_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; "
                f"font-weight: {brand.FW_MEDIUM};"
            )
            return lbl

        header_layout.addWidget(_mini_label("Tarih"))

        self.tarih_baslangic = QDateEdit()
        self.tarih_baslangic.setDate(QDate.currentDate().addDays(-7))
        self.tarih_baslangic.setCalendarPopup(True)
        self.tarih_baslangic.setStyleSheet(self._input_style())
        self.tarih_baslangic.setFixedWidth(brand.sp(110))
        self.tarih_baslangic.setFixedHeight(brand.sp(30))
        self.tarih_baslangic.dateChanged.connect(self._load_data)
        header_layout.addWidget(self.tarih_baslangic)

        header_layout.addWidget(_mini_label("—"))

        self.tarih_bitis = QDateEdit()
        self.tarih_bitis.setDate(QDate.currentDate())
        self.tarih_bitis.setCalendarPopup(True)
        self.tarih_bitis.setStyleSheet(self._input_style())
        self.tarih_bitis.setFixedWidth(brand.sp(110))
        self.tarih_bitis.setFixedHeight(brand.sp(30))
        self.tarih_bitis.dateChanged.connect(self._load_data)
        header_layout.addWidget(self.tarih_bitis)

        header_layout.addWidget(_mini_label("Vardiya"))
        self.vardiya_combo = QComboBox()
        self.vardiya_combo.setStyleSheet(self._input_style())
        self.vardiya_combo.setFixedWidth(brand.sp(110))
        self.vardiya_combo.setFixedHeight(brand.sp(30))
        self.vardiya_combo.setCursor(Qt.PointingHandCursor)
        self.vardiya_combo.currentIndexChanged.connect(self._load_data)
        header_layout.addWidget(self.vardiya_combo)

        header_layout.addWidget(_mini_label("Operator"))
        self.operator_combo = QComboBox()
        self.operator_combo.setStyleSheet(self._input_style())
        self.operator_combo.setFixedWidth(brand.sp(140))
        self.operator_combo.setFixedHeight(brand.sp(30))
        self.operator_combo.setCursor(Qt.PointingHandCursor)
        self.operator_combo.currentIndexChanged.connect(self._load_data)
        header_layout.addWidget(self.operator_combo)

        header_layout.addStretch()

        refresh_btn = QPushButton("Yenile")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setFixedHeight(brand.sp(30))
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
            }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(refresh_btn)

        layout.addWidget(header_frame)

        # ===== OZET KARTLARI =====
        ozet_layout = QHBoxLayout()
        ozet_layout.setSpacing(brand.SP_3)

        self.kart_toplam  = self._create_ozet_kart("chart",        "Toplam Kayit",  "0",       brand.PRIMARY)
        self.kart_adet    = self._create_ozet_kart("box",          "Toplam Uretim", "0 adet",  brand.SUCCESS)
        self.kart_sure    = self._create_ozet_kart("clock",        "Ortalama Sure", "0 dk",    brand.WARNING)
        self.kart_vardiya = self._create_ozet_kart("factory",      "Aktif Vardiya", "-",       brand.INFO)

        ozet_layout.addWidget(self.kart_toplam)
        ozet_layout.addWidget(self.kart_adet)
        ozet_layout.addWidget(self.kart_sure)
        ozet_layout.addWidget(self.kart_vardiya)

        layout.addLayout(ozet_layout)

        # ===== TAB WIDGET =====
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                background: {brand.BG_CARD};
                top: -1px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {brand.TEXT_MUTED};
                border: 1px solid transparent;
                border-top-left-radius: {brand.R_SM}px;
                border-top-right-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_5}px;
                margin-right: {brand.SP_1}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
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
        
        # SEKME 1: Vardiya Detay
        detay_tab = QWidget()
        detay_layout = QVBoxLayout(detay_tab)
        detay_layout.setContentsMargins(brand.SP_3, brand.SP_3, brand.SP_3, brand.SP_3)
        detay_layout.setSpacing(brand.SP_2)

        # Splitter - Sol: Vardiya ozeti, Sag: Detay tablo
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(brand.sp(4))
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {brand.BORDER}; }}
            QSplitter::handle:hover {{ background: {brand.BORDER_HARD}; }}
        """)

        # SOL - Vardiya ozet tablosu
        sol_widget = QWidget()
        sol_layout = QVBoxLayout(sol_widget)
        sol_layout.setContentsMargins(0, 0, 0, 0)
        sol_layout.setSpacing(brand.SP_2)

        sol_title = QLabel("VARDIYA OZETI")
        sol_title.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_CAPTION}px; padding: {brand.SP_1}px 0; "
            f"letter-spacing: 0.8px;"
        )
        sol_layout.addWidget(sol_title)

        self.ozet_table = QTableWidget()
        self._apply_table_style(self.ozet_table)
        self.ozet_table.setColumnCount(4)
        self.ozet_table.setHorizontalHeaderLabels(["VARDIYA", "KAYIT", "URETIM", "ORT. SURE"])
        self.ozet_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ozet_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.ozet_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.ozet_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.ozet_table.verticalHeader().setVisible(False)
        self.ozet_table.verticalHeader().setDefaultSectionSize(brand.sp(38))
        self.ozet_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ozet_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ozet_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        sol_layout.addWidget(self.ozet_table)

        splitter.addWidget(sol_widget)

        # SAG - Detay tablo
        sag_widget = QWidget()
        sag_layout = QVBoxLayout(sag_widget)
        sag_layout.setContentsMargins(0, 0, 0, 0)
        sag_layout.setSpacing(brand.SP_2)

        sag_title = QLabel("DETAYLI KAYITLAR")
        sag_title.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_CAPTION}px; padding: {brand.SP_1}px 0; "
            f"letter-spacing: 0.8px;"
        )
        sag_layout.addWidget(sag_title)

        self.detay_table = QTableWidget()
        self._apply_table_style(self.detay_table)
        self.detay_table.setColumnCount(9)
        self.detay_table.setHorizontalHeaderLabels([
            "TARIH", "VARDIYA", "OPERATOR", "IS EMRI",
            "URUN", "URETILEN", "KALITE", "SURE (DK)", "NOT"
        ])

        self.detay_table.setColumnWidth(0, brand.sp(90))
        self.detay_table.setColumnWidth(1, brand.sp(80))
        self.detay_table.setColumnWidth(2, brand.sp(120))
        self.detay_table.setColumnWidth(3, brand.sp(110))
        self.detay_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.detay_table.setColumnWidth(5, brand.sp(80))
        self.detay_table.setColumnWidth(6, brand.sp(70))
        self.detay_table.setColumnWidth(7, brand.sp(80))
        self.detay_table.setColumnWidth(8, brand.sp(80))

        self.detay_table.verticalHeader().setVisible(False)
        self.detay_table.verticalHeader().setDefaultSectionSize(brand.sp(36))
        self.detay_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.detay_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.detay_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        sag_layout.addWidget(self.detay_table)

        splitter.addWidget(sag_widget)
        splitter.setSizes([brand.sp(280), brand.sp(820)])

        detay_layout.addWidget(splitter)
        self.tab_widget.addTab(detay_tab, "Vardiya Detay")
        
        # SEKME 2: Trend Raporu
        self._setup_trend_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Combolar yükle
        self._load_combos()
    
    def _setup_trend_tab(self):
        """Trend raporu sekmesini olustur"""
        trend_tab = QWidget()
        trend_layout = QVBoxLayout(trend_tab)
        trend_layout.setContentsMargins(brand.SP_3, brand.SP_3, brand.SP_3, brand.SP_3)
        trend_layout.setSpacing(brand.SP_3)

        # Ust filtre paneli
        filter_frame = QFrame()
        filter_frame.setFixedHeight(brand.sp(54))
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_SURFACE};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_MD}px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(brand.SP_4, 0, brand.SP_4, 0)
        filter_layout.setSpacing(brand.SP_3)

        def _mini_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; "
                f"font-weight: {brand.FW_SEMIBOLD}; letter-spacing: 0.4px;"
            )
            return lbl

        cal_icon_box = QFrame()
        cal_icon_box.setFixedSize(brand.sp(28), brand.sp(28))
        cal_icon_box.setStyleSheet(
            f"background: {_soft(brand.PRIMARY, 0.12)}; "
            f"border-radius: {brand.R_SM}px;"
        )
        cib = QVBoxLayout(cal_icon_box)
        cib.setContentsMargins(0, 0, 0, 0)
        cib.addWidget(BrandIcon("calendar", brand.PRIMARY, brand.sp(14)), 0, Qt.AlignCenter)
        filter_layout.addWidget(cal_icon_box)

        filter_layout.addWidget(_mini_label("TARIH ARALIGI"))

        self.trend_baslangic = QDateEdit()
        self.trend_baslangic.setDate(QDate.currentDate().addDays(-7))
        self.trend_baslangic.setCalendarPopup(True)
        self.trend_baslangic.setStyleSheet(self._input_style())
        self.trend_baslangic.setFixedWidth(brand.sp(120))
        self.trend_baslangic.setFixedHeight(brand.sp(32))
        self.trend_baslangic.dateChanged.connect(self._load_trend_data)
        filter_layout.addWidget(self.trend_baslangic)

        filter_layout.addWidget(_mini_label("—"))

        self.trend_bitis = QDateEdit()
        self.trend_bitis.setDate(QDate.currentDate())
        self.trend_bitis.setCalendarPopup(True)
        self.trend_bitis.setStyleSheet(self._input_style())
        self.trend_bitis.setFixedWidth(brand.sp(120))
        self.trend_bitis.setFixedHeight(brand.sp(32))
        self.trend_bitis.dateChanged.connect(self._load_trend_data)
        filter_layout.addWidget(self.trend_bitis)

        filter_layout.addWidget(_mini_label("HAT"))
        self.trend_hat_combo = QComboBox()
        self.trend_hat_combo.setStyleSheet(self._input_style())
        self.trend_hat_combo.setFixedWidth(brand.sp(120))
        self.trend_hat_combo.setFixedHeight(brand.sp(32))
        self.trend_hat_combo.setCursor(Qt.PointingHandCursor)
        self.trend_hat_combo.addItems(["TUM HATLAR", "KTL", "CINKO", "DIGER"])
        self.trend_hat_combo.currentIndexChanged.connect(self._load_trend_data)
        filter_layout.addWidget(self.trend_hat_combo)

        filter_layout.addStretch()

        trend_refresh_btn = QPushButton("Yenile")
        trend_refresh_btn.setCursor(Qt.PointingHandCursor)
        trend_refresh_btn.setFixedHeight(brand.sp(32))
        trend_refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: 1px solid {brand.PRIMARY};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{
                background: {brand.PRIMARY_HOVER};
                border-color: {brand.PRIMARY_HOVER};
            }}
        """)
        trend_refresh_btn.clicked.connect(self._load_trend_data)
        filter_layout.addWidget(trend_refresh_btn)

        trend_layout.addWidget(filter_frame)

        # Ozet istatistikler - 4 kart
        ozet_frame = QFrame()
        ozet_frame.setStyleSheet("background: transparent; border: none;")
        ozet_stat_layout = QHBoxLayout(ozet_frame)
        ozet_stat_layout.setContentsMargins(0, 0, 0, 0)
        ozet_stat_layout.setSpacing(brand.SP_3)

        self.trend_kart_toplam   = self._create_trend_kart("box",           "Toplam Uretim",   "0", brand.PRIMARY)
        self.trend_kart_ortalama = self._create_trend_kart("chart",         "Gunluk Ortalama", "0", brand.SUCCESS)
        self.trend_kart_maks     = self._create_trend_kart("trending-up",   "En Yuksek Gun",   "0", brand.WARNING)
        self.trend_kart_min      = self._create_trend_kart("trending-down", "En Dusuk Gun",    "0", brand.INFO)

        ozet_stat_layout.addWidget(self.trend_kart_toplam)
        ozet_stat_layout.addWidget(self.trend_kart_ortalama)
        ozet_stat_layout.addWidget(self.trend_kart_maks)
        ozet_stat_layout.addWidget(self.trend_kart_min)

        trend_layout.addWidget(ozet_frame)

        # Gunluk Trend Tablosu
        tablo_title = QLabel("GUNLUK URETIM TRENDI")
        tablo_title.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_CAPTION}px; padding: {brand.SP_1}px 0; "
            f"letter-spacing: 0.8px;"
        )
        trend_layout.addWidget(tablo_title)

        self.trend_table = QTableWidget()
        self._apply_table_style(self.trend_table)
        self.trend_table.setColumnCount(10)
        self.trend_table.setHorizontalHeaderLabels([
            "TARIH", "GUN", "TOPLAM URETIM", "KTL", "CINKO",
            "DIGER", "ORT. SICAKLIK", "ORT. AKIM", "ORT. VOLTAJ", "KAYIT"
        ])

        widths = {0: 100, 1: 90, 2: 120, 3: 90, 4: 90, 5: 90, 6: 130, 7: 90, 8: 90, 9: 90}
        for col, w in widths.items():
            self.trend_table.setColumnWidth(col, brand.sp(w))

        self.trend_table.verticalHeader().setVisible(False)
        self.trend_table.verticalHeader().setDefaultSectionSize(brand.sp(38))
        self.trend_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.trend_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.trend_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.trend_table.setAlternatingRowColors(False)

        trend_layout.addWidget(self.trend_table, 1)

        self.tab_widget.addTab(trend_tab, "Trend Raporu")

        # Ilk yukleme
        QTimer.singleShot(200, self._load_trend_data)
    
    def _create_trend_kart(self, icon_kind: str, title: str, value: str, color: str) -> QFrame:
        """Trend icin kompakt ozet karti olustur"""
        frame = QFrame()
        frame.setFixedHeight(brand.sp(76))
        frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-left: 3px solid {color};
                border-radius: {brand.R_MD}px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(brand.SP_3, brand.SP_3, brand.SP_3, brand.SP_3)
        layout.setSpacing(brand.SP_1)

        # Baslik satiri
        header_layout = QHBoxLayout()
        header_layout.setSpacing(brand.SP_2)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header_layout.addWidget(BrandIcon(icon_kind, color, brand.sp(16)), 0, Qt.AlignVCenter)

        title_label = QLabel(title.upper())
        title_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; letter-spacing: 0.6px; "
            f"background: transparent; border: none;"
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Deger
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(
            f"color: {color}; font-size: {brand.FS_HEADING_LG}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(value_label)

        return frame
    
    def _load_trend_data(self):
        """Trend verilerini PLC'den yükle"""
        try:
            # Tarihleri datetime.date formatına çevir
            baslangic_date = self.trend_baslangic.date().toPython()
            bitis_date = self.trend_bitis.date().toPython()
            
            # SQL Server için string formatına çevir
            baslangic = baslangic_date.strftime('%Y-%m-%d')
            bitis = bitis_date.strftime('%Y-%m-%d')
            
            hat_filtre = self.trend_hat_combo.currentText()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Hat filtresi
            hat_where = ""
            if hat_filtre != "TÜM HATLAR":
                hat_where = f"AND hat_kodu = '{hat_filtre}'"
            
            # Debug bilgisi
            print(f"[TREND DEBUG] Başlangıç: {baslangic} ({type(baslangic)})")
            print(f"[TREND DEBUG] Bitiş: {bitis} ({type(bitis)})")
            print(f"[TREND DEBUG] Hat Filtre: {hat_filtre}")
            
            # Günlük trend sorgusu - plc_tarihce tablosundan
            query = f"""
                SELECT 
                    CAST(tarih_doldurma AS DATE) AS gun,
                    COUNT(*) AS kayit_sayisi,
                    SUM(ISNULL(miktar, 0)) AS toplam_uretim,
                    SUM(CASE WHEN hat_kodu = 'KTL' THEN ISNULL(miktar, 0) ELSE 0 END) AS ktl_uretim,
                    SUM(CASE WHEN hat_kodu = 'CINKO' THEN ISNULL(miktar, 0) ELSE 0 END) AS cinko_uretim,
                    SUM(CASE WHEN hat_kodu = 'DIGER' THEN ISNULL(miktar, 0) ELSE 0 END) AS diger_uretim,
                    AVG(CASE WHEN sicaklik BETWEEN 0 AND 500 THEN sicaklik ELSE NULL END) AS ort_sicaklik,
                    AVG(CASE WHEN akim BETWEEN 0 AND 9999 THEN akim ELSE NULL END) AS ort_akim,
                    AVG(CASE WHEN voltaj BETWEEN 0 AND 9999 THEN voltaj ELSE NULL END) AS ort_voltaj
                FROM uretim.plc_tarihce
                WHERE CAST(tarih_doldurma AS DATE) >= '{baslangic}' 
                  AND CAST(tarih_doldurma AS DATE) <= '{bitis}'
                {hat_where}
                GROUP BY CAST(tarih_doldurma AS DATE)
                ORDER BY gun DESC
            """
            
            print(f"[TREND DEBUG] SQL:\n{query}")
            
            cursor.execute(query)
            
            rows = cursor.fetchall()
            
            print(f"[TREND DEBUG] Bulunan kayıt sayısı: {len(rows)}")
            if rows:
                print(f"[TREND DEBUG] İlk 3 kayıt: {rows[:3]}")
            
            conn.close()
            
            # İstatistikler hesapla
            if rows:
                toplam_uretim = sum(r[2] or 0 for r in rows)
                ortalama_uretim = toplam_uretim / len(rows) if rows else 0
                maks_gun = max(rows, key=lambda x: x[2] or 0)
                min_gun = min(rows, key=lambda x: x[2] or 0)
                
                self.trend_kart_toplam.findChild(QLabel, "value").setText(f"{toplam_uretim:,.0f}")
                self.trend_kart_ortalama.findChild(QLabel, "value").setText(f"{ortalama_uretim:,.0f}")
                self.trend_kart_maks.findChild(QLabel, "value").setText(
                    f"{maks_gun[2]:,.0f}" if maks_gun[2] else "0"
                )
                self.trend_kart_min.findChild(QLabel, "value").setText(
                    f"{min_gun[2]:,.0f}" if min_gun[2] else "0"
                )
            else:
                self.trend_kart_toplam.findChild(QLabel, "value").setText("0")
                self.trend_kart_ortalama.findChild(QLabel, "value").setText("0")
                self.trend_kart_maks.findChild(QLabel, "value").setText("0")
                self.trend_kart_min.findChild(QLabel, "value").setText("0")
            
            # Tabloyu doldur
            self.trend_table.setRowCount(len(rows))
            
            gun_isimleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
            
            for i, row in enumerate(rows):
                gun_tarih, kayit, toplam, ktl, cinko, diger, sicak, akim, voltaj = row
                
                # Tarih
                tarih_str = gun_tarih.strftime('%d.%m.%Y') if gun_tarih else "-"
                self.trend_table.setItem(i, 0, QTableWidgetItem(tarih_str))
                
                # Gün adı
                gun_adi = gun_isimleri[gun_tarih.weekday()] if gun_tarih else "-"
                gun_item = QTableWidgetItem(gun_adi)
                if gun_tarih and gun_tarih.weekday() >= 5:  # Cumartesi/Pazar
                    gun_item.setForeground(QColor(brand.WARNING))
                self.trend_table.setItem(i, 1, gun_item)

                # Toplam uretim
                toplam_item = QTableWidgetItem(f"{toplam:,.0f}" if toplam else "0")
                toplam_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                font = QFont()
                font.setBold(True)
                toplam_item.setFont(font)
                toplam_item.setForeground(QColor(brand.PRIMARY))
                self.trend_table.setItem(i, 2, toplam_item)
                
                # KTL
                ktl_item = QTableWidgetItem(f"{ktl:,.0f}" if ktl else "0")
                ktl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.trend_table.setItem(i, 3, ktl_item)
                
                # CINKO
                cinko_item = QTableWidgetItem(f"{cinko:,.0f}" if cinko else "0")
                cinko_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.trend_table.setItem(i, 4, cinko_item)
                
                # Diğer
                diger_item = QTableWidgetItem(f"{diger:,.0f}" if diger else "0")
                diger_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.trend_table.setItem(i, 5, diger_item)
                
                # Ortalama Sicaklik
                sicak_str = f"{sicak:.1f} °C" if sicak else "-"
                sicak_item = QTableWidgetItem(sicak_str)
                sicak_item.setTextAlignment(Qt.AlignCenter)
                if sicak and sicak > 100:
                    sicak_item.setForeground(QColor(brand.ERROR))
                self.trend_table.setItem(i, 6, sicak_item)
                
                # Ortalama Akım
                akim_str = f"{akim:.1f} A" if akim else "-"
                akim_item = QTableWidgetItem(akim_str)
                akim_item.setTextAlignment(Qt.AlignCenter)
                self.trend_table.setItem(i, 7, akim_item)
                
                # Ortalama Voltaj
                voltaj_str = f"{voltaj:.1f} V" if voltaj else "-"
                voltaj_item = QTableWidgetItem(voltaj_str)
                voltaj_item.setTextAlignment(Qt.AlignCenter)
                self.trend_table.setItem(i, 8, voltaj_item)
                
                # Kayit sayisi
                kayit_item = QTableWidgetItem(str(kayit))
                kayit_item.setTextAlignment(Qt.AlignCenter)
                kayit_item.setForeground(QColor(brand.TEXT_DIM))
                self.trend_table.setItem(i, 9, kayit_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Trend verisi yükleme hatası: {str(e)}")
            import traceback
            traceback.print_exc()
    
    
    def _create_ozet_kart(self, icon_kind: str, title: str, value: str, color: str) -> QFrame:
        """Ozet karti olustur"""
        frame = QFrame()
        frame.setFixedHeight(brand.sp(62))
        frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-left: 3px solid {color};
                border-radius: {brand.R_MD}px;
            }}
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(brand.SP_3, brand.SP_2, brand.SP_3, brand.SP_2)
        layout.setSpacing(brand.SP_3)

        # Icon kutusu
        icon_box = QFrame()
        icon_box.setFixedSize(brand.sp(32), brand.sp(32))
        icon_box.setStyleSheet(
            f"background: {_soft(color, 0.12)}; "
            f"border-radius: {brand.R_SM}px;"
        )
        ib = QVBoxLayout(icon_box)
        ib.setContentsMargins(0, 0, 0, 0)
        ib.addWidget(BrandIcon(icon_kind, color, brand.sp(16)), 0, Qt.AlignCenter)
        layout.addWidget(icon_box)

        # Text container
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(title.upper())
        title_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; letter-spacing: 0.5px; "
            f"background: transparent; border: none;"
        )
        text_layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(
            f"color: {color}; font-size: {brand.FS_BODY_LG}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"background: transparent; border: none;"
        )
        text_layout.addWidget(value_label)

        layout.addLayout(text_layout)
        layout.addStretch()

        return frame
    
    def _load_combos(self):
        """Combo boxları doldur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Vardiya combo
            self.vardiya_combo.clear()
            self.vardiya_combo.addItem("Tümü", None)
            cursor.execute("SELECT id, ad FROM tanim.vardiyalar WHERE aktif_mi=1 ORDER BY id")
            for row in cursor.fetchall():
                self.vardiya_combo.addItem(row[1], row[0])
            
            # Operatör combo
            self.operator_combo.clear()
            self.operator_combo.addItem("Tümü", None)
            cursor.execute("""
                SELECT DISTINCT p.id, p.ad + ' ' + p.soyad AS ad_soyad
                FROM ik.personeller p
                JOIN uretim.uretim_kayitlari uk ON p.id = uk.operator_id
                WHERE p.aktif_mi = 1
                ORDER BY ad_soyad
            """)
            for row in cursor.fetchall():
                self.operator_combo.addItem(row[1], row[0])
            
            conn.close()
        except Exception as e:
            print(f"Combo yükleme hatası: {e}")
    
    def _load_data(self):
        """Verileri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Filtre parametreleri
            tarih_baslangic = self.tarih_baslangic.date().toPython()
            tarih_bitis = self.tarih_bitis.date().toPython()
            vardiya_id = self.vardiya_combo.currentData()
            operator_id = self.operator_combo.currentData()
            
            # SQL koşulları
            sql_where = "WHERE uk.tarih BETWEEN ? AND ?"
            params = [tarih_baslangic, tarih_bitis]
            
            if vardiya_id:
                sql_where += " AND uk.vardiya_id = ?"
                params.append(vardiya_id)
            
            if operator_id:
                sql_where += " AND uk.operator_id = ?"
                params.append(operator_id)
            
            # Detay verileri
            cursor.execute(f"""
                SELECT 
                    uk.tarih,
                    v.ad AS vardiya,
                    p.ad + ' ' + p.soyad AS operator,
                    ie.is_emri_no,
                    u.urun_kodu + ' - ' + u.urun_adi AS urun,
                    uk.uretilen_miktar,
                    uk.durum AS kayit_durumu,
                    CASE 
                        WHEN uk.baslama_zamani IS NOT NULL AND uk.bitis_zamani IS NOT NULL 
                        THEN DATEDIFF(MINUTE, uk.baslama_zamani, uk.bitis_zamani)
                        ELSE NULL
                    END AS sure_dk,
                    NULL AS notlar
                FROM uretim.uretim_kayitlari uk
                LEFT JOIN tanim.vardiyalar v ON uk.vardiya_id = v.id
                LEFT JOIN ik.personeller p ON uk.operator_id = p.id
                LEFT JOIN siparis.is_emirleri ie ON uk.is_emri_id = ie.id
                LEFT JOIN stok.urunler u ON ie.urun_id = u.id
                {sql_where}
                ORDER BY uk.tarih DESC, uk.olusturma_tarihi DESC
            """, params)
            
            detay_rows = cursor.fetchall()
            
            # Özet verileri (Vardiya bazlı)
            cursor.execute(f"""
                SELECT 
                    v.ad AS vardiya,
                    COUNT(*) AS kayit_sayisi,
                    SUM(uk.uretilen_miktar) AS toplam_uretim,
                    AVG(CASE 
                        WHEN uk.baslama_zamani IS NOT NULL AND uk.bitis_zamani IS NOT NULL 
                        THEN DATEDIFF(MINUTE, uk.baslama_zamani, uk.bitis_zamani)
                        ELSE NULL
                    END) AS ort_sure_dk
                FROM uretim.uretim_kayitlari uk
                LEFT JOIN tanim.vardiyalar v ON uk.vardiya_id = v.id
                {sql_where}
                GROUP BY v.ad, uk.vardiya_id
                ORDER BY uk.vardiya_id
            """, params)
            
            ozet_rows = cursor.fetchall()
            
            conn.close()
            
            # Özet kartları güncelle
            toplam_kayit = len(detay_rows)
            toplam_uretim = sum(row[5] for row in detay_rows if row[5])
            
            sure_list = [row[7] for row in detay_rows if row[7] is not None]
            ort_sure = sum(sure_list) / len(sure_list) if sure_list else 0
            
            # Aktif vardiya (şu anki saat bazlı)
            aktif_vardiya = self._get_aktif_vardiya()
            
            self.kart_toplam.findChild(QLabel, "value").setText(str(toplam_kayit))
            self.kart_adet.findChild(QLabel, "value").setText(f"{toplam_uretim:,.0f} adet")
            self.kart_sure.findChild(QLabel, "value").setText(f"{ort_sure:.0f} dk")
            self.kart_vardiya.findChild(QLabel, "value").setText(aktif_vardiya)
            
            # Özet tablosu doldur
            self.ozet_table.setRowCount(len(ozet_rows))
            for i, row in enumerate(ozet_rows):
                vardiya, kayit, uretim, sure = row
                
                self.ozet_table.setItem(i, 0, QTableWidgetItem(vardiya or "-"))
                self.ozet_table.setItem(i, 1, QTableWidgetItem(str(kayit)))
                self.ozet_table.setItem(i, 2, QTableWidgetItem(f"{uretim:,.0f}" if uretim else "0"))
                self.ozet_table.setItem(i, 3, QTableWidgetItem(f"{sure:.0f} dk" if sure else "-"))
                
                # Renklendirme
                for col in range(4):
                    item = self.ozet_table.item(i, col)
                    if col == 0:
                        item.setForeground(QColor(brand.PRIMARY))
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
            
            # Detay tablosu doldur
            self.detay_table.setRowCount(len(detay_rows))
            for i, row in enumerate(detay_rows):
                tarih, vardiya, operator, is_emri, urun, miktar, kalite, sure, not_ = row
                
                # Tarih
                tarih_str = tarih.strftime('%d.%m.%Y') if tarih else "-"
                self.detay_table.setItem(i, 0, QTableWidgetItem(tarih_str))
                
                # Vardiya
                self.detay_table.setItem(i, 1, QTableWidgetItem(vardiya or "-"))
                
                # Operatör
                self.detay_table.setItem(i, 2, QTableWidgetItem(operator or "-"))
                
                # İş Emri
                self.detay_table.setItem(i, 3, QTableWidgetItem(is_emri or "-"))
                
                # Ürün
                self.detay_table.setItem(i, 4, QTableWidgetItem(urun or "-"))
                
                # Miktar
                miktar_item = QTableWidgetItem(f"{miktar:,.0f}" if miktar else "0")
                miktar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.detay_table.setItem(i, 5, miktar_item)
                
                # Kalite
                kalite_item = QTableWidgetItem(kalite or "-")
                if kalite == "OK":
                    kalite_item.setForeground(QColor(brand.SUCCESS))
                elif kalite == "RED":
                    kalite_item.setForeground(QColor(brand.ERROR))
                else:
                    kalite_item.setForeground(QColor(brand.WARNING))
                self.detay_table.setItem(i, 6, kalite_item)
                
                # Süre
                sure_str = f"{sure} dk" if sure else "-"
                self.detay_table.setItem(i, 7, QTableWidgetItem(sure_str))
                
                # Not
                self.detay_table.setItem(i, 8, QTableWidgetItem(not_ or "-"))
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yükleme hatası: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _get_aktif_vardiya(self):
        """Şu anki saate göre aktif vardiyayı bul"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Şimdiki saat
            su_an = datetime.now().time()
            
            cursor.execute("""
                SELECT ad 
                FROM tanim.vardiyalar 
                WHERE aktif_mi = 1
                  AND baslangic_saati <= ? 
                  AND bitis_saati >= ?
                ORDER BY id
            """, (su_an, su_an))
            
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else "-"
        except Exception:
            return "-"
    
    def _input_style(self):
        return f"""
            QComboBox, QDateEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_1}px {brand.SP_3}px;
                font-size: {brand.FS_BODY_SM}px;
            }}
            QComboBox:hover, QDateEdit:hover {{ border-color: {brand.BORDER_HARD}; }}
            QComboBox:focus, QDateEdit:focus {{ border-color: {brand.PRIMARY}; }}
            QComboBox::drop-down, QDateEdit::drop-down {{ border: none; width: {brand.sp(22)}px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_ELEVATED};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                selection-background-color: {brand.PRIMARY};
                selection-color: white;
            }}
        """

    def _apply_table_style(self, table: QTableWidget):
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
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {brand.BORDER_HARD};
                border-radius: {brand.sp(4)}px;
                min-height: {brand.sp(30)}px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{
                background: transparent;
                height: {brand.sp(8)}px;
            }}
            QScrollBar::handle:horizontal {{
                background: {brand.BORDER_HARD};
                border-radius: {brand.sp(4)}px;
                min-width: {brand.sp(30)}px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        """)
        table.setShowGrid(False)
        table.setFrameShape(QFrame.NoFrame)
        table.horizontalHeader().setHighlightSections(False)
