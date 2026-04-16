# -*- coding: utf-8 -*-
"""
Zimmet Türleri Tanımları Sayfası
ik.zimmet_turleri tablosu için CRUD işlemleri
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QSpinBox, QFrame, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


# Kategori ve birim seçenekleri
KATEGORILER = [
    ("KKD", "Kişisel Koruyucu Donanım"),
    ("IS_EKIPMANI", "İş Ekipmanı"),
    ("ELEKTRONIK", "Elektronik"),
    ("MOBILYA", "Mobilya"),
    ("DIGER", "Diğer")
]

BIRIMLER = ["ADET", "CIFT", "TAKIM", "KUTU"]


class ZimmetTuruDialog(QDialog):
    """Zimmet türü ekleme/düzenleme dialogu"""
    
    def __init__(self, theme: dict, parent=None, zimmet_turu_id=None):
        super().__init__(parent)
        self.theme = theme
        self.zimmet_turu_id = zimmet_turu_id
        self.setWindowTitle("Zimmet Türü Ekle" if not zimmet_turu_id else "Zimmet Türü Düzenle")
        self.setMinimumWidth(450)
        self.setModal(True)
        self.setup_ui()
        
        if zimmet_turu_id:
            self.load_data()
    
    def setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QSpinBox, QTextEdit, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 8px;
                color: {brand.TEXT};
            }}
            QGroupBox {{
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Form grubu
        form_group = QGroupBox("Zimmet Türü Bilgileri")
        form_layout = QFormLayout()
        
        # Kod
        self.txt_kod = QLineEdit()
        self.txt_kod.setMaxLength(20)
        self.txt_kod.setPlaceholderText("Örn: BARET, ELDIVEN")
        form_layout.addRow("Zimmet Kodu*:", self.txt_kod)
        
        # Ad
        self.txt_ad = QLineEdit()
        self.txt_ad.setMaxLength(100)
        self.txt_ad.setPlaceholderText("Örn: Koruyucu Baret")
        form_layout.addRow("Zimmet Adı*:", self.txt_ad)
        
        # Kategori
        self.cmb_kategori = QComboBox()
        for kod, ad in KATEGORILER:
            self.cmb_kategori.addItem(ad, kod)
        form_layout.addRow("Kategori:", self.cmb_kategori)
        
        # Birim
        self.cmb_birim = QComboBox()
        self.cmb_birim.addItems(BIRIMLER)
        form_layout.addRow("Birim:", self.cmb_birim)
        
        # Yenileme periyodu
        self.spin_periyot = QSpinBox()
        self.spin_periyot.setRange(0, 3650)
        self.spin_periyot.setValue(0)
        self.spin_periyot.setSpecialValueText("Belirsiz")
        self.spin_periyot.setSuffix(" gün")
        form_layout.addRow("Yenileme Periyodu:", self.spin_periyot)
        
        # Stok takibi
        self.chk_stok_takibi = QCheckBox("Stok Takibi Yap")
        self.chk_stok_takibi.setStyleSheet(f"color: {brand.TEXT};")
        self.chk_stok_takibi.stateChanged.connect(self.stok_takibi_changed)
        form_layout.addRow("", self.chk_stok_takibi)
        
        # Mevcut stok
        self.spin_mevcut_stok = QSpinBox()
        self.spin_mevcut_stok.setRange(0, 999999)
        self.spin_mevcut_stok.setEnabled(False)
        form_layout.addRow("Mevcut Stok:", self.spin_mevcut_stok)
        
        # Minimum stok
        self.spin_min_stok = QSpinBox()
        self.spin_min_stok.setRange(0, 999999)
        self.spin_min_stok.setEnabled(False)
        form_layout.addRow("Minimum Stok:", self.spin_min_stok)
        
        # Açıklama
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(80)
        self.txt_aciklama.setPlaceholderText("Zimmet türü açıklaması...")
        form_layout.addRow("Açıklama:", self.txt_aciklama)
        
        # Aktif
        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        self.chk_aktif.setStyleSheet(f"color: {brand.TEXT};")
        form_layout.addRow("", self.chk_aktif)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setStyleSheet(f"background-color: {brand.SUCCESS}; color: white; padding: 8px 20px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self.kaydet)
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 8px 20px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_kaydet)
        btn_layout.addWidget(btn_iptal)
        layout.addLayout(btn_layout)
    
    def stok_takibi_changed(self, state):
        """Stok takibi checkbox değiştiğinde"""
        enabled = state == Qt.Checked
        self.spin_mevcut_stok.setEnabled(enabled)
        self.spin_min_stok.setEnabled(enabled)
    
    def load_data(self):
        """Mevcut zimmet türü verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kod, ad, kategori, birim, periyot_gun, stok_takibi, 
                       mevcut_stok, min_stok, aciklama, aktif_mi
                FROM ik.zimmet_turleri WHERE id = ?
            """, (self.zimmet_turu_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_kod.setText(row.kod or "")
                self.txt_kod.setEnabled(False)
                self.txt_ad.setText(row.ad or "")
                
                # Kategori
                idx = self.cmb_kategori.findData(row.kategori)
                if idx >= 0:
                    self.cmb_kategori.setCurrentIndex(idx)
                
                # Birim
                idx = self.cmb_birim.findText(row.birim)
                if idx >= 0:
                    self.cmb_birim.setCurrentIndex(idx)
                
                self.spin_periyot.setValue(row.periyot_gun or 0)
                self.chk_stok_takibi.setChecked(row.stok_takibi if row.stok_takibi is not None else False)
                self.spin_mevcut_stok.setValue(row.mevcut_stok or 0)
                self.spin_min_stok.setValue(row.min_stok or 0)
                self.txt_aciklama.setPlainText(row.aciklama or "")
                self.chk_aktif.setChecked(row.aktif_mi)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def kaydet(self):
        """Zimmet türünü kaydet"""
        kod = self.txt_kod.text().strip().upper()
        ad = self.txt_ad.text().strip()
        
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad alanları zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            kategori = self.cmb_kategori.currentData()
            birim = self.cmb_birim.currentText()
            periyot = self.spin_periyot.value() if self.spin_periyot.value() > 0 else None
            stok_takibi = self.chk_stok_takibi.isChecked()
            mevcut_stok = self.spin_mevcut_stok.value() if stok_takibi else None
            min_stok = self.spin_min_stok.value() if stok_takibi else None
            aciklama = self.txt_aciklama.toPlainText().strip() or None
            
            if self.zimmet_turu_id:
                cursor.execute("""
                    UPDATE ik.zimmet_turleri 
                    SET ad = ?, kategori = ?, birim = ?, periyot_gun = ?,
                        stok_takibi = ?, mevcut_stok = ?, min_stok = ?, aciklama = ?, aktif_mi = ?
                    WHERE id = ?
                """, (ad, kategori, birim, periyot, stok_takibi, mevcut_stok, min_stok,
                      aciklama, self.chk_aktif.isChecked(), self.zimmet_turu_id))
            else:
                # Kod kontrolü
                cursor.execute("SELECT COUNT(*) FROM ik.zimmet_turleri WHERE kod = ?", (kod,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu kod zaten kullanılıyor!")
                    conn.close()
                    return
                
                cursor.execute("""
                    INSERT INTO ik.zimmet_turleri (kod, ad, kategori, birim, periyot_gun, 
                                                   stok_takibi, mevcut_stok, min_stok, aciklama, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (kod, ad, kategori, birim, periyot, stok_takibi, mevcut_stok, min_stok,
                      aciklama, self.chk_aktif.isChecked()))
            
            conn.commit()
            conn.close()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class TanimZimmetTurleriPage(BasePage):
    """Zimmet Türleri Tanımları Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Başlık
        header = QLabel("📦 Zimmet Türleri Tanımları")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {brand.TEXT}; padding: 10px;")
        layout.addWidget(header)
        
        # Toolbar
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(f"background: {brand.BG_CARD}; border-radius: 8px;")
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(16, 12, 16, 12)
        
        btn_ekle = QPushButton("➕ Yeni Zimmet Türü")
        btn_ekle.setStyleSheet(f"background-color: {brand.SUCCESS}; color: white; padding: 8px 15px; border-radius: 6px;")
        btn_ekle.clicked.connect(self._yeni_zimmet_turu)
        toolbar.addWidget(btn_ekle)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 8px 15px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background-color: {brand.ERROR}; color: white; padding: 8px 15px; border-radius: 6px;")
        btn_sil.clicked.connect(self._sil)
        toolbar.addWidget(btn_sil)
        
        toolbar.addStretch()
        
        # Kategori filtresi
        toolbar.addWidget(QLabel("Kategori:"))
        self.cmb_filtre = QComboBox()
        self.cmb_filtre.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 6px; border-radius: 4px;")
        self.cmb_filtre.addItem("Tümü", None)
        for kod, ad in KATEGORILER:
            self.cmb_filtre.addItem(ad, kod)
        self.cmb_filtre.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.cmb_filtre)
        
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 8px 15px; border-radius: 6px;")
        btn_yenile.clicked.connect(self._load_data)
        toolbar.addWidget(btn_yenile)
        
        layout.addWidget(toolbar_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Kategori", "Birim", "Periyot", "Stok", "Min Stok"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 8px;
                gridline-color: {brand.BORDER};
                color: {brand.TEXT};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {brand.BORDER};
            }}
            QTableWidget::item:selected {{
                background: {brand.PRIMARY};
            }}
            QHeaderView::section {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-weight: bold;
            }}
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
    
    def _load_data(self):
        """Verileri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            where = ["aktif_mi = 1"]
            params = []
            
            kategori = self.cmb_filtre.currentData()
            if kategori:
                where.append("kategori = ?")
                params.append(kategori)
            
            cursor.execute(f"""
                SELECT id, kod, ad, kategori, birim, periyot_gun, mevcut_stok, min_stok, stok_takibi
                FROM ik.zimmet_turleri
                WHERE {' AND '.join(where)}
                ORDER BY kategori, kod
            """, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row.id)))
                self.table.setItem(i, 1, QTableWidgetItem(row.kod or ""))
                self.table.setItem(i, 2, QTableWidgetItem(row.ad or ""))
                
                # Kategori adı
                kategori_ad = row.kategori or ""
                for kod, ad in KATEGORILER:
                    if kod == row.kategori:
                        kategori_ad = ad
                        break
                self.table.setItem(i, 3, QTableWidgetItem(kategori_ad))
                
                self.table.setItem(i, 4, QTableWidgetItem(row.birim or ""))
                self.table.setItem(i, 5, QTableWidgetItem(f"{row.periyot_gun} gün" if row.periyot_gun else "-"))
                
                # Stok durumu
                if row.stok_takibi:
                    stok_item = QTableWidgetItem(str(row.mevcut_stok or 0))
                    min_stok = row.min_stok or 0
                    if (row.mevcut_stok or 0) <= min_stok:
                        stok_item.setForeground(QColor("#e74c3c"))
                    self.table.setItem(i, 6, stok_item)
                    self.table.setItem(i, 7, QTableWidgetItem(str(min_stok)))
                else:
                    self.table.setItem(i, 6, QTableWidgetItem("-"))
                    self.table.setItem(i, 7, QTableWidgetItem("-"))
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _yeni_zimmet_turu(self):
        """Yeni zimmet türü ekle"""
        dialog = ZimmetTuruDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        """Seçili zimmet türünü düzenle"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir zimmet türü seçin!")
            return
        
        zimmet_turu_id = int(self.table.item(row, 0).text())
        dialog = ZimmetTuruDialog(self.theme, self, zimmet_turu_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _sil(self):
        """Seçili zimmet türünü sil (soft delete)"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir zimmet türü seçin!")
            return
        
        zimmet_turu_id = int(self.table.item(row, 0).text())
        kod = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Onay", 
            f"'{kod}' zimmet türünü silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE ik.zimmet_turleri SET aktif_mi = 0 WHERE id = ?", (zimmet_turu_id,))
                conn.commit()
                conn.close()
                self._load_data()
                QMessageBox.information(self, "Başarılı", "Zimmet türü silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
