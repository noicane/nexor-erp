# -*- coding: utf-8 -*-
"""
NEXOR ERP - Modul Lisans Sync (Config -> DB)

Bayi tarafindan `config.json profiles[active_profile].moduller_aktif` altinda
saklanan musteri-spesifik modul lisanslarini, NEXOR startup'ta DB'deki
`lisans.modul_durumlari` tablosuna yansitir.

Mantik:
- Her modul kaydi icin {aktif, bitis_tarihi, notlar} alanlari config'te varsa
  DB'ye UPSERT edilir (UPDATE varsa, INSERT yoksa).
- Config'te bulunmayan modul DB'de oldugu gibi kalir (kismi override).
- Config'te `aktif` belirtilmemisse o satir atlanir (bos dict = no-op).

Cagri yeri: main.py startup'ta migration_runner sonrasi, ModulServisi.yenile()
ONCESI calisir; boylece in-memory cache zaten guncel DB'yi okur.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _parse_date(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except Exception:
        return None


def sync_config_to_db(conn=None) -> int:
    """Aktif profilin moduller_aktif config'ini lisans.modul_durumlari'na yansit.

    Returns: yansitilan modul satiri sayisi.
    """
    from core.external_config import config_manager

    moduller = (config_manager.get('moduller_aktif') or {})
    if not isinstance(moduller, dict) or not moduller:
        logger.debug("[MODUL-SYNC] Aktif profilde moduller_aktif bos, sync atlandi.")
        return 0

    close_after = False
    if conn is None:
        from core.database import get_db_connection
        conn = get_db_connection()
        close_after = True

    yansitilan = 0
    try:
        cur = conn.cursor()
        for kod, ayar in moduller.items():
            if not isinstance(ayar, dict):
                continue
            if 'aktif' not in ayar:
                continue  # parsiyel kayit, atla

            aktif = 1 if bool(ayar.get('aktif')) else 0
            bitis = _parse_date(str(ayar.get('bitis_tarihi') or ''))
            notlar = ayar.get('notlar') or None

            try:
                cur.execute(
                    """
                    UPDATE lisans.modul_durumlari
                    SET aktif = ?, bitis_tarihi = ?, notlar = ?
                    WHERE modul_kodu = ?
                    """,
                    (aktif, bitis, notlar, kod),
                )
                if cur.rowcount == 0:
                    cur.execute(
                        """
                        INSERT INTO lisans.modul_durumlari
                            (modul_kodu, aktif, bitis_tarihi, notlar)
                        VALUES (?, ?, ?, ?)
                        """,
                        (kod, aktif, bitis, notlar),
                    )
                yansitilan += 1
            except Exception as e:
                logger.warning("[MODUL-SYNC] %s yansitilamadi: %s", kod, e)
        conn.commit()
        if yansitilan:
            logger.info("[MODUL-SYNC] %d modul config -> DB yansitildi", yansitilan)
        return yansitilan
    finally:
        if close_after:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    n = sync_config_to_db()
    print(f"\n[OK] {n} modul yansitildi")
