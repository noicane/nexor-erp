# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Hareket Motoru v3
Merkezi stok hareket yönetimi - Akış şablonlarına entegre

Kullanım:
    from core.hareket_motoru import HareketMotoru, HareketTipi
    
    motor = HareketMotoru(conn)
    
    # Stok girişi (irsaliye kabul)
    motor.stok_giris(
        urun_id=1,
        miktar=1000,
        lot_no="LOT-2501-0001-01",
        kaynak="IRSALIYE",
        kaynak_id=123
    )
    
    # Depo transferi (planlama sonrası)
    motor.transfer(
        lot_no="LOT-2501-0001-01",
        hedef_depo_id=14,  # HB-KTF
        miktar=1000,
        kaynak="IS_EMRI",
        kaynak_id=456
    )
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


class HareketTipi(Enum):
    """Stok hareket tipleri"""
    GIRIS = "GIRIS"              # İrsaliye girişi
    CIKIS = "CIKIS"              # Sevkiyat çıkışı
    TRANSFER = "TRANSFER"        # Depo transferi
    URETIM_GIRIS = "URETIM_GIRIS"  # Üretimden giriş
    URETIM_CIKIS = "URETIM_CIKIS"  # Üretime çıkış
    SAYIM_FAZLA = "SAYIM_FAZLA"  # Sayım fazlası
    SAYIM_EKSIK = "SAYIM_EKSIK"  # Sayım eksiği
    FIRE = "FIRE"                # Fire/hurda
    IADE = "IADE"                # İade


class HareketNedeni(Enum):
    """Hareket nedenleri"""
    IRSALIYE = "IRSALIYE"
    IS_EMRI = "IS_EMRI"
    PLANLAMA = "PLANLAMA"
    KALITE_ONAY = "KALITE_ONAY"
    KALITE_RED = "KALITE_RED"
    SEVKIYAT = "SEVKIYAT"
    SAYIM = "SAYIM"
    DUZELTME = "DUZELTME"
    REWORK = "REWORK"
    KIMYASAL_TUKETIM = "KIMYASAL_TUKETIM"


@dataclass
class HareketSonuc:
    """Hareket işlem sonucu"""
    basarili: bool
    hareket_id: Optional[int] = None
    bakiye_id: Optional[int] = None
    mesaj: str = ""
    hata: Optional[str] = None


class HareketMotoru:
    """
    Merkezi Stok Hareket Yönetimi
    
    Tüm stok hareketleri bu sınıf üzerinden yapılır.
    - Akış şablonlarına göre hedef depo belirleme
    - stok.stok_bakiye güncelleme
    - stok.stok_hareketleri loglama
    """
    
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
        self._akis_cache = {}
    
    # =========================================================================
    # ANA HAREKET FONKSİYONLARI
    # =========================================================================
    
    def stok_giris(
        self,
        urun_id: int,
        miktar: float,
        lot_no: str,
        depo_id: int = None,
        parent_lot_no: str = None,
        palet_no: int = None,
        toplam_palet: int = None,
        urun_kodu: str = None,  # DÜZELTME: stok_kodu -> urun_kodu
        urun_adi: str = None,   # DÜZELTME: stok_adi -> urun_adi
        cari_unvani: str = None,
        kaplama_tipi: str = None,
        birim: str = "ADET",
        irsaliye_satir_id: int = None,
        kalite_durumu: str = "BEKLIYOR",
        durum_kodu: str = "KABUL",  # YENİ: Durum sistemi
        aciklama: str = None
    ) -> HareketSonuc:
        """
        Stok girişi yap (İrsaliye kabul)
        
        Args:
            urun_id: Ürün ID
            miktar: Giriş miktarı
            lot_no: Lot numarası
            depo_id: Hedef depo ID (None ise akış şablonundan bulunur)
            ... diğer parametreler
        
        Returns:
            HareketSonuc
        """
        try:
            # Hedef depo belirleme
            if depo_id is None:
                depo_id = self._get_giris_deposu(urun_id)
            
            # Mevcut bakiye kontrolü
            self.cursor.execute("""
                SELECT id, miktar FROM stok.stok_bakiye WHERE lot_no = ?
            """, (lot_no,))
            existing = self.cursor.fetchone()
            
            if existing:
                # Mevcut kaydı güncelle
                # NOT: Bakiye 0'dan yukseliyorsa (kapanmis kayit yeniden acilir),
                # kalite_durumu/durum_kodu da yeni degerle tazelenir. Aksi halde
                # eski kayitta SEVK_EDILDI takili kalip lot sevk hazir listede gorunmez.
                bakiye_id = existing[0]
                self.cursor.execute("""
                    UPDATE stok.stok_bakiye
                    SET miktar = miktar + ?,
                        kalite_durumu = CASE WHEN miktar = 0 THEN ? ELSE kalite_durumu END,
                        durum_kodu    = CASE WHEN miktar = 0 THEN ? ELSE durum_kodu END,
                        son_hareket_tarihi = GETDATE()
                    WHERE id = ?
                """, (miktar, kalite_durumu, durum_kodu, bakiye_id))
            else:
                # Yeni kayıt
                self.cursor.execute("""
                    INSERT INTO stok.stok_bakiye 
                    (urun_id, depo_id, lot_no, parent_lot_no, miktar, rezerve_miktar,
                     kalite_durumu, durum_kodu, palet_no, toplam_palet,
                     irsaliye_satir_id, giris_tarihi, son_hareket_tarihi)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
                """, (urun_id, depo_id, lot_no, parent_lot_no, miktar, kalite_durumu,
                      durum_kodu, palet_no, toplam_palet, irsaliye_satir_id))
                bakiye_id = self.cursor.fetchone()[0]
            
            # Hareket kaydı
            hareket_id = self._log_hareket(
                hareket_tipi=HareketTipi.GIRIS,
                hareket_nedeni=HareketNedeni.IRSALIYE,
                urun_id=urun_id,
                depo_id=depo_id,
                miktar=miktar,
                lot_no=lot_no,
                referans_tip="IRSALIYE_SATIR",
                referans_id=irsaliye_satir_id,
                aciklama=aciklama or f"İrsaliye girişi - {lot_no}"
            )
            
            # self.conn.commit()  # ❌ Caller commit yapacak
            
            return HareketSonuc(
                basarili=True,
                hareket_id=hareket_id,
                bakiye_id=bakiye_id,
                mesaj=f"Stok girişi başarılı: {miktar} {birim}"
            )
            
        except Exception as e:
            self.conn.rollback()
            return HareketSonuc(
                basarili=False,
                hata=str(e),
                mesaj=f"Stok girişi hatası: {str(e)}"
            )
    
    def transfer(
        self,
        lot_no: str,
        hedef_depo_id: int,
        miktar: float = None,
        kaynak: str = None,
        kaynak_id: int = None,
        aciklama: str = None,
        kalite_durumu: str = None,
        durum_kodu: str = None
    ) -> HareketSonuc:
        """
        Depo transferi yap - AYRI BAKİYELER TUTAR
        
        Args:
            lot_no: Transfer edilecek lot
            hedef_depo_id: Hedef depo ID
            miktar: Transfer miktarı (None ise tüm bakiye)
            kaynak: Referans tipi (IS_EMRI, PLANLAMA vb.)
            kaynak_id: Referans ID
            kalite_durumu: Kalite durumu (opsiyonel)
        
        Returns:
            HareketSonuc
        """
        try:
            # Kaynak depoda bakiye bul (hedef depo hariç)
            self.cursor.execute("""
                SELECT id, urun_id, depo_id, miktar, rezerve_miktar,
                       stok_kodu, stok_adi, cari_unvani, kaplama_tipi, birim,
                       giris_tarihi, parent_lot_no, kalite_durumu, durum_kodu
                FROM stok.stok_bakiye 
                WHERE lot_no = ? AND depo_id != ?
                ORDER BY id
            """, (lot_no, hedef_depo_id))
            bakiye = self.cursor.fetchone()
            
            if not bakiye:
                return HareketSonuc(
                    basarili=False,
                    hata="LOT_BULUNAMADI",
                    mesaj=f"Lot bulunamadı: {lot_no}"
                )
            
            (bakiye_id, urun_id, kaynak_depo_id, mevcut_miktar, rezerve,
             stok_kodu, stok_adi, cari_unvani, kaplama_tipi, birim,
             giris_tarihi, parent_lot_no, mevcut_kalite, mevcut_durum) = bakiye
            
            kullanilabilir = mevcut_miktar - (rezerve or 0)
            
            if miktar is None:
                miktar = kullanilabilir
            
            if miktar > kullanilabilir:
                return HareketSonuc(
                    basarili=False,
                    hata="YETERSIZ_STOK",
                    mesaj=f"Yetersiz stok: {kullanilabilir} mevcut, {miktar} istendi"
                )
            
            # 1. Kaynak bakiyeyi azalt veya sil
            if mevcut_miktar <= miktar:
                self.cursor.execute("DELETE FROM stok.stok_bakiye WHERE id = ?", (bakiye_id,))
            else:
                self.cursor.execute("""
                    UPDATE stok.stok_bakiye 
                    SET miktar = miktar - ?, son_hareket_tarihi = GETDATE()
                    WHERE id = ?
                """, (miktar, bakiye_id))
            
            # 2. Çıkış hareketi
            self._log_hareket(
                hareket_tipi=HareketTipi.TRANSFER,
                hareket_nedeni=HareketNedeni.PLANLAMA if kaynak == "PLANLAMA" else HareketNedeni.IS_EMRI,
                urun_id=urun_id,
                depo_id=kaynak_depo_id,
                miktar=-miktar,
                lot_no=lot_no,
                referans_tip=kaynak,
                referans_id=kaynak_id,
                aciklama=aciklama or f"Transfer çıkış: {lot_no}"
            )
            
            # 3. Hedef depoda bakiye var mı?
            self.cursor.execute("""
                SELECT id FROM stok.stok_bakiye 
                WHERE lot_no = ? AND depo_id = ?
            """, (lot_no, hedef_depo_id))
            hedef_bakiye = self.cursor.fetchone()
            
            if hedef_bakiye:
                hedef_bakiye_id = hedef_bakiye[0]
                self.cursor.execute("""
                    UPDATE stok.stok_bakiye 
                    SET miktar = miktar + ?, 
                        son_hareket_tarihi = GETDATE(),
                        kalite_durumu = COALESCE(?, kalite_durumu),
                        durum_kodu = COALESCE(?, durum_kodu)
                    WHERE id = ?
                """, (miktar, kalite_durumu, durum_kodu, hedef_bakiye_id))
            else:
                self.cursor.execute("""
                    INSERT INTO stok.stok_bakiye (
                        urun_id, depo_id, lot_no, miktar, rezerve_miktar,
                        son_hareket_tarihi, parent_lot_no, kalite_durumu, durum_kodu,
                        stok_kodu, stok_adi, cari_unvani, kaplama_tipi, birim, giris_tarihi
                    ) OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, 0, GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (urun_id, hedef_depo_id, lot_no, miktar, parent_lot_no, 
                      kalite_durumu or mevcut_kalite, durum_kodu or mevcut_durum or 'AKTIF',
                      stok_kodu, stok_adi, cari_unvani, kaplama_tipi, birim, giris_tarihi))
                hedef_bakiye_id = self.cursor.fetchone()[0]
            
            # 4. Giriş hareketi
            hareket_id = self._log_hareket(
                hareket_tipi=HareketTipi.TRANSFER,
                hareket_nedeni=HareketNedeni.PLANLAMA if kaynak == "PLANLAMA" else HareketNedeni.IS_EMRI,
                urun_id=urun_id,
                depo_id=hedef_depo_id,
                miktar=miktar,
                lot_no=lot_no,
                referans_tip=kaynak,
                referans_id=kaynak_id,
                aciklama=aciklama or f"Transfer giriş: {lot_no}"
            )
            
            # NOT: Commit caller tarafından yapılacak (transaction bütünlüğü için)
            # self.conn.commit()  # ❌ KALDIRILDI
            
            return HareketSonuc(
                basarili=True,
                hareket_id=hareket_id,
                bakiye_id=hedef_bakiye_id,
                mesaj=f"Transfer başarılı: {miktar} adet, Depo {kaynak_depo_id} → {hedef_depo_id}"
            )
            
        except Exception as e:
            self.conn.rollback()
            return HareketSonuc(
                basarili=False,
                hata=str(e),
                mesaj=f"Transfer hatası: {str(e)}"
            )
    
    def kalite_onayla(
        self,
        lot_no: str,
        onay_durumu: str,  # "ONAYLANDI" veya "REDDEDILDI"
        onaylayan_id: int = None,
        aciklama: str = None,
        is_emri_id: int = None
    ) -> HareketSonuc:
        """
        Kalite onay/red işlemi

        Args:
            lot_no: Lot numarası
            onay_durumu: ONAYLANDI veya REDDEDILDI
            onaylayan_id: Onaylayan kullanıcı ID
            is_emri_id: Varsa, islem sonrasi IE durumu otomatik tazelenir

        Returns:
            HareketSonuc
        """
        try:
            # Bakiye bilgisi
            self.cursor.execute("""
                SELECT id, urun_id, depo_id, miktar
                FROM stok.stok_bakiye 
                WHERE lot_no = ?
            """, (lot_no,))
            bakiye = self.cursor.fetchone()
            
            if not bakiye:
                return HareketSonuc(
                    basarili=False,
                    hata="LOT_BULUNAMADI",
                    mesaj=f"Lot bulunamadı: {lot_no}"
                )
            
            bakiye_id, urun_id, depo_id, miktar = bakiye
            
            # Kalite durumu güncelle
            self.cursor.execute("""
                UPDATE stok.stok_bakiye 
                SET kalite_durumu = ?, son_hareket_tarihi = GETDATE()
                WHERE id = ?
            """, (onay_durumu, bakiye_id))
            
            # Onaylandıysa ve akışa göre transfer gerekiyorsa
            if onay_durumu == "ONAYLANDI":
                # Akış şablonundan sonraki depoyu bul
                hedef_depo_id = self._get_sonraki_depo(urun_id, "KALITE_GIRIS")
                
                if hedef_depo_id and hedef_depo_id != depo_id:
                    self.cursor.execute("""
                        UPDATE stok.stok_bakiye 
                        SET depo_id = ?
                        WHERE id = ?
                    """, (hedef_depo_id, bakiye_id))
            
            # Hareket kaydı
            hareket_id = self._log_hareket(
                hareket_tipi=HareketTipi.TRANSFER if onay_durumu == "ONAYLANDI" else HareketTipi.CIKIS,
                hareket_nedeni=HareketNedeni.KALITE_ONAY if onay_durumu == "ONAYLANDI" else HareketNedeni.KALITE_RED,
                urun_id=urun_id,
                depo_id=depo_id,
                miktar=miktar,
                lot_no=lot_no,
                referans_tip="KALITE",
                referans_id=None,
                aciklama=aciklama or f"Kalite {onay_durumu.lower()}: {lot_no}"
            )

            # self.conn.commit()  # ❌ Caller commit yapacak

            # IE durumu otomatik tazele (verildiyse)
            if is_emri_id:
                self.is_emri_durum_tazele(is_emri_id)

            return HareketSonuc(
                basarili=True,
                hareket_id=hareket_id,
                bakiye_id=bakiye_id,
                mesaj=f"Kalite durumu güncellendi: {onay_durumu}"
            )
            
        except Exception as e:
            self.conn.rollback()
            return HareketSonuc(
                basarili=False,
                hata=str(e),
                mesaj=f"Kalite onay hatası: {str(e)}"
            )
    
    def rezerve_et(
        self,
        lot_no: str,
        miktar: float,
        is_emri_id: int = None
    ) -> HareketSonuc:
        """
        Stok rezerve et (planlama için)
        """
        try:
            self.cursor.execute("""
                UPDATE stok.stok_bakiye 
                SET rezerve_miktar = ISNULL(rezerve_miktar, 0) + ?
                WHERE lot_no = ?
            """, (miktar, lot_no))
            
            # self.conn.commit()  # ❌ Caller commit yapacak
            
            return HareketSonuc(
                basarili=True,
                mesaj=f"Rezervasyon başarılı: {miktar} adet"
            )
            
        except Exception as e:
            self.conn.rollback()
            return HareketSonuc(
                basarili=False,
                hata=str(e),
                mesaj=f"Rezervasyon hatası: {str(e)}"
            )
    
    def rezerve_iptal(
        self,
        lot_no: str,
        miktar: float
    ) -> HareketSonuc:
        """
        Rezervasyonu iptal et
        """
        try:
            self.cursor.execute("""
                UPDATE stok.stok_bakiye 
                SET rezerve_miktar = CASE 
                    WHEN ISNULL(rezerve_miktar, 0) - ? < 0 THEN 0 
                    ELSE ISNULL(rezerve_miktar, 0) - ? 
                END
                WHERE lot_no = ?
            """, (miktar, miktar, lot_no))
            
            # self.conn.commit()  # ❌ Caller commit yapacak
            
            return HareketSonuc(
                basarili=True,
                mesaj=f"Rezervasyon iptal: {miktar} adet"
            )
            
        except Exception as e:
            self.conn.rollback()
            return HareketSonuc(
                basarili=False,
                hata=str(e),
                mesaj=f"Rezervasyon iptal hatası: {str(e)}"
            )
    
    def stok_cikis(
        self,
        lot_no: str,
        miktar: float = None,
        kaynak: str = None,
        kaynak_id: int = None,
        aciklama: str = None,
        is_emri_id: int = None
    ) -> HareketSonuc:
        """
        Stok çıkışı yap (Sevkiyat için)

        Args:
            lot_no: Çıkış yapılacak lot
            miktar: Çıkış miktarı (None ise tüm bakiye)
            kaynak: Referans tipi (IRSALIYE, SEVKIYAT vb.)
            kaynak_id: Referans ID
            is_emri_id: Varsa, cikis sonrasi IE durumu otomatik tazelenir

        Returns:
            HareketSonuc
        """
        try:
            # Mevcut bakiye bilgisi
            self.cursor.execute("""
                SELECT id, urun_id, depo_id, miktar, stok_kodu
                FROM stok.stok_bakiye 
                WHERE lot_no = ?
            """, (lot_no,))
            bakiye = self.cursor.fetchone()
            
            if not bakiye:
                return HareketSonuc(
                    basarili=False,
                    hata="LOT_BULUNAMADI",
                    mesaj=f"Lot bulunamadı: {lot_no}"
                )
            
            bakiye_id, urun_id, depo_id, mevcut_miktar, stok_kodu = bakiye
            
            if miktar is None:
                miktar = mevcut_miktar
            
            if miktar > mevcut_miktar:
                return HareketSonuc(
                    basarili=False,
                    hata="YETERSIZ_STOK",
                    mesaj=f"Yetersiz stok: {mevcut_miktar} mevcut, {miktar} istendi"
                )
            
            # Bakiyeyi güncelle
            yeni_miktar = mevcut_miktar - miktar
            self.cursor.execute("""
                UPDATE stok.stok_bakiye 
                SET miktar = ?, 
                    kalite_durumu = CASE WHEN ? = 0 THEN 'SEVK_EDILDI' ELSE kalite_durumu END,
                    son_hareket_tarihi = GETDATE()
                WHERE id = ?
            """, (yeni_miktar, yeni_miktar, bakiye_id))
            
            # Hareket kaydı
            hareket_id = self._log_hareket(
                hareket_tipi=HareketTipi.CIKIS,
                hareket_nedeni=HareketNedeni.SEVKIYAT,
                urun_id=urun_id,
                depo_id=depo_id,
                miktar=-miktar,  # Negatif = çıkış
                lot_no=lot_no,
                referans_tip=kaynak,
                referans_id=kaynak_id,
                aciklama=aciklama or f"Stok çıkışı - {lot_no}"
            )

            # self.conn.commit()  # ❌ Caller commit yapacak

            # IE durumu otomatik tazele (verildiyse)
            if is_emri_id:
                self.is_emri_durum_tazele(is_emri_id)

            return HareketSonuc(
                basarili=True,
                hareket_id=hareket_id,
                bakiye_id=bakiye_id,
                mesaj=f"Stok çıkışı başarılı: {miktar} adet"
            )
            
        except Exception as e:
            self.conn.rollback()
            return HareketSonuc(
                basarili=False,
                hata=str(e),
                mesaj=f"Stok çıkışı hatası: {str(e)}"
            )

    # =========================================================================
    # İŞ EMRİ DURUM YÖNETİMİ (merkezi)
    # =========================================================================

    # Dokunulmayacak durumlar (manuel iptal/arşiv gibi)
    _KORUNAN_DURUMLAR = ('IPTAL', 'IPTAL_EDILDI', 'ARSIV')

    def is_emri_durum_hesapla(self, is_emri_id: int) -> Optional[str]:
        """
        Is emrinin olmasi gereken durumu hesaplar (UPDATE yapmaz, sadece dondurur).

        Mantik (oncelikli):
          IPTAL/ARSIV           -> korunur (None doner, dokunma)
          sevk_edilen >= toplam -> SEVK_EDILDI
          sevk_edilen > 0       -> KISMI_SEVK
          kontrol == toplam:
              hata == 0          -> ONAYLANDI
              saglam == 0        -> REDDEDILDI
              ikisi de > 0       -> KISMI_RED
          kontrol > 0            -> URETIMDE (kismi kontrol, henuz bitmedi)
          uretilen > 0           -> URETIMDE
          PLANLI korunur         -> PLANLI
          default                -> BEKLIYOR
        """
        self.cursor.execute("""
            SELECT ie.durum, ISNULL(ie.toplam_miktar, 0), ISNULL(ie.uretilen_miktar, 0),
                   ISNULL((SELECT SUM(fk.kontrol_miktar) FROM kalite.final_kontrol fk
                           WHERE fk.is_emri_id = ie.id), 0) AS kontrol_toplam,
                   ISNULL((SELECT SUM(fk.saglam_adet) FROM kalite.final_kontrol fk
                           WHERE fk.is_emri_id = ie.id), 0) AS saglam_toplam,
                   ISNULL((SELECT SUM(fk.hatali_adet) FROM kalite.final_kontrol fk
                           WHERE fk.is_emri_id = ie.id), 0) AS hatali_toplam,
                   ISNULL((SELECT SUM(sat.miktar)
                           FROM siparis.cikis_irsaliye_satirlar sat
                           LEFT JOIN siparis.cikis_irsaliyeleri ci ON sat.irsaliye_id = ci.id
                           WHERE sat.is_emri_id = ie.id
                             AND ISNULL(ci.durum, '') <> 'IPTAL'), 0) AS sevk_edilen
            FROM siparis.is_emirleri ie
            WHERE ie.id = ?
        """, (is_emri_id,))
        row = self.cursor.fetchone()
        if not row:
            return None

        mevcut_durum = row[0]
        toplam = float(row[1] or 0)
        uretilen = float(row[2] or 0)
        kontrol = float(row[3] or 0)
        saglam = float(row[4] or 0)
        hatali = float(row[5] or 0)
        sevk = float(row[6] or 0)

        # Korunan durumlara dokunma
        if mevcut_durum in self._KORUNAN_DURUMLAR:
            return None

        # Toplam 0 ise karar verilemez; mevcut durumu koru
        if toplam <= 0:
            return mevcut_durum

        # Sevk oncelikli
        if sevk >= toplam:
            return 'SEVK_EDILDI'
        if sevk > 0:
            return 'KISMI_SEVK'

        # Kalite kontrol tamamlandiysa
        if kontrol >= toplam:
            if hatali == 0:
                return 'ONAYLANDI'
            if saglam == 0:
                return 'REDDEDILDI'
            return 'KISMI_RED'

        # Kismi kontrol veya uretim baslamis ise URETIMDE
        if kontrol > 0 or uretilen > 0:
            return 'URETIMDE'

        # PLANLI'yi koru (henuz uretim baslamamis)
        if mevcut_durum == 'PLANLI':
            return 'PLANLI'

        return 'BEKLIYOR'

    def is_emri_durum_tazele(self, is_emri_id: int) -> HareketSonuc:
        """
        Is emrinin durumunu yeniden hesaplayip yazar.
        Degisiklik yoksa UPDATE atilmaz (log kirlenmez).
        Her hareket (sevk/kalite/iade) sonrasi cagrilmalidir.
        """
        try:
            yeni_durum = self.is_emri_durum_hesapla(is_emri_id)
            if yeni_durum is None:
                return HareketSonuc(
                    basarili=True,
                    mesaj=f"IE {is_emri_id}: durum korundu (iptal/arsiv veya kayit yok)"
                )

            # Mevcut durumu tekrar al (karar verirken okuduk ama net olmasi icin)
            self.cursor.execute(
                "SELECT durum FROM siparis.is_emirleri WHERE id = ?", (is_emri_id,)
            )
            row = self.cursor.fetchone()
            if not row:
                return HareketSonuc(
                    basarili=False,
                    hata="IE_BULUNAMADI",
                    mesaj=f"Is emri yok: {is_emri_id}"
                )
            mevcut = row[0]

            if mevcut == yeni_durum:
                return HareketSonuc(
                    basarili=True,
                    mesaj=f"IE {is_emri_id}: durum ayni ({mevcut})"
                )

            self.cursor.execute("""
                UPDATE siparis.is_emirleri
                SET durum = ?, guncelleme_tarihi = GETDATE()
                WHERE id = ?
            """, (yeni_durum, is_emri_id))

            return HareketSonuc(
                basarili=True,
                mesaj=f"IE {is_emri_id}: {mevcut} -> {yeni_durum}"
            )
        except Exception as e:
            return HareketSonuc(
                basarili=False,
                hata=str(e),
                mesaj=f"Durum tazele hatasi: {e}"
            )

    # =========================================================================
    # YARDIMCI FONKSİYONLAR
    # =========================================================================
    
    def _log_hareket(
        self,
        hareket_tipi: HareketTipi,
        hareket_nedeni: HareketNedeni,
        urun_id: int,
        depo_id: int,
        miktar: float,
        lot_no: str,
        referans_tip: str = None,
        referans_id: int = None,
        aciklama: str = None,
        birim_id: int = 1
    ) -> int:
        """Hareket kaydı oluştur"""
        self.cursor.execute("""
            INSERT INTO stok.stok_hareketleri 
            (uuid, hareket_tipi, hareket_nedeni, tarih, urun_id, depo_id, 
             miktar, birim_id, lot_no, referans_tip, referans_id, aciklama, olusturma_tarihi)
            OUTPUT INSERTED.id
            VALUES (NEWID(), ?, ?, GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """, (hareket_tipi.value, hareket_nedeni.value, urun_id, depo_id,
              miktar, birim_id, lot_no, referans_tip, referans_id, aciklama))
        
        return self.cursor.fetchone()[0]
    
    def _get_giris_deposu(self, urun_id: int) -> int:
        """Ürün için giriş deposunu bul (akış şablonundan)"""
        try:
            # Önce ürünün akış şablonunu bul
            self.cursor.execute("""
                SELECT akis_sablon_id FROM stok.urunler WHERE id = ?
            """, (urun_id,))
            row = self.cursor.fetchone()
            
            sablon_id = row[0] if row and row[0] else None
            
            # Şablon yoksa varsayılanı bul
            if not sablon_id:
                self.cursor.execute("""
                    SELECT id FROM tanim.akis_sablon 
                    WHERE varsayilan_mi = 1 AND aktif_mi = 1
                """)
                row = self.cursor.fetchone()
                sablon_id = row[0] if row else None
            
            if sablon_id:
                # KABUL adımının hedef deposunu bul
                self.cursor.execute("""
                    SELECT d.id
                    FROM tanim.akis_adim a
                    JOIN tanim.akis_adim_tipleri t ON a.adim_tipi_id = t.id
                    LEFT JOIN tanim.depo_tipleri dt ON a.hedef_depo_tipi_id = dt.id
                    LEFT JOIN tanim.depolar d ON d.depo_tipi_id = dt.id AND d.aktif_mi = 1
                    WHERE a.sablon_id = ? AND t.kod = 'KABUL' AND a.aktif_mi = 1
                    ORDER BY d.id
                """, (sablon_id,))
                row = self.cursor.fetchone()
                if row:
                    return row[0]
            
            # Varsayılan: KAB-01 (ID=7)
            return 7
            
        except Exception as e:
            print(f"Giriş deposu bulma hatası: {e}")
            return 7  # Varsayılan KAB-01
    
    def _get_sonraki_depo(self, urun_id: int, mevcut_adim_tipi: str) -> Optional[int]:
        """Akış şablonundan sonraki adımın deposunu bul"""
        try:
            # Ürünün akış şablonunu bul
            self.cursor.execute("""
                SELECT COALESCE(u.akis_sablon_id, 
                    (SELECT id FROM tanim.akis_sablon WHERE varsayilan_mi = 1 AND aktif_mi = 1))
                FROM stok.urunler u WHERE u.id = ?
            """, (urun_id,))
            row = self.cursor.fetchone()
            
            if not row or not row[0]:
                return None
            
            sablon_id = row[0]
            
            # Mevcut adımın sırasını bul
            self.cursor.execute("""
                SELECT a.sira
                FROM tanim.akis_adim a
                JOIN tanim.akis_adim_tipleri t ON a.adim_tipi_id = t.id
                WHERE a.sablon_id = ? AND t.kod = ? AND a.aktif_mi = 1
            """, (sablon_id, mevcut_adim_tipi))
            row = self.cursor.fetchone()
            
            if not row:
                return None
            
            mevcut_sira = row[0]
            
            # Sonraki adımın deposunu bul
            self.cursor.execute("""
                SELECT TOP 1 d.id
                FROM tanim.akis_adim a
                LEFT JOIN tanim.depo_tipleri dt ON a.hedef_depo_tipi_id = dt.id
                LEFT JOIN tanim.depolar d ON d.depo_tipi_id = dt.id AND d.aktif_mi = 1
                WHERE a.sablon_id = ? AND a.sira > ? AND a.aktif_mi = 1
                ORDER BY a.sira, d.id
            """, (sablon_id, mevcut_sira))
            row = self.cursor.fetchone()
            
            return row[0] if row else None
            
        except Exception as e:
            print(f"Sonraki depo bulma hatası: {e}")
            return None
    
    def get_hat_basi_deposu(self, hat_id: int) -> Optional[int]:
        """Hat için hat başı deposunu bul"""
        try:
            # Hat koduna göre hat başı deposu bul
            self.cursor.execute("""
                SELECT d.id
                FROM tanim.uretim_hatlari h
                JOIN tanim.depolar d ON d.kod = 'HB-' + 
                    CASE 
                        WHEN h.kod LIKE '%KTF%' OR h.kod LIKE '%KATA%' THEN 'KTF'
                        WHEN h.kod LIKE '%TOZ%' THEN 'TOZ'
                        WHEN h.kod LIKE '%ZN%' OR h.kod LIKE '%CINKO%' OR h.kod LIKE '%ÇİNKO%' THEN 'ZN'
                        ELSE 'KTF'
                    END
                WHERE h.id = ? AND d.aktif_mi = 1
            """, (hat_id,))
            row = self.cursor.fetchone()
            
            if row:
                return row[0]
            
            # Bulunamazsa genel hat başı deposu
            self.cursor.execute("""
                SELECT TOP 1 id FROM tanim.depolar 
                WHERE depo_tipi_id = (SELECT id FROM tanim.depo_tipleri WHERE kod = 'HAT_BASI')
                AND aktif_mi = 1
            """)
            row = self.cursor.fetchone()
            
            return row[0] if row else None
            
        except Exception as e:
            print(f"Hat başı deposu bulma hatası: {e}")
            return None
    
    def get_uretim_deposu(self, hat_id: int) -> Optional[int]:
        """Hat için üretim deposunu bul"""
        try:
            self.cursor.execute("""
                SELECT d.id
                FROM tanim.uretim_hatlari h
                JOIN tanim.depolar d ON d.kod = 'URT-' + 
                    CASE 
                        WHEN h.kod LIKE '%KTF%' OR h.kod LIKE '%KATA%' THEN 'KATAFOREZ'
                        WHEN h.kod LIKE '%TOZ%' THEN 'TOZBOYA'
                        WHEN h.kod LIKE '%ZN%' OR h.kod LIKE '%CINKO%' OR h.kod LIKE '%ÇİNKO%' THEN 'ZNNI'
                        ELSE 'KATAFOREZ'
                    END
                WHERE h.id = ? AND d.aktif_mi = 1
            """, (hat_id,))
            row = self.cursor.fetchone()
            
            return row[0] if row else None
            
        except Exception as e:
            print(f"Üretim deposu bulma hatası: {e}")
            return None
    
    def get_depo_by_tip(self, depo_tipi_kod: str) -> Optional[int]:
        """Depo tipi koduna göre depo ID bul"""
        try:
            self.cursor.execute("""
                SELECT TOP 1 d.id 
                FROM tanim.depolar d
                JOIN tanim.depo_tipleri dt ON d.depo_tipi_id = dt.id
                WHERE dt.kod = ? AND d.aktif_mi = 1
                ORDER BY d.id
            """, (depo_tipi_kod,))
            row = self.cursor.fetchone()
            
            return row[0] if row else None
            
        except Exception as e:
            print(f"Depo bulma hatası: {e}")
            return None
    
    # =========================================================================
    # SORGULAMA FONKSİYONLARI
    # =========================================================================
    
    def get_bakiye(self, lot_no: str) -> Optional[Dict]:
        """Lot bakiye bilgisini getir"""
        try:
            self.cursor.execute("""
                SELECT sb.id, sb.urun_id, sb.depo_id, d.kod as depo_kod, d.ad as depo_ad,
                       sb.miktar, sb.rezerve_miktar, sb.kalite_durumu,
                       sb.stok_kodu, sb.stok_adi, sb.cari_unvani
                FROM stok.stok_bakiye sb
                LEFT JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE sb.lot_no = ?
            """, (lot_no,))
            row = self.cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'urun_id': row[1],
                    'depo_id': row[2],
                    'depo_kod': row[3],
                    'depo_ad': row[4],
                    'miktar': row[5],
                    'rezerve_miktar': row[6] or 0,
                    'kullanilabilir': (row[5] or 0) - (row[6] or 0),
                    'kalite_durumu': row[7],
                    'stok_kodu': row[8],
                    'stok_adi': row[9],
                    'cari_unvani': row[10]
                }
            return None
            
        except Exception as e:
            print(f"Bakiye sorgulama hatası: {e}")
            return None
    
    def get_hareketler(self, lot_no: str, limit: int = 50) -> List[Dict]:
        """Lot hareket geçmişini getir"""
        try:
            self.cursor.execute("""
                SELECT TOP (?) h.id, h.hareket_tipi, h.hareket_nedeni, h.tarih,
                       d.kod as depo_kod, h.miktar, h.aciklama
                FROM stok.stok_hareketleri h
                LEFT JOIN tanim.depolar d ON h.depo_id = d.id
                WHERE h.lot_no = ?
                ORDER BY h.tarih DESC, h.id DESC
            """, (limit, lot_no))
            
            return [
                {
                    'id': row[0],
                    'hareket_tipi': row[1],
                    'hareket_nedeni': row[2],
                    'tarih': row[3],
                    'depo_kod': row[4],
                    'miktar': row[5],
                    'aciklama': row[6]
                }
                for row in self.cursor.fetchall()
            ]
            
        except Exception as e:
            print(f"Hareket sorgulama hatası: {e}")
            return []
