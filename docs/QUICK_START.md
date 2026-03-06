# 🚀 REDLINE NEXOR - Hızlı Başlangıç Rehberi

## 📦 İçerik

Bu pakette şunlar bulunmaktadır:

```
nexor_rebrand/
├── assets/              # Logo ve icon dosyaları (6 adet)
├── themes/              # Nexor tema sistemi
├── dialogs/             # Premium login ekranı
├── docs/                # Detaylı dokümantasyon
└── install_nexor.py     # Otomatik kurulum scripti
```

---

## ⚡ Hızlı Kurulum (3 Dakika)

### Yöntem 1: Otomatik Kurulum (Önerilen)

```bash
# 1. Kurulum scriptini çalıştır
python install_nexor.py

# 2. ERP projenizin yolunu girin
# Örn: /home/user/Atmo_Logic_Erp/atmo_erp_modular

# 3. 'y' ile onaylayın

# 4. Kurulum tamamlandı! Uygulamayı başlatın
cd /your/erp/path
python main.py
```

### Yöntem 2: Manuel Kurulum

```bash
# 1. Asset dosyalarını kopyala
cp nexor_rebrand/assets/* your_erp/assets/

# 2. Tema dosyasını değiştir
cp your_erp/themes.py your_erp/themes.py.backup
cp nexor_rebrand/themes/nexor_theme.py your_erp/themes.py

# 3. Login'i güncelle
cp your_erp/dialogs/login.py your_erp/dialogs/login.py.backup
cp nexor_rebrand/dialogs/nexor_login.py your_erp/dialogs/login.py

# 4. config.py'de APP_NAME'i değiştir
# "ATMO LOGIC ERP" → "Redline Nexor ERP"
```

---

## 🎨 İlk Kullanım

### 1. Uygulamayı Başlat

```bash
python main.py
```

### 2. Yeni Login Ekranını Gör

Premium tasarım:
- Redline Nexor logosu
- Modern input alanları
- Smooth animations
- Corporate dark theme

### 3. Sistem Ayarlarından Temayı Özelleştir

**Ayarlar > Sistem Ayarları > Tema**

Seçenekler:
- **Corporate Dark** (varsayılan - önerilen)
- Professional Light
- Executive Black
- Silver Edition
- Energy Orange

---

## 🎯 Öne Çıkan Özellikler

### 1. Premium Login Ekranı

✅ Tam logo entegrasyonu  
✅ Modern gradient background  
✅ Animated entrance  
✅ Professional error handling  
✅ "Remember me" & "Forgot password"  

### 2. Nexor Tema Sistemi

✅ 2 ana tema (Dark/Light)  
✅ 5 farklı renk paleti  
✅ Kurumsal kırmızı vurguları  
✅ Minimalist tasarım  
✅ Premium shadows & borders  

### 3. Kurumsal Kimlik

✅ Consistent branding  
✅ Professional typography  
✅ Redline red accents (#E2130D)  
✅ Modern UI components  

---

## 📊 Dosya Boyutları

```
Logo dosyaları:  ~373 KB
Tema dosyası:    ~15 KB
Login dosyası:   ~20 KB
Dokümantasyon:   ~25 KB
─────────────────────────
TOPLAM:          ~433 KB
```

**Performans:** Minimal etki, hızlı yükleme süreleri.

---

## 🔧 Yapılandırma

### Logo Yollarını Özelleştir

**config.py**
```python
LOGO_LOGIN = "assets/logo_login.png"
LOGO_SIDEBAR = "assets/logo_sidebar.png"
LOGO_SMALL = "assets/logo_small.png"
```

### Varsayılan Temayı Değiştir

**main.py veya themes.py**
```python
# Varsayılan renk
self.current_color = "nexor"  # nexor, executive, silver, energy, ocean

# Varsayılan mod
self.current_mode = "dark"  # dark, light
```

### Kurumsal Renkleri Özelleştir

**themes/nexor_theme.py**
```python
NEXOR_COLORS = {
    "redline_red": "#E2130D",      # Ana marka rengi
    "redline_red_dark": "#C20F0A",
    "redline_red_light": "#F5160E",
    ...
}
```

---

## ✅ Test Checklist

Kurulumdan sonra kontrol edin:

- [ ] Login ekranı yeni tasarımla açılıyor
- [ ] Logo doğru görünüyor
- [ ] Tema renkleri Redline red
- [ ] Favicon değişti
- [ ] Sidebar logosu görünüyor
- [ ] Sistem ayarlarında tema seçenekleri var

---

## 🐛 Sorun Giderme

### Logo Görünmüyor

```bash
# Logo dosyalarının varlığını kontrol et
ls -la your_erp/assets/logo_*.png

# Yoksa tekrar kopyala
cp nexor_rebrand/assets/* your_erp/assets/
```

### Tema Değişmedi

```bash
# Cache'i temizle
rm -rf your_erp/__pycache__
rm -rf your_erp/*/__pycache__

# Uygulamayı yeniden başlat
python main.py
```

### Eski Login Ekranı Görünüyor

```bash
# login.py'nin güncellendiğini kontrol et
head -5 your_erp/dialogs/login.py
# "REDLINE NEXOR" yazısını görmelisiniz

# Güncellenmemişse:
cp nexor_rebrand/dialogs/nexor_login.py your_erp/dialogs/login.py
```

### PyInstaller ile Build

```bash
# Icon'u dahil et
pyinstaller --onefile --windowed \
  --icon=assets/icon.ico \
  --add-data "assets:assets" \
  main.py
```

---

## 📚 Detaylı Dokümantasyon

Daha fazla bilgi için:

1. **REBRANDING_GUIDE.md** - Tam rebrand rehberi
2. **nexor_theme.py** - Tema sistemi kodu
3. **nexor_login.py** - Login ekranı kodu

---

## 🎓 İpuçları

### Profes yonel Görünüm İçin

1. **Corporate Dark temasını kullanın** (varsayılan)
2. **Nexor renk paletini seçin** (kırmızı)
3. **Sidebar'ı expanded modda tutun**
4. **Logo'yu sidebar'da gösterin**

### Özelleştirme

```python
# Kendi logonuzu ekleyin
# 400x267 PNG formatında
# Şeffaf arka plan önerili

# Sidebar'da göstermek için:
# Ayarlar > Sistem Ayarları > Logo Yükle
```

### Demo Modu

```python
# Test kullanıcısı oluşturun
username: demo
password: demo123

# Veya
username: admin
password: admin
```

---

## 🌟 Bonus Özellikler

### 1. Çoklu Tema Desteği

Kullanıcılar kendi tecrübelerini özelleştirebilir:
- Dark/Light mod seçimi
- 5 farklı renk paleti
- Sidebar genişlik tercihi

### 2. Premium Animasyonlar

- Login entrance animation
- Smooth transitions
- Hover effects
- Loading states

### 3. Responsive Design

- Farklı ekran boyutlarına uyum
- Minimum 1280x800 çözünürlük
- Maximized mod desteği

---

## 📞 Destek

### Teknik Sorunlar

Email: support@redlinecreative.com  
Tel: +90 XXX XXX XX XX

### Özelleştirme Talepleri

Email: custom@redlinecreative.com

### Dokümantasyon

Web: docs.redlinenexor.com  
GitHub: github.com/redline/nexor-erp

---

## 📄 Lisans

**Redline Nexor ERP**  
© 2026 Redline Creative Solutions  
Tüm hakları saklıdır.

---

## 🎉 Tebrikler!

Redline Nexor ERP sistemi kurulumunuz tamamlandı.

**Enterprise Resource Planning** çözümünüzün keyfini çıkarın!

---

**Son Güncelleme:** 26 Ocak 2026  
**Versiyon:** 1.0.0  
**Hazırlayan:** Redline Creative Solutions
