# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Red Kayıtları / Uygunsuzluk Yönetimi Sayfası
Müşteri şikayeti, iç red, tedarikçi red kayıtları
"""
from datetime import datetime, date
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QTextEdit, QGridLayout, QGroupBox, QFormLayout,
    QDoubleSpinBox, QDateEdit, QTabWidget, QWidget, QSplitter,
    QInputDialog, QRadioButton, QButtonGroup, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.hareket_motoru import HareketMotoru
from dialogs.login import ModernLoginDialog


# ============================================================================
# RED DEPOT KARAR DIALOG
# ============================================================================

class RedKararDialog(QDialog):
    """Red depot kararı dialog'u - Tablo bazlı, satıra tıkla karar ver"""
    
    def __init__(self, theme: dict, red_kayit: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.red_kayit = red_kayit
        self.max_miktar = int(red_kayit.get('red_miktar', 0) or 0)
        self.setWindowTitle("🔴 Red Depot Karar")
        self.setMinimumSize(600, 450)
        self.karar_data = None
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main', '#1a1f2e')}; }}
            QLabel {{ color: {self.theme.get('text', '#fff')}; }}
            QGroupBox {{ 
                color: {self.theme.get('primary', '#6366f1')}; 
                font-weight: bold; 
                border: 1px solid {self.theme.get('border', '#3d4454')}; 
                border-radius: 8px; 
                margin-top: 12px; 
                padding-top: 8px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 8px; }}
            QComboBox, QSpinBox {{ 
                background: {self.theme.get('bg_input', '#1e293b')}; 
                color: {self.theme.get('text', '#fff')}; 
                border: 1px solid {self.theme.get('border', '#3d4454')}; 
                border-radius: 4px; 
                padding: 4px 8px;
                min-width: 100px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Başlık
        header = QHBoxLayout()
        title = QLabel("🔴 Red Depot Karar Verme")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary', '#6366f1')};")
        header.addWidget(title)
        header.addStretch()
        
        # Lot ve Ürün bilgisi
        lot_info = QLabel(f"📦 {self.red_kayit.get('lot_no', '-')} | {(self.red_kayit.get('urun_adi') or '-')[:30]}")
        lot_info.setStyleSheet(f"color: {self.theme.get('text_secondary', '#94a3b8')};")
        header.addWidget(lot_info)
        layout.addLayout(header)
        
        # Bilgi satırı
        info_layout = QHBoxLayout()
        
        musteri = self.red_kayit.get('musteri') or '-'
        musteri_lbl = QLabel(f"👤 {musteri[:25]}")
        info_layout.addWidget(musteri_lbl)
        
        hata_turu = self.red_kayit.get('hata_turu_adi') or '-'
        hata_lbl = QLabel(f"⚠️ Hata: {hata_turu}")
        hata_lbl.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-weight: bold;")
        info_layout.addWidget(hata_lbl)
        
        info_layout.addStretch()
        
        miktar_lbl = QLabel(f"🔢 Toplam: {self.max_miktar} adet")
        miktar_lbl.setStyleSheet(f"color: {self.theme.get('danger', '#ef4444')}; font-weight: bold;")
        info_layout.addWidget(miktar_lbl)
        
        layout.addLayout(info_layout)
        
        # Karar Tablosu
        karar_group = QGroupBox("⚖️ Karar Ver")
        karar_layout = QVBoxLayout(karar_group)
        
        # Tablo - Miktar ve Karar seçimi
        self.karar_table = QTableWidget()
        self.karar_table.setColumnCount(4)
        self.karar_table.setHorizontalHeaderLabels(["Hata Türü", "Miktar", "Karar", "Açıklama"])
        self.karar_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.karar_table.setColumnWidth(1, 120)
        self.karar_table.setColumnWidth(2, 150)
        self.karar_table.setColumnWidth(3, 150)
        self.karar_table.verticalHeader().setVisible(False)
        self.karar_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.karar_table.setStyleSheet(f"""
            QTableWidget {{ 
                background: {self.theme.get('bg_card', '#1e293b')}; 
                color: {self.theme.get('text', '#fff')}; 
                gridline-color: {self.theme.get('border', '#3d4454')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
            }}
            QTableWidget::item {{ padding: 8px; }}
            QHeaderView::section {{ 
                background: {self.theme.get('bg_input', '#1e293b')}; 
                color: {self.theme.get('text', '#fff')}; 
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
        """)
        
        # Tek satır ekle (mevcut red kaydı için)
        self.karar_table.setRowCount(1)
        self.karar_table.setRowHeight(0, 45)
        
        # Hata Türü
        hata_item = QTableWidgetItem(hata_turu)
        hata_item.setFlags(hata_item.flags() & ~Qt.ItemIsEditable)
        self.karar_table.setItem(0, 0, hata_item)
        
        # Miktar (SpinBox)
        self.spn_miktar = QSpinBox()
        self.spn_miktar.setRange(1, self.max_miktar)
        self.spn_miktar.setValue(self.max_miktar)
        self.spn_miktar.valueChanged.connect(self._miktar_degisti)
        self.karar_table.setCellWidget(0, 1, self.spn_miktar)
        
        # Karar (ComboBox)
        self.cmb_karar = QComboBox()
        self.cmb_karar.addItem("🔧 SÖKÜM", "SOKUM")
        self.cmb_karar.addItem("✅ KABUL", "KABUL")
        self.cmb_karar.addItem("⏳ MÜŞTERİ ONAYI", "MUSTERI_ONAY")
        self.karar_table.setCellWidget(0, 2, self.cmb_karar)
        
        # Açıklama
        self.txt_aciklama = QLineEdit()
        self.txt_aciklama.setPlaceholderText("Not...")
        self.txt_aciklama.setStyleSheet(f"""
            background: {self.theme.get('bg_input', '#1e293b')}; 
            color: {self.theme.get('text', '#fff')}; 
            border: 1px solid {self.theme.get('border', '#3d4454')}; 
            border-radius: 4px; 
            padding: 4px 8px;
        """)
        self.karar_table.setCellWidget(0, 3, self.txt_aciklama)
        
        karar_layout.addWidget(self.karar_table)
        
        # Kalan miktar bilgisi
        self.lbl_kalan = QLabel("")
        self.lbl_kalan.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-size: 12px;")
        karar_layout.addWidget(self.lbl_kalan)
        
        layout.addWidget(karar_group)
        
        # Karar açıklamaları
        aciklama_frame = QFrame()
        aciklama_frame.setStyleSheet(f"background: {self.theme.get('bg_card', '#1e293b')}; border-radius: 6px; padding: 8px;")
        aciklama_layout = QVBoxLayout(aciklama_frame)
        aciklama_layout.setSpacing(4)
        
        lbl1 = QLabel("🔧 SÖKÜM → XI deposuna gönderilir, kaplama sökülür")
        lbl1.setStyleSheet(f"color: {self.theme.get('text_secondary', '#94a3b8')}; font-size: 11px;")
        aciklama_layout.addWidget(lbl1)
        
        lbl2 = QLabel("✅ KABUL → FKK'ya geri döner, tekrar kontrol edilir")
        lbl2.setStyleSheet(f"color: {self.theme.get('text_secondary', '#94a3b8')}; font-size: 11px;")
        aciklama_layout.addWidget(lbl2)
        
        lbl3 = QLabel("⏳ MÜŞTERİ ONAYI → Karantinaya alınır, müşteri kararı beklenir")
        lbl3.setStyleSheet(f"color: {self.theme.get('text_secondary', '#94a3b8')}; font-size: 11px;")
        aciklama_layout.addWidget(lbl3)
        
        layout.addWidget(aciklama_frame)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"""
            background: {self.theme.get('bg_input', '#1e293b')}; 
            color: {self.theme.get('text', '#fff')}; 
            border: 1px solid {self.theme.get('border', '#3d4454')}; 
            border-radius: 6px; 
            padding: 10px 24px;
            font-weight: bold;
        """)
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_onayla = QPushButton("✓ Kararı Uygula")
        btn_onayla.setStyleSheet(f"""
            background: {self.theme.get('success', '#22c55e')}; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            padding: 10px 24px;
            font-weight: bold;
            font-size: 14px;
        """)
        btn_onayla.clicked.connect(self._onayla)
        btn_layout.addWidget(btn_onayla)
        
        layout.addLayout(btn_layout)
    
    def _miktar_degisti(self, value):
        """Miktar değiştiğinde kalan bilgisini güncelle"""
        kalan = self.max_miktar - value
        if kalan > 0:
            self.lbl_kalan.setText(f"⚠️ {kalan} adet RED deposunda kalacak")
        else:
            self.lbl_kalan.setText("")
    
    def _onayla(self):
        """Kararı onayla"""
        karar_tip = self.cmb_karar.currentData()
        islem_miktar = self.spn_miktar.value()
        
        if islem_miktar <= 0:
            QMessageBox.warning(self, "Uyarı", "İşlem miktarı 0'dan büyük olmalı!")
            return
        
        self.karar_data = {
            'tip': karar_tip,
            'miktar': islem_miktar,
            'kalan_miktar': self.max_miktar - islem_miktar,
            'not': self.txt_aciklama.text().strip(),
            'red_kayit': self.red_kayit
        }
        
        self.accept()
    
    def get_karar(self):
        """Karar verisini al"""
        return self.karar_data


# ============================================================================
# UYGUNSUZLUK DIALOG (MEVCUT)
# ============================================================================

class UygunsuzlukDialog(QDialog):
    """Yeni uygunsuzluk kaydı dialog'u"""
    
    def __init__(self, theme: dict, kayit_tipi: str = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.kayit_tipi = kayit_tipi
        self.setWindowTitle("Yeni Uygunsuzluk Kaydı")
        self.setMinimumSize(700, 650)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main', '#0f172a')}; }}
            QLabel {{ color: {self.theme.get('text', '#ffffff')}; }}
            QGroupBox {{ 
                color: {self.theme.get('primary', '#3b82f6')}; 
                font-weight: bold; 
                border: 1px solid {self.theme.get('border')}; 
                border-radius: 8px; 
                margin-top: 12px; 
                padding-top: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        title = QLabel("📋 Yeni Uygunsuzluk Kaydı")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)
        
        # Kayıt Tipi
        tip_group = QGroupBox("Kayıt Tipi")
        tip_layout = QHBoxLayout()
        
        self.cmb_kayit_tipi = QComboBox()
        self.cmb_kayit_tipi.addItems([
            'MÜŞTERİ_ŞİKAYETİ',
            'İÇ_RED',
            'TEDARİKÇİ_RED',
            'PROSES_RED',
            'DENETİM_BULGUSU'
        ])
        if self.kayit_tipi:
            idx = self.cmb_kayit_tipi.findText(self.kayit_tipi)
            if idx >= 0:
                self.cmb_kayit_tipi.setCurrentIndex(idx)
        self.cmb_kayit_tipi.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        tip_layout.addWidget(self.cmb_kayit_tipi)
        
        self.cmb_oncelik = QComboBox()
        self.cmb_oncelik.addItems(['DÜŞÜK', 'NORMAL', 'YÜKSEK', 'KRİTİK'])
        self.cmb_oncelik.setCurrentText('NORMAL')
        self.cmb_oncelik.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        tip_layout.addWidget(QLabel("Öncelik:"))
        tip_layout.addWidget(self.cmb_oncelik)
        
        tip_group.setLayout(tip_layout)
        layout.addWidget(tip_group)
        
        # Temel Bilgiler
        bilgi_group = QGroupBox("Temel Bilgiler")
        bilgi_form = QFormLayout()
        bilgi_form.setSpacing(10)
        
        # Bildiren
        self.cmb_bildiren = QComboBox()
        self.cmb_bildiren.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self._load_personel()
        bilgi_form.addRow("Bildiren:", self.cmb_bildiren)
        
        # Müşteri/Tedarikçi
        self.cmb_cari = QComboBox()
        self.cmb_cari.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self._load_cariler()
        self.cmb_cari.currentIndexChanged.connect(self._on_cari_changed)
        bilgi_form.addRow("Müşteri/Tedarikçi:", self.cmb_cari)
        
        # Ürün
        self.cmb_urun = QComboBox()
        self.cmb_urun.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        bilgi_form.addRow("Ürün:", self.cmb_urun)
        
        # Lot No
        self.txt_lot = QLineEdit()
        self.txt_lot.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self.txt_lot.setPlaceholderText("Lot numarası")
        bilgi_form.addRow("Lot No:", self.txt_lot)
        
        # Etkilenen Miktar
        miktar_layout = QHBoxLayout()
        self.txt_miktar = QDoubleSpinBox()
        self.txt_miktar.setRange(0, 9999999)
        self.txt_miktar.setDecimals(2)
        self.txt_miktar.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        miktar_layout.addWidget(self.txt_miktar)
        miktar_layout.addWidget(QLabel("Adet"))
        bilgi_form.addRow("Etkilenen Miktar:", miktar_layout)
        
        # Tespit Yeri
        self.txt_tespit_yeri = QLineEdit()
        self.txt_tespit_yeri.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self.txt_tespit_yeri.setPlaceholderText("Ör: Final Kontrol, Müşteri Sahası, Giriş Kalite")
        bilgi_form.addRow("Tespit Yeri:", self.txt_tespit_yeri)
        
        bilgi_group.setLayout(bilgi_form)
        layout.addWidget(bilgi_group)
        
        # Hata Tanımı
        hata_group = QGroupBox("Hata Detayları")
        hata_layout = QVBoxLayout()
        
        # Hata Türü
        hata_tur_layout = QHBoxLayout()
        hata_tur_layout.addWidget(QLabel("Hata Türü:"))
        self.cmb_hata_turu = QComboBox()
        self.cmb_hata_turu.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self._load_hata_turleri()
        hata_tur_layout.addWidget(self.cmb_hata_turu, 1)
        hata_layout.addLayout(hata_tur_layout)
        
        hata_layout.addWidget(QLabel("Hata Tanımı:"))
        self.txt_hata_tanimi = QTextEdit()
        self.txt_hata_tanimi.setMaximumHeight(100)
        self.txt_hata_tanimi.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self.txt_hata_tanimi.setPlaceholderText("Hatanın detaylı açıklaması...")
        hata_layout.addWidget(self.txt_hata_tanimi)
        
        hata_group.setLayout(hata_layout)
        layout.addWidget(hata_group)
        
        # Sorumlu ve Tarih
        sorumluluk_layout = QHBoxLayout()
        
        sorumluluk_layout.addWidget(QLabel("Sorumlu:"))
        self.cmb_sorumlu = QComboBox()
        self.cmb_sorumlu.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self._load_personel_sorumlu()
        sorumluluk_layout.addWidget(self.cmb_sorumlu)
        
        sorumluluk_layout.addWidget(QLabel("Hedef Kapanış:"))
        self.date_hedef = QDateEdit()
        self.date_hedef.setDate(QDate.currentDate().addDays(7))
        self.date_hedef.setCalendarPopup(True)
        self.date_hedef.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        sorumluluk_layout.addWidget(self.date_hedef)
        
        layout.addLayout(sorumluluk_layout)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 24px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_personel(self):
        """Personel listesi"""
        self.cmb_bildiren.clear()
        self.cmb_bildiren.addItem("-- Seçin --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_bildiren.addItem(row[1], row[0])
            conn.close()
        except Exception as e:
            print(f"Personel yükleme hatası: {e}")
    
    def _load_personel_sorumlu(self):
        """Sorumlu personel listesi"""
        self.cmb_sorumlu.clear()
        self.cmb_sorumlu.addItem("-- Seçin --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_sorumlu.addItem(row[1], row[0])
            conn.close()
        except Exception as e:
            print(f"Personel yükleme hatası: {e}")
    
    def _load_cariler(self):
        """Cari listesi - StokKartlari'nda ürünü olan müşteriler"""
        self.cmb_cari.clear()
        self.cmb_cari.addItem("-- Müşteri/Tedarikçi Seçin --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # StokKartlari'ndan benzersiz müşteri listesi (unvan olarak)
            cursor.execute("""
                SELECT DISTINCT cari_unvani 
                FROM stok.urunler 
                WHERE cari_unvani IS NOT NULL AND cari_unvani <> ''
                ORDER BY cari_unvani
            """)
            for row in cursor.fetchall():
                # Data olarak unvanı tut (ürün filtrelemede kullanılacak)
                self.cmb_cari.addItem(row[0], row[0])
            conn.close()
        except Exception as e:
            print(f"Cari yükleme hatası: {e}")
    
    def _on_cari_changed(self):
        """Cari değiştiğinde ürünleri güncelle"""
        cari_id = self.cmb_cari.currentData()
        self._load_urunler(cari_id)
    
    def _load_urunler(self, cari_unvani=None):
        """Ürün listesi - seçilen müşteriye ait ürünler"""
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
            rows = cursor.fetchall()
            print(f"Müşteriye ait ürün sayısı: {len(rows)}")
            for row in rows:
                # u.id NULL olabilir, o zaman stok.urunler'de yok demektir
                if row[0]:
                    self.cmb_urun.addItem(row[1], row[0])
                else:
                    # stok.urunler'de yoksa stok_kodu'nu data olarak kullan (sonra handle edilir)
                    self.cmb_urun.addItem(row[1], None)
            conn.close()
        except Exception as e:
            print(f"Ürün yükleme hatası: {e}")
    
    def _load_hata_turleri(self):
        """Hata türleri"""
        self.cmb_hata_turu.clear()
        self.cmb_hata_turu.addItem("-- Seçin --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod + ' - ' + ad FROM tanim.hata_turleri WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_hata_turu.addItem(row[1], row[0])
            conn.close()
        except Exception as e:
            print(f"Hata türleri yükleme hatası: {e}")
    
    def _kaydet(self):
        """Kaydı kaydet"""
        bildiren_id = self.cmb_bildiren.currentData()
        if not bildiren_id:
            QMessageBox.warning(self, "Uyarı", "Bildiren kişi seçilmelidir!")
            return
        
        hata_tanimi = self.txt_hata_tanimi.toPlainText().strip()
        if not hata_tanimi:
            QMessageBox.warning(self, "Uyarı", "Hata tanımı girilmelidir!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # cari_unvani'den cari_id bul
            cari_unvani = self.cmb_cari.currentData()
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
            """, (f"NCR-{datetime.now().strftime('%Y%m')}%",))
            row = cursor.fetchone()
            if row:
                last_no = int(row[0].split('-')[-1])
                kayit_no = f"NCR-{datetime.now().strftime('%Y%m')}-{last_no + 1:04d}"
            else:
                kayit_no = f"NCR-{datetime.now().strftime('%Y%m')}-0001"
            
            cursor.execute("""
                INSERT INTO kalite.uygunsuzluklar (
                    uuid, kayit_no, kayit_tipi, kayit_tarihi, bildiren_id, cari_id, urun_id,
                    lot_no, etkilenen_miktar, hata_turu_id, hata_tanimi, tespit_yeri,
                    oncelik, durum, sorumlu_id, hedef_kapanis_tarihi,
                    olusturma_tarihi, guncelleme_tarihi
                ) VALUES (
                    NEWID(), ?, ?, CAST(GETDATE() AS DATE), ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, 'AÇIK', ?, ?,
                    GETDATE(), GETDATE()
                )
            """, (
                kayit_no,
                self.cmb_kayit_tipi.currentText(),
                bildiren_id,
                cari_id,
                self.cmb_urun.currentData(),
                self.txt_lot.text() or None,
                self.txt_miktar.value() if self.txt_miktar.value() > 0 else None,
                self.cmb_hata_turu.currentData(),
                hata_tanimi,
                self.txt_tespit_yeri.text() or None,
                self.cmb_oncelik.currentText(),
                self.cmb_sorumlu.currentData(),
                self.date_hedef.date().toPython()
            ))
            
            conn.commit()
            LogManager.log_insert('kalite', 'kalite.uygunsuzluklar', None, 'Uygunsuzluk kaydi olustu')
            conn.close()
            
            QMessageBox.information(self, "Başarılı", f"Uygunsuzluk kaydı oluşturuldu!\n\nKayıt No: {kayit_no}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt başarısız: {e}")


class UygunsuzlukDetayDialog(QDialog):
    """Uygunsuzluk detay ve aksiyon yönetimi dialog'u"""
    
    def __init__(self, theme: dict, kayit_id: int, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.kayit_id = kayit_id
        self.setWindowTitle("Uygunsuzluk Detayı")
        self.setMinimumSize(900, 700)
        self._load_kayit()
        self._setup_ui()
    
    def _load_kayit(self):
        """Kayıt bilgilerini yükle"""
        self.kayit = {}
        self.aksiyonlar = []
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.kayit_no, u.kayit_tipi, u.kayit_tarihi, 
                       p1.ad + ' ' + p1.soyad as bildiren,
                       c.unvan, s.urun_kodu + ' - ' + s.urun_adi as urun,
                       u.lot_no, u.etkilenen_miktar, u.hata_tanimi, u.tespit_yeri,
                       u.oncelik, u.durum, p2.ad + ' ' + p2.soyad as sorumlu,
                       u.hedef_kapanis_tarihi, u.kapanis_tarihi, u.maliyet,
                       ht.ad as hata_turu
                FROM kalite.uygunsuzluklar u
                LEFT JOIN ik.personeller p1 ON u.bildiren_id = p1.id
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN stok.urunler s ON u.urun_id = s.id
                LEFT JOIN ik.personeller p2 ON u.sorumlu_id = p2.id
                LEFT JOIN tanim.hata_turleri ht ON u.hata_turu_id = ht.id
                WHERE u.id = ?
            """, (self.kayit_id,))
            
            row = cursor.fetchone()
            if row:
                self.kayit = {
                    'id': row[0], 'kayit_no': row[1], 'kayit_tipi': row[2],
                    'kayit_tarihi': row[3], 'bildiren': row[4], 'cari': row[5],
                    'urun': row[6], 'lot_no': row[7], 'miktar': row[8],
                    'hata_tanimi': row[9], 'tespit_yeri': row[10], 'oncelik': row[11],
                    'durum': row[12], 'sorumlu': row[13], 'hedef_kapanis': row[14],
                    'kapanis_tarihi': row[15], 'maliyet': row[16], 'hata_turu': row[17]
                }
            
            # Aksiyonları yükle
            cursor.execute("""
                SELECT a.id, a.aksiyon_tipi, a.d_adimi, a.aciklama, 
                       p.ad + ' ' + p.soyad as sorumlu, a.hedef_tarih,
                       a.tamamlanma_tarihi, a.durum
                FROM kalite.uygunsuzluk_aksiyonlar a
                LEFT JOIN ik.personeller p ON a.sorumlu_id = p.id
                WHERE a.uygunsuzluk_id = ?
                ORDER BY a.d_adimi, a.olusturma_tarihi
            """, (self.kayit_id,))
            
            for row in cursor.fetchall():
                self.aksiyonlar.append({
                    'id': row[0], 'tip': row[1], 'd_adimi': row[2],
                    'aciklama': row[3], 'sorumlu': row[4], 'hedef': row[5],
                    'tamamlanma': row[6], 'durum': row[7]
                })
            
            conn.close()
        except Exception as e:
            print(f"Kayıt yükleme hatası: {e}")
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main', '#0f172a')}; }}
            QLabel {{ color: {self.theme.get('text', '#ffffff')}; }}
            QGroupBox {{ 
                color: {self.theme.get('primary', '#3b82f6')}; 
                font-weight: bold; 
                border: 1px solid {self.theme.get('border')}; 
                border-radius: 8px; 
                margin-top: 12px; 
                padding-top: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        header = QHBoxLayout()
        title = QLabel(f"📋 {self.kayit.get('kayit_no', '')}")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        header.addWidget(title)
        
        durum = self.kayit.get('durum', '')
        durum_colors = {
            'AÇIK': self.theme.get('warning', '#f59e0b'),
            'İŞLEMDE': self.theme.get('info', '#06b6d4'),
            'KAPATILDI': self.theme.get('success', '#22c55e'),
            'İPTAL': self.theme.get('text_secondary', '#94a3b8')
        }
        durum_lbl = QLabel(durum)
        durum_lbl.setStyleSheet(f"background: {durum_colors.get(durum, '#666')}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;")
        header.addWidget(durum_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {self.theme.get('border')}; border-radius: 8px; }}
            QTabBar::tab {{ 
                background: {self.theme.get('bg_card')}; 
                color: {self.theme.get('text')}; 
                padding: 10px 20px; 
                border: 1px solid {self.theme.get('border')}; 
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{ background: {self.theme.get('primary')}; color: white; }}
        """)
        
        # Tab 1 - Detay
        detay_widget = QWidget()
        detay_layout = QVBoxLayout(detay_widget)
        
        # Bilgi grid
        info_grid = QGridLayout()
        info_grid.setSpacing(10)
        
        labels = [
            ("Kayıt Tipi:", self.kayit.get('kayit_tipi', '')),
            ("Tarih:", str(self.kayit.get('kayit_tarihi', ''))),
            ("Bildiren:", self.kayit.get('bildiren', '')),
            ("Müşteri/Tedarikçi:", self.kayit.get('cari', '') or '-'),
            ("Ürün:", self.kayit.get('urun', '') or '-'),
            ("Lot No:", self.kayit.get('lot_no', '') or '-'),
            ("Etkilenen Miktar:", str(self.kayit.get('miktar', 0) or 0)),
            ("Tespit Yeri:", self.kayit.get('tespit_yeri', '') or '-'),
            ("Hata Türü:", self.kayit.get('hata_turu', '') or '-'),
            ("Öncelik:", self.kayit.get('oncelik', '')),
            ("Sorumlu:", self.kayit.get('sorumlu', '') or '-'),
            ("Hedef Kapanış:", str(self.kayit.get('hedef_kapanis', '') or '-'))
        ]
        
        row = 0
        col = 0
        for label, value in labels:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {self.theme.get('text_secondary')}; font-weight: bold;")
            info_grid.addWidget(lbl, row, col)
            
            val = QLabel(str(value))
            val.setStyleSheet(f"color: {self.theme.get('text')};")
            info_grid.addWidget(val, row, col + 1)
            
            col += 2
            if col >= 4:
                col = 0
                row += 1
        
        detay_layout.addLayout(info_grid)
        
        # Hata tanımı
        detay_layout.addWidget(QLabel("Hata Tanımı:"))
        hata_text = QTextEdit()
        hata_text.setPlainText(self.kayit.get('hata_tanimi', ''))
        hata_text.setReadOnly(True)
        hata_text.setMaximumHeight(100)
        hata_text.setStyleSheet(f"background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        detay_layout.addWidget(hata_text)
        
        detay_layout.addStretch()
        tabs.addTab(detay_widget, "📄 Detay")
        
        # Tab 2 - Aksiyonlar
        aksiyon_widget = QWidget()
        aksiyon_layout = QVBoxLayout(aksiyon_widget)
        
        # Aksiyon ekle butonu
        btn_aksiyon = QPushButton("➕ Aksiyon Ekle")
        btn_aksiyon.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        btn_aksiyon.clicked.connect(self._aksiyon_ekle)
        aksiyon_layout.addWidget(btn_aksiyon, alignment=Qt.AlignLeft)
        
        # Aksiyon tablosu
        self.aksiyon_table = QTableWidget()
        self.aksiyon_table.setColumnCount(6)
        self.aksiyon_table.setHorizontalHeaderLabels([
            "Tip", "D Adımı", "Açıklama", "Sorumlu", "Hedef", "Durum"
        ])
        self.aksiyon_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.aksiyon_table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_sidebar')};
                color: {self.theme.get('text')};
                padding: 8px;
                border: none;
            }}
        """)
        
        self._refresh_aksiyonlar()
        aksiyon_layout.addWidget(self.aksiyon_table)
        
        tabs.addTab(aksiyon_widget, "⚡ Aksiyonlar")
        
        layout.addWidget(tabs, 1)
        
        # Alt butonlar
        btn_layout = QHBoxLayout()
        
        if self.kayit.get('durum') != 'KAPATILDI':
            btn_kapat = QPushButton("✓ Kaydı Kapat")
            btn_kapat.setStyleSheet(f"background: {self.theme.get('success')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
            btn_kapat.clicked.connect(self._kaydi_kapat)
            btn_layout.addWidget(btn_kapat)
        
        btn_layout.addStretch()
        
        btn_kapat_dlg = QPushButton("Kapat")
        btn_kapat_dlg.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 24px;")
        btn_kapat_dlg.clicked.connect(self.accept)
        btn_layout.addWidget(btn_kapat_dlg)
        
        layout.addLayout(btn_layout)
    
    def _refresh_aksiyonlar(self):
        """Aksiyon tablosunu güncelle"""
        self.aksiyon_table.setRowCount(len(self.aksiyonlar))
        for i, a in enumerate(self.aksiyonlar):
            self.aksiyon_table.setItem(i, 0, QTableWidgetItem(a.get('tip', '')))
            
            d_adimi = a.get('d_adimi')
            self.aksiyon_table.setItem(i, 1, QTableWidgetItem(f"D{d_adimi}" if d_adimi else "-"))
            
            self.aksiyon_table.setItem(i, 2, QTableWidgetItem((a.get('aciklama', '') or '')[:50]))
            self.aksiyon_table.setItem(i, 3, QTableWidgetItem(a.get('sorumlu', '') or ''))
            
            hedef = a.get('hedef')
            self.aksiyon_table.setItem(i, 4, QTableWidgetItem(str(hedef) if hedef else '-'))
            
            durum = a.get('durum', '')
            durum_item = QTableWidgetItem(durum)
            if durum == 'TAMAMLANDI':
                durum_item.setForeground(QColor(self.theme.get('success')))
            elif durum == 'AÇIK':
                durum_item.setForeground(QColor(self.theme.get('warning')))
            self.aksiyon_table.setItem(i, 5, durum_item)
    
    def _aksiyon_ekle(self):
        """Yeni aksiyon ekle"""
        QMessageBox.information(self, "Bilgi", "Aksiyon ekleme özelliği yakında eklenecek.")
    
    def _kaydi_kapat(self):
        """Kaydı kapat"""
        reply = QMessageBox.question(
            self, "Onay", 
            "Bu uygunsuzluk kaydını kapatmak istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE kalite.uygunsuzluklar 
                    SET durum = 'KAPATILDI', kapanis_tarihi = CAST(GETDATE() AS DATE),
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (self.kayit_id,))
                conn.commit()
                LogManager.log_update('kalite', 'kalite.uygunsuzluklar', None, 'Durum guncellendi')
                conn.close()
                
                QMessageBox.information(self, "Başarılı", "Kayıt kapatıldı.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kayıt kapatılamadı: {e}")


class KaliteRedPage(BasePage):
    """Red Kayıtları / Uygunsuzluk Yönetimi Sayfası - Üretim Redler sekmesi ile"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_all_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("❌ Red Kayıtları / Uygunsuzluk Yönetimi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text', '#fff')};")
        header.addWidget(title)
        header.addStretch()
        
        # Yenile butonu
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 16px;")
        btn_yenile.clicked.connect(self._load_all_data)
        header.addWidget(btn_yenile)
        
        layout.addLayout(header)
        
        # TAB WIDGET - Ana yapı
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                background: {self.theme.get('bg_card', '#1e293b')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QTabBar::tab:selected {{
                background: {self.theme.get('primary')};
                color: white;
                font-weight: bold;
            }}
        """)
        
        # TAB 1: Üretim Redleri (Yeni)
        self.uretim_tab = QWidget()
        self._setup_uretim_redler_tab()
        self.tab_widget.addTab(self.uretim_tab, "🏭 Üretim Redleri")
        
        # TAB 2: Uygunsuzluklar (Mevcut)
        self.uygunsuzluk_tab = QWidget()
        self._setup_uygunsuzluk_tab()
        self.tab_widget.addTab(self.uygunsuzluk_tab, "📋 Uygunsuzluklar")
        
        # TAB 3: Event Log (YENİ)
        self.event_log_tab = QWidget()
        self._setup_event_log_tab()
        self.tab_widget.addTab(self.event_log_tab, "📋 Event Log")
        
        layout.addWidget(self.tab_widget)
    
    def _setup_uretim_redler_tab(self):
        """Üretim Redleri sekmesi - Kalite kontrolden gelen redler"""
        layout = QVBoxLayout(self.uretim_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Üst bilgi
        info_layout = QHBoxLayout()
        info_lbl = QLabel("🏭 Üretimden gelen kalite kontrol red kayıtları")
        info_lbl.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 13px;")
        info_layout.addWidget(info_lbl)
        info_layout.addStretch()
        
        # İstatistik kartları
        self.uretim_stat_bekleyen = self._create_stat_card("⏳ Bekleyen", "0", self.theme.get('warning', '#f59e0b'))
        info_layout.addWidget(self.uretim_stat_bekleyen)
        
        self.uretim_stat_islenen = self._create_stat_card("✅ İşlenen", "0", self.theme.get('success', '#22c55e'))
        info_layout.addWidget(self.uretim_stat_islenen)
        
        self.uretim_stat_toplam = self._create_stat_card("📊 Toplam", "0", self.theme.get('primary', '#3b82f6'))
        info_layout.addWidget(self.uretim_stat_toplam)
        
        layout.addLayout(info_layout)
        
        # Filtreler
        filtre_layout = QHBoxLayout()
        
        filtre_layout.addWidget(QLabel("Durum:"))
        self.uretim_durum_combo = QComboBox()
        self.uretim_durum_combo.addItems(['Tümü', 'BEKLIYOR', 'İŞLENDİ', 'İADE', 'HURDA'])
        self.uretim_durum_combo.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 6px 12px;")
        self.uretim_durum_combo.currentIndexChanged.connect(self._load_uretim_redler)
        filtre_layout.addWidget(self.uretim_durum_combo)
        
        filtre_layout.addStretch()
        layout.addLayout(filtre_layout)
        
        # Tablo
        self.uretim_table = QTableWidget()
        self.uretim_table.setColumnCount(9)
        self.uretim_table.setHorizontalHeaderLabels([
            "ID", "Tarih", "İş Emri", "Lot No", "Ürün", "Red Adet", "Kontrol Eden", "Durum", "İşlem"
        ])
        self.uretim_table.setColumnHidden(0, True)
        self.uretim_table.setColumnWidth(1, 120)
        self.uretim_table.setColumnWidth(2, 100)
        self.uretim_table.setColumnWidth(3, 120)
        self.uretim_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.uretim_table.setColumnWidth(5, 80)
        self.uretim_table.setColumnWidth(6, 100)
        self.uretim_table.setColumnWidth(7, 80)
        self.uretim_table.setColumnWidth(8, 100)
        self.uretim_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.uretim_table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card', '#1e293b')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QHeaderView::section {{
                background: {self.theme.get('bg_sidebar')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)
        self.uretim_table.verticalHeader().setVisible(False)
        self.uretim_table.doubleClicked.connect(self._uretim_red_detay)
        layout.addWidget(self.uretim_table)
    
    def _setup_uygunsuzluk_tab(self):
        """Uygunsuzluklar sekmesi - Mevcut yapı"""
        layout = QVBoxLayout(self.uygunsuzluk_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Yeni kayıt butonları
        btn_layout = QHBoxLayout()
        
        btn_musteri = QPushButton("🏢 Müşteri Şikayeti")
        btn_musteri.setStyleSheet(f"background: {self.theme.get('danger', '#ef4444')}; color: white; border: none; border-radius: 6px; padding: 10px 16px; font-weight: bold;")
        btn_musteri.clicked.connect(lambda: self._yeni_kayit('MÜŞTERİ_ŞİKAYETİ'))
        btn_layout.addWidget(btn_musteri)
        
        btn_ic = QPushButton("🏭 İç Red")
        btn_ic.setStyleSheet(f"background: {self.theme.get('warning', '#f59e0b')}; color: white; border: none; border-radius: 6px; padding: 10px 16px; font-weight: bold;")
        btn_ic.clicked.connect(lambda: self._yeni_kayit('İÇ_RED'))
        btn_layout.addWidget(btn_ic)
        
        btn_tedarikci = QPushButton("📦 Tedarikçi Red")
        btn_tedarikci.setStyleSheet(f"background: {self.theme.get('info', '#06b6d4')}; color: white; border: none; border-radius: 6px; padding: 10px 16px; font-weight: bold;")
        btn_tedarikci.clicked.connect(lambda: self._yeni_kayit('TEDARİKÇİ_RED'))
        btn_layout.addWidget(btn_tedarikci)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # İstatistik kartları
        stat_layout = QHBoxLayout()
        
        self.stat_acik = self._create_stat_card("📋 Açık", "0", self.theme.get('warning', '#f59e0b'))
        stat_layout.addWidget(self.stat_acik)
        
        self.stat_islemde = self._create_stat_card("⚡ İşlemde", "0", self.theme.get('info', '#06b6d4'))
        stat_layout.addWidget(self.stat_islemde)
        
        self.stat_kapatilan = self._create_stat_card("✅ Kapatılan (Bu Ay)", "0", self.theme.get('success', '#22c55e'))
        stat_layout.addWidget(self.stat_kapatilan)
        
        self.stat_toplam = self._create_stat_card("📊 Toplam (Bu Ay)", "0", self.theme.get('primary', '#3b82f6'))
        stat_layout.addWidget(self.stat_toplam)
        
        stat_layout.addStretch()
        layout.addLayout(stat_layout)
        
        # Filtre
        filtre_layout = QHBoxLayout()
        
        filtre_layout.addWidget(QLabel("Durum:"))
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(['Tümü', 'AÇIK', 'İŞLEMDE', 'KAPATILDI'])
        self.cmb_durum.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 6px 12px;")
        self.cmb_durum.currentIndexChanged.connect(self._load_data)
        filtre_layout.addWidget(self.cmb_durum)
        
        filtre_layout.addWidget(QLabel("Tip:"))
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(['Tümü', 'MÜŞTERİ_ŞİKAYETİ', 'İÇ_RED', 'TEDARİKÇİ_RED', 'PROSES_RED', 'DENETİM_BULGUSU'])
        self.cmb_tip.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 6px 12px;")
        self.cmb_tip.currentIndexChanged.connect(self._load_data)
        filtre_layout.addWidget(self.cmb_tip)
        
        filtre_layout.addStretch()
        layout.addLayout(filtre_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kayıt No", "Tip", "Tarih", "Müşteri/Tedarikçi", "Ürün", "Öncelik", "Durum", "İşlem"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setColumnWidth(8, 120)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card', '#1e293b')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QHeaderView::section {{
                background: {self.theme.get('bg_sidebar')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)
    
    def _load_all_data(self):
        """Tüm sekmelerin verilerini yükle"""
        self._load_uretim_redler()
        self._load_data()
    
    def _load_uretim_redler(self):
        """Üretim redleri verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            durum_filtre = self.uretim_durum_combo.currentText()
            
            # Önce tablo var mı kontrol et, yoksa oluştur
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables t 
                              JOIN sys.schemas s ON t.schema_id = s.schema_id 
                              WHERE s.name = 'kalite' AND t.name = 'uretim_redler')
                BEGIN
                    CREATE TABLE kalite.uretim_redler (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        is_emri_id INT,
                        lot_no NVARCHAR(50),
                        red_miktar INT,
                        kontrol_id INT,
                        red_tarihi DATETIME DEFAULT GETDATE(),
                        kontrol_eden_id INT,
                        durum NVARCHAR(20) DEFAULT 'BEKLIYOR',
                        islem_tipi NVARCHAR(20),
                        aciklama NVARCHAR(500),
                        olusturma_tarihi DATETIME DEFAULT GETDATE(),
                        guncelleme_tarihi DATETIME
                    )
                END
            """)
            conn.commit()
            
            # Veri çek
            where_clause = ""
            params = []
            if durum_filtre != 'Tümü':
                where_clause = "WHERE ur.durum = ?"
                params.append(durum_filtre)
            
            cursor.execute(f"""
                SELECT ur.id, ur.red_tarihi, ie.is_emri_no, ur.lot_no, ie.stok_adi,
                       ur.red_miktar, p.ad + ' ' + p.soyad as kontrolcu, ur.durum
                FROM kalite.uretim_redler ur
                LEFT JOIN siparis.is_emirleri ie ON ur.is_emri_id = ie.id
                LEFT JOIN ik.personeller p ON ur.kontrol_eden_id = p.id
                {where_clause}
                ORDER BY ur.red_tarihi DESC
            """, params)
            
            rows = cursor.fetchall()
            self.uretim_table.setRowCount(len(rows))
            
            bekleyen = 0
            islenen = 0
            
            for i, row in enumerate(rows):
                self.uretim_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                
                # Tarih
                tarih = row[1]
                tarih_str = tarih.strftime('%d.%m.%Y') if tarih else '-'
                self.uretim_table.setItem(i, 1, QTableWidgetItem(tarih_str))
                
                # İş emri
                ie_item = QTableWidgetItem(row[2] or '-')
                ie_item.setForeground(QColor(self.theme.get('primary', '#6366f1')))
                self.uretim_table.setItem(i, 2, ie_item)
                
                # Lot no
                self.uretim_table.setItem(i, 3, QTableWidgetItem(row[3] or '-'))
                
                # Ürün
                self.uretim_table.setItem(i, 4, QTableWidgetItem((row[4] or '')[:30]))
                
                # Red adet
                adet_item = QTableWidgetItem(f"{row[5] or 0:,}")
                adet_item.setTextAlignment(Qt.AlignCenter)
                adet_item.setForeground(QColor(self.theme.get('danger', '#ef4444')))
                self.uretim_table.setItem(i, 5, adet_item)
                
                # Kontrol eden
                self.uretim_table.setItem(i, 6, QTableWidgetItem(row[6] or '-'))
                
                # Durum
                durum = row[7] or 'BEKLIYOR'
                durum_item = QTableWidgetItem(durum)
                if durum == 'BEKLIYOR':
                    durum_item.setForeground(QColor(self.theme.get('warning', '#f59e0b')))
                    bekleyen += 1
                elif durum in ('İŞLENDİ', 'İADE', 'HURDA'):
                    durum_item.setForeground(QColor(self.theme.get('success', '#22c55e')))
                    islenen += 1
                self.uretim_table.setItem(i, 7, durum_item)
                
                # İşlem butonu
                widget = self.create_action_buttons([
                    ("⚙️", "İşle", lambda checked, rid=row[0]: self._isle_uretim_red(rid), "edit"),
                ])
                self.uretim_table.setCellWidget(i, 8, widget)
                self.uretim_table.setRowHeight(i, 42)

            # İstatistikleri güncelle
            self.uretim_stat_bekleyen.findChild(QLabel, "stat_value").setText(str(bekleyen))
            self.uretim_stat_islenen.findChild(QLabel, "stat_value").setText(str(islenen))
            self.uretim_stat_toplam.findChild(QLabel, "stat_value").setText(str(len(rows)))
            
            conn.close()
            
        except Exception as e:
            print(f"Üretim redleri yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _isle_uretim_red(self, red_id: int):
        """Üretim red kaydını işle - YENİ VERSİYON"""
        try:
            # Red kaydını al
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    ur.id, ur.lot_no, ur.red_miktar, ur.is_emri_id,
                    ur.kontrol_eden_id, ur.durum, ur.aciklama,
                    ie.stok_adi, ie.stok_kodu, ie.urun_id, ie.cari_unvani,
                    ur.red_tarihi, ht.ad as hata_turu_adi
                FROM kalite.uretim_redler ur
                LEFT JOIN siparis.is_emirleri ie ON ur.is_emri_id = ie.id
                LEFT JOIN tanim.hata_turleri ht ON ur.hata_turu_id = ht.id
                WHERE ur.id = ?
            """, (red_id,))
            
            row = cursor.fetchone()
            if not row:
                QMessageBox.warning(self, "Uyarı", "Red kaydı bulunamadı!")
                conn.close()
                return
            
            # Red kayıt verisi
            red_kayit = {
                'id': row[0],
                'lot_no': row[1],
                'red_miktar': row[2],
                'is_emri_id': row[3],
                'kontrol_eden_id': row[4],
                'durum': row[5],
                'aciklama': row[6],
                'urun_adi': row[7],
                'stok_kodu': row[8],
                'urun_id': row[9],
                'musteri': row[10],
                'red_tarihi': row[11],
                'hata_turu_adi': row[12]
            }
            
            # Durum kontrolü
            if red_kayit['durum'] not in ['BEKLIYOR', 'MUSTERI_ONAY', None]:
                QMessageBox.information(self, "Bilgi", 
                    f"Bu kayıt zaten işlenmiş. Durum: {red_kayit['durum']}")
                conn.close()
                return
            
            conn.close()
            
            # Karar dialog'unu aç
            dlg = RedKararDialog(self.theme, red_kayit, self)
            if dlg.exec() != QDialog.Accepted:
                return  # İptal
            
            karar = dlg.get_karar()
            if not karar:
                return
            
            # Kararı işle
            self._isle_karar(karar)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İşlem hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_depo_id(self, kod: str) -> int:
        """Depo kodundan ID al"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tanim.depolar WHERE kod = ?", (kod,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"Depo ID alma hatası: {e}")
            return None
    
    def _isle_karar(self, karar: dict):
        """Kararı işle ve stok hareketini yap"""
        try:
            karar_tip = karar['tip']
            karar_not = karar['not']
            red_kayit = karar['red_kayit']
            islem_miktar = karar.get('miktar', red_kayit['red_miktar'])
            kalan_miktar = karar.get('kalan_miktar', 0)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            motor = HareketMotoru(conn)
            
            # Depo ID'leri - dinamik al
            RED_DEPO_ID = self._get_depo_id('RED') or 12
            FKK_DEPO_ID = self._get_depo_id('FKK') or 10
            SOKUM_DEPO_ID = self._get_depo_id('SOKUM') or self._get_depo_id('XI') or 13
            KAR_DEPO_ID = self._get_depo_id('KAR')  # Karantina Deposu
            
            # Akış şablonu ID'lerini al
            sablon_id = None
            if karar_tip == 'KABUL':
                sablon_id = self._get_akis_sablon_id(cursor, 'RED-KABUL') or self._get_akis_sablon_id(cursor, 'RED KABUL')
            elif karar_tip == 'SOKUM':
                sablon_id = self._get_akis_sablon_id(cursor, 'söküm') or self._get_akis_sablon_id(cursor, 'SOKUM')
            elif karar_tip == 'MUSTERI_ONAY':
                sablon_id = self._get_akis_sablon_id(cursor, 'RED-KARANTINA') or self._get_akis_sablon_id(cursor, 'RED KARANTINA')
            
            print(f"DEBUG: Karar tip={karar_tip}, Akış şablonu ID={sablon_id}")
            
            # Kullanıcı ID
            user_id = ModernLoginDialog.current_user_id or 1
            
            if karar_tip == 'KABUL':
                # KABUL - RED -> FKK (Final Kalite)
                self._isle_kabul(red_kayit, karar_not, motor, cursor, user_id, 
                                RED_DEPO_ID, FKK_DEPO_ID, islem_miktar, sablon_id)
            
            elif karar_tip == 'SOKUM':
                # SÖKÜM - RED -> XI (Söküm İstasyonu)
                self._isle_sokum(red_kayit, karar_not, motor, cursor, user_id, 
                                RED_DEPO_ID, SOKUM_DEPO_ID, islem_miktar, sablon_id)
            
            elif karar_tip == 'MUSTERI_ONAY':
                # MÜŞTERİ ONAYI - RED -> KAR (Karantina Deposu)
                self._isle_musteri_onay(red_kayit, karar_not, motor, cursor, user_id, 
                                       RED_DEPO_ID, KAR_DEPO_ID, islem_miktar, sablon_id)
            
            # Kalan miktar varsa red kaydını güncelle, yoksa işlenmiş olarak işaretle
            if kalan_miktar > 0:
                # Kısmi işlem - kalan miktar RED'de kalacak, durum BEKLIYOR kalmalı
                cursor.execute("""
                    UPDATE kalite.uretim_redler
                    SET red_miktar = ?,
                        durum = 'BEKLIYOR',
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (kalan_miktar, red_kayit['id']))
                print(f"DEBUG: Kalan miktar güncellendi: {kalan_miktar}, durum=BEKLIYOR")
            
            # ✅ OBSERVER - EVENT KAYDI
            try:
                from utils.hareket_observer import HareketObserver
                observer = HareketObserver(conn)
                
                # Hedef depo belirle
                hedef_depo = None
                if karar_tip == 'KABUL':
                    hedef_depo = FKK_DEPO_ID
                elif karar_tip == 'SOKUM':
                    hedef_depo = SOKUM_DEPO_ID
                elif karar_tip == 'MUSTERI_ONAY':
                    hedef_depo = KAR_DEPO_ID
                
                # Event kaydı oluştur
                if hedef_depo:
                    observer.on_hareket_completed(
                        lot_no=red_kayit['lot_no'],
                        depo_id=hedef_depo,
                        miktar=islem_miktar
                    )
            except Exception as e:
                print(f"⚠️ Observer hatası (önemsiz): {e}")
            # ✅ OBSERVER BİTTİ
            
            conn.commit()
            conn.close()
            
            karar_mesajlari = {
                'KABUL': f'{islem_miktar} adet Final Kalite deposuna gönderildi.',
                'SOKUM': f'{islem_miktar} adet Söküm İstasyonuna gönderildi.',
                'MUSTERI_ONAY': f'{islem_miktar} adet Karantina deposuna gönderildi.'
            }
            
            kalan_msg = f"\n\nKalan: {kalan_miktar} adet RED'de bekliyor." if kalan_miktar > 0 else ""
            
            QMessageBox.information(self, "✓ Başarılı", 
                f"Karar: {karar_tip}\n\n{karar_mesajlari.get(karar_tip, '')}{kalan_msg}")
            
            self._load_uretim_redler()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Karar işleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_akis_sablon_id(self, cursor, kod: str):
        """Akış şablonu ID'sini al"""
        try:
            cursor.execute("""
                SELECT id FROM tanim.akis_sablon 
                WHERE kod = ? AND aktif_mi = 1
            """, (kod,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception:
            return None
    
    def _isle_kabul(self, red_kayit: dict, karar_not: str, motor, cursor, 
                    user_id: int, red_depo_id: int, fkk_depo_id: int,
                    islem_miktar: int = None, sablon_id: int = None):
        """KABUL kararını işle - RED -> FKK transfer"""
        orijinal_lot = red_kayit['lot_no']
        miktar = islem_miktar if islem_miktar else red_kayit['red_miktar']
        
        # RED lot'unu bul - önce RED deposunda, sonra tüm depolarda ara
        # LOT-2601-0001-02 -> LOT-2601-0001-RED veya LOT-2601-0001-02-RED formatında olabilir
        lot_prefix = '-'.join(orijinal_lot.split('-')[:3])  # LOT-2601-0001
        
        cursor.execute("""
            SELECT lot_no, depo_id, miktar FROM stok.stok_bakiye 
            WHERE miktar > 0 AND (
                lot_no = ? OR 
                lot_no LIKE ? OR 
                lot_no = ?
            )
            ORDER BY 
                CASE WHEN depo_id = ? THEN 0 ELSE 1 END,
                CASE WHEN lot_no LIKE '%-RED' AND lot_no NOT LIKE '%-RED-S' THEN 0 ELSE 1 END
        """, (orijinal_lot, f"{lot_prefix}%-RED", f"{orijinal_lot}-RED", red_depo_id))
        
        red_lot_rows = cursor.fetchall()  # Tüm sonuçları al - cursor'ı temizle
        if red_lot_rows:
            red_lot_no = red_lot_rows[0][0]
            kaynak_depo_id = red_lot_rows[0][1]
            mevcut_miktar = red_lot_rows[0][2]
            print(f"DEBUG: Bulunan lot: {red_lot_no}, depo={kaynak_depo_id}, miktar={mevcut_miktar}")
        else:
            raise Exception(f"RED deposunda stok bulunamadı! Lot: {orijinal_lot}")
        
        # Miktar kontrolü
        if miktar > mevcut_miktar:
            raise Exception(f"Yetersiz stok! İstenen: {miktar}, Mevcut: {mevcut_miktar}")
        
        # FKK deposunda aynı lot var mı kontrol et
        cursor.execute("""
            SELECT id, miktar FROM stok.stok_bakiye 
            WHERE lot_no = ? AND depo_id = ?
        """, (red_lot_no, fkk_depo_id))
        mevcut_fkk = cursor.fetchall()
        
        if mevcut_fkk:
            # Mevcut FKK lot'una miktar ekle
            yeni_miktar = mevcut_fkk[0][1] + miktar
            
            # Kaynak lot'tan düş
            cursor.execute("""
                UPDATE stok.stok_bakiye 
                SET miktar = miktar - ?
                WHERE lot_no = ? AND depo_id = ? AND miktar >= ?
            """, (miktar, red_lot_no, kaynak_depo_id, miktar))
            
            # Hedef lot'a ekle
            cursor.execute("""
                UPDATE stok.stok_bakiye 
                SET miktar = ?, 
                    kalite_durumu = 'BEKLIYOR',
                    durum_kodu = 'FKK_BEKLIYOR'
                WHERE lot_no = ? AND depo_id = ?
            """, (yeni_miktar, red_lot_no, fkk_depo_id))
            
            print(f"DEBUG: Mevcut FKK lot'una eklendi: {red_lot_no}, yeni miktar={yeni_miktar}")
        else:
            # Yeni kayıt - transfer yap
            sonuc = motor.transfer(
                lot_no=red_lot_no,
                hedef_depo_id=fkk_depo_id,
                miktar=miktar,
                kaynak="KALITE_RED",
                kaynak_id=red_kayit['id'],
                aciklama=f"Red depot kabulü - {karar_not}" if karar_not else "Red depot kabulü"
            )
            
            if not sonuc.basarili:
                raise Exception(f"Stok hareketi başarısız: {sonuc.mesaj}")
            
            # Hedef lot kalite durumunu güncelle
            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET kalite_durumu = 'BEKLIYOR',
                    durum_kodu = 'FKK_BEKLIYOR'
                WHERE lot_no = ? AND depo_id = ?
            """, (red_lot_no, fkk_depo_id))
        
        # kalite.uretim_redler tablosunu güncelle
        cursor.execute("""
            UPDATE kalite.uretim_redler
            SET durum = 'KABUL',
                karar = 'KABUL',
                karar_veren_id = ?,
                karar_tarihi = GETDATE(),
                karar_notu = ?,
                guncelleme_tarihi = GETDATE()
            WHERE id = ?
        """, (user_id, karar_not, red_kayit['id']))
        
        print(f"✓ KABUL işlemi tamamlandı: {red_lot_no} -> FKK ({miktar} adet)")
    
    def _isle_sokum(self, red_kayit: dict, karar_not: str, motor, cursor,
                    user_id: int, red_depo_id: int, sokum_depo_id: int,
                    islem_miktar: int = None, sablon_id: int = None):
        """SÖKÜM kararını işle - RED -> XI, lot'a -S eki"""
        orijinal_lot = red_kayit['lot_no']
        miktar = islem_miktar if islem_miktar else red_kayit['red_miktar']
        
        # RED lot'unu bul - önce RED deposunda, sonra tüm depolarda ara
        lot_prefix = '-'.join(orijinal_lot.split('-')[:3])  # LOT-2601-0001
        
        cursor.execute("""
            SELECT lot_no, depo_id, miktar FROM stok.stok_bakiye 
            WHERE miktar > 0 AND (
                lot_no = ? OR 
                lot_no LIKE ? OR 
                lot_no = ?
            ) AND lot_no NOT LIKE '%-RED-S'
            ORDER BY 
                CASE WHEN depo_id = ? THEN 0 ELSE 1 END,
                CASE WHEN lot_no LIKE '%-RED' THEN 0 ELSE 1 END
        """, (orijinal_lot, f"{lot_prefix}%-RED", f"{orijinal_lot}-RED", red_depo_id))
        
        red_lot_rows = cursor.fetchall()  # Tüm sonuçları al - cursor'ı temizle
        if red_lot_rows:
            red_lot_no = red_lot_rows[0][0]
            kaynak_depo_id = red_lot_rows[0][1]
            mevcut_miktar = red_lot_rows[0][2]
            print(f"DEBUG: Bulunan lot: {red_lot_no}, depo={kaynak_depo_id}, miktar={mevcut_miktar}")
        else:
            raise Exception(f"RED deposunda stok bulunamadı! Lot: {orijinal_lot}")
        
        # Miktar kontrolü
        if miktar > mevcut_miktar:
            raise Exception(f"Yetersiz stok! İstenen: {miktar}, Mevcut: {mevcut_miktar}")
        
        # Yeni lot numarası: -S eki ekle
        sokum_lot = f"{red_lot_no}-S"
        
        # XI deposunda -S lot'u zaten var mı kontrol et
        cursor.execute("""
            SELECT id, miktar FROM stok.stok_bakiye 
            WHERE lot_no = ? AND depo_id = ?
        """, (sokum_lot, sokum_depo_id))
        mevcut_sokum = cursor.fetchall()
        
        if mevcut_sokum:
            # Mevcut -S lot'una miktar ekle (transfer yerine direkt güncelle)
            yeni_miktar = mevcut_sokum[0][1] + miktar
            
            # Kaynak lot'tan düş
            cursor.execute("""
                UPDATE stok.stok_bakiye 
                SET miktar = miktar - ?
                WHERE lot_no = ? AND depo_id = ? AND miktar >= ?
            """, (miktar, red_lot_no, kaynak_depo_id, miktar))
            
            # Hedef lot'a ekle
            cursor.execute("""
                UPDATE stok.stok_bakiye 
                SET miktar = ?,
                    durum_kodu = 'SOKUM'
                WHERE lot_no = ? AND depo_id = ?
            """, (yeni_miktar, sokum_lot, sokum_depo_id))
            
            print(f"DEBUG: Mevcut söküm lot'una eklendi: {sokum_lot}, yeni miktar={yeni_miktar}")
        else:
            # Yeni -S lot'u oluştur - transfer yap
            sonuc = motor.transfer(
                lot_no=red_lot_no,
                hedef_depo_id=sokum_depo_id,
                miktar=miktar,
                kaynak="KALITE_RED",
                kaynak_id=red_kayit['id'],
                aciklama=f"Söküm için transfer - {karar_not}" if karar_not else "Söküm için transfer"
            )
            
            if not sonuc.basarili:
                raise Exception(f"Stok transferi başarısız: {sonuc.mesaj}")
            
            # Hedef depodaki kaydın lot adını -S ekli yap
            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET lot_no = ?,
                    kalite_durumu = 'SOKUM_BEKLIYOR',
                    durum_kodu = 'SOKUM'
                WHERE lot_no = ? AND depo_id = ?
            """, (sokum_lot, red_lot_no, sokum_depo_id))
        
        # kalite.uretim_redler tablosunu güncelle
        cursor.execute("""
            UPDATE kalite.uretim_redler
            SET durum = 'SOKUM_BEKLIYOR',
                karar = 'SOKUM',
                karar_veren_id = ?,
                karar_tarihi = GETDATE(),
                karar_notu = ?,
                guncelleme_tarihi = GETDATE()
            WHERE id = ?
        """, (user_id, karar_not, red_kayit['id']))
        
        print(f"✓ Söküm işlemi tamamlandı: {red_lot_no} -> {sokum_lot} (XI deposu, {miktar} adet)")
    
    def _isle_musteri_onay(self, red_kayit: dict, karar_not: str, motor, cursor, 
                           user_id: int, red_depo_id: int, kar_depo_id: int,
                           islem_miktar: int = None, sablon_id: int = None):
        """MÜŞTERİ ONAYI kararını işle - RED -> KAR (Karantina) transfer"""
        orijinal_lot = red_kayit['lot_no']
        miktar = islem_miktar if islem_miktar else red_kayit['red_miktar']
        
        # RED lot'unu bul - önce RED deposunda, sonra tüm depolarda ara
        lot_prefix = '-'.join(orijinal_lot.split('-')[:3])  # LOT-2601-0001
        
        cursor.execute("""
            SELECT lot_no, depo_id, miktar FROM stok.stok_bakiye 
            WHERE miktar > 0 AND (
                lot_no = ? OR 
                lot_no LIKE ? OR 
                lot_no = ?
            ) AND lot_no NOT LIKE '%-RED-S'
            ORDER BY 
                CASE WHEN depo_id = ? THEN 0 ELSE 1 END,
                CASE WHEN lot_no LIKE '%-RED' THEN 0 ELSE 1 END
        """, (orijinal_lot, f"{lot_prefix}%-RED", f"{orijinal_lot}-RED", red_depo_id))
        
        red_lot_rows = cursor.fetchall()  # Tüm sonuçları al - cursor'ı temizle
        if red_lot_rows:
            red_lot_no = red_lot_rows[0][0]
            kaynak_depo_id = red_lot_rows[0][1]
            mevcut_miktar = red_lot_rows[0][2]
            print(f"DEBUG: Bulunan lot: {red_lot_no}, depo={kaynak_depo_id}, miktar={mevcut_miktar}")
        else:
            raise Exception(f"RED deposunda stok bulunamadı! Lot: {orijinal_lot}")
        
        # Miktar kontrolü
        if miktar > mevcut_miktar:
            raise Exception(f"Yetersiz stok! İstenen: {miktar}, Mevcut: {mevcut_miktar}")
        
        # Karantina deposu tanımlı mı kontrol et
        if kar_depo_id:
            # Stok hareketi: kaynak depo -> KAR transfer
            sonuc = motor.transfer(
                lot_no=red_lot_no,
                hedef_depo_id=kar_depo_id,
                miktar=miktar,
                kaynak="KALITE_RED",
                kaynak_id=red_kayit['id'],
                aciklama=f"Müşteri onayı için karantinaya - {karar_not}" if karar_not else "Müşteri onayı için karantinaya"
            )
            
            if not sonuc.basarili:
                raise Exception(f"Stok hareketi başarısız: {sonuc.mesaj}")
            
            # stok_bakiye kalite durumunu güncelle
            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET kalite_durumu = 'MUSTERI_ONAY_BEKLIYOR',
                    durum_kodu = 'KARANTINA'
                WHERE lot_no = ? AND depo_id = ?
            """, (red_lot_no, kar_depo_id))
        
        # kalite.uretim_redler tablosunu güncelle
        cursor.execute("""
            UPDATE kalite.uretim_redler
            SET durum = 'MUSTERI_ONAY',
                karar = 'MUSTERI_ONAY',
                karar_veren_id = ?,
                karar_tarihi = GETDATE(),
                karar_notu = ?,
                guncelleme_tarihi = GETDATE()
            WHERE id = ?
        """, (user_id, karar_not, red_kayit['id']))
        
        print(f"✓ Müşteri onayı için karantinaya alındı: {red_lot_no} ({miktar} adet)")
    
    def _uretim_red_detay(self, index):
        """Üretim red detayı göster"""
        row = index.row()
        red_id = int(self.uretim_table.item(row, 0).text())
        # TODO: Detay dialog'u
        QMessageBox.information(self, "Detay", f"Red ID: {red_id} detayları yakında eklenecek.")
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """İstatistik kartı"""
        card = QFrame()
        card.setFixedSize(160, 70)
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
    
    def _yeni_kayit(self, tip: str):
        """Yeni uygunsuzluk kaydı"""
        dlg = UygunsuzlukDialog(self.theme, tip, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _on_double_click(self, index):
        """Satıra çift tıklama"""
        row = index.row()
        kayit_id = int(self.table.item(row, 0).text())
        dlg = UygunsuzlukDetayDialog(self.theme, kayit_id, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _detay_goster(self, kayit_id: int):
        """Detay dialog'unu göster"""
        dlg = UygunsuzlukDetayDialog(self.theme, kayit_id, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _load_data(self):
        """Verileri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Filtreler
            durum_filtre = self.cmb_durum.currentText()
            tip_filtre = self.cmb_tip.currentText()
            
            where_clauses = []
            params = []
            
            if durum_filtre != 'Tümü':
                where_clauses.append("u.durum = ?")
                params.append(durum_filtre)
            
            if tip_filtre != 'Tümü':
                where_clauses.append("u.kayit_tipi = ?")
                params.append(tip_filtre)
            
            where_sql = " AND " + " AND ".join(where_clauses) if where_clauses else ""
            
            # Ana sorgu
            cursor.execute(f"""
                SELECT TOP 200 u.id, u.kayit_no, u.kayit_tipi, u.kayit_tarihi,
                       c.unvan, s.urun_adi, u.oncelik, u.durum
                FROM kalite.uygunsuzluklar u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN stok.urunler s ON u.urun_id = s.id
                WHERE 1=1 {where_sql}
                ORDER BY u.kayit_tarihi DESC, u.id DESC
            """, params)
            
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                
                # Tip
                tip = row[2] or ''
                tip_item = QTableWidgetItem(tip.replace('_', ' '))
                self.table.setItem(i, 2, tip_item)
                
                # Tarih
                tarih = row[3]
                tarih_str = tarih.strftime('%d.%m.%Y') if tarih else '-'
                self.table.setItem(i, 3, QTableWidgetItem(tarih_str))
                
                self.table.setItem(i, 4, QTableWidgetItem((row[4] or '')[:30]))
                self.table.setItem(i, 5, QTableWidgetItem((row[5] or '')[:30]))
                
                # Öncelik
                oncelik = row[6] or ''
                oncelik_item = QTableWidgetItem(oncelik)
                oncelik_colors = {
                    'KRİTİK': self.theme.get('danger'),
                    'YÜKSEK': self.theme.get('warning'),
                    'NORMAL': self.theme.get('info'),
                    'DÜŞÜK': self.theme.get('text_secondary')
                }
                if oncelik in oncelik_colors:
                    oncelik_item.setForeground(QColor(oncelik_colors[oncelik]))
                self.table.setItem(i, 6, oncelik_item)
                
                # Durum
                durum = row[7] or ''
                durum_item = QTableWidgetItem(durum)
                durum_colors = {
                    'AÇIK': self.theme.get('warning'),
                    'İŞLEMDE': self.theme.get('info'),
                    'KAPATILDI': self.theme.get('success'),
                    'İPTAL': self.theme.get('text_secondary')
                }
                if durum in durum_colors:
                    durum_item.setForeground(QColor(durum_colors[durum]))
                self.table.setItem(i, 7, durum_item)
                
                # İşlem butonu
                widget = self.create_action_buttons([
                    ("📋", "Detay", lambda checked, kid=row[0]: self._detay_goster(kid), "info"),
                ])
                self.table.setCellWidget(i, 8, widget)
                self.table.setRowHeight(i, 42)

            # İstatistikler
            cursor.execute("SELECT COUNT(*) FROM kalite.uygunsuzluklar WHERE durum = 'AÇIK'")
            self.stat_acik.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            cursor.execute("SELECT COUNT(*) FROM kalite.uygunsuzluklar WHERE durum = 'İŞLEMDE'")
            self.stat_islemde.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            cursor.execute("""
                SELECT COUNT(*) FROM kalite.uygunsuzluklar 
                WHERE durum = 'KAPATILDI' AND MONTH(kapanis_tarihi) = MONTH(GETDATE()) AND YEAR(kapanis_tarihi) = YEAR(GETDATE())
            """)
            self.stat_kapatilan.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            cursor.execute("""
                SELECT COUNT(*) FROM kalite.uygunsuzluklar 
                WHERE MONTH(kayit_tarihi) = MONTH(GETDATE()) AND YEAR(kayit_tarihi) = YEAR(GETDATE())
            """)
            self.stat_toplam.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            conn.close()
            
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
    
    def _setup_event_log_tab(self):
        """Event Log sekmesi - kalite_event_log.py içeriğini buraya embed ediyoruz"""
        from .kalite_event_log import EventLogPage
        
        # Event log sayfasını bu tab içine embed et
        layout = QVBoxLayout(self.event_log_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # EventLogPage widget'ını oluştur
        event_log_widget = EventLogPage(self.theme)
        layout.addWidget(event_log_widget)
