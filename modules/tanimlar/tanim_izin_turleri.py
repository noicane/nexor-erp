# -*- coding: utf-8 -*-
"""
İzin Türleri Tanımları Sayfası
ik.izin_turleri tablosu için CRUD işlemleri
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QColorDialog,
    QDialog, QFormLayout, QCheckBox, QSpinBox, QFrame, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class IzinTuruDialog(QDialog):
    """İzin türü ekleme/düzenleme dialogu"""
    
    def __init__(self, theme: dict, parent=None, izin_turu_id=None):
        super().__init__(parent)
        self.theme = theme
        self.izin_turu_id = izin_turu_id
        self.renk_kodu = "#3b82f6"
        self.setWindowTitle("İzin Türü Ekle" if not izin_turu_id else "İzin Türü Düzenle")
        self.setMinimumWidth(450)
        self.setModal(True)
        self.setup_ui()
        
        if izin_turu_id:
            self.load_data()
    
    def setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QSpinBox, QTextEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
            QGroupBox {{
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Form grubu
        form_group = QGroupBox("İzin Türü Bilgileri")
        form_layout = QFormLayout()
        
        # Kod
        self.txt_kod = QLineEdit()
        self.txt_kod.setMaxLength(20)
        self.txt_kod.setPlaceholderText("Örn: YILLIK, MAZERET")
        form_layout.addRow("İzin Kodu*:", self.txt_kod)
        
        # Ad
        self.txt_ad = QLineEdit()
        self.txt_ad.setMaxLength(100)
        self.txt_ad.setPlaceholderText("Örn: Yıllık İzin")
        form_layout.addRow("İzin Adı*:", self.txt_ad)
        
        # Ücretli mi
        self.chk_ucretli = QCheckBox("Ücretli İzin")
        self.chk_ucretli.setChecked(True)
        self.chk_ucretli.setStyleSheet(f"color: {self.theme.get('text')};")
        form_layout.addRow("", self.chk_ucretli)
        
        # Max gün
        self.spin_max_gun = QSpinBox()
        self.spin_max_gun.setRange(0, 365)
        self.spin_max_gun.setValue(0)
        self.spin_max_gun.setSpecialValueText("Sınırsız")
        self.spin_max_gun.setSuffix(" gün")
        form_layout.addRow("Maksimum Gün:", self.spin_max_gun)
        
        # Yıllık hak gün
        self.spin_yillik_hak = QSpinBox()
        self.spin_yillik_hak.setRange(0, 365)
        self.spin_yillik_hak.setValue(0)
        self.spin_yillik_hak.setSuffix(" gün")
        form_layout.addRow("Yıllık Hak:", self.spin_yillik_hak)
        
        # Renk seçimi
        renk_layout = QHBoxLayout()
        self.btn_renk = QPushButton()
        self.btn_renk.setFixedSize(80, 30)
        self.btn_renk.setStyleSheet(f"background-color: {self.renk_kodu}; border: 1px solid #ccc; border-radius: 4px;")
        self.btn_renk.clicked.connect(self.renk_sec)
        renk_layout.addWidget(self.btn_renk)
        
        self.lbl_renk = QLabel(self.renk_kodu)
        self.lbl_renk.setStyleSheet(f"color: {self.theme.get('text')};")
        renk_layout.addWidget(self.lbl_renk)
        renk_layout.addStretch()
        form_layout.addRow("Renk:", renk_layout)
        
        # Açıklama
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(80)
        self.txt_aciklama.setPlaceholderText("İzin türü açıklaması...")
        form_layout.addRow("Açıklama:", self.txt_aciklama)
        
        # Aktif
        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        self.chk_aktif.setStyleSheet(f"color: {self.theme.get('text')};")
        form_layout.addRow("", self.chk_aktif)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setStyleSheet(f"background-color: {self.theme.get('success')}; color: white; padding: 8px 20px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self.kaydet)
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 20px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_kaydet)
        btn_layout.addWidget(btn_iptal)
        layout.addLayout(btn_layout)
    
    def renk_sec(self):
        """Renk seçim dialogu"""
        color = QColorDialog.getColor(QColor(self.renk_kodu), self, "Renk Seçin")
        if color.isValid():
            self.renk_kodu = color.name()
            self.btn_renk.setStyleSheet(f"background-color: {self.renk_kodu}; border: 1px solid #ccc; border-radius: 4px;")
            self.lbl_renk.setText(self.renk_kodu)
    
    def load_data(self):
        """Mevcut izin türü verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kod, ad, ucretli_mi, max_gun, yillik_hak_gun, renk_kodu, aciklama, aktif_mi
                FROM ik.izin_turleri WHERE id = ?
            """, (self.izin_turu_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_kod.setText(row.kod or "")
                self.txt_kod.setEnabled(False)
                self.txt_ad.setText(row.ad or "")
                self.chk_ucretli.setChecked(row.ucretli_mi if row.ucretli_mi is not None else True)
                self.spin_max_gun.setValue(row.max_gun or 0)
                self.spin_yillik_hak.setValue(row.yillik_hak_gun or 0)
                
                if row.renk_kodu:
                    self.renk_kodu = row.renk_kodu
                    self.btn_renk.setStyleSheet(f"background-color: {self.renk_kodu}; border: 1px solid #ccc; border-radius: 4px;")
                    self.lbl_renk.setText(self.renk_kodu)
                
                self.txt_aciklama.setPlainText(row.aciklama or "")
                self.chk_aktif.setChecked(row.aktif_mi)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def kaydet(self):
        """İzin türünü kaydet"""
        kod = self.txt_kod.text().strip().upper()
        ad = self.txt_ad.text().strip()
        
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad alanları zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            max_gun = self.spin_max_gun.value() if self.spin_max_gun.value() > 0 else None
            yillik_hak = self.spin_yillik_hak.value() if self.spin_yillik_hak.value() > 0 else None
            aciklama = self.txt_aciklama.toPlainText().strip() or None
            
            if self.izin_turu_id:
                cursor.execute("""
                    UPDATE ik.izin_turleri 
                    SET ad = ?, ucretli_mi = ?, max_gun = ?, yillik_hak_gun = ?,
                        renk_kodu = ?, aciklama = ?, aktif_mi = ?
                    WHERE id = ?
                """, (ad, self.chk_ucretli.isChecked(), max_gun, yillik_hak,
                      self.renk_kodu, aciklama, self.chk_aktif.isChecked(), self.izin_turu_id))
            else:
                # Kod kontrolü
                cursor.execute("SELECT COUNT(*) FROM ik.izin_turleri WHERE kod = ?", (kod,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu kod zaten kullanılıyor!")
                    conn.close()
                    return
                
                cursor.execute("""
                    INSERT INTO ik.izin_turleri (kod, ad, ucretli_mi, max_gun, yillik_hak_gun, renk_kodu, aciklama, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (kod, ad, self.chk_ucretli.isChecked(), max_gun, yillik_hak,
                      self.renk_kodu, aciklama, self.chk_aktif.isChecked()))
            
            conn.commit()
            conn.close()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class TanimIzinTurleriPage(BasePage):
    """İzin Türleri Tanımları Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Başlık
        header = QLabel("🏖️ İzin Türleri Tanımları")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')}; padding: 10px;")
        layout.addWidget(header)
        
        # Toolbar
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(16, 12, 16, 12)
        
        btn_ekle = QPushButton("➕ Yeni İzin Türü")
        btn_ekle.setStyleSheet(f"background-color: {self.theme.get('success')}; color: white; padding: 8px 15px; border-radius: 6px;")
        btn_ekle.clicked.connect(self._yeni_izin_turu)
        toolbar.addWidget(btn_ekle)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 15px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background-color: {self.theme.get('danger')}; color: white; padding: 8px 15px; border-radius: 6px;")
        btn_sil.clicked.connect(self._sil)
        toolbar.addWidget(btn_sil)
        
        toolbar.addStretch()
        
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 15px; border-radius: 6px;")
        btn_yenile.clicked.connect(self._load_data)
        toolbar.addWidget(btn_yenile)
        
        layout.addWidget(toolbar_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Ücretli", "Max Gün", "Yıllık Hak", "Renk"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {self.theme.get('border')};
            }}
            QTableWidget::item:selected {{
                background: {self.theme.get('primary')};
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary')};
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
        
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
    
    def _load_data(self):
        """Verileri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad, ucretli_mi, max_gun, yillik_hak_gun, renk_kodu, aktif_mi
                FROM ik.izin_turleri
                WHERE aktif_mi = 1
                ORDER BY kod
            """)
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row.id)))
                self.table.setItem(i, 1, QTableWidgetItem(row.kod or ""))
                self.table.setItem(i, 2, QTableWidgetItem(row.ad or ""))
                self.table.setItem(i, 3, QTableWidgetItem("✔" if row.ucretli_mi else "✗"))
                self.table.setItem(i, 4, QTableWidgetItem(str(row.max_gun) if row.max_gun else "-"))
                self.table.setItem(i, 5, QTableWidgetItem(str(row.yillik_hak_gun) if row.yillik_hak_gun else "-"))
                
                # Renk hücresi
                renk_item = QTableWidgetItem("  ")
                if row.renk_kodu:
                    renk_item.setBackground(QColor(row.renk_kodu))
                self.table.setItem(i, 6, renk_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _yeni_izin_turu(self):
        """Yeni izin türü ekle"""
        dialog = IzinTuruDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        """Seçili izin türünü düzenle"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir izin türü seçin!")
            return
        
        izin_turu_id = int(self.table.item(row, 0).text())
        dialog = IzinTuruDialog(self.theme, self, izin_turu_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _sil(self):
        """Seçili izin türünü sil (soft delete)"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir izin türü seçin!")
            return
        
        izin_turu_id = int(self.table.item(row, 0).text())
        kod = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Onay", 
            f"'{kod}' izin türünü silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE ik.izin_turleri SET aktif_mi = 0 WHERE id = ?", (izin_turu_id,))
                conn.commit()
                conn.close()
                self._load_data()
                QMessageBox.information(self, "Başarılı", "İzin türü silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
