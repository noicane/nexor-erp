# -*- coding: utf-8 -*-
"""
NEXOR ERP - Teklif Modülü
Kaplama sektörü teklif yönetimi
"""
from modules import PageRegistry

MODULE_NAME = "teklif"

# Sayfa importları
from .teklif_liste import TeklifListePage
from .teklif_sablonlar import TeklifSablonlarPage

# Sayfa kayıtları
PageRegistry.register("teklif_liste", TeklifListePage, MODULE_NAME)
PageRegistry.register("teklif_sablonlar", TeklifSablonlarPage, MODULE_NAME)

__all__ = [
    "TeklifListePage",
    "TeklifSablonlarPage",
]
