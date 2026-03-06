# -*- coding: utf-8 -*-
"""
NEXOR - Kaplama Planlama Veri Kesif Araci
Mevcut PLC, kazan, banyo, recete verilerini tarar ve raporlar.
Calistir: python tools/kaplama_kesif.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db_connection

SEPARATOR = "=" * 80


def section(title):
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def safe_query(cursor, sql, desc=""):
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description] if cursor.description else []
        return rows, cols
    except Exception as e:
        print(f"  [HATA] {desc}: {e}")
        return [], []


def main():
    print("NEXOR - Kaplama Planlama Veri Kesif Raporu")
    print(f"{'=' * 50}")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"DB baglanti hatasi: {e}")
        return

    # ═══════════════════════════════════════════════
    # 1. PLC CACHE - Mevcut Kazanlar
    # ═══════════════════════════════════════════════
    section("1. PLC CACHE - Aktif Kazanlar")
    rows, cols = safe_query(cursor, """
        SELECT kazan_no, hat_kodu, pozisyon_adi, durum, durum_dakika,
               ort_sicaklik, ort_akim, recete_no, son_bara,
               islem_sayisi_24s, toplam_miktar_24s, gunluk_bara_adet
        FROM uretim.plc_cache
        ORDER BY kazan_no
    """, "plc_cache")

    if rows:
        print(f"\n  Toplam kazan: {len(rows)}")
        print(f"\n  {'Kazan':>6} {'Hat':>6} {'Pozisyon':<25} {'Durum':<10} {'Dk':>5} {'Sicak':>7} {'Akim':>7} {'Recete':>7} {'Bara':>5} {'24s':>5}")
        print(f"  {'-'*6} {'-'*6} {'-'*25} {'-'*10} {'-'*5} {'-'*7} {'-'*7} {'-'*7} {'-'*5} {'-'*5}")
        for r in rows:
            print(f"  {r[0]:>6} {(r[1] or '-'):>6} {(r[2] or '-'):<25} {(r[3] or '-'):<10} {(r[4] or 0):>5} {(r[5] or 0):>7.1f} {(r[6] or 0):>7.1f} {(r[7] or '-'):>7} {(r[8] or '-'):>5} {(r[9] or 0):>5}")

        # Hat bazli ozet
        print(f"\n  --- Hat Bazli Ozet ---")
        for hat in ['KTL', 'CINKO', 'DIGER']:
            hat_rows = [r for r in rows if (r[1] or '') == hat]
            aktif = sum(1 for r in hat_rows if r[3] == 'AKTIF')
            bekliyor = sum(1 for r in hat_rows if r[3] == 'BEKLIYOR')
            durdu = sum(1 for r in hat_rows if r[3] == 'DURDU')
            print(f"  {hat:>6}: {len(hat_rows)} kazan (Aktif:{aktif}, Bekliyor:{bekliyor}, Durdu:{durdu})")
    else:
        print("  PLC cache bos veya tablo yok")

    # ═══════════════════════════════════════════════
    # 2. BANYO TANIMLARI
    # ═══════════════════════════════════════════════
    section("2. BANYO TANIMLARI")
    rows, cols = safe_query(cursor, """
        SELECT b.id, b.kod, b.ad, b.hacim_lt,
               b.sicaklik_min, b.sicaklik_max, b.sicaklik_hedef,
               bt.kod as tip_kodu, bt.ad as tip_adi,
               h.kod as hat_kodu, h.ad as hat_adi,
               b.aktif_mi
        FROM uretim.banyo_tanimlari b
        LEFT JOIN tanim.banyo_tipleri bt ON b.banyo_tipi_id = bt.id
        LEFT JOIN tanim.uretim_hatlari h ON b.hat_id = h.id
        ORDER BY h.kod, b.kod
    """, "banyo_tanimlari")

    if rows:
        print(f"\n  Toplam banyo: {len(rows)} (Aktif: {sum(1 for r in rows if r[11])})")
        print(f"\n  {'ID':>4} {'Kod':<20} {'Ad':<30} {'Hacim':>7} {'SMin':>5} {'SMax':>5} {'SHdf':>5} {'Tip':<10} {'Hat':<8} {'Aktif':>5}")
        print(f"  {'-'*4} {'-'*20} {'-'*30} {'-'*7} {'-'*5} {'-'*5} {'-'*5} {'-'*10} {'-'*8} {'-'*5}")
        for r in rows:
            print(f"  {r[0]:>4} {(r[1] or '-'):<20} {(r[2] or '-'):<30} {(r[3] or 0):>7.0f} {(r[4] or 0):>5.0f} {(r[5] or 0):>5.0f} {(r[6] or 0):>5.0f} {(r[7] or '-'):<10} {(r[9] or '-'):<8} {'Evet' if r[11] else 'Hayir':>5}")
    else:
        print("  Banyo tanimlari tablosu bos veya yok")

    # ═══════════════════════════════════════════════
    # 3. BANYO TIPLERI
    # ═══════════════════════════════════════════════
    section("3. BANYO TIPLERI")
    rows, cols = safe_query(cursor, """
        SELECT id, kod, ad, kategori, aktif_mi,
               kimyasal_gerekli_mi, sicaklik_gerekli_mi, ph_gerekli_mi, akim_gerekli_mi
        FROM tanim.banyo_tipleri
        ORDER BY kod
    """, "banyo_tipleri")

    if rows:
        print(f"\n  {'ID':>4} {'Kod':<15} {'Ad':<25} {'Kategori':<15} {'Kimyasal':>8} {'Sicak':>6} {'pH':>4} {'Akim':>5}")
        for r in rows:
            print(f"  {r[0]:>4} {(r[1] or '-'):<15} {(r[2] or '-'):<25} {(r[3] or '-'):<15} {'E' if r[5] else '-':>8} {'E' if r[6] else '-':>6} {'E' if r[7] else '-':>4} {'E' if r[8] else '-':>5}")
    else:
        print("  Banyo tipleri tablosu bos veya yok")

    # ═══════════════════════════════════════════════
    # 4. HAT POZISYONLARI
    # ═══════════════════════════════════════════════
    section("4. HAT POZISYONLARI")
    rows, cols = safe_query(cursor, """
        SELECT hp.id, hp.kod, hp.ad, hp.sira_no,
               h.kod as hat_kodu, h.ad as hat_adi,
               bt.kod as banyo_tipi_kodu
        FROM tanim.hat_pozisyonlar hp
        LEFT JOIN tanim.uretim_hatlari h ON hp.hat_id = h.id
        LEFT JOIN tanim.banyo_tipleri bt ON hp.banyo_tipi_id = bt.id
        ORDER BY h.kod, hp.sira_no
    """, "hat_pozisyonlar")

    if rows:
        print(f"\n  Toplam pozisyon: {len(rows)}")
        current_hat = ""
        for r in rows:
            hat = r[4] or '-'
            if hat != current_hat:
                current_hat = hat
                print(f"\n  --- {hat} ({r[5] or ''}) ---")
            print(f"    {(r[3] or 0):>3}. [{r[1] or '-':<12}] {(r[2] or '-'):<35} Tip: {r[6] or '-'}")
    else:
        print("  Hat pozisyonlari tablosu bos veya yok")

    # ═══════════════════════════════════════════════
    # 5. URETIM HATLARI
    # ═══════════════════════════════════════════════
    section("5. URETIM HATLARI")
    rows, cols = safe_query(cursor, """
        SELECT id, kod, ad, aktif_mi
        FROM tanim.uretim_hatlari
        ORDER BY kod
    """, "uretim_hatlari")

    if rows:
        for r in rows:
            print(f"  [{r[0]}] {r[1]:<10} {r[2]:<30} {'Aktif' if r[3] else 'Pasif'}")
    else:
        print("  Uretim hatlari tablosu bos veya yok")

    # ═══════════════════════════════════════════════
    # 6. RECETE ORNEKLERI (ilk 5 urun)
    # ═══════════════════════════════════════════════
    section("6. RECETE ORNEKLERI")
    rows, cols = safe_query(cursor, """
        SELECT TOP 5 u.urun_kodu, u.urun_adi,
               (SELECT COUNT(*) FROM stok.urun_recete r WHERE r.urun_id = u.id AND r.aktif_mi = 1) as adim_sayisi,
               (SELECT SUM(r2.sure_sn) FROM stok.urun_recete r2 WHERE r2.urun_id = u.id AND r2.aktif_mi = 1) as toplam_sure_sn
        FROM stok.urunler u
        WHERE EXISTS (SELECT 1 FROM stok.urun_recete r WHERE r.urun_id = u.id AND r.aktif_mi = 1)
        ORDER BY u.urun_kodu
    """, "recete ornekleri")

    if rows:
        for r in rows:
            print(f"\n  {r[0]} - {r[1] or ''}")
            print(f"    Adim sayisi: {r[2]}, Toplam sure: {r[3] or 0}sn ({(r[3] or 0)//60}dk)")

            # Bu urunun recete adimlari
            adimlar, _ = safe_query(cursor, f"""
                SELECT r.sira_no, r.islem_adi, r.sure_sn,
                       r.sicaklik_hedef, r.akim_hedef,
                       bt.kod as banyo_tipi
                FROM stok.urun_recete r
                LEFT JOIN tanim.banyo_tipleri bt ON r.banyo_tipi_id = bt.id
                WHERE r.urun_id = (SELECT id FROM stok.urunler WHERE urun_kodu = '{r[0]}')
                  AND r.aktif_mi = 1
                ORDER BY r.sira_no
            """, "recete adimlar")

            for a in adimlar:
                sicak = f"{a[3]:.0f}C" if a[3] else "-"
                akim = f"{a[4]:.1f}A" if a[4] else "-"
                print(f"      {a[0]:>2}. {(a[1] or '-'):<25} {(a[2] or 0):>5}sn  Sicak:{sicak:<6} Akim:{akim:<8} Tip:{a[5] or '-'}")
    else:
        print("  Recetesi olan urun bulunamadi")

    # ═══════════════════════════════════════════════
    # 7. KAPLAMA TURLERI
    # ═══════════════════════════════════════════════
    section("7. KAPLAMA TURLERI")
    rows, cols = safe_query(cursor, """
        SELECT id, kod, ad, aktif_mi
        FROM tanim.kaplama_turleri
        ORDER BY kod
    """, "kaplama_turleri")

    if rows:
        for r in rows:
            print(f"  [{r[0]}] {r[1]:<15} {r[2]:<30} {'Aktif' if r[3] else 'Pasif'}")
    else:
        print("  Kaplama turleri tablosu bos veya yok")

    # ═══════════════════════════════════════════════
    # 8. ASKI TIPLERI
    # ═══════════════════════════════════════════════
    section("8. ASKI TIPLERI")
    rows, cols = safe_query(cursor, """
        SELECT id, kod, ad, aktif_mi
        FROM tanim.aski_tipleri
        ORDER BY kod
    """, "aski_tipleri")

    if rows:
        for r in rows:
            print(f"  [{r[0]}] {r[1]:<15} {r[2]:<30} {'Aktif' if r[3] else 'Pasif'}")
    else:
        print("  Aski tipleri tablosu bos veya yok")

    # ═══════════════════════════════════════════════
    # 9. PLC TARIHCE ISTATISTIK
    # ═══════════════════════════════════════════════
    section("9. PLC TARIHCE ISTATISTIK")
    rows, cols = safe_query(cursor, """
        SELECT
            COUNT(*) as toplam,
            MIN(tarih_doldurma) as ilk_kayit,
            MAX(tarih_doldurma) as son_kayit,
            COUNT(DISTINCT kazan_no) as farkli_kazan,
            COUNT(DISTINCT recete_no) as farkli_recete,
            COUNT(DISTINCT bara_no) as farkli_bara
        FROM uretim.plc_tarihce
    """, "plc_tarihce istatistik")

    if rows and rows[0]:
        r = rows[0]
        print(f"  Toplam kayit    : {r[0]:,}")
        print(f"  Ilk kayit       : {r[1]}")
        print(f"  Son kayit       : {r[2]}")
        print(f"  Farkli kazan    : {r[3]}")
        print(f"  Farkli recete   : {r[4]}")
        print(f"  Farkli bara     : {r[5]}")

    # Kazan bazli son 24s istatistik
    rows2, _ = safe_query(cursor, """
        SELECT kazan_no, COUNT(*) as islem,
               AVG(sicaklik) as ort_sicak,
               COUNT(DISTINCT recete_no) as recete_cesit,
               COUNT(DISTINCT bara_no) as bara_cesit
        FROM uretim.plc_tarihce
        WHERE tarih_doldurma >= DATEADD(hour, -24, GETDATE())
        GROUP BY kazan_no
        ORDER BY kazan_no
    """, "24s kazan istatistik")

    if rows2:
        print(f"\n  --- Son 24 Saat Kazan Bazli ---")
        print(f"  {'Kazan':>6} {'Islem':>6} {'OrtSicak':>9} {'RecCesit':>8} {'BaraCesit':>9}")
        for r in rows2:
            print(f"  {r[0]:>6} {r[1]:>6} {(r[2] or 0):>9.1f} {r[3]:>8} {r[4]:>9}")

    # ═══════════════════════════════════════════════
    # 10. PLC'DEKI BENZERSIZ RECETE NUMARALARI
    # ═══════════════════════════════════════════════
    section("10. PLC RECETE NUMARALARI (tarihce)")
    rows, cols = safe_query(cursor, """
        SELECT recete_no, COUNT(*) as kullanim,
               MIN(tarih_doldurma) as ilk, MAX(tarih_doldurma) as son,
               COUNT(DISTINCT kazan_no) as kazan_sayisi
        FROM uretim.plc_tarihce
        WHERE recete_no IS NOT NULL AND recete_no > 0
        GROUP BY recete_no
        ORDER BY kullanim DESC
    """, "recete numaralari")

    if rows:
        print(f"\n  Toplam farkli recete: {len(rows)}")
        print(f"\n  {'Recete':>7} {'Kullanim':>9} {'Kazan':>6} {'Ilk Kullanim':<22} {'Son Kullanim':<22}")
        for r in rows[:30]:  # ilk 30
            print(f"  {r[0]:>7} {r[1]:>9} {r[4]:>6} {str(r[2]):<22} {str(r[3]):<22}")
        if len(rows) > 30:
            print(f"  ... ve {len(rows)-30} recete daha")

    # ═══════════════════════════════════════════════
    # 11. STOK KARTLARINDA ASKI/BARA BILGISI
    # ═══════════════════════════════════════════════
    section("11. STOK KARTLARINDA ASKI/BARA BILGISI OLAN URUNLER")
    rows, cols = safe_query(cursor, """
        SELECT TOP 20 u.urun_kodu, u.urun_adi,
               u.aski_adedi, u.bara_adedi,
               at.kod as aski_tip, at.ad as aski_tip_adi,
               kt.kod as kaplama, kt.ad as kaplama_adi
        FROM stok.urunler u
        LEFT JOIN tanim.aski_tipleri at ON u.aski_tipi_id = at.id
        LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
        WHERE u.aktif_mi = 1 AND (u.aski_adedi > 0 OR u.bara_adedi > 0)
        ORDER BY u.urun_kodu
    """, "aski/bara olan urunler")

    if rows:
        print(f"\n  {'Urun Kodu':<18} {'Aski':>5} {'Bara':>5} {'Aski Tip':<15} {'Kaplama':<15}")
        print(f"  {'-'*18} {'-'*5} {'-'*5} {'-'*15} {'-'*15}")
        for r in rows:
            print(f"  {(r[0] or '-'):<18} {(r[2] or 0):>5} {(r[3] or 0):>5} {(r[4] or '-'):<15} {(r[6] or '-'):<15}")

        # Toplam istatistik
        rows2, _ = safe_query(cursor, """
            SELECT COUNT(*) as toplam,
                   SUM(CASE WHEN aski_adedi > 0 THEN 1 ELSE 0 END) as aski_olan,
                   SUM(CASE WHEN bara_adedi > 0 THEN 1 ELSE 0 END) as bara_olan
            FROM stok.urunler WHERE aktif_mi = 1
        """, "stok istatistik")
        if rows2 and rows2[0]:
            print(f"\n  Toplam aktif urun: {rows2[0][0]}")
            print(f"  Aski adedi tanimli: {rows2[0][1]}")
            print(f"  Bara adedi tanimli: {rows2[0][2]}")
    else:
        print("  Aski/bara bilgisi olan urun bulunamadi")

    # ═══════════════════════════════════════════════
    # 12. ENTEGRASYON TABLOLARI
    # ═══════════════════════════════════════════════
    section("12. ENTEGRASYON - PLC URETIM PLANI")
    rows, cols = safe_query(cursor, """
        SELECT TOP 10 id, is_emri_no, stok_kodu, planlanan_bara, tarih, durum
        FROM entegrasyon.plc_uretim_plani
        ORDER BY id DESC
    """, "plc_uretim_plani")

    if rows:
        print(f"\n  {'ID':>6} {'Is Emri':<15} {'Stok Kodu':<18} {'Bara':>5} {'Tarih':<12} {'Durum':<10}")
        for r in rows:
            print(f"  {r[0]:>6} {(r[1] or '-'):<15} {(r[2] or '-'):<18} {(r[3] or 0):>5} {str(r[4] or '-'):<12} {(r[5] or '-'):<10}")
    else:
        print("  PLC uretim plani tablosu bos veya yok")

    print(f"\n{SEPARATOR}")
    print("  RAPOR TAMAMLANDI")
    print(f"  Bu raporu kaplama planlama modulune aktarmak icin kaydedin.")
    print(SEPARATOR)

    conn.close()


if __name__ == "__main__":
    main()
