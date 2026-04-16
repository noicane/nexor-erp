# -*- coding: utf-8 -*-
"""
NEXOR ERP - Dashboard Modülü
"""
from modules import PageRegistry

MODULE_NAME = "dashboard"

# Brand-aware v3 aktif dashboard
from .dashboard_v3 import DashboardPageV3
# Eski v2 geriye uyumluluk icin
from .dashboard_v2 import DashboardPageV2

# Alias — her ikisi de 'dashboard' sayfa kimligine esit
DashboardPage = DashboardPageV3

# Sayfa kayitlari
PageRegistry.register("dashboard", DashboardPageV3, MODULE_NAME)

__all__ = [
    "DashboardPage",
    "DashboardPageV2",
    "DashboardPageV3",
]
