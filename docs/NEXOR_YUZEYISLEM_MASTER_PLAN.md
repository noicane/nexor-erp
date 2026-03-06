# 🎯 REDLINE NEXOR ERP - YÜZEYİŞLEM MASTER PLAN

**Tarih:** 31 Ocak 2026  
**Kapsam:** 4 Hat Tam Entegrasyon (Kataforez + Çinko + Çinko-Nikel + Toz Boya)  
**Versiyon:** 1.0 - Strategic Master Plan

---

## 📊 MEVCUT DURUM ANALİZİ

### Tesiste Bulunan Hatlar:
```
1. 🎨 KATAFOREZ HATTI (KTL)
   └── Ürünler: LB-800 Black, Additive S-TW0672 TBF, TC5020BD, TW5201BD
   
2. ⚡ ÇİNKO HATTI
   └── Proses: Unizinc NCZ 420 (Alkaline Cyanide-free)
   
3. ⚙️ ÇİNKO-NİKEL HATTI  
   └── Proses: ZINKOR Ni 14 CD (%10-15 Ni içerikli)
   
4. 🎨 TOZ BOYA HATTI
   └── Elektrostatik Toz Boya Uygulaması
```

### Şu Anda Kullandığınız Veri Kaynakları:
- ✅ **Kalite Modülü** → Final kalite, proses kalite, red kayıtları
- ✅ **İK PDKS** → Personel süreleri, vardiya bilgileri
- ✅ **Laboratuvar** → Analiz sonuçları (yeni entegre edildi)
- ✅ **Üretim Modülü** → Üretim girişleri, hat takip
- ❌ **TDS Tüketim Sistemi** → YOK (kritik eksiklik!)

---

## 🏭 4 HAT TEKNİK ÖZET

### 1️⃣ KATAFOREZ HATTI (KTL)

**Proses Akışı:**
```
Ön Temizlik → Yağ Alma → Yıkama → Aktifleştirme → Yıkama → 
→ Fosfatlama → Yıkama → Pasifleştirme → Yıkama → 
→ DI Water → KATAFOREZ BANYO → UF Yıkama → DI Yıkama → 
→ Fırın (170-180°C, 20-25 dk)
```

**Kritik Parametreler:**
| Parametre | Hedef | Min | Max | Birim |
|-----------|-------|-----|-----|-------|
| Katı Madde | 18.0 | 16.0 | 20.0 | % |
| pH | 5.8 | 5.6 | 6.0 | - |
| Sıcaklık | 28 | 26 | 30 | °C |
| İletkenlik | 1400 | 1200 | 1600 | µS/cm |
| P/B Oranı | 0.35 | 0.30 | 0.40 | - |
| Film Kalınlığı | 20 | 15 | 25 | µm |

**Kimyasal Tüketim (TDS'den):**
- Additive S-TW0672 TBF: 2.5 L/ton kaplama
- TC5020BD (Add A): 1.8 L/ton
- TW5201BD (Add B): 1.2 L/ton
- LB-800 Black Paste: 35 kg/ton

---

### 2️⃣ ÇİNKO HATTI (Unizinc NCZ 420)

**Proses Akışı:**
```
Yağ Alma (Alkaline) → Yıkama → Asit Dekap → Yıkama → 
→ Aktifleştirme → ÇİNKO KAPLAMA → Yıkama → 
→ Nötralizasyon → Pasivasyona → Yıkama → Kurutma
```

**Kritik Parametreler:**
| Parametre | Rack | Barrel | Birim |
|-----------|------|--------|-------|
| Zn Metal | 10 | 10 | g/L |
| NaOH | 120 | 120 | g/L |
| Sıcaklık | 18-34 | 18-34 | °C |
| Akım Yoğunluğu | 2.0 | 1.0 | A/dm² |
| Verim | 40-90 | 40-90 | % |
| Kaplama Hızı | 0.27 µm/dk @ 1A/dm², %100 verim |

**Kimyasal Tüketim (10,000 Ah başına):**
- Unizinc NCZ 421 3x Conc (Brightener): 0.7-1.0 L
- Unizinc NCZ 422 3x (BG) (Grain Refiner): 0.16-0.34 L
- Unizinc NCZ 420 WS: 0.1 L per kg NaOH replenishment

---

### 3️⃣ ÇİNKO-NİKEL HATTI (ZINKOR Ni 14 CD)

**Proses Akışı:**
```
Yağ Alma → Yıkama → Asit Dekap → Yıkama → 
→ Elektrolit Yağ Alma (2-5 dk) → Yıkama → Asit Dip → 
→ Ön Daldırma (%5 NaOH) → ZnNi KAPLAMA → Yıkama → 
→ Nötralizasyon (0.05-0.1% HCl) → Pasivasyona → Yıkama → Kurutma
```

**Kritik Parametreler:**
| Parametre | Değer | Birim |
|-----------|-------|-------|
| Zn Metal | 5.0-8.0 | g/L |
| Ni Metal | 1.2-2.0 | g/L |
| NaOH | 130-150 | g/L |
| Sıcaklık | 20-27 | °C |
| Akım Yoğunluğu | 1-6 | A/dm² |
| Ni Oranı (hedef) | 10-15 | % |
| Kaplama Hızı | 0.27 µm/dk @ 1A/dm², %100 verim |

**Kimyasal Tüketim (10,000 Ah başına):**
- ZINKOR Ni 14 CNAD (Nickel Solution): 8.0-11.0 L
- ZINKOR Ni 14 CD Brightener: 1.0-1.5 L
- ZINKOR Ni 14 CD Special Additive: 0-0.75 L

**Performans:**
- Korozyon Dayanımı: >1,000 saat beyaz pas (DIN EN ISO 9227)
- Korozyon Dayanımı: >3,000 saat kırmızı pas
- Sıcaklık Dayanımı: 24h @ 120°C sonrası korozyon koruması

---

### 4️⃣ TOZ BOYA HATTI

**Proses Akışı:**
```
Ön Temizlik → Yağ Alma → Yıkama → Fosfatlama → Yıkama → 
→ Pasifleştirme → Yıkama → Kurutma (Ön Fırın) → 
→ TOZ BOYA UYGULAMA → Fırın (180-200°C, 10-15 dk)
```

**Kritik Parametreler:**
| Parametre | Hedef | Birim |
|-----------|-------|-------|
| Gerilim | 60-90 | kV |
| Hava Basıncı | 2.5-3.5 | bar |
| Püskürtme Mesafesi | 20-30 | cm |
| Film Kalınlığı | 60-80 | µm |
| Fırın Sıcaklığı | 180-200 | °C |
| Fırın Süresi | 10-15 | dakika |

**Kimyasal/Malzeme Tüketim:**
- Toz boya: 150-200 g/m² (geri kazanım öncesi)
- Geri kazanım oranı: %95-98
- Net tüketim: 3-10 g/m² (kayıp)

---

## 🎯 STRATEJİK VİZYON: 4 HAT ENT EGRE YÖNETİM

### YENİ MENÜ YAPISI

```
📊 YÖNETİM KONSOLU
   │
   ├── 🎨 KATAFOREZ YÖNETİM
   │   ├── Dashboard (Gerçek Zamanlı)
   │   ├── Banyo Takip (12-15 banyo)
   │   ├── Parametre Trend & SPC
   │   ├── TDS Tüketim Analizi ★
   │   ├── Hata Yönetimi & Pareto
   │   ├── Bakım Planlama
   │   └── Maliyet Optimizasyonu
   │
   ├── ⚡ ÇİNKO YÖNETİM
   │   ├── Dashboard
   │   ├── Banyo Takip (Rack + Barrel)
   │   ├── Parametre Trend
   │   ├── TDS Tüketim Analizi ★
   │   ├── Kaplama Kalınlığı Kontrolü
   │   ├── Brightener/Additive Takip
   │   └── Maliyet Analizi
   │
   ├── ⚙️ ÇİNKO-NİKEL YÖNETİM
   │   ├── Dashboard
   │   ├── Banyo Takip
   │   ├── Ni Oranı Takip (%10-15)
   │   ├── TDS Tüketim Analizi ★
   │   ├── Alloy Composition Monitoring
   │   ├── Pasivasyona Performans
   │   └── Maliyet Analizi
   │
   ├── 🎨 TOZ BOYA YÖNETİM
   │   ├── Dashboard
   │   ├── Kabine Takip
   │   ├── Toz Tüketim & Geri Kazanım
   │   ├── Film Kalınlığı Kontrolü
   │   ├── Fırın Profil Takip
   │   ├── Renk Yönetimi
   │   └── Maliyet Analizi
   │
   └── 📊 KARŞILAŞTIRMALI ANALİZ
       ├── 4 Hat KPI Dashboard
       ├── Hat Bazında Verimlilik
       ├── Maliyet Karşılaştırması
       ├── Kalite Performans Kıyası
       ├── Kapasite Kullanım Analizi
       └── Executive Summary Report
```

---

## 🗄️ VERİTABANI MİMARİSİ

### Mevcut Yapı (Lab Modülü)
```sql
-- ZATEN VAR (Kataforez için kuruldu)
uretim.banyo_analiz_sonuclari
uretim.banyo_tanimlari
uretim.kataforez_hata_kayitlari
uretim.kataforez_hata_tipleri
uretim.kataforez_gunluk_kontrol
uretim.kataforez_haftalik_bakim
uretim.kataforez_periyodik_bakim
uretim.yuzey_alan_hesaplama
uretim.kataforez_maliyet
```

### YENİ TABLOLAR (Tüm Hatlar İçin)

#### 1. Genel Hat Yönetimi
```sql
CREATE TABLE uretim.hat_tanimlari (
    id BIGINT PRIMARY KEY IDENTITY,
    hat_kodu NVARCHAR(50) UNIQUE NOT NULL,  -- KTL, ZN, ZNNI, POWDER
    hat_adi NVARCHAR(200) NOT NULL,
    hat_tipi NVARCHAR(50) NOT NULL,          -- KATAFOREZ, ZINC, ZINC_NICKEL, POWDER_COAT
    aktif BIT DEFAULT 1,
    
    -- Kapasite Bilgileri
    teorik_kapasite_m2_saat DECIMAL(10,2),
    teorik_kapasite_adet_saat INT,
    calisma_rejimi NVARCHAR(50),             -- 1_VARDIYA, 2_VARDIYA, 3_VARDIYA
    
    -- Enerji
    guc_tuketimi_kwh DECIMAL(10,2),
    
    olusturma_tarihi DATETIME2 DEFAULT GETDATE()
);

-- Seed Data
INSERT INTO uretim.hat_tanimlari VALUES
('KTL', 'Kataforez Hattı', 'KATAFOREZ', 1, 120.0, 450, '2_VARDIYA', 75.0, GETDATE()),
('ZN', 'Çinko Hattı (Unizinc NCZ 420)', 'ZINC', 1, 80.0, 300, '2_VARDIYA', 45.0, GETDATE()),
('ZNNI', 'Çinko-Nikel Hattı (ZINKOR Ni 14 CD)', 'ZINC_NICKEL', 1, 65.0, 250, '2_VARDIYA', 50.0, GETDATE()),
('POWDER', 'Toz Boya Hattı', 'POWDER_COAT', 1, 100.0, 400, '2_VARDIYA', 65.0, GETDATE());
```

#### 2. TDS Master Database (KRİTİK!)
```sql
CREATE TABLE uretim.urun_tds_master (
    id BIGINT PRIMARY KEY IDENTITY,
    urun_id BIGINT REFERENCES stok.urunler(id),
    hat_kodu NVARCHAR(50) REFERENCES uretim.hat_tanimlari(hat_kodu),
    
    -- TDS Dosyası
    tds_dosya_path NVARCHAR(500),
    tds_versiyon NVARCHAR(50),
    tds_tarih DATE,
    gecerlilik_baslangic DATE,
    gecerlilik_bitis DATE,
    
    -- Ürün Özellikleri
    yuzey_alan_m2 DECIMAL(10,4),
    agirlik_kg DECIMAL(10,3),
    kalinlik_mm DECIMAL(8,3),
    
    -- Hedef Değerler (Her hat için)
    hedef_film_kalinlik_um DECIMAL(8,2),
    hedef_kaplama_suresi_dk INT,
    
    -- Kataforez Özel
    hedef_ktl_kati_madde_yuzde DECIMAL(5,2),
    hedef_ktl_ph DECIMAL(4,2),
    hedef_ktl_sicaklik_c DECIMAL(5,2),
    hedef_ktl_pb_orani DECIMAL(5,3),
    hedef_ktl_boya_g_m2 DECIMAL(10,2),
    hedef_ktl_additive_s_ml_m2 DECIMAL(10,2),
    hedef_ktl_additive_a_ml_m2 DECIMAL(10,2),
    hedef_ktl_additive_b_ml_m2 DECIMAL(10,2),
    
    -- Çinko Özel
    hedef_zn_metal_gl DECIMAL(6,2),
    hedef_zn_naoh_gl DECIMAL(6,2),
    hedef_zn_sicaklik_c DECIMAL(5,2),
    hedef_zn_akim_a_dm2 DECIMAL(5,2),
    hedef_zn_brightener_ml_10kah DECIMAL(10,2),
    hedef_zn_grain_refiner_ml_10kah DECIMAL(10,2),
    
    -- Çinko-Nikel Özel
    hedef_znni_zn_gl DECIMAL(6,2),
    hedef_znni_ni_gl DECIMAL(6,2),
    hedef_znni_naoh_gl DECIMAL(6,2),
    hedef_znni_ni_oran_yuzde DECIMAL(5,2),        -- 10-15%
    hedef_znni_akim_a_dm2 DECIMAL(5,2),
    hedef_znni_ni_solution_ml_10kah DECIMAL(10,2),
    hedef_znni_brightener_ml_10kah DECIMAL(10,2),
    
    -- Toz Boya Özel
    hedef_powder_kalinlik_um INT,
    hedef_powder_tuketim_g_m2 DECIMAL(10,2),
    hedef_powder_geri_kazanim_yuzde DECIMAL(5,2),
    hedef_powder_gerilim_kv DECIMAL(5,1),
    hedef_powder_basinc_bar DECIMAL(4,2),
    hedef_powder_firin_sicaklik_c INT,
    hedef_powder_firin_sure_dk INT,
    
    -- Kalite Kriterleri (Ortak)
    min_kalinlik_um INT,
    max_kalinlik_um INT,
    min_adezyon_mpa DECIMAL(5,2),
    max_porozite_adet INT,
    
    -- Toleranslar
    tolerans_yuzde DECIMAL(5,2) DEFAULT 5.0,
    
    -- Maliyet Bilgileri (TDS'den)
    hedef_kimyasal_maliyet_eur_m2 DECIMAL(10,4),
    hedef_enerji_maliyet_eur_m2 DECIMAL(10,4),
    hedef_isguc_maliyet_eur_m2 DECIMAL(10,4),
    hedef_toplam_maliyet_eur_m2 DECIMAL(10,4),
    
    aktif BIT DEFAULT 1,
    olusturma_tarihi DATETIME2 DEFAULT GETDATE(),
    guncellenme_tarihi DATETIME2 DEFAULT GETDATE(),
    olusturan_id BIGINT REFERENCES sistem.kullanicilar(id)
);

CREATE INDEX idx_tds_urun_hat ON uretim.urun_tds_master(urun_id, hat_kodu, aktif);
```

#### 3. Gerçekleşen Üretim Log (4 Hat)
```sql
CREATE TABLE uretim.hat_uretim_log (
    id BIGINT PRIMARY KEY IDENTITY,
    is_emri_id BIGINT,
    urun_id BIGINT REFERENCES stok.urunler(id),
    hat_kodu NVARCHAR(50) REFERENCES uretim.hat_tanimlari(hat_kodu),
    
    tarih DATE NOT NULL,
    vardiya_id BIGINT,
    baslangic_saat TIME,
    bitis_saat TIME,
    
    -- Üretim Miktarları
    planlanan_adet INT,
    uretilen_adet INT,
    iyi_adet INT,
    red_adet INT,
    rework_adet INT,
    
    -- Yüzey Alanı
    uretilen_toplam_m2 DECIMAL(12,2),
    
    -- Süre
    toplam_sure_dk INT,
    net_uretim_sure_dk INT,
    durus_sure_dk INT,
    
    -- Operatörler
    operator_id BIGINT,
    operator_2_id BIGINT,
    
    -- Kimyasal Tüketim (Hat Tipine Göre)
    -- KATAFOREZ
    ktl_kullanilan_boya_kg DECIMAL(10,3),
    ktl_additive_s_litre DECIMAL(10,3),
    ktl_additive_a_litre DECIMAL(10,3),
    ktl_additive_b_litre DECIMAL(10,3),
    
    -- ÇİNKO
    zn_brightener_litre DECIMAL(10,3),
    zn_grain_refiner_litre DECIMAL(10,3),
    zn_ws_litre DECIMAL(10,3),
    
    -- ÇİNKO-NİKEL
    znni_ni_solution_litre DECIMAL(10,3),
    znni_brightener_litre DECIMAL(10,3),
    znni_special_additive_litre DECIMAL(10,3),
    
    -- TOZ BOYA
    powder_kullanilan_kg DECIMAL(10,3),
    powder_geri_kazanim_kg DECIMAL(10,3),
    powder_fire_kg DECIMAL(10,3),
    
    -- Enerji
    kullanilan_enerji_kwh DECIMAL(10,3),
    
    -- Maliyet (Otomatik Hesaplanan)
    birim_kimyasal_maliyet_eur_m2 DECIMAL(10,4),
    birim_enerji_maliyet_eur_m2 DECIMAL(10,4),
    birim_isguc_maliyet_eur_m2 DECIMAL(10,4),
    birim_toplam_maliyet_eur_m2 DECIMAL(10,4),
    
    toplam_kimyasal_maliyet_eur DECIMAL(12,2),
    toplam_enerji_maliyet_eur DECIMAL(12,2),
    toplam_isguc_maliyet_eur DECIMAL(12,2),
    toplam_maliyet_eur DECIMAL(12,2),
    
    -- Notlar
    notlar NVARCHAR(MAX),
    
    kayit_tarihi DATETIME2 DEFAULT GETDATE(),
    kaydeden_id BIGINT REFERENCES sistem.kullanicilar(id)
);

CREATE INDEX idx_hat_uretim_tarih ON uretim.hat_uretim_log(tarih, hat_kodu);
CREATE INDEX idx_hat_uretim_ie ON uretim.hat_uretim_log(is_emri_id);
```

#### 4. TDS Sapma Analizi (Günlük Otomatik)
```sql
CREATE TABLE uretim.tds_sapma_analiz (
    id BIGINT PRIMARY KEY IDENTITY,
    uretim_log_id BIGINT REFERENCES uretim.hat_uretim_log(id),
    analiz_tarihi DATE NOT NULL,
    hat_kodu NVARCHAR(50),
    urun_id BIGINT,
    
    -- TDS Hedef vs Gerçekleşen
    tds_hedef_kimyasal_eur_m2 DECIMAL(10,4),
    gerceklesen_kimyasal_eur_m2 DECIMAL(10,4),
    sapma_kimyasal_eur_m2 DECIMAL(10,4),
    sapma_kimyasal_yuzde DECIMAL(6,2),
    
    tds_hedef_sure_dk INT,
    gerceklesen_sure_dk INT,
    sapma_sure_dk INT,
    sapma_sure_yuzde DECIMAL(6,2),
    
    tds_hedef_enerji_eur_m2 DECIMAL(10,4),
    gerceklesen_enerji_eur_m2 DECIMAL(10,4),
    sapma_enerji_yuzde DECIMAL(6,2),
    
    tds_hedef_toplam_eur_m2 DECIMAL(10,4),
    gerceklesen_toplam_eur_m2 DECIMAL(10,4),
    sapma_toplam_eur_m2 DECIMAL(10,4),
    sapma_toplam_yuzde DECIMAL(6,2),
    
    -- Aylık Kümülatif Etki
    aylik_fazla_harcama_eur DECIMAL(12,2),
    yillik_tahmini_etki_eur DECIMAL(12,2),
    
    -- AI Öneriler
    kok_neden_1 NVARCHAR(500),
    kok_neden_2 NVARCHAR(500),
    kok_neden_3 NVARCHAR(500),
    
    oneri_1 NVARCHAR(500),
    oneri_2 NVARCHAR(500),
    oneri_3 NVARCHAR(500),
    
    potansiyel_tasarruf_eur_ay DECIMAL(10,2),
    
    olusturma_tarihi DATETIME2 DEFAULT GETDATE()
);

CREATE INDEX idx_sapma_tarih_hat ON uretim.tds_sapma_analiz(analiz_tarihi, hat_kodu);
```

#### 5. Banyo Takip (4 Hat - Genişletilmiş)
```sql
CREATE TABLE uretim.hat_banyo_tanimlari (
    id BIGINT PRIMARY KEY IDENTITY,
    hat_kodu NVARCHAR(50) REFERENCES uretim.hat_tanimlari(hat_kodu),
    banyo_kodu NVARCHAR(50) NOT NULL,
    banyo_adi NVARCHAR(200) NOT NULL,
    banyo_tipi NVARCHAR(100),                    -- KAPLAMA, ON_ISLEM, YIKAMA, PASIVASYONA
    sira_no INT,
    
    kapasite_litre DECIMAL(10,2),
    aktif BIT DEFAULT 1,
    
    -- Parametreler (JSON veya ayrı tabloda)
    parametre_tanimlari NVARCHAR(MAX),           -- JSON
    
    UNIQUE(hat_kodu, banyo_kodu)
);

CREATE TABLE uretim.hat_banyo_analiz (
    id BIGINT PRIMARY KEY IDENTITY,
    banyo_id BIGINT REFERENCES uretim.hat_banyo_tanimlari(id),
    analiz_tarihi DATETIME2 NOT NULL,
    analiz_tipi NVARCHAR(50),                    -- GUNLUK, HAFTALIK, AYLIK
    
    -- Ortak Parametreler
    sicaklik_c DECIMAL(5,2),
    ph DECIMAL(4,2),
    iletkenlik_us_cm INT,
    
    -- Kataforez Özel
    ktl_kati_madde_yuzde DECIMAL(5,2),
    ktl_pb_orani DECIMAL(5,3),
    ktl_solvent_yuzde DECIMAL(5,2),
    ktl_meq DECIMAL(6,2),
    ktl_demir_ppm DECIMAL(8,2),
    ktl_cinko_ppm DECIMAL(8,2),
    
    -- Çinko Özel
    zn_metal_gl DECIMAL(6,2),
    zn_naoh_gl DECIMAL(6,2),
    zn_karbonat_gl DECIMAL(6,2),
    
    -- Çinko-Nikel Özel
    znni_zn_gl DECIMAL(6,2),
    znni_ni_gl DECIMAL(6,2),
    znni_naoh_gl DECIMAL(6,2),
    znni_ni_oran_yuzde DECIMAL(5,2),             -- Gerçek alloy oranı
    
    -- Sonuçlar
    sonuc NVARCHAR(50),                          -- NORMAL, UYARI, KRITIK
    notlar NVARCHAR(MAX),
    
    analizci_id BIGINT REFERENCES sistem.kullanicilar(id),
    kayit_tarihi DATETIME2 DEFAULT GETDATE()
);

CREATE INDEX idx_banyo_analiz_tarih ON uretim.hat_banyo_analiz(analiz_tarihi);
```

#### 6. Kimyasal Stok & Otomatik İkmal
```sql
CREATE TABLE uretim.kimyasal_stok (
    id BIGINT PRIMARY KEY IDENTITY,
    kimyasal_kodu NVARCHAR(100) UNIQUE NOT NULL,
    kimyasal_adi NVARCHAR(200) NOT NULL,
    tedarikci NVARCHAR(200),
    
    -- Stok
    mevcut_miktar DECIMAL(10,2),
    birim NVARCHAR(20),                          -- KG, LITRE, ADET
    minimum_stok DECIMAL(10,2),
    maksimum_stok DECIMAL(10,2),
    
    -- Maliyet
    birim_fiyat_eur DECIMAL(10,4),
    son_alis_tarihi DATE,
    
    -- Uyarı
    stok_durumu NVARCHAR(50),                    -- YETERLI, DUSUK, KRITIK
    
    aktif BIT DEFAULT 1,
    guncellenme_tarihi DATETIME2 DEFAULT GETDATE()
);

-- Seed Data (Örnekler)
INSERT INTO uretim.kimyasal_stok VALUES
('KTL_LB800', 'LB-800 Black Paste', 'Nippon Paint', 1250.0, 'KG', 500.0, 2000.0, 12.50, '2026-01-15', 'YETERLI', 1, GETDATE()),
('KTL_ADD_S', 'Additive S-TW0672 TBF', 'Nippon Paint', 85.0, 'LITRE', 30.0, 150.0, 45.00, '2026-01-20', 'YETERLI', 1, GETDATE()),
('ZN_421', 'Unizinc NCZ 421 3x Conc (Brightener)', 'Atotech', 45.0, 'LITRE', 20.0, 100.0, 38.50, '2026-01-10', 'YETERLI', 1, GETDATE()),
('ZN_422', 'Unizinc NCZ 422 3x (BG)', 'Atotech', 22.0, 'LITRE', 10.0, 50.0, 42.00, '2026-01-10', 'YETERLI', 1, GETDATE()),
('ZNNI_NI', 'ZINKOR Ni 14 CNAD (Nickel Solution)', 'DR. HESSE', 125.0, 'LITRE', 50.0, 200.0, 55.00, '2026-01-18', 'YETERLI', 1, GETDATE()),
('ZNNI_BRIGHT', 'ZINKOR Ni 14 CD Brightener', 'DR. HESSE', 18.0, 'LITRE', 10.0, 50.0, 48.00, '2026-01-18', 'DUSUK', 1, GETDATE());

CREATE TABLE uretim.kimyasal_hareket (
    id BIGINT PRIMARY KEY IDENTITY,
    kimyasal_id BIGINT REFERENCES uretim.kimyasal_stok(id),
    hareket_tipi NVARCHAR(50),                   -- GIRIS, CIKIS, SAYIM, FIRE
    miktar DECIMAL(10,2),
    birim NVARCHAR(20),
    
    -- Çıkış için
    uretim_log_id BIGINT,
    hat_kodu NVARCHAR(50),
    
    aciklama NVARCHAR(500),
    hareket_tarihi DATETIME2 DEFAULT GETDATE(),
    kaydeden_id BIGINT REFERENCES sistem.kullanicilar(id)
);
```

---

## 🔄 VERİ AKIŞI & ENTEGRASYONLAR

### 1. İş Emri → TDS Eşleştirme
```
İş Emri Oluşturma
    ↓
[Ürün Seç] → [Hat Seç]
    ↓
Sistem otomatik TDS'yi çeker:
    urun_tds_master tablosu
    ↓
Hedef değerler gösterilir:
    - Kimyasal tüketim
    - Süre
    - Maliyet
    ↓
Üretim başlar
```

### 2. Üretim Gerçekleşme
```
Üretim Tamamlandı
    ↓
Operatör hat_uretim_log kaydını girer:
    - Adet
    - Kullanılan kimyasal (manuel/otomatik tartım)
    - Süre
    ↓
Sistem otomatik hesaplar:
    - m² bazında tüketim
    - Birim maliyet
    ↓
Kalite kontrolü:
    - Film kalınlığı
    - Adezyon
    - Görünüm
    ↓
TDS Sapma Analizi (otomatik trigger):
    - Hedef vs Gerçekleşen
    - Sapma %
    - Maliyet farkı
    - AI öneriler
```

### 3. Laboratuvar Analiz
```
Günlük Analiz (Sabah 08:00)
    ↓
Lab teknisyeni analiz yapar:
    hat_banyo_analiz
    ↓
Parametreler kaydedilir:
    - pH, Sıcaklık, İletkenlik
    - Katı madde, P/B, MEQ (KTL)
    - Zn, Ni oranları
    ↓
Sistem kontrol eder:
    - Normal aralıkta mı?
    - Uyarı/Kritik seviye mi?
    ↓
Eğer kritik → Alarm:
    - Dashboard'da kırmızı
    - Email/SMS gönder
    - Üretim durdur (opsiyonel)
```

### 4. Kimyasal Stok Takip
```
Üretim yapıldı
    ↓
Kimyasal kullanıldı (log'a kaydedildi)
    ↓
Trigger: kimyasal_stok güncellenir
    - Mevcut stok azalır
    ↓
Eğer stok < minimum_stok:
    - stok_durumu = 'DUSUK'
    - Satınalma talebine otomatik ekle
    ↓
Eğer stok < kritik_seviye (%10):
    - Alarm
    - Acil tedarik talebi
```

### 5. PDKS Entegrasyonu
```
Vardiya başlangıcı
    ↓
PDKS'den personel listesi çekilir:
    ik.pdks_kayitlar
    ↓
Hat üretim log'una operatör atanır
    ↓
Vardiya bitişi
    ↓
Toplam çalışma saati hesaplanır
    ↓
İşgücü maliyeti:
    (Çalışma saati × Saatlik ücret) / Üretilen m²
```

---

## 📊 PYTHON MODÜL YAPISI

### Genel Hat Yönetimi
```
modules/yonetim/
├── hatlar/
│   ├── hat_dashboard.py               # 4 Hat Genel Dashboard
│   ├── hat_karsilastirma.py          # Hat Bazında Karşılaştırma
│   └── hat_kapasite_analiz.py        # Kapasite Kullanım Analizi
│
├── kataforez/
│   ├── ktl_dashboard.py              # KTL Dashboard
│   ├── ktl_banyo_takip.py            # 12-15 Banyo Takip
│   ├── ktl_parametre_trend.py        # SPC Grafikleri
│   ├── ktl_tds_tuketim.py            # TDS vs Gerçekleşen ★
│   ├── ktl_hata_yonetim.py           # Hata + Pareto
│   ├── ktl_bakim_planlama.py         # Bakım Takvimi
│   └── ktl_maliyet_optimizasyon.py   # AI Öneriler
│
├── cinko/
│   ├── zn_dashboard.py
│   ├── zn_banyo_takip.py
│   ├── zn_parametre_trend.py
│   ├── zn_tds_tuketim.py             # ★
│   ├── zn_kalinlik_kontrolu.py
│   ├── zn_additive_takip.py
│   └── zn_maliyet_analiz.py
│
├── cinko_nikel/
│   ├── znni_dashboard.py
│   ├── znni_banyo_takip.py
│   ├── znni_ni_oran_takip.py         # %10-15 kontrol
│   ├── znni_tds_tuketim.py           # ★
│   ├── znni_alloy_composition.py     # Alaşım takip
│   ├── znni_pasivation_perf.py
│   └── znni_maliyet_analiz.py
│
├── toz_boya/
│   ├── powder_dashboard.py
│   ├── powder_kabine_takip.py
│   ├── powder_tuketim_geri_kazanim.py
│   ├── powder_kalinlik_kontrol.py
│   ├── powder_firin_profil.py
│   ├── powder_renk_yonetim.py
│   └── powder_maliyet_analiz.py
│
└── ortak/
    ├── tds_yukleme.py                # TDS PDF Parser
    ├── tds_master_yonetim.py         # TDS CRUD
    ├── kimyasal_stok_yonetim.py      # Stok Takip
    ├── sapma_analiz_motor.py         # Otomatik sapma hesaplama
    └── ai_oneri_motoru.py            # Makine öğrenmesi önerileri
```

---

## 🎯 ÖNCELİK SIRASI & YOL HARİTASI

### FAZ 1: TEMELİ KURALIM (1-2 Hafta) - KRİTİK

**1.1 Veritabanı (3 gün)**
```sql
✅ hat_tanimlari
✅ urun_tds_master (4 hat için)
✅ hat_uretim_log
✅ tds_sapma_analiz
✅ hat_banyo_tanimlari
✅ hat_banyo_analiz
✅ kimyasal_stok
✅ kimyasal_hareket
```

**1.2 Menü Güncellemesi (1 gün)**
```python
# core/menu_structure.py
{"id": "yonetim", "icon": "📊", "label": "Yönetim Konsolu", "children": [
    {"id": "hat_genel_dashboard", "label": "4 Hat Dashboard"},
    {"id": "yonetim_ktl", "label": "🎨 Kataforez"},
    {"id": "yonetim_zn", "label": "⚡ Çinko"},
    {"id": "yonetim_znni", "label": "⚙️ Çinko-Nikel"},
    {"id": "yonetim_powder", "label": "🎨 Toz Boya"},
]}
```

**1.3 TDS Yükleme Modülü (2 gün)**
```python
# modules/yonetim/ortak/tds_yukleme.py
# PDF Parser ile TDS'lerden veri çekme
# Manuel düzeltme + kaydetme
```

**1.4 Basit Hat Dashboard (2 gün)**
```python
# modules/yonetim/hatlar/hat_dashboard.py
# 4 hattın özeti, günlük üretim, canlı durum
```

---

### FAZ 2: KATAFOREZ DERİNLEŞME (2 Hafta)

**Öncelik sırası:**
1. KTL Dashboard (1 gün)
2. KTL TDS Tüketim Analizi ★ (3 gün)
3. KTL Banyo Takip (2 gün)
4. KTL Parametre Trend & SPC (2 gün)
5. KTL Hata Yönetimi (2 gün)
6. KTL Bakım Planlama (2 gün)
7. KTL Maliyet Optimizasyonu + AI (2 gün)

---

### FAZ 3: ÇİNKO & ÇİNKO-NİKEL (2 Hafta)

**Çinko Hattı:**
1. ZN Dashboard (1 gün)
2. ZN TDS Tüketim ★ (2 gün)
3. ZN Banyo Takip (1 gün)
4. ZN Parametre Trend (1 gün)
5. ZN Kalınlık Kontrolü (1 gün)
6. ZN Additive Takip (1 gün)
7. ZN Maliyet Analizi (1 gün)

**Çinko-Nikel Hattı:**
1. ZNNI Dashboard (1 gün)
2. ZNNI TDS Tüketim ★ (2 gün)
3. ZNNI Ni Oranı Takip (%10-15) (1 gün)
4. ZNNI Alloy Composition (1 gün)
5. ZNNI Pasivasyona Performans (1 gün)
6. ZNNI Maliyet Analizi (1 gün)

---

### FAZ 4: TOZ BOYA (1 Hafta)

1. Powder Dashboard (1 gün)
2. Powder Kabine Takip (1 gün)
3. Powder Tüketim & Geri Kazanım (1 gün)
4. Powder Kalınlık Kontrol (1 gün)
5. Powder Fırın Profil (1 gün)
6. Powder Renk Yönetimi (1 gün)
7. Powder Maliyet (1 gün)

---

### FAZ 5: AI & OPTİMİZASYON (2 Hafta)

1. Sapma Analiz Motoru (otomatik) (3 gün)
2. AI Öneri Motoru (3 gün)
3. Predictive Maintenance (3 gün)
4. Maliyet Optimizasyon Simülasyonu (2 gün)
5. Executive Reports (2 gün)

---

### FAZ 6: RAPORLAR & DASHBOARD (1 Hafta)

1. Hat Karşılaştırmalı Analiz
2. KPI Scorecard (4 Hat)
3. Executive Summary
4. PDF/Excel Export
5. Email Otomasyonu

---

## 📋 HEMEN YAPMAMIZ GEREKENLER

### ⚠️ KRİTİK EKSİKLİKLER

1. **TDS Veritabanı YOK!**
   - Hiçbir ürünün TDS değerleri sistemde yok
   - Manuel giriş gerekiyor
   - PDF'lerden parse edilmeli

2. **Kimyasal Stok Takibi YOK!**
   - Hangi kimyasaldan ne kadar var bilinmiyor
   - Otomatik ikmal sistemi yok

3. **Gerçekleşen Tüketim Kaydı YOK!**
   - Üretimde ne kadar kimyasal kullanıldığı kayıt altında değil
   - Manuel tartım/kayıt gerekiyor

4. **4 Hat Ayrı Entegrasyon YOK!**
   - Sadece kataforez için lab_analiz.py var
   - Diğer 3 hat için benzer modüller yok

---

## 💡 ÖNERİLER

### Teknik Öneriler

1. **TDS Parser Geliştir**
   ```python
   # PDF'den otomatik çekim
   import PyPDF2, pdfplumber
   
   def parse_tds_pdf(file_path, hat_tipi):
       # Regex ile parametreleri çek
       # Tabloya kaydet
   ```

2. **Tartım Entegrasyonu**
   - Kimyasal tankları için dijital tartım sistemleri
   - Otomatik veri gönderimi (RS-485, Modbus)
   - Gerçek zamanlı stok güncellemesi

3. **PLC Entegrasyonu**
   - Hat başlatma/durdurma
   - Enerji tüketimi ölçümü
   - Süre takibi

4. **Barkod/QR Sistemi**
   - Her iş emrine QR kod
   - Operatör okutarak üretimi başlatır
   - Otomatik log kaydı

### Operasyonel Öneriler

1. **Günlük Rutin**
   - 08:00: Lab analizi (4 hat)
   - 16:00: Vardiya raporu
   - 22:00: Günlük özet

2. **Haftalık Rutin**
   - Pazartesi: Haftalık planlama
   - Cuma: Haftalık performans review
   - Kimyasal sipariş kontrolü

3. **Aylık Rutin**
   - TDS vs Gerçekleşen analizi
   - Maliyet optimizasyon toplantısı
   - Bakım planlaması

---

## 🚀 BAŞLANGIÇ PLANI (İLK 1 HAFTA)

### Gün 1-2: Veritabanı
- Tüm tabloları oluştur
- Seed data ekle
- Test et

### Gün 3-4: TDS Yükleme
- PDF parser yaz
- Manuel düzeltme UI'ı
- İlk 10 ürünün TDS'ini yükle

### Gün 5-6: Basit Dashboard
- 4 hat özet dashboard
- Günlük üretim gösterimi
- Canlı durum

### Gün 7: Test & Demo
- Tüm sistemi test et
- Demo hazırla
- Kullanıcı eğitimi

---

## 📊 BEKLENEN SONUÇLAR

### 3 Ay Sonra:
- ✅ 4 hat tam entegre
- ✅ TDS tüketim analizi çalışıyor
- ✅ Gerçek zamanlı dashboardlar
- ✅ Otomatik sapma analizi
- ✅ Kimyasal stok takibi

### 6 Ay Sonra:
- ✅ AI önerileri aktif
- ✅ Predictive maintenance
- ✅ Tam otomasyon (tartım, PLC)
- ✅ Executive raporlar
- ✅ Mobil erişim

### 1 Yıl Sonra:
- ✅ %8-12 maliyet düşüşü
- ✅ %15+ OEE artışı
- ✅ %30+ kalite iyileşmesi
- ✅ Tam paperless üretim
- ✅ Predictive quality control

---

## 🎯 BAŞLAYALIM MI?

**İlk adım ne olsun?**

1. **Veritabanı kuralım** (SQL scriptleri hazırlayayım)
2. **TDS Parser yazalım** (PDF'lerden veri çekelim)
3. **Dashboard prototip** (4 hattın genel görünümü)

Hangisinden başlamak istersin? 🚀
