# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Satınalma Siparişleri
satinalma.siparisler ve satinalma.siparis_satirlari
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QSpinBox,
    QDoubleSpinBox, QTabWidget
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager


class SiparisSatirDialog(QDialog):
    """Sipariş satırı ekleme/düzenleme"""
    
    def __init__(self, theme: dict, siparis_id: int, tedarikci_id: int, parent=None, satir_id=None):
        super().__init__(parent)
        self.theme = theme
        self.siparis_id = siparis_id
        self.tedarikci_id = tedarikci_id
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
        form.addRow("Ürün Adı*:", self.txt_urun_adi)
        
        miktar_layout = QHBoxLayout()
        self.spin_miktar = QDoubleSpinBox()
        self.spin_miktar.setRange(0.01, 9999999)
        self.spin_miktar.setDecimals(2)
        self.spin_miktar.setValue(1)
        self.spin_miktar.valueChanged.connect(self._calc_tutar)
        miktar_layout.addWidget(self.spin_miktar)
        
        self.cmb_birim = QComboBox()
        self.cmb_birim.addItems(["ADET", "KG", "LT", "MT", "M2", "M3", "PAKET", "KUTU", "VARIL"])
        miktar_layout.addWidget(self.cmb_birim)
        form.addRow("Miktar*:", miktar_layout)
        
        fiyat_layout = QHBoxLayout()
        self.spin_fiyat = QDoubleSpinBox()
        self.spin_fiyat.setRange(0, 9999999)
        self.spin_fiyat.setDecimals(4)
        self.spin_fiyat.setPrefix("")
        self.spin_fiyat.valueChanged.connect(self._calc_tutar)
        fiyat_layout.addWidget(self.spin_fiyat)

        self.cmb_para_birimi = QComboBox()
        self.cmb_para_birimi.setMinimumWidth(80)
        fiyat_layout.addWidget(self.cmb_para_birimi)
        form.addRow("Birim Fiyat*:", fiyat_layout)
        
        self.spin_kdv = QSpinBox()
        self.spin_kdv.setRange(0, 100)
        self.spin_kdv.setValue(20)
        self.spin_kdv.setSuffix(" %")
        self.spin_kdv.valueChanged.connect(self._calc_tutar)
        form.addRow("KDV Oranı:", self.spin_kdv)
        
        self.lbl_tutar = QLabel("Tutar: 0.00 + KDV 0.00 = 0.00")
        self.lbl_tutar.setStyleSheet(f"font-weight: bold; color: {self.theme.get('primary')};")
        form.addRow("", self.lbl_tutar)
        
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(60)
        form.addRow("Açıklama:", self.txt_aciklama)
        
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

            # Para birimleri
            self.cmb_para_birimi.clear()
            try:
                cursor.execute("SELECT kod FROM tanim.para_birimleri WHERE aktif_mi = 1 ORDER BY CASE WHEN kod='TRY' THEN 0 ELSE 1 END, kod")
                for r in cursor.fetchall():
                    self.cmb_para_birimi.addItem(r[0], r[0])
            except Exception:
                pass
            if self.cmb_para_birimi.count() == 0:
                self.cmb_para_birimi.addItem("TRY", "TRY")
                self.cmb_para_birimi.addItem("USD", "USD")
                self.cmb_para_birimi.addItem("EUR", "EUR")

            self.cmb_urun.addItem("-- Manuel Giriş --", None)
            
            # Anlaşmalı fiyatlar
            if self.tedarikci_id:
                cursor.execute("""
                    SELECT urun_id, urun_adi, birim_fiyat FROM satinalma.tedarikci_fiyatlari 
                    WHERE tedarikci_id = ? AND aktif_mi = 1 
                    AND GETDATE() BETWEEN gecerlilik_baslangic AND ISNULL(gecerlilik_bitis, '2099-12-31')
                """, (self.tedarikci_id,))
                for row in cursor.fetchall():
                    self.cmb_urun.addItem(f"[ANLASMALI] {row[1]} - {row[2]:.4f}", (row[0], row[2]))
            
            cursor.execute("SELECT id, urun_kodu, urun_adi FROM stok.urunler WHERE aktif_mi = 1 ORDER BY urun_kodu")
            for row in cursor.fetchall():
                self.cmb_urun.addItem(f"{row[1]} - {row[2]}", (row[0], None))
            conn.close()
        except Exception:
            pass
    
    def _on_urun_changed(self, index):
        if index > 0:
            text = self.cmb_urun.currentText()
            data = self.cmb_urun.currentData()
            if "[ANLAŞMALI]" in text:
                urun_adi = text.replace("[ANLAŞMALI] ", "").split(" - ")[0]
                self.txt_urun_adi.setText(urun_adi)
                if data and data[1]:
                    self.spin_fiyat.setValue(float(data[1]))
            elif " - " in text:
                self.txt_urun_adi.setText(text.split(" - ", 1)[1])
        self._calc_tutar()
    
    def _calc_tutar(self):
        miktar = self.spin_miktar.value()
        fiyat = self.spin_fiyat.value()
        kdv_orani = self.spin_kdv.value()
        tutar = miktar * fiyat
        kdv = tutar * kdv_orani / 100
        toplam = tutar + kdv
        self.lbl_tutar.setText(f"Tutar: {tutar:,.2f} + KDV {kdv:,.2f} = {toplam:,.2f}")
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # para_birimi kolonu garanti
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA='satinalma' AND TABLE_NAME='siparis_satirlari' AND COLUMN_NAME='para_birimi')
                    ALTER TABLE satinalma.siparis_satirlari ADD para_birimi NVARCHAR(10) NULL
            """)
            cursor.execute("""
                SELECT urun_id, urun_adi, siparis_miktar, birim, birim_fiyat, kdv_orani, aciklama,
                       ISNULL(para_birimi, 'TRY')
                FROM satinalma.siparis_satirlari WHERE id = ?
            """, (self.satir_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.txt_urun_adi.setText(row[1] or "")
                self.spin_miktar.setValue(float(row[2]) if row[2] else 1)
                idx = self.cmb_birim.findText(row[3] or "ADET")
                if idx >= 0: self.cmb_birim.setCurrentIndex(idx)
                self.spin_fiyat.setValue(float(row[4]) if row[4] else 0)
                self.spin_kdv.setValue(int(row[5]) if row[5] else 20)
                self.txt_aciklama.setPlainText(row[6] or "")
                pb_idx = self.cmb_para_birimi.findData(row[7])
                if pb_idx >= 0:
                    self.cmb_para_birimi.setCurrentIndex(pb_idx)
                self._calc_tutar()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        urun_adi = self.txt_urun_adi.text().strip()
        if not urun_adi:
            QMessageBox.warning(self, "Uyarı", "Ürün adı zorunludur!")
            return
        if self.spin_fiyat.value() <= 0:
            QMessageBox.warning(self, "Uyarı", "Birim fiyat girilmelidir!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # para_birimi kolonu garanti
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA='satinalma' AND TABLE_NAME='siparis_satirlari' AND COLUMN_NAME='para_birimi')
                    ALTER TABLE satinalma.siparis_satirlari ADD para_birimi NVARCHAR(10) NULL
            """)

            data = self.cmb_urun.currentData()
            urun_id = data[0] if data else None
            miktar = self.spin_miktar.value()
            fiyat = self.spin_fiyat.value()
            kdv_orani = self.spin_kdv.value()
            tutar = miktar * fiyat
            kdv = tutar * kdv_orani / 100
            toplam = tutar + kdv
            para_birimi = self.cmb_para_birimi.currentData() or 'TRY'

            if self.satir_id:
                cursor.execute("""
                    UPDATE satinalma.siparis_satirlari SET
                        urun_id = ?, urun_adi = ?, siparis_miktar = ?, birim = ?,
                        birim_fiyat = ?, tutar = ?, kdv_orani = ?, kdv_tutari = ?, toplam = ?,
                        para_birimi = ?, aciklama = ?
                    WHERE id = ?
                """, (urun_id, urun_adi, miktar, self.cmb_birim.currentText(),
                      fiyat, tutar, kdv_orani, kdv, toplam, para_birimi,
                      self.txt_aciklama.toPlainText().strip() or None, self.satir_id))
            else:
                cursor.execute("SELECT ISNULL(MAX(satir_no), 0) + 1 FROM satinalma.siparis_satirlari WHERE siparis_id = ?", (self.siparis_id,))
                satir_no = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO satinalma.siparis_satirlari
                    (siparis_id, satir_no, urun_id, urun_adi, siparis_miktar, birim, birim_fiyat, tutar, kdv_orani, kdv_tutari, toplam, para_birimi, aciklama)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.siparis_id, satir_no, urun_id, urun_adi, miktar, self.cmb_birim.currentText(),
                      fiyat, tutar, kdv_orani, kdv, toplam, para_birimi, self.txt_aciklama.toPlainText().strip() or None))
            
            conn.commit()
            LogManager.log_insert('satinalma', 'satinalma.siparis_satirlari', None, 'Siparis kaydi olustu')
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class SiparisDialog(QDialog):
    """Satınalma siparişi oluşturma/düzenleme"""
    
    def __init__(self, theme: dict, parent=None, siparis_id=None):
        super().__init__(parent)
        self.theme = theme
        self.siparis_id = siparis_id
        self.tedarikci_id = None
        self.setWindowTitle("Satınalma Siparişi" if not siparis_id else "Sipariş Düzenle")
        self.setMinimumSize(950, 650)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if siparis_id:
            self._load_data()
            self._load_satirlar()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox {{
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
        
        self.txt_siparis_no = QLineEdit()
        self.txt_siparis_no.setReadOnly(True)
        self.txt_siparis_no.setPlaceholderText("Otomatik")
        genel_layout.addRow("Sipariş No:", self.txt_siparis_no)
        
        self.date_tarih = QDateEdit()
        self.date_tarih.setDate(QDate.currentDate())
        self.date_tarih.setCalendarPopup(True)
        genel_layout.addRow("Tarih:", self.date_tarih)
        
        self.cmb_tedarikci = QComboBox()
        self.cmb_tedarikci.currentIndexChanged.connect(self._on_tedarikci_changed)
        genel_layout.addRow("Tedarikçi*:", self.cmb_tedarikci)
        
        self.cmb_andasma = QComboBox()
        genel_layout.addRow("Anlaşma:", self.cmb_andasma)
        
        self.date_teslim = QDateEdit()
        self.date_teslim.setDate(QDate.currentDate().addDays(14))
        self.date_teslim.setCalendarPopup(True)
        genel_layout.addRow("İstenen Teslim:", self.date_teslim)
        
        self.spin_vade = QSpinBox()
        self.spin_vade.setRange(0, 365)
        self.spin_vade.setValue(30)
        self.spin_vade.setSuffix(" gün")
        genel_layout.addRow("Ödeme Vadesi:", self.spin_vade)
        
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(60)
        genel_layout.addRow("Notlar:", self.txt_notlar)
        
        tabs.addTab(tab_genel, "📋 Genel")
        
        # Tab 2: Kalemler
        tab_kalemler = QWidget()
        kalem_layout = QVBoxLayout(tab_kalemler)
        
        toolbar = QHBoxLayout()
        btn_ekle = QPushButton("➕ Kalem Ekle")
        btn_ekle.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_ekle.clicked.connect(self._add_satir)
        toolbar.addWidget(btn_ekle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._delete_satir)
        toolbar.addWidget(btn_sil)
        toolbar.addStretch()
        kalem_layout.addLayout(toolbar)
        
        self.table_satirlar = QTableWidget()
        self.table_satirlar.setColumnCount(8)
        self.table_satirlar.setHorizontalHeaderLabels(["ID", "Sıra", "Ürün Adı", "Miktar", "Birim", "Birim Fiyat", "KDV", "Toplam"])
        self.table_satirlar.setColumnHidden(0, True)
        self.table_satirlar.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_satirlar.setStyleSheet(f"QTableWidget {{ background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; }}")
        header = self.table_satirlar.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_satirlar.doubleClicked.connect(self._edit_satir)
        kalem_layout.addWidget(self.table_satirlar)
        
        self.lbl_genel_toplam = QLabel("Genel Toplam: 0.00")
        self.lbl_genel_toplam.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {self.theme.get('primary')};")
        kalem_layout.addWidget(self.lbl_genel_toplam)
        
        tabs.addTab(tab_kalemler, "📦 Kalemler")
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
        self.cmb_andasma.clear()
        self.cmb_andasma.addItem("-- Anlaşma Yok --", None)
        if self.tedarikci_id:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, andasma_no FROM satinalma.tedarikci_anlasmalari
                    WHERE tedarikci_id = ? AND durum = 'AKTIF' AND bitis_tarihi >= GETDATE()
                """, (self.tedarikci_id,))
                for row in cursor.fetchall():
                    self.cmb_andasma.addItem(row[1], row[0])
                conn.close()
            except Exception:
                pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT siparis_no, tarih, tedarikci_id, istenen_teslim_tarihi, odeme_vade_gun, notlar FROM satinalma.siparisler WHERE id = ?", (self.siparis_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.txt_siparis_no.setText(row[0] or "")
                if row[1]: self.date_tarih.setDate(QDate(row[1].year, row[1].month, row[1].day))
                if row[2]:
                    self.tedarikci_id = row[2]
                    idx = self.cmb_tedarikci.findData(row[2])
                    if idx >= 0: self.cmb_tedarikci.setCurrentIndex(idx)
                if row[3]: self.date_teslim.setDate(QDate(row[3].year, row[3].month, row[3].day))
                self.spin_vade.setValue(row[4] or 30)
                self.txt_notlar.setPlainText(row[5] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _load_satirlar(self):
        if not self.siparis_id: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, satir_no, urun_adi, siparis_miktar, birim, birim_fiyat, kdv_tutari, toplam FROM satinalma.siparis_satirlari WHERE siparis_id = ? ORDER BY satir_no", (self.siparis_id,))
            rows = cursor.fetchall()
            conn.close()
            
            self.table_satirlar.setRowCount(len(rows))
            genel_toplam = 0
            for i, row in enumerate(rows):
                self.table_satirlar.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_satirlar.setItem(i, 1, QTableWidgetItem(str(row[1])))
                self.table_satirlar.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.table_satirlar.setItem(i, 3, QTableWidgetItem(f"{row[3]:,.2f}" if row[3] else ""))
                self.table_satirlar.setItem(i, 4, QTableWidgetItem(row[4] or ""))
                self.table_satirlar.setItem(i, 5, QTableWidgetItem(f"{row[5]:,.4f}" if row[5] else ""))
                self.table_satirlar.setItem(i, 6, QTableWidgetItem(f"{row[6]:,.2f}" if row[6] else ""))
                self.table_satirlar.setItem(i, 7, QTableWidgetItem(f"{row[7]:,.2f}" if row[7] else ""))
                if row[7]: genel_toplam += float(row[7])
            self.lbl_genel_toplam.setText(f"Genel Toplam: {genel_toplam:,.2f}")
        except Exception: pass
    
    def _add_satir(self):
        if not self.siparis_id:
            QMessageBox.warning(self, "Uyarı", "Önce siparişi kaydedin!")
            return
        if not self.tedarikci_id:
            QMessageBox.warning(self, "Uyarı", "Tedarikçi seçin!")
            return
        dialog = SiparisSatirDialog(self.theme, self.siparis_id, self.tedarikci_id, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
    
    def _edit_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0: return
        satir_id = int(self.table_satirlar.item(row, 0).text())
        dialog = SiparisSatirDialog(self.theme, self.siparis_id, self.tedarikci_id, self, satir_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
    
    def _delete_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0: return
        satir_id = int(self.table_satirlar.item(row, 0).text())
        if QMessageBox.question(self, "Onay", "Kalemi silmek istiyor musunuz?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM satinalma.siparis_satirlari WHERE id = ?", (satir_id,))
                conn.commit()
                LogManager.log_delete('satinalma', 'satinalma.siparis_satirlari', None, 'Kayit silindi')
                conn.close()
                self._load_satirlar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        if not self.cmb_tedarikci.currentData():
            QMessageBox.warning(self, "Uyarı", "Tedarikçi seçimi zorunludur!")
            return
        try:
            from core.yetki_manager import YetkiManager
            current_user_id = getattr(YetkiManager, '_current_user_id', None)

            conn = get_db_connection()
            cursor = conn.cursor()

            # Hazirlayan/Onaylayan isim + onay tarihi kolonlarini garanti et
            for col_sql in [
                "IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='satinalma' AND TABLE_NAME='siparisler' AND COLUMN_NAME='hazirlayan_ad') ALTER TABLE satinalma.siparisler ADD hazirlayan_ad NVARCHAR(150) NULL",
                "IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='satinalma' AND TABLE_NAME='siparisler' AND COLUMN_NAME='onaylayan_ad') ALTER TABLE satinalma.siparisler ADD onaylayan_ad NVARCHAR(150) NULL",
                "IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='satinalma' AND TABLE_NAME='siparisler' AND COLUMN_NAME='onay_tarihi') ALTER TABLE satinalma.siparisler ADD onay_tarihi DATETIME NULL",
            ]:
                cursor.execute(col_sql)

            # current user ad soyad
            current_ad = None
            if current_user_id:
                cursor.execute("SELECT LTRIM(RTRIM(ISNULL(ad,'') + ' ' + ISNULL(soyad,''))) FROM sistem.kullanicilar WHERE id = ?", (current_user_id,))
                r = cursor.fetchone()
                if r and r[0] and r[0].strip():
                    current_ad = r[0].strip()

            if self.siparis_id:
                cursor.execute("""
                    UPDATE satinalma.siparisler SET tedarikci_id = ?, andasma_id = ?, istenen_teslim_tarihi = ?,
                        odeme_vade_gun = ?, notlar = ?,
                        onaylayan_ad = ISNULL(?, onaylayan_ad),
                        hazirlayan_ad = ISNULL(hazirlayan_ad, ?),
                        onay_tarihi = GETDATE(),
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (self.cmb_tedarikci.currentData(), self.cmb_andasma.currentData(),
                      self.date_teslim.date().toPython(), self.spin_vade.value(),
                      self.txt_notlar.toPlainText().strip() or None,
                      current_ad, current_ad, self.siparis_id))
            else:
                cursor.execute("SELECT 'SIP-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM satinalma.siparisler), 0) + 1 AS VARCHAR), 4)")
                siparis_no = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO satinalma.siparisler (siparis_no, tarih, tedarikci_id, andasma_id, istenen_teslim_tarihi, odeme_vade_gun, notlar, hazirlayan_ad, onaylayan_ad, onay_tarihi)
                    OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (siparis_no, self.date_tarih.date().toPython(), self.cmb_tedarikci.currentData(),
                      self.cmb_andasma.currentData(), self.date_teslim.date().toPython(),
                      self.spin_vade.value(), self.txt_notlar.toPlainText().strip() or None,
                      current_ad, current_ad))
                self.siparis_id = cursor.fetchone()[0]
                self.txt_siparis_no.setText(siparis_no)
            
            cursor.execute("""
                UPDATE satinalma.siparisler SET
                    ara_toplam = (SELECT SUM(tutar) FROM satinalma.siparis_satirlari WHERE siparis_id = ?),
                    kdv_toplam = (SELECT SUM(kdv_tutari) FROM satinalma.siparis_satirlari WHERE siparis_id = ?),
                    genel_toplam = (SELECT SUM(toplam) FROM satinalma.siparis_satirlari WHERE siparis_id = ?)
                WHERE id = ?
            """, (self.siparis_id, self.siparis_id, self.siparis_id, self.siparis_id))
            
            conn.commit()
            LogManager.log_update('satinalma', 'satinalma.siparisler', None, 'Kayit guncellendi')
            conn.close()
            QMessageBox.information(self, "Başarılı", "Sipariş kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class SatinalmaSiparislerPage(BasePage):
    """Satınalma Siparişleri Ana Sayfa"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("📦 Satınalma Siparişleri")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Sipariş")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)

        toolbar_layout.addStretch()
        
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tümü", "TASLAK", "GONDERILDI", "KISMI_TESLIM", "TAMAMLANDI"])
        self.cmb_durum.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px; color: {self.theme.get('text')};")
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_durum)
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 16px; color: {self.theme.get('text')};")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Sipariş No", "Tarih", "Tedarikçi", "Teslim", "Toplam", "Durum", "İşlem"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; color: {self.theme.get('text')}; }}
            QTableWidget::item:selected {{ background: {self.theme.get('primary')}; }}
            QHeaderView::section {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px; font-weight: bold; }}
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(7, 120)
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
                SELECT s.id, s.siparis_no, FORMAT(s.tarih, 'dd.MM.yyyy'), c.unvan,
                       FORMAT(s.istenen_teslim_tarihi, 'dd.MM.yyyy'), s.genel_toplam, s.durum
                FROM satinalma.siparisler s
                LEFT JOIN musteri.cariler c ON s.tedarikci_id = c.id
                ORDER BY s.tarih DESC
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}\n\nÖnce SQL tabloları oluşturun!")
    
    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 5 and val:
                    item = QTableWidgetItem(f"{val:,.2f}")
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)

            rid = row[0]
            widget = self.create_action_buttons([
                ("PDF", "PDF Yazdir", lambda checked, rid=rid: self._siparis_pdf(rid), "info"),
                ("Duzenle", "Duzenle", lambda checked, rid=rid: self._duzenle_by_id(rid), "edit"),
            ])
            self.table.setCellWidget(i, 7, widget)
            self.table.setRowHeight(i, 42)

        self.lbl_stat.setText(f"Toplam: {len(rows)} sipariş")

    def _duzenle_by_id(self, siparis_id):
        """ID ile siparis duzenleme"""
        dialog = SiparisDialog(self.theme, self, siparis_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _siparis_pdf(self, siparis_id):
        """Siparis PDF - talep formu ile ayni stil"""
        try:
            from utils.satinalma_siparis_pdf import satinalma_siparis_pdf
            satinalma_siparis_pdf(siparis_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF hatasi: {e}")
            import traceback
            traceback.print_exc()

    def _filter(self):
        durum = self.cmb_durum.currentText()
        if durum == "Tümü":
            self._display_data(self.all_rows)
        else:
            self._display_data([r for r in self.all_rows if r[6] == durum])
    
    def _yeni(self):
        dialog = SiparisDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        siparis_id = int(self.table.item(row, 0).text())
        dialog = SiparisDialog(self.theme, self, siparis_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
