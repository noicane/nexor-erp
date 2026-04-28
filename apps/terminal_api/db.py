# -*- coding: utf-8 -*-
"""
NEXOR Terminal API - DB Helper

Iki mod desteklenir:
  1. Standalone: .env'de DB_SERVER/DB_USER/DB_PASSWORD varsa direkt pyodbc baglantisi
     (server deploy icin; NEXOR core'a ihtiyac yoktur)
  2. Embedded: NEXOR root icinden cagriliyorsa core.database fallback
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

import pyodbc


def _conn_from_env():
    server = os.environ.get("DB_SERVER") or os.environ.get("NEXOR_DB_SERVER")
    database = os.environ.get("DB_NAME") or os.environ.get("NEXOR_DB_NAME") or "AtmoLogicERP"
    user = os.environ.get("DB_USER") or os.environ.get("NEXOR_DB_USER")
    password = os.environ.get("DB_PASSWORD") or os.environ.get("NEXOR_DB_PASS")
    driver = os.environ.get("DB_DRIVER", "ODBC Driver 18 for SQL Server")

    if not (server and user and password):
        return None

    return pyodbc.connect(
        f"DRIVER={{{driver}}};"
        f"SERVER={server};DATABASE={database};"
        f"UID={user};PWD={password};"
        f"Encrypt=no;TrustServerCertificate=yes;"
        f"Connection Timeout=10",
        autocommit=False,
    )


def get_conn():
    """ERP DB baglantisi - once .env, sonra NEXOR core fallback."""
    conn = _conn_from_env()
    if conn is not None:
        return conn

    _NEXOR_ROOT = Path(__file__).resolve().parent.parent.parent
    if str(_NEXOR_ROOT) not in sys.path:
        sys.path.insert(0, str(_NEXOR_ROOT))
    from core.database import get_db_connection
    return get_db_connection()


def fetch_all(sql: str, *params) -> list[dict]:
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
