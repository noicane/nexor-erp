# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kaplama Test Kayitlari
===================================
laboratuvar.kaplama_testleri tablosu icin CRUD
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
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
from core.nexor_brand import brand

# =====================================================================
# FOTOGRAF AYARLARI - JSON Config
# =====================================================================
DESTEKLENEN_FORMATLAR = "Resim Dosyalari (*.jpg *.jpeg *.png *.bmp *.tiff *.webp)"
VARSAYILAN_FOTO_KLASORU = r"\\192.168.1.66\lab_fotolar\kaplama_test"


def _config_yolu():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "lab_kaplama_config.json")


def ayarlari_yukle() -> dict:
    """JSON config dosyasindan ayarlari yukle"""
    yol = _config_yolu()
    varsayilan = {"foto_klasoru": VARSAYILAN_FOTO_KLASORU}
    try:
        if os.path.exists(yol):
            with open(yol, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {**varsayilan, **data}
    except Exception as e:
        print(f"Config yukleme hatasi: {e}")
    return varsayilan


def ayarlari_kaydet(ayarlar: dict):
    """JSON config dosyasina ayarlari kaydet"""
    yol = _config_yolu()
    try:
        with open(yol, "w", encoding="utf-8") as f:
            json.dump(ayarlar, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Config kaydetme hatasi: {e}")
        return False


def get_foto_klasoru() -> str:
    """Gecerli fotograf klasorunu doner"""
    return ayarlari_yukle().get("foto_klasoru", VARSAYILAN_FOTO_KLASORU)


def foto_klasoru_kontrol():
    klasor = get_foto_klasoru()
    try:
        if not os.path.exists(klasor):
            os.makedirs(klasor, exist_ok=True)
        return True
    except Exception as e:
        print(f"Fotograf klasoru olusturulamadi: {e}")
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
        print(f"Fotograf kopyalama hatasi: {e}")
        return kaynak_yol


# =====================================================================
# FOTOGRAF AYARLARI DIALOG
# =====================================================================
class FotoAyarlariDialog(QDialog):
    """Fotograf kayit klasoru ayarlari"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Fotograf Ayarlari")
        self.setMinimumWidth(brand.sp(550))
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_4)

        title = QLabel("Fotograf Kayit Ayarlari")
        title.setStyleSheet(
            f"font-size: {brand.FS_HEADING_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"color: {brand.TEXT};"
        )
        layout.addWidget(title)

        info = QLabel(
            "Test plakasi fotograflarinin kaydedilecegi klasor yolunu belirleyin.\n"
            "Ag paylasim yolu (\\\\sunucu\\klasor) veya yerel yol (C:\\...) kullanabilirsiniz."
        )
        info.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Klasor yolu
        grp = QGroupBox("Fotograf Klasoru")
        grp.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                margin-top: {brand.SP_5}px;
                padding: {brand.SP_5}px;
                padding-top: {brand.SP_8}px;
                background: {brand.BG_CARD};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {brand.SP_4}px;
                top: {brand.SP_2}px;
                padding: 0 {brand.SP_2}px;
                color: {brand.TEXT_MUTED};
                background: {brand.BG_MAIN};
            }}
        """)
        gl = QVBoxLayout(grp)
        gl.setSpacing(brand.SP_3)

        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(get_foto_klasoru())
        self.path_input.setPlaceholderText("Orn: \\\\192.168.1.66\\lab_fotolar\\kaplama_test")
        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton("Gozat")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setFixedHeight(brand.sp(38))
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        """)
        browse_btn.clicked.connect(self._gozat)
        path_layout.addWidget(browse_btn)
        gl.addLayout(path_layout)

        # Durum gostergesi
        self.durum_label = QLabel("")
        self.durum_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"
        )
        gl.addWidget(self.durum_label)

        # Test butonu
        test_btn = QPushButton("Klasoru Test Et")
        test_btn.setCursor(Qt.PointingHandCursor)
        test_btn.setFixedHeight(brand.sp(38))
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        """)
        test_btn.clicked.connect(self._test_klasor)
        gl.addWidget(test_btn)

        layout.addWidget(grp)

        # Mevcut ayar bilgisi
        config_lbl = QLabel(f"Config dosyasi: {_config_yolu()}")
        config_lbl.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"
        )
        config_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(config_lbl)

        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        reset_btn = QPushButton("Varsayilana Don")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setFixedHeight(brand.sp(38))
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        """)
        reset_btn.clicked.connect(self._varsayilana_don)
        btn_layout.addWidget(reset_btn)

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(brand.sp(38))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(brand.sp(38))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        save_btn.clicked.connect(self._kaydet)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        # Ilk yuklemede test et
        self._test_klasor()

    def _gozat(self):
        klasor = QFileDialog.getExistingDirectory(self, "Fotograf Klasoru Sec", self.path_input.text())
        if klasor:
            self.path_input.setText(klasor)
            self._test_klasor()

    def _test_klasor(self):
        yol = self.path_input.text().strip()
        if not yol:
            self.durum_label.setText("Klasor yolu bos olamaz")
            self.durum_label.setStyleSheet(
                f"color: {brand.WARNING}; font-size: {brand.FS_CAPTION}px;")
            return
        if os.path.exists(yol):
            if os.access(yol, os.W_OK):
                self.durum_label.setText("Klasor erisilebilir ve yazilabilir")
                self.durum_label.setStyleSheet(
                    f"color: {brand.SUCCESS}; font-size: {brand.FS_CAPTION}px;")
            else:
                self.durum_label.setText("Klasor var ama yazma izni yok!")
                self.durum_label.setStyleSheet(
                    f"color: {brand.WARNING}; font-size: {brand.FS_CAPTION}px;")
        else:
            self.durum_label.setText("Klasor mevcut degil - ilk kayitta otomatik olusturulacak")
            self.durum_label.setStyleSheet(
                f"color: {brand.INFO}; font-size: {brand.FS_CAPTION}px;")

    def _varsayilana_don(self):
        self.path_input.setText(VARSAYILAN_FOTO_KLASORU)
        self._test_klasor()

    def _kaydet(self):
        yol = self.path_input.text().strip()
        if not yol:
            QMessageBox.warning(self, "Uyari", "Klasor yolu bos olamaz!")
            return
        ayarlar = ayarlari_yukle()
        ayarlar["foto_klasoru"] = yol
        if ayarlari_kaydet(ayarlar):
            QMessageBox.information(self, "Basarili", f"Fotograf klasoru kaydedildi:\n{yol}")
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Ayarlar kaydedilemedi!")


# =====================================================================
# AI YORUM
# =====================================================================
def generate_ai_yorum(td: dict, tds_parametreler: list = None, banyo_olcumler: dict = None) -> str:
    yorumlar, sorunlar, oneriler = [], [], []
    ab = td.get('ab_orani', 0) or 0
    kal_a = td.get('kalinlik_a', 0) or 0
    kal_b = td.get('kalinlik_b', 0) or 0
    sic = td.get('sicaklik', 0) or 0
    kap = td.get('kaplama_turu', '')

    if ab > 0:
        if ab <= 1.5:
            yorumlar.append(f"A/B orani {ab:.2f} - Iyi dagilim.")
        elif ab <= 2.0:
            yorumlar.append(f"A/B orani {ab:.2f} - Kabul edilebilir.")
            oneriler.append("Anot-katot mesafesini kontrol edin.")
        elif ab <= 3.0:
            sorunlar.append(f"A/B orani {ab:.2f} - Homojenlik dusuk!")
            oneriler.append("Anot pozisyonunu gozden gecirin.")
        else:
            sorunlar.append(f"A/B orani {ab:.2f} - Kritik!")
            oneriler.append("Acil: Anot geometrisi ve akim yogunlugunu gozden gecirin.")

    if kal_a > 0 and kal_b > 0:
        ort = (kal_a + kal_b) / 2
        if ort < 1.0:
            sorunlar.append(f"Ort. kalinlik {ort:.2f}u - Dusuk!")
        else:
            yorumlar.append(f"Ort. kalinlik: {ort:.2f}u")

    for kim in td.get('kimyasallar', []):
        d, mn, mx = kim.get('deger', 0), kim.get('min'), kim.get('max')
        adi = kim.get('parametre_adi', '')
        if mn and mx:
            if d < mn:
                sorunlar.append(f"{adi}: {d:.2f} - Min ({mn:.2f}) altinda!")
                oneriler.append(f"{adi} takviyesi yapilmali.")
            elif d > mx:
                sorunlar.append(f"{adi}: {d:.2f} - Max ({mx:.2f}) ustunde!")
            else:
                yorumlar.append(f"{adi}: {d:.2f} - Normal.")

    if sic > 0:
        if 'Nikel' in kap and sic < 40:
            sorunlar.append(f"Sicaklik {sic:.0f}C - Nikel icin dusuk (ideal: 45-60C)")
        elif 'Cinko' in kap and sic > 40:
            sorunlar.append(f"Sicaklik {sic:.0f}C - Cinko icin yuksek")

    # --- TDS Kontrol Karsilastirmasi ---
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
                    tds_sorunlar.append(f"{adi}: Olcum verisi yok (kritik parametre!)")
                continue

            gercek = float(gercek)
            if tds_min and tds_max and tds_min > 0:
                if gercek < tds_min:
                    tds_sorunlar.append(f"{adi}: {gercek:.2f} < TDS Min ({tds_min:.2f})")
                    oneriler.append(f"TDS'e gore {adi} dusuk - takviye gerekli")
                elif gercek > tds_max:
                    tds_sorunlar.append(f"{adi}: {gercek:.2f} > TDS Max ({tds_max:.2f})")
                    oneriler.append(f"TDS'e gore {adi} yuksek - duzenleme gerekli")
                else:
                    yorumlar.append(f"{adi}: {gercek:.2f} - TDS araliginda")
            elif tds_hedef and tds_hedef > 0:
                sapma = abs((gercek - tds_hedef) / tds_hedef * 100)
                tolerans = float(p.get("tolerans_yuzde") or 10)
                if sapma > tolerans * 2:
                    tds_sorunlar.append(f"{adi}: %{sapma:.0f} sapma (Hedef: {tds_hedef:.2f}, Gercek: {gercek:.2f})")
                elif sapma > tolerans:
                    tds_sorunlar.append(f"{adi}: %{sapma:.0f} sapma (Hedef: {tds_hedef:.2f})")

    r = "=== AI Kaplama Test Degerlendirmesi ===\n\n"
    if yorumlar:
        r += "Degerlendirme:\n" + "\n".join(f"  {y}" for y in yorumlar) + "\n\n"
    if sorunlar:
        r += "Sorunlar:\n" + "\n".join(f"  {s}" for s in sorunlar) + "\n\n"
    if tds_sorunlar:
        r += "TDS Kontrol Sapmalari:\n" + "\n".join(f"  {s}" for s in tds_sorunlar) + "\n\n"
        sorunlar.extend(tds_sorunlar)
    if oneriler:
        r += "Oneriler:\n" + "\n".join(f"  - {o}" for o in oneriler) + "\n\n"
    if not sorunlar:
        r += "Genel: UYGUN"
    elif len(sorunlar) <= 2:
        r += "Genel: DIKKAT"
    else:
        r += "Genel: KRITIK"
    r += f"\n\n{datetime.now().strftime('%d.%m.%Y %H:%M')}"
    return r


# =====================================================================
# FOTOGRAF ONIZLEME DIALOG
# =====================================================================
class FotoOnizlemeDialog(QDialog):
    def __init__(self, foto_yolu: str, theme: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Plakasi Fotografi")
        self.setMinimumSize(brand.sp(700), brand.sp(550))
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_3)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"border: none; background: {brand.BG_MAIN};")
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)
        if foto_yolu and os.path.exists(foto_yolu):
            px = QPixmap(foto_yolu)
            if not px.isNull():
                lbl.setPixmap(px.scaled(
                    QSize(brand.sp(660), brand.sp(500)),
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
            else:
                lbl.setText("Yuklenemedi")
        else:
            lbl.setText("Dosya bulunamadi")
        lbl.setStyleSheet(
            f"color: {brand.ERROR}; font-size: {brand.FS_HEADING_SM}px;"
        )
        scroll.setWidget(lbl)
        layout.addWidget(scroll, 1)

        yol_lbl = QLabel(foto_yolu or "-")
        yol_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px;"
        )
        yol_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(yol_lbl)

        btn = QPushButton("Kapat")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(brand.sp(38))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        """)
        btn.clicked.connect(self.close)
        layout.addWidget(btn, alignment=Qt.AlignRight)


# =====================================================================
# FOTOGRAF SECICI WIDGET
# =====================================================================
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
        self.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; "
            f"border: 2px dashed {brand.BORDER}; "
            f"border-radius: {brand.R_LG}px; }}"
        )
        self.setMinimumHeight(brand.sp(200))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_3)

        self.onizleme_label = QLabel()
        self.onizleme_label.setAlignment(Qt.AlignCenter)
        self.onizleme_label.setMinimumSize(brand.sp(200), brand.sp(120))
        self._goster_bos()
        layout.addWidget(self.onizleme_label, 1)

        self.yol_label = QLabel("-")
        self.yol_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px; border: none;"
        )
        self.yol_label.setWordWrap(True)
        self.yol_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.yol_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_2)

        self.sec_btn = QPushButton("Fotograf Sec")
        self.sec_btn.setCursor(Qt.PointingHandCursor)
        self.sec_btn.setFixedHeight(brand.sp(38))
        self.sec_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        self.sec_btn.clicked.connect(self._dosya_sec)
        btn_layout.addWidget(self.sec_btn)

        self.goruntule_btn = QPushButton("Buyut")
        self.goruntule_btn.setCursor(Qt.PointingHandCursor)
        self.goruntule_btn.setFixedHeight(brand.sp(38))
        self.goruntule_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        """)
        self.goruntule_btn.clicked.connect(self._buyut)
        self.goruntule_btn.setEnabled(False)
        btn_layout.addWidget(self.goruntule_btn)

        self.kaldir_btn = QPushButton("Kaldir")
        self.kaldir_btn.setCursor(Qt.PointingHandCursor)
        self.kaldir_btn.setFixedHeight(brand.sp(38))
        self.kaldir_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.ERROR};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.ERROR_SOFT}; }}
        """)
        self.kaldir_btn.clicked.connect(self._kaldir)
        self.kaldir_btn.setEnabled(False)
        btn_layout.addWidget(self.kaldir_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _goster_bos(self):
        self.onizleme_label.setText("Fotograf secilmedi\nDosya sec butonunu kullanin")
        self.onizleme_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_LG}px; "
            f"border: none; padding: {brand.SP_5}px;"
        )
        self.onizleme_label.setCursor(Qt.PointingHandCursor)
        self.onizleme_label.mousePressEvent = lambda e: self._dosya_sec()

    def _goster_onizleme(self, yol: str):
        if not yol or not os.path.exists(yol):
            self._goster_bos()
            return
        px = QPixmap(yol)
        if px.isNull():
            self.onizleme_label.setText("Yuklenemedi")
            return
        self.onizleme_label.setPixmap(
            px.scaled(QSize(brand.sp(380), brand.sp(280)),
                      Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.onizleme_label.setStyleSheet("border: none;")
        self.onizleme_label.setCursor(Qt.PointingHandCursor)
        self.onizleme_label.mousePressEvent = lambda e: self._buyut()
        self.yol_label.setText(yol)
        self.goruntule_btn.setEnabled(True)
        self.kaldir_btn.setEnabled(True)

    def _dosya_sec(self):
        dosya, _ = QFileDialog.getOpenFileName(
            self, "Test Plakasi Fotografi Sec", "", DESTEKLENEN_FORMATLAR
        )
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
        self.yol_label.setText("-")
        self.goruntule_btn.setEnabled(False)
        self.kaldir_btn.setEnabled(False)

    def get_foto_yolu(self):
        return self.foto_yolu

    def get_kaynak_yol(self):
        return self._kaynak_yol


# =====================================================================
# KAPLAMA TEST DIALOG
# =====================================================================
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
        self.setWindowTitle("Yeni Kaplama Testi" if not test_id else "Kaplama Testi Duzenle")
        self.setMinimumSize(brand.sp(850), brand.sp(750))
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
                try:
                    conn.close()
                except Exception:
                    pass

    # -- ortak stiller --
    def _groupbox_css(self):
        return f"""
            QGroupBox {{
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                margin-top: {brand.SP_5}px;
                padding: {brand.SP_5}px;
                padding-top: {brand.SP_8}px;
                background: {brand.BG_CARD};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {brand.SP_4}px;
                top: {brand.SP_2}px;
                padding: 0 {brand.SP_2}px;
                color: {brand.TEXT_MUTED};
                background: {brand.BG_MAIN};
            }}
        """

    def _input_css(self):
        return f"""
            QComboBox, QDoubleSpinBox, QDateTimeEdit, QLineEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus, QLineEdit:focus {{
                border-color: {brand.PRIMARY};
            }}
        """

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            {self._input_css()}
            QTextEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QTextEdit:focus {{ border-color: {brand.PRIMARY}; }}
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                background: {brand.BG_CARD};
                border-radius: {brand.R_LG}px;
            }}
            QTabBar::tab {{
                background: {brand.BG_INPUT};
                padding: {brand.SP_3}px {brand.SP_5}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
                border-top-left-radius: {brand.R_SM}px;
                border-top-right-radius: {brand.R_SM}px;
            }}
            QTabBar::tab:selected {{
                background: {brand.BG_CARD};
                border-bottom: 3px solid {brand.PRIMARY};
                font-weight: {brand.FW_SEMIBOLD};
            }}
            {self._groupbox_css()}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_3)

        # -- Header --
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)

        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(title)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)

        # Temel bilgiler
        grp = QGroupBox("Temel Bilgiler")
        frm = QFormLayout(grp)
        frm.setSpacing(brand.SP_3)

        self.banyo_combo = QComboBox()
        self.banyo_combo.addItem("-- Banyo Seciniz --", None)
        self._load_banyolar()
        self.banyo_combo.currentIndexChanged.connect(self._on_banyo_changed)
        frm.addRow("Banyo *:", self.banyo_combo)

        self.kaplama_turu_combo = QComboBox()
        self.kaplama_turu_combo.addItem("-- Kaplama Turu --", None)
        self._load_kaplama_turleri()
        self.kaplama_turu_combo.currentIndexChanged.connect(self._load_kimyasal_parametreler)
        frm.addRow("Kaplama Turu *:", self.kaplama_turu_combo)

        self.tarih_input = QDateTimeEdit()
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.tarih_input.setDateTime(
            QDateTime(self.data['test_tarihi']) if self.data.get('test_tarihi')
            else QDateTime.currentDateTime()
        )
        frm.addRow("Test Tarihi *:", self.tarih_input)

        self.analist_combo = QComboBox()
        self.analist_combo.addItem("-- Analist --", None)
        self._load_analistler()
        frm.addRow("Analist *:", self.analist_combo)

        layout.addWidget(grp)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._tab_proses(), "Proses")
        tabs.addTab(self._tab_kimyasal(), "Kimyasal")
        tabs.addTab(self._tab_kalinlik(), "Kalinlik")
        tabs.addTab(self._tab_tds_kontrol(), "TDS Kontrol")
        tabs.addTab(self._tab_foto(), "Fotograf")
        tabs.addTab(self._tab_sonuc(), "Sonuc")
        layout.addWidget(tabs, 1)

        # Butonlar
        bl = QHBoxLayout()
        bl.setSpacing(brand.SP_3)
        bl.addStretch()

        cb = QPushButton("Iptal")
        cb.setCursor(Qt.PointingHandCursor)
        cb.setFixedHeight(brand.sp(38))
        cb.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        """)
        cb.clicked.connect(self.reject)
        bl.addWidget(cb)

        ab = QPushButton("AI Degerlendir")
        ab.setCursor(Qt.PointingHandCursor)
        ab.setFixedHeight(brand.sp(38))
        ab.setStyleSheet(f"""
            QPushButton {{
                background: #7C3AED;
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #6D28D9; }}
        """)
        ab.clicked.connect(self._ai_degerlendirme)
        bl.addWidget(ab)

        sb = QPushButton("Kaydet")
        sb.setCursor(Qt.PointingHandCursor)
        sb.setFixedHeight(brand.sp(38))
        sb.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_8}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        sb.clicked.connect(self._save)
        bl.addWidget(sb)
        layout.addLayout(bl)

    def _tab_proses(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        lo.setSpacing(brand.SP_3)

        g = QGroupBox("Elektroliz Parametreleri")
        gl = QGridLayout(g)
        gl.setSpacing(brand.SP_3)

        gl.addWidget(QLabel("Akim (A):"), 0, 0)
        self.amper_input = QDoubleSpinBox()
        self.amper_input.setRange(0, 9999)
        self.amper_input.setDecimals(2)
        self.amper_input.setSuffix(" A")
        self.amper_input.setValue(self.data.get('amper', 0) or 0)
        gl.addWidget(self.amper_input, 0, 1)

        gl.addWidget(QLabel("Voltaj (V):"), 0, 2)
        self.volt_input = QDoubleSpinBox()
        self.volt_input.setRange(0, 9999)
        self.volt_input.setDecimals(2)
        self.volt_input.setSuffix(" V")
        self.volt_input.setValue(self.data.get('volt', 0) or 0)
        gl.addWidget(self.volt_input, 0, 3)

        gl.addWidget(QLabel("Sure (dk):"), 1, 0)
        self.sure_input = QDoubleSpinBox()
        self.sure_input.setRange(0, 9999)
        self.sure_input.setDecimals(1)
        self.sure_input.setSuffix(" dk")
        self.sure_input.setValue(self.data.get('sure_dk', 0) or 0)
        gl.addWidget(self.sure_input, 1, 1)

        gl.addWidget(QLabel("Sicaklik (C):"), 1, 2)
        self.sicaklik_input = QDoubleSpinBox()
        self.sicaklik_input.setRange(-10, 200)
        self.sicaklik_input.setDecimals(1)
        self.sicaklik_input.setSuffix(" C")
        self.sicaklik_input.setValue(self.data.get('sicaklik', 0) or 0)
        gl.addWidget(self.sicaklik_input, 1, 3)

        lo.addWidget(g)
        lo.addStretch()
        return w

    def _tab_kimyasal(self):
        w = QWidget()
        self.kimyasal_layout = QVBoxLayout(w)
        self.kimyasal_layout.setContentsMargins(
            brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4
        )
        self.kimyasal_container = QVBoxLayout()
        self.kimyasal_layout.addLayout(self.kimyasal_container)
        lbl = QLabel("Kaplama turu secildiginde kimyasal parametreler burada gorunecektir.")
        lbl.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY}px; "
            f"padding: {brand.SP_5}px;"
        )
        lbl.setAlignment(Qt.AlignCenter)
        self.kimyasal_container.addWidget(lbl)
        self.kimyasal_layout.addStretch()
        return w

    def _tab_kalinlik(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        lo.setSpacing(brand.SP_4)

        hl = QHBoxLayout()
        hl.setSpacing(brand.SP_5)

        ag = QGroupBox("Nokta A")
        af = QFormLayout(ag)
        af.setSpacing(brand.SP_3)
        self.kalinlik_a_input = QDoubleSpinBox()
        self.kalinlik_a_input.setRange(0, 9999)
        self.kalinlik_a_input.setDecimals(4)
        self.kalinlik_a_input.setSuffix(" u")
        self.kalinlik_a_input.setValue(self.data.get('kalinlik_a', 0) or 0)
        self.kalinlik_a_input.valueChanged.connect(self._hesapla_ab)
        af.addRow("Kalinlik:", self.kalinlik_a_input)
        self.sapma_a_input = QDoubleSpinBox()
        self.sapma_a_input.setRange(-100, 100)
        self.sapma_a_input.setDecimals(2)
        self.sapma_a_input.setSuffix(" %")
        self.sapma_a_input.setValue(self.data.get('sapma_a', 0) or 0)
        af.addRow("Sapma:", self.sapma_a_input)
        hl.addWidget(ag)

        bg = QGroupBox("Nokta B")
        bf = QFormLayout(bg)
        bf.setSpacing(brand.SP_3)
        self.kalinlik_b_input = QDoubleSpinBox()
        self.kalinlik_b_input.setRange(0, 9999)
        self.kalinlik_b_input.setDecimals(4)
        self.kalinlik_b_input.setSuffix(" u")
        self.kalinlik_b_input.setValue(self.data.get('kalinlik_b', 0) or 0)
        self.kalinlik_b_input.valueChanged.connect(self._hesapla_ab)
        bf.addRow("Kalinlik:", self.kalinlik_b_input)
        self.sapma_b_input = QDoubleSpinBox()
        self.sapma_b_input.setRange(-100, 100)
        self.sapma_b_input.setDecimals(2)
        self.sapma_b_input.setSuffix(" %")
        self.sapma_b_input.setValue(self.data.get('sapma_b', 0) or 0)
        bf.addRow("Sapma:", self.sapma_b_input)
        hl.addWidget(bg)
        lo.addLayout(hl)

        # A/B Orani
        of = QFrame()
        of.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; "
            f"border: 2px solid {brand.BORDER}; "
            f"border-radius: {brand.R_LG}px; "
            f"padding: {brand.SP_5}px; }}"
        )
        ol = QVBoxLayout(of)
        ot = QLabel("A / B Orani")
        ot.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_LG}px;"
        )
        ot.setAlignment(Qt.AlignCenter)
        ol.addWidget(ot)

        self.ab_oran_label = QLabel("-")
        self.ab_oran_label.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_DISPLAY}px; "
            f"font-weight: {brand.FW_BOLD};"
        )
        self.ab_oran_label.setAlignment(Qt.AlignCenter)
        ol.addWidget(self.ab_oran_label)

        self.ab_durum_label = QLabel("")
        self.ab_durum_label.setAlignment(Qt.AlignCenter)
        ol.addWidget(self.ab_durum_label)
        lo.addWidget(of)

        if self.data.get('kalinlik_a') and self.data.get('kalinlik_b'):
            self._hesapla_ab()
        lo.addStretch()
        return w

    def _tab_foto(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        lo.setSpacing(brand.SP_3)

        # Baslik + Ayarlar butonu
        header = QHBoxLayout()
        t_lbl = QLabel("Test Plakasi Fotografi")
        t_lbl.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(t_lbl)
        header.addStretch()

        ayar_btn = QPushButton("Klasor Ayarlari")
        ayar_btn.setCursor(Qt.PointingHandCursor)
        ayar_btn.setFixedHeight(brand.sp(38))
        ayar_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_3}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        """)
        ayar_btn.clicked.connect(self._foto_ayarlari)
        header.addWidget(ayar_btn)
        lo.addLayout(header)

        i = QLabel(
            "Test plakasinin fotografini secin. Fotograf belirlenen klasore kopyalanacaktir."
        )
        i.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;"
        )
        lo.addWidget(i)

        self.foto_widget = FotoSeciciWidget(
            self.theme, mevcut_yol=self.data.get('foto_yolu')
        )
        lo.addWidget(self.foto_widget, 1)

        self.foto_klasor_label = QLabel(f"Kayit klasoru: {get_foto_klasoru()}")
        self.foto_klasor_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"
        )
        self.foto_klasor_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lo.addWidget(self.foto_klasor_label)
        return w

    def _foto_ayarlari(self):
        """Fotograf klasor ayarlari dialogunu ac"""
        dlg = FotoAyarlariDialog(self.theme, self)
        if dlg.exec() == QDialog.Accepted:
            self.foto_klasor_label.setText(f"Kayit klasoru: {get_foto_klasoru()}")

    def _tab_sonuc(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        lo.setSpacing(brand.SP_3)

        sg = QGroupBox("Sonuc")
        sf = QFormLayout(sg)
        sf.setSpacing(brand.SP_3)
        self.sonuc_combo = QComboBox()
        self.sonuc_combo.addItem("Beklemede", "BEKLEMEDE")
        self.sonuc_combo.addItem("Uygun", "UYGUN")
        self.sonuc_combo.addItem("Uygun Degil", "UYGUN_DEGIL")
        idx = self.sonuc_combo.findData(self.data.get('sonuc', 'BEKLEMEDE'))
        if idx >= 0:
            self.sonuc_combo.setCurrentIndex(idx)
        sf.addRow("Sonuc:", self.sonuc_combo)
        lo.addWidget(sg)

        ng = QGroupBox("Notlar")
        nl = QVBoxLayout(ng)
        self.notlar_input = QTextEdit()
        self.notlar_input.setPlaceholderText("Test ile ilgili notlar...")
        self.notlar_input.setText(self.data.get('notlar', '') or '')
        self.notlar_input.setMaximumHeight(brand.sp(100))
        nl.addWidget(self.notlar_input)
        lo.addWidget(ng)

        aig = QGroupBox("AI Degerlendirmesi")
        ail = QVBoxLayout(aig)
        self.ai_yorum_text = QTextEdit()
        self.ai_yorum_text.setReadOnly(True)
        self.ai_yorum_text.setText(self.data.get('ai_yorum', '') or '')
        self.ai_yorum_text.setStyleSheet(
            f"background: {brand.BG_INPUT}; "
            f"border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_SM}px; "
            f"padding: {brand.SP_3}px; "
            f"color: {brand.TEXT}; "
            f"font-family: Consolas; "
            f"font-size: {brand.FS_BODY_SM}px;"
        )
        ail.addWidget(self.ai_yorum_text)
        lo.addWidget(aig, 1)
        return w

    # --- TDS Kontrol Noktalari ---
    def _tab_tds_kontrol(self):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        lo.setSpacing(brand.SP_3)

        # Ust bilgi
        info_bar = QHBoxLayout()
        self.tds_info_label = QLabel("Banyo seciniz - TDS kontrol noktalari otomatik yuklenecek")
        self.tds_info_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY}px;"
        )
        info_bar.addWidget(self.tds_info_label)
        info_bar.addStretch()

        self.tds_kontrol_btn = QPushButton("Kontrol Et")
        self.tds_kontrol_btn.setCursor(Qt.PointingHandCursor)
        self.tds_kontrol_btn.setFixedHeight(brand.sp(38))
        self.tds_kontrol_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        self.tds_kontrol_btn.clicked.connect(self._run_tds_kontrol)
        self.tds_kontrol_btn.setEnabled(False)
        info_bar.addWidget(self.tds_kontrol_btn)
        lo.addLayout(info_bar)

        # Genel durum gostergesi
        self.tds_durum_frame = QFrame()
        self.tds_durum_frame.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_LG}px; "
            f"padding: {brand.SP_3}px; }}"
        )
        durum_lo = QHBoxLayout(self.tds_durum_frame)
        self.tds_durum_label = QLabel("Henuz kontrol yapilmadi")
        self.tds_durum_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; "
            f"font-size: {brand.FS_BODY_LG}px; "
            f"font-weight: {brand.FW_BOLD};"
        )
        durum_lo.addWidget(self.tds_durum_label)
        durum_lo.addStretch()
        self.tds_sorun_label = QLabel("")
        self.tds_sorun_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;"
        )
        durum_lo.addWidget(self.tds_sorun_label)
        lo.addWidget(self.tds_durum_frame)

        # Kontrol noktalari tablosu
        grp = QGroupBox("Kontrol Noktalari")
        g_lo = QVBoxLayout(grp)

        self.tds_kontrol_table = QTableWidget()
        self.tds_kontrol_table.setColumnCount(7)
        self.tds_kontrol_table.setHorizontalHeaderLabels([
            "Parametre", "Birim", "TDS Min", "TDS Hedef", "TDS Max", "Gercek", "Durum"
        ])
        self.tds_kontrol_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tds_kontrol_table.setColumnWidth(1, brand.sp(60))
        self.tds_kontrol_table.setColumnWidth(2, brand.sp(75))
        self.tds_kontrol_table.setColumnWidth(3, brand.sp(75))
        self.tds_kontrol_table.setColumnWidth(4, brand.sp(75))
        self.tds_kontrol_table.setColumnWidth(5, brand.sp(85))
        self.tds_kontrol_table.setColumnWidth(6, brand.sp(90))
        self.tds_kontrol_table.verticalHeader().setVisible(False)
        self.tds_kontrol_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.tds_kontrol_table.setShowGrid(False)
        self.tds_kontrol_table.setAlternatingRowColors(True)
        self.tds_kontrol_table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked
        )
        self.tds_kontrol_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tds_kontrol_table.setStyleSheet(self._table_css())
        g_lo.addWidget(self.tds_kontrol_table)
        lo.addWidget(grp, 1)

        # Sorun ve oneriler
        alt_lo = QHBoxLayout()
        alt_lo.setSpacing(brand.SP_3)

        sorun_grp = QGroupBox("Sorunlar")
        s_lo = QVBoxLayout(sorun_grp)
        self.tds_sorunlar_text = QTextEdit()
        self.tds_sorunlar_text.setReadOnly(True)
        self.tds_sorunlar_text.setMaximumHeight(brand.sp(120))
        s_lo.addWidget(self.tds_sorunlar_text)
        alt_lo.addWidget(sorun_grp)

        oneri_grp = QGroupBox("Oneriler")
        o_lo = QVBoxLayout(oneri_grp)
        self.tds_oneriler_text = QTextEdit()
        self.tds_oneriler_text.setReadOnly(True)
        self.tds_oneriler_text.setMaximumHeight(brand.sp(120))
        o_lo.addWidget(self.tds_oneriler_text)
        alt_lo.addWidget(oneri_grp)
        lo.addLayout(alt_lo)

        return w

    def _table_css(self):
        """Standart tablo CSS - El Kitabi v3"""
        return f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_2}px {brand.SP_3}px;
                border-bottom: 1px solid {brand.BORDER};
                color: {brand.TEXT};
            }}
            QTableWidget::item:alternate {{ background: {brand.BG_MAIN}; }}
            QTableWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """

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
                f"color: {brand.SUCCESS}; "
                f"font-size: {brand.FS_BODY}px; "
                f"font-weight: {brand.FW_BOLD};"
            )

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
                col_map = {
                    "sicaklik": 0, "ph": 1, "iletkenlik": 2, "kati_madde": 3,
                    "pb_orani": 4, "solvent": 5, "meq": 6,
                    "toplam_asit": 7, "serbest_asit": 8
                }
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
                try:
                    conn.close()
                except Exception:
                    pass

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
                ("sicaklik", "Sicaklik", "C", 0, 1, 2),
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
                self.tds_info_label.setStyleSheet(
                    f"color: {brand.WARNING}; font-size: {brand.FS_BODY}px;"
                )
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
            self.tds_kontrol_table.setItem(
                i, 0, self._make_readonly_item(p.get("parametre_adi", "")))
            self.tds_kontrol_table.setItem(
                i, 1, self._make_readonly_item(p.get("birim", "")))
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
                gercek_item.setForeground(QColor(brand.TEXT_DIM))
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
                self.tds_kontrol_table.setItem(
                    i, 0, QTableWidgetItem(k.get("parametre", "")))
                self.tds_kontrol_table.setItem(
                    i, 1, QTableWidgetItem(k.get("birim", "")))
                self.tds_kontrol_table.setItem(i, 2, QTableWidgetItem(
                    f"{k['tds_min']:.2f}" if k.get("tds_min") else "-"))
                self.tds_kontrol_table.setItem(i, 3, QTableWidgetItem(
                    f"{k['tds_hedef']:.2f}" if k.get("tds_hedef") else "-"))
                self.tds_kontrol_table.setItem(i, 4, QTableWidgetItem(
                    f"{k['tds_max']:.2f}" if k.get("tds_max") else "-"))

                gercek = k.get("gercek")
                if gercek is not None:
                    self.tds_kontrol_table.setItem(
                        i, 5, QTableWidgetItem(f"{gercek:.2f}"))
                else:
                    self.tds_kontrol_table.setItem(
                        i, 5, QTableWidgetItem("--"))

                durum = k.get("durum", "")
                durum_item = QTableWidgetItem(durum)
                durum_renk = {
                    "NORMAL": brand.SUCCESS, "UYARI": brand.WARNING,
                    "KRITIK": brand.ERROR, "DUSUK": brand.WARNING,
                    "YUKSEK": brand.WARNING, "OLCUM_YOK": brand.TEXT_DIM,
                }
                durum_item.setForeground(QColor(durum_renk.get(durum, brand.TEXT)))
                if k.get("kritik"):
                    font = durum_item.font()
                    font.setBold(True)
                    durum_item.setFont(font)
                self.tds_kontrol_table.setItem(i, 6, durum_item)

            # Genel durum
            genel = sonuc.get("genel_durum", "UYGUN")
            durum_map = {
                "UYGUN": ("UYGUN", brand.SUCCESS),
                "DIKKAT": ("DIKKAT", brand.WARNING),
                "KRITIK": ("KRITIK", brand.ERROR),
            }
            txt, renk = durum_map.get(genel, ("?", brand.TEXT))
            self.tds_durum_label.setText(f"Genel Durum: {txt}")
            self.tds_durum_label.setStyleSheet(
                f"color: {renk}; "
                f"font-size: {brand.FS_BODY_LG}px; "
                f"font-weight: {brand.FW_BOLD};"
            )
            self.tds_durum_frame.setStyleSheet(
                f"QFrame {{ background: {brand.BG_CARD}; "
                f"border: 2px solid {renk}; "
                f"border-radius: {brand.R_LG}px; "
                f"padding: {brand.SP_3}px; }}"
            )

            sorunlar = sonuc.get("sorunlar", [])
            self.tds_sorun_label.setText(
                f"{len(sorunlar)} sorun tespit edildi" if sorunlar else "Sorun yok"
            )

            # Sorunlar ve oneriler
            self.tds_sorunlar_text.setPlainText(
                "\n".join(f"- {s}" for s in sorunlar) if sorunlar
                else "Sorun tespit edilmedi."
            )
            oneriler = sonuc.get("oneriler", [])
            self.tds_oneriler_text.setPlainText(
                "\n".join(f"* {o}" for o in oneriler) if oneriler
                else "Oneri yok."
            )

        except Exception as e:
            QMessageBox.critical(self, "TDS Kontrol Hatasi", str(e))
            import traceback
            traceback.print_exc()

    # --- Yardimcilar ---
    def _load_banyolar(self):
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT b.id, b.kod, b.ad, h.kod "
                "FROM uretim.banyo_tanimlari b "
                "JOIN tanim.uretim_hatlari h ON b.hat_id=h.id "
                "WHERE b.aktif_mi=1 ORDER BY h.sira_no, b.kod"
            )
            for r in cur.fetchall():
                self.banyo_combo.addItem(f"{r[3]} / {r[1]} - {r[2]}", r[0])
            if self.data.get('banyo_id'):
                idx = self.banyo_combo.findData(self.data['banyo_id'])
                if idx >= 0:
                    self.banyo_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_kaplama_turleri(self):
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, kod, ad FROM laboratuvar.kaplama_turleri "
                "WHERE aktif_mi=1 ORDER BY sira_no"
            )
            for r in cur.fetchall():
                self.kaplama_turu_combo.addItem(f"{r[1]} - {r[2]}", r[0])
            if self.data.get('kaplama_turu_id'):
                idx = self.kaplama_turu_combo.findData(self.data['kaplama_turu_id'])
                if idx >= 0:
                    self.kaplama_turu_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_analistler(self):
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, ad, soyad FROM ik.personeller "
                "WHERE aktif_mi=1 ORDER BY ad"
            )
            for r in cur.fetchall():
                self.analist_combo.addItem(f"{r[1]} {r[2]}", r[0])
            if self.data.get('analist_id'):
                idx = self.analist_combo.findData(self.data['analist_id'])
                if idx >= 0:
                    self.analist_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_kimyasal_parametreler(self):
        kt_id = self.kaplama_turu_combo.currentData()
        self.kimyasal_inputs.clear()
        self.kimyasal_params.clear()
        while self.kimyasal_container.count():
            item = self.kimyasal_container.takeAt(0)
            ww = item.widget()
            if ww:
                ww.deleteLater()
        if not kt_id:
            lbl = QLabel("Kaplama turu secildiginde parametreler gorunecektir.")
            lbl.setStyleSheet(
                f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY}px; "
                f"padding: {brand.SP_5}px;"
            )
            lbl.setAlignment(Qt.AlignCenter)
            self.kimyasal_container.addWidget(lbl)
            return
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, parametre_kodu, parametre_adi, birim, min_deger, "
                "max_deger, hedef_deger "
                "FROM laboratuvar.kaplama_kimyasal_parametreleri "
                "WHERE kaplama_turu_id=? AND aktif_mi=1 ORDER BY sira_no",
                (kt_id,)
            )
            params = cur.fetchall()
            if not params:
                lbl = QLabel("Bu kaplama turu icin kimyasal parametre tanimlanmamis.")
                lbl.setStyleSheet(
                    f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY}px; "
                    f"padding: {brand.SP_5}px;"
                )
                lbl.setAlignment(Qt.AlignCenter)
                self.kimyasal_container.addWidget(lbl)
                return
            mevcut = {}
            if self.test_id:
                c2 = None
                try:
                    c2 = get_db_connection()
                    cu2 = c2.cursor()
                    cu2.execute(
                        "SELECT parametre_id, deger "
                        "FROM laboratuvar.kaplama_test_kimyasallari WHERE test_id=?",
                        (self.test_id,)
                    )
                    for r in cu2.fetchall():
                        mevcut[r[0]] = r[1]
                except Exception:
                    pass
                finally:
                    if c2:
                        try:
                            c2.close()
                        except Exception:
                            pass
            grp = QGroupBox("Banyo Kimyasal Degerleri")
            frm = QFormLayout(grp)
            frm.setSpacing(brand.SP_3)
            for p in params:
                pid, pkod, padi, birim, mn, mx, hd = p
                rl = QHBoxLayout()
                sb = QDoubleSpinBox()
                sb.setRange(0, 99999)
                sb.setDecimals(4)
                if birim:
                    sb.setSuffix(f" {birim}")
                sb.setValue(float(mevcut.get(pid, 0) or 0))
                sb.setMinimumWidth(brand.sp(150))
                rl.addWidget(sb)
                lt = ""
                if mn and mx:
                    lt = f"  [{mn:.2f} - {mx:.2f}]"
                    if hd:
                        lt += f" Hedef: {hd:.2f}"
                ll = QLabel(lt)
                ll.setStyleSheet(
                    f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"
                )
                rl.addWidget(ll)
                rl.addStretch()
                cw = QWidget()
                cw.setLayout(rl)
                frm.addRow(f"{padi}:", cw)
                self.kimyasal_inputs.append(sb)
                self.kimyasal_params.append({
                    'id': pid, 'kod': pkod, 'adi': padi, 'birim': birim,
                    'min': float(mn) if mn else None,
                    'max': float(mx) if mx else None,
                    'hedef': float(hd) if hd else None,
                })
            self.kimyasal_container.addWidget(grp)
        except Exception as e:
            el = QLabel(f"Hata: {e}")
            el.setStyleSheet(f"color: {brand.ERROR};")
            self.kimyasal_container.addWidget(el)
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _hesapla_ab(self):
        a, b = self.kalinlik_a_input.value(), self.kalinlik_b_input.value()
        if a > 0 and b > 0:
            o = a / b
            self.ab_oran_label.setText(f"{o:.2f}")
            if o <= 1.5:
                self.ab_oran_label.setStyleSheet(
                    f"color: {brand.SUCCESS}; "
                    f"font-size: {brand.FS_DISPLAY}px; "
                    f"font-weight: {brand.FW_BOLD};"
                )
                self.ab_durum_label.setText("Mukemmel")
                self.ab_durum_label.setStyleSheet(
                    f"color: {brand.SUCCESS}; font-size: {brand.FS_BODY_LG}px;"
                )
            elif o <= 2.0:
                self.ab_oran_label.setStyleSheet(
                    f"color: {brand.WARNING}; "
                    f"font-size: {brand.FS_DISPLAY}px; "
                    f"font-weight: {brand.FW_BOLD};"
                )
                self.ab_durum_label.setText("Kabul edilebilir")
                self.ab_durum_label.setStyleSheet(
                    f"color: {brand.WARNING}; font-size: {brand.FS_BODY_LG}px;"
                )
            elif o <= 3.0:
                self.ab_oran_label.setStyleSheet(
                    f"color: {brand.ERROR}; "
                    f"font-size: {brand.FS_DISPLAY}px; "
                    f"font-weight: {brand.FW_BOLD};"
                )
                self.ab_durum_label.setText("Homojenlik dusuk")
                self.ab_durum_label.setStyleSheet(
                    f"color: {brand.ERROR}; font-size: {brand.FS_BODY_LG}px;"
                )
            else:
                self.ab_oran_label.setStyleSheet(
                    f"color: {brand.ERROR}; "
                    f"font-size: {brand.FS_DISPLAY}px; "
                    f"font-weight: {brand.FW_BOLD};"
                )
                self.ab_durum_label.setText("Kritik!")
                self.ab_durum_label.setStyleSheet(
                    f"color: {brand.ERROR}; "
                    f"font-size: {brand.FS_BODY_LG}px; "
                    f"font-weight: {brand.FW_BOLD};"
                )
        else:
            self.ab_oran_label.setText("-")
            self.ab_oran_label.setStyleSheet(
                f"color: {brand.TEXT_DIM}; "
                f"font-size: {brand.FS_DISPLAY}px; "
                f"font-weight: {brand.FW_BOLD};"
            )
            self.ab_durum_label.setText("")

    def _ai_degerlendirme(self):
        kims = []
        for i, p in enumerate(self.kimyasal_params):
            if i < len(self.kimyasal_inputs):
                kims.append({
                    'parametre_adi': p['adi'],
                    'deger': self.kimyasal_inputs[i].value(),
                    'min': p.get('min'),
                    'max': p.get('max'),
                    'hedef': p.get('hedef'),
                })
        av, bv = self.kalinlik_a_input.value(), self.kalinlik_b_input.value()
        td = {
            'kaplama_turu': self.kaplama_turu_combo.currentText() or '',
            'amper': self.amper_input.value(),
            'volt': self.volt_input.value(),
            'sure_dk': self.sure_input.value(),
            'sicaklik': self.sicaklik_input.value(),
            'kalinlik_a': av,
            'kalinlik_b': bv,
            'ab_orani': (av / bv) if bv > 0 else 0,
            'sapma_a': self.sapma_a_input.value(),
            'sapma_b': self.sapma_b_input.value(),
            'kimyasallar': kims,
        }
        yorum = generate_ai_yorum(td, self.tds_parametreler, self.tds_banyo_olcumler)
        self.ai_yorum_text.setText(yorum)
        if "KRITIK" in yorum:
            idx = self.sonuc_combo.findData("UYGUN_DEGIL")
            if idx >= 0:
                self.sonuc_combo.setCurrentIndex(idx)
        elif "UYGUN" in yorum and "DIKKAT" not in yorum:
            idx = self.sonuc_combo.findData("UYGUN")
            if idx >= 0:
                self.sonuc_combo.setCurrentIndex(idx)

    def _save(self):
        banyo_id = self.banyo_combo.currentData()
        kt_id = self.kaplama_turu_combo.currentData()
        analist_id = self.analist_combo.currentData()
        if not banyo_id or not kt_id or not analist_id:
            QMessageBox.warning(
                self, "Uyari",
                "Banyo, Kaplama Turu ve Analist secimi zorunludur!"
            )
            return
        av = self.kalinlik_a_input.value() or None
        bv = self.kalinlik_b_input.value() or None
        ab = (av / bv) if av and bv and bv > 0 else None

        # Fotograf
        foto_db = self.data.get('foto_yolu')
        kaynak = self.foto_widget.get_kaynak_yol()
        secili = self.foto_widget.get_foto_yolu()
        if kaynak:
            foto_db = foto_kaydet(kaynak, self.data.get('test_no', 'YENI'))
        elif not secili:
            foto_db = None

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            params = (
                banyo_id, kt_id, self.tarih_input.dateTime().toPython(), analist_id,
                self.amper_input.value() or None, self.volt_input.value() or None,
                self.sure_input.value() or None, self.sicaklik_input.value() or None,
                av, self.sapma_a_input.value() or None,
                bv, self.sapma_b_input.value() or None, ab,
                foto_db, self.sonuc_combo.currentData(),
                self.ai_yorum_text.toPlainText().strip() or None,
                datetime.now() if self.ai_yorum_text.toPlainText().strip() else None,
                self.notlar_input.toPlainText().strip() or None,
            )
            if self.test_id:
                cur.execute("""UPDATE laboratuvar.kaplama_testleri SET
                    banyo_id=?, kaplama_turu_id=?, test_tarihi=?, analist_id=?,
                    amper=?, volt=?, sure_dk=?, sicaklik=?,
                    kalinlik_a=?, sapma_a=?, kalinlik_b=?, sapma_b=?, ab_orani=?,
                    foto_yolu=?, sonuc=?, ai_yorum=?, ai_yorum_tarihi=?, notlar=?,
                    guncelleme_tarihi=GETDATE() WHERE id=?""", params + (self.test_id,))
                cur.execute(
                    "DELETE FROM laboratuvar.kaplama_test_kimyasallari WHERE test_id=?",
                    (self.test_id,)
                )
                tid = self.test_id
            else:
                cur.execute("""INSERT INTO laboratuvar.kaplama_testleri
                    (banyo_id, kaplama_turu_id, test_tarihi, analist_id,
                     amper, volt, sure_dk, sicaklik,
                     kalinlik_a, sapma_a, kalinlik_b, sapma_b, ab_orani,
                     foto_yolu, sonuc, ai_yorum, ai_yorum_tarihi, notlar)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", params)
                cur.execute("SELECT @@IDENTITY")
                tid = cur.fetchone()[0]
            for i, p in enumerate(self.kimyasal_params):
                if i < len(self.kimyasal_inputs):
                    d = self.kimyasal_inputs[i].value()
                    if d > 0:
                        dur = 'NORMAL'
                        if p.get('min') and d < p['min']:
                            dur = 'DUSUK'
                        elif p.get('max') and d > p['max']:
                            dur = 'YUKSEK'
                        cur.execute(
                            "INSERT INTO laboratuvar.kaplama_test_kimyasallari "
                            "(test_id, parametre_id, deger, durum) VALUES (?,?,?,?)",
                            (tid, p['id'], d, dur)
                        )
            conn.commit()

            # Yeni kayitsa fotografi test_no ile yeniden adlandir
            if not self.test_id and foto_db and kaynak:
                cur.execute(
                    "SELECT test_no FROM laboratuvar.kaplama_testleri WHERE id=?",
                    (tid,)
                )
                tno = cur.fetchone()
                if tno and tno[0]:
                    yeni = foto_kaydet(kaynak, tno[0])
                    if yeni and yeni != foto_db:
                        cur.execute(
                            "UPDATE laboratuvar.kaplama_testleri SET foto_yolu=? WHERE id=?",
                            (yeni, tid)
                        )
                        conn.commit()
                        try:
                            if os.path.exists(foto_db) and foto_db != kaynak:
                                os.remove(foto_db)
                        except Exception:
                            pass
            QMessageBox.information(
                self, "Basarili", "Kaplama test kaydi basariyla kaydedildi!"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit hatasi:\n{str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# =====================================================================
# KAPLAMA TEST LISTE SAYFASI
# =====================================================================
class LabKaplamaTestPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_4)

        # Header
        header = self.create_page_header(
            "Kaplama Test Kayitlari",
            "Kaplama kalinlik testlerini kaydedin ve takip edin"
        )
        layout.addLayout(header)

        # KPI Kartlari
        sl = QHBoxLayout()
        sl.setSpacing(brand.SP_3)
        self.card_toplam = self.create_stat_card("TOPLAM TEST", "0", color=brand.INFO)
        self.card_uygun = self.create_stat_card("UYGUN", "0", color=brand.SUCCESS)
        self.card_uygun_degil = self.create_stat_card("UYGUN DEGIL", "0", color=brand.ERROR)
        self.card_beklemede = self.create_stat_card("BEKLEMEDE", "0", color=brand.WARNING)
        sl.addWidget(self.card_toplam)
        sl.addWidget(self.card_uygun)
        sl.addWidget(self.card_uygun_degil)
        sl.addWidget(self.card_beklemede)
        layout.addLayout(sl)

        # Toolbar
        _input_css = f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """
        tb = QHBoxLayout()
        tb.setSpacing(brand.SP_3)

        self.banyo_combo = QComboBox()
        self.banyo_combo.addItem("Tum Banyolar", None)
        self._load_banyo_filter()
        self.banyo_combo.setMinimumWidth(brand.sp(200))
        self.banyo_combo.setStyleSheet(_input_css)
        self.banyo_combo.currentIndexChanged.connect(self._load_data)
        tb.addWidget(self.banyo_combo)

        self.kaplama_combo = QComboBox()
        self.kaplama_combo.addItem("Tum Kaplama Turleri", None)
        self._load_kaplama_filter()
        self.kaplama_combo.setMinimumWidth(brand.sp(150))
        self.kaplama_combo.setStyleSheet(_input_css)
        self.kaplama_combo.currentIndexChanged.connect(self._load_data)
        tb.addWidget(self.kaplama_combo)

        self.sonuc_combo = QComboBox()
        self.sonuc_combo.addItem("Tum Sonuclar", None)
        self.sonuc_combo.addItem("Uygun", "UYGUN")
        self.sonuc_combo.addItem("Uygun Degil", "UYGUN_DEGIL")
        self.sonuc_combo.addItem("Beklemede", "BEKLEMEDE")
        self.sonuc_combo.setMinimumWidth(brand.sp(120))
        self.sonuc_combo.setStyleSheet(_input_css)
        self.sonuc_combo.currentIndexChanged.connect(self._load_data)
        tb.addWidget(self.sonuc_combo)

        tb.addStretch()

        add_btn = QPushButton("Yeni Test")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(brand.sp(38))
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_new)
        tb.addWidget(add_btn)
        layout.addLayout(tb)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "ID", "Test No", "Tarih", "Banyo", "Kaplama", "Analist",
            "A (u)", "B (u)", "A/B", "Amper", "Sicaklik", "Foto", "Sonuc", "Islem"
        ])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        for col, w in [
            (0, 50), (1, 110), (2, 120), (4, 80), (5, 110),
            (6, 65), (7, 65), (8, 55), (9, 65), (10, 70),
            (11, 40), (12, 95), (13, 170)
        ]:
            self.table.setColumnWidth(col, brand.sp(w))
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_2}px {brand.SP_3}px;
                border-bottom: 1px solid {brand.BORDER};
                color: {brand.TEXT};
            }}
            QTableWidget::item:alternate {{ background: {brand.BG_MAIN}; }}
            QTableWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """)
        layout.addWidget(self.table, 1)

    def _load_banyo_filter(self):
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT b.id, b.kod, h.kod "
                "FROM uretim.banyo_tanimlari b "
                "JOIN tanim.uretim_hatlari h ON b.hat_id=h.id "
                "WHERE b.aktif_mi=1 ORDER BY h.sira_no, b.kod"
            )
            for r in cur.fetchall():
                self.banyo_combo.addItem(f"{r[2]} / {r[1]}", r[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_kaplama_filter(self):
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, kod, ad FROM laboratuvar.kaplama_turleri "
                "WHERE aktif_mi=1 ORDER BY sira_no"
            )
            for r in cur.fetchall():
                self.kaplama_combo.addItem(f"{r[1]} - {r[2]}", r[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            sql = """SELECT t.id, t.test_no, t.test_tarihi, b.kod, kt.kod,
                       p.ad+' '+p.soyad,
                       t.kalinlik_a, t.kalinlik_b, t.ab_orani,
                       t.amper, t.sicaklik, t.foto_yolu, t.sonuc
                FROM laboratuvar.kaplama_testleri t
                JOIN uretim.banyo_tanimlari b ON t.banyo_id=b.id
                JOIN laboratuvar.kaplama_turleri kt ON t.kaplama_turu_id=kt.id
                JOIN ik.personeller p ON t.analist_id=p.id
                WHERE t.silindi_mi=0"""
            prm = []
            bid = self.banyo_combo.currentData()
            if bid:
                sql += " AND t.banyo_id=?"
                prm.append(bid)
            kid = self.kaplama_combo.currentData()
            if kid:
                sql += " AND t.kaplama_turu_id=?"
                prm.append(kid)
            sf = self.sonuc_combo.currentData()
            if sf:
                sql += " AND t.sonuc=?"
                prm.append(sf)
            sql += " ORDER BY t.test_tarihi DESC"
            cur.execute(sql, prm)
            rows = cur.fetchall()

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
                self.table.setItem(i, 2, QTableWidgetItem(
                    r[2].strftime("%d.%m.%Y %H:%M") if r[2] else '-'))
                self.table.setItem(i, 3, QTableWidgetItem(r[3] or ''))
                self.table.setItem(i, 4, QTableWidgetItem(r[4] or ''))
                self.table.setItem(i, 5, QTableWidgetItem(r[5] or ''))
                self.table.setItem(i, 6, QTableWidgetItem(
                    f"{r[6]:.2f}" if r[6] else '-'))
                self.table.setItem(i, 7, QTableWidgetItem(
                    f"{r[7]:.2f}" if r[7] else '-'))

                ab_item = QTableWidgetItem(f"{r[8]:.2f}" if r[8] else '-')
                if r[8]:
                    if r[8] <= 1.5:
                        ab_item.setForeground(QColor(brand.SUCCESS))
                    elif r[8] <= 2.0:
                        ab_item.setForeground(QColor(brand.WARNING))
                    else:
                        ab_item.setForeground(QColor(brand.ERROR))
                self.table.setItem(i, 8, ab_item)

                self.table.setItem(i, 9, QTableWidgetItem(
                    f"{r[9]:.1f}A" if r[9] else '-'))
                self.table.setItem(i, 10, QTableWidgetItem(
                    f"{r[10]:.0f}C" if r[10] else '-'))

                # Fotograf ikonu
                foto_item = QTableWidgetItem("Var" if r[11] else "-")
                if r[11]:
                    foto_item.setToolTip(r[11])
                self.table.setItem(i, 11, foto_item)

                smap = {
                    "UYGUN": "Uygun",
                    "UYGUN_DEGIL": "Uyg.Degil",
                    "BEKLEMEDE": "Bekleme",
                }
                scol = {
                    "UYGUN": brand.SUCCESS,
                    "UYGUN_DEGIL": brand.ERROR,
                    "BEKLEMEDE": brand.WARNING,
                }
                si = QTableWidgetItem(smap.get(r[12], r[12] or ''))
                si.setForeground(QColor(scol.get(r[12], brand.TEXT)))
                self.table.setItem(i, 12, si)

                # Islem butonlari
                buttons = [
                    ("Duzenle", "Duzenle",
                     lambda checked, rid=r[0]: self._edit_item(rid), "edit"),
                ]
                if r[11]:
                    buttons.append(
                        ("Foto", "Fotograf",
                         lambda checked, fp=r[11]: self._view_foto(fp), "photo")
                    )
                buttons.append(
                    ("Sil", "Sil",
                     lambda checked, rid=r[0]: self._delete_item(rid), "delete")
                )
                widget = self.create_action_buttons(buttons)
                self.table.setCellWidget(i, 13, widget)

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _add_new(self):
        dlg = KaplamaTestDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _edit_item(self, tid):
        dlg = KaplamaTestDialog(self.theme, tid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _view_foto(self, foto_yolu):
        FotoOnizlemeDialog(foto_yolu, self.theme, self).exec()

    def _delete_item(self, tid):
        if QMessageBox.question(
            self, "Onay",
            "Bu test kaydini silmek istediginize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE laboratuvar.kaplama_testleri SET silindi_mi=1 WHERE id=?",
                    (tid,)
                )
                conn.commit()
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
