# -*- coding: utf-8 -*-
"""
NEXOR ERP - Lab Dashboard
Laboratuvar performans dashboard'u - grafikler ve trendler
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
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
from core.nexor_brand import brand


class LabDashboardPage(BasePage):
    """Lab Dashboard - Performans ve trend analizi"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

        # Otomatik yenileme (1 dakika)
        self.auto_refresh = QTimer()
        self.auto_refresh.timeout.connect(self._load_data)
        self.auto_refresh.start(60000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # ── 1. Header ──
        header = self.create_page_header(
            "Lab Dashboard",
            "Laboratuvar performans ve trend analizi"
        )
        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        header.addWidget(btn_yenile)
        layout.addLayout(header)

        # ── 2. KPI cards ──
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self.card_toplam = self.create_stat_card("TOPLAM ANALIZ (30 GUN)", "0", color=brand.INFO)
        kpi_row.addWidget(self.card_toplam)

        self.card_kritik = self.create_stat_card("KRITIK EVENT", "0", color=brand.ERROR)
        kpi_row.addWidget(self.card_kritik)

        self.card_uyari = self.create_stat_card("UYARI EVENT", "0", color=brand.WARNING)
        kpi_row.addWidget(self.card_uyari)

        self.card_basari = self.create_stat_card("BASARI ORANI", "0%", color=brand.SUCCESS)
        kpi_row.addWidget(self.card_basari)

        layout.addLayout(kpi_row)

        # ── 3. Ana Icerik - Yan Yana ──
        content_layout = QHBoxLayout()
        content_layout.setSpacing(brand.SP_4)

        # Sol: Banyo Performans Tablosu
        left_frame = QFrame()
        left_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(brand.SP_5, brand.SP_5, brand.SP_5, brand.SP_5)
        left_layout.setSpacing(brand.SP_4)

        left_title = QLabel("Banyo Performansi (Son 30 Gun)")
        left_title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_SUBTITLE}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        left_layout.addWidget(left_title)

        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(4)
        self.performance_table.setHorizontalHeaderLabels(["Banyo", "Analiz", "Basari %", "Kritik"])
        self.performance_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.performance_table.setColumnWidth(1, brand.sp(80))
        self.performance_table.setColumnWidth(2, brand.sp(90))
        self.performance_table.setColumnWidth(3, brand.sp(80))
        self.performance_table.verticalHeader().setVisible(False)
        self.performance_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.performance_table.setShowGrid(False)
        self.performance_table.setAlternatingRowColors(True)
        self.performance_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.performance_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.performance_table.setStyleSheet(self._table_css())
        left_layout.addWidget(self.performance_table)

        content_layout.addWidget(left_frame, 1)

        # Sag: Haftalik Trend
        right_frame = QFrame()
        right_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(brand.SP_5, brand.SP_5, brand.SP_5, brand.SP_5)
        right_layout.setSpacing(brand.SP_4)

        right_title = QLabel("Haftalik Trend")
        right_title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_SUBTITLE}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        right_layout.addWidget(right_title)

        self.trend_table = QTableWidget()
        self.trend_table.setColumnCount(4)
        self.trend_table.setHorizontalHeaderLabels(["Hafta", "Analiz", "Kritik", "Sapma"])
        self.trend_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.trend_table.setColumnWidth(1, brand.sp(80))
        self.trend_table.setColumnWidth(2, brand.sp(80))
        self.trend_table.setColumnWidth(3, brand.sp(80))
        self.trend_table.verticalHeader().setVisible(False)
        self.trend_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.trend_table.setShowGrid(False)
        self.trend_table.setAlternatingRowColors(True)
        self.trend_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.trend_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.trend_table.setStyleSheet(self._table_css())
        right_layout.addWidget(self.trend_table)

        content_layout.addWidget(right_frame, 1)

        layout.addLayout(content_layout, 1)

    # -----------------------------------------------------------------
    @staticmethod
    def _table_css() -> str:
        return f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_3}px {brand.SP_4}px;
                border-bottom: 1px solid {brand.BORDER};
                color: {brand.TEXT};
            }}
            QTableWidget::item:alternate {{ background: {brand.BG_MAIN}; }}
            QTableWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_4}px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """

    # -----------------------------------------------------------------
    def _load_data(self):
        """Dashboard verilerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # KPI'lar - Son 30 gun
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

                self.card_toplam.findChild(QLabel, "stat_value").setText(str(toplam))
                self.card_kritik.findChild(QLabel, "stat_value").setText(str(kritik))
                self.card_uyari.findChild(QLabel, "stat_value").setText(str(uyari))
                self.card_basari.findChild(QLabel, "stat_value").setText(f"{basari_oran:.1f}%")

            # Banyo Performansi
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
                    basari_item.setForeground(QColor(brand.SUCCESS))
                elif row[2] and row[2] >= 70:
                    basari_item.setForeground(QColor(brand.WARNING))
                else:
                    basari_item.setForeground(QColor(brand.ERROR))
                self.performance_table.setItem(i, 2, basari_item)

                kritik_item = QTableWidgetItem(str(row[3] or 0))
                if row[3] and row[3] > 5:
                    kritik_item.setForeground(QColor(brand.ERROR))
                self.performance_table.setItem(i, 3, kritik_item)

            # Haftalik Trend
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
                    kritik_item.setForeground(QColor(brand.ERROR))
                self.trend_table.setItem(i, 2, kritik_item)

                sapma_text = f"{row[3]:.2f}" if row[3] else "-"
                self.trend_table.setItem(i, 3, QTableWidgetItem(sapma_text))

        except Exception as e:
            print(f"Dashboard yukleme hatasi: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
