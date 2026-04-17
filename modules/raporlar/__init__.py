# -*- coding: utf-8 -*-
"""
NEXOR ERP - Raporlar Modülü
"""
from modules import PageRegistry

MODULE_NAME = "raporlar"

# Sayfa importları
from .rapor_uretim import RaporUretimPage
from .rapor_kalite import RaporKalitePage
from .rapor_maliyet import RaporMaliyetPage
from .rapor_kpi import RaporKPIPage
from .rapor_musteri_hareket import RaporMusteriHareketPage
from .rapor_akim import RaporAkimPage

# Sayfa kayıtları
PageRegistry.register("rapor_uretim", RaporUretimPage, MODULE_NAME)
PageRegistry.register("rapor_kalite", RaporKalitePage, MODULE_NAME)
PageRegistry.register("rapor_maliyet", RaporMaliyetPage, MODULE_NAME)
PageRegistry.register("rapor_kpi", RaporKPIPage, MODULE_NAME)
PageRegistry.register("rapor_musteri_hareket", RaporMusteriHareketPage, MODULE_NAME)
PageRegistry.register("rapor_akim", RaporAkimPage, MODULE_NAME)

__all__ = [
    "RaporUretimPage",
    "RaporKalitePage",
    "RaporMaliyetPage",
    "RaporKPIPage",
    "RaporMusteriHareketPage",
    "RaporAkimPage"
]
