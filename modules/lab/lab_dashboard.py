# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Lab Dashboard
Laboratuvar performans dashboard'u - grafikler ve trendler
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

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


class LabDashboardPage(BasePage):
    """Lab Dashboard - Performans ve trend analizi"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
        
        # Otomatik yenileme (1 dakika)
        self.auto_refresh = QTimer()
        self.auto_refresh.timeout.connect(self._load_data)
        self.auto_refresh.start(60000)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🔬 Lab Dashboard")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; }} QPushButton:hover {{ background: #B91C1C; }}")
        refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Performans Kartları
        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)
        
        self.card_toplam = self._create_card("Toplam Analiz (30 gün)", "0", "🧪", s['info'])
        cards_layout.addWidget(self.card_toplam, 0, 0)
        
        self.card_kritik = self._create_card("Kritik Event", "0", "🔴", s['error'])
        cards_layout.addWidget(self.card_kritik, 0, 1)
        
        self.card_uyari = self._create_card("Uyarı Event", "0", "⚠️", s['warning'])
        cards_layout.addWidget(self.card_uyari, 0, 2)
        
        self.card_basari = self._create_card("Başarı Oranı", "0%", "✅", s['success'])
        cards_layout.addWidget(self.card_basari, 0, 3)
        
        layout.addLayout(cards_layout)
        
        # Ana İçerik - Yan Yana
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # Sol: Banyo Performans Tablosu
        left_frame = QFrame()
        left_frame.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; padding: 16px;")
        left_layout = QVBoxLayout(left_frame)
        
        left_title = QLabel("🏆 Banyo Performansı (Son 30 Gün)")
        left_title.setStyleSheet(f"color: {s['text']}; font-size: 16px; font-weight: 600;")
        left_layout.addWidget(left_title)
        
        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(4)
        self.performance_table.setHorizontalHeaderLabels(["Banyo", "Analiz", "Başarı %", "Kritik"])
        self.performance_table.setStyleSheet(f"""
            QTableWidget {{ 
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: none;
                gridline-color: {s['border']};
            }}
            QHeaderView::section {{ 
                background: rgba(0,0,0,0.3); 
                color: {s['text_secondary']}; 
                padding: 8px; 
                border: none;
                font-weight: 600;
            }}
        """)
        self.performance_table.verticalHeader().setVisible(False)
        self.performance_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.performance_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        left_layout.addWidget(self.performance_table)
        
        content_layout.addWidget(left_frame, 1)
        
        # Sağ: Haftalık Trend
        right_frame = QFrame()
        right_frame.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; padding: 16px;")
        right_layout = QVBoxLayout(right_frame)
        
        right_title = QLabel("📈 Haftalık Trend")
        right_title.setStyleSheet(f"color: {s['text']}; font-size: 16px; font-weight: 600;")
        right_layout.addWidget(right_title)
        
        self.trend_table = QTableWidget()
        self.trend_table.setColumnCount(4)
        self.trend_table.setHorizontalHeaderLabels(["Hafta", "Analiz", "Kritik", "Sapma"])
        self.trend_table.setStyleSheet(f"""
            QTableWidget {{ 
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: none;
                gridline-color: {s['border']};
            }}
            QHeaderView::section {{ 
                background: rgba(0,0,0,0.3); 
                color: {s['text_secondary']}; 
                padding: 8px; 
                border: none;
                font-weight: 600;
            }}
        """)
        self.trend_table.verticalHeader().setVisible(False)
        self.trend_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.trend_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.trend_table)
        
        content_layout.addWidget(right_frame, 1)
        
        layout.addLayout(content_layout, 1)
    
    def _create_card(self, title: str, value: str, icon: str, color: str) -> QFrame:
        """Performans kartı oluştur"""
        s = self.s
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 12px;
                border-left: 4px solid {color};
                padding: 16px;
            }}
        """)
        card.setMinimumSize(200, 100)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 12px;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold;")
        layout.addWidget(value_label)
        
        return card
    
    def _load_data(self):
        """Dashboard verilerini yükle"""
        s = self.s
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # KPI'lar - Son 30 gün
            cursor.execute("""
                SELECT 
                    COUNT(*) AS toplam,
                    SUM(CASE WHEN event_tipi = 'LAB_ANALIZ_KRITIK' THEN 1 ELSE 0 END) AS kritik,
                    SUM(CASE WHEN event_tipi = 'LAB_ANALIZ_UYARI' THEN 1 ELSE 0 END) AS uyari,
                    SUM(CASE WHEN event_tipi = 'LAB_ANALIZ_NORMAL' THEN 1 ELSE 0 END) AS normal
                FROM uretim.lab_event_log
                WHERE event_zamani >= DATEADD(DAY, -30, GETDATE())
            """)
            kpi = cursor.fetchone()
            
            if kpi:
                toplam = kpi[0] or 0
                kritik = kpi[1] or 0
                uyari = kpi[2] or 0
                normal = kpi[3] or 0
                
                basari_oran = (normal / toplam * 100) if toplam > 0 else 0
                
                self.card_toplam.findChild(QLabel, "value_label").setText(str(toplam))
                self.card_kritik.findChild(QLabel, "value_label").setText(str(kritik))
                self.card_uyari.findChild(QLabel, "value_label").setText(str(uyari))
                self.card_basari.findChild(QLabel, "value_label").setText(f"{basari_oran:.1f}%")
            
            # Banyo Performansı
            cursor.execute("""
                SELECT 
                    b.kod + ' - ' + b.ad AS banyo,
                    p.toplam_analiz,
                    p.basari_yuzdesi,
                    p.kritik_adet
                FROM uretim.vw_lab_banyo_performans p
                JOIN uretim.banyo_tanimlari b ON p.banyo_id = b.id
                ORDER BY p.basari_yuzdesi DESC
            """)
            perf_rows = cursor.fetchall()
            
            self.performance_table.setRowCount(len(perf_rows))
            for i, row in enumerate(perf_rows):
                self.performance_table.setItem(i, 0, QTableWidgetItem(row[0]))
                self.performance_table.setItem(i, 1, QTableWidgetItem(str(row[1] or 0)))
                
                basari_item = QTableWidgetItem(f"{row[2]:.1f}%" if row[2] else "0%")
                if row[2] and row[2] >= 90:
                    basari_item.setForeground(QColor(s['success']))
                elif row[2] and row[2] >= 70:
                    basari_item.setForeground(QColor(s['warning']))
                else:
                    basari_item.setForeground(QColor(s['error']))
                self.performance_table.setItem(i, 2, basari_item)
                
                kritik_item = QTableWidgetItem(str(row[3] or 0))
                if row[3] and row[3] > 5:
                    kritik_item.setForeground(QColor(s['error']))
                self.performance_table.setItem(i, 3, kritik_item)
            
            # Haftalık Trend
            cursor.execute("""
                SELECT TOP 8
                    'Hafta ' + CAST(hafta AS NVARCHAR) AS hafta_text,
                    toplam_analiz,
                    kritik_sayisi,
                    CAST(sicaklik_sapma AS DECIMAL(5,2)) AS sapma
                FROM uretim.vw_lab_haftalik_trend
                WHERE yil = YEAR(GETDATE())
                ORDER BY yil DESC, hafta DESC
            """)
            trend_rows = cursor.fetchall()
            
            self.trend_table.setRowCount(len(trend_rows))
            for i, row in enumerate(trend_rows):
                self.trend_table.setItem(i, 0, QTableWidgetItem(row[0]))
                self.trend_table.setItem(i, 1, QTableWidgetItem(str(row[1] or 0)))
                
                kritik_item = QTableWidgetItem(str(row[2] or 0))
                if row[2] and row[2] > 0:
                    kritik_item.setForeground(QColor(s['error']))
                self.trend_table.setItem(i, 2, kritik_item)
                
                sapma_text = f"{row[3]:.2f}" if row[3] else "-"
                self.trend_table.setItem(i, 3, QTableWidgetItem(sapma_text))
            
            conn.close()
            
        except Exception as e:
            print(f"Dashboard yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
