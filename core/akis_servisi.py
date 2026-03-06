# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Akış Servisi
Stok akış şablonlarını yöneten servis

Hareket motoru bu servisi kullanarak:
- Ürünün akış şablonunu bulur
- Mevcut adımı belirler
- Sonraki adımı ve hedef depoyu döner
"""

from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class AkisAdim:
    """Akış adım bilgisi"""
    id: int
    sira: int
    adim_tipi_kod: str
    adim_tipi_ad: str
    hedef_depo_tipi_id: Optional[int]
    hedef_depo_tipi_kod: Optional[str]
    hedef_depo_id: Optional[int]
    zorunlu: bool
    atlanabilir: bool
    kalite_kontrol_gerekli: bool
    aciklama: Optional[str]


@dataclass
class AkisSablon:
    """Akış şablon bilgisi"""
    id: int
    kod: str
    ad: str
    varsayilan_mi: bool
    adimlar: List[AkisAdim]


class AkisServisi:
    """
    Akış Yönetim Servisi
    
    Kullanım:
        servis = AkisServisi(conn)
        
        # Ürünün akışını al
        akis = servis.get_urun_akisi(urun_id)
        
        # Sonraki adımı bul
        sonraki = servis.get_sonraki_adim(urun_id, mevcut_adim_tipi='KALITE_GIRIS')
        
        # Hedef depoyu bul
        depo_id = servis.get_hedef_depo(urun_id, adim_tipi='DEPO')
    """
    
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
        self._cache = {}
    
    def get_varsayilan_sablon_id(self) -> Optional[int]:
        """Varsayılan şablon ID'sini döner"""
        self.cursor.execute("""
            SELECT id FROM tanim.akis_sablon 
            WHERE varsayilan_mi = 1 AND aktif_mi = 1
        """)
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def get_urun_sablon_id(self, urun_id: int) -> Optional[int]:
        """Ürünün akış şablon ID'sini döner (yoksa varsayılan)"""
        self.cursor.execute("""
            SELECT akis_sablon_id FROM stok.urunler WHERE id = ?
        """, (urun_id,))
        row = self.cursor.fetchone()
        
        if row and row[0]:
            return row[0]
        
        return self.get_varsayilan_sablon_id()
    
    def get_sablon(self, sablon_id: int) -> Optional[AkisSablon]:
        """Şablon ve adımlarını getir"""
        # Cache kontrol
        if sablon_id in self._cache:
            return self._cache[sablon_id]
        
        # Şablon bilgisi
        self.cursor.execute("""
            SELECT id, kod, ad, varsayilan_mi 
            FROM tanim.akis_sablon 
            WHERE id = ? AND aktif_mi = 1
        """, (sablon_id,))
        row = self.cursor.fetchone()
        
        if not row:
            return None
        
        # Adımları al
        self.cursor.execute("""
            SELECT 
                a.id, a.sira, t.kod, t.ad,
                a.hedef_depo_tipi_id, dt.kod,
                a.hedef_depo_id,
                a.zorunlu, a.atlanabilir, a.kalite_kontrol_gerekli,
                a.aciklama
            FROM tanim.akis_adim a
            JOIN tanim.akis_adim_tipleri t ON a.adim_tipi_id = t.id
            LEFT JOIN tanim.depo_tipleri dt ON a.hedef_depo_tipi_id = dt.id
            WHERE a.sablon_id = ? AND a.aktif_mi = 1
            ORDER BY a.sira
        """, (sablon_id,))
        
        adimlar = []
        for r in self.cursor.fetchall():
            adimlar.append(AkisAdim(
                id=r[0],
                sira=r[1],
                adim_tipi_kod=r[2],
                adim_tipi_ad=r[3],
                hedef_depo_tipi_id=r[4],
                hedef_depo_tipi_kod=r[5],
                hedef_depo_id=r[6],
                zorunlu=bool(r[7]),
                atlanabilir=bool(r[8]),
                kalite_kontrol_gerekli=bool(r[9]),
                aciklama=r[10]
            ))
        
        sablon = AkisSablon(
            id=row[0],
            kod=row[1],
            ad=row[2],
            varsayilan_mi=bool(row[3]),
            adimlar=adimlar
        )
        
        self._cache[sablon_id] = sablon
        return sablon
    
    def get_urun_akisi(self, urun_id: int) -> Optional[AkisSablon]:
        """Ürünün akış şablonunu getir"""
        sablon_id = self.get_urun_sablon_id(urun_id)
        if sablon_id:
            return self.get_sablon(sablon_id)
        return None
    
    def get_adim_by_tip(self, sablon_id: int, adim_tipi_kod: str, sira: int = None) -> Optional[AkisAdim]:
        """Belirli tipteki adımı getir"""
        sablon = self.get_sablon(sablon_id)
        if not sablon:
            return None
        
        # Aynı tipte birden fazla adım olabilir (örn: HASSAS akışta 2x KALITE_GIRIS)
        # sira belirtilmişse o sıradakini, yoksa ilkini döner
        for adim in sablon.adimlar:
            if adim.adim_tipi_kod == adim_tipi_kod:
                if sira is None or adim.sira == sira:
                    return adim
        return None
    
    def get_sonraki_adim(
        self, 
        urun_id: int = None,
        sablon_id: int = None,
        mevcut_adim_tipi: str = None,
        mevcut_sira: int = None
    ) -> Optional[AkisAdim]:
        """
        Sonraki adımı bul
        
        Args:
            urun_id: Ürün ID (sablon_id verilmemişse)
            sablon_id: Şablon ID (direkt)
            mevcut_adim_tipi: Şu anki adım tipi kodu
            mevcut_sira: Şu anki adım sırası
        
        Returns:
            Sonraki AkisAdim veya None
        """
        if not sablon_id:
            sablon_id = self.get_urun_sablon_id(urun_id)
        
        sablon = self.get_sablon(sablon_id)
        if not sablon or not sablon.adimlar:
            return None
        
        # Mevcut sırayı bul
        if mevcut_sira is None and mevcut_adim_tipi:
            for adim in sablon.adimlar:
                if adim.adim_tipi_kod == mevcut_adim_tipi:
                    mevcut_sira = adim.sira
                    break
        
        if mevcut_sira is None:
            # İlk adımı döner
            return sablon.adimlar[0] if sablon.adimlar else None
        
        # Sonraki adımı bul
        for adim in sablon.adimlar:
            if adim.sira > mevcut_sira:
                return adim
        
        return None  # Son adımdayız
    
    def get_hedef_depo(
        self,
        urun_id: int = None,
        sablon_id: int = None,
        adim_tipi: str = None,
        adim_sira: int = None,
        hat_id: int = None
    ) -> Optional[int]:
        """
        Adım için hedef depo ID'sini döner
        
        Args:
            urun_id: Ürün ID
            sablon_id: Şablon ID
            adim_tipi: Adım tipi kodu
            adim_sira: Adım sırası
            hat_id: Hat ID (URETIM adımı için)
        
        Returns:
            Depo ID
        """
        if not sablon_id and urun_id:
            sablon_id = self.get_urun_sablon_id(urun_id)
        
        adim = self.get_adim_by_tip(sablon_id, adim_tipi, adim_sira)
        if not adim:
            return None
        
        # Spesifik depo tanımlıysa
        if adim.hedef_depo_id:
            return adim.hedef_depo_id
        
        # Depo tipi tanımlıysa, o tipte bir depo bul
        if adim.hedef_depo_tipi_id:
            # URETIM tipi için hat deposuna bak
            if adim.adim_tipi_kod == 'URETIM' and hat_id:
                self.cursor.execute("""
                    SELECT depo_id FROM tanim.hatlar WHERE id = ?
                """, (hat_id,))
                row = self.cursor.fetchone()
                if row and row[0]:
                    return row[0]
            
            # Depo tipine göre bul
            self.cursor.execute("""
                SELECT TOP 1 id FROM tanim.depolar 
                WHERE depo_tipi_id = ? AND aktif_mi = 1
                ORDER BY id
            """, (adim.hedef_depo_tipi_id,))
            row = self.cursor.fetchone()
            if row:
                return row[0]
        
        return None
    
    def kalite_kontrol_gerekli_mi(
        self,
        urun_id: int = None,
        sablon_id: int = None,
        adim_tipi: str = None
    ) -> bool:
        """Bu adımda kalite kontrol gerekli mi?"""
        if not sablon_id and urun_id:
            sablon_id = self.get_urun_sablon_id(urun_id)
        
        adim = self.get_adim_by_tip(sablon_id, adim_tipi)
        return adim.kalite_kontrol_gerekli if adim else False
    
    def get_tum_sablonlar(self) -> List[Dict]:
        """Tüm aktif şablonları listele (dropdown için)"""
        self.cursor.execute("""
            SELECT id, kod, ad, varsayilan_mi,
                   (SELECT COUNT(*) FROM tanim.akis_adim WHERE sablon_id = s.id AND aktif_mi = 1) as adim_sayisi
            FROM tanim.akis_sablon s
            WHERE aktif_mi = 1
            ORDER BY varsayilan_mi DESC, kod
        """)
        
        return [
            {
                'id': row[0],
                'kod': row[1],
                'ad': row[2],
                'varsayilan_mi': bool(row[3]),
                'adim_sayisi': row[4]
            }
            for row in self.cursor.fetchall()
        ]
    
    def clear_cache(self):
        """Cache'i temizle"""
        self._cache = {}
