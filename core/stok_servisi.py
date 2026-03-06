# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Stok Servisi
Stok sorgulama, bakiye kontrolü ve yardımcı fonksiyonlar

Bu servis OKUMA işlemleri için kullanılır.
YAZMA işlemleri HareketMotoru üzerinden yapılmalıdır.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, date


@dataclass
class StokBakiye:
    """Stok bakiye detay bilgisi"""
    id: int
    lot_no: str
    parent_lot_no: Optional[str]
    urun_id: int
    stok_kodu: str
    stok_adi: str
    miktar: float
    rezerve_miktar: float
    kullanilabilir_miktar: float
    birim: str
    depo_id: int
    depo_kodu: str
    depo_adi: str
    depo_tipi: str
    depo_kategorisi: str
    kalite_durumu: str
    uretim_durumu: Optional[str]
    bloke_mi: bool
    cari_unvani: Optional[str]
    kaplama_tipi: Optional[str]
    giris_tarihi: Optional[datetime]
    palet_no: Optional[int]
    toplam_palet: Optional[int]


@dataclass
class StokOzet:
    """Ürün bazlı stok özeti"""
    urun_id: int
    stok_kodu: str
    stok_adi: str
    toplam_miktar: float
    rezerve_miktar: float
    kullanilabilir_miktar: float
    lot_sayisi: int
    depo_sayisi: int


class StokServisi:
    """
    Stok Sorgulama Servisi
    
    Kullanım:
        servis = StokServisi(conn)
        
        # Tek bakiye
        bakiye = servis.get_bakiye(stok_bakiye_id=123)
        
        # Lot ile sorgula
        bakiye = servis.get_bakiye_by_lot("LOT-2501-0001-01")
        
        # Kullanılabilir stoklar
        stoklar = servis.get_kullanilabilir_stoklar(
            kalite_durumu='ONAY',
            depo_kategorisi='DEPO'
        )
    """
    
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
    
    # =========================================================================
    # TEK KAYIT SORGULARI
    # =========================================================================
    
    def get_bakiye(self, stok_bakiye_id: int) -> Optional[StokBakiye]:
        """ID ile stok bakiye getir"""
        self.cursor.execute("""
            SELECT 
                sb.id, sb.lot_no, sb.parent_lot_no, sb.urun_id,
                ISNULL(sb.stok_kodu, u.urun_kodu) as stok_kodu,
                ISNULL(sb.stok_adi, u.urun_adi) as stok_adi,
                sb.miktar, ISNULL(sb.rezerve_miktar, 0),
                sb.miktar - ISNULL(sb.rezerve_miktar, 0),
                ISNULL(sb.birim, 'ADET'),
                sb.depo_id, d.kod, d.ad,
                dt.kod, dt.kategori,
                ISNULL(sb.kalite_durumu_v2, sb.kalite_durumu),
                sb.uretim_durumu,
                ISNULL(sb.bloke_mi, 0),
                sb.cari_unvani, sb.kaplama_tipi,
                sb.giris_tarihi, sb.palet_no, sb.toplam_palet
            FROM stok.stok_bakiye sb
            LEFT JOIN stok.urunler u ON sb.urun_id = u.id
            LEFT JOIN tanim.depolar d ON sb.depo_id = d.id
            LEFT JOIN tanim.depo_tipleri dt ON d.depo_tipi_id = dt.id
            WHERE sb.id = ?
        """, (stok_bakiye_id,))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return self._row_to_bakiye(row)
    
    def get_bakiye_by_lot(self, lot_no: str) -> Optional[StokBakiye]:
        """Lot numarası ile stok bakiye getir"""
        self.cursor.execute("""
            SELECT 
                sb.id, sb.lot_no, sb.parent_lot_no, sb.urun_id,
                ISNULL(sb.stok_kodu, u.urun_kodu),
                ISNULL(sb.stok_adi, u.urun_adi),
                sb.miktar, ISNULL(sb.rezerve_miktar, 0),
                sb.miktar - ISNULL(sb.rezerve_miktar, 0),
                ISNULL(sb.birim, 'ADET'),
                sb.depo_id, d.kod, d.ad,
                dt.kod, dt.kategori,
                ISNULL(sb.kalite_durumu_v2, sb.kalite_durumu),
                sb.uretim_durumu,
                ISNULL(sb.bloke_mi, 0),
                sb.cari_unvani, sb.kaplama_tipi,
                sb.giris_tarihi, sb.palet_no, sb.toplam_palet
            FROM stok.stok_bakiye sb
            LEFT JOIN stok.urunler u ON sb.urun_id = u.id
            LEFT JOIN tanim.depolar d ON sb.depo_id = d.id
            LEFT JOIN tanim.depo_tipleri dt ON d.depo_tipi_id = dt.id
            WHERE sb.lot_no = ?
        """, (lot_no,))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return self._row_to_bakiye(row)
    
    # =========================================================================
    # LİSTE SORGULARI
    # =========================================================================
    
    def get_kullanilabilir_stoklar(
        self,
        kalite_durumu: str = 'ONAY',
        depo_kategorisi: str = None,
        depo_id: int = None,
        urun_id: int = None,
        cari_unvani: str = None,
        min_miktar: float = 0,
        limit: int = 500
    ) -> List[StokBakiye]:
        """
        Kullanılabilir stokları getir
        
        Args:
            kalite_durumu: 'ONAY', 'BEKLIYOR', 'RED', 'SARTLI' veya None (tümü)
            depo_kategorisi: 'GIRIS', 'KALITE', 'DEPO', 'URETIM', 'CIKIS' veya None
            depo_id: Belirli depo
            urun_id: Belirli ürün
            cari_unvani: Müşteri filtresi
            min_miktar: Minimum kullanılabilir miktar
            limit: Max kayıt sayısı
        """
        sql = """
            SELECT TOP (?)
                sb.id, sb.lot_no, sb.parent_lot_no, sb.urun_id,
                ISNULL(sb.stok_kodu, u.urun_kodu),
                ISNULL(sb.stok_adi, u.urun_adi),
                sb.miktar, ISNULL(sb.rezerve_miktar, 0),
                sb.miktar - ISNULL(sb.rezerve_miktar, 0),
                ISNULL(sb.birim, 'ADET'),
                sb.depo_id, d.kod, d.ad,
                dt.kod, dt.kategori,
                ISNULL(sb.kalite_durumu_v2, sb.kalite_durumu),
                sb.uretim_durumu,
                ISNULL(sb.bloke_mi, 0),
                sb.cari_unvani, sb.kaplama_tipi,
                sb.giris_tarihi, sb.palet_no, sb.toplam_palet
            FROM stok.stok_bakiye sb
            LEFT JOIN stok.urunler u ON sb.urun_id = u.id
            LEFT JOIN tanim.depolar d ON sb.depo_id = d.id
            LEFT JOIN tanim.depo_tipleri dt ON d.depo_tipi_id = dt.id
            WHERE sb.miktar > 0
            AND ISNULL(sb.bloke_mi, 0) = 0
            AND (sb.miktar - ISNULL(sb.rezerve_miktar, 0)) > ?
        """
        params = [limit, min_miktar]
        
        if kalite_durumu:
            sql += " AND ISNULL(sb.kalite_durumu_v2, sb.kalite_durumu) = ?"
            params.append(kalite_durumu)
        
        if depo_kategorisi:
            sql += " AND dt.kategori = ?"
            params.append(depo_kategorisi)
        
        if depo_id:
            sql += " AND sb.depo_id = ?"
            params.append(depo_id)
        
        if urun_id:
            sql += " AND sb.urun_id = ?"
            params.append(urun_id)
        
        if cari_unvani:
            sql += " AND sb.cari_unvani LIKE ?"
            params.append(f"%{cari_unvani}%")
        
        sql += " ORDER BY sb.giris_tarihi ASC"  # FIFO
        
        self.cursor.execute(sql, params)
        
        return [self._row_to_bakiye(row) for row in self.cursor.fetchall()]
    
    def get_is_emri_stoklari(self, is_emri_id: int) -> List[Dict]:
        """İş emrine tahsis edilmiş stokları getir"""
        self.cursor.execute("""
            SELECT 
                iesh.id, iesh.stok_bakiye_id, iesh.lot_no,
                iesh.tahsis_miktar, iesh.cikis_miktar, iesh.uretilen_miktar,
                iesh.fire_miktar, iesh.durum, iesh.hat_id,
                sb.stok_kodu, sb.stok_adi, sb.miktar as bakiye_miktar,
                d.kod as depo_kodu, d.ad as depo_adi
            FROM siparis.is_emri_stok_hareketi iesh
            JOIN stok.stok_bakiye sb ON iesh.stok_bakiye_id = sb.id
            LEFT JOIN tanim.depolar d ON sb.depo_id = d.id
            WHERE iesh.is_emri_id = ?
            ORDER BY iesh.tahsis_zamani
        """, (is_emri_id,))
        
        return [
            {
                'id': row[0],
                'stok_bakiye_id': row[1],
                'lot_no': row[2],
                'tahsis_miktar': float(row[3]) if row[3] else 0,
                'cikis_miktar': float(row[4]) if row[4] else 0,
                'uretilen_miktar': float(row[5]) if row[5] else 0,
                'fire_miktar': float(row[6]) if row[6] else 0,
                'durum': row[7],
                'hat_id': row[8],
                'stok_kodu': row[9],
                'stok_adi': row[10],
                'bakiye_miktar': float(row[11]) if row[11] else 0,
                'depo_kodu': row[12],
                'depo_adi': row[13]
            }
            for row in self.cursor.fetchall()
        ]
    
    def get_depo_stoklari(self, depo_id: int) -> List[StokBakiye]:
        """Belirli depodaki tüm stokları getir"""
        return self.get_kullanilabilir_stoklar(
            depo_id=depo_id,
            kalite_durumu=None,  # Tüm kalite durumları
            min_miktar=-999999   # Sıfır ve negatif dahil
        )
    
    # =========================================================================
    # ÖZET SORGULARI
    # =========================================================================
    
    def get_stok_ozet(self, urun_id: int = None, stok_kodu: str = None) -> Optional[StokOzet]:
        """Ürün bazlı stok özeti"""
        if not urun_id and not stok_kodu:
            return None
        
        where = "u.id = ?" if urun_id else "u.urun_kodu = ?"
        param = urun_id if urun_id else stok_kodu
        
        self.cursor.execute(f"""
            SELECT 
                u.id, u.urun_kodu, u.urun_adi,
                SUM(sb.miktar) as toplam,
                SUM(ISNULL(sb.rezerve_miktar, 0)) as rezerve,
                SUM(sb.miktar - ISNULL(sb.rezerve_miktar, 0)) as kullanilabilir,
                COUNT(DISTINCT sb.lot_no) as lot_sayisi,
                COUNT(DISTINCT sb.depo_id) as depo_sayisi
            FROM stok.stok_bakiye sb
            JOIN stok.urunler u ON sb.urun_id = u.id
            WHERE {where} AND sb.miktar > 0
            GROUP BY u.id, u.urun_kodu, u.urun_adi
        """, (param,))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return StokOzet(
            urun_id=row[0],
            stok_kodu=row[1],
            stok_adi=row[2],
            toplam_miktar=float(row[3]) if row[3] else 0,
            rezerve_miktar=float(row[4]) if row[4] else 0,
            kullanilabilir_miktar=float(row[5]) if row[5] else 0,
            lot_sayisi=row[6] or 0,
            depo_sayisi=row[7] or 0
        )
    
    def get_depo_ozet(self, depo_id: int) -> Dict:
        """Depo bazlı stok özeti"""
        self.cursor.execute("""
            SELECT 
                COUNT(DISTINCT sb.lot_no) as lot_sayisi,
                COUNT(DISTINCT sb.urun_id) as urun_sayisi,
                SUM(sb.miktar) as toplam_miktar,
                SUM(CASE WHEN ISNULL(sb.kalite_durumu_v2, sb.kalite_durumu) = 'ONAY' THEN sb.miktar ELSE 0 END) as onayli_miktar,
                SUM(CASE WHEN ISNULL(sb.kalite_durumu_v2, sb.kalite_durumu) = 'BEKLIYOR' THEN sb.miktar ELSE 0 END) as bekleyen_miktar
            FROM stok.stok_bakiye sb
            WHERE sb.depo_id = ? AND sb.miktar > 0
        """, (depo_id,))
        
        row = self.cursor.fetchone()
        return {
            'lot_sayisi': row[0] or 0,
            'urun_sayisi': row[1] or 0,
            'toplam_miktar': float(row[2]) if row[2] else 0,
            'onayli_miktar': float(row[3]) if row[3] else 0,
            'bekleyen_miktar': float(row[4]) if row[4] else 0
        }
    
    # =========================================================================
    # HAREKET GEÇMİŞİ
    # =========================================================================
    
    def get_lot_gecmisi(self, lot_no: str) -> List[Dict]:
        """Lot'un tüm hareket geçmişi"""
        self.cursor.execute("""
            SELECT 
                hl.id, hl.hareket_no, hl.hareket_zamani,
                hl.hareket_tipi_kod, ht.ad as hareket_tipi_adi,
                hl.miktar, hl.onceki_miktar, hl.sonraki_miktar,
                hl.kaynak_depo_kod, hl.hedef_depo_kod,
                hl.kalite_durumu_onceki, hl.kalite_durumu_sonraki,
                hl.is_emri_no, hl.yapan_adi, hl.aciklama,
                hl.iptal_mi
            FROM stok.hareket_log hl
            LEFT JOIN tanim.hareket_tipleri ht ON hl.hareket_tipi_id = ht.id
            WHERE hl.lot_no = ?
            ORDER BY hl.hareket_zamani DESC
        """, (lot_no,))
        
        return [
            {
                'id': row[0],
                'hareket_no': row[1],
                'hareket_zamani': row[2],
                'hareket_tipi_kod': row[3],
                'hareket_tipi_adi': row[4],
                'miktar': float(row[5]) if row[5] else 0,
                'onceki_miktar': float(row[6]) if row[6] else 0,
                'sonraki_miktar': float(row[7]) if row[7] else 0,
                'kaynak_depo': row[8],
                'hedef_depo': row[9],
                'kalite_onceki': row[10],
                'kalite_sonraki': row[11],
                'is_emri_no': row[12],
                'yapan': row[13],
                'aciklama': row[14],
                'iptal_mi': bool(row[15])
            }
            for row in self.cursor.fetchall()
        ]
    
    # =========================================================================
    # YARDIMCI METODLAR
    # =========================================================================
    
    def _row_to_bakiye(self, row) -> StokBakiye:
        """SQL row'u StokBakiye objesine çevir"""
        return StokBakiye(
            id=row[0],
            lot_no=row[1],
            parent_lot_no=row[2],
            urun_id=row[3],
            stok_kodu=row[4] or '',
            stok_adi=row[5] or '',
            miktar=float(row[6]) if row[6] else 0,
            rezerve_miktar=float(row[7]) if row[7] else 0,
            kullanilabilir_miktar=float(row[8]) if row[8] else 0,
            birim=row[9] or 'ADET',
            depo_id=row[10],
            depo_kodu=row[11] or '',
            depo_adi=row[12] or '',
            depo_tipi=row[13] or '',
            depo_kategorisi=row[14] or '',
            kalite_durumu=row[15] or 'BEKLIYOR',
            uretim_durumu=row[16],
            bloke_mi=bool(row[17]),
            cari_unvani=row[18],
            kaplama_tipi=row[19],
            giris_tarihi=row[20],
            palet_no=row[21],
            toplam_palet=row[22]
        )
    
    # =========================================================================
    # KONTROL METODLARI
    # =========================================================================
    
    def bakiye_yeterli_mi(self, stok_bakiye_id: int, miktar: float) -> tuple:
        """
        Bakiye yeterliliğini kontrol et
        
        Returns:
            (yeterli_mi: bool, kullanilabilir: float, mesaj: str)
        """
        bakiye = self.get_bakiye(stok_bakiye_id)
        if not bakiye:
            return (False, 0, "Stok bakiyesi bulunamadı")
        
        if bakiye.bloke_mi:
            return (False, 0, "Stok blokeli")
        
        if miktar > bakiye.kullanilabilir_miktar:
            return (
                False, 
                bakiye.kullanilabilir_miktar,
                f"Yetersiz miktar. Kullanılabilir: {bakiye.kullanilabilir_miktar}"
            )
        
        return (True, bakiye.kullanilabilir_miktar, "OK")
    
    def kalite_uygun_mu(self, stok_bakiye_id: int, gereken_durum: str = 'ONAY') -> tuple:
        """
        Kalite durumu kontrolü
        
        Returns:
            (uygun_mu: bool, mevcut_durum: str, mesaj: str)
        """
        bakiye = self.get_bakiye(stok_bakiye_id)
        if not bakiye:
            return (False, None, "Stok bakiyesi bulunamadı")
        
        if bakiye.kalite_durumu != gereken_durum:
            return (
                False,
                bakiye.kalite_durumu,
                f"Kalite durumu uygun değil. Mevcut: {bakiye.kalite_durumu}, Gereken: {gereken_durum}"
            )
        
        return (True, bakiye.kalite_durumu, "OK")
