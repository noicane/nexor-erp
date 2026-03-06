# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Lab Event Log
Laboratuvar analiz event'lerini listeler ve yönetir
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QTimer, QDate
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


class LabEventLogPage(BasePage):
    """Lab Event Log - Laboratuvar olayları takip ekranı"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
        
        # Otomatik yenileme (30 saniye)
        self.auto_refresh = QTimer()
        self.auto_refresh.timeout.connect(self._load_data)
        self.auto_refresh.start(30000)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; padding: 16px;")
        header_layout = QHBoxLayout(header_frame)
        
        # Başlık
        title_layout = QVBoxLayout()
        title_row = QHBoxLayout()
        icon = QLabel("🔬")
        icon.setStyleSheet("font-size: 24px;")
        title_row.addWidget(icon)
        
        title = QLabel("Lab Event Log")
        title.setStyleSheet(f"color: {s['text']}; font-size: 20px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_layout.addLayout(title_row)
        
        subtitle = QLabel("Laboratuvar analiz olayları ve uyarılar")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 12px;")
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # İstatistikler
        self.stat_widgets = {}
        for key, emoji, color in [
            ('toplam', '📊', s['info']),
            ('bekleyen', '⏳', s['warning']),
            ('kritik', '🔴', s['error'])
        ]:
            stat_frame = QFrame()
            stat_layout = QHBoxLayout(stat_frame)
            stat_layout.setContentsMargins(12, 8, 12, 8)
            stat_layout.setSpacing(6)
            
            emoji_lbl = QLabel(emoji)
            emoji_lbl.setStyleSheet("font-size: 16px;")
            stat_layout.addWidget(emoji_lbl)
            
            val_lbl = QLabel("0")
            val_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 600;")
            self.stat_widgets[key] = val_lbl
            stat_layout.addWidget(val_lbl)
            
            header_layout.addWidget(stat_frame)
        
        refresh_btn = QPushButton("Yenile")
        refresh_btn.setFixedSize(60, 32)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 6px; font-size: 12px; }} QPushButton:hover {{ background: {s['border']}; }}")
        refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header_frame)
        
        # Filtreler
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; padding: 12px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(12)
        
        input_style = f"background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 6px; padding: 8px; font-size: 12px;"
        
        # Banyo
        filter_layout.addWidget(QLabel("Banyo:", styleSheet=f"color: {s['text']}; font-size: 12px;"))
        self.banyo_combo = QComboBox()
        self.banyo_combo.setFixedWidth(180)
        self.banyo_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.banyo_combo.addItem("Tümü", None)
        self._load_banyo_filter()
        self.banyo_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.banyo_combo)
        
        # Event Tipi
        filter_layout.addWidget(QLabel("Tip:", styleSheet=f"color: {s['text']}; font-size: 12px;"))
        self.event_combo = QComboBox()
        self.event_combo.setFixedWidth(150)
        self.event_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.event_combo.addItem("Tümü", None)
        self.event_combo.addItem("⚠️ Uyarı", "LAB_ANALIZ_UYARI")
        self.event_combo.addItem("🔴 Kritik", "LAB_ANALIZ_KRITIK")
        self.event_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.event_combo)
        
        # Durum
        filter_layout.addWidget(QLabel("Durum:", styleSheet=f"color: {s['text']}; font-size: 12px;"))
        self.durum_combo = QComboBox()
        self.durum_combo.setFixedWidth(120)
        self.durum_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.durum_combo.addItem("Tümü", None)
        self.durum_combo.addItem("⏳ Bekleyen", "BEKLIYOR")
        self.durum_combo.addItem("✅ Okundu", "OKUNDU")
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.durum_combo)
        
        # Tarih
        filter_layout.addWidget(QLabel("Tarih:", styleSheet=f"color: {s['text']}; font-size: 12px;"))
        
        self.tarih_bas = QDateEdit()
        self.tarih_bas.setDate(QDate.currentDate().addDays(-7))
        self.tarih_bas.setCalendarPopup(True)
        self.tarih_bas.setFixedWidth(110)
        self.tarih_bas.setStyleSheet(f"QDateEdit {{ {input_style} }}")
        filter_layout.addWidget(self.tarih_bas)
        
        filter_layout.addWidget(QLabel("-", styleSheet=f"color: {s['text_muted']};"))
        
        self.tarih_bit = QDateEdit()
        self.tarih_bit.setDate(QDate.currentDate())
        self.tarih_bit.setCalendarPopup(True)
        self.tarih_bit.setFixedWidth(110)
        self.tarih_bit.setStyleSheet(f"QDateEdit {{ {input_style} }}")
        filter_layout.addWidget(self.tarih_bit)
        
        ara_btn = QPushButton("🔍 Ara")
        ara_btn.setCursor(Qt.PointingHandCursor)
        ara_btn.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; }} QPushButton:hover {{ background: #B91C1C; }}")
        ara_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(ara_btn)
        
        filter_layout.addStretch()
        layout.addWidget(filter_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Banyo", "Event", "Sıcaklık", "pH", "Analist", "Zaman", "Durum", "İşlem"
        ])
        
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 140)
        self.table.setColumnWidth(7, 100)
        self.table.setColumnWidth(8, 100)
        
        self.table.setStyleSheet(f"""
            QTableWidget {{ 
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: 1px solid {s['border']}; 
                border-radius: 10px;
                gridline-color: {s['border']};
                font-size: 12px;
            }}
            QTableWidget::item {{ 
                padding: 8px; 
                border-bottom: 1px solid {s['border']};
            }}
            QTableWidget::item:selected {{ 
                background: {s['primary']}; 
            }}
            QHeaderView::section {{ 
                background: rgba(0,0,0,0.3); 
                color: {s['text_secondary']}; 
                padding: 10px 8px; 
                border: none; 
                border-bottom: 2px solid {s['primary']};
                font-weight: 600;
                font-size: 11px;
            }}
        """)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
        # Footer
        footer_frame = QFrame()
        footer_frame.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; padding: 12px;")
        footer_layout = QHBoxLayout(footer_frame)
        
        self.footer_label = QLabel("Yükleniyor...")
        self.footer_label.setStyleSheet(f"color: {s['text_secondary']}; font-size: 12px;")
        footer_layout.addWidget(self.footer_label)
        
        footer_layout.addStretch()
        layout.addWidget(footer_frame)
    
    def _load_banyo_filter(self):
        """Banyo filtresi yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad 
                FROM uretim.banyo_tanimlari 
                WHERE aktif_mi = 1 
                ORDER BY kod
            """)
            for row in cursor.fetchall():
                self.banyo_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception as e:
            print(f"Banyo filtresi yükleme hatası: {e}")
    
    def _load_data(self):
        """Event log verilerini yükle"""
        s = self.s
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Filtreler
            banyo_id = self.banyo_combo.currentData()
            event_tipi = self.event_combo.currentData()
            durum = self.durum_combo.currentData()
            tarih_bas = self.tarih_bas.date().toPython()
            tarih_bit = self.tarih_bit.date().toPython()
            
            # Ana sorgu
            query = """
                SELECT 
                    e.id,
                    b.kod + ' - ' + b.ad AS banyo,
                    e.event_tipi,
                    e.sicaklik,
                    e.ph,
                    p.ad + ' ' + p.soyad AS analist,
                    e.event_zamani,
                    e.event_durumu,
                    e.banyo_id
                FROM uretim.lab_event_log e
                LEFT JOIN uretim.banyo_tanimlari b ON e.banyo_id = b.id
                LEFT JOIN ik.personeller p ON e.analist_id = p.id
                WHERE e.event_zamani >= ? AND e.event_zamani < DATEADD(DAY, 1, ?)
            """
            params = [tarih_bas, tarih_bit]
            
            if banyo_id:
                query += " AND e.banyo_id = ?"
                params.append(banyo_id)
            
            if event_tipi:
                query += " AND e.event_tipi = ?"
                params.append(event_tipi)
            
            if durum:
                query += " AND e.event_durumu = ?"
                params.append(durum)
            
            query += " ORDER BY e.event_zamani DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # İstatistikler
            cursor.execute("""
                SELECT 
                    COUNT(*) AS toplam,
                    SUM(CASE WHEN event_durumu = 'BEKLIYOR' THEN 1 ELSE 0 END) AS bekleyen,
                    SUM(CASE WHEN event_tipi = 'LAB_ANALIZ_KRITIK' THEN 1 ELSE 0 END) AS kritik
                FROM uretim.lab_event_log
                WHERE event_zamani >= ? AND event_zamani < DATEADD(DAY, 1, ?)
            """, (tarih_bas, tarih_bit))
            stats = cursor.fetchone()
            
            conn.close()
            
            # İstatistikleri güncelle
            if stats:
                self.stat_widgets['toplam'].setText(str(stats[0] or 0))
                self.stat_widgets['bekleyen'].setText(str(stats[1] or 0))
                self.stat_widgets['kritik'].setText(str(stats[2] or 0))
            
            # Tabloyu doldur
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # ID
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                
                # Banyo
                banyo_item = QTableWidgetItem(row[1] or '')
                self.table.setItem(i, 1, banyo_item)
                
                # Event Tipi
                event_text = row[2] or ''
                event_item = QTableWidgetItem(event_text.replace('LAB_ANALIZ_', ''))
                if 'KRITIK' in event_text:
                    event_item.setForeground(QColor(s['error']))
                elif 'UYARI' in event_text:
                    event_item.setForeground(QColor(s['warning']))
                self.table.setItem(i, 2, event_item)
                
                # Sıcaklık
                sic_item = QTableWidgetItem(f"{row[3]:.1f}°C" if row[3] else "-")
                self.table.setItem(i, 3, sic_item)
                
                # pH
                ph_item = QTableWidgetItem(f"{row[4]:.2f}" if row[4] else "-")
                self.table.setItem(i, 4, ph_item)
                
                # Analist
                analist_item = QTableWidgetItem(row[5] or "-")
                self.table.setItem(i, 5, analist_item)
                
                # Zaman
                zaman_str = row[6].strftime('%d.%m.%Y %H:%M') if row[6] else ''
                self.table.setItem(i, 6, QTableWidgetItem(zaman_str))
                
                # Durum
                durum_text = row[7] or ''
                durum_item = QTableWidgetItem(durum_text)
                if durum_text == 'BEKLIYOR':
                    durum_item.setForeground(QColor(s['warning']))
                    durum_item.setText("⏳ Bekliyor")
                elif durum_text == 'OKUNDU':
                    durum_item.setForeground(QColor(s['success']))
                    durum_item.setText("✅ Okundu")
                self.table.setItem(i, 7, durum_item)
                
                # İşlem butonu
                if durum_text == 'BEKLIYOR':
                    btn = QPushButton("✓ Okundu")
                    btn.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 4px; padding: 4px 8px; }} QPushButton:hover {{ background: #059669; }}")
                    btn.clicked.connect(lambda _, eid=row[0]: self._mark_read(eid))
                    self.table.setCellWidget(i, 8, btn)
            
            # Footer güncelle
            self.footer_label.setText(f"Toplam {len(rows)} kayıt | Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yükleme hatası:\n{str(e)}")
            print(f"Lab event log yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _mark_read(self, event_id: int):
        """Event'i okundu olarak işaretle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE uretim.lab_event_log
                SET event_durumu = 'OKUNDU',
                    okundu_mu = 1,
                    okunma_zamani = GETDATE()
                WHERE id = ?
            """, (event_id,))
            conn.commit()
            conn.close()
            
            self._load_data()  # Yenile
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İşaretleme hatası:\n{str(e)}")
