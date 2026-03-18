# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Tedarikçi Anlaşmaları ve Fiyatları
satinalma.tedarikci_anlasmalari ve satinalma.tedarikci_fiyatlari
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QSpinBox,
    QDoubleSpinBox, QTabWidget, QSplitter
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class FiyatDialog(QDialog):
    """Anlaşmalı fiyat ekleme/düzenleme"""
    
    def __init__(self, theme: dict, andasma_id: int, tedarikci_id: int, parent=None, fiyat_id=None):
        super().__init__(parent)
        self.theme = theme
        self.andasma_id = andasma_id
        self.tedarikci_id = tedarikci_id
        self.fiyat_id = fiyat_id
        self.setWindowTitle("Fiyat Ekle" if not fiyat_id else "Fiyat Düzenle")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if fiyat_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px; padding: 8px;
                color: {self.theme.get('text')};
            }}
        """)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.cmb_urun = QComboBox()
        self.cmb_urun.setEditable(True)
        self.cmb_urun.currentIndexChanged.connect(self._on_urun_changed)
        form.addRow("Ürün:", self.cmb_urun)
        
        self.txt_urun_adi = QLineEdit()
        self.txt_urun_adi.setPlaceholderText("Ürün/Malzeme adı")
        form.addRow("Ürün Adı*:", self.txt_urun_adi)
        
        fiyat_layout = QHBoxLayout()
        self.spin_fiyat = QDoubleSpinBox()
        self.spin_fiyat.setRange(0.0001, 9999999)
        self.spin_fiyat.setDecimals(4)
        self.spin_fiyat.setPrefix("₺ ")
        fiyat_layout.addWidget(self.spin_fiyat)
        
        self.cmb_birim = QComboBox()
        self.cmb_birim.addItems(["ADET", "KG", "LT", "MT", "M2", "M3", "PAKET", "KUTU", "VARIL"])
        fiyat_layout.addWidget(self.cmb_birim)
        form.addRow("Birim Fiyat*:", fiyat_layout)
        
        self.spin_min_miktar = QDoubleSpinBox()
        self.spin_min_miktar.setRange(0, 9999999)
        self.spin_min_miktar.setDecimals(2)
        self.spin_min_miktar.setValue(1)
        form.addRow("Min. Sipariş Miktar:", self.spin_min_miktar)
        
        self.date_baslangic = QDateEdit()
        self.date_baslangic.setDate(QDate.currentDate())
        self.date_baslangic.setCalendarPopup(True)
        form.addRow("Geçerlilik Başlangıç*:", self.date_baslangic)
        
        self.date_bitis = QDateEdit()
        self.date_bitis.setDate(QDate.currentDate().addYears(1))
        self.date_bitis.setCalendarPopup(True)
        form.addRow("Geçerlilik Bitiş:", self.date_bitis)
        
        layout.addLayout(form)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 20px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 20px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            self.cmb_urun.addItem("-- Manuel Giriş --", None)
            cursor.execute("SELECT id, urun_kodu, urun_adi FROM stok.urunler WHERE aktif_mi = 1 ORDER BY urun_kodu")
            for row in cursor.fetchall():
                self.cmb_urun.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception:
            pass
    
    def _on_urun_changed(self, index):
        if index > 0:
            text = self.cmb_urun.currentText()
            if " - " in text:
                self.txt_urun_adi.setText(text.split(" - ", 1)[1])
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT urun_id, urun_adi, birim_fiyat, birim_id, min_siparis_miktar,
                       gecerlilik_baslangic, gecerlilik_bitis
                FROM satinalma.tedarikci_fiyatlari WHERE id = ?
            """, (self.fiyat_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                if row[0]:
                    idx = self.cmb_urun.findData(row[0])
                    if idx >= 0: self.cmb_urun.setCurrentIndex(idx)
                self.txt_urun_adi.setText(row[1] or "")
                self.spin_fiyat.setValue(float(row[2]) if row[2] else 0)
                self.spin_min_miktar.setValue(float(row[4]) if row[4] else 1)
                if row[5]: self.date_baslangic.setDate(QDate(row[5].year, row[5].month, row[5].day))
                if row[6]: self.date_bitis.setDate(QDate(row[6].year, row[6].month, row[6].day))
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        urun_adi = self.txt_urun_adi.text().strip()
        if not urun_adi:
            QMessageBox.warning(self, "Uyarı", "Ürün adı zorunludur!")
            return
        if self.spin_fiyat.value() <= 0:
            QMessageBox.warning(self, "Uyarı", "Fiyat girilmelidir!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            urun_id = self.cmb_urun.currentData()
            
            if self.fiyat_id:
                cursor.execute("""
                    UPDATE satinalma.tedarikci_fiyatlari SET
                        urun_id = ?, urun_adi = ?, birim_fiyat = ?, min_siparis_miktar = ?,
                        gecerlilik_baslangic = ?, gecerlilik_bitis = ?
                    WHERE id = ?
                """, (
                    urun_id, urun_adi, self.spin_fiyat.value(), self.spin_min_miktar.value(),
                    self.date_baslangic.date().toPython(), self.date_bitis.date().toPython(),
                    self.fiyat_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO satinalma.tedarikci_fiyatlari
                    (andasma_id, tedarikci_id, urun_id, urun_adi, birim_fiyat, min_siparis_miktar,
                     gecerlilik_baslangic, gecerlilik_bitis)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.andasma_id, self.tedarikci_id, urun_id, urun_adi,
                    self.spin_fiyat.value(), self.spin_min_miktar.value(),
                    self.date_baslangic.date().toPython(), self.date_bitis.date().toPython()
                ))
            
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class AndasmaDialog(QDialog):
    """Tedarikçi anlaşması oluşturma/düzenleme"""
    
    def __init__(self, theme: dict, parent=None, andasma_id=None):
        super().__init__(parent)
        self.theme = theme
        self.andasma_id = andasma_id
        self.tedarikci_id = None
        self.setWindowTitle("Tedarikçi Anlaşması" if not andasma_id else "Anlaşma Düzenle")
        self.setMinimumSize(900, 550)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if andasma_id:
            self._load_data()
            self._load_fiyatlar()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QDoubleSpinBox, QSpinBox {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px; padding: 8px;
                color: {self.theme.get('text')};
            }}
            QTabWidget::pane {{ border: 1px solid {self.theme.get('border')}; }}
            QTabBar::tab {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 20px; }}
            QTabBar::tab:selected {{ background: {self.theme.get('primary')}; color: white; }}
        """)
        
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        
        # Tab 1: Genel
        tab_genel = QWidget()
        genel_layout = QFormLayout(tab_genel)
        
        self.txt_andasma_no = QLineEdit()
        self.txt_andasma_no.setReadOnly(True)
        self.txt_andasma_no.setPlaceholderText("Otomatik")
        genel_layout.addRow("Anlaşma No:", self.txt_andasma_no)
        
        self.cmb_tedarikci = QComboBox()
        self.cmb_tedarikci.currentIndexChanged.connect(self._on_tedarikci_changed)
        genel_layout.addRow("Tedarikçi*:", self.cmb_tedarikci)
        
        self.date_baslangic = QDateEdit()
        self.date_baslangic.setDate(QDate.currentDate())
        self.date_baslangic.setCalendarPopup(True)
        genel_layout.addRow("Başlangıç Tarihi*:", self.date_baslangic)
        
        self.date_bitis = QDateEdit()
        self.date_bitis.setDate(QDate.currentDate().addYears(1))
        self.date_bitis.setCalendarPopup(True)
        genel_layout.addRow("Bitiş Tarihi*:", self.date_bitis)
        
        self.spin_toplam = QDoubleSpinBox()
        self.spin_toplam.setRange(0, 999999999)
        self.spin_toplam.setDecimals(2)
        self.spin_toplam.setPrefix("₺ ")
        genel_layout.addRow("Yıllık Anlaşma Tutarı:", self.spin_toplam)
        
        self.spin_vade = QSpinBox()
        self.spin_vade.setRange(0, 365)
        self.spin_vade.setValue(30)
        self.spin_vade.setSuffix(" gün")
        genel_layout.addRow("Ödeme Vadesi:", self.spin_vade)
        
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["AKTIF", "PASIF", "SURESI_DOLDU"])
        genel_layout.addRow("Durum:", self.cmb_durum)
        
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(80)
        genel_layout.addRow("Notlar:", self.txt_notlar)
        
        tabs.addTab(tab_genel, "📋 Genel")
        
        # Tab 2: Fiyatlar
        tab_fiyatlar = QWidget()
        fiyat_layout = QVBoxLayout(tab_fiyatlar)
        
        toolbar = QHBoxLayout()
        btn_ekle = QPushButton("➕ Fiyat Ekle")
        btn_ekle.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_ekle.clicked.connect(self._add_fiyat)
        toolbar.addWidget(btn_ekle)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._edit_fiyat)
        toolbar.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._delete_fiyat)
        toolbar.addWidget(btn_sil)
        toolbar.addStretch()
        
        self.lbl_fiyat_sayisi = QLabel("0 ürün")
        self.lbl_fiyat_sayisi.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        toolbar.addWidget(self.lbl_fiyat_sayisi)
        fiyat_layout.addLayout(toolbar)
        
        self.table_fiyatlar = QTableWidget()
        self.table_fiyatlar.setColumnCount(6)
        self.table_fiyatlar.setHorizontalHeaderLabels(["ID", "Ürün", "Birim Fiyat", "Min. Miktar", "Geç. Başlangıç", "Geç. Bitiş"])
        self.table_fiyatlar.setColumnHidden(0, True)
        self.table_fiyatlar.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_fiyatlar.setStyleSheet(f"QTableWidget {{ background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; }}")
        header = self.table_fiyatlar.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_fiyatlar.setColumnWidth(2, 100)
        self.table_fiyatlar.setColumnWidth(3, 80)
        self.table_fiyatlar.setColumnWidth(4, 100)
        self.table_fiyatlar.setColumnWidth(5, 100)
        self.table_fiyatlar.doubleClicked.connect(self._edit_fiyat)
        fiyat_layout.addWidget(self.table_fiyatlar)
        
        tabs.addTab(tab_fiyatlar, "💰 Anlaşmalı Fiyatlar")
        layout.addWidget(tabs)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 24px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            self.cmb_tedarikci.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, cari_kodu, unvan FROM musteri.cariler WHERE cari_tipi = 'TEDARIKCI' AND aktif_mi = 1 ORDER BY cari_kodu")
            for row in cursor.fetchall():
                self.cmb_tedarikci.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception:
            pass
    
    def _on_tedarikci_changed(self, index):
        self.tedarikci_id = self.cmb_tedarikci.currentData()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT andasma_no, tedarikci_id, baslangic_tarihi, bitis_tarihi,
                       toplam_tutar, odeme_vade_gun, durum, notlar
                FROM satinalma.tedarikci_anlasmalari WHERE id = ?
            """, (self.andasma_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_andasma_no.setText(row[0] or "")
                if row[1]:
                    self.tedarikci_id = row[1]
                    idx = self.cmb_tedarikci.findData(row[1])
                    if idx >= 0: self.cmb_tedarikci.setCurrentIndex(idx)
                if row[2]: self.date_baslangic.setDate(QDate(row[2].year, row[2].month, row[2].day))
                if row[3]: self.date_bitis.setDate(QDate(row[3].year, row[3].month, row[3].day))
                self.spin_toplam.setValue(float(row[4]) if row[4] else 0)
                self.spin_vade.setValue(row[5] or 30)
                if row[6]:
                    idx = self.cmb_durum.findText(row[6])
                    if idx >= 0: self.cmb_durum.setCurrentIndex(idx)
                self.txt_notlar.setPlainText(row[7] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _load_fiyatlar(self):
        if not self.andasma_id: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, urun_adi, birim_fiyat, min_siparis_miktar,
                       FORMAT(gecerlilik_baslangic, 'dd.MM.yyyy'), FORMAT(gecerlilik_bitis, 'dd.MM.yyyy')
                FROM satinalma.tedarikci_fiyatlari WHERE andasma_id = ? AND aktif_mi = 1
                ORDER BY urun_adi
            """, (self.andasma_id,))
            rows = cursor.fetchall()
            conn.close()
            
            self.table_fiyatlar.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table_fiyatlar.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_fiyatlar.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                self.table_fiyatlar.setItem(i, 2, QTableWidgetItem(f"₺ {row[2]:,.4f}" if row[2] else ""))
                self.table_fiyatlar.setItem(i, 3, QTableWidgetItem(f"{row[3]:,.2f}" if row[3] else ""))
                self.table_fiyatlar.setItem(i, 4, QTableWidgetItem(row[4] or ""))
                self.table_fiyatlar.setItem(i, 5, QTableWidgetItem(row[5] or ""))
            
            self.lbl_fiyat_sayisi.setText(f"{len(rows)} ürün")
        except Exception: pass
    
    def _add_fiyat(self):
        if not self.andasma_id:
            QMessageBox.warning(self, "Uyarı", "Önce anlaşmayı kaydedin!")
            return
        if not self.tedarikci_id:
            QMessageBox.warning(self, "Uyarı", "Tedarikçi seçin!")
            return
        dialog = FiyatDialog(self.theme, self.andasma_id, self.tedarikci_id, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_fiyatlar()
    
    def _edit_fiyat(self):
        row = self.table_fiyatlar.currentRow()
        if row < 0: return
        fiyat_id = int(self.table_fiyatlar.item(row, 0).text())
        dialog = FiyatDialog(self.theme, self.andasma_id, self.tedarikci_id, self, fiyat_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_fiyatlar()
    
    def _delete_fiyat(self):
        row = self.table_fiyatlar.currentRow()
        if row < 0: return
        fiyat_id = int(self.table_fiyatlar.item(row, 0).text())
        if QMessageBox.question(self, "Onay", "Bu fiyatı silmek istiyor musunuz?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE satinalma.tedarikci_fiyatlari SET aktif_mi = 0 WHERE id = ?", (fiyat_id,))
                conn.commit()
                conn.close()
                self._load_fiyatlar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        if not self.cmb_tedarikci.currentData():
            QMessageBox.warning(self, "Uyarı", "Tedarikçi seçimi zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.andasma_id:
                cursor.execute("""
                    UPDATE satinalma.tedarikci_anlasmalari SET
                        tedarikci_id = ?, baslangic_tarihi = ?, bitis_tarihi = ?,
                        toplam_tutar = ?, odeme_vade_gun = ?, durum = ?, notlar = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    self.cmb_tedarikci.currentData(),
                    self.date_baslangic.date().toPython(),
                    self.date_bitis.date().toPython(),
                    self.spin_toplam.value() if self.spin_toplam.value() > 0 else None,
                    self.spin_vade.value(),
                    self.cmb_durum.currentText(),
                    self.txt_notlar.toPlainText().strip() or None,
                    self.andasma_id
                ))
            else:
                cursor.execute("SELECT 'ANL-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM satinalma.tedarikci_anlasmalari), 0) + 1 AS VARCHAR), 4)")
                andasma_no = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO satinalma.tedarikci_anlasmalari
                    (andasma_no, tedarikci_id, baslangic_tarihi, bitis_tarihi, toplam_tutar, odeme_vade_gun, durum, notlar)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    andasma_no, self.cmb_tedarikci.currentData(),
                    self.date_baslangic.date().toPython(), self.date_bitis.date().toPython(),
                    self.spin_toplam.value() if self.spin_toplam.value() > 0 else None,
                    self.spin_vade.value(), self.cmb_durum.currentText(),
                    self.txt_notlar.toPlainText().strip() or None
                ))
                self.andasma_id = cursor.fetchone()[0]
                self.txt_andasma_no.setText(andasma_no)
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Anlaşma kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class TedarikciAnlasmalariPage(BasePage):
    """Tedarikçi Anlaşmaları Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("📜 Tedarikçi Anlaşmaları")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Anlaşma")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)

        toolbar_layout.addStretch()
        
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tümü", "AKTIF", "PASIF", "SURESI_DOLDU"])
        self.cmb_durum.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px; color: {self.theme.get('text')};")
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_durum)
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 16px; color: {self.theme.get('text')};")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Anlaşma No", "Tedarikçi", "Başlangıç", "Bitiş", "Tutar", "Fiyat Sayısı", "Durum", "İşlem"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; color: {self.theme.get('text')}; }}
            QTableWidget::item:selected {{ background: {self.theme.get('primary')}; }}
            QHeaderView::section {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px; font-weight: bold; }}
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 100)
        self.table.setColumnWidth(8, 120)
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.id, a.andasma_no, c.unvan,
                       FORMAT(a.baslangic_tarihi, 'dd.MM.yyyy'), FORMAT(a.bitis_tarihi, 'dd.MM.yyyy'),
                       a.toplam_tutar,
                       (SELECT COUNT(*) FROM satinalma.tedarikci_fiyatlari WHERE andasma_id = a.id AND aktif_mi = 1),
                       a.durum
                FROM satinalma.tedarikci_anlasmalari a
                LEFT JOIN musteri.cariler c ON a.tedarikci_id = c.id
                ORDER BY a.bitis_tarihi DESC
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")
    
    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 5 and val:  # Tutar
                    item = QTableWidgetItem(f"₺ {val:,.2f}")
                elif j == 7:  # Durum
                    item = QTableWidgetItem(str(val) if val else "")
                    if val == "AKTIF":
                        item.setForeground(QColor(self.theme.get('success')))
                    elif val == "SURESI_DOLDU":
                        item.setForeground(QColor(self.theme.get('danger')))
                    else:
                        item.setForeground(QColor(self.theme.get('text_muted')))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)

            rid = row[0]
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=rid: self._duzenle_by_id(rid), "edit"),
            ])
            self.table.setCellWidget(i, 8, widget)
            self.table.setRowHeight(i, 42)

        aktif = len([r for r in rows if r[7] == "AKTIF"])
        self.lbl_stat.setText(f"Toplam: {len(rows)} anlaşma | Aktif: {aktif}")

    def _duzenle_by_id(self, andasma_id):
        """ID ile anlaşma düzenleme (satır butonundan)"""
        dialog = AndasmaDialog(self.theme, self, andasma_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _filter(self):
        durum = self.cmb_durum.currentText()
        if durum == "Tümü":
            self._display_data(self.all_rows)
        else:
            self._display_data([r for r in self.all_rows if r[7] == durum])
    
    def _yeni(self):
        dialog = AndasmaDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        andasma_id = int(self.table.item(row, 0).text())
        dialog = AndasmaDialog(self.theme, self, andasma_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
