# -*- coding: utf-8 -*-
"""
NEXOR ERP - Numara Uretici (tek nokta sequence wrapper)

siparis.giris_irsaliyeleri tablosuna yazan tum kod yollari (depo_kabul,
apps/irsaliye_okuyucu, gelecekteki mobil/API yollari) numara uretiminde
SADECE bu modulu cagirmali. try/except fallback yazmak yasak: fallback
dali sequence'i advance etmedigi icin UNIQUE KEY 'UQ_giris_irsaliyeleri_no'
ihlali olusur (bkz. memory feedback_seq_no_fallback).
"""
from __future__ import annotations

from datetime import datetime


def yeni_giris_irsaliye_no(cursor) -> str:
    """GRS-YYYYMM-NNNN format, siparis.seq_giris_irsaliye_id sequence'i kullanir.

    Cagri SQL Server tarafinda atomiktir; iki oturum ayni anda cagirsa bile
    farkli numara doner. Fallback YOK; sequence yoksa migration ile yarat.
    """
    cursor.execute("SELECT NEXT VALUE FOR siparis.seq_giris_irsaliye_id")
    next_id = int(cursor.fetchone()[0])
    return f"GRS-{datetime.now().strftime('%Y%m')}-{next_id:04d}"
