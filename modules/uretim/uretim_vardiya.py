# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Vardiya Raporu Sayfası
[MODERNIZED UI - v3.0]

Vardiya bazlı üretim kayıtlarını gösterir
"""
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QDateEdit,
    QGridLayout, QWidget, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection


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


class UretimVardiyaPage(BasePage):
    """Vardiya Raporu Sayfası"""
    
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
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(10)
        
        # Header - Kompakt tek satır
        header_frame = QFrame()
        header_frame.setFixedHeight(50)
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 0, 12, 0)
        header_layout.setSpacing(10)
        
        # Başlık
        title = QLabel("🏭 Vardiya Raporu")
        title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {s['text']};")
        header_layout.addWidget(title)
        
        header_layout.addWidget(QLabel("Tarih:", styleSheet=f"color: {s['text_muted']}; font-size: 11px;"))
        
        self.tarih_baslangic = QDateEdit()
        self.tarih_baslangic.setDate(QDate.currentDate().addDays(-7))
        self.tarih_baslangic.setCalendarPopup(True)
        self.tarih_baslangic.setStyleSheet(self._input_style())
        self.tarih_baslangic.setFixedWidth(100)
        self.tarih_baslangic.setFixedHeight(28)
        self.tarih_baslangic.dateChanged.connect(self._load_data)
        header_layout.addWidget(self.tarih_baslangic)
        
        header_layout.addWidget(QLabel("-", styleSheet=f"color: {s['text_muted']};"))
        
        self.tarih_bitis = QDateEdit()
        self.tarih_bitis.setDate(QDate.currentDate())
        self.tarih_bitis.setCalendarPopup(True)
        self.tarih_bitis.setStyleSheet(self._input_style())
        self.tarih_bitis.setFixedWidth(100)
        self.tarih_bitis.setFixedHeight(28)
        self.tarih_bitis.dateChanged.connect(self._load_data)
        header_layout.addWidget(self.tarih_bitis)
        
        header_layout.addWidget(QLabel("Vardiya:", styleSheet=f"color: {s['text_muted']}; font-size: 11px;"))
        self.vardiya_combo = QComboBox()
        self.vardiya_combo.setStyleSheet(self._input_style())
        self.vardiya_combo.setFixedWidth(100)
        self.vardiya_combo.setFixedHeight(28)
        self.vardiya_combo.currentIndexChanged.connect(self._load_data)
        header_layout.addWidget(self.vardiya_combo)
        
        header_layout.addWidget(QLabel("Operatör:", styleSheet=f"color: {s['text_muted']}; font-size: 11px;"))
        self.operator_combo = QComboBox()
        self.operator_combo.setStyleSheet(self._input_style())
        self.operator_combo.setFixedWidth(120)
        self.operator_combo.setFixedHeight(28)
        self.operator_combo.currentIndexChanged.connect(self._load_data)
        header_layout.addWidget(self.operator_combo)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setFixedHeight(28)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 4px;
                padding: 0 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background: {s['border']}; }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header_frame)
        
        # Özet kartları - Kompakt tek satır
        ozet_layout = QHBoxLayout()
        ozet_layout.setSpacing(10)
        
        self.kart_toplam = self._create_ozet_kart("📊", "Toplam Kayıt", "0", s['primary'])
        self.kart_adet = self._create_ozet_kart("📦", "Toplam Üretim", "0 adet", s['success'])
        self.kart_sure = self._create_ozet_kart("⏱️", "Ortalama Süre", "0 dk", s['warning'])
        self.kart_vardiya = self._create_ozet_kart("🏭", "Aktif Vardiya", "-", s['info'])
        
        ozet_layout.addWidget(self.kart_toplam)
        ozet_layout.addWidget(self.kart_adet)
        ozet_layout.addWidget(self.kart_sure)
        ozet_layout.addWidget(self.kart_vardiya)
        
        layout.addLayout(ozet_layout)
        
        # TabWidget - İki sekme: Vardiya Detay ve Trend Raporu
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {s['border']};
                border-radius: 8px;
                background: {s['card_bg']};
                top: -1px;
            }}
            QTabBar::tab {{
                background: {s['input_bg']};
                color: {s['text_muted']};
                border: 1px solid {s['border']};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
                font-size: 12px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {s['card_bg']};
                color: {s['primary']};
                border-bottom: 2px solid {s['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {s['border']};
            }}
        """)
        
        # SEKME 1: Vardiya Detay (mevcut splitter)
        detay_tab = QWidget()
        detay_layout = QVBoxLayout(detay_tab)
        detay_layout.setContentsMargins(10, 10, 10, 10)
        detay_layout.setSpacing(8)
        
        # Splitter - Sol: Vardiya özeti, Sağ: Detay tablo
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {s['border']}; width: 2px; }}")
        
        # SOL - Vardiya özet tablosu
        sol_widget = QWidget()
        sol_layout = QVBoxLayout(sol_widget)
        sol_layout.setContentsMargins(0, 0, 0, 0)
        sol_layout.setSpacing(4)
        
        sol_title = QLabel("📈 VARDIYA ÖZETİ")
        sol_title.setStyleSheet(f"color: {s['primary']}; font-weight: 600; font-size: 12px; padding: 4px;")
        sol_layout.addWidget(sol_title)
        
        self.ozet_table = QTableWidget()
        self.ozet_table.setStyleSheet(self._table_style())
        self.ozet_table.setColumnCount(4)
        self.ozet_table.setHorizontalHeaderLabels(["Vardiya", "Kayıt", "Üretim", "Ort. Süre"])
        self.ozet_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ozet_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.ozet_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.ozet_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.ozet_table.verticalHeader().setVisible(False)
        self.ozet_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ozet_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ozet_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        sol_layout.addWidget(self.ozet_table)
        
        splitter.addWidget(sol_widget)
        
        # SAĞ - Detay tablo
        sag_widget = QWidget()
        sag_layout = QVBoxLayout(sag_widget)
        sag_layout.setContentsMargins(0, 0, 0, 0)
        sag_layout.setSpacing(4)
        
        sag_title = QLabel("📋 DETAYLI KAYITLAR")
        sag_title.setStyleSheet(f"color: {s['primary']}; font-weight: 600; font-size: 12px; padding: 4px;")
        sag_layout.addWidget(sag_title)
        
        self.detay_table = QTableWidget()
        self.detay_table.setStyleSheet(self._table_style())
        self.detay_table.setColumnCount(9)
        self.detay_table.setHorizontalHeaderLabels([
            "Tarih", "Vardiya", "Operatör", "İş Emri", 
            "Ürün", "Üretilen", "Kalite", "Süre (dk)", "Not"
        ])
        
        self.detay_table.setColumnWidth(0, 80)
        self.detay_table.setColumnWidth(1, 70)
        self.detay_table.setColumnWidth(2, 90)
        self.detay_table.setColumnWidth(3, 100)
        self.detay_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.detay_table.setColumnWidth(5, 65)
        self.detay_table.setColumnWidth(6, 55)
        self.detay_table.setColumnWidth(7, 65)
        self.detay_table.setColumnWidth(8, 70)
        
        self.detay_table.verticalHeader().setVisible(False)
        self.detay_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.detay_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.detay_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        sag_layout.addWidget(self.detay_table)
        
        splitter.addWidget(sag_widget)
        splitter.setSizes([250, 750])
        
        detay_layout.addWidget(splitter)
        self.tab_widget.addTab(detay_tab, "📊 Vardiya Detay")
        
        # SEKME 2: Trend Raporu
        self._setup_trend_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Combolar yükle
        self._load_combos()
    
    def _setup_trend_tab(self):
        """Trend raporu sekmesini oluştur"""
        s = self.s
        
        trend_tab = QWidget()
        trend_layout = QVBoxLayout(trend_tab)
        trend_layout.setContentsMargins(10, 10, 10, 10)
        trend_layout.setSpacing(10)
        
        # Üst filtre paneli
        filter_frame = QFrame()
        filter_frame.setFixedHeight(50)
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 0, 12, 0)
        filter_layout.setSpacing(12)
        
        filter_layout.addWidget(QLabel("📅 Tarih Aralığı:", styleSheet=f"color: {s['text']}; font-weight: 600; font-size: 11px;"))
        
        self.trend_baslangic = QDateEdit()
        self.trend_baslangic.setDate(QDate.currentDate().addDays(-7))
        self.trend_baslangic.setCalendarPopup(True)
        self.trend_baslangic.setStyleSheet(self._input_style())
        self.trend_baslangic.setFixedWidth(110)
        self.trend_baslangic.setFixedHeight(32)
        self.trend_baslangic.dateChanged.connect(self._load_trend_data)
        filter_layout.addWidget(self.trend_baslangic)
        
        filter_layout.addWidget(QLabel("-", styleSheet=f"color: {s['text_muted']};"))
        
        self.trend_bitis = QDateEdit()
        self.trend_bitis.setDate(QDate.currentDate())
        self.trend_bitis.setCalendarPopup(True)
        self.trend_bitis.setStyleSheet(self._input_style())
        self.trend_bitis.setFixedWidth(110)
        self.trend_bitis.setFixedHeight(32)
        self.trend_bitis.dateChanged.connect(self._load_trend_data)
        filter_layout.addWidget(self.trend_bitis)
        
        filter_layout.addWidget(QLabel("Hat:", styleSheet=f"color: {s['text']}; font-weight: 600; font-size: 11px;"))
        self.trend_hat_combo = QComboBox()
        self.trend_hat_combo.setStyleSheet(self._input_style())
        self.trend_hat_combo.setFixedWidth(100)
        self.trend_hat_combo.setFixedHeight(32)
        self.trend_hat_combo.addItems(["TÜM HATLAR", "KTL", "CINKO", "DIGER"])
        self.trend_hat_combo.currentIndexChanged.connect(self._load_trend_data)
        filter_layout.addWidget(self.trend_hat_combo)
        
        filter_layout.addStretch()
        
        trend_refresh_btn = QPushButton("🔄 Yenile")
        trend_refresh_btn.setCursor(Qt.PointingHandCursor)
        trend_refresh_btn.setFixedHeight(32)
        trend_refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #B91C1C; }}
        """)
        trend_refresh_btn.clicked.connect(self._load_trend_data)
        filter_layout.addWidget(trend_refresh_btn)
        
        trend_layout.addWidget(filter_frame)
        
        # Özet istatistikler - 4 kart
        ozet_frame = QFrame()
        ozet_frame.setStyleSheet(f"background: transparent; border: none;")
        ozet_stat_layout = QHBoxLayout(ozet_frame)
        ozet_stat_layout.setSpacing(10)
        
        self.trend_kart_toplam = self._create_trend_kart("📦", "Toplam Üretim", "0", s['primary'])
        self.trend_kart_ortalama = self._create_trend_kart("📊", "Günlük Ortalama", "0", s['success'])
        self.trend_kart_maks = self._create_trend_kart("⬆️", "En Yüksek Gün", "0", s['warning'])
        self.trend_kart_min = self._create_trend_kart("⬇️", "En Düşük Gün", "0", s['info'])
        
        ozet_stat_layout.addWidget(self.trend_kart_toplam)
        ozet_stat_layout.addWidget(self.trend_kart_ortalama)
        ozet_stat_layout.addWidget(self.trend_kart_maks)
        ozet_stat_layout.addWidget(self.trend_kart_min)
        
        trend_layout.addWidget(ozet_frame)
        
        # Günlük Trend Tablosu
        tablo_title = QLabel("📈 GÜNLÜK ÜRETİM TRENDİ")
        tablo_title.setStyleSheet(f"color: {s['primary']}; font-weight: 700; font-size: 13px; padding: 6px 0;")
        trend_layout.addWidget(tablo_title)
        
        self.trend_table = QTableWidget()
        self.trend_table.setStyleSheet(self._table_style())
        self.trend_table.setColumnCount(10)
        self.trend_table.setHorizontalHeaderLabels([
            "Tarih", "Gün", "Toplam Üretim", "KTL", "CINKO", 
            "Diğer", "Ortalama Sıcaklık", "Ort. Akım", "Ort. Voltaj", "Kayıt Sayısı"
        ])
        
        # Kolon genişlikleri
        self.trend_table.setColumnWidth(0, 90)
        self.trend_table.setColumnWidth(1, 80)
        self.trend_table.setColumnWidth(2, 110)
        self.trend_table.setColumnWidth(3, 90)
        self.trend_table.setColumnWidth(4, 90)
        self.trend_table.setColumnWidth(5, 90)
        self.trend_table.setColumnWidth(6, 130)
        self.trend_table.setColumnWidth(7, 90)
        self.trend_table.setColumnWidth(8, 90)
        self.trend_table.setColumnWidth(9, 100)
        
        self.trend_table.verticalHeader().setVisible(False)
        self.trend_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.trend_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.trend_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.trend_table.setAlternatingRowColors(True)
        
        trend_layout.addWidget(self.trend_table, 1)
        
        self.tab_widget.addTab(trend_tab, "📈 Trend Raporu")
        
        # İlk yükleme
        QTimer.singleShot(200, self._load_trend_data)
    
    def _create_trend_kart(self, icon: str, title: str, value: str, color: str) -> QFrame:
        """Trend için kompakt özet kartı oluştur"""
        s = self.s
        frame = QFrame()
        frame.setFixedHeight(65)
        frame.setStyleSheet(f"""
            QFrame {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-left: 4px solid {color};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Başlık satırı
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 16px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 10px; font-weight: 500;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Değer
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 700;")
        layout.addWidget(value_label)
        
        return frame
    
    def _load_trend_data(self):
        """Trend verilerini PLC'den yükle"""
        try:
            # Tarihleri datetime.date formatına çevir
            baslangic_date = self.trend_baslangic.date().toPython()
            bitis_date = self.trend_bitis.date().toPython()
            
            # SQL Server için string formatına çevir
            baslangic = baslangic_date.strftime('%Y-%m-%d')
            bitis = bitis_date.strftime('%Y-%m-%d')
            
            hat_filtre = self.trend_hat_combo.currentText()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Hat filtresi
            hat_where = ""
            if hat_filtre != "TÜM HATLAR":
                hat_where = f"AND hat_kodu = '{hat_filtre}'"
            
            # Debug bilgisi
            print(f"[TREND DEBUG] Başlangıç: {baslangic} ({type(baslangic)})")
            print(f"[TREND DEBUG] Bitiş: {bitis} ({type(bitis)})")
            print(f"[TREND DEBUG] Hat Filtre: {hat_filtre}")
            
            # Günlük trend sorgusu - plc_tarihce tablosundan
            query = f"""
                SELECT 
                    CAST(tarih_doldurma AS DATE) AS gun,
                    COUNT(*) AS kayit_sayisi,
                    SUM(ISNULL(miktar, 0)) AS toplam_uretim,
                    SUM(CASE WHEN hat_kodu = 'KTL' THEN ISNULL(miktar, 0) ELSE 0 END) AS ktl_uretim,
                    SUM(CASE WHEN hat_kodu = 'CINKO' THEN ISNULL(miktar, 0) ELSE 0 END) AS cinko_uretim,
                    SUM(CASE WHEN hat_kodu = 'DIGER' THEN ISNULL(miktar, 0) ELSE 0 END) AS diger_uretim,
                    AVG(CASE WHEN sicaklik BETWEEN 0 AND 500 THEN sicaklik ELSE NULL END) AS ort_sicaklik,
                    AVG(CASE WHEN akim BETWEEN 0 AND 9999 THEN akim ELSE NULL END) AS ort_akim,
                    AVG(CASE WHEN voltaj BETWEEN 0 AND 9999 THEN voltaj ELSE NULL END) AS ort_voltaj
                FROM uretim.plc_tarihce
                WHERE CAST(tarih_doldurma AS DATE) >= '{baslangic}' 
                  AND CAST(tarih_doldurma AS DATE) <= '{bitis}'
                {hat_where}
                GROUP BY CAST(tarih_doldurma AS DATE)
                ORDER BY gun DESC
            """
            
            print(f"[TREND DEBUG] SQL:\n{query}")
            
            cursor.execute(query)
            
            rows = cursor.fetchall()
            
            print(f"[TREND DEBUG] Bulunan kayıt sayısı: {len(rows)}")
            if rows:
                print(f"[TREND DEBUG] İlk 3 kayıt: {rows[:3]}")
            
            conn.close()
            
            # İstatistikler hesapla
            if rows:
                toplam_uretim = sum(r[2] or 0 for r in rows)
                ortalama_uretim = toplam_uretim / len(rows) if rows else 0
                maks_gun = max(rows, key=lambda x: x[2] or 0)
                min_gun = min(rows, key=lambda x: x[2] or 0)
                
                self.trend_kart_toplam.findChild(QLabel, "value").setText(f"{toplam_uretim:,.0f}")
                self.trend_kart_ortalama.findChild(QLabel, "value").setText(f"{ortalama_uretim:,.0f}")
                self.trend_kart_maks.findChild(QLabel, "value").setText(
                    f"{maks_gun[2]:,.0f}" if maks_gun[2] else "0"
                )
                self.trend_kart_min.findChild(QLabel, "value").setText(
                    f"{min_gun[2]:,.0f}" if min_gun[2] else "0"
                )
            else:
                self.trend_kart_toplam.findChild(QLabel, "value").setText("0")
                self.trend_kart_ortalama.findChild(QLabel, "value").setText("0")
                self.trend_kart_maks.findChild(QLabel, "value").setText("0")
                self.trend_kart_min.findChild(QLabel, "value").setText("0")
            
            # Tabloyu doldur
            self.trend_table.setRowCount(len(rows))
            
            gun_isimleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
            
            for i, row in enumerate(rows):
                gun_tarih, kayit, toplam, ktl, cinko, diger, sicak, akim, voltaj = row
                
                # Tarih
                tarih_str = gun_tarih.strftime('%d.%m.%Y') if gun_tarih else "-"
                self.trend_table.setItem(i, 0, QTableWidgetItem(tarih_str))
                
                # Gün adı
                gun_adi = gun_isimleri[gun_tarih.weekday()] if gun_tarih else "-"
                gun_item = QTableWidgetItem(gun_adi)
                if gun_tarih and gun_tarih.weekday() >= 5:  # Cumartesi/Pazar
                    gun_item.setForeground(QColor(self.s['warning']))
                self.trend_table.setItem(i, 1, gun_item)
                
                # Toplam üretim
                toplam_item = QTableWidgetItem(f"{toplam:,.0f}" if toplam else "0")
                toplam_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                font = QFont()
                font.setBold(True)
                toplam_item.setFont(font)
                toplam_item.setForeground(QColor(self.s['primary']))
                self.trend_table.setItem(i, 2, toplam_item)
                
                # KTL
                ktl_item = QTableWidgetItem(f"{ktl:,.0f}" if ktl else "0")
                ktl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.trend_table.setItem(i, 3, ktl_item)
                
                # CINKO
                cinko_item = QTableWidgetItem(f"{cinko:,.0f}" if cinko else "0")
                cinko_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.trend_table.setItem(i, 4, cinko_item)
                
                # Diğer
                diger_item = QTableWidgetItem(f"{diger:,.0f}" if diger else "0")
                diger_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.trend_table.setItem(i, 5, diger_item)
                
                # Ortalama Sıcaklık
                sicak_str = f"{sicak:.1f} °C" if sicak else "-"
                sicak_item = QTableWidgetItem(sicak_str)
                sicak_item.setTextAlignment(Qt.AlignCenter)
                if sicak and sicak > 100:
                    sicak_item.setForeground(QColor(self.s['error']))
                self.trend_table.setItem(i, 6, sicak_item)
                
                # Ortalama Akım
                akim_str = f"{akim:.1f} A" if akim else "-"
                akim_item = QTableWidgetItem(akim_str)
                akim_item.setTextAlignment(Qt.AlignCenter)
                self.trend_table.setItem(i, 7, akim_item)
                
                # Ortalama Voltaj
                voltaj_str = f"{voltaj:.1f} V" if voltaj else "-"
                voltaj_item = QTableWidgetItem(voltaj_str)
                voltaj_item.setTextAlignment(Qt.AlignCenter)
                self.trend_table.setItem(i, 8, voltaj_item)
                
                # Kayıt sayısı
                kayit_item = QTableWidgetItem(str(kayit))
                kayit_item.setTextAlignment(Qt.AlignCenter)
                kayit_item.setForeground(QColor(self.s['text_muted']))
                self.trend_table.setItem(i, 9, kayit_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Trend verisi yükleme hatası: {str(e)}")
            import traceback
            traceback.print_exc()
    
    
    def _create_ozet_kart(self, icon: str, title: str, value: str, color: str) -> QFrame:
        """Özet kartı oluştur - Kompakt versiyon"""
        s = self.s
        frame = QFrame()
        frame.setFixedHeight(55)
        frame.setStyleSheet(f"""
            QFrame {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-left: 3px solid {color};
                border-radius: 6px;
            }}
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_label)
        
        # Text container
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 10px;")
        text_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 600;")
        text_layout.addWidget(value_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        return frame
    
    def _load_combos(self):
        """Combo boxları doldur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Vardiya combo
            self.vardiya_combo.clear()
            self.vardiya_combo.addItem("Tümü", None)
            cursor.execute("SELECT id, ad FROM tanim.vardiyalar WHERE aktif_mi=1 ORDER BY id")
            for row in cursor.fetchall():
                self.vardiya_combo.addItem(row[1], row[0])
            
            # Operatör combo
            self.operator_combo.clear()
            self.operator_combo.addItem("Tümü", None)
            cursor.execute("""
                SELECT DISTINCT p.id, p.ad + ' ' + p.soyad AS ad_soyad
                FROM ik.personeller p
                JOIN uretim.uretim_kayitlari uk ON p.id = uk.operator_id
                WHERE p.aktif_mi = 1
                ORDER BY ad_soyad
            """)
            for row in cursor.fetchall():
                self.operator_combo.addItem(row[1], row[0])
            
            conn.close()
        except Exception as e:
            print(f"Combo yükleme hatası: {e}")
    
    def _load_data(self):
        """Verileri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Filtre parametreleri
            tarih_baslangic = self.tarih_baslangic.date().toPython()
            tarih_bitis = self.tarih_bitis.date().toPython()
            vardiya_id = self.vardiya_combo.currentData()
            operator_id = self.operator_combo.currentData()
            
            # SQL koşulları
            sql_where = "WHERE uk.tarih BETWEEN ? AND ?"
            params = [tarih_baslangic, tarih_bitis]
            
            if vardiya_id:
                sql_where += " AND uk.vardiya_id = ?"
                params.append(vardiya_id)
            
            if operator_id:
                sql_where += " AND uk.operator_id = ?"
                params.append(operator_id)
            
            # Detay verileri
            cursor.execute(f"""
                SELECT 
                    uk.tarih,
                    v.ad AS vardiya,
                    p.ad + ' ' + p.soyad AS operator,
                    ie.is_emri_no,
                    u.urun_kodu + ' - ' + u.urun_adi AS urun,
                    uk.uretilen_miktar,
                    uk.durum AS kayit_durumu,
                    CASE 
                        WHEN uk.baslama_zamani IS NOT NULL AND uk.bitis_zamani IS NOT NULL 
                        THEN DATEDIFF(MINUTE, uk.baslama_zamani, uk.bitis_zamani)
                        ELSE NULL
                    END AS sure_dk,
                    NULL AS notlar
                FROM uretim.uretim_kayitlari uk
                LEFT JOIN tanim.vardiyalar v ON uk.vardiya_id = v.id
                LEFT JOIN ik.personeller p ON uk.operator_id = p.id
                LEFT JOIN siparis.is_emirleri ie ON uk.is_emri_id = ie.id
                LEFT JOIN stok.urunler u ON ie.urun_id = u.id
                {sql_where}
                ORDER BY uk.tarih DESC, uk.olusturma_tarihi DESC
            """, params)
            
            detay_rows = cursor.fetchall()
            
            # Özet verileri (Vardiya bazlı)
            cursor.execute(f"""
                SELECT 
                    v.ad AS vardiya,
                    COUNT(*) AS kayit_sayisi,
                    SUM(uk.uretilen_miktar) AS toplam_uretim,
                    AVG(CASE 
                        WHEN uk.baslama_zamani IS NOT NULL AND uk.bitis_zamani IS NOT NULL 
                        THEN DATEDIFF(MINUTE, uk.baslama_zamani, uk.bitis_zamani)
                        ELSE NULL
                    END) AS ort_sure_dk
                FROM uretim.uretim_kayitlari uk
                LEFT JOIN tanim.vardiyalar v ON uk.vardiya_id = v.id
                {sql_where}
                GROUP BY v.ad, uk.vardiya_id
                ORDER BY uk.vardiya_id
            """, params)
            
            ozet_rows = cursor.fetchall()
            
            conn.close()
            
            # Özet kartları güncelle
            toplam_kayit = len(detay_rows)
            toplam_uretim = sum(row[5] for row in detay_rows if row[5])
            
            sure_list = [row[7] for row in detay_rows if row[7] is not None]
            ort_sure = sum(sure_list) / len(sure_list) if sure_list else 0
            
            # Aktif vardiya (şu anki saat bazlı)
            aktif_vardiya = self._get_aktif_vardiya()
            
            self.kart_toplam.findChild(QLabel, "value").setText(str(toplam_kayit))
            self.kart_adet.findChild(QLabel, "value").setText(f"{toplam_uretim:,.0f} adet")
            self.kart_sure.findChild(QLabel, "value").setText(f"{ort_sure:.0f} dk")
            self.kart_vardiya.findChild(QLabel, "value").setText(aktif_vardiya)
            
            # Özet tablosu doldur
            self.ozet_table.setRowCount(len(ozet_rows))
            for i, row in enumerate(ozet_rows):
                vardiya, kayit, uretim, sure = row
                
                self.ozet_table.setItem(i, 0, QTableWidgetItem(vardiya or "-"))
                self.ozet_table.setItem(i, 1, QTableWidgetItem(str(kayit)))
                self.ozet_table.setItem(i, 2, QTableWidgetItem(f"{uretim:,.0f}" if uretim else "0"))
                self.ozet_table.setItem(i, 3, QTableWidgetItem(f"{sure:.0f} dk" if sure else "-"))
                
                # Renklendirme
                for col in range(4):
                    item = self.ozet_table.item(i, col)
                    if col == 0:
                        item.setForeground(QColor(self.theme.get('primary', '#6366f1')))
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
            
            # Detay tablosu doldur
            self.detay_table.setRowCount(len(detay_rows))
            for i, row in enumerate(detay_rows):
                tarih, vardiya, operator, is_emri, urun, miktar, kalite, sure, not_ = row
                
                # Tarih
                tarih_str = tarih.strftime('%d.%m.%Y') if tarih else "-"
                self.detay_table.setItem(i, 0, QTableWidgetItem(tarih_str))
                
                # Vardiya
                self.detay_table.setItem(i, 1, QTableWidgetItem(vardiya or "-"))
                
                # Operatör
                self.detay_table.setItem(i, 2, QTableWidgetItem(operator or "-"))
                
                # İş Emri
                self.detay_table.setItem(i, 3, QTableWidgetItem(is_emri or "-"))
                
                # Ürün
                self.detay_table.setItem(i, 4, QTableWidgetItem(urun or "-"))
                
                # Miktar
                miktar_item = QTableWidgetItem(f"{miktar:,.0f}" if miktar else "0")
                miktar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.detay_table.setItem(i, 5, miktar_item)
                
                # Kalite
                kalite_item = QTableWidgetItem(kalite or "-")
                if kalite == "OK":
                    kalite_item.setForeground(QColor(self.theme.get('success', '#22c55e')))
                elif kalite == "RED":
                    kalite_item.setForeground(QColor(self.theme.get('error', '#ef4444')))
                else:
                    kalite_item.setForeground(QColor(self.theme.get('warning', '#f59e0b')))
                self.detay_table.setItem(i, 6, kalite_item)
                
                # Süre
                sure_str = f"{sure} dk" if sure else "-"
                self.detay_table.setItem(i, 7, QTableWidgetItem(sure_str))
                
                # Not
                self.detay_table.setItem(i, 8, QTableWidgetItem(not_ or "-"))
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yükleme hatası: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _get_aktif_vardiya(self):
        """Şu anki saate göre aktif vardiyayı bul"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Şimdiki saat
            su_an = datetime.now().time()
            
            cursor.execute("""
                SELECT ad 
                FROM tanim.vardiyalar 
                WHERE aktif_mi = 1
                  AND baslangic_saati <= ? 
                  AND bitis_saati >= ?
                ORDER BY id
            """, (su_an, su_an))
            
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else "-"
        except:
            return "-"
    
    def _input_style(self):
        s = self.s
        return f"""
            QComboBox, QDateEdit {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
            }}
            QComboBox:focus, QDateEdit:focus {{
                border-color: {s['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """
    
    def _button_style(self):
        s = self.s
        return f"""
            QPushButton {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {s['primary']};
                border-color: {s['primary']};
            }}
        """
    
    def _table_style(self):
        s = self.s
        return f"""
            QTableWidget {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                gridline-color: {s['border']};
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {s['border']};
            }}
            QTableWidget::item:selected {{
                background: {s['primary']};
            }}
            QTableWidget::item:hover {{
                background: rgba(220, 38, 38, 0.1);
            }}
            QHeaderView::section {{
                background: rgba(0, 0, 0, 0.3);
                color: {s['text_secondary']};
                padding: 8px 6px;
                border: none;
                border-bottom: 2px solid {s['primary']};
                font-weight: 600;
                font-size: 11px;
            }}
        """
