# ATMO LOGIC ERP - VERİTABANI ŞEMASI

## Genel Bilgiler

- **Veritabanı:** SQL Server 2019+
- **Karakter Seti:** Turkish_CI_AS
- **Adlandırma:** Türkçe, snake_case

---

## ŞEMALAR (SCHEMAS)

| Şema | Açıklama |
|------|----------|
| `tanim` | Sabit tanım tabloları (lookup) |
| `musteri` | Müşteri ve cari yönetimi |
| `siparis` | Sipariş ve iş emirleri |
| `uretim` | Üretim ve hat yönetimi |
| `stok` | Stok ve depo yönetimi |
| `kalite` | Kalite kontrol ve laboratuvar |
| `bakim` | Bakım yönetimi |
| `ik` | İnsan kaynakları |
| `sistem` | Kullanıcı ve yetkilendirme |
| `entegrasyon` | Dış sistem entegrasyonları |
| `log` | Denetim izleri |

---

## ORTAK ALANLAR

Her tabloda bulunacak standart alanlar:

```sql
id                  BIGINT IDENTITY(1,1) PRIMARY KEY,
uuid                UNIQUEIDENTIFIER DEFAULT NEWID() NOT NULL,
olusturma_tarihi    DATETIME2 DEFAULT GETDATE() NOT NULL,
guncelleme_tarihi   DATETIME2 DEFAULT GETDATE() NOT NULL,
olusturan_id        BIGINT NOT NULL,      -- FK: sistem.kullanicilar
guncelleyen_id      BIGINT NOT NULL,      -- FK: sistem.kullanicilar
silindi_mi          BIT DEFAULT 0 NOT NULL,
silinme_tarihi      DATETIME2 NULL,
silen_id            BIGINT NULL
```

---

# ŞEMA: tanim (Sabit Tanımlar)

## tanim.kaplama_turleri
Kaplama türleri tanımları (Kataforez, Çinko, vb.)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | KTF, ZN, ZNNI, TOZ |
| ad | NVARCHAR(100) | ✓ | Kataforez, Çinko, vb. |
| aciklama | NVARCHAR(500) | | |
| renk_kodu | NVARCHAR(7) | | UI için (#FF5733) |
| sira | INT | | Görüntüleme sırası |
| aktif_mi | BIT | ✓ | Varsayılan: 1 |

---

## tanim.uretim_hatlari
Üretim hatları tanımları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | HAT-01, HAT-02 |
| ad | NVARCHAR(100) | ✓ | Kataforez Hattı 1 |
| kaplama_turu_id | BIGINT | ✓ | FK: tanim.kaplama_turleri |
| plc_ip_adresi | NVARCHAR(50) | | S7-1500 IP |
| plc_rack | INT | | |
| plc_slot | INT | | |
| kapasite_saat | DECIMAL(10,2) | | m²/saat |
| kapasite_aski | INT | | Askı sayısı |
| calisme_suresi_dk | INT | | Devir süresi (dakika) |
| aktif_mi | BIT | ✓ | |

---

## tanim.birimler
Ölçü birimleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(10) | ✓ | KG, LT, M2, ADET |
| ad | NVARCHAR(50) | ✓ | Kilogram, Litre |
| kategori | NVARCHAR(30) | ✓ | agirlik, hacim, alan, adet |
| aktif_mi | BIT | ✓ | |

---

## tanim.para_birimleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(3) | ✓ | TRY, USD, EUR |
| sembol | NVARCHAR(5) | ✓ | ₺, $, € |
| ad | NVARCHAR(50) | ✓ | |
| varsayilan_mi | BIT | | |
| aktif_mi | BIT | ✓ | |

---

## tanim.ulkeler

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(3) | ✓ | TR, DE, US |
| ad | NVARCHAR(100) | ✓ | Türkiye |
| aktif_mi | BIT | ✓ | |

---

## tanim.sehirler

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| ulke_id | BIGINT | ✓ | FK: tanim.ulkeler |
| plaka_kodu | NVARCHAR(5) | | 34, 16 |
| ad | NVARCHAR(100) | ✓ | İstanbul, Bursa |
| aktif_mi | BIT | ✓ | |

---

## tanim.ilceler

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| sehir_id | BIGINT | ✓ | FK: tanim.sehirler |
| ad | NVARCHAR(100) | ✓ | |
| aktif_mi | BIT | ✓ | |

---

## tanim.hata_turleri
Kalite hata türleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | HT001 |
| ad | NVARCHAR(100) | ✓ | Kabarcık, Çatlak, vb. |
| kategori | NVARCHAR(50) | | Görsel, Ölçüsel, vb. |
| onem_derecesi | INT | | 1-5 (1: kritik) |
| aciklama | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

## tanim.test_turleri
Laboratuvar test türleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | TUZ, KALINLIK, YAPISMA |
| ad | NVARCHAR(100) | ✓ | Tuz Sisi Testi |
| kategori | NVARCHAR(50) | | Korozyon, Mekanik, Kimyasal |
| birim_id | BIGINT | | FK: tanim.birimler |
| varsayilan_min | DECIMAL(18,4) | | Varsayılan min değer |
| varsayilan_max | DECIMAL(18,4) | | Varsayılan max değer |
| test_suresi_saat | DECIMAL(8,2) | | Test süresi |
| metot_standardi | NVARCHAR(50) | | ISO 9227, ASTM B117 |
| aciklama | NVARCHAR(1000) | | |
| aktif_mi | BIT | ✓ | |

---

## tanim.durus_nedenleri
Üretim duruş nedenleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | |
| ad | NVARCHAR(100) | ✓ | |
| kategori | NVARCHAR(50) | ✓ | Planlı, Arıza, Kalite, Malzeme |
| oee_etkisi | BIT | ✓ | OEE hesabına dahil mi |
| aktif_mi | BIT | ✓ | |

---

## tanim.ambalaj_turleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | |
| ad | NVARCHAR(100) | ✓ | Koli, Palet, Kasa |
| max_kapasite | DECIMAL(10,2) | | |
| birim_id | BIGINT | | FK: tanim.birimler |
| aktif_mi | BIT | ✓ | |

---

## tanim.vardiyalar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(10) | ✓ | V1, V2, V3 |
| ad | NVARCHAR(50) | ✓ | Sabah, Akşam, Gece |
| baslangic_saati | TIME | ✓ | 08:00 |
| bitis_saati | TIME | ✓ | 16:00 |
| mola_suresi_dk | INT | | Toplam mola süresi |
| aktif_mi | BIT | ✓ | |

---

## tanim.oem_standartlari
OEM müşteri standartları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(50) | ✓ | VW TL 211, BMW GS 90010 |
| ad | NVARCHAR(200) | ✓ | |
| oem_firma | NVARCHAR(100) | | VW, BMW, Mercedes |
| aciklama | NVARCHAR(1000) | | |
| dokuman_yolu | NVARCHAR(500) | | PDF/Dosya yolu |
| aktif_mi | BIT | ✓ | |

---

## tanim.kimyasal_kategoriler

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | |
| ad | NVARCHAR(100) | ✓ | Ön İşlem, Kaplama, Pasivasyou |
| aktif_mi | BIT | ✓ | |

---

# ŞEMA: musteri (Müşteri Yönetimi)

## musteri.cariler
Ana müşteri/tedarikçi tablosu

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| cari_tipi | NVARCHAR(20) | ✓ | MUSTERI, TEDARIKCI, HER_IKISI |
| cari_kodu | NVARCHAR(30) | ✓ | Unique |
| unvan | NVARCHAR(250) | ✓ | |
| kisa_ad | NVARCHAR(50) | | |
| vergi_dairesi | NVARCHAR(100) | | |
| vergi_no | NVARCHAR(20) | | |
| tc_kimlik_no | NVARCHAR(11) | | Şahıs firmaları için |
| ulke_id | BIGINT | | FK: tanim.ulkeler |
| sehir_id | BIGINT | | FK: tanim.sehirler |
| ilce_id | BIGINT | | FK: tanim.ilceler |
| adres | NVARCHAR(500) | | |
| posta_kodu | NVARCHAR(10) | | |
| telefon | NVARCHAR(20) | | |
| faks | NVARCHAR(20) | | |
| email | NVARCHAR(100) | | |
| web_sitesi | NVARCHAR(200) | | |
| para_birimi_id | BIGINT | | FK: tanim.para_birimleri |
| odeme_vade_gun | INT | | Varsayılan vade |
| kredi_limiti | DECIMAL(18,2) | | |
| risk_durumu | NVARCHAR(20) | | NORMAL, RISKLI, BLOKE |
| zirve_cari_kodu | NVARCHAR(50) | | Zirve entegrasyon kodu |
| notlar | NVARCHAR(MAX) | | |
| aktif_mi | BIT | ✓ | |

---

## musteri.cari_adresler
Alternatif teslimat/fatura adresleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| cari_id | BIGINT | ✓ | FK: musteri.cariler |
| adres_tipi | NVARCHAR(20) | ✓ | SEVKIYAT, FATURA |
| adres_adi | NVARCHAR(100) | ✓ | Fabrika, Depo-1 |
| ulke_id | BIGINT | | FK |
| sehir_id | BIGINT | | FK |
| ilce_id | BIGINT | | FK |
| adres | NVARCHAR(500) | ✓ | |
| posta_kodu | NVARCHAR(10) | | |
| yetkili_kisi | NVARCHAR(100) | | |
| telefon | NVARCHAR(20) | | |
| varsayilan_mi | BIT | | |
| aktif_mi | BIT | ✓ | |

---

## musteri.cari_yetkililer
Müşteri yetkili kişileri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| cari_id | BIGINT | ✓ | FK: musteri.cariler |
| ad_soyad | NVARCHAR(100) | ✓ | |
| unvan | NVARCHAR(100) | | Satın Alma Müdürü |
| departman | NVARCHAR(100) | | Satın Alma, Kalite |
| telefon | NVARCHAR(20) | | |
| cep_telefon | NVARCHAR(20) | | |
| email | NVARCHAR(100) | | |
| birincil_yetkili_mi | BIT | | |
| notlar | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

## musteri.cari_spesifikasyonlar
Müşteri bazlı kaplama spesifikasyonları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| cari_id | BIGINT | ✓ | FK: musteri.cariler |
| kaplama_turu_id | BIGINT | ✓ | FK: tanim.kaplama_turleri |
| oem_standart_id | BIGINT | | FK: tanim.oem_standartlari |
| spesifikasyon_kodu | NVARCHAR(50) | | |
| min_kalinlik_um | DECIMAL(8,2) | | Minimum kaplama kalınlığı (µm) |
| max_kalinlik_um | DECIMAL(8,2) | | Maximum kaplama kalınlığı (µm) |
| hedef_kalinlik_um | DECIMAL(8,2) | | Hedef kalınlık |
| tuz_testi_saat | INT | | Minimum tuz sisi süresi |
| ek_gereksinimler | NVARCHAR(MAX) | | |
| dokuman_yolu | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

# ŞEMA: stok (Stok Yönetimi)

## stok.urunler
Parça/ürün ana tanım tablosu

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| urun_kodu | NVARCHAR(50) | ✓ | Unique |
| urun_adi | NVARCHAR(250) | ✓ | |
| cari_id | BIGINT | | FK: Sahip müşteri |
| musteri_parca_no | NVARCHAR(100) | | Müşteri parça numarası |
| urun_tipi | NVARCHAR(20) | ✓ | PARCA, HAMMADDE, KIMYASAL, YEDEK_PARCA |
| birim_id | BIGINT | ✓ | FK: tanim.birimler |
| kaplama_turu_id | BIGINT | | FK: (parçalar için) |
| yuzey_alani_m2 | DECIMAL(12,6) | | Hesaplanan/ölçülen yüzey alanı |
| agirlik_kg | DECIMAL(12,6) | | Birim ağırlık |
| teknik_resim_no | NVARCHAR(50) | | |
| stl_dosya_yolu | NVARCHAR(500) | | 3D model |
| resim_yolu | NVARCHAR(500) | | |
| min_stok | DECIMAL(18,4) | | Minimum stok seviyesi |
| max_stok | DECIMAL(18,4) | | Maximum stok seviyesi |
| kritik_stok | DECIMAL(18,4) | | Kritik stok seviyesi |
| raf_omru_gun | INT | | Kimyasallar için |
| notlar | NVARCHAR(MAX) | | |
| aktif_mi | BIT | ✓ | |

---

## stok.urun_spesifikasyonlar
Ürün bazlı kaplama gereksinimleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| urun_id | BIGINT | ✓ | FK: stok.urunler |
| kaplama_turu_id | BIGINT | ✓ | FK |
| oem_standart_id | BIGINT | | FK |
| min_kalinlik_um | DECIMAL(8,2) | | |
| max_kalinlik_um | DECIMAL(8,2) | | |
| hedef_kalinlik_um | DECIMAL(8,2) | | |
| tuz_testi_saat | INT | | |
| ozel_talimatlar | NVARCHAR(MAX) | | |
| aktif_mi | BIT | ✓ | |

---

## stok.depolar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | |
| ad | NVARCHAR(100) | ✓ | |
| depo_tipi | NVARCHAR(30) | ✓ | HAMMADDE, EMANET, MAMUL, KIMYASAL |
| lokasyon | NVARCHAR(200) | | |
| sorumlu_id | BIGINT | | FK: ik.personeller |
| aktif_mi | BIT | ✓ | |

---

## stok.depo_lokasyonlar
Depo içi raf/lokasyon tanımları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| depo_id | BIGINT | ✓ | FK: stok.depolar |
| lokasyon_kodu | NVARCHAR(30) | ✓ | A-01-02 (Koridor-Raf-Kat) |
| aciklama | NVARCHAR(100) | | |
| kapasite | DECIMAL(10,2) | | |
| birim_id | BIGINT | | FK |
| aktif_mi | BIT | ✓ | |

---

## stok.stok_hareketleri
Tüm stok giriş/çıkış hareketleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| hareket_tipi | NVARCHAR(30) | ✓ | GIRIS, CIKIS, TRANSFER, SAYIM, FIRE |
| hareket_nedeni | NVARCHAR(30) | ✓ | IRSALIYE, URETIM, SEVKIYAT, SAYIM_FARKI |
| tarih | DATETIME2 | ✓ | |
| urun_id | BIGINT | ✓ | FK: stok.urunler |
| depo_id | BIGINT | ✓ | FK: stok.depolar |
| lokasyon_id | BIGINT | | FK: stok.depo_lokasyonlar |
| miktar | DECIMAL(18,4) | ✓ | +/- değer |
| birim_id | BIGINT | ✓ | FK |
| lot_no | NVARCHAR(50) | | Parti numarası |
| referans_tip | NVARCHAR(30) | | IRSALIYE, IS_EMRI, SEVKIYAT |
| referans_id | BIGINT | | İlgili kayıt ID |
| aciklama | NVARCHAR(500) | | |

---

## stok.stok_bakiye
Güncel stok bakiyeleri (Materialized view gibi)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| urun_id | BIGINT | ✓ | FK |
| depo_id | BIGINT | ✓ | FK |
| lokasyon_id | BIGINT | | FK |
| lot_no | NVARCHAR(50) | | |
| miktar | DECIMAL(18,4) | ✓ | |
| rezerve_miktar | DECIMAL(18,4) | | İş emrine ayrılan |
| kullanilabilir_miktar | DECIMAL(18,4) | | miktar - rezerve |
| son_hareket_tarihi | DATETIME2 | | |

---

## stok.emanet_stok
Müşteri emanet stok takibi

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| cari_id | BIGINT | ✓ | FK: musteri.cariler |
| urun_id | BIGINT | ✓ | FK: stok.urunler |
| giris_irsaliye_id | BIGINT | ✓ | FK: siparis.giris_irsaliyeleri |
| lot_no | NVARCHAR(50) | | |
| giren_miktar | DECIMAL(18,4) | ✓ | |
| kalan_miktar | DECIMAL(18,4) | ✓ | |
| giris_tarihi | DATETIME2 | ✓ | |
| durum | NVARCHAR(20) | ✓ | BEKLIYOR, URETIMDE, TAMAMLANDI |

---

## stok.kimyasallar
Kimyasal stok detay bilgileri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| urun_id | BIGINT | ✓ | FK: stok.urunler |
| kategori_id | BIGINT | ✓ | FK: tanim.kimyasal_kategoriler |
| tedarikci_id | BIGINT | | FK: musteri.cariler |
| uretici | NVARCHAR(100) | | |
| tehlike_sinifi | NVARCHAR(50) | | |
| sds_dokuman_yolu | NVARCHAR(500) | | Güvenlik Bilgi Formu |
| depolama_sicaklik_min | DECIMAL(5,2) | | |
| depolama_sicaklik_max | DECIMAL(5,2) | | |
| yogunluk | DECIMAL(8,4) | | g/ml |
| aktif_mi | BIT | ✓ | |

---

# ŞEMA: siparis (Sipariş Yönetimi)

## siparis.giris_irsaliyeleri
Gelen parça irsaliyeleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| irsaliye_no | NVARCHAR(30) | ✓ | Unique |
| cari_id | BIGINT | ✓ | FK: musteri.cariler |
| cari_irsaliye_no | NVARCHAR(50) | | Müşteri irsaliye no |
| tarih | DATE | ✓ | |
| teslim_alan_id | BIGINT | | FK: ik.personeller |
| arac_plaka | NVARCHAR(15) | | |
| sofor_adi | NVARCHAR(100) | | |
| durum | NVARCHAR(20) | ✓ | TASLAK, ONAYLANDI, IPTAL |
| notlar | NVARCHAR(MAX) | | |

---

## siparis.giris_irsaliye_satirlar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| irsaliye_id | BIGINT | ✓ | FK: siparis.giris_irsaliyeleri |
| satir_no | INT | ✓ | |
| urun_id | BIGINT | ✓ | FK: stok.urunler |
| miktar | DECIMAL(18,4) | ✓ | |
| birim_id | BIGINT | ✓ | FK |
| lot_no | NVARCHAR(50) | | |
| kaplama_turu_id | BIGINT | | FK: İstenen kaplama |
| termin_tarihi | DATE | | |
| giris_kalite_durumu | NVARCHAR(20) | | BEKLIYOR, KABUL, RED |
| notlar | NVARCHAR(500) | | |

---

## siparis.is_emirleri
Üretim iş emirleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| is_emri_no | NVARCHAR(30) | ✓ | Unique (IE-2024-00001) |
| tarih | DATE | ✓ | |
| cari_id | BIGINT | ✓ | FK |
| giris_irsaliye_satir_id | BIGINT | | FK: Kaynak irsaliye satır |
| urun_id | BIGINT | ✓ | FK |
| hat_id | BIGINT | | FK: tanim.uretim_hatlari |
| kaplama_turu_id | BIGINT | ✓ | FK |
| planlanan_miktar | DECIMAL(18,4) | ✓ | |
| birim_id | BIGINT | ✓ | FK |
| lot_no | NVARCHAR(50) | | Üretim lot no |
| oncelik | INT | | 1: En yüksek |
| planlanan_baslama | DATETIME2 | | |
| planlanan_bitis | DATETIME2 | | |
| fiili_baslama | DATETIME2 | | |
| fiili_bitis | DATETIME2 | | |
| uretilen_miktar | DECIMAL(18,4) | | |
| fire_miktar | DECIMAL(18,4) | | |
| durum | NVARCHAR(20) | ✓ | TASLAK, PLANLI, URETIMDE, KALITE, TAMAMLANDI, IPTAL |
| spesifikasyon_id | BIGINT | | FK: stok.urun_spesifikasyonlar |
| ozel_talimatlar | NVARCHAR(MAX) | | |

---

## siparis.is_emri_operasyonlar
İş emri operasyon/rota adımları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| is_emri_id | BIGINT | ✓ | FK |
| sira_no | INT | ✓ | |
| operasyon_adi | NVARCHAR(100) | ✓ | Yağ Alma, Fosfat, Kaplama |
| hat_id | BIGINT | | FK |
| planlanan_sure_dk | INT | | |
| fiili_sure_dk | INT | | |
| durum | NVARCHAR(20) | | BEKLIYOR, DEVAM, TAMAMLANDI |
| baslama_zamani | DATETIME2 | | |
| bitis_zamani | DATETIME2 | | |
| operator_id | BIGINT | | FK: ik.personeller |

---

## siparis.cikis_irsaliyeleri
Sevkiyat irsaliyeleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| irsaliye_no | NVARCHAR(30) | ✓ | Unique |
| cari_id | BIGINT | ✓ | FK |
| teslimat_adresi_id | BIGINT | | FK: musteri.cari_adresler |
| tarih | DATE | ✓ | |
| sevk_tarihi | DATETIME2 | | |
| teslim_eden_id | BIGINT | | FK: ik.personeller |
| tasiyici_firma | NVARCHAR(100) | | |
| arac_plaka | NVARCHAR(15) | | |
| sofor_adi | NVARCHAR(100) | | |
| durum | NVARCHAR(20) | ✓ | TASLAK, HAZIRLANIYOR, SEVKEDILDI, TESLIM_EDILDI, IPTAL |
| fatura_id | BIGINT | | FK: siparis.faturalar |
| notlar | NVARCHAR(MAX) | | |

---

## siparis.cikis_irsaliye_satirlar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| irsaliye_id | BIGINT | ✓ | FK |
| satir_no | INT | ✓ | |
| is_emri_id | BIGINT | ✓ | FK: siparis.is_emirleri |
| urun_id | BIGINT | ✓ | FK |
| miktar | DECIMAL(18,4) | ✓ | |
| birim_id | BIGINT | ✓ | FK |
| lot_no | NVARCHAR(50) | | |
| ambalaj_turu_id | BIGINT | | FK |
| koli_adedi | INT | | |

---

## siparis.faturalar
Satış faturaları (Zirve'ye aktarılacak)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| fatura_no | NVARCHAR(30) | ✓ | |
| fatura_tipi | NVARCHAR(20) | ✓ | SATIS, IADE |
| cari_id | BIGINT | ✓ | FK |
| tarih | DATE | ✓ | |
| vade_tarihi | DATE | | |
| para_birimi_id | BIGINT | ✓ | FK |
| kur | DECIMAL(18,6) | | |
| ara_toplam | DECIMAL(18,2) | | |
| kdv_toplam | DECIMAL(18,2) | | |
| genel_toplam | DECIMAL(18,2) | | |
| durum | NVARCHAR(20) | ✓ | TASLAK, ONAYLANDI, ZIRVE_AKTARILDI, IPTAL |
| zirve_fatura_id | NVARCHAR(50) | | Zirve entegrasyon ID |
| notlar | NVARCHAR(MAX) | | |

---

## siparis.fatura_satirlar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| fatura_id | BIGINT | ✓ | FK |
| satir_no | INT | ✓ | |
| cikis_irsaliye_satir_id | BIGINT | | FK |
| urun_id | BIGINT | ✓ | FK |
| aciklama | NVARCHAR(500) | | |
| miktar | DECIMAL(18,4) | ✓ | |
| birim_id | BIGINT | ✓ | FK |
| birim_fiyat | DECIMAL(18,6) | ✓ | |
| tutar | DECIMAL(18,2) | | |
| kdv_orani | DECIMAL(5,2) | | |
| kdv_tutari | DECIMAL(18,2) | | |
| toplam | DECIMAL(18,2) | | |

---

# ŞEMA: uretim (Üretim Yönetimi)

## uretim.uretim_kayitlari
Gerçekleşen üretim kayıtları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| is_emri_id | BIGINT | ✓ | FK |
| hat_id | BIGINT | ✓ | FK |
| vardiya_id | BIGINT | ✓ | FK |
| tarih | DATE | ✓ | |
| baslama_zamani | DATETIME2 | ✓ | |
| bitis_zamani | DATETIME2 | | |
| operator_id | BIGINT | ✓ | FK: ik.personeller |
| uretilen_miktar | DECIMAL(18,4) | | |
| fire_miktar | DECIMAL(18,4) | | |
| aski_sayisi | INT | | |
| durum | NVARCHAR(20) | | DEVAM, TAMAMLANDI, DURDURULDU |

---

## uretim.durus_kayitlari
Üretim duruş kayıtları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| uretim_kayit_id | BIGINT | | FK |
| hat_id | BIGINT | ✓ | FK |
| durus_nedeni_id | BIGINT | ✓ | FK: tanim.durus_nedenleri |
| baslama_zamani | DATETIME2 | ✓ | |
| bitis_zamani | DATETIME2 | | |
| sure_dk | INT | | Hesaplanan süre |
| aciklama | NVARCHAR(500) | | |
| bakim_kayit_id | BIGINT | | FK: bakim.bakim_kayitlari (arıza ise) |

---

## uretim.banyo_tanimlari
Banyo ana tanımları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | BNY-01 |
| ad | NVARCHAR(100) | ✓ | Kataforez Banyosu 1 |
| hat_id | BIGINT | ✓ | FK |
| banyo_tipi | NVARCHAR(50) | ✓ | YAG_ALMA, FOSFAT, KAPLAMA, DURULAMA |
| hacim_lt | DECIMAL(10,2) | | |
| sicaklik_min | DECIMAL(5,2) | | |
| sicaklik_max | DECIMAL(5,2) | | |
| sicaklik_hedef | DECIMAL(5,2) | | |
| ph_min | DECIMAL(4,2) | | |
| ph_max | DECIMAL(4,2) | | |
| ph_hedef | DECIMAL(4,2) | | |
| aktif_mi | BIT | ✓ | |

---

## uretim.banyo_parametre_tanimlari
Banyo izlenecek parametre tanımları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| banyo_id | BIGINT | ✓ | FK |
| parametre_adi | NVARCHAR(50) | ✓ | Sıcaklık, pH, İletkenlik |
| birim | NVARCHAR(20) | | °C, pH, mS/cm |
| min_deger | DECIMAL(18,4) | | |
| max_deger | DECIMAL(18,4) | | |
| hedef_deger | DECIMAL(18,4) | | |
| plc_tag_adresi | NVARCHAR(100) | | S7 tag adresi |
| alarm_aktif_mi | BIT | | |
| aktif_mi | BIT | ✓ | |

---

## uretim.banyo_parametre_log
PLC'den okunan anlık değerler (yüksek hacimli)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| banyo_id | BIGINT | ✓ | FK |
| parametre_id | BIGINT | ✓ | FK |
| deger | DECIMAL(18,4) | ✓ | |
| zaman_damgasi | DATETIME2 | ✓ | |
| alarm_durumu | NVARCHAR(20) | | NORMAL, UYARI, ALARM |

> **Not:** Bu tablo partitioning ve data retention policy ile yönetilmeli.

---

## uretim.banyo_analiz_sonuclari
Manuel banyo analiz sonuçları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| banyo_id | BIGINT | ✓ | FK |
| tarih | DATETIME2 | ✓ | |
| analist_id | BIGINT | ✓ | FK: ik.personeller |
| sicaklik | DECIMAL(5,2) | | |
| ph | DECIMAL(4,2) | | |
| iletkenlik | DECIMAL(10,2) | | |
| toplam_asitlik | DECIMAL(10,4) | | |
| serbest_asitlik | DECIMAL(10,4) | | |
| demir_ppm | DECIMAL(10,4) | | |
| cinko_ppm | DECIMAL(10,4) | | |
| ek_parametreler | NVARCHAR(MAX) | | JSON format |
| notlar | NVARCHAR(500) | | |

---

## uretim.banyo_takviyeler
Banyo kimyasal takviyeleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| banyo_id | BIGINT | ✓ | FK |
| tarih | DATETIME2 | ✓ | |
| kimyasal_id | BIGINT | ✓ | FK: stok.urunler |
| miktar | DECIMAL(10,4) | ✓ | |
| birim_id | BIGINT | ✓ | FK |
| takviye_nedeni | NVARCHAR(100) | | |
| yapan_id | BIGINT | ✓ | FK: ik.personeller |
| notlar | NVARCHAR(500) | | |

---

## uretim.aski_jigler
Askı/Jig tanımları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(30) | ✓ | |
| ad | NVARCHAR(100) | ✓ | |
| hat_id | BIGINT | | FK |
| tipi | NVARCHAR(50) | | Universal, Özel |
| kapasite | INT | | Max parça sayısı |
| max_agirlik_kg | DECIMAL(10,2) | | |
| durum | NVARCHAR(20) | | AKTIF, BAKIMDA, HURDA |
| son_bakim_tarihi | DATE | | |
| toplam_kullanim_sayisi | INT | | |
| notlar | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

# ŞEMA: kalite (Kalite Yönetimi)

## kalite.kontrol_planlari
Ürün bazlı kontrol planları (16949)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| plan_no | NVARCHAR(30) | ✓ | |
| revizyon | INT | | |
| urun_id | BIGINT | | FK (NULL ise genel plan) |
| kaplama_turu_id | BIGINT | | FK |
| cari_id | BIGINT | | FK (müşteri özel plan) |
| gecerlilik_baslangic | DATE | ✓ | |
| gecerlilik_bitis | DATE | | |
| hazirlayan_id | BIGINT | | FK |
| onaylayan_id | BIGINT | | FK |
| durum | NVARCHAR(20) | ✓ | TASLAK, AKTIF, PASIF |
| notlar | NVARCHAR(MAX) | | |

---

## kalite.kontrol_plan_satirlar
Kontrol planı kontrol noktaları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| plan_id | BIGINT | ✓ | FK |
| sira_no | INT | ✓ | |
| operasyon | NVARCHAR(100) | ✓ | Hangi aşamada |
| kontrol_ozelligi | NVARCHAR(200) | ✓ | Ne kontrol edilecek |
| spesifikasyon | NVARCHAR(200) | | Kabul kriteri |
| min_deger | DECIMAL(18,4) | | |
| max_deger | DECIMAL(18,4) | | |
| olcum_metodu | NVARCHAR(100) | | Nasıl ölçülecek |
| olcum_cihazi | NVARCHAR(100) | | Hangi cihazla |
| numune_boyutu | NVARCHAR(50) | | 5 adet, %10, vb. |
| frekans | NVARCHAR(50) | | Her parti, saatlik |
| reaksiyon_plani | NVARCHAR(500) | | Uygunsuzlukta ne yapılır |
| kayit_formu | NVARCHAR(100) | | Hangi forma kaydedilir |
| kritik_mi | BIT | | Kritik karakteristik |
| spc_uygulanacak_mi | BIT | | SPC takibi var mı |

---

## kalite.muayeneler
Kalite kontrol kayıtları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| muayene_no | NVARCHAR(30) | ✓ | |
| muayene_tipi | NVARCHAR(30) | ✓ | GIRIS, PROSES, FINAL |
| tarih | DATETIME2 | ✓ | |
| is_emri_id | BIGINT | | FK |
| urun_id | BIGINT | ✓ | FK |
| lot_no | NVARCHAR(50) | | |
| kontrol_plani_id | BIGINT | | FK |
| muayeneci_id | BIGINT | ✓ | FK: ik.personeller |
| numune_miktari | DECIMAL(10,2) | | |
| kontrol_miktari | DECIMAL(10,2) | | |
| kabul_miktari | DECIMAL(10,2) | | |
| red_miktari | DECIMAL(10,2) | | |
| sonuc | NVARCHAR(20) | ✓ | KABUL, RED, SARTLI_KABUL |
| notlar | NVARCHAR(MAX) | | |

---

## kalite.muayene_detaylar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| muayene_id | BIGINT | ✓ | FK |
| kontrol_plan_satir_id | BIGINT | | FK |
| kontrol_ozelligi | NVARCHAR(200) | ✓ | |
| olcum_degeri | DECIMAL(18,4) | | |
| olcum_degeri_metin | NVARCHAR(200) | | Sayısal olmayan sonuçlar |
| min_deger | DECIMAL(18,4) | | |
| max_deger | DECIMAL(18,4) | | |
| sonuc | NVARCHAR(20) | ✓ | UYGUN, UYGUNSUZ |
| hata_turu_id | BIGINT | | FK: tanim.hata_turleri |
| notlar | NVARCHAR(500) | | |

---

## kalite.spc_olcumler
SPC kontrol grafiği ölçümleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| tarih | DATETIME2 | ✓ | |
| hat_id | BIGINT | ✓ | FK |
| parametre_adi | NVARCHAR(100) | ✓ | Kaplama Kalınlığı |
| urun_id | BIGINT | | FK |
| is_emri_id | BIGINT | | FK |
| olcum_1 | DECIMAL(18,4) | | |
| olcum_2 | DECIMAL(18,4) | | |
| olcum_3 | DECIMAL(18,4) | | |
| olcum_4 | DECIMAL(18,4) | | |
| olcum_5 | DECIMAL(18,4) | | |
| ortalama | DECIMAL(18,4) | | X-bar |
| aralik | DECIMAL(18,4) | | R değeri |
| ust_kontrol_limiti | DECIMAL(18,4) | | UCL |
| alt_kontrol_limiti | DECIMAL(18,4) | | LCL |
| kural_ihlali | NVARCHAR(100) | | Western Electric kuralları |
| opertor_id | BIGINT | | FK |

---

## kalite.test_talepleri
Laboratuvar test talepleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| talep_no | NVARCHAR(30) | ✓ | |
| tarih | DATETIME2 | ✓ | |
| talep_eden_id | BIGINT | ✓ | FK: ik.personeller |
| is_emri_id | BIGINT | | FK |
| muayene_id | BIGINT | | FK |
| urun_id | BIGINT | ✓ | FK |
| lot_no | NVARCHAR(50) | | |
| numune_sayisi | INT | | |
| oncelik | NVARCHAR(20) | | NORMAL, ACIL |
| talep_nedeni | NVARCHAR(100) | | Rutin, Şikayet, PPAP |
| durum | NVARCHAR(20) | ✓ | BEKLIYOR, DEVAM, TAMAMLANDI |
| notlar | NVARCHAR(500) | | |

---

## kalite.test_talep_testler
Talep edilen testler

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| talep_id | BIGINT | ✓ | FK |
| test_turu_id | BIGINT | ✓ | FK: tanim.test_turleri |
| ozel_spesifikasyon | NVARCHAR(200) | | Özel gereksinim |
| min_deger | DECIMAL(18,4) | | |
| max_deger | DECIMAL(18,4) | | |

---

## kalite.test_sonuclari
Laboratuvar test sonuçları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| talep_test_id | BIGINT | ✓ | FK: kalite.test_talep_testler |
| tarih | DATETIME2 | ✓ | |
| analist_id | BIGINT | ✓ | FK: ik.personeller |
| cihaz_id | BIGINT | | FK: kalite.olcum_cihazlari |
| olcum_degeri | DECIMAL(18,4) | | |
| olcum_birimi | NVARCHAR(20) | | |
| sonuc | NVARCHAR(20) | ✓ | UYGUN, UYGUNSUZ |
| sertifika_no | NVARCHAR(50) | | |
| rapor_yolu | NVARCHAR(500) | | |
| notlar | NVARCHAR(MAX) | | |

---

## kalite.olcum_cihazlari

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| cihaz_kodu | NVARCHAR(30) | ✓ | |
| cihaz_adi | NVARCHAR(100) | ✓ | |
| marka | NVARCHAR(50) | | |
| model | NVARCHAR(50) | | |
| seri_no | NVARCHAR(50) | | |
| olcum_araligi | NVARCHAR(100) | | 0-25mm |
| cozunurluk | NVARCHAR(50) | | 0.001mm |
| lokasyon | NVARCHAR(100) | | Laboratuvar, Hat-1 |
| sorumlu_id | BIGINT | | FK: ik.personeller |
| durum | NVARCHAR(20) | | AKTIF, KALIBRASYONDA, ARIZALI |
| aktif_mi | BIT | ✓ | |

---

## kalite.kalibrasyon_planlari

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| cihaz_id | BIGINT | ✓ | FK |
| kalibrasyon_periyodu_ay | INT | ✓ | |
| son_kalibrasyon_tarihi | DATE | | |
| sonraki_kalibrasyon_tarihi | DATE | ✓ | |
| kalibrasyon_firma | NVARCHAR(100) | | İç/Dış |
| notlar | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

## kalite.kalibrasyon_kayitlari

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| cihaz_id | BIGINT | ✓ | FK |
| kalibrasyon_tarihi | DATE | ✓ | |
| gecerlilik_tarihi | DATE | ✓ | |
| yapan_firma | NVARCHAR(100) | ✓ | |
| sertifika_no | NVARCHAR(50) | | |
| sertifika_yolu | NVARCHAR(500) | | |
| sonuc | NVARCHAR(20) | ✓ | UYGUN, UYGUNSUZ |
| maliyet | DECIMAL(18,2) | | |
| notlar | NVARCHAR(500) | | |

---

## kalite.uygunsuzluklar
Uygunsuzluk kayıtları (8D dahil)

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kayit_no | NVARCHAR(30) | ✓ | UYG-2024-0001 |
| kayit_tipi | NVARCHAR(30) | ✓ | DAHILI, MUSTERI_SIKAYETI, TEDARIKCI |
| kayit_tarihi | DATE | ✓ | |
| bildiren_id | BIGINT | ✓ | FK |
| cari_id | BIGINT | | FK (müşteri şikayeti ise) |
| urun_id | BIGINT | | FK |
| is_emri_id | BIGINT | | FK |
| lot_no | NVARCHAR(50) | | |
| etkilenen_miktar | DECIMAL(18,4) | | |
| hata_turu_id | BIGINT | | FK |
| hata_tanimi | NVARCHAR(MAX) | ✓ | |
| tespit_yeri | NVARCHAR(100) | | |
| oncelik | NVARCHAR(20) | | DUSUK, ORTA, YUKSEK, KRITIK |
| durum | NVARCHAR(30) | ✓ | ACIK, ANALIZ, AKSIYON, DOGRULAMA, KAPALI |
| sorumlu_id | BIGINT | | FK |
| hedef_kapanis_tarihi | DATE | | |
| kapanis_tarihi | DATE | | |
| maliyet | DECIMAL(18,2) | | Kalitesizlik maliyeti |

---

## kalite.uygunsuzluk_aksiyonlar
8D aksiyonları

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| uygunsuzluk_id | BIGINT | ✓ | FK |
| aksiyon_tipi | NVARCHAR(30) | ✓ | ACIL, DUZELTICI, ONLEYICI |
| d_adimi | INT | | 8D adımı (D1-D8) |
| aciklama | NVARCHAR(MAX) | ✓ | |
| sorumlu_id | BIGINT | ✓ | FK |
| hedef_tarih | DATE | | |
| tamamlanma_tarihi | DATE | | |
| durum | NVARCHAR(20) | ✓ | BEKLIYOR, DEVAM, TAMAMLANDI |
| dogrulama_tarihi | DATE | | |
| dogrulayan_id | BIGINT | | FK |
| etkinlik_degerlendirme | NVARCHAR(500) | | |

---

# ŞEMA: bakim (Bakım Yönetimi)

## bakim.ekipmanlar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| ekipman_kodu | NVARCHAR(30) | ✓ | |
| ekipman_adi | NVARCHAR(100) | ✓ | |
| hat_id | BIGINT | | FK |
| lokasyon | NVARCHAR(100) | | |
| kategori | NVARCHAR(50) | | Pompa, Motor, Konveyör |
| marka | NVARCHAR(50) | | |
| model | NVARCHAR(50) | | |
| seri_no | NVARCHAR(50) | | |
| kurulum_tarihi | DATE | | |
| garanti_bitis | DATE | | |
| kritiklik | NVARCHAR(20) | | A, B, C |
| durum | NVARCHAR(20) | | CALISIR, ARIZALI, BAKIMDA |
| teknik_ozellikler | NVARCHAR(MAX) | | JSON |
| dokuman_yolu | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

## bakim.periyodik_bakim_planlari

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| ekipman_id | BIGINT | ✓ | FK |
| bakim_adi | NVARCHAR(100) | ✓ | |
| periyot_gun | INT | | Her X günde bir |
| periyot_calisma_saati | INT | | Her X saatte bir |
| son_bakim_tarihi | DATE | | |
| sonraki_bakim_tarihi | DATE | ✓ | |
| tahmini_sure_dk | INT | | |
| talimat | NVARCHAR(MAX) | | |
| sorumlu_id | BIGINT | | FK |
| aktif_mi | BIT | ✓ | |

---

## bakim.bakim_kayitlari

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kayit_no | NVARCHAR(30) | ✓ | |
| ekipman_id | BIGINT | ✓ | FK |
| bakim_tipi | NVARCHAR(30) | ✓ | PERIYODIK, ARIZA, KESTIRIMCI |
| plan_id | BIGINT | | FK: bakim.periyodik_bakim_planlari |
| ariza_bildirimi_id | BIGINT | | FK |
| baslama_zamani | DATETIME2 | ✓ | |
| bitis_zamani | DATETIME2 | | |
| sure_dk | INT | | |
| yapilan_islemler | NVARCHAR(MAX) | | |
| sonuc | NVARCHAR(20) | | TAMAMLANDI, BEKLIYOR |
| teknisyen_id | BIGINT | ✓ | FK: ik.personeller |
| maliyet | DECIMAL(18,2) | | |

---

## bakim.ariza_bildirimleri

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| bildirim_no | NVARCHAR(30) | ✓ | |
| ekipman_id | BIGINT | ✓ | FK |
| bildirim_zamani | DATETIME2 | ✓ | |
| bildiren_id | BIGINT | ✓ | FK |
| ariza_tanimi | NVARCHAR(500) | ✓ | |
| oncelik | NVARCHAR(20) | ✓ | DUSUK, ORTA, YUKSEK, ACIL |
| durum | NVARCHAR(20) | ✓ | ACIK, ATANDI, DEVAM, KAPALI |
| atanan_id | BIGINT | | FK: ik.personeller |
| cozum_zamani | DATETIME2 | | |

---

## bakim.yedek_parcalar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| urun_id | BIGINT | ✓ | FK: stok.urunler |
| ekipman_id | BIGINT | | FK |
| kritik_mi | BIT | | |
| min_stok | DECIMAL(10,2) | | |
| tedarik_suresi_gun | INT | | |

---

## bakim.bakim_yedek_parca_kullanim

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| bakim_kayit_id | BIGINT | ✓ | FK |
| urun_id | BIGINT | ✓ | FK |
| miktar | DECIMAL(10,4) | ✓ | |
| birim_fiyat | DECIMAL(18,4) | | |

---

# ŞEMA: ik (İnsan Kaynakları)

## ik.departmanlar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | |
| ad | NVARCHAR(100) | ✓ | |
| ust_departman_id | BIGINT | | FK (hiyerarşi) |
| yonetici_id | BIGINT | | FK: ik.personeller |
| aktif_mi | BIT | ✓ | |

---

## ik.pozisyonlar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | |
| ad | NVARCHAR(100) | ✓ | |
| departman_id | BIGINT | ✓ | FK |
| aktif_mi | BIT | ✓ | |

---

## ik.personeller

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| sicil_no | NVARCHAR(20) | ✓ | |
| ad | NVARCHAR(50) | ✓ | |
| soyad | NVARCHAR(50) | ✓ | |
| tc_kimlik_no | NVARCHAR(11) | | |
| dogum_tarihi | DATE | | |
| cinsiyet | NVARCHAR(10) | | |
| telefon | NVARCHAR(20) | | |
| email | NVARCHAR(100) | | |
| adres | NVARCHAR(500) | | |
| departman_id | BIGINT | ✓ | FK |
| pozisyon_id | BIGINT | ✓ | FK |
| yonetici_id | BIGINT | | FK (üst yönetici) |
| ise_giris_tarihi | DATE | ✓ | |
| isten_cikis_tarihi | DATE | | |
| calisma_durumu | NVARCHAR(20) | ✓ | AKTIF, PASIF, IZINLI |
| fotograf_yolu | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

## ik.yetkinlikler

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(20) | ✓ | |
| ad | NVARCHAR(100) | ✓ | Hat-1 Operatörlüğü |
| kategori | NVARCHAR(50) | | Teknik, Kalite, Güvenlik |
| aciklama | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

## ik.personel_yetkinlikler

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| personel_id | BIGINT | ✓ | FK |
| yetkinlik_id | BIGINT | ✓ | FK |
| seviye | INT | | 1-5 |
| kazanim_tarihi | DATE | | |
| gecerlilik_tarihi | DATE | | Yenileme gerekiyorsa |
| belge_yolu | NVARCHAR(500) | | |

---

## ik.egitimler

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| egitim_kodu | NVARCHAR(30) | ✓ | |
| egitim_adi | NVARCHAR(200) | ✓ | |
| kategori | NVARCHAR(50) | | OHS, Kalite, Teknik |
| sure_saat | DECIMAL(5,2) | | |
| periyot_ay | INT | | Tekrar periyodu |
| zorunlu_mu | BIT | | |
| aciklama | NVARCHAR(MAX) | | |
| aktif_mi | BIT | ✓ | |

---

## ik.egitim_kayitlari

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| egitim_id | BIGINT | ✓ | FK |
| personel_id | BIGINT | ✓ | FK |
| egitim_tarihi | DATE | ✓ | |
| egitmen | NVARCHAR(100) | | |
| sure_saat | DECIMAL(5,2) | | |
| sonuc | NVARCHAR(20) | | BASARILI, BASARISIZ |
| puan | DECIMAL(5,2) | | |
| sonraki_egitim_tarihi | DATE | | |
| belge_yolu | NVARCHAR(500) | | |
| notlar | NVARCHAR(500) | | |

---

# ŞEMA: sistem (Sistem Yönetimi)

## sistem.kullanicilar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kullanici_adi | NVARCHAR(50) | ✓ | Unique |
| email | NVARCHAR(100) | ✓ | Unique |
| sifre_hash | NVARCHAR(256) | ✓ | Bcrypt hash |
| personel_id | BIGINT | | FK: ik.personeller |
| son_giris_tarihi | DATETIME2 | | |
| son_giris_ip | NVARCHAR(50) | | |
| basarisiz_giris_sayisi | INT | | |
| hesap_kilitli_mi | BIT | | |
| kilit_bitis_zamani | DATETIME2 | | |
| sifre_degisim_tarihi | DATETIME2 | | |
| sifre_degisim_gerekli | BIT | | |
| aktif_mi | BIT | ✓ | |

---

## sistem.roller

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(30) | ✓ | ADMIN, URETIM_MD, OPERATOR |
| ad | NVARCHAR(100) | ✓ | |
| aciklama | NVARCHAR(500) | | |
| aktif_mi | BIT | ✓ | |

---

## sistem.kullanici_roller

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kullanici_id | BIGINT | ✓ | FK |
| rol_id | BIGINT | ✓ | FK |

---

## sistem.izinler

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kod | NVARCHAR(50) | ✓ | is_emri.olustur, rapor.goruntule |
| modul | NVARCHAR(50) | ✓ | |
| aciklama | NVARCHAR(200) | | |

---

## sistem.rol_izinler

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| rol_id | BIGINT | ✓ | FK |
| izin_id | BIGINT | ✓ | FK |

---

## sistem.oturum_kayitlari

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kullanici_id | BIGINT | ✓ | FK |
| token | NVARCHAR(500) | ✓ | JWT token |
| olusturma_zamani | DATETIME2 | ✓ | |
| son_aktivite_zamani | DATETIME2 | | |
| gecerlilik_zamani | DATETIME2 | ✓ | |
| ip_adresi | NVARCHAR(50) | | |
| cihaz_bilgisi | NVARCHAR(500) | | User-Agent |
| aktif_mi | BIT | ✓ | |

---

## sistem.ayarlar

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| kategori | NVARCHAR(50) | ✓ | GENEL, URETIM, KALITE |
| anahtar | NVARCHAR(100) | ✓ | |
| deger | NVARCHAR(MAX) | | |
| veri_tipi | NVARCHAR(20) | | STRING, INT, BOOL, JSON |
| aciklama | NVARCHAR(500) | | |

---

# ŞEMA: entegrasyon (Dış Sistem Entegrasyonları)

## entegrasyon.zirve_senkron_log

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| islem_tipi | NVARCHAR(30) | ✓ | CARI_CEKME, FATURA_GONDERME |
| islem_zamani | DATETIME2 | ✓ | |
| basarili_mi | BIT | ✓ | |
| kayit_sayisi | INT | | |
| hata_mesaji | NVARCHAR(MAX) | | |
| istek_verisi | NVARCHAR(MAX) | | JSON |
| yanit_verisi | NVARCHAR(MAX) | | JSON |

---

## entegrasyon.plc_baglanti_durumu

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| hat_id | BIGINT | ✓ | FK |
| son_baglanti_zamani | DATETIME2 | | |
| baglanti_durumu | NVARCHAR(20) | | BAGLI, BAGLANTI_YOK, HATA |
| hata_mesaji | NVARCHAR(500) | | |

---

# ŞEMA: log (Denetim İzleri)

## log.islem_log

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| zaman_damgasi | DATETIME2 | ✓ | |
| kullanici_id | BIGINT | | FK |
| kullanici_adi | NVARCHAR(50) | | |
| islem_tipi | NVARCHAR(20) | ✓ | INSERT, UPDATE, DELETE |
| tablo_adi | NVARCHAR(100) | ✓ | |
| kayit_id | BIGINT | ✓ | |
| eski_degerler | NVARCHAR(MAX) | | JSON |
| yeni_degerler | NVARCHAR(MAX) | | JSON |
| ip_adresi | NVARCHAR(50) | | |

---

## log.hata_log

| Kolon | Tip | Zorunlu | Açıklama |
|-------|-----|---------|----------|
| id | BIGINT | ✓ | PK |
| zaman_damgasi | DATETIME2 | ✓ | |
| seviye | NVARCHAR(20) | ✓ | DEBUG, INFO, WARNING, ERROR |
| kaynak | NVARCHAR(100) | | Modül/Servis adı |
| mesaj | NVARCHAR(MAX) | ✓ | |
| exception | NVARCHAR(MAX) | | Stack trace |
| kullanici_id | BIGINT | | |
| ek_bilgi | NVARCHAR(MAX) | | JSON |

---

# İNDEKS ÖNERİLERİ

Her tablo için önerilen indeksler:

1. **Primary Key:** Otomatik
2. **Foreign Keys:** Tüm FK kolonlarına
3. **Unique:** Kod, numara alanlarına
4. **Filtreleme:** Sık filtrelenen alanlara (tarih, durum)
5. **Arama:** Ad, unvan gibi metin aramalarına

Örnek:
```sql
-- siparis.is_emirleri için
CREATE INDEX IX_is_emirleri_tarih ON siparis.is_emirleri(tarih);
CREATE INDEX IX_is_emirleri_durum ON siparis.is_emirleri(durum);
CREATE INDEX IX_is_emirleri_cari ON siparis.is_emirleri(cari_id);
CREATE INDEX IX_is_emirleri_hat ON siparis.is_emirleri(hat_id);
```

---

# DATA RETENTION (Veri Saklama)

| Tablo | Saklama Süresi | Strateji |
|-------|---------------|----------|
| uretim.banyo_parametre_log | 2 yıl | Partitioning by month |
| log.islem_log | 5 yıl | Archive to cold storage |
| log.hata_log | 1 yıl | Auto-delete |
| Diğer tablolar | Süresiz | Soft delete |

---

# VERSİYON GEÇMİŞİ

| Versiyon | Tarih | Açıklama |
|----------|-------|----------|
| 1.0 | 2024 | İlk tasarım |
