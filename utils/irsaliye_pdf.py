# -*- coding: utf-8 -*-
"""
NEXOR ERP - Sevk Irsaliyesi PDF
PDFTemplate motoru uzerinden calisir.
"""
import os
from datetime import datetime

from reportlab.lib.units import mm

from core.database import get_db_connection
from utils.pdf_template import PDFTemplate, format_tarih


def _fetch_irsaliye(cursor, irsaliye_id: int):
    cursor.execute("""
        SELECT ci.id, ci.irsaliye_no, ci.tarih, ci.sevk_tarihi,
               ci.tasiyici_firma, ci.arac_plaka, ci.sofor_adi,
               ci.durum, ci.notlar, ci.zirve_evrakno,
               COALESCE(c.unvan, '') AS musteri_unvan,
               COALESCE(c.adres, '') AS musteri_adres,
               COALESCE(c.vergi_no, '') AS musteri_vkn,
               COALESCE(c.vergi_dairesi, '') AS musteri_vd,
               COALESCE(c.telefon, '') AS musteri_tel,
               COALESCE(c.cari_kodu, '') AS musteri_kodu
        FROM siparis.cikis_irsaliyeleri ci
        LEFT JOIN musteri.cariler c ON ci.cari_id = c.id
        WHERE ci.id = ?
    """, (irsaliye_id,))
    row = cursor.fetchone()
    if not row:
        raise Exception(f"Irsaliye bulunamadi: {irsaliye_id}")

    irs = {
        'id': row[0], 'irsaliye_no': row[1] or '',
        'tarih': row[2], 'sevk_tarihi': row[3] or row[2],
        'tasiyici': row[4] or '', 'plaka': row[5] or '', 'sofor': row[6] or '',
        'durum': row[7] or '', 'notlar': row[8] or '',
        'zirve_evrakno': row[9] or '',
        'musteri_unvan': row[10] or '', 'musteri_adres': row[11] or '',
        'musteri_vkn': row[12] or '', 'musteri_vd': row[13] or '',
        'musteri_tel': row[14] or '', 'musteri_kodu': row[15] or '',
    }

    cursor.execute("""
        SELECT
            cis.lot_no,
            COALESCE(ie.stok_kodu, u.urun_kodu, '') as stok_kodu,
            COALESCE(ie.stok_adi, u.urun_adi, '') as stok_adi,
            cis.miktar,
            COALESCE(b.kod, 'AD') as birim,
            COALESCE(u.musteri_parca_no, '') as musteri_parca_no
        FROM siparis.cikis_irsaliye_satirlar cis
        LEFT JOIN siparis.is_emirleri ie ON cis.is_emri_id = ie.id
        LEFT JOIN stok.urunler u ON cis.urun_id = u.id
        LEFT JOIN tanim.birimler b ON cis.birim_id = b.id
        WHERE cis.irsaliye_id = ?
        ORDER BY cis.satir_no
    """, (irsaliye_id,))

    satirlar = []
    for r in cursor.fetchall():
        satirlar.append({
            'lot_no': r[0] or '',
            'stok_kodu': r[1] or '',
            'stok_adi': r[2] or '',
            'miktar': float(r[3] or 0),
            'birim': r[4] or 'AD',
            'musteri_parca_no': r[5] or '',
        })

    return irs, satirlar


def generate_irsaliye_pdf(irsaliye_id: int, output_path: str = None) -> str:
    """
    Atlas Kataforez formatli sevk irsaliyesi PDF uret.

    Args:
        irsaliye_id: siparis.cikis_irsaliyeleri.id
        output_path: Cikti dosyasi. Verilmezse varsayilan raporlar klasorune yazilir.

    Returns:
        Olusturulan PDF dosyasinin tam yolu.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        irs, satirlar = _fetch_irsaliye(cursor, irsaliye_id)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    safe_no = ''.join(ch if ch.isalnum() or ch in '-_' else '_'
                      for ch in irs['irsaliye_no'])
    dosya_adi = f"Irsaliye_{safe_no}.pdf"

    tpl = PDFTemplate(
        title="SEVK IRSALIYESI",
        form_no=irs['irsaliye_no'],
        filename=dosya_adi,
    )
    c = tpl.canvas
    y = tpl.content_top

    # ── MUSTERI / ALICI ──
    y = tpl.section("ALICI / MUSTERI", y)
    y = tpl.field_row(y, "Musteri Unvani", irs['musteri_unvan'][:50],
                         "Musteri Kodu", irs['musteri_kodu'])
    if irs['musteri_adres']:
        y = tpl.field_row(y, "Adres", irs['musteri_adres'][:80])
    y = tpl.field_row(y, "VKN", irs['musteri_vkn'] or '-',
                         "Vergi Dairesi", irs['musteri_vd'] or '-')
    if irs['musteri_tel']:
        y = tpl.field_row(y, "Telefon", irs['musteri_tel'])
    y -= 2 * mm

    # ── SEVK BILGILERI ──
    y = tpl.section("SEVK BILGILERI", y)
    y = tpl.field_row(y, "Irsaliye No", irs['irsaliye_no'],
                         "Duzenleme Tarihi", format_tarih(irs['tarih']))
    y = tpl.field_row(y, "Sevk Tarihi", format_tarih(irs['sevk_tarihi']),
                         "Durum", irs['durum'] or '-')
    y = tpl.field_row(y, "Tasiyici", irs['tasiyici'] or '-',
                         "Arac Plaka", irs['plaka'] or '-')
    y = tpl.field_row(y, "Sofor", irs['sofor'] or '-',
                         "Zirve Evrak No", irs['zirve_evrakno'] or '-')
    y -= 2 * mm

    # ── IRSALIYE KALEMLERI ──
    y = tpl.section("IRSALIYE KALEMLERI", y)

    headers = ["Sira", "Stok Kodu", "Musteri Ref.", "Urun Adi", "Lot No", "Miktar", "Birim"]
    col_widths = [8 * mm, 24 * mm, 22 * mm, 66 * mm, 22 * mm, 20 * mm, 12 * mm]

    rows = []
    toplam_miktar = 0.0
    for i, s in enumerate(satirlar, 1):
        rows.append([
            str(i),
            s['stok_kodu'][:14],
            s['musteri_parca_no'][:13],
            s['stok_adi'][:42],
            s['lot_no'][:14],
            f"{s['miktar']:,.0f}",
            s['birim'][:6],
        ])
        toplam_miktar += s['miktar']

    y = tpl.table(y, headers, rows, col_widths)

    # Toplam satiri
    c.setFillColor(tpl.theme['section_bg'])
    c.setFont("NexorFont-Bold", 9)
    c.drawRightString(tpl.margin + tpl.usable_w - 36 * mm, y + 2 * mm,
                      f"TOPLAM ({len(satirlar)} kalem):")
    c.drawRightString(tpl.margin + tpl.usable_w - 14 * mm, y + 2 * mm,
                      f"{toplam_miktar:,.0f}")
    c.setFillColor(tpl.theme['muted'])
    c.setFont("NexorFont", 7)
    c.drawString(tpl.margin + tpl.usable_w - 12 * mm, y + 2 * mm, "AD")
    y -= 10 * mm

    # ── NOTLAR ──
    if irs['notlar']:
        y = tpl.section("NOTLAR", y)
        y = tpl.text_block(y, str(irs['notlar']), max_lines=3)

    # ── IMZA ALANI ──
    y -= 4 * mm
    tpl.signature_row(y, ["Teslim Eden", "Tasiyici", "Teslim Alan"])

    path = tpl.finish(open_file=False)

    # output_path verilmisse oraya kopyala
    if output_path:
        import shutil
        os.makedirs(os.path.dirname(os.path.abspath(output_path)) or '.', exist_ok=True)
        shutil.copy2(path, output_path)
        return output_path

    return path
