# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kaplama Planlama Gantt Widget
[KURUMSAL UI - v2.0]

QPainter ile ozel Gantt cizelgesi
"""
from typing import List, Optional, Callable
from PySide6.QtWidgets import QWidget, QToolTip, QMenu
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QSize
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QPainterPath, QLinearGradient, QMouseEvent, QPaintEvent
)
from .models import PlanGorev, BARA_SAYISI, VARDIYA_SURE_DK, VARDIYA_SAYISI, GUN_SAYISI


# ── Renk Sabitleri ──
COLOR_ZN = QColor("#F59E0B")
COLOR_ZN_NI = QColor("#3B82F6")
COLOR_ACIL = QColor("#EF4444")
COLOR_GRID = QColor("#1E2736")
COLOR_HEADER_BG = QColor("#111822")
COLOR_BG = QColor("#0F1419")
COLOR_TEXT = QColor("#E8ECF1")
COLOR_TEXT_DIM = QColor("#8896A6")
COLOR_TEXT_MUTED = QColor("#5C6878")
COLOR_VARDIYA_1 = QColor("#151B23")
COLOR_VARDIYA_2 = QColor("#131920")
COLOR_VARDIYA_3 = QColor("#11171E")
COLOR_HOVER = QColor(255, 255, 255, 25)
COLOR_PRIMARY = QColor("#DC2626")

GUN_ISIMLERI = ["Pzt", "Sal", "Car", "Per", "Cum", "Cmt", "Paz"]
VARDIYA_ISIMLERI = ["V1", "V2", "V3"]

# ── Layout Sabitleri ──
HEADER_HEIGHT = 52
ROW_HEADER_WIDTH = 70
ROW_HEIGHT = 48
MIN_BLOCK_WIDTH = 4


class GanttWidget(QWidget):
    """Haftalik Gantt cizelgesi widget'i"""

    gorev_secildi = Signal(object)
    gorev_silindi = Signal(object)
    gorev_duzenlendi = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._gorevler: List[PlanGorev] = []
        self._hover_gorev: Optional[PlanGorev] = None
        self._selected_gorev: Optional[PlanGorev] = None
        self.setMouseTracking(True)
        self.setMinimumSize(800, HEADER_HEIGHT + BARA_SAYISI * ROW_HEIGHT + 20)

    def set_gorevler(self, gorevler: List[PlanGorev]):
        self._gorevler = gorevler
        self._hover_gorev = None
        self._selected_gorev = None
        self.update()

    def get_gorevler(self) -> List[PlanGorev]:
        return self._gorevler

    def sizeHint(self) -> QSize:
        return QSize(1200, HEADER_HEIGHT + BARA_SAYISI * ROW_HEIGHT + 20)

    # ─── Koordinat hesaplama ───

    def _content_width(self) -> int:
        return self.width() - ROW_HEADER_WIDTH

    def _slot_count(self) -> int:
        return GUN_SAYISI * VARDIYA_SAYISI

    def _slot_width(self) -> float:
        return self._content_width() / self._slot_count()

    def _gorev_rect(self, g: PlanGorev) -> QRect:
        slot_idx = g.gun * VARDIYA_SAYISI + (g.vardiya - 1)
        sw = self._slot_width()
        x_offset = (g.baslangic_dk / VARDIYA_SURE_DK) * sw
        block_w = (g.sure_dk / VARDIYA_SURE_DK) * sw

        x = ROW_HEADER_WIDTH + slot_idx * sw + x_offset
        y = HEADER_HEIGHT + (g.bara_no - 1) * ROW_HEIGHT + 4
        w = max(block_w, MIN_BLOCK_WIDTH)
        h = ROW_HEIGHT - 8

        return QRect(int(x), int(y), int(w), int(h))

    def _gorev_at(self, pos: QPoint) -> Optional[PlanGorev]:
        for g in reversed(self._gorevler):
            if self._gorev_rect(g).contains(pos):
                return g
        return None

    # ─── Cizim ───

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), COLOR_BG)
        self._draw_header(p)
        self._draw_grid(p)
        self._draw_gorevler(p)
        p.end()

    def _draw_header(self, p: QPainter):
        sw = self._slot_width()
        font_day = QFont("Segoe UI", 10, QFont.Bold)
        font_var = QFont("Segoe UI", 8)

        # Gun basliklari
        for gun in range(GUN_SAYISI):
            x = ROW_HEADER_WIDTH + gun * VARDIYA_SAYISI * sw
            w = VARDIYA_SAYISI * sw
            rect = QRect(int(x), 0, int(w), 26)
            p.fillRect(rect, COLOR_HEADER_BG)
            p.setPen(COLOR_GRID)
            p.drawRect(rect)
            p.setFont(font_day)
            p.setPen(COLOR_TEXT)
            p.drawText(rect, Qt.AlignCenter, GUN_ISIMLERI[gun])

        # Vardiya basliklari
        for slot in range(self._slot_count()):
            x = ROW_HEADER_WIDTH + slot * sw
            rect = QRect(int(x), 26, int(sw), 26)
            vardiya_idx = slot % VARDIYA_SAYISI
            bg = [COLOR_VARDIYA_1, COLOR_VARDIYA_2, COLOR_VARDIYA_3][vardiya_idx]
            p.fillRect(rect, bg)
            p.setPen(COLOR_GRID)
            p.drawRect(rect)
            p.setFont(font_var)
            p.setPen(COLOR_TEXT_DIM)
            p.drawText(rect, Qt.AlignCenter, VARDIYA_ISIMLERI[vardiya_idx])

        # Sol ust kose
        p.fillRect(QRect(0, 0, ROW_HEADER_WIDTH, HEADER_HEIGHT), COLOR_HEADER_BG)
        # Accent cizgi
        p.fillRect(QRect(0, 0, 3, HEADER_HEIGHT), COLOR_PRIMARY)
        p.setPen(COLOR_GRID)
        p.drawRect(QRect(0, 0, ROW_HEADER_WIDTH, HEADER_HEIGHT))
        p.setFont(font_var)
        p.setPen(COLOR_TEXT_DIM)
        p.drawText(QRect(0, 0, ROW_HEADER_WIDTH, HEADER_HEIGHT), Qt.AlignCenter, "BARA")

    def _draw_grid(self, p: QPainter):
        sw = self._slot_width()
        font = QFont("Segoe UI", 9, QFont.Bold)

        for row in range(BARA_SAYISI):
            y = HEADER_HEIGHT + row * ROW_HEIGHT
            bg = COLOR_VARDIYA_1 if row % 2 == 0 else COLOR_VARDIYA_2
            p.fillRect(QRect(0, y, self.width(), ROW_HEIGHT), bg)

            # Bara etiketi
            p.setFont(font)
            p.setPen(COLOR_TEXT)
            p.drawText(QRect(0, y, ROW_HEADER_WIDTH, ROW_HEIGHT), Qt.AlignCenter, f"B{row + 1}")

            # Yatay cizgi
            p.setPen(QPen(COLOR_GRID, 1))
            p.drawLine(ROW_HEADER_WIDTH, y, self.width(), y)

        # Dikey cizgiler
        for slot in range(self._slot_count() + 1):
            x = ROW_HEADER_WIDTH + slot * sw
            is_gun_border = slot % VARDIYA_SAYISI == 0
            pen_width = 2 if is_gun_border else 1
            color = QColor("#2A3545") if is_gun_border else COLOR_GRID
            p.setPen(QPen(color, pen_width))
            p.drawLine(int(x), HEADER_HEIGHT, int(x), HEADER_HEIGHT + BARA_SAYISI * ROW_HEIGHT)

        y_bottom = HEADER_HEIGHT + BARA_SAYISI * ROW_HEIGHT
        p.setPen(QPen(COLOR_GRID, 1))
        p.drawLine(ROW_HEADER_WIDTH, y_bottom, self.width(), y_bottom)

    def _draw_gorevler(self, p: QPainter):
        font = QFont("Segoe UI", 8, QFont.Bold)
        p.setFont(font)
        fm = QFontMetrics(font)

        for g in self._gorevler:
            rect = self._gorev_rect(g)

            if g.acil:
                color = COLOR_ACIL
            elif g.tip == "zn-ni":
                color = COLOR_ZN_NI
            else:
                color = COLOR_ZN

            is_selected = (self._selected_gorev and self._selected_gorev.id == g.id)
            is_hover = (self._hover_gorev and self._hover_gorev.id == g.id)

            # Gradient
            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            grad.setColorAt(0, color.lighter(120 if is_hover else 110))
            grad.setColorAt(1, color)

            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 5, 5)
            p.fillPath(path, QBrush(grad))

            # Secili kenarlik
            if is_selected:
                p.setPen(QPen(QColor("#FFFFFF"), 2))
                p.drawPath(path)

            # Metin
            if rect.width() > 30:
                text = g.urun_ref
                elided = fm.elidedText(text, Qt.ElideRight, rect.width() - 6)
                p.setPen(QColor("#FFFFFF"))
                p.drawText(rect.adjusted(3, 0, -3, 0), Qt.AlignVCenter | Qt.AlignLeft, elided)

    # ─── Mouse olaylari ───

    def mouseMoveEvent(self, event: QMouseEvent):
        gorev = self._gorev_at(event.pos())
        if gorev != self._hover_gorev:
            self._hover_gorev = gorev
            self.update()

        if gorev:
            tip = "Cinko-Nikel" if gorev.tip == "zn-ni" else "Cinko"
            acil_str = " [ACIL]" if gorev.acil else ""
            tooltip = (
                f"{gorev.urun_ref}{acil_str}\n"
                f"Tip: {tip}\n"
                f"Bara: B{gorev.bara_no}\n"
                f"Gun: {GUN_ISIMLERI[gorev.gun]} - {VARDIYA_ISIMLERI[gorev.vardiya - 1]}\n"
                f"Aski: {gorev.aski_sayisi}\n"
                f"Sure: {gorev.sure_dk} dk"
            )
            QToolTip.showText(event.globalPosition().toPoint(), tooltip, self)
        else:
            QToolTip.hideText()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            gorev = self._gorev_at(event.pos())
            self._selected_gorev = gorev
            if gorev:
                self.gorev_secildi.emit(gorev)
            self.update()
        elif event.button() == Qt.RightButton:
            gorev = self._gorev_at(event.pos())
            if gorev:
                self._show_context_menu(event.globalPosition().toPoint(), gorev)

    def _show_context_menu(self, pos: QPoint, gorev: PlanGorev):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {COLOR_HEADER_BG.name()}; color: {COLOR_TEXT.name()};
                border: 1px solid {COLOR_GRID.name()};
                padding: 4px; border-radius: 8px;
            }}
            QMenu::item {{ padding: 8px 20px; border-radius: 4px; }}
            QMenu::item:selected {{ background: {COLOR_PRIMARY.name()}22; }}
        """)

        tip_str = "Cinko-Nikel" if gorev.tip == "zn-ni" else "Cinko"
        info_action = menu.addAction(f"{gorev.urun_ref} ({tip_str})")
        info_action.setEnabled(False)
        menu.addSeparator()

        sil_action = menu.addAction("Gorevi Sil")

        action = menu.exec(pos)
        if action == sil_action:
            self._gorevler = [g for g in self._gorevler if g.id != gorev.id]
            self._selected_gorev = None
            self._hover_gorev = None
            self.gorev_silindi.emit(gorev)
            self.update()

    def leaveEvent(self, event):
        self._hover_gorev = None
        self.update()
