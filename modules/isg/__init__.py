# -*- coding: utf-8 -*-
"""
NEXOR ERP - İSG Modülü
"""
from modules import PageRegistry

MODULE_NAME = "isg"

# Sayfa importları
from .isg_risk_degerlendirme import ISGRiskDegerlendirmePage
from .isg_olay_kayitlari import ISGOlayKayitlariPage
from .isg_kkd_dagitim import ISGKKDDagitimPage
from .isg_egitimler import ISGEgitimlerPage
from .isg_saglik_gozetimi import ISGSaglikGozetimiPage
from .isg_denetimler import ISGDenetimlerPage
from .isg_yasal_takip import ISGYasalTakipPage
from .isg_acil_durum import ISGAcilDurumEkipleriPage
from .isg_tatbikatlar import ISGTatbikatlarPage
from .isg_gbf import ISGGBFPage

# Sayfa kayıtları
PageRegistry.register("isg_risk_degerlendirme", ISGRiskDegerlendirmePage, MODULE_NAME)
PageRegistry.register("isg_olay_kayitlari", ISGOlayKayitlariPage, MODULE_NAME)
PageRegistry.register("isg_kkd_dagitim", ISGKKDDagitimPage, MODULE_NAME)
PageRegistry.register("isg_egitimler", ISGEgitimlerPage, MODULE_NAME)
PageRegistry.register("isg_saglik_gozetimi", ISGSaglikGozetimiPage, MODULE_NAME)
PageRegistry.register("isg_denetimler", ISGDenetimlerPage, MODULE_NAME)
PageRegistry.register("isg_yasal_takip", ISGYasalTakipPage, MODULE_NAME)
PageRegistry.register("isg_acil_durum", ISGAcilDurumEkipleriPage, MODULE_NAME)
PageRegistry.register("isg_tatbikatlar", ISGTatbikatlarPage, MODULE_NAME)
PageRegistry.register("isg_gbf", ISGGBFPage, MODULE_NAME)

__all__ = [
    "ISGRiskDegerlendirmePage",
    "ISGOlayKayitlariPage",
    "ISGKKDDagitimPage",
    "ISGEgitimlerPage",
    "ISGSaglikGozetimiPage",
    "ISGDenetimlerPage",
    "ISGYasalTakipPage",
    "ISGAcilDurumEkipleriPage",
    "ISGTatbikatlarPage",
    "ISGGBFPage"
]
