# -*- coding: utf-8 -*-
"""
NEXOR - Tek seferlik migration: iade_irsaliye_satirlar kolon genislet
- stok_adi: NVARCHAR(200) -> NVARCHAR(250)
- iade_nedeni: NVARCHAR(200) -> NVARCHAR(500)

Calistir: python scripts/run_migration_iade_kolon.py
"""
import sys
from pathlib import Path

# Proje kokuni path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_db_connection


MIGRATIONS = [
    # (ad, kontrol_sorgu, alter_sorgu)
    (
        "stok_adi -> NVARCHAR(250)",
        """
        SELECT max_length FROM sys.columns
        WHERE object_id = OBJECT_ID('siparis.iade_irsaliye_satirlar')
          AND name = 'stok_adi'
        """,
        "ALTER TABLE siparis.iade_irsaliye_satirlar ALTER COLUMN stok_adi NVARCHAR(250) NULL",
        500,  # beklenen yeni max_length (NVARCHAR(250) = 500 byte)
    ),
    (
        "iade_nedeni -> NVARCHAR(500)",
        """
        SELECT max_length FROM sys.columns
        WHERE object_id = OBJECT_ID('siparis.iade_irsaliye_satirlar')
          AND name = 'iade_nedeni'
        """,
        "ALTER TABLE siparis.iade_irsaliye_satirlar ALTER COLUMN iade_nedeni NVARCHAR(500) NULL",
        1000,  # NVARCHAR(500) = 1000 byte
    ),
]


def main():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        for ad, check_sql, alter_sql, beklenen in MIGRATIONS:
            cur.execute(check_sql)
            row = cur.fetchone()
            mevcut = row[0] if row else None

            if mevcut == beklenen:
                print(f"[SKIP] {ad} - zaten guncel (max_length={mevcut})")
                continue
            if mevcut is None:
                print(f"[WARN] {ad} - kolon bulunamadi, atlaniyor")
                continue

            print(f"[RUN ] {ad} (mevcut max_length={mevcut})")
            cur.execute(alter_sql)
            conn.commit()
            print(f"       OK")
        print("\nMigration tamamlandi.")
    except Exception as e:
        conn.rollback()
        print(f"\n[HATA] {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
