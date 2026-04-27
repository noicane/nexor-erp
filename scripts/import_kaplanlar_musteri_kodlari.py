# -*- coding: utf-8 -*-
"""
Kaplanlar Sogutma - Excel'den musteri kod eslestirmesi import.

Kaynak: 'Atlas Kataforez Guncel Fiyat Listesi Dosyasinin Kopyasi.xlsx'
Kolon yapisi:
  1 (Malzeme)             -> musteri_parca_no  (ornek: 100001015589)
  2 (Malzeme Uzun Tanimi) -> referans, DB'ye yazilmaz
  3 (Cizim numarasi)      -> bizim urun_kodu   (ornek: K533)

Hedef: stok.urunler.musteri_parca_no + cari_id guncelle.

Guvenlik:
- Mevcut cari_id farkli (Kaplanlar degil) ise o satiri atla (rapor)
- Mevcut cari_id null veya Kaplanlar ise guncelle
- urun_kodu bulunamazsa raporla

Calistir (ONCE DRY-RUN):
    python scripts/import_kaplanlar_musteri_kodlari.py
    python scripts/import_kaplanlar_musteri_kodlari.py --apply
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import openpyxl
from core.database import get_db_connection


EXCEL_PATH = r"C:\Users\maydi\Desktop\Atlas Kataforez Güncel Fiyat Listesi Dosyasının Kopyası.xlsx"
CARI_ID = 6298  # KAPLANLAR SOĞUTMA SAN.TİC.A.Ş.
CARI_UNVAN = "KAPLANLAR SOĞUTMA SAN.TİC.A.Ş."


def main(apply_changes: bool = False):
    print(f"Excel: {EXCEL_PATH}")
    print(f"Hedef cari: {CARI_UNVAN} (id={CARI_ID})")
    print(f"Mod: {'UYGULA' if apply_changes else 'DRY-RUN (veri degistirmez)'}")
    print("-" * 70)

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active

    conn = get_db_connection()
    cur = conn.cursor()

    updated = 0
    already_same = 0
    skipped_other_cari = []
    not_found = []
    empty_rows = 0
    musteri_kod_conflict = []  # Ayni musteri kodu farkli urunlerde mi?

    musteri_kod_seen: dict[str, str] = {}  # musteri_kod -> urun_kodu ilk gecisi

    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        musteri_kod = row[0]
        musteri_ad = row[1]
        cizim = row[2]

        if not cizim or not musteri_kod:
            empty_rows += 1
            continue

        cizim = str(cizim).strip()
        musteri_kod = str(musteri_kod).strip()

        # Excel icinde duplicate musteri kodu var mi?
        if musteri_kod in musteri_kod_seen and musteri_kod_seen[musteri_kod] != cizim:
            musteri_kod_conflict.append(
                (musteri_kod, musteri_kod_seen[musteri_kod], cizim)
            )
        else:
            musteri_kod_seen[musteri_kod] = cizim

        # Bizim DB'de urun_kodu (cizim) ara
        cur.execute("""
            SELECT id, urun_adi, cari_id, musteri_parca_no
            FROM stok.urunler
            WHERE urun_kodu = ?
        """, (cizim,))
        r = cur.fetchone()
        if not r:
            not_found.append((cizim, musteri_kod, (musteri_ad or "")[:40]))
            continue

        urun_id, urun_adi, mevcut_cari, mevcut_mk = r

        # Farkli cari varsa skip
        if mevcut_cari and int(mevcut_cari) != CARI_ID:
            skipped_other_cari.append((cizim, urun_adi[:40], mevcut_cari))
            continue

        # Ayni bilgi zaten varsa sayim
        if (mevcut_cari == CARI_ID
                and (mevcut_mk or "").strip() == musteri_kod):
            already_same += 1
            continue

        # UPDATE
        if apply_changes:
            cur.execute("""
                UPDATE stok.urunler
                SET musteri_parca_no = ?, cari_id = ?
                WHERE id = ?
            """, (musteri_kod[:100], CARI_ID, urun_id))
        updated += 1

    if apply_changes:
        conn.commit()
        print("[COMMIT] Degisiklikler kalici olarak kaydedildi.")
    else:
        conn.rollback()
        print("[DRY-RUN] Hicbir veri degismedi. --apply ile gercekten yaz.")

    conn.close()

    print()
    print("=" * 70)
    print(f"Ozet:")
    print(f"  Guncellenen (yeni eslesme): {updated}")
    print(f"  Zaten dogru (atlandi):      {already_same}")
    print(f"  Farkli cari (atlandi):      {len(skipped_other_cari)}")
    print(f"  Bulunamayan cizim:          {len(not_found)}")
    print(f"  Bos satir:                  {empty_rows}")
    print(f"  Excel ici duplicate:        {len(musteri_kod_conflict)}")

    if skipped_other_cari:
        print(f"\n[!] Farkli cariye atanmis {len(skipped_other_cari)} urun (atlandi):")
        for cizim, ad, cari in skipped_other_cari[:5]:
            print(f"      {cizim}: {ad} (mevcut cari_id={cari})")
        if len(skipped_other_cari) > 5:
            print(f"      ... ve {len(skipped_other_cari) - 5} tane daha")

    if not_found:
        print(f"\n[!] Sistemde bulunamayan {len(not_found)} cizim kodu:")
        for cizim, mk, ad in not_found[:10]:
            print(f"      {cizim}: {mk} - {ad}")
        if len(not_found) > 10:
            print(f"      ... ve {len(not_found) - 10} tane daha")

    if musteri_kod_conflict:
        print(f"\n[!] Excel'de {len(musteri_kod_conflict)} duplicate musteri kodu:")
        for mk, ilk, sonra in musteri_kod_conflict[:5]:
            print(f"      {mk}: {ilk} <-> {sonra}")


if __name__ == "__main__":
    apply_changes = "--apply" in sys.argv
    main(apply_changes=apply_changes)
