# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Depo Takip Sayfası
Tüm depoların anlık stok durumunu gösterir
[MODERNIZED UI - v2.0]
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QSplitter, QWidget,
    QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection

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

class DepoTakipPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.secili_depo_id = None
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
        self.auto_refresh = QTimer(); self.auto_refresh.timeout.connect(self._load_data); self.auto_refresh.start(10000)
        self.timer = QTimer(); self.timer.timeout.connect(self._update_time); self.timer.start(1000)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout(); title_section = QVBoxLayout(); title_section.setSpacing(4)
        title_row = QHBoxLayout(); icon = QLabel("🏭"); icon.setStyleSheet("font-size: 28px;"); title_row.addWidget(icon)
        title = QLabel("Depo Takip"); title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;"); title_row.addWidget(title); title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Anlık depo stok durumları"); subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;"); title_section.addWidget(subtitle)
        header.addLayout(title_section); header.addStretch()
        self.auto_label = QLabel("⟳ Otomatik yenileme: 10sn"); self.auto_label.setStyleSheet(f"color: {s['success']}; font-size: 12px;"); header.addWidget(self.auto_label)
        header.addSpacing(20)
        self.saat_label = QLabel(); self.saat_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 18px; font-weight: bold;"); header.addWidget(self.saat_label)
        refresh_btn = QPushButton("🔄"); refresh_btn.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}"); refresh_btn.clicked.connect(self._load_data); header.addWidget(refresh_btn)
        layout.addLayout(header)
        
        # Özet kartları
        self.ozet_frame = QFrame(); self.ozet_frame.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px;")
        ozet_layout = QHBoxLayout(self.ozet_frame); ozet_layout.setContentsMargins(16, 16, 16, 16); ozet_layout.setSpacing(16)
        self.kart_depo = self._create_ozet_kart("🏭", "Toplam Depo", "0", s['primary']); ozet_layout.addWidget(self.kart_depo)
        self.kart_dolu = self._create_ozet_kart("📦", "Stoklu Depo", "0", s['success']); ozet_layout.addWidget(self.kart_dolu)
        self.kart_toplam = self._create_ozet_kart("📊", "Toplam Stok", "0", s['warning']); ozet_layout.addWidget(self.kart_toplam)
        self.kart_lot = self._create_ozet_kart("🏷️", "Toplam Lot", "0", s['info']); ozet_layout.addWidget(self.kart_lot)
        layout.addWidget(self.ozet_frame)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Sol - Depo kartları
        sol_widget = QWidget(); sol_layout = QVBoxLayout(sol_widget); sol_layout.setContentsMargins(0, 0, 0, 0)
        sol_title = QLabel("📍 DEPOLAR"); sol_title.setStyleSheet(f"color: {s['text']}; font-weight: bold; font-size: 14px;"); sol_layout.addWidget(sol_title)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.depo_container = QWidget(); self.depo_grid = QGridLayout(self.depo_container); self.depo_grid.setSpacing(12)
        scroll.setWidget(self.depo_container); sol_layout.addWidget(scroll, 1)
        splitter.addWidget(sol_widget)
        
        # Sağ - Stok detay
        sag_widget = QFrame(); sag_widget.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px;")
        sag_layout = QVBoxLayout(sag_widget); sag_layout.setContentsMargins(16, 16, 16, 16)
        self.detay_title = QLabel("📋 STOK DETAYI"); self.detay_title.setStyleSheet(f"color: {s['primary']}; font-weight: bold; font-size: 14px;"); sag_layout.addWidget(self.detay_title)
        search_layout = QHBoxLayout(); search_layout.addWidget(QLabel("Ara:"))
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Lot no, stok kodu...")
        self.search_input.setStyleSheet(f"QLineEdit {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; }}")
        self.search_input.textChanged.connect(self._apply_filter); search_layout.addWidget(self.search_input)
        sag_layout.addLayout(search_layout)
        
        self.stok_table = QTableWidget()
        self.stok_table.setStyleSheet(f"QTableWidget {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; color: {s['text']}; }} QTableWidget::item {{ padding: 8px; }} QTableWidget::item:selected {{ background: {s['primary']}; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 10px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; }}")
        self.stok_table.setColumnCount(7); self.stok_table.setHorizontalHeaderLabels(["Lot No", "Stok Kodu", "Stok Adı", "Miktar", "Birim", "Son Hareket", "Durum"])
        self.stok_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.stok_table.setColumnWidth(0, 120); self.stok_table.setColumnWidth(1, 100); self.stok_table.setColumnWidth(3, 80); self.stok_table.setColumnWidth(4, 60); self.stok_table.setColumnWidth(5, 100); self.stok_table.setColumnWidth(6, 100)
        self.stok_table.verticalHeader().setVisible(False); self.stok_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        sag_layout.addWidget(self.stok_table, 1)
        splitter.addWidget(sag_widget); splitter.setSizes([400, 600])
        layout.addWidget(splitter, 1)
    
    def _create_ozet_kart(self, icon: str, baslik: str, deger: str, renk: str) -> QFrame:
        s = self.s
        frame = QFrame(); frame.setStyleSheet(f"QFrame {{ background: {s['input_bg']}; border: 1px solid {renk}; border-radius: 10px; }}")
        layout = QVBoxLayout(frame); layout.setContentsMargins(16, 12, 16, 12); layout.setSpacing(6)
        header = QLabel(f"{icon} {baslik}"); header.setStyleSheet(f"color: {s['text_muted']}; font-size: 12px;"); layout.addWidget(header)
        value = QLabel(deger); value.setObjectName("value"); value.setStyleSheet(f"color: {renk}; font-size: 26px; font-weight: bold;"); layout.addWidget(value)
        return frame
    
    def _create_depo_kart(self, depo_id: int, kod: str, ad: str, miktar: float, lot_sayisi: int) -> QFrame:
        s = self.s
        border_color = s['success'] if miktar > 0 else s['border']; bg_color = '#1a2e1a' if miktar > 0 else s['input_bg']
        frame = QFrame(); frame.setObjectName(f"depo_{depo_id}")
        frame.setStyleSheet(f"QFrame#depo_{depo_id} {{ background: {bg_color}; border: 1px solid {border_color}; border-radius: 10px; }} QFrame#depo_{depo_id}:hover {{ border: 2px solid {s['primary']}; }}")
        frame.setCursor(Qt.PointingHandCursor); frame.setMinimumHeight(100)
        frame.mousePressEvent = lambda e, did=depo_id, dk=kod: self._depo_secildi(did, dk)
        layout = QVBoxLayout(frame); layout.setContentsMargins(12, 10, 12, 10); layout.setSpacing(4)
        kod_label = QLabel(kod); kod_label.setStyleSheet(f"color: {s['primary']}; font-weight: bold; font-size: 14px;"); layout.addWidget(kod_label)
        ad_label = QLabel(ad[:20] + "..." if len(ad) > 20 else ad); ad_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 11px;"); layout.addWidget(ad_label)
        miktar_label = QLabel(f"{miktar:,.0f}"); miktar_label.setStyleSheet(f"color: {s['success'] if miktar > 0 else s['text_muted']}; font-size: 18px; font-weight: bold;"); layout.addWidget(miktar_label)
        lot_label = QLabel(f"🏷️ {lot_sayisi} lot"); lot_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 10px;"); layout.addWidget(lot_label)
        return frame
    
    def _update_time(self): self.saat_label.setText(datetime.now().strftime("%H:%M:%S"))
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""SELECT d.id, d.kod, d.ad, COALESCE(SUM(sb.miktar), 0), COUNT(DISTINCT sb.lot_no)
                FROM tanim.depolar d LEFT JOIN stok.stok_bakiye sb ON d.id = sb.depo_id AND sb.miktar > 0
                WHERE d.aktif_mi = 1 AND d.kod NOT LIKE 'URT-%' AND d.kod NOT LIKE 'ZN-%' AND d.kod NOT IN ('Yi')
                GROUP BY d.id, d.kod, d.ad ORDER BY d.kod""")
            depolar = cursor.fetchall()
            toplam_depo = len(depolar); dolu_depo = sum(1 for d in depolar if d[3] > 0); toplam_stok = sum(d[3] for d in depolar); toplam_lot = sum(d[4] for d in depolar)
            self.kart_depo.findChild(QLabel, "value").setText(str(toplam_depo))
            self.kart_dolu.findChild(QLabel, "value").setText(str(dolu_depo))
            self.kart_toplam.findChild(QLabel, "value").setText(f"{toplam_stok:,.0f}")
            self.kart_lot.findChild(QLabel, "value").setText(str(toplam_lot))
            while self.depo_grid.count():
                item = self.depo_grid.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            row, col, max_col = 0, 0, 3
            for depo in depolar:
                kart = self._create_depo_kart(depo[0], depo[1], depo[2], depo[3], depo[4])
                self.depo_grid.addWidget(kart, row, col); col += 1
                if col >= max_col: col = 0; row += 1
            conn.close()
            if depolar and not self.secili_depo_id: self._depo_secildi(depolar[0][0], depolar[0][1])
            elif self.secili_depo_id: self._load_stok_detay(self.secili_depo_id)
        except Exception as e: print(f"Hata: {e}")
    
    def _depo_secildi(self, depo_id: int, depo_kod: str):
        self.secili_depo_id = depo_id; self.detay_title.setText(f"📋 STOK DETAYI - {depo_kod}"); self._load_stok_detay(depo_id)
    
    def _load_stok_detay(self, depo_id: int):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""SELECT sb.lot_no, COALESCE(sb.stok_kodu, u.urun_kodu, ''), COALESCE(sb.stok_adi, u.urun_adi, ''),
                sb.miktar, COALESCE(sb.birim, b.kod, 'AD'), sb.son_hareket_tarihi, sb.kalite_durumu
                FROM stok.stok_bakiye sb LEFT JOIN stok.urunler u ON sb.urun_id = u.id LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                WHERE sb.depo_id = ? AND sb.miktar > 0 ORDER BY sb.son_hareket_tarihi DESC""", (depo_id,))
            rows = cursor.fetchall(); conn.close(); self.stok_data = rows; self._display_stok(rows)
        except Exception as e: print(f"Hata: {e}")
    
    def _display_stok(self, rows):
        s = self.s
        self.stok_table.setRowCount(0)
        for row in rows:
            row_idx = self.stok_table.rowCount(); self.stok_table.insertRow(row_idx)
            item = QTableWidgetItem(row[0] or ''); item.setForeground(QColor(s['primary'])); self.stok_table.setItem(row_idx, 0, item)
            self.stok_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
            self.stok_table.setItem(row_idx, 2, QTableWidgetItem(row[2] or ''))
            item = QTableWidgetItem(f"{row[3]:,.0f}"); item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter); self.stok_table.setItem(row_idx, 3, item)
            self.stok_table.setItem(row_idx, 4, QTableWidgetItem(row[4] or 'AD'))
            self.stok_table.setItem(row_idx, 5, QTableWidgetItem(row[5].strftime('%d.%m.%Y') if row[5] else '-'))
            durum = row[6] or ''; item = QTableWidgetItem(durum)
            if durum in ('ONAYLANDI', 'SEVKE_HAZIR'): item.setForeground(QColor(s['success']))
            elif durum in ('BEKLIYOR', 'KALITE_BEKLIYOR', 'URETIMDE'): item.setForeground(QColor(s['warning']))
            elif 'RED' in durum.upper(): item.setForeground(QColor(s['error']))
            self.stok_table.setItem(row_idx, 6, item)
    
    def _apply_filter(self):
        search = self.search_input.text().lower().strip()
        if not search: self._display_stok(self.stok_data); return
        filtered = [r for r in self.stok_data if search in f"{r[0]} {r[1]} {r[2]}".lower()]
        self._display_stok(filtered)
