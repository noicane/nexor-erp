# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Ürün Maliyet Yönetimi
[MODERNIZED UI - v3.0]

Ürün maliyet bileşenlerini tanımlama ve hesaplama

Not: Bu modül maliyet kalemlerini (hammadde, işçilik, enerji, kimyasal, amortisman vb.)
yönetir ve ürün bazında toplam maliyet hesaplar.
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QDoubleSpinBox, QTextEdit, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
import uuid


def get_modern_style(theme: dict) -> dict:
    """Modern tema renkleri - TÜM MODÜLLERDE AYNI"""
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


class MaliyetKalemiDialog(QDialog):
    def __init__(self, theme: dict, urun_id: int, kalem_data: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.urun_id = urun_id
        self.kalem_data = kalem_data or {}
        self.is_edit = bool(kalem_data)
        self.setWindowTitle("Maliyet Kalemi Düzenle" if self.is_edit else "Yeni Maliyet Kalemi")
        self.setMinimumWidth(450)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']};
            }}
        """)
        
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Maliyet Tipi
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["HAMMADDE", "ISCILIK", "ENERJI", "KIMYASAL", "AMORTISMAN", "NAKLIYE", "GENEL_GIDER", "DIGER"])
        if self.kalem_data.get('maliyet_tipi'):
            idx = self.cmb_tip.findText(self.kalem_data['maliyet_tipi'])
            if idx >= 0: self.cmb_tip.setCurrentIndex(idx)
        layout.addRow("Maliyet Tipi:", self.cmb_tip)
        
        # Kalem Adı
        self.txt_ad = QLineEdit()
        self.txt_ad.setText(self.kalem_data.get('kalem_adi', ''))
        self.txt_ad.setPlaceholderText("Örn: Çinko, Elektrik, İşçilik")
        layout.addRow("Kalem Adı *:", self.txt_ad)
        
        # Birim Maliyet
        self.spin_birim = QDoubleSpinBox()
        self.spin_birim.setRange(0, 999999999)
        self.spin_birim.setDecimals(4)
        self.spin_birim.setValue(self.kalem_data.get('birim_maliyet') or 0)
        layout.addRow("Birim Maliyet:", self.spin_birim)
        
        # Miktar
        self.spin_miktar = QDoubleSpinBox()
        self.spin_miktar.setRange(0, 999999999)
        self.spin_miktar.setDecimals(4)
        self.spin_miktar.setValue(self.kalem_data.get('miktar') or 1)
        layout.addRow("Miktar:", self.spin_miktar)
        
        # Birim
        self.cmb_birim = QComboBox()
        self.cmb_birim.setEditable(True)
        self.cmb_birim.addItems(["", "adet", "kg", "lt", "m²", "kWh", "saat", "dk"])
        if self.kalem_data.get('birim'): self.cmb_birim.setCurrentText(self.kalem_data['birim'])
        layout.addRow("Birim:", self.cmb_birim)
        
        # Para Birimi
        self.cmb_para = QComboBox()
        self.cmb_para.addItems(["TRY", "USD", "EUR"])
        if self.kalem_data.get('para_birimi'): self.cmb_para.setCurrentText(self.kalem_data['para_birimi'])
        layout.addRow("Para Birimi:", self.cmb_para)
        
        # Açıklama
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setPlainText(self.kalem_data.get('aciklama', ''))
        self.txt_aciklama.setMaximumHeight(60)
        layout.addRow("Açıklama:", self.txt_aciklama)
        
        # Butonlar
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
    
    def _save(self):
        kalem_adi = self.txt_ad.text().strip()
        if not kalem_adi:
            QMessageBox.warning(self, "Uyarı", "Kalem adı zorunludur!")
            return
        
        self.result_data = {
            'maliyet_tipi': self.cmb_tip.currentText(),
            'kalem_adi': kalem_adi,
            'birim_maliyet': self.spin_birim.value(),
            'miktar': self.spin_miktar.value(),
            'birim': self.cmb_birim.currentText() or None,
            'para_birimi': self.cmb_para.currentText(),
            'aciklama': self.txt_aciklama.toPlainText().strip() or None,
            'toplam': self.spin_birim.value() * self.spin_miktar.value()
        }
        self.accept()
    
    def get_data(self): return getattr(self, 'result_data', {})


class StokMaliyetPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.selected_urun_id = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        header = QHBoxLayout()
        title = QLabel("📊 Ürün Maliyet Yönetimi")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Ürün Seçimi
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
        
        btn_yeni = QPushButton("+ Maliyet Kalemi")
        btn_yeni.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 10px 20px;")
        btn_yeni.clicked.connect(self._yeni_kalem)
        f_layout.addWidget(btn_yeni)
        layout.addWidget(filter_frame)
        
        # Ürün Bilgisi ve Özet
        info_layout = QHBoxLayout()
        
        self.urun_info = QLabel("Ürün seçiniz...")
        self.urun_info.setStyleSheet(f"color: {self.theme['text_muted']}; padding: 8px; background: {self.theme['bg_hover']}; border-radius: 6px;")
        info_layout.addWidget(self.urun_info, 2)
        
        self.toplam_label = QLabel("Toplam Maliyet: ₺0.00")
        self.toplam_label.setStyleSheet(f"color: {self.theme['success']}; padding: 8px; background: {self.theme['bg_card_solid']}; border-radius: 6px; font-weight: bold; font-size: 14px;")
        info_layout.addWidget(self.toplam_label, 1)
        
        layout.addLayout(info_layout)
        
        # Maliyet Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Tip", "Kalem", "Birim Maliyet", "Miktar", "Birim", "Toplam", "Durum"])
        self.table.setStyleSheet(self._table_style())
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._duzenle_kalem)
        layout.addWidget(self.table, 1)
        
        # Alt Butonlar
        btn_layout = QHBoxLayout()
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(self._button_style())
        btn_duzenle.clicked.connect(self._duzenle_kalem)
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(self._button_style())
        btn_sil.clicked.connect(self._sil_kalem)
        btn_hesapla = QPushButton("🔄 Yeniden Hesapla")
        btn_hesapla.setStyleSheet(self._button_style())
        btn_hesapla.clicked.connect(self._hesapla_toplam)
        btn_layout.addWidget(btn_duzenle)
        btn_layout.addWidget(btn_sil)
        btn_layout.addWidget(btn_hesapla)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _table_style(self):
        return f"QTableWidget {{ background: {self.theme['bg_main']}; border: 1px solid {self.theme['border']}; }} QTableWidget::item {{ padding: 8px; color: {self.theme['text']}; }} QHeaderView::section {{ background: {self.theme['bg_card_solid']}; color: {self.theme['text']}; padding: 10px; border-bottom: 2px solid {self.theme['primary']}; }}"
    
    def _button_style(self):
        return f"QPushButton {{ background: {self.theme['bg_card_solid']}; color: {self.theme['text']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px 16px; }}"
    
    def _ara_urun(self):
        arama = self.txt_arama.text().strip()
        if not arama: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 1 id, urun_kodu, urun_adi, yuzey_alani_m2 FROM stok.urunler WHERE (urun_kodu LIKE ? OR urun_adi LIKE ?) AND aktif_mi = 1", (f"%{arama}%", f"%{arama}%"))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.selected_urun_id = row[0]
                m2_info = f" | m²: {row[3]}" if row[3] else ""
                self.urun_info.setText(f"📦 {row[1]} - {row[2]}{m2_info}")
                self._load_kalemler()
            else:
                QMessageBox.warning(self, "Uyarı", "Ürün bulunamadı!")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _load_kalemler(self):
        self.table.setRowCount(0)
        toplam = 0
        if not self.selected_urun_id: return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # urun_maliyetler tablosu yoksa stok.urun_maliyetler oluşturulmalı
            # Şimdilik basit bir yapı kullanıyoruz
            cursor.execute("""
                SELECT id, maliyet_tipi, kalem_adi, birim_maliyet, miktar, birim, toplam_maliyet, aktif_mi
                FROM stok.urun_maliyetler
                WHERE urun_id = ? AND (silindi_mi = 0 OR silindi_mi IS NULL)
                ORDER BY maliyet_tipi, kalem_adi
            """, (self.selected_urun_id,))
            
            for row in cursor.fetchall():
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(r, 1, QTableWidgetItem(row[1] or ""))
                self.table.setItem(r, 2, QTableWidgetItem(row[2] or ""))
                self.table.setItem(r, 3, QTableWidgetItem(f"{row[3]:,.4f}" if row[3] else ""))
                self.table.setItem(r, 4, QTableWidgetItem(f"{row[4]:,.2f}" if row[4] else ""))
                self.table.setItem(r, 5, QTableWidgetItem(row[5] or ""))
                self.table.setItem(r, 6, QTableWidgetItem(f"{row[6]:,.4f}" if row[6] else ""))
                
                durum = QTableWidgetItem("✓" if row[7] else "✗")
                durum.setForeground(QColor('#22c55e') if row[7] else QColor('#ef4444'))
                self.table.setItem(r, 7, durum)
                
                if row[6]: toplam += float(row[6])
            
            conn.close()
            self.toplam_label.setText(f"Toplam Maliyet: ₺{toplam:,.2f}")
        except Exception as e:
            # Tablo yoksa oluştur
            if "Invalid object name" in str(e):
                self._create_maliyet_table()
            else:
                QMessageBox.warning(self, "Hata", str(e))
    
    def _create_maliyet_table(self):
        """Maliyet tablosu yoksa oluştur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'urun_maliyetler' AND schema_id = SCHEMA_ID('stok'))
                BEGIN
                    CREATE TABLE stok.urun_maliyetler (
                        id BIGINT IDENTITY(1,1) PRIMARY KEY,
                        uuid UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
                        urun_id BIGINT NOT NULL,
                        maliyet_tipi NVARCHAR(60) NOT NULL,
                        kalem_adi NVARCHAR(200) NOT NULL,
                        birim_maliyet DECIMAL(18,4),
                        miktar DECIMAL(18,4) DEFAULT 1,
                        birim NVARCHAR(40),
                        para_birimi NVARCHAR(10) DEFAULT 'TRY',
                        toplam_maliyet DECIMAL(18,4),
                        aciklama NVARCHAR(500),
                        aktif_mi BIT DEFAULT 1,
                        olusturma_tarihi DATETIME2 DEFAULT GETDATE(),
                        guncelleme_tarihi DATETIME2 DEFAULT GETDATE(),
                        silindi_mi BIT DEFAULT 0
                    )
                END
            """)
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Bilgi", "Maliyet tablosu oluşturuldu!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Tablo oluşturulamadı: {e}")
    
    def _yeni_kalem(self):
        if not self.selected_urun_id:
            QMessageBox.warning(self, "Uyarı", "Önce ürün arayın!")
            return
        dialog = MaliyetKalemiDialog(self.theme, self.selected_urun_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO stok.urun_maliyetler (uuid, urun_id, maliyet_tipi, kalem_adi, birim_maliyet, miktar, birim, para_birimi, toplam_maliyet, aciklama, aktif_mi, olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, GETDATE(), GETDATE(), 0)
                """, (str(uuid.uuid4()), self.selected_urun_id, data['maliyet_tipi'], data['kalem_adi'], data['birim_maliyet'], data['miktar'], data['birim'], data['para_birimi'], data['toplam'], data['aciklama']))
                conn.commit()
                conn.close()
                self._load_kalemler()
                QMessageBox.information(self, "Başarılı", "Maliyet kalemi eklendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _duzenle_kalem(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Kalem seçin!")
            return
        kalem_id = int(self.table.item(selected[0].row(), 0).text())
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT maliyet_tipi, kalem_adi, birim_maliyet, miktar, birim, para_birimi, aciklama FROM stok.urun_maliyetler WHERE id = ?", (kalem_id,))
            row = cursor.fetchone()
            conn.close()
            if not row: return
            mevcut = {'maliyet_tipi': row[0], 'kalem_adi': row[1], 'birim_maliyet': row[2], 'miktar': row[3], 'birim': row[4], 'para_birimi': row[5], 'aciklama': row[6]}
            dialog = MaliyetKalemiDialog(self.theme, self.selected_urun_id, mevcut, self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE stok.urun_maliyetler SET maliyet_tipi=?, kalem_adi=?, birim_maliyet=?, miktar=?, birim=?, para_birimi=?, toplam_maliyet=?, aciklama=?, guncelleme_tarihi=GETDATE() WHERE id=?",
                    (data['maliyet_tipi'], data['kalem_adi'], data['birim_maliyet'], data['miktar'], data['birim'], data['para_birimi'], data['toplam'], data['aciklama'], kalem_id))
                conn.commit()
                conn.close()
                self._load_kalemler()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _sil_kalem(self):
        selected = self.table.selectedItems()
        if not selected: return
        kalem_id = int(self.table.item(selected[0].row(), 0).text())
        if QMessageBox.question(self, "Onay", "Silmek istiyor musunuz?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE stok.urun_maliyetler SET silindi_mi=1 WHERE id=?", (kalem_id,))
                conn.commit()
                conn.close()
                self._load_kalemler()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _hesapla_toplam(self):
        """Tüm kalemlerin toplamını yeniden hesapla"""
        self._load_kalemler()
        QMessageBox.information(self, "Bilgi", "Toplam maliyet yeniden hesaplandı!")
