# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Zirve Ticari Entegrasyon
Nexor irsaliyelerini Zirve ATLAS_KATAFOREZ_2026T veritabanına aktarır.

Zirve Tablo Yapısı (ATLAS_KATAFOREZ_2026T):
    IRSALIYE        - Ana irsaliye (SIRANO IDENTITY, P_ID GUID ile bağlantı)
    IRSALIYE_ALT    - Satırlar (REF IDENTITY, P_ID+IRSREF ile parent bağlantı)
    CARIGEN         - Cari kartlar (REF, CRK=hesap kodu)
    tbEIrsaliyeAlici       - E-İrsaliye alıcı bilgisi
    tbEIrsaliyeTasiyici    - E-İrsaliye taşıyıcı/araç
    tbEIrsaliyeTeslimatAdresi - E-İrsaliye teslimat adresi

Eşleştirme:
    Nexor musteri.cariler.zirve_cari_kodu <-> Zirve CARIGEN.CRK
"""

import uuid
import pyodbc
import base64
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

import os
from core.database import get_db_connection


# Zirve sabit değerleri
ZIRVE_TUR = 70            # Satış irsaliyesi
ZIRVE_ISLEMTIPI = 1
ZIRVE_AORS = 'S'          # Satış
ZIRVE_EIRSALIYE = 'E'     # E-İrsaliye
ZIRVE_DEPOREF = 1         # Varsayılan depo
ZIRVE_KULLANICI = 'NEXOR'
ZIRVE_KDVY = 20.0         # Varsayılan KDV %


@dataclass
class ZirveAktarimSonuc:
    basarili: bool
    zirve_sirano: Optional[int] = None
    zirve_evrakno: str = ""
    zirve_pid: str = ""
    mesaj: str = ""
    hata: Optional[str] = None


def _get_zirve_connection():
    """Zirve ATLAS_KATAFOREZ_2026T veritabanına bağlantı"""
    try:
        config_path = "C:/NEXOR/config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        db = config.get('database', {})
        server = db.get('server', r'192.168.10.66\SQLEXPRESS')
        user = db.get('user', 'MERP')
        pwd_b64 = db.get('password', '')
        try:
            password = base64.b64decode(pwd_b64).decode()
        except Exception:
            password = pwd_b64
    except Exception:
        server = os.environ.get('NEXOR_DB_SERVER', r'192.168.10.66\SQLEXPRESS')
        user = os.environ.get('NEXOR_DB_USER', '')
        password = os.environ.get('NEXOR_DB_PASS', '')

    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 18 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE=ATLAS_KATAFOREZ_2026T;'
        f'UID={user};PWD={password};'
        f'TrustServerCertificate=yes;'
        f'Connection Timeout=10'
    )
    return conn


def _get_zirve_cari(zirve_cursor, crk: str) -> Optional[dict]:
    """Zirve CARIGEN tablosundan cari bilgisi çek"""
    zirve_cursor.execute("""
        SELECT REF, STA, CRK, VERGINO, VERGID, ADRES1, SEHIR, SEMT,
               ULKE, TEL, EPOSTA, EFATURAMI, POSTAKODU
        FROM dbo.CARIGEN
        WHERE CRK = ?
    """, (crk,))
    row = zirve_cursor.fetchone()
    if row:
        return {
            'ref': row[0],
            'unvan': row[1] or '',
            'crk': row[2] or '',
            'vergi_no': row[3] or '',
            'vergi_dairesi': row[4] or '',
            'adres': row[5] or '',
            'sehir': row[6] or '',
            'semt': row[7] or '',
            'ulke': row[8] or 'TÜRKİYE',
            'tel': row[9] or '',
            'eposta': row[10] or '',
            'efatura': row[11] or '',
            'posta_kodu': row[12] or ''
        }
    return None


def _sonraki_evrakno(zirve_cursor) -> str:
    """Zirve'deki son EVRAKNO'dan sonraki numarayı üret"""
    yil = datetime.now().year
    prefix = f'IRS{yil}'

    zirve_cursor.execute("""
        SELECT MAX(EVRAKNO) FROM dbo.IRSALIYE
        WHERE EVRAKNO LIKE ? AND TUR = 70
    """, (f'{prefix}%',))
    row = zirve_cursor.fetchone()
    max_evrak = row[0] if row and row[0] else None

    if max_evrak:
        # IRS2026000001102 -> 000001102 -> 1102
        numara_str = max_evrak[len(prefix):]
        try:
            son_no = int(numara_str)
        except ValueError:
            son_no = 0
        yeni_no = son_no + 1
    else:
        yeni_no = 1

    # Format: IRS + YYYY + 9 basamaklı numara = 16 karakter
    return f"{prefix}{yeni_no:09d}"


def irsaliye_aktar(irsaliye_id: int) -> ZirveAktarimSonuc:
    """
    Nexor irsaliyesini Zirve'ye aktar.

    Args:
        irsaliye_id: siparis.cikis_irsaliyeleri.id

    Returns:
        ZirveAktarimSonuc
    """
    try:
        # 1) Nexor verilerini çek
        nexor_conn = get_db_connection()
        nexor_cursor = nexor_conn.cursor()

        # İrsaliye bilgileri
        nexor_cursor.execute("""
            SELECT ci.id, ci.irsaliye_no, ci.cari_id, ci.tarih, ci.sevk_tarihi,
                   ci.tasiyici_firma, ci.arac_plaka, ci.sofor_adi, ci.durum, ci.notlar,
                   COALESCE(c.unvan, c.kisa_ad, '') as musteri_adi,
                   c.zirve_cari_kodu, c.vergi_no, c.vergi_dairesi
            FROM siparis.cikis_irsaliyeleri ci
            LEFT JOIN musteri.cariler c ON ci.cari_id = c.id
            WHERE ci.id = ?
        """, (irsaliye_id,))
        irs = nexor_cursor.fetchone()

        if not irs:
            nexor_conn.close()
            return ZirveAktarimSonuc(basarili=False, hata="İrsaliye bulunamadı!")

        irsaliye_no = irs[1]
        cari_id = irs[2]
        tarih = irs[3]
        sevk_tarihi = irs[4] or tarih
        tasiyici = irs[5] or ''
        plaka = irs[6] or ''
        sofor = irs[7] or ''
        durum = irs[8]
        notlar = irs[9] or ''
        musteri_adi = irs[10] or ''
        zirve_cari_kodu = irs[11]
        firma_vergi_no = '1020415496'  # Atlas Kataforez VKN

        # Durum kontrolü
        if durum == 'IPTAL':
            nexor_conn.close()
            return ZirveAktarimSonuc(basarili=False, hata="İptal edilmiş irsaliye aktarılamaz!")

        # Zirve cari kodu kontrolü
        if not zirve_cari_kodu:
            nexor_conn.close()
            return ZirveAktarimSonuc(
                basarili=False,
                hata=f"Müşterinin Zirve cari kodu (CRK) tanımlı değil!\n\n"
                     f"Müşteri: {musteri_adi}\n\n"
                     f"Cari kartında 'Zirve Cari Kodu' alanını doldurun."
            )

        # Zaten aktarılmış mı?
        try:
            nexor_cursor.execute("""
                SELECT zirve_id, durum FROM entegrasyon.zirve_senkron_log
                WHERE referans_tablo = 'cikis_irsaliyeleri' AND referans_id = ? AND durum = 'BASARILI'
            """, (irsaliye_id,))
            existing = nexor_cursor.fetchone()
            if existing:
                nexor_conn.close()
                return ZirveAktarimSonuc(
                    basarili=False,
                    hata=f"Bu irsaliye zaten Zirve'ye aktarılmış!\n"
                         f"Zirve SIRANO: {existing[0]}"
                )
        except Exception:
            pass  # Tablo yoksa devam

        # İrsaliye satırları
        nexor_cursor.execute("""
            SELECT cis.lot_no, cis.miktar,
                   COALESCE(ie.stok_kodu, u.urun_kodu, '') as stok_kodu,
                   COALESCE(ie.stok_adi, u.urun_adi, '') as stok_adi,
                   COALESCE(b.kod, 'AD') as birim,
                   cis.is_emri_id, cis.urun_id
            FROM siparis.cikis_irsaliye_satirlar cis
            LEFT JOIN siparis.is_emirleri ie ON cis.is_emri_id = ie.id
            LEFT JOIN stok.urunler u ON cis.urun_id = u.id
            LEFT JOIN tanim.birimler b ON cis.birim_id = b.id
            WHERE cis.irsaliye_id = ?
            ORDER BY cis.satir_no
        """, (irsaliye_id,))
        satirlar = nexor_cursor.fetchall()

        if not satirlar:
            nexor_conn.close()
            return ZirveAktarimSonuc(basarili=False, hata="İrsaliye satırı bulunamadı!")

        # 2) Zirve'ye bağlan
        zirve_conn = _get_zirve_connection()
        zirve_cursor = zirve_conn.cursor()

        # 3) Zirve'de cari bul
        cari = _get_zirve_cari(zirve_cursor, zirve_cari_kodu)
        if not cari:
            zirve_conn.close()
            nexor_conn.close()
            return ZirveAktarimSonuc(
                basarili=False,
                hata=f"Zirve'de cari bulunamadı!\n\n"
                     f"CRK: {zirve_cari_kodu}\n"
                     f"Müşteri: {musteri_adi}\n\n"
                     f"Zirve'de bu hesap kodunun tanımlı olduğundan emin olun."
            )

        # 4) EVRAKNO üret
        evrakno = _sonraki_evrakno(zirve_cursor)

        # 5) P_ID üret (GUID)
        p_id = str(uuid.uuid4()).upper()

        now = datetime.now()

        # 6) Zirve'den cari P_ID al
        cari_p_id = None
        try:
            zirve_cursor.execute("SELECT P_ID FROM dbo.CARIGEN WHERE REF = ?", (cari['ref'],))
            row = zirve_cursor.fetchone()
            if row:
                cari_p_id = row[0]
        except Exception:
            pass

        # 7) IRSALIYE master INSERT
        zirve_cursor.execute("""
            INSERT INTO dbo.IRSALIYE (
                SUBE, EVRAKTAR, TUR, AORS, ISLEMTIPI, EVRAKNO, ACIKLAMA,
                CARIADI, CARIREF, CRK, DEPOREF, KULLANICI,
                EIRSALIYE, EFATURA, P_ID, IRSMI,
                TURAC, DOVIZC, MASRAFMERKEZI,
                ADRES1, SEMT1, SEHIR1, ULKE,
                TOPLAMKDV, GENELTOPLAM, TOPLAMKDVD, GENELTOPLAMD,
                TARIH_1, SUBE2, IVERGINO, CARIP_ID,
                KAGITFATURA, INTERNETSATIS, IDISIrsaliyesi
            ) VALUES (
                1, ?, 70, 'S', 1, ?, ?,
                ?, ?, ?, 1, ?,
                'E', 'E', ?, 1,
                N'Satış İrsaliyesi', 1, 'MERKEZ',
                ?, ?, ?, ?,
                0, 0, 0, 0,
                ?, 0, ?, ?,
                0, 0, 0
            )
        """, (
            tarih, evrakno, notlar,
            cari['unvan'], cari['ref'], cari['crk'], ZIRVE_KULLANICI,
            p_id,
            cari['adres'], cari['semt'], cari['sehir'], cari.get('ulke', 'TÜRKİYE'),
            tarih, firma_vergi_no, cari_p_id
        ))

        # Oluşturulan SIRANO'yu al
        zirve_cursor.execute("SELECT IDENT_CURRENT('dbo.IRSALIYE')")
        sirano = int(zirve_cursor.fetchone()[0])

        # 7) IRSALIYE_ALT satırları INSERT
        for idx, satir in enumerate(satirlar):
            lot_no = satir[0] or ''
            miktar = satir[1] or 0
            stok_kodu = satir[2] or ''
            stok_adi = satir[3] or ''
            birim = satir[4] or 'ADET'
            siralama = (idx + 1) * 2  # Zirve 2'şer artırıyor

            # Zirve'de stok ref ve P_ID bul
            stok_ref = 0
            stok_p_id = None
            if stok_kodu:
                zirve_cursor.execute("""
                    SELECT TOP 1 REF, P_ID FROM dbo.STOKGEN WHERE STK = ?
                """, (stok_kodu,))
                stok_row = zirve_cursor.fetchone()
                if stok_row:
                    stok_ref = stok_row[0]
                    stok_p_id = stok_row[1]

            # Satır P_ID ve SATIRP_ID
            satir_pid = str(uuid.uuid4()).upper()
            satir_no = idx + 1

            zirve_cursor.execute("""
                INSERT INTO dbo.IRSALIYE_ALT (
                    STK, STA, STB, MIKTAR, TUR, AORS, ISLEMTIPI,
                    EVRAKNO, IRSREF, IRSEVRAKNO, CARIREF,
                    DEPOREF, TARIH, KDVY, STOKREF, STOKP_ID,
                    P_ID, SIRALAMA, LOTNO, KULLANICI,
                    FATIP, BRKODU, DOVIZC, SUBE,
                    TURAC, MASRAFMERKEZI, FATIRSTUR,
                    IRSSATIRREF, SATIRREF, SATIRP_ID,
                    CKMIK, SIPMIKTAR, IRSMIKTAR, FATMIKTAR,
                    BRFTL, TUTARTL, KDVTL, OTVTL, NETTUTARTL,
                    INDY, INDTL, IND1, IND2, IND3, IND4, IND5, IND6,
                    GK, UGDK, SATINDTL, GRMIK,
                    GRBRFTL, CKBRFTL, GRTUTARTL, CKTUTARTL,
                    DEPO2REF, ANABROR2, ANABROR3, RECETEVAR,
                    KARTDOVIZC, KARTUGDK, KARTDOVIZTUTAR,
                    KDVDH, NETKG, BRUTKG, PAKETM,
                    INDSIZKDV, HARICTUTARTL, OIVVERGIMATRAH,
                    SEVKTARIHI, SUBE2,
                    BR2ISLEM, BR3ISLEM
                ) VALUES (
                    ?, ?, 'AD', ?, 70, 'S', 1,
                    ?, ?, ?, ?,
                    1, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    'N', 1, 1, 1,
                    N'Satış İrsaliyesi', 'MERKEZ', 2,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0,
                    0, 0, 0, 0,
                    0, 1, 1, 0,
                    1, 1, 0,
                    0, 0, 0, 0,
                    0, 0, 0,
                    ?, 0,
                    '*', '*'
                )
            """, (
                stok_kodu, stok_kodu, miktar,
                evrakno, sirano, evrakno, cari['ref'],
                tarih, ZIRVE_KDVY, stok_ref, stok_p_id,
                p_id, siralama, lot_no, ZIRVE_KULLANICI,
                satir_no, satir_no, satir_pid,
                miktar, miktar, miktar, miktar,
                sevk_tarihi
            ))

        # 8) tbEIrsaliyeAlici INSERT
        zirve_cursor.execute("""
            INSERT INTO dbo.tbEIrsaliyeAlici (
                vkn, unvan, sehir, ilce, irsaliyeP_ID, ulke
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            cari['vergi_no'], cari['unvan'],
            cari['sehir'], cari['semt'],
            p_id, cari.get('ulke', 'TÜRKİYE')
        ))

        # 9) tbEIrsaliyeTasiyici INSERT
        zirve_cursor.execute("""
            INSERT INTO dbo.tbEIrsaliyeTasiyici (
                sevk_tarihi, turu, vkn, unvan, AracPlaka, irsaliyeP_ID
            ) VALUES (?, 'Firma', ?, ?, ?, ?)
        """, (
            sevk_tarihi, firma_vergi_no,
            sofor or tasiyici, plaka, p_id
        ))

        # 10) tbEIrsaliyeTeslimatAdresi INSERT
        zirve_cursor.execute("""
            INSERT INTO dbo.tbEIrsaliyeTeslimatAdresi (
                sehir, ilce, posta_kodu, irsaliyeP_ID, ulke
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            cari['sehir'], cari['semt'],
            cari.get('posta_kodu', ''), p_id,
            cari.get('ulke', 'TÜRKİYE')
        ))

        zirve_conn.commit()
        zirve_conn.close()

        # 11) Nexor irsaliye kaydına Zirve bilgilerini yaz
        try:
            nexor_cursor.execute("""
                UPDATE siparis.cikis_irsaliyeleri
                SET zirve_evrakno = ?, zirve_sirano = ?, zirve_aktarim_tarihi = GETDATE()
                WHERE id = ?
            """, (evrakno, sirano, irsaliye_id))
        except Exception as upd_err:
            print(f"İrsaliye Zirve bilgisi güncelleme hatası: {upd_err}")

        # 12) Nexor senkron log
        try:
            nexor_cursor.execute("""
                INSERT INTO entegrasyon.zirve_senkron_log
                (islem_tipi, yonu, referans_tablo, referans_id, zirve_id, durum, request_data)
                VALUES ('IRSALIYE', 'NEXOR_ZIRVE', 'cikis_irsaliyeleri', ?, ?, 'BASARILI', ?)
            """, (
                irsaliye_id, str(sirano),
                f"EVRAKNO:{evrakno}, SIRANO:{sirano}, P_ID:{p_id}, CARI:{cari['crk']}, SATIR:{len(satirlar)}"
            ))
        except Exception as log_err:
            print(f"Senkron log hatası (kritik değil): {log_err}")

        nexor_conn.commit()

        nexor_conn.close()

        return ZirveAktarimSonuc(
            basarili=True,
            zirve_sirano=sirano,
            zirve_evrakno=evrakno,
            zirve_pid=p_id,
            mesaj=f"İrsaliye Zirve'ye aktarıldı!\n\n"
                  f"Nexor İrsaliye: {irsaliye_no}\n"
                  f"Zirve Evrak No: {evrakno}\n"
                  f"Zirve SIRANO: {sirano}\n"
                  f"Müşteri: {cari['unvan']}\n"
                  f"Satır: {len(satirlar)} kalem"
        )

    except Exception as e:
        # Hata logla
        try:
            log_conn = get_db_connection()
            log_cursor = log_conn.cursor()
            log_cursor.execute("""
                INSERT INTO entegrasyon.zirve_senkron_log
                (islem_tipi, yonu, referans_tablo, referans_id, durum, hata_mesaji)
                VALUES ('IRSALIYE', 'NEXOR_ZIRVE', 'cikis_irsaliyeleri', ?, 'HATA', ?)
            """, (irsaliye_id, str(e)[:500]))
            log_conn.commit()
            log_conn.close()
        except Exception:
            pass

        import traceback
        traceback.print_exc()
        return ZirveAktarimSonuc(basarili=False, hata=str(e))


def zirve_aktarim_kontrol(irsaliye_id: int) -> dict:
    """İrsaliyenin Zirve aktarım durumunu kontrol et"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT zirve_id, durum, islem_tarihi, hata_mesaji
            FROM entegrasyon.zirve_senkron_log
            WHERE referans_tablo = 'cikis_irsaliyeleri' AND referans_id = ?
            ORDER BY islem_tarihi DESC
        """, (irsaliye_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'aktarildi': row[1] == 'BASARILI',
                'zirve_sirano': row[0],
                'durum': row[1],
                'tarih': row[2],
                'hata': row[3]
            }
        return {'aktarildi': False, 'durum': None}
    except Exception:
        return {'aktarildi': False, 'durum': None}
