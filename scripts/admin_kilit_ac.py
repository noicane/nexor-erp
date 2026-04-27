# -*- coding: utf-8 -*-
"""
Admin hesabinin kilidini acar ve basarisiz giris sayacini sifirlar.
Kullanim: python scripts/admin_kilit_ac.py [kullanici_adi]
Varsayilan kullanici: admin
"""
import sys
from pathlib import Path

# Proje koküne ekle
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import get_db_connection


def main():
    kullanici_adi = sys.argv[1] if len(sys.argv) > 1 else "admin"

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, kullanici_adi, hesap_kilitli_mi, basarisiz_giris_sayisi, aktif_mi
            FROM sistem.kullanicilar
            WHERE kullanici_adi = ?
        """, (kullanici_adi,))
        row = cursor.fetchone()

        if not row:
            print(f"HATA: '{kullanici_adi}' kullanicisi bulunamadi.")
            return 1

        print(f"Once: id={row[0]}, kullanici={row[1]}, kilitli={row[2]}, basarisiz={row[3]}, aktif={row[4]}")

        cursor.execute("""
            UPDATE sistem.kullanicilar
            SET hesap_kilitli_mi = 0,
                basarisiz_giris_sayisi = 0
            WHERE kullanici_adi = ?
        """, (kullanici_adi,))
        conn.commit()

        cursor.execute("""
            SELECT hesap_kilitli_mi, basarisiz_giris_sayisi
            FROM sistem.kullanicilar
            WHERE kullanici_adi = ?
        """, (kullanici_adi,))
        row2 = cursor.fetchone()
        print(f"Sonra: kilitli={row2[0]}, basarisiz={row2[1]}")
        print(f"OK: '{kullanici_adi}' hesabi acildi.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
