# -*- coding: utf-8 -*-
"""
NEXOR ERP - Satınalma Modülü
"""
from modules import PageRegistry

MODULE_NAME = "satinalma"

# Sayfa importları
from .satinalma_talepler import SatinalmaTaleplerPage
from .satinalma_siparisler import SatinalmaSiparislerPage
from .satinalma_mal_kabul import MalKabulPage
from .satinalma_anlasmalar import TedarikciAnlasmalariPage

# Sayfa kayıtları
PageRegistry.register("satinalma_talepler", SatinalmaTaleplerPage, MODULE_NAME)
PageRegistry.register("satinalma_siparisler", SatinalmaSiparislerPage, MODULE_NAME)
PageRegistry.register("satinalma_mal_kabul", MalKabulPage, MODULE_NAME)
PageRegistry.register("satinalma_anlasmalar", TedarikciAnlasmalariPage, MODULE_NAME)

__all__ = [
    "SatinalmaTaleplerPage",
    "SatinalmaSiparislerPage",
    "MalKabulPage",
    "TedarikciAnlasmalariPage"
]
