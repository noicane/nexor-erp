# -*- coding: utf-8 -*-
"""
NEXOR ERP - Sistem Modülü
"""
from modules import PageRegistry

MODULE_NAME = "sistem"

# Sayfa importları
from .sistem_veritabani import VeriTabaniBaglantiPage
from .sistem_kullanici import SistemKullaniciPage
from .sistem_rol import SistemRolPage
from .sistem_yetki import SistemYetkiPage
from .sistem_rol_izin import SistemRolIzinPage
from .sistem_kullanici_yetki import SistemKullaniciYetkiPage
from .sistem_ayar import SistemAyarPage
from .sistem_log import SistemLogPage
from .sistem_yedekleme import SistemYedeklemePage
from .sistem_whatsapp import SistemWhatsappPage
from .sistem_firma import SistemFirmaPage
from .bildirim_tercihleri import BildirimTercihleriPage
from .sistem_modul_lisans import SistemModulLisansPage
from .sistem_musteri_yonetimi import SistemMusteriYonetimiPage

# Sayfa kayıtları
PageRegistry.register("sistem_veritabani", VeriTabaniBaglantiPage, MODULE_NAME)
PageRegistry.register("sistem_kullanici", SistemKullaniciPage, MODULE_NAME)
PageRegistry.register("sistem_rol", SistemRolPage, MODULE_NAME)
PageRegistry.register("sistem_yetki", SistemYetkiPage, MODULE_NAME)
PageRegistry.register("sistem_rol_izin", SistemRolIzinPage, MODULE_NAME)
PageRegistry.register("sistem_kullanici_yetki", SistemKullaniciYetkiPage, MODULE_NAME)
PageRegistry.register("sistem_ayar", SistemAyarPage, MODULE_NAME)
PageRegistry.register("sistem_log", SistemLogPage, MODULE_NAME)
PageRegistry.register("sistem_yedekleme", SistemYedeklemePage, MODULE_NAME)
PageRegistry.register("sistem_whatsapp", SistemWhatsappPage, MODULE_NAME)
PageRegistry.register("sistem_firma", SistemFirmaPage, MODULE_NAME)
PageRegistry.register("bildirim_tercihleri", BildirimTercihleriPage, MODULE_NAME)
PageRegistry.register("sistem_modul_lisans", SistemModulLisansPage, MODULE_NAME)
PageRegistry.register("sistem_musteri_yonetimi", SistemMusteriYonetimiPage, MODULE_NAME)

__all__ = [
    "VeriTabaniBaglantiPage",
    "SistemKullaniciPage",
    "SistemRolPage",
    "SistemYetkiPage",
    "SistemRolIzinPage",
    "SistemKullaniciYetkiPage",
    "SistemAyarPage",
    "SistemLogPage",
    "SistemYedeklemePage",
    "SistemWhatsappPage",
    "SistemFirmaPage",
    "BildirimTercihleriPage",
    "SistemModulLisansPage",
    "SistemMusteriYonetimiPage",
]