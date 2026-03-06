# NEXOR ERP - Teklif Modulu Calisma Raporu
**Tarih:** 2026-02-16

---

## Oturum - Teklif Modulu Buyuk Guncelleme

### 1. Toplam/Fiyat Bolumleri Kaldirildi
- UI formdan Ara Toplam, Iskonto, KDV, Genel Toplam alanlari kaldirildi
- PDF ciktidan FIYAT OZETI bolumu tamamen kaldirildi
- Liste sayfasindan (teklif_liste.py) Toplam, KDV, G.Toplam sutunlari kaldirildi
- Stat card "Bu Ay Toplam" yerine "Bu Ay Teklif" (adet bazli) oldu
- Sadece birim fiyat veriliyor, toplam hesaplanmiyor

### 2. Dosya Ekleme Ozelligi
- **Kaplama Sartnamesi** dosya ekleme (PDF, DOC, gorsel vb.)
- **Parca Gorseli** dosya ekleme + 200x200 onizleme
- Dosyalar `~/.redline_nexor/teklif_dosyalar/{teklif_id}/` altina kopyalaniyor
- PDF'de parca gorseli ve kaplama sartnamesi gosteriliyor
- DB: `satislar.teklifler` tablosuna `kaplama_sartnamesi_dosya`, `parca_gorseli_dosya` sutunlari

### 3. PDF Ust Uste Binme Duzeltmeleri
- Firma adi uzunsa alt satira iniyor (wrap), kisaltma yok
- `_draw_field` fonksiyonu cok satirli metin destegi ile yeniden yazildi
- `_wrap_field_text` helper fonksiyonu eklendi
- Tablo-bolum arasi bosluk 4mm -> 12mm, musteri-tablo arasi 4mm -> 8mm

### 4. Tablo Okunabilirlik Duzeltmeleri
- Secim rengi kirmizi (#DC2626) -> koyu mavi (#2A3A5C)
- **Yazarken metin gorunmeme** sorunu duzeltildi (QLineEdit stili tabloya eklendi)
- Alternatif satir renkleri, ComboBox stili, 38px satir yuksekligi

### 5. Satir Bazli Gorsel Ekleme
- Tabloya "Gorsel" sutunu eklendi (son sutun)
- Her satirda gorsel butonu ile gorsel secme
- Secilince tik olarak degisiyor
- Gorseller `satir_X_gorsel.png` olarak kopyalaniyor
- PDF'de "PARCA GORSELLERI" bolumunde 3'lu grid halinde gosteriliyor
- DB: `satislar.teklif_satirlari` tablosuna `gorsel_dosya` sutunu

### 6. Dahili Bilgiler Bolumu (PDF'de Gorunmez)
- "Dahili Not" alani eklendi (serbest metin)
- DB: `satislar.teklifler` tablosuna `dahili_not` sutunu

### 7. Yillik Adet ve Ciro (Satir Bazli)
- **Y.Adet** sutunu tabloya eklendi (duzenlenebilir, her satir icin)
- **Y.Ciro** sutunu tabloya eklendi (otomatik hesaplaniyor: B.Fiyat x Y.Adet, read-only)
- Tablonun altinda **Toplam Yillik Ciro** etiketi gosteriliyor
- Bunlar **PDF'de gorunmuyor** (sadece dahili bilgi)
- DB: `satislar.teklif_satirlari` tablosuna `yillik_adet` sutunu

### 8. PDF Tablo Sutunlari Guncellendi
- Eski: #, Kaplama, Kalinlik, Malzeme, Birim, Miktar, B.Fiyat (7 sutun)
- Yeni: **#, Ref.No, Isim, Kaplama, Kalinlik, Malzeme, Birim, Miktar, B.Fiyat** (9 sutun)
- Kalinlik degerinin PDF'e yansimama sorunu duzeltildi (float donusumu eklendi)

### 9. "Kaydet ve Gonder" Butonu
- Sadece durum degistiriyor (GONDERILDI), gercek gonderim yapmiyor
- Ileride e-posta gonderimi eklenebilir

---

## Degisiklik Yapilan Dosyalar

| Dosya | Degisiklik |
|-------|-----------|
| `modules/teklif/teklif_detay.py` | UI formu: toplam kaldirildi, dosyalar, dahili bilgiler, Y.Adet/Y.Ciro, gorsel butonu, QLineEdit stili |
| `utils/teklif_pdf.py` | PDF: toplam kaldirildi, Ref.No/Isim sutunlari, kalinlik fix, satir gorselleri, metin wrap |
| `modules/teklif/teklif_liste.py` | Liste: toplam sutunlari kaldirildi, stat card guncellendi |
| `docs/teklif_migration_dosyalar.sql` | Migration: tum yeni DB sutunlari |

---

## Veritabani Migration (CALISTIRILMASI GEREKLI)

**Dosya:** `docs/teklif_migration_dosyalar.sql`

Eklenen sutunlar:
```
satislar.teklifler:
  - kaplama_sartnamesi_dosya  NVARCHAR(500) NULL
  - parca_gorseli_dosya       NVARCHAR(500) NULL
  - yillik_adet               INT NULL           (artik kullanilmiyor, satira tasindi)
  - yillik_ciro               DECIMAL(18,2) NULL (artik kullanilmiyor, satira tasindi)
  - dahili_not                NVARCHAR(MAX) NULL

satislar.teklif_satirlari:
  - gorsel_dosya              NVARCHAR(500) NULL
  - yillik_adet               INT NULL
```

---

## UI Tablo Sutun Yapisi (Guncel)

```
Col  | Sutun          | Tip        | PDF'de | Not
-----|----------------|------------|--------|----
0    | #              | read-only  | Evet   |
1    | Stok Kodu      | text       | Evet   | PDF'de "Ref.No"
2    | Urun Adi       | text       | Evet   | PDF'de "Isim"
3    | Kaplama Tipi   | ComboBox   | Evet   |
4    | Kalinlik(um)   | text       | Evet   |
5    | Malzeme        | text       | Evet   |
6    | Yuzey Alani    | text       | Hayir  |
7    | Birim          | ComboBox   | Evet   |
8    | Miktar         | text       | Evet   |
9    | Birim Fiyat    | text       | Evet   |
10   | Y.Adet         | text       | Hayir  | Yillik adet (dahili)
11   | Y.Ciro         | read-only  | Hayir  | Otomatik = B.Fiyat x Y.Adet
12   | Aciklama       | text       | Hayir  |
13   | Gorsel         | buton      | Evet   | Satir gorseli secme
```

---

## Dosya Depolama Yapisi

```
~/.redline_nexor/
  ├── reports/                          # PDF ciktilari
  │   └── TEKLIF_TEK_2026_XXXX_RevXX_*.pdf
  ├── teklif_dosyalar/
  │   └── {teklif_id}/
  │       ├── sartname.pdf              # Kaplama sartnamesi
  │       ├── parca_gorseli.png         # Ana parca gorseli
  │       ├── satir_1_gorsel.png        # Satir 1 gorseli
  │       └── satir_2_gorsel.jpg        # Satir 2 gorseli
  ├── settings.json
  ├── logs/
  └── backups/
```

---

## Bilinen Sorunlar / Devam Edilecekler
- [ ] Migration SQL veritabaninda calistirilmali
- [ ] "Kaydet ve Gonder" gercek e-posta gonderimi eklenebilir
- [ ] PDF'de Aciklama sutunu gosterilmiyor (yer kalmadi, gerekirse eklenebilir)
- [ ] teklifler tablosundaki yillik_adet ve yillik_ciro sutunlari artik kullanilmiyor (satirlara tasindi), temizlenebilir
