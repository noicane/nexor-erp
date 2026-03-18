# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Zimmet Teslim Formu PDF
Personelin tum aktif zimmetlerini listeleyen form
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
ORANGE = HexColor('#F59E0B')

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def _format_tarih(val):
    if val is None:
        return "-"
    if isinstance(val, datetime):
        return val.strftime("%d.%m.%Y")
    if isinstance(val, date):
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


def zimmet_formu_pdf(personel_id: int):
    """
    Personelin tum aktif zimmetlerini iceren zimmet teslim formu PDF'i olustur.

    Args:
        personel_id: Personel ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Personel bilgileri
    cursor.execute("""
        SELECT p.sicil_no, p.ad, p.soyad, p.tc_kimlik_no,
               d.ad as departman, poz.ad as pozisyon
        FROM ik.personeller p
        LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
        LEFT JOIN ik.pozisyonlar poz ON p.pozisyon_id = poz.id
        WHERE p.id = ?
    """, (personel_id,))
    prow = cursor.fetchone()
    if not prow:
        conn.close()
        raise Exception("Personel bulunamadi")

    personel = {
        'sicil_no': prow[0] or '-',
        'ad': prow[1] or '',
        'soyad': prow[2] or '',
        'tc': prow[3] or '-',
        'departman': prow[4] or '-',
        'pozisyon': prow[5] or '-',
    }

    # Aktif zimmetler
    cursor.execute("""
        SELECT z.zimmet_no, zt.ad, zt.kategori, z.teslim_tarihi,
               z.miktar, z.beden, z.seri_no, z.sonraki_yenileme, z.aciklama
        FROM ik.zimmetler z
        JOIN ik.zimmet_turleri zt ON z.zimmet_turu_id = zt.id
        WHERE z.personel_id = ? AND z.durum = 'TESLIM'
        ORDER BY z.teslim_tarihi DESC
    """, (personel_id,))
    zimmetler = cursor.fetchall()
    conn.close()

    # PDF Olustur
    _register_dejavu_fonts()
    firma = get_firma_bilgileri()
    firma_adi = firma.get('name', '') or APP_COMPANY
    firma_logo = get_firma_logo_path()

    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dosya_adi = f"ZIMMET_FORM_{personel['ad']}_{personel['soyad']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = str(REPORT_OUTPUT_DIR / dosya_adi)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setTitle(f"Zimmet Formu - {personel['ad']} {personel['soyad']}")
    c.setAuthor(firma_adi)

    usable_w = PAGE_W - 2 * MARGIN
    y = PAGE_H - MARGIN

    # ══════════════════════════════
    # HEADER
    # ══════════════════════════════
    header_h = 28 * mm
    _draw_rounded_rect(c, MARGIN, y - header_h, usable_w, header_h, 3 * mm, fill_color=DARK_BG)

    # Logo
    logo_w = 0
    if firma_logo and os.path.exists(firma_logo):
        try:
            from reportlab.lib.utils import ImageReader
            logo_w = 20 * mm
            c.drawImage(ImageReader(firma_logo), MARGIN + 4 * mm, y - header_h + 6 * mm,
                        width=16 * mm, height=16 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            logo_w = 0

    # Firma adi (ust satir)
    text_x = MARGIN + 4 * mm + logo_w
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 12)
    c.drawString(text_x, y - 9 * mm, firma_adi)

    # Baslik + tarih (alt satir)
    c.setFont("NexorFont-Bold", 15)
    c.drawString(text_x, y - 18 * mm, "ZIMMET TESLIM FORMU")

    c.setFont("NexorFont", 9)
    c.setFillColor(GRAY_300)
    c.drawRightString(PAGE_W - MARGIN - 5 * mm, y - 18 * mm,
                      f"Basim: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    y -= header_h + 5 * mm

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
        c.setFont("NexorFont-Bold", 9)
        c.drawString(x + 32 * mm, yy + 2 * mm, str(value or "-"))
        return yy - 7 * mm

    y = draw_field(MARGIN, y, "Ad Soyad:", f"{personel['ad']} {personel['soyad']}")
    y = draw_field(MARGIN, y, "Sicil No:", personel['sicil_no'])
    draw_field(MARGIN + col_w, y + 7 * mm, "TC Kimlik:", personel['tc'])
    y = draw_field(MARGIN, y, "Departman:", personel['departman'])
    draw_field(MARGIN + col_w, y + 7 * mm, "Pozisyon:", personel['pozisyon'])

    y -= 5 * mm

    # ══════════════════════════════
    # ZIMMET LISTESI
    # ══════════════════════════════
    y = _draw_section_title(c, MARGIN, y, f"TESLIM EDILEN ZIMMETLER ({len(zimmetler)} adet)", usable_w)

    if zimmetler:
        # Tablo basliklari
        headers = ["#", "Zimmet No", "Zimmet Adi", "Kategori", "Teslim", "Mkt", "Beden", "Yenileme"]
        col_widths = [8 * mm, 28 * mm, 42 * mm, 22 * mm, 22 * mm, 12 * mm, 16 * mm, 22 * mm]

        row_h = 6.5 * mm
        x = MARGIN

        # Baslik satiri
        _draw_rounded_rect(c, MARGIN, y - 1 * mm, usable_w, row_h + 1 * mm, 1.5 * mm, fill_color=PRIMARY)
        c.setFillColor(WHITE)
        c.setFont("NexorFont-Bold", 7.5)
        for i, h in enumerate(headers):
            c.drawString(x + 1.5 * mm, y + 1 * mm, h)
            x += col_widths[i]

        y -= row_h + 2 * mm

        # Satirlar
        for idx, row in enumerate(zimmetler):
            # Arka plan (cift satirlar gri)
            if idx % 2 == 0:
                _draw_rounded_rect(c, MARGIN, y - 1 * mm, usable_w, row_h, 0, fill_color=GRAY_100)

            c.setFillColor(BLACK)
            c.setFont("NexorFont", 8)
            x = MARGIN
            values = [
                str(idx + 1),
                str(row[0] or ''),
                str(row[1] or ''),
                str(row[2] or ''),
                _format_tarih(row[3]),
                str(row[4] or 1),
                str(row[5] or '-'),
                _format_tarih(row[7]),
            ]
            for i, val in enumerate(values):
                # Uzun metni kes
                max_char = int(col_widths[i] / (1.8 * mm))
                display = val[:max_char] if len(val) > max_char else val
                c.drawString(x + 1.5 * mm, y + 1 * mm, display)
                x += col_widths[i]

            y -= row_h

            # Sayfa kontrolu
            if y < MARGIN + 60 * mm:
                # Imza alanlari icin yer birak veya yeni sayfa
                c.showPage()
                y = PAGE_H - MARGIN
                c.setFont("NexorFont", 8)
    else:
        c.setFillColor(GRAY_500)
        c.setFont("NexorFont", 10)
        c.drawString(MARGIN + 5 * mm, y + 1 * mm, "Bu personele ait aktif zimmet kaydi bulunmamaktadir.")
        y -= 10 * mm

    y -= 10 * mm

    # ══════════════════════════════
    # BEYAN
    # ══════════════════════════════
    y = _draw_section_title(c, MARGIN, y, "BEYAN", usable_w)

    beyan_text = (
        "Yukarda listelenen malzemeleri eksiksiz ve hasarsiz olarak teslim aldim. "
        "Kullanimim sirasinda olusacak hasar ve kayiplardan sorumluyum. "
        "Is akdimin sona ermesi halinde tum zimmetleri eksiksiz iade edecegimi taahhut ederim."
    )
    c.setFillColor(BLACK)
    c.setFont("NexorFont", 9)

    # Satir satirina yaz (basit word wrap)
    words = beyan_text.split()
    line = ""
    for w in words:
        test = f"{line} {w}".strip()
        if c.stringWidth(test, "NexorFont", 9) > usable_w - 10 * mm:
            c.drawString(MARGIN + 3 * mm, y + 1 * mm, line)
            y -= 5 * mm
            line = w
        else:
            line = test
    if line:
        c.drawString(MARGIN + 3 * mm, y + 1 * mm, line)
        y -= 5 * mm

    y -= 10 * mm

    # ══════════════════════════════
    # IMZA ALANLARI
    # ══════════════════════════════
    imza_w = usable_w / 2 - 5 * mm

    # Sol - Teslim Alan
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(MARGIN, y, "Teslim Alan (Personel)")

    c.setFillColor(BLACK)
    c.setFont("NexorFont-Bold", 10)
    c.drawString(MARGIN, y - 8 * mm, f"{personel['ad']} {personel['soyad']}")

    c.setStrokeColor(GRAY_300)
    c.line(MARGIN, y - 30 * mm, MARGIN + imza_w, y - 30 * mm)
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawCentredString(MARGIN + imza_w / 2, y - 34 * mm, "Imza / Tarih")

    # Sag - Teslim Eden
    rx = MARGIN + usable_w / 2 + 5 * mm
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(rx, y, "Teslim Eden (IK / Depo)")

    c.setStrokeColor(GRAY_300)
    c.line(rx, y - 30 * mm, rx + imza_w, y - 30 * mm)
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawCentredString(rx + imza_w / 2, y - 34 * mm, "Imza / Tarih")

    y -= 45 * mm

    # ══════════════════════════════
    # FOOTER
    # ══════════════════════════════
    c.setStrokeColor(GRAY_300)
    c.line(MARGIN, MARGIN + 8 * mm, PAGE_W - MARGIN, MARGIN + 8 * mm)
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 7)
    c.drawString(MARGIN, MARGIN + 3 * mm, f"{firma_adi} - Zimmet Teslim Formu")
    c.drawRightString(PAGE_W - MARGIN, MARGIN + 3 * mm,
                      f"Olusturma: {datetime.now().strftime('%d.%m.%Y %H:%M')} | NEXOR ERP")

    c.save()

    # PDF'i ac
    try:
        os.startfile(pdf_path)
    except Exception:
        pass

    return pdf_path
