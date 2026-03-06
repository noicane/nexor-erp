# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Aksiyon Servisi
Aksiyon CRUD islemleri ve bildirim entegrasyonu

Kullanim:
    from core.aksiyon_service import AksiyonService

    # Yeni aksiyon olustur
    aksiyon_id = AksiyonService.olustur(
        baslik="Uygunsuzluk aksiyonu",
        aciklama="8D kapsaminda kök neden analizi yapılacak",
        kategori="DUZELTICI",
        kaynak_modul="KALITE",
        sorumlu_id=15,
        hedef_tarih="2026-03-01"
    )

    # Durum guncelle
    AksiyonService.durum_guncelle(aksiyon_id, 'DEVAM_EDIYOR', yorum="Calismaya baslandi")

    # Yorum ekle
    AksiyonService.yorum_ekle(aksiyon_id, "Kok neden analizi tamamlandi")
"""

import os
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from core.database import execute_query, execute_non_query, get_db_connection


class AksiyonService:
    """Aksiyon CRUD ve bildirim entegrasyon servisi"""

    # =========================================================================
    # OLUSTUR
    # =========================================================================

    @staticmethod
    def olustur(
        baslik: str,
        aciklama: str = None,
        kategori: str = 'GENEL',
        kaynak_modul: str = 'GENEL',
        oncelik: str = 'NORMAL',
        sorumlu_id: int = None,
        sorumlu_departman_id: int = None,
        talep_eden_id: int = None,
        hedef_tarih: str = None,
        kaynak_tablo: str = None,
        kaynak_id: int = None,
        sayfa_yonlendirme: str = None,
    ) -> Optional[int]:
        """
        Yeni aksiyon olustur ve sorumluya bildirim gonder.

        Returns:
            Oluşturulan aksiyon ID veya None
        """
        try:
            olusturan_id = AksiyonService._get_current_user_id()

            conn = get_db_connection()
            cursor = conn.cursor()

            # Aksiyon numarası üret
            cursor.execute("SELECT sistem.fn_yeni_aksiyon_no() AS aksiyon_no")
            aksiyon_no = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO sistem.aksiyonlar
                    (aksiyon_no, baslik, aciklama, kategori, kaynak_modul,
                     oncelik, sorumlu_id, sorumlu_departman_id, talep_eden_id,
                     hedef_tarih, kaynak_tablo, kaynak_id, sayfa_yonlendirme,
                     durum, tamamlanma_orani, aktif_mi, silindi_mi,
                     olusturan_id, olusturma_tarihi, guncelleme_tarihi)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        'BEKLIYOR', 0, 1, 0, ?, GETDATE(), GETDATE())
            """, [
                aksiyon_no, baslik, aciklama, kategori, kaynak_modul,
                oncelik, sorumlu_id, sorumlu_departman_id, talep_eden_id,
                hedef_tarih, kaynak_tablo, kaynak_id, sayfa_yonlendirme,
                olusturan_id,
            ])

            row = cursor.fetchone()
            aksiyon_id = row[0] if row else None
            conn.commit()
            conn.close()

            # NAS klasoru olustur
            if aksiyon_id:
                AksiyonService.klasor_olustur(aksiyon_no)

            # Sorumluya bildirim gonder
            if aksiyon_id and sorumlu_id:
                AksiyonService._bildirim_aksiyon_atandi(
                    aksiyon_id, aksiyon_no, baslik, hedef_tarih, sorumlu_id
                )

            return aksiyon_id

        except Exception as e:
            print(f"[AksiyonService] Olusturma hatasi: {e}")
            return None

    # =========================================================================
    # GUNCELLE
    # =========================================================================

    @staticmethod
    def guncelle(
        aksiyon_id: int,
        baslik: str = None,
        aciklama: str = None,
        kategori: str = None,
        oncelik: str = None,
        sorumlu_id: int = None,
        sorumlu_departman_id: int = None,
        hedef_tarih: str = None,
        tamamlanma_orani: int = None,
    ) -> bool:
        """Aksiyon bilgilerini guncelle."""
        try:
            guncelleyen_id = AksiyonService._get_current_user_id()
            updates = []
            params = []

            if baslik is not None:
                updates.append("baslik = ?")
                params.append(baslik)
            if aciklama is not None:
                updates.append("aciklama = ?")
                params.append(aciklama)
            if kategori is not None:
                updates.append("kategori = ?")
                params.append(kategori)
            if oncelik is not None:
                updates.append("oncelik = ?")
                params.append(oncelik)
            if sorumlu_id is not None:
                updates.append("sorumlu_id = ?")
                params.append(sorumlu_id)
            if sorumlu_departman_id is not None:
                updates.append("sorumlu_departman_id = ?")
                params.append(sorumlu_departman_id)
            if hedef_tarih is not None:
                updates.append("hedef_tarih = ?")
                params.append(hedef_tarih)
            if tamamlanma_orani is not None:
                updates.append("tamamlanma_orani = ?")
                params.append(tamamlanma_orani)

            if not updates:
                return True

            updates.append("guncelleme_tarihi = GETDATE()")
            updates.append("guncelleyen_id = ?")
            params.append(guncelleyen_id)
            params.append(aksiyon_id)

            execute_non_query(
                f"UPDATE sistem.aksiyonlar SET {', '.join(updates)} WHERE id = ?",
                params
            )
            return True

        except Exception as e:
            print(f"[AksiyonService] Guncelleme hatasi: {e}")
            return False

    # =========================================================================
    # DURUM GUNCELLE
    # =========================================================================

    @staticmethod
    def durum_guncelle(
        aksiyon_id: int,
        yeni_durum: str,
        yorum: str = None,
    ) -> bool:
        """
        Aksiyon durumunu guncelle ve yorum ekle.
        Durum degisikliginde otomatik bildirim gonderir.
        """
        try:
            # Mevcut durumu al
            mevcut = execute_query(
                "SELECT durum, aksiyon_no, baslik, sorumlu_id FROM sistem.aksiyonlar WHERE id = ?",
                [aksiyon_id]
            )
            if not mevcut:
                return False

            eski_durum = mevcut[0]['durum']
            aksiyon_no = mevcut[0]['aksiyon_no']
            guncelleyen_id = AksiyonService._get_current_user_id()

            update_parts = [
                "durum = ?", "guncelleme_tarihi = GETDATE()", "guncelleyen_id = ?"
            ]
            params = [yeni_durum, guncelleyen_id]

            # Tamamlandi ise tarihi set et
            if yeni_durum in ('TAMAMLANDI', 'DOGRULANDI'):
                update_parts.append("tamamlanma_tarihi = CAST(GETDATE() AS DATE)")
                if yeni_durum == 'TAMAMLANDI':
                    update_parts.append("tamamlanma_orani = 100")

            if yeni_durum == 'DOGRULANDI':
                update_parts.append("dogrulayan_id = ?")
                # dogrulayan = sorumlu personelden bul
                try:
                    from core.yetki_manager import YetkiManager
                    user = execute_query(
                        "SELECT personel_id FROM sistem.kullanicilar WHERE id = ?",
                        [YetkiManager._current_user_id]
                    )
                    if user and user[0].get('personel_id'):
                        params.append(user[0]['personel_id'])
                    else:
                        params.append(None)
                except Exception:
                    params.append(None)
                update_parts.append("dogrulama_tarihi = CAST(GETDATE() AS DATE)")

            params.append(aksiyon_id)

            execute_non_query(
                f"UPDATE sistem.aksiyonlar SET {', '.join(update_parts)} WHERE id = ?",
                params
            )

            # Yorum / durum degisikligi kaydi ekle
            yorum_metni = yorum or f"Durum degisikligi: {eski_durum} -> {yeni_durum}"
            AksiyonService.yorum_ekle(
                aksiyon_id=aksiyon_id,
                yorum=yorum_metni,
                yorum_tipi='DURUM_DEGISIKLIGI',
                eski_durum=eski_durum,
                yeni_durum=yeni_durum,
            )

            return True

        except Exception as e:
            print(f"[AksiyonService] Durum guncelleme hatasi: {e}")
            return False

    # =========================================================================
    # YORUM
    # =========================================================================

    @staticmethod
    def yorum_ekle(
        aksiyon_id: int,
        yorum: str,
        yorum_tipi: str = 'YORUM',
        eski_durum: str = None,
        yeni_durum: str = None,
    ) -> Optional[int]:
        """Aksiyona yorum ekle."""
        try:
            yazan_id = AksiyonService._get_current_user_id()
            if not yazan_id:
                yazan_id = 1  # Sistem kullanicisi

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sistem.aksiyon_yorumlar
                    (aksiyon_id, yorum, yorum_tipi, eski_durum, yeni_durum, yazan_id)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?)
            """, [aksiyon_id, yorum, yorum_tipi, eski_durum, yeni_durum, yazan_id])

            row = cursor.fetchone()
            yorum_id = row[0] if row else None
            conn.commit()
            conn.close()
            return yorum_id

        except Exception as e:
            print(f"[AksiyonService] Yorum ekleme hatasi: {e}")
            return None

    @staticmethod
    def yorumlari_getir(aksiyon_id: int) -> list:
        """Aksiyonun tum yorumlarini getir."""
        try:
            return execute_query("""
                SELECT y.id, y.yorum, y.yorum_tipi, y.eski_durum, y.yeni_durum,
                       y.olusturma_tarihi,
                       k.ad + ' ' + k.soyad AS yazan_adi
                FROM sistem.aksiyon_yorumlar y
                LEFT JOIN sistem.kullanicilar k ON k.id = y.yazan_id
                WHERE y.aksiyon_id = ?
                ORDER BY y.olusturma_tarihi DESC
            """, [aksiyon_id])
        except Exception as e:
            print(f"[AksiyonService] Yorum getirme hatasi: {e}")
            return []

    # =========================================================================
    # SORGULAMA
    # =========================================================================

    @staticmethod
    def getir(aksiyon_id: int) -> Optional[dict]:
        """Tek aksiyonun detayini getir."""
        try:
            result = execute_query(
                "SELECT * FROM sistem.vw_aksiyon_ozet WHERE id = ?",
                [aksiyon_id]
            )
            return result[0] if result else None
        except Exception as e:
            print(f"[AksiyonService] Detay hatasi: {e}")
            return None

    @staticmethod
    def sil(aksiyon_id: int) -> bool:
        """Aksiyonu soft delete yap."""
        try:
            silen_id = AksiyonService._get_current_user_id()
            execute_non_query("""
                UPDATE sistem.aksiyonlar
                SET silindi_mi = 1, silinme_tarihi = GETDATE(),
                    silen_id = ?, aktif_mi = 0
                WHERE id = ?
            """, [silen_id, aksiyon_id])
            return True
        except Exception as e:
            print(f"[AksiyonService] Silme hatasi: {e}")
            return False

    # =========================================================================
    # DOSYA / KLASOR ISLEMLERI
    # =========================================================================

    @staticmethod
    def _get_aksiyon_base_path() -> str:
        """NAS uzerindeki aksiyon temel yolunu dondur."""
        try:
            from config import NAS_PATHS
            return NAS_PATHS.get('aksiyon_path', '')
        except Exception:
            return ''

    @staticmethod
    def klasor_olustur(aksiyon_no: str) -> Optional[str]:
        """
        NAS uzerinde aksiyon klasoru olustur.
        Returns: Olusturulan klasor yolu veya None
        """
        try:
            base = AksiyonService._get_aksiyon_base_path()
            if not base:
                print("[AksiyonService] aksiyon_path yapilandirilmamis")
                return None

            klasor = os.path.join(base, aksiyon_no)
            os.makedirs(klasor, exist_ok=True)
            return klasor
        except Exception as e:
            print(f"[AksiyonService] Klasor olusturma hatasi: {e}")
            return None

    @staticmethod
    def dosya_yukle(
        aksiyon_id: int,
        aksiyon_no: str,
        kaynak_dosya: str,
        aciklama: str = None,
    ) -> Optional[int]:
        """
        Dosyayi NAS'a kopyala ve DB'ye kaydet.
        Returns: Oluşturulan ek ID veya None
        """
        try:
            yukleyen_id = AksiyonService._get_current_user_id()
            if not yukleyen_id:
                yukleyen_id = 1

            # Klasoru garantile
            klasor = AksiyonService.klasor_olustur(aksiyon_no)
            if not klasor:
                print("[AksiyonService] Hedef klasor olusturulamadi")
                return None

            kaynak = Path(kaynak_dosya)
            dosya_adi = kaynak.name
            dosya_tipi = kaynak.suffix.lower()
            dosya_boyutu = kaynak.stat().st_size

            # Ayni isimde dosya varsa yeniden adlandir
            hedef = os.path.join(klasor, dosya_adi)
            if os.path.exists(hedef):
                stem = kaynak.stem
                counter = 1
                while os.path.exists(hedef):
                    dosya_adi = f"{stem}_{counter}{dosya_tipi}"
                    hedef = os.path.join(klasor, dosya_adi)
                    counter += 1

            # Dosyayi kopyala
            shutil.copy2(kaynak_dosya, hedef)

            # DB kaydi
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sistem.aksiyon_ekler
                    (aksiyon_id, dosya_adi, dosya_yolu, dosya_boyutu,
                     dosya_tipi, aciklama, yukleyen_id)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                aksiyon_id, dosya_adi, hedef, dosya_boyutu,
                dosya_tipi, aciklama, yukleyen_id
            ])
            row = cursor.fetchone()
            ek_id = row[0] if row else None
            conn.commit()
            conn.close()

            return ek_id

        except Exception as e:
            print(f"[AksiyonService] Dosya yukleme hatasi: {e}")
            return None

    @staticmethod
    def ekleri_getir(aksiyon_id: int) -> list:
        """Aksiyonun dosya eklerini getir."""
        try:
            return execute_query("""
                SELECT e.id, e.dosya_adi, e.dosya_yolu, e.dosya_boyutu,
                       e.dosya_tipi, e.aciklama, e.olusturma_tarihi,
                       k.ad + ' ' + k.soyad AS yukleyen_adi
                FROM sistem.aksiyon_ekler e
                LEFT JOIN sistem.kullanicilar k ON k.id = e.yukleyen_id
                WHERE e.aksiyon_id = ? AND e.silindi_mi = 0
                ORDER BY e.olusturma_tarihi DESC
            """, [aksiyon_id])
        except Exception as e:
            print(f"[AksiyonService] Ek getirme hatasi: {e}")
            return []

    @staticmethod
    def ek_sil(ek_id: int) -> bool:
        """Eki soft delete yap."""
        try:
            silen_id = AksiyonService._get_current_user_id()
            execute_non_query("""
                UPDATE sistem.aksiyon_ekler
                SET silindi_mi = 1, silinme_tarihi = GETDATE(), silen_id = ?
                WHERE id = ?
            """, [silen_id, ek_id])
            return True
        except Exception as e:
            print(f"[AksiyonService] Ek silme hatasi: {e}")
            return False

    # =========================================================================
    # YARDIMCI
    # =========================================================================

    @staticmethod
    def _get_current_user_id() -> Optional[int]:
        try:
            from core.yetki_manager import YetkiManager
            return YetkiManager._current_user_id
        except Exception:
            return None

    @staticmethod
    def _bildirim_aksiyon_atandi(
        aksiyon_id: int, aksiyon_no: str, baslik: str,
        hedef_tarih: str, sorumlu_id: int,
    ):
        """Aksiyon atandığında sorumluya bildirim gönder."""
        try:
            # Sorumlu personelin kullanıcı ID'sini bul
            result = execute_query("""
                SELECT k.id
                FROM sistem.kullanicilar k
                WHERE k.personel_id = ? AND k.aktif_mi = 1 AND k.silindi_mi = 0
            """, [sorumlu_id])

            if result:
                from core.bildirim_tetikleyici import BildirimTetikleyici
                BildirimTetikleyici.aksiyon_atandi(
                    aksiyon_id=aksiyon_id,
                    aksiyon_no=aksiyon_no,
                    baslik=baslik,
                    hedef_tarih=str(hedef_tarih) if hedef_tarih else 'Belirtilmedi',
                    sorumlu_kullanici_id=result[0]['id'],
                )
        except Exception as e:
            print(f"[AksiyonService] Bildirim gonderim hatasi: {e}")
