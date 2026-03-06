# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Proses Kalite Kontrol Sayfası
Lot bazlı kalite kontrol, hata kayıt ve etiket basma
"""
import os
import subprocess
import tempfile
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QSpinBox, QTextEdit, QSplitter, QWidget, QGridLayout,
    QDoubleSpinBox, QInputDialog, QGroupBox, QListWidget, QListWidgetItem,
    QDialogButtonBox
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QColor, QFont, QPixmap
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from components.base_page import BasePage
from core.database import get_db_connection

# Etiket ayarları (sonra sistem ayarlarından gelecek)
ETIKET_YAZICI = "Godex G500"  # Windows yazıcı adı
ETIKET_BOYUT = (100, 50)  # mm
from config import NAS_PATHS
NAS_IMAGE_PATH = NAS_PATHS["image_path"]


class EtiketOnizlemeDialog(QDialog):
    """Gelişmiş etiket önizleme ve yazdırma dialog'u"""
    
    def __init__(self, theme: dict, etiket_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.etiket_data = etiket_data
        self.setWindowTitle("🏷️ Etiket Önizleme ve Yazdır")
        self.setMinimumSize(550, 550)
        self._setup_ui()
        self._load_sablonlar()
        self._load_yazicilar()
    
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
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        title = QLabel("🏷️ Etiket Önizleme")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary', '#6366f1')};")
        layout.addWidget(title)
        
        # Etiket önizleme frame - 100x50mm oranında
        etiket_frame = QFrame()
        etiket_frame.setFixedSize(400, 200)
        etiket_frame.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid {self.theme.get('border', '#3d4454')};
                border-radius: 8px;
            }}
        """)
        
        etiket_layout = QVBoxLayout(etiket_frame)
        etiket_layout.setContentsMargins(15, 10, 15, 10)
        etiket_layout.setSpacing(4)
        
        # Müşteri adı (büyük)
        musteri_lbl = QLabel(self.etiket_data.get('musteri', '')[:35])
        musteri_lbl.setStyleSheet("color: #000; font-size: 16px; font-weight: bold;")
        musteri_lbl.setAlignment(Qt.AlignCenter)
        etiket_layout.addWidget(musteri_lbl)
        
        # Ayırıcı çizgi
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #333;")
        line.setFixedHeight(1)
        etiket_layout.addWidget(line)
        
        # Ürün
        urun_lbl = QLabel(f"Ürün: {self.etiket_data.get('urun', '')[:30]}")
        urun_lbl.setStyleSheet("color: #000; font-size: 12px;")
        etiket_layout.addWidget(urun_lbl)
        
        # Lot No
        lot_lbl = QLabel(f"Lot: {self.etiket_data.get('lot_no', '')}")
        lot_lbl.setStyleSheet("color: #000; font-size: 12px; font-weight: bold;")
        etiket_layout.addWidget(lot_lbl)
        
        # Adet ve Tarih yan yana
        info_layout = QHBoxLayout()
        adet_lbl = QLabel(f"Adet: {self.etiket_data.get('adet', 0):,}")
        adet_lbl.setStyleSheet("color: #000; font-size: 12px;")
        info_layout.addWidget(adet_lbl)
        
        tarih_lbl = QLabel(f"Tarih: {self.etiket_data.get('tarih', '')}")
        tarih_lbl.setStyleSheet("color: #000; font-size: 12px;")
        info_layout.addWidget(tarih_lbl)
        etiket_layout.addLayout(info_layout)
        
        # Kontrol eden
        kontrol_lbl = QLabel(f"Kontrol: {self.etiket_data.get('kontrolcu', '')[:20]}")
        kontrol_lbl.setStyleSheet("color: #000; font-size: 11px;")
        etiket_layout.addWidget(kontrol_lbl)
        
        # Barkod gösterimi (simüle)
        barkod_lbl = QLabel("|||||||||||||||||||||||||||||||||||")
        barkod_lbl.setStyleSheet("color: #000; font-size: 20px; font-family: monospace;")
        barkod_lbl.setAlignment(Qt.AlignCenter)
        etiket_layout.addWidget(barkod_lbl)
        
        barkod_text = QLabel(self.etiket_data.get('lot_no', ''))
        barkod_text.setStyleSheet("color: #000; font-size: 10px;")
        barkod_text.setAlignment(Qt.AlignCenter)
        etiket_layout.addWidget(barkod_text)
        
        layout.addWidget(etiket_frame, alignment=Qt.AlignCenter)
        
        # Boyut bilgisi
        info = QLabel("100 x 50 mm")
        info.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 11px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        # Şablon Seçimi
        sablon_group = QGroupBox("📋 Etiket Şablonu")
        sablon_layout = QHBoxLayout(sablon_group)
        sablon_layout.addWidget(QLabel("Şablon:"))
        self.sablon_combo = QComboBox()
        self.sablon_combo.setMinimumWidth(250)
        self.sablon_combo.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        sablon_layout.addWidget(self.sablon_combo)
        sablon_layout.addStretch()
        layout.addWidget(sablon_group)
        
        # Yazıcı Seçimi
        yazici_group = QGroupBox("🖨️ Yazıcı Ayarları")
        yazici_layout = QHBoxLayout(yazici_group)
        yazici_layout.addWidget(QLabel("Yazıcı:"))
        self.yazici_combo = QComboBox()
        self.yazici_combo.setMinimumWidth(200)
        self.yazici_combo.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        yazici_layout.addWidget(self.yazici_combo)
        
        yazici_layout.addWidget(QLabel("Mod:"))
        self.mod_combo = QComboBox()
        self.mod_combo.addItem("PDF Yazdır", "PDF")
        self.mod_combo.addItem("Godex Direkt (EZPL)", "EZPL")
        self.mod_combo.setStyleSheet(self.yazici_combo.styleSheet())
        yazici_layout.addWidget(self.mod_combo)
        yazici_layout.addStretch()
        layout.addWidget(yazici_group)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        onizle_btn = QPushButton("👁️ PDF Önizle")
        onizle_btn.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 20px;")
        onizle_btn.clicked.connect(self._pdf_onizle)
        btn_layout.addWidget(onizle_btn)
        
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 20px;")
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)
        
        yazdir_btn = QPushButton("🖨️ Yazdır")
        yazdir_btn.setStyleSheet(f"background: {self.theme.get('success', '#22c55e')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        yazdir_btn.clicked.connect(self.accept)
        btn_layout.addWidget(yazdir_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_sablonlar(self):
        """Etiket şablonlarını yükle"""
        self.sablon_combo.clear()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sablon_kodu, sablon_adi, varsayilan_mi
                FROM tanim.etiket_sablonlari
                WHERE aktif_mi = 1 AND sablon_tipi IN ('PALET', 'MAMUL', 'SEVK')
                ORDER BY varsayilan_mi DESC, sablon_adi
            """)
            for row in cursor.fetchall():
                varsayilan = " ⭐" if row[3] else ""
                self.sablon_combo.addItem(f"{row[2]}{varsayilan}", row[0])
            conn.close()
            if self.sablon_combo.count() == 0:
                self.sablon_combo.addItem("Varsayılan Şablon", None)
        except Exception as e:
            print(f"Şablon yükleme hatası: {e}")
            self.sablon_combo.addItem("Varsayılan Şablon", None)
    
    def _load_yazicilar(self):
        """Mevcut yazıcıları yükle"""
        self.yazici_combo.clear()
        try:
            from utils.etiket_yazdir import get_available_printers, get_godex_printers
            all_printers = get_available_printers()
            godex_printers = get_godex_printers()
            if godex_printers:
                for p in godex_printers:
                    self.yazici_combo.addItem(f"🏷️ {p}", p)
            for p in all_printers:
                if p not in godex_printers:
                    self.yazici_combo.addItem(p, p)
            if self.yazici_combo.count() == 0:
                self.yazici_combo.addItem("PDF Dosyası Olarak Kaydet", "PDF_ONLY")
        except ImportError:
            self.yazici_combo.addItem("PDF Dosyası Olarak Kaydet", "PDF_ONLY")
        except Exception as e:
            print(f"Yazıcı listesi yüklenemedi: {e}")
            self.yazici_combo.addItem("PDF Dosyası Olarak Kaydet", "PDF_ONLY")
    
    def _pdf_onizle(self):
        """PDF önizleme"""
        import subprocess
        import tempfile
        try:
            from utils.etiket_yazdir import a4_etiket_pdf_olustur
            etiketler = [self.etiket_data]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='etiket_onizle_')
            temp_path = temp_file.name
            temp_file.close()
            a4_etiket_pdf_olustur(temp_path, etiketler)
            subprocess.Popen(['start', '', temp_path], shell=True)
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"PDF önizleme hatası: {e}")
    
    def get_sablon_id(self):
        return self.sablon_combo.currentData()
    
    def get_yazici(self):
        return self.yazici_combo.currentData()
    
    def get_mod(self):
        return self.mod_combo.currentData()


class HataEkleDialog(QDialog):
    """Hata ekleme dialog'u"""
    
    def __init__(self, theme: dict, hata_turleri: list, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.hata_turleri = hata_turleri
        self.setWindowTitle("Hata Ekle")
        self.setMinimumSize(400, 200)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main', '#1a1f2e')}; }}
            QLabel {{ color: {self.theme.get('text', '#fff')}; }}
            QComboBox, QSpinBox {{
                background: {self.theme.get('bg_input', '#2d3548')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 8px 12px;
                color: {self.theme.get('text', '#fff')};
                min-width: 200px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Hata türü
        layout.addWidget(QLabel("Hata Türü:"))
        self.hata_combo = QComboBox()
        for hata in self.hata_turleri:
            self.hata_combo.addItem(f"{hata['kod']} - {hata['ad']}", hata['id'])
        layout.addWidget(self.hata_combo)
        
        # Adet
        layout.addWidget(QLabel("Hatalı Adet:"))
        self.adet_input = QSpinBox()
        self.adet_input.setRange(1, 99999)
        self.adet_input.setValue(1)
        layout.addWidget(self.adet_input)
        
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 16px;")
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)
        
        ekle_btn = QPushButton("✓ Ekle")
        ekle_btn.setStyleSheet(f"background: {self.theme.get('success', '#22c55e')}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        ekle_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ekle_btn)
        
        layout.addLayout(btn_layout)
    
    def get_data(self):
        return {
            'hata_turu_id': self.hata_combo.currentData(),
            'hata_adi': self.hata_combo.currentText(),
            'adet': self.adet_input.value()
        }


class PersonelGirisDialog(QDialog):
    """Personel kart/sicil giriş dialogu"""
    
    def __init__(self, theme, gorev_data, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.gorev = gorev_data
        self.personel_data = None
        self.setWindowTitle("Personel Girişi")
        self.setMinimumSize(450, 380)
        self.setModal(True)
        self._setup_ui()
        self.sicil_input.setFocus()
    
    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main', '#1a1f2e')}; }} QLabel {{ color: {self.theme.get('text', '#fff')}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        title = QLabel("🔐 Kontrol İşlemine Başla")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary', '#6366f1')};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        info_frame = QFrame()
        info_frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card', '#242938')}; border: 1px solid {self.theme.get('border', '#3d4454')}; border-radius: 8px; padding: 12px; }}")
        info_layout = QVBoxLayout(info_frame)
        
        ie_lbl = QLabel(f"📋 {self.gorev.get('is_emri_no', '')} - {self.gorev.get('lot_no', '')}")
        ie_lbl.setStyleSheet(f"color: {self.theme.get('primary', '#6366f1')}; font-weight: bold;")
        info_layout.addWidget(ie_lbl)
        
        urun_lbl = QLabel(f"📦 {(self.gorev.get('urun_adi', '') or '')[:40]}")
        info_layout.addWidget(urun_lbl)
        
        kontrol_adet = self.gorev.get('kontrol_adet', 0) or self.gorev.get('toplam_adet', 0)
        miktar_lbl = QLabel(f"🔢 Kontrol Edilecek: {kontrol_adet:,} adet")
        miktar_lbl.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-weight: bold; font-size: 14px;")
        info_layout.addWidget(miktar_lbl)
        
        atanan = self.gorev.get('atanan_personel', '')
        if atanan:
            atanan_lbl = QLabel(f"👤 Atanan: {atanan}")
            atanan_lbl.setStyleSheet(f"color: {self.theme.get('success', '#22c55e')}; font-weight: bold;")
            info_layout.addWidget(atanan_lbl)
        
        layout.addWidget(info_frame)
        
        nfc_lbl = QLabel("💳 Kartınızı okutun veya sicil numaranızı girin")
        nfc_lbl.setStyleSheet(f"color: {self.theme.get('text_muted', '#8a94a6')}; padding: 15px; border: 2px dashed {self.theme.get('primary', '#6366f1')}; border-radius: 8px;")
        nfc_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(nfc_lbl)
        
        input_style = f"background: {self.theme.get('bg_input', '#2d3548')}; color: {self.theme.get('text', '#fff')}; border: 1px solid {self.theme.get('border', '#3d4454')}; border-radius: 8px; padding: 12px;"
        
        self.sicil_input = QLineEdit()
        self.sicil_input.setPlaceholderText("Sicil No veya Kart ID")
        self.sicil_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        self.sicil_input.returnPressed.connect(self._login)
        layout.addWidget(self.sicil_input)
        
        giris_btn = QPushButton("🚀 İşleme Başla")
        giris_btn.setCursor(Qt.PointingHandCursor)
        giris_btn.setStyleSheet(f"QPushButton {{ background: {self.theme.get('primary', '#6366f1')}; color: white; border: none; border-radius: 8px; padding: 12px; font-weight: bold; }}")
        giris_btn.clicked.connect(self._login)
        layout.addWidget(giris_btn)
        
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {self.theme.get('text_muted', '#8a94a6')}; border: 1px solid {self.theme.get('border', '#3d4454')}; border-radius: 6px; padding: 8px; }}")
        iptal_btn.clicked.connect(self.reject)
        layout.addWidget(iptal_btn)
    
    def _login(self):
        sicil = self.sicil_input.text().strip()
        if not sicil:
            QMessageBox.warning(self, "Uyarı", "Sicil numarası veya kart ID giriniz!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, uuid, ad, soyad, sicil_no, departman_id, kart_no
                FROM ik.personeller WHERE (sicil_no = ? OR kart_no = ?) AND aktif_mi = 1
            """, (sicil, sicil))
            personel = cursor.fetchone()
            if not personel:
                QMessageBox.warning(self, "Hata", "Personel bulunamadı!")
                conn.close()
                return
            
            personel_uuid = personel[1]
            atanan_id = self.gorev.get('atanan_personel_id')
            if atanan_id and str(personel_uuid) != str(atanan_id):
                QMessageBox.warning(self, "Yetki Hatası", f"Bu görev {self.gorev.get('atanan_personel', '')} personeline atanmış!")
                conn.close()
                return
            
            conn.close()
            self.personel_data = {
                'id': personel[0], 'uuid': str(personel_uuid),
                'ad': personel[2], 'soyad': personel[3],
                'sicil_no': personel[4], 'ad_soyad': f"{personel[2]} {personel[3]}"
            }
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Giriş hatası: {e}")


class KaliteFinalPage(BasePage):
    """Proses Kalite Kontrol Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.secili_is_emri = None
        self.hata_listesi = []  # Eklenen hatalar
        self.hata_turleri = []  # Hata türleri cache
        self._setup_ui()
        self._load_hata_turleri()
        self._load_kontrolcular()
        QTimer.singleShot(100, self._load_data)
        
        # Saat
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("✅ Proses Kalite Kontrol")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text', '#fff')};")
        header.addWidget(title)
        header.addStretch()
        
        self.saat_label = QLabel()
        self.saat_label.setStyleSheet(f"color: {self.theme.get('text_muted', '#8a94a6')}; font-size: 18px; font-weight: bold;")
        header.addWidget(self.saat_label)
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(self._button_style())
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        layout.addLayout(header)
        
        # Splitter - Sol: Bekleyen lotlar, Sağ: Kontrol formu
        splitter = QSplitter(Qt.Horizontal)
        
        # SOL PANEL - Kontrol Bekleyen Lotlar
        sol_widget = QWidget()
        sol_layout = QVBoxLayout(sol_widget)
        sol_layout.setContentsMargins(0, 0, 0, 0)
        
        sol_header = QLabel("📋 KONTROL BEKLEYEN LOTLAR")
        sol_header.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-weight: bold; font-size: 14px;")
        sol_layout.addWidget(sol_header)
        
        self.bekleyen_table = QTableWidget()
        self.bekleyen_table.setColumnCount(8)
        self.bekleyen_table.setHorizontalHeaderLabels([
            "ID", "İş Emri", "Ürün", "Lot No", "Adet", "Atanan", "Durum", "İşlem"
        ])
        self.bekleyen_table.setColumnHidden(0, True)
        self.bekleyen_table.setColumnWidth(1, 100)
        self.bekleyen_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.bekleyen_table.setColumnWidth(3, 110)
        self.bekleyen_table.setColumnWidth(4, 70)
        self.bekleyen_table.setColumnWidth(5, 120)
        self.bekleyen_table.setColumnWidth(6, 80)
        self.bekleyen_table.setColumnWidth(7, 120)
        self.bekleyen_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bekleyen_table.setStyleSheet(self._table_style())
        self.bekleyen_table.verticalHeader().setVisible(False)
        sol_layout.addWidget(self.bekleyen_table)
        
        splitter.addWidget(sol_widget)
        
        # SAĞ PANEL - Kontrol Formu
        sag_widget = QFrame()
        sag_widget.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card', '#242938')}; border: 2px solid {self.theme.get('primary', '#6366f1')}; border-radius: 12px; }}")
        sag_layout = QVBoxLayout(sag_widget)
        sag_layout.setContentsMargins(16, 16, 16, 16)
        sag_layout.setSpacing(12)
        
        sag_header = QLabel("📝 KONTROL FORMU")
        sag_header.setStyleSheet(f"color: {self.theme.get('primary', '#6366f1')}; font-weight: bold; font-size: 14px;")
        sag_layout.addWidget(sag_header)
        
        # Seçili lot bilgileri
        self.bilgi_frame = QFrame()
        self.bilgi_frame.setStyleSheet(f"background: {self.theme.get('bg_main')}; border-radius: 8px; padding: 12px;")
        bilgi_layout = QGridLayout(self.bilgi_frame)
        bilgi_layout.setSpacing(8)
        
        lbl1 = QLabel("İş Emri:")
        lbl1.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        bilgi_layout.addWidget(lbl1, 0, 0)
        self.lbl_is_emri = QLabel("-")
        self.lbl_is_emri.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold;")
        bilgi_layout.addWidget(self.lbl_is_emri, 0, 1)
        
        lbl2 = QLabel("Ürün:")
        lbl2.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        bilgi_layout.addWidget(lbl2, 0, 2)
        self.lbl_urun = QLabel("-")
        self.lbl_urun.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold;")
        bilgi_layout.addWidget(self.lbl_urun, 0, 3)
        
        lbl3 = QLabel("Lot No:")
        lbl3.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        bilgi_layout.addWidget(lbl3, 1, 0)
        self.lbl_lot = QLabel("-")
        self.lbl_lot.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold;")
        bilgi_layout.addWidget(self.lbl_lot, 1, 1)
        
        lbl4 = QLabel("Toplam Adet:")
        lbl4.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        bilgi_layout.addWidget(lbl4, 1, 2)
        self.lbl_toplam = QLabel("-")
        self.lbl_toplam.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold; font-size: 16px;")
        bilgi_layout.addWidget(self.lbl_toplam, 1, 3)
        
        sag_layout.addWidget(self.bilgi_frame)
        
        # Kontrol girişleri
        giris_frame = QFrame()
        giris_frame.setStyleSheet(f"background: {self.theme.get('bg_main')}; border-radius: 8px; padding: 12px;")
        giris_layout = QGridLayout(giris_frame)
        giris_layout.setSpacing(12)
        
        # Kontrol edilen adet
        lbl5 = QLabel("🔍 Kontrol Edilen:")
        lbl5.setStyleSheet(f"color: {self.theme.get('text')};")
        giris_layout.addWidget(lbl5, 0, 0)
        self.kontrol_edilen_input = QSpinBox()
        self.kontrol_edilen_input.setRange(0, 999999)
        self.kontrol_edilen_input.setStyleSheet(self._input_style())
        self.kontrol_edilen_input.valueChanged.connect(self._hesapla_adetler)
        giris_layout.addWidget(self.kontrol_edilen_input, 0, 1)
        
        # Kalan (bakiye)
        lbl_kalan = QLabel("📦 Kalan Bakiye:")
        lbl_kalan.setStyleSheet(f"color: {self.theme.get('text')};")
        giris_layout.addWidget(lbl_kalan, 0, 2)
        self.kalan_label = QLabel("0")
        self.kalan_label.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-weight: bold; font-size: 16px;")
        giris_layout.addWidget(self.kalan_label, 0, 3)
        
        # Sağlam adet
        lbl6 = QLabel("✅ Sağlam Adet:")
        lbl6.setStyleSheet(f"color: {self.theme.get('text')};")
        giris_layout.addWidget(lbl6, 1, 0)
        self.saglam_input = QSpinBox()
        self.saglam_input.setRange(0, 999999)
        self.saglam_input.setStyleSheet(self._input_style())
        self.saglam_input.valueChanged.connect(self._hesapla_hatali)
        giris_layout.addWidget(self.saglam_input, 1, 1)
        
        # Hatalı adet (otomatik)
        lbl7 = QLabel("❌ Hatalı Adet:")
        lbl7.setStyleSheet(f"color: {self.theme.get('text')};")
        giris_layout.addWidget(lbl7, 1, 2)
        self.hatali_label = QLabel("0")
        self.hatali_label.setStyleSheet(f"color: {self.theme.get('danger', '#ef4444')}; font-weight: bold; font-size: 18px;")
        giris_layout.addWidget(self.hatali_label, 1, 3)
        
        # Kalınlık ölçüm
        lbl8 = QLabel("📏 Kalınlık (µm):")
        lbl8.setStyleSheet(f"color: {self.theme.get('text')};")
        giris_layout.addWidget(lbl8, 2, 0)
        self.kalinlik_input = QDoubleSpinBox()
        self.kalinlik_input.setRange(0, 9999)
        self.kalinlik_input.setDecimals(2)
        self.kalinlik_input.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.kalinlik_input, 2, 1)
        
        # Kontrol eden
        lbl9 = QLabel("👤 Kontrol Eden:")
        lbl9.setStyleSheet(f"color: {self.theme.get('text')};")
        giris_layout.addWidget(lbl9, 2, 2)
        self.kontrolcu_combo = QComboBox()
        self.kontrolcu_combo.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.kontrolcu_combo, 2, 3)
        
        sag_layout.addWidget(giris_frame)
        
        # Hata listesi
        hata_header = QHBoxLayout()
        hata_lbl = QLabel("⚠️ Hata Detayları:")
        hata_lbl.setStyleSheet(f"color: {self.theme.get('text')};")
        hata_header.addWidget(hata_lbl)
        hata_header.addStretch()
        
        hata_ekle_btn = QPushButton("+ Hata Ekle")
        hata_ekle_btn.setStyleSheet(f"background: {self.theme.get('warning', '#f59e0b')}; color: white; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold;")
        hata_ekle_btn.clicked.connect(self._hata_ekle)
        hata_header.addWidget(hata_ekle_btn)
        sag_layout.addLayout(hata_header)
        
        self.hata_table = QTableWidget()
        self.hata_table.setColumnCount(4)
        self.hata_table.setHorizontalHeaderLabels(["ID", "Hata Türü", "Adet", "Sil"])
        self.hata_table.setColumnHidden(0, True)
        self.hata_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.hata_table.setColumnWidth(2, 80)
        self.hata_table.setColumnWidth(3, 60)
        self.hata_table.setMaximumHeight(150)
        self.hata_table.setStyleSheet(self._table_style())
        self.hata_table.verticalHeader().setVisible(False)
        sag_layout.addWidget(self.hata_table)
        
        # Not
        not_lbl = QLabel("📝 Not:")
        not_lbl.setStyleSheet(f"color: {self.theme.get('text')};")
        sag_layout.addWidget(not_lbl)
        self.not_input = QTextEdit()
        self.not_input.setMaximumHeight(60)
        self.not_input.setStyleSheet(self._input_style())
        self.not_input.setPlaceholderText("Kontrol notu...")
        sag_layout.addWidget(self.not_input)
        
        # Kaydet ve Etiket butonları
        btn_layout = QHBoxLayout()
        
        self.kaydet_btn = QPushButton("💾 Kaydet")
        self.kaydet_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_muted')};
            }}
        """)
        self.kaydet_btn.clicked.connect(self._kaydet)
        self.kaydet_btn.setEnabled(False)
        btn_layout.addWidget(self.kaydet_btn)
        
        self.etiket_btn = QPushButton("🏷️ Etiket Bas")
        self.etiket_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#6366f1')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_muted')};
            }}
        """)
        self.etiket_btn.clicked.connect(self._bas_etiket_manual)
        self.etiket_btn.setEnabled(True)  # ✅ Her zaman aktif (kuyruktan basabilir)
        btn_layout.addWidget(self.etiket_btn)
        
        sag_layout.addLayout(btn_layout)
        
        splitter.addWidget(sag_widget)
        splitter.setSizes([400, 500])
        
        layout.addWidget(splitter, 1)
    
    def _button_style(self):
        return f"QPushButton {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 16px; }}"
    
    def _input_style(self):
        return f"""
            background: {self.theme.get('bg_input', '#2d3548')};
            border: 1px solid {self.theme.get('border', '#3d4454')};
            border-radius: 6px;
            padding: 8px 12px;
            color: {self.theme.get('text', '#fff')};
        """
    
    def _table_style(self):
        return f"""
            QTableWidget {{
                background: {self.theme.get('bg_card', '#242938')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border', '#3d4454')};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QHeaderView::section {{
                background: {self.theme.get('bg_hover', '#2d3548')};
                color: {self.theme.get('text', '#fff')};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """
    
    def _update_time(self):
        self.saat_label.setText(QTime.currentTime().toString("HH:mm:ss"))
    
    def _load_hata_turleri(self):
        """Hata türlerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.hata_turleri WHERE aktif_mi = 1 ORDER BY sira_no, kod")
            self.hata_turleri = [{'id': r[0], 'kod': r[1], 'ad': r[2]} for r in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"Hata türleri yüklenemedi: {e}")
    
    def _load_kontrolcular(self):
        """Kontrol eden personel listesi"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ad + ' ' + soyad as ad_soyad 
                FROM ik.personeller 
                WHERE aktif_mi = 1 
                ORDER BY ad, soyad
            """)
            self.kontrolcu_combo.clear()
            self.kontrolcu_combo.addItem("-- Seçin --", None)
            for row in cursor.fetchall():
                self.kontrolcu_combo.addItem(row[1], row[0])
            conn.close()
        except Exception as e:
            print(f"Kontrolcüler yüklenemedi: {e}")
    
    def _load_data(self):
        """Kontrol bekleyen lotları yükle - Atanan görevler (ATANDI, DEVAM_EDIYOR)"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # kalite.kontrol_is_emirleri tablosundan ATANDI ve DEVAM_EDIYOR durumundaki görevleri getir
            cursor.execute("""
                SELECT ie.id, ie.is_emri_no, ie.stok_adi, ie.lot_no, 
                       kie.kontrol_miktar as adet,
                       ie.stok_kodu,
                       kie.id as kontrol_id, 
                       p.ad + ' ' + p.soyad as atanan_personel,
                       kie.personel_id as atanan_personel_id,
                       kie.durum
                FROM kalite.kontrol_is_emirleri kie
                INNER JOIN siparis.is_emirleri ie ON kie.is_emri_id = ie.id
                LEFT JOIN ik.personeller p ON kie.personel_id = p.uuid
                WHERE kie.durum IN ('ATANDI', 'DEVAM_EDIYOR')
                ORDER BY 
                    CASE WHEN kie.durum = 'DEVAM_EDIYOR' THEN 0 
                         WHEN kie.durum = 'ATANDI' THEN 1 
                         ELSE 2 END,
                    kie.atama_tarihi ASC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            self.bekleyen_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                # ID (gizli)
                self.bekleyen_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                
                # İş Emri No
                ie_item = QTableWidgetItem(row[1] or '')
                ie_item.setFont(QFont("", -1, QFont.Bold))
                self.bekleyen_table.setItem(i, 1, ie_item)
                
                # Ürün
                self.bekleyen_table.setItem(i, 2, QTableWidgetItem((row[2] or '')[:25]))
                
                # Lot No
                lot_item = QTableWidgetItem(row[3] or '')
                lot_item.setForeground(QColor(self.theme.get('primary', '#6366f1')))
                self.bekleyen_table.setItem(i, 3, lot_item)
                
                # Adet
                adet_item = QTableWidgetItem(f"{int(row[4] or 0):,}")
                adet_item.setTextAlignment(Qt.AlignCenter)
                self.bekleyen_table.setItem(i, 4, adet_item)
                
                # Atanan Personel
                atanan = row[7] or '-'
                atanan_item = QTableWidgetItem(atanan[:15] if atanan != '-' else '-')
                if atanan != '-':
                    atanan_item.setForeground(QColor(self.theme.get('success', '#22c55e')))
                    atanan_item.setFont(QFont("", -1, QFont.Bold))
                self.bekleyen_table.setItem(i, 5, atanan_item)
                
                # Durum
                durum = row[9] or 'BEKLIYOR'
                durum_item = QTableWidgetItem(durum)
                if durum == 'DEVAM_EDIYOR':
                    durum_item.setForeground(QColor(self.theme.get('warning', '#f59e0b')))
                elif durum == 'ATANDI':
                    durum_item.setForeground(QColor(self.theme.get('success', '#22c55e')))
                else:
                    durum_item.setForeground(QColor(self.theme.get('text_muted', '#8a94a6')))
                self.bekleyen_table.setItem(i, 6, durum_item)
                
                # İşlem Butonu
                kontrol_id = row[6]
                atanan_personel = row[7]
                atanan_personel_id = row[8]

                gorev_data = {
                    'id': row[0], 'is_emri_no': row[1], 'urun_adi': row[2],
                    'lot_no': row[3], 'toplam_adet': int(row[4] or 0),
                    'kontrol_adet': int(row[4] or 0), 'urun_kodu': row[5],
                    'kontrol_id': kontrol_id, 'atanan_personel': atanan_personel,
                    'atanan_personel_id': atanan_personel_id
                }

                if atanan_personel:
                    widget = self.create_action_buttons([
                        ("🔐", "Başla", lambda checked, gd=gorev_data: self._on_kontrol_click(gd), "success"),
                    ])
                else:
                    widget = self.create_action_buttons([
                        ("🔍", "Kontrol", lambda checked, gd=gorev_data: self._on_kontrol_click(gd), "view"),
                    ])
                self.bekleyen_table.setCellWidget(i, 7, widget)
                self.bekleyen_table.setRowHeight(i, 38)
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yüklenemedi: {e}")
    
    def _on_kontrol_click(self, gorev_data):
        """Kontrol butonuna tıklandığında - atanmışsa kart okut"""
        if gorev_data.get('atanan_personel'):
            giris_dlg = PersonelGirisDialog(self.theme, gorev_data, self)
            if giris_dlg.exec() != QDialog.Accepted or not giris_dlg.personel_data:
                return
            
            if gorev_data.get('kontrol_id'):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE kalite.kontrol_is_emirleri 
                        SET durum = 'DEVAM_EDIYOR', baslama_tarihi = GETDATE() 
                        WHERE id = ?
                    """, (gorev_data['kontrol_id'],))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"Durum güncelleme hatası: {e}")
            
            self._set_kontrolcu(giris_dlg.personel_data)
        
        self._sec_lot_from_gorev(gorev_data)
    
    def _set_kontrolcu(self, personel_data):
        """Kontrolcü combo'sunda personeli seç"""
        ad_soyad = personel_data.get('ad_soyad', '')
        for i in range(self.kontrolcu_combo.count()):
            if ad_soyad in self.kontrolcu_combo.itemText(i):
                self.kontrolcu_combo.setCurrentIndex(i)
                return
        personel_id = personel_data.get('id')
        for i in range(self.kontrolcu_combo.count()):
            if self.kontrolcu_combo.itemData(i) == personel_id:
                self.kontrolcu_combo.setCurrentIndex(i)
                return
    
    def _sec_lot_from_gorev(self, gorev_data):
        """Görev verisinden formu doldur"""
        toplam_adet = gorev_data.get('toplam_adet', 0) or gorev_data.get('kontrol_adet', 0)
        
        self.secili_is_emri = {
            'id': gorev_data['id'],
            'is_emri_no': gorev_data.get('is_emri_no', ''),
            'urun_adi': gorev_data.get('urun_adi', ''),
            'lot_no': gorev_data.get('lot_no', ''),
            'toplam_adet': toplam_adet,
            'urun_kodu': gorev_data.get('urun_kodu', ''),
            'kontrol_id': gorev_data.get('kontrol_id'),
            'atanan_personel_id': gorev_data.get('atanan_personel_id')
        }
        
        self.lbl_is_emri.setText(gorev_data.get('is_emri_no', '') or '-')
        self.lbl_urun.setText((gorev_data.get('urun_adi', '') or '-')[:25])
        self.lbl_lot.setText(gorev_data.get('lot_no', '') or '-')
        self.lbl_toplam.setText(f"{toplam_adet:,}")
        
        self.kontrol_edilen_input.setMaximum(toplam_adet)
        self.kontrol_edilen_input.setValue(toplam_adet)
        
        self.saglam_input.setMaximum(toplam_adet)
        self.saglam_input.setValue(toplam_adet)
        
        self.kalan_label.setText("0")
        self.hatali_label.setText("0")
        self.kalinlik_input.setValue(0)
        self.not_input.clear()
        
        self.hata_listesi = []
        self._refresh_hata_table()
        
        self.kaydet_btn.setEnabled(True)
    
    def _sec_lot(self, is_emri_id: int, data: tuple):
        """Lot seç ve formu doldur"""
        toplam_adet = int(data[4] or 0)
        
        self.secili_is_emri = {
            'id': data[0],
            'is_emri_no': data[1],
            'urun_adi': data[2],
            'lot_no': data[3],
            'toplam_adet': toplam_adet,
            'urun_kodu': data[6]
        }
        
        self.lbl_is_emri.setText(data[1] or '-')
        self.lbl_urun.setText((data[2] or '-')[:25])
        self.lbl_lot.setText(data[3] or '-')
        self.lbl_toplam.setText(str(toplam_adet))
        
        # Kontrol edilen varsayılan = toplam
        self.kontrol_edilen_input.setMaximum(toplam_adet)
        self.kontrol_edilen_input.setValue(toplam_adet)
        
        self.saglam_input.setMaximum(toplam_adet)
        self.saglam_input.setValue(toplam_adet)
        
        self.kalan_label.setText("0")
        self.hatali_label.setText("0")
        self.kalinlik_input.setValue(0)
        self.not_input.clear()
        
        self.hata_listesi = []
        self._refresh_hata_table()
        
        self.kaydet_btn.setEnabled(True)
    
    def _hesapla_adetler(self):
        """Kontrol edilen değiştiğinde kalan ve sağlamı güncelle"""
        if not self.secili_is_emri:
            return
        toplam = self.secili_is_emri.get('toplam_adet', 0)
        kontrol_edilen = self.kontrol_edilen_input.value()
        kalan = toplam - kontrol_edilen
        self.kalan_label.setText(str(max(0, kalan)))
        
        # Sağlam maksimumu güncelle
        self.saglam_input.setMaximum(kontrol_edilen)
        if self.saglam_input.value() > kontrol_edilen:
            self.saglam_input.setValue(kontrol_edilen)
        
        self._hesapla_hatali()
    
    def _hesapla_hatali(self):
        """Hatalı adedi hesapla = kontrol edilen - sağlam"""
        if not self.secili_is_emri:
            return
        kontrol_edilen = self.kontrol_edilen_input.value()
        saglam = self.saglam_input.value()
        hatali = kontrol_edilen - saglam
        self.hatali_label.setText(str(max(0, hatali)))
    
    def _hata_ekle(self):
        """Hata ekle dialog'u"""
        if not self.secili_is_emri:
            QMessageBox.warning(self, "Uyarı", "Önce bir lot seçin!")
            return
        
        if not self.hata_turleri:
            QMessageBox.warning(self, "Uyarı", "Hata türleri tanımlanmamış!")
            return
        
        dlg = HataEkleDialog(self.theme, self.hata_turleri, self)
        if dlg.exec() == QDialog.Accepted:
            hata = dlg.get_data()
            self.hata_listesi.append(hata)
            self._refresh_hata_table()
            self._update_hatali_toplam()
    
    def _refresh_hata_table(self):
        """Hata tablosunu güncelle"""
        self.hata_table.setRowCount(len(self.hata_listesi))
        for i, hata in enumerate(self.hata_listesi):
            self.hata_table.setItem(i, 0, QTableWidgetItem(str(hata.get('hata_turu_id', ''))))
            self.hata_table.setItem(i, 1, QTableWidgetItem(hata.get('hata_adi', '')))
            
            adet_item = QTableWidgetItem(str(hata.get('adet', 0)))
            adet_item.setTextAlignment(Qt.AlignCenter)
            self.hata_table.setItem(i, 2, adet_item)
            
            widget = self.create_action_buttons([
                ("🗑️", "Sil", lambda checked, idx=i: self._sil_hata(idx), "delete"),
            ])
            self.hata_table.setCellWidget(i, 3, widget)
            self.hata_table.setRowHeight(i, 42)

    def _sil_hata(self, idx: int):
        """Hata sil"""
        if 0 <= idx < len(self.hata_listesi):
            self.hata_listesi.pop(idx)
            self._refresh_hata_table()
            self._update_hatali_toplam()
    
    def _update_hatali_toplam(self):
        """Hata adetlerinden hatalı toplamı güncelle"""
        toplam_hata = sum(h.get('adet', 0) for h in self.hata_listesi)
        if self.secili_is_emri:
            toplam = self.secili_is_emri.get('toplam_adet', 0)
            saglam = toplam - toplam_hata
            self.saglam_input.setValue(max(0, saglam))
            self.hatali_label.setText(str(toplam_hata))
    
    def _kaydet(self):
        """Kontrol kaydını kaydet ve etiket bas"""
        if not self.secili_is_emri:
            return
        
        kontrolcu_id = self.kontrolcu_combo.currentData()
        if not kontrolcu_id:
            QMessageBox.warning(self, "Uyarı", "Kontrol eden seçin!")
            return
        
        kontrol_edilen = self.kontrol_edilen_input.value()
        saglam = self.saglam_input.value()
        hatali = kontrol_edilen - saglam
        toplam = self.secili_is_emri.get('toplam_adet', 0)
        kalan = toplam - kontrol_edilen
        
        if kontrol_edilen == 0:
            QMessageBox.warning(self, "Uyarı", "Kontrol edilen adet 0 olamaz!")
            return
        
        # Hata adetleri toplamı kontrol
        hata_toplam = sum(h.get('adet', 0) for h in self.hata_listesi)
        if hatali > 0 and hata_toplam != hatali:
            QMessageBox.warning(self, "Uyarı", f"Hata adetleri toplamı ({hata_toplam}) hatalı adet ({hatali}) ile eşleşmiyor!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # ========== FINAL KONTROL KAYDI (FKK - Son Ürün Kontrolü) ==========
            cursor.execute("""
                INSERT INTO kalite.final_kontrol 
                (is_emri_id, lot_no, kontrol_miktar, saglam_adet, hatali_adet, 
                 sonuc, kontrol_tarihi, olusturma_tarihi, guncelleme_tarihi)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, GETDATE(), GETDATE(), GETDATE())
            """, (
                self.secili_is_emri['id'],
                self.secili_is_emri['lot_no'],
                kontrol_edilen,
                saglam,
                hatali,
                'KABUL' if hatali == 0 else ('RED' if saglam == 0 else 'KISMI')
            ))
            
            # Son eklenen ID'yi al
            kontrol_id = cursor.fetchone()[0]
            print(f"✅ Final kontrol kaydı oluşturuldu (ID: {kontrol_id})")
            # ===================================================================
            
            # Hata kayıtları (final_kontrol_hatalar tablosuna)
            for hata in self.hata_listesi:
                try:
                    cursor.execute("""
                        INSERT INTO kalite.final_kontrol_hatalar (final_kontrol_id, hata_turu_id, adet)
                        VALUES (?, ?, ?)
                    """, (kontrol_id, hata['hata_turu_id'], hata['adet']))
                except Exception as hata_err:
                    print(f"⚠️ Final kontrol hata kaydı hatası: {hata_err}")
            
            # Sonuç belirleme
            if hatali == 0:
                sonuc = 'ONAY'
            elif saglam == 0:
                sonuc = 'RED'
            else:
                sonuc = 'KISMI'
            
            # Eğer atanmış görev varsa kontrol_is_emirleri tablosunu da güncelle
            kontrol_is_emri_id = self.secili_is_emri.get('kontrol_id')
            if kontrol_is_emri_id:
                cursor.execute("""
                    UPDATE kalite.kontrol_is_emirleri 
                    SET durum = 'TAMAMLANDI', bitis_tarihi = GETDATE(),
                        kontrol_miktar = ?, saglam_miktar = ?, hatali_miktar = ?,
                        sonuc = ?, notlar = ?
                    WHERE id = ?
                """, (kontrol_edilen, saglam, hatali, sonuc, self.not_input.toPlainText(), kontrol_is_emri_id))
            
            # Depo ID'lerini bul: SEVK (sağlam) ve RED (hatalı)
            # Hareket motorunu başlat (AYNI connection ile - lock çakışması olmasın)
            from core.hareket_motoru import HareketMotoru
            motor = HareketMotoru(conn)  # ✅ AYNI CONNECTION!
            
            # SEVK deposunu bul
            sevk_depo_id = motor.get_depo_by_tip('SVK')
            if not sevk_depo_id:
                cursor.execute("SELECT TOP 1 id FROM tanim.depolar WHERE kod LIKE '%SEVK%' OR kod = 'SEV-01' AND aktif_mi = 1")
                row = cursor.fetchone()
                sevk_depo_id = row[0] if row else None
            print(f"DEBUG: SEVK depo_id={sevk_depo_id}")
            
            # RED deposunu bul
            red_depo_id = motor.get_depo_by_tip('RED')
            if not red_depo_id:
                cursor.execute("SELECT TOP 1 id FROM tanim.depolar WHERE kod = 'RED' AND aktif_mi = 1")
                row = cursor.fetchone()
                red_depo_id = row[0] if row else None
            print(f"DEBUG: RED depo_id={red_depo_id}")
            
            lot_no = self.secili_is_emri.get('lot_no', '')
            is_emri_id = self.secili_is_emri['id']
            urun_kodu = self.secili_is_emri.get('urun_kodu', '') or ''
            urun_adi = self.secili_is_emri.get('urun_adi', '') or ''
            
            print(f"DEBUG: lot_no={lot_no}, urun_kodu={urun_kodu}, sevk_depo_id={sevk_depo_id}, saglam={saglam}, hatali={hatali}")
            
            # urun_id bul veya oluştur
            urun_id = None
            if urun_kodu:
                cursor.execute("SELECT id FROM stok.urunler WHERE urun_kodu = ?", (urun_kodu,))
                urun_row = cursor.fetchone()
                
                if urun_row:
                    urun_id = urun_row[0]
                    print(f"DEBUG: Mevcut ürün bulundu - urun_id={urun_id}")
                else:
                    cursor.execute("""
                        INSERT INTO stok.urunler (uuid, urun_kodu, urun_adi, urun_tipi, birim_id, aktif_mi, 
                                                 olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                        OUTPUT INSERTED.id
                        VALUES (NEWID(), ?, ?, 'MAMUL', 1, 1, GETDATE(), GETDATE(), 0)
                    """, (urun_kodu, urun_adi))
                    urun_id = cursor.fetchone()[0]
                    print(f"DEBUG: Yeni ürün oluşturuldu - urun_id={urun_id}")
            else:
                print("DEBUG: stok_kodu BOŞ! Varsayılan ürün aranıyor...")
                # stok_kodu boşsa is_emri_no'dan oluştur
                stok_kodu = f"URN-{is_emri_id}"
                cursor.execute("""
                    INSERT INTO stok.urunler (uuid, urun_kodu, urun_adi, urun_tipi, birim_id, aktif_mi, 
                                             olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                    OUTPUT INSERTED.id
                    VALUES (NEWID(), ?, ?, 'MAMUL', 1, 1, GETDATE(), GETDATE(), 0)
                """, (stok_kodu, stok_adi or f"Ürün {is_emri_id}"))
                urun_id = cursor.fetchone()[0]
                print(f"DEBUG: Varsayılan ürün oluşturuldu - urun_id={urun_id}, stok_kodu={stok_kodu}")
            
            # Sağlam ürünler -> SEVK DEPO (Hareket Motoru ile)
            # NOT: Sadece sağlam miktarı transfer et, kalan FKK'da kalmalı
            if saglam > 0 and sevk_depo_id:
                print(f"DEBUG: Sevk depoya transfer yapılıyor... lot_no={lot_no}, sevk_depo_id={sevk_depo_id}, saglam={saglam}")
                
                # Önce FKK deposundaki mevcut bakiyeyi kontrol et
                cursor.execute("""
                    SELECT sb.miktar, sb.depo_id 
                    FROM stok.stok_bakiye sb
                    INNER JOIN tanim.depolar d ON sb.depo_id = d.id
                    WHERE sb.lot_no = ? AND d.kod = 'FKK'
                """, (lot_no,))
                bakiye_row = cursor.fetchone()
                mevcut_miktar = bakiye_row[0] if bakiye_row else 0
                mevcut_depo = bakiye_row[1] if bakiye_row else None
                print(f"DEBUG: Mevcut bakiye (FKK) - miktar={mevcut_miktar}, depo_id={mevcut_depo}")
                
                # Sağlam miktarı için yeni lot oluştur ve SEV-01'e gönder
                sevk_lot = f"{lot_no}-SEV"
                
                sevk_sonuc = motor.stok_giris(
                    urun_id=urun_id,
                    miktar=saglam,
                    lot_no=sevk_lot,
                    depo_id=sevk_depo_id,
                    urun_kodu=urun_kodu,  # DÜZELTME
                    urun_adi=urun_adi,    # DÜZELTME
                    kalite_durumu='ONAYLANDI',
                    durum_kodu='SEVK_HAZIR',  # YENİ!
                    aciklama=f"Final kalite onay - Sağlam: {saglam}"
                )
                
                if sevk_sonuc.basarili:
                    print(f"DEBUG: ✓ Sevk depoya giriş başarılı - sevk_lot={sevk_lot}")
                    
                    # Orijinal lot'tan kontrol edilen toplam miktarı düş (sağlam + hatalı)
                    kontrol_edilen = saglam + hatali
                    yeni_miktar = mevcut_miktar - kontrol_edilen
                    
                    # FKK depo ID'sini al
                    cursor.execute("SELECT id FROM tanim.depolar WHERE kod = 'FKK'")
                    fkk_row = cursor.fetchone()
                    fkk_depo_id = fkk_row[0] if fkk_row else mevcut_depo
                    
                    if yeni_miktar > 0:
                        # Kalan miktar var, FKK'da bırak
                        cursor.execute("""
                            UPDATE stok.stok_bakiye 
                            SET miktar = ?,
                                durum_kodu = 'FKK_BEKLIYOR'
                            WHERE lot_no = ? AND depo_id = ?
                        """, (yeni_miktar, lot_no, fkk_depo_id))
                        print(f"DEBUG: Orijinal lot güncellendi - kalan miktar={yeni_miktar}, depo_id={fkk_depo_id}")
                    else:
                        # Kalan miktar yok, orijinal lot'u sıfırla
                        cursor.execute("""
                            UPDATE stok.stok_bakiye 
                            SET miktar = 0, 
                                kalite_durumu = 'TAMAMLANDI',
                                durum_kodu = 'SEVK_EDILDI'
                            WHERE lot_no = ? AND depo_id = ?
                        """, (lot_no, fkk_depo_id))
                        print(f"DEBUG: Orijinal lot tamamlandı - miktar=0, depo_id={fkk_depo_id}")
                else:
                    print(f"DEBUG: ✗ Sevk giriş hatası: {sevk_sonuc.mesaj}")
            else:
                print(f"DEBUG: Sevk depoya kayıt YAPILMADI! saglam={saglam}, sevk_depo_id={sevk_depo_id}")
            
            # Hatalı ürünler -> RED DEPO + kalite.uretim_redler tablosuna kayıt (Hareket Motoru ile)
            if hatali > 0 and red_depo_id:
                lot_prefix = '-'.join(lot_no.split('-')[:3]) if lot_no else ''
                red_lot = f"{lot_prefix}-RED" if lot_prefix else f"RED-{is_emri_id}"
                
                # Hareket motoru ile red deposuna giriş
                red_sonuc = motor.stok_giris(
                    urun_id=urun_id,
                    miktar=hatali,
                    lot_no=red_lot,
                    depo_id=red_depo_id,
                    urun_kodu=urun_kodu,  # DÜZELTME
                    urun_adi=urun_adi,    # DÜZELTME
                    kalite_durumu='REDDEDILDI',
                    durum_kodu='RED',  # YENİ!
                    aciklama=f"Final kalite red - Hatalı: {hatali}"
                )
                
                if red_sonuc.basarili:
                    print(f"DEBUG: ✓ Red depoya stok girişi başarılı - red_lot={red_lot}")
                    # NOT: Miktar zaten yukarıda düşüldü (sağlam+hatalı)
                else:
                    print(f"DEBUG: ✗ Red stok girişi hatası: {red_sonuc.mesaj}")
                
                # kalite.uretim_redler tablosuna kayıt ekle (kalite_red ekranında görünmesi için)
                # Her hata türü için ayrı kayıt oluştur
                try:
                    if self.hata_listesi:
                        for hata in self.hata_listesi:
                            cursor.execute("""
                                INSERT INTO kalite.uretim_redler 
                                (is_emri_id, lot_no, red_miktar, hata_turu_id, kontrol_id, red_tarihi, 
                                 kontrol_eden_id, durum, aciklama, olusturma_tarihi)
                                VALUES (?, ?, ?, ?, ?, GETDATE(), ?, 'BEKLIYOR', ?, GETDATE())
                            """, (is_emri_id, lot_no, hata.get('adet', 0), hata.get('hata_turu_id'), 
                                  kontrol_id, kontrolcu_id, self.not_input.toPlainText()))
                    else:
                        # Hata listesi boşsa toplam hatalı miktarı kaydet
                        cursor.execute("""
                            INSERT INTO kalite.uretim_redler 
                            (is_emri_id, lot_no, red_miktar, kontrol_id, red_tarihi, 
                             kontrol_eden_id, durum, aciklama, olusturma_tarihi)
                            VALUES (?, ?, ?, ?, GETDATE(), ?, 'BEKLIYOR', ?, GETDATE())
                        """, (is_emri_id, lot_no, hatali, kontrol_id, kontrolcu_id, 
                              self.not_input.toPlainText()))
                except Exception as red_err:
                    print(f"Üretim red kaydı hatası (tablo olmayabilir): {red_err}")
            
            # İş emri durumunu ve miktarını güncelle
            if kalan == 0:
                # Tamamı kontrol edildi
                if hatali == 0:
                    yeni_durum = 'ONAYLANDI'
                else:
                    yeni_durum = 'KISMI_RED'
                
                cursor.execute("""
                    UPDATE siparis.is_emirleri 
                    SET durum = ?, 
                        toplam_miktar = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (yeni_durum, saglam, self.secili_is_emri['id']))
            else:
                # Kısmi kontrol - kalan miktar var, beklemede kal
                cursor.execute("""
                    UPDATE siparis.is_emirleri 
                    SET toplam_miktar = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (kalan, self.secili_is_emri['id']))
            
            # Etiket verilerini kaydet (aynı connection ve transaction içinde)
            if saglam > 0:
                try:
                    # Müşteri bilgisini al (aynı cursor ile)
                    cursor.execute("""
                        SELECT ie.cari_unvani
                        FROM siparis.is_emirleri ie
                        WHERE ie.id = ?
                    """, (is_emri_id,))
                    row = cursor.fetchone()
                    musteri = row[0] if row else ''
                    
                    # Kontrolcü
                    kontrolcu_adi = self.kontrolcu_combo.currentText()
                    if kontrolcu_adi.startswith("--"):
                        kontrolcu_adi = ""
                    
                    # Etiket kuyruğuna ekle (aynı transaction içinde)
                    sevk_lot = f"{lot_no}-SEV"
                    cursor.execute("""
                        INSERT INTO kalite.etiket_kuyrugu (
                            proses_kontrol_id, lot_no, stok_kodu, stok_adi,
                            musteri, miktar, kontrolcu_adi,
                            kontrol_tarihi, basildi_mi, olusturma_tarihi
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), 0, GETDATE())
                    """, (
                        kontrol_id, sevk_lot, urun_kodu, urun_adi,
                        musteri, saglam, kontrolcu_adi
                    ))
                    print(f"DEBUG: ✓ Etiket kuyruğuna eklendi - lot={sevk_lot}")
                except Exception as etiket_err:
                    print(f"⚠️ Etiket kuyruğu hatası (görmezden gelindi): {etiket_err}")
            
            # Connection'ı commit et ve kapat (tek seferde tüm transaction)
            conn.commit()
            conn.close()
            
            # Başarı mesajı
            msg = f"✅ Kontrol kaydedildi!\n\n"
            msg += f"Kontrol Edilen: {kontrol_edilen}\n"
            msg += f"Sağlam: {saglam}\n"
            msg += f"Hatalı: {hatali}\n"
            msg += f"Kalan Bakiye: {kalan}\n\n"
            
            if saglam > 0:
                msg += f"✓ {saglam} adet SEVK deposuna aktarıldı\n"
                msg += f"  Lot: {lot_no}-SEV\n\n"
            
            if hatali > 0:
                msg += f"✗ {hatali} adet RED deposuna aktarıldı\n"
                msg += f"  Lot: {'-'.join(lot_no.split('-')[:3])}-RED\n\n"
            
            msg += f"FKK'da kalan: {kalan} adet"
            
            QMessageBox.information(self, "✅ Başarılı", msg)
            
            # Formu temizle
            self.secili_is_emri = None
            self.hata_listesi = []
            self._refresh_hata_table()
            self.kaydet_btn.setEnabled(False)
            # etiket_btn her zaman aktif kalır (kuyruktan basabilir)
            self.lbl_is_emri.setText("-")
            self.lbl_urun.setText("-")
            self.lbl_lot.setText("-")
            self.lbl_toplam.setText("-")
            
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt başarısız: {e}")
    
    def _bas_etiket_manual(self):
        """Manuel etiket basma - kuyruktaki etiketlerden seç"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Bekleyen etiketleri getir
            cursor.execute("""
                SELECT 
                    id, lot_no, stok_kodu, stok_adi, musteri, miktar,
                    kontrolcu_adi, kontrol_tarihi, basim_sayisi
                FROM kalite.etiket_kuyrugu
                WHERE basildi_mi = 0
                ORDER BY kontrol_tarihi DESC
            """)
            
            etiketler = cursor.fetchall()
            conn.close()
            
            if not etiketler:
                QMessageBox.information(self, "Bilgi", "Bekleyen etiket yok!")
                return
            
            # Etiket seçim dialog'u
            dlg = QDialog(self)
            dlg.setWindowTitle("🏷️ Etiket Seç")
            dlg.setMinimumSize(600, 400)
            dlg.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main')}; }}")
            
            layout = QVBoxLayout(dlg)
            
            lbl = QLabel("Basılacak etiketi seçin:")
            lbl.setStyleSheet(f"color: {self.theme.get('text')}; font-size: 14px; font-weight: bold;")
            layout.addWidget(lbl)
            
            liste = QListWidget()
            liste.setStyleSheet(f"""
                QListWidget {{
                    background: {self.theme.get('bg_card')};
                    color: {self.theme.get('text')};
                    border: 1px solid {self.theme.get('border')};
                    border-radius: 8px;
                    padding: 8px;
                }}
                QListWidget::item {{
                    padding: 12px;
                    border-bottom: 1px solid {self.theme.get('border')};
                }}
                QListWidget::item:selected {{
                    background: {self.theme.get('primary')};
                    color: white;
                }}
            """)
            
            for etiket in etiketler:
                etiket_id, lot_no, stok_kodu, stok_adi, musteri, miktar, kontrolcu, tarih, basim = etiket
                tarih_str = tarih.strftime("%d.%m.%Y %H:%M") if tarih else "-"
                
                item_text = f"📦 {lot_no}\n"
                item_text += f"   {stok_kodu} - {stok_adi[:30]}\n"
                item_text += f"   Müşteri: {musteri[:30]} | {miktar} adet\n"
                item_text += f"   Kontrol: {kontrolcu} | {tarih_str}"
                if basim > 0:
                    item_text += f" | Basım: {basim}x"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, etiket_id)
                liste.addItem(item)
            
            layout.addWidget(liste)
            
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btn_box.setStyleSheet(f"""
                QPushButton {{
                    background: {self.theme.get('primary')};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                }}
            """)
            btn_box.accepted.connect(dlg.accept)
            btn_box.rejected.connect(dlg.reject)
            layout.addWidget(btn_box)
            
            if dlg.exec() != QDialog.Accepted:
                return
            
            secili_item = liste.currentItem()
            if not secili_item:
                return
            
            etiket_id = secili_item.data(Qt.UserRole)
            
            # Etiket verilerini al
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    lot_no, stok_kodu, stok_adi, musteri, miktar, kontrolcu_adi
                FROM kalite.etiket_kuyrugu
                WHERE id = ?
            """, (etiket_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return
            
            lot_no, stok_kodu, stok_adi, musteri, miktar, kontrolcu = row
            
            # Etiket verisi
            etiket_data = {
                'musteri': musteri or '',
                'urun': stok_adi or '',
                'lot_no': lot_no or '',
                'adet': miktar,
                'tarih': datetime.now().strftime('%d.%m.%Y'),
                'kontrolcu': kontrolcu or '',
                'stok_kodu': stok_kodu or ''
            }
            
            # Etiket dialog'unu göster
            dlg_etiket = EtiketOnizlemeDialog(self.theme, etiket_data, self)
            if dlg_etiket.exec() == QDialog.Accepted:
                # Basım sayısını artır
                cursor.execute("""
                    UPDATE kalite.etiket_kuyrugu 
                    SET basim_sayisi = basim_sayisi + 1,
                        basim_tarihi = GETDATE(),
                        basildi_mi = 1
                    WHERE id = ?
                """, (etiket_id,))
                conn.commit()
                QMessageBox.information(self, "✅ Başarılı", "Etiket basıldı!")
            
            conn.close()
            
        except Exception as e:
            QMessageBox.warning(self, "⚠️ Etiket Hatası", f"Etiket basılamadı:\n{str(e)}")
    
    def _bas_etiket(self):
        """Etiket bas - Godex EZPL formatı"""
        if not self.secili_is_emri:
            return None
        
        try:
            # Müşteri bilgisini al
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ie.cari_unvani
                FROM siparis.is_emirleri ie
                WHERE ie.id = ?
            """, (self.secili_is_emri['id'],))
            row = cursor.fetchone()
            musteri = row[0] if row else ''
            conn.close()
            
            # Kontrol eden adı
            kontrolcu = self.kontrolcu_combo.currentText()
            if kontrolcu.startswith("--"):
                kontrolcu = ""
            
            # Etiket verisi
            etiket_data = {
                'musteri': musteri or '',
                'urun': self.secili_is_emri.get('stok_adi', ''),
                'lot_no': self.secili_is_emri.get('lot_no', ''),
                'adet': self.saglam_input.value(),
                'tarih': datetime.now().strftime('%d.%m.%Y'),
                'kontrolcu': kontrolcu,
                'stok_kodu': self.secili_is_emri.get('stok_kodu', '')
            }
            
            # Önizleme dialog'u göster
            dlg = EtiketOnizlemeDialog(self.theme, etiket_data, self)
            if dlg.exec() != QDialog.Accepted:
                return None  # İptal edildi
            
            # EZPL komutu oluştur (Godex için)
            ezpl = self._generate_ezpl(etiket_data)
            
            # Yazıcıya gönder (şimdilik dosyaya kaydet - test için)
            lot_safe = (etiket_data['lot_no'] or 'etiket').replace('/', '-').replace('\\', '-')
            etiket_dosya = os.path.join(os.path.expanduser("~"), "Desktop", f"etiket_{lot_safe}.prn")
            with open(etiket_dosya, 'w', encoding='utf-8') as f:
                f.write(ezpl)
            
            print(f"Etiket dosyası oluşturuldu: {etiket_dosya}")
            return etiket_dosya
            
            # TODO: Gerçek yazıcıya gönderme
            # self._send_to_printer(ezpl)
            
        except Exception as e:
            print(f"Etiket basma hatası: {e}")
            return None
    
    def _generate_ezpl(self, data: dict) -> str:
        """Godex EZPL etiket komutu oluştur - 100x50mm"""
        # EZPL komutları (Godex yazıcılar için)
        ezpl = f"""
^Q50,3
^W100
^H10
^P1
^S3
^AD
^C1
^R0
~Q+0
^O0
^D0
^E18
~R200
^L
Dy2-me-dd
Th:m:s
AE,48,36,1,1,0,0,{data['musteri'][:30]}
AE,48,26,1,1,0,3,Urun: {data['urun'][:25]}
AE,48,18,1,1,0,3,Lot: {data['lot_no']}
AE,48,12,1,1,0,3,Adet: {data['adet']}
AE,48,6,1,1,0,3,Tarih: {data['tarih']}
AE,48,0,1,1,0,3,Kontrol: {data['kontrolcu'][:15]}
BE,10,40,1,3,70,0,2,{data['lot_no']}
E
"""
        return ezpl
    
    def _send_to_printer(self, data: str):
        """Yazıcıya gönder"""
        try:
            import win32print
            printer_name = ETIKET_YAZICI
            
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Etiket", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, data.encode('utf-8'))
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            print(f"Yazıcı hatası: {e}")
