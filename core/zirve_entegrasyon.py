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

# Zirve'ye stok aktariminda sorulan onay sifresi.
# Bu sifre harici sistemde degisiklik yapmadan once ikinci guvenlik kontrolu saglar.
# Degistirmek icin bu sabiti duzenleyin.
ZIRVE_AKTARIM_SIFRESI = 'zirve2026'


@dataclass
class ZirveAktarimSonuc:
    basarili: bool
    zirve_sirano: Optional[int] = None
    zirve_evrakno: str = ""
    zirve_pid: str = ""
    mesaj: str = ""
    hata: Optional[str] = None


def _get_zirve_connection():
    """Zirve ATLAS_KATAFOREZ_2026T veritabanına bağlantı.

    Oncelik sirasi:
        1. db_manager'da tanimli 'ZIRVE' baglantisi (sistem_veritabani_baglantilari)
        2. db_manager'daki ERP credentials'i + DATABASE override
        3. UDL dosyasi (Nexor.UDL)
        4. C:/NEXOR/config.json
        5. Environment variables (son care)
    """
    server = None
    user = None
    password = None
    driver = 'ODBC Driver 18 for SQL Server'

    # 1) db_manager'da ZIRVE tanimli mi?
    try:
        from core.database_manager import db_manager
        if 'ZIRVE' in db_manager.get_available_connections():
            return db_manager.get_connection('ZIRVE')
    except Exception:
        pass

    # 2) ERP credentials'i al, DATABASE'i override et
    try:
        from core.database_manager import db_manager
        erp_cfg = db_manager._configs.get('ERP') if hasattr(db_manager, '_configs') else None
        if erp_cfg and erp_cfg.get('user') and erp_cfg.get('password'):
            server = erp_cfg.get('server')
            user = erp_cfg.get('user')
            password = erp_cfg.get('password')
            driver = erp_cfg.get('driver', driver)
    except Exception:
        pass

    # 3) UDL dosyasi
    if not user or not password:
        try:
            from core.external_config import _UDL_FILE, parse_udl_file
            if _UDL_FILE and parse_udl_file:
                udl = parse_udl_file(_UDL_FILE)
                if udl and udl.get('user'):
                    server = server or udl.get('server')
                    user = udl.get('user')
                    password = udl.get('password', '')
        except Exception:
            pass

    # 4) C:/NEXOR/config.json (eski davranis)
    if not user or not password:
        try:
            config_path = "C:/NEXOR/config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            db = config.get('database', {})
            server = server or db.get('server')
            user = db.get('user')
            pwd_b64 = db.get('password', '')
            try:
                password = base64.b64decode(pwd_b64).decode()
            except Exception:
                password = pwd_b64
        except Exception:
            pass

    # 5) Environment variables
    if not server:
        server = os.environ.get('NEXOR_DB_SERVER', r'192.168.10.66\SQLEXPRESS')
    if not user:
        user = os.environ.get('NEXOR_DB_USER', '')
    if not password:
        password = os.environ.get('NEXOR_DB_PASS', '')

    if not user or not password:
        raise ConnectionError(
            "Zirve baglantisi icin kullanici/sifre bulunamadi. "
            "Sistem > Veritabani Baglantilari ekranindan kontrol edin."
        )

    conn = pyodbc.connect(
        f'DRIVER={{{driver}}};'
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


def _musteri_email_gonder(cari_email: str, cari_adi: str, irsaliye_id: int,
                          irsaliye_no: str, evrakno: str) -> str:
    """
    Zirve aktarimi sonrasi musteriye irsaliye + kalite raporlarini email ile gonder.
    Returns: durum mesaji
    """
    try:
        from utils.email_service import get_email_service
        from utils.final_kalite_raporu_pdf import batch_final_kalite_raporu
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders
        import os

        es = get_email_service()
        if not es.ayarlar:
            return "\nEmail ayarlari yapilandirilmamis"

        # Kalite raporlarini olustur
        sonuclar = batch_final_kalite_raporu(irsaliye_id)
        rapor_pdfler = [path for lot, path in sonuclar if not str(path).startswith("HATA")]

        # Email olustur
        msg = MIMEMultipart()
        msg['From'] = f"{es.ayarlar['gonderen_adi']} <{es.ayarlar['gonderen_email']}>"
        msg['To'] = cari_email
        msg['Subject'] = f"Sevkiyat - {irsaliye_no} - ATLAS KATAFOREZ"

        body = f"""Sayin {cari_adi},

{irsaliye_no} numarali sevkiyatimiza ait kalite kontrol raporlari ekte gonderilmistir.

Zirve Evrak No: {evrakno}
Toplam Rapor: {len(rapor_pdfler)} adet

Iyi calismalar dileriz.

Saygilarimizla,
ATLAS KATAFOREZ
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Kalite raporlarini ekle
        for pdf_path in rapor_pdfler:
            try:
                with open(pdf_path, 'rb') as f:
                    part = MIMEBase('application', 'pdf')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition',
                                    f'attachment; filename="{os.path.basename(pdf_path)}"')
                    msg.attach(part)
            except Exception as ek_err:
                print(f"[Zirve] PDF ek hatasi {pdf_path}: {ek_err}")

        # SMTP ile gonder
        if es.ayarlar['smtp_ssl'] and es.ayarlar['smtp_port'] == 465:
            server = smtplib.SMTP_SSL(es.ayarlar['smtp_server'],
                                      es.ayarlar['smtp_port'], timeout=20)
        else:
            server = smtplib.SMTP(es.ayarlar['smtp_server'],
                                  es.ayarlar['smtp_port'], timeout=20)
            if es.ayarlar['smtp_ssl']:
                server.starttls()
        if es.ayarlar['gonderen_sifre']:
            server.login(es.ayarlar['gonderen_email'], es.ayarlar['gonderen_sifre'])
        server.send_message(msg)
        server.quit()

        return f"\nEmail gonderildi: {cari_email} ({len(rapor_pdfler)} rapor)"

    except Exception as e:
        return f"\nEmail hatasi: {e}"


def _sonraki_evrakno(zirve_cursor) -> str:
    """Zirve'deki son EVRAKNO'dan sonraki numarayı üret (IRO serisi)"""
    yil = datetime.now().year
    prefix = f'IRO{yil}'

    zirve_cursor.execute("""
        SELECT MAX(EVRAKNO) FROM dbo.IRSALIYE
        WHERE EVRAKNO LIKE ? AND TUR = 70
    """, (f'{prefix}%',))
    row = zirve_cursor.fetchone()
    max_evrak = row[0] if row and row[0] else None

    if max_evrak:
        numara_str = max_evrak[len(prefix):]
        try:
            son_no = int(numara_str)
        except ValueError:
            son_no = 0
        yeni_no = son_no + 1
    else:
        yeni_no = 1

    # Format: IRO + YYYY + 9 basamaklı numara = 16 karakter
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

        # 7) IRSALIYE_ALT satırları INSERT - Aynı stok kodları toplanır
        toplanan = {}
        for satir in satirlar:
            stok_kodu = satir[2] or ''
            if not stok_kodu:
                continue
            if stok_kodu in toplanan:
                toplanan[stok_kodu]['miktar'] += float(satir[1] or 0)
                if satir[0]:
                    toplanan[stok_kodu]['lot_no_list'].append(satir[0])
            else:
                toplanan[stok_kodu] = {
                    'miktar': float(satir[1] or 0),
                    'stok_kodu': stok_kodu,
                    'stok_adi': satir[3] or '',
                    'birim': satir[4] or 'ADET',
                    'lot_no_list': [satir[0]] if satir[0] else [],
                }

        for idx, (stok_kodu, data) in enumerate(toplanan.items()):
            # LOTNO max 30 karakter (Zirve siniri)
            if data['lot_no_list']:
                if len(data['lot_no_list']) == 1:
                    lot_no = str(data['lot_no_list'][0])[:30]
                else:
                    # Coklu lot: ilk lot + adet
                    ilk = str(data['lot_no_list'][0])
                    suffix = f" +{len(data['lot_no_list'])-1}"
                    lot_no = ilk[:30 - len(suffix)] + suffix
            else:
                lot_no = ''
            miktar = data['miktar']
            stok_adi = data['stok_adi']
            birim = data['birim']
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
                stok_kodu, stok_adi, miktar,
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

        # 13) Musteriye email gonder (irsaliye PDF + kalite raporlari)
        # Yetkililerden fkk_mail_alacak veya irsaliye_mail_alacak olanlari topla
        email_mesaj = ""
        try:
            nexor_cursor.execute("""
                SELECT cy.email, cy.ad_soyad
                FROM musteri.cari_yetkililer cy
                JOIN musteri.cariler c ON cy.cari_id = c.id
                WHERE c.zirve_cari_kodu = ?
                  AND cy.aktif_mi = 1
                  AND (cy.silindi_mi = 0 OR cy.silindi_mi IS NULL)
                  AND cy.email IS NOT NULL AND cy.email LIKE '%@%'
                  AND (cy.fkk_mail_alacak = 1 OR cy.irsaliye_mail_alacak = 1)
            """, (zirve_cari_kodu,))
            yetkili_emails = [(r[0].strip(), r[1] or '') for r in nexor_cursor.fetchall()]

            # Yetkili yoksa cari ana email'ine de bak
            if not yetkili_emails:
                nexor_cursor.execute("SELECT email FROM musteri.cariler WHERE zirve_cari_kodu = ?", (zirve_cari_kodu,))
                cari_row = nexor_cursor.fetchone()
                if cari_row and cari_row[0] and '@' in str(cari_row[0]):
                    yetkili_emails = [(cari_row[0].strip(), cari['unvan'])]

            if yetkili_emails:
                gonderilen = []
                for email_adr, isim in yetkili_emails:
                    sonuc = _musteri_email_gonder(
                        cari_email=email_adr,
                        cari_adi=cari['unvan'],
                        irsaliye_id=irsaliye_id,
                        irsaliye_no=irsaliye_no,
                        evrakno=evrakno,
                    )
                    if 'gonderildi' in sonuc.lower() or 'gonderildi' in sonuc:
                        gonderilen.append(email_adr)
                email_mesaj = f"\nEmail gonderildi: {len(gonderilen)} alici"
                if gonderilen:
                    email_mesaj += f"\n  " + "\n  ".join(gonderilen)
            else:
                email_mesaj = f"\nMail alacak yetkili bulunamadi ({zirve_cari_kodu})"
        except Exception as em_err:
            email_mesaj = f"\nEmail gonderim hatasi: {em_err}"
            print(f"[Zirve] Email hatasi: {em_err}")

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
                  f"Satır: {len(satirlar)} kalem{email_mesaj}"
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


# ============================================================================
# CARİ SENKRONLAMA - Zirve CARIGEN → Nexor musteri.cariler
# ============================================================================

def zirve_cari_senkronla() -> dict:
    """
    Zirve CARIGEN tablosundaki tüm carileri Nexor musteri.cariler'e senkronize eder.
    - Zirve'de olup Nexor'da olmayan: yeni kayıt (zirve_cari_kodu=CRK ile)
    - Zirve'de olup Nexor'da olan: unvan, vergi bilgileri, adres güncelle
    Returns: {'eklenen': int, 'guncellenen': int, 'toplam_zirve': int, 'hata': str|None}
    """
    sonuc = {'eklenen': 0, 'guncellenen': 0, 'toplam_zirve': 0, 'hatalar': [], 'hata': None}

    zirve_conn = None
    nexor_conn = None
    try:
        zirve_conn = _get_zirve_connection()
        zirve_cursor = zirve_conn.cursor()

        nexor_conn = get_db_connection()
        nexor_cursor = nexor_conn.cursor()

        # Zirve'den sadece müşteri/tedarikçi carilerini çek (120=müşteri, 320=tedarikçi)
        zirve_cursor.execute("""
            SELECT CRK, STA, VERGINO, VERGID, ADRES1, SEHIR, SEMT,
                   ULKE, TEL, EPOSTA, POSTAKODU
            FROM dbo.CARIGEN
            WHERE CRK IS NOT NULL AND CRK <> ''
              AND (CRK LIKE '120 %' OR CRK LIKE '320 %')
        """)
        zirve_cariler = zirve_cursor.fetchall()
        sonuc['toplam_zirve'] = len(zirve_cariler)

        # Nexor'daki mevcut zirve eşleştirmeleri
        nexor_cursor.execute("SELECT id, zirve_cari_kodu FROM musteri.cariler WHERE zirve_cari_kodu IS NOT NULL")
        mevcut = {row[1]: row[0] for row in nexor_cursor.fetchall()}

        for row in zirve_cariler:
            crk = (row[0] or '').strip()
            if not crk:
                continue

            unvan = (row[1] or '').strip()
            vergi_no = (row[2] or '').strip()
            vergi_dairesi = (row[3] or '').strip()
            adres = (row[4] or '').strip()
            sehir = (row[5] or '').strip()
            semt = (row[6] or '').strip()
            telefon = (row[8] or '').strip()
            email = (row[9] or '').strip()

            # Cari tipi: 120=müşteri, 320=tedarikçi
            cari_tipi = 'MUSTERI' if crk.startswith('120') else 'TEDARIKCI'

            try:
                if crk in mevcut:
                    # Güncelle
                    nexor_cursor.execute("""
                        UPDATE musteri.cariler SET
                            unvan = ?, vergi_no = ?, vergi_dairesi = ?,
                            adres = ?, telefon = ?, email = ?,
                            cari_tipi = ?,
                            guncelleme_tarihi = GETDATE()
                        WHERE id = ?
                    """, (unvan or None, vergi_no or None, vergi_dairesi or None,
                          adres or None, telefon or None, email or None,
                          cari_tipi, mevcut[crk]))
                    sonuc['guncellenen'] += 1
                else:
                    # Zirve CRK kodunu doğrudan cari_kodu olarak kullan
                    nexor_cursor.execute("""
                        INSERT INTO musteri.cariler
                            (cari_kodu, unvan, cari_tipi, vergi_no, vergi_dairesi,
                             adres, telefon, email, zirve_cari_kodu, aktif_mi)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """, (crk, unvan or crk, cari_tipi, vergi_no or None,
                          vergi_dairesi or None, adres or None,
                          telefon or None, email or None, crk))
                    sonuc['eklenen'] += 1

            except Exception as e:
                sonuc['hatalar'].append(f"{crk}: {str(e)}")

        nexor_conn.commit()

    except Exception as e:
        sonuc['hata'] = str(e)
    finally:
        if zirve_conn:
            try: zirve_conn.close()
            except Exception: pass
        if nexor_conn:
            try: nexor_conn.close()
            except Exception: pass

    return sonuc


# ============================================================================
# STOK SENKRONLAMA - Zirve STOKGEN → Nexor stok.urunler
# Kural: Mevcut urunlerde sadece fiyat guncellenir, ad/kod/birim dokunulmaz
# ============================================================================

def zirve_stok_senkronla(sadece_yeni=False):
    """
    Zirve STOKGEN tablosundan stok kartlarini senkronize eder.

    Kurallar:
        - NEXOR'da OLMAYAN urunler: STK, STA, birim, fiyat ile yeni eklenir
        - NEXOR'da OLAN urunler: Sadece alis fiyati (ALIS1_1) ve satis fiyati (SAT1_1) guncellenir
        - Urun adi, kodu, birimi, tipi ASLA degistirilmez (kullanici duzeltmeleri korunur)

    Args:
        sadece_yeni: True ise sadece yeni urunleri ekler, mevcutlari guncellemez

    Returns:
        dict: {'eklenen': int, 'fiyat_guncellenen': int, 'toplam_zirve': int, 'hata': str}
    """
    sonuc = {'eklenen': 0, 'fiyat_guncellenen': 0, 'toplam_zirve': 0, 'hata': None}
    zirve_conn = None
    nexor_conn = None

    try:
        zirve_conn = _get_zirve_connection()
        nexor_conn = get_db_connection()
        z_cursor = zirve_conn.cursor()
        n_cursor = nexor_conn.cursor()

        # Zirve'den stok kartlarini cek
        z_cursor.execute("""
            SELECT STK, STA, BBIRIM, ALIS1_1, SAT1_1, KDV,
                   OZELKOD1, OZELKOD2, GRUP1, ASSTOK, AZSTOK, ACIKLAMA
            FROM STOKGEN
            WHERE STK IS NOT NULL AND LTRIM(RTRIM(STK)) <> ''
            ORDER BY STK
        """)
        zirve_stoklar = z_cursor.fetchall()
        sonuc['toplam_zirve'] = len(zirve_stoklar)

        # NEXOR'daki mevcut urun kodlarini ve id'lerini al
        n_cursor.execute("SELECT id, urun_kodu FROM stok.urunler WHERE aktif_mi = 1")
        nexor_map = {}
        for r in n_cursor.fetchall():
            if r[1]:
                nexor_map[r[1].strip()] = r[0]

        for zs in zirve_stoklar:
            stk = (zs[0] or '').strip()
            sta = (zs[1] or '').strip()
            birim = (zs[2] or 'ADET').strip() or 'ADET'
            alis_fiyat = float(zs[3] or 0)
            satis_fiyat = float(zs[4] or 0)
            kdv = float(zs[5] or 0)
            ozelkod1 = (zs[6] or '').strip()
            ozelkod2 = (zs[7] or '').strip()
            grup = (zs[8] or '').strip()
            min_stok = float(zs[9] or 0)
            max_stok = float(zs[10] or 0)
            aciklama = (zs[11] or '').strip()

            if not stk or not sta:
                continue

            if stk in nexor_map:
                # MEVCUT - Sadece fiyat guncelle (kullanici duzeltmeleri korunur)
                if not sadece_yeni and (alis_fiyat > 0 or satis_fiyat > 0):
                    urun_id = nexor_map[stk]
                    n_cursor.execute("""
                        UPDATE stok.urunler SET
                            zirve_alis_fiyat = ?,
                            zirve_satis_fiyat = ?,
                            zirve_son_senkron = GETDATE()
                        WHERE id = ? AND aktif_mi = 1
                    """, (alis_fiyat, satis_fiyat, urun_id))
                    if n_cursor.rowcount > 0:
                        sonuc['fiyat_guncellenen'] += 1
            else:
                # YENI - Ekle
                # Birim eslestirme
                birim_map = {'KG': 2, 'GR': 3, 'TON': 4, 'LT': 5, 'ML': 6,
                             'M3': 7, 'M2': 8, 'M': 11, 'CM': 12, 'MM': 13,
                             'ADET': 1, 'AD': 1, 'PAKET': 1, 'KUTU': 1}
                birim_id = birim_map.get(birim.upper(), 1)

                try:
                    n_cursor.execute("""
                        INSERT INTO stok.urunler
                            (urun_kodu, urun_adi, urun_tipi, birim_id, aktif_mi,
                             zirve_alis_fiyat, zirve_satis_fiyat, zirve_son_senkron,
                             min_stok, max_stok, notlar)
                        VALUES (?, ?, 'HAMMADDE', ?, 1, ?, ?, GETDATE(), ?, ?, ?)
                    """, (stk[:50], sta[:250], birim_id, alis_fiyat, satis_fiyat,
                          min_stok if min_stok else None,
                          max_stok if max_stok else None,
                          aciklama[:500] if aciklama else None))
                    sonuc['eklenen'] += 1
                except Exception:
                    pass  # Constraint hatasi - atla

        nexor_conn.commit()
        # MetaData2025'ten tedarikci eslesmesi (stok kodu + urun adi ile)
        tedarikci_eslesen = 0
        try:
            z_cursor.execute("""
                SELECT StokKodu, StokAdi, HesapKoduTD, UnvaniTD, AlisTutari
                FROM MetaData2025.dbo.StokGenelTedarikci
                WHERE HesapKoduTD IS NOT NULL AND HesapKoduTD <> ''
            """)
            td_rows = z_cursor.fetchall()

            # NEXOR urun adi -> id map (ad ile eslestirme icin)
            n_cursor.execute("SELECT id, urun_kodu, UPPER(LTRIM(RTRIM(urun_adi))) FROM stok.urunler WHERE aktif_mi = 1")
            nexor_ad_map = {}
            for r in n_cursor.fetchall():
                if r[2]:
                    nexor_ad_map[r[2]] = r[0]

            # Tedarikci CRK -> id cache
            tedarikci_cache = {}

            for td in td_rows:
                stk_kodu = (td[0] or '').strip()
                stk_adi = (td[1] or '').strip()
                crk = (td[2] or '').strip()
                alis = float(td[4] or 0)

                if not crk:
                    continue

                # NEXOR'da urun bul: once kod, sonra tam ad, sonra icerik eslesmesi
                urun_id = nexor_map.get(stk_kodu)
                if not urun_id and stk_adi:
                    urun_id = nexor_ad_map.get(stk_adi.upper())
                if not urun_id and stk_adi:
                    # Icerik eslesmesi: NEXOR adi MetaData adini iceriyor mu veya tersi
                    aranan = stk_adi.upper().strip()
                    for nexor_ad, nid in nexor_ad_map.items():
                        if aranan in nexor_ad or nexor_ad in aranan:
                            urun_id = nid
                            break

                if not urun_id:
                    continue

                # Tedarikci bul (cache)
                if crk not in tedarikci_cache:
                    n_cursor.execute("""
                        SELECT id FROM musteri.cariler
                        WHERE zirve_cari_kodu = ? AND aktif_mi = 1
                    """, (crk,))
                    cari_row = n_cursor.fetchone()
                    tedarikci_cache[crk] = cari_row[0] if cari_row else None

                tedarikci_id = tedarikci_cache.get(crk)
                if not tedarikci_id:
                    continue

                # Guncelle (mevcut cari_id'yi bozma)
                n_cursor.execute("""
                    UPDATE stok.urunler SET
                        cari_id = ISNULL(cari_id, ?),
                        zirve_alis_fiyat = CASE WHEN ? > 0 THEN ? ELSE zirve_alis_fiyat END,
                        zirve_son_senkron = GETDATE()
                    WHERE id = ?
                """, (tedarikci_id, alis, alis, urun_id))
                if n_cursor.rowcount > 0:
                    tedarikci_eslesen += 1

            nexor_conn.commit()
        except Exception as e:
            print(f"[WARN] Tedarikci eslestirme hatasi: {e}")

        sonuc['tedarikci_eslesen'] = tedarikci_eslesen
        print(f"[INFO] Stok senkron: {sonuc['eklenen']} eklendi, "
              f"{sonuc['fiyat_guncellenen']} fiyat guncellendi, "
              f"{tedarikci_eslesen} tedarikci eslesti, "
              f"Zirve toplam: {sonuc['toplam_zirve']}")

    except Exception as e:
        sonuc['hata'] = str(e)
        print(f"[ERROR] Stok senkron hatasi: {e}")
    finally:
        if zirve_conn:
            try: zirve_conn.close()
            except Exception: pass
        if nexor_conn:
            try: nexor_conn.close()
            except Exception: pass

    return sonuc


# ============================================================================
# NEXOR -> ZIRVE STOK AKTARIMI (tekil kart, butondan tetiklenir)
# Guvenlik: sifre kontrolu + template-based INSERT + duplicate link
# ============================================================================

def _ensure_zirve_stk_kolonu(nexor_cursor):
    """stok.urunler.zirve_stk kolonu yoksa ekle (runtime guard)."""
    try:
        nexor_cursor.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA='stok' AND TABLE_NAME='urunler' AND COLUMN_NAME='zirve_stk'
            )
            BEGIN
                ALTER TABLE stok.urunler ADD zirve_stk NVARCHAR(50) NULL;
            END
        """)
    except Exception:
        pass


def stok_aktar(urun_id: int, sifre: str = "") -> ZirveAktarimSonuc:
    """
    Nexor urununu Zirve STOKGEN tablosuna aktarir.

    Guvenlik:
        - ZIRVE_AKTARIM_SIFRESI ile eslesmezse hic bir islem yapmaz
        - Nexor'da zirve_stk dolu ise tekrar aktarmaz
        - Zirve'de ayni STK zaten varsa yeni kayit acmaz, sadece baglar

    Strateji:
        - Zirve'de en son eklenen bir stok karti TEMPLATE olarak okunur
        - Tum kolonlar kopyalanir, SADECE kritik alanlar Nexor verisiyle override edilir
        - Bu sayede NOT NULL / defaults / muhasebe kolonlari korunur

    Args:
        urun_id: stok.urunler.id
        sifre: Kullanici tarafindan girilen aktarim sifresi

    Returns:
        ZirveAktarimSonuc
    """
    # 1) Sifre kontrolu
    if not sifre or sifre != ZIRVE_AKTARIM_SIFRESI:
        return ZirveAktarimSonuc(
            basarili=False,
            hata="Yanlis aktarim sifresi! Islem iptal edildi."
        )

    nexor_conn = None
    zirve_conn = None
    try:
        # 2) Nexor urun verisi
        nexor_conn = get_db_connection()
        nc = nexor_conn.cursor()
        _ensure_zirve_stk_kolonu(nc)

        nc.execute("""
            SELECT u.urun_kodu, u.urun_adi, b.kod AS birim_kod,
                   u.zirve_alis_fiyat, u.zirve_satis_fiyat,
                   u.notlar, u.zirve_stk,
                   u.urun_tipi
            FROM stok.urunler u
            LEFT JOIN tanim.birimler b ON u.birim_id = b.id
            WHERE u.id = ?
        """, (urun_id,))
        row = nc.fetchone()
        if not row:
            return ZirveAktarimSonuc(basarili=False, hata="Nexor'da urun bulunamadi!")

        urun_kodu = (row[0] or '').strip()
        urun_adi = (row[1] or '').strip()
        birim_kod = (row[2] or 'AD').strip() or 'AD'
        alis_fiyat = float(row[3] or 0)
        satis_fiyat = float(row[4] or 0)
        notlar = (row[5] or '').strip()
        mevcut_zirve_stk = row[6]
        urun_tipi = (row[7] or '').strip()

        if not urun_kodu:
            return ZirveAktarimSonuc(basarili=False, hata="Urun kodu bos olamaz!")

        if mevcut_zirve_stk:
            return ZirveAktarimSonuc(
                basarili=False,
                hata=f"Bu urun zaten Zirve'ye aktarilmis!\n\n"
                     f"Zirve STK: {mevcut_zirve_stk}\n"
                     f"Tekrar aktarim istiyorsaniz once Zirve baglantisini kaldirin."
            )

        # 3) Zirve baglanti
        zirve_conn = _get_zirve_connection()
        zc = zirve_conn.cursor()

        # 4) Zirve'de bu STK zaten var mi?
        zc.execute("SELECT TOP 1 STK, STA, REF FROM dbo.STOKGEN WHERE STK = ?", (urun_kodu,))
        mevcut = zc.fetchone()
        if mevcut:
            # Link et (yeni kart acmadan)
            nc.execute("UPDATE stok.urunler SET zirve_stk = ? WHERE id = ?",
                       (mevcut[0], urun_id))
            try:
                nc.execute("""
                    INSERT INTO entegrasyon.zirve_senkron_log
                    (islem_tipi, yonu, referans_tablo, referans_id, zirve_id, durum, request_data)
                    VALUES ('STOK', 'NEXOR_ZIRVE', 'stok.urunler', ?, ?, 'BASARILI',
                            ?)
                """, (urun_id, str(mevcut[2]),
                      f"LINKED STK:{mevcut[0]} (Zirve'de zaten vardi)"))
            except Exception:
                pass
            nexor_conn.commit()
            return ZirveAktarimSonuc(
                basarili=True,
                zirve_sirano=int(mevcut[2]) if mevcut[2] else None,
                zirve_evrakno=mevcut[0],
                mesaj=f"Zirve'de ayni STK kodu zaten vardi.\n"
                      f"Yeni kart acilmadi, mevcut karta baglandi.\n\n"
                      f"STK: {mevcut[0]}\nSTA: {mevcut[1]}"
            )

        # 5) Template: Zirve'de en son eklenen uygun bir stok karti
        zc.execute("""
            SELECT TOP 1 * FROM dbo.STOKGEN
            WHERE STK IS NOT NULL AND LTRIM(RTRIM(STK)) <> ''
            ORDER BY REF DESC
        """)
        template_row = zc.fetchone()
        if not template_row:
            return ZirveAktarimSonuc(
                basarili=False,
                hata="Zirve STOKGEN tablosunda template olarak kullanilacak kart yok!"
            )

        cols = [d[0] for d in zc.description]

        # 6) Override edilecek alanlar (NEXOR verisi)
        import uuid as _uuid
        yeni_p_id = str(_uuid.uuid4()).upper()

        overrides = {
            'STK': urun_kodu[:50],
            'STA': (urun_adi or urun_kodu)[:250],
            'P_ID': yeni_p_id,
            'BBIRIM': birim_kod[:10],
            'ALIS1_1': alis_fiyat,
            'SAT1_1': satis_fiyat,
            'ACIKLAMA': (notlar or '')[:250],
            'KULLANICI': ZIRVE_KULLANICI,
        }
        # Tarih kolonlari varsa bugune cek
        now = datetime.now()
        for tarih_kol in ('TARIH', 'KAYITTARIHI', 'KAYIT_TARIHI', 'OLUSTURMATARIHI',
                          'DEGISTIRMETARIHI', 'ILKKAYITTARIHI'):
            overrides[tarih_kol] = now

        # 6b) Identity / computed / timestamp (rowversion) kolonlarini tespit et
        # Bu tipler INSERT'e dahil edilemez
        skip_cols = {'REF'}  # REF IDENTITY (yedek)
        try:
            zc.execute("""
                SELECT c.name, c.is_identity, c.is_computed, t.name AS type_name
                FROM sys.columns c
                JOIN sys.types t ON c.user_type_id = t.user_type_id
                WHERE c.object_id = OBJECT_ID('dbo.STOKGEN')
            """)
            for meta_row in zc.fetchall():
                col_name, is_ident, is_comp, type_name = meta_row
                if is_ident or is_comp or (type_name or '').lower() in ('timestamp', 'rowversion'):
                    skip_cols.add(col_name.upper())
        except Exception as meta_err:
            print(f"[Zirve] STOKGEN metadata okuma uyarisi: {meta_err}")

        # 7) INSERT SQL'i olustur
        insert_cols = []
        insert_vals = []
        for i, col in enumerate(cols):
            if col.upper() in skip_cols:
                continue
            insert_cols.append(f'[{col}]')
            key = col.upper()
            if key in overrides:
                insert_vals.append(overrides[key])
            else:
                insert_vals.append(template_row[i])

        placeholders = ','.join(['?'] * len(insert_cols))
        col_sql = ','.join(insert_cols)
        sql = f"INSERT INTO dbo.STOKGEN ({col_sql}) VALUES ({placeholders})"

        zc.execute(sql, insert_vals)

        zc.execute("SELECT IDENT_CURRENT('dbo.STOKGEN')")
        yeni_ref = int(zc.fetchone()[0])

        zirve_conn.commit()

        # 8) Nexor tarafina baglantiyi yaz + log
        nc.execute("UPDATE stok.urunler SET zirve_stk = ? WHERE id = ?",
                   (urun_kodu, urun_id))
        try:
            nc.execute("""
                INSERT INTO entegrasyon.zirve_senkron_log
                (islem_tipi, yonu, referans_tablo, referans_id, zirve_id, durum, request_data)
                VALUES ('STOK', 'NEXOR_ZIRVE', 'stok.urunler', ?, ?, 'BASARILI', ?)
            """, (urun_id, str(yeni_ref),
                  f"STK:{urun_kodu}, REF:{yeni_ref}, STA:{urun_adi}, "
                  f"TIP:{urun_tipi}, BIRIM:{birim_kod}"))
        except Exception:
            pass
        nexor_conn.commit()

        return ZirveAktarimSonuc(
            basarili=True,
            zirve_sirano=yeni_ref,
            zirve_evrakno=urun_kodu,
            zirve_pid=yeni_p_id,
            mesaj=f"Stok karti Zirve'ye aktarildi!\n\n"
                  f"STK : {urun_kodu}\n"
                  f"STA : {urun_adi}\n"
                  f"REF : {yeni_ref}\n"
                  f"Birim: {birim_kod}\n"
                  f"Alis : {alis_fiyat:,.2f}\n"
                  f"Satis: {satis_fiyat:,.2f}"
        )

    except Exception as e:
        # Hata logla
        try:
            if nexor_conn:
                log_cur = nexor_conn.cursor()
                log_cur.execute("""
                    INSERT INTO entegrasyon.zirve_senkron_log
                    (islem_tipi, yonu, referans_tablo, referans_id, durum, hata_mesaji)
                    VALUES ('STOK', 'NEXOR_ZIRVE', 'stok.urunler', ?, 'HATA', ?)
                """, (urun_id, str(e)[:500]))
                nexor_conn.commit()
        except Exception:
            pass
        import traceback
        traceback.print_exc()
        return ZirveAktarimSonuc(basarili=False, hata=str(e))
    finally:
        if zirve_conn:
            try: zirve_conn.close()
            except Exception: pass
        if nexor_conn:
            try: nexor_conn.close()
            except Exception: pass


def stok_aktarim_kontrol(urun_id: int) -> dict:
    """Bir urunun Zirve aktarim durumunu dondurur."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        _ensure_zirve_stk_kolonu(cur)
        cur.execute("SELECT zirve_stk FROM stok.urunler WHERE id = ?", (urun_id,))
        row = cur.fetchone()
        zirve_stk = row[0] if row else None
        conn.close()
        return {
            'aktarildi': bool(zirve_stk),
            'zirve_stk': zirve_stk
        }
    except Exception:
        return {'aktarildi': False, 'zirve_stk': None}
