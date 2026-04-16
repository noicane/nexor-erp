# -*- coding: utf-8 -*-
"""
NEXOR ERP - Zimmet Teslim Formu PDF
PDFTemplate motoru uzerinden calisir.
"""
from datetime import datetime

from reportlab.lib.units import mm

from core.database import get_db_connection
from utils.pdf_template import PDFTemplate, format_tarih


def zimmet_formu_pdf(personel_id: int):
    """
    Personelin tum aktif zimmetlerini iceren zimmet teslim formu PDF'i olustur.

    Args:
        personel_id: Personel ID
    """
    conn = None
    try:
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
    except Exception as e:
        raise Exception(f"Zimmet verileri okunamadi: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # PDF Olustur
    dosya_adi = f"ZIMMET_FORM_{personel['ad']}_{personel['soyad']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    tpl = PDFTemplate(
        title="ZIMMET TESLIM FORMU",
        form_no=f"ZMT-{personel_id:05d}",
        filename=dosya_adi,
    )
    y = tpl.content_top

    # -- PERSONEL BILGILERI --
    y = tpl.section("PERSONEL BILGILERI", y)
    y = tpl.field_row(y, "Ad Soyad", f"{personel['ad']} {personel['soyad']}", "Sicil No", personel['sicil_no'])
    y = tpl.field_row(y, "Departman", personel['departman'], "Pozisyon", personel['pozisyon'])
    y = tpl.field_row(y, "TC Kimlik No", personel['tc'])
    y -= 2 * mm

    # -- ZIMMET LISTESI --
    y = tpl.section(f"TESLIM EDILEN ZIMMETLER ({len(zimmetler)} adet)", y)

    if zimmetler:
        headers = ["#", "Zimmet No", "Zimmet Adi", "Kategori", "Teslim", "Mkt", "Beden", "Yenileme"]
        col_widths = [8 * mm, 28 * mm, 42 * mm, 22 * mm, 22 * mm, 12 * mm, 16 * mm, 22 * mm]

        rows = []
        for idx, row in enumerate(zimmetler):
            rows.append([
                str(idx + 1),
                str(row[0] or ''),
                str(row[1] or ''),
                str(row[2] or ''),
                format_tarih(row[3]),
                str(row[4] or 1),
                str(row[5] or '-'),
                format_tarih(row[7]),
            ])

        y = tpl.table(y, headers, rows, col_widths, row_height=6.5 * mm)
    else:
        c = tpl.canvas
        c.setFillColor(tpl.theme['label_color'])
        c.setFont("NexorFont", 10)
        c.drawString(tpl.margin + 5 * mm, y + 1 * mm, "Bu personele ait aktif zimmet kaydi bulunmamaktadir.")
        y -= 10 * mm

    y -= 6 * mm

    # -- BEYAN --
    y = tpl.section("BEYAN", y)

    beyan_text = (
        "Yukarda listelenen malzemeleri eksiksiz ve hasarsiz olarak teslim aldim. "
        "Kullanimim sirasinda olusacak hasar ve kayiplardan sorumluyum. "
        "Is akdimin sona ermesi halinde tum zimmetleri eksiksiz iade edecegimi taahhut ederim."
    )
    y = tpl.text_block(y, beyan_text, max_lines=5)

    y -= 4 * mm

    # -- IMZA ALANLARI --
    y = tpl.section("ONAY VE IMZA", y)
    tpl.signature_row(y, ["Teslim Alan (Personel)", "Teslim Eden (IK / Depo)"])

    return tpl.finish()
