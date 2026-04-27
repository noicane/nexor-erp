# NEXOR Terminal - Kurulum Adimlari

> Flutter SDK gerekli (3.24+). https://docs.flutter.dev/get-started/install/windows

## 1. Flutter SDK kurulumu (sadece bir kez)

```bat
:: Flutter SDK indirip C:\flutter altina aciyorsan:
setx PATH "%PATH%;C:\flutter\bin"
:: Yeni terminal acip:
flutter --version
flutter doctor
```

Android Studio kuruluyken Android SDK + emulator zaten gelir.

## 2. Bu projeyi calistirma

```bat
cd D:\PROJELER\ALL\NEXOR_CORE_DATA\apps\nexor_terminal

:: Eksik flutter dosyalarini uret (BIR KEZ; var olan dosyalarimizi ezmez)
flutter create . --project-name nexor_terminal --org com.nexor --platforms android

:: local.properties yoksa example'dan kopyala ve yollari duzenle
copy android\local.properties.example android\local.properties

:: Bagimliliklari yukle
flutter pub get

:: Cihazi bagla, USB debug acik olmali
flutter devices
```

## 3. Calistirma

```bat
:: Backend onceden calisir olmali (NEXOR ana makinede):
:: cd D:\PROJELER\ALL\NEXOR_CORE_DATA\apps\terminal_api && run.bat

flutter run -d <device_id> ^
  --dart-define=API_BASE_URL=http://192.168.10.66:8002
```

## 4. Release APK build

```bat
flutter build apk --release ^
  --dart-define=API_BASE_URL=http://192.168.10.66:8002

:: Cikti: build\app\outputs\flutter-apk\app-release.apk
:: EDA51 cihazina USB ile veya MDM uzerinden kur.
```

## 5. EDA51 Scanner Konfigurasyonu

EDA51 cihazinda **Settings > Honeywell Settings > Scanning > Internal Scanner**:
- **Wedge Method**: Intent
- **Intent Action**: `com.honeywell.scan.broadcast.data.scan`
- **Intent Category**: yok (bos)
- **Intent Extra Key (data)**: `data`
- **Mode**: Broadcast

Bunlar olmazsa scanner intent gelmez; uygulama lot input alanina kalir
(USB klavye-mode okuyucu fallback olarak yine calisir).

## 6. PIN Tanimlama (Bayide / NEXOR'da)

NEXOR'da **Sistem > Kullanicilar** > kullanici sec > **Terminal PIN** butonu.
4 veya 6 hane yazip kaydet. Cihazda kart yoksa bu PIN ile login yapilir.

## Sorun Giderme

- **flutter doctor uyarilari**: `flutter doctor --android-licenses` ile lisanslari kabul et.
- **Cihaz gozukmuyor**: `adb devices` ile teyit et. EDA51'de USB debug acik mi?
- **API'ye baglanamiyor**: aynı LAN'da mi? `http://<NEXOR_IP>:8002/health` browser'dan calismali.
- **Honeywell scanner intent gelmiyor**: Manifest'te action eklenmis mi (var), EDA51 ayarlari adim 5'teki gibi mi?
