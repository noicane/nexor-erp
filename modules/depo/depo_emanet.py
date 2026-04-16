# -*- coding: utf-8 -*-
"""
NEXOR ERP - Emanet Stoklar Sayfasi
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QWidget, QDialog,
    QFormLayout, QDateEdit, QDoubleSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand


class EmanetStokDialog(QDialog):
    def __init__(self, theme: dict, parent=None, emanet_id=None):
        super().__init__(parent)
        self.theme = theme
        self.emanet_id = emanet_id
        self.setWindowTitle("Emanet Stok Kaydi")
        self.setMinimumSize(brand.sp(500), brand.sp(500))
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if emanet_id:
            self._load_data()

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
        title = QLabel("Emanet Stok Kaydi")
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
            QComboBox, QDateEdit, QDoubleSpinBox, QLineEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus, QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """

        form = QFormLayout()
        form.setSpacing(brand.SP_3)
        label_style = f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; font-weight: {brand.FW_MEDIUM};"

        lbl = QLabel("Cari *")
        lbl.setStyleSheet(label_style)
        self.cmb_cari = QComboBox()
        self.cmb_cari.setStyleSheet(input_css)
        form.addRow(lbl, self.cmb_cari)

        lbl = QLabel("Stok *")
        lbl.setStyleSheet(label_style)
        self.cmb_stok = QComboBox()
        self.cmb_stok.setStyleSheet(input_css)
        form.addRow(lbl, self.cmb_stok)

        lbl = QLabel("Miktar *")
        lbl.setStyleSheet(label_style)
        self.spin_miktar = QDoubleSpinBox()
        self.spin_miktar.setRange(0.01, 9999999)
        self.spin_miktar.setDecimals(2)
        self.spin_miktar.setStyleSheet(input_css)
        form.addRow(lbl, self.spin_miktar)

        lbl = QLabel("Giris Tarihi")
        lbl.setStyleSheet(label_style)
        self.date_giris = QDateEdit()
        self.date_giris.setDate(QDate.currentDate())
        self.date_giris.setCalendarPopup(True)
        self.date_giris.setStyleSheet(input_css)
        form.addRow(lbl, self.date_giris)

        lbl = QLabel("Planlanan Iade")
        lbl.setStyleSheet(label_style)
        self.date_iade = QDateEdit()
        self.date_iade.setDate(QDate.currentDate().addMonths(1))
        self.date_iade.setCalendarPopup(True)
        self.date_iade.setStyleSheet(input_css)
        form.addRow(lbl, self.date_iade)

        lbl = QLabel("Aciklama")
        lbl.setStyleSheet(label_style)
        self.txt_aciklama = QLineEdit()
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
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            self.cmb_cari.addItem("-- Seciniz --", None)
            cursor.execute("SELECT id, kod, unvan FROM cari.cariler WHERE aktif_mi = 1 ORDER BY unvan")
            for row in cursor.fetchall():
                self.cmb_cari.addItem(f"{row[1]} - {row[2][:30]}", row[0])
            self.cmb_stok.addItem("-- Seciniz --", None)
            cursor.execute("SELECT id, urun_kodu, urun_adi FROM stok.urunler WHERE aktif_mi = 1 ORDER BY urun_kodu")
            for row in cursor.fetchall():
                self.cmb_stok.addItem(f"{row[1]} - {row[2][:30]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT cari_id, urun_id, miktar, giris_tarihi, planlanan_iade_tarihi, aciklama FROM stok.emanet_stoklar WHERE id = ?", (self.emanet_id,))
            row = cursor.fetchone()
            if row:
                if row[0]:
                    idx = self.cmb_cari.findData(row[0])
                    if idx >= 0:
                        self.cmb_cari.setCurrentIndex(idx)
                if row[1]:
                    idx = self.cmb_stok.findData(row[1])
                    if idx >= 0:
                        self.cmb_stok.setCurrentIndex(idx)
                self.spin_miktar.setValue(float(row[2] or 0))
                if row[3]:
                    self.date_giris.setDate(QDate(row[3].year, row[3].month, row[3].day))
                if row[4]:
                    self.date_iade.setDate(QDate(row[4].year, row[4].month, row[4].day))
                self.txt_aciklama.setText(row[5] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _save(self):
        if not self.cmb_cari.currentData() or not self.cmb_stok.currentData():
            QMessageBox.warning(self, "Uyari", "Cari ve Stok secimi zorunludur!")
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if self.emanet_id:
                cursor.execute(
                    "UPDATE stok.emanet_stoklar SET cari_id = ?, urun_id = ?, miktar = ?, giris_tarihi = ?, planlanan_iade_tarihi = ?, aciklama = ? WHERE id = ?",
                    (self.cmb_cari.currentData(), self.cmb_stok.currentData(), self.spin_miktar.value(),
                     self.date_giris.date().toPython(), self.date_iade.date().toPython(),
                     self.txt_aciklama.text().strip() or None, self.emanet_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO stok.emanet_stoklar (cari_id, urun_id, miktar, giris_tarihi, planlanan_iade_tarihi, aciklama, durum) VALUES (?, ?, ?, ?, ?, ?, 'AKTIF')",
                    (self.cmb_cari.currentData(), self.cmb_stok.currentData(), self.spin_miktar.value(),
                     self.date_giris.date().toPython(), self.date_iade.date().toPython(),
                     self.txt_aciklama.text().strip() or None)
                )
            conn.commit()
            self.accept()
            LogManager.log_insert('depo', 'stok.emanet_stoklar', None, 'Emanet stok kaydi olustu')
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class DepoEmanetPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # Header
        header = self.create_page_header(
            "Emanet Stoklar",
            "Musteri emanet stok takibi"
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

        btn_yeni = self.create_primary_button("Yeni Emanet")
        btn_yeni.clicked.connect(self._yeni)
        toolbar.addWidget(btn_yeni)

        btn_geciken = QPushButton("Suresi Gecenler")
        btn_geciken.setCursor(Qt.PointingHandCursor)
        btn_geciken.setFixedHeight(brand.sp(38))
        btn_geciken.setStyleSheet(f"""
            QPushButton {{
                background: {brand.WARNING};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #D97706; }}
        """)
        btn_geciken.clicked.connect(self._show_geciken)
        toolbar.addWidget(btn_geciken)
        toolbar.addStretch()

        self.txt_arama = QLineEdit()
        self.txt_arama.setPlaceholderText("Cari veya stok ara...")
        self.txt_arama.setFixedWidth(brand.sp(200))
        self.txt_arama.textChanged.connect(self._filter)
        toolbar.addWidget(self.txt_arama)

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        toolbar.addWidget(btn_yenile)
        layout.addLayout(toolbar)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Cari", "Stok", "Miktar", "Giris", "Plan. Iade", "Durum", "Islem"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(3, brand.sp(100))
        self.table.setColumnWidth(4, brand.sp(100))
        self.table.setColumnWidth(5, brand.sp(100))
        self.table.setColumnWidth(6, brand.sp(100))
        self.table.setColumnWidth(7, brand.sp(120))
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
            cursor.execute("""SELECT e.id, c.unvan, u.urun_kodu + ' - ' + u.urun_adi, e.miktar, FORMAT(e.giris_tarihi, 'dd.MM.yyyy'),
                FORMAT(e.planlanan_iade_tarihi, 'dd.MM.yyyy'), e.durum, DATEDIFF(DAY, GETDATE(), e.planlanan_iade_tarihi)
                FROM stok.emanet_stoklar e
                LEFT JOIN cari.cariler c ON e.cari_id = c.id
                LEFT JOIN stok.urunler u ON e.urun_id = u.id
                WHERE e.durum = 'AKTIF' ORDER BY e.planlanan_iade_tarihi ASC""")
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
        geciken = 0
        for i, row in enumerate(rows):
            for j in range(7):
                item = QTableWidgetItem(str(row[j]) if row[j] else "")
                if j == 6:
                    kalan = row[7] if len(row) > 7 else 0
                    if kalan is not None and kalan < 0:
                        item.setForeground(QColor(brand.ERROR))
                        item.setText("GECIKMIS")
                        geciken += 1
                    elif kalan is not None and kalan <= 7:
                        item.setForeground(QColor(brand.WARNING))
                    else:
                        item.setForeground(QColor(brand.SUCCESS))
                self.table.setItem(i, j, item)
            widget = self.create_action_buttons([
                ("Duzenle", "Duzenle", lambda checked, rid=row[0]: self._duzenle(rid), "edit"),
                ("Iade", "Iade Et", lambda checked, rid=row[0]: self._iade(rid), "success"),
            ])
            self.table.setCellWidget(i, 7, widget)
            self.table.setRowHeight(i, brand.sp(42))
        self.stat_label.setText(f"Toplam: {len(rows)} | Geciken: {geciken}")

    def _filter(self):
        arama = self.txt_arama.text().lower()
        if not arama:
            self._display_data(self.all_rows)
        else:
            self._display_data([r for r in self.all_rows if arama in str(r[1]).lower() or arama in str(r[2]).lower()])

    def _show_geciken(self):
        self._display_data([r for r in self.all_rows if r[7] is not None and r[7] < 0])

    def _yeni(self):
        dialog = EmanetStokDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _duzenle(self, emanet_id):
        dialog = EmanetStokDialog(self.theme, self, emanet_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _iade(self, emanet_id):
        if QMessageBox.question(self, "Onay", "Emanet stok iade edilsin mi?") != QMessageBox.Yes:
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE stok.emanet_stoklar SET durum = 'IADE', iade_tarihi = GETDATE() WHERE id = ?", (emanet_id,))
            conn.commit()
            self._load_data()
            LogManager.log_update('depo', 'stok.emanet_stoklar', None, 'Durum guncellendi')
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
