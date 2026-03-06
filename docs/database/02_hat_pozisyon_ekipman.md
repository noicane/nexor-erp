# HAT - POZİSYON - EKİPMAN HİYERARŞİSİ

## Genel Mimari

```
┌─────────────────────────────────────────────────────────────────┐
│                         HAT BOLUMU                               │
│                        (E-HAT Kombine)                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ E-HAT       │  │ E-HAT       │  │ E-HAT       │              │
│  │ ÖN İŞLEM    │  │ ZN/Nİ       │  │ KTL         │              │
│  │ (Poz 1-22)  │  │ (Poz 200+)  │  │ (Poz 101+)  │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐              │
│  │ POZİSYONLAR │  │ POZİSYONLAR │  │ POZİSYONLAR │              │
│  │ (Tanklar)   │  │ (Tanklar)   │  │ (Tanklar)   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│  ┌──────▼──────────────────────────────────────────┐            │
│  │              EKİPMANLAR                          │            │
│  │  • Pompalar      • Isıtıcılar    • Filtreler    │            │
│  │  • Valfler       • Sensörler     • Motorlar     │            │
│  │  • Rektifiyörler • Redüktörler   • Fanlar       │            │
│  └─────────────────────────────────────────────────┘            │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  ROBOT 1    │  │  ROBOT 2    │  │  ROBOT 3    │              │
│  │  (2 Robot)  │  │  (2+1 Robot)│  │  (3 Robot)  │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                                                        │
│  ┌──────▼──────────────────────────────────────────┐            │
│  │           ROBOT EKİPMANLARI                      │            │
│  │  • Servo Motorlar  • Encoderlar  • Redüktörler  │            │
│  │  • Kablolar        • Sensörler   • Frenler      │            │
│  └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

# TABLO YAPILARI

## 1. tanim.hat_bolumleri
Kombine hat grupları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | E-HAT |
| ad | NVARCHAR(100) | ✓ | E Hat (Kombine Çinko-KTL) |
| aciklama | NVARCHAR(500) | | |
| plc_ip_adresi | NVARCHAR(50) | | Ana PLC IP |
| plc_rack | INT | | |
| plc_slot | INT | | |
| sql_veri_kaynagi | NVARCHAR(200) | | PLC SQL bağlantı string |
| sql_veritabani | NVARCHAR(100) | | PLC veritabanı adı |
| sira | INT | | Görüntüleme sırası |
| aktif_mi | BIT | ✓ | |

---

## 2. tanim.uretim_hatlari
Hat bölümleri (her biri ayrı üretim hattı)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| hat_bolum_id | BIGINT | | FK: tanim.hat_bolumleri |
| kod | NVARCHAR(20) | ✓ | E-HAT-ONISLEM |
| ad | NVARCHAR(100) | ✓ | E Hat - Ön İşlem |
| kisa_ad | NVARCHAR(30) | | Ön İşlem |
| kaplama_turu_id | BIGINT | | FK: tanim.kaplama_turleri |
| hat_tipi | NVARCHAR(30) | ✓ | ON_ISLEM, KAPLAMA, KURUTMA, FIRIN |
| sira_no | INT | | Proses sırası (1, 2, 3...) |
| robot_sayisi | INT | | |
| toplam_pozisyon | INT | | |
| devir_suresi_dk | INT | | Dakika cinsinden |
| kapasite_saat_m2 | DECIMAL(10,2) | | m²/saat |
| renk_kodu | NVARCHAR(7) | | UI için (#FF5733) |
| aktif_mi | BIT | ✓ | |

---

## 3. tanim.pozisyon_tipleri
Pozisyon tipi tanımları (lookup)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(30) | ✓ | BANYO, GECIS, ISTASYON, FIRIN, KURUTMA, ROBOT_ALANI |
| ad | NVARCHAR(50) | ✓ | |
| ikon | NVARCHAR(50) | | UI ikonu |
| renk_kodu | NVARCHAR(7) | | |
| aktif_mi | BIT | ✓ | |

---

## 4. tanim.banyo_tipleri
Banyo tipi tanımları (lookup)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(30) | ✓ | |
| ad | NVARCHAR(100) | ✓ | |
| kategori | NVARCHAR(30) | ✓ | ON_ISLEM, KAPLAMA, DURULAMA, PASIVASYON, KURUTMA |
| kimyasal_gerekli_mi | BIT | | |
| sicaklik_gerekli_mi | BIT | | |
| ph_gerekli_mi | BIT | | |
| akim_gerekli_mi | BIT | | Elektroliz banyoları için |
| aktif_mi | BIT | ✓ | |

**Örnek Veriler:**
```
KOD                  | AD                      | KATEGORİ
---------------------|-------------------------|----------
SPREY_YIKAMA         | Sprey Yıkama            | ON_ISLEM
SICAK_YAG_ALMA       | Sıcak Yağ Alma          | ON_ISLEM
ULTRASONIK           | Ultrasonik Yıkama       | ON_ISLEM
ASIDIK_YAG_ALMA      | Asidik Yağ Alma         | ON_ISLEM
ASIDIK_SOKME         | Asidik Sökme            | ON_ISLEM
ELEKTRIKLI_YAG_ALMA  | Elektrikli Yağ Alma     | ON_ISLEM
DURULAMA             | Durulama                | DURULAMA
SYA_DURULAMA         | SYA Durulama            | DURULAMA
ALK_DURULAMA         | Alkali Durulama         | DURULAMA
AKTIVASYON           | Aktivasyon              | ON_ISLEM
FOSFAT               | Fosfat                  | ON_ISLEM
ALKALI_ZN_KAPLAMA    | Alkali Çinko Kaplama    | KAPLAMA
ZN_NI_KAPLAMA        | Çinko Nikel Kaplama     | KAPLAMA
KTL_KAPLAMA          | Kataforez Kaplama       | KAPLAMA
MAVI_PAS             | Mavi Pasivasyon         | PASIVASYON
SEFFAF_PAS           | Şeffaf Pasivasyon       | PASIVASYON
DIA                  | DIA                     | DURULAMA
UF                   | Ultra Filtrasyon        | DURULAMA
NOTR                 | Nötr                    | DURULAMA
KURUTMA              | Kurutma                 | KURUTMA
FIRIN                | Fırın                   | KURUTMA
```

---

## 5. tanim.hat_pozisyonlar
Hat pozisyonları (Tank/İstasyon)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| hat_id | BIGINT | ✓ | FK: tanim.uretim_hatlari |
| pozisyon_no | INT | ✓ | 201, 202, 101, 102... |
| sensor_no | INT | | PLC sensör numarası |
| plc_pozisyon_adi | NVARCHAR(50) | | POS 30, POS 31 |
| ad | NVARCHAR(100) | ✓ | Sıcak Yağ Alma 1 |
| kisa_ad | NVARCHAR(30) | | SYA-1 |
| pozisyon_tipi_id | BIGINT | ✓ | FK: tanim.pozisyon_tipleri |
| banyo_tipi_id | BIGINT | | FK: tanim.banyo_tipleri |
| tank_tipi | NVARCHAR(20) | | TEKLI, CIFTLI |
| gecis_tipi | NVARCHAR(20) | | ISLAK, KURU (geçiş pozisyonları için) |
| sira_no | INT | ✓ | Fiziksel sıra |
| hacim_lt | DECIMAL(10,2) | | Tank hacmi (litre) |
| sicaklik_min | DECIMAL(5,2) | | |
| sicaklik_max | DECIMAL(5,2) | | |
| sicaklik_hedef | DECIMAL(5,2) | | |
| ph_min | DECIMAL(4,2) | | |
| ph_max | DECIMAL(4,2) | | |
| ph_hedef | DECIMAL(4,2) | | |
| akim_min | DECIMAL(10,2) | | Amper |
| akim_max | DECIMAL(10,2) | | |
| akim_hedef | DECIMAL(10,2) | | |
| bekleme_suresi_sn | INT | | Daldırma süresi (saniye) |
| sql_tablo_adi | NVARCHAR(100) | | PLC SQL tablo adı |
| sql_sicaklik_kolon | NVARCHAR(100) | | |
| sql_ph_kolon | NVARCHAR(100) | | |
| sql_akim_kolon | NVARCHAR(100) | | |
| sql_durum_kolon | NVARCHAR(100) | | |
| notlar | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

## 6. tanim.hat_robotlar
Hatlardaki robotlar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| hat_id | BIGINT | ✓ | FK: tanim.uretim_hatlari |
| robot_no | INT | ✓ | 1, 2, 3 |
| kod | NVARCHAR(20) | ✓ | E-ON-R1 |
| ad | NVARCHAR(100) | ✓ | Ön İşlem Robot 1 |
| robot_tipi | NVARCHAR(50) | | TASIYICI, DALDIRMA, TRANSFER |
| marka | NVARCHAR(50) | | |
| model | NVARCHAR(50) | | |
| seri_no | NVARCHAR(50) | | |
| pozisyon_baslangic | INT | | Çalışma alanı başlangıç |
| pozisyon_bitis | INT | | Çalışma alanı bitiş |
| max_taşima_kg | DECIMAL(10,2) | | Maksimum taşıma kapasitesi |
| sql_tablo_adi | NVARCHAR(100) | | PLC SQL tablo adı |
| sql_durum_kolon | NVARCHAR(100) | | |
| sql_pozisyon_kolon | NVARCHAR(100) | | |
| kurulum_tarihi | DATE | | |
| garanti_bitis | DATE | | |
| notlar | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

## 7. tanim.ekipman_kategorileri
Ekipman kategorileri (lookup)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(30) | ✓ | |
| ad | NVARCHAR(100) | ✓ | |
| ust_kategori_id | BIGINT | | FK (hiyerarşi için) |
| ikon | NVARCHAR(50) | | |
| aktif_mi | BIT | ✓ | |

**Örnek Veriler:**
```
KOD              | AD                  | ÜST KATEGORİ
-----------------|---------------------|-------------
POMPA            | Pompalar            | NULL
ISITICI          | Isıtıcılar          | NULL
FILTRE           | Filtreler           | NULL
VALF             | Valfler             | NULL
SENSOR           | Sensörler           | NULL
MOTOR            | Motorlar            | NULL
REDUKTOR         | Redüktörler         | NULL
REKTIFIYOR       | Rektifiyörler       | NULL
FAN              | Fanlar              | NULL
ENCODER          | Encoderlar          | NULL
FREN             | Frenler             | NULL
KONVEYOR         | Konveyörler         | NULL
```

---

## 8. tanim.ekipman_tipleri
Ekipman tipleri (kategorilerin alt kırılımı)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kategori_id | BIGINT | ✓ | FK: tanim.ekipman_kategorileri |
| kod | NVARCHAR(30) | ✓ | |
| ad | NVARCHAR(100) | ✓ | |
| varsayilan_bakim_periyodu_gun | INT | | |
| kritik_mi | BIT | | |
| aktif_mi | BIT | ✓ | |

**Örnek Veriler:**
```
KATEGORİ | KOD              | AD                    | PERİYOT
---------|------------------|----------------------|--------
POMPA    | POMPA_SIRKUL     | Sirkülasyon Pompası  | 90
POMPA    | POMPA_DOZAJ      | Dozaj Pompası        | 30
POMPA    | POMPA_TRANSFER   | Transfer Pompası     | 90
ISITICI  | ISITICI_ELEKTRIK | Elektrikli Isıtıcı   | 180
ISITICI  | ISITICI_BUHAR    | Buhar Eşanjörü       | 180
FILTRE   | FILTRE_TORBA     | Torba Filtre         | 30
FILTRE   | FILTRE_KARBON    | Karbon Filtre        | 90
SENSOR   | SENSOR_SICAKLIK  | Sıcaklık Sensörü     | 365
SENSOR   | SENSOR_PH        | pH Sensörü           | 180
SENSOR   | SENSOR_ILETKEN   | İletkenlik Sensörü   | 180
MOTOR    | MOTOR_SERVO      | Servo Motor          | 365
MOTOR    | MOTOR_ASENKRON   | Asenkron Motor       | 180
```

---

## 9. bakim.ekipmanlar
Ana ekipman tablosu (TÜM EKİPMANLAR)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| ekipman_kodu | NVARCHAR(50) | ✓ | E-ON-P01-POMPA-01 |
| ekipman_adi | NVARCHAR(150) | ✓ | Sıcak Yağ Alma 1 - Sirkülasyon Pompası |
| ekipman_tipi_id | BIGINT | ✓ | FK: tanim.ekipman_tipleri |
| ust_ekipman_id | BIGINT | | FK: bakim.ekipmanlar (hiyerarşi) |
| hat_id | BIGINT | | FK: tanim.uretim_hatlari |
| pozisyon_id | BIGINT | | FK: tanim.hat_pozisyonlar |
| robot_id | BIGINT | | FK: tanim.hat_robotlar |
| lokasyon | NVARCHAR(100) | | Serbest metin lokasyon |
| marka | NVARCHAR(50) | | |
| model | NVARCHAR(50) | | |
| seri_no | NVARCHAR(50) | | |
| uretici | NVARCHAR(100) | | |
| tedarikci_id | BIGINT | | FK: musteri.cariler |
| kurulum_tarihi | DATE | | |
| garanti_bitis | DATE | | |
| satinalma_tarihi | DATE | | |
| satinalma_fiyati | DECIMAL(18,2) | | |
| kritiklik | NVARCHAR(20) | | A, B, C (A: En kritik) |
| durum | NVARCHAR(30) | ✓ | CALISIR, ARIZALI, BAKIMDA, DEVRE_DISI, HURDA |
| teknik_ozellikler | NVARCHAR(MAX) | | JSON formatında |
| guc_kw | DECIMAL(10,2) | | Güç (kW) |
| kapasite | NVARCHAR(50) | | 100 lt/dk, 5 m³/h vb. |
| dokuman_yolu | NVARCHAR(500) | | Teknik doküman |
| resim_yolu | NVARCHAR(500) | | |
| notlar | NVARCHAR(MAX) | | |
| aktif_mi | BIT | ✓ | |

---

## 10. bakim.ekipman_parametre_tanimlari
Ekipman izleme parametreleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| ekipman_id | BIGINT | ✓ | FK: bakim.ekipmanlar |
| parametre_adi | NVARCHAR(50) | ✓ | Sıcaklık, Basınç, Titreşim |
| birim | NVARCHAR(20) | | °C, bar, mm/s |
| min_deger | DECIMAL(18,4) | | |
| max_deger | DECIMAL(18,4) | | |
| hedef_deger | DECIMAL(18,4) | | |
| alarm_alt | DECIMAL(18,4) | | |
| alarm_ust | DECIMAL(18,4) | | |
| sql_tablo_adi | NVARCHAR(100) | | PLC SQL tablo |
| sql_kolon_adi | NVARCHAR(100) | | PLC SQL kolon |
| aktif_mi | BIT | ✓ | |

---

## 11. bakim.ekipman_sayaclari
Ekipman çalışma sayaçları (saat, devir, vb.)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| ekipman_id | BIGINT | ✓ | FK: bakim.ekipmanlar |
| sayac_tipi | NVARCHAR(30) | ✓ | CALISMA_SAATI, DEVIR, URETIM_ADEDI |
| birim | NVARCHAR(20) | | saat, adet, devir |
| mevcut_deger | DECIMAL(18,2) | | |
| son_sifirlama_tarihi | DATETIME2 | | |
| sql_tablo_adi | NVARCHAR(100) | | |
| sql_kolon_adi | NVARCHAR(100) | | |
| aktif_mi | BIT | ✓ | |

---

## 12. bakim.periyodik_bakim_planlari (Güncelleme)
Pozisyon ve ekipman bazlı bakım planları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| plan_kodu | NVARCHAR(30) | ✓ | PBP-001 |
| plan_adi | NVARCHAR(100) | ✓ | |
| ekipman_id | BIGINT | | FK: bakim.ekipmanlar |
| pozisyon_id | BIGINT | | FK: tanim.hat_pozisyonlar (tank bakımı için) |
| robot_id | BIGINT | | FK: tanim.hat_robotlar |
| bakim_tipi | NVARCHAR(30) | ✓ | PERIYODIK, CALISMA_SAATI, SAYAC |
| periyot_gun | INT | | Her X günde bir |
| periyot_calisma_saati | INT | | Her X saatte bir |
| periyot_sayac | DECIMAL(18,2) | | Sayaç değerine göre |
| son_bakim_tarihi | DATE | | |
| son_bakim_sayac | DECIMAL(18,2) | | |
| sonraki_bakim_tarihi | DATE | ✓ | |
| sonraki_bakim_sayac | DECIMAL(18,2) | | |
| tahmini_sure_dk | INT | | |
| talimat | NVARCHAR(MAX) | | Bakım talimatları |
| kontrol_listesi | NVARCHAR(MAX) | | JSON: checklist |
| sorumlu_departman_id | BIGINT | | FK: ik.departmanlar |
| maliyet_tahmini | DECIMAL(18,2) | | |
| uyari_gun_oncesi | INT | | Kaç gün önce uyarı |
| kritik_mi | BIT | | |
| aktif_mi | BIT | ✓ | |

---

## 13. bakim.bakim_kontrol_maddeleri
Bakım planı kontrol listesi maddeleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| plan_id | BIGINT | ✓ | FK: bakim.periyodik_bakim_planlari |
| sira_no | INT | ✓ | |
| madde | NVARCHAR(500) | ✓ | Yapılacak iş |
| olcum_gerekli_mi | BIT | | Ölçüm değeri girilecek mi |
| birim | NVARCHAR(20) | | |
| min_deger | DECIMAL(18,4) | | |
| max_deger | DECIMAL(18,4) | | |
| kritik_mi | BIT | | |
| aktif_mi | BIT | ✓ | |

---

## 14. bakim.bakim_kayitlari (Güncelleme)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kayit_no | NVARCHAR(30) | ✓ | BKM-2024-00001 |
| bakim_tipi | NVARCHAR(30) | ✓ | PERIYODIK, ARIZA, KESTIRIMCI, REVIZY ON |
| plan_id | BIGINT | | FK: bakim.periyodik_bakim_planlari |
| ariza_id | BIGINT | | FK: bakim.ariza_bildirimleri |
| ekipman_id | BIGINT | | FK: bakim.ekipmanlar |
| pozisyon_id | BIGINT | | FK: tanim.hat_pozisyonlar |
| robot_id | BIGINT | | FK: tanim.hat_robotlar |
| hat_id | BIGINT | | FK: tanim.uretim_hatlari |
| planlanan_tarih | DATE | | |
| baslama_zamani | DATETIME2 | ✓ | |
| bitis_zamani | DATETIME2 | | |
| sure_dk | INT | | |
| yapilan_islemler | NVARCHAR(MAX) | | |
| bulgular | NVARCHAR(MAX) | | |
| sonuc | NVARCHAR(30) | | TAMAMLANDI, DEVAM_EDECEK, IPTAL |
| teknisyen_id | BIGINT | ✓ | FK: ik.personeller |
| onaylayan_id | BIGINT | | FK: ik.personeller |
| iscilik_maliyeti | DECIMAL(18,2) | | |
| malzeme_maliyeti | DECIMAL(18,2) | | |
| toplam_maliyet | DECIMAL(18,2) | | |
| sayac_degeri | DECIMAL(18,2) | | Bakım anındaki sayaç |
| notlar | NVARCHAR(MAX) | | |

---

## 15. bakim.bakim_kontrol_kayitlari
Bakım sırasında yapılan kontroller

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| bakim_kayit_id | BIGINT | ✓ | FK: bakim.bakim_kayitlari |
| kontrol_madde_id | BIGINT | ✓ | FK: bakim.bakim_kontrol_maddeleri |
| yapildi_mi | BIT | | |
| olcum_degeri | DECIMAL(18,4) | | |
| sonuc | NVARCHAR(20) | | UYGUN, UYGUNSUZ, ATLANIDI |
| notlar | NVARCHAR(500) | | |

---

# ÖRNEK VERİ YAPISI: E-HAT ÖN İŞLEM

## Pozisyonlar ve Ekipmanları

```
E-HAT-ONISLEM (Hat ID: 1)
│
├── POZ-001 (Sprey Yıkama) - Pozisyon ID: 1
│   ├── EKP-001: Sprey Pompası 1 (POMPA_SIRKUL)
│   ├── EKP-002: Sprey Pompası 2 (POMPA_SIRKUL)
│   ├── EKP-003: Isıtıcı (ISITICI_BUHAR)
│   ├── EKP-004: Sıcaklık Sensörü (SENSOR_SICAKLIK)
│   └── EKP-005: Basınç Sensörü (SENSOR_BASINC)
│
├── POZ-002 (Sıcak Yağ Alma 1) - Pozisyon ID: 2
│   ├── EKP-006: Sirkülasyon Pompası (POMPA_SIRKUL)
│   ├── EKP-007: Transfer Pompası (POMPA_TRANSFER)
│   ├── EKP-008: Isıtıcı 1 (ISITICI_ELEKTRIK)
│   ├── EKP-009: Isıtıcı 2 (ISITICI_ELEKTRIK)
│   ├── EKP-010: Torba Filtre (FILTRE_TORBA)
│   ├── EKP-011: Sıcaklık Sensörü (SENSOR_SICAKLIK)
│   └── EKP-012: pH Sensörü (SENSOR_PH)
│
├── POZ-003 (Sıcak Yağ Alma 2) - Pozisyon ID: 3
│   └── ... (benzer ekipmanlar)
│
├── ROBOT-001 (Robot 1) - Robot ID: 1
│   ├── EKP-050: Kaldırma Servo Motor (MOTOR_SERVO)
│   ├── EKP-051: İleri-Geri Servo Motor (MOTOR_SERVO)
│   ├── EKP-052: Encoder 1 (ENCODER)
│   ├── EKP-053: Encoder 2 (ENCODER)
│   ├── EKP-054: Redüktör (REDUKTOR)
│   └── EKP-055: Fren (FREN)
│
└── ROBOT-002 (Robot 2) - Robot ID: 2
    └── ... (benzer ekipmanlar)
```

---

# API ENDPOINTLERİ

## Hat Pozisyon Yönetimi

```
/api/v1/hatlar/{hat_id}/pozisyonlar
├── GET    /                    # Pozisyon listesi
├── POST   /                    # Yeni pozisyon ekle
├── GET    /{pozisyon_id}       # Pozisyon detay
├── PUT    /{pozisyon_id}       # Pozisyon güncelle
├── DELETE /{pozisyon_id}       # Pozisyon sil (soft delete)
├── PUT    /{pozisyon_id}/sira  # Sıra değiştir
│
├── GET    /{pozisyon_id}/ekipmanlar      # Pozisyona bağlı ekipmanlar
├── POST   /{pozisyon_id}/ekipmanlar      # Pozisyona ekipman ekle
└── DELETE /{pozisyon_id}/ekipmanlar/{id} # Ekipman çıkar

/api/v1/hatlar/{hat_id}/robotlar
├── GET    /                    # Robot listesi
├── POST   /                    # Yeni robot ekle
├── GET    /{robot_id}          # Robot detay
├── PUT    /{robot_id}          # Robot güncelle
├── DELETE /{robot_id}          # Robot sil
│
├── GET    /{robot_id}/ekipmanlar         # Robota bağlı ekipmanlar
├── POST   /{robot_id}/ekipmanlar         # Robota ekipman ekle
└── DELETE /{robot_id}/ekipmanlar/{id}    # Ekipman çıkar

/api/v1/ekipmanlar
├── GET    /                    # Tüm ekipmanlar (filtreli)
├── POST   /                    # Yeni ekipman
├── GET    /{id}                # Ekipman detay
├── PUT    /{id}                # Ekipman güncelle
├── DELETE /{id}                # Ekipman sil
├── GET    /{id}/bakim-gecmisi  # Bakım geçmişi
├── GET    /{id}/bakim-planlari # Bakım planları
└── POST   /{id}/ariza-bildir   # Arıza bildirimi oluştur
```

---

# UI EKRANLARI

## 1. Hat Dizilim Editörü
- Sürükle-bırak ile pozisyon sıralama
- Pozisyon ekleme/çıkarma
- Pozisyon özelliklerini düzenleme
- Tank tipi seçimi (Tekli/Çiftli)
- Banyo tipi seçimi

## 2. Ekipman Ağacı Görünümü
```
[E-HAT]
 ├── [Ön İşlem]
 │   ├── [POZ-001: Sprey Yıkama]
 │   │   ├── Pompa 1 ⚙️ Çalışıyor
 │   │   ├── Pompa 2 ⚙️ Çalışıyor
 │   │   └── Isıtıcı 🔥 Çalışıyor
 │   ├── [POZ-002: Sıcak Yağ Alma 1]
 │   │   └── ...
 │   └── [ROBOT-001]
 │       ├── Servo Motor 1 ⚙️
 │       └── Servo Motor 2 ⚙️
 └── [ZN/Ni Kaplama]
     └── ...
```

## 3. Bakım Panosu
- Yaklaşan bakımlar (pozisyon/ekipman bazlı)
- Geciken bakımlar (kırmızı uyarı)
- Ekipman durumu özeti
- Arıza bildirimleri

---

# VERSİYON

| Versiyon | Tarih | Açıklama |
|----------|-------|----------|
| 1.0 | 2024 | Hat-Pozisyon-Ekipman hiyerarşisi |
