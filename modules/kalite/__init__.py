# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kalite Modülü
"""
from modules import PageRegistry

MODULE_NAME = "kalite"

# Sayfa importları
from .kalite_giris import KaliteGirisPage
from .kalite_proses import KaliteProsesPage
from .kalite_red import KaliteRedPage
from .kalite_8d import Kalite8DPage
from .kalite_ppap import KalitePPAPPage
from .kalite_kalibrasyon import KaliteKalibrasyonPage
from .kalite_final_kontrol import KaliteFinalKontrolPage
from .kalite_polivelans import PolivelansPage
from .kalite_fmea import FMEAYonetimiPage
from .kalite_kontrol_plani import KontrolPlaniPage
from .kalite_event_log import EventLogPage  # ← YENİ

# Sayfa kayıtları
PageRegistry.register("kalite_giris", KaliteGirisPage, MODULE_NAME)
PageRegistry.register("kalite_proses", KaliteProsesPage, MODULE_NAME)
PageRegistry.register("kalite_red", KaliteRedPage, MODULE_NAME)
PageRegistry.register("kalite_8d", Kalite8DPage, MODULE_NAME)
PageRegistry.register("kalite_ppap", KalitePPAPPage, MODULE_NAME)
PageRegistry.register("kalite_kalibrasyon", KaliteKalibrasyonPage, MODULE_NAME)
PageRegistry.register("kalite_final_kontrol", KaliteFinalKontrolPage, MODULE_NAME)
PageRegistry.register("kalite_polivelans", PolivelansPage, MODULE_NAME)
PageRegistry.register("kalite_fmea", FMEAYonetimiPage, MODULE_NAME)
PageRegistry.register("kalite_kontrol_plani", KontrolPlaniPage, MODULE_NAME)
PageRegistry.register("event_log", EventLogPage, MODULE_NAME)  # ← YENİ

__all__ = [
    "KaliteGirisPage",
    "KaliteProsesPage",
    "KaliteRedPage",
    "Kalite8DPage",
    "KalitePPAPPage",
    "KaliteKalibrasyonPage",
    "KaliteFinalKontrolPage",
    "PolivelansPage",
    "FMEAYonetimiPage",
    "KontrolPlaniPage",
    "EventLogPage"  # ← YENİ
]
