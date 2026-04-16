# NEXOR ERP - Geliştirme El Kitabı

> **Yaşayan belge.** Her yeni modül, her tasarım kararı burada güncellenir.
> Başlangıç: 2026-04-14

---

## 0. Bu Kitap Niye Var

Her modülün kendi rengi, kendi boşluğu, kendi font boyutu vardı. Sonuç: programa her açıldığında farklı bir uygulamada çalışıyormuş hissi. Bu kitap şunu garantiler:

- **Her modül aynı hissi verir** — aynı renkler, aynı tipografi, aynı boşluklar
- **Yeni modül yazmak kolaydır** — ne kullanacağın belli, nerede ne var belli
- **Eski PC'de iyi çalışır** — her şey ekran genişliğine göre kendini ölçekler
- **Değişiklik tek yerden yapılır** — bir rengi değiştirmek isterse tek dosyayı düzelt, her yer güncellenir

---

## 1. Marka Sistemi (Brand)

**Tek otorite**: `core/nexor_brand.py`

Uygulamada **hiçbir yerde** hard-coded hex (`#DC2626`) veya px (`16`) yazma. Her zaman `brand` üzerinden git:

```python
from core.nexor_brand import brand

# Renk
color = brand.PRIMARY          # #DC2626
bg    = brand.BG_CARD          # #111113

# Spacing / font / radius (scale uygulanmış, int döner)
spacing   = brand.SP_4         # 16 * scale
font_size = brand.FS_TITLE     # 24 * scale
radius    = brand.R_LG         # 14 * scale

# Dinamik kullanım (token yoksa)
custom_sp = brand.sp(18)       # 18 * scale
custom_fs = brand.fs(22)       # 22 * scale
```

### 1.1 Renk Paleti

| Token | Hex | Kullanım |
|---|---|---|
| `BG_MAIN` | `#0F1419` | Uygulamanın en dış zemini |
| `BG_SURFACE` | `#0B0E13` | İkinci katman (sidebar) |
| `BG_CARD` | `#151B23` | Kart / panel arkaplanı |
| `BG_ELEVATED` | `#111822` | Dialog, popup |
| `BG_HOVER` | `#1C2430` | Hover state |
| `BG_INPUT` | `#232C3B` | Input arkaplanı |
| `BORDER` | `#1E2736` | Varsayılan kenarlık |
| `BORDER_HARD` | `#2A3545` | Focus / hover kenarlığı |
| `TEXT` | `#E8ECF1` | Birincil (başlık, ana içerik) |
| `TEXT_MUTED` | `#8896A6` | İkincil (label, açıklama) |
| `TEXT_DIM` | `#5C6878` | Üçüncül (caption, footer) |
| `PRIMARY` | `#C41E1E` | Nexor kırmızısı — CTA, aksiyon |
| `SUCCESS` | `#10B981` | Başarı, onay |
| `WARNING` | `#F59E0B` | Uyarı, bekleme |
| `ERROR` | `#EF4444` | Hata, red |
| `INFO` | `#3B82F6` | Bilgi, link |

**Kural**: Renk ÖNCE anlam sonra estetik. Yeşil = "başarılı/onay", sarı = "uyarı/bekleme", kırmızı = "hata/kritik". Sadece "güzel görünsün" diye renk kullanma. Genel UI **gri tonlarda**, renk sadece vurgu için.

### 1.2 Typography (Tipografi)

Font: **Inter** (`assets/fonts/Inter-*.ttf`), fallback: `Segoe UI`.

| Token | Referans px | Kullanım |
|---|---|---|
| `FS_CAPTION` | 11 | Footer, en küçük metin, timestamp |
| `FS_BODY_SM` | 12 | İkincil metin, form label |
| `FS_BODY` | 13 | Standart içerik, tablo hücresi |
| `FS_BODY_LG` | 15 | Vurgulu body |
| `FS_HEADING_SM` | 16 | Küçük başlık |
| `FS_HEADING` | 18 | Section başlığı |
| `FS_HEADING_LG` | 20 | Büyük section |
| `FS_TITLE` | 24 | Sayfa başlığı |
| `FS_TITLE_LG` | 28 | Büyük sayfa başlığı |
| `FS_DISPLAY` | 32 | KPI rakamı |
| `FS_DISPLAY_LG` | 40 | Çok büyük rakam |

**Hiyerarşi kuralı**: Bir sayfada en fazla 3 farklı font boyutu. `TITLE → BODY → CAPTION`. Aşırı tipografi hiyerarşisi karışıklık yaratır.

### 1.3 Spacing (4-tabanlı grid)

| Token | Referans px | Kullanım |
|---|---|---|
| `SP_1` | 4 | En sıkı (icon-text arası) |
| `SP_2` | 8 | Yakın (badge içi, küçük group) |
| `SP_3` | 12 | Kompakt (form satır) |
| `SP_4` | 16 | **Standart**: kart padding, button padding |
| `SP_5` | 20 | Rahat (card iç padding) |
| `SP_6` | 24 | Bölüm arası |
| `SP_8` | 32 | Section arası |
| `SP_10` | 40 | Sayfa kenar boşluğu |
| `SP_12` | 48 | Büyük section arası |

**Kural**: Spacing **daima grid'ten** gelir. "17px" demek yasak — 16 (SP_4) veya 20 (SP_5) seç. Grid dışı sayılar, tasarım tutarlılığını bozar.

### 1.4 Radius

| Token | Referans px | Kullanım |
|---|---|---|
| `R_SM` | 6 | Button, badge, small input |
| `R_MD` | 10 | Input, checkbox indicator |
| `R_LG` | 14 | Kart, panel |
| `R_XL` | 20 | Dialog, modal |

---

## 2. Responsive / DPI — Eski PC Uyumluluğu

Uygulama açılırken `brand.init(app)` çağrılır → ekran genişliği ölçülür → scale hesaplanır. Tüm `SP_*`, `FS_*`, `R_*` tokenları otomatik olarak bu scale ile çarpılır.

| Ekran genişliği | Scale | Örnek: FS_TITLE |
|---|---|---|
| ≥ 1920 | 1.00 | 24px |
| 1600 | 0.90 | 22px |
| 1440 | 0.85 | 20px |
| 1366 | 0.80 | 19px |
| 1280 | 0.75 | 18px |
| < 1280 | 0.70 | 17px |

**Hiçbir yerde sabit px kullanma** — scale devreye girmez. Her zaman `brand.SP_4` veya `brand.sp(18)`.

Debug için: `brand.scale_factor`, `brand.screen_width`.

---

## 3. Sayfa Yapısı (Kod Konvansiyonu)

Her modül sayfası `BasePage`'ten türer, `components/base_page.py`:

```python
from components.base_page import BasePage
from core.nexor_brand import brand

class UrunListesiPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10,
                                   brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # 1. Header
        layout.addLayout(self._build_header())
        # 2. İçerik
        layout.addWidget(self._build_content(), 1)
```

### 3.1 Sayfa İskeleti (zorunlu sıra)

1. **Header** — title (`FS_TITLE`) + subtitle (`TEXT_MUTED`) + sağda CTA button
2. **Filters / toolbar** (opsiyonel) — arama, tarih, combo
3. **KPI cards** (opsiyonel) — 3-4 kart, `KPICard` component
4. **Ana içerik** — tablo / form / detail panel
5. **Footer** yok — sayfa dolsun, footer yerine pagination

### 3.2 İsimlendirme

| Tip | Konvansiyon | Örnek |
|---|---|---|
| Modül dosya | `{alan}_{ekran}.py` | `modules/stok/stok_listesi.py` |
| Page sınıf | `{Alan}{Ekran}Page` | `StokListesiPage` |
| Metot | `_setup_ui`, `_load_data`, `_on_*`, `_build_*` | `_on_save_clicked` |
| Private | `_` önekle | `self._combo_cari` |
| DB bağlantı | `from core.database import get_db_connection` |  |

---

## 4. Ortak Component'ler

Her şey elden yazılmaz — mevcut component'leri kullan:

| Component | Dosya | Kullanım |
|---|---|---|
| `BasePage` | `components/base_page.py` | Tüm sayfalar bundan türer |
| `create_action_buttons()` | `components/base_page.py` | Tablo satır butonları |
| `ModernTable` (yakında) | `components/ui_kit.py` | Modern tablo |
| `KPICard` (yakında) | `components/ui_kit.py` | KPI kartı |
| `SectionHeader` (yakında) | `components/ui_kit.py` | Section başlık |
| `Badge` (yakında) | `components/ui_kit.py` | Durum badge |
| `Icon` | `components/ui_kit.py` (yakında) | Monoline icon |

**Kural**: 2 yerde aynı şeyi yazıyorsan component yap. 3 yerde aynı şey varsa component yapmayı UNUTMA.

---

## 5. İkonografi

**EMOJI YASAK** (🚀 📋 ✅ vb.). Sebep: işletim sistemine göre farklı render edilir, kurumsal görünmez.

Onun yerine:
- **QPainter monoline icons** — `components/ui_kit.py` içindeki `Icon` sınıfı (tek renk, scale-aware)
- **Assets**: `assets/icons/*.svg` (ileride eklenirse)

İkon isimleri: `box`, `truck`, `check`, `alert`, `users`, `trending-up`, `trending-down`, `search`, `settings`, `bell`, `edit`, `delete`, `plus`, `x`, `menu`, `home`, `filter`, `sort`, `calendar`, `file`, `folder`.

Yeni ikon eklemek: `Icon.paintEvent` içine bir `elif self.kind == "yeni"` bloğu ekle.

---

## 6. Database Patterns

```python
from core.database import get_db_connection

# ✅ DOGRU — with pattern yok çünkü pyodbc with desteksiz olabilir
conn = None
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ... FROM ... WHERE id = ?", (id,))
    row = cursor.fetchone()
    if not row:
        return None
    # ...
    conn.commit()
except Exception as e:
    print(f"[Module] hata: {e}")
finally:
    if conn:
        try:
            conn.close()
        except Exception:
            pass
```

**Kurallar**:
- Her zaman parametrik sorgu (`?`), asla f-string ile SQL
- UPDATE/INSERT sonrası `conn.commit()`
- `try/finally` ile kapat
- Tablo/kolon isimleri snake_case Türkçe (`cikis_irsaliyeleri`, `stok_kodu`)
- Soft delete: `silindi_mi = 1`, sorguda her zaman `ISNULL(silindi_mi, 0) = 0`
- Aktif kontrol: `aktif_mi = 1`

### 6.1 Merkezi Servisler

| Servis | Ne İçin |
|---|---|
| `core.database.get_db_connection()` | ERP DB bağlantısı |
| `core.yetki_manager.YetkiManager` | Aktif kullanıcı + yetki |
| `core.log_manager.LogManager` | Audit log |
| `core.bildirim_service.BildirimService` | Kullanıcıya bildirim gönder |
| `core.rfid_service.RFIDService` | RFID kart okuma (global) |
| `utils.email_service.get_email_service()` | Email gönder |
| `utils.whatsapp_service.get_whatsapp_service()` | WhatsApp text/document |

Dış sistemler:
- Zirve Ticari: `core.zirve_entegrasyon` — `ATLAS_KATAFOREZ_2026T` DB
- PLC: `core.plc_sync_service`
- PDKS: `core.pdks_reader_service`

---

## 7. Modül Eklerken Checklist

Yeni bir sayfa eklerken adım adım:

- [ ] `modules/{alan}/{alan}_{ekran}.py` oluştur
- [ ] `BasePage`'ten türeyen sınıf yaz (örn. `StokListesiPage`)
- [ ] `from core.nexor_brand import brand` → sabit px/hex yazma
- [ ] Header (title + subtitle + CTA) kur
- [ ] DB sorgularını parametrik yap
- [ ] `core/menu_structure.py` içine menüye ekle (ikon, label, sayfa id)
- [ ] Yetki kontrolü gerekli mi? `YetkiManager.has_permission(...)` ile kontrol
- [ ] Sayfa başlığı altında ne yaptığını anlatan bir subtitle olsun
- [ ] Aksiyon loguna yaz (`LogManager.log_insert/update/delete`)
- [ ] Test et: (a) 1920x1080, (b) 1366x768 ekran

---

## 8. Yapılan/Yapılacak İşler Günlüğü

Her büyük değişiklik buraya bir satır olarak düşer. Detay için git log.

### 2026-04-14
- ✅ `core/nexor_brand.py` — marka sistemi (token + responsive scale + font loader)
- ✅ `docs/NEXOR_GELISTIRME_EL_KITABI.md` — bu kitap
- 🔄 Login ekranı redesign (devam ediyor)
- ⏳ Ana menü / sidebar redesign
- ⏳ `components/ui_kit.py` — paylaşılan UI component library

### 2026-04-13
- ✅ `modules/sevkiyat/sevk_irsaliye.py` — FKK Mail Gönder butonu + `kalite.fkk_mail_log`
- ✅ `utils/irsaliye_pdf.py` — reportlab tabanlı Atlas Kataforez irsaliye PDF
- ✅ `modules/cari/cari_yetkililer.py` — WhatsApp ile irsaliye PDF gönderimi (`sistem.whatsapp_log`)
- ✅ `utils/whatsapp_service.py` — `gonder_dokuman()` WHAPI destekli
- ✅ `modules/uretim/uretim_durus.py` — arıza → tüm Nexor kullanıcılarına bildirim
- ✅ `modules/tanimlar/tanim_numara.py` — irsaliye sayacı Nexor fiili max ile sync
- ✅ FKK PDF dosya adı → `Fkk_{referans_kodu}_{rapor_no}.pdf`
- ✅ Mail'e tek birleşik PDF yerine her lot için ayrı PDF ek

---

## 9. Migration Notları

### 9.1 Eski kodu brand sistemine taşıma

**Önce:**
```python
layout.setContentsMargins(24, 24, 24, 24)
layout.setSpacing(20)
title.setStyleSheet("color: #E8ECF1; font-size: 24px; font-weight: 600;")
```

**Sonra:**
```python
from core.nexor_brand import brand

layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
layout.setSpacing(brand.SP_5)
title.setStyleSheet(
    f"color: {brand.TEXT}; "
    f"font-size: {brand.FS_TITLE}px; "
    f"font-weight: {brand.FW_SEMIBOLD};"
)
```

**Yaklaşım**: Tek seferde tüm modülleri geçirme. Önce en çok kullanılan 5-10 sayfa (dashboard, login, sidebar, sevkiyat, stok, kalite). Sonra yeni modüller zaten brand kullanır, eskisi zamanla gider.

---

## 10. Sık Karşılaşılan Hatalar

| Hata | Sebep | Çözüm |
|---|---|---|
| "Yazılar çok küçük, eski PC'de" | Sabit `font-size: 13px` kullanılmış | `brand.fs(13)` veya `brand.FS_BODY` |
| "Kartlar sıkışık, rakamlar kesiliyor" | Fixed height < içerik | Fixed height'i büyüt veya stretch ekle |
| "Renkler farklı görünüyor" | Inline hex kullanılmış | `brand.TEXT`, `brand.PRIMARY` vb. |
| "Tablo iç içe grid çizgili" | `setShowGrid(True)` | Modern: `setShowGrid(False)` + `border-bottom` |
| "Emoji iconlar OS'a göre farklı" | Emoji kullanılmış | `Icon` component ile monoline çiz |

---

## Ek: Hızlı Başvuru

```python
# Import
from core.nexor_brand import brand

# Renk
brand.BG_MAIN, brand.BG_CARD, brand.BORDER
brand.TEXT, brand.TEXT_MUTED, brand.TEXT_DIM
brand.PRIMARY, brand.SUCCESS, brand.WARNING, brand.ERROR, brand.INFO

# Spacing (4-grid)
brand.SP_1, SP_2, SP_3, SP_4, SP_5, SP_6, SP_8, SP_10, SP_12

# Font
brand.FS_CAPTION, FS_BODY_SM, FS_BODY, FS_BODY_LG
brand.FS_HEADING_SM, FS_HEADING, FS_HEADING_LG
brand.FS_TITLE, FS_TITLE_LG, FS_DISPLAY, FS_DISPLAY_LG
brand.FW_REGULAR, FW_MEDIUM, FW_SEMIBOLD, FW_BOLD
brand.FONT_FAMILY, FONT_MONO

# Radius
brand.R_SM, R_MD, R_LG, R_XL

# Icon boyutu
brand.ICON_XS, ICON_SM, ICON_MD, ICON_LG, ICON_XL

# Dinamik
brand.sp(px), brand.fs(px), brand.radius(px), brand.icon(px)
```
