# -*- coding: utf-8 -*-
"""
NEXOR ERP - Modern Tema Sistemi v2.0
Tema 1 (Modern Dark) + Tema 3 (Clean Light)

Ozellikler:
- Tum renkler HEX formatinda (rgba yok - uyumluluk icin)
- Minimal ve profesyonel tasarim
- Her PC'de ayni gorunum
"""

import json
import os
from pathlib import Path
from typing import Optional, Callable

# =============================================================================
# KURUMSAL RENK PALETI
# =============================================================================

BRAND_COLORS = {
    # Ana Marka Renkleri (PRAXIS kurumsal stil)
    "primary": "#C41E1E",        # Kurumsal Kırmızı
    "primary_dark": "#9B1818",   # Koyu Kırmızı
    "primary_light": "#E53535",  # Açık Kırmızı

    # Notr Renkler
    "white": "#FFFFFF",
    "black": "#000000",

    # Lacivert-Siyah Skalası (Dark Mode - PRAXIS stil)
    "gray_950": "#0B0E13",
    "gray_900": "#0F1419",
    "gray_850": "#111822",
    "gray_800": "#151B23",
    "gray_700": "#1C2430",
    "gray_600": "#232C3B",
    "gray_500": "#5C6878",
    "gray_400": "#8896A6",
    "gray_300": "#E8ECF1",
    
    # Gri Skalasi (Light Mode)
    "slate_50": "#F8FAFC",
    "slate_100": "#F1F5F9",
    "slate_200": "#E2E8F0",
    "slate_300": "#CBD5E1",
    "slate_400": "#94A3B8",
    "slate_500": "#64748B",
    "slate_600": "#475569",
    "slate_700": "#334155",
    "slate_800": "#1E293B",
    "slate_900": "#0F172A",
    
    # Durum Renkleri
    "success": "#10B981",
    "success_dark": "#059669",
    "success_bg_dark": "#052E1C",
    "success_bg_light": "#DCFCE7",
    
    "warning": "#F59E0B",
    "warning_dark": "#D97706",
    "warning_bg_dark": "#2E2006",
    "warning_bg_light": "#FEF3C7",
    
    "error": "#EF4444",
    "error_dark": "#DC2626",
    "error_bg_dark": "#2E0A0A",
    "error_bg_light": "#FEE2E2",
    
    "info": "#3B82F6",
    "info_dark": "#2563EB",
    "info_bg_dark": "#0A1A2E",
    "info_bg_light": "#DBEAFE",
}

# =============================================================================
# RENK PALETLERI (Accent Color Secenekleri)
# =============================================================================

COLOR_PRESETS = {
    "nexor": {
        "name": "Nexor Red",
        "primary": "#C41E1E",
        "primary_hover": "#9B1818",
        "start": "#C41E1E",
        "end": "#9B1818",
        "icon": "🔴"
    },
    "redline": {
        "name": "Redline Red",
        "primary": "#C41E1E",
        "primary_hover": "#9B1818",
        "start": "#C41E1E",
        "end": "#9B1818",
        "icon": "🔴"
    },
    "blue": {
        "name": "Ocean Blue",
        "primary": "#2563EB",
        "primary_hover": "#1D4ED8",
        "start": "#2563EB",
        "end": "#1D4ED8",
        "icon": "🔵"
    },
    "emerald": {
        "name": "Emerald",
        "primary": "#059669",
        "primary_hover": "#047857",
        "start": "#059669",
        "end": "#047857",
        "icon": "🟢"
    },
    "purple": {
        "name": "Purple",
        "primary": "#7C3AED",
        "primary_hover": "#6D28D9",
        "start": "#7C3AED",
        "end": "#6D28D9",
        "icon": "🟣"
    },
    "orange": {
        "name": "Orange",
        "primary": "#EA580C",
        "primary_hover": "#C2410C",
        "start": "#EA580C",
        "end": "#C2410C",
        "icon": "🟠"
    },
}

# =============================================================================
# DARK THEME (Tema 1 - Modern Dark)
# =============================================================================

DARK_THEME = {
    "mode": "dark",
    "mode_name": "Modern Dark",

    # === Arka Planlar (PRAXIS Lacivert-Siyah) ===
    "bg_main": "#0F1419",           # Ana arka plan
    "bg_sidebar": "#0B0E13",        # Sidebar arka plani
    "bg_card": "#151B23",           # Kart arka plani
    "bg_card_solid": "#151B23",     # Solid kart (eski uyumluluk)
    "bg_card_hover": "#1C2430",     # Kart hover
    "bg_input": "#232C3B",          # Input arka plani
    "bg_input_focus": "#2A3545",    # Input focus
    "bg_hover": "#1C2430",          # Genel hover
    "bg_selected": "#1E1215",       # Secili item (kirmizi ton)
    "bg_tooltip": "#151B23",        # Tooltip
    "bg_modal": "#111822",          # Modal arka plan
    "bg_dropdown": "#151B23",       # Dropdown menu

    # === Kenarliklar ===
    "border": "#1E2736",            # Normal kenarlik
    "border_light": "#2A3545",      # Acik kenarlik
    "border_focus": "#C41E1E",      # Focus kenarlik (primary)
    "border_input": "#1E2736",      # Input kenarlik

    # === Metinler ===
    "text": "#E8ECF1",              # Ana metin
    "text_secondary": "#8896A6",    # Ikincil metin
    "text_muted": "#5C6878",        # Soluk metin
    "text_disabled": "#3A4555",     # Devre disi metin
    "text_inverse": "#0B0E13",      # Ters metin (butonlar icin)
    "text_link": "#3B82F6",         # Link rengi

    # === Durum Renkleri ===
    "success": "#10B981",
    "success_bg": "#0D2B1F",
    "success_text": "#10B981",
    "warning": "#F59E0B",
    "warning_bg": "#2B2210",
    "warning_text": "#F59E0B",
    "error": "#EF4444",
    "error_bg": "#2B1111",
    "error_text": "#EF4444",
    "info": "#3B82F6",
    "info_bg": "#111D2E",
    "info_text": "#3B82F6",

    # === Tablo ===
    "table_header_bg": "#111822",
    "table_header_text": "#9EACBC",
    "table_row_bg": "#151B23",
    "table_row_alt": "#0D1219",
    "table_row_hover": "#161E2B",
    "table_row_selected": "#1E1215",
    "table_border": "#1E2736",

    # === Scrollbar ===
    "scrollbar_bg": "#0F1419",
    "scrollbar_thumb": "#1E2736",
    "scrollbar_thumb_hover": "#2A3545",

    # === Golge ===
    "shadow_color": "#000000",

    # === Ozel ===
    "sidebar_item_active_bg": "#C41E1E",
    "sidebar_item_active_text": "#FFFFFF",
    "sidebar_item_hover_bg": "#141A22",
    "badge_bg": "#1E2736",
}

# =============================================================================
# LIGHT THEME (Tema 3 - Clean Light)
# =============================================================================

LIGHT_THEME = {
    "mode": "light",
    "mode_name": "Clean Light",
    
    # === Arka Planlar ===
    "bg_main": "#F8FAFC",           # Ana arka plan
    "bg_sidebar": "#FFFFFF",        # Sidebar arka plani
    "bg_card": "#FFFFFF",           # Kart arka plani
    "bg_card_solid": "#FFFFFF",     # Solid kart (eski uyumluluk)
    "bg_card_hover": "#F1F5F9",     # Kart hover (web ile tutarli)
    "bg_input": "#F8FAFC",          # Input arka plani (hafif tint)
    "bg_input_focus": "#FFFFFF",    # Input focus (tam beyaz)
    "bg_hover": "#F1F5F9",          # Genel hover
    "bg_selected": "#FEF2F2",       # Secili item (kirimizi tint)
    "bg_tooltip": "#1E293B",        # Tooltip (koyu)
    "bg_modal": "#FFFFFF",          # Modal arka plan
    "bg_dropdown": "#FFFFFF",       # Dropdown menu
    
    # === Kenarliklar ===
    "border": "#E2E8F0",            # Normal kenarlik
    "border_light": "#CBD5E1",      # Acik kenarlik (hover border gorunsun)
    "border_focus": "#DC2626",      # Focus kenarlik (primary)
    "border_input": "#E2E8F0",      # Input kenarlik
    
    # === Metinler ===
    "text": "#1E293B",              # Ana metin
    "text_secondary": "#475569",    # Ikincil metin
    "text_muted": "#94A3B8",        # Soluk metin
    "text_disabled": "#CBD5E1",     # Devre disi metin
    "text_inverse": "#FFFFFF",      # Ters metin (butonlar icin)
    "text_link": "#2563EB",         # Link rengi
    
    # === Durum Renkleri ===
    "success": "#059669",
    "success_bg": "#DCFCE7",
    "success_text": "#166534",
    "warning": "#D97706",
    "warning_bg": "#FEF3C7",
    "warning_text": "#92400E",
    "error": "#DC2626",
    "error_bg": "#FEE2E2",
    "error_text": "#991B1B",
    "info": "#2563EB",
    "info_bg": "#DBEAFE",
    "info_text": "#1E40AF",
    
    # === Tablo ===
    "table_header_bg": "#F8FAFC",
    "table_header_text": "#64748B",
    "table_row_bg": "#FFFFFF",
    "table_row_alt": "#F8FAFC",
    "table_row_hover": "#F1F5F9",
    "table_row_selected": "#FEF2F2",
    "table_border": "#E2E8F0",
    
    # === Scrollbar ===
    "scrollbar_bg": "#F1F5F9",
    "scrollbar_thumb": "#CBD5E1",
    "scrollbar_thumb_hover": "#94A3B8",
    
    # === Golge ===
    "shadow_color": "#000000",
    
    # === Ozel ===
    "sidebar_item_active_bg": "#DC2626",      # Kirmizi arka plan
    "sidebar_item_active_text": "#FFFFFF",    # Beyaz yazi
    "sidebar_item_hover_bg": "#F1F5F9",
    "badge_bg": "#F1F5F9",
}


# =============================================================================
# TEMA OLUSTURUCU
# =============================================================================

_theme_cache: dict = {}

def build_theme(mode: str = "dark", color: str = "redline") -> dict:
    """
    Tema sozlugu olustur (onbellekli - max 12 kombinasyon)

    Args:
        mode: "dark" veya "light"
        color: Renk paleti adi ("redline", "blue", "emerald", "purple", "orange")

    Returns:
        Tema dictionary
    """
    cache_key = f"{mode}_{color}"
    if cache_key in _theme_cache:
        return _theme_cache[cache_key].copy()

    # Temel tema
    base = DARK_THEME.copy() if mode == "dark" else LIGHT_THEME.copy()
    
    # Renk paleti
    preset = COLOR_PRESETS.get(color, COLOR_PRESETS["redline"])
    
    # Primary renkleri ekle
    base["primary"] = preset["primary"]
    base["primary_hover"] = preset["primary_hover"]
    base["color_preset"] = color
    base["color_name"] = preset["name"]
    
    # Eski uyumluluk icin gradient anahtarlari
    base["gradient_start"] = preset["primary"]
    base["gradient_end"] = preset["primary_hover"]
    base["start"] = preset["primary"]  # Eski kod icin
    base["end"] = preset["primary_hover"]  # Eski kod icin
    
    # Focus border'i primary ile esitle
    base["border_focus"] = preset["primary"]
    
    # Sidebar active bg'yi primary ile esitle (web ile tutarli - her iki modda da)
    base["sidebar_item_active_bg"] = preset["primary"]
    
    # Gradient (Qt icin)
    base["gradient_css"] = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {preset['primary']}, stop:1 {preset['primary_hover']})"
    
    # Brand bilgileri
    base["brand_name"] = "NEXOR ERP"
    base["brand_company"] = "Redline Creative Solutions"

    # Onbellege kaydet (max 12)
    if len(_theme_cache) >= 12:
        _theme_cache.pop(next(iter(_theme_cache)))
    _theme_cache[cache_key] = base.copy()

    return base


# =============================================================================
# TEMA YONETICISI (Singleton)
# =============================================================================

class ThemeManager:
    """
    Tema Yoneticisi - Singleton
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._mode = "dark"
        self._color = "redline"
        self._callbacks = []
        self._settings_file = self._get_settings_path()
        
        self._load_settings()
    
    def _get_settings_path(self) -> Path:
        """Ayar dosyasi yolu"""
        if os.name == 'nt':
            base = Path(os.environ.get('APPDATA', '.'))
        else:
            base = Path.home() / '.config'
        
        config_dir = base / 'NexorERP'
        config_dir.mkdir(parents=True, exist_ok=True)
        
        return config_dir / 'theme.json'
    
    def _load_settings(self):
        """Kayitli ayarlari yukle"""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._mode = data.get('mode', 'dark')
                    self._color = data.get('color', 'redline')
        except Exception:
            pass
    
    def _save_settings(self):
        """Ayarlari kaydet"""
        try:
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'mode': self._mode,
                    'color': self._color
                }, f, indent=2)
        except Exception:
            pass
    
    def _notify_callbacks(self):
        """Degisikligi bildir"""
        theme = self.get_theme()
        for callback in self._callbacks:
            try:
                callback(theme)
            except Exception:
                pass
    
    # === Public API ===
    
    def get_theme(self) -> dict:
        """Mevcut temayi dondur"""
        return build_theme(self._mode, self._color)
    
    def get_mode(self) -> str:
        return self._mode
    
    def get_color(self) -> str:
        return self._color
    
    def is_dark(self) -> bool:
        return self._mode == "dark"
    
    def set_mode(self, mode: str):
        if mode in ("dark", "light") and mode != self._mode:
            self._mode = mode
            self._save_settings()
            self._notify_callbacks()
    
    def set_color(self, color: str):
        if color in COLOR_PRESETS and color != self._color:
            self._color = color
            self._save_settings()
            self._notify_callbacks()
    
    def toggle_mode(self):
        self.set_mode("light" if self._mode == "dark" else "dark")
    
    def set_theme(self, mode: str, color: str):
        changed = False
        
        if mode in ("dark", "light") and mode != self._mode:
            self._mode = mode
            changed = True
        
        if color in COLOR_PRESETS and color != self._color:
            self._color = color
            changed = True
        
        if changed:
            self._save_settings()
            self._notify_callbacks()
    
    def on_theme_changed(self, callback: Callable):
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    @staticmethod
    def get_color_presets() -> dict:
        return COLOR_PRESETS.copy()
    
    @staticmethod
    def get_modes() -> list:
        return [
            {"id": "dark", "name": "Modern Dark", "icon": "D"},
            {"id": "light", "name": "Clean Light", "icon": "L"},
        ]


# =============================================================================
# GERIYE UYUMLULUK
# =============================================================================

# Eski fonksiyon adlari
build_nexor_theme = build_theme
create_nexor_theme = build_theme
NexorThemeManager = ThemeManager

# Global theme manager instance
_theme_manager = None

def get_theme_manager() -> ThemeManager:
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
