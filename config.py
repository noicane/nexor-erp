# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Konfigürasyon
Veritabanı ayarları ve uygulama sabitleri
Enterprise Resource Planning System

NOT: Bu tek merkezi config dosyasıdır.
     - config_updated.py (SİLİNDİ - buraya birleştirildi)
     - core/config.py (SİLİNDİ - buraya birleştirildi)
"""
import sys
from pathlib import Path


# =========================
# EXE / FROZEN MOD DESTEĞİ
# =========================
def get_base_path() -> Path:
    """
    Uygulamanın çalıştığı temel dizini döndürür.
    EXE modunda executable dizini, geliştirme modunda proje dizini.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def get_resource_path(relative_path: str) -> Path:
    """
    Kaynak dosyalarına erişim için yol döndürür.
    EXE modunda _MEIPASS, normal modda proje dizini kullanılır.
    """
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    return base_path / relative_path


def is_frozen() -> bool:
    """EXE olarak çalışıp çalışmadığını kontrol eder"""
    return getattr(sys, 'frozen', False)


# Temel dizinler
BASE_DIR = get_base_path()

# Debug modu - EXE'de kapalı, geliştirmede açık
DEBUG_MODE = not is_frozen()

# =========================
# UDL DOSYASINDAN BAGLANTI OKUMA
# =========================
def _read_nexor_udl():
    """Nexor.UDL dosyasindan baglanti bilgilerini oku"""
    import json as _json

    # config.json'dan udl_path oku
    # One-file EXE modunda _MEIPASS'i de kontrol et
    _udl_paths = []
    _cfg_candidates = [BASE_DIR / "config.json"]
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        _cfg_candidates.append(Path(sys._MEIPASS) / "config.json")

    for _cfg_file in _cfg_candidates:
        try:
            if _cfg_file.exists():
                with open(_cfg_file, 'r', encoding='utf-8') as _f:
                    _udl_custom = _json.load(_f).get('udl_path', '')
                if _udl_custom:
                    _udl_paths.append(Path(_udl_custom))
                break
        except Exception:
            pass

    _udl_paths += [
        BASE_DIR / "Nexor.UDL",
    ]
    # One-file EXE modunda _MEIPASS'teki UDL'yi de kontrol et
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        _udl_paths.append(Path(sys._MEIPASS) / "Nexor.UDL")
    _udl_paths.append(Path("C:/NEXOR/Nexor.UDL"))
    for _p in _udl_paths:
        if not _p.exists():
            continue
        try:
            try:
                _content = _p.read_text(encoding='utf-16')
            except (UnicodeError, UnicodeDecodeError):
                _content = _p.read_text(encoding='utf-8')
            for _line in _content.splitlines():
                _line = _line.strip()
                if not _line or _line.startswith('[') or _line.startswith(';'):
                    continue
                _params = {}
                for _part in _line.split(';'):
                    if '=' in _part:
                        _k, _v = _part.split('=', 1)
                        _params[_k.strip().lower()] = _v.strip()
                _srv = _params.get('data source', '')
                _db = _params.get('initial catalog', '')
                if _srv and _db:
                    return {'server': _srv, 'database': _db,
                            'user': _params.get('user id', ''),
                            'password': _params.get('password', '')}
        except Exception:
            continue
    return None

_UDL_DATA = _read_nexor_udl()

# =========================
# VERİTABANI AYARLARI
# =========================
# Öncelik: 1) UDL dosyası  2) external_config (config.json)  3) Varsayılan (boş)
# NOT: Hardcoded şifreler kaynak kodda OLMAMALIDIR.
#      Bağlantı bilgileri Nexor.UDL veya config.json'dan gelir.

def _load_db_config():
    """DB config'ini güvenli kaynaklardan yükle"""
    # 1. UDL'den geldi mi?
    if _UDL_DATA:
        return {
            "server": _UDL_DATA['server'],
            "database": _UDL_DATA['database'],
            "user": _UDL_DATA.get('user', ''),
            "password": _UDL_DATA.get('password', ''),
            "driver": "ODBC Driver 18 for SQL Server",
            "timeout": 10,
            "autocommit": False,
            "trusted_connection": False
        }

    # 2. external_config'den oku
    try:
        from core.external_config import config_manager as _ext_cfg
        _db = _ext_cfg.get_db_config()
        if _db and _db.get('server'):
            return {
                "server": _db['server'],
                "database": _db['database'],
                "user": _db.get('user', ''),
                "password": _db.get('password', ''),
                "driver": _db.get('driver', 'ODBC Driver 18 for SQL Server'),
                "timeout": _db.get('timeout', 10),
                "autocommit": False,
                "trusted_connection": _db.get('trusted_connection', False)
            }
    except Exception:
        pass

    # 3. Varsayılan (kurulum gerekli)
    print("[CONFIG] UYARI: Veritabanı ayarları bulunamadı! Kurulum wizard'ı açılacak.")
    return {
        "server": "",
        "database": "",
        "user": "",
        "password": "",
        "driver": "ODBC Driver 18 for SQL Server",
        "timeout": 10,
        "autocommit": False,
        "trusted_connection": False
    }


def _load_plc_config():
    """PLC config'ini güvenli kaynaklardan yükle"""
    try:
        from core.external_config import config_manager as _ext_cfg
        _plc = _ext_cfg.get_plc_config()
        if _plc:
            return _plc
    except Exception:
        pass

    # UDL'den ana sunucu bilgisini al, PLC DB adını kullan
    if _UDL_DATA:
        return {
            "server": _UDL_DATA['server'],
            "database": "PLC_Database",
            "user": _UDL_DATA.get('user', ''),
            "password": _UDL_DATA.get('password', ''),
            "driver": "ODBC Driver 18 for SQL Server",
            "timeout": 5
        }

    return {
        "server": "", "database": "", "user": "", "password": "",
        "driver": "ODBC Driver 18 for SQL Server", "timeout": 5
    }


DB_CONFIG = _load_db_config()
PLC_DB_CONFIG = _load_plc_config()

if _UDL_DATA:
    print(f"[CONFIG] UDL'den yuklendi: {_UDL_DATA['server']} / {_UDL_DATA['database']}")
elif DB_CONFIG.get('server'):
    print(f"[CONFIG] Config'den yuklendi: {DB_CONFIG['server']} / {DB_CONFIG['database']}")
else:
    print("[CONFIG] Veritabanı ayarları henüz yapılandırılmamış.")

# =========================
# NAS YOLLARI (config.json aktif profilinden yuklenir)
# =========================
# Profil'deki nas.shares anahtar -> alias eslesmesi (geriye uyum):
#   profile_key  -> NAS_PATHS_legacy_alias
_NAS_SHARE_ALIAS = {
    "mamul_resim":   "image_path",
    "urunler":       "product_path",
    "kimyasallar":   "chemical_path",
    "logo":          "logo_path",
    "tds":           "tds_path",
    "aksiyonlar":    "aksiyon_path",
    "kalite":        "quality_path",
    "update_server": "update_server",
    "personel":      "personel_path",
}

def _load_nas_paths():
    """NAS yollarini aktif profilden yukle. Her musterinin kendi sunucusu/yollari olabilir."""
    server = "AtlasNAS"
    shares: dict = {}
    try:
        from core.external_config import config_manager
        server = config_manager.get('nas.server', 'AtlasNAS') or 'AtlasNAS'
        shares = config_manager.get('nas.shares') or {}
    except Exception:
        pass

    # Varsayilanlar (profile'da bulunmayan key'ler icin fallback)
    defaults = {
        "mamul_resim":   "Data Yönetimi/MAMUL_RESIM",
        "urunler":       "Data Yönetimi/Urunler",
        "kimyasallar":   "Data Yönetimi/Kimyasallar",
        "logo":          "Data Yönetimi/LOGO/atlas_logo.png",
        "tds":           "Data Yönetimi/TDS_Dokumanlari",
        "aksiyonlar":    "Data Yönetimi/Aksiyonlar",
        "kalite":        "Kalite",
        "update_server": "Atmo_Logic",
        "personel":      "Personel",
    }

    out = {}
    for key, alias in _NAS_SHARE_ALIAS.items():
        sub = (shares.get(key) or defaults[key]).replace('/', '\\')
        out[alias] = rf"\\{server}\{sub}"
    return out

NAS_PATHS = _load_nas_paths()

# =========================
# UYGULAMA AYARLARI
# =========================
APP_NAME = "Redline Nexor ERP"
APP_VERSION = "1.0.0"
APP_COMPANY = "Redline Creative Solutions"
APP_TAGLINE = "Enterprise Resource Planning"
APP_COPYRIGHT = "© 2026 Redline Creative Solutions"

# Ayar dosyası konumu
SETTINGS_FILE = Path.home() / ".redline_nexor" / "settings.json"

# =========================
# KURUMSAL KİMLİK
# =========================
BRAND_COLORS = {
    "primary": "#E2130D",           # Redline Red
    "primary_dark": "#C20F0A",
    "primary_light": "#F5160E",
    "secondary": "#000000",          # Deep Black
    "accent": "#2D3748",            # Dark Gray
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#E2130D",
    "info": "#3B82F6"
}

# Logo dosya yolları
LOGO_FILES = {
    "web": "assets/logo_web.png",           # 800x533
    "sidebar": "assets/logo_sidebar.png",   # 400x267
    "login": "assets/logo_login.png",       # 320x213
    "small": "assets/logo_small.png",       # 200x133
    "icon": "assets/icon.ico",              # 64x64
    "favicon": "assets/favicon.png"         # 64x64
}

# =========================
# TEMA AYARLARI
# =========================
DEFAULT_THEME_MODE = "dark"      # "dark" veya "light"
DEFAULT_THEME_COLOR = "nexor"    # "nexor", "executive", "silver", "energy", "ocean"

# =========================
# SAYFALAMA VE GÖRÜNÜM
# =========================
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
MIN_PAGE_SIZE = 10

# Tablo ayarları
TABLE_ROW_HEIGHT = 32
TABLE_HEADER_HEIGHT = 40

# =========================
# GÜVENLİK AYARLARI
# =========================
# Şifre kuralları
PASSWORD_MIN_LENGTH = 6
PASSWORD_REQUIRE_UPPERCASE = False
PASSWORD_REQUIRE_LOWERCASE = False
PASSWORD_REQUIRE_NUMBERS = False
PASSWORD_REQUIRE_SPECIAL = False

# Oturum ayarları
SESSION_TIMEOUT_MINUTES = 480    # 8 saat
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION = 30    # dakika

# =========================
# LOG AYARLARI
# =========================
LOG_LEVEL = "INFO"               # "DEBUG", "INFO", "WARNING", "ERROR"
LOG_TO_FILE = True
LOG_TO_DATABASE = True
LOG_FILE_PATH = Path.home() / ".redline_nexor" / "logs"
LOG_RETENTION_DAYS = 90

# =========================
# PERFORMANS AYARLARI
# =========================
# Cache
ENABLE_CACHE = True
CACHE_TIMEOUT = 300              # saniye

# Veritabanı connection pool
DB_POOL_SIZE = 5
DB_POOL_MAX_OVERFLOW = 10

# =========================
# MODÜL AYARLARI
# =========================
# Aktif modüller
MODULES = {
    "stok": True,
    "uretim": True,
    "kalite": True,
    "bakim": True,
    "ik": True,
    "satinalma": True,
    "sevkiyat": True,
    "cevre": True,
    "isg": True,
    "sistem": True
}

# =========================
# RAPOR AYARLARI
# =========================
REPORT_OUTPUT_DIR = Path.home() / "Documents" / "Nexor Raporlar"
REPORT_FORMATS = ["PDF", "XLSX", "CSV"]
DEFAULT_REPORT_FORMAT = "PDF"

# =========================
# YEDEKLEME AYARLARI
# =========================
BACKUP_DIR = Path.home() / ".redline_nexor" / "backups"
AUTO_BACKUP_ENABLED = False
AUTO_BACKUP_INTERVAL_DAYS = 7

# =========================
# E-POSTA AYARLARI (Opsiyonel)
# =========================
EMAIL_ENABLED = False
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USERNAME = ""
EMAIL_PASSWORD = ""
EMAIL_FROM = "noreply@redlinenexor.com"

# =========================
# API AYARLARI (Opsiyonel)
# =========================
API_ENABLED = False
API_HOST = "0.0.0.0"
API_PORT = 8000
API_DEBUG = False

# =========================
# PDKS AYARLARI
# =========================
PDKS_ENABLED = True
PDKS_POLL_INTERVAL = 10          # saniye
PDKS_DEVICE_IP = "192.168.1.100"
PDKS_DEVICE_PORT = 4370

# =========================
# RFID KART OKUYUCU AYARLARI
# =========================
RFID_LOGIN_ENABLED = True
RFID_KEYSTROKE_TIMEOUT_MS = 150   # Tuş vuruşları arası max süre (ms) - kart vs insan ayırt eder
RFID_MIN_CARD_LENGTH = 4          # Minimum kart ID uzunluğu
RFID_MAX_CARD_LENGTH = 20         # Maksimum kart ID uzunluğu
RFID_BUFFER_RESET_MS = 300        # Buffer sıfırlama süresi (ms)

# =========================
# PLC AYARLARI
# =========================
PLC_SYNC_ENABLED = True
PLC_SYNC_INTERVAL = 5            # saniye
PLC_CONNECTION_TIMEOUT = 3

# =========================
# DİĞER AYARLAR
# =========================
# Varsayılan dil
DEFAULT_LANGUAGE = "tr_TR"

# Tarih formatı
DATE_FORMAT = "%d.%m.%Y"
DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"

# Para birimi
DEFAULT_CURRENCY = "TRY"
CURRENCY_SYMBOL = "₺"

# Ondalık ayracı
DECIMAL_SEPARATOR = ","
THOUSAND_SEPARATOR = "."

# Telefon formatı
PHONE_FORMAT = "(XXX) XXX XX XX"

# =========================
# GELİŞTİRİCİ AYARLARI
# =========================
# DEBUG_MODE yukarıda is_frozen() ile belirleniyor
SHOW_SQL_QUERIES = False
ENABLE_HOT_RELOAD = False

# =========================
# DESTEK BİLGİLERİ
# =========================
SUPPORT_EMAIL = "support@redlinecreative.com"
SUPPORT_PHONE = "+90 XXX XXX XX XX"
SUPPORT_URL = "https://redlinenexor.com/support"
DOCUMENTATION_URL = "https://docs.redlinenexor.com"

# =========================
# LİSANS BİLGİLERİ
# =========================
LICENSE_TYPE = "Enterprise"      # "Trial", "Standard", "Professional", "Enterprise"
LICENSE_KEY = ""                 # Buraya lisans anahtarınızı girin
LICENSE_EXPIRY = None            # None = Sınırsız

# =========================
# ÖZEL AYARLAR
# =========================
# Özel ayarlarınızı buraya ekleyebilirsiniz
CUSTOM_SETTINGS = {}


# =========================
# YARDIMCI FONKSİYONLAR
# =========================
def get_db_connection_string() -> str:
    """
    Veritabanı bağlantı string'ini oluşturur
    """
    return (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['user']};"
        f"PWD={DB_CONFIG['password']};"
        f"TrustServerCertificate=yes;"
    )


def get_logo_path(logo_type: str = "login") -> Path:
    """
    Logo dosya yolunu döndürür
    
    Args:
        logo_type: "web", "sidebar", "login", "small", "icon", "favicon"
    
    Returns:
        Path: Logo dosya yolu
    """
    from pathlib import Path
    import sys
    
    if getattr(sys, 'frozen', False):
        # PyInstaller ile paketlenmiş
        base_path = Path(sys._MEIPASS)
    else:
        # Development modu
        base_path = Path(__file__).parent
    
    logo_file = LOGO_FILES.get(logo_type, LOGO_FILES["login"])
    return base_path / logo_file


def ensure_directories():
    """
    Gerekli dizinleri oluşturur
    """
    directories = [
        SETTINGS_FILE.parent,
        LOG_FILE_PATH,
        REPORT_OUTPUT_DIR,
        BACKUP_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_app_title() -> str:
    """
    Uygulama başlığını döndürür
    """
    return f"{APP_NAME} v{APP_VERSION}"


def get_full_app_info() -> dict:
    """
    Tam uygulama bilgilerini döndürür
    """
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "company": APP_COMPANY,
        "tagline": APP_TAGLINE,
        "copyright": APP_COPYRIGHT,
        "license": LICENSE_TYPE
    }


# =========================
# BAŞLANGIÇ
# =========================
# Gerekli dizinleri oluştur
ensure_directories()

# =========================
# NOTLAR
# =========================
"""
REDLINE NEXOR ERP - Konfigürasyon Notları

1. VERİTABANI:
   - SQL Server bağlantısı kullanılıyor
   - Connection pooling etkin
   - Timeout: 10 saniye

2. TEMA:
   - Varsayılan: Corporate Dark (Nexor)
   - 5 farklı renk paleti mevcut
   - Kullanıcı özelleştirilebilir

3. GÜVENLİK:
   - Şifre şifreleme: SHA256 + bcrypt
   - Oturum timeout: 8 saat
   - Max login denemesi: 5

4. PERFORMANS:
   - Cache aktif
   - Connection pool: 5-15 bağlantı
   - Sayfalama: 50 kayıt

5. MODÜLLER:
   - Tüm modüller varsayılan aktif
   - config.py'den kolayca açılıp kapatılabilir

6. DESTEK:
   - Email: support@redlinecreative.com
   - Docs: https://docs.redlinenexor.com

© 2026 Redline Creative Solutions
"""
