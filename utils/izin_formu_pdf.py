# -*- coding: utf-8 -*-
"""
NEXOR ERP - Izin Talep Formu PDF
PDFTemplate motoru uzerinden calisir.
"""
from datetime import datetime, date

from reportlab.lib.units import mm

from core.database import get_db_connection
from utils.pdf_template import PDFTemplate, format_tarih


def izin_formu_pdf(talep_id: int):
    """
    Izin talep formunu PDF olarak olusturur ve acar.

    Args:
        talep_id: ik.izin_talepleri tablosundaki ID
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

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
    except Exception as e:
        raise Exception(f"Izin talebi okunamadi: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

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
    dosya_adi = (
        f"IZIN_FORM_{talep['ad']}_{talep['soyad']}_{talep_id}"
        f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

    tpl = PDFTemplate(
        title="IZIN TALEP FORMU",
        form_no=f"IZN-{talep_id:05d}",
        filename=dosya_adi,
    )
    y = tpl.content_top

    # ── PERSONEL BILGILERI ──
    y = tpl.section("PERSONEL BILGILERI", y)
    y = tpl.field_row(y, "Ad Soyad", f"{talep['ad']} {talep['soyad']}", "Sicil No", talep['sicil_no'])
    y = tpl.field_row(y, "Departman", talep['departman'], "Pozisyon", talep['pozisyon'])
    y = tpl.field_row(y, "TC Kimlik No", talep['tc'])
    y -= 2 * mm

    # ── IZIN BILGILERI ──
    y = tpl.section("IZIN BILGILERI", y)
    y = tpl.field_row(y, "Izin Turu", talep['izin_turu'], "Talep Tarihi", format_tarih(talep['talep_tarihi']))
    y = tpl.field_row(y, "Baslangic Tarihi", format_tarih(talep['baslangic']),
                         "Bitis Tarihi", format_tarih(talep['bitis']))

    # Gun sayisi + durum (buyuk)
    durum = talep['durum']
    durum_renk = tpl.theme['success'] if durum == 'ONAYLANDI' else tpl.theme['accent']

    x1 = tpl.margin + 4 * mm
    x2 = tpl.margin + tpl.col_w + 4 * mm
    tpl.big_value(x1, y, "Toplam Gun Sayisi", f"{talep['gun_sayisi']} Gun")
    tpl.big_value(x2, y, "Durum", durum, color=durum_renk)
    y -= 18 * mm

    if talep['onay_tarihi']:
        y = tpl.field_row(y, "Onay Tarihi", format_tarih(talep['onay_tarihi']))

    y -= 4 * mm

    # ── ACIKLAMA ──
    if talep['aciklama']:
        y = tpl.section("ACIKLAMA", y)
        y = tpl.text_block(y, talep['aciklama'], max_lines=5)

    # ── IMZA ALANI ──
    y -= 6 * mm
    y = tpl.section("ONAY VE IMZA", y)
    tpl.signature_row(y, ["Personel", "Birim Yoneticisi", "Insan Kaynaklari"])

    return tpl.finish()
