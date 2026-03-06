# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Çevre İzinler
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox, QDialog, QFormLayout, QFrame, QDateEdit, QSpinBox, QAbstractItemView)
from PySide6.QtCore import Qt, QDate, QTimer
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

class IzinDialog(QDialog):
    def __init__(self, theme: dict, parent=None, izin_id=None):
        super().__init__(parent)
        self.theme = theme; self.s = get_modern_style(theme); self.izin_id = izin_id
        self.setWindowTitle("Çevresel İzin"); self.setMinimumSize(550, 500); self.setModal(True)
        self._setup_ui()
        if izin_id: self._load_data()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }} QLabel {{ color: {s['text']}; background: transparent; }} QLineEdit, QComboBox, QDateEdit, QSpinBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 12px; color: {s['text']}; font-size: 13px; }}")
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        header = QHBoxLayout(); icon = QLabel("📜"); icon.setStyleSheet("font-size: 28px;"); header.addWidget(icon)
        title = QLabel(self.windowTitle()); title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};"); header.addWidget(title); header.addStretch(); layout.addLayout(header)
        form = QFormLayout(); form.setSpacing(14); label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        lbl = QLabel("İzin Tipi *"); lbl.setStyleSheet(label_style); self.cmb_tip = QComboBox(); self.cmb_tip.addItems(["CEVRE_IZNI", "EMISYON_IZNI", "DESARJ_IZNI", "GGI", "ATIK_LISANSI"]); form.addRow(lbl, self.cmb_tip)
        lbl = QLabel("İzin Adı *"); lbl.setStyleSheet(label_style); self.txt_ad = QLineEdit(); form.addRow(lbl, self.txt_ad)
        lbl = QLabel("İzin No"); lbl.setStyleSheet(label_style); self.txt_no = QLineEdit(); form.addRow(lbl, self.txt_no)
        lbl = QLabel("Veren Kurum"); lbl.setStyleSheet(label_style); self.txt_kurum = QLineEdit(); form.addRow(lbl, self.txt_kurum)
        lbl = QLabel("Başlangıç"); lbl.setStyleSheet(label_style); self.date_baslangic = QDateEdit(); self.date_baslangic.setDate(QDate.currentDate()); self.date_baslangic.setCalendarPopup(True); form.addRow(lbl, self.date_baslangic)
        lbl = QLabel("Bitiş"); lbl.setStyleSheet(label_style); self.date_bitis = QDateEdit(); self.date_bitis.setDate(QDate.currentDate().addYears(5)); self.date_bitis.setCalendarPopup(True); form.addRow(lbl, self.date_bitis)
        lbl = QLabel("Hatırlatma"); lbl.setStyleSheet(label_style); self.spin_hatirlatma = QSpinBox(); self.spin_hatirlatma.setRange(7, 180); self.spin_hatirlatma.setValue(60); self.spin_hatirlatma.setSuffix(" gün önce"); form.addRow(lbl, self.spin_hatirlatma)
        lbl = QLabel("Durum"); lbl.setStyleSheet(label_style); self.cmb_durum = QComboBox(); self.cmb_durum.addItems(["AKTIF", "SURESI_DOLDU", "IPTAL"]); form.addRow(lbl, self.cmb_durum)
        layout.addLayout(form); layout.addStretch()
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(12); btn_layout.addStretch()
        btn_iptal = QPushButton("İptal"); btn_iptal.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }}"); btn_iptal.clicked.connect(self.reject); btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾  Kaydet"); btn_kaydet.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}"); btn_kaydet.clicked.connect(self._save); btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT izin_tipi, izin_adi, izin_no, veren_kurum, baslangic_tarihi, bitis_tarihi, hatirlatma_gun, durum FROM cevre.cevresel_izinler WHERE id = ?", (self.izin_id,))
            row = cursor.fetchone(); conn.close()
            if row:
                if row[0]: idx = self.cmb_tip.findText(row[0]); self.cmb_tip.setCurrentIndex(idx) if idx >= 0 else None
                self.txt_ad.setText(row[1] or ""); self.txt_no.setText(row[2] or ""); self.txt_kurum.setText(row[3] or "")
                if row[4]: self.date_baslangic.setDate(QDate(row[4].year, row[4].month, row[4].day))
                if row[5]: self.date_bitis.setDate(QDate(row[5].year, row[5].month, row[5].day))
                self.spin_hatirlatma.setValue(row[6] or 60)
                if row[7]: idx = self.cmb_durum.findText(row[7]); self.cmb_durum.setCurrentIndex(idx) if idx >= 0 else None
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _save(self):
        if not self.txt_ad.text().strip(): QMessageBox.warning(self, "⚠️ Uyarı", "İzin adı zorunludur!"); return
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            if self.izin_id:
                cursor.execute("UPDATE cevre.cevresel_izinler SET izin_tipi = ?, izin_adi = ?, izin_no = ?, veren_kurum = ?, baslangic_tarihi = ?, bitis_tarihi = ?, hatirlatma_gun = ?, durum = ? WHERE id = ?", (self.cmb_tip.currentText(), self.txt_ad.text().strip(), self.txt_no.text().strip() or None, self.txt_kurum.text().strip() or None, self.date_baslangic.date().toPython(), self.date_bitis.date().toPython(), self.spin_hatirlatma.value(), self.cmb_durum.currentText(), self.izin_id))
            else:
                cursor.execute("INSERT INTO cevre.cevresel_izinler (izin_tipi, izin_adi, izin_no, veren_kurum, baslangic_tarihi, bitis_tarihi, hatirlatma_gun, durum) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (self.cmb_tip.currentText(), self.txt_ad.text().strip(), self.txt_no.text().strip() or None, self.txt_kurum.text().strip() or None, self.date_baslangic.date().toPython(), self.date_bitis.date().toPython(), self.spin_hatirlatma.value(), self.cmb_durum.currentText()))
            conn.commit(); conn.close(); self.accept()
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))

class CevreIzinlerPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme); self.s = get_modern_style(theme); self._setup_ui(); QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        header = QHBoxLayout(); title_section = QVBoxLayout(); title_section.setSpacing(4)
        title_row = QHBoxLayout(); icon = QLabel("📜"); icon.setStyleSheet("font-size: 28px;"); title_row.addWidget(icon)
        title = QLabel("Çevresel İzinler"); title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;"); title_row.addWidget(title); title_row.addStretch()
        title_section.addLayout(title_row); subtitle = QLabel("İzin ve lisans takibi"); subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;"); title_section.addWidget(subtitle)
        header.addLayout(title_section); header.addStretch()
        self.stat_label = QLabel(""); self.stat_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px; padding: 8px 16px; background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px;"); header.addWidget(self.stat_label)
        layout.addLayout(header)
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        btn_yeni = QPushButton("➕ Yeni İzin"); btn_yeni.setCursor(Qt.PointingHandCursor); btn_yeni.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_yeni.clicked.connect(self._yeni); toolbar.addWidget(btn_yeni)
        btn_yaklasiyor = QPushButton("⚠️ Süresi Yaklaşanlar"); btn_yaklasiyor.setStyleSheet(f"QPushButton {{ background: {s['warning']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_yaklasiyor.clicked.connect(self._show_yaklasiyor); toolbar.addWidget(btn_yaklasiyor)
        toolbar.addStretch(); btn_yenile = QPushButton("🔄"); btn_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}"); btn_yenile.clicked.connect(self._load_data); toolbar.addWidget(btn_yenile)
        layout.addLayout(toolbar)
        self.table = QTableWidget()
        self.table.setStyleSheet(f"QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; color: {s['text']}; }} QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }} QTableWidget::item:selected {{ background: {s['primary']}; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 12px; text-transform: uppercase; }}")
        self.table.setColumnCount(8); self.table.setHorizontalHeaderLabels(["ID", "Tip", "İzin Adı", "İzin No", "Bitiş", "Kalan Gün", "Durum", "İşlem"]); self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch); self.table.setColumnWidth(1, 120); self.table.setColumnWidth(3, 110); self.table.setColumnWidth(4, 100); self.table.setColumnWidth(5, 90); self.table.setColumnWidth(6, 100); self.table.setColumnWidth(7, 120)
        self.table.verticalHeader().setVisible(False); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT id, izin_tipi, izin_adi, izin_no, FORMAT(bitis_tarihi, 'dd.MM.yyyy'), DATEDIFF(DAY, GETDATE(), bitis_tarihi), durum FROM cevre.cevresel_izinler ORDER BY bitis_tarihi ASC")
            self.all_rows = cursor.fetchall(); conn.close()
            self._display_data(self.all_rows)
        except Exception as e: QMessageBox.critical(self, "❌ Hata", f"Hata: {str(e)}")
    
    def _display_data(self, rows):
        s = self.s
        self.table.setRowCount(len(rows)); yaklasiyor = 0
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 5:
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    if val is not None and val < 0: item.setForeground(QColor(s['error'])); item.setText(f"{val} (DOLDU)"); yaklasiyor += 1
                    elif val is not None and val <= 60: item.setForeground(QColor(s['warning'])); yaklasiyor += 1
                    else: item.setForeground(QColor(s['success']))
                elif j == 6:
                    item = QTableWidgetItem(str(val) if val else "")
                    if val == "SURESI_DOLDU": item.setForeground(QColor(s['error']))
                    elif val == "IPTAL": item.setForeground(QColor(s['text_muted']))
                else: item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=row[0]: self._duzenle(rid), "edit"),
            ])
            self.table.setCellWidget(i, 7, widget); self.table.setRowHeight(i, 48)
        self.stat_label.setText(f"📊 Toplam: {len(rows)} izin | Dikkat: {yaklasiyor}")
    
    def _show_yaklasiyor(self):
        self._display_data([r for r in self.all_rows if r[5] is not None and r[5] <= 60])
    
    def _yeni(self):
        dialog = IzinDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted: self._load_data()
    
    def _duzenle(self, izin_id):
        dialog = IzinDialog(self.theme, self, izin_id)
        if dialog.exec() == QDialog.Accepted: self._load_data()
