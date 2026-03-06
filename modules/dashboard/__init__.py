# -*- coding: utf-8 -*-
"""
NEXOR ERP - Dashboard Modülü
"""
from modules import PageRegistry

MODULE_NAME = "dashboard"

# Sayfa importları - Her iki dosyada da DashboardPageV2 var
from .dashboard_v2 import DashboardPageV2

# Geriye dönük uyumluluk için alias
DashboardPage = DashboardPageV2

# Sayfa kayıtları
PageRegistry.register("dashboard", DashboardPageV2, MODULE_NAME)

__all__ = [
    "DashboardPage",
    "DashboardPageV2"
]
