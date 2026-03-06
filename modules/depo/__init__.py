# -*- coding: utf-8 -*-
"""
NEXOR ERP - Depo Modülü
"""
from modules import PageRegistry

MODULE_NAME = "depo"

# Sayfa importları
from .depo_takip import DepoTakipPage
from .depo_kabul import DepoKabulPage
from .depo_cikis import DepoCikisPage
from .depo_emanet import DepoEmanetPage
from .depo_sayim import DepoSayimPage
from .depo_stok_takip import DepoStokTakipPage
from .depo_tanimlari_ui import DepoTanimlariWidget

# Alias
DepoTanimlariPage = DepoTanimlariWidget

# Sayfa kayıtları
PageRegistry.register("depo_takip", DepoTakipPage, MODULE_NAME)
PageRegistry.register("depo_kabul", DepoKabulPage, MODULE_NAME)
PageRegistry.register("depo_cikis", DepoCikisPage, MODULE_NAME)
PageRegistry.register("depo_emanet", DepoEmanetPage, MODULE_NAME)
PageRegistry.register("depo_sayim", DepoSayimPage, MODULE_NAME)
PageRegistry.register("depo_stok_takip", DepoStokTakipPage, MODULE_NAME)
PageRegistry.register("depo_tanimlari", DepoTanimlariWidget, MODULE_NAME)

__all__ = [
    "DepoTakipPage",
    "DepoKabulPage",
    "DepoCikisPage",
    "DepoEmanetPage",
    "DepoSayimPage",
    "DepoStokTakipPage",
    "DepoTanimlariPage",
    "DepoTanimlariWidget"
]
