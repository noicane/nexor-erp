# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Ekipman Kartları Sayfası
bakim.ekipmanlar tablosu için CRUD
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QSpinBox, QDoubleSpinBox, QTextEdit, QComboBox, QTabWidget,
    QWidget, QDateEdit, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand


# ============================================================================
# MODERN STYLE HELPER
# ============================================================================
def get_modern_style(theme: dict) -> dict:
    """Brand-based style helper (backward compat)"""
    return {
        'card_bg': brand.BG_CARD,
        'input_bg': brand.BG_INPUT,
        'border': brand.BORDER,
        'text': brand.TEXT,
        'text_secondary': brand.TEXT_MUTED,
        'text_muted': brand.TEXT_DIM,
        'primary': brand.PRIMARY,
        'primary_hover': brand.PRIMARY_HOVER,
        'success': brand.SUCCESS,
        'warning': brand.WARNING,
        'error': brand.ERROR,
        'danger': brand.ERROR,
        'info': brand.INFO,
        'bg_main': brand.BG_MAIN,
        'bg_hover': brand.BG_HOVER,
        'bg_selected': brand.BG_SELECTED,
        'border_light': brand.BORDER_HARD,
        'border_input': brand.BORDER,
        'card_solid': brand.BG_CARD,
        'gradient': '',
    }


class EkipmanDialog(QDialog):
    """Ekipman Ekleme/Düzenleme - Modern UI"""
    
    def __init__(self, theme: dict, ekipman_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.ekipman_id = ekipman_id
        self.data = {}
        
        self.setWindowTitle("Yeni Ekipman" if not ekipman_id else "Ekipman Düzenle")
        self.setMinimumSize(700, 750)
        self.setModal(True)
        
        if ekipman_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bakim.ekipmanlar WHERE id = ?", (self.ekipman_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 12px;
            }}
            QLabel {{
                color: {s['text']};
                background: transparent;
            }}
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {s['text']};
                font-size: 13px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border-color: {s['primary']};
            }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                color: {s['text']};
                selection-background-color: {s['primary']};
            }}
            QTabWidget::pane {{
                border: 1px solid {s['border']};
                background: {s['card_bg']};
                border-radius: 10px;
                padding: 16px;
            }}
            QTabBar::tab {{
                background: transparent;
                padding: 12px 24px;
                color: {s['text_muted']};
                font-weight: 500;
                border: none;
                border-bottom: 3px solid transparent;
            }}
            QTabBar::tab:hover {{
                color: {s['text']};
                background: rgba(255,255,255,0.05);
            }}
            QTabBar::tab:selected {{
                color: {s['primary']};
                border-bottom-color: {s['primary']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        icon = QLabel("🔧")
        icon.setStyleSheet("font-size: 28px;")
        header.addWidget(icon)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_genel_tab(), "📋 Genel")
        tabs.addTab(self._create_teknik_tab(), "⚙️ Teknik")
        tabs.addTab(self._create_maliyet_tab(), "💰 Maliyet / Tarih")
        layout.addWidget(tabs, 1)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {s['border']}; border-color: {s['primary']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾  Kaydet")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 28px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_genel_tab(self):
        s = self.s
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)
        
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        
        lbl = QLabel("Ekipman Kodu *")
        lbl.setStyleSheet(label_style)
        self.kod_input = QLineEdit(self.data.get('ekipman_kodu', ''))
        self.kod_input.setMaxLength(30)
        self.kod_input.setPlaceholderText("Örn: EKP-001")
        form.addRow(lbl, self.kod_input)
        
        lbl = QLabel("Ekipman Adı *")
        lbl.setStyleSheet(label_style)
        self.ad_input = QLineEdit(self.data.get('ekipman_adi', ''))
        self.ad_input.setMaxLength(100)
        self.ad_input.setPlaceholderText("Örn: Ana Pompa #1")
        form.addRow(lbl, self.ad_input)
        
        lbl = QLabel("Kategori *")
        lbl.setStyleSheet(label_style)
        self.kategori_combo = QComboBox()
        self.tipi_combo = QComboBox()
        self._load_kategoriler()
        self.kategori_combo.currentIndexChanged.connect(self._load_tipler)
        form.addRow(lbl, self.kategori_combo)
        
        lbl = QLabel("Ekipman Tipi *")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, self.tipi_combo)
        
        lbl = QLabel("Üretim Hattı")
        lbl.setStyleSheet(label_style)
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("-- Seçiniz --", None)
        self._load_hatlar()
        form.addRow(lbl, self.hat_combo)
        
        lbl = QLabel("Pozisyon")
        lbl.setStyleSheet(label_style)
        self.pozisyon_combo = QComboBox()
        self.pozisyon_combo.addItem("-- Seçiniz --", None)
        self.hat_combo.currentIndexChanged.connect(self._load_pozisyonlar)
        form.addRow(lbl, self.pozisyon_combo)
        
        lbl = QLabel("Lokasyon")
        lbl.setStyleSheet(label_style)
        self.lokasyon_input = QLineEdit(self.data.get('lokasyon', '') or '')
        self.lokasyon_input.setPlaceholderText("Örn: A Blok, Kat 2")
        form.addRow(lbl, self.lokasyon_input)
        
        lbl = QLabel("Kritiklik")
        lbl.setStyleSheet(label_style)
        self.kritiklik_combo = QComboBox()
        self.kritiklik_combo.addItem("-- Seçiniz --", None)
        for k, icon in [("DUSUK", "🟢"), ("NORMAL", "🟡"), ("YUKSEK", "🟠"), ("KRITIK", "🔴")]:
            self.kritiklik_combo.addItem(f"{icon} {k}", k)
        if self.data.get('kritiklik'):
            idx = self.kritiklik_combo.findData(self.data['kritiklik'])
            if idx >= 0: self.kritiklik_combo.setCurrentIndex(idx)
        form.addRow(lbl, self.kritiklik_combo)
        
        lbl = QLabel("Durum")
        lbl.setStyleSheet(label_style)
        self.durum_combo = QComboBox()
        for d, label in [("AKTIF", "✅ Aktif"), ("ARIZALI", "⚠️ Arızalı"), ("BAKIMDA", "🔧 Bakımda"), ("DEVRE_DISI", "❌ Devre Dışı")]:
            self.durum_combo.addItem(label, d)
        if self.data.get('durum'):
            idx = self.durum_combo.findData(self.data['durum'])
            if idx >= 0: self.durum_combo.setCurrentIndex(idx)
        form.addRow(lbl, self.durum_combo)
        
        lbl = QLabel("Notlar")
        lbl.setStyleSheet(label_style)
        self.notlar_input = QTextEdit()
        self.notlar_input.setMaximumHeight(80)
        self.notlar_input.setPlaceholderText("Ek notlar...")
        self.notlar_input.setText(self.data.get('notlar', '') or '')
        form.addRow(lbl, self.notlar_input)
        
        return widget
    
    def _create_teknik_tab(self):
        s = self.s
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)
        
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        
        lbl = QLabel("Marka")
        lbl.setStyleSheet(label_style)
        self.marka_input = QLineEdit(self.data.get('marka', '') or '')
        form.addRow(lbl, self.marka_input)
        
        lbl = QLabel("Model")
        lbl.setStyleSheet(label_style)
        self.model_input = QLineEdit(self.data.get('model', '') or '')
        form.addRow(lbl, self.model_input)
        
        lbl = QLabel("Seri No")
        lbl.setStyleSheet(label_style)
        self.seri_no_input = QLineEdit(self.data.get('seri_no', '') or '')
        form.addRow(lbl, self.seri_no_input)
        
        lbl = QLabel("Üretici")
        lbl.setStyleSheet(label_style)
        self.uretici_input = QLineEdit(self.data.get('uretici', '') or '')
        form.addRow(lbl, self.uretici_input)
        
        lbl = QLabel("Güç")
        lbl.setStyleSheet(label_style)
        self.guc_input = QDoubleSpinBox()
        self.guc_input.setRange(0, 99999)
        self.guc_input.setDecimals(2)
        self.guc_input.setSuffix(" kW")
        self.guc_input.setValue(self.data.get('guc_kw', 0) or 0)
        form.addRow(lbl, self.guc_input)
        
        lbl = QLabel("Kapasite")
        lbl.setStyleSheet(label_style)
        self.kapasite_input = QLineEdit(self.data.get('kapasite', '') or '')
        self.kapasite_input.setPlaceholderText("Örn: 100 L/dk")
        form.addRow(lbl, self.kapasite_input)
        
        lbl = QLabel("Teknik Özellikler")
        lbl.setStyleSheet(label_style)
        self.teknik_input = QTextEdit()
        self.teknik_input.setMaximumHeight(100)
        self.teknik_input.setPlaceholderText("Teknik detaylar...")
        self.teknik_input.setText(self.data.get('teknik_ozellikler', '') or '')
        form.addRow(lbl, self.teknik_input)
        
        return widget
    
    def _create_maliyet_tab(self):
        s = self.s
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)
        
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        
        lbl = QLabel("Satın Alma Tarihi")
        lbl.setStyleSheet(label_style)
        self.satin_alma_tarihi = QDateEdit()
        self.satin_alma_tarihi.setCalendarPopup(True)
        self.satin_alma_tarihi.setDisplayFormat("dd.MM.yyyy")
        if self.data.get('satin_alma_tarihi'):
            self.satin_alma_tarihi.setDate(self.data['satin_alma_tarihi'])
        else:
            self.satin_alma_tarihi.setDate(QDate.currentDate())
        form.addRow(lbl, self.satin_alma_tarihi)
        
        lbl = QLabel("Satın Alma Fiyatı")
        lbl.setStyleSheet(label_style)
        self.fiyat_input = QDoubleSpinBox()
        self.fiyat_input.setRange(0, 99999999)
        self.fiyat_input.setDecimals(2)
        self.fiyat_input.setSuffix(" ₺")
        self.fiyat_input.setValue(self.data.get('satin_alma_fiyati', 0) or 0)
        form.addRow(lbl, self.fiyat_input)
        
        lbl = QLabel("Garanti Bitiş")
        lbl.setStyleSheet(label_style)
        self.garanti_bitis = QDateEdit()
        self.garanti_bitis.setCalendarPopup(True)
        self.garanti_bitis.setDisplayFormat("dd.MM.yyyy")
        if self.data.get('garanti_bitis'):
            self.garanti_bitis.setDate(self.data['garanti_bitis'])
        else:
            self.garanti_bitis.setDate(QDate.currentDate().addYears(1))
        form.addRow(lbl, self.garanti_bitis)
        
        lbl = QLabel("Ekonomik Ömür")
        lbl.setStyleSheet(label_style)
        self.omur_input = QSpinBox()
        self.omur_input.setRange(0, 100)
        self.omur_input.setSuffix(" yıl")
        self.omur_input.setValue(self.data.get('ekonomik_omur_yil', 10) or 10)
        form.addRow(lbl, self.omur_input)
        
        return widget
    
    # ========== DATA METHODS (UNCHANGED) ==========
    def _load_kategoriler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM tanim.ekipman_kategorileri WHERE aktif_mi=1 ORDER BY ad")
            self.kategori_combo.addItem("-- Seçiniz --", None)
            for row in cursor.fetchall():
                self.kategori_combo.addItem(row[1], row[0])

            if self.data.get('ekipman_tipi_id'):
                cursor.execute("SELECT kategori_id FROM tanim.ekipman_tipleri WHERE id=?", (self.data['ekipman_tipi_id'],))
                r = cursor.fetchone()
                if r:
                    idx = self.kategori_combo.findData(r[0])
                    if idx >= 0:
                        self.kategori_combo.setCurrentIndex(idx)
        except Exception: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _load_tipler(self):
        self.tipi_combo.clear()
        self.tipi_combo.addItem("-- Seçiniz --", None)
        kategori_id = self.kategori_combo.currentData()
        if not kategori_id: return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM tanim.ekipman_tipleri WHERE kategori_id=? AND aktif_mi=1 ORDER BY ad", (kategori_id,))
            for row in cursor.fetchall():
                self.tipi_combo.addItem(row[1], row[0])

            if self.data.get('ekipman_tipi_id'):
                idx = self.tipi_combo.findData(self.data['ekipman_tipi_id'])
                if idx >= 0: self.tipi_combo.setCurrentIndex(idx)
        except Exception: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _load_hatlar(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod FROM tanim.uretim_hatlari WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no")
            for row in cursor.fetchall():
                self.hat_combo.addItem(row[1], row[0])

            if self.data.get('hat_id'):
                idx = self.hat_combo.findData(self.data['hat_id'])
                if idx >= 0: self.hat_combo.setCurrentIndex(idx)
        except Exception: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _load_pozisyonlar(self):
        self.pozisyon_combo.clear()
        self.pozisyon_combo.addItem("-- Seçiniz --", None)
        hat_id = self.hat_combo.currentData()
        if not hat_id: return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM tanim.hat_pozisyonlar WHERE hat_id=? AND aktif_mi=1 ORDER BY sira_no", (hat_id,))
            for row in cursor.fetchall():
                self.pozisyon_combo.addItem(row[1], row[0])

            if self.data.get('pozisyon_id'):
                idx = self.pozisyon_combo.findData(self.data['pozisyon_id'])
                if idx >= 0: self.pozisyon_combo.setCurrentIndex(idx)
        except Exception: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _save(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()
        tipi_id = self.tipi_combo.currentData()

        if not kod or not ad or not tipi_id:
            QMessageBox.warning(self, "⚠️ Eksik Bilgi", "Ekipman Kodu, Adı ve Tipi zorunludur!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            params = (
                kod, ad, tipi_id,
                self.hat_combo.currentData(), self.pozisyon_combo.currentData(),
                self.lokasyon_input.text().strip() or None,
                self.kritiklik_combo.currentData(), self.durum_combo.currentData(),
                self.marka_input.text().strip() or None, self.model_input.text().strip() or None,
                self.seri_no_input.text().strip() or None, self.uretici_input.text().strip() or None,
                self.guc_input.value() or None, self.kapasite_input.text().strip() or None,
                self.teknik_input.toPlainText().strip() or None,
                self.satin_alma_tarihi.date().toPython(), self.fiyat_input.value() or None,
                self.garanti_bitis.date().toPython(), self.omur_input.value() or None,
                self.notlar_input.toPlainText().strip() or None
            )

            if self.ekipman_id:
                cursor.execute("""UPDATE bakim.ekipmanlar SET ekipman_kodu=?, ekipman_adi=?, ekipman_tipi_id=?,
                    hat_id=?, pozisyon_id=?, lokasyon=?, kritiklik=?, durum=?,
                    marka=?, model=?, seri_no=?, uretici=?, guc_kw=?, kapasite=?, teknik_ozellikler=?,
                    satin_alma_tarihi=?, satin_alma_fiyati=?, garanti_bitis=?, ekonomik_omur_yil=?, notlar=?,
                    guncelleme_tarihi=GETDATE() WHERE id=?""",
                    params + (self.ekipman_id,))
            else:
                cursor.execute("""INSERT INTO bakim.ekipmanlar (ekipman_kodu, ekipman_adi, ekipman_tipi_id,
                    hat_id, pozisyon_id, lokasyon, kritiklik, durum,
                    marka, model, seri_no, uretici, guc_kw, kapasite, teknik_ozellikler,
                    satin_alma_tarihi, satin_alma_fiyati, garanti_bitis, ekonomik_omur_yil, notlar)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", params)

            conn.commit()
            LogManager.log_insert('bakim', 'bakim.ekipmanlar', None, 'Ekipman kaydi eklendi')
            QMessageBox.information(self, "✓ Başarılı", "Ekipman kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass


class BakimEkipmanPage(BasePage):
    """Ekipman Kartları Listesi - Modern UI"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        
        title_row = QHBoxLayout()
        icon = QLabel("🔧")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Ekipman Kartları")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        
        subtitle = QLabel("Pompa, ısıtıcı, sensör vb. ekipmanları yönetin")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()
        
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(f"""
            color: {s['text_muted']};
            font-size: 13px;
            padding: 8px 16px;
            background: {s['card_bg']};
            border: 1px solid {s['border']};
            border-radius: 8px;
        """)
        header.addWidget(self.stat_label)
        
        layout.addLayout(header)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara (Kod, Ad)")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 14px;
                color: {s['text']};
                font-size: 13px;
                min-width: 200px;
            }}
            QLineEdit:focus {{ border-color: {s['primary']}; }}
        """)
        self.search_input.returnPressed.connect(self._load_data)
        toolbar.addWidget(self.search_input)
        
        combo_style = f"""
            QComboBox {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {s['text']};
                min-width: 130px;
                font-size: 13px;
            }}
            QComboBox:hover {{ border-color: {s['border_light']}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                color: {s['text']};
                selection-background-color: {s['primary']};
            }}
        """
        
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("🏭 Tüm Hatlar", None)
        self._load_hat_filter()
        self.hat_combo.setStyleSheet(combo_style)
        self.hat_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.hat_combo)
        
        self.durum_combo = QComboBox()
        self.durum_combo.addItem("📊 Tüm Durumlar", None)
        self.durum_combo.addItem("✅ Aktif", "AKTIF")
        self.durum_combo.addItem("⚠️ Arızalı", "ARIZALI")
        self.durum_combo.addItem("🔧 Bakımda", "BAKIMDA")
        self.durum_combo.addItem("❌ Devre Dışı", "DEVRE_DISI")
        self.durum_combo.setStyleSheet(combo_style)
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.durum_combo)
        
        toolbar.addStretch()
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Yenile")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {s['border']}; border-color: {s['primary']}; }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(refresh_btn)
        
        add_btn = QPushButton("➕  Yeni Ekipman")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        add_btn.clicked.connect(self._add_new)
        toolbar.addWidget(add_btn)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 10px;
                gridline-color: {s['border']};
                color: {s['text']};
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {s['border']};
            }}
            QTableWidget::item:selected {{ background: {s['primary']}; }}
            QTableWidget::item:hover {{ background: rgba(220, 38, 38, 0.1); }}
            QHeaderView::section {{
                background: rgba(0,0,0,0.3);
                color: {s['text_secondary']};
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid {s['primary']};
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }}
        """)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Kategori", "Hat", "Marka/Model", "Kritiklik", "Durum", "Garanti", "İşlem"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 110)
        self.table.setColumnWidth(6, 85)
        self.table.setColumnWidth(7, 85)
        self.table.setColumnWidth(8, 90)
        self.table.setColumnWidth(9, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    # ========== DATA METHODS (UNCHANGED) ==========
    def _load_hat_filter(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod FROM tanim.uretim_hatlari WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no")
            for row in cursor.fetchall():
                self.hat_combo.addItem(row[1], row[0])
        except Exception: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _load_data(self):
        s = self.s
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """SELECT e.id, e.ekipman_kodu, e.ekipman_adi, ek.ad as kategori, h.kod as hat,
                     CONCAT(e.marka, ' ', e.model), e.kritiklik, e.durum, e.garanti_bitis
                     FROM bakim.ekipmanlar e
                     JOIN tanim.ekipman_tipleri et ON e.ekipman_tipi_id=et.id
                     JOIN tanim.ekipman_kategorileri ek ON et.kategori_id=ek.id
                     LEFT JOIN tanim.uretim_hatlari h ON e.hat_id=h.id
                     WHERE e.silindi_mi=0"""
            params = []

            search = self.search_input.text().strip()
            if search:
                sql += " AND (e.ekipman_kodu LIKE ? OR e.ekipman_adi LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            hat_id = self.hat_combo.currentData()
            if hat_id:
                sql += " AND e.hat_id=?"
                params.append(hat_id)

            durum = self.durum_combo.currentData()
            if durum:
                sql += " AND e.durum=?"
                params.append(durum)

            sql += " ORDER BY e.ekipman_kodu"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            durum_colors = {
                "AKTIF": s['success'], 
                "ARIZALI": s['error'], 
                "BAKIMDA": s['warning'], 
                "DEVRE_DISI": s['text_muted']
            }
            kritiklik_colors = {
                "KRITIK": s['error'], 
                "YUKSEK": s['warning'], 
                "NORMAL": "#EAB308", 
                "DUSUK": s['success']
            }
            
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                item = QTableWidgetItem(str(row[0]))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor(s['text_muted']))
                self.table.setItem(i, 0, item)
                
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or ''))
                self.table.setItem(i, 4, QTableWidgetItem(row[4] or '-'))
                self.table.setItem(i, 5, QTableWidgetItem(row[5] or '-'))
                
                kritiklik_item = QTableWidgetItem(row[6] or '-')
                if row[6] in kritiklik_colors:
                    kritiklik_item.setForeground(QColor(kritiklik_colors[row[6]]))
                kritiklik_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 6, kritiklik_item)
                
                durum_item = QTableWidgetItem(row[7] or '')
                if row[7] in durum_colors:
                    durum_item.setForeground(QColor(durum_colors[row[7]]))
                durum_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 7, durum_item)
                
                garanti = row[8].strftime("%d.%m.%Y") if row[8] else '-'
                garanti_item = QTableWidgetItem(garanti)
                garanti_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 8, garanti_item)
                
                # Action Buttons
                btn_widget = self.create_action_buttons([
                    ("", "Düzenle", lambda _, rid=row[0]: self._edit_item(rid), "edit"),
                    ("", "Sil", lambda _, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 9, btn_widget)
                self.table.setRowHeight(i, 48)
            
            self.stat_label.setText(f"📊 Toplam: {len(rows)} ekipman")
        except Exception as e:
            QMessageBox.warning(self, "⚠️ Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _add_new(self):
        dlg = EkipmanDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _edit_item(self, eid):
        dlg = EkipmanDialog(self.theme, eid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _delete_item(self, eid):
        if QMessageBox.question(self, "🗑️ Silme Onayı",
            "Bu ekipmanı silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE bakim.ekipmanlar SET silindi_mi=1, silinme_tarihi=GETDATE() WHERE id=?", (eid,))
                conn.commit()
                LogManager.log_delete('bakim', 'bakim.ekipmanlar', None, 'Kayit silindi (soft delete)')
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "❌ Hata", str(e))
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass
