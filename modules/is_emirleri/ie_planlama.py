# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Üretim Planlama Modülü
[MODERNIZED UI - v3.0]
"""
import os
import sys
from datetime import datetime, date, timedelta
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QTableWidget, QTableWidgetItem, QSplitter,
    QHeaderView, QAbstractItemView, QCheckBox, QMessageBox,
    QWidget, QDateEdit, QDialog, QGridLayout, QGroupBox,
    QSpinBox, QScrollArea, QTreeWidget, QTreeWidgetItem,
    QSizePolicy, QStyle, QLineEdit, QInputDialog
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QFont, QBrush

from components.base_page import BasePage
from core.database import get_db_connection

TURKCE_GUNLER_KISA = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
PLC_SIFRE = "2010"


def get_modern_style(theme: dict) -> dict:
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


class IsEmriPlanlamaPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.selected_lots = []
        self.planned_lots = []
        self.hatlar = []
        self.vardiyalar = []
        self.stok_data = {}
        self.toplam_bekleyen_miktar = 0
        self.toplam_bekleyen_bara = 0
        
        # Eski değişken isimleri için uyumluluk
        self.bg_card = self.s['card_bg']
        self.bg_input = self.s['input_bg']
        self.text = self.s['text']
        self.text_muted = self.s['text_muted']
        self.border = self.s['border']
        self.primary = self.s['primary']
        self.success = self.s['success']
        self.warning = self.s['warning']
        self.danger = self.s['error']
        
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        header = QFrame()
        header.setStyleSheet(f"QFrame {{ background: {self.bg_card}; border-radius: 8px; padding: 12px; }}")
        header_layout = QHBoxLayout(header)
        title = QLabel("📅 Üretim Planlama")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.text};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(f"QPushButton {{ background: {self.bg_input}; color: {self.text}; border: 1px solid {self.border}; border-radius: 6px; padding: 8px 16px; }} QPushButton:hover {{ background: {self.border}; }}")
        refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(refresh_btn)
        layout.addWidget(header)
        
        # Ana Splitter - SOL BÜYÜK, SAĞ KÜÇÜK
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setStyleSheet(f"QSplitter::handle {{ background: {self.border}; width: 3px; }}")
        
        # SOL PANEL - Stok Havuzu
        main_splitter.addWidget(self._create_stok_panel())
        
        # SAĞ PANEL
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.addWidget(self._create_planlanan_panel())
        right_layout.addWidget(self._create_takvim_panel(), 1)
        main_splitter.addWidget(right_widget)
        
        # Sol %65, Sağ %35
        main_splitter.setSizes([750, 450])
        layout.addWidget(main_splitter, 1)
    
    def _create_stok_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.bg_card}; border-radius: 8px; }}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Başlık
        header = QLabel("📦 Stok Havuzu - Bekleyen Ürünler")
        header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.text};")
        layout.addWidget(header)
        
        # Filtreler
        filter_layout = QHBoxLayout()
        input_style = f"background: {self.bg_input}; color: {self.text}; border: 1px solid {self.border}; border-radius: 4px; padding: 6px 10px;"
        
        self.musteri_filter = QComboBox()
        self.musteri_filter.setStyleSheet(f"QComboBox {{ {input_style} min-width: 150px; }}")
        self.musteri_filter.addItem("Tüm Müşteriler", "")
        self.musteri_filter.currentIndexChanged.connect(self._filter_stoklar)
        filter_layout.addWidget(self.musteri_filter)
        
        self.kaplama_filter = QComboBox()
        self.kaplama_filter.setStyleSheet(f"QComboBox {{ {input_style} min-width: 130px; }}")
        self.kaplama_filter.addItem("Tüm Kaplamalar", "")
        self.kaplama_filter.currentIndexChanged.connect(self._filter_stoklar)
        filter_layout.addWidget(self.kaplama_filter)
        
        self.hat_filter = QComboBox()
        self.hat_filter.setStyleSheet(f"QComboBox {{ {input_style} min-width: 130px; }}")
        self.hat_filter.addItem("Tüm Hatlar", "")
        self.hat_filter.currentIndexChanged.connect(self._filter_stoklar)
        filter_layout.addWidget(self.hat_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Tree Widget
        self.stok_tree = QTreeWidget()
        self.stok_tree.setColumnCount(7)
        self.stok_tree.setHeaderLabels(["Ürün / Lot", "Stok Adı", "Müşteri", "Miktar", "Bara", "Kaplama", "Geliş Tarihi", "Seç"])
        self.stok_tree.setStyleSheet(f"""
            QTreeWidget {{ background: {self.bg_input}; color: {self.text}; border: 1px solid {self.border}; border-radius: 4px; }}
            QTreeWidget::item {{ padding: 6px 4px; border-bottom: 1px solid {self.border}; }}
            QTreeWidget::item:selected {{ background: {self.primary}; }}
            QTreeWidget::item:hover {{ background: {self.bg_card}; }}
            QHeaderView::section {{ background: {self.bg_card}; color: {self.text}; padding: 8px 4px; border: none; font-weight: bold; }}
        """)
        
        h = self.stok_tree.header()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, 7):
            h.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(7, QHeaderView.Fixed)
        self.stok_tree.setColumnWidth(7, 60)
        self.stok_tree.itemExpanded.connect(self._on_item_expanded)
        self.stok_tree.itemCollapsed.connect(self._on_item_collapsed)
        layout.addWidget(self.stok_tree, 1)
        
        # ALT KISIM - TOPLAM BEKLEYEN + SEÇİM
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet(f"QFrame {{ background: {self.bg_input}; border: 2px solid {self.warning}; border-radius: 8px; }}")
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(16, 12, 16, 12)
        
        # TOPLAM BEKLEYEN
        self.toplam_bekleyen_label = QLabel("📊 Toplam Bekleyen: 0 adet, 0 bara")
        self.toplam_bekleyen_label.setStyleSheet(f"color: {self.warning}; font-size: 14px; font-weight: bold;")
        bottom_layout.addWidget(self.toplam_bekleyen_label)
        
        bottom_layout.addStretch()
        
        # Seçili
        self.secim_label = QLabel("Seçili: 0 lot, 0 bara")
        self.secim_label.setStyleSheet(f"color: {self.text_muted}; font-size: 13px;")
        bottom_layout.addWidget(self.secim_label)
        
        # Ekle butonu
        self.planla_btn = QPushButton("➕ Seçilenleri Ekle")
        self.planla_btn.setStyleSheet(f"QPushButton {{ background: {self.primary}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold; }} QPushButton:hover {{ background: #5558e3; }} QPushButton:disabled {{ background: {self.border}; }}")
        self.planla_btn.clicked.connect(self._add_to_planned)
        self.planla_btn.setEnabled(False)
        bottom_layout.addWidget(self.planla_btn)
        
        layout.addWidget(bottom_frame)
        return frame
    
    def _create_planlanan_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.bg_card}; border-radius: 8px; border: 2px solid {self.success}; }}")
        frame.setMaximumHeight(320)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Başlık
        header_layout = QHBoxLayout()
        header = QLabel("🎯 Planlanan Ürünler")
        header.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {self.success};")
        header_layout.addWidget(header)
        header_layout.addStretch()
        self.planlanan_ozet_label = QLabel("0 ürün, 0 bara")
        self.planlanan_ozet_label.setStyleSheet(f"color: {self.text}; font-weight: bold;")
        header_layout.addWidget(self.planlanan_ozet_label)
        temizle_btn = QPushButton("🗑️")
        temizle_btn.setStyleSheet(f"QPushButton {{ background: {self.danger}; color: white; border: none; border-radius: 4px; padding: 4px 8px; }} QPushButton:hover {{ background: #dc2626; }}")
        temizle_btn.clicked.connect(self._clear_planned)
        header_layout.addWidget(temizle_btn)
        layout.addLayout(header_layout)

        # Tablo
        self.planlanan_table = QTableWidget()
        self.planlanan_table.setColumnCount(6)
        self.planlanan_table.setHorizontalHeaderLabels(["Stok Kodu", "Stok Adı", "Lot", "Miktar", "Bara", "X"])
        self.planlanan_table.setStyleSheet(f"QTableWidget {{ background: {self.bg_input}; color: {self.text}; border: 1px solid {self.border}; font-size: 11px; }} QHeaderView::section {{ background: {self.bg_card}; color: {self.text}; padding: 4px; border: none; font-size: 10px; }}")
        h = self.planlanan_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.Fixed)
        self.planlanan_table.setColumnWidth(5, 120)
        self.planlanan_table.verticalHeader().setVisible(False)
        layout.addWidget(self.planlanan_table, 1)

        # Inline planlama ayarları
        input_style = f"background: {self.bg_input}; color: {self.text}; border: 1px solid {self.border}; border-radius: 4px; padding: 5px 8px;"

        plan_row = QHBoxLayout()
        plan_row.setSpacing(8)

        plan_row.addWidget(QLabel("Hat:"))
        self.plan_hat_combo = QComboBox()
        self.plan_hat_combo.setStyleSheet(f"QComboBox {{ {input_style} min-width: 110px; }}")
        self.plan_hat_combo.currentIndexChanged.connect(self._update_inline_kapasite)
        plan_row.addWidget(self.plan_hat_combo)

        plan_row.addWidget(QLabel("Vardiya:"))
        self.plan_vardiya_combo = QComboBox()
        self.plan_vardiya_combo.setStyleSheet(f"QComboBox {{ {input_style} min-width: 90px; }}")
        self.plan_vardiya_combo.currentIndexChanged.connect(self._update_inline_kapasite)
        plan_row.addWidget(self.plan_vardiya_combo)

        plan_row.addWidget(QLabel("Tarih:"))
        self.plan_tarih_combo = QComboBox()
        self.plan_tarih_combo.setStyleSheet(f"QComboBox {{ {input_style} min-width: 100px; }}")
        bugun = date.today()
        yarin = bugun + timedelta(days=1)
        self.plan_tarih_combo.addItem(f"BUGÜN ({bugun.strftime('%d.%m')})", bugun)
        self.plan_tarih_combo.addItem(f"YARIN ({yarin.strftime('%d.%m')})", yarin)
        self.plan_tarih_combo.currentIndexChanged.connect(self._update_inline_kapasite)
        plan_row.addWidget(self.plan_tarih_combo)

        layout.addLayout(plan_row)

        # Kapasite bilgi + kaydet butonu
        bottom_row = QHBoxLayout()
        self.inline_kapasite_label = QLabel("")
        self.inline_kapasite_label.setStyleSheet(f"color: {self.text_muted}; font-size: 11px;")
        bottom_row.addWidget(self.inline_kapasite_label, 1)

        self.planla_kaydet_btn = QPushButton("📅 Planla")
        self.planla_kaydet_btn.setStyleSheet(f"QPushButton {{ background: {self.success}; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: bold; font-size: 13px; }} QPushButton:hover {{ background: #1da34d; }} QPushButton:disabled {{ background: {self.border}; }}")
        self.planla_kaydet_btn.clicked.connect(self._inline_planla)
        self.planla_kaydet_btn.setEnabled(False)
        bottom_row.addWidget(self.planla_kaydet_btn)
        layout.addLayout(bottom_row)

        return frame
    
    def _create_takvim_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.bg_card}; border-radius: 8px; }}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Başlık ve hat seçimi
        header_layout = QHBoxLayout()
        header = QLabel("📊 Kapasite (Bugün + Yarın)")
        header.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {self.text};")
        header_layout.addWidget(header)
        header_layout.addStretch()
        self.takvim_hat_combo = QComboBox()
        self.takvim_hat_combo.setStyleSheet(f"QComboBox {{ background: {self.bg_input}; color: {self.text}; border: 1px solid {self.border}; border-radius: 4px; padding: 4px 8px; min-width: 100px; }}")
        self.takvim_hat_combo.currentIndexChanged.connect(self._load_takvim)
        self.takvim_hat_combo.currentIndexChanged.connect(self._load_planlanmis_isler)
        header_layout.addWidget(self.takvim_hat_combo)
        layout.addLayout(header_layout)
        
        self.kapasite_label = QLabel("Kapasite: -")
        self.kapasite_label.setStyleSheet(f"color: {self.text_muted}; font-size: 11px;")
        layout.addWidget(self.kapasite_label)
        
        # Takvim container
        self.takvim_container = QVBoxLayout()
        self.takvim_container.setSpacing(6)
        layout.addLayout(self.takvim_container)
        
        # Planlanmış işler
        plan_header = QHBoxLayout()
        plan_label = QLabel("📋 Planlanmış İşler")
        plan_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {self.text};")
        plan_header.addWidget(plan_label)
        plan_header.addStretch()
        self.plc_gonder_btn = QPushButton("🔐 PLC Gönder")
        self.plc_gonder_btn.setStyleSheet(f"QPushButton {{ background: {self.primary}; color: white; border: none; border-radius: 4px; padding: 5px 12px; font-size: 11px; }} QPushButton:hover {{ background: #5558e3; }}")
        self.plc_gonder_btn.clicked.connect(self._plc_gonder_sifreli)
        plan_header.addWidget(self.plc_gonder_btn)
        layout.addLayout(plan_header)
        
        self.plan_table = QTableWidget()
        self.plan_table.setColumnCount(7)
        self.plan_table.setHorizontalHeaderLabels(["✓", "İş Emri", "Stok Kodu", "Bara", "Vardiya", "Durum", "PLC"])
        self.plan_table.setStyleSheet(f"QTableWidget {{ background: {self.bg_input}; color: {self.text}; border: 1px solid {self.border}; font-size: 10px; }} QHeaderView::section {{ background: {self.bg_card}; color: {self.text}; padding: 4px; border: none; font-size: 9px; }}")
        h = self.plan_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Fixed)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.Fixed)
        self.plan_table.setColumnWidth(0, 30)
        self.plan_table.setColumnWidth(3, 45)
        self.plan_table.setColumnWidth(6, 35)
        self.plan_table.verticalHeader().setVisible(False)
        layout.addWidget(self.plan_table, 1)
        
        self.plan_ozet_label = QLabel("0 iş, 0 bara")
        self.plan_ozet_label.setStyleSheet(f"color: {self.text_muted}; font-size: 10px;")
        layout.addWidget(self.plan_ozet_label)
        
        return frame

    def _load_data(self):
        try:
            conn = get_db_connection()
            if not conn:
                return
            cursor = conn.cursor()
            self._load_hatlar(cursor)
            self._load_vardiyalar(cursor)
            self._load_filters(cursor)
            self._load_stoklar_grouped(cursor)
            self._load_takvim()
            self._load_planlanmis_isler()
            conn.close()
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")

    def _load_hatlar(self, cursor):
        try:
            cursor.execute("""
                SELECT h.id, h.kod, h.ad, COALESCE(p.vardiya_kapasite_bara, h.vardiya_kapasite_bara, 350)
                FROM tanim.uretim_hatlari h
                LEFT JOIN tanim.prosesler p ON p.hat_id = h.id AND p.aktif_mi = 1 AND p.silindi_mi = 0
                WHERE h.aktif_mi = 1 ORDER BY h.kod
            """)
            self.hatlar = []
            self.takvim_hat_combo.blockSignals(True)
            self.takvim_hat_combo.clear()
            self.plan_hat_combo.blockSignals(True)
            self.plan_hat_combo.clear()
            self.hat_filter.blockSignals(True)
            self.hat_filter.clear()
            self.hat_filter.addItem("Tüm Hatlar", "")
            for row in cursor.fetchall():
                self.hatlar.append({'id': row[0], 'kod': row[1], 'ad': row[2], 'kapasite': row[3] or 350})
                self.takvim_hat_combo.addItem(f"{row[1]}", row[0])
                self.plan_hat_combo.addItem(f"{row[1]} - {row[2]}", row[0])
                self.hat_filter.addItem(f"{row[1]} - {row[2]}", row[0])
            self.takvim_hat_combo.blockSignals(False)
            self.plan_hat_combo.blockSignals(False)
            self.hat_filter.blockSignals(False)
        except Exception as e:
            print(f"Hat yükleme hatası: {e}")

    def _load_vardiyalar(self, cursor):
        try:
            cursor.execute("SELECT id, kod, ad, baslangic_saati, bitis_saati FROM tanim.vardiyalar WHERE aktif_mi = 1 ORDER BY id")
            self.vardiyalar = []
            self.plan_vardiya_combo.blockSignals(True)
            self.plan_vardiya_combo.clear()
            for row in cursor.fetchall():
                v = {'id': row[0], 'kod': row[1], 'ad': row[2], 'baslangic': str(row[3])[:5] if row[3] else '', 'bitis': str(row[4])[:5] if row[4] else ''}
                self.vardiyalar.append(v)
                self.plan_vardiya_combo.addItem(f"{v['kod']} ({v['baslangic']}-{v['bitis']})", v['id'])
            self.plan_vardiya_combo.blockSignals(False)
        except Exception as e:
            print(f"Vardiya yükleme hatası: {e}")

    def _load_filters(self, cursor):
        try:
            self.musteri_filter.blockSignals(True)
            self.musteri_filter.clear()
            self.musteri_filter.addItem("Tüm Müşteriler", "")
            cursor.execute("""
                SELECT DISTINCT c.unvan 
                FROM stok.stok_bakiye sb
                INNER JOIN stok.urunler u ON sb.urun_id = u.id
                INNER JOIN musteri.cariler c ON u.cari_id = c.id
                WHERE sb.miktar - ISNULL(sb.rezerve_miktar, 0) > 0 
                  AND sb.durum_kodu = 'GIRIS_ONAY'
                  AND c.unvan IS NOT NULL 
                ORDER BY c.unvan
            """)
            for row in cursor.fetchall():
                if row[0]:
                    self.musteri_filter.addItem(row[0], row[0])
            self.musteri_filter.blockSignals(False)
            
            self.kaplama_filter.blockSignals(True)
            self.kaplama_filter.clear()
            self.kaplama_filter.addItem("Tüm Kaplamalar", "")
            cursor.execute("""
                SELECT DISTINCT kt.ad 
                FROM stok.stok_bakiye sb
                INNER JOIN stok.urunler u ON sb.urun_id = u.id
                INNER JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                WHERE sb.miktar - ISNULL(sb.rezerve_miktar, 0) > 0 
                  AND sb.durum_kodu = 'GIRIS_ONAY'
                  AND kt.ad IS NOT NULL 
                ORDER BY kt.ad
            """)
            for row in cursor.fetchall():
                if row[0]:
                    self.kaplama_filter.addItem(row[0], row[0])
            self.kaplama_filter.blockSignals(False)
        except Exception as e:
            print(f"Filtre yükleme hatası: {e}")

    def _load_stoklar_grouped(self, cursor=None):
        close_conn = False
        try:
            if cursor is None:
                conn = get_db_connection()
                if not conn:
                    return
                cursor = conn.cursor()
                close_conn = True
            
            musteri = self.musteri_filter.currentData() or ""
            kaplama = self.kaplama_filter.currentData() or ""
            
            query = """
                SELECT sb.id, sb.lot_no, u.urun_kodu, u.urun_adi,
                       sb.miktar - ISNULL(sb.rezerve_miktar, 0), u.bara_adedi,
                       kt.ad as kaplama_tip_adi, c.unvan as cari_unvani,
                       sb.urun_id, sb.giris_tarihi, sb.miktar,
                       u.varsayilan_hat_id
                FROM stok.stok_bakiye sb
                INNER JOIN stok.urunler u ON sb.urun_id = u.id
                LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                WHERE sb.miktar - ISNULL(sb.rezerve_miktar, 0) > 0 
                  AND sb.durum_kodu = 'GIRIS_ONAY'
            """
            params = []
            if musteri:
                query += " AND c.unvan = ?"
                params.append(musteri)
            if kaplama:
                query += " AND kt.ad = ?"
                params.append(kaplama)
            query += " ORDER BY 3, sb.giris_tarihi"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            self.stok_data = {}
            self.toplam_bekleyen_miktar = 0
            self.toplam_bekleyen_bara = 0
            
            for row in rows:
                stok_kodu = row[2] or "BİLİNMİYOR"
                miktar = float(row[4]) if row[4] else 0
                bara_miktar = int(row[5]) if row[5] and row[5] > 0 else 1
                bara_adet = round(miktar / bara_miktar, 2)  # Küsuratlı bara
                
                self.toplam_bekleyen_miktar += miktar
                self.toplam_bekleyen_bara += bara_adet
                
                giris_tarihi = row[9]
                giris_str = giris_tarihi.strftime("%d.%m.%Y") if giris_tarihi and hasattr(giris_tarihi, 'strftime') else "-"
                
                lot_data = {
                    'id': row[0], 'lot_no': row[1] or "-", 'stok_kodu': stok_kodu, 'stok_adi': row[3] or "-",
                    'miktar': miktar, 'bara': bara_adet, 'bara_miktar': bara_miktar,
                    'kaplama': row[6], 'musteri': row[7], 'urun_id': row[8], 'giris_tarihi': giris_str,
                    'varsayilan_hat_id': row[11]
                }
                
                if stok_kodu not in self.stok_data:
                    self.stok_data[stok_kodu] = {'stok_kodu': stok_kodu, 'stok_adi': row[3] or "-", 'musteri': row[7], 'kaplama': row[6], 'lots': []}
                self.stok_data[stok_kodu]['lots'].append(lot_data)
            
            self.toplam_bekleyen_label.setText(f"📊 Toplam Bekleyen: {self.toplam_bekleyen_miktar:,.0f} adet, {self.toplam_bekleyen_bara:,.2f} bara")
            self._populate_tree()
            
            if close_conn:
                conn.close()
        except Exception as e:
            print(f"Stok yükleme hatası: {e}")

    def _populate_tree(self):
        self.stok_tree.clear()
        for stok_kodu, data in self.stok_data.items():
            lots = data['lots']
            toplam_miktar = sum(l['miktar'] for l in lots)
            toplam_bara = sum(l['bara'] for l in lots)
            lot_sayisi = len(lots)
            
            parent = QTreeWidgetItem()
            parent.setText(0, f"📦 {stok_kodu}" + (f" ({lot_sayisi} lot)" if lot_sayisi > 1 else ""))
            parent.setText(1, data['stok_adi'] or "-")
            parent.setToolTip(1, data['stok_adi'] or "")
            parent.setText(2, (data['musteri'] or "-")[:20])
            parent.setText(3, f"{toplam_miktar:,.0f}")
            parent.setTextAlignment(3, Qt.AlignRight | Qt.AlignVCenter)
            parent.setText(4, f"{toplam_bara:,.2f}")
            parent.setTextAlignment(4, Qt.AlignRight | Qt.AlignVCenter)
            parent.setForeground(4, QBrush(QColor(self.primary)))
            parent.setText(5, data['kaplama'] or "-")
            parent.setText(6, lots[0]['giris_tarihi'] if lots else "-")
            parent.setData(0, Qt.UserRole, {'type': 'parent', 'stok_kodu': stok_kodu})
            
            font = QFont()
            font.setBold(True)
            parent.setFont(0, font)
            parent.setFont(4, font)
            
            for lot in lots:
                child = QTreeWidgetItem(parent)
                child.setText(0, f"   └ {lot['lot_no']}")
                child.setForeground(0, QBrush(QColor(self.text_muted)))
                child.setText(3, f"{lot['miktar']:,.0f}")
                child.setTextAlignment(3, Qt.AlignRight | Qt.AlignVCenter)
                child.setText(4, f"{lot['bara']:,.2f}")
                child.setTextAlignment(4, Qt.AlignRight | Qt.AlignVCenter)
                child.setForeground(4, QBrush(QColor(self.primary)))
                child.setText(6, lot['giris_tarihi'])
                child.setData(0, Qt.UserRole, {'type': 'lot', 'lot_data': lot})

                cb = QCheckBox()
                cb.setProperty("lot_data", lot)
                cb.stateChanged.connect(self._update_secim)
                cb_widget = QWidget()
                cb_layout = QHBoxLayout(cb_widget)
                cb_layout.addWidget(cb)
                cb_layout.setAlignment(Qt.AlignCenter)
                cb_layout.setContentsMargins(0, 0, 0, 0)
                self.stok_tree.setItemWidget(child, 7, cb_widget)

            if lot_sayisi == 1:
                cb = QCheckBox()
                cb.setProperty("lot_data", lots[0])
                cb.stateChanged.connect(self._update_secim)
                cb_widget = QWidget()
                cb_layout = QHBoxLayout(cb_widget)
                cb_layout.addWidget(cb)
                cb_layout.setAlignment(Qt.AlignCenter)
                cb_layout.setContentsMargins(0, 0, 0, 0)
                self.stok_tree.setItemWidget(parent, 7, cb_widget)
                parent.setData(0, Qt.UserRole, {'type': 'single', 'lot_data': lots[0]})
            
            self.stok_tree.addTopLevelItem(parent)
        self.stok_tree.collapseAll()

    def _on_item_expanded(self, item):
        data = item.data(0, Qt.UserRole)
        if data and data.get('type') == 'parent':
            item.setText(0, item.text(0).replace("📦", "📂"))

    def _on_item_collapsed(self, item):
        data = item.data(0, Qt.UserRole)
        if data and data.get('type') == 'parent':
            item.setText(0, item.text(0).replace("📂", "📦"))

    def _filter_stoklar(self):
        self._load_stoklar_grouped()

    def _update_secim(self):
        self.selected_lots = []
        toplam_miktar = 0
        toplam_bara = 0
        
        def check_items(item):
            nonlocal toplam_miktar, toplam_bara
            cb_widget = self.stok_tree.itemWidget(item, 7)
            if cb_widget:
                cb = cb_widget.findChild(QCheckBox)
                if cb and cb.isChecked():
                    lot_data = cb.property("lot_data")
                    if lot_data:
                        self.selected_lots.append(lot_data)
                        toplam_miktar += lot_data.get('miktar', 0)
                        toplam_bara += lot_data.get('bara', 0)
            for i in range(item.childCount()):
                check_items(item.child(i))
        
        for i in range(self.stok_tree.topLevelItemCount()):
            check_items(self.stok_tree.topLevelItem(i))
        
        self.secim_label.setText(f"Seçili: {len(self.selected_lots)} lot, {toplam_bara:,.2f} bara")
        self.planla_btn.setEnabled(len(self.selected_lots) > 0)

    def _add_to_planned(self):
        if not self.selected_lots:
            return
        existing_ids = {lot['id'] for lot in self.planned_lots}
        added = 0
        for lot in self.selected_lots:
            if lot['id'] not in existing_ids:
                self.planned_lots.append(lot.copy())
                added += 1
        if added > 0:
            self._update_planlanan_table()
            self._clear_selections()
            self._auto_select_inline_hat()
            QMessageBox.information(self, "✓", f"{added} lot eklendi.")

    def _auto_select_inline_hat(self):
        """Planlanan lotların varsayılan hat bilgisine göre hat combo'yu otomatik seç"""
        hat_ids = [l.get('varsayilan_hat_id') for l in self.planned_lots if l.get('varsayilan_hat_id')]
        if hat_ids:
            from collections import Counter
            en_cok = Counter(hat_ids).most_common(1)[0][0]
            for i in range(self.plan_hat_combo.count()):
                if self.plan_hat_combo.itemData(i) == en_cok:
                    self.plan_hat_combo.setCurrentIndex(i)
                    break

    def _clear_selections(self):
        def uncheck(item):
            cb_widget = self.stok_tree.itemWidget(item, 7)
            if cb_widget:
                cb = cb_widget.findChild(QCheckBox)
                if cb:
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
            for i in range(item.childCount()):
                uncheck(item.child(i))
        for i in range(self.stok_tree.topLevelItemCount()):
            uncheck(self.stok_tree.topLevelItem(i))
        self.selected_lots = []
        self._update_secim()

    def _update_planlanan_table(self):
        self.planlanan_table.setRowCount(len(self.planned_lots))
        toplam_bara = 0
        for i, lot in enumerate(self.planned_lots):
            self.planlanan_table.setItem(i, 0, QTableWidgetItem(lot.get('stok_kodu', '-')[:20]))
            self.planlanan_table.setItem(i, 1, QTableWidgetItem(lot.get('stok_adi', '-')))
            self.planlanan_table.setItem(i, 2, QTableWidgetItem(lot.get('lot_no', '-')))
            self.planlanan_table.setItem(i, 3, QTableWidgetItem(f"{lot.get('miktar', 0):,.0f}"))
            bara = lot.get('bara', 0)
            toplam_bara += bara
            bara_item = QTableWidgetItem(f"{bara}")
            bara_item.setForeground(QColor(self.primary))
            self.planlanan_table.setItem(i, 4, bara_item)

            widget = self.create_action_buttons([
                ("🗑️", "Kaldir", lambda c, lid=lot['id']: self._remove_from_planned(lid), "delete"),
            ])
            self.planlanan_table.setCellWidget(i, 5, widget)
            self.planlanan_table.setRowHeight(i, 42)
        
        self.planlanan_ozet_label.setText(f"{len(self.planned_lots)} ürün, {toplam_bara:,.2f} bara")
        self.planla_kaydet_btn.setEnabled(len(self.planned_lots) > 0)
        self._update_inline_kapasite()

    def _remove_from_planned(self, lot_id):
        self.planned_lots = [l for l in self.planned_lots if l['id'] != lot_id]
        self._update_planlanan_table()

    def _clear_planned(self):
        if self.planned_lots:
            self.planned_lots = []
            self._update_planlanan_table()

    def _update_inline_kapasite(self):
        """Inline kapasite bilgisini güncelle"""
        hat_id = self.plan_hat_combo.currentData()
        vardiya_id = self.plan_vardiya_combo.currentData()
        tarih = self.plan_tarih_combo.currentData()
        if not all([hat_id, vardiya_id, tarih]):
            self.inline_kapasite_label.setText("")
            return

        hat = next((h for h in self.hatlar if h['id'] == hat_id), None)
        kapasite = hat['kapasite'] if hat else 350

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(SUM(planlanan_bara), 0) FROM uretim.planlama WHERE hat_id = ? AND tarih = ? AND vardiya_id = ?", (hat_id, tarih, vardiya_id))
            mevcut = int(cursor.fetchone()[0] or 0)
            conn.close()

            toplam_bara = sum(l.get('bara', 0) for l in self.planned_lots)
            yeni = mevcut + toplam_bara
            kalan = kapasite - mevcut

            if toplam_bara > 0 and yeni > kapasite:
                self.inline_kapasite_label.setText(f"⚠️ Kapasite aşılacak! {mevcut}/{kapasite} + {toplam_bara:.1f}")
                self.inline_kapasite_label.setStyleSheet(f"color: #ef4444; font-size: 11px; font-weight: bold;")
            elif toplam_bara > 0:
                self.inline_kapasite_label.setText(f"✓ {mevcut}/{kapasite} bara dolu, +{toplam_bara:.1f} eklenecek")
                self.inline_kapasite_label.setStyleSheet(f"color: {self.success}; font-size: 11px;")
            else:
                self.inline_kapasite_label.setText(f"{mevcut}/{kapasite} bara dolu")
                self.inline_kapasite_label.setStyleSheet(f"color: {self.text_muted}; font-size: 11px;")
        except Exception as e:
            print(f"Inline kapasite hatası: {e}")

    def _inline_planla(self):
        """Inline planlama - dialog açmadan doğrudan planla"""
        if not self.planned_lots:
            return

        hat_id = self.plan_hat_combo.currentData()
        vardiya_id = self.plan_vardiya_combo.currentData()
        tarih = self.plan_tarih_combo.currentData()

        if not hat_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen hat seçin!")
            return
        if not vardiya_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen vardiya seçin!")
            return

        hat_kod = self.plan_hat_combo.currentText()
        toplam_bara = sum(l.get('bara', 0) for l in self.planned_lots)

        cevap = QMessageBox.question(
            self, "Planlama Onayı",
            f"{len(self.planned_lots)} lot planlanacak:\n\n"
            f"Hat: {hat_kod}\n"
            f"Vardiya: {self.plan_vardiya_combo.currentText()}\n"
            f"Tarih: {self.plan_tarih_combo.currentText()}\n"
            f"Toplam: {toplam_bara:,.2f} bara\n\n"
            f"Onaylıyor musunuz?",
            QMessageBox.Yes | QMessageBox.No
        )
        if cevap != QMessageBox.Yes:
            return

        # PlanlamaDialog._save() ile aynı kayıt işlemini yap
        dialog = PlanlamaDialog(self, self.planned_lots, self.hatlar, self.vardiyalar, self.theme)
        # Dialog'u göstermeden combo'ları ayarla
        for i in range(dialog.hat_combo.count()):
            if dialog.hat_combo.itemData(i) == hat_id:
                dialog.hat_combo.setCurrentIndex(i)
                break
        for i in range(dialog.vardiya_combo.count()):
            if dialog.vardiya_combo.itemData(i) == vardiya_id:
                dialog.vardiya_combo.setCurrentIndex(i)
                break
        for i in range(dialog.tarih_combo.count()):
            if dialog.tarih_combo.itemData(i) == tarih:
                dialog.tarih_combo.setCurrentIndex(i)
                break

        dialog._save()
        if dialog.result() == QDialog.Accepted:
            self.planned_lots = []
            self._update_planlanan_table()
            self._load_data()

    def _show_planlama_dialog(self):
        if not self.planned_lots:
            return
        dialog = PlanlamaDialog(self, self.planned_lots, self.hatlar, self.vardiyalar, self.theme)
        if dialog.exec() == QDialog.Accepted:
            self.planned_lots = []
            self._update_planlanan_table()
            self._load_data()

    def _load_takvim(self):
        # Temizle
        while self.takvim_container.count():
            child = self.takvim_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        hat_id = self.takvim_hat_combo.currentData()
        if not hat_id:
            return
        
        hat = next((h for h in self.hatlar if h['id'] == hat_id), None)
        kapasite = hat['kapasite'] if hat else 350
        self.kapasite_label.setText(f"Kapasite: {kapasite} bara/vardiya")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Sadece BUGÜN ve YARIN
            for day_offset in range(2):
                current_date = date.today() + timedelta(days=day_offset)
                gun_adi = "BUGÜN" if day_offset == 0 else "YARIN"
                
                cursor.execute("""
                    SELECT v.kod, ISNULL(SUM(p.planlanan_bara), 0)
                    FROM tanim.vardiyalar v
                    LEFT JOIN uretim.planlama p ON p.vardiya_id = v.id AND p.hat_id = ? AND p.tarih = ? AND p.durum IN ('PLANLANDI', 'URETIMDE')
                    WHERE v.aktif_mi = 1 GROUP BY v.id, v.kod ORDER BY v.id
                """, (hat_id, current_date))
                vardiya_data = cursor.fetchall()
                
                day_frame = QFrame()
                border_color = self.primary if day_offset == 0 else self.success
                day_frame.setStyleSheet(f"QFrame {{ background: {self.bg_input}; border: 2px solid {border_color}; border-radius: 6px; padding: 4px; }}")
                day_layout = QHBoxLayout(day_frame)
                day_layout.setContentsMargins(8, 4, 8, 4)
                day_layout.setSpacing(8)
                
                date_label = QLabel(f"{gun_adi}\n{current_date.strftime('%d.%m')}")
                date_label.setStyleSheet(f"color: {border_color}; font-weight: bold; font-size: 10px;")
                day_layout.addWidget(date_label)
                
                for vdata in vardiya_data:
                    v_kod, v_bara = vdata[0], int(vdata[1] or 0)
                    doluluk = (v_bara / kapasite * 100) if kapasite > 0 else 0
                    bar_color = self.danger if doluluk >= 100 else self.warning if doluluk >= 80 else self.success if doluluk > 0 else self.border
                    
                    v_label = QLabel(f"{v_kod}\n{v_bara}/{kapasite}")
                    v_label.setStyleSheet(f"color: {bar_color}; font-size: 9px; font-weight: bold;")
                    day_layout.addWidget(v_label)
                
                day_layout.addStretch()
                self.takvim_container.addWidget(day_frame)
            
            conn.close()
        except Exception as e:
            print(f"Takvim hatası: {e}")

    def _load_planlanmis_isler(self):
        hat_id = self.takvim_hat_combo.currentData()
        if not hat_id:
            return
        
        bugun = date.today()
        yarin = bugun + timedelta(days=1)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, ie.is_emri_no, ie.stok_kodu, p.planlanan_bara, v.kod, p.durum,
                       CASE WHEN EXISTS (SELECT 1 FROM entegrasyon.plc_uretim_plani plc WHERE plc.planlama_id = p.id) THEN 1 ELSE 0 END,
                       p.tarih, ie.id
                FROM uretim.planlama p
                JOIN siparis.is_emirleri ie ON p.is_emri_id = ie.id
                LEFT JOIN tanim.vardiyalar v ON p.vardiya_id = v.id
                WHERE p.hat_id = ? AND p.tarih BETWEEN ? AND ? AND p.durum IN ('PLANLANDI', 'URETIMDE')
                ORDER BY p.tarih, p.sira_no
            """, (hat_id, bugun, yarin))
            rows = cursor.fetchall()
            conn.close()
            
            self.plan_table.setRowCount(len(rows))
            toplam_bara = 0
            
            for i, row in enumerate(rows):
                cb = QCheckBox()
                cb.setProperty("plan_data", {'planlama_id': row[0], 'is_emri_id': row[8], 'is_emri_no': row[1], 'stok_kodu': row[2], 'planlanan_bara': row[3], 'tarih': row[7], 'plc_gonderildi': row[6]})
                if row[6]:
                    cb.setEnabled(False)
                cb_widget = QWidget()
                cb_layout = QHBoxLayout(cb_widget)
                cb_layout.addWidget(cb)
                cb_layout.setAlignment(Qt.AlignCenter)
                cb_layout.setContentsMargins(0, 0, 0, 0)
                self.plan_table.setCellWidget(i, 0, cb_widget)
                self.plan_table.setRowHeight(i, 42)
                
                self.plan_table.setItem(i, 1, QTableWidgetItem(str(row[1] or "")[-8:]))
                self.plan_table.setItem(i, 2, QTableWidgetItem(str(row[2] or "")[:15]))
                bara = int(row[3] or 0)
                toplam_bara += bara
                bara_item = QTableWidgetItem(str(bara))
                bara_item.setForeground(QColor(self.primary))
                self.plan_table.setItem(i, 3, bara_item)
                self.plan_table.setItem(i, 4, QTableWidgetItem(str(row[4] or "")))
                durum_item = QTableWidgetItem(str(row[5] or "")[:8])
                durum_item.setForeground(QColor(self.success if row[5] == 'URETIMDE' else self.warning))
                self.plan_table.setItem(i, 5, durum_item)
                plc_item = QTableWidgetItem("✓" if row[6] else "")
                plc_item.setForeground(QColor(self.success))
                self.plan_table.setItem(i, 6, plc_item)
            
            self.plan_ozet_label.setText(f"{len(rows)} iş, {toplam_bara:,.2f} bara")
        except Exception as e:
            print(f"Planlanmış işler hatası: {e}")

    def _plc_gonder_sifreli(self):
        selected = []
        for i in range(self.plan_table.rowCount()):
            w = self.plan_table.cellWidget(i, 0)
            if w:
                cb = w.findChild(QCheckBox)
                if cb and cb.isChecked():
                    data = cb.property("plan_data")
                    if data and not data.get('plc_gonderildi'):
                        selected.append(data)
        
        if not selected:
            QMessageBox.warning(self, "Uyarı", "PLC'ye gönderilecek plan seçilmedi!")
            return
        
        # ŞİFRE SOR
        sifre, ok = QInputDialog.getText(self, "🔐 PLC Şifresi", "Şifreyi girin:", QLineEdit.Password)
        if not ok:
            return
        if sifre != PLC_SIFRE:
            QMessageBox.critical(self, "❌ Hata", "Şifre yanlış!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            for plan in selected:
                cursor.execute("""
                    INSERT INTO entegrasyon.plc_uretim_plani (planlama_id, is_emri_id, is_emri_no, stok_kodu, planlanan_bara, tarih, durum, gonderim_tarihi)
                    VALUES (?, ?, ?, ?, ?, ?, 'BEKLIYOR', GETDATE())
                """, (plan['planlama_id'], plan['is_emri_id'], plan['is_emri_no'], plan['stok_kodu'], plan['planlanan_bara'], plan['tarih']))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "✓", f"{len(selected)} iş PLC'ye gönderildi.")
            self._load_planlanmis_isler()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class PlanlamaDialog(QDialog):
    def __init__(self, parent, lots, hatlar, vardiyalar, theme):
        super().__init__(parent)
        self.lots = lots
        self.hatlar = hatlar
        self.vardiyalar = vardiyalar
        self.theme = theme
        self.setWindowTitle("📅 Planlama")
        self.setMinimumSize(450, 350)
        self.setModal(True)
        self._setup_ui()
        self._auto_select_hat()
        self._update_kapasite()

    def _auto_select_hat(self):
        """Lotların varsayılan hat bilgisine göre hat combo'yu otomatik seç"""
        hat_ids = [l.get('varsayilan_hat_id') for l in self.lots if l.get('varsayilan_hat_id')]
        if hat_ids:
            from collections import Counter
            en_cok = Counter(hat_ids).most_common(1)[0][0]
            for i in range(self.hat_combo.count()):
                if self.hat_combo.itemData(i) == en_cok:
                    self.hat_combo.setCurrentIndex(i)
                    break

    def _setup_ui(self):
        bg = self.theme.get('bg_card', '#242938')
        inp = self.theme.get('bg_input', '#1e2330')
        txt = self.theme.get('text', '#ffffff')
        brd = self.theme.get('border', '#3d4454')
        suc = self.theme.get('success', '#22c55e')
        pri = self.theme.get('primary', '#6366f1')
        
        self.setStyleSheet(f"QDialog {{ background: {bg}; }} QLabel {{ color: {txt}; }} QComboBox {{ background: {inp}; color: {txt}; border: 1px solid {brd}; border-radius: 4px; padding: 8px; }}")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        toplam_bara = sum(l.get('bara', 0) for l in self.lots)
        ozet = QLabel(f"📦 {len(self.lots)} lot, {toplam_bara:,.2f} bara")
        ozet.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {pri};")
        layout.addWidget(ozet)
        
        form = QGridLayout()
        form.setSpacing(12)
        
        form.addWidget(QLabel("Hat:"), 0, 0)
        self.hat_combo = QComboBox()
        for h in self.hatlar:
            self.hat_combo.addItem(f"{h['kod']} - {h['ad']}", h['id'])
        self.hat_combo.currentIndexChanged.connect(self._update_kapasite)
        form.addWidget(self.hat_combo, 0, 1)
        
        form.addWidget(QLabel("Vardiya:"), 1, 0)
        self.vardiya_combo = QComboBox()
        for v in self.vardiyalar:
            self.vardiya_combo.addItem(f"{v['kod']} ({v['baslangic']}-{v['bitis']})", v['id'])
        self.vardiya_combo.currentIndexChanged.connect(self._update_kapasite)
        form.addWidget(self.vardiya_combo, 1, 1)
        
        form.addWidget(QLabel("Tarih:"), 2, 0)
        self.tarih_combo = QComboBox()
        bugun = date.today()
        yarin = bugun + timedelta(days=1)
        self.tarih_combo.addItem(f"BUGÜN - {bugun.strftime('%d.%m.%Y')}", bugun)
        self.tarih_combo.addItem(f"YARIN - {yarin.strftime('%d.%m.%Y')}", yarin)
        self.tarih_combo.currentIndexChanged.connect(self._update_kapasite)
        form.addWidget(self.tarih_combo, 2, 1)
        
        layout.addLayout(form)
        
        self.kapasite_label = QLabel("")
        layout.addWidget(self.kapasite_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        iptal = QPushButton("İptal")
        iptal.setStyleSheet(f"QPushButton {{ background: {brd}; color: {txt}; border: none; border-radius: 6px; padding: 10px 20px; }}")
        iptal.clicked.connect(self.reject)
        btn_layout.addWidget(iptal)
        kaydet = QPushButton("✓ Planla")
        kaydet.setStyleSheet(f"QPushButton {{ background: {suc}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold; }}")
        kaydet.clicked.connect(self._save)
        btn_layout.addWidget(kaydet)
        layout.addLayout(btn_layout)

    def _update_kapasite(self):
        hat_id = self.hat_combo.currentData()
        vardiya_id = self.vardiya_combo.currentData()
        tarih = self.tarih_combo.currentData()
        if not all([hat_id, vardiya_id, tarih]):
            return
        
        hat = next((h for h in self.hatlar if h['id'] == hat_id), None)
        kapasite = hat['kapasite'] if hat else 350
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(SUM(planlanan_bara), 0) FROM uretim.planlama WHERE hat_id = ? AND tarih = ? AND vardiya_id = ?", (hat_id, tarih, vardiya_id))
            mevcut = int(cursor.fetchone()[0] or 0)
            conn.close()
            
            toplam_bara = sum(l.get('bara', 0) for l in self.lots)
            yeni = mevcut + toplam_bara
            kalan = kapasite - mevcut
            
            if yeni > kapasite:
                self.kapasite_label.setText(f"⚠️ Kapasite aşılacak! {mevcut}/{kapasite} + {toplam_bara} = {yeni}")
                self.kapasite_label.setStyleSheet("color: #ef4444; font-weight: bold;")
            else:
                self.kapasite_label.setText(f"✓ Mevcut: {mevcut}/{kapasite}, Eklenecek: {toplam_bara}, Kalan: {kalan - toplam_bara}")
                self.kapasite_label.setStyleSheet(f"color: {self.theme.get('success', '#22c55e')}; font-weight: bold;")
        except Exception as e:
            print(f"Kapasite hatası: {e}")


    def _save(self):
        """Planlama kaydet - Rezervasyon + Depo Çıkış Emri (Transfer YAPILMAZ!)"""
        hat_id = self.hat_combo.currentData()
        vardiya_id = self.vardiya_combo.currentData()
        tarih = self.tarih_combo.currentData()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # ===== HAREKET MOTORU BAŞLAT =====
            from core.hareket_motoru import HareketMotoru
            motor = HareketMotoru(conn)
            
            # Hat başı deposunu bul (çıkış emri için hedef depo)
            hat_basi_depo_id = motor.get_hat_basi_deposu(hat_id)
            if not hat_basi_depo_id:
                hat_basi_depo_id = motor.get_depo_by_tip('HAT_BASI')
                print(f"Hat başı deposu bulunamadı, varsayılan kullanılıyor: {hat_basi_depo_id}")
            
            print(f"DEBUG: Hat ID: {hat_id}, Hat Başı Depo ID: {hat_basi_depo_id}")
            
            # Mevcut sıra numarası
            cursor.execute("""
                SELECT ISNULL(MAX(sira_no), 0) + 1 
                FROM uretim.planlama 
                WHERE hat_id = ? AND tarih = ? AND vardiya_id = ?
            """, (hat_id, tarih, vardiya_id))
            sira_no = cursor.fetchone()[0]
            
            # Bugünkü iş emri sayısı
            cursor.execute("""
                SELECT COUNT(*) FROM siparis.is_emirleri 
                WHERE CAST(olusturma_tarihi AS DATE) = CAST(GETDATE() AS DATE)
            """)
            is_emri_count = cursor.fetchone()[0]
            
            # Depo çıkış emri numarası için sayaç
            cursor.execute("""
                SELECT ISNULL(MAX(CAST(SUBSTRING(emir_no, 4, 10) AS INT)), 0)
                FROM stok.depo_cikis_emirleri
                WHERE emir_no LIKE 'DC-%'
            """)
            dc_count = cursor.fetchone()[0] or 0
            
            basarili_lotlar = []
            
            for lot in self.lots:
                is_emri_count += 1
                dc_count += 1
                is_emri_no = f"IE-{datetime.now().strftime('%Y%m%d')}-{is_emri_count:04d}"
                emir_no = f"DC-{dc_count:06d}"
                
                # ===== SADECE ADET BAZLI - Bara bilgi amaçlı =====
                planlanan_miktar = lot.get('miktar', 0)  # DİREKT ADET!
                planlanan_bara = lot.get('bara', 0)      # Sadece bilgi/gösterim
                lot_no = lot.get('lot_no', '')
                
                # 1. İş emri oluştur
                cursor.execute("""
                    INSERT INTO siparis.is_emirleri 
                    (uuid, is_emri_no, tarih, cari_unvani, stok_kodu, stok_adi, kaplama_tipi, 
                     toplam_miktar, birim, toplam_bara, hat_id, termin_tarihi, durum, 
                     olusturma_tarihi, guncelleme_tarihi, silindi_mi, urun_id, planlanan_miktar, lot_no)
                    OUTPUT INSERTED.id 
                    VALUES (NEWID(), ?, GETDATE(), ?, ?, ?, ?, ?, 'ADET', ?, ?, ?, 'PLANLANDI', 
                            GETDATE(), GETDATE(), 0, ?, ?, ?)
                """, (is_emri_no, lot.get('musteri', ''), lot.get('stok_kodu', ''), 
                      lot.get('stok_adi', ''), lot.get('kaplama', ''), planlanan_miktar, 
                      planlanan_bara, hat_id, tarih, lot.get('urun_id'), planlanan_miktar, lot_no))
                is_emri_id = cursor.fetchone()[0]
                
                # 2. Planlama kaydı
                cursor.execute("""
                    INSERT INTO uretim.planlama 
                    (uuid, tarih, hat_id, vardiya_id, is_emri_id, sira_no, planlanan_bara, 
                     stok_bakiye_id, durum, olusturma_tarihi) 
                    VALUES (NEWID(), ?, ?, ?, ?, ?, ?, ?, 'PLANLANDI', GETDATE())
                """, (tarih, hat_id, vardiya_id, is_emri_id, sira_no, planlanan_bara, lot.get('id')))
                
                # 3. LOT DURUM GÜNCELLEME - GIRIS_ONAY → PLANLANDI
                if lot_no:
                    cursor.execute("""
                        UPDATE stok.stok_bakiye 
                        SET durum_kodu = 'PLANLANDI',
                            son_hareket_tarihi = GETDATE()
                        WHERE lot_no = ?
                    """, (lot_no,))
                    print(f"✓ LOT durumu güncellendi: {lot_no} → PLANLANDI")
                
                # ===== REZERVASYON YAP - ADET BAZLI =====
                if lot_no:
                    rezerve_sonuc = motor.rezerve_et(
                        lot_no=lot_no,
                        miktar=planlanan_miktar,  # ADET!
                        is_emri_id=is_emri_id
                    )
                    
                    if rezerve_sonuc.basarili:
                        print(f"✓ Rezervasyon başarılı: {lot_no}, {planlanan_miktar} ADET (Bara: {planlanan_bara})")
                    else:
                        print(f"⚠️ Rezervasyon başarısız - {lot_no}: {rezerve_sonuc.mesaj}")
                
                # ===== DEPO ÇIKIŞ EMRİ OLUŞTUR - ADET BAZLI =====
                if lot_no and hat_basi_depo_id:
                    # Kaynak depo (mal kabul) ID'sini bul
                    kaynak_depo_id = motor.get_depo_by_tip('KABUL')
                    if not kaynak_depo_id:
                        cursor.execute("SELECT TOP 1 id FROM tanim.depolar WHERE kod LIKE 'KAB%' AND aktif_mi = 1")
                        row = cursor.fetchone()
                        kaynak_depo_id = row[0] if row else 7  # Varsayılan KAB-01
                    
                    # Tablo yapısına uygun INSERT - ADET BAZLI
                    cursor.execute("""
                        INSERT INTO stok.depo_cikis_emirleri
                        (emir_no, lot_no, stok_kodu, stok_adi, kaynak_depo_id, hedef_depo_id,
                         talep_miktar, durum, is_emri_id)
                        OUTPUT INSERTED.id
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'BEKLIYOR', ?)
                    """, (emir_no, lot_no, lot.get('stok_kodu', ''), lot.get('stok_adi', ''),
                          kaynak_depo_id, hat_basi_depo_id, planlanan_miktar, is_emri_id))
                    dce_row = cursor.fetchone()
                    dce_id = dce_row[0] if dce_row else None
                    print(f"✓ Depo çıkış emri: {emir_no} → {lot_no}, {planlanan_miktar} ADET")
                else:
                    dce_id = None

                basarili_lotlar.append({
                    'is_emri_no': is_emri_no,
                    'emir_no': emir_no,
                    'lot_no': lot_no,
                    'stok_kodu': lot.get('stok_kodu', ''),
                    'miktar': planlanan_miktar,
                    'bara': planlanan_bara,
                    'dce_id': dce_id
                })
                
                sira_no += 1
            
            conn.commit()
            conn.close()

            # Bildirim: Yeni iş emirleri planlandı
            try:
                from core.bildirim_tetikleyici import BildirimTetikleyici
                for lot in basarili_lotlar[:5]:  # İlk 5 IE için bildirim
                    BildirimTetikleyici.is_emri_olusturuldu(
                        ie_id=lot.get('is_emri_id', 0),
                        ie_no=lot.get('is_emri_no', ''),
                        musteri_adi=lot.get('musteri', ''),
                    )
            except Exception as bt_err:
                print(f"Bildirim hatasi: {bt_err}")

            # Özet mesaj - ADET göster, bara bilgi olarak
            toplam_adet = sum(l['miktar'] for l in basarili_lotlar)
            ozet = "\n".join([f"  • {l['is_emri_no']}: {l['stok_kodu']} - {l['miktar']:,.0f} adet" 
                             for l in basarili_lotlar[:5]])
            if len(basarili_lotlar) > 5:
                ozet += f"\n  ... ve {len(basarili_lotlar) - 5} adet daha"
            
            QMessageBox.information(self, "✓ Planlama Tamamlandı",
                f"{len(self.lots)} lot planlandı.\n"
                f"Toplam: {toplam_adet:,.0f} ADET\n\n"
                f"İş Emirleri:\n{ozet}\n\n"
                f"📦 Stoklar REZERVE edildi (KAB-01'de bekliyor)\n"
                f"📋 Depo çıkış emirleri oluşturuldu\n\n"
                f"⚠️ Transfer için 'Depo Çıkış' ekranını kullanın!")

            # Depo çıkış emirlerini yazdır
            dce_ids = [l['dce_id'] for l in basarili_lotlar if l.get('dce_id')]
            if dce_ids:
                cevap = QMessageBox.question(self, "🖨️ Yazdır",
                    f"{len(dce_ids)} adet depo çıkış emri oluşturuldu.\nPDF olarak yazdırmak ister misiniz?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if cevap == QMessageBox.Yes:
                    try:
                        from utils.depo_cikis_pdf import depo_cikis_pdf_olustur
                        for dce_id in dce_ids:
                            depo_cikis_pdf_olustur(dce_id)
                    except Exception as pe:
                        QMessageBox.warning(self, "⚠️ PDF Hatası", f"PDF oluşturulamadı:\n{pe}")

            self.accept()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Planlama hatası:\n{str(e)}")
