# -*- coding: utf-8 -*-
"""
NEXOR ERP - Stok Sayim Sayfasi
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QWidget, QDialog,
    QFormLayout, QDateEdit, QTextEdit, QCheckBox, QSplitter,
    QListWidget, QListWidgetItem, QDoubleSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand


def _ensure_sayim_tables():
    """stok.sayimlar ve stok.sayim_detaylari tablolarini olusturur (yoksa)"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SCHEMA_ID('stok')")
        if cursor.fetchone()[0] is None:
            cursor.execute("EXEC('CREATE SCHEMA stok')")
            conn.commit()
        cursor.execute("SELECT OBJECT_ID('stok.sayimlar')")
        if cursor.fetchone()[0] is None:
            cursor.execute("""CREATE TABLE stok.sayimlar (
                id INT IDENTITY(1,1) PRIMARY KEY,
                sayim_no NVARCHAR(50) NOT NULL,
                sayim_tipi NVARCHAR(30) NOT NULL,
                depo_id INT,
                sayim_tarihi DATE DEFAULT GETDATE(),
                aciklama NVARCHAR(500),
                durum NVARCHAR(20) DEFAULT 'TASLAK',
                olusturma_tarihi DATETIME DEFAULT GETDATE()
            )""")
            conn.commit()
        cursor.execute("SELECT OBJECT_ID('stok.sayim_detaylari')")
        if cursor.fetchone()[0] is None:
            cursor.execute("""CREATE TABLE stok.sayim_detaylari (
                id BIGINT IDENTITY(1,1) PRIMARY KEY,
                sayim_id INT NOT NULL,
                urun_id BIGINT NOT NULL,
                urun_kodu NVARCHAR(50),
                urun_adi NVARCHAR(250),
                urun_tipi NVARCHAR(100),
                birim NVARCHAR(20),
                sistem_miktari DECIMAL(18,4) DEFAULT 0,
                sayilan_miktar DECIMAL(18,4) NULL,
                fark DECIMAL(18,4) NULL,
                notlar NVARCHAR(500),
                durum NVARCHAR(20) DEFAULT 'BEKLIYOR',
                olusturma_tarihi DATETIME DEFAULT GETDATE()
            )""")
            conn.commit()
    except Exception:
        pass
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


class SayimOlusturDialog(QDialog):
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Yeni Sayim Olustur")
        self.setMinimumSize(brand.sp(500), brand.sp(400))
        self.setModal(True)
        self._setup_ui()
        self._load_combos()

    def _setup_ui(self):
        self.setStyleSheet(f"""
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
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # Header
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)
        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        title = QLabel("Yeni Sayim Olustur")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(title)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)

        # Form
        input_css = f"""
            QComboBox, QDateEdit, QTextEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """

        form = QFormLayout()
        form.setSpacing(brand.SP_3)
        label_style = f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; font-weight: {brand.FW_MEDIUM};"

        lbl = QLabel("Sayim Tipi *")
        lbl.setStyleSheet(label_style)
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["TAM_SAYIM", "SPOT_SAYIM", "DEVIR_SAYIMI"])
        self.cmb_tip.setStyleSheet(input_css)
        form.addRow(lbl, self.cmb_tip)

        lbl = QLabel("Depo *")
        lbl.setStyleSheet(label_style)
        self.cmb_depo = QComboBox()
        self.cmb_depo.setStyleSheet(input_css)
        form.addRow(lbl, self.cmb_depo)

        lbl = QLabel("Sayim Tarihi")
        lbl.setStyleSheet(label_style)
        self.date_sayim = QDateEdit()
        self.date_sayim.setDate(QDate.currentDate())
        self.date_sayim.setCalendarPopup(True)
        self.date_sayim.setStyleSheet(input_css)
        form.addRow(lbl, self.date_sayim)

        lbl = QLabel("Aciklama")
        lbl.setStyleSheet(label_style)
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(brand.sp(60))
        self.txt_aciklama.setStyleSheet(input_css)
        form.addRow(lbl, self.txt_aciklama)

        layout.addLayout(form)
        layout.addStretch()

        # Buttons
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

        btn_olustur = QPushButton("Sayim Olustur")
        btn_olustur.setCursor(Qt.PointingHandCursor)
        btn_olustur.setFixedHeight(brand.sp(38))
        btn_olustur.setStyleSheet(f"""
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
        btn_olustur.clicked.connect(self._olustur)
        btn_layout.addWidget(btn_olustur)
        layout.addLayout(btn_layout)

    def _load_combos(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            self.cmb_depo.addItem("-- Seciniz --", None)
            cursor.execute("SELECT id, kod, ad FROM tanim.depolar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_depo.addItem(f"{row[1]} - {row[2]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _olustur(self):
        if not self.cmb_depo.currentData():
            QMessageBox.warning(self, "Uyari", "Depo secimi zorunludur!")
            return
        conn = None
        try:
            _ensure_sayim_tables()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 'SYM-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM stok.sayimlar), 0) + 1 AS VARCHAR), 4)")
            sayim_no = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO stok.sayimlar (sayim_no, sayim_tipi, depo_id, sayim_tarihi, aciklama, durum) VALUES (?, ?, ?, ?, ?, 'TASLAK')",
                (sayim_no, self.cmb_tip.currentText(), self.cmb_depo.currentData(),
                 self.date_sayim.date().toPython(), self.txt_aciklama.toPlainText().strip() or None)
            )
            conn.commit()
            self.accept()
            LogManager.log_insert('depo', 'stok.sayimlar', None, 'Sayim kaydi olustu')
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class SayimDetayDialog(QDialog):
    """Sayim detay ekrani - Grup bazli urun cekme ve miktar girisi"""
    def __init__(self, sayim_id, theme: dict, parent=None):
        super().__init__(parent)
        self.sayim_id = sayim_id
        self.theme = theme
        self.setWindowTitle("Sayim Detay")
        self.setMinimumSize(brand.sp(1100), brand.sp(700))
        self.setModal(True)
        _ensure_sayim_tables()
        self._setup_ui()
        self._load_header()
        self._load_grup_listesi()
        self._load_detaylar()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px;
                color: {brand.TEXT};
            }}
            QLineEdit:focus, QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
            QListWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                color: {brand.TEXT};
            }}
            QListWidget::item {{
                padding: {brand.SP_2}px;
                border-bottom: 1px solid {brand.BORDER};
            }}
            QListWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_4)

        # Header
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)
        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        self.lbl_title = QLabel("Sayim Detay")
        self.lbl_title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(self.lbl_title)
        header.addLayout(title_col)
        header.addStretch()

        self.lbl_durum = QLabel("")
        self.lbl_durum.setStyleSheet(
            f"padding: {brand.SP_1}px {brand.SP_4}px; "
            f"border-radius: {brand.R_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_BODY_SM}px;"
        )
        header.addWidget(self.lbl_durum)
        layout.addLayout(header)

        # Info bar
        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"padding: {brand.SP_2}px {brand.SP_3}px; "
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_SM}px;"
        )
        layout.addWidget(self.lbl_info)

        # Content: Sol grup listesi + Sag tablo
        content = QHBoxLayout()
        content.setSpacing(brand.SP_4)

        # Sol panel
        left_panel = QVBoxLayout()
        left_panel.setSpacing(brand.SP_3)
        lbl_grup = QLabel("Urun Grubu Sec")
        lbl_grup.setStyleSheet(
            f"font-size: {brand.FS_BODY}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"color: {brand.TEXT};"
        )
        left_panel.addWidget(lbl_grup)

        self.lst_gruplar = QListWidget()
        self.lst_gruplar.setMaximumWidth(brand.sp(250))
        self.lst_gruplar.setMinimumWidth(brand.sp(200))
        left_panel.addWidget(self.lst_gruplar, 1)

        btn_ekle = QPushButton("Grubu Sayima Ekle")
        btn_ekle.setCursor(Qt.PointingHandCursor)
        btn_ekle.setFixedHeight(brand.sp(38))
        btn_ekle.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        btn_ekle.clicked.connect(self._grup_ekle)
        left_panel.addWidget(btn_ekle)

        left_frame = QFrame()
        left_frame.setLayout(left_panel)
        content.addWidget(left_frame)

        # Sag panel
        right_panel = QVBoxLayout()
        right_panel.setSpacing(brand.SP_3)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)
        self.lbl_satir = QLabel("0 kalem")
        self.lbl_satir.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;"
        )
        toolbar.addWidget(self.lbl_satir)
        toolbar.addStretch()
        self.txt_ara = QLineEdit()
        self.txt_ara.setPlaceholderText("Urun ara...")
        self.txt_ara.setMaximumWidth(brand.sp(250))
        self.txt_ara.textChanged.connect(self._filtrele)
        toolbar.addWidget(self.txt_ara)
        right_panel.addLayout(toolbar)

        # Tablo
        self.tbl_detay = QTableWidget()
        self.tbl_detay.setColumnCount(8)
        self.tbl_detay.setHorizontalHeaderLabels(["Stok Kodu", "Urun Adi", "Grup", "Birim", "Sistem Stok", "Sayilan", "Fark", "Durum"])
        self.tbl_detay.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_detay.setColumnWidth(0, brand.sp(120))
        self.tbl_detay.setColumnWidth(2, brand.sp(100))
        self.tbl_detay.setColumnWidth(3, brand.sp(70))
        self.tbl_detay.setColumnWidth(4, brand.sp(100))
        self.tbl_detay.setColumnWidth(5, brand.sp(110))
        self.tbl_detay.setColumnWidth(6, brand.sp(90))
        self.tbl_detay.setColumnWidth(7, brand.sp(90))
        self.tbl_detay.verticalHeader().setVisible(False)
        self.tbl_detay.setShowGrid(False)
        self.tbl_detay.setAlternatingRowColors(True)
        self.tbl_detay.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_detay.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.tbl_detay.setStyleSheet(f"""
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
                padding: {brand.SP_3}px {brand.SP_2}px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """)
        right_panel.addWidget(self.tbl_detay, 1)

        right_frame = QFrame()
        right_frame.setLayout(right_panel)
        content.addWidget(right_frame, 1)
        layout.addLayout(content, 1)

        # Alt butonlar
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(brand.SP_3)

        btn_sil_grup = QPushButton("Secili Grubu Kaldir")
        btn_sil_grup.setCursor(Qt.PointingHandCursor)
        btn_sil_grup.setFixedHeight(brand.sp(38))
        btn_sil_grup.setStyleSheet(f"""
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
        btn_sil_grup.clicked.connect(self._grup_kaldir)

        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setCursor(Qt.PointingHandCursor)
        btn_kaydet.setFixedHeight(brand.sp(38))
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {brand.INFO};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #2563EB; }}
        """)
        btn_kaydet.clicked.connect(self._kaydet)

        btn_tamamla = QPushButton("Sayimi Tamamla")
        btn_tamamla.setCursor(Qt.PointingHandCursor)
        btn_tamamla.setFixedHeight(brand.sp(38))
        btn_tamamla.setStyleSheet(f"""
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
        btn_tamamla.clicked.connect(self._tamamla)

        btn_kapat = QPushButton("Kapat")
        btn_kapat.setCursor(Qt.PointingHandCursor)
        btn_kapat.setFixedHeight(brand.sp(38))
        btn_kapat.setStyleSheet(f"""
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
        btn_kapat.clicked.connect(self.accept)

        btn_bar.addWidget(btn_sil_grup)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_kaydet)
        btn_bar.addWidget(btn_tamamla)
        btn_bar.addWidget(btn_kapat)
        layout.addLayout(btn_bar)

    def _load_header(self):
        """Sayim bilgilerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT s.sayim_no, s.sayim_tipi, s.durum, d.kod + ' - ' + d.ad, FORMAT(s.sayim_tarihi, 'dd.MM.yyyy')
                FROM stok.sayimlar s LEFT JOIN tanim.depolar d ON s.depo_id = d.id WHERE s.id = ?""", (self.sayim_id,))
            row = cursor.fetchone()
            if row:
                self.lbl_title.setText(f"Sayim: {row[0]}")
                self.lbl_info.setText(f"Tip: {row[1]}  |  Depo: {row[3] or '-'}  |  Tarih: {row[4]}")
                durum = row[2]
                if durum == 'TASLAK':
                    self.lbl_durum.setText("TASLAK")
                    self.lbl_durum.setStyleSheet(
                        f"padding: {brand.SP_1}px {brand.SP_4}px; border-radius: {brand.R_SM}px; "
                        f"font-weight: {brand.FW_SEMIBOLD}; font-size: {brand.FS_BODY_SM}px; "
                        f"background: {brand.WARNING}; color: #000;"
                    )
                elif durum == 'DEVAM_EDIYOR':
                    self.lbl_durum.setText("DEVAM EDIYOR")
                    self.lbl_durum.setStyleSheet(
                        f"padding: {brand.SP_1}px {brand.SP_4}px; border-radius: {brand.R_SM}px; "
                        f"font-weight: {brand.FW_SEMIBOLD}; font-size: {brand.FS_BODY_SM}px; "
                        f"background: {brand.INFO}; color: white;"
                    )
                elif durum == 'TAMAMLANDI':
                    self.lbl_durum.setText("TAMAMLANDI")
                    self.lbl_durum.setStyleSheet(
                        f"padding: {brand.SP_1}px {brand.SP_4}px; border-radius: {brand.R_SM}px; "
                        f"font-weight: {brand.FW_SEMIBOLD}; font-size: {brand.FS_BODY_SM}px; "
                        f"background: {brand.SUCCESS}; color: white;"
                    )
        except Exception as e:
            self.lbl_info.setText(f"Hata: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_grup_listesi(self):
        """Urun tiplerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM stok.urun_tipleri WHERE aktif_mi = 1 ORDER BY sira_no, ad")
            rows = cursor.fetchall()
            for row in rows:
                item = QListWidgetItem(f"{row[1]} - {row[2]}")
                item.setData(Qt.UserRole, row[0])
                item.setData(Qt.UserRole + 1, row[2])
                self.lst_gruplar.addItem(item)
        except Exception:
            # urun_tipleri yoksa urun_tipi string'den unique degerler al
            conn2 = None
            try:
                conn2 = get_db_connection()
                cursor2 = conn2.cursor()
                cursor2.execute("SELECT DISTINCT urun_tipi FROM stok.urunler WHERE urun_tipi IS NOT NULL AND aktif_mi = 1 ORDER BY urun_tipi")
                rows = cursor2.fetchall()
                for row in rows:
                    item = QListWidgetItem(row[0])
                    item.setData(Qt.UserRole, row[0])
                    item.setData(Qt.UserRole + 1, row[0])
                    self.lst_gruplar.addItem(item)
            except Exception:
                pass
            finally:
                if conn2:
                    try:
                        conn2.close()
                    except Exception:
                        pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _grup_ekle(self):
        """Secili grubu sayima ekle - o gruptaki urunleri detay tablosuna aktar"""
        sel = self.lst_gruplar.currentItem()
        if not sel:
            QMessageBox.warning(self, "Uyari", "Lutfen bir urun grubu secin!")
            return

        grup_id = sel.data(Qt.UserRole)
        grup_adi = sel.data(Qt.UserRole + 1)

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT depo_id FROM stok.sayimlar WHERE id = ?", (self.sayim_id,))
            depo_id = cursor.fetchone()[0]

            if isinstance(grup_id, int):
                cursor.execute("""
                    SELECT u.id, u.urun_kodu, u.urun_adi, ut.ad, b.ad,
                           ISNULL((SELECT SUM(sb.miktar) FROM stok.stok_bakiye sb WHERE sb.urun_id = u.id AND sb.depo_id = ?), 0) as sistem_stok
                    FROM stok.urunler u
                    LEFT JOIN stok.urun_tipleri ut ON u.urun_tipi_id = ut.id
                    LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                    WHERE u.urun_tipi_id = ? AND ISNULL(u.aktif_mi, 1) = 1 AND ISNULL(u.silindi_mi, 0) = 0
                    ORDER BY u.urun_kodu
                """, (depo_id, grup_id))
            else:
                cursor.execute("""
                    SELECT u.id, u.urun_kodu, u.urun_adi, u.urun_tipi, b.ad,
                           ISNULL((SELECT SUM(sb.miktar) FROM stok.stok_bakiye sb WHERE sb.urun_id = u.id AND sb.depo_id = ?), 0) as sistem_stok
                    FROM stok.urunler u
                    LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                    WHERE u.urun_tipi = ? AND ISNULL(u.aktif_mi, 1) = 1 AND ISNULL(u.silindi_mi, 0) = 0
                    ORDER BY u.urun_kodu
                """, (depo_id, grup_id))

            urunler = cursor.fetchall()
            if not urunler:
                QMessageBox.information(self, "Bilgi", f"'{grup_adi}' grubunda urun bulunamadi.")
                return

            cursor.execute("SELECT urun_id FROM stok.sayim_detaylari WHERE sayim_id = ?", (self.sayim_id,))
            mevcut = {row[0] for row in cursor.fetchall()}

            eklenen = 0
            for urun in urunler:
                urun_id = urun[0]
                if urun_id in mevcut:
                    continue
                sistem_stok = float(urun[5] or 0)
                cursor.execute("""
                    INSERT INTO stok.sayim_detaylari (sayim_id, urun_id, urun_kodu, urun_adi, urun_tipi, birim, sistem_miktari, durum)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'BEKLIYOR')
                """, (self.sayim_id, urun_id, urun[1], urun[2], urun[3], urun[4], sistem_stok))
                eklenen += 1

            if eklenen > 0:
                cursor.execute("UPDATE stok.sayimlar SET durum = 'DEVAM_EDIYOR' WHERE id = ? AND durum = 'TASLAK'", (self.sayim_id,))

            conn.commit()
            self._load_detaylar()
            self._load_header()
            QMessageBox.information(self, "Bilgi", f"'{grup_adi}' grubundan {eklenen} urun eklendi." + (f" ({len(urunler) - eklenen} zaten mevcut)" if len(urunler) - eklenen > 0 else ""))
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _grup_kaldir(self):
        """Secili gruptaki urunleri sayimdan kaldir"""
        sel = self.lst_gruplar.currentItem()
        if not sel:
            QMessageBox.warning(self, "Uyari", "Lutfen kaldirilacak grubu secin!")
            return
        grup_adi = sel.data(Qt.UserRole + 1)
        cevap = QMessageBox.question(self, "Onay", f"'{grup_adi}' grubundaki tum urunler sayimdan kaldirilsin mi?", QMessageBox.Yes | QMessageBox.No)
        if cevap != QMessageBox.Yes:
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stok.sayim_detaylari WHERE sayim_id = ? AND urun_tipi = ?", (self.sayim_id, grup_adi))
            conn.commit()
            self._load_detaylar()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_detaylar(self):
        """Sayim detaylarini tabloya yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, urun_kodu, urun_adi, urun_tipi, birim, sistem_miktari, sayilan_miktar, fark, durum
                FROM stok.sayim_detaylari WHERE sayim_id = ? ORDER BY urun_tipi, urun_kodu
            """, (self.sayim_id,))
            self.detay_rows = cursor.fetchall()
            self._display_detaylar(self.detay_rows)
        except Exception as e:
            self.detay_rows = []
            self.lbl_satir.setText(f"Hata: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _display_detaylar(self, rows):
        self.tbl_detay.setRowCount(len(rows))
        bekliyor = sayildi = 0

        cell_input_css = f"""
            background: {brand.BG_INPUT};
            border: 1px solid {brand.BORDER};
            border-radius: {brand.R_SM}px;
            padding: {brand.SP_1}px {brand.SP_2}px;
            color: {brand.TEXT};
            font-size: {brand.FS_BODY}px;
        """

        for i, row in enumerate(rows):
            detay_id = row[0]

            self.tbl_detay.setItem(i, 0, QTableWidgetItem(str(row[1] or "")))
            self.tbl_detay.setItem(i, 1, QTableWidgetItem(str(row[2] or "")))
            self.tbl_detay.setItem(i, 2, QTableWidgetItem(str(row[3] or "")))
            self.tbl_detay.setItem(i, 3, QTableWidgetItem(str(row[4] or "")))

            sistem = float(row[5] or 0)
            item_sistem = QTableWidgetItem(f"{sistem:,.2f}")
            item_sistem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_detay.setItem(i, 4, item_sistem)

            spin = QDoubleSpinBox()
            spin.setRange(0, 9999999)
            spin.setDecimals(2)
            spin.setStyleSheet(cell_input_css)
            spin.setProperty("detay_id", detay_id)
            spin.setProperty("sistem", sistem)
            spin.blockSignals(True)
            if row[6] is not None:
                spin.setValue(float(row[6]))
            spin.blockSignals(False)
            spin.setProperty("dirty", False)
            spin.valueChanged.connect(
                lambda val, r=i, sp=spin: (sp.setProperty("dirty", True),
                                            self._miktar_degisti(r, sp))
            )
            self.tbl_detay.setCellWidget(i, 5, spin)

            fark_val = float(row[7]) if row[7] is not None else None
            item_fark = QTableWidgetItem(f"{fark_val:,.2f}" if fark_val is not None else "-")
            item_fark.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if fark_val is not None and fark_val != 0:
                item_fark.setForeground(QColor(brand.ERROR) if fark_val < 0 else QColor(brand.WARNING))
            self.tbl_detay.setItem(i, 6, item_fark)

            durum = row[8]
            item_durum = QTableWidgetItem(durum or "")
            if durum == 'BEKLIYOR':
                item_durum.setForeground(QColor(brand.TEXT_DIM))
                bekliyor += 1
            elif durum == 'SAYILDI':
                item_durum.setForeground(QColor(brand.SUCCESS))
                sayildi += 1
            self.tbl_detay.setItem(i, 7, item_durum)

            self.tbl_detay.setRowHeight(i, brand.sp(42))

        self.lbl_satir.setText(f"{len(rows)} kalem | Bekliyor: {bekliyor} | Sayildi: {sayildi}")

    def _miktar_degisti(self, row, spin):
        """Sayilan miktar degistiginde fark hesapla"""
        sistem = spin.property("sistem") or 0
        sayilan = spin.value()
        fark = sayilan - sistem
        item_fark = QTableWidgetItem(f"{fark:,.2f}")
        item_fark.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if fark != 0:
            item_fark.setForeground(QColor(brand.ERROR) if fark < 0 else QColor(brand.WARNING))
        self.tbl_detay.setItem(row, 6, item_fark)
        self.tbl_detay.setItem(row, 7, QTableWidgetItem("SAYILDI"))

    def _filtrele(self, text):
        """Tabloda ara"""
        text = text.lower()
        for i in range(self.tbl_detay.rowCount()):
            kod = (self.tbl_detay.item(i, 0).text() if self.tbl_detay.item(i, 0) else "").lower()
            ad = (self.tbl_detay.item(i, 1).text() if self.tbl_detay.item(i, 1) else "").lower()
            self.tbl_detay.setRowHidden(i, text not in kod and text not in ad)

    def _kaydet(self):
        """Sayilan miktarlari kaydet (sadece kullanici tarafindan degistirilen satirlar)"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            saved = 0
            for i in range(self.tbl_detay.rowCount()):
                spin = self.tbl_detay.cellWidget(i, 5)
                if spin is None or not spin.property("dirty"):
                    continue
                detay_id = spin.property("detay_id")
                sayilan = spin.value()
                sistem = spin.property("sistem") or 0
                fark = sayilan - sistem
                cursor.execute("""
                    UPDATE stok.sayim_detaylari SET sayilan_miktar = ?, fark = ?, durum = 'SAYILDI'
                    WHERE id = ?
                """, (sayilan, fark, detay_id))
                saved += 1
            conn.commit()
            self._load_detaylar()
            if saved:
                QMessageBox.information(self, "Bilgi", f"{saved} kalem kaydedildi.")
            else:
                QMessageBox.information(self, "Bilgi", "Kaydedilecek degisiklik yok.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _tamamla(self):
        """Sayimi tamamla ve fark olan kalemleri stok hareketine yansit"""
        cevap = QMessageBox.question(self, "Onay",
            "Sayim tamamlansin mi?\n\nFark olan kalemler icin stok hareketi olusturulacak.\nTamamlanan sayimda degisiklik yapilamaz.",
            QMessageBox.Yes | QMessageBox.No)
        if cevap != QMessageBox.Yes:
            return
        conn = None
        try:
            self._kaydet_silent()
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT depo_id, sayim_no FROM stok.sayimlar WHERE id = ?", (self.sayim_id,))
            sayim_row = cursor.fetchone()
            depo_id = sayim_row[0]
            sayim_no = sayim_row[1]

            cursor.execute("""
                SELECT id, urun_id, urun_kodu, urun_adi, sayilan_miktar, fark
                FROM stok.sayim_detaylari
                WHERE sayim_id = ? AND fark IS NOT NULL AND fark <> 0
            """, (self.sayim_id,))
            fark_rows = cursor.fetchall()

            fazla = eksik = 0
            if fark_rows:
                for row in fark_rows:
                    detay_id, urun_id, urun_kodu, urun_adi, sayilan, fark = row

                    if fark > 0:
                        hareket_tipi = 'SAYIM_FAZLA'
                        fazla += 1
                    else:
                        hareket_tipi = 'SAYIM_EKSIK'
                        eksik += 1

                    cursor.execute("""
                        SELECT TOP 1 id, lot_no, miktar FROM stok.stok_bakiye
                        WHERE urun_id = ? AND depo_id = ?
                        ORDER BY giris_tarihi ASC
                    """, (urun_id, depo_id))
                    bakiye = cursor.fetchone()

                    if bakiye:
                        yeni_miktar = bakiye[2] + fark
                        if yeni_miktar < 0:
                            yeni_miktar = 0
                        cursor.execute("""UPDATE stok.stok_bakiye SET miktar = ?,
                            son_hareket_tarihi = GETDATE() WHERE id = ?""", (yeni_miktar, bakiye[0]))
                        ref_lot = bakiye[1]
                    else:
                        if fark > 0:
                            ref_lot = f"SAYIM-{sayim_no}-{urun_kodu}"
                            cursor.execute("""
                                INSERT INTO stok.stok_bakiye
                                (urun_id, depo_id, lot_no, miktar, rezerve_miktar,
                                 bloke_mi, kalite_durumu, durum_kodu,
                                 giris_tarihi, son_hareket_tarihi)
                                VALUES (?, ?, ?, ?, 0, 0, 'ONAYLANDI', 'SAYIM', GETDATE(), GETDATE())
                            """, (urun_id, depo_id, ref_lot, fark))
                        else:
                            ref_lot = 'YOK'

                    cursor.execute("""
                        INSERT INTO stok.stok_hareketleri
                        (uuid, hareket_tipi, hareket_nedeni, tarih, urun_id, depo_id,
                         miktar, birim_id, lot_no, referans_tip, referans_id, aciklama, olusturma_tarihi)
                        VALUES (NEWID(), ?, 'SAYIM', GETDATE(), ?, ?, ?, 1, ?, 'SAYIM', ?, ?, GETDATE())
                    """, (hareket_tipi, urun_id, depo_id, abs(fark), ref_lot, self.sayim_id,
                          f"Sayim {'fazlasi' if fark > 0 else 'eksigi'} - {sayim_no}"))

            cursor.execute("UPDATE stok.sayimlar SET durum = 'TAMAMLANDI' WHERE id = ?", (self.sayim_id,))
            conn.commit()
            self._load_header()

            msg = "Sayim tamamlandi."
            if fark_rows:
                msg += f"\n\nStok hareketleri olusturuldu:\n  Fazla: {fazla} kalem\n  Eksik: {eksik} kalem"
            QMessageBox.information(self, "Bilgi", msg)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _kaydet_silent(self):
        """Sessiz kaydet (sadece kullanici tarafindan degistirilen satirlar)"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            for i in range(self.tbl_detay.rowCount()):
                spin = self.tbl_detay.cellWidget(i, 5)
                if spin is None or not spin.property("dirty"):
                    continue
                detay_id = spin.property("detay_id")
                sayilan = spin.value()
                sistem = spin.property("sistem") or 0
                fark = sayilan - sistem
                cursor.execute("UPDATE stok.sayim_detaylari SET sayilan_miktar = ?, fark = ?, durum = 'SAYILDI' WHERE id = ?", (sayilan, fark, detay_id))
            conn.commit()
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class DepoSayimPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        _ensure_sayim_tables()
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # Header
        header = self.create_page_header(
            "Stok Sayim",
            "Depo sayim islemleri ve fark raporlari"
        )
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"padding: {brand.SP_2}px {brand.SP_4}px; "
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_SM}px;"
        )
        header.addWidget(self.stat_label)
        layout.addLayout(header)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)

        btn_yeni = self.create_primary_button("Yeni Sayim")
        btn_yeni.clicked.connect(self._yeni)
        toolbar.addWidget(btn_yeni)
        toolbar.addStretch()

        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tumu", "TASLAK", "DEVAM_EDIYOR", "TAMAMLANDI"])
        self.cmb_durum.setMinimumWidth(brand.sp(140))
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        toolbar.addWidget(self.cmb_durum)

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        toolbar.addWidget(btn_yenile)
        layout.addLayout(toolbar)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Sayim No", "Tip", "Depo", "Tarih", "Durum", "Islem"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(1, brand.sp(150))
        self.table.setColumnWidth(2, brand.sp(120))
        self.table.setColumnWidth(4, brand.sp(100))
        self.table.setColumnWidth(5, brand.sp(120))
        self.table.setColumnWidth(6, brand.sp(120))
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
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
        layout.addWidget(self.table, 1)

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT s.id, s.sayim_no, s.sayim_tipi, d.kod + ' - ' + d.ad, FORMAT(s.sayim_tarihi, 'dd.MM.yyyy'), s.durum
                FROM stok.sayimlar s LEFT JOIN tanim.depolar d ON s.depo_id = d.id ORDER BY s.sayim_tarihi DESC""")
            self.all_rows = cursor.fetchall()
            self._display_data(self.all_rows)
        except Exception:
            self.all_rows = []
            self.stat_label.setText("Tablo bulunamadi")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        taslak = devam = 0
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "")
                if j == 5:
                    if val == 'TASLAK':
                        item.setForeground(QColor(brand.WARNING))
                        taslak += 1
                    elif val == 'DEVAM_EDIYOR':
                        item.setForeground(QColor(brand.INFO))
                        devam += 1
                    elif val == 'TAMAMLANDI':
                        item.setForeground(QColor(brand.SUCCESS))
                self.table.setItem(i, j, item)
            widget = self.create_action_buttons([
                ("Detay", "Detay", lambda checked, rid=row[0]: self._detay(rid), "view"),
            ])
            self.table.setCellWidget(i, 6, widget)
            self.table.setRowHeight(i, brand.sp(42))
        self.stat_label.setText(f"Toplam: {len(rows)} | Taslak: {taslak} | Devam: {devam}")

    def _filter(self):
        durum = self.cmb_durum.currentText()
        if durum == "Tumu":
            self._display_data(self.all_rows)
        else:
            self._display_data([r for r in self.all_rows if r[5] == durum])

    def _yeni(self):
        dialog = SayimOlusturDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _detay(self, sayim_id):
        dialog = SayimDetayDialog(sayim_id, self.theme, self)
        dialog.exec()
        self._load_data()
