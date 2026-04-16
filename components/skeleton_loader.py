# -*- coding: utf-8 -*-
"""
NEXOR ERP - Skeleton Loader
Sayfa yuklenirken gosterilen shimmer animasyonlu placeholder
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QLinearGradient, QColor

from core.nexor_brand import brand


class SkeletonBlock(QWidget):
    """Shimmer animasyonlu tek bir placeholder bar"""

    def __init__(self, width: int = 0, height: int = 20, radius: int = 8,
                 base_color: str = None, shimmer_color: str = None,
                 parent=None):
        super().__init__(parent)
        self._radius = radius
        self._phase = 0.0
        # Notr varsayilan renkler (tema tarafindan override edilir)
        self._base_color = QColor(base_color or brand.BG_HOVER)
        self._shimmer_color = QColor(shimmer_color or brand.BORDER)

        if width > 0:
            self.setFixedWidth(width)
        else:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(height)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(30)

    def set_colors(self, base: str, shimmer: str):
        self._base_color = QColor(base)
        self._shimmer_color = QColor(shimmer)

    def _advance(self):
        self._phase += 0.02
        if self._phase > 2.0:
            self._phase = 0.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(0, 0, self.width(), self.height())

        grad = QLinearGradient(0, 0, self.width(), 0)
        pos = self._phase - 1.0
        grad.setColorAt(max(0.0, pos - 0.3), self._base_color)
        grad.setColorAt(max(0.0, min(1.0, pos)), self._shimmer_color)
        grad.setColorAt(min(1.0, pos + 0.3), self._base_color)

        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, self._radius, self._radius)
        p.end()

    def stop(self):
        self._timer.stop()


class SkeletonCardLoader(QWidget):
    """Kart seklinde skeleton - baslik + birkaç satir"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._blocks = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_4)

        # Baslik block
        title = SkeletonBlock(width=brand.sp(200), height=brand.sp(24), radius=brand.R_SM)
        self._blocks.append(title)
        layout.addWidget(title)

        # Ust kartlar (4 adet)
        cards_row = QHBoxLayout()
        cards_row.setSpacing(brand.SP_4)
        for _ in range(4):
            card = SkeletonBlock(height=brand.sp(100), radius=brand.R_LG)
            self._blocks.append(card)
            cards_row.addWidget(card)
        layout.addLayout(cards_row)

        # Alt satirlar
        for w in [0, 0, 300]:
            blk = SkeletonBlock(width=brand.sp(w) if w else 0, height=brand.sp(16), radius=brand.SP_1)
            self._blocks.append(blk)
            layout.addWidget(blk)

        layout.addStretch()

    def set_theme_colors(self, base: str, shimmer: str):
        for blk in self._blocks:
            blk.set_colors(base, shimmer)

    def stop(self):
        for blk in self._blocks:
            blk.stop()
