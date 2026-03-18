# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Rework (Söküm) Yönetimi
[MODERNIZED UI - v3.0]

Sökümü bekleyen ürünler için iş emri oluşturma ve giriş yönetimi
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QTabWidget, QWidget,
    QComboBox, QSpinBox, QTextEdit, QDateEdit, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from datetime import datetime

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.hareket_motoru import HareketMotoru
from dialogs.login import ModernLoginDialog


def get_modern_style(theme: dict) -> dict:
    """Modern tema renkleri - TÜM MODÜLLERDE AYNI"""
    t = theme or {}
    return {
        'card_bg': t.get('bg_card', '#151B23'),
        'input_bg': t.get('bg_input', '#232C3B'),
        'border': t.get('border', '#1E2736'),
        'text': t.get('text', '#E8ECF1'),
        'text_secondary': t.get('text_secondary', '#8896A6'),
        'text_muted': t.get('text_muted', '#5C6878'),
        'primary': t.get('primary', '#DC2626'),
        'primary_hover': t.get('primary_hover', '#9B1818'),
        'success': t.get('success', '#10B981'),
        'warning': t.get('warning', '#F59E0B'),
        'error': t.get('error', '#EF4444'),
        'danger': t.get('error', '#EF4444'),
        'info': t.get('info', '#3B82F6'),
        'bg_main': t.get('bg_main', '#0F1419'),
        'bg_hover': t.get('bg_hover', '#1C2430'),
        'bg_selected': t.get('bg_selected', '#1E1215'),
        'border_light': t.get('border_light', '#2A3545'),
        'border_input': t.get('border_input', '#1E2736'),
        'card_solid': t.get('bg_card_solid', '#151B23'),
        'gradient': t.get('gradient_css', ''),
    }


class ReworkPage(BasePage):
    """Rework (Söküm) Yönetimi - İş Emri ve Giriş"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.setWindowTitle("🔄 Rework (Söküm) Yönetimi")
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Ana UI oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._get_tab_style())
        
        # Sekme 1: İş Emri Yönetimi
        self.tab_ie = self._create_is_emri_tab()
        self.tab_widget.addTab(self.tab_ie, "📄 İş Emri Yönetimi")
        
        # Sekme 2: Söküm Girişi
        self.tab_giris = self._create_giris_tab()
        self.tab_widget.addTab(self.tab_giris, "✅ Söküm Girişi")
        
        # Sekme 3: Depo Takip
        self.tab_depo = self._create_depo_takip_tab()
        self.tab_widget.addTab(self.tab_depo, "📊 Depo Takip")
        
        layout.addWidget(self.tab_widget)
    
    def _create_header(self):
        """Başlık oluştur"""
        header = QHBoxLayout()
        
        # Başlık
        title = QLabel("🔄 REWORK (SÖKÜM) YÖNETİMİ")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text', '#fff')};")
        header.addWidget(title)
        
        header.addStretch()
        
        # Yenile butonu
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(self._button_style())
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        
        header_widget = QWidget()
        header_widget.setLayout(header)
        return header_widget
    
    # ========================================================
    # SEKME 1: İŞ EMRİ YÖNETİMİ
    # ========================================================
    
    def _create_is_emri_tab(self):
        """İş emri yönetimi sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Bekleyen Sökümler
        bekleyen_header = QLabel("📋 Bekleyen Sökümler (SOKUM deposu)")
        bekleyen_header.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-weight: bold; font-size: 14px;")
        layout.addWidget(bekleyen_header)
        
        self.bekleyen_table = self._create_table([
            "Lot No", "Ürün Kodu", "Ürün Adı", "Miktar", 
            "Birim", "Depo", "Durum", "Tarih"
        ])
        self.bekleyen_table.itemSelectionChanged.connect(self._on_bekleyen_secim)
        layout.addWidget(self.bekleyen_table)
        
        # İş Emri Form
        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card', '#242938')}; border: 2px solid {self.theme.get('primary', '#6366f1')}; border-radius: 12px; }}")
        form_layout_main = QVBoxLayout(form_frame)
        form_layout_main.setContentsMargins(16, 16, 16, 16)
        form_layout_main.setSpacing(12)
        
        form_header = QLabel("🛠️ Yeni İş Emri Oluştur")
        form_header.setStyleSheet(f"color: {self.theme.get('primary', '#6366f1')}; font-weight: bold; font-size: 14px;")
        form_layout_main.addWidget(form_header)
        
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        
        row = 0
        
        # Lot No (Readonly)
        lbl_lot = QLabel("Lot No:")
        lbl_lot.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        form_layout.addWidget(lbl_lot, row, 0)
        self.ie_lot_edit = QLineEdit()
        self.ie_lot_edit.setReadOnly(True)
        self.ie_lot_edit.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_lot_edit, row, 1)
        
        # Ürün (Readonly)
        lbl_urun = QLabel("Ürün:")
        lbl_urun.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        form_layout.addWidget(lbl_urun, row, 2)
        self.ie_urun_edit = QLineEdit()
        self.ie_urun_edit.setReadOnly(True)
        self.ie_urun_edit.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_urun_edit, row, 3)
        
        row += 1
        
        # Miktar (Readonly)
        lbl_miktar = QLabel("Miktar:")
        lbl_miktar.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        form_layout.addWidget(lbl_miktar, row, 0)
        self.ie_miktar_edit = QLineEdit()
        self.ie_miktar_edit.setReadOnly(True)
        self.ie_miktar_edit.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_miktar_edit, row, 1)
        
        # Söküm Tipi (Sabit: Kimyasal)
        lbl_tip = QLabel("Söküm Tipi:")
        lbl_tip.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        form_layout.addWidget(lbl_tip, row, 2)
        self.ie_tip_combo = QComboBox()
        self.ie_tip_combo.addItem("Kimyasal")
        self.ie_tip_combo.setEnabled(False)
        self.ie_tip_combo.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_tip_combo, row, 3)
        
        row += 1
        
        # Sorumlu
        lbl_sorumlu = QLabel("Sorumlu:")
        lbl_sorumlu.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        form_layout.addWidget(lbl_sorumlu, row, 0)
        self.ie_sorumlu_combo = QComboBox()
        self.ie_sorumlu_combo.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_sorumlu_combo, row, 1)
        
        # Başlangıç Tarihi
        lbl_tarih = QLabel("Başlangıç:")
        lbl_tarih.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        form_layout.addWidget(lbl_tarih, row, 2)
        self.ie_tarih_edit = QDateEdit()
        self.ie_tarih_edit.setDate(datetime.now().date())
        self.ie_tarih_edit.setCalendarPopup(True)
        self.ie_tarih_edit.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_tarih_edit, row, 3)
        
        row += 1
        
        # Not
        lbl_not = QLabel("Not:")
        lbl_not.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        form_layout.addWidget(lbl_not, row, 0, Qt.AlignTop)
        self.ie_not_edit = QTextEdit()
        self.ie_not_edit.setMaximumHeight(80)
        self.ie_not_edit.setStyleSheet(self._input_style())
        form_layout.addWidget(self.ie_not_edit, row, 1, 1, 3)
        
        form_layout_main.addLayout(form_layout)
        
        row += 1
        
        # Buton
        self.ie_olustur_btn = QPushButton("📄 İş Emri Oluştur")
        self.ie_olustur_btn.setStyleSheet(f"QPushButton {{ background: {self.theme.get('success', '#22c55e')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold; }}")
        self.ie_olustur_btn.clicked.connect(self._is_emri_olustur)
        self.ie_olustur_btn.setEnabled(False)
        form_layout_main.addWidget(self.ie_olustur_btn)
        
        layout.addWidget(form_frame)
        
        # Aktif İş Emirleri
        aktif_header = QLabel("📊 Aktif İş Emirleri")
        aktif_header.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-weight: bold; font-size: 14px;")
        layout.addWidget(aktif_header)
        
        self.aktif_ie_table = self._create_table([
            "İş Emri No", "Lot No", "Ürün", "Miktar", 
            "Tip", "Durum", "Sorumlu", "Başlangıç"
        ])
        layout.addWidget(self.aktif_ie_table)
        
        return tab
    
    # ========================================================
    # SEKME 2: SÖKÜM GİRİŞİ
    # ========================================================
    
    def _create_giris_tab(self):
        """Söküm girişi sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Aktif İş Emirleri
        ie_header = QLabel("🔧 Aktif İş Emirleri")
        ie_header.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-weight: bold; font-size: 14px;")
        layout.addWidget(ie_header)
        
        self.giris_ie_table = self._create_table([
            "İş Emri No", "Lot No", "Ürün", "Toplam Miktar",
            "Tip", "Sorumlu", "Başlangıç"
        ])
        self.giris_ie_table.itemSelectionChanged.connect(self._on_giris_ie_secim)
        layout.addWidget(self.giris_ie_table)
        
        # Giriş Bilgileri
        giris_frame = QFrame()
        giris_frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card', '#242938')}; border: 2px solid {self.theme.get('primary', '#6366f1')}; border-radius: 12px; }}")
        giris_layout_main = QVBoxLayout(giris_frame)
        giris_layout_main.setContentsMargins(16, 16, 16, 16)
        giris_layout_main.setSpacing(12)
        
        giris_header = QLabel("✅ Giriş Bilgileri")
        giris_header.setStyleSheet(f"color: {self.theme.get('primary', '#6366f1')}; font-weight: bold; font-size: 14px;")
        giris_layout_main.addWidget(giris_header)
        
        giris_layout = QGridLayout()
        giris_layout.setSpacing(12)
        
        row = 0
        
        # İş Emri No (Readonly)
        lbl_ie = QLabel("İş Emri No:")
        lbl_ie.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        giris_layout.addWidget(lbl_ie, row, 0)
        self.giris_ie_edit = QLineEdit()
        self.giris_ie_edit.setReadOnly(True)
        self.giris_ie_edit.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_ie_edit, row, 1)
        
        # Lot No (Readonly)
        lbl_lot = QLabel("Lot No:")
        lbl_lot.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        giris_layout.addWidget(lbl_lot, row, 2)
        self.giris_lot_edit = QLineEdit()
        self.giris_lot_edit.setReadOnly(True)
        self.giris_lot_edit.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_lot_edit, row, 3)
        
        row += 1
        
        # Toplam Miktar (Readonly)
        lbl_toplam = QLabel("Toplam Miktar:")
        lbl_toplam.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        giris_layout.addWidget(lbl_toplam, row, 0)
        self.giris_toplam_edit = QLineEdit()
        self.giris_toplam_edit.setReadOnly(True)
        self.giris_toplam_edit.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_toplam_edit, row, 1)
        
        # Giriş Miktarı
        lbl_giris = QLabel("Giriş Miktarı:")
        lbl_giris.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        giris_layout.addWidget(lbl_giris, row, 2)
        self.giris_miktar_spin = QSpinBox()
        self.giris_miktar_spin.setMinimum(0)
        self.giris_miktar_spin.setMaximum(999999)
        self.giris_miktar_spin.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_miktar_spin, row, 3)
        
        row += 1
        
        # Kalite Durumu
        lbl_kalite = QLabel("Kalite Durumu:")
        lbl_kalite.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        giris_layout.addWidget(lbl_kalite, row, 0)
        self.giris_kalite_combo = QComboBox()
        self.giris_kalite_combo.addItems(["", "İYİ", "ORTA", "KÖTÜ"])
        self.giris_kalite_combo.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_kalite_combo, row, 1)
        
        # Söküm Süresi (dakika)
        lbl_sure = QLabel("Söküm Süresi (dk):")
        lbl_sure.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        giris_layout.addWidget(lbl_sure, row, 2)
        self.giris_sure_spin = QSpinBox()
        self.giris_sure_spin.setMinimum(0)
        self.giris_sure_spin.setMaximum(9999)
        self.giris_sure_spin.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_sure_spin, row, 3)
        
        row += 1
        
        # Not
        lbl_not = QLabel("Not:")
        lbl_not.setStyleSheet(f"color: {self.theme.get('text', '#fff')};")
        giris_layout.addWidget(lbl_not, row, 0, Qt.AlignTop)
        self.giris_not_edit = QTextEdit()
        self.giris_not_edit.setMaximumHeight(80)
        self.giris_not_edit.setStyleSheet(self._input_style())
        giris_layout.addWidget(self.giris_not_edit, row, 1, 1, 3)
        
        giris_layout_main.addLayout(giris_layout)
        
        # Buton
        self.giris_btn = QPushButton("✅ Kaydı Tamamla")
        self.giris_btn.setStyleSheet(f"QPushButton {{ background: {self.theme.get('success', '#22c55e')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold; }}")
        self.giris_btn.clicked.connect(self._giris_kaydet)
        self.giris_btn.setEnabled(False)
        giris_layout_main.addWidget(self.giris_btn)
        
        layout.addWidget(giris_frame)
        
        # Geçmiş Girişler
        gecmis_header = QLabel("📜 Geçmiş Girişler (Bugün)")
        gecmis_header.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-weight: bold; font-size: 14px;")
        layout.addWidget(gecmis_header)
        
        self.gecmis_table = self._create_table([
            "Tarih", "İş Emri No", "Lot No", "Giriş Miktarı",
            "Kalan", "Kalite", "Süre (dk)", "Yapan"
        ])
        layout.addWidget(self.gecmis_table)
        
        return tab
    
    # ========================================================
    # SEKME 3: DEPO TAKİP
    # ========================================================
    
    def _create_depo_takip_tab(self):
        """Depo takip sekmesi - Söküm sürecindeki depoları göster"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Başlık
        header = QLabel("📊 Söküm Süreci Depo Durumu")
        header.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-weight: bold; font-size: 16px;")
        layout.addWidget(header)
        
        # Depo kartları için container
        depo_frame = QFrame()
        depo_frame.setStyleSheet(f"background: {self.theme.get('bg_card', '#242938')}; border-radius: 12px; padding: 16px;")
        depo_layout = QVBoxLayout(depo_frame)
        
        # Depo kartları grid
        depo_grid = QGridLayout()
        depo_grid.setSpacing(16)
        
        # İlgili depolar: RED, Yi, SOKUM, KAB-01
        ilgili_depolar = [
            ('RED', 'RED Deposu', '🔴', 'danger'),
            ('Yi', 'Söküm Bekleyen', '🟡', 'warning'),
            ('SOKUM', 'Söküm Deposu', '🟠', 'warning'),
            ('KAB-01', 'Kabul Alanı', '🟢', 'success')
        ]
        
        self.depo_widgets = {}
        
        for idx, (kod, ad, icon, renk) in enumerate(ilgili_depolar):
            row = idx // 2
            col = idx % 2
            
            # Depo kartı
            kart = QFrame()
            kart_renk = self.theme.get(renk, '#6366f1')
            kart.setStyleSheet(f"""
                QFrame {{
                    background: {self.theme.get('bg_main', '#1a1f2e')};
                    border: 2px solid {kart_renk};
                    border-radius: 10px;
                    padding: 12px;
                }}
            """)
            kart_layout = QVBoxLayout(kart)
            kart_layout.setSpacing(8)
            
            # Başlık
            baslik = QLabel(f"{icon} {ad} ({kod})")
            baslik.setStyleSheet(f"color: {kart_renk}; font-weight: bold; font-size: 14px;")
            kart_layout.addWidget(baslik)
            
            # Miktar etiketi
            miktar_lbl = QLabel("0 adet")
            miktar_lbl.setObjectName(f"miktar_{kod}")
            miktar_lbl.setStyleSheet(f"color: {self.theme.get('text', '#fff')}; font-size: 24px; font-weight: bold;")
            kart_layout.addWidget(miktar_lbl)
            
            # Lot sayısı
            lot_lbl = QLabel("0 lot")
            lot_lbl.setObjectName(f"lot_{kod}")
            lot_lbl.setStyleSheet(f"color: {self.theme.get('text_muted', '#8a94a6')}; font-size: 12px;")
            kart_layout.addWidget(lot_lbl)
            
            # Durum listesi
            durum_lbl = QLabel("")
            durum_lbl.setObjectName(f"durum_{kod}")
            durum_lbl.setStyleSheet(f"color: {self.theme.get('text_muted', '#8a94a6')}; font-size: 11px;")
            durum_lbl.setWordWrap(True)
            kart_layout.addWidget(durum_lbl)
            
            self.depo_widgets[kod] = {
                'miktar': miktar_lbl,
                'lot': lot_lbl,
                'durum': durum_lbl
            }
            
            depo_grid.addWidget(kart, row, col)
        
        depo_layout.addLayout(depo_grid)
        layout.addWidget(depo_frame)
        
        # Detay tablosu
        detay_header = QLabel("📋 Detaylı Stok Listesi")
        detay_header.setStyleSheet(f"color: {self.theme.get('primary', '#6366f1')}; font-weight: bold; font-size: 14px; margin-top: 16px;")
        layout.addWidget(detay_header)
        
        self.depo_detay_table = self._create_table([
            "Depo", "Lot No", "Ürün Kodu", "Ürün Adı", 
            "Miktar", "Birim", "Durum", "Son Hareket"
        ])
        layout.addWidget(self.depo_detay_table)
        
        # İlk yükleme
        self._load_depo_takip()
        
        return tab
    
    def _load_depo_takip(self):
        """Depo takip verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # İlgili depoların özeti
            cursor.execute("""
                SELECT 
                    d.kod,
                    COALESCE(SUM(sb.miktar), 0) as toplam_miktar,
                    COUNT(DISTINCT sb.lot_no) as lot_sayisi,
                    STUFF((
                        SELECT DISTINCT ', ' + sb2.durum_kodu
                        FROM stok.stok_bakiye sb2
                        WHERE sb2.depo_id = d.id AND sb2.miktar > 0
                        FOR XML PATH(''), TYPE
                    ).value('.', 'NVARCHAR(MAX)'), 1, 2, '') as durumlar
                FROM tanim.depolar d
                LEFT JOIN stok.stok_bakiye sb ON d.id = sb.depo_id AND sb.miktar > 0
                WHERE d.kod IN ('RED', 'Yi', 'SOKUM', 'KAB-01')
                GROUP BY d.kod, d.id
            """)
            
            for row in cursor.fetchall():
                kod, miktar, lot_sayisi, durumlar = row
                if kod in self.depo_widgets:
                    self.depo_widgets[kod]['miktar'].setText(f"{miktar:,.0f} adet")
                    self.depo_widgets[kod]['lot'].setText(f"{lot_sayisi} lot")
                    self.depo_widgets[kod]['durum'].setText(durumlar or "Boş")
            
            # Detay tablosu
            cursor.execute("""
                SELECT 
                    d.kod AS depo_kod,
                    sb.lot_no,
                    u.urun_kodu,
                    u.urun_adi,
                    sb.miktar,
                    sb.birim,
                    sb.durum_kodu,
                    sb.son_hareket_tarihi
                FROM stok.stok_bakiye sb
                JOIN tanim.depolar d ON sb.depo_id = d.id
                JOIN stok.urunler u ON sb.urun_id = u.id
                WHERE d.kod IN ('RED', 'Yi', 'SOKUM', 'KAB-01')
                  AND sb.miktar > 0
                ORDER BY d.kod, sb.lot_no
            """)
            
            self.depo_detay_table.setRowCount(0)
            
            for row_data in cursor.fetchall():
                row = self.depo_detay_table.rowCount()
                self.depo_detay_table.insertRow(row)
                
                for col, value in enumerate(row_data):
                    if col == 4:  # Miktar
                        value = f"{value:,.0f}"
                    elif col == 7:  # Tarih
                        value = value.strftime("%d.%m.%Y %H:%M") if value else ""
                    
                    item = QTableWidgetItem(str(value) if value else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # Depo kodu renklendirme
                    if col == 0:
                        if value == 'RED':
                            item.setForeground(QColor('#ef4444'))
                        elif value in ('Yi', 'SOKUM'):
                            item.setForeground(QColor('#f59e0b'))
                        elif value == 'KAB-01':
                            item.setForeground(QColor('#22c55e'))
                    
                    # Durum renklendirme
                    if col == 6:
                        if 'RED' in str(value):
                            item.setForeground(QColor('#ef4444'))
                        elif 'SOKUM' in str(value):
                            item.setForeground(QColor('#f59e0b'))
                        elif 'KABUL' in str(value):
                            item.setForeground(QColor('#22c55e'))
                    
                    self.depo_detay_table.setItem(row, col, item)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Depo takip yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    # ========================================================
    # VERİ YÜKLEME
    # ========================================================
    
    def _load_data(self):
        """Tüm verileri yükle"""
        self._load_bekleyen_sokumler()
        self._load_aktif_is_emirleri()
        self._load_sokum_is_emirleri()
        self._load_gecmis_girisler()
        self._load_sorumlular()
        self._load_depo_takip()  # ✅ Depo takip de yüklensin
    
    def _load_bekleyen_sokumler(self):
        """SOKUM deposundaki ürünleri listele"""
        self.bekleyen_table.setRowCount(0)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # ✅ Düzeltildi: LIKE 'SOKUM%' ile tüm SOKUM durumları, giris_tarihi kullanıldı
            cursor.execute("""
                SELECT 
                    sb.lot_no,
                    u.urun_kodu,
                    u.urun_adi,
                    sb.miktar,
                    sb.birim,
                    d.kod AS depo_kod,
                    sb.durum_kodu,
                    sb.giris_tarihi
                FROM stok.stok_bakiye sb
                JOIN stok.urunler u ON sb.urun_id = u.id
                JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE d.kod = 'SOKUM'
                  AND sb.miktar > 0
                  AND sb.durum_kodu LIKE 'SOKUM%'
                ORDER BY sb.giris_tarihi DESC
            """)
            
            rows = cursor.fetchall()
            
            for row_data in rows:
                row = self.bekleyen_table.rowCount()
                self.bekleyen_table.insertRow(row)
                
                for col, value in enumerate(row_data):
                    if col == 7:  # Tarih
                        value = value.strftime("%d.%m.%Y %H:%M") if value else ""
                    elif col == 3:  # Miktar
                        value = f"{value:,.0f}"
                    
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.bekleyen_table.setItem(row, col, item)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Bekleyen sökümler yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_aktif_is_emirleri(self):
        """Aktif iş emirlerini listele (İş Emri sekmesi için)"""
        self.aktif_ie_table.setRowCount(0)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    sie.is_emri_no,
                    sie.lot_no,
                    u.urun_adi,
                    sie.miktar,
                    sie.sokum_tipi,
                    sie.durum,
                    p.ad + ' ' + p.soyad AS sorumlu,
                    sie.baslangic_tarihi
                FROM uretim.sokum_is_emirleri sie
                LEFT JOIN stok.urunler u ON sie.urun_id = u.id
                LEFT JOIN ik.personeller p ON sie.sorumlu_id = p.id
                WHERE sie.durum IN ('BEKLEMEDE', 'DEVAM_EDIYOR')
                ORDER BY sie.id DESC
            """)
            
            rows = cursor.fetchall()
            
            for row_data in rows:
                row = self.aktif_ie_table.rowCount()
                self.aktif_ie_table.insertRow(row)
                
                for col, value in enumerate(row_data):
                    if col == 7:  # Tarih
                        value = value.strftime("%d.%m.%Y") if value else ""
                    elif col == 3:  # Miktar
                        value = f"{value:,.0f}"
                    
                    item = QTableWidgetItem(str(value) if value else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # Durum renklendirme
                    if col == 5:  # Durum kolonu
                        if value == 'BEKLEMEDE':
                            item.setForeground(QColor('#fbbf24'))  # amber
                        elif value == 'DEVAM_EDIYOR':
                            item.setForeground(QColor('#3b82f6'))  # blue
                    
                    self.aktif_ie_table.setItem(row, col, item)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Aktif iş emirleri yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_sokum_is_emirleri(self):
        """Söküm girişi için aktif iş emirlerini listele"""
        self.giris_ie_table.setRowCount(0)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    sie.id,
                    sie.is_emri_no,
                    sie.lot_no,
                    u.urun_adi,
                    sie.miktar,
                    sie.sokum_tipi,
                    p.ad + ' ' + p.soyad AS sorumlu,
                    sie.baslangic_tarihi
                FROM uretim.sokum_is_emirleri sie
                LEFT JOIN stok.urunler u ON sie.urun_id = u.id
                LEFT JOIN ik.personeller p ON sie.sorumlu_id = p.id
                WHERE sie.durum IN ('BEKLEMEDE', 'DEVAM_EDIYOR')
                  AND sie.miktar > 0
                ORDER BY sie.id DESC
            """)
            
            rows = cursor.fetchall()
            
            for row_data in rows:
                row = self.giris_ie_table.rowCount()
                self.giris_ie_table.insertRow(row)
                
                # id'yi sakla (görünmez)
                ie_id = row_data[0]
                
                for col, value in enumerate(row_data[1:], start=0):
                    if col == 6:  # Tarih
                        value = value.strftime("%d.%m.%Y") if value else ""
                    elif col == 3:  # Miktar
                        value = f"{value:,.0f}"
                    
                    item = QTableWidgetItem(str(value) if value else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # İlk satıra id'yi sakla
                    if col == 0:
                        item.setData(Qt.UserRole, ie_id)
                    
                    self.giris_ie_table.setItem(row, col, item)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İş emirleri yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_gecmis_girisler(self):
        """Bugünkü girişleri listele"""
        self.gecmis_table.setRowCount(0)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    sg.giris_tarihi,
                    sie.is_emri_no,
                    sg.lot_no,
                    sg.giris_miktar,
                    sg.kalan_miktar,
                    sg.kalite_durumu,
                    sg.sokum_suresi,
                    p.ad + ' ' + p.soyad AS yapan
                FROM uretim.sokum_giris sg
                JOIN uretim.sokum_is_emirleri sie ON sg.sokum_is_emri_id = sie.id
                LEFT JOIN ik.personeller p ON sg.giris_yapan_id = p.id
                WHERE CAST(sg.giris_tarihi AS DATE) = CAST(GETDATE() AS DATE)
                ORDER BY sg.id DESC
            """)
            
            rows = cursor.fetchall()
            
            for row_data in rows:
                row = self.gecmis_table.rowCount()
                self.gecmis_table.insertRow(row)
                
                for col, value in enumerate(row_data):
                    if col == 0:  # Tarih
                        value = value.strftime("%d.%m.%Y %H:%M") if value else ""
                    elif col in [3, 4]:  # Miktar kolonları
                        value = f"{value:,.0f}" if value else "0"
                    
                    item = QTableWidgetItem(str(value) if value else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.gecmis_table.setItem(row, col, item)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Geçmiş girişler yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_sorumlular(self):
        """Sorumlu personel listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, ad + ' ' + soyad AS ad_soyad
                FROM ik.personeller
                WHERE aktif_mi = 1
                ORDER BY ad, soyad
            """)
            
            self.ie_sorumlu_combo.clear()
            self.ie_sorumlu_combo.addItem("-- Seçiniz --", None)
            
            for row in cursor.fetchall():
                self.ie_sorumlu_combo.addItem(row[1], row[0])
            
            conn.close()
            
        except Exception as e:
            print(f"Sorumlular yüklenemedi: {e}")
            import traceback
            traceback.print_exc()
    
    # ========================================================
    # EVENT HANDLERS
    # ========================================================
    
    def _on_bekleyen_secim(self):
        """Bekleyen sökümlerden seçim yapıldığında"""
        selected = self.bekleyen_table.selectedItems()
        if not selected:
            self.ie_olustur_btn.setEnabled(False)
            return
        
        row = selected[0].row()
        
        lot_no = self.bekleyen_table.item(row, 0).text()
        urun_kodu = self.bekleyen_table.item(row, 1).text()
        urun_adi = self.bekleyen_table.item(row, 2).text()
        miktar = self.bekleyen_table.item(row, 3).text()
        
        self.ie_lot_edit.setText(lot_no)
        self.ie_urun_edit.setText(f"{urun_kodu} - {urun_adi}")
        self.ie_miktar_edit.setText(miktar)
        
        self.ie_olustur_btn.setEnabled(True)
    
    def _on_giris_ie_secim(self):
        """Giriş için iş emri seçildiğinde"""
        selected = self.giris_ie_table.selectedItems()
        if not selected:
            self.giris_btn.setEnabled(False)
            return
        
        row = selected[0].row()
        
        ie_no = self.giris_ie_table.item(row, 0).text()
        lot_no = self.giris_ie_table.item(row, 1).text()
        miktar = self.giris_ie_table.item(row, 3).text()
        
        # id'yi al
        ie_id = self.giris_ie_table.item(row, 0).data(Qt.UserRole)
        
        self.giris_ie_edit.setText(ie_no)
        self.giris_ie_edit.setProperty('ie_id', ie_id)
        self.giris_lot_edit.setText(lot_no)
        self.giris_toplam_edit.setText(miktar)
        
        # Miktar spin'i ayarla
        miktar_int = int(miktar.replace(',', '').replace('.', ''))
        self.giris_miktar_spin.setMaximum(miktar_int)
        self.giris_miktar_spin.setValue(miktar_int)
        
        self.giris_btn.setEnabled(True)
    
    # ========================================================
    # İŞ EMRİ İŞLEMLERİ
    # ========================================================
    
    def _is_emri_olustur(self):
        """Yeni iş emri oluştur"""
        try:
            lot_no = self.ie_lot_edit.text().strip()
            if not lot_no:
                QMessageBox.warning(self, "Uyarı", "Lot numarası seçilmedi!")
                return
            
            sorumlu_id = self.ie_sorumlu_combo.currentData()
            if not sorumlu_id:
                QMessageBox.warning(self, "Uyarı", "Sorumlu seçilmedi!")
                return
            
            baslangic = self.ie_tarih_edit.date().toPython()
            notlar = self.ie_not_edit.toPlainText().strip()
            
            # Lot'tan ürün bilgisini al
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # ✅ Düzeltildi: LIKE 'SOKUM%' ile
            cursor.execute("""
                SELECT sb.urun_id, sb.miktar
                FROM stok.stok_bakiye sb
                JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE sb.lot_no = ? 
                  AND d.kod = 'SOKUM'
                  AND sb.durum_kodu LIKE 'SOKUM%'
            """, (lot_no,))
            
            row = cursor.fetchone()
            if not row:
                raise Exception("Lot bilgisi bulunamadı!")
            
            urun_id, miktar = row
            
            # İş emri numarası oluştur (SOKUM-YYMMDD-XXXX formatında)
            tarih_str = datetime.now().strftime('%y%m%d')
            
            cursor.execute("""
                SELECT ISNULL(MAX(CAST(RIGHT(is_emri_no, 4) AS INT)), 0) + 1
                FROM uretim.sokum_is_emirleri
                WHERE is_emri_no LIKE ?
            """, (f'SOKUM-{tarih_str}-%',))
            
            sira = cursor.fetchone()[0]
            is_emri_no = f"SOKUM-{tarih_str}-{sira:04d}"
            
            # İş emrini kaydet
            cursor.execute("""
                INSERT INTO uretim.sokum_is_emirleri (
                    is_emri_no, lot_no, urun_id, miktar, sokum_tipi,
                    durum, sorumlu_id, baslangic_tarihi, notlar,
                    olusturan_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                is_emri_no,
                lot_no,
                urun_id,
                miktar,
                'Kimyasal',
                'BEKLEMEDE',
                sorumlu_id,
                baslangic,
                notlar or None,
                ModernLoginDialog.current_user_id or 1
            ))
            
            conn.commit()
            LogManager.log_insert('uretim', 'uretim.rework_is_emirleri', None,
                                  f'Rework is emri olusturuldu: {is_emri_no}, Lot: {lot_no}, {miktar} adet')
            conn.close()

            QMessageBox.information(
                self,
                "✓ Başarılı",
                f"İş emri oluşturuldu!\n\nİş Emri No: {is_emri_no}\nLot: {lot_no}"
            )
            
            # Formu temizle
            self.ie_lot_edit.clear()
            self.ie_urun_edit.clear()
            self.ie_miktar_edit.clear()
            self.ie_not_edit.clear()
            self.ie_sorumlu_combo.setCurrentIndex(0)
            self.ie_olustur_btn.setEnabled(False)
            
            # Verileri yenile
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İş emri oluşturulamadı: {e}")
            import traceback
            traceback.print_exc()
    
    # ========================================================
    # SÖKÜM GİRİŞİ İŞLEMLERİ
    # ========================================================
    
    def _giris_kaydet(self):
        """Söküm girişini kaydet"""
        try:
            ie_id = self.giris_ie_edit.property('ie_id')
            if not ie_id:
                QMessageBox.warning(self, "Uyarı", "İş emri seçilmedi!")
                return
            
            giris_miktar = self.giris_miktar_spin.value()
            if giris_miktar <= 0:
                QMessageBox.warning(self, "Uyarı", "Giriş miktarı 0'dan büyük olmalı!")
                return
            
            eski_lot_no = self.giris_lot_edit.text().strip()
            is_emri_no = self.giris_ie_edit.text().strip()
            toplam_miktar_str = self.giris_toplam_edit.text().replace(',', '').replace('.', '')
            toplam_miktar = int(toplam_miktar_str)
            
            if giris_miktar > toplam_miktar:
                QMessageBox.warning(
                    self, 
                    "Uyarı", 
                    f"Giriş miktarı ({giris_miktar}) toplam miktarı ({toplam_miktar}) aşamaz!"
                )
                return
            
            # ✅ YENİ LOT NUMARASI: -RED kaldır, -S ekle
            if eski_lot_no.endswith('-RED'):
                yeni_lot_no = eski_lot_no.replace('-RED', '-S')
            elif not eski_lot_no.endswith('-S'):
                yeni_lot_no = f"{eski_lot_no}-S"
            else:
                yeni_lot_no = eski_lot_no
            
            conn = get_db_connection()
            cursor = conn.cursor()
            motor = HareketMotoru(conn)
            
            # Depo ID'lerini al
            cursor.execute("SELECT id FROM tanim.depolar WHERE kod = 'KAB-01'")
            kab_depo_row = cursor.fetchone()
            if not kab_depo_row:
                raise Exception("KAB-01 deposu bulunamadı!")
            kab_depo_id = kab_depo_row[0]
            
            cursor.execute("SELECT id FROM tanim.depolar WHERE kod = 'SOKUM'")
            sokum_depo_row = cursor.fetchone()
            if not sokum_depo_row:
                raise Exception("SOKUM deposu bulunamadı!")
            sokum_depo_id = sokum_depo_row[0]
            
            # ✅ Ürün ID'sini al
            cursor.execute("""
                SELECT urun_id 
                FROM stok.stok_bakiye 
                WHERE lot_no = ? AND depo_id = ?
            """, (eski_lot_no, sokum_depo_id))
            
            urun_row = cursor.fetchone()
            if not urun_row:
                raise Exception(f"SOKUM deposunda {eski_lot_no} bulunamadı!")
            urun_id = urun_row[0]
            
            # ✅ 1. SOKUM deposundan ÇIKIŞ (eski lot)
            cikis_sonuc = motor.stok_cikis(
                lot_no=eski_lot_no,
                miktar=giris_miktar
            )
            
            if not cikis_sonuc.basarili:
                raise Exception(f"SOKUM'dan çıkış başarısız: {cikis_sonuc.mesaj}")
            
            # ✅ 2. KAB-01 deposuna GİRİŞ (yeni lot)
            giris_sonuc = motor.stok_giris(
                urun_id=urun_id,
                lot_no=yeni_lot_no,
                depo_id=kab_depo_id,
                miktar=giris_miktar
            )
            
            if not giris_sonuc.basarili:
                raise Exception(f"KAB-01'e giriş başarısız: {giris_sonuc.mesaj}")
            
            # ✅ Hareket kayıtlarını manuel ekle (motor eklemiyor gibi)
            cursor.execute("""
                INSERT INTO stok.stok_hareket (
                    urun_id, lot_no, hareket_tipi, depo_id, miktar,
                    kaynak, kaynak_id, aciklama, hareket_tarihi
                ) VALUES (?, ?, 'CIKIS', ?, ?, 'SOKUM_GIRIS', ?, ?, GETDATE())
            """, (
                urun_id, eski_lot_no, sokum_depo_id, giris_miktar,
                ie_id, f"Söküm girişi - İE: {is_emri_no}"
            ))
            
            cursor.execute("""
                INSERT INTO stok.stok_hareket (
                    urun_id, lot_no, hareket_tipi, depo_id, miktar,
                    kaynak, kaynak_id, aciklama, hareket_tarihi
                ) VALUES (?, ?, 'GIRIS', ?, ?, 'SOKUM_GIRIS', ?, ?, GETDATE())
            """, (
                urun_id, yeni_lot_no, kab_depo_id, giris_miktar,
                ie_id, f"Söküm tamamlandı - İE: {is_emri_no}"
            ))
            
            # ✅ 3. Hedef depoda durum_kodu güncelle
            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET durum_kodu = 'KABUL'
                WHERE lot_no = ? AND depo_id = ?
            """, (yeni_lot_no, kab_depo_id))
            
            # ✅ 4. Söküm girişi kaydet
            kalan_miktar = toplam_miktar - giris_miktar
            
            cursor.execute("""
                INSERT INTO uretim.sokum_giris (
                    sokum_is_emri_id, lot_no, giris_miktar, kalan_miktar,
                    kalite_durumu, sokum_suresi, hedef_depo_id,
                    durum_kodu, notlar, giris_yapan_id, giris_tarihi
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                ie_id,
                yeni_lot_no,  # ✅ Yeni lot numarası kaydedildi
                giris_miktar,
                kalan_miktar,
                self.giris_kalite_combo.currentText() or None,
                self.giris_sure_spin.value() or None,
                kab_depo_id,
                "KABUL",
                self.giris_not_edit.toPlainText().strip() or None,
                ModernLoginDialog.current_user_id or 1
            ))
            
            # ✅ 5. İş emri durumu güncelle
            if kalan_miktar > 0:
                # Kısmi giriş
                cursor.execute("""
                    UPDATE uretim.sokum_is_emirleri
                    SET miktar = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (kalan_miktar, ie_id))
                
                mesaj = f"""✓ Kısmi giriş yapıldı!

Giriş: {giris_miktar} adet
Kalan: {kalan_miktar} adet

Eski Lot: {eski_lot_no}
Yeni Lot: {yeni_lot_no}
Hedef: KAB-01 (Kabul Alanı)"""
            else:
                # Tam giriş
                cursor.execute("""
                    UPDATE uretim.sokum_is_emirleri
                    SET durum = 'TAMAMLANDI', 
                        bitis_tarihi = GETDATE(),
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (ie_id,))
                
                mesaj = f"""✓ İş emri tamamlandı!

Giriş: {giris_miktar} adet

Eski Lot: {eski_lot_no}
Yeni Lot: {yeni_lot_no}
Hedef: KAB-01 (Kabul Alanı)"""
            
            conn.commit()
            LogManager.log_update('uretim', 'uretim.rework_is_emirleri', ie_id,
                                  f'Rework giris yapildi: {giris_miktar} adet, Eski Lot: {eski_lot_no}, Yeni Lot: {yeni_lot_no}')
            conn.close()

            QMessageBox.information(self, "✓ Başarılı", mesaj)
            
            # Formu temizle
            self._clear_giris_form()
            
            # Verileri yenile
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Giriş yapılamadı: {e}")
            import traceback
            traceback.print_exc()
    
    def _clear_giris_form(self):
        """Giriş formunu temizle"""
        self.giris_ie_edit.clear()
        self.giris_lot_edit.clear()
        self.giris_toplam_edit.clear()
        self.giris_miktar_spin.setValue(0)
        self.giris_kalite_combo.setCurrentIndex(0)
        self.giris_sure_spin.setValue(0)
        self.giris_not_edit.clear()
        self.giris_btn.setEnabled(False)
    
    # ========================================================
    # HELPER METHODS - STİL (kalite_final.py ile aynı)
    # ========================================================
    
    def _create_table(self, headers):
        """Tablo oluştur"""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setStyleSheet(self._table_style())
        table.verticalHeader().setVisible(False)
        
        return table
    
    def _button_style(self):
        """Buton stili - kalite_final.py ile aynı"""
        return f"QPushButton {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 16px; }}"
    
    def _input_style(self):
        """Input stili - kalite_final.py ile aynı"""
        return f"""
            background: {self.theme.get('bg_input', '#2d3548')};
            border: 1px solid {self.theme.get('border', '#3d4454')};
            border-radius: 6px;
            padding: 8px 12px;
            color: {self.theme.get('text', '#fff')};
        """
    
    def _table_style(self):
        """Tablo stili - kalite_final.py ile aynı"""
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
            QTableWidget::item:selected {{
                background: {self.theme.get('primary', '#6366f1')};
                color: white;
            }}
        """
    
    def _get_tab_style(self):
        """Tab widget stili"""
        return f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar::tab {{
                background: {self.theme.get('bg_card', '#242938')};
                color: {self.theme.get('text', '#fff')};
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {self.theme.get('primary', '#6366f1')};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background: {self.theme.get('bg_hover', '#2d3548')};
            }}
        """
