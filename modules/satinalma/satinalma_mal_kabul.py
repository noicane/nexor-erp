# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Mal Kabul (Giriş Kabul)
satinalma.mal_kabuller ve satinalma.mal_kabul_satirlari
Lot, Parti, SKT, Sertifika takibi
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QCheckBox,
    QDoubleSpinBox, QTabWidget, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from datetime import datetime


class MalKabulSatirDialog(QDialog):
    """Mal kabul satırı - Lot/Parti/SKT/Sertifika bilgileri"""
    
    def __init__(self, theme: dict, kabul_id: int, parent=None, satir_id=None):
        super().__init__(parent)
        self.theme = theme
        self.kabul_id = kabul_id
        self.satir_id = satir_id
        self.setWindowTitle("Kalem Ekle" if not satir_id else "Kalem Düzenle")
        self.setMinimumWidth(550)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if satir_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px; padding: 8px;
                color: {self.theme.get('text')};
            }}
            QGroupBox {{ color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; margin-top: 10px; padding-top: 10px; }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Ürün Bilgileri
        form1 = QFormLayout()
        
        self.cmb_urun = QComboBox()
        self.cmb_urun.setEditable(True)
        self.cmb_urun.currentIndexChanged.connect(self._on_urun_changed)
        form1.addRow("Ürün:", self.cmb_urun)
        
        self.txt_urun_adi = QLineEdit()
        form1.addRow("Ürün Adı*:", self.txt_urun_adi)
        
        miktar_layout = QHBoxLayout()
        self.spin_miktar = QDoubleSpinBox()
        self.spin_miktar.setRange(0.01, 9999999)
        self.spin_miktar.setDecimals(2)
        self.spin_miktar.setValue(1)
        miktar_layout.addWidget(self.spin_miktar)
        
        self.cmb_birim = QComboBox()
        self.cmb_birim.addItems(["ADET", "KG", "LT", "MT", "M2", "M3", "PAKET", "KUTU", "VARIL"])
        miktar_layout.addWidget(self.cmb_birim)
        form1.addRow("Teslim Miktar*:", miktar_layout)
        
        layout.addLayout(form1)
        
        # Lot/Parti Bilgileri
        lbl_lot = QLabel("📦 Lot / Parti Bilgileri")
        lbl_lot.setStyleSheet(f"font-weight: bold; color: {self.theme.get('primary')}; margin-top: 10px;")
        layout.addWidget(lbl_lot)
        
        form2 = QFormLayout()
        
        self.txt_lot_no = QLineEdit()
        self.txt_lot_no.setPlaceholderText("Tedarikçi lot numarası")
        form2.addRow("Lot No:", self.txt_lot_no)
        
        self.txt_parti_no = QLineEdit()
        self.txt_parti_no.setPlaceholderText("Parti/Batch numarası")
        form2.addRow("Parti No:", self.txt_parti_no)
        
        self.txt_seri_no = QLineEdit()
        self.txt_seri_no.setPlaceholderText("Seri numarası (varsa)")
        form2.addRow("Seri No:", self.txt_seri_no)
        
        layout.addLayout(form2)
        
        # Tarihler
        lbl_tarih = QLabel("📅 Tarih Bilgileri")
        lbl_tarih.setStyleSheet(f"font-weight: bold; color: {self.theme.get('primary')}; margin-top: 10px;")
        layout.addWidget(lbl_tarih)
        
        form3 = QFormLayout()
        
        self.date_uretim = QDateEdit()
        self.date_uretim.setCalendarPopup(True)
        self.date_uretim.setDate(QDate.currentDate())
        self.date_uretim.setDisplayFormat("dd.MM.yyyy")
        form3.addRow("Üretim Tarihi:", self.date_uretim)
        
        self.date_skt = QDateEdit()
        self.date_skt.setCalendarPopup(True)
        self.date_skt.setDate(QDate.currentDate().addYears(2))
        self.date_skt.setDisplayFormat("dd.MM.yyyy")
        form3.addRow("Son Kullanma Tarihi:", self.date_skt)
        
        layout.addLayout(form3)
        
        # Sertifika
        lbl_sertifika = QLabel("📄 Sertifika Bilgileri")
        lbl_sertifika.setStyleSheet(f"font-weight: bold; color: {self.theme.get('primary')}; margin-top: 10px;")
        layout.addWidget(lbl_sertifika)
        
        form4 = QFormLayout()
        
        self.chk_sertifika = QCheckBox("Sertifika Mevcut")
        self.chk_sertifika.setStyleSheet(f"color: {self.theme.get('text')};")
        form4.addRow("", self.chk_sertifika)
        
        self.txt_sertifika_no = QLineEdit()
        self.txt_sertifika_no.setPlaceholderText("Sertifika/CoA numarası")
        form4.addRow("Sertifika No:", self.txt_sertifika_no)
        
        dosya_layout = QHBoxLayout()
        self.txt_dosya = QLineEdit()
        self.txt_dosya.setReadOnly(True)
        self.txt_dosya.setPlaceholderText("Sertifika dosyası seçilmedi")
        dosya_layout.addWidget(self.txt_dosya)
        
        btn_dosya = QPushButton("📁")
        btn_dosya.setFixedWidth(40)
        btn_dosya.clicked.connect(self._select_file)
        dosya_layout.addWidget(btn_dosya)
        form4.addRow("Dosya:", dosya_layout)
        
        layout.addLayout(form4)
        
        # Açıklama
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(50)
        self.txt_aciklama.setPlaceholderText("Açıklama / Notlar")
        layout.addWidget(self.txt_aciklama)
        
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
    
    def _select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sertifika Dosyası Seç", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            self.txt_dosya.setText(file_path)
            self.chk_sertifika.setChecked(True)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT urun_id, urun_adi, teslim_miktar, birim, lot_no, parti_no, seri_no,
                       uretim_tarihi, son_kullanma_tarihi, sertifika_var_mi, sertifika_no, 
                       sertifika_dosya_yolu, aciklama
                FROM satinalma.mal_kabul_satirlari WHERE id = ?
            """, (self.satir_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                if row[0]:
                    idx = self.cmb_urun.findData(row[0])
                    if idx >= 0: self.cmb_urun.setCurrentIndex(idx)
                self.txt_urun_adi.setText(row[1] or "")
                self.spin_miktar.setValue(float(row[2]) if row[2] else 1)
                idx = self.cmb_birim.findText(row[3] or "ADET")
                if idx >= 0: self.cmb_birim.setCurrentIndex(idx)
                self.txt_lot_no.setText(row[4] or "")
                self.txt_parti_no.setText(row[5] or "")
                self.txt_seri_no.setText(row[6] or "")
                if row[7]: self.date_uretim.setDate(QDate(row[7].year, row[7].month, row[7].day))
                if row[8]: self.date_skt.setDate(QDate(row[8].year, row[8].month, row[8].day))
                self.chk_sertifika.setChecked(row[9] or False)
                self.txt_sertifika_no.setText(row[10] or "")
                self.txt_dosya.setText(row[11] or "")
                self.txt_aciklama.setPlainText(row[12] or "")
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
            
            if self.satir_id:
                cursor.execute("""
                    UPDATE satinalma.mal_kabul_satirlari SET
                        urun_id = ?, urun_adi = ?, teslim_miktar = ?, birim = ?,
                        lot_no = ?, parti_no = ?, seri_no = ?,
                        uretim_tarihi = ?, son_kullanma_tarihi = ?,
                        sertifika_var_mi = ?, sertifika_no = ?, sertifika_dosya_yolu = ?, aciklama = ?
                    WHERE id = ?
                """, (
                    urun_id, urun_adi, self.spin_miktar.value(), self.cmb_birim.currentText(),
                    self.txt_lot_no.text().strip() or None,
                    self.txt_parti_no.text().strip() or None,
                    self.txt_seri_no.text().strip() or None,
                    self.date_uretim.date().toPython(),
                    self.date_skt.date().toPython(),
                    self.chk_sertifika.isChecked(),
                    self.txt_sertifika_no.text().strip() or None,
                    self.txt_dosya.text().strip() or None,
                    self.txt_aciklama.toPlainText().strip() or None,
                    self.satir_id
                ))
            else:
                cursor.execute("SELECT ISNULL(MAX(satir_no), 0) + 1 FROM satinalma.mal_kabul_satirlari WHERE kabul_id = ?", (self.kabul_id,))
                satir_no = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO satinalma.mal_kabul_satirlari
                    (kabul_id, satir_no, urun_id, urun_adi, teslim_miktar, birim,
                     lot_no, parti_no, seri_no, uretim_tarihi, son_kullanma_tarihi,
                     sertifika_var_mi, sertifika_no, sertifika_dosya_yolu, aciklama)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.kabul_id, satir_no, urun_id, urun_adi,
                    self.spin_miktar.value(), self.cmb_birim.currentText(),
                    self.txt_lot_no.text().strip() or None,
                    self.txt_parti_no.text().strip() or None,
                    self.txt_seri_no.text().strip() or None,
                    self.date_uretim.date().toPython(),
                    self.date_skt.date().toPython(),
                    self.chk_sertifika.isChecked(),
                    self.txt_sertifika_no.text().strip() or None,
                    self.txt_dosya.text().strip() or None,
                    self.txt_aciklama.toPlainText().strip() or None
                ))
            
            conn.commit()
            LogManager.log_insert('satinalma', 'satinalma.mal_kabul_satirlari', None, 'Mal kabul kaydi olustu')
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class MalKabulDialog(QDialog):
    """Mal kabul ana dialog"""
    
    def __init__(self, theme: dict, parent=None, kabul_id=None):
        super().__init__(parent)
        self.theme = theme
        self.kabul_id = kabul_id
        self.setWindowTitle("Mal Kabul" if not kabul_id else "Mal Kabul Düzenle")
        self.setMinimumSize(950, 600)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if kabul_id:
            self._load_data()
            self._load_satirlar()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit {{
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
        
        self.txt_kabul_no = QLineEdit()
        self.txt_kabul_no.setReadOnly(True)
        self.txt_kabul_no.setPlaceholderText("Otomatik")
        genel_layout.addRow("Kabul No:", self.txt_kabul_no)
        
        self.date_tarih = QDateEdit()
        self.date_tarih.setDate(QDate.currentDate())
        self.date_tarih.setCalendarPopup(True)
        self.date_tarih.setDisplayFormat("dd.MM.yyyy HH:mm")
        genel_layout.addRow("Tarih:", self.date_tarih)
        
        self.cmb_tedarikci = QComboBox()
        genel_layout.addRow("Tedarikçi*:", self.cmb_tedarikci)
        
        self.cmb_siparis = QComboBox()
        self.cmb_siparis.currentIndexChanged.connect(self._on_siparis_changed)
        genel_layout.addRow("Siparis:", self.cmb_siparis)
        
        self.txt_tedarikci_irsaliye = QLineEdit()
        self.txt_tedarikci_irsaliye.setPlaceholderText("Tedarikçi irsaliye numarası")
        genel_layout.addRow("Tedarikçi İrsaliye No:", self.txt_tedarikci_irsaliye)
        
        self.cmb_teslim_alan = QComboBox()
        genel_layout.addRow("Teslim Alan:", self.cmb_teslim_alan)
        
        self.txt_plaka = QLineEdit()
        self.txt_plaka.setPlaceholderText("Araç plakası")
        genel_layout.addRow("Araç Plaka:", self.txt_plaka)
        
        self.txt_sofor = QLineEdit()
        genel_layout.addRow("Şoför Adı:", self.txt_sofor)
        
        self.chk_kalite = QCheckBox("Kalite Kontrol Gerekli")
        self.chk_kalite.setChecked(True)
        self.chk_kalite.setStyleSheet(f"color: {self.theme.get('text')};")
        genel_layout.addRow("", self.chk_kalite)
        
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
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._edit_satir)
        toolbar.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._delete_satir)
        toolbar.addWidget(btn_sil)
        toolbar.addStretch()
        kalem_layout.addLayout(toolbar)
        
        self.table_satirlar = QTableWidget()
        self.table_satirlar.setColumnCount(9)
        self.table_satirlar.setHorizontalHeaderLabels(["ID", "Ürün", "Miktar", "Birim", "Lot No", "Parti No", "SKT", "Sertifika", "Kalite"])
        self.table_satirlar.setColumnHidden(0, True)
        self.table_satirlar.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_satirlar.setStyleSheet(f"QTableWidget {{ background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; }}")
        header = self.table_satirlar.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_satirlar.setColumnWidth(2, 80)
        self.table_satirlar.setColumnWidth(3, 60)
        self.table_satirlar.setColumnWidth(4, 100)
        self.table_satirlar.setColumnWidth(5, 100)
        self.table_satirlar.setColumnWidth(6, 90)
        self.table_satirlar.setColumnWidth(7, 70)
        self.table_satirlar.setColumnWidth(8, 120)
        self.table_satirlar.doubleClicked.connect(self._edit_satir)
        kalem_layout.addWidget(self.table_satirlar)
        
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
        
        if self.kabul_id:
            btn_kalite = QPushButton("🔬 Kalite Kontrole Gönder")
            btn_kalite.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; padding: 10px 24px; border-radius: 6px;")
            btn_kalite.clicked.connect(self._send_to_quality)
            btn_layout.addWidget(btn_kalite)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            self.cmb_tedarikci.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, cari_kodu, unvan FROM musteri.cariler WHERE cari_tipi IN ('TEDARIKCI', 'TEDARIKCI_MUSTERI') AND aktif_mi = 1 ORDER BY cari_kodu")
            for row in cursor.fetchall():
                self.cmb_tedarikci.addItem(f"{row[1]} - {row[2]}", row[0])
            
            self.cmb_siparis.addItem("-- Siparissiz Giris --", None)
            cursor.execute("""
                SELECT s.id, s.siparis_no, FORMAT(s.tarih, 'dd.MM.yyyy'),
                       ISNULL(c.unvan, '') as tedarikci, s.durum
                FROM satinalma.siparisler s
                LEFT JOIN musteri.cariler c ON s.tedarikci_id = c.id
                WHERE s.durum IN ('TASLAK', 'ONAYLANDI', 'GONDERILDI', 'KISMI_TESLIM')
                ORDER BY s.tarih DESC
            """)
            for row in cursor.fetchall():
                self.cmb_siparis.addItem(f"{row[1]} - {row[3][:25]} ({row[2]})", row[0])
            
            self.cmb_teslim_alan.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_teslim_alan.addItem(f"{row[1]} - {row[2]}", row[0])
            
            conn.close()
        except Exception:
            pass

    def _on_siparis_changed(self, index):
        """Siparis secildiginde tedarikciyi otomatik sec ve satirlari yukle"""
        siparis_id = self.cmb_siparis.currentData()
        if not siparis_id:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Siparis tedarikcisini bul ve otomatik sec
            cursor.execute("SELECT tedarikci_id FROM satinalma.siparisler WHERE id = ?", (siparis_id,))
            row = cursor.fetchone()
            if row and row[0]:
                idx = self.cmb_tedarikci.findData(row[0])
                if idx >= 0:
                    self.cmb_tedarikci.setCurrentIndex(idx)

            # Siparis satirlarini kontrol et
            cursor.execute("SELECT COUNT(*) FROM satinalma.mal_kabul_satirlari WHERE kabul_id = ?", (self.kabul_id,))
            mevcut = cursor.fetchone()[0] if self.kabul_id else 0

            if mevcut == 0:
                cursor.execute("""
                    SELECT ss.urun_id, ss.urun_adi, ss.siparis_miktar, ss.birim,
                           ISNULL(ss.teslim_miktar, 0) as teslim_edilen,
                           ss.siparis_miktar - ISNULL(ss.teslim_miktar, 0) as kalan,
                           ss.urun_kodu
                    FROM satinalma.siparis_satirlari ss
                    WHERE ss.siparis_id = ? AND ss.siparis_miktar > ISNULL(ss.teslim_miktar, 0)
                    ORDER BY ss.satir_no
                """, (siparis_id,))
                satirlar = cursor.fetchall()

                if satirlar:
                    # Otomatik aktar
                    for satir in satirlar:
                        row_count = self.table_satirlar.rowCount()
                        self.table_satirlar.setRowCount(row_count + 1)
                        self.table_satirlar.setItem(row_count, 0, QTableWidgetItem(""))
                        urun_text = satir[1] or ""
                        if satir[6]:  # urun_kodu varsa basina ekle
                            urun_text = f"{satir[6]} - {urun_text}"
                        self.table_satirlar.setItem(row_count, 1, QTableWidgetItem(urun_text))
                        self.table_satirlar.setItem(row_count, 2, QTableWidgetItem(f"{float(satir[5]):,.0f}"))
                        self.table_satirlar.setItem(row_count, 3, QTableWidgetItem(satir[3] or "ADET"))
                        self.table_satirlar.setItem(row_count, 4, QTableWidgetItem(""))  # lot_no
                        self.table_satirlar.setItem(row_count, 5, QTableWidgetItem(""))  # parti_no
                        self.table_satirlar.setItem(row_count, 6, QTableWidgetItem(""))  # SKT
                        self.table_satirlar.setItem(row_count, 7, QTableWidgetItem("Hayir"))  # sertifika
                        self.table_satirlar.setItem(row_count, 8, QTableWidgetItem("BEKLIYOR"))  # kalite
                        self.table_satirlar.setRowHeight(row_count, 36)

                    QMessageBox.information(
                        self, "Siparis Aktarimi",
                        f"{len(satirlar)} kalem siparisindan otomatik aktarildi."
                    )

            conn.close()
        except Exception as e:
            print(f"Siparis degisim hatasi: {e}")

    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kabul_no, tarih, tedarikci_id, siparis_id, tedarikci_irsaliye_no,
                       teslim_alan_id, arac_plaka, sofor_adi, kalite_kontrol_gerekli, notlar
                FROM satinalma.mal_kabuller WHERE id = ?
            """, (self.kabul_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_kabul_no.setText(row[0] or "")
                if row[2]:
                    idx = self.cmb_tedarikci.findData(row[2])
                    if idx >= 0: self.cmb_tedarikci.setCurrentIndex(idx)
                if row[3]:
                    idx = self.cmb_siparis.findData(row[3])
                    if idx >= 0: self.cmb_siparis.setCurrentIndex(idx)
                self.txt_tedarikci_irsaliye.setText(row[4] or "")
                if row[5]:
                    idx = self.cmb_teslim_alan.findData(row[5])
                    if idx >= 0: self.cmb_teslim_alan.setCurrentIndex(idx)
                self.txt_plaka.setText(row[6] or "")
                self.txt_sofor.setText(row[7] or "")
                self.chk_kalite.setChecked(row[8] if row[8] is not None else True)
                self.txt_notlar.setPlainText(row[9] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _load_satirlar(self):
        if not self.kabul_id: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, urun_adi, teslim_miktar, birim, lot_no, parti_no,
                       FORMAT(son_kullanma_tarihi, 'dd.MM.yyyy'), sertifika_var_mi, kalite_durumu
                FROM satinalma.mal_kabul_satirlari WHERE kabul_id = ? ORDER BY satir_no
            """, (self.kabul_id,))
            rows = cursor.fetchall()
            conn.close()
            
            self.table_satirlar.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table_satirlar.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_satirlar.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                self.table_satirlar.setItem(i, 2, QTableWidgetItem(f"{row[2]:,.2f}" if row[2] else ""))
                self.table_satirlar.setItem(i, 3, QTableWidgetItem(row[3] or ""))
                self.table_satirlar.setItem(i, 4, QTableWidgetItem(row[4] or "-"))
                self.table_satirlar.setItem(i, 5, QTableWidgetItem(row[5] or "-"))
                self.table_satirlar.setItem(i, 6, QTableWidgetItem(row[6] or "-"))
                
                sertifika_item = QTableWidgetItem("✓" if row[7] else "✗")
                sertifika_item.setForeground(QColor(self.theme.get('success') if row[7] else self.theme.get('danger')))
                self.table_satirlar.setItem(i, 7, sertifika_item)
                
                kalite = row[8] or "BEKLIYOR"
                kalite_item = QTableWidgetItem(kalite)
                if kalite == "ONAYLANDI":
                    kalite_item.setForeground(QColor(self.theme.get('success')))
                elif kalite == "REDDEDILDI":
                    kalite_item.setForeground(QColor(self.theme.get('danger')))
                else:
                    kalite_item.setForeground(QColor(self.theme.get('warning')))
                self.table_satirlar.setItem(i, 8, kalite_item)
        except Exception: pass
    
    def _add_satir(self):
        if not self.kabul_id:
            QMessageBox.warning(self, "Uyarı", "Önce mal kabulu kaydedin!")
            return
        dialog = MalKabulSatirDialog(self.theme, self.kabul_id, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
    
    def _edit_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0: return
        satir_id = int(self.table_satirlar.item(row, 0).text())
        dialog = MalKabulSatirDialog(self.theme, self.kabul_id, self, satir_id)
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
                cursor.execute("DELETE FROM satinalma.mal_kabul_satirlari WHERE id = ?", (satir_id,))
                conn.commit()
                LogManager.log_delete('satinalma', 'satinalma.mal_kabul_satirlari', None, 'Kayit silindi')
                conn.close()
                self._load_satirlar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        if not self.cmb_tedarikci.currentData():
            QMessageBox.warning(self, "Uyarı", "Tedarikçi seçimi zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.kabul_id:
                cursor.execute("""
                    UPDATE satinalma.mal_kabuller SET
                        tedarikci_id = ?, siparis_id = ?, tedarikci_irsaliye_no = ?,
                        teslim_alan_id = ?, arac_plaka = ?, sofor_adi = ?,
                        kalite_kontrol_gerekli = ?, notlar = ?
                    WHERE id = ?
                """, (
                    self.cmb_tedarikci.currentData(), self.cmb_siparis.currentData(),
                    self.txt_tedarikci_irsaliye.text().strip() or None,
                    self.cmb_teslim_alan.currentData(),
                    self.txt_plaka.text().strip() or None,
                    self.txt_sofor.text().strip() or None,
                    self.chk_kalite.isChecked(),
                    self.txt_notlar.toPlainText().strip() or None,
                    self.kabul_id
                ))
            else:
                cursor.execute("SELECT 'MK-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM satinalma.mal_kabuller), 0) + 1 AS VARCHAR), 4)")
                kabul_no = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO satinalma.mal_kabuller
                    (kabul_no, tedarikci_id, siparis_id, tedarikci_irsaliye_no,
                     teslim_alan_id, arac_plaka, sofor_adi, kalite_kontrol_gerekli, notlar)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    kabul_no, self.cmb_tedarikci.currentData(), self.cmb_siparis.currentData(),
                    self.txt_tedarikci_irsaliye.text().strip() or None,
                    self.cmb_teslim_alan.currentData(),
                    self.txt_plaka.text().strip() or None,
                    self.txt_sofor.text().strip() or None,
                    self.chk_kalite.isChecked(),
                    self.txt_notlar.toPlainText().strip() or None
                ))
                self.kabul_id = cursor.fetchone()[0]
                self.txt_kabul_no.setText(kabul_no)
            
            conn.commit()
            LogManager.log_insert('satinalma', 'satinalma.mal_kabuller', None, 'Irsaliye kaydi olustu')
            conn.close()
            QMessageBox.information(self, "Başarılı", "Mal kabul kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _send_to_quality(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE satinalma.mal_kabuller SET durum = 'KALITE_KONTROLDE' WHERE id = ?", (self.kabul_id,))
            cursor.execute("UPDATE satinalma.mal_kabul_satirlari SET kalite_durumu = 'KONTROL_EDILECEK' WHERE kabul_id = ?", (self.kabul_id,))
            conn.commit()
            LogManager.log_update('satinalma', 'satinalma.mal_kabul_satirlari', None, 'Durum guncellendi')
            conn.close()
            QMessageBox.information(self, "Başarılı", "Mal kabul kalite kontrole gönderildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class MalKabulPage(BasePage):
    """Mal Kabul Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("📥 Mal Kabul (Giriş Kabul)")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Mal Kabul")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)

        toolbar_layout.addStretch()
        
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tümü", "KABUL_EDILDI", "KALITE_KONTROLDE", "ONAYLANDI", "REDDEDILDI"])
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
        self.table.setHorizontalHeaderLabels(["ID", "Kabul No", "Tarih", "Tedarikçi", "İrsaliye No", "Kalem", "Durum", "Kalite", "İşlem"])
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
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 80)
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
                SELECT mk.id, mk.kabul_no, FORMAT(mk.tarih, 'dd.MM.yyyy'), c.unvan,
                       mk.tedarikci_irsaliye_no,
                       (SELECT COUNT(*) FROM satinalma.mal_kabul_satirlari WHERE kabul_id = mk.id),
                       mk.durum, mk.kalite_kontrol_gerekli
                FROM satinalma.mal_kabuller mk
                LEFT JOIN musteri.cariler c ON mk.tedarikci_id = c.id
                ORDER BY mk.tarih DESC
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
                if j == 6:  # Durum
                    item = QTableWidgetItem(str(val) if val else "")
                    if val == "ONAYLANDI":
                        item.setForeground(QColor(self.theme.get('success')))
                    elif val == "REDDEDILDI":
                        item.setForeground(QColor(self.theme.get('danger')))
                    elif val == "KALITE_KONTROLDE":
                        item.setForeground(QColor(self.theme.get('warning')))
                elif j == 7:  # Kalite gerekli
                    item = QTableWidgetItem("Evet" if val else "Hayır")
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)

            rid = row[0]
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=rid: self._duzenle_by_id(rid), "edit"),
            ])
            self.table.setCellWidget(i, 8, widget)
            self.table.setRowHeight(i, 42)

        self.lbl_stat.setText(f"Toplam: {len(rows)} mal kabul")

    def _duzenle_by_id(self, kabul_id):
        """ID ile mal kabul düzenleme (satır butonundan)"""
        dialog = MalKabulDialog(self.theme, self, kabul_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _filter(self):
        durum = self.cmb_durum.currentText()
        if durum == "Tümü":
            self._display_data(self.all_rows)
        else:
            self._display_data([r for r in self.all_rows if r[6] == durum])
    
    def _yeni(self):
        dialog = MalKabulDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        kabul_id = int(self.table.item(row, 0).text())
        dialog = MalKabulDialog(self.theme, self, kabul_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
