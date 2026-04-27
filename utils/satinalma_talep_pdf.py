# -*- coding: utf-8 -*-
"""
NEXOR ERP - Satinalma Talep Formu PDF
PDFTemplate motoru uzerinden calisir.
"""
from datetime import datetime, date

from reportlab.lib.units import mm

from core.database import get_db_connection
from utils.pdf_template import PDFTemplate, format_tarih


PB_SIMGE = {'TRY': 'TL', 'USD': '$', 'EUR': '\u20ac', 'GBP': '\u00a3'}


def _fmt_para(val, pb='TRY'):
    if val is None or val == 0:
        return "-"
    simge = PB_SIMGE.get(pb, pb)
    return f"{float(val):,.2f} {simge}"


def satinalma_talep_pdf(talep_id: int):
    """Satinalma talep formunu PDF olarak olusturur ve acar."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

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
                COALESCE(sa.ad + ' ' + sa.soyad,
                         LTRIM(RTRIM(ISNULL(uk.ad,'') + ' ' + ISNULL(uk.soyad,'')))) as satinalma_onaylayan,
                ted.unvan as tedarikci_unvan,
                ted.telefon as tedarikci_telefon
            FROM satinalma.talepler t
            JOIN ik.personeller p ON t.talep_eden_id = p.id
            LEFT JOIN ik.departmanlar d ON t.departman_id = d.id
            LEFT JOIN ik.personeller amir ON t.amir_id = amir.id
            LEFT JOIN sistem.kullanicilar uk ON t.satinalma_onaylayan_id = uk.id
            LEFT JOIN ik.personeller sa ON uk.personel_id = sa.id
            LEFT JOIN musteri.cariler ted ON t.tedarikci_id = ted.id
            WHERE t.id = ?
        """, (talep_id,))
        row = cursor.fetchone()
        if not row:
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
            'tedarikci': row[19] or '-',
            'tedarikci_tel': row[20] or '-',
        }

        cursor.execute("""
            SELECT satir_no, urun_kodu, urun_adi, talep_miktar, birim,
                   tahmini_birim_fiyat, tahmini_tutar, aciklama,
                   ISNULL(para_birimi, 'TRY') as para_birimi
            FROM satinalma.talep_satirlari
            WHERE talep_id = ?
            ORDER BY satir_no
        """, (talep_id,))
        satirlar = cursor.fetchall()
    except Exception as e:
        raise Exception(f"Satinalma talebi okunamadi: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # PDF Olustur
    dosya_adi = f"SATINALMA_TALEP_{talep['talep_no']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    # Para birimini satirlardan al
    para_birimi = 'TRY'
    if satirlar:
        pb_first = satirlar[0][8] if len(satirlar[0]) > 8 and satirlar[0][8] else 'TRY'
        para_birimi = pb_first

    tpl = PDFTemplate(
        title="SATINALMA TALEP FORMU",
        form_no=talep['talep_no'],
        filename=dosya_adi,
    )
    y = tpl.content_top

    # ── TALEP BILGILERI ──
    y = tpl.section("TALEP BILGILERI", y)
    y = tpl.field_row(y, "Talep Eden", talep['talep_eden'], "Sicil No", talep['sicil_no'])
    y = tpl.field_row(y, "Departman", talep['departman'], "Talep Tarihi", format_tarih(talep['tarih']))
    y = tpl.field_row(y, "Istenen Termin", format_tarih(talep['istenen_termin']), "Oncelik", talep['oncelik'])
    y = tpl.field_row(y, "Durum", talep['durum'], "Tahmini Tutar", _fmt_para(talep['tahmini_tutar'], para_birimi))
    # Tedarikci bilgisi (varsa)
    if talep['tedarikci'] and talep['tedarikci'] != '-':
        tel = talep['tedarikci_tel'] if talep['tedarikci_tel'] and talep['tedarikci_tel'] != '-' else ''
        tel_txt = f" ({tel})" if tel else ""
        y = tpl.field_row(y, "Tedarikci", f"{talep['tedarikci']}{tel_txt}"[:100])
    if talep['talep_nedeni']:
        y = tpl.field_row(y, "Talep Nedeni", talep['talep_nedeni'][:80])
    y -= 2 * mm

    # ── MALZEME LISTESI ──
    y = tpl.section("TALEP EDILEN MALZEMELER", y)

    pb_label = PB_SIMGE.get(para_birimi, para_birimi)
    headers = ["No", "Urun Kodu", "Urun Adi", "Miktar", "Birim", "B.Fiyat", f"Tutar ({pb_label})"]
    col_widths = [8 * mm, 22 * mm, 58 * mm, 20 * mm, 15 * mm, 22 * mm, 30 * mm]

    genel_toplam = 0
    rows = []
    for satir in satirlar:
        rows.append([
            str(satir[0] or ''),
            str(satir[1] or '')[:13],
            str(satir[2] or '')[:38],
            f"{float(satir[3]):,.2f}" if satir[3] else '-',
            str(satir[4] or ''),
            f"{float(satir[5]):,.2f}" if satir[5] else '-',
            f"{float(satir[6]):,.2f}" if satir[6] else '-',
        ])
        if satir[6]:
            genel_toplam += float(satir[6])

    y = tpl.table(y, headers, rows, col_widths)

    # Toplam
    c = tpl.canvas
    c.setFont("NexorFont-Bold", 9)
    c.setFillColor(tpl.theme['accent'])
    c.drawRightString(tpl.page_w - tpl.margin - 4 * mm, y,
                      f"GENEL TOPLAM: {_fmt_para(genel_toplam, para_birimi)}")
    y -= 10 * mm

    # ── ONAY BILGILERI ──
    y = tpl.section("ONAY BILGILERI", y)
    amir_text = f"{talep['amir_onay'] or 'BEKLEMEDE'} - {format_tarih(talep['amir_onay_tarihi'])} - {talep['amir_adi']}"
    sa_text = f"{talep['sa_onay'] or 'BEKLEMEDE'} - {format_tarih(talep['sa_onay_tarihi'])} - {talep['sa_onaylayan']}"
    y = tpl.field_row(y, "Amir Onay", amir_text, "Satinalma Onay", sa_text)
    y -= 2 * mm

    # ── IMZA ALANI ──
    y = tpl.section("ONAY VE IMZA", y)
    tpl.signature_row(y, ["Talep Eden", "Birim Amiri", "Satinalma", "Genel Mudur"])

    return tpl.finish()
