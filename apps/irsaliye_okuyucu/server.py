# -*- coding: utf-8 -*-
"""
NEXOR Irsaliye Okuyucu - FastAPI Backend

Mobile/tablet uzerinden musteri irsaliye fotografini okur, Claude Vision ile
parse eder, NEXOR'un cari ve stok kartlari ile fuzzy eslesme onerir.
Kullanici onaylayinca siparis.giris_irsaliyeleri + satirlar tablolarina yazar.

Akis:
1. POST /api/parse-irsaliye  -> foto + OCR + fuzzy match
2. POST /api/kaydet          -> onaylanan JSON -> DB INSERT

NEXOR masaustu uygulamasina DOKUNMAZ. Sadece DB'ye okur/yazar.
"""
from __future__ import annotations

import base64
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pyodbc
from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from rapidfuzz import fuzz, process

# ---------------------------------------------------------------------------
# Ortam
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent  # NEXOR projesi kokun
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("irsaliye_okuyucu")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


# ---------------------------------------------------------------------------
# Veritabani (NEXOR'un Nexor.UDL veya .env'den)
# ---------------------------------------------------------------------------

def _read_udl() -> Optional[dict]:
    """Proje kokundeki Nexor.UDL'den baglanti bilgileri oku"""
    for p in [PROJECT_ROOT / "Nexor.UDL", Path("C:/NEXOR/Nexor.UDL")]:
        if not p.exists():
            continue
        try:
            try:
                text = p.read_text(encoding="utf-16")
            except UnicodeError:
                text = p.read_text(encoding="utf-8")
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("[") or line.startswith(";"):
                    continue
                params = {}
                for part in line.split(";"):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        params[k.strip().lower()] = v.strip()
                if params.get("data source") and params.get("initial catalog"):
                    return {
                        "server": params["data source"],
                        "database": params["initial catalog"],
                        "user": params.get("user id", ""),
                        "password": params.get("password", ""),
                    }
        except Exception:
            continue
    return None


def _db_config() -> dict:
    """DB config: once .env, sonra UDL"""
    if os.environ.get("DB_SERVER"):
        return {
            "server": os.environ["DB_SERVER"],
            "database": os.environ.get("DB_NAME", ""),
            "user": os.environ.get("DB_USER", ""),
            "password": os.environ.get("DB_PASSWORD", ""),
        }
    udl = _read_udl()
    if udl:
        return udl
    raise RuntimeError("DB config bulunamadi - .env veya Nexor.UDL gerekli")


_DB_CFG = _db_config()


def get_conn() -> pyodbc.Connection:
    """Her istek icin yeni pyodbc baglantisi"""
    cs = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={_DB_CFG['server']};"
        f"DATABASE={_DB_CFG['database']};"
        f"UID={_DB_CFG['user']};"
        f"PWD={_DB_CFG['password']};"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(cs, timeout=10)


# ---------------------------------------------------------------------------
# Anthropic client
# ---------------------------------------------------------------------------

_anthropic_client: Optional[Anthropic] = None


def get_anthropic() -> Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        if not ANTHROPIC_API_KEY or not ANTHROPIC_API_KEY.startswith("sk-ant-"):
            raise HTTPException(
                500,
                "ANTHROPIC_API_KEY tanimli degil veya gecersiz. "
                ".env dosyasina 'sk-ant-api03-...' ile baslayan anahtari ekle.",
            )
        _anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    return _anthropic_client


# ---------------------------------------------------------------------------
# Modeller (Pydantic)
# ---------------------------------------------------------------------------

class KalemOneri(BaseModel):
    urun_id: int
    urun_kodu: str
    urun_adi: str
    skor: float  # 0-100
    kaynak: str = "fuzzy"  # "ogrenilmis" | "fuzzy" | "kod_exact"


class Kalem(BaseModel):
    sira: int
    kod: str = ""          # Musteri irsaliyesindeki stok kodu
    ad: str                # Urun adi (zorunlu)
    miktar: float
    birim: str = "ADET"
    kaplama: Optional[str] = None  # Kaplama tipi (e.g. KTFRZ, ZNNI)
    oneriler: List[KalemOneri] = []  # Fuzzy match onerileri
    secilen_urun_id: Optional[int] = None  # Kullanici secimi


class CariOneri(BaseModel):
    id: int
    unvan: str
    vergi_no: Optional[str] = None
    skor: float


class ParseSonucu(BaseModel):
    tedarikci_unvan: str = ""
    tedarikci_vkn: Optional[str] = None
    cari_onerileri: List[CariOneri] = []
    secilen_cari_id: Optional[int] = None
    cari_irsaliye_no: str = ""
    tarih: str = ""  # ISO format YYYY-MM-DD
    arac_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    kalemler: List[Kalem] = []
    notlar: Optional[str] = None


class KaydetRequest(BaseModel):
    secilen_cari_id: Optional[int] = None
    cari_unvan: str
    cari_irsaliye_no: str
    tarih: str
    arac_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    teslim_alan: Optional[str] = None
    notlar: Optional[str] = None
    kalemler: List[Kalem]


# ---------------------------------------------------------------------------
# Claude Vision: fotograf -> yapilandirilmis JSON
# ---------------------------------------------------------------------------

CLAUDE_SYSTEM_PROMPT = """Sen Turkce e-Irsaliye okuma uzmanisin. Fotograftan SADECE JSON don:

{
  "tedarikci_unvan": "<gonderen firma>",
  "tedarikci_vkn": "<10 haneli VKN>",
  "cari_irsaliye_no": "<irsaliye no>",
  "tarih": "<YYYY-MM-DD>",
  "arac_plaka": "<varsa>",
  "sofor_adi": "<varsa>",
  "notlar": "<FASON/BEDELSIZ/KAPLANMAK UZERE gibi ozel notlar>",
  "kalemler": [
    {
      "sira": 1,
      "kod": "<malzeme kodu - kolondaki orijinal>",
      "ad": "<malzeme adi - kolondaki orijinal>",
      "miktar": 123,
      "birim": "ADET",
      "kaplama": "<KTFRZ / ZNNI / BOYA / null>"
    }
  ]
}

MIKTAR OKUMA (EN KRITIK KURAL - YANLIS OKUMA OLMAMALI):
- Turk matbaa formati: ondalik "," VE binlik "." kullanir. Ornekler:
  * "1.200" = 1200 (binlik ayraci, tam sayi)
  * "1.200,00" = 1200 (binlik + ondalik sifir)
  * "2.400" = 2400 (binlik ayraci)
  * "120" = 120 (tam sayi)
  * "120,5" = 120.5 (ondalik)
  * "1.943" = 1943 (binlik)
  * "12.500" = 12500 (binlik)
- "1.200 Adet" gibi birimle yazilmis ise birim kismini ayir
- SUTUN BASLIGINI BUL: "Miktar", "MIKTAR", "Adet", "ADET", "MIKTAR(ADET)"
  o sutundaki HER SATIRIN degerini dikkatli oku
- Sayi okunamiyorsa veya belirsizse 0 yazma, 'sira' atla
- Her kalemdeki miktar mutlaka o kalemin KENDI SATIRINDAN olmali,
  baska satirin degerini karistirma
- Miktar alani yalnizca pozitif sayi (int veya float)

DIGER KURALLAR:
1. Sadece JSON, aciklama yok, markdown yok
2. Kod sutununun orijinalini koru (20003728, R_CON-S-0130 vs)
3. Urun adindaki kaplama tipi parantez:
   (KTFRZ) -> kaplama="KTFRZ"
   (KATAFOREZ) -> kaplama="KATAFOREZ"
   (KAPLANMAMIS) -> kaplama=null
4. Birim normalle: "Adet"/"AD" -> "ADET", "Kg" -> "KG"
5. Tarih: 21.04.2026 / 21-04-2026 / 2026-04-21 hepsi -> "2026-04-21"
6. VKN bulunamazsa null
7. Kalem sayisi: tabloda kac satir varsa hepsi. Satir atlamadan sirayla oku.
   Ornek: tabloda 6 satir varsa JSON'da 6 kalem olmali."""


_ANTHROPIC_IMAGE_LIMIT = 5 * 1024 * 1024  # 5 MB - Claude Vision max
_SAFE_IMAGE_LIMIT = 4 * 1024 * 1024       # 4 MB - guvenli alt sinir (base64 buyumesi icin)


def _compress_image_if_needed(image_bytes: bytes, media_type: str) -> tuple[bytes, str]:
    """Resim 4 MB'tan buyukse JPEG'e cevirip resize+compress et.
    Anthropic Vision 5 MB sinirini astiginda 400 hatasi verir.
    Tabletten gelen yuksek cozunurluklu resimler genelde 5-10 MB.
    """
    if len(image_bytes) <= _SAFE_IMAGE_LIMIT:
        return image_bytes, media_type

    try:
        from io import BytesIO
        from PIL import Image
    except ImportError:
        # Pillow yoksa olduğu gibi gönder (Anthropic 400 dönerse de net hata)
        return image_bytes, media_type

    img = Image.open(BytesIO(image_bytes))
    # JPEG icin alpha kanal sorunu - RGB'ye cevir
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")

    # Once boyut kontrolu - max kenar 2000px (yeterli OCR icin)
    max_side = 2000
    if max(img.size) > max_side:
        ratio = max_side / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # JPEG quality dusurerek 4 MB'in altina cek
    for quality in (85, 75, 65, 55, 45):
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        out = buf.getvalue()
        if len(out) <= _SAFE_IMAGE_LIMIT:
            logger.info(
                "Image compress: %d -> %d bytes (q=%d, %dx%d)",
                len(image_bytes), len(out), quality, *img.size,
            )
            return out, "image/jpeg"

    # En dusuk quality bile yetmedi - yine de don, Anthropic exception versin
    return out, "image/jpeg"


def parse_irsaliye_with_claude(image_bytes: bytes, media_type: str) -> dict:
    """Fotografi Claude Vision'a yolla, JSON cikarimi yap"""
    client = get_anthropic()
    image_bytes, media_type = _compress_image_if_needed(image_bytes, media_type)
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    msg = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=CLAUDE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Bu e-Irsaliye fotografini okuyup belirtilen JSON'u don. Sadece JSON, baska metin yok.",
                    },
                ],
            }
        ],
    )

    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    # Bazen claude ```json ... ``` ile sarmalar, temizle
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()

    import json as _json
    try:
        return _json.loads(text)
    except _json.JSONDecodeError as e:
        logger.error("Claude JSON parse hatasi: %s\nYanit: %s", e, text[:500])
        raise HTTPException(502, f"AI yanitini ayristiramadik: {e}")


# ---------------------------------------------------------------------------
# Fuzzy matching: Cari + Stok
# ---------------------------------------------------------------------------

def _cari_oneri_bul(tedarikci_unvan: str, tedarikci_vkn: Optional[str]) -> (Optional[int], List[CariOneri]):
    """
    Once VKN exact match, bulamazsa unvan fuzzy.
    Return: (secilen_id or None, top_5_oneri)
    """
    onerier: List[CariOneri] = []
    secilen_id: Optional[int] = None

    try:
        conn = get_conn()
        cur = conn.cursor()
        # VKN exact
        if tedarikci_vkn:
            cur.execute("""
                SELECT TOP 1 id, unvan, vergi_no
                FROM musteri.cariler
                WHERE vergi_no = ?
                  AND (aktif_mi IS NULL OR aktif_mi = 1)
            """, (tedarikci_vkn,))
            row = cur.fetchone()
            if row:
                secilen_id = int(row[0])
                onerier.append(CariOneri(id=secilen_id, unvan=row[1], vergi_no=row[2], skor=100.0))

        # Unvan fuzzy (en fazla 5)
        cur.execute("""
            SELECT id, unvan, vergi_no
            FROM musteri.cariler
            WHERE (aktif_mi IS NULL OR aktif_mi = 1)
              AND unvan IS NOT NULL
        """)
        tum = [(int(r[0]), r[1], r[2]) for r in cur.fetchall()]
        conn.close()

        if tedarikci_unvan and tum:
            adaylar = [(r[1] or "", idx) for idx, r in enumerate(tum)]
            scores = process.extract(
                tedarikci_unvan, [a[0] for a in adaylar],
                scorer=fuzz.WRatio, limit=5
            )
            for (_match_text, score, idx_in_tum) in scores:
                cid, unvan, vkn = tum[idx_in_tum]
                # Zaten eklendi mi?
                if any(o.id == cid for o in onerier):
                    continue
                if score < 50:
                    break
                onerier.append(CariOneri(id=cid, unvan=unvan, vergi_no=vkn, skor=float(score)))

        # Secilen yoksa en yuksek skorluyu oner (>= 85)
        if secilen_id is None and onerier and onerier[0].skor >= 85:
            secilen_id = onerier[0].id

    except Exception as e:
        logger.warning("Cari fuzzy match hatasi: %s", e)

    return secilen_id, onerier[:5]


_stok_urunler_cache: Optional[list] = None


def _stok_listesini_getir() -> list:
    """Tum aktif urunleri cache'le (1000+ urun hizli eslesme icin)"""
    global _stok_urunler_cache
    if _stok_urunler_cache is not None:
        return _stok_urunler_cache
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, urun_kodu, urun_adi, cari_id, musteri_parca_no
            FROM stok.urunler
            WHERE (aktif_mi IS NULL OR aktif_mi = 1)
              AND urun_kodu IS NOT NULL
        """)
        _stok_urunler_cache = [
            {
                "id": int(r[0]),
                "kod": r[1] or "",
                "ad": r[2] or "",
                "cari_id": int(r[3]) if r[3] else None,
                "musteri_parca_no": (r[4] or "").strip(),
            }
            for r in cur.fetchall()
        ]
        conn.close()
        cari_bagli = sum(1 for u in _stok_urunler_cache if u["cari_id"])
        parca_no_dolu = sum(1 for u in _stok_urunler_cache if u["musteri_parca_no"])
        logger.info(
            "Stok cache: %d urun (cari_id: %d, musteri_parca_no: %d)",
            len(_stok_urunler_cache), cari_bagli, parca_no_dolu
        )
    except Exception as e:
        logger.warning("Stok cache hatasi: %s", e)
        _stok_urunler_cache = []
    return _stok_urunler_cache


def _ogrenilmis_eslesme_bul(cari_id: int, musteri_kodu: str) -> Optional[dict]:
    """
    Ogrenilmis eslestirmede bu cari + bu musteri kodu var mi?
    Varsa kullanim_sayisini +1 yap, son_kullanim'i guncelle.
    """
    if not cari_id or not musteri_kodu:
        return None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT TOP 1 m.id, m.urun_id, u.urun_kodu, u.urun_adi
            FROM musteri.musteri_urun_kodlari m
            JOIN stok.urunler u ON m.urun_id = u.id
            WHERE m.cari_id = ? AND m.musteri_stok_kodu = ?
        """, (cari_id, musteri_kodu))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        map_id, urun_id, urun_kodu, urun_adi = row
        # Kullanim istatigini guncelle (bilgi amacli)
        cur.execute("""
            UPDATE musteri.musteri_urun_kodlari
            SET kullanim_sayisi = kullanim_sayisi + 1, son_kullanim = GETDATE()
            WHERE id = ?
        """, (map_id,))
        conn.commit()
        conn.close()
        return {"urun_id": int(urun_id), "urun_kodu": urun_kodu, "urun_adi": urun_adi}
    except Exception as e:
        logger.warning("Ogrenilmis eslesme sorgu hatasi: %s", e)
        return None


def _stok_oneri_bul(
    kod: str, ad: str, cari_id: Optional[int] = None
) -> (Optional[int], List[KalemOneri]):
    """
    Eslestirme sirasi (yuksekten dusuge):
    1) stok.urunler.musteri_parca_no EXACT (cari + kod bire bir) -> %100
    2) stok.urunler.musteri_parca_no bu cariye ait FUZZY (yazim hatasi)
    3) Ogrenilmis eslesme (musteri.musteri_urun_kodlari)
    4) Kod exact (genel urun_kodu)
    5) Kod+ad birlesik fuzzy
    """
    urunler = _stok_listesini_getir()
    if not urunler:
        return None, []

    onerier: List[KalemOneri] = []
    secilen_id: Optional[int] = None
    kod_up = (kod or "").strip().upper()

    # 1) MUSTERI PARCA NO EXACT (stok kartindan)
    if cari_id and kod_up:
        for u in urunler:
            if (u.get("cari_id") == cari_id
                    and u.get("musteri_parca_no")
                    and u["musteri_parca_no"].upper() == kod_up):
                secilen_id = u["id"]
                onerier.append(KalemOneri(
                    urun_id=u["id"], urun_kodu=u["kod"], urun_adi=u["ad"],
                    skor=100.0, kaynak="musteri_parca_no",
                ))
                break

    # 2) MUSTERI PARCA NO fuzzy (bu cariye ait olanlar icinde)
    if cari_id and kod_up and secilen_id is None:
        cari_urunleri = [
            u for u in urunler
            if u.get("cari_id") == cari_id and u.get("musteri_parca_no")
        ]
        if cari_urunleri:
            aday_kodlari = [u["musteri_parca_no"] for u in cari_urunleri]
            scores = process.extract(
                kod_up, aday_kodlari, scorer=fuzz.ratio, limit=3
            )
            for match_text, score, idx in scores:
                if score < 85:
                    break
                u = cari_urunleri[idx]
                if any(o.urun_id == u["id"] for o in onerier):
                    continue
                if secilen_id is None:
                    secilen_id = u["id"]
                onerier.append(KalemOneri(
                    urun_id=u["id"], urun_kodu=u["kod"], urun_adi=u["ad"],
                    skor=float(score), kaynak="musteri_parca_no_fuzzy",
                ))

    # 3) OGRENILMIS ESLESME
    if cari_id and secilen_id is None:
        ogr = _ogrenilmis_eslesme_bul(cari_id, kod)
        if ogr:
            secilen_id = ogr["urun_id"]
            onerier.append(KalemOneri(
                urun_id=ogr["urun_id"],
                urun_kodu=ogr["urun_kodu"],
                urun_adi=ogr["urun_adi"],
                skor=100.0,
                kaynak="ogrenilmis",
            ))

    # 4) Kod exact (genel urun_kodu)
    if kod_up:
        for u in urunler:
            if u["kod"].strip().upper() == kod_up:
                if any(o.urun_id == u["id"] for o in onerier):
                    break
                if secilen_id is None:
                    secilen_id = u["id"]
                onerier.append(KalemOneri(
                    urun_id=u["id"], urun_kodu=u["kod"], urun_adi=u["ad"],
                    skor=100.0, kaynak="kod_exact",
                ))
                break

    # 5a) Cari-ozel isim fuzzy - bu cariye ait urunler icinde ad bazli
    # (musteri_parca_no bos olsa da ad benzerliginden buluruz)
    if cari_id and ad:
        cari_urunleri = [u for u in urunler if u.get("cari_id") == cari_id]
        if cari_urunleri:
            adaylar = [u["ad"] for u in cari_urunleri]
            scores = process.extract(ad, adaylar, scorer=fuzz.WRatio, limit=5)
            for match_text, score, idx in scores:
                if score < 50:
                    break
                u = cari_urunleri[idx]
                if any(o.urun_id == u["id"] for o in onerier):
                    continue
                onerier.append(KalemOneri(
                    urun_id=u["id"], urun_kodu=u["kod"], urun_adi=u["ad"],
                    skor=float(score), kaynak="cari_ad_fuzzy",
                ))

    # 5b) Fuzzy (kod+ad birlesik, tum urunler) - son care
    if ad and len(onerier) < 5:
        hedefler = [(u["kod"] + " " + u["ad"], u) for u in urunler]
        scores = process.extract(
            (kod + " " + ad).strip(),
            [h[0] for h in hedefler],
            scorer=fuzz.WRatio,
            limit=5,
        )
        for match_text, score, idx in scores:
            u = hedefler[idx][1]
            if any(o.urun_id == u["id"] for o in onerier):
                continue
            if score < 60:
                break
            onerier.append(KalemOneri(
                urun_id=u["id"], urun_kodu=u["kod"], urun_adi=u["ad"],
                skor=float(score), kaynak="fuzzy",
            ))

    # Otomatik secim: hala bir sey secilmedi + ilk oneri yeterince yuksekse
    if secilen_id is None and onerier and onerier[0].skor >= 88:
        secilen_id = onerier[0].urun_id

    return secilen_id, onerier[:5]


# ---------------------------------------------------------------------------
# Irsaliye no uretme
# ---------------------------------------------------------------------------

def _yeni_irsaliye_no(cursor) -> str:
    """GRS-YYYYMM-NNNN. siparis.seq_giris_irsaliye_id sequence'i kullanir.

    NEXOR core/numara_uretici.py ile ayni mantik (inline) - server'da NEXOR
    core klasoru yok, dependency'siz calismak icin yerel implementasyon.
    Fallback YOK: sequence yoksa migration uygulanmali (UNIQUE KEY ihlali
    risk i icin try/except MAX+1 yasak - feedback_seq_no_fallback).
    """
    cursor.execute("SELECT NEXT VALUE FOR siparis.seq_giris_irsaliye_id")
    next_id = int(cursor.fetchone()[0])
    return f"GRS-{datetime.now().strftime('%Y%m')}-{next_id:04d}"


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Irsaliye Okuyucu baslatiliyor - DB=%s", _DB_CFG["database"])
    # Stok cache'i onceden doldur
    try:
        _stok_listesini_getir()
    except Exception:
        pass
    yield
    logger.info("Kapanıyor.")


app = FastAPI(title="NEXOR Irsaliye Okuyucu", lifespan=lifespan)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/health")
async def health():
    api_key_ok = bool(ANTHROPIC_API_KEY and ANTHROPIC_API_KEY.startswith("sk-ant-"))
    try:
        conn = get_conn()
        conn.close()
        db_ok = True
    except Exception as e:
        logger.warning("DB health hatasi: %s", e)
        db_ok = False
    return {
        "status": "ok" if (api_key_ok and db_ok) else "degraded",
        "anthropic_api_key": api_key_ok,
        "model": ANTHROPIC_MODEL,
        "db": db_ok,
        "db_name": _DB_CFG.get("database"),
        "stok_cache": len(_stok_urunler_cache) if _stok_urunler_cache else 0,
    }


@app.post("/api/parse-irsaliye", response_model=ParseSonucu)
async def parse_irsaliye_endpoint(foto: UploadFile = File(...)):
    if not foto.content_type or not foto.content_type.startswith("image/"):
        raise HTTPException(400, "Sadece resim dosyasi kabul edilir")

    image_bytes = await foto.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(413, "Dosya 10MB'dan buyuk olamaz")

    # Claude'a gonder
    logger.info("Vision parse: %s (%.1fKB)", foto.filename, len(image_bytes) / 1024)
    parsed = parse_irsaliye_with_claude(image_bytes, foto.content_type)

    # Fuzzy matching
    secilen_cari_id, cari_onerileri = _cari_oneri_bul(
        parsed.get("tedarikci_unvan", ""),
        parsed.get("tedarikci_vkn"),
    )

    kalemler: List[Kalem] = []
    for k in parsed.get("kalemler", []):
        secilen_urun_id, oneri = _stok_oneri_bul(
            k.get("kod", "") or "",
            k.get("ad", "") or "",
            cari_id=secilen_cari_id,
        )
        kalemler.append(Kalem(
            sira=int(k.get("sira", len(kalemler) + 1)),
            kod=k.get("kod", "") or "",
            ad=k.get("ad", "") or "",
            miktar=float(k.get("miktar", 0) or 0),
            birim=(k.get("birim") or "ADET").upper(),
            kaplama=k.get("kaplama"),
            oneriler=oneri,
            secilen_urun_id=secilen_urun_id,
        ))

    return ParseSonucu(
        tedarikci_unvan=parsed.get("tedarikci_unvan", ""),
        tedarikci_vkn=parsed.get("tedarikci_vkn"),
        cari_onerileri=cari_onerileri,
        secilen_cari_id=secilen_cari_id,
        cari_irsaliye_no=parsed.get("cari_irsaliye_no", ""),
        tarih=parsed.get("tarih", ""),
        arac_plaka=parsed.get("arac_plaka"),
        sofor_adi=parsed.get("sofor_adi"),
        kalemler=kalemler,
        notlar=parsed.get("notlar"),
    )


@app.get("/api/stok-ara")
async def stok_ara(q: str = "", cari_id: Optional[int] = None, limit: int = 20):
    """
    Manuel arama: kod veya ad ile fuzzy ara.
    cari_id verilirse o cariye ait urunler onceliklidir.
    """
    q = (q or "").strip()
    if len(q) < 2:
        return {"sonuclar": []}

    urunler = _stok_listesini_getir()
    if not urunler:
        return {"sonuclar": []}

    # Cari_id varsa once o cariye ait urunler
    oncelikli = [u for u in urunler if cari_id and u.get("cari_id") == cari_id]
    digerleri = [u for u in urunler if not (cari_id and u.get("cari_id") == cari_id)]

    sonuclar = []
    # Oncelikli grup icinde
    if oncelikli:
        adaylar = [u["kod"] + " " + u["ad"] for u in oncelikli]
        scores = process.extract(q, adaylar, scorer=fuzz.WRatio, limit=limit)
        for _t, score, idx in scores:
            if score < 40:
                break
            u = oncelikli[idx]
            sonuclar.append({
                "urun_id": u["id"], "urun_kodu": u["kod"], "urun_adi": u["ad"],
                "skor": float(score), "cari_oncelik": True,
            })

    # Kalan kapasiteyi genel arama ile doldur
    kalan = limit - len(sonuclar)
    if kalan > 0 and digerleri:
        adaylar = [u["kod"] + " " + u["ad"] for u in digerleri]
        scores = process.extract(q, adaylar, scorer=fuzz.WRatio, limit=kalan)
        for _t, score, idx in scores:
            if score < 50:
                break
            u = digerleri[idx]
            sonuclar.append({
                "urun_id": u["id"], "urun_kodu": u["kod"], "urun_adi": u["ad"],
                "skor": float(score), "cari_oncelik": False,
            })

    return {"sonuclar": sonuclar}


@app.post("/api/kaydet")
async def kaydet(data: KaydetRequest):
    """Onaylanan JSON'u siparis.giris_irsaliyeleri + satirlar tablosuna yaz"""
    if not data.kalemler:
        raise HTTPException(400, "En az 1 kalem gerekli")

    try:
        tarih_dt = datetime.strptime(data.tarih, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, f"Gecersiz tarih formati: {data.tarih} (YYYY-MM-DD bekleniyor)")

    conn = get_conn()
    cur = conn.cursor()
    try:
        # Irsaliye no uret
        irsaliye_no = _yeni_irsaliye_no(cur)

        # Ana kayit - TASLAK (NEXOR'da onaylanacak)
        cur.execute("""
            INSERT INTO siparis.giris_irsaliyeleri
                (irsaliye_no, cari_unvani, cari_irsaliye_no, tarih,
                 teslim_alan, arac_plaka, sofor_adi, durum, notlar)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, 'TASLAK', ?)
        """, (
            irsaliye_no,
            (data.cari_unvan or "")[:500],
            (data.cari_irsaliye_no or "")[:50],
            tarih_dt,
            (data.teslim_alan or "")[:100] or None,
            (data.arac_plaka or "")[:50] or None,
            (data.sofor_adi or "")[:200] or None,
            data.notlar or None,
        ))
        irsaliye_id = int(cur.fetchone()[0])

        # Satirlar
        yeni_eslesme_sayisi = 0
        for i, k in enumerate(data.kalemler, 1):
            if not k.ad or k.miktar <= 0:
                continue
            cur.execute("""
                INSERT INTO siparis.giris_irsaliye_satirlar
                    (irsaliye_id, satir_no, stok_kodu, stok_adi,
                     miktar, birim, kaplama, kalite_durumu)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'BEKLIYOR')
            """, (
                irsaliye_id,
                i,
                (k.kod or "")[:50],
                (k.ad or "")[:200],
                k.miktar,
                (k.birim or "ADET")[:20],
                (k.kaplama or "")[:100] or None,
            ))

            # OGREN: Kullanici bir urun_id sectiyse + cari biliniyorsa
            # musteri.musteri_urun_kodlari tablosuna ekle (yoksa)
            if data.secilen_cari_id and k.secilen_urun_id and k.kod:
                try:
                    cur.execute("""
                        IF NOT EXISTS (
                            SELECT 1 FROM musteri.musteri_urun_kodlari
                            WHERE cari_id = ? AND musteri_stok_kodu = ?
                        )
                        INSERT INTO musteri.musteri_urun_kodlari
                            (cari_id, musteri_stok_kodu, musteri_stok_adi,
                             urun_id, kaplama_hint, kullanim_sayisi, son_kullanim)
                        VALUES (?, ?, ?, ?, ?, 1, GETDATE())
                    """, (
                        data.secilen_cari_id, (k.kod or "")[:50],
                        data.secilen_cari_id, (k.kod or "")[:50],
                        (k.ad or "")[:250],
                        k.secilen_urun_id,
                        (k.kaplama or "")[:50] or None,
                    ))
                    if cur.rowcount > 0:
                        yeni_eslesme_sayisi += 1
                except Exception as e:
                    logger.warning("Ogrenme kaydi hatasi (satir %d): %s", i, e)

        conn.commit()
        logger.info("Giris irsaliyesi: %s (id=%d, %d kalem, %d yeni eslesme ogrenildi)",
                    irsaliye_no, irsaliye_id, len(data.kalemler), yeni_eslesme_sayisi)
        mesaj = f"Kaydedildi: {irsaliye_no} - NEXOR'da onaylanabilir (durum: TASLAK)"
        if yeni_eslesme_sayisi:
            mesaj += f"  · {yeni_eslesme_sayisi} yeni stok eşleşmesi öğrenildi"
        return {
            "basarili": True,
            "irsaliye_no": irsaliye_no,
            "irsaliye_id": irsaliye_id,
            "kalem_sayisi": len(data.kalemler),
            "yeni_eslesme": yeni_eslesme_sayisi,
            "mesaj": mesaj,
        }
    except Exception as e:
        conn.rollback()
        logger.exception("Kaydet hatasi: %s", e)
        raise HTTPException(500, f"DB kayit hatasi: {e}")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    # host="0.0.0.0" -> LAN'daki tum cihazlar erisebilir
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False, log_level="info")
