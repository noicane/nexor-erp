# -*- coding: utf-8 -*-
"""
NEXOR ERP - Firma Bilgileri Yardimci Modulu
config.json icindeki company bolumunden firma bilgilerini okur/yazar.
"""
import logging
from typing import Dict, Optional

from core.external_config import config_manager

logger = logging.getLogger(__name__)

DEFAULT_COMPANY = {
    "name": "",
    "address": "",
    "phone": "",
    "email": "",
    "tax_id": "",
    "logo_path": ""
}


def get_firma_bilgileri() -> Dict[str, str]:
    """
    config.json'dan firma bilgilerini oku.

    Returns:
        dict: name, address, phone, email, tax_id, logo_path
    """
    data = config_manager.get('company', None)
    if not data or not isinstance(data, dict):
        return DEFAULT_COMPANY.copy()

    result = DEFAULT_COMPANY.copy()
    result.update({k: v for k, v in data.items() if k in DEFAULT_COMPANY})
    return result


def set_firma_bilgileri(data: Dict[str, str]) -> bool:
    """
    Firma bilgilerini config.json'a yaz.

    Args:
        data: name, address, phone, email, tax_id, logo_path alanlari

    Returns:
        bool: Basarili ise True
    """
    current = get_firma_bilgileri()
    current.update({k: v for k, v in data.items() if k in DEFAULT_COMPANY})
    config_manager.set('company', current)
    return config_manager.save()


def get_firma_logo_path() -> Optional[str]:
    """
    Firma logo yolunu dondur.

    Returns:
        str | None: Logo yolu veya None
    """
    bilgi = get_firma_bilgileri()
    path = bilgi.get('logo_path', '')
    if path:
        import os
        if os.path.isfile(path):
            return path
    return None
