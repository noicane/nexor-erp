# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kaplama Planlama Modülü
Haftalık kaplama hattı planlama ve Gantt çizelgesi
"""
from modules import PageRegistry

MODULE_NAME = "kaplama_planlama"

from .kaplama_planlama_page import KaplamaPlanlamaPage

PageRegistry.register("kaplama_planlama", KaplamaPlanlamaPage, MODULE_NAME)

__all__ = ["KaplamaPlanlamaPage"]
