# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Bildirim Tercihleri Sayfasi
Kullanicilarin modul bazli bildirim tercihlerini yonetir
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QCheckBox, QComboBox, QMessageBox, QScrollArea, QWidget,
    QGridLayout
)
from PySide6.QtCore import Qt, QTimer

from components.base_page import BasePage
from core.nexor_brand import brand


MODULLER = [
    ('IS_EMIRLERI', '📋', 'Is Emirleri'),
    ('KALITE', '✅', 'Kalite'),
    ('URETIM', '🏭', 'Uretim'),
    ('BAKIM', '🔧', 'Bakim'),
    ('STOK', '📦', 'Stok / Depo'),
    ('SEVKIYAT', '🚚', 'Sevkiyat'),
    ('ISG', '🦺', 'Is Guvenligi'),
    ('SATINALMA', '🛒', 'Satinalma'),
    ('LAB', '🔬', 'Laboratuvar'),
    ('CEVRE', '🌿', 'Cevre Yonetimi'),
    ('IK', '👥', 'Insan Kaynaklari'),
    ('SISTEM', '⚙️', 'Sistem'),
]

ONEM_SEVIYELERI = ['DUSUK', 'NORMAL', 'YUKSEK', 'KRITIK']


def get_style(theme: dict) -> dict:
    return {
        'card_bg': theme.get('bg_card', '#1E1E1E'),
        'input_bg': theme.get('bg_input', '#1A1A1A'),
        'border': theme.get('border', '#2A2A2A'),
        'text': theme.get('text', '#FFFFFF'),
        'text_secondary': theme.get('text_secondary', '#AAAAAA'),
        'text_muted': theme.get('text_muted', '#666666'),
        'primary': theme.get('primary', '#DC2626'),
        'primary_hover': theme.get('primary_hover', '#B91C1C'),
        'success': theme.get('success', '#10B981'),
    }


class ModulTercihKart(QFrame):
    """Tek modul icin bildirim tercih karti"""

    def __init__(self, modul_kod: str, modul_icon: str, modul_ad: str,
                 theme: dict, tercih: dict = None, parent=None):
        super().__init__(parent)
        self.modul_kod = modul_kod
        self.s = get_style(theme)
        self._tercih = tercih or {}
        self._setup_ui(modul_icon, modul_ad)

    def _setup_ui(self, icon: str, ad: str):
        s = self.s
        self.setStyleSheet(f"""
            ModulTercihKart {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 10px;
            }}
        """)
        self.setMinimumHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Modul icon + ad
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        lbl_baslik = QLabel(f"{icon} {ad}")
        lbl_baslik.setStyleSheet(f"color: {s['text']}; font-size: 14px; font-weight: bold;")
        info_layout.addWidget(lbl_baslik)

        lbl_kod = QLabel(self.modul_kod)
        lbl_kod.setStyleSheet(f"color: {s['text_muted']}; font-size: 11px;")
        info_layout.addWidget(lbl_kod)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Checkboxlar
        cb_style = f"""
            QCheckBox {{
                color: {s['text']}; font-size: 12px; spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 2px solid {s['border']};
                border-radius: 4px; background: {s['input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background: {s['primary']}; border-color: {s['primary']};
            }}
        """

        self.chk_uygulama = QCheckBox("Uygulama")
        self.chk_uygulama.setStyleSheet(cb_style)
        self.chk_uygulama.setChecked(self._tercih.get('uygulama_ici', True))
        layout.addWidget(self.chk_uygulama)

        self.chk_email = QCheckBox("E-posta")
        self.chk_email.setStyleSheet(cb_style)
        self.chk_email.setChecked(self._tercih.get('email', False))
        layout.addWidget(self.chk_email)

        self.chk_whatsapp = QCheckBox("WhatsApp")
        self.chk_whatsapp.setStyleSheet(cb_style)
        self.chk_whatsapp.setChecked(self._tercih.get('whatsapp', False))
        layout.addWidget(self.chk_whatsapp)

        # Minimum onem
        self.cmb_onem = QComboBox()
        for onem in ONEM_SEVIYELERI:
            self.cmb_onem.addItem(onem, onem)
        current_onem = self._tercih.get('minimum_onem', 'DUSUK')
        idx = ONEM_SEVIYELERI.index(current_onem) if current_onem in ONEM_SEVIYELERI else 0
        self.cmb_onem.setCurrentIndex(idx)
        self.cmb_onem.setStyleSheet(f"""
            QComboBox {{
                background: {s['input_bg']}; border: 1px solid {s['border']};
                border-radius: 6px; padding: 6px 10px;
                color: {s['text']}; min-width: 90px; font-size: 12px;
            }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']}; border: 1px solid {s['border']};
                color: {s['text']}; selection-background-color: {s['primary']};
            }}
        """)
        self.cmb_onem.setToolTip("Minimum onem seviyesi")
        layout.addWidget(self.cmb_onem)

    def get_tercih(self) -> dict:
        return {
            'modul': self.modul_kod,
            'uygulama_ici': self.chk_uygulama.isChecked(),
            'email': self.chk_email.isChecked(),
            'whatsapp': self.chk_whatsapp.isChecked(),
            'minimum_onem': self.cmb_onem.currentData(),
        }


class BildirimTercihleriPage(BasePage):
    """Bildirim Tercihleri Sayfasi"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_style(theme)
        self._modul_kartlari = []
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _get_user_id(self):
        try:
            from core.yetki_manager import YetkiManager
            return YetkiManager._current_user_id
        except Exception:
            return None

    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)

        title_row = QHBoxLayout()
        icon = QLabel("🔔")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Bildirim Tercihleri")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        header.addLayout(title_row)

        subtitle = QLabel("Varsayilan: KRITIK/YUKSEK bildirimler WhatsApp + E-posta, NORMAL bildirimler E-posta ile gonderilir. Kisisel tercihlerinizi asagidan belirleyebilirsiniz.")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Tablo basliklari
        header_row = QHBoxLayout()
        header_row.setContentsMargins(16, 0, 16, 0)
        header_row.setSpacing(16)

        lbl_modul_h = QLabel("Modul")
        lbl_modul_h.setStyleSheet(f"color: {s['text_muted']}; font-size: 12px; font-weight: bold;")
        header_row.addWidget(lbl_modul_h)
        header_row.addStretch()

        for header_text in ["Uygulama", "E-posta", "WhatsApp", "Min. Onem"]:
            lbl = QLabel(header_text)
            lbl.setStyleSheet(f"color: {s['text_muted']}; font-size: 11px; font-weight: bold;")
            lbl.setFixedWidth(90 if header_text == "Min. Onem" else 75)
            lbl.setAlignment(Qt.AlignCenter)
            header_row.addWidget(lbl)

        layout.addLayout(header_row)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {s['card_bg']}; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {s['border']}; border-radius: 4px;
            }}
        """)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll, 1)

        # Alt butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_sifirla = QPushButton("Varsayilana Don")
        btn_sifirla.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']}; color: {s['text']};
                border: 1px solid {s['border']}; border-radius: 8px;
                padding: 12px 24px; font-size: 13px;
            }}
            QPushButton:hover {{ background: {s['border']}; }}
        """)
        btn_sifirla.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(btn_sifirla)

        btn_kaydet = QPushButton("Tercihleri Kaydet")
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']}; color: white;
                border: none; border-radius: 8px;
                padding: 12px 28px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)

    def _load_data(self):
        """Mevcut tercihleri yukle ve kartlari olustur."""
        user_id = self._get_user_id()
        mevcut_tercihler = {}

        if user_id:
            try:
                from core.bildirim_service import BildirimService
                tercihler = BildirimService.tercih_getir(user_id)
                for t in tercihler:
                    mevcut_tercihler[t['modul']] = t
            except Exception as e:
                print(f"[BildirimTercihleri] Tercih yukle hata: {e}")

        # Kartlari olustur
        self._modul_kartlari = []
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for kod, icon, ad in MODULLER:
            tercih = mevcut_tercihler.get(kod, {})
            kart = ModulTercihKart(kod, icon, ad, self.theme, tercih)
            self._modul_kartlari.append(kart)
            self.cards_layout.addWidget(kart)

    def _save(self):
        """Tum tercihleri kaydet."""
        user_id = self._get_user_id()
        if not user_id:
            QMessageBox.warning(self, "Uyari", "Kullanici bilgisi alinamadi.")
            return

        try:
            from core.bildirim_service import BildirimService
            basarili = 0
            for kart in self._modul_kartlari:
                tercih = kart.get_tercih()
                result = BildirimService.tercih_kaydet(
                    kullanici_id=user_id,
                    modul=tercih['modul'],
                    uygulama_ici=tercih['uygulama_ici'],
                    email=tercih['email'],
                    whatsapp=tercih['whatsapp'],
                    minimum_onem=tercih['minimum_onem'],
                )
                if result:
                    basarili += 1

            QMessageBox.information(
                self, "Basarili",
                f"{basarili}/{len(self._modul_kartlari)} modul tercihi kaydedildi."
            )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit hatasi: {str(e)}")

    def _reset_defaults(self):
        """Tum tercihleri varsayilana dondur."""
        reply = QMessageBox.question(
            self, "Sifirlama",
            "Tum bildirim tercihlerini varsayilana dondurmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for kart in self._modul_kartlari:
                kart.chk_uygulama.setChecked(True)
                kart.chk_email.setChecked(True)    # Email varsayilan acik
                kart.chk_whatsapp.setChecked(False)  # WhatsApp varsayilan kapali
                kart.cmb_onem.setCurrentIndex(0)  # DUSUK
