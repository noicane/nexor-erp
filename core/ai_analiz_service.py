# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - AI Analiz Servisi
Banyo TDS analizi icin kural tabanli + opsiyonel OpenAI backend

Strateji deseni:
  1. RuleBasedBackend - Her zaman calisir, API gerektirmez
  2. OpenAIBackend   - config.json'da api_key varsa aktif
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# ============================================================
# VERI MODELLERI
# ============================================================

class KarsilastirmaSonuc:
    """TDS hedef vs gercek olcum karsilastirma sonucu"""
    def __init__(self, parametre: str, birim: str, tds_hedef: float,
                 tds_min: float, tds_max: float, gercek: float,
                 tolerans_yuzde: float = 10.0):
        self.parametre = parametre
        self.birim = birim
        self.tds_hedef = tds_hedef
        self.tds_min = tds_min
        self.tds_max = tds_max
        self.gercek = gercek
        self.tolerans_yuzde = tolerans_yuzde

        if tds_hedef and tds_hedef != 0:
            self.sapma = gercek - tds_hedef
            self.sapma_yuzde = abs(self.sapma / tds_hedef * 100)
        else:
            self.sapma = 0
            self.sapma_yuzde = 0

        # Durum belirleme
        if self.sapma_yuzde <= tolerans_yuzde:
            self.durum = "NORMAL"
        elif self.sapma_yuzde <= tolerans_yuzde * 2:
            self.durum = "UYARI"
        else:
            self.durum = "KRITIK"

    def to_dict(self):
        return {
            "parametre": self.parametre,
            "birim": self.birim,
            "tds_hedef": self.tds_hedef,
            "tds_min": self.tds_min,
            "tds_max": self.tds_max,
            "gercek": self.gercek,
            "sapma": round(self.sapma, 4),
            "sapma_yuzde": round(self.sapma_yuzde, 2),
            "durum": self.durum,
        }


class TrendSonuc:
    """Trend analizi sonucu"""
    def __init__(self, parametre: str, egim: float, yorum: str,
                 son_deger: float, ortalama: float, veri_sayisi: int):
        self.parametre = parametre
        self.egim = egim
        self.yorum = yorum  # "artan", "azalan", "stabil"
        self.son_deger = son_deger
        self.ortalama = ortalama
        self.veri_sayisi = veri_sayisi

    def to_dict(self):
        return {
            "parametre": self.parametre,
            "egim": round(self.egim, 6),
            "yorum": self.yorum,
            "son_deger": round(self.son_deger, 4),
            "ortalama": round(self.ortalama, 4),
            "veri_sayisi": self.veri_sayisi,
        }


class TahminSonuc:
    """Tahmin sonucu"""
    def __init__(self, parametre: str, mevcut: float, tahmini_7gun: float,
                 tds_min: float, tds_max: float, risk: str):
        self.parametre = parametre
        self.mevcut = mevcut
        self.tahmini_7gun = tahmini_7gun
        self.tds_min = tds_min
        self.tds_max = tds_max
        self.risk = risk  # "DUSUK", "NORMAL", "YUKSEK"

    def to_dict(self):
        return {
            "parametre": self.parametre,
            "mevcut": round(self.mevcut, 4),
            "tahmini_7gun": round(self.tahmini_7gun, 4),
            "tds_min": self.tds_min,
            "tds_max": self.tds_max,
            "risk": self.risk,
        }


class TakviyeOneri:
    """Kimyasal takviye onerisi"""
    def __init__(self, parametre: str, kimyasal: str, miktar: float,
                 birim: str, oncelik: str, aciklama: str = ""):
        self.parametre = parametre
        self.kimyasal = kimyasal
        self.miktar = miktar
        self.birim = birim
        self.oncelik = oncelik  # "DUSUK", "ORTA", "YUKSEK", "ACIL"
        self.aciklama = aciklama

    def to_dict(self):
        return {
            "parametre": self.parametre,
            "kimyasal": self.kimyasal,
            "miktar": round(self.miktar, 2),
            "birim": self.birim,
            "oncelik": self.oncelik,
            "aciklama": self.aciklama,
        }


# ============================================================
# KURAL TABANLI BACKEND
# ============================================================

class RuleBasedBackend:
    """Her zaman calisan, API gerektirmeyen analiz motoru"""

    # Parametre bazli takviye kural tablosu
    TAKVIYE_KURALLARI = {
        "ph": {
            "dusuk": {"kimyasal": "NaOH (%10)", "birim": "ml/lt", "faktor": 0.5},
            "yuksek": {"kimyasal": "Asetik Asit", "birim": "ml/lt", "faktor": 0.3},
        },
        "sicaklik": {
            "dusuk": {"kimyasal": "Isitici Ayari", "birim": "°C", "faktor": 1.0},
            "yuksek": {"kimyasal": "Sogutma Ayari", "birim": "°C", "faktor": 1.0},
        },
        "iletkenlik": {
            "dusuk": {"kimyasal": "Iletkenlik Duzenleyici", "birim": "ml/lt", "faktor": 0.1},
            "yuksek": {"kimyasal": "DI Su Takviyesi", "birim": "lt", "faktor": 2.0},
        },
        "kati_madde": {
            "dusuk": {"kimyasal": "Boya Paste", "birim": "kg", "faktor": 0.05},
            "yuksek": {"kimyasal": "UF Permeate Takviyesi", "birim": "lt", "faktor": 5.0},
        },
        "pb_orani": {
            "dusuk": {"kimyasal": "Pigment Paste", "birim": "kg", "faktor": 0.02},
            "yuksek": {"kimyasal": "Resin Takviyesi", "birim": "kg", "faktor": 0.03},
        },
        "solvent": {
            "dusuk": {"kimyasal": "Solvent Takviyesi", "birim": "lt", "faktor": 0.1},
            "yuksek": {"kimyasal": "UF Permeate Takviyesi", "birim": "lt", "faktor": 3.0},
        },
        "meq": {
            "dusuk": {"kimyasal": "Asit Notralizor", "birim": "ml/lt", "faktor": 0.2},
            "yuksek": {"kimyasal": "Baz Notralizor", "birim": "ml/lt", "faktor": 0.2},
        },
        "toplam_asit": {
            "dusuk": {"kimyasal": "Asit Takviyesi", "birim": "ml/lt", "faktor": 0.1},
            "yuksek": {"kimyasal": "Notralizasyon Kimyasali", "birim": "ml/lt", "faktor": 0.15},
        },
        "serbest_asit": {
            "dusuk": {"kimyasal": "Serbest Asit Takviyesi", "birim": "ml/lt", "faktor": 0.1},
            "yuksek": {"kimyasal": "Notralizasyon Kimyasali", "birim": "ml/lt", "faktor": 0.12},
        },
    }

    def karsilastirma(self, tds_parametreler: List[Dict], son_olcumler: Dict) -> List[KarsilastirmaSonuc]:
        """
        TDS hedef degerleri ile son olcumleri karsilastir.

        Args:
            tds_parametreler: [{"parametre_kodu", "parametre_adi", "birim", "tds_min", "tds_hedef", "tds_max", "tolerans_yuzde"}]
            son_olcumler: {"sicaklik": 28.5, "ph": 5.8, ...}

        Returns:
            KarsilastirmaSonuc listesi
        """
        sonuclar = []
        for p in tds_parametreler:
            kod = p.get("parametre_kodu", "")
            gercek = son_olcumler.get(kod)
            if gercek is None:
                continue
            try:
                gercek = float(gercek)
            except (ValueError, TypeError):
                continue

            tds_hedef = float(p.get("tds_hedef") or 0)
            tds_min = float(p.get("tds_min") or 0)
            tds_max = float(p.get("tds_max") or 0)
            tolerans = float(p.get("tolerans_yuzde") or 10.0)

            sonuclar.append(KarsilastirmaSonuc(
                parametre=p.get("parametre_adi", kod),
                birim=p.get("birim", ""),
                tds_hedef=tds_hedef,
                tds_min=tds_min,
                tds_max=tds_max,
                gercek=gercek,
                tolerans_yuzde=tolerans,
            ))
        return sonuclar

    def trend_analizi(self, veri_serisi: List[Dict]) -> List[TrendSonuc]:
        """
        Son 30 gunluk veriden lineer regresyon ile egim hesapla.

        Args:
            veri_serisi: [{"parametre": "ph", "tarih": datetime, "deger": 5.8}, ...]
                         Ayni parametreden birden fazla olcum olabilir.

        Returns:
            TrendSonuc listesi (parametre bazli)
        """
        # Parametrelere gore grupla
        param_gruplari: Dict[str, List] = {}
        for v in veri_serisi:
            p = v.get("parametre", "")
            if p not in param_gruplari:
                param_gruplari[p] = []
            param_gruplari[p].append(v)

        sonuclar = []
        for parametre, veriler in param_gruplari.items():
            if len(veriler) < 2:
                continue

            # Tarihe gore sirala
            veriler.sort(key=lambda x: x.get("tarih", datetime.min))

            degerler = [float(v.get("deger", 0)) for v in veriler]
            n = len(degerler)

            # Lineer regresyon (en kucuk kareler)
            x_vals = list(range(n))
            x_mean = sum(x_vals) / n
            y_mean = sum(degerler) / n

            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, degerler))
            denominator = sum((x - x_mean) ** 2 for x in x_vals)

            if denominator == 0:
                egim = 0.0
            else:
                egim = numerator / denominator

            # Yorum belirleme
            esik = abs(y_mean * 0.005) if y_mean != 0 else 0.01
            if egim > esik:
                yorum = "artan"
            elif egim < -esik:
                yorum = "azalan"
            else:
                yorum = "stabil"

            sonuclar.append(TrendSonuc(
                parametre=parametre,
                egim=egim,
                yorum=yorum,
                son_deger=degerler[-1],
                ortalama=y_mean,
                veri_sayisi=n,
            ))

        return sonuclar

    def tahmin(self, veri_serisi: List[Dict], tds_parametreler: List[Dict],
               gun: int = 7) -> List[TahminSonuc]:
        """
        Lineer ekstrapolasyon ile gelecek tahmini.

        Args:
            veri_serisi: trend_analizi ile ayni format
            tds_parametreler: TDS limit bilgileri
            gun: Kac gun sonrasi icin tahmin (varsayilan 7)

        Returns:
            TahminSonuc listesi
        """
        trend_sonuclari = self.trend_analizi(veri_serisi)

        # TDS limitleri haritala
        tds_map = {}
        for p in tds_parametreler:
            tds_map[p.get("parametre_kodu", "")] = p

        sonuclar = []
        for trend in trend_sonuclari:
            tds_p = tds_map.get(trend.parametre, {})
            tds_min = float(tds_p.get("tds_min") or 0)
            tds_max = float(tds_p.get("tds_max") or 99999)

            # Tahmini deger: son_deger + (egim * gun)
            tahmini = trend.son_deger + (trend.egim * gun)

            # Risk belirleme
            if tds_min <= tahmini <= tds_max:
                risk = "NORMAL"
            elif tahmini < tds_min * 0.9 or tahmini > tds_max * 1.1:
                risk = "YUKSEK"
            else:
                risk = "DUSUK"

            sonuclar.append(TahminSonuc(
                parametre=trend.parametre,
                mevcut=trend.son_deger,
                tahmini_7gun=tahmini,
                tds_min=tds_min,
                tds_max=tds_max,
                risk=risk,
            ))

        return sonuclar

    def kaplama_tds_kontrol(self, tds_parametreler: List[Dict],
                            banyo_olcumler: Dict,
                            kaplama_test: Dict) -> Dict[str, Any]:
        """
        Kaplama testi icin TDS kontrol noktalarini olustur.
        TDS hedefleriyle banyo olcumlerini + kaplama test sonuclarini karsilastir.

        Args:
            tds_parametreler: TDS parametre listesi (banyo_tds_parametreler)
            banyo_olcumler: Son banyo analiz olcumleri {"sicaklik": 28.5, ...}
            kaplama_test: Kaplama test verileri {
                "sicaklik", "amper", "volt", "sure_dk",
                "kalinlik_a", "kalinlik_b", "ab_orani",
                "kimyasallar": [{"parametre_adi", "deger", "min", "max", "hedef"}]
            }

        Returns:
            {
                "kontrol_noktalari": [...],  # kontrol edilen her parametre
                "sorunlar": [...],           # tespit edilen sorunlar
                "oneriler": [...],           # aksiyona donuk oneriler
                "genel_durum": "UYGUN"|"DIKKAT"|"KRITIK",
                "ozet_metin": str
            }
        """
        kontrol_noktalari = []
        sorunlar = []
        oneriler = []

        # --- 1. Banyo parametrelerini TDS'e gore kontrol ---
        for p in tds_parametreler:
            kod = p.get("parametre_kodu", "")
            adi = p.get("parametre_adi", kod)
            birim = p.get("birim", "")
            tds_min = float(p.get("tds_min") or 0)
            tds_hedef = float(p.get("tds_hedef") or 0)
            tds_max = float(p.get("tds_max") or 0)
            tolerans = float(p.get("tolerans_yuzde") or 10.0)
            kritik = p.get("kritik_mi", False)

            gercek = banyo_olcumler.get(kod)
            if gercek is None:
                kontrol_noktalari.append({
                    "parametre": adi, "birim": birim,
                    "tds_min": tds_min, "tds_hedef": tds_hedef, "tds_max": tds_max,
                    "gercek": None, "durum": "OLCUM_YOK",
                    "aciklama": f"{adi} icin olcum verisi bulunamadi",
                    "kritik": kritik,
                })
                if kritik:
                    sorunlar.append(f"{adi}: Kritik parametre icin olcum verisi yok!")
                continue

            gercek = float(gercek)

            # Sapma hesapla
            if tds_hedef and tds_hedef != 0:
                sapma_yuzde = abs((gercek - tds_hedef) / tds_hedef * 100)
            else:
                sapma_yuzde = 0

            # Durum belirle - limit bazli (min/max) oncelikli
            if tds_min and tds_max and tds_min > 0:
                if tds_min <= gercek <= tds_max:
                    durum = "NORMAL"
                elif gercek < tds_min:
                    durum = "DUSUK"
                else:
                    durum = "YUKSEK"
            elif sapma_yuzde <= tolerans:
                durum = "NORMAL"
            elif sapma_yuzde <= tolerans * 2:
                durum = "UYARI"
            else:
                durum = "KRITIK"

            kontrol_noktalari.append({
                "parametre": adi, "birim": birim,
                "tds_min": tds_min, "tds_hedef": tds_hedef, "tds_max": tds_max,
                "gercek": gercek, "sapma_yuzde": round(sapma_yuzde, 1),
                "durum": durum, "kritik": kritik,
                "aciklama": "",
            })

            if durum in ("DUSUK", "YUKSEK", "KRITIK", "UYARI"):
                yon_txt = "dusuk" if (durum == "DUSUK" or gercek < tds_hedef) else "yuksek"
                sorunlar.append(f"{adi}: {gercek:.2f} {birim} - TDS araliginin disinda "
                                f"(Hedef: {tds_hedef:.2f}, Min: {tds_min:.2f}, Max: {tds_max:.2f})")
                # Otoneriler
                if kod == "ph" and yon_txt == "dusuk":
                    oneriler.append(f"pH dusuk ({gercek:.2f}): NaOH takviyesi gerekli")
                elif kod == "ph" and yon_txt == "yuksek":
                    oneriler.append(f"pH yuksek ({gercek:.2f}): Asit ile dusurun")
                elif kod == "sicaklik" and yon_txt == "dusuk":
                    oneriler.append(f"Sicaklik dusuk ({gercek:.1f}°C): Isiticiyi kontrol edin")
                elif kod == "sicaklik" and yon_txt == "yuksek":
                    oneriler.append(f"Sicaklik yuksek ({gercek:.1f}°C): Sogutmayi kontrol edin")
                elif kod == "kati_madde" and yon_txt == "dusuk":
                    oneriler.append(f"Kati madde dusuk ({gercek:.2f}%): Paste takviyesi gerekli")
                elif kod == "iletkenlik":
                    oneriler.append(f"Iletkenlik sapma ({gercek:.1f} mS/cm): DI su / iletkenlik duzenleme")
                elif yon_txt == "dusuk":
                    oneriler.append(f"{adi} dusuk ({gercek:.2f}): Takviye gerekli")
                elif yon_txt == "yuksek":
                    oneriler.append(f"{adi} yuksek ({gercek:.2f}): Seyreltme/duzenleme gerekli")

        # --- 2. Kaplama test sonuclarini TDS'le iliskilendir ---
        ab = kaplama_test.get("ab_orani", 0) or 0
        kal_a = kaplama_test.get("kalinlik_a", 0) or 0
        kal_b = kaplama_test.get("kalinlik_b", 0) or 0
        test_sic = kaplama_test.get("sicaklik", 0) or 0

        if ab > 0:
            ab_durum = "NORMAL" if ab <= 1.5 else ("UYARI" if ab <= 2.0 else "KRITIK")
            kontrol_noktalari.append({
                "parametre": "A/B Orani", "birim": "",
                "tds_min": 0, "tds_hedef": 1.0, "tds_max": 1.5,
                "gercek": ab, "sapma_yuzde": 0, "durum": ab_durum,
                "kritik": True, "aciklama": "Kaplama homojenlik gostergesi",
            })
            if ab_durum != "NORMAL":
                sorunlar.append(f"A/B orani {ab:.2f} - {'Kabul edilebilir' if ab_durum == 'UYARI' else 'Homojenlik kritik!'}")
                oneriler.append("Anot pozisyonu ve akım yogunlugunu kontrol edin")

        if kal_a > 0 and kal_b > 0:
            ort_kalinlik = (kal_a + kal_b) / 2
            kal_durum = "NORMAL" if ort_kalinlik >= 15 else ("UYARI" if ort_kalinlik >= 10 else "KRITIK")
            kontrol_noktalari.append({
                "parametre": "Ort. Kalinlik", "birim": "µ",
                "tds_min": 15, "tds_hedef": 20, "tds_max": 35,
                "gercek": ort_kalinlik, "sapma_yuzde": 0, "durum": kal_durum,
                "kritik": True, "aciklama": "Kaplama kalinligi",
            })
            if kal_durum != "NORMAL":
                sorunlar.append(f"Ort. kalinlik {ort_kalinlik:.2f}µ - {'Dusuk' if ort_kalinlik < 15 else 'Kritik!'}")
                # TDS'teki kati madde ve voltaj iliskisi
                km = banyo_olcumler.get("kati_madde")
                if km and float(km) < 18:
                    oneriler.append(f"Kalinlik dusuk olabilir cunku kati madde dusuk ({float(km):.1f}%)")
                oneriler.append("Voltaj, sure veya kati madde oranini artirin")

        # --- 3. Kimyasal parametreleri TDS ile cross-check ---
        for kim in kaplama_test.get("kimyasallar", []):
            deger = kim.get("deger", 0) or 0
            mn = kim.get("min")
            mx = kim.get("max")
            hedef = kim.get("hedef")
            adi = kim.get("parametre_adi", "")
            if mn is not None and mx is not None and deger > 0:
                if deger < mn:
                    sorunlar.append(f"Kimyasal {adi}: {deger:.2f} - Min ({mn:.2f}) altinda!")
                    oneriler.append(f"{adi} takviyesi yapilmali")
                elif deger > mx:
                    sorunlar.append(f"Kimyasal {adi}: {deger:.2f} - Max ({mx:.2f}) ustunde!")

        # --- 4. Genel durum ---
        kritik_sayisi = sum(1 for k in kontrol_noktalari if k.get("durum") in ("KRITIK", "YUKSEK", "DUSUK") and k.get("kritik"))
        uyari_sayisi = sum(1 for k in kontrol_noktalari if k.get("durum") in ("UYARI", "YUKSEK", "DUSUK"))

        if kritik_sayisi > 0:
            genel_durum = "KRITIK"
        elif uyari_sayisi > 0:
            genel_durum = "DIKKAT"
        else:
            genel_durum = "UYGUN"

        # Ozet metin
        ozet_satirlari = [f"TDS Kontrol Raporu - {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                          f"Kontrol edilen parametre: {len(kontrol_noktalari)}",
                          f"Genel durum: {genel_durum}", ""]
        if sorunlar:
            ozet_satirlari.append("SORUNLAR:")
            for s in sorunlar:
                ozet_satirlari.append(f"  - {s}")
            ozet_satirlari.append("")
        if oneriler:
            ozet_satirlari.append("ONERILER:")
            for o in oneriler:
                ozet_satirlari.append(f"  * {o}")

        return {
            "kontrol_noktalari": kontrol_noktalari,
            "sorunlar": sorunlar,
            "oneriler": oneriler,
            "genel_durum": genel_durum,
            "ozet_metin": "\n".join(ozet_satirlari),
        }

    def parametre_optimizasyonu(self, tds_parametreler: List[Dict],
                                son_olcumler: Dict,
                                veri_serisi: List[Dict]) -> List[Dict]:
        """
        TDS parametreleri, son olcumler ve trend verilerini analiz ederek
        banyo karti icin optimal kontrol parametrelerini oner.

        Args:
            tds_parametreler: TDS parametre listesi
            son_olcumler: {"sicaklik": 28.5, "ph": 5.8, ...}
            veri_serisi: Son 30 gunluk olcum verileri

        Returns:
            [{"parametre_kodu", "parametre_adi", "birim",
              "tds_min", "tds_hedef", "tds_max",
              "onerilen_min", "onerilen_hedef", "onerilen_max",
              "trend", "durum", "aciklama"}, ...]
        """
        # Trend analizi
        trend_sonuclari = self.trend_analizi(veri_serisi)
        trend_map = {t.parametre: t for t in trend_sonuclari}

        sonuclar = []
        for p in tds_parametreler:
            kod = p.get("parametre_kodu", "")
            adi = p.get("parametre_adi", kod)
            birim = p.get("birim", "")
            tds_min = float(p.get("tds_min") or 0)
            tds_hedef = float(p.get("tds_hedef") or 0)
            tds_max = float(p.get("tds_max") or 0)
            tolerans = float(p.get("tolerans_yuzde") or 10.0)

            # Son olcum
            gercek = son_olcumler.get(kod)
            gercek_f = float(gercek) if gercek is not None else None

            # Trend bilgisi
            trend = trend_map.get(kod)
            trend_yorum = trend.yorum if trend else "veri_yok"
            trend_egim = trend.egim if trend else 0
            trend_ort = trend.ortalama if trend else None

            # --- AI Kural Motoru: Optimal deger hesaplama ---
            onerilen_min = tds_min
            onerilen_hedef = tds_hedef
            onerilen_max = tds_max
            aciklama_parcalari = []

            if tds_hedef > 0:
                aralik = tds_max - tds_min if (tds_max > 0 and tds_min > 0) else tds_hedef * (tolerans / 100) * 2

                if trend_yorum == "artan" and trend_egim > 0:
                    # Parametre artis trendinde - hedefi biraz asagi cek
                    kayma = min(aralik * 0.1, abs(trend_egim) * 7)
                    onerilen_hedef = tds_hedef - kayma
                    aciklama_parcalari.append(f"Artis trendi tespit edildi (egim: {trend_egim:.4f}/gun)")
                    aciklama_parcalari.append(f"Hedef {kayma:.2f} asagi cekildi")

                elif trend_yorum == "azalan" and trend_egim < 0:
                    # Parametre dusus trendinde - hedefi biraz yukari cek
                    kayma = min(aralik * 0.1, abs(trend_egim) * 7)
                    onerilen_hedef = tds_hedef + kayma
                    aciklama_parcalari.append(f"Dusus trendi tespit edildi (egim: {trend_egim:.4f}/gun)")
                    aciklama_parcalari.append(f"Hedef {kayma:.2f} yukari cekildi")

                else:
                    aciklama_parcalari.append("Stabil trend - TDS hedefleri korundu")

                # Gercek deger ile karsilastir
                if gercek_f is not None and tds_hedef > 0:
                    sapma_yuzde = abs((gercek_f - tds_hedef) / tds_hedef * 100)
                    if sapma_yuzde > tolerans * 2:
                        aciklama_parcalari.append(f"KRITIK: Gercek deger ({gercek_f:.2f}) hedeften %{sapma_yuzde:.0f} sapmada")
                    elif sapma_yuzde > tolerans:
                        aciklama_parcalari.append(f"UYARI: Gercek deger ({gercek_f:.2f}) hedeften %{sapma_yuzde:.0f} sapmada")

                # Ortalama bazli ince ayar
                if trend_ort is not None and tds_hedef > 0:
                    ort_sapma = abs(trend_ort - tds_hedef) / tds_hedef * 100
                    if ort_sapma < tolerans * 0.5:
                        aciklama_parcalari.append(f"Ortalama hedef yakininda ({trend_ort:.2f})")

                # Min/Max optimize
                if onerilen_hedef > 0:
                    if tds_min > 0 and tds_max > 0:
                        onerilen_min = tds_min
                        onerilen_max = tds_max
                    else:
                        marj = onerilen_hedef * (tolerans / 100)
                        onerilen_min = onerilen_hedef - marj
                        onerilen_max = onerilen_hedef + marj
            else:
                aciklama_parcalari.append("TDS hedef degeri tanimlanmamis")

            # Durum belirleme
            if gercek_f is not None and tds_hedef > 0:
                sapma_pct = abs((gercek_f - tds_hedef) / tds_hedef * 100)
                if sapma_pct <= tolerans:
                    durum = "NORMAL"
                elif sapma_pct <= tolerans * 2:
                    durum = "UYARI"
                else:
                    durum = "KRITIK"
            else:
                durum = "BILGI_YOK"

            sonuclar.append({
                "parametre_kodu": kod,
                "parametre_adi": adi,
                "birim": birim,
                "tds_min": round(tds_min, 4),
                "tds_hedef": round(tds_hedef, 4),
                "tds_max": round(tds_max, 4),
                "onerilen_min": round(onerilen_min, 4),
                "onerilen_hedef": round(onerilen_hedef, 4),
                "onerilen_max": round(onerilen_max, 4),
                "gercek": round(gercek_f, 4) if gercek_f is not None else None,
                "trend": trend_yorum,
                "durum": durum,
                "aciklama": " | ".join(aciklama_parcalari),
            })

        return sonuclar

    def takviye_onerisi(self, karsilastirma_sonuclari: List[KarsilastirmaSonuc],
                        hacim_lt: float = 1000.0) -> List[TakviyeOneri]:
        """
        Parametre sapmalarina gore kimyasal takviye onerisi.

        Args:
            karsilastirma_sonuclari: karsilastirma() ciktisi
            hacim_lt: Banyo hacmi (litre)

        Returns:
            TakviyeOneri listesi
        """
        oneriler = []
        for ks in karsilastirma_sonuclari:
            if ks.durum == "NORMAL":
                continue

            # Parametre kodunu bul (parametre_adi'ndan)
            param_kod = None
            for kod in self.TAKVIYE_KURALLARI:
                if kod in ks.parametre.lower().replace(" ", "_").replace("ı", "i"):
                    param_kod = kod
                    break

            if not param_kod:
                continue

            kurallar = self.TAKVIYE_KURALLARI[param_kod]
            yonu = "dusuk" if ks.sapma < 0 else "yuksek"
            kural = kurallar.get(yonu)
            if not kural:
                continue

            # Miktar hesaplama: sapma × hacim × faktor
            miktar = abs(ks.sapma) * (hacim_lt / 1000.0) * kural["faktor"]

            # Oncelik
            if ks.durum == "KRITIK":
                oncelik = "ACIL"
            else:
                oncelik = "ORTA"

            oneriler.append(TakviyeOneri(
                parametre=ks.parametre,
                kimyasal=kural["kimyasal"],
                miktar=miktar,
                birim=kural["birim"],
                oncelik=oncelik,
                aciklama=f"{ks.parametre}: {ks.gercek:.2f} (Hedef: {ks.tds_hedef:.2f}, Sapma: {ks.sapma_yuzde:.1f}%)",
            ))

        # Oncelik sirasina gore sirala
        oncelik_sira = {"ACIL": 0, "YUKSEK": 1, "ORTA": 2, "DUSUK": 3}
        oneriler.sort(key=lambda x: oncelik_sira.get(x.oncelik, 99))

        return oneriler


# ============================================================
# OPENAI BACKEND (ISKELET)
# ============================================================

class OpenAIBackend:
    """
    OpenAI API ile gelismis analiz.
    config.json'da 'openai_api_key' yoksa kullanilmaz.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.available = bool(api_key)

    def is_available(self) -> bool:
        return self.available

    def analiz_yap(self, prompt: str) -> Optional[str]:
        """OpenAI API ile analiz yap"""
        if not self.available:
            return None
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Sen bir kataforez banyo kimyasal analiz uzmanisın. "
                     "Turkce yanit ver. Kisa ve oneriye yonelik cevaplar ver."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"OpenAI analiz hatasi: {e}")
            return None


# ============================================================
# ANA SERVIS (FACADE)
# ============================================================

class AIAnalizService:
    """
    AI Analiz ana servisi.
    Kural tabanli backend her zaman calisir.
    OpenAI backend opsiyonel olarak ek yorum saglar.
    """

    def __init__(self):
        self.rule_engine = RuleBasedBackend()
        self.openai_engine = self._init_openai()

    def _init_openai(self) -> OpenAIBackend:
        """config.json'dan OpenAI API key oku"""
        try:
            from core.external_config import config_manager
            api_key = config_manager.get("openai_api_key", "")
            return OpenAIBackend(api_key)
        except Exception:
            return OpenAIBackend(None)

    def tam_analiz(self, banyo_id: int, tds_parametreler: List[Dict],
                   son_olcumler: Dict, veri_serisi: List[Dict],
                   hacim_lt: float = 1000.0) -> Dict[str, Any]:
        """
        Tum analiz turlerini calistir ve sonuclari birlestir.

        Returns:
            {
                "karsilastirma": [...],
                "trend": [...],
                "tahmin": [...],
                "takviye": [...],
                "ai_yorum": str veya None,
                "risk_seviyesi": "NORMAL"|"UYARI"|"KRITIK",
                "tarih": datetime
            }
        """
        # 1. Karsilastirma
        karsilastirma = self.rule_engine.karsilastirma(tds_parametreler, son_olcumler)

        # 2. Trend
        trend = self.rule_engine.trend_analizi(veri_serisi)

        # 3. Tahmin
        tahmin = self.rule_engine.tahmin(veri_serisi, tds_parametreler)

        # 4. Takviye onerileri
        takviye = self.rule_engine.takviye_onerisi(karsilastirma, hacim_lt)

        # Genel risk seviyesi
        risk = "NORMAL"
        for k in karsilastirma:
            if k.durum == "KRITIK":
                risk = "KRITIK"
                break
            elif k.durum == "UYARI" and risk != "KRITIK":
                risk = "UYARI"

        # OpenAI ek yorum (opsiyonel)
        ai_yorum = None
        if self.openai_engine.is_available():
            ozet = self._sonuclari_ozetle(karsilastirma, trend, tahmin, takviye)
            ai_yorum = self.openai_engine.analiz_yap(ozet)

        return {
            "karsilastirma": [k.to_dict() for k in karsilastirma],
            "trend": [t.to_dict() for t in trend],
            "tahmin": [t.to_dict() for t in tahmin],
            "takviye": [t.to_dict() for t in takviye],
            "ai_yorum": ai_yorum,
            "risk_seviyesi": risk,
            "tarih": datetime.now(),
        }

    def kaplama_tds_analiz(self, banyo_id: int, tds_parametreler: List[Dict],
                           banyo_olcumler: Dict, kaplama_test: Dict) -> Dict[str, Any]:
        """
        Kaplama testi icin TDS kontrol analizi.
        Banyo olcumlerini TDS hedefleriyle, kaplama sonuclarini standartlarla karsilastirir.
        """
        sonuc = self.rule_engine.kaplama_tds_kontrol(
            tds_parametreler, banyo_olcumler, kaplama_test)

        # OpenAI ek yorum (opsiyonel)
        if self.openai_engine.is_available():
            prompt = (f"Kaplama test TDS kontrol sonuclari:\n"
                      f"Genel durum: {sonuc['genel_durum']}\n"
                      f"Sorunlar: {'; '.join(sonuc['sorunlar']) if sonuc['sorunlar'] else 'Yok'}\n"
                      f"Bu sonuclara gore kaplama kalitesi icin kisa degerlendirme yap.")
            ai_yorum = self.openai_engine.analiz_yap(prompt)
            if ai_yorum:
                sonuc["ozet_metin"] += f"\n\nAI DEGERLENDIRME:\n{ai_yorum}"

        return sonuc

    def parametre_optimizasyonu(self, banyo_id: int, tds_parametreler: List[Dict],
                                son_olcumler: Dict, veri_serisi: List[Dict]) -> Dict[str, Any]:
        """
        TDS parametrelerinden banyo karti icin AI destekli optimal kontrol parametreleri oner.

        Returns:
            {
                "parametreler": [...],  # optimize edilmis parametre listesi
                "ai_yorum": str veya None,
                "tarih": datetime
            }
        """
        parametreler = self.rule_engine.parametre_optimizasyonu(
            tds_parametreler, son_olcumler, veri_serisi)

        # OpenAI ek yorum
        ai_yorum = None
        if self.openai_engine.is_available():
            satirlar = ["Banyo parametre optimizasyonu sonuclari:\n"]
            for p in parametreler:
                satirlar.append(
                    f"- {p['parametre_adi']}: TDS Hedef={p['tds_hedef']}, "
                    f"Onerilen={p['onerilen_hedef']}, Gercek={p.get('gercek', '-')}, "
                    f"Trend={p['trend']}, Durum={p['durum']}")
            satirlar.append("\nBu sonuclara gore parametre optimizasyonu icin kisa degerlendirme yap.")
            ai_yorum = self.openai_engine.analiz_yap("\n".join(satirlar))

        return {
            "parametreler": parametreler,
            "ai_yorum": ai_yorum,
            "tarih": datetime.now(),
        }

    def _sonuclari_ozetle(self, karsilastirma, trend, tahmin, takviye) -> str:
        """OpenAI'a gonderilecek ozet metin olustur"""
        satirlar = ["Banyo analiz sonuclari:\n"]
        for k in karsilastirma:
            satirlar.append(f"- {k.parametre}: Hedef={k.tds_hedef}, Gercek={k.gercek}, "
                          f"Sapma={k.sapma_yuzde:.1f}%, Durum={k.durum}")
        for t in trend:
            satirlar.append(f"- {t.parametre} trendi: {t.yorum} (egim={t.egim:.4f})")
        for th in tahmin:
            satirlar.append(f"- {th.parametre} 7 gun tahmini: {th.tahmini_7gun:.2f} (Risk: {th.risk})")

        satirlar.append("\nBu sonuclara gore kisa bir degerlendirme ve oneri yap.")
        return "\n".join(satirlar)

    def sonuclari_kaydet(self, banyo_id: int, tds_id: int, analiz_tipi: str,
                         sonuclar: Dict) -> bool:
        """Analiz sonuclarini veritabanina kaydet (cache)"""
        try:
            from core.database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO uretim.banyo_tds_ai_analiz
                (banyo_id, tds_id, analiz_tipi, sonuc_json, ozet, risk_seviyesi, oneriler, ai_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                banyo_id, tds_id, analiz_tipi,
                json.dumps(sonuclar, default=str, ensure_ascii=False),
                sonuclar.get("ai_yorum", ""),
                sonuclar.get("risk_seviyesi", "NORMAL"),
                json.dumps(sonuclar.get("takviye", []), default=str, ensure_ascii=False),
                "openai" if sonuclar.get("ai_yorum") else "rule_based",
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"AI analiz kayit hatasi: {e}")
            return False
