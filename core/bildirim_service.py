# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Merkezi Bildirim Servisi
Tüm modüllerden bildirim oluşturma, kullanıcı bazlı listeleme ve yönetim

Kullanım:
    from core.bildirim_service import BildirimService

    # Tekil bildirim
    BildirimService.gonder(
        kullanici_id=5,
        baslik="Yeni İş Emri",
        mesaj="IE-2026-0150 size atandı",
        modul="IS_EMIRLERI",
        onem="NORMAL"
    )

    # Role toplu gönderim
    BildirimService.role_gonder(
        rol_id=3,
        baslik="Kalibrasyon Uyarısı",
        mesaj="5 cihazın kalibrasyonu yaklaşıyor",
        modul="KALITE",
        onem="YUKSEK"
    )

    # Şablondan bildirim
    BildirimService.sablon_gonder(
        kod="IE_YENI",
        hedef_kullanici_id=5,
        parametreler={"is_emri_no": "IE-2026-0150", "musteri_adi": "ABC Ltd."}
    )

Tarih: 2026-02-18
"""

from datetime import datetime
from typing import Optional
from core.database import get_db_connection, execute_query, execute_non_query


# Önem derecesi sıralama (filtre için)
ONEM_SIRA = {
    'KRITIK': 1,
    'YUKSEK': 2,
    'NORMAL': 3,
    'DUSUK': 4,
}


class BildirimService:
    """Merkezi bildirim yönetim servisi"""

    # =========================================================================
    # BİLDİRİM GÖNDERME
    # =========================================================================

    @staticmethod
    def gonder(
        kullanici_id: int,
        baslik: str,
        mesaj: str,
        modul: str = 'SISTEM',
        onem: str = 'NORMAL',
        tip: str = 'BILGI',
        kaynak_tablo: str = None,
        kaynak_id: int = None,
        sayfa_yonlendirme: str = None,
        gonderen_id: int = None,
    ) -> Optional[int]:
        """
        Tek kullanıcıya bildirim gönder.

        Args:
            kullanici_id: Hedef kullanıcı ID
            baslik: Bildirim başlığı
            mesaj: Bildirim mesajı
            modul: Kaynak modül (IS_EMIRLERI, KALITE, BAKIM, URETIM, STOK, vb.)
            onem: Önem derecesi (KRITIK, YUKSEK, NORMAL, DUSUK)
            tip: Bildirim tipi (BILGI, UYARI, GOREV, ONAY_BEKLIYOR, HATIRLATMA)
            kaynak_tablo: İlişkili tablo adı
            kaynak_id: İlişkili kayıt ID
            sayfa_yonlendirme: Tıklanınca gidilecek sayfa ID
            gonderen_id: Gönderen kullanıcı ID (None = sistem)

        Returns:
            Oluşturulan bildirim ID veya None
        """
        if not kullanici_id or not baslik:
            return None

        # Kullanıcının tercihlerini kontrol et
        if not BildirimService._tercih_kontrol(kullanici_id, modul, onem):
            return None

        if not gonderen_id:
            gonderen_id = BildirimService._get_current_user_id()

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sistem.bildirimler
                    (baslik, mesaj, modul, onem_derecesi, tip,
                     hedef_kullanici_id, gonderen_id,
                     kaynak_tablo, kaynak_id, sayfa_yonlendirme,
                     okundu_mu, aktif_mi, olusturma_tarihi)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, GETDATE())
            """, [baslik, mesaj, modul, onem, tip,
                  kullanici_id, gonderen_id,
                  kaynak_tablo, kaynak_id, sayfa_yonlendirme])

            row = cursor.fetchone()
            bildirim_id = row[0] if row else None
            conn.commit()
            conn.close()

            return bildirim_id

        except Exception as e:
            print(f"[BildirimService] Gönderim hatası: {e}")
            return None

    @staticmethod
    def role_gonder(
        rol_id: int,
        baslik: str,
        mesaj: str,
        modul: str = 'SISTEM',
        onem: str = 'NORMAL',
        tip: str = 'BILGI',
        kaynak_tablo: str = None,
        kaynak_id: int = None,
        sayfa_yonlendirme: str = None,
        gonderen_id: int = None,
    ) -> int:
        """
        Belirli bir roldeki tüm kullanıcılara bildirim gönder.

        Returns:
            Gönderilen bildirim sayısı
        """
        try:
            kullanicilar = execute_query(
                "SELECT id FROM sistem.kullanicilar WHERE rol_id = ? AND aktif_mi = 1 AND silindi_mi = 0",
                [rol_id]
            )
            count = 0
            for k in kullanicilar:
                result = BildirimService.gonder(
                    kullanici_id=k['id'],
                    baslik=baslik, mesaj=mesaj, modul=modul,
                    onem=onem, tip=tip,
                    kaynak_tablo=kaynak_tablo, kaynak_id=kaynak_id,
                    sayfa_yonlendirme=sayfa_yonlendirme,
                    gonderen_id=gonderen_id,
                )
                if result:
                    count += 1
            return count

        except Exception as e:
            print(f"[BildirimService] Rol gönderim hatası: {e}")
            return 0

    @staticmethod
    def departman_gonder(
        departman_id: int,
        baslik: str,
        mesaj: str,
        modul: str = 'SISTEM',
        onem: str = 'NORMAL',
        tip: str = 'BILGI',
        kaynak_tablo: str = None,
        kaynak_id: int = None,
        sayfa_yonlendirme: str = None,
        gonderen_id: int = None,
    ) -> int:
        """
        Belirli bir departmandaki tüm kullanıcılara bildirim gönder.
        Personel tablosundan departman_id üzerinden kullanıcıları bulur.

        Returns:
            Gönderilen bildirim sayısı
        """
        try:
            kullanicilar = execute_query("""
                SELECT k.id
                FROM sistem.kullanicilar k
                INNER JOIN ik.personeller p ON p.id = k.personel_id
                WHERE p.departman_id = ?
                  AND k.aktif_mi = 1
                  AND k.silindi_mi = 0
            """, [departman_id])

            count = 0
            for k in kullanicilar:
                result = BildirimService.gonder(
                    kullanici_id=k['id'],
                    baslik=baslik, mesaj=mesaj, modul=modul,
                    onem=onem, tip=tip,
                    kaynak_tablo=kaynak_tablo, kaynak_id=kaynak_id,
                    sayfa_yonlendirme=sayfa_yonlendirme,
                    gonderen_id=gonderen_id,
                )
                if result:
                    count += 1
            return count

        except Exception as e:
            print(f"[BildirimService] Departman gönderim hatası: {e}")
            return 0

    @staticmethod
    def toplu_gonder(
        kullanici_idler: list,
        baslik: str,
        mesaj: str,
        modul: str = 'SISTEM',
        onem: str = 'NORMAL',
        tip: str = 'BILGI',
        kaynak_tablo: str = None,
        kaynak_id: int = None,
        sayfa_yonlendirme: str = None,
        gonderen_id: int = None,
    ) -> int:
        """
        Birden fazla kullanıcıya bildirim gönder.

        Returns:
            Gönderilen bildirim sayısı
        """
        count = 0
        for kid in kullanici_idler:
            result = BildirimService.gonder(
                kullanici_id=kid,
                baslik=baslik, mesaj=mesaj, modul=modul,
                onem=onem, tip=tip,
                kaynak_tablo=kaynak_tablo, kaynak_id=kaynak_id,
                sayfa_yonlendirme=sayfa_yonlendirme,
                gonderen_id=gonderen_id,
            )
            if result:
                count += 1
        return count

    @staticmethod
    def herkese_gonder(
        baslik: str,
        mesaj: str,
        modul: str = 'SISTEM',
        onem: str = 'NORMAL',
        tip: str = 'BILGI',
        gonderen_id: int = None,
    ) -> int:
        """Tüm aktif kullanıcılara bildirim gönder (duyuru)."""
        try:
            kullanicilar = execute_query(
                "SELECT id FROM sistem.kullanicilar WHERE aktif_mi = 1 AND silindi_mi = 0"
            )
            count = 0
            for k in kullanicilar:
                result = BildirimService.gonder(
                    kullanici_id=k['id'],
                    baslik=baslik, mesaj=mesaj, modul=modul,
                    onem=onem, tip=tip,
                    gonderen_id=gonderen_id,
                )
                if result:
                    count += 1
            return count
        except Exception as e:
            print(f"[BildirimService] Herkese gönderim hatası: {e}")
            return 0

    @staticmethod
    def sablon_gonder(
        kod: str,
        hedef_kullanici_id: int = None,
        hedef_rol_id: int = None,
        hedef_departman_id: int = None,
        parametreler: dict = None,
        kaynak_tablo: str = None,
        kaynak_id: int = None,
        gonderen_id: int = None,
    ) -> int:
        """
        Bildirim tanımı şablonundan bildirim gönder.

        Args:
            kod: Bildirim tanım kodu (IE_YENI, KALITE_UYGUNSUZLUK, vb.)
            hedef_kullanici_id: Hedef kullanıcı (opsiyonel)
            hedef_rol_id: Hedef rol (opsiyonel)
            hedef_departman_id: Hedef departman (opsiyonel)
            parametreler: Şablon parametreleri {'is_emri_no': 'IE-001', ...}
            kaynak_tablo: Kaynak tablo
            kaynak_id: Kaynak kayıt ID
            gonderen_id: Gönderen kullanıcı ID

        Returns:
            Gönderilen bildirim sayısı
        """
        try:
            tanimlar = execute_query(
                "SELECT * FROM sistem.bildirim_tanimlari WHERE kod = ? AND aktif_mi = 1",
                [kod]
            )
            if not tanimlar:
                print(f"[BildirimService] Bildirim tanımı bulunamadı: {kod}")
                return 0

            tanim = tanimlar[0]
            baslik = tanim['baslik']
            mesaj = tanim.get('sablon_mesaj') or tanim.get('aciklama') or baslik
            modul = tanim['modul']
            onem = tanim.get('onem_derecesi', 'NORMAL')
            tip = tanim.get('bildirim_tipi', 'BILGI')
            sayfa = tanim.get('sayfa_yonlendirme')

            # Şablon parametrelerini uygula
            if parametreler:
                for key, value in parametreler.items():
                    mesaj = mesaj.replace('{' + key + '}', str(value))
                    baslik = baslik.replace('{' + key + '}', str(value))

            # Hedef belirleme
            count = 0
            if hedef_kullanici_id:
                result = BildirimService.gonder(
                    kullanici_id=hedef_kullanici_id,
                    baslik=baslik, mesaj=mesaj, modul=modul,
                    onem=onem, tip=tip,
                    kaynak_tablo=kaynak_tablo, kaynak_id=kaynak_id,
                    sayfa_yonlendirme=sayfa,
                    gonderen_id=gonderen_id,
                )
                count = 1 if result else 0
            elif hedef_rol_id:
                count = BildirimService.role_gonder(
                    rol_id=hedef_rol_id,
                    baslik=baslik, mesaj=mesaj, modul=modul,
                    onem=onem, tip=tip,
                    kaynak_tablo=kaynak_tablo, kaynak_id=kaynak_id,
                    sayfa_yonlendirme=sayfa,
                    gonderen_id=gonderen_id,
                )
            elif hedef_departman_id:
                count = BildirimService.departman_gonder(
                    departman_id=hedef_departman_id,
                    baslik=baslik, mesaj=mesaj, modul=modul,
                    onem=onem, tip=tip,
                    kaynak_tablo=kaynak_tablo, kaynak_id=kaynak_id,
                    sayfa_yonlendirme=sayfa,
                    gonderen_id=gonderen_id,
                )
            elif tanim.get('hedef_rol_id'):
                # Tanımda varsayılan hedef rol varsa onu kullan
                count = BildirimService.role_gonder(
                    rol_id=tanim['hedef_rol_id'],
                    baslik=baslik, mesaj=mesaj, modul=modul,
                    onem=onem, tip=tip,
                    kaynak_tablo=kaynak_tablo, kaynak_id=kaynak_id,
                    sayfa_yonlendirme=sayfa,
                    gonderen_id=gonderen_id,
                )

            return count

        except Exception as e:
            print(f"[BildirimService] Şablon gönderim hatası: {e}")
            return 0

    # =========================================================================
    # BİLDİRİM LİSTELEME
    # =========================================================================

    @staticmethod
    def kullanici_bildirimleri(
        kullanici_id: int,
        sadece_okunmamis: bool = False,
        modul: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list:
        """
        Kullanıcının bildirimlerini getir.
        Kullanıcıya direkt gönderilmiş + rolüne gönderilmiş + departmanına
        gönderilmiş bildirimleri birleştirir.
        """
        try:
            # Kullanıcının rol ve departman bilgisini al
            user_info = execute_query("""
                SELECT k.rol_id, p.departman_id
                FROM sistem.kullanicilar k
                LEFT JOIN ik.personeller p ON p.id = k.personel_id
                WHERE k.id = ?
            """, [kullanici_id])

            rol_id = user_info[0]['rol_id'] if user_info else None
            departman_id = user_info[0].get('departman_id') if user_info else None

            # Koşulları oluştur
            kosullar = ["b.aktif_mi = 1"]
            params = []

            # Hedef filtresi: kullanıcıya, rolüne veya departmanına gönderilmiş
            hedef_kosul = ["b.hedef_kullanici_id = ?"]
            params.append(kullanici_id)

            if rol_id:
                hedef_kosul.append("b.hedef_rol_id = ?")
                params.append(rol_id)

            if departman_id:
                hedef_kosul.append("b.hedef_departman_id = ?")
                params.append(departman_id)

            # hedef_kullanici_id NULL = herkese gönderilmiş
            hedef_kosul.append(
                "(b.hedef_kullanici_id IS NULL AND b.hedef_rol_id IS NULL AND b.hedef_departman_id IS NULL)"
            )

            kosullar.append("(" + " OR ".join(hedef_kosul) + ")")

            if sadece_okunmamis:
                kosullar.append("ISNULL(b.okundu_mu, 0) = 0")

            if modul:
                kosullar.append("b.modul = ?")
                params.append(modul)

            where_clause = " AND ".join(kosullar)

            query = f"""
                SELECT
                    b.id, b.baslik, b.mesaj, b.modul, b.onem_derecesi,
                    b.tip, b.kaynak_tablo, b.kaynak_id, b.sayfa_yonlendirme,
                    b.okundu_mu, b.olusturma_tarihi, b.gonderen_id,
                    g.ad + ' ' + g.soyad AS gonderen_adi
                FROM sistem.bildirimler b
                LEFT JOIN sistem.kullanicilar g ON g.id = b.gonderen_id
                WHERE {where_clause}
                ORDER BY ISNULL(b.okundu_mu, 0) ASC, b.olusturma_tarihi DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            params.extend([offset, limit])

            return execute_query(query, params)

        except Exception as e:
            print(f"[BildirimService] Listeleme hatası: {e}")
            return []

    @staticmethod
    def okunmamis_sayisi(kullanici_id: int) -> int:
        """Kullanıcının okunmamış bildirim sayısını döndür."""
        try:
            user_info = execute_query("""
                SELECT k.rol_id, p.departman_id
                FROM sistem.kullanicilar k
                LEFT JOIN ik.personeller p ON p.id = k.personel_id
                WHERE k.id = ?
            """, [kullanici_id])

            rol_id = user_info[0]['rol_id'] if user_info else None
            departman_id = user_info[0].get('departman_id') if user_info else None

            hedef_kosul = ["b.hedef_kullanici_id = ?"]
            params = [kullanici_id]

            if rol_id:
                hedef_kosul.append("b.hedef_rol_id = ?")
                params.append(rol_id)

            if departman_id:
                hedef_kosul.append("b.hedef_departman_id = ?")
                params.append(departman_id)

            hedef_kosul.append(
                "(b.hedef_kullanici_id IS NULL AND b.hedef_rol_id IS NULL AND b.hedef_departman_id IS NULL)"
            )

            where = " OR ".join(hedef_kosul)

            result = execute_query(f"""
                SELECT COUNT(*) AS sayi
                FROM sistem.bildirimler b
                WHERE b.aktif_mi = 1
                  AND ISNULL(b.okundu_mu, 0) = 0
                  AND ({where})
            """, params)

            return result[0]['sayi'] if result else 0

        except Exception as e:
            print(f"[BildirimService] Sayı alma hatası: {e}")
            return 0

    # =========================================================================
    # BİLDİRİM YÖNETİM
    # =========================================================================

    @staticmethod
    def okundu_isaretle(bildirim_id: int, kullanici_id: int = None) -> bool:
        """Bildirimi okundu olarak işaretle."""
        try:
            if not kullanici_id:
                kullanici_id = BildirimService._get_current_user_id()

            execute_non_query("""
                UPDATE sistem.bildirimler
                SET okundu_mu = 1,
                    okunma_tarihi = GETDATE(),
                    okuyan_id = ?
                WHERE id = ? AND ISNULL(okundu_mu, 0) = 0
            """, [kullanici_id, bildirim_id])
            return True
        except Exception as e:
            print(f"[BildirimService] Okundu işaretleme hatası: {e}")
            return False

    @staticmethod
    def tumunu_okundu_isaretle(kullanici_id: int) -> int:
        """Kullanıcının tüm bildirimlerini okundu olarak işaretle."""
        try:
            user_info = execute_query("""
                SELECT k.rol_id, p.departman_id
                FROM sistem.kullanicilar k
                LEFT JOIN ik.personeller p ON p.id = k.personel_id
                WHERE k.id = ?
            """, [kullanici_id])

            rol_id = user_info[0]['rol_id'] if user_info else None
            departman_id = user_info[0].get('departman_id') if user_info else None

            hedef_kosul = ["hedef_kullanici_id = ?"]
            params = [kullanici_id, kullanici_id]  # ilk kullanici_id okuyan_id için

            if rol_id:
                hedef_kosul.append("hedef_rol_id = ?")
                params.append(rol_id)

            if departman_id:
                hedef_kosul.append("hedef_departman_id = ?")
                params.append(departman_id)

            hedef_kosul.append(
                "(hedef_kullanici_id IS NULL AND hedef_rol_id IS NULL AND hedef_departman_id IS NULL)"
            )

            where = " OR ".join(hedef_kosul)

            return execute_non_query(f"""
                UPDATE sistem.bildirimler
                SET okundu_mu = 1,
                    okunma_tarihi = GETDATE(),
                    okuyan_id = ?
                WHERE aktif_mi = 1
                  AND ISNULL(okundu_mu, 0) = 0
                  AND ({where})
            """, params)

        except Exception as e:
            print(f"[BildirimService] Toplu okundu hatası: {e}")
            return 0

    @staticmethod
    def sil(bildirim_id: int) -> bool:
        """Bildirimi sil (soft delete - aktif_mi = 0)."""
        try:
            execute_non_query(
                "UPDATE sistem.bildirimler SET aktif_mi = 0 WHERE id = ?",
                [bildirim_id]
            )
            return True
        except Exception as e:
            print(f"[BildirimService] Silme hatası: {e}")
            return False

    @staticmethod
    def eski_temizle(gun: int = 30) -> int:
        """Belirtilen günden eski ve okunmuş bildirimleri temizle."""
        try:
            return execute_non_query("""
                UPDATE sistem.bildirimler
                SET aktif_mi = 0
                WHERE okundu_mu = 1
                  AND olusturma_tarihi < DATEADD(day, ?, GETDATE())
            """, [-abs(gun)])
        except Exception as e:
            print(f"[BildirimService] Temizleme hatası: {e}")
            return 0

    # =========================================================================
    # TERCİH YÖNETİMİ
    # =========================================================================

    @staticmethod
    def tercih_getir(kullanici_id: int) -> list:
        """Kullanıcının bildirim tercihlerini getir."""
        try:
            return execute_query("""
                SELECT modul, uygulama_ici, email, whatsapp, minimum_onem
                FROM sistem.bildirim_tercihleri
                WHERE kullanici_id = ? AND aktif_mi = 1
            """, [kullanici_id])
        except Exception as e:
            print(f"[BildirimService] Tercih getirme hatası: {e}")
            return []

    @staticmethod
    def tercih_kaydet(
        kullanici_id: int,
        modul: str,
        uygulama_ici: bool = True,
        email: bool = False,
        whatsapp: bool = False,
        minimum_onem: str = 'DUSUK',
    ) -> bool:
        """Kullanıcının bildirim tercihini kaydet/güncelle (MERGE)."""
        try:
            execute_non_query("""
                MERGE sistem.bildirim_tercihleri AS hedef
                USING (SELECT ? AS kullanici_id, ? AS modul) AS kaynak
                ON hedef.kullanici_id = kaynak.kullanici_id AND hedef.modul = kaynak.modul
                WHEN MATCHED THEN
                    UPDATE SET
                        uygulama_ici = ?,
                        email = ?,
                        whatsapp = ?,
                        minimum_onem = ?,
                        guncelleme_tarihi = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (kullanici_id, modul, uygulama_ici, email, whatsapp, minimum_onem)
                    VALUES (?, ?, ?, ?, ?, ?);
            """, [
                kullanici_id, modul,
                uygulama_ici, email, whatsapp, minimum_onem,
                kullanici_id, modul, uygulama_ici, email, whatsapp, minimum_onem,
            ])
            return True
        except Exception as e:
            print(f"[BildirimService] Tercih kaydetme hatası: {e}")
            return False

    # =========================================================================
    # YARDIMCI METODLAR
    # =========================================================================

    @staticmethod
    def _tercih_kontrol(kullanici_id: int, modul: str, onem: str) -> bool:
        """
        Kullanıcının bu modül ve önem seviyesi için bildirim almak
        isteyip istemediğini kontrol eder.
        Tercih kaydı yoksa varsayılan olarak True döner.
        """
        try:
            tercihler = execute_query("""
                SELECT uygulama_ici, minimum_onem
                FROM sistem.bildirim_tercihleri
                WHERE kullanici_id = ? AND modul = ? AND aktif_mi = 1
            """, [kullanici_id, modul])

            if not tercihler:
                return True  # Tercih yoksa bildirim gönder

            tercih = tercihler[0]

            # Uygulama içi kapalıysa gönderme
            if not tercih.get('uygulama_ici', True):
                return False

            # Önem filtresi kontrolü
            min_onem = tercih.get('minimum_onem', 'DUSUK')
            if ONEM_SIRA.get(onem, 3) > ONEM_SIRA.get(min_onem, 4):
                return False

            return True

        except Exception:
            return True  # Hata durumunda varsayılan gönder

    @staticmethod
    def _get_current_user_id() -> Optional[int]:
        """Şu anki aktif kullanıcı ID'sini al."""
        try:
            from core.yetki_manager import YetkiManager
            return YetkiManager._current_user_id
        except Exception:
            return None

    @staticmethod
    def bildirim_getir(bildirim_id: int) -> Optional[dict]:
        """Tek bir bildirimin detayını getir."""
        try:
            sonuc = execute_query("""
                SELECT
                    b.id, b.baslik, b.mesaj, b.modul, b.onem_derecesi,
                    b.tip, b.kaynak_tablo, b.kaynak_id, b.sayfa_yonlendirme,
                    b.okundu_mu, b.olusturma_tarihi, b.gonderen_id,
                    g.ad + ' ' + g.soyad AS gonderen_adi
                FROM sistem.bildirimler b
                LEFT JOIN sistem.kullanicilar g ON g.id = b.gonderen_id
                WHERE b.id = ?
            """, [bildirim_id])
            return sonuc[0] if sonuc else None
        except Exception as e:
            print(f"[BildirimService] Detay hatası: {e}")
            return None
