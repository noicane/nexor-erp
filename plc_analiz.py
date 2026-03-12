# -*- coding: utf-8 -*-
"""
PLC Veri Analizi - Ortak Kazanlar ve Veri Yapisi
Bir kere calistirilip sonuclara bakilacak
"""
import pyodbc
from datetime import datetime, timedelta

def get_conn():
    from core.database import get_plc_connection
    return get_plc_connection()

def analiz():
    conn = get_conn()
    cursor = conn.cursor()

    print("=" * 80)
    print("PLC VERİ ANALİZİ - ORTAK KAZANLAR")
    print("=" * 80)

    # -------------------------------------------------------
    # 1) dbo.data tablosunun kolon yapisi
    # -------------------------------------------------------
    print("\n[1] dbo.data TABLO KOLONLARI:")
    print("-" * 50)
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'data' AND TABLE_SCHEMA = 'dbo'
        ORDER BY ORDINAL_POSITION
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:30s} {row[1]:15s} {str(row[2] or ''):>10s}")

    # -------------------------------------------------------
    # 2) Bugunun verisinden bir bara'nin tum gecislerini goster
    #    (CINKO hatti - KznNo 201-247 arasinda)
    # -------------------------------------------------------
    print("\n\n[2] SON TAMAMLANAN BİR BARA'NIN TÜM POZİSYON GEÇİŞLERİ (ÇINKO):")
    print("-" * 80)

    # Once son tamamlanan bir bara bul (201 numarali kazandan cikan)
    cursor.execute("""
        SELECT TOP 1 BaraNo, ReceteNo
        FROM dbo.data
        WHERE KznNo = 201
          AND TarihDoldurma >= DATEADD(DAY, -1, GETDATE())
        ORDER BY TarihDoldurma DESC
    """)
    row = cursor.fetchone()
    if row:
        bara_no, recete_no = row[0], row[1]
        print(f"  Bara: {bara_no}, Recete: {recete_no}")
        print()

        # Bu baranin tum pozisyon gecisleri
        cursor.execute("""
            SELECT KznNo, ReceteNo, ReceteAdim, Recete_Zamani,
                   TarihDoldurma, TarihBosaltma, Sicaklik,
                   Ort_Redresor_Akim, Miktar
            FROM dbo.data
            WHERE BaraNo = ? AND ReceteNo = ?
              AND TarihDoldurma >= DATEADD(DAY, -2, GETDATE())
            ORDER BY TarihDoldurma
        """, (bara_no, recete_no))

        print(f"  {'Sira':>4s} {'KznNo':>6s} {'Adim':>5s} {'RecZaman':>9s} {'Doldurma':>20s} {'Bosaltma':>20s} {'Sicaklik':>9s} {'Akim':>8s}")
        print(f"  {'----':>4s} {'-----':>6s} {'----':>5s} {'---------':>9s} {'--------':>20s} {'--------':>20s} {'---------':>9s} {'----':>8s}")

        for i, r in enumerate(cursor.fetchall()):
            kzn = r[0]
            adim = r[2] if r[2] is not None else '-'
            zaman = r[3] if r[3] is not None else '-'
            doldurma = r[4].strftime('%d.%m %H:%M:%S') if r[4] else '-'
            bosaltma = r[5].strftime('%d.%m %H:%M:%S') if r[5] else '-'
            sicaklik = f"{r[6]}" if r[6] is not None else '-'
            akim = f"{r[7]}" if r[7] is not None else '-'
            print(f"  {i+1:4d} {kzn:6d} {str(adim):>5s} {str(zaman):>9s} {doldurma:>20s} {bosaltma:>20s} {sicaklik:>9s} {akim:>8s}")
    else:
        print("  Cinko hattinda son 1 gunde veri bulunamadi!")

    # -------------------------------------------------------
    # 3) Ayni analiz KTL icin
    # -------------------------------------------------------
    print("\n\n[3] SON TAMAMLANAN BİR BARA'NIN TÜM POZİSYON GEÇİŞLERİ (KTL):")
    print("-" * 80)

    cursor.execute("""
        SELECT TOP 1 BaraNo, ReceteNo
        FROM dbo.data
        WHERE KznNo = 101
          AND TarihDoldurma >= DATEADD(DAY, -1, GETDATE())
        ORDER BY TarihDoldurma DESC
    """)
    row = cursor.fetchone()
    if row:
        bara_no, recete_no = row[0], row[1]
        print(f"  Bara: {bara_no}, Recete: {recete_no}")
        print()

        cursor.execute("""
            SELECT KznNo, ReceteNo, ReceteAdim, Recete_Zamani,
                   TarihDoldurma, TarihBosaltma, Sicaklik,
                   Ort_Redresor_Akim, Miktar
            FROM dbo.data
            WHERE BaraNo = ? AND ReceteNo = ?
              AND TarihDoldurma >= DATEADD(DAY, -2, GETDATE())
            ORDER BY TarihDoldurma
        """, (bara_no, recete_no))

        print(f"  {'Sira':>4s} {'KznNo':>6s} {'Adim':>5s} {'RecZaman':>9s} {'Doldurma':>20s} {'Bosaltma':>20s} {'Sicaklik':>9s} {'Akim':>8s}")
        print(f"  {'----':>4s} {'-----':>6s} {'----':>5s} {'---------':>9s} {'--------':>20s} {'--------':>20s} {'---------':>9s} {'----':>8s}")

        for i, r in enumerate(cursor.fetchall()):
            kzn = r[0]
            adim = r[2] if r[2] is not None else '-'
            zaman = r[3] if r[3] is not None else '-'
            doldurma = r[4].strftime('%d.%m %H:%M:%S') if r[4] else '-'
            bosaltma = r[5].strftime('%d.%m %H:%M:%S') if r[5] else '-'
            sicaklik = f"{r[6]}" if r[6] is not None else '-'
            akim = f"{r[7]}" if r[7] is not None else '-'
            print(f"  {i+1:4d} {kzn:6d} {str(adim):>5s} {str(zaman):>9s} {doldurma:>20s} {bosaltma:>20s} {sicaklik:>9s} {akim:>8s}")
    else:
        print("  KTL hattinda son 1 gunde veri bulunamadi!")

    # -------------------------------------------------------
    # 4) ORTAK KAZANLAR - Ayni KznNo'yu kullanan farkli ReceteNo'lar
    # -------------------------------------------------------
    print("\n\n[4] ORTAK KAZANLAR (Son 3 gun - ayni kazani kullanan farkli receteler):")
    print("-" * 80)
    cursor.execute("""
        SELECT KznNo, COUNT(DISTINCT ReceteNo) as recete_sayisi,
               STRING_AGG(CAST(ReceteNo AS VARCHAR), ',') as receteler
        FROM (
            SELECT DISTINCT KznNo, ReceteNo
            FROM dbo.data
            WHERE TarihDoldurma >= DATEADD(DAY, -3, GETDATE())
        ) t
        GROUP BY KznNo
        HAVING COUNT(DISTINCT ReceteNo) > 1
        ORDER BY recete_sayisi DESC, KznNo
    """)
    print(f"  {'KznNo':>6s} {'Recete Sayisi':>14s} {'Receteler'}")
    print(f"  {'-----':>6s} {'-------------':>14s} {'---------'}")
    for r in cursor.fetchall():
        print(f"  {r[0]:6d} {r[1]:14d} {r[2]}")

    # -------------------------------------------------------
    # 5) Ayni recetede ayni adimda farkli KznNo kullanilmis mi?
    #    (Ortak kazan mantigi)
    # -------------------------------------------------------
    print("\n\n[5] AYNI REÇETE + AYNI ADIM = FARKLI KAZANLAR (ortak kazan kaniti):")
    print("-" * 80)
    cursor.execute("""
        SELECT ReceteNo, ReceteAdim, COUNT(DISTINCT KznNo) as kazan_sayisi,
               STRING_AGG(CAST(KznNo AS VARCHAR), ',') as kazanlar
        FROM (
            SELECT DISTINCT ReceteNo, ReceteAdim, KznNo
            FROM dbo.data
            WHERE TarihDoldurma >= DATEADD(DAY, -3, GETDATE())
              AND ReceteAdim IS NOT NULL
        ) t
        GROUP BY ReceteNo, ReceteAdim
        HAVING COUNT(DISTINCT KznNo) > 1
        ORDER BY kazan_sayisi DESC, ReceteNo, ReceteAdim
    """)
    rows = cursor.fetchall()
    if rows:
        print(f"  {'ReceteNo':>9s} {'Adim':>5s} {'Kazan Sayisi':>13s} {'Kazanlar'}")
        print(f"  {'--------':>9s} {'----':>5s} {'------------':>13s} {'--------'}")
        for r in rows:
            print(f"  {r[0]:9d} {r[1]:5d} {r[2]:13d} {r[3]}")
    else:
        print("  Ortak kazan verisi bulunamadi!")

    # -------------------------------------------------------
    # 6) ReceteAdimlar tablosu var mi? Yapisi nedir?
    # -------------------------------------------------------
    print("\n\n[6] ReceteAdimlar TABLO YAPISI:")
    print("-" * 50)
    try:
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'ReceteAdimlar'
            ORDER BY ORDINAL_POSITION
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]:30s} {row[1]}")
    except:
        print("  ReceteAdimlar tablosu bulunamadi!")

    # -------------------------------------------------------
    # 7) Ornek bir recete icin ReceteAdimlar verisi
    # -------------------------------------------------------
    print("\n\n[7] ÖRNEK REÇETE ADIMLARI (Recete 53 - ZNNI):")
    print("-" * 80)
    try:
        cursor.execute("""
            SELECT *
            FROM ReceteAdimlar
            WHERE Panel_Recete_No = 53
            ORDER BY Kazan_No
        """)
        cols = [desc[0] for desc in cursor.description]
        print(f"  Kolonlar: {', '.join(cols)}")
        print()
        for r in cursor.fetchall():
            vals = [f"{v}" for v in r]
            print(f"  {' | '.join(vals)}")
    except Exception as e:
        print(f"  Hata: {e}")

    # -------------------------------------------------------
    # 8) CINKO hattinda hangi kazanlar kullaniliyor?
    # -------------------------------------------------------
    print("\n\n[8] ÇINKO HATTI KAZAN KULLANIMI (Son 3 gun):")
    print("-" * 60)
    cursor.execute("""
        SELECT KznNo, COUNT(*) as islem_sayisi,
               COUNT(DISTINCT BaraNo) as farkli_bara,
               COUNT(DISTINCT ReceteNo) as farkli_recete
        FROM dbo.data
        WHERE KznNo BETWEEN 201 AND 247
          AND TarihDoldurma >= DATEADD(DAY, -3, GETDATE())
        GROUP BY KznNo
        ORDER BY KznNo
    """)
    print(f"  {'KznNo':>6s} {'Islem':>8s} {'Bara':>8s} {'Recete':>8s}")
    print(f"  {'-----':>6s} {'-----':>8s} {'----':>8s} {'------':>8s}")
    for r in cursor.fetchall():
        print(f"  {r[0]:6d} {r[1]:8d} {r[2]:8d} {r[3]:8d}")

    conn.close()
    print("\n\n✅ Analiz tamamlandi!")

if __name__ == "__main__":
    analiz()
