# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kaplama Planlama Motoru
Otomatik görev yerleştirme algoritması

Askı döngüsel kullanım mantığı:
- Askılar hatta girer, çevrim süresi sonunda geri gelir, boşaltılıp tekrar yüklenir
- Örnek: 1000 adet, 10 askı, askı kapasitesi=10, bara başına 2 askı, çevrim=45dk
  → Her çevrimde: 10 askı × 10 adet = 100 adet işlenir
  → Toplam çevrim: ceil(1000/100) = 10 çevrim
  → Toplam süre: 10 × 45dk = 450dk
  → Bara kullanımı: ceil(10 askı / 2 askı/bara) = 5 bara paralel
  → Bir vardiyada (480dk) 10 çevrim yapılabilir → tek vardiyada biter
"""
from typing import List
from dataclasses import dataclass
from .models import (
    KaplamaUrun, PlanGorev, BANYOLAR,
    BARA_SAYISI, VARDIYA_SURE_DK, VARDIYA_SAYISI, GUN_SAYISI
)


@dataclass
class PlanlamaSonuc:
    """Planlama sonucu"""
    gorevler: List[PlanGorev]
    uyarilar: List[str]
    yerlestirilemeyenler: List[str]


def _banyo_uygun_mu(tip: str) -> bool:
    """Verilen tip için uygun banyo var mı?"""
    return any(b.tip == tip for b in BANYOLAR)


def _ardisik_slot_bul(
    mevcut_gorevler: List[PlanGorev],
    bara_nolar: List[int],
    toplam_sure_dk: int,
    cevrim_suresi: int,
    gun: int,
    vardiya: int
) -> int:
    """
    Birden fazla bara için aynı zaman diliminde ardışık çevrimler yerleştirebilecek
    başlangıç dakikasını bul. Tüm baralar aynı anda çalışır.
    -1 = sığmıyor
    """
    # Her bara için o gün/vardiyada doluluk kontrolü
    for bara_no in bara_nolar:
        slot_gorevler = [
            g for g in mevcut_gorevler
            if g.bara_no == bara_no and g.gun == gun and g.vardiya == vardiya
        ]
        slot_gorevler.sort(key=lambda g: g.baslangic_dk)

        # En erken boş noktayı bul
        cursor = 0
        for g in slot_gorevler:
            cursor = max(cursor, g.bitis_dk)

        # Bu baraya toplam süre sığmalı
        if cursor + toplam_sure_dk > VARDIYA_SURE_DK:
            return -1

    # Tüm baralardaki en geç başlangıç noktasını bul (hepsi aynı anda başlamalı)
    max_cursor = 0
    for bara_no in bara_nolar:
        slot_gorevler = [
            g for g in mevcut_gorevler
            if g.bara_no == bara_no and g.gun == gun and g.vardiya == vardiya
        ]
        cursor = 0
        for g in slot_gorevler:
            cursor = max(cursor, g.bitis_dk)
        max_cursor = max(max_cursor, cursor)

    if max_cursor + toplam_sure_dk <= VARDIYA_SURE_DK:
        return max_cursor

    return -1


def _bos_bara_bul(
    mevcut_gorevler: List[PlanGorev],
    gerekli_bara: int,
    toplam_sure_dk: int,
    cevrim_suresi: int,
    gun: int,
    vardiya: int
) -> List[int]:
    """Uygun boş bara grubunu bul. Boş liste = bulunamadı"""
    # Her bara için kalan süreyi hesapla
    bara_bosluk = []
    for bara_no in range(1, BARA_SAYISI + 1):
        slot_gorevler = [
            g for g in mevcut_gorevler
            if g.bara_no == bara_no and g.gun == gun and g.vardiya == vardiya
        ]
        kullanilan = max((g.bitis_dk for g in slot_gorevler), default=0)
        kalan = VARDIYA_SURE_DK - kullanilan
        bara_bosluk.append((bara_no, kalan))

    # En çok boşluğu olan baraları seç
    bara_bosluk.sort(key=lambda x: -x[1])

    # gerekli_bara kadar bara seç, hepsine toplam_sure sığmalı
    secilen = []
    for bara_no, kalan in bara_bosluk:
        if kalan >= toplam_sure_dk:
            secilen.append(bara_no)
            if len(secilen) >= gerekli_bara:
                break

    return secilen


def otomatik_planla(urunler: List[KaplamaUrun]) -> PlanlamaSonuc:
    """
    Ürün listesini otomatik olarak baralara yerleştirir.

    Döngüsel askı mantığı:
    - Askılar hatta girer → çevrim süresi sonra geri gelir → boşaltılır → tekrar yüklenir
    - stok_aski: fiziksel askı sayısı (tekrar tekrar kullanılır)
    - bara_aski: bir baraya kaç askı asılır
    - Her çevrimde tüm askılar kullanılır, çevrim süresi sonunda geri gelir

    Algoritma:
    1. Acil ürünleri öne al
    2. Toplam çevrim sayısı = ceil(ihtiyaç / (stok_aski × kapasite))
    3. Toplam süre = çevrim sayısı × çevrim süresi
    4. Gerekli bara = ceil(stok_aski / bara_aski)
    5. Gün→Vardiya sırasıyla uygun bara grubu bul ve yerleştir
    """
    gorevler: List[PlanGorev] = []
    uyarilar: List[str] = []
    yerlestirilemeyenler: List[str] = []

    # Acil olanları öne al, sonra ihtiyaca göre sırala
    sirali = sorted(urunler, key=lambda u: (0 if u.oncelik == "acil" else 1, -u.haftalik_ihtiyac))

    gorev_id_counter = 1

    for urun in sirali:
        if urun.haftalik_ihtiyac <= 0:
            continue

        # Banyo tipi kontrolü
        if not _banyo_uygun_mu(urun.tip):
            uyarilar.append(f"{urun.ref}: Uygun banyo bulunamadı (tip={urun.tip})")
            yerlestirilemeyenler.append(urun.ref)
            continue

        # Askı kontrolü - en az 1 askı olmalı
        if not urun.aski_yeterli:
            uyarilar.append(f"{urun.ref}: Askı tanımlı değil (stok_aski=0)")
            yerlestirilemeyenler.append(urun.ref)
            continue

        # Hesaplamalar
        parca_per_cevrim = urun.stok_aski * urun.kapasite
        toplam_cevrim = urun.toplam_cevrim
        gerekli_bara = urun.gerekli_bara

        # Bilgi mesajı
        uyarilar.append(
            f"{urun.ref}: {urun.haftalik_ihtiyac} adet → "
            f"{urun.stok_aski} askı × {urun.kapasite} kap = {parca_per_cevrim} adet/çevrim, "
            f"{toplam_cevrim} çevrim × {urun.cevrim_suresi}dk = {urun.toplam_sure_dk}dk toplam, "
            f"{gerekli_bara} bara"
        )

        kalan_sure_dk = urun.toplam_sure_dk
        yerlestirildi = False

        # Gün → Vardiya sırasıyla yerleştir
        for gun in range(GUN_SAYISI):
            if kalan_sure_dk <= 0:
                break
            for vardiya in range(1, VARDIYA_SAYISI + 1):
                if kalan_sure_dk <= 0:
                    break

                # Bu vardiyada sığacak süreyi hesapla
                vardiya_icin_sure = min(kalan_sure_dk, VARDIYA_SURE_DK)

                # Uygun bara grubu bul
                secilen_baralar = _bos_bara_bul(
                    gorevler, gerekli_bara, vardiya_icin_sure,
                    urun.cevrim_suresi, gun, vardiya
                )

                if not secilen_baralar:
                    # Tam grup bulunamadı, tek tek dene
                    for bara_no in range(1, BARA_SAYISI + 1):
                        if kalan_sure_dk <= 0:
                            break
                        tek_bara = _bos_bara_bul(
                            gorevler, 1, min(kalan_sure_dk, VARDIYA_SURE_DK),
                            urun.cevrim_suresi, gun, vardiya
                        )
                        if not tek_bara or tek_bara[0] in [g.bara_no for g in gorevler
                                if g.gun == gun and g.vardiya == vardiya and g.urun_ref == urun.ref]:
                            continue

                        baslangic = _ardisik_slot_bul(
                            gorevler, tek_bara,
                            min(kalan_sure_dk, VARDIYA_SURE_DK),
                            urun.cevrim_suresi, gun, vardiya
                        )
                        if baslangic < 0:
                            continue

                        slot_sure = min(kalan_sure_dk, VARDIYA_SURE_DK - baslangic)
                        slot_cevrim = slot_sure // urun.cevrim_suresi
                        if slot_cevrim <= 0:
                            continue
                        gercek_sure = slot_cevrim * urun.cevrim_suresi
                        # Bu baradaki askı sayısı
                        bara_aski_sayisi = min(urun.stok_aski, urun.bara_aski)

                        gorev = PlanGorev(
                            id=gorev_id_counter,
                            urun_id=urun.id,
                            bara_no=tek_bara[0],
                            gun=gun,
                            vardiya=vardiya,
                            urun_ref=urun.ref,
                            tip=urun.tip,
                            aski_sayisi=bara_aski_sayisi * slot_cevrim,
                            acil=(urun.oncelik == "acil"),
                            baslangic_dk=baslangic,
                            sure_dk=gercek_sure
                        )
                        gorevler.append(gorev)
                        gorev_id_counter += 1
                        kalan_sure_dk -= gercek_sure
                        yerlestirildi = True
                    continue

                # Bara grubu bulundu - başlangıç noktası
                baslangic = _ardisik_slot_bul(
                    gorevler, secilen_baralar, vardiya_icin_sure,
                    urun.cevrim_suresi, gun, vardiya
                )

                if baslangic < 0:
                    continue

                # Sığan süreyi hesapla (çevrim süresinin katı olmalı)
                maks_sure = VARDIYA_SURE_DK - baslangic
                slot_sure = min(kalan_sure_dk, maks_sure)
                slot_cevrim = slot_sure // urun.cevrim_suresi
                if slot_cevrim <= 0:
                    continue
                gercek_sure = slot_cevrim * urun.cevrim_suresi

                # Her bara için görev oluştur (tüm baralar paralel çalışır)
                for bara_no in secilen_baralar:
                    bara_aski_sayisi = min(urun.bara_aski, urun.stok_aski)

                    gorev = PlanGorev(
                        id=gorev_id_counter,
                        urun_id=urun.id,
                        bara_no=bara_no,
                        gun=gun,
                        vardiya=vardiya,
                        urun_ref=urun.ref,
                        tip=urun.tip,
                        aski_sayisi=bara_aski_sayisi * slot_cevrim,
                        acil=(urun.oncelik == "acil"),
                        baslangic_dk=baslangic,
                        sure_dk=gercek_sure
                    )
                    gorevler.append(gorev)
                    gorev_id_counter += 1

                kalan_sure_dk -= gercek_sure
                yerlestirildi = True

        if kalan_sure_dk > 0:
            kalan_cevrim = -(-kalan_sure_dk // urun.cevrim_suresi)
            kalan_adet = kalan_cevrim * parca_per_cevrim
            uyarilar.append(
                f"{urun.ref}: {kalan_adet} adet ({kalan_cevrim} çevrim) yerleştirilemedi - haftalık kapasite yetersiz"
            )
            if not yerlestirildi:
                yerlestirilemeyenler.append(urun.ref)

    return PlanlamaSonuc(
        gorevler=gorevler,
        uyarilar=uyarilar,
        yerlestirilemeyenler=yerlestirilemeyenler
    )
