# -*- coding: utf-8 -*-
"""
NEXOR ERP - Is Emri PDF Ciktisi
PDFTemplate motoru uzerinden calisir.
"""
from datetime import datetime, date

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

from core.database import get_db_connection
from utils.pdf_template import PDFTemplate, format_tarih


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
        'BEKLIYOR': HexColor('#F59E0B'),
        'PLANLI': HexColor('#3B82F6'),
        'URETIMDE': HexColor('#10B981'),
        'TAMAMLANDI': HexColor('#059669'),
        'KALITE_BEKLIYOR': HexColor('#8B5CF6'),
        'IPTAL': HexColor('#EF4444'),
    }
    return renkler.get(durum, HexColor('#6B7280'))


def _durum_metin(durum: str):
    metinler = {
        'BEKLIYOR': 'Bekliyor',
        'PLANLI': 'Planlandi',
        'URETIMDE': 'Uretimde',
        'TAMAMLANDI': 'Tamamlandi',
        'KALITE_BEKLIYOR': 'Kalite Bekliyor',
        'IPTAL': 'Iptal',
    }
    return metinler.get(durum, durum)


def is_emri_pdf_olustur(is_emri_id: int):
    """
    Is emri detay PDF'i olustur ve ac.

    Args:
        is_emri_id: Is emri ID
    """
    conn = None
    try:
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
            raise Exception(f"Is emri bulunamadi (ID: {is_emri_id})")

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

        # is_emri_lotlar tablosundan da lotlari kontrol et (birden fazla lot olabilir)
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
    except Exception as e:
        raise Exception(f"Is emri verileri okunamadi: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # -- PDF Olustur --
    dosya_adi = f"IS_EMRI_{ie['is_emri_no'].replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    tpl = PDFTemplate(
        title="IS EMRI",
        form_no=ie['is_emri_no'],
        filename=dosya_adi,
    )
    y = tpl.content_top
    c = tpl.canvas
    t = tpl.theme

    # Durum badge (header altina)
    durum_text = _durum_metin(ie['durum'])
    durum_color = _durum_renk(ie['durum'])
    c.setFillColor(durum_color)
    c.setFont("NexorFont-Bold", 10)
    c.drawRightString(tpl.page_w - tpl.margin - 5 * mm, y + 8 * mm, durum_text)

    # -- MUSTERI BILGILERI --
    y = tpl.section("MUSTERI BILGILERI", y)
    y = tpl.field_row(y, "Musteri", ie['cari_unvani'], "Tarih", format_tarih(ie['tarih']))
    y = tpl.field_row(y, "Termin Tarihi", format_tarih(ie['termin_tarihi']),
                      "Oncelik", {1: "Cok Yuksek", 2: "Yuksek", 3: "Normal", 4: "Dusuk", 5: "Cok Dusuk"}.get(ie['oncelik'], str(ie['oncelik'])))

    # Termin uyarisi
    if ie['termin_tarihi'] and ie['durum'] not in ('TAMAMLANDI', 'IPTAL'):
        termin = ie['termin_tarihi']
        if hasattr(termin, 'date'):
            termin = termin.date()
        if termin < date.today():
            gecikme = (date.today() - termin).days
            c.setFillColor(t['error'])
            c.setFont("NexorFont-Bold", 8)
            c.drawString(tpl.margin + 4 * mm, y + 10 * mm, f"! {gecikme} gun gecikmis!")
            y -= 4 * mm

    y -= 2 * mm

    # -- URUN BILGILERI --
    y = tpl.section("URUN BILGILERI", y)
    y = tpl.field_row(y, "Stok Kodu", ie['stok_kodu'], "Kaplama", ie['kaplama_tipi'] or '-')
    y = tpl.field_row(y, "Urun Adi", ie['stok_adi'])
    y = tpl.field_row(y, "Lot No", ie['lot_no'] or '-', "Uretim Hatti", ie['hat_adi'])
    y -= 2 * mm

    # -- MIKTAR BILGILERI --
    y = tpl.section("MIKTAR BILGILERI", y)

    x1 = tpl.margin + 4 * mm
    x2 = tpl.margin + tpl.usable_w / 4 + 4 * mm
    x3 = tpl.margin + tpl.usable_w / 2 + 4 * mm
    x4 = tpl.margin + tpl.usable_w * 3 / 4 + 4 * mm

    tpl.big_value(x1, y, "Planlanan", f"{_format_miktar(ie['planlanan_miktar'])} {ie['birim']}", color=t['info'])
    tpl.big_value(x2, y, "Uretilen", f"{_format_miktar(ie['uretilen_miktar'])} {ie['birim']}", color=t['success'])
    tpl.big_value(x3, y, "Fire", f"{_format_miktar(ie['fire_miktar'])} {ie['birim']}", color=t['error'])
    tpl.big_value(x4, y, "Kalan", f"{_format_miktar(kalan)} {ie['birim']}", color=t['warning'])
    y -= 18 * mm

    # Bara ve sure
    bara_str = str(ie['toplam_bara'])
    sure_str = '-'
    if ie['tahmini_sure_dk'] > 0:
        saat = ie['tahmini_sure_dk'] // 60
        dk = ie['tahmini_sure_dk'] % 60
        sure_str = f"{saat} saat {dk} dk" if saat > 0 else f"{dk} dk"
    y = tpl.field_row(y, "Toplam Bara", bara_str, "Tahmini Sure", sure_str)
    y -= 2 * mm

    # -- OPERASYONLAR --
    if operasyonlar:
        y = tpl.section("URETIM OPERASYONLARI", y)

        headers = ["#", "Operasyon", "Plan (dk)", "Fiili (dk)", "Durum"]
        col_widths = [10 * mm, 65 * mm, 28 * mm, 28 * mm, 35 * mm]
        rows = []
        for op in operasyonlar:
            rows.append([
                str(op['sira']),
                op['adi'],
                str(op['plan_dk']),
                str(op['fiili_dk']),
                _durum_metin(op['durum']),
            ])
        y = tpl.table(y, headers, rows, col_widths)

    # -- OZEL TALIMATLAR --
    if ie['uretim_notu']:
        y = tpl.section("OZEL TALIMATLAR", y)
        y = tpl.text_block(y, ie['uretim_notu'], max_lines=5)

    # -- IMZA ALANI --
    y -= 6 * mm
    y = tpl.section("ONAY VE IMZA", y)
    tpl.signature_row(y, ["Hazirlayan", "Uretim Sorumlusu", "Kalite Kontrol"])

    return tpl.finish()
