# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İSG GBF/MSDS
Güvenlik Bilgi Formları (Material Safety Data Sheet)
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


class GBFDialog(QDialog):
    """GBF/MSDS kaydı"""
    
    def __init__(self, theme: dict, parent=None, gbf_id=None):
        super().__init__(parent)
        self.theme = theme
        self.gbf_id = gbf_id
        self.setWindowTitle("Güvenlik Bilgi Formu" if not gbf_id else "GBF Düzenle")
        self.setMinimumWidth(550)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if gbf_id:
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
        
        self.txt_kimyasal = QLineEdit()
        form.addRow("Kimyasal Adı*:", self.txt_kimyasal)
        
        self.cmb_urun = QComboBox()
        form.addRow("Stok Kartı:", self.cmb_urun)
        
        self.txt_uretici = QLineEdit()
        form.addRow("Üretici Firma:", self.txt_uretici)
        
        self.txt_cas = QLineEdit()
        self.txt_cas.setPlaceholderText("Örn: 7732-18-5")
        form.addRow("CAS No:", self.txt_cas)
        
        self.txt_un = QLineEdit()
        self.txt_un.setPlaceholderText("Örn: UN1993")
        form.addRow("UN No:", self.txt_un)
        
        # Tehlike bilgileri
        lbl_tehlike = QLabel("⚠️ Tehlike Bilgileri")
        lbl_tehlike.setStyleSheet(f"font-weight: bold; color: {self.theme.get('warning')}; margin-top: 10px;")
        form.addRow("", lbl_tehlike)
        
        self.txt_sinif = QLineEdit()
        self.txt_sinif.setPlaceholderText("GHS sınıflandırması")
        form.addRow("Tehlike Sınıfı:", self.txt_sinif)
        
        self.txt_h_kod = QLineEdit()
        self.txt_h_kod.setPlaceholderText("Örn: H302, H315, H319")
        form.addRow("H Kodları:", self.txt_h_kod)
        
        self.txt_p_kod = QLineEdit()
        self.txt_p_kod.setPlaceholderText("Örn: P264, P280, P301+P312")
        form.addRow("P Kodları:", self.txt_p_kod)
        
        self.date_revizyon = QDateEdit()
        self.date_revizyon.setDate(QDate.currentDate())
        self.date_revizyon.setCalendarPopup(True)
        form.addRow("GBF Revizyon Tarihi:", self.date_revizyon)
        
        self.txt_dosya = QLineEdit()
        self.txt_dosya.setPlaceholderText("GBF dosya yolu...")
        form.addRow("Dosya Yolu:", self.txt_dosya)
        
        self.txt_kullanim = QTextEdit()
        self.txt_kullanim.setMaximumHeight(60)
        self.txt_kullanim.setPlaceholderText("Kullanıldığı alanlar...")
        form.addRow("Kullanım Alanları:", self.txt_kullanim)
        
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
            self.cmb_urun.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM stok.urunler WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_urun.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception:
            pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kimyasal_adi, urun_id, uretici_firma, cas_no, un_no,
                       tehlike_sinifi, h_kodlari, p_kodlari, gbf_revizyon_tarihi,
                       gbf_dosya_yolu, kullanim_alanlari
                FROM isg.guvenlik_bilgi_formlari WHERE id = ?
            """, (self.gbf_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_kimyasal.setText(row[0] or "")
                if row[1]:
                    idx = self.cmb_urun.findData(row[1])
                    if idx >= 0: self.cmb_urun.setCurrentIndex(idx)
                self.txt_uretici.setText(row[2] or "")
                self.txt_cas.setText(row[3] or "")
                self.txt_un.setText(row[4] or "")
                self.txt_sinif.setText(row[5] or "")
                self.txt_h_kod.setText(row[6] or "")
                self.txt_p_kod.setText(row[7] or "")
                if row[8]: self.date_revizyon.setDate(QDate(row[8].year, row[8].month, row[8].day))
                self.txt_dosya.setText(row[9] or "")
                self.txt_kullanim.setPlainText(row[10] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        kimyasal = self.txt_kimyasal.text().strip()
        if not kimyasal:
            QMessageBox.warning(self, "Uyarı", "Kimyasal adı zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.gbf_id:
                cursor.execute("""
                    UPDATE isg.guvenlik_bilgi_formlari SET
                        kimyasal_adi = ?, urun_id = ?, uretici_firma = ?, cas_no = ?, un_no = ?,
                        tehlike_sinifi = ?, h_kodlari = ?, p_kodlari = ?, gbf_revizyon_tarihi = ?,
                        gbf_dosya_yolu = ?, kullanim_alanlari = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    kimyasal, self.cmb_urun.currentData(), self.txt_uretici.text().strip() or None,
                    self.txt_cas.text().strip() or None, self.txt_un.text().strip() or None,
                    self.txt_sinif.text().strip() or None, self.txt_h_kod.text().strip() or None,
                    self.txt_p_kod.text().strip() or None, self.date_revizyon.date().toPython(),
                    self.txt_dosya.text().strip() or None, self.txt_kullanim.toPlainText().strip() or None,
                    self.gbf_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO isg.guvenlik_bilgi_formlari
                    (kimyasal_adi, urun_id, uretici_firma, cas_no, un_no, tehlike_sinifi,
                     h_kodlari, p_kodlari, gbf_revizyon_tarihi, gbf_dosya_yolu, kullanim_alanlari)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    kimyasal, self.cmb_urun.currentData(), self.txt_uretici.text().strip() or None,
                    self.txt_cas.text().strip() or None, self.txt_un.text().strip() or None,
                    self.txt_sinif.text().strip() or None, self.txt_h_kod.text().strip() or None,
                    self.txt_p_kod.text().strip() or None, self.date_revizyon.date().toPython(),
                    self.txt_dosya.text().strip() or None, self.txt_kullanim.toPlainText().strip() or None
                ))
            
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class ISGGBFPage(BasePage):
    """İSG GBF/MSDS Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("📋 Güvenlik Bilgi Formları (GBF/MSDS)")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni GBF")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar_layout.addWidget(btn_duzenle)
        
        toolbar_layout.addStretch()
        
        self.txt_arama = QLineEdit()
        self.txt_arama.setPlaceholderText("🔍 Kimyasal ara...")
        self.txt_arama.setFixedWidth(200)
        self.txt_arama.textChanged.connect(self._filter)
        toolbar_layout.addWidget(self.txt_arama)
        
        btn_yenile = QPushButton("🔄")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Kimyasal", "Üretici", "CAS No", "Tehlike", "H Kodları", "Revizyon"])
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
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 150)
        self.table.setColumnWidth(6, 90)
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        self.lbl_stat = QLabel()
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kimyasal_adi, uretici_firma, cas_no, tehlike_sinifi, h_kodlari,
                       FORMAT(gbf_revizyon_tarihi, 'dd.MM.yyyy')
                FROM isg.guvenlik_bilgi_formlari
                WHERE aktif_mi = 1
                ORDER BY kimyasal_adi
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")
    
    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 4 and val:  # Tehlike sınıfı
                    item = QTableWidgetItem(str(val))
                    item.setForeground(QColor(self.theme.get('warning')))
                elif j == 5 and val:  # H kodları
                    item = QTableWidgetItem(str(val))
                    item.setForeground(QColor(self.theme.get('danger')))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)
        
        self.lbl_stat.setText(f"Toplam: {len(rows)} kimyasal")
    
    def _filter(self):
        arama = self.txt_arama.text().lower()
        if not arama:
            self._display_data(self.all_rows)
        else:
            filtered = [r for r in self.all_rows if arama in str(r[1]).lower() or arama in str(r[3]).lower()]
            self._display_data(filtered)
    
    def _yeni(self):
        dialog = GBFDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        gbf_id = int(self.table.item(row, 0).text())
        dialog = GBFDialog(self.theme, self, gbf_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
