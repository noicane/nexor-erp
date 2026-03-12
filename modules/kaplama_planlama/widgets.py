# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kaplama Planlama Gorsel Bilesenler
[KURUMSAL UI - v2.0]

Aciklama:
- QPainter ile ozel widget'lar
- SicaklikGauge, DolulukHalka, BanyoCard, HatDurumu, BaraStrip
"""
import math
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QToolTip, QSizePolicy
)
from PySide6.QtCore import Qt, QRect, QRectF, QPoint, QSize, QTimer, Signal
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QPainterPath, QLinearGradient, QRadialGradient,
    QConicalGradient, QPaintEvent, QMouseEvent
)


# ── Stil Sabitleri ──
CARD_RADIUS = 10
LABEL_SIZE = 10
SMALL_SIZE = 11
BODY_SIZE = 13
BG_DARK = "#0F1419"
BORDER_COLOR = "#1E2736"
GRID_COLOR = "#1E2736"


# ══════════════════════════════════════════════════════════════
#  SICAKLIK GAUGE - Yarim daire sicaklik gostergesi
# ══════════════════════════════════════════════════════════════

class SicaklikGauge(QWidget):
    """Yarim daire sicaklik gauge'u - min/hedef/max ile"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._min_val = 0.0
        self._max_val = 100.0
        self._hedef = 50.0
        self._label = ""
        self._unit = "C"
        self.setFixedSize(100, 65)

    def set_data(self, value: float, min_val: float, max_val: float, hedef: float, label: str = ""):
        self._value = value
        self._min_val = min_val
        self._max_val = max_val
        self._hedef = hedef
        self._label = label
        self.update()

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h - 8
        radius = min(w, h * 2) // 2 - 8

        # Arka plan yay
        pen = QPen(QColor(GRID_COLOR), 6, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        arc_rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        p.drawArc(arc_rect, 180 * 16, 180 * 16)

        # Deger yay
        rng = self._max_val - self._min_val
        if rng <= 0:
            rng = 1
        ratio = max(0.0, min(1.0, (self._value - self._min_val) / rng))
        angle = ratio * 180

        hedef_ratio = (self._hedef - self._min_val) / rng if rng > 0 else 0.5
        diff = abs(ratio - hedef_ratio)
        if diff < 0.15:
            color = QColor("#10B981")
        elif diff < 0.3:
            color = QColor("#F59E0B")
        else:
            color = QColor("#EF4444")

        pen.setColor(color)
        pen.setWidth(6)
        p.setPen(pen)
        p.drawArc(arc_rect, 180 * 16, int(angle * 16))

        # Hedef cizgisi
        hedef_angle = math.radians(180 - hedef_ratio * 180)
        hx = cx + int((radius - 2) * math.cos(hedef_angle))
        hy = cy - int((radius - 2) * math.sin(hedef_angle))
        hx2 = cx + int((radius + 5) * math.cos(hedef_angle))
        hy2 = cy - int((radius + 5) * math.sin(hedef_angle))
        p.setPen(QPen(QColor("#FFFFFF88"), 2))
        p.drawLine(hx, hy, hx2, hy2)

        # Deger metni
        p.setPen(QColor("#E8ECF1"))
        font = QFont("Segoe UI", 11, QFont.Bold)
        p.setFont(font)
        p.drawText(QRect(0, cy - radius // 2 - 2, w, 20), Qt.AlignCenter, f"{self._value:.1f}")

        # Birim
        font.setPointSize(7)
        font.setBold(False)
        p.setFont(font)
        p.setPen(QColor("#8896A6"))
        p.drawText(QRect(0, cy - radius // 2 + 14, w, 14), Qt.AlignCenter, f"{self._unit}")

        p.end()


# ══════════════════════════════════════════════════════════════
#  DOLULUK HALKA - Yuvarlak doluluk gostergesi
# ══════════════════════════════════════════════════════════════

class DolulukHalka(QWidget):
    """Yuvarlak doluluk gostergesi (0-100%)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._max_val = 100
        self._label = ""
        self._color = QColor("#10B981")
        self.setFixedSize(50, 50)

    def set_data(self, value: int, max_val: int, label: str = "", color: str = "#10B981"):
        self._value = value
        self._max_val = max(max_val, 1)
        self._label = label
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        s = min(self.width(), self.height())
        margin = 4
        rect = QRectF(margin, margin, s - margin * 2, s - margin * 2)

        # Arka plan halka
        pen = QPen(QColor(GRID_COLOR), 5, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 90 * 16, 360 * 16)

        # Deger halka
        ratio = min(1.0, self._value / self._max_val)
        pen.setColor(self._color)
        p.setPen(pen)
        p.drawArc(rect, 90 * 16, int(-ratio * 360 * 16))

        # Metin
        p.setPen(QColor("#E8ECF1"))
        font = QFont("Segoe UI", 9, QFont.Bold)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignCenter, str(self._value))

        p.end()


# ══════════════════════════════════════════════════════════════
#  BANYO KARTI - Zengin banyo bilgi karti
# ══════════════════════════════════════════════════════════════

class BanyoCard(QFrame):
    """Zengin banyo durum karti: sicaklik gauge + doluluk + bilgiler"""

    clicked = Signal(dict)

    def __init__(self, style: dict, parent=None):
        super().__init__(parent)
        self.s = style
        self._data = {}
        self.setCursor(Qt.PointingHandCursor)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(160)
        self.setMaximumWidth(200)
        self._setup_ui()

    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        self.lbl_ad = QLabel("Banyo")
        self.lbl_ad.setStyleSheet(f"color: {s['text']}; font-size: {SMALL_SIZE}px; font-weight: 600;")
        self.lbl_ad.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_ad)

        # Gauge + Doluluk
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(6)

        self.gauge = SicaklikGauge()
        mid_layout.addWidget(self.gauge)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.lbl_durum = QLabel("--")
        self.lbl_durum.setStyleSheet(f"color: {s['success']}; font-size: {LABEL_SIZE}px; font-weight: 600;")
        self.lbl_durum.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.lbl_durum)

        self.doluluk = DolulukHalka()
        info_layout.addWidget(self.doluluk, 0, Qt.AlignCenter)

        mid_layout.addLayout(info_layout)
        layout.addLayout(mid_layout)

        # Alt bilgiler
        info_style = f"color: {s['text_muted']}; font-size: 9px;"
        self.lbl_recete = QLabel("Recete: -")
        self.lbl_recete.setStyleSheet(info_style)
        layout.addWidget(self.lbl_recete)

        self.lbl_akim = QLabel("Akim: -")
        self.lbl_akim.setStyleSheet(info_style)
        layout.addWidget(self.lbl_akim)

        self.lbl_sure = QLabel("Sure: -")
        self.lbl_sure.setStyleSheet(info_style)
        layout.addWidget(self.lbl_sure)

    def set_data(self, data: dict):
        s = self.s
        self._data = data
        ad = data.get('ad', f"Kazan {data.get('kazan_no', '?')}")
        self.lbl_ad.setText(ad)

        # Sicaklik gauge
        sicaklik = data.get('sicaklik', 0) or 0
        s_min = data.get('sicaklik_min', 0) or 0
        s_max = data.get('sicaklik_max', 100) or 100
        s_hedef = data.get('sicaklik_hedef', 50) or 50
        self.gauge.set_data(sicaklik, s_min, s_max, s_hedef)

        # Durum
        durum = data.get('durum', 'BELIRSIZ')
        durum_dk = data.get('durum_dakika', 0) or 0
        durum_renk = {
            'AKTIF': s['success'],
            'BEKLIYOR': s['warning'],
            'DURDU': s['error'],
        }.get(durum, s['text_muted'])
        self.lbl_durum.setText(f"{durum}\n{durum_dk}dk")
        self.lbl_durum.setStyleSheet(f"color: {durum_renk}; font-size: {LABEL_SIZE}px; font-weight: 600;")

        # Doluluk
        aktif = data.get('aktif_aski', 0) or 0
        maks = data.get('max_aski', 4) or 4
        d_color = s['success'] if aktif < maks else s['error']
        self.doluluk.set_data(aktif, maks, color=d_color)

        # Alt bilgiler
        recete = data.get('recete_no', '-') or '-'
        recete_adi = data.get('recete_adi', '')
        recete_acik = data.get('recete_aciklama', '')
        if recete_adi:
            self.lbl_recete.setText(f"R{recete}: {recete_adi}")
            self.lbl_recete.setToolTip(f"Recete #{recete} - {recete_adi} / {recete_acik}")
        else:
            self.lbl_recete.setText(f"Recete: {recete}")

        akim = data.get('akim', 0) or 0
        recete_sure = data.get('recete_sure_dk')
        if recete_sure:
            self.lbl_akim.setText(f"Akim: {akim:.1f}A | {recete_sure}dk")
        else:
            self.lbl_akim.setText(f"Akim: {akim:.1f}A")

        bara = data.get('son_bara', '-') or '-'
        self.lbl_sure.setText(f"Bara: {bara} | {durum_dk}dk")

        # Kart stili: sol accent + durum rengi
        self.setStyleSheet(f"""
            QFrame[frameShape="StyledPanel"] {{
                background: {durum_renk}11;
                border: 1px solid {durum_renk}22;
                border-left: 3px solid {durum_renk};
                border-radius: {CARD_RADIUS}px;
            }}
        """)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self._data:
            self.clicked.emit(self._data)


# ══════════════════════════════════════════════════════════════
#  HAT CANLI GORUNUM - Tum kazanlarin canli durumu
# ══════════════════════════════════════════════════════════════

class HatCanliWidget(QWidget):
    """Hat uzerindeki tum kazanlarin canli durumunu gosteren QPainter widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._kazanlar: List[Dict] = []
        self._hover_idx = -1
        self.setMouseTracking(True)
        self.setMinimumHeight(200)

    def set_kazanlar(self, kazanlar: List[Dict]):
        self._kazanlar = kazanlar
        self._hover_idx = -1
        self.update()

    def _kazan_rect(self, idx: int) -> QRect:
        if not self._kazanlar:
            return QRect()
        cols = min(len(self._kazanlar), 12)
        rows = math.ceil(len(self._kazanlar) / cols)
        margin = 10
        avail_w = self.width() - margin * 2
        avail_h = self.height() - margin * 2 - 30
        cell_w = avail_w / cols
        cell_h = avail_h / max(rows, 1)
        r, c = divmod(idx, cols)
        pad = 3
        x = margin + c * cell_w + pad
        y = margin + 30 + r * cell_h + pad
        w = cell_w - pad * 2
        h = cell_h - pad * 2
        return QRect(int(x), int(y), int(w), int(h))

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(BG_DARK))

        if not self._kazanlar:
            p.setPen(QColor("#5C6878"))
            p.setFont(QFont("Segoe UI", 12))
            p.drawText(self.rect(), Qt.AlignCenter, "PLC verisi bekleniyor...")
            p.end()
            return

        # Baslik
        p.setPen(QColor("#8896A6"))
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.drawText(QRect(10, 4, self.width(), 24), Qt.AlignLeft | Qt.AlignVCenter, "HAT CANLI GORUNUM")

        font_no = QFont("Segoe UI", 8, QFont.Bold)
        font_info = QFont("Segoe UI", 7)

        for i, kz in enumerate(self._kazanlar):
            rect = self._kazan_rect(i)
            durum = kz.get('durum', 'BELIRSIZ')
            sicaklik = kz.get('sicaklik', 0) or 0

            color_map = {
                'AKTIF': QColor("#10B981"),
                'BEKLIYOR': QColor("#F59E0B"),
                'DURDU': QColor("#EF4444"),
                'BELIRSIZ': QColor("#3A4555"),
            }
            color = color_map.get(durum, QColor("#3A4555"))

            is_hover = (i == self._hover_idx)

            # Kutu
            path = QPainterPath()
            path.addRoundedRect(QRectF(rect), 6, 6)

            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            grad.setColorAt(0, color.darker(200) if not is_hover else color.darker(150))
            grad.setColorAt(1, color.darker(300))
            p.fillPath(path, QBrush(grad))

            # Sol accent cizgisi
            bar_rect = QRectF(rect.x(), rect.y(), 3, rect.height())
            bar_path = QPainterPath()
            bar_path.addRoundedRect(bar_rect, 1.5, 1.5)
            p.fillPath(bar_path, QBrush(color))

            # Kazan no
            p.setPen(QColor("#E8ECF1"))
            p.setFont(font_no)
            p.drawText(rect.adjusted(8, 3, -4, -rect.height() // 2),
                       Qt.AlignLeft | Qt.AlignVCenter, str(kz.get('kazan_no', '?')))

            # Sicaklik
            if rect.height() > 35:
                p.setFont(font_info)
                if sicaklik > 0:
                    p.setPen(QColor("#E8ECF1"))
                    p.drawText(rect.adjusted(8, rect.height() // 2 - 4, -4, -2),
                               Qt.AlignLeft | Qt.AlignVCenter, f"{sicaklik:.1f}C")
                else:
                    p.setPen(QColor("#5C6878"))
                    p.drawText(rect.adjusted(8, rect.height() // 2 - 4, -4, -2),
                               Qt.AlignLeft | Qt.AlignVCenter, "--")

            # Hover
            if is_hover:
                p.setPen(QPen(QColor("#FFFFFF44"), 1))
                p.drawPath(path)

        p.end()

    def mouseMoveEvent(self, event: QMouseEvent):
        old_hover = self._hover_idx
        self._hover_idx = -1
        for i in range(len(self._kazanlar)):
            if self._kazan_rect(i).contains(event.pos()):
                self._hover_idx = i
                break
        if self._hover_idx != old_hover:
            self.update()
        if self._hover_idx >= 0:
            kz = self._kazanlar[self._hover_idx]
            tip = (
                f"Kazan: {kz.get('kazan_no', '?')}\n"
                f"Hat: {kz.get('hat_kodu', '-')}\n"
                f"Durum: {kz.get('durum', '-')} ({kz.get('durum_dakika', 0)}dk)\n"
                f"Sicaklik: {kz.get('sicaklik', 0):.1f}C\n"
                f"Akim: {kz.get('akim', 0):.1f}A\n"
                f"Recete: {kz.get('recete_no', '-')}\n"
                f"Son Bara: {kz.get('son_bara', '-')}"
            )
            QToolTip.showText(event.globalPosition().toPoint(), tip, self)
        else:
            QToolTip.hideText()

    def leaveEvent(self, event):
        self._hover_idx = -1
        self.update()


# ══════════════════════════════════════════════════════════════
#  BARA DURUM STRIP - Gantt ustunde canli bara durumu
# ══════════════════════════════════════════════════════════════

class BaraDurumStrip(QWidget):
    """Gantt ustunde 11 baranin canli durumunu gosteren yatay serit"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bara_data: List[Dict] = []
        self.setFixedHeight(38)
        self.setMouseTracking(True)
        self._hover_idx = -1

    def set_data(self, bara_data: List[Dict]):
        self._bara_data = bara_data
        self.update()

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(BG_DARK))

        if not self._bara_data:
            p.setPen(QColor("#5C6878"))
            p.setFont(QFont("Segoe UI", 9))
            p.drawText(self.rect(), Qt.AlignCenter, "Bara durumu bekleniyor...")
            p.end()
            return

        n = len(self._bara_data)
        margin = 6
        spacing = 4
        total_spacing = spacing * (n - 1)
        cell_w = (self.width() - margin * 2 - total_spacing) / max(n, 1)
        h = self.height() - margin * 2

        font = QFont("Segoe UI", 8, QFont.Bold)
        p.setFont(font)

        for i, bd in enumerate(self._bara_data):
            x = margin + i * (cell_w + spacing)
            rect = QRectF(x, margin, cell_w, h)

            durum = bd.get('durum', 'BOS')
            color_map = {
                'AKTIF': QColor("#10B981"),
                'PLANLANDI': QColor("#3B82F6"),
                'BOS': QColor("#1E2736"),
                'BAKIM': QColor("#EF4444"),
            }
            color = color_map.get(durum, QColor("#1E2736"))

            is_hover = (i == self._hover_idx)
            if is_hover:
                color = color.lighter(130)

            path = QPainterPath()
            path.addRoundedRect(rect, 5, 5)
            p.fillPath(path, QBrush(color))

            p.setPen(QColor("#E8ECF1") if durum != 'BOS' else QColor("#5C6878"))
            p.drawText(rect, Qt.AlignCenter, f"B{bd.get('bara_no', i+1)}")

        p.end()

    def mouseMoveEvent(self, event: QMouseEvent):
        old = self._hover_idx
        self._hover_idx = -1
        if self._bara_data:
            n = len(self._bara_data)
            margin = 6
            spacing = 4
            cell_w = (self.width() - margin * 2 - spacing * (n - 1)) / max(n, 1)
            for i in range(n):
                x = margin + i * (cell_w + spacing)
                if x <= event.pos().x() <= x + cell_w:
                    self._hover_idx = i
                    break
        if self._hover_idx != old:
            self.update()
        if 0 <= self._hover_idx < len(self._bara_data):
            bd = self._bara_data[self._hover_idx]
            tip = f"Bara {bd.get('bara_no', '?')}: {bd.get('durum', '-')}"
            if bd.get('urun_ref'):
                tip += f"\nUrun: {bd['urun_ref']}"
            if bd.get('kalan_dk'):
                tip += f"\nKalan: {bd['kalan_dk']}dk"
            QToolTip.showText(event.globalPosition().toPoint(), tip, self)

    def leaveEvent(self, event):
        self._hover_idx = -1
        self.update()


# ══════════════════════════════════════════════════════════════
#  HAT ISTATISTIK KARTI
# ══════════════════════════════════════════════════════════════

class HatIstatistikCard(QFrame):
    """Tek bir hat (KTL/ZNNI) icin ozet istatistik karti"""

    def __init__(self, style: dict, parent=None):
        super().__init__(parent)
        self.s = style
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame[frameShape="StyledPanel"] {{
                background: {self.s['card_bg']};
                border: 1px solid {self.s['border']};
                border-radius: {CARD_RADIUS}px;
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        self.lbl_hat = QLabel("Hat")
        self.lbl_hat.setStyleSheet(f"color: {s['text']}; font-size: 14px; font-weight: 600;")
        layout.addWidget(self.lbl_hat)

        self.stats_layout = QGridLayout()
        self.stats_layout.setSpacing(6)

        self._stat_labels = {}
        stats = [
            ("aktif", "AKTIF KAZAN", s['success']),
            ("bekliyor", "BEKLIYOR", s['warning']),
            ("durdu", "DURDU", s['error']),
            ("ort_sicaklik", "ORT. SICAKLIK", s['info']),
            ("toplam_miktar", "24S URETIM", s['text']),
            ("bara_adet", "BARA/GUN", s['text_secondary']),
        ]
        for i, (key, label, color) in enumerate(stats):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {s['text_muted']}; font-size: {LABEL_SIZE}px; font-weight: 600; letter-spacing: 1px;")
            val = QLabel("-")
            val.setObjectName(f"stat_{key}")
            val.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 700;")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row, col = divmod(i, 2)
            self.stats_layout.addWidget(lbl, row, col * 2)
            self.stats_layout.addWidget(val, row, col * 2 + 1)
            self._stat_labels[key] = val

        layout.addLayout(self.stats_layout)

    def set_data(self, hat_adi: str, data: dict):
        self.lbl_hat.setText(hat_adi)
        for key, val_lbl in self._stat_labels.items():
            value = data.get(key, '-')
            if isinstance(value, float):
                val_lbl.setText(f"{value:.1f}")
            else:
                val_lbl.setText(str(value))


# ══════════════════════════════════════════════════════════════
#  RECETE ADIM WIDGET - Urun recete adimlari gorsel
# ══════════════════════════════════════════════════════════════

class ReceteAdimWidget(QWidget):
    """Urun recete adimlarini yatay akis seklinde gosteren widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._adimlar: List[Dict] = []
        self.setFixedHeight(60)
        self.setMouseTracking(True)
        self._hover_idx = -1

    def set_adimlar(self, adimlar: List[Dict]):
        self._adimlar = adimlar
        self.update()

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(BG_DARK))

        if not self._adimlar:
            p.setPen(QColor("#5C6878"))
            p.setFont(QFont("Segoe UI", 9))
            p.drawText(self.rect(), Qt.AlignCenter, "Recete adimlari bulunamadi")
            p.end()
            return

        n = len(self._adimlar)
        margin = 6
        arrow_w = 12
        avail_w = self.width() - margin * 2 - arrow_w * max(n - 1, 0)
        step_w = avail_w / max(n, 1)
        h = self.height() - margin * 2

        font_name = QFont("Segoe UI", 7, QFont.Bold)
        font_info = QFont("Segoe UI", 7)

        for i, adim in enumerate(self._adimlar):
            x = margin + i * (step_w + arrow_w)
            rect = QRectF(x, margin, step_w, h)

            banyo = (adim.get('banyo_tipi', '') or '').upper()
            if 'NI' in banyo:
                color = QColor("#3B82F6")
            elif 'ZN' in banyo or 'CINKO' in banyo:
                color = QColor("#F59E0B")
            elif 'YIKAMA' in (adim.get('islem', '') or '').upper():
                color = QColor("#06B6D4")
            else:
                color = QColor("#6B7280")

            is_hover = (i == self._hover_idx)
            if is_hover:
                color = color.lighter(130)

            # Kutu
            path = QPainterPath()
            path.addRoundedRect(rect, 5, 5)
            p.fillPath(path, QBrush(color.darker(200)))

            # Ust accent cizgisi
            top_bar = QRectF(rect.x(), rect.y(), rect.width(), 3)
            top_path = QPainterPath()
            top_path.addRoundedRect(top_bar, 1.5, 1.5)
            p.fillPath(top_path, QBrush(color))

            # Islem adi
            p.setPen(QColor("#E8ECF1"))
            p.setFont(font_name)
            text = adim.get('islem', f"Adim {adim.get('sira', i+1)}")
            fm = QFontMetrics(font_name)
            elided = fm.elidedText(text, Qt.ElideRight, int(rect.width() - 6))
            p.drawText(rect.adjusted(3, 6, -3, -h // 2), Qt.AlignLeft | Qt.AlignVCenter, elided)

            # Sure
            p.setFont(font_info)
            p.setPen(QColor("#C0C8D4"))
            sure_sn = adim.get('sure_sn', 0)
            if sure_sn >= 60:
                sure_txt = f"{sure_sn // 60}dk {sure_sn % 60}sn"
            else:
                sure_txt = f"{sure_sn}sn"
            p.drawText(rect.adjusted(3, h // 2 - 2, -3, -4), Qt.AlignLeft | Qt.AlignVCenter, sure_txt)

            # Ok isareti
            if i < n - 1:
                ax = x + step_w + 2
                ay = margin + h // 2
                p.setPen(QPen(QColor("#3A4555"), 2))
                p.drawLine(int(ax), int(ay), int(ax + arrow_w - 4), int(ay))
                p.drawLine(int(ax + arrow_w - 7), int(ay - 3), int(ax + arrow_w - 4), int(ay))
                p.drawLine(int(ax + arrow_w - 7), int(ay + 3), int(ax + arrow_w - 4), int(ay))

        p.end()

    def mouseMoveEvent(self, event: QMouseEvent):
        old = self._hover_idx
        self._hover_idx = -1
        if self._adimlar:
            n = len(self._adimlar)
            margin = 6
            arrow_w = 12
            avail_w = self.width() - margin * 2 - arrow_w * max(n - 1, 0)
            step_w = avail_w / max(n, 1)
            for i in range(n):
                x = margin + i * (step_w + arrow_w)
                if x <= event.pos().x() <= x + step_w:
                    self._hover_idx = i
                    break
        if self._hover_idx != old:
            self.update()
        if 0 <= self._hover_idx < len(self._adimlar):
            a = self._adimlar[self._hover_idx]
            tip = f"Adim {a.get('sira', '?')}: {a.get('islem', '-')}\n"
            tip += f"Sure: {a.get('sure_sn', 0)}sn\n"
            tip += f"Banyo: {a.get('banyo_tipi', '-')}\n"
            if a.get('sicaklik_hedef'):
                tip += f"Sicaklik: {a['sicaklik_hedef']}C\n"
            if a.get('akim_hedef'):
                tip += f"Akim: {a['akim_hedef']}A"
            QToolTip.showText(event.globalPosition().toPoint(), tip, self)

    def leaveEvent(self, event):
        self._hover_idx = -1
        self.update()


# ══════════════════════════════════════════════════════════════
#  KAPASİTE GÖRSEL WİDGET - Yatay bar chart ile kapasite analizi
# ══════════════════════════════════════════════════════════════

_CLR_CINKO = QColor("#F59E0B")
_CLR_NIKEL = QColor("#3B82F6")
_CLR_KAP_LINE = QColor("#EF4444")
_CLR_BOS = QColor("#1E2736")
_CLR_BG = QColor("#0F1419")
_CLR_TEXT = QColor("#E8ECF1")
_CLR_MUTED = QColor("#5C6878")
_CLR_SUCCESS = QColor("#10B981")
_CLR_WARN = QColor("#F59E0B")
_CLR_ERR = QColor("#EF4444")


class KapasiteGorselWidget(QWidget):
    """Ürün bazlı kapasite bar chart - yatay stacked barlar + kapasite çizgisi"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._urunler = []
        self._paralel_bara = 15
        self._cevrim_dk = 90
        self._vardiya_sayisi = 3
        self.setMinimumHeight(350)

    def set_data(self, urunler: list, paralel_bara: int = 15,
                 cevrim_dk: int = 90, vardiya_sayisi: int = 3):
        """
        urunler: [{adi, tip ('cinko'/'nikel'), ihtiyac, bara_adeti, bara_gerekli}]
        """
        self._urunler = urunler
        self._paralel_bara = paralel_bara
        self._cevrim_dk = cevrim_dk
        self._vardiya_sayisi = vardiya_sayisi
        h = 260 + len(urunler) * 19
        self.setMinimumHeight(max(350, h))
        self.update()

    @property
    def _vardiya_kapasite(self):
        cevrim_per_v = 480 // max(self._cevrim_dk, 1)
        return cevrim_per_v * self._paralel_bara

    @property
    def _gunluk_kapasite(self):
        return self._vardiya_kapasite * self._vardiya_sayisi

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, _CLR_BG)

        if not self._urunler:
            p.setPen(_CLR_MUTED)
            p.setFont(QFont("Segoe UI", 12))
            p.drawText(QRect(0, 0, w, h), Qt.AlignCenter,
                       "Ürün verisi yok.\nExcel'den veya ürün listesinden veri yükleyin.")
            p.end()
            return

        cinko = [u for u in self._urunler if u.get('tip', '').lower() in ('cinko', 'zn')]
        nikel = [u for u in self._urunler if u.get('tip', '').lower() in ('nikel', 'zn-ni', 'ni')]
        cinko_bara = sum(u.get('bara_gerekli', 0) for u in cinko)
        nikel_bara = sum(u.get('bara_gerekli', 0) for u in nikel)
        toplam_bara = cinko_bara + nikel_bara
        kapasite = self._gunluk_kapasite
        max_val = max(toplam_bara, kapasite) * 1.15

        LM, RM, TM = 140, 30, 70
        bar_area_w = w - LM - RM
        scale = bar_area_w / max_val if max_val > 0 else 1

        # ── Başlık ──
        p.setPen(_CLR_TEXT)
        p.setFont(QFont("Segoe UI", 14, QFont.Bold))
        p.drawText(12, 28, "Günlük Kapasite vs İhtiyaç")

        doluluk = (toplam_bara / kapasite * 100) if kapasite > 0 else 0
        if doluluk <= 70:
            dc, dt = _CLR_SUCCESS, "YETERLI"
        elif doluluk <= 95:
            dc, dt = _CLR_WARN, "SINIRDA"
        else:
            dc, dt = _CLR_ERR, "YETERSIZ"

        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.setPen(dc)
        fm = QFontMetrics(p.font())
        p.drawText(w - fm.horizontalAdvance(dt) - 15, 28, dt)

        p.setFont(QFont("Segoe UI", 10))
        p.setPen(_CLR_MUTED)
        p.drawText(12, 48,
                   f"{self._paralel_bara} paralel bara  |  "
                   f"{self._cevrim_dk}dk çevrim  |  "
                   f"{self._vardiya_sayisi} vardiya  |  "
                   f"Kapasite: {kapasite} bara/gün  |  "
                   f"Doluluk: %{doluluk:.0f}")

        # ── 3 yatay bar: Çinko, Nikel, Toplam ──
        bar_h = min(40, (h - TM - 120) // 4)
        bar_gap = 12
        rows = [
            ("Çinko", cinko, cinko_bara, _CLR_CINKO),
            ("Nikel", nikel, nikel_bara, _CLR_NIKEL),
            ("TOPLAM", self._urunler, toplam_bara, QColor("#8B5CF6")),
        ]

        for idx, (label, ulist, bara_t, color) in enumerate(rows):
            y = TM + idx * (bar_h + bar_gap)

            p.setPen(color)
            p.setFont(QFont("Segoe UI", 11, QFont.Bold))
            p.drawText(QRect(5, y, LM - 10, bar_h),
                       Qt.AlignVCenter | Qt.AlignRight, label)

            # Kapasite arka plan
            kap_w = int(kapasite * scale)
            p.fillRect(LM, y + 2, kap_w, bar_h - 4, _CLR_BOS)

            # Ürün segmentleri
            cx = LM
            for u in sorted(ulist, key=lambda u: u.get('bara_gerekli', 0), reverse=True):
                sb = u.get('bara_gerekli', 0)
                if sb <= 0:
                    continue
                sw = max(2, int(sb * scale))
                path = QPainterPath()
                path.addRoundedRect(QRectF(cx, y + 2, sw, bar_h - 4), 3, 3)
                p.fillPath(path, color)

                if sw > 40 and idx < 2:
                    p.setPen(QColor("white"))
                    p.setFont(QFont("Segoe UI", 8))
                    p.drawText(QRect(int(cx + 3), y + 2, sw - 6, bar_h - 4),
                               Qt.AlignVCenter | Qt.AlignLeft,
                               f"{u.get('adi', '?')[:12]} ({sb})")
                cx += sw

            p.setPen(_CLR_TEXT)
            p.setFont(QFont("Segoe UI", 10, QFont.Bold))
            tx = max(int(cx + 5), LM + int(bara_t * scale) + 5)
            p.drawText(QRect(tx, y, 120, bar_h),
                       Qt.AlignVCenter | Qt.AlignLeft, f"{bara_t} bara")

        bar_bottom = TM + 3 * (bar_h + bar_gap)

        # ── Kapasite çizgisi ──
        kap_x = LM + int(kapasite * scale)
        p.setPen(QPen(_CLR_KAP_LINE, 2, Qt.DashLine))
        p.drawLine(kap_x, TM - 5, kap_x, bar_bottom)
        p.setPen(_CLR_KAP_LINE)
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.drawText(kap_x + 5, TM + 5, f"Kapasite: {kapasite}")

        # ── Vardiya çizgileri ──
        for v in range(1, self._vardiya_sayisi + 1):
            vx = LM + int(self._vardiya_kapasite * v * scale)
            if vx < w - RM:
                p.setPen(QPen(QColor("#2A3545"), 1, Qt.DotLine))
                p.drawLine(vx, TM - 3, vx, bar_bottom)
                p.setPen(_CLR_MUTED)
                p.setFont(QFont("Segoe UI", 8))
                p.drawText(vx + 3, bar_bottom + 12, f"V{v}: {self._vardiya_kapasite * v}")

        # ── Alt detay tablosu ──
        tbl_y = bar_bottom + 25
        row_h = 19
        has_aski = any(u.get('bara_aski', 0) > 0 for u in self._urunler)
        if has_aski:
            cols_w = [LM - 15, 50, 65, 55, 55, 50]
            hdrs = ["Ürün", "Tip", "İhtiyaç", "Bara Ad.", "Askı", "Bara"]
        else:
            cols_w = [LM - 5, 55, 70, 60, 60]
            hdrs = ["Ürün", "Tip", "İhtiyaç", "Bara Ad.", "Bara"]

        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        cx = 5
        for hdr, cw in zip(hdrs, cols_w):
            p.setPen(_CLR_MUTED)
            p.drawText(QRect(cx, tbl_y, cw, row_h),
                       Qt.AlignVCenter | Qt.AlignLeft, hdr)
            cx += cw
        p.setPen(QPen(QColor("#2A3545"), 1))
        p.drawLine(5, tbl_y + row_h, cx, tbl_y + row_h)

        p.setFont(QFont("Segoe UI", 9))
        all_sorted = sorted(self._urunler,
                            key=lambda u: u.get('bara_gerekli', 0), reverse=True)
        for ri, u in enumerate(all_sorted):
            ry = tbl_y + (ri + 1) * row_h + 2
            if ry + row_h > h:
                break

            is_cinko = u.get('tip', '').lower() in ('cinko', 'zn')
            if has_aski:
                aski = u.get('bara_aski', 0)
                vals = [
                    u.get('adi', '?')[:20],
                    'Çinko' if is_cinko else 'Nikel',
                    f"{u.get('ihtiyac', 0):,}",
                    str(u.get('bara_adeti', 0)),
                    str(aski) if aski > 0 else '-',
                    str(u.get('bara_gerekli', 0)),
                ]
            else:
                vals = [
                    u.get('adi', '?')[:22],
                    'Çinko' if is_cinko else 'Nikel',
                    f"{u.get('ihtiyac', 0):,}",
                    str(u.get('bara_adeti', 0)),
                    str(u.get('bara_gerekli', 0)),
                ]
            cx = 5
            last_col = len(vals) - 1
            for ci, (v, cw) in enumerate(zip(vals, cols_w)):
                if ci == 1:
                    p.setPen(_CLR_CINKO if is_cinko else _CLR_NIKEL)
                elif ci == last_col:
                    bg = u.get('bara_gerekli', 0)
                    p.setPen(_CLR_ERR if bg >= 10 else
                             (_CLR_WARN if bg >= 5 else _CLR_TEXT))
                else:
                    p.setPen(_CLR_TEXT)
                p.drawText(QRect(cx, ry, cw, row_h),
                           Qt.AlignVCenter | Qt.AlignLeft, v)
                cx += cw

        p.end()

    def sizeHint(self):
        n = len(self._urunler) if self._urunler else 5
        return QSize(700, 260 + n * 19)


# ══════════════════════════════════════════════════════════════
#  ÇEVRİM PLAN OPTİMİZASYONU & WIDGET
# ══════════════════════════════════════════════════════════════

def optimize_cevrim_plan(urunler: list, paralel_bara: int = 15,
                         cevrim_dk: int = 90, vardiya_sayisi: int = 3,
                         vardiya_baslangic: str = "07:30",
                         setup_dk: int = 10, ktl_bara_gun: int = 0,
                         sya_tank: int = 4, yag_alma_dk: int = 15):
    """
    Ürünleri çevrim bazlı optimal sıraya dizer.
    Her çevrimde paralel_bara slotunu mümkün olduğunca doldurur.
    Baralar arası setup_dk dakika setup süresi ile saatlik plan çıkarır.

    Hat modeli (pipeline):
      - Baralar ardışık girer, aralarında setup_dk dk boşluk
      - Her bara cevrim_dk dk sonra çıkar
      - Bir çevrimde N bara varsa: ilk giriş T, son giriş T+(N-1)*setup
      - Sonraki çevrim başlangıç: T + N*setup (son giriş + setup)

    ktl_bara_gun: KTL hattından günlük gelen bara (ortak yağ alma kapasitesini düşürür)

    Returns: {
        'cevrimler': [[(adi, bara_aski, tip, urun_idx), ...], ...],
        'baralar': [{cevrim, sira, adi, tip, bara_no, giris, cikis, vardiya, ...}],
        'zaman': [{'ilk_giris', 'son_cikis', 'vardiya', ...}],
        'vardiyalar': [{no, baslangic, bitis, cevrim_adet, bara_adet}],
        'aski_analiz': [{...}],
        'ozet': {...},
    }
    """
    import math

    vardiya_dk = 480
    cevrim_per_v = vardiya_dk // max(cevrim_dk, 1)

    # Vardiya başlangıç dakikası (gece yarısından itibaren)
    bh, bm = [int(x) for x in vardiya_baslangic.split(':')]
    baslangic_dk = bh * 60 + bm  # 07:30 = 450

    # ── Pipeline kapasite: 1 vardiyada kaç bara alınabilir ──
    bara_per_vardiya = vardiya_dk // max(setup_dk, 1)  # 480/10 = 48
    bara_per_gun = bara_per_vardiya * vardiya_sayisi     # 48*3 = 144

    # ── Yağ alma (SYA) kapasite hesabı ──
    # SYA'da sya_tank adet banyo var (K5, K6, K7, K8 = 4 tank)
    # Her bara yağ almada yag_alma_dk dakika kalır
    # 4 tank paralel çalışır → her yag_alma_dk dakikada 4 bara işlenebilir
    # Günlük SYA kapasitesi = tank_sayisi × (günlük_dk / yag_alma_sure)
    gunluk_dk = vardiya_dk * vardiya_sayisi  # 480 × 3 = 1440 dk
    yag_alma_kapasite = sya_tank * (gunluk_dk // max(yag_alma_dk, 1))
    # Örn: 4 tank × (1440/15) = 4 × 96 = 384 bara/gün

    # KTL baraları da SYA'yı kullanıyor → kalan kapasite
    yag_alma_kalan = yag_alma_kapasite - ktl_bara_gun
    # Örn: 384 - 130 = 254 bara/gün kalan

    # Askı analizi
    aski_analiz = []
    for i, u in enumerate(urunler):
        ihtiyac = u.get('ihtiyac', 0)
        bara_adeti = u.get('bara_adeti', 1)
        bara_aski = u.get('bara_aski', 1)
        if ihtiyac <= 0:
            continue

        cevrim_uretim = bara_adeti * bara_aski
        gerekli_cevrim = math.ceil(ihtiyac / max(cevrim_uretim, 1))
        toplam_slot = gerekli_cevrim * bara_aski

        verimlilik = bara_aski / max(gerekli_cevrim, 1)

        aski_analiz.append({
            'idx': i,
            'adi': u.get('adi', '?'),
            'tip': u.get('tip', ''),
            'ihtiyac': ihtiyac,
            'bara_adeti': bara_adeti,
            'bara_aski': bara_aski,
            'cevrim_uretim': cevrim_uretim,
            'gerekli_cevrim': gerekli_cevrim,
            'toplam_slot': toplam_slot,
            'verimlilik': verimlilik,
            'kalan_cevrim': gerekli_cevrim,
        })

    # ── Greedy bin-packing ──
    cevrimler = []
    for _ in range(500):
        aktif = [a for a in aski_analiz if a['kalan_cevrim'] > 0]
        if not aktif:
            break

        slot = []
        kalan_bara = paralel_bara

        for a in sorted(aktif,
                        key=lambda x: (-x['bara_aski'], -x['kalan_cevrim'])):
            if a['kalan_cevrim'] <= 0:
                continue
            if a['bara_aski'] <= kalan_bara:
                slot.append((a['adi'], a['bara_aski'], a['tip'], a['idx']))
                kalan_bara -= a['bara_aski']
                a['kalan_cevrim'] -= 1

        cevrimler.append(slot)

    # ── Zaman hesaplama: setup destekli pipeline model ──
    def _dk_to_saat(toplam_dk):
        toplam_dk = int(toplam_dk) % (24 * 60)
        return f"{toplam_dk // 60:02d}:{toplam_dk % 60:02d}"

    baralar = []       # her fiziksel bara detayı
    zaman = []         # çevrim bazlı özet zaman
    vardiyalar = {}
    cursor_dk = baslangic_dk  # pipeline imleci (dakika cinsinden)
    toplam_bara = 0

    for ci, slot in enumerate(cevrimler):
        bara_count = sum(x[1] for x in slot)
        ilk_giris_dk = cursor_dk
        son_giris_dk = cursor_dk + (bara_count - 1) * setup_dk
        son_cikis_dk = son_giris_dk + cevrim_dk

        # Vardiya tespiti (ilk giriş saatine göre)
        gecen_dk = ilk_giris_dk - baslangic_dk
        v_no = int(gecen_dk // vardiya_dk) + 1
        c_no_in_v = int((gecen_dk % vardiya_dk) // max(
            bara_count * setup_dk + (cevrim_dk - bara_count * setup_dk), cevrim_dk)) + 1

        zaman.append({
            'ilk_giris': _dk_to_saat(ilk_giris_dk),
            'son_cikis': _dk_to_saat(son_cikis_dk),
            'ilk_giris_dk': ilk_giris_dk,
            'son_cikis_dk': son_cikis_dk,
            'vardiya': v_no,
            'bara_adet': bara_count,
        })

        # Her bara için detay satırı
        bara_sira = 0
        for adi, aski, tip, uidx in slot:
            for b in range(aski):
                giris_dk = cursor_dk + bara_sira * setup_dk
                cikis_dk = giris_dk + cevrim_dk
                toplam_bara += 1

                baralar.append({
                    'cevrim': ci,
                    'sira': bara_sira + 1,
                    'adi': adi,
                    'tip': tip,
                    'uidx': uidx,
                    'bara_no': f"{b+1}/{aski}",
                    'giris': _dk_to_saat(giris_dk),
                    'cikis': _dk_to_saat(cikis_dk),
                    'giris_dk': giris_dk,
                    'cikis_dk': cikis_dk,
                    'vardiya': v_no,
                })
                bara_sira += 1

        # Sonraki çevrim: son giriş + setup (pipeline devam)
        cursor_dk = cursor_dk + bara_count * setup_dk

        # Vardiya bilgisi
        if v_no not in vardiyalar:
            vardiyalar[v_no] = {
                'no': v_no,
                'baslangic': _dk_to_saat(ilk_giris_dk),
                'baslangic_dk': ilk_giris_dk,
                'bitis': _dk_to_saat(son_cikis_dk),
                'bitis_dk': son_cikis_dk,
                'cevrim_adet': 0,
                'bara_adet': 0,
            }
        vardiyalar[v_no]['bitis'] = _dk_to_saat(son_cikis_dk)
        vardiyalar[v_no]['bitis_dk'] = son_cikis_dk
        vardiyalar[v_no]['cevrim_adet'] += 1
        vardiyalar[v_no]['bara_adet'] += bara_count

    vardiya_list = sorted(vardiyalar.values(), key=lambda x: x['no'])

    # ── Özet hesaplar ──
    toplam_cevrim = len(cevrimler)
    vardiya_gerekli = len(vardiyalar)
    toplam_slot_kullanilan = sum(sum(x[1] for x in c) for c in cevrimler)
    toplam_slot_mevcut = toplam_cevrim * paralel_bara
    verimlilik_pct = (toplam_slot_kullanilan / toplam_slot_mevcut * 100
                      ) if toplam_slot_mevcut > 0 else 0

    # Pipeline süre: ilk giriş → son çıkış (toplam dk)
    toplam_sure_dk = (cursor_dk - baslangic_dk) + cevrim_dk if cevrimler else 0

    # Boş çevrimler
    bos_cevrimler = []
    for ci, slot in enumerate(cevrimler):
        kullanilan = sum(x[1] for x in slot)
        bos = paralel_bara - kullanilan
        if bos > paralel_bara * 0.5:
            bos_cevrimler.append({
                'cevrim': ci,
                'vardiya': zaman[ci]['vardiya'] if ci < len(zaman) else 0,
                'kullanilan': kullanilan,
                'bos': bos,
            })

    # Kalan_cevrim sıfırla
    for a in aski_analiz:
        a['kalan_cevrim'] = a['gerekli_cevrim']

    return {
        'cevrimler': cevrimler,
        'baralar': baralar,
        'zaman': zaman,
        'vardiyalar': vardiya_list,
        'aski_analiz': sorted(aski_analiz,
                              key=lambda x: x['verimlilik']),
        'bos_cevrimler': bos_cevrimler,
        'ozet': {
            'toplam_cevrim': toplam_cevrim,
            'toplam_bara': toplam_bara,
            'vardiya_gerekli': vardiya_gerekli,
            'gun_gerekli': round(vardiya_gerekli / max(vardiya_sayisi, 1), 1),
            'verimlilik_pct': verimlilik_pct,
            'toplam_slot': toplam_slot_mevcut,
            'kullanilan_slot': toplam_slot_kullanilan,
            'bos_slot': toplam_slot_mevcut - toplam_slot_kullanilan,
            'cevrim_per_v': cevrim_per_v,
            'baslangic': vardiya_baslangic,
            'setup_dk': setup_dk,
            'toplam_sure_dk': toplam_sure_dk,
            # Pipeline kapasite bilgisi
            'bara_per_vardiya': bara_per_vardiya,
            'bara_per_gun': bara_per_gun,
            'ktl_bara_gun': ktl_bara_gun,
            'yag_alma_kapasite': yag_alma_kapasite,
            'yag_alma_kalan': yag_alma_kalan,
            'sya_tank': sya_tank,
            'yag_alma_dk': yag_alma_dk,
        },
    }


# Ürün renkleri - tekrar eden ürünlere tutarlı renk atamak için
_URUN_RENK_PALETI = [
    QColor("#F59E0B"), QColor("#3B82F6"), QColor("#10B981"), QColor("#EF4444"),
    QColor("#8B5CF6"), QColor("#EC4899"), QColor("#06B6D4"), QColor("#F97316"),
    QColor("#84CC16"), QColor("#E879F9"), QColor("#14B8A6"), QColor("#FB923C"),
    QColor("#A78BFA"), QColor("#F472B6"), QColor("#22D3EE"), QColor("#FACC15"),
    QColor("#34D399"), QColor("#FB7185"), QColor("#818CF8"), QColor("#2DD4BF"),
]


class CevrimPlanWidget(QWidget):
    """Çevrim bazlı hat doluluk planı - QPainter ile grid görünüm"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plan = None   # optimize_cevrim_plan() sonucu
        self._paralel_bara = 15
        self._cevrim_dk = 90
        self._hover_cell = (-1, -1)
        self.setMouseTracking(True)
        self.setMinimumHeight(400)

    def set_plan(self, plan: dict, paralel_bara: int = 15, cevrim_dk: int = 90):
        self._plan = plan
        self._paralel_bara = paralel_bara
        self._cevrim_dk = cevrim_dk
        cevrim_count = plan['ozet']['toplam_cevrim'] if plan else 0
        h = 220 + max(cevrim_count, 5) * 26
        self.setMinimumHeight(h)
        self.update()

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, _CLR_BG)

        if not self._plan:
            p.setPen(_CLR_MUTED)
            p.setFont(QFont("Segoe UI", 12))
            p.drawText(QRect(0, 0, w, h), Qt.AlignCenter,
                       "Hesapla butonuna basarak çevrim planını oluşturun.")
            p.end()
            return

        ozet = self._plan['ozet']
        cevrimler = self._plan['cevrimler']
        aski_analiz = self._plan['aski_analiz']
        cevrim_per_v = ozet['cevrim_per_v']

        # Ürün -> renk haritası
        urun_renkler = {}
        ri = 0
        for a in aski_analiz:
            if a['adi'] not in urun_renkler:
                urun_renkler[a['adi']] = _URUN_RENK_PALETI[ri % len(_URUN_RENK_PALETI)]
                ri += 1

        # ── Başlık ──
        p.setPen(_CLR_TEXT)
        p.setFont(QFont("Segoe UI", 14, QFont.Bold))
        p.drawText(12, 28, "Çevrim Bazlı Hat Doluluk Planı")

        ver = ozet['verimlilik_pct']
        if ver >= 70:
            vc, vt = _CLR_SUCCESS, f"Verimlilik: %{ver:.0f}"
        elif ver >= 40:
            vc, vt = _CLR_WARN, f"Verimlilik: %{ver:.0f}"
        else:
            vc, vt = _CLR_ERR, f"Verimlilik: %{ver:.0f}"
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.setPen(vc)
        fm = QFontMetrics(p.font())
        p.drawText(w - fm.horizontalAdvance(vt) - 15, 28, vt)

        zaman = self._plan.get('zaman', [])
        vardiyalar = self._plan.get('vardiyalar', [])

        p.setFont(QFont("Segoe UI", 10))
        p.setPen(_CLR_MUTED)
        baslangic_str = ozet.get('baslangic', '07:30')
        bitis_str = zaman[-1]['son_cikis'] if zaman else '?'
        setup_dk = ozet.get('setup_dk', 10)
        toplam_bara = ozet.get('toplam_bara', 0)
        p.drawText(12, 48,
                   f"{ozet['toplam_cevrim']} çevrim  |  "
                   f"{toplam_bara} bara  |  "
                   f"Setup: {setup_dk}dk  |  "
                   f"{baslangic_str} → {bitis_str}  |  "
                   f"{ozet['vardiya_gerekli']} vardiya  |  "
                   f"{ozet['gun_gerekli']} gün")

        # KTL / Yağ alma satırı (varsa)
        ktl = ozet.get('ktl_bara_gun', 0)
        if ktl > 0:
            p.setFont(QFont("Segoe UI", 9))
            sya_tank = ozet.get('sya_tank', 4)
            yag_dk = ozet.get('yag_alma_dk', 15)
            yag_kapasite = ozet.get('yag_alma_kapasite', 0)
            yag_kalan = ozet.get('yag_alma_kalan', 0)
            if yag_kalan < toplam_bara:
                p.setPen(_CLR_ERR)
                durum = "KAPASITE YETERSIZ"
            elif yag_kalan < toplam_bara * 1.2:
                p.setPen(_CLR_WARN)
                durum = "SINIRDA"
            else:
                p.setPen(_CLR_SUCCESS)
                durum = "YETERLI"
            p.drawText(12, 62,
                       f"SYA: {sya_tank} tank × {yag_dk}dk = {yag_kapasite} bara/gün  |  "
                       f"KTL: -{ktl}  |  "
                       f"Kalan: {yag_kalan}  |  "
                       f"İhtiyaç: {toplam_bara}  →  {durum}")

        # ── Askı Analizi (sol üst) ──
        ax_y = 65
        ktl_shown = ozet.get('ktl_bara_gun', 0) > 0
        if ktl_shown:
            ax_y += 18  # KTL satırı için ek boşluk
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.setPen(_CLR_TEXT)
        p.drawText(12, ax_y, "Askı Analizi (darboğaz sırası):")

        ax_y += 5
        p.setFont(QFont("Segoe UI", 9))
        col_w = [130, 40, 50, 50, 55]
        hdrs = ["Ürün", "Askı", "Çevrim", "Slot", "Verim"]
        cx = 12
        for hdr, cw in zip(hdrs, col_w):
            p.setPen(_CLR_MUTED)
            p.drawText(QRect(cx, ax_y, cw, 16), Qt.AlignVCenter | Qt.AlignLeft, hdr)
            cx += cw

        ax_y += 17
        for ai, a in enumerate(aski_analiz[:8]):
            color = urun_renkler.get(a['adi'], _CLR_TEXT)
            vals = [
                a['adi'][:18],
                str(a['bara_aski']),
                str(a['gerekli_cevrim']),
                str(a['toplam_slot']),
                f"{a['verimlilik']:.2f}",
            ]
            cx = 12
            for ci, (v, cw) in enumerate(zip(vals, col_w)):
                if ci == 0:
                    p.setPen(color)
                elif ci == 4:
                    if a['verimlilik'] < 0.1:
                        p.setPen(_CLR_ERR)
                    elif a['verimlilik'] < 0.5:
                        p.setPen(_CLR_WARN)
                    else:
                        p.setPen(_CLR_SUCCESS)
                else:
                    p.setPen(_CLR_TEXT)
                p.drawText(QRect(cx, ax_y, cw, 16),
                           Qt.AlignVCenter | Qt.AlignLeft, v)
                cx += cw
            ax_y += 16

        # ── Çevrim Grid ──
        grid_top = max(ax_y + 15, 220)
        grid_left = 130  # daha geniş: saat + V-C label sığması için
        cell_h = 22
        bara_w = max(20, min(40, (w - grid_left - 20) // self._paralel_bara))
        grid_w = bara_w * self._paralel_bara

        # Vardiya 1 başlık
        if vardiyalar:
            vd = vardiyalar[0]
            p.setPen(QColor("#F59E0B"))
            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            v1_txt = f"Vardiya {vd['no']}: {vd['baslangic']} - {vd['bitis']}"
            p.drawText(QRect(grid_left, grid_top - 30, grid_w, 14),
                       Qt.AlignCenter, v1_txt)

        # Header: bara numaraları
        p.setFont(QFont("Segoe UI", 8))
        for bi in range(self._paralel_bara):
            bx = grid_left + bi * bara_w
            p.setPen(_CLR_MUTED)
            p.drawText(QRect(bx, grid_top - 15, bara_w, 14),
                       Qt.AlignCenter, f"B{bi+1}")

        # Çevrim satırları
        for ci, slot in enumerate(cevrimler):
            y = grid_top + ci * cell_h
            if y + cell_h > h:
                break

            v_no = ci // cevrim_per_v + 1
            c_no = ci % cevrim_per_v + 1

            # Zaman bilgisi (pipeline: ilk giriş → son çıkış)
            giris_str = zaman[ci]['ilk_giris'] if ci < len(zaman) else ''
            cikis_str = zaman[ci]['son_cikis'] if ci < len(zaman) else ''
            bara_cnt = zaman[ci]['bara_adet'] if ci < len(zaman) else 0

            # Sol label: saat aralığı + çevrim no
            p.setPen(_CLR_MUTED)
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(QRect(2, y, grid_left - 5, cell_h),
                       Qt.AlignVCenter | Qt.AlignRight,
                       f"{giris_str}-{cikis_str}  V{v_no}-Ç{c_no}")

            # Vardiya ayırıcı çizgi + vardiya bilgisi
            if c_no == 1 and ci > 0:
                p.setPen(QPen(_CLR_KAP_LINE, 2))
                p.drawLine(grid_left, y - 1, grid_left + grid_w, y - 1)
                # Vardiya başlık
                vi = v_no - 1
                if vi < len(vardiyalar):
                    vd = vardiyalar[vi]
                    p.setPen(QColor("#F59E0B"))
                    p.setFont(QFont("Segoe UI", 7, QFont.Bold))
                    vd_txt = f"── Vardiya {vd['no']}: {vd['baslangic']} - {vd['bitis']} ──"
                    p.drawText(QRect(grid_left, y - 14, grid_w, 13),
                               Qt.AlignCenter, vd_txt)

            # Hücreleri çiz
            bx = grid_left
            for adi, aski, tip, uidx in slot:
                color = urun_renkler.get(adi, _CLR_MUTED)
                seg_w = aski * bara_w

                # Hücre arka planı
                path = QPainterPath()
                path.addRoundedRect(QRectF(bx + 1, y + 1, seg_w - 2, cell_h - 2), 3, 3)
                p.fillPath(path, color)

                # Ürün adı (yeterli genişlikte ise)
                if seg_w > 30:
                    p.setPen(QColor("white"))
                    p.setFont(QFont("Segoe UI", 7))
                    p.drawText(QRect(int(bx + 3), y + 1, seg_w - 6, cell_h - 2),
                               Qt.AlignVCenter | Qt.AlignLeft,
                               f"{adi[:seg_w // 7]}")

                bx += seg_w

            # Boş slotlar
            kullanilan = sum(x[1] for x in slot)
            bos = self._paralel_bara - kullanilan
            if bos > 0:
                p.fillRect(int(bx), y + 1,
                           bos * bara_w, cell_h - 2, QColor("#0D1117"))
                # Boş göstergesi
                if bos > 2:
                    p.setPen(QColor("#2A3545"))
                    p.setFont(QFont("Segoe UI", 7))
                    p.drawText(QRect(int(bx), y + 1, bos * bara_w, cell_h - 2),
                               Qt.AlignCenter, f"{bos} boş")

            # Sağda yüzde
            pct = kullanilan / self._paralel_bara * 100
            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            if pct >= 80:
                p.setPen(_CLR_SUCCESS)
            elif pct >= 40:
                p.setPen(_CLR_WARN)
            else:
                p.setPen(_CLR_ERR)
            p.drawText(QRect(grid_left + grid_w + 5, y, 50, cell_h),
                       Qt.AlignVCenter | Qt.AlignLeft, f"%{pct:.0f}")

        # ── Lejant ──
        lej_x = grid_left + grid_w + 60
        lej_y = grid_top
        if lej_x + 150 < w:
            p.setFont(QFont("Segoe UI", 9, QFont.Bold))
            p.setPen(_CLR_TEXT)
            p.drawText(lej_x, lej_y, "Ürünler:")
            lej_y += 18

            p.setFont(QFont("Segoe UI", 8))
            for adi, color in urun_renkler.items():
                if lej_y + 14 > h:
                    break
                p.fillRect(lej_x, lej_y + 2, 10, 10, color)
                p.setPen(_CLR_TEXT)
                p.drawText(lej_x + 14, lej_y + 11, adi[:15])
                lej_y += 15

        p.end()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self._plan:
            return
        cevrimler = self._plan['cevrimler']
        zaman = self._plan.get('zaman', [])
        baralar = self._plan.get('baralar', [])
        grid_top = max(220, 65 + 5 + 17 + min(len(self._plan['aski_analiz']), 8) * 16 + 15)
        ktl = self._plan['ozet'].get('ktl_bara_gun', 0)
        if ktl > 0:
            grid_top += 18
        grid_left = 130
        cell_h = 22
        bara_w = max(20, min(40, (self.width() - grid_left - 20) // self._paralel_bara))

        mx, my = event.pos().x(), event.pos().y()
        ci = int((my - grid_top) / cell_h)
        if 0 <= ci < len(cevrimler):
            slot = cevrimler[ci]
            bx = grid_left
            for adi, aski, tip, uidx in slot:
                seg_w = aski * bara_w
                if bx <= mx <= bx + seg_w:
                    a = next((x for x in self._plan['aski_analiz'] if x['idx'] == uidx), None)
                    if a:
                        # Bu ürünün bu çevrimdeki bara detayları
                        cev_baralar = [b for b in baralar
                                       if b['cevrim'] == ci and b['adi'] == adi]
                        tip_str = f"Ürün: {a['adi']}\n"
                        tip_str += f"Tip: {a['tip']}\n"
                        tip_str += f"Askı: {a['bara_aski']} bara\n"
                        if cev_baralar:
                            tip_str += f"İlk giriş: {cev_baralar[0]['giris']}\n"
                            tip_str += f"Son çıkış: {cev_baralar[-1]['cikis']}\n"
                            for b in cev_baralar:
                                tip_str += f"  Bara {b['bara_no']}: {b['giris']}→{b['cikis']}\n"
                        tip_str += f"İhtiyaç: {a['ihtiyac']:,} adet\n"
                        tip_str += f"Çevrim üretim: {a['cevrim_uretim']:,} adet\n"
                        tip_str += f"Gerekli çevrim: {a['gerekli_cevrim']}"
                        QToolTip.showText(event.globalPosition().toPoint(), tip_str, self)
                    return
                bx += seg_w

    def sizeHint(self):
        if self._plan:
            n = self._plan['ozet']['toplam_cevrim']
            return QSize(800, 220 + n * 22)
        return QSize(800, 400)
