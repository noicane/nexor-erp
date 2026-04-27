# -*- coding: utf-8 -*-
"""
NEXOR ERP - Recete Maliyet Hesaplayicisi (A2)

Birim parca basina:
  Hammadde   = hammadde_birim_fiyat * hammadde_tuketim_kg
  Iscilik    = (saat_ucreti * cevrim_dk * kisi) / (60 * aski_kapasitesi)
  Enerji     = enerji_kwh_per_saat * (cevrim_dk / 60) * enerji_birim_fiyat / aski_kapasitesi
  Kimyasal   = kimyasal_birim_fiyat * kimyasal_tuketim_kg
  MOH        = (DM + DL + Enerji + Kimyasal) * moh_yuzde / 100  +  moh_sabit_tutar
  Toplam     = DM + DL + Enerji + Kimyasal + MOH

Cache tablosu (maliyet.recete_maliyet_cache) sik sorgu icin tutulur.
A3 (musteri karlilik), B1 (variance), A4 (durus TL kayip) bu cache'i kullanir.

Kullanim:
    from core.maliyet_calculator import ReceteMaliyetCalculator
    calc = ReceteMaliyetCalculator()
    sonuc = calc.hesapla_tek(recete_no=1)        # tek recete
    calc.cache_doldur()                          # tum receteler icin cache yenile
    sonuc = calc.cache_oku(recete_no=1)          # cache'ten oku
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from core.database import get_db_connection

logger = logging.getLogger(__name__)


@dataclass
class ReceteMaliyetSonuc:
    recete_no: int
    recete_adi: str = ''
    cevrim_suresi_dk: float = 0.0
    para_birimi: str = 'TRY'

    # Bilesen bazli (TL/parca)
    m_hammadde: float = 0.0
    m_iscilik: float = 0.0
    m_enerji: float = 0.0
    m_kimyasal: float = 0.0
    m_moh: float = 0.0
    m_toplam: float = 0.0
    m_satis_onerisi: float = 0.0

    # Hesap parametreleri (denetim icin)
    bilesen_id: Optional[int] = None
    hata: str = ''

    @property
    def tamamlandi_mi(self) -> bool:
        return self.bilesen_id is not None and not self.hata


class ReceteMaliyetCalculator:
    """Recete maliyet hesaplama servisi."""

    def hesapla_tek(self, recete_no: int, tarih: date | None = None) -> ReceteMaliyetSonuc:
        """Belirli bir recete icin maliyeti hesapla. Tarih verilmezse bugun."""
        if tarih is None:
            tarih = date.today()

        sonuc = ReceteMaliyetSonuc(recete_no=recete_no)
        conn = get_db_connection()
        try:
            cur = conn.cursor()

            # Recete bilgileri
            cur.execute("""
                SELECT recete_no, recete_adi, ISNULL(toplam_sure_dk, 0)
                FROM kaplama.plc_recete_tanimlari
                WHERE recete_no = ?
            """, recete_no)
            r = cur.fetchone()
            if not r:
                sonuc.hata = f"Recete {recete_no} tanimli degil"
                return sonuc
            sonuc.recete_adi = r[1] or ''
            sonuc.cevrim_suresi_dk = float(r[2] or 0)

            # Aktif bilesen kaydi (gecerlilik araliginda)
            cur.execute("""
                SELECT TOP 1
                    id, hammadde_birim_fiyat, hammadde_tuketim_kg,
                    iscilik_saat_ucreti, iscilik_kisi_sayisi, aski_parca_kapasitesi,
                    enerji_kwh_per_saat, enerji_birim_fiyat,
                    kimyasal_tuketim_kg, kimyasal_birim_fiyat,
                    moh_yuzde, moh_sabit_tutar,
                    kar_marj_yuzde, para_birimi
                FROM maliyet.recete_bilesenleri
                WHERE recete_no = ?
                  AND gecerlilik_baslangic <= ?
                  AND (gecerlilik_bitis IS NULL OR gecerlilik_bitis >= ?)
                ORDER BY gecerlilik_baslangic DESC
            """, recete_no, tarih, tarih)
            b = cur.fetchone()
            if not b:
                sonuc.hata = "Aktif maliyet bileseni tanimli degil"
                return sonuc

            sonuc.bilesen_id = int(b[0])
            sonuc.para_birimi = b[13] or 'TRY'

            hammadde_fiyat = float(b[1] or 0)
            hammadde_tuketim = float(b[2] or 0)
            iscilik_saat = float(b[3] or 0)
            iscilik_kisi = float(b[4] or 1) or 1
            aski_kap = max(1, int(b[5] or 1))
            enerji_kwh = float(b[6] or 0)
            enerji_fiyat = float(b[7] or 0)
            kimyasal_tuketim = float(b[8] or 0)
            kimyasal_fiyat = float(b[9] or 0)
            moh_yuzde = float(b[10] or 0)
            moh_sabit = float(b[11] or 0)
            kar_marj = float(b[12] or 0)

            cevrim_dk = sonuc.cevrim_suresi_dk

            # Hesap
            sonuc.m_hammadde = hammadde_fiyat * hammadde_tuketim

            if cevrim_dk > 0 and aski_kap > 0:
                sonuc.m_iscilik = (iscilik_saat * cevrim_dk * iscilik_kisi) / (60.0 * aski_kap)
                sonuc.m_enerji = (enerji_kwh * (cevrim_dk / 60.0) * enerji_fiyat) / aski_kap

            sonuc.m_kimyasal = kimyasal_fiyat * kimyasal_tuketim

            ara_toplam = sonuc.m_hammadde + sonuc.m_iscilik + sonuc.m_enerji + sonuc.m_kimyasal
            sonuc.m_moh = (ara_toplam * moh_yuzde / 100.0) + moh_sabit

            sonuc.m_toplam = ara_toplam + sonuc.m_moh
            sonuc.m_satis_onerisi = sonuc.m_toplam * (1 + kar_marj / 100.0)

            return sonuc
        finally:
            conn.close()

    def cache_doldur(self, tarih: date | None = None) -> dict:
        """Tum receteler icin maliyet hesaplayip cache tablosuna UPSERT eder."""
        if tarih is None:
            tarih = date.today()

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT recete_no FROM kaplama.plc_recete_tanimlari ORDER BY recete_no")
            recete_no_list = [r[0] for r in cur.fetchall()]
        finally:
            conn.close()

        basari = 0
        eksik = 0
        for rn in recete_no_list:
            sonuc = self.hesapla_tek(rn, tarih)
            if sonuc.tamamlandi_mi:
                self._cache_yaz(sonuc)
                basari += 1
            else:
                eksik += 1
        return {
            'toplam': len(recete_no_list),
            'basari': basari,
            'eksik_bilesen': eksik,
            'tarih': tarih.isoformat(),
        }

    def _cache_yaz(self, s: ReceteMaliyetSonuc) -> None:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                MERGE maliyet.recete_maliyet_cache AS T
                USING (SELECT ? AS recete_no) AS S ON T.recete_no = S.recete_no
                WHEN MATCHED THEN UPDATE SET
                    recete_adi=?, cevrim_suresi_dk=?, m_hammadde=?, m_iscilik=?, m_enerji=?,
                    m_kimyasal=?, m_moh=?, m_toplam=?, m_satis_onerisi=?,
                    para_birimi=?, son_hesap_tarihi=SYSDATETIME(), bilesen_id=?
                WHEN NOT MATCHED THEN INSERT (
                    recete_no, recete_adi, cevrim_suresi_dk,
                    m_hammadde, m_iscilik, m_enerji, m_kimyasal, m_moh, m_toplam, m_satis_onerisi,
                    para_birimi, bilesen_id
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?);
            """,
                s.recete_no,
                # UPDATE
                s.recete_adi, s.cevrim_suresi_dk, s.m_hammadde, s.m_iscilik, s.m_enerji,
                s.m_kimyasal, s.m_moh, s.m_toplam, s.m_satis_onerisi, s.para_birimi, s.bilesen_id,
                # INSERT
                s.recete_no, s.recete_adi, s.cevrim_suresi_dk,
                s.m_hammadde, s.m_iscilik, s.m_enerji, s.m_kimyasal, s.m_moh, s.m_toplam,
                s.m_satis_onerisi, s.para_birimi, s.bilesen_id,
            )
            conn.commit()
        finally:
            conn.close()

    def cache_oku(self, recete_no: int) -> Optional[ReceteMaliyetSonuc]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT recete_no, recete_adi, cevrim_suresi_dk,
                       m_hammadde, m_iscilik, m_enerji, m_kimyasal, m_moh, m_toplam, m_satis_onerisi,
                       para_birimi, bilesen_id
                FROM maliyet.recete_maliyet_cache
                WHERE recete_no = ?
            """, recete_no)
            r = cur.fetchone()
            if not r:
                return None
            s = ReceteMaliyetSonuc(
                recete_no=r[0], recete_adi=r[1] or '', cevrim_suresi_dk=float(r[2] or 0),
                m_hammadde=float(r[3] or 0), m_iscilik=float(r[4] or 0),
                m_enerji=float(r[5] or 0), m_kimyasal=float(r[6] or 0),
                m_moh=float(r[7] or 0), m_toplam=float(r[8] or 0),
                m_satis_onerisi=float(r[9] or 0), para_birimi=r[10] or 'TRY',
                bilesen_id=int(r[11]) if r[11] is not None else None,
            )
            return s
        finally:
            conn.close()

    def cache_listele(self) -> list[ReceteMaliyetSonuc]:
        """Tum recete cache'i don."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT c.recete_no, ISNULL(c.recete_adi, r.recete_adi),
                       c.cevrim_suresi_dk,
                       c.m_hammadde, c.m_iscilik, c.m_enerji, c.m_kimyasal, c.m_moh,
                       c.m_toplam, c.m_satis_onerisi, c.para_birimi, c.bilesen_id
                FROM maliyet.recete_maliyet_cache c
                LEFT JOIN kaplama.plc_recete_tanimlari r ON r.recete_no = c.recete_no
                ORDER BY c.recete_no
            """)
            sonuclar = []
            for r in cur.fetchall():
                sonuclar.append(ReceteMaliyetSonuc(
                    recete_no=r[0], recete_adi=r[1] or '',
                    cevrim_suresi_dk=float(r[2] or 0),
                    m_hammadde=float(r[3] or 0), m_iscilik=float(r[4] or 0),
                    m_enerji=float(r[5] or 0), m_kimyasal=float(r[6] or 0),
                    m_moh=float(r[7] or 0), m_toplam=float(r[8] or 0),
                    m_satis_onerisi=float(r[9] or 0), para_birimi=r[10] or 'TRY',
                    bilesen_id=int(r[11]) if r[11] is not None else None,
                ))
            return sonuclar
        finally:
            conn.close()
