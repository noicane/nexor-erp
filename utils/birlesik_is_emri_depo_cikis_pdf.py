# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Birleşik İş Emri + Depo Çıkış PDF
Birden fazla iş emri ve ilgili depo çıkış emirlerini tek kağıtta listeler.
"""
import os
import subprocess
import tempfile
from datetime import datetime, date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas

from core.database import get_db_connection
from core.firma_bilgileri import get_firma_bilgileri
from utils.etiket_yazdir import _register_dejavu_fonts

PRIMARY = HexColor('#DC2626')
GRAY_300 = HexColor('#D1D5DB')
GRAY_100 = HexColor('#F3F4F6')
GRAY_700 = HexColor('#374151')
PAGE_W, PAGE_H = A4
MARGIN = 15 * mm


def _fmt_tarih(val):
    if val is None:
        return "-"
    if isinstance(val, datetime):
        return val.strftime("%d.%m.%Y")
    if isinstance(val, date):
        return val.strftime("%d.%m.%Y")
    return str(val)[:10]


def _fmt_miktar(val):
    if val is None:
        return "0"
    try:
        return f"{int(float(val)):,}".replace(",", ".")
    except Exception:
        return str(val)


def birlesik_pdf_olustur(is_emri_ids: list) -> str:
    """
    Birden fazla iş emri + ilgili depo çıkış emirlerini tek PDF'te listeler.

    Args:
        is_emri_ids: İş emri ID listesi

    Returns:
        str: Oluşturulan PDF dosya yolu
    """
    if not is_emri_ids:
        raise ValueError("En az bir iş emri ID gerekli")

    _register_dejavu_fonts()

    conn = get_db_connection()
    cursor = conn.cursor()

    # İş emirlerini çek
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

    # İlgili depo çıkış emirlerini çek
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

    conn.close()

    # Depo çıkışlarını iş emrine göre grupla
    cikis_map = {}
    for row in depo_cikislar:
        ie_id = row[0]
        if ie_id not in cikis_map:
            cikis_map[ie_id] = []
        cikis_map[ie_id].append(row)

    # Firma bilgileri
    firma = get_firma_bilgileri() or {}
    firma_adi = firma.get('firma_adi', 'ATMO MANUFACTURING')

    # PDF oluştur
    output_path = os.path.join(
        tempfile.gettempdir(),
        f"birlesik_is_emri_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )
    c = canvas.Canvas(output_path, pagesize=A4)

    # Başlık
    y = PAGE_H - MARGIN
    c.setFont("DejaVuSans-Bold", 14)
    c.setFillColor(PRIMARY)
    c.drawString(MARGIN, y, firma_adi)
    c.setFont("DejaVuSans", 10)
    c.setFillColor(GRAY_700)
    c.drawRightString(PAGE_W - MARGIN, y, f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    y -= 8 * mm
    c.setFont("DejaVuSans-Bold", 12)
    c.setFillColor(black)
    c.drawString(MARGIN, y, f"Birlesik Is Emri + Depo Cikis Listesi ({len(is_emirleri)} adet)")

    y -= 3 * mm
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1.5)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)
    y -= 5 * mm

    # İş emirleri tablosu
    col_widths = [75, 55, 45, 100, 80, 50, 50, 45, 60]
    headers = ["Is Emri No", "Tarih", "Termin", "Musteri", "Urun", "Kaplama", "Miktar", "Durum", "Hat"]

    # Header
    c.setFillColor(GRAY_100)
    c.rect(MARGIN, y - 5 * mm, PAGE_W - 2 * MARGIN, 6 * mm, fill=1, stroke=0)
    c.setFillColor(GRAY_700)
    c.setFont("DejaVuSans-Bold", 7)
    x = MARGIN + 2
    for i, h in enumerate(headers):
        c.drawString(x, y - 3.5 * mm, h)
        x += col_widths[i]
    y -= 7 * mm

    c.setFont("DejaVuSans", 7)
    c.setFillColor(black)

    for ie in is_emirleri:
        if y < 40 * mm:
            c.showPage()
            y = PAGE_H - MARGIN

        x = MARGIN + 2
        vals = [
            str(ie[1] or ''),
            _fmt_tarih(ie[2]),
            _fmt_tarih(ie[3]),
            str(ie[4] or '')[:18],
            str(ie[5] or '')[:12],
            str(ie[7] or '')[:8],
            _fmt_miktar(ie[8]),
            str(ie[11] or '')[:10],
            str(ie[12] or '')[:10]
        ]
        for i, v in enumerate(vals):
            c.drawString(x, y, v)
            x += col_widths[i]

        # Satır altı çizgi
        y -= 1 * mm
        c.setStrokeColor(GRAY_300)
        c.setLineWidth(0.3)
        c.line(MARGIN, y, PAGE_W - MARGIN, y)
        y -= 4 * mm

        # İlgili depo çıkışları
        cikislar = cikis_map.get(ie[0], [])
        if cikislar:
            c.setFont("DejaVuSans", 6)
            c.setFillColor(GRAY_700)
            for dc in cikislar:
                if y < 30 * mm:
                    c.showPage()
                    y = PAGE_H - MARGIN
                c.drawString(MARGIN + 10, y,
                    f"  Depo Cikis: {dc[1] or ''} | {dc[2] or ''} - {str(dc[3] or '')[:20]} | "
                    f"Miktar: {_fmt_miktar(dc[4])} | {dc[6] or ''} -> {dc[7] or ''} | {dc[5] or ''}")
                y -= 3.5 * mm

            c.setFillColor(black)
            c.setFont("DejaVuSans", 7)
            y -= 2 * mm

    # İmza alanları
    if y > 50 * mm:
        y -= 15 * mm
    else:
        c.showPage()
        y = PAGE_H - MARGIN - 20 * mm

    c.setStrokeColor(GRAY_300)
    c.setFont("DejaVuSans", 8)
    c.setFillColor(GRAY_700)
    imza_y = y
    for i, label in enumerate(["Hazirlayan", "Depo Sorumlusu", "Uretim Sorumlusu"]):
        ix = MARGIN + i * 60 * mm
        c.line(ix, imza_y, ix + 50 * mm, imza_y)
        c.drawCentredString(ix + 25 * mm, imza_y - 4 * mm, label)

    # Footer
    c.setFont("DejaVuSans", 6)
    c.setFillColor(GRAY_700)
    c.drawCentredString(PAGE_W / 2, 10 * mm,
        f"REDLINE NEXOR ERP | {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    c.save()
    return output_path


def birlesik_pdf_olustur_ve_ac(is_emri_ids: list):
    """PDF oluştur ve aç"""
    path = birlesik_pdf_olustur(is_emri_ids)
    subprocess.Popen(['start', '', path], shell=True)
    return path
