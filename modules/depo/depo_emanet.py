# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Emanet Stoklar Sayfası
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QWidget, QDialog,
    QFormLayout, QDateEdit, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager

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

class EmanetStokDialog(QDialog):
    def __init__(self, theme: dict, parent=None, emanet_id=None):
        super().__init__(parent)
        self.theme = theme; self.s = get_modern_style(theme); self.emanet_id = emanet_id
        self.setWindowTitle("Emanet Stok Kaydı"); self.setMinimumSize(500, 500); self.setModal(True)
        self._setup_ui(); self._load_combos()
        if emanet_id: self._load_data()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }} QLabel {{ color: {s['text']}; }} QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; }}")
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        header = QHBoxLayout(); icon = QLabel("📦"); icon.setStyleSheet("font-size: 28px;"); header.addWidget(icon)
        title = QLabel(self.windowTitle()); title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};"); header.addWidget(title); header.addStretch()
        layout.addLayout(header)
        form = QFormLayout(); form.setSpacing(14); label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        lbl = QLabel("Cari *"); lbl.setStyleSheet(label_style); self.cmb_cari = QComboBox(); form.addRow(lbl, self.cmb_cari)
        lbl = QLabel("Stok *"); lbl.setStyleSheet(label_style); self.cmb_stok = QComboBox(); form.addRow(lbl, self.cmb_stok)
        lbl = QLabel("Miktar *"); lbl.setStyleSheet(label_style); self.spin_miktar = QDoubleSpinBox(); self.spin_miktar.setRange(0.01, 9999999); self.spin_miktar.setDecimals(2); form.addRow(lbl, self.spin_miktar)
        lbl = QLabel("Giriş Tarihi"); lbl.setStyleSheet(label_style); self.date_giris = QDateEdit(); self.date_giris.setDate(QDate.currentDate()); self.date_giris.setCalendarPopup(True); form.addRow(lbl, self.date_giris)
        lbl = QLabel("Planlanan İade"); lbl.setStyleSheet(label_style); self.date_iade = QDateEdit(); self.date_iade.setDate(QDate.currentDate().addMonths(1)); self.date_iade.setCalendarPopup(True); form.addRow(lbl, self.date_iade)
        lbl = QLabel("Açıklama"); lbl.setStyleSheet(label_style); self.txt_aciklama = QLineEdit(); form.addRow(lbl, self.txt_aciklama)
        layout.addLayout(form); layout.addStretch()
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(12); btn_layout.addStretch()
        btn_iptal = QPushButton("İptal"); btn_iptal.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }}"); btn_iptal.clicked.connect(self.reject); btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾  Kaydet"); btn_kaydet.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}"); btn_kaydet.clicked.connect(self._save); btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            self.cmb_cari.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, unvan FROM cari.cariler WHERE aktif_mi = 1 ORDER BY unvan")
            for row in cursor.fetchall(): self.cmb_cari.addItem(f"{row[1]} - {row[2][:30]}", row[0])
            self.cmb_stok.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, urun_kodu, urun_adi FROM stok.urunler WHERE aktif_mi = 1 ORDER BY urun_kodu")
            for row in cursor.fetchall(): self.cmb_stok.addItem(f"{row[1]} - {row[2][:30]}", row[0])
            conn.close()
        except Exception: pass
    
    def _load_data(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT cari_id, urun_id, miktar, giris_tarihi, planlanan_iade_tarihi, aciklama FROM stok.emanet_stoklar WHERE id = ?", (self.emanet_id,))
            row = cursor.fetchone(); conn.close()
            if row:
                if row[0]: idx = self.cmb_cari.findData(row[0]); self.cmb_cari.setCurrentIndex(idx) if idx >= 0 else None
                if row[1]: idx = self.cmb_stok.findData(row[1]); self.cmb_stok.setCurrentIndex(idx) if idx >= 0 else None
                self.spin_miktar.setValue(float(row[2] or 0))
                if row[3]: self.date_giris.setDate(QDate(row[3].year, row[3].month, row[3].day))
                if row[4]: self.date_iade.setDate(QDate(row[4].year, row[4].month, row[4].day))
                self.txt_aciklama.setText(row[5] or "")
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _save(self):
        if not self.cmb_cari.currentData() or not self.cmb_stok.currentData():
            QMessageBox.warning(self, "⚠️ Uyarı", "Cari ve Stok seçimi zorunludur!"); return
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            if self.emanet_id:
                cursor.execute("UPDATE stok.emanet_stoklar SET cari_id = ?, urun_id = ?, miktar = ?, giris_tarihi = ?, planlanan_iade_tarihi = ?, aciklama = ? WHERE id = ?", (self.cmb_cari.currentData(), self.cmb_stok.currentData(), self.spin_miktar.value(), self.date_giris.date().toPython(), self.date_iade.date().toPython(), self.txt_aciklama.text().strip() or None, self.emanet_id))
            else:
                cursor.execute("INSERT INTO stok.emanet_stoklar (cari_id, urun_id, miktar, giris_tarihi, planlanan_iade_tarihi, aciklama, durum) VALUES (?, ?, ?, ?, ?, ?, 'AKTIF')", (self.cmb_cari.currentData(), self.cmb_stok.currentData(), self.spin_miktar.value(), self.date_giris.date().toPython(), self.date_iade.date().toPython(), self.txt_aciklama.text().strip() or None))
            conn.commit(); conn.close(); self.accept()
            LogManager.log_insert('depo', 'stok.emanet_stoklar', None, 'Emanet stok kaydi olustu')
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))

class DepoEmanetPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        
        header = QHBoxLayout(); title_section = QVBoxLayout(); title_section.setSpacing(4)
        title_row = QHBoxLayout(); icon = QLabel("📦"); icon.setStyleSheet("font-size: 28px;"); title_row.addWidget(icon)
        title = QLabel("Emanet Stoklar"); title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;"); title_row.addWidget(title); title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Müşteri emanet stok takibi"); subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;"); title_section.addWidget(subtitle)
        header.addLayout(title_section); header.addStretch()
        self.stat_label = QLabel(""); self.stat_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px; padding: 8px 16px; background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px;"); header.addWidget(self.stat_label)
        layout.addLayout(header)
        
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        btn_yeni = QPushButton("➕ Yeni Emanet"); btn_yeni.setCursor(Qt.PointingHandCursor); btn_yeni.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_yeni.clicked.connect(self._yeni); toolbar.addWidget(btn_yeni)
        btn_geciken = QPushButton("⚠️ Süresi Geçenler"); btn_geciken.setStyleSheet(f"QPushButton {{ background: {s['warning']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_geciken.clicked.connect(self._show_geciken); toolbar.addWidget(btn_geciken)
        toolbar.addStretch()
        self.txt_arama = QLineEdit(); self.txt_arama.setPlaceholderText("🔍 Cari veya stok ara..."); self.txt_arama.setFixedWidth(200); self.txt_arama.setStyleSheet(f"QLineEdit {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; }}"); self.txt_arama.textChanged.connect(self._filter); toolbar.addWidget(self.txt_arama)
        btn_yenile = QPushButton("🔄"); btn_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}"); btn_yenile.clicked.connect(self._load_data); toolbar.addWidget(btn_yenile)
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setStyleSheet(f"QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; color: {s['text']}; }} QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }} QTableWidget::item:selected {{ background: {s['primary']}; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 12px; text-transform: uppercase; }}")
        self.table.setColumnCount(8); self.table.setHorizontalHeaderLabels(["ID", "Cari", "Stok", "Miktar", "Giriş", "Plan. İade", "Durum", "İşlem"]); self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch); self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(3, 100); self.table.setColumnWidth(4, 100); self.table.setColumnWidth(5, 100); self.table.setColumnWidth(6, 100); self.table.setColumnWidth(7, 120)
        self.table.verticalHeader().setVisible(False); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""SELECT e.id, c.unvan, u.urun_kodu + ' - ' + u.urun_adi, e.miktar, FORMAT(e.giris_tarihi, 'dd.MM.yyyy'), 
                FORMAT(e.planlanan_iade_tarihi, 'dd.MM.yyyy'), e.durum, DATEDIFF(DAY, GETDATE(), e.planlanan_iade_tarihi)
                FROM stok.emanet_stoklar e
                LEFT JOIN cari.cariler c ON e.cari_id = c.id
                LEFT JOIN stok.urunler u ON e.urun_id = u.id
                WHERE e.durum = 'AKTIF' ORDER BY e.planlanan_iade_tarihi ASC""")
            self.all_rows = cursor.fetchall(); conn.close()
            self._display_data(self.all_rows)
        except Exception as e: 
            self.all_rows = []
            self.stat_label.setText("📊 Tablo bulunamadı")
    
    def _display_data(self, rows):
        s = self.s
        self.table.setRowCount(len(rows)); geciken = 0
        for i, row in enumerate(rows):
            for j in range(7):
                item = QTableWidgetItem(str(row[j]) if row[j] else "")
                if j == 6:
                    kalan = row[7] if len(row) > 7 else 0
                    if kalan is not None and kalan < 0: item.setForeground(QColor(s['error'])); item.setText("GECİKMİŞ"); geciken += 1
                    elif kalan is not None and kalan <= 7: item.setForeground(QColor(s['warning']))
                    else: item.setForeground(QColor(s['success']))
                self.table.setItem(i, j, item)
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=row[0]: self._duzenle(rid), "edit"),
                ("📤", "Iade", lambda checked, rid=row[0]: self._iade(rid), "success"),
            ])
            self.table.setCellWidget(i, 7, widget); self.table.setRowHeight(i, 48)
        self.stat_label.setText(f"📊 Toplam: {len(rows)} | Geciken: {geciken}")
    
    def _filter(self):
        arama = self.txt_arama.text().lower()
        if not arama: self._display_data(self.all_rows)
        else: self._display_data([r for r in self.all_rows if arama in str(r[1]).lower() or arama in str(r[2]).lower()])
    
    def _show_geciken(self):
        self._display_data([r for r in self.all_rows if r[7] is not None and r[7] < 0])
    
    def _yeni(self):
        dialog = EmanetStokDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted: self._load_data()
    
    def _duzenle(self, emanet_id):
        dialog = EmanetStokDialog(self.theme, self, emanet_id)
        if dialog.exec() == QDialog.Accepted: self._load_data()
    
    def _iade(self, emanet_id):
        if QMessageBox.question(self, "Onay", "Emanet stok iade edilsin mi?") != QMessageBox.Yes: return
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("UPDATE stok.emanet_stoklar SET durum = 'IADE', iade_tarihi = GETDATE() WHERE id = ?", (emanet_id,))
            conn.commit(); conn.close(); self._load_data()
            LogManager.log_update('depo', 'stok.emanet_stoklar', None, 'Durum guncellendi')
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
