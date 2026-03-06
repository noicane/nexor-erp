# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Çevre Atıksu Analizleri
[MODERNIZED UI - v2.0]
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QTabWidget,
    QDoubleSpinBox, QCheckBox, QLineEdit, QAbstractItemView
)
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


class AtiksuAnalizDialog(QDialog):
    def __init__(self, theme: dict, parent=None, analiz_id=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.analiz_id = analiz_id
        self.setWindowTitle("Atıksu Analizi")
        self.setMinimumSize(800, 550)
        self.setModal(True)
        self._setup_ui()
        if analiz_id:
            self._load_data()
            self._load_detaylar()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }}
            QLabel {{ color: {s['text']}; background: transparent; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QDoubleSpinBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 12px; color: {s['text']}; font-size: 13px; }}
            QTabWidget::pane {{ border: 1px solid {s['border']}; background: {s['card_bg']}; border-radius: 10px; padding: 16px; }}
            QTabBar::tab {{ background: transparent; color: {s['text_muted']}; padding: 12px 24px; border: none; border-bottom: 3px solid transparent; }}
            QTabBar::tab:selected {{ color: {s['primary']}; border-bottom-color: {s['primary']}; }}
            QCheckBox {{ color: {s['text']}; font-size: 13px; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        icon = QLabel("🚿")
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
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        
        lbl = QLabel("Analiz No"); lbl.setStyleSheet(label_style)
        self.txt_no = QLineEdit(); self.txt_no.setReadOnly(True)
        genel_layout.addRow(lbl, self.txt_no)
        
        lbl = QLabel("Numune Tarihi *"); lbl.setStyleSheet(label_style)
        self.date_numune = QDateEdit(); self.date_numune.setDate(QDate.currentDate()); self.date_numune.setCalendarPopup(True)
        genel_layout.addRow(lbl, self.date_numune)
        
        lbl = QLabel("Numune Noktası"); lbl.setStyleSheet(label_style)
        self.txt_nokta = QLineEdit(); self.txt_nokta.setPlaceholderText("Giriş, Çıkış, Ara nokta...")
        genel_layout.addRow(lbl, self.txt_nokta)
        
        lbl = QLabel("Laboratuvar"); lbl.setStyleSheet(label_style)
        self.txt_lab = QLineEdit()
        genel_layout.addRow(lbl, self.txt_lab)
        
        lbl = QLabel("Akreditasyon No"); lbl.setStyleSheet(label_style)
        self.txt_akreditasyon = QLineEdit()
        genel_layout.addRow(lbl, self.txt_akreditasyon)
        
        lbl = QLabel("Rapor No"); lbl.setStyleSheet(label_style)
        self.txt_rapor_no = QLineEdit()
        genel_layout.addRow(lbl, self.txt_rapor_no)
        
        self.chk_asim = QCheckBox("⚠️ Sınır Aşımı Var")
        genel_layout.addRow("", self.chk_asim)
        
        lbl = QLabel("Notlar"); lbl.setStyleSheet(label_style)
        self.txt_notlar = QTextEdit(); self.txt_notlar.setMaximumHeight(60)
        genel_layout.addRow(lbl, self.txt_notlar)
        
        tabs.addTab(tab_genel, "📋 Genel")
        
        tab_param = QWidget()
        param_layout = QVBoxLayout(tab_param)
        toolbar = QHBoxLayout()
        btn_ekle = QPushButton("➕ Parametre Ekle")
        btn_ekle.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; padding: 8px 16px; border-radius: 6px; }}")
        btn_ekle.clicked.connect(self._add_parametre)
        toolbar.addWidget(btn_ekle)
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"QPushButton {{ background: {s['error']}; color: white; padding: 8px 16px; border-radius: 6px; }}")
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
        btn_iptal.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }}")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾  Kaydet")
        btn_kaydet.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT analiz_no, numune_tarihi, numune_noktasi, laboratuvar_adi, akreditasyon_no, rapor_no, sinir_asimi_var_mi, notlar FROM cevre.atiksu_analizleri WHERE id = ?", (self.analiz_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.txt_no.setText(row[0] or "")
                if row[1]: self.date_numune.setDate(QDate(row[1].year, row[1].month, row[1].day))
                self.txt_nokta.setText(row[2] or "")
                self.txt_lab.setText(row[3] or "")
                self.txt_akreditasyon.setText(row[4] or "")
                self.txt_rapor_no.setText(row[5] or "")
                self.chk_asim.setChecked(row[6] or False)
                self.txt_notlar.setPlainText(row[7] or "")
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _load_detaylar(self):
        if not self.analiz_id: return
        s = self.s
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, parametre, olculen_deger, birim, sinir_deger, sinir_asimi FROM cevre.atiksu_analiz_detaylari WHERE analiz_id = ? ORDER BY id", (self.analiz_id,))
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
        except: pass
    
    def _add_parametre(self):
        if not self.analiz_id:
            QMessageBox.warning(self, "⚠️ Uyarı", "Önce analizi kaydedin!")
            return
        param, ok = QMessageBox.getText(self, "Parametre Ekle", "Parametre adı (pH, KOI, BOI, AKM...):")
        if not ok or not param: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO cevre.atiksu_analiz_detaylari (analiz_id, parametre, birim) VALUES (?, ?, 'mg/L')", (self.analiz_id, param))
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
            cursor.execute("DELETE FROM cevre.atiksu_analiz_detaylari WHERE id = ?", (int(self.table_param.item(row, 0).text()),))
            conn.commit()
            conn.close()
            self._load_detaylar()
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _save(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if self.analiz_id:
                cursor.execute("UPDATE cevre.atiksu_analizleri SET numune_tarihi = ?, numune_noktasi = ?, laboratuvar_adi = ?, akreditasyon_no = ?, rapor_no = ?, sinir_asimi_var_mi = ?, notlar = ? WHERE id = ?",
                    (self.date_numune.date().toPython(), self.txt_nokta.text().strip() or None, self.txt_lab.text().strip() or None, self.txt_akreditasyon.text().strip() or None, self.txt_rapor_no.text().strip() or None, self.chk_asim.isChecked(), self.txt_notlar.toPlainText().strip() or None, self.analiz_id))
            else:
                cursor.execute("SELECT 'AS-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM cevre.atiksu_analizleri), 0) + 1 AS VARCHAR), 4)")
                no = cursor.fetchone()[0]
                cursor.execute("INSERT INTO cevre.atiksu_analizleri (analiz_no, numune_tarihi, numune_noktasi, laboratuvar_adi, akreditasyon_no, rapor_no, sinir_asimi_var_mi, notlar) OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (no, self.date_numune.date().toPython(), self.txt_nokta.text().strip() or None, self.txt_lab.text().strip() or None, self.txt_akreditasyon.text().strip() or None, self.txt_rapor_no.text().strip() or None, self.chk_asim.isChecked(), self.txt_notlar.toPlainText().strip() or None))
                self.analiz_id = cursor.fetchone()[0]
                self.txt_no.setText(no)
            conn.commit()
            conn.close()
            QMessageBox.information(self, "✓ Başarılı", "Analiz kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))


class CevreAtiksuPage(BasePage):
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
        icon = QLabel("🚿")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Atıksu Analizleri")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Parametre bazlı analiz sonuçları")
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
        btn_yeni = QPushButton("➕ Yeni Analiz")
        btn_yeni.setCursor(Qt.PointingHandCursor)
        btn_yeni.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }} QPushButton:hover {{ background: {s['primary_hover']}; }}")
        btn_yeni.clicked.connect(self._yeni)
        toolbar.addWidget(btn_yeni)
        btn_asim = QPushButton("⚠️ Sınır Aşımları")
        btn_asim.setCursor(Qt.PointingHandCursor)
        btn_asim.setStyleSheet(f"QPushButton {{ background: {s['error']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}")
        btn_asim.clicked.connect(self._show_asim)
        toolbar.addWidget(btn_asim)
        toolbar.addStretch()
        btn_yenile = QPushButton("🔄")
        btn_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}")
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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "No", "Tarih", "Nokta", "Laboratuvar", "Durum", "İşlem"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, analiz_no, FORMAT(numune_tarihi, 'dd.MM.yyyy'), numune_noktasi, laboratuvar_adi, CASE WHEN sinir_asimi_var_mi = 1 THEN '⚠️ AŞIM' ELSE '✓ UYGUN' END FROM cevre.atiksu_analizleri ORDER BY numune_tarihi DESC")
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _display_data(self, rows):
        s = self.s
        self.table.setRowCount(len(rows))
        asim = 0
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "")
                if j == 5 and "AŞIM" in str(val):
                    item.setForeground(QColor(s['error']))
                    asim += 1
                elif j == 5:
                    item.setForeground(QColor(s['success']))
                self.table.setItem(i, j, item)
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=row[0]: self._duzenle(rid), "edit"),
            ])
            self.table.setCellWidget(i, 6, widget)
            self.table.setRowHeight(i, 48)
        self.stat_label.setText(f"📊 Toplam: {len(rows)} analiz | Sınır aşımı: {asim}")
    
    def _show_asim(self):
        self._display_data([r for r in self.all_rows if "AŞIM" in str(r[5])])
    
    def _yeni(self):
        dialog = AtiksuAnalizDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted: self._load_data()
    
    def _duzenle(self, analiz_id):
        dialog = AtiksuAnalizDialog(self.theme, self, analiz_id)
        if dialog.exec() == QDialog.Accepted: self._load_data()
