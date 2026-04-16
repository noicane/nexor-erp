# -*- coding: utf-8 -*-
"""
NEXOR ERP - Marka Sistemi (Brand System)
=========================================

Tek otorite: tum renkler, tipografi, spacing, radius BURADA tanimlanir.
Baska yerde sabit px / hex yazmak yasak — `brand.SP_4`, `brand.FS_TITLE`,
`brand.PRIMARY` gibi kullan.

TEMA MODU (dark / light)
------------------------
Renk tokenlari iki paletten (DARK/LIGHT) gelir. `brand.set_mode('light')`
cagirildigi an tum `brand.BG_*`, `brand.TEXT*`, `brand.BORDER*` degerleri
degisir. Tipografi, spacing ve radius mod'dan bagimsizdir.

RESPONSIVE SCALE
----------------
Eski PC'lerde dusuk cozunurluk sorunu icin uygulama acilirken ekran genisligi
olculur ve scale_factor hesaplanir. SP_*, FS_*, R_*, ICON_* tokenlari bu
faktorle carpilir.

   1920+  ->  1.00  (referans)
   1600   ->  0.90
   1440   ->  0.85
   1366   ->  0.80
   1280   ->  0.75
   <1280  ->  0.70

KULLANIM
--------
    from core.nexor_brand import brand

    lbl.setStyleSheet(f"color: {brand.TEXT}; font-size: {brand.FS_TITLE}px;")
    layout.setSpacing(brand.SP_4)

BASLANGICTA INIT
----------------
main.py'da QApplication olusturulduktan HEMEN SONRA bir kere cagir:

    from core.nexor_brand import brand
    brand.init(app)
    brand.set_mode('dark')   # veya 'light'
"""
from __future__ import annotations
from pathlib import Path


# =============================================================================
# PALETLER
# =============================================================================

_DARK_PALETTE = {
    # Background (PRAXIS Lacivert-Siyah — themes.py ile eslesik)
    "BG_MAIN":       "#0F1419",
    "BG_SURFACE":    "#0B0E13",
    "BG_CARD":       "#151B23",
    "BG_ELEVATED":   "#111822",
    "BG_HOVER":      "#1C2430",
    "BG_INPUT":      "#232C3B",
    "BG_SELECTED":   "#1E1215",

    # Border
    "BORDER":        "#1E2736",
    "BORDER_HARD":   "#2A3545",
    "BORDER_FOCUS":  "#DC2626",

    # Text
    "TEXT":          "#E8ECF1",
    "TEXT_MUTED":    "#8896A6",
    "TEXT_DIM":      "#5C6878",
    "TEXT_DISABLED": "#3A4555",
    "TEXT_INVERSE":  "#0B0E13",

    # Brand (PRAXIS kurumsal kirmizi)
    "PRIMARY":       "#C41E1E",
    "PRIMARY_HOVER": "#9B1818",
    "PRIMARY_SOFT":  "rgba(196,30,30,0.12)",
    "PRIMARY_BORDER":"rgba(196,30,30,0.35)",

    # Semantic
    "SUCCESS":       "#10B981",
    "SUCCESS_SOFT":  "rgba(16,185,129,0.12)",
    "WARNING":       "#F59E0B",
    "WARNING_SOFT":  "rgba(245,158,11,0.12)",
    "ERROR":         "#EF4444",
    "ERROR_SOFT":    "rgba(239,68,68,0.12)",
    "INFO":          "#3B82F6",
    "INFO_SOFT":     "rgba(59,130,246,0.12)",
}

_LIGHT_PALETTE = {
    # Background
    "BG_MAIN":       "#F7F7F8",
    "BG_SURFACE":    "#FFFFFF",
    "BG_CARD":       "#FFFFFF",
    "BG_ELEVATED":   "#FFFFFF",
    "BG_HOVER":      "#F1F1F2",
    "BG_INPUT":      "#FFFFFF",
    "BG_SELECTED":   "#F9EAEA",

    # Border
    "BORDER":        "#E5E5E8",
    "BORDER_HARD":   "#D4D4D8",
    "BORDER_FOCUS":  "#DC2626",

    # Text
    "TEXT":          "#0A0A0B",
    "TEXT_MUTED":    "#52525B",
    "TEXT_DIM":      "#71717A",
    "TEXT_DISABLED": "#A1A1AA",
    "TEXT_INVERSE":  "#FAFAFA",

    # Brand
    "PRIMARY":       "#DC2626",
    "PRIMARY_HOVER": "#B91C1C",
    "PRIMARY_SOFT":  "rgba(220,38,38,0.10)",
    "PRIMARY_BORDER":"rgba(220,38,38,0.35)",

    # Semantic
    "SUCCESS":       "#059669",
    "SUCCESS_SOFT":  "rgba(5,150,105,0.10)",
    "WARNING":       "#D97706",
    "WARNING_SOFT":  "rgba(217,119,6,0.10)",
    "ERROR":         "#DC2626",
    "ERROR_SOFT":    "rgba(220,38,38,0.10)",
    "INFO":          "#2563EB",
    "INFO_SOFT":     "rgba(37,99,235,0.10)",
}


class _NexorBrand:
    """Nexor marka sistemi — singleton. Tema modu + responsive scale."""

    # ================================================================
    # TIPOGRAFI (mod'dan bagimsiz, scale uygulanir)
    # ================================================================

    FONT_FAMILY   = "'Inter', 'Segoe UI', -apple-system, system-ui, sans-serif"
    FONT_MONO     = "'JetBrains Mono', 'Consolas', 'Menlo', monospace"

    _FS_CAPTION    = 11
    _FS_BODY_SM    = 12
    _FS_BODY       = 13
    _FS_BODY_LG    = 15
    _FS_HEADING_SM = 16
    _FS_HEADING    = 18
    _FS_HEADING_LG = 20
    _FS_TITLE      = 24
    _FS_TITLE_LG   = 28
    _FS_DISPLAY    = 32
    _FS_DISPLAY_LG = 40

    FW_REGULAR  = 400
    FW_MEDIUM   = 500
    FW_SEMIBOLD = 600
    FW_BOLD     = 700

    # ================================================================
    # SPACING — 4 tabanli grid
    # ================================================================

    _SP_1  = 4
    _SP_2  = 8
    _SP_3  = 12
    _SP_4  = 16
    _SP_5  = 20
    _SP_6  = 24
    _SP_8  = 32
    _SP_10 = 40
    _SP_12 = 48
    _SP_16 = 64

    # ================================================================
    # RADIUS
    # ================================================================

    _R_SM = 6
    _R_MD = 10
    _R_LG = 14
    _R_XL = 20

    # ================================================================
    # ICON BOYUTLARI
    # ================================================================

    _ICON_XS = 14
    _ICON_SM = 16
    _ICON_MD = 20
    _ICON_LG = 24
    _ICON_XL = 32

    # ================================================================
    # STATE
    # ================================================================

    _scale_factor: float = 1.0
    _screen_width: int = 1920
    _screen_height: int = 1080
    _mode: str = "dark"
    _palette: dict = None
    _initialized: bool = False
    _listeners: list = None

    def __init__(self):
        self._palette = _DARK_PALETTE
        self._listeners = []

    # ================================================================
    # INIT
    # ================================================================

    def init(self, app=None) -> None:
        if self._initialized:
            return
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtGui import QFontDatabase, QFont

            app = app or QApplication.instance()
            if not app:
                self._initialized = True
                return

            screen = app.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self._screen_width = geo.width()
                self._screen_height = geo.height()

            self._scale_factor = self._compute_scale(self._screen_width)
            self._load_fonts()

            try:
                families = QFontDatabase.families()
                if "Inter" in families:
                    app.setFont(QFont("Inter", self.fs(10)))
                elif "Segoe UI" in families:
                    app.setFont(QFont("Segoe UI", self.fs(10)))
            except Exception:
                pass

            print(f"[NexorBrand] Ekran: {self._screen_width}x{self._screen_height}  "
                  f"scale={self._scale_factor:.2f}  mode={self._mode}")
        except Exception as e:
            print(f"[NexorBrand] init hatasi: {e}")
        finally:
            self._initialized = True

    @staticmethod
    def _compute_scale(width: int) -> float:
        if width >= 1920: return 1.00
        if width >= 1600: return 0.90
        if width >= 1440: return 0.85
        if width >= 1366: return 0.80
        if width >= 1280: return 0.75
        return 0.70

    def _load_fonts(self) -> None:
        try:
            from PySide6.QtGui import QFontDatabase
            base = Path(__file__).parent.parent / "assets" / "fonts"
            if not base.exists():
                return
            for ttf in base.glob("*.ttf"):
                QFontDatabase.addApplicationFont(str(ttf))
        except Exception:
            pass

    # ================================================================
    # TEMA MODU
    # ================================================================

    def set_mode(self, mode: str) -> bool:
        """Tema modunu degistir. Degisiklik varsa True doner ve listener'lari bilgilendirir."""
        mode = (mode or "dark").lower()
        if mode not in ("dark", "light"):
            mode = "dark"
        if mode == self._mode:
            return False
        self._mode = mode
        self._palette = _LIGHT_PALETTE if mode == "light" else _DARK_PALETTE
        # Listener'lari bilgilendir
        for cb in list(self._listeners):
            try:
                cb(mode)
            except Exception as e:
                print(f"[NexorBrand] Listener hatasi: {e}")
        return True

    @property
    def mode(self) -> str:
        return self._mode

    def on_mode_change(self, callback) -> None:
        """Tema modu degistiginde cagrilacak callback ekle."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def off_mode_change(self, callback) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    # ================================================================
    # SCALE HELPER'LARI
    # ================================================================

    def sp(self, px: int) -> int:
        return max(1, int(round(px * self._scale_factor)))

    def fs(self, px: int) -> int:
        return max(9, int(round(px * self._scale_factor)))

    def radius(self, px: int) -> int:
        return max(2, int(round(px * self._scale_factor)))

    def icon(self, px: int) -> int:
        return max(10, int(round(px * self._scale_factor)))

    # ================================================================
    # RENK PROPERTY'LERI (palette'den dinamik okunur)
    # ================================================================

    @property
    def BG_MAIN(self)       -> str: return self._palette["BG_MAIN"]
    @property
    def BG_SURFACE(self)    -> str: return self._palette["BG_SURFACE"]
    @property
    def BG_CARD(self)       -> str: return self._palette["BG_CARD"]
    @property
    def BG_ELEVATED(self)   -> str: return self._palette["BG_ELEVATED"]
    @property
    def BG_HOVER(self)      -> str: return self._palette["BG_HOVER"]
    @property
    def BG_INPUT(self)      -> str: return self._palette["BG_INPUT"]
    @property
    def BG_SELECTED(self)   -> str: return self._palette["BG_SELECTED"]

    @property
    def BORDER(self)        -> str: return self._palette["BORDER"]
    @property
    def BORDER_HARD(self)   -> str: return self._palette["BORDER_HARD"]
    @property
    def BORDER_FOCUS(self)  -> str: return self._palette["BORDER_FOCUS"]

    @property
    def TEXT(self)          -> str: return self._palette["TEXT"]
    @property
    def TEXT_MUTED(self)    -> str: return self._palette["TEXT_MUTED"]
    @property
    def TEXT_DIM(self)      -> str: return self._palette["TEXT_DIM"]
    @property
    def TEXT_DISABLED(self) -> str: return self._palette["TEXT_DISABLED"]
    @property
    def TEXT_INVERSE(self)  -> str: return self._palette["TEXT_INVERSE"]

    @property
    def PRIMARY(self)       -> str: return self._palette["PRIMARY"]
    @property
    def PRIMARY_HOVER(self) -> str: return self._palette["PRIMARY_HOVER"]
    @property
    def PRIMARY_SOFT(self)  -> str: return self._palette["PRIMARY_SOFT"]
    @property
    def PRIMARY_BORDER(self)-> str: return self._palette["PRIMARY_BORDER"]

    @property
    def SUCCESS(self)       -> str: return self._palette["SUCCESS"]
    @property
    def SUCCESS_SOFT(self)  -> str: return self._palette["SUCCESS_SOFT"]
    @property
    def WARNING(self)       -> str: return self._palette["WARNING"]
    @property
    def WARNING_SOFT(self)  -> str: return self._palette["WARNING_SOFT"]
    @property
    def ERROR(self)         -> str: return self._palette["ERROR"]
    @property
    def ERROR_SOFT(self)    -> str: return self._palette["ERROR_SOFT"]
    @property
    def INFO(self)          -> str: return self._palette["INFO"]
    @property
    def INFO_SOFT(self)     -> str: return self._palette["INFO_SOFT"]

    # ================================================================
    # PRE-SCALED TYPOGRAFI / SPACING / RADIUS / ICON
    # ================================================================

    # Spacing
    @property
    def SP_1(self)  -> int: return self.sp(self._SP_1)
    @property
    def SP_2(self)  -> int: return self.sp(self._SP_2)
    @property
    def SP_3(self)  -> int: return self.sp(self._SP_3)
    @property
    def SP_4(self)  -> int: return self.sp(self._SP_4)
    @property
    def SP_5(self)  -> int: return self.sp(self._SP_5)
    @property
    def SP_6(self)  -> int: return self.sp(self._SP_6)
    @property
    def SP_8(self)  -> int: return self.sp(self._SP_8)
    @property
    def SP_10(self) -> int: return self.sp(self._SP_10)
    @property
    def SP_12(self) -> int: return self.sp(self._SP_12)
    @property
    def SP_16(self) -> int: return self.sp(self._SP_16)

    # Font sizes
    @property
    def FS_CAPTION(self)    -> int: return self.fs(self._FS_CAPTION)
    @property
    def FS_BODY_SM(self)    -> int: return self.fs(self._FS_BODY_SM)
    @property
    def FS_BODY(self)       -> int: return self.fs(self._FS_BODY)
    @property
    def FS_BODY_LG(self)    -> int: return self.fs(self._FS_BODY_LG)
    @property
    def FS_HEADING_SM(self) -> int: return self.fs(self._FS_HEADING_SM)
    @property
    def FS_HEADING(self)    -> int: return self.fs(self._FS_HEADING)
    @property
    def FS_HEADING_LG(self) -> int: return self.fs(self._FS_HEADING_LG)
    @property
    def FS_TITLE(self)      -> int: return self.fs(self._FS_TITLE)
    @property
    def FS_TITLE_LG(self)   -> int: return self.fs(self._FS_TITLE_LG)
    @property
    def FS_DISPLAY(self)    -> int: return self.fs(self._FS_DISPLAY)
    @property
    def FS_DISPLAY_LG(self) -> int: return self.fs(self._FS_DISPLAY_LG)

    # Radius
    @property
    def R_SM(self) -> int: return self.radius(self._R_SM)
    @property
    def R_MD(self) -> int: return self.radius(self._R_MD)
    @property
    def R_LG(self) -> int: return self.radius(self._R_LG)
    @property
    def R_XL(self) -> int: return self.radius(self._R_XL)

    # Icon
    @property
    def ICON_XS(self) -> int: return self.icon(self._ICON_XS)
    @property
    def ICON_SM(self) -> int: return self.icon(self._ICON_SM)
    @property
    def ICON_MD(self) -> int: return self.icon(self._ICON_MD)
    @property
    def ICON_LG(self) -> int: return self.icon(self._ICON_LG)
    @property
    def ICON_XL(self) -> int: return self.icon(self._ICON_XL)

    # Scale info
    @property
    def scale_factor(self) -> float: return self._scale_factor
    @property
    def screen_width(self) -> int: return self._screen_width
    @property
    def screen_height(self) -> int: return self._screen_height


brand = _NexorBrand()
