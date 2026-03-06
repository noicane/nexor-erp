# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Ciro ve Finans Analizi Modülü
Yönetim > Ciro Analiz

Fatura sorgu ve satış analizi dashboard.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QFrame, QLabel,
    QPushButton, QLineEdit, QComboBox, QDateEdit, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout,
    QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush, QPainter

try:
    from PySide6.QtCharts import QChart, QChartView, QPieSeries
    HAS_CHARTS = True
except ImportError:
    HAS_CHARTS = False

import pandas as pd
from datetime import datetime

from components.base_page import BasePage
from core.database import get_db_connection


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================
def format_number(val) -> str:
    """Sayıyı TR formatına çevir"""
    try:
        return f"{float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"


def render_to_table(table: QTableWidget, df: pd.DataFrame, columns: list):
    """DataFrame'i tabloya render et"""
    table.clear()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    
    if df is None or df.empty:
        table.setRowCount(0)
        return
    
    table.setRowCount(len(df))
    numeric_cols = ["MIKTAR", "BRFTL", "TUTARTL", "KDVTL", "TUTARD", "ADET", "NETTL", "BRUTTL", "BRUT", "NET", "KDV"]
    
    for r, row in df.iterrows():
        for c, col in enumerate(columns):
            val = str(row.get(col, ""))
            if col in numeric_cols:
                val = format_number(row.get(col, 0))
            
            item = QTableWidgetItem(val)
            if col in numeric_cols:
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(r, c, item)
    
    table.resizeColumnsToContents()


# =============================================================================
# SEKME 1: FATURA SORGU
# =============================================================================
class FaturaSorguTab(QWidget):
    def __init__(self, theme: dict):
        super().__init__()
        self.theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Filtre Paneli
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme['bg_card']};
                border: 1px solid {self.theme['border']};
                border-radius: 12px;
            }}
        """)
        filter_layout = QGridLayout(filter_frame)
        filter_layout.setContentsMargins(16, 16, 16, 16)
        filter_layout.setSpacing(12)
        
        input_style = f"""
            background: {self.theme['bg_main']};
            color: {self.theme['text']};
            border: 1px solid {self.theme['border']};
            border-radius: 6px;
            padding: 6px;
        """
        label_style = f"color: {self.theme['text_secondary']}; font-weight: bold;"
        
        # Tarih aralığı
        filter_layout.addWidget(QLabel("Başlangıç:", styleSheet=label_style), 0, 0)
        self.dt_from = QDateEdit(QDate.currentDate().addMonths(-1))
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setStyleSheet(input_style)
        filter_layout.addWidget(self.dt_from, 0, 1)
        
        filter_layout.addWidget(QLabel("Bitiş:", styleSheet=label_style), 0, 2)
        self.dt_to = QDateEdit(QDate.currentDate())
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setStyleSheet(input_style)
        filter_layout.addWidget(self.dt_to, 0, 3)
        
        # Tür ve Cari
        filter_layout.addWidget(QLabel("Tür:", styleSheet=label_style), 1, 0)
        self.cb_tur = QComboBox()
        self.cb_tur.addItems(["Tümü", "Satış", "Alış"])
        self.cb_tur.setStyleSheet(input_style)
        filter_layout.addWidget(self.cb_tur, 1, 1)
        
        filter_layout.addWidget(QLabel("Cari Adı:", styleSheet=label_style), 1, 2)
        self.ed_cari = QLineEdit()
        self.ed_cari.setPlaceholderText("Cari adı ara...")
        self.ed_cari.setStyleSheet(input_style)
        filter_layout.addWidget(self.ed_cari, 1, 3)
        
        # Sorgula butonu
        btn_search = QPushButton("🔍 Sorgula")
        btn_search.setCursor(Qt.PointingHandCursor)
        btn_search.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme['primary']};
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background: {self.theme.get('primary_dark', '#2563EB')};
            }}
        """)
        btn_search.clicked.connect(self._run_query)
        filter_layout.addWidget(btn_search, 0, 4, 2, 1)
        
        layout.addWidget(filter_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme['bg_card']};
                color: {self.theme['text']};
                border: none;
                gridline-color: {self.theme['border']};
            }}
            QHeaderView::section {{
                background: {self.theme['bg_main']};
                color: {self.theme['text']};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {self.theme['primary']};
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {self.theme['border']};
            }}
        """)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        
        # Alt Toplam
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme['bg_card']};
                border: 1px solid {self.theme['border']};
                border-radius: 12px;
            }}
        """)
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(16, 12, 16, 12)
        
        self.lbl_total = QLabel("Toplam: -")
        self.lbl_total.setStyleSheet(f"color: {self.theme.get('warning', '#F59E0B')}; font-weight: bold; font-size: 14px;")
        bottom_layout.addWidget(self.lbl_total)
        bottom_layout.addStretch()
        
        layout.addWidget(bottom_frame)
    
    def _run_query(self):
        """Fatura sorgusunu çalıştır"""
        d1 = self.dt_from.date().toString("yyyy-MM-dd")
        d2 = self.dt_to.date().toString("yyyy-MM-dd")
        tur = self.cb_tur.currentText()
        cari = self.ed_cari.text().strip()
        
        try:
            conn = get_db_connection()
            if not conn:
                QMessageBox.warning(self, "Hata", "Veritabanına bağlanılamadı!")
                return
            
            # Not: Bu sorgu örnek - gerçek tablo yapınıza göre düzenlenecek
            query = f"""
                SELECT TOP 1000 
                    'SATIS' as TURAC,
                    GETDATE() as TARIH,
                    'F-001' as EVRAKNO,
                    'Örnek Cari' as CARI_ADI,
                    'STK001' as STK,
                    'Örnek Stok' as STOK_ADI,
                    100 as MIKTAR,
                    1000.00 as TUTARTL,
                    180.00 as KDVTL
                WHERE 1=0
            """
            
            # Gerçek sorgu için:
            # cursor = conn.cursor()
            # cursor.execute(query)
            # df = pd.DataFrame.from_records(cursor.fetchall(), columns=[...])
            
            # Şimdilik boş tablo
            df = pd.DataFrame()
            
            cols = ["TURAC", "TARIH", "EVRAKNO", "CARI_ADI", "STK", "STOK_ADI", "MIKTAR", "TUTARTL", "KDVTL"]
            render_to_table(self.table, df, cols)
            
            if df is not None and not df.empty:
                self.lbl_total.setText(f"Toplam Tutar: {format_number(df['TUTARTL'].sum())} TL")
            else:
                self.lbl_total.setText("Veri bulunamadı")
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sorgu hatası:\n{str(e)}")


# =============================================================================
# SEKME 2: SATIŞ ANALİZİ
# =============================================================================
class AnalizTab(QWidget):
    def __init__(self, theme: dict):
        super().__init__()
        self.theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Üst Filtre
        top_frame = QFrame()
        top_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme['bg_card']};
                border: 1px solid {self.theme['border']};
                border-radius: 12px;
            }}
        """)
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(16, 12, 16, 12)
        
        input_style = f"""
            background: {self.theme['bg_main']};
            color: {self.theme['text']};
            border: 1px solid {self.theme['border']};
            border-radius: 6px;
            padding: 6px;
        """
        
        top_layout.addWidget(QLabel("Yıl:", styleSheet=f"color: {self.theme['text_secondary']}; font-weight: bold;"))
        self.sp_year = QSpinBox()
        self.sp_year.setRange(2000, 2100)
        self.sp_year.setValue(datetime.now().year)
        self.sp_year.setStyleSheet(input_style)
        top_layout.addWidget(self.sp_year)
        
        top_layout.addWidget(QLabel("Ay:", styleSheet=f"color: {self.theme['text_secondary']}; font-weight: bold;"))
        self.cb_month = QComboBox()
        self.cb_month.addItems([f"{i:02d}" for i in range(1, 13)])
        self.cb_month.setCurrentIndex(datetime.now().month - 1)
        self.cb_month.setStyleSheet(input_style)
        top_layout.addWidget(self.cb_month)
        
        btn_run = QPushButton("📊 Analiz Et")
        btn_run.setCursor(Qt.PointingHandCursor)
        btn_run.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme['primary']};
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 8px;
                border: none;
            }}
        """)
        btn_run.clicked.connect(self._run_analysis)
        top_layout.addWidget(btn_run)
        top_layout.addStretch()
        
        layout.addWidget(top_frame)
        
        # İçerik: Grafik + Detay Paneli
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # Sol: Grafik
        if HAS_CHARTS:
            self.chart_view = QChartView()
            self.chart_view.setRenderHint(QPainter.Antialiasing)
            self.chart_view.setStyleSheet("background: transparent; border: none;")
            self.chart_view.setMinimumWidth(400)
            content_layout.addWidget(self.chart_view, 2)
        else:
            no_chart = QLabel("📊 Grafik için QtCharts gerekli")
            no_chart.setAlignment(Qt.AlignCenter)
            no_chart.setStyleSheet(f"color: {self.theme['text_secondary']};")
            content_layout.addWidget(no_chart, 2)
        
        # Sağ: Detay Paneli
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)
        
        # Top 15 Tablosu
        right_layout.addWidget(QLabel("📈 Top 15 Cari (Brüt TL)", styleSheet=f"color: {self.theme['text']}; font-weight: bold;"))
        self.tbl_top = QTableWidget()
        self.tbl_top.setStyleSheet(self._table_style())
        self.tbl_top.setMaximumHeight(200)
        self.tbl_top.verticalHeader().setVisible(False)
        right_layout.addWidget(self.tbl_top)
        
        # Özet Kartları
        card_layout = QHBoxLayout()
        card_layout.setSpacing(12)
        
        self.card_brut = self._create_card("Brüt TL", "#F2C94C")
        self.card_net = self._create_card("Net TL", "#2F80ED")
        self.card_kdv = self._create_card("KDV TL", "#95A5A6")
        self.card_adet = self._create_card("Adet", "#EB984E")
        
        for card in [self.card_brut, self.card_net, self.card_kdv, self.card_adet]:
            card_layout.addWidget(card)
        
        right_layout.addLayout(card_layout)
        
        # Tüm Cariler Tablosu
        right_layout.addWidget(QLabel("📋 Tüm Cariler", styleSheet=f"color: {self.theme['text']}; font-weight: bold;"))
        self.tbl_all = QTableWidget()
        self.tbl_all.setStyleSheet(self._table_style())
        self.tbl_all.verticalHeader().setVisible(False)
        right_layout.addWidget(self.tbl_all, 1)
        
        content_layout.addWidget(right_panel, 3)
        layout.addLayout(content_layout, 1)
    
    def _table_style(self) -> str:
        return f"""
            QTableWidget {{
                background: {self.theme['bg_card']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                gridline-color: {self.theme['border']};
            }}
            QHeaderView::section {{
                background: {self.theme['bg_main']};
                color: {self.theme['text']};
                padding: 6px;
                border: none;
                font-weight: bold;
            }}
        """
    
    def _create_card(self, title: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"background: {color}; border-radius: 12px;")
        frame.setFixedHeight(80)
        
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(4)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: black; font-size: 12px; font-weight: bold; background: transparent;")
        lbl_title.setAlignment(Qt.AlignCenter)
        
        lbl_value = QLabel("0")
        lbl_value.setStyleSheet("color: black; font-size: 16px; font-weight: 800; background: transparent;")
        lbl_value.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        
        frame.value_label = lbl_value
        return frame
    
    def _run_analysis(self):
        """Satış analizini çalıştır"""
        year = self.sp_year.value()
        month = int(self.cb_month.currentText())
        
        # Örnek veri (gerçek sorgu ile değiştirilecek)
        sample_data = [
            {"STA": "Müşteri A", "BRUT": 150000, "NET": 127118, "KDV": 22882, "ADET": 1200},
            {"STA": "Müşteri B", "BRUT": 120000, "NET": 101695, "KDV": 18305, "ADET": 950},
            {"STA": "Müşteri C", "BRUT": 95000, "NET": 80508, "KDV": 14492, "ADET": 780},
            {"STA": "Müşteri D", "BRUT": 80000, "NET": 67797, "KDV": 12203, "ADET": 650},
            {"STA": "Müşteri E", "BRUT": 65000, "NET": 55085, "KDV": 9915, "ADET": 520},
        ]
        
        df = pd.DataFrame(sample_data)
        
        if df.empty:
            QMessageBox.information(self, "Bilgi", "Veri bulunamadı.")
            return
        
        # Top 15 Tablosu
        cols_top = ["Sıra", "Cari", "Adet", "Net TL", "KDV TL", "Brüt TL"]
        self.tbl_top.clear()
        self.tbl_top.setColumnCount(len(cols_top))
        self.tbl_top.setHorizontalHeaderLabels(cols_top)
        self.tbl_top.setRowCount(len(df))
        
        for r, row in df.iterrows():
            vals = [str(r + 1), str(row["STA"]), format_number(row["ADET"]),
                    format_number(row["NET"]), format_number(row["KDV"]), format_number(row["BRUT"])]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c > 1:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tbl_top.setItem(r, c, item)
        self.tbl_top.resizeColumnsToContents()
        
        # Kartları güncelle
        self.card_brut.value_label.setText(format_number(df["BRUT"].sum()))
        self.card_net.value_label.setText(format_number(df["NET"].sum()))
        self.card_kdv.value_label.setText(format_number(df["KDV"].sum()))
        self.card_adet.value_label.setText(format_number(df["ADET"].sum()))
        
        # Tüm Cariler (Heatmap)
        cols_all = ["Cari", "Adet", "Net TL", "KDV TL", "Brüt TL"]
        self.tbl_all.clear()
        self.tbl_all.setColumnCount(len(cols_all))
        self.tbl_all.setHorizontalHeaderLabels(cols_all)
        self.tbl_all.setRowCount(len(df))
        
        max_val = df["BRUT"].max()
        
        for r, row in df.iterrows():
            if r == 0:
                bg_color = QColor("#F2C94C")
                fg_color = QColor("black")
            else:
                ratio = row["BRUT"] / max_val if max_val > 0 else 0
                bg_color = QColor("#27AE60")
                bg_color.setAlphaF(0.3 + (ratio * 0.7))
                fg_color = QColor("white")
            
            vals = [str(row["STA"]), format_number(row["ADET"]),
                    format_number(row["NET"]), format_number(row["KDV"]), format_number(row["BRUT"])]
            
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setBackground(QBrush(bg_color))
                item.setForeground(QBrush(fg_color))
                if c > 0:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tbl_all.setItem(r, c, item)
        
        self.tbl_all.resizeColumnsToContents()
        
        # Grafik
        if HAS_CHARTS:
            chart = QChart()
            chart.setBackgroundBrush(QBrush(QColor(0, 0, 0, 0)))
            chart.setTitle(f"{month}/{year} Satış Dağılımı")
            chart.setTitleBrush(QBrush(QColor("white")))
            
            series = QPieSeries()
            for _, row in df.head(10).iterrows():
                sl = series.append(str(row["STA"])[:15], float(row["BRUT"]))
                sl.setLabelVisible(True)
                sl.setLabelColor(QColor("white"))
            
            chart.addSeries(series)
            chart.legend().setVisible(False)
            self.chart_view.setChart(chart)


# =============================================================================
# ANA SAYFA
# =============================================================================
class CiroAnalizPage(BasePage):
    """Ciro ve Finans Analizi Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Başlık
        header = QFrame()
        header.setStyleSheet(f"background: {self.theme['bg_card']}; border-radius: 12px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        icon_frame = QFrame()
        icon_frame.setFixedSize(48, 48)
        icon_frame.setStyleSheet(f"background: {self.theme.get('gradient_css', '#10B981')}; border-radius: 12px;")
        icon_lbl = QLabel("💰")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(icon_lbl)
        header_layout.addWidget(icon_frame)
        
        title_layout = QVBoxLayout()
        title = QLabel("Ciro ve Finans Analizi")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 18px; font-weight: bold;")
        subtitle = QLabel("Fatura sorgu ve satış performans dashboard")
        subtitle.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 12px;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Sekmeler
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background: {self.theme['bg_card']};
                border: none;
                border-radius: 12px;
            }}
            QTabBar::tab {{
                background: {self.theme['bg_main']};
                color: {self.theme['text_secondary']};
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background: {self.theme['bg_card']};
                color: {self.theme['primary']};
            }}
        """)
        
        self.tab_fatura = FaturaSorguTab(self.theme)
        self.tab_analiz = AnalizTab(self.theme)
        
        self.tabs.addTab(self.tab_fatura, "📄 Fatura Sorgu")
        self.tabs.addTab(self.tab_analiz, "📊 Satış Analizi")
        
        layout.addWidget(self.tabs, 1)
