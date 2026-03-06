# -*- coding: utf-8 -*-
"""
NEXOR ERP - Cari Hesaplar Modülü
"""
from modules import PageRegistry

MODULE_NAME = "cari"

# Sayfa importları
from .cari_liste import CariListePage
from .cari_detay import CariDetayPage
from .cari_bakiye import CariBakiyePage
from .cari_adresler import CariAdreslerPage
from .cari_yetkililer import CariYetkililerPage
from .cari_spesifikasyonlar import CariSpesifikasyonlarPage

# Sayfa kayıtları
PageRegistry.register("cari_liste", CariListePage, MODULE_NAME)
PageRegistry.register("cari_detay", CariDetayPage, MODULE_NAME)
PageRegistry.register("cari_bakiye", CariBakiyePage, MODULE_NAME)
PageRegistry.register("cari_adresler", CariAdreslerPage, MODULE_NAME)
PageRegistry.register("cari_yetkililer", CariYetkililerPage, MODULE_NAME)
PageRegistry.register("cari_spesifikasyonlar", CariSpesifikasyonlarPage, MODULE_NAME)

__all__ = [
    "CariListePage",
    "CariDetayPage",
    "CariBakiyePage",
    "CariAdreslerPage",
    "CariYetkililerPage",
    "CariSpesifikasyonlarPage"
]
