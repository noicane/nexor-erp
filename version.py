# -*- coding: utf-8 -*-
"""
NEXOR ERP - Versiyon Bilgileri
===================================
Bu dosya build.py tarafından otomatik güncellenir.
Manuel değişiklik yapmayın!
"""

# Versiyon bilgileri (Semantic Versioning)
VERSION = "3.1.11"
VERSION_MAJOR = 3
VERSION_MINOR = 1
VERSION_PATCH = 11

# Build bilgileri
BUILD_DATE = "2026-04-03"
BUILD_NUMBER = 56

# Güncelleme sunucusu
from config import NAS_PATHS as _NAS_PATHS
UPDATE_SERVER = _NAS_PATHS["update_server"]
VERSION_FILE = "version.json"

# Uygulama bilgileri
APP_NAME = "NexorERP"
APP_DISPLAY_NAME = "Nexor ERP"
APP_AUTHOR = "ATMO Logic"


def get_version_tuple():
    """Versiyon tuple döndürür: (1, 0, 0)"""
    return (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)


def get_version_string():
    """Versiyon string döndürür: '1.0.0'"""
    return VERSION


def get_full_version():
    """Tam versiyon bilgisi: 'v1.0.0 (Build 1)'"""
    return f"v{VERSION} (Build {BUILD_NUMBER})"


def compare_versions(v1: str, v2: str) -> int:
    """
    İki versiyonu karşılaştırır.
    
    Returns:
        -1: v1 < v2 (v1 daha eski)
         0: v1 == v2 (aynı)
         1: v1 > v2 (v1 daha yeni)
    """
    def parse(v):
        return tuple(map(int, v.split('.')))
    
    t1, t2 = parse(v1), parse(v2)
    
    if t1 < t2:
        return -1
    elif t1 > t2:
        return 1
    return 0
