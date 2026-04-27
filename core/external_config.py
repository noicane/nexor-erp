# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Harici Konfigurasyon Yoneticisi
C:/NEXOR/config.json dosyasindan ayarlari yonetir

Ozellikler:
- JSON formatinda harici config
- Sifre base64 encoding (basit obfuscation)
- Ilk kurulum wizard destegi
- Baglanti testi
- Otomatik yedekleme

Tarih: 2026-01-26
"""

import json
import os
import base64
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# =============================================================================
# UDL DOSYASI DESTEGI
# =============================================================================

def _find_udl_file() -> Optional[Path]:
    """
    Nexor.UDL dosyasini ara (oncelik sirasina gore)

    Arama sirasi:
        1. config.json icindeki "udl_path" ayari (sunucu yolu vb.)
        2. Uygulama dizini (Nexor.UDL)
        3. C:/NEXOR/Nexor.UDL
    """
    import sys

    # 1. config.json'dan udl_path oku (varsa)
    # Yeni format (v2.0): profiles[active_profile].udl_path
    # Eski format (v1.0): top-level udl_path
    udl_from_config = None
    try:
        config_path = None
        if getattr(sys, 'frozen', False):
            config_path = Path(sys.executable).parent / "config.json"
        else:
            config_path = Path(__file__).parent.parent / "config.json"

        if config_path and config_path.exists():
            import json as _json
            with open(config_path, 'r', encoding='utf-8') as _f:
                _cfg = _json.load(_f)
            # Yeni format: aktif profilin udl_path'i
            active = _cfg.get('active_profile')
            profiles = _cfg.get('profiles') or {}
            if active and active in profiles:
                udl_from_config = (profiles[active] or {}).get('udl_path', '')
            # Eski format fallback
            if not udl_from_config:
                udl_from_config = _cfg.get('udl_path', '')
    except Exception:
        pass

    search_paths = []

    # 1. config.json'daki yol (en oncelikli)
    if udl_from_config:
        search_paths.append(Path(udl_from_config))

    # 2. Uygulama dizini
    if getattr(sys, 'frozen', False):
        # EXE'nin yanı
        search_paths.append(Path(sys.executable).parent / "Nexor.UDL")
        # _MEIPASS (PyInstaller internal dizini)
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            search_paths.append(Path(meipass) / "Nexor.UDL")
    else:
        search_paths.append(Path(__file__).parent.parent / "Nexor.UDL")

    # 3. C:/NEXOR
    search_paths.append(Path("C:/NEXOR/Nexor.UDL"))

    for p in search_paths:
        try:
            if p.exists():
                return p
        except (OSError, PermissionError):
            continue
    return None


def parse_udl_file(udl_path: Path) -> Optional[Dict[str, str]]:
    """
    UDL dosyasindan baglanti bilgilerini oku.

    UDL formati:
        [oledb]
        ; Everything after this line is an OLE DB initstring
        Provider=SQLOLEDB.1;...;Data Source=SERVER;Initial Catalog=DB;User ID=x;Password=y

    Returns:
        {'server': ..., 'database': ..., 'user': ..., 'password': ...} veya None
    """
    try:
        # Windows UDL dosyalari UTF-16 LE kodlamasi kullanir
        try:
            content = udl_path.read_text(encoding='utf-16')
        except (UnicodeError, UnicodeDecodeError):
            content = udl_path.read_text(encoding='utf-8')

        for line in content.splitlines():
            line = line.strip()
            # Bos satirlari, bolum basliklarini ve yorumlari atla
            if not line or line.startswith('[') or line.startswith(';'):
                continue

            # OLE DB connection string satirini parse et
            params = {}
            for part in line.split(';'):
                part = part.strip()
                if '=' in part:
                    key, value = part.split('=', 1)
                    params[key.strip().lower()] = value.strip()

            server = params.get('data source', '')
            database = params.get('initial catalog', '')

            if server and database:
                result = {
                    'server': server,
                    'database': database,
                    'user': params.get('user id', ''),
                    'password': params.get('password', ''),
                }
                logger.info(f"UDL dosyasindan baglanti bilgileri okundu: {udl_path}")
                return result

        logger.warning(f"UDL dosyasinda gecerli baglanti bilgisi bulunamadi: {udl_path}")
        return None

    except Exception as e:
        logger.error(f"UDL dosyasi okuma hatasi ({udl_path}): {e}")
        return None


# UDL dosyasini baslangicta bir kez ara
_UDL_FILE = _find_udl_file()
if _UDL_FILE:
    print(f"[CONFIG] UDL dosyasi bulundu: {_UDL_FILE}")


# =============================================================================
# SABITLER
# =============================================================================

# Config dosyasi konumu - Uygulama dizininde veya C:/NEXOR
def _get_config_path():
    """Config dosyası yolunu belirle"""
    import sys
    from pathlib import Path
    
    # 1. Önce uygulama dizinini kontrol et
    if getattr(sys, 'frozen', False):
        # PyInstaller ile paketlenmiş
        app_dir = Path(sys.executable).parent
    else:
        # Development modu - main.py'nin bulunduğu dizin
        app_dir = Path(__file__).parent.parent
    
    # Uygulama dizininde config.json varsa veya yazılabilirse orayı kullan
    app_config = app_dir / "config.json"
    
    # 2. C:/NEXOR dizinini de kontrol et (eski uyumluluk)
    system_config_dir = Path("C:/NEXOR")
    system_config = system_config_dir / "config.json"
    
    # Öncelik: Mevcut config dosyası
    if app_config.exists():
        return app_dir, app_config
    elif system_config.exists():
        return system_config_dir, system_config
    
    # Yeni kurulum - uygulama dizinini tercih et
    try:
        # Yazma testi
        test_file = app_dir / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        return app_dir, app_config
    except Exception:
        # Uygulama dizinine yazılamıyorsa C:/NEXOR kullan
        return system_config_dir, system_config

CONFIG_DIR, CONFIG_FILE = _get_config_path()
CONFIG_BACKUP_DIR = CONFIG_DIR / "config_backups"

# Debug için log
print(f"[CONFIG] Dizin: {CONFIG_DIR}")
print(f"[CONFIG] Dosya: {CONFIG_FILE}")

# Profil-spesifik anahtarlar: aktif profilin altinda yasarlar.
# get/set/save bu anahtarlari otomatik olarak profile yonlendirir.
_PROFILE_KEYS = {
    "udl_path",
    "database",
    "plc_database",
    "pdks",
    "company",
    "musteri_kodu",
    "musteri_adi",
    "kisa_ad",
    "musteri_tipi",
    "segment",
    "sektor",
    "durum",
    "logo_path",
    "vergi",
    "iletisim",
    "adresler",
    "kisiler",
    "anlasma",
    "bakim",
    "kurulum",
    "belgeler",
    "raporlama",
    "moduller_aktif",
    "nas",
    "aktiviteler",
    "destek",
    "finansal",
    "audit_log",
}

# Varsayilan profil icerigi
DEFAULT_PROFILE = {
    "musteri_kodu": "default",
    "musteri_adi": "",
    "kisa_ad": "",
    "musteri_tipi": "AKTIF",   # DEMO, AKTIF, ESKI, PILOT
    "segment": "",              # Mikro, KOBI, Kurumsal
    "sektor": "",
    "durum": "AKTIF",           # AKTIF, PASIF, ASKIDA
    "udl_path": "",
    "logo_path": "",

    "vergi": {
        "vergi_dairesi": "",
        "vkn_tckn": "",
        "mersis_no": ""
    },

    "iletisim": {
        "telefon": "",
        "email": "",
        "web": ""
    },

    "adresler": [],   # her kayit: {tip, baslik, adres, sehir, ilce, posta_kodu}
    "kisiler": [],    # her kayit: {ad, unvan, telefon, email, rol}

    "database": {
        "server": "localhost\\SQLEXPRESS",
        "database": "NexorERP",
        "user": "",
        "password": "",  # Base64 encoded
        "driver": "ODBC Driver 18 for SQL Server",
        "timeout": 10,
        "max_connections": 20,
        "trusted_connection": False
    },
    "plc_database": {
        "enabled": False,
        "server": "localhost\\SQLEXPRESS",
        "database": "PLC_Database",
        "user": "",
        "password": "",
        "driver": "ODBC Driver 18 for SQL Server",
        "timeout": 5,
        "max_connections": 5
    },
    "pdks": {
        "enabled": False,
        "device_ip": "",
        "device_port": 4370,
        "poll_interval": 10
    },
    "company": {
        "name": "",
        "address": "",
        "phone": "",
        "email": "",
        "tax_id": "",
        "logo_path": ""
    },

    "anlasma": {
        "sozlesme_no": "",
        "baslangic_tarihi": "",
        "bitis_tarihi": "",
        "yenileme_tipi": "MANUEL",      # MANUEL, OTOMATIK
        "lisans_tipi": "YILLIK",        # PERPETUAL, YILLIK, AYLIK
        "bedel": 0.0,
        "para_birimi": "TRY",
        "kdv_dahil": False,
        "odeme_periyodu": "YILLIK",     # TEK, AYLIK, YILLIK
        "kullanici_limiti": 0,
        "ek_kullanici_ucreti": 0.0,
        "imza_pdf_path": "",
        "notlar": ""
    },

    "bakim": {
        "var": True,
        "aylik_ucret": 0.0,
        "sonraki_fatura_tarihi": "",
        "bitis_tarihi": "",
        "yanit_suresi_saat": 4,
        "cozum_suresi_saat": 24,
        "destek_7_24": False
    },

    "kurulum": {
        "tip": "ON_PREM",               # ON_PREM, CLOUD
        "sql_surumu": "",
        "nexor_versiyonu": "",
        "son_guncelleme_tarihi": ""
    },

    "belgeler": [],   # her kayit: {tip, dosya_yolu, eklenme_tarihi, aciklama}

    "raporlama": {
        "sorumlu_personel": "",
        "etiketler": [],
        "kazanim_kanali": "",
        "ilk_satis_tarihi": "",
        "son_yenileme_tarihi": ""
    },

    # Modul lisanslari (musteri bazli override).
    # Anahtar: modul_kodu, deger: {aktif: bool, bitis_tarihi: 'YYYY-MM-DD', notlar: str}
    # Bos dict = tum moduller default (DB seed durumunda).
    "moduller_aktif": {},

    # NAS sunucu + paylasim yollari (her musteri farkli sunucuda olabilir)
    # `server` UNC adi (ornek: "AtlasNAS" -> \\AtlasNAS\..., ya da IP "192.168.10.50")
    # `shares` her ozel klasor icin paylasim+alt yol (sunucudan sonraki kisim).
    # Yol bos birakilirsa o ozellik calismaz; UI bunu uyarir.
    "nas": {
        "server": "AtlasNAS",
        "shares": {
            "mamul_resim":  "Data Yönetimi/MAMUL_RESIM",
            "urunler":      "Data Yönetimi/Urunler",
            "kimyasallar":  "Data Yönetimi/Kimyasallar",
            "logo":         "Data Yönetimi/LOGO/atlas_logo.png",
            "tds":          "Data Yönetimi/TDS_Dokumanlari",
            "aksiyonlar":   "Data Yönetimi/Aksiyonlar",
            "kalite":       "Kalite",
            "update_server":"Atmo_Logic",
            "personel":     "Personel"
        }
    },

    # M2.1 - Aktivite/Notlar timeline (Chatter mantigi)
    # Her kayit: {zaman, tip, baslik, icerik, kullanici, ek_dosyalar:[path, ...]}
    # tip: NOT, ARAMA, ZIYARET, MAIL, EGITIM, KURULUM, DESTEK, ANLASMA, DIGER
    "aktiviteler": [],

    # M2.2 - Destek gecmisi
    # ozet: KPI snapshot (ortalama yanit/cozum, memnuniyet)
    # ticketlar: [{no, tarih, baslik, durum, oncelik, yanit_dk, cozum_dk, memnuniyet_1_5, aciklama}]
    "destek": {
        "ozet": {
            "son_ziyaret_tarihi": "",
            "memnuniyet_skoru": 0.0,
            "ortalama_yanit_dk": 0,
            "ortalama_cozum_dk": 0
        },
        "ticketlar": []
    },

    # M2.3 - Finansal bilgiler
    # bankalar: [{banka_adi, sube, hesap_no, iban, para_birimi}]
    "finansal": {
        "zirve_cari_kodu": "",
        "cari_bakiye": 0.0,
        "kredi_limiti": 0.0,
        "vade_gun": 30,
        "risk_skoru": "",
        "para_birimi": "TRY",
        "son_odeme_tarihi": "",
        "son_odeme_tutari": 0.0,
        "notlar": "",
        "bankalar": []
    },

    # M2.5 - Audit log
    # Her kayit: {zaman, kullanici, alan, eski, yeni, kategori}
    # kategori: ANLASMA, BAKIM, LISANS, ILETISIM, DB, DIGER
    "audit_log": []
}

# Varsayilan ayarlar (yeni sema - profil destekli)
DEFAULT_CONFIG = {
    "version": "2.0",
    "created_date": None,
    "modified_date": None,

    # Aktif profil ismi (profiles dict'inde anahtar olarak bulunmali)
    "active_profile": "default",

    # Profil tanimlari (musteri/ortam bazli)
    "profiles": {
        "default": dict(DEFAULT_PROFILE)
    },

    # ---- Global (profilden bagimsiz) ayarlar ----
    "application": {
        "theme": "dark",
        "language": "tr_TR",
        "auto_update": True,
        "update_server": "",
        "log_level": "INFO"
    }
}


# =============================================================================
# SIFRE ENCODING (Basit Obfuscation)
# =============================================================================

def encode_password(password: str) -> str:
    """Sifreyi base64 ile encode et (basit obfuscation)"""
    if not password:
        return ""
    try:
        return base64.b64encode(password.encode('utf-8')).decode('utf-8')
    except Exception:
        return ""


def decode_password(encoded: str) -> str:
    """Base64 encoded sifreyi decode et"""
    if not encoded:
        return ""
    try:
        return base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
    except Exception:
        return ""


# =============================================================================
# CONFIG MANAGER
# =============================================================================

class ExternalConfigManager:
    """
    Harici Config Yoneticisi
    
    Kullanim:
        from core.external_config import config_manager
        
        # Ayar okuma
        server = config_manager.get('database.server')
        
        # Ayar yazma
        config_manager.set('database.server', 'localhost\\SQLEXPRESS')
        config_manager.save()
        
        # Baglanti bilgileri
        db_config = config_manager.get_db_config()
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._config: Dict[str, Any] = {}
        self._is_loaded = False
        self._config_exists = False
        
        # Dizinleri olustur
        self._ensure_directories()
        
        # Config'i yukle
        self._load()
    
    def _ensure_directories(self) -> None:
        """Gerekli dizinleri olustur"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Dizin olusturma hatasi: {e}")
    
    def _load(self) -> bool:
        """Config dosyasini yukle ve gerekirse v1.0 -> v2.0 migrate et."""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                self._is_loaded = True
                self._config_exists = True
                logger.info(f"Config yuklendi: {CONFIG_FILE}")
                # Eski formatsa profil yapisina gec ve dosyayi gunelle
                self._migrate_to_profiles()
                return True
            else:
                # Varsayilan config
                import copy
                self._config = copy.deepcopy(DEFAULT_CONFIG)
                self._config['created_date'] = datetime.now().isoformat()
                self._is_loaded = True
                self._config_exists = False
                logger.warning(f"Config dosyasi bulunamadi: {CONFIG_FILE}")
                return False

        except json.JSONDecodeError as e:
            logger.error(f"Config JSON hatasi: {e}")
            import copy
            self._config = copy.deepcopy(DEFAULT_CONFIG)
            self._is_loaded = True
            self._config_exists = False
            return False

        except Exception as e:
            logger.error(f"Config yukleme hatasi: {e}")
            import copy
            self._config = copy.deepcopy(DEFAULT_CONFIG)
            self._is_loaded = True
            self._config_exists = False
            return False

    def _migrate_to_profiles(self) -> None:
        """v1.0 (top-level database/pdks/...) -> v2.0 (profiles[atmo].* + active_profile).

        Idempotent: yeni format zaten varsa hicbir sey yapmaz. Migration sonrasi
        config dosyasini diske yazar (eski format kayit kalmaz).
        """
        if 'profiles' in self._config and 'active_profile' in self._config:
            # Yeni format - ama yine de yeni eklenen profil-spesifik alanlari kontrol et
            self._migrate_top_level_to_active_profile()
            return  # Zaten yeni format

        logger.info("Config v1.0 -> v2.0 migrate ediliyor (atmo profil olusturuluyor)")
        old = self._config

        atmo_profile = {
            "musteri_kodu": "atmo",
            "musteri_adi": (old.get('company') or {}).get('name', '') or "Atmo",
            "udl_path": old.get('udl_path', ''),
            "database": old.get('database') or dict(DEFAULT_PROFILE['database']),
            "plc_database": old.get('plc_database') or dict(DEFAULT_PROFILE['plc_database']),
            "pdks": old.get('pdks') or dict(DEFAULT_PROFILE['pdks']),
            "company": old.get('company') or dict(DEFAULT_PROFILE['company']),
        }

        new_config = {
            "version": "2.0",
            "created_date": old.get('created_date'),
            "modified_date": datetime.now().isoformat(),
            "active_profile": "atmo",
            "profiles": {"atmo": atmo_profile},
        }
        # Global anahtarlari kopyala (profil-spesifik olmayan her sey)
        for key, value in old.items():
            if key in {'version', 'created_date', 'modified_date',
                       'active_profile', 'profiles', 'udl_path',
                       'database', 'plc_database', 'pdks', 'company',
                       'musteri_kodu', 'musteri_adi'}:
                continue
            new_config[key] = value

        self._config = new_config

        # Yeni format diske kaydet (eski format silinsin)
        try:
            self.save()
            logger.info("Config v2.0 olarak kaydedildi (profil: atmo)")
        except Exception as e:
            logger.error(f"Config v2.0 kaydetme hatasi: {e}")

    def _migrate_top_level_to_active_profile(self) -> None:
        """v2.0 sonrasi yeni eklenen profil-spesifik alanlari (ornek: 'nas')
        eski global'den aktif profile'a tasi. Idempotent.
        """
        active = self._config.get('active_profile')
        profiles = self._config.get('profiles') or {}
        if not active or active not in profiles:
            return

        profile = profiles[active]
        degisti = False
        for key in _PROFILE_KEYS:
            if key in self._config and key not in profile:
                logger.info("[CONFIG MIGRATE] '%s' top-level -> profiles.%s'a tasiniyor", key, active)
                profile[key] = self._config.pop(key)
                degisti = True

        if degisti:
            try:
                self.save()
            except Exception as e:
                logger.error(f"Top-level migration kaydetme hatasi: {e}")
    
    def save(self) -> bool:
        """Config dosyasini kaydet"""
        try:
            print(f"[CONFIG] Kaydediliyor: {CONFIG_FILE}")
            
            # Dizin yoksa oluştur
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            
            # Yedek al
            if CONFIG_FILE.exists():
                self._backup_config()
            
            # Guncelleme tarihi
            self._config['modified_date'] = datetime.now().isoformat()
            if not self._config.get('created_date'):
                self._config['created_date'] = self._config['modified_date']
            
            # Kaydet
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)

            self._config_exists = True
            print(f"[CONFIG] [OK] Kaydedildi: {CONFIG_FILE}")
            logger.info(f"Config kaydedildi: {CONFIG_FILE}")
            return True

        except Exception as e:
            print(f"[CONFIG] [HATA] Kaydetme hatasi: {e}")
            logger.error(f"Config kaydetme hatasi: {e}")
            return False
    
    def _backup_config(self) -> None:
        """Config yedegi al"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = CONFIG_BACKUP_DIR / f"config_{timestamp}.json"
            shutil.copy2(CONFIG_FILE, backup_file)
            
            # Eski yedekleri temizle (son 10 tane kalsin)
            backups = sorted(CONFIG_BACKUP_DIR.glob("config_*.json"))
            for old_backup in backups[:-10]:
                old_backup.unlink()
                
        except Exception as e:
            logger.error(f"Yedekleme hatasi: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Ayar degeri al (noktali notasyon destekli).

        Profil-spesifik anahtarlar (database, plc_database, pdks, udl_path,
        company, musteri_*) otomatik olarak aktif profilden okunur.

        Ornek:
            config_manager.get('database.server')   -> profiles[active].database.server
            config_manager.get('application.theme') -> top-level application.theme
        """
        parts = key.split('.')
        first = parts[0] if parts else ''

        if first in _PROFILE_KEYS:
            profile = self._active_profile_dict()
            try:
                value = profile
                for part in parts:
                    value = value[part]
                return value
            except (KeyError, TypeError):
                return default

        try:
            value = self._config
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Ayar degeri yaz (noktali notasyon destekli).

        Profil-spesifik anahtarlar otomatik olarak aktif profile yazilir.

        Ornek:
            config_manager.set('database.server', 'localhost\\SQLEXPRESS')
            config_manager.set('application.theme', 'dark')
        """
        parts = key.split('.')
        first = parts[0] if parts else ''

        if first in _PROFILE_KEYS:
            target = self._active_profile_dict(create=True)
        else:
            target = self._config

        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value

    # ---------- Profil yardimcilari ----------

    def _active_profile_dict(self, create: bool = False) -> Dict[str, Any]:
        """Aktif profilin dict referansini dondur. create=True ise yoksa olusturur."""
        active = self._config.get('active_profile') or 'default'
        profiles = self._config.get('profiles')
        if not isinstance(profiles, dict):
            if not create:
                return {}
            profiles = {}
            self._config['profiles'] = profiles
        if active not in profiles:
            if not create:
                return {}
            import copy
            profiles[active] = copy.deepcopy(DEFAULT_PROFILE)
        return profiles[active]

    def get_active_profile(self) -> str:
        """Aktif profil ismini dondur."""
        return self._config.get('active_profile') or 'default'

    def set_active_profile(self, name: str) -> bool:
        """Aktif profili degistir (profilin var oldugunu varsayar). Save edilir."""
        profiles = self._config.get('profiles') or {}
        if name not in profiles:
            logger.error(f"Profil bulunamadi: {name}")
            return False
        self._config['active_profile'] = name
        return self.save()

    def list_profiles(self) -> list:
        """Mevcut profil isimleri (alfabetik)."""
        profiles = self._config.get('profiles') or {}
        return sorted(profiles.keys())

    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Verilen profil dict'ini dondur (yoksa None)."""
        profiles = self._config.get('profiles') or {}
        return profiles.get(name)

    def add_profile(self, name: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Yeni profil ekle. Mevcutsa False doner. Save edilir."""
        profiles = self._config.setdefault('profiles', {})
        if name in profiles:
            logger.error(f"Profil zaten var: {name}")
            return False
        import copy
        new_profile = copy.deepcopy(DEFAULT_PROFILE)
        new_profile['musteri_kodu'] = name
        if data:
            new_profile.update(data)
        profiles[name] = new_profile
        return self.save()

    def remove_profile(self, name: str) -> bool:
        """Profili sil. Aktif profil ise veya tek profil ise False doner."""
        profiles = self._config.get('profiles') or {}
        if name not in profiles:
            return False
        if name == self.get_active_profile():
            logger.error(f"Aktif profil silinemez: {name}")
            return False
        if len(profiles) <= 1:
            logger.error("Son profil silinemez")
            return False
        profiles.pop(name)
        return self.save()
    
    def config_exists(self) -> bool:
        """Config dosyasi mevcut mu?"""
        return self._config_exists
    
    def needs_setup(self) -> bool:
        """Ilk kurulum gerekli mi?"""
        # UDL dosyasi varsa kuruluma gerek yok
        if _UDL_FILE and parse_udl_file(_UDL_FILE):
            return False

        if not self._config_exists:
            return True

        # Veritabani ayarlari bos mu? (aktif profilden)
        db_config = self._active_profile_dict().get('database', {}) or {}
        if not db_config.get('server') or not db_config.get('database'):
            return True

        return False

    def get_db_config(self) -> Dict[str, Any]:
        """
        Veritabani baglanti ayarlarini dondur (aktif profil + UDL override).
        (database_manager.py ile uyumlu format)

        Oncelik sirasi:
            1. Nexor.UDL dosyasi (masaustu / uygulama dizini / C:/NEXOR)
            2. config.json -> profiles[active_profile].database
        """
        db = self._active_profile_dict().get('database', {}) or {}

        config = {
            'server': db.get('server', ''),
            'database': db.get('database', ''),
            'driver': db.get('driver', 'ODBC Driver 18 for SQL Server'),
            'timeout': db.get('timeout', 10),
            'max_connections': db.get('max_connections', 20),
            'trusted_connection': db.get('trusted_connection', False)
        }

        if not config['trusted_connection']:
            config['user'] = db.get('user', '')
            config['password'] = decode_password(db.get('password', ''))

        # UDL dosyasi varsa server/database/user/password degerlerini override et
        if _UDL_FILE:
            udl = parse_udl_file(_UDL_FILE)
            if udl:
                config['server'] = udl['server']
                config['database'] = udl['database']
                if udl.get('user'):
                    config['user'] = udl['user']
                    config['password'] = udl.get('password', '')
                    config['trusted_connection'] = False

        return config
    
    def set_db_config(self, server: str, database: str,
                      user: str = '', password: str = '',
                      trusted_connection: bool = False,
                      driver: str = 'ODBC Driver 18 for SQL Server',
                      timeout: int = 10, max_connections: int = 20) -> None:
        """Veritabani baglanti ayarlarini aktif profile yaz."""
        profile = self._active_profile_dict(create=True)
        profile['database'] = {
            'server': server,
            'database': database,
            'user': user if not trusted_connection else '',
            'password': encode_password(password) if not trusted_connection else '',
            'driver': driver,
            'timeout': timeout,
            'max_connections': max_connections,
            'trusted_connection': trusted_connection
        }

    def get_plc_config(self) -> Optional[Dict[str, Any]]:
        """PLC veritabani ayarlarini dondur (aktif profilden)."""
        plc = self._active_profile_dict().get('plc_database', {}) or {}

        if not plc.get('enabled', False):
            return None

        return {
            'server': plc.get('server', ''),
            'database': plc.get('database', ''),
            'user': plc.get('user', ''),
            'password': decode_password(plc.get('password', '')),
            'driver': plc.get('driver', 'ODBC Driver 18 for SQL Server'),
            'timeout': plc.get('timeout', 5),
            'max_connections': plc.get('max_connections', 5)
        }

    def set_plc_config(self, enabled: bool, server: str = '',
                       database: str = '', user: str = '',
                       password: str = '', **kwargs) -> None:
        """PLC veritabani ayarlarini aktif profile yaz."""
        profile = self._active_profile_dict(create=True)
        profile['plc_database'] = {
            'enabled': enabled,
            'server': server,
            'database': database,
            'user': user,
            'password': encode_password(password),
            'driver': kwargs.get('driver', 'ODBC Driver 18 for SQL Server'),
            'timeout': kwargs.get('timeout', 5),
            'max_connections': kwargs.get('max_connections', 5)
        }

    def get_app_config(self) -> Dict[str, Any]:
        """Uygulama ayarlarini dondur (global)."""
        return self._config.get('application', {})

    def get_pdks_config(self) -> Dict[str, Any]:
        """PDKS ayarlarini dondur (aktif profilden)."""
        return self._active_profile_dict().get('pdks', {}) or {}
    
    def get_connection_string(self, for_plc: bool = False) -> str:
        """
        ODBC connection string olustur
        """
        if for_plc:
            config = self.get_plc_config()
            if not config:
                raise ValueError("PLC veritabani devre disi")
        else:
            config = self.get_db_config()
        
        if config.get('trusted_connection'):
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                "Trusted_Connection=yes;"
                "Encrypt=no;TrustServerCertificate=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"UID={config['user']};"
                f"PWD={config['password']};"
                "Encrypt=no;TrustServerCertificate=yes;"
            )
        
        return conn_str
    
    def test_connection(self, for_plc: bool = False) -> Tuple[bool, str]:
        """
        Veritabani baglantisini test et
        
        Returns:
            (success: bool, message: str)
        """
        try:
            import pyodbc
            
            conn_str = self.get_connection_string(for_plc)
            config = self.get_plc_config() if for_plc else self.get_db_config()
            
            conn = pyodbc.connect(conn_str, timeout=config.get('timeout', 10))
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            db_name = "PLC" if for_plc else "ERP"
            return True, f"{db_name} baglantisi basarili!"
            
        except Exception as e:
            return False, f"Baglanti hatasi: {str(e)}"
    
    def get_nas_server(self) -> str:
        """NAS sunucu adresini dondur"""
        return self.get('nas.server', 'AtlasNAS')

    def set_nas_server(self, server: str) -> None:
        """NAS sunucu adresini ayarla"""
        self.set('nas.server', server)

    def get_nas_path(self, share: str, *sub_paths: str) -> str:
        """
        NAS paylasim yolunu olustur

        Ornek:
            get_nas_path('Data Yönetimi', 'MAMUL_RESIM')
            -> r'\\\\AtlasNAS\\Data Yönetimi\\MAMUL_RESIM'
        """
        server = self.get_nas_server()
        parts = [rf"\\{server}\{share}"] + list(sub_paths)
        return os.path.join(*parts)

    def get_full_config(self) -> Dict[str, Any]:
        """Tum config'i dondur (debug icin)"""
        return self._config.copy()
    
    def reset_to_defaults(self) -> None:
        """Varsayilan ayarlara don"""
        import copy
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self._config['created_date'] = datetime.now().isoformat()
    
    def reload(self) -> bool:
        """Config'i yeniden yukle"""
        self._is_loaded = False
        return self._load()


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

config_manager = ExternalConfigManager()


# =============================================================================
# YARDIMCI FONKSIYONLAR (Geriye Uyumluluk)
# =============================================================================

def get_db_config() -> Dict[str, Any]:
    """Geriye uyumlu: DB config dondur"""
    return config_manager.get_db_config()


def get_connection_string() -> str:
    """Geriye uyumlu: Connection string dondur"""
    return config_manager.get_connection_string()


def needs_setup() -> bool:
    """Ilk kurulum gerekli mi?"""
    return config_manager.needs_setup()


# =============================================================================
# TEST
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("EXTERNAL CONFIG MANAGER - TEST")
    print("=" * 60)
    
    print(f"\nConfig dosyasi: {CONFIG_FILE}")
    print(f"Config mevcut: {config_manager.config_exists()}")
    print(f"Kurulum gerekli: {config_manager.needs_setup()}")
    
    print("\n--- Veritabani Ayarlari ---")
    db = config_manager.get_db_config()
    print(f"Server: {db.get('server')}")
    print(f"Database: {db.get('database')}")
    print(f"Driver: {db.get('driver')}")
    
    print("\n--- Baglanti Testi ---")
    success, message = config_manager.test_connection()
    print(f"Sonuc: {'OK' if success else 'FAIL'} {message}")
    
    print("\n" + "=" * 60)
