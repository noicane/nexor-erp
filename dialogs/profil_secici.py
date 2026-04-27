# -*- coding: utf-8 -*-
"""
NEXOR ERP - Profil Secici Dialog (Gelistirici Modu)

Acilista config'te 2+ profil varsa ve gelistirici_modu=True ise gosterilir.
Kullanici aktif profili degistirebilir; secim sonrasi NEXOR yeniden baslatilmali
(DB connection ayri profile gore kurulur).

Production (gelistirici_modu=False) musteride bu dialog gosterilmez - sabit
profile baglanir.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout,
)

from core.external_config import config_manager
from core.nexor_brand import brand


class ProfilSeciciDialog(QDialog):
    """Aktif profili degistir."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profil Sec")
        self.setModal(True)
        self.setMinimumWidth(420)
        self._secilen: str | None = None
        self._build_ui()
        self._fill()

    def _build_ui(self) -> None:
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QComboBox {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                padding: 8px; min-height: 28px;
            }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_CARD}; color: {brand.TEXT};
                selection-background-color: {brand.PRIMARY};
            }}
            QPushButton {{
                background: {brand.BG_CARD}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                padding: 8px 16px; min-width: 100px;
            }}
            QPushButton#primary {{
                background: {brand.PRIMARY}; color: white; border: none;
            }}
            QPushButton#primary:hover {{ background: {brand.PRIMARY_HOVER}; }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        baslik = QLabel("<b>Profil Secimi</b>")
        baslik.setStyleSheet(f"font-size: 14px; color: {brand.TEXT};")
        lay.addWidget(baslik)

        aciklama = QLabel(
            "Hangi musteri profiline baglanmak istiyorsun?\n"
            "Secim sonrasi NEXOR yeniden baslatilacak."
        )
        aciklama.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: 11px;")
        lay.addWidget(aciklama)

        form = QFormLayout()
        form.setSpacing(10)
        self.combo = QComboBox()
        form.addRow(QLabel("Profil:"), self.combo)
        lay.addLayout(form)

        self.bilgi = QLabel("")
        self.bilgi.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 10px;")
        self.bilgi.setWordWrap(True)
        lay.addWidget(self.bilgi)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_iptal = QPushButton("Iptal")
        self.btn_iptal.clicked.connect(self.reject)
        self.btn_tamam = QPushButton("Sec ve Baglan")
        self.btn_tamam.setObjectName("primary")
        self.btn_tamam.clicked.connect(self._kabul)
        btn_row.addWidget(self.btn_iptal)
        btn_row.addWidget(self.btn_tamam)
        lay.addLayout(btn_row)

        self.combo.currentIndexChanged.connect(self._secim_degisti)

    def _fill(self) -> None:
        profiller = config_manager.list_profiles()
        aktif = config_manager.get_active_profile()
        self.combo.clear()
        for ad in profiller:
            self.combo.addItem(ad)
        if aktif in profiller:
            self.combo.setCurrentText(aktif)
        self._secim_degisti(self.combo.currentIndex())

    def _secim_degisti(self, idx: int) -> None:
        ad = self.combo.currentText()
        profil = config_manager.get_profile(ad) or {}
        db = (profil.get('database') or {})
        musteri_adi = profil.get('musteri_adi') or '(isim yok)'
        server = db.get('server') or '?'
        veritabani = db.get('database') or '?'
        self.bilgi.setText(
            f"<b>{musteri_adi}</b><br>"
            f"DB: {server} / {veritabani}"
        )

    def _kabul(self) -> None:
        ad = self.combo.currentText().strip()
        if not ad:
            return
        self._secilen = ad
        self.accept()

    @property
    def secilen_profil(self) -> str | None:
        return self._secilen


def profil_sec_eger_gerekirse() -> str | None:
    """Acilista cagrilir. gelistirici_modu False veya tek profil varsa atlar.

    Returns:
        Yeni secilen profil adi (degistirildi) veya None (degisiklik yok).
    """
    try:
        from core.modul_servisi import ModulServisi
        if not ModulServisi.instance().gelistirici_modu:
            return None
    except Exception:
        # ModulServisi yuklenmediyse config'den direkt oku
        if not config_manager.get('gelistirici_modu', False):
            return None

    profiller = config_manager.list_profiles()
    if len(profiller) < 2:
        return None

    dlg = ProfilSeciciDialog()
    if dlg.exec() != QDialog.Accepted:
        return None

    yeni = dlg.secilen_profil
    if not yeni or yeni == config_manager.get_active_profile():
        return None

    if config_manager.set_active_profile(yeni):
        return yeni
    return None
