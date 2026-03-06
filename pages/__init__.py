# -*- coding: utf-8 -*-
"""
NEXOR ERP - Sayfalar (Eski uyumluluk için)

NOT: Bu dosya geriye dönük uyumluluk için korunmaktadır.
     Yeni kod modules/ yapısını kullanmalıdır.
"""
# Modül sistemini import et
from modules import PageRegistry

# PAGE_CLASSES'ı PageRegistry'den oluştur
def get_page_classes():
    """Geriye dönük uyumluluk için PAGE_CLASSES dict'i döndürür"""
    return PageRegistry.all_pages()

PAGE_CLASSES = get_page_classes()

# Eski import'lar için - modüllerden re-export
from modules.dashboard import *
from modules.cari import *
from modules.stok import *
from modules.is_emirleri import *
from modules.uretim import *
from modules.kalite import *
from modules.lab import *
from modules.depo import *
from modules.sevkiyat import *
from modules.satinalma import *
from modules.ik import *
from modules.bakim import *
from modules.isg import *
from modules.cevre import *
from modules.tanimlar import *
from modules.raporlar import *
from modules.sistem import *
from modules.yonetim import *
from modules.placeholder import PlaceholderPage
