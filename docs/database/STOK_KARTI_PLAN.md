# STOK KARTI GELİŞTİRME PLANI

## 🎯 HEDEF
StokKartlari VIEW → stok.urunler + normalize tablolar geçişi
Tam kapsamlı stok kartı yönetimi

---

## 📊 VERİTABANI DEĞİŞİKLİKLERİ

### 1. stok.urunler TABLOSU - YENİ ALANLAR

```sql
-- Revizyon Takibi
revizyon_no         NVARCHAR(20) NULL,
revizyon_tarihi     DATE NULL,

-- Fiziksel Özellikler
malzeme_cinsi_id    BIGINT NULL,          -- FK: tanim.malzeme_cinsleri
en_mm               DECIMAL(10,2) NULL,
boy_mm              DECIMAL(10,2) NULL,
yukseklik_mm        DECIMAL(10,2) NULL,

-- Kaplama Detay
pasivasyon_tipi_id  BIGINT NULL,          -- FK: tanim.pasivasyon_tipleri
renk_kodu           NVARCHAR(20) NULL,     -- RAL kodu

-- Üretim Parametreleri
varsayilan_hat_id   BIGINT NULL,          -- FK: tanim.uretim_hatlari
aski_tipi_id        BIGINT NULL,          -- FK: tanim.aski_tipleri
aski_adedi          INT NULL,              -- Askıya kaç parça
bara_adedi          INT NULL,              -- Baraya kaç askı
pitch_mm            DECIMAL(8,2) NULL,
yonlendirme         NVARCHAR(20) NULL,     -- DUZGUN, 90_DERECE, EGIMLI
ozel_talimatlar     NVARCHAR(MAX) NULL,    -- Maskeleme vs.

-- Paketleme
ambalaj_turu_id     BIGINT NULL,          -- FK: tanim.ambalaj_turleri
kutu_ici_adet       INT NULL,
palet_kutu_adet     INT NULL,

-- Kalite & İzlenebilirlik
lot_takibi_zorunlu  BIT DEFAULT 0,
lot_kurallari       NVARCHAR(500) NULL,
kabul_kriterleri    NVARCHAR(MAX) NULL,
ozel_kontrol_gerek  NVARCHAR(MAX) NULL,

-- Fiyat
fiyat_tipi          NVARCHAR(20) NULL,     -- ADET, M2, KG
birim_fiyat         DECIMAL(18,6) NULL,
para_birimi_id      BIGINT NULL,          -- FK: tanim.para_birimleri
```

### 2. YENİ LOOKUP TABLOLARI

```sql
-- tanim.malzeme_cinsleri
CREATE TABLE tanim.malzeme_cinsleri (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    kod NVARCHAR(20) NOT NULL,
    ad NVARCHAR(100) NOT NULL,            -- Çelik, Döküm, Aluminyum, Paslanmaz
    aktif_mi BIT DEFAULT 1
);

-- tanim.pasivasyon_tipleri  
CREATE TABLE tanim.pasivasyon_tipleri (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    kod NVARCHAR(20) NOT NULL,
    ad NVARCHAR(100) NOT NULL,            -- Mavi, Sarı, Siyah, Şeffaf
    renk_kodu NVARCHAR(7) NULL,           -- Hex color
    aktif_mi BIT DEFAULT 1
);

-- tanim.aski_tipleri
CREATE TABLE tanim.aski_tipleri (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    kod NVARCHAR(20) NOT NULL,
    ad NVARCHAR(100) NOT NULL,            -- Standart, Özel, Tel askı
    aciklama NVARCHAR(500) NULL,
    aktif_mi BIT DEFAULT 1
);
```

### 3. stok.urun_recete (İŞLEM ADIMLARI)

```sql
CREATE TABLE stok.urun_recete (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    uuid UNIQUEIDENTIFIER DEFAULT NEWID(),
    urun_id BIGINT NOT NULL,              -- FK: stok.urunler
    sira_no INT NOT NULL,
    islem_adi NVARCHAR(100) NOT NULL,     -- Sıcak Yağ Alma, Durulama, vb.
    banyo_tipi_id BIGINT NULL,            -- FK: tanim.banyo_tipleri
    sure_sn INT NULL,                      -- Bekleme süresi (saniye)
    sicaklik_hedef DECIMAL(5,2) NULL,
    akim_hedef DECIMAL(10,2) NULL,
    gerilim_hedef DECIMAL(10,2) NULL,
    ozel_parametre NVARCHAR(500) NULL,
    kontrol_noktasi_mi BIT DEFAULT 0,      -- Kontrol planı için
    kontrol_tipi NVARCHAR(50) NULL,        -- GORSEL, OLCUM, TEST
    kontrol_frekansi NVARCHAR(50) NULL,    -- HER_PARCA, SAATLIK, VARDIYA
    aktif_mi BIT DEFAULT 1,
    
    CONSTRAINT FK_urun_recete_urun FOREIGN KEY (urun_id) REFERENCES stok.urunler(id),
    CONSTRAINT FK_urun_recete_banyo_tipi FOREIGN KEY (banyo_tipi_id) REFERENCES tanim.banyo_tipleri(id)
);
```

### 4. stok.urun_dosyalar

```sql
CREATE TABLE stok.urun_dosyalar (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    uuid UNIQUEIDENTIFIER DEFAULT NEWID(),
    urun_id BIGINT NOT NULL,              -- FK: stok.urunler
    dosya_tipi NVARCHAR(30) NOT NULL,     -- STL, TEKNIK_RESIM, FOTOGRAF, PPAP, TEST_SONUC, DIGER
    dosya_adi NVARCHAR(200) NOT NULL,
    dosya_yolu NVARCHAR(500) NOT NULL,
    dosya_boyutu_kb INT NULL,
    mime_type NVARCHAR(100) NULL,
    aciklama NVARCHAR(500) NULL,
    revizyon_no NVARCHAR(20) NULL,
    yukleme_tarihi DATETIME2 DEFAULT GETDATE(),
    yukleyen_id BIGINT NULL,
    aktif_mi BIT DEFAULT 1,
    
    CONSTRAINT FK_urun_dosyalar_urun FOREIGN KEY (urun_id) REFERENCES stok.urunler(id),
    CONSTRAINT FK_urun_dosyalar_yukleyen FOREIGN KEY (yukleyen_id) REFERENCES sistem.kullanicilar(id)
);
```

---

## 🖥️ UI DEĞİŞİKLİKLERİ (stok_liste.py)

### MEVCUT SEKMELER (Güncelleme)
1. **Genel** → Revizyon bilgileri ekle
2. **Ölçüler** → Malzeme cinsi ekle
3. **Kaplama** → Pasivasyon tipi, askı detayları genişlet
4. **Fiyat/Stok** → Fiyat tipi, para birimi ekle

### YENİ SEKMELER
5. **Üretim** → Hat, askı, bara, pitch, yönlendirme, talimatlar
6. **Paketleme** → Ambalaj, kutu içi, palet
7. **Kalite** → Lot takibi, kabul kriterleri, kontrol gereksinimleri
8. **Reçete** → İşlem adımları tablosu (CRUD)
9. **Dosyalar** → Dosya listesi, yükleme, önizleme

---

## 📋 UYGULAMA SIRASI

### ADIM 1: Veritabanı (SQL Script)
- [ ] tanim.malzeme_cinsleri oluştur
- [ ] tanim.pasivasyon_tipleri oluştur
- [ ] tanim.aski_tipleri oluştur
- [ ] stok.urunler ALTER (yeni alanlar)
- [ ] stok.urun_recete oluştur
- [ ] stok.urun_dosyalar oluştur
- [ ] Varsayılan veriler ekle

### ADIM 2: VIEW Güncelleme (Geçiş Dönemi)
- [ ] StokKartlari VIEW'ı stok.urunler ile senkronize et
- [ ] veya yeni VW_StokKartlari_Detay oluştur

### ADIM 3: UI - StokDetayDialog Güncelleme
- [ ] Mevcut sekmeleri güncelle (combo'lar FK'ya bağla)
- [ ] Üretim sekmesi ekle
- [ ] Paketleme sekmesi ekle
- [ ] Kalite sekmesi ekle
- [ ] Reçete sekmesi ekle (tablo + CRUD)
- [ ] Dosyalar sekmesi ekle (liste + upload)

### ADIM 4: Liste Sayfası
- [ ] Yeni filtrelere göre güncelle
- [ ] Yeni kolonlar ekle

---

## 🔄 GEÇİŞ STRATEJİSİ

```
MEVCUT                          YENİ
┌──────────────┐               ┌──────────────┐
│ StokKartlari │               │ stok.urunler │
│    (VIEW)    │ ──migration─► │   (TABLE)    │
└──────────────┘               └──────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │ urun_recete  │ │ urun_dosyalar│ │urun_spesifik │
            └──────────────┘ └──────────────┘ └──────────────┘
```

---

## ⏱️ TAHMİNİ SÜRE

| Adım | Süre |
|------|------|
| DB Script | 1 saat |
| UI Güncelleme | 3-4 saat |
| Test & Debug | 1 saat |
| **TOPLAM** | ~5-6 saat |

---

## ✅ ONAY BEKLİYOR

Bu plan uygun mu? Başlayalım mı?
