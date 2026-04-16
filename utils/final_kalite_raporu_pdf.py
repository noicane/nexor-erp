# -*- coding: utf-8 -*-
"""
NEXOR ERP - Final Kalite Raporu PDF
Kaplama turune gore sablon bazli kalite raporu uretir.
PDFTemplate motoru uzerinden calisir (raw canvas cizim icin tpl.canvas kullanilir).
"""
import os
from datetime import datetime, date

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white

from core.database import get_db_connection
from config import REPORT_OUTPUT_DIR
from utils.pdf_template import PDFTemplate, format_tarih

# Ek renkler (sablon ozel)
GRAY_400 = HexColor('#9CA3AF')
GRAY_200 = HexColor('#D1D5DB')
GRAY_100 = HexColor('#E5E7EB')
GREEN_CHECK = HexColor('#16A34A')


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
          fill=None, border=True, text_color=black, clip=False):
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
    c.setFillColor(black)
    if line2:
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


def _draw_step_row(c, y, h, lbl1, lbl2, value, olcu,
                   C_PARAM, C_CHAR, C_OLCU, C_TOL, C_SONUC, C_KAB, C_RED, MARGIN_L):
    """Proses adimi satiri ciz (Uygulama Tipi / Uygulama Sartlari)."""
    cx = MARGIN_L
    _cell(c, cx, y - h, C_PARAM, h)
    c.setFont("NexorFont", 4.5)
    c.setFillColor(black)
    c.drawString(cx + 1 * mm, y - h + h * 0.55, lbl1)
    c.drawString(cx + 1 * mm, y - h + h * 0.12, lbl2)
    cx += C_PARAM

    _cell(c, cx, y - h, C_CHAR, h, value, font_size=6, bold=True)
    cx += C_CHAR

    _cell(c, cx, y - h, C_OLCU, h, olcu, font_size=5.5, align="center")
    cx += C_OLCU

    _cell(c, cx, y - h, C_TOL, h)
    cx += C_TOL

    _cell(c, cx, y - h, C_SONUC, h, "UYGUN", font_size=5.5, align="center")
    cx += C_SONUC

    _cell(c, cx, y - h, C_KAB, h)
    _check(c, cx, y - h, C_KAB, h)
    cx += C_KAB

    _cell(c, cx, y - h, C_RED, h)


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
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Lot bilgilerini cek - is_emri_id varsa direkt ona git
        where_clause = ""
        params = []
        if is_emri_id:
            where_clause = "ie.id = ?"
            params = [is_emri_id]
        else:
            ana_lot = lot_no.replace('-SEV', '').strip()
            where_clause = """
                ie.lot_no = ? OR ie.lot_no = ?
            """
            params = [lot_no, ana_lot]

        cursor.execute(f"""
            SELECT
                ie.is_emri_no,
                ie.stok_kodu,
                ie.stok_adi,
                ie.toplam_miktar,
                COALESCE(b.kod, 'AD') as birim,
                COALESCE(c.unvan, ie.cari_unvani, '') as cari_unvani,
                COALESCE(kt.ad, ie.kaplama_tipi, '') as kaplama_adi,
                COALESCE(ie.kaplama_turu_id, u.kaplama_turu_id, h.kaplama_turu_id) as kaplama_turu_id,
                ci.irsaliye_no,
                ci.tarih as irs_tarihi,
                u.musteri_parca_no
            FROM siparis.is_emirleri ie
            LEFT JOIN stok.urunler u ON ie.urun_id = u.id
            LEFT JOIN tanim.uretim_hatlari h ON ie.hat_id = h.id
            LEFT JOIN tanim.kaplama_turleri kt ON COALESCE(ie.kaplama_turu_id, u.kaplama_turu_id, h.kaplama_turu_id) = kt.id
            LEFT JOIN musteri.cariler c ON ie.cari_id = c.id
            LEFT JOIN tanim.birimler b ON ie.birim_id = b.id
            LEFT JOIN siparis.cikis_irsaliyeleri ci ON ci.id = ?
            WHERE {where_clause}
        """, [irsaliye_id] + params)

        row = cursor.fetchone()
        if not row:
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
            'musteri_parca_no': (row[10] or '').strip(),
        }

        if not d['kaplama_turu_id']:
            raise Exception(f"Urun icin kaplama turu tanimli degil: {d['stok_kodu']}")

        sablon_id, adimlar, kontroller = _get_sablon(cursor, d['kaplama_turu_id'])
        if not sablon_id:
            raise Exception(f"Rapor sablonu bulunamadi (kaplama_turu_id={d['kaplama_turu_id']})")

        rapor_no = _get_next_rapor_no(cursor)
        rapor_tarihi = datetime.now()

        if not kontrol_eden:
            kontrol_eden = "MURAT SIMSEK"
        if not onaylayan:
            onaylayan = "ZUMRUT HILAL GUNAY"
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
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # ======================== PDF OLUSTUR ========================
    referans = d.get('musteri_parca_no') or d.get('stok_kodu') or ''
    referans_safe = ''.join(ch if ch.isalnum() or ch in '-_' else '_' for ch in referans)
    if referans_safe:
        dosya_adi = f"Fkk_{referans_safe}_{rapor_no}.pdf"
    else:
        dosya_adi = f"Fkk_{lot_no}_{rapor_no}.pdf"

    tpl = PDFTemplate(
        title="FINAL KALITE RAPORU",
        form_no=rapor_no,
        filename=dosya_adi,
    )
    c = tpl.canvas
    MARGIN_L = tpl.margin
    CONTENT_W = tpl.usable_w
    MARGIN_B = 8 * mm  # alt bosluk minimalize

    y = tpl.content_top
    rapor_tarih_str = rapor_tarihi.strftime("%d.%m.%Y")

    # ============================================================
    # HEADER BILGI TABLOSU (ozel layout - raw canvas)
    # ============================================================
    hdr_h = 14 * mm
    half_h = hdr_h / 2
    info_total = 62 * mm
    lbl_part = CONTENT_W - info_total

    # Sol taraf: is emri bilgileri
    _label_cell(c, MARGIN_L, y - half_h, lbl_part, half_h,
                "IS EMRI NO / WORK ORDER NO", "")
    _cell(c, MARGIN_L, y - hdr_h, lbl_part, half_h,
          d['is_emri_no'], font_size=8, bold=True, align="center")

    # Sag bilgi: 2 satir x 2 kolon
    ix = MARGIN_L + lbl_part
    c2 = 26 * mm
    c3 = info_total - c2

    _label_cell(c, ix, y - half_h, c2, half_h, "RAPOR TARIHI", "REPORT DATE")
    _cell(c, ix + c2, y - half_h, c3, half_h,
          rapor_tarih_str, font_size=8, bold=True, align="center")

    _label_cell(c, ix, y - hdr_h, c2, half_h, "RAPOR NO", "REPORT NO")
    _cell(c, ix + c2, y - hdr_h, c3, half_h,
          rapor_no, font_size=9, bold=True, align="center")

    y -= hdr_h

    # ============================================================
    # BILGI SATIRLARI (4 satir)
    # ============================================================
    rh = 6.5 * mm
    lbl_w = 20 * mm
    val1_w = 76 * mm
    lbl2_w = 22 * mm
    val2_w = CONTENT_W - lbl_w - val1_w - lbl2_w

    rows_info = [
        ("FIRMA ADI", "COMPANY NAME", d['cari_unvani'],
         "SARTNAME NO", "SPECIFICATION NO", ""),
        ("STOK KODU", "STOCK CODE", d['stok_kodu'],
         "OPERASYON ADI", "OPERATION NAME", d['kaplama_adi']),
        ("STOK ADI", "STOCK NAME", d['stok_adi'],
         "MIKTAR", "QUANTITY", f"{lot_miktar:,.0f}          {d['birim']}"),
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

    _label_cell(c, MARGIN_L, y - rh, irs_lbl_w, rh, "IRS. TARIHI", "WAYBILL DATE")
    _cell(c, MARGIN_L + irs_lbl_w, y - rh, irs_val_w, rh,
          format_tarih(d['irs_tarihi']), font_size=6.5, bold=True)

    nx = MARGIN_L + irs_lbl_w + irs_val_w
    _label_cell(c, nx, y - rh, irs_no_lbl_w, rh, "IRSALIYE NO", "WAYBILL NO")
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
    th = 7 * mm
    C_PARAM = 28 * mm
    C_CHAR = 62 * mm
    C_OLCU = 16 * mm
    C_TOL = 14 * mm
    C_SONUC = 18 * mm
    C_KAB = (CONTENT_W - C_PARAM - C_CHAR - C_OLCU - C_TOL - C_SONUC) / 2
    C_RED = C_KAB

    cx = MARGIN_L
    for lbl, lbl2, w in [
        ("KONTROL PARAMETRESI", "CONTROL PARAMETER", C_PARAM),
        ("KARAKTERISTIK", "CHARACTERISTIC", C_CHAR),
        ("OLCU ALETI", "MEASURIN", C_OLCU),
        ("TOLERANS", "MIN-MAX", C_TOL),
        ("SONUC", "RESULT", C_SONUC),
        ("KAB.", "OK", C_KAB),
        ("RED", "NOK", C_RED),
    ]:
        _cell(c, cx, y - th, w, th, fill=GRAY_200)
        c.setFont("NexorFont-Bold", 5)
        c.setFillColor(black)
        c.drawCentredString(cx + w / 2, y - th + 5 * mm, lbl)
        c.setFont("NexorFont", 4)
        c.drawCentredString(cx + w / 2, y - th + 1.5 * mm, lbl2)
        cx += w
    y -= th

    # ============================================================
    # PROSES ADIMLARI
    # ============================================================
    sth = 5 * mm
    srh = 5 * mm

    for adim in adimlar:
        sira, adi_tr, adi_en, uyg_tipi, uyg_sart, olcu = adim

        needed = sth + srh * 2
        if y - needed < MARGIN_B + 14 * mm:
            y = tpl.new_page()

        # Adim basligi
        _cell(c, MARGIN_L, y - sth, CONTENT_W, sth, fill=GRAY_100)
        title = f" {adi_tr}/{adi_en}" if adi_en else f" {adi_tr}"
        c.setFont("NexorFont-Bold", 6.5)
        c.setFillColor(black)
        c.drawString(MARGIN_L + 1.5 * mm, y - sth + 1.5 * mm, title)
        y -= sth

        # Uygulama Tipi
        _draw_step_row(c, y, srh, "UYGULAMA TIPI (TYPE OF", "PRACTICE)",
                       uyg_tipi, olcu, C_PARAM, C_CHAR, C_OLCU, C_TOL, C_SONUC, C_KAB, C_RED, MARGIN_L)
        y -= srh

        # Uygulama Sartlari
        _draw_step_row(c, y, srh, "UYGULAMA SARTLARI", "(CONDITION OF PRACTICE)",
                       uyg_sart, olcu, C_PARAM, C_CHAR, C_OLCU, C_TOL, C_SONUC, C_KAB, C_RED, MARGIN_L)
        y -= srh

    # ============================================================
    # KONTROL TESTLERI
    # ============================================================
    for kontrol in kontroller:
        (k_sira, k_adi_tr, k_adi_en, k_karakt, k_acik_tr, k_acik_en,
         k_olcu, k_birim, k_min, k_max, k_deger_mi) = kontrol

        needed = sth + 6.5 * mm
        if y - needed < MARGIN_B + 14 * mm:
            y = tpl.new_page()

        # Kontrol basligi
        title = f" {k_adi_tr}/ {k_adi_en}" if k_adi_en else f" {k_adi_tr}"
        _cell(c, MARGIN_L, y - sth, CONTENT_W, sth, fill=GRAY_100)
        c.setFont("NexorFont-Bold", 6.5)
        c.setFillColor(black)
        c.drawString(MARGIN_L + 1.5 * mm, y - sth + 1.5 * mm, title)
        y -= sth

        # Detay satiri
        drh = 5 * mm
        cx = MARGIN_L
        _cell(c, cx, y - drh, C_PARAM, drh, k_karakt or '', font_size=5.5)
        cx += C_PARAM

        acik = k_acik_tr or ''
        _cell(c, cx, y - drh, C_CHAR, drh, acik, font_size=5, clip=True)
        cx += C_CHAR

        _cell(c, cx, y - drh, C_OLCU, drh, k_olcu or '', font_size=5.5, align="center")
        cx += C_OLCU

        tol = ""
        if k_min is not None and k_max is not None:
            tol = f"{int(k_min)}    {int(k_max)}"
        _cell(c, cx, y - drh, C_TOL, drh, tol, font_size=5.5, align="center")
        cx += C_TOL

        if k_deger_mi and kalinlik_olcumleri:
            _cell(c, cx, y - drh, C_SONUC, drh, kalinlik_olcumleri,
                  font_size=4.5, align="center")
        else:
            _cell(c, cx, y - drh, C_SONUC, drh, "UYGUN", font_size=5.5, align="center")
        cx += C_SONUC

        _cell(c, cx, y - drh, C_KAB, drh)
        _check(c, cx, y - drh, C_KAB, drh)
        cx += C_KAB
        _cell(c, cx, y - drh, C_RED, drh)
        y -= drh

    # ============================================================
    # FOOTER - IMZALAR
    # ============================================================
    y -= 3 * mm
    imza_h = 6 * mm
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
    c.setFillColor(tpl.theme['muted'])
    c.drawString(MARGIN_L, y - 4 * mm, "Sayfa No    1 of 1")

    path = tpl.finish(open_file=False)
    return path


def batch_final_kalite_raporu(irsaliye_id: int, kontrol_eden: str = None,
                                onaylayan: str = None) -> list:
    """
    Bir irsaliyedeki tum satirlar (ve birlestirilmis lot_no'lar) icin toplu rapor uret.
    Sevkiyat irsaliyesinde ayni stok kodlu paketler tek satira toplaniyor (lot_no virgullu).
    Bu fonksiyon her bir lot icin ayri rapor uretir.

    Returns:
        list: [(lot_no, pdf_path), ...]
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cis.lot_no, cis.is_emri_id, cis.miktar
            FROM siparis.cikis_irsaliye_satirlar cis
            WHERE cis.irsaliye_id = ?
            ORDER BY cis.satir_no
        """, (irsaliye_id,))
        satirlar = cursor.fetchall()
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # Tum lot'lari topla (virgullu olanlari ayir)
    tum_lotlar = []
    for lot_no_str, is_emri_id, miktar in satirlar:
        if not lot_no_str:
            continue
        for lot in str(lot_no_str).split(','):
            lot = lot.strip()
            if lot:
                tum_lotlar.append((lot, is_emri_id))

    # Mukerrer lot'lari temizle (set ile)
    gorulen = set()
    benzersiz = []
    for lot, ie_id in tum_lotlar:
        if lot not in gorulen:
            gorulen.add(lot)
            benzersiz.append((lot, ie_id))

    sonuclar = []
    for lot_no, is_emri_id in benzersiz:
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
