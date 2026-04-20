# -*- coding: utf-8 -*-
"""
NEXOR REDLINE ICON SET
======================
20 modul icin ozgun monoline ikon. QPainter ile 20x20 viewbox uzerinde cizilir,
sonra hedef boyuta scale edilir. Stroke 1.5 (1.2+ olcege gore), yuvarlak uclar.

Aktif durumda (is_active=True) veya color override verildiginde ikon kirmizi
olur; aksi halde TEXT_MUTED tonunda durur.

Kullanim:
    from core.nexor_icons import NexorIcon
    ic = NexorIcon('factory', size=18)
    ic.setActive(True)   # kirmizi
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath
from PySide6.QtWidgets import QLabel

from core.nexor_brand import brand


# =============================================================================
# CIZIM HELPER'LARI (20x20 viewbox)
# =============================================================================

def _draw_dashboard(p: QPainter) -> None:
    # 4 asimetrik panel — sol/sag ust/alt
    # Sol ust (uzun dikey)
    p.drawRoundedRect(3, 3, 6.5, 9, 1, 1)
    # Sag ust (kisa)
    p.drawRoundedRect(10.5, 3, 6.5, 5, 1, 1)
    # Sol alt (kisa)
    p.drawRoundedRect(3, 13, 6.5, 4, 1, 1)
    # Sag alt (uzun)
    p.drawRoundedRect(10.5, 9.5, 6.5, 7.5, 1, 1)


def _draw_users(p: QPainter) -> None:
    # Iki insan silueti — on (buyuk) + arka (kucuk)
    # Arka kisi basi
    p.drawEllipse(11, 3, 4, 4)
    # On kisi basi
    p.drawEllipse(4.5, 4.5, 5.5, 5.5)
    # On omuz kavisi
    path = QPainterPath()
    path.moveTo(2, 17)
    path.cubicTo(2, 12, 11, 12, 11, 17)
    p.drawPath(path)
    # Arka omuz kavisi
    path2 = QPainterPath()
    path2.moveTo(11.2, 12)
    path2.cubicTo(13, 10.5, 17, 10.5, 17.5, 14)
    p.drawPath(path2)


def _draw_box(p: QPainter) -> None:
    # Isometric kutu
    p.drawPolygon([
        _pt(3, 6), _pt(10, 2.5), _pt(17, 6), _pt(17, 15), _pt(10, 18.5),
        _pt(3, 15),
    ])
    # Orta sutun + ust capraz hatlar
    p.drawLine(10, 10, 10, 18.5)
    p.drawLine(3, 6, 10, 10)
    p.drawLine(17, 6, 10, 10)


def _draw_document(p: QPainter) -> None:
    # Sag ust kose kirilmis sayfa
    path = QPainterPath()
    path.moveTo(4, 2.5)
    path.lineTo(13, 2.5)
    path.lineTo(16.5, 6)
    path.lineTo(16.5, 17.5)
    path.lineTo(4, 17.5)
    path.closeSubpath()
    p.drawPath(path)
    # Kirilan kose ic cizgi
    p.drawLine(13, 2.5, 13, 6)
    p.drawLine(13, 6, 16.5, 6)
    # Yazi satirlari
    p.drawLine(6.5, 10, 14, 10)
    p.drawLine(6.5, 12.5, 14, 12.5)
    p.drawLine(6.5, 15, 11.5, 15)


def _draw_clipboard(p: QPainter) -> None:
    # Panel
    p.drawRoundedRect(4, 4, 12, 14, 1.5, 1.5)
    # Ust klips
    p.drawRoundedRect(7.5, 2, 5, 3.2, 0.8, 0.8)
    # Satirlar
    p.drawLine(7, 10, 13, 10)
    p.drawLine(7, 12.5, 13, 12.5)
    p.drawLine(7, 15, 11, 15)


def _draw_factory(p: QPainter) -> None:
    # Fabrika silueti: sol yuksek baca + catili govde
    path = QPainterPath()
    path.moveTo(2.5, 17.5)
    path.lineTo(2.5, 8)
    path.lineTo(6, 8)
    path.lineTo(6, 5)
    path.lineTo(9, 5)
    path.lineTo(9, 10)
    path.lineTo(12.5, 7.5)
    path.lineTo(12.5, 10.5)
    path.lineTo(16, 8)
    path.lineTo(16, 17.5)
    path.closeSubpath()
    p.drawPath(path)
    # Kapi
    p.drawLine(9, 17.5, 9, 13.5)
    p.drawLine(9, 13.5, 12, 13.5)
    p.drawLine(12, 13.5, 12, 17.5)


def _draw_check(p: QPainter) -> None:
    # Daire icinde tik
    p.drawEllipse(2.5, 2.5, 15, 15)
    # Tik
    path = QPainterPath()
    path.moveTo(6.5, 10.2)
    path.lineTo(9.2, 13)
    path.lineTo(14, 7.5)
    p.drawPath(path)


def _draw_flask(p: QPainter) -> None:
    # Deney sisesi
    # Boyun
    p.drawLine(8, 2.5, 8, 8)
    p.drawLine(12, 2.5, 12, 8)
    p.drawLine(7, 2.5, 13, 2.5)
    # Govde (konik)
    path = QPainterPath()
    path.moveTo(8, 8)
    path.lineTo(4, 16.5)
    path.quadTo(10, 18.5, 16, 16.5)
    path.lineTo(12, 8)
    p.drawPath(path)
    # Sivi seviyesi ic cizgi
    p.drawLine(5.8, 13.5, 14.2, 13.5)
    # Kabarcik
    p.drawEllipse(9.3, 15, 1.4, 1.4)


def _draw_truck(p: QPainter) -> None:
    # Yuk kasasi
    p.drawRoundedRect(2, 7, 9, 7, 0.8, 0.8)
    # Kabin (sag)
    path = QPainterPath()
    path.moveTo(11, 7)
    path.lineTo(15, 7)
    path.lineTo(17.5, 10)
    path.lineTo(17.5, 14)
    path.lineTo(11, 14)
    path.closeSubpath()
    p.drawPath(path)
    # Pencere cizgisi
    p.drawLine(12, 10, 16.5, 10)
    # Tekerlek 1
    p.drawEllipse(4, 13.5, 3.5, 3.5)
    # Tekerlek 2
    p.drawEllipse(12.5, 13.5, 3.5, 3.5)


def _draw_cart(p: QPainter) -> None:
    # Sepet gicri
    p.drawLine(2, 3.5, 4, 3.5)
    p.drawLine(4, 3.5, 6, 12.5)
    # Sepet ust kenar
    path = QPainterPath()
    path.moveTo(5.2, 6)
    path.lineTo(17.5, 6)
    path.lineTo(15.5, 12.5)
    path.lineTo(6, 12.5)
    p.drawPath(path)
    # Dikey cizgiler (sepet icligi)
    p.drawLine(9, 6, 9.3, 12.5)
    p.drawLine(12.5, 6, 12.5, 12.5)
    # Tekerlekler
    p.drawEllipse(6.2, 15, 2.2, 2.2)
    p.drawEllipse(13.3, 15, 2.2, 2.2)


def _draw_warehouse(p: QPainter) -> None:
    # Ucgen cati + govde
    path = QPainterPath()
    path.moveTo(2, 9)
    path.lineTo(10, 3)
    path.lineTo(18, 9)
    path.lineTo(18, 17.5)
    path.lineTo(2, 17.5)
    path.closeSubpath()
    p.drawPath(path)
    # Kapi
    p.drawRect(8, 12, 4, 5.5)
    # Pencereler
    p.drawLine(4.5, 10.5, 7, 10.5)
    p.drawLine(13, 10.5, 15.5, 10.5)


def _draw_user_badge(p: QPainter) -> None:
    # Insan + rozet
    p.drawEllipse(6, 3, 8, 8)  # bas
    # Omuz
    path = QPainterPath()
    path.moveTo(3, 17.5)
    path.cubicTo(3, 11, 17, 11, 17, 17.5)
    p.drawPath(path)
    # Rozet kordonu (opsiyonel küçük nokta)
    p.drawEllipse(9.3, 14.5, 1.4, 1.4)


def _draw_wrench(p: QPainter) -> None:
    # Ingiliz anahtari
    path = QPainterPath()
    # Dis halka (C sekli) — ust
    path.moveTo(11, 2.5)
    path.arcTo(6, 2.5, 9, 9, 90, 270)
    # Govde (capraz)
    path.lineTo(17.5, 17.5)
    path.lineTo(15, 15)
    path.lineTo(8, 8)
    p.drawPath(path)
    # Alternatif: basitce iki cemberi kapraz kirik
    p.drawLine(14.5, 14.5, 17.5, 17.5)


def _draw_shield(p: QPainter) -> None:
    # Kalkan + ic tik
    path = QPainterPath()
    path.moveTo(10, 2)
    path.lineTo(16.5, 4.5)
    path.lineTo(16.5, 10)
    path.quadTo(16.5, 16, 10, 18)
    path.quadTo(3.5, 16, 3.5, 10)
    path.lineTo(3.5, 4.5)
    path.closeSubpath()
    p.drawPath(path)
    # Ic tik
    path2 = QPainterPath()
    path2.moveTo(7.5, 10)
    path2.lineTo(9.3, 12)
    path2.lineTo(13, 7.8)
    p.drawPath(path2)


def _draw_leaf(p: QPainter) -> None:
    # Yaprak sekli + damar
    path = QPainterPath()
    path.moveTo(16.5, 3)
    path.cubicTo(16.5, 13, 12, 17, 4, 17)
    path.cubicTo(4, 10, 9, 4, 16.5, 3)
    p.drawPath(path)
    # Damar
    p.drawLine(4.5, 16.5, 15, 5.5)
    # Ic 2-3 damarlar
    p.drawLine(7.5, 13.5, 11.5, 9)
    p.drawLine(10, 15, 13, 11.5)


def _draw_list(p: QPainter) -> None:
    # 3 satir + sol noktalar
    for i, y in enumerate((5, 10, 15)):
        p.drawEllipse(3, y - 1.1, 2.2, 2.2)
        p.drawLine(7, y, 17, y)


def _draw_chart(p: QPainter) -> None:
    # Bar chart (artan) + eksen
    # Y ekseni
    p.drawLine(3, 2.5, 3, 17)
    # X ekseni
    p.drawLine(3, 17, 17.5, 17)
    # Bar'lar (3 adet artan)
    p.drawRect(5, 12, 3, 5)
    p.drawRect(9.5, 8, 3, 9)
    p.drawRect(14, 4, 3, 13)


def _draw_gear(p: QPainter) -> None:
    # Dis carki - 8 dis
    import math
    cx, cy = 10, 10
    inner = 4.0
    outer = 7.2
    # Cokenin ici
    p.drawEllipse(cx - 2.8, cy - 2.8, 5.6, 5.6)
    # Disler — 8 tane, her biri kucuk kare
    for i in range(8):
        a = i * (2 * math.pi / 8)
        ra = a
        # Dis ortasi
        tx = cx + outer * math.cos(ra)
        ty = cy + outer * math.sin(ra)
        # Kucuk dis cubugu (cember merkezine dogru ince cizgi)
        ix = cx + inner * math.cos(ra)
        iy = cy + inner * math.sin(ra)
        p.drawLine(ix, iy, tx, ty)


def _draw_crown(p: QPainter) -> None:
    # Tac - 3 zirveli
    path = QPainterPath()
    path.moveTo(3, 15)
    path.lineTo(5.5, 6)
    path.lineTo(8, 11)
    path.lineTo(10, 5)
    path.lineTo(12, 11)
    path.lineTo(14.5, 6)
    path.lineTo(17, 15)
    path.closeSubpath()
    p.drawPath(path)
    # Alt tas
    p.drawLine(3.5, 15, 16.5, 15)


def _draw_lock(p: QPainter) -> None:
    # Govde
    p.drawRoundedRect(4, 9, 12, 9, 1.5, 1.5)
    # Ust kavis
    path = QPainterPath()
    path.moveTo(6.5, 9)
    path.lineTo(6.5, 6.5)
    path.arcTo(6.5, 2.5, 7, 7, 180, -180)
    path.lineTo(13.5, 9)
    p.drawPath(path)
    # Anahtar deligi nokta
    p.drawEllipse(9.3, 12.5, 1.4, 1.4)
    p.drawLine(10, 14, 10, 15.5)


# =============================================================================
# KAYIT
# =============================================================================

_DRAW_MAP = {
    'dashboard':  _draw_dashboard,
    'users':      _draw_users,
    'box':        _draw_box,
    'document':   _draw_document,
    'clipboard':  _draw_clipboard,
    'factory':    _draw_factory,
    'check':      _draw_check,
    'flask':      _draw_flask,
    'truck':      _draw_truck,
    'cart':       _draw_cart,
    'warehouse':  _draw_warehouse,
    'user-badge': _draw_user_badge,
    'wrench':     _draw_wrench,
    'shield':     _draw_shield,
    'leaf':       _draw_leaf,
    'list':       _draw_list,
    'chart':      _draw_chart,
    'gear':       _draw_gear,
    'crown':      _draw_crown,
    'lock':       _draw_lock,
}


def _pt(x: float, y: float):
    from PySide6.QtCore import QPointF
    return QPointF(x, y)


# =============================================================================
# WIDGET
# =============================================================================

class NexorIcon(QLabel):
    """
    Monoline, tema-aware, aktif durum destekli ikon.

        ic = NexorIcon('factory', size=20)
        ic.setActive(True)  # kirmizi

    `kind` listesi: dashboard, users, box, document, clipboard, factory, check,
    flask, truck, cart, warehouse, user-badge, wrench, shield, leaf, list, chart,
    gear, crown, lock.
    """

    def __init__(self, kind: str = 'dashboard', color: str | None = None,
                 size: int = 20, parent=None):
        super().__init__(parent)
        self.kind = kind
        self._color = color
        self._active = False
        self._size = brand.sp(size)
        self.setFixedSize(self._size, self._size)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    # ---------- Public API ----------
    def setKind(self, kind: str) -> None:
        self.kind = kind
        self.update()

    def setActive(self, active: bool) -> None:
        if active != self._active:
            self._active = active
            self.update()

    def setColor(self, color: str | None) -> None:
        self._color = color
        self.update()

    # ---------- Paint ----------
    def paintEvent(self, _):
        draw_fn = _DRAW_MAP.get(self.kind)
        if not draw_fn:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        col = self._color or (brand.PRIMARY if self._active else brand.TEXT_MUTED)
        pen = QPen(QColor(col))
        pen.setWidthF(max(1.1, self._size / 13.0))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        # 20x20 viewbox -> hedef boyut
        scale = self._size / 20.0
        p.scale(scale, scale)
        draw_fn(p)
        p.end()
