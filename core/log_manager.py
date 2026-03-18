# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Merkezi Log Sistemi
Tüm kullanıcı işlemlerini log.islem_log tablosuna kaydeder
"""

import socket
from datetime import datetime
from core.database import get_db_connection


class LogManager:
    """Merkezi log yönetim sınıfı"""
    
    _current_user_id = None
    _current_user_name = None
    _ip_address = None
    
    @classmethod
    def set_current_user(cls, user_id: int, user_name: str):
        """Aktif kullanıcıyı ayarla (login sonrası çağrılır)"""
        cls._current_user_id = user_id
        cls._current_user_name = user_name
        cls._ip_address = cls._get_local_ip()
    
    @classmethod
    def clear_current_user(cls):
        """Kullanıcı bilgisini temizle (logout sonrası)"""
        cls._current_user_id = None
        cls._current_user_name = None
    
    @classmethod
    def _get_local_ip(cls):
        """Yerel IP adresini al"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    @classmethod
    def log(cls, modul: str, islem: str, tablo_adi: str = None, kayit_id: int = None,
            aciklama: str = None, eski_deger: str = None, yeni_deger: str = None):
        """
        İşlem logu kaydet
        
        Args:
            modul: Modül adı (uretim, kalite, stok, sistem, vb.)
            islem: İşlem tipi (INSERT, UPDATE, DELETE, VIEW, LOGIN, LOGOUT, EXPORT)
            tablo_adi: Etkilenen tablo adı
            kayit_id: Etkilenen kayıt ID'si
            aciklama: İşlem açıklaması
            eski_deger: Güncelleme öncesi değer (JSON string)
            yeni_deger: Güncelleme sonrası değer (JSON string)
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO log.islem_log
                (tarih, kullanici_id, kullanici_adi, ip_adresi, modul, islem,
                 tablo_adi, kayit_id, aciklama, eski_deger, yeni_deger)
                VALUES (GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                cls._current_user_id,
                cls._current_user_name or 'system',
                cls._ip_address or '127.0.0.1',
                modul,
                islem,
                tablo_adi,
                kayit_id,
                aciklama,
                eski_deger,
                yeni_deger
            ])

            conn.commit()

        except ConnectionError:
            pass  # DB bağlantısı yoksa log sessizce atlanır
        except Exception as e:
            print(f"Log kayıt hatası: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    @classmethod
    def log_login(cls, user_id: int, user_name: str, basarili: bool = True):
        """Giriş logla"""
        cls.set_current_user(user_id, user_name)
        cls.log(
            modul='sistem',
            islem='LOGIN',
            aciklama=f"Kullanıcı {'başarıyla giriş yaptı' if basarili else 'giriş başarısız'}"
        )
    
    @classmethod
    def log_logout(cls):
        """Çıkış logla"""
        cls.log(
            modul='sistem',
            islem='LOGOUT',
            aciklama='Kullanıcı çıkış yaptı'
        )
        cls.clear_current_user()
    
    @classmethod
    def log_insert(cls, modul: str, tablo: str, kayit_id: int, aciklama: str = None, yeni_deger: str = None):
        """Yeni kayıt ekleme logla"""
        cls.log(
            modul=modul,
            islem='INSERT',
            tablo_adi=tablo,
            kayit_id=kayit_id,
            aciklama=aciklama or f'{tablo} tablosuna yeni kayıt eklendi',
            yeni_deger=yeni_deger
        )
    
    @classmethod
    def log_update(cls, modul: str, tablo: str, kayit_id: int, aciklama: str = None, 
                   eski_deger: str = None, yeni_deger: str = None):
        """Kayıt güncelleme logla"""
        cls.log(
            modul=modul,
            islem='UPDATE',
            tablo_adi=tablo,
            kayit_id=kayit_id,
            aciklama=aciklama or f'{tablo} tablosunda kayıt güncellendi',
            eski_deger=eski_deger,
            yeni_deger=yeni_deger
        )
    
    @classmethod
    def log_delete(cls, modul: str, tablo: str, kayit_id: int, aciklama: str = None, eski_deger: str = None):
        """Kayıt silme logla"""
        cls.log(
            modul=modul,
            islem='DELETE',
            tablo_adi=tablo,
            kayit_id=kayit_id,
            aciklama=aciklama or f'{tablo} tablosundan kayıt silindi',
            eski_deger=eski_deger
        )
    
    @classmethod
    def log_view(cls, modul: str, tablo: str = None, kayit_id: int = None, aciklama: str = None):
        """Görüntüleme logla"""
        cls.log(
            modul=modul,
            islem='VIEW',
            tablo_adi=tablo,
            kayit_id=kayit_id,
            aciklama=aciklama
        )
    
    @classmethod
    def log_export(cls, modul: str, aciklama: str = None):
        """Dışa aktarma logla"""
        cls.log(
            modul=modul,
            islem='EXPORT',
            aciklama=aciklama or 'Veri dışa aktarıldı'
        )


# Kısa yol fonksiyonları
def log_islem(modul: str, islem: str, **kwargs):
    """Kısa yol log fonksiyonu"""
    LogManager.log(modul, islem, **kwargs)

def log_insert(modul: str, tablo: str, kayit_id: int, **kwargs):
    LogManager.log_insert(modul, tablo, kayit_id, **kwargs)

def log_update(modul: str, tablo: str, kayit_id: int, **kwargs):
    LogManager.log_update(modul, tablo, kayit_id, **kwargs)

def log_delete(modul: str, tablo: str, kayit_id: int, **kwargs):
    LogManager.log_delete(modul, tablo, kayit_id, **kwargs)

def log_view(modul: str, **kwargs):
    LogManager.log_view(modul, **kwargs)
