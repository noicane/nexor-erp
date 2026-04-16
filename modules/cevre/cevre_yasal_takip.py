# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Çevre Yasal Takip
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox, QDialog, QFormLayout, QFrame, QDateEdit, QSpinBox, QAbstractItemView)
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
        'bg_main': brand.BG_MAIN,
        'bg_hover': brand.BG_HOVER,
        'border_light': brand.BORDER_HARD,
    }

class CevreYasalTakipDialog(QDialog):
    def __init__(self, theme: dict, parent=None, kayit_id=None):
        super().__init__(parent)
        self.theme = theme; self.s = get_modern_style(theme); self.kayit_id = kayit_id
        self.setWindowTitle("Çevre Yasal Gereklilik"); self.setMinimumSize(550, 500); self.setModal(True)
        self._setup_ui(); self._load_combos()
        if kayit_id: self._load_data()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }} QLabel {{ color: {s['text']}; background: transparent; }} QLineEdit, QComboBox, QDateEdit, QSpinBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 12px; color: {s['text']}; font-size: 13px; }}")
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        header = QHBoxLayout(); icon = QLabel("⚖️"); icon.setStyleSheet("font-size: 28px;"); header.addWidget(icon)
        title = QLabel(self.windowTitle()); title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};"); header.addWidget(title); header.addStretch(); layout.addLayout(header)
        form = QFormLayout(); form.setSpacing(14); label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        lbl = QLabel("Gereklilik Adı *"); lbl.setStyleSheet(label_style); self.txt_ad = QLineEdit(); form.addRow(lbl, self.txt_ad)
        lbl = QLabel("Mevzuat"); lbl.setStyleSheet(label_style); self.txt_mevzuat = QLineEdit(); form.addRow(lbl, self.txt_mevzuat)
        lbl = QLabel("Periyot"); lbl.setStyleSheet(label_style); self.cmb_periyot = QComboBox(); self.cmb_periyot.addItems(["YILLIK", "6_AYLIK", "AYLIK", "TEK_SEFER"]); self.cmb_periyot.currentIndexChanged.connect(self._on_periyot_changed); form.addRow(lbl, self.cmb_periyot)
        lbl = QLabel("Periyot (gün)"); lbl.setStyleSheet(label_style); self.spin_gun = QSpinBox(); self.spin_gun.setRange(1, 1825); self.spin_gun.setValue(365); self.spin_gun.setSuffix(" gün"); form.addRow(lbl, self.spin_gun)
        lbl = QLabel("Son Yapılma"); lbl.setStyleSheet(label_style); self.date_son = QDateEdit(); self.date_son.setDate(QDate.currentDate()); self.date_son.setCalendarPopup(True); form.addRow(lbl, self.date_son)
        lbl = QLabel("Sonraki"); lbl.setStyleSheet(label_style); self.date_sonraki = QDateEdit(); self.date_sonraki.setDate(QDate.currentDate().addYears(1)); self.date_sonraki.setCalendarPopup(True); form.addRow(lbl, self.date_sonraki)
        lbl = QLabel("Sorumlu"); lbl.setStyleSheet(label_style); self.cmb_sorumlu = QComboBox(); form.addRow(lbl, self.cmb_sorumlu)
        layout.addLayout(form); layout.addStretch()
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
        except Exception: pass
    
    def _on_periyot_changed(self):
        gunler = {"YILLIK": 365, "6_AYLIK": 180, "AYLIK": 30, "TEK_SEFER": 0}
        self.spin_gun.setValue(gunler.get(self.cmb_periyot.currentText(), 365))
    
    def _load_data(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT gereklilik_adi, mevzuat_adi, periyot_tipi, periyot_gun, son_yapilma_tarihi, sonraki_tarih, sorumlu_id FROM cevre.yasal_takip WHERE id = ?", (self.kayit_id,))
            row = cursor.fetchone(); conn.close()
            if row:
                self.txt_ad.setText(row[0] or ""); self.txt_mevzuat.setText(row[1] or "")
                if row[2]: idx = self.cmb_periyot.findText(row[2]); self.cmb_periyot.setCurrentIndex(idx) if idx >= 0 else None
                self.spin_gun.setValue(row[3] or 365)
                if row[4]: self.date_son.setDate(QDate(row[4].year, row[4].month, row[4].day))
                if row[5]: self.date_sonraki.setDate(QDate(row[5].year, row[5].month, row[5].day))
                if row[6]: idx = self.cmb_sorumlu.findData(row[6]); self.cmb_sorumlu.setCurrentIndex(idx) if idx >= 0 else None
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _save(self):
        if not self.txt_ad.text().strip(): QMessageBox.warning(self, "⚠️ Uyarı", "Gereklilik adı zorunludur!"); return
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            if self.kayit_id:
                cursor.execute("UPDATE cevre.yasal_takip SET gereklilik_adi = ?, mevzuat_adi = ?, periyot_tipi = ?, periyot_gun = ?, son_yapilma_tarihi = ?, sonraki_tarih = ?, sorumlu_id = ? WHERE id = ?", (self.txt_ad.text().strip(), self.txt_mevzuat.text().strip() or None, self.cmb_periyot.currentText(), self.spin_gun.value(), self.date_son.date().toPython(), self.date_sonraki.date().toPython(), self.cmb_sorumlu.currentData(), self.kayit_id))
            else:
                cursor.execute("INSERT INTO cevre.yasal_takip (gereklilik_adi, mevzuat_adi, periyot_tipi, periyot_gun, son_yapilma_tarihi, sonraki_tarih, sorumlu_id) VALUES (?, ?, ?, ?, ?, ?, ?)", (self.txt_ad.text().strip(), self.txt_mevzuat.text().strip() or None, self.cmb_periyot.currentText(), self.spin_gun.value(), self.date_son.date().toPython(), self.date_sonraki.date().toPython(), self.cmb_sorumlu.currentData()))
            conn.commit(); conn.close(); self.accept()
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))

class CevreYasalTakipPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme); self.s = get_modern_style(theme); self._setup_ui(); QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        header = QHBoxLayout(); title_section = QVBoxLayout(); title_section.setSpacing(4)
        title_row = QHBoxLayout(); icon = QLabel("⚖️"); icon.setStyleSheet("font-size: 28px;"); title_row.addWidget(icon)
        title = QLabel("Çevre Yasal Takip"); title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;"); title_row.addWidget(title); title_row.addStretch()
        title_section.addLayout(title_row); subtitle = QLabel("Çevresel mevzuat gereklilikleri takibi"); subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;"); title_section.addWidget(subtitle)
        header.addLayout(title_section); header.addStretch()
        self.stat_label = QLabel(""); self.stat_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px; padding: 8px 16px; background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px;"); header.addWidget(self.stat_label)
        layout.addLayout(header)
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        btn_yeni = QPushButton("➕ Yeni Gereklilik"); btn_yeni.setCursor(Qt.PointingHandCursor); btn_yeni.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_yeni.clicked.connect(self._yeni); toolbar.addWidget(btn_yeni)
        btn_tamamla = QPushButton("✓ Tamamlandı"); btn_tamamla.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_tamamla.clicked.connect(self._tamamla); toolbar.addWidget(btn_tamamla)
        btn_geciken = QPushButton("⚠️ Süresi Geçenler"); btn_geciken.setStyleSheet(f"QPushButton {{ background: {s['warning']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_geciken.clicked.connect(self._show_geciken); toolbar.addWidget(btn_geciken)
        toolbar.addStretch(); btn_yenile = QPushButton("🔄"); btn_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}"); btn_yenile.clicked.connect(self._load_data); toolbar.addWidget(btn_yenile)
        layout.addLayout(toolbar)
        self.table = QTableWidget()
        self.table.setStyleSheet(f"QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; color: {s['text']}; }} QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }} QTableWidget::item:selected {{ background: {s['primary']}; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 12px; text-transform: uppercase; }}")
        self.table.setColumnCount(7); self.table.setHorizontalHeaderLabels(["ID", "Gereklilik", "Periyot", "Son Yapılma", "Sonraki", "Kalan Gün", "İşlem"]); self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch); self.table.setColumnWidth(2, 100); self.table.setColumnWidth(3, 100); self.table.setColumnWidth(4, 100); self.table.setColumnWidth(5, 100); self.table.setColumnWidth(6, 120)
        self.table.verticalHeader().setVisible(False); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT id, gereklilik_adi, periyot_tipi, FORMAT(son_yapilma_tarihi, 'dd.MM.yyyy'), FORMAT(sonraki_tarih, 'dd.MM.yyyy'), DATEDIFF(DAY, GETDATE(), sonraki_tarih) FROM cevre.yasal_takip WHERE aktif_mi = 1 ORDER BY sonraki_tarih ASC")
            self.all_rows = cursor.fetchall(); conn.close()
            self._display_data(self.all_rows)
        except Exception as e: QMessageBox.critical(self, "❌ Hata", f"Hata: {str(e)}")
    
    def _display_data(self, rows):
        s = self.s
        self.table.setRowCount(len(rows)); geciken = 0
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 5:
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    if val is not None and val < 0: item.setForeground(QColor(s['error'])); item.setText(f"{val} (GECİKMİŞ)"); geciken += 1
                    elif val is not None and val <= 30: item.setForeground(QColor(s['warning']))
                    else: item.setForeground(QColor(s['success']))
                else: item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=row[0]: self._duzenle(rid), "edit"),
            ])
            self.table.setCellWidget(i, 6, widget); self.table.setRowHeight(i, 48)
        self.stat_label.setText(f"📊 Toplam: {len(rows)} | Süresi geçen: {geciken}")
    
    def _show_geciken(self):
        self._display_data([r for r in self.all_rows if r[5] is not None and r[5] < 0])
    
    def _tamamla(self):
        row = self.table.currentRow()
        if row < 0: return
        kayit_id = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, "Onay", "Gereklilik tamamlandı olarak işaretlensin mi?") != QMessageBox.Yes: return
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("UPDATE cevre.yasal_takip SET son_yapilma_tarihi = GETDATE(), sonraki_tarih = DATEADD(DAY, periyot_gun, GETDATE()) WHERE id = ?", (kayit_id,))
            conn.commit(); conn.close(); self._load_data()
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _yeni(self):
        dialog = CevreYasalTakipDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted: self._load_data()
    
    def _duzenle(self, kayit_id):
        dialog = CevreYasalTakipDialog(self.theme, self, kayit_id)
        if dialog.exec() == QDialog.Accepted: self._load_data()
