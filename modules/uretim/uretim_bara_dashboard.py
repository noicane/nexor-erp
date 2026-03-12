# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kaplama Bara Dashboard (Canlı)
Kaplama hattı canlı üretim takip - bara sayıları ve trendler
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from datetime import datetime

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from components.nexor_components import get_theme_colors
from core.database import get_plc_connection


class MplCanvas(FigureCanvasQTAgg):
    """Matplotlib grafik canvas'ı"""
    def __init__(self, parent=None, width=6, height=4, dpi=100, bg_color='#1E1E1E'):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=bg_color)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

        self.fig.patch.set_facecolor(bg_color)
        self.axes.set_facecolor('#1A1A1A')
        self.axes.tick_params(colors='#AAAAAA', labelsize=9)
        self.axes.spines['bottom'].set_color('#2A2A2A')
        self.axes.spines['left'].set_color('#2A2A2A')
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.grid(True, alpha=0.1, color='#2A2A2A', linestyle='--')


class BaraDashboardPage(QWidget):
    """Kaplama Bara Dashboard - Canlı üretim takip"""

    def __init__(self, theme: dict):
        super().__init__()
        self.theme = get_theme_colors(theme)

        self.colors = {
            'bg': self.theme.get('bg', '#0F0F0F'),
            'card': self.theme.get('card_bg', '#1E1E1E'),
            'border': self.theme.get('border', '#2A2A2A'),
            'text': self.theme.get('text', '#FFFFFF'),
            'text_muted': self.theme.get('text_secondary', '#AAAAAA'),
            'primary': self.theme.get('primary', '#DC2626'),
            'success': self.theme.get('success', '#10B981'),
            'warning': self.theme.get('warning', '#F59E0B'),
            'info': self.theme.get('info', '#3B82F6'),
        }

        self._setup_ui()
        self._apply_styles()

        # İlk veri yükleme
        QTimer.singleShot(200, self._load_data)

        # Otomatik yenileme (30 saniye)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_data)
        self.refresh_timer.start(30000)

    def on_page_shown(self):
        """Sayfa gösterildiğinde veriyi yenile"""
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Üst Kartlar (3 büyük kart)
        top_cards = QHBoxLayout()
        top_cards.setSpacing(20)

        self.card_canli = self._create_mega_card(
            "CANLI URETIM", "0", "Bugun 00:00'dan Itibaren",
            self.colors['primary'], "#2A1A1A"
        )
        self.card_ktl = self._create_mega_card(
            "KATAFOREZ", "0", "Kazan 101",
            self.colors['success'], "#1A2A1A"
        )
        self.card_cinko = self._create_mega_card(
            "CINKO", "0", "Kazan 201",
            self.colors['warning'], "#2A2A1A"
        )

        top_cards.addWidget(self.card_canli)
        top_cards.addWidget(self.card_ktl)
        top_cards.addWidget(self.card_cinko)

        layout.addLayout(top_cards)

        # Grafikler
        graphs = QHBoxLayout()
        graphs.setSpacing(20)

        # Kataforez Trend
        ktl_frame = QFrame()
        ktl_layout = QVBoxLayout(ktl_frame)
        ktl_layout.setContentsMargins(20, 15, 20, 15)
        ktl_layout.setSpacing(10)

        ktl_title = QLabel("KATAFOREZ TREND")
        ktl_title.setStyleSheet(f"color: {self.colors['success']}; font-size: 15px; font-weight: bold;")
        ktl_layout.addWidget(ktl_title)

        ktl_subtitle = QLabel("Son 7 Gun")
        ktl_subtitle.setStyleSheet(f"color: {self.colors['text_muted']}; font-size: 11px;")
        ktl_layout.addWidget(ktl_subtitle)

        self.ktl_canvas = MplCanvas(self, width=7, height=4.5, dpi=100, bg_color=self.colors['card'])
        ktl_layout.addWidget(self.ktl_canvas)

        graphs.addWidget(ktl_frame)

        # Çinko Trend
        cinko_frame = QFrame()
        cinko_layout = QVBoxLayout(cinko_frame)
        cinko_layout.setContentsMargins(20, 15, 20, 15)
        cinko_layout.setSpacing(10)

        cinko_title = QLabel("CINKO TREND")
        cinko_title.setStyleSheet(f"color: {self.colors['warning']}; font-size: 15px; font-weight: bold;")
        cinko_layout.addWidget(cinko_title)

        cinko_subtitle = QLabel("Son 7 Gun")
        cinko_subtitle.setStyleSheet(f"color: {self.colors['text_muted']}; font-size: 11px;")
        cinko_layout.addWidget(cinko_subtitle)

        self.cinko_canvas = MplCanvas(self, width=7, height=4.5, dpi=100, bg_color=self.colors['card'])
        cinko_layout.addWidget(self.cinko_canvas)

        graphs.addWidget(cinko_frame)

        layout.addLayout(graphs, 1)

        # Alt: Toplam Trend
        total_frame = QFrame()
        total_layout = QVBoxLayout(total_frame)
        total_layout.setContentsMargins(20, 15, 20, 15)
        total_layout.setSpacing(10)

        total_title = QLabel("TOPLAM URETIM TRENDI")
        total_title.setStyleSheet(f"color: {self.colors['primary']}; font-size: 15px; font-weight: bold;")
        total_layout.addWidget(total_title)

        total_subtitle = QLabel("Son 7 Gun - Kataforez + Cinko")
        total_subtitle.setStyleSheet(f"color: {self.colors['text_muted']}; font-size: 11px;")
        total_layout.addWidget(total_subtitle)

        self.total_canvas = MplCanvas(self, width=14, height=4, dpi=100, bg_color=self.colors['card'])
        total_layout.addWidget(self.total_canvas)

        layout.addWidget(total_frame)

    def _create_header(self):
        frame = QFrame()
        frame.setFixedHeight(90)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)

        # Başlık
        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)

        title = QLabel("KAPLAMA BARA DASHBOARD")
        title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {self.colors['primary']};")
        title_layout.addWidget(title)

        subtitle = QLabel("Canli Uretim Takip")
        subtitle.setStyleSheet(f"font-size: 13px; color: {self.colors['text_muted']};")
        title_layout.addWidget(subtitle)

        layout.addLayout(title_layout)
        layout.addStretch()

        # Saat + Durum
        status_layout = QVBoxLayout()
        status_layout.setSpacing(5)
        status_layout.setAlignment(Qt.AlignRight)

        self.time_label = QLabel()
        self.time_label.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {self.colors['primary']};")
        status_layout.addWidget(self.time_label, alignment=Qt.AlignRight)

        self.status_label = QLabel("CANLI")
        self.status_label.setStyleSheet(f"font-size: 12px; color: {self.colors['success']}; font-weight: bold;")
        status_layout.addWidget(self.status_label, alignment=Qt.AlignRight)

        layout.addLayout(status_layout)

        return frame

    def _create_mega_card(self, title, value, subtitle, color, bg_color):
        card = QFrame()
        card.setFixedHeight(200)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        # Title
        header = QHBoxLayout()
        header.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {self.colors['text_muted']}; font-size: 14px; font-weight: 600; letter-spacing: 1px;")
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)

        # Değer
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"""
            color: {color};
            font-size: 72px;
            font-weight: bold;
            letter-spacing: -2px;
        """)
        layout.addWidget(value_label)

        # Alt yazı
        sub_label = QLabel(subtitle)
        sub_label.setObjectName("subtitle")
        sub_label.setStyleSheet(f"color: {self.colors['text_muted']}; font-size: 12px;")
        layout.addWidget(sub_label)

        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {bg_color}, stop:1 {self.colors['card']});
                border: 2px solid {color};
                border-radius: 15px;
            }}
        """)

        return card

    def _load_data(self):
        try:
            conn = get_plc_connection()
            if not conn:
                self.status_label.setText("BAGLANTI YOK")
                self.status_label.setStyleSheet("font-size: 12px; color: #EF4444; font-weight: bold;")
                return

            cursor = conn.cursor()

            # CANLI (Bugün)
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

            # ÇINKO
            cursor.execute("""
                SELECT COUNT(*)
                FROM dbo.data
                WHERE KznNo = 201
                  AND CAST(TarihDoldurma AS DATE) = CAST(GETDATE() AS DATE)
            """)
            canli_cinko = cursor.fetchone()[0]

            # Kartları güncelle
            self.card_canli.findChild(QLabel, "value").setText(f"{canli_total:,}")
            self.card_ktl.findChild(QLabel, "value").setText(f"{canli_ktl:,}")
            self.card_cinko.findChild(QLabel, "value").setText(f"{canli_cinko:,}")

            # Son 7 gün trend
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

            # Grafikleri çiz
            self._draw_ktl_trend(trend_data)
            self._draw_cinko_trend(trend_data)
            self._draw_total_trend(trend_data)

            # Saat + Durum
            self.time_label.setText(datetime.now().strftime('%H:%M:%S'))
            self.status_label.setText("CANLI")
            self.status_label.setStyleSheet(f"font-size: 12px; color: {self.colors['success']}; font-weight: bold;")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Veri yukleme hatasi:\n{str(e)}")

    def _draw_ktl_trend(self, data):
        self.ktl_canvas.axes.clear()
        self.ktl_canvas.axes.set_facecolor('#1A1A1A')
        self.ktl_canvas.axes.grid(True, alpha=0.1, color='#2A2A2A', linestyle='--')

        if not data:
            self.ktl_canvas.draw()
            return

        labels = [row[0].strftime('%d.%m') for row in data]
        values = [row[1] for row in data]

        x = range(len(labels))
        bars = self.ktl_canvas.axes.bar(x, values, color='#00E676', alpha=0.9,
                                        edgecolor='#00C853', linewidth=2.5, width=0.7)

        for bar, v in zip(bars, values):
            height = bar.get_height()
            self.ktl_canvas.axes.text(bar.get_x() + bar.get_width() / 2., height + max(values) * 0.02,
                                      f'{int(v):,}', ha='center', va='bottom',
                                      color='#FFFFFF', fontsize=11, fontweight='bold')

        self.ktl_canvas.axes.set_xticks(x)
        self.ktl_canvas.axes.set_xticklabels(labels, fontsize=10, color='#AAAAAA')
        self.ktl_canvas.axes.set_ylabel('Bara Sayisi', color='#AAAAAA', fontsize=10)
        self.ktl_canvas.axes.set_ylim(0, max(values) * 1.2 if values else 1)

        self.ktl_canvas.fig.tight_layout()
        self.ktl_canvas.draw()

    def _draw_cinko_trend(self, data):
        self.cinko_canvas.axes.clear()
        self.cinko_canvas.axes.set_facecolor('#1A1A1A')
        self.cinko_canvas.axes.grid(True, alpha=0.1, color='#2A2A2A', linestyle='--')

        if not data:
            self.cinko_canvas.draw()
            return

        labels = [row[0].strftime('%d.%m') for row in data]
        values = [row[2] for row in data]

        x = range(len(labels))
        bars = self.cinko_canvas.axes.bar(x, values, color='#FFB800', alpha=0.9,
                                          edgecolor='#FF8F00', linewidth=2.5, width=0.7)

        for bar, v in zip(bars, values):
            height = bar.get_height()
            self.cinko_canvas.axes.text(bar.get_x() + bar.get_width() / 2., height + max(values) * 0.02,
                                        f'{int(v):,}', ha='center', va='bottom',
                                        color='#FFFFFF', fontsize=11, fontweight='bold')

        self.cinko_canvas.axes.set_xticks(x)
        self.cinko_canvas.axes.set_xticklabels(labels, fontsize=10, color='#AAAAAA')
        self.cinko_canvas.axes.set_ylabel('Bara Sayisi', color='#AAAAAA', fontsize=10)
        self.cinko_canvas.axes.set_ylim(0, max(values) * 1.2 if values else 1)

        self.cinko_canvas.fig.tight_layout()
        self.cinko_canvas.draw()

    def _draw_total_trend(self, data):
        self.total_canvas.axes.clear()
        self.total_canvas.axes.set_facecolor('#1A1A1A')
        self.total_canvas.axes.grid(True, alpha=0.1, color='#2A2A2A', linestyle='--')

        if not data:
            self.total_canvas.draw()
            return

        labels = [row[0].strftime('%d.%m') for row in data]
        ktl_values = [row[1] for row in data]
        cinko_values = [row[2] for row in data]

        x = range(len(labels))
        width = 0.65

        bars1 = self.total_canvas.axes.bar(x, ktl_values, width, label='Kataforez',
                                           color='#00E676', alpha=0.9, edgecolor='#00C853', linewidth=2)
        bars2 = self.total_canvas.axes.bar(x, cinko_values, width, bottom=ktl_values, label='Cinko',
                                           color='#FFB800', alpha=0.9, edgecolor='#FF8F00', linewidth=2)

        totals = [k + c for k, c in zip(ktl_values, cinko_values)]
        for i, total in enumerate(totals):
            self.total_canvas.axes.text(i, total + max(totals) * 0.02, f'{int(total):,}',
                                        ha='center', va='bottom', color='#FFFFFF', fontsize=12, fontweight='bold')

        self.total_canvas.axes.set_xticks(x)
        self.total_canvas.axes.set_xticklabels(labels, fontsize=11, color='#AAAAAA')
        self.total_canvas.axes.set_ylabel('Bara Sayisi', color='#AAAAAA', fontsize=11)
        self.total_canvas.axes.set_ylim(0, max(totals) * 1.2 if totals else 1)

        legend = self.total_canvas.axes.legend(loc='upper left', framealpha=0.9,
                                               facecolor='#1E1E1E', edgecolor='#2A2A2A', fontsize=10)
        for text in legend.get_texts():
            text.set_color('#FFFFFF')

        self.total_canvas.fig.tight_layout()
        self.total_canvas.draw()

    def _apply_styles(self):
        c = self.colors
        self.setStyleSheet(f"""
            QLabel {{
                color: {c['text']};
            }}
            QFrame {{
                background: {c['card']};
                border: 1px solid {c['border']};
                border-radius: 15px;
            }}
        """)
