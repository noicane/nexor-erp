# REDLINE NEXOR ERP - Modül Geliştirme Kuralları

**Versiyon:** 3.0  
**Son Güncelleme:** 27 Ocak 2026  
**Amaç:** Tüm yeni modüllerin tutarlı, modern ve bakımı kolay olmasını sağlamak

---

## 📁 Dosya Yapısı

### Dosya Başlığı (Zorunlu)
```python
# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - [Modül Adı]
[MODERNIZED UI - v3.0]

Açıklama:
- Özellik 1
- Özellik 2
"""
```

### Import Sırası
```python
# 1. Standart kütüphaneler
import os
import sys
from datetime import datetime, date, timedelta

# 2. Path ayarı (gerekirse)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 3. PySide6 imports
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

# 4. Proje imports
from components.base_page import BasePage
from core.database import get_db_connection
```

---

## 🎨 Tema Sistemi

### Zorunlu Tema Fonksiyonu
Her modülde bu fonksiyon bulunmalı:

```python
def get_modern_style(theme: dict) -> dict:
    """Modern tema renkleri - TÜM MODÜLLERDE AYNI"""
    return {
        'card_bg': theme.get('bg_card', '#1E1E1E'),
        'input_bg': theme.get('bg_input', '#1A1A1A'),
        'border': theme.get('border', '#2A2A2A'),
        'text': theme.get('text', '#FFFFFF'),
        'text_secondary': theme.get('text_secondary', '#AAAAAA'),
        'text_muted': theme.get('text_muted', '#666666'),
        'primary': theme.get('primary', '#DC2626'),      # Kırmızı - Ana renk
        'success': theme.get('success', '#10B981'),      # Yeşil - Başarı
        'warning': theme.get('warning', '#F59E0B'),      # Turuncu - Uyarı
        'error': theme.get('error', '#EF4444'),          # Kırmızı - Hata
        'info': theme.get('info', '#3B82F6'),            # Mavi - Bilgi
    }
```

### Tema Kullanımı
```python
class MyPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)  # 's' kısaltması standart
        self._setup_ui()
```

---

## 📐 Layout Standartları

### Ana Sayfa Layout
```python
def _setup_ui(self):
    s = self.s
    layout = QVBoxLayout(self)
    layout.setContentsMargins(24, 24, 24, 24)  # Sabit: 24px
    layout.setSpacing(20)                       # Sabit: 20px
    
    # 1. Header
    layout.addLayout(self._create_header())
    
    # 2. Filtreler (varsa)
    layout.addWidget(self._create_filters())
    
    # 3. Ana içerik
    layout.addWidget(self._create_content(), 1)  # stretch=1
    
    # 4. Alt bar (varsa)
    layout.addWidget(self._create_footer())
```

### Header Yapısı (Standart)
```python
def _create_header(self) -> QHBoxLayout:
    s = self.s
    header = QHBoxLayout()
    
    # Sol: Başlık
    title_section = QVBoxLayout()
    title_section.setSpacing(4)
    
    title_row = QHBoxLayout()
    icon = QLabel("📦")  # Modüle uygun emoji
    icon.setStyleSheet("font-size: 28px;")
    title_row.addWidget(icon)
    
    title = QLabel("Modül Başlığı")
    title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
    title_row.addWidget(title)
    title_row.addStretch()
    title_section.addLayout(title_row)
    
    subtitle = QLabel("Modül açıklaması")
    subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
    title_section.addWidget(subtitle)
    
    header.addLayout(title_section)
    header.addStretch()
    
    # Sağ: Butonlar
    # ... butonlar
    
    return header
```

---

## 🎯 UI Bileşen Stilleri

### Kart (Card/Frame)
```python
frame = QFrame()
frame.setStyleSheet(f"""
    QFrame {{
        background: {s['card_bg']};
        border: 1px solid {s['border']};
        border-radius: 12px;
    }}
""")
layout = QVBoxLayout(frame)
layout.setContentsMargins(20, 20, 20, 20)
layout.setSpacing(16)
```

### Vurgulu Kart (Renkli Border)
```python
frame.setStyleSheet(f"""
    QFrame {{
        background: {s['card_bg']};
        border: 2px solid {s['success']};  # veya primary, warning, error
        border-radius: 12px;
    }}
""")
```

### Input Alanları
```python
input_style = f"""
    QLineEdit, QComboBox, QDateEdit, QSpinBox {{
        background: {s['input_bg']};
        color: {s['text']};
        border: 1px solid {s['border']};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 13px;
    }}
    QLineEdit:focus, QComboBox:focus {{
        border-color: {s['primary']};
    }}
"""
```

### Butonlar

#### Primary Button (Ana Aksiyon)
```python
btn = QPushButton("💾 Kaydet")
btn.setCursor(Qt.PointingHandCursor)
btn.setStyleSheet(f"""
    QPushButton {{
        background: {s['primary']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton:hover {{ background: #B91C1C; }}
    QPushButton:disabled {{ background: {s['border']}; color: {s['text_muted']}; }}
""")
```

#### Success Button (Onay/Kaydet)
```python
btn.setStyleSheet(f"""
    QPushButton {{
        background: {s['success']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background: #059669; }}
""")
```

#### Secondary Button (İkincil)
```python
btn.setStyleSheet(f"""
    QPushButton {{
        background: {s['input_bg']};
        color: {s['text']};
        border: 1px solid {s['border']};
        border-radius: 8px;
        padding: 12px 24px;
    }}
    QPushButton:hover {{ background: {s['border']}; }}
""")
```

#### Icon Button (Küçük/Aksiyon)
```python
btn = QPushButton("✏️")
btn.setFixedSize(36, 30)
btn.setCursor(Qt.PointingHandCursor)
btn.setStyleSheet(f"""
    QPushButton {{
        background: {s['info']};
        color: white;
        border: none;
        border-radius: 6px;
    }}
    QPushButton:hover {{ background: #2563EB; }}
""")
```

### Tablo (QTableWidget)
```python
table = QTableWidget()
table.setStyleSheet(f"""
    QTableWidget {{
        background: {s['input_bg']};
        color: {s['text']};
        border: 1px solid {s['border']};
        border-radius: 10px;
        gridline-color: {s['border']};
        font-size: 13px;
    }}
    QTableWidget::item {{
        padding: 10px;
        border-bottom: 1px solid {s['border']};
    }}
    QTableWidget::item:selected {{
        background: {s['primary']};
    }}
    QTableWidget::item:hover {{
        background: rgba(220, 38, 38, 0.1);
    }}
    QHeaderView::section {{
        background: rgba(0, 0, 0, 0.3);
        color: {s['text_secondary']};
        padding: 12px 10px;
        border: none;
        border-bottom: 2px solid {s['primary']};
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
    }}
""")
table.verticalHeader().setVisible(False)
table.setSelectionBehavior(QTableWidget.SelectRows)
table.setSelectionMode(QTableWidget.SingleSelection)
table.setEditTriggers(QTableWidget.NoEditTriggers)
table.setAlternatingRowColors(False)
```

### İstatistik Kartı
```python
def _create_stat_card(self, icon: str, label: str, value: str, color: str) -> QFrame:
    s = self.s
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {s['card_bg']};
            border: 1px solid {color};
            border-radius: 10px;
        }}
    """)
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(12, 8, 12, 8)
    layout.setSpacing(10)
    
    icon_lbl = QLabel(icon)
    icon_lbl.setStyleSheet("font-size: 20px;")
    layout.addWidget(icon_lbl)
    
    text_layout = QVBoxLayout()
    text_layout.setSpacing(2)
    
    label_lbl = QLabel(label)
    label_lbl.setStyleSheet(f"color: {s['text_muted']}; font-size: 11px;")
    text_layout.addWidget(label_lbl)
    
    value_lbl = QLabel(value)
    value_lbl.setObjectName("value")  # Güncelleme için
    value_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
    text_layout.addWidget(value_lbl)
    
    layout.addLayout(text_layout)
    return frame
```

---

## 🗄️ Veritabanı Kuralları

### Bağlantı Yönetimi
```python
def _load_data(self):
    """Veri yükleme - standart pattern"""
    try:
        conn = get_db_connection()
        if not conn:
            return
        cursor = conn.cursor()
        
        # Sorgular...
        cursor.execute("SELECT ... FROM ... WHERE ...")
        rows = cursor.fetchall()
        
        # İşlemler...
        
        conn.close()  # MUTLAKA kapat
        
    except Exception as e:
        print(f"Veri yükleme hatası: {e}")
        # veya QMessageBox.critical(self, "Hata", str(e))
```

### Parametreli Sorgular (SQL Injection Koruması)
```python
# ✅ DOĞRU - Parametreli
cursor.execute("SELECT * FROM tablo WHERE id = ? AND durum = ?", (id_val, durum))

# ❌ YANLIŞ - String birleştirme
cursor.execute(f"SELECT * FROM tablo WHERE id = {id_val}")  # KULLANMA!
```

### INSERT/UPDATE Pattern
```python
def _save(self):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO schema.tablo (kolon1, kolon2, olusturma_tarihi)
            VALUES (?, ?, GETDATE())
        """, (deger1, deger2))
        
        conn.commit()  # MUTLAKA commit
        conn.close()
        
        QMessageBox.information(self, "✓ Başarılı", "Kayıt eklendi.")
        
    except Exception as e:
        QMessageBox.critical(self, "❌ Hata", f"Kayıt hatası:\n{str(e)}")
```

---

## 📋 Dialog Kuralları

### Dialog Sınıfı Yapısı
```python
class MyDialog(QDialog):
    def __init__(self, parent=None, data=None, theme: dict = None):
        super().__init__(parent)
        self.data = data
        self.theme = theme or {}
        self.s = get_modern_style(self.theme)
        
        self.setWindowTitle("📝 Dialog Başlığı")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        self._setup_ui()
        
        if data:
            self._fill_form()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{
                background: {s['card_bg']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        # Form alanları
        # Butonlar (en altta)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("✓ Kaydet")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
```

---

## 🔢 Durum Kodları ve Renkler

### Standart Durum Renkleri
```python
DURUM_RENKLERI = {
    # Bekleyen/Taslak durumlar
    'BEKLIYOR': 'warning',      # Turuncu
    'TASLAK': 'warning',
    'ONAY_BEKLIYOR': 'warning',
    
    # Devam eden durumlar
    'DEVAM_EDIYOR': 'info',     # Mavi
    'URETIMDE': 'info',
    'ISLEMDE': 'info',
    
    # Tamamlanan durumlar
    'TAMAMLANDI': 'success',    # Yeşil
    'ONAYLANDI': 'success',
    'AKTIF': 'success',
    
    # Hata/İptal durumlar
    'IPTAL': 'error',           # Kırmızı
    'HATA': 'error',
    'RED': 'error',
}

def _get_durum_color(self, durum: str) -> str:
    s = self.s
    color_key = DURUM_RENKLERI.get(durum, 'text_muted')
    return s.get(color_key, s['text_muted'])
```

### Durum Gösterimi
```python
durum_item = QTableWidgetItem(durum)
durum_item.setForeground(QColor(self._get_durum_color(durum)))
```

---

## 🔣 Emoji Kullanımı

### Modül İkonları
| Modül | Emoji |
|-------|-------|
| Depo | 📦 🏭 |
| Stok | 📊 📈 |
| İş Emri | 📋 📝 |
| Planlama | 📅 🗓️ |
| Üretim | ⚙️ 🔧 |
| Kalite | ✅ ✓ |
| Müşteri | 👤 👥 |
| Rapor | 📄 📑 |
| Ayarlar | ⚙️ 🔧 |

### Aksiyon İkonları
| Aksiyon | Emoji |
|---------|-------|
| Ekle | ➕ |
| Düzenle | ✏️ |
| Sil | 🗑️ ❌ |
| Kaydet | 💾 ✓ |
| Yenile | 🔄 |
| Ara | 🔍 |
| Filtre | 🔽 |
| Yazdır | 🖨️ |
| Export | 📤 |
| Import | 📥 |

### Durum İkonları
| Durum | Emoji |
|-------|-------|
| Başarılı | ✅ ✓ |
| Uyarı | ⚠️ |
| Hata | ❌ |
| Bilgi | ℹ️ |
| Bekliyor | 🟡 ⏳ |
| Devam | 🔵 🔄 |
| Tamamlandı | 🟢 |

---

## ⏱️ Timer ve Auto-Refresh

### Otomatik Yenileme
```python
def __init__(self, theme: dict):
    super().__init__(theme)
    # ...
    
    # Auto-refresh timer (10 saniye)
    self.refresh_timer = QTimer(self)
    self.refresh_timer.timeout.connect(self._load_data)
    self.refresh_timer.start(10000)  # 10000ms = 10sn

def closeEvent(self, event):
    """Sayfa kapanırken timer'ı durdur"""
    if hasattr(self, 'refresh_timer'):
        self.refresh_timer.stop()
    super().closeEvent(event)
```

### Gecikmeli Yükleme
```python
def __init__(self, theme: dict):
    super().__init__(theme)
    self._setup_ui()
    
    # UI hazır olduktan sonra veri yükle
    QTimer.singleShot(100, self._load_data)
```

---

## 📏 Boyut Standartları

### Sabit Değerler
```python
# Layout
MARGIN = 24          # Ana layout margin
SPACING = 20         # Ana layout spacing
CARD_SPACING = 16    # Kart içi spacing
CARD_MARGIN = 20     # Kart içi margin

# Font
TITLE_SIZE = 24      # Ana başlık
SUBTITLE_SIZE = 13   # Alt başlık
HEADER_SIZE = 16     # Bölüm başlığı
BODY_SIZE = 13       # Normal metin
SMALL_SIZE = 11      # Küçük metin

# Border Radius
CARD_RADIUS = 12     # Kartlar
INPUT_RADIUS = 8     # Input alanları
BUTTON_RADIUS = 8    # Butonlar
SMALL_RADIUS = 6     # Küçük butonlar

# Tablo
ROW_HEIGHT = 48      # Satır yüksekliği
HEADER_HEIGHT = 44   # Header yüksekliği
```

---

## ✅ Checklist - Yeni Modül

Yeni modül oluştururken kontrol edin:

- [ ] Dosya başlığı ve docstring
- [ ] `get_modern_style()` fonksiyonu
- [ ] `self.s = get_modern_style(theme)` kullanımı
- [ ] 24px margin, 20px spacing
- [ ] Header: emoji + başlık + alt başlık
- [ ] Tablo: modern stil, header border
- [ ] Butonlar: cursor, hover efekti
- [ ] Veritabanı: parametreli sorgular
- [ ] Veritabanı: try/except/finally
- [ ] Veritabanı: conn.close()
- [ ] QTimer.singleShot(100, self._load_data)
- [ ] QMessageBox: emoji + mesaj

---

## 🚫 Yapılmaması Gerekenler

1. **String birleştirme ile SQL yazma** - SQL injection riski
2. **conn.close() unutma** - Bağlantı sızıntısı
3. **Hardcoded renkler** - Tema uyumsuzluğu
4. **Layout margin/spacing'siz bırakma** - Tutarsız görünüm
5. **cursor.setPointing() unutma** - UX eksikliği
6. **try/except olmadan DB işlemi** - Crash riski
7. **QTimer olmadan _load_data çağırma** - UI donması

---

**Bu kurallar NEXOR ERP v3.0 standardıdır. Tüm yeni modüller bu kurallara uygun yazılmalıdır.**
