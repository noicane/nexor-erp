# -*- coding: utf-8 -*-
"""
NEXOR ERP - OEE Hesaplayicisi (Genel Ekipman Etkinligi)

OEE = Kullanilabilirlik x Performans x Kalite

- Kullanilabilirlik = (Planlanan Sure - OEE Etkili Durus) / Planlanan Sure
- Performans = (Standart Cevrim Suresi x Uretilen) / Calisma Suresi
- Kalite = (Uretilen - Red) / Uretilen

Veri kaynaklari:
- tanim.uretim_hatlari (devir_suresi_dk, kapasite)
- tanim.durus_nedenleri (oee_etkisi flag)
- uretim.durus_kayitlari (gercek durus)
- uretim.plc_cache / plc_tarihce (uretilen bara/parca)
- kalite.uretim_redler (red miktari)
- tanim.vardiyalar (planlanan vardiya saatleri)

Kullanim:
    from core.oee_calculator import OEECalculator

    calc = OEECalculator()
    sonuc = calc.hesapla(
        baslangic_tarihi='2026-04-01',
        bitis_tarihi='2026-04-27',
        hat_id=None,  # Hepsi icin None
    )
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Optional

from core.database import get_db_connection

logger = logging.getLogger(__name__)


# ============================================================================
# Veri yapilari
# ============================================================================

@dataclass
class OEESonuc:
    """Tek bir hat/donem icin OEE hesabi."""
    hat_id: int
    hat_kodu: str
    hat_adi: str
    baslangic: date
    bitis: date

    # Sureler (dakika)
    planlanan_sure_dk: int = 0
    calisma_sure_dk: int = 0       # Planlanan - OEE etkili durus
    durus_oee_etkili_dk: int = 0
    durus_planli_dk: int = 0       # Mola, vardiya degisimi vb. - OEE'den dusulmez
    durus_toplam_dk: int = 0

    # Uretim
    uretilen_adet: int = 0
    standart_cevrim_dk: float = 0.0  # Bir bara/parca icin sn->dk
    teorik_uretim_adet: float = 0.0  # Calisma sure / standart cevrim

    # Kalite
    red_adet: int = 0
    onayli_adet: int = 0

    # Yuzdeler
    kullanilabilirlik: float = 0.0
    performans: float = 0.0
    kalite: float = 0.0
    oee: float = 0.0

    def hesapla(self) -> None:
        """Yuzdeleri olusturulan ham verilerden hesapla."""
        # Kullanilabilirlik
        if self.planlanan_sure_dk > 0:
            self.calisma_sure_dk = max(0, self.planlanan_sure_dk - self.durus_oee_etkili_dk)
            self.kullanilabilirlik = self.calisma_sure_dk / self.planlanan_sure_dk
        else:
            self.calisma_sure_dk = 0
            self.kullanilabilirlik = 0.0

        # Performans
        if self.standart_cevrim_dk > 0 and self.calisma_sure_dk > 0:
            self.teorik_uretim_adet = self.calisma_sure_dk / self.standart_cevrim_dk
            if self.teorik_uretim_adet > 0:
                self.performans = min(1.0, self.uretilen_adet / self.teorik_uretim_adet)
            else:
                self.performans = 0.0
        else:
            self.performans = 0.0

        # Kalite
        if self.uretilen_adet > 0:
            self.onayli_adet = max(0, self.uretilen_adet - self.red_adet)
            self.kalite = self.onayli_adet / self.uretilen_adet
        else:
            self.onayli_adet = 0
            self.kalite = 0.0

        # OEE
        self.oee = self.kullanilabilirlik * self.performans * self.kalite


@dataclass
class DurusKayipPareto:
    """6 buyuk kayip kategorisi icin pareto verisi."""
    kategori: str
    neden_kodu: str
    neden_adi: str
    sure_dk: int = 0
    sayi: int = 0
    yuzde: float = 0.0  # Toplam OEE etkili duruslar icindeki pay


# ============================================================================
# Hesaplayici
# ============================================================================

class OEECalculator:
    """OEE + 6 buyuk kayip pareto hesaplama servisi."""

    def hesapla(
        self,
        baslangic_tarihi: str | date,
        bitis_tarihi: str | date,
        hat_id: Optional[int] = None,
        vardiya_id: Optional[int] = None,
    ) -> list[OEESonuc]:
        """Verilen donemde hat bazli OEE listesi don."""
        if isinstance(baslangic_tarihi, str):
            baslangic_tarihi = datetime.strptime(baslangic_tarihi[:10], "%Y-%m-%d").date()
        if isinstance(bitis_tarihi, str):
            bitis_tarihi = datetime.strptime(bitis_tarihi[:10], "%Y-%m-%d").date()

        gun_sayisi = max(1, (bitis_tarihi - baslangic_tarihi).days + 1)
        conn = get_db_connection()
        try:
            hatlar = self._hatlari_getir(conn, hat_id)
            vardiya_dk = self._vardiya_dakikasi_getir(conn, vardiya_id)
            sonuclar: list[OEESonuc] = []
            for h in hatlar:
                s = OEESonuc(
                    hat_id=h["id"],
                    hat_kodu=h["kod"] or "",
                    hat_adi=h["ad"] or "",
                    baslangic=baslangic_tarihi,
                    bitis=bitis_tarihi,
                )
                # Planlanan sure: vardiya x gun_sayisi (vardiya yoksa 24sa)
                s.planlanan_sure_dk = (vardiya_dk or (24 * 60)) * gun_sayisi

                # Standart cevrim: hatlar.devir_suresi_dk (dk cinsinden zaten)
                s.standart_cevrim_dk = float(h.get("devir_suresi_dk") or 0) or self._varsayilan_cevrim_recete(conn, h["id"])

                # Duruslar
                durus = self._durus_topla(conn, h["id"], baslangic_tarihi, bitis_tarihi)
                s.durus_oee_etkili_dk = durus["oee_etkili_dk"]
                s.durus_planli_dk = durus["planli_dk"]
                s.durus_toplam_dk = durus["toplam_dk"]

                # Uretim (PLC'den bara/parca sayisi - hat_kodu uzerinden)
                s.uretilen_adet = self._uretim_topla(conn, h["kod"], baslangic_tarihi, bitis_tarihi)

                # Kalite red
                s.red_adet = self._red_topla(conn, h["id"], baslangic_tarihi, bitis_tarihi)

                s.hesapla()
                sonuclar.append(s)
            return sonuclar
        finally:
            conn.close()

    def pareto(
        self,
        baslangic_tarihi: str | date,
        bitis_tarihi: str | date,
        hat_id: Optional[int] = None,
        sadece_oee_etkili: bool = True,
    ) -> list[DurusKayipPareto]:
        """Donemdeki duruslari neden/kategori bazinda topla, en uzundan sirala."""
        if isinstance(baslangic_tarihi, str):
            baslangic_tarihi = datetime.strptime(baslangic_tarihi[:10], "%Y-%m-%d").date()
        if isinstance(bitis_tarihi, str):
            bitis_tarihi = datetime.strptime(bitis_tarihi[:10], "%Y-%m-%d").date()

        sql = """
            SELECT dn.kategori, dn.kod AS neden_kodu, dn.ad AS neden_adi,
                   ISNULL(dn.oee_etkisi, 1) AS oee_etkisi,
                   SUM(ISNULL(dk.sure_dk, 0)) AS sure_dk,
                   COUNT(*) AS sayi
            FROM uretim.durus_kayitlari dk
            INNER JOIN tanim.durus_nedenleri dn ON dn.id = dk.durus_nedeni_id
            WHERE CAST(dk.baslama_zamani AS date) BETWEEN ? AND ?
        """
        params: list = [baslangic_tarihi, bitis_tarihi]
        if hat_id:
            sql += " AND dk.hat_id = ?"
            params.append(hat_id)
        if sadece_oee_etkili:
            sql += " AND ISNULL(dn.oee_etkisi, 1) = 1"
        sql += " GROUP BY dn.kategori, dn.kod, dn.ad, dn.oee_etkisi ORDER BY sure_dk DESC"

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, *params)
            rows = cur.fetchall()
            kayitlar: list[DurusKayipPareto] = []
            toplam = sum(r[4] or 0 for r in rows) or 1
            for r in rows:
                p = DurusKayipPareto(
                    kategori=r[0] or "DIGER",
                    neden_kodu=r[1] or "",
                    neden_adi=r[2] or "",
                    sure_dk=int(r[4] or 0),
                    sayi=int(r[5] or 0),
                    yuzde=(int(r[4] or 0) / toplam) if toplam > 0 else 0.0,
                )
                kayitlar.append(p)
            return kayitlar
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Yardimci sorgular
    # ------------------------------------------------------------------

    def _hatlari_getir(self, conn, hat_id: Optional[int]) -> list[dict]:
        cur = conn.cursor()
        sql = """
            SELECT id, kod, ad, hat_tipi, devir_suresi_dk
            FROM tanim.uretim_hatlari
            WHERE aktif_mi = 1
        """
        params: list = []
        if hat_id:
            sql += " AND id = ?"
            params.append(hat_id)
        sql += " ORDER BY sira_no, id"
        cur.execute(sql, *params)
        return [
            {
                "id": r[0],
                "kod": r[1],
                "ad": r[2],
                "hat_tipi": r[3],
                "devir_suresi_dk": float(r[4]) if r[4] is not None else 0.0,
            }
            for r in cur.fetchall()
        ]

    def _vardiya_dakikasi_getir(self, conn, vardiya_id: Optional[int]) -> int:
        """Vardiya verilmise o, yoksa AKTIF tum vardiyalarin toplam suresini don.
        Mola sureleri planlanan_sure'den dusulur."""
        cur = conn.cursor()
        if vardiya_id:
            cur.execute("""
                SELECT baslangic_saati, bitis_saati, ISNULL(mola_suresi_dk, 0)
                FROM tanim.vardiyalar WHERE id = ?
            """, vardiya_id)
            r = cur.fetchone()
            if not r:
                return 0
            return self._vardiya_brut_dk(r[0], r[1]) - int(r[2] or 0)

        # Tum aktif vardiyalarin toplami (gun basina)
        cur.execute("""
            SELECT baslangic_saati, bitis_saati, ISNULL(mola_suresi_dk, 0)
            FROM tanim.vardiyalar WHERE aktif_mi = 1
        """)
        toplam = 0
        for r in cur.fetchall():
            toplam += self._vardiya_brut_dk(r[0], r[1]) - int(r[2] or 0)
        return toplam if toplam > 0 else (24 * 60)  # vardiya tanimi yoksa 24sa

    def _vardiya_brut_dk(self, baslangic: time, bitis: time) -> int:
        """Vardiya brut suresi (gece geciyorsa +24sa)."""
        if baslangic is None or bitis is None:
            return 0
        b = baslangic.hour * 60 + baslangic.minute
        e = bitis.hour * 60 + bitis.minute
        if e <= b:
            e += 24 * 60
        return max(0, e - b)

    def _durus_topla(
        self, conn, hat_id: int, baslangic: date, bitis: date
    ) -> dict:
        cur = conn.cursor()
        cur.execute("""
            SELECT
              SUM(CASE WHEN ISNULL(dn.oee_etkisi, 1) = 1 THEN dk.sure_dk ELSE 0 END) AS oee_etkili,
              SUM(CASE WHEN ISNULL(dn.oee_etkisi, 1) = 0 THEN dk.sure_dk ELSE 0 END) AS planli,
              SUM(ISNULL(dk.sure_dk, 0)) AS toplam
            FROM uretim.durus_kayitlari dk
            INNER JOIN tanim.durus_nedenleri dn ON dn.id = dk.durus_nedeni_id
            WHERE dk.hat_id = ?
              AND CAST(dk.baslama_zamani AS date) BETWEEN ? AND ?
        """, hat_id, baslangic, bitis)
        r = cur.fetchone()
        return {
            "oee_etkili_dk": int(r[0] or 0),
            "planli_dk": int(r[1] or 0),
            "toplam_dk": int(r[2] or 0),
        }

    def _uretim_topla(
        self, conn, hat_kodu: str, baslangic: date, bitis: date
    ) -> int:
        """PLC tarihcesinden hat_kodu icin donem toplam bara/parca sayisi.

        plc_tarihce yoksa plc_cache'in gunluk_bara_adet'i toplanir.
        """
        cur = conn.cursor()
        # Once plc_tarihce dene
        try:
            cur.execute("""
                SELECT COUNT(DISTINCT bara_no) AS adet
                FROM uretim.plc_tarihce
                WHERE hat_kodu = ?
                  AND CAST(islem_zamani AS date) BETWEEN ? AND ?
                  AND bara_no IS NOT NULL AND bara_no > 0
            """, hat_kodu, baslangic, bitis)
            r = cur.fetchone()
            if r and r[0]:
                return int(r[0])
        except Exception:
            pass

        # Fallback: plc_cache (anlik degerden tahmin)
        try:
            cur.execute("""
                SELECT SUM(ISNULL(gunluk_bara_adet, 0))
                FROM uretim.plc_cache
                WHERE hat_kodu = ?
            """, hat_kodu)
            r = cur.fetchone()
            return int(r[0] or 0)
        except Exception:
            return 0

    def _red_topla(
        self, conn, hat_id: int, baslangic: date, bitis: date
    ) -> int:
        """Donem icindeki red miktari. uretim_redler hat_id'ye sahipse ona, degilse
        durus_kategori=KALITE'ye dusen kayitlar uzerinden tahmin (basit)."""
        cur = conn.cursor()
        try:
            # uretim_redler tablosunda hat_id varsa (degisken; varsa kullan)
            cur.execute("""
                SELECT COUNT(*)
                FROM kalite.uretim_redler r
                WHERE CAST(r.olusturma_tarihi AS date) BETWEEN ? AND ?
            """, baslangic, bitis)
            r = cur.fetchone()
            return int(r[0] or 0)
        except Exception:
            return 0

    def _varsayilan_cevrim_recete(self, conn, hat_id: int) -> float:
        """Hat tanimi devir_suresi_dk yoksa, recete tanimlarindan ortalama cevrim al.
        Bu kaba bir tahmin; kalibre edildiginde guncellenmeli."""
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT AVG(CAST(toplam_sure_dk AS float))
                FROM kaplama.plc_recete_tanimlari
                WHERE toplam_sure_dk > 0
            """)
            r = cur.fetchone()
            return float(r[0] or 0)
        except Exception:
            return 0.0
