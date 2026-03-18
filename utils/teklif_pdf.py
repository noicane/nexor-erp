# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Teklif PDF Çıktısı
Kaplama sektörü teklif raporu oluşturma (A4)
"""
import os
import math
from datetime import datetime, date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas

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

DURUM_RENKLER = {
    'TASLAK': GRAY_500,
    'GONDERILDI': BLUE,
    'ONAYLANDI': GREEN,
    'REDDEDILDI': PRIMARY,
    'IPTAL': GRAY_500,
    'IS_EMRINE_DONUSTURULDU': HexColor('#8B5CF6'),
}

DURUM_METINLER = {
    'TASLAK': 'Taslak',
    'GONDERILDI': 'Gönderildi',
    'ONAYLANDI': 'Onaylandı',
    'REDDEDILDI': 'Reddedildi',
    'IPTAL': 'İptal',
    'IS_EMRINE_DONUSTURULDU': 'İş Emrine Dönüştürüldü',
}


def _format_tarih(val):
    if val is None:
        return "-"
    if isinstance(val, datetime):
        return val.strftime("%d.%m.%Y")
    if isinstance(val, date):
        return val.strftime("%d.%m.%Y")
    return str(val)[:10]


def _format_para(val, simge='₺'):
    if val is None:
        return f"{simge}0,00"
    try:
        v = float(val)
        return f"{simge}{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(val)


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


def _draw_field(c, x, y, label, value, label_w=30*mm, h=7*mm, max_w=None):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 8)
    c.drawString(x, y + 2*mm, label)
    c.setFillColor(BLACK)
    font_name = "NexorFont-Bold"
    font_size = 9
    c.setFont(font_name, font_size)
    val_str = str(value or "-")
    if max_w and stringWidth(val_str, font_name, font_size) > max_w:
        # Önce küçük font dene
        font_size = 8
        c.setFont(font_name, font_size)
        if stringWidth(val_str, font_name, font_size) > max_w:
            # Hala sığmıyorsa alt satıra in
            line_h = 4 * mm
            lines = _wrap_field_text(val_str, font_name, font_size, max_w)
            for i, line in enumerate(lines):
                c.drawString(x + label_w, y + 2*mm - i * line_h, line)
            extra_h = max(0, (len(lines) - 1)) * line_h
            return y - h - extra_h
    c.drawString(x + label_w, y + 2*mm, val_str)
    return y - h


def _wrap_field_text(text, font_name, font_size, max_w):
    """Metni satırlara böl (kelime bazlı)"""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip() if current else word
        if stringWidth(test, font_name, font_size) <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            # Tek kelime bile sığmıyorsa zorla kır
            if stringWidth(word, font_name, font_size) > max_w:
                while word:
                    part = word
                    while len(part) > 1 and stringWidth(part, font_name, font_size) > max_w:
                        part = part[:-1]
                    lines.append(part)
                    word = word[len(part):]
                current = ""
            else:
                current = word
    if current:
        lines.append(current)
    return lines if lines else [text]


def _draw_section_title(c, x, y, title, width):
    _draw_rounded_rect(c, x, y - 1*mm, width, 8*mm, 2*mm, fill_color=DARK_BG)
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 9)
    c.drawString(x + 4*mm, y + 1.5*mm, title)
    return y - 11*mm


def _new_page(c, firma_adi, teklif_no, page_num):
    """Yeni sayfa oluştur ve footer çiz"""
    c.showPage()
    # Footer
    _draw_footer(c, firma_adi, teklif_no, page_num)
    return PAGE_H - MARGIN


def _draw_footer(c, firma_adi, teklif_no, page_num):
    footer_y = MARGIN - 4*mm
    usable_w = PAGE_W - 2 * MARGIN
    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.5)
    c.line(MARGIN, footer_y + 8*mm, MARGIN + usable_w, footer_y + 8*mm)
    c.setFillColor(GRAY_500)
    c.setFont("NexorFont", 7)
    c.drawString(MARGIN, footer_y + 3*mm, f"{APP_NAME} | {firma_adi}")
    c.drawCentredString(PAGE_W / 2, footer_y + 3*mm, f"Sayfa {page_num}")
    c.drawRightString(MARGIN + usable_w, footer_y + 3*mm, f"Teklif: {teklif_no}")


def teklif_pdf_olustur(teklif_id: int):
    """Teklif PDF'i oluştur ve aç."""

    # ── Veri çek ──
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.id, t.teklif_no, t.revizyon_no, t.tarih, t.gecerlilik_tarihi,
               t.cari_unvani, t.cari_yetkili, t.cari_telefon, t.cari_email,
               t.ara_toplam, t.iskonto_oran, t.iskonto_tutar,
               t.kdv_oran, t.kdv_tutar, t.genel_toplam, t.para_birimi,
               t.durum, t.referans_no, t.proje_adi, t.teslim_suresi,
               t.odeme_kosullari, t.notlar, t.ozel_kosullar,
               t.olusturma_tarihi
        FROM satislar.teklifler t
        WHERE t.id = ? AND t.silindi_mi = 0
    """, (teklif_id,))

    row = cursor.fetchone()
    if not row:
        conn.close()
        raise Exception(f"Teklif bulunamadı (ID: {teklif_id})")

    tek = {
        'id': row[0], 'teklif_no': row[1] or '', 'revizyon_no': row[2] or 0,
        'tarih': row[3], 'gecerlilik': row[4],
        'cari_unvani': row[5] or '', 'cari_yetkili': row[6] or '',
        'cari_telefon': row[7] or '', 'cari_email': row[8] or '',
        'ara_toplam': float(row[9] or 0), 'iskonto_oran': float(row[10] or 0),
        'iskonto_tutar': float(row[11] or 0), 'kdv_oran': float(row[12] or 20),
        'kdv_tutar': float(row[13] or 0), 'genel_toplam': float(row[14] or 0),
        'para_birimi': row[15] or 'TRY', 'durum': row[16] or 'TASLAK',
        'referans_no': row[17] or '', 'proje_adi': row[18] or '',
        'teslim_suresi': row[19] or '', 'odeme_kosullari': row[20] or '',
        'notlar': row[21] or '', 'ozel_kosullar': row[22] or '',
        'olusturma_tarihi': row[23],
    }

    para = tek['para_birimi']
    simge = '₺' if para == 'TRY' else ('€' if para == 'EUR' else ('$' if para == 'USD' else para))

    # Satırları çek
    try:
        cursor.execute("""
            SELECT satir_no, stok_kodu, stok_adi, kaplama_tipi_adi, kalinlik_mikron,
                   malzeme_tipi, yuzey_alani, birim, miktar, birim_fiyat,
                   iskonto_oran, tutar, aciklama, gorsel_dosya
            FROM satislar.teklif_satirlari WHERE teklif_id = ? ORDER BY satir_no
        """, (teklif_id,))
        has_gorsel_col = True
    except Exception:
        cursor.execute("""
            SELECT satir_no, stok_kodu, stok_adi, kaplama_tipi_adi, kalinlik_mikron,
                   malzeme_tipi, yuzey_alani, birim, miktar, birim_fiyat,
                   iskonto_oran, tutar, aciklama
            FROM satislar.teklif_satirlari WHERE teklif_id = ? ORDER BY satir_no
        """, (teklif_id,))
        has_gorsel_col = False

    satirlar = []
    for srow in cursor.fetchall():
        satirlar.append({
            'no': srow[0], 'stok_kodu': srow[1] or '', 'stok_adi': srow[2] or '',
            'kaplama': srow[3] or '', 'kalinlik': srow[4],
            'malzeme': srow[5] or '', 'yuzey': srow[6],
            'birim': srow[7] or '', 'miktar': float(srow[8] or 0),
            'fiyat': float(srow[9] or 0), 'iskonto': float(srow[10] or 0),
            'tutar': float(srow[11] or 0), 'aciklama': srow[12] or '',
            'gorsel': str(srow[13] or '') if has_gorsel_col else '',
        })

    # Dosya yollarını çek
    sartname_dosya = ''
    gorsel_dosya = ''
    try:
        cursor.execute("""
            SELECT kaplama_sartnamesi_dosya, parca_gorseli_dosya
            FROM satislar.teklifler WHERE id = ?
        """, (teklif_id,))
        dosya_row = cursor.fetchone()
        if dosya_row:
            sartname_dosya = str(dosya_row[0] or '')
            gorsel_dosya = str(dosya_row[1] or '')
    except Exception:
        pass

    conn.close()

    # ── PDF oluştur ──
    _register_dejavu_fonts()

    firma = get_firma_bilgileri()
    firma_adi = firma.get('name', '') or APP_COMPANY
    firma_logo = get_firma_logo_path()

    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_no = tek['teklif_no'].replace('-', '_')
    dosya_adi = f"TEKLIF_{safe_no}_Rev{tek['revizyon_no']:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = str(REPORT_OUTPUT_DIR / dosya_adi)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setTitle(f"Teklif - {tek['teklif_no']}")
    c.setAuthor(firma_adi)

    usable_w = PAGE_W - 2 * MARGIN
    y = PAGE_H - MARGIN
    page_num = 1

    # ════════════════════════════════════════
    # HEADER
    # ════════════════════════════════════════
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
    except Exception:
        text_x = MARGIN + 6*mm

    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 16)
    c.drawString(text_x, y - 10*mm, "TEKLİF")
    c.setFont("NexorFont", 9)
    c.setFillColor(GRAY_300)
    c.drawString(text_x, y - 16*mm, firma_adi)
    c.drawString(text_x, y - 21*mm, f"Tarih: {_format_tarih(tek['tarih'])}")

    # Sağ üst - No ve durum
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 14)
    c.drawRightString(MARGIN + usable_w - 6*mm, y - 10*mm, f"{tek['teklif_no']} Rev.{tek['revizyon_no']:02d}")

    durum_text = DURUM_METINLER.get(tek['durum'], tek['durum'])
    durum_color = DURUM_RENKLER.get(tek['durum'], GRAY_500)
    badge_w = max(len(durum_text) * 3*mm + 8*mm, 25*mm)
    badge_x = MARGIN + usable_w - 6*mm - badge_w
    badge_y = y - header_h + 4*mm
    _draw_rounded_rect(c, badge_x, badge_y, badge_w, 7*mm, 3*mm, fill_color=durum_color)
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 9)
    c.drawCentredString(badge_x + badge_w / 2, badge_y + 2*mm, durum_text)

    y -= header_h + 6*mm

    # ════════════════════════════════════════
    # MÜŞTERİ ve TEKLİF BİLGİLERİ
    # ════════════════════════════════════════
    col_w = usable_w / 2 - 2*mm
    rx = MARGIN + col_w + 4*mm

    # Sol - Müşteri
    field_max_w = col_w - 34*mm  # Label sonrası kalan alan
    y = _draw_section_title(c, MARGIN, y, "MÜŞTERİ BİLGİLERİ", col_w)
    y_left = y
    y_left = _draw_field(c, MARGIN + 2*mm, y_left, "Firma:", tek['cari_unvani'], max_w=field_max_w)
    y_left = _draw_field(c, MARGIN + 2*mm, y_left, "Yetkili:", tek['cari_yetkili'], max_w=field_max_w)
    y_left = _draw_field(c, MARGIN + 2*mm, y_left, "Telefon:", tek['cari_telefon'], max_w=field_max_w)
    y_left = _draw_field(c, MARGIN + 2*mm, y_left, "E-posta:", tek['cari_email'], max_w=field_max_w)

    # Sağ - Teklif Bilgileri
    _draw_section_title(c, rx, y + 11*mm, "TEKLİF BİLGİLERİ", col_w)
    y_right = y
    y_right = _draw_field(c, rx + 2*mm, y_right, "Referans:", tek['referans_no'], max_w=field_max_w)
    y_right = _draw_field(c, rx + 2*mm, y_right, "Proje:", tek['proje_adi'], max_w=field_max_w)
    y_right = _draw_field(c, rx + 2*mm, y_right, "Teslim:", tek['teslim_suresi'], max_w=field_max_w)
    y_right = _draw_field(c, rx + 2*mm, y_right, "Ödeme:", tek['odeme_kosullari'], max_w=field_max_w)
    y_right = _draw_field(c, rx + 2*mm, y_right, "Geçerlilik:", _format_tarih(tek['gecerlilik']), max_w=field_max_w)

    y = min(y_left, y_right) - 8*mm

    # ════════════════════════════════════════
    # KALEM TABLOSU
    # ════════════════════════════════════════
    y = _draw_section_title(c, MARGIN, y, "TEKLİF KALEMLERİ", usable_w)

    # Tablo başlık
    cols = [8*mm, 18*mm, 30*mm, 22*mm, 18*mm, 18*mm, 15*mm, 15*mm, 17*mm]
    # Total = 8+18+30+22+18+18+15+15+17 = 161mm, kalan 9mm son sütuna ekle
    cols[-1] = usable_w - sum(cols[:-1])
    headers = ["#", "Ref.No", "İsim", "Kaplama", "Kalınlık", "Malzeme", "Birim", "Miktar", "B.Fiyat"]

    hdr_y = y
    _draw_rounded_rect(c, MARGIN, hdr_y - 7*mm, usable_w, 7*mm, 1*mm, fill_color=GRAY_700)
    c.setFillColor(WHITE)
    c.setFont("NexorFont-Bold", 7)
    cx = MARGIN + 2*mm
    for i, hdr in enumerate(headers):
        c.drawString(cx, hdr_y - 5*mm, hdr)
        cx += cols[i]

    y = hdr_y - 7*mm
    min_y = MARGIN + 60*mm  # Alan kontrolü (imza alanı için)

    for idx, satir in enumerate(satirlar):
        if y < min_y:
            _draw_footer(c, firma_adi, tek['teklif_no'], page_num)
            page_num += 1
            y = _new_page(c, firma_adi, tek['teklif_no'], page_num)
            y -= 10*mm

        row_bg = GRAY_100 if idx % 2 == 0 else WHITE
        c.setFillColor(row_bg)
        c.rect(MARGIN, y - 7*mm, usable_w, 7*mm, fill=1, stroke=0)

        c.setFillColor(BLACK)
        c.setFont("NexorFont", 7.5)
        cx = MARGIN + 2*mm

        try:
            kalinlik_val = float(satir['kalinlik']) if satir['kalinlik'] else None
        except Exception:
            kalinlik_val = None
        kalinlik_str = f"{kalinlik_val:.1f}µm" if kalinlik_val else '-'

        vals = [
            str(satir['no']),
            satir['stok_kodu'][:12],
            satir['stok_adi'][:20],
            satir['kaplama'][:14],
            kalinlik_str,
            satir['malzeme'][:12],
            satir['birim'],
            f"{satir['miktar']:,.0f}",
            _format_para(satir['fiyat'], simge),
        ]
        for i, v in enumerate(vals):
            if i == 8:  # B.Fiyat bold
                c.setFont("NexorFont-Bold", 7.5)
            c.drawString(cx, y - 5*mm, v)
            cx += cols[i]
        y -= 7*mm

    y -= 12*mm

    # ════════════════════════════════════════
    # SATIR GÖRSELLERİ
    # ════════════════════════════════════════
    satir_gorselleri = [s for s in satirlar if s.get('gorsel') and os.path.isfile(s['gorsel'])]
    if satir_gorselleri:
        if y < MARGIN + 80*mm:
            _draw_footer(c, firma_adi, tek['teklif_no'], page_num)
            page_num += 1
            y = _new_page(c, firma_adi, tek['teklif_no'], page_num)
            y -= 10*mm

        y = _draw_section_title(c, MARGIN, y, "PARÇA GÖRSELLERİ", usable_w)

        from reportlab.lib.utils import ImageReader
        img_per_row = 3
        img_max_w = (usable_w - (img_per_row - 1) * 4*mm) / img_per_row
        img_max_h = 45*mm

        for g_idx, satir in enumerate(satir_gorselleri):
            col_pos = g_idx % img_per_row
            if col_pos == 0 and g_idx > 0:
                y -= img_max_h + 14*mm
                if y < MARGIN + img_max_h + 30*mm:
                    _draw_footer(c, firma_adi, tek['teklif_no'], page_num)
                    page_num += 1
                    y = _new_page(c, firma_adi, tek['teklif_no'], page_num)
                    y -= 10*mm

            img_x = MARGIN + col_pos * (img_max_w + 4*mm)
            try:
                img = ImageReader(satir['gorsel'])
                iw, ih = img.getSize()
                ratio = min(img_max_w / iw, img_max_h / ih)
                draw_w = iw * ratio
                draw_h = ih * ratio
                _draw_rounded_rect(c, img_x, y - draw_h - 2*mm,
                                   img_max_w, draw_h + 10*mm, 2*mm, fill_color=GRAY_100)
                c.drawImage(satir['gorsel'], img_x + (img_max_w - draw_w) / 2, y - draw_h,
                            width=draw_w, height=draw_h,
                            preserveAspectRatio=True, mask='auto')
                # Satır numarası etiketi
                c.setFillColor(DARK_BG)
                c.setFont("NexorFont-Bold", 7)
                c.drawString(img_x + 2*mm, y - draw_h - 1*mm + 6*mm, f"Satır {satir['no']}: {satir['kaplama']}")
            except Exception:
                c.setFillColor(GRAY_500)
                c.setFont("NexorFont", 7)
                c.drawString(img_x, y - 5*mm, f"Satır {satir['no']}: {os.path.basename(satir['gorsel'])}")

        # Son satırdan sonra boşluk
        remaining = len(satir_gorselleri) % img_per_row
        if remaining > 0 or len(satir_gorselleri) > 0:
            y -= img_max_h + 16*mm

    # ════════════════════════════════════════
    # PARÇA GÖRSELİ VE KAPLAMA ŞARTNAMESİ
    # ════════════════════════════════════════
    has_gorsel = gorsel_dosya and os.path.isfile(gorsel_dosya)
    has_sartname = sartname_dosya and os.path.isfile(sartname_dosya)

    if has_gorsel or has_sartname:
        needed_h = 70*mm if has_gorsel else 15*mm
        if y < MARGIN + needed_h + 30*mm:
            _draw_footer(c, firma_adi, tek['teklif_no'], page_num)
            page_num += 1
            y = _new_page(c, firma_adi, tek['teklif_no'], page_num)
            y -= 10*mm

    if has_gorsel:
        y = _draw_section_title(c, MARGIN, y, "PARÇA GÖRSELİ", usable_w)
        img_max_w = 60*mm
        img_max_h = 60*mm
        try:
            from reportlab.lib.utils import ImageReader
            img = ImageReader(gorsel_dosya)
            iw, ih = img.getSize()
            ratio = min(img_max_w / iw, img_max_h / ih)
            draw_w = iw * ratio
            draw_h = ih * ratio
            img_x = MARGIN + (usable_w - draw_w) / 2
            _draw_rounded_rect(c, img_x - 2*mm, y - draw_h - 2*mm,
                               draw_w + 4*mm, draw_h + 4*mm, 2*mm,
                               fill_color=GRAY_100)
            c.drawImage(gorsel_dosya, img_x, y - draw_h,
                        width=draw_w, height=draw_h,
                        preserveAspectRatio=True, mask='auto')
            y -= draw_h + 8*mm
        except Exception:
            c.setFillColor(GRAY_500)
            c.setFont("NexorFont", 8)
            c.drawString(MARGIN + 4*mm, y - 5*mm, f"Görsel: {os.path.basename(gorsel_dosya)}")
            y -= 10*mm

    if has_sartname:
        y = _draw_section_title(c, MARGIN, y, "KAPLAMA ŞARTNAMESİ", usable_w)
        sartname_ext = os.path.splitext(sartname_dosya)[1].lower()
        if sartname_ext in ('.png', '.jpg', '.jpeg', '.bmp'):
            try:
                from reportlab.lib.utils import ImageReader
                img = ImageReader(sartname_dosya)
                iw, ih = img.getSize()
                sart_max_w = usable_w - 10*mm
                sart_max_h = 80*mm
                ratio = min(sart_max_w / iw, sart_max_h / ih)
                draw_w = iw * ratio
                draw_h = ih * ratio
                img_x = MARGIN + (usable_w - draw_w) / 2
                if y < MARGIN + draw_h + 30*mm:
                    _draw_footer(c, firma_adi, tek['teklif_no'], page_num)
                    page_num += 1
                    y = _new_page(c, firma_adi, tek['teklif_no'], page_num)
                    y -= 10*mm
                c.drawImage(sartname_dosya, img_x, y - draw_h,
                            width=draw_w, height=draw_h,
                            preserveAspectRatio=True, mask='auto')
                y -= draw_h + 8*mm
            except Exception:
                c.setFillColor(GRAY_500)
                c.setFont("NexorFont", 8)
                c.drawString(MARGIN + 4*mm, y - 5*mm, f"Şartname: {os.path.basename(sartname_dosya)}")
                y -= 10*mm
        else:
            _draw_rounded_rect(c, MARGIN, y - 10*mm, usable_w, 10*mm, 2*mm, fill_color=GRAY_100)
            c.setFillColor(BLACK)
            c.setFont("NexorFont", 9)
            c.drawString(MARGIN + 4*mm, y - 7*mm, f"Ek dosya: {os.path.basename(sartname_dosya)}")
            y -= 14*mm

    # ════════════════════════════════════════
    # NOTLAR VE ÖZEL KOŞULLAR
    # ════════════════════════════════════════
    if tek['ozel_kosullar'] or tek['notlar']:
        if y < MARGIN + 50*mm:
            _draw_footer(c, firma_adi, tek['teklif_no'], page_num)
            page_num += 1
            y = _new_page(c, firma_adi, tek['teklif_no'], page_num)
            y -= 10*mm

        if tek['ozel_kosullar']:
            y = _draw_section_title(c, MARGIN, y, "ÖZEL KOŞULLAR", usable_w)
            text = tek['ozel_kosullar']
            lines = _wrap_text(text, 90)
            text_h = len(lines) * 4*mm + 8*mm
            _draw_rounded_rect(c, MARGIN, y - text_h, usable_w, text_h, 3*mm,
                               fill_color=PRIMARY_LIGHT, stroke_color=PRIMARY)
            c.setFillColor(BLACK)
            c.setFont("NexorFont", 9)
            ty = y - 5*mm
            for line in lines[:8]:
                c.drawString(MARGIN + 4*mm, ty, line)
                ty -= 4*mm
            y -= text_h + 4*mm

        if tek['notlar']:
            y = _draw_section_title(c, MARGIN, y, "NOTLAR", usable_w)
            lines = _wrap_text(tek['notlar'], 90)
            c.setFillColor(GRAY_500)
            c.setFont("NexorFont", 8)
            for line in lines[:5]:
                c.drawString(MARGIN + 2*mm, y + 2*mm, line)
                y -= 4*mm
            y -= 4*mm

    # ════════════════════════════════════════
    # İMZA ALANI
    # ════════════════════════════════════════
    if y < MARGIN + 30*mm:
        _draw_footer(c, firma_adi, tek['teklif_no'], page_num)
        page_num += 1
        y = _new_page(c, firma_adi, tek['teklif_no'], page_num)
        y -= 10*mm

    y -= 10*mm
    sig_w = usable_w / 3 - 3*mm
    sig_labels = ["Hazırlayan", "Onaylayan", "Müşteri"]
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

    # ════════════════════════════════════════
    # FOOTER
    # ════════════════════════════════════════
    _draw_footer(c, firma_adi, tek['teklif_no'], page_num)

    # Kaydet ve aç
    c.save()
    os.startfile(pdf_path)
    return pdf_path


def _wrap_text(text, max_char=90):
    """Metni satırlara böl"""
    lines = []
    for paragraph in text.split('\n'):
        while paragraph:
            if len(paragraph) <= max_char:
                lines.append(paragraph)
                break
            split_idx = paragraph[:max_char].rfind(' ')
            if split_idx == -1:
                split_idx = max_char
            lines.append(paragraph[:split_idx])
            paragraph = paragraph[split_idx:].strip()
    return lines
