# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Splash Screen
Uygulama açılış ekranı - PRAXIS kurumsal stil

- Logo + uygulama adı
- Yükleme ilerleme çubuğu
- Durum mesajları
"""

from PySide6.QtWidgets import QSplashScreen, QProgressBar, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QFont

from version import VERSION


class NexorSplashScreen(QSplashScreen):
    """NEXOR ERP açılış ekranı."""

    def __init__(self):
        # Boş pixmap oluştur ve üzerine çiz
        pixmap = QPixmap(520, 360)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Arka plan gradient
        gradient = QLinearGradient(0, 0, 0, 360)
        gradient.setColorAt(0, QColor("#0B0E13"))
        gradient.setColorAt(1, QColor("#0F1419"))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 520, 360, 16, 16)

        # Üst kırmızı accent çizgi
        red_gradient = QLinearGradient(0, 0, 520, 0)
        red_gradient.setColorAt(0, QColor("#E2130D"))
        red_gradient.setColorAt(1, QColor("#FF4136"))
        painter.setBrush(red_gradient)
        painter.drawRect(0, 0, 520, 4)

        # REDLINE yazısı
        painter.setPen(QColor("#5C6878"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Normal))
        painter.drawText(0, 90, 520, 30, Qt.AlignCenter, "REDLINE")

        # NEXOR yazısı
        painter.setPen(QColor("#E8ECF1"))
        painter.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        painter.drawText(0, 115, 520, 60, Qt.AlignCenter, "NEXOR")

        # ERP YÖNETİM SİSTEMLERİ yazısı (kırmızı)
        painter.setPen(QColor("#E2130D"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        painter.drawText(0, 175, 520, 30, Qt.AlignCenter, "ERP YÖNETİM SİSTEMLERİ")

        # Alt kırmızı çizgi (dekoratif)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#E2130D"))
        painter.drawRect(180, 212, 160, 2)

        # Versiyon
        painter.setPen(QColor("#5C6878"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(0, 330, 510, 20, Qt.AlignRight, f"v{VERSION}")

        # Powered by
        painter.setPen(QColor("#3A4250"))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(10, 330, 300, 20, Qt.AlignLeft, "Redline Creative Solutions")

        painter.end()

        super().__init__(pixmap)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        # Progress bar
        self.progress = QProgressBar(self)
        self.progress.setGeometry(40, 280, 440, 6)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #1E2736;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E2130D, stop:1 #FF4136);
                border-radius: 3px;
            }
        """)

        # Durum mesajı
        self.status_label = QLabel(self)
        self.status_label.setGeometry(40, 292, 440, 20)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #5C6878; font-size: 10px;")
        self.status_label.setText("Başlatılıyor...")

    def set_progress(self, value: int, message: str = ""):
        """İlerleme ve mesaj güncelle."""
        self.progress.setValue(value)
        if message:
            self.status_label.setText(message)
        self.repaint()

    def start_loading(self, callback):
        """
        Yükleme animasyonu başlatır ve bitince callback çağırır.

        Kullanım:
            splash.start_loading(on_loaded)
        """
        self._callback = callback
        self._step = 0
        self._steps = [
            (10, "Konfigürasyon yükleniyor..."),
            (25, "Veritabanı bağlantısı kontrol ediliyor..."),
            (40, "Güncelleme kontrol ediliyor..."),
            (60, "Modüller hazırlanıyor..."),
            (80, "Arayüz yükleniyor..."),
            (100, "Hazır!"),
        ]
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(400)

    def _advance(self):
        if self._step < len(self._steps):
            val, msg = self._steps[self._step]
            self.set_progress(val, msg)
            self._step += 1
        else:
            self._timer.stop()
            QTimer.singleShot(300, self._callback)
