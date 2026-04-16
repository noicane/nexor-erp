# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Şoför Tanımları
e-İrsaliye için şoför bilgileri
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame
)
from PySide6.QtCore import Qt
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


class SoforDialog(QDialog):
    """Şoför ekleme/düzenleme dialogu"""
    
    def __init__(self, theme: dict, parent=None, sofor_id=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.sofor_id = sofor_id
        self.setWindowTitle("Şoför Ekle" if not sofor_id else "Şoför Düzenle")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._setup_ui()
        
        if sofor_id:
            self._load_data()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{ background: {s['card_bg']}; }}
            QLabel {{ color: {s['text']}; }}
            QLineEdit, QComboBox {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 6px;
                padding: 8px;
                color: {s['text']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Başlık
        title = QLabel("🚗 Şoför Bilgileri")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {s['primary']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        # Ad Soyad
        self.txt_ad_soyad = QLineEdit()
        self.txt_ad_soyad.setPlaceholderText("Örn: Ahmet Yılmaz")
        form.addRow("Ad Soyad*:", self.txt_ad_soyad)
        
        # TC Kimlik No
        self.txt_tc = QLineEdit()
        self.txt_tc.setMaxLength(11)
        self.txt_tc.setPlaceholderText("11 haneli TC Kimlik No")
        form.addRow("TC Kimlik No*:", self.txt_tc)
        
        # Telefon
        self.txt_telefon = QLineEdit()
        self.txt_telefon.setPlaceholderText("05XX XXX XX XX")
        form.addRow("Telefon:", self.txt_telefon)
        
        # Ehliyet Sınıfı
        self.cmb_ehliyet = QComboBox()
        self.cmb_ehliyet.addItems(["B", "C", "D", "E", "B+E", "C+E", "D+E"])
        form.addRow("Ehliyet Sınıfı:", self.cmb_ehliyet)
        
        # Ehliyet No
        self.txt_ehliyet_no = QLineEdit()
        self.txt_ehliyet_no.setPlaceholderText("Ehliyet seri no")
        form.addRow("Ehliyet No:", self.txt_ehliyet_no)
        
        # Aktif
        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        self.chk_aktif.setStyleSheet(f"color: {s['text']};")
        form.addRow("", self.chk_aktif)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {s['input_bg']}; color: {s['text']}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {s['success']}; color: white; padding: 10px 24px; border-radius: 6px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        """Mevcut şoför verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ad_soyad, tc_kimlik_no, telefon, ehliyet_sinifi, ehliyet_no, aktif_mi
                FROM lojistik.soforler WHERE id = ?
            """, (self.sofor_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_ad_soyad.setText(row[0] or "")
                self.txt_tc.setText(row[1] or "")
                self.txt_telefon.setText(row[2] or "")
                if row[3]:
                    idx = self.cmb_ehliyet.findText(row[3])
                    if idx >= 0:
                        self.cmb_ehliyet.setCurrentIndex(idx)
                self.txt_ehliyet_no.setText(row[4] or "")
                self.chk_aktif.setChecked(row[5] if row[5] is not None else True)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _save(self):
        """Şoförü kaydet"""
        ad_soyad = self.txt_ad_soyad.text().strip()
        tc = self.txt_tc.text().strip()
        
        if not ad_soyad:
            QMessageBox.warning(self, "Uyarı", "Ad Soyad zorunludur!")
            return
        
        if not tc or len(tc) != 11 or not tc.isdigit():
            QMessageBox.warning(self, "Uyarı", "TC Kimlik No 11 haneli olmalıdır!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            telefon = self.txt_telefon.text().strip() or None
            ehliyet_sinifi = self.cmb_ehliyet.currentText()
            ehliyet_no = self.txt_ehliyet_no.text().strip() or None
            
            if self.sofor_id:
                cursor.execute("""
                    UPDATE lojistik.soforler SET
                        ad_soyad = ?, tc_kimlik_no = ?, telefon = ?, 
                        ehliyet_sinifi = ?, ehliyet_no = ?, aktif_mi = ?
                    WHERE id = ?
                """, (ad_soyad, tc, telefon, ehliyet_sinifi, ehliyet_no, 
                      self.chk_aktif.isChecked(), self.sofor_id))
            else:
                # TC kontrolü
                cursor.execute("SELECT COUNT(*) FROM lojistik.soforler WHERE tc_kimlik_no = ?", (tc,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu TC Kimlik No zaten kayıtlı!")
                    conn.close()
                    return
                
                cursor.execute("""
                    INSERT INTO lojistik.soforler (ad_soyad, tc_kimlik_no, telefon, ehliyet_sinifi, ehliyet_no, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ad_soyad, tc, telefon, ehliyet_sinifi, ehliyet_no, self.chk_aktif.isChecked()))
            
            conn.commit()
            conn.close()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class TanimSoforlerPage(BasePage):
    """Şoför Tanımları Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("🚗 Şoför Tanımları")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {s['text']};")
        layout.addWidget(header)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {s['card_bg']}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Şoför")
        btn_yeni.setStyleSheet(f"background: {s['success']}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(f"background: {s['input_bg']}; color: {s['text']}; padding: 8px 16px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar_layout.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background: {s['danger']}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._sil)
        toolbar_layout.addWidget(btn_sil)
        
        toolbar_layout.addStretch()
        
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.setStyleSheet(f"background: {s['input_bg']}; color: {s['text']}; padding: 8px 16px; border-radius: 6px;")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Ad Soyad", "TC Kimlik No", "Telefon", "Ehliyet", "Ehliyet No", "Durum"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                color: {s['text']};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QTableWidget::item:selected {{ background: {s['primary']}; }}
            QHeaderView::section {{
                background: {s['input_bg']};
                color: {s['text']};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {s['primary']};
                font-weight: bold;
            }}
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 80)
        
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        # İstatistik
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(f"color: {s['text_secondary']};")
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        """Şoför listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ad_soyad, tc_kimlik_no, telefon, ehliyet_sinifi, ehliyet_no, aktif_mi
                FROM lojistik.soforler
                ORDER BY ad_soyad
            """)
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            aktif_sayisi = 0
            
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or "-"))
                self.table.setItem(i, 4, QTableWidgetItem(row[4] or "-"))
                self.table.setItem(i, 5, QTableWidgetItem(row[5] or "-"))
                
                aktif = row[6]
                durum_item = QTableWidgetItem("✓ Aktif" if aktif else "✗ Pasif")
                durum_item.setForeground(QColor(brand.SUCCESS if aktif else brand.ERROR))
                self.table.setItem(i, 6, durum_item)
                
                if aktif:
                    aktif_sayisi += 1
            
            self.lbl_stat.setText(f"Toplam: {len(rows)} şoför | Aktif: {aktif_sayisi}")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _yeni(self):
        dialog = SoforDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şoför seçin!")
            return
        
        sofor_id = int(self.table.item(row, 0).text())
        dialog = SoforDialog(self.theme, self, sofor_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _sil(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şoför seçin!")
            return
        
        sofor_id = int(self.table.item(row, 0).text())
        ad = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Onay", f"'{ad}' şoförünü silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE lojistik.soforler SET aktif_mi = 0 WHERE id = ?", (sofor_id,))
                conn.commit()
                conn.close()
                self._load_data()
                QMessageBox.information(self, "Başarılı", "Şoför pasif yapıldı.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
