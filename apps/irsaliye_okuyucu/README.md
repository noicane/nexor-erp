# NEXOR İrsaliye Okuyucu

Müşteri parça teslim irsaliyelerini tablet/telefon kamerasından çekip
otomatik olarak **siparis.giris_irsaliyeleri** (TASLAK) kaydı oluşturan web uygulaması.

Sonrasında NEXOR'un mevcut **Depo > Mal Kabul** ekranında lot bölme, etiket, onay yapılır.

---

## Kurulum (NEXOR PC'de bir kerelik — 5 dakika)

### 1) Anthropic API Key al
- https://console.anthropic.com/ → giriş yap (yoksa kayıt ol, $5 ücretsiz kredi gelir)
- Sol menü **API Keys** → **Create Key** → isim ver (örn. "NEXOR İrsaliye OCR")
- `sk-ant-api03-...` ile başlayan anahtarı **tek seferlik** gösterilirken kopyala

### 2) Ortam dosyası
```
copy .env.example .env
notepad .env
```
`ANTHROPIC_API_KEY=sk-ant-api03-...` satırına kopyaladığın anahtarı yapıştır, kaydet.

### 3) Çalıştır
```
run.bat
```
İlk çalıştırmada sanal ortam + paketler yüklenir (~2 dakika, ~80 MB).
Sonraki çalıştırmalar birkaç saniyede açılır.

---

## Kullanım

### Bilgisayardan test
http://localhost:8000

### Telefondan/tabletten (LAN)
1. Cihaz aynı Wi-Fi'de olmalı
2. Tarayıcıdan `http://192.168.10.66:8000` aç (NEXOR PC'nin IP'si)
3. Ana ekrana kısayol ekle — tek tıkla açılır

### Windows Firewall
İlk açılışta Windows "port 8000'i aç mı?" diye sorabilir — **İzin Ver**'i seç.
Eğer LAN'dan erişilmezse elle:
```
netsh advfirewall firewall add rule name="NEXOR Irsaliye Okuyucu" dir=in action=allow protocol=TCP localport=8000
```

---

## Akış

```
[Tablet] Fotoğraf çek
   ↓
[Claude Vision] Türkçe e-İrsaliye'yi oku → tedarikçi, tarih, no, kalemler
   ↓
[Fuzzy Match] VKN'den cari bul + her kalem için stok önerisi (top 3)
   ↓
[Tablet] Kullanıcı önizler, gerekiyorsa düzeltir, onaylar
   ↓
[DB] siparis.giris_irsaliyeleri (durum=TASLAK) + satirlar INSERT
   ↓
[NEXOR Depo Mal Kabul] Sorumlu açar → lot böler → etiket basar → ONAYLANDI
```

## Kaydedilen alanlar

### siparis.giris_irsaliyeleri
| Kolon | Değer |
|---|---|
| irsaliye_no | Otomatik: `GRS-YYYYMM-NNNN` |
| cari_unvani | Seçilen cari ünvanı (veya manuel) |
| cari_irsaliye_no | Fotoğraftan (PS12026000001281 vs.) |
| tarih | Fotoğraftan |
| arac_plaka, sofor_adi | Varsa fotoğraftan veya manuel |
| durum | **TASLAK** (NEXOR'da onaylanacak) |
| notlar | "FASON", "BEDELSİZ" gibi notlar |

### siparis.giris_irsaliye_satirlar
| Kolon | Değer |
|---|---|
| stok_kodu | Fotoğraftaki kod (20000391 vs.) |
| stok_adi | Fotoğraftaki ürün adı |
| miktar | Fotoğraftaki miktar |
| birim | ADET |
| kaplama | KTFRZ / ZNNI / BOYA / null |
| lot_no | **BOŞ** (NEXOR'da atanacak) |
| kalite_durumu | BEKLIYOR |

---

## Maliyet

- **Claude Haiku 4.5** (varsayılan, `.env`): ~$0.003 - 0.005 / fotoğraf
- **Claude Sonnet 4.6** (yüksek doğruluk): ~$0.02 / fotoğraf
- El yazılı / bozuk irsaliyelerde Sonnet'e geçmek faydalı olabilir

---

## Sorun giderme

| Belirti | Çözüm |
|---|---|
| Status "eksik: API key" | `.env`'de `ANTHROPIC_API_KEY` boş veya yanlış |
| Status "eksik: DB" | Nexor.UDL'de veya .env'de DB bilgileri yanlış |
| Parse 502 döner | Fotoğraf bozuk / boyut 10MB'dan büyük / Claude JSON dönüşü bozuk |
| Telefondan bağlanmıyor | Firewall 8000 portu + aynı Wi-Fi'de olma |
| Kaydet "Dize kesilecek" | Çok uzun ad / kod — server.py otomatik trunc ediyor, sorun olmamalı |

## Geliştirme

```
# Auto-reload ile calistir
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```
