# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Depo Çıkış Emri PDF Çıktısı
A4 form şeklinde PDF rapor oluşturma
"""
import os
import subprocess
import tempfile
from datetime import datetime, date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from core.database import get_db_connection
from config import APP_NAME, APP_COMPANY, REPORT_OUTPUT_DIR, get_logo_path
from core.firma_bilgileri import get_firma_bilgileri, get_firma_logo_path
from utils.etiket_yazdir import _register_dejavu_fonts

# Renkler
PRIMARY = HexColor('#DC2626')
PRIMARY_LIGHT = HexColor('#FEE2E2')
DARK_BG = HexColor('#1F2937')
GRAY_700 = HexColor('#374151')
GRAY_500 = HexColor('#6B7280')
GRAY_300 = HexColor('#D1D5DB')
GRAY_100 = HexColor('#F3F4F6')
WHITE = white
BLACK = black
GREEN = HexColor('#10B981')
GREEN_DARK = HexColor('#059669')
BLUE = HexColor('#3B82F6')
ORANGE = HexColor('#F59E0B')

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def _format_tarih(val):
    if val is None:
        return "-"
    if isinstance(val, datetime):
        return val.strftime("%d.%m.%Y %H:%M")
    if isinstance(val, date):
        return val.strftime("%d.%m.%Y")
    return str(val)[:10]


def _format_miktar(val):
    if val is None:
        return "0"
    try:
        v = float(val)
        if v == int(v):
            return f"{int(v):,}".replace(",", ".")
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)


def _durum_renk(durum: str):
    renkler = {
        'BEKLIYOR': ORANGE,
        'TAMAMLANDI': GREEN_DARK,
    }
    return renkler.get(durum, GRAY_500)


def _durum_metin(durum: str):
    metinler = {
        'BEKLIYOR': 'Bekliyor',
        'TAMAMLANDI': 'Tamamlandı',
    }
    return metinler.get(durum, durum)


def _draw_rounded_rect(c, x, y, w, h, r, fill_color=None, stroke_color=None):
    """Kosleleri yuvarlatiilmis dikdortgen ciz"""
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


def _draw_field(c, x, y, label, value, label_w=35*mm, value_w=55*mm, h=7*mm):
    """Tek bir form alani ciz"""
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(x, y + 2*mm, label)
    c.setFillColor(BLACK)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(x + label_w, y + 2*mm, str(value or "-"))
    return y - h


def _draw_section_title(c, x, y, title, width):
    """Bolum basligi ciz"""
    _draw_rounded_rect(c, x, y - 1*mm, width, 8*mm, 2*mm, fill_color=DARK_BG)
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(x + 4*mm, y + 1.5*mm, title)
    return y - 11*mm


def depo_cikis_pdf_olustur(emir_id: int):
    """
    Depo cikis emri PDF'i olustur ve ac.

    Args:
        emir_id: Depo cikis emri ID
    """
    # -- Veri cek --
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            dce.id, dce.emir_no, dce.lot_no, dce.stok_kodu, dce.stok_adi,
            dce.talep_miktar, dce.transfer_miktar, dce.durum,
            dce.talep_tarihi, dce.tamamlanma_tarihi, dce.olusturma_tarihi,
            kd.kod, kd.ad,
            hd.kod, hd.ad,
            ie.is_emri_no, ie.cari_unvani, ie.kaplama_tipi,
            ie.termin_tarihi, ie.birim
        FROM stok.depo_cikis_emirleri dce
        LEFT JOIN tanim.depolar kd ON dce.kaynak_depo_id = kd.id
        LEFT JOIN tanim.depolar hd ON dce.hedef_depo_id = hd.id
        LEFT JOIN siparis.is_emirleri ie ON dce.is_emri_id = ie.id
        WHERE dce.id = ?
    """, (emir_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise Exception(f"Depo cikis emri bulunamadi (ID: {emir_id})")

    dce = {
        'id': row[0],
        'emir_no': row[1] or '',
        'lot_no': row[2] or '',
        'stok_kodu': row[3] or '',
        'stok_adi': row[4] or '',
        'talep_miktar': row[5] or 0,
        'transfer_miktar': row[6] or 0,
        'durum': row[7] or 'BEKLIYOR',
        'talep_tarihi': row[8],
        'tamamlanma_tarihi': row[9],
        'olusturma_tarihi': row[10],
        'kaynak_depo_kod': row[11] or '',
        'kaynak_depo_ad': row[12] or '',
        'hedef_depo_kod': row[13] or '',
        'hedef_depo_ad': row[14] or '',
        'is_emri_no': row[15] or '',
        'cari_unvani': row[16] or '',
        'kaplama_tipi': row[17] or '',
        'termin_tarihi': row[18],
        'birim': row[19] or 'ADET',
    }

    # -- PDF Olustur --
    _register_dejavu_fonts()

    firma = get_firma_bilgileri()
    firma_adi = firma.get('name', '') or APP_COMPANY
    firma_logo = get_firma_logo_path()

    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dosya_adi = f"DEPO_CIKIS_{dce['emir_no'].replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = str(REPORT_OUTPUT_DIR / dosya_adi)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setTitle(f"Depo Cikis Emri - {dce['emir_no']}")
    c.setAuthor(firma_adi)

    usable_w = PAGE_W - 2 * MARGIN
    y = PAGE_H - MARGIN

    # ==============================
    # HEADER
    # ==============================
    header_h = 28 * mm
    _draw_rounded_rect(c, MARGIN, y - header_h, usable_w, header_h, 4*mm, fill_color=DARK_BG)

    # Logo
    try:
        if firma_logo and os.path.isfile(firma_logo):
            c.drawImage(firma_logo, MARGIN + 4*mm, y - header_h + 4*mm,
                        width=20*mm, height=20*mm, preserveAspectRatio=True, mask='auto')
            text_x = MARGIN + 28*mm
        else:
            logo_path = get_logo_path("small")
            if logo_path.exists():
                c.drawImage(str(logo_path), MARGIN + 4*mm, y - header_h + 4*mm,
                            width=20*mm, height=20*mm, preserveAspectRatio=True, mask='auto')
                text_x = MARGIN + 28*mm
            else:
                text_x = MARGIN + 6*mm
    except:
        text_x = MARGIN + 6*mm

    # Firma ve belge bilgisi
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 16)
    c.drawString(text_x, y - 10*mm, "DEPO CIKIS EMRI")
    c.setFont("NexorFont", 9)
    c.setFillColor(GRAY_300)
    c.drawString(text_x, y - 16*mm, firma_adi)
    c.drawString(text_x, y - 21*mm, f"Olusturma: {_format_tarih(dce['olusturma_tarihi'])}")

    # Sag taraf - Emir no ve durum
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 14)
    c.drawRightString(MARGIN + usable_w - 6*mm, y - 10*mm, dce['emir_no'])

    # Durum badge
    durum_text = _durum_metin(dce['durum'])
    durum_color = _durum_renk(dce['durum'])
    badge_w = max(len(durum_text) * 3*mm + 8*mm, 25*mm)
    badge_x = MARGIN + usable_w - 6*mm - badge_w
    badge_y = y - header_h + 4*mm
    _draw_rounded_rect(c, badge_x, badge_y, badge_w, 7*mm, 3*mm, fill_color=durum_color)
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 9)
    c.drawCentredString(badge_x + badge_w / 2, badge_y + 2*mm, durum_text)

    y -= header_h + 6*mm

    # ==============================
    # IS EMRI BILGILERI
    # ==============================
    y = _draw_section_title(c, MARGIN, y, "IS EMRI BILGILERI", usable_w)

    col_w = usable_w / 2 - 2*mm
    rx = MARGIN + col_w + 4*mm

    y = _draw_field(c, MARGIN + 2*mm, y, "Is Emri No:", dce['is_emri_no'], 30*mm, 55*mm)
    # Sag tarafta termin tarihi (ayni satir)
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(rx + 2*mm, y + 7*mm + 2*mm, "Termin Tarihi:")
    c.setFillColor(BLACK)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(rx + 2*mm + 32*mm, y + 7*mm + 2*mm, _format_tarih(dce['termin_tarihi']))

    y = _draw_field(c, MARGIN + 2*mm, y, "Musteri:", dce['cari_unvani'], 30*mm, 120*mm)

    y -= 4*mm

    # ==============================
    # URUN BILGILERI
    # ==============================
    y = _draw_section_title(c, MARGIN, y, "URUN BILGILERI", usable_w)

    y = _draw_field(c, MARGIN + 2*mm, y, "Stok Kodu:", dce['stok_kodu'], 28*mm, 55*mm)
    # Sag tarafta kaplama
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(rx + 2*mm, y + 7*mm + 2*mm, "Kaplama:")
    c.setFillColor(BLACK)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(rx + 2*mm + 28*mm, y + 7*mm + 2*mm, dce['kaplama_tipi'] or "-")

    y = _draw_field(c, MARGIN + 2*mm, y, "Urun Adi:", dce['stok_adi'], 28*mm, 120*mm)

    # Lot no
    y = _draw_field(c, MARGIN + 2*mm, y, "Lot No:", dce['lot_no'], 28*mm, 55*mm)

    y -= 4*mm

    # ==============================
    # TRANSFER BILGILERI
    # ==============================
    y = _draw_section_title(c, MARGIN, y, "TRANSFER BILGILERI", usable_w)

    # Kaynak ve hedef depo - oklu gosterim
    depo_box_w = usable_w * 0.38
    arrow_w = usable_w * 0.24
    depo_box_h = 22*mm

    # Kaynak depo kutusu
    kaynak_x = MARGIN
    _draw_rounded_rect(c, kaynak_x, y - depo_box_h, depo_box_w, depo_box_h, 3*mm,
                       fill_color=GRAY_100, stroke_color=GRAY_300)
    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.5)
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawCentredString(kaynak_x + depo_box_w / 2, y - 6*mm, "KAYNAK DEPO")
    c.setFillColor(BLACK)
    c.setFont("NexorFont-Bold", 11)
    kaynak_text = f"{dce['kaynak_depo_kod']}"
    c.drawCentredString(kaynak_x + depo_box_w / 2, y - 12*mm, kaynak_text)
    c.setFillColor(GRAY_700)
    c.setFont("NexorFont", 8)
    c.drawCentredString(kaynak_x + depo_box_w / 2, y - 17*mm, dce['kaynak_depo_ad'])

    # Ok
    arrow_x = kaynak_x + depo_box_w
    arrow_mid_y = y - depo_box_h / 2
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(2)
    c.line(arrow_x + 8*mm, arrow_mid_y, arrow_x + arrow_w - 8*mm, arrow_mid_y)
    # Ok ucu
    c.setFillColor(PRIMARY)
    arrow_tip_x = arrow_x + arrow_w - 8*mm
    p = c.beginPath()
    p.moveTo(arrow_tip_x, arrow_mid_y + 3*mm)
    p.lineTo(arrow_tip_x + 5*mm, arrow_mid_y)
    p.lineTo(arrow_tip_x, arrow_mid_y - 3*mm)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    # Ok ustune yazi
    c.setFillColor(PRIMARY)
    c.setFont("NexorFont-Bold", 8)
    c.drawCentredString(arrow_x + arrow_w / 2, arrow_mid_y + 5*mm, "TRANSFER")

    # Hedef depo kutusu
    hedef_x = kaynak_x + depo_box_w + arrow_w
    _draw_rounded_rect(c, hedef_x, y - depo_box_h, depo_box_w, depo_box_h, 3*mm,
                       fill_color=HexColor('#ECFDF5'), stroke_color=GREEN)
    c.setStrokeColor(GREEN)
    c.setLineWidth(0.5)
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawCentredString(hedef_x + depo_box_w / 2, y - 6*mm, "HEDEF DEPO")
    c.setFillColor(BLACK)
    c.setFont("NexorFont-Bold", 11)
    hedef_text = f"{dce['hedef_depo_kod']}"
    c.drawCentredString(hedef_x + depo_box_w / 2, y - 12*mm, hedef_text)
    c.setFillColor(GRAY_700)
    c.setFont("NexorFont", 8)
    c.drawCentredString(hedef_x + depo_box_w / 2, y - 17*mm, dce['hedef_depo_ad'])

    y -= depo_box_h + 6*mm

    # Miktar kutucuklari
    miktar_data = [
        ("Talep Miktar", dce['talep_miktar'], BLUE),
        ("Transfer Miktar", dce['transfer_miktar'], GREEN),
    ]

    box_w = usable_w / 2 - 2*mm
    box_h = 18*mm
    bx = MARGIN

    for label, val, color in miktar_data:
        _draw_rounded_rect(c, bx, y - box_h, box_w, box_h, 3*mm, fill_color=GRAY_100)
        _draw_rounded_rect(c, bx, y - 2*mm, box_w, 2*mm, 1*mm, fill_color=color)
        c.setFillColor(BLACK)
        c.setFont("NexorFont-Bold", 14)
        c.drawCentredString(bx + box_w / 2, y - 10*mm, _format_miktar(val))
        c.setFillColor(GRAY_500)
        c.setFont("NexorFont", 7)
        c.drawCentredString(bx + box_w / 2, y - 13*mm, dce['birim'])
        c.setFont("NexorFont", 8)
        c.drawCentredString(bx + box_w / 2, y - 17*mm, label)
        bx += box_w + 4*mm

    y -= box_h + 6*mm

    # ==============================
    # TARIH BILGILERI
    # ==============================
    y = _draw_section_title(c, MARGIN, y, "TARIH BILGILERI", usable_w)

    third_w = usable_w / 3 - 2*mm

    tarih_data = [
        ("Talep Tarihi", _format_tarih(dce['talep_tarihi'])),
        ("Tamamlanma Tarihi", _format_tarih(dce['tamamlanma_tarihi'])),
        ("Olusturma Tarihi", _format_tarih(dce['olusturma_tarihi'])),
    ]

    tx = MARGIN + 2*mm
    for label, val in tarih_data:
        c.setFillColor(GRAY_500)
        c.setFont("NexorFont", 8)
        c.drawString(tx, y + 2*mm, label + ":")
        c.setFillColor(BLACK)
        c.setFont("NexorFont-Bold", 9)
        c.drawString(tx, y - 4*mm, val)
        tx += third_w + 2*mm

    y -= 14*mm

    # ==============================
    # IMZA ALANI
    # ==============================
    y -= 6*mm
    sig_w = usable_w / 3 - 3*mm
    sig_labels = ["Hazirlayan", "Depo Sorumlusu", "Teslim Alan"]
    sx = MARGIN

    for lbl in sig_labels:
        c.setStrokeColor(GRAY_300)
        c.setLineWidth(0.5)
        c.line(sx, y, sx + sig_w, y)
        c.setFillColor(GRAY_500)
        c.setFont("NexorFont", 8)
        c.drawCentredString(sx + sig_w / 2, y - 5*mm, lbl)
        c.setFillColor(GRAY_300)
        c.setFont("NexorFont", 7)
        c.drawCentredString(sx + sig_w / 2, y - 10*mm, "Tarih: ...../...../........")
        sx += sig_w + 3*mm

    # ==============================
    # FOOTER
    # ==============================
    footer_y = MARGIN - 4*mm
    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.5)
    c.line(MARGIN, footer_y + 8*mm, MARGIN + usable_w, footer_y + 8*mm)

    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 7)
    c.drawString(MARGIN, footer_y + 3*mm, f"{APP_NAME} | {firma_adi}")
    c.drawCentredString(PAGE_W / 2, footer_y + 3*mm, f"Yazdirma: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    c.drawRightString(MARGIN + usable_w, footer_y + 3*mm, f"Depo Cikis: {dce['emir_no']}")

    # -- Kaydet ve ac --
    c.save()
    os.startfile(pdf_path)
    return pdf_path
