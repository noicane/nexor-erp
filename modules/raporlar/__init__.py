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

# Sayfa kayıtları
PageRegistry.register("rapor_uretim", RaporUretimPage, MODULE_NAME)
PageRegistry.register("rapor_kalite", RaporKalitePage, MODULE_NAME)
PageRegistry.register("rapor_maliyet", RaporMaliyetPage, MODULE_NAME)
PageRegistry.register("rapor_kpi", RaporKPIPage, MODULE_NAME)

__all__ = [
    "RaporUretimPage",
    "RaporKalitePage",
    "RaporMaliyetPage",
    "RaporKPIPage"
]
