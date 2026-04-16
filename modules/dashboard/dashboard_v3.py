# -*- coding: utf-8 -*-
"""
NEXOR ERP - Dashboard v3 (Brand System)
Brand token'larla yazilmis, hem dark hem light temada dogru calisan dashboard.
"""
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)

from core.nexor_brand import brand
from core.database import get_db_connection


# =============================================================================
# ICON (QPainter monoline, tema-aware)
# =============================================================================

class BrandIcon(QLabel):
    def __init__(self, kind: str, color: str = None, size: int = None, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.color = color or brand.TEXT
        self.size_px = size or brand.ICON_MD
        self.setFixedSize(self.size_px, self.size_px)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(self.color))
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        s = self.size_px
        m = s * 0.18

        if self.kind == "trending-up":
            p.drawLine(int(m), int(s - m * 1.5), int(s * 0.42), int(s * 0.6))
            p.drawLine(int(s * 0.42), int(s * 0.6), int(s * 0.62), int(s * 0.75))
            p.drawLine(int(s * 0.62), int(s * 0.75), int(s - m), int(m * 1.5))
            p.drawLine(int(s - m), int(m * 1.5), int(s * 0.7), int(m * 1.5))
            p.drawLine(int(s - m), int(m * 1.5), int(s - m), int(s * 0.42))
        elif self.kind == "trending-down":
            p.drawLine(int(m), int(m * 1.5), int(s * 0.42), int(s * 0.42))
            p.drawLine(int(s * 0.42), int(s * 0.42), int(s * 0.62), int(s * 0.28))
            p.drawLine(int(s * 0.62), int(s * 0.28), int(s - m), int(s - m * 1.5))
            p.drawLine(int(s - m), int(s - m * 1.5), int(s * 0.7), int(s - m * 1.5))
            p.drawLine(int(s - m), int(s - m * 1.5), int(s - m), int(s * 0.58))
        elif self.kind == "box":
            p.drawRect(int(m), int(m), int(s - 2 * m), int(s - 2 * m))
            p.drawLine(int(m), int(s * 0.42), int(s - m), int(s * 0.42))
        elif self.kind == "truck":
            p.drawRect(int(m), int(s * 0.32), int(s * 0.5), int(s * 0.42))
            p.drawLine(int(s * 0.5 + m), int(s * 0.4), int(s * 0.72), int(s * 0.4))
            p.drawLine(int(s * 0.72), int(s * 0.4), int(s * 0.85), int(s * 0.55))
            p.drawLine(int(s * 0.85), int(s * 0.55), int(s - m), int(s * 0.55))
            p.drawLine(int(s - m), int(s * 0.55), int(s - m), int(s * 0.74))
            p.drawLine(int(m), int(s * 0.74), int(s - m), int(s * 0.74))
            p.setBrush(QBrush(QColor(self.color)))
            p.drawEllipse(int(s * 0.22), int(s * 0.76), int(s * 0.1), int(s * 0.1))
            p.drawEllipse(int(s * 0.72), int(s * 0.76), int(s * 0.1), int(s * 0.1))
        elif self.kind == "check":
            p.drawLine(int(s * 0.22), int(s * 0.5), int(s * 0.42), int(s * 0.7))
            p.drawLine(int(s * 0.42), int(s * 0.7), int(s * 0.78), int(s * 0.32))
        elif self.kind == "alert":
            p.drawLine(int(s * 0.5), int(m), int(s - m), int(s - m))
            p.drawLine(int(s - m), int(s - m), int(m), int(s - m))
            p.drawLine(int(m), int(s - m), int(s * 0.5), int(m))
            p.drawLine(int(s * 0.5), int(s * 0.38), int(s * 0.5), int(s * 0.62))
            p.setBrush(QBrush(QColor(self.color)))
            p.drawEllipse(int(s * 0.46), int(s * 0.7), 3, 3)
        elif self.kind == "clock":
            p.drawEllipse(int(m), int(m), int(s - 2 * m), int(s - 2 * m))
            p.drawLine(int(s * 0.5), int(s * 0.5), int(s * 0.5), int(s * 0.28))
            p.drawLine(int(s * 0.5), int(s * 0.5), int(s * 0.7), int(s * 0.5))
        elif self.kind == "activity":
            p.drawLine(int(m), int(s * 0.5), int(s * 0.3), int(s * 0.5))
            p.drawLine(int(s * 0.3), int(s * 0.5), int(s * 0.42), int(s * 0.2))
            p.drawLine(int(s * 0.42), int(s * 0.2), int(s * 0.58), int(s * 0.8))
            p.drawLine(int(s * 0.58), int(s * 0.8), int(s * 0.7), int(s * 0.5))
            p.drawLine(int(s * 0.7), int(s * 0.5), int(s - m), int(s * 0.5))
        p.end()


# =============================================================================
# KPI CARD
# =============================================================================

class KPICard(QFrame):
    def __init__(self, title, value, change, icon_kind, accent, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.change = change
        self.icon_kind = icon_kind
        self.accent = accent
        self.setObjectName("kpiCard")
        self.setFixedHeight(brand.sp(168))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame#kpiCard {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
            QFrame#kpiCard:hover {{
                border-color: {brand.BORDER_HARD};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(brand.SP_6, brand.SP_5, brand.SP_6, brand.SP_5)
        outer.setSpacing(brand.SP_3)

        # Ust satir
        top = QHBoxLayout()
        top.setSpacing(brand.SP_2)
        top.setContentsMargins(0, 0, 0, 0)

        self.title_lbl = QLabel(self.title.upper())
        self.title_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; letter-spacing: 0.8px;"
        )
        top.addWidget(self.title_lbl, 1, Qt.AlignLeft | Qt.AlignVCenter)

        self.icon_box = QFrame()
        self.icon_box.setObjectName("iconBox")
        self.icon_box.setFixedSize(brand.sp(32), brand.sp(32))
        self._restyle_icon_box()
        ib_layout = QVBoxLayout(self.icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        self.icon_widget = BrandIcon(self.icon_kind, self.accent, brand.sp(16))
        ib_layout.addWidget(self.icon_widget, 0, Qt.AlignCenter)
        top.addWidget(self.icon_box, 0, Qt.AlignRight | Qt.AlignVCenter)

        outer.addLayout(top)
        outer.addSpacing(brand.SP_2)

        # Deger
        self.value_lbl = QLabel(self.value)
        self.value_lbl.setMinimumHeight(brand.sp(44))
        self.value_lbl.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_DISPLAY}px; "
            f"font-weight: {brand.FW_BOLD}; letter-spacing: -0.6px;"
        )
        outer.addWidget(self.value_lbl)

        outer.addStretch()

        # Trend
        is_up = self.change.startswith('+')
        trend_color = brand.SUCCESS if is_up else brand.ERROR
        bot = QHBoxLayout()
        bot.setSpacing(brand.SP_2)
        bot.setContentsMargins(0, 0, 0, 0)

        self.trend_icon = BrandIcon("trending-up" if is_up else "trending-down",
                                    trend_color, brand.sp(14))
        bot.addWidget(self.trend_icon)

        self.change_lbl = QLabel(self.change)
        self.change_lbl.setStyleSheet(
            f"color: {trend_color}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        bot.addWidget(self.change_lbl)

        self.sub_lbl = QLabel("gecen aya gore")
        self.sub_lbl.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"
        )
        bot.addWidget(self.sub_lbl)

        bot.addStretch()
        outer.addLayout(bot)

    def _soft_bg(self, hex_color: str) -> str:
        c = QColor(hex_color)
        return f"rgba({c.red()},{c.green()},{c.blue()},0.12)"

    def _soft_border(self, hex_color: str) -> str:
        c = QColor(hex_color)
        return f"rgba({c.red()},{c.green()},{c.blue()},0.35)"

    def _restyle_icon_box(self):
        self.icon_box.setStyleSheet(
            f"QFrame#iconBox {{"
            f" background: {self._soft_bg(self.accent)};"
            f" border: 1px solid {self._soft_border(self.accent)};"
            f" border-radius: {brand.R_SM}px;"
            f"}}"
        )

    def update_theme(self, theme: dict = None):
        """Tema degisti — stilleri yeniden uygula."""
        self.setStyleSheet(f"""
            QFrame#kpiCard {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
            QFrame#kpiCard:hover {{ border-color: {brand.BORDER_HARD}; }}
            QLabel {{ background: transparent; border: none; }}
        """)
        self._restyle_icon_box()
        self.title_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; letter-spacing: 0.8px;"
        )
        self.value_lbl.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_DISPLAY}px; "
            f"font-weight: {brand.FW_BOLD}; letter-spacing: -0.6px;"
        )
        is_up = self.change.startswith('+')
        trend_color = brand.SUCCESS if is_up else brand.ERROR
        self.change_lbl.setStyleSheet(
            f"color: {trend_color}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        self.sub_lbl.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"
        )


# =============================================================================
# BADGE
# =============================================================================

def make_badge(text: str, color: str) -> QLabel:
    bg = QColor(color)
    badge = QLabel(text)
    badge.setAlignment(Qt.AlignCenter)
    badge.setStyleSheet(f"""
        color: {color};
        background: rgba({bg.red()},{bg.green()},{bg.blue()},0.12);
        border: 1px solid rgba({bg.red()},{bg.green()},{bg.blue()},0.4);
        border-radius: {brand.R_SM}px;
        padding: {brand.SP_1}px {brand.SP_3}px;
        font-size: {brand.FS_CAPTION}px;
        font-weight: {brand.FW_SEMIBOLD};
    """)
    badge.setFixedHeight(brand.sp(24))
    return badge


# =============================================================================
# DASHBOARD PAGE
# =============================================================================

class DashboardPageV3(QWidget):
    """Brand-aware Dashboard — hem dark hem light temada dogru calisir."""

    def __init__(self, theme: dict = None):
        super().__init__()
        self.theme = theme
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT};
                font-family: {brand.FONT_FAMILY};
                font-size: {brand.FS_BODY}px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background: {brand.BG_MAIN}; border: none; }}
            QScrollBar:vertical {{
                background: transparent;
                width: {brand.sp(8)}px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {brand.BORDER_HARD};
                border-radius: {brand.sp(4)}px;
                min-height: {brand.sp(30)}px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self.inner = QWidget()
        self.inner.setStyleSheet(f"background: {brand.BG_MAIN};")

        main = QVBoxLayout(self.inner)
        main.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        main.setSpacing(brand.SP_8)

        # ===== HEADER =====
        header = QHBoxLayout()
        header.setSpacing(brand.SP_4)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_2)
        self.title = QLabel("Gösterge Paneli")
        self.title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_TITLE_LG}px; "
            f"font-weight: {brand.FW_BOLD}; letter-spacing: -0.6px;"
        )
        title_col.addWidget(self.title)

        self.sub = QLabel("ATLAS KATAFOREZ — Üretim ve sevkiyat özeti")
        self.sub.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px;"
        )
        title_col.addWidget(self.sub)

        header.addLayout(title_col)
        header.addStretch()

        # Tarih rozeti
        self.date_badge = QLabel(
            datetime.now().strftime("%d %B %Y  •  %H:%M")
                    .replace("January", "Ocak").replace("February", "Şubat")
                    .replace("March", "Mart").replace("April", "Nisan")
                    .replace("May", "Mayıs").replace("June", "Haziran")
                    .replace("July", "Temmuz").replace("August", "Ağustos")
                    .replace("September", "Eylül").replace("October", "Ekim")
                    .replace("November", "Kasım").replace("December", "Aralık")
        )
        self.date_badge.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_SM}px; "
            f"padding: {brand.SP_2}px {brand.SP_4}px; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_MEDIUM};"
        )
        header.addWidget(self.date_badge)

        main.addLayout(header)

        # ===== KPI GRID =====
        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(brand.SP_4)

        self.kpi_cards = [
            KPICard("Toplam İrsaliye", "—", "+0%",   "box",      brand.INFO),
            KPICard("Bekleyen Sevk",   "—", "+0%",   "truck",    brand.WARNING),
            KPICard("Teslim Edildi",   "—", "+0%",   "check",    brand.SUCCESS),
            KPICard("Açık Arıza",      "—", "+0",    "alert",    brand.ERROR),
        ]
        for c in self.kpi_cards:
            self.kpi_row.addWidget(c)

        main.addLayout(self.kpi_row)

        # ===== SECTION HEADER =====
        main.addSpacing(brand.SP_2)
        sec_title = QLabel("Son İrsaliyeler")
        sec_title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; letter-spacing: -0.2px;"
        )
        main.addWidget(sec_title)

        sec_sub = QLabel("En son oluşturulan 10 sevk irsaliyesi")
        sec_sub.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;"
        )
        main.addWidget(sec_sub)
        self.sec_title = sec_title
        self.sec_sub = sec_sub

        # ===== TABLE =====
        self.table = self._build_table()
        main.addWidget(self.table)

        main.addStretch()
        self.scroll.setWidget(self.inner)
        root.addWidget(self.scroll)

    def _build_table(self) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(6)
        t.setHorizontalHeaderLabels([
            "İRSALİYE NO", "MÜŞTERİ", "TARİH", "PLAKA", "TOPLAM", "DURUM"
        ])
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setSelectionMode(QAbstractItemView.SingleSelection)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setShowGrid(False)
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setHighlightSections(False)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        t.verticalHeader().setDefaultSectionSize(brand.sp(44))
        t.setFrameShape(QFrame.NoFrame)
        t.setMinimumHeight(brand.sp(440))
        self._apply_table_style(t)
        return t

    def _apply_table_style(self, t: QTableWidget):
        t.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: 0;
                font-size: {brand.FS_BODY}px;
            }}
            QTableWidget::item {{
                padding: 0 {brand.SP_4}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
            }}
            QTableWidget::item:selected {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT};
            }}
            QHeaderView::section {{
                background: transparent;
                color: {brand.TEXT_DIM};
                padding: {brand.SP_3}px {brand.SP_4}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
                font-size: {brand.FS_CAPTION}px;
                font-weight: {brand.FW_SEMIBOLD};
                text-transform: uppercase;
                letter-spacing: 0.6px;
            }}
        """)

    # -----------------------------------------------------------------
    # DATA
    # -----------------------------------------------------------------

    def _load_data(self):
        try:
            self._load_kpis()
            self._load_son_irsaliyeler()
        except Exception as e:
            print(f"[Dashboard v3] Veri yukleme hatasi: {e}")

    def _load_kpis(self):
        """4 KPI'yi DB'den cek."""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Toplam irsaliye (bu ay)
            cur.execute("""
                SELECT COUNT(*) FROM siparis.cikis_irsaliyeleri
                WHERE YEAR(tarih) = YEAR(GETDATE())
                  AND MONTH(tarih) = MONTH(GETDATE())
                  AND ISNULL(silindi_mi,0) = 0
            """)
            toplam = cur.fetchone()[0] or 0

            # Bekleyen sevk
            cur.execute("""
                SELECT COUNT(*) FROM siparis.cikis_irsaliyeleri
                WHERE durum = 'HAZIRLANDI' AND ISNULL(silindi_mi,0) = 0
            """)
            bekleyen = cur.fetchone()[0] or 0

            # Teslim edildi (bu ay)
            cur.execute("""
                SELECT COUNT(*) FROM siparis.cikis_irsaliyeleri
                WHERE durum = 'TESLIM_EDILDI'
                  AND YEAR(tarih) = YEAR(GETDATE())
                  AND MONTH(tarih) = MONTH(GETDATE())
                  AND ISNULL(silindi_mi,0) = 0
            """)
            teslim = cur.fetchone()[0] or 0

            # Acik ariza
            try:
                cur.execute("""
                    SELECT COUNT(*) FROM bakim.ariza_bildirimleri
                    WHERE durum = 'ACIK'
                """)
                ariza = cur.fetchone()[0] or 0
            except Exception:
                ariza = 0

            conn.close()

            self.kpi_cards[0].value_lbl.setText(f"{toplam:,}".replace(",", "."))
            self.kpi_cards[1].value_lbl.setText(f"{bekleyen}")
            self.kpi_cards[2].value_lbl.setText(f"{teslim:,}".replace(",", "."))
            self.kpi_cards[3].value_lbl.setText(f"{ariza}")
        except Exception as e:
            print(f"[Dashboard v3] KPI hatasi: {e}")

    def _load_son_irsaliyeler(self):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT TOP 10
                    ci.irsaliye_no,
                    COALESCE(c.unvan, '') AS musteri,
                    ci.tarih,
                    ISNULL(ci.arac_plaka, '') AS plaka,
                    (SELECT COALESCE(SUM(cis.miktar), 0)
                     FROM siparis.cikis_irsaliye_satirlar cis
                     WHERE cis.irsaliye_id = ci.id) AS toplam,
                    ci.durum
                FROM siparis.cikis_irsaliyeleri ci
                LEFT JOIN musteri.cariler c ON ci.cari_id = c.id
                WHERE ISNULL(ci.silindi_mi, 0) = 0
                ORDER BY ci.id DESC
            """)
            rows = cur.fetchall()
            conn.close()

            durum_renk = {
                'HAZIRLANDI':    ('Hazırlandı',    brand.WARNING),
                'SEVK_EDILDI':   ('Yolda',         brand.INFO),
                'TESLIM_EDILDI': ('Teslim Edildi', brand.SUCCESS),
                'IPTAL':         ('İptal',         brand.ERROR),
            }

            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                no, musteri, tarih, plaka, toplam, durum = row
                tarih_str = tarih.strftime('%d.%m.%Y') if hasattr(tarih, 'strftime') else str(tarih or '')

                # Irsaliye no - monospace
                it = QTableWidgetItem(str(no or ''))
                font = QFont()
                font.setFamily("Consolas")
                font.setPointSize(brand.fs(10))
                it.setFont(font)
                it.setForeground(QColor(brand.TEXT_MUTED))
                self.table.setItem(r, 0, it)

                self.table.setItem(r, 1, QTableWidgetItem(str(musteri)[:45]))
                self.table.setItem(r, 2, QTableWidgetItem(tarih_str))
                self.table.setItem(r, 3, QTableWidgetItem(str(plaka)))

                miktar_it = QTableWidgetItem(f"{float(toplam):,.0f} AD".replace(",", "."))
                miktar_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                f = QFont()
                f.setBold(True)
                miktar_it.setFont(f)
                self.table.setItem(r, 4, miktar_it)

                durum_text, durum_color = durum_renk.get(
                    durum or '', (durum or '-', brand.TEXT_DIM)
                )
                self.table.setCellWidget(r, 5, make_badge(durum_text, durum_color))

            self.table.setColumnWidth(0, brand.sp(180))
            self.table.setColumnWidth(2, brand.sp(110))
            self.table.setColumnWidth(3, brand.sp(120))
            self.table.setColumnWidth(4, brand.sp(130))
            self.table.setColumnWidth(5, brand.sp(140))
        except Exception as e:
            print(f"[Dashboard v3] Irsaliye listesi hatasi: {e}")

    # -----------------------------------------------------------------
    # TEMA GUNCELLEME
    # -----------------------------------------------------------------

    def update_theme(self, theme: dict = None):
        self.theme = theme
        self.setStyleSheet(f"""
            QWidget {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT};
                font-family: {brand.FONT_FAMILY};
                font-size: {brand.FS_BODY}px;
            }}
        """)
        self.inner.setStyleSheet(f"background: {brand.BG_MAIN};")
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background: {brand.BG_MAIN}; border: none; }}
            QScrollBar:vertical {{
                background: transparent;
                width: {brand.sp(8)}px;
            }}
            QScrollBar::handle:vertical {{
                background: {brand.BORDER_HARD};
                border-radius: {brand.sp(4)}px;
                min-height: {brand.sp(30)}px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self.title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_TITLE_LG}px; "
            f"font-weight: {brand.FW_BOLD}; letter-spacing: -0.6px;"
        )
        self.sub.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px;"
        )
        self.date_badge.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_SM}px; "
            f"padding: {brand.SP_2}px {brand.SP_4}px; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_MEDIUM};"
        )
        self.sec_title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        self.sec_sub.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;"
        )

        for c in self.kpi_cards:
            c.update_theme()

        self._apply_table_style(self.table)
        # Durum badge'lerini yeniden cizmek icin listeyi yeniden yukle
        self._load_son_irsaliyeler()
