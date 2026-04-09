# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Bildirim Tetikleyici
Modullerden otomatik bildirim olusturma fonksiyonlari

Bu dosya, modullerdeki islemler sonrasi otomatik bildirim
uretmek icin yardimci fonksiyonlar icerir.

Kullanim:
    from core.bildirim_tetikleyici import BildirimTetikleyici

    # Is emri olusturuldu
    BildirimTetikleyici.is_emri_olusturuldu(ie_id, ie_no, musteri_adi, sorumlu_id)

    # Uygunsuzluk acildi
    BildirimTetikleyici.uygunsuzluk_acildi(kayit_no, urun_adi, sorumlu_id)

    # Aksiyon atandi
    BildirimTetikleyici.aksiyon_atandi(aksiyon_no, baslik, hedef_tarih, sorumlu_kullanici_id)
"""

from typing import Optional
from core.bildirim_service import BildirimService
from core.database import execute_query, get_db_connection


class BildirimTetikleyici:
    """Modüllerden otomatik bildirim oluşturma"""

    # =========================================================================
    # IS EMIRLERI
    # =========================================================================

    @staticmethod
    def is_emri_olusturuldu(
        ie_id: int,
        ie_no: str,
        musteri_adi: str = '',
        sorumlu_kullanici_id: int = None,
        uretim_rol_id: int = None,
    ):
        """Yeni is emri olusturuldu bildirimi"""
        BildirimService.sablon_gonder(
            kod='IE_YENI',
            hedef_kullanici_id=sorumlu_kullanici_id,
            hedef_rol_id=uretim_rol_id,
            parametreler={
                'is_emri_no': ie_no,
                'musteri_adi': musteri_adi,
            },
            kaynak_tablo='siparis.is_emirleri',
            kaynak_id=ie_id,
        )

    @staticmethod
    def is_emri_termin_yaklasti(
        ie_id: int,
        ie_no: str,
        termin_tarih: str,
        sorumlu_kullanici_id: int = None,
    ):
        """Is emri termin tarihi yaklasti (3 gun icinde)"""
        BildirimService.sablon_gonder(
            kod='IE_TERMIN_YAKIN',
            hedef_kullanici_id=sorumlu_kullanici_id,
            parametreler={
                'is_emri_no': ie_no,
                'termin_tarih': termin_tarih,
            },
            kaynak_tablo='siparis.is_emirleri',
            kaynak_id=ie_id,
        )

    @staticmethod
    def is_emri_termin_gecti(
        ie_id: int,
        ie_no: str,
        termin_tarih: str,
        sorumlu_kullanici_id: int = None,
    ):
        """Is emri termin tarihi gecti"""
        BildirimService.sablon_gonder(
            kod='IE_TERMIN_GECTI',
            hedef_kullanici_id=sorumlu_kullanici_id,
            parametreler={
                'is_emri_no': ie_no,
                'termin_tarih': termin_tarih,
            },
            kaynak_tablo='siparis.is_emirleri',
            kaynak_id=ie_id,
        )

    # =========================================================================
    # KALITE
    # =========================================================================

    @staticmethod
    def uygunsuzluk_acildi(
        kayit_id: int,
        kayit_no: str,
        urun_adi: str = '',
        sorumlu_kullanici_id: int = None,
        kalite_rol_id: int = None,
    ):
        """Yeni uygunsuzluk kaydi acildi"""
        BildirimService.sablon_gonder(
            kod='KALITE_UYGUNSUZLUK',
            hedef_kullanici_id=sorumlu_kullanici_id,
            hedef_rol_id=kalite_rol_id,
            parametreler={
                'kayit_no': kayit_no,
                'urun_adi': urun_adi,
            },
            kaynak_tablo='kalite.uygunsuzluklar',
            kaynak_id=kayit_id,
        )

    @staticmethod
    def kalibrasyon_yaklasti(
        cihaz_id: int,
        cihaz_adi: str,
        tarih: str,
        kalite_rol_id: int = None,
    ):
        """Kalibrasyon suresi yaklasti"""
        BildirimService.sablon_gonder(
            kod='KALITE_KALIBRASYON',
            hedef_rol_id=kalite_rol_id,
            parametreler={
                'cihaz_adi': cihaz_adi,
                'tarih': tarih,
            },
            kaynak_tablo='kalite.kalibrasyon_planlari',
            kaynak_id=cihaz_id,
        )

    # =========================================================================
    # BAKIM
    # =========================================================================

    @staticmethod
    def ariza_bildirildi(
        ariza_id: int,
        ekipman_adi: str,
        ariza_aciklama: str = '',
        bakim_rol_id: int = None,
    ):
        """Yeni ariza kaydedildi"""
        BildirimService.sablon_gonder(
            kod='BAKIM_ARIZA',
            hedef_rol_id=bakim_rol_id,
            parametreler={
                'ekipman_adi': ekipman_adi,
                'ariza_aciklama': ariza_aciklama[:100] if ariza_aciklama else '',
            },
            kaynak_tablo='bakim.ariza_bildirimleri',
            kaynak_id=ariza_id,
        )

    @staticmethod
    def bakim_zamani_geldi(
        plan_id: int,
        ekipman_adi: str,
        plan_adi: str = '',
        bakim_rol_id: int = None,
    ):
        """Periyodik bakim zamani geldi"""
        BildirimService.sablon_gonder(
            kod='BAKIM_PLAN',
            hedef_rol_id=bakim_rol_id,
            parametreler={
                'ekipman_adi': ekipman_adi,
                'plan_adi': plan_adi,
            },
            kaynak_tablo='bakim.periyodik_bakim_planlari',
            kaynak_id=plan_id,
        )

    # =========================================================================
    # STOK
    # =========================================================================

    @staticmethod
    def stok_minimum_alti(
        urun_id: int,
        urun_adi: str,
        mevcut_stok: str,
        min_stok: str,
        depo_rol_id: int = None,
        satinalma_rol_id: int = None,
    ):
        """Stok minimum seviye altina dustu"""
        params = {
            'urun_adi': urun_adi,
            'mevcut_stok': mevcut_stok,
            'min_stok': min_stok,
        }

        # Depo ekibine gonder
        if depo_rol_id:
            BildirimService.sablon_gonder(
                kod='STOK_MINIMUM',
                hedef_rol_id=depo_rol_id,
                parametreler=params,
                kaynak_tablo='stok.urunler',
                kaynak_id=urun_id,
            )

        # Satinalma ekibine gonder
        if satinalma_rol_id:
            BildirimService.sablon_gonder(
                kod='STOK_MINIMUM',
                hedef_rol_id=satinalma_rol_id,
                parametreler=params,
                kaynak_tablo='stok.urunler',
                kaynak_id=urun_id,
            )

    # =========================================================================
    # SEVKIYAT
    # =========================================================================

    @staticmethod
    def sevkiyat_planlandi(
        sevk_id: int,
        musteri_adi: str,
        sevk_tarih: str,
        sevkiyat_rol_id: int = None,
    ):
        """Yeni sevkiyat planlandi"""
        BildirimService.sablon_gonder(
            kod='SEVKIYAT_PLAN',
            hedef_rol_id=sevkiyat_rol_id,
            parametreler={
                'musteri_adi': musteri_adi,
                'sevk_tarih': sevk_tarih,
            },
            kaynak_tablo='siparis.sevkiyatlar',
            kaynak_id=sevk_id,
        )

    # =========================================================================
    # ISG
    # =========================================================================

    @staticmethod
    def isg_olay_kaydedildi(
        olay_id: int,
        olay_aciklama: str,
        bolum: str = '',
        isg_rol_id: int = None,
        yonetici_ids: list = None,
    ):
        """Is guvenligi olayi kaydedildi"""
        params = {
            'olay_aciklama': olay_aciklama[:100] if olay_aciklama else '',
            'bolum': bolum,
        }

        BildirimService.sablon_gonder(
            kod='ISG_OLAY',
            hedef_rol_id=isg_rol_id,
            parametreler=params,
            kaynak_tablo='isg.olay_kayitlari',
            kaynak_id=olay_id,
        )

        # Yoneticilere de gonder
        if yonetici_ids:
            BildirimService.toplu_gonder(
                kullanici_idler=yonetici_ids,
                baslik='ISG Olayi Kaydedildi',
                mesaj=f'Is guvenligi olayi: {olay_aciklama[:100]}. Bolum: {bolum}',
                modul='ISG',
                onem='KRITIK',
                tip='UYARI',
                kaynak_tablo='isg.olay_kayitlari',
                kaynak_id=olay_id,
                sayfa_yonlendirme='isg_olay_kayitlari',
            )

    # =========================================================================
    # LABORATUVAR
    # =========================================================================

    @staticmethod
    def lab_analiz_hatali(
        analiz_id: int,
        banyo_adi: str,
        durum: str = 'UYARI',
        detay: str = '',
        lab_rol_id: int = None,
        uretim_rol_id: int = None,
    ):
        """Lab analiz sonucu limit disi cikti - tum abonelere bildirim gonder"""
        onem = 'KRITIK' if durum == 'KRITIK' else 'YUKSEK'
        baslik = f'Lab Analiz {durum}: {banyo_adi}'
        mesaj = f'{banyo_adi} banyo analiz sonucu {durum}. {detay}'

        # Tum aktif kullanicilara gonder (kanal karari kullanici bazli yapilacak)
        try:
            kullanicilar = execute_query(
                "SELECT id FROM sistem.kullanicilar WHERE aktif_mi = 1 AND silindi_mi = 0"
            )
            for k in kullanicilar:
                BildirimService.gonder(
                    kullanici_id=k['id'],
                    baslik=baslik,
                    mesaj=mesaj,
                    modul='LAB',
                    onem=onem,
                    tip='UYARI',
                    kaynak_tablo='uretim.banyo_analiz_sonuclari',
                    kaynak_id=analiz_id,
                    sayfa_yonlendirme='lab_analiz',
                    bildirim_tanim_kod='LAB_ANALIZ_HATALI',
                )
        except Exception as e:
            print(f"[BildirimTetikleyici] Lab bildirim hatasi: {e}")

    # =========================================================================
    # AKSIYONLAR
    # =========================================================================

    @staticmethod
    def aksiyon_atandi(
        aksiyon_id: int,
        aksiyon_no: str,
        baslik: str,
        hedef_tarih: str,
        sorumlu_kullanici_id: int = None,
    ):
        """Yeni aksiyon atandi"""
        if not sorumlu_kullanici_id:
            return

        BildirimService.sablon_gonder(
            kod='AKSIYON_ATANDI',
            hedef_kullanici_id=sorumlu_kullanici_id,
            parametreler={
                'aksiyon_no': aksiyon_no,
                'baslik': baslik,
                'hedef_tarih': hedef_tarih or 'Belirtilmedi',
            },
            kaynak_tablo='sistem.aksiyonlar',
            kaynak_id=aksiyon_id,
        )

    @staticmethod
    def aksiyon_hedef_yaklasti(
        aksiyon_id: int,
        aksiyon_no: str,
        hedef_tarih: str,
        sorumlu_kullanici_id: int = None,
    ):
        """Aksiyon hedef tarihi yaklasti"""
        BildirimService.sablon_gonder(
            kod='AKSIYON_HEDEF_YAKIN',
            hedef_kullanici_id=sorumlu_kullanici_id,
            parametreler={
                'aksiyon_no': aksiyon_no,
                'hedef_tarih': hedef_tarih,
            },
            kaynak_tablo='sistem.aksiyonlar',
            kaynak_id=aksiyon_id,
        )

    @staticmethod
    def aksiyon_gecikti(
        aksiyon_id: int,
        aksiyon_no: str,
        hedef_tarih: str,
        sorumlu_kullanici_id: int = None,
    ):
        """Aksiyon hedef tarihi gecti"""
        BildirimService.sablon_gonder(
            kod='AKSIYON_GECIKTI',
            hedef_kullanici_id=sorumlu_kullanici_id,
            parametreler={
                'aksiyon_no': aksiyon_no,
                'hedef_tarih': hedef_tarih,
            },
            kaynak_tablo='sistem.aksiyonlar',
            kaynak_id=aksiyon_id,
        )

    # =========================================================================
    # GENEL
    # =========================================================================

    @staticmethod
    def onay_bekliyor(
        onaylayici_id: int,
        kayit_tipi: str,
        kayit_aciklama: str,
        kaynak_tablo: str = None,
        kaynak_id: int = None,
        sayfa_yonlendirme: str = None,
    ):
        """Onay bekleyen kayit bildirimi"""
        BildirimService.sablon_gonder(
            kod='ONAY_BEKLIYOR',
            hedef_kullanici_id=onaylayici_id,
            parametreler={
                'kayit_tipi': kayit_tipi,
                'kayit_aciklama': kayit_aciklama,
            },
            kaynak_tablo=kaynak_tablo,
            kaynak_id=kaynak_id,
        )

    @staticmethod
    def sistem_duyurusu(mesaj: str, onem: str = 'NORMAL'):
        """Tum kullanicilara sistem duyurusu"""
        BildirimService.herkese_gonder(
            baslik='Sistem Duyurusu',
            mesaj=mesaj,
            modul='SISTEM',
            onem=onem,
            tip='BILGI',
        )

    # =========================================================================
    # ZAMANLANMIS KONTROLLER (Timer ile cagrilabilir)
    # =========================================================================

    @staticmethod
    def zamanlanmis_kontrol():
        """
        Periyodik olarak cagrilmasi gereken kontroller.
        Termin, kalibrasyon, aksiyon hedef tarihi vb.
        MainWindow'dan QTimer ile 1 saatte bir cagrilabilir.
        """
        try:
            BildirimTetikleyici._kontrol_ie_terminler()
            BildirimTetikleyici._kontrol_aksiyon_hedefler()
            BildirimTetikleyici._kontrol_kalibrasyonlar()
            BildirimTetikleyici._kalibrasyon_toplu_uyari()
            print("[BildirimTetikleyici] Zamanlanmis kontrol tamamlandi")
        except Exception as e:
            print(f"[BildirimTetikleyici] Zamanlanmis kontrol hatasi: {e}")

    @staticmethod
    def _kontrol_ie_terminler():
        """3 gun icinde termin dolacak is emirlerini kontrol et"""
        try:
            rows = execute_query("""
                SELECT ie.id, ie.is_emri_no,
                       FORMAT(ie.termin_tarihi, 'dd.MM.yyyy') AS termin_tarih,
                       ie.olusturan_id
                FROM siparis.is_emirleri ie
                WHERE ie.termin_tarihi BETWEEN CAST(GETDATE() AS DATE)
                      AND DATEADD(day, 3, CAST(GETDATE() AS DATE))
                  AND ie.durum NOT IN ('TAMAMLANDI', 'IPTAL')
                  AND NOT EXISTS (
                      SELECT 1 FROM sistem.bildirimler b
                      WHERE b.kaynak_tablo = 'siparis.is_emirleri'
                        AND b.kaynak_id = ie.id
                        AND b.tip = 'UYARI'
                        AND b.olusturma_tarihi > DATEADD(day, -1, GETDATE())
                  )
            """)
            for row in rows:
                BildirimTetikleyici.is_emri_termin_yaklasti(
                    ie_id=row['id'],
                    ie_no=row['is_emri_no'],
                    termin_tarih=row['termin_tarih'],
                    sorumlu_kullanici_id=row.get('olusturan_id'),
                )
        except Exception as e:
            print(f"[BildirimTetikleyici] IE termin kontrol hatasi: {e}")

    @staticmethod
    def _kontrol_aksiyon_hedefler():
        """3 gun icinde hedef tarihi dolacak aksiyonlari kontrol et"""
        try:
            rows = execute_query("""
                SELECT a.id, a.aksiyon_no,
                       FORMAT(a.hedef_tarih, 'dd.MM.yyyy') AS hedef_tarih,
                       k.id AS kullanici_id
                FROM sistem.aksiyonlar a
                LEFT JOIN ik.personeller p ON p.id = a.sorumlu_id
                LEFT JOIN sistem.kullanicilar k ON k.personel_id = p.id
                WHERE a.hedef_tarih BETWEEN CAST(GETDATE() AS DATE)
                      AND DATEADD(day, 3, CAST(GETDATE() AS DATE))
                  AND a.durum IN ('BEKLIYOR', 'DEVAM_EDIYOR')
                  AND a.aktif_mi = 1 AND a.silindi_mi = 0
                  AND NOT EXISTS (
                      SELECT 1 FROM sistem.bildirimler b
                      WHERE b.kaynak_tablo = 'sistem.aksiyonlar'
                        AND b.kaynak_id = a.id
                        AND b.tip = 'HATIRLATMA'
                        AND b.olusturma_tarihi > DATEADD(day, -1, GETDATE())
                  )
            """)
            for row in rows:
                if row.get('kullanici_id'):
                    BildirimTetikleyici.aksiyon_hedef_yaklasti(
                        aksiyon_id=row['id'],
                        aksiyon_no=row['aksiyon_no'],
                        hedef_tarih=row['hedef_tarih'],
                        sorumlu_kullanici_id=row['kullanici_id'],
                    )
        except Exception as e:
            print(f"[BildirimTetikleyici] Aksiyon hedef kontrol hatasi: {e}")

    @staticmethod
    def _kontrol_kalibrasyonlar():
        """7 gun icinde kalibrasyonu dolacak cihazlari kontrol et"""
        try:
            rows = execute_query("""
                SELECT kp.id, ISNULL(oc.cihaz_adi, CONCAT('Cihaz #', kp.cihaz_id)) AS cihaz_adi,
                       FORMAT(kp.sonraki_kalibrasyon_tarihi, 'dd.MM.yyyy') AS tarih
                FROM kalite.kalibrasyon_planlari kp
                LEFT JOIN kalite.olcum_cihazlari oc ON kp.cihaz_id = oc.id
                WHERE kp.sonraki_kalibrasyon_tarihi BETWEEN CAST(GETDATE() AS DATE)
                      AND DATEADD(day, 7, CAST(GETDATE() AS DATE))
                  AND kp.aktif_mi = 1
                  AND NOT EXISTS (
                      SELECT 1 FROM sistem.bildirimler b
                      WHERE b.kaynak_tablo = 'kalite.kalibrasyon_planlari'
                        AND b.kaynak_id = kp.id
                        AND b.olusturma_tarihi > DATEADD(day, -3, GETDATE())
                  )
            """)
            for row in rows:
                BildirimTetikleyici.kalibrasyon_yaklasti(
                    cihaz_id=row['id'],
                    cihaz_adi=row.get('cihaz_adi', ''),
                    tarih=row.get('tarih', ''),
                )
        except Exception as e:
            print(f"[BildirimTetikleyici] Kalibrasyon kontrol hatasi: {e}")

    @staticmethod
    def _kalibrasyon_toplu_uyari():
        """Suresi gecmis + 30 gun icinde dolacak kalibrasyonlari WhatsApp ve E-mail ile gonder"""
        try:
            # Son 24 saat icinde bu uyari gonderilmis mi kontrol et
            check = execute_query("""
                SELECT 1 FROM sistem.bildirimler
                WHERE kaynak_tablo = 'kalite.kalibrasyon_toplu'
                  AND olusturma_tarihi > DATEADD(hour, -24, GETDATE())
            """)
            if check:
                return  # Son 24 saatte zaten gonderilmis

            rows = execute_query("""
                SELECT c.cihaz_kodu, c.cihaz_adi, c.lokasyon,
                       FORMAT(p.sonraki_kalibrasyon_tarihi, 'dd.MM.yyyy') AS sonraki,
                       DATEDIFF(day, GETDATE(), p.sonraki_kalibrasyon_tarihi) AS kalan
                FROM kalite.olcum_cihazlari c
                JOIN kalite.kalibrasyon_planlari p ON c.id = p.cihaz_id AND p.aktif_mi = 1
                WHERE c.aktif_mi = 1
                  AND p.sonraki_kalibrasyon_tarihi <= DATEADD(day, 30, GETDATE())
                ORDER BY p.sonraki_kalibrasyon_tarihi
            """)

            if not rows:
                return

            # Mesaj olustur
            gecmis = [r for r in rows if r['kalan'] < 0]
            yaklasan = [r for r in rows if r['kalan'] >= 0]

            # WhatsApp mesaji
            wp_mesaj = "[ONEMLI] *NEXOR - Kalibrasyon Uyarisi*\n\n"
            if gecmis:
                wp_mesaj += f"*SURESI GECMIS ({len(gecmis)} cihaz):*\n"
                for r in gecmis:
                    wp_mesaj += f"- {r['cihaz_kodu']} {r['cihaz_adi']} ({r['lokasyon'] or '-'}) | {abs(r['kalan'])} gun gecti\n"
                wp_mesaj += "\n"
            if yaklasan:
                wp_mesaj += f"*30 GUN ICINDE ({len(yaklasan)} cihaz):*\n"
                for r in yaklasan:
                    wp_mesaj += f"- {r['cihaz_kodu']} {r['cihaz_adi']} ({r['lokasyon'] or '-'}) | {r['kalan']} gun kaldi\n"

            # HTML e-mail icerigi
            html = """<html><body style="font-family:Calibri,Arial,sans-serif;">
            <h2 style="color:#dc2626;">NEXOR ERP - Kalibrasyon Uyarisi</h2>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
            <tr style="background:#1a1a2e;color:white;">
                <th>Cihaz Kodu</th><th>Cihaz Adi</th><th>Lokasyon</th><th>Sonraki Tarih</th><th>Kalan Gun</th><th>Durum</th>
            </tr>"""

            for r in rows:
                kalan = r['kalan']
                if kalan < 0:
                    renk = '#fee2e2'
                    durum = f"<b style='color:red'>{abs(kalan)} gun gecti</b>"
                else:
                    renk = '#fef9c3' if kalan <= 7 else '#fff'
                    durum = f"{kalan} gun"
                html += f"""<tr style="background:{renk}">
                    <td>{r['cihaz_kodu']}</td><td>{r['cihaz_adi']}</td><td>{r['lokasyon'] or '-'}</td>
                    <td>{r['sonraki']}</td><td align="center">{durum}</td>
                    <td>{'GECMIS' if kalan<0 else 'YAKIN'}</td></tr>"""

            html += "</table><br><p style='color:gray;font-size:11px;'>Bu otomatik bildirim NEXOR ERP tarafindan gonderilmistir.</p></body></html>"

            # WhatsApp abonelerine gonder
            try:
                from utils.whatsapp_service import get_whatsapp_service
                ws = get_whatsapp_service()
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT k.id, k.telefon
                    FROM sistem.bildirim_abonelikleri a
                    JOIN sistem.kullanicilar k ON a.kullanici_id = k.id
                    WHERE a.whatsapp_bildirim = 1 AND k.telefon IS NOT NULL AND k.aktif_mi = 1
                """)
                for tel_row in cursor.fetchall():
                    try:
                        ws.gonder(tel_row[1], wp_mesaj)
                    except Exception:
                        pass
                conn.close()
                print(f"[Kalibrasyon] WhatsApp uyarilari gonderildi")
            except Exception as wp_err:
                print(f"[Kalibrasyon] WhatsApp gonderim hatasi: {wp_err}")

            # E-mail gonder
            try:
                from utils.email_service import get_email_service
                es = get_email_service()
                if es.ayarlar:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT k.id, k.email
                        FROM sistem.bildirim_abonelikleri a
                        JOIN sistem.kullanicilar k ON a.kullanici_id = k.id
                        WHERE k.email IS NOT NULL AND k.email LIKE '%@%' AND k.aktif_mi = 1
                    """)
                    for em_row in cursor.fetchall():
                        try:
                            es.gonder(em_row[1], f"NEXOR Kalibrasyon Uyarisi - {len(gecmis)} gecmis, {len(yaklasan)} yaklasan", html)
                        except Exception:
                            pass
                    conn.close()
                    print(f"[Kalibrasyon] E-mail uyarilari gonderildi")
            except Exception as em_err:
                print(f"[Kalibrasyon] E-mail gonderim hatasi: {em_err}")

            # Bildirim tablosuna isaret birak (24 saat tekrar onleme)
            try:
                from core.database import get_db_connection as _gc
                conn = _gc()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sistem.bildirimler
                    (baslik, mesaj, modul, onem_derecesi, tip, kaynak_tablo,
                     okundu_mu, aktif_mi, olusturma_tarihi)
                    VALUES (?, ?, 'KALITE', 'YUKSEK', 'UYARI', 'kalite.kalibrasyon_toplu',
                            0, 1, GETDATE())
                """, (
                    f"Kalibrasyon Uyarisi: {len(gecmis)} gecmis, {len(yaklasan)} yaklasan",
                    wp_mesaj[:500]
                ))
                conn.commit()
                conn.close()
            except Exception:
                pass

        except Exception as e:
            print(f"[BildirimTetikleyici] Kalibrasyon toplu uyari hatasi: {e}")
