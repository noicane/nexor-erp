# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İş Emri PDF Çıktısı
Derli toplu form şeklinde A4 PDF rapor oluşturma
"""
import os
import subprocess
import tempfile
from datetime import datetime, date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white, Color
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
    except Exception:
        return str(val)


def _durum_renk(durum: str):
    renkler = {
        'BEKLIYOR': ORANGE,
        'PLANLI': BLUE,
        'URETIMDE': GREEN,
        'TAMAMLANDI': HexColor('#059669'),
        'KALITE_BEKLIYOR': HexColor('#8B5CF6'),
        'IPTAL': HexColor('#EF4444'),
    }
    return renkler.get(durum, GRAY_500)


def _durum_metin(durum: str):
    metinler = {
        'BEKLIYOR': 'Bekliyor',
        'PLANLI': 'Planlandı',
        'URETIMDE': 'Üretimde',
        'TAMAMLANDI': 'Tamamlandı',
        'KALITE_BEKLIYOR': 'Kalite Bekliyor',
        'IPTAL': 'İptal',
    }
    return metinler.get(durum, durum)


def _draw_rounded_rect(c, x, y, w, h, r, fill_color=None, stroke_color=None):
    """Köşeleri yuvarlatılmış dikdörtgen çiz"""
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
    """Tek bir form alanı çiz"""
    # Label
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(x, y + 2*mm, label)
    # Value
    c.setFillColor(BLACK)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(x + label_w, y + 2*mm, str(value or "-"))
    return y - h


def _draw_section_title(c, x, y, title, width):
    """Bölüm başlığı çiz"""
    _draw_rounded_rect(c, x, y - 1*mm, width, 8*mm, 2*mm, fill_color=DARK_BG)
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(x + 4*mm, y + 1.5*mm, title)
    return y - 11*mm


def is_emri_pdf_olustur(is_emri_id: int):
    """
    İş emri detay PDF'i oluştur ve aç.

    Args:
        is_emri_id: İş emri ID
    """
    # ── Veri çek ──
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ie.id, ie.is_emri_no, ie.tarih, ie.termin_tarihi, ie.durum, ie.oncelik,
            ie.cari_unvani,
            ie.stok_kodu, ie.stok_adi, ie.kaplama_tipi,
            ISNULL(ie.toplam_miktar, ie.planlanan_miktar),
            ISNULL(ie.uretilen_miktar, 0),
            ISNULL(ie.fire_miktar, 0),
            ie.birim,
            ISNULL(ie.toplam_bara, 0),
            ISNULL(ie.tahmini_sure_dk, 0),
            ie.uretim_notu,
            ie.olusturma_tarihi,
            h.ad,
            ie.lot_no
        FROM siparis.is_emirleri ie
        LEFT JOIN tanim.uretim_hatlari h ON ie.hat_id = h.id
        WHERE ie.id = ? AND ie.silindi_mi = 0
    """, (is_emri_id,))

    row = cursor.fetchone()
    if not row:
        conn.close()
        raise Exception(f"İş emri bulunamadı (ID: {is_emri_id})")

    ie = {
        'id': row[0],
        'is_emri_no': row[1],
        'tarih': row[2],
        'termin_tarihi': row[3],
        'durum': row[4] or 'BEKLIYOR',
        'oncelik': row[5] or 5,
        'cari_unvani': row[6] or '',
        'stok_kodu': row[7] or '',
        'stok_adi': row[8] or '',
        'kaplama_tipi': row[9] or '',
        'planlanan_miktar': row[10] or 0,
        'uretilen_miktar': row[11] or 0,
        'fire_miktar': row[12] or 0,
        'birim': row[13] or '',
        'toplam_bara': row[14] or 0,
        'tahmini_sure_dk': row[15] or 0,
        'uretim_notu': row[16] or '',
        'olusturma_tarihi': row[17],
        'hat_adi': row[18] or '-',
        'lot_no': row[19] or '',
    }

    # is_emri_lotlar tablosundan da lotları kontrol et (birden fazla lot olabilir)
    try:
        cursor.execute("""
            SELECT lot_no FROM siparis.is_emri_lotlar
            WHERE is_emri_id = ?
        """, (is_emri_id,))
        lotlar = [str(r[0]) for r in cursor.fetchall() if r[0]]
        if lotlar:
            ie['lot_no'] = ', '.join(lotlar)
    except Exception:
        pass

    kalan = float(ie['planlanan_miktar']) - float(ie['uretilen_miktar']) - float(ie['fire_miktar'])

    # Operasyonlar
    operasyonlar = []
    try:
        cursor.execute("""
            SELECT sira_no, operasyon_adi, planlanan_sure_dk, fiili_sure_dk, durum
            FROM siparis.is_emri_operasyonlar
            WHERE is_emri_id = ? AND silindi_mi = 0
            ORDER BY sira_no
        """, (is_emri_id,))
        for orow in cursor.fetchall():
            operasyonlar.append({
                'sira': orow[0],
                'adi': orow[1] or '',
                'plan_dk': orow[2] or 0,
                'fiili_dk': orow[3] or 0,
                'durum': orow[4] or 'BEKLIYOR',
            })
    except Exception:
        pass

    conn.close()

    # ── PDF Oluştur ──
    _register_dejavu_fonts()

    firma = get_firma_bilgileri()
    firma_adi = firma.get('name', '') or APP_COMPANY
    firma_logo = get_firma_logo_path()

    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dosya_adi = f"IS_EMRI_{ie['is_emri_no'].replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = str(REPORT_OUTPUT_DIR / dosya_adi)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setTitle(f"İş Emri - {ie['is_emri_no']}")
    c.setAuthor(firma_adi)

    usable_w = PAGE_W - 2 * MARGIN
    y = PAGE_H - MARGIN

    # ════════════════════════════════════════════
    # HEADER
    # ════════════════════════════════════════════
    header_h = 28 * mm
    _draw_rounded_rect(c, MARGIN, y - header_h, usable_w, header_h, 4*mm, fill_color=DARK_BG)

    # Logo - firma logosu varsa onu kullan, yoksa APP logosu
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
    except Exception:
        text_x = MARGIN + 6*mm

    # Firma ve belge bilgisi
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 16)
    c.drawString(text_x, y - 10*mm, "İŞ EMRİ")
    c.setFont("NexorFont", 9)
    c.setFillColor(GRAY_300)
    c.drawString(text_x, y - 16*mm, firma_adi)
    c.drawString(text_x, y - 21*mm, f"Oluşturma: {_format_tarih(ie['olusturma_tarihi'])}")

    # Sağ taraf - İş emri no ve durum
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 14)
    no_text = ie['is_emri_no']
    c.drawRightString(MARGIN + usable_w - 6*mm, y - 10*mm, no_text)

    # Durum badge
    durum_text = _durum_metin(ie['durum'])
    durum_color = _durum_renk(ie['durum'])
    badge_w = max(len(durum_text) * 3*mm + 8*mm, 25*mm)
    badge_x = MARGIN + usable_w - 6*mm - badge_w
    badge_y = y - header_h + 4*mm
    _draw_rounded_rect(c, badge_x, badge_y, badge_w, 7*mm, 3*mm, fill_color=durum_color)
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 9)
    c.drawCentredString(badge_x + badge_w / 2, badge_y + 2*mm, durum_text)

    y -= header_h + 6*mm

    # ════════════════════════════════════════════
    # MÜŞTERİ VE TARİH BİLGİLERİ
    # ════════════════════════════════════════════
    col_w = usable_w / 2 - 2*mm

    # Sol kolon - Müşteri
    y = _draw_section_title(c, MARGIN, y, "MÜŞTERİ BİLGİLERİ", col_w)
    y_left = y
    y_left = _draw_field(c, MARGIN + 2*mm, y_left, "Müşteri:", ie['cari_unvani'], 28*mm, 60*mm)

    # Sağ kolon - Tarihler
    rx = MARGIN + col_w + 4*mm
    _draw_section_title(c, rx, y + 11*mm, "TARİH BİLGİLERİ", col_w)
    y_right = y
    y_right = _draw_field(c, rx + 2*mm, y_right, "Tarih:", _format_tarih(ie['tarih']), 28*mm, 60*mm)
    y_right = _draw_field(c, rx + 2*mm, y_right, "Termin:", _format_tarih(ie['termin_tarihi']), 28*mm, 60*mm)

    # Termin uyarısı
    if ie['termin_tarihi'] and ie['durum'] not in ('TAMAMLANDI', 'IPTAL'):
        termin = ie['termin_tarihi']
        if hasattr(termin, 'date'):
            termin = termin.date()
        if termin < date.today():
            c.setFillColor(PRIMARY)
            c.setFont("NexorFont-Bold", 8)
            gecikme = (date.today() - termin).days
            c.drawString(rx + 2*mm, y_right + 2*mm, f"⚠ {gecikme} gün gecikmiş!")
            y_right -= 7*mm

    oncelik_metin = {1: "Çok Yüksek", 2: "Yüksek", 3: "Normal", 4: "Düşük", 5: "Çok Düşük"}
    y_right = _draw_field(c, rx + 2*mm, y_right, "Öncelik:", oncelik_metin.get(ie['oncelik'], str(ie['oncelik'])), 28*mm, 60*mm)

    y = min(y_left, y_right) - 4*mm

    # ════════════════════════════════════════════
    # ÜRÜN BİLGİLERİ
    # ════════════════════════════════════════════
    y = _draw_section_title(c, MARGIN, y, "ÜRÜN BİLGİLERİ", usable_w)

    # Ürün bilgileri iki sütun
    y = _draw_field(c, MARGIN + 2*mm, y, "Stok Kodu:", ie['stok_kodu'], 28*mm, 55*mm)

    # Sağ tarafta kaplama tipi (aynı satıra)
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(rx + 2*mm, y + 7*mm + 2*mm, "Kaplama:")
    c.setFillColor(BLACK)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(rx + 2*mm + 28*mm, y + 7*mm + 2*mm, ie['kaplama_tipi'] or "-")

    y = _draw_field(c, MARGIN + 2*mm, y, "Ürün Adı:", ie['stok_adi'], 28*mm, 120*mm)

    # Lot ve Hat aynı satır
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(MARGIN + 2*mm, y + 2*mm, "Lot No:")
    c.setFillColor(BLACK)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(MARGIN + 2*mm + 28*mm, y + 2*mm, ie['lot_no'] or "-")

    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(rx + 2*mm, y + 2*mm, "Üretim Hattı:")
    c.setFillColor(BLACK)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(rx + 2*mm + 28*mm, y + 2*mm, ie['hat_adi'])
    y -= 7*mm

    y -= 4*mm

    # ════════════════════════════════════════════
    # MİKTAR BİLGİLERİ (Tablo şeklinde)
    # ════════════════════════════════════════════
    y = _draw_section_title(c, MARGIN, y, "MİKTAR BİLGİLERİ", usable_w)

    miktar_data = [
        ("Planlanan", ie['planlanan_miktar'], BLUE),
        ("Üretilen", ie['uretilen_miktar'], GREEN),
        ("Fire", ie['fire_miktar'], PRIMARY),
        ("Kalan", kalan, ORANGE),
    ]

    box_w = usable_w / len(miktar_data) - 2*mm
    box_h = 18*mm
    bx = MARGIN

    for label, val, color in miktar_data:
        # Box arka plan
        _draw_rounded_rect(c, bx, y - box_h, box_w, box_h, 3*mm, fill_color=GRAY_100)
        # Üst renk çizgisi
        _draw_rounded_rect(c, bx, y - 2*mm, box_w, 2*mm, 1*mm, fill_color=color)
        # Değer
        c.setFillColor(BLACK)
        c.setFont("NexorFont-Bold", 13)
        c.drawCentredString(bx + box_w / 2, y - 10*mm, _format_miktar(val))
        # Birim
        c.setFillColor(GRAY_500)
        c.setFont("NexorFont", 7)
        c.drawCentredString(bx + box_w / 2, y - 13*mm, ie['birim'])
        # Label
        c.setFont("NexorFont", 8)
        c.drawCentredString(bx + box_w / 2, y - 17*mm, label)
        bx += box_w + 2*mm

    y -= box_h + 4*mm

    # Bara ve süre
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(MARGIN + 2*mm, y + 2*mm, f"Toplam Bara: ")
    c.setFillColor(BLACK)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(MARGIN + 2*mm + 28*mm, y + 2*mm, str(ie['toplam_bara']))

    if ie['tahmini_sure_dk'] > 0:
        saat = ie['tahmini_sure_dk'] // 60
        dk = ie['tahmini_sure_dk'] % 60
        sure_str = f"{saat} saat {dk} dk" if saat > 0 else f"{dk} dk"
        c.setFillColor(GRAY_500)
        c.setFont("NexorFont", 8)
        c.drawString(rx + 2*mm, y + 2*mm, "Tahmini Süre:")
        c.setFillColor(BLACK)
        c.setFont("NexorFont-Bold", 9)
        c.drawString(rx + 2*mm + 28*mm, y + 2*mm, sure_str)

    y -= 10*mm

    # ════════════════════════════════════════════
    # OPERASYONLAR TABLOSU
    # ════════════════════════════════════════════
    if operasyonlar:
        y = _draw_section_title(c, MARGIN, y, "ÜRETİM OPERASYONLARI", usable_w)

        # Tablo başlık
        cols = [10*mm, 65*mm, 28*mm, 28*mm, 35*mm]
        headers = ["#", "Operasyon", "Plan (dk)", "Fiili (dk)", "Durum"]
        hdr_y = y
        _draw_rounded_rect(c, MARGIN, hdr_y - 7*mm, usable_w, 7*mm, 1*mm, fill_color=GRAY_700)
        c.setFillColor(WHITE)
        c.setFont("NexorFont-Bold", 8)
        cx = MARGIN + 2*mm
        for i, hdr in enumerate(headers):
            c.drawString(cx, hdr_y - 5*mm, hdr)
            cx += cols[i]

        y = hdr_y - 7*mm
        for idx, op in enumerate(operasyonlar):
            row_bg = GRAY_100 if idx % 2 == 0 else WHITE
            c.setFillColor(row_bg)
            c.rect(MARGIN, y - 7*mm, usable_w, 7*mm, fill=1, stroke=0)

            c.setFillColor(BLACK)
            c.setFont("NexorFont", 8)
            cx = MARGIN + 2*mm
            vals = [
                str(op['sira']),
                op['adi'],
                str(op['plan_dk']),
                str(op['fiili_dk']),
                _durum_metin(op['durum']),
            ]
            for i, v in enumerate(vals):
                if i == 4:
                    c.setFillColor(_durum_renk(op['durum']))
                    c.setFont("NexorFont-Bold", 8)
                c.drawString(cx, y - 5*mm, v)
                cx += cols[i]
            y -= 7*mm

        y -= 4*mm

    # ════════════════════════════════════════════
    # ÖZEL TALİMATLAR
    # ════════════════════════════════════════════
    if ie['uretim_notu']:
        y = _draw_section_title(c, MARGIN, y, "ÖZEL TALİMATLAR", usable_w)
        _draw_rounded_rect(c, MARGIN, y - 25*mm, usable_w, 25*mm, 3*mm,
                           fill_color=PRIMARY_LIGHT, stroke_color=PRIMARY)
        c.setStrokeColor(PRIMARY)
        c.setLineWidth(0.5)
        c.setFillColor(BLACK)
        c.setFont("NexorFont", 9)
        # Metin sarmalama
        text = ie['uretim_notu']
        lines = []
        max_char = 90
        while text:
            if len(text) <= max_char:
                lines.append(text)
                break
            split_idx = text[:max_char].rfind(' ')
            if split_idx == -1:
                split_idx = max_char
            lines.append(text[:split_idx])
            text = text[split_idx:].strip()

        ty = y - 5*mm
        for line in lines[:5]:
            c.drawString(MARGIN + 4*mm, ty, line)
            ty -= 4*mm

        y -= 29*mm

    # ════════════════════════════════════════════
    # İMZA ALANI
    # ════════════════════════════════════════════
    y -= 6*mm
    sig_w = usable_w / 3 - 3*mm
    sig_labels = ["Hazırlayan", "Üretim Sorumlusu", "Kalite Kontrol"]
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

    # ════════════════════════════════════════════
    # FOOTER
    # ════════════════════════════════════════════
    footer_y = MARGIN - 4*mm
    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.5)
    c.line(MARGIN, footer_y + 8*mm, MARGIN + usable_w, footer_y + 8*mm)

    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 7)
    c.drawString(MARGIN, footer_y + 3*mm, f"{APP_NAME} | {firma_adi}")
    c.drawCentredString(PAGE_W / 2, footer_y + 3*mm, f"Yazdırma: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    c.drawRightString(MARGIN + usable_w, footer_y + 3*mm, f"İş Emri: {ie['is_emri_no']}")

    # ── Kaydet ve aç ──
    c.save()
    os.startfile(pdf_path)
    return pdf_path
