# -*- coding: utf-8 -*-
"""
NEXOR ERP - Sevkiyat Modülü
"""
from modules import PageRegistry

MODULE_NAME = "sevkiyat"

# Sayfa importları
from .sevk_liste import SevkListePage
from .sevk_yeni import SevkYeniPage
from .sevk_irsaliye import SevkIrsaliyePage
from .sevk_iade import SevkIadePage

# Sayfa kayıtları
PageRegistry.register("sevk_liste", SevkListePage, MODULE_NAME)
PageRegistry.register("sevk_yeni", SevkYeniPage, MODULE_NAME)
PageRegistry.register("sevk_irsaliye", SevkIrsaliyePage, MODULE_NAME)
PageRegistry.register("sevk_iade", SevkIadePage, MODULE_NAME)

__all__ = [
    "SevkListePage",
    "SevkYeniPage",
    "SevkIrsaliyePage",
    "SevkIadePage"
]
