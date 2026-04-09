# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Yeni Sevkiyat Sayfası
Barkod okutarak sevkiyat oluşturma
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QGridLayout,
    QSplitter, QWidget, QTextEdit, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager

# Sevke hazır durumlar
SEVK_HAZIR_DURUMLAR = ('KONTROL_EDILDI', 'ONAYLANDI', 'SEVKE_HAZIR')


class SevkYeniPage(BasePage):
    """Yeni Sevkiyat Sayfası - Barkod Okutma"""
    
    # Sevkiyat tamamlandığında sinyal
    sevkiyat_tamamlandi = Signal(int)  # sevkiyat_id
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.okutulan_paketler = []  # Okutulan lot listesi
        self.sevkiyat_id = None
        self._hazir_data = []
        self._setup_ui()
        self._load_arac_bilgileri()
        QTimer.singleShot(200, self._load_hazir_urunler)

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
        
        title = QLabel("🚚 Yeni Sevkiyat")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text', '#fff')};")
        header.addWidget(title)
        
        header.addStretch()
        
        self.saat_label = QLabel()
        self.saat_label.setStyleSheet(f"color: {self.theme.get('text_muted', '#8a94a6')}; font-size: 18px; font-weight: bold;")
        header.addWidget(self.saat_label)
        
        # Temizle butonu
        temizle_btn = QPushButton("🗑️ Temizle")
        temizle_btn.setStyleSheet(self._button_style())
        temizle_btn.clicked.connect(self._temizle)
        header.addWidget(temizle_btn)
        
        layout.addLayout(header)
        
        # Splitter - Sol: Barkod & Araç, Sağ: Okutulan paketler
        splitter = QSplitter(Qt.Horizontal)
        
        # SOL PANEL
        sol_widget = QWidget()
        sol_layout = QVBoxLayout(sol_widget)
        sol_layout.setContentsMargins(0, 0, 0, 0)
        sol_layout.setSpacing(12)
        
        # Barkod okutma alanı
        barkod_frame = QFrame()
        barkod_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card', '#242938')};
                border: 2px solid {self.theme.get('primary', '#6366f1')};
                border-radius: 12px;
            }}
        """)
        barkod_layout = QVBoxLayout(barkod_frame)
        barkod_layout.setContentsMargins(16, 16, 16, 16)
        barkod_layout.setSpacing(12)
        
        barkod_title = QLabel("📷 BARKOD OKUT")
        barkod_title.setStyleSheet(f"color: {self.theme.get('primary', '#6366f1')}; font-weight: bold; font-size: 16px;")
        barkod_layout.addWidget(barkod_title)
        
        self.barkod_input = QLineEdit()
        self.barkod_input.setPlaceholderText("Lot barkodunu okutun veya girin...")
        self.barkod_input.setStyleSheet(f"""
            QLineEdit {{
                background: {self.theme.get('bg_main', '#1a1f2e')};
                border: 2px solid {self.theme.get('border', '#3d4454')};
                border-radius: 8px;
                padding: 16px;
                font-size: 18px;
                color: {self.theme.get('text', '#fff')};
            }}
            QLineEdit:focus {{
                border-color: {self.theme.get('primary', '#6366f1')};
            }}
        """)
        self.barkod_input.returnPressed.connect(self._barkod_okut)
        barkod_layout.addWidget(self.barkod_input)
        
        # Son okutulan bilgisi
        self.son_okutma_label = QLabel("Son okutma: -")
        self.son_okutma_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px;")
        barkod_layout.addWidget(self.son_okutma_label)
        
        sol_layout.addWidget(barkod_frame)
        
        # Araç bilgileri
        arac_frame = QFrame()
        arac_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card', '#242938')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 12px;
            }}
        """)
        arac_layout = QVBoxLayout(arac_frame)
        arac_layout.setContentsMargins(16, 16, 16, 16)
        arac_layout.setSpacing(12)
        
        arac_title = QLabel("🚛 ARAÇ BİLGİLERİ")
        arac_title.setStyleSheet(f"color: {self.theme.get('text', '#fff')}; font-weight: bold; font-size: 14px;")
        arac_layout.addWidget(arac_title)
        
        arac_grid = QGridLayout()
        arac_grid.setSpacing(8)
        
        # Taşıyıcı firma
        arac_grid.addWidget(QLabel("Taşıyıcı:"), 0, 0)
        self.tasiyici_input = QComboBox()
        self.tasiyici_input.setEditable(True)
        self.tasiyici_input.setStyleSheet(self._input_style())
        arac_grid.addWidget(self.tasiyici_input, 0, 1)
        
        # Plaka (tanımlardan)
        arac_grid.addWidget(QLabel("Plaka:"), 1, 0)
        self.plaka_input = QComboBox()
        self.plaka_input.setEditable(True)
        self.plaka_input.setStyleSheet(self._input_style())
        self.plaka_input.setPlaceholderText("Plaka seçin veya yazın")
        arac_grid.addWidget(self.plaka_input, 1, 1)

        # Şoför (tanımlardan)
        arac_grid.addWidget(QLabel("Şoför:"), 2, 0)
        self.sofor_input = QComboBox()
        self.sofor_input.setEditable(True)
        self.sofor_input.setStyleSheet(self._input_style())
        self.sofor_input.setPlaceholderText("Şoför seçin veya yazın")
        arac_grid.addWidget(self.sofor_input, 2, 1)
        
        arac_layout.addLayout(arac_grid)
        
        # Not
        not_label = QLabel("Not:")
        not_label.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        arac_layout.addWidget(not_label)
        
        self.not_input = QTextEdit()
        self.not_input.setMaximumHeight(80)
        self.not_input.setPlaceholderText("Sevkiyat notu...")
        self.not_input.setStyleSheet(self._input_style())
        arac_layout.addWidget(self.not_input)
        
        sol_layout.addWidget(arac_frame)

        # Sevke Hazır Ürünler Listesi
        hazir_frame = QFrame()
        hazir_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card', '#242938')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 12px;
            }}
        """)
        hazir_layout = QVBoxLayout(hazir_frame)
        hazir_layout.setContentsMargins(12, 12, 12, 12)
        hazir_layout.setSpacing(8)

        hazir_header = QHBoxLayout()
        hazir_title = QLabel("SEVKE HAZIR ÜRÜNLER")
        hazir_title.setStyleSheet(f"color: {self.theme.get('success', '#22c55e')}; font-weight: bold; font-size: 13px;")
        hazir_header.addWidget(hazir_title)
        hazir_header.addStretch()

        self.hazir_count_label = QLabel("0 lot")
        self.hazir_count_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 11px;")
        hazir_header.addWidget(self.hazir_count_label)

        hazir_yenile_btn = QPushButton("Yenile")
        hazir_yenile_btn.setFixedHeight(26)
        hazir_yenile_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input', '#2d3548')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background: {self.theme.get('bg_hover', '#3d4454')}; }}
        """)
        hazir_yenile_btn.clicked.connect(self._load_hazir_urunler)
        hazir_header.addWidget(hazir_yenile_btn)
        hazir_layout.addLayout(hazir_header)

        # Arama
        self.hazir_search = QLineEdit()
        self.hazir_search.setPlaceholderText("Filtrele... (lot, müşteri, ürün)")
        self.hazir_search.setFixedHeight(28)
        self.hazir_search.setStyleSheet(f"""
            QLineEdit {{
                background: {self.theme.get('bg_input', '#2d3548')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 4px;
                padding: 4px 8px;
                color: {self.theme.get('text', '#fff')};
                font-size: 11px;
            }}
        """)
        self.hazir_search.textChanged.connect(self._filter_hazir_urunler)
        hazir_layout.addWidget(self.hazir_search)

        # Tablo
        self.hazir_table = QTableWidget()
        self.hazir_table.setColumnCount(6)
        self.hazir_table.setHorizontalHeaderLabels(["", "Lot No", "Müşteri", "Ürün", "Miktar", "Gün"])
        self.hazir_table.setColumnWidth(0, 30)   # Checkbox
        self.hazir_table.setColumnWidth(1, 120)
        self.hazir_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.hazir_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.hazir_table.setColumnWidth(4, 70)
        self.hazir_table.setColumnWidth(5, 40)
        self.hazir_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.hazir_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.hazir_table.verticalHeader().setVisible(False)
        self.hazir_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.theme.get('bg_main', '#1a1f2e')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 4px;
                gridline-color: {self.theme.get('border', '#3d4454')};
                color: {self.theme.get('text', '#fff')};
                font-size: 11px;
            }}
            QTableWidget::item {{ padding: 3px; }}
            QTableWidget::item:selected {{ background-color: {self.theme.get('primary', '#6366f1')}; }}
            QHeaderView::section {{
                background-color: {self.theme.get('bg_input', '#2d3548')};
                color: {self.theme.get('text', '#fff')};
                padding: 4px;
                border: none;
                border-bottom: 1px solid {self.theme.get('border', '#3d4454')};
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        hazir_layout.addWidget(self.hazir_table, 1)

        # Ekle butonu
        ekle_btn = QPushButton("Secilenleri Ekle")
        ekle_btn.setCursor(Qt.PointingHandCursor)
        ekle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {self.theme.get('success_hover', '#16a34a')}; }}
        """)
        ekle_btn.clicked.connect(self._hazir_secilenleri_ekle)
        hazir_layout.addWidget(ekle_btn)

        sol_layout.addWidget(hazir_frame, 1)

        splitter.addWidget(sol_widget)
        
        # SAĞ PANEL - Okutulan paketler
        sag_widget = QWidget()
        sag_layout = QVBoxLayout(sag_widget)
        sag_layout.setContentsMargins(0, 0, 0, 0)
        
        # Başlık ve özet
        sag_header = QHBoxLayout()
        sag_title = QLabel("📋 OKUTULAN PAKETLER")
        sag_title.setStyleSheet(f"color: {self.theme.get('success', '#22c55e')}; font-weight: bold; font-size: 14px;")
        sag_header.addWidget(sag_title)
        
        sag_header.addStretch()
        
        self.ozet_label = QLabel("0 paket, 0 adet")
        self.ozet_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-weight: bold;")
        sag_header.addWidget(self.ozet_label)
        
        sag_layout.addLayout(sag_header)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Sıra", "Lot No", "Müşteri", "Stok Kodu", "Stok Adı", "Miktar", "Saat", "Sil"
        ])
        
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 70)
        self.table.setColumnWidth(7, 120)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(self._table_style())
        self.table.verticalHeader().setVisible(False)
        
        sag_layout.addWidget(self.table, 1)
        
        # Müşteri bazlı özet
        musteri_frame = QFrame()
        musteri_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px; padding: 8px;")
        musteri_layout = QVBoxLayout(musteri_frame)
        musteri_layout.setContentsMargins(12, 8, 12, 8)
        
        musteri_title = QLabel("👥 MÜŞTERİ BAZLI ÖZET")
        musteri_title.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-weight: bold;")
        musteri_layout.addWidget(musteri_title)
        
        self.musteri_ozet_label = QLabel("-")
        self.musteri_ozet_label.setStyleSheet(f"color: {self.theme.get('text')}; font-size: 12px;")
        self.musteri_ozet_label.setWordWrap(True)
        musteri_layout.addWidget(self.musteri_ozet_label)
        
        sag_layout.addWidget(musteri_frame)
        
        splitter.addWidget(sag_widget)
        splitter.setSizes([350, 550])
        
        layout.addWidget(splitter, 1)
        
        # Alt butonlar
        footer = QHBoxLayout()
        footer.addStretch()
        
        # İptal
        iptal_btn = QPushButton("❌ İptal")
        iptal_btn.setStyleSheet(self._button_style())
        iptal_btn.clicked.connect(self._temizle)
        footer.addWidget(iptal_btn)
        
        # Sevkiyat Oluştur
        self.sevk_btn = QPushButton("✅ Sevkiyat Oluştur")
        self.sevk_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {self.theme.get('success_hover', '#16a34a')};
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover', '#3d4454')};
                color: {self.theme.get('text_muted')};
            }}
        """)
        self.sevk_btn.clicked.connect(self._sevkiyat_olustur)
        self.sevk_btn.setEnabled(False)
        footer.addWidget(self.sevk_btn)
        
        layout.addLayout(footer)
        
        # Barkod inputa fokus
        def _safe_focus():
            try:
                self.barkod_input.setFocus()
            except RuntimeError:
                pass
        QTimer.singleShot(100, _safe_focus)
    
    def _button_style(self):
        return f"""
            QPushButton {{
                background: {self.theme.get('bg_input', '#2d3548')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background: {self.theme.get('bg_hover', '#3d4454')};
            }}
        """
    
    def _input_style(self):
        return f"""
            QLineEdit, QComboBox, QTextEdit {{
                background: {self.theme.get('bg_input', '#2d3548')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 8px 12px;
                color: {self.theme.get('text', '#fff')};
            }}
        """
    
    def _table_style(self):
        return f"""
            QTableWidget {{
                background-color: {self.theme.get('bg_card', '#242938')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border', '#3d4454')};
                color: {self.theme.get('text', '#ffffff')};
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {self.theme.get('border', '#3d4454')};
            }}
            QTableWidget::item:selected {{
                background-color: {self.theme.get('primary', '#6366f1')};
            }}
            QHeaderView::section {{
                background-color: {self.theme.get('bg_input', '#2d3548')};
                color: {self.theme.get('text', '#ffffff')};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {self.theme.get('success', '#22c55e')};
                font-weight: bold;
            }}
        """
    
    def _update_time(self):
        now = datetime.now()
        self.saat_label.setText(now.strftime("%H:%M:%S"))
    
    def _load_arac_bilgileri(self):
        """Taşıyıcı, araç ve şoför bilgilerini tanımlardan yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Taşıyıcı firmalar (önceki irsaliyelerden)
            cursor.execute("""
                SELECT DISTINCT tasiyici_firma
                FROM siparis.cikis_irsaliyeleri
                WHERE tasiyici_firma IS NOT NULL AND tasiyici_firma != ''
                ORDER BY tasiyici_firma
            """)
            self.tasiyici_input.clear()
            self.tasiyici_input.addItem("")
            for row in cursor.fetchall():
                self.tasiyici_input.addItem(row[0])

            # Araçlar (lojistik.araclar tanımından)
            self.plaka_input.clear()
            self.plaka_input.addItem("")
            try:
                cursor.execute("""
                    SELECT plaka, arac_tipi, marka
                    FROM lojistik.araclar
                    WHERE aktif_mi = 1
                    ORDER BY plaka
                """)
                for row in cursor.fetchall():
                    plaka = row[0]
                    detay = f"{row[1] or ''} {row[2] or ''}".strip()
                    display = f"{plaka} ({detay})" if detay else plaka
                    self.plaka_input.addItem(display, plaka)
            except Exception:
                pass  # Tablo yoksa sessizce geç

            # Şoförler (lojistik.soforler tanımından)
            self.sofor_input.clear()
            self.sofor_input.addItem("")
            try:
                cursor.execute("""
                    SELECT ad_soyad, telefon
                    FROM lojistik.soforler
                    WHERE aktif_mi = 1
                    ORDER BY ad_soyad
                """)
                for row in cursor.fetchall():
                    ad = row[0]
                    tel = row[1] or ''
                    display = f"{ad} ({tel})" if tel else ad
                    self.sofor_input.addItem(display, ad)
            except Exception:
                pass  # Tablo yoksa sessizce geç

            conn.close()
        except Exception:
            pass

    # =========================================================================
    # SEVKE HAZIR ÜRÜNLER LİSTESİ
    # =========================================================================

    def _load_hazir_urunler(self):
        """SEV deposundaki onaylı ürünleri yükle"""
        self._hazir_data = []
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    sb.id,
                    sb.lot_no,
                    COALESCE(ie.cari_unvani, 'Tanımsız') as musteri,
                    COALESCE(ie.stok_kodu, sb.stok_kodu, '') as stok_kodu,
                    COALESCE(ie.stok_adi, sb.stok_adi, '') as stok_adi,
                    sb.miktar,
                    ie.cari_id,
                    ie.id as is_emri_id,
                    DATEDIFF(day, sb.son_hareket_tarihi, GETDATE()) as gun
                FROM stok.stok_bakiye sb
                LEFT JOIN siparis.is_emirleri ie
                    ON REPLACE(REPLACE(sb.lot_no, '-SEV', ''), '-SEVK', '') = ie.lot_no
                JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE d.kod IN ('SEV-01', 'SEVK', 'SEV', 'MAMUL')
                  AND sb.kalite_durumu IN ('ONAYLANDI', 'OK', 'SEVKE_HAZIR')
                  AND sb.miktar > 0
                ORDER BY sb.son_hareket_tarihi DESC
            """)
            for row in cursor.fetchall():
                self._hazir_data.append({
                    'stok_bakiye_id': row[0],
                    'lot_no': row[1] or '',
                    'musteri': row[2] or 'Tanımsız',
                    'stok_kodu': row[3] or '',
                    'stok_adi': row[4] or '',
                    'miktar': row[5] or 0,
                    'cari_id': row[6],
                    'is_emri_id': row[7],
                    'gun': row[8] or 0,
                })
            conn.close()
        except Exception as e:
            print(f"Hazır ürünler yükleme hatası: {e}")

        self._display_hazir_urunler(self._hazir_data)

    def _display_hazir_urunler(self, data):
        """Sevke hazır ürünleri tabloda göster"""
        # Zaten okutulanları çıkar
        okutulan_lotlar = {p['lot_no'] for p in self.okutulan_paketler}

        filtered = [d for d in data if d['lot_no'] not in okutulan_lotlar]

        self.hazir_table.setRowCount(len(filtered))
        for i, d in enumerate(filtered):
            # Checkbox
            cb = QCheckBox()
            cb.setProperty('lot_data', d)
            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self.hazir_table.setCellWidget(i, 0, cb_widget)

            lot_item = QTableWidgetItem(d['lot_no'])
            lot_item.setForeground(QColor(self.theme.get('info', '#3b82f6')))
            self.hazir_table.setItem(i, 1, lot_item)

            self.hazir_table.setItem(i, 2, QTableWidgetItem(d['musteri'][:20]))

            urun = d['stok_kodu'] or d['stok_adi']
            self.hazir_table.setItem(i, 3, QTableWidgetItem(urun[:25]))

            miktar_item = QTableWidgetItem(f"{d['miktar']:,.0f}")
            miktar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.hazir_table.setItem(i, 4, miktar_item)

            gun_item = QTableWidgetItem(str(d['gun']))
            gun_item.setTextAlignment(Qt.AlignCenter)
            if d['gun'] >= 14:
                gun_item.setForeground(QColor('#ef4444'))
            elif d['gun'] >= 7:
                gun_item.setForeground(QColor('#f59e0b'))
            self.hazir_table.setItem(i, 5, gun_item)

            self.hazir_table.setRowHeight(i, 32)

        self.hazir_count_label.setText(f"{len(filtered)} lot")

    def _filter_hazir_urunler(self):
        """Sevke hazır ürünleri filtrele"""
        search = self.hazir_search.text().strip().lower()
        if not search:
            self._display_hazir_urunler(self._hazir_data if hasattr(self, '_hazir_data') else [])
            return

        filtered = []
        for d in (self._hazir_data if hasattr(self, '_hazir_data') else []):
            searchable = f"{d['lot_no']} {d['musteri']} {d['stok_kodu']} {d['stok_adi']}".lower()
            if search in searchable:
                filtered.append(d)
        self._display_hazir_urunler(filtered)

    def _hazir_secilenleri_ekle(self):
        """Seçili hazır ürünleri okutulan paketlere ekle"""
        eklenen = 0
        for i in range(self.hazir_table.rowCount()):
            cb_widget = self.hazir_table.cellWidget(i, 0)
            if not cb_widget:
                continue
            cb = cb_widget.findChild(QCheckBox)
            if not cb or not cb.isChecked():
                continue

            lot_data = cb.property('lot_data')
            if not lot_data:
                continue

            # Daha önce okutulanlar arasında var mı?
            already = any(p['lot_no'] == lot_data['lot_no'] for p in self.okutulan_paketler)
            if already:
                continue

            paket = {
                'stok_bakiye_id': lot_data['stok_bakiye_id'],
                'lot_no': lot_data['lot_no'],
                'musteri': lot_data['musteri'],
                'stok_kodu': lot_data['stok_kodu'],
                'stok_adi': lot_data['stok_adi'],
                'miktar': lot_data['miktar'],
                'cari_id': lot_data['cari_id'],
                'is_emri_id': lot_data['is_emri_id'],
                'okutma_saati': datetime.now()
            }
            self.okutulan_paketler.append(paket)
            eklenen += 1

        if eklenen > 0:
            self._refresh_table()
            # Hazır listesini güncelle (eklenenler çıkarılacak)
            self._display_hazir_urunler(self._hazir_data if hasattr(self, '_hazir_data') else [])
            self.son_okutma_label.setText(f"{eklenen} lot listeden eklendi")
            self.son_okutma_label.setStyleSheet(f"color: {self.theme.get('success')}; font-size: 12px;")
        else:
            QMessageBox.information(self, "Bilgi", "Eklenecek lot seçilmedi veya seçilenler zaten ekli.")

    def _barkod_okut(self):
        """Barkod okutulduğunda - SEV deposundaki stoktan kontrol et"""
        barkod = self.barkod_input.text().strip()
        if not barkod:
            return
        
        # Barkod = Lot No
        lot_no = barkod
        
        # Daha önce okutulmuş mu?
        for p in self.okutulan_paketler:
            if p['lot_no'] == lot_no:
                QMessageBox.warning(self, "Uyarı", f"Bu lot zaten okutulmuş!\n\nLot: {lot_no}")
                self.barkod_input.clear()
                self.barkod_input.setFocus()
                return
        
        # SEV deposundaki stoktan kontrol et
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # SEV deposundaki ONAYLANDI durumlu stokları getir
            # NOT: stok_bakiye'de cari_id yok, is_emirleri'den alınıyor
            cursor.execute("""
                SELECT 
                    sb.id,
                    sb.lot_no,
                    COALESCE(ie.cari_unvani, 'Tanımsız') as musteri,
                    COALESCE(ie.stok_kodu, sb.stok_kodu, '') as stok_kodu,
                    COALESCE(ie.stok_adi, sb.stok_adi, '') as stok_adi,
                    sb.miktar,
                    ie.cari_id,
                    ie.id as is_emri_id
                FROM stok.stok_bakiye sb
                LEFT JOIN siparis.is_emirleri ie ON REPLACE(REPLACE(sb.lot_no, '-SEV', ''), '-SEVK', '') = ie.lot_no
                JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE sb.lot_no = ?
                  AND d.kod IN ('SEV-01', 'SEVK', 'SEV', 'MAMUL')
                  AND sb.kalite_durumu IN ('ONAYLANDI', 'OK', 'SEVKE_HAZIR')
                  AND sb.miktar > 0
            """, (lot_no,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                QMessageBox.warning(
                    self, "Hata", 
                    f"Bu lot sevk deposunda bulunamadı!\n\nLot: {lot_no}\n\n"
                    "Lütfen lot numarasını kontrol edin veya\n"
                    "kalite kontrolünün tamamlandığından emin olun."
                )
                self.barkod_input.clear()
                self.barkod_input.setFocus()
                return
            
            # Paketi ekle
            paket = {
                'stok_bakiye_id': row[0],
                'lot_no': row[1],
                'musteri': row[2] or 'Tanımsız',
                'stok_kodu': row[3] or '',
                'stok_adi': row[4] or '',
                'miktar': row[5] or 0,
                'cari_id': row[6],
                'is_emri_id': row[7],
                'okutma_saati': datetime.now()
            }
            
            self.okutulan_paketler.append(paket)
            self._refresh_table()
            self._display_hazir_urunler(self._hazir_data if hasattr(self, '_hazir_data') else [])

            # Son okutma bilgisi
            self.son_okutma_label.setText(
                f"✓ {lot_no} - {paket['musteri'][:20]} - {paket['miktar']:,.0f} ad"
            )
            self.son_okutma_label.setStyleSheet(f"color: {self.theme.get('success')}; font-size: 12px;")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veritabanı hatası: {e}")
        
        self.barkod_input.clear()
        self.barkod_input.setFocus()
    
    def _refresh_table(self):
        """Tabloyu müşteriye göre gruplanmış şekilde güncelle"""
        self.table.setRowCount(0)
        
        # Müşteriye göre grupla
        musteri_gruplari = {}
        toplam_miktar = 0
        
        for paket in self.okutulan_paketler:
            musteri = paket['musteri']
            cari_id = paket.get('cari_id')
            key = (cari_id, musteri)  # cari_id + musteri ile grupla
            
            if key not in musteri_gruplari:
                musteri_gruplari[key] = {
                    'musteri': musteri,
                    'cari_id': cari_id,
                    'paketler': [],
                    'toplam_lot': 0,
                    'toplam_adet': 0
                }
            
            musteri_gruplari[key]['paketler'].append(paket)
            musteri_gruplari[key]['toplam_lot'] += 1
            musteri_gruplari[key]['toplam_adet'] += paket['miktar']
            toplam_miktar += paket['miktar']
        
        # Her müşteri grubu için satırlar ekle
        row_idx = 0
        self.musteri_row_map = {}  # Satır numarası -> cari_id eşlemesi
        
        for (cari_id, musteri), grup in musteri_gruplari.items():
            # Grup başlık satırı (müşteri adı)
            self.table.insertRow(row_idx)
            
            # Tüm hücreleri birleştir etkisi için başlık
            header_item = QTableWidgetItem(f"📦 {musteri} - {grup['toplam_lot']} lot, {grup['toplam_adet']:,.0f} adet")
            header_item.setBackground(QColor(self.theme.get('primary', '#6366f1')))
            header_item.setForeground(QColor('#ffffff'))
            font = header_item.font()
            font.setBold(True)
            header_item.setFont(font)
            self.table.setItem(row_idx, 0, header_item)
            
            # Diğer sütunları boş ama aynı renkte yap
            for col in range(1, 7):
                empty_item = QTableWidgetItem('')
                empty_item.setBackground(QColor(self.theme.get('primary', '#6366f1')))
                self.table.setItem(row_idx, col, empty_item)
            
            # İrsaliye Oluştur butonu
            widget = self.create_action_buttons([
                ("📄", "İrsaliye Oluştur", lambda checked, cid=cari_id, m=musteri: self._irsaliye_olustur(cid, m), "primary"),
            ])
            self.table.setCellWidget(row_idx, 7, widget)
            self.table.setRowHeight(row_idx, 42)
            
            self.musteri_row_map[row_idx] = cari_id
            row_idx += 1
            
            # Grup altındaki paketler
            for i, paket in enumerate(grup['paketler']):
                self.table.insertRow(row_idx)
                
                # Sıra (alt satır için boşluk + numara)
                item = QTableWidgetItem(f"  {i + 1}")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 0, item)
                
                # Lot No
                item = QTableWidgetItem(paket['lot_no'])
                item.setForeground(QColor(self.theme.get('info', '#3b82f6')))
                self.table.setItem(row_idx, 1, item)
                
                # Müşteri (boş - grup başlığında var)
                self.table.setItem(row_idx, 2, QTableWidgetItem(''))
                
                # Stok Kodu
                self.table.setItem(row_idx, 3, QTableWidgetItem(paket['stok_kodu']))
                
                # Stok Adı
                self.table.setItem(row_idx, 4, QTableWidgetItem(paket['stok_adi']))
                
                # Miktar
                item = QTableWidgetItem(f"{paket['miktar']:,.0f}")
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row_idx, 5, item)
                
                # Saat
                saat = paket['okutma_saati'].strftime('%H:%M')
                self.table.setItem(row_idx, 6, QTableWidgetItem(saat))
                
                # Sil butonu
                # Paketi bul - lot_no ile
                paket_idx = self.okutulan_paketler.index(paket)
                widget = self.create_action_buttons([
                    ("🗑️", "Sil", lambda checked, idx=paket_idx: self._paket_sil(idx), "delete"),
                ])
                self.table.setCellWidget(row_idx, 7, widget)
                self.table.setRowHeight(row_idx, 42)
                
                row_idx += 1
        
        # Özet güncelle
        self.ozet_label.setText(f"{len(self.okutulan_paketler)} paket, {toplam_miktar:,.0f} adet")
        
        # Müşteri özeti
        if musteri_gruplari:
            ozet_str = " | ".join([
                f"{g['musteri'][:15]}: {g['toplam_lot']} lot" 
                for g in musteri_gruplari.values()
            ])
            self.musteri_ozet_label.setText(ozet_str)
        else:
            self.musteri_ozet_label.setText("-")
        
        # Sevk butonu aktifliği - artık her cari için ayrı buton var
        self.sevk_btn.setEnabled(len(self.okutulan_paketler) > 0)
    
    def _irsaliye_olustur(self, cari_id, musteri_adi, otomatik=False):
        """Seçili cari için irsaliye oluştur
        
        Args:
            cari_id: Müşteri ID
            musteri_adi: Müşteri adı
            otomatik: True ise onay sorulmaz (toplu işlem için)
        """
        # Bu cariye ait paketleri bul (cari_id VE musteri eşleşmeli)
        cari_paketleri = [p for p in self.okutulan_paketler
                         if p.get('cari_id') == cari_id and p.get('musteri') == musteri_adi]
        
        if not cari_paketleri:
            raise Exception(f"Bu müşteriye ait paket bulunamadı!")
        
        toplam_adet = sum(p['miktar'] for p in cari_paketleri)
        
        # Onay al (sadece manuel işlemde)
        if not otomatik:
            reply = QMessageBox.question(
                self, "İrsaliye Onayı",
                f"İrsaliye oluşturulacak:\n\n"
                f"Müşteri: {musteri_adi}\n"
                f"Paket Sayısı: {len(cari_paketleri)}\n"
                f"Toplam Adet: {toplam_adet:,.0f}\n\n"
                f"Devam etmek istiyor musunuz?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                raise Exception("Kullanıcı iptal etti")
        
        # İrsaliye oluştur
        # Plaka: tanımdan seçildiyse data'yı al, elle yazıldıysa text'i al
        plaka = self.plaka_input.currentData() or self.plaka_input.currentText().strip()
        # Parantez içi detay varsa temizle (örn: "34 ABC 123 (Kamyon Ford)" → "34 ABC 123")
        if plaka and '(' in plaka:
            plaka = plaka.split('(')[0].strip()
        # Şoför: tanımdan seçildiyse data'yı al, elle yazıldıysa text'i al
        sofor = self.sofor_input.currentData() or self.sofor_input.currentText().strip()
        if sofor and '(' in sofor:
            sofor = sofor.split('(')[0].strip()
        tasiyici = self.tasiyici_input.currentText().strip()
        notlar = self.not_input.toPlainText().strip()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Cari ID yoksa bulmaya çalış
            if not cari_id:
                cursor.execute("""
                    SELECT TOP 1 id FROM musteri.cariler 
                    WHERE unvan LIKE ? OR kisa_ad LIKE ?
                """, (f'%{musteri_adi[:20]}%', f'%{musteri_adi[:20]}%'))
                row = cursor.fetchone()
                if row:
                    cari_id = row[0]
            
            if not cari_id:
                cursor.execute("SELECT TOP 1 id FROM musteri.cariler WHERE aktif_mi = 1")
                row = cursor.fetchone()
                if row:
                    cari_id = row[0]
                else:
                    raise Exception("Müşteri bulunamadı!")
            
            # İrsaliye numarası oluştur (tanımlardan)
            try:
                from modules.tanimlar.tanim_numara import sonraki_numara_al
                irsaliye_no = sonraki_numara_al('IRSALIYE')
            except Exception:
                # Tanım yoksa eski yöntemle devam et
                cursor.execute("""
                    SELECT MAX(CAST(SUBSTRING(irsaliye_no, 5, 10) AS INT))
                    FROM siparis.cikis_irsaliyeleri
                    WHERE irsaliye_no LIKE 'IRS-%'
                """)
                max_no = cursor.fetchone()[0] or 0
                irsaliye_no = f"IRS-{max_no + 1:06d}"
            
            # İrsaliye oluştur
            cursor.execute("""
                INSERT INTO siparis.cikis_irsaliyeleri
                (uuid, irsaliye_no, cari_id, tarih, sevk_tarihi, tasiyici_firma, arac_plaka, sofor_adi, durum, notlar, olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                OUTPUT INSERTED.id
                VALUES (NEWID(), ?, ?, GETDATE(), GETDATE(), ?, ?, ?, 'HAZIRLANDI', ?, GETDATE(), GETDATE(), 0)
            """, (irsaliye_no, cari_id, tasiyici, plaka, sofor, notlar))
            
            irsaliye_id = cursor.fetchone()[0]
            
            # Hareket motorunu başlat
            from core.hareket_motoru import HareketMotoru
            motor = HareketMotoru(conn)
            
            # İrsaliye satırları
            satir_no = 0
            for paket in cari_paketleri:
                satir_no += 1
                
                # urun_id bul
                urun_id = None
                if paket.get('stok_kodu'):
                    cursor.execute("""
                        SELECT TOP 1 id FROM stok.urunler WHERE urun_kodu = ?
                    """, (paket['stok_kodu'],))
                    row = cursor.fetchone()
                    if row:
                        urun_id = row[0]
                
                if not urun_id:
                    cursor.execute("SELECT TOP 1 id FROM stok.urunler")
                    row = cursor.fetchone()
                    if row:
                        urun_id = row[0]
                    else:
                        urun_id = 1
                
                cursor.execute("""
                    INSERT INTO siparis.cikis_irsaliye_satirlar
                    (uuid, irsaliye_id, satir_no, is_emri_id, urun_id, miktar, birim_id, lot_no)
                    VALUES (NEWID(), ?, ?, ?, ?, ?, 1, ?)
                """, (irsaliye_id, satir_no, paket.get('is_emri_id'), urun_id, paket['miktar'], paket['lot_no']))
                
                # Hareket motoru ile stok çıkışı
                lot_no = paket.get('lot_no', '')
                if lot_no:
                    cikis_sonuc = motor.stok_cikis(
                        lot_no=lot_no,
                        miktar=paket['miktar'],
                        kaynak="IRSALIYE",
                        kaynak_id=irsaliye_id,
                        aciklama=f"Sevkiyat çıkışı - {irsaliye_no}"
                    )
                    if cikis_sonuc.basarili:
                        print(f"✓ Stok çıkışı: {lot_no}, {paket['miktar']} adet")
                    else:
                        print(f"✗ Stok çıkışı hatası: {cikis_sonuc.mesaj}")
                
                # İş emri durumunu SEVK_EDILDI yap
                if paket.get('is_emri_id'):
                    cursor.execute("""
                        UPDATE siparis.is_emirleri
                        SET durum = 'SEVK_EDILDI',
                            guncelleme_tarihi = GETDATE()
                        WHERE id = ?
                    """, (paket['is_emri_id'],))
            
            conn.commit()
            LogManager.log_update('sevkiyat', 'siparis.is_emirleri', None, 'Durum guncellendi')
            conn.close()

            # Bildirim: Sevkiyat planlandı
            try:
                from core.bildirim_tetikleyici import BildirimTetikleyici
                BildirimTetikleyici.sevkiyat_planlandi(
                    sevk_id=0,
                    musteri_adi=musteri_adi,
                    sevk_tarih=datetime.now().strftime('%d.%m.%Y'),
                )
            except Exception as bt_err:
                print(f"Bildirim hatasi: {bt_err}")

            # Bu carinin paketlerini listeden çıkar (cari_id VE musteri eşleşeni çıkar)
            self.okutulan_paketler = [p for p in self.okutulan_paketler
                                       if not (p.get('cari_id') == cari_id and p.get('musteri') == musteri_adi)]
            self._refresh_table()
            
            # Başarılı mesajı (sadece manuel işlemde)
            if not otomatik:
                QMessageBox.information(
                    self, "✓ Başarılı",
                    f"İrsaliye oluşturuldu!\n\n"
                    f"İrsaliye No: {irsaliye_no}\n"
                    f"Müşteri: {musteri_adi}\n"
                    f"Paket: {len(cari_paketleri)}\n"
                    f"Toplam: {toplam_adet:,.0f} adet\n\n"
                    f"İrsaliye sayfasından yazdırabilirsiniz."
                )
                self.barkod_input.setFocus()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"İrsaliye oluşturulamadı: {e}")
        
        # Sevk butonu aktifliği
        self.sevk_btn.setEnabled(len(self.okutulan_paketler) > 0)
    
    def _paket_sil(self, idx):
        """Paketi listeden sil"""
        if 0 <= idx < len(self.okutulan_paketler):
            paket = self.okutulan_paketler.pop(idx)
            self._refresh_table()
            self.son_okutma_label.setText(f"✗ {paket['lot_no']} silindi")
            self.son_okutma_label.setStyleSheet(f"color: {self.theme.get('warning')}; font-size: 12px;")
    
    def _temizle(self):
        """Formu temizle"""
        if self.okutulan_paketler:
            reply = QMessageBox.question(
                self, "Onay",
                f"{len(self.okutulan_paketler)} paket okutulmuş.\n\nTemizlemek istediğinize emin misiniz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        self.okutulan_paketler = []
        self.plaka_input.setCurrentIndex(0)
        self.sofor_input.setCurrentIndex(0)
        self.tasiyici_input.setCurrentIndex(0)
        self.not_input.clear()
        self._refresh_table()
        self._load_hazir_urunler()
        self.son_okutma_label.setText("Son okutma: -")
        self.son_okutma_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px;")
        self.barkod_input.setFocus()
    
    def _sevkiyat_olustur(self):
        """Tüm müşteriler için toplu sevkiyat oluştur"""
        if not self.okutulan_paketler:
            QMessageBox.warning(self, "Uyarı", "En az bir paket okutmalısınız!")
            return
        
        # Müşterilere göre grupla
        musteri_gruplari = {}
        for paket in self.okutulan_paketler:
            musteri = paket['musteri']
            cari_id = paket.get('cari_id')
            key = (cari_id, musteri)
            if key not in musteri_gruplari:
                musteri_gruplari[key] = {
                    'musteri': musteri,
                    'paketler': [],
                    'toplam_adet': 0
                }
            musteri_gruplari[key]['paketler'].append(paket)
            musteri_gruplari[key]['toplam_adet'] += paket['miktar']
        
        # Birden fazla müşteri varsa detaylı uyar
        if len(musteri_gruplari) > 1:
            detay_text = "\n".join([
                f"  • {data['musteri']}: {len(data['paketler'])} paket, {data['toplam_adet']:,.0f} adet"
                for key, data in musteri_gruplari.items()
            ])
            
            reply = QMessageBox.question(
                self, "⚠️ Birden Fazla Müşteri",
                f"🔔 UYARI: {len(musteri_gruplari)} FARKLI MÜŞTERİ TESPİT EDİLDİ!\n\n"
                f"{detay_text}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ EVET: Her müşteri için AYRI irsaliye oluştur\n"
                "❌ HAYIR: İptal et\n\n"
                "Devam edilsin mi?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        # Her müşteri için irsaliye oluştur
        olusturulan = []
        basarisiz = []
        
        for (cari_id, musteri), data in musteri_gruplari.items():
            try:
                # Otomatik mod: Her müşteri için ayrı onay sorma
                self._irsaliye_olustur(cari_id, musteri, otomatik=True)
                olusturulan.append(f"{musteri} ({len(data['paketler'])} paket)")
            except Exception as e:
                basarisiz.append(f"{musteri}: {str(e)}")
        
        # Sonuç mesajı
        if olusturulan:
            msg = f"✅ {len(olusturulan)} müşteri için irsaliye oluşturuldu:\n\n" + "\n".join([f"  • {m}" for m in olusturulan])
            if basarisiz:
                msg += f"\n\n❌ Başarısız:\n" + "\n".join([f"  • {m}" for m in basarisiz])
            QMessageBox.information(self, "Sevkiyat Tamamlandı", msg)
            
            # Ekranı temizle
            self.okutulan_paketler = []
            self._refresh_table()
            self._load_hazir_urunler()
        elif basarisiz:
            QMessageBox.critical(
                self, "Hata",
                f"❌ Hiçbir irsaliye oluşturulamadı:\n\n" + "\n".join([f"  • {m}" for m in basarisiz])
            )
