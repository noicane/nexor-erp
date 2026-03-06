# 🏭 ATMO LOGIC ERP - KAPSAMLI ÜRETİM AKIŞI DOKÜMANTASYONU

**Tarih:** 24 Ocak 2026  
**Versiyon:** 1.0  
**Sistem:** AtmoLogicERP - Manufacturing Execution System

---

## 📋 İÇİNDEKİLER

1. [Sistem Mimarisi](#sistem-mimarisi)
2. [7 Fazlı Üretim Akışı](#7-fazlı-üretim-akışı)
3. [RED Yönetim Sistemi](#red-yönetim-sistemi)
4. [Durum Kodu Sistemi](#durum-kodu-sistemi)
5. [Akış Şablonları](#akış-şablonları)
6. [Etiket Yönetimi](#etiket-yönetimi)
7. [Veritabanı Şeması](#veritabanı-şeması)
8. [Önemli Fonksiyonlar](#önemli-fonksiyonlar)
9. [Sorun Giderme](#sorun-giderme)
10. [Gelecek Geliştirmeler](#gelecek-geliştirmeler)

---

## 🏗️ SİSTEM MİMARİSİ

### Teknoloji Stack'i

```
Frontend:
├─ PySide6 (Qt6) - Desktop GUI
├─ QTableWidget - Liste görünümleri
└─ Custom Dialogs - Modal pencereler

Backend:
├─ Python 3.x
├─ SQL Server - Veritabanı
├─ pyodbc - Database driver
└─ Connection Pooling - Performans optimizasyonu

Modüller:
├─ mal_kabul.py - Malzeme kabul
├─ kalite_giris.py - Giriş kalite kontrol
├─ planlama.py - Üretim planlama
├─ depo_cikis.py - Depo çıkış operasyonları
├─ uretim_giris.py - Üretim girişi
├─ kalite_final.py - Final kalite kontrol
└─ kalite_red.py - Red yönetimi

Core:
├─ hareket_motoru.py - Stok hareket yönetimi
├─ database.py - DB connection pooling
└─ base_page.py - Temel sayfa sınıfı
```

### Mimari Özellikler

- **API-First**: FastAPI geçiş hedefi (4 fazlı plan)
- **Modüler Yapı**: Her modül bağımsız
- **Lot Bazlı**: Tüm takip lot numarası ile
- **Durum Bazlı**: durum_kodu ile akış yönetimi
- **Thread-Safe**: Connection pooling ile
- **Network Deploy**: \\AtlasNAS\Atmo_Logic\

---

## 🔄 7 FAZLI ÜRETİM AKIŞI

### GENEL AKIŞ DİYAGRAMI

```
┌─────────────────────────────────────────────────────────────────┐
│                      ÜRETİM AKIŞI                               │
└─────────────────────────────────────────────────────────────────┘

  1. MAL KABUL (KABUL)
  ↓
  Müşteriden malzeme gelir
  Lot numarası oluşturulur: LOT-YYMM-SSSS-PP
  Kabul Alanı (KAB-01) deposuna giriş
  durum_kodu = 'KABUL'
  
  ─────────────────────────────────────────────────
  
  2. GİRİŞ KALİTE (GIRIS_ONAY)
  ↓
  Görsel kontrol yapılır
  Miktar kontrolü
  Gerekirse örnek alınır
  durum_kodu = 'GIRIS_ONAY'
  Aynı depoda kalır (KAB-01)
  
  ─────────────────────────────────────────────────
  
  3. PLANLAMA (PLANLANDI)
  ↓
  İş emri oluşturulur
  Bara (batch) miktarları belirlenir
  Hat ve proses ataması
  durum_kodu = 'PLANLANDI'
  
  ─────────────────────────────────────────────────
  
  4. DEPO ÇIKIŞ (URETIMDE)
  ↓
  Üretim hattına transfer
  Kataforez/Toz Boya/Çinko hattı
  durum_kodu = 'URETIMDE'
  Bara bazında takip
  
  ─────────────────────────────────────────────────
  
  5. ÜRETİM GİRİŞİ (FKK_BEKLIYOR)
  ↓
  Üretim tamamlandı
  Final Kalite Kontrol (FKK) deposuna
  durum_kodu = 'FKK_BEKLIYOR'
  PLC verisi kaydedilir
  
  ─────────────────────────────────────────────────
  
  6. FİNAL KALİTE (SEVK_HAZIR / RED)
  ↓
  Kalite kontrolcü atanır
  Kontrol adet belirlenir
  
  ┌─────────────────┐
  │ Kontrol Sonucu  │
  └─────────────────┘
  
  ┌────────────┐         ┌────────────┐
  │  SAĞLAM    │         │   HATALI   │
  └────────────┘         └────────────┘
       ↓                      ↓
  SEVK-01 deposu        RED deposu
  durum_kodu =          durum_kodu = 'RED'
  'SEVK_HAZIR'          
  Lot: LOT-xxx-SEV      Lot: LOT-xxx-RED
  
  ─────────────────────────────────────────────────
  
  7. RED YÖNETİMİ (Varsa)
  ↓
  Red kararı verilir:
  
  ┌─────────┬────────────┬──────────────┐
  │ KABUL   │   SÖKÜM    │  KARANTINA   │
  └─────────┴────────────┴──────────────┘
       ↓           ↓            ↓
    FKK         SOKUM          KAR
  FKK_BEKLIYOR  SOKUM      KARANTINA
```

---

## 📝 FAZ 1: MAL KABUL

### Modül: `mal_kabul.py`

### Amaç
Müşteriden gelen malzemelerin sisteme kaydedilmesi ve ilk depoya girişi.

### İşlem Adımları

1. **İrsaliye Okuma**
   - Müşteri irsaliyesi okunur
   - Cari firma, tarih, irsaliye no kaydedilir

2. **Lot Numarası Oluşturma**
   ```python
   Format: LOT-YYMM-SSSS-PP
   
   LOT: Sabit prefix
   YYMM: Yıl-Ay (2601 = Ocak 2026)
   SSSS: Sıra numarası (0001, 0002...)
   PP: Palet numarası (01, 02...)
   
   Örnek: LOT-2601-0001-01
   ```

3. **Stok Kaydı**
   ```sql
   INSERT INTO stok.stok_bakiye (
       urun_id,
       lot_no,
       depo_id,  -- KAB-01 (Kabul Alanı)
       miktar,
       durum_kodu,  -- 'KABUL'
       kalite_durumu  -- 'KABUL_BEKLIYOR'
   )
   ```

4. **Hareket Kaydı**
   ```python
   motor.stok_giris(
       urun_id=urun_id,
       lot_no=lot_no,
       depo_id=kabul_depo_id,
       miktar=miktar,
       kaynak="MAL_KABUL",
       kaynak_id=kabul_id
   )
   ```

### Önemli Noktalar

- ✅ Lot numarası **benzersiz** olmalı
- ✅ Palet numarası **otomatik artar** (01, 02, 03...)
- ✅ KAB-01 deposu **sabit** kullanılır
- ✅ durum_kodu mutlaka **'KABUL'** olmalı

### Veritabanı Tabloları

- `tanim.mal_kabul` - Kabul kayıtları
- `stok.stok_bakiye` - Stok durumu
- `stok.stok_hareket` - Hareket geçmişi

---

## 📝 FAZ 2: GİRİŞ KALİTE KONTROL

### Modül: `kalite_giris.py`

### Amaç
Kabul edilen malzemelerin kalite kontrolü ve onaylanması.

### İşlem Adımları

1. **Bekleyen Lot'ları Listeleme**
   ```sql
   SELECT * FROM stok.stok_bakiye
   WHERE durum_kodu = 'KABUL'
     AND depo_id = (SELECT id FROM tanim.depolar WHERE kod = 'KAB-01')
     AND miktar > 0
   ```

2. **Kontrol Verisi Girişi**
   - Görsel kontrol notları
   - Miktar kontrolü
   - Örnek alma (varsa)
   - Kontrol eden personel

3. **Onay/Red Kararı**
   ```python
   if onaylandi:
       durum_kodu = 'GIRIS_ONAY'
       kalite_durumu = 'ONAYLANDI'
   else:
       durum_kodu = 'RED'
       kalite_durumu = 'REDDEDILDI'
       # RED deposuna transfer
   ```

4. **Durum Güncelleme**
   ```sql
   UPDATE stok.stok_bakiye
   SET durum_kodu = 'GIRIS_ONAY',
       kalite_durumu = 'ONAYLANDI'
   WHERE lot_no = ? AND depo_id = ?
   ```

### Önemli Noktalar

- ✅ Kontrol **lot bazında** yapılır
- ✅ Red edilen **direkt RED deposuna** gider
- ✅ Onaylanan **aynı depoda** kalır (KAB-01)
- ✅ Kontrol kaydı **kalite.giris_kontrol** tablosuna yazılır

### Veritabanı Tabloları

- `kalite.giris_kontrol` - Kontrol kayıtları
- `stok.stok_bakiye` - Durum güncelleme

---

## 📝 FAZ 3: PLANLAMA

### Modül: `planlama.py`

### Amaç
Üretim iş emirlerinin oluşturulması ve bara (batch) planlaması.

### İşlem Adımları

1. **Onaylı Lot'ları Listeleme**
   ```sql
   SELECT * FROM stok.stok_bakiye
   WHERE durum_kodu = 'GIRIS_ONAY'
     AND miktar > 0
   ORDER BY lot_no
   ```

2. **İş Emri Oluşturma**
   ```python
   # Manuel veya otomatik
   is_emri_no = generate_ie_no()  # IE-2601-0001
   
   INSERT INTO siparis.is_emirleri (
       is_emri_no,
       stok_id,
       musteri_id,
       miktar,
       durum  -- 'PLANLANDI'
   )
   ```

3. **Bara (Batch) Hesaplama**
   ```python
   # Örnek: 600 adet, bara=100
   bara_sayisi = math.ceil(600 / 100)  # 6 bara
   
   baralara_bol = {
       'bara_1': 100,
       'bara_2': 100,
       ...
       'bara_6': 100
   }
   ```

4. **Hat ve Proses Ataması**
   - Kataforez Hattı (KTL)
   - Toz Boya Hattı
   - Çinko Kaplama
   - Reçete bilgileri

5. **Durum Güncelleme**
   ```sql
   UPDATE stok.stok_bakiye
   SET durum_kodu = 'PLANLANDI'
   WHERE lot_no = ?
   ```

### Önemli Noktalar

- ✅ Bara miktarı **hat kapasitesine** göre
- ✅ İş emri numarası **benzersiz** olmalı
- ✅ Reçete bilgisi **zorunlu** (sıcaklık, süre, vs.)
- ✅ Planlanan lot **aynı depoda** kalır

### Veritabanı Tabloları

- `siparis.is_emirleri` - İş emirleri
- `uretim.baralama` - Bara planları
- `uretim.recete` - Reçete bilgileri

---

## 📝 FAZ 4: DEPO ÇIKIŞ

### Modül: `depo_cikis.py`

### Amaç
Planlanan lot'ların üretim hattına transferi.

### İşlem Adımları

1. **Planlı Lot'ları Listeleme**
   ```sql
   SELECT * FROM stok.stok_bakiye sb
   JOIN siparis.is_emirleri ie ON sb.lot_no = ie.lot_no
   WHERE sb.durum_kodu = 'PLANLANDI'
     AND ie.durum = 'PLANLANDI'
   ```

2. **Hat Seçimi**
   - Kataforez Hattı → KATAFOREZ-HAT
   - Toz Boya → TOZBOYA-HAT
   - Çinko → CINKO-HAT

3. **Transfer İşlemi**
   ```python
   motor.transfer(
       lot_no=lot_no,
       hedef_depo_id=hat_depo_id,
       miktar=miktar,
       kaynak="DEPO_CIKIS",
       kaynak_id=cikis_id
   )
   ```

4. **Durum Güncelleme**
   ```sql
   UPDATE stok.stok_bakiye
   SET durum_kodu = 'URETIMDE',
       depo_id = hat_depo_id
   WHERE lot_no = ?
   ```

### Önemli Noktalar

- ✅ Transfer **bara bazında** yapılabilir
- ✅ Hat deposu **dinamik** (hat seçimine göre)
- ✅ Çıkış zamanı **kaydedilir**
- ✅ İş emri durumu **'URETIMDE'** olur

### Veritabanı Tabloları

- `stok.depo_cikis` - Çıkış kayıtları
- `stok.stok_hareket` - Transfer geçmişi

---

## 📝 FAZ 5: ÜRETİM GİRİŞİ

### Modül: `uretim_giris.py`

### Amaç
Üretim tamamlanan lot'ların FKK (Final Kalite Kontrol) deposuna girişi.

### İşlem Adımları

1. **Üretimdeki Lot'ları Listeleme**
   ```sql
   SELECT * FROM stok.stok_bakiye
   WHERE durum_kodu = 'URETIMDE'
     AND depo_id IN (
         SELECT id FROM tanim.depolar 
         WHERE kod LIKE '%HAT%'
     )
   ```

2. **PLC Verisi Okuma** (Opsiyonel)
   ```python
   plc_data = {
       'sicaklik': 180,
       'sure': 20,
       'akim': 2.5,
       'voltaj': 220
   }
   ```

3. **FKK Transfer**
   ```python
   motor.transfer(
       lot_no=lot_no,
       hedef_depo_id=fkk_depo_id,  # FKK deposu
       miktar=miktar,
       kaynak="URETIM_GIRIS",
       kaynak_id=giris_id
   )
   ```

4. **Durum Güncelleme**
   ```sql
   UPDATE stok.stok_bakiye
   SET durum_kodu = 'FKK_BEKLIYOR',
       kalite_durumu = 'KONTROL_BEKLIYOR',
       depo_id = fkk_depo_id
   WHERE lot_no = ?
   ```

5. **PLC Veri Kaydetme**
   ```sql
   INSERT INTO uretim.plc_kayitlari (
       lot_no, sicaklik, sure, akim, voltaj, zaman
   )
   ```

### Önemli Noktalar

- ✅ FKK deposu **sabit** (FKK kodu)
- ✅ PLC verisi **opsiyonel** (hat varsa)
- ✅ Üretim süresi **hesaplanır**
- ✅ Bara bilgileri **korunur**

### Veritabanı Tabloları

- `stok.uretim_giris` - Giriş kayıtları
- `uretim.plc_kayitlari` - PLC verileri
- `stok.stok_hareket` - Transfer geçmişi

---

## 📝 FAZ 6: FİNAL KALİTE KONTROL

### Modül: `kalite_final.py`

### Amaç
Üretim tamamlanan ürünlerin final kalite kontrolü ve sevk/red kararı.

### İşlem Adımları

#### 6A. PERSONEL ATAMA (`kalite_final_kontrol.py`)

1. **FKK'daki Lot'ları Listeleme**
   ```sql
   SELECT * FROM stok.stok_bakiye
   WHERE durum_kodu = 'FKK_BEKLIYOR'
     AND depo_id = (SELECT id FROM tanim.depolar WHERE kod = 'FKK')
   ```

2. **Personel Atama**
   - Kontrolcü seç
   - Kontrol adedi belirle
   - İş emri oluştur

3. **Kayıt**
   ```sql
   INSERT INTO kalite.kontrol_is_emirleri (
       lot_no,
       kontrolcu_id,
       kontrol_adet,
       durum  -- 'BEKLIYOR'
   )
   ```

#### 6B. KONTROL VERİSİ GİRİŞİ (`kalite_final.py`)

1. **Atanmış Görevleri Listeleme**
   ```sql
   SELECT * FROM kalite.kontrol_is_emirleri
   WHERE durum = 'BEKLIYOR'
     AND kontrolcu_id = @current_user
   ```

2. **Kontrol Verisi Girişi**
   ```python
   kontrol_data = {
       'kontrol_edilen': 100,  # Kontrol edilen adet
       'saglam': 95,           # Sağlam adet
       'hatali': 5,            # Hatalı adet
       'hata_turleri': [       # Hata detayları
           {'hata_id': 1, 'adet': 3, 'not': 'Çizik'},
           {'hata_id': 2, 'adet': 2, 'not': 'Leke'}
       ]
   }
   ```

3. **Sağlam Ürün Transferi (SEVK)**
   ```python
   if saglam > 0:
       sevk_lot = f"{lot_no}-SEV"
       
       motor.stok_giris(
           urun_id=urun_id,
           lot_no=sevk_lot,
           depo_id=sevk_depo_id,  # SEVK-01
           miktar=saglam,
           kaynak="FINAL_KALITE",
           kaynak_id=kontrol_id
       )
       
       # Durum güncelle
       UPDATE stok.stok_bakiye
       SET durum_kodu = 'SEVK_HAZIR'
       WHERE lot_no = sevk_lot
   ```

4. **Hatalı Ürün Transferi (RED)**
   ```python
   if hatali > 0:
       red_lot = f"{lot_prefix}-RED"
       
       motor.stok_giris(
           urun_id=urun_id,
           lot_no=red_lot,
           depo_id=red_depo_id,  # RED
           miktar=hatali,
           kaynak="FINAL_KALITE",
           kaynak_id=kontrol_id
       )
       
       # Durum güncelle
       UPDATE stok.stok_bakiye
       SET durum_kodu = 'RED',
           kalite_durumu = 'REDDEDILDI'
       WHERE lot_no = red_lot
   ```

5. **FKK Bakiye Güncelleme**
   ```python
   kalan = toplam_miktar - kontrol_edilen
   
   if kalan > 0:
       # FKK'da kalan var
       UPDATE stok.stok_bakiye
       SET miktar = kalan
       WHERE lot_no = lot_no AND depo_id = fkk_depo_id
   else:
       # Hepsi kontrol edildi, FKK'yı sıfırla
       UPDATE stok.stok_bakiye
       SET miktar = 0, durum_kodu = 'SEVK_EDILDI'
       WHERE lot_no = lot_no AND depo_id = fkk_depo_id
   ```

6. **Etiket Kuyruğuna Ekleme**
   ```sql
   INSERT INTO kalite.etiket_kuyrugu (
       proses_kontrol_id,
       lot_no,  -- sevk_lot (LOT-xxx-SEV)
       stok_kodu,
       stok_adi,
       musteri,
       miktar,
       kontrolcu_adi,
       kontrol_tarihi,
       basildi_mi  -- 0
   )
   ```

### Önemli Noktalar

- ✅ Kontrol **adet bazında** yapılır
- ✅ **İki ayrı modül**: Atama + Kontrol verisi
- ✅ Sağlam → **SEVK-01** deposu, Lot: LOT-xxx-SEV
- ✅ Hatalı → **RED** deposu, Lot: LOT-xxx-RED
- ✅ Kalan → **FKK** deposunda kalır
- ✅ Hata türleri **detaylı kaydedilir**
- ✅ Etiket verisi **otomatik kaydedilir**
- ✅ **Tek connection** kullanılır (deadlock önleme)
- ✅ **Tek transaction** (ACID garantisi)

### Kritik Hatalar ve Çözümler

#### ❌ HATA 1: FKK'dan Miktar Düşmüyor
```python
# YANLIŞ:
UPDATE stok.stok_bakiye SET miktar = ?
WHERE lot_no = ?

# DOĞRU:
UPDATE stok.stok_bakiye SET miktar = ?
WHERE lot_no = ? AND depo_id = ?  # ✅ depo_id eklendi
```

#### ❌ HATA 2: Deadlock
```python
# YANLIŞ:
conn = get_db_connection()
motor_conn = get_db_connection()  # İki connection
motor = HareketMotoru(motor_conn)
motor_conn.commit()  # Ara commit
conn.commit()

# DOĞRU:
conn = get_db_connection()
motor = HareketMotoru(conn)  # ✅ Aynı connection
conn.commit()  # ✅ Tek commit
```

#### ❌ HATA 3: Etiket Dialog Donması
```python
# YANLIŞ:
# Kaydet butonuna basınca etiket dialog açılıyor

# DOĞRU:
# İki ayrı buton:
💾 Kaydet (etiket yok)
🏷️ Etiket Bas (opsiyonel, kuyruktan seçer)
```

### Veritabanı Tabloları

- `kalite.kontrol_is_emirleri` - Kontrol görevleri
- `kalite.proses_kontrol` - Kontrol kayıtları
- `kalite.proses_kontrol_detay` - Hata detayları
- `kalite.etiket_kuyrugu` - Etiket verileri
- `stok.stok_bakiye` - Stok durumu (3 depo: FKK, SEVK-01, RED)
- `stok.stok_hareket` - Hareket geçmişi

---

## 📝 FAZ 7: RED YÖNETİMİ

### Modül: `kalite_red.py`

### Amaç
Red edilen ürünler için karar verme ve ilgili depoya transfer.

### Red Kararları

#### 1. KABUL (FKK'ya Dön)
```python
# RED → FKK transferi
motor.transfer(
    lot_no=red_lot_no,
    hedef_depo_id=fkk_depo_id,
    miktar=miktar,
    kaynak="KALITE_RED",
    kaynak_id=red_kayit_id
)

# Durum güncelle
UPDATE stok.stok_bakiye
SET durum_kodu = 'FKK_BEKLIYOR',
    kalite_durumu = 'KONTROL_BEKLIYOR'
WHERE lot_no = ? AND depo_id = fkk_depo_id
```

**Kullanım:** Küçük hatalar, tekrar kontrol edilebilir

#### 2. SÖKÜM
```python
# Lot adına -S eki ekle
sokum_lot = f"{red_lot_no}-S"

# RED → SOKUM transferi
motor.transfer(
    lot_no=red_lot_no,
    hedef_depo_id=sokum_depo_id,
    miktar=miktar,
    kaynak="KALITE_RED",
    kaynak_id=red_kayit_id
)

# Lot adını değiştir ve durum güncelle
UPDATE stok.stok_bakiye
SET lot_no = sokum_lot,
    durum_kodu = 'SOKUM',
    kalite_durumu = 'SOKUM_BEKLIYOR'
WHERE lot_no = red_lot_no AND depo_id = sokum_depo_id
```

**Kullanım:** Kaplama sökülecek, tekrar işlenecek

#### 3. MÜŞTERİ ONAYI (Karantina)
```python
# RED → KAR (Karantina) transferi
motor.transfer(
    lot_no=red_lot_no,
    hedef_depo_id=kar_depo_id,
    miktar=miktar,
    kaynak="KALITE_RED",
    kaynak_id=red_kayit_id
)

# Durum güncelle
UPDATE stok.stok_bakiye
SET durum_kodu = 'KARANTINA',
    kalite_durumu = 'MUSTERI_ONAY_BEKLIYOR'
WHERE lot_no = ? AND depo_id = kar_depo_id
```

**Kullanım:** Müşteri kararı beklenecek, OKEY gelirse sevk

### Kısmi Karar Desteği

```python
# Örnek: 3 adet RED var, 2'sine karar veriyorsun

islem_miktar = 2  # Karar verilen
kalan_miktar = 3 - 2  # 1 adet kalacak

# Transfer yap
motor.transfer(..., miktar=islem_miktar)

# RED kaydını güncelle
if kalan_miktar > 0:
    UPDATE kalite.uretim_redler
    SET red_miktar = kalan_miktar,
        durum = 'BEKLIYOR'  # ✅ Tekrar karar alınabilir
    WHERE id = red_kayit_id
```

### Önemli Noktalar

- ✅ Kısmi karar **desteklenir**
- ✅ SÖKÜM'de lot adı **-S eki** alır
- ✅ **WHERE'de depo_id** olmalı (kritik!)
- ✅ Kalan miktar **BEKLIYOR** durumda kalır
- ✅ Akış şablonları **kullanılır** (RED-KABUL, söküm, RED-KARANTINA)

### Kritik Hatalar ve Çözümler

#### ❌ HATA: Yanlış Depodan Düşüyor
```python
# YANLIŞ:
UPDATE stok.stok_bakiye 
SET miktar = miktar - ?
WHERE lot_no = ? AND miktar >= ?

# Aynı lot_no birden fazla depoda olabilir!
# Yanlış depodan düşer!

# DOĞRU:
UPDATE stok.stok_bakiye 
SET miktar = miktar - ?
WHERE lot_no = ? 
  AND depo_id = ?  # ✅ Kaynak depo
  AND miktar >= ?
```

#### ❌ HATA: Kısmi Karar Sonrası Tekrar Karar Alınamıyor
```python
# YANLIŞ:
UPDATE kalite.uretim_redler
SET red_miktar = ?
WHERE id = ?
# durum değişmedi, sistem "işlendi" sanıyor

# DOĞRU:
UPDATE kalite.uretim_redler
SET red_miktar = ?,
    durum = 'BEKLIYOR'  # ✅ Tekrar karar alınabilir
WHERE id = ?
```

### Veritabanı Tabloları

- `kalite.uretim_redler` - Red kayıtları
- `stok.stok_bakiye` - Stok durumu
- `stok.stok_hareket` - Transfer geçmişi

---

## 🏷️ DURUM KODU SİSTEMİ

### Tüm Durum Kodları

| Durum Kodu | Açıklama | Depo | Sonraki Adım |
|------------|----------|------|--------------|
| `KABUL` | Mal kabul edildi | KAB-01 | Giriş Kalite |
| `GIRIS_ONAY` | Giriş kalite onaylandı | KAB-01 | Planlama |
| `PLANLANDI` | Üretim planlandı | KAB-01 | Depo Çıkış |
| `URETIMDE` | Üretim hattında | HAT depoları | Üretim Girişi |
| `FKK_BEKLIYOR` | Final kalite bekliyor | FKK | Final Kalite |
| `SEVK_HAZIR` | Sevke hazır | SEVK-01 | Sevkiyat |
| `SEVK_EDILDI` | Sevk edildi | - | Tamamlandı |
| `RED` | Red edildi | RED | Red Yönetimi |
| `SOKUM` | Söküme gönderildi | SOKUM | Söküm İşlemi |
| `KARANTINA` | Karantinada | KAR | Müşteri Kararı |

### Durum Geçiş Matrisi

```
KABUL ──────────────────────> GIRIS_ONAY ──────────> PLANLANDI
                                    │
                                    │ (Red)
                                    ↓
                                  RED
                                  
PLANLANDI ──────────────────────> URETIMDE ────────> FKK_BEKLIYOR

FKK_BEKLIYOR ───┬───────────> SEVK_HAZIR ────────> SEVK_EDILDI
                │
                └───────────> RED
                
RED ─────────┬─────────> FKK_BEKLIYOR (Kabul)
             │
             ├─────────> SOKUM (Söküm)
             │
             └─────────> KARANTINA (Müşteri Onayı)
```

### SQL Sorguları

```sql
-- Durum bazında stok raporu
SELECT 
    durum_kodu,
    COUNT(DISTINCT lot_no) as lot_sayisi,
    SUM(miktar) as toplam_miktar
FROM stok.stok_bakiye
WHERE miktar > 0
GROUP BY durum_kodu
ORDER BY durum_kodu;

-- Belirli durumdaki lot'lar
SELECT 
    sb.lot_no,
    d.kod as depo,
    sb.miktar,
    sb.durum_kodu,
    sb.kalite_durumu
FROM stok.stok_bakiye sb
LEFT JOIN tanim.depolar d ON sb.depo_id = d.id
WHERE sb.durum_kodu = 'FKK_BEKLIYOR'
  AND sb.miktar > 0;

-- Lot geçmişi
SELECT 
    sh.islem_tarihi,
    sh.islem_tipi,
    d1.kod as kaynak_depo,
    d2.kod as hedef_depo,
    sh.miktar,
    sh.onceki_durum_kodu,
    sh.yeni_durum_kodu
FROM stok.stok_hareket sh
LEFT JOIN tanim.depolar d1 ON sh.kaynak_depo_id = d1.id
LEFT JOIN tanim.depolar d2 ON sh.hedef_depo_id = d2.id
WHERE sh.lot_no = 'LOT-2601-0001-01'
ORDER BY sh.islem_tarihi;
```

---

## 📋 AKIŞ ŞABLONLARI

### Tanım
Akış şablonları, stok hareketlerinin otomatik adımlarını tanımlar. `tanim.akis` modülünden yönetilir.

### Mevcut Şablonlar

#### 1. STANDART-FKK (Normal Üretim)
```
Adımlar:
1. Mal Kabul → Kabul Alanı
2. Giriş Kalite → Kabul Alanı (KK Gerekli)
3. Depo → Kabul Alanı
4. Üretim → Kataforez Hattı
5. Final Kalite → FinalKalite (KK Gerekli)
6. Sevk → Sevk Depo
```

#### 2. RED-KABUL (FKK Dönüşü)
```
Adımlar:
1. Red → FKK (TRANSFER)
   - Zorunlu: ✓
   - KK Gerekli: ✗
```

#### 3. söküm (Söküm)
```
Adımlar:
1. Red → SOKUM (TRANSFER)
   - Zorunlu: ✓
   - KK Gerekli: ✗
```

#### 4. RED-KARANTINA (Müşteri Onayı)
```
Adımlar:
1. Red → KAR (TRANSFER)
   - Zorunlu: ✓
   - KK Gerekli: ✗
```

### Veritabanı Yapısı

```sql
-- Akış şablonları
tanim.akis_sablon
├─ id (PK)
├─ kod (Unique)
├─ ad
├─ aciklama
├─ varsayilan_mi
└─ aktif_mi

-- Akış adımları
tanim.akis_adim
├─ id (PK)
├─ sablon_id (FK)
├─ sira
├─ adim_tipi_id (FK)
├─ hedef_depo_id (FK)
├─ zorunlu
├─ kalite_kontrol_gerekli
├─ atlanabilir
└─ aciklama

-- Adım tipleri
tanim.akis_adim_tipleri
├─ id (PK)
├─ kod
├─ ad
└─ aciklama
```

### GUI'den Yönetim

```python
# tanim_akis.py modülü

# Yeni şablon ekleme
+ Yeni Şablon
  ├─ Kod: RED-KABUL
  ├─ Ad: Red Kabul - FKK Dönüşü
  ├─ Açıklama: Red edilen ürünlerin FKK'ya dönüşü
  └─ Varsayılan: ☐

# Adım ekleme
+ Adım Ekle
  ├─ Sıra: 1
  ├─ Adım Tipi: TRANSFER
  ├─ Hedef Depo: FKK
  ├─ Zorunlu: ☑
  ├─ KK Gerekli: ☐
  └─ Açıklama: Red deposundan FKK'ya transfer
```

---

## 🏷️ ETİKET YÖNETİMİ

### Etiket Kuyruğu Sistemi

```sql
-- Etiket kuyruğu
kalite.etiket_kuyrugu
├─ id (PK)
├─ proses_kontrol_id (FK)
├─ lot_no
├─ stok_kodu
├─ stok_adi
├─ musteri
├─ miktar
├─ kontrolcu_adi
├─ kontrol_tarihi
├─ basildi_mi (BIT)
├─ basim_tarihi
├─ basim_sayisi
└─ olusturma_tarihi
```

### İşleyiş

1. **Otomatik Kayıt** (Final Kalite)
   ```python
   if saglam > 0:
       INSERT INTO kalite.etiket_kuyrugu (
           lot_no,  # LOT-xxx-SEV
           miktar,
           kontrolcu_adi,
           basildi_mi  # 0 (Bekliyor)
       )
   ```

2. **Manuel Basım**
   ```python
   # 🏷️ Etiket Bas butonu
   # Her zaman aktif!
   
   # Bekleyen etiketleri listele
   SELECT * FROM kalite.etiket_kuyrugu
   WHERE basildi_mi = 0
   ORDER BY kontrol_tarihi DESC
   
   # Kullanıcı seçer, etiket dialog açılır
   # Basıldı → basildi_mi = 1, basim_sayisi++
   ```

3. **Çoklu Basım**
   - Aynı etiketi birden fazla kez basabilirsiniz
   - `basim_sayisi` artırılır
   - `basildi_mi` = 1 olur

### Önemli Noktalar

- ✅ **İki ayrı buton**: 💾 Kaydet, 🏷️ Etiket Bas
- ✅ Etiket butonu **her zaman aktif**
- ✅ Etiket verisi **kaydedilir** (kaybolmaz)
- ✅ **Kuyruktan seçim** yapılır
- ✅ Çoklu basım **desteklenir**

### Godex Yazıcı Entegrasyonu

```python
# Etiket formatı: EZPL
def generate_ezpl(etiket_data):
    ezpl = f"""
    ^Q50,3
    ^W100
    ^H10
    ^P1
    ^S4
    ^AD
    ^C1
    ^R0
    ~Q+0
    ^O0
    ^D0
    ^E18
    ~R255
    ^L
    Dy2-me-dd
    Th:m:s
    
    # Müşteri
    T10,10,0,3,pt8;{etiket_data['musteri']}
    
    # Ürün
    T10,60,0,3,pt8;{etiket_data['urun']}
    
    # Lot No (Barkod)
    B10,110,0,1,3,5,90,N,"{etiket_data['lot_no']}"
    
    # Miktar
    T10,220,0,3,pt10;ADET: {etiket_data['adet']}
    
    # Tarih
    T200,10,0,3,pt6;{etiket_data['tarih']}
    
    E
    """
    return ezpl
```

---

## 💾 VERİTABANI ŞEMASI

### Temel Tablolar

#### stok.stok_bakiye
```sql
CREATE TABLE stok.stok_bakiye (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    urun_id INT NOT NULL,
    lot_no NVARCHAR(50) NOT NULL,
    depo_id INT NOT NULL,
    miktar DECIMAL(18,4) DEFAULT 0,
    rezerve_miktar DECIMAL(18,4) DEFAULT 0,
    durum_kodu NVARCHAR(50),  -- ✅ Yeni kolon
    kalite_durumu NVARCHAR(50),
    olusturma_tarihi DATETIME DEFAULT GETDATE(),
    guncelleme_tarihi DATETIME,
    
    CONSTRAINT UQ_lot_depo UNIQUE (lot_no, depo_id)
);

-- Index'ler
CREATE INDEX IX_stok_bakiye_lot_no ON stok.stok_bakiye(lot_no);
CREATE INDEX IX_stok_bakiye_durum_kodu ON stok.stok_bakiye(durum_kodu);
CREATE INDEX IX_stok_bakiye_depo_id ON stok.stok_bakiye(depo_id);
```

#### stok.stok_hareket
```sql
CREATE TABLE stok.stok_hareket (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    lot_no NVARCHAR(50) NOT NULL,
    urun_id INT NOT NULL,
    islem_tipi NVARCHAR(20) NOT NULL,  -- GIRIS, CIKIS, TRANSFER
    kaynak_depo_id INT,
    hedef_depo_id INT,
    miktar DECIMAL(18,4) NOT NULL,
    kaynak NVARCHAR(50),  -- IS_EMRI, MAL_KABUL, KALITE_RED vb.
    kaynak_id INT,
    kullanici_id INT,
    aciklama NVARCHAR(500),
    onceki_durum_kodu NVARCHAR(50),  -- ✅ Yeni kolon
    yeni_durum_kodu NVARCHAR(50),    -- ✅ Yeni kolon
    islem_tarihi DATETIME DEFAULT GETDATE()
);

-- Index'ler
CREATE INDEX IX_stok_hareket_lot_no ON stok.stok_hareket(lot_no);
CREATE INDEX IX_stok_hareket_islem_tarihi ON stok.stok_hareket(islem_tarihi);
```

#### kalite.proses_kontrol
```sql
CREATE TABLE kalite.proses_kontrol (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    lot_no NVARCHAR(50) NOT NULL,
    is_emri_id INT,
    kontrol_eden_id INT NOT NULL,
    kontrol_tarihi DATETIME DEFAULT GETDATE(),
    toplam_miktar INT,
    kontrol_edilen INT,
    saglam INT,
    hatali INT,
    kalan INT,
    notlar NVARCHAR(MAX),
    durum NVARCHAR(20) DEFAULT 'TAMAMLANDI'
);
```

#### kalite.proses_kontrol_detay
```sql
CREATE TABLE kalite.proses_kontrol_detay (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    kontrol_id BIGINT NOT NULL,
    hata_turu_id INT NOT NULL,
    adet INT NOT NULL,
    notlar NVARCHAR(500),
    
    CONSTRAINT FK_kontrol_detay_kontrol 
        FOREIGN KEY (kontrol_id) 
        REFERENCES kalite.proses_kontrol(id)
);
```

#### kalite.etiket_kuyrugu
```sql
CREATE TABLE kalite.etiket_kuyrugu (
    id INT IDENTITY(1,1) PRIMARY KEY,
    proses_kontrol_id BIGINT,
    lot_no NVARCHAR(100) NOT NULL,
    stok_kodu NVARCHAR(50),
    stok_adi NVARCHAR(200),
    musteri NVARCHAR(200),
    miktar INT NOT NULL,
    kontrolcu_adi NVARCHAR(100),
    kontrol_tarihi DATETIME,
    basildi_mi BIT DEFAULT 0,
    basim_tarihi DATETIME,
    basim_sayisi INT DEFAULT 0,
    olusturma_tarihi DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT FK_etiket_kuyrugu_proses_kontrol 
        FOREIGN KEY (proses_kontrol_id) 
        REFERENCES kalite.proses_kontrol(id)
);
```

#### kalite.uretim_redler
```sql
CREATE TABLE kalite.uretim_redler (
    id INT IDENTITY(1,1) PRIMARY KEY,
    is_emri_id INT,
    lot_no NVARCHAR(50),
    red_miktar INT,
    kontrol_id BIGINT,
    red_tarihi DATETIME DEFAULT GETDATE(),
    kontrol_eden_id INT,
    durum NVARCHAR(20) DEFAULT 'BEKLIYOR',  -- BEKLIYOR, KABUL, SOKUM, MUSTERI_ONAY
    karar NVARCHAR(20),
    karar_veren_id INT,
    karar_tarihi DATETIME,
    karar_notu NVARCHAR(500),
    islem_tipi NVARCHAR(20),
    aciklama NVARCHAR(500),
    olusturma_tarihi DATETIME DEFAULT GETDATE(),
    guncelleme_tarihi DATETIME
);
```

### Akış Tabloları

#### tanim.akis_sablon
```sql
CREATE TABLE tanim.akis_sablon (
    id INT IDENTITY(1,1) PRIMARY KEY,
    kod NVARCHAR(50) NOT NULL UNIQUE,
    ad NVARCHAR(200) NOT NULL,
    aciklama NVARCHAR(500),
    varsayilan_mi BIT DEFAULT 0,
    aktif_mi BIT DEFAULT 1,
    olusturma_tarihi DATETIME DEFAULT GETDATE(),
    guncelleme_tarihi DATETIME
);
```

#### tanim.akis_adim
```sql
CREATE TABLE tanim.akis_adim (
    id INT IDENTITY(1,1) PRIMARY KEY,
    sablon_id INT NOT NULL,
    sira INT NOT NULL,
    adim_tipi_id INT NOT NULL,
    hedef_depo_id INT,
    zorunlu BIT DEFAULT 1,
    kalite_kontrol_gerekli BIT DEFAULT 0,
    atlanabilir BIT DEFAULT 0,
    aciklama NVARCHAR(500),
    aktif_mi BIT DEFAULT 1,
    
    CONSTRAINT FK_akis_adim_sablon 
        FOREIGN KEY (sablon_id) 
        REFERENCES tanim.akis_sablon(id),
    CONSTRAINT FK_akis_adim_tipi 
        FOREIGN KEY (adim_tipi_id) 
        REFERENCES tanim.akis_adim_tipleri(id)
);
```

---

## ⚙️ ÖNEMLİ FONKSİYONLAR

### HareketMotoru.transfer()

```python
def transfer(
    self,
    lot_no: str,
    hedef_depo_id: int,
    miktar: float = None,
    kaynak: str = None,
    kaynak_id: int = None,
    aciklama: str = None
) -> HareketSonuc:
    """
    Depo transferi yap
    
    Args:
        lot_no: Transfer edilecek lot
        hedef_depo_id: Hedef depo ID
        miktar: Transfer miktarı (None ise tüm bakiye)
        kaynak: Referans tipi (IS_EMRI, KALITE_RED vb.)
        kaynak_id: Referans ID
        aciklama: Açıklama
    
    Returns:
        HareketSonuc(basarili, hata, mesaj)
    """
```

**Önemli:**
- ✅ Kaynak depodan **otomatik düşer**
- ✅ Hedef depoda **yeni kayıt** oluşturur
- ✅ Lot numarası **aynı kalır** (değişmez)
- ✅ Hareket kaydı **otomatik** oluşur
- ✅ **Transaction güvenli**

### HareketMotoru.stok_giris()

```python
def stok_giris(
    self,
    urun_id: int,
    lot_no: str,
    depo_id: int,
    miktar: float,
    kaynak: str = None,
    kaynak_id: int = None,
    aciklama: str = None
) -> HareketSonuc:
    """
    Stok girişi yap
    
    Args:
        urun_id: Ürün ID
        lot_no: Lot numarası
        depo_id: Hedef depo ID
        miktar: Giriş miktarı
        kaynak: Referans tipi
        kaynak_id: Referans ID
        aciklama: Açıklama
    
    Returns:
        HareketSonuc(basarili, hata, mesaj)
    """
```

**Önemli:**
- ✅ Yeni lot için **yeni kayıt** oluşturur
- ✅ Mevcut lot varsa **miktarı artırır**
- ✅ Hareket kaydı **otomatik** oluşur
- ✅ **Transaction güvenli**

### get_db_connection() - Connection Pooling

```python
# core/database.py

# YANLIŞ KULLANIM:
def query():
    conn = pyodbc.connect(...)  # Her seferinde yeni bağlantı
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    conn.close()

# DOĞRU KULLANIM:
def query():
    conn = get_db_connection()  # Pool'dan alır
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    conn.close()  # Pool'a geri verir
```

**Özellikler:**
- ✅ **Connection pooling** (10 max connection)
- ✅ **Auto-recovery** (bağlantı kopsa yeniden bağlanır)
- ✅ **Thread-safe**
- ✅ **84.1% pool hit rate** (2,908 ops/sec)

---

## 🔧 SORUN GİDERME

### Sık Karşılaşılan Hatalar

#### 1. FKK'dan Miktar Düşmüyor

**Belirti:**
```
Final kalite kontrol → Sağlam 95, Hatalı 5
FKK deposunda hala 100 adet var
```

**Sebep:**
```python
# WHERE'de depo_id eksik
UPDATE stok.stok_bakiye 
SET miktar = miktar - ?
WHERE lot_no = ?
```

**Çözüm:**
```python
UPDATE stok.stok_bakiye 
SET miktar = miktar - ?
WHERE lot_no = ? AND depo_id = ?  # ✅
```

#### 2. Deadlock / Program Donuyor

**Belirti:**
```
Kaydet butonuna basınca program donuyor
SQL Server: DEADLOCK detected
```

**Sebep:**
```python
# İki ayrı connection
conn = get_db_connection()
motor_conn = get_db_connection()
motor = HareketMotoru(motor_conn)
motor_conn.commit()  # Ara commit
conn.commit()
```

**Çözüm:**
```python
# Tek connection, tek transaction
conn = get_db_connection()
motor = HareketMotoru(conn)
# Ara commit'ler YOK
conn.commit()  # Tek commit
```

#### 3. Etiket Dialog Donması

**Belirti:**
```
Kaydet butonuna basınca etiket dialog açılıyor
Yazıcı bulunamıyor, askıda kalıyor
```

**Sebep:**
```python
# Kaydet butonu etiket basıyor
self.kaydet_btn.clicked.connect(self._kaydet_ve_etiket)
```

**Çözüm:**
```python
# İki ayrı buton
💾 Kaydet → Sadece kayıt
🏷️ Etiket Bas → Kuyruktan seç ve bas
```

#### 4. Kısmi Karar Sonrası Tekrar Karar Alınamıyor

**Belirti:**
```
3 adet RED var
2'sine karar veriyorsun
1 adet kalıyor ama "karar alındı" diyor
```

**Sebep:**
```python
# durum güncellenmedi
UPDATE kalite.uretim_redler
SET red_miktar = ?
WHERE id = ?
```

**Çözüm:**
```python
UPDATE kalite.uretim_redler
SET red_miktar = ?,
    durum = 'BEKLIYOR'  # ✅
WHERE id = ?
```

#### 5. Yanlış Depodan Düşüyor (RED)

**Belirti:**
```
RED'den 2 adet söküm
Ama SOKUM'da 3 adet görünüyor
KAB-01'den düşmüş
```

**Sebep:**
```python
# WHERE'de depo_id eksik
UPDATE stok.stok_bakiye 
SET miktar = miktar - ?
WHERE lot_no = ?
# Aynı prefix'li tüm lot'lardan düşer!
```

**Çözüm:**
```python
UPDATE stok.stok_bakiye 
SET miktar = miktar - ?
WHERE lot_no = ? 
  AND depo_id = ?  # ✅ Kaynak depo
  AND miktar >= ?
```

### Debug Teknikleri

#### 1. Console Debug
```python
print(f"DEBUG: lot_no={lot_no}, depo_id={depo_id}, miktar={miktar}")
print(f"DEBUG: Durum güncellendi - durum_kodu='{durum_kodu}'")
```

#### 2. SQL Profiler
```sql
-- Gerçek zamanlı SQL sorguları izle
-- SQL Server Profiler veya Extended Events
```

#### 3. Transaction Kontrolü
```python
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # İşlemler...
    
    conn.commit()  # ✅ Başarılı
    print("✓ Transaction commit edildi")
except Exception as e:
    conn.rollback()  # ❌ Hata
    print(f"✗ Transaction rollback: {e}")
finally:
    conn.close()
```

#### 4. Stok Bakiye Kontrolü
```sql
-- Her işlem sonrası kontrol
SELECT 
    sb.lot_no,
    d.kod AS depo,
    sb.miktar,
    sb.durum_kodu,
    sb.kalite_durumu
FROM stok.stok_bakiye sb
JOIN tanim.depolar d ON sb.depo_id = d.id
WHERE sb.lot_no LIKE 'LOT-2601-0001%'
  AND sb.miktar > 0
ORDER BY sb.lot_no, d.kod;
```

---

## 🚀 GELECEK GELİŞTİRMELER

### Faz 1: API Migration (FastAPI)
- [ ] RESTful API endpoints
- [ ] JWT authentication
- [ ] WebSocket for real-time updates
- [ ] Swagger documentation

### Faz 2: Web Frontend
- [ ] React + TypeScript
- [ ] Material-UI components
- [ ] Progressive Web App (PWA)
- [ ] Mobile responsive

### Faz 3: Advanced Analytics
- [ ] Production efficiency dashboard
- [ ] Quality control statistics
- [ ] Bottleneck analysis
- [ ] Predictive maintenance

### Faz 4: Integrations
- [ ] PLC real-time integration
- [ ] Barcode scanner support
- [ ] E-invoice automation
- [ ] ERP integration (Zirve)

### Faz 5: Advanced Features
- [ ] AI-powered defect detection
- [ ] Recipe deviation alerts
- [ ] Capacity planning optimization
- [ ] Customer portal

---

## 📞 DESTEK

### Geliştirici Notları

```python
# Önemli dosyalar
kalite_final_v10_IMPORT_FIXED.py      # Final kalite (son versiyon)
kalite_red_v5_DEPO_ID_FIX.py          # RED yönetimi (son versiyon)
ETIKET_KUYRUGU_TABLO_v2.sql           # Etiket kuyruğu tablosu
hareket_motoru.py                      # Stok hareket yönetimi
database.py                            # Connection pooling

# Kritik ayarlar
Connection pool size: 10
Max operations/sec: 2,908
Pool hit rate: 84.1%
Transaction timeout: 30 saniye
Network path: \\AtlasNAS\Atmo_Logic\
```

### Test Senaryoları

1. **Normal Üretim Akışı**
   ```
   Mal Kabul → Giriş Kalite → Planlama → Depo Çıkış 
   → Üretim Girişi → Final Kalite → Sevk
   ```

2. **RED Akışı - SÖKÜM**
   ```
   Final Kalite (Hatalı 5 adet) → RED deposu 
   → RED Yönetimi → SÖKÜM → SOKUM deposu
   ```

3. **RED Akışı - KABUL**
   ```
   Final Kalite (Hatalı 10 adet) → RED deposu 
   → RED Yönetimi → KABUL → FKK deposu 
   → Final Kalite (tekrar)
   ```

4. **Kısmi Karar**
   ```
   RED deposu: 3 adet
   → 2 adet SÖKÜM (SOKUM'a)
   → 1 adet kalır (RED'de)
   → Kalan 1 adete tekrar karar
   ```

5. **Etiket Kuyruğu**
   ```
   Final Kalite → Kaydet (etiket yok)
   → Sonradan: Etiket Bas → Kuyruktan seç → Bas
   → Tekrar bas (çoklu basım)
   ```

---

## 📚 REFERANSLAR

### Dokümantasyon Dosyaları

```
/mnt/user-data/outputs/
├── kalite_final_v10_IMPORT_FIXED.py
├── kalite_red_v5_DEPO_ID_FIX.py
├── ETIKET_KUYRUGU_TABLO_v2.sql
├── RED_MODUL_OZET.md
├── RED_AKIS_ENTEGRASYON_OZET.md
├── FINAL_KALITE_IKI_MODUL_GUNCELLEME.md
└── HATA_DUZELTMELERI_v4.md
```

### Veritabanı Şema Dosyaları

```
01_veritabani_semasi.md       # Tüm tablo yapıları
02_hat_pozisyon_*.md          # PLC entegrasyon
stok_kartı.txt                # Stok kartı yapısı
maliyet.txt                   # Maliyet hesaplama
tablo.txt                     # 663 satır tablo listesi
```

---

## ✅ VERSION HISTORY

| Versiyon | Tarih | Değişiklikler |
|----------|-------|---------------|
| 1.0 | 24.01.2026 | İlk kapsamlı dokümantasyon |
| | | - 7 fazlı akış tamamlandı |
| | | - RED yönetimi entegre edildi |
| | | - Etiket kuyruğu eklendi |
| | | - durum_kodu sistemi tamamlandı |
| | | - Tüm kritik hatalar düzeltildi |

---

**SON GÜNCELLEME:** 24 Ocak 2026, 22:00  
**DURUM:** ✅ Production Ready  
**TEST EDİLDİ:** ✅ Tüm senaryolar çalışıyor

---

**🎉 ATMO LOGIC ERP - TAM ÜRETİM TAKİP SİSTEMİ HAZIR! 🎉**
