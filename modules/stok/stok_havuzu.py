# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Stok Havuzu Sayfası
Giriş irsaliyesinden kabul edilen lotları listeler, iş emri oluşturma akışını başlatır
"""
import os
import sys
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox, QMessageBox,
    QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class StokHavuzuPage(BasePage):
    """Stok Havuzu Sayfası - Kullanılabilir lotları listeler"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.selected_lots = []  # Seçilen lotlar
        
        # Güvenli theme erişimi
        self.bg_card = brand.BG_CARD
        self.bg_input = brand.BG_INPUT
        self.bg_main = brand.BG_MAIN
        self.text = brand.TEXT
        self.text_muted = brand.TEXT_MUTED
        self.border = brand.BORDER
        self.primary = brand.PRIMARY
        self.success = brand.SUCCESS
        self.warning = brand.WARNING
        
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        layout.addWidget(self._create_header())
        
        # Filtreler
        layout.addWidget(self._create_filters())
        
        # Tablo
        self.table = self._create_table()
        layout.addWidget(self.table)
        
        # Alt bar - Seçim bilgisi ve butonlar
        layout.addWidget(self._create_bottom_bar())
    
    def _create_header(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.bg_card}; border-radius: 8px; padding: 16px; }}")
        
        layout = QHBoxLayout(frame)
        
        title = QLabel("📦 Stok Havuzu")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.text};")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Yenile butonu
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.bg_input}; color: {self.text};
                border: 1px solid {self.border}; border-radius: 6px;
                padding: 8px 16px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {self.border}; }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        layout.addWidget(refresh_btn)
        
        return frame
    
    def _create_filters(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.bg_card}; border-radius: 8px; padding: 12px; }}")
        
        layout = QHBoxLayout(frame)
        layout.setSpacing(12)
        
        input_style = f"""
            background: {self.bg_input}; color: {self.text};
            border: 1px solid {self.border}; border-radius: 6px;
            padding: 8px 12px; min-width: 150px;
        """
        
        # Arama
        layout.addWidget(QLabel("🔍"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Stok kodu veya adı ara...")
        self.search_input.setStyleSheet(f"QLineEdit {{ {input_style} min-width: 250px; }}")
        self.search_input.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self.search_input)
        
        # Müşteri filtresi
        layout.addWidget(QLabel("Müşteri:"))
        self.musteri_combo = QComboBox()
        self.musteri_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.musteri_combo.addItem("Tümü", "")
        self.musteri_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.musteri_combo)
        
        # Depo filtresi
        layout.addWidget(QLabel("Depo:"))
        self.depo_combo = QComboBox()
        self.depo_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.depo_combo.addItem("Tümü", "")
        self.depo_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.depo_combo)
        
        layout.addStretch()
        
        return frame
    
    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "Seç", "Lot No", "Stok Kodu", "Stok Adı", "Müşteri",
            "Miktar", "Rezerve", "Kullanılabilir", "Depo"
        ])
        
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.bg_card}; color: {self.text};
                border: 1px solid {self.border}; border-radius: 8px;
                gridline-color: {self.border};
            }}
            QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {self.border}; }}
            QTableWidget::item:selected {{ background: {self.primary}; }}
            QHeaderView::section {{
                background: {self.bg_input}; color: {self.text};
                padding: 10px; border: none; font-weight: bold;
            }}
        """)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Seç
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Lot No
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Stok Kodu
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Stok Adı
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Müşteri
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Miktar
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Rezerve
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Kullanılabilir
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Depo
        
        table.setColumnWidth(0, 60)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        
        return table
    
    def _create_bottom_bar(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.bg_card}; border-radius: 8px; padding: 12px; }}")
        
        layout = QHBoxLayout(frame)
        
        # Seçim bilgisi
        self.selection_label = QLabel("Seçili: 0 lot, 0 adet")
        self.selection_label.setStyleSheet(f"color: {self.text}; font-size: 14px;")
        layout.addWidget(self.selection_label)
        
        layout.addStretch()
        
        # Tümünü seç
        select_all_btn = QPushButton("☑️ Tümünü Seç")
        select_all_btn.setCursor(Qt.PointingHandCursor)
        select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.bg_input}; color: {self.text};
                border: 1px solid {self.border}; border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: {self.border}; }}
        """)
        select_all_btn.clicked.connect(self._select_all)
        layout.addWidget(select_all_btn)
        
        # Seçimi temizle
        clear_btn = QPushButton("⬜ Seçimi Temizle")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.bg_input}; color: {self.text};
                border: 1px solid {self.border}; border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: {self.border}; }}
        """)
        clear_btn.clicked.connect(self._clear_selection)
        layout.addWidget(clear_btn)
        
        # Yeni İş Emri butonu
        new_order_btn = QPushButton("📋 Yeni İş Emri Oluştur")
        new_order_btn.setCursor(Qt.PointingHandCursor)
        new_order_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.success}; color: white;
                border: none; border-radius: 6px;
                padding: 10px 20px; font-weight: bold; font-size: 14px;
            }}
            QPushButton:hover {{ background: #1da34d; }}
        """)
        new_order_btn.clicked.connect(self._create_is_emri)
        layout.addWidget(new_order_btn)
        
        return frame
    
    def _load_data(self):
        """Stok bakiye verilerini yükle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Müşteri listesini yükle
            self._load_musteriler(cursor)

            # Depo listesini yükle
            self._load_depolar(cursor)

            # Stok verilerini yükle
            self._load_stok_data(cursor)

        except ConnectionError:
            from core.themed_messagebox import themed_warning
            themed_warning(self, "Bağlantı Hatası", "Veritabanına bağlanılamadı.\nVeriler yüklenemedi.")
        except Exception as e:
            print(f"[stok_havuzu] Veri yükleme hatası: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def _load_musteriler(self, cursor):
        """Müşteri listesini yükle"""
        try:
            self.musteri_combo.blockSignals(True)
            current = self.musteri_combo.currentData()
            self.musteri_combo.clear()
            self.musteri_combo.addItem("Tümü", "")
            
            cursor.execute("""
                SELECT DISTINCT sk.cari_unvani 
                FROM StokKartlari sk
                WHERE sk.cari_unvani IS NOT NULL AND sk.cari_unvani != ''
                ORDER BY sk.cari_unvani
            """)
            
            for row in cursor.fetchall():
                if row[0]:
                    self.musteri_combo.addItem(row[0], row[0])
            
            # Önceki seçimi geri yükle
            if current:
                idx = self.musteri_combo.findData(current)
                if idx >= 0:
                    self.musteri_combo.setCurrentIndex(idx)
            
            self.musteri_combo.blockSignals(False)
            
        except Exception as e:
            print(f"Müşteri yükleme hatası: {e}")
    
    def _load_depolar(self, cursor):
        """Depo listesini yükle"""
        try:
            self.depo_combo.blockSignals(True)
            current = self.depo_combo.currentData()
            self.depo_combo.clear()
            self.depo_combo.addItem("Tümü", "")
            
            cursor.execute("SELECT id, depo_adi FROM stok.depolar WHERE aktif_mi = 1 ORDER BY depo_adi")
            
            for row in cursor.fetchall():
                self.depo_combo.addItem(row[1], row[0])
            
            if current:
                idx = self.depo_combo.findData(current)
                if idx >= 0:
                    self.depo_combo.setCurrentIndex(idx)
            
            self.depo_combo.blockSignals(False)
            
        except Exception as e:
            print(f"Depo yükleme hatası: {e}")
    
    def _load_stok_data(self, cursor=None):
        """Stok bakiye verilerini tabloya yükle"""
        close_conn = False
        try:
            if cursor is None:
                conn = get_db_connection()
                if not conn:
                    return
                cursor = conn.cursor()
                close_conn = True
            
            # Filtreler
            search = self.search_input.text().strip()
            musteri = self.musteri_combo.currentData() or ""
            depo_id = self.depo_combo.currentData() or ""
            
            # SQL sorgusu
            query = """
                SELECT 
                    sb.id,
                    sb.lot_no,
                    u.urun_kodu,
                    u.urun_adi,
                    ISNULL(sk.cari_unvani, '') as musteri,
                    sb.miktar,
                    sb.rezerve_miktar,
                    sb.miktar - ISNULL(sb.rezerve_miktar, 0) as kullanilabilir,
                    ISNULL(d.ad, 'Ana Depo') as depo,
                    sb.urun_id,
                    sb.depo_id,
                    sk.bara_miktar
                FROM stok.stok_bakiye sb
                JOIN stok.urunler u ON sb.urun_id = u.id
                LEFT JOIN StokKartlari sk ON u.urun_kodu = sk.stok_kodu
                LEFT JOIN stok.depolar d ON sb.depo_id = d.id
                WHERE (sb.miktar - ISNULL(sb.rezerve_miktar, 0)) > 0
            """
            
            params = []
            
            if search:
                query += " AND (u.urun_kodu LIKE ? OR u.urun_adi LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            
            if musteri:
                query += " AND sk.cari_unvani = ?"
                params.append(musteri)
            
            if depo_id:
                query += " AND sb.depo_id = ?"
                params.append(depo_id)
            
            query += " ORDER BY sb.lot_no DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Tabloyu doldur
            self.table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                # Checkbox
                checkbox = QCheckBox()
                checkbox.setStyleSheet("QCheckBox { margin-left: 15px; }")
                checkbox.stateChanged.connect(self._update_selection)
                
                # Lot verilerini checkbox'a ekle
                checkbox.setProperty("lot_data", {
                    'id': row[0],
                    'lot_no': row[1],
                    'urun_kodu': row[2],
                    'urun_adi': row[3],
                    'musteri': row[4],
                    'miktar': float(row[5]) if row[5] else 0,
                    'kullanilabilir': float(row[7]) if row[7] else 0,
                    'urun_id': row[9],
                    'depo_id': row[10],
                    'bara_miktar': int(row[11]) if row[11] else 1
                })
                
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.table.setCellWidget(i, 0, checkbox_widget)
                
                # Diğer kolonlar
                self.table.setItem(i, 1, QTableWidgetItem(str(row[1] or "")))
                self.table.setItem(i, 2, QTableWidgetItem(str(row[2] or "")))
                self.table.setItem(i, 3, QTableWidgetItem(str(row[3] or "")))
                self.table.setItem(i, 4, QTableWidgetItem(str(row[4] or "")))
                
                # Miktar kolonları
                miktar_item = QTableWidgetItem(f"{row[5]:,.0f}" if row[5] else "0")
                miktar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, 5, miktar_item)
                
                rezerve_item = QTableWidgetItem(f"{row[6]:,.0f}" if row[6] else "0")
                rezerve_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, 6, rezerve_item)
                
                kullanilabilir_item = QTableWidgetItem(f"{row[7]:,.0f}" if row[7] else "0")
                kullanilabilir_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                kullanilabilir_item.setForeground(QColor(self.success))
                self.table.setItem(i, 7, kullanilabilir_item)
                
                self.table.setItem(i, 8, QTableWidgetItem(str(row[8] or "")))
            
            if close_conn:
                conn.close()
                
        except Exception as e:
            print(f"Stok veri yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_filter_changed(self):
        """Filtre değiştiğinde"""
        self._load_stok_data()
    
    def _update_selection(self):
        """Seçim değiştiğinde"""
        self.selected_lots = []
        total_qty = 0
        
        for i in range(self.table.rowCount()):
            widget = self.table.cellWidget(i, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    lot_data = checkbox.property("lot_data")
                    if lot_data:
                        self.selected_lots.append(lot_data)
                        total_qty += lot_data.get('kullanilabilir', 0)
        
        self.selection_label.setText(f"Seçili: {len(self.selected_lots)} lot, {total_qty:,.0f} adet")
    
    def _select_all(self):
        """Tüm satırları seç"""
        for i in range(self.table.rowCount()):
            widget = self.table.cellWidget(i, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
    
    def _clear_selection(self):
        """Seçimi temizle"""
        for i in range(self.table.rowCount()):
            widget = self.table.cellWidget(i, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
    
    def _create_is_emri(self):
        """Seçili lotlarla iş emri oluştur"""
        if not self.selected_lots:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir lot seçin!")
            return
        
        # Aynı müşteri kontrolü
        musteriler = set(lot.get('musteri', '') for lot in self.selected_lots)
        if len(musteriler) > 1:
            QMessageBox.warning(
                self, "Uyarı", 
                "Farklı müşterilere ait lotlar seçilemez!\nLütfen aynı müşterinin lotlarını seçin."
            )
            return
        
        # Aynı ürün kontrolü
        urunler = set(lot.get('urun_kodu', '') for lot in self.selected_lots)
        if len(urunler) > 1:
            QMessageBox.warning(
                self, "Uyarı", 
                "Farklı ürünlere ait lotlar seçilemez!\nLütfen aynı ürünün lotlarını seçin."
            )
            return
        
        # İş emri dialog'unu aç
        try:
            from pages.is_emri.ie_yeni import IsEmriYeniPage
            
            dialog = IsEmriYeniPage(
                is_emri_id=None,
                theme=self.theme,
                selected_lots=self.selected_lots,  # Seçili lotları gönder
                parent=self
            )
            
            if dialog.exec():
                # Başarılı kayıt sonrası listeyi yenile
                self._load_data()
                self._clear_selection()
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İş emri açılamadı: {e}")
            import traceback
            traceback.print_exc()
