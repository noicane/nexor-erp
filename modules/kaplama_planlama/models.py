# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kaplama Planlama Veri Modelleri
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KaplamaUrun:
    """Kaplama planına eklenecek ürün"""
    id: int = 0
    ref: str = ""                # NEXOR referans kodu
    recete_no: str = ""          # Reçete numarası
    tip: str = "zn"              # "zn" | "zn-ni"
    aski_tip: str = ""           # Askı tipi kodu
    kapasite: int = 1            # Askı başına ürün adedi
    cevrim_suresi: int = 45      # Dakika
    stok_aski: int = 0           # Mevcut askı adedi (fiziksel askı sayısı)
    bara_aski: int = 2           # Bara başına askı adedi
    haftalik_ihtiyac: int = 0    # Adet
    oncelik: str = "normal"      # "normal" | "acil"

    @property
    def toplam_cevrim(self) -> int:
        """Tüm ihtiyacı karşılamak için gereken toplam yükleme sayısı"""
        if self.kapasite <= 0 or self.stok_aski <= 0:
            return 0
        parca_per_cevrim = self.stok_aski * self.kapasite  # Tüm askılar bir çevrimde
        return -(-self.haftalik_ihtiyac // parca_per_cevrim)  # ceil division

    @property
    def toplam_sure_dk(self) -> int:
        """Tüm çevrimlerin toplam süresi (dakika)"""
        return self.toplam_cevrim * self.cevrim_suresi

    @property
    def gerekli_bara(self) -> int:
        """Aynı anda kaç bara kullanılacak"""
        if self.bara_aski <= 0:
            return 1
        return -(-self.stok_aski // self.bara_aski)  # ceil division

    @property
    def aski_yeterli(self) -> bool:
        """En az 1 askı varsa üretim yapılabilir"""
        return self.stok_aski > 0


@dataclass
class PlanGorev:
    """Gantt çizelgesinde bir görev bloğu"""
    id: int = 0
    urun_id: int = 0
    bara_no: int = 1             # 1-11
    gun: int = 0                 # 0=Pzt..6=Pzr
    vardiya: int = 1             # 1, 2, 3
    urun_ref: str = ""
    tip: str = "zn"              # "zn" | "zn-ni"
    aski_sayisi: int = 0
    acil: bool = False
    baslangic_dk: int = 0        # Vardiya içi dakika offset
    sure_dk: int = 45            # Toplam süre

    @property
    def bitis_dk(self) -> int:
        return self.baslangic_dk + self.sure_dk

    @property
    def global_baslangic(self) -> int:
        """Hafta başından itibaren toplam dakika"""
        return self.gun * 1440 + (self.vardiya - 1) * 480 + self.baslangic_dk

    @property
    def global_bitis(self) -> int:
        return self.global_baslangic + self.sure_dk


@dataclass
class BanyoDurum:
    """Banyo doluluk durumu"""
    banyo_id: int = 0
    ad: str = ""
    tip: str = "zn"              # "zn" | "zn-ni"
    max_aski: int = 4
    mevcut_aski: int = 0

    @property
    def doluluk_yuzde(self) -> float:
        if self.max_aski <= 0:
            return 0.0
        return (self.mevcut_aski / self.max_aski) * 100.0


# Sabit tanımlar
BANYOLAR = [
    BanyoDurum(1, "Çinko-1", "zn", 4),
    BanyoDurum(2, "Çinko-2", "zn", 4),
    BanyoDurum(3, "Çinko-3", "zn", 4),
    BanyoDurum(4, "Çinko-4", "zn", 4),
    BanyoDurum(5, "Çinko-Nikel-1", "zn-ni", 3),
    BanyoDurum(6, "Çinko-Nikel-2", "zn-ni", 3),
    BanyoDurum(7, "Çinko-Nikel-3", "zn-ni", 3),
]

BARA_SAYISI = 11
VARDIYA_SURE_DK = 480  # 8 saat
VARDIYA_SAYISI = 3
GUN_SAYISI = 7
