# -*- coding: utf-8 -*-
"""
NEXOR ERP - Bakım Modülü
"""
from modules import PageRegistry

MODULE_NAME = "bakim"

# Sayfa importları
from .bakim_ekipman import BakimEkipmanPage
from .bakim_plan import BakimPlanPage
from .bakim_ariza import BakimArizaPage
from .bakim_yedek import BakimYedekPage
from .bakim_durus_talep import BakimDurusTalepPage

# Sayfa kayıtları
PageRegistry.register("bakim_ekipman", BakimEkipmanPage, MODULE_NAME)
PageRegistry.register("bakim_plan", BakimPlanPage, MODULE_NAME)
PageRegistry.register("bakim_ariza", BakimArizaPage, MODULE_NAME)
PageRegistry.register("bakim_yedek", BakimYedekPage, MODULE_NAME)
PageRegistry.register("bakim_durus_talep", BakimDurusTalepPage, MODULE_NAME)

__all__ = [
    "BakimEkipmanPage",
    "BakimPlanPage",
    "BakimArizaPage",
    "BakimYedekPage",
    "BakimDurusTalepPage"
]
