# -*- coding: utf-8 -*-
"""
NEXOR ERP - Modül Sistemi
Tüm sayfa modüllerinin merkezi yönetimi
"""
from typing import Dict, Type, Optional, List
from dataclasses import dataclass


@dataclass
class ModuleInfo:
    """Modül bilgisi"""
    name: str
    title: str
    icon: str
    description: str
    enabled: bool = True


# Modül tanımları
MODULES: Dict[str, ModuleInfo] = {
    "dashboard": ModuleInfo("dashboard", "Dashboard", "📊", "Ana gösterge paneli"),
    "cari": ModuleInfo("cari", "Cari Hesaplar", "👥", "Müşteri ve tedarikçi yönetimi"),
    "stok": ModuleInfo("stok", "Stok Yönetimi", "📦", "Ürün ve stok kartları"),
    "teklif": ModuleInfo("teklif", "Teklifler", "📝", "Teklif yönetimi"),
    "is_emirleri": ModuleInfo("is_emirleri", "İş Emirleri", "📋", "İş emri planlama ve takip"),
    "uretim": ModuleInfo("uretim", "Üretim", "🏭", "Üretim operasyonları"),
    "kalite": ModuleInfo("kalite", "Kalite", "✅", "Kalite kontrol ve yönetim"),
    "lab": ModuleInfo("lab", "Laboratuvar", "🔬", "Lab analizleri ve testler"),
    "depo": ModuleInfo("depo", "Depo", "🏪", "Depo ve envanter yönetimi"),
    "sevkiyat": ModuleInfo("sevkiyat", "Sevkiyat", "🚚", "Sevkiyat ve irsaliye"),
    "satinalma": ModuleInfo("satinalma", "Satınalma", "🛒", "Satınalma süreçleri"),
    "ik": ModuleInfo("ik", "İnsan Kaynakları", "👔", "Personel ve PDKS yönetimi"),
    "bakim": ModuleInfo("bakim", "Bakım", "🔧", "Ekipman bakım yönetimi"),
    "isg": ModuleInfo("isg", "İSG", "⛑️", "İş sağlığı ve güvenliği"),
    "cevre": ModuleInfo("cevre", "Çevre", "🌿", "Çevre yönetimi"),
    "tanimlar": ModuleInfo("tanimlar", "Tanımlar", "⚙️", "Sistem tanımları"),
    "raporlar": ModuleInfo("raporlar", "Raporlar", "📈", "Raporlama sistemi"),
    "sistem": ModuleInfo("sistem", "Sistem", "🖥️", "Sistem yönetimi"),
    "yonetim": ModuleInfo("yonetim", "Yönetim", "📊", "Yönetim raporları"),
    "aksiyonlar": ModuleInfo("aksiyonlar", "Aksiyonlar", "📋", "Aksiyon takip ve yönetim"),
    "kaplama_planlama": ModuleInfo("kaplama_planlama", "Kaplama Planlama", "📅", "Kaplama hattı haftalık planlama"),
    "maliyet": ModuleInfo("maliyet", "Maliyet", "💰", "Maliyet yönetimi ve analizi"),
}


class PageRegistry:
    """
    Sayfa kayıt sistemi - Tüm sayfaları merkezi olarak yönetir
    """
    _pages: Dict[str, Type] = {}
    _page_modules: Dict[str, str] = {}  # page_id -> module_name
    
    @classmethod
    def register(cls, page_id: str, page_class: Type, module_name: str = None):
        """Sayfa kaydet"""
        cls._pages[page_id] = page_class
        if module_name:
            cls._page_modules[page_id] = module_name
    
    @classmethod
    def get(cls, page_id: str) -> Optional[Type]:
        """Sayfa sınıfını getir"""
        return cls._pages.get(page_id)
    
    @classmethod
    def get_module(cls, page_id: str) -> Optional[str]:
        """Sayfanın modülünü getir"""
        return cls._page_modules.get(page_id)
    
    @classmethod
    def all_pages(cls) -> Dict[str, Type]:
        """Tüm sayfaları getir"""
        return cls._pages.copy()
    
    @classmethod
    def pages_by_module(cls, module_name: str) -> Dict[str, Type]:
        """Modüle ait sayfaları getir"""
        return {
            page_id: page_class
            for page_id, page_class in cls._pages.items()
            if cls._page_modules.get(page_id) == module_name
        }
    
    @classmethod
    def is_registered(cls, page_id: str) -> bool:
        """Sayfa kayıtlı mı?"""
        return page_id in cls._pages


def get_enabled_modules() -> List[str]:
    """Aktif modülleri getir"""
    return [name for name, info in MODULES.items() if info.enabled]


def get_module_info(module_name: str) -> Optional[ModuleInfo]:
    """Modül bilgisini getir"""
    return MODULES.get(module_name)


# Modülleri import et (circular import'ları önlemek için en sonda)
def _import_modules():
    """Modülleri gecikmeli yükle"""
    from modules import dashboard
    from modules import cari
    from modules import stok
    from modules import teklif
    from modules import is_emirleri
    from modules import uretim
    from modules import kalite
    from modules import lab
    from modules import depo
    from modules import sevkiyat
    from modules import satinalma
    from modules import ik
    from modules import bakim
    from modules import isg
    from modules import cevre
    from modules import tanimlar
    from modules import raporlar
    from modules import sistem
    from modules import yonetim
    from modules import aksiyonlar
    from modules import kaplama_planlama
    from modules import maliyet


def get_placeholder_page():
    """PlaceholderPage'i lazy yükle"""
    from modules.placeholder import PlaceholderPage
    return PlaceholderPage


# Modülleri yükle
_import_modules()

__all__ = [
    'MODULES',
    'ModuleInfo', 
    'PageRegistry',
    'get_enabled_modules',
    'get_module_info',
    'get_placeholder_page',
]
