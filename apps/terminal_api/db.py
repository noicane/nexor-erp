# -*- coding: utf-8 -*-
"""
NEXOR Terminal API - DB Helper
NEXOR'un core/database baglanti yapisini kullanir.
"""
from __future__ import annotations

import sys
from pathlib import Path

# NEXOR root'unu sys.path'e ekle (apps/terminal_api/.. -> NEXOR root)
_NEXOR_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_NEXOR_ROOT) not in sys.path:
    sys.path.insert(0, str(_NEXOR_ROOT))


def get_conn():
    """NEXOR'un aktif profil ERP DB baglantisini don."""
    from core.database import get_db_connection
    return get_db_connection()


def fetch_all(sql: str, *params) -> list[dict]:
    """SELECT calistir, dict listesi don."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, *params)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.close()
        return rows
    finally:
        conn.close()


def fetch_one(sql: str, *params) -> dict | None:
    rows = fetch_all(sql, *params)
    return rows[0] if rows else None


def execute(sql: str, *params) -> int:
    """INSERT/UPDATE/DELETE - etkilenen satir sayisini don."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, *params)
        conn.commit()
        n = cur.rowcount
        cur.close()
        return n
    finally:
        conn.close()
