# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Izin Talep Formu PDF
Onaylanan izin taleplerini imzalatilabilir form olarak cikarir.
"""
import os
from datetime import datetime, date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas

from core.database import get_db_connection
from config import APP_COMPANY, REPORT_OUTPUT_DIR
from core.firma_bilgileri import get_firma_bilgileri, get_firma_logo_path
from utils.etiket_yazdir import _register_dejavu_fonts

# Renkler
PRIMARY = HexColor('#DC2626')
DARK_BG = HexColor('#1F2937')
GRAY_500 = HexColor('#6B7280')
GRAY_300 = HexColor('#D1D5DB')
GRAY_100 = HexColor('#F3F4F6')
WHITE = white
BLACK = black
GREEN = HexColor('#10B981')

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def _format_tarih(val):
    if val is None:
        return "-"
    if isinstance(val, (datetime, date)):
        return val.strftime("%d.%m.%Y")
    return str(val)[:10]


def _draw_rounded_rect(c, x, y, w, h, r, fill_color=None, stroke_color=None):
    p = c.beginPath()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.arcTo(x + w - r, y, x + w, y + r, 0)
    p.lineTo(x + w, y + h - r)
    p.arcTo(x + w, y + h - r, x + w - r, y + h, 0)
    p.lineTo(x + r, y + h)
    p.arcTo(x + r, y + h, x, y + h - r, 0)
    p.lineTo(x, y + r)
    p.arcTo(x, y + r, x + r, y, 0)
    p.close()
    if fill_color:
        c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.drawPath(p, fill=1 if fill_color else 0, stroke=1)
    elif fill_color:
        c.drawPath(p, fill=1, stroke=0)


def _draw_section_title(c, x, y, title, width):
    _draw_rounded_rect(c, x, y - 1 * mm, width, 8 * mm, 2 * mm, fill_color=DARK_BG)
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(x + 4 * mm, y + 1.5 * mm, title)
    return y - 11 * mm


def izin_formu_pdf(talep_id: int):
    """
    Izin talep formunu PDF olarak olusturur ve acar.

    Args:
        talep_id: ik.izin_talepleri tablosundaki ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Izin talep bilgileri
    cursor.execute("""
        SELECT
            t.id, t.baslangic_tarihi, t.bitis_tarihi, t.gun_sayisi,
            t.aciklama, t.durum, t.onay_tarihi, t.olusturma_tarihi,
            p.sicil_no, p.ad, p.soyad, p.tc_kimlik_no,
            d.ad as departman, poz.ad as pozisyon,
            it.ad as izin_turu
        FROM ik.izin_talepleri t
        JOIN ik.personeller p ON t.personel_id = p.id
        LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
        LEFT JOIN ik.pozisyonlar poz ON p.pozisyon_id = poz.id
        LEFT JOIN ik.izin_turleri it ON t.izin_turu_id = it.id
        WHERE t.id = ?
    """, (talep_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise Exception("Izin talebi bulunamadi")

    talep = {
        'id': row[0],
        'baslangic': row[1],
        'bitis': row[2],
        'gun_sayisi': row[3] or 0,
        'aciklama': row[4] or '',
        'durum': row[5] or '',
        'onay_tarihi': row[6],
        'talep_tarihi': row[7],
        'sicil_no': row[8] or '-',
        'ad': row[9] or '',
        'soyad': row[10] or '',
        'tc': row[11] or '-',
        'departman': row[12] or '-',
        'pozisyon': row[13] or '-',
        'izin_turu': row[14] or '-',
    }

    # PDF Olustur
    _register_dejavu_fonts()
    firma = get_firma_bilgileri()
    firma_adi = firma.get('name', '') or APP_COMPANY
    firma_logo = get_firma_logo_path()

    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dosya_adi = f"IZIN_FORM_{talep['ad']}_{talep['soyad']}_{talep_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = str(REPORT_OUTPUT_DIR / dosya_adi)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setTitle(f"Izin Formu - {talep['ad']} {talep['soyad']}")
    c.setAuthor(firma_adi)

    usable_w = PAGE_W - 2 * MARGIN
    y = PAGE_H - MARGIN

    # ══════════════════════════════
    # HEADER
    # ══════════════════════════════
    header_h = 28 * mm
    _draw_rounded_rect(c, MARGIN, y - header_h, usable_w, header_h, 3 * mm, fill_color=DARK_BG)

    logo_w = 0
    if firma_logo and os.path.exists(firma_logo):
        try:
            from reportlab.lib.utils import ImageReader
            logo_w = 20 * mm
            c.drawImage(ImageReader(firma_logo), MARGIN + 4 * mm, y - header_h + 6 * mm,
                        width=16 * mm, height=16 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            logo_w = 0

    text_x = MARGIN + 4 * mm + logo_w
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 12)
    c.drawString(text_x, y - 9 * mm, firma_adi)

    c.setFont("NexorFont-Bold", 15)
    c.drawString(text_x, y - 18 * mm, "IZIN TALEP FORMU")

    # Sag ust: Form no + tarih
    c.setFont("NexorFont", 9)
    c.setFillColor(GRAY_300)
    c.drawRightString(PAGE_W - MARGIN - 5 * mm, y - 9 * mm,
                      f"Form No: IZN-{talep_id:05d}")
    c.drawRightString(PAGE_W - MARGIN - 5 * mm, y - 18 * mm,
                      f"Basim: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    y -= header_h + 6 * mm

    # ══════════════════════════════
    # PERSONEL BILGILERI
    # ══════════════════════════════
    y = _draw_section_title(c, MARGIN, y, "PERSONEL BILGILERI", usable_w)

    col_w = usable_w / 2 - 2 * mm

    def draw_field(x, yy, label, value):
        c.setFillColor(GRAY_500)
        c.setFont("NexorFont", 8)
        c.drawString(x, yy + 2 * mm, label)
        c.setFillColor(BLACK)
        c.setFont("NexorFont-Bold", 10)
        c.drawString(x, yy - 4 * mm, str(value))

    draw_field(MARGIN + 4 * mm, y, "Ad Soyad", f"{talep['ad']} {talep['soyad']}")
    draw_field(MARGIN + col_w + 4 * mm, y, "Sicil No", talep['sicil_no'])
    y -= 14 * mm

    draw_field(MARGIN + 4 * mm, y, "Departman", talep['departman'])
    draw_field(MARGIN + col_w + 4 * mm, y, "Pozisyon", talep['pozisyon'])
    y -= 14 * mm

    draw_field(MARGIN + 4 * mm, y, "TC Kimlik No", talep['tc'])
    y -= 16 * mm

    # ══════════════════════════════
    # IZIN BILGILERI
    # ══════════════════════════════
    y = _draw_section_title(c, MARGIN, y, "IZIN BILGILERI", usable_w)

    draw_field(MARGIN + 4 * mm, y, "Izin Turu", talep['izin_turu'])
    draw_field(MARGIN + col_w + 4 * mm, y, "Talep Tarihi", _format_tarih(talep['talep_tarihi']))
    y -= 14 * mm

    draw_field(MARGIN + 4 * mm, y, "Baslangic Tarihi", _format_tarih(talep['baslangic']))
    draw_field(MARGIN + col_w + 4 * mm, y, "Bitis Tarihi", _format_tarih(talep['bitis']))
    y -= 14 * mm

    # Gun sayisi buyuk yaz
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(MARGIN + 4 * mm, y + 2 * mm, "Toplam Gun Sayisi")
    c.setFillColor(PRIMARY)
    c.setFont("NexorFont-Bold", 16)
    c.drawString(MARGIN + 4 * mm, y - 6 * mm, f"{talep['gun_sayisi']} Gun")

    # Durum
    durum = talep['durum']
    durum_renk = GREEN if durum == 'ONAYLANDI' else PRIMARY
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(MARGIN + col_w + 4 * mm, y + 2 * mm, "Durum")
    c.setFillColor(durum_renk)
    c.setFont("NexorFont-Bold", 14)
    c.drawString(MARGIN + col_w + 4 * mm, y - 6 * mm, durum)
    y -= 18 * mm

    # Onay tarihi
    if talep['onay_tarihi']:
        draw_field(MARGIN + 4 * mm, y, "Onay Tarihi", _format_tarih(talep['onay_tarihi']))
        y -= 14 * mm

    y -= 4 * mm

    # ══════════════════════════════
    # ACIKLAMA
    # ══════════════════════════════
    if talep['aciklama']:
        y = _draw_section_title(c, MARGIN, y, "ACIKLAMA", usable_w)
        c.setFillColor(BLACK)
        c.setFont("NexorFont", 10)
        # Cok satirli aciklama
        lines = talep['aciklama'].split('\n')
        for line in lines[:5]:
            c.drawString(MARGIN + 4 * mm, y, line[:80])
            y -= 5 * mm
        y -= 6 * mm

    # ══════════════════════════════
    # IMZA ALANI
    # ══════════════════════════════
    y -= 10 * mm
    y = _draw_section_title(c, MARGIN, y, "ONAY VE IMZA", usable_w)

    imza_w = usable_w / 3 - 4 * mm
    imza_h = 30 * mm
    imza_labels = ["Personel", "Birim Yoneticisi", "Insan Kaynaklari"]

    for i, label in enumerate(imza_labels):
        x = MARGIN + i * (imza_w + 4 * mm)

        # Imza kutusu
        c.setStrokeColor(GRAY_300)
        c.setLineWidth(0.5)
        c.rect(x, y - imza_h, imza_w, imza_h)

        # Baslik
        c.setFillColor(GRAY_500)
        c.setFont("NexorFont-Bold", 9)
        c.drawCentredString(x + imza_w / 2, y + 2 * mm, label)

        # Alt cizgi (imza yeri)
        line_y = y - imza_h + 8 * mm
        c.setStrokeColor(GRAY_300)
        c.line(x + 8 * mm, line_y, x + imza_w - 8 * mm, line_y)

        # Tarih yeri
        c.setFillColor(GRAY_500)
        c.setFont("NexorFont", 7)
        c.drawCentredString(x + imza_w / 2, y - imza_h + 2 * mm, "Tarih: ...../...../........")

    y -= imza_h + 15 * mm

    # ══════════════════════════════
    # ALT BILGI
    # ══════════════════════════════
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 7)
    c.drawString(MARGIN, MARGIN - 5 * mm,
                 f"Bu belge {firma_adi} Insan Kaynaklari birimi tarafindan olusturulmustur.")
    c.drawRightString(PAGE_W - MARGIN, MARGIN - 5 * mm,
                      f"NEXOR ERP - {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    c.save()

    # PDF'i ac
    try:
        os.startfile(pdf_path)
    except Exception:
        pass

    return pdf_path
