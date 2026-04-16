# -*- coding: utf-8 -*-
"""
NEXOR ERP - Birlesik Is Emri + Depo Cikis PDF
PDFTemplate motoru uzerinden calisir.
"""
import os
import subprocess
from datetime import datetime, date

from reportlab.lib.units import mm

from core.database import get_db_connection
from utils.pdf_template import PDFTemplate, format_tarih


def _fmt_miktar(val):
    if val is None:
        return "0"
    try:
        return f"{int(float(val)):,}".replace(",", ".")
    except Exception:
        return str(val)


def birlesik_pdf_olustur(is_emri_ids: list) -> str:
    """
    Birden fazla is emri + ilgili depo cikis emirlerini tek PDF'te listeler.

    Args:
        is_emri_ids: Is emri ID listesi

    Returns:
        str: Olusturulan PDF dosya yolu
    """
    if not is_emri_ids:
        raise ValueError("En az bir is emri ID gerekli")

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Is emirlerini cek
        placeholders = ','.join(['?' for _ in is_emri_ids])
        cursor.execute(f"""
            SELECT
                ie.id, ie.is_emri_no, ie.tarih, ie.termin_tarihi,
                ie.cari_unvani, ie.stok_kodu, ie.stok_adi, ie.kaplama_tipi,
                ISNULL(ie.toplam_miktar, ie.planlanan_miktar) as miktar,
                ie.birim, ie.lot_no, ie.durum,
                h.ad as hat_adi
            FROM siparis.is_emirleri ie
            LEFT JOIN tanim.uretim_hatlari h ON ie.hat_id = h.id
            WHERE ie.id IN ({placeholders}) AND ie.silindi_mi = 0
            ORDER BY ie.is_emri_no
        """, is_emri_ids)
        is_emirleri = cursor.fetchall()

        # Ilgili depo cikis emirlerini cek
        cursor.execute(f"""
            SELECT
                dce.is_emri_id, dce.emir_no, dce.stok_kodu, dce.stok_adi,
                dce.talep_miktar, dce.durum,
                kd.ad as kaynak_depo, hd.ad as hedef_depo
            FROM stok.depo_cikis_emirleri dce
            LEFT JOIN tanim.depolar kd ON dce.kaynak_depo_id = kd.id
            LEFT JOIN tanim.depolar hd ON dce.hedef_depo_id = hd.id
            WHERE dce.is_emri_id IN ({placeholders})
            ORDER BY dce.is_emri_id, dce.emir_no
        """, is_emri_ids)
        depo_cikislar = cursor.fetchall()
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # Depo cikislarini is emrine gore grupla
    cikis_map = {}
    for row in depo_cikislar:
        ie_id = row[0]
        if ie_id not in cikis_map:
            cikis_map[ie_id] = []
        cikis_map[ie_id].append(row)

    # PDF olustur
    dosya_adi = f"birlesik_is_emri_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    tpl = PDFTemplate(
        title="BIRLESIK IS EMRI + DEPO CIKIS LISTESI",
        form_no=f"{len(is_emirleri)} adet",
        filename=dosya_adi,
    )
    c = tpl.canvas
    y = tpl.content_top

    # ── IS EMIRLERI TABLOSU ──
    y = tpl.section("IS EMIRLERI", y)

    headers = ["Is Emri No", "Tarih", "Termin", "Musteri", "Urun", "Kaplama", "Miktar", "Durum", "Hat"]
    col_widths = [22 * mm, 18 * mm, 18 * mm, 30 * mm, 24 * mm, 16 * mm, 16 * mm, 14 * mm, 18 * mm]

    rows = []
    for ie in is_emirleri:
        rows.append([
            str(ie[1] or ''),
            format_tarih(ie[2]),
            format_tarih(ie[3]),
            str(ie[4] or '')[:18],
            str(ie[5] or '')[:12],
            str(ie[7] or '')[:8],
            _fmt_miktar(ie[8]),
            str(ie[11] or '')[:10],
            str(ie[12] or '')[:10],
        ])

    y = tpl.table(y, headers, rows, col_widths)

    # ── DEPO CIKIS DETAYLARI ──
    has_cikis = any(cikis_map.get(ie[0]) for ie in is_emirleri)
    if has_cikis:
        y -= 2 * mm
        y = tpl.section("DEPO CIKIS EMIRLERI", y)

        dc_headers = ["Is Emri", "Emir No", "Stok Kodu", "Stok Adi", "Miktar", "Kaynak", "Hedef", "Durum"]
        dc_widths = [22 * mm, 18 * mm, 22 * mm, 36 * mm, 16 * mm, 22 * mm, 22 * mm, 18 * mm]

        dc_rows = []
        for ie in is_emirleri:
            cikislar = cikis_map.get(ie[0], [])
            for dc in cikislar:
                dc_rows.append([
                    str(ie[1] or '')[:12],
                    str(dc[1] or ''),
                    str(dc[2] or '')[:12],
                    str(dc[3] or '')[:20],
                    _fmt_miktar(dc[4]),
                    str(dc[6] or '')[:12],
                    str(dc[7] or '')[:12],
                    str(dc[5] or '')[:10],
                ])

        if dc_rows:
            y = tpl.table(y, dc_headers, dc_rows, dc_widths)

    # ── IMZA ALANI ──
    y -= 6 * mm
    tpl.signature_row(y, ["Hazirlayan", "Depo Sorumlusu", "Uretim Sorumlusu"])

    return tpl.finish(open_file=False)


def birlesik_pdf_olustur_ve_ac(is_emri_ids: list):
    """PDF olustur ve ac"""
    path = birlesik_pdf_olustur(is_emri_ids)
    subprocess.Popen(['start', '', path], shell=True)
    return path
