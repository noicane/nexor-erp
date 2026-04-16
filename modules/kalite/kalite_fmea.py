# -*- coding: utf-8 -*-
"""
NEXOR ERP - FMEA Yonetimi
=========================
Failure Mode and Effects Analysis (Hata Turu ve Etkileri Analizi)
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QGroupBox, QDateEdit,
    QSpinBox, QTextEdit, QTabWidget, QProgressBar, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush, QFont

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


def get_rpn_color(rpn):
    """RPN degerine gore renk dondur"""
    if rpn >= 200:
        return "#ef4444"  # Kirmizi - Kritik
    elif rpn >= 120:
        return "#f97316"  # Turuncu - Yuksek
    elif rpn >= 80:
        return "#eab308"  # Sari - Orta
    else:
        return "#22c55e"  # Yesil - Dusuk


# =====================================================================
# HELPER: Ortak stil parcalari
# =====================================================================

def _dialog_base_css():
    return f"""
        QDialog {{
            background: {brand.BG_MAIN};
            font-family: {brand.FONT_FAMILY};
        }}
        QLabel {{ color: {brand.TEXT}; background: transparent; }}
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
        QCheckBox {{ color: {brand.TEXT}; }}
    """


def _input_css():
    return f"""
        QLineEdit, QSpinBox, QComboBox, QDateEdit, QTextEdit {{
            background: {brand.BG_INPUT};
            color: {brand.TEXT};
            border: 1px solid {brand.BORDER};
            border-radius: {brand.R_SM}px;
            padding: {brand.SP_2}px {brand.SP_3}px;
            font-size: {brand.FS_BODY}px;
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{
            border-color: {brand.PRIMARY};
        }}
    """


def _tab_css():
    return f"""
        QTabWidget::pane {{
            border: 1px solid {brand.BORDER};
            border-radius: {brand.R_LG}px;
        }}
        QTabBar::tab {{
            background: {brand.BG_INPUT};
            color: {brand.TEXT};
            padding: {brand.SP_2}px {brand.SP_5}px;
            border-radius: {brand.R_SM}px {brand.R_SM}px 0 0;
            font-size: {brand.FS_BODY}px;
            font-weight: {brand.FW_MEDIUM};
        }}
        QTabBar::tab:selected {{
            background: {brand.PRIMARY};
            color: white;
            font-weight: {brand.FW_SEMIBOLD};
        }}
        QTabBar::tab:hover:!selected {{
            background: {brand.BG_HOVER};
        }}
    """


def _table_css():
    return f"""
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
    """


def _ghost_btn(text):
    """Ghost stil buton olustur"""
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(brand.sp(38))
    btn.setStyleSheet(f"""
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
    return btn


def _primary_btn(text):
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(brand.sp(38))
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {brand.PRIMARY};
            color: white;
            border: none;
            border-radius: {brand.R_SM}px;
            padding: 0 {brand.SP_6}px;
            font-size: {brand.FS_BODY}px;
            font-weight: {brand.FW_SEMIBOLD};
        }}
        QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
    """)
    return btn


def _success_btn(text):
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(brand.sp(38))
    btn.setStyleSheet(f"""
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
    return btn


def _danger_btn(text):
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(brand.sp(38))
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {brand.ERROR};
            color: white;
            border: none;
            border-radius: {brand.R_SM}px;
            padding: 0 {brand.SP_6}px;
            font-size: {brand.FS_BODY}px;
            font-weight: {brand.FW_SEMIBOLD};
        }}
        QPushButton:hover {{ background: #DC2626; }}
    """)
    return btn


def _dialog_header(layout, title_text, subtitle_text=""):
    """Dialog header: accent bar + title + subtitle"""
    header = QHBoxLayout()
    header.setSpacing(brand.SP_3)

    accent = QFrame()
    accent.setFixedSize(brand.SP_1, brand.sp(32))
    accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
    header.addWidget(accent)

    title_col = QVBoxLayout()
    title_col.setSpacing(brand.SP_1)
    title = QLabel(title_text)
    title.setStyleSheet(
        f"color: {brand.TEXT}; "
        f"font-size: {brand.FS_HEADING}px; "
        f"font-weight: {brand.FW_SEMIBOLD};"
    )
    title_col.addWidget(title)
    if subtitle_text:
        sub = QLabel(subtitle_text)
        sub.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        title_col.addWidget(sub)
    header.addLayout(title_col)
    header.addStretch()
    layout.addLayout(header)


# =====================================================================
# DIALOG: FMEA Satir (Hata Modu)
# =====================================================================

class FMEASatirDialog(QDialog):
    """FMEA satiri (hata modu) ekleme/duzenleme — el kitabi uyumlu"""

    def __init__(self, theme: dict, fmea_id: int, parent=None, satir_id=None):
        super().__init__(parent)
        self.theme = theme
        self.fmea_id = fmea_id
        self.satir_id = satir_id
        self.setWindowTitle("Hata Modu Ekle" if not satir_id else "Hata Modu Duzenle")
        self.setMinimumSize(brand.sp(700), brand.sp(600))
        self.setModal(True)
        self._setup_ui()

        if satir_id:
            self._load_data()

        self._calculate_rpn()

    def _setup_ui(self):
        self.setStyleSheet(_dialog_base_css() + _input_css() + _tab_css())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # -- Header --
        _dialog_header(layout, "Hata Modu" if not self.satir_id else "Hata Modu Duzenle")

        # Tab widget
        tabs = QTabWidget()

        # Tab 1: Hata Bilgileri
        tab1 = QWidget()
        tab1_layout = QFormLayout(tab1)
        tab1_layout.setSpacing(brand.SP_3)

        self.spin_sira = QSpinBox()
        self.spin_sira.setRange(1, 999)
        tab1_layout.addRow("Sira No*:", self.spin_sira)

        self.txt_proses = QLineEdit()
        self.txt_proses.setPlaceholderText("Proses adimi veya fonksiyon")
        tab1_layout.addRow("Proses/Fonksiyon*:", self.txt_proses)

        self.txt_hata_modu = QTextEdit()
        self.txt_hata_modu.setMaximumHeight(brand.sp(60))
        self.txt_hata_modu.setPlaceholderText("Potansiyel hata modu nedir?")
        tab1_layout.addRow("Hata Modu*:", self.txt_hata_modu)

        self.txt_hata_etkisi = QTextEdit()
        self.txt_hata_etkisi.setMaximumHeight(brand.sp(60))
        self.txt_hata_etkisi.setPlaceholderText("Hatanin musteri/surec uzerindeki etkisi")
        tab1_layout.addRow("Hata Etkisi:", self.txt_hata_etkisi)

        self.txt_hata_nedeni = QTextEdit()
        self.txt_hata_nedeni.setMaximumHeight(brand.sp(60))
        self.txt_hata_nedeni.setPlaceholderText("Hatanin potansiyel nedeni")
        tab1_layout.addRow("Hata Nedeni:", self.txt_hata_nedeni)

        tabs.addTab(tab1, "Hata Bilgileri")

        # Tab 2: RPN Degerlendirmesi
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.setSpacing(brand.SP_4)

        # Mevcut RPN
        rpn_group = QGroupBox("RPN Degerlendirmesi (1-10)")
        rpn_layout = QHBoxLayout(rpn_group)
        rpn_layout.setSpacing(brand.SP_4)

        # Siddet
        siddet_layout = QVBoxLayout()
        lbl_s = QLabel("Siddet (S)")
        lbl_s.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; font-weight: {brand.FW_SEMIBOLD};")
        siddet_layout.addWidget(lbl_s)
        self.spin_siddet = QSpinBox()
        self.spin_siddet.setRange(1, 10)
        self.spin_siddet.setValue(5)
        self.spin_siddet.valueChanged.connect(self._calculate_rpn)
        siddet_layout.addWidget(self.spin_siddet)
        rpn_layout.addLayout(siddet_layout)

        lbl_x1 = QLabel("x")
        lbl_x1.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_HEADING}px;")
        lbl_x1.setAlignment(Qt.AlignCenter)
        rpn_layout.addWidget(lbl_x1)

        # Olasilik
        olasilik_layout = QVBoxLayout()
        lbl_o = QLabel("Olasilik (O)")
        lbl_o.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; font-weight: {brand.FW_SEMIBOLD};")
        olasilik_layout.addWidget(lbl_o)
        self.spin_olasilik = QSpinBox()
        self.spin_olasilik.setRange(1, 10)
        self.spin_olasilik.setValue(5)
        self.spin_olasilik.valueChanged.connect(self._calculate_rpn)
        olasilik_layout.addWidget(self.spin_olasilik)
        rpn_layout.addLayout(olasilik_layout)

        lbl_x2 = QLabel("x")
        lbl_x2.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_HEADING}px;")
        lbl_x2.setAlignment(Qt.AlignCenter)
        rpn_layout.addWidget(lbl_x2)

        # Tespit
        tespit_layout = QVBoxLayout()
        lbl_d = QLabel("Tespit (D)")
        lbl_d.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; font-weight: {brand.FW_SEMIBOLD};")
        tespit_layout.addWidget(lbl_d)
        self.spin_tespit = QSpinBox()
        self.spin_tespit.setRange(1, 10)
        self.spin_tespit.setValue(5)
        self.spin_tespit.valueChanged.connect(self._calculate_rpn)
        tespit_layout.addWidget(self.spin_tespit)
        rpn_layout.addLayout(tespit_layout)

        lbl_eq = QLabel("=")
        lbl_eq.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_HEADING}px;")
        lbl_eq.setAlignment(Qt.AlignCenter)
        rpn_layout.addWidget(lbl_eq)

        # RPN sonuc
        rpn_result_layout = QVBoxLayout()
        lbl_rpn_title = QLabel("RPN")
        lbl_rpn_title.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; font-weight: {brand.FW_SEMIBOLD};")
        rpn_result_layout.addWidget(lbl_rpn_title)
        self.lbl_rpn = QLabel("125")
        self.lbl_rpn.setStyleSheet(
            f"font-size: {brand.FS_TITLE}px; font-weight: {brand.FW_BOLD}; "
            f"padding: {brand.SP_2}px;"
        )
        rpn_result_layout.addWidget(self.lbl_rpn)
        rpn_layout.addLayout(rpn_result_layout)

        tab2_layout.addWidget(rpn_group)

        # Mevcut kontroller
        kontrol_group = QGroupBox("Mevcut Kontroller")
        kontrol_layout = QFormLayout(kontrol_group)
        kontrol_layout.setSpacing(brand.SP_3)

        self.txt_onleme = QTextEdit()
        self.txt_onleme.setMaximumHeight(brand.sp(50))
        self.txt_onleme.setPlaceholderText("Mevcut onleme kontrolu")
        kontrol_layout.addRow("Onleme:", self.txt_onleme)

        self.txt_tespit_kontrol = QTextEdit()
        self.txt_tespit_kontrol.setMaximumHeight(brand.sp(50))
        self.txt_tespit_kontrol.setPlaceholderText("Mevcut tespit kontrolu")
        kontrol_layout.addRow("Tespit:", self.txt_tespit_kontrol)

        tab2_layout.addWidget(kontrol_group)
        tab2_layout.addStretch()

        tabs.addTab(tab2, "RPN Degerlendirmesi")

        # Tab 3: Aksiyonlar
        tab3 = QWidget()
        tab3_layout = QFormLayout(tab3)
        tab3_layout.setSpacing(brand.SP_3)

        self.txt_aksiyon = QTextEdit()
        self.txt_aksiyon.setMaximumHeight(brand.sp(80))
        self.txt_aksiyon.setPlaceholderText("Onerilen duzeltici/onleyici aksiyon")
        tab3_layout.addRow("Onerilen Aksiyon:", self.txt_aksiyon)

        self.cmb_sorumlu = QComboBox()
        self.cmb_sorumlu.addItem("-- Seciniz --", None)
        self._load_personeller()
        tab3_layout.addRow("Sorumlu:", self.cmb_sorumlu)

        self.date_hedef = QDateEdit()
        self.date_hedef.setDate(QDate.currentDate().addMonths(1))
        self.date_hedef.setCalendarPopup(True)
        tab3_layout.addRow("Hedef Tarih:", self.date_hedef)

        # Aksiyon sonrasi RPN
        yeni_rpn_group = QGroupBox("Aksiyon Sonrasi Beklenen RPN")
        yeni_rpn_layout = QHBoxLayout(yeni_rpn_group)
        yeni_rpn_layout.setSpacing(brand.SP_3)

        self.spin_yeni_siddet = QSpinBox()
        self.spin_yeni_siddet.setRange(1, 10)
        self.spin_yeni_siddet.valueChanged.connect(self._calculate_yeni_rpn)
        lbl_ys = QLabel("S:")
        lbl_ys.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD};")
        yeni_rpn_layout.addWidget(lbl_ys)
        yeni_rpn_layout.addWidget(self.spin_yeni_siddet)

        self.spin_yeni_olasilik = QSpinBox()
        self.spin_yeni_olasilik.setRange(1, 10)
        self.spin_yeni_olasilik.valueChanged.connect(self._calculate_yeni_rpn)
        lbl_yo = QLabel("O:")
        lbl_yo.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD};")
        yeni_rpn_layout.addWidget(lbl_yo)
        yeni_rpn_layout.addWidget(self.spin_yeni_olasilik)

        self.spin_yeni_tespit = QSpinBox()
        self.spin_yeni_tespit.setRange(1, 10)
        self.spin_yeni_tespit.valueChanged.connect(self._calculate_yeni_rpn)
        lbl_yd = QLabel("D:")
        lbl_yd.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD};")
        yeni_rpn_layout.addWidget(lbl_yd)
        yeni_rpn_layout.addWidget(self.spin_yeni_tespit)

        self.lbl_yeni_rpn = QLabel("= 0")
        self.lbl_yeni_rpn.setStyleSheet(
            f"font-weight: {brand.FW_BOLD}; font-size: {brand.FS_BODY_LG}px;"
        )
        yeni_rpn_layout.addWidget(self.lbl_yeni_rpn)

        tab3_layout.addRow(yeni_rpn_group)

        # Siniflandirma
        sinif_layout = QHBoxLayout()
        self.chk_ozel = QCheckBox("Ozel Karakteristik")
        self.chk_ozel.setStyleSheet(f"""
            QCheckBox {{
                color: {brand.TEXT};
                spacing: {brand.SP_2}px;
                font-size: {brand.FS_BODY}px;
                padding: {brand.SP_1}px 0;
            }}
            QCheckBox::indicator {{
                width: {brand.sp(18)}px; height: {brand.sp(18)}px;
                border: 2px solid {brand.BORDER};
                border-radius: {brand.SP_1}px;
                background: {brand.BG_INPUT};
            }}
            QCheckBox::indicator:checked {{
                background: {brand.SUCCESS};
                border-color: {brand.SUCCESS};
            }}
        """)
        sinif_layout.addWidget(self.chk_ozel)

        self.cmb_sinif = QComboBox()
        self.cmb_sinif.addItems(["", "CC", "SC", "HI", "SI"])
        lbl_sinif = QLabel("Sinif:")
        lbl_sinif.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD};")
        sinif_layout.addWidget(lbl_sinif)
        sinif_layout.addWidget(self.cmb_sinif)
        sinif_layout.addStretch()
        tab3_layout.addRow("", sinif_layout)

        tabs.addTab(tab3, "Aksiyonlar")

        layout.addWidget(tabs, 1)

        # -- Alt butonlar --
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        btn_iptal = _ghost_btn("Iptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)

        btn_kaydet = _success_btn("Kaydet")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)

        layout.addLayout(btn_layout)

    def _load_personeller(self):
        """Personel listesini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_sorumlu.addItem(f"{row[1]} - {row[2]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _calculate_rpn(self):
        """RPN hesapla ve goster"""
        rpn = self.spin_siddet.value() * self.spin_olasilik.value() * self.spin_tespit.value()
        self.lbl_rpn.setText(str(rpn))
        self.lbl_rpn.setStyleSheet(
            f"font-size: {brand.FS_TITLE}px; font-weight: {brand.FW_BOLD}; "
            f"padding: {brand.SP_2}px; color: {get_rpn_color(rpn)};"
        )

    def _calculate_yeni_rpn(self):
        """Yeni RPN hesapla"""
        s = self.spin_yeni_siddet.value()
        o = self.spin_yeni_olasilik.value()
        d = self.spin_yeni_tespit.value()
        if s and o and d:
            rpn = s * o * d
            self.lbl_yeni_rpn.setText(f"= {rpn}")
            self.lbl_yeni_rpn.setStyleSheet(
                f"font-weight: {brand.FW_BOLD}; font-size: {brand.FS_BODY_LG}px; "
                f"color: {get_rpn_color(rpn)};"
            )
        else:
            self.lbl_yeni_rpn.setText("= 0")
            self.lbl_yeni_rpn.setStyleSheet(
                f"font-weight: {brand.FW_BOLD}; font-size: {brand.FS_BODY_LG}px;"
            )

    def _load_data(self):
        """Mevcut satir verilerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sira_no, proses_adimi, potansiyel_hata_modu, potansiyel_hata_etkisi,
                       potansiyel_hata_nedeni, siddet, olasilik, tespit,
                       mevcut_onleme_kontrolu, mevcut_tespit_kontrolu,
                       onerilen_aksiyon, aksiyon_sorumlu_id, aksiyon_hedef_tarih,
                       yeni_siddet, yeni_olasilik, yeni_tespit,
                       ozel_karakteristik, sinif
                FROM kalite.fmea_satirlar WHERE id = ?
            """, (self.satir_id,))
            row = cursor.fetchone()

            if row:
                self.spin_sira.setValue(row[0] or 1)
                self.txt_proses.setText(row[1] or "")
                self.txt_hata_modu.setPlainText(row[2] or "")
                self.txt_hata_etkisi.setPlainText(row[3] or "")
                self.txt_hata_nedeni.setPlainText(row[4] or "")
                self.spin_siddet.setValue(row[5] or 1)
                self.spin_olasilik.setValue(row[6] or 1)
                self.spin_tespit.setValue(row[7] or 1)
                self.txt_onleme.setPlainText(row[8] or "")
                self.txt_tespit_kontrol.setPlainText(row[9] or "")
                self.txt_aksiyon.setPlainText(row[10] or "")

                if row[11]:
                    idx = self.cmb_sorumlu.findData(row[11])
                    if idx >= 0: self.cmb_sorumlu.setCurrentIndex(idx)

                if row[12]:
                    self.date_hedef.setDate(QDate(row[12].year, row[12].month, row[12].day))

                self.spin_yeni_siddet.setValue(row[13] or 0)
                self.spin_yeni_olasilik.setValue(row[14] or 0)
                self.spin_yeni_tespit.setValue(row[15] or 0)
                self.chk_ozel.setChecked(row[16] or False)

                if row[17]:
                    idx = self.cmb_sinif.findText(row[17])
                    if idx >= 0: self.cmb_sinif.setCurrentIndex(idx)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yuklenirken hata: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _save(self):
        """Satiri kaydet"""
        proses = self.txt_proses.text().strip()
        hata_modu = self.txt_hata_modu.toPlainText().strip()

        if not proses or not hata_modu:
            QMessageBox.warning(self, "Uyari", "Proses ve Hata Modu zorunludur!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            yeni_s = self.spin_yeni_siddet.value() if self.spin_yeni_siddet.value() > 0 else None
            yeni_o = self.spin_yeni_olasilik.value() if self.spin_yeni_olasilik.value() > 0 else None
            yeni_d = self.spin_yeni_tespit.value() if self.spin_yeni_tespit.value() > 0 else None

            if self.satir_id:
                cursor.execute("""
                    UPDATE kalite.fmea_satirlar SET
                        sira_no = ?, proses_adimi = ?, potansiyel_hata_modu = ?,
                        potansiyel_hata_etkisi = ?, potansiyel_hata_nedeni = ?,
                        siddet = ?, olasilik = ?, tespit = ?,
                        mevcut_onleme_kontrolu = ?, mevcut_tespit_kontrolu = ?,
                        onerilen_aksiyon = ?, aksiyon_sorumlu_id = ?, aksiyon_hedef_tarih = ?,
                        yeni_siddet = ?, yeni_olasilik = ?, yeni_tespit = ?,
                        ozel_karakteristik = ?, sinif = ?
                    WHERE id = ?
                """, (
                    self.spin_sira.value(), proses, hata_modu,
                    self.txt_hata_etkisi.toPlainText().strip() or None,
                    self.txt_hata_nedeni.toPlainText().strip() or None,
                    self.spin_siddet.value(), self.spin_olasilik.value(), self.spin_tespit.value(),
                    self.txt_onleme.toPlainText().strip() or None,
                    self.txt_tespit_kontrol.toPlainText().strip() or None,
                    self.txt_aksiyon.toPlainText().strip() or None,
                    self.cmb_sorumlu.currentData(),
                    self.date_hedef.date().toPython() if self.txt_aksiyon.toPlainText().strip() else None,
                    yeni_s, yeni_o, yeni_d,
                    self.chk_ozel.isChecked(),
                    self.cmb_sinif.currentText() or None,
                    self.satir_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO kalite.fmea_satirlar
                    (fmea_id, sira_no, proses_adimi, potansiyel_hata_modu,
                     potansiyel_hata_etkisi, potansiyel_hata_nedeni,
                     siddet, olasilik, tespit,
                     mevcut_onleme_kontrolu, mevcut_tespit_kontrolu,
                     onerilen_aksiyon, aksiyon_sorumlu_id, aksiyon_hedef_tarih,
                     yeni_siddet, yeni_olasilik, yeni_tespit,
                     ozel_karakteristik, sinif)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.fmea_id, self.spin_sira.value(), proses, hata_modu,
                    self.txt_hata_etkisi.toPlainText().strip() or None,
                    self.txt_hata_nedeni.toPlainText().strip() or None,
                    self.spin_siddet.value(), self.spin_olasilik.value(), self.spin_tespit.value(),
                    self.txt_onleme.toPlainText().strip() or None,
                    self.txt_tespit_kontrol.toPlainText().strip() or None,
                    self.txt_aksiyon.toPlainText().strip() or None,
                    self.cmb_sorumlu.currentData(),
                    self.date_hedef.date().toPython() if self.txt_aksiyon.toPlainText().strip() else None,
                    yeni_s, yeni_o, yeni_d,
                    self.chk_ozel.isChecked(),
                    self.cmb_sinif.currentText() or None
                ))

            conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatasi: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# =====================================================================
# DIALOG: FMEA Ana Dialog
# =====================================================================

class FMEADialog(QDialog):
    """FMEA ekleme/duzenleme ana dialog — el kitabi uyumlu"""

    def __init__(self, theme: dict, parent=None, fmea_id=None):
        super().__init__(parent)
        self.theme = theme
        self.fmea_id = fmea_id
        self.setWindowTitle("FMEA Olustur" if not fmea_id else "FMEA Duzenle")
        self.setMinimumSize(brand.sp(1000), brand.sp(700))
        self.setModal(True)
        self._setup_ui()
        self._load_combos()

        if fmea_id:
            self._load_data()
            self._load_satirlar()

    def _setup_ui(self):
        self.setStyleSheet(_dialog_base_css() + _input_css() + _tab_css())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # -- Header --
        _dialog_header(layout, "FMEA Olustur" if not self.fmea_id else "FMEA Duzenle")

        tabs = QTabWidget()

        # Tab 1: Genel Bilgiler
        tab_genel = QWidget()
        genel_layout = QFormLayout(tab_genel)
        genel_layout.setSpacing(brand.SP_3)

        self.txt_fmea_no = QLineEdit()
        self.txt_fmea_no.setPlaceholderText("Orn: FMEA-2024-001")
        genel_layout.addRow("FMEA No*:", self.txt_fmea_no)

        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["PROSES", "TASARIM", "SISTEM"])
        genel_layout.addRow("FMEA Tipi:", self.cmb_tip)

        self.spin_revizyon = QSpinBox()
        self.spin_revizyon.setRange(1, 99)
        genel_layout.addRow("Revizyon:", self.spin_revizyon)

        self.txt_baslik = QLineEdit()
        self.txt_baslik.setPlaceholderText("FMEA basligi")
        genel_layout.addRow("Baslik*:", self.txt_baslik)

        self.cmb_musteri = QComboBox()
        genel_layout.addRow("Musteri:", self.cmb_musteri)

        self.cmb_urun = QComboBox()
        genel_layout.addRow("Urun:", self.cmb_urun)

        self.cmb_hazirlayan = QComboBox()
        genel_layout.addRow("Hazirlayan:", self.cmb_hazirlayan)

        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["TASLAK", "ONAY_BEKLIYOR", "ONAYLANDI", "IPTAL"])
        genel_layout.addRow("Durum:", self.cmb_durum)

        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(brand.sp(80))
        genel_layout.addRow("Aciklama:", self.txt_aciklama)

        tabs.addTab(tab_genel, "Genel Bilgiler")

        # Tab 2: Hata Modlari
        tab_satirlar = QWidget()
        satirlar_layout = QVBoxLayout(tab_satirlar)
        satirlar_layout.setSpacing(brand.SP_4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)

        btn_ekle = _success_btn("Hata Modu Ekle")
        btn_ekle.clicked.connect(self._add_satir)
        toolbar.addWidget(btn_ekle)

        btn_duzenle = _ghost_btn("Duzenle")
        btn_duzenle.clicked.connect(self._edit_satir)
        toolbar.addWidget(btn_duzenle)

        btn_sil = _danger_btn("Sil")
        btn_sil.clicked.connect(self._delete_satir)
        toolbar.addWidget(btn_sil)

        toolbar.addStretch()

        # RPN ozeti
        self.lbl_rpn_ozet = QLabel("Toplam: 0 | Kritik (>=200): 0 | Yuksek (>=120): 0")
        self.lbl_rpn_ozet.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;"
        )
        toolbar.addWidget(self.lbl_rpn_ozet)

        satirlar_layout.addLayout(toolbar)

        # Tablo
        self.table_satirlar = QTableWidget()
        self.table_satirlar.setColumnCount(10)
        self.table_satirlar.setHorizontalHeaderLabels([
            "ID", "Sira", "Proses", "Hata Modu", "S", "O", "D", "RPN", "Aksiyon", "Yeni RPN"
        ])
        self.table_satirlar.setColumnHidden(0, True)
        self.table_satirlar.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_satirlar.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_satirlar.verticalHeader().setVisible(False)
        self.table_satirlar.setShowGrid(False)
        self.table_satirlar.setAlternatingRowColors(True)
        self.table_satirlar.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table_satirlar.setStyleSheet(_table_css())

        header = self.table_satirlar.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(8, QHeaderView.Stretch)
        self.table_satirlar.setColumnWidth(1, brand.sp(60))
        self.table_satirlar.setColumnWidth(2, brand.sp(120))
        self.table_satirlar.setColumnWidth(4, brand.sp(60))
        self.table_satirlar.setColumnWidth(5, brand.sp(60))
        self.table_satirlar.setColumnWidth(6, brand.sp(60))
        self.table_satirlar.setColumnWidth(7, brand.sp(60))
        self.table_satirlar.setColumnWidth(9, brand.sp(70))

        self.table_satirlar.doubleClicked.connect(self._edit_satir)
        satirlar_layout.addWidget(self.table_satirlar)

        tabs.addTab(tab_satirlar, "Hata Modlari")

        layout.addWidget(tabs, 1)

        # -- Alt butonlar --
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        btn_iptal = _ghost_btn("Iptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)

        btn_kaydet = _success_btn("Kaydet")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)

        layout.addLayout(btn_layout)

    def _load_combos(self):
        """Combo listelerini doldur"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            self.cmb_musteri.addItem("-- Musteri Seciniz --", None)
            cursor.execute("""
                SELECT DISTINCT c.id, c.unvan
                FROM musteri.cariler c
                INNER JOIN stok.urunler u ON c.id = u.cari_id
                WHERE c.unvan IS NOT NULL AND c.unvan <> '' AND c.aktif_mi = 1 AND u.aktif_mi = 1
                ORDER BY c.unvan
            """)
            for row in cursor.fetchall():
                self.cmb_musteri.addItem(row[1], row[0])

            self.cmb_musteri.currentIndexChanged.connect(self._on_musteri_changed)

            self.cmb_urun.addItem("-- Once Musteri Secin --", None)

            self.cmb_hazirlayan.addItem("-- Seciniz --", None)
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_hazirlayan.addItem(row[1], row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _on_musteri_changed(self):
        """Musteri degistiginde urunleri guncelle"""
        cari_id = self.cmb_musteri.currentData()
        self._load_urunler(cari_id)

    def _load_urunler(self, cari_id=None):
        """Secilen musteriye ait urun listesi"""
        self.cmb_urun.clear()
        self.cmb_urun.addItem("-- Urun Secin --", None)
        if not cari_id:
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.urun_kodu + ' - ' + u.urun_adi
                FROM stok.urunler u
                WHERE u.cari_id = ? AND u.aktif_mi = 1
                ORDER BY u.urun_kodu
            """, (cari_id,))
            for row in cursor.fetchall():
                if row[0]:
                    self.cmb_urun.addItem(row[1], row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_data(self):
        """FMEA verilerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.fmea_no, f.fmea_tipi, f.revizyon, f.baslik, f.urun_id, f.cari_id,
                       f.hazirlayan_id, f.durum, f.aciklama, c.unvan
                FROM kalite.fmea f
                LEFT JOIN musteri.cariler c ON f.cari_id = c.id
                WHERE f.id = ?
            """, (self.fmea_id,))
            row = cursor.fetchone()

            if row:
                self.txt_fmea_no.setText(row[0] or "")
                self.txt_fmea_no.setEnabled(False)

                idx = self.cmb_tip.findText(row[1] or "PROSES")
                if idx >= 0: self.cmb_tip.setCurrentIndex(idx)

                self.spin_revizyon.setValue(row[2] or 1)
                self.txt_baslik.setText(row[3] or "")

                cari_unvani = row[9]
                if cari_unvani:
                    idx = self.cmb_musteri.findData(cari_unvani)
                    if idx >= 0:
                        self.cmb_musteri.setCurrentIndex(idx)
                        self._load_urunler(cari_unvani)

                if row[4]:
                    idx = self.cmb_urun.findData(row[4])
                    if idx >= 0: self.cmb_urun.setCurrentIndex(idx)

                if row[6]:
                    idx = self.cmb_hazirlayan.findData(row[6])
                    if idx >= 0: self.cmb_hazirlayan.setCurrentIndex(idx)

                if row[7]:
                    idx = self.cmb_durum.findText(row[7])
                    if idx >= 0: self.cmb_durum.setCurrentIndex(idx)

                self.txt_aciklama.setPlainText(row[8] or "")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yuklenirken hata: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_satirlar(self):
        """Hata modlarini yukle"""
        if not self.fmea_id:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sira_no, proses_adimi, potansiyel_hata_modu,
                       siddet, olasilik, tespit,
                       onerilen_aksiyon, yeni_siddet, yeni_olasilik, yeni_tespit
                FROM kalite.fmea_satirlar
                WHERE fmea_id = ? AND aktif_mi = 1
                ORDER BY sira_no
            """, (self.fmea_id,))
            rows = cursor.fetchall()

            self.table_satirlar.setRowCount(len(rows))
            kritik = 0
            yuksek = 0

            for i, row in enumerate(rows):
                self.table_satirlar.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_satirlar.setItem(i, 1, QTableWidgetItem(str(row[1])))
                self.table_satirlar.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.table_satirlar.setItem(i, 3, QTableWidgetItem(row[3][:50] + "..." if len(row[3] or "") > 50 else row[3] or ""))
                self.table_satirlar.setItem(i, 4, QTableWidgetItem(str(row[4])))
                self.table_satirlar.setItem(i, 5, QTableWidgetItem(str(row[5])))
                self.table_satirlar.setItem(i, 6, QTableWidgetItem(str(row[6])))

                rpn = row[4] * row[5] * row[6]
                rpn_item = QTableWidgetItem(str(rpn))
                rpn_item.setForeground(QColor(get_rpn_color(rpn)))
                rpn_item.setData(Qt.FontRole, QFont("", -1, QFont.Bold))
                self.table_satirlar.setItem(i, 7, rpn_item)

                if rpn >= 200: kritik += 1
                elif rpn >= 120: yuksek += 1

                self.table_satirlar.setItem(i, 8, QTableWidgetItem(row[7][:30] + "..." if row[7] and len(row[7]) > 30 else row[7] or "-"))

                # Yeni RPN
                if row[8] and row[9] and row[10]:
                    yeni_rpn = row[8] * row[9] * row[10]
                    yeni_rpn_item = QTableWidgetItem(str(yeni_rpn))
                    yeni_rpn_item.setForeground(QColor(get_rpn_color(yeni_rpn)))
                    self.table_satirlar.setItem(i, 9, yeni_rpn_item)
                else:
                    self.table_satirlar.setItem(i, 9, QTableWidgetItem("-"))

            self.lbl_rpn_ozet.setText(f"Toplam: {len(rows)} | Kritik (>=200): {kritik} | Yuksek (>=120): {yuksek}")

        except Exception as e:
            print(f"Satir yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _add_satir(self):
        if not self.fmea_id:
            QMessageBox.warning(self, "Uyari", "Once FMEA'yi kaydedin!")
            return
        dialog = FMEASatirDialog(self.theme, self.fmea_id, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()

    def _edit_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir satir secin!")
            return
        satir_id = int(self.table_satirlar.item(row, 0).text())
        dialog = FMEASatirDialog(self.theme, self.fmea_id, self, satir_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()

    def _delete_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir satir secin!")
            return

        satir_id = int(self.table_satirlar.item(row, 0).text())
        reply = QMessageBox.question(self, "Onay", "Bu hata modunu silmek istediginize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE kalite.fmea_satirlar SET aktif_mi = 0 WHERE id = ?", (satir_id,))
                conn.commit()
                self._load_satirlar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatasi: {str(e)}")
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    def _save(self):
        fmea_no = self.txt_fmea_no.text().strip()
        baslik = self.txt_baslik.text().strip()

        if not fmea_no or not baslik:
            QMessageBox.warning(self, "Uyari", "FMEA No ve Baslik zorunludur!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # cari_unvani'den cari_id bul
            cari_unvani = self.cmb_musteri.currentData()
            cari_id = None
            if cari_unvani:
                cursor.execute("""
                    SELECT TOP 1 id FROM musteri.cariler
                    WHERE unvan = ? AND aktif_mi = 1 AND silindi_mi = 0
                """, (cari_unvani,))
                row = cursor.fetchone()
                if row:
                    cari_id = row[0]

            if self.fmea_id:
                cursor.execute("""
                    UPDATE kalite.fmea SET
                        fmea_tipi = ?, revizyon = ?, baslik = ?, urun_id = ?,
                        cari_id = ?, hazirlayan_id = ?, durum = ?, aciklama = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    self.cmb_tip.currentText(), self.spin_revizyon.value(), baslik,
                    self.cmb_urun.currentData(), cari_id,
                    self.cmb_hazirlayan.currentData(), self.cmb_durum.currentText(),
                    self.txt_aciklama.toPlainText().strip() or None,
                    self.fmea_id
                ))
            else:
                cursor.execute("SELECT COUNT(*) FROM kalite.fmea WHERE fmea_no = ?", (fmea_no,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyari", "Bu FMEA No zaten kullaniliyor!")
                    return

                cursor.execute("""
                    INSERT INTO kalite.fmea
                    (fmea_no, fmea_tipi, revizyon, baslik, urun_id, cari_id,
                     hazirlayan_id, durum, aciklama)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fmea_no, self.cmb_tip.currentText(), self.spin_revizyon.value(), baslik,
                    self.cmb_urun.currentData(), cari_id,
                    self.cmb_hazirlayan.currentData(), self.cmb_durum.currentText(),
                    self.txt_aciklama.toPlainText().strip() or None
                ))
                self.fmea_id = cursor.fetchone()[0]

            conn.commit()
            QMessageBox.information(self, "Basarili", "FMEA kaydedildi!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatasi: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# =====================================================================
# ANA SAYFA
# =====================================================================

class FMEAYonetimiPage(BasePage):
    """FMEA Yonetimi Ana Sayfasi — el kitabi uyumlu"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # -- 1. Header --
        header = self.create_page_header(
            "FMEA Yonetimi",
            "Hata Turu ve Etkileri Analizi"
        )
        layout.addLayout(header)

        # -- 2. KPI cards --
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self._kpi_toplam = self.create_stat_card("TOPLAM FMEA", "0", color=brand.INFO)
        kpi_row.addWidget(self._kpi_toplam)

        self._kpi_taslak = self.create_stat_card("TASLAK", "0", color=brand.WARNING)
        kpi_row.addWidget(self._kpi_taslak)

        self._kpi_onaylandi = self.create_stat_card("ONAYLANDI", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self._kpi_onaylandi)

        self._kpi_kritik = self.create_stat_card("KRITIK RPN", "0", color=brand.ERROR)
        kpi_row.addWidget(self._kpi_kritik)

        kpi_row.addStretch()
        layout.addLayout(kpi_row)

        # -- 3. Toolbar --
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)
        toolbar_layout.setSpacing(brand.SP_3)

        btn_yeni = _success_btn("Yeni FMEA")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)

        btn_duzenle = _ghost_btn("Duzenle")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar_layout.addWidget(btn_duzenle)

        btn_sil = _danger_btn("Sil")
        btn_sil.clicked.connect(self._sil)
        toolbar_layout.addWidget(btn_sil)

        toolbar_layout.addStretch()

        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["Tum Tipler", "PROSES", "TASARIM", "SISTEM"])
        self.cmb_tip.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.cmb_tip.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_tip)

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)

        layout.addWidget(toolbar_frame)

        # -- 4. Tablo --
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "FMEA No", "Tip", "Baslik", "Urun", "Satir", "Max RPN", "Durum"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setStyleSheet(_table_css())

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(1, brand.sp(120))
        self.table.setColumnWidth(2, brand.sp(80))
        self.table.setColumnWidth(5, brand.sp(60))
        self.table.setColumnWidth(6, brand.sp(80))
        self.table.setColumnWidth(7, brand.sp(100))

        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table, 1)

        # -- 5. Status bar --
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;"
        )
        layout.addWidget(self.lbl_stat)

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    f.id, f.fmea_no, f.fmea_tipi, f.baslik,
                    u.urun_kodu,
                    (SELECT COUNT(*) FROM kalite.fmea_satirlar WHERE fmea_id = f.id AND aktif_mi = 1),
                    (SELECT MAX(siddet * olasilik * tespit) FROM kalite.fmea_satirlar WHERE fmea_id = f.id AND aktif_mi = 1),
                    f.durum
                FROM kalite.fmea f
                LEFT JOIN stok.urunler u ON f.urun_id = u.id
                WHERE f.aktif_mi = 1
                ORDER BY f.olusturma_tarihi DESC
            """)
            self.all_rows = cursor.fetchall()

            # KPI guncelle
            toplam = len(self.all_rows)
            taslak = sum(1 for r in self.all_rows if r[7] == 'TASLAK')
            onaylandi = sum(1 for r in self.all_rows if r[7] == 'ONAYLANDI')
            kritik = sum(1 for r in self.all_rows if r[6] and r[6] >= 200)

            self._kpi_toplam.findChild(QLabel, "stat_value").setText(str(toplam))
            self._kpi_taslak.findChild(QLabel, "stat_value").setText(str(taslak))
            self._kpi_onaylandi.findChild(QLabel, "stat_value").setText(str(onaylandi))
            self._kpi_kritik.findChild(QLabel, "stat_value").setText(str(kritik))

            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yuklenirken hata: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _display_data(self, rows):
        self.table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 6 and val:  # Max RPN
                    item = QTableWidgetItem(str(val))
                    item.setForeground(QColor(get_rpn_color(val)))
                    item.setData(Qt.FontRole, QFont("", -1, QFont.Bold))
                elif j == 7:  # Durum
                    item = QTableWidgetItem(str(val) if val else "")
                    colors = {'TASLAK': brand.WARNING, 'ONAYLANDI': brand.SUCCESS, 'IPTAL': brand.ERROR}
                    item.setForeground(QColor(colors.get(val, brand.TEXT)))
                else:
                    item = QTableWidgetItem(str(val) if val else "-")
                self.table.setItem(i, j, item)

        self.lbl_stat.setText(f"Toplam: {len(rows)} FMEA")

    def _filter(self):
        tip = self.cmb_tip.currentText()
        if tip == "Tum Tipler":
            self._display_data(self.all_rows)
        else:
            filtered = [r for r in self.all_rows if r[2] == tip]
            self._display_data(filtered)

    def _yeni(self):
        dialog = FMEADialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir FMEA secin!")
            return
        fmea_id = int(self.table.item(row, 0).text())
        dialog = FMEADialog(self.theme, self, fmea_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _sil(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir FMEA secin!")
            return

        fmea_id = int(self.table.item(row, 0).text())
        fmea_no = self.table.item(row, 1).text()

        reply = QMessageBox.question(self, "Onay", f"'{fmea_no}' FMEA'yi silmek istediginize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE kalite.fmea SET aktif_mi = 0 WHERE id = ?", (fmea_id,))
                conn.commit()
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatasi: {str(e)}")
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
