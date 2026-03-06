# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Çevre Denetimleri
[MODERNIZED UI - v2.0]
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateTimeEdit, QTextEdit, QCheckBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QDateTime, QTimer
from PySide6.QtGui import QColor
from components.base_page import BasePage
from core.database import get_db_connection

def get_modern_style(theme: dict) -> dict:
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

class CevreDenetimDialog(QDialog):
    def __init__(self, theme: dict, parent=None, denetim_id=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.denetim_id = denetim_id
        self.setWindowTitle("Çevre Denetimi")
        self.setMinimumSize(600, 700)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if denetim_id: self._load_data()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }} QLabel {{ color: {s['text']}; background: transparent; }} QLineEdit, QComboBox, QDateTimeEdit, QTextEdit {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 12px; color: {s['text']}; font-size: 13px; }} QCheckBox {{ color: {s['text']}; font-size: 13px; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        header = QHBoxLayout()
        icon = QLabel("🔍"); icon.setStyleSheet("font-size: 28px;")
        header.addWidget(icon)
        title = QLabel(self.windowTitle()); title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};")
        header.addWidget(title); header.addStretch()
        layout.addLayout(header)
        form = QFormLayout(); form.setSpacing(12)
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        lbl = QLabel("Denetim No"); lbl.setStyleSheet(label_style); self.txt_no = QLineEdit(); self.txt_no.setReadOnly(True); form.addRow(lbl, self.txt_no)
        lbl = QLabel("Denetim Tarihi *"); lbl.setStyleSheet(label_style); self.dt_denetim = QDateTimeEdit(); self.dt_denetim.setDateTime(QDateTime.currentDateTime()); self.dt_denetim.setCalendarPopup(True); form.addRow(lbl, self.dt_denetim)
        lbl = QLabel("Denetim Tipi"); lbl.setStyleSheet(label_style); self.cmb_tip = QComboBox(); self.cmb_tip.addItems(["IC", "BAKANLIK", "IL_MUDURLUGU", "MUSTERI", "DIGER"]); form.addRow(lbl, self.cmb_tip)
        lbl = QLabel("Denetçi"); lbl.setStyleSheet(label_style); self.txt_denetci = QLineEdit(); form.addRow(lbl, self.txt_denetci)
        lbl = QLabel("Kurum"); lbl.setStyleSheet(label_style); self.txt_kurum = QLineEdit(); form.addRow(lbl, self.txt_kurum)
        lbl = QLabel("Kapsam"); lbl.setStyleSheet(label_style); self.txt_kapsam = QTextEdit(); self.txt_kapsam.setMaximumHeight(60); form.addRow(lbl, self.txt_kapsam)
        self.chk_uygunsuzluk = QCheckBox("⚠️ Uygunsuzluk Var"); form.addRow("", self.chk_uygunsuzluk)
        lbl = QLabel("Bulgular"); lbl.setStyleSheet(label_style); self.txt_bulgular = QTextEdit(); self.txt_bulgular.setMaximumHeight(80); form.addRow(lbl, self.txt_bulgular)
        lbl = QLabel("Düzeltici Faaliyet"); lbl.setStyleSheet(label_style); self.txt_duzeltici = QTextEdit(); self.txt_duzeltici.setMaximumHeight(60); form.addRow(lbl, self.txt_duzeltici)
        lbl = QLabel("Sorumlu"); lbl.setStyleSheet(label_style); self.cmb_sorumlu = QComboBox(); form.addRow(lbl, self.cmb_sorumlu)
        lbl = QLabel("Durum"); lbl.setStyleSheet(label_style); self.cmb_durum = QComboBox(); self.cmb_durum.addItems(["TAMAMLANDI", "DEVAM_EDIYOR", "BEKLIYOR"]); form.addRow(lbl, self.cmb_durum)
        layout.addLayout(form)
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(12); btn_layout.addStretch()
        btn_iptal = QPushButton("İptal"); btn_iptal.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }}"); btn_iptal.clicked.connect(self.reject); btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾  Kaydet"); btn_kaydet.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}"); btn_kaydet.clicked.connect(self._save); btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            self.cmb_sorumlu.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall(): self.cmb_sorumlu.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except: pass
    
    def _load_data(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT denetim_no, denetim_tarihi, denetim_tipi, denetci_adi, denetci_kurumu, kapsam, uygunsuzluk_var_mi, bulgular, duzeltici_faaliyet, faaliyet_sorumlu_id, durum FROM cevre.cevre_denetimleri WHERE id = ?", (self.denetim_id,))
            row = cursor.fetchone(); conn.close()
            if row:
                self.txt_no.setText(row[0] or "")
                if row[1]: self.dt_denetim.setDateTime(QDateTime(row[1]))
                if row[2]: idx = self.cmb_tip.findText(row[2]); self.cmb_tip.setCurrentIndex(idx) if idx >= 0 else None
                self.txt_denetci.setText(row[3] or ""); self.txt_kurum.setText(row[4] or ""); self.txt_kapsam.setPlainText(row[5] or ""); self.chk_uygunsuzluk.setChecked(row[6] or False); self.txt_bulgular.setPlainText(row[7] or ""); self.txt_duzeltici.setPlainText(row[8] or "")
                if row[9]: idx = self.cmb_sorumlu.findData(row[9]); self.cmb_sorumlu.setCurrentIndex(idx) if idx >= 0 else None
                if row[10]: idx = self.cmb_durum.findText(row[10]); self.cmb_durum.setCurrentIndex(idx) if idx >= 0 else None
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _save(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            if self.denetim_id:
                cursor.execute("UPDATE cevre.cevre_denetimleri SET denetim_tarihi = ?, denetim_tipi = ?, denetci_adi = ?, denetci_kurumu = ?, kapsam = ?, uygunsuzluk_var_mi = ?, bulgular = ?, duzeltici_faaliyet = ?, faaliyet_sorumlu_id = ?, durum = ? WHERE id = ?", (self.dt_denetim.dateTime().toPython(), self.cmb_tip.currentText(), self.txt_denetci.text().strip() or None, self.txt_kurum.text().strip() or None, self.txt_kapsam.toPlainText().strip() or None, self.chk_uygunsuzluk.isChecked(), self.txt_bulgular.toPlainText().strip() or None, self.txt_duzeltici.toPlainText().strip() or None, self.cmb_sorumlu.currentData(), self.cmb_durum.currentText(), self.denetim_id))
            else:
                cursor.execute("SELECT 'CD-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM cevre.cevre_denetimleri), 0) + 1 AS VARCHAR), 4)")
                no = cursor.fetchone()[0]
                cursor.execute("INSERT INTO cevre.cevre_denetimleri (denetim_no, denetim_tarihi, denetim_tipi, denetci_adi, denetci_kurumu, kapsam, uygunsuzluk_var_mi, bulgular, duzeltici_faaliyet, faaliyet_sorumlu_id, durum) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (no, self.dt_denetim.dateTime().toPython(), self.cmb_tip.currentText(), self.txt_denetci.text().strip() or None, self.txt_kurum.text().strip() or None, self.txt_kapsam.toPlainText().strip() or None, self.chk_uygunsuzluk.isChecked(), self.txt_bulgular.toPlainText().strip() or None, self.txt_duzeltici.toPlainText().strip() or None, self.cmb_sorumlu.currentData(), self.cmb_durum.currentText()))
                self.txt_no.setText(no)
            conn.commit(); conn.close(); self.accept()
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))

class CevreDenetimlerPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        header = QHBoxLayout()
        title_section = QVBoxLayout(); title_section.setSpacing(4)
        title_row = QHBoxLayout()
        icon = QLabel("🔍"); icon.setStyleSheet("font-size: 28px;"); title_row.addWidget(icon)
        title = QLabel("Çevre Denetimleri"); title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;"); title_row.addWidget(title); title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("İç ve dış denetimler, bulgular"); subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;"); title_section.addWidget(subtitle)
        header.addLayout(title_section); header.addStretch()
        self.stat_label = QLabel(""); self.stat_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px; padding: 8px 16px; background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px;"); header.addWidget(self.stat_label)
        layout.addLayout(header)
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        btn_yeni = QPushButton("➕ Yeni Denetim"); btn_yeni.setCursor(Qt.PointingHandCursor); btn_yeni.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_yeni.clicked.connect(self._yeni); toolbar.addWidget(btn_yeni)
        btn_uygunsuz = QPushButton("⚠️ Uygunsuzluklar"); btn_uygunsuz.setStyleSheet(f"QPushButton {{ background: {s['warning']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_uygunsuz.clicked.connect(self._show_uygunsuz); toolbar.addWidget(btn_uygunsuz)
        toolbar.addStretch()
        self.cmb_tip = QComboBox(); self.cmb_tip.addItems(["Tümü", "IC", "BAKANLIK", "IL_MUDURLUGU", "MUSTERI"]); self.cmb_tip.setStyleSheet(f"QComboBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; min-width: 120px; }}"); self.cmb_tip.currentIndexChanged.connect(self._filter); toolbar.addWidget(self.cmb_tip)
        btn_yenile = QPushButton("🔄"); btn_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}"); btn_yenile.clicked.connect(self._load_data); toolbar.addWidget(btn_yenile)
        layout.addLayout(toolbar)
        self.table = QTableWidget()
        self.table.setStyleSheet(f"QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; color: {s['text']}; }} QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }} QTableWidget::item:selected {{ background: {s['primary']}; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 12px; text-transform: uppercase; }}")
        self.table.setColumnCount(7); self.table.setHorizontalHeaderLabels(["ID", "No", "Tarih", "Tip", "Denetçi", "Durum", "İşlem"]); self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch); self.table.setColumnWidth(1, 140); self.table.setColumnWidth(2, 100); self.table.setColumnWidth(3, 120); self.table.setColumnWidth(5, 110); self.table.setColumnWidth(6, 120)
        self.table.verticalHeader().setVisible(False); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT id, denetim_no, FORMAT(denetim_tarihi, 'dd.MM.yyyy'), denetim_tipi, denetci_adi, CASE WHEN uygunsuzluk_var_mi = 1 THEN '⚠️ UYGUNSUZ' ELSE '✓' END FROM cevre.cevre_denetimleri ORDER BY denetim_tarihi DESC")
            self.all_rows = cursor.fetchall(); conn.close()
            self._display_data(self.all_rows)
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _display_data(self, rows):
        s = self.s
        self.table.setRowCount(len(rows)); uygunsuz = 0
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "")
                if j == 5 and "UYGUNSUZ" in str(val): item.setForeground(QColor(s['warning'])); uygunsuz += 1
                self.table.setItem(i, j, item)
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=row[0]: self._duzenle(rid), "edit"),
            ])
            self.table.setCellWidget(i, 6, widget); self.table.setRowHeight(i, 48)
        self.stat_label.setText(f"📊 Toplam: {len(rows)} denetim | Uygunsuzluk: {uygunsuz}")
    
    def _filter(self):
        tip = self.cmb_tip.currentText()
        if tip == "Tümü": self._display_data(self.all_rows)
        else: self._display_data([r for r in self.all_rows if r[3] == tip])
    
    def _show_uygunsuz(self):
        self._display_data([r for r in self.all_rows if "UYGUNSUZ" in str(r[5])])
    
    def _yeni(self):
        dialog = CevreDenetimDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted: self._load_data()
    
    def _duzenle(self, denetim_id):
        dialog = CevreDenetimDialog(self.theme, self, denetim_id)
        if dialog.exec() == QDialog.Accepted: self._load_data()
