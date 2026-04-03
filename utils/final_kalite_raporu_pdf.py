# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Final Kalite Raporu PDF
Kaplama turune gore sablon bazli kalite raporu uretir.
Birebir musteri formatina uygun (ATMO layout).
"""
import os
from datetime import datetime, date
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas

from core.database import get_db_connection
from config import REPORT_OUTPUT_DIR
from core.firma_bilgileri import get_firma_bilgileri, get_firma_logo_path
from utils.etiket_yazdir import _register_dejavu_fonts

# Renkler
PRIMARY = HexColor('#DC2626')
DARK_BG = HexColor('#1F2937')
GRAY_600 = HexColor('#4B5563')
GRAY_400 = HexColor('#9CA3AF')
GRAY_200 = HexColor('#D1D5DB')
GRAY_100 = HexColor('#E5E7EB')
WHITE = white
BLACK = black
GREEN_CHECK = HexColor('#16A34A')

PAGE_W, PAGE_H = A4
MARGIN_L = 12 * mm
MARGIN_R = 12 * mm
MARGIN_T = 10 * mm
MARGIN_B = 10 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


def _format_tarih(val):
    if val is None:
        return "-"
    if isinstance(val, (datetime, date)):
        return val.strftime("%d.%m.%Y")
    return str(val)[:10]


def _get_sablon(cursor, kaplama_turu_id):
    """Kaplama turune gore aktif sablonu getir."""
    cursor.execute("""
        SELECT id, sablon_adi
        FROM kalite.rapor_sablonlari
        WHERE kaplama_turu_id = ? AND aktif_mi = 1
    """, (kaplama_turu_id,))
    row = cursor.fetchone()
    if not row:
        return None, [], []

    sablon_id = row[0]

    cursor.execute("""
        SELECT sira, adim_adi_tr, adim_adi_en, uygulama_tipi, uygulama_sartlari, olcu_aleti
        FROM kalite.rapor_sablon_adimlari
        WHERE sablon_id = ?
        ORDER BY sira
    """, (sablon_id,))
    adimlar = cursor.fetchall()

    cursor.execute("""
        SELECT sira, kontrol_adi_tr, kontrol_adi_en, karakteristik,
               aciklama_tr, aciklama_en, olcu_aleti, birim,
               tolerans_min, tolerans_max, deger_girilir_mi
        FROM kalite.rapor_sablon_kontroller
        WHERE sablon_id = ?
        ORDER BY sira
    """, (sablon_id,))
    kontroller = cursor.fetchall()

    return sablon_id, adimlar, kontroller


def _get_next_rapor_no(cursor):
    """Siradaki rapor numarasini olustur."""
    cursor.execute("""
        SELECT MAX(CAST(rapor_no AS INT))
        FROM kalite.final_kalite_raporlari
        WHERE ISNUMERIC(rapor_no) = 1
    """)
    row = cursor.fetchone()
    last = row[0] if row and row[0] else 70000
    return str(last + 1)


def _cell(c, x, y, w, h, text="", font_size=6, bold=False, align="left",
          fill=None, border=True, text_color=BLACK, clip=False):
    """Tablo hucresi ciz."""
    if fill:
        c.setFillColor(fill)
        c.rect(x, y, w, h, fill=1, stroke=0)
    if border:
        c.setStrokeColor(GRAY_400)
        c.setLineWidth(0.4)
        c.rect(x, y, w, h, fill=0, stroke=1)
    if text:
        fn = "NexorFont-Bold" if bold else "NexorFont"
        c.setFont(fn, font_size)
        c.setFillColor(text_color)
        pad = 1.5 * mm
        ty = y + h / 2 - font_size * 0.35
        txt = str(text)
        if clip:
            max_w = w - 2 * pad
            while c.stringWidth(txt, fn, font_size) > max_w and len(txt) > 1:
                txt = txt[:-1]
        if align == "center":
            c.drawCentredString(x + w / 2, ty, txt)
        elif align == "right":
            c.drawRightString(x + w - pad, ty, txt)
        else:
            c.drawString(x + pad, ty, txt)


def _label_cell(c, x, y, w, h, line1, line2=""):
    """Iki satirli label hucresi (TR/EN)."""
    c.setStrokeColor(GRAY_400)
    c.setLineWidth(0.4)
    c.setFillColor(GRAY_100)
    c.rect(x, y, w, h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    if line2:
        # 2 satir: ust %60, alt %25 pozisyonunda
        c.setFont("NexorFont-Bold", 5.5)
        c.drawString(x + 1.5 * mm, y + h * 0.52, line1)
        c.setFont("NexorFont", 4)
        c.drawString(x + 1.5 * mm, y + h * 0.18, line2)
    else:
        c.setFont("NexorFont-Bold", 5.5)
        c.drawString(x + 1.5 * mm, y + h / 2 - 1.5 * mm, line1)


def _check(c, x, y, w, h):
    """Tick isareti ciz."""
    cx, cy = x + w / 2, y + h / 2
    c.setStrokeColor(GREEN_CHECK)
    c.setLineWidth(1.5)
    c.line(cx - 2 * mm, cy, cx - 0.5 * mm, cy - 2 * mm)
    c.line(cx - 0.5 * mm, cy - 2 * mm, cx + 2.5 * mm, cy + 2 * mm)


def final_kalite_raporu_pdf(
    lot_no: str,
    irsaliye_id: int = None,
    is_emri_id: int = None,
    kalinlik_olcumleri: str = None,
    kontrol_eden: str = None,
    onaylayan: str = None,
    sonuclar: dict = None,
) -> str:
    """
    Final Kalite Raporu PDF olustur.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Lot bilgilerini cek
    where_clause = ""
    params = []
    if is_emri_id:
        where_clause = "ie.id = ?"
        params = [is_emri_id]
    else:
        where_clause = """
            ie.id IN (
                SELECT TOP 1 cis.is_emri_id
                FROM siparis.cikis_irsaliye_satirlar cis
                WHERE cis.lot_no = ? AND cis.irsaliye_id = COALESCE(?, cis.irsaliye_id)
            )
        """
        params = [lot_no, irsaliye_id]

    cursor.execute(f"""
        SELECT
            ie.is_emri_no,
            ie.stok_kodu,
            ie.stok_adi,
            ie.toplam_miktar,
            COALESCE(b.kod, 'AD') as birim,
            COALESCE(c.unvan, ie.cari_unvani, '') as cari_unvani,
            COALESCE(kt.ad, ie.kaplama_tipi, '') as kaplama_adi,
            COALESCE(ie.kaplama_turu_id, u.kaplama_turu_id) as kaplama_turu_id,
            ci.irsaliye_no,
            ci.tarih as irs_tarihi
        FROM siparis.is_emirleri ie
        LEFT JOIN stok.urunler u ON ie.urun_id = u.id
        LEFT JOIN tanim.kaplama_turleri kt ON COALESCE(ie.kaplama_turu_id, u.kaplama_turu_id) = kt.id
        LEFT JOIN musteri.cariler c ON ie.cari_id = c.id
        LEFT JOIN tanim.birimler b ON ie.birim_id = b.id
        LEFT JOIN siparis.cikis_irsaliye_satirlar cis ON cis.is_emri_id = ie.id AND cis.lot_no = ?
        LEFT JOIN siparis.cikis_irsaliyeleri ci ON cis.irsaliye_id = ci.id
        WHERE {where_clause}
    """, [lot_no] + params)

    row = cursor.fetchone()
    if not row:
        conn.close()
        raise Exception(f"Lot bilgisi bulunamadi: {lot_no}")

    d = {
        'is_emri_no': str(row[0] or ''),
        'stok_kodu': row[1] or '',
        'stok_adi': row[2] or '',
        'miktar': row[3] or 0,
        'birim': row[4] or 'AD',
        'cari_unvani': row[5] or '',
        'kaplama_adi': (row[6] or '').upper(),
        'kaplama_turu_id': row[7],
        'irsaliye_no': row[8] or '',
        'irs_tarihi': row[9],
    }

    if not d['kaplama_turu_id']:
        conn.close()
        raise Exception(f"Urun icin kaplama turu tanimli degil: {d['stok_kodu']}")

    sablon_id, adimlar, kontroller = _get_sablon(cursor, d['kaplama_turu_id'])
    if not sablon_id:
        conn.close()
        raise Exception(f"Rapor sablonu bulunamadi (kaplama_turu_id={d['kaplama_turu_id']})")

    rapor_no = _get_next_rapor_no(cursor)
    rapor_tarihi = datetime.now()

    if not kontrol_eden:
        kontrol_eden = "MURAT ŞİMŞEK"
    if not onaylayan:
        onaylayan = "ZÜMRÜT HİLAL GÜNAY"
    if sonuclar is None:
        sonuclar = {}

    lot_miktar = d['miktar']
    if irsaliye_id:
        cursor.execute("""
            SELECT miktar FROM siparis.cikis_irsaliye_satirlar
            WHERE irsaliye_id = ? AND lot_no = ?
        """, (irsaliye_id, lot_no))
        mrow = cursor.fetchone()
        if mrow:
            lot_miktar = mrow[0]

    # DB kayit
    cursor.execute("""
        INSERT INTO kalite.final_kalite_raporlari
            (rapor_no, sablon_id, irsaliye_id, is_emri_id, lot_no, miktar, birim,
             kalinlik_olcumleri, kontrol_eden, onaylayan, sonuc, rapor_tarihi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rapor_no, sablon_id, irsaliye_id, is_emri_id, lot_no,
        lot_miktar, d['birim'], kalinlik_olcumleri or '',
        kontrol_eden, onaylayan, 'UYGUN', rapor_tarihi
    ))
    conn.commit()
    conn.close()

    # ======================== PDF OLUSTUR ========================
    _register_dejavu_fonts()
    logo_path = get_firma_logo_path()

    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dosya_adi = f"FKR_{lot_no}_{rapor_no}.pdf"
    pdf_path = str(REPORT_OUTPUT_DIR / dosya_adi)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setTitle(f"Final Kalite Raporu - {lot_no}")

    y = PAGE_H - MARGIN_T
    rapor_tarih_str = rapor_tarihi.strftime("%d.%m.%Y")

    # ============================================================
    # HEADER: [LOGO] [BASLIK] [IE_LBL | RTARIHI_LBL | RTARIHI_VAL]
    #                         [IE_VAL | RNO_LBL     | RNO_VAL    ]
    # ============================================================
    hdr_h = 22 * mm
    half_h = hdr_h / 2
    logo_w = 30 * mm
    info_total = 62 * mm
    title_w = CONTENT_W - logo_w - info_total

    # Logo
    _cell(c, MARGIN_L, y - hdr_h, logo_w, hdr_h)
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, MARGIN_L + 2 * mm, y - hdr_h + 2 * mm,
                        width=logo_w - 4 * mm, height=hdr_h - 4 * mm,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Baslik
    tx = MARGIN_L + logo_w
    _cell(c, tx, y - hdr_h, title_w, hdr_h)
    c.setFont("NexorFont-Bold", 10)
    c.setFillColor(BLACK)
    c.drawCentredString(tx + title_w / 2, y - 8 * mm,
                        "FİNAL KALİTE RAPORU (FINAL CONTROL")
    c.drawCentredString(tx + title_w / 2, y - 14 * mm, "REPORT)")

    # Sag bilgi: 2 satir x 3 kolon
    ix = tx + title_w
    c1 = 26 * mm   # is emri lbl/deger (genis)
    c2 = 18 * mm   # rapor tarihi/no lbl
    c3 = info_total - c1 - c2  # tarih/no deger

    # Ust satir: [IS EMRI NO lbl] [RAPOR TARIHI lbl] [tarih deger]
    _label_cell(c, ix, y - half_h, c1, half_h, "İŞ EMRİ NO", "WORK ORDER NO")
    _label_cell(c, ix + c1, y - half_h, c2, half_h, "RAPOR TARİHİ", "REPORT DATE")
    _cell(c, ix + c1 + c2, y - half_h, c3, half_h,
          rapor_tarih_str, font_size=8, bold=True, align="center")

    # Alt satir: [is emri deger] [RAPOR NO lbl] [rapor no deger]
    _cell(c, ix, y - hdr_h, c1, half_h,
          d['is_emri_no'], font_size=5.5, bold=True, align="center")
    _label_cell(c, ix + c1, y - hdr_h, c2, half_h, "RAPOR NO", "REPORT NO")
    _cell(c, ix + c1 + c2, y - hdr_h, c3, half_h,
          rapor_no, font_size=9, bold=True, align="center")

    y -= hdr_h

    # ============================================================
    # BILGI SATIRLARI (4 satir)
    # ============================================================
    rh = 7.5 * mm  # satir yuksekligi
    lbl_w = 20 * mm
    val1_w = 76 * mm
    lbl2_w = 22 * mm
    val2_w = CONTENT_W - lbl_w - val1_w - lbl2_w

    rows_info = [
        ("FİRMA ADI", "COMPANY NAME", d['cari_unvani'],
         "ŞARTNAME NO", "SPECIFICATION NO", ""),
        ("STOK KODU", "STOCK CODE", d['stok_kodu'],
         "OPERASYON ADI", "OPERATION NAME", d['kaplama_adi']),
        ("STOK ADI", "STOCK NAME", d['stok_adi'],
         "MİKTAR", "QUANTITY", f"{lot_miktar:,.0f}          {d['birim']}"),
    ]

    for l1, l1e, v1, l2, l2e, v2 in rows_info:
        _label_cell(c, MARGIN_L, y - rh, lbl_w, rh, l1, l1e)
        _cell(c, MARGIN_L + lbl_w, y - rh, val1_w, rh,
              v1, font_size=6.5, bold=True, clip=True)
        x2 = MARGIN_L + lbl_w + val1_w
        _label_cell(c, x2, y - rh, lbl2_w, rh, l2, l2e)
        _cell(c, x2 + lbl2_w, y - rh, val2_w, rh,
              v2, font_size=7, bold=True)
        y -= rh

    # Irsaliye satiri
    irs_lbl_w = 22 * mm
    irs_val_w = 20 * mm
    irs_no_lbl_w = 20 * mm
    irs_no_val_w = 38 * mm
    lot_lbl_w = 14 * mm
    lot_val_w = CONTENT_W - irs_lbl_w - irs_val_w - irs_no_lbl_w - irs_no_val_w - lot_lbl_w

    _label_cell(c, MARGIN_L, y - rh, irs_lbl_w, rh, "İRS. TARİHİ", "WAYBILL DATE")
    _cell(c, MARGIN_L + irs_lbl_w, y - rh, irs_val_w, rh,
          _format_tarih(d['irs_tarihi']), font_size=6.5, bold=True)

    nx = MARGIN_L + irs_lbl_w + irs_val_w
    _label_cell(c, nx, y - rh, irs_no_lbl_w, rh, "İRSALİYE NO", "WAYBILL NO")
    _cell(c, nx + irs_no_lbl_w, y - rh, irs_no_val_w, rh,
          d['irsaliye_no'], font_size=6, bold=True)

    nx2 = nx + irs_no_lbl_w + irs_no_val_w
    _label_cell(c, nx2, y - rh, lot_lbl_w, rh, "LOT NO", "LOT NO")
    _cell(c, nx2 + lot_lbl_w, y - rh, lot_val_w, rh,
          lot_no, font_size=6.5, bold=True)
    y -= rh

    # ============================================================
    # TABLO HEADER
    # ============================================================
    th = 8 * mm
    # Kolon genislikleri
    C_PARAM = 28 * mm
    C_CHAR = 62 * mm
    C_OLCU = 16 * mm
    C_TOL = 14 * mm
    C_SONUC = 18 * mm
    C_KAB = (CONTENT_W - C_PARAM - C_CHAR - C_OLCU - C_TOL - C_SONUC) / 2
    C_RED = C_KAB

    cx = MARGIN_L
    for lbl, lbl2, w in [
        ("KONTROL PARAMETRESİ", "CONTROL PARAMETER", C_PARAM),
        ("KARAKTERİSTİK", "CHARACTERISTIC", C_CHAR),
        ("ÖLÇÜ ALETİ", "MEASURİN", C_OLCU),
        ("TOLERANS", "MİN-MAX", C_TOL),
        ("SONUÇ", "RESULT", C_SONUC),
        ("KAB.", "OK", C_KAB),
        ("RED", "NOK", C_RED),
    ]:
        _cell(c, cx, y - th, w, th, fill=GRAY_200)
        c.setFont("NexorFont-Bold", 5)
        c.setFillColor(BLACK)
        c.drawCentredString(cx + w / 2, y - th + 5 * mm, lbl)
        c.setFont("NexorFont", 4)
        c.drawCentredString(cx + w / 2, y - th + 1.5 * mm, lbl2)
        cx += w
    y -= th

    # ============================================================
    # PROSES ADIMLARI
    # ============================================================
    sth = 5.5 * mm  # step title h
    srh = 6 * mm    # step row h (2 satirli label icin)

    for adim in adimlar:
        sira, adi_tr, adi_en, uyg_tipi, uyg_sart, olcu = adim

        needed = sth + srh * 2
        if y - needed < MARGIN_B + 20 * mm:
            c.showPage()
            y = PAGE_H - MARGIN_T

        # Adim basligi
        _cell(c, MARGIN_L, y - sth, CONTENT_W, sth, fill=GRAY_100)
        title = f" {adi_tr}/{adi_en}" if adi_en else f" {adi_tr}"
        c.setFont("NexorFont-Bold", 6.5)
        c.setFillColor(BLACK)
        c.drawString(MARGIN_L + 1.5 * mm, y - sth + 1.5 * mm, title)
        y -= sth

        # Uygulama Tipi
        _draw_step_row(c, y, srh, "UYGULAMA TİPİ (TYPE OF", "PRACTICE)",
                       uyg_tipi, olcu, C_PARAM, C_CHAR, C_OLCU, C_TOL, C_SONUC, C_KAB, C_RED)
        y -= srh

        # Uygulama Sartlari
        _draw_step_row(c, y, srh, "UYGULAMA ŞARTLARI", "(CONDITION OF PRACTICE)",
                       uyg_sart, olcu, C_PARAM, C_CHAR, C_OLCU, C_TOL, C_SONUC, C_KAB, C_RED)
        y -= srh

    # ============================================================
    # KONTROL TESTLERI
    # ============================================================
    for kontrol in kontroller:
        (k_sira, k_adi_tr, k_adi_en, k_karakt, k_acik_tr, k_acik_en,
         k_olcu, k_birim, k_min, k_max, k_deger_mi) = kontrol

        needed = sth + 6.5 * mm
        if y - needed < MARGIN_B + 20 * mm:
            c.showPage()
            y = PAGE_H - MARGIN_T

        # Kontrol basligi
        title = f" {k_adi_tr}/ {k_adi_en}" if k_adi_en else f" {k_adi_tr}"
        _cell(c, MARGIN_L, y - sth, CONTENT_W, sth, fill=GRAY_100)
        c.setFont("NexorFont-Bold", 6.5)
        c.setFillColor(BLACK)
        c.drawString(MARGIN_L + 1.5 * mm, y - sth + 1.5 * mm, title)
        y -= sth

        # Detay satiri
        drh = 6 * mm
        cx = MARGIN_L
        _cell(c, cx, y - drh, C_PARAM, drh, k_karakt or '', font_size=5.5)
        cx += C_PARAM

        # Aciklama - metin uzunsa kirp
        acik = k_acik_tr or ''
        _cell(c, cx, y - drh, C_CHAR, drh, acik, font_size=5, clip=True)
        cx += C_CHAR

        _cell(c, cx, y - drh, C_OLCU, drh, k_olcu or '', font_size=5.5, align="center")
        cx += C_OLCU

        # Tolerans
        tol = ""
        if k_min is not None and k_max is not None:
            tol = f"{int(k_min)}    {int(k_max)}"
        _cell(c, cx, y - drh, C_TOL, drh, tol, font_size=5.5, align="center")
        cx += C_TOL

        # Sonuc/olcum
        if k_deger_mi and kalinlik_olcumleri:
            _cell(c, cx, y - drh, C_SONUC, drh, kalinlik_olcumleri,
                  font_size=4.5, align="center")
        else:
            _cell(c, cx, y - drh, C_SONUC, drh, "UYGUN", font_size=5.5, align="center")
        cx += C_SONUC

        # KAB + RED
        _cell(c, cx, y - drh, C_KAB, drh)
        _check(c, cx, y - drh, C_KAB, drh)
        cx += C_KAB
        _cell(c, cx, y - drh, C_RED, drh)
        y -= drh

    # ============================================================
    # FOOTER - IMZALAR
    # ============================================================
    y -= 6 * mm
    imza_h = 7 * mm
    half = CONTENT_W / 2

    _cell(c, MARGIN_L, y - imza_h, half, imza_h, "KONTROL EDEN",
          font_size=7, bold=True, align="center", fill=GRAY_200)
    _cell(c, MARGIN_L + half, y - imza_h, half, imza_h, "ONAYLAYAN",
          font_size=7, bold=True, align="center", fill=GRAY_200)
    y -= imza_h

    _cell(c, MARGIN_L, y - imza_h, half, imza_h, kontrol_eden,
          font_size=6.5, align="center")
    _cell(c, MARGIN_L + half, y - imza_h, half, imza_h, onaylayan,
          font_size=6.5, align="center")
    y -= imza_h

    # Sayfa no
    c.setFont("NexorFont", 5.5)
    c.setFillColor(GRAY_600)
    c.drawString(MARGIN_L, y - 4 * mm, "Sayfa No    1 of 1")
    c.drawRightString(PAGE_W - MARGIN_R, y - 4 * mm, "22 / 17.05.2018 / 22")

    c.save()
    return pdf_path


def _draw_step_row(c, y, h, lbl1, lbl2, value, olcu,
                   C_PARAM, C_CHAR, C_OLCU, C_TOL, C_SONUC, C_KAB, C_RED):
    """Proses adimi satiri ciz (Uygulama Tipi / Uygulama Sartlari)."""
    cx = MARGIN_L
    # Param label (2 satir)
    _cell(c, cx, y - h, C_PARAM, h)
    c.setFont("NexorFont", 4.5)
    c.setFillColor(BLACK)
    c.drawString(cx + 1 * mm, y - h + h * 0.55, lbl1)
    c.drawString(cx + 1 * mm, y - h + h * 0.12, lbl2)
    cx += C_PARAM

    # Karakteristik deger
    _cell(c, cx, y - h, C_CHAR, h, value, font_size=6, bold=True)
    cx += C_CHAR

    # Olcu aleti
    _cell(c, cx, y - h, C_OLCU, h, olcu, font_size=5.5, align="center")
    cx += C_OLCU

    # Tolerans (bos)
    _cell(c, cx, y - h, C_TOL, h)
    cx += C_TOL

    # Sonuc
    _cell(c, cx, y - h, C_SONUC, h, "UYGUN", font_size=5.5, align="center")
    cx += C_SONUC

    # KAB check
    _cell(c, cx, y - h, C_KAB, h)
    _check(c, cx, y - h, C_KAB, h)
    cx += C_KAB

    # RED (bos)
    _cell(c, cx, y - h, C_RED, h)


def batch_final_kalite_raporu(irsaliye_id: int, kontrol_eden: str = None,
                                onaylayan: str = None) -> list:
    """
    Bir irsaliyedeki tum satirlar icin toplu rapor uret.

    Returns:
        list: [(lot_no, pdf_path), ...]
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cis.lot_no, cis.is_emri_id, cis.miktar
        FROM siparis.cikis_irsaliye_satirlar cis
        WHERE cis.irsaliye_id = ?
        ORDER BY cis.satir_no
    """, (irsaliye_id,))
    satirlar = cursor.fetchall()
    conn.close()

    sonuclar = []
    for lot_no, is_emri_id, miktar in satirlar:
        if not lot_no:
            continue
        try:
            pdf_path = final_kalite_raporu_pdf(
                lot_no=lot_no,
                irsaliye_id=irsaliye_id,
                is_emri_id=is_emri_id,
                kontrol_eden=kontrol_eden,
                onaylayan=onaylayan,
            )
            sonuclar.append((lot_no, pdf_path))
        except Exception as e:
            sonuclar.append((lot_no, f"HATA: {e}"))

    return sonuclar
