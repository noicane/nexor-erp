# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Çevre Kimyasal Envanter (REACH/CLP)
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox, QDialog, QFormLayout, QFrame, QTextEdit, QDoubleSpinBox, QCheckBox, QAbstractItemView)
from PySide6.QtCore import Qt, QTimer
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

class KimyasalDialog(QDialog):
    def __init__(self, theme: dict, parent=None, kimyasal_id=None):
        super().__init__(parent)
        self.theme = theme; self.s = get_modern_style(theme); self.kimyasal_id = kimyasal_id
        self.setWindowTitle("Kimyasal Madde"); self.setMinimumSize(600, 700); self.setModal(True)
        self._setup_ui(); self._load_combos()
        if kimyasal_id: self._load_data()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }} QLabel {{ color: {s['text']}; background: transparent; }} QLineEdit, QComboBox, QTextEdit, QDoubleSpinBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 12px; color: {s['text']}; font-size: 13px; }} QCheckBox {{ color: {s['text']}; font-size: 13px; }}")
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(16)
        header = QHBoxLayout(); icon = QLabel("🧪"); icon.setStyleSheet("font-size: 28px;"); header.addWidget(icon)
        title = QLabel(self.windowTitle()); title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};"); header.addWidget(title); header.addStretch(); layout.addLayout(header)
        form = QFormLayout(); form.setSpacing(12); label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        lbl = QLabel("Kimyasal Adı *"); lbl.setStyleSheet(label_style); self.txt_kimyasal = QLineEdit(); form.addRow(lbl, self.txt_kimyasal)
        lbl = QLabel("Ticari Adı"); lbl.setStyleSheet(label_style); self.txt_ticari = QLineEdit(); form.addRow(lbl, self.txt_ticari)
        lbl = QLabel("Stok Kartı"); lbl.setStyleSheet(label_style); self.cmb_urun = QComboBox(); form.addRow(lbl, self.cmb_urun)
        lbl = QLabel("CAS No"); lbl.setStyleSheet(label_style); self.txt_cas = QLineEdit(); self.txt_cas.setPlaceholderText("Örn: 7732-18-5"); form.addRow(lbl, self.txt_cas)
        lbl = QLabel("EC No"); lbl.setStyleSheet(label_style); self.txt_ec = QLineEdit(); form.addRow(lbl, self.txt_ec)
        lbl_tehlike = QLabel("⚠️ Sınıflandırma"); lbl_tehlike.setStyleSheet(f"font-weight: bold; color: {s['warning']}; margin-top: 10px; font-size: 14px;"); form.addRow("", lbl_tehlike)
        lbl = QLabel("Tehlike Sınıfı"); lbl.setStyleSheet(label_style); self.txt_tehlike_sinifi = QLineEdit(); form.addRow(lbl, self.txt_tehlike_sinifi)
        lbl = QLabel("H Kodları"); lbl.setStyleSheet(label_style); self.txt_h_kodlari = QLineEdit(); self.txt_h_kodlari.setPlaceholderText("H302, H315, H319..."); form.addRow(lbl, self.txt_h_kodlari)
        lbl = QLabel("P Kodları"); lbl.setStyleSheet(label_style); self.txt_p_kodlari = QLineEdit(); form.addRow(lbl, self.txt_p_kodlari)
        lbl = QLabel("Yıllık Kullanım"); lbl.setStyleSheet(label_style); self.spin_yillik = QDoubleSpinBox(); self.spin_yillik.setRange(0, 9999999); self.spin_yillik.setDecimals(2); self.spin_yillik.setSuffix(" kg/yıl"); form.addRow(lbl, self.spin_yillik)
        lbl = QLabel("Kullanım Alanı"); lbl.setStyleSheet(label_style); self.txt_kullanim = QTextEdit(); self.txt_kullanim.setMaximumHeight(50); form.addRow(lbl, self.txt_kullanim)
        lbl_reach = QLabel("🇪🇺 REACH/CLP"); lbl_reach.setStyleSheet(f"font-weight: bold; color: {s['info']}; margin-top: 10px; font-size: 14px;"); form.addRow("", lbl_reach)
        self.chk_reach = QCheckBox("REACH Kayıtlı"); form.addRow("", self.chk_reach)
        self.chk_svhc = QCheckBox("⚠️ SVHC (Yüksek Önem Arz Eden Madde)"); form.addRow("", self.chk_svhc)
        layout.addLayout(form)
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(12); btn_layout.addStretch()
        btn_iptal = QPushButton("İptal"); btn_iptal.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }}"); btn_iptal.clicked.connect(self.reject); btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾  Kaydet"); btn_kaydet.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}"); btn_kaydet.clicked.connect(self._save); btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            self.cmb_urun.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM stok.urunler WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall(): self.cmb_urun.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception: pass
    
    def _load_data(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT kimyasal_adi, ticari_adi, urun_id, cas_no, ec_no, tehlike_sinifi, h_kodlari, p_kodlari, yillik_kullanim_kg, kullanim_alani, reach_kayitli_mi, svhc_mi FROM cevre.kimyasal_envanter WHERE id = ?", (self.kimyasal_id,))
            row = cursor.fetchone(); conn.close()
            if row:
                self.txt_kimyasal.setText(row[0] or ""); self.txt_ticari.setText(row[1] or "")
                if row[2]: idx = self.cmb_urun.findData(row[2]); self.cmb_urun.setCurrentIndex(idx) if idx >= 0 else None
                self.txt_cas.setText(row[3] or ""); self.txt_ec.setText(row[4] or ""); self.txt_tehlike_sinifi.setText(row[5] or ""); self.txt_h_kodlari.setText(row[6] or ""); self.txt_p_kodlari.setText(row[7] or "")
                self.spin_yillik.setValue(float(row[8] or 0)); self.txt_kullanim.setPlainText(row[9] or ""); self.chk_reach.setChecked(row[10] or False); self.chk_svhc.setChecked(row[11] or False)
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _save(self):
        if not self.txt_kimyasal.text().strip(): QMessageBox.warning(self, "⚠️ Uyarı", "Kimyasal adı zorunludur!"); return
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            if self.kimyasal_id:
                cursor.execute("UPDATE cevre.kimyasal_envanter SET kimyasal_adi = ?, ticari_adi = ?, urun_id = ?, cas_no = ?, ec_no = ?, tehlike_sinifi = ?, h_kodlari = ?, p_kodlari = ?, yillik_kullanim_kg = ?, kullanim_alani = ?, reach_kayitli_mi = ?, svhc_mi = ? WHERE id = ?", (self.txt_kimyasal.text().strip(), self.txt_ticari.text().strip() or None, self.cmb_urun.currentData(), self.txt_cas.text().strip() or None, self.txt_ec.text().strip() or None, self.txt_tehlike_sinifi.text().strip() or None, self.txt_h_kodlari.text().strip() or None, self.txt_p_kodlari.text().strip() or None, self.spin_yillik.value() or None, self.txt_kullanim.toPlainText().strip() or None, self.chk_reach.isChecked(), self.chk_svhc.isChecked(), self.kimyasal_id))
            else:
                cursor.execute("INSERT INTO cevre.kimyasal_envanter (kimyasal_adi, ticari_adi, urun_id, cas_no, ec_no, tehlike_sinifi, h_kodlari, p_kodlari, yillik_kullanim_kg, kullanim_alani, reach_kayitli_mi, svhc_mi) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.txt_kimyasal.text().strip(), self.txt_ticari.text().strip() or None, self.cmb_urun.currentData(), self.txt_cas.text().strip() or None, self.txt_ec.text().strip() or None, self.txt_tehlike_sinifi.text().strip() or None, self.txt_h_kodlari.text().strip() or None, self.txt_p_kodlari.text().strip() or None, self.spin_yillik.value() or None, self.txt_kullanim.toPlainText().strip() or None, self.chk_reach.isChecked(), self.chk_svhc.isChecked()))
            conn.commit(); conn.close(); self.accept()
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))

class CevreKimyasalEnvanterPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme); self.s = get_modern_style(theme); self._setup_ui(); QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        header = QHBoxLayout(); title_section = QVBoxLayout(); title_section.setSpacing(4)
        title_row = QHBoxLayout(); icon = QLabel("🧪"); icon.setStyleSheet("font-size: 28px;"); title_row.addWidget(icon)
        title = QLabel("Kimyasal Madde Envanteri"); title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;"); title_row.addWidget(title); title_row.addStretch()
        title_section.addLayout(title_row); subtitle = QLabel("REACH/CLP kimyasal madde takibi"); subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;"); title_section.addWidget(subtitle)
        header.addLayout(title_section); header.addStretch()
        self.stat_label = QLabel(""); self.stat_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px; padding: 8px 16px; background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px;"); header.addWidget(self.stat_label)
        layout.addLayout(header)
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        btn_yeni = QPushButton("➕ Yeni Kimyasal"); btn_yeni.setCursor(Qt.PointingHandCursor); btn_yeni.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_yeni.clicked.connect(self._yeni); toolbar.addWidget(btn_yeni)
        btn_svhc = QPushButton("⚠️ SVHC Maddeler"); btn_svhc.setStyleSheet(f"QPushButton {{ background: {s['error']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_svhc.clicked.connect(self._show_svhc); toolbar.addWidget(btn_svhc)
        toolbar.addStretch()
        self.txt_arama = QLineEdit(); self.txt_arama.setPlaceholderText("🔍 Kimyasal ara..."); self.txt_arama.setFixedWidth(200); self.txt_arama.setStyleSheet(f"QLineEdit {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; color: {s['text']}; }}"); self.txt_arama.textChanged.connect(self._filter); toolbar.addWidget(self.txt_arama)
        btn_yenile = QPushButton("🔄"); btn_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}"); btn_yenile.clicked.connect(self._load_data); toolbar.addWidget(btn_yenile)
        layout.addLayout(toolbar)
        self.table = QTableWidget()
        self.table.setStyleSheet(f"QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; color: {s['text']}; }} QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }} QTableWidget::item:selected {{ background: {s['primary']}; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 12px; text-transform: uppercase; }}")
        self.table.setColumnCount(8); self.table.setHorizontalHeaderLabels(["ID", "Kimyasal", "CAS No", "Tehlike", "H Kodları", "REACH", "SVHC", "İşlem"]); self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch); self.table.setColumnWidth(2, 100); self.table.setColumnWidth(3, 100); self.table.setColumnWidth(4, 140); self.table.setColumnWidth(5, 70); self.table.setColumnWidth(6, 70); self.table.setColumnWidth(7, 120)
        self.table.verticalHeader().setVisible(False); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT id, kimyasal_adi, cas_no, tehlike_sinifi, h_kodlari, CASE WHEN reach_kayitli_mi = 1 THEN '✓' ELSE '' END, CASE WHEN svhc_mi = 1 THEN '⚠️' ELSE '' END FROM cevre.kimyasal_envanter WHERE aktif_mi = 1 ORDER BY kimyasal_adi")
            self.all_rows = cursor.fetchall(); conn.close()
            self._display_data(self.all_rows)
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _display_data(self, rows):
        s = self.s
        self.table.setRowCount(len(rows)); svhc_count = 0
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "")
                if j == 3 and val: item.setForeground(QColor(s['warning']))
                elif j == 4 and val: item.setForeground(QColor(s['error']))
                elif j == 5 and val: item.setForeground(QColor(s['success']))
                elif j == 6 and val: item.setForeground(QColor(s['error'])); svhc_count += 1
                self.table.setItem(i, j, item)
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=row[0]: self._duzenle(rid), "edit"),
            ])
            self.table.setCellWidget(i, 7, widget); self.table.setRowHeight(i, 48)
        self.stat_label.setText(f"📊 Toplam: {len(rows)} kimyasal | SVHC: {svhc_count}")
    
    def _filter(self):
        arama = self.txt_arama.text().lower()
        if not arama: self._display_data(self.all_rows)
        else: self._display_data([r for r in self.all_rows if arama in str(r[1]).lower() or arama in str(r[2]).lower()])
    
    def _show_svhc(self):
        self._display_data([r for r in self.all_rows if r[6]])
    
    def _yeni(self):
        dialog = KimyasalDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted: self._load_data()
    
    def _duzenle(self, kimyasal_id):
        dialog = KimyasalDialog(self.theme, self, kimyasal_id)
        if dialog.exec() == QDialog.Accepted: self._load_data()
