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
    from PySide6.QtCharts import (
        QChart, QChartView, QPieSeries,
        QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QLineSeries,
        QAbstractBarSeries,
    )
    HAS_CHARTS = True
except ImportError:
    HAS_CHARTS = False

import pandas as pd
from datetime import datetime

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


def _get_zirve_connection():
    """Zirve Ticari veritabanı bağlantısı"""
    from core.zirve_entegrasyon import _get_zirve_connection as _zc
    return _zc()


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================
def format_number(val) -> str:
    """Sayıyı TR formatına çevir"""
    try:
        return f"{float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
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
    numeric_cols = ["MIKTAR", "BRFTL", "TUTARTL", "KDVTL", "KDVY", "TUTARD", "ADET", "NETTL", "BRUTTL", "BRUT", "NET", "KDV"]
    
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
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 12px;
            }}
        """)
        filter_layout = QGridLayout(filter_frame)
        filter_layout.setContentsMargins(16, 16, 16, 16)
        filter_layout.setSpacing(12)
        
        input_style = f"""
            background: {brand.BG_MAIN};
            color: {brand.TEXT};
            border: 1px solid {brand.BORDER};
            border-radius: 6px;
            padding: 6px;
        """
        label_style = f"color: {brand.TEXT_MUTED}; font-weight: bold;"
        
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
                background: {brand.PRIMARY};
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background: {brand.PRIMARY_HOVER};
            }}
        """)
        btn_search.clicked.connect(self._run_query)
        filter_layout.addWidget(btn_search, 0, 4, 2, 1)
        
        layout.addWidget(filter_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: none;
                gridline-color: {brand.BORDER};
            }}
            QHeaderView::section {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {brand.BORDER};
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
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 12px;
            }}
        """)
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(16, 12, 16, 12)
        
        self.lbl_total = QLabel("Toplam: -")
        self.lbl_total.setStyleSheet(f"color: {brand.WARNING}; font-weight: bold; font-size: 14px;")
        bottom_layout.addWidget(self.lbl_total)
        bottom_layout.addStretch()
        
        layout.addWidget(bottom_frame)
    
    def _run_query(self):
        """Fatura sorgusunu çalıştır — Zirve FATURA + FATURA_ALT"""
        d1 = self.dt_from.date().toString("yyyy-MM-dd")
        d2 = self.dt_to.date().toString("yyyy-MM-dd")
        tur = self.cb_tur.currentText()
        cari = self.ed_cari.text().strip()

        try:
            conn = _get_zirve_connection()
            if not conn:
                QMessageBox.warning(self, "Hata", "Zirve veritabanına bağlanılamadı!")
                return

            cursor = conn.cursor()

            where = "WHERE f.EVRAKTAR BETWEEN ? AND ?"
            params = [d1, d2]

            if tur == "Satış":
                where += " AND f.AORS = 'S'"
            elif tur == "Alış":
                where += " AND f.AORS = 'A'"

            if cari:
                where += " AND c.STA LIKE ?"
                params.append(f"%{cari}%")

            query = f"""
                SELECT TOP 1000
                    f.TURAC,
                    CONVERT(VARCHAR(10), f.EVRAKTAR, 104) as TARIH,
                    f.EVRAKNO,
                    c.STA,
                    a.STK,
                    a.OZELKOD1,
                    s.STA as STA2,
                    a.STB,
                    a.MIKTAR,
                    a.BRFTL,
                    a.TUTARTL,
                    a.KDVY,
                    a.KDVTL
                FROM dbo.FATURA f
                INNER JOIN dbo.FATURA_ALT a ON a.P_ID = f.P_ID
                LEFT JOIN dbo.CARIGEN c ON c.REF = f.CARIREF
                LEFT JOIN dbo.STOKGEN s ON s.STK = a.STK
                {where}
                ORDER BY f.EVRAKTAR DESC, f.SIRANO DESC
            """

            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            df = pd.DataFrame.from_records(rows, columns=columns) if rows else pd.DataFrame()

            cols = ["TURAC", "TARIH", "EVRAKNO", "STA", "STK", "OZELKOD1", "STA2", "STB", "MIKTAR", "BRFTL", "TUTARTL", "KDVY", "KDVTL"]
            render_to_table(self.table, df, cols)

            if df is not None and not df.empty:
                toplam = df['TUTARTL'].sum() if 'TUTARTL' in df.columns else 0
                kdv_toplam = df['KDVTL'].sum() if 'KDVTL' in df.columns else 0
                genel = toplam + kdv_toplam
                self.lbl_total.setText(
                    f"Tutar: {format_number(toplam)} TL  |  KDV: {format_number(kdv_toplam)} TL  |  "
                    f"Genel: {format_number(genel)} TL  |  {len(df)} kayıt"
                )
            else:
                self.lbl_total.setText("Veri bulunamadı")

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
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 12px;
            }}
        """)
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(16, 12, 16, 12)
        
        input_style = f"""
            background: {brand.BG_MAIN};
            color: {brand.TEXT};
            border: 1px solid {brand.BORDER};
            border-radius: 6px;
            padding: 6px;
        """
        
        top_layout.addWidget(QLabel("Yıl:", styleSheet=f"color: {brand.TEXT_MUTED}; font-weight: bold;"))
        self.sp_year = QSpinBox()
        self.sp_year.setRange(2000, 2100)
        self.sp_year.setValue(datetime.now().year)
        self.sp_year.setStyleSheet(input_style)
        top_layout.addWidget(self.sp_year)
        
        top_layout.addWidget(QLabel("Ay:", styleSheet=f"color: {brand.TEXT_MUTED}; font-weight: bold;"))
        self.cb_month = QComboBox()
        self.cb_month.addItems([f"{i:02d}" for i in range(1, 13)])
        self.cb_month.setCurrentIndex(datetime.now().month - 1)
        self.cb_month.setStyleSheet(input_style)
        top_layout.addWidget(self.cb_month)
        
        btn_run = QPushButton("📊 Analiz Et")
        btn_run.setCursor(Qt.PointingHandCursor)
        btn_run.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
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
            no_chart.setStyleSheet(f"color: {brand.TEXT_MUTED};")
            content_layout.addWidget(no_chart, 2)
        
        # Sağ: Detay Paneli
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)
        
        # Top 15 Tablosu
        right_layout.addWidget(QLabel("📈 Top 15 Cari (Brüt TL)", styleSheet=f"color: {brand.TEXT}; font-weight: bold;"))
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
        right_layout.addWidget(QLabel("📋 Tüm Cariler", styleSheet=f"color: {brand.TEXT}; font-weight: bold;"))
        self.tbl_all = QTableWidget()
        self.tbl_all.setStyleSheet(self._table_style())
        self.tbl_all.verticalHeader().setVisible(False)
        right_layout.addWidget(self.tbl_all, 1)
        
        content_layout.addWidget(right_panel, 3)
        layout.addLayout(content_layout, 1)
    
    def _table_style(self) -> str:
        return f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                gridline-color: {brand.BORDER};
            }}
            QHeaderView::section {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT};
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
        """Satış analizini çalıştır — Zirve FATURA verilerinden"""
        year = self.sp_year.value()
        month = int(self.cb_month.currentText())

        try:
            conn = _get_zirve_connection()
            if not conn:
                QMessageBox.warning(self, "Hata", "Zirve veritabanına bağlanılamadı!")
                return

            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.STA,
                    SUM(a.TUTARTL + a.KDVTL) as BRUT,
                    SUM(a.TUTARTL) as NET,
                    SUM(a.KDVTL) as KDV,
                    COUNT(*) as ADET
                FROM dbo.FATURA f
                INNER JOIN dbo.FATURA_ALT a ON a.P_ID = f.P_ID
                LEFT JOIN dbo.CARIGEN c ON c.REF = f.CARIREF
                WHERE f.AORS = 'S'
                  AND YEAR(f.EVRAKTAR) = ?
                  AND MONTH(f.EVRAKTAR) = ?
                GROUP BY c.STA
                ORDER BY BRUT DESC
            """, (year, month))

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            df = pd.DataFrame.from_records(rows, columns=columns) if rows else pd.DataFrame()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Analiz hatası:\n{str(e)}")
            return
        
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
# SEKME 3: TREND ANALİZİ
# =============================================================================
class TrendTab(QWidget):
    """Firma bazlı aylık ciro trend analizi"""

    COLORS = [
        "#DC2626", "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6",
        "#EC4899", "#06B6D4", "#84CC16", "#F97316", "#6366F1",
    ]

    def __init__(self, theme: dict):
        super().__init__()
        self.theme = theme
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        input_style = f"""
            background: {brand.BG_MAIN};
            color: {brand.TEXT};
            border: 1px solid {brand.BORDER};
            border-radius: 6px;
            padding: 6px;
        """
        label_style = f"color: {brand.TEXT_MUTED}; font-weight: bold;"

        # Filtre paneli
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 12px;
            }}
        """)
        fl = QVBoxLayout(filter_frame)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(10)

        # Üst satır: Firma seçimi
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        row1.addWidget(QLabel("Firma:", styleSheet=label_style))
        self.firma_combo = QComboBox()
        self.firma_combo.setEditable(True)
        self.firma_combo.setInsertPolicy(QComboBox.NoInsert)
        self.firma_combo.lineEdit().setPlaceholderText("Firma seçin veya yazın...")
        self.firma_combo.setMinimumWidth(350)
        combo_style = input_style + """
            QComboBox QAbstractItemView {
                background: """ + brand.BG_CARD + """;
                color: """ + brand.TEXT + """;
                border: 1px solid """ + brand.BORDER + """;
                selection-background-color: """ + brand.PRIMARY + """;
            }
        """
        self.firma_combo.setStyleSheet(combo_style)
        row1.addWidget(self.firma_combo, 1)

        # Yil secimi (Zirve'de her yil ayri DB)
        row1.addWidget(QLabel("Yıl:", styleSheet=label_style))
        self.yil_combo = QComboBox()
        self.yil_combo.setStyleSheet(input_style)
        self.yil_combo.setMinimumWidth(100)
        row1.addWidget(self.yil_combo)

        btn = QPushButton("📈 Göster")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white; font-weight: bold;
                padding: 8px 24px; border-radius: 8px; border: none;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        btn.clicked.connect(self._run_trend)
        row1.addWidget(btn)

        fl.addLayout(row1)

        # Alt satır: Çoklu firma seçimi
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self.secili_firmalar = []
        self.secili_label = QLabel("Firma seçip Göster'e tıklayın. Birden fazla firma eklemek için + Ekle butonunu kullanın.")
        self.secili_label.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px;")
        self.secili_label.setWordWrap(True)
        row2.addWidget(self.secili_label, 1)

        firma_ekle_btn = QPushButton("+ Ekle")
        firma_ekle_btn.setToolTip("Seçili firmayı karşılaştırma listesine ekle")
        firma_ekle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white; border: none; border-radius: 6px;
                padding: 5px 12px; font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        firma_ekle_btn.clicked.connect(self._firma_ekle)
        row2.addWidget(firma_ekle_btn)

        firma_temizle_btn = QPushButton("Temizle")
        firma_temizle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {brand.ERROR};
                border: 1px solid {brand.ERROR};
                border-radius: 6px;
                padding: 5px 12px; font-size: 11px;
            }}
            QPushButton:hover {{ background: {brand.ERROR}; color: white; }}
        """)
        firma_temizle_btn.clicked.connect(self._firma_temizle)
        row2.addWidget(firma_temizle_btn)

        fl.addLayout(row2)

        layout.addWidget(filter_frame)

        # Yil ve firma listelerini yukle
        self._load_yillar()
        self._load_firmalar()
        # Yil degisince firma listesi de yenilensin
        self.yil_combo.currentIndexChanged.connect(lambda _: self._load_firmalar())

        # İçerik: Grafik + Tablo
        content = QHBoxLayout()
        content.setSpacing(16)

        # Sol: Grafik
        if HAS_CHARTS:
            self.chart_view = QChartView()
            self.chart_view.setRenderHint(QPainter.Antialiasing)
            self.chart_view.setStyleSheet("background: transparent; border: none;")
            content.addWidget(self.chart_view, 3)
        else:
            lbl = QLabel("📈 Grafik için QtCharts gerekli")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {brand.TEXT_MUTED};")
            content.addWidget(lbl, 3)

        # Sağ: Tablo
        right = QVBoxLayout()
        right.setSpacing(12)

        right.addWidget(QLabel("📋 Aylık Detay", styleSheet=f"color: {brand.TEXT}; font-weight: bold; font-size: 14px;"))

        self.tbl_trend = QTableWidget()
        self.tbl_trend.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                gridline-color: {brand.BORDER};
            }}
            QHeaderView::section {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT};
                padding: 6px; border: none; font-weight: bold;
            }}
        """)
        self.tbl_trend.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_trend.verticalHeader().setVisible(False)
        self.tbl_trend.horizontalHeader().setStretchLastSection(True)
        right.addWidget(self.tbl_trend, 1)

        # Toplam kartları
        self.lbl_trend_total = QLabel("")
        self.lbl_trend_total.setStyleSheet(f"color: {brand.WARNING}; font-weight: bold; font-size: 13px;")
        right.addWidget(self.lbl_trend_total)

        content.addLayout(right, 2)
        layout.addLayout(content, 1)

    def _load_yillar(self):
        """Zirve sunucusunda mevcut yil DB'lerini combo'ya yukle."""
        try:
            from core.zirve_entegrasyon import list_zirve_yillar
            yillar = list_zirve_yillar()
        except Exception as e:
            print(f"Yil listesi alinamadi: {e}")
            yillar = []
        if not yillar:
            yillar = [datetime.now().year]
        self.yil_combo.clear()
        for y in yillar:
            self.yil_combo.addItem(str(y), y)
        # Varsayilan: en yeni yil
        self.yil_combo.setCurrentIndex(0)

    def _load_firmalar(self):
        """Secili yilin DB'sinden cari listesini combobox'a yukle"""
        try:
            from core.zirve_entegrasyon import get_zirve_connection_for_year
            yil = self.yil_combo.currentData() or datetime.now().year
            conn = get_zirve_connection_for_year(yil)
            if not conn:
                return
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT c.STA
                FROM dbo.CARIGEN c
                WHERE c.STA IS NOT NULL AND c.STA != ''
                ORDER BY c.STA
            """)
            self.firma_combo.clear()
            self.firma_combo.addItem("")
            for row in cursor.fetchall():
                self.firma_combo.addItem(row[0])
            conn.close()
        except Exception as e:
            print(f"Firma listesi yükleme hatası: {e}")

    def _firma_ekle(self):
        """Seçili firmayı listeye ekle"""
        firma = self.firma_combo.currentText().strip()
        if firma and firma not in self.secili_firmalar:
            self.secili_firmalar.append(firma)
            self._update_secili_label()

    def _firma_temizle(self):
        """Seçili firma listesini temizle"""
        self.secili_firmalar.clear()
        self._update_secili_label()

    def _update_secili_label(self):
        """Seçili firmaları göster"""
        if self.secili_firmalar:
            self.secili_label.setText(f"Seçili firmalar ({len(self.secili_firmalar)}): " + " | ".join(self.secili_firmalar))
        else:
            self.secili_label.setText("")

    def _run_trend(self):
        """Secili yilin 12 ayinda firma bazli ciro trendini cek"""
        # Seçili firmalar varsa onları kullan, yoksa combo'daki firmayı al
        if self.secili_firmalar:
            firma_list = list(self.secili_firmalar)
        else:
            combo_text = self.firma_combo.currentText().strip()
            firma_list = [combo_text] if combo_text else []

        if not firma_list:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir firma seçin!")
            return

        yil = self.yil_combo.currentData()
        if not yil:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir yıl seçin!")
            return
        self.secili_yil = int(yil)

        try:
            from core.zirve_entegrasyon import get_zirve_connection_for_year
            conn = get_zirve_connection_for_year(self.secili_yil)
            if not conn:
                QMessageBox.warning(self, "Hata", "Zirve veritabanına bağlanılamadı!")
                return

            cursor = conn.cursor()

            placeholders = ','.join(['?' for _ in firma_list])
            params = list(firma_list)

            cursor.execute(f"""
                SELECT
                    c.STA as FIRMA,
                    MONTH(f.EVRAKTAR) as AY_NO,
                    SUM(a.TUTARTL) as NET,
                    SUM(a.KDVTL) as KDV,
                    SUM(a.TUTARTL + a.KDVTL) as BRUT
                FROM dbo.FATURA f
                INNER JOIN dbo.FATURA_ALT a ON a.P_ID = f.P_ID
                LEFT JOIN dbo.CARIGEN c ON c.REF = f.CARIREF
                WHERE f.AORS = 'S'
                  AND c.STA IN ({placeholders})
                GROUP BY c.STA, MONTH(f.EVRAKTAR)
                ORDER BY c.STA, MONTH(f.EVRAKTAR)
            """, params)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                QMessageBox.information(self, "Bilgi", f"{self.secili_yil} yili icin veri bulunamadi.")
                return

            df = pd.DataFrame.from_records(rows, columns=columns)
            self._render_trend(df)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Trend sorgu hatası:\n{str(e)}")

    def _render_trend(self, df: pd.DataFrame):
        """Secili yilin 12 ayina ait trend grafigi ve tablo"""
        yil = getattr(self, 'secili_yil', datetime.now().year)
        all_months = list(range(1, 13))  # 1..12

        # Pivot: AY_NO (1..12) x Firma -> BRUT
        pivot = df.pivot_table(index='AY_NO', columns='FIRMA', values='BRUT', aggfunc='sum').fillna(0)
        pivot = pivot.reindex(all_months, fill_value=0)

        months = list(pivot.index)
        firms = list(pivot.columns)

        ay_kisaltma = {
            1: 'Oca', 2: 'Şub', 3: 'Mar', 4: 'Nis',
            5: 'May', 6: 'Haz', 7: 'Tem', 8: 'Ağu',
            9: 'Eyl', 10: 'Eki', 11: 'Kas', 12: 'Ara',
        }
        ay_labels = [ay_kisaltma[m] for m in months]

        # ---- Grafik ----
        if HAS_CHARTS:
            from PySide6.QtGui import QFont
            text_color = QColor(brand.TEXT)
            grid_color = QColor(brand.BORDER)

            # Buyuk rakamlar dik yazinca da sigmaz -> Bin TL'ye cevir
            scale = 1000
            unit = "Bin TL"

            chart = QChart()
            chart.setBackgroundBrush(QBrush(QColor(brand.BG_CARD)))
            chart.setTitle(f"{yil} Aylik Ciro Trendi  ({unit})")
            chart.setTitleBrush(QBrush(text_color))
            title_font = QFont()
            title_font.setBold(True)
            title_font.setPointSize(11)
            chart.setTitleFont(title_font)
            chart.setAnimationOptions(QChart.SeriesAnimations)

            max_val = 0
            bar_series = QBarSeries()
            for i, firma in enumerate(firms):
                bar_set = QBarSet(firma[:40])
                bar_set.setColor(QColor(self.COLORS[i % len(self.COLORS)]))
                bar_set.setLabelColor(text_color)
                for ay in months:
                    val = float(pivot.loc[ay, firma]) / scale
                    bar_set.append(val)
                    if val > max_val:
                        max_val = val
                bar_series.append(bar_set)

            # Sutun ustunde rakam (TR binlik ayraci)
            bar_series.setLabelsVisible(True)
            bar_series.setLabelsPosition(QAbstractBarSeries.LabelsOutsideEnd)
            bar_series.setLabelsFormat("@value")
            bar_series.setLabelsAngle(-90)

            chart.addSeries(bar_series)

            # Eksen yazi tipleri
            axis_font = QFont()
            axis_font.setPointSize(10)

            axis_x = QBarCategoryAxis()
            axis_x.append(ay_labels)
            axis_x.setLabelsColor(text_color)
            axis_x.setLabelsFont(axis_font)
            axis_x.setGridLineVisible(False)
            axis_x.setLinePenColor(grid_color)
            chart.addAxis(axis_x, Qt.AlignBottom)
            bar_series.attachAxis(axis_x)

            axis_y = QValueAxis()
            axis_y.setRange(0, max_val * 1.25 if max_val > 0 else 1000)
            axis_y.setLabelFormat("%.0f")
            axis_y.setLabelsColor(text_color)
            axis_y.setLabelsFont(axis_font)
            axis_y.setGridLineColor(grid_color)
            axis_y.setLinePenColor(grid_color)
            axis_y.setTitleText(unit)
            axis_y.setTitleBrush(QBrush(QColor(brand.TEXT_MUTED)))
            chart.addAxis(axis_y, Qt.AlignLeft)
            bar_series.attachAxis(axis_y)

            # Cari'ler altta legend
            legend_font = QFont()
            legend_font.setPointSize(10)
            legend_font.setBold(True)
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)
            chart.legend().setLabelColor(text_color)
            chart.legend().setFont(legend_font)

            self.chart_view.setChart(chart)
            self.chart_view.setBackgroundBrush(QBrush(QColor(brand.BG_CARD)))

        # ---- Tablo ----
        # Firma | Ay1 | Ay2 | ... | TOPLAM
        cols = ["Firma"] + ay_labels + ["TOPLAM"]
        self.tbl_trend.clear()
        self.tbl_trend.setColumnCount(len(cols))
        self.tbl_trend.setHorizontalHeaderLabels(cols)
        self.tbl_trend.setRowCount(len(firms))

        genel_toplam = 0
        for r, firma in enumerate(firms):
            # Firma adı
            item = QTableWidgetItem(firma)
            color = QColor(self.COLORS[r % len(self.COLORS)])
            item.setForeground(QBrush(color))
            self.tbl_trend.setItem(r, 0, item)

            firma_toplam = 0
            for c, ay in enumerate(months):
                val = float(pivot.loc[ay, firma])
                firma_toplam += val
                item = QTableWidgetItem(format_number(val))
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if val == 0:
                    item.setForeground(QBrush(QColor(100, 100, 100)))
                self.tbl_trend.setItem(r, c + 1, item)

            # Toplam kolonu
            genel_toplam += firma_toplam
            item = QTableWidgetItem(format_number(firma_toplam))
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setForeground(QBrush(QColor("#F59E0B")))
            from PySide6.QtGui import QFont as _QFont
            font = _QFont()
            font.setBold(True)
            item.setFont(font)
            self.tbl_trend.setItem(r, len(months) + 1, item)

        self.tbl_trend.resizeColumnsToContents()
        self.lbl_trend_total.setText(
            f"{yil} Genel Toplam: {format_number(genel_toplam)} TL  |  "
            f"{len(firms)} firma  |  {len(months)} ay"
        )


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
        header.setStyleSheet(f"background: {brand.BG_CARD}; border-radius: 12px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        icon_frame = QFrame()
        icon_frame.setFixedSize(48, 48)
        icon_frame.setStyleSheet(f"background: {brand.PRIMARY_SOFT}; border-radius: 12px;")
        icon_lbl = QLabel("💰")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(icon_lbl)
        header_layout.addWidget(icon_frame)
        
        title_layout = QVBoxLayout()
        title = QLabel("Ciro ve Finans Analizi")
        title.setStyleSheet(f"color: {brand.TEXT}; font-size: 18px; font-weight: bold;")
        subtitle = QLabel("Fatura sorgu ve satış performans dashboard")
        subtitle.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: 12px;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Sekmeler
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background: {brand.BG_CARD};
                border: none;
                border-radius: 12px;
            }}
            QTabBar::tab {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT_MUTED};
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background: {brand.BG_CARD};
                color: {brand.PRIMARY};
            }}
        """)
        
        self.tab_fatura = FaturaSorguTab(self.theme)
        self.tab_analiz = AnalizTab(self.theme)
        self.tab_trend = TrendTab(self.theme)

        self.tabs.addTab(self.tab_fatura, "📄 Fatura Sorgu")
        self.tabs.addTab(self.tab_analiz, "📊 Satış Analizi")
        self.tabs.addTab(self.tab_trend, "📈 Trend Analizi")
        
        layout.addWidget(self.tabs, 1)
