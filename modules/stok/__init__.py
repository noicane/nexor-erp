# -*- coding: utf-8 -*-
"""
NEXOR ERP - Stok Yönetimi Modülü
"""
from modules import PageRegistry

MODULE_NAME = "stok"

# Sayfa importları
from .stok_liste import StokListePage
from .stok_fiyat import StokFiyatPage
from .stok_maliyet import StokMaliyetPage
from .stok_kimyasal import StokKimyasalPage
from .stok_havuzu import StokHavuzuPage
from .urun_izlenebilirlik import UrunIzlenebilirlikPage

# Sayfa kayıtları
PageRegistry.register("stok_liste", StokListePage, MODULE_NAME)
PageRegistry.register("stok_fiyat", StokFiyatPage, MODULE_NAME)
PageRegistry.register("stok_maliyet", StokMaliyetPage, MODULE_NAME)
PageRegistry.register("stok_kimyasal", StokKimyasalPage, MODULE_NAME)
PageRegistry.register("stok_havuzu", StokHavuzuPage, MODULE_NAME)
PageRegistry.register("urun_izlenebilirlik", UrunIzlenebilirlikPage, MODULE_NAME)

__all__ = [
    "StokListePage",
    "StokFiyatPage",
    "StokMaliyetPage",
    "StokKimyasalPage",
    "StokHavuzuPage",
    "UrunIzlenebilirlikPage"
]
