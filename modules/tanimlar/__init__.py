# -*- coding: utf-8 -*-
"""
NEXOR ERP - Tanımlar Modülü
"""
from modules import PageRegistry

MODULE_NAME = "tanimlar"

# Sayfa importları
from .tanim_hat import TanimHatPage
from .tanim_proses import TanimProsesPage
from .tanim_rota import TanimRotaPage
from .tanim_kaplama import TanimKaplamaPage
from .tanim_malzeme import TanimMalzemePage
from .tanim_depo import TanimDepoPage
from .tanim_akis import AkisYonetimiPage
from .tanim_hata_turleri import HataTurleriPage
from .tanim_vardiya import TanimVardiyaPage
from .tanim_izin_turleri import TanimIzinTurleriPage
from .tanim_zimmet_turleri import TanimZimmetTurleriPage
from .tanim_departmanlar import TanimDepartmanlarPage
from .tanim_etiket_tasarim import EtiketTasarimPage
from .tanim_giris_kalite_kriterleri import GirisKaliteKriterleriPage
from .tanim_pozisyonlar import TanimPozisyonlarPage
from .tanim_soforler import TanimSoforlerPage
from .tanim_araclar import TanimAraclarPage
from .tanim_numara import TanimNumaraPage
from .dokumantasyon_yonetimi import DokumantasyonYonetimiPage
from .bildirim_sistemi import BildirimSistemiPage

# Sayfa kayıtları
PageRegistry.register("tanim_hat", TanimHatPage, MODULE_NAME)
PageRegistry.register("tanim_proses", TanimProsesPage, MODULE_NAME)
PageRegistry.register("tanim_rota", TanimRotaPage, MODULE_NAME)
PageRegistry.register("tanim_kaplama", TanimKaplamaPage, MODULE_NAME)
PageRegistry.register("tanim_malzeme", TanimMalzemePage, MODULE_NAME)
PageRegistry.register("tanim_depo", TanimDepoPage, MODULE_NAME)
PageRegistry.register("tanim_akis", AkisYonetimiPage, MODULE_NAME)
PageRegistry.register("tanim_hata_turleri", HataTurleriPage, MODULE_NAME)
PageRegistry.register("tanim_vardiya", TanimVardiyaPage, MODULE_NAME)
PageRegistry.register("tanim_izin_turleri", TanimIzinTurleriPage, MODULE_NAME)
PageRegistry.register("tanim_zimmet_turleri", TanimZimmetTurleriPage, MODULE_NAME)
PageRegistry.register("tanim_departmanlar", TanimDepartmanlarPage, MODULE_NAME)
PageRegistry.register("tanim_etiket_tasarim", EtiketTasarimPage, MODULE_NAME)
PageRegistry.register("tanim_giris_kalite_kriterleri", GirisKaliteKriterleriPage, MODULE_NAME)
PageRegistry.register("tanim_pozisyonlar", TanimPozisyonlarPage, MODULE_NAME)
PageRegistry.register("tanim_soforler", TanimSoforlerPage, MODULE_NAME)
PageRegistry.register("tanim_araclar", TanimAraclarPage, MODULE_NAME)
PageRegistry.register("tanim_numara", TanimNumaraPage, MODULE_NAME)
PageRegistry.register("dokumantasyon_yonetimi", DokumantasyonYonetimiPage, MODULE_NAME)
PageRegistry.register("bildirim_sistemi", BildirimSistemiPage, MODULE_NAME)

__all__ = [
    "TanimHatPage",
    "TanimProsesPage",
    "TanimRotaPage",
    "TanimKaplamaPage",
    "TanimMalzemePage",
    "TanimDepoPage",
    "AkisYonetimiPage",
    "HataTurleriPage",
    "TanimVardiyaPage",
    "TanimIzinTurleriPage",
    "TanimZimmetTurleriPage",
    "TanimDepartmanlarPage",
    "EtiketTasarimPage",
    "GirisKaliteKriterleriPage",
    "TanimPozisyonlarPage",
    "TanimSoforlerPage",
    "TanimAraclarPage",
    "TanimNumaraPage",
    "DokumantasyonYonetimiPage",
    "BildirimSistemiPage"
]
