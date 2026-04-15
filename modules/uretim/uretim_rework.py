# -*- coding: utf-8 -*-
"""
NEXOR ERP - Rework (Sokum) Yonetimi (Brand System)
==================================================
Sokumu bekleyen urunler icin is emri olusturma ve giris yonetimi.
Tum stiller core.nexor_brand uzerinden gelir.
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QTabWidget, QWidget,
    QComboBox, QSpinBox, QTextEdit, QDateEdit, QGridLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from datetime import datetime

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.hareket_motoru import HareketMotoru
from core.nexor_brand import brand
from dialogs.login import ModernLoginDialog


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

        if k == "refresh":
            from PySide6.QtCore import QRectF
            rect = QRectF(m, m, s - 2 * m, s - 2 * m)
            p.drawArc(rect, 45 * 16, 270 * 16)
            p.drawLine(int(s - m * 1.2), int(m), int(s - m * 1.2), int(m * 2.2))
            p.drawLine(int(s - m * 1.2), int(m * 2.2), int(s - m * 2.4), int(m * 2.2))
        elif k == "file":
            p.drawRect(int(s * 0.25), int(m), int(s * 0.5), int(s - 2 * m))
            p.drawLine(int(s * 0.35), int(s * 0.35), int(s * 0.65), int(s * 0.35))
            p.drawLine(int(s * 0.35), int(s * 0.5), int(s * 0.65), int(s * 0.5))
            p.drawLine(int(s * 0.35), int(s * 0.65), int(s * 0.55), int(s * 0.65))
        elif k == "check":
            p.drawLine(int(s * 0.22), int(s * 0.5), int(s * 0.42), int(s * 0.7))
            p.drawLine(int(s * 0.42), int(s * 0.7), int(s * 0.78), int(s * 0.32))
        elif k == "box":
            p.drawRect(int(m), int(m), int(s - 2 * m), int(s - 2 * m))
            p.drawLine(int(m), int(s * 0.42), int(s - m), int(s * 0.42))
        elif k == "tool":
            p.drawLine(int(m), int(s - m), int(s * 0.5), int(s * 0.5))
            p.drawLine(int(s * 0.5), int(s * 0.5), int(s - m), int(m))
            p.drawLine(int(s - m), int(m), int(s - m * 1.5), int(m * 1.5))
        elif k == "dot":
            p.setBrush(QBrush(QColor(self.color)))
            p.drawEllipse(int(s * 0.3), int(s * 0.3), int(s * 0.4), int(s * 0.4))
        elif k == "recycle":
            p.drawLine(int(m), int(s * 0.6), int(s * 0.35), int(s * 0.35))
            p.drawLine(int(s * 0.35), int(s * 0.35), int(s * 0.7), int(s * 0.35))
            p.drawLine(int(s * 0.7), int(s * 0.35), int(s * 0.55), int(s * 0.15))
            p.drawLine(int(s * 0.7), int(s * 0.35), int(s * 0.58), int(s * 0.5))
        p.end()


def _soft(color_hex: str, alpha: float = 0.12) -> str:
    c = QColor(color_hex)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


class ReworkPage(BasePage):
    """Rework (Sokum) Yonetimi - Is Emri ve Giris"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.setWindowTitle("Rework (Sokum) Yonetimi")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Ana UI olustur"""
        self.setStyleSheet(f"""
            QWidget {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT};
                font-family: {brand.FONT_FAMILY};
                font-size: {brand.FS_BODY}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_5, brand.SP_6, brand.SP_5)
        layout.setSpacing(brand.SP_4)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._get_tab_style())

        # Sekme 1: Is Emri Yonetimi
        self.tab_ie = self._create_is_emri_tab()
        self.tab_widget.addTab(self.tab_ie, "Is Emri Yonetimi")

        # Sekme 2: Sokum Girisi
        self.tab_giris = self._create_giris_tab()
        self.tab_widget.addTab(self.tab_giris, "Sokum Girisi")

        # Sekme 3: Depo Takip
        self.tab_depo = self._create_depo_takip_tab()
        self.tab_widget.addTab(self.tab_depo, "Depo Takip")

        layout.addWidget(self.tab_widget)

    def _create_header(self):
        """Baslik olustur"""
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
        ib.addWidget(BrandIcon("recycle", brand.PRIMARY, brand.sp(20)), 0, Qt.AlignCenter)
        header.addWidget(icon_box)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        title = QLabel("Rework (Sokum) Yonetimi")
        title.setStyleSheet(
            f"font-size: {brand.FS_TITLE}px; font-weight: {brand.FW_BOLD}; "
            f"color: {brand.TEXT}; letter-spacing: -0.4px;"
        )
        title_col.addWidget(title)

        subtitle = QLabel("Sokum is emri olusturma, giris ve depo takip")
        subtitle.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px;"
        )
        title_col.addWidget(subtitle)
        header.addLayout(title_col)

        header.addStretch()

        refresh_btn = QPushButton("Yenile")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(self._button_style())
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)

        header_widget = QWidget()
        header_widget.setLayout(header)
        return header_widget
    
    # ========================================================
    # SEKME 1: İŞ EMRİ YÖNETİMİ
    # ========================================================
    
    def _create_is_emri_tab(self):
        """Is emri yonetimi sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_3)

        section_title_style = (
            f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_CAPTION}px; padding: {brand.SP_1}px 0; "
            f"letter-spacing: 0.8px;"
        )
        label_style = (
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_MEDIUM}; background: transparent;"
        )

        bekleyen_header = QLabel("BEKLEYEN SOKUMLER (SOKUM DEPOSU)")
        bekleyen_header.setStyleSheet(section_title_style)
        layout.addWidget(bekleyen_header)

        self.bekleyen_table = self._create_table([
            "LOT NO", "URUN KODU", "URUN ADI", "MIKTAR",
            "BIRIM", "DEPO", "DURUM", "TARIH"
        ])
        self.bekleyen_table.itemSelectionChanged.connect(self._on_bekleyen_secim)
        layout.addWidget(self.bekleyen_table)

        # Is Emri Form
        form_frame = QFrame()
        form_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        form_layout_main = QVBoxLayout(form_frame)
        form_layout_main.setContentsMargins(brand.SP_5, brand.SP_4, brand.SP_5, brand.SP_4)
        form_layout_main.setSpacing(brand.SP_3)

        form_header = QLabel("YENI IS EMRI OLUSTUR")
        form_header.setStyleSheet(
            f"color: {brand.PRIMARY}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY_SM}px; letter-spacing: 0.6px; "
            f"background: transparent; border: none;"
        )
        form_layout_main.addWidget(form_header)

        form_layout = QGridLayout()
        form_layout.setSpacing(brand.SP_3)

        row = 0

        lbl_lot = QLabel("Lot No")
        lbl_lot.setStyleSheet(label_style)
        form_layout.addWidget(lbl_lot, row, 0)
        self.ie_lot_edit = QLineEdit()
        self.ie_lot_edit.setReadOnly(True)
        self.ie_lot_edit.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_lot_edit, row, 1)

        lbl_urun = QLabel("Urun")
        lbl_urun.setStyleSheet(label_style)
        form_layout.addWidget(lbl_urun, row, 2)
        self.ie_urun_edit = QLineEdit()
        self.ie_urun_edit.setReadOnly(True)
        self.ie_urun_edit.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_urun_edit, row, 3)

        row += 1

        lbl_miktar = QLabel("Miktar")
        lbl_miktar.setStyleSheet(label_style)
        form_layout.addWidget(lbl_miktar, row, 0)
        self.ie_miktar_edit = QLineEdit()
        self.ie_miktar_edit.setReadOnly(True)
        self.ie_miktar_edit.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_miktar_edit, row, 1)

        lbl_tip = QLabel("Sokum Tipi")
        lbl_tip.setStyleSheet(label_style)
        form_layout.addWidget(lbl_tip, row, 2)
        self.ie_tip_combo = QComboBox()
        self.ie_tip_combo.addItem("Kimyasal")
        self.ie_tip_combo.setEnabled(False)
        self.ie_tip_combo.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_tip_combo, row, 3)

        row += 1

        lbl_sorumlu = QLabel("Sorumlu")
        lbl_sorumlu.setStyleSheet(label_style)
        form_layout.addWidget(lbl_sorumlu, row, 0)
        self.ie_sorumlu_combo = QComboBox()
        self.ie_sorumlu_combo.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_sorumlu_combo, row, 1)

        lbl_tarih = QLabel("Baslangic")
        lbl_tarih.setStyleSheet(label_style)
        form_layout.addWidget(lbl_tarih, row, 2)
        self.ie_tarih_edit = QDateEdit()
        self.ie_tarih_edit.setDate(datetime.now().date())
        self.ie_tarih_edit.setCalendarPopup(True)
        self.ie_tarih_edit.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_tarih_edit, row, 3)

        row += 1

        lbl_not = QLabel("Not")
        lbl_not.setStyleSheet(label_style)
        form_layout.addWidget(lbl_not, row, 0, Qt.AlignTop)
        self.ie_not_edit = QTextEdit()
        self.ie_not_edit.setMaximumHeight(brand.sp(80))
        self.ie_not_edit.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_not_edit, row, 1, 1, 3)

        form_layout_main.addLayout(form_layout)

        # Buton
        self.ie_olustur_btn = QPushButton("IS EMRI OLUSTUR")
        self.ie_olustur_btn.setCursor(Qt.PointingHandCursor)
        self.ie_olustur_btn.setStyleSheet(self._cta_button_style(brand.SUCCESS))
        self.ie_olustur_btn.clicked.connect(self._is_emri_olustur)
        self.ie_olustur_btn.setEnabled(False)
        form_layout_main.addWidget(self.ie_olustur_btn)

        layout.addWidget(form_frame)

        # Aktif Is Emirleri
        aktif_header = QLabel("AKTIF IS EMIRLERI")
        aktif_header.setStyleSheet(section_title_style)
        layout.addWidget(aktif_header)

        self.aktif_ie_table = self._create_table([
            "IS EMRI NO", "LOT NO", "URUN", "MIKTAR",
            "TIP", "DURUM", "SORUMLU", "BASLANGIC"
        ])
        layout.addWidget(self.aktif_ie_table)

        return tab
    
    # ========================================================
    # SEKME 2: SÖKÜM GİRİŞİ
    # ========================================================
    
    def _create_giris_tab(self):
        """Sokum girisi sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_3)

        section_title_style = (
            f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_CAPTION}px; padding: {brand.SP_1}px 0; "
            f"letter-spacing: 0.8px;"
        )
        label_style = (
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_MEDIUM}; background: transparent;"
        )

        ie_header = QLabel("AKTIF IS EMIRLERI")
        ie_header.setStyleSheet(section_title_style)
        layout.addWidget(ie_header)

        self.giris_ie_table = self._create_table([
            "IS EMRI NO", "LOT NO", "URUN", "TOPLAM MIKTAR",
            "TIP", "SORUMLU", "BASLANGIC"
        ])
        self.giris_ie_table.itemSelectionChanged.connect(self._on_giris_ie_secim)
        layout.addWidget(self.giris_ie_table)

        # Giris Bilgileri
        giris_frame = QFrame()
        giris_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        giris_layout_main = QVBoxLayout(giris_frame)
        giris_layout_main.setContentsMargins(brand.SP_5, brand.SP_4, brand.SP_5, brand.SP_4)
        giris_layout_main.setSpacing(brand.SP_3)

        giris_header = QLabel("GIRIS BILGILERI")
        giris_header.setStyleSheet(
            f"color: {brand.PRIMARY}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY_SM}px; letter-spacing: 0.6px; "
            f"background: transparent; border: none;"
        )
        giris_layout_main.addWidget(giris_header)

        giris_layout = QGridLayout()
        giris_layout.setSpacing(brand.SP_3)

        row = 0

        lbl_ie = QLabel("Is Emri No")
        lbl_ie.setStyleSheet(label_style)
        giris_layout.addWidget(lbl_ie, row, 0)
        self.giris_ie_edit = QLineEdit()
        self.giris_ie_edit.setReadOnly(True)
        self.giris_ie_edit.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_ie_edit, row, 1)

        lbl_lot = QLabel("Lot No")
        lbl_lot.setStyleSheet(label_style)
        giris_layout.addWidget(lbl_lot, row, 2)
        self.giris_lot_edit = QLineEdit()
        self.giris_lot_edit.setReadOnly(True)
        self.giris_lot_edit.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_lot_edit, row, 3)

        row += 1

        lbl_toplam = QLabel("Toplam Miktar")
        lbl_toplam.setStyleSheet(label_style)
        giris_layout.addWidget(lbl_toplam, row, 0)
        self.giris_toplam_edit = QLineEdit()
        self.giris_toplam_edit.setReadOnly(True)
        self.giris_toplam_edit.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_toplam_edit, row, 1)

        lbl_giris = QLabel("Giris Miktari")
        lbl_giris.setStyleSheet(label_style)
        giris_layout.addWidget(lbl_giris, row, 2)
        self.giris_miktar_spin = QSpinBox()
        self.giris_miktar_spin.setMinimum(0)
        self.giris_miktar_spin.setMaximum(999999)
        self.giris_miktar_spin.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_miktar_spin, row, 3)

        row += 1

        lbl_kalite = QLabel("Kalite Durumu")
        lbl_kalite.setStyleSheet(label_style)
        giris_layout.addWidget(lbl_kalite, row, 0)
        self.giris_kalite_combo = QComboBox()
        self.giris_kalite_combo.addItems(["", "IYI", "ORTA", "KOTU"])
        self.giris_kalite_combo.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_kalite_combo, row, 1)

        lbl_sure = QLabel("Sokum Suresi (dk)")
        lbl_sure.setStyleSheet(label_style)
        giris_layout.addWidget(lbl_sure, row, 2)
        self.giris_sure_spin = QSpinBox()
        self.giris_sure_spin.setMinimum(0)
        self.giris_sure_spin.setMaximum(9999)
        self.giris_sure_spin.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_sure_spin, row, 3)

        row += 1

        lbl_not = QLabel("Not")
        lbl_not.setStyleSheet(label_style)
        giris_layout.addWidget(lbl_not, row, 0, Qt.AlignTop)
        self.giris_not_edit = QTextEdit()
        self.giris_not_edit.setMaximumHeight(brand.sp(80))
        self.giris_not_edit.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_not_edit, row, 1, 1, 3)

        giris_layout_main.addLayout(giris_layout)

        # Buton
        self.giris_btn = QPushButton("KAYDI TAMAMLA")
        self.giris_btn.setCursor(Qt.PointingHandCursor)
        self.giris_btn.setStyleSheet(self._cta_button_style(brand.SUCCESS))
        self.giris_btn.clicked.connect(self._giris_kaydet)
        self.giris_btn.setEnabled(False)
        giris_layout_main.addWidget(self.giris_btn)

        layout.addWidget(giris_frame)

        # Gecmis Girisler
        gecmis_header = QLabel("GECMIS GIRISLER (BUGUN)")
        gecmis_header.setStyleSheet(section_title_style)
        layout.addWidget(gecmis_header)

        self.gecmis_table = self._create_table([
            "TARIH", "IS EMRI NO", "LOT NO", "GIRIS MIKTARI",
            "KALAN", "KALITE", "SURE (DK)", "YAPAN"
        ])
        layout.addWidget(self.gecmis_table)

        return tab
    
    # ========================================================
    # SEKME 3: DEPO TAKİP
    # ========================================================
    
    def _create_depo_takip_tab(self):
        """Depo takip sekmesi - Sokum surecindeki depolari goster"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_3)

        header = QLabel("SOKUM SURECI DEPO DURUMU")
        header.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_CAPTION}px; padding: {brand.SP_1}px 0; "
            f"letter-spacing: 0.8px;"
        )
        layout.addWidget(header)

        # Depo kartlari icin container
        depo_frame = QFrame()
        depo_frame.setStyleSheet(
            f"background: transparent; border: none;"
        )
        depo_layout = QVBoxLayout(depo_frame)
        depo_layout.setContentsMargins(0, 0, 0, 0)

        depo_grid = QGridLayout()
        depo_grid.setSpacing(brand.SP_3)

        # Ilgili depolar (kod, ad, renk)
        ilgili_depolar = [
            ('RED',    'RED Deposu',     brand.ERROR),
            ('Yi',     'Sokum Bekleyen', brand.WARNING),
            ('SOKUM',  'Sokum Deposu',   brand.WARNING),
            ('KAB-01', 'Kabul Alani',    brand.SUCCESS),
        ]

        self.depo_widgets = {}

        for idx, (kod, ad, kart_renk) in enumerate(ilgili_depolar):
            row = idx // 2
            col = idx % 2

            kart = QFrame()
            kart.setStyleSheet(f"""
                QFrame {{
                    background: {brand.BG_CARD};
                    border: 1px solid {brand.BORDER};
                    border-left: 3px solid {kart_renk};
                    border-radius: {brand.R_MD}px;
                }}
            """)
            kart_layout = QVBoxLayout(kart)
            kart_layout.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)
            kart_layout.setSpacing(brand.SP_2)

            # Baslik satiri
            header_row = QHBoxLayout()
            header_row.setSpacing(brand.SP_2)
            header_row.setContentsMargins(0, 0, 0, 0)
            header_row.addWidget(BrandIcon("dot", kart_renk, brand.sp(12)), 0, Qt.AlignVCenter)

            baslik = QLabel(f"{ad.upper()} ({kod})")
            baslik.setStyleSheet(
                f"color: {kart_renk}; font-weight: {brand.FW_SEMIBOLD}; "
                f"font-size: {brand.FS_BODY_SM}px; letter-spacing: 0.4px; "
                f"background: transparent; border: none;"
            )
            header_row.addWidget(baslik)
            header_row.addStretch()
            kart_layout.addLayout(header_row)

            # Miktar etiketi
            miktar_lbl = QLabel("0 adet")
            miktar_lbl.setObjectName(f"miktar_{kod}")
            miktar_lbl.setStyleSheet(
                f"color: {brand.TEXT}; font-size: {brand.FS_TITLE}px; "
                f"font-weight: {brand.FW_BOLD}; "
                f"background: transparent; border: none;"
            )
            kart_layout.addWidget(miktar_lbl)

            # Lot sayisi
            lot_lbl = QLabel("0 lot")
            lot_lbl.setObjectName(f"lot_{kod}")
            lot_lbl.setStyleSheet(
                f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
                f"background: transparent; border: none;"
            )
            kart_layout.addWidget(lot_lbl)

            # Durum listesi
            durum_lbl = QLabel("")
            durum_lbl.setObjectName(f"durum_{kod}")
            durum_lbl.setStyleSheet(
                f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px; "
                f"background: transparent; border: none;"
            )
            durum_lbl.setWordWrap(True)
            kart_layout.addWidget(durum_lbl)

            self.depo_widgets[kod] = {
                'miktar': miktar_lbl,
                'lot': lot_lbl,
                'durum': durum_lbl,
            }

            depo_grid.addWidget(kart, row, col)

        depo_layout.addLayout(depo_grid)
        layout.addWidget(depo_frame)

        # Detay tablosu
        detay_header = QLabel("DETAYLI STOK LISTESI")
        detay_header.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_CAPTION}px; padding-top: {brand.SP_3}px; "
            f"letter-spacing: 0.8px;"
        )
        layout.addWidget(detay_header)

        self.depo_detay_table = self._create_table([
            "DEPO", "LOT NO", "URUN KODU", "URUN ADI",
            "MIKTAR", "BIRIM", "DURUM", "SON HAREKET"
        ])
        layout.addWidget(self.depo_detay_table)

        # Ilk yukleme
        self._load_depo_takip()

        return tab
    
    def _load_depo_takip(self):
        """Depo takip verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # İlgili depoların özeti
            cursor.execute("""
                SELECT 
                    d.kod,
                    COALESCE(SUM(sb.miktar), 0) as toplam_miktar,
                    COUNT(DISTINCT sb.lot_no) as lot_sayisi,
                    STUFF((
                        SELECT DISTINCT ', ' + sb2.durum_kodu
                        FROM stok.stok_bakiye sb2
                        WHERE sb2.depo_id = d.id AND sb2.miktar > 0
                        FOR XML PATH(''), TYPE
                    ).value('.', 'NVARCHAR(MAX)'), 1, 2, '') as durumlar
                FROM tanim.depolar d
                LEFT JOIN stok.stok_bakiye sb ON d.id = sb.depo_id AND sb.miktar > 0
                WHERE d.kod IN ('RED', 'Yi', 'SOKUM', 'KAB-01')
                GROUP BY d.kod, d.id
            """)
            
            for row in cursor.fetchall():
                kod, miktar, lot_sayisi, durumlar = row
                if kod in self.depo_widgets:
                    self.depo_widgets[kod]['miktar'].setText(f"{miktar:,.0f} adet")
                    self.depo_widgets[kod]['lot'].setText(f"{lot_sayisi} lot")
                    self.depo_widgets[kod]['durum'].setText(durumlar or "Boş")
            
            # Detay tablosu
            cursor.execute("""
                SELECT 
                    d.kod AS depo_kod,
                    sb.lot_no,
                    u.urun_kodu,
                    u.urun_adi,
                    sb.miktar,
                    sb.birim,
                    sb.durum_kodu,
                    sb.son_hareket_tarihi
                FROM stok.stok_bakiye sb
                JOIN tanim.depolar d ON sb.depo_id = d.id
                JOIN stok.urunler u ON sb.urun_id = u.id
                WHERE d.kod IN ('RED', 'Yi', 'SOKUM', 'KAB-01')
                  AND sb.miktar > 0
                ORDER BY d.kod, sb.lot_no
            """)
            
            self.depo_detay_table.setRowCount(0)
            
            for row_data in cursor.fetchall():
                row = self.depo_detay_table.rowCount()
                self.depo_detay_table.insertRow(row)
                
                for col, value in enumerate(row_data):
                    if col == 4:  # Miktar
                        value = f"{value:,.0f}"
                    elif col == 7:  # Tarih
                        value = value.strftime("%d.%m.%Y %H:%M") if value else ""
                    
                    item = QTableWidgetItem(str(value) if value else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # Depo kodu renklendirme
                    if col == 0:
                        if value == 'RED':
                            item.setForeground(QColor(brand.ERROR))
                        elif value in ('Yi', 'SOKUM'):
                            item.setForeground(QColor(brand.WARNING))
                        elif value == 'KAB-01':
                            item.setForeground(QColor(brand.SUCCESS))

                    # Durum renklendirme
                    if col == 6:
                        if 'RED' in str(value):
                            item.setForeground(QColor(brand.ERROR))
                        elif 'SOKUM' in str(value):
                            item.setForeground(QColor(brand.WARNING))
                        elif 'KABUL' in str(value):
                            item.setForeground(QColor(brand.SUCCESS))
                    
                    self.depo_detay_table.setItem(row, col, item)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Depo takip yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    # ========================================================
    # VERİ YÜKLEME
    # ========================================================
    
    def _load_data(self):
        """Tüm verileri yükle"""
        self._load_bekleyen_sokumler()
        self._load_aktif_is_emirleri()
        self._load_sokum_is_emirleri()
        self._load_gecmis_girisler()
        self._load_sorumlular()
        self._load_depo_takip()  # ✅ Depo takip de yüklensin
    
    def _load_bekleyen_sokumler(self):
        """SOKUM deposundaki ürünleri listele"""
        self.bekleyen_table.setRowCount(0)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # ✅ Düzeltildi: LIKE 'SOKUM%' ile tüm SOKUM durumları, giris_tarihi kullanıldı
            cursor.execute("""
                SELECT 
                    sb.lot_no,
                    u.urun_kodu,
                    u.urun_adi,
                    sb.miktar,
                    sb.birim,
                    d.kod AS depo_kod,
                    sb.durum_kodu,
                    sb.giris_tarihi
                FROM stok.stok_bakiye sb
                JOIN stok.urunler u ON sb.urun_id = u.id
                JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE d.kod = 'SOKUM'
                  AND sb.miktar > 0
                  AND sb.durum_kodu LIKE 'SOKUM%'
                ORDER BY sb.giris_tarihi DESC
            """)
            
            rows = cursor.fetchall()
            
            for row_data in rows:
                row = self.bekleyen_table.rowCount()
                self.bekleyen_table.insertRow(row)
                
                for col, value in enumerate(row_data):
                    if col == 7:  # Tarih
                        value = value.strftime("%d.%m.%Y %H:%M") if value else ""
                    elif col == 3:  # Miktar
                        value = f"{value:,.0f}"
                    
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.bekleyen_table.setItem(row, col, item)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Bekleyen sökümler yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_aktif_is_emirleri(self):
        """Aktif iş emirlerini listele (İş Emri sekmesi için)"""
        self.aktif_ie_table.setRowCount(0)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    sie.is_emri_no,
                    sie.lot_no,
                    u.urun_adi,
                    sie.miktar,
                    sie.sokum_tipi,
                    sie.durum,
                    p.ad + ' ' + p.soyad AS sorumlu,
                    sie.baslangic_tarihi
                FROM uretim.sokum_is_emirleri sie
                LEFT JOIN stok.urunler u ON sie.urun_id = u.id
                LEFT JOIN ik.personeller p ON sie.sorumlu_id = p.id
                WHERE sie.durum IN ('BEKLEMEDE', 'DEVAM_EDIYOR')
                ORDER BY sie.id DESC
            """)
            
            rows = cursor.fetchall()
            
            for row_data in rows:
                row = self.aktif_ie_table.rowCount()
                self.aktif_ie_table.insertRow(row)
                
                for col, value in enumerate(row_data):
                    if col == 7:  # Tarih
                        value = value.strftime("%d.%m.%Y") if value else ""
                    elif col == 3:  # Miktar
                        value = f"{value:,.0f}"
                    
                    item = QTableWidgetItem(str(value) if value else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # Durum renklendirme
                    if col == 5:  # Durum kolonu
                        if value == 'BEKLEMEDE':
                            item.setForeground(QColor('#fbbf24'))  # amber
                        elif value == 'DEVAM_EDIYOR':
                            item.setForeground(QColor('#3b82f6'))  # blue
                    
                    self.aktif_ie_table.setItem(row, col, item)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Aktif iş emirleri yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_sokum_is_emirleri(self):
        """Söküm girişi için aktif iş emirlerini listele"""
        self.giris_ie_table.setRowCount(0)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    sie.id,
                    sie.is_emri_no,
                    sie.lot_no,
                    u.urun_adi,
                    sie.miktar,
                    sie.sokum_tipi,
                    p.ad + ' ' + p.soyad AS sorumlu,
                    sie.baslangic_tarihi
                FROM uretim.sokum_is_emirleri sie
                LEFT JOIN stok.urunler u ON sie.urun_id = u.id
                LEFT JOIN ik.personeller p ON sie.sorumlu_id = p.id
                WHERE sie.durum IN ('BEKLEMEDE', 'DEVAM_EDIYOR')
                  AND sie.miktar > 0
                ORDER BY sie.id DESC
            """)
            
            rows = cursor.fetchall()
            
            for row_data in rows:
                row = self.giris_ie_table.rowCount()
                self.giris_ie_table.insertRow(row)
                
                # id'yi sakla (görünmez)
                ie_id = row_data[0]
                
                for col, value in enumerate(row_data[1:], start=0):
                    if col == 6:  # Tarih
                        value = value.strftime("%d.%m.%Y") if value else ""
                    elif col == 3:  # Miktar
                        value = f"{value:,.0f}"
                    
                    item = QTableWidgetItem(str(value) if value else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # İlk satıra id'yi sakla
                    if col == 0:
                        item.setData(Qt.UserRole, ie_id)
                    
                    self.giris_ie_table.setItem(row, col, item)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İş emirleri yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_gecmis_girisler(self):
        """Bugünkü girişleri listele"""
        self.gecmis_table.setRowCount(0)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    sg.giris_tarihi,
                    sie.is_emri_no,
                    sg.lot_no,
                    sg.giris_miktar,
                    sg.kalan_miktar,
                    sg.kalite_durumu,
                    sg.sokum_suresi,
                    p.ad + ' ' + p.soyad AS yapan
                FROM uretim.sokum_giris sg
                JOIN uretim.sokum_is_emirleri sie ON sg.sokum_is_emri_id = sie.id
                LEFT JOIN ik.personeller p ON sg.giris_yapan_id = p.id
                WHERE CAST(sg.giris_tarihi AS DATE) = CAST(GETDATE() AS DATE)
                ORDER BY sg.id DESC
            """)
            
            rows = cursor.fetchall()
            
            for row_data in rows:
                row = self.gecmis_table.rowCount()
                self.gecmis_table.insertRow(row)
                
                for col, value in enumerate(row_data):
                    if col == 0:  # Tarih
                        value = value.strftime("%d.%m.%Y %H:%M") if value else ""
                    elif col in [3, 4]:  # Miktar kolonları
                        value = f"{value:,.0f}" if value else "0"
                    
                    item = QTableWidgetItem(str(value) if value else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.gecmis_table.setItem(row, col, item)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Geçmiş girişler yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_sorumlular(self):
        """Sorumlu personel listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, ad + ' ' + soyad AS ad_soyad
                FROM ik.personeller
                WHERE aktif_mi = 1
                ORDER BY ad, soyad
            """)
            
            self.ie_sorumlu_combo.clear()
            self.ie_sorumlu_combo.addItem("-- Seçiniz --", None)
            
            for row in cursor.fetchall():
                self.ie_sorumlu_combo.addItem(row[1], row[0])
            
            conn.close()
            
        except Exception as e:
            print(f"Sorumlular yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    # ========================================================
    # EVENT HANDLERS
    # ========================================================
    
    def _on_bekleyen_secim(self):
        """Bekleyen sökümlerden seçim yapıldığında"""
        selected = self.bekleyen_table.selectedItems()
        if not selected:
            self.ie_olustur_btn.setEnabled(False)
            return
        
        row = selected[0].row()
        
        lot_no = self.bekleyen_table.item(row, 0).text()
        urun_kodu = self.bekleyen_table.item(row, 1).text()
        urun_adi = self.bekleyen_table.item(row, 2).text()
        miktar = self.bekleyen_table.item(row, 3).text()
        
        self.ie_lot_edit.setText(lot_no)
        self.ie_urun_edit.setText(f"{urun_kodu} - {urun_adi}")
        self.ie_miktar_edit.setText(miktar)
        
        self.ie_olustur_btn.setEnabled(True)
    
    def _on_giris_ie_secim(self):
        """Giriş için iş emri seçildiğinde"""
        selected = self.giris_ie_table.selectedItems()
        if not selected:
            self.giris_btn.setEnabled(False)
            return
        
        row = selected[0].row()
        
        ie_no = self.giris_ie_table.item(row, 0).text()
        lot_no = self.giris_ie_table.item(row, 1).text()
        miktar = self.giris_ie_table.item(row, 3).text()
        
        # id'yi al
        ie_id = self.giris_ie_table.item(row, 0).data(Qt.UserRole)
        
        self.giris_ie_edit.setText(ie_no)
        self.giris_ie_edit.setProperty('ie_id', ie_id)
        self.giris_lot_edit.setText(lot_no)
        self.giris_toplam_edit.setText(miktar)
        
        # Miktar spin'i ayarla
        miktar_int = int(miktar.replace(',', '').replace('.', ''))
        self.giris_miktar_spin.setMaximum(miktar_int)
        self.giris_miktar_spin.setValue(miktar_int)
        
        self.giris_btn.setEnabled(True)
    
    # ========================================================
    # İŞ EMRİ İŞLEMLERİ
    # ========================================================
    
    def _is_emri_olustur(self):
        """Yeni iş emri oluştur"""
        try:
            lot_no = self.ie_lot_edit.text().strip()
            if not lot_no:
                QMessageBox.warning(self, "Uyarı", "Lot numarası seçilmedi!")
                return
            
            sorumlu_id = self.ie_sorumlu_combo.currentData()
            if not sorumlu_id:
                QMessageBox.warning(self, "Uyarı", "Sorumlu seçilmedi!")
                return
            
            baslangic = self.ie_tarih_edit.date().toPython()
            notlar = self.ie_not_edit.toPlainText().strip()
            
            # Lot'tan ürün bilgisini al
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # ✅ Düzeltildi: LIKE 'SOKUM%' ile
            cursor.execute("""
                SELECT sb.urun_id, sb.miktar
                FROM stok.stok_bakiye sb
                JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE sb.lot_no = ? 
                  AND d.kod = 'SOKUM'
                  AND sb.durum_kodu LIKE 'SOKUM%'
            """, (lot_no,))
            
            row = cursor.fetchone()
            if not row:
                raise Exception("Lot bilgisi bulunamadı!")
            
            urun_id, miktar = row
            
            # İş emri numarası oluştur (SOKUM-YYMMDD-XXXX formatında)
            tarih_str = datetime.now().strftime('%y%m%d')
            
            cursor.execute("""
                SELECT ISNULL(MAX(CAST(RIGHT(is_emri_no, 4) AS INT)), 0) + 1
                FROM uretim.sokum_is_emirleri
                WHERE is_emri_no LIKE ?
            """, (f'SOKUM-{tarih_str}-%',))
            
            sira = cursor.fetchone()[0]
            is_emri_no = f"SOKUM-{tarih_str}-{sira:04d}"
            
            # İş emrini kaydet
            cursor.execute("""
                INSERT INTO uretim.sokum_is_emirleri (
                    is_emri_no, lot_no, urun_id, miktar, sokum_tipi,
                    durum, sorumlu_id, baslangic_tarihi, notlar,
                    olusturan_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                is_emri_no,
                lot_no,
                urun_id,
                miktar,
                'Kimyasal',
                'BEKLEMEDE',
                sorumlu_id,
                baslangic,
                notlar or None,
                ModernLoginDialog.current_user_id or 1
            ))
            
            conn.commit()
            LogManager.log_insert('uretim', 'uretim.rework_is_emirleri', None,
                                  f'Rework is emri olusturuldu: {is_emri_no}, Lot: {lot_no}, {miktar} adet')
            conn.close()

            QMessageBox.information(
                self,
                "Basarili",
                f"İş emri oluşturuldu!\n\nİş Emri No: {is_emri_no}\nLot: {lot_no}"
            )
            
            # Formu temizle
            self.ie_lot_edit.clear()
            self.ie_urun_edit.clear()
            self.ie_miktar_edit.clear()
            self.ie_not_edit.clear()
            self.ie_sorumlu_combo.setCurrentIndex(0)
            self.ie_olustur_btn.setEnabled(False)
            
            # Verileri yenile
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İş emri oluşturulamadı: {e}")
            import traceback
            traceback.print_exc()
    
    # ========================================================
    # SÖKÜM GİRİŞİ İŞLEMLERİ
    # ========================================================
    
    def _giris_kaydet(self):
        """Söküm girişini kaydet"""
        try:
            ie_id = self.giris_ie_edit.property('ie_id')
            if not ie_id:
                QMessageBox.warning(self, "Uyarı", "İş emri seçilmedi!")
                return
            
            giris_miktar = self.giris_miktar_spin.value()
            if giris_miktar <= 0:
                QMessageBox.warning(self, "Uyarı", "Giriş miktarı 0'dan büyük olmalı!")
                return
            
            eski_lot_no = self.giris_lot_edit.text().strip()
            is_emri_no = self.giris_ie_edit.text().strip()
            toplam_miktar_str = self.giris_toplam_edit.text().replace(',', '').replace('.', '')
            toplam_miktar = int(toplam_miktar_str)
            
            if giris_miktar > toplam_miktar:
                QMessageBox.warning(
                    self, 
                    "Uyarı", 
                    f"Giriş miktarı ({giris_miktar}) toplam miktarı ({toplam_miktar}) aşamaz!"
                )
                return
            
            # ✅ YENİ LOT NUMARASI: -RED kaldır, -S ekle
            if eski_lot_no.endswith('-RED'):
                yeni_lot_no = eski_lot_no.replace('-RED', '-S')
            elif not eski_lot_no.endswith('-S'):
                yeni_lot_no = f"{eski_lot_no}-S"
            else:
                yeni_lot_no = eski_lot_no
            
            conn = get_db_connection()
            cursor = conn.cursor()
            motor = HareketMotoru(conn)
            
            # Depo ID'lerini al
            cursor.execute("SELECT id FROM tanim.depolar WHERE kod = 'KAB-01'")
            kab_depo_row = cursor.fetchone()
            if not kab_depo_row:
                raise Exception("KAB-01 deposu bulunamadı!")
            kab_depo_id = kab_depo_row[0]
            
            cursor.execute("SELECT id FROM tanim.depolar WHERE kod = 'SOKUM'")
            sokum_depo_row = cursor.fetchone()
            if not sokum_depo_row:
                raise Exception("SOKUM deposu bulunamadı!")
            sokum_depo_id = sokum_depo_row[0]
            
            # ✅ Ürün ID'sini al
            cursor.execute("""
                SELECT urun_id 
                FROM stok.stok_bakiye 
                WHERE lot_no = ? AND depo_id = ?
            """, (eski_lot_no, sokum_depo_id))
            
            urun_row = cursor.fetchone()
            if not urun_row:
                raise Exception(f"SOKUM deposunda {eski_lot_no} bulunamadı!")
            urun_id = urun_row[0]
            
            # ✅ 1. SOKUM deposundan ÇIKIŞ (eski lot)
            cikis_sonuc = motor.stok_cikis(
                lot_no=eski_lot_no,
                miktar=giris_miktar
            )
            
            if not cikis_sonuc.basarili:
                raise Exception(f"SOKUM'dan çıkış başarısız: {cikis_sonuc.mesaj}")
            
            # ✅ 2. KAB-01 deposuna GİRİŞ (yeni lot)
            giris_sonuc = motor.stok_giris(
                urun_id=urun_id,
                lot_no=yeni_lot_no,
                depo_id=kab_depo_id,
                miktar=giris_miktar
            )
            
            if not giris_sonuc.basarili:
                raise Exception(f"KAB-01'e giriş başarısız: {giris_sonuc.mesaj}")
            
            # ✅ Hareket kayıtlarını manuel ekle (motor eklemiyor gibi)
            cursor.execute("""
                INSERT INTO stok.stok_hareket (
                    urun_id, lot_no, hareket_tipi, depo_id, miktar,
                    kaynak, kaynak_id, aciklama, hareket_tarihi
                ) VALUES (?, ?, 'CIKIS', ?, ?, 'SOKUM_GIRIS', ?, ?, GETDATE())
            """, (
                urun_id, eski_lot_no, sokum_depo_id, giris_miktar,
                ie_id, f"Söküm girişi - İE: {is_emri_no}"
            ))
            
            cursor.execute("""
                INSERT INTO stok.stok_hareket (
                    urun_id, lot_no, hareket_tipi, depo_id, miktar,
                    kaynak, kaynak_id, aciklama, hareket_tarihi
                ) VALUES (?, ?, 'GIRIS', ?, ?, 'SOKUM_GIRIS', ?, ?, GETDATE())
            """, (
                urun_id, yeni_lot_no, kab_depo_id, giris_miktar,
                ie_id, f"Söküm tamamlandı - İE: {is_emri_no}"
            ))
            
            # ✅ 3. Hedef depoda durum_kodu güncelle
            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET durum_kodu = 'KABUL'
                WHERE lot_no = ? AND depo_id = ?
            """, (yeni_lot_no, kab_depo_id))
            
            # ✅ 4. Söküm girişi kaydet
            kalan_miktar = toplam_miktar - giris_miktar
            
            cursor.execute("""
                INSERT INTO uretim.sokum_giris (
                    sokum_is_emri_id, lot_no, giris_miktar, kalan_miktar,
                    kalite_durumu, sokum_suresi, hedef_depo_id,
                    durum_kodu, notlar, giris_yapan_id, giris_tarihi
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                ie_id,
                yeni_lot_no,  # ✅ Yeni lot numarası kaydedildi
                giris_miktar,
                kalan_miktar,
                self.giris_kalite_combo.currentText() or None,
                self.giris_sure_spin.value() or None,
                kab_depo_id,
                "KABUL",
                self.giris_not_edit.toPlainText().strip() or None,
                ModernLoginDialog.current_user_id or 1
            ))
            
            # ✅ 5. İş emri durumu güncelle
            if kalan_miktar > 0:
                # Kısmi giriş
                cursor.execute("""
                    UPDATE uretim.sokum_is_emirleri
                    SET miktar = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (kalan_miktar, ie_id))
                
                mesaj = f"""Kismi giris yapildi.

Giris: {giris_miktar} adet
Kalan: {kalan_miktar} adet

Eski Lot: {eski_lot_no}
Yeni Lot: {yeni_lot_no}
Hedef: KAB-01 (Kabul Alani)"""
            else:
                # Tam giriş
                cursor.execute("""
                    UPDATE uretim.sokum_is_emirleri
                    SET durum = 'TAMAMLANDI', 
                        bitis_tarihi = GETDATE(),
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (ie_id,))
                
                mesaj = f"""Is emri tamamlandi.

Giris: {giris_miktar} adet

Eski Lot: {eski_lot_no}
Yeni Lot: {yeni_lot_no}
Hedef: KAB-01 (Kabul Alani)"""
            
            conn.commit()
            LogManager.log_update('uretim', 'uretim.rework_is_emirleri', ie_id,
                                  f'Rework giris yapildi: {giris_miktar} adet, Eski Lot: {eski_lot_no}, Yeni Lot: {yeni_lot_no}')
            conn.close()

            QMessageBox.information(self, "Basarili", mesaj)
            
            # Formu temizle
            self._clear_giris_form()
            
            # Verileri yenile
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Giriş yapılamadı: {e}")
            import traceback
            traceback.print_exc()
    
    def _clear_giris_form(self):
        """Giriş formunu temizle"""
        self.giris_ie_edit.clear()
        self.giris_lot_edit.clear()
        self.giris_toplam_edit.clear()
        self.giris_miktar_spin.setValue(0)
        self.giris_kalite_combo.setCurrentIndex(0)
        self.giris_sure_spin.setValue(0)
        self.giris_not_edit.clear()
        self.giris_btn.setEnabled(False)
    
    # ========================================================
    # HELPER METHODS - STIL
    # ========================================================

    def _create_table(self, headers):
        """Tablo olustur"""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setHighlightSections(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setShowGrid(False)
        table.setFrameShape(QFrame.NoFrame)
        table.setStyleSheet(self._table_style())
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(brand.sp(38))

        return table

    def _button_style(self):
        return f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
            }}
        """

    def _cta_button_style(self, accent_color: str):
        hover = "#059669" if accent_color == brand.SUCCESS else brand.PRIMARY_HOVER
        return f"""
            QPushButton {{
                background: {accent_color};
                color: white;
                border: 1px solid {accent_color};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_3}px {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_BOLD};
                letter-spacing: 0.4px;
            }}
            QPushButton:hover {{
                background: {hover};
                border-color: {hover};
            }}
            QPushButton:disabled {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT_DISABLED};
                border-color: {brand.BORDER};
            }}
        """

    def _input_style(self):
        return f"""
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QDateEdit:hover, QSpinBox:hover {{
                border-color: {brand.BORDER_HARD};
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {{
                border-color: {brand.PRIMARY};
            }}
            QLineEdit[readOnly="true"] {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT_MUTED};
            }}
            QComboBox::drop-down, QDateEdit::drop-down {{ border: none; width: {brand.sp(22)}px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_ELEVATED};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                selection-background-color: {brand.PRIMARY};
                selection-color: white;
            }}
        """

    def _table_style(self):
        return f"""
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
            QTableWidget::item:selected {{
                background: {_soft(brand.PRIMARY, 0.18)};
                color: {brand.TEXT};
            }}
            QTableWidget::item:hover {{
                background: {brand.BG_HOVER};
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
        """

    def _get_tab_style(self):
        """Tab widget stili"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                background: {brand.BG_CARD};
                top: -1px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_5}px;
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
        """
