# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kaplama Bara Dashboard (Brand System)
==================================================
Kaplama hatti canli uretim takip - bara sayilari ve trendler.
Tum stiller core.nexor_brand uzerinden; matplotlib grafik renkleri de brand'den alinir.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from datetime import datetime

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from core.database import get_plc_connection
from core.nexor_brand import brand


def _soft(color_hex: str, alpha: float = 0.12) -> str:
    c = QColor(color_hex)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


# =============================================================================
# BRAND ICON
# =============================================================================

class BrandIcon(QLabel):
    def __init__(self, kind: str, color: str = None, size: int = None, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.color = color or brand.TEXT
        self.size_px = size or brand.ICON_MD
        self.setFixedSize(self.size_px, self.size_px)
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(self.color))
        pen.setWidthF(max(1.4, self.size_px / 12))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        s = self.size_px
        m = s * 0.18
        if self.kind == "factory":
            p.drawLine(int(m), int(s - m), int(m), int(s * 0.45))
            p.drawLine(int(m), int(s * 0.45), int(s * 0.45), int(s * 0.6))
            p.drawLine(int(s * 0.45), int(s * 0.6), int(s * 0.45), int(s * 0.3))
            p.drawLine(int(s * 0.45), int(s * 0.3), int(s - m), int(s * 0.45))
            p.drawLine(int(s - m), int(s * 0.45), int(s - m), int(s - m))
            p.drawLine(int(m), int(s - m), int(s - m), int(s - m))
        p.end()


# =============================================================================
# MATPLOTLIB CANVAS - brand-aware
# =============================================================================

class MplCanvas(FigureCanvasQTAgg):
    """Matplotlib grafik canvas - brand renkleri kullanir."""

    def __init__(self, parent=None, width=6, height=4, dpi=100):
        bg = brand.BG_CARD
        grid = brand.BORDER
        tick = brand.TEXT_MUTED

        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=bg)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

        self.fig.patch.set_facecolor(bg)
        self.axes.set_facecolor(bg)
        self.axes.tick_params(colors=tick, labelsize=9)
        self.axes.spines['bottom'].set_color(grid)
        self.axes.spines['left'].set_color(grid)
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.grid(True, alpha=0.18, color=grid, linestyle='--')


# =============================================================================
# BARA DASHBOARD PAGE
# =============================================================================

class BaraDashboardPage(QWidget):
    """Kaplama Bara Dashboard - Canli uretim takip"""

    def __init__(self, theme: dict = None):
        super().__init__()
        self.theme = theme or {}

        self._setup_ui()
        self._apply_styles()

        # Saat guncelleme (her saniye)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        # Ilk veri yukleme
        QTimer.singleShot(200, self._load_data)

        # Otomatik yenileme (30 saniye)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_data)
        self.refresh_timer.start(30000)

    def on_page_shown(self):
        """Sayfa gosterildiginde veriyi yenile"""
        self._load_data()

    def _update_clock(self):
        if hasattr(self, 'time_label'):
            self.time_label.setText(datetime.now().strftime('%H:%M:%S'))

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Ust Kartlar (3 buyuk kart)
        top_cards = QHBoxLayout()
        top_cards.setSpacing(brand.SP_5)

        self.card_canli = self._create_mega_card(
            "CANLI URETIM", "0", "Bugun 00:00'dan Itibaren",
            brand.PRIMARY
        )
        self.card_ktl = self._create_mega_card(
            "KATAFOREZ", "0", "Kazan 101",
            brand.SUCCESS
        )
        self.card_cinko = self._create_mega_card(
            "CINKO", "0", "Kazan 201",
            brand.WARNING
        )

        top_cards.addWidget(self.card_canli)
        top_cards.addWidget(self.card_ktl)
        top_cards.addWidget(self.card_cinko)

        layout.addLayout(top_cards)

        # Grafikler
        graphs = QHBoxLayout()
        graphs.setSpacing(brand.SP_5)

        # Kataforez Trend
        ktl_frame = self._create_chart_frame("KATAFOREZ TREND", "Son 7 Gun", brand.SUCCESS)
        self.ktl_canvas = MplCanvas(self, width=7, height=4.5, dpi=100)
        ktl_frame.layout().addWidget(self.ktl_canvas)
        graphs.addWidget(ktl_frame)

        # Cinko Trend
        cinko_frame = self._create_chart_frame("CINKO TREND", "Son 7 Gun", brand.WARNING)
        self.cinko_canvas = MplCanvas(self, width=7, height=4.5, dpi=100)
        cinko_frame.layout().addWidget(self.cinko_canvas)
        graphs.addWidget(cinko_frame)

        layout.addLayout(graphs, 1)

        # Alt: Toplam Trend
        total_frame = self._create_chart_frame("TOPLAM URETIM TRENDI",
                                                "Son 7 Gun - Kataforez + Cinko",
                                                brand.PRIMARY)
        self.total_canvas = MplCanvas(self, width=14, height=4, dpi=100)
        total_frame.layout().addWidget(self.total_canvas)
        layout.addWidget(total_frame)

    def _create_chart_frame(self, title: str, subtitle: str, accent: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("chartFrame")
        frame.setStyleSheet(f"""
            QFrame#chartFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(brand.SP_5, brand.SP_4, brand.SP_5, brand.SP_4)
        lay.setSpacing(brand.SP_2)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {accent}; font-size: {brand.FS_BODY_LG}px; "
            f"font-weight: {brand.FW_BOLD}; letter-spacing: 0.6px; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(title_lbl)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(sub_lbl)

        return frame

    def _create_header(self):
        frame = QFrame()
        frame.setObjectName("headerFrame")
        frame.setFixedHeight(brand.sp(96))
        frame.setStyleSheet(f"""
            QFrame#headerFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(brand.SP_5, brand.SP_4, brand.SP_5, brand.SP_4)
        layout.setSpacing(brand.SP_4)

        # Ikon kutusu
        icon_box = QFrame()
        icon_box.setFixedSize(brand.sp(48), brand.sp(48))
        icon_box.setStyleSheet(
            f"background: {_soft(brand.PRIMARY, 0.12)}; "
            f"border: 1px solid {_soft(brand.PRIMARY, 0.35)}; "
            f"border-radius: {brand.R_SM}px;"
        )
        ib = QVBoxLayout(icon_box)
        ib.setContentsMargins(0, 0, 0, 0)
        ib.addWidget(BrandIcon("factory", brand.PRIMARY, brand.sp(24)), 0, Qt.AlignCenter)
        layout.addWidget(icon_box)

        # Baslik
        title_layout = QVBoxLayout()
        title_layout.setSpacing(brand.SP_1)

        title = QLabel("KAPLAMA BARA DASHBOARD")
        title.setStyleSheet(
            f"font-size: {brand.FS_TITLE}px; font-weight: {brand.FW_BOLD}; "
            f"color: {brand.TEXT}; letter-spacing: -0.3px; "
            f"background: transparent; border: none;"
        )
        title_layout.addWidget(title)

        subtitle = QLabel("Canli Uretim Takip")
        subtitle.setStyleSheet(
            f"font-size: {brand.FS_BODY}px; color: {brand.TEXT_MUTED}; "
            f"background: transparent; border: none;"
        )
        title_layout.addWidget(subtitle)

        layout.addLayout(title_layout)
        layout.addStretch()

        # Saat + Durum
        status_layout = QVBoxLayout()
        status_layout.setSpacing(brand.SP_1)
        status_layout.setAlignment(Qt.AlignRight)

        self.time_label = QLabel(datetime.now().strftime('%H:%M:%S'))
        self.time_label.setStyleSheet(
            f"font-size: {brand.FS_DISPLAY}px; font-weight: {brand.FW_BOLD}; "
            f"color: {brand.PRIMARY}; font-family: {brand.FONT_MONO}; "
            f"background: transparent; border: none;"
        )
        status_layout.addWidget(self.time_label, alignment=Qt.AlignRight)

        self.status_label = QLabel("  CANLI")
        self.status_label.setStyleSheet(
            f"font-size: {brand.FS_BODY_SM}px; color: {brand.SUCCESS}; "
            f"font-weight: {brand.FW_BOLD}; letter-spacing: 0.8px; "
            f"background: transparent; border: none;"
        )
        status_layout.addWidget(self.status_label, alignment=Qt.AlignRight)

        layout.addLayout(status_layout)

        return frame

    def _create_mega_card(self, title, value, subtitle, color):
        card = QFrame()
        card.setObjectName("megaCard")
        card.setFixedHeight(brand.sp(200))

        layout = QVBoxLayout(card)
        layout.setContentsMargins(brand.SP_6, brand.SP_5, brand.SP_6, brand.SP_5)
        layout.setSpacing(brand.SP_3)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; letter-spacing: 1px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(title_label)

        # Deger
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(
            f"color: {color}; font-size: {brand.fs(72)}px; "
            f"font-weight: {brand.FW_BOLD}; letter-spacing: -2px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(value_label)

        # Alt yazi
        sub_label = QLabel(subtitle)
        sub_label.setObjectName("subtitle")
        sub_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(sub_label)

        card.setStyleSheet(f"""
            QFrame#megaCard {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-left: 4px solid {color};
                border-radius: {brand.R_LG}px;
            }}
        """)

        return card

    def _load_data(self):
        try:
            conn = get_plc_connection()
            if not conn:
                self.status_label.setText("  BAGLANTI YOK")
                self.status_label.setStyleSheet(
                    f"font-size: {brand.FS_BODY_SM}px; color: {brand.ERROR}; "
                    f"font-weight: {brand.FW_BOLD}; letter-spacing: 0.8px; "
                    f"background: transparent; border: none;"
                )
                return

            cursor = conn.cursor()

            # CANLI (Bugun)
            cursor.execute("""
                SELECT COUNT(*)
                FROM dbo.data
                WHERE KznNo IN (101, 201)
                  AND CAST(TarihDoldurma AS DATE) = CAST(GETDATE() AS DATE)
            """)
            canli_total = cursor.fetchone()[0]

            # KTL
            cursor.execute("""
                SELECT COUNT(*)
                FROM dbo.data
                WHERE KznNo = 101
                  AND CAST(TarihDoldurma AS DATE) = CAST(GETDATE() AS DATE)
            """)
            canli_ktl = cursor.fetchone()[0]

            # CINKO
            cursor.execute("""
                SELECT COUNT(*)
                FROM dbo.data
                WHERE KznNo = 201
                  AND CAST(TarihDoldurma AS DATE) = CAST(GETDATE() AS DATE)
            """)
            canli_cinko = cursor.fetchone()[0]

            # Kartlari guncelle
            self.card_canli.findChild(QLabel, "value").setText(f"{canli_total:,}")
            self.card_ktl.findChild(QLabel, "value").setText(f"{canli_ktl:,}")
            self.card_cinko.findChild(QLabel, "value").setText(f"{canli_cinko:,}")

            # Son 7 gun trend
            cursor.execute("""
                SELECT
                    CAST(TarihDoldurma AS DATE) AS gun,
                    SUM(CASE WHEN KznNo = 101 THEN 1 ELSE 0 END) AS ktl_bara,
                    SUM(CASE WHEN KznNo = 201 THEN 1 ELSE 0 END) AS cinko_bara,
                    COUNT(*) AS toplam
                FROM dbo.data
                WHERE KznNo IN (101, 201)
                  AND TarihDoldurma >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
                GROUP BY CAST(TarihDoldurma AS DATE)
                ORDER BY gun
            """)

            trend_data = cursor.fetchall()
            conn.close()

            # Grafikleri ciz
            self._draw_trend_bars(self.ktl_canvas, trend_data, col_idx=1, color=brand.SUCCESS)
            self._draw_trend_bars(self.cinko_canvas, trend_data, col_idx=2, color=brand.WARNING)
            self._draw_total_trend(trend_data)

            # Durum
            self.status_label.setText("  CANLI")
            self.status_label.setStyleSheet(
                f"font-size: {brand.FS_BODY_SM}px; color: {brand.SUCCESS}; "
                f"font-weight: {brand.FW_BOLD}; letter-spacing: 0.8px; "
                f"background: transparent; border: none;"
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Veri yukleme hatasi:\n{str(e)}")

    def _draw_trend_bars(self, canvas: MplCanvas, data, col_idx: int, color: str):
        canvas.axes.clear()
        canvas.axes.set_facecolor(brand.BG_CARD)
        canvas.axes.grid(True, alpha=0.18, color=brand.BORDER, linestyle='--')

        if not data:
            canvas.draw()
            return

        labels = [row[0].strftime('%d.%m') for row in data]
        values = [row[col_idx] for row in data]
        max_v = max(values) if values else 1

        x = range(len(labels))
        bars = canvas.axes.bar(x, values, color=color, alpha=0.9,
                               edgecolor=color, linewidth=2.0, width=0.7)

        for bar, v in zip(bars, values):
            height = bar.get_height()
            canvas.axes.text(
                bar.get_x() + bar.get_width() / 2.,
                height + max_v * 0.02,
                f'{int(v):,}',
                ha='center', va='bottom',
                color=brand.TEXT, fontsize=10, fontweight='bold'
            )

        canvas.axes.set_xticks(x)
        canvas.axes.set_xticklabels(labels, fontsize=10, color=brand.TEXT_MUTED)
        canvas.axes.set_ylabel('Bara Sayisi', color=brand.TEXT_MUTED, fontsize=10)
        canvas.axes.set_ylim(0, max_v * 1.2 if max_v else 1)

        canvas.fig.tight_layout()
        canvas.draw()

    def _draw_total_trend(self, data):
        self.total_canvas.axes.clear()
        self.total_canvas.axes.set_facecolor(brand.BG_CARD)
        self.total_canvas.axes.grid(True, alpha=0.18, color=brand.BORDER, linestyle='--')

        if not data:
            self.total_canvas.draw()
            return

        labels = [row[0].strftime('%d.%m') for row in data]
        ktl_values = [row[1] for row in data]
        cinko_values = [row[2] for row in data]

        x = range(len(labels))
        width = 0.65

        self.total_canvas.axes.bar(
            x, ktl_values, width, label='Kataforez',
            color=brand.SUCCESS, alpha=0.9, edgecolor=brand.SUCCESS, linewidth=1.5
        )
        self.total_canvas.axes.bar(
            x, cinko_values, width, bottom=ktl_values, label='Cinko',
            color=brand.WARNING, alpha=0.9, edgecolor=brand.WARNING, linewidth=1.5
        )

        totals = [k + c for k, c in zip(ktl_values, cinko_values)]
        max_t = max(totals) if totals else 1
        for i, total in enumerate(totals):
            self.total_canvas.axes.text(
                i, total + max_t * 0.02, f'{int(total):,}',
                ha='center', va='bottom', color=brand.TEXT,
                fontsize=11, fontweight='bold'
            )

        self.total_canvas.axes.set_xticks(x)
        self.total_canvas.axes.set_xticklabels(labels, fontsize=11, color=brand.TEXT_MUTED)
        self.total_canvas.axes.set_ylabel('Bara Sayisi', color=brand.TEXT_MUTED, fontsize=11)
        self.total_canvas.axes.set_ylim(0, max_t * 1.2 if max_t else 1)

        legend = self.total_canvas.axes.legend(
            loc='upper left', framealpha=0.9,
            facecolor=brand.BG_ELEVATED, edgecolor=brand.BORDER, fontsize=10
        )
        for text in legend.get_texts():
            text.set_color(brand.TEXT)

        self.total_canvas.fig.tight_layout()
        self.total_canvas.draw()

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT};
                font-family: {brand.FONT_FAMILY};
                font-size: {brand.FS_BODY}px;
            }}
        """)
