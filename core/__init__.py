# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Core Modülleri
"""

# Mevcut importlar
from .database import get_db_connection
from .menu_structure import MENU_STRUCTURE

# Updater
try:
    from .updater import SelfUpdater, UpdateInfo, UpdateDialog
except ImportError as e:
    print(f"updater import hatası: {e}")
    SelfUpdater = None
    UpdateInfo = None
    UpdateDialog = None

# Servisler - try/except ile güvenli import
try:
    from .hareket_motoru import HareketMotoru, HareketTipi, HareketSonuc, HareketNedeni
except ImportError as e:
    print(f"hareket_motoru import hatası: {e}")
    HareketMotoru = None
    HareketTipi = None
    HareketSonuc = None
    HareketNedeni = None

try:
    from .stok_servisi import StokServisi, StokBakiye, StokOzet
except ImportError as e:
    print(f"stok_servisi import hatası: {e}")
    StokServisi = None
    StokBakiye = None
    StokOzet = None

try:
    from .is_emri_servisi import IsEmriServisi, IsEmriDurum, IsEmri, IsEmriOzet
except ImportError as e:
    print(f"is_emri_servisi import hatası: {e}")
    IsEmriServisi = None
    IsEmriDurum = None
    IsEmri = None
    IsEmriOzet = None

try:
    from .akis_servisi import AkisServisi, AkisSablon, AkisAdim
except ImportError as e:
    print(f"akis_servisi import hatası: {e}")
    AkisServisi = None
    AkisSablon = None
    AkisAdim = None

__all__ = [
    # Mevcut
    'get_db_connection',
    'MENU_STRUCTURE',
    
    # Updater
    'SelfUpdater',
    'UpdateInfo',
    'UpdateDialog',
    
    # Hareket Motoru
    'HareketMotoru',
    'HareketTipi', 
    'HareketSonuc',
    'HareketNedeni',
    
    # Stok Servisi
    'StokServisi',
    'StokBakiye',
    'StokOzet',
    
    # İş Emri Servisi
    'IsEmriServisi',
    'IsEmriDurum',
    'IsEmri',
    'IsEmriOzet',
    
    # Akış Servisi
    'AkisServisi',
    'AkisSablon',
    'AkisAdim',
]