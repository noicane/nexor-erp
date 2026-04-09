# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - WhatsApp Gönderim Servisi
Twilio veya pywhatkit ile WhatsApp mesajı gönderir
"""
from core.database import get_db_connection


class WhatsAppService:
    """WhatsApp mesaj gönderme servisi"""
    
    def __init__(self):
        self.ayarlar = self._load_ayarlar()
    
    def _load_ayarlar(self):
        """Aktif ayarları yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT servis_tipi, twilio_account_sid, twilio_auth_token, twilio_whatsapp_number,
                       pywhatkit_wait_time, pywhatkit_close_time, test_modu, test_telefon,
                       whapi_token
                FROM sistem.whatsapp_ayarlari WHERE aktif_mi = 1
            """)
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return {
                'servis_tipi': row[0],
                'twilio_sid': row[1],
                'twilio_token': row[2],
                'twilio_number': row[3],
                'pywhatkit_wait': row[4] or 15,
                'pywhatkit_close': row[5] or 5,
                'test_modu': row[6],
                'test_telefon': row[7],
                'whapi_token': row[8] or '',
            }
        except Exception as e:
            print(f"[UYARI] WhatsApp ayarlari yuklenemedi: {e}")
            return None
    
    def gonder(self, telefon: str, mesaj: str, bildirim_id: int = None):
        """
        WhatsApp mesajı gönder
        
        Args:
            telefon: Alıcı telefon (+905321234567 formatında)
            mesaj: Gönderilecek mesaj
            bildirim_id: Bildirim kayıt ID (opsiyonel)
        
        Returns:
            (success: bool, message: str)
        """
        if not self.ayarlar:
            return False, "WhatsApp ayarları yapılandırılmamış"
        
        # Test modu kontrolü
        if self.ayarlar['test_modu'] == 1 or self.ayarlar['test_modu'] == True:
            print(f"[TEST] TEST MODU AKTIF - Tüm mesajlar {self.ayarlar['test_telefon']} numarasına gidiyor")
            telefon = self.ayarlar['test_telefon']
            mesaj = f"[TEST MODU]\n{mesaj}"
        else:
            print(f"[OK] NORMAL MOD - Mesaj {telefon} numarasina gidecek")
        
        # Telefon format kontrolü
        if not telefon or not telefon.startswith('+'):
            return False, f"Geçersiz telefon formatı: {telefon}"
        
        # Servis tipine göre gönder
        if self.ayarlar['servis_tipi'] == 'WHAPI':
            success, msg = self._gonder_whapi(telefon, mesaj)
        elif self.ayarlar['servis_tipi'] == 'TWILIO':
            success, msg = self._gonder_twilio(telefon, mesaj)
        elif self.ayarlar['servis_tipi'] == 'PYWHATKIT':
            success, msg = self._gonder_pywhatkit(telefon, mesaj)
        else:
            return False, f"Bilinmeyen servis tipi: {self.ayarlar['servis_tipi']}"
        
        # Sonucu kaydet
        if bildirim_id:
            self._kaydet_sonuc(bildirim_id, telefon, success, msg)
        
        return success, msg
    
    def _gonder_twilio(self, telefon: str, mesaj: str):
        """Twilio ile gönder"""
        try:
            from twilio.rest import Client
            
            client = Client(
                self.ayarlar['twilio_sid'],
                self.ayarlar['twilio_token']
            )
            
            message = client.messages.create(
                from_=f"whatsapp:{self.ayarlar['twilio_number']}",
                body=mesaj,
                to=f"whatsapp:{telefon}"
            )
            
            print(f"[OK] Twilio mesaj gonderildi: {message.sid}")
            return True, f"Gönderildi (SID: {message.sid})"
            
        except ImportError:
            return False, "Twilio kütüphanesi yüklü değil. Terminalde çalıştırın: pip install twilio --break-system-packages"
        except Exception as e:
            print(f"[HATA] Twilio hatasi: {e}")
            return False, str(e)
    
    def _gonder_whapi(self, telefon: str, mesaj: str):
        """whapi.cloud REST API ile gonder"""
        try:
            import requests

            # Telefon: +905326386254 -> 905326386254
            telefon_temiz = telefon.replace('+', '').replace(' ', '').replace('-', '')

            token = self.ayarlar.get('whapi_token', '')
            if not token:
                return False, "WHAPI token ayarlanmamis"

            url = "https://gate.whapi.cloud/messages/text"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            payload = {
                "to": f"{telefon_temiz}@s.whatsapp.net",
                "body": mesaj,
            }

            resp = requests.post(url, json=payload, headers=headers, timeout=15)

            if resp.status_code in (200, 201):
                print(f"[OK] WHAPI mesaj gonderildi: {telefon}")
                return True, "Gonderildi"
            else:
                err = resp.text[:200]
                print(f"[HATA] WHAPI hata ({resp.status_code}): {err}")
                return False, f"HTTP {resp.status_code}: {err}"

        except ImportError:
            return False, "requests kutuphanesi yuklu degil: pip install requests"
        except Exception as e:
            print(f"[HATA] WHAPI hatasi: {e}")
            return False, str(e)

    def _gonder_pywhatkit(self, telefon: str, mesaj: str):
        """pywhatkit ile gönder"""
        try:
            import pywhatkit
            
            # Telefon numarasından + işaretini kaldır
            telefon_temiz = telefon.replace('+', '').replace(' ', '')
            
            pywhatkit.sendwhatmsg_instantly(
                phone_no=f"+{telefon_temiz}",
                message=mesaj,
                wait_time=self.ayarlar['pywhatkit_wait'],
                tab_close=True,
                close_time=self.ayarlar['pywhatkit_close']
            )
            
            print(f"[OK] pywhatkit mesaj gonderildi: {telefon}")
            return True, "Gönderildi"
            
        except ImportError as e:
            import sys
            error_msg = f"""pywhatkit yüklü değil!

Python yolu: {sys.executable}

Terminalde çalıştır:
{sys.executable} -m pip install pywhatkit

Hata detayı: {str(e)}"""
            return False, error_msg
        except Exception as e:
            print(f"[HATA] pywhatkit hatasi: {e}")
            return False, str(e)
    
    def _kaydet_sonuc(self, bildirim_id: int, telefon: str, success: bool, mesaj: str):
        """Gönderim sonucunu kaydet"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if success:
                cursor.execute("""
                    UPDATE sistem.bildirimler SET
                        whatsapp_gonderildi_mi = 1,
                        whatsapp_gonderim_tarihi = GETDATE(),
                        whatsapp_telefon = ?
                    WHERE id = ?
                """, (telefon, bildirim_id))
            else:
                cursor.execute("""
                    UPDATE sistem.bildirimler SET
                        whatsapp_gonderildi_mi = 0,
                        whatsapp_telefon = ?,
                        whatsapp_hata_mesaji = ?
                    WHERE id = ?
                """, (telefon, mesaj, bildirim_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[UYARI] Sonuc kaydetme hatasi: {e}")
    
    def toplu_gonder(self, alicilar: list, mesaj: str):
        """
        Toplu WhatsApp gönderimi
        
        Args:
            alicilar: [(kullanici_id, telefon), ...] listesi
            mesaj: Gönderilecek mesaj
        
        Returns:
            (basarili_sayisi, toplam_sayi, hatalar)
        """
        basarili = 0
        toplam = len(alicilar)
        hatalar = []
        
        for kullanici_id, telefon in alicilar:
            if not telefon:
                hatalar.append(f"Kullanıcı {kullanici_id}: Telefon yok")
                continue
            
            success, msg = self.gonder(telefon, mesaj)
            
            if success:
                basarili += 1
            else:
                hatalar.append(f"{telefon}: {msg}")
        
        return basarili, toplam, hatalar


# Global servis instance
_whatsapp_service = None

def get_whatsapp_service():
    """WhatsApp servisini al (singleton)"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service


def gonder_whatsapp(telefon: str, mesaj: str, bildirim_id: int = None):
    """
    Kolay kullanım için wrapper fonksiyon
    
    Kullanım:
        from utils.whatsapp_service import gonder_whatsapp
        
        success, msg = gonder_whatsapp(
            telefon="+905321234567",
            mesaj="🔴 KRİTİK! Lab analiz limiti aşıldı"
        )
    """
    service = get_whatsapp_service()
    return service.gonder(telefon, mesaj, bildirim_id)
