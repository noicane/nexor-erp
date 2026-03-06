# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - PDKS Service Test Script
PDKS okuma servisini test etmek için kullanılır
"""

import sys
import time
from datetime import datetime

# Test için gerekli importlar
try:
    from core.pdks_reader_service import (
        get_pdks_service, 
        start_pdks_service, 
        stop_pdks_service,
        is_service_running
    )
    from core.database import get_db_connection
    print("✅ İmportlar başarılı")
except ImportError as e:
    print(f"❌ İmport hatası: {e}")
    sys.exit(1)


def test_database_connection():
    """Veritabanı bağlantısını test et"""
    print("\n" + "="*50)
    print("TEST 1: Veritabanı Bağlantısı")
    print("="*50)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tabloları kontrol et
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'ik' 
            AND TABLE_NAME IN ('pdks_cihazlari', 'pdks_hareketler', 'pdks_okuma_loglari')
        """)
        count = cursor.fetchone()[0]
        
        if count == 3:
            print("✅ Tüm PDKS tabloları mevcut")
        else:
            print(f"⚠️ Uyarı: {count}/3 tablo bulundu. Migration çalıştı mı?")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Veritabanı hatası: {e}")
        return False


def test_cihaz_listesi():
    """Cihaz listesini test et"""
    print("\n" + "="*50)
    print("TEST 2: Cihaz Listesi")
    print("="*50)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cihaz_kodu, cihaz_adi, ip_adresi, port, aktif_mi, durum, okuma_periyodu
            FROM ik.pdks_cihazlari
            ORDER BY cihaz_kodu
        """)
        
        cihazlar = cursor.fetchall()
        
        if not cihazlar:
            print("⚠️ Uyarı: Hiç cihaz tanımlanmamış!")
            print("   Lütfen önce cihaz ekleyin.")
            return False
        
        print(f"✅ {len(cihazlar)} cihaz bulundu:\n")
        
        for cihaz in cihazlar:
            kod, ad, ip, port, aktif, durum, periyot = cihaz
            aktif_str = "✓ Aktif" if aktif else "✗ Pasif"
            print(f"  • {kod}: {ad}")
            print(f"    IP: {ip}:{port} | Durum: {durum} | {aktif_str} | Periyot: {periyot}dk")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Cihaz listesi hatası: {e}")
        return False


def test_personel_kart_ids():
    """Personel kart ID'lerini kontrol et"""
    print("\n" + "="*50)
    print("TEST 3: Personel Kart ID'leri")
    print("="*50)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Toplam aktif personel
        cursor.execute("SELECT COUNT(*) FROM ik.personeller WHERE aktif_mi = 1")
        toplam = cursor.fetchone()[0]
        
        # Kart ID'si olan
        cursor.execute("SELECT COUNT(*) FROM ik.personeller WHERE aktif_mi = 1 AND kart_id IS NOT NULL")
        kart_id_olan = cursor.fetchone()[0]
        
        print(f"Toplam aktif personel: {toplam}")
        print(f"Kart ID'si olan: {kart_id_olan}")
        
        if kart_id_olan == 0:
            print("⚠️ Uyarı: Hiç personelin kart ID'si yok!")
            print("   PDKS cihazdan gelen veriler personelle eşleşmeyecek.")
        elif kart_id_olan < toplam:
            print(f"⚠️ Uyarı: {toplam - kart_id_olan} personelin kart ID'si eksik")
        else:
            print("✅ Tüm personelin kart ID'si tanımlı")
        
        # Örnek listele
        cursor.execute("""
            SELECT TOP 5 ad, soyad, kart_id 
            FROM ik.personeller 
            WHERE aktif_mi = 1 AND kart_id IS NOT NULL
        """)
        
        ornekler = cursor.fetchall()
        if ornekler:
            print("\nÖrnek personeller:")
            for ad, soyad, kart_id in ornekler:
                print(f"  • {ad} {soyad}: {kart_id}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Personel kontrolü hatası: {e}")
        return False


def test_service_singleton():
    """Service singleton'ını test et"""
    print("\n" + "="*50)
    print("TEST 4: Service Singleton")
    print("="*50)
    
    try:
        service1 = get_pdks_service()
        service2 = get_pdks_service()
        
        if service1 is service2:
            print("✅ Singleton pattern doğru çalışıyor")
            return True
        else:
            print("❌ Singleton pattern çalışmıyor!")
            return False
            
    except Exception as e:
        print(f"❌ Singleton testi hatası: {e}")
        return False


def test_service_lifecycle():
    """Service başlatma/durdurma test et"""
    print("\n" + "="*50)
    print("TEST 5: Service Lifecycle")
    print("="*50)
    
    try:
        # İlk durum
        if is_service_running():
            print("ℹ️ Servis zaten çalışıyor, durduruluyor...")
            stop_pdks_service()
            time.sleep(2)
        
        print("✅ Servis durmuş durumda")
        
        # Başlat
        print("\nServis başlatılıyor...")
        start_pdks_service()
        time.sleep(3)
        
        if is_service_running():
            print("✅ Servis başarıyla başlatıldı")
        else:
            print("❌ Servis başlatılamadı!")
            return False
        
        # 5 saniye bekle
        print("\n5 saniye bekleniyor (ilk okumalar için)...")
        for i in range(5, 0, -1):
            print(f"  {i}...", end="\r")
            time.sleep(1)
        print()
        
        # Durdur
        print("\nServis durduruluyor...")
        stop_pdks_service()
        time.sleep(2)
        
        if not is_service_running():
            print("✅ Servis başarıyla durduruldu")
        else:
            print("⚠️ Uyarı: Servis hala çalışıyor!")
        
        return True
        
    except Exception as e:
        print(f"❌ Lifecycle testi hatası: {e}")
        return False


def test_okuma_loglari():
    """Okuma loglarını kontrol et"""
    print("\n" + "="*50)
    print("TEST 6: Okuma Logları")
    print("="*50)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT TOP 10 
                c.cihaz_kodu,
                l.okuma_zamani,
                l.okuma_tipi,
                l.kayit_sayisi,
                l.yeni_kayit_sayisi,
                l.basarili,
                l.hata_mesaji
            FROM ik.pdks_okuma_loglari l
            INNER JOIN ik.pdks_cihazlari c ON l.cihaz_id = c.id
            ORDER BY l.okuma_zamani DESC
        """)
        
        loglar = cursor.fetchall()
        
        if not loglar:
            print("ℹ️ Henüz okuma logu yok")
            print("   Servis çalıştıktan sonra loglar görünecek")
        else:
            print(f"✅ {len(loglar)} log kaydı bulundu:\n")
            
            for log in loglar[:5]:  # İlk 5'i göster
                kod, zaman, tip, kayit, yeni, basarili, hata = log
                durum = "✓" if basarili else "✗"
                hata_str = f" ({hata})" if hata else ""
                print(f"  {durum} {kod} [{tip}] - {zaman.strftime('%d.%m %H:%M:%S')}")
                print(f"    Kayıt: {kayit} | Yeni: {yeni}{hata_str}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Log kontrolü hatası: {e}")
        return False


def run_all_tests():
    """Tüm testleri çalıştır"""
    print("\n" + "="*70)
    print("🔬 REDLINE NEXOR ERP - PDKS SERVICE TEST SÜİTİ")
    print("="*70)
    print(f"Başlangıç Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Testleri çalıştır
    results.append(("Veritabanı Bağlantısı", test_database_connection()))
    results.append(("Cihaz Listesi", test_cihaz_listesi()))
    results.append(("Personel Kart ID'leri", test_personel_kart_ids()))
    results.append(("Service Singleton", test_service_singleton()))
    results.append(("Service Lifecycle", test_service_lifecycle()))
    results.append(("Okuma Logları", test_okuma_loglari()))
    
    # Özet
    print("\n" + "="*70)
    print("📊 TEST SONUÇLARI")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{status:15} | {test_name}")
    
    print("-"*70)
    print(f"Toplam: {passed}/{total} test başarılı ({passed*100//total}%)")
    print("="*70)
    
    if passed == total:
        print("\n🎉 TÜM TESTLER BAŞARILI!")
        print("PDKS servisi kullanıma hazır.")
    else:
        print(f"\n⚠️ {total - passed} TEST BAŞARISIZ!")
        print("Lütfen hataları düzeltip tekrar deneyin.")
    
    print(f"\nBitiş Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test iptal edildi")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
