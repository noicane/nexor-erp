# -*- coding: utf-8 -*-
"""
NEXOR ERP - SEQUENCE Health Check

Startup'ta SQL Server SEQUENCE objelerinin tablodaki gercek max suffix'in
ilerisinde olup olmadigini dogrular. Geride kalmis bir sequence varsa
otomatik olarak max suffix + 1'e RESTART eder ve uyari log'u yazar.

Niye var: Bir kod yolu yanlislikla MAX(...)+1 ile numara ureterek sequence'i
bypass ederse, sequence tablonun gerisinde kalir ve bir sonraki NEXT VALUE FOR
cagrisi UNIQUE KEY ihlali uretir. Bu kontrol her startup'ta NEXOR'u kendinden
onarir; ek olarak hatayi log'a dusup teshis kolaylastirir.

Calisma noktasi: main.py'de migration_runner sonrasi cagirilir.
"""
from __future__ import annotations

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


# (sequence_full_name, table_full_name, suffix_select_sql)
# suffix_select_sql: SUFFIX integer'i donduren SELECT (tek satir, tek kolon)
_CHECKS: List[Tuple[str, str, str]] = [
    (
        "siparis.seq_giris_irsaliye_id",
        "siparis.giris_irsaliyeleri",
        "SELECT ISNULL(MAX(TRY_CONVERT(INT, RIGHT(irsaliye_no, 4))), 0) "
        "FROM siparis.giris_irsaliyeleri WHERE irsaliye_no LIKE 'GRS-%'",
    ),
]


def _sequence_current_value(cursor, full_name: str):
    # current_value sql_variant tipinde; pyodbc okuyamiyor -> BIGINT'e cast.
    schema, name = full_name.split(".", 1)
    cursor.execute(
        """
        SELECT CAST(current_value AS BIGINT) FROM sys.sequences
        WHERE name = ? AND SCHEMA_NAME(schema_id) = ?
        """,
        (name, schema),
    )
    row = cursor.fetchone()
    return None if row is None else int(row[0])


def _restart_sequence(cursor, full_name: str, value: int) -> None:
    # Sequence isimleri whitelist'ten geliyor, ALTER SEQUENCE parametre kabul
    # etmedigi icin string concat zorunlu.
    cursor.execute(f"ALTER SEQUENCE {full_name} RESTART WITH {int(value)}")


def check_and_resync_sequences(conn=None) -> int:
    """Geride kalmis sequence'leri tablo max suffix + 1'e ceker.

    Returns: resync edilen sequence sayisi.
    """
    close_after = False
    if conn is None:
        from core.database import get_db_connection
        conn = get_db_connection()
        close_after = True

    resynced = 0
    try:
        cursor = conn.cursor()
        for seq_name, table_name, suffix_sql in _CHECKS:
            try:
                current = _sequence_current_value(cursor, seq_name)
                if current is None:
                    logger.warning("[SEQ-HEALTH] %s yok, atlandi", seq_name)
                    continue

                cursor.execute(suffix_sql)
                row = cursor.fetchone()
                max_suffix = int(row[0]) if row and row[0] is not None else 0

                if current <= max_suffix:
                    yeni = max_suffix + 1
                    logger.warning(
                        "[SEQ-HEALTH] %s geride (current=%d, table_max=%d) -> RESTART WITH %d (%s)",
                        seq_name, current, max_suffix, yeni, table_name,
                    )
                    _restart_sequence(cursor, seq_name, yeni)
                    conn.commit()
                    resynced += 1
                else:
                    logger.debug(
                        "[SEQ-HEALTH] %s OK (current=%d > table_max=%d)",
                        seq_name, current, max_suffix,
                    )
            except Exception as e:
                conn.rollback()
                logger.exception("[SEQ-HEALTH] %s kontrol hatasi: %s", seq_name, e)
        return resynced
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
    n = check_and_resync_sequences()
    print(f"\n[OK] {n} sequence resync edildi")
