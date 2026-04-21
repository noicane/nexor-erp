# -*- coding: utf-8 -*-
"""
NEXOR ERP - Üretim Modülü
"""
from modules import PageRegistry

MODULE_NAME = "uretim"

# Sayfa importları
from .uretim_giris import UretimGirisPage
from .uretim_hat import UretimHatPage
from .uretim_verimlilik import VerimlilikAnalizPage
from .uretim_durus import UretimDurusPage
from .uretim_vardiya import UretimVardiyaPage
from .uretim_rework import ReworkPage
from .uretim_bara_dashboard import BaraDashboardPage
from .askilama_planlama import AskilamaPlanlamaPage

# Sayfa kayıtları
PageRegistry.register("uretim_giris", UretimGirisPage, MODULE_NAME)
PageRegistry.register("uretim_hat", UretimHatPage, MODULE_NAME)
PageRegistry.register("uretim_verimlilik", VerimlilikAnalizPage, MODULE_NAME)
PageRegistry.register("uretim_durus", UretimDurusPage, MODULE_NAME)
PageRegistry.register("uretim_vardiya", UretimVardiyaPage, MODULE_NAME)
PageRegistry.register("uretim_rework", ReworkPage, MODULE_NAME)
PageRegistry.register("uretim_bara_dashboard", BaraDashboardPage, MODULE_NAME)
PageRegistry.register("askilama_planlama", AskilamaPlanlamaPage, MODULE_NAME)

__all__ = [
    "UretimGirisPage",
    "UretimHatPage",
    "VerimlilikAnalizPage",
    "UretimDurusPage",
    "UretimVardiyaPage",
    "ReworkPage",
    "BaraDashboardPage",
    "AskilamaPlanlamaPage"
]
