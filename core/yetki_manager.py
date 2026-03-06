# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Yetki Yönetim Sistemi
Kullanıcı bazlı izin ve menü kontrolü
"""

from core.database import get_db_connection


class YetkiManager:
    """Merkezi yetki yönetim sınıfı"""
    
    _current_user_id = None
    _current_user_role_id = None
    _cached_permissions = set()  # Rol izinleri
    _cached_menu_permissions = set()  # Kullanıcı menü yetkileri
    _cache_loaded = False
    _is_admin = False
    
    @classmethod
    def set_current_user(cls, user_id: int, role_id: int = None):
        """Aktif kullanıcıyı ayarla ve izinleri yükle"""
        cls._current_user_id = user_id
        cls._current_user_role_id = role_id
        cls._cache_loaded = False
        cls._cached_permissions = set()
        cls._cached_menu_permissions = set()
        cls._is_admin = False
        cls._load_permissions()
    
    @classmethod
    def clear(cls):
        """Kullanıcı bilgisini temizle"""
        cls._current_user_id = None
        cls._current_user_role_id = None
        cls._cached_permissions = set()
        cls._cached_menu_permissions = set()
        cls._cache_loaded = False
        cls._is_admin = False
    
    @classmethod
    def _load_permissions(cls):
        """Kullanıcının tüm izinlerini yükle"""
        if cls._cache_loaded or not cls._current_user_id:
            return
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Kullanıcının rol_id'sini ve rol kodunu al
            cursor.execute("""
                SELECT k.rol_id, r.rol_kodu
                FROM sistem.kullanicilar k
                LEFT JOIN sistem.roller r ON k.rol_id = r.id
                WHERE k.id = ?
            """, [cls._current_user_id])
            row = cursor.fetchone()

            if row:
                cls._current_user_role_id = row.rol_id
                # Admin kontrolü
                if row.rol_kodu == 'ADMIN':
                    cls._is_admin = True

            # Rolün izinlerini al
            if cls._current_user_role_id:
                cursor.execute("""
                    SELECT i.kod
                    FROM sistem.rol_izinler ri
                    INNER JOIN sistem.izinler i ON ri.izin_id = i.id
                    WHERE ri.rol_id = ? AND ISNULL(i.aktif_mi, 1) = 1
                """, [cls._current_user_role_id])

                for row in cursor.fetchall():
                    cls._cached_permissions.add(row.kod)

            # Kullanıcının menü yetkilerini al (tablo varsa)
            try:
                cursor.execute("""
                    SELECT menu_id FROM sistem.kullanici_menu_yetkileri WHERE kullanici_id = ?
                """, [cls._current_user_id])

                for row in cursor.fetchall():
                    cls._cached_menu_permissions.add(row.menu_id)
            except:
                # Tablo yoksa sessizce geç
                pass

            cls._cache_loaded = True

            print(f"[YetkiManager] Kullanıcı: {cls._current_user_id}, Admin: {cls._is_admin}")
            print(f"[YetkiManager] {len(cls._cached_permissions)} rol izni, {len(cls._cached_menu_permissions)} menü yetkisi yüklendi")

        except Exception as e:
            print(f"[YetkiManager] İzin yükleme hatası: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    @classmethod
    def can_access_menu(cls, menu_id: str) -> bool:
        """
        Kullanıcı bu menüye erişebilir mi?
        
        Args:
            menu_id: Menü ID'si (örn: 'uretim_anlik', 'depo_stok')
        
        Returns:
            bool: Erişim varsa True
        """
        if not cls._cache_loaded:
            cls._load_permissions()
        
        # Admin her şeye erişebilir
        if cls._is_admin:
            return True
        
        # Dashboard herkes görebilir
        if menu_id == "dashboard":
            return True
        
        # ÖNEMLI: Yetki sistemi aktif değilse (kimsenin menü yetkisi yoksa)
        # tüm kullanıcılara erişim ver (geriye uyumluluk)
        # Ama kullanıcının kendisine özel yetki tanımlanmışsa, sadece o menülere erişebilir
        if len(cls._cached_menu_permissions) == 0:
            # Bu kullanıcının hiç menü yetkisi yok
            # Veritabanını kontrol et: Başka kullanıcıların yetkisi var mı?
            conn = None
            try:
                from core.database import get_db_connection
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sistem.kullanici_menu_yetkileri")
                total_count = cursor.fetchone()[0]

                # Eğer sistemde hiç yetki kaydı yoksa, eski sistem - herkese aç
                if total_count == 0:
                    return True
                # Sistemde yetki kayıtları var ama bu kullanıcıda yok - erişim yok
                else:
                    return False
            except:
                # Tablo yoksa veya hata varsa geriye uyumluluk için aç
                return True
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
        
        return menu_id in cls._cached_menu_permissions
    
    @classmethod
    def has_permission(cls, permission_code: str) -> bool:
        """
        Kullanıcının belirli bir izni var mı kontrol et
        
        Args:
            permission_code: İzin kodu (örn: 'uretim.goruntule', 'kalite.olustur')
        
        Returns:
            bool: İzin varsa True
        """
        if not cls._cache_loaded:
            cls._load_permissions()
        
        # Admin her şeye yetkili
        if cls._is_admin:
            return True
        
        # Direkt izin kontrolü
        if permission_code in cls._cached_permissions:
            return True
        
        # Modül bazlı wildcard kontrolü (örn: 'uretim.*')
        if '.' in permission_code:
            modul = permission_code.split('.')[0]
            if f'{modul}.*' in cls._cached_permissions:
                return True
        
        return False
    
    @classmethod
    def can_view(cls, modul: str) -> bool:
        """Modülü görüntüleme izni var mı"""
        return cls.has_permission(f'{modul}.goruntule')
    
    @classmethod
    def can_create(cls, modul: str) -> bool:
        """Modülde oluşturma izni var mı"""
        return cls.has_permission(f'{modul}.olustur')
    
    @classmethod
    def can_edit(cls, modul: str) -> bool:
        """Modülde düzenleme izni var mı"""
        return cls.has_permission(f'{modul}.duzenle')
    
    @classmethod
    def can_delete(cls, modul: str) -> bool:
        """Modülde silme izni var mı"""
        return cls.has_permission(f'{modul}.sil')
    
    @classmethod
    def can_export(cls, modul: str) -> bool:
        """Modülde dışa aktarma izni var mı"""
        return cls.has_permission(f'{modul}.export')
    
    @classmethod
    def get_all_permissions(cls) -> set:
        """Kullanıcının tüm izinlerini döndür"""
        if not cls._cache_loaded:
            cls._load_permissions()
        return cls._cached_permissions.copy()
    
    @classmethod
    def get_menu_permissions(cls) -> set:
        """Kullanıcının menü yetkilerini döndür"""
        if not cls._cache_loaded:
            cls._load_permissions()
        return cls._cached_menu_permissions.copy()
    
    @classmethod
    def is_admin(cls) -> bool:
        """Kullanıcı admin mi"""
        if not cls._cache_loaded:
            cls._load_permissions()
        return cls._is_admin
    
    @classmethod
    def refresh_permissions(cls):
        """İzinleri yeniden yükle"""
        cls._cache_loaded = False
        cls._cached_permissions = set()
        cls._cached_menu_permissions = set()
        cls._load_permissions()


# Kısa yol fonksiyonları
def can_access_menu(menu_id: str) -> bool:
    return YetkiManager.can_access_menu(menu_id)

def has_permission(code: str) -> bool:
    return YetkiManager.has_permission(code)

def can_view(modul: str) -> bool:
    return YetkiManager.can_view(modul)

def can_create(modul: str) -> bool:
    return YetkiManager.can_create(modul)

def can_edit(modul: str) -> bool:
    return YetkiManager.can_edit(modul)

def can_delete(modul: str) -> bool:
    return YetkiManager.can_delete(modul)

def is_admin() -> bool:
    return YetkiManager.is_admin()
