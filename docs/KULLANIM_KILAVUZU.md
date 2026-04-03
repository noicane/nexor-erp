# NEXOR ERP - Kullanım Kılavuzu

**Versiyon:** 3.1.9 (Build 54)  
**Tarih:** 2026-04-03  
**Geliştirici:** ATMO Logic / Redline Creative Solutions

---

## İçindekiler

1. [Genel Bakış](#1-genel-bakış)
2. [Sistem Gereksinimleri](#2-sistem-gereksinimleri)
3. [Kurulum ve İlk Çalıştırma](#3-kurulum-ve-ilk-çalıştırma)
4. [Giriş Ekranı](#4-giriş-ekranı)
5. [Ana Ekran ve Gezinme](#5-ana-ekran-ve-gezinme)
6. [Modüller](#6-modüller)
   - 6.1 [Dashboard](#61-dashboard)
   - 6.2 [Cariler](#62-cariler)
   - 6.3 [Stok Kartları](#63-stok-kartları)
   - 6.4 [Teklifler](#64-teklifler)
   - 6.5 [İş Emirleri](#65-iş-emirleri)
   - 6.6 [Üretim](#66-üretim)
   - 6.7 [Kalite](#67-kalite)
   - 6.8 [Laboratuvar](#68-laboratuvar)
   - 6.9 [Sevkiyat](#69-sevkiyat)
   - 6.10 [Satınalma](#610-satınalma)
   - 6.11 [Depo / Emanet](#611-depo--emanet)
   - 6.12 [İnsan Kaynakları](#612-insan-kaynakları)
   - 6.13 [Bakım](#613-bakım)
   - 6.14 [İş Sağlığı Güvenliği](#614-iş-sağlığı-güvenliği)
   - 6.15 [Çevre Yönetimi](#615-çevre-yönetimi)
   - 6.16 [Aksiyonlar](#616-aksiyonlar)
   - 6.17 [Maliyet](#617-maliyet)
   - 6.18 [Raporlar](#618-raporlar)
   - 6.19 [Tanımlar](#619-tanımlar)
   - 6.20 [Sistem](#620-sistem)
7. [Genel Kullanım İpuçları](#7-genel-kullanım-ipuçları)
8. [Kısayollar ve Pratik Bilgiler](#8-kısayollar-ve-pratik-bilgiler)
9. [Sık Sorulan Sorular](#9-sık-sorulan-sorular)

---

## 1. Genel Bakış

NEXOR ERP, yüzey işlem (kaplama) sektörüne özel geliştirilmiş kapsamlı bir kurumsal kaynak planlama yazılımıdır. Üretim takibinden kalite kontrole, insan kaynaklarından bakım yönetimine kadar tüm fabrika operasyonlarını tek bir platformda yönetmenizi sağlar.

### Temel Özellikler

- Üretim hattı canlı takibi (PLC entegrasyonu)
- Kaplama planlama ve Gantt çizelgesi
- Kalite kontrol (Giriş / Proses / Final)
- Laboratuvar banyo analiz yönetimi
- Sevkiyat ve irsaliye yönetimi (Zirve Ticari entegrasyonu)
- PDKS (Personel Devam Kontrol Sistemi) ile turnike entegrasyonu
- RFID/NFC kart okuyucu desteği
- Rol tabanlı yetkilendirme
- Karanlık tema (dark mode) arayüz
- Excel dışa aktarma ve PDF raporlama
- WhatsApp bildirim entegrasyonu

---

## 2. Sistem Gereksinimleri

| Gereksinim | Minimum |
|---|---|
| İşletim Sistemi | Windows 10 / 11 |
| Ekran Çözünürlüğü | 1280 x 800 |
| Veritabanı | SQL Server 2016+ |
| Python | 3.10+ |
| RAM | 4 GB |
| Ağ | Yerel ağ (LAN) bağlantısı |

---

## 3. Kurulum ve İlk Çalıştırma

### 3.1 İlk Kurulum

Uygulama ilk kez çalıştırıldığında **Kurulum Sihirbazı** otomatik olarak açılır. Bu sihirbazda:

1. **Veritabanı Bağlantısı** — SQL Server adresi, kullanıcı adı ve şifre bilgilerini girin
2. **Bağlantı Testi** — "Test Et" butonuyla bağlantıyı doğrulayın
3. **Kaydet** — Ayarlar `C:/NEXOR/config.json` dosyasına kaydedilir

### 3.2 Yapılandırma Dosyaları

| Dosya | Konum | Açıklama |
|---|---|---|
| config.json | `C:/NEXOR/config.json` | Veritabanı ve uygulama ayarları |
| Nexor.UDL | `C:/NEXOR/Nexor.UDL` | Alternatif veritabanı bağlantı dosyası |

### 3.3 Güncelleme

Uygulama açılışta otomatik güncelleme kontrolü yapar. Yeni sürüm varsa bildirim gösterilir ve güncelleme uygulanır.

---

## 4. Giriş Ekranı

Uygulama başlatıldığında giriş ekranı karşınıza gelir.

### 4.1 Manuel Giriş

1. **Kullanıcı Adı** alanına kullanıcı adınızı yazın
2. **Şifre** alanına şifrenizi girin
3. **Giriş** butonuna tıklayın veya `Enter` tuşuna basın

### 4.2 RFID Kart ile Giriş

Eğer sisteminize USB RFID kart okuyucu bağlıysa:
1. Kartınızı okuyucuya yaklaştırın
2. Kart numaranız otomatik olarak tanınır ve giriş yapılır

> **Not:** RFID kart numarası sistem yöneticisi tarafından kullanıcı kartınıza tanımlanmış olmalıdır.

### 4.3 Roller

Giriş yaptığınızda size atanmış role göre menülere erişim sağlarsınız. Yetkisiz menüler görünmez veya devre dışı kalır.

---

## 5. Ana Ekran ve Gezinme

### 5.1 Ekran Yapısı

Ana ekran üç ana bölümden oluşur:

```
┌──────────────────────────────────────────────┐
│                   HEADER                     │
├────────┬─────────────────────────────────────┤
│        │                                     │
│  SOL   │                                     │
│  MENÜ  │          İÇERİK ALANI               │
│        │                                     │
│        │                                     │
├────────┴─────────────────────────────────────┤
```

- **Header (Üst Bar):** Logo, kullanıcı bilgisi, global arama ve bildirimler
- **Sol Menü (Sidebar):** Modül navigasyonu — daraltılabilir/genişletilebilir
- **İçerik Alanı:** Seçilen sayfanın içeriği

### 5.2 Sol Menü Kullanımı

- Ana menü başlıklarına tıklayarak alt menüleri açın/kapatın
- Menü daraltıldığında sadece simgeler görünür (ikon moduna geçer)
- Alt menü öğelerine tıklayarak ilgili sayfaya gidin

### 5.3 Global Arama

Header'daki arama kutusunu kullanarak tüm modüller arasında hızlı arama yapabilirsiniz. Menü adı, sayfa adı veya işlev adıyla aratın.

### 5.4 Bildirimler

Header'daki bildirim ikonuna tıklayarak bekleyen bildirimleri görebilirsiniz. Bildirimler, atanan aksiyonlar, onay bekleyen talepler gibi konuları içerir.

---

## 6. Modüller

---

### 6.1 Dashboard

📊 Uygulamanın ana sayfası. Günlük üretim ve performans verilerini özetler.

**Özellikler:**
- Vardiya bazlı üretim kartları (4 vardiya)
- KPI göstergeleri
- Durum tablosu
- 10 saniyede bir otomatik yenileme

---

### 6.2 Cariler

👥 Müşteri ve tedarikçi hesaplarının yönetimi.

| Alt Sayfa | Açıklama |
|---|---|
| **Cari Listesi** | Tüm cari hesapları listeler. Arama, filtreleme ve Excel dışa aktarma |
| **Cari Detay** | Seçilen carinin detay bilgileri |
| **Cari Bakiye** | Borç/alacak bakiye takibi |
| **Cari Adresler** | Cari firmaya ait birden fazla adres tanımı |
| **Cari Yetkililer** | İlgili kişi/yetkili bilgileri |
| **Cari Spesifikasyonlar** | Müşteriye özel teknik spesifikasyonlar |

**Temel İşlemler:**
1. **Yeni Cari Ekle:** Cari Listesi sayfasında "Ekle" butonuna tıklayın
2. **Cari Ara:** Arama kutusuna firma adı veya cari kodu yazın
3. **Excel'e Aktar:** Listelerde "Excel" butonuyla dışa aktarın

---

### 6.3 Stok Kartları

📦 Ürün ve malzeme kartlarının yönetimi.

| Alt Sayfa | Açıklama |
|---|---|
| **Stok Listesi** | Tüm ürün/malzeme kartları. Detaylı filtreleme ve arama |
| **Fiyat Listesi** | Ürün fiyat tanımları ve güncelleme |
| **Maliyet Tanımları** | Ürün maliyet bileşenleri |
| **Kimyasal Tüketim** | Kimyasal malzeme tüketim takibi |
| **Ürün Rota Atama** | Ürünlere üretim rotası atama |

**Temel İşlemler:**
1. **Ürün Kartı Açma:** Stok Listesi'nde satıra çift tıklayın
2. **Rota Atama:** Ürün seçip ilgili üretim hattı rotasını tanımlayın
3. **Toplu İşlem:** Filtreleyip birden fazla ürüne aynı anda işlem uygulayın

---

### 6.4 Teklifler

📝 Müşteri tekliflerinin hazırlanması ve takibi.

| Alt Sayfa | Açıklama |
|---|---|
| **Teklif Listesi** | Tüm teklifleri listeler, durumlarını gösterir |
| **Teklif Şablonları** | Tekrar kullanılabilir teklif şablonları |

---

### 6.5 İş Emirleri

📋 Üretim iş emirlerinin oluşturulması ve takibi.

| Alt Sayfa | Açıklama |
|---|---|
| **İş Emri Listesi** | Tüm iş emirleri — durum, tarih ve öncelik filtresi |
| **Yeni İş Emri** | Yeni iş emri oluşturma formu |
| **Planlama** | İş emirlerinin üretim hattına planlanması |
| **Termin Takip** | Teslim tarihi takibi ve gecikme uyarıları |

**İş Emri Durumları:**
- `Bekliyor` — Henüz üretime alınmadı
- `Üretimde` — Üretim devam ediyor
- `Tamamlandı` — Üretim bitti
- `İptal` — İptal edildi

---

### 6.6 Üretim

🏭 Üretim operasyonlarının canlı takibi ve yönetimi.

| Alt Sayfa | Açıklama |
|---|---|
| **Üretim Girişi** | İş emri bazlı üretim giriş ve takip ekranı |
| **Hat Takip** | Kaplama hatlarının canlı durumu (PLC entegrasyonu) |
| **Rework (Söküm)** | Hatalı ürünlerin söküm/yeniden işlem kaydı |
| **Verimlilik Analizi** | OEE ve hat verimliliği analizi |
| **Duruş Kayıtları** | Planlı/plansız duruş kayıtları |
| **Vardiya Raporu** | Vardiya bazlı üretim performansı |
| **Kaplama Planlama** | Gantt çizelgesiyle kaplama planlama |
| **Bara Dashboard** | Bara bazlı üretim takip panosu |

**Hat Takip Ekranı:**
- Kazan bazlı anlık sıcaklık, akım ve reçete bilgisi
- PLC'den otomatik veri çekme (10 saniye aralık)
- Reçete analizi ve çevrim süresi hesaplama
- 3 hat tipi: KTL (Kataforez), ZNNI (Çinko-Nikel), ÖN (Ön İşlem)

**Kaplama Planlama:**
1. Ürün seçin
2. Reçete seçin (PLC'den süre otomatik gelir)
3. Askı/bara bilgilerini girin
4. "Planla" butonuyla Gantt çizelgesine ekleyin

---

### 6.7 Kalite

✅ Üç aşamalı kalite kontrol sistemi.

| Alt Sayfa | Açıklama |
|---|---|
| **Giriş Kalite** | Hammadde/malzeme giriş kalite kontrolü |
| **Proses Kalite** | Üretim sırasında proses kontrolü |
| **Final Kalite Kontrol** | Bitmiş ürün son kontrol (RFID destekli) |
| **Red Kayıtları** | Reddedilen ürün/lot kayıtları |
| **Event Log** | Kalite olayları kronolojik kaydı |
| **8D / CAPA** | 8D problem çözme ve düzeltici faaliyet |
| **PPAP** | Üretim Parçası Onay Prosesi |
| **Kalibrasyon** | Ölçüm aleti kalibrasyon takibi |
| **Kontrol Planları** | Ürün/proses kontrol planları |
| **FMEA Yönetimi** | Hata Türü ve Etkileri Analizi |
| **Polivelans Matrisi** | Personel yetkinlik matrisi |
| **Dokümantasyon** | Kalite doküman yönetimi |

**Final Kalite Kontrol Kullanımı:**
1. Sicil numaranızı girin veya RFID kartınızı okutun
2. İş emri veya lot numarasını seçin
3. Kontrol kriterlerini doldurun
4. Fotoğraf ekleyin (isteğe bağlı, 3 adede kadar)
5. Sonucu kaydedin (Kabul / Red)

**Çözünürlük Ayarı (Final Kalite):**
- Login ekranının sağ üstündeki "Aa" slider'ı ile yazı boyutunu %100 — %250 arasında ayarlayabilirsiniz
- "Uygula" butonuna tıklayarak kaydedin

---

### 6.8 Laboratuvar

🔬 Banyo analiz ve kimyasal yönetimi.

| Alt Sayfa | Açıklama |
|---|---|
| **Dashboard** | Laboratuvar özet panosu |
| **Event Log** | Laboratuvar olayları kaydı |
| **Analiz Sonuçları** | Gerçekleştirilen analizlerin sonuçları |
| **Banyo Analiz Kayıtları** | Banyo analiz giriş ekranı |
| **Banyo Kartları** | Banyo tanım kartları ve geçmişi |
| **Kimyasal Stok** | Kimyasal malzeme stok takibi |
| **Test Tanımları** | Laboratuvar test parametreleri |
| **Kaplama Test** | Kaplama kalite testleri (kalınlık, yapışma vb.) |

---

### 6.9 Sevkiyat

🚚 Ürün sevkiyat ve irsaliye yönetimi.

| Alt Sayfa | Açıklama |
|---|---|
| **Sevkiyat Listesi** | Tüm sevkiyatları listeler |
| **Yeni Sevkiyat** | Yeni sevkiyat emri oluşturma |
| **İrsaliye Yazdır** | İrsaliye oluşturma ve yazdırma |
| **İade Girişi** | Müşteriden gelen iade kayıtları |

**İrsaliye Oluşturma:**
1. Sevkiyat kaydını seçin
2. İrsaliye detaylarını kontrol edin
3. "Yazdır" butonuyla irsaliye çıktısı alın
4. Zirve Ticari'ye otomatik aktarım yapılabilir

**Zirve Ticari Entegrasyonu:**
- İrsaliye onaylandığında Zirve Ticari muhasebe yazılımına otomatik aktarılır
- Cari eşleştirmesi `zirve_cari_kodu` üzerinden yapılır

---

### 6.10 Satınalma

🛒 Satınalma süreçlerinin yönetimi.

| Alt Sayfa | Açıklama |
|---|---|
| **Satınalma Talepleri** | Departmanlardan gelen satınalma talepleri |
| **Satınalma Siparişleri** | Onaylanan taleplerin siparişe dönüştürülmesi |
| **Mal Kabul** | Gelen malzemenin kabul işlemi |
| **Tedarikçi Anlaşmaları** | Tedarikçi sözleşme ve anlaşma takibi |

**Satınalma Talep Akışı:**
1. İlgili departman talep oluşturur
2. Yetkili kişi talebi onaylar/reddeder
3. Onaylanan talep siparişe dönüştürülür
4. Malzeme geldiğinde Mal Kabul yapılır

---

### 6.11 Depo / Emanet

🏪 Depo ve emanet stok yönetimi.

| Alt Sayfa | Açıklama |
|---|---|
| **Depo Takip** | Depo giriş/çıkış hareketleri |
| **Mal Kabul** | Depoya malzeme kabul |
| **Depo Çıkış** | Depodan malzeme çıkış fişi |
| **Emanet Stoklar** | Emanet olarak alınan/verilen malzemeler |
| **Stok Sayım** | Periyodik stok sayım işlemleri |
| **Stok Takip** | Anlık stok durumu görüntüleme |

---

### 6.12 İnsan Kaynakları

🧑‍💼 Personel ve insan kaynakları yönetimi.

| Alt Sayfa | Açıklama |
|---|---|
| **Personel Listesi** | Tüm personel kartları ve bilgileri |
| **Puantaj** | Aylık puantaj tablosu |
| **İzin Yönetimi** | İzin talep, onay ve bakiye takibi |
| **Zimmet Takip** | Personele verilen zimmet malzemeleri |
| **Vardiya Planlama** | Haftalık/aylık vardiya planlaması |
| **Eğitim Takip** | Personel eğitim kayıtları |
| **PDKS Canlı Monitör** | Turnike giriş/çıkış canlı takibi |
| **Cihaz Ayarları** | PDKS cihaz (ZK turnike) yapılandırması |
| **Okuma Servisi** | PDKS okuma servisini başlat/durdur |

**PDKS Sistemi:**
- ZK marka turnike cihazlarıyla entegre çalışır
- Personel kartlarıyla giriş/çıkış kaydeder
- Canlı monitörde anlık geçişler görüntülenir
- Puantaj tablosuyla otomatik entegrasyon

**İzin Talebi:**
1. İzin Yönetimi sayfasını açın
2. "Yeni İzin Talebi" butonuna tıklayın
3. İzin türü, başlangıç/bitiş tarihi ve açıklama girin
4. Talebi gönderin — onay sürecine girer

---

### 6.13 Bakım

🔧 Bakım ve arıza yönetimi.

| Alt Sayfa | Açıklama |
|---|---|
| **Duruş Talepleri** | Üretimden gelen bakım/duruş talepleri |
| **Ekipman Kartları** | Makine ve ekipman envanteri |
| **Bakım Planları** | Periyodik bakım takvimi |
| **Arıza Kayıtları** | Arıza bildirimi ve müdahale kaydı |
| **Yedek Parça** | Yedek parça stok ve tüketim takibi |

---

### 6.14 İş Sağlığı Güvenliği

🦺 İSG süreçlerinin yönetimi.

| Alt Sayfa | Açıklama |
|---|---|
| **Risk Değerlendirme** | İş yeri risk analizi ve önlemler |
| **Olay Kayıtları** | İş kazası ve ramak kala olayları |
| **KKD Dağıtım** | Kişisel koruyucu donanım dağıtım takibi |
| **İSG Eğitimleri** | Zorunlu İSG eğitim kayıtları |
| **Sağlık Gözetimi** | Periyodik sağlık muayene takibi |
| **Saha Denetimleri** | İSG saha denetim raporları |
| **Acil Durum Ekipleri** | Acil durum ekip ve görevlendirme |
| **Tatbikatlar** | Acil durum tatbikat kayıtları |
| **Yasal Takip** | İSG yasal yükümlülük takibi |
| **GBF/MSDS** | Güvenlik Bilgi Formları yönetimi |

---

### 6.15 Çevre Yönetimi

🌿 Çevresel süreçlerin izlenmesi.

| Alt Sayfa | Açıklama |
|---|---|
| **Atık Yönetimi** | Tehlikeli/tehlikesiz atık takibi |
| **Emisyon Takibi** | Hava emisyon ölçüm sonuçları |
| **Çevresel İzinler** | Çevre izin belgeleri ve süreleri |
| **Yasal Takip** | Çevre mevzuatı uyum takibi |
| **Su/Enerji Tüketimi** | Su ve enerji tüketim takibi |
| **Atıksu Analizleri** | Atıksu deşarj analiz sonuçları |
| **Çevre Denetimleri** | İç/dış çevre denetim kayıtları |
| **Kimyasal Envanter** | Tesiste kullanılan kimyasal listesi |

---

### 6.16 Aksiyonlar

📋 Düzeltici ve önleyici faaliyet yönetimi.

| Alt Sayfa | Açıklama |
|---|---|
| **Aksiyon Dashboard** | Aksiyon durumlarının özet görünümü |
| **Aksiyon Listesi** | Tüm aksiyonların listesi ve takibi |
| **Bana Atananlar** | Giriş yapan kullanıcıya atanmış aksiyonlar |

**Aksiyon Oluşturma:**
1. "Yeni Aksiyon" butonuna tıklayın
2. Başlık, açıklama, sorumlu kişi ve termin tarihi girin
3. Öncelik seviyesini belirleyin
4. Kaydedin — sorumlu kişiye bildirim gider

---

### 6.17 Maliyet

💰 Maliyet hesaplama ve analizi.

| Alt Sayfa | Açıklama |
|---|---|
| **İş Merkezi Tanımları** | Üretim iş merkezleri ve saat maliyetleri |
| **Personel Maliyet** | Personel bazlı maliyet hesaplama |
| **Ürün Maliyet Tanımları** | Ürün maliyet bileşenleri |
| **Fiyat Listesi** | Satış fiyat listeleri |

---

### 6.18 Raporlar

📈 Raporlama ve analiz modülü.

| Alt Sayfa | Açıklama |
|---|---|
| **Üretim Raporları** | Günlük/haftalık/aylık üretim raporları |
| **Kalite Raporları** | Kalite istatistik ve trend raporları |
| **Maliyet Raporları** | Maliyet analiz raporları |
| **KPI Dashboard** | Temel performans göstergeleri panosu |
| **Ürün İzlenebilirlik** | Ürün lot bazlı izlenebilirlik geçmişi |

**Rapor Dışa Aktarma:**
- Tüm raporlar Excel formatında dışa aktarılabilir
- PDF çıktı desteği (irsaliye, izin formu, satınalma talep vb.)

---

### 6.19 Tanımlar

⚙️ Sistem genelinde kullanılan temel tanımlar.

| Alt Sayfa | Açıklama |
|---|---|
| **Üretim Hatları** | Üretim hattı tanımları |
| **Prosesler** | Üretim proses tanımları |
| **Rotalar** | Üretim rota tanımları |
| **Kaplama Tipleri** | Kaplama türü tanımları (KTL, ZNNI, ÖN vb.) |
| **Malzeme Grupları** | Malzeme grup ve sınıflandırma |
| **Depo Tanımları** | Depo lokasyon tanımları |
| **Akış Şablonları** | İş akışı şablonları |
| **Hata Türleri** | Kalite hata türü tanımları |
| **Vardiya Tanımları** | Vardiya saat ve çalışma düzeni |
| **İzin Türleri** | Yıllık izin, rapor, mazeret vb. |
| **Zimmet Türleri** | Zimmet malzeme kategorileri |
| **Organizasyon Tanımları** | Departman ve pozisyon yapısı |
| **Şoför Tanımları** | Sevkiyat şoför bilgileri |
| **Araç Tanımları** | Sevkiyat araç bilgileri |
| **Numara Tanımları** | Otomatik numara şablonları (irsaliye, iş emri vb.) |
| **Etiket Tasarım** | Ürün etiket şablon tasarımı |
| **Giriş Kalite Kriterleri** | Giriş kalite kontrol kriter tanımları |

---

### 6.20 Sistem

🛡️ Sistem yönetimi ve yapılandırma.

| Alt Sayfa | Açıklama |
|---|---|
| **Veritabanı Bağlantıları** | SQL Server bağlantı ayarları |
| **Bildirimler** | Bildirim sistemi yapılandırması |
| **Bildirim Tercihleri** | Kullanıcı bildirim tercihleri |
| **WhatsApp Bildirimleri** | WhatsApp entegrasyon ayarları |
| **Kullanıcılar** | Kullanıcı hesap yönetimi (RFID kart atama dahil) |
| **Roller** | Kullanıcı rol tanımları |
| **İzinler** | Sistem izin tanımları |
| **Rol İzinleri** | Rollere izin atama |
| **Kullanıcı Yetkileri** | Kullanıcıya özel yetki atama |
| **Firma Bilgileri** | Şirket bilgileri (logo, adres, vergi no vb.) |
| **Sistem Ayarları** | Genel uygulama ayarları |
| **İşlem Logları** | Tüm kullanıcı işlemlerinin kayıt geçmişi |
| **Yedekleme** | Veritabanı yedekleme işlemleri |

**Kullanıcı Ekleme:**
1. Kullanıcılar sayfasını açın
2. "Yeni Kullanıcı" butonuna tıklayın
3. Ad, kullanıcı adı, şifre ve rol bilgisini girin
4. RFID kart atamak için "Kart Okut" butonuna tıklayıp kartı okutun
5. Kaydedin

---

## 7. Genel Kullanım İpuçları

### Tablolarda Çalışma

- **Sıralama:** Kolon başlığına tıklayarak sıralama yapın (tekrar tıklayınca ters sıra)
- **Arama:** Tablonun üstündeki arama kutusuna yazarak filtreleyin
- **Excel:** "Excel'e Aktar" butonuyla tüm listeyi dışa aktarın
- **Detay:** Satıra çift tıklayarak detay ekranını açın
- **Yenile:** Sayfadaki yenile butonuyla güncel verileri çekin

### Tarih Seçimi

- Tarih alanlarına tıklayarak takvim açılır
- Tarih aralığı filtrelerinde "Başlangıç" ve "Bitiş" tarihlerini seçin

### Form Kaydetme

- Zorunlu alanlar işaretlidir — boş bırakılamaz
- "Kaydet" butonuna tıklayın veya `Ctrl+S` kısayolunu kullanın
- Başarılı kayıt sonrası sağ üstte yeşil bildirim görünür
- Hata durumunda kırmızı bildirim ve açıklama mesajı gösterilir

---

## 8. Kısayollar ve Pratik Bilgiler

| Kısayol | İşlev |
|---|---|
| `Enter` | Form onaylama / Giriş yapma |
| `Escape` | Dialog kapatma / İptal |
| `Ctrl+S` | Kaydetme |
| `F5` | Sayfayı yenileme |

### Etiket Yazdırma

İş emri veya ürün etiketlerini yazdırmak için:
1. İlgili kaydı seçin
2. "Etiket Yazdır" butonuna tıklayın
3. Önizleme penceresinde şablon seçin
4. Yazıcıyı seçip yazdırın

### PDF Çıktılar

Aşağıdaki belgeler PDF olarak alınabilir:
- İrsaliye
- İzin formu
- Satınalma talep formu
- İş emri depo çıkış formu
- Final kalite raporu

---

## 9. Sık Sorulan Sorular

**S: Şifremi unuttum, ne yapmalıyım?**  
C: Sistem yöneticinize başvurun. Sistem > Kullanıcılar sayfasından şifreniz sıfırlanabilir.

**S: RFID kartım okunmuyor, ne yapmalıyım?**  
C: USB kart okuyucunun bağlı olduğundan emin olun. Kartınız henüz tanımlanmamışsa sistem yöneticinizden kart tanımlama yapmasını isteyin.

**S: PDKS cihazı bağlanmıyor, ne yapmalıyım?**  
C: İK > Cihaz Ayarları sayfasından cihaz IP adresini kontrol edin. Cihazın ağda erişilebilir olduğundan emin olun (varsayılan port: 4370).

**S: Kalite ekranında yazılar çok küçük/büyük, nasıl ayarlarım?**  
C: Final Kalite Kontrol giriş ekranının sağ üstündeki "Aa" slider'ı ile yazı boyutunu %100 — %250 arasında ayarlayıp "Uygula" butonuna tıklayın.

**S: İrsaliye Zirve Ticari'ye aktarılmıyor, ne yapmalıyım?**  
C: Cari kartında `zirve_cari_kodu` alanının doğru tanımlı olduğunu kontrol edin. Entegrasyon loglarını Sistem > İşlem Logları'ndan inceleyebilirsiniz.

**S: Excel dışa aktarma çalışmıyor?**  
C: Bilgisayarınızda `openpyxl` kütüphanesinin kurulu olduğundan emin olun. Dosya kaydedileceği klasöre yazma izniniz olmalıdır.

**S: Uygulama güncellemesi nasıl yapılır?**  
C: Uygulama her açılışta otomatik güncelleme kontrolü yapar. Yeni sürüm varsa bildirim alırsınız.

---

> **NEXOR ERP v3.1.9** — ATMO Logic / Redline Creative Solutions  
> Destek ve geri bildirim için sistem yöneticinize başvurun.
