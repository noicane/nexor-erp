# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Bayi Master DB Sync (M2.7)

Aktif kuruluma ait config.json profil verisini bayinin merkezi master DB'sine
(redline.musterilerim) push/pull yapar.

Calisma mantigi:
1) Master baglanti bilgisi: config.json -> top-level 'redline_master' (global).
   Yoksa best-effort olarak get_db_connection() (yerel DB) kullanir.
2) push_musteri(kod): Aktif config'teki kod profilini UPSERT eder.
3) push_all(): Tum profilleri sirayla push eder.
4) pull_all(): master'dan tum kayitlari cek (gelistirme amacli; UI'a entegre degil).

Tarih: 2026-04-27
"""
from __future__ import annotations

import json
import logging
import socket
import os
from datetime import datetime
from typing import Optional, Any

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Master baglantisi
# ------------------------------------------------------------------

def _get_master_connection():
    """Master DB baglantisini kur. Once config'teki redline_master ayarini dene,
    yoksa yerel DB'yi kullan (bayi == musteri durumu).
    """
    try:
        from core.external_config import config_manager
        master = config_manager.get('redline_master') or {}
    except Exception:
        master = {}

    # Master config dolu mu?
    if master and master.get('server') and master.get('database'):
        try:
            import pyodbc
            from core.external_config import decode_password
            cs_parts = [
                f"DRIVER={{{master.get('driver', 'ODBC Driver 18 for SQL Server')}}}",
                f"SERVER={master['server']}",
                f"DATABASE={master['database']}",
                "Encrypt=no", "TrustServerCertificate=yes",
            ]
            if master.get('trusted_connection'):
                cs_parts.append("Trusted_Connection=yes")
            else:
                cs_parts.append(f"UID={master.get('user', '')}")
                pwd = decode_password(master.get('password', '') or '')
                cs_parts.append(f"PWD={pwd}")
            cs = ";".join(cs_parts) + ";"
            return pyodbc.connect(cs, timeout=int(master.get('timeout', 8)))
        except Exception as e:
            logger.warning("Master DB baglanti hatasi (yerel DB'ye dusuyor): %s", e)

    # Fallback: yerel DB
    from core.database import get_db_connection
    return get_db_connection()


def _ensure_table(conn) -> bool:
    """redline.musterilerim tablosu var mi kontrol et; yoksa False don."""
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM sys.tables t
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = 'redline' AND t.name = 'musterilerim'
        """)
        n = cur.fetchone()[0]
        cur.close()
        return n > 0
    except Exception as e:
        logger.warning("redline tablosu kontrol hatasi: %s", e)
        return False


def _date_or_none(s: Any) -> Optional[str]:
    """'YYYY-MM-DD' string'ini SQL gecerli date string'i yap; bos/'2000-01-01' -> None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()[:10]
    if not s or s == '2000-01-01':
        return None
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except Exception:
        return None


def _safe_float(v) -> Optional[float]:
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _profil_to_row(kod: str, p: dict) -> dict:
    a = p.get('anlasma') or {}
    b = p.get('bakim') or {}
    k = p.get('kurulum') or {}
    fin = p.get('finansal') or {}
    il = p.get('iletisim') or {}
    v = p.get('vergi') or {}
    rep = p.get('raporlama') or {}

    # JSON snapshot'a sifre/secret hariciyle yaz
    snap = dict(p)
    if isinstance(snap.get('database'), dict):
        snap['database'] = {k2: v2 for k2, v2 in snap['database'].items() if k2 != 'password'}

    return {
        'musteri_kodu': kod[:60],
        'musteri_adi': (p.get('musteri_adi') or kod)[:200],
        'kisa_ad': (p.get('kisa_ad') or '')[:60] or None,
        'musteri_tipi': (p.get('musteri_tipi') or '')[:20] or None,
        'durum': (p.get('durum') or '')[:20] or None,
        'segment': (p.get('segment') or '')[:40] or None,
        'sektor': (p.get('sektor') or '')[:80] or None,
        'sorumlu_personel': (rep.get('sorumlu_personel') or '')[:80] or None,
        'vkn_tckn': (v.get('vkn_tckn') or '')[:20] or None,
        'telefon': (il.get('telefon') or '')[:40] or None,
        'email': (il.get('email') or '')[:120] or None,
        'web': (il.get('web') or '')[:120] or None,
        'sozlesme_no': (a.get('sozlesme_no') or '')[:50] or None,
        'anlasma_baslangic': _date_or_none(a.get('baslangic_tarihi')),
        'anlasma_bitis': _date_or_none(a.get('bitis_tarihi')),
        'lisans_tipi': (a.get('lisans_tipi') or '')[:20] or None,
        'bedel': _safe_float(a.get('bedel')),
        'para_birimi': (a.get('para_birimi') or '')[:10] or None,
        'kullanici_limiti': int(a.get('kullanici_limiti') or 0),
        'bakim_var': 1 if b.get('var') else 0,
        'bakim_aylik_ucret': _safe_float(b.get('aylik_ucret')),
        'bakim_bitis': _date_or_none(b.get('bitis_tarihi')),
        'kurulum_tipi': (k.get('tip') or '')[:20] or None,
        'nexor_versiyonu': (k.get('nexor_versiyonu') or '')[:40] or None,
        'sql_surumu': (k.get('sql_surumu') or '')[:80] or None,
        'son_guncelleme': _date_or_none(k.get('son_guncelleme_tarihi')),
        'zirve_cari_kodu': (fin.get('zirve_cari_kodu') or '')[:40] or None,
        'cari_bakiye': _safe_float(fin.get('cari_bakiye')),
        'kredi_limiti': _safe_float(fin.get('kredi_limiti')),
        'risk_skoru': (fin.get('risk_skoru') or '')[:20] or None,
        'profil_json': json.dumps(snap, ensure_ascii=False, default=str),
        'son_sync_pc': socket.gethostname()[:120],
        'son_sync_kullanici': (os.environ.get('USERNAME') or os.environ.get('USER') or '')[:80] or None,
    }


# ------------------------------------------------------------------
# UPSERT
# ------------------------------------------------------------------

_UPSERT_SQL = """
MERGE redline.musterilerim AS T
USING (SELECT ? AS musteri_kodu) AS S
ON T.musteri_kodu = S.musteri_kodu
WHEN MATCHED THEN UPDATE SET
    musteri_adi=?, kisa_ad=?, musteri_tipi=?, durum=?, segment=?, sektor=?, sorumlu_personel=?,
    vkn_tckn=?, telefon=?, email=?, web=?,
    sozlesme_no=?, anlasma_baslangic=?, anlasma_bitis=?, lisans_tipi=?, bedel=?, para_birimi=?, kullanici_limiti=?,
    bakim_var=?, bakim_aylik_ucret=?, bakim_bitis=?,
    kurulum_tipi=?, nexor_versiyonu=?, sql_surumu=?, son_guncelleme=?,
    zirve_cari_kodu=?, cari_bakiye=?, kredi_limiti=?, risk_skoru=?,
    profil_json=?, son_sync_tarihi=SYSDATETIME(), son_sync_pc=?, son_sync_kullanici=?
WHEN NOT MATCHED THEN INSERT (
    musteri_kodu, musteri_adi, kisa_ad, musteri_tipi, durum, segment, sektor, sorumlu_personel,
    vkn_tckn, telefon, email, web,
    sozlesme_no, anlasma_baslangic, anlasma_bitis, lisans_tipi, bedel, para_birimi, kullanici_limiti,
    bakim_var, bakim_aylik_ucret, bakim_bitis,
    kurulum_tipi, nexor_versiyonu, sql_surumu, son_guncelleme,
    zirve_cari_kodu, cari_bakiye, kredi_limiti, risk_skoru,
    profil_json, son_sync_pc, son_sync_kullanici
) VALUES (
    ?,?,?,?,?,?,?,?,
    ?,?,?,?,
    ?,?,?,?,?,?,?,
    ?,?,?,
    ?,?,?,?,
    ?,?,?,?,
    ?,?,?
);
"""


def push_musteri(kod: str) -> bool:
    """Verilen kod profilini master'a UPSERT eder."""
    try:
        from core.external_config import config_manager
        p = config_manager.get_profile(kod)
        if p is None:
            logger.info("push_musteri: profil bulunamadi (%s)", kod)
            return False
    except Exception as e:
        logger.warning("push_musteri config okuma hatasi: %s", e)
        return False

    row = _profil_to_row(kod, p)

    try:
        conn = _get_master_connection()
    except Exception as e:
        logger.info("push_musteri: master baglanti yok (%s) - atlandi", e)
        return False

    if not _ensure_table(conn):
        try:
            conn.close()
        except Exception:
            pass
        logger.info("push_musteri: redline.musterilerim tablosu yok (migration calistirilmadi mi?)")
        return False

    try:
        cur = conn.cursor()
        # MATCH parametreleri (UPDATE) + USING anahtari + INSERT parametreleri
        # Toplam: 1 (USING) + 32 (UPDATE) + 33 (INSERT) = 66
        match_params = [
            row['musteri_kodu'],
            # UPDATE alanlari (32 kolon)
            row['musteri_adi'], row['kisa_ad'], row['musteri_tipi'], row['durum'],
            row['segment'], row['sektor'], row['sorumlu_personel'],
            row['vkn_tckn'], row['telefon'], row['email'], row['web'],
            row['sozlesme_no'], row['anlasma_baslangic'], row['anlasma_bitis'],
            row['lisans_tipi'], row['bedel'], row['para_birimi'], row['kullanici_limiti'],
            row['bakim_var'], row['bakim_aylik_ucret'], row['bakim_bitis'],
            row['kurulum_tipi'], row['nexor_versiyonu'], row['sql_surumu'], row['son_guncelleme'],
            row['zirve_cari_kodu'], row['cari_bakiye'], row['kredi_limiti'], row['risk_skoru'],
            row['profil_json'], row['son_sync_pc'], row['son_sync_kullanici'],
        ]
        insert_params = [
            row['musteri_kodu'], row['musteri_adi'], row['kisa_ad'], row['musteri_tipi'],
            row['durum'], row['segment'], row['sektor'], row['sorumlu_personel'],
            row['vkn_tckn'], row['telefon'], row['email'], row['web'],
            row['sozlesme_no'], row['anlasma_baslangic'], row['anlasma_bitis'],
            row['lisans_tipi'], row['bedel'], row['para_birimi'], row['kullanici_limiti'],
            row['bakim_var'], row['bakim_aylik_ucret'], row['bakim_bitis'],
            row['kurulum_tipi'], row['nexor_versiyonu'], row['sql_surumu'], row['son_guncelleme'],
            row['zirve_cari_kodu'], row['cari_bakiye'], row['kredi_limiti'], row['risk_skoru'],
            row['profil_json'], row['son_sync_pc'], row['son_sync_kullanici'],
        ]
        cur.execute(_UPSERT_SQL, *match_params, *insert_params)
        conn.commit()
        cur.close()

        # Sync log
        try:
            cur2 = conn.cursor()
            cur2.execute(
                "INSERT INTO redline.sync_log (musteri_kodu, islem, sonuc, mesaj, kaynak_pc) "
                "VALUES (?,?,?,?,?)",
                row['musteri_kodu'], 'PUSH', 'BASARILI',
                f"Profile boyutu: {len(row['profil_json'])} byte",
                row['son_sync_pc'],
            )
            conn.commit()
            cur2.close()
        except Exception:
            pass

        conn.close()
        logger.info("push_musteri OK: %s", kod)
        return True
    except Exception as e:
        logger.error("push_musteri UPSERT hatasi (%s): %s", kod, e)
        # sync_log'a hata yaz
        try:
            cur2 = conn.cursor()
            cur2.execute(
                "INSERT INTO redline.sync_log (musteri_kodu, islem, sonuc, mesaj, kaynak_pc) "
                "VALUES (?,?,?,?,?)",
                row['musteri_kodu'], 'PUSH', 'HATA', str(e)[:1500],
                row['son_sync_pc'],
            )
            conn.commit()
            cur2.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        return False


def push_all() -> dict:
    """Tum profilleri master'a push et."""
    try:
        from core.external_config import config_manager
        kodlar = config_manager.list_profiles()
    except Exception as e:
        return {'basari': 0, 'hata': 0, 'mesaj': str(e)}

    basari = 0
    hata = 0
    for k in kodlar:
        if push_musteri(k):
            basari += 1
        else:
            hata += 1
    return {'basari': basari, 'hata': hata, 'toplam': len(kodlar)}
