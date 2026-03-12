# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Global RFID Kart Okuyucu Servisi
QApplication seviyesinde tüm tuş vuruşlarını yakalar.
Kart okutulduğunda subscriber'lara sinyal gönderir.
Login, iş emri onay, kalite kontrol vs. her yerde kullanılır.
"""

from PySide6.QtCore import QObject, Signal, QEvent
from PySide6.QtWidgets import QApplication
from core.rfid_reader import RFIDCardReader
from config import RFID_LOGIN_ENABLED


class RFIDService(QObject):
    """
    Global RFID kart okuyucu servisi.

    Kullanım:
        # Başlatma (main.py'de bir kere):
        rfid_svc = RFIDService.instance()
        rfid_svc.start()

        # Herhangi bir modülde kart okuma:
        from core.rfid_service import RFIDService
        RFIDService.instance().card_detected.connect(self._on_card)

        # Geçici olarak durdurmak (örn. metin girişi sırasında):
        RFIDService.instance().set_paused(True)
        # ... metin girişi ...
        RFIDService.instance().set_paused(False)
    """

    card_detected = Signal(str)   # Kart ID okunduğunda
    card_reading = Signal(bool)   # Okuma durumu değiştiğinde

    _instance = None

    @classmethod
    def instance(cls) -> "RFIDService":
        """Singleton instance döndürür."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self._reader = RFIDCardReader(self)
        self._reader.set_active(False)
        self._reader.card_detected.connect(self._on_card)
        self._reader.card_reading.connect(self.card_reading.emit)
        self._started = False
        self._paused = False

    def start(self):
        """Servisi başlat - QApplication eventFilter olarak yükle."""
        if self._started or not RFID_LOGIN_ENABLED:
            return
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
            self._reader.set_active(True)
            self._started = True

    def stop(self):
        """Servisi durdur."""
        if not self._started:
            return
        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)
        self._reader.set_active(False)
        self._started = False

    def set_paused(self, paused: bool):
        """Geçici olarak duraklat/devam ettir."""
        self._paused = paused
        self._reader.set_active(not paused and self._started)

    def is_active(self) -> bool:
        return self._started and not self._paused

    def eventFilter(self, obj, event):
        """QApplication seviyesinde tüm KeyPress olaylarını yakala."""
        if event.type() == QEvent.Type.KeyPress and not self._paused:
            # Sadece focused widget için işle (parent propagation'dan gelen duplikeleri önle)
            app = QApplication.instance()
            if app and obj is app.focusWidget():
                if self._reader.process_key(event):
                    return True  # Enter tüketildi (kart algılandı)
        return False

    def _on_card(self, card_id: str):
        """Dahili reader'dan gelen kart sinyalini dışarı ilet."""
        self.card_detected.emit(card_id)
