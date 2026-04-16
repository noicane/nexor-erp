# -*- coding: utf-8 -*-
"""
NEXOR ERP - Teklif PDF Ciktisi
PDFTemplate motoru uzerinden calisir.
"""
import os
from datetime import datetime, date

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

from core.database import get_db_connection
from utils.pdf_template import PDFTemplate, format_tarih, _rounded_rect, MARGIN


DURUM_METINLER = {
    'TASLAK': 'Taslak', 'GONDERILDI': 'Gonderildi', 'ONAYLANDI': 'Onaylandi',
    'REDDEDILDI': 'Reddedildi', 'IPTAL': 'Iptal',
    'IS_EMRINE_DONUSTURULDU': 'Is Emrine Donusturuldu',
}


def _fmt_para(val, simge='TL'):
    if val is None or val == 0:
        return "-"
    try:
        v = float(val)
        return f"{v:,.2f} {simge}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(val)


def _wrap_text(text, max_char=90):
    lines = []
    for paragraph in (text or '').split('\n'):
        while paragraph:
            if len(paragraph) <= max_char:
                lines.append(paragraph)
                break
            idx = paragraph[:max_char].rfind(' ')
            if idx == -1:
                idx = max_char
            lines.append(paragraph[:idx])
            paragraph = paragraph[idx:].strip()
    return lines


def teklif_pdf_olustur(teklif_id: int):
    """Teklif PDF'i olustur ve ac."""

    # ── Veri cek ──
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.id, t.teklif_no, t.revizyon_no, t.tarih, t.gecerlilik_tarihi,
                   t.cari_unvani, t.cari_yetkili, t.cari_telefon, t.cari_email,
                   t.ara_toplam, t.iskonto_oran, t.iskonto_tutar,
                   t.kdv_oran, t.kdv_tutar, t.genel_toplam, t.para_birimi,
                   t.durum, t.referans_no, t.proje_adi, t.teslim_suresi,
                   t.odeme_kosullari, t.notlar, t.ozel_kosullar, t.olusturma_tarihi
            FROM satislar.teklifler t
            WHERE t.id = ? AND t.silindi_mi = 0
        """, (teklif_id,))
        row = cursor.fetchone()
        if not row:
            raise Exception(f"Teklif bulunamadi (ID: {teklif_id})")

        tek = {
            'id': row[0], 'teklif_no': row[1] or '', 'revizyon_no': row[2] or 0,
            'tarih': row[3], 'gecerlilik': row[4],
            'cari_unvani': row[5] or '', 'cari_yetkili': row[6] or '',
            'cari_telefon': row[7] or '', 'cari_email': row[8] or '',
            'para_birimi': row[15] or 'TRY', 'durum': row[16] or 'TASLAK',
            'referans_no': row[17] or '', 'proje_adi': row[18] or '',
            'teslim_suresi': row[19] or '', 'odeme_kosullari': row[20] or '',
            'notlar': row[21] or '', 'ozel_kosullar': row[22] or '',
        }

        simge = {'TRY': 'TL', 'EUR': 'EUR', 'USD': 'USD'}.get(tek['para_birimi'], tek['para_birimi'])

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
            try:
                kal = float(srow[4]) if srow[4] else None
            except Exception:
                kal = None
            satirlar.append({
                'no': srow[0], 'stok_kodu': srow[1] or '', 'stok_adi': srow[2] or '',
                'kaplama': srow[3] or '', 'kalinlik': f"{kal:.1f}um" if kal else '-',
                'malzeme': srow[5] or '', 'birim': srow[7] or '',
                'miktar': f"{float(srow[8] or 0):,.0f}",
                'fiyat': _fmt_para(srow[9], simge),
                'gorsel': str(srow[13] or '') if has_gorsel_col else '',
            })

        gorsel_dosya = ''
        sartname_dosya = ''
        try:
            cursor.execute("SELECT kaplama_sartnamesi_dosya, parca_gorseli_dosya FROM satislar.teklifler WHERE id = ?", (teklif_id,))
            dr = cursor.fetchone()
            if dr:
                sartname_dosya = str(dr[0] or '')
                gorsel_dosya = str(dr[1] or '')
        except Exception:
            pass

    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # ── PDF Olustur ──
    safe_no = tek['teklif_no'].replace('-', '_')
    dosya_adi = f"TEKLIF_{safe_no}_Rev{tek['revizyon_no']:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    tpl = PDFTemplate(
        title="TEKLIF",
        form_no=f"{tek['teklif_no']} Rev.{tek['revizyon_no']:02d}",
        filename=dosya_adi,
    )
    c = tpl.canvas
    t = tpl.theme
    y = tpl.content_top

    # Durum badge (sag ust)
    durum_text = DURUM_METINLER.get(tek['durum'], tek['durum'])
    durum_colors = {
        'TASLAK': t['muted'], 'GONDERILDI': t['info'], 'ONAYLANDI': t['success'],
        'REDDEDILDI': t['error'], 'IPTAL': t['muted'],
        'IS_EMRINE_DONUSTURULDU': HexColor('#8B5CF6'),
    }
    d_color = durum_colors.get(tek['durum'], t['muted'])
    badge_w = max(len(durum_text) * 3 * mm + 8 * mm, 25 * mm)
    badge_x = tpl.page_w - tpl.margin - badge_w
    _rounded_rect(c, badge_x, y + 8 * mm, badge_w, 7 * mm, 3 * mm, fill_color=d_color)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("NexorFont-Bold", 9)
    c.drawCentredString(badge_x + badge_w / 2, y + 10 * mm, durum_text)

    # ── Musteri + Teklif bilgileri (2 kolon) ──
    col_w = tpl.usable_w / 2 - 2 * mm
    rx = tpl.margin + col_w + 4 * mm

    y = tpl.section("MUSTERI BILGILERI", y)
    y_left = y
    y_left = tpl.field_row(y_left, "Firma", tek['cari_unvani'][:40])
    y_left = tpl.field_row(y_left, "Yetkili", tek['cari_yetkili'][:30])
    y_left = tpl.field_row(y_left, "Telefon", tek['cari_telefon'], "E-posta", tek['cari_email'])

    # Sag kolon: teklif bilgileri (ayni y seviyesinde)
    c.setFillColor(t['section_bg'])
    c.setFont("NexorFont-Bold", 9)
    _rounded_rect(c, rx, y + 10 * mm, col_w, 8 * mm, 2 * mm, fill_color=t['section_bg'])
    c.setFillColor(t['section_text'])
    c.drawString(rx + 4 * mm, y + 12.5 * mm, "TEKLIF BILGILERI")

    tpl.field(rx + 2 * mm, y, "Referans", tek['referans_no'][:30])
    tpl.field(rx + 2 * mm, y - 14 * mm, "Proje", tek['proje_adi'][:30])
    tpl.field(rx + 2 * mm, y - 28 * mm, "Teslim", tek['teslim_suresi'][:25])
    tpl.field(rx + 2 * mm, y - 42 * mm, "Odeme", tek['odeme_kosullari'][:25])
    tpl.field(rx + 2 * mm, y - 56 * mm, "Gecerlilik", format_tarih(tek['gecerlilik']))

    y = min(y_left, y - 70 * mm) - 4 * mm

    # ── Kalem Tablosu ──
    headers = ["#", "Ref.No", "Isim", "Kaplama", "Kalinlik", "Malzeme", "Birim", "Miktar", "B.Fiyat"]
    col_widths = [8*mm, 18*mm, 30*mm, 22*mm, 18*mm, 18*mm, 15*mm, 15*mm, None]
    col_widths[-1] = tpl.usable_w - sum(w for w in col_widths if w)

    rows = []
    for s in satirlar:
        rows.append([
            str(s['no']), s['stok_kodu'][:12], s['stok_adi'][:20],
            s['kaplama'][:14], s['kalinlik'], s['malzeme'][:12],
            s['birim'], s['miktar'], s['fiyat']
        ])

    y = tpl.section("TEKLIF KALEMLERI", y)

    # Sayfa kontrolu - cok satirsa yeni sayfa
    available = y - tpl.margin - 60 * mm
    row_h = 7 * mm
    rows_fit = int(available / row_h)

    if len(rows) <= rows_fit:
        y = tpl.table(y, headers, rows, col_widths, row_height=row_h)
    else:
        # Ilk sayfa
        y = tpl.table(y, headers, rows[:rows_fit], col_widths, row_height=row_h)
        remaining = rows[rows_fit:]
        while remaining:
            y = tpl.new_page()
            y -= 6 * mm
            batch = remaining[:40]
            remaining = remaining[40:]
            y = tpl.table(y, headers, batch, col_widths, row_height=row_h)

    y -= 4 * mm

    # ── Satir Gorselleri ──
    satir_gorselleri = [s for s in satirlar if s.get('gorsel') and os.path.isfile(s['gorsel'])]
    if satir_gorselleri:
        if y < tpl.margin + 80 * mm:
            y = tpl.new_page()

        y = tpl.section("PARCA GORSELLERI", y)
        img_per_row = 3
        img_max_w = (tpl.usable_w - (img_per_row - 1) * 4 * mm) / img_per_row
        img_max_h = 45 * mm

        for g_idx, satir in enumerate(satir_gorselleri):
            col_pos = g_idx % img_per_row
            if col_pos == 0 and g_idx > 0:
                y -= img_max_h + 14 * mm
                if y < tpl.margin + img_max_h + 30 * mm:
                    y = tpl.new_page()

            img_x = tpl.margin + col_pos * (img_max_w + 4 * mm)
            try:
                img = ImageReader(satir['gorsel'])
                iw, ih = img.getSize()
                ratio = min(img_max_w / iw, img_max_h / ih)
                draw_w, draw_h = iw * ratio, ih * ratio
                _rounded_rect(c, img_x, y - draw_h - 2 * mm,
                              img_max_w, draw_h + 10 * mm, 2 * mm, fill_color=t['bg_light'])
                c.drawImage(satir['gorsel'], img_x + (img_max_w - draw_w) / 2, y - draw_h,
                            width=draw_w, height=draw_h, preserveAspectRatio=True, mask='auto')
                c.setFillColor(t['value_color'])
                c.setFont("NexorFont-Bold", 7)
                c.drawString(img_x + 2 * mm, y - draw_h - 1 * mm + 6 * mm,
                             f"Satir {satir['no']}: {satir['kaplama'][:20]}")
            except Exception:
                pass

        y -= img_max_h + 16 * mm

    # ── Parca gorseli + sartname ──
    has_gorsel = gorsel_dosya and os.path.isfile(gorsel_dosya)
    has_sartname = sartname_dosya and os.path.isfile(sartname_dosya)

    if has_gorsel:
        if y < tpl.margin + 80 * mm:
            y = tpl.new_page()
        y = tpl.section("PARCA GORSELI", y)
        try:
            img = ImageReader(gorsel_dosya)
            iw, ih = img.getSize()
            ratio = min(60 * mm / iw, 60 * mm / ih)
            dw, dh = iw * ratio, ih * ratio
            ix = tpl.margin + (tpl.usable_w - dw) / 2
            c.drawImage(gorsel_dosya, ix, y - dh, width=dw, height=dh,
                        preserveAspectRatio=True, mask='auto')
            y -= dh + 8 * mm
        except Exception:
            y -= 10 * mm

    if has_sartname:
        if y < tpl.margin + 40 * mm:
            y = tpl.new_page()
        y = tpl.section("KAPLAMA SARTNAMESI", y)
        ext = os.path.splitext(sartname_dosya)[1].lower()
        if ext in ('.png', '.jpg', '.jpeg', '.bmp'):
            try:
                img = ImageReader(sartname_dosya)
                iw, ih = img.getSize()
                max_w = tpl.usable_w - 10 * mm
                ratio = min(max_w / iw, 80 * mm / ih)
                dw, dh = iw * ratio, ih * ratio
                c.drawImage(sartname_dosya, tpl.margin + (tpl.usable_w - dw) / 2, y - dh,
                            width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                y -= dh + 8 * mm
            except Exception:
                y -= 10 * mm
        else:
            c.setFillColor(t['label_color'])
            c.setFont("NexorFont", 9)
            c.drawString(tpl.margin + 4 * mm, y - 5 * mm, f"Ek dosya: {os.path.basename(sartname_dosya)}")
            y -= 14 * mm

    # ── Ozel kosullar + Notlar ──
    if tek['ozel_kosullar']:
        if y < tpl.margin + 40 * mm:
            y = tpl.new_page()
        y = tpl.section("OZEL KOSULLAR", y)
        y = tpl.text_block(y, tek['ozel_kosullar'], max_lines=8)

    if tek['notlar']:
        if y < tpl.margin + 30 * mm:
            y = tpl.new_page()
        y = tpl.section("NOTLAR", y)
        y = tpl.text_block(y, tek['notlar'], max_lines=5)

    # ── Imza ──
    if y < tpl.margin + 30 * mm:
        y = tpl.new_page()
    y -= 6 * mm
    tpl.signature_row(y, ["Hazirlayan", "Onaylayan", "Musteri"])

    return tpl.finish()
