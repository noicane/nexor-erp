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
