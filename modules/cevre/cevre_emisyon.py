# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Çevre Emisyon Takibi
Emisyon Kaynakları ve Ölçüm Takibi
[MODERNIZED UI - v2.0]
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QDoubleSpinBox,
    QTabWidget, QCheckBox, QAbstractItemView
)
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


class EmisyonOlcumDialog(QDialog):
    def __init__(self, theme: dict, parent=None, olcum_id=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.olcum_id = olcum_id
        self.setWindowTitle("Emisyon Ölçümü")
        self.setMinimumSize(850, 600)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if olcum_id:
            self._load_data()
            self._load_detaylar()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }}
            QLabel {{ color: {s['text']}; background: transparent; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QDoubleSpinBox {{
                background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px;
                padding: 10px 12px; color: {s['text']}; font-size: 13px;
            }}
            QTabWidget::pane {{ border: 1px solid {s['border']}; background: {s['card_bg']}; border-radius: 10px; padding: 16px; }}
            QTabBar::tab {{ background: transparent; color: {s['text_muted']}; padding: 12px 24px; border: none; border-bottom: 3px solid transparent; }}
            QTabBar::tab:selected {{ color: {s['primary']}; border-bottom-color: {s['primary']}; }}
            QCheckBox {{ color: {s['text']}; font-size: 13px; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        icon = QLabel("💨")
        icon.setStyleSheet("font-size: 28px;")
        header.addWidget(icon)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        tabs = QTabWidget()
        
        tab_genel = QWidget()
        genel_layout = QFormLayout(tab_genel)
        genel_layout.setSpacing(14)
        genel_layout.setLabelAlignment(Qt.AlignRight)
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        
        lbl = QLabel("Ölçüm No")
        lbl.setStyleSheet(label_style)
        self.txt_no = QLineEdit()
        self.txt_no.setReadOnly(True)
        genel_layout.addRow(lbl, self.txt_no)
        
        lbl = QLabel("Emisyon Kaynağı *")
        lbl.setStyleSheet(label_style)
        self.cmb_kaynak = QComboBox()
        genel_layout.addRow(lbl, self.cmb_kaynak)
        
        lbl = QLabel("Ölçüm Tarihi *")
        lbl.setStyleSheet(label_style)
        self.date_olcum = QDateEdit()
        self.date_olcum.setDate(QDate.currentDate())
        self.date_olcum.setCalendarPopup(True)
        genel_layout.addRow(lbl, self.date_olcum)
        
        lbl = QLabel("Ölçüm Firması")
        lbl.setStyleSheet(label_style)
        self.txt_firma = QLineEdit()
        self.txt_firma.setPlaceholderText("Akredite ölçüm firması")
        genel_layout.addRow(lbl, self.txt_firma)
        
        lbl = QLabel("Akreditasyon No")
        lbl.setStyleSheet(label_style)
        self.txt_akreditasyon = QLineEdit()
        genel_layout.addRow(lbl, self.txt_akreditasyon)
        
        lbl = QLabel("Rapor No")
        lbl.setStyleSheet(label_style)
        self.txt_rapor_no = QLineEdit()
        genel_layout.addRow(lbl, self.txt_rapor_no)
        
        self.chk_asim = QCheckBox("⚠️ Sınır Aşımı Var")
        genel_layout.addRow("", self.chk_asim)
        
        lbl = QLabel("Değerlendirme")
        lbl.setStyleSheet(label_style)
        self.txt_degerlendirme = QTextEdit()
        self.txt_degerlendirme.setMaximumHeight(60)
        genel_layout.addRow(lbl, self.txt_degerlendirme)
        
        lbl = QLabel("Sonraki Ölçüm")
        lbl.setStyleSheet(label_style)
        self.date_sonraki = QDateEdit()
        self.date_sonraki.setDate(QDate.currentDate().addYears(1))
        self.date_sonraki.setCalendarPopup(True)
        genel_layout.addRow(lbl, self.date_sonraki)
        
        tabs.addTab(tab_genel, "📋 Genel")
        
        tab_param = QWidget()
        param_layout = QVBoxLayout(tab_param)
        
        toolbar = QHBoxLayout()
        btn_ekle = QPushButton("➕ Parametre Ekle")
        btn_ekle.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; padding: 8px 16px; border-radius: 6px; }} QPushButton:hover {{ background: #059669; }}")
        btn_ekle.clicked.connect(self._add_parametre)
        toolbar.addWidget(btn_ekle)
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"QPushButton {{ background: {s['error']}; color: white; padding: 8px 16px; border-radius: 6px; }} QPushButton:hover {{ background: #DC2626; }}")
        btn_sil.clicked.connect(self._remove_parametre)
        toolbar.addWidget(btn_sil)
        toolbar.addStretch()
        param_layout.addLayout(toolbar)
        
        self.table_param = QTableWidget()
        self.table_param.setColumnCount(6)
        self.table_param.setHorizontalHeaderLabels(["ID", "Parametre", "Ölçülen", "Birim", "Sınır", "Aşım"])
        self.table_param.setColumnHidden(0, True)
        self.table_param.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_param.setStyleSheet(f"QTableWidget {{ background: {s['card_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 10px; border: none; font-weight: 600; }}")
        self.table_param.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        param_layout.addWidget(self.table_param)
        
        tabs.addTab(tab_param, "📊 Parametreler")
        layout.addWidget(tabs)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }} QPushButton:hover {{ background: {s['border']}; }}")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾  Kaydet")
        btn_kaydet.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }} QPushButton:hover {{ background: #059669; }}")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            self.cmb_kaynak.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, kaynak_adi, kaynak_tipi FROM cevre.emisyon_kaynaklari WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_kaynak.addItem(f"{row[1]} - {row[2]} ({row[3]})", row[0])
            conn.close()
        except Exception: pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT olcum_no, kaynak_id, olcum_tarihi, olcum_firmasi, akreditasyon_no, rapor_no, sinir_asimi_var_mi, degerlendirme, sonraki_olcum_tarihi FROM cevre.emisyon_olcumleri WHERE id = ?", (self.olcum_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.txt_no.setText(row[0] or "")
                if row[1]:
                    idx = self.cmb_kaynak.findData(row[1])
                    if idx >= 0: self.cmb_kaynak.setCurrentIndex(idx)
                if row[2]: self.date_olcum.setDate(QDate(row[2].year, row[2].month, row[2].day))
                self.txt_firma.setText(row[3] or "")
                self.txt_akreditasyon.setText(row[4] or "")
                self.txt_rapor_no.setText(row[5] or "")
                self.chk_asim.setChecked(row[6] or False)
                self.txt_degerlendirme.setPlainText(row[7] or "")
                if row[8]: self.date_sonraki.setDate(QDate(row[8].year, row[8].month, row[8].day))
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _load_detaylar(self):
        if not self.olcum_id: return
        s = self.s
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, parametre, olculen_deger, birim, sinir_deger, sinir_asimi FROM cevre.emisyon_olcum_detaylari WHERE olcum_id = ? ORDER BY id", (self.olcum_id,))
            rows = cursor.fetchall()
            conn.close()
            self.table_param.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table_param.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_param.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                self.table_param.setItem(i, 2, QTableWidgetItem(str(row[2]) if row[2] else ""))
                self.table_param.setItem(i, 3, QTableWidgetItem(row[3] or ""))
                self.table_param.setItem(i, 4, QTableWidgetItem(str(row[4]) if row[4] else ""))
                asim = "⚠️ AŞIM" if row[5] else "✓"
                asim_item = QTableWidgetItem(asim)
                asim_item.setForeground(QColor(s['error'] if row[5] else s['success']))
                self.table_param.setItem(i, 5, asim_item)
        except Exception: pass
    
    def _add_parametre(self):
        if not self.olcum_id:
            QMessageBox.warning(self, "⚠️ Uyarı", "Önce ölçümü kaydedin!")
            return
        param, ok = QMessageBox.getText(self, "Parametre Ekle", "Parametre adı:")
        if not ok or not param: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO cevre.emisyon_olcum_detaylari (olcum_id, parametre, birim) VALUES (?, ?, 'mg/Nm³')", (self.olcum_id, param))
            conn.commit()
            conn.close()
            self._load_detaylar()
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _remove_parametre(self):
        row = self.table_param.currentRow()
        if row < 0: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cevre.emisyon_olcum_detaylari WHERE id = ?", (int(self.table_param.item(row, 0).text()),))
            conn.commit()
            conn.close()
            self._load_detaylar()
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _save(self):
        if not self.cmb_kaynak.currentData():
            QMessageBox.warning(self, "⚠️ Uyarı", "Emisyon kaynağı seçiniz!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if self.olcum_id:
                cursor.execute("UPDATE cevre.emisyon_olcumleri SET kaynak_id = ?, olcum_tarihi = ?, olcum_firmasi = ?, akreditasyon_no = ?, rapor_no = ?, sinir_asimi_var_mi = ?, degerlendirme = ?, sonraki_olcum_tarihi = ? WHERE id = ?",
                    (self.cmb_kaynak.currentData(), self.date_olcum.date().toPython(), self.txt_firma.text().strip() or None, self.txt_akreditasyon.text().strip() or None, self.txt_rapor_no.text().strip() or None, self.chk_asim.isChecked(), self.txt_degerlendirme.toPlainText().strip() or None, self.date_sonraki.date().toPython(), self.olcum_id))
            else:
                cursor.execute("SELECT 'EM-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM cevre.emisyon_olcumleri), 0) + 1 AS VARCHAR), 4)")
                no = cursor.fetchone()[0]
                cursor.execute("INSERT INTO cevre.emisyon_olcumleri (olcum_no, kaynak_id, olcum_tarihi, olcum_firmasi, akreditasyon_no, rapor_no, sinir_asimi_var_mi, degerlendirme, sonraki_olcum_tarihi) OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (no, self.cmb_kaynak.currentData(), self.date_olcum.date().toPython(), self.txt_firma.text().strip() or None, self.txt_akreditasyon.text().strip() or None, self.txt_rapor_no.text().strip() or None, self.chk_asim.isChecked(), self.txt_degerlendirme.toPlainText().strip() or None, self.date_sonraki.date().toPython()))
                self.olcum_id = cursor.fetchone()[0]
                self.txt_no.setText(no)
            conn.commit()
            conn.close()
            QMessageBox.information(self, "✓ Başarılı", "Ölçüm kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))


class CevreEmisyonPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        title_row = QHBoxLayout()
        icon = QLabel("💨")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Emisyon Takibi")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Emisyon kaynakları ve ölçüm takibi")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px; padding: 8px 16px; background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px;")
        header.addWidget(self.stat_label)
        layout.addLayout(header)
        
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        btn_yeni = QPushButton("➕ Yeni Ölçüm")
        btn_yeni.setCursor(Qt.PointingHandCursor)
        btn_yeni.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }} QPushButton:hover {{ background: {s['primary_hover']}; }}")
        btn_yeni.clicked.connect(self._yeni)
        toolbar.addWidget(btn_yeni)
        
        btn_asim = QPushButton("⚠️ Sınır Aşımları")
        btn_asim.setCursor(Qt.PointingHandCursor)
        btn_asim.setStyleSheet(f"QPushButton {{ background: {s['error']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }} QPushButton:hover {{ background: #DC2626; }}")
        btn_asim.clicked.connect(self._show_asim)
        toolbar.addWidget(btn_asim)
        
        toolbar.addStretch()
        
        btn_yenile = QPushButton("🔄")
        btn_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }} QPushButton:hover {{ background: {s['border']}; }}")
        btn_yenile.clicked.connect(self._load_data)
        toolbar.addWidget(btn_yenile)
        
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; color: {s['text']}; }}
            QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }}
            QTableWidget::item:selected {{ background: {s['primary']}; }}
            QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
        """)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "No", "Kaynak", "Tarih", "Firma", "Sonraki", "Durum", "İşlem"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.id, o.olcum_no, k.kod + ' - ' + k.kaynak_adi, FORMAT(o.olcum_tarihi, 'dd.MM.yyyy'),
                       o.olcum_firmasi, FORMAT(o.sonraki_olcum_tarihi, 'dd.MM.yyyy'),
                       CASE WHEN o.sinir_asimi_var_mi = 1 THEN '⚠️ AŞIM' ELSE '✓ UYGUN' END
                FROM cevre.emisyon_olcumleri o
                JOIN cevre.emisyon_kaynaklari k ON o.kaynak_id = k.id
                ORDER BY o.olcum_tarihi DESC
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", f"Hata: {str(e)}")
    
    def _display_data(self, rows):
        s = self.s
        asim_sayisi = 0
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 6:
                    item = QTableWidgetItem(str(val) if val else "")
                    if "AŞIM" in str(val):
                        item.setForeground(QColor(s['error']))
                        asim_sayisi += 1
                    else:
                        item.setForeground(QColor(s['success']))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)
            
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=row[0]: self._duzenle(rid), "edit"),
            ])
            self.table.setCellWidget(i, 7, widget)
            self.table.setRowHeight(i, 48)
        
        self.stat_label.setText(f"📊 Toplam: {len(rows)} ölçüm | Sınır aşımı: {asim_sayisi}")
    
    def _show_asim(self):
        self._display_data([r for r in self.all_rows if "AŞIM" in str(r[6])])
    
    def _yeni(self):
        dialog = EmisyonOlcumDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self, olcum_id):
        dialog = EmisyonOlcumDialog(self.theme, self, olcum_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
