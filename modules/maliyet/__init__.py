# -*- coding: utf-8 -*-
"""
NEXOR ERP - Maliyet Modulu
"""
from modules import PageRegistry

MODULE_NAME = "maliyet"

from .maliyet_personel import MaliyetPersonelPage
from .recete_maliyet import ReceteMaliyetPage

PageRegistry.register("maliyet_personel", MaliyetPersonelPage, MODULE_NAME)
PageRegistry.register("maliyet_recete", ReceteMaliyetPage, MODULE_NAME)

__all__ = [
    "MaliyetPersonelPage",
    "ReceteMaliyetPage",
]
