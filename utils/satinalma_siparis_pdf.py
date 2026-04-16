# -*- coding: utf-8 -*-
"""
NEXOR ERP - Satinalma Siparis Formu PDF
PDFTemplate motoru uzerinden calisir.
"""
from datetime import datetime, date

from reportlab.lib.units import mm

from core.database import get_db_connection
from utils.pdf_template import PDFTemplate, format_tarih


PB_SIMGE = {'TRY': 'TL', 'USD': '$', 'EUR': '\u20ac', 'GBP': '\u00a3'}


def _fmt_para(val, pb='TRY'):
    if val is None:
        return "-"
    simge = PB_SIMGE.get(pb, pb)
    return f"{float(val):,.2f} {simge}"


def satinalma_siparis_pdf(siparis_id: int):
    """Satinalma siparis formunu PDF olarak olusturur ve acar."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Kolonlari garanti et
        for col_sql in [
            "IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='satinalma' AND TABLE_NAME='siparisler' AND COLUMN_NAME='hazirlayan_ad') ALTER TABLE satinalma.siparisler ADD hazirlayan_ad NVARCHAR(150) NULL",
            "IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='satinalma' AND TABLE_NAME='siparisler' AND COLUMN_NAME='onaylayan_ad') ALTER TABLE satinalma.siparisler ADD onaylayan_ad NVARCHAR(150) NULL",
            "IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='satinalma' AND TABLE_NAME='siparisler' AND COLUMN_NAME='onay_tarihi') ALTER TABLE satinalma.siparisler ADD onay_tarihi DATETIME NULL",
            "IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='satinalma' AND TABLE_NAME='siparis_satirlari' AND COLUMN_NAME='para_birimi') ALTER TABLE satinalma.siparis_satirlari ADD para_birimi NVARCHAR(10) NULL",
        ]:
            cursor.execute(col_sql)
        conn.commit()

        # NULL ise current user ile backfill (eski kayitlar icin)
        try:
            from core.yetki_manager import YetkiManager
            cu_id = getattr(YetkiManager, '_current_user_id', None)
            if cu_id:
                cursor.execute("SELECT LTRIM(RTRIM(ISNULL(ad,'') + ' ' + ISNULL(soyad,''))) FROM sistem.kullanicilar WHERE id = ?", (cu_id,))
                rr = cursor.fetchone()
                cu_ad = rr[0].strip() if rr and rr[0] else None
                if cu_ad:
                    cursor.execute("""
                        UPDATE satinalma.siparisler
                        SET hazirlayan_ad = ISNULL(hazirlayan_ad, ?),
                            onaylayan_ad = ISNULL(onaylayan_ad, ?),
                            onay_tarihi  = ISNULL(onay_tarihi, GETDATE())
                        WHERE id = ?
                    """, (cu_ad, cu_ad, siparis_id))
                    conn.commit()
        except Exception:
            pass

        cursor.execute("""
            SELECT
                s.id, s.siparis_no, s.tarih, s.istenen_teslim_tarihi,
                s.odeme_vade_gun, s.notlar, s.durum,
                s.ara_toplam, s.kdv_toplam, s.genel_toplam,
                s.onay_tarihi,
                c.cari_kodu, c.unvan, c.vergi_no, c.vergi_dairesi,
                s.hazirlayan_ad,
                s.onaylayan_ad
            FROM satinalma.siparisler s
            LEFT JOIN musteri.cariler c ON s.tedarikci_id = c.id
            WHERE s.id = ?
        """, (siparis_id,))
        row = cursor.fetchone()
        if not row:
            raise Exception("Siparis bulunamadi")

        sip = {
            'id': row[0], 'siparis_no': row[1], 'tarih': row[2],
            'teslim_tarihi': row[3], 'vade': row[4],
            'notlar': row[5] or '', 'durum': row[6] or '',
            'ara_toplam': row[7], 'kdv_toplam': row[8], 'genel_toplam': row[9],
            'onay_tarihi': row[10],
            'tedarikci_kodu': row[11] or '-',
            'tedarikci_unvan': row[12] or '-',
            'vergi_no': row[13] or '-',
            'vergi_dairesi': row[14] or '-',
            'hazirlayan': row[15] or '-',
            'onaylayan': row[16] or '-',
        }

        cursor.execute("""
            SELECT satir_no, urun_kodu, urun_adi, siparis_miktar, birim,
                   birim_fiyat, tutar, kdv_orani, toplam,
                   ISNULL(para_birimi, 'TRY') AS para_birimi
            FROM satinalma.siparis_satirlari
            WHERE siparis_id = ?
            ORDER BY satir_no
        """, (siparis_id,))
        satirlar = cursor.fetchall()
    except Exception as e:
        raise Exception(f"Satinalma siparisi okunamadi: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # PDF Olustur
    dosya_adi = f"SATINALMA_SIPARIS_{sip['siparis_no']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    tpl = PDFTemplate(
        title="SATINALMA SIPARIS FORMU",
        form_no=f"SIP-{sip['siparis_no']}",
        filename=dosya_adi,
    )
    y = tpl.content_top

    # ── TEDARIKCI BILGILERI ──
    y = tpl.section("TEDARIKCI BILGILERI", y)
    y = tpl.field_row(y, "Tedarikci Kodu", sip['tedarikci_kodu'], "Unvan", sip['tedarikci_unvan'])
    y = tpl.field_row(y, "Vergi Dairesi", sip['vergi_dairesi'], "Vergi No", sip['vergi_no'])
    y = tpl.field_row(y, "Durum", sip['durum'])
    y -= 2 * mm

    # ── SIPARIS BILGILERI ──
    y = tpl.section("SIPARIS BILGILERI", y)
    y = tpl.field_row(y, "Siparis Tarihi", format_tarih(sip['tarih']), "Istenen Teslim", format_tarih(sip['teslim_tarihi']))
    y = tpl.field_row(y, "Odeme Vadesi", f"{sip['vade'] or 0} gun")
    y -= 2 * mm

    # ── SIPARIS KALEMLERI ──
    y = tpl.section("SIPARIS KALEMLERI", y)

    headers = ["No", "Urun Kodu", "Urun Adi", "Miktar", "Birim", "B.Fiyat", "KDV%", "Toplam"]
    col_widths = [8 * mm, 22 * mm, 55 * mm, 18 * mm, 12 * mm, 22 * mm, 12 * mm, 26 * mm]

    ara_toplam = 0.0
    kdv_toplam = 0.0
    genel_toplam_hesap = 0.0
    ortak_pb = None
    rows = []
    for satir in satirlar:
        pb = satir[9] or 'TRY'
        if ortak_pb is None:
            ortak_pb = pb
        elif ortak_pb != pb:
            ortak_pb = 'MIX'

        miktar = float(satir[3] or 0)
        bfiyat = float(satir[5] or 0)
        tutar = float(satir[6] or 0)
        kdv_oran = float(satir[7] or 0)
        toplam = float(satir[8] or 0)

        rows.append([
            str(satir[0] or ''),
            str(satir[1] or '')[:14],
            str(satir[2] or '')[:36],
            f"{miktar:,.2f}",
            str(satir[4] or ''),
            _fmt_para(bfiyat, pb),
            f"%{kdv_oran:.0f}",
            _fmt_para(toplam, pb),
        ])

        ara_toplam += tutar
        kdv_toplam += (toplam - tutar)
        genel_toplam_hesap += toplam

    y = tpl.table(y, headers, rows, col_widths)

    gt_pb = ortak_pb if ortak_pb and ortak_pb != 'MIX' else 'TRY'

    # Toplamlar
    c = tpl.canvas
    c.setFont("NexorFont", 8)
    c.setFillColor(tpl.theme['label_color'])
    c.drawRightString(tpl.page_w - tpl.margin - 4 * mm, y,
                      f"Ara Toplam: {_fmt_para(sip['ara_toplam'] if sip['ara_toplam'] else ara_toplam, gt_pb)}")
    y -= 5 * mm
    c.drawRightString(tpl.page_w - tpl.margin - 4 * mm, y,
                      f"KDV Toplam: {_fmt_para(sip['kdv_toplam'] if sip['kdv_toplam'] else kdv_toplam, gt_pb)}")
    y -= 6 * mm
    c.setFont("NexorFont-Bold", 10)
    c.setFillColor(tpl.theme['accent'])
    c.drawRightString(tpl.page_w - tpl.margin - 4 * mm, y,
                      f"GENEL TOPLAM: {_fmt_para(sip['genel_toplam'] if sip['genel_toplam'] else genel_toplam_hesap, gt_pb)}")
    y -= 10 * mm

    # ── NOTLAR ──
    if sip['notlar']:
        y = tpl.section("NOTLAR", y)
        y = tpl.text_block(y, sip['notlar'], max_lines=3)

    # ── IMZA ALANI ──
    y = tpl.section("ONAY VE IMZA", y)
    tpl.signature_row(y, ["Hazirlayan", "Onaylayan", "Tedarikci"])

    return tpl.finish()
