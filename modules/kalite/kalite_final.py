# -*- coding: utf-8 -*-
"""
NEXOR ERP - Proses Kalite Kontrol Sayfasi
==========================================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
Lot bazli kalite kontrol, hata kayit ve etiket basma
"""
import os
import subprocess
import tempfile
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QSpinBox, QTextEdit, QSplitter, QWidget, QGridLayout,
    QDoubleSpinBox, QInputDialog, QGroupBox, QListWidget, QListWidgetItem,
    QDialogButtonBox
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QColor, QFont, QPixmap
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand

# Etiket ayarlari (sonra sistem ayarlarindan gelecek)
ETIKET_YAZICI = "Godex G500"  # Windows yazici adi
ETIKET_BOYUT = (100, 50)  # mm
from config import NAS_PATHS
NAS_IMAGE_PATH = NAS_PATHS["image_path"]


# =====================================================================
# DIALOG STYLES — ortak
# =====================================================================

_DIALOG_BASE_CSS = f"""
    QDialog {{
        background: {brand.BG_MAIN};
        font-family: {brand.FONT_FAMILY};
    }}
    QLabel {{ color: {brand.TEXT}; background: transparent; }}
    QGroupBox {{
        color: {brand.TEXT};
        font-size: {brand.FS_BODY}px;
        font-weight: {brand.FW_SEMIBOLD};
        border: 1px solid {brand.BORDER};
        border-radius: {brand.R_LG}px;
        margin-top: {brand.SP_5}px;
        padding: {brand.SP_5}px;
        padding-top: {brand.SP_8}px;
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

_INPUT_CSS = f"""
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{
        background: {brand.BG_INPUT};
        color: {brand.TEXT};
        border: 1px solid {brand.BORDER};
        border-radius: {brand.R_SM}px;
        padding: {brand.SP_2}px {brand.SP_3}px;
        font-size: {brand.FS_BODY}px;
    }}
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {{
        border-color: {brand.PRIMARY};
    }}
"""

_BTN_GHOST_CSS = f"""
    QPushButton {{
        background: {brand.BG_CARD};
        color: {brand.TEXT};
        border: 1px solid {brand.BORDER};
        border-radius: {brand.R_SM}px;
        padding: 0 {brand.SP_5}px;
        font-size: {brand.FS_BODY}px;
        font-weight: {brand.FW_MEDIUM};
        min-height: {brand.sp(38)}px;
    }}
    QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
"""

_BTN_PRIMARY_CSS = f"""
    QPushButton {{
        background: {brand.PRIMARY};
        color: white;
        border: none;
        border-radius: {brand.R_SM}px;
        padding: 0 {brand.SP_6}px;
        font-size: {brand.FS_BODY}px;
        font-weight: {brand.FW_SEMIBOLD};
        min-height: {brand.sp(38)}px;
    }}
    QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
    QPushButton:disabled {{
        background: {brand.BG_HOVER};
        color: {brand.TEXT_MUTED};
    }}
"""

_BTN_SUCCESS_CSS = f"""
    QPushButton {{
        background: {brand.SUCCESS};
        color: white;
        border: none;
        border-radius: {brand.R_SM}px;
        padding: 0 {brand.SP_6}px;
        font-size: {brand.FS_BODY}px;
        font-weight: {brand.FW_SEMIBOLD};
        min-height: {brand.sp(38)}px;
    }}
    QPushButton:hover {{ background: #059669; }}
    QPushButton:disabled {{
        background: {brand.BG_HOVER};
        color: {brand.TEXT_MUTED};
    }}
"""

_BTN_WARNING_CSS = f"""
    QPushButton {{
        background: {brand.WARNING};
        color: white;
        border: none;
        border-radius: {brand.R_SM}px;
        padding: 0 {brand.SP_5}px;
        font-size: {brand.FS_BODY}px;
        font-weight: {brand.FW_SEMIBOLD};
        min-height: {brand.sp(38)}px;
    }}
    QPushButton:hover {{ opacity: 0.9; }}
"""

_TABLE_CSS = f"""
    QTableWidget {{
        background: {brand.BG_CARD};
        border: 1px solid {brand.BORDER};
        border-radius: {brand.R_LG}px;
        outline: none;
    }}
    QTableWidget::item {{
        padding: {brand.SP_3}px {brand.SP_4}px;
        border-bottom: 1px solid {brand.BORDER};
        color: {brand.TEXT};
    }}
    QTableWidget::item:alternate {{ background: {brand.BG_MAIN}; }}
    QTableWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
    QHeaderView::section {{
        background: {brand.BG_SURFACE};
        color: {brand.TEXT_MUTED};
        padding: {brand.SP_3}px {brand.SP_4}px;
        border: none;
        border-bottom: 2px solid {brand.PRIMARY};
        font-size: {brand.FS_BODY_SM}px;
        font-weight: {brand.FW_SEMIBOLD};
    }}
"""


# =====================================================================
# DIALOG: Etiket Onizleme
# =====================================================================

class EtiketOnizlemeDialog(QDialog):
    """Etiket onizleme ve yazdirma dialog'u — el kitabi uyumlu"""

    def __init__(self, theme: dict, etiket_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.etiket_data = etiket_data
        self.setWindowTitle("Etiket Onizleme ve Yazdir")
        self.setMinimumSize(brand.sp(550), brand.sp(550))
        self._setup_ui()
        self._load_sablonlar()
        self._load_yazicilar()

    def _setup_ui(self):
        self.setStyleSheet(_DIALOG_BASE_CSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # ── Header ──
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)

        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title = QLabel("Etiket Onizleme")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # ── Etiket onizleme frame — 100x50mm oraninda ──
        etiket_frame = QFrame()
        etiket_frame.setFixedSize(brand.sp(400), brand.sp(200))
        etiket_frame.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)

        etiket_layout = QVBoxLayout(etiket_frame)
        etiket_layout.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)
        etiket_layout.setSpacing(brand.SP_1)

        # Musteri adi (buyuk)
        musteri_lbl = QLabel(self.etiket_data.get('musteri', '')[:35])
        musteri_lbl.setStyleSheet(
            f"color: #000; font-size: {brand.FS_HEADING_SM}px; font-weight: {brand.FW_BOLD};"
        )
        musteri_lbl.setAlignment(Qt.AlignCenter)
        etiket_layout.addWidget(musteri_lbl)

        # Ayirici cizgi
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #333;")
        line.setFixedHeight(1)
        etiket_layout.addWidget(line)

        # Urun
        urun_lbl = QLabel(f"Urun: {self.etiket_data.get('urun', '')[:30]}")
        urun_lbl.setStyleSheet(f"color: #000; font-size: {brand.FS_BODY_SM}px;")
        etiket_layout.addWidget(urun_lbl)

        # Lot No
        lot_lbl = QLabel(f"Lot: {self.etiket_data.get('lot_no', '')}")
        lot_lbl.setStyleSheet(
            f"color: #000; font-size: {brand.FS_BODY_SM}px; font-weight: {brand.FW_BOLD};"
        )
        etiket_layout.addWidget(lot_lbl)

        # Adet ve Tarih yan yana
        info_layout = QHBoxLayout()
        adet_lbl = QLabel(f"Adet: {self.etiket_data.get('adet', 0):,}")
        adet_lbl.setStyleSheet(f"color: #000; font-size: {brand.FS_BODY_SM}px;")
        info_layout.addWidget(adet_lbl)

        tarih_lbl = QLabel(f"Tarih: {self.etiket_data.get('tarih', '')}")
        tarih_lbl.setStyleSheet(f"color: #000; font-size: {brand.FS_BODY_SM}px;")
        info_layout.addWidget(tarih_lbl)
        etiket_layout.addLayout(info_layout)

        # Kontrol eden
        kontrol_lbl = QLabel(f"Kontrol: {self.etiket_data.get('kontrolcu', '')[:20]}")
        kontrol_lbl.setStyleSheet(f"color: #000; font-size: {brand.FS_CAPTION}px;")
        etiket_layout.addWidget(kontrol_lbl)

        # Barkod gosterimi (simule)
        barkod_lbl = QLabel("|||||||||||||||||||||||||||||||||||")
        barkod_lbl.setStyleSheet(
            f"color: #000; font-size: {brand.FS_TITLE}px; font-family: monospace;"
        )
        barkod_lbl.setAlignment(Qt.AlignCenter)
        etiket_layout.addWidget(barkod_lbl)

        barkod_text = QLabel(self.etiket_data.get('lot_no', ''))
        barkod_text.setStyleSheet(f"color: #000; font-size: {brand.FS_CAPTION}px;")
        barkod_text.setAlignment(Qt.AlignCenter)
        etiket_layout.addWidget(barkod_text)

        layout.addWidget(etiket_frame, alignment=Qt.AlignCenter)

        # Boyut bilgisi
        info = QLabel("100 x 50 mm")
        info.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px;"
        )
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        # Sablon Secimi
        sablon_group = QGroupBox("Etiket Sablonu")
        sablon_layout = QHBoxLayout(sablon_group)
        sablon_layout.addWidget(QLabel("Sablon:"))
        self.sablon_combo = QComboBox()
        self.sablon_combo.setMinimumWidth(brand.sp(250))
        self.sablon_combo.setStyleSheet(_INPUT_CSS)
        sablon_layout.addWidget(self.sablon_combo)
        sablon_layout.addStretch()
        layout.addWidget(sablon_group)

        # Yazici Secimi
        yazici_group = QGroupBox("Yazici Ayarlari")
        yazici_layout = QHBoxLayout(yazici_group)
        yazici_layout.addWidget(QLabel("Yazici:"))
        self.yazici_combo = QComboBox()
        self.yazici_combo.setMinimumWidth(brand.sp(200))
        self.yazici_combo.setStyleSheet(_INPUT_CSS)
        yazici_layout.addWidget(self.yazici_combo)

        yazici_layout.addWidget(QLabel("Mod:"))
        self.mod_combo = QComboBox()
        self.mod_combo.addItem("PDF Yazdir", "PDF")
        self.mod_combo.addItem("Godex Direkt (EZPL)", "EZPL")
        self.mod_combo.setStyleSheet(_INPUT_CSS)
        yazici_layout.addWidget(self.mod_combo)
        yazici_layout.addStretch()
        layout.addWidget(yazici_group)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        onizle_btn = QPushButton("PDF Onizle")
        onizle_btn.setCursor(Qt.PointingHandCursor)
        onizle_btn.setStyleSheet(_BTN_GHOST_CSS)
        onizle_btn.clicked.connect(self._pdf_onizle)
        btn_layout.addWidget(onizle_btn)

        iptal_btn = QPushButton("Iptal")
        iptal_btn.setCursor(Qt.PointingHandCursor)
        iptal_btn.setStyleSheet(_BTN_GHOST_CSS)
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)

        yazdir_btn = QPushButton("Yazdir")
        yazdir_btn.setCursor(Qt.PointingHandCursor)
        yazdir_btn.setStyleSheet(_BTN_SUCCESS_CSS)
        yazdir_btn.clicked.connect(self.accept)
        btn_layout.addWidget(yazdir_btn)

        layout.addLayout(btn_layout)

    def _load_sablonlar(self):
        """Etiket sablonlarini yukle"""
        self.sablon_combo.clear()
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sablon_kodu, sablon_adi, varsayilan_mi
                FROM tanim.etiket_sablonlari
                WHERE aktif_mi = 1 AND sablon_tipi IN ('PALET', 'MAMUL', 'SEVK')
                ORDER BY varsayilan_mi DESC, sablon_adi
            """)
            for row in cursor.fetchall():
                varsayilan = " (Varsayilan)" if row[3] else ""
                self.sablon_combo.addItem(f"{row[2]}{varsayilan}", row[0])
            if self.sablon_combo.count() == 0:
                self.sablon_combo.addItem("Varsayilan Sablon", None)
        except Exception as e:
            print(f"Sablon yukleme hatasi: {e}")
            self.sablon_combo.addItem("Varsayilan Sablon", None)
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_yazicilar(self):
        """Mevcut yazicilari yukle"""
        self.yazici_combo.clear()
        try:
            from utils.etiket_yazdir import get_available_printers, get_godex_printers
            all_printers = get_available_printers()
            godex_printers = get_godex_printers()
            if godex_printers:
                for p in godex_printers:
                    self.yazici_combo.addItem(f"[Godex] {p}", p)
            for p in all_printers:
                if p not in godex_printers:
                    self.yazici_combo.addItem(p, p)
            if self.yazici_combo.count() == 0:
                self.yazici_combo.addItem("PDF Dosyasi Olarak Kaydet", "PDF_ONLY")
        except ImportError:
            self.yazici_combo.addItem("PDF Dosyasi Olarak Kaydet", "PDF_ONLY")
        except Exception as e:
            print(f"Yazici listesi yuklenemedi: {e}")
            self.yazici_combo.addItem("PDF Dosyasi Olarak Kaydet", "PDF_ONLY")

    def _pdf_onizle(self):
        """PDF onizleme"""
        import subprocess
        import tempfile
        try:
            from utils.etiket_yazdir import a4_etiket_pdf_olustur
            etiketler = [self.etiket_data]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='etiket_onizle_')
            temp_path = temp_file.name
            temp_file.close()
            a4_etiket_pdf_olustur(temp_path, etiketler)
            subprocess.Popen(['start', '', temp_path], shell=True)
        except Exception as e:
            QMessageBox.warning(self, "Uyari", f"PDF onizleme hatasi: {e}")

    def get_sablon_id(self):
        return self.sablon_combo.currentData()

    def get_yazici(self):
        return self.yazici_combo.currentData()

    def get_mod(self):
        return self.mod_combo.currentData()


# =====================================================================
# DIALOG: Hata Ekle
# =====================================================================

class HataEkleDialog(QDialog):
    """Hata ekleme dialog'u — el kitabi uyumlu"""

    def __init__(self, theme: dict, hata_turleri: list, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.hata_turleri = hata_turleri
        self.setWindowTitle("Hata Ekle")
        self.setMinimumSize(brand.sp(400), brand.sp(200))
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(_DIALOG_BASE_CSS + _INPUT_CSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_4)

        # Hata turu
        lbl_tur = QLabel("Hata Turu:")
        lbl_tur.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        layout.addWidget(lbl_tur)
        self.hata_combo = QComboBox()
        for hata in self.hata_turleri:
            self.hata_combo.addItem(f"{hata['kod']} - {hata['ad']}", hata['id'])
        layout.addWidget(self.hata_combo)

        # Adet
        lbl_adet = QLabel("Hatali Adet:")
        lbl_adet.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        layout.addWidget(lbl_adet)
        self.adet_input = QSpinBox()
        self.adet_input.setRange(1, 99999)
        self.adet_input.setValue(1)
        layout.addWidget(self.adet_input)

        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        iptal_btn = QPushButton("Iptal")
        iptal_btn.setCursor(Qt.PointingHandCursor)
        iptal_btn.setStyleSheet(_BTN_GHOST_CSS)
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)

        ekle_btn = QPushButton("Ekle")
        ekle_btn.setCursor(Qt.PointingHandCursor)
        ekle_btn.setStyleSheet(_BTN_SUCCESS_CSS)
        ekle_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ekle_btn)

        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            'hata_turu_id': self.hata_combo.currentData(),
            'hata_adi': self.hata_combo.currentText(),
            'adet': self.adet_input.value()
        }


# =====================================================================
# DIALOG: Personel Giris
# =====================================================================

class PersonelGirisDialog(QDialog):
    """Personel kart/sicil giris dialogu — el kitabi uyumlu"""

    def __init__(self, theme, gorev_data, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.gorev = gorev_data
        self.personel_data = None
        self.setWindowTitle("Personel Girisi")
        self.setMinimumSize(brand.sp(450), brand.sp(380))
        self.setModal(True)
        self._setup_ui()
        self.sicil_input.setFocus()

    def _setup_ui(self):
        self.setStyleSheet(_DIALOG_BASE_CSS + _INPUT_CSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # ── Header ──
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)

        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title = QLabel("Kontrol Islemine Basla")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # ── Bilgi frame ──
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                padding: {brand.SP_4}px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(brand.SP_2)

        ie_lbl = QLabel(f"{self.gorev.get('is_emri_no', '')} - {self.gorev.get('lot_no', '')}")
        ie_lbl.setStyleSheet(
            f"color: {brand.PRIMARY}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY}px;"
        )
        info_layout.addWidget(ie_lbl)

        urun_lbl = QLabel(f"{(self.gorev.get('urun_adi', '') or '')[:40]}")
        urun_lbl.setStyleSheet(f"font-size: {brand.FS_BODY}px;")
        info_layout.addWidget(urun_lbl)

        kontrol_adet = self.gorev.get('kontrol_adet', 0) or self.gorev.get('toplam_adet', 0)
        miktar_lbl = QLabel(f"Kontrol Edilecek: {kontrol_adet:,} adet")
        miktar_lbl.setStyleSheet(
            f"color: {brand.WARNING}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY_LG}px;"
        )
        info_layout.addWidget(miktar_lbl)

        atanan = self.gorev.get('atanan_personel', '')
        if atanan:
            atanan_lbl = QLabel(f"Atanan: {atanan}")
            atanan_lbl.setStyleSheet(
                f"color: {brand.SUCCESS}; font-weight: {brand.FW_BOLD}; "
                f"font-size: {brand.FS_BODY}px;"
            )
            info_layout.addWidget(atanan_lbl)

        layout.addWidget(info_frame)

        # ── Kart okutma alani ──
        nfc_lbl = QLabel("Kartinizi okutun veya sicil numaranizi girin")
        nfc_lbl.setStyleSheet(f"""
            color: {brand.TEXT_MUTED};
            padding: {brand.SP_4}px;
            border: 2px dashed {brand.PRIMARY};
            border-radius: {brand.R_LG}px;
            font-size: {brand.FS_BODY}px;
        """)
        nfc_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(nfc_lbl)

        self.sicil_input = QLineEdit()
        self.sicil_input.setPlaceholderText("Sicil No veya Kart ID")
        self.sicil_input.returnPressed.connect(self._login)
        layout.addWidget(self.sicil_input)

        giris_btn = QPushButton("Isleme Basla")
        giris_btn.setCursor(Qt.PointingHandCursor)
        giris_btn.setStyleSheet(_BTN_PRIMARY_CSS)
        giris_btn.clicked.connect(self._login)
        layout.addWidget(giris_btn)

        iptal_btn = QPushButton("Iptal")
        iptal_btn.setCursor(Qt.PointingHandCursor)
        iptal_btn.setStyleSheet(_BTN_GHOST_CSS)
        iptal_btn.clicked.connect(self.reject)
        layout.addWidget(iptal_btn)

    def _login(self):
        sicil = self.sicil_input.text().strip()
        if not sicil:
            QMessageBox.warning(self, "Uyari", "Sicil numarasi veya kart ID giriniz!")
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, uuid, ad, soyad, sicil_no, departman_id, kart_no
                FROM ik.personeller WHERE (sicil_no = ? OR kart_no = ?) AND aktif_mi = 1
            """, (sicil, sicil))
            personel = cursor.fetchone()
            if not personel:
                QMessageBox.warning(self, "Hata", "Personel bulunamadi!")
                return

            personel_uuid = personel[1]
            atanan_id = self.gorev.get('atanan_personel_id')
            if atanan_id and str(personel_uuid) != str(atanan_id):
                QMessageBox.warning(
                    self, "Yetki Hatasi",
                    f"Bu gorev {self.gorev.get('atanan_personel', '')} personeline atanmis!"
                )
                return

            self.personel_data = {
                'id': personel[0], 'uuid': str(personel_uuid),
                'ad': personel[2], 'soyad': personel[3],
                'sicil_no': personel[4], 'ad_soyad': f"{personel[2]} {personel[3]}"
            }
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Giris hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# =====================================================================
# MAIN PAGE: Kalite Final
# =====================================================================

class KaliteFinalPage(BasePage):
    """Proses Kalite Kontrol Sayfasi — el kitabi uyumlu"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.secili_is_emri = None
        self.hata_listesi = []
        self.hata_turleri = []
        self._setup_ui()
        self._load_hata_turleri()
        self._load_kontrolcular()
        QTimer.singleShot(100, self._load_data)

        self._clock = QTimer()
        self._clock.timeout.connect(self._tick)
        self._clock.start(1000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # ── 1. Header ──
        header = self.create_page_header(
            "Proses Kalite Kontrol",
            "Lot bazli kalite kontrol, hata kayit ve etiket basma"
        )

        self._saat_lbl = QLabel()
        self._saat_lbl.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(self._saat_lbl)

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        header.addWidget(btn_yenile)

        layout.addLayout(header)

        # ── 2. KPI cards ──
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self._kpi_bekleyen = self.create_stat_card("BEKLEYEN", "0", color=brand.WARNING)
        kpi_row.addWidget(self._kpi_bekleyen)

        self._kpi_onay = self.create_stat_card("BUGUN ONAY", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self._kpi_onay)

        self._kpi_red = self.create_stat_card("BUGUN RED", "0", color=brand.ERROR)
        kpi_row.addWidget(self._kpi_red)

        kpi_row.addStretch()
        layout.addLayout(kpi_row)

        # ── 3. Splitter — Sol: Bekleyen lotlar, Sag: Kontrol formu ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(brand.SP_1)

        # --- SOL PANEL — Kontrol Bekleyen Lotlar ---
        sol_widget = QWidget()
        sol_layout = QVBoxLayout(sol_widget)
        sol_layout.setContentsMargins(0, 0, 0, 0)
        sol_layout.setSpacing(brand.SP_3)

        sol_header = QLabel("KONTROL BEKLEYEN LOTLAR")
        sol_header.setStyleSheet(
            f"color: {brand.WARNING}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY_LG}px;"
        )
        sol_layout.addWidget(sol_header)

        self.bekleyen_table = QTableWidget()
        self.bekleyen_table.setColumnCount(8)
        self.bekleyen_table.setHorizontalHeaderLabels([
            "ID", "Is Emri", "Urun", "Lot No", "Adet", "Atanan", "Durum", "Islem"
        ])
        self.bekleyen_table.setColumnHidden(0, True)
        self.bekleyen_table.setColumnWidth(1, brand.sp(100))
        self.bekleyen_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.bekleyen_table.setColumnWidth(3, brand.sp(110))
        self.bekleyen_table.setColumnWidth(4, brand.sp(70))
        self.bekleyen_table.setColumnWidth(5, brand.sp(120))
        self.bekleyen_table.setColumnWidth(6, brand.sp(80))
        self.bekleyen_table.setColumnWidth(7, brand.sp(120))
        self.bekleyen_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bekleyen_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.bekleyen_table.verticalHeader().setVisible(False)
        self.bekleyen_table.setShowGrid(False)
        self.bekleyen_table.setAlternatingRowColors(True)
        self.bekleyen_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.bekleyen_table.setStyleSheet(_TABLE_CSS)
        sol_layout.addWidget(self.bekleyen_table)

        splitter.addWidget(sol_widget)

        # --- SAG PANEL — Kontrol Formu ---
        sag_widget = QFrame()
        sag_widget.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 2px solid {brand.PRIMARY};
                border-radius: {brand.R_LG}px;
            }}
        """)
        sag_layout = QVBoxLayout(sag_widget)
        sag_layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        sag_layout.setSpacing(brand.SP_4)

        sag_header = QLabel("KONTROL FORMU")
        sag_header.setStyleSheet(
            f"color: {brand.PRIMARY}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY_LG}px;"
        )
        sag_layout.addWidget(sag_header)

        # ── Secili lot bilgileri ──
        self.bilgi_frame = QFrame()
        self.bilgi_frame.setStyleSheet(f"""
            background: {brand.BG_MAIN};
            border-radius: {brand.R_LG}px;
            padding: {brand.SP_4}px;
        """)
        bilgi_layout = QGridLayout(self.bilgi_frame)
        bilgi_layout.setSpacing(brand.SP_2)

        lbl_style_muted = f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;"
        lbl_style_bold = (
            f"color: {brand.TEXT}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY}px;"
        )

        lbl1 = QLabel("Is Emri:")
        lbl1.setStyleSheet(lbl_style_muted)
        bilgi_layout.addWidget(lbl1, 0, 0)
        self.lbl_is_emri = QLabel("-")
        self.lbl_is_emri.setStyleSheet(lbl_style_bold)
        bilgi_layout.addWidget(self.lbl_is_emri, 0, 1)

        lbl2 = QLabel("Urun:")
        lbl2.setStyleSheet(lbl_style_muted)
        bilgi_layout.addWidget(lbl2, 0, 2)
        self.lbl_urun = QLabel("-")
        self.lbl_urun.setStyleSheet(lbl_style_bold)
        bilgi_layout.addWidget(self.lbl_urun, 0, 3)

        lbl3 = QLabel("Lot No:")
        lbl3.setStyleSheet(lbl_style_muted)
        bilgi_layout.addWidget(lbl3, 1, 0)
        self.lbl_lot = QLabel("-")
        self.lbl_lot.setStyleSheet(
            f"color: {brand.PRIMARY}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY}px;"
        )
        bilgi_layout.addWidget(self.lbl_lot, 1, 1)

        lbl4 = QLabel("Toplam Adet:")
        lbl4.setStyleSheet(lbl_style_muted)
        bilgi_layout.addWidget(lbl4, 1, 2)
        self.lbl_toplam = QLabel("-")
        self.lbl_toplam.setStyleSheet(
            f"color: {brand.TEXT}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_HEADING_SM}px;"
        )
        bilgi_layout.addWidget(self.lbl_toplam, 1, 3)

        sag_layout.addWidget(self.bilgi_frame)

        # ── Kontrol girisleri ──
        giris_frame = QFrame()
        giris_frame.setStyleSheet(f"""
            background: {brand.BG_MAIN};
            border-radius: {brand.R_LG}px;
            padding: {brand.SP_4}px;
        """)
        giris_layout = QGridLayout(giris_frame)
        giris_layout.setSpacing(brand.SP_3)

        giris_lbl_style = f"color: {brand.TEXT}; font-size: {brand.FS_BODY}px;"

        # Kontrol edilen adet
        lbl5 = QLabel("Kontrol Edilen:")
        lbl5.setStyleSheet(giris_lbl_style)
        giris_layout.addWidget(lbl5, 0, 0)
        self.kontrol_edilen_input = QSpinBox()
        self.kontrol_edilen_input.setRange(0, 999999)
        self.kontrol_edilen_input.setStyleSheet(_INPUT_CSS)
        self.kontrol_edilen_input.valueChanged.connect(self._hesapla_adetler)
        giris_layout.addWidget(self.kontrol_edilen_input, 0, 1)

        # Kalan (bakiye)
        lbl_kalan = QLabel("Kalan Bakiye:")
        lbl_kalan.setStyleSheet(giris_lbl_style)
        giris_layout.addWidget(lbl_kalan, 0, 2)
        self.kalan_label = QLabel("0")
        self.kalan_label.setStyleSheet(
            f"color: {brand.WARNING}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_HEADING_SM}px;"
        )
        giris_layout.addWidget(self.kalan_label, 0, 3)

        # Saglam adet
        lbl6 = QLabel("Saglam Adet:")
        lbl6.setStyleSheet(giris_lbl_style)
        giris_layout.addWidget(lbl6, 1, 0)
        self.saglam_input = QSpinBox()
        self.saglam_input.setRange(0, 999999)
        self.saglam_input.setStyleSheet(_INPUT_CSS)
        self.saglam_input.valueChanged.connect(self._hesapla_hatali)
        giris_layout.addWidget(self.saglam_input, 1, 1)

        # Hatali adet (otomatik)
        lbl7 = QLabel("Hatali Adet:")
        lbl7.setStyleSheet(giris_lbl_style)
        giris_layout.addWidget(lbl7, 1, 2)
        self.hatali_label = QLabel("0")
        self.hatali_label.setStyleSheet(
            f"color: {brand.ERROR}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_HEADING}px;"
        )
        giris_layout.addWidget(self.hatali_label, 1, 3)

        # Kalinlik olcum
        lbl8 = QLabel("Kalinlik (um):")
        lbl8.setStyleSheet(giris_lbl_style)
        giris_layout.addWidget(lbl8, 2, 0)
        self.kalinlik_input = QDoubleSpinBox()
        self.kalinlik_input.setRange(0, 9999)
        self.kalinlik_input.setDecimals(2)
        self.kalinlik_input.setStyleSheet(_INPUT_CSS)
        giris_layout.addWidget(self.kalinlik_input, 2, 1)

        # Kontrol eden
        lbl9 = QLabel("Kontrol Eden:")
        lbl9.setStyleSheet(giris_lbl_style)
        giris_layout.addWidget(lbl9, 2, 2)
        self.kontrolcu_combo = QComboBox()
        self.kontrolcu_combo.setStyleSheet(_INPUT_CSS)
        giris_layout.addWidget(self.kontrolcu_combo, 2, 3)

        sag_layout.addWidget(giris_frame)

        # ── Hata listesi ──
        hata_header = QHBoxLayout()
        hata_header.setSpacing(brand.SP_3)
        hata_lbl = QLabel("Hata Detaylari:")
        hata_lbl.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_BODY}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        hata_header.addWidget(hata_lbl)
        hata_header.addStretch()

        hata_ekle_btn = QPushButton("+ Hata Ekle")
        hata_ekle_btn.setCursor(Qt.PointingHandCursor)
        hata_ekle_btn.setStyleSheet(_BTN_WARNING_CSS)
        hata_ekle_btn.clicked.connect(self._hata_ekle)
        hata_header.addWidget(hata_ekle_btn)
        sag_layout.addLayout(hata_header)

        self.hata_table = QTableWidget()
        self.hata_table.setColumnCount(4)
        self.hata_table.setHorizontalHeaderLabels(["ID", "Hata Turu", "Adet", "Sil"])
        self.hata_table.setColumnHidden(0, True)
        self.hata_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.hata_table.setColumnWidth(2, brand.sp(80))
        self.hata_table.setColumnWidth(3, brand.sp(60))
        self.hata_table.setMaximumHeight(brand.sp(150))
        self.hata_table.verticalHeader().setVisible(False)
        self.hata_table.setShowGrid(False)
        self.hata_table.setAlternatingRowColors(True)
        self.hata_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.hata_table.setStyleSheet(_TABLE_CSS)
        sag_layout.addWidget(self.hata_table)

        # ── Not ──
        not_lbl = QLabel("Not:")
        not_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        sag_layout.addWidget(not_lbl)
        self.not_input = QTextEdit()
        self.not_input.setMaximumHeight(brand.sp(60))
        self.not_input.setStyleSheet(f"""
            QTextEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_MD}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QTextEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.not_input.setPlaceholderText("Kontrol notu...")
        sag_layout.addWidget(self.not_input)

        # ── Kaydet ve Etiket butonlari ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)

        self.kaydet_btn = QPushButton("Kaydet")
        self.kaydet_btn.setCursor(Qt.PointingHandCursor)
        self.kaydet_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_HEADING_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
                min-height: {brand.sp(44)}px;
            }}
            QPushButton:hover {{ background: #059669; }}
            QPushButton:disabled {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT_MUTED};
            }}
        """)
        self.kaydet_btn.clicked.connect(self._kaydet)
        self.kaydet_btn.setEnabled(False)
        btn_layout.addWidget(self.kaydet_btn)

        self.etiket_btn = QPushButton("Etiket Bas")
        self.etiket_btn.setCursor(Qt.PointingHandCursor)
        self.etiket_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_HEADING_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
                min-height: {brand.sp(44)}px;
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
            QPushButton:disabled {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT_MUTED};
            }}
        """)
        self.etiket_btn.clicked.connect(self._bas_etiket_manual)
        self.etiket_btn.setEnabled(True)
        btn_layout.addWidget(self.etiket_btn)

        sag_layout.addLayout(btn_layout)

        splitter.addWidget(sag_widget)
        splitter.setSizes([brand.sp(400), brand.sp(500)])

        layout.addWidget(splitter, 1)

    # -----------------------------------------------------------------
    def _tick(self):
        self._saat_lbl.setText(QTime.currentTime().toString("HH:mm:ss"))

    # -----------------------------------------------------------------
    def _load_hata_turleri(self):
        """Hata turlerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, kod, ad FROM tanim.hata_turleri "
                "WHERE aktif_mi = 1 ORDER BY sira_no, kod"
            )
            self.hata_turleri = [
                {'id': r[0], 'kod': r[1], 'ad': r[2]} for r in cursor.fetchall()
            ]
        except Exception as e:
            print(f"Hata turleri yuklenemedi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_kontrolcular(self):
        """Kontrol eden personel listesi"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ad + ' ' + soyad as ad_soyad
                FROM ik.personeller
                WHERE aktif_mi = 1
                ORDER BY ad, soyad
            """)
            self.kontrolcu_combo.clear()
            self.kontrolcu_combo.addItem("-- Secin --", None)
            for row in cursor.fetchall():
                self.kontrolcu_combo.addItem(row[1], row[0])
        except Exception as e:
            print(f"Kontrolculer yuklenemedi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_data(self):
        """Kontrol bekleyen lotlari yukle — Atanan gorevler (ATANDI, DEVAM_EDIYOR)"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # kalite.kontrol_is_emirleri tablosundan ATANDI ve DEVAM_EDIYOR durumundaki gorevleri getir
            cursor.execute("""
                SELECT ie.id, ie.is_emri_no, ie.stok_adi, ie.lot_no,
                       kie.kontrol_miktar as adet,
                       ie.stok_kodu,
                       kie.id as kontrol_id,
                       p.ad + ' ' + p.soyad as atanan_personel,
                       kie.personel_id as atanan_personel_id,
                       kie.durum
                FROM kalite.kontrol_is_emirleri kie
                INNER JOIN siparis.is_emirleri ie ON kie.is_emri_id = ie.id
                LEFT JOIN ik.personeller p ON kie.personel_id = p.uuid
                WHERE kie.durum IN ('ATANDI', 'DEVAM_EDIYOR')
                ORDER BY
                    CASE WHEN kie.durum = 'DEVAM_EDIYOR' THEN 0
                         WHEN kie.durum = 'ATANDI' THEN 1
                         ELSE 2 END,
                    kie.atama_tarihi ASC
            """)

            rows = cursor.fetchall()

            self.bekleyen_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # ID (gizli)
                self.bekleyen_table.setItem(i, 0, QTableWidgetItem(str(row[0])))

                # Is Emri No
                ie_item = QTableWidgetItem(row[1] or '')
                ie_item.setFont(QFont(brand.FONT_FAMILY, -1, QFont.Bold))
                self.bekleyen_table.setItem(i, 1, ie_item)

                # Urun
                self.bekleyen_table.setItem(i, 2, QTableWidgetItem((row[2] or '')[:25]))

                # Lot No
                lot_item = QTableWidgetItem(row[3] or '')
                lot_item.setForeground(QColor(brand.PRIMARY))
                self.bekleyen_table.setItem(i, 3, lot_item)

                # Adet
                adet_item = QTableWidgetItem(f"{int(row[4] or 0):,}")
                adet_item.setTextAlignment(Qt.AlignCenter)
                self.bekleyen_table.setItem(i, 4, adet_item)

                # Atanan Personel
                atanan = row[7] or '-'
                atanan_item = QTableWidgetItem(atanan[:15] if atanan != '-' else '-')
                if atanan != '-':
                    atanan_item.setForeground(QColor(brand.SUCCESS))
                    atanan_item.setFont(QFont(brand.FONT_FAMILY, -1, QFont.Bold))
                self.bekleyen_table.setItem(i, 5, atanan_item)

                # Durum
                durum = row[9] or 'BEKLIYOR'
                durum_item = QTableWidgetItem(durum)
                if durum == 'DEVAM_EDIYOR':
                    durum_item.setForeground(QColor(brand.WARNING))
                elif durum == 'ATANDI':
                    durum_item.setForeground(QColor(brand.SUCCESS))
                else:
                    durum_item.setForeground(QColor(brand.TEXT_MUTED))
                self.bekleyen_table.setItem(i, 6, durum_item)

                # Islem Butonu
                kontrol_id = row[6]
                atanan_personel = row[7]
                atanan_personel_id = row[8]

                gorev_data = {
                    'id': row[0], 'is_emri_no': row[1], 'urun_adi': row[2],
                    'lot_no': row[3], 'toplam_adet': int(row[4] or 0),
                    'kontrol_adet': int(row[4] or 0), 'urun_kodu': row[5],
                    'kontrol_id': kontrol_id, 'atanan_personel': atanan_personel,
                    'atanan_personel_id': atanan_personel_id
                }

                if atanan_personel:
                    widget = self.create_action_buttons([
                        ("Basla", "Isleme Basla", lambda checked, gd=gorev_data: self._on_kontrol_click(gd), "success"),
                    ])
                else:
                    widget = self.create_action_buttons([
                        ("Kontrol", "Kontrol Et", lambda checked, gd=gorev_data: self._on_kontrol_click(gd), "view"),
                    ])
                self.bekleyen_table.setCellWidget(i, 7, widget)

            # KPI guncelle
            self._kpi_bekleyen.findChild(QLabel, "stat_value").setText(str(len(rows)))

            cursor.execute("""
                SELECT COUNT(*) FROM kalite.final_kontrol
                WHERE CAST(kontrol_tarihi AS DATE) = CAST(GETDATE() AS DATE)
                  AND sonuc = 'KABUL'
            """)
            self._kpi_onay.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            cursor.execute("""
                SELECT COUNT(*) FROM kalite.final_kontrol
                WHERE CAST(kontrol_tarihi AS DATE) = CAST(GETDATE() AS DATE)
                  AND sonuc IN ('RED', 'KISMI')
            """)
            self._kpi_red.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yuklenemedi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _on_kontrol_click(self, gorev_data):
        """Kontrol butonuna tiklandiginda — atanmissa kart okut"""
        if gorev_data.get('atanan_personel'):
            giris_dlg = PersonelGirisDialog(self.theme, gorev_data, self)
            if giris_dlg.exec() != QDialog.Accepted or not giris_dlg.personel_data:
                return

            if gorev_data.get('kontrol_id'):
                conn = None
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE kalite.kontrol_is_emirleri
                        SET durum = 'DEVAM_EDIYOR', baslama_tarihi = GETDATE()
                        WHERE id = ?
                    """, (gorev_data['kontrol_id'],))
                    conn.commit()
                except Exception as e:
                    print(f"Durum guncelleme hatasi: {e}")
                finally:
                    if conn:
                        try:
                            conn.close()
                        except Exception:
                            pass

            self._set_kontrolcu(giris_dlg.personel_data)

        self._sec_lot_from_gorev(gorev_data)

    def _set_kontrolcu(self, personel_data):
        """Kontrolcu combo'sunda personeli sec"""
        ad_soyad = personel_data.get('ad_soyad', '')
        for i in range(self.kontrolcu_combo.count()):
            if ad_soyad in self.kontrolcu_combo.itemText(i):
                self.kontrolcu_combo.setCurrentIndex(i)
                return
        personel_id = personel_data.get('id')
        for i in range(self.kontrolcu_combo.count()):
            if self.kontrolcu_combo.itemData(i) == personel_id:
                self.kontrolcu_combo.setCurrentIndex(i)
                return

    def _sec_lot_from_gorev(self, gorev_data):
        """Gorev verisinden formu doldur"""
        toplam_adet = gorev_data.get('toplam_adet', 0) or gorev_data.get('kontrol_adet', 0)

        self.secili_is_emri = {
            'id': gorev_data['id'],
            'is_emri_no': gorev_data.get('is_emri_no', ''),
            'urun_adi': gorev_data.get('urun_adi', ''),
            'lot_no': gorev_data.get('lot_no', ''),
            'toplam_adet': toplam_adet,
            'urun_kodu': gorev_data.get('urun_kodu', ''),
            'kontrol_id': gorev_data.get('kontrol_id'),
            'atanan_personel_id': gorev_data.get('atanan_personel_id')
        }

        self.lbl_is_emri.setText(gorev_data.get('is_emri_no', '') or '-')
        self.lbl_urun.setText((gorev_data.get('urun_adi', '') or '-')[:25])
        self.lbl_lot.setText(gorev_data.get('lot_no', '') or '-')
        self.lbl_toplam.setText(f"{toplam_adet:,}")

        self.kontrol_edilen_input.setMaximum(toplam_adet)
        self.kontrol_edilen_input.setValue(toplam_adet)

        self.saglam_input.setMaximum(toplam_adet)
        self.saglam_input.setValue(toplam_adet)

        self.kalan_label.setText("0")
        self.hatali_label.setText("0")
        self.kalinlik_input.setValue(0)
        self.not_input.clear()

        self.hata_listesi = []
        self._refresh_hata_table()

        self.kaydet_btn.setEnabled(True)

    def _sec_lot(self, is_emri_id: int, data: tuple):
        """Lot sec ve formu doldur"""
        toplam_adet = int(data[4] or 0)

        self.secili_is_emri = {
            'id': data[0],
            'is_emri_no': data[1],
            'urun_adi': data[2],
            'lot_no': data[3],
            'toplam_adet': toplam_adet,
            'urun_kodu': data[6]
        }

        self.lbl_is_emri.setText(data[1] or '-')
        self.lbl_urun.setText((data[2] or '-')[:25])
        self.lbl_lot.setText(data[3] or '-')
        self.lbl_toplam.setText(str(toplam_adet))

        # Kontrol edilen varsayilan = toplam
        self.kontrol_edilen_input.setMaximum(toplam_adet)
        self.kontrol_edilen_input.setValue(toplam_adet)

        self.saglam_input.setMaximum(toplam_adet)
        self.saglam_input.setValue(toplam_adet)

        self.kalan_label.setText("0")
        self.hatali_label.setText("0")
        self.kalinlik_input.setValue(0)
        self.not_input.clear()

        self.hata_listesi = []
        self._refresh_hata_table()

        self.kaydet_btn.setEnabled(True)

    def _hesapla_adetler(self):
        """Kontrol edilen degistiginde kalan ve saglami guncelle"""
        if not self.secili_is_emri:
            return
        toplam = self.secili_is_emri.get('toplam_adet', 0)
        kontrol_edilen = self.kontrol_edilen_input.value()
        kalan = toplam - kontrol_edilen
        self.kalan_label.setText(str(max(0, kalan)))

        # Saglam maksimumu guncelle
        self.saglam_input.setMaximum(kontrol_edilen)
        if self.saglam_input.value() > kontrol_edilen:
            self.saglam_input.setValue(kontrol_edilen)

        self._hesapla_hatali()

    def _hesapla_hatali(self):
        """Hatali adedi hesapla = kontrol edilen - saglam"""
        if not self.secili_is_emri:
            return
        kontrol_edilen = self.kontrol_edilen_input.value()
        saglam = self.saglam_input.value()
        hatali = kontrol_edilen - saglam
        self.hatali_label.setText(str(max(0, hatali)))

    def _hata_ekle(self):
        """Hata ekle dialog'u"""
        if not self.secili_is_emri:
            QMessageBox.warning(self, "Uyari", "Once bir lot secin!")
            return

        if not self.hata_turleri:
            QMessageBox.warning(self, "Uyari", "Hata turleri tanimlanmamis!")
            return

        dlg = HataEkleDialog(self.theme, self.hata_turleri, self)
        if dlg.exec() == QDialog.Accepted:
            hata = dlg.get_data()
            self.hata_listesi.append(hata)
            self._refresh_hata_table()
            self._update_hatali_toplam()

    def _refresh_hata_table(self):
        """Hata tablosunu guncelle"""
        self.hata_table.setRowCount(len(self.hata_listesi))
        for i, hata in enumerate(self.hata_listesi):
            self.hata_table.setItem(i, 0, QTableWidgetItem(str(hata.get('hata_turu_id', ''))))
            self.hata_table.setItem(i, 1, QTableWidgetItem(hata.get('hata_adi', '')))

            adet_item = QTableWidgetItem(str(hata.get('adet', 0)))
            adet_item.setTextAlignment(Qt.AlignCenter)
            self.hata_table.setItem(i, 2, adet_item)

            widget = self.create_action_buttons([
                ("Sil", "Sil", lambda checked, idx=i: self._sil_hata(idx), "delete"),
            ])
            self.hata_table.setCellWidget(i, 3, widget)

    def _sil_hata(self, idx: int):
        """Hata sil"""
        if 0 <= idx < len(self.hata_listesi):
            self.hata_listesi.pop(idx)
            self._refresh_hata_table()
            self._update_hatali_toplam()

    def _update_hatali_toplam(self):
        """Hata adetlerinden hatali toplami guncelle"""
        toplam_hata = sum(h.get('adet', 0) for h in self.hata_listesi)
        if self.secili_is_emri:
            toplam = self.secili_is_emri.get('toplam_adet', 0)
            saglam = toplam - toplam_hata
            self.saglam_input.setValue(max(0, saglam))
            self.hatali_label.setText(str(toplam_hata))

    def _kaydet(self):
        """Kontrol kaydini kaydet ve etiket bas"""
        if not self.secili_is_emri:
            return

        kontrolcu_id = self.kontrolcu_combo.currentData()
        if not kontrolcu_id:
            QMessageBox.warning(self, "Uyari", "Kontrol eden secin!")
            return

        kontrol_edilen = self.kontrol_edilen_input.value()
        saglam = self.saglam_input.value()
        hatali = kontrol_edilen - saglam
        toplam = self.secili_is_emri.get('toplam_adet', 0)
        kalan = toplam - kontrol_edilen

        if kontrol_edilen == 0:
            QMessageBox.warning(self, "Uyari", "Kontrol edilen adet 0 olamaz!")
            return

        # Hata adetleri toplami kontrol
        hata_toplam = sum(h.get('adet', 0) for h in self.hata_listesi)
        if hatali > 0 and hata_toplam != hatali:
            QMessageBox.warning(
                self, "Uyari",
                f"Hata adetleri toplami ({hata_toplam}) hatali adet ({hatali}) ile eslesmyor!"
            )
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # ========== FINAL KONTROL KAYDI (FKK - Son Urun Kontrolu) ==========
            cursor.execute("""
                INSERT INTO kalite.final_kontrol
                (is_emri_id, lot_no, kontrol_miktar, saglam_adet, hatali_adet,
                 sonuc, kontrol_tarihi, olusturma_tarihi, guncelleme_tarihi)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, GETDATE(), GETDATE(), GETDATE())
            """, (
                self.secili_is_emri['id'],
                self.secili_is_emri['lot_no'],
                kontrol_edilen,
                saglam,
                hatali,
                'KABUL' if hatali == 0 else ('RED' if saglam == 0 else 'KISMI')
            ))

            # Son eklenen ID'yi al
            kontrol_id = cursor.fetchone()[0]
            print(f"Final kontrol kaydi olusturuldu (ID: {kontrol_id})")
            # ===================================================================

            # Hata kayitlari (final_kontrol_hatalar tablosuna)
            for hata in self.hata_listesi:
                try:
                    cursor.execute("""
                        INSERT INTO kalite.final_kontrol_hatalar (final_kontrol_id, hata_turu_id, adet)
                        VALUES (?, ?, ?)
                    """, (kontrol_id, hata['hata_turu_id'], hata['adet']))
                except Exception as hata_err:
                    print(f"Final kontrol hata kaydi hatasi: {hata_err}")

            # Sonuc belirleme
            if hatali == 0:
                sonuc = 'ONAY'
            elif saglam == 0:
                sonuc = 'RED'
            else:
                sonuc = 'KISMI'

            # Eger atanmis gorev varsa kontrol_is_emirleri tablosunu da guncelle
            kontrol_is_emri_id = self.secili_is_emri.get('kontrol_id')
            if kontrol_is_emri_id:
                cursor.execute("""
                    UPDATE kalite.kontrol_is_emirleri
                    SET durum = 'TAMAMLANDI', bitis_tarihi = GETDATE(),
                        kontrol_miktar = ?, saglam_miktar = ?, hatali_miktar = ?,
                        sonuc = ?, notlar = ?
                    WHERE id = ?
                """, (kontrol_edilen, saglam, hatali, sonuc, self.not_input.toPlainText(), kontrol_is_emri_id))

            # Depo ID'lerini bul: SEVK (saglam) ve RED (hatali)
            # Hareket motorunu baslat (AYNI connection ile - lock cakismasi olmasin)
            from core.hareket_motoru import HareketMotoru
            motor = HareketMotoru(conn)

            # SEVK deposunu bul
            sevk_depo_id = motor.get_depo_by_tip('SVK')
            if not sevk_depo_id:
                cursor.execute("SELECT TOP 1 id FROM tanim.depolar WHERE kod LIKE '%SEVK%' OR kod = 'SEV-01' AND aktif_mi = 1")
                row = cursor.fetchone()
                sevk_depo_id = row[0] if row else None
            print(f"DEBUG: SEVK depo_id={sevk_depo_id}")

            # RED deposunu bul
            red_depo_id = motor.get_depo_by_tip('RED')
            if not red_depo_id:
                cursor.execute("SELECT TOP 1 id FROM tanim.depolar WHERE kod = 'RED' AND aktif_mi = 1")
                row = cursor.fetchone()
                red_depo_id = row[0] if row else None
            print(f"DEBUG: RED depo_id={red_depo_id}")

            lot_no = self.secili_is_emri.get('lot_no', '')
            is_emri_id = self.secili_is_emri['id']
            urun_kodu = self.secili_is_emri.get('urun_kodu', '') or ''
            urun_adi = self.secili_is_emri.get('urun_adi', '') or ''

            print(f"DEBUG: lot_no={lot_no}, urun_kodu={urun_kodu}, sevk_depo_id={sevk_depo_id}, saglam={saglam}, hatali={hatali}")

            # urun_id bul veya olustur
            urun_id = None
            if urun_kodu:
                cursor.execute("SELECT id FROM stok.urunler WHERE urun_kodu = ? AND aktif_mi = 1", (urun_kodu,))
                urun_row = cursor.fetchone()

                if urun_row:
                    urun_id = urun_row[0]
                    print(f"DEBUG: Mevcut urun bulundu - urun_id={urun_id}")
                else:
                    cursor.execute("""
                        INSERT INTO stok.urunler (uuid, urun_kodu, urun_adi, urun_tipi, birim_id, aktif_mi,
                                                 olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                        OUTPUT INSERTED.id
                        VALUES (NEWID(), ?, ?, 'MAMUL', 1, 1, GETDATE(), GETDATE(), 0)
                    """, (urun_kodu, urun_adi))
                    urun_id = cursor.fetchone()[0]
                    print(f"DEBUG: Yeni urun olusturuldu - urun_id={urun_id}")
            else:
                print("DEBUG: stok_kodu BOS! Varsayilan urun araniyor...")
                # stok_kodu bossa is_emri_no'dan olustur
                stok_kodu = f"URN-{is_emri_id}"
                cursor.execute("""
                    INSERT INTO stok.urunler (uuid, urun_kodu, urun_adi, urun_tipi, birim_id, aktif_mi,
                                             olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                    OUTPUT INSERTED.id
                    VALUES (NEWID(), ?, ?, 'MAMUL', 1, 1, GETDATE(), GETDATE(), 0)
                """, (stok_kodu, stok_adi or f"Urun {is_emri_id}"))
                urun_id = cursor.fetchone()[0]
                print(f"DEBUG: Varsayilan urun olusturuldu - urun_id={urun_id}, stok_kodu={stok_kodu}")

            # Saglam urunler -> SEVK DEPO (Hareket Motoru ile)
            # NOT: Sadece saglam miktari transfer et, kalan FKK'da kalmali
            if saglam > 0 and sevk_depo_id:
                print(f"DEBUG: Sevk depoya transfer yapiliyor... lot_no={lot_no}, sevk_depo_id={sevk_depo_id}, saglam={saglam}")

                # Once FKK deposundaki mevcut bakiyeyi kontrol et
                cursor.execute("""
                    SELECT sb.miktar, sb.depo_id
                    FROM stok.stok_bakiye sb
                    INNER JOIN tanim.depolar d ON sb.depo_id = d.id
                    WHERE sb.lot_no = ? AND d.kod = 'FKK'
                """, (lot_no,))
                bakiye_row = cursor.fetchone()
                mevcut_miktar = bakiye_row[0] if bakiye_row else 0
                mevcut_depo = bakiye_row[1] if bakiye_row else None
                print(f"DEBUG: Mevcut bakiye (FKK) - miktar={mevcut_miktar}, depo_id={mevcut_depo}")

                # Saglam miktari icin yeni lot olustur ve SEV-01'e gonder
                sevk_lot = f"{lot_no}-SEV"

                sevk_sonuc = motor.stok_giris(
                    urun_id=urun_id,
                    miktar=saglam,
                    lot_no=sevk_lot,
                    depo_id=sevk_depo_id,
                    urun_kodu=urun_kodu,
                    urun_adi=urun_adi,
                    kalite_durumu='ONAYLANDI',
                    durum_kodu='SEVK_HAZIR',
                    aciklama=f"Final kalite onay - Saglam: {saglam}"
                )

                if sevk_sonuc.basarili:
                    print(f"DEBUG: Sevk depoya giris basarili - sevk_lot={sevk_lot}")

                    # Orijinal lot'tan kontrol edilen toplam miktari dus (saglam + hatali)
                    kontrol_edilen = saglam + hatali
                    yeni_miktar = mevcut_miktar - kontrol_edilen

                    # FKK depo ID'sini al
                    cursor.execute("SELECT id FROM tanim.depolar WHERE kod = 'FKK'")
                    fkk_row = cursor.fetchone()
                    fkk_depo_id = fkk_row[0] if fkk_row else mevcut_depo

                    if yeni_miktar > 0:
                        # Kalan miktar var, FKK'da birak
                        cursor.execute("""
                            UPDATE stok.stok_bakiye
                            SET miktar = ?,
                                durum_kodu = 'FKK_BEKLIYOR'
                            WHERE lot_no = ? AND depo_id = ?
                        """, (yeni_miktar, lot_no, fkk_depo_id))
                        print(f"DEBUG: Orijinal lot guncellendi - kalan miktar={yeni_miktar}, depo_id={fkk_depo_id}")
                    else:
                        # Kalan miktar yok, orijinal lot'u sifirla
                        cursor.execute("""
                            UPDATE stok.stok_bakiye
                            SET miktar = 0,
                                kalite_durumu = 'TAMAMLANDI',
                                durum_kodu = 'SEVK_EDILDI'
                            WHERE lot_no = ? AND depo_id = ?
                        """, (lot_no, fkk_depo_id))
                        print(f"DEBUG: Orijinal lot tamamlandi - miktar=0, depo_id={fkk_depo_id}")
                else:
                    print(f"DEBUG: Sevk giris hatasi: {sevk_sonuc.mesaj}")
            else:
                print(f"DEBUG: Sevk depoya kayit YAPILMADI! saglam={saglam}, sevk_depo_id={sevk_depo_id}")

            # Hatali urunler -> RED DEPO + kalite.uretim_redler tablosuna kayit (Hareket Motoru ile)
            if hatali > 0 and red_depo_id:
                lot_prefix = '-'.join(lot_no.split('-')[:3]) if lot_no else ''
                red_lot = f"{lot_prefix}-RED" if lot_prefix else f"RED-{is_emri_id}"

                # Hareket motoru ile red deposuna giris
                red_sonuc = motor.stok_giris(
                    urun_id=urun_id,
                    miktar=hatali,
                    lot_no=red_lot,
                    depo_id=red_depo_id,
                    urun_kodu=urun_kodu,
                    urun_adi=urun_adi,
                    kalite_durumu='REDDEDILDI',
                    durum_kodu='RED',
                    aciklama=f"Final kalite red - Hatali: {hatali}"
                )

                if red_sonuc.basarili:
                    print(f"DEBUG: Red depoya stok girisi basarili - red_lot={red_lot}")
                else:
                    print(f"DEBUG: Red stok girisi hatasi: {red_sonuc.mesaj}")

                # kalite.uretim_redler tablosuna kayit ekle (kalite_red ekraninda gorunmesi icin)
                # Her hata turu icin ayri kayit olustur
                try:
                    if self.hata_listesi:
                        for hata in self.hata_listesi:
                            cursor.execute("""
                                INSERT INTO kalite.uretim_redler
                                (is_emri_id, lot_no, red_miktar, hata_turu_id, kontrol_id, red_tarihi,
                                 kontrol_eden_id, durum, aciklama, olusturma_tarihi)
                                VALUES (?, ?, ?, ?, ?, GETDATE(), ?, 'BEKLIYOR', ?, GETDATE())
                            """, (is_emri_id, lot_no, hata.get('adet', 0), hata.get('hata_turu_id'),
                                  kontrol_id, kontrolcu_id, self.not_input.toPlainText()))
                    else:
                        # Hata listesi bossa toplam hatali miktari kaydet
                        cursor.execute("""
                            INSERT INTO kalite.uretim_redler
                            (is_emri_id, lot_no, red_miktar, kontrol_id, red_tarihi,
                             kontrol_eden_id, durum, aciklama, olusturma_tarihi)
                            VALUES (?, ?, ?, ?, GETDATE(), ?, 'BEKLIYOR', ?, GETDATE())
                        """, (is_emri_id, lot_no, hatali, kontrol_id, kontrolcu_id,
                              self.not_input.toPlainText()))
                except Exception as red_err:
                    print(f"Uretim red kaydi hatasi (tablo olmayabilir): {red_err}")

            # Is emri durumunu ve miktarini guncelle
            if kalan == 0:
                # Tamami kontrol edildi
                if hatali == 0:
                    yeni_durum = 'ONAYLANDI'
                else:
                    yeni_durum = 'KISMI_RED'

                cursor.execute("""
                    UPDATE siparis.is_emirleri
                    SET durum = ?,
                        toplam_miktar = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (yeni_durum, saglam, self.secili_is_emri['id']))
            else:
                # Kismi kontrol - kalan miktar var, beklemede kal
                cursor.execute("""
                    UPDATE siparis.is_emirleri
                    SET toplam_miktar = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (kalan, self.secili_is_emri['id']))

            # Etiket verilerini kaydet (ayni connection ve transaction icinde)
            if saglam > 0:
                try:
                    # Musteri bilgisini al (ayni cursor ile)
                    cursor.execute("""
                        SELECT ie.cari_unvani
                        FROM siparis.is_emirleri ie
                        WHERE ie.id = ?
                    """, (is_emri_id,))
                    row = cursor.fetchone()
                    musteri = row[0] if row else ''

                    # Kontrolcu
                    kontrolcu_adi = self.kontrolcu_combo.currentText()
                    if kontrolcu_adi.startswith("--"):
                        kontrolcu_adi = ""

                    # Etiket kuyruguna ekle (ayni transaction icinde)
                    sevk_lot = f"{lot_no}-SEV"
                    cursor.execute("""
                        INSERT INTO kalite.etiket_kuyrugu (
                            proses_kontrol_id, lot_no, stok_kodu, stok_adi,
                            musteri, miktar, kontrolcu_adi,
                            kontrol_tarihi, basildi_mi, olusturma_tarihi
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), 0, GETDATE())
                    """, (
                        kontrol_id, sevk_lot, urun_kodu, urun_adi,
                        musteri, saglam, kontrolcu_adi
                    ))
                    print(f"DEBUG: Etiket kuyruguna eklendi - lot={sevk_lot}")
                except Exception as etiket_err:
                    print(f"Etiket kuyrugu hatasi (gormezden gelindi): {etiket_err}")

            # Connection'i commit et ve kapat (tek seferde tum transaction)
            conn.commit()

            # Basari mesaji
            msg = f"Kontrol kaydedildi!\n\n"
            msg += f"Kontrol Edilen: {kontrol_edilen}\n"
            msg += f"Saglam: {saglam}\n"
            msg += f"Hatali: {hatali}\n"
            msg += f"Kalan Bakiye: {kalan}\n\n"

            if saglam > 0:
                msg += f"{saglam} adet SEVK deposuna aktarildi\n"
                msg += f"  Lot: {lot_no}-SEV\n\n"

            if hatali > 0:
                msg += f"{hatali} adet RED deposuna aktarildi\n"
                msg += f"  Lot: {'-'.join(lot_no.split('-')[:3])}-RED\n\n"

            msg += f"FKK'da kalan: {kalan} adet"

            QMessageBox.information(self, "Basarili", msg)

            # Formu temizle
            self.secili_is_emri = None
            self.hata_listesi = []
            self._refresh_hata_table()
            self.kaydet_btn.setEnabled(False)
            # etiket_btn her zaman aktif kalir (kuyruktan basabilir)
            self.lbl_is_emri.setText("-")
            self.lbl_urun.setText("-")
            self.lbl_lot.setText("-")
            self.lbl_toplam.setText("-")

            self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit basarisiz: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _bas_etiket_manual(self):
        """Manuel etiket basma — kuyruktaki etiketlerden sec"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Bekleyen etiketleri getir
            cursor.execute("""
                SELECT
                    id, lot_no, stok_kodu, stok_adi, musteri, miktar,
                    kontrolcu_adi, kontrol_tarihi, basim_sayisi
                FROM kalite.etiket_kuyrugu
                WHERE basildi_mi = 0
                ORDER BY kontrol_tarihi DESC
            """)

            etiketler = cursor.fetchall()

            if not etiketler:
                QMessageBox.information(self, "Bilgi", "Bekleyen etiket yok!")
                return

            # Etiket secim dialog'u
            dlg = QDialog(self)
            dlg.setWindowTitle("Etiket Sec")
            dlg.setMinimumSize(brand.sp(600), brand.sp(400))
            dlg.setStyleSheet(_DIALOG_BASE_CSS)

            d_layout = QVBoxLayout(dlg)
            d_layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
            d_layout.setSpacing(brand.SP_4)

            lbl = QLabel("Basilacak etiketi secin:")
            lbl.setStyleSheet(
                f"color: {brand.TEXT}; font-size: {brand.FS_BODY_LG}px; "
                f"font-weight: {brand.FW_BOLD};"
            )
            d_layout.addWidget(lbl)

            liste = QListWidget()
            liste.setStyleSheet(f"""
                QListWidget {{
                    background: {brand.BG_CARD};
                    color: {brand.TEXT};
                    border: 1px solid {brand.BORDER};
                    border-radius: {brand.R_LG}px;
                    padding: {brand.SP_2}px;
                    font-size: {brand.FS_BODY}px;
                }}
                QListWidget::item {{
                    padding: {brand.SP_3}px;
                    border-bottom: 1px solid {brand.BORDER};
                }}
                QListWidget::item:selected {{
                    background: {brand.BG_SELECTED};
                    color: {brand.TEXT};
                }}
            """)

            for etiket in etiketler:
                etiket_id, lot_no, stok_kodu, stok_adi, musteri, miktar, kontrolcu, tarih, basim = etiket
                tarih_str = tarih.strftime("%d.%m.%Y %H:%M") if tarih else "-"

                item_text = f"{lot_no}\n"
                item_text += f"   {stok_kodu} - {stok_adi[:30]}\n"
                item_text += f"   Musteri: {musteri[:30]} | {miktar} adet\n"
                item_text += f"   Kontrol: {kontrolcu} | {tarih_str}"
                if basim > 0:
                    item_text += f" | Basim: {basim}x"

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, etiket_id)
                liste.addItem(item)

            d_layout.addWidget(liste)

            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btn_box.setStyleSheet(f"""
                QPushButton {{
                    background: {brand.PRIMARY};
                    color: white;
                    border: none;
                    border-radius: {brand.R_SM}px;
                    padding: {brand.SP_2}px {brand.SP_4}px;
                    min-height: {brand.sp(38)}px;
                    font-size: {brand.FS_BODY}px;
                }}
                QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
            """)
            btn_box.accepted.connect(dlg.accept)
            btn_box.rejected.connect(dlg.reject)
            d_layout.addWidget(btn_box)

            if dlg.exec() != QDialog.Accepted:
                return

            secili_item = liste.currentItem()
            if not secili_item:
                return

            etiket_id = secili_item.data(Qt.UserRole)

            # Etiket verilerini al
            cursor.execute("""
                SELECT
                    lot_no, stok_kodu, stok_adi, musteri, miktar, kontrolcu_adi
                FROM kalite.etiket_kuyrugu
                WHERE id = ?
            """, (etiket_id,))

            row = cursor.fetchone()
            if not row:
                return

            lot_no, stok_kodu, stok_adi, musteri, miktar, kontrolcu = row

            # Etiket verisi
            etiket_data = {
                'musteri': musteri or '',
                'urun': stok_adi or '',
                'lot_no': lot_no or '',
                'adet': miktar,
                'tarih': datetime.now().strftime('%d.%m.%Y'),
                'kontrolcu': kontrolcu or '',
                'stok_kodu': stok_kodu or ''
            }

            # Etiket dialog'unu goster
            dlg_etiket = EtiketOnizlemeDialog(self.theme, etiket_data, self)
            if dlg_etiket.exec() == QDialog.Accepted:
                # Basim sayisini artir
                cursor.execute("""
                    UPDATE kalite.etiket_kuyrugu
                    SET basim_sayisi = basim_sayisi + 1,
                        basim_tarihi = GETDATE(),
                        basildi_mi = 1
                    WHERE id = ?
                """, (etiket_id,))
                conn.commit()
                QMessageBox.information(self, "Basarili", "Etiket basildi!")

        except Exception as e:
            QMessageBox.warning(self, "Etiket Hatasi", f"Etiket basilamadi:\n{str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _bas_etiket(self):
        """Etiket bas — Godex EZPL formati"""
        if not self.secili_is_emri:
            return None

        conn = None
        try:
            # Musteri bilgisini al
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ie.cari_unvani
                FROM siparis.is_emirleri ie
                WHERE ie.id = ?
            """, (self.secili_is_emri['id'],))
            row = cursor.fetchone()
            musteri = row[0] if row else ''

            # Kontrol eden adi
            kontrolcu = self.kontrolcu_combo.currentText()
            if kontrolcu.startswith("--"):
                kontrolcu = ""

            # Etiket verisi
            etiket_data = {
                'musteri': musteri or '',
                'urun': self.secili_is_emri.get('stok_adi', ''),
                'lot_no': self.secili_is_emri.get('lot_no', ''),
                'adet': self.saglam_input.value(),
                'tarih': datetime.now().strftime('%d.%m.%Y'),
                'kontrolcu': kontrolcu,
                'stok_kodu': self.secili_is_emri.get('stok_kodu', '')
            }

            # Onizleme dialog'u goster
            dlg = EtiketOnizlemeDialog(self.theme, etiket_data, self)
            if dlg.exec() != QDialog.Accepted:
                return None

            # EZPL komutu olustur (Godex icin)
            ezpl = self._generate_ezpl(etiket_data)

            # Yaziciya gonder (simdilik dosyaya kaydet - test icin)
            lot_safe = (etiket_data['lot_no'] or 'etiket').replace('/', '-').replace('\\', '-')
            etiket_dosya = os.path.join(os.path.expanduser("~"), "Desktop", f"etiket_{lot_safe}.prn")
            with open(etiket_dosya, 'w', encoding='utf-8') as f:
                f.write(ezpl)

            print(f"Etiket dosyasi olusturuldu: {etiket_dosya}")
            return etiket_dosya

        except Exception as e:
            print(f"Etiket basma hatasi: {e}")
            return None
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _generate_ezpl(self, data: dict) -> str:
        """Godex EZPL etiket komutu olustur — 100x50mm"""
        ezpl = f"""
^Q50,3
^W100
^H10
^P1
^S3
^AD
^C1
^R0
~Q+0
^O0
^D0
^E18
~R200
^L
Dy2-me-dd
Th:m:s
AE,48,36,1,1,0,0,{data['musteri'][:30]}
AE,48,26,1,1,0,3,Urun: {data['urun'][:25]}
AE,48,18,1,1,0,3,Lot: {data['lot_no']}
AE,48,12,1,1,0,3,Adet: {data['adet']}
AE,48,6,1,1,0,3,Tarih: {data['tarih']}
AE,48,0,1,1,0,3,Kontrol: {data['kontrolcu'][:15]}
BE,10,40,1,3,70,0,2,{data['lot_no']}
E
"""
        return ezpl

    def _send_to_printer(self, data: str):
        """Yaziciya gonder"""
        try:
            import win32print
            printer_name = ETIKET_YAZICI

            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Etiket", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, data.encode('utf-8'))
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            print(f"Yazici hatasi: {e}")
