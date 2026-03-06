# -*- coding: utf-8 -*-
"""
NEXOR ERP - Çevre Modülü
"""
from modules import PageRegistry

MODULE_NAME = "cevre"

# Sayfa importları
from .cevre_atik_yonetimi import CevreAtikYonetimiPage
from .cevre_emisyon import CevreEmisyonPage
from .cevre_izinler import CevreIzinlerPage
from .cevre_yasal_takip import CevreYasalTakipPage
from .cevre_su_enerji import CevreSuEnerjiPage
from .cevre_atiksu import CevreAtiksuPage
from .cevre_denetimler import CevreDenetimlerPage
from .cevre_kimyasal import CevreKimyasalEnvanterPage

# Sayfa kayıtları
PageRegistry.register("cevre_atik_yonetimi", CevreAtikYonetimiPage, MODULE_NAME)
PageRegistry.register("cevre_emisyon", CevreEmisyonPage, MODULE_NAME)
PageRegistry.register("cevre_izinler", CevreIzinlerPage, MODULE_NAME)
PageRegistry.register("cevre_yasal_takip", CevreYasalTakipPage, MODULE_NAME)
PageRegistry.register("cevre_su_enerji", CevreSuEnerjiPage, MODULE_NAME)
PageRegistry.register("cevre_atiksu", CevreAtiksuPage, MODULE_NAME)
PageRegistry.register("cevre_denetimler", CevreDenetimlerPage, MODULE_NAME)
PageRegistry.register("cevre_kimyasal", CevreKimyasalEnvanterPage, MODULE_NAME)

__all__ = [
    "CevreAtikYonetimiPage",
    "CevreEmisyonPage",
    "CevreIzinlerPage",
    "CevreYasalTakipPage",
    "CevreSuEnerjiPage",
    "CevreAtiksuPage",
    "CevreDenetimlerPage",
    "CevreKimyasalEnvanterPage"
]
