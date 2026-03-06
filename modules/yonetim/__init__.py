# -*- coding: utf-8 -*-
"""
NEXOR ERP - Yönetim Modülü
"""
from modules import PageRegistry

MODULE_NAME = "yonetim"

# Sayfa importları
from .yonetim_bara_hesaplama import BaraHesaplamaPage
from .yonetim_ciro_analiz import CiroAnalizPage

# Alias'lar
YonetimBaraHesaplamaPage = BaraHesaplamaPage
YonetimCiroAnalizPage = CiroAnalizPage

# Sayfa kayıtları
PageRegistry.register("yonetim_bara_hesaplama", BaraHesaplamaPage, MODULE_NAME)
PageRegistry.register("yonetim_ciro_analiz", CiroAnalizPage, MODULE_NAME)

__all__ = [
    "BaraHesaplamaPage",
    "CiroAnalizPage",
    "YonetimBaraHesaplamaPage",
    "YonetimCiroAnalizPage"
]
