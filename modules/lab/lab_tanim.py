# -*- coding: utf-8 -*-
"""
NEXOR ERP - Laboratuvar Tanimlari
Banyo Tipleri ve Pozisyon Tipleri yonetimi
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QSpinBox, QTextEdit, QComboBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QTimer

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


# =====================================================================
# DIALOG: Banyo Tipi
# =====================================================================

class BanyoTipiDialog(QDialog):
    """Banyo Tipi Ekleme/Duzenleme — el kitabi uyumlu"""

    def __init__(self, theme: dict, tip_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.tip_id = tip_id
        self.data = {}

        self.setWindowTitle("Yeni Banyo Tipi" if not tip_id else "Banyo Tipi Duzenle")
        self.setMinimumSize(brand.sp(400), brand.sp(400))

        if tip_id:
            self._load_data()
        self._setup_ui()

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.banyo_tipleri WHERE id = ?", (self.tip_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {brand.PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_4)

        # ── Header ──
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)
        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        form = QFormLayout()
        form.setSpacing(brand.SP_3)

        self.kod_input = QLineEdit(self.data.get('kod', ''))
        self.kod_input.setPlaceholderText("Orn: KATAFOREZ, ALKALI_ZN")
        form.addRow("Kod *:", self.kod_input)

        self.ad_input = QLineEdit(self.data.get('ad', ''))
        self.ad_input.setPlaceholderText("Orn: Kataforez Banyosu")
        form.addRow("Ad *:", self.ad_input)

        self.kategori_combo = QComboBox()
        self.kategori_combo.addItem("On Islem", "ON_ISLEM")
        self.kategori_combo.addItem("Kaplama", "KAPLAMA")
        self.kategori_combo.addItem("Son Islem", "SON_ISLEM")
        self.kategori_combo.addItem("Yikama", "YIKAMA")
        self.kategori_combo.addItem("Diger", "DIGER")
        if self.data.get('kategori'):
            idx = self.kategori_combo.findData(self.data['kategori'])
            if idx >= 0:
                self.kategori_combo.setCurrentIndex(idx)
        form.addRow("Kategori *:", self.kategori_combo)

        # Gereklilik bayraklari
        gerekli_label = QLabel("-- Gereklilik Ayarlari --")
        gerekli_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; margin-top: {brand.SP_2}px;"
        )
        form.addRow("", gerekli_label)

        self.kimyasal_check = QComboBox()
        self.kimyasal_check.addItem("Evet", True)
        self.kimyasal_check.addItem("Hayir", False)
        self.kimyasal_check.setCurrentIndex(0 if self.data.get('kimyasal_gerekli_mi', True) else 1)
        form.addRow("Kimyasal Gerekli:", self.kimyasal_check)

        self.sicaklik_check = QComboBox()
        self.sicaklik_check.addItem("Evet", True)
        self.sicaklik_check.addItem("Hayir", False)
        self.sicaklik_check.setCurrentIndex(0 if self.data.get('sicaklik_gerekli_mi', True) else 1)
        form.addRow("Sicaklik Gerekli:", self.sicaklik_check)

        self.ph_check = QComboBox()
        self.ph_check.addItem("Evet", True)
        self.ph_check.addItem("Hayir", False)
        self.ph_check.setCurrentIndex(0 if self.data.get('ph_gerekli_mi', True) else 1)
        form.addRow("pH Gerekli:", self.ph_check)

        self.akim_check = QComboBox()
        self.akim_check.addItem("Evet", True)
        self.akim_check.addItem("Hayir", False)
        self.akim_check.setCurrentIndex(0 if self.data.get('akim_gerekli_mi', False) else 1)
        form.addRow("Akim Gerekli:", self.akim_check)

        self.aktif_combo = QComboBox()
        self.aktif_combo.addItem("Aktif", True)
        self.aktif_combo.addItem("Pasif", False)
        self.aktif_combo.setCurrentIndex(0 if self.data.get('aktif_mi', True) else 1)
        form.addRow("Durum:", self.aktif_combo)

        layout.addLayout(form)
        layout.addStretch()

        # ── Alt butonlar ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(brand.sp(38))
        cancel_btn.setStyleSheet(f"""
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
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(brand.sp(38))
        save_btn.setStyleSheet(f"""
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
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _save(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()

        if not kod or not ad:
            QMessageBox.warning(self, "Uyari", "Kod ve Ad zorunludur!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            params = (kod, ad, self.kategori_combo.currentData(),
                      self.kimyasal_check.currentData(), self.sicaklik_check.currentData(),
                      self.ph_check.currentData(), self.akim_check.currentData(),
                      self.aktif_combo.currentData())

            if self.tip_id:
                cursor.execute("""UPDATE tanim.banyo_tipleri SET kod=?, ad=?, kategori=?,
                    kimyasal_gerekli_mi=?, sicaklik_gerekli_mi=?, ph_gerekli_mi=?, akim_gerekli_mi=?,
                    aktif_mi=? WHERE id=?""", params + (self.tip_id,))
            else:
                cursor.execute("""INSERT INTO tanim.banyo_tipleri (kod, ad, kategori,
                    kimyasal_gerekli_mi, sicaklik_gerekli_mi, ph_gerekli_mi, akim_gerekli_mi, aktif_mi)
                    VALUES (?,?,?,?,?,?,?,?)""", params)

            conn.commit()
            QMessageBox.information(self, "Basarili", "Kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# =====================================================================
# DIALOG: Pozisyon Tipi
# =====================================================================

class PozisyonTipiDialog(QDialog):
    """Pozisyon Tipi Ekleme/Duzenleme — el kitabi uyumlu"""

    def __init__(self, theme: dict, tip_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.tip_id = tip_id
        self.data = {}

        self.setWindowTitle("Yeni Pozisyon Tipi" if not tip_id else "Pozisyon Tipi Duzenle")
        self.setMinimumSize(brand.sp(400), brand.sp(350))

        if tip_id:
            self._load_data()
        self._setup_ui()

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.pozisyon_tipleri WHERE id = ?", (self.tip_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {brand.PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_4)

        # ── Header ──
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)
        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        form = QFormLayout()
        form.setSpacing(brand.SP_3)

        self.kod_input = QLineEdit(self.data.get('kod', ''))
        self.kod_input.setPlaceholderText("Orn: BANYO, FIRIN, KURUTMA")
        form.addRow("Kod *:", self.kod_input)

        self.ad_input = QLineEdit(self.data.get('ad', ''))
        self.ad_input.setPlaceholderText("Orn: Banyo Pozisyonu")
        form.addRow("Ad *:", self.ad_input)

        self.ikon_input = QLineEdit(self.data.get('ikon', '') or '')
        self.ikon_input.setPlaceholderText("Orn: icon adi")
        form.addRow("Ikon:", self.ikon_input)

        self.renk_input = QLineEdit(self.data.get('renk_kodu', '') or '')
        self.renk_input.setPlaceholderText("Orn: #3B82F6")
        form.addRow("Renk Kodu:", self.renk_input)

        self.aktif_combo = QComboBox()
        self.aktif_combo.addItem("Aktif", True)
        self.aktif_combo.addItem("Pasif", False)
        self.aktif_combo.setCurrentIndex(0 if self.data.get('aktif_mi', True) else 1)
        form.addRow("Durum:", self.aktif_combo)

        layout.addLayout(form)
        layout.addStretch()

        # ── Alt butonlar ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(brand.sp(38))
        cancel_btn.setStyleSheet(f"""
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
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(brand.sp(38))
        save_btn.setStyleSheet(f"""
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
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _save(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()

        if not kod or not ad:
            QMessageBox.warning(self, "Uyari", "Kod ve Ad zorunludur!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            params = (kod, ad, self.ikon_input.text().strip() or None,
                      self.renk_input.text().strip() or None,
                      self.aktif_combo.currentData())

            if self.tip_id:
                cursor.execute("""UPDATE tanim.pozisyon_tipleri SET kod=?, ad=?, ikon=?, renk_kodu=?, aktif_mi=?
                    WHERE id=?""", params + (self.tip_id,))
            else:
                cursor.execute("""INSERT INTO tanim.pozisyon_tipleri (kod, ad, ikon, renk_kodu, aktif_mi)
                    VALUES (?,?,?,?,?)""", params)

            conn.commit()
            QMessageBox.information(self, "Basarili", "Kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# =====================================================================
# ANA SAYFA
# =====================================================================

class LabTanimPage(BasePage):
    """Laboratuvar Tanimlari Ana Sayfasi"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_all)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # ── 1. Header ──
        header = self.create_page_header(
            "Laboratuvar Tanimlari",
            "Banyo tipleri ve pozisyon tipleri yonetimi"
        )
        layout.addLayout(header)

        # ── 2. Tabs ──
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                background: {brand.BG_CARD};
                border-radius: {brand.R_LG}px;
            }}
            QTabBar::tab {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                padding: {brand.SP_3}px {brand.SP_5}px;
                margin-right: {brand.SP_1}px;
                border-radius: {brand.R_SM}px {brand.R_SM}px 0 0;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QTabBar::tab:selected {{
                background: {brand.BG_CARD};
                border-bottom: 2px solid {brand.PRIMARY};
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QTabBar::tab:hover {{
                background: {brand.BG_HOVER};
            }}
        """)

        self.tabs.addTab(self._create_banyo_tipleri_tab(), "Banyo Tipleri")
        self.tabs.addTab(self._create_pozisyon_tipleri_tab(), "Pozisyon Tipleri")
        self.tabs.currentChanged.connect(self._on_tab_change)

        layout.addWidget(self.tabs, 1)

    # -----------------------------------------------------------------
    def _create_banyo_tipleri_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(brand.SP_5, brand.SP_5, brand.SP_5, brand.SP_5)
        layout.setSpacing(brand.SP_4)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)

        self.banyo_search = QLineEdit()
        self.banyo_search.setPlaceholderText("Ara...")
        self.banyo_search.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.banyo_search.setMaximumWidth(brand.sp(250))
        self.banyo_search.returnPressed.connect(self._load_banyo_tipleri)
        toolbar.addWidget(self.banyo_search)

        self.banyo_kategori_combo = QComboBox()
        self.banyo_kategori_combo.addItem("Tum Kategoriler", None)
        self.banyo_kategori_combo.addItem("On Islem", "ON_ISLEM")
        self.banyo_kategori_combo.addItem("Kaplama", "KAPLAMA")
        self.banyo_kategori_combo.addItem("Son Islem", "SON_ISLEM")
        self.banyo_kategori_combo.addItem("Yikama", "YIKAMA")
        self.banyo_kategori_combo.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
                min-width: {brand.sp(120)}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.banyo_kategori_combo.currentIndexChanged.connect(self._load_banyo_tipleri)
        toolbar.addWidget(self.banyo_kategori_combo)

        toolbar.addStretch()

        add_btn = QPushButton("Yeni Banyo Tipi")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(brand.sp(38))
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_banyo_tipi)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        self.banyo_table = QTableWidget()
        self.banyo_table.setColumnCount(6)
        self.banyo_table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Kategori", "Durum", "Islem"])
        self.banyo_table.setColumnWidth(5, brand.sp(170))
        self.banyo_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.banyo_table.verticalHeader().setVisible(False)
        self.banyo_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.banyo_table.setShowGrid(False)
        self.banyo_table.setAlternatingRowColors(True)
        self.banyo_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.banyo_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.banyo_table.setStyleSheet(self._table_style())
        layout.addWidget(self.banyo_table, 1)

        return widget

    # -----------------------------------------------------------------
    def _create_pozisyon_tipleri_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(brand.SP_5, brand.SP_5, brand.SP_5, brand.SP_5)
        layout.setSpacing(brand.SP_4)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)

        self.poz_search = QLineEdit()
        self.poz_search.setPlaceholderText("Ara...")
        self.poz_search.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.poz_search.setMaximumWidth(brand.sp(250))
        self.poz_search.returnPressed.connect(self._load_pozisyon_tipleri)
        toolbar.addWidget(self.poz_search)
        toolbar.addStretch()

        add_btn = QPushButton("Yeni Pozisyon Tipi")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(brand.sp(38))
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_pozisyon_tipi)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        self.poz_table = QTableWidget()
        self.poz_table.setColumnCount(5)
        self.poz_table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Durum", "Islem"])
        self.poz_table.setColumnWidth(4, brand.sp(170))
        self.poz_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.poz_table.verticalHeader().setVisible(False)
        self.poz_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.poz_table.setShowGrid(False)
        self.poz_table.setAlternatingRowColors(True)
        self.poz_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.poz_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.poz_table.setStyleSheet(self._table_style())
        layout.addWidget(self.poz_table, 1)

        return widget

    # -----------------------------------------------------------------
    def _load_all(self):
        self._load_banyo_tipleri()
        self._load_pozisyon_tipleri()

    def _on_tab_change(self, idx):
        if idx == 0:
            self._load_banyo_tipleri()
        elif idx == 1:
            self._load_pozisyon_tipleri()

    # -----------------------------------------------------------------
    def _load_banyo_tipleri(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = "SELECT id, kod, ad, kategori, aktif_mi FROM tanim.banyo_tipleri WHERE 1=1"
            params = []

            search = self.banyo_search.text().strip()
            if search:
                sql += " AND (kod LIKE ? OR ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            kategori = self.banyo_kategori_combo.currentData()
            if kategori:
                sql += " AND kategori=?"
                params.append(kategori)

            sql += " ORDER BY kod"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            kategori_map = {
                "ON_ISLEM": "On Islem", "KAPLAMA": "Kaplama",
                "SON_ISLEM": "Son Islem", "YIKAMA": "Yikama", "DIGER": "Diger"
            }

            self.banyo_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.banyo_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.banyo_table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.banyo_table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.banyo_table.setItem(i, 3, QTableWidgetItem(kategori_map.get(row[3], row[3] or '')))

                durum_text = "Aktif" if row[4] else "Pasif"
                durum = QTableWidgetItem(durum_text)
                durum.setForeground(QColor(brand.SUCCESS) if row[4] else QColor(brand.ERROR))
                self.banyo_table.setItem(i, 4, durum)

                widget = self.create_action_buttons([
                    ("Duzenle", "Duzenle", lambda checked, rid=row[0]: self._edit_banyo_tipi(rid), "edit"),
                    ("Sil", "Sil", lambda checked, rid=row[0]: self._delete_banyo_tipi(rid), "delete"),
                ])
                self.banyo_table.setCellWidget(i, 5, widget)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # -----------------------------------------------------------------
    def _load_pozisyon_tipleri(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = "SELECT id, kod, ad, aktif_mi FROM tanim.pozisyon_tipleri WHERE 1=1"
            params = []

            search = self.poz_search.text().strip()
            if search:
                sql += " AND (kod LIKE ? OR ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            sql += " ORDER BY kod"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            self.poz_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.poz_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.poz_table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.poz_table.setItem(i, 2, QTableWidgetItem(row[2] or ''))

                durum_text = "Aktif" if row[3] else "Pasif"
                durum = QTableWidgetItem(durum_text)
                durum.setForeground(QColor(brand.SUCCESS) if row[3] else QColor(brand.ERROR))
                self.poz_table.setItem(i, 3, durum)

                widget = self.create_action_buttons([
                    ("Duzenle", "Duzenle", lambda checked, rid=row[0]: self._edit_pozisyon_tipi(rid), "edit"),
                    ("Sil", "Sil", lambda checked, rid=row[0]: self._delete_pozisyon_tipi(rid), "delete"),
                ])
                self.poz_table.setCellWidget(i, 4, widget)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # -----------------------------------------------------------------
    def _add_banyo_tipi(self):
        dlg = BanyoTipiDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_banyo_tipleri()

    def _edit_banyo_tipi(self, tid):
        dlg = BanyoTipiDialog(self.theme, tid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_banyo_tipleri()

    def _delete_banyo_tipi(self, tid):
        if QMessageBox.question(self, "Onay", "Bu banyo tipini silmek istediginize emin misiniz?") == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM uretim.banyo_tanimlari WHERE banyo_tipi_id=?", (tid,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyari", "Bu tipe bagli banyolar var!")
                    return
                cursor.execute("DELETE FROM tanim.banyo_tipleri WHERE id=?", (tid,))
                conn.commit()
                self._load_banyo_tipleri()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    def _add_pozisyon_tipi(self):
        dlg = PozisyonTipiDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_pozisyon_tipleri()

    def _edit_pozisyon_tipi(self, tid):
        dlg = PozisyonTipiDialog(self.theme, tid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_pozisyon_tipleri()

    def _delete_pozisyon_tipi(self, tid):
        if QMessageBox.question(self, "Onay", "Bu pozisyon tipini silmek istediginize emin misiniz?") == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tanim.hat_pozisyonlar WHERE pozisyon_tipi_id=?", (tid,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyari", "Bu tipe bagli pozisyonlar var!")
                    return
                cursor.execute("DELETE FROM tanim.pozisyon_tipleri WHERE id=?", (tid,))
                conn.commit()
                self._load_pozisyon_tipleri()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    # -----------------------------------------------------------------
    @staticmethod
    def _table_style():
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
