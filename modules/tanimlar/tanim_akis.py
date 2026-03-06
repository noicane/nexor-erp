# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Akış Yönetimi
Stok akış şablonlarını tanımlama ve düzenleme ekranı
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QDialog, QFormLayout, QMessageBox, QHeaderView, QSpinBox,
    QGroupBox, QSplitter, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon
from core.database import get_db_connection


class AkisYonetimiPage(QWidget):
    """Akış Şablonları Yönetim Ekranı"""
    
    def __init__(self, theme: dict = None):
        super().__init__()
        self.theme = theme or {}
        self.selected_sablon_id = None
        self._init_ui()
        self._load_sablonlar()
    
    def _init_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Başlık
        header = QLabel("📋 Akış Şablonları Yönetimi")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Splitter - Sol: Şablonlar, Sağ: Adımlar
        splitter = QSplitter(Qt.Horizontal)
        
        # === SOL PANEL: ŞABLONLAR ===
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        
        # Şablon listesi başlık
        sablon_header = QHBoxLayout()
        sablon_header.addWidget(QLabel("Akış Şablonları"))
        sablon_header.addStretch()
        
        btn_yeni_sablon = QPushButton("+ Yeni Şablon")
        btn_yeni_sablon.clicked.connect(self._yeni_sablon)
        sablon_header.addWidget(btn_yeni_sablon)
        left_layout.addLayout(sablon_header)
        
        # Şablon tablosu
        self.tbl_sablonlar = QTableWidget()
        self.tbl_sablonlar.setColumnCount(4)
        self.tbl_sablonlar.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Varsayılan"])
        self.tbl_sablonlar.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_sablonlar.setSelectionMode(QTableWidget.SingleSelection)
        self.tbl_sablonlar.itemSelectionChanged.connect(self._sablon_secildi)
        self.tbl_sablonlar.setColumnHidden(0, True)
        self.tbl_sablonlar.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        left_layout.addWidget(self.tbl_sablonlar)
        
        # Şablon butonları
        sablon_btn_layout = QHBoxLayout()
        btn_duzenle_sablon = QPushButton("✏️ Düzenle")
        btn_duzenle_sablon.clicked.connect(self._duzenle_sablon)
        btn_sil_sablon = QPushButton("🗑️ Sil")
        btn_sil_sablon.clicked.connect(self._sil_sablon)
        sablon_btn_layout.addWidget(btn_duzenle_sablon)
        sablon_btn_layout.addWidget(btn_sil_sablon)
        sablon_btn_layout.addStretch()
        left_layout.addLayout(sablon_btn_layout)
        
        splitter.addWidget(left_panel)
        
        # === SAĞ PANEL: ADIMLAR ===
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        # Adım listesi başlık
        adim_header = QHBoxLayout()
        self.lbl_secili_sablon = QLabel("Adımlar: (Şablon seçin)")
        self.lbl_secili_sablon.setStyleSheet("font-weight: bold;")
        adim_header.addWidget(self.lbl_secili_sablon)
        adim_header.addStretch()
        
        btn_yeni_adim = QPushButton("+ Adım Ekle")
        btn_yeni_adim.clicked.connect(self._yeni_adim)
        adim_header.addWidget(btn_yeni_adim)
        right_layout.addLayout(adim_header)
        
        # Adım tablosu
        self.tbl_adimlar = QTableWidget()
        self.tbl_adimlar.setColumnCount(7)
        self.tbl_adimlar.setHorizontalHeaderLabels([
            "ID", "Sıra", "Adım Tipi", "Hedef Depo", "Zorunlu", "KK Gerekli", "Açıklama"
        ])
        self.tbl_adimlar.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_adimlar.setSelectionMode(QTableWidget.SingleSelection)
        self.tbl_adimlar.setColumnHidden(0, True)
        self.tbl_adimlar.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        right_layout.addWidget(self.tbl_adimlar)
        
        # Adım butonları
        adim_btn_layout = QHBoxLayout()
        btn_yukari = QPushButton("⬆️ Yukarı")
        btn_yukari.clicked.connect(self._adim_yukari)
        btn_asagi = QPushButton("⬇️ Aşağı")
        btn_asagi.clicked.connect(self._adim_asagi)
        btn_duzenle_adim = QPushButton("✏️ Düzenle")
        btn_duzenle_adim.clicked.connect(self._duzenle_adim)
        btn_sil_adim = QPushButton("🗑️ Sil")
        btn_sil_adim.clicked.connect(self._sil_adim)
        
        adim_btn_layout.addWidget(btn_yukari)
        adim_btn_layout.addWidget(btn_asagi)
        adim_btn_layout.addWidget(btn_duzenle_adim)
        adim_btn_layout.addWidget(btn_sil_adim)
        adim_btn_layout.addStretch()
        right_layout.addLayout(adim_btn_layout)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
    
    def _load_sablonlar(self):
        """Şablonları yükle"""
        self.tbl_sablonlar.setRowCount(0)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad, varsayilan_mi 
                FROM tanim.akis_sablon 
                WHERE aktif_mi = 1 
                ORDER BY varsayilan_mi DESC, kod
            """)
            
            for row_data in cursor.fetchall():
                row = self.tbl_sablonlar.rowCount()
                self.tbl_sablonlar.insertRow(row)
                self.tbl_sablonlar.setItem(row, 0, QTableWidgetItem(str(row_data[0])))
                self.tbl_sablonlar.setItem(row, 1, QTableWidgetItem(row_data[1]))
                self.tbl_sablonlar.setItem(row, 2, QTableWidgetItem(row_data[2]))
                self.tbl_sablonlar.setItem(row, 3, QTableWidgetItem("✓" if row_data[3] else ""))
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Şablonlar yüklenemedi: {e}")
    
    def _load_adimlar(self, sablon_id):
        """Seçili şablonun adımlarını yükle"""
        self.tbl_adimlar.setRowCount(0)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    a.id, a.sira, t.ad as adim_tipi, d.ad as depo_ad,
                    a.zorunlu, a.kalite_kontrol_gerekli, a.aciklama
                FROM tanim.akis_adim a
                JOIN tanim.akis_adim_tipleri t ON a.adim_tipi_id = t.id
                LEFT JOIN tanim.depolar d ON a.hedef_depo_id = d.id
                WHERE a.sablon_id = ? AND a.aktif_mi = 1
                ORDER BY a.sira
            """, (sablon_id,))
            
            for row_data in cursor.fetchall():
                row = self.tbl_adimlar.rowCount()
                self.tbl_adimlar.insertRow(row)
                self.tbl_adimlar.setItem(row, 0, QTableWidgetItem(str(row_data[0])))
                self.tbl_adimlar.setItem(row, 1, QTableWidgetItem(str(row_data[1])))
                self.tbl_adimlar.setItem(row, 2, QTableWidgetItem(row_data[2] or ""))
                self.tbl_adimlar.setItem(row, 3, QTableWidgetItem(row_data[3] or ""))
                self.tbl_adimlar.setItem(row, 4, QTableWidgetItem("✓" if row_data[4] else ""))
                self.tbl_adimlar.setItem(row, 5, QTableWidgetItem("✓" if row_data[5] else ""))
                self.tbl_adimlar.setItem(row, 6, QTableWidgetItem(row_data[6] or ""))
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Adımlar yüklenemedi: {e}")
    
    def _sablon_secildi(self):
        """Şablon seçildiğinde"""
        selected = self.tbl_sablonlar.selectedItems()
        if selected:
            row = selected[0].row()
            self.selected_sablon_id = int(self.tbl_sablonlar.item(row, 0).text())
            sablon_ad = self.tbl_sablonlar.item(row, 2).text()
            self.lbl_secili_sablon.setText(f"Adımlar: {sablon_ad}")
            self._load_adimlar(self.selected_sablon_id)
        else:
            self.selected_sablon_id = None
            self.lbl_secili_sablon.setText("Adımlar: (Şablon seçin)")
            self.tbl_adimlar.setRowCount(0)
    
    def _yeni_sablon(self):
        """Yeni şablon ekle"""
        dialog = SablonDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._load_sablonlar()
    
    def _duzenle_sablon(self):
        """Şablon düzenle"""
        if not self.selected_sablon_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şablon seçin")
            return
        dialog = SablonDialog(sablon_id=self.selected_sablon_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._load_sablonlar()
    
    def _sil_sablon(self):
        """Şablon sil"""
        if not self.selected_sablon_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şablon seçin")
            return
        
        reply = QMessageBox.question(
            self, "Onay", 
            "Bu şablonu silmek istediğinize emin misiniz?\nTüm adımları da silinecek.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE tanim.akis_adim SET aktif_mi = 0 WHERE sablon_id = ?", 
                              (self.selected_sablon_id,))
                cursor.execute("UPDATE tanim.akis_sablon SET aktif_mi = 0 WHERE id = ?", 
                              (self.selected_sablon_id,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Başarılı", "Şablon silindi")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
            self._load_sablonlar()
            self.tbl_adimlar.setRowCount(0)
            self.selected_sablon_id = None
    
    def _yeni_adim(self):
        """Yeni adım ekle"""
        if not self.selected_sablon_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir şablon seçin")
            return
        dialog = AdimDialog(sablon_id=self.selected_sablon_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._load_adimlar(self.selected_sablon_id)
    
    def _duzenle_adim(self):
        """Adım düzenle"""
        selected = self.tbl_adimlar.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir adım seçin")
            return
        adim_id = int(self.tbl_adimlar.item(selected[0].row(), 0).text())
        dialog = AdimDialog(sablon_id=self.selected_sablon_id, adim_id=adim_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._load_adimlar(self.selected_sablon_id)
    
    def _sil_adim(self):
        """Adım sil"""
        selected = self.tbl_adimlar.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir adım seçin")
            return
        
        reply = QMessageBox.question(self, "Onay", "Bu adımı silmek istediğinize emin misiniz?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            adim_id = int(self.tbl_adimlar.item(selected[0].row(), 0).text())
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE tanim.akis_adim SET aktif_mi = 0 WHERE id = ?", (adim_id,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Başarılı", "Adım silindi")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
            self._load_adimlar(self.selected_sablon_id)
    
    def _adim_yukari(self):
        """Adımı yukarı taşı"""
        self._adim_tasi(-1)
    
    def _adim_asagi(self):
        """Adımı aşağı taşı"""
        self._adim_tasi(1)
    
    def _adim_tasi(self, direction):
        """Adım sırasını değiştir"""
        selected = self.tbl_adimlar.selectedItems()
        if not selected:
            return
        
        current_row = selected[0].row()
        new_row = current_row + direction
        
        if new_row < 0 or new_row >= self.tbl_adimlar.rowCount():
            return
        
        current_id = int(self.tbl_adimlar.item(current_row, 0).text())
        other_id = int(self.tbl_adimlar.item(new_row, 0).text())
        current_sira = int(self.tbl_adimlar.item(current_row, 1).text())
        other_sira = int(self.tbl_adimlar.item(new_row, 1).text())
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE tanim.akis_adim SET sira = ? WHERE id = ?", (other_sira, current_id))
            cursor.execute("UPDATE tanim.akis_adim SET sira = ? WHERE id = ?", (current_sira, other_id))
            conn.commit()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sıra değiştirme hatası: {e}")
        
        self._load_adimlar(self.selected_sablon_id)
        self.tbl_adimlar.selectRow(new_row)


class SablonDialog(QDialog):
    """Şablon ekleme/düzenleme dialog"""
    
    def __init__(self, sablon_id=None, parent=None):
        super().__init__(parent)
        self.sablon_id = sablon_id
        self.setWindowTitle("Şablon Düzenle" if sablon_id else "Yeni Şablon")
        self.setMinimumWidth(400)
        self._init_ui()
        if sablon_id:
            self._load_data()
    
    def _init_ui(self):
        layout = QFormLayout(self)
        
        self.txt_kod = QLineEdit()
        self.txt_kod.setMaxLength(20)
        layout.addRow("Kod:", self.txt_kod)
        
        self.txt_ad = QLineEdit()
        self.txt_ad.setMaxLength(100)
        layout.addRow("Ad:", self.txt_ad)
        
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(80)
        layout.addRow("Açıklama:", self.txt_aciklama)
        
        self.chk_varsayilan = QCheckBox("Varsayılan şablon")
        layout.addRow("", self.chk_varsayilan)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_kaydet)
        btn_layout.addWidget(btn_iptal)
        layout.addRow("", btn_layout)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT kod, ad, aciklama, varsayilan_mi FROM tanim.akis_sablon WHERE id = ?", 
                          (self.sablon_id,))
            row = cursor.fetchone()
            if row:
                self.txt_kod.setText(row[0])
                self.txt_ad.setText(row[1])
                self.txt_aciklama.setPlainText(row[2] or "")
                self.chk_varsayilan.setChecked(bool(row[3]))
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenemedi: {e}")
    
    def _kaydet(self):
        kod = self.txt_kod.text().strip().upper()
        ad = self.txt_ad.text().strip()
        
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad alanları zorunludur")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Varsayılan seçildiyse diğerlerini kaldır
            if self.chk_varsayilan.isChecked():
                cursor.execute("UPDATE tanim.akis_sablon SET varsayilan_mi = 0")
            
            if self.sablon_id:
                cursor.execute("""
                    UPDATE tanim.akis_sablon 
                    SET kod = ?, ad = ?, aciklama = ?, varsayilan_mi = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (kod, ad, self.txt_aciklama.toPlainText(), self.chk_varsayilan.isChecked(), self.sablon_id))
            else:
                cursor.execute("""
                    INSERT INTO tanim.akis_sablon (kod, ad, aciklama, varsayilan_mi, aktif_mi)
                    VALUES (?, ?, ?, ?, 1)
                """, (kod, ad, self.txt_aciklama.toPlainText(), self.chk_varsayilan.isChecked()))
            
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")


class AdimDialog(QDialog):
    """Adım ekleme/düzenleme dialog"""
    
    def __init__(self, sablon_id, adim_id=None, parent=None):
        super().__init__(parent)
        self.sablon_id = sablon_id
        self.adim_id = adim_id
        self.setWindowTitle("Adım Düzenle" if adim_id else "Yeni Adım")
        self.setMinimumWidth(450)
        self._init_ui()
        self._load_combos()
        if adim_id:
            self._load_data()
    
    def _init_ui(self):
        layout = QFormLayout(self)
        
        self.spin_sira = QSpinBox()
        self.spin_sira.setRange(1, 99)
        layout.addRow("Sıra:", self.spin_sira)
        
        self.cmb_adim_tipi = QComboBox()
        layout.addRow("Adım Tipi:", self.cmb_adim_tipi)
        
        self.cmb_depo_tipi = QComboBox()
        layout.addRow("Hedef Depo:", self.cmb_depo_tipi)
        
        self.chk_zorunlu = QCheckBox("Zorunlu adım")
        self.chk_zorunlu.setChecked(True)
        layout.addRow("", self.chk_zorunlu)
        
        self.chk_kk = QCheckBox("Kalite kontrol gerekli")
        layout.addRow("", self.chk_kk)
        
        self.chk_atlanabilir = QCheckBox("Atlanabilir")
        layout.addRow("", self.chk_atlanabilir)
        
        self.txt_aciklama = QLineEdit()
        layout.addRow("Açıklama:", self.txt_aciklama)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_kaydet)
        btn_layout.addWidget(btn_iptal)
        layout.addRow("", btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Adım tipleri
            cursor.execute("SELECT id, kod, ad FROM tanim.akis_adim_tipleri ORDER BY sira")
            self.adim_tipleri = []
            for row in cursor.fetchall():
                self.adim_tipleri.append((row[0], row[1]))
                self.cmb_adim_tipi.addItem(f"{row[1]} - {row[2]}", row[0])
            
            # Depolar (depo tipleri değil, gerçek depolar)
            cursor.execute("""
                SELECT id, kod, ad 
                FROM tanim.depolar 
                WHERE aktif_mi = 1 
                ORDER BY kod
            """)
            self.cmb_depo_tipi.addItem("-- Seçiniz --", None)
            for row in cursor.fetchall():
                self.cmb_depo_tipi.addItem(f"{row[1]} - {row[2]}", row[0])
            
            # Sonraki sıra numarası - sadece aktif adımlara bak
            if not self.adim_id:
                cursor.execute("SELECT ISNULL(MAX(sira), 0) + 1 FROM tanim.akis_adim WHERE sablon_id = ? AND aktif_mi = 1", 
                              (self.sablon_id,))
                self.spin_sira.setValue(cursor.fetchone()[0])
            
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenemedi: {e}")
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sira, adim_tipi_id, hedef_depo_id, zorunlu, 
                       kalite_kontrol_gerekli, atlanabilir, aciklama
                FROM tanim.akis_adim WHERE id = ?
            """, (self.adim_id,))
            row = cursor.fetchone()
            if row:
                self.spin_sira.setValue(row[0])
                
                # Adım tipi seç
                idx = self.cmb_adim_tipi.findData(row[1])
                if idx >= 0:
                    self.cmb_adim_tipi.setCurrentIndex(idx)
                
                # Hedef depo seç
                idx = self.cmb_depo_tipi.findData(row[2])
                if idx >= 0:
                    self.cmb_depo_tipi.setCurrentIndex(idx)
                
                self.chk_zorunlu.setChecked(bool(row[3]))
                self.chk_kk.setChecked(bool(row[4]))
                self.chk_atlanabilir.setChecked(bool(row[5]))
                self.txt_aciklama.setText(row[6] or "")
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenemedi: {e}")
    
    def _kaydet(self):
        adim_tipi_id = self.cmb_adim_tipi.currentData()
        depo_tipi_id = self.cmb_depo_tipi.currentData()
        
        if not adim_tipi_id:
            QMessageBox.warning(self, "Uyarı", "Adım tipi seçiniz")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.adim_id:
                cursor.execute("""
                    UPDATE tanim.akis_adim 
                    SET sira = ?, adim_tipi_id = ?, hedef_depo_id = ?,
                        zorunlu = ?, kalite_kontrol_gerekli = ?, atlanabilir = ?, aciklama = ?
                    WHERE id = ?
                """, (
                    self.spin_sira.value(), adim_tipi_id, depo_tipi_id,
                    self.chk_zorunlu.isChecked(), self.chk_kk.isChecked(),
                    self.chk_atlanabilir.isChecked(), self.txt_aciklama.text(),
                    self.adim_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO tanim.akis_adim 
                    (sablon_id, sira, adim_tipi_id, hedef_depo_id, zorunlu, 
                     kalite_kontrol_gerekli, atlanabilir, aciklama, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    self.sablon_id, self.spin_sira.value(), adim_tipi_id, depo_tipi_id,
                    self.chk_zorunlu.isChecked(), self.chk_kk.isChecked(),
                    self.chk_atlanabilir.isChecked(), self.txt_aciklama.text()
                ))
            
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")
