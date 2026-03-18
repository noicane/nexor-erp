# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Satınalma Talepleri (Onay Sistemi Entegrasyonlu)
satinalma.talepler ve satinalma.talep_satirlari
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QSpinBox,
    QDoubleSpinBox, QTabWidget, QGroupBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtGui import QPainter, QFont, QTextDocument

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from datetime import datetime


class TalepSatirDialog(QDialog):
    """Talep satırı ekleme/düzenleme"""
    
    def __init__(self, theme: dict, talep_id: int, parent=None, satir_id=None):
        super().__init__(parent)
        self.theme = theme
        self.talep_id = talep_id
        self.satir_id = satir_id
        self.setWindowTitle("Kalem Ekle" if not satir_id else "Kalem Düzenle")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        
        if satir_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
        """)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Ürün seçimi veya manuel giriş
        self.cmb_urun = QComboBox()
        self.cmb_urun.setEditable(True)
        self.cmb_urun.currentIndexChanged.connect(self._on_urun_changed)
        form.addRow("Ürün:", self.cmb_urun)
        
        self.txt_urun_adi = QLineEdit()
        self.txt_urun_adi.setPlaceholderText("Ürün/Malzeme adı")
        form.addRow("Ürün Adı*:", self.txt_urun_adi)
        
        # Miktar
        miktar_layout = QHBoxLayout()
        self.spin_miktar = QDoubleSpinBox()
        self.spin_miktar.setRange(0.01, 9999999)
        self.spin_miktar.setDecimals(2)
        self.spin_miktar.setValue(1)
        miktar_layout.addWidget(self.spin_miktar)
        
        self.cmb_birim = QComboBox()
        self.cmb_birim.addItems(["ADET", "KG", "LT", "MT", "M2", "M3", "PAKET", "KUTU", "VARIL"])
        miktar_layout.addWidget(self.cmb_birim)
        form.addRow("Miktar*:", miktar_layout)
        
        # Tahmini fiyat
        self.spin_fiyat = QDoubleSpinBox()
        self.spin_fiyat.setRange(0, 9999999)
        self.spin_fiyat.setDecimals(4)
        self.spin_fiyat.setPrefix("₺ ")
        form.addRow("Tahmini Birim Fiyat:", self.spin_fiyat)
        
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(60)
        form.addRow("Açıklama:", self.txt_aciklama)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Butonlar
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
                SELECT urun_id, urun_adi, talep_miktar, birim, tahmini_birim_fiyat, aciklama
                FROM satinalma.talep_satirlari WHERE id = ?
            """, (self.satir_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                if row[0]:
                    idx = self.cmb_urun.findData(row[0])
                    if idx >= 0:
                        self.cmb_urun.setCurrentIndex(idx)
                self.txt_urun_adi.setText(row[1] or "")
                self.spin_miktar.setValue(float(row[2]) if row[2] else 1)
                idx = self.cmb_birim.findText(row[3] or "ADET")
                if idx >= 0:
                    self.cmb_birim.setCurrentIndex(idx)
                self.spin_fiyat.setValue(float(row[4]) if row[4] else 0)
                self.txt_aciklama.setPlainText(row[5] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        urun_adi = self.txt_urun_adi.text().strip()
        if not urun_adi:
            QMessageBox.warning(self, "Uyarı", "Ürün adı zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            urun_id = self.cmb_urun.currentData()
            miktar = self.spin_miktar.value()
            fiyat = self.spin_fiyat.value()
            tutar = miktar * fiyat if fiyat else None
            
            if self.satir_id:
                cursor.execute("""
                    UPDATE satinalma.talep_satirlari SET
                        urun_id = ?, urun_adi = ?, talep_miktar = ?, birim = ?,
                        tahmini_birim_fiyat = ?, tahmini_tutar = ?, aciklama = ?
                    WHERE id = ?
                """, (urun_id, urun_adi, miktar, self.cmb_birim.currentText(),
                      fiyat if fiyat else None, tutar, 
                      self.txt_aciklama.toPlainText().strip() or None, self.satir_id))
            else:
                # Satır no bul
                cursor.execute("SELECT ISNULL(MAX(satir_no), 0) + 1 FROM satinalma.talep_satirlari WHERE talep_id = ?", (self.talep_id,))
                satir_no = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO satinalma.talep_satirlari
                    (talep_id, satir_no, urun_id, urun_adi, talep_miktar, birim, tahmini_birim_fiyat, tahmini_tutar, aciklama)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.talep_id, satir_no, urun_id, urun_adi, miktar, self.cmb_birim.currentText(),
                      fiyat if fiyat else None, tutar, self.txt_aciklama.toPlainText().strip() or None))
            
            conn.commit()
            LogManager.log_insert('satinalma', 'satinalma.talep_satirlari', None, 'Talep kaydi olustu')
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class TalepDialog(QDialog):
    """Satınalma talebi oluşturma/düzenleme"""
    
    def __init__(self, theme: dict, parent=None, talep_id=None, kullanici_id=None):
        super().__init__(parent)
        self.theme = theme
        self.talep_id = talep_id
        self.kullanici_id = kullanici_id
        self.setWindowTitle("Satınalma Talebi" if not talep_id else "Talep Düzenle")
        self.setMinimumSize(900, 600)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        
        if talep_id:
            self._load_data()
            self._load_satirlar()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
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
        
        self.txt_talep_no = QLineEdit()
        self.txt_talep_no.setReadOnly(True)
        self.txt_talep_no.setPlaceholderText("Otomatik oluşturulacak")
        genel_layout.addRow("Talep No:", self.txt_talep_no)
        
        # Talep Eden (Personel seçimi)
        self.cmb_talep_eden = QComboBox()
        self.cmb_talep_eden.setEditable(True)
        genel_layout.addRow("Talep Eden*:", self.cmb_talep_eden)
        
        self.date_tarih = QDateEdit()
        self.date_tarih.setDate(QDate.currentDate())
        self.date_tarih.setCalendarPopup(True)
        genel_layout.addRow("Tarih:", self.date_tarih)
        
        self.cmb_departman = QComboBox()
        genel_layout.addRow("Departman*:", self.cmb_departman)
        
        self.cmb_oncelik = QComboBox()
        self.cmb_oncelik.addItems(["DUSUK", "NORMAL", "YUKSEK", "ACIL"])
        self.cmb_oncelik.setCurrentText("NORMAL")
        genel_layout.addRow("Öncelik:", self.cmb_oncelik)
        
        self.date_termin = QDateEdit()
        self.date_termin.setDate(QDate.currentDate().addDays(14))
        self.date_termin.setCalendarPopup(True)
        genel_layout.addRow("İstenen Termin:", self.date_termin)
        
        self.txt_neden = QTextEdit()
        self.txt_neden.setMaximumHeight(60)
        self.txt_neden.setPlaceholderText("Talep nedeni/açıklaması")
        genel_layout.addRow("Talep Nedeni:", self.txt_neden)
        
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(60)
        genel_layout.addRow("Notlar:", self.txt_notlar)
        
        # Durum bilgisi
        durum_group = QGroupBox("Onay Durumu")
        durum_layout = QFormLayout()
        
        self.lbl_durum = QLabel("-")
        durum_layout.addRow("Talep Durumu:", self.lbl_durum)
        
        self.lbl_amir_onay = QLabel("-")
        durum_layout.addRow("Amir Onayı:", self.lbl_amir_onay)
        
        self.lbl_satinalma_onay = QLabel("-")
        durum_layout.addRow("Satın Alma Onayı:", self.lbl_satinalma_onay)
        
        durum_group.setLayout(durum_layout)
        genel_layout.addRow(durum_group)
        
        tabs.addTab(tab_genel, "📋 Genel Bilgiler")
        
        # Tab 2: Kalemler
        tab_kalemler = QWidget()
        kalem_layout = QVBoxLayout(tab_kalemler)
        
        toolbar = QHBoxLayout()
        btn_ekle = QPushButton("➕ Kalem Ekle")
        btn_ekle.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_ekle.clicked.connect(self._add_satir)
        toolbar.addWidget(btn_ekle)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._edit_satir)
        toolbar.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._delete_satir)
        toolbar.addWidget(btn_sil)
        
        toolbar.addStretch()
        self.lbl_toplam = QLabel("Tahmini Toplam: ₺ 0.00")
        self.lbl_toplam.setStyleSheet(f"font-weight: bold; color: {self.theme.get('text')};")
        toolbar.addWidget(self.lbl_toplam)
        kalem_layout.addLayout(toolbar)
        
        self.table_satirlar = QTableWidget()
        self.table_satirlar.setColumnCount(7)
        self.table_satirlar.setHorizontalHeaderLabels(["ID", "Sıra", "Ürün Adı", "Miktar", "Birim", "Birim Fiyat", "Tutar"])
        self.table_satirlar.setColumnHidden(0, True)
        self.table_satirlar.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_satirlar.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; color: {self.theme.get('text')}; }}
            QHeaderView::section {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px; }}
        """)
        header = self.table_satirlar.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_satirlar.setColumnWidth(1, 60)
        self.table_satirlar.setColumnWidth(3, 80)
        self.table_satirlar.setColumnWidth(4, 60)
        self.table_satirlar.setColumnWidth(5, 100)
        self.table_satirlar.setColumnWidth(6, 100)
        kalem_layout.addWidget(self.table_satirlar)
        
        tabs.addTab(tab_kalemler, "📦 Talep Kalemleri")
        
        layout.addWidget(tabs)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_yazdir = QPushButton("🖨️ Yazdır")
        btn_yazdir.setStyleSheet(f"background: {self.theme.get('info')}; color: white; padding: 10px 24px; border-radius: 6px;")
        btn_yazdir.clicked.connect(self._print_talep)
        btn_layout.addWidget(btn_yazdir)
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 24px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        self.btn_onaya = QPushButton("📤 Onaya Gönder")
        self.btn_onaya.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; padding: 10px 24px; border-radius: 6px;")
        self.btn_onaya.clicked.connect(self._send_approval)
        self.btn_onaya.setVisible(False)  # İlk başta gizli
        btn_layout.addWidget(self.btn_onaya)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Departmanları yükle
            self.cmb_departman.addItem("-- Departman Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_departman.addItem(f"{row[1]} - {row[2]}", row[0])
            
            # PERSONEL LİSTESİ - Direkt personeller tablosundan çek
            self.cmb_talep_eden.addItem("-- Talep Eden Seçiniz --", None)
            cursor.execute("""
                SELECT p.id, p.ad, p.soyad, p.sicil_no, d.ad as departman
                FROM ik.personeller p
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                WHERE p.aktif_mi = 1
                ORDER BY p.ad, p.soyad
            """)
            for row in cursor.fetchall():
                personel_id = row[0]
                ad = row[1] or ""
                soyad = row[2] or ""
                sicil = row[3] or ""
                departman = row[4] or ""
                
                # Label oluştur
                label = f"{ad} {soyad}"
                if sicil:
                    label += f" ({sicil})"
                if departman:
                    label += f" - {departman}"
                
                self.cmb_talep_eden.addItem(label, personel_id)
            
            # Mevcut kullanıcının personel_id'sini bul ve seç
            if self.kullanici_id:
                cursor.execute("""
                    SELECT personel_id 
                    FROM sistem.kullanicilar 
                    WHERE id = ? AND personel_id IS NOT NULL
                """, (self.kullanici_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    personel_id = row[0]
                    # Combo'da bu personel_id'yi bul
                    for i in range(self.cmb_talep_eden.count()):
                        if self.cmb_talep_eden.itemData(i) == personel_id:
                            self.cmb_talep_eden.setCurrentIndex(i)
                            break
            
            conn.close()
        except Exception as e:
            print(f"Combo yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Hata", f"Personel listesi yüklenemedi:\n{str(e)}")
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT talep_no, tarih, talep_eden_id, departman_id, oncelik, istenen_termin, talep_nedeni, notlar, 
                       durum, amir_onay_durumu, satinalma_onay_durumu
                FROM satinalma.talepler WHERE id = ?
            """, (self.talep_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_talep_no.setText(row[0] or "")
                if row[1]:
                    self.date_tarih.setDate(QDate(row[1].year, row[1].month, row[1].day))
                # Talep eden seç
                if row[2]:
                    idx = self.cmb_talep_eden.findData(row[2])
                    if idx >= 0:
                        self.cmb_talep_eden.setCurrentIndex(idx)
                # Departman seç
                if row[3]:
                    idx = self.cmb_departman.findData(row[3])
                    if idx >= 0:
                        self.cmb_departman.setCurrentIndex(idx)
                if row[4]:
                    idx = self.cmb_oncelik.findText(row[4])
                    if idx >= 0:
                        self.cmb_oncelik.setCurrentIndex(idx)
                if row[5]:
                    self.date_termin.setDate(QDate(row[5].year, row[5].month, row[5].day))
                self.txt_neden.setPlainText(row[6] or "")
                self.txt_notlar.setPlainText(row[7] or "")
                
                # Durum bilgilerini güncelle
                durum = row[8] or "TASLAK"
                self.lbl_durum.setText(durum)
                self.lbl_durum.setStyleSheet(f"color: {self._get_durum_color(durum)}; font-weight: bold;")
                
                amir_onay = row[9] or "-"
                self.lbl_amir_onay.setText(amir_onay)
                self.lbl_amir_onay.setStyleSheet(f"color: {self._get_onay_color(amir_onay)}; font-weight: bold;")
                
                satinalma_onay = row[10] or "-"
                self.lbl_satinalma_onay.setText(satinalma_onay)
                self.lbl_satinalma_onay.setStyleSheet(f"color: {self._get_onay_color(satinalma_onay)}; font-weight: bold;")
                
                # Onaya gönder butonunu göster/gizle
                if durum == "TASLAK":
                    self.btn_onaya.setVisible(True)
                else:
                    self.btn_onaya.setVisible(False)
                    
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _get_durum_color(self, durum):
        colors = {
            'TASLAK': self.theme.get('text_muted'),
            'ONAY_BEKLIYOR': self.theme.get('warning'),
            'AMIR_ONAYLADI': self.theme.get('info'),
            'SATINALMA_ONAYLANDI': self.theme.get('success'),
            'REDDEDILDI': self.theme.get('danger'),
        }
        return colors.get(durum, self.theme.get('text'))
    
    def _get_onay_color(self, onay):
        if onay == "ONAYLANDI":
            return self.theme.get('success')
        elif onay == "REDDEDILDI":
            return self.theme.get('danger')
        return self.theme.get('text_muted')
    
    def _load_satirlar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, satir_no, urun_adi, talep_miktar, birim, tahmini_birim_fiyat, tahmini_tutar
                FROM satinalma.talep_satirlari WHERE talep_id = ? ORDER BY satir_no
            """, (self.talep_id,))
            rows = cursor.fetchall()
            conn.close()
            
            self.table_satirlar.setRowCount(len(rows))
            toplam = 0
            
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    if j == 5 and val:  # Birim fiyat
                        item = QTableWidgetItem(f"₺ {val:,.4f}")
                    elif j == 6 and val:  # Tutar
                        item = QTableWidgetItem(f"₺ {val:,.2f}")
                        toplam += val
                    else:
                        item = QTableWidgetItem(str(val) if val else "")
                    self.table_satirlar.setItem(i, j, item)
            
            self.lbl_toplam.setText(f"Tahmini Toplam: ₺ {toplam:,.2f}")
        except Exception as e:
            print(f"Satır yükleme hatası: {e}")
    
    def _add_satir(self):
        if not self.talep_id:
            QMessageBox.warning(self, "Uyarı", "Önce talebi kaydedin!")
            return
        
        dialog = TalepSatirDialog(self.theme, self.talep_id, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
            self._update_talep_tutar()
    
    def _edit_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir satır seçin!")
            return
        
        satir_id = int(self.table_satirlar.item(row, 0).text())
        dialog = TalepSatirDialog(self.theme, self.talep_id, self, satir_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
            self._update_talep_tutar()
    
    def _delete_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir satır seçin!")
            return
        
        satir_id = int(self.table_satirlar.item(row, 0).text())
        reply = QMessageBox.question(self, "Onay", "Bu satırı silmek istediğinize emin misiniz?", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM satinalma.talep_satirlari WHERE id = ?", (satir_id,))
                conn.commit()
                LogManager.log_delete('satinalma', 'satinalma.talep_satirlari', None, 'Kayit silindi')
                conn.close()
                self._load_satirlar()
                self._update_talep_tutar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _update_talep_tutar(self):
        """Talep toplam tutarını güncelle"""
        if not self.talep_id:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE satinalma.talepler 
                SET tahmini_tutar = (
                    SELECT SUM(ISNULL(tahmini_tutar, 0)) 
                    FROM satinalma.talep_satirlari 
                    WHERE talep_id = ?
                ),
                guncelleme_tarihi = GETDATE()
                WHERE id = ?
            """, (self.talep_id, self.talep_id))
            conn.commit()
            LogManager.log_update('satinalma', 'satinalma.talepler', None, 'Kayit guncellendi')
            conn.close()
        except Exception as e:
            print(f"Tutar güncelleme hatası: {e}")
    
    def _save(self):
        # Talep eden kontrolü
        talep_eden_id = self.cmb_talep_eden.currentData()
        if not talep_eden_id:
            QMessageBox.warning(self, "Uyarı", "Talep eden seçiniz!")
            return
        
        # Departman kontrolü
        departman_id = self.cmb_departman.currentData()
        if not departman_id:
            QMessageBox.warning(self, "Uyarı", "Departman seçiniz!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            tarih = self.date_tarih.date().toPython()
            termin = self.date_termin.date().toPython()
            
            if self.talep_id:
                # Güncelleme
                cursor.execute("""
                    UPDATE satinalma.talepler SET
                        tarih = ?, talep_eden_id = ?, departman_id = ?, oncelik = ?, istenen_termin = ?,
                        talep_nedeni = ?, notlar = ?, guncelleme_tarihi = GETDATE(),
                        guncelleyen_id = ?
                    WHERE id = ?
                """, (tarih, talep_eden_id, departman_id, self.cmb_oncelik.currentText(), termin,
                      self.txt_neden.toPlainText().strip() or None,
                      self.txt_notlar.toPlainText().strip() or None,
                      self.kullanici_id, self.talep_id))
            else:
                # Yeni talep
                # Talep numarası oluştur
                tarih_str = datetime.now().strftime('%Y%m%d')
                cursor.execute("""
                    SELECT ISNULL(MAX(CAST(RIGHT(talep_no, 4) AS INT)), 0) + 1
                    FROM satinalma.talepler
                    WHERE talep_no LIKE ?
                """, (f"TLP-{tarih_str}-%",))
                sira = cursor.fetchone()[0]
                talep_no = f"TLP-{tarih_str}-{sira:04d}"
                
                cursor.execute("""
                    INSERT INTO satinalma.talepler 
                    (talep_no, tarih, talep_eden_id, departman_id, oncelik, istenen_termin,
                     talep_nedeni, notlar, durum, olusturan_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'TASLAK', ?)
                """, (talep_no, tarih, talep_eden_id, departman_id, 
                      self.cmb_oncelik.currentText(), termin,
                      self.txt_neden.toPlainText().strip() or None,
                      self.txt_notlar.toPlainText().strip() or None,
                      self.kullanici_id))
                
                # Yeni ID'yi al
                cursor.execute("SELECT @@IDENTITY")
                self.talep_id = cursor.fetchone()[0]
                self.txt_talep_no.setText(talep_no)
                self.btn_onaya.setVisible(True)  # Onaya gönder butonunu göster
            
            conn.commit()
            LogManager.log_insert('satinalma', 'satinalma.talepler', None, 'Talep kaydi olustu')
            conn.close()
            
            QMessageBox.information(self, "Başarılı", "Talep kaydedildi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _send_approval(self):
        """Talebi onaya gönder"""
        if not self.talep_id:
            QMessageBox.warning(self, "Uyarı", "Önce talebi kaydedin!")
            return
        
        # Satır kontrolü
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM satinalma.talep_satirlari WHERE talep_id = ?", (self.talep_id,))
            satir_sayisi = cursor.fetchone()[0]
            
            if satir_sayisi == 0:
                QMessageBox.warning(self, "Uyarı", "Onaya göndermek için en az bir kalem eklemelisiniz!")
                conn.close()
                return
            
            # Onay prosedürünü çağır
            reply = QMessageBox.question(
                self, "Onay", 
                "Bu talebi onaya göndermek istediğinize emin misiniz?\n\n"
                "Onaya gönderildikten sonra değişiklik yapamazsınız.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor.execute("EXEC satinalma.sp_TalepOnayaGonder ?, ?", (self.talep_id, self.kullanici_id))
                conn.commit()
                LogManager.log_update('satinalma', 'satinalma.sp_TalepOnayaGonder', None, 'satinalma.sp_TalepOnayaGonder islemi yapildi')
                conn.close()
                
                QMessageBox.information(
                    self, "Başarılı", 
                    "Talep onaya gönderildi!\n\n"
                    "Yetkili kişilere bildirim gönderildi."
                )
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Onaya gönderme hatası: {str(e)}")
    
    def _print_talep(self):
        """Talebi yazdır"""
        if not self.talep_id:
            QMessageBox.warning(self, "Uyarı", "Önce talebi kaydedin!")
            return
        
        try:
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec() == QDialog.Accepted:
                # HTML formatında talep formu oluştur
                html = self._generate_talep_html()
                
                document = QTextDocument()
                document.setHtml(html)
                
                # QPainter kullanarak yazdır
                painter = QPainter(printer)
                document.drawContents(painter)
                painter.end()
                
                QMessageBox.information(self, "Başarılı", "Talep yazdırıldı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yazdırma hatası: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _generate_talep_html(self):
        """Talep formu HTML'i oluştur - Resmi format"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Talep bilgilerini al
            cursor.execute("""
                SELECT t.talep_no, t.tarih, t.oncelik, t.istenen_termin, t.talep_nedeni,
                       d.ad as departman, p.ad + ' ' + p.soyad as talep_eden, t.tahmini_tutar,
                       t.durum, t.amir_onay_durumu, t.satinalma_onay_durumu
                FROM satinalma.talepler t
                LEFT JOIN ik.departmanlar d ON t.departman_id = d.id
                LEFT JOIN ik.personeller p ON t.talep_eden_id = p.id
                WHERE t.id = ?
            """, (self.talep_id,))
            talep = cursor.fetchone()
            
            # Satırları al
            cursor.execute("""
                SELECT satir_no, urun_adi, urun_kodu, talep_miktar, birim, aciklama
                FROM satinalma.talep_satirlari
                WHERE talep_id = ?
                ORDER BY satir_no
            """, (self.talep_id,))
            satirlar = cursor.fetchall()
            conn.close()
            
            # Tarih formatı
            tarih_str = talep[1].strftime('%d/%m/%Y') if talep[1] else '..../...../ 200'
            termin_str = talep[3].strftime('%d/%m/%Y') if talep[3] else ''
            
            # HTML - Resmi form formatı
            html = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{
                        size: A4;
                        margin: 15mm;
                    }}
                    body {{
                        font-family: Arial, sans-serif;
                        font-size: 10pt;
                        margin: 0;
                        padding: 0;
                    }}
                    .header-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 10px;
                    }}
                    .header-table td {{
                        border: 2px solid #000;
                        padding: 10px;
                        text-align: center;
                        font-weight: bold;
                    }}
                    .header-table .logo {{
                        width: 35%;
                        font-size: 14pt;
                    }}
                    .header-table .title {{
                        width: 35%;
                        font-size: 14pt;
                    }}
                    .header-table .date {{
                        width: 30%;
                        font-size: 10pt;
                    }}
                    .section-title {{
                        font-weight: bold;
                        font-size: 11pt;
                        margin-top: 15px;
                        margin-bottom: 5px;
                    }}
                    .content-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 10px;
                    }}
                    .content-table th,
                    .content-table td {{
                        border: 1px solid #000;
                        padding: 6px 4px;
                        font-size: 9pt;
                        text-align: left;
                        vertical-align: top;
                    }}
                    .content-table th {{
                        background-color: #f0f0f0;
                        font-weight: bold;
                        text-align: center;
                    }}
                    .content-table .sira {{
                        width: 30px;
                        text-align: center;
                    }}
                    .content-table .malzeme {{
                        width: 25%;
                    }}
                    .content-table .teknik {{
                        width: 20%;
                    }}
                    .content-table .miktar {{
                        width: 80px;
                        text-align: center;
                    }}
                    .content-table .tarih {{
                        width: 90px;
                        text-align: center;
                    }}
                    .content-table .aciklama {{
                        width: auto;
                    }}
                    .signature-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                    }}
                    .signature-table td {{
                        border: 1px solid #000;
                        padding: 40px 10px 10px 10px;
                        text-align: center;
                        font-weight: bold;
                        width: 33.33%;
                    }}
                    .footer {{
                        margin-top: 10px;
                        font-size: 8pt;
                        display: flex;
                        justify-content: space-between;
                    }}
                </style>
            </head>
            <body>
                <!-- Başlık -->
                <table class="header-table">
                    <tr>
                        <td class="logo">FİRMA<br/>LOGO</td>
                        <td class="title">SATINALMA<br/>TALEP<br/>FORMU</td>
                        <td class="date">
                            TARİH: {tarih_str}<br/><br/>
                            SIRA NO: {talep[0] or ''}
                        </td>
                    </tr>
                </table>
                
                <!-- Talep Eden Bölüm -->
                <div class="section-title">TALEP EDEN BÖLÜM:</div>
                <div style="margin-bottom: 10px; padding: 5px; border: 1px solid #ccc;">
                    <strong>Departman:</strong> {talep[5] or ''} &nbsp;&nbsp;&nbsp;
                    <strong>Talep Eden:</strong> {talep[6] or ''} &nbsp;&nbsp;&nbsp;
                    <strong>İstenen Termin:</strong> {termin_str}
                </div>
                
                <!-- Malzeme Listesi -->
                <table class="content-table">
                    <thead>
                        <tr>
                            <th class="sira">S/N</th>
                            <th class="malzeme">MALZEMENİN CİNSİ</th>
                            <th class="teknik">TEKNİK ÖZELLİK<br/>LOT/KOD NO</th>
                            <th class="miktar">MİKTAR</th>
                            <th class="tarih">İSTENİLEN<br/>TARİH</th>
                            <th class="aciklama">AÇIKLAMA</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Satırları ekle
            for i in range(25):  # 25 satır (formda görünen)
                if i < len(satirlar):
                    satir = satirlar[i]
                    html += f"""
                        <tr>
                            <td class="sira">{satir[0]}</td>
                            <td class="malzeme">{satir[1] or ''}</td>
                            <td class="teknik">{satir[2] or ''}</td>
                            <td class="miktar">{satir[3]} {satir[4]}</td>
                            <td class="tarih">{termin_str}</td>
                            <td class="aciklama">{satir[5] or ''}</td>
                        </tr>
                    """
                else:
                    html += f"""
                        <tr>
                            <td class="sira">{i+1}</td>
                            <td class="malzeme">&nbsp;</td>
                            <td class="teknik">&nbsp;</td>
                            <td class="miktar">&nbsp;</td>
                            <td class="tarih">&nbsp;</td>
                            <td class="aciklama">&nbsp;</td>
                        </tr>
                    """
            
            html += """
                    </tbody>
                </table>
                
                <!-- Onay Bölümü -->
                <div class="section-title">ONAY SONUCU:</div>
                <table class="signature-table">
                    <tr>
                        <td>TALEP EDEN/KİSİM AMİRİ<br/>TARİH/İMZA</td>
                        <td>ONAY<br/>TARİH/İMZA</td>
                        <td>SATINALMA<br/>TARİH/İMZA</td>
                    </tr>
                </table>
                
                <!-- Footer -->
                <div class="footer">
                    <span>FORM NO.:</span>
                    <span>REV.NO.:</span>
                    <span>REV.TAR.:</span>
                    <span>İLK YAY.TAR.:</span>
                </div>
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            print(f"HTML oluşturma hatası: {e}")
            import traceback
            traceback.print_exc()
            return "<html><body><h1>Hata: Form oluşturulamadı</h1></body></html>"
    

class SatinalmaTaleplerPage(BasePage):
    """Satınalma Talepleri Ana Sayfa"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.kullanici_id = 1  # Varsayılan kullanıcı
        self.all_rows = []
        self.has_approval_authority = True  # Herkes onaylayabilir
        self._setup_ui()
        self._load_data()
    
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Başlık
        header = QLabel("📋 Satınalma Talepleri")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px; padding: 12px;")
        toolbar_layout = QHBoxLayout(toolbar)
        
        btn_yeni = QPushButton("➕ Yeni Talep")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)

        # Onay butonları - BU SAYFAYI GÖREBİLİYORSANIZ ZATEN YETKİNİZ VAR
        # Menü yetkileri zaten kontrol ediyor
        btn_onayla = QPushButton("✅ Onayla")
        btn_onayla.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_onayla.clicked.connect(self._onayla)
        toolbar_layout.addWidget(btn_onayla)

        btn_reddet = QPushButton("❌ Reddet")
        btn_reddet.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_reddet.clicked.connect(self._reddet)
        toolbar_layout.addWidget(btn_reddet)

        toolbar_layout.addStretch()

        toolbar_layout.addWidget(self.create_export_button(title="Satinalma Talepleri"))

        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tümü", "TASLAK", "ONAY_BEKLIYOR", "AMIR_ONAYLADI", 
                                 "SATINALMA_ONAYLANDI", "REDDEDILDI"])
        self.cmb_durum.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px; color: {self.theme.get('text')};")
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_durum)
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 16px; color: {self.theme.get('text')};")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Talep No", "Tarih", "Departman", "Öncelik", "Tahmini Tutar", "Durum", "Amir Onay", "İşlem"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; color: {self.theme.get('text')}; }}
            QTableWidget::item {{ padding: 8px; }}
            QTableWidget::item:selected {{ background: {self.theme.get('primary')}; }}
            QHeaderView::section {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px; border: none; font-weight: bold; }}
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 150)
        self.table.setColumnWidth(7, 120)
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
            
            # TÜM TALEPLERİ GÖSTER (test için - sonra filtre ekleriz)
            cursor.execute("""
                SELECT t.id, t.talep_no, FORMAT(t.tarih, 'dd.MM.yyyy'),
                       d.ad, t.oncelik, t.tahmini_tutar, t.durum, t.amir_onay_durumu
                FROM satinalma.talepler t
                LEFT JOIN ik.departmanlar d ON t.departman_id = d.id
                ORDER BY t.tarih DESC, t.id DESC
            """)
            
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        
        durum_colors = {
            'TASLAK': self.theme.get('text_muted'),
            'ONAY_BEKLIYOR': self.theme.get('warning'),
            'AMIR_ONAYLADI': self.theme.get('info'),
            'SATINALMA_ONAYLANDI': self.theme.get('success'),
            'REDDEDILDI': self.theme.get('danger'),
        }
        
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 5 and val:  # Tutar
                    item = QTableWidgetItem(f"₺ {val:,.2f}")
                elif j == 6:  # Durum
                    item = QTableWidgetItem(str(val) if val else "")
                    item.setForeground(QColor(durum_colors.get(val, self.theme.get('text'))))
                elif j == 7:  # Amir onay
                    item = QTableWidgetItem(str(val) if val else "-")
                    if val == "ONAYLANDI":
                        item.setForeground(QColor(self.theme.get('success')))
                    elif val == "REDDEDILDI":
                        item.setForeground(QColor(self.theme.get('danger')))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)

            rid = row[0]
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=rid: self._duzenle_by_id(rid), "edit"),
            ])
            self.table.setCellWidget(i, 8, widget)
            self.table.setRowHeight(i, 42)

        self.lbl_stat.setText(f"Toplam: {len(rows)} talep")

    def _duzenle_by_id(self, talep_id):
        """ID ile talep düzenleme (satır butonundan)"""
        dialog = TalepDialog(self.theme, self, talep_id, self.kullanici_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _filter(self):
        durum = self.cmb_durum.currentText()
        if durum == "Tümü":
            self._display_data(self.all_rows)
        else:
            filtered = [r for r in self.all_rows if r[6] == durum]
            self._display_data(filtered)
    
    def _yeni(self):
        dialog = TalepDialog(self.theme, self, kullanici_id=self.kullanici_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir talep seçin!")
            return
        talep_id = int(self.table.item(row, 0).text())
        dialog = TalepDialog(self.theme, self, talep_id, self.kullanici_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _onayla(self):
        """Seçili talebi onayla"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir talep seçin!")
            return
        
        talep_id = int(self.table.item(row, 0).text())
        durum = self.table.item(row, 6).text()
        
        if durum not in ("ONAY_BEKLIYOR", "AMIR_ONAYLADI"):
            QMessageBox.warning(self, "Uyarı", "Sadece onay bekleyen talepler onaylanabilir!")
            return
        
        # Onay notu al
        from PySide6.QtWidgets import QInputDialog
        onay_notu, ok = QInputDialog.getMultiLineText(
            self, "Onay Notu", 
            "Onay notu (opsiyonel):"
        )
        
        if not ok:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("EXEC satinalma.sp_TalepOnayla ?, ?, ?", 
                          (talep_id, self.kullanici_id, onay_notu or None))
            conn.commit()
            LogManager.log_update('satinalma', 'satinalma.sp_TalepOnayla', None, 'satinalma.sp_TalepOnayla islemi yapildi')
            conn.close()
            
            self._load_data()
            QMessageBox.information(self, "Başarılı", "Talep onaylandı ve ilgili kişilere bildirim gönderildi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Onaylama hatası: {str(e)}")
    
    def _reddet(self):
        """Seçili talebi reddet"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir talep seçin!")
            return
        
        talep_id = int(self.table.item(row, 0).text())
        durum = self.table.item(row, 6).text()
        
        if durum not in ("ONAY_BEKLIYOR", "AMIR_ONAYLADI"):
            QMessageBox.warning(self, "Uyarı", "Sadece onay bekleyen talepler reddedilebilir!")
            return
        
        # Red nedeni al
        from PySide6.QtWidgets import QInputDialog
        red_nedeni, ok = QInputDialog.getMultiLineText(
            self, "Red Nedeni", 
            "Red nedeni (zorunlu):"
        )
        
        if not ok or not red_nedeni.strip():
            QMessageBox.warning(self, "Uyarı", "Red nedeni girilmeli!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("EXEC satinalma.sp_TalepReddet ?, ?, ?", 
                          (talep_id, self.kullanici_id, red_nedeni))
            conn.commit()
            LogManager.log_update('satinalma', 'satinalma.sp_TalepReddet', None, 'satinalma.sp_TalepReddet islemi yapildi')
            conn.close()
            
            self._load_data()
            QMessageBox.information(self, "Başarılı", "Talep reddedildi ve talep edene bildirim gönderildi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Reddetme hatası: {str(e)}")
