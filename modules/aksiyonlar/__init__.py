# -*- coding: utf-8 -*-
"""
NEXOR ERP - Aksiyonlar Modulu
Firma ici aksiyon takip ve yonetim
"""
from modules import PageRegistry

MODULE_NAME = "aksiyonlar"

# Sayfa importlari
from .aksiyon_liste import AksiyonListePage
from .aksiyon_bana_atanan import AksiyonBanaAtanan
from .aksiyon_dashboard import AksiyonDashboard
from .aksiyon_detay_dialog import AksiyonDetayDialog

# Sayfa kayitlari
PageRegistry.register("aksiyon_liste", AksiyonListePage, MODULE_NAME)
PageRegistry.register("aksiyon_bana_atanan", AksiyonBanaAtanan, MODULE_NAME)
PageRegistry.register("aksiyon_dashboard", AksiyonDashboard, MODULE_NAME)

__all__ = [
    "AksiyonListePage",
    "AksiyonBanaAtanan",
    "AksiyonDashboard",
    "AksiyonDetayDialog",
]
