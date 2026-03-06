# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İş Emri Servisi
İş emri sorgulama, durum yönetimi ve akış kontrolü
"""

from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum


class IsEmriDurum(Enum):
    """İş emri durumları"""
    BEKLIYOR = "BEKLIYOR"       # Oluşturuldu, henüz planlanmadı
    PLANLI = "PLANLI"           # Planlama yapıldı, üretim bekliyor
    URETIMDE = "URETIMDE"       # Üretime başlandı
    KALITE_BEKLIYOR = "KALITE_BEKLIYOR"  # Final kalite kontrolü bekliyor
    TAMAMLANDI = "TAMAMLANDI"   # Tamamlandı, sevke hazır
    IPTAL = "IPTAL"             # İptal edildi


@dataclass
class IsEmri:
    """İş emri detay bilgisi"""
    id: int
    is_emri_no: str
    tarih: date
    termin_tarihi: Optional[date]
    durum: str
    oncelik: int
    
    # Müşteri bilgileri
    cari_id: int
    cari_unvani: str
    
    # Ürün bilgileri
    urun_id: int
    stok_kodu: str
    stok_adi: str
    kaplama_tipi: Optional[str]
    
    # Miktar bilgileri
    planlanan_miktar: float
    uretilen_miktar: float
    fire_miktar: float
    sevk_miktar: float
    kalan_miktar: float
    
    # Üretim bilgileri
    hat_id: Optional[int]
    hat_adi: Optional[str]
    toplam_bara: int
    tahmini_sure_dk: int
    
    # Lot bilgileri
    tahsis_lot_sayisi: int
    tahsis_miktar: float


@dataclass
class IsEmriOzet:
    """İş emri özet bilgisi (liste için)"""
    id: int
    is_emri_no: str
    cari_unvani: str
    stok_kodu: str
    stok_adi: str
    planlanan_miktar: float
    durum: str
    termin_tarihi: Optional[date]
    oncelik: int
    gecikme_gun: int


class IsEmriServisi:
    """
    İş Emri Servisi
    
    Kullanım:
        servis = IsEmriServisi(conn)
        
        # Tek iş emri
        ie = servis.get_is_emri(123)
        
        # Bekleyen iş emirleri
        liste = servis.get_bekleyen_is_emirleri()
        
        # Durum değiştir
        servis.durum_degistir(123, IsEmriDurum.PLANLI)
    """
    
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
    
    # =========================================================================
    # TEK KAYIT SORGULARI
    # =========================================================================
    
    def get_is_emri(self, is_emri_id: int) -> Optional[IsEmri]:
        """ID ile iş emri getir"""
        self.cursor.execute("""
            SELECT 
                ie.id, ie.is_emri_no, ie.tarih, ie.termin_tarihi, ie.durum, ie.oncelik,
                ie.cari_id, ie.cari_unvani,
                ie.urun_id, ie.stok_kodu, ie.stok_adi, ie.kaplama_tipi,
                ie.planlanan_miktar,
                ISNULL(ie.uretilen_miktar, 0),
                ISNULL(ie.fire_miktar, 0),
                ISNULL(ie.sevk_miktar, 0),
                ie.planlanan_miktar - ISNULL(ie.uretilen_miktar, 0) - ISNULL(ie.fire_miktar, 0),
                ie.hat_id, h.hat_adi,
                ISNULL(ie.toplam_bara, 0),
                ISNULL(ie.tahmini_sure_dk, 0),
                (SELECT COUNT(*) FROM siparis.is_emri_stok_hareketi WHERE is_emri_id = ie.id),
                (SELECT ISNULL(SUM(tahsis_miktar), 0) FROM siparis.is_emri_stok_hareketi WHERE is_emri_id = ie.id)
            FROM siparis.is_emirleri ie
            LEFT JOIN tanim.hatlar h ON ie.hat_id = h.id
            WHERE ie.id = ? AND ie.silindi_mi = 0
        """, (is_emri_id,))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return IsEmri(
            id=row[0],
            is_emri_no=row[1],
            tarih=row[2],
            termin_tarihi=row[3],
            durum=row[4],
            oncelik=row[5] or 5,
            cari_id=row[6],
            cari_unvani=row[7] or '',
            urun_id=row[8],
            stok_kodu=row[9] or '',
            stok_adi=row[10] or '',
            kaplama_tipi=row[11],
            planlanan_miktar=float(row[12]) if row[12] else 0,
            uretilen_miktar=float(row[13]) if row[13] else 0,
            fire_miktar=float(row[14]) if row[14] else 0,
            sevk_miktar=float(row[15]) if row[15] else 0,
            kalan_miktar=float(row[16]) if row[16] else 0,
            hat_id=row[17],
            hat_adi=row[18],
            toplam_bara=row[19] or 0,
            tahmini_sure_dk=row[20] or 0,
            tahsis_lot_sayisi=row[21] or 0,
            tahsis_miktar=float(row[22]) if row[22] else 0
        )
    
    def get_is_emri_by_no(self, is_emri_no: str) -> Optional[IsEmri]:
        """İş emri numarası ile getir"""
        self.cursor.execute("""
            SELECT id FROM siparis.is_emirleri 
            WHERE is_emri_no = ? AND silindi_mi = 0
        """, (is_emri_no,))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return self.get_is_emri(row[0])
    
    # =========================================================================
    # LİSTE SORGULARI
    # =========================================================================
    
    def get_is_emirleri(
        self,
        durum: str = None,
        durumlar: List[str] = None,
        cari_id: int = None,
        hat_id: int = None,
        tarih_baslangic: date = None,
        tarih_bitis: date = None,
        termin_baslangic: date = None,
        termin_bitis: date = None,
        limit: int = 200
    ) -> List[IsEmriOzet]:
        """
        İş emirlerini listele
        
        Args:
            durum: Tek durum filtresi
            durumlar: Birden fazla durum ['BEKLIYOR', 'PLANLI']
            cari_id: Müşteri filtresi
            hat_id: Hat filtresi
            tarih_baslangic/bitis: Oluşturma tarihi aralığı
            termin_baslangic/bitis: Termin tarihi aralığı
            limit: Max kayıt
        """
        sql = """
            SELECT TOP (?)
                ie.id, ie.is_emri_no, ie.cari_unvani,
                ie.stok_kodu, ie.stok_adi, ie.planlanan_miktar,
                ie.durum, ie.termin_tarihi, ie.oncelik,
                CASE 
                    WHEN ie.termin_tarihi < CAST(GETDATE() AS DATE) AND ie.durum NOT IN ('TAMAMLANDI', 'IPTAL')
                    THEN DATEDIFF(DAY, ie.termin_tarihi, GETDATE())
                    ELSE 0 
                END as gecikme_gun
            FROM siparis.is_emirleri ie
            WHERE ie.silindi_mi = 0
        """
        params = [limit]
        
        if durum:
            sql += " AND ie.durum = ?"
            params.append(durum)
        elif durumlar:
            placeholders = ','.join(['?' for _ in durumlar])
            sql += f" AND ie.durum IN ({placeholders})"
            params.extend(durumlar)
        
        if cari_id:
            sql += " AND ie.cari_id = ?"
            params.append(cari_id)
        
        if hat_id:
            sql += " AND ie.hat_id = ?"
            params.append(hat_id)
        
        if tarih_baslangic:
            sql += " AND ie.tarih >= ?"
            params.append(tarih_baslangic)
        
        if tarih_bitis:
            sql += " AND ie.tarih <= ?"
            params.append(tarih_bitis)
        
        if termin_baslangic:
            sql += " AND ie.termin_tarihi >= ?"
            params.append(termin_baslangic)
        
        if termin_bitis:
            sql += " AND ie.termin_tarihi <= ?"
            params.append(termin_bitis)
        
        sql += " ORDER BY ie.oncelik ASC, ie.termin_tarihi ASC, ie.tarih ASC"
        
        self.cursor.execute(sql, params)
        
        return [
            IsEmriOzet(
                id=row[0],
                is_emri_no=row[1],
                cari_unvani=row[2] or '',
                stok_kodu=row[3] or '',
                stok_adi=row[4] or '',
                planlanan_miktar=float(row[5]) if row[5] else 0,
                durum=row[6],
                termin_tarihi=row[7],
                oncelik=row[8] or 5,
                gecikme_gun=row[9] or 0
            )
            for row in self.cursor.fetchall()
        ]
    
    def get_bekleyen_is_emirleri(self, cari_id: int = None) -> List[IsEmriOzet]:
        """Bekleyen (planlanmamış) iş emirleri"""
        return self.get_is_emirleri(durum='BEKLIYOR', cari_id=cari_id)
    
    def get_planli_is_emirleri(self, hat_id: int = None) -> List[IsEmriOzet]:
        """Planlı (üretim bekleyen) iş emirleri"""
        return self.get_is_emirleri(durum='PLANLI', hat_id=hat_id)
    
    def get_uretimde_is_emirleri(self, hat_id: int = None) -> List[IsEmriOzet]:
        """Üretimde olan iş emirleri"""
        return self.get_is_emirleri(durum='URETIMDE', hat_id=hat_id)
    
    def get_geciken_is_emirleri(self) -> List[IsEmriOzet]:
        """Termini geçmiş iş emirleri"""
        self.cursor.execute("""
            SELECT 
                ie.id, ie.is_emri_no, ie.cari_unvani,
                ie.stok_kodu, ie.stok_adi, ie.planlanan_miktar,
                ie.durum, ie.termin_tarihi, ie.oncelik,
                DATEDIFF(DAY, ie.termin_tarihi, GETDATE()) as gecikme_gun
            FROM siparis.is_emirleri ie
            WHERE ie.silindi_mi = 0
            AND ie.termin_tarihi < CAST(GETDATE() AS DATE)
            AND ie.durum NOT IN ('TAMAMLANDI', 'IPTAL')
            ORDER BY gecikme_gun DESC, ie.oncelik ASC
        """)
        
        return [
            IsEmriOzet(
                id=row[0],
                is_emri_no=row[1],
                cari_unvani=row[2] or '',
                stok_kodu=row[3] or '',
                stok_adi=row[4] or '',
                planlanan_miktar=float(row[5]) if row[5] else 0,
                durum=row[6],
                termin_tarihi=row[7],
                oncelik=row[8] or 5,
                gecikme_gun=row[9] or 0
            )
            for row in self.cursor.fetchall()
        ]
    
    # =========================================================================
    # DURUM YÖNETİMİ
    # =========================================================================
    
    def durum_degistir(
        self,
        is_emri_id: int,
        yeni_durum: IsEmriDurum,
        kullanici_id: int = None,
        aciklama: str = None
    ) -> tuple:
        """
        İş emri durumunu değiştir
        
        Returns:
            (basarili: bool, mesaj: str)
        """
        # Mevcut durumu al
        ie = self.get_is_emri(is_emri_id)
        if not ie:
            return (False, "İş emri bulunamadı")
        
        eski_durum = ie.durum
        
        # Geçiş kuralları kontrolü
        gecerli = self._durum_gecisi_gecerli_mi(eski_durum, yeni_durum.value)
        if not gecerli:
            return (False, f"Geçersiz durum geçişi: {eski_durum} → {yeni_durum.value}")
        
        # Durumu güncelle
        self.cursor.execute("""
            UPDATE siparis.is_emirleri
            SET durum = ?, guncelleme_tarihi = GETDATE()
            WHERE id = ?
        """, (yeni_durum.value, is_emri_id))
        
        # Log kaydı (opsiyonel)
        if kullanici_id:
            self.cursor.execute("""
                INSERT INTO sistem.islem_log 
                (tablo_adi, kayit_id, islem_tipi, eski_deger, yeni_deger, kullanici_id, aciklama)
                VALUES ('siparis.is_emirleri', ?, 'DURUM_DEGISIKLIGI', ?, ?, ?, ?)
            """, (is_emri_id, eski_durum, yeni_durum.value, kullanici_id, aciklama))
        
        return (True, f"Durum değiştirildi: {eski_durum} → {yeni_durum.value}")
    
    def _durum_gecisi_gecerli_mi(self, eski: str, yeni: str) -> bool:
        """Durum geçiş kurallarını kontrol et"""
        # İzin verilen geçişler
        gecisler = {
            'BEKLIYOR': ['PLANLI', 'IPTAL'],
            'PLANLI': ['BEKLIYOR', 'URETIMDE', 'IPTAL'],
            'URETIMDE': ['PLANLI', 'KALITE_BEKLIYOR', 'TAMAMLANDI', 'IPTAL'],
            'KALITE_BEKLIYOR': ['URETIMDE', 'TAMAMLANDI', 'IPTAL'],
            'TAMAMLANDI': [],  # Tamamlanan değiştirilemez
            'IPTAL': []  # İptal değiştirilemez
        }
        
        return yeni in gecisler.get(eski, [])
    
    # =========================================================================
    # ÖZET VE İSTATİSTİK
    # =========================================================================
    
    def get_dashboard_ozet(self) -> Dict:
        """Dashboard için özet bilgiler"""
        self.cursor.execute("""
            SELECT 
                COUNT(CASE WHEN durum = 'BEKLIYOR' THEN 1 END) as bekleyen,
                COUNT(CASE WHEN durum = 'PLANLI' THEN 1 END) as planli,
                COUNT(CASE WHEN durum = 'URETIMDE' THEN 1 END) as uretimde,
                COUNT(CASE WHEN durum = 'TAMAMLANDI' AND tarih >= DATEADD(DAY, -7, GETDATE()) THEN 1 END) as bu_hafta_tamamlanan,
                COUNT(CASE WHEN termin_tarihi < CAST(GETDATE() AS DATE) AND durum NOT IN ('TAMAMLANDI', 'IPTAL') THEN 1 END) as geciken,
                SUM(CASE WHEN durum IN ('BEKLIYOR', 'PLANLI', 'URETIMDE') THEN planlanan_miktar ELSE 0 END) as toplam_bekleyen_miktar
            FROM siparis.is_emirleri
            WHERE silindi_mi = 0
        """)
        
        row = self.cursor.fetchone()
        return {
            'bekleyen': row[0] or 0,
            'planli': row[1] or 0,
            'uretimde': row[2] or 0,
            'bu_hafta_tamamlanan': row[3] or 0,
            'geciken': row[4] or 0,
            'toplam_bekleyen_miktar': float(row[5]) if row[5] else 0
        }
    
    def get_musteri_ozet(self, cari_id: int) -> Dict:
        """Müşteri bazlı iş emri özeti"""
        self.cursor.execute("""
            SELECT 
                COUNT(*) as toplam_is_emri,
                COUNT(CASE WHEN durum IN ('BEKLIYOR', 'PLANLI', 'URETIMDE') THEN 1 END) as aktif,
                COUNT(CASE WHEN durum = 'TAMAMLANDI' THEN 1 END) as tamamlanan,
                SUM(CASE WHEN durum IN ('BEKLIYOR', 'PLANLI', 'URETIMDE') THEN planlanan_miktar ELSE 0 END) as bekleyen_miktar,
                MIN(CASE WHEN durum IN ('BEKLIYOR', 'PLANLI', 'URETIMDE') THEN termin_tarihi END) as en_yakin_termin
            FROM siparis.is_emirleri
            WHERE cari_id = ? AND silindi_mi = 0
        """, (cari_id,))
        
        row = self.cursor.fetchone()
        return {
            'toplam_is_emri': row[0] or 0,
            'aktif': row[1] or 0,
            'tamamlanan': row[2] or 0,
            'bekleyen_miktar': float(row[3]) if row[3] else 0,
            'en_yakin_termin': row[4]
        }
    
    # =========================================================================
    # YARDIMCI METODLAR
    # =========================================================================
    
    def miktar_guncelle(
        self,
        is_emri_id: int,
        uretilen: float = None,
        fire: float = None,
        sevk: float = None
    ):
        """İş emri miktar alanlarını güncelle"""
        updates = []
        params = []
        
        if uretilen is not None:
            updates.append("uretilen_miktar = ISNULL(uretilen_miktar, 0) + ?")
            params.append(uretilen)
        
        if fire is not None:
            updates.append("fire_miktar = ISNULL(fire_miktar, 0) + ?")
            params.append(fire)
        
        if sevk is not None:
            updates.append("sevk_miktar = ISNULL(sevk_miktar, 0) + ?")
            params.append(sevk)
        
        if updates:
            updates.append("guncelleme_tarihi = GETDATE()")
            sql = f"UPDATE siparis.is_emirleri SET {', '.join(updates)} WHERE id = ?"
            params.append(is_emri_id)
            self.cursor.execute(sql, params)
    
    def lot_tahsis_kontrol(self, is_emri_id: int) -> Dict:
        """İş emrine tahsis edilen lotların durumu"""
        self.cursor.execute("""
            SELECT 
                COUNT(*) as lot_sayisi,
                SUM(tahsis_miktar) as tahsis_toplam,
                SUM(cikis_miktar) as cikis_toplam,
                SUM(uretilen_miktar) as uretilen_toplam,
                SUM(fire_miktar) as fire_toplam,
                COUNT(CASE WHEN durum = 'TAHSIS' THEN 1 END) as tahsis_bekleyen,
                COUNT(CASE WHEN durum = 'CIKTI' THEN 1 END) as cikis_yapilan,
                COUNT(CASE WHEN durum = 'TAMAMLANDI' THEN 1 END) as tamamlanan
            FROM siparis.is_emri_stok_hareketi
            WHERE is_emri_id = ?
        """, (is_emri_id,))
        
        row = self.cursor.fetchone()
        return {
            'lot_sayisi': row[0] or 0,
            'tahsis_toplam': float(row[1]) if row[1] else 0,
            'cikis_toplam': float(row[2]) if row[2] else 0,
            'uretilen_toplam': float(row[3]) if row[3] else 0,
            'fire_toplam': float(row[4]) if row[4] else 0,
            'tahsis_bekleyen': row[5] or 0,
            'cikis_yapilan': row[6] or 0,
            'tamamlanan': row[7] or 0
        }
