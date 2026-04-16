# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Araç Tanımları
e-İrsaliye için araç bilgileri
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QSpinBox
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


class AracDialog(QDialog):
    """Araç ekleme/düzenleme dialogu"""
    
    def __init__(self, theme: dict, parent=None, arac_id=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.arac_id = arac_id
        self.setWindowTitle("Araç Ekle" if not arac_id else "Araç Düzenle")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._setup_ui()
        
        if arac_id:
            self._load_data()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{ background: {s['card_bg']}; }}
            QLabel {{ color: {s['text']}; }}
            QLineEdit, QComboBox, QSpinBox {{
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
        title = QLabel("🚛 Araç Bilgileri")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {s['primary']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        # Plaka
        self.txt_plaka = QLineEdit()
        self.txt_plaka.setPlaceholderText("Örn: 16 ABC 123")
        form.addRow("Plaka*:", self.txt_plaka)
        
        # Araç Tipi
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems([
            "Kamyon", "Kamyonet", "TIR", "Çekici", "Dorse", 
            "Tanker", "Frigorifik", "Panelvan", "Pickup", "Diğer"
        ])
        form.addRow("Araç Tipi:", self.cmb_tip)
        
        # Marka
        self.txt_marka = QLineEdit()
        self.txt_marka.setPlaceholderText("Örn: Mercedes, Ford, Iveco")
        form.addRow("Marka:", self.txt_marka)
        
        # Model
        self.txt_model = QLineEdit()
        self.txt_model.setPlaceholderText("Örn: Actros, Cargo")
        form.addRow("Model:", self.txt_model)
        
        # Model Yılı
        self.spn_yil = QSpinBox()
        self.spn_yil.setRange(1990, 2030)
        self.spn_yil.setValue(2020)
        form.addRow("Model Yılı:", self.spn_yil)
        
        # Şasi No
        self.txt_sasi = QLineEdit()
        self.txt_sasi.setPlaceholderText("Şasi numarası")
        form.addRow("Şasi No:", self.txt_sasi)
        
        # Kapasite (ton)
        self.spn_kapasite = QSpinBox()
        self.spn_kapasite.setRange(0, 100)
        self.spn_kapasite.setValue(10)
        self.spn_kapasite.setSuffix(" ton")
        form.addRow("Kapasite:", self.spn_kapasite)
        
        # Ruhsat Sahibi
        self.txt_ruhsat_sahibi = QLineEdit()
        self.txt_ruhsat_sahibi.setPlaceholderText("Ruhsat sahibi adı/unvanı")
        form.addRow("Ruhsat Sahibi:", self.txt_ruhsat_sahibi)
        
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
        """Mevcut araç verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT plaka, arac_tipi, marka, model, model_yili, sasi_no, 
                       kapasite_ton, ruhsat_sahibi, aktif_mi
                FROM lojistik.araclar WHERE id = ?
            """, (self.arac_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_plaka.setText(row[0] or "")
                if row[1]:
                    idx = self.cmb_tip.findText(row[1])
                    if idx >= 0:
                        self.cmb_tip.setCurrentIndex(idx)
                self.txt_marka.setText(row[2] or "")
                self.txt_model.setText(row[3] or "")
                if row[4]:
                    self.spn_yil.setValue(row[4])
                self.txt_sasi.setText(row[5] or "")
                if row[6]:
                    self.spn_kapasite.setValue(int(row[6]))
                self.txt_ruhsat_sahibi.setText(row[7] or "")
                self.chk_aktif.setChecked(row[8] if row[8] is not None else True)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _save(self):
        """Aracı kaydet"""
        plaka = self.txt_plaka.text().strip().upper()
        
        if not plaka:
            QMessageBox.warning(self, "Uyarı", "Plaka zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            arac_tipi = self.cmb_tip.currentText()
            marka = self.txt_marka.text().strip() or None
            model = self.txt_model.text().strip() or None
            model_yili = self.spn_yil.value()
            sasi_no = self.txt_sasi.text().strip() or None
            kapasite = self.spn_kapasite.value()
            ruhsat_sahibi = self.txt_ruhsat_sahibi.text().strip() or None
            
            if self.arac_id:
                cursor.execute("""
                    UPDATE lojistik.araclar SET
                        plaka = ?, arac_tipi = ?, marka = ?, model = ?, model_yili = ?,
                        sasi_no = ?, kapasite_ton = ?, ruhsat_sahibi = ?, aktif_mi = ?
                    WHERE id = ?
                """, (plaka, arac_tipi, marka, model, model_yili, sasi_no, 
                      kapasite, ruhsat_sahibi, self.chk_aktif.isChecked(), self.arac_id))
            else:
                # Plaka kontrolü
                cursor.execute("SELECT COUNT(*) FROM lojistik.araclar WHERE plaka = ?", (plaka,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu plaka zaten kayıtlı!")
                    conn.close()
                    return
                
                cursor.execute("""
                    INSERT INTO lojistik.araclar (plaka, arac_tipi, marka, model, model_yili,
                        sasi_no, kapasite_ton, ruhsat_sahibi, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (plaka, arac_tipi, marka, model, model_yili, sasi_no, 
                      kapasite, ruhsat_sahibi, self.chk_aktif.isChecked()))
            
            conn.commit()
            conn.close()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class TanimAraclarPage(BasePage):
    """Araç Tanımları Sayfası"""
    
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
        header = QLabel("🚛 Araç Tanımları")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {s['text']};")
        layout.addWidget(header)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {s['card_bg']}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Araç")
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
        
        # Tip filtresi
        self.cmb_filtre = QComboBox()
        self.cmb_filtre.addItem("Tüm Araçlar", None)
        self.cmb_filtre.addItems(["Kamyon", "Kamyonet", "TIR", "Çekici", "Dorse", "Tanker", "Frigorifik", "Panelvan", "Pickup", "Diğer"])
        self.cmb_filtre.setStyleSheet(f"background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 6px; padding: 6px; min-width: 120px;")
        self.cmb_filtre.currentIndexChanged.connect(self._load_data)
        toolbar_layout.addWidget(self.cmb_filtre)
        
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.setStyleSheet(f"background: {s['input_bg']}; color: {s['text']}; padding: 8px 16px; border-radius: 6px;")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Plaka", "Tip", "Marka", "Model", "Yıl", "Kapasite", "Ruhsat Sahibi", "Durum"
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
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(8, 80)
        
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        # İstatistik
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(f"color: {s['text_secondary']};")
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        """Araç listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            filtre = self.cmb_filtre.currentText()
            if filtre and filtre != "Tüm Araçlar":
                cursor.execute("""
                    SELECT id, plaka, arac_tipi, marka, model, model_yili, 
                           kapasite_ton, ruhsat_sahibi, aktif_mi
                    FROM lojistik.araclar
                    WHERE arac_tipi = ?
                    ORDER BY plaka
                """, (filtre,))
            else:
                cursor.execute("""
                    SELECT id, plaka, arac_tipi, marka, model, model_yili, 
                           kapasite_ton, ruhsat_sahibi, aktif_mi
                    FROM lojistik.araclar
                    ORDER BY plaka
                """)
            
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            aktif_sayisi = 0
            
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or "-"))
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or "-"))
                self.table.setItem(i, 4, QTableWidgetItem(row[4] or "-"))
                self.table.setItem(i, 5, QTableWidgetItem(str(row[5]) if row[5] else "-"))
                self.table.setItem(i, 6, QTableWidgetItem(f"{row[6]} ton" if row[6] else "-"))
                self.table.setItem(i, 7, QTableWidgetItem(row[7] or "-"))
                
                aktif = row[8]
                durum_item = QTableWidgetItem("✓ Aktif" if aktif else "✗ Pasif")
                durum_item.setForeground(QColor(brand.SUCCESS if aktif else brand.ERROR))
                self.table.setItem(i, 8, durum_item)
                
                if aktif:
                    aktif_sayisi += 1
            
            self.lbl_stat.setText(f"Toplam: {len(rows)} araç | Aktif: {aktif_sayisi}")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _yeni(self):
        dialog = AracDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir araç seçin!")
            return
        
        arac_id = int(self.table.item(row, 0).text())
        dialog = AracDialog(self.theme, self, arac_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _sil(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir araç seçin!")
            return
        
        arac_id = int(self.table.item(row, 0).text())
        plaka = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Onay", f"'{plaka}' plakalı aracı silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE lojistik.araclar SET aktif_mi = 0 WHERE id = ?", (arac_id,))
                conn.commit()
                conn.close()
                self._load_data()
                QMessageBox.information(self, "Başarılı", "Araç pasif yapıldı.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
