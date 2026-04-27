# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Çevre Su ve Enerji Tüketimi
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox, QDialog, QFormLayout, QDateEdit, QDoubleSpinBox, QSpinBox, QTabWidget, QAbstractItemView)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QColor
from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand

def get_modern_style(theme: dict) -> dict:
    return {
        'card_bg': brand.BG_CARD,
        'input_bg': brand.BG_INPUT,
        'border': brand.BORDER,
        'text': brand.TEXT,
        'text_secondary': brand.TEXT_MUTED,
        'text_muted': brand.TEXT_DIM,
        'primary': brand.PRIMARY,
        'primary_hover': brand.PRIMARY_HOVER,
        'success': brand.SUCCESS,
        'warning': brand.WARNING,
        'danger': brand.ERROR,
        'error': brand.ERROR,
        'info': brand.INFO,
        'bg_main': brand.BG_MAIN,
        'bg_hover': brand.BG_HOVER,
        'border_light': brand.BORDER_HARD,
    }

class SuTuketimDialog(QDialog):
    def __init__(self, theme: dict, parent=None, kayit_id=None):
        super().__init__(parent)
        self.theme = theme; self.s = get_modern_style(theme); self.kayit_id = kayit_id
        self.setWindowTitle("Su Tüketimi Kaydı"); self.setMinimumSize(500, 450); self.setModal(True); self._setup_ui()
        if kayit_id: self._load_data()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }} QLabel {{ color: {s['text']}; }} QLineEdit, QDateEdit, QDoubleSpinBox, QSpinBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; }}")
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(16)
        header = QHBoxLayout(); icon = QLabel("💧"); icon.setStyleSheet("font-size: 28px;"); header.addWidget(icon)
        title = QLabel(self.windowTitle()); title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {s['text']};"); header.addWidget(title); header.addStretch(); layout.addLayout(header)
        form = QFormLayout(); form.setSpacing(12); label_style = f"color: {s['text_secondary']}; font-size: 13px;"
        lbl = QLabel("Sayaç No"); lbl.setStyleSheet(label_style); self.txt_sayac_id = QLineEdit(); form.addRow(lbl, self.txt_sayac_id)
        lbl = QLabel("Sayaç Adı"); lbl.setStyleSheet(label_style); self.txt_sayac_adi = QLineEdit(); form.addRow(lbl, self.txt_sayac_adi)
        lbl = QLabel("Okuma Tarihi *"); lbl.setStyleSheet(label_style); self.date_okuma = QDateEdit(); self.date_okuma.setDate(QDate.currentDate()); self.date_okuma.setCalendarPopup(True); form.addRow(lbl, self.date_okuma)
        lbl = QLabel("Önceki Okuma"); lbl.setStyleSheet(label_style); self.spin_onceki = QDoubleSpinBox(); self.spin_onceki.setRange(0, 9999999); self.spin_onceki.setDecimals(2); self.spin_onceki.setSuffix(" m³"); form.addRow(lbl, self.spin_onceki)
        lbl = QLabel("Güncel Okuma *"); lbl.setStyleSheet(label_style); self.spin_guncel = QDoubleSpinBox(); self.spin_guncel.setRange(0, 9999999); self.spin_guncel.setDecimals(2); self.spin_guncel.setSuffix(" m³"); form.addRow(lbl, self.spin_guncel)
        lbl = QLabel("Dönem Ay"); lbl.setStyleSheet(label_style); self.spin_ay = QSpinBox(); self.spin_ay.setRange(1, 12); self.spin_ay.setValue(QDate.currentDate().month()); form.addRow(lbl, self.spin_ay)
        lbl = QLabel("Dönem Yıl"); lbl.setStyleSheet(label_style); self.spin_yil = QSpinBox(); self.spin_yil.setRange(2020, 2050); self.spin_yil.setValue(QDate.currentDate().year()); form.addRow(lbl, self.spin_yil)
        lbl = QLabel("Notlar"); lbl.setStyleSheet(label_style); self.txt_notlar = QLineEdit(); form.addRow(lbl, self.txt_notlar)
        layout.addLayout(form); layout.addStretch()
        btn_layout = QHBoxLayout(); btn_layout.addStretch()
        btn_iptal = QPushButton("İptal"); btn_iptal.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }}"); btn_iptal.clicked.connect(self.reject); btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾  Kaydet"); btn_kaydet.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}"); btn_kaydet.clicked.connect(self._save); btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT sayac_id, sayac_adi, okuma_tarihi, onceki_okuma, guncel_okuma, donem_ay, donem_yil, notlar FROM cevre.su_tuketimi WHERE id = ?", (self.kayit_id,))
            row = cursor.fetchone(); conn.close()
            if row:
                self.txt_sayac_id.setText(row[0] or ""); self.txt_sayac_adi.setText(row[1] or "")
                if row[2]: self.date_okuma.setDate(QDate(row[2].year, row[2].month, row[2].day))
                self.spin_onceki.setValue(float(row[3] or 0)); self.spin_guncel.setValue(float(row[4] or 0))
                if row[5]: self.spin_ay.setValue(row[5])
                if row[6]: self.spin_yil.setValue(row[6])
                self.txt_notlar.setText(row[7] or "")
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _save(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            if self.kayit_id:
                cursor.execute("UPDATE cevre.su_tuketimi SET sayac_id = ?, sayac_adi = ?, okuma_tarihi = ?, onceki_okuma = ?, guncel_okuma = ?, donem_ay = ?, donem_yil = ?, notlar = ? WHERE id = ?", (self.txt_sayac_id.text().strip() or None, self.txt_sayac_adi.text().strip() or None, self.date_okuma.date().toPython(), self.spin_onceki.value(), self.spin_guncel.value(), self.spin_ay.value(), self.spin_yil.value(), self.txt_notlar.text().strip() or None, self.kayit_id))
            else:
                cursor.execute("INSERT INTO cevre.su_tuketimi (sayac_id, sayac_adi, okuma_tarihi, onceki_okuma, guncel_okuma, donem_ay, donem_yil, notlar) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (self.txt_sayac_id.text().strip() or None, self.txt_sayac_adi.text().strip() or None, self.date_okuma.date().toPython(), self.spin_onceki.value(), self.spin_guncel.value(), self.spin_ay.value(), self.spin_yil.value(), self.txt_notlar.text().strip() or None))
            conn.commit(); conn.close(); self.accept()
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))

class EnerjiTuketimDialog(QDialog):
    def __init__(self, theme: dict, parent=None, kayit_id=None):
        super().__init__(parent)
        self.theme = theme; self.s = get_modern_style(theme); self.kayit_id = kayit_id
        self.setWindowTitle("Enerji Tüketimi Kaydı"); self.setMinimumSize(500, 500); self.setModal(True); self._setup_ui()
        if kayit_id: self._load_data()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }} QLabel {{ color: {s['text']}; }} QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; }}")
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(16)
        header = QHBoxLayout(); icon = QLabel("⚡"); icon.setStyleSheet("font-size: 28px;"); header.addWidget(icon)
        title = QLabel(self.windowTitle()); title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {s['text']};"); header.addWidget(title); header.addStretch(); layout.addLayout(header)
        form = QFormLayout(); form.setSpacing(12); label_style = f"color: {s['text_secondary']}; font-size: 13px;"
        lbl = QLabel("Enerji Tipi *"); lbl.setStyleSheet(label_style); self.cmb_tip = QComboBox(); self.cmb_tip.addItems(["ELEKTRIK", "DOGALGAZ", "LPG", "MOTORIN"]); self.cmb_tip.currentIndexChanged.connect(self._on_tip_changed); form.addRow(lbl, self.cmb_tip)
        lbl = QLabel("Sayaç No"); lbl.setStyleSheet(label_style); self.txt_sayac_id = QLineEdit(); form.addRow(lbl, self.txt_sayac_id)
        lbl = QLabel("Sayaç Adı"); lbl.setStyleSheet(label_style); self.txt_sayac_adi = QLineEdit(); form.addRow(lbl, self.txt_sayac_adi)
        lbl = QLabel("Okuma Tarihi *"); lbl.setStyleSheet(label_style); self.date_okuma = QDateEdit(); self.date_okuma.setDate(QDate.currentDate()); self.date_okuma.setCalendarPopup(True); form.addRow(lbl, self.date_okuma)
        lbl = QLabel("Önceki Okuma"); lbl.setStyleSheet(label_style); self.spin_onceki = QDoubleSpinBox(); self.spin_onceki.setRange(0, 99999999); self.spin_onceki.setDecimals(2); form.addRow(lbl, self.spin_onceki)
        lbl = QLabel("Güncel Okuma *"); lbl.setStyleSheet(label_style); self.spin_guncel = QDoubleSpinBox(); self.spin_guncel.setRange(0, 99999999); self.spin_guncel.setDecimals(2); form.addRow(lbl, self.spin_guncel)
        lbl = QLabel("Birim"); lbl.setStyleSheet(label_style); self.txt_birim = QLineEdit("kWh"); form.addRow(lbl, self.txt_birim)
        lbl = QLabel("Dönem Ay"); lbl.setStyleSheet(label_style); self.spin_ay = QSpinBox(); self.spin_ay.setRange(1, 12); self.spin_ay.setValue(QDate.currentDate().month()); form.addRow(lbl, self.spin_ay)
        lbl = QLabel("Dönem Yıl"); lbl.setStyleSheet(label_style); self.spin_yil = QSpinBox(); self.spin_yil.setRange(2020, 2050); self.spin_yil.setValue(QDate.currentDate().year()); form.addRow(lbl, self.spin_yil)
        layout.addLayout(form); layout.addStretch()
        btn_layout = QHBoxLayout(); btn_layout.addStretch()
        btn_iptal = QPushButton("İptal"); btn_iptal.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }}"); btn_iptal.clicked.connect(self.reject); btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾  Kaydet"); btn_kaydet.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}"); btn_kaydet.clicked.connect(self._save); btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _on_tip_changed(self):
        birimler = {"ELEKTRIK": "kWh", "DOGALGAZ": "m³", "LPG": "kg", "MOTORIN": "lt"}
        self.txt_birim.setText(birimler.get(self.cmb_tip.currentText(), ""))
    
    def _load_data(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT enerji_tipi, sayac_id, sayac_adi, okuma_tarihi, onceki_okuma, guncel_okuma, birim, donem_ay, donem_yil FROM cevre.enerji_tuketimi WHERE id = ?", (self.kayit_id,))
            row = cursor.fetchone(); conn.close()
            if row:
                if row[0]: idx = self.cmb_tip.findText(row[0]); self.cmb_tip.setCurrentIndex(idx) if idx >= 0 else None
                self.txt_sayac_id.setText(row[1] or ""); self.txt_sayac_adi.setText(row[2] or "")
                if row[3]: self.date_okuma.setDate(QDate(row[3].year, row[3].month, row[3].day))
                self.spin_onceki.setValue(float(row[4] or 0)); self.spin_guncel.setValue(float(row[5] or 0)); self.txt_birim.setText(row[6] or "")
                if row[7]: self.spin_ay.setValue(row[7])
                if row[8]: self.spin_yil.setValue(row[8])
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _save(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            if self.kayit_id:
                cursor.execute("UPDATE cevre.enerji_tuketimi SET enerji_tipi = ?, sayac_id = ?, sayac_adi = ?, okuma_tarihi = ?, onceki_okuma = ?, guncel_okuma = ?, birim = ?, donem_ay = ?, donem_yil = ? WHERE id = ?", (self.cmb_tip.currentText(), self.txt_sayac_id.text().strip() or None, self.txt_sayac_adi.text().strip() or None, self.date_okuma.date().toPython(), self.spin_onceki.value(), self.spin_guncel.value(), self.txt_birim.text().strip() or None, self.spin_ay.value(), self.spin_yil.value(), self.kayit_id))
            else:
                cursor.execute("INSERT INTO cevre.enerji_tuketimi (enerji_tipi, sayac_id, sayac_adi, okuma_tarihi, onceki_okuma, guncel_okuma, birim, donem_ay, donem_yil) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.cmb_tip.currentText(), self.txt_sayac_id.text().strip() or None, self.txt_sayac_adi.text().strip() or None, self.date_okuma.date().toPython(), self.spin_onceki.value(), self.spin_guncel.value(), self.txt_birim.text().strip() or None, self.spin_ay.value(), self.spin_yil.value()))
            conn.commit(); conn.close(); self.accept()
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))

class CevreSuEnerjiPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme); self.s = get_modern_style(theme); self._setup_ui()
        QTimer.singleShot(100, self._load_su_data); QTimer.singleShot(150, self._load_enerji_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        header = QHBoxLayout(); title_section = QVBoxLayout(); title_section.setSpacing(4)
        title_row = QHBoxLayout(); icon = QLabel("💧⚡"); icon.setStyleSheet("font-size: 28px;"); title_row.addWidget(icon)
        title = QLabel("Su ve Enerji Tüketimi"); title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;"); title_row.addWidget(title); title_row.addStretch()
        title_section.addLayout(title_row); subtitle = QLabel("Sayaç okuma ve dönemsel takip"); subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;"); title_section.addWidget(subtitle)
        header.addLayout(title_section); header.addStretch(); layout.addLayout(header)
        
        tabs = QTabWidget()
        tabs.setStyleSheet(f"QTabWidget::pane {{ border: 1px solid {s['border']}; background: {s['card_bg']}; border-radius: 10px; padding: 16px; }} QTabBar::tab {{ background: transparent; color: {s['text_muted']}; padding: 12px 24px; border: none; border-bottom: 3px solid transparent; }} QTabBar::tab:selected {{ color: {s['primary']}; border-bottom-color: {s['primary']}; }}")
        
        # Su Tab
        tab_su = QWidget(); su_layout = QVBoxLayout(tab_su); su_layout.setSpacing(16)
        su_toolbar = QHBoxLayout()
        btn_su_yeni = QPushButton("➕ Yeni Kayıt"); btn_su_yeni.setStyleSheet(f"QPushButton {{ background: {s['info']}; color: white; padding: 10px 20px; border-radius: 8px; font-weight: 600; }}"); btn_su_yeni.clicked.connect(self._yeni_su); su_toolbar.addWidget(btn_su_yeni)
        su_toolbar.addStretch()
        self.lbl_su_stat = QLabel(""); self.lbl_su_stat.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px;"); su_toolbar.addWidget(self.lbl_su_stat)
        btn_su_yenile = QPushButton("🔄"); btn_su_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}"); btn_su_yenile.clicked.connect(self._load_su_data); su_toolbar.addWidget(btn_su_yenile)
        su_layout.addLayout(su_toolbar)
        self.table_su = QTableWidget()
        self.table_su.setStyleSheet(f"QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; color: {s['text']}; }} QTableWidget::item {{ padding: 10px; }} QTableWidget::item:selected {{ background: {s['primary']}; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px; border: none; border-bottom: 2px solid {s['info']}; font-weight: 600; }}")
        self.table_su.setColumnCount(7); self.table_su.setHorizontalHeaderLabels(["ID", "Sayaç", "Tarih", "Önceki", "Güncel", "Tüketim (m³)", "İşlem"]); self.table_su.setColumnHidden(0, True)
        self.table_su.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch); self.table_su.setColumnWidth(2, 100); self.table_su.setColumnWidth(3, 100); self.table_su.setColumnWidth(4, 100); self.table_su.setColumnWidth(5, 110); self.table_su.setColumnWidth(6, 120)
        self.table_su.verticalHeader().setVisible(False); self.table_su.setSelectionBehavior(QAbstractItemView.SelectRows); self.table_su.setAlternatingRowColors(True)
        su_layout.addWidget(self.table_su)
        tabs.addTab(tab_su, "💧 Su Tüketimi")
        
        # Enerji Tab
        tab_enerji = QWidget(); enerji_layout = QVBoxLayout(tab_enerji); enerji_layout.setSpacing(16)
        enerji_toolbar = QHBoxLayout()
        btn_enerji_yeni = QPushButton("➕ Yeni Kayıt"); btn_enerji_yeni.setStyleSheet(f"QPushButton {{ background: {s['warning']}; color: white; padding: 10px 20px; border-radius: 8px; font-weight: 600; }}"); btn_enerji_yeni.clicked.connect(self._yeni_enerji); enerji_toolbar.addWidget(btn_enerji_yeni)
        self.cmb_enerji_tip = QComboBox(); self.cmb_enerji_tip.addItems(["Tümü", "ELEKTRIK", "DOGALGAZ", "LPG", "MOTORIN"]); self.cmb_enerji_tip.setStyleSheet(f"QComboBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; min-width: 120px; }}"); self.cmb_enerji_tip.currentIndexChanged.connect(self._filter_enerji); enerji_toolbar.addWidget(self.cmb_enerji_tip)
        enerji_toolbar.addStretch()
        self.lbl_enerji_stat = QLabel(""); self.lbl_enerji_stat.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px;"); enerji_toolbar.addWidget(self.lbl_enerji_stat)
        btn_enerji_yenile = QPushButton("🔄"); btn_enerji_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}"); btn_enerji_yenile.clicked.connect(self._load_enerji_data); enerji_toolbar.addWidget(btn_enerji_yenile)
        enerji_layout.addLayout(enerji_toolbar)
        self.table_enerji = QTableWidget()
        self.table_enerji.setStyleSheet(f"QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; color: {s['text']}; }} QTableWidget::item {{ padding: 10px; }} QTableWidget::item:selected {{ background: {s['primary']}; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px; border: none; border-bottom: 2px solid {s['warning']}; font-weight: 600; }}")
        self.table_enerji.setColumnCount(8); self.table_enerji.setHorizontalHeaderLabels(["ID", "Tip", "Sayaç", "Tarih", "Önceki", "Güncel", "Tüketim", "İşlem"]); self.table_enerji.setColumnHidden(0, True)
        self.table_enerji.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch); self.table_enerji.setColumnWidth(1, 100); self.table_enerji.setColumnWidth(3, 100); self.table_enerji.setColumnWidth(4, 100); self.table_enerji.setColumnWidth(5, 100); self.table_enerji.setColumnWidth(6, 120); self.table_enerji.setColumnWidth(7, 80)
        self.table_enerji.verticalHeader().setVisible(False); self.table_enerji.setSelectionBehavior(QAbstractItemView.SelectRows); self.table_enerji.setAlternatingRowColors(True)
        enerji_layout.addWidget(self.table_enerji)
        tabs.addTab(tab_enerji, "⚡ Enerji Tüketimi")
        
        layout.addWidget(tabs)
    
    def _load_su_data(self):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT id, ISNULL(sayac_adi, sayac_id), FORMAT(okuma_tarihi, 'dd.MM.yyyy'), onceki_okuma, guncel_okuma, guncel_okuma - ISNULL(onceki_okuma, 0) FROM cevre.su_tuketimi ORDER BY okuma_tarihi DESC")
            rows = cursor.fetchall(); conn.close()
            self.table_su.setRowCount(len(rows)); toplam = 0
            for i, row in enumerate(rows):
                for j, val in enumerate(row): self.table_su.setItem(i, j, QTableWidgetItem(str(val) if val else ""))
                try: toplam += float(row[5] or 0)
                except Exception: pass
                widget = self.create_action_buttons([
                    ("✏️", "Duzenle", lambda checked, rid=row[0]: self._duzenle_su(rid), "edit"),
                ])
                self.table_su.setCellWidget(i, 6, widget); self.table_su.setRowHeight(i, 44)
            self.lbl_su_stat.setText(f"📊 {len(rows)} kayıt | Toplam: {toplam:.2f} m³")
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _load_enerji_data(self):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT id, enerji_tipi, ISNULL(sayac_adi, sayac_id), FORMAT(okuma_tarihi, 'dd.MM.yyyy'), onceki_okuma, guncel_okuma, CAST(guncel_okuma - ISNULL(onceki_okuma, 0) AS VARCHAR) + ' ' + ISNULL(birim, '') FROM cevre.enerji_tuketimi ORDER BY okuma_tarihi DESC")
            self.enerji_rows = cursor.fetchall(); conn.close()
            self._display_enerji(self.enerji_rows)
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _display_enerji(self, rows):
        s = self.s
        tip_colors = {"ELEKTRIK": "#f1c40f", "DOGALGAZ": "#3498db", "LPG": "#e74c3c", "MOTORIN": "#2ecc71"}
        self.table_enerji.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "")
                if j == 1: item.setForeground(QColor(tip_colors.get(val, s['text'])))
                self.table_enerji.setItem(i, j, item)
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=row[0]: self._duzenle_enerji(rid), "edit"),
            ])
            self.table_enerji.setCellWidget(i, 7, widget); self.table_enerji.setRowHeight(i, 44)
        self.lbl_enerji_stat.setText(f"📊 {len(rows)} kayıt")
    
    def _filter_enerji(self):
        tip = self.cmb_enerji_tip.currentText()
        if tip == "Tümü": self._display_enerji(self.enerji_rows)
        else: self._display_enerji([r for r in self.enerji_rows if r[1] == tip])
    
    def _yeni_su(self):
        dialog = SuTuketimDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted: self._load_su_data()
    
    def _duzenle_su(self, kayit_id):
        dialog = SuTuketimDialog(self.theme, self, kayit_id)
        if dialog.exec() == QDialog.Accepted: self._load_su_data()
    
    def _yeni_enerji(self):
        dialog = EnerjiTuketimDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted: self._load_enerji_data()
    
    def _duzenle_enerji(self, kayit_id):
        dialog = EnerjiTuketimDialog(self.theme, self, kayit_id)
        if dialog.exec() == QDialog.Accepted: self._load_enerji_data()
