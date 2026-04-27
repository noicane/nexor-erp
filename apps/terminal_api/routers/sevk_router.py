# -*- coding: utf-8 -*-
"""
NEXOR Terminal API - Sevkiyat Yukleme Router

Akis:
1. GET /sevk/acik             -> durum=HAZIRLANDI olan irsaliyeler
2. GET /sevk/{id}             -> irsaliye master + satirlar
3. POST /sevk/{id}/lot-tara   -> okutulan lot satirlari ile esleyip dogrula
4. POST /sevk/{id}/yukle      -> tum satirlar tamamsa durum=SEVK_EDILDI

Veri modelleri:
- siparis.cikis_irsaliyeleri (master)
- siparis.cikis_irsaliye_satirlar (kalemler, lot_no virgul ayrali)
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from ..auth import current_user
from ..db import execute, fetch_all, fetch_one

router = APIRouter(prefix="/sevk", tags=["sevk"])


# ============================================================================
# MODELLER
# ============================================================================

class IrsaliyeOzet(BaseModel):
    id: int
    irsaliye_no: str
    tarih: Optional[str] = None
    cari_id: Optional[int] = None
    cari_adi: Optional[str] = None
    durum: str
    tasiyici_firma: Optional[str] = ""
    arac_plaka: Optional[str] = ""
    sofor_adi: Optional[str] = ""
    satir_sayisi: int = 0
    okutulan_lot_sayisi: int = 0


class SatirDetay(BaseModel):
    id: int
    satir_no: int
    urun_id: Optional[int] = None
    urun_kodu: Optional[str] = ""
    urun_adi: Optional[str] = ""
    miktar: float
    lot_no: str = ""
    koli_adedi: Optional[int] = 0
    durum: str = "BEKLIYOR"  # BEKLIYOR, OKUTULDU, EKSIK, FAZLA


class IrsaliyeDetay(BaseModel):
    ozet: IrsaliyeOzet
    satirlar: list[SatirDetay]


class LotTaraInput(BaseModel):
    lot_no: str = Field(..., min_length=1, max_length=200)


class LotTaraSonuc(BaseModel):
    lot_no: str
    bulundu: bool
    mesaj: str
    satir_id: Optional[int] = None
    urun_kodu: Optional[str] = None
    urun_adi: Optional[str] = None
    miktar: Optional[float] = None
    onceden_okutulmus: bool = False


class YuklenmeSonucu(BaseModel):
    irsaliye_id: int
    yeni_durum: str
    eksik_satir_sayisi: int
    mesaj: str


# ============================================================================
# YARDIMCI: lot-okutma cache (DB-persistent)
# ============================================================================
# Migration 0009 ile gelen sevkiyat.terminal_okutma_log tablosuna yazar/okur.
# Eszamanli kullanim + API restart guvenli.

def _okutulan_lotlar(irsaliye_id: int) -> set[str]:
    """Bir irsaliyede okutulmus normalized lot'lari don."""
    rows = fetch_all(
        "SELECT DISTINCT lot_no_norm FROM sevkiyat.terminal_okutma_log WHERE irsaliye_id = ?",
        irsaliye_id,
    )
    return {r["lot_no_norm"] for r in rows}


def _okutulan_sayisi(irsaliye_id: int) -> int:
    r = fetch_one(
        "SELECT COUNT(DISTINCT lot_no_norm) AS n FROM sevkiyat.terminal_okutma_log WHERE irsaliye_id = ?",
        irsaliye_id,
    )
    return int(r["n"]) if r else 0


def _okutmayi_kaydet(
    irsaliye_id: int,
    lot_norm: str,
    lot_raw: str,
    kullanici_id: int,
    satir_id: Optional[int] = None,
    urun_id: Optional[int] = None,
    kaynak: str = "TERMINAL",
) -> None:
    execute("""
        INSERT INTO sevkiyat.terminal_okutma_log
            (irsaliye_id, lot_no_norm, lot_no_raw, satir_id, urun_id, kullanici_id, kaynak)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, irsaliye_id, lot_norm, lot_raw, satir_id, urun_id, kullanici_id, kaynak)


def _cache_temizle(irsaliye_id: int) -> int:
    """Bu irsaliyenin okutma loglarini sil. Silinen kayit sayisini don."""
    return execute(
        "DELETE FROM sevkiyat.terminal_okutma_log WHERE irsaliye_id = ?",
        irsaliye_id,
    )


def _normalize_lot(s: str) -> str:
    """Lot eslemesinde -SEV/-SEVK ekleri ve bosluklari ihmal et."""
    if not s:
        return ""
    return (
        s.upper()
        .replace("-SEVK", "")
        .replace("-SEV", "")
        .strip()
    )


def _lot_listesi(satir_lot_no: str) -> list[str]:
    """Bir satirdaki cok-lot string'ini virguliyle ayir, normalize et."""
    if not satir_lot_no:
        return []
    return [_normalize_lot(p) for p in satir_lot_no.split(",") if p.strip()]


# ============================================================================
# ENDPOINTLER
# ============================================================================

@router.get("/acik", response_model=list[IrsaliyeOzet], summary="Yuklenmeyi bekleyen irsaliyeler")
def acik_irsaliyeler(
    arama: Optional[str] = Query(None, description="Irsaliye no / cari unvan / plaka arar"),
    user: dict = Depends(current_user),
):
    sql = """
        SELECT i.id, i.irsaliye_no, CONVERT(varchar(10), i.tarih, 23) AS tarih,
               i.cari_id, c.unvan AS cari_adi, i.durum,
               ISNULL(i.tasiyici_firma,'') AS tasiyici_firma,
               ISNULL(i.arac_plaka,'') AS arac_plaka,
               ISNULL(i.sofor_adi,'') AS sofor_adi,
               (SELECT COUNT(*) FROM siparis.cikis_irsaliye_satirlar s
                WHERE s.irsaliye_id = i.id) AS satir_sayisi
        FROM siparis.cikis_irsaliyeleri i
        LEFT JOIN musteri.cariler c ON c.id = i.cari_id
        WHERE i.silindi_mi = 0 AND i.durum = 'HAZIRLANDI'
    """
    params: list = []
    if arama:
        sql += " AND (i.irsaliye_no LIKE ? OR c.unvan LIKE ? OR i.arac_plaka LIKE ?)"
        like = f"%{arama.strip()}%"
        params.extend([like, like, like])
    sql += " ORDER BY i.id DESC"
    rows = fetch_all(sql, *params)

    sonuc: list[IrsaliyeOzet] = []
    for r in rows:
        okutulan = _okutulan_sayisi(r["id"])
        sonuc.append(IrsaliyeOzet(
            id=r["id"],
            irsaliye_no=r["irsaliye_no"],
            tarih=r["tarih"],
            cari_id=r["cari_id"],
            cari_adi=r["cari_adi"],
            durum=r["durum"],
            tasiyici_firma=r["tasiyici_firma"],
            arac_plaka=r["arac_plaka"],
            sofor_adi=r["sofor_adi"],
            satir_sayisi=r["satir_sayisi"] or 0,
            okutulan_lot_sayisi=okutulan,
        ))
    return sonuc


@router.get("/{irsaliye_id}", response_model=IrsaliyeDetay, summary="Irsaliye detay + satirlar")
def irsaliye_detay(
    irsaliye_id: int = Path(..., gt=0),
    user: dict = Depends(current_user),
):
    master = fetch_one("""
        SELECT i.id, i.irsaliye_no, CONVERT(varchar(10), i.tarih, 23) AS tarih,
               i.cari_id, c.unvan AS cari_adi, i.durum,
               ISNULL(i.tasiyici_firma,'') AS tasiyici_firma,
               ISNULL(i.arac_plaka,'') AS arac_plaka,
               ISNULL(i.sofor_adi,'') AS sofor_adi
        FROM siparis.cikis_irsaliyeleri i
        LEFT JOIN musteri.cariler c ON c.id = i.cari_id
        WHERE i.id = ? AND i.silindi_mi = 0
    """, irsaliye_id)
    if not master:
        raise HTTPException(status_code=404, detail="Irsaliye bulunamadi")

    rows = fetch_all("""
        SELECT s.id, s.satir_no, s.urun_id,
               u.urun_kodu, u.urun_adi,
               CAST(s.miktar AS float) AS miktar,
               ISNULL(s.lot_no,'') AS lot_no,
               ISNULL(s.koli_adedi, 0) AS koli_adedi
        FROM siparis.cikis_irsaliye_satirlar s
        LEFT JOIN stok.urunler u ON u.id = s.urun_id
        WHERE s.irsaliye_id = ?
        ORDER BY s.satir_no, s.id
    """, irsaliye_id)

    okutulan_set = _okutulan_lotlar(irsaliye_id)
    satirlar: list[SatirDetay] = []
    for r in rows:
        lots = _lot_listesi(r["lot_no"])
        # En az bir lot okutulmussa OKUTULDU say (cok-lot satirinda kismi takip)
        has_match = any(l in okutulan_set for l in lots)
        durum = "OKUTULDU" if has_match else "BEKLIYOR"
        satirlar.append(SatirDetay(
            id=r["id"],
            satir_no=r["satir_no"] or 0,
            urun_id=r["urun_id"],
            urun_kodu=r["urun_kodu"] or "",
            urun_adi=r["urun_adi"] or "",
            miktar=float(r["miktar"] or 0),
            lot_no=r["lot_no"] or "",
            koli_adedi=int(r["koli_adedi"] or 0),
            durum=durum,
        ))

    ozet = IrsaliyeOzet(
        id=master["id"],
        irsaliye_no=master["irsaliye_no"],
        tarih=master["tarih"],
        cari_id=master["cari_id"],
        cari_adi=master["cari_adi"],
        durum=master["durum"],
        tasiyici_firma=master["tasiyici_firma"],
        arac_plaka=master["arac_plaka"],
        sofor_adi=master["sofor_adi"],
        satir_sayisi=len(satirlar),
        okutulan_lot_sayisi=len(okutulan_set),
    )
    return IrsaliyeDetay(ozet=ozet, satirlar=satirlar)


@router.post("/{irsaliye_id}/lot-tara", response_model=LotTaraSonuc, summary="Tek lot okutma")
def lot_tara(
    irsaliye_id: int = Path(..., gt=0),
    payload: LotTaraInput = Body(...),
    user: dict = Depends(current_user),
):
    """Barkod'dan okutulan lot'u irsaliye satirlariyla esle.

    Lot eslemesi `_normalize_lot` ile -SEV/-SEVK eklerini yok sayarak yapilir.
    """
    # Irsaliye varligi
    master = fetch_one(
        "SELECT id, durum FROM siparis.cikis_irsaliyeleri WHERE id = ? AND silindi_mi = 0",
        irsaliye_id,
    )
    if not master:
        raise HTTPException(status_code=404, detail="Irsaliye bulunamadi")
    if master["durum"] != "HAZIRLANDI":
        raise HTTPException(
            status_code=400,
            detail=f"Bu irsaliye yuklenemez (durum: {master['durum']})"
        )

    okutulan_norm = _normalize_lot(payload.lot_no)
    if not okutulan_norm:
        raise HTTPException(status_code=400, detail="Lot numarasi bos")

    # Onceden okutulmus mu? (DB'den)
    onceden = okutulan_norm in _okutulan_lotlar(irsaliye_id)

    # Satirlarda ara
    rows = fetch_all("""
        SELECT s.id, s.satir_no, s.lot_no, s.urun_id,
               u.urun_kodu, u.urun_adi, CAST(s.miktar AS float) AS miktar
        FROM siparis.cikis_irsaliye_satirlar s
        LEFT JOIN stok.urunler u ON u.id = s.urun_id
        WHERE s.irsaliye_id = ?
    """, irsaliye_id)

    eslenen = None
    for r in rows:
        lots = _lot_listesi(r["lot_no"])
        if okutulan_norm in lots:
            eslenen = r
            break

    if eslenen is None:
        return LotTaraSonuc(
            lot_no=payload.lot_no,
            bulundu=False,
            mesaj=f"'{payload.lot_no}' bu irsaliyede yok. Yanlis irsaliyeyi mi okuttunuz?",
        )

    # Esleme basarili - DB'ye yaz (onceden okutulduysa idempotent: yine yeni log atilir,
    # cunku kim ne zaman okuttu bilgisi kayitli kalsin; DISTINCT count ile sayariz)
    _okutmayi_kaydet(
        irsaliye_id=irsaliye_id,
        lot_norm=okutulan_norm,
        lot_raw=payload.lot_no,
        kullanici_id=user["id"],
        satir_id=eslenen["id"],
        urun_id=eslenen.get("urun_id"),
        kaynak="TERMINAL",
    )

    return LotTaraSonuc(
        lot_no=payload.lot_no,
        bulundu=True,
        mesaj=("Tekrar okutuldu (zaten kabul edildi)" if onceden else "Eslesti, kabul edildi"),
        satir_id=eslenen["id"],
        urun_kodu=eslenen["urun_kodu"],
        urun_adi=eslenen["urun_adi"],
        miktar=eslenen["miktar"],
        onceden_okutulmus=onceden,
    )


@router.post("/{irsaliye_id}/yukle", response_model=YuklenmeSonucu, summary="Yukleme tamamlandi")
def yukleme_tamam(
    irsaliye_id: int = Path(..., gt=0),
    zorla: bool = Query(False, description="Eksik lot olsa bile yuklendi olarak isaretle"),
    user: dict = Depends(current_user),
):
    """Tum satirlardaki lotlar okutuldu mu kontrol et, eksiksiz ise SEVK_EDILDI yap."""
    master = fetch_one(
        "SELECT id, durum FROM siparis.cikis_irsaliyeleri WHERE id = ? AND silindi_mi = 0",
        irsaliye_id,
    )
    if not master:
        raise HTTPException(status_code=404, detail="Irsaliye bulunamadi")
    if master["durum"] not in ("HAZIRLANDI", "SEVK_EDILDI"):
        raise HTTPException(
            status_code=400,
            detail=f"Bu irsaliye yuklenemez (durum: {master['durum']})"
        )

    rows = fetch_all("""
        SELECT s.id, s.satir_no, ISNULL(s.lot_no,'') AS lot_no
        FROM siparis.cikis_irsaliye_satirlar s
        WHERE s.irsaliye_id = ?
    """, irsaliye_id)

    okutulanlar = _okutulan_lotlar(irsaliye_id)
    eksik = 0
    for r in rows:
        lots = _lot_listesi(r["lot_no"])
        if not lots:
            # Lot bilgisi olmayan satir - sayilmaz
            continue
        if not any(l in okutulanlar for l in lots):
            eksik += 1

    if eksik > 0 and not zorla:
        raise HTTPException(
            status_code=400,
            detail=f"{eksik} satirda lot okutulmamis. Tum kalemleri tarayin veya zorla=true ile gonderin.",
        )

    # Durumu guncelle
    n = execute("""
        UPDATE siparis.cikis_irsaliyeleri
        SET durum = 'SEVK_EDILDI',
            guncelleme_tarihi = SYSDATETIME(),
            guncelleyen_id = ?
        WHERE id = ?
    """, user["id"], irsaliye_id)

    if n != 1:
        raise HTTPException(status_code=500, detail="Durum guncellenemedi")

    # NOT: cache'i SILMEYIZ - audit trail kalsin (kim ne zaman okuttu).
    # /cache endpoint'i debug icin manuel temizleme saglar.

    return YuklenmeSonucu(
        irsaliye_id=irsaliye_id,
        yeni_durum="SEVK_EDILDI",
        eksik_satir_sayisi=eksik,
        mesaj=("Eksik kalemlerle zorla yuklendi" if eksik > 0 else "Yukleme tamamlandi"),
    )


@router.delete("/{irsaliye_id}/cache", summary="Okutulan lot loglarini sil (debug/test)")
def cache_temizle(
    irsaliye_id: int = Path(..., gt=0),
    user: dict = Depends(current_user),
):
    """sevkiyat.terminal_okutma_log'dan bu irsaliyeye ait kayitlari siler."""
    sayi = _cache_temizle(irsaliye_id)
    return {"silinen": sayi, "irsaliye_id": irsaliye_id}
