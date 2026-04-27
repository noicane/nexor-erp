# -*- coding: utf-8 -*-
"""
NEXOR ERP - Migration Runner
Startup'ta scripts/migrations/NNNN_*.sql dosyalarini sirayla uygular.

Kurallar:
- Dosya ismi: "NNNN_aciklama.sql" (NNNN = 4 basamakli numara)
- Numarali sirayla uygulanir, sistem.migration_log'a yazilir
- Uygulanan migration yeniden calistirilmaz
- 0001_baseline.sql her durumda log'a yazilir (hicbir DDL yok, isaretleme amacli)
- GO ayracli SQL'ler destekler (tedious/pyodbc batch olarak bolerek calistirir)
- Hata olursa logla ve raise - uygulamayi baslatma

Kullanim:
    from core.migration_runner import run_pending_migrations
    run_pending_migrations()  # main.py startup'ta cagrilir
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)


# Migration dosya adi: 0001_baseline.sql gibi
_MIGRATION_RE = re.compile(r'^(\d{4})_([^.]+)\.sql$', re.IGNORECASE)


def _get_migrations_dir() -> Path:
    """scripts/migrations/ dizinini bul"""
    # core/migration_runner.py -> ../scripts/migrations/
    base = Path(__file__).resolve().parent.parent
    return base / 'scripts' / 'migrations'


def _discover_migrations() -> List[Tuple[int, str, Path]]:
    """Dosyalari tara, (numara, dosya_adi, yol) tuple listesini numaraya gore sirali dondur"""
    d = _get_migrations_dir()
    if not d.exists():
        logger.warning("Migration dizini yok: %s", d)
        return []

    found: List[Tuple[int, str, Path]] = []
    for p in d.iterdir():
        if not p.is_file():
            continue
        m = _MIGRATION_RE.match(p.name)
        if not m:
            continue
        no = int(m.group(1))
        found.append((no, p.name, p))

    found.sort(key=lambda t: t[0])

    # Duplicate numara kontrolu
    seen = set()
    for no, name, _ in found:
        if no in seen:
            raise RuntimeError(f"Duplicate migration numarasi: {no}")
        seen.add(no)

    return found


def _checksum(path: Path) -> str:
    """SHA-256 (ilk 16 hex char) - dosya degisirse tesbit etmek icin"""
    try:
        data = path.read_bytes()
        return hashlib.sha256(data).hexdigest()[:16]
    except Exception:
        return ''


def _split_batches(sql: str) -> List[str]:
    """
    SQL metnini 'GO' ayraci ile batch'lere bol.
    GO sadece kendi satirinda olmali (SSMS davranisi).
    """
    batches: List[str] = []
    current: List[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.upper() == 'GO':
            text = '\n'.join(current).strip()
            if text:
                batches.append(text)
            current = []
        else:
            current.append(line)
    # Son batch
    text = '\n'.join(current).strip()
    if text:
        batches.append(text)
    return batches


def _migration_log_exists(cursor) -> bool:
    """sistem.migration_log tablosu var mi?"""
    cursor.execute("""
        SELECT 1 FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE s.name = 'sistem' AND t.name = 'migration_log'
    """)
    return cursor.fetchone() is not None


def _applied_migration_nos(cursor) -> set:
    """Uygulanmis migration numaralarini dondur"""
    if not _migration_log_exists(cursor):
        return set()
    cursor.execute("SELECT migration_no FROM sistem.migration_log")
    return {row[0] for row in cursor.fetchall()}


def _apply_migration(conn, no: int, name: str, path: Path) -> None:
    """Tek bir migration dosyasini uygula"""
    logger.info("[MIGRATION] %04d %s", no, name)
    sql = path.read_text(encoding='utf-8-sig')  # BOM tolerant
    batches = _split_batches(sql)

    cursor = conn.cursor()
    try:
        for batch in batches:
            cursor.execute(batch)
        # Log'a yaz (eger migration_log varsa; 0002'den sonra mevcut)
        if _migration_log_exists(cursor):
            cursor.execute("""
                INSERT INTO sistem.migration_log (migration_no, dosya_adi, checksum, uygulayan)
                VALUES (?, ?, ?, ?)
            """, (no, name, _checksum(path), os.environ.get('USERNAME', 'unknown')))
        conn.commit()
        logger.info("[MIGRATION] %04d OK", no)
    except Exception as e:
        conn.rollback()
        logger.exception("[MIGRATION] %04d HATA: %s", no, e)
        raise


def run_pending_migrations(conn=None) -> int:
    """
    Eksik migration'lari sirayla uygular.
    Geriye uygulanan migration sayisini dondurur.
    """
    # DB baglantisi
    close_after = False
    if conn is None:
        from core.database import get_db_connection
        conn = get_db_connection()
        close_after = True

    try:
        cursor = conn.cursor()
        applied = _applied_migration_nos(cursor)
        all_migrations = _discover_migrations()

        if not all_migrations:
            logger.info("Migration dizini bos")
            return 0

        pending = [(no, name, p) for (no, name, p) in all_migrations if no not in applied]
        if not pending:
            logger.info("Tum migration'lar guncel (%d uygulanmis)", len(applied))
            return 0

        logger.info(
            "Uygulanacak migration: %d (toplam: %d, mevcut: %d)",
            len(pending), len(all_migrations), len(applied)
        )
        count = 0
        for no, name, path in pending:
            _apply_migration(conn, no, name, path)
            count += 1
        return count
    finally:
        if close_after:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    # Manuel calistirma: python -m core.migration_runner
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )
    # Proje kokuni path'e ekle
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    try:
        n = run_pending_migrations()
        print(f"\n[OK] {n} migration uygulandi")
    except Exception as e:
        print(f"\n[HATA] {e}")
        sys.exit(1)
