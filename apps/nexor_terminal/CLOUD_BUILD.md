# Cloud Build (GitHub Actions) — Hizli APK

> Yerel makineye Flutter SDK kurmak yerine bulutta APK derleriz.
> 5 dk push, GitHub'da derlenir, ZIP indirip EDA51'e kurarsin.

## Bir kerelik kurulum

### 1. GitHub'da private repo ac
1. https://github.com/new
2. Owner: kendi hesabin
3. Repository name: `nexor-erp` (oneri)
4. **Private** sec
5. README, .gitignore, license: hicbiri eklenmesin (zaten var)
6. **Create repository**

### 2. Yerel repoyu GitHub'a baglayip push et

Git Bash'te:

```bash
cd /d/PROJELER/ALL/NEXOR_CORE_DATA

# Remote ekle (kendi kullanici_adin/repo_adin)
git remote add origin https://github.com/<kullanici>/nexor-erp.git

# Tum degisiklikleri stage'le
git add .

# Tum dosyalar commit olacak (M2 + Terminal API + Flutter scaffold + workflow)
git commit -m "Initial: NEXOR + Terminal API + Flutter scaffold + GitHub Actions"

# Push (master varsayilan)
git push -u origin master
```

## Her seferinde: APK uretmek

### Yontem A — Manuel tetikleme (onerilen)
1. GitHub repo > **Actions** sekmesi
2. Soldan **NEXOR Terminal APK Build**
3. **Run workflow** butonu (sag ust)
4. API URL'i kontrol et (varsayilan `http://192.168.10.66:8002`), build mode sec (release/debug)
5. **Run workflow** -> ~5-7 dk surer

### Yontem B — Otomatik (commit ile)
`apps/nexor_terminal/` altinda bir sey degistirip push edersen workflow kendiliginden tetiklenir:

```bash
git add apps/nexor_terminal
git commit -m "Terminal: ..."
git push
```

## APK indirme

1. Actions sekmesinde calisan/biten run'a tikla
2. En altta **Artifacts** bolumu
3. `nexor-terminal-release-XXXXXXX.apk` dosyasini indir (ZIP icinde)
4. ZIP'i ac, APK'yi cikar

## EDA51 cihazina kurulum

```bash
# adb varsa USB ile direkt:
adb install -r nexor-terminal-release-XXXXXXX.apk

# adb yoksa: APK'yi cihaza kopyala (USB MTP / SD kart / mail / drive)
# Cihazda dosya yoneticisinden APK'ya dokun, "Bilinmeyen kaynaklara izin ver" sor
# -> Bir kez aktif et -> Kur
```

## Sorun giderme

- **flutter create hatasi**: Workflow `--platforms=android` ile bunu otomatik yapar; manuel etkilesim gerekmez.
- **Pub get cache miss**: `subosito/flutter-action@v2` cache: true ile pubspec.lock cache'lenir.
- **Imzalama**: Su an debug keystore ile imzalanir (release build dahi). Production'da release keystore eklemek icin `android/key.properties` + `build.gradle` signingConfig duzenlenmeli; o zaman keystore.jks'yi GitHub Secrets'a base64 encode edip workflow'a ekleriz.
- **API URL degisirse**: Manuel run'da input olarak ver. Push tetikleyici varsayilan kullanir; degistirmek icin workflow yml'de `default` degerini guncelle.

## Avantajlar

- Yerel Flutter SDK / Android SDK / JDK kurulumu **GEREKMEZ**
- Bayi makinesi degissin/yeniden kuruluyor olsun farketmez
- Ekipte baska biri katilirsa ayni pipeline calisir
- Build cache'li (~3 dk eklenen build'lerde)
- Free tier: ayda 2000 dk (~285 build), limitin asilmasi olasiligi sifir
