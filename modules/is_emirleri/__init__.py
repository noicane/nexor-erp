# -*- coding: utf-8 -*-
"""
NEXOR ERP - İş Emirleri Modülü
"""
from modules import PageRegistry

MODULE_NAME = "is_emirleri"

# Sayfa importları
from .ie_liste import IsEmriListePage
from .ie_yeni import IsEmriYeniPage
from .ie_planlama import IsEmriPlanlamaPage
from .ie_termin import IsEmriTerminPage

# Sayfa kayıtları
PageRegistry.register("ie_liste", IsEmriListePage, MODULE_NAME)
PageRegistry.register("ie_yeni", IsEmriYeniPage, MODULE_NAME)
PageRegistry.register("ie_planlama", IsEmriPlanlamaPage, MODULE_NAME)
PageRegistry.register("ie_termin", IsEmriTerminPage, MODULE_NAME)

__all__ = [
    "IsEmriListePage",
    "IsEmriYeniPage",
    "IsEmriPlanlamaPage",
    "IsEmriTerminPage"
]