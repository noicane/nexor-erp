# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Kaplama Test Kayıtları
laboratuvar.kaplama_testleri tablosu için CRUD
Versiyon: 1.1 - Fotoğraf Desteği
"""
import os
import sys
import json
import shutil
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QDoubleSpinBox, QTextEdit, QComboBox, QDateTimeEdit,
    QTabWidget, QWidget, QGroupBox, QGridLayout, QLineEdit,
    QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QDateTime, QSize
from PySide6.QtGui import QColor, QPixmap

from components.base_page import BasePage
from core.database import get_db_connection
from datetime import datetime

# ═══════════════════════════════════════════════
# FOTOĞRAF AYARLARI - JSON Config
# ═══════════════════════════════════════════════
DESTEKLENEN_FORMATLAR = "Resim Dosyaları (*.jpg *.jpeg *.png *.bmp *.tiff *.webp)"
VARSAYILAN_FOTO_KLASORU = r"\\192.168.1.66\lab_fotolar\kaplama_test"

# Config dosya yolu: EXE yanı veya proje kökü
def _config_yolu():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "lab_kaplama_config.json")


def ayarlari_yukle() -> dict:
    """JSON config dosyasından ayarları yükle"""
    yol = _config_yolu()
    varsayilan = {"foto_klasoru": VARSAYILAN_FOTO_KLASORU}
    try:
        if os.path.exists(yol):
            with open(yol, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {**varsayilan, **data}
    except Exception as e:
        print(f"⚠️ Config yükleme hatası: {e}")
    return varsayilan


def ayarlari_kaydet(ayarlar: dict):
    """JSON config dosyasına ayarları kaydet"""
    yol = _config_yolu()
    try:
        with open(yol, "w", encoding="utf-8") as f:
            json.dump(ayarlar, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Config kaydetme hatası: {e}")
        return False


def get_foto_klasoru() -> str:
    """Geçerli fotoğraf klasörünü döner"""
    return ayarlari_yukle().get("foto_klasoru", VARSAYILAN_FOTO_KLASORU)


def foto_klasoru_kontrol():
    klasor = get_foto_klasoru()
    try:
        if not os.path.exists(klasor):
            os.makedirs(klasor, exist_ok=True)
        return True
    except Exception as e:
        print(f"⚠️ Fotoğraf klasörü oluşturulamadı: {e}")
        return False


def foto_kaydet(kaynak_yol: str, test_no: str = None) -> str:
    if not kaynak_yol or not os.path.exists(kaynak_yol):
        return None
    foto_klasoru_kontrol()
    klasor = get_foto_klasoru()
    ext = os.path.splitext(kaynak_yol)[1].lower()
    zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
    onek = test_no.replace("-", "") if test_no else "YENI"
    yeni_ad = f"{onek}_{zaman}{ext}"
    hedef = os.path.join(klasor, yeni_ad)
    try:
        shutil.copy2(kaynak_yol, hedef)
        return hedef
    except Exception as e:
        print(f"⚠️ Fotoğraf kopyalama hatası: {e}")
        return kaynak_yol


# ═══════════════════════════════════════════════
# FOTOĞRAF AYARLARI DIALOG
# ═══════════════════════════════════════════════
class FotoAyarlariDialog(QDialog):
    """Fotoğraf kayıt klasörü ayarları"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("⚙️ Fotoğraf Ayarları")
        self.setMinimumWidth(550)
        self.setStyleSheet(f"""
            QDialog {{ background: {theme['bg_main']}; }}
            QLabel {{ color: {theme['text']}; }}
            QLineEdit {{ background: {theme['bg_input']}; border: 1px solid {theme['border']};
                border-radius: 6px; padding: 8px; color: {theme['text']}; }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        t = self.theme
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("⚙️ Fotoğraf Kayıt Ayarları")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {t['text']};")
        layout.addWidget(title)

        info = QLabel("Test plakası fotoğraflarının kaydedileceği klasör yolunu belirleyin.\n"
                       "Ağ paylaşım yolu (\\\\sunucu\\klasör) veya yerel yol (C:\\...) kullanabilirsiniz.")
        info.setStyleSheet(f"color: {t['text_muted']}; font-size: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Klasör yolu
        grp = QGroupBox("📁 Fotoğraf Klasörü")
        grp.setStyleSheet(f"""
            QGroupBox {{ border: 1px solid {t['border']}; border-radius: 8px; margin-top: 10px; padding: 15px; background: {t['bg_card_solid']}; }}
            QGroupBox::title {{ color: {t['primary']}; font-weight: bold; }}
        """)
        gl = QVBoxLayout(grp)

        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(get_foto_klasoru())
        self.path_input.setPlaceholderText("Örn: \\\\192.168.1.66\\lab_fotolar\\kaplama_test")
        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton("📂 Gözat")
        browse_btn.setStyleSheet(f"background: {t['bg_input']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 8px 12px;")
        browse_btn.clicked.connect(self._gozat)
        path_layout.addWidget(browse_btn)
        gl.addLayout(path_layout)

        # Durum göstergesi
        self.durum_label = QLabel("")
        self.durum_label.setStyleSheet(f"color: {t['text_muted']}; font-size: 11px;")
        gl.addWidget(self.durum_label)

        # Test butonu
        test_btn = QPushButton("🔍 Klasörü Test Et")
        test_btn.setStyleSheet(f"background: {t['bg_input']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 8px 16px;")
        test_btn.clicked.connect(self._test_klasor)
        gl.addWidget(test_btn)

        layout.addWidget(grp)

        # Mevcut ayar bilgisi
        config_lbl = QLabel(f"📄 Config dosyası: {_config_yolu()}")
        config_lbl.setStyleSheet(f"color: {t['text_muted']}; font-size: 10px;")
        config_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(config_lbl)

        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reset_btn = QPushButton("🔄 Varsayılana Dön")
        reset_btn.setStyleSheet(f"background: {t['bg_input']}; color: {t['text']}; border: 1px solid {t['border']}; padding: 10px 16px; border-radius: 6px;")
        reset_btn.clicked.connect(self._varsayilana_don)
        btn_layout.addWidget(reset_btn)

        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"background: {t['bg_input']}; color: {t['text']}; border: 1px solid {t['border']}; padding: 10px 16px; border-radius: 6px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(f"background: {t['primary']}; color: white; border: none; padding: 10px 24px; border-radius: 6px; font-weight: bold;")
        save_btn.clicked.connect(self._kaydet)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        # İlk yüklemede test et
        self._test_klasor()

    def _gozat(self):
        klasor = QFileDialog.getExistingDirectory(self, "Fotoğraf Klasörü Seç", self.path_input.text())
        if klasor:
            self.path_input.setText(klasor)
            self._test_klasor()

    def _test_klasor(self):
        yol = self.path_input.text().strip()
        if not yol:
            self.durum_label.setText("⚠️ Klasör yolu boş olamaz")
            self.durum_label.setStyleSheet("color: #F59E0B; font-size: 11px;")
            return
        if os.path.exists(yol):
            if os.access(yol, os.W_OK):
                self.durum_label.setText("✅ Klasör erişilebilir ve yazılabilir")
                self.durum_label.setStyleSheet("color: #22C55E; font-size: 11px;")
            else:
                self.durum_label.setText("⚠️ Klasör var ama yazma izni yok!")
                self.durum_label.setStyleSheet("color: #F59E0B; font-size: 11px;")
        else:
            self.durum_label.setText("ℹ️ Klasör mevcut değil - ilk kayıtta otomatik oluşturulacak")
            self.durum_label.setStyleSheet("color: #3B82F6; font-size: 11px;")

    def _varsayilana_don(self):
        self.path_input.setText(VARSAYILAN_FOTO_KLASORU)
        self._test_klasor()

    def _kaydet(self):
        yol = self.path_input.text().strip()
        if not yol:
            QMessageBox.warning(self, "Uyarı", "Klasör yolu boş olamaz!")
            return
        ayarlar = ayarlari_yukle()
        ayarlar["foto_klasoru"] = yol
        if ayarlari_kaydet(ayarlar):
            QMessageBox.information(self, "Başarılı", f"Fotoğraf klasörü kaydedildi:\n{yol}")
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Ayarlar kaydedilemedi!")


# ═══════════════════════════════════════════════
# AI YORUM
# ═══════════════════════════════════════════════
def generate_ai_yorum(td: dict, tds_parametreler: list = None, banyo_olcumler: dict = None) -> str:
    yorumlar, sorunlar, oneriler = [], [], []
    ab = td.get('ab_orani', 0) or 0
    kal_a = td.get('kalinlik_a', 0) or 0
    kal_b = td.get('kalinlik_b', 0) or 0
    sic = td.get('sicaklik', 0) or 0
    kap = td.get('kaplama_turu', '')

    if ab > 0:
        if ab <= 1.5:
            yorumlar.append(f"✅ A/B oranı {ab:.2f} - İyi dağılım.")
        elif ab <= 2.0:
            yorumlar.append(f"⚠️ A/B oranı {ab:.2f} - Kabul edilebilir.")
            oneriler.append("Anot-katot mesafesini kontrol edin.")
        elif ab <= 3.0:
            sorunlar.append(f"🔴 A/B oranı {ab:.2f} - Homojenlik düşük!")
            oneriler.append("Anot pozisyonunu gözden geçirin.")
        else:
            sorunlar.append(f"🔴 A/B oranı {ab:.2f} - Kritik!")
            oneriler.append("Acil: Anot geometrisi ve akım yoğunluğunu gözden geçirin.")

    if kal_a > 0 and kal_b > 0:
        ort = (kal_a + kal_b) / 2
        if ort < 1.0:
            sorunlar.append(f"⚠️ Ort. kalınlık {ort:.2f}µ - Düşük!")
        else:
            yorumlar.append(f"📏 Ort. kalınlık: {ort:.2f}µ")

    for kim in td.get('kimyasallar', []):
        d, mn, mx = kim.get('deger', 0), kim.get('min'), kim.get('max')
        adi = kim.get('parametre_adi', '')
        if mn and mx:
            if d < mn:
                sorunlar.append(f"⚠️ {adi}: {d:.2f} - Min ({mn:.2f}) altında!")
                oneriler.append(f"{adi} takviyesi yapılmalı.")
            elif d > mx:
                sorunlar.append(f"⚠️ {adi}: {d:.2f} - Max ({mx:.2f}) üstünde!")
            else:
                yorumlar.append(f"✅ {adi}: {d:.2f} - Normal.")

    if sic > 0:
        if 'Nikel' in kap and sic < 40:
            sorunlar.append(f"🌡️ Sıcaklık {sic:.0f}°C - Nikel için düşük (ideal: 45-60°C)")
        elif 'Çinko' in kap and sic > 40:
            sorunlar.append(f"🌡️ Sıcaklık {sic:.0f}°C - Çinko için yüksek")

    # --- TDS Kontrol Karşılaştırması ---
    tds_sorunlar = []
    if tds_parametreler and banyo_olcumler:
        for p in tds_parametreler:
            kod = p.get("parametre_kodu", "")
            adi = p.get("parametre_adi", kod)
            tds_min = p.get("tds_min") or 0
            tds_hedef = p.get("tds_hedef") or 0
            tds_max = p.get("tds_max") or 0
            gercek = banyo_olcumler.get(kod)

            if gercek is None:
                if p.get("kritik_mi"):
                    tds_sorunlar.append(f"⚠️ {adi}: Ölçüm verisi yok (kritik parametre!)")
                continue

            gercek = float(gercek)
            if tds_min and tds_max and tds_min > 0:
                if gercek < tds_min:
                    tds_sorunlar.append(f"🔻 {adi}: {gercek:.2f} < TDS Min ({tds_min:.2f})")
                    oneriler.append(f"TDS'e göre {adi} düşük - takviye gerekli")
                elif gercek > tds_max:
                    tds_sorunlar.append(f"🔺 {adi}: {gercek:.2f} > TDS Max ({tds_max:.2f})")
                    oneriler.append(f"TDS'e göre {adi} yüksek - düzenleme gerekli")
                else:
                    yorumlar.append(f"✅ {adi}: {gercek:.2f} - TDS aralığında")
            elif tds_hedef and tds_hedef > 0:
                sapma = abs((gercek - tds_hedef) / tds_hedef * 100)
                tolerans = float(p.get("tolerans_yuzde") or 10)
                if sapma > tolerans * 2:
                    tds_sorunlar.append(f"🔴 {adi}: %{sapma:.0f} sapma (Hedef: {tds_hedef:.2f}, Gerçek: {gercek:.2f})")
                elif sapma > tolerans:
                    tds_sorunlar.append(f"⚠️ {adi}: %{sapma:.0f} sapma (Hedef: {tds_hedef:.2f})")

    r = "═══ AI Kaplama Test Değerlendirmesi ═══\n\n"
    if yorumlar: r += "📋 Değerlendirme:\n" + "\n".join(f"  {y}" for y in yorumlar) + "\n\n"
    if sorunlar: r += "⚠️ Sorunlar:\n" + "\n".join(f"  {s}" for s in sorunlar) + "\n\n"
    if tds_sorunlar:
        r += "📋 TDS Kontrol Sapmaları:\n" + "\n".join(f"  {s}" for s in tds_sorunlar) + "\n\n"
        sorunlar.extend(tds_sorunlar)
    if oneriler: r += "💡 Öneriler:\n" + "\n".join(f"  • {o}" for o in oneriler) + "\n\n"
    if not sorunlar:
        r += "🟢 Genel: UYGUN"
    elif len(sorunlar) <= 2:
        r += "🟡 Genel: DİKKAT"
    else:
        r += "🔴 Genel: KRİTİK"
    r += f"\n\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    return r


# ═══════════════════════════════════════════════
# FOTOĞRAF ÖNİZLEME DIALOG
# ═══════════════════════════════════════════════
class FotoOnizlemeDialog(QDialog):
    def __init__(self, foto_yolu: str, theme: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📷 Test Plakası Fotoğrafı")
        self.setMinimumSize(700, 550)
        self.setStyleSheet(f"QDialog {{ background: {theme['bg_main']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"border: none; background: {theme['bg_main']};")
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)
        if foto_yolu and os.path.exists(foto_yolu):
            px = QPixmap(foto_yolu)
            if not px.isNull():
                lbl.setPixmap(px.scaled(QSize(660, 500), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                lbl.setText("⚠️ Yüklenemedi")
        else:
            lbl.setText("⚠️ Dosya bulunamadı")
        lbl.setStyleSheet(f"color: {theme.get('error', '#EF4444')}; font-size: 16px;")
        scroll.setWidget(lbl)
        layout.addWidget(scroll, 1)

        yol_lbl = QLabel(foto_yolu or "—")
        yol_lbl.setStyleSheet(f"color: {theme['text_muted']}; font-size: 11px;")
        yol_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(yol_lbl)

        btn = QPushButton("Kapat")
        btn.setStyleSheet(f"background: {theme['bg_input']}; color: {theme['text']}; border: 1px solid {theme['border']}; padding: 8px 24px; border-radius: 6px;")
        btn.clicked.connect(self.close)
        layout.addWidget(btn, alignment=Qt.AlignRight)


# ═══════════════════════════════════════════════
# FOTOĞRAF SEÇİCİ WIDGET
# ═══════════════════════════════════════════════
class FotoSeciciWidget(QFrame):
    def __init__(self, theme: dict, mevcut_yol: str = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.foto_yolu = mevcut_yol
        self._kaynak_yol = None
        self._setup_ui()
        if mevcut_yol:
            self._goster_onizleme(mevcut_yol)

    def _setup_ui(self):
        t = self.theme
        self.setStyleSheet(f"QFrame {{ background: {t['bg_card_solid']}; border: 2px dashed {t['border']}; border-radius: 12px; }}")
        self.setMinimumHeight(200)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.onizleme_label = QLabel()
        self.onizleme_label.setAlignment(Qt.AlignCenter)
        self.onizleme_label.setMinimumSize(200, 120)
        self._goster_bos()
        layout.addWidget(self.onizleme_label, 1)

        self.yol_label = QLabel("—")
        self.yol_label.setStyleSheet(f"color: {t['text_muted']}; font-size: 11px; border: none;")
        self.yol_label.setWordWrap(True)
        self.yol_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.yol_label)

        btn_layout = QHBoxLayout()
        self.sec_btn = QPushButton("📁 Fotoğraf Seç")
        self.sec_btn.setStyleSheet(f"QPushButton {{ background: {t['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }} QPushButton:hover {{ background: #B91C1C; }}")
        self.sec_btn.clicked.connect(self._dosya_sec)
        btn_layout.addWidget(self.sec_btn)

        self.goruntule_btn = QPushButton("🔍 Büyüt")
        self.goruntule_btn.setStyleSheet(f"QPushButton {{ background: {t['bg_input']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 8px 16px; }} QPushButton:hover {{ background: {t['border']}; }}")
        self.goruntule_btn.clicked.connect(self._buyut)
        self.goruntule_btn.setEnabled(False)
        btn_layout.addWidget(self.goruntule_btn)

        self.kaldir_btn = QPushButton("🗑️ Kaldır")
        self.kaldir_btn.setStyleSheet(f"QPushButton {{ background: {t['bg_input']}; color: #EF4444; border: 1px solid {t['border']}; border-radius: 6px; padding: 8px 16px; }} QPushButton:hover {{ background: #FEE2E2; }}")
        self.kaldir_btn.clicked.connect(self._kaldir)
        self.kaldir_btn.setEnabled(False)
        btn_layout.addWidget(self.kaldir_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _goster_bos(self):
        self.onizleme_label.setText("📷\nFotoğraf seçilmedi\nDosya seç butonunu kullanın")
        self.onizleme_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 14px; border: none; padding: 20px;")
        self.onizleme_label.setCursor(Qt.PointingHandCursor)
        self.onizleme_label.mousePressEvent = lambda e: self._dosya_sec()

    def _goster_onizleme(self, yol: str):
        if not yol or not os.path.exists(yol):
            self._goster_bos()
            return
        px = QPixmap(yol)
        if px.isNull():
            self.onizleme_label.setText("⚠️ Yüklenemedi")
            return
        self.onizleme_label.setPixmap(px.scaled(QSize(380, 280), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.onizleme_label.setStyleSheet("border: none;")
        self.onizleme_label.setCursor(Qt.PointingHandCursor)
        self.onizleme_label.mousePressEvent = lambda e: self._buyut()
        self.yol_label.setText(yol)
        self.goruntule_btn.setEnabled(True)
        self.kaldir_btn.setEnabled(True)

    def _dosya_sec(self):
        dosya, _ = QFileDialog.getOpenFileName(self, "Test Plakası Fotoğrafı Seç", "", DESTEKLENEN_FORMATLAR)
        if dosya:
            self._kaynak_yol = dosya
            self.foto_yolu = dosya
            self._goster_onizleme(dosya)

    def _buyut(self):
        if self.foto_yolu and os.path.exists(self.foto_yolu):
            FotoOnizlemeDialog(self.foto_yolu, self.theme, self).exec()

    def _kaldir(self):
        self.foto_yolu = None
        self._kaynak_yol = None
        self._goster_bos()
        self.yol_label.setText("—")
        self.goruntule_btn.setEnabled(False)
        self.kaldir_btn.setEnabled(False)

    def get_foto_yolu(self): return self.foto_yolu
    def get_kaynak_yol(self): return self._kaynak_yol


# ═══════════════════════════════════════════════
# KAPLAMA TEST DİALOG
# ═══════════════════════════════════════════════
class KaplamaTestDialog(QDialog):
    def __init__(self, theme: dict, test_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.test_id = test_id
        self.data = {}
        self.kimyasal_inputs = []
        self.kimyasal_params = []
        self.tds_parametreler = []
        self.tds_banyo_olcumler = {}
        self.setWindowTitle("Yeni Kaplama Testi" if not test_id else "Kaplama Testi Düzenle")
        self.setMinimumSize(850, 750)
        if test_id:
            self._load_data()
        self._setup_ui()

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM laboratuvar.kaplama_testleri WHERE id = ?", (self.test_id,))
            row = cur.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cur.description], row))
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _setup_ui(self):
        t = self.theme
        self.setStyleSheet(f"""
            QDialog {{ background: {t['bg_main']}; }}
            QLabel {{ color: {t['text']}; }}
            QLineEdit, QTextEdit, QDoubleSpinBox, QComboBox, QDateTimeEdit {{
                background: {t['bg_input']}; border: 1px solid {t['border']};
                border-radius: 6px; padding: 8px; color: {t['text']};
            }}
            QTabWidget::pane {{ border: 1px solid {t['border']}; background: {t['bg_card_solid']}; border-radius: 8px; }}
            QTabBar::tab {{ background: {t['bg_input']}; padding: 10px 18px; color: {t['text']}; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
            QTabBar::tab:selected {{ background: {t['bg_card_solid']}; border-bottom: 3px solid {t['primary']}; }}
            QGroupBox {{ border: 1px solid {t['border']}; border-radius: 8px; margin-top: 10px; padding: 15px; background: {t['bg_card_solid']}; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: {t['primary']}; font-weight: bold; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("🔬 " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {t['text']};")
        layout.addWidget(title)

        # Temel bilgiler
        grp = QGroupBox("📋 Temel Bilgiler")
        frm = QFormLayout(grp); frm.setSpacing(10)

        self.banyo_combo = QComboBox()
        self.banyo_combo.addItem("-- Banyo Seçiniz --", None)
        self._load_banyolar()
        self.banyo_combo.currentIndexChanged.connect(self._on_banyo_changed)
        frm.addRow("Banyo *:", self.banyo_combo)

        self.kaplama_turu_combo = QComboBox()
        self.kaplama_turu_combo.addItem("-- Kaplama Türü --", None)
        self._load_kaplama_turleri()
        self.kaplama_turu_combo.currentIndexChanged.connect(self._load_kimyasal_parametreler)
        frm.addRow("Kaplama Türü *:", self.kaplama_turu_combo)

        self.tarih_input = QDateTimeEdit()
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.tarih_input.setDateTime(QDateTime(self.data['test_tarihi']) if self.data.get('test_tarihi') else QDateTime.currentDateTime())
        frm.addRow("Test Tarihi *:", self.tarih_input)

        self.analist_combo = QComboBox()
        self.analist_combo.addItem("-- Analist --", None)
        self._load_analistler()
        frm.addRow("Analist *:", self.analist_combo)

        layout.addWidget(grp)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._tab_proses(), "⚡ Proses")
        tabs.addTab(self._tab_kimyasal(), "🧪 Kimyasal")
        tabs.addTab(self._tab_kalinlik(), "📏 Kalınlık")
        tabs.addTab(self._tab_tds_kontrol(), "📋 TDS Kontrol")
        tabs.addTab(self._tab_foto(), "📷 Fotoğraf")
        tabs.addTab(self._tab_sonuc(), "📝 Sonuç")
        layout.addWidget(tabs, 1)

        # Butonlar
        bl = QHBoxLayout(); bl.addStretch()

        cb = QPushButton("İptal")
        cb.clicked.connect(self.reject)
        cb.setStyleSheet(f"background: {t['bg_input']}; color: {t['text']}; border: 1px solid {t['border']}; padding: 10px 20px; border-radius: 6px;")
        bl.addWidget(cb)

        ab = QPushButton("🤖 AI Değerlendir")
        ab.setStyleSheet("background: #7C3AED; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
        ab.clicked.connect(self._ai_degerlendirme)
        bl.addWidget(ab)

        sb = QPushButton("💾 Kaydet")
        sb.setStyleSheet(f"background: {t['primary']}; color: white; border: none; padding: 10px 30px; border-radius: 6px; font-weight: bold;")
        sb.clicked.connect(self._save)
        bl.addWidget(sb)
        layout.addLayout(bl)

    def _tab_proses(self):
        w = QWidget(); lo = QVBoxLayout(w); lo.setContentsMargins(15, 15, 15, 15)
        g = QGroupBox("⚡ Elektroliz Parametreleri"); gl = QGridLayout(g); gl.setSpacing(12)
        gl.addWidget(QLabel("Akım (A):"), 0, 0)
        self.amper_input = QDoubleSpinBox(); self.amper_input.setRange(0, 9999); self.amper_input.setDecimals(2); self.amper_input.setSuffix(" A"); self.amper_input.setValue(self.data.get('amper', 0) or 0)
        gl.addWidget(self.amper_input, 0, 1)
        gl.addWidget(QLabel("Voltaj (V):"), 0, 2)
        self.volt_input = QDoubleSpinBox(); self.volt_input.setRange(0, 9999); self.volt_input.setDecimals(2); self.volt_input.setSuffix(" V"); self.volt_input.setValue(self.data.get('volt', 0) or 0)
        gl.addWidget(self.volt_input, 0, 3)
        gl.addWidget(QLabel("Süre (dk):"), 1, 0)
        self.sure_input = QDoubleSpinBox(); self.sure_input.setRange(0, 9999); self.sure_input.setDecimals(1); self.sure_input.setSuffix(" dk"); self.sure_input.setValue(self.data.get('sure_dk', 0) or 0)
        gl.addWidget(self.sure_input, 1, 1)
        gl.addWidget(QLabel("Sıcaklık (°C):"), 1, 2)
        self.sicaklik_input = QDoubleSpinBox(); self.sicaklik_input.setRange(-10, 200); self.sicaklik_input.setDecimals(1); self.sicaklik_input.setSuffix(" °C"); self.sicaklik_input.setValue(self.data.get('sicaklik', 0) or 0)
        gl.addWidget(self.sicaklik_input, 1, 3)
        lo.addWidget(g)
        lo.addStretch()
        return w

    def _tab_kimyasal(self):
        w = QWidget()
        self.kimyasal_layout = QVBoxLayout(w); self.kimyasal_layout.setContentsMargins(15, 15, 15, 15)
        self.kimyasal_container = QVBoxLayout()
        self.kimyasal_layout.addLayout(self.kimyasal_container)
        lbl = QLabel("ℹ️ Kaplama türü seçildiğinde kimyasal parametreler burada görünecektir.")
        lbl.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 13px; padding: 20px;")
        lbl.setAlignment(Qt.AlignCenter)
        self.kimyasal_container.addWidget(lbl)
        self.kimyasal_layout.addStretch()
        return w

    def _tab_kalinlik(self):
        w = QWidget(); lo = QVBoxLayout(w); lo.setContentsMargins(15, 15, 15, 15)
        hl = QHBoxLayout(); hl.setSpacing(20)

        ag = QGroupBox("📍 Nokta A"); af = QFormLayout(ag); af.setSpacing(10)
        self.kalinlik_a_input = QDoubleSpinBox(); self.kalinlik_a_input.setRange(0, 9999); self.kalinlik_a_input.setDecimals(4); self.kalinlik_a_input.setSuffix(" µ"); self.kalinlik_a_input.setValue(self.data.get('kalinlik_a', 0) or 0)
        self.kalinlik_a_input.valueChanged.connect(self._hesapla_ab)
        af.addRow("Kalınlık:", self.kalinlik_a_input)
        self.sapma_a_input = QDoubleSpinBox(); self.sapma_a_input.setRange(-100, 100); self.sapma_a_input.setDecimals(2); self.sapma_a_input.setSuffix(" %"); self.sapma_a_input.setValue(self.data.get('sapma_a', 0) or 0)
        af.addRow("Sapma:", self.sapma_a_input)
        hl.addWidget(ag)

        bg = QGroupBox("📍 Nokta B"); bf = QFormLayout(bg); bf.setSpacing(10)
        self.kalinlik_b_input = QDoubleSpinBox(); self.kalinlik_b_input.setRange(0, 9999); self.kalinlik_b_input.setDecimals(4); self.kalinlik_b_input.setSuffix(" µ"); self.kalinlik_b_input.setValue(self.data.get('kalinlik_b', 0) or 0)
        self.kalinlik_b_input.valueChanged.connect(self._hesapla_ab)
        bf.addRow("Kalınlık:", self.kalinlik_b_input)
        self.sapma_b_input = QDoubleSpinBox(); self.sapma_b_input.setRange(-100, 100); self.sapma_b_input.setDecimals(2); self.sapma_b_input.setSuffix(" %"); self.sapma_b_input.setValue(self.data.get('sapma_b', 0) or 0)
        bf.addRow("Sapma:", self.sapma_b_input)
        hl.addWidget(bg)
        lo.addLayout(hl)

        # A/B Oranı
        of = QFrame()
        of.setStyleSheet(f"QFrame {{ background: {self.theme['bg_card_solid']}; border: 2px solid {self.theme['border']}; border-radius: 12px; padding: 20px; }}")
        ol = QVBoxLayout(of)
        ot = QLabel("A / B Oranı"); ot.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 14px;"); ot.setAlignment(Qt.AlignCenter); ol.addWidget(ot)
        self.ab_oran_label = QLabel("-"); self.ab_oran_label.setStyleSheet(f"color: {self.theme['text']}; font-size: 48px; font-weight: bold;"); self.ab_oran_label.setAlignment(Qt.AlignCenter); ol.addWidget(self.ab_oran_label)
        self.ab_durum_label = QLabel(""); self.ab_durum_label.setAlignment(Qt.AlignCenter); ol.addWidget(self.ab_durum_label)
        lo.addWidget(of)

        if self.data.get('kalinlik_a') and self.data.get('kalinlik_b'):
            self._hesapla_ab()
        lo.addStretch()
        return w

    def _tab_foto(self):
        w = QWidget(); lo = QVBoxLayout(w); lo.setContentsMargins(15, 15, 15, 15)

        # Başlık + Ayarlar butonu
        header = QHBoxLayout()
        t_lbl = QLabel("📷 Test Plakası Fotoğrafı"); t_lbl.setStyleSheet(f"color: {self.theme['text']}; font-size: 16px; font-weight: 600;")
        header.addWidget(t_lbl)
        header.addStretch()
        ayar_btn = QPushButton("⚙️ Klasör Ayarları")
        ayar_btn.setStyleSheet(f"background: {self.theme['bg_input']}; color: {self.theme['text']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 6px 12px; font-size: 12px;")
        ayar_btn.clicked.connect(self._foto_ayarlari)
        header.addWidget(ayar_btn)
        lo.addLayout(header)

        i = QLabel("💡 Test plakasının fotoğrafını seçin. Fotoğraf belirlenen klasöre kopyalanacaktır."); i.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 12px;"); lo.addWidget(i)
        self.foto_widget = FotoSeciciWidget(self.theme, mevcut_yol=self.data.get('foto_yolu'))
        lo.addWidget(self.foto_widget, 1)
        self.foto_klasor_label = QLabel(f"📁 Kayıt klasörü: {get_foto_klasoru()}")
        self.foto_klasor_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 10px;")
        self.foto_klasor_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lo.addWidget(self.foto_klasor_label)
        return w

    def _foto_ayarlari(self):
        """Fotoğraf klasör ayarları dialogunu aç"""
        dlg = FotoAyarlariDialog(self.theme, self)
        if dlg.exec() == QDialog.Accepted:
            self.foto_klasor_label.setText(f"📁 Kayıt klasörü: {get_foto_klasoru()}")

    def _tab_sonuc(self):
        w = QWidget(); lo = QVBoxLayout(w); lo.setContentsMargins(15, 15, 15, 15)

        sg = QGroupBox("🏁 Sonuç"); sf = QFormLayout(sg)
        self.sonuc_combo = QComboBox()
        self.sonuc_combo.addItem("⏳ Beklemede", "BEKLEMEDE")
        self.sonuc_combo.addItem("✅ Uygun", "UYGUN")
        self.sonuc_combo.addItem("❌ Uygun Değil", "UYGUN_DEGIL")
        idx = self.sonuc_combo.findData(self.data.get('sonuc', 'BEKLEMEDE'))
        if idx >= 0: self.sonuc_combo.setCurrentIndex(idx)
        sf.addRow("Sonuç:", self.sonuc_combo)
        lo.addWidget(sg)

        ng = QGroupBox("📝 Notlar"); nl = QVBoxLayout(ng)
        self.notlar_input = QTextEdit(); self.notlar_input.setPlaceholderText("Test ile ilgili notlar...")
        self.notlar_input.setText(self.data.get('notlar', '') or ''); self.notlar_input.setMaximumHeight(100)
        nl.addWidget(self.notlar_input); lo.addWidget(ng)

        aig = QGroupBox("🤖 AI Değerlendirmesi"); ail = QVBoxLayout(aig)
        self.ai_yorum_text = QTextEdit(); self.ai_yorum_text.setReadOnly(True)
        self.ai_yorum_text.setText(self.data.get('ai_yorum', '') or '')
        self.ai_yorum_text.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 10px; color: {self.theme['text']}; font-family: Consolas; font-size: 12px;")
        ail.addWidget(self.ai_yorum_text); lo.addWidget(aig, 1)
        return w

    # ─── TDS Kontrol Noktaları ───
    def _tab_tds_kontrol(self):
        w = QWidget()
        lo = QVBoxLayout(w); lo.setContentsMargins(15, 15, 15, 15); lo.setSpacing(10)

        # Ust bilgi
        info_bar = QHBoxLayout()
        self.tds_info_label = QLabel("Banyo seciniz - TDS kontrol noktalari otomatik yuklenecek")
        self.tds_info_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 13px;")
        info_bar.addWidget(self.tds_info_label)
        info_bar.addStretch()

        self.tds_kontrol_btn = QPushButton("Kontrol Et")
        self.tds_kontrol_btn.setStyleSheet(
            f"background: {self.theme['primary']}; color: white; border: none; "
            f"padding: 6px 14px; border-radius: 4px; font-weight: bold;")
        self.tds_kontrol_btn.clicked.connect(self._run_tds_kontrol)
        self.tds_kontrol_btn.setEnabled(False)
        info_bar.addWidget(self.tds_kontrol_btn)
        lo.addLayout(info_bar)

        # Genel durum gostergesi
        self.tds_durum_frame = QFrame()
        self.tds_durum_frame.setStyleSheet(
            f"QFrame {{ background: {self.theme['bg_card_solid']}; "
            f"border: 1px solid {self.theme['border']}; border-radius: 8px; padding: 10px; }}")
        durum_lo = QHBoxLayout(self.tds_durum_frame)
        self.tds_durum_label = QLabel("Henuz kontrol yapilmadi")
        self.tds_durum_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 14px; font-weight: bold;")
        durum_lo.addWidget(self.tds_durum_label)
        durum_lo.addStretch()
        self.tds_sorun_label = QLabel("")
        self.tds_sorun_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 12px;")
        durum_lo.addWidget(self.tds_sorun_label)
        lo.addWidget(self.tds_durum_frame)

        # Kontrol noktalari tablosu
        grp = QGroupBox("Kontrol Noktalari")
        grp.setStyleSheet(f"""
            QGroupBox {{ border: 1px solid {self.theme['border']}; border-radius: 8px;
                margin-top: 10px; padding: 15px; background: {self.theme['bg_card_solid']}; }}
            QGroupBox::title {{ subcontrol-origin: margin; padding: 0 5px;
                color: {self.theme['primary']}; font-weight: bold; }}
        """)
        g_lo = QVBoxLayout(grp)
        self.tds_kontrol_table = QTableWidget()
        self.tds_kontrol_table.setColumnCount(7)
        self.tds_kontrol_table.setHorizontalHeaderLabels([
            "Parametre", "Birim", "TDS Min", "TDS Hedef", "TDS Max", "Gercek", "Durum"])
        self.tds_kontrol_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tds_kontrol_table.setColumnWidth(1, 60)
        self.tds_kontrol_table.setColumnWidth(2, 75)
        self.tds_kontrol_table.setColumnWidth(3, 75)
        self.tds_kontrol_table.setColumnWidth(4, 75)
        self.tds_kontrol_table.setColumnWidth(5, 85)
        self.tds_kontrol_table.setColumnWidth(6, 90)
        self.tds_kontrol_table.verticalHeader().setVisible(False)
        self.tds_kontrol_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.tds_kontrol_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        g_lo.addWidget(self.tds_kontrol_table)
        lo.addWidget(grp, 1)

        # Sorun ve oneriler
        alt_lo = QHBoxLayout()
        sorun_grp = QGroupBox("Sorunlar")
        sorun_grp.setStyleSheet(grp.styleSheet())
        s_lo = QVBoxLayout(sorun_grp)
        self.tds_sorunlar_text = QTextEdit()
        self.tds_sorunlar_text.setReadOnly(True)
        self.tds_sorunlar_text.setMaximumHeight(120)
        self.tds_sorunlar_text.setStyleSheet(
            f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; "
            f"border-radius: 6px; color: {self.theme['text']}; font-size: 12px;")
        s_lo.addWidget(self.tds_sorunlar_text)
        alt_lo.addWidget(sorun_grp)

        oneri_grp = QGroupBox("Oneriler")
        oneri_grp.setStyleSheet(grp.styleSheet())
        o_lo = QVBoxLayout(oneri_grp)
        self.tds_oneriler_text = QTextEdit()
        self.tds_oneriler_text.setReadOnly(True)
        self.tds_oneriler_text.setMaximumHeight(120)
        self.tds_oneriler_text.setStyleSheet(
            f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; "
            f"border-radius: 6px; color: {self.theme['text']}; font-size: 12px;")
        o_lo.addWidget(self.tds_oneriler_text)
        alt_lo.addWidget(oneri_grp)
        lo.addLayout(alt_lo)

        return w

    def _on_banyo_changed(self):
        """Banyo secimi degistiginde TDS parametrelerini yukle"""
        banyo_id = self.banyo_combo.currentData()
        self.tds_parametreler = []
        self.tds_banyo_olcumler = {}

        if not banyo_id:
            self.tds_info_label.setText("Banyo seciniz - TDS kontrol noktalari otomatik yuklenecek")
            self.tds_kontrol_btn.setEnabled(False)
            self.tds_kontrol_table.setRowCount(0)
            return

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Aktif TDS bul
            cur.execute("""
                SELECT TOP 1 t.id, t.tds_kodu, t.tds_adi, t.tedarikci
                FROM uretim.banyo_tds t
                WHERE t.banyo_id = ? AND t.aktif_mi = 1
                ORDER BY t.olusturma_tarihi DESC
            """, (banyo_id,))
            tds_row = cur.fetchone()

            if not tds_row:
                self.tds_info_label.setText("Bu banyo icin TDS tanimi bulunamadi")
                self.tds_kontrol_btn.setEnabled(False)
                # TDS yok ise tabloya banyo parametrelerinden yukle
                self._load_banyo_params_as_kontrol(banyo_id, cur)
                return

            tds_id = tds_row[0]
            tds_bilgi = f"TDS: {tds_row[1]} - {tds_row[2]}"
            if tds_row[3]:
                tds_bilgi += f" [{tds_row[3]}]"
            self.tds_info_label.setText(tds_bilgi)
            self.tds_info_label.setStyleSheet(
                f"color: {self.theme.get('success', '#10B981')}; font-size: 13px; font-weight: bold;")

            # TDS parametrelerini yukle
            cur.execute("""
                SELECT parametre_kodu, parametre_adi, birim,
                       tds_min, tds_hedef, tds_max, tolerans_yuzde, kritik_mi
                FROM uretim.banyo_tds_parametreler
                WHERE tds_id = ?
                ORDER BY sira_no
            """, (tds_id,))
            for r in cur.fetchall():
                self.tds_parametreler.append({
                    "parametre_kodu": r[0], "parametre_adi": r[1], "birim": r[2],
                    "tds_min": float(r[3]) if r[3] else None,
                    "tds_hedef": float(r[4]) if r[4] else None,
                    "tds_max": float(r[5]) if r[5] else None,
                    "tolerans_yuzde": float(r[6]) if r[6] else 10.0,
                    "kritik_mi": bool(r[7]),
                })

            # Son banyo analiz olcumlerini al
            cur.execute("""
                SELECT TOP 1 sicaklik, ph, iletkenlik, kati_madde, pb_orani,
                       solvent, meq, toplam_asitlik, serbest_asitlik
                FROM uretim.banyo_analiz_sonuclari
                WHERE banyo_id = ?
                ORDER BY tarih DESC
            """, (banyo_id,))
            row = cur.fetchone()
            if row:
                col_map = {"sicaklik": 0, "ph": 1, "iletkenlik": 2, "kati_madde": 3,
                           "pb_orani": 4, "solvent": 5, "meq": 6,
                           "toplam_asit": 7, "serbest_asit": 8}
                for kod, idx in col_map.items():
                    if row[idx] is not None:
                        self.tds_banyo_olcumler[kod] = float(row[idx])

            self.tds_kontrol_btn.setEnabled(True)

            # Tabloya TDS parametrelerini goster (henuz kontrol yapilmadan)
            self._fill_tds_kontrol_table_initial()

        except Exception as e:
            self.tds_info_label.setText(f"TDS yuklenemedi: {e}")
            print(f"TDS yukleme hatasi: {e}")
        finally:
            if conn:
                try: conn.close()
                except: pass

    def _load_banyo_params_as_kontrol(self, banyo_id, cursor):
        """TDS tanimi yoksa banyo parametrelerinden kontrol listesi olustur"""
        try:
            cursor.execute("""
                SELECT sicaklik_min, sicaklik_hedef, sicaklik_max,
                       ph_min, ph_hedef, ph_max,
                       iletkenlik_min, iletkenlik_hedef, iletkenlik_max,
                       kati_madde_min, kati_madde_hedef, kati_madde_max,
                       pb_orani_min, pb_orani_hedef, pb_orani_max,
                       solvent_min, solvent_hedef, solvent_max,
                       meq_min, meq_hedef, meq_max,
                       toplam_asit_min, toplam_asit_hedef, toplam_asit_max,
                       serbest_asit_min, serbest_asit_hedef, serbest_asit_max
                FROM uretim.banyo_tanimlari WHERE id = ?
            """, (banyo_id,))
            row = cursor.fetchone()
            if not row:
                return

            param_listesi = [
                ("sicaklik", "Sicaklik", "°C", 0, 1, 2),
                ("ph", "pH", "", 3, 4, 5),
                ("iletkenlik", "Iletkenlik", "mS/cm", 6, 7, 8),
                ("kati_madde", "Kati Madde", "%", 9, 10, 11),
                ("pb_orani", "P/B Orani", "", 12, 13, 14),
                ("solvent", "Solvent", "%", 15, 16, 17),
                ("meq", "MEQ", "meq/100g", 18, 19, 20),
                ("toplam_asit", "Toplam Asit", "ml", 21, 22, 23),
                ("serbest_asit", "Serbest Asit", "ml", 24, 25, 26),
            ]

            self.tds_parametreler = []
            for kod, adi, birim, mi, hi, mx in param_listesi:
                if row[hi] is not None and row[hi] != 0:
                    self.tds_parametreler.append({
                        "parametre_kodu": kod, "parametre_adi": adi, "birim": birim,
                        "tds_min": float(row[mi]) if row[mi] else None,
                        "tds_hedef": float(row[hi]) if row[hi] else None,
                        "tds_max": float(row[mx]) if row[mx] else None,
                        "tolerans_yuzde": 10.0, "kritik_mi": False,
                    })

            if self.tds_parametreler:
                self.tds_info_label.setText("TDS yok - Banyo tanimindan parametreler yuklendi")
                self.tds_info_label.setStyleSheet(f"color: {self.theme.get('warning', '#F59E0B')}; font-size: 13px;")
                self.tds_kontrol_btn.setEnabled(True)
                self._fill_tds_kontrol_table_initial()

        except Exception as e:
            print(f"Banyo parametreleri yuklenemedi: {e}")

    def _make_readonly_item(self, text):
        """Salt okunur tablo hucre ogesi olustur"""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def _fill_tds_kontrol_table_initial(self):
        """TDS parametrelerini tabloya goster (kontrol oncesi)"""
        self.tds_kontrol_table.setRowCount(len(self.tds_parametreler))
        for i, p in enumerate(self.tds_parametreler):
            self.tds_kontrol_table.setItem(i, 0, self._make_readonly_item(p.get("parametre_adi", "")))
            self.tds_kontrol_table.setItem(i, 1, self._make_readonly_item(p.get("birim", "")))
            self.tds_kontrol_table.setItem(i, 2, self._make_readonly_item(
                f"{p['tds_min']:.2f}" if p.get("tds_min") else "-"))
            self.tds_kontrol_table.setItem(i, 3, self._make_readonly_item(
                f"{p['tds_hedef']:.2f}" if p.get("tds_hedef") else "-"))
            self.tds_kontrol_table.setItem(i, 4, self._make_readonly_item(
                f"{p['tds_max']:.2f}" if p.get("tds_max") else "-"))

            # Gercek deger (son olcum) - DUZENLENEBILIR
            kod = p.get("parametre_kodu", "")
            gercek = self.tds_banyo_olcumler.get(kod)
            if gercek is not None:
                gercek_item = QTableWidgetItem(f"{gercek:.2f}")
            else:
                gercek_item = QTableWidgetItem("")
                gercek_item.setForeground(QColor(self.theme.get('text_muted', '#888')))
            gercek_item.setToolTip("Cift tiklayarak manuel deger girebilirsiniz")
            self.tds_kontrol_table.setItem(i, 5, gercek_item)

            # Durum - bekleniyor (salt okunur)
            self.tds_kontrol_table.setItem(i, 6, self._make_readonly_item("--"))

    def _run_tds_kontrol(self):
        """TDS kontrol analizini calistir"""
        if not self.tds_parametreler:
            QMessageBox.warning(self, "Uyari", "TDS parametreleri bulunamadi!")
            return

        try:
            # Tablodan manuel girilen degerleri oku
            for i, p in enumerate(self.tds_parametreler):
                if i < self.tds_kontrol_table.rowCount():
                    gercek_item = self.tds_kontrol_table.item(i, 5)
                    if gercek_item:
                        txt = gercek_item.text().strip()
                        if txt:
                            try:
                                self.tds_banyo_olcumler[p["parametre_kodu"]] = float(txt)
                            except ValueError:
                                pass

            from core.ai_analiz_service import AIAnalizService
            service = AIAnalizService()

            # Kaplama test verilerini topla
            av = self.kalinlik_a_input.value()
            bv = self.kalinlik_b_input.value()
            kaplama_test = {
                "sicaklik": self.sicaklik_input.value(),
                "amper": self.amper_input.value(),
                "volt": self.volt_input.value(),
                "sure_dk": self.sure_input.value(),
                "kalinlik_a": av,
                "kalinlik_b": bv,
                "ab_orani": (av / bv) if bv > 0 else 0,
                "kimyasallar": [],
            }
            for i, p in enumerate(self.kimyasal_params):
                if i < len(self.kimyasal_inputs):
                    kaplama_test["kimyasallar"].append({
                        "parametre_adi": p["adi"],
                        "deger": self.kimyasal_inputs[i].value(),
                        "min": p.get("min"),
                        "max": p.get("max"),
                        "hedef": p.get("hedef"),
                    })

            sonuc = service.kaplama_tds_analiz(
                self.banyo_combo.currentData(),
                self.tds_parametreler,
                self.tds_banyo_olcumler,
                kaplama_test
            )

            # Kontrol noktalari tablosunu guncelle
            kn = sonuc.get("kontrol_noktalari", [])
            self.tds_kontrol_table.setRowCount(len(kn))
            for i, k in enumerate(kn):
                self.tds_kontrol_table.setItem(i, 0, QTableWidgetItem(k.get("parametre", "")))
                self.tds_kontrol_table.setItem(i, 1, QTableWidgetItem(k.get("birim", "")))
                self.tds_kontrol_table.setItem(i, 2, QTableWidgetItem(
                    f"{k['tds_min']:.2f}" if k.get("tds_min") else "-"))
                self.tds_kontrol_table.setItem(i, 3, QTableWidgetItem(
                    f"{k['tds_hedef']:.2f}" if k.get("tds_hedef") else "-"))
                self.tds_kontrol_table.setItem(i, 4, QTableWidgetItem(
                    f"{k['tds_max']:.2f}" if k.get("tds_max") else "-"))

                gercek = k.get("gercek")
                if gercek is not None:
                    self.tds_kontrol_table.setItem(i, 5, QTableWidgetItem(f"{gercek:.2f}"))
                else:
                    self.tds_kontrol_table.setItem(i, 5, QTableWidgetItem("--"))

                durum = k.get("durum", "")
                durum_item = QTableWidgetItem(durum)
                durum_renk = {
                    "NORMAL": "#22C55E", "UYARI": "#F59E0B",
                    "KRITIK": "#EF4444", "DUSUK": "#F59E0B",
                    "YUKSEK": "#F59E0B", "OLCUM_YOK": "#6B7280",
                }
                durum_item.setForeground(QColor(durum_renk.get(durum, "#ffffff")))
                if k.get("kritik"):
                    font = durum_item.font()
                    font.setBold(True)
                    durum_item.setFont(font)
                self.tds_kontrol_table.setItem(i, 6, durum_item)

            # Genel durum
            genel = sonuc.get("genel_durum", "UYGUN")
            durum_map = {"UYGUN": ("UYGUN", "#22C55E"), "DIKKAT": ("DIKKAT", "#F59E0B"), "KRITIK": ("KRITIK", "#EF4444")}
            txt, renk = durum_map.get(genel, ("?", "#fff"))
            self.tds_durum_label.setText(f"Genel Durum: {txt}")
            self.tds_durum_label.setStyleSheet(f"color: {renk}; font-size: 14px; font-weight: bold;")
            self.tds_durum_frame.setStyleSheet(
                f"QFrame {{ background: {self.theme['bg_card_solid']}; "
                f"border: 2px solid {renk}; border-radius: 8px; padding: 10px; }}")

            sorunlar = sonuc.get("sorunlar", [])
            self.tds_sorun_label.setText(f"{len(sorunlar)} sorun tespit edildi" if sorunlar else "Sorun yok")

            # Sorunlar ve oneriler
            self.tds_sorunlar_text.setPlainText("\n".join(f"- {s}" for s in sorunlar) if sorunlar else "Sorun tespit edilmedi.")
            oneriler = sonuc.get("oneriler", [])
            self.tds_oneriler_text.setPlainText("\n".join(f"* {o}" for o in oneriler) if oneriler else "Oneri yok.")

        except Exception as e:
            QMessageBox.critical(self, "TDS Kontrol Hatasi", str(e))
            import traceback; traceback.print_exc()

    # ─── Yardımcılar ───
    def _load_banyolar(self):
        conn = None
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT b.id, b.kod, b.ad, h.kod FROM uretim.banyo_tanimlari b JOIN tanim.uretim_hatlari h ON b.hat_id=h.id WHERE b.aktif_mi=1 ORDER BY h.sira_no, b.kod")
            for r in cur.fetchall(): self.banyo_combo.addItem(f"{r[3]} / {r[1]} - {r[2]}", r[0])
            if self.data.get('banyo_id'):
                idx = self.banyo_combo.findData(self.data['banyo_id'])
                if idx >= 0: self.banyo_combo.setCurrentIndex(idx)
        except: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_kaplama_turleri(self):
        conn = None
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT id, kod, ad FROM laboratuvar.kaplama_turleri WHERE aktif_mi=1 ORDER BY sira_no")
            for r in cur.fetchall(): self.kaplama_turu_combo.addItem(f"{r[1]} - {r[2]}", r[0])
            if self.data.get('kaplama_turu_id'):
                idx = self.kaplama_turu_combo.findData(self.data['kaplama_turu_id'])
                if idx >= 0: self.kaplama_turu_combo.setCurrentIndex(idx)
        except: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_analistler(self):
        conn = None
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT id, ad, soyad FROM ik.personeller WHERE aktif_mi=1 ORDER BY ad")
            for r in cur.fetchall(): self.analist_combo.addItem(f"{r[1]} {r[2]}", r[0])
            if self.data.get('analist_id'):
                idx = self.analist_combo.findData(self.data['analist_id'])
                if idx >= 0: self.analist_combo.setCurrentIndex(idx)
        except: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_kimyasal_parametreler(self):
        kt_id = self.kaplama_turu_combo.currentData()
        self.kimyasal_inputs.clear(); self.kimyasal_params.clear()
        while self.kimyasal_container.count():
            item = self.kimyasal_container.takeAt(0)
            ww = item.widget()
            if ww: ww.deleteLater()
        if not kt_id:
            lbl = QLabel("ℹ️ Kaplama türü seçildiğinde parametreler görünecektir.")
            lbl.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 13px; padding: 20px;"); lbl.setAlignment(Qt.AlignCenter)
            self.kimyasal_container.addWidget(lbl); return
        conn = None
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT id, parametre_kodu, parametre_adi, birim, min_deger, max_deger, hedef_deger FROM laboratuvar.kaplama_kimyasal_parametreleri WHERE kaplama_turu_id=? AND aktif_mi=1 ORDER BY sira_no", (kt_id,))
            params = cur.fetchall()
            if not params:
                lbl = QLabel("ℹ️ Bu kaplama türü için kimyasal parametre tanımlanmamış.")
                lbl.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 13px; padding: 20px;"); lbl.setAlignment(Qt.AlignCenter)
                self.kimyasal_container.addWidget(lbl); return
            mevcut = {}
            if self.test_id:
                c2 = None
                try:
                    c2 = get_db_connection(); cu2 = c2.cursor()
                    cu2.execute("SELECT parametre_id, deger FROM laboratuvar.kaplama_test_kimyasallari WHERE test_id=?", (self.test_id,))
                    for r in cu2.fetchall(): mevcut[r[0]] = r[1]
                except: pass
                finally:
                    if c2:
                        try: c2.close()
                        except Exception: pass
            grp = QGroupBox("🧪 Banyo Kimyasal Değerleri"); frm = QFormLayout(grp); frm.setSpacing(10)
            for p in params:
                pid, pkod, padi, birim, mn, mx, hd = p
                rl = QHBoxLayout()
                sb = QDoubleSpinBox(); sb.setRange(0, 99999); sb.setDecimals(4)
                if birim: sb.setSuffix(f" {birim}")
                sb.setValue(float(mevcut.get(pid, 0) or 0)); sb.setMinimumWidth(150); rl.addWidget(sb)
                lt = ""
                if mn and mx:
                    lt = f"  [{mn:.2f} - {mx:.2f}]"
                    if hd: lt += f" Hedef: {hd:.2f}"
                ll = QLabel(lt); ll.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 11px;"); rl.addWidget(ll); rl.addStretch()
                cw = QWidget(); cw.setLayout(rl); frm.addRow(f"{padi}:", cw)
                self.kimyasal_inputs.append(sb)
                self.kimyasal_params.append({'id': pid, 'kod': pkod, 'adi': padi, 'birim': birim, 'min': float(mn) if mn else None, 'max': float(mx) if mx else None, 'hedef': float(hd) if hd else None})
            self.kimyasal_container.addWidget(grp)
        except Exception as e:
            el = QLabel(f"⚠️ Hata: {e}"); el.setStyleSheet("color: #EF4444;"); self.kimyasal_container.addWidget(el)
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _hesapla_ab(self):
        a, b = self.kalinlik_a_input.value(), self.kalinlik_b_input.value()
        if a > 0 and b > 0:
            o = a / b; self.ab_oran_label.setText(f"{o:.2f}")
            if o <= 1.5:
                self.ab_oran_label.setStyleSheet("color: #22C55E; font-size: 48px; font-weight: bold;")
                self.ab_durum_label.setText("✅ Mükemmel"); self.ab_durum_label.setStyleSheet("color: #22C55E; font-size: 14px;")
            elif o <= 2.0:
                self.ab_oran_label.setStyleSheet("color: #F59E0B; font-size: 48px; font-weight: bold;")
                self.ab_durum_label.setText("⚠️ Kabul edilebilir"); self.ab_durum_label.setStyleSheet("color: #F59E0B; font-size: 14px;")
            elif o <= 3.0:
                self.ab_oran_label.setStyleSheet("color: #EF4444; font-size: 48px; font-weight: bold;")
                self.ab_durum_label.setText("🔴 Homojenlik düşük"); self.ab_durum_label.setStyleSheet("color: #EF4444; font-size: 14px;")
            else:
                self.ab_oran_label.setStyleSheet("color: #DC2626; font-size: 48px; font-weight: bold;")
                self.ab_durum_label.setText("🔴 Kritik!"); self.ab_durum_label.setStyleSheet("color: #DC2626; font-size: 14px; font-weight: bold;")
        else:
            self.ab_oran_label.setText("-"); self.ab_oran_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 48px; font-weight: bold;")
            self.ab_durum_label.setText("")

    def _ai_degerlendirme(self):
        kims = []
        for i, p in enumerate(self.kimyasal_params):
            if i < len(self.kimyasal_inputs):
                kims.append({'parametre_adi': p['adi'], 'deger': self.kimyasal_inputs[i].value(), 'min': p.get('min'), 'max': p.get('max'), 'hedef': p.get('hedef')})
        av, bv = self.kalinlik_a_input.value(), self.kalinlik_b_input.value()
        td = {'kaplama_turu': self.kaplama_turu_combo.currentText() or '', 'amper': self.amper_input.value(), 'volt': self.volt_input.value(), 'sure_dk': self.sure_input.value(), 'sicaklik': self.sicaklik_input.value(), 'kalinlik_a': av, 'kalinlik_b': bv, 'ab_orani': (av/bv) if bv > 0 else 0, 'sapma_a': self.sapma_a_input.value(), 'sapma_b': self.sapma_b_input.value(), 'kimyasallar': kims}
        yorum = generate_ai_yorum(td, self.tds_parametreler, self.tds_banyo_olcumler); self.ai_yorum_text.setText(yorum)
        if "KRİTİK" in yorum:
            idx = self.sonuc_combo.findData("UYGUN_DEGIL")
            if idx >= 0: self.sonuc_combo.setCurrentIndex(idx)
        elif "UYGUN" in yorum and "DİKKAT" not in yorum:
            idx = self.sonuc_combo.findData("UYGUN")
            if idx >= 0: self.sonuc_combo.setCurrentIndex(idx)

    def _save(self):
        banyo_id = self.banyo_combo.currentData()
        kt_id = self.kaplama_turu_combo.currentData()
        analist_id = self.analist_combo.currentData()
        if not banyo_id or not kt_id or not analist_id:
            QMessageBox.warning(self, "Uyarı", "Banyo, Kaplama Türü ve Analist seçimi zorunludur!"); return
        av = self.kalinlik_a_input.value() or None; bv = self.kalinlik_b_input.value() or None
        ab = (av / bv) if av and bv and bv > 0 else None

        # Fotoğraf
        foto_db = self.data.get('foto_yolu')
        kaynak = self.foto_widget.get_kaynak_yol()
        secili = self.foto_widget.get_foto_yolu()
        if kaynak:
            foto_db = foto_kaydet(kaynak, self.data.get('test_no', 'YENI'))
        elif not secili:
            foto_db = None

        conn = None
        try:
            conn = get_db_connection(); cur = conn.cursor()
            params = (banyo_id, kt_id, self.tarih_input.dateTime().toPython(), analist_id,
                      self.amper_input.value() or None, self.volt_input.value() or None,
                      self.sure_input.value() or None, self.sicaklik_input.value() or None,
                      av, self.sapma_a_input.value() or None, bv, self.sapma_b_input.value() or None, ab,
                      foto_db, self.sonuc_combo.currentData(),
                      self.ai_yorum_text.toPlainText().strip() or None,
                      datetime.now() if self.ai_yorum_text.toPlainText().strip() else None,
                      self.notlar_input.toPlainText().strip() or None)
            if self.test_id:
                cur.execute("""UPDATE laboratuvar.kaplama_testleri SET
                    banyo_id=?, kaplama_turu_id=?, test_tarihi=?, analist_id=?,
                    amper=?, volt=?, sure_dk=?, sicaklik=?,
                    kalinlik_a=?, sapma_a=?, kalinlik_b=?, sapma_b=?, ab_orani=?,
                    foto_yolu=?, sonuc=?, ai_yorum=?, ai_yorum_tarihi=?, notlar=?,
                    guncelleme_tarihi=GETDATE() WHERE id=?""", params + (self.test_id,))
                cur.execute("DELETE FROM laboratuvar.kaplama_test_kimyasallari WHERE test_id=?", (self.test_id,))
                tid = self.test_id
            else:
                cur.execute("""INSERT INTO laboratuvar.kaplama_testleri
                    (banyo_id, kaplama_turu_id, test_tarihi, analist_id, amper, volt, sure_dk, sicaklik,
                     kalinlik_a, sapma_a, kalinlik_b, sapma_b, ab_orani, foto_yolu, sonuc, ai_yorum, ai_yorum_tarihi, notlar)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", params)
                cur.execute("SELECT @@IDENTITY"); tid = cur.fetchone()[0]
            for i, p in enumerate(self.kimyasal_params):
                if i < len(self.kimyasal_inputs):
                    d = self.kimyasal_inputs[i].value()
                    if d > 0:
                        dur = 'NORMAL'
                        if p.get('min') and d < p['min']: dur = 'DUSUK'
                        elif p.get('max') and d > p['max']: dur = 'YUKSEK'
                        cur.execute("INSERT INTO laboratuvar.kaplama_test_kimyasallari (test_id, parametre_id, deger, durum) VALUES (?,?,?,?)", (tid, p['id'], d, dur))
            conn.commit()

            # Yeni kayıtsa fotoğrafı test_no ile yeniden adlandır
            if not self.test_id and foto_db and kaynak:
                cur.execute("SELECT test_no FROM laboratuvar.kaplama_testleri WHERE id=?", (tid,))
                tno = cur.fetchone()
                if tno and tno[0]:
                    yeni = foto_kaydet(kaynak, tno[0])
                    if yeni and yeni != foto_db:
                        cur.execute("UPDATE laboratuvar.kaplama_testleri SET foto_yolu=? WHERE id=?", (yeni, tid))
                        conn.commit()
                        try:
                            if os.path.exists(foto_db) and foto_db != kaynak: os.remove(foto_db)
                        except: pass
            QMessageBox.information(self, "Başarılı", "Kaplama test kaydı başarıyla kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası:\n{str(e)}")
            import traceback; traceback.print_exc()
        finally:
            if conn:
                try: conn.close()
                except Exception: pass


# ═══════════════════════════════════════════════
# KAPLAMA TEST LİSTE SAYFASI
# ═══════════════════════════════════════════════
class LabKaplamaTestPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        t = self.theme
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        tl = QVBoxLayout()
        tt = QLabel("🔬 Kaplama Test Kayıtları"); tt.setStyleSheet(f"color: {t['text']}; font-size: 24px; font-weight: bold;"); tl.addWidget(tt)
        st = QLabel("Kaplama kalınlık testlerini kaydedin ve takip edin"); st.setStyleSheet(f"color: {t['text_muted']}; font-size: 13px;"); tl.addWidget(st)
        hdr.addLayout(tl); hdr.addStretch()
        self.stat_label = QLabel(""); self.stat_label.setStyleSheet(f"color: {t['text_muted']};"); hdr.addWidget(self.stat_label)
        layout.addLayout(hdr)

        # Kartlar
        sl = QHBoxLayout(); sl.setSpacing(12)
        self.card_toplam = self._mk_card("Toplam Test", "0", "🔬", "#3B82F6")
        self.card_uygun = self._mk_card("Uygun", "0", "✅", "#22C55E")
        self.card_uygun_degil = self._mk_card("Uygun Değil", "0", "❌", "#EF4444")
        self.card_beklemede = self._mk_card("Beklemede", "0", "⏳", "#F59E0B")
        sl.addWidget(self.card_toplam); sl.addWidget(self.card_uygun); sl.addWidget(self.card_uygun_degil); sl.addWidget(self.card_beklemede)
        layout.addLayout(sl)

        # Toolbar
        tb = QHBoxLayout()
        self.banyo_combo = QComboBox(); self.banyo_combo.addItem("Tüm Banyolar", None); self._load_banyo_filter()
        self.banyo_combo.setStyleSheet(f"background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 8px; color: {t['text']}; min-width: 200px;")
        self.banyo_combo.currentIndexChanged.connect(self._load_data); tb.addWidget(self.banyo_combo)
        self.kaplama_combo = QComboBox(); self.kaplama_combo.addItem("Tüm Kaplama Türleri", None); self._load_kaplama_filter()
        self.kaplama_combo.setStyleSheet(f"background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 8px; color: {t['text']}; min-width: 150px;")
        self.kaplama_combo.currentIndexChanged.connect(self._load_data); tb.addWidget(self.kaplama_combo)
        self.sonuc_combo = QComboBox(); self.sonuc_combo.addItem("Tüm Sonuçlar", None); self.sonuc_combo.addItem("✅ Uygun", "UYGUN"); self.sonuc_combo.addItem("❌ Uygun Değil", "UYGUN_DEGIL"); self.sonuc_combo.addItem("⏳ Beklemede", "BEKLEMEDE")
        self.sonuc_combo.setStyleSheet(f"background: {t['bg_input']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 8px; color: {t['text']}; min-width: 120px;")
        self.sonuc_combo.currentIndexChanged.connect(self._load_data); tb.addWidget(self.sonuc_combo)
        tb.addStretch()
        ab = QPushButton("➕ Yeni Test"); ab.setStyleSheet(f"background: {t['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        ab.clicked.connect(self._add_new); tb.addWidget(ab)
        layout.addLayout(tb)

        # Tablo
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {t['bg_card_solid']}; border: 1px solid {t['border']}; border-radius: 8px; gridline-color: {t['border']}; color: {t['text']}; }}
            QTableWidget::item {{ padding: 6px; }} QTableWidget::item:selected {{ background: {t['primary']}; }}
            QHeaderView::section {{ background: {t['bg_main']}; color: {t['text']}; padding: 8px; border: none; border-bottom: 2px solid {t['primary']}; font-weight: bold; }}
        """)
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels(["ID", "Test No", "Tarih", "Banyo", "Kaplama", "Analist", "A (µ)", "B (µ)", "A/B", "Amper", "Sıcaklık", "📷", "Sonuç", "İşlem"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        for col, w in [(0,50),(1,110),(2,120),(4,80),(5,110),(6,65),(7,65),(8,55),(9,65),(10,70),(11,40),(12,95),(13,170)]:
            self.table.setColumnWidth(col, w)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

    def _mk_card(self, title, value, icon, color):
        t = self.theme
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: {t['bg_card_solid']}; border: 1px solid {t['border']}; border-radius: 12px; border-left: 4px solid {color}; }}")
        card.setMinimumSize(150, 80)
        lo = QVBoxLayout(card); lo.setContentsMargins(16, 12, 16, 12)
        hl = QHBoxLayout()
        il = QLabel(icon); il.setStyleSheet("font-size: 20px;"); hl.addWidget(il)
        tl = QLabel(title); tl.setStyleSheet(f"color: {t['text_muted']}; font-size: 12px;"); hl.addWidget(tl); hl.addStretch()
        lo.addLayout(hl)
        vl = QLabel(value); vl.setObjectName("value_label"); vl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;"); lo.addWidget(vl)
        return card

    def _load_banyo_filter(self):
        conn = None
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT b.id, b.kod, h.kod FROM uretim.banyo_tanimlari b JOIN tanim.uretim_hatlari h ON b.hat_id=h.id WHERE b.aktif_mi=1 ORDER BY h.sira_no, b.kod")
            for r in cur.fetchall(): self.banyo_combo.addItem(f"{r[2]} / {r[1]}", r[0])
        except: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_kaplama_filter(self):
        conn = None
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT id, kod, ad FROM laboratuvar.kaplama_turleri WHERE aktif_mi=1 ORDER BY sira_no")
            for r in cur.fetchall(): self.kaplama_combo.addItem(f"{r[1]} - {r[2]}", r[0])
        except: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection(); cur = conn.cursor()
            sql = """SELECT t.id, t.test_no, t.test_tarihi, b.kod, kt.kod, p.ad+' '+p.soyad,
                       t.kalinlik_a, t.kalinlik_b, t.ab_orani, t.amper, t.sicaklik, t.foto_yolu, t.sonuc
                FROM laboratuvar.kaplama_testleri t
                JOIN uretim.banyo_tanimlari b ON t.banyo_id=b.id
                JOIN laboratuvar.kaplama_turleri kt ON t.kaplama_turu_id=kt.id
                JOIN ik.personeller p ON t.analist_id=p.id WHERE t.silindi_mi=0"""
            prm = []
            bid = self.banyo_combo.currentData()
            if bid: sql += " AND t.banyo_id=?"; prm.append(bid)
            kid = self.kaplama_combo.currentData()
            if kid: sql += " AND t.kaplama_turu_id=?"; prm.append(kid)
            sf = self.sonuc_combo.currentData()
            if sf: sql += " AND t.sonuc=?"; prm.append(sf)
            sql += " ORDER BY t.test_tarihi DESC"
            cur.execute(sql, prm); rows = cur.fetchall()

            toplam = len(rows)
            uygun = sum(1 for r in rows if r[12] == 'UYGUN')
            uygun_d = sum(1 for r in rows if r[12] == 'UYGUN_DEGIL')
            bekl = sum(1 for r in rows if r[12] == 'BEKLEMEDE')
            self.card_toplam.findChild(QLabel, "value_label").setText(str(toplam))
            self.card_uygun.findChild(QLabel, "value_label").setText(str(uygun))
            self.card_uygun_degil.findChild(QLabel, "value_label").setText(str(uygun_d))
            self.card_beklemede.findChild(QLabel, "value_label").setText(str(bekl))

            self.table.setRowCount(toplam)
            for i, r in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(r[0])))
                self.table.setItem(i, 1, QTableWidgetItem(r[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(r[2].strftime("%d.%m.%Y %H:%M") if r[2] else '-'))
                self.table.setItem(i, 3, QTableWidgetItem(r[3] or ''))
                self.table.setItem(i, 4, QTableWidgetItem(r[4] or ''))
                self.table.setItem(i, 5, QTableWidgetItem(r[5] or ''))
                self.table.setItem(i, 6, QTableWidgetItem(f"{r[6]:.2f}" if r[6] else '-'))
                self.table.setItem(i, 7, QTableWidgetItem(f"{r[7]:.2f}" if r[7] else '-'))

                ab_item = QTableWidgetItem(f"{r[8]:.2f}" if r[8] else '-')
                if r[8]:
                    if r[8] <= 1.5: ab_item.setForeground(QColor("#22C55E"))
                    elif r[8] <= 2.0: ab_item.setForeground(QColor("#F59E0B"))
                    else: ab_item.setForeground(QColor("#EF4444"))
                self.table.setItem(i, 8, ab_item)

                self.table.setItem(i, 9, QTableWidgetItem(f"{r[9]:.1f}A" if r[9] else '-'))
                self.table.setItem(i, 10, QTableWidgetItem(f"{r[10]:.0f}°C" if r[10] else '-'))

                # Fotoğraf ikonu
                foto_item = QTableWidgetItem("📷" if r[11] else "—")
                if r[11]:
                    foto_item.setToolTip(r[11])
                self.table.setItem(i, 11, foto_item)

                smap = {"UYGUN": "✅ Uygun", "UYGUN_DEGIL": "❌ Uyg.Değil", "BEKLEMEDE": "⏳ Bekleme"}
                scol = {"UYGUN": "#22C55E", "UYGUN_DEGIL": "#EF4444", "BEKLEMEDE": "#F59E0B"}
                si = QTableWidgetItem(smap.get(r[12], r[12] or ''))
                si.setForeground(QColor(scol.get(r[12], self.theme['text'])))
                self.table.setItem(i, 12, si)

                # İşlem butonları
                buttons = [
                    ("✏️", "Duzenle", lambda checked, rid=r[0]: self._edit_item(rid), "edit"),
                ]
                if r[11]:
                    buttons.append(("🔍", "Fotograf", lambda checked, fp=r[11]: self._view_foto(fp), "info"))
                buttons.append(("🗑️", "Sil", lambda checked, rid=r[0]: self._delete_item(rid), "delete"))
                widget = self.create_action_buttons(buttons)
                self.table.setCellWidget(i, 13, widget)
                self.table.setRowHeight(i, 42)

            self.stat_label.setText(f"Toplam: {toplam} test")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
            import traceback; traceback.print_exc()
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _add_new(self):
        dlg = KaplamaTestDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted: self._load_data()

    def _edit_item(self, tid):
        dlg = KaplamaTestDialog(self.theme, tid, parent=self)
        if dlg.exec() == QDialog.Accepted: self._load_data()

    def _view_foto(self, foto_yolu):
        FotoOnizlemeDialog(foto_yolu, self.theme, self).exec()

    def _delete_item(self, tid):
        if QMessageBox.question(self, "Onay", "Bu test kaydını silmek istediğinize emin misiniz?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection(); cur = conn.cursor()
                cur.execute("UPDATE laboratuvar.kaplama_testleri SET silindi_mi=1 WHERE id=?", (tid,))
                conn.commit(); self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass
