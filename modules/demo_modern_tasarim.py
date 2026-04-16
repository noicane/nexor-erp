# -*- coding: utf-8 -*-
"""
NEXOR ERP - Modern Tasarim Demo
Mevcut kodu hic etkilemez. Calistirmak icin:

    python -m modules.demo_modern_tasarim

veya

    python modules/demo_modern_tasarim.py

Gosterdigi seyler:
- Design tokens (renk, spacing, typography tek yerden)
- Ayri komponent: KPICard, SectionHeader, ModernTable
- Hierarchy: dusuk density, okunur tipografi, nefes alan spacing
- Renk sadece aksiyonu vurgulamak icin (gri = data, renk = anlam)
"""
import sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QPainterPath, QPen, QBrush
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSizePolicy, QScrollArea,
)


# =============================================================================
# DESIGN TOKENS - tek yerden kontrol edilir
# =============================================================================
class Tokens:
    # Renkler (shadcn/vercel/linear ilham)
    BG_MAIN      = "#0A0A0B"   # En dis
    BG_CARD      = "#111113"   # Kart arkaplan
    BG_HOVER     = "#18181B"
    BG_ELEVATED  = "#1A1A1D"

    BORDER       = "#1F1F23"
    BORDER_HARD  = "#2A2A2F"

    TEXT         = "#FAFAFA"   # Birincil
    TEXT_MUTED   = "#A1A1AA"   # Ikincil
    TEXT_DIM     = "#52525B"   # Tertiary

    ACCENT       = "#DC2626"   # Nexor kirmizi
    ACCENT_SOFT  = "#450A0A"

    GREEN        = "#10B981"
    GREEN_SOFT   = "#064E3B"
    YELLOW       = "#F59E0B"
    YELLOW_SOFT  = "#451A03"
    BLUE         = "#3B82F6"
    BLUE_SOFT    = "#1E3A5F"
    PURPLE       = "#8B5CF6"
    PURPLE_SOFT  = "#2E1065"

    # Spacing - 4 tabanli grid
    SP_1 = 4
    SP_2 = 8
    SP_3 = 12
    SP_4 = 16
    SP_5 = 20
    SP_6 = 24
    SP_8 = 32
    SP_10 = 40

    # Typography
    FONT_FAMILY  = "'Inter', 'Segoe UI', system-ui, sans-serif"
    FS_CAPTION   = 11
    FS_BODY_SM   = 12
    FS_BODY      = 13
    FS_BODY_LG   = 15
    FS_HEADING   = 18
    FS_TITLE     = 24
    FS_DISPLAY   = 32

    RADIUS_SM    = 6
    RADIUS_MD    = 10
    RADIUS_LG    = 14


T = Tokens


# =============================================================================
# BASIT SVG ICON - emoji yerine temiz cizgiler (QPainter)
# =============================================================================
class Icon(QLabel):
    """Basit monoline icon - QPainter ile cizilir, emoji degil."""
    def __init__(self, kind: str, color: str = T.TEXT, size: int = 18, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.color = color
        self.setFixedSize(size, size)
        self.size_px = size

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
        m = s * 0.18  # margin

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
            path = QPainterPath()
            path.moveTo(s * 0.5, m)
            path.lineTo(s - m, s - m)
            path.lineTo(m, s - m)
            path.closeSubpath()
            p.drawPath(path)
            p.drawLine(int(s * 0.5), int(s * 0.38), int(s * 0.5), int(s * 0.62))
            p.setBrush(QBrush(QColor(self.color)))
            p.drawEllipse(int(s * 0.46), int(s * 0.7), 3, 3)
        elif self.kind == "users":
            p.drawEllipse(int(s * 0.2), int(s * 0.15), int(s * 0.3), int(s * 0.3))
            p.drawArc(int(s * 0.1), int(s * 0.45), int(s * 0.5), int(s * 0.5), 0, 180 * 16)
            p.drawEllipse(int(s * 0.55), int(s * 0.22), int(s * 0.22), int(s * 0.22))
        p.end()


# =============================================================================
# KPI CARD - TEK GERCEK COMPONENT
# =============================================================================
class KPICard(QFrame):
    """Linear/Vercel tarzi KPI karti: baslik sol, ikon sag, nefes alan layout."""

    def __init__(self, title: str, value: str, change: str,
                 icon_kind: str, accent: str, parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        self.setFixedHeight(168)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QFrame#kpiCard {{
                background: {T.BG_CARD};
                border: 1px solid {T.BORDER};
                border-radius: {T.RADIUS_LG}px;
            }}
            QFrame#kpiCard:hover {{
                border-color: {T.BORDER_HARD};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(T.SP_6, T.SP_5, T.SP_6, T.SP_5)
        outer.setSpacing(T.SP_3)

        # ---- 1. Satir: baslik (sol) + ikon (sag) ----
        top = QHBoxLayout()
        top.setSpacing(T.SP_2)
        top.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet(
            f"color: {T.TEXT_MUTED}; font-size: {T.FS_CAPTION}px; "
            f"font-weight: 600; letter-spacing: 0.8px;"
        )
        top.addWidget(title_lbl, 1, Qt.AlignLeft | Qt.AlignVCenter)

        icon_box = QFrame()
        icon_box.setObjectName("iconBox")
        icon_box.setFixedSize(32, 32)
        icon_box.setStyleSheet(
            f"QFrame#iconBox {{"
            f" background: {self._soft(accent)};"
            f" border: 1px solid {self._soft_border(accent)};"
            f" border-radius: {T.RADIUS_SM}px;"
            f"}}"
        )
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ib_layout.addWidget(Icon(icon_kind, accent, 16), 0, Qt.AlignCenter)
        top.addWidget(icon_box, 0, Qt.AlignRight | Qt.AlignVCenter)

        outer.addLayout(top)

        # ---- 2. Satir: Ana deger (buyuk rakam) ----
        outer.addSpacing(T.SP_2)
        value_lbl = QLabel(value)
        value_lbl.setMinimumHeight(44)
        value_lbl.setStyleSheet(
            f"color: {T.TEXT}; font-size: {T.FS_DISPLAY}px; "
            f"font-weight: 700; letter-spacing: -0.6px;"
        )
        outer.addWidget(value_lbl)

        # ---- 3. Satir: Trend ----
        outer.addStretch()
        is_up = change.startswith('+')
        trend_color = T.GREEN if is_up else T.ACCENT
        bot = QHBoxLayout()
        bot.setSpacing(T.SP_2)
        bot.setContentsMargins(0, 0, 0, 0)

        bot.addWidget(Icon("trending-up" if is_up else "trending-down", trend_color, 14))

        change_lbl = QLabel(change)
        change_lbl.setStyleSheet(
            f"color: {trend_color}; font-size: {T.FS_BODY_SM}px; font-weight: 600;"
        )
        bot.addWidget(change_lbl)

        sub = QLabel("gecen aya gore")
        sub.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: {T.FS_CAPTION}px;")
        bot.addWidget(sub)

        bot.addStretch()
        outer.addLayout(bot)

    @staticmethod
    def _soft(hex_color: str) -> str:
        c = QColor(hex_color)
        return f"rgba({c.red()},{c.green()},{c.blue()},0.12)"

    @staticmethod
    def _soft_border(hex_color: str) -> str:
        c = QColor(hex_color)
        return f"rgba({c.red()},{c.green()},{c.blue()},0.35)"


# =============================================================================
# SECTION HEADER
# =============================================================================
class SectionHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(T.SP_1)

        t = QLabel(title)
        t.setStyleSheet(
            f"color: {T.TEXT}; font-size: {T.FS_HEADING}px; font-weight: 600; "
            f"letter-spacing: -0.2px;"
        )
        layout.addWidget(t)

        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet(f"color: {T.TEXT_MUTED}; font-size: {T.FS_BODY_SM}px;")
            layout.addWidget(s)


# =============================================================================
# MODERN TABLE
# =============================================================================
class ModernTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.horizontalHeader().setHighlightSections(False)
        self.setFrameShape(QFrame.NoFrame)
        self.verticalHeader().setDefaultSectionSize(48)  # nefes alan satir

        self.setStyleSheet(f"""
            QTableWidget {{
                background: {T.BG_CARD};
                color: {T.TEXT};
                border: 1px solid {T.BORDER};
                border-radius: {T.RADIUS_LG}px;
                outline: 0;
                font-size: {T.FS_BODY}px;
            }}
            QTableWidget::item {{
                padding: 0 {T.SP_4}px;
                border: none;
                border-bottom: 1px solid {T.BORDER};
            }}
            QTableWidget::item:selected {{
                background: {T.BG_HOVER};
                color: {T.TEXT};
            }}
            QHeaderView::section {{
                background: transparent;
                color: {T.TEXT_DIM};
                padding: {T.SP_3}px {T.SP_4}px;
                border: none;
                border-bottom: 1px solid {T.BORDER};
                font-size: {T.FS_CAPTION}px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.6px;
            }}
        """)


# =============================================================================
# BADGE - durum gostergesi
# =============================================================================
def make_badge(text: str, color: str) -> QLabel:
    bg = QColor(color)
    badge = QLabel(text)
    badge.setAlignment(Qt.AlignCenter)
    badge.setStyleSheet(f"""
        color: {color};
        background: rgba({bg.red()},{bg.green()},{bg.blue()},0.12);
        border: 1px solid rgba({bg.red()},{bg.green()},{bg.blue()},0.4);
        border-radius: {T.RADIUS_SM}px;
        padding: 4px 10px;
        font-size: {T.FS_CAPTION}px;
        font-weight: 600;
    """)
    badge.setFixedHeight(24)
    return badge


# =============================================================================
# DEMO PAGE
# =============================================================================
class DemoPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            QWidget {{
                background: {T.BG_MAIN};
                color: {T.TEXT};
                font-family: {T.FONT_FAMILY};
                font-size: {T.FS_BODY}px;
            }}
        """)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {T.BG_MAIN}; border: none; }}")

        inner = QWidget()
        main = QVBoxLayout(inner)
        main.setContentsMargins(T.SP_10, T.SP_10, T.SP_10, T.SP_10)
        main.setSpacing(T.SP_8)

        # ============ HEADER ============
        header = QHBoxLayout()
        header.setSpacing(T.SP_4)

        title_col = QVBoxLayout()
        title_col.setSpacing(T.SP_2)
        title = QLabel("Sevkiyat Yönetimi")
        title.setStyleSheet(
            f"color: {T.TEXT}; font-size: 28px; font-weight: 700; "
            f"letter-spacing: -0.6px; padding: 0;"
        )
        title_col.addWidget(title)
        sub = QLabel("İrsaliyeleri takip et, durumlarını yönet")
        sub.setStyleSheet(
            f"color: {T.TEXT_MUTED}; font-size: {T.FS_BODY}px; padding: 0;"
        )
        title_col.addWidget(sub)

        header.addLayout(title_col)
        header.addStretch()

        # CTA
        cta = QLabel("+  Yeni İrsaliye")
        cta.setAlignment(Qt.AlignCenter)
        cta.setFixedHeight(38)
        cta.setStyleSheet(f"""
            background: {T.ACCENT};
            color: white;
            border-radius: {T.RADIUS_SM}px;
            padding: 0 {T.SP_5}px;
            font-size: {T.FS_BODY}px;
            font-weight: 600;
        """)
        header.addWidget(cta)

        main.addLayout(header)

        # ============ KPI GRID ============
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(T.SP_4)
        kpi_row.addWidget(KPICard("Toplam İrsaliye", "1.284", "+12.5%", "box",   T.BLUE))
        kpi_row.addWidget(KPICard("Sevkiyat Bekleyen", "47", "-3.2%",  "truck", T.YELLOW))
        kpi_row.addWidget(KPICard("Teslim Edildi",    "1.137", "+8.1%", "check", T.GREEN))
        kpi_row.addWidget(KPICard("Geciken",          "12", "+2",      "alert", T.ACCENT))
        main.addLayout(kpi_row)

        # ============ SECTION ============
        main.addSpacing(T.SP_2)
        main.addWidget(SectionHeader("Son İrsaliyeler", "En son 8 sevk irsaliyesi"))

        # ============ TABLE ============
        table = ModernTable()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "İRSALİYE NO", "MÜŞTERİ", "TARİH", "PLAKA", "TOPLAM", "DURUM"
        ])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        data = [
            ("IRO2026-000000562", "Ford Otosan San. Tic. A.Ş.",   "14.04.2026", "34 BDE 712", "1.247 AD",  ("Teslim Edildi", T.GREEN)),
            ("IRO2026-000000561", "Orau Orhan Otomotiv",          "14.04.2026", "16 KRL 88",  "812 AD",    ("Yolda", T.BLUE)),
            ("IRO2026-000000560", "Beleon Kimya",                 "13.04.2026", "34 HZT 44",  "2.130 AD",  ("Teslim Edildi", T.GREEN)),
            ("IRO2026-000000559", "Farplas Oto Yedek Parça",      "13.04.2026", "16 AS 4401", "540 AD",    ("Hazırlandı", T.YELLOW)),
            ("IRO2026-000000558", "Tofaş Türk Otomobil",          "13.04.2026", "34 NXR 01",  "3.200 AD",  ("Teslim Edildi", T.GREEN)),
            ("IRO2026-000000557", "BMC Truck & Bus",              "12.04.2026", "35 BMC 55",  "187 AD",    ("Gecikti", T.ACCENT)),
            ("IRO2026-000000556", "Hidromek",                     "12.04.2026", "06 HM 2312", "456 AD",    ("Yolda", T.BLUE)),
            ("IRO2026-000000555", "Coşkunöz Metal Form",          "12.04.2026", "16 CM 908",  "910 AD",    ("Teslim Edildi", T.GREEN)),
        ]
        table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row[:-1]):
                it = QTableWidgetItem(val)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                if c == 0:
                    font = QFont()
                    font.setFamily("Consolas")
                    font.setPointSize(10)
                    it.setFont(font)
                    it.setForeground(QColor(T.TEXT_MUTED))
                elif c == 4:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    font = QFont()
                    font.setBold(True)
                    it.setFont(font)
                table.setItem(r, c, it)
            # Durum badge
            durum_text, durum_color = row[-1]
            table.setCellWidget(r, 5, make_badge(durum_text, durum_color))

        table.setColumnWidth(0, 180)
        table.setColumnWidth(2, 110)
        table.setColumnWidth(3, 120)
        table.setColumnWidth(4, 110)
        table.setColumnWidth(5, 140)
        table.setFixedHeight(table.verticalHeader().defaultSectionSize() * 8 + 60)

        main.addWidget(table)
        main.addStretch()

        scroll.setWidget(inner)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    # Inter varsa kullan
    try:
        from PySide6.QtGui import QFontDatabase
        fams = QFontDatabase.families()
        if "Inter" in fams:
            app.setFont(QFont("Inter", 10))
        else:
            app.setFont(QFont("Segoe UI", 10))
    except Exception:
        pass

    w = DemoPage()
    w.setWindowTitle("NEXOR Modern Tasarim Demo")
    w.resize(1400, 900)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
