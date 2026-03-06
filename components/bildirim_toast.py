# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Toast Bildirim Sistemi
Sağ alt köşede anlık bildirim popup gösterimi

Kullanım:
    from components.bildirim_toast import ToastManager

    # Uygulama başlatırken (MainWindow'da)
    self.toast_manager = ToastManager(self, theme)

    # Bildirim göster
    self.toast_manager.show_toast(
        baslik="Yeni İş Emri",
        mesaj="IE-2026-0150 size atandı",
        onem="NORMAL",
        modul="IS_EMIRLERI"
    )
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QApplication
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, QRect, Property
)
from PySide6.QtGui import QColor


_ONEM_COLORS = {
    'KRITIK': '#ef4444',
    'YUKSEK': '#f97316',
    'NORMAL': '#3b82f6',
    'DUSUK': '#6b7280',
}

_ONEM_ICONS = {
    'KRITIK': '🔴',
    'YUKSEK': '🟠',
    'NORMAL': '🔵',
    'DUSUK': '⚪',
}

_MODUL_ICONS = {
    'KALITE': '✅', 'URETIM': '🏭', 'BAKIM': '🔧', 'IK': '👥',
    'STOK': '📦', 'SEVKIYAT': '🚚', 'SISTEM': '⚙️', 'IS_EMIRLERI': '📋',
    'ISG': '🦺', 'SATINALMA': '🛒', 'LAB': '🔬', 'CEVRE': '🌿',
}


class ToastWidget(QFrame):
    """Tek bir toast bildirim widget'ı"""
    closed = Signal(object)
    clicked = Signal(dict)

    def __init__(self, bildirim: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.bildirim = bildirim
        self.theme = theme
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFixedWidth(360)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        t = self.theme
        onem = self.bildirim.get('onem', 'NORMAL')
        border_color = _ONEM_COLORS.get(onem, '#3b82f6')

        self.setStyleSheet(f"""
            ToastWidget {{
                background: {t.get('bg_card', '#1E1E1E')};
                border: 1px solid {t.get('border', '#2A2A2A')};
                border-left: 4px solid {border_color};
                border-radius: 10px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Üst satır: modül + önem + kapatma butonu
        header = QHBoxLayout()
        header.setSpacing(6)

        modul = self.bildirim.get('modul', '')
        modul_icon = _MODUL_ICONS.get(modul, '📋')
        lbl_modul = QLabel(f"{modul_icon} {modul}")
        lbl_modul.setStyleSheet(f"""
            color: {t.get('text_muted', '#666')};
            font-size: 11px; background: transparent;
        """)
        header.addWidget(lbl_modul)
        header.addStretch()

        onem_icon = _ONEM_ICONS.get(onem, '🔵')
        lbl_onem = QLabel(f"{onem_icon} {onem}")
        lbl_onem.setStyleSheet(f"color: {border_color}; font-size: 10px; font-weight: bold; background: transparent;")
        header.addWidget(lbl_onem)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {t.get('text_muted', '#666')}; font-size: 14px;
            }}
            QPushButton:hover {{ color: {t.get('text', '#FFF')}; }}
        """)
        btn_close.clicked.connect(self._close)
        header.addWidget(btn_close)

        layout.addLayout(header)

        # Başlık
        lbl_baslik = QLabel(self.bildirim.get('baslik', ''))
        lbl_baslik.setStyleSheet(f"color: {t.get('text', '#FFF')}; font-size: 13px; font-weight: bold; background: transparent;")
        lbl_baslik.setWordWrap(True)
        layout.addWidget(lbl_baslik)

        # Mesaj (kısa)
        mesaj = self.bildirim.get('mesaj', '')
        if len(mesaj) > 120:
            mesaj = mesaj[:117] + '...'
        if mesaj:
            lbl_mesaj = QLabel(mesaj)
            lbl_mesaj.setStyleSheet(f"color: {t.get('text_secondary', '#AAA')}; font-size: 12px; background: transparent;")
            lbl_mesaj.setWordWrap(True)
            layout.addWidget(lbl_mesaj)

    def _setup_timer(self):
        """Otomatik kapanma zamanlayıcısı."""
        onem = self.bildirim.get('onem', 'NORMAL')
        # Kritik bildirimler daha uzun süre gösterilir
        süreler = {'KRITIK': 10000, 'YUKSEK': 7000, 'NORMAL': 5000, 'DUSUK': 4000}
        süre = süreler.get(onem, 5000)

        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self._close)
        self._close_timer.start(süre)

    def _close(self):
        self._close_timer.stop()
        self.closed.emit(self)
        self.close()
        self.deleteLater()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._close_timer.stop()
            self.clicked.emit(self.bildirim)
            self._close()

    def enterEvent(self, event):
        """Mouse üstüne gelince zamanlayıcıyı durdur."""
        self._close_timer.stop()

    def leaveEvent(self, event):
        """Mouse ayrılınca zamanlayıcıyı tekrar başlat."""
        self._close_timer.start(3000)


class ToastManager:
    """Toast bildirimlerini yöneten sınıf"""

    def __init__(self, parent_window, theme: dict):
        self.parent = parent_window
        self.theme = theme
        self._active_toasts: list[ToastWidget] = []
        self._max_toasts = 4
        self._toast_spacing = 10
        self._margin_bottom = 20
        self._margin_right = 20

    def show_toast(
        self,
        baslik: str,
        mesaj: str = '',
        onem: str = 'NORMAL',
        modul: str = 'SISTEM',
        bildirim_data: dict = None,
    ):
        """Yeni toast bildirim göster."""
        if len(self._active_toasts) >= self._max_toasts:
            # En eski toast'ı kapat
            oldest = self._active_toasts[0]
            oldest._close()

        data = bildirim_data or {
            'baslik': baslik,
            'mesaj': mesaj,
            'onem': onem,
            'modul': modul,
        }

        toast = ToastWidget(data, self.theme)
        toast.closed.connect(self._on_toast_closed)
        toast.clicked.connect(self._on_toast_clicked)

        self._active_toasts.append(toast)
        self._reposition_toasts()
        toast.show()

    def _reposition_toasts(self):
        """Tüm toast'ların pozisyonlarını yeniden hesapla."""
        screen = QApplication.primaryScreen()
        if not screen:
            return
        screen_geo = screen.availableGeometry()

        y_offset = self._margin_bottom
        for toast in reversed(self._active_toasts):
            toast.adjustSize()
            x = screen_geo.right() - toast.width() - self._margin_right
            y = screen_geo.bottom() - toast.height() - y_offset
            toast.move(x, y)
            y_offset += toast.height() + self._toast_spacing

    def _on_toast_closed(self, toast):
        """Toast kapandığında listeden çıkar."""
        if toast in self._active_toasts:
            self._active_toasts.remove(toast)
        self._reposition_toasts()

    def _on_toast_clicked(self, bildirim: dict):
        """Toast'a tıklanınca - sayfa yönlendirme yapılabilir."""
        # MainWindow'da bu sinyale bağlanarak sayfa yönlendirmesi yapılabilir
        pass

    def update_theme(self, theme: dict):
        """Tema değişikliğini uygula."""
        self.theme = theme
