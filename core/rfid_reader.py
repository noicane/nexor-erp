# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - USB RFID/NFC Kart Okuyucu
USB HID kart okuyuculardan gelen hızlı tuş vuruşlarını algılar.
Kart okuyucular klavye emülasyonu yapar: kart ID'sini hızlı tuş vuruşları + Enter olarak gönderir.
"""

from PySide6.QtCore import QObject, Signal, QElapsedTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from config import (
    RFID_KEYSTROKE_TIMEOUT_MS,
    RFID_MIN_CARD_LENGTH,
    RFID_MAX_CARD_LENGTH,
    RFID_BUFFER_RESET_MS,
)


class RFIDCardReader(QObject):
    """
    USB HID RFID/NFC kart okuyucu tuş vuruşu algılayıcı.

    Çalışma mantığı:
      1. Widget'ların eventFilter'ına bağlanarak tuş vuruşlarını yakalar.
      2. Ardışık tuş vuruşları arasındaki süreyi ölçer.
      3. Hızlı tuş vuruşları (< RFID_KEYSTROKE_TIMEOUT_MS) buffer'a yazılır.
      4. Enter/Return geldiğinde buffer uzunluğu uygunsa card_detected sinyali emit edilir.
      5. Yavaş tuş vuruşları (normal insan yazımı) buffer'ı sıfırlar ve widget'a geçirilir.

    Sinyaller:
      card_detected(str)  – Geçerli bir kart ID okunduğunda emit edilir.
      card_reading(bool)  – Okuma başladığında True, bittiğinde False emit edilir.
    """

    card_detected = Signal(str)
    card_reading = Signal(bool)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._buffer: str = ""
        self._timer = QElapsedTimer()
        self._active = True
        self._is_reading = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_active(self, active: bool):
        """Okuyucuyu aktif/pasif yap."""
        self._active = active
        if not active:
            self._reset_buffer()

    def is_active(self) -> bool:
        return self._active

    def process_key(self, event: QKeyEvent) -> bool:
        """
        Bir tuş vuruşunu işler.

        Şeffaf (transparent) yaklaşım:
          - Yazdırılabilir karakterler ASLA tüketilmez (return False).
            Böylece QLineEdit'ler normal çalışmaya devam eder.
          - Karakterler arka planda buffer'da takip edilir.
          - Yalnızca Enter tuşu, buffer'da geçerli bir kart ID varsa tüketilir.
          - Kart okunduğunda card_detected sinyali emit edilir; çağıran taraf
            QLineEdit'lerdeki artık karakterleri temizlemelidir.

        Returns:
            True  – Enter tüketildi (kart algılandı), widget'a iletilmemeli.
            False – Normal tuş, widget kendi işlesin.
        """
        if not self._active:
            return False

        key = event.key()
        text = event.text()

        # Modifier tuşlarını (Shift, Ctrl vb.) yoksay
        if key in (
            0x01000020,  # Qt.Key_Shift
            0x01000021,  # Qt.Key_Control
            0x01000023,  # Qt.Key_Alt
            0x01000024,  # Qt.Key_Meta
        ):
            return False

        now_elapsed = self._timer.elapsed() if self._timer.isValid() else RFID_BUFFER_RESET_MS + 1

        # Enter / Return tuşu
        if key in (0x01000004, 0x01000005):  # Qt.Key_Return, Qt.Key_Enter
            if self._buffer and RFID_MIN_CARD_LENGTH <= len(self._buffer) <= RFID_MAX_CARD_LENGTH:
                card_id = self._buffer
                print(f"[RFID] Kart algılandı: {card_id} ({len(card_id)} karakter)")
                self._reset_buffer()
                self.card_detected.emit(card_id)
                return True  # Sadece burada tüket – kart algılandı
            else:
                if self._buffer:
                    print(f"[RFID] Buffer geçersiz: '{self._buffer}' ({len(self._buffer)} karakter)")
                self._reset_buffer()
                return False

        # Yazdırılabilir karakter değilse yoksay
        if not text or not text.isprintable():
            return False

        # --- Buffer takibi (karakter asla tüketilmez) ---

        if now_elapsed > RFID_BUFFER_RESET_MS:
            # Uzun süre sessizlik – yeni dizi başlıyor
            self._buffer = ""
            self._timer.start()

        if self._buffer == "":
            # İlk karakter – buffer'a ekle, timer başlat
            self._buffer = text
            self._timer.start()
            self._set_reading(True)
        else:
            # Sonraki karakterler – zamanlama kontrolü
            elapsed = now_elapsed
            self._timer.start()

            if elapsed <= RFID_KEYSTROKE_TIMEOUT_MS:
                # Hızlı tuş vuruşu → kart okuyucu buffer'ına ekle
                self._buffer += text
                if len(self._buffer) > RFID_MAX_CARD_LENGTH:
                    self._reset_buffer()
            else:
                # Yavaş tuş vuruşu → insan yazımı, buffer sıfırla
                self._reset_buffer()
                # Yeni dizinin ilk karakteri olarak başlat
                self._buffer = text
                self._timer.start()

        return False  # Karakter asla tüketilmez

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _reset_buffer(self):
        """Buffer'ı sıfırla ve okuma durumunu kapat."""
        self._buffer = ""
        self._set_reading(False)

    def _set_reading(self, reading: bool):
        if self._is_reading != reading:
            self._is_reading = reading
            self.card_reading.emit(reading)
