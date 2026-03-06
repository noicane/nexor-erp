# -*- coding: utf-8 -*-
"""
NEXOR ERP - İnsan Kaynakları Modülü
"""
from modules import PageRegistry

MODULE_NAME = "ik"

# Sayfa importları
from .ik_personel import IKPersonelPage
from .ik_puantaj import IKPuantajPage
from .ik_izin import IKIzinPage
from .ik_zimmet import IKZimmetPage
from .ik_pdks import IKPdksPage
from .ik_vardiya import IKVardiyaPage
from .ik_egitim import IKEgitimPage
from .pdks_cihaz_ayarlari import PDKSCihazAyarlariPage
from .pdks_service_control import PDKSServiceControlPage

# Sayfa kayıtları
PageRegistry.register("ik_personel", IKPersonelPage, MODULE_NAME)
PageRegistry.register("ik_puantaj", IKPuantajPage, MODULE_NAME)
PageRegistry.register("ik_izin", IKIzinPage, MODULE_NAME)
PageRegistry.register("ik_zimmet", IKZimmetPage, MODULE_NAME)
PageRegistry.register("ik_pdks", IKPdksPage, MODULE_NAME)
PageRegistry.register("ik_vardiya", IKVardiyaPage, MODULE_NAME)
PageRegistry.register("ik_egitim", IKEgitimPage, MODULE_NAME)
PageRegistry.register("pdks_cihaz_ayarlari", PDKSCihazAyarlariPage, MODULE_NAME)
PageRegistry.register("pdks_service_control", PDKSServiceControlPage, MODULE_NAME)

__all__ = [
    "IKPersonelPage",
    "IKPuantajPage",
    "IKIzinPage",
    "IKZimmetPage",
    "IKPdksPage",
    "IKVardiyaPage",
    "IKEgitimPage",
    "PDKSCihazAyarlariPage",
    "PDKSServiceControlPage"
]
