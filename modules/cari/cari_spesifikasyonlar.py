# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Cari Spesifikasyonlar Yönetimi
musteri.cari_spesifikasyonlar tablosu üzerinden müşteri özel gereksinimleri

Tablo: musteri.cari_spesifikasyonlar
- id, uuid, cari_id, spesifikasyon_tipi, kriter_adi
- deger, tolerans_min, tolerans_max, birim
- zorunlu_mu, kontrol_frekansi, test_metodu
- aciklama, referans_dokuman
- aktif_mi, olusturma_tarihi, guncelleme_tarihi
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QCheckBox, QTextEdit, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
import uuid


class SpesifikasyonDialog(QDialog):
    """Spesifikasyon Ekleme/Düzenleme Dialog"""
    
    def __init__(self, theme: dict, cari_id: int, spec_data: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.cari_id = cari_id
        self.spec_data = spec_data or {}
        self.is_edit = bool(spec_data)
        
        self.setWindowTitle("Spesifikasyon Düzenle" if self.is_edit else "Yeni Spesifikasyon")
        self.setMinimumWidth(500)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox {{
                background: {self.theme['bg_input']};
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme['text']};
            }}
            QCheckBox {{ color: {self.theme['text']}; }}
        """)
        
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Spesifikasyon Tipi
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["KAPLAMA", "KALINLIK", "RENK", "TEST", "PAKETLEME", "ETIKET", "DIGER"])
        if self.spec_data.get('spesifikasyon_tipi'):
            idx = self.cmb_tip.findText(self.spec_data['spesifikasyon_tipi'])
            if idx >= 0:
                self.cmb_tip.setCurrentIndex(idx)
        layout.addRow("Tip:", self.cmb_tip)
        
        # Kriter Adı
        self.txt_kriter = QLineEdit()
        self.txt_kriter.setText(self.spec_data.get('kriter_adi', ''))
        self.txt_kriter.setPlaceholderText("Örn: Min. Kaplama Kalınlığı")
        layout.addRow("Kriter Adı *:", self.txt_kriter)
        
        # Değer
        self.txt_deger = QLineEdit()
        self.txt_deger.setText(self.spec_data.get('deger', ''))
        self.txt_deger.setPlaceholderText("Örn: 12 µm, RAL 9005, ...")
        layout.addRow("Değer:", self.txt_deger)
        
        # Tolerans
        tol_layout = QHBoxLayout()
        self.spin_tol_min = QDoubleSpinBox()
        self.spin_tol_min.setRange(-99999, 99999)
        self.spin_tol_min.setDecimals(2)
        self.spin_tol_min.setValue(self.spec_data.get('tolerans_min') or 0)
        tol_layout.addWidget(QLabel("Min:"))
        tol_layout.addWidget(self.spin_tol_min)
        
        self.spin_tol_max = QDoubleSpinBox()
        self.spin_tol_max.setRange(-99999, 99999)
        self.spin_tol_max.setDecimals(2)
        self.spin_tol_max.setValue(self.spec_data.get('tolerans_max') or 0)
        tol_layout.addWidget(QLabel("Max:"))
        tol_layout.addWidget(self.spin_tol_max)
        layout.addRow("Tolerans:", tol_layout)
        
        # Birim
        self.cmb_birim = QComboBox()
        self.cmb_birim.setEditable(True)
        self.cmb_birim.addItems(["", "µm", "mm", "saat", "adet", "%", "g/m²", "N/mm²"])
        if self.spec_data.get('birim'):
            self.cmb_birim.setCurrentText(self.spec_data['birim'])
        layout.addRow("Birim:", self.cmb_birim)
        
        # Test Metodu
        self.txt_test = QLineEdit()
        self.txt_test.setText(self.spec_data.get('test_metodu', ''))
        self.txt_test.setPlaceholderText("Örn: Elcometer, Tuz Testi")
        layout.addRow("Test Metodu:", self.txt_test)
        
        # Kontrol Frekansı
        self.cmb_frekans = QComboBox()
        self.cmb_frekans.addItems(["", "Her Parti", "Günlük", "Haftalık", "Aylık", "Sipariş Başı"])
        if self.spec_data.get('kontrol_frekansi'):
            self.cmb_frekans.setCurrentText(self.spec_data['kontrol_frekansi'])
        layout.addRow("Kontrol Frekansı:", self.cmb_frekans)
        
        # Referans Doküman
        self.txt_referans = QLineEdit()
        self.txt_referans.setText(self.spec_data.get('referans_dokuman', ''))
        self.txt_referans.setPlaceholderText("Örn: SPEC-001, ISO 9227")
        layout.addRow("Referans:", self.txt_referans)
        
        # Açıklama
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setPlainText(self.spec_data.get('aciklama', ''))
        self.txt_aciklama.setMaximumHeight(60)
        layout.addRow("Açıklama:", self.txt_aciklama)
        
        # Zorunlu mu
        self.chk_zorunlu = QCheckBox("Bu kriter zorunludur")
        self.chk_zorunlu.setChecked(self.spec_data.get('zorunlu_mu', True))
        layout.addRow("", self.chk_zorunlu)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_iptal)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_kaydet)
        layout.addRow("", btn_layout)
    
    def _save(self):
        kriter_adi = self.txt_kriter.text().strip()
        
        if not kriter_adi:
            QMessageBox.warning(self, "Uyarı", "Kriter adı zorunludur!")
            return
        
        self.result_data = {
            'spesifikasyon_tipi': self.cmb_tip.currentText(),
            'kriter_adi': kriter_adi,
            'deger': self.txt_deger.text().strip() or None,
            'tolerans_min': self.spin_tol_min.value() if self.spin_tol_min.value() != 0 else None,
            'tolerans_max': self.spin_tol_max.value() if self.spin_tol_max.value() != 0 else None,
            'birim': self.cmb_birim.currentText().strip() or None,
            'test_metodu': self.txt_test.text().strip() or None,
            'kontrol_frekansi': self.cmb_frekans.currentText() or None,
            'referans_dokuman': self.txt_referans.text().strip() or None,
            'aciklama': self.txt_aciklama.toPlainText().strip() or None,
            'zorunlu_mu': 1 if self.chk_zorunlu.isChecked() else 0
        }
        self.accept()
    
    def get_data(self):
        return getattr(self, 'result_data', {})


class CariSpesifikasyonlarPage(BasePage):
    """Cari Spesifikasyonlar Yönetimi Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.selected_cari_id = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📝 Cari Spesifikasyonlar")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Cari Seçimi
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {self.theme['bg_card_solid']}; border-radius: 8px; padding: 12px;")
        f_layout = QHBoxLayout(filter_frame)
        
        f_layout.addWidget(QLabel("Cari Seçin:"))
        self.cmb_cari = QComboBox()
        self.cmb_cari.setMinimumWidth(400)
        self.cmb_cari.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']};")
        self.cmb_cari.currentIndexChanged.connect(self._on_cari_changed)
        f_layout.addWidget(self.cmb_cari)
        f_layout.addStretch()
        
        btn_yeni = QPushButton("+ Yeni Spesifikasyon")
        btn_yeni.setCursor(Qt.PointingHandCursor)
        btn_yeni.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni_spec)
        f_layout.addWidget(btn_yeni)
        
        layout.addWidget(filter_frame)
        
        # Spesifikasyon Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(["ID", "Tip", "Kriter", "Değer", "Tolerans", "Birim", "Test", "Zorunlu", "Durum", "İşlem"])
        self.table.setStyleSheet(self._table_style())
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(9, 170)
        self.table.doubleClicked.connect(self._duzenle_spec)
        layout.addWidget(self.table, 1)
        
        self._load_cariler()
    
    def _table_style(self):
        return f"""
            QTableWidget {{ background: {self.theme['bg_main']}; border: 1px solid {self.theme['border']}; gridline-color: {self.theme['border']}; }}
            QTableWidget::item {{ padding: 8px; color: {self.theme['text']}; }}
            QHeaderView::section {{ background: {self.theme['bg_card_solid']}; color: {self.theme['text']}; padding: 10px; border: none; border-bottom: 2px solid {self.theme['primary']}; font-weight: bold; }}
        """
    
    def _button_style(self):
        return f"QPushButton {{ background: {self.theme['bg_card_solid']}; color: {self.theme['text']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px 16px; }} QPushButton:hover {{ background: {self.theme['bg_hover']}; }}"
    
    def _load_cariler(self):
        self.cmb_cari.clear()
        self.cmb_cari.addItem("-- Cari Seçiniz --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, cari_kodu, unvan FROM musteri.cariler WHERE aktif_mi = 1 AND (silindi_mi = 0 OR silindi_mi IS NULL) ORDER BY unvan")
            for row in cursor.fetchall():
                self.cmb_cari.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Cariler yüklenemedi: {e}")
    
    def _on_cari_changed(self):
        self.selected_cari_id = self.cmb_cari.currentData()
        self._load_specs()
    
    def _load_specs(self):
        self.table.setRowCount(0)
        if not self.selected_cari_id:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, spesifikasyon_tipi, kriter_adi, deger, tolerans_min, tolerans_max, birim, test_metodu, zorunlu_mu, aktif_mi
                FROM musteri.cari_spesifikasyonlar
                WHERE cari_id = ? AND (silindi_mi = 0 OR silindi_mi IS NULL)
                ORDER BY spesifikasyon_tipi, kriter_adi
            """, (self.selected_cari_id,))
            
            for row in cursor.fetchall():
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(r, 1, QTableWidgetItem(row[1] or ""))
                self.table.setItem(r, 2, QTableWidgetItem(row[2] or ""))
                self.table.setItem(r, 3, QTableWidgetItem(row[3] or ""))
                
                # Tolerans gösterimi
                tol_min = row[4]
                tol_max = row[5]
                tol_str = ""
                if tol_min is not None or tol_max is not None:
                    tol_str = f"{tol_min or '-'} / {tol_max or '-'}"
                self.table.setItem(r, 4, QTableWidgetItem(tol_str))
                
                self.table.setItem(r, 5, QTableWidgetItem(row[6] or ""))
                self.table.setItem(r, 6, QTableWidgetItem(row[7] or ""))
                
                zorunlu = QTableWidgetItem("✓" if row[8] else "")
                zorunlu.setForeground(QColor('#ef4444'))
                self.table.setItem(r, 7, zorunlu)
                
                durum = QTableWidgetItem("✓" if row[9] else "✗")
                durum.setForeground(QColor('#22c55e') if row[9] else QColor('#ef4444'))
                self.table.setItem(r, 8, durum)

                rid = row[0]
                widget = self.create_action_buttons([
                    ("✏️", "Duzenle", lambda checked, rid=rid: self._duzenle_spec_by_id(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=rid: self._sil_spec_by_id(rid), "delete"),
                ])
                self.table.setCellWidget(r, 9, widget)
                self.table.setRowHeight(r, 42)

            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Spesifikasyonlar yüklenemedi: {e}")
    
    def _yeni_spec(self):
        if not self.selected_cari_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir cari seçin!")
            return
        
        dialog = SpesifikasyonDialog(self.theme, self.selected_cari_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO musteri.cari_spesifikasyonlar (uuid, cari_id, spesifikasyon_tipi, kriter_adi, deger, tolerans_min, tolerans_max, birim, test_metodu, kontrol_frekansi, referans_dokuman, aciklama, zorunlu_mu, aktif_mi, olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, GETDATE(), GETDATE(), 0)
                """, (str(uuid.uuid4()), self.selected_cari_id, data['spesifikasyon_tipi'], data['kriter_adi'], data['deger'], data['tolerans_min'], data['tolerans_max'], data['birim'], data['test_metodu'], data['kontrol_frekansi'], data['referans_dokuman'], data['aciklama'], data['zorunlu_mu']))
                
                conn.commit()
                conn.close()
                self._load_specs()
                QMessageBox.information(self, "Başarılı", "Spesifikasyon eklendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Spesifikasyon eklenemedi: {e}")
    
    def _duzenle_spec_by_id(self, spec_id):
        """ID ile spesifikasyon düzenleme (satır butonundan)"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT spesifikasyon_tipi, kriter_adi, deger, tolerans_min, tolerans_max, birim, test_metodu, kontrol_frekansi, referans_dokuman, aciklama, zorunlu_mu
                FROM musteri.cari_spesifikasyonlar WHERE id = ?
            """, (spec_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return

            mevcut = {
                'spesifikasyon_tipi': row[0], 'kriter_adi': row[1], 'deger': row[2],
                'tolerans_min': row[3], 'tolerans_max': row[4], 'birim': row[5],
                'test_metodu': row[6], 'kontrol_frekansi': row[7], 'referans_dokuman': row[8],
                'aciklama': row[9], 'zorunlu_mu': row[10]
            }

            dialog = SpesifikasyonDialog(self.theme, self.selected_cari_id, mevcut, self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE musteri.cari_spesifikasyonlar SET spesifikasyon_tipi = ?, kriter_adi = ?, deger = ?, tolerans_min = ?, tolerans_max = ?, birim = ?, test_metodu = ?, kontrol_frekansi = ?, referans_dokuman = ?, aciklama = ?, zorunlu_mu = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (data['spesifikasyon_tipi'], data['kriter_adi'], data['deger'], data['tolerans_min'], data['tolerans_max'], data['birim'], data['test_metodu'], data['kontrol_frekansi'], data['referans_dokuman'], data['aciklama'], data['zorunlu_mu'], spec_id))

                conn.commit()
                conn.close()
                self._load_specs()
                QMessageBox.information(self, "Başarılı", "Spesifikasyon güncellendi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {e}")

    def _sil_spec_by_id(self, spec_id):
        """ID ile spesifikasyon silme (satır butonundan)"""
        reply = QMessageBox.question(self, "Onay", "Bu spesifikasyonu silmek istediğinize emin misiniz?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE musteri.cari_spesifikasyonlar SET silindi_mi = 1, silinme_tarihi = GETDATE() WHERE id = ?", (spec_id,))
                conn.commit()
                conn.close()
                self._load_specs()
                QMessageBox.information(self, "Başarılı", "Spesifikasyon silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    def _duzenle_spec(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir spesifikasyon seçin!")
            return
        
        spec_id = int(self.table.item(selected[0].row(), 0).text())
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT spesifikasyon_tipi, kriter_adi, deger, tolerans_min, tolerans_max, birim, test_metodu, kontrol_frekansi, referans_dokuman, aciklama, zorunlu_mu
                FROM musteri.cari_spesifikasyonlar WHERE id = ?
            """, (spec_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return
            
            mevcut = {
                'spesifikasyon_tipi': row[0], 'kriter_adi': row[1], 'deger': row[2],
                'tolerans_min': row[3], 'tolerans_max': row[4], 'birim': row[5],
                'test_metodu': row[6], 'kontrol_frekansi': row[7], 'referans_dokuman': row[8],
                'aciklama': row[9], 'zorunlu_mu': row[10]
            }
            
            dialog = SpesifikasyonDialog(self.theme, self.selected_cari_id, mevcut, self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE musteri.cari_spesifikasyonlar SET spesifikasyon_tipi = ?, kriter_adi = ?, deger = ?, tolerans_min = ?, tolerans_max = ?, birim = ?, test_metodu = ?, kontrol_frekansi = ?, referans_dokuman = ?, aciklama = ?, zorunlu_mu = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (data['spesifikasyon_tipi'], data['kriter_adi'], data['deger'], data['tolerans_min'], data['tolerans_max'], data['birim'], data['test_metodu'], data['kontrol_frekansi'], data['referans_dokuman'], data['aciklama'], data['zorunlu_mu'], spec_id))
                
                conn.commit()
                conn.close()
                self._load_specs()
                QMessageBox.information(self, "Başarılı", "Spesifikasyon güncellendi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {e}")
    
    def _sil_spec(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir spesifikasyon seçin!")
            return
        
        spec_id = int(self.table.item(selected[0].row(), 0).text())
        
        reply = QMessageBox.question(self, "Onay", "Bu spesifikasyonu silmek istediğinize emin misiniz?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE musteri.cari_spesifikasyonlar SET silindi_mi = 1, silinme_tarihi = GETDATE() WHERE id = ?", (spec_id,))
                conn.commit()
                conn.close()
                self._load_specs()
                QMessageBox.information(self, "Başarılı", "Spesifikasyon silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
