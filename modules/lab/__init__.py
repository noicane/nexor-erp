# -*- coding: utf-8 -*-
"""
NEXOR ERP - Laboratuvar Modülü
"""
from modules import PageRegistry

MODULE_NAME = "lab"

# Sayfa importları
from .lab_tanim import LabTanimPage
from .lab_sonuc import LabSonucPage
from .lab_banyo import LabBanyoPage
from .lab_kimyasal import LabKimyasalPage
from .lab_analiz import LabAnalizPage
from .lab_event_log import LabEventLogPage
from .lab_dashboard import LabDashboardPage
from .lab_kaplama_test import LabKaplamaTestPage  # YENİ

# Sayfa kayıtları
PageRegistry.register("lab_tanim", LabTanimPage, MODULE_NAME)
PageRegistry.register("lab_sonuc", LabSonucPage, MODULE_NAME)
PageRegistry.register("lab_banyo", LabBanyoPage, MODULE_NAME)
PageRegistry.register("lab_kimyasal", LabKimyasalPage, MODULE_NAME)
PageRegistry.register("lab_analiz", LabAnalizPage, MODULE_NAME)
PageRegistry.register("lab_event_log", LabEventLogPage, MODULE_NAME)
PageRegistry.register("lab_dashboard", LabDashboardPage, MODULE_NAME)
PageRegistry.register("lab_kaplama_test", LabKaplamaTestPage, MODULE_NAME)  # YENİ

__all__ = [
    "LabTanimPage",
    "LabSonucPage",
    "LabBanyoPage",
    "LabKimyasalPage",
    "LabAnalizPage",
    "LabEventLogPage",
    "LabDashboardPage",
    "LabKaplamaTestPage",
]
