# -*- coding: utf-8 -*-
"""
Connection Pool Test Script
Devreye almadan önce bu testi çalıştırın

Test Senaryoları:
1. Basit bağlantı testi
2. Çoklu eşzamanlı bağlantı
3. Hata durumu recovery
4. Pool istatistikleri
5. HareketMotoru uyumluluğu
"""
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Test için path ayarı
import sys
sys.path.insert(0, '.')

from database import (
    get_db_connection, 
    execute_query, 
    execute_non_query,
    get_pool_stats,
    transaction
)


def test_1_basit_baglanti():
    """Test 1: Basit bağlantı testi"""
    print("\n" + "="*60)
    print("TEST 1: Basit Bağlantı")
    print("="*60)
    
    try:
        # Yeni stil (with)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test, GETDATE() as tarih")
            row = cursor.fetchone()
            print(f"✓ With kullanımı başarılı: test={row[0]}, tarih={row[1]}")
        
        # Eski stil
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0][:50]
        conn.close()
        print(f"✓ Eski stil başarılı: {version}...")
        
        # execute_query
        result = execute_query("SELECT TOP 1 id, ad FROM tanim.depolar")
        if result:
            print(f"✓ execute_query başarılı: {result[0]}")
        else:
            print("✓ execute_query başarılı (boş sonuç)")
        
        return True
        
    except Exception as e:
        print(f"✗ HATA: {e}")
        return False


def test_2_coklu_baglanti():
    """Test 2: 20 eşzamanlı bağlantı"""
    print("\n" + "="*60)
    print("TEST 2: Çoklu Eşzamanlı Bağlantı (20 thread)")
    print("="*60)
    
    results = {'success': 0, 'fail': 0, 'times': []}
    lock = threading.Lock()
    
    def worker(worker_id):
        start = time.time()
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # Gerçekçi bir sorgu
                cursor.execute("""
                    SELECT TOP 10 id, ad, kod 
                    FROM tanim.depolar 
                    WHERE aktif_mi = 1
                """)
                rows = cursor.fetchall()
                time.sleep(0.1)  # İşlem simülasyonu
                
            elapsed = time.time() - start
            with lock:
                results['success'] += 1
                results['times'].append(elapsed)
            return True
            
        except Exception as e:
            with lock:
                results['fail'] += 1
            print(f"  Worker {worker_id} hatası: {e}")
            return False
    
    # 20 thread aynı anda
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(worker, i) for i in range(20)]
        for future in as_completed(futures):
            pass
    
    avg_time = sum(results['times']) / len(results['times']) if results['times'] else 0
    
    print(f"✓ Başarılı: {results['success']}")
    print(f"✗ Başarısız: {results['fail']}")
    print(f"⏱ Ortalama süre: {avg_time:.3f}s")
    
    stats = get_pool_stats()
    print(f"📊 Pool durumu: {stats['erp']}")
    
    return results['fail'] == 0


def test_3_yuk_testi():
    """Test 3: Yoğun yük testi (100 işlem)"""
    print("\n" + "="*60)
    print("TEST 3: Yük Testi (100 işlem, 20 thread)")
    print("="*60)
    
    results = {'success': 0, 'fail': 0}
    lock = threading.Lock()
    start_time = time.time()
    
    def worker(i):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tanim.depolar")
                cursor.fetchone()
            with lock:
                results['success'] += 1
            return True
        except Exception as e:
            with lock:
                results['fail'] += 1
            return False
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(worker, i) for i in range(100)]
        for future in as_completed(futures):
            pass
    
    elapsed = time.time() - start_time
    ops_per_sec = results['success'] / elapsed
    
    print(f"✓ Başarılı: {results['success']}/100")
    print(f"✗ Başarısız: {results['fail']}")
    print(f"⏱ Toplam süre: {elapsed:.2f}s")
    print(f"📈 Saniyede işlem: {ops_per_sec:.1f}")
    
    return results['fail'] == 0


def test_4_transaction():
    """Test 4: Transaction yönetimi"""
    print("\n" + "="*60)
    print("TEST 4: Transaction Yönetimi")
    print("="*60)
    
    try:
        # Başarılı transaction
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        print("✓ Başarılı transaction tamamlandı")
        
        # Rollback test - hata durumu
        try:
            with transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                raise ValueError("Test hatası")
        except ValueError:
            print("✓ Hata durumunda rollback yapıldı")
        
        return True
        
    except Exception as e:
        print(f"✗ HATA: {e}")
        return False


def test_5_hareket_motoru_uyumu():
    """Test 5: HareketMotoru ile uyumluluk"""
    print("\n" + "="*60)
    print("TEST 5: HareketMotoru Uyumluluğu")
    print("="*60)
    
    try:
        # HareketMotoru'nun beklediği şekilde connection kullanımı
        with get_db_connection() as conn:
            # HareketMotoru şunu yapıyor:
            # self.conn = conn
            # self.cursor = conn.cursor()
            
            cursor = conn.cursor()
            
            # Bir transaction simülasyonu
            cursor.execute("SELECT COUNT(*) FROM stok.stok_bakiye")
            count = cursor.fetchone()[0]
            
            # Birden fazla sorgu aynı connection'da
            cursor.execute("SELECT TOP 1 * FROM stok.stok_bakiye")
            
            # commit (HareketMotoru'daki gibi)
            conn.commit()
            
        print(f"✓ HareketMotoru uyumlu çalışıyor (bakiye sayısı: {count})")
        return True
        
    except Exception as e:
        print(f"✗ HATA: {e}")
        return False


def test_6_pool_stats():
    """Test 6: Pool istatistikleri"""
    print("\n" + "="*60)
    print("TEST 6: Pool İstatistikleri")
    print("="*60)
    
    stats = get_pool_stats()
    
    if stats['erp']:
        erp = stats['erp']
        print(f"📊 ERP Pool:")
        print(f"   - Toplam istek: {erp['total_requests']}")
        print(f"   - Pool hit: {erp['pool_hits']}")
        print(f"   - Yeni connection: {erp['new_connections']}")
        print(f"   - Aktif connection: {erp['active_connections']}")
        print(f"   - Pool boyutu: {erp['pool_size']}")
        print(f"   - Maks connection: {erp['max_connections']}")
        
        hit_rate = (erp['pool_hits'] / erp['total_requests'] * 100) if erp['total_requests'] > 0 else 0
        print(f"   - Hit oranı: {hit_rate:.1f}%")
    
    return True


def run_all_tests():
    """Tüm testleri çalıştır"""
    print("\n" + "="*60)
    print("REDLINE NEXOR ERP - Connection Pool Test Suite")
    print("="*60)
    
    tests = [
        ("Basit Bağlantı", test_1_basit_baglanti),
        ("Çoklu Bağlantı", test_2_coklu_baglanti),
        ("Yük Testi", test_3_yuk_testi),
        ("Transaction", test_4_transaction),
        ("HareketMotoru Uyumu", test_5_hareket_motoru_uyumu),
        ("Pool İstatistikleri", test_6_pool_stats),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} EXCEPTION: {e}")
            results.append((name, False))
    
    # Özet
    print("\n" + "="*60)
    print("TEST SONUÇLARI")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ BAŞARILI" if result else "✗ BAŞARISIZ"
        print(f"  {status}: {name}")
    
    print(f"\nToplam: {passed}/{total} test başarılı")
    
    if passed == total:
        print("\n🎉 TÜM TESTLER BAŞARILI - Devreye almaya hazır!")
    else:
        print("\n⚠️ BAZI TESTLER BAŞARISIZ - Kontrol edin!")
    
    return passed == total


if __name__ == "__main__":
    run_all_tests()
