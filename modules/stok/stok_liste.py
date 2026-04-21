# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Stok Kartları Listesi Sayfası
[MODERNIZED UI - v3.0]

Ürün kartları yönetimi - stok.urunler tablosu üzerinden

YENİ YAPI:
- stok.urunler merkezi tablo
- stok.vw_urun_kart view ile zengin veri
- Akış şablonu desteği
- Ürün ağacı (BOM) desteği
- Kategori ve tip yönetimi
- Kalite entegrasyonu (giriş/proses/final kontrol)
- Üretim & Trend grafikleri
- Gelişmiş dosya yönetimi (NAS entegrasyonu)

Resim Yolu: \\\\AtlasNAS\\Data Yönetimi\\MAMUL_RESIM\\{UrunKodu}.jpg
Dosya Yolu: \\\\AtlasNAS\\Data Yönetimi\\Urunler\\{CariAdi}\\{UrunKodu}\\
"""
import os
import uuid
import subprocess
import shutil
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog, 
    QScrollArea, QWidget, QTabWidget, QDoubleSpinBox, QSpinBox,
    QTextEdit, QSplitter, QFileDialog, QCheckBox, QGroupBox,
    QFormLayout, QCompleter, QTreeWidget, QTreeWidgetItem,
    QProgressBar, QListWidget, QListWidgetItem, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor, QFont, QIcon

from components.base_page import BasePage, create_action_buttons
from components.dialog_minimize_bar import add_minimize_button
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand
from config import DEFAULT_PAGE_SIZE

# Matplotlib için
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Sabit resim yolu - NAS (config.json'dan)
from config import NAS_PATHS
NAS_IMAGE_PATH = NAS_PATHS["image_path"]
NAS_URUN_PATH = NAS_PATHS["product_path"]
NAS_KIMYASAL_PATH = NAS_PATHS.get("chemical_path", NAS_URUN_PATH)

# Ürün dosya kategorileri
DOSYA_KATEGORILERI = {
    '01_Teknik_Resimler': {'icon': '📐', 'ad': 'Teknik Resimler', 'uzantilar': ['.pdf', '.dwg', '.dxf', '.step', '.stp']},
    '02_Urun_Fotograflari': {'icon': '📸', 'ad': 'Ürün Fotoğrafları', 'uzantilar': ['.jpg', '.jpeg', '.png', '.bmp']},
    '03_Musteri_Hata_Bildirimleri': {'icon': '⚠️', 'ad': 'Müşteri Hata Bildirimleri', 'uzantilar': ['.pdf', '.jpg', '.png', '.xlsx', '.docx']},
    '04_Ic_Hatalar': {'icon': '🔴', 'ad': 'İç Hatalar', 'uzantilar': ['.pdf', '.jpg', '.png', '.xlsx', '.docx']},
    '05_PPAP': {'icon': '📋', 'ad': 'PPAP Dokümanları', 'uzantilar': ['.pdf', '.xlsx', '.docx']},
    '06_Ilk_Urun_Onaylari': {'icon': '✅', 'ad': 'İlk Ürün Onayları', 'uzantilar': ['.pdf', '.jpg', '.png', '.xlsx']},
    '07_Seriye_Alma': {'icon': '🏭', 'ad': 'Seriye Alma', 'uzantilar': ['.pdf', '.xlsx', '.docx']},
    '08_Test_Dokumanlari': {'icon': '🧪', 'ad': 'Test Dokümanları', 'uzantilar': ['.pdf', '.xlsx', '.docx']},
    '09_Sertifikalar': {'icon': '📜', 'ad': 'Sertifikalar', 'uzantilar': ['.pdf', '.jpg', '.png']},
    '10_Ambalajlama_Talimatlari': {'icon': '📦', 'ad': 'Ambalajlama Talimatları', 'uzantilar': ['.jpg', '.jpeg', '.png', '.bmp']}
}

# Kimyasal dosya kategorileri
KIMYASAL_DOSYA_KATEGORILERI = {
    '01_GBF_SDS': {'icon': '☣️', 'ad': 'GBF / SDS', 'uzantilar': ['.pdf', '.docx']},
    '02_TDS': {'icon': '📋', 'ad': 'TDS (Teknik Veri)', 'uzantilar': ['.pdf', '.docx']},
    '03_Sertifikalar': {'icon': '📜', 'ad': 'Sertifikalar / CoA', 'uzantilar': ['.pdf', '.jpg', '.png']},
    '04_Analiz_Raporlari': {'icon': '🔬', 'ad': 'Analiz Raporları', 'uzantilar': ['.pdf', '.xlsx', '.docx']},
    '05_Tedarikci_Belgeleri': {'icon': '🏢', 'ad': 'Tedarikçi Belgeleri', 'uzantilar': ['.pdf', '.xlsx', '.docx']},
}

# Kimyasal ürün tipleri (bu tiplerden biri ise kimyasal klasörüne yönlendir)
KIMYASAL_URUN_TIPLERI = {'HAMMADDE', 'YARDIMCI'}


def get_modern_style(theme: dict = None) -> dict:
    """Modern tema renkleri — brand sisteminden okuyor."""
    return {
        'card_bg':        brand.BG_CARD,
        'card_solid':     brand.BG_CARD,
        'input_bg':       brand.BG_INPUT,
        'bg_main':        brand.BG_MAIN,
        'bg_hover':       brand.BG_HOVER,
        'bg_selected':    brand.BG_SELECTED,
        'border':         brand.BORDER,
        'border_light':   brand.BORDER_HARD,
        'border_input':   brand.BORDER,
        'text':           brand.TEXT,
        'text_secondary': brand.TEXT_MUTED,
        'text_muted':     brand.TEXT_DIM,
        'primary':        brand.PRIMARY,
        'primary_hover':  brand.PRIMARY_HOVER,
        'success':        brand.SUCCESS,
        'warning':        brand.WARNING,
        'error':          brand.ERROR,
        'danger':         brand.ERROR,
        'info':           brand.INFO,
        'gradient':       brand.PRIMARY,
    }


class BOMDialog(QDialog):
    """Ürün Ağacı (BOM) Bileşen Ekleme Dialog"""
    
    def __init__(self, theme: dict, ana_urun_id: int, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.ana_urun_id = ana_urun_id
        self.selected_bilesen_id = None
        
        self.setWindowTitle("Bileşen Ekle")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._load_birimler()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QComboBox, QDoubleSpinBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 8px;
                color: {brand.TEXT};
            }}
        """)
        
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Bileşen Arama
        self.txt_arama = QLineEdit()
        self.txt_arama.setPlaceholderText("Ürün kodu veya adı yazın...")
        self.txt_arama.textChanged.connect(self._on_search)
        layout.addRow("Bileşen Ara:", self.txt_arama)
        
        # Bileşen Seçimi (sonuçlar)
        self.cmb_bilesen = QComboBox()
        self.cmb_bilesen.setMinimumWidth(350)
        self.cmb_bilesen.currentIndexChanged.connect(self._on_bilesen_selected)
        layout.addRow("Bileşen Seç:", self.cmb_bilesen)
        
        # Seçili ürün bilgisi
        self.lbl_secili = QLabel("-")
        self.lbl_secili.setStyleSheet(f"color: {brand.TEXT_DIM}; font-style: italic;")
        layout.addRow("", self.lbl_secili)
        
        # Miktar
        self.spin_miktar = QDoubleSpinBox()
        self.spin_miktar.setRange(0.0001, 999999)
        self.spin_miktar.setDecimals(4)
        self.spin_miktar.setValue(1)
        layout.addRow("Miktar:", self.spin_miktar)
        
        # Birim
        self.cmb_birim = QComboBox()
        layout.addRow("Birim:", self.cmb_birim)
        
        # Bileşen Tipi
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["HAMMADDE", "YARI_MAMUL", "AMBALAJ", "YARDIMCI", "DIGER"])
        layout.addRow("Bileşen Tipi:", self.cmb_tip)
        
        # Fire Oranı
        self.spin_fire = QDoubleSpinBox()
        self.spin_fire.setRange(0, 100)
        self.spin_fire.setDecimals(2)
        self.spin_fire.setValue(0)
        self.spin_fire.setSuffix(" %")
        layout.addRow("Fire Oranı:", self.spin_fire)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_kaydet = QPushButton("💾 Ekle")
        btn_kaydet.setStyleSheet(f"background: {brand.PRIMARY}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_iptal)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_kaydet)
        layout.addRow("", btn_layout)
    
    def _load_birimler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.birimler WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_birim.addItem(f"{row[1]} - {row[2]}", row[0])
        except Exception as e:
            print(f"Birim yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _on_search(self):
        arama = self.txt_arama.text().strip()
        self.cmb_bilesen.clear()
        
        if len(arama) < 2:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 20 id, urun_kodu, urun_adi
                FROM stok.urunler
                WHERE (urun_kodu LIKE ? OR urun_adi LIKE ?)
                  AND aktif_mi = 1
                  AND (silindi_mi = 0 OR silindi_mi IS NULL)
                  AND id != ?
                ORDER BY urun_kodu
            """, (f"%{arama}%", f"%{arama}%", self.ana_urun_id))

            for row in cursor.fetchall():
                self.cmb_bilesen.addItem(f"{row[1]} - {row[2][:40]}", row[0])
        except Exception as e:
            print(f"Arama hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _on_bilesen_selected(self):
        self.selected_bilesen_id = self.cmb_bilesen.currentData()
        if self.selected_bilesen_id:
            self.lbl_secili.setText(f"✓ Seçildi: {self.cmb_bilesen.currentText()}")
            self.lbl_secili.setStyleSheet(f"color: {brand.SUCCESS}; font-weight: bold;")
        else:
            self.lbl_secili.setText("-")
            self.lbl_secili.setStyleSheet(f"color: {brand.TEXT_DIM}; font-style: italic;")
    
    def _save(self):
        if not self.selected_bilesen_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir bileşen seçin!")
            return
        
        self.result_data = {
            'bilesen_urun_id': self.selected_bilesen_id,
            'miktar': self.spin_miktar.value(),
            'birim_id': self.cmb_birim.currentData(),
            'bilesen_tipi': self.cmb_tip.currentText(),
            'fire_orani': self.spin_fire.value()
        }
        self.accept()
    
    def get_data(self):
        return getattr(self, 'result_data', {})


class StokDetayDialog(QDialog):
    """Stok Kartı Detay ve Düzenleme Dialog - Yeni Yapı"""
    
    def __init__(self, urun_id: int, theme: dict, parent=None):
        super().__init__(parent)
        self.urun_id = urun_id
        self.theme = theme
        self.urun_data = {}
        self.edit_mode = False
        self.edit_widgets = {}
        self.combo_data = {}
        
        self._load_data()
        self.setWindowTitle(f"Stok Kartı - {self.urun_data.get('urun_kodu', '')}")
        self.setMinimumSize(1100, 750)
        self._setup_ui()
        add_minimize_button(self)

    def create_action_buttons(self, buttons: list) -> QWidget:
        """Standalone create_action_buttons fonksiyonuna delege eder."""
        return create_action_buttons(self.theme, buttons)

    def _load_data(self):
        """Veritabanından ürün bilgilerini yükle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Ana ürün bilgileri
            cursor.execute("""
                SELECT u.*,
                       c.unvan as cari_unvani,
                       b.kod as birim_kod, b.ad as birim_adi,
                       kt.kod as kaplama_kodu, kt.ad as kaplama_adi,
                       h.kod as hat_kodu, h.ad as hat_adi,
                       aks.kod as akis_kodu, aks.ad as akis_adi,
                       uk.ad as kategori_adi,
                       ut.ad as tip_adi,
                       ut.kod as tip_kodu
                FROM stok.urunler u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                LEFT JOIN tanim.uretim_hatlari h ON u.varsayilan_hat_id = h.id
                LEFT JOIN tanim.akis_sablon aks ON u.akis_sablon_id = aks.id
                LEFT JOIN stok.urun_kategorileri uk ON u.kategori_id = uk.id
                LEFT JOIN stok.urun_tipleri ut ON u.urun_tipi_id = ut.id
                WHERE u.id = ?
            """, (self.urun_id,))

            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                self.urun_data = dict(zip(columns, row))
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yüklenemedi: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QScrollArea {{ background: transparent; border: none; }}
            QTabWidget::pane {{ border: 1px solid {brand.BORDER}; background: {brand.BG_CARD}; border-radius: 8px; }}
            QTabBar::tab {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 8px 16px; border: 1px solid {brand.BORDER}; border-bottom: none; border-radius: 4px 4px 0 0; margin-right: 2px; }}
            QTabBar::tab:selected {{ background: {brand.BG_CARD}; border-bottom: 2px solid {brand.PRIMARY}; }}
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                color: {brand.TEXT};
            }}
            QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT_DIM};
            }}
            QCheckBox {{ color: {brand.TEXT}; }}
            QGroupBox {{ 
                font-weight: bold; 
                border: 1px solid {brand.BORDER}; 
                border-radius: 8px; 
                margin-top: 12px; 
                padding-top: 10px;
                color: {brand.PRIMARY};
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Ana içerik - Sol: Resim, Sağ: Tabs
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: transparent; }")
        
        # Sol panel - Resim ve özet
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Sağ panel - Tabs
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([350, 750])
        layout.addWidget(splitter, 1)
        
        # Resmi yükle
        self._load_image()
        
        # Başlangıçta düzenleme kapalı
        self._set_edit_enabled(False)
    
    def _create_header(self) -> QFrame:
        """Header — cari pattern'i ile ayni: kucuk pill + ghost butonlar."""
        header = QFrame()
        header.setFixedHeight(brand.sp(64))
        header.setStyleSheet(
            f"QFrame {{ background: {brand.BG_MAIN}; "
            f"border-bottom: 1px solid {brand.BORDER}; }}"
        )
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(brand.SP_6, 0, brand.SP_4, 0)
        h_layout.setSpacing(brand.SP_3)

        # Başlık
        title = QLabel(
            f"{self.urun_data.get('urun_kodu', '')} — "
            f"{self.urun_data.get('urun_adi', '')}"
        )
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"letter-spacing: -0.2px; "
            f"background: transparent; border: none;"
        )
        title.setWordWrap(True)
        h_layout.addWidget(title, 1)

        # Durum pill
        is_aktif = self.urun_data.get('aktif_mi', 1)
        self.aktif_label = self._make_pill(
            "Aktif" if is_aktif else "Pasif",
            brand.SUCCESS if is_aktif else brand.ERROR
        )
        h_layout.addWidget(self.aktif_label)

        h_layout.addSpacing(brand.SP_2)

        # Aktif/Pasif ghost buton
        self.toggle_aktif_btn = QPushButton("Pasif Yap" if is_aktif else "Aktif Yap")
        self.toggle_aktif_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_aktif_btn.setFixedHeight(brand.sp(34))
        self.toggle_aktif_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {brand.TEXT_MUTED};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
                color: {brand.TEXT};
            }}
        """)
        self.toggle_aktif_btn.clicked.connect(self._toggle_aktif)
        h_layout.addWidget(self.toggle_aktif_btn)

        # Zirve'ye Aktar
        zirve_stk_mevcut = self.urun_data.get('zirve_stk') if isinstance(self.urun_data, dict) else None
        self.zirve_btn = QPushButton(
            f"✓ Zirve: {zirve_stk_mevcut}" if zirve_stk_mevcut else "Zirve'ye Aktar"
        )
        self.zirve_btn.setCursor(Qt.PointingHandCursor)
        self.zirve_btn.setFixedHeight(brand.sp(34))
        if zirve_stk_mevcut:
            self.zirve_btn.setEnabled(False)
            self.zirve_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {brand.SUCCESS_SOFT};
                    color: {brand.SUCCESS};
                    border: 1px solid {brand.SUCCESS};
                    border-radius: {brand.R_SM}px;
                    padding: 0 {brand.SP_5}px;
                    font-size: {brand.FS_BODY_SM}px;
                    font-weight: {brand.FW_SEMIBOLD};
                }}
            """)
        else:
            self.zirve_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {brand.INFO};
                    color: white;
                    border: none;
                    border-radius: {brand.R_SM}px;
                    padding: 0 {brand.SP_5}px;
                    font-size: {brand.FS_BODY_SM}px;
                    font-weight: {brand.FW_SEMIBOLD};
                }}
                QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
            """)
            self.zirve_btn.clicked.connect(self._zirveye_aktar)
        h_layout.addWidget(self.zirve_btn)

        # Düzenle — primary buton
        self.edit_btn = QPushButton("Düzenle")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedHeight(brand.sp(34))
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        self.edit_btn.clicked.connect(self._toggle_edit_mode)
        h_layout.addWidget(self.edit_btn)

        # Kapat
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(brand.sp(34), brand.sp(34))
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {brand.TEXT_DIM};
                border: 1px solid {brand.BORDER};
                font-size: {brand.fs(14)}px;
                border-radius: {brand.R_SM}px;
            }}
            QPushButton:hover {{
                background: {brand.ERROR_SOFT};
                color: {brand.ERROR};
                border-color: {brand.ERROR};
            }}
        """)
        close_btn.clicked.connect(self.close)
        h_layout.addWidget(close_btn)

        return header

    def _make_pill(self, text: str, color: str) -> QLabel:
        """Cari pattern — kucuk, sakin badge."""
        c = QColor(color)
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedHeight(brand.sp(26))
        lbl.setStyleSheet(f"""
            color: {color};
            background: rgba({c.red()},{c.green()},{c.blue()},0.12);
            border: 1px solid rgba({c.red()},{c.green()},{c.blue()},0.35);
            border-radius: {brand.R_SM}px;
            padding: 0 {brand.SP_3}px;
            font-size: {brand.FS_CAPTION}px;
            font-weight: {brand.FW_SEMIBOLD};
        """)
        return lbl
    
    def _create_left_panel(self) -> QFrame:
        """Sol panel - Resim ve özet bilgiler"""
        left_panel = QFrame()
        left_panel.setMinimumWidth(300)
        left_panel.setMaximumWidth(400)
        left_panel.setStyleSheet(f"background: {brand.BG_CARD}; border-right: 1px solid {brand.BORDER};")
        l_layout = QVBoxLayout(left_panel)
        l_layout.setContentsMargins(16, 16, 16, 16)
        l_layout.setSpacing(12)
        
        # Resim alanı
        self.img_label = QLabel("🖼️ Resim Yükleniyor...")
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setMinimumHeight(280)
        self.img_label.setStyleSheet(f"""
            QLabel {{
                background: {brand.BG_HOVER};
                border: 2px dashed {brand.BORDER};
                border-radius: 12px;
                font-size: 14px;
                color: {brand.TEXT_DIM};
            }}
        """)
        l_layout.addWidget(self.img_label)
        
        # Resim yolu
        self.img_path_label = QLabel("")
        self.img_path_label.setWordWrap(True)
        self.img_path_label.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 10px;")
        l_layout.addWidget(self.img_path_label)
        
        # Özet bilgiler
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background: {brand.BG_HOVER}; border-radius: 8px; padding: 8px;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(6)
        
        info_items = [
            ("Müşteri", self.urun_data.get('cari_unvani')),
            ("Kaplama", self.urun_data.get('kaplama_adi')),
            ("Akış", self.urun_data.get('akis_adi') or "Varsayılan"),
            ("Kategori", self.urun_data.get('kategori_adi')),
            ("Birim", self.urun_data.get('birim_adi')),
        ]
        
        for label, value in info_items:
            row = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px;")
            lbl.setFixedWidth(70)
            row.addWidget(lbl)
            val = QLabel(str(value) if value else "-")
            val.setStyleSheet(f"color: {brand.TEXT}; font-size: 12px; font-weight: bold;")
            row.addWidget(val, 1)
            info_layout.addLayout(row)
        
        l_layout.addWidget(info_frame)
        l_layout.addStretch()
        
        return left_panel
    
    def _create_right_panel(self) -> QWidget:
        """Sağ panel - Sekmeler"""
        right_panel = QWidget()
        r_layout = QVBoxLayout(right_panel)
        r_layout.setContentsMargins(0, 0, 0, 0)
        
        tabs = QTabWidget()
        tabs.addTab(self._create_genel_tab(), "📋 Genel")
        tabs.addTab(self._create_olculer_tab(), "📐 Ölçüler")
        tabs.addTab(self._create_kaplama_tab(), "🎨 Kaplama")
        tabs.addTab(self._create_uretim_tab(), "🏭 Üretim")
        tabs.addTab(self._create_akis_tab(), "🔄 Akış")
        tabs.addTab(self._create_bom_tab(), "🧩 Ürün Ağacı")
        tabs.addTab(self._create_kalite_tab(), "✅ Kalite")
        tabs.addTab(self._create_trend_tab(), "📈 Trend")
        tabs.addTab(self._create_fiyat_tab(), "💰 Fiyat")
        tabs.addTab(self._create_dosyalar_tab(), "📁 Dosyalar")
        tabs.addTab(self._create_ambalajlama_tab(), "📦 Ambalajlama")

        r_layout.addWidget(tabs)
        return right_panel
    
    def _load_image(self):
        """NAS'tan resim yükle"""
        urun_kodu = self.urun_data.get('urun_kodu', '')
        
        if not urun_kodu:
            self.img_label.setText("🖼️ Ürün Kodu Yok")
            return
        
        extensions = ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG']
        found_path = None
        
        base_path = os.path.join(NAS_IMAGE_PATH, urun_kodu)
        
        for ext in extensions:
            test_path = base_path + ext
            if os.path.exists(test_path):
                found_path = test_path
                break
        
        self.img_path_label.setText(f"📁 {NAS_IMAGE_PATH}\\{urun_kodu}.jpg")
        
        if not found_path:
            self.img_label.setText(f"🖼️ Dosya Bulunamadı\n\n{urun_kodu}.jpg")
            return
        
        try:
            pixmap = QPixmap(found_path)
            if pixmap.isNull():
                self.img_label.setText("🖼️ Resim Yüklenemedi")
                return
            
            scaled = pixmap.scaled(350, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_label.setPixmap(scaled)
            self.img_label.setStyleSheet(f"""
                QLabel {{
                    background: {brand.BG_HOVER};
                    border: 1px solid {brand.BORDER};
                    border-radius: 12px;
                }}
            """)
            self.img_path_label.setText(f"📁 {found_path}")
        except Exception as e:
            self.img_label.setText(f"🖼️ Hata: {str(e)}")
    
    # ==================== SEKMELER ====================
    
    def _create_genel_tab(self) -> QScrollArea:
        """Genel bilgiler sekmesi"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Temel Bilgiler
        group1 = self._create_group("Temel Bilgiler")
        g1_layout = group1.layout()
        g1_layout.addLayout(self._create_editable_field('urun_kodu', 'Ürün Kodu', self.urun_data.get('urun_kodu')))
        g1_layout.addLayout(self._create_editable_field('urun_adi', 'Ürün Adı', self.urun_data.get('urun_adi')))
        g1_layout.addLayout(self._create_editable_field('musteri_parca_no', 'Müşteri Parça No', self.urun_data.get('musteri_parca_no')))
        g1_layout.addLayout(self._create_editable_field('barkod', 'Barkod', self.urun_data.get('barkod')))
        layout.addWidget(group1)
        
        # Kategori ve Tip
        group2 = self._create_group("Sınıflandırma")
        g2_layout = group2.layout()
        kategoriler = self._load_kategoriler()
        g2_layout.addLayout(self._create_editable_combo('kategori_id', 'Kategori', kategoriler, 
                                                        self.urun_data.get('kategori_id'), 'id', 'ad'))
        tipler = self._load_urun_tipleri()
        g2_layout.addLayout(self._create_editable_combo('urun_tipi_id', 'Ürün Tipi', tipler,
                                                        self.urun_data.get('urun_tipi_id'), 'id', 'ad'))
        layout.addWidget(group2)
        
        # Cari Bilgileri
        group3 = self._create_group("Cari Bilgileri")
        g3_layout = group3.layout()
        cariler = self._load_cariler()
        g3_layout.addLayout(self._create_editable_combo('cari_id', 'Müşteri', cariler,
                                                        self.urun_data.get('cari_id'), 'id', 'unvan'))
        layout.addWidget(group3)
        
        # Birim
        group4 = self._create_group("Birim")
        g4_layout = group4.layout()
        birimler = self._load_birimler()
        g4_layout.addLayout(self._create_editable_combo('birim_id', 'Birim', birimler,
                                                        self.urun_data.get('birim_id'), 'id', 'ad'))
        layout.addWidget(group4)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def _create_olculer_tab(self) -> QScrollArea:
        """Ölçüler sekmesi"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Boyutlar
        group1 = self._create_group("Boyutlar (mm)")
        g1_layout = group1.layout()
        g1_layout.addLayout(self._create_editable_field('en_mm', 'En', self.urun_data.get('en_mm'), 'number'))
        g1_layout.addLayout(self._create_editable_field('boy_mm', 'Boy', self.urun_data.get('boy_mm'), 'number'))
        g1_layout.addLayout(self._create_editable_field('yukseklik_mm', 'Yükseklik', self.urun_data.get('yukseklik_mm'), 'number'))
        layout.addWidget(group1)
        
        # Fiziksel Özellikler
        group2 = self._create_group("Fiziksel Özellikler")
        g2_layout = group2.layout()
        g2_layout.addLayout(self._create_editable_field('yuzey_alani_m2', 'Yüzey Alanı (m²)', self.urun_data.get('yuzey_alani_m2'), 'number', decimals=4))
        g2_layout.addLayout(self._create_editable_field('agirlik_kg', 'Ağırlık (kg)', self.urun_data.get('agirlik_kg'), 'number', decimals=3))
        layout.addWidget(group2)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def _create_kaplama_tab(self) -> QScrollArea:
        """Kaplama sekmesi"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Kaplama Tipi
        group1 = self._create_group("Kaplama Bilgileri")
        g1_layout = group1.layout()
        kaplama_turleri = self._load_kaplama_turleri()
        g1_layout.addLayout(self._create_editable_combo('kaplama_turu_id', 'Kaplama Türü', kaplama_turleri,
                                                        self.urun_data.get('kaplama_turu_id'), 'id', 'ad'))
        g1_layout.addLayout(self._create_editable_field('renk_kodu', 'Renk Kodu', self.urun_data.get('renk_kodu')))
        g1_layout.addLayout(self._create_editable_field('ral_kodu', 'RAL Kodu', self.urun_data.get('ral_kodu')))
        layout.addWidget(group1)
        
        # Kalınlık
        group2 = self._create_group("Kalınlık Spesifikasyonu (µm)")
        g2_layout = group2.layout()
        g2_layout.addLayout(self._create_editable_field('kalinlik_min_um', 'Minimum', self.urun_data.get('kalinlik_min_um'), 'number'))
        g2_layout.addLayout(self._create_editable_field('kalinlik_hedef_um', 'Hedef', self.urun_data.get('kalinlik_hedef_um'), 'number'))
        g2_layout.addLayout(self._create_editable_field('kalinlik_max_um', 'Maksimum', self.urun_data.get('kalinlik_max_um'), 'number'))
        layout.addWidget(group2)
        
        # Pasivasyon
        group3 = self._create_group("Pasivasyon")
        g3_layout = group3.layout()
        pasivasyon_tipleri = self._load_pasivasyon_tipleri()
        g3_layout.addLayout(self._create_editable_combo('pasivasyon_tipi_id', 'Pasivasyon Tipi', pasivasyon_tipleri,
                                                        self.urun_data.get('pasivasyon_tipi_id'), 'id', 'ad'))
        layout.addWidget(group3)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def _create_uretim_tab(self) -> QScrollArea:
        """Üretim sekmesi"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Üretim Hattı
        group1 = self._create_group("Varsayılan Üretim Ayarları")
        g1_layout = group1.layout()
        hatlar = self._load_uretim_hatlari()
        g1_layout.addLayout(self._create_editable_combo('varsayilan_hat_id', 'Varsayılan Hat', hatlar,
                                                        self.urun_data.get('varsayilan_hat_id'), 'id', 'ad'))
        
        # Teknik Resim No ve Reçete No
        g1_layout.addLayout(self._create_editable_field('teknik_resim_no', 'Teknik Resim No', 
                                                        self.urun_data.get('teknik_resim_no'), 'text'))
        g1_layout.addLayout(self._create_editable_field('recete_no', 'Reçete No', 
                                                        self.urun_data.get('recete_no'), 'text'))
        
        layout.addWidget(group1)
        
        # Askı Bilgileri
        group2 = self._create_group("Askı Bilgileri")
        g2_layout = group2.layout()
        aski_tipleri = self._load_aski_tipleri()
        g2_layout.addLayout(self._create_editable_combo('aski_tipi_id', 'Askı Tipi', aski_tipleri,
                                                        self.urun_data.get('aski_tipi_id'), 'id', 'ad'))
        g2_layout.addLayout(self._create_editable_field('aski_adedi', 'Askı Adedi', self.urun_data.get('aski_adedi'), 'int'))
        g2_layout.addLayout(self._create_editable_field('bara_adedi', 'Bara Adedi', self.urun_data.get('bara_adedi'), 'int'))
        g2_layout.addLayout(self._create_editable_field('pitch_mm', 'Pitch (mm)', self.urun_data.get('pitch_mm'), 'number'))
        layout.addWidget(group2)
        
        # Stok Seviyeleri
        group3 = self._create_group("Stok Seviyeleri")
        g3_layout = group3.layout()
        g3_layout.addLayout(self._create_editable_field('min_stok', 'Minimum Stok', self.urun_data.get('min_stok'), 'number'))
        g3_layout.addLayout(self._create_editable_field('max_stok', 'Maksimum Stok', self.urun_data.get('max_stok'), 'number'))
        g3_layout.addLayout(self._create_editable_field('kritik_stok', 'Kritik Stok', self.urun_data.get('kritik_stok'), 'number'))
        layout.addWidget(group3)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def _create_akis_tab(self) -> QScrollArea:
        """Akış sekmesi - YENİ"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Akış Şablonu
        group1 = self._create_group("Stok Akış Şablonu")
        g1_layout = group1.layout()
        
        akis_sablonlari = self._load_akis_sablonlari()
        g1_layout.addLayout(self._create_editable_combo('akis_sablon_id', 'Akış Şablonu', akis_sablonlari,
                                                        self.urun_data.get('akis_sablon_id'), 'id', 'display'))
        
        # Bilgi etiketi
        akis_info = QLabel("ℹ️ Akış şablonu, bu ürünün mal kabulden sevke kadar hangi aşamalardan geçeceğini belirler.\n"
                          "Boş bırakılırsa varsayılan (★) şablon kullanılır.")
        akis_info.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px; padding: 8px;")
        akis_info.setWordWrap(True)
        g1_layout.addWidget(akis_info)
        
        layout.addWidget(group1)
        
        # Seçili Akış Adımları
        group2 = self._create_group("Akış Adımları")
        g2_layout = group2.layout()
        
        self.akis_adim_table = QTableWidget()
        self.akis_adim_table.setColumnCount(4)
        self.akis_adim_table.setHorizontalHeaderLabels(["Sıra", "Adım", "Hedef Depo", "Kalite Kontrol"])
        self.akis_adim_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.akis_adim_table.setMaximumHeight(250)
        self._load_akis_adimlari()
        g2_layout.addWidget(self.akis_adim_table)
        
        layout.addWidget(group2)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def _create_bom_tab(self) -> QScrollArea:
        """Ürün Ağacı (BOM) sekmesi - YENİ"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # BOM Tablosu
        group1 = self._create_group("Ürün Ağacı / Malzeme Listesi")
        g1_layout = group1.layout()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_ekle = QPushButton("+ Bileşen Ekle")
        btn_ekle.clicked.connect(self._add_bom_item)
        btn_layout.addWidget(btn_ekle)
        
        btn_sil = QPushButton("🗑️ Seçili Sil")
        btn_sil.clicked.connect(self._delete_bom_item)
        btn_layout.addWidget(btn_sil)
        
        btn_layout.addStretch()
        g1_layout.addLayout(btn_layout)
        
        # Tablo
        self.bom_table = QTableWidget()
        self.bom_table.setColumnCount(6)
        self.bom_table.setHorizontalHeaderLabels(["Bileşen Kodu", "Bileşen Adı", "Miktar", "Birim", "Tip", "Fire %"])
        self.bom_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.bom_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bom_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._load_bom()
        g1_layout.addWidget(self.bom_table)
        
        layout.addWidget(group1)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def _create_kalite_tab(self) -> QScrollArea:
        """Kalite sekmesi - Genişletilmiş"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # ========== Kalite Özeti ==========
        group_ozet = self._create_group("📊 Kalite Özeti")
        ozet_layout = group_ozet.layout()
        
        ozet_grid = QHBoxLayout()
        
        # Kontrol Planı durumu
        self.lbl_kontrol_plani = QLabel("⏳ Yükleniyor...")
        self.lbl_kontrol_plani.setStyleSheet(f"padding: 8px; background: {brand.BG_HOVER}; border-radius: 6px;")
        ozet_grid.addWidget(self._create_stat_box("Kontrol Planı", self.lbl_kontrol_plani))
        
        # FMEA durumu
        self.lbl_fmea = QLabel("⏳ Yükleniyor...")
        self.lbl_fmea.setStyleSheet(f"padding: 8px; background: {brand.BG_HOVER}; border-radius: 6px;")
        ozet_grid.addWidget(self._create_stat_box("FMEA", self.lbl_fmea))
        
        # Son kontrol sonucu
        self.lbl_son_kontrol = QLabel("⏳ Yükleniyor...")
        self.lbl_son_kontrol.setStyleSheet(f"padding: 8px; background: {brand.BG_HOVER}; border-radius: 6px;")
        ozet_grid.addWidget(self._create_stat_box("Son Kontrol", self.lbl_son_kontrol))
        
        # Açık uygunsuzluk sayısı
        self.lbl_acik_uygunsuzluk = QLabel("⏳")
        self.lbl_acik_uygunsuzluk.setStyleSheet(f"padding: 8px; background: {brand.BG_HOVER}; border-radius: 6px;")
        ozet_grid.addWidget(self._create_stat_box("Açık Uygunsuzluk", self.lbl_acik_uygunsuzluk))
        
        ozet_layout.addLayout(ozet_grid)
        layout.addWidget(group_ozet)
        
        # ========== Test Gereksinimleri ==========
        group_test = self._create_group("🧪 Test Gereksinimleri")
        test_layout = group_test.layout()
        test_layout.addLayout(self._create_editable_field('tuz_testi_saat', 'Tuz Testi (saat)', self.urun_data.get('tuz_testi_saat'), 'int'))
        test_layout.addLayout(self._create_editable_field('final_kontrol_suresi_sn', 'Final Kontrol Süresi (sn)', self.urun_data.get('final_kontrol_suresi_sn'), 'int'))
        layout.addWidget(group_test)
        
        # ========== Son Giriş Kontrolleri ==========
        group_giris = self._create_group("📋 Son Giriş Kontrolleri")
        giris_layout = group_giris.layout()
        
        self.giris_kontrol_table = QTableWidget()
        self.giris_kontrol_table.setColumnCount(5)
        self.giris_kontrol_table.setHorizontalHeaderLabels(["Tarih", "Lot No", "Miktar", "Sonuç", "Kontrol Eden"])
        self.giris_kontrol_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.giris_kontrol_table.setMaximumHeight(150)
        self.giris_kontrol_table.setStyleSheet(self._mini_table_style())
        giris_layout.addWidget(self.giris_kontrol_table)
        layout.addWidget(group_giris)
        
        # ========== Son Final Kontroller ==========
        group_final = self._create_group("✓ Son Final Kontroller")
        final_layout = group_final.layout()
        
        self.final_kontrol_table = QTableWidget()
        self.final_kontrol_table.setColumnCount(7)
        self.final_kontrol_table.setHorizontalHeaderLabels(["Tarih", "Lot No", "Kontrol", "Sağlam", "Hatalı", "Sonuç", "Süre(sn)"])
        self.final_kontrol_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.final_kontrol_table.setMaximumHeight(150)
        self.final_kontrol_table.setStyleSheet(self._mini_table_style())
        final_layout.addWidget(self.final_kontrol_table)
        layout.addWidget(group_final)
        
        # ========== Açık Uygunsuzluklar ==========
        group_uygunsuzluk = self._create_group("⚠️ Açık Uygunsuzluklar")
        uygunsuzluk_layout = group_uygunsuzluk.layout()
        
        self.uygunsuzluk_table = QTableWidget()
        self.uygunsuzluk_table.setColumnCount(5)
        self.uygunsuzluk_table.setHorizontalHeaderLabels(["Kayıt No", "Tarih", "Tip", "Tanım", "Durum"])
        self.uygunsuzluk_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.uygunsuzluk_table.setMaximumHeight(150)
        self.uygunsuzluk_table.setStyleSheet(self._mini_table_style())
        uygunsuzluk_layout.addWidget(self.uygunsuzluk_table)
        layout.addWidget(group_uygunsuzluk)
        
        # ========== İzlenebilirlik ==========
        group_izlenebilirlik = self._create_group("🔍 İzlenebilirlik")
        iz_layout = group_izlenebilirlik.layout()
        iz_layout.addLayout(self._create_editable_field('lot_takibi_zorunlu', 'Lot Takibi Zorunlu', self.urun_data.get('lot_takibi_zorunlu'), 'checkbox'))
        iz_layout.addLayout(self._create_editable_field('kabul_kriterleri', 'Kabul Kriterleri', self.urun_data.get('kabul_kriterleri'), 'multiline'))
        layout.addWidget(group_izlenebilirlik)
        
        # ========== Özel Talimatlar ==========
        group_talimat = self._create_group("📝 Özel Talimatlar")
        talimat_layout = group_talimat.layout()
        talimat_layout.addLayout(self._create_editable_field('ozel_talimatlar', 'Özel Talimatlar', self.urun_data.get('ozel_talimatlar'), 'multiline'))
        talimat_layout.addLayout(self._create_editable_field('maskeleme_talimati', 'Maskeleme Talimatı', self.urun_data.get('maskeleme_talimati'), 'multiline'))
        layout.addWidget(group_talimat)
        
        layout.addStretch()
        scroll.setWidget(content)
        
        # Kalite verilerini yükle
        QTimer.singleShot(100, self._load_kalite_verileri)
        
        return scroll
    
    def _create_stat_box(self, title: str, value_label: QLabel) -> QFrame:
        """İstatistik kutusu oluştur"""
        box = QFrame()
        box.setStyleSheet(f"background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 8px; padding: 8px;")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(8, 8, 8, 8)
        box_layout.setSpacing(4)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px;")
        box_layout.addWidget(title_lbl)
        box_layout.addWidget(value_label)
        
        return box
    
    def _mini_table_style(self) -> str:
        return f"""
            QTableWidget {{
                background: {brand.BG_MAIN};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                gridline-color: {brand.BORDER};
                font-size: 11px;
            }}
            QTableWidget::item {{ padding: 4px; }}
            QHeaderView::section {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                padding: 6px;
                border: none;
                font-size: 11px;
                font-weight: bold;
            }}
        """
    
    def _load_kalite_verileri(self):
        """Kalite verilerini yükle"""
        urun_id = self.urun_id
        urun_kodu = self.urun_data.get('urun_kodu', '')
        cari_id = self.urun_data.get('cari_id')

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Kontrol Planı var mı?
            cursor.execute("""
                SELECT COUNT(*) FROM kalite.kontrol_planlari 
                WHERE (urun_id = ? OR kaplama_turu_id = ?) AND durum = 'ONAYLANDI'
            """, (urun_id, self.urun_data.get('kaplama_turu_id')))
            kontrol_plani = cursor.fetchone()[0] > 0
            self.lbl_kontrol_plani.setText("✅ Var" if kontrol_plani else "❌ Yok")
            self.lbl_kontrol_plani.setStyleSheet(f"color: {'#22c55e' if kontrol_plani else '#ef4444'}; font-weight: bold;")
            
            # FMEA var mı?
            cursor.execute("""
                SELECT COUNT(*) FROM kalite.fmea 
                WHERE (urun_id = ? OR kaplama_turu_id = ?) AND aktif_mi = 1
            """, (urun_id, self.urun_data.get('kaplama_turu_id')))
            fmea = cursor.fetchone()[0] > 0
            self.lbl_fmea.setText("✅ Var" if fmea else "❌ Yok")
            self.lbl_fmea.setStyleSheet(f"color: {'#22c55e' if fmea else '#ef4444'}; font-weight: bold;")
            
            # Son kontrol sonucu (final_kontrol tablosundan)
            cursor.execute("""
                SELECT TOP 1 sonuc FROM kalite.final_kontrol fc
                JOIN siparis.is_emirleri ie ON fc.is_emri_id = ie.id
                WHERE ie.stok_kodu = ?
                ORDER BY fc.kontrol_tarihi DESC
            """, (urun_kodu,))
            son_kontrol = cursor.fetchone()
            if son_kontrol:
                sonuc = son_kontrol[0] or 'BELİRSİZ'
                color = '#22c55e' if 'KABUL' in sonuc.upper() or 'OK' in sonuc.upper() else '#ef4444'
                self.lbl_son_kontrol.setText(sonuc)
                self.lbl_son_kontrol.setStyleSheet(f"color: {color}; font-weight: bold;")
            else:
                self.lbl_son_kontrol.setText("- Kayıt yok -")
                self.lbl_son_kontrol.setStyleSheet(f"color: {brand.TEXT_DIM};")
            
            # Açık uygunsuzluk sayısı
            cursor.execute("""
                SELECT COUNT(*) FROM kalite.uygunsuzluklar 
                WHERE urun_id = ? AND durum IN ('AÇIK', 'İŞLEMDE')
            """, (urun_id,))
            acik_uygunsuzluk = cursor.fetchone()[0]
            self.lbl_acik_uygunsuzluk.setText(str(acik_uygunsuzluk))
            self.lbl_acik_uygunsuzluk.setStyleSheet(f"color: {'#ef4444' if acik_uygunsuzluk > 0 else '#22c55e'}; font-weight: bold; font-size: 16px;")
            
            # Giriş kontrolleri (lot_no üzerinden)
            self.giris_kontrol_table.setRowCount(0)
            cursor.execute("""
                SELECT TOP 10 gk.kontrol_tarihi, gk.lot_no, sb.miktar, gk.sonuc, p.ad + ' ' + p.soyad
                FROM kalite.giris_kontrol_kayitlari gk
                LEFT JOIN stok.stok_bakiye sb ON gk.lot_no = sb.lot_no
                LEFT JOIN ik.personeller p ON gk.kontrol_eden_id = p.id
                WHERE sb.urun_id = ?
                ORDER BY gk.kontrol_tarihi DESC
            """, (urun_id,))
            for row in cursor.fetchall():
                r = self.giris_kontrol_table.rowCount()
                self.giris_kontrol_table.insertRow(r)
                self.giris_kontrol_table.setItem(r, 0, QTableWidgetItem(str(row[0])[:10] if row[0] else ''))
                self.giris_kontrol_table.setItem(r, 1, QTableWidgetItem(row[1] or ''))
                self.giris_kontrol_table.setItem(r, 2, QTableWidgetItem(f"{row[2]:,.0f}" if row[2] else ''))
                sonuc_item = QTableWidgetItem(row[3] or '')
                if row[3] and 'KABUL' in row[3].upper():
                    sonuc_item.setForeground(QColor('#22c55e'))
                elif row[3] and 'RED' in row[3].upper():
                    sonuc_item.setForeground(QColor('#ef4444'))
                self.giris_kontrol_table.setItem(r, 3, sonuc_item)
                self.giris_kontrol_table.setItem(r, 4, QTableWidgetItem(row[4] or ''))
            
            # Final kontroller
            self.final_kontrol_table.setRowCount(0)
            cursor.execute("""
                SELECT TOP 10 fc.kontrol_tarihi, fc.lot_no, fc.kontrol_miktar, fc.saglam_adet, 
                       fc.hatali_adet, fc.sonuc, DATEDIFF(SECOND, fc.olusturma_tarihi, fc.guncelleme_tarihi)
                FROM kalite.final_kontrol fc
                JOIN siparis.is_emirleri ie ON fc.is_emri_id = ie.id
                WHERE ie.stok_kodu = ?
                ORDER BY fc.kontrol_tarihi DESC
            """, (urun_kodu,))
            for row in cursor.fetchall():
                r = self.final_kontrol_table.rowCount()
                self.final_kontrol_table.insertRow(r)
                self.final_kontrol_table.setItem(r, 0, QTableWidgetItem(str(row[0])[:10] if row[0] else ''))
                self.final_kontrol_table.setItem(r, 1, QTableWidgetItem(row[1] or ''))
                self.final_kontrol_table.setItem(r, 2, QTableWidgetItem(f"{row[2]:,.0f}" if row[2] else ''))
                self.final_kontrol_table.setItem(r, 3, QTableWidgetItem(f"{row[3]:,.0f}" if row[3] else ''))
                self.final_kontrol_table.setItem(r, 4, QTableWidgetItem(f"{row[4]:,.0f}" if row[4] else ''))
                sonuc_item = QTableWidgetItem(row[5] or '')
                if row[5] and 'KABUL' in row[5].upper():
                    sonuc_item.setForeground(QColor('#22c55e'))
                elif row[5] and 'RED' in row[5].upper():
                    sonuc_item.setForeground(QColor('#ef4444'))
                self.final_kontrol_table.setItem(r, 5, sonuc_item)
                self.final_kontrol_table.setItem(r, 6, QTableWidgetItem(str(row[6]) if row[6] else ''))
            
            # Açık uygunsuzluklar
            self.uygunsuzluk_table.setRowCount(0)
            cursor.execute("""
                SELECT TOP 10 kayit_no, kayit_tarihi, kayit_tipi, LEFT(hata_tanimi, 100), durum
                FROM kalite.uygunsuzluklar
                WHERE urun_id = ? AND durum IN ('AÇIK', 'İŞLEMDE')
                ORDER BY kayit_tarihi DESC
            """, (urun_id,))
            for row in cursor.fetchall():
                r = self.uygunsuzluk_table.rowCount()
                self.uygunsuzluk_table.insertRow(r)
                self.uygunsuzluk_table.setItem(r, 0, QTableWidgetItem(row[0] or ''))
                self.uygunsuzluk_table.setItem(r, 1, QTableWidgetItem(str(row[1])[:10] if row[1] else ''))
                self.uygunsuzluk_table.setItem(r, 2, QTableWidgetItem(row[2] or ''))
                self.uygunsuzluk_table.setItem(r, 3, QTableWidgetItem(row[3] or ''))
                durum_item = QTableWidgetItem(row[4] or '')
                durum_item.setForeground(QColor('#f59e0b'))
                self.uygunsuzluk_table.setItem(r, 4, durum_item)
        except Exception as e:
            print(f"Kalite verileri yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _create_trend_tab(self) -> QScrollArea:
        """Üretim & Trend sekmesi - Matplotlib grafikleri"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Periyot seçimi
        periyot_layout = QHBoxLayout()
        periyot_layout.addWidget(QLabel("Periyot:"))
        
        self.trend_periyot = QComboBox()
        self.trend_periyot.addItem("Son 30 Gün", 30)
        self.trend_periyot.addItem("Son 3 Ay", 90)
        self.trend_periyot.addItem("Son 6 Ay", 180)
        self.trend_periyot.addItem("Son 1 Yıl", 365)
        self.trend_periyot.setCurrentIndex(1)
        self.trend_periyot.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; border: 1px solid {brand.BORDER}; padding: 6px; border-radius: 6px;")
        self.trend_periyot.currentIndexChanged.connect(self._load_trend_verileri)
        periyot_layout.addWidget(self.trend_periyot)
        periyot_layout.addStretch()
        
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.clicked.connect(self._load_trend_verileri)
        periyot_layout.addWidget(btn_yenile)
        layout.addLayout(periyot_layout)
        
        # Özet kartları
        ozet_layout = QHBoxLayout()
        
        self.trend_toplam_uretim = QLabel("0")
        self.trend_toplam_uretim.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {brand.PRIMARY};")
        ozet_layout.addWidget(self._create_stat_box("Toplam Üretim", self.trend_toplam_uretim))
        
        self.trend_toplam_hata = QLabel("0")
        self.trend_toplam_hata.setStyleSheet(f"font-size: 24px; font-weight: bold; color: #ef4444;")
        ozet_layout.addWidget(self._create_stat_box("Toplam Hata", self.trend_toplam_hata))
        
        self.trend_ppm = QLabel("0")
        self.trend_ppm.setStyleSheet(f"font-size: 24px; font-weight: bold; color: #f59e0b;")
        ozet_layout.addWidget(self._create_stat_box("PPM", self.trend_ppm))
        
        self.trend_ortalama_sure = QLabel("0 sn")
        self.trend_ortalama_sure.setStyleSheet(f"font-size: 24px; font-weight: bold; color: #22c55e;")
        ozet_layout.addWidget(self._create_stat_box("Ort. Kontrol Süresi", self.trend_ortalama_sure))
        
        layout.addLayout(ozet_layout)
        
        # Grafik alanı
        if MATPLOTLIB_AVAILABLE:
            self.trend_figure = Figure(figsize=(10, 4), facecolor=brand.BG_MAIN)
            self.trend_canvas = FigureCanvas(self.trend_figure)
            self.trend_canvas.setMinimumHeight(300)
            layout.addWidget(self.trend_canvas)
        else:
            layout.addWidget(QLabel("⚠️ Grafik için matplotlib gerekli: pip install matplotlib"))
        
        # Üretim geçmişi tablosu
        group_gecmis = self._create_group("📋 Üretim Geçmişi")
        gecmis_layout = group_gecmis.layout()
        
        self.trend_table = QTableWidget()
        self.trend_table.setColumnCount(7)
        self.trend_table.setHorizontalHeaderLabels(["Tarih", "İş Emri", "Lot No", "Üretilen", "Hatalı", "Oran %", "Süre"])
        self.trend_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.trend_table.setStyleSheet(self._mini_table_style())
        gecmis_layout.addWidget(self.trend_table)
        layout.addWidget(group_gecmis)
        
        layout.addStretch()
        scroll.setWidget(content)
        
        # Verileri yükle
        QTimer.singleShot(200, self._load_trend_verileri)
        
        return scroll
    
    def _load_trend_verileri(self):
        """Trend verilerini yükle ve grafik çiz"""
        urun_kodu = self.urun_data.get('urun_kodu', '')
        gun_sayisi = self.trend_periyot.currentData() or 90

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Üretim ve hata verileri
            cursor.execute("""
                SELECT
                    CAST(fc.kontrol_tarihi AS DATE) as tarih,
                    ie.is_emri_no,
                    fc.lot_no,
                    ISNULL(fc.kontrol_miktar, 0) as uretilen,
                    ISNULL(fc.hatali_adet, 0) as hatali,
                    fc.sonuc
                FROM kalite.final_kontrol fc
                JOIN siparis.is_emirleri ie ON fc.is_emri_id = ie.id
                WHERE ie.stok_kodu = ?
                  AND fc.kontrol_tarihi >= DATEADD(DAY, ?, GETDATE())
                ORDER BY fc.kontrol_tarihi DESC
            """, (urun_kodu, -gun_sayisi))

            rows = cursor.fetchall()
            
            # Tabloyu doldur
            self.trend_table.setRowCount(0)
            toplam_uretim = 0
            toplam_hata = 0
            tarih_uretim = {}
            tarih_hata = {}
            
            for row in rows:
                r = self.trend_table.rowCount()
                self.trend_table.insertRow(r)
                
                tarih_str = str(row[0]) if row[0] else ''
                self.trend_table.setItem(r, 0, QTableWidgetItem(tarih_str))
                self.trend_table.setItem(r, 1, QTableWidgetItem(row[1] or ''))
                self.trend_table.setItem(r, 2, QTableWidgetItem(row[2] or ''))
                
                uretilen = row[3] or 0
                hatali = row[4] or 0
                oran = (hatali / uretilen * 100) if uretilen > 0 else 0
                
                self.trend_table.setItem(r, 3, QTableWidgetItem(f"{uretilen:,.0f}"))
                self.trend_table.setItem(r, 4, QTableWidgetItem(f"{hatali:,.0f}"))
                
                oran_item = QTableWidgetItem(f"{oran:.2f}%")
                if oran > 5:
                    oran_item.setForeground(QColor('#ef4444'))
                elif oran > 2:
                    oran_item.setForeground(QColor('#f59e0b'))
                else:
                    oran_item.setForeground(QColor('#22c55e'))
                self.trend_table.setItem(r, 5, oran_item)
                self.trend_table.setItem(r, 6, QTableWidgetItem('-'))
                
                toplam_uretim += uretilen
                toplam_hata += hatali
                
                # Grafik için grupla
                if tarih_str:
                    tarih_uretim[tarih_str] = tarih_uretim.get(tarih_str, 0) + uretilen
                    tarih_hata[tarih_str] = tarih_hata.get(tarih_str, 0) + hatali
            
            # Özet kartları güncelle
            self.trend_toplam_uretim.setText(f"{toplam_uretim:,.0f}")
            self.trend_toplam_hata.setText(f"{toplam_hata:,.0f}")
            ppm = (toplam_hata / toplam_uretim * 1_000_000) if toplam_uretim > 0 else 0
            self.trend_ppm.setText(f"{ppm:,.0f}")
            
            # Grafik çiz
            if MATPLOTLIB_AVAILABLE and tarih_uretim:
                self._draw_trend_chart(tarih_uretim, tarih_hata)
        except Exception as e:
            print(f"Trend verileri yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _draw_trend_chart(self, tarih_uretim: dict, tarih_hata: dict):
        """Trend grafiği çiz"""
        self.trend_figure.clear()
        
        # Tarihleri sırala
        tarihler = sorted(tarih_uretim.keys())[-30:]  # Son 30 gün
        uretim = [tarih_uretim.get(t, 0) for t in tarihler]
        hata = [tarih_hata.get(t, 0) for t in tarihler]
        
        # Grafik stili
        bg_color = brand.BG_MAIN
        text_color = brand.TEXT
        
        ax = self.trend_figure.add_subplot(111)
        ax.set_facecolor(bg_color)
        
        # Çizgiler
        ax.bar(range(len(tarihler)), uretim, color='#6366f1', alpha=0.7, label='Üretim')
        ax.plot(range(len(tarihler)), hata, color='#ef4444', marker='o', linewidth=2, label='Hata')
        
        # Stil
        ax.set_xticks(range(0, len(tarihler), max(1, len(tarihler)//10)))
        ax.set_xticklabels([tarihler[i][5:] for i in range(0, len(tarihler), max(1, len(tarihler)//10))], rotation=45, color=text_color)
        ax.tick_params(colors=text_color)
        ax.spines['bottom'].set_color(text_color)
        ax.spines['left'].set_color(text_color)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend(facecolor=bg_color, edgecolor=text_color, labelcolor=text_color)
        ax.set_title('Üretim & Hata Trendi', color=text_color, fontsize=12)
        
        self.trend_figure.tight_layout()
        self.trend_canvas.draw()
    
    def _create_fiyat_tab(self) -> QScrollArea:
        """Fiyat sekmesi"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Fiyat tablosu
        group1 = self._create_group("Fiyat Listesi")
        g1_layout = group1.layout()
        
        btn_layout = QHBoxLayout()
        btn_ekle = QPushButton("+ Fiyat Ekle")
        btn_ekle.clicked.connect(self._add_fiyat)
        btn_layout.addWidget(btn_ekle)
        btn_layout.addStretch()
        g1_layout.addLayout(btn_layout)
        
        self.fiyat_table = QTableWidget()
        self.fiyat_table.setColumnCount(5)
        self.fiyat_table.setHorizontalHeaderLabels(["Tip", "Fiyat", "Para Birimi", "Geçerlilik", "Cari"])
        self.fiyat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._load_fiyatlar()
        g1_layout.addWidget(self.fiyat_table)
        
        layout.addWidget(group1)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def _create_dosyalar_tab(self) -> QScrollArea:
        """Dosyalar sekmesi - Gelişmiş NAS entegrasyonu"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Araç çubuğu
        toolbar = QHBoxLayout()
        
        btn_yukle = QPushButton("📤 Dosya Yükle")
        btn_yukle.clicked.connect(self._upload_file_to_category)
        btn_yukle.setStyleSheet(f"background: {brand.PRIMARY}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        toolbar.addWidget(btn_yukle)
        
        btn_klasor = QPushButton("📂 Ana Klasörü Aç")
        btn_klasor.clicked.connect(self._open_urun_folder)
        toolbar.addWidget(btn_klasor)
        
        btn_olustur = QPushButton("🗂️ Klasör Yapısı Oluştur")
        btn_olustur.clicked.connect(self._create_folder_structure)
        toolbar.addWidget(btn_olustur)
        
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.clicked.connect(self._load_dosyalar_from_nas)
        toolbar.addWidget(btn_yenile)
        
        toolbar.addStretch()
        
        # Yol göster
        self.dosya_path_label = QLabel("")
        self.dosya_path_label.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 10px;")
        toolbar.addWidget(self.dosya_path_label)
        
        layout.addLayout(toolbar)
        
        # Ana içerik - Sol: Kategori ağacı, Sağ: Dosya listesi
        splitter = QSplitter(Qt.Horizontal)
        
        # Sol - Kategori Ağacı
        left_panel = QFrame()
        left_panel.setStyleSheet(f"background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 8px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        
        cat_title = QLabel("📁 Kategoriler")
        cat_title.setStyleSheet(f"font-weight: bold; color: {brand.PRIMARY};")
        left_layout.addWidget(cat_title)
        
        self.kategori_tree = QTreeWidget()
        self.kategori_tree.setHeaderHidden(True)
        self.kategori_tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {brand.BG_MAIN};
                border: none;
                color: {brand.TEXT};
            }}
            QTreeWidget::item {{
                padding: 6px;
            }}
            QTreeWidget::item:selected {{
                background: {brand.PRIMARY};
            }}
        """)
        self.kategori_tree.itemClicked.connect(self._on_kategori_selected)
        self._populate_kategori_tree()
        left_layout.addWidget(self.kategori_tree)
        
        splitter.addWidget(left_panel)
        
        # Sağ - Dosya Listesi
        right_panel = QFrame()
        right_panel.setStyleSheet(f"background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 8px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        
        self.dosya_kategori_label = QLabel("📄 Tüm Dosyalar")
        self.dosya_kategori_label.setStyleSheet(f"font-weight: bold; color: {brand.PRIMARY};")
        right_layout.addWidget(self.dosya_kategori_label)
        
        self.dosya_table = QTableWidget()
        self.dosya_table.setColumnCount(5)
        self.dosya_table.setHorizontalHeaderLabels(["Kategori", "Dosya Adı", "Boyut", "Değiştirilme", ""])
        self.dosya_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.dosya_table.setColumnWidth(0, 120)
        self.dosya_table.setColumnWidth(2, 80)
        self.dosya_table.setColumnWidth(3, 100)
        self.dosya_table.setColumnWidth(4, 120)
        self.dosya_table.doubleClicked.connect(self._open_selected_file)
        self.dosya_table.setStyleSheet(self._mini_table_style())
        right_layout.addWidget(self.dosya_table)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 500])
        
        layout.addWidget(splitter)
        
        scroll.setWidget(content)
        
        # Dosyaları yükle ve klasör yapısını otomatik oluştur
        QTimer.singleShot(300, self._auto_create_and_load_files)
        
        return scroll

    # ==================== AMBALAJLAMA SEKMESİ ====================

    def _create_ambalajlama_tab(self) -> QScrollArea:
        """Ambalajlama talimatları sekmesi - 3 adım fotoğrafı"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Başlık
        header = QLabel("📦 Ambalajlama Talimatları")
        header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {brand.PRIMARY};")
        layout.addWidget(header)

        desc = QLabel("Ürünün ambalajlanma adımlarını gösteren 3 adet talimat fotoğrafı tanımlayın.")
        desc.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px;")
        layout.addWidget(desc)

        # 3 fotoğraf kutusu yan yana
        photos_layout = QHBoxLayout()
        photos_layout.setSpacing(16)

        self.ambalaj_labels = []
        self.ambalaj_upload_btns = []
        self.ambalaj_delete_btns = []
        self.ambalaj_paths = [None, None, None]

        for i in range(3):
            frame = QFrame()
            frame.setStyleSheet(f"""
                QFrame {{
                    background: {brand.BG_CARD};
                    border: 1px solid {brand.BORDER};
                    border-radius: 10px;
                }}
            """)
            f_layout = QVBoxLayout(frame)
            f_layout.setContentsMargins(12, 12, 12, 12)
            f_layout.setSpacing(8)

            # Adım başlığı
            step_lbl = QLabel(f"Adım {i + 1}")
            step_lbl.setAlignment(Qt.AlignCenter)
            step_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {brand.TEXT}; border: none;")
            f_layout.addWidget(step_lbl)

            # Fotoğraf alanı
            img_lbl = QLabel("Fotoğraf Yok")
            img_lbl.setFixedSize(280, 210)
            img_lbl.setAlignment(Qt.AlignCenter)
            img_lbl.setStyleSheet(f"""
                background: {brand.BG_INPUT};
                border: 2px dashed {brand.BORDER};
                border-radius: 8px;
                color: {brand.TEXT_DIM};
                font-size: 13px;
            """)
            f_layout.addWidget(img_lbl, alignment=Qt.AlignCenter)
            self.ambalaj_labels.append(img_lbl)

            # Butonlar
            btn_layout = QHBoxLayout()
            btn_upload = QPushButton("📤 Yükle")
            btn_upload.setStyleSheet(f"background: {brand.PRIMARY}; color: white; border: none; border-radius: 6px; padding: 6px 14px; font-weight: bold;")
            btn_upload.clicked.connect(lambda checked, idx=i: self._upload_ambalaj_foto(idx))
            btn_layout.addWidget(btn_upload)
            self.ambalaj_upload_btns.append(btn_upload)

            btn_delete = QPushButton("🗑️ Sil")
            btn_delete.setStyleSheet(f"background: {brand.ERROR}; color: white; border: none; border-radius: 6px; padding: 6px 14px; font-weight: bold;")
            btn_delete.clicked.connect(lambda checked, idx=i: self._delete_ambalaj_foto(idx))
            btn_layout.addWidget(btn_delete)
            self.ambalaj_delete_btns.append(btn_delete)

            f_layout.addLayout(btn_layout)
            photos_layout.addWidget(frame)

        layout.addLayout(photos_layout)
        layout.addStretch()

        scroll.setWidget(content)

        # Fotoğrafları yükle
        QTimer.singleShot(400, self._load_ambalaj_fotograflari)

        return scroll

    def _get_ambalaj_klasor_yolu(self) -> str:
        """Ambalajlama talimatları klasör yolunu döndür"""
        base_path = self._get_urun_base_path()
        return os.path.join(base_path, '10_Ambalajlama_Talimatlari')

    def _load_ambalaj_fotograflari(self):
        """NAS'tan 3 ambalaj fotoğrafını yükle"""
        klasor = self._get_ambalaj_klasor_yolu()

        for i in range(3):
            self.ambalaj_paths[i] = None
            found = False

            for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.JPG', '.JPEG', '.PNG', '.BMP']:
                dosya = os.path.join(klasor, f"ambalaj_{i + 1}{ext}")
                if os.path.exists(dosya):
                    try:
                        pixmap = QPixmap(dosya)
                        if not pixmap.isNull():
                            scaled = pixmap.scaled(280, 210, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            self.ambalaj_labels[i].setPixmap(scaled)
                            self.ambalaj_labels[i].setStyleSheet(f"""
                                background: {brand.BG_INPUT};
                                border: 1px solid {brand.BORDER};
                                border-radius: 8px;
                            """)
                            self.ambalaj_paths[i] = dosya
                            found = True
                            break
                    except Exception:
                        pass

            if not found:
                self.ambalaj_labels[i].clear()
                self.ambalaj_labels[i].setText("Fotoğraf Yok")
                self.ambalaj_labels[i].setStyleSheet(f"""
                    background: {brand.BG_INPUT};
                    border: 2px dashed {brand.BORDER};
                    border-radius: 8px;
                    color: {brand.TEXT_DIM};
                    font-size: 13px;
                """)

    def _upload_ambalaj_foto(self, index: int):
        """Ambalaj fotoğrafı yükle"""
        dosya, _ = QFileDialog.getOpenFileName(
            self, f"Ambalaj Adım {index + 1} Fotoğrafı Seç",
            "", "Resim Dosyaları (*.jpg *.jpeg *.png *.bmp)"
        )
        if not dosya:
            return

        klasor = self._get_ambalaj_klasor_yolu()
        try:
            os.makedirs(klasor, exist_ok=True)

            # Uzantıyı koru
            _, ext = os.path.splitext(dosya)
            hedef = os.path.join(klasor, f"ambalaj_{index + 1}{ext.lower()}")

            # Önceki dosyayı sil (farklı uzantı olabilir)
            for old_ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                old_file = os.path.join(klasor, f"ambalaj_{index + 1}{old_ext}")
                if os.path.exists(old_file):
                    os.remove(old_file)

            shutil.copy2(dosya, hedef)
            self._load_ambalaj_fotograflari()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Fotoğraf yüklenemedi:\n{str(e)}")

    def _delete_ambalaj_foto(self, index: int):
        """Ambalaj fotoğrafını sil"""
        if not self.ambalaj_paths[index]:
            QMessageBox.information(self, "Bilgi", "Silinecek fotoğraf yok.")
            return

        cevap = QMessageBox.question(
            self, "Onay",
            f"Adım {index + 1} fotoğrafını silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if cevap != QMessageBox.Yes:
            return

        try:
            os.remove(self.ambalaj_paths[index])
            self._load_ambalaj_fotograflari()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası:\n{str(e)}")

    def _populate_kategori_tree(self):
        """Kategori ağacını doldur (ürün tipine göre)"""
        self.kategori_tree.clear()

        # Tümü
        all_item = QTreeWidgetItem(["📂 Tüm Dosyalar"])
        all_item.setData(0, Qt.UserRole, None)
        self.kategori_tree.addTopLevelItem(all_item)

        # Ürün tipine göre kategoriler
        kategoriler = self._get_dosya_kategorileri()
        for kod, bilgi in kategoriler.items():
            item = QTreeWidgetItem([f"{bilgi['icon']} {bilgi['ad']}"])
            item.setData(0, Qt.UserRole, kod)
            self.kategori_tree.addTopLevelItem(item)

        self.kategori_tree.expandAll()
    
    def _on_kategori_selected(self, item: QTreeWidgetItem):
        """Kategori seçildiğinde"""
        kategori = item.data(0, Qt.UserRole)
        self.selected_kategori = kategori

        if kategori:
            kategoriler = self._get_dosya_kategorileri()
            bilgi = kategoriler.get(kategori, {})
            self.dosya_kategori_label.setText(f"{bilgi.get('icon', '📁')} {bilgi.get('ad', kategori)}")
        else:
            self.dosya_kategori_label.setText("📄 Tüm Dosyalar")
        
        self._load_dosyalar_from_nas(kategori)
    
    def _is_kimyasal(self) -> bool:
        """Ürün kimyasal/hammadde mi kontrol et"""
        # Birden fazla alandan kontrol - hangisi doluysa
        urun_tipi = (self.urun_data.get('urun_tipi') or '').upper().strip()
        tip_kodu = (self.urun_data.get('tip_kodu') or '').upper().strip()
        tip_adi = (self.urun_data.get('tip_adi') or '').upper().strip()
        return (urun_tipi in KIMYASAL_URUN_TIPLERI
                or tip_kodu in KIMYASAL_URUN_TIPLERI
                or tip_adi in KIMYASAL_URUN_TIPLERI)

    def _get_dosya_kategorileri(self) -> dict:
        """Ürün tipine göre dosya kategorilerini döndür"""
        if self._is_kimyasal():
            return KIMYASAL_DOSYA_KATEGORILERI
        return DOSYA_KATEGORILERI

    def _get_urun_base_path(self) -> str:
        """Ürün tipine göre klasör yolunu oluştur"""
        cari_adi = self.urun_data.get('cari_unvani', 'Genel')
        urun_kodu = self.urun_data.get('urun_kodu', '')

        # Geçersiz karakterleri temizle
        for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            cari_adi = cari_adi.replace(char, '_') if cari_adi else 'Genel'
            urun_kodu = urun_kodu.replace(char, '_') if urun_kodu else 'URUN'

        # Kimyasal ise ayrı klasöre yönlendir
        if self._is_kimyasal():
            return os.path.join(NAS_KIMYASAL_PATH, cari_adi, urun_kodu)

        return os.path.join(NAS_URUN_PATH, cari_adi, urun_kodu)
    
    def _auto_create_and_load_files(self):
        """Klasör yapısını otomatik oluştur ve dosyaları yükle"""
        base_path = self._get_urun_base_path()
        tip_label = "Kimyasal" if self._is_kimyasal() else "Ürün"
        self.dosya_path_label.setText(f"[{tip_label}] {base_path}")

        # Kategori ağacını güncelle (ürün tipine göre)
        self._populate_kategori_tree()

        # Klasör yapısını oluştur (sessizce)
        kategoriler = self._get_dosya_kategorileri()
        try:
            if not os.path.exists(base_path):
                os.makedirs(base_path, exist_ok=True)
                for kod in kategoriler.keys():
                    os.makedirs(os.path.join(base_path, kod), exist_ok=True)
        except Exception as e:
            print(f"Klasör oluşturma hatası: {e}")

        # Dosyaları yükle
        self._load_dosyalar_from_nas(None)

    def _create_folder_structure(self):
        """Klasör yapısını oluştur"""
        base_path = self._get_urun_base_path()
        kategoriler = self._get_dosya_kategorileri()

        try:
            os.makedirs(base_path, exist_ok=True)

            for kod, bilgi in kategoriler.items():
                klasor_yolu = os.path.join(base_path, kod)
                os.makedirs(klasor_yolu, exist_ok=True)

            QMessageBox.information(self, "Başarılı", f"Klasör yapısı oluşturuldu:\n{base_path}")
            self._load_dosyalar_from_nas(None)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Klasör oluşturulamadı:\n{e}")
    
    def _load_dosyalar_from_nas(self, kategori: str = None):
        """NAS'tan dosyaları yükle"""
        self.dosya_table.setRowCount(0)
        base_path = self._get_urun_base_path()
        kategoriler = self._get_dosya_kategorileri()

        if not os.path.exists(base_path):
            return

        dosyalar = []

        if kategori:
            # Belirli kategoriden yükle
            kategori_path = os.path.join(base_path, kategori)
            if os.path.exists(kategori_path):
                for dosya in os.listdir(kategori_path):
                    dosya_yolu = os.path.join(kategori_path, dosya)
                    if os.path.isfile(dosya_yolu):
                        dosyalar.append((kategori, dosya, dosya_yolu))
        else:
            # Tüm kategorilerden yükle
            for kod in kategoriler.keys():
                kategori_path = os.path.join(base_path, kod)
                if os.path.exists(kategori_path):
                    for dosya in os.listdir(kategori_path):
                        dosya_yolu = os.path.join(kategori_path, dosya)
                        if os.path.isfile(dosya_yolu):
                            dosyalar.append((kod, dosya, dosya_yolu))

            # Ana klasördeki dosyalar
            for dosya in os.listdir(base_path):
                dosya_yolu = os.path.join(base_path, dosya)
                if os.path.isfile(dosya_yolu):
                    dosyalar.append(('Diğer', dosya, dosya_yolu))

        for kat, dosya_adi, dosya_yolu in dosyalar:
            row = self.dosya_table.rowCount()
            self.dosya_table.insertRow(row)
            
            # Kategori
            aktif_kategoriler = self._get_dosya_kategorileri()
            if kat in aktif_kategoriler:
                kat_text = f"{aktif_kategoriler[kat]['icon']} {aktif_kategoriler[kat]['ad'][:15]}"
            else:
                kat_text = kat
            self.dosya_table.setItem(row, 0, QTableWidgetItem(kat_text))
            
            # Dosya adı
            self.dosya_table.setItem(row, 1, QTableWidgetItem(dosya_adi))
            self.dosya_table.item(row, 1).setData(Qt.UserRole, dosya_yolu)
            
            # Boyut
            try:
                size = os.path.getsize(dosya_yolu)
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                else:
                    size_str = f"{size / 1024:.1f} KB"
                self.dosya_table.setItem(row, 2, QTableWidgetItem(size_str))
            except Exception:
                self.dosya_table.setItem(row, 2, QTableWidgetItem("-"))
            
            # Değiştirilme tarihi
            try:
                mtime = os.path.getmtime(dosya_yolu)
                mtime_str = datetime.fromtimestamp(mtime).strftime('%d.%m.%Y')
                self.dosya_table.setItem(row, 3, QTableWidgetItem(mtime_str))
            except Exception:
                self.dosya_table.setItem(row, 3, QTableWidgetItem("-"))
            
            # Aç butonu
            widget = create_action_buttons(self.theme, [
                ("📄", "Dosyayi Ac", lambda checked, path=dosya_yolu: self._open_file_path(path), "view"),
            ])
            self.dosya_table.setCellWidget(row, 4, widget)
            self.dosya_table.setRowHeight(row, 42)
    
    def _upload_file_to_category(self):
        """Kategoriye dosya yükle"""
        # Kategori seç dialog
        from PySide6.QtWidgets import QInputDialog

        kategoriler = self._get_dosya_kategorileri()
        kategori_list = [f"{v['icon']} {v['ad']}" for v in kategoriler.values()]
        kategori_kodlari = list(kategoriler.keys())
        
        secim, ok = QInputDialog.getItem(self, "Kategori Seç", "Dosya kategorisi:", kategori_list, 0, False)
        
        if ok and secim:
            idx = kategori_list.index(secim)
            kategori_kod = kategori_kodlari[idx]
            
            # Dosya seç
            dosya_yolu, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Tüm Dosyalar (*.*)")
            
            if dosya_yolu:
                base_path = self._get_urun_base_path()
                hedef_klasor = os.path.join(base_path, kategori_kod)
                
                try:
                    os.makedirs(hedef_klasor, exist_ok=True)
                    dosya_adi = os.path.basename(dosya_yolu)
                    hedef_yol = os.path.join(hedef_klasor, dosya_adi)
                    
                    shutil.copy2(dosya_yolu, hedef_yol)
                    QMessageBox.information(self, "Başarılı", f"Dosya yüklendi:\n{hedef_yol}")
                    self._load_dosyalar_from_nas(None)
                    
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Dosya yüklenemedi:\n{e}")
    
    def _open_urun_folder(self):
        """Ürün ana klasörünü aç"""
        base_path = self._get_urun_base_path()
        try:
            if os.path.exists(base_path):
                os.startfile(base_path)
            else:
                QMessageBox.warning(self, "Uyarı", f"Klasör bulunamadı:\n{base_path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Klasör açılamadı:\n{e}")
    
    def _open_selected_file(self, index):
        """Seçili dosyayı aç"""
        row = index.row()
        dosya_yolu = self.dosya_table.item(row, 1).data(Qt.UserRole)
        if dosya_yolu:
            self._open_file_path(dosya_yolu)
    
    def _open_file_path(self, path: str):
        """Dosya yolunu aç"""
        try:
            if os.path.exists(path):
                os.startfile(path)
            else:
                QMessageBox.warning(self, "Uyarı", f"Dosya bulunamadı:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya açılamadı:\n{e}")
    
    # ==================== YARDIMCI METODLAR ====================
    
    def _create_group(self, title: str) -> QFrame:
        """Grup kutusu oluştur"""
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 10px; }}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {brand.PRIMARY}; font-weight: bold; font-size: 13px; border: none;")
        layout.addWidget(title_lbl)
        return frame
    
    def _create_editable_field(self, key: str, label: str, value, field_type: str = "text", 
                                max_val: float = 999999, decimals: int = 2) -> QHBoxLayout:
        """Düzenlenebilir alan oluştur"""
        row = QHBoxLayout()
        
        lbl = QLabel(f"{label}:")
        lbl.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px;")
        lbl.setFixedWidth(140)
        row.addWidget(lbl)
        
        if field_type == "text":
            widget = QLineEdit()
            widget.setText(str(value) if value else "")
        elif field_type == "number":
            widget = QDoubleSpinBox()
            widget.setRange(0, max_val)
            widget.setDecimals(decimals)
            widget.setValue(float(value) if value else 0)
        elif field_type == "int":
            widget = QSpinBox()
            widget.setRange(0, int(max_val))
            widget.setValue(int(value) if value else 0)
        elif field_type == "checkbox":
            widget = QCheckBox()
            widget.setChecked(bool(value))
        elif field_type == "multiline":
            widget = QTextEdit()
            widget.setPlainText(str(value) if value else "")
            widget.setMaximumHeight(80)
        else:
            widget = QLineEdit()
            widget.setText(str(value) if value else "")
        
        widget.setEnabled(False)
        self.edit_widgets[key] = widget
        row.addWidget(widget, 1)
        
        return row
    
    def _create_editable_combo(self, key: str, label: str, items: list, current_value, 
                                value_field: str = 'id', display_field: str = 'ad') -> QHBoxLayout:
        """Düzenlenebilir combo box"""
        row = QHBoxLayout()
        
        lbl = QLabel(f"{label}:")
        lbl.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px;")
        lbl.setFixedWidth(140)
        row.addWidget(lbl)
        
        combo = QComboBox()
        combo.addItem("-- Seçiniz --", None)
        
        selected_index = 0
        for i, item in enumerate(items):
            display = item.get(display_field) or item.get('ad') or str(item.get(value_field))
            combo.addItem(str(display), item)
            
            if current_value and item.get(value_field) == current_value:
                selected_index = i + 1
        
        combo.setCurrentIndex(selected_index)
        combo.setEnabled(False)
        self.edit_widgets[key] = combo
        self.combo_data[key] = {'value_field': value_field, 'display_field': display_field}
        row.addWidget(combo, 1)
        
        return row
    
    # ==================== VERİ YÜKLEME ====================
    
    def _load_kategoriler(self) -> list:
        items = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad, tam_yol FROM stok.urun_kategorileri WHERE aktif_mi = 1 ORDER BY sira_no, ad")
            for row in cursor.fetchall():
                items.append({'id': row[0], 'kod': row[1], 'ad': row[2], 'tam_yol': row[3]})
        except Exception as e:
            print(f"Kategori yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
        return items
    
    def _load_urun_tipleri(self) -> list:
        items = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM stok.urun_tipleri WHERE aktif_mi = 1 ORDER BY sira_no")
            for row in cursor.fetchall():
                items.append({'id': row[0], 'kod': row[1], 'ad': row[2]})
        except Exception as e:
            print(f"Tip yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
        return items
    
    def _load_cariler(self) -> list:
        items = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, cari_kodu, unvan
                FROM musteri.cariler
                WHERE aktif_mi = 1 AND (silindi_mi = 0 OR silindi_mi IS NULL)
                ORDER BY unvan
            """)
            for row in cursor.fetchall():
                items.append({'id': row[0], 'kod': row[1], 'unvan': row[2]})
        except Exception as e:
            print(f"Cari yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
        return items
    
    def _load_birimler(self) -> list:
        items = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.birimler WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                items.append({'id': row[0], 'kod': row[1], 'ad': row[2]})
        except Exception as e:
            print(f"Birim yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
        return items
    
    def _load_kaplama_turleri(self) -> list:
        items = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.kaplama_turleri WHERE aktif_mi = 1 ORDER BY sira, ad")
            for row in cursor.fetchall():
                items.append({'id': row[0], 'kod': row[1], 'ad': row[2]})
        except Exception as e:
            print(f"Kaplama türü yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
        return items
    
    def _load_pasivasyon_tipleri(self) -> list:
        items = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.pasivasyon_tipleri WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                items.append({'id': row[0], 'kod': row[1], 'ad': row[2]})
        except Exception as e:
            print(f"Pasivasyon yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
        return items
    
    def _load_uretim_hatlari(self) -> list:
        items = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.uretim_hatlari WHERE aktif_mi = 1 ORDER BY sira_no, ad")
            for row in cursor.fetchall():
                items.append({'id': row[0], 'kod': row[1], 'ad': row[2]})
        except Exception as e:
            print(f"Hat yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
        return items
    
    def _load_aski_tipleri(self) -> list:
        items = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.aski_tipleri WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                items.append({'id': row[0], 'kod': row[1], 'ad': row[2]})
        except Exception as e:
            print(f"Askı tipi yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
        return items
    
    def _load_akis_sablonlari(self) -> list:
        items = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad, varsayilan_mi,
                       (SELECT COUNT(*) FROM tanim.akis_adim WHERE sablon_id = s.id AND aktif_mi = 1) as adim_sayisi
                FROM tanim.akis_sablon s
                WHERE aktif_mi = 1
                ORDER BY varsayilan_mi DESC, kod
            """)
            for row in cursor.fetchall():
                items.append({
                    'id': row[0],
                    'kod': row[1],
                    'ad': row[2],
                    'varsayilan_mi': row[3],
                    'adim_sayisi': row[4],
                    'display': f"{row[1]} - {row[2]} ({row[4]} adım)" + (" ★" if row[3] else "")
                })
        except Exception as e:
            print(f"Akış şablonu yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
        return items
    
    def _load_akis_adimlari(self):
        """Seçili akış şablonunun adımlarını yükle"""
        self.akis_adim_table.setRowCount(0)
        sablon_id = self.urun_data.get('akis_sablon_id')

        if not sablon_id:
            # Varsayılan şablonu al
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM tanim.akis_sablon WHERE varsayilan_mi = 1 AND aktif_mi = 1")
                row = cursor.fetchone()
                if row:
                    sablon_id = row[0]
            except Exception:
                return
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass

        if not sablon_id:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.sira, t.ad, d.ad, a.kalite_kontrol_gerekli
                FROM tanim.akis_adim a
                JOIN tanim.akis_adim_tipleri t ON a.adim_tipi_id = t.id
                LEFT JOIN tanim.depolar d ON a.hedef_depo_id = d.id
                WHERE a.sablon_id = ? AND a.aktif_mi = 1
                ORDER BY a.sira
            """, (sablon_id,))

            for row in cursor.fetchall():
                r = self.akis_adim_table.rowCount()
                self.akis_adim_table.insertRow(r)
                self.akis_adim_table.setItem(r, 0, QTableWidgetItem(str(row[0])))
                self.akis_adim_table.setItem(r, 1, QTableWidgetItem(row[1] or ""))
                self.akis_adim_table.setItem(r, 2, QTableWidgetItem(row[2] or ""))
                self.akis_adim_table.setItem(r, 3, QTableWidgetItem("✓" if row[3] else ""))
        except Exception as e:
            print(f"Akış adımları yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _load_bom(self):
        """Ürün ağacını yükle"""
        self.bom_table.setRowCount(0)
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Önce tablo var mı kontrol et
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'stok' AND TABLE_NAME = 'urun_agaci'
            """)
            if cursor.fetchone()[0] == 0:
                return  # Tablo yok, boş bırak

            # silindi_mi sütunu var mı kontrol et
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'stok' AND TABLE_NAME = 'urun_agaci' AND COLUMN_NAME = 'silindi_mi'
            """)
            has_silindi = cursor.fetchone()[0] > 0

            if has_silindi:
                query = """
                    SELECT ua.id, u.urun_kodu, u.urun_adi, ua.miktar, b.kod, ua.bilesen_tipi, ua.fire_orani
                    FROM stok.urun_agaci ua
                    JOIN stok.urunler u ON ua.bilesen_urun_id = u.id
                    LEFT JOIN tanim.birimler b ON ua.birim_id = b.id
                    WHERE ua.ana_urun_id = ? AND ua.aktif_mi = 1 AND (ua.silindi_mi = 0 OR ua.silindi_mi IS NULL)
                    ORDER BY ua.bilesen_tipi, u.urun_kodu
                """
            else:
                query = """
                    SELECT ua.id, u.urun_kodu, u.urun_adi, ua.miktar, b.kod, ua.bilesen_tipi, ua.fire_orani
                    FROM stok.urun_agaci ua
                    JOIN stok.urunler u ON ua.bilesen_urun_id = u.id
                    LEFT JOIN tanim.birimler b ON ua.birim_id = b.id
                    WHERE ua.ana_urun_id = ? AND ua.aktif_mi = 1
                    ORDER BY ua.bilesen_tipi, u.urun_kodu
                """

            cursor.execute(query, (self.urun_id,))

            for row in cursor.fetchall():
                r = self.bom_table.rowCount()
                self.bom_table.insertRow(r)

                # ID'yi ilk kolona gizli olarak sakla
                item0 = QTableWidgetItem(row[1] or "")
                item0.setData(Qt.UserRole, row[0])  # BOM ID
                self.bom_table.setItem(r, 0, item0)

                self.bom_table.setItem(r, 1, QTableWidgetItem(row[2] or ""))
                self.bom_table.setItem(r, 2, QTableWidgetItem(f"{row[3]:.4f}" if row[3] else ""))
                self.bom_table.setItem(r, 3, QTableWidgetItem(row[4] or ""))
                self.bom_table.setItem(r, 4, QTableWidgetItem(row[5] or ""))
                self.bom_table.setItem(r, 5, QTableWidgetItem(f"{row[6]:.2f}" if row[6] else "0"))
        except Exception as e:
            print(f"BOM yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _delete_bom_item(self):
        """Seçili bileşeni sil"""
        selected = self.bom_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek bileşeni seçin!")
            return
        
        row = selected[0].row()
        bom_id = self.bom_table.item(row, 0).data(Qt.UserRole)
        bilesen_kodu = self.bom_table.item(row, 0).text()
        
        if not bom_id:
            QMessageBox.warning(self, "Uyarı", "Bileşen ID bulunamadı!")
            return
        
        reply = QMessageBox.question(
            self, "Onay", 
            f"'{bilesen_kodu}' bileşenini silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                # silindi_mi sütunu var mı kontrol et
                cursor.execute("""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = 'stok' AND TABLE_NAME = 'urun_agaci' AND COLUMN_NAME = 'silindi_mi'
                """)
                has_silindi = cursor.fetchone()[0] > 0

                if has_silindi:
                    cursor.execute("""
                        UPDATE stok.urun_agaci
                        SET silindi_mi = 1, silinme_tarihi = GETDATE()
                        WHERE id = ?
                    """, (bom_id,))
                else:
                    # silindi_mi yoksa aktif_mi'yi 0 yap
                    cursor.execute("""
                        UPDATE stok.urun_agaci
                        SET aktif_mi = 0
                        WHERE id = ?
                    """, (bom_id,))

                conn.commit()
                LogManager.log_delete('stok', 'stok.urun_agaci', None, 'Kayit silindi (soft delete)')

                self._load_bom()
                QMessageBox.information(self, "Başarılı", "Bileşen silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass
    
    def _load_fiyatlar(self):
        """Fiyatları yükle"""
        self.fiyat_table.setRowCount(0)
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.fiyat_tipi, f.fiyat, f.para_birimi, f.gecerlilik_baslangic, c.unvan
                FROM stok.urun_fiyatlari f
                LEFT JOIN musteri.cariler c ON f.cari_id = c.id
                WHERE f.urun_id = ? AND f.aktif_mi = 1
                ORDER BY f.fiyat_tipi
            """, (self.urun_id,))

            for row in cursor.fetchall():
                r = self.fiyat_table.rowCount()
                self.fiyat_table.insertRow(r)
                self.fiyat_table.setItem(r, 0, QTableWidgetItem(row[0] or ""))
                self.fiyat_table.setItem(r, 1, QTableWidgetItem(f"{row[1]:,.2f}" if row[1] else ""))
                self.fiyat_table.setItem(r, 2, QTableWidgetItem(row[2] or "TRY"))
                self.fiyat_table.setItem(r, 3, QTableWidgetItem(str(row[3]) if row[3] else ""))
                self.fiyat_table.setItem(r, 4, QTableWidgetItem(row[4] or "Genel"))
        except Exception as e:
            print(f"Fiyat yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _load_dosyalar(self):
        """Dosyaları yükle"""
        self.dosya_table.setRowCount(0)
        urun_kodu = self.urun_data.get('urun_kodu', '')
        
        # NAS'tan resim dosyası
        for ext in ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG']:
            base_path = os.path.join(NAS_IMAGE_PATH, urun_kodu)
            test_path = base_path + ext
            if os.path.exists(test_path):
                row = self.dosya_table.rowCount()
                self.dosya_table.insertRow(row)
                self.dosya_table.setItem(row, 0, QTableWidgetItem("📷 Fotoğraf"))
                self.dosya_table.setItem(row, 1, QTableWidgetItem(f"{urun_kodu}{ext}"))
                try:
                    size = os.path.getsize(test_path) / 1024
                    self.dosya_table.setItem(row, 2, QTableWidgetItem(f"{size:.1f} KB"))
                except Exception:
                    self.dosya_table.setItem(row, 2, QTableWidgetItem("-"))
                self.dosya_table.setItem(row, 3, QTableWidgetItem("Ürün fotoğrafı"))
                self.dosya_table.item(row, 1).setData(Qt.UserRole, test_path)
                break
    
    # ==================== BUTON AKSIYONLARI ====================
    
    def _toggle_aktif(self):
        """Aktif/Pasif değiştir"""
        current = self.urun_data.get('aktif_mi', 1)
        new_value = 0 if current else 1
        msg = "pasif" if new_value == 0 else "aktif"
        
        reply = QMessageBox.question(self, "Onay", f"Bu ürünü {msg} yapmak istediğinize emin misiniz?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE stok.urunler SET aktif_mi = ?, guncelleme_tarihi = GETDATE() WHERE id = ?",
                              (new_value, self.urun_id))
                conn.commit()
                LogManager.log_update('stok', 'stok.urunler', None, 'Aktiflik durumu degistirildi')

                self.urun_data['aktif_mi'] = new_value
                self._update_aktif_ui(new_value)
                QMessageBox.information(self, "Başarılı", f"Ürün {msg} yapıldı!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"İşlem başarısız:\n{str(e)}")
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass
    
    def _update_aktif_ui(self, is_aktif):
        # Pill'i brand stili ile yeniden ciz
        color = brand.SUCCESS if is_aktif else brand.ERROR
        c = QColor(color)
        self.aktif_label.setText("Aktif" if is_aktif else "Pasif")
        self.aktif_label.setStyleSheet(f"""
            color: {color};
            background: rgba({c.red()},{c.green()},{c.blue()},0.12);
            border: 1px solid rgba({c.red()},{c.green()},{c.blue()},0.35);
            border-radius: {brand.R_SM}px;
            padding: 0 {brand.SP_3}px;
            font-size: {brand.FS_CAPTION}px;
            font-weight: {brand.FW_SEMIBOLD};
        """)
        self.toggle_aktif_btn.setText("Pasif Yap" if is_aktif else "Aktif Yap")
        # Buton stili ghost — degismiyor

    def _zirveye_aktar(self):
        """Stok kartini Zirve'ye aktar (sifre dogrulamasi ile)."""
        from PySide6.QtWidgets import QInputDialog, QLineEdit
        from core.zirve_entegrasyon import stok_aktar

        urun_kodu = self.urun_data.get('urun_kodu', '') if isinstance(self.urun_data, dict) else ''
        urun_adi = self.urun_data.get('urun_adi', '') if isinstance(self.urun_data, dict) else ''

        # 1) On onay
        onay = QMessageBox.question(
            self,
            "Zirve'ye Aktarim",
            f"Bu stok karti Zirve'ye aktarilacak:\n\n"
            f"Kod: {urun_kodu}\n"
            f"Adi: {urun_adi}\n\n"
            f"Devam etmek icin sifre istenecek. Emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if onay != QMessageBox.Yes:
            return

        # 2) Sifre sor
        sifre, ok = QInputDialog.getText(
            self,
            "Aktarim Sifresi",
            f"Zirve aktarim sifresini girin:\n({urun_kodu} - {urun_adi})",
            QLineEdit.Password
        )
        if not ok or not sifre:
            return

        # 3) Aktar
        self.zirve_btn.setEnabled(False)
        self.zirve_btn.setText("Aktariliyor...")
        QApplication.processEvents()

        try:
            sonuc = stok_aktar(self.urun_id, sifre)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Beklenmeyen hata:\n{e}")
            self.zirve_btn.setEnabled(True)
            self.zirve_btn.setText("Zirve'ye Aktar")
            return

        if sonuc.basarili:
            QMessageBox.information(self, "Basarili", sonuc.mesaj)
            # Butonu guncelle
            self.zirve_btn.setText(f"✓ Zirve: {sonuc.zirve_evrakno}")
            self.zirve_btn.setEnabled(False)
            self.zirve_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {brand.SUCCESS_SOFT};
                    color: {brand.SUCCESS};
                    border: 1px solid {brand.SUCCESS};
                    border-radius: {brand.R_SM}px;
                    padding: 0 {brand.SP_5}px;
                    font-size: {brand.FS_BODY_SM}px;
                    font-weight: {brand.FW_SEMIBOLD};
                }}
            """)
            # Cache'i guncelle
            if isinstance(self.urun_data, dict):
                self.urun_data['zirve_stk'] = sonuc.zirve_evrakno
        else:
            QMessageBox.warning(self, "Aktarim Basarisiz", sonuc.hata or "Bilinmeyen hata")
            self.zirve_btn.setEnabled(True)
            self.zirve_btn.setText("Zirve'ye Aktar")

    def _toggle_edit_mode(self):
        if self.edit_mode:
            self._save_data()
        else:
            self.edit_mode = True
            self.edit_btn.setText("Kaydet")
            self.edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {brand.SUCCESS};
                    color: white;
                    border: none;
                    border-radius: {brand.R_SM}px;
                    padding: 0 {brand.SP_5}px;
                    font-size: {brand.FS_BODY_SM}px;
                    font-weight: {brand.FW_SEMIBOLD};
                }}
            """)
            self._set_edit_enabled(True)
    
    def _set_edit_enabled(self, enabled: bool):
        for widget in self.edit_widgets.values():
            widget.setEnabled(enabled)
    
    def _save_data(self):
        """Verileri kaydet"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            for key, widget in self.edit_widgets.items():
                if isinstance(widget, QLineEdit):
                    value = widget.text().strip() or None
                elif isinstance(widget, QTextEdit):
                    value = widget.toPlainText().strip() or None
                elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                    value = widget.value()
                elif isinstance(widget, QCheckBox):
                    value = 1 if widget.isChecked() else 0
                elif isinstance(widget, QComboBox):
                    selected_data = widget.currentData()
                    if selected_data and isinstance(selected_data, dict):
                        value_field = self.combo_data.get(key, {}).get('value_field', 'id')
                        value = selected_data.get(value_field)
                    else:
                        value = None
                else:
                    continue

                updates.append(f"{key} = ?")
                params.append(value)

            if updates:
                params.append(self.urun_id)
                sql = f"UPDATE stok.urunler SET {', '.join(updates)}, guncelleme_tarihi = GETDATE() WHERE id = ?"
                cursor.execute(sql, params)
                conn.commit()
                LogManager.log_update('stok', 'stok.urunler', None, 'Kayit guncellendi')

            QMessageBox.information(self, "Başarılı", "Ürün kartı güncellendi!")

            self.edit_mode = False
            self.edit_btn.setText("Düzenle")
            self.edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {brand.PRIMARY};
                    color: white;
                    border: none;
                    border-radius: {brand.R_SM}px;
                    padding: 0 {brand.SP_5}px;
                    font-size: {brand.FS_BODY_SM}px;
                    font-weight: {brand.FW_SEMIBOLD};
                }}
                QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
            """)
            self._set_edit_enabled(False)
            self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası:\n{str(e)}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _add_bom_item(self):
        """Ürün ağacına bileşen ekle"""
        dialog = BOMDialog(self.theme, self.urun_id, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                # silindi_mi sütunu var mı kontrol et
                cursor.execute("""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = 'stok' AND TABLE_NAME = 'urun_agaci' AND COLUMN_NAME = 'silindi_mi'
                """)
                has_silindi = cursor.fetchone()[0] > 0

                # Aynı bileşen var mı kontrol et
                if has_silindi:
                    cursor.execute("""
                        SELECT id FROM stok.urun_agaci
                        WHERE ana_urun_id = ? AND bilesen_urun_id = ? AND aktif_mi = 1 AND (silindi_mi = 0 OR silindi_mi IS NULL)
                    """, (self.urun_id, data['bilesen_urun_id']))
                else:
                    cursor.execute("""
                        SELECT id FROM stok.urun_agaci
                        WHERE ana_urun_id = ? AND bilesen_urun_id = ? AND aktif_mi = 1
                    """, (self.urun_id, data['bilesen_urun_id']))

                if cursor.fetchone():
                    QMessageBox.warning(self, "Uyarı", "Bu bileşen zaten ürün ağacında mevcut!")
                    return

                # Ekle - silindi_mi sütunu olmadan
                cursor.execute("""
                    INSERT INTO stok.urun_agaci (uuid, ana_urun_id, bilesen_urun_id, miktar, birim_id, bilesen_tipi, fire_orani, aktif_mi, olusturma_tarihi, guncelleme_tarihi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, GETDATE(), GETDATE())
                """, (str(uuid.uuid4()), self.urun_id, data['bilesen_urun_id'], data['miktar'], data['birim_id'], data['bilesen_tipi'], data['fire_orani']))

                conn.commit()
                LogManager.log_insert('stok', 'stok.urun_agaci', None, 'Yeni kayit eklendi')

                self._load_bom()
                QMessageBox.information(self, "Başarılı", "Bileşen eklendi!")

            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Bileşen eklenemedi: {e}")
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass
    
    def _add_fiyat(self):
        if not self.urun_id:
            QMessageBox.warning(self, "Uyari", "Urun secili degil!"); return

        t = self.theme
        dlg = QDialog(self)
        dlg.setWindowTitle("Fiyat Ekle")
        dlg.setMinimumWidth(450); dlg.setModal(True)
        dlg.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QComboBox, QDoubleSpinBox, QDateEdit, QLineEdit {{ background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px; color: {brand.TEXT}; }}
        """)
        lay = QVBoxLayout(dlg); lay.setContentsMargins(20, 20, 20, 20); lay.setSpacing(14)
        lay.addWidget(QLabel("Yeni Fiyat Ekle"))

        form = QFormLayout(); form.setSpacing(10)

        cmb_tip = QComboBox()
        cmb_tip.addItems(["ALIS", "SATIS", "LISTE", "KAMPANYA"])
        form.addRow("Fiyat Tipi:", cmb_tip)

        from PySide6.QtWidgets import QDoubleSpinBox, QDateEdit
        spin_fiyat = QDoubleSpinBox(); spin_fiyat.setRange(0, 99999999); spin_fiyat.setDecimals(4)
        form.addRow("Fiyat:", spin_fiyat)

        cmb_pb = QComboBox()
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT kod FROM tanim.para_birimleri WHERE aktif_mi = 1 ORDER BY CASE WHEN varsayilan_mi = 1 THEN 0 ELSE 1 END, kod")
            for r in cursor.fetchall(): cmb_pb.addItem(r[0])
            conn.close()
        except:
            cmb_pb.addItems(["TRY", "USD", "EUR"])
        form.addRow("Para Birimi:", cmb_pb)

        from PySide6.QtCore import QDate
        dt_gecerlilik = QDateEdit(); dt_gecerlilik.setDate(QDate.currentDate()); dt_gecerlilik.setCalendarPopup(True)
        form.addRow("Gecerlilik:", dt_gecerlilik)

        cmb_cari = QComboBox(); cmb_cari.addItem("-- Genel --", None)
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT id, unvan FROM musteri.cariler WHERE aktif_mi = 1 ORDER BY unvan")
            for r in cursor.fetchall(): cmb_cari.addItem(r[1][:40], r[0])
            conn.close()
        except: pass
        form.addRow("Cari:", cmb_cari)

        lay.addLayout(form)

        btn_bar = QHBoxLayout(); btn_bar.addStretch()
        btn_iptal = QPushButton("Iptal"); btn_iptal.clicked.connect(dlg.reject); btn_bar.addWidget(btn_iptal)
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setStyleSheet(f"background: {brand.SUCCESS}; color: white; padding: 8px 20px; border-radius: 6px; font-weight: bold;")

        def _save_fiyat():
            fiyat = spin_fiyat.value()
            if fiyat <= 0:
                QMessageBox.warning(dlg, "Uyari", "Fiyat giriniz!"); return
            try:
                conn = get_db_connection(); cursor = conn.cursor()
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'stok' AND TABLE_NAME = 'urun_fiyatlari')
                    BEGIN
                        CREATE TABLE stok.urun_fiyatlari (
                            id BIGINT IDENTITY(1,1) PRIMARY KEY,
                            urun_id BIGINT NOT NULL,
                            fiyat_tipi NVARCHAR(20),
                            fiyat DECIMAL(18,4),
                            para_birimi NVARCHAR(10) DEFAULT 'TRY',
                            gecerlilik_baslangic DATE,
                            gecerlilik_bitis DATE,
                            cari_id BIGINT,
                            aktif_mi BIT DEFAULT 1,
                            olusturma_tarihi DATETIME DEFAULT GETDATE()
                        )
                    END
                """)
                cursor.execute("""
                    INSERT INTO stok.urun_fiyatlari (urun_id, fiyat_tipi, fiyat, para_birimi, gecerlilik_baslangic, cari_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (self.urun_id, cmb_tip.currentText(), fiyat, cmb_pb.currentText(),
                      dt_gecerlilik.date().toPython(), cmb_cari.currentData()))
                conn.commit(); conn.close()
                QMessageBox.information(dlg, "Basarili", "Fiyat eklendi!")
                dlg.accept()
                self._load_fiyatlar()
            except Exception as e:
                QMessageBox.critical(dlg, "Hata", str(e))

        btn_kaydet.clicked.connect(_save_fiyat)
        btn_bar.addWidget(btn_kaydet)
        lay.addLayout(btn_bar)
        dlg.exec()
    
    def _upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "",
            "Tüm Dosyalar (*);;PDF (*.pdf);;Resimler (*.jpg *.png)")
        if file_path:
            QMessageBox.information(self, "Bilgi", f"Dosya seçildi:\n{file_path}\n\nYükleme özelliği yakında aktif olacak.")
    
    def _open_folder(self):
        if os.path.exists(NAS_IMAGE_PATH):
            os.startfile(NAS_IMAGE_PATH)
        else:
            QMessageBox.warning(self, "Hata", f"Klasör bulunamadı:\n{NAS_IMAGE_PATH}")
    
    def _open_file(self, index):
        row = index.row()
        file_path = self.dosya_table.item(row, 1).data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            os.startfile(file_path)
        else:
            QMessageBox.warning(self, "Hata", "Dosya bulunamadı!")


# ==================== YENİ ÜRÜN DIALOG ====================

class YeniUrunDialog(QDialog):
    """Yeni stok kartı ekleme dialog'u"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.yeni_id = None
        self.setWindowTitle("Yeni Stok Kartı")
        self.setMinimumSize(600, 550)
        self._setup_ui()
        self._load_combos()
        add_minimize_button(self)

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("➕ Yeni Stok Kartı Oluştur")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {brand.PRIMARY};")
        layout.addWidget(title)

        input_style = f"""
            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QTextEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 8px;
                color: {brand.TEXT};
            }}
        """
        label_style = f"color: {brand.TEXT}; font-size: 12px;"

        form_frame = QFrame()
        form_frame.setStyleSheet(f"background: {brand.BG_CARD}; border-radius: 8px;")
        form = QFormLayout(form_frame)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        # Ürün Kodu (zorunlu)
        self.urun_kodu = QLineEdit()
        self.urun_kodu.setPlaceholderText("Örn: PRD-001")
        self.urun_kodu.setStyleSheet(input_style)
        lbl = QLabel("Ürün Kodu *:")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, self.urun_kodu)

        # Ürün Adı (zorunlu)
        self.urun_adi = QLineEdit()
        self.urun_adi.setPlaceholderText("Ürün açıklaması")
        self.urun_adi.setStyleSheet(input_style)
        lbl = QLabel("Ürün Adı *:")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, self.urun_adi)

        # Müşteri
        self.cari_combo = QComboBox()
        self.cari_combo.setStyleSheet(input_style)
        lbl = QLabel("Müşteri:")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, self.cari_combo)

        # Müşteri Parça No
        self.musteri_parca_no = QLineEdit()
        self.musteri_parca_no.setStyleSheet(input_style)
        lbl = QLabel("Müşteri Parça No:")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, self.musteri_parca_no)

        # Ürün Tipi
        self.tip_combo = QComboBox()
        self.tip_combo.setStyleSheet(input_style)
        lbl = QLabel("Ürün Tipi *:")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, self.tip_combo)

        # Birim
        self.birim_combo = QComboBox()
        self.birim_combo.setStyleSheet(input_style)
        lbl = QLabel("Birim *:")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, self.birim_combo)

        # Kaplama Türü
        self.kaplama_combo = QComboBox()
        self.kaplama_combo.setStyleSheet(input_style)
        lbl = QLabel("Kaplama Türü:")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, self.kaplama_combo)

        # Yüzey Alanı
        self.yuzey_alani = QDoubleSpinBox()
        self.yuzey_alani.setDecimals(4)
        self.yuzey_alani.setRange(0, 999999)
        self.yuzey_alani.setStyleSheet(input_style)
        lbl = QLabel("Yüzey Alanı (m²):")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, self.yuzey_alani)

        # Ağırlık
        self.agirlik = QDoubleSpinBox()
        self.agirlik.setDecimals(4)
        self.agirlik.setRange(0, 999999)
        self.agirlik.setStyleSheet(input_style)
        lbl = QLabel("Ağırlık (kg):")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, self.agirlik)

        # Not
        self.notlar = QTextEdit()
        self.notlar.setMaximumHeight(60)
        self.notlar.setStyleSheet(input_style)
        lbl = QLabel("Notlar:")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, self.notlar)

        layout.addWidget(form_frame)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 10px 24px;
            }}
        """)
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)

        kaydet_btn = QPushButton("💾 Kaydet")
        kaydet_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
            }}
        """)
        kaydet_btn.clicked.connect(self._kaydet)
        btn_layout.addWidget(kaydet_btn)

        layout.addLayout(btn_layout)

    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Müşteriler
            self.cari_combo.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, COALESCE(unvan, kisa_ad) FROM musteri.cariler WHERE aktif_mi = 1 ORDER BY unvan")
            for row in cursor.fetchall():
                self.cari_combo.addItem(row[1], row[0])

            # Ürün Tipleri
            self.tip_combo.addItem("-- Seçiniz --", None)
            try:
                cursor.execute("SELECT id, ad FROM stok.urun_tipleri WHERE aktif_mi = 1 ORDER BY ad")
                for row in cursor.fetchall():
                    self.tip_combo.addItem(row[1], row[0])
            except Exception:
                # Tablo yoksa sabit değerler
                for tip in ['MAMUL', 'YARI_MAMUL', 'HAMMADDE', 'YARDIMCI']:
                    self.tip_combo.addItem(tip, tip)

            # Birimler
            self.birim_combo.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, COALESCE(ad, kod) FROM tanim.birimler WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.birim_combo.addItem(row[1], row[0])

            # Kaplama Türleri
            self.kaplama_combo.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, ad FROM tanim.kaplama_turleri WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.kaplama_combo.addItem(row[1], row[0])

            conn.close()
        except Exception as e:
            print(f"Combo yükleme hatası: {e}")

    def _kaydet(self):
        urun_kodu = self.urun_kodu.text().strip()
        urun_adi = self.urun_adi.text().strip()

        if not urun_kodu:
            QMessageBox.warning(self, "Uyarı", "Ürün kodu zorunludur!")
            self.urun_kodu.setFocus()
            return
        if not urun_adi:
            QMessageBox.warning(self, "Uyarı", "Ürün adı zorunludur!")
            self.urun_adi.setFocus()
            return

        birim_id = self.birim_combo.currentData()
        if not birim_id:
            QMessageBox.warning(self, "Uyarı", "Birim seçimi zorunludur!")
            return

        # urun_tipi: id veya string olabilir
        tip_data = self.tip_combo.currentData()
        tip_id = None
        tip_str = 'MAMUL'
        if isinstance(tip_data, int):
            tip_id = tip_data
        elif isinstance(tip_data, str):
            tip_str = tip_data

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Aynı kod var mı?
            cursor.execute("SELECT id FROM stok.urunler WHERE urun_kodu = ?", (urun_kodu,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Uyarı", f"'{urun_kodu}' kodlu ürün zaten mevcut!")
                conn.close()
                return

            # urun_tipi_id kolonu var mı kontrol
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'stok' AND TABLE_NAME = 'urunler' AND COLUMN_NAME = 'urun_tipi_id'
            """)
            has_tip_id = cursor.fetchone()[0] > 0

            if has_tip_id and tip_id:
                cursor.execute("""
                    INSERT INTO stok.urunler
                        (urun_kodu, urun_adi, cari_id, musteri_parca_no, urun_tipi, urun_tipi_id,
                         birim_id, kaplama_turu_id, yuzey_alani_m2, agirlik_kg, notlar)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, 'MAMUL', ?, ?, ?, ?, ?, ?)
                """, (
                    urun_kodu, urun_adi,
                    self.cari_combo.currentData(),
                    self.musteri_parca_no.text().strip() or None,
                    tip_id, birim_id,
                    self.kaplama_combo.currentData(),
                    self.yuzey_alani.value() or None,
                    self.agirlik.value() or None,
                    self.notlar.toPlainText().strip() or None
                ))
            else:
                cursor.execute("""
                    INSERT INTO stok.urunler
                        (urun_kodu, urun_adi, cari_id, musteri_parca_no, urun_tipi,
                         birim_id, kaplama_turu_id, yuzey_alani_m2, agirlik_kg, notlar)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    urun_kodu, urun_adi,
                    self.cari_combo.currentData(),
                    self.musteri_parca_no.text().strip() or None,
                    tip_str, birim_id,
                    self.kaplama_combo.currentData(),
                    self.yuzey_alani.value() or None,
                    self.agirlik.value() or None,
                    self.notlar.toPlainText().strip() or None
                ))

            row = cursor.fetchone()
            self.yeni_id = row[0] if row else 0

            conn.commit()
            conn.close()

            LogManager.log_insert('stok', 'stok.urunler', self.yeni_id, f"Yeni stok kartı: {urun_kodu}")
            QMessageBox.information(self, "Başarılı", f"Stok kartı oluşturuldu!\n\nKod: {urun_kodu}\nAd: {urun_adi}")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası:\n{e}")


# ==================== ANA LİSTE SAYFASI ====================

class StokListePage(BasePage):
    """Stok Kartları Listesi Sayfası - stok.urunler tablosu üzerinden"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.current_page = 1
        self.page_size = DEFAULT_PAGE_SIZE
        self.total_pages = 1
        self.total_items = 0
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_8, brand.SP_8, brand.SP_8, brand.SP_8)
        layout.setSpacing(brand.SP_6)

        # ================ HEADER ================
        header = QHBoxLayout()
        header.setSpacing(brand.SP_4)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)

        self.title_label = QLabel("Stok Kartları")
        self.title_label.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_TITLE_LG}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"letter-spacing: -0.4px;"
        )
        title_col.addWidget(self.title_label)

        self.subtitle_label = QLabel("Ürün ve malzeme kartlarını yönetin")
        self.subtitle_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px;"
        )
        title_col.addWidget(self.subtitle_label)

        header.addLayout(title_col)
        header.addStretch()

        self.stat_label = QLabel("Yükleniyor...")
        self.stat_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"padding: {brand.SP_2}px {brand.SP_4}px; "
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_SM}px;"
        )
        header.addWidget(self.stat_label)

        layout.addLayout(header)

        # ================ TOOLBAR ================
        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ürün kodu, adı veya barkod ile ara...")
        self.search_input.setMinimumWidth(brand.sp(280))
        self.search_input.setFixedHeight(brand.sp(40))
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.returnPressed.connect(self._on_search)
        toolbar.addWidget(self.search_input)

        self.kategori_combo = QComboBox()
        self.kategori_combo.addItem("Tüm Kategoriler", None)
        self.kategori_combo.setFixedHeight(brand.sp(40))
        self.kategori_combo.setStyleSheet(self._combo_style())
        self.kategori_combo.currentIndexChanged.connect(self._on_filter_change)
        toolbar.addWidget(self.kategori_combo)

        self.kaplama_combo = QComboBox()
        self.kaplama_combo.addItem("Tüm Kaplamalar", None)
        self.kaplama_combo.setFixedHeight(brand.sp(40))
        self.kaplama_combo.setStyleSheet(self._combo_style())
        self.kaplama_combo.currentIndexChanged.connect(self._on_filter_change)
        toolbar.addWidget(self.kaplama_combo)

        self.musteri_combo = QComboBox()
        self.musteri_combo.addItem("Tüm Müşteriler", None)
        self.musteri_combo.setFixedHeight(brand.sp(40))
        self.musteri_combo.setStyleSheet(self._combo_style())
        self.musteri_combo.currentIndexChanged.connect(self._on_filter_change)
        toolbar.addWidget(self.musteri_combo)

        self.aktif_combo = QComboBox()
        self.aktif_combo.addItem("Aktif", True)
        self.aktif_combo.addItem("Pasif", False)
        self.aktif_combo.addItem("Tümü", None)
        self.aktif_combo.setFixedHeight(brand.sp(40))
        self.aktif_combo.setStyleSheet(self._combo_style())
        self.aktif_combo.currentIndexChanged.connect(self._on_filter_change)
        toolbar.addWidget(self.aktif_combo)

        toolbar.addStretch()

        toolbar.addWidget(self.create_export_button(title="Urun Listesi"))

        btn_refresh = QPushButton("Yenile")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setFixedHeight(brand.sp(40))
        btn_refresh.setStyleSheet(self._button_style())
        btn_refresh.clicked.connect(self._load_data)
        toolbar.addWidget(btn_refresh)

        btn_yeni = QPushButton("+ Yeni Stok Kartı")
        btn_yeni.setCursor(Qt.PointingHandCursor)
        btn_yeni.setFixedHeight(brand.sp(40))
        btn_yeni.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        btn_yeni.clicked.connect(self._yeni_urun)
        toolbar.addWidget(btn_yeni)

        layout.addLayout(toolbar)

        # ================ TABLO ================
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Ürün Kodu", "Ürün Adı", "Müşteri", "Kategori", "Kaplama",
            "Kalınlık (µm)", "m²", "Ağırlık (kg)", "Birim", "Durum"
        ])
        self.table.setStyleSheet(self._table_style())
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(44))
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setFrameShape(QFrame.NoFrame)
        self.table.doubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.table, 1)

        # ================ SAYFALAMA ================
        self.paging_frame = QFrame()
        self.paging_frame.setFixedHeight(brand.sp(56))
        self.paging_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        p_layout = QHBoxLayout(self.paging_frame)
        p_layout.setContentsMargins(brand.SP_5, 0, brand.SP_5, 0)

        self.total_label = QLabel("")
        self.total_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"background: transparent; border: none;"
        )
        p_layout.addWidget(self.total_label)

        p_layout.addStretch()

        page_btn_style = f"""
            QPushButton {{
                background: transparent;
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.PRIMARY};
            }}
            QPushButton:disabled {{
                color: {brand.TEXT_DISABLED};
                border-color: {brand.BORDER};
            }}
        """

        self.prev_btn = QPushButton("‹  Önceki")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setFixedHeight(brand.sp(36))
        self.prev_btn.setStyleSheet(page_btn_style)
        self.prev_btn.clicked.connect(self._prev_page)
        p_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("Sayfa 1 / 1")
        self.page_label.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_MEDIUM}; "
            f"margin: 0 {brand.SP_4}px; "
            f"background: transparent; border: none;"
        )
        p_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("Sonraki  ›")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setFixedHeight(brand.sp(36))
        self.next_btn.setStyleSheet(page_btn_style)
        self.next_btn.clicked.connect(self._next_page)
        p_layout.addWidget(self.next_btn)

        layout.addWidget(self.paging_frame)

        self._load_filters()
    
    def _input_style(self):
        return f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus {{
                border-color: {brand.PRIMARY};
                background: {brand.BG_HOVER};
            }}
        """

    def _combo_style(self):
        return f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_3}px;
                color: {brand.TEXT};
                min-width: {brand.sp(130)}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:hover {{ border-color: {brand.BORDER_HARD}; }}
            QComboBox::drop-down {{ border: none; width: {brand.sp(28)}px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                color: {brand.TEXT};
                selection-background-color: {brand.PRIMARY};
                outline: 0;
                padding: {brand.SP_1}px;
            }}
        """

    def _button_style(self):
        return f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
            }}
        """

    def _table_style(self):
        return f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: 0;
                font-size: {brand.FS_BODY}px;
            }}
            QTableWidget::item {{
                padding: 0 {brand.SP_4}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
            }}
            QTableWidget::item:selected {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT};
            }}
            QHeaderView::section {{
                background: transparent;
                color: {brand.TEXT_DIM};
                padding: {brand.SP_3}px {brand.SP_4}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
                font-size: {brand.FS_CAPTION}px;
                font-weight: {brand.FW_SEMIBOLD};
                text-transform: uppercase;
                letter-spacing: 0.6px;
            }}
            QTableWidget QTableCornerButton::section {{
                background: transparent; border: none;
            }}
        """
    
    def _load_filters(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Kategoriler
            cursor.execute("SELECT id, ad FROM stok.urun_kategorileri WHERE aktif_mi = 1 ORDER BY sira_no, ad")
            for row in cursor.fetchall():
                self.kategori_combo.addItem(row[1], row[0])

            # Kaplama türleri
            cursor.execute("SELECT id, ad FROM tanim.kaplama_turleri WHERE aktif_mi = 1 ORDER BY sira, ad")
            for row in cursor.fetchall():
                self.kaplama_combo.addItem(row[1], row[0])

            # Müşteriler - Tüm aktif cariler
            cursor.execute("""
                SELECT id, unvan
                FROM musteri.cariler
                WHERE aktif_mi = 1 AND (silindi_mi = 0 OR silindi_mi IS NULL)
                ORDER BY unvan
            """)
            for row in cursor.fetchall():
                self.musteri_combo.addItem(row[1], row[0])
        except Exception as e:
            print(f"Filtre yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _load_data(self):
        self.stat_label.setText("Yükleniyor...")
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            where_conditions = ["(u.silindi_mi = 0 OR u.silindi_mi IS NULL)"]
            params = []

            # Arama
            arama = self.search_input.text().strip()
            if arama:
                where_conditions.append("(u.urun_kodu LIKE ? OR u.urun_adi LIKE ? OR u.musteri_parca_no LIKE ? OR u.barkod LIKE ?)")
                params.extend([f"%{arama}%"] * 4)

            # Kategori
            kategori = self.kategori_combo.currentData()
            if kategori:
                where_conditions.append("u.kategori_id = ?")
                params.append(kategori)

            # Kaplama
            kaplama = self.kaplama_combo.currentData()
            if kaplama:
                where_conditions.append("u.kaplama_turu_id = ?")
                params.append(kaplama)

            # Müşteri
            musteri = self.musteri_combo.currentData()
            if musteri:
                where_conditions.append("u.cari_id = ?")
                params.append(musteri)

            # Aktif
            aktif = self.aktif_combo.currentData()
            if aktif is not None:
                where_conditions.append("ISNULL(u.aktif_mi, 1) = ?")
                params.append(1 if aktif else 0)

            where_clause = " AND ".join(where_conditions)

            # Toplam sayı
            cursor.execute(f"SELECT COUNT(*) FROM stok.urunler u WHERE {where_clause}", params)
            self.total_items = cursor.fetchone()[0]
            self.total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)

            # Veri çek
            offset = (self.current_page - 1) * self.page_size
            cursor.execute(f"""
                SELECT u.id, u.urun_kodu, u.urun_adi, c.unvan, uk.ad, kt.ad,
                       u.kalinlik_hedef_um, u.yuzey_alani_m2, u.agirlik_kg, b.kod, u.aktif_mi
                FROM stok.urunler u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN stok.urun_kategorileri uk ON u.kategori_id = uk.id
                LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                WHERE {where_clause}
                ORDER BY u.urun_kodu
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, params + [offset, self.page_size])

            items = []
            for row in cursor.fetchall():
                items.append({
                    'id': row[0], 'urun_kodu': row[1], 'urun_adi': row[2],
                    'cari_unvani': row[3], 'kategori': row[4], 'kaplama': row[5],
                    'kalinlik': row[6], 'm2': row[7], 'agirlik': row[8],
                    'birim': row[9], 'aktif': row[10] if row[10] is not None else 1
                })

            self._populate_table(items)
            self._update_paging()
            self.stat_label.setText(f"Toplam: {self.total_items:,} kayıt")

        except Exception as e:
            self.stat_label.setText(f"Hata: {str(e)}")
            print(f"Veri yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _populate_table(self, items):
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('urun_kodu') or '')))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('urun_adi') or '')))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('cari_unvani') or '')))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('kategori') or '')))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('kaplama') or '')))
            self.table.setItem(row, 5, QTableWidgetItem(str(item.get('kalinlik') or '')))
            self.table.setItem(row, 6, QTableWidgetItem(f"{item.get('m2'):.4f}" if item.get('m2') else ''))
            self.table.setItem(row, 7, QTableWidgetItem(f"{item.get('agirlik'):.3f}" if item.get('agirlik') else ''))
            self.table.setItem(row, 8, QTableWidgetItem(str(item.get('birim') or '')))
            
            aktif = item.get('aktif', 1)
            durum = QTableWidgetItem("✓ Aktif" if aktif else "✗ Pasif")
            durum.setForeground(QColor('#22c55e') if aktif else QColor('#ef4444'))
            self.table.setItem(row, 9, durum)
            
            # ID'yi sakla
            self.table.item(row, 0).setData(Qt.UserRole, item.get('id'))
    
    def _update_paging(self):
        self.page_label.setText(f"Sayfa {self.current_page} / {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
        start = (self.current_page - 1) * self.page_size + 1
        end = min(self.current_page * self.page_size, self.total_items)
        self.total_label.setText(f"{start:,} - {end:,} / {self.total_items:,}")
    
    def _on_search(self):
        self.current_page = 1
        self._load_data()
    
    def _on_filter_change(self):
        self.current_page = 1
        self._load_data()
    
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load_data()
    
    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._load_data()
    
    def _yeni_urun(self):
        """Yeni stok kartı oluştur"""
        dialog = YeniUrunDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
            if dialog.yeni_id:
                detay = StokDetayDialog(dialog.yeni_id, self.theme, self)
                detay.exec()
                self._load_data()

    def _on_row_double_click(self, index):
        row = index.row()
        urun_id = self.table.item(row, 0).data(Qt.UserRole)
        if urun_id:
            dialog = StokDetayDialog(urun_id, self.theme, self)
            dialog.exec()
            self._load_data()
