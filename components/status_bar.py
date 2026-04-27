# -*- coding: utf-8 -*-
"""
NEXOR ERP - Ana Pencere Status Bar
Alt seritte: NEXOR brand + sürüm | bağlı DB | aktif müşteri profili | PLC durumu
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from core.nexor_brand import brand


class NexorStatusBar(QFrame):
    """Ana pencerenin en altinda gozuken bilgi seridi."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setObjectName("nexor_status_bar")
        self._build_ui()
        # 30 saniyede bir tazele (PLC durumu degisirse)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tazele)
        self._timer.start(30000)

    def _build_ui(self):
        self.setStyleSheet(f"""
            QFrame#nexor_status_bar {{
                background: {brand.BG_SURFACE};
                border-top: 1px solid {brand.BORDER};
            }}
            QLabel {{
                color: {brand.TEXT_DIM};
                font-size: 11px;
                background: transparent;
            }}
            QLabel#nx_brand {{ color: {brand.TEXT}; font-weight: bold; }}
            QLabel#nx_alive {{ color: #16A34A; font-weight: bold; }}
            QLabel#nx_off   {{ color: {brand.TEXT_DISABLED}; }}
            QLabel#nx_sep   {{ color: {brand.TEXT_DISABLED}; padding: 0 4px; }}
            QLabel#nx_db    {{ color: {brand.TEXT}; }}
        """)

        h = QHBoxLayout(self)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(6)

        # SOL: NEXOR + sürüm
        try:
            from version import VERSION
            ver = f"v{VERSION}"
        except Exception:
            ver = ""
        self.lbl_brand = QLabel(f"NEXOR ERP {ver}".strip())
        self.lbl_brand.setObjectName("nx_brand")
        h.addWidget(self.lbl_brand)
        h.addWidget(self._sep())

        # ORTA: Canli + DB
        self.lbl_dot_db = QLabel("●")
        self.lbl_dot_db.setObjectName("nx_alive")
        h.addWidget(self.lbl_dot_db)
        self.lbl_db = QLabel("...")
        self.lbl_db.setObjectName("nx_db")
        h.addWidget(self.lbl_db)
        h.addWidget(self._sep())

        # ORTA-2: Aktif musteri profili
        self.lbl_musteri = QLabel("Musteri: ...")
        h.addWidget(self.lbl_musteri)

        h.addStretch()

        # SAG: PLC durumu
        self.lbl_plc_dot = QLabel("●")
        self.lbl_plc_text = QLabel("PLC")
        h.addWidget(self.lbl_plc_dot)
        h.addWidget(self.lbl_plc_text)

        self._tazele()

    def _sep(self) -> QLabel:
        s = QLabel("·")
        s.setObjectName("nx_sep")
        return s

    def _tazele(self):
        """DB / profil / PLC bilgilerini config_manager'dan oku ve göster."""
        try:
            from core.external_config import config_manager
            db = config_manager.get_db_config() or {}
            server = db.get('server') or '?'
            veritabani = db.get('database') or '?'
            self.lbl_db.setText(f"{server} · {veritabani}")

            profil = config_manager.get_active_profile()
            p = config_manager.get_profile(profil) or {}
            # Kisa ad oncelikli; yoksa unvan (32 karakterden uzunsa kisalt); yoksa profil kodu
            kisa = (p.get('kisa_ad') or '').strip()
            unvan = (p.get('musteri_adi') or '').strip()
            if kisa:
                gosterim = kisa
            elif unvan:
                gosterim = unvan if len(unvan) <= 32 else unvan[:30].rstrip() + '...'
            else:
                gosterim = profil
            self.lbl_musteri.setText(f"Musteri: {gosterim}")
            self.lbl_musteri.setToolTip(f"Profil: {profil}\nUnvan: {unvan or '-'}")

            plc_cfg = config_manager.get_plc_config()
            if plc_cfg:
                # PLC config var; sync servisi calisiyor mu?
                aktif = self._plc_sync_aktif()
                if aktif:
                    self.lbl_plc_dot.setStyleSheet(f"color: #16A34A; font-weight: bold;")
                    self.lbl_plc_text.setText("PLC SENKRON")
                else:
                    self.lbl_plc_dot.setStyleSheet(f"color: {brand.TEXT_DISABLED};")
                    self.lbl_plc_text.setText("PLC BEKLEMEDE")
            else:
                self.lbl_plc_dot.setStyleSheet(f"color: {brand.TEXT_DISABLED};")
                self.lbl_plc_text.setText("PLC KAPALI")
        except Exception:
            # Sessiz: status bar uygulamayi cokertmemeli
            pass

    def _plc_sync_aktif(self) -> bool:
        """PLC sync servisi calisiyor mu?"""
        try:
            from core.plc_sync_service import PLCSyncService
            inst = PLCSyncService.instance() if hasattr(PLCSyncService, 'instance') else None
            return bool(inst and inst.isRunning()) if inst else False
        except Exception:
            return False
