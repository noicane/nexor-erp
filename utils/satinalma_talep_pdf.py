# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Satinalma Talep Formu PDF
Onaylanan satinalma taleplerini imzalatilabilir form olarak cikarir.
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

PRIMARY = HexColor('#DC2626')
DARK_BG = HexColor('#1F2937')
GRAY_500 = HexColor('#6B7280')
GRAY_300 = HexColor('#D1D5DB')
GRAY_100 = HexColor('#F3F4F6')
WHITE = white
BLACK = black
GREEN = HexColor('#10B981')
BLUE = HexColor('#3B82F6')

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


def _fmt(val):
    if val is None:
        return "-"
    if isinstance(val, (datetime, date)):
        return val.strftime("%d.%m.%Y")
    return str(val)


def _fmt_para(val):
    if val is None or val == 0:
        return "-"
    return f"{val:,.2f} TL"


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


def _section(c, x, y, title, width):
    _draw_rounded_rect(c, x, y - 1 * mm, width, 8 * mm, 2 * mm, fill_color=DARK_BG)
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(x + 4 * mm, y + 1.5 * mm, title)
    return y - 11 * mm


def satinalma_talep_pdf(talep_id: int):
    """Satinalma talep formunu PDF olarak olusturur ve acar."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Talep bilgileri
    cursor.execute("""
        SELECT
            t.id, t.talep_no, t.tarih, t.oncelik, t.istenen_termin,
            t.talep_nedeni, t.notlar, t.durum, t.tahmini_tutar,
            t.amir_onay_durumu, t.amir_onay_tarihi,
            t.satinalma_onay_durumu, t.satinalma_onay_tarihi,
            t.olusturma_tarihi,
            p.ad + ' ' + p.soyad as talep_eden,
            p.sicil_no,
            d.ad as departman,
            amir.ad + ' ' + amir.soyad as amir_adi,
            sa.ad + ' ' + sa.soyad as satinalma_onaylayan
        FROM satinalma.talepler t
        JOIN ik.personeller p ON t.talep_eden_id = p.id
        LEFT JOIN ik.departmanlar d ON t.departman_id = d.id
        LEFT JOIN ik.personeller amir ON t.amir_id = amir.id
        LEFT JOIN ik.personeller sa ON t.satinalma_onaylayan_id = sa.id
        WHERE t.id = ?
    """, (talep_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise Exception("Talep bulunamadi")

    talep = {
        'id': row[0], 'talep_no': row[1], 'tarih': row[2],
        'oncelik': row[3] or '-', 'istenen_termin': row[4],
        'talep_nedeni': row[5] or '', 'notlar': row[6] or '',
        'durum': row[7] or '', 'tahmini_tutar': row[8],
        'amir_onay': row[9] or '', 'amir_onay_tarihi': row[10],
        'sa_onay': row[11] or '', 'sa_onay_tarihi': row[12],
        'olusturma': row[13],
        'talep_eden': row[14] or '-', 'sicil_no': row[15] or '-',
        'departman': row[16] or '-',
        'amir_adi': row[17] or '-', 'sa_onaylayan': row[18] or '-',
    }

    # Talep satirlari
    cursor.execute("""
        SELECT satir_no, urun_kodu, urun_adi, talep_miktar, birim,
               tahmini_birim_fiyat, tahmini_tutar, aciklama
        FROM satinalma.talep_satirlari
        WHERE talep_id = ?
        ORDER BY satir_no
    """, (talep_id,))
    satirlar = cursor.fetchall()
    conn.close()

    # PDF Olustur
    _register_dejavu_fonts()
    firma = get_firma_bilgileri()
    firma_adi = firma.get('name', '') or APP_COMPANY
    firma_logo = get_firma_logo_path()

    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dosya_adi = f"SATINALMA_TALEP_{talep['talep_no']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = str(REPORT_OUTPUT_DIR / dosya_adi)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setTitle(f"Satinalma Talep - {talep['talep_no']}")
    c.setAuthor(firma_adi)

    usable_w = PAGE_W - 2 * MARGIN
    y = PAGE_H - MARGIN

    # ══════════════ HEADER ══════════════
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

    tx = MARGIN + 4 * mm + logo_w
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 12)
    c.drawString(tx, y - 9 * mm, firma_adi)
    c.setFont("NexorFont-Bold", 15)
    c.drawString(tx, y - 18 * mm, "SATINALMA TALEP FORMU")

    c.setFont("NexorFont", 9)
    c.setFillColor(GRAY_300)
    c.drawRightString(PAGE_W - MARGIN - 5 * mm, y - 9 * mm, f"Talep No: {talep['talep_no']}")
    c.drawRightString(PAGE_W - MARGIN - 5 * mm, y - 18 * mm,
                      f"Basim: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    y -= header_h + 6 * mm

    # ══════════════ TALEP BILGILERI ══════════════
    y = _section(c, MARGIN, y, "TALEP BILGILERI", usable_w)
    col_w = usable_w / 3 - 2 * mm

    def field(x, yy, label, value):
        c.setFillColor(GRAY_500)
        c.setFont("NexorFont", 8)
        c.drawString(x, yy + 2 * mm, label)
        c.setFillColor(BLACK)
        c.setFont("NexorFont-Bold", 10)
        c.drawString(x, yy - 4 * mm, str(value))

    lx = MARGIN + 4 * mm
    field(lx, y, "Talep Eden", talep['talep_eden'])
    field(lx + col_w, y, "Sicil No", talep['sicil_no'])
    field(lx + col_w * 2, y, "Departman", talep['departman'])
    y -= 14 * mm

    field(lx, y, "Talep Tarihi", _fmt(talep['tarih']))
    field(lx + col_w, y, "Istenen Termin", _fmt(talep['istenen_termin']))
    field(lx + col_w * 2, y, "Oncelik", talep['oncelik'])
    y -= 14 * mm

    # Durum
    field(lx, y, "Durum", talep['durum'])
    field(lx + col_w, y, "Tahmini Tutar", _fmt_para(talep['tahmini_tutar']))
    y -= 16 * mm

    # Talep nedeni
    if talep['talep_nedeni']:
        c.setFillColor(GRAY_500)
        c.setFont("NexorFont", 8)
        c.drawString(lx, y + 2 * mm, "Talep Nedeni")
        c.setFillColor(BLACK)
        c.setFont("NexorFont", 10)
        for line in talep['talep_nedeni'].split('\n')[:3]:
            y -= 5 * mm
            c.drawString(lx, y, line[:90])
        y -= 6 * mm

    # ══════════════ MALZEME LISTESI ══════════════
    y = _section(c, MARGIN, y, "TALEP EDILEN MALZEMELER", usable_w)

    # Tablo baslik
    cols = [
        (8 * mm, "No"),
        (25 * mm, "Urun Kodu"),
        (65 * mm, "Urun Adi"),
        (18 * mm, "Miktar"),
        (15 * mm, "Birim"),
        (22 * mm, "B.Fiyat"),
        (22 * mm, "Tutar"),
    ]

    _draw_rounded_rect(c, MARGIN, y - 1 * mm, usable_w, 7 * mm, 1 * mm, fill_color=GRAY_100)
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont-Bold", 8)
    cx = MARGIN + 2 * mm
    for w, title in cols:
        c.drawString(cx, y + 1 * mm, title)
        cx += w
    y -= 9 * mm

    # Satirlar
    c.setFont("NexorFont", 9)
    genel_toplam = 0
    for satir in satirlar:
        if y < MARGIN + 60 * mm:
            # Yeni sayfa
            c.showPage()
            y = PAGE_H - MARGIN
            y = _section(c, MARGIN, y, "MALZEME LISTESI (devam)", usable_w)

        cx = MARGIN + 2 * mm
        vals = [
            str(satir[0] or ''),
            str(satir[1] or '')[:15],
            str(satir[2] or '')[:40],
            str(satir[3] or ''),
            str(satir[4] or ''),
            _fmt_para(satir[5]).replace(' TL', '') if satir[5] else '-',
            _fmt_para(satir[6]).replace(' TL', '') if satir[6] else '-',
        ]
        c.setFillColor(BLACK)
        for i, (w, _) in enumerate(cols):
            c.drawString(cx, y, vals[i])
            cx += w

        if satir[6]:
            genel_toplam += float(satir[6])

        # Alt cizgi
        c.setStrokeColor(GRAY_100)
        c.setLineWidth(0.3)
        c.line(MARGIN, y - 2 * mm, PAGE_W - MARGIN, y - 2 * mm)
        y -= 7 * mm

    # Toplam satiri
    y -= 2 * mm
    c.setFont("NexorFont-Bold", 10)
    c.setFillColor(PRIMARY)
    c.drawRightString(PAGE_W - MARGIN - 5 * mm, y, f"GENEL TOPLAM: {_fmt_para(genel_toplam)}")
    y -= 12 * mm

    # ══════════════ ONAY BILGILERI ══════════════
    y = _section(c, MARGIN, y, "ONAY BILGILERI", usable_w)

    col2 = usable_w / 2 - 2 * mm
    field(lx, y, "Amir Onay Durumu", talep['amir_onay'] or "BEKLEMEDE")
    field(lx + col2, y, "Amir Onay Tarihi", _fmt(talep['amir_onay_tarihi']))
    y -= 14 * mm

    field(lx, y, "Onaylayan Amir", talep['amir_adi'])
    y -= 14 * mm

    field(lx, y, "Satinalma Onay Durumu", talep['sa_onay'] or "BEKLEMEDE")
    field(lx + col2, y, "Satinalma Onay Tarihi", _fmt(talep['sa_onay_tarihi']))
    y -= 14 * mm

    field(lx, y, "Satinalma Onaylayan", talep['sa_onaylayan'])
    y -= 18 * mm

    # ══════════════ IMZA ALANI ══════════════
    if y < MARGIN + 50 * mm:
        c.showPage()
        y = PAGE_H - MARGIN

    y = _section(c, MARGIN, y, "ONAY VE IMZA", usable_w)

    imza_w = usable_w / 4 - 3 * mm
    imza_h = 28 * mm
    imza_labels = ["Talep Eden", "Birim Amiri", "Satinalma", "Genel Mudur"]

    for i, label in enumerate(imza_labels):
        x = MARGIN + i * (imza_w + 3 * mm)
        c.setStrokeColor(GRAY_300)
        c.setLineWidth(0.5)
        c.rect(x, y - imza_h, imza_w, imza_h)

        c.setFillColor(GRAY_500)
        c.setFont("NexorFont-Bold", 8)
        c.drawCentredString(x + imza_w / 2, y + 2 * mm, label)

        # Imza cizgisi
        line_y = y - imza_h + 8 * mm
        c.line(x + 6 * mm, line_y, x + imza_w - 6 * mm, line_y)

        c.setFont("NexorFont", 6)
        c.drawCentredString(x + imza_w / 2, y - imza_h + 2 * mm, "Tarih: ...../...../........")

    # ══════════════ FOOTER ══════════════
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 7)
    c.drawString(MARGIN, MARGIN - 5 * mm,
                 f"Bu belge {firma_adi} Satinalma birimi tarafindan olusturulmustur.")
    c.drawRightString(PAGE_W - MARGIN, MARGIN - 5 * mm,
                      f"NEXOR ERP - {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    c.save()

    try:
        os.startfile(pdf_path)
    except Exception:
        pass

    return pdf_path
