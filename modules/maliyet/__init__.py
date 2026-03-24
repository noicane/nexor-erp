# -*- coding: utf-8 -*-
"""
NEXOR ERP - Maliyet Modulu
"""
from modules import PageRegistry

MODULE_NAME = "maliyet"

from .maliyet_personel import MaliyetPersonelPage

PageRegistry.register("maliyet_personel", MaliyetPersonelPage, MODULE_NAME)

__all__ = [
    "MaliyetPersonelPage",
]
