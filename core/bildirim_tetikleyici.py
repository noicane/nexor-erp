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
from core.database import execute_query


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
                SELECT kp.id, kp.cihaz_adi,
                       FORMAT(kp.sonraki_kalibrasyon_tarihi, 'dd.MM.yyyy') AS tarih
                FROM kalite.kalibrasyon_planlari kp
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
