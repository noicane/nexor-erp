# -*- coding: utf-8 -*-
"""
NEXOR Terminal API - Yeni Sevkiyat Router

Desktop modules/sevkiyat/sevk_yeni.py karsiligi.
Tek dogruluk kaynagi: siparis.sp_sevkiyat_olustur (migration 0011).

Endpointler:
  GET  /sevk-yeni/arac-bilgileri        -> tasiyici/plaka/sofor dropdownlari
  GET  /sevk-yeni/hazir-urunler?arama=  -> sevke hazir lot listesi
  POST /sevk-yeni/lot-dogrula           -> tek barkod kontrolu
  POST /sevk-yeni/olustur               -> SP cagir (cari'ye gore grupla)
"""
from __future__ import annotations

from typing import Optional
from xml.sax.saxutils import quoteattr

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth import current_user
from ..db import fetch_all, fetch_one, get_conn

router = APIRouter(prefix="/sevk-yeni", tags=["sevk-yeni"])


# ============================================================================
# MODELLER
# ============================================================================

class AracBilgileri(BaseModel):
    tasiyicilar: list[str] = []
    plakalar: list[dict] = []   # [{plaka, detay}]
    soforler: list[dict] = []   # [{ad, telefon}]


class HazirUrun(BaseModel):
    stok_bakiye_id: int
    lot_no: str
    musteri: str
    stok_kodu: str = ""
    stok_adi: str = ""
    miktar: float
    cari_id: Optional[int] = None
    is_emri_id: Optional[int] = None
    gun: int = 0


class LotDogrulaInput(BaseModel):
    lot_no: str = Field(..., min_length=1, max_length=100)


class LotDogrulaSonuc(BaseModel):
    bulundu: bool
    mesaj: str
    urun: Optional[HazirUrun] = None


class SevkLotInput(BaseModel):
    lot_no: str
    miktar: float
    cari_id: Optional[int] = None
    is_emri_id: int
    stok_kodu: str = ""
    musteri: str = ""


class SevkOlusturInput(BaseModel):
    tasiyici: Optional[str] = ""
    plaka: Optional[str] = ""
    sofor: Optional[str] = ""
    notlar: Optional[str] = ""
    lotlar: list[SevkLotInput]


class SevkOlusturItem(BaseModel):
    irsaliye_id: int
    irsaliye_no: str
    cari_id: Optional[int]
    musteri: str
    lot_sayisi: int
    toplam_miktar: float


class SevkOlusturSonuc(BaseModel):
    olusturulan: list[SevkOlusturItem] = []
    basarisiz: list[dict] = []   # [{musteri, hata}]


# ============================================================================
# ENDPOINT: arac bilgileri (tasiyici/plaka/sofor)
# ============================================================================

@router.get("/arac-bilgileri", response_model=AracBilgileri,
            summary="Tasiyici/plaka/sofor dropdownlari icin liste")
def arac_bilgileri(user: dict = Depends(current_user)):
    # Tasiyicilar (gecmis irsaliyelerden distinct)
    tasiyicilar: list[str] = []
    try:
        rows = fetch_all("""
            SELECT DISTINCT tasiyici_firma
            FROM siparis.cikis_irsaliyeleri
            WHERE tasiyici_firma IS NOT NULL AND tasiyici_firma <> ''
            ORDER BY tasiyici_firma
        """)
        tasiyicilar = [r["tasiyici_firma"] for r in rows]
    except Exception:
        pass

    # Plakalar (lojistik.araclar)
    plakalar: list[dict] = []
    try:
        rows = fetch_all("""
            SELECT plaka, ISNULL(arac_tipi,'') AS arac_tipi, ISNULL(marka,'') AS marka
            FROM lojistik.araclar
            WHERE aktif_mi = 1
            ORDER BY plaka
        """)
        for r in rows:
            detay = (r["arac_tipi"] + " " + r["marka"]).strip()
            plakalar.append({"plaka": r["plaka"], "detay": detay})
    except Exception:
        pass

    # Soforler (lojistik.soforler)
    soforler: list[dict] = []
    try:
        rows = fetch_all("""
            SELECT ad_soyad, ISNULL(telefon,'') AS telefon
            FROM lojistik.soforler
            WHERE aktif_mi = 1
            ORDER BY ad_soyad
        """)
        for r in rows:
            soforler.append({"ad": r["ad_soyad"], "telefon": r["telefon"]})
    except Exception:
        pass

    return AracBilgileri(
        tasiyicilar=tasiyicilar,
        plakalar=plakalar,
        soforler=soforler,
    )


# ============================================================================
# ENDPOINT: sevke hazir urunler
# ============================================================================

_HAZIR_SQL = """
SELECT
    sb.id AS bakiye_id,
    sb.lot_no,
    COALESCE(ie.cari_unvani, sb.cari_unvani, N'Tanimsiz') AS musteri,
    COALESCE(ie.stok_kodu, sb.stok_kodu, N'') AS stok_kodu,
    COALESCE(ie.stok_adi, sb.stok_adi, N'') AS stok_adi,
    CAST(sb.miktar AS float) AS miktar,
    ie.cari_id,
    ie.id AS is_emri_id,
    DATEDIFF(day, sb.son_hareket_tarihi, GETDATE()) AS gun
FROM stok.stok_bakiye sb
LEFT JOIN siparis.is_emirleri ie
    ON REPLACE(REPLACE(sb.lot_no, N'-SEV', N''), N'-SEVK', N'') = ie.lot_no
JOIN tanim.depolar d ON sb.depo_id = d.id
WHERE d.kod IN ('SEV-01', 'SEVK', 'SEV', 'MAMUL')
  AND sb.kalite_durumu IN ('ONAYLANDI', 'OK', 'SEVKE_HAZIR')
  AND sb.miktar > 0
"""


@router.get("/hazir-urunler", response_model=list[HazirUrun],
            summary="Sevke hazir lot listesi")
def hazir_urunler(
    arama: Optional[str] = Query(None, description="Lot/musteri/stok ile filtre"),
    user: dict = Depends(current_user),
):
    sql = _HAZIR_SQL
    params: list = []
    if arama:
        like = f"%{arama.strip()}%"
        sql += """
          AND (sb.lot_no LIKE ?
               OR COALESCE(ie.cari_unvani, sb.cari_unvani, '') LIKE ?
               OR COALESCE(ie.stok_kodu, sb.stok_kodu, '') LIKE ?
               OR COALESCE(ie.stok_adi, sb.stok_adi, '') LIKE ?)
        """
        params.extend([like, like, like, like])
    sql += " ORDER BY sb.son_hareket_tarihi DESC"

    rows = fetch_all(sql, *params)
    return [
        HazirUrun(
            stok_bakiye_id=r["bakiye_id"],
            lot_no=r["lot_no"] or "",
            musteri=r["musteri"] or "Tanimsiz",
            stok_kodu=r["stok_kodu"] or "",
            stok_adi=r["stok_adi"] or "",
            miktar=float(r["miktar"] or 0),
            cari_id=r["cari_id"],
            is_emri_id=r["is_emri_id"],
            gun=int(r["gun"] or 0),
        )
        for r in rows
    ]


# ============================================================================
# ENDPOINT: lot dogrula (tek barkod)
# ============================================================================

@router.post("/lot-dogrula", response_model=LotDogrulaSonuc,
             summary="Tek lot bilgisini cek (barkod okuma)")
def lot_dogrula(
    payload: LotDogrulaInput = Body(...),
    user: dict = Depends(current_user),
):
    lot_no = payload.lot_no.strip()
    if not lot_no:
        return LotDogrulaSonuc(bulundu=False, mesaj="Lot numarasi bos")

    sql = _HAZIR_SQL + " AND sb.lot_no = ?"
    rows = fetch_all(sql, lot_no)
    if not rows:
        return LotDogrulaSonuc(
            bulundu=False,
            mesaj=f"'{lot_no}' sevk deposunda yok ya da kalite onayli degil",
        )

    r = rows[0]
    return LotDogrulaSonuc(
        bulundu=True,
        mesaj="OK",
        urun=HazirUrun(
            stok_bakiye_id=r["bakiye_id"],
            lot_no=r["lot_no"] or "",
            musteri=r["musteri"] or "Tanimsiz",
            stok_kodu=r["stok_kodu"] or "",
            stok_adi=r["stok_adi"] or "",
            miktar=float(r["miktar"] or 0),
            cari_id=r["cari_id"],
            is_emri_id=r["is_emri_id"],
            gun=int(r["gun"] or 0),
        ),
    )


# ============================================================================
# ENDPOINT: sevkiyat olustur (cari basina SP cagir)
# ============================================================================

def _build_lotlar_xml(lotlar: list[SevkLotInput]) -> str:
    """SP'nin bekledigi <lotlar><lot ... /></lotlar> XML'ini uret."""
    parts = ["<lotlar>"]
    for lot in lotlar:
        parts.append(
            "<lot lot_no={lot_no} miktar={miktar} cari_id={cari_id} "
            "is_emri_id={ie} stok_kodu={stok} />".format(
                lot_no=quoteattr(lot.lot_no or ""),
                miktar=quoteattr(str(lot.miktar)),
                cari_id=quoteattr(str(lot.cari_id) if lot.cari_id is not None else ""),
                ie=quoteattr(str(lot.is_emri_id)),
                stok=quoteattr(lot.stok_kodu or ""),
            )
        )
    parts.append("</lotlar>")
    return "".join(parts)


def _sp_cagir(grup_lotlar: list[SevkLotInput], cari_id: Optional[int],
              musteri: str, payload: SevkOlusturInput, kullanici_id: int
              ) -> tuple[int, str]:
    """sp_sevkiyat_olustur cagir, (irsaliye_id, irsaliye_no) don."""
    xml = _build_lotlar_xml(grup_lotlar)
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            DECLARE @irs_id BIGINT, @irs_no NVARCHAR(30);
            EXEC siparis.sp_sevkiyat_olustur
                @cari_id = ?,
                @musteri_adi = ?,
                @tasiyici = ?,
                @plaka = ?,
                @sofor = ?,
                @notlar = ?,
                @lotlar_xml = ?,
                @kullanici_id = ?,
                @irsaliye_id = @irs_id OUTPUT,
                @irsaliye_no = @irs_no OUTPUT;
            SELECT @irs_id AS id, @irs_no AS no;
        """, (
            cari_id,
            musteri,
            payload.tasiyici or None,
            payload.plaka or None,
            payload.sofor or None,
            payload.notlar or None,
            xml,
            kullanici_id,
        ))
        row = cur.fetchone()
        conn.commit()
        return int(row[0]), str(row[1])
    finally:
        conn.close()


@router.post("/olustur", response_model=SevkOlusturSonuc,
             summary="Lotlari cari'ye gore grupla, her grup icin irsaliye olustur")
def olustur(
    payload: SevkOlusturInput = Body(...),
    user: dict = Depends(current_user),
):
    if not payload.lotlar:
        raise HTTPException(status_code=400, detail="En az bir lot gerekli")

    # (cari_id, musteri) bazinda grupla - desktop _sevkiyat_olustur ile birebir
    gruplar: dict[tuple, list[SevkLotInput]] = {}
    for lot in payload.lotlar:
        key = (lot.cari_id, lot.musteri or "Tanimsiz")
        gruplar.setdefault(key, []).append(lot)

    olusturulan: list[SevkOlusturItem] = []
    basarisiz: list[dict] = []

    for (cari_id, musteri), grup in gruplar.items():
        try:
            irs_id, irs_no = _sp_cagir(
                grup_lotlar=grup,
                cari_id=cari_id,
                musteri=musteri,
                payload=payload,
                kullanici_id=user["id"],
            )
            olusturulan.append(SevkOlusturItem(
                irsaliye_id=irs_id,
                irsaliye_no=irs_no,
                cari_id=cari_id,
                musteri=musteri,
                lot_sayisi=len(grup),
                toplam_miktar=sum(l.miktar for l in grup),
            ))
        except Exception as e:
            basarisiz.append({"musteri": musteri, "hata": str(e)[:300]})

    return SevkOlusturSonuc(olusturulan=olusturulan, basarisiz=basarisiz)
