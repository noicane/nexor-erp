# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kontrol Plani Yonetimi
===================================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
kalite.kontrol_planlari ve kalite.kontrol_plan_satirlar tablolari
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QGroupBox, QDateEdit,
    QSpinBox, QTextEdit, QTabWidget, QSplitter, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


# =====================================================================
# DIALOG: Kontrol Plan Satiri
# =====================================================================

class KontrolPlanSatirDialog(QDialog):
    """Kontrol plani satiri ekleme/duzenleme - el kitabi uyumlu"""

    def __init__(self, theme: dict, plan_id: int, parent=None, satir_id=None):
        super().__init__(parent)
        self.theme = theme
        self.plan_id = plan_id
        self.satir_id = satir_id
        self.setWindowTitle("Kontrol Satiri Ekle" if not satir_id else "Kontrol Satiri Duzenle")
        self.setMinimumSize(brand.sp(600), brand.sp(500))
        self.setModal(True)
        self._setup_ui()

        if satir_id:
            self._load_data()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QSpinBox, QComboBox, QTextEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
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
            QCheckBox {{
                color: {brand.TEXT};
                spacing: {brand.SP_2}px;
                font-size: {brand.FS_BODY}px;
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # -- Header --
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

        # Form
        form = QFormLayout()
        form.setSpacing(brand.SP_3)
        form.setLabelAlignment(Qt.AlignRight)

        self.spin_sira = QSpinBox()
        self.spin_sira.setRange(1, 999)
        self.spin_sira.setValue(1)
        form.addRow("Sira No*:", self.spin_sira)

        self.txt_operasyon = QLineEdit()
        self.txt_operasyon.setPlaceholderText("Orn: Kaplama, Paketleme, Montaj")
        form.addRow("Operasyon*:", self.txt_operasyon)

        self.txt_kontrol = QLineEdit()
        self.txt_kontrol.setPlaceholderText("Orn: Kaplama Kalinligi, Gorsel Kontrol")
        form.addRow("Kontrol Ozelligi*:", self.txt_kontrol)

        self.txt_spesifikasyon = QLineEdit()
        self.txt_spesifikasyon.setPlaceholderText("Orn: 8-12 um, Cizik/Catlak yok")
        form.addRow("Spesifikasyon:", self.txt_spesifikasyon)

        # Min-Max
        minmax_layout = QHBoxLayout()
        self.txt_min = QLineEdit()
        self.txt_min.setPlaceholderText("Min")
        minmax_layout.addWidget(self.txt_min)
        sep = QLabel("-")
        sep.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px;")
        minmax_layout.addWidget(sep)
        self.txt_max = QLineEdit()
        self.txt_max.setPlaceholderText("Max")
        minmax_layout.addWidget(self.txt_max)
        form.addRow("Min - Max:", minmax_layout)

        self.txt_metod = QLineEdit()
        self.txt_metod.setPlaceholderText("Orn: XRF, Gorsel, Kaliper")
        form.addRow("Olcum Metodu:", self.txt_metod)

        self.txt_cihaz = QLineEdit()
        self.txt_cihaz.setPlaceholderText("Orn: XRF-001, Kaliper-05")
        form.addRow("Olcum Cihazi:", self.txt_cihaz)

        self.txt_numune = QLineEdit()
        self.txt_numune.setPlaceholderText("Orn: 5 adet, %10, Ilk parca")
        form.addRow("Numune Boyutu:", self.txt_numune)

        self.txt_frekans = QLineEdit()
        self.txt_frekans.setPlaceholderText("Orn: Her parti, Saatlik, Vardiya basi")
        form.addRow("Kontrol Frekansi:", self.txt_frekans)

        self.txt_reaksiyon = QTextEdit()
        self.txt_reaksiyon.setMaximumHeight(brand.sp(60))
        self.txt_reaksiyon.setPlaceholderText("Uygunsuzluk durumunda yapilacak islem")
        form.addRow("Reaksiyon Plani:", self.txt_reaksiyon)

        self.txt_form = QLineEdit()
        self.txt_form.setPlaceholderText("Orn: FR-KAL-001")
        form.addRow("Kayit Formu:", self.txt_form)

        # Checkbox'lar
        check_layout = QHBoxLayout()
        self.chk_kritik = QCheckBox("Kritik Ozellik (CC)")
        self.chk_spc = QCheckBox("SPC Uygulanacak")
        check_layout.addWidget(self.chk_kritik)
        check_layout.addWidget(self.chk_spc)
        check_layout.addStretch()
        form.addRow("", check_layout)

        layout.addLayout(form)
        layout.addStretch()

        # -- Alt butonlar --
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
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
        """Mevcut satir verilerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sira_no, operasyon, kontrol_ozelligi, spesifikasyon,
                       min_deger, max_deger, olcum_metodu, olcum_cihazi,
                       numune_boyutu, frekans, reaksiyon_plani, kayit_formu,
                       kritik_mi, spc_uygulanacak_mi
                FROM kalite.kontrol_plan_satirlar WHERE id = ?
            """, (self.satir_id,))
            row = cursor.fetchone()

            if row:
                self.spin_sira.setValue(row[0] or 1)
                self.txt_operasyon.setText(row[1] or "")
                self.txt_kontrol.setText(row[2] or "")
                self.txt_spesifikasyon.setText(row[3] or "")
                self.txt_min.setText(str(row[4]) if row[4] else "")
                self.txt_max.setText(str(row[5]) if row[5] else "")
                self.txt_metod.setText(row[6] or "")
                self.txt_cihaz.setText(row[7] or "")
                self.txt_numune.setText(row[8] or "")
                self.txt_frekans.setText(row[9] or "")
                self.txt_reaksiyon.setPlainText(row[10] or "")
                self.txt_form.setText(row[11] or "")
                self.chk_kritik.setChecked(row[12] or False)
                self.chk_spc.setChecked(row[13] or False)
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
        operasyon = self.txt_operasyon.text().strip()
        kontrol = self.txt_kontrol.text().strip()

        if not operasyon or not kontrol:
            QMessageBox.warning(self, "Uyari", "Operasyon ve Kontrol Ozelligi zorunludur!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            min_val = float(self.txt_min.text()) if self.txt_min.text().strip() else None
            max_val = float(self.txt_max.text()) if self.txt_max.text().strip() else None

            if self.satir_id:
                cursor.execute("""
                    UPDATE kalite.kontrol_plan_satirlar SET
                        sira_no = ?, operasyon = ?, kontrol_ozelligi = ?, spesifikasyon = ?,
                        min_deger = ?, max_deger = ?, olcum_metodu = ?, olcum_cihazi = ?,
                        numune_boyutu = ?, frekans = ?, reaksiyon_plani = ?, kayit_formu = ?,
                        kritik_mi = ?, spc_uygulanacak_mi = ?
                    WHERE id = ?
                """, (
                    self.spin_sira.value(), operasyon, kontrol,
                    self.txt_spesifikasyon.text().strip() or None,
                    min_val, max_val,
                    self.txt_metod.text().strip() or None,
                    self.txt_cihaz.text().strip() or None,
                    self.txt_numune.text().strip() or None,
                    self.txt_frekans.text().strip() or None,
                    self.txt_reaksiyon.toPlainText().strip() or None,
                    self.txt_form.text().strip() or None,
                    self.chk_kritik.isChecked(), self.chk_spc.isChecked(),
                    self.satir_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO kalite.kontrol_plan_satirlar
                    (plan_id, sira_no, operasyon, kontrol_ozelligi, spesifikasyon,
                     min_deger, max_deger, olcum_metodu, olcum_cihazi,
                     numune_boyutu, frekans, reaksiyon_plani, kayit_formu,
                     kritik_mi, spc_uygulanacak_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.plan_id, self.spin_sira.value(), operasyon, kontrol,
                    self.txt_spesifikasyon.text().strip() or None,
                    min_val, max_val,
                    self.txt_metod.text().strip() or None,
                    self.txt_cihaz.text().strip() or None,
                    self.txt_numune.text().strip() or None,
                    self.txt_frekans.text().strip() or None,
                    self.txt_reaksiyon.toPlainText().strip() or None,
                    self.txt_form.text().strip() or None,
                    self.chk_kritik.isChecked(), self.chk_spc.isChecked()
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
# DIALOG: Kontrol Plani
# =====================================================================

class KontrolPlanDialog(QDialog):
    """Kontrol plani ekleme/duzenleme - el kitabi uyumlu"""

    def __init__(self, theme: dict, parent=None, plan_id=None):
        super().__init__(parent)
        self.theme = theme
        self.plan_id = plan_id
        self.setWindowTitle("Kontrol Plani Ekle" if not plan_id else "Kontrol Plani Duzenle")
        self.setMinimumSize(brand.sp(900), brand.sp(600))
        self.setModal(True)
        self._setup_ui()
        self._load_combos()

        if plan_id:
            self._load_data()
            self._load_satirlar()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QSpinBox, QComboBox, QDateEdit, QTextEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{
                border-color: {brand.PRIMARY};
            }}
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                background: {brand.BG_CARD};
            }}
            QTabBar::tab {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_5}px;
                margin-right: {brand.SP_1}px;
                border-top-left-radius: {brand.R_SM}px;
                border-top-right-radius: {brand.R_SM}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QTabBar::tab:selected {{
                background: {brand.PRIMARY};
                color: white;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QCheckBox {{
                color: {brand.TEXT};
                spacing: {brand.SP_2}px;
                font-size: {brand.FS_BODY}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # -- Header --
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)
        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)
        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(title)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)

        # Tab widget
        tabs = QTabWidget()

        # Tab 1: Genel Bilgiler
        tab_genel = QWidget()
        genel_layout = QFormLayout(tab_genel)
        genel_layout.setSpacing(brand.SP_3)
        genel_layout.setLabelAlignment(Qt.AlignRight)
        genel_layout.setContentsMargins(brand.SP_5, brand.SP_5, brand.SP_5, brand.SP_5)

        self.txt_plan_no = QLineEdit()
        self.txt_plan_no.setPlaceholderText("Orn: CP-001, KP-2024-001")
        genel_layout.addRow("Plan No*:", self.txt_plan_no)

        self.spin_revizyon = QSpinBox()
        self.spin_revizyon.setRange(1, 99)
        self.spin_revizyon.setValue(1)
        genel_layout.addRow("Revizyon:", self.spin_revizyon)

        self.cmb_musteri = QComboBox()
        genel_layout.addRow("Musteri:", self.cmb_musteri)

        self.cmb_urun = QComboBox()
        genel_layout.addRow("Urun:", self.cmb_urun)

        self.cmb_kaplama = QComboBox()
        genel_layout.addRow("Kaplama Turu:", self.cmb_kaplama)

        self.date_baslangic = QDateEdit()
        self.date_baslangic.setDate(QDate.currentDate())
        self.date_baslangic.setCalendarPopup(True)
        genel_layout.addRow("Gecerlilik Baslangic*:", self.date_baslangic)

        self.date_bitis = QDateEdit()
        self.date_bitis.setDate(QDate.currentDate().addYears(1))
        self.date_bitis.setCalendarPopup(True)
        genel_layout.addRow("Gecerlilik Bitis:", self.date_bitis)

        self.cmb_hazirlayan = QComboBox()
        genel_layout.addRow("Hazirlayan:", self.cmb_hazirlayan)

        self.cmb_onaylayan = QComboBox()
        genel_layout.addRow("Onaylayan:", self.cmb_onaylayan)

        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["TASLAK", "ONAY_BEKLIYOR", "ONAYLANDI", "IPTAL"])
        genel_layout.addRow("Durum:", self.cmb_durum)

        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(brand.sp(80))
        genel_layout.addRow("Notlar:", self.txt_notlar)

        tabs.addTab(tab_genel, "Genel Bilgiler")

        # Tab 2: Kontrol Satirlari
        tab_satirlar = QWidget()
        satirlar_layout = QVBoxLayout(tab_satirlar)
        satirlar_layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        satirlar_layout.setSpacing(brand.SP_4)

        # Toolbar
        satir_toolbar = QHBoxLayout()
        satir_toolbar.setSpacing(brand.SP_3)

        btn_satir_ekle = QPushButton("Satir Ekle")
        btn_satir_ekle.setCursor(Qt.PointingHandCursor)
        btn_satir_ekle.setFixedHeight(brand.sp(38))
        btn_satir_ekle.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        btn_satir_ekle.clicked.connect(self._add_satir)
        satir_toolbar.addWidget(btn_satir_ekle)

        btn_satir_duzenle = QPushButton("Duzenle")
        btn_satir_duzenle.setCursor(Qt.PointingHandCursor)
        btn_satir_duzenle.setFixedHeight(brand.sp(38))
        btn_satir_duzenle.setStyleSheet(f"""
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
        btn_satir_duzenle.clicked.connect(self._edit_satir)
        satir_toolbar.addWidget(btn_satir_duzenle)

        btn_satir_sil = QPushButton("Sil")
        btn_satir_sil.setCursor(Qt.PointingHandCursor)
        btn_satir_sil.setFixedHeight(brand.sp(38))
        btn_satir_sil.setStyleSheet(f"""
            QPushButton {{
                background: {brand.ERROR};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #DC2626; }}
        """)
        btn_satir_sil.clicked.connect(self._delete_satir)
        satir_toolbar.addWidget(btn_satir_sil)

        satir_toolbar.addStretch()
        satirlar_layout.addLayout(satir_toolbar)

        # Tablo
        self.table_satirlar = QTableWidget()
        self.table_satirlar.setColumnCount(9)
        self.table_satirlar.setHorizontalHeaderLabels([
            "ID", "Sira", "Operasyon", "Kontrol Ozelligi", "Spesifikasyon",
            "Metod", "Frekans", "Kritik", "SPC"
        ])
        self.table_satirlar.setColumnHidden(0, True)
        self.table_satirlar.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_satirlar.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_satirlar.verticalHeader().setVisible(False)
        self.table_satirlar.setShowGrid(False)
        self.table_satirlar.setAlternatingRowColors(True)
        self.table_satirlar.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table_satirlar.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_2}px {brand.SP_3}px;
                border-bottom: 1px solid {brand.BORDER};
                color: {brand.TEXT};
            }}
            QTableWidget::item:alternate {{ background: {brand.BG_MAIN}; }}
            QTableWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """)
        tbl_header = self.table_satirlar.horizontalHeader()
        tbl_header.setSectionResizeMode(3, QHeaderView.Stretch)
        tbl_header.setSectionResizeMode(4, QHeaderView.Stretch)

        satirlar_layout.addWidget(self.table_satirlar)
        tabs.addTab(tab_satirlar, "Kontrol Satirlari")

        layout.addWidget(tabs, 1)

        # -- Alt butonlar --
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
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

    def _load_combos(self):
        """Combo listelerini doldur"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Musteriler
            self.cmb_musteri.addItem("-- Musteri Seciniz --", None)
            cursor.execute("""
                SELECT DISTINCT cari_unvani
                FROM stok.urunler
                WHERE cari_unvani IS NOT NULL AND cari_unvani <> '' AND aktif_mi = 1
                ORDER BY cari_unvani
            """)
            for row in cursor.fetchall():
                self.cmb_musteri.addItem(row[0], row[0])

            # Musteri degisince urunleri guncelle
            self.cmb_musteri.currentIndexChanged.connect(self._on_musteri_changed)

            # Urunler - bos baslar
            self.cmb_urun.addItem("-- Once Musteri Secin --", None)

            # Kaplama turleri
            self.cmb_kaplama.addItem("-- Seciniz --", None)
            cursor.execute("SELECT id, kod, ad FROM tanim.kaplama_turleri WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_kaplama.addItem(f"{row[1]} - {row[2]}", row[0])

            # Personeller
            self.cmb_hazirlayan.addItem("-- Seciniz --", None)
            self.cmb_onaylayan.addItem("-- Seciniz --", None)
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_hazirlayan.addItem(row[1], row[0])
                self.cmb_onaylayan.addItem(row[1], row[0])

        except Exception as e:
            print(f"[kontrol_plani] Combo yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _on_musteri_changed(self):
        """Musteri degistiginde urunleri guncelle"""
        cari_unvani = self.cmb_musteri.currentData()
        self._load_urunler(cari_unvani)

    def _load_urunler(self, cari_unvani=None):
        """Secilen musteriye ait urun listesi"""
        self.cmb_urun.clear()
        self.cmb_urun.addItem("-- Urun Secin --", None)
        if not cari_unvani:
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, ISNULL(s.urun_kodu, '') + ' - ' + ISNULL(s.urun_adi, '')
                FROM stok.urunler s
                LEFT JOIN stok.urunler u ON u.urun_kodu = s.stok_kodu
                WHERE s.cari_unvani = ? AND ISNULL(s.aktif, 1) = 1
                ORDER BY s.stok_kodu
            """, (cari_unvani,))
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
        """Plan verilerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kp.plan_no, kp.revizyon, kp.urun_id, kp.kaplama_turu_id, kp.cari_id,
                       kp.gecerlilik_baslangic, kp.gecerlilik_bitis,
                       kp.hazirlayan_id, kp.onaylayan_id, kp.durum, kp.notlar, c.unvan
                FROM kalite.kontrol_planlari kp
                LEFT JOIN musteri.cariler c ON kp.cari_id = c.id
                WHERE kp.id = ?
            """, (self.plan_id,))
            row = cursor.fetchone()

            if row:
                self.txt_plan_no.setText(row[0] or "")
                self.txt_plan_no.setEnabled(False)
                self.spin_revizyon.setValue(row[1] or 1)

                # Once musteriyi set et
                cari_unvani = row[11]
                if cari_unvani:
                    idx = self.cmb_musteri.findData(cari_unvani)
                    if idx >= 0:
                        self.cmb_musteri.setCurrentIndex(idx)
                        self._load_urunler(cari_unvani)

                # Sonra urunu set et
                if row[2]:
                    idx = self.cmb_urun.findData(row[2])
                    if idx >= 0:
                        self.cmb_urun.setCurrentIndex(idx)

                if row[3]:
                    idx = self.cmb_kaplama.findData(row[3])
                    if idx >= 0:
                        self.cmb_kaplama.setCurrentIndex(idx)

                if row[5]:
                    self.date_baslangic.setDate(QDate(row[5].year, row[5].month, row[5].day))
                if row[6]:
                    self.date_bitis.setDate(QDate(row[6].year, row[6].month, row[6].day))

                if row[7]:
                    idx = self.cmb_hazirlayan.findData(row[7])
                    if idx >= 0:
                        self.cmb_hazirlayan.setCurrentIndex(idx)

                if row[8]:
                    idx = self.cmb_onaylayan.findData(row[8])
                    if idx >= 0:
                        self.cmb_onaylayan.setCurrentIndex(idx)

                if row[9]:
                    idx = self.cmb_durum.findText(row[9])
                    if idx >= 0:
                        self.cmb_durum.setCurrentIndex(idx)

                self.txt_notlar.setPlainText(row[10] or "")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yuklenirken hata: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_satirlar(self):
        """Kontrol satirlarini yukle"""
        if not self.plan_id:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sira_no, operasyon, kontrol_ozelligi, spesifikasyon,
                       olcum_metodu, frekans, kritik_mi, spc_uygulanacak_mi
                FROM kalite.kontrol_plan_satirlar
                WHERE plan_id = ? AND aktif_mi = 1
                ORDER BY sira_no
            """, (self.plan_id,))
            rows = cursor.fetchall()

            self.table_satirlar.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table_satirlar.setRowHeight(i, brand.sp(42))
                self.table_satirlar.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_satirlar.setItem(i, 1, QTableWidgetItem(str(row[1])))
                self.table_satirlar.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.table_satirlar.setItem(i, 3, QTableWidgetItem(row[3] or ""))
                self.table_satirlar.setItem(i, 4, QTableWidgetItem(row[4] or ""))
                self.table_satirlar.setItem(i, 5, QTableWidgetItem(row[5] or ""))
                self.table_satirlar.setItem(i, 6, QTableWidgetItem(row[6] or ""))

                kritik_item = QTableWidgetItem("Evet" if row[7] else "")
                if row[7]:
                    kritik_item.setForeground(QColor(brand.ERROR))
                self.table_satirlar.setItem(i, 7, kritik_item)

                spc_item = QTableWidgetItem("Evet" if row[8] else "")
                if row[8]:
                    spc_item.setForeground(QColor(brand.SUCCESS))
                self.table_satirlar.setItem(i, 8, spc_item)

        except Exception as e:
            print(f"[kontrol_plani] Satir yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _add_satir(self):
        """Yeni satir ekle"""
        if not self.plan_id:
            QMessageBox.warning(self, "Uyari", "Once plani kaydedin!")
            return

        dialog = KontrolPlanSatirDialog(self.theme, self.plan_id, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()

    def _edit_satir(self):
        """Satir duzenle"""
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir satir secin!")
            return

        satir_id = int(self.table_satirlar.item(row, 0).text())
        dialog = KontrolPlanSatirDialog(self.theme, self.plan_id, self, satir_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()

    def _delete_satir(self):
        """Satir sil"""
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir satir secin!")
            return

        satir_id = int(self.table_satirlar.item(row, 0).text())

        reply = QMessageBox.question(self, "Onay", "Bu satiri silmek istediginize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE kalite.kontrol_plan_satirlar SET aktif_mi = 0 WHERE id = ?", (satir_id,))
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
        """Plani kaydet"""
        plan_no = self.txt_plan_no.text().strip()

        if not plan_no:
            QMessageBox.warning(self, "Uyari", "Plan No zorunludur!")
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

            if self.plan_id:
                cursor.execute("""
                    UPDATE kalite.kontrol_planlari SET
                        revizyon = ?, urun_id = ?, kaplama_turu_id = ?, cari_id = ?,
                        gecerlilik_baslangic = ?, gecerlilik_bitis = ?,
                        hazirlayan_id = ?, onaylayan_id = ?, durum = ?, notlar = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    self.spin_revizyon.value(),
                    self.cmb_urun.currentData(),
                    self.cmb_kaplama.currentData(),
                    cari_id,
                    self.date_baslangic.date().toPython(),
                    self.date_bitis.date().toPython(),
                    self.cmb_hazirlayan.currentData(),
                    self.cmb_onaylayan.currentData(),
                    self.cmb_durum.currentText(),
                    self.txt_notlar.toPlainText().strip() or None,
                    self.plan_id
                ))
            else:
                # Plan no kontrolu
                cursor.execute("SELECT COUNT(*) FROM kalite.kontrol_planlari WHERE plan_no = ?", (plan_no,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyari", "Bu Plan No zaten kullaniliyor!")
                    return

                cursor.execute("""
                    INSERT INTO kalite.kontrol_planlari
                    (plan_no, revizyon, urun_id, kaplama_turu_id, cari_id,
                     gecerlilik_baslangic, gecerlilik_bitis,
                     hazirlayan_id, onaylayan_id, durum, notlar)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    plan_no, self.spin_revizyon.value(),
                    self.cmb_urun.currentData(),
                    self.cmb_kaplama.currentData(),
                    cari_id,
                    self.date_baslangic.date().toPython(),
                    self.date_bitis.date().toPython(),
                    self.cmb_hazirlayan.currentData(),
                    self.cmb_onaylayan.currentData(),
                    self.cmb_durum.currentText(),
                    self.txt_notlar.toPlainText().strip() or None
                ))
                self.plan_id = cursor.fetchone()[0]

            conn.commit()

            QMessageBox.information(self, "Basarili", "Plan kaydedildi!")
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

class KontrolPlaniPage(BasePage):
    """Kontrol Plani Yonetimi Sayfasi - el kitabi uyumlu"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.all_rows = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # -- 1. Header --
        header = self.create_page_header(
            "Kontrol Plani Yonetimi",
            "Urun ve proses kontrol planlari"
        )

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        header.addWidget(btn_yenile)

        layout.addLayout(header)

        # -- 2. KPI cards --
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self._kpi_toplam = self.create_stat_card("TOPLAM PLAN", "0", color=brand.PRIMARY)
        kpi_row.addWidget(self._kpi_toplam)

        self._kpi_onaylandi = self.create_stat_card("ONAYLANDI", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self._kpi_onaylandi)

        self._kpi_taslak = self.create_stat_card("TASLAK", "0", color=brand.WARNING)
        kpi_row.addWidget(self._kpi_taslak)

        self._kpi_bekliyor = self.create_stat_card("ONAY BEKLIYOR", "0", color=brand.INFO)
        kpi_row.addWidget(self._kpi_bekliyor)

        kpi_row.addStretch()
        layout.addLayout(kpi_row)

        # -- 3. Toolbar --
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)
        toolbar_layout.setSpacing(brand.SP_3)

        btn_yeni = QPushButton("Yeni Plan")
        btn_yeni.setCursor(Qt.PointingHandCursor)
        btn_yeni.setFixedHeight(brand.sp(38))
        btn_yeni.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        btn_yeni.clicked.connect(self._yeni_plan)
        toolbar_layout.addWidget(btn_yeni)

        btn_duzenle = QPushButton("Duzenle")
        btn_duzenle.setCursor(Qt.PointingHandCursor)
        btn_duzenle.setFixedHeight(brand.sp(38))
        btn_duzenle.setStyleSheet(f"""
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
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar_layout.addWidget(btn_duzenle)

        btn_sil = QPushButton("Sil")
        btn_sil.setCursor(Qt.PointingHandCursor)
        btn_sil.setFixedHeight(brand.sp(38))
        btn_sil.setStyleSheet(f"""
            QPushButton {{
                background: {brand.ERROR};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #DC2626; }}
        """)
        btn_sil.clicked.connect(self._sil)
        toolbar_layout.addWidget(btn_sil)

        toolbar_layout.addStretch()

        # Arama
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Plan No veya Urun ara...")
        self.txt_search.setFixedHeight(brand.sp(38))
        self.txt_search.setMinimumWidth(brand.sp(200))
        self.txt_search.setStyleSheet(f"""
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
        self.txt_search.textChanged.connect(self._filter)
        toolbar_layout.addWidget(self.txt_search)

        # Durum filtresi
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tumu", "TASLAK", "ONAY_BEKLIYOR", "ONAYLANDI", "IPTAL"])
        self.cmb_durum.setFixedHeight(brand.sp(38))
        self.cmb_durum.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_durum)

        layout.addWidget(toolbar)

        # -- 4. Tablo --
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Plan No", "Rev", "Urun/Kaplama", "Musteri",
            "Gecerlilik", "Durum", "Satir", "Olusturma"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
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

        tbl_header = self.table.horizontalHeader()
        tbl_header.setSectionResizeMode(3, QHeaderView.Stretch)
        tbl_header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(1, brand.sp(100))
        self.table.setColumnWidth(2, brand.sp(60))
        self.table.setColumnWidth(5, brand.sp(100))
        self.table.setColumnWidth(6, brand.sp(100))
        self.table.setColumnWidth(7, brand.sp(60))
        self.table.setColumnWidth(8, brand.sp(100))

        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table, 1)

        # -- 5. Alt istatistik --
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;"
        )
        layout.addWidget(self.lbl_stat)

    def _load_data(self):
        """Verileri yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    kp.id, kp.plan_no, kp.revizyon,
                    ISNULL(u.urun_kodu, '') + ' / ' + ISNULL(kt.kod, '') as urun_kaplama,
                    c.unvan,
                    FORMAT(kp.gecerlilik_baslangic, 'dd.MM.yyyy') + ' - ' + ISNULL(FORMAT(kp.gecerlilik_bitis, 'dd.MM.yyyy'), '-'),
                    kp.durum,
                    (SELECT COUNT(*) FROM kalite.kontrol_plan_satirlar WHERE plan_id = kp.id AND aktif_mi = 1),
                    FORMAT(kp.olusturma_tarihi, 'dd.MM.yyyy')
                FROM kalite.kontrol_planlari kp
                LEFT JOIN stok.urunler u ON kp.urun_id = u.id
                LEFT JOIN tanim.kaplama_turleri kt ON kp.kaplama_turu_id = kt.id
                LEFT JOIN musteri.cariler c ON kp.cari_id = c.id
                ORDER BY kp.olusturma_tarihi DESC
            """)
            self.all_rows = cursor.fetchall()

            self._display_data(self.all_rows)

            # KPI guncelle
            toplam = len(self.all_rows)
            onaylandi = sum(1 for r in self.all_rows if r[6] == 'ONAYLANDI')
            taslak = sum(1 for r in self.all_rows if r[6] == 'TASLAK')
            bekliyor = sum(1 for r in self.all_rows if r[6] == 'ONAY_BEKLIYOR')

            self._kpi_toplam.findChild(QLabel, "stat_value").setText(str(toplam))
            self._kpi_onaylandi.findChild(QLabel, "stat_value").setText(str(onaylandi))
            self._kpi_taslak.findChild(QLabel, "stat_value").setText(str(taslak))
            self._kpi_bekliyor.findChild(QLabel, "stat_value").setText(str(bekliyor))

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yuklenirken hata: {str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _display_data(self, rows):
        """Verileri tabloda goster"""
        self.table.setRowCount(len(rows))

        durum_colors = {
            'TASLAK': brand.WARNING,
            'ONAY_BEKLIYOR': brand.INFO,
            'ONAYLANDI': brand.SUCCESS,
            'IPTAL': brand.ERROR,
        }

        for i, row in enumerate(rows):
            self.table.setRowHeight(i, brand.sp(42))
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "")

                # Durum rengi
                if j == 6 and val:
                    item.setForeground(QColor(durum_colors.get(val, brand.TEXT)))

                # Satir sayisi ortalama
                if j == 7:
                    item.setTextAlignment(Qt.AlignCenter)

                self.table.setItem(i, j, item)

        self.lbl_stat.setText(f"Toplam: {len(rows)} kontrol plani")

    def _filter(self):
        """Filtrele"""
        search = self.txt_search.text().lower()
        durum = self.cmb_durum.currentText()

        filtered = []
        for row in self.all_rows:
            # Arama
            if search:
                if search not in str(row[1]).lower() and search not in str(row[3]).lower():
                    continue
            # Durum
            if durum != "Tumu" and row[6] != durum:
                continue
            filtered.append(row)

        self._display_data(filtered)

    def _yeni_plan(self):
        """Yeni plan ekle"""
        dialog = KontrolPlanDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _duzenle(self):
        """Plan duzenle"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir plan secin!")
            return

        plan_id = int(self.table.item(row, 0).text())
        dialog = KontrolPlanDialog(self.theme, self, plan_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _sil(self):
        """Plan sil"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir plan secin!")
            return

        plan_id = int(self.table.item(row, 0).text())
        plan_no = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Onay", f"'{plan_no}' planini silmek istediginize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM kalite.kontrol_planlari WHERE id = ?", (plan_id,))
                conn.commit()
                self._load_data()
                QMessageBox.information(self, "Basarili", "Plan silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatasi: {str(e)}")
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
