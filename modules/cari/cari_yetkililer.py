# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Cari Yetkililer Yönetimi
musteri.cari_yetkililer tablosu üzerinden iletişim kişileri yönetimi

Tablo: musteri.cari_yetkililer
- id, uuid, cari_id, ad_soyad, unvan, departman
- telefon, cep_telefon, dahili, email
- varsayilan_mi, aktif_mi
- olusturma_tarihi, guncelleme_tarihi
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
import uuid


class YetkiliDialog(QDialog):
    """Yetkili Ekleme/Düzenleme Dialog"""
    
    def __init__(self, theme: dict, cari_id: int, yetkili_data: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.cari_id = cari_id
        self.yetkili_data = yetkili_data or {}
        self.is_edit = bool(yetkili_data)
        
        self.setWindowTitle("Yetkili Düzenle" if self.is_edit else "Yeni Yetkili")
        self.setMinimumWidth(450)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit, QComboBox {{
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
        
        # Ad Soyad
        self.txt_ad_soyad = QLineEdit()
        self.txt_ad_soyad.setText(self.yetkili_data.get('ad_soyad', ''))
        self.txt_ad_soyad.setPlaceholderText("Ad Soyad")
        layout.addRow("Ad Soyad *:", self.txt_ad_soyad)
        
        # Ünvan
        self.txt_unvan = QLineEdit()
        self.txt_unvan.setText(self.yetkili_data.get('unvan', ''))
        self.txt_unvan.setPlaceholderText("Örn: Satın Alma Müdürü")
        layout.addRow("Ünvan:", self.txt_unvan)
        
        # Departman
        self.cmb_departman = QComboBox()
        self.cmb_departman.setEditable(True)
        self.cmb_departman.addItems(["", "Satın Alma", "Kalite", "Üretim", "Muhasebe", "Sevkiyat", "Genel Müdürlük", "Teknik", "Diğer"])
        if self.yetkili_data.get('departman'):
            self.cmb_departman.setCurrentText(self.yetkili_data['departman'])
        layout.addRow("Departman:", self.cmb_departman)
        
        # Telefon
        self.txt_telefon = QLineEdit()
        self.txt_telefon.setText(self.yetkili_data.get('telefon', ''))
        self.txt_telefon.setPlaceholderText("Sabit telefon")
        layout.addRow("Telefon:", self.txt_telefon)
        
        # Cep Telefon
        self.txt_cep = QLineEdit()
        self.txt_cep.setText(self.yetkili_data.get('cep_telefon', ''))
        self.txt_cep.setPlaceholderText("Cep telefonu")
        layout.addRow("Cep Telefon:", self.txt_cep)
        
        # Dahili
        self.txt_dahili = QLineEdit()
        self.txt_dahili.setText(self.yetkili_data.get('dahili', ''))
        self.txt_dahili.setPlaceholderText("Dahili numara")
        layout.addRow("Dahili:", self.txt_dahili)
        
        # E-posta
        self.txt_email = QLineEdit()
        self.txt_email.setText(self.yetkili_data.get('email', ''))
        self.txt_email.setPlaceholderText("E-posta adresi")
        layout.addRow("E-posta:", self.txt_email)
        
        # Varsayılan
        self.chk_varsayilan = QCheckBox("Ana iletişim kişisi")
        self.chk_varsayilan.setChecked(self.yetkili_data.get('varsayilan_mi', False))
        layout.addRow("", self.chk_varsayilan)
        
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
        ad_soyad = self.txt_ad_soyad.text().strip()
        
        if not ad_soyad:
            QMessageBox.warning(self, "Uyarı", "Ad soyad zorunludur!")
            return
        
        self.result_data = {
            'ad_soyad': ad_soyad,
            'unvan': self.txt_unvan.text().strip() or None,
            'departman': self.cmb_departman.currentText().strip() or None,
            'telefon': self.txt_telefon.text().strip() or None,
            'cep_telefon': self.txt_cep.text().strip() or None,
            'dahili': self.txt_dahili.text().strip() or None,
            'email': self.txt_email.text().strip() or None,
            'varsayilan_mi': 1 if self.chk_varsayilan.isChecked() else 0
        }
        self.accept()
    
    def get_data(self):
        return getattr(self, 'result_data', {})


class CariYetkililerPage(BasePage):
    """Cari Yetkililer Yönetimi Sayfası"""
    
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
        title = QLabel("👥 Cari Yetkililer Yönetimi")
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
        
        btn_yeni = QPushButton("+ Yeni Yetkili")
        btn_yeni.setCursor(Qt.PointingHandCursor)
        btn_yeni.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni_yetkili)
        f_layout.addWidget(btn_yeni)
        
        layout.addWidget(filter_frame)
        
        # Yetkili Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(["ID", "Ad Soyad", "Ünvan", "Departman", "Telefon", "Cep", "E-posta", "Ana", "Durum", "İşlem"])
        self.table.setStyleSheet(self._table_style())
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(9, 170)
        self.table.doubleClicked.connect(self._duzenle_yetkili)
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
        self._load_yetkililer()
    
    def _load_yetkililer(self):
        self.table.setRowCount(0)
        if not self.selected_cari_id:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ad_soyad, unvan, departman, telefon, cep_telefon, email, varsayilan_mi, aktif_mi
                FROM musteri.cari_yetkililer
                WHERE cari_id = ? AND (silindi_mi = 0 OR silindi_mi IS NULL)
                ORDER BY varsayilan_mi DESC, ad_soyad
            """, (self.selected_cari_id,))
            
            for row in cursor.fetchall():
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(r, 1, QTableWidgetItem(row[1] or ""))
                self.table.setItem(r, 2, QTableWidgetItem(row[2] or ""))
                self.table.setItem(r, 3, QTableWidgetItem(row[3] or ""))
                self.table.setItem(r, 4, QTableWidgetItem(row[4] or ""))
                self.table.setItem(r, 5, QTableWidgetItem(row[5] or ""))
                self.table.setItem(r, 6, QTableWidgetItem(row[6] or ""))
                
                varsayilan = QTableWidgetItem("★" if row[7] else "")
                varsayilan.setForeground(QColor('#f59e0b'))
                self.table.setItem(r, 7, varsayilan)
                
                durum = QTableWidgetItem("✓" if row[8] else "✗")
                durum.setForeground(QColor('#22c55e') if row[8] else QColor('#ef4444'))
                self.table.setItem(r, 8, durum)

                rid = row[0]
                widget = self.create_action_buttons([
                    ("✏️", "Duzenle", lambda checked, rid=rid: self._duzenle_yetkili_by_id(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=rid: self._sil_yetkili_by_id(rid), "delete"),
                ])
                self.table.setCellWidget(r, 9, widget)
                self.table.setRowHeight(r, 42)

            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Yetkililer yüklenemedi: {e}")
    
    def _yeni_yetkili(self):
        if not self.selected_cari_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir cari seçin!")
            return
        
        dialog = YetkiliDialog(self.theme, self.selected_cari_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                if data['varsayilan_mi']:
                    cursor.execute("UPDATE musteri.cari_yetkililer SET varsayilan_mi = 0 WHERE cari_id = ?", (self.selected_cari_id,))
                
                cursor.execute("""
                    INSERT INTO musteri.cari_yetkililer (uuid, cari_id, ad_soyad, unvan, departman, telefon, cep_telefon, dahili, email, varsayilan_mi, aktif_mi, olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, GETDATE(), GETDATE(), 0)
                """, (str(uuid.uuid4()), self.selected_cari_id, data['ad_soyad'], data['unvan'], data['departman'], data['telefon'], data['cep_telefon'], data['dahili'], data['email'], data['varsayilan_mi']))
                
                conn.commit()
                conn.close()
                self._load_yetkililer()
                QMessageBox.information(self, "Başarılı", "Yetkili eklendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Yetkili eklenemedi: {e}")
    
    def _duzenle_yetkili_by_id(self, yetkili_id):
        """ID ile yetkili düzenleme (satır butonundan)"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ad_soyad, unvan, departman, telefon, cep_telefon, dahili, email, varsayilan_mi
                FROM musteri.cari_yetkililer WHERE id = ?
            """, (yetkili_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return

            mevcut = {
                'ad_soyad': row[0], 'unvan': row[1], 'departman': row[2], 'telefon': row[3],
                'cep_telefon': row[4], 'dahili': row[5], 'email': row[6], 'varsayilan_mi': row[7]
            }

            dialog = YetkiliDialog(self.theme, self.selected_cari_id, mevcut, self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                conn = get_db_connection()
                cursor = conn.cursor()

                if data['varsayilan_mi']:
                    cursor.execute("UPDATE musteri.cari_yetkililer SET varsayilan_mi = 0 WHERE cari_id = ?", (self.selected_cari_id,))

                cursor.execute("""
                    UPDATE musteri.cari_yetkililer SET ad_soyad = ?, unvan = ?, departman = ?, telefon = ?, cep_telefon = ?, dahili = ?, email = ?, varsayilan_mi = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (data['ad_soyad'], data['unvan'], data['departman'], data['telefon'], data['cep_telefon'], data['dahili'], data['email'], data['varsayilan_mi'], yetkili_id))

                conn.commit()
                conn.close()
                self._load_yetkililer()
                QMessageBox.information(self, "Başarılı", "Yetkili güncellendi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {e}")

    def _sil_yetkili_by_id(self, yetkili_id):
        """ID ile yetkili silme (satır butonundan)"""
        reply = QMessageBox.question(self, "Onay", "Bu yetkiliyi silmek istediğinize emin misiniz?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE musteri.cari_yetkililer SET silindi_mi = 1, silinme_tarihi = GETDATE() WHERE id = ?", (yetkili_id,))
                conn.commit()
                conn.close()
                self._load_yetkililer()
                QMessageBox.information(self, "Başarılı", "Yetkili silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    def _duzenle_yetkili(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir yetkili seçin!")
            return

        yetkili_id = int(self.table.item(selected[0].row(), 0).text())

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ad_soyad, unvan, departman, telefon, cep_telefon, dahili, email, varsayilan_mi
                FROM musteri.cari_yetkililer WHERE id = ?
            """, (yetkili_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return
            
            mevcut = {
                'ad_soyad': row[0], 'unvan': row[1], 'departman': row[2], 'telefon': row[3],
                'cep_telefon': row[4], 'dahili': row[5], 'email': row[6], 'varsayilan_mi': row[7]
            }
            
            dialog = YetkiliDialog(self.theme, self.selected_cari_id, mevcut, self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                conn = get_db_connection()
                cursor = conn.cursor()
                
                if data['varsayilan_mi']:
                    cursor.execute("UPDATE musteri.cari_yetkililer SET varsayilan_mi = 0 WHERE cari_id = ?", (self.selected_cari_id,))
                
                cursor.execute("""
                    UPDATE musteri.cari_yetkililer SET ad_soyad = ?, unvan = ?, departman = ?, telefon = ?, cep_telefon = ?, dahili = ?, email = ?, varsayilan_mi = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (data['ad_soyad'], data['unvan'], data['departman'], data['telefon'], data['cep_telefon'], data['dahili'], data['email'], data['varsayilan_mi'], yetkili_id))
                
                conn.commit()
                conn.close()
                self._load_yetkililer()
                QMessageBox.information(self, "Başarılı", "Yetkili güncellendi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {e}")
    
    def _sil_yetkili(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir yetkili seçin!")
            return
        
        yetkili_id = int(self.table.item(selected[0].row(), 0).text())
        
        reply = QMessageBox.question(self, "Onay", "Bu yetkiliyi silmek istediğinize emin misiniz?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE musteri.cari_yetkililer SET silindi_mi = 1, silinme_tarihi = GETDATE() WHERE id = ?", (yetkili_id,))
                conn.commit()
                conn.close()
                self._load_yetkililer()
                QMessageBox.information(self, "Başarılı", "Yetkili silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
