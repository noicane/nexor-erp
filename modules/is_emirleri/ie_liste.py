# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İş Emri Liste Sayfası
[MODERNIZED UI - v3.0]
"""
import os
import sys
from datetime import datetime, date

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from config import DEFAULT_PAGE_SIZE


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


class IsEmriListePage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.page_size = DEFAULT_PAGE_SIZE
        self.current_page = 1
        self.total_pages = 1
        self.total_items = 0
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        layout.addWidget(self._create_header())
        layout.addWidget(self._create_toolbar())
        self.table = self._create_table()
        layout.addWidget(self.table)
        layout.addWidget(self._create_bottom_bar())
    
    def _create_header(self) -> QFrame:
        s = self.s
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }}")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        title_row = QHBoxLayout()
        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 24px;")
        title_row.addWidget(icon)
        title = QLabel("İş Emirleri")
        title.setStyleSheet(f"color: {s['text']}; font-size: 20px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Tüm iş emirlerini görüntüleyin ve yönetin")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 12px;")
        title_section.addWidget(subtitle)
        layout.addLayout(title_section)
        layout.addStretch()
        
        new_btn = QPushButton("➕ Yeni İş Emri")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }} QPushButton:hover {{ background: #059669; }}")
        new_btn.clicked.connect(self._new_is_emri)
        layout.addWidget(new_btn)
        return frame
    
    def _create_toolbar(self) -> QFrame:
        s = self.s
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }}")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        input_style = f"background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 6px; padding: 8px 12px; font-size: 12px;"
        label_style = f"color: {s['text']}; font-weight: 600; font-size: 12px;"
        
        lbl = QLabel("🔍 Arama:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("İş emri no, müşteri...")
        self.search_input.setFixedWidth(180)
        self.search_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        self.search_input.returnPressed.connect(self._load_data)
        layout.addWidget(self.search_input)
        
        lbl2 = QLabel("📅 Tarih:")
        lbl2.setStyleSheet(label_style)
        layout.addWidget(lbl2)
        
        self.tarih_bas = QDateEdit()
        self.tarih_bas.setDate(QDate.currentDate().addDays(-30))
        self.tarih_bas.setCalendarPopup(True)
        self.tarih_bas.setStyleSheet(f"QDateEdit {{ {input_style} min-width: 100px; }}")
        self.tarih_bas.dateChanged.connect(self._filter_changed)
        layout.addWidget(self.tarih_bas)

        layout.addWidget(QLabel("-", styleSheet=f"color: {s['text_muted']};"))

        self.tarih_bit = QDateEdit()
        self.tarih_bit.setDate(QDate.currentDate().addDays(30))
        self.tarih_bit.setCalendarPopup(True)
        self.tarih_bit.setStyleSheet(f"QDateEdit {{ {input_style} min-width: 100px; }}")
        self.tarih_bit.dateChanged.connect(self._filter_changed)
        layout.addWidget(self.tarih_bit)
        
        lbl3 = QLabel("Durum:")
        lbl3.setStyleSheet(label_style)
        layout.addWidget(lbl3)
        
        self.durum_combo = QComboBox()
        self.durum_combo.addItem("Tümü", "")
        self.durum_combo.addItem("Bekliyor", "BEKLIYOR")
        self.durum_combo.addItem("Planlandı", "PLANLI")
        self.durum_combo.addItem("Üretimde", "URETIMDE")
        self.durum_combo.addItem("Tamamlandı", "TAMAMLANDI")
        self.durum_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.durum_combo.currentIndexChanged.connect(self._filter_changed)
        layout.addWidget(self.durum_combo)
        
        search_btn = QPushButton("🔍 Ara")
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; }} QPushButton:hover {{ background: #B91C1C; }}")
        search_btn.clicked.connect(self._load_data)
        layout.addWidget(search_btn)

        pdf_btn = QPushButton("📄 PDF")
        pdf_btn.setCursor(Qt.PointingHandCursor)
        pdf_btn.setStyleSheet(f"QPushButton {{ background: {s['info']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; }} QPushButton:hover {{ background: #2563EB; }}")
        pdf_btn.clicked.connect(self._export_pdf)
        layout.addWidget(pdf_btn)

        layout.addStretch()
        return frame
    
    def _create_table(self) -> QTableWidget:
        s = self.s
        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels(["İş Emri No", "Termin", "Müşteri", "Ürün", "Kaplama", "Miktar", "Bara", "Hat", "Durum", "Oluşturma"])
        table.setStyleSheet(f"""
            QTableWidget {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; font-size: 12px; }}
            QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {s['border']}; }}
            QTableWidget::item:selected {{ background: {s['primary']}; }}
            QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 10px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 11px; }}
        """)
        header = table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        table.setColumnWidth(0, 120)
        table.setColumnWidth(1, 90)
        table.setColumnWidth(4, 90)
        table.setColumnWidth(5, 70)
        table.setColumnWidth(6, 60)
        table.setColumnWidth(7, 70)
        table.setColumnWidth(8, 90)
        table.setColumnWidth(9, 90)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(False)
        table.doubleClicked.connect(self._open_detail)
        return table
    
    def _create_bottom_bar(self) -> QFrame:
        s = self.s
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; }}")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)
        
        self.stat_label = QLabel("Yükleniyor...")
        self.stat_label.setStyleSheet(f"color: {s['text_secondary']}; font-size: 12px;")
        layout.addWidget(self.stat_label)
        layout.addStretch()
        
        btn_style = f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 6px; padding: 6px 14px; font-size: 12px; }} QPushButton:hover {{ background: {s['border']}; }}"
        
        self.prev_btn = QPushButton("◀ Önceki")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet(btn_style)
        self.prev_btn.clicked.connect(self._prev_page)
        layout.addWidget(self.prev_btn)
        
        self.page_label = QLabel("1 / 1")
        self.page_label.setStyleSheet(f"color: {s['text']}; padding: 0 12px; font-weight: 600;")
        layout.addWidget(self.page_label)
        
        self.next_btn = QPushButton("Sonraki ▶")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(btn_style)
        self.next_btn.clicked.connect(self._next_page)
        layout.addWidget(self.next_btn)
        return frame
    
    def _load_data(self):
        s = self.s
        self.stat_label.setText("Yükleniyor...")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """SELECT id, is_emri_no, termin_tarihi, cari_unvani, stok_kodu, stok_adi, kaplama_tipi, toplam_miktar, birim, toplam_bara, hat_id, durum, olusturma_tarihi FROM siparis.is_emirleri WHERE silindi_mi = 0 ORDER BY id DESC"""
            cursor.execute(sql)
            items = []
            for row in cursor.fetchall():
                item = []
                for i in range(13):
                    try:
                        item.append(row[i])
                    except:
                        item.append(None)
                items.append(item)
            conn.close()
            
            arama = self.search_input.text().strip().lower()
            durum_filtre = self.durum_combo.currentData() or ""
            tarih_bas = self.tarih_bas.date().toPython()
            tarih_bit = self.tarih_bit.date().toPython()

            filtered = []
            for item in items:
                # Arama filtresi
                if arama:
                    is_emri_no = str(item[1] or '').lower()
                    cari = str(item[3] or '').lower()
                    stok = str(item[4] or '').lower()
                    if arama not in is_emri_no and arama not in cari and arama not in stok:
                        continue
                # Durum filtresi
                if durum_filtre:
                    if str(item[11] or '') != durum_filtre:
                        continue
                # Tarih filtresi (termin tarihine göre)
                termin = item[2]
                if termin:
                    if hasattr(termin, 'date'):
                        termin = termin.date()
                    if termin < tarih_bas or termin > tarih_bit:
                        continue
                filtered.append(item)
            
            self.total_items = len(filtered)
            self.total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)
            start = (self.current_page - 1) * self.page_size
            end = start + self.page_size
            page_items = filtered[start:end]
            self._populate_table(page_items)
            self._update_paging()
            self.stat_label.setText(f"Toplam: {self.total_items} iş emri")
        except Exception as e:
            self.stat_label.setText(f"Hata: {str(e)[:50]}")
            self.table.setRowCount(0)
    
    def _populate_table(self, items):
        s = self.s
        self.table.clearSelection()
        self.table.setRowCount(0)
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            no_item = QTableWidgetItem(str(item[1] or ''))
            try:
                id_val = int(item[0]) if item[0] else 0
            except:
                id_val = 0
            no_item.setData(Qt.UserRole, id_val)
            self.table.setItem(row, 0, no_item)
            
            termin = item[2]
            termin_str = str(termin)[:10] if termin else '-'
            termin_item = QTableWidgetItem(termin_str)
            if termin and termin < date.today():
                termin_item.setForeground(QColor(s['error']))
            self.table.setItem(row, 1, termin_item)
            
            self.table.setItem(row, 2, QTableWidgetItem(str(item[3] or '')[:25]))
            self.table.setItem(row, 3, QTableWidgetItem(str(item[4] or '')))
            self.table.setItem(row, 4, QTableWidgetItem(str(item[6] or '')))
            
            miktar = item[7] or 0
            self.table.setItem(row, 5, QTableWidgetItem(f"{miktar:,.0f}"))
            self.table.setItem(row, 6, QTableWidgetItem(str(item[9] or '')))
            self.table.setItem(row, 7, QTableWidgetItem('-'))
            
            durum = item[11] or 'BEKLIYOR'
            durum_item = QTableWidgetItem(durum)
            colors = {'BEKLIYOR': s['warning'], 'PLANLI': s['info'], 'URETIMDE': s['success'], 'TAMAMLANDI': '#10b981'}
            durum_item.setForeground(QColor(colors.get(durum, '#888')))
            self.table.setItem(row, 8, durum_item)
            
            olusturma = item[12]
            self.table.setItem(row, 9, QTableWidgetItem(str(olusturma)[:10] if olusturma else ''))
    
    def _update_paging(self):
        self.page_label.setText(f"{self.current_page} / {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
    
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load_data()
    
    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._load_data()
    
    def _filter_changed(self):
        """Filtre değiştiğinde sayfayı sıfırla ve yeniden yükle"""
        self.current_page = 1
        self._load_data()

    def _export_pdf(self):
        """Seçili iş emrini PDF olarak dışa aktar"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen PDF çıktısı almak için bir iş emri seçin.")
            return
        item = self.table.item(current_row, 0)
        if not item:
            return
        is_emri_id = item.data(Qt.UserRole)
        try:
            is_emri_id = int(is_emri_id) if is_emri_id else None
        except:
            is_emri_id = None
        if not is_emri_id:
            return
        try:
            from utils.is_emri_pdf import is_emri_pdf_olustur
            is_emri_pdf_olustur(is_emri_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturma hatası: {e}")

    def _new_is_emri(self):
        from modules.is_emirleri.ie_yeni import IsEmriYeniPage
        dialog = IsEmriYeniPage(theme=self.theme, parent=self)
        if dialog.exec():
            self._load_data()
    
    def _open_detail(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        item = self.table.item(current_row, 0)
        if not item:
            return
        is_emri_id = item.data(Qt.UserRole)
        try:
            is_emri_id = int(is_emri_id) if is_emri_id else None
        except:
            is_emri_id = None
        if is_emri_id:
            from modules.is_emirleri.ie_yeni import IsEmriYeniPage
            dialog = IsEmriYeniPage(is_emri_id=is_emri_id, theme=self.theme, parent=self)
            if dialog.exec():
                self._load_data()
