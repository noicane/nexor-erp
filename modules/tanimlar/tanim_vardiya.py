# -*- coding: utf-8 -*-
"""
Vardiya Tanımları Sayfası
tanim.vardiyalar tablosu için CRUD işlemleri
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QTimeEdit,
    QDialog, QFormLayout, QCheckBox, QSpinBox, QFrame, QGroupBox
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QColor
from datetime import datetime

from components.base_page import BasePage
from core.database import get_db_connection


class VardiyaDialog(QDialog):
    """Vardiya ekleme/düzenleme dialogu"""
    
    def __init__(self, theme: dict, parent=None, vardiya_id=None):
        super().__init__(parent)
        self.theme = theme
        self.vardiya_id = vardiya_id
        self.setWindowTitle("Vardiya Ekle" if not vardiya_id else "Vardiya Düzenle")
        self.setMinimumWidth(400)
        self.setModal(True)
        self.setup_ui()
        
        if vardiya_id:
            self.load_data()
    
    def setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QTimeEdit, QSpinBox {{
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
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Form grubu
        form_group = QGroupBox("Vardiya Bilgileri")
        form_layout = QFormLayout()
        
        # Kod
        self.txt_kod = QLineEdit()
        self.txt_kod.setMaxLength(10)
        self.txt_kod.setPlaceholderText("Örn: V1, SABAH")
        form_layout.addRow("Vardiya Kodu*:", self.txt_kod)
        
        # Ad
        self.txt_ad = QLineEdit()
        self.txt_ad.setMaxLength(50)
        self.txt_ad.setPlaceholderText("Örn: Sabah Vardiyası")
        form_layout.addRow("Vardiya Adı*:", self.txt_ad)
        
        # Başlangıç Saati
        self.time_baslangic = QTimeEdit()
        self.time_baslangic.setDisplayFormat("HH:mm")
        self.time_baslangic.setTime(QTime(8, 0))
        form_layout.addRow("Başlangıç Saati*:", self.time_baslangic)
        
        # Bitiş Saati
        self.time_bitis = QTimeEdit()
        self.time_bitis.setDisplayFormat("HH:mm")
        self.time_bitis.setTime(QTime(17, 0))
        form_layout.addRow("Bitiş Saati*:", self.time_bitis)
        
        # Mola Süresi
        self.spin_mola = QSpinBox()
        self.spin_mola.setRange(0, 180)
        self.spin_mola.setValue(60)
        self.spin_mola.setSuffix(" dk")
        form_layout.addRow("Mola Süresi:", self.spin_mola)
        
        # Aktif
        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        self.chk_aktif.setStyleSheet(f"color: {self.theme.get('text')};")
        form_layout.addRow("", self.chk_aktif)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Çalışma saati hesaplama
        self.lbl_calisma = QLabel()
        self.lbl_calisma.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold; padding: 10px;")
        layout.addWidget(self.lbl_calisma)
        
        # Saat değişimlerini izle
        self.time_baslangic.timeChanged.connect(self.hesapla_calisma)
        self.time_bitis.timeChanged.connect(self.hesapla_calisma)
        self.spin_mola.valueChanged.connect(self.hesapla_calisma)
        self.hesapla_calisma()
        
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
    
    def hesapla_calisma(self):
        """Net çalışma saatini hesapla"""
        baslangic = self.time_baslangic.time()
        bitis = self.time_bitis.time()
        
        baslangic_dk = baslangic.hour() * 60 + baslangic.minute()
        bitis_dk = bitis.hour() * 60 + bitis.minute()
        
        # Gece vardiyası kontrolü
        if bitis_dk <= baslangic_dk:
            bitis_dk += 24 * 60
        
        toplam_dk = bitis_dk - baslangic_dk - self.spin_mola.value()
        saat = toplam_dk // 60
        dakika = toplam_dk % 60
        
        self.lbl_calisma.setText(f"Net Çalışma Süresi: {saat} saat {dakika} dakika")
    
    def load_data(self):
        """Mevcut vardiya verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kod, ad, baslangic_saati, bitis_saati, mola_suresi_dk, aktif_mi
                FROM tanim.vardiyalar WHERE id = ?
            """, (self.vardiya_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_kod.setText(row.kod or "")
                self.txt_kod.setEnabled(False)
                self.txt_ad.setText(row.ad or "")
                
                if row.baslangic_saati:
                    self.time_baslangic.setTime(QTime(row.baslangic_saati.hour, row.baslangic_saati.minute))
                if row.bitis_saati:
                    self.time_bitis.setTime(QTime(row.bitis_saati.hour, row.bitis_saati.minute))
                
                self.spin_mola.setValue(row.mola_suresi_dk or 0)
                self.chk_aktif.setChecked(row.aktif_mi if row.aktif_mi is not None else True)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def kaydet(self):
        """Vardiyayı kaydet"""
        kod = self.txt_kod.text().strip().upper()
        ad = self.txt_ad.text().strip()
        
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad alanları zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            baslangic = self.time_baslangic.time().toString("HH:mm:ss")
            bitis = self.time_bitis.time().toString("HH:mm:ss")
            
            if self.vardiya_id:
                cursor.execute("""
                    UPDATE tanim.vardiyalar 
                    SET ad = ?, baslangic_saati = ?, bitis_saati = ?, 
                        mola_suresi_dk = ?, aktif_mi = ?
                    WHERE id = ?
                """, (ad, baslangic, bitis, self.spin_mola.value(), 
                      self.chk_aktif.isChecked(), self.vardiya_id))
            else:
                # Kod kontrolü
                cursor.execute("SELECT COUNT(*) FROM tanim.vardiyalar WHERE kod = ?", (kod,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu kod zaten kullanılıyor!")
                    conn.close()
                    return
                
                cursor.execute("""
                    INSERT INTO tanim.vardiyalar (kod, ad, baslangic_saati, bitis_saati, mola_suresi_dk, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (kod, ad, baslangic, bitis, self.spin_mola.value(), self.chk_aktif.isChecked()))
            
            conn.commit()
            conn.close()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class TanimVardiyaPage(BasePage):
    """Vardiya Tanımları Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Başlık
        header = QLabel("⏰ Vardiya Tanımları")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')}; padding: 10px;")
        layout.addWidget(header)
        
        # Toolbar
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(16, 12, 16, 12)
        
        btn_ekle = QPushButton("➕ Yeni Vardiya")
        btn_ekle.setStyleSheet(f"background-color: {self.theme.get('success')}; color: white; padding: 8px 15px; border-radius: 6px;")
        btn_ekle.clicked.connect(self._yeni_vardiya)
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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Başlangıç", "Bitiş", "Mola (dk)"])
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
        
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
    
    def _load_data(self):
        """Verileri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad, baslangic_saati, bitis_saati, mola_suresi_dk, aktif_mi
                FROM tanim.vardiyalar
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
                self.table.setItem(i, 3, QTableWidgetItem(str(row.baslangic_saati)[:5] if row.baslangic_saati else ""))
                self.table.setItem(i, 4, QTableWidgetItem(str(row.bitis_saati)[:5] if row.bitis_saati else ""))
                self.table.setItem(i, 5, QTableWidgetItem(str(row.mola_suresi_dk or 0)))
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _yeni_vardiya(self):
        """Yeni vardiya ekle"""
        dialog = VardiyaDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        """Seçili vardiyayı düzenle"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir vardiya seçin!")
            return
        
        vardiya_id = int(self.table.item(row, 0).text())
        dialog = VardiyaDialog(self.theme, self, vardiya_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _sil(self):
        """Seçili vardiyayı sil (soft delete)"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir vardiya seçin!")
            return
        
        vardiya_id = int(self.table.item(row, 0).text())
        kod = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Onay", 
            f"'{kod}' vardiyasını silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE tanim.vardiyalar SET aktif_mi = 0 WHERE id = ?", (vardiya_id,))
                conn.commit()
                conn.close()
                self._load_data()
                QMessageBox.information(self, "Başarılı", "Vardiya silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
