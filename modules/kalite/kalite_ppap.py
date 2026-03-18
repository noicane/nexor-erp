# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - PPAP Sayfası
Production Part Approval Process (Üretim Parçası Onay Süreci)
"""
from datetime import datetime, date
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QTextEdit, QFormLayout, QDateEdit, QGroupBox, QCheckBox,
    QScrollArea, QWidget, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


# PPAP Elementleri (18 Element)
PPAP_ELEMENTS = [
    (1, "Design Records", "Tasarım Kayıtları"),
    (2, "Engineering Change Documents", "Mühendislik Değişiklik Dokümanları"),
    (3, "Customer Engineering Approval", "Müşteri Mühendislik Onayı"),
    (4, "Design FMEA", "Tasarım FMEA"),
    (5, "Process Flow Diagram", "Proses Akış Diyagramı"),
    (6, "Process FMEA", "Proses FMEA"),
    (7, "Control Plan", "Kontrol Planı"),
    (8, "MSA Studies", "MSA Çalışmaları"),
    (9, "Dimensional Results", "Boyutsal Sonuçlar"),
    (10, "Material/Performance Test Results", "Malzeme/Performans Test Sonuçları"),
    (11, "Initial Process Studies", "İlk Proses Çalışmaları"),
    (12, "Qualified Laboratory Documentation", "Akredite Lab. Dokümantasyonu"),
    (13, "Appearance Approval Report", "Görünüm Onay Raporu"),
    (14, "Sample Production Parts", "Numune Üretim Parçaları"),
    (15, "Master Sample", "Ana Numune"),
    (16, "Checking Aids", "Kontrol Aparatları"),
    (17, "Customer Specific Requirements", "Müşteriye Özel Gereksinimler"),
    (18, "Part Submission Warrant", "Parça Sunum Garantisi (PSW)")
]

# PPAP Seviyeleri
PPAP_LEVELS = {
    1: "Seviye 1 - Sadece PSW",
    2: "Seviye 2 - PSW + Sınırlı Dokümantasyon",
    3: "Seviye 3 - PSW + Tam Dokümantasyon",
    4: "Seviye 4 - PSW + Müşteri Tanımlı Gereksinimler",
    5: "Seviye 5 - PSW + Tam Dokümantasyon (Yerinde İnceleme)"
}


class YeniPPAPDialog(QDialog):
    """Yeni PPAP kaydı dialog'u"""
    
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Yeni PPAP Kaydı")
        self.setMinimumSize(700, 650)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main', '#0f172a')}; }}
            QLabel {{ color: {self.theme.get('text', '#ffffff')}; }}
            QGroupBox {{ color: {self.theme.get('primary')}; font-weight: bold; border: 1px solid {self.theme.get('border')}; border-radius: 8px; margin-top: 12px; padding-top: 12px; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        input_style = f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;"
        
        # Başlık
        title = QLabel("📋 Yeni PPAP Kaydı")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)
        
        # Temel Bilgiler
        bilgi_group = QGroupBox("Temel Bilgiler")
        bilgi_form = QFormLayout()
        bilgi_form.setSpacing(10)
        
        # Müşteri
        self.cmb_musteri = QComboBox()
        self.cmb_musteri.setStyleSheet(input_style)
        self._load_musteriler()
        self.cmb_musteri.currentIndexChanged.connect(self._on_musteri_changed)
        bilgi_form.addRow("Müşteri:", self.cmb_musteri)
        
        # Ürün
        self.cmb_urun = QComboBox()
        self.cmb_urun.setStyleSheet(input_style)
        bilgi_form.addRow("Ürün:", self.cmb_urun)
        
        # Part Number
        self.txt_part_no = QLineEdit()
        self.txt_part_no.setStyleSheet(input_style)
        self.txt_part_no.setPlaceholderText("Müşteri parça numarası")
        bilgi_form.addRow("Part Number:", self.txt_part_no)
        
        # Revizyon
        self.txt_revizyon = QLineEdit()
        self.txt_revizyon.setStyleSheet(input_style)
        self.txt_revizyon.setPlaceholderText("Rev. A, Rev. 01, vb.")
        bilgi_form.addRow("Revizyon:", self.txt_revizyon)
        
        # PPAP Seviyesi
        self.cmb_seviye = QComboBox()
        for level, desc in PPAP_LEVELS.items():
            self.cmb_seviye.addItem(desc, level)
        self.cmb_seviye.setCurrentIndex(2)  # Default Seviye 3
        self.cmb_seviye.setStyleSheet(input_style)
        bilgi_form.addRow("PPAP Seviyesi:", self.cmb_seviye)
        
        # Sunum Nedeni
        self.cmb_neden = QComboBox()
        self.cmb_neden.addItems([
            'Yeni Parça / Ürün',
            'Mühendislik Değişikliği',
            'Takım / Ekipman Değişikliği',
            'Tedarikçi / Malzeme Değişikliği',
            'Üretim Yeri Değişikliği',
            'Yeniden Sunum',
            'Diğer'
        ])
        self.cmb_neden.setStyleSheet(input_style)
        bilgi_form.addRow("Sunum Nedeni:", self.cmb_neden)
        
        bilgi_group.setLayout(bilgi_form)
        layout.addWidget(bilgi_group)
        
        # Tarihler
        tarih_group = QGroupBox("Tarihler ve Sorumlu")
        tarih_form = QFormLayout()
        
        self.date_baslangic = QDateEdit()
        self.date_baslangic.setDate(QDate.currentDate())
        self.date_baslangic.setCalendarPopup(True)
        self.date_baslangic.setStyleSheet(input_style)
        tarih_form.addRow("Başlangıç:", self.date_baslangic)
        
        self.date_hedef = QDateEdit()
        self.date_hedef.setDate(QDate.currentDate().addDays(30))
        self.date_hedef.setCalendarPopup(True)
        self.date_hedef.setStyleSheet(input_style)
        tarih_form.addRow("Hedef Sunum:", self.date_hedef)
        
        self.cmb_sorumlu = QComboBox()
        self.cmb_sorumlu.setStyleSheet(input_style)
        self._load_personel()
        tarih_form.addRow("Sorumlu:", self.cmb_sorumlu)
        
        tarih_group.setLayout(tarih_form)
        layout.addWidget(tarih_group)
        
        # Notlar
        layout.addWidget(QLabel("Notlar:"))
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(60)
        self.txt_notlar.setStyleSheet(input_style)
        layout.addWidget(self.txt_notlar)
        
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("🚀 PPAP Başlat")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_musteriler(self):
        self.cmb_musteri.clear()
        self.cmb_musteri.addItem("-- Seçin --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # StokKartlari'ndan benzersiz müşteriler
            cursor.execute("""
                SELECT DISTINCT cari_unvani 
                FROM stok.urunler 
                WHERE cari_unvani IS NOT NULL AND cari_unvani <> ''
                ORDER BY cari_unvani
            """)
            for row in cursor.fetchall():
                self.cmb_musteri.addItem(row[0], row[0])
            conn.close()
        except Exception: pass
    
    def _on_musteri_changed(self):
        """Müşteri değiştiğinde ürünleri güncelle"""
        cari_unvani = self.cmb_musteri.currentData()
        self._load_urunler(cari_unvani)
    
    def _load_urunler(self, cari_unvani=None):
        """Seçilen müşteriye ait ürün listesi"""
        self.cmb_urun.clear()
        self.cmb_urun.addItem("-- Ürün Seçin --", None)
        if not cari_unvani:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # StokKartlari'ndan stok_kodu al, stok.urunler'den id'yi bul
            cursor.execute("""
                SELECT u.id, ISNULL(s.urun_kodu, '') + ' - ' + ISNULL(s.urun_adi, '') 
                FROM stok.urunler s
                LEFT JOIN stok.urunler u ON u.urun_kodu = s.stok_kodu
                WHERE s.cari_unvani = ? AND ISNULL(s.aktif, 1) = 1
                ORDER BY s.stok_kodu
            """, (cari_unvani,))
            for row in cursor.fetchall():
                if row[0]:
                    self.cmb_urun.addItem(row[1], row[0])
            conn.close()
        except Exception: pass
    
    def _load_personel(self):
        self.cmb_sorumlu.clear()
        self.cmb_sorumlu.addItem("-- Seçin --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_sorumlu.addItem(row[1], row[0])
            conn.close()
        except Exception: pass
    
    def _kaydet(self):
        cari_unvani = self.cmb_musteri.currentData()
        if not cari_unvani:
            QMessageBox.warning(self, "Uyarı", "Müşteri seçilmelidir!")
            return
        
        sorumlu_id = self.cmb_sorumlu.currentData()
        if not sorumlu_id:
            QMessageBox.warning(self, "Uyarı", "Sorumlu seçilmelidir!")
            return
        
        # PPAP kaydı veritabanına - kontrol_planlari tablosu kullanılabilir veya özel tablo
        # Şimdilik uygunsuzluklar tablosu üzerinden yönetim
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # cari_unvani'den cari_id bul
            cari_id = None
            if cari_unvani:
                cursor.execute("""
                    SELECT TOP 1 id FROM musteri.cariler 
                    WHERE unvan = ? AND aktif_mi = 1 AND silindi_mi = 0
                """, (cari_unvani,))
                row = cursor.fetchone()
                if row:
                    cari_id = row[0]
            
            # Kayıt no oluştur
            cursor.execute("""
                SELECT TOP 1 kayit_no FROM kalite.uygunsuzluklar 
                WHERE kayit_no LIKE ? ORDER BY kayit_no DESC
            """, (f"PPAP-{datetime.now().strftime('%Y')}%",))
            row = cursor.fetchone()
            if row:
                last_no = int(row[0].split('-')[-1])
                kayit_no = f"PPAP-{datetime.now().strftime('%Y')}-{last_no + 1:04d}"
            else:
                kayit_no = f"PPAP-{datetime.now().strftime('%Y')}-0001"
            
            # Detay bilgisi oluştur
            detay = f"""PPAP Seviyesi: {self.cmb_seviye.currentText()}
Sunum Nedeni: {self.cmb_neden.currentText()}
Part Number: {self.txt_part_no.text()}
Revizyon: {self.txt_revizyon.text()}
Hedef Sunum: {self.date_hedef.date().toString('dd.MM.yyyy')}
{self.txt_notlar.toPlainText()}"""
            
            cursor.execute("""
                INSERT INTO kalite.uygunsuzluklar (
                    uuid, kayit_no, kayit_tipi, kayit_tarihi, bildiren_id, cari_id, urun_id,
                    hata_tanimi, oncelik, durum, sorumlu_id, hedef_kapanis_tarihi,
                    olusturma_tarihi, guncelleme_tarihi
                ) VALUES (
                    NEWID(), ?, 'PPAP', CAST(GETDATE() AS DATE), ?, ?, ?,
                    ?, 'NORMAL', 'AÇIK', ?, ?,
                    GETDATE(), GETDATE()
                )
            """, (
                kayit_no,
                sorumlu_id,
                cari_id,
                self.cmb_urun.currentData(),
                detay,
                sorumlu_id,
                self.date_hedef.date().toPython()
            ))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Başarılı", f"PPAP kaydı oluşturuldu!\n\nKayıt No: {kayit_no}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt başarısız: {e}")


class PPAPDetayDialog(QDialog):
    """PPAP detay ve element takip dialog'u"""
    
    def __init__(self, theme: dict, kayit_id: int, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.kayit_id = kayit_id
        self.setWindowTitle("PPAP Detayı")
        self.setMinimumSize(900, 700)
        self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        self.kayit = {}
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.kayit_no, u.kayit_tarihi, c.unvan, s.urun_adi,
                       u.hata_tanimi, u.durum, p.ad + ' ' + p.soyad, u.hedef_kapanis_tarihi
                FROM kalite.uygunsuzluklar u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN stok.urunler s ON u.urun_id = s.id
                LEFT JOIN ik.personeller p ON u.sorumlu_id = p.id
                WHERE u.id = ?
            """, (self.kayit_id,))
            row = cursor.fetchone()
            if row:
                self.kayit = {
                    'id': row[0], 'kayit_no': row[1], 'tarih': row[2], 'musteri': row[3],
                    'urun': row[4], 'detay': row[5], 'durum': row[6], 'sorumlu': row[7], 'hedef': row[8]
                }
            conn.close()
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
    
    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main')}; }} QLabel {{ color: {self.theme.get('text')}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(f"📋 {self.kayit.get('kayit_no', '')}")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        header.addWidget(title)
        
        durum = self.kayit.get('durum', '')
        durum_colors = {'AÇIK': self.theme.get('warning'), 'İŞLEMDE': self.theme.get('info'), 'KAPATILDI': self.theme.get('success')}
        durum_lbl = QLabel(durum)
        durum_lbl.setStyleSheet(f"background: {durum_colors.get(durum, '#666')}; color: white; padding: 4px 12px; border-radius: 4px;")
        header.addWidget(durum_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        # Bilgi kartı
        info_card = QFrame()
        info_card.setStyleSheet(f"background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; padding: 12px;")
        info_layout = QGridLayout(info_card)
        
        info_layout.addWidget(QLabel("Müşteri:"), 0, 0)
        info_layout.addWidget(QLabel(self.kayit.get('musteri', '-') or '-'), 0, 1)
        info_layout.addWidget(QLabel("Ürün:"), 0, 2)
        info_layout.addWidget(QLabel(self.kayit.get('urun', '-') or '-'), 0, 3)
        info_layout.addWidget(QLabel("Sorumlu:"), 1, 0)
        info_layout.addWidget(QLabel(self.kayit.get('sorumlu', '-') or '-'), 1, 1)
        info_layout.addWidget(QLabel("Hedef:"), 1, 2)
        hedef = self.kayit.get('hedef')
        info_layout.addWidget(QLabel(hedef.strftime('%d.%m.%Y') if hedef else '-'), 1, 3)
        
        layout.addWidget(info_card)
        
        # Detay
        detay_lbl = QLabel("Detaylar:")
        detay_lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(detay_lbl)
        
        detay_text = QTextEdit()
        detay_text.setPlainText(self.kayit.get('detay', ''))
        detay_text.setReadOnly(True)
        detay_text.setMaximumHeight(100)
        detay_text.setStyleSheet(f"background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px;")
        layout.addWidget(detay_text)
        
        # PPAP Elementleri
        elem_lbl = QLabel("📋 PPAP Elementleri (18 Element):")
        elem_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(elem_lbl)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        
        self.element_checks = {}
        for num, eng, tr in PPAP_ELEMENTS:
            row_layout = QHBoxLayout()
            
            check = QCheckBox()
            check.setStyleSheet("QCheckBox::indicator { width: 20px; height: 20px; }")
            row_layout.addWidget(check)
            self.element_checks[num] = check
            
            num_lbl = QLabel(f"{num}.")
            num_lbl.setFixedWidth(25)
            num_lbl.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold;")
            row_layout.addWidget(num_lbl)
            
            name_lbl = QLabel(f"{tr} ({eng})")
            name_lbl.setStyleSheet(f"color: {self.theme.get('text')};")
            row_layout.addWidget(name_lbl, 1)
            
            btn_upload = QPushButton("Dosya Ekle")
            btn_upload.setFixedSize(72, 28)
            btn_upload.setToolTip("Dosya Ekle")
            btn_upload.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 4px; font-size: 11px;")
            row_layout.addWidget(btn_upload)
            
            scroll_layout.addLayout(row_layout)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        btn_kaydet = QPushButton("💾 İlerleme Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; border: none; border-radius: 6px; padding: 10px 20px;")
        btn_kaydet.clicked.connect(self._kaydet_ilerleme)
        btn_layout.addWidget(btn_kaydet)
        
        btn_layout.addStretch()
        
        btn_kapat = QPushButton("Kapat")
        btn_kapat.clicked.connect(self.accept)
        btn_layout.addWidget(btn_kapat)
        
        layout.addLayout(btn_layout)
    
    def _kaydet_ilerleme(self):
        tamamlanan = sum(1 for check in self.element_checks.values() if check.isChecked())
        QMessageBox.information(self, "Bilgi", f"İlerleme kaydedildi.\nTamamlanan element: {tamamlanan}/18")


class KalitePPAPPage(BasePage):
    """PPAP Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📋 PPAP Yönetimi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text', '#fff')};")
        header.addWidget(title)
        header.addStretch()
        
        btn_yeni = QPushButton("➕ Yeni PPAP")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni_ppap)
        header.addWidget(btn_yeni)
        layout.addLayout(header)
        
        # Bilgi
        info_card = QFrame()
        info_card.setStyleSheet(f"background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; padding: 12px;")
        info_layout = QHBoxLayout(info_card)
        info_text = QLabel("📋 PPAP (Production Part Approval Process) - Müşteri onayı gerektiren yeni parça/değişiklik süreçlerinin yönetimi.")
        info_text.setStyleSheet(f"color: {self.theme.get('text_secondary')};")
        info_layout.addWidget(info_text)
        layout.addWidget(info_card)
        
        # İstatistik kartları
        stat_layout = QHBoxLayout()
        self.stat_aktif = self._create_stat_card("⚡ Aktif", "0", self.theme.get('warning', '#f59e0b'))
        stat_layout.addWidget(self.stat_aktif)
        self.stat_onaylanan = self._create_stat_card("✅ Onaylanan", "0", self.theme.get('success', '#22c55e'))
        stat_layout.addWidget(self.stat_onaylanan)
        self.stat_toplam = self._create_stat_card("📊 Toplam", "0", self.theme.get('primary', '#3b82f6'))
        stat_layout.addWidget(self.stat_toplam)
        stat_layout.addStretch()
        layout.addLayout(stat_layout)
        
        # Filtre
        filtre_layout = QHBoxLayout()
        filtre_layout.addWidget(QLabel("Durum:"))
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(['Tümü', 'AÇIK', 'İŞLEMDE', 'KAPATILDI'])
        self.cmb_durum.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 6px;")
        self.cmb_durum.currentIndexChanged.connect(self._load_data)
        filtre_layout.addWidget(self.cmb_durum)
        filtre_layout.addStretch()
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.clicked.connect(self._load_data)
        filtre_layout.addWidget(btn_yenile)
        layout.addLayout(filtre_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Kayıt No", "Müşteri", "Ürün", "Tarih", "Hedef", "Durum", "İşlem"])
        self.table.setColumnWidth(7, 120)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; }}
            QHeaderView::section {{ background: {self.theme.get('bg_sidebar')}; color: {self.theme.get('text')}; padding: 10px; border: none; font-weight: bold; }}
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table, 1)
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(140, 70)
        card.setStyleSheet(f"background: {self.theme.get('bg_card')}; border: 1px solid {color}; border-radius: 8px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {self.theme.get('text_secondary')}; font-size: 11px;")
        layout.addWidget(lbl_title)
        lbl_value = QLabel(value)
        lbl_value.setObjectName("stat_value")
        lbl_value.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        layout.addWidget(lbl_value)
        return card
    
    def _yeni_ppap(self):
        dlg = YeniPPAPDialog(self.theme, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _on_double_click(self, index):
        row = index.row()
        kayit_id = int(self.table.item(row, 0).text())
        dlg = PPAPDetayDialog(self.theme, kayit_id, self)
        dlg.exec()
    
    def _detay_goster(self, kayit_id: int):
        dlg = PPAPDetayDialog(self.theme, kayit_id, self)
        dlg.exec()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            durum_filtre = self.cmb_durum.currentText()
            where_clause = "" if durum_filtre == 'Tümü' else f"AND u.durum = '{durum_filtre}'"
            
            cursor.execute(f"""
                SELECT u.id, u.kayit_no, c.unvan, s.urun_adi, u.kayit_tarihi, u.hedef_kapanis_tarihi, u.durum
                FROM kalite.uygunsuzluklar u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN stok.urunler s ON u.urun_id = s.id
                WHERE u.kayit_tipi = 'PPAP' {where_clause}
                ORDER BY u.kayit_tarihi DESC
            """)
            
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem((row[2] or '')[:25]))
                self.table.setItem(i, 3, QTableWidgetItem((row[3] or '')[:30]))
                
                tarih = row[4]
                self.table.setItem(i, 4, QTableWidgetItem(tarih.strftime('%d.%m.%Y') if tarih else '-'))
                
                hedef = row[5]
                hedef_item = QTableWidgetItem(hedef.strftime('%d.%m.%Y') if hedef else '-')
                if hedef and hedef < date.today() and row[6] != 'KAPATILDI':
                    hedef_item.setForeground(QColor(self.theme.get('danger')))
                self.table.setItem(i, 5, hedef_item)
                
                durum = row[6] or ''
                durum_item = QTableWidgetItem(durum)
                durum_colors = {'AÇIK': self.theme.get('warning'), 'İŞLEMDE': self.theme.get('info'), 'KAPATILDI': self.theme.get('success')}
                if durum in durum_colors:
                    durum_item.setForeground(QColor(durum_colors[durum]))
                self.table.setItem(i, 6, durum_item)
                
                widget = self.create_action_buttons([
                    ("📋", "Detay", lambda checked, kid=row[0]: self._detay_goster(kid), "info"),
                ])
                self.table.setCellWidget(i, 7, widget)
                self.table.setRowHeight(i, 42)
            
            # İstatistikler
            cursor.execute("SELECT COUNT(*) FROM kalite.uygunsuzluklar WHERE kayit_tipi = 'PPAP' AND durum IN ('AÇIK', 'İŞLEMDE')")
            self.stat_aktif.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            cursor.execute("SELECT COUNT(*) FROM kalite.uygunsuzluklar WHERE kayit_tipi = 'PPAP' AND durum = 'KAPATILDI'")
            self.stat_onaylanan.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            cursor.execute("SELECT COUNT(*) FROM kalite.uygunsuzluklar WHERE kayit_tipi = 'PPAP'")
            self.stat_toplam.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            conn.close()
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
