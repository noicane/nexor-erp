# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Sevkiyat Listesi Sayfası
Sevk deposunda bekleyen kalite onaylı lotları listeler
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection

# Sevke hazır durumlar
SEVK_HAZIR_DURUMLAR = ('KONTROL_EDILDI', 'ONAYLANDI', 'SEVKE_HAZIR')


class SevkListePage(BasePage):
    """Sevkiyat Listesi Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
        
        # Saat güncelleme
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📦 Sevkiyat Listesi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text', '#fff')};")
        header.addWidget(title)
        
        header.addStretch()
        
        # Saat
        self.saat_label = QLabel()
        self.saat_label.setStyleSheet(f"color: {self.theme.get('text_muted', '#8a94a6')}; font-size: 18px; font-weight: bold;")
        header.addWidget(self.saat_label)
        
        # Yenile butonu
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(self._button_style())
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Filtre satırı
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {self.theme.get('bg_card', '#242938')}; border-radius: 8px; padding: 8px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 8, 12, 8)
        
        # Müşteri filtresi
        filter_layout.addWidget(QLabel("Müşteri:"))
        self.musteri_filter = QComboBox()
        self.musteri_filter.setMinimumWidth(200)
        self.musteri_filter.setStyleSheet(self._input_style())
        self.musteri_filter.currentIndexChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.musteri_filter)
        
        filter_layout.addSpacing(20)
        
        # Arama
        filter_layout.addWidget(QLabel("Ara:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Lot no, stok kodu...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        
        # Özet bilgiler
        self.ozet_label = QLabel()
        self.ozet_label.setStyleSheet(f"color: {self.theme.get('primary', '#6366f1')}; font-weight: bold;")
        filter_layout.addWidget(self.ozet_label)
        
        layout.addWidget(filter_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Lot No", "Müşteri", "Stok Kodu", "Stok Adı", 
            "Miktar", "Birim", "Kalite Tarihi", "Gün", "Durum"
        ])
        
        # ID kolonunu gizle
        self.table.setColumnHidden(0, True)
        
        # Kolon genişlikleri
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Müşteri
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Stok Adı
        self.table.setColumnWidth(1, 130)  # Lot No
        self.table.setColumnWidth(3, 120)  # Stok Kodu
        self.table.setColumnWidth(5, 80)   # Miktar
        self.table.setColumnWidth(6, 60)   # Birim
        self.table.setColumnWidth(7, 100)  # Kalite Tarihi
        self.table.setColumnWidth(8, 60)   # Gün
        self.table.setColumnWidth(9, 100)  # Durum
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.setStyleSheet(self._table_style())
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table, 1)
        
        # Alt bilgi satırı
        footer = QHBoxLayout()
        
        self.secili_label = QLabel("Seçili: 0 lot")
        self.secili_label.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        footer.addWidget(self.secili_label)
        
        footer.addStretch()
        
        # Yeni Sevkiyat butonu
        self.sevk_btn = QPushButton("🚚 Yeni Sevkiyat Oluştur")
        self.sevk_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {self.theme.get('success_hover', '#16a34a')};
            }}
        """)
        self.sevk_btn.clicked.connect(self._yeni_sevkiyat)
        footer.addWidget(self.sevk_btn)
        
        layout.addLayout(footer)
        
        # Seçim değişikliği
        self.table.itemSelectionChanged.connect(self._update_selection)
    
    def _button_style(self):
        return f"""
            QPushButton {{
                background: {self.theme.get('bg_input', '#2d3548')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {self.theme.get('bg_hover', '#3d4454')};
            }}
        """
    
    def _input_style(self):
        return f"""
            QLineEdit, QComboBox, QDateEdit {{
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
                alternate-background-color: {self.theme.get('bg_main', '#1a1f2e')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border', '#3d4454')};
                color: {self.theme.get('text', '#ffffff')};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {self.theme.get('border', '#3d4454')};
            }}
            QTableWidget::item:selected {{
                background-color: {self.theme.get('primary', '#6366f1')};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {self.theme.get('bg_input', '#2d3548')};
                color: {self.theme.get('text', '#ffffff')};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary', '#6366f1')};
                font-weight: bold;
            }}
        """
    
    def _update_time(self):
        now = datetime.now()
        self.saat_label.setText(now.strftime("%H:%M:%S"))
    
    def _load_data(self):
        """Sevke hazır lotları yükle - SEV deposundaki stoklar"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # SEV deposundaki ONAYLANDI durumlu stokları getir
            query = """
                SELECT 
                    sb.id,
                    sb.lot_no,
                    COALESCE(ie.cari_unvani, 'Tanımsız') as musteri,
                    COALESCE(ie.stok_kodu, sb.stok_kodu, '') as stok_kodu,
                    COALESCE(ie.stok_adi, sb.stok_adi, '') as stok_adi,
                    sb.miktar,
                    COALESCE(sb.birim, 'ADET') as birim,
                    sb.son_hareket_tarihi as kontrol_tarihi,
                    DATEDIFF(day, sb.son_hareket_tarihi, GETDATE()) as gun_sayisi,
                    sb.kalite_durumu as durum,
                    ie.cari_id,
                    ie.id as is_emri_id
                FROM stok.stok_bakiye sb
                LEFT JOIN siparis.is_emirleri ie ON REPLACE(REPLACE(sb.lot_no, '-SEV', ''), '-SEVK', '') = ie.lot_no
                JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE d.kod IN ('SEV-01', 'SEVK', 'SEV', 'MAMUL')
                  AND sb.kalite_durumu IN ('ONAYLANDI', 'OK', 'SEVKE_HAZIR')
                  AND sb.miktar > 0
                ORDER BY sb.son_hareket_tarihi DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            print(f"DEBUG: Sevk listesi - {len(rows)} kayıt bulundu")
            
            # Tabloyu doldur
            self.table.setRowCount(0)
            self.all_data = []
            musteriler = set()
            
            for row in rows:
                data = {
                    'id': row[0],
                    'lot_no': row[1] or '',
                    'musteri': row[2] or 'Tanımsız',
                    'stok_kodu': row[3] or '',
                    'stok_adi': row[4] or '',
                    'miktar': row[5] or 0,
                    'birim': row[6] or 'ADET',
                    'kalite_tarihi': row[7],
                    'gun_sayisi': row[8] or 0,
                    'durum': row[9] or 'ONAYLANDI',
                    'cari_id': row[10],
                    'is_emri_id': row[11]
                }
                self.all_data.append(data)
                musteriler.add(data['musteri'])
            
            # Müşteri filtresini güncelle
            self.musteri_filter.blockSignals(True)
            self.musteri_filter.clear()
            self.musteri_filter.addItem("-- Tümü --", None)
            for m in sorted(musteriler):
                if m:
                    self.musteri_filter.addItem(m, m)
            self.musteri_filter.blockSignals(False)
            
            conn.close()
            
            # Tabloyu göster
            self._display_data(self.all_data)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Veri yüklenemedi: {e}")
    
    def _display_data(self, data_list):
        """Tabloyu verilerle doldur"""
        self.table.setRowCount(0)
        
        for data in data_list:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            # ID
            item = QTableWidgetItem(str(data['id']))
            self.table.setItem(row_idx, 0, item)
            
            # Lot No
            item = QTableWidgetItem(data['lot_no'])
            item.setForeground(QColor(self.theme.get('primary', '#6366f1')))
            self.table.setItem(row_idx, 1, item)
            
            # Müşteri
            self.table.setItem(row_idx, 2, QTableWidgetItem(data['musteri']))
            
            # Stok Kodu
            self.table.setItem(row_idx, 3, QTableWidgetItem(data['stok_kodu']))
            
            # Stok Adı
            self.table.setItem(row_idx, 4, QTableWidgetItem(data['stok_adi']))
            
            # Miktar
            item = QTableWidgetItem(f"{data['miktar']:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 5, item)
            
            # Birim
            self.table.setItem(row_idx, 6, QTableWidgetItem(data['birim']))
            
            # Kalite Tarihi
            kalite_str = data['kalite_tarihi'].strftime('%d.%m.%Y') if data['kalite_tarihi'] else '-'
            self.table.setItem(row_idx, 7, QTableWidgetItem(kalite_str))
            
            # Gün
            item = QTableWidgetItem(str(data['gun_sayisi']))
            item.setTextAlignment(Qt.AlignCenter)
            # Eski lotları vurgula
            if data['gun_sayisi'] > 7:
                item.setForeground(QColor(self.theme.get('warning', '#f59e0b')))
            if data['gun_sayisi'] > 14:
                item.setForeground(QColor(self.theme.get('danger', '#ef4444')))
            self.table.setItem(row_idx, 8, item)
            
            # Durum
            item = QTableWidgetItem(data['durum'])
            if data['durum'] == 'Rezerve':
                item.setForeground(QColor(self.theme.get('warning', '#f59e0b')))
            else:
                item.setForeground(QColor(self.theme.get('success', '#22c55e')))
            self.table.setItem(row_idx, 9, item)
        
        # Özet güncelle
        toplam_lot = len(data_list)
        toplam_miktar = sum(d['miktar'] for d in data_list)
        self.ozet_label.setText(f"Toplam: {toplam_lot} lot, {toplam_miktar:,.0f} adet")
    
    def _apply_filter(self):
        """Filtreleri uygula"""
        musteri = self.musteri_filter.currentData()
        search = self.search_input.text().lower().strip()
        
        filtered = []
        for data in self.all_data:
            # Müşteri filtresi
            if musteri and data['musteri'] != musteri:
                continue
            
            # Arama filtresi
            if search:
                searchable = f"{data['lot_no']} {data['stok_kodu']} {data['stok_adi']}".lower()
                if search not in searchable:
                    continue
            
            filtered.append(data)
        
        self._display_data(filtered)
    
    def _update_selection(self):
        """Seçim değiştiğinde"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        self.secili_label.setText(f"Seçili: {len(selected_rows)} lot")
    
    def _yeni_sevkiyat(self):
        """Yeni sevkiyat sayfasına yönlendir"""
        # Ana pencereye sinyal gönder
        # Bu örnek için mesaj göster
        QMessageBox.information(
            self, 
            "Bilgi", 
            "Yeni Sevkiyat sayfasına yönlendiriliyorsunuz.\n\n"
            "Barkod okutarak paketleri ekleyebilirsiniz."
        )
        # TODO: Ana pencereden sayfa değişikliği tetiklenecek
