# -*- coding: utf-8 -*-
"""
NEXOR ERP - Depo Cikis Emri PDF Ciktisi
PDFTemplate motoru uzerinden calisir.
"""
from datetime import datetime

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
        'TAMAMLANDI': HexColor('#059669'),
    }
    return renkler.get(durum, HexColor('#6B7280'))


def _durum_metin(durum: str):
    metinler = {
        'BEKLIYOR': 'Bekliyor',
        'TAMAMLANDI': 'Tamamlandi',
    }
    return metinler.get(durum, durum)


def depo_cikis_pdf_olustur(emir_id: int):
    """
    Depo cikis emri PDF'i olustur ve ac.

    Args:
        emir_id: Depo cikis emri ID
    """
    conn = None
    try:
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
    except Exception as e:
        raise Exception(f"Depo cikis verileri okunamadi: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # -- PDF Olustur --
    dosya_adi = f"DEPO_CIKIS_{dce['emir_no'].replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    tpl = PDFTemplate(
        title="DEPO CIKIS EMRI",
        form_no=dce['emir_no'],
        filename=dosya_adi,
    )
    y = tpl.content_top
    c = tpl.canvas
    t = tpl.theme

    # Durum badge (header altina)
    durum_text = _durum_metin(dce['durum'])
    durum_color = _durum_renk(dce['durum'])
    c.setFillColor(durum_color)
    c.setFont("NexorFont-Bold", 10)
    c.drawRightString(tpl.page_w - tpl.margin - 5 * mm, y + 8 * mm, durum_text)

    # -- IS EMRI BILGILERI --
    y = tpl.section("IS EMRI BILGILERI", y)
    y = tpl.field_row(y, "Is Emri No", dce['is_emri_no'], "Termin Tarihi", format_tarih(dce['termin_tarihi']))
    y = tpl.field_row(y, "Musteri", dce['cari_unvani'])
    y -= 2 * mm

    # -- URUN BILGILERI --
    y = tpl.section("URUN BILGILERI", y)
    y = tpl.field_row(y, "Stok Kodu", dce['stok_kodu'], "Kaplama", dce['kaplama_tipi'] or '-')
    y = tpl.field_row(y, "Urun Adi", dce['stok_adi'])
    y = tpl.field_row(y, "Lot No", dce['lot_no'] or '-')
    y -= 2 * mm

    # -- TRANSFER BILGILERI --
    y = tpl.section("TRANSFER BILGILERI", y)

    # Kaynak -> Hedef depo oklu gosterim (canvas ile ozel cizim)
    from utils.pdf_template import _rounded_rect

    depo_box_w = tpl.usable_w * 0.38
    arrow_w = tpl.usable_w * 0.24
    depo_box_h = 22 * mm

    # Kaynak depo kutusu
    kaynak_x = tpl.margin
    _rounded_rect(c, kaynak_x, y - depo_box_h, depo_box_w, depo_box_h, 3 * mm,
                  fill_color=t['bg_light'], stroke_color=t['border_color'])
    c.setStrokeColor(t['border_color'])
    c.setLineWidth(0.5)
    c.setFillColor(t['label_color'])
    c.setFont("NexorFont", 8)
    c.drawCentredString(kaynak_x + depo_box_w / 2, y - 6 * mm, "KAYNAK DEPO")
    c.setFillColor(t['value_color'])
    c.setFont("NexorFont-Bold", 11)
    c.drawCentredString(kaynak_x + depo_box_w / 2, y - 12 * mm, dce['kaynak_depo_kod'])
    c.setFillColor(t['label_color'])
    c.setFont("NexorFont", 8)
    c.drawCentredString(kaynak_x + depo_box_w / 2, y - 17 * mm, dce['kaynak_depo_ad'])

    # Ok
    arrow_x = kaynak_x + depo_box_w
    arrow_mid_y = y - depo_box_h / 2
    c.setStrokeColor(t['accent'])
    c.setLineWidth(2)
    c.line(arrow_x + 8 * mm, arrow_mid_y, arrow_x + arrow_w - 8 * mm, arrow_mid_y)
    # Ok ucu
    c.setFillColor(t['accent'])
    arrow_tip_x = arrow_x + arrow_w - 8 * mm
    p = c.beginPath()
    p.moveTo(arrow_tip_x, arrow_mid_y + 3 * mm)
    p.lineTo(arrow_tip_x + 5 * mm, arrow_mid_y)
    p.lineTo(arrow_tip_x, arrow_mid_y - 3 * mm)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    # Ok ustune yazi
    c.setFillColor(t['accent'])
    c.setFont("NexorFont-Bold", 8)
    c.drawCentredString(arrow_x + arrow_w / 2, arrow_mid_y + 5 * mm, "TRANSFER")

    # Hedef depo kutusu
    hedef_x = kaynak_x + depo_box_w + arrow_w
    _rounded_rect(c, hedef_x, y - depo_box_h, depo_box_w, depo_box_h, 3 * mm,
                  fill_color=HexColor('#ECFDF5'), stroke_color=t['success'])
    c.setStrokeColor(t['success'])
    c.setLineWidth(0.5)
    c.setFillColor(t['label_color'])
    c.setFont("NexorFont", 8)
    c.drawCentredString(hedef_x + depo_box_w / 2, y - 6 * mm, "HEDEF DEPO")
    c.setFillColor(t['value_color'])
    c.setFont("NexorFont-Bold", 11)
    c.drawCentredString(hedef_x + depo_box_w / 2, y - 12 * mm, dce['hedef_depo_kod'])
    c.setFillColor(t['label_color'])
    c.setFont("NexorFont", 8)
    c.drawCentredString(hedef_x + depo_box_w / 2, y - 17 * mm, dce['hedef_depo_ad'])

    y -= depo_box_h + 6 * mm

    # Miktar kutucuklari
    x1 = tpl.margin + 4 * mm
    x2 = tpl.margin + tpl.col_w + 4 * mm
    tpl.big_value(x1, y, "Talep Miktar", f"{_format_miktar(dce['talep_miktar'])} {dce['birim']}", color=t['info'])
    tpl.big_value(x2, y, "Transfer Miktar", f"{_format_miktar(dce['transfer_miktar'])} {dce['birim']}", color=t['success'])
    y -= 18 * mm

    y -= 2 * mm

    # -- TARIH BILGILERI --
    y = tpl.section("TARIH BILGILERI", y)
    y = tpl.field_row(y, "Talep Tarihi", format_tarih(dce['talep_tarihi']),
                      "Tamamlanma Tarihi", format_tarih(dce['tamamlanma_tarihi']))
    y = tpl.field_row(y, "Olusturma Tarihi", format_tarih(dce['olusturma_tarihi']))
    y -= 2 * mm

    # -- IMZA ALANI --
    y -= 6 * mm
    y = tpl.section("ONAY VE IMZA", y)
    tpl.signature_row(y, ["Hazirlayan", "Depo Sorumlusu", "Teslim Alan"])

    return tpl.finish()
