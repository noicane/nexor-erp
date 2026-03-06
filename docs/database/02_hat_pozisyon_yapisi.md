# HAT VE POZİSYON YAPISI

## Genel Mimari

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   S7-1500 PLC   │────▶│  SQL Server     │────▶│  Atmo Logic ERP │
│   (Saha)        │     │  (PLC Verileri) │     │  (Yeni DB)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        Mevcut Tablolar:
                        - Banyo parametreleri
                        - Pozisyon durumları
                        - Sensör verileri
```

---

# YENİ/GÜNCELLENMİŞ TABLOLAR

## tanim.hat_bolumler
Hat ana bölümleri (E-HAT gibi kombine hatlar için)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | E-HAT |
| ad | NVARCHAR(100) | ✓ | E Hat (Kombine) |
| aciklama | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

## tanim.uretim_hatlari (Güncelleme)
Her hat bölümü ayrı kayıt

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | E-HAT-ONISLEM |
| ad | NVARCHAR(100) | ✓ | E Hat - Ön İşlem |
| hat_bolum_id | BIGINT | | FK: tanim.hat_bolumler (kombine hatlar için) |
| kaplama_turu_id | BIGINT | | FK: tanim.kaplama_turleri |
| hat_tipi | NVARCHAR(30) | ✓ | ON_ISLEM, KAPLAMA, KURUTMA, FIRIN |
| sira_no | INT | | Proses sırası |
| pozisyon_baslangic | INT | | İlk pozisyon no |
| pozisyon_bitis | INT | | Son pozisyon no |
| robot_sayisi | INT | | |
| plc_veri_kaynagi | NVARCHAR(100) | | SQL bağlantı adı |
| aktif_mi | BIT | ✓ | |

---

## tanim.hat_pozisyonlar
Hat içindeki tüm pozisyonlar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| hat_id | BIGINT | ✓ | FK: tanim.uretim_hatlari |
| pozisyon_no | INT | ✓ | 201, 202, ... |
| sensor_no | INT | | 200, 201, ... |
| plc_pozisyon_adi | NVARCHAR(50) | | POS 30, POS 31 |
| sira_no | INT | ✓ | Fiziksel sıra |
| pozisyon_tipi | NVARCHAR(30) | ✓ | BANYO, GECIS, ISTASYON, FIRIN, ROBOT |
| banyo_id | BIGINT | | FK: uretim.banyo_tanimlari |
| banyo_tipi | NVARCHAR(20) | | TEKLI, CIFTLI |
| gecis_tipi | NVARCHAR(20) | | ISLAK, KURU (geçiş pozisyonları için) |
| sql_kaynak_tablo | NVARCHAR(100) | | PLC SQL'deki tablo adı |
| sql_kaynak_kolon | NVARCHAR(100) | | PLC SQL'deki kolon adı |
| aktif_mi | BIT | ✓ | |

---

## tanim.hat_robotlar
Hatlardaki robotlar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| hat_id | BIGINT | ✓ | FK: tanim.uretim_hatlari |
| robot_kodu | NVARCHAR(20) | ✓ | E-HAT-R1 |
| robot_adi | NVARCHAR(100) | | Robot 1 |
| robot_tipi | NVARCHAR(50) | | TASIYICI, DALDIRMA |
| pozisyon_baslangic | INT | | Çalışma alanı başlangıç |
| pozisyon_bitis | INT | | Çalışma alanı bitiş |
| sql_kaynak_tablo | NVARCHAR(100) | | |
| aktif_mi | BIT | ✓ | |

---

## uretim.banyo_tanimlari (Güncelleme)
Banyo tanımlarına ek alanlar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | BNY-E-001 |
| ad | NVARCHAR(100) | ✓ | Sıcak Yağ Alma 1 |
| hat_id | BIGINT | ✓ | FK |
| pozisyon_id | BIGINT | | FK: tanim.hat_pozisyonlar |
| banyo_tipi | NVARCHAR(50) | ✓ | Aşağıdaki listeye göre |
| banyo_kategorisi | NVARCHAR(30) | ✓ | ON_ISLEM, KAPLAMA, DURULAMA, PASIVASYON, KURUTMA |
| hacim_lt | DECIMAL(10,2) | | |
| sicaklik_min | DECIMAL(5,2) | | |
| sicaklik_max | DECIMAL(5,2) | | |
| sicaklik_hedef | DECIMAL(5,2) | | |
| sql_sicaklik_tag | NVARCHAR(100) | | PLC SQL'deki sıcaklık kolonu |
| sql_ph_tag | NVARCHAR(100) | | PLC SQL'deki pH kolonu |
| sql_akim_tag | NVARCHAR(100) | | PLC SQL'