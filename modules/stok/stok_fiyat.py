# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Ürün Fiyat Yönetimi
stok.urun_fiyatlari tablosu üzerinden fiyat yönetimi
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QDoubleSpinBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
import uuid


class FiyatDialog(QDialog):
    def __init__(self, theme: dict, urun_id: int, fiyat_data: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.urun_id = urun_id
        self.fiyat_data = fiyat_data or {}
        self.is_edit = bool(fiyat_data)
        self.setWindowTitle("Fiyat Düzenle" if self.is_edit else "Yeni Fiyat")
        self.setMinimumWidth(450)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']};
            }}
        """)
        
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["SATIS", "ALIS", "FASON", "LISTE"])
        if self.fiyat_data.get('fiyat_tipi'):
            idx = self.cmb_tip.findText(self.fiyat_data['fiyat_tipi'])
            if idx >= 0: self.cmb_tip.setCurrentIndex(idx)
        layout.addRow("Fiyat Tipi:", self.cmb_tip)
        
        self.spin_fiyat = QDoubleSpinBox()
        self.spin_fiyat.setRange(0, 999999999)
        self.spin_fiyat.setDecimals(4)
        self.spin_fiyat.setValue(self.fiyat_data.get('fiyat') or 0)
        layout.addRow("Fiyat *:", self.spin_fiyat)
        
        self.cmb_para = QComboBox()
        self.cmb_para.addItems(["TRY", "USD", "EUR"])
        if self.fiyat_data.get('para_birimi'): self.cmb_para.setCurrentText(self.fiyat_data['para_birimi'])
        layout.addRow("Para Birimi:", self.cmb_para)
        
        self.cmb_cari = QComboBox()
        self.cmb_cari.addItem("-- Genel Fiyat --", None)
        self._load_cariler()
        layout.addRow("Müşteri (Özel):", self.cmb_cari)
        
        self.date_baslangic = QDateEdit()
        self.date_baslangic.setCalendarPopup(True)
        self.date_baslangic.setDate(QDate.currentDate())
        if self.fiyat_data.get('gecerlilik_baslangic'):
            self.date_baslangic.setDate(QDate.fromString(str(self.fiyat_data['gecerlilik_baslangic'])[:10], "yyyy-MM-dd"))
        layout.addRow("Başlangıç:", self.date_baslangic)
        
        self.date_bitis = QDateEdit()
        self.date_bitis.setCalendarPopup(True)
        self.date_bitis.setDate(QDate.currentDate().addYears(1))
        if self.fiyat_data.get('gecerlilik_bitis'):
            self.date_bitis.setDate(QDate.fromString(str(self.fiyat_data['gecerlilik_bitis'])[:10], "yyyy-MM-dd"))
        layout.addRow("Bitiş:", self.date_bitis)
        
        btn_layout = QHBoxLayout()
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 10px 20px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_iptal)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_kaydet)
        layout.addRow("", btn_layout)
    
    def _load_cariler(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, cari_kodu, unvan FROM musteri.cariler WHERE aktif_mi = 1 ORDER BY unvan")
            for row in cursor.fetchall():
                self.cmb_cari.addItem(f"{row[1]} - {row[2][:30]}", row[0])
            conn.close()
            if self.fiyat_data.get('cari_id'):
                for i in range(self.cmb_cari.count()):
                    if self.cmb_cari.itemData(i) == self.fiyat_data['cari_id']:
                        self.cmb_cari.setCurrentIndex(i)
                        break
        except: pass
    
    def _save(self):
        if self.spin_fiyat.value() <= 0:
            QMessageBox.warning(self, "Uyarı", "Fiyat 0'dan büyük olmalı!")
            return
        self.result_data = {
            'fiyat_tipi': self.cmb_tip.currentText(),
            'fiyat': self.spin_fiyat.value(),
            'para_birimi': self.cmb_para.currentText(),
            'cari_id': self.cmb_cari.currentData(),
            'gecerlilik_baslangic': self.date_baslangic.date().toString("yyyy-MM-dd"),
            'gecerlilik_bitis': self.date_bitis.date().toString("yyyy-MM-dd")
        }
        self.accept()
    
    def get_data(self): return getattr(self, 'result_data', {})


class StokFiyatPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.selected_urun_id = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        header = QHBoxLayout()
        title = QLabel("💰 Ürün Fiyat Yönetimi")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {self.theme['bg_card_solid']}; border-radius: 8px; padding: 12px;")
        f_layout = QHBoxLayout(filter_frame)
        
        f_layout.addWidget(QLabel("Ürün Ara:"))
        self.txt_arama = QLineEdit()
        self.txt_arama.setPlaceholderText("Ürün kodu veya adı...")
        self.txt_arama.setMinimumWidth(300)
        self.txt_arama.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']};")
        self.txt_arama.returnPressed.connect(self._ara_urun)
        f_layout.addWidget(self.txt_arama)
        
        btn_ara = QPushButton("🔍 Ara")
        btn_ara.setStyleSheet(self._button_style())
        btn_ara.clicked.connect(self._ara_urun)
        f_layout.addWidget(btn_ara)
        f_layout.addStretch()
        
        btn_yeni = QPushButton("+ Yeni Fiyat")
        btn_yeni.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 10px 20px;")
        btn_yeni.clicked.connect(self._yeni_fiyat)
        f_layout.addWidget(btn_yeni)
        layout.addWidget(filter_frame)
        
        self.urun_info = QLabel("Ürün seçiniz...")
        self.urun_info.setStyleSheet(f"color: {self.theme['text_muted']}; padding: 8px; background: {self.theme['bg_hover']}; border-radius: 6px;")
        layout.addWidget(self.urun_info)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Tip", "Fiyat", "Para", "Müşteri", "Başlangıç", "Bitiş", "Durum"])
        self.table.setStyleSheet(self._table_style())
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._duzenle_fiyat)
        layout.addWidget(self.table, 1)
        
        btn_layout = QHBoxLayout()
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(self._button_style())
        btn_duzenle.clicked.connect(self._duzenle_fiyat)
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(self._button_style())
        btn_sil.clicked.connect(self._sil_fiyat)
        btn_layout.addWidget(btn_duzenle)
        btn_layout.addWidget(btn_sil)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _table_style(self):
        return f"QTableWidget {{ background: {self.theme['bg_main']}; border: 1px solid {self.theme['border']}; }} QHeaderView::section {{ background: {self.theme['bg_card_solid']}; color: {self.theme['text']}; padding: 10px; border-bottom: 2px solid {self.theme['primary']}; }}"
    
    def _button_style(self):
        return f"QPushButton {{ background: {self.theme['bg_card_solid']}; color: {self.theme['text']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px 16px; }}"
    
    def _ara_urun(self):
        arama = self.txt_arama.text().strip()
        if not arama: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 1 id, urun_kodu, urun_adi FROM stok.urunler WHERE (urun_kodu LIKE ? OR urun_adi LIKE ?) AND aktif_mi = 1", (f"%{arama}%", f"%{arama}%"))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.selected_urun_id = row[0]
                self.urun_info.setText(f"📦 {row[1]} - {row[2]}")
                self._load_fiyatlar()
            else:
                QMessageBox.warning(self, "Uyarı", "Ürün bulunamadı!")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _load_fiyatlar(self):
        self.table.setRowCount(0)
        if not self.selected_urun_id: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.id, f.fiyat_tipi, f.fiyat, f.para_birimi, c.unvan, f.gecerlilik_baslangic, f.gecerlilik_bitis, f.aktif_mi
                FROM stok.urun_fiyatlari f LEFT JOIN musteri.cariler c ON f.cari_id = c.id
                WHERE f.urun_id = ? AND (f.silindi_mi = 0 OR f.silindi_mi IS NULL)
            """, (self.selected_urun_id,))
            for row in cursor.fetchall():
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(r, 1, QTableWidgetItem(row[1] or ""))
                self.table.setItem(r, 2, QTableWidgetItem(f"{row[2]:,.4f}" if row[2] else ""))
                self.table.setItem(r, 3, QTableWidgetItem(row[3] or "TRY"))
                self.table.setItem(r, 4, QTableWidgetItem(row[4] or "Genel"))
                self.table.setItem(r, 5, QTableWidgetItem(str(row[5])[:10] if row[5] else ""))
                self.table.setItem(r, 6, QTableWidgetItem(str(row[6])[:10] if row[6] else ""))
                durum = QTableWidgetItem("✓" if row[7] else "✗")
                durum.setForeground(QColor('#22c55e') if row[7] else QColor('#ef4444'))
                self.table.setItem(r, 7, durum)
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _yeni_fiyat(self):
        if not self.selected_urun_id:
            QMessageBox.warning(self, "Uyarı", "Önce ürün arayın!")
            return
        dialog = FiyatDialog(self.theme, self.selected_urun_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO stok.urun_fiyatlari (uuid, urun_id, cari_id, fiyat_tipi, fiyat, para_birimi, gecerlilik_baslangic, gecerlilik_bitis, aktif_mi, olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, GETDATE(), GETDATE(), 0)
                """, (str(uuid.uuid4()), self.selected_urun_id, data['cari_id'], data['fiyat_tipi'], data['fiyat'], data['para_birimi'], data['gecerlilik_baslangic'], data['gecerlilik_bitis']))
                conn.commit()
                conn.close()
                self._load_fiyatlar()
                QMessageBox.information(self, "Başarılı", "Fiyat eklendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _duzenle_fiyat(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Fiyat seçin!")
            return
        fiyat_id = int(self.table.item(selected[0].row(), 0).text())
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT fiyat_tipi, fiyat, para_birimi, cari_id, gecerlilik_baslangic, gecerlilik_bitis FROM stok.urun_fiyatlari WHERE id = ?", (fiyat_id,))
            row = cursor.fetchone()
            conn.close()
            if not row: return
            mevcut = {'fiyat_tipi': row[0], 'fiyat': row[1], 'para_birimi': row[2], 'cari_id': row[3], 'gecerlilik_baslangic': row[4], 'gecerlilik_bitis': row[5]}
            dialog = FiyatDialog(self.theme, self.selected_urun_id, mevcut, self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE stok.urun_fiyatlari SET fiyat_tipi=?, fiyat=?, para_birimi=?, cari_id=?, gecerlilik_baslangic=?, gecerlilik_bitis=?, guncelleme_tarihi=GETDATE() WHERE id=?",
                    (data['fiyat_tipi'], data['fiyat'], data['para_birimi'], data['cari_id'], data['gecerlilik_baslangic'], data['gecerlilik_bitis'], fiyat_id))
                conn.commit()
                conn.close()
                self._load_fiyatlar()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _sil_fiyat(self):
        selected = self.table.selectedItems()
        if not selected: return
        fiyat_id = int(self.table.item(selected[0].row(), 0).text())
        if QMessageBox.question(self, "Onay", "Silmek istiyor musunuz?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE stok.urun_fiyatlari SET silindi_mi=1 WHERE id=?", (fiyat_id,))
                conn.commit()
                conn.close()
                self._load_fiyatlar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
