# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İSG Sağlık Gözetimi
Periyodik Muayene Takibi
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class SaglikDialog(QDialog):
    """Sağlık muayenesi kaydı"""
    
    def __init__(self, theme: dict, parent=None, kayit_id=None):
        super().__init__(parent)
        self.theme = theme
        self.kayit_id = kayit_id
        self.setWindowTitle("Sağlık Muayenesi" if not kayit_id else "Muayene Düzenle")
        self.setMinimumWidth(550)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if kayit_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit {{
                background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')};
                border-radius: 6px; padding: 8px; color: {self.theme.get('text')};
            }}
        """)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.cmb_personel = QComboBox()
        form.addRow("Personel*:", self.cmb_personel)
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["ISE_GIRIS", "PERIYODIK", "IS_DEGISIKLIGI", "ISTEN_AYRILMA"])
        form.addRow("Muayene Tipi*:", self.cmb_tip)
        
        self.date_muayene = QDateEdit()
        self.date_muayene.setDate(QDate.currentDate())
        self.date_muayene.setCalendarPopup(True)
        form.addRow("Muayene Tarihi*:", self.date_muayene)
        
        self.cmb_sonuc = QComboBox()
        self.cmb_sonuc.addItems(["UYGUN", "UYGUN_DEGIL", "SARTLI_UYGUN"])
        form.addRow("Sonuç*:", self.cmb_sonuc)
        
        self.txt_kisitlama = QTextEdit()
        self.txt_kisitlama.setMaximumHeight(60)
        self.txt_kisitlama.setPlaceholderText("Varsa çalışma kısıtlamaları...")
        form.addRow("Kısıtlamalar:", self.txt_kisitlama)
        
        self.txt_hekim = QLineEdit()
        form.addRow("Hekim:", self.txt_hekim)
        
        self.txt_kurum = QLineEdit()
        form.addRow("Sağlık Kuruluşu:", self.txt_kurum)
        
        self.txt_rapor_no = QLineEdit()
        form.addRow("Rapor No:", self.txt_rapor_no)
        
        self.date_sonraki = QDateEdit()
        self.date_sonraki.setDate(QDate.currentDate().addYears(1))
        self.date_sonraki.setCalendarPopup(True)
        form.addRow("Sonraki Muayene:", self.date_sonraki)
        
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(50)
        form.addRow("Notlar:", self.txt_notlar)
        
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
            self.cmb_personel.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_personel.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except:
            pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT personel_id, muayene_tipi, muayene_tarihi, sonuc, kisitlamalar,
                       hekim_adi, saglik_kurulugu, rapor_no, sonraki_muayene_tarihi, notlar
                FROM isg.saglik_gozetimi WHERE id = ?
            """, (self.kayit_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                if row[0]:
                    idx = self.cmb_personel.findData(row[0])
                    if idx >= 0: self.cmb_personel.setCurrentIndex(idx)
                if row[1]:
                    idx = self.cmb_tip.findText(row[1])
                    if idx >= 0: self.cmb_tip.setCurrentIndex(idx)
                if row[2]: self.date_muayene.setDate(QDate(row[2].year, row[2].month, row[2].day))
                if row[3]:
                    idx = self.cmb_sonuc.findText(row[3])
                    if idx >= 0: self.cmb_sonuc.setCurrentIndex(idx)
                self.txt_kisitlama.setPlainText(row[4] or "")
                self.txt_hekim.setText(row[5] or "")
                self.txt_kurum.setText(row[6] or "")
                self.txt_rapor_no.setText(row[7] or "")
                if row[8]: self.date_sonraki.setDate(QDate(row[8].year, row[8].month, row[8].day))
                self.txt_notlar.setPlainText(row[9] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        if not self.cmb_personel.currentData():
            QMessageBox.warning(self, "Uyarı", "Personel seçin!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.kayit_id:
                cursor.execute("""
                    UPDATE isg.saglik_gozetimi SET
                        personel_id = ?, muayene_tipi = ?, muayene_tarihi = ?, sonuc = ?,
                        kisitlamalar = ?, hekim_adi = ?, saglik_kurulugu = ?, rapor_no = ?,
                        sonraki_muayene_tarihi = ?, notlar = ?
                    WHERE id = ?
                """, (
                    self.cmb_personel.currentData(), self.cmb_tip.currentText(),
                    self.date_muayene.date().toPython(), self.cmb_sonuc.currentText(),
                    self.txt_kisitlama.toPlainText().strip() or None,
                    self.txt_hekim.text().strip() or None, self.txt_kurum.text().strip() or None,
                    self.txt_rapor_no.text().strip() or None, self.date_sonraki.date().toPython(),
                    self.txt_notlar.toPlainText().strip() or None, self.kayit_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO isg.saglik_gozetimi
                    (personel_id, muayene_tipi, muayene_tarihi, sonuc, kisitlamalar, hekim_adi,
                     saglik_kurulugu, rapor_no, sonraki_muayene_tarihi, notlar)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.cmb_personel.currentData(), self.cmb_tip.currentText(),
                    self.date_muayene.date().toPython(), self.cmb_sonuc.currentText(),
                    self.txt_kisitlama.toPlainText().strip() or None,
                    self.txt_hekim.text().strip() or None, self.txt_kurum.text().strip() or None,
                    self.txt_rapor_no.text().strip() or None, self.date_sonraki.date().toPython(),
                    self.txt_notlar.toPlainText().strip() or None
                ))
            
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class ISGSaglikGozetimiPage(BasePage):
    """İSG Sağlık Gözetimi Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("🏥 Sağlık Gözetimi")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Muayene")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar_layout.addWidget(btn_duzenle)
        
        btn_geciken = QPushButton("⚠️ Süresi Geçenler")
        btn_geciken.setStyleSheet(f"background: {self.theme.get('warning')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_geciken.clicked.connect(self._show_geciken)
        toolbar_layout.addWidget(btn_geciken)
        
        toolbar_layout.addStretch()
        
        self.txt_arama = QLineEdit()
        self.txt_arama.setPlaceholderText("🔍 Personel ara...")
        self.txt_arama.setFixedWidth(200)
        self.txt_arama.textChanged.connect(self._filter)
        toolbar_layout.addWidget(self.txt_arama)
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 12px; color: {self.theme.get('text')};")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Personel", "Tip", "Tarih", "Sonuç", "Sonraki", "Kalan Gün", "Kısıtlama"])
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
                SELECT s.id, p.ad + ' ' + p.soyad, s.muayene_tipi, FORMAT(s.muayene_tarihi, 'dd.MM.yyyy'),
                       s.sonuc, FORMAT(s.sonraki_muayene_tarihi, 'dd.MM.yyyy'),
                       DATEDIFF(DAY, GETDATE(), s.sonraki_muayene_tarihi),
                       CASE WHEN s.kisitlamalar IS NOT NULL THEN 'VAR' ELSE '' END
                FROM isg.saglik_gozetimi s
                JOIN ik.personeller p ON s.personel_id = p.id
                ORDER BY s.sonraki_muayene_tarihi ASC
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
                if j == 4:  # Sonuç
                    item = QTableWidgetItem(str(val) if val else "")
                    if val == "UYGUN":
                        item.setForeground(QColor(self.theme.get('success')))
                    elif val == "UYGUN_DEGIL":
                        item.setForeground(QColor(self.theme.get('danger')))
                    elif val == "SARTLI_UYGUN":
                        item.setForeground(QColor(self.theme.get('warning')))
                elif j == 6:  # Kalan gün
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    if val is not None and val < 0:
                        item.setForeground(QColor(self.theme.get('danger')))
                        item.setText(f"{val} (GECİKMİŞ)")
                        geciken += 1
                    elif val is not None and val <= 30:
                        item.setForeground(QColor(self.theme.get('warning')))
                elif j == 7 and val:  # Kısıtlama
                    item = QTableWidgetItem(val)
                    item.setForeground(QColor(self.theme.get('danger')))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)
        
        self.lbl_stat.setText(f"Toplam: {len(rows)} muayene | Süresi geçen: {geciken}")
    
    def _filter(self):
        arama = self.txt_arama.text().lower()
        if not arama:
            self._display_data(self.all_rows)
        else:
            filtered = [r for r in self.all_rows if arama in str(r[1]).lower()]
            self._display_data(filtered)
    
    def _show_geciken(self):
        geciken = [r for r in self.all_rows if r[6] is not None and r[6] < 0]
        self._display_data(geciken)
    
    def _yeni(self):
        dialog = SaglikDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        kayit_id = int(self.table.item(row, 0).text())
        dialog = SaglikDialog(self.theme, self, kayit_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
