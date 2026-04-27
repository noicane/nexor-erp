# -*- coding: utf-8 -*-
"""
NEXOR ERP - Bayi Paneli
master/008384 ile girilen ayri yonetim ekrani.

NEXOR ana arayuzu acilmaz; sadece Musteri Yonetimi gosterilir. Yetki sistemi
ve modul lisans karmasasiyla baglantili degildir; bayi profilleri yonetir.

Cikis: uygulama tamamen kapanir (login ekrani tekrar gosterilmez).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from core.nexor_brand import brand


class BayiPaneli(QMainWindow):
    """Bayi/yonetim paneli ana penceresi."""

    def __init__(self, theme: dict | None = None):
        super().__init__()
        self.theme = theme or {}
        self.setWindowTitle("NEXOR Bayi Paneli")
        self.setMinimumSize(1200, 740)

        # Window icon
        try:
            from dialogs.login import get_icon_path
            ip = get_icon_path()
            if ip:
                self.setWindowIcon(QIcon(ip))
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"QMainWindow {{ background: {brand.BG_MAIN}; }}")

        central = QWidget()
        self.setCentralWidget(central)

        ana = QVBoxLayout(central)
        ana.setContentsMargins(0, 0, 0, 0)
        ana.setSpacing(0)

        # ---------- UST BANNER ----------
        banner = QWidget()
        banner.setFixedHeight(56)
        banner.setStyleSheet(f"""
            background: {brand.PRIMARY};
        """)
        bh = QHBoxLayout(banner)
        bh.setContentsMargins(20, 0, 20, 0)
        bh.setSpacing(12)

        baslik = QLabel("BAYİ PANELİ")
        baslik.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        bh.addWidget(baslik)

        alt_baslik = QLabel("·  NEXOR Yönetim Konsolu")
        alt_baslik.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 13px;")
        bh.addWidget(alt_baslik)

        bh.addStretch()

        # Aktif profil bilgisi
        try:
            from core.external_config import config_manager
            profil = config_manager.get_active_profile()
            p = config_manager.get_profile(profil) or {}
            kisa = (p.get('kisa_ad') or p.get('musteri_adi') or profil)
            if len(kisa) > 28:
                kisa = kisa[:26] + "..."
            bilgi = QLabel(f"Aktif: {kisa}")
            bilgi.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 12px;")
            bh.addWidget(bilgi)
        except Exception:
            pass

        btn_cikis = QPushButton("Çıkış")
        btn_cikis.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.15); color: white; border: none;
                border-radius: 6px; padding: 8px 18px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(255,255,255,0.25); }
        """)
        btn_cikis.clicked.connect(self._cikis)
        bh.addWidget(btn_cikis)

        ana.addWidget(banner)

        # ---------- ICERIK: MUSTERI YONETIMI SAYFASI ----------
        try:
            from modules.sistem.sistem_musteri_yonetimi import SistemMusteriYonetimiPage
            self.page = SistemMusteriYonetimiPage(self.theme)
            ana.addWidget(self.page, 1)
        except Exception as e:
            err = QLabel(f"Müşteri Yönetimi yüklenemedi:\n{e}")
            err.setAlignment(Qt.AlignCenter)
            err.setStyleSheet(f"color: {brand.TEXT}; font-size: 14px; padding: 40px;")
            ana.addWidget(err, 1)

        # ---------- ALT BILGI ----------
        try:
            from components.status_bar import NexorStatusBar
            self.sb = NexorStatusBar(self)
            ana.addWidget(self.sb)
        except Exception:
            pass

    def _cikis(self):
        if QMessageBox.question(
            self, "Çıkış",
            "Bayi panelini kapatmak istiyor musunuz?\nNEXOR uygulaması tamamen kapanacak."
        ) != QMessageBox.Yes:
            return
        self.close()

    def closeEvent(self, event):
        # Pencere kapaninca uygulamayi kapat
        try:
            QApplication.instance().quit()
        except Exception:
            pass
        super().closeEvent(event)
