# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Stok Sayım Sayfası
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QWidget, QDialog,
    QFormLayout, QDateEdit, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, QDate
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

class SayimOlusturDialog(QDialog):
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme; self.s = get_modern_style(theme)
        self.setWindowTitle("Yeni Sayım Oluştur"); self.setMinimumSize(500, 400); self.setModal(True)
        self._setup_ui(); self._load_combos()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }} QLabel {{ color: {s['text']}; }} QLineEdit, QComboBox, QDateEdit, QTextEdit {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; }}")
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        header = QHBoxLayout(); icon = QLabel("📋"); icon.setStyleSheet("font-size: 28px;"); header.addWidget(icon)
        title = QLabel(self.windowTitle()); title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};"); header.addWidget(title); header.addStretch()
        layout.addLayout(header)
        form = QFormLayout(); form.setSpacing(14); label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        lbl = QLabel("Sayım Tipi *"); lbl.setStyleSheet(label_style); self.cmb_tip = QComboBox(); self.cmb_tip.addItems(["TAM_SAYIM", "SPOT_SAYIM", "DEVIR_SAYIMI"]); form.addRow(lbl, self.cmb_tip)
        lbl = QLabel("Depo *"); lbl.setStyleSheet(label_style); self.cmb_depo = QComboBox(); form.addRow(lbl, self.cmb_depo)
        lbl = QLabel("Sayım Tarihi"); lbl.setStyleSheet(label_style); self.date_sayim = QDateEdit(); self.date_sayim.setDate(QDate.currentDate()); self.date_sayim.setCalendarPopup(True); form.addRow(lbl, self.date_sayim)
        lbl = QLabel("Açıklama"); lbl.setStyleSheet(label_style); self.txt_aciklama = QTextEdit(); self.txt_aciklama.setMaximumHeight(60); form.addRow(lbl, self.txt_aciklama)
        layout.addLayout(form); layout.addStretch()
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(12); btn_layout.addStretch()
        btn_iptal = QPushButton("İptal"); btn_iptal.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }}"); btn_iptal.clicked.connect(self.reject); btn_layout.addWidget(btn_iptal)
        btn_olustur = QPushButton("📋 Sayım Oluştur"); btn_olustur.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}"); btn_olustur.clicked.connect(self._olustur); btn_layout.addWidget(btn_olustur)
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            self.cmb_depo.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM tanim.depolar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall(): self.cmb_depo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except: pass
    
    def _olustur(self):
        if not self.cmb_depo.currentData(): QMessageBox.warning(self, "⚠️ Uyarı", "Depo seçimi zorunludur!"); return
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT 'SYM-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM stok.sayimlar), 0) + 1 AS VARCHAR), 4)")
            sayim_no = cursor.fetchone()[0]
            cursor.execute("INSERT INTO stok.sayimlar (sayim_no, sayim_tipi, depo_id, sayim_tarihi, aciklama, durum) VALUES (?, ?, ?, ?, ?, 'TASLAK')", (sayim_no, self.cmb_tip.currentText(), self.cmb_depo.currentData(), self.date_sayim.date().toPython(), self.txt_aciklama.toPlainText().strip() or None))
            conn.commit(); conn.close(); self.accept()
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))

class DepoSayimPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        
        header = QHBoxLayout(); title_section = QVBoxLayout(); title_section.setSpacing(4)
        title_row = QHBoxLayout(); icon = QLabel("📋"); icon.setStyleSheet("font-size: 28px;"); title_row.addWidget(icon)
        title = QLabel("Stok Sayım"); title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;"); title_row.addWidget(title); title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Depo sayım işlemleri ve fark raporları"); subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;"); title_section.addWidget(subtitle)
        header.addLayout(title_section); header.addStretch()
        self.stat_label = QLabel(""); self.stat_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px; padding: 8px 16px; background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px;"); header.addWidget(self.stat_label)
        layout.addLayout(header)
        
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        btn_yeni = QPushButton("➕ Yeni Sayım"); btn_yeni.setCursor(Qt.PointingHandCursor); btn_yeni.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_yeni.clicked.connect(self._yeni); toolbar.addWidget(btn_yeni)
        toolbar.addStretch()
        self.cmb_durum = QComboBox(); self.cmb_durum.addItems(["Tümü", "TASLAK", "DEVAM_EDIYOR", "TAMAMLANDI"]); self.cmb_durum.setStyleSheet(f"QComboBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; min-width: 140px; }}"); self.cmb_durum.currentIndexChanged.connect(self._filter); toolbar.addWidget(self.cmb_durum)
        btn_yenile = QPushButton("🔄"); btn_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}"); btn_yenile.clicked.connect(self._load_data); toolbar.addWidget(btn_yenile)
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setStyleSheet(f"QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; color: {s['text']}; }} QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }} QTableWidget::item:selected {{ background: {s['primary']}; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 12px; text-transform: uppercase; }}")
        self.table.setColumnCount(7); self.table.setHorizontalHeaderLabels(["ID", "Sayım No", "Tip", "Depo", "Tarih", "Durum", "İşlem"]); self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 150); self.table.setColumnWidth(2, 120); self.table.setColumnWidth(4, 100); self.table.setColumnWidth(5, 120); self.table.setColumnWidth(6, 120)
        self.table.verticalHeader().setVisible(False); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""SELECT s.id, s.sayim_no, s.sayim_tipi, d.kod + ' - ' + d.ad, FORMAT(s.sayim_tarihi, 'dd.MM.yyyy'), s.durum
                FROM stok.sayimlar s LEFT JOIN tanim.depolar d ON s.depo_id = d.id ORDER BY s.sayim_tarihi DESC""")
            self.all_rows = cursor.fetchall(); conn.close()
            self._display_data(self.all_rows)
        except Exception as e: 
            self.all_rows = []
            self.stat_label.setText("📊 Tablo bulunamadı")
    
    def _display_data(self, rows):
        s = self.s
        self.table.setRowCount(len(rows)); taslak = devam = 0
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "")
                if j == 5:
                    if val == 'TASLAK': item.setForeground(QColor(s['warning'])); taslak += 1
                    elif val == 'DEVAM_EDIYOR': item.setForeground(QColor(s['info'])); devam += 1
                    elif val == 'TAMAMLANDI': item.setForeground(QColor(s['success']))
                self.table.setItem(i, j, item)
            widget = self.create_action_buttons([
                ("📋", "Detay", lambda checked, rid=row[0]: self._detay(rid), "view"),
            ])
            self.table.setCellWidget(i, 6, widget); self.table.setRowHeight(i, 48)
        self.stat_label.setText(f"📊 Toplam: {len(rows)} | Taslak: {taslak} | Devam: {devam}")
    
    def _filter(self):
        durum = self.cmb_durum.currentText()
        if durum == "Tümü": self._display_data(self.all_rows)
        else: self._display_data([r for r in self.all_rows if r[5] == durum])
    
    def _yeni(self):
        dialog = SayimOlusturDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted: self._load_data()
    
    def _detay(self, sayim_id):
        QMessageBox.information(self, "ℹ️ Bilgi", f"Sayım detay ekranı: ID {sayim_id}\n\nBu özellik geliştirme aşamasında...")
