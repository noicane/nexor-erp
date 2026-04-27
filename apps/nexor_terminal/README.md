# NEXOR Terminal (Flutter)

NEXOR ERP icin Honeywell EDA51 el terminali + tablet (kalite/kamera) Android uygulamasi.

> Backend: `apps/terminal_api/` (FastAPI). Once o calisir durumda olmali.

## Kurulum

```bat
:: Flutter SDK gerekli (3.24+). Bir kere proje altinda:
cd apps\nexor_terminal
flutter pub get

:: Konfigurasyon: dart-define ile API URL
flutter run -d <device_id> --dart-define=API_BASE_URL=http://192.168.10.66:8002
```

`API_BASE_URL` verilmezse `lib/config.dart`'taki varsayilan kullanilir
(`http://192.168.10.66:8002`).

## Build (release APK)

```bat
flutter build apk --release --dart-define=API_BASE_URL=http://192.168.10.66:8002
:: Cikti: build\app\outputs\flutter-apk\app-release.apk
```

EDA51 cihazina USB veya MDM uzerinden kurulur.

## Mimari

### lib/
- `config.dart` — sabit ayarlar (API URL, renkler)
- `models/irsaliye.dart` — backend modellerine 1-1 Dart karsiliklari
- `services/api_client.dart` — Dio singleton + token interceptor + secure_storage
- `services/auth_service.dart` — kart + PIN login
- `services/sevk_service.dart` — sevkiyat endpointleri
- `services/scanner_service.dart` — Honeywell intent broadcast stream + cihaz bilgisi
- `screens/login_screen.dart` — kart girisi (otomatik focus + PIN fallback)
- `screens/sevk_liste_screen.dart` — durum=HAZIRLANDI irsaliyeler
- `screens/sevk_detay_screen.dart` — lot tarama + yukleme onay

### android/app/src/main/kotlin/com/nexor/terminal/MainActivity.kt
- `EventChannel: com.nexor.terminal/scanner` — Honeywell broadcast intent stream
- `MethodChannel: com.nexor.terminal/device` — `getDeviceInfo` (manufacturer / isHoneywell)

## EDA51 Konfigurasyonu

EDA51 ayarlarinda Scanner > Wedge'a gidin:
- Output to: **Intent**
- Action: `com.honeywell.scan.broadcast.data.scan`
- Extra: `data` (string)

Trigger tusu basildiginda barkod intent olarak gelir; uygulama her ekranda
otomatik dinler ve aktif input alanina yazar.

## Tablet Kullanimi

Honeywell olmayan cihazda intent gelmez, ama:
- USB klavye-mode kart okuyucu varsa → focus alanina yazar (mevcut akis)
- Kamera ile barkod gerekirse `mobile_scanner` plugin'i ekrana eklenebilir
  (henuz UI'a baglanmadi — son dakika)

## Akis (sevkiyat)

1. **Login** — kart oku veya kullanici/PIN
2. **Sevk Listesi** — durum=HAZIRLANDI olan irsaliyeler (arama desteği)
3. **Sevk Detay** — kalemleri ve lotlari listeler
4. Operator lot barkodunu okutur → satir OKUTULDU olur
5. Tum kalemler tamam → "Yukleme Tamam" butonu → durum=SEVK_EDILDI
6. Eksik kalem varsa zorla onayi sorulur

## Bilinen Sinirlar (MVP)

- **Online-only**: wifi olmadan calismaz (kullanici karari).
- **In-memory cache**: backend lot okutma cache'i FastAPI restart'ta silinir.
  Production icin `sevkiyat.terminal_okutma_log` tablosuna persistance eklenmeli.
- **Tek API server**: Birden cok terminal eszamanli yuklerse cache cakisabilir
  (gelistirilebilir: cache'i DB'ye al, redis vb).
- **PIN brute-force koruması yok**: backend'e basit lockout eklenmeli.
- **Kamera (mobile_scanner)** plugin'i import edildi ama UI'a baglanmadi.
