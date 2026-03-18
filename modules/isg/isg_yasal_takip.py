# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İSG Yasal Takip
Mevzuat Gereklilikleri Takibi
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QSpinBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class YasalTakipDialog(QDialog):
    """Yasal gereklilik kaydı"""
    
    def __init__(self, theme: dict, parent=None, kayit_id=None):
        super().__init__(parent)
        self.theme = theme
        self.kayit_id = kayit_id
        self.setWindowTitle("Yasal Gereklilik")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if kayit_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox {{
                background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')};
                border-radius: 6px; padding: 8px; color: {self.theme.get('text')};
            }}
        """)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.txt_ad = QLineEdit()
        form.addRow("Gereklilik Adı*:", self.txt_ad)
        
        self.txt_mevzuat = QLineEdit()
        form.addRow("Mevzuat:", self.txt_mevzuat)
        
        self.cmb_periyot = QComboBox()
        self.cmb_periyot.addItems(["YILLIK", "6_AYLIK", "AYLIK", "TEK_SEFER"])
        self.cmb_periyot.currentIndexChanged.connect(self._on_periyot_changed)
        form.addRow("Periyot:", self.cmb_periyot)
        
        self.spin_gun = QSpinBox()
        self.spin_gun.setRange(1, 730)
        self.spin_gun.setValue(365)
        self.spin_gun.setSuffix(" gün")
        form.addRow("Periyot (gün):", self.spin_gun)
        
        self.date_son = QDateEdit()
        self.date_son.setDate(QDate.currentDate())
        self.date_son.setCalendarPopup(True)
        form.addRow("Son Yapılma:", self.date_son)
        
        self.date_sonraki = QDateEdit()
        self.date_sonraki.setDate(QDate.currentDate().addYears(1))
        self.date_sonraki.setCalendarPopup(True)
        form.addRow("Sonraki Tarih:", self.date_sonraki)
        
        self.cmb_sorumlu = QComboBox()
        form.addRow("Sorumlu:", self.cmb_sorumlu)
        
        layout.addLayout(form)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 24px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            self.cmb_sorumlu.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_sorumlu.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception:
            pass
    
    def _on_periyot_changed(self):
        periyot = self.cmb_periyot.currentText()
        gunler = {"YILLIK": 365, "6_AYLIK": 180, "AYLIK": 30, "TEK_SEFER": 0}
        self.spin_gun.setValue(gunler.get(periyot, 365))
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT gereklilik_adi, mevzuat_adi, periyot_tipi, periyot_gun,
                       son_yapilma_tarihi, sonraki_tarih, sorumlu_id
                FROM isg.yasal_takip WHERE id = ?
            """, (self.kayit_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_ad.setText(row[0] or "")
                self.txt_mevzuat.setText(row[1] or "")
                if row[2]:
                    idx = self.cmb_periyot.findText(row[2])
                    if idx >= 0: self.cmb_periyot.setCurrentIndex(idx)
                self.spin_gun.setValue(row[3] or 365)
                if row[4]: self.date_son.setDate(QDate(row[4].year, row[4].month, row[4].day))
                if row[5]: self.date_sonraki.setDate(QDate(row[5].year, row[5].month, row[5].day))
                if row[6]:
                    idx = self.cmb_sorumlu.findData(row[6])
                    if idx >= 0: self.cmb_sorumlu.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        ad = self.txt_ad.text().strip()
        if not ad:
            QMessageBox.warning(self, "Uyarı", "Gereklilik adı zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.kayit_id:
                cursor.execute("""
                    UPDATE isg.yasal_takip SET
                        gereklilik_adi = ?, mevzuat_adi = ?, periyot_tipi = ?, periyot_gun = ?,
                        son_yapilma_tarihi = ?, sonraki_tarih = ?, sorumlu_id = ?
                    WHERE id = ?
                """, (ad, self.txt_mevzuat.text().strip() or None, self.cmb_periyot.currentText(),
                      self.spin_gun.value(), self.date_son.date().toPython(),
                      self.date_sonraki.date().toPython(), self.cmb_sorumlu.currentData(), self.kayit_id))
            else:
                cursor.execute("""
                    INSERT INTO isg.yasal_takip (gereklilik_adi, mevzuat_adi, periyot_tipi, periyot_gun,
                    son_yapilma_tarihi, sonraki_tarih, sorumlu_id) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ad, self.txt_mevzuat.text().strip() or None, self.cmb_periyot.currentText(),
                      self.spin_gun.value(), self.date_son.date().toPython(),
                      self.date_sonraki.date().toPython(), self.cmb_sorumlu.currentData()))
            
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class ISGYasalTakipPage(BasePage):
    """İSG Yasal Takip Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("⚖️ Yasal Takip")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Gereklilik")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)
        
        btn_tamamla = QPushButton("✓ Tamamlandı")
        btn_tamamla.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_tamamla.clicked.connect(self._tamamla)
        toolbar_layout.addWidget(btn_tamamla)
        
        btn_geciken = QPushButton("⚠️ Süresi Geçenler")
        btn_geciken.setStyleSheet(f"background: {self.theme.get('warning')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_geciken.clicked.connect(self._show_geciken)
        toolbar_layout.addWidget(btn_geciken)
        
        toolbar_layout.addStretch()
        btn_yenile = QPushButton("🔄")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Gereklilik", "Periyot", "Son Yapılma", "Sonraki", "Kalan Gün", "Sorumlu"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; color: {self.theme.get('text')}; }}
            QTableWidget::item:selected {{ background: {self.theme.get('primary')}; }}
            QHeaderView::section {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px; font-weight: bold; }}
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        self.lbl_stat = QLabel()
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT y.id, y.gereklilik_adi, y.periyot_tipi,
                       FORMAT(y.son_yapilma_tarihi, 'dd.MM.yyyy'),
                       FORMAT(y.sonraki_tarih, 'dd.MM.yyyy'),
                       DATEDIFF(DAY, GETDATE(), y.sonraki_tarih),
                       p.ad + ' ' + p.soyad
                FROM isg.yasal_takip y
                LEFT JOIN ik.personeller p ON y.sorumlu_id = p.id
                WHERE y.aktif_mi = 1 ORDER BY y.sonraki_tarih ASC
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")
    
    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        geciken = 0
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 5:
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    if val is not None and val < 0:
                        item.setForeground(QColor(self.theme.get('danger')))
                        item.setText(f"{val} (GECİKMİŞ)")
                        geciken += 1
                    elif val is not None and val <= 30:
                        item.setForeground(QColor(self.theme.get('warning')))
                    else:
                        item.setForeground(QColor(self.theme.get('success')))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)
        self.lbl_stat.setText(f"Toplam: {len(rows)} | Süresi geçen: {geciken}")
    
    def _show_geciken(self):
        self._display_data([r for r in self.all_rows if r[5] is not None and r[5] < 0])
    
    def _tamamla(self):
        row = self.table.currentRow()
        if row < 0: return
        kayit_id = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, "Onay", "Gereklilik tamamlandı olarak işaretlensin mi?") != QMessageBox.Yes:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE isg.yasal_takip SET son_yapilma_tarihi = GETDATE(), sonraki_tarih = DATEADD(DAY, periyot_gun, GETDATE()) WHERE id = ?", (kayit_id,))
            conn.commit()
            conn.close()
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _yeni(self):
        dialog = YasalTakipDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        dialog = YasalTakipDialog(self.theme, self, int(self.table.item(row, 0).text()))
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
