# -*- coding: utf-8 -*-
"""
NEXOR ERP - Red Kayitlari / Uygunsuzluk Yonetimi Sayfasi
=========================================================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
from datetime import datetime, date
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QTextEdit, QGridLayout, QGroupBox, QFormLayout,
    QDoubleSpinBox, QDateEdit, QTabWidget, QWidget, QSplitter,
    QInputDialog, QRadioButton, QButtonGroup, QSpinBox,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.hareket_motoru import HareketMotoru
from core.nexor_brand import brand
from dialogs.login import ModernLoginDialog


# ── Ortak stil yardimcilari ──────────────────────────────────────────

def _dialog_base_css():
    """Tum dialog'lar icin ortak stylesheet"""
    return f"""
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


def _input_css():
    """Ortak input stileri"""
    return f"""
        QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QLineEdit {{
            background: {brand.BG_INPUT};
            color: {brand.TEXT};
            border: 1px solid {brand.BORDER};
            border-radius: {brand.R_SM}px;
            padding: {brand.SP_2}px {brand.SP_3}px;
            font-size: {brand.FS_BODY}px;
        }}
        QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
        QDateEdit:focus, QLineEdit:focus {{
            border-color: {brand.PRIMARY};
        }}
    """


def _table_css():
    """El kitabi uyumlu tablo stilesi"""
    return f"""
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


def _brand_btn(bg, hover_bg, fg="white"):
    """Brand-aware buton stili"""
    return f"""
        QPushButton {{
            background: {bg};
            color: {fg};
            border: none;
            border-radius: {brand.R_SM}px;
            padding: 0 {brand.SP_5}px;
            font-size: {brand.FS_BODY}px;
            font-weight: {brand.FW_SEMIBOLD};
            min-height: {brand.sp(38)}px;
        }}
        QPushButton:hover {{ background: {hover_bg}; }}
    """


def _ghost_btn():
    """Iptal / ghost buton stili"""
    return f"""
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


def _dialog_header(title_text, subtitle_text=None):
    """Dialog ust baslik blogu"""
    header = QHBoxLayout()
    header.setSpacing(brand.SP_3)

    accent = QFrame()
    accent.setFixedSize(brand.SP_1, brand.sp(32))
    accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
    header.addWidget(accent)

    title_col = QVBoxLayout()
    title_col.setSpacing(brand.SP_1)
    title = QLabel(title_text)
    title.setStyleSheet(
        f"color: {brand.TEXT}; "
        f"font-size: {brand.FS_HEADING}px; "
        f"font-weight: {brand.FW_SEMIBOLD};"
    )
    title_col.addWidget(title)
    if subtitle_text:
        sub = QLabel(subtitle_text)
        sub.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        title_col.addWidget(sub)
    header.addLayout(title_col)
    header.addStretch()
    return header


# =====================================================================
# RED DEPOT KARAR DIALOG
# =====================================================================

class RedKararDialog(QDialog):
    """Red depot karari dialog'u — el kitabi uyumlu"""

    def __init__(self, theme: dict, red_kayit: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.red_kayit = red_kayit
        self.max_miktar = int(red_kayit.get('red_miktar', 0) or 0)
        self.setWindowTitle("Red Depot Karar")
        self.setMinimumSize(brand.sp(600), brand.sp(450))
        self.karar_data = None
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(_dialog_base_css() + _input_css())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # ── Header ──
        header = _dialog_header("Red Depot Karar Verme")

        # Lot ve Urun bilgisi
        lot_info = QLabel(f"{self.red_kayit.get('lot_no', '-')} | {(self.red_kayit.get('urun_adi') or '-')[:30]}")
        lot_info.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        header.addWidget(lot_info)
        layout.addLayout(header)

        # Bilgi satiri
        info_layout = QHBoxLayout()
        info_layout.setSpacing(brand.SP_4)

        musteri = self.red_kayit.get('musteri') or '-'
        musteri_lbl = QLabel(f"Musteri: {musteri[:25]}")
        musteri_lbl.setStyleSheet(f"color: {brand.TEXT}; font-size: {brand.FS_BODY}px;")
        info_layout.addWidget(musteri_lbl)

        hata_turu = self.red_kayit.get('hata_turu_adi') or '-'
        hata_lbl = QLabel(f"Hata: {hata_turu}")
        hata_lbl.setStyleSheet(
            f"color: {brand.WARNING}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_BODY}px;"
        )
        info_layout.addWidget(hata_lbl)

        info_layout.addStretch()

        miktar_lbl = QLabel(f"Toplam: {self.max_miktar} adet")
        miktar_lbl.setStyleSheet(
            f"color: {brand.ERROR}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_BODY}px;"
        )
        info_layout.addWidget(miktar_lbl)

        layout.addLayout(info_layout)

        # Karar Tablosu
        karar_group = QGroupBox("Karar Ver")
        karar_layout = QVBoxLayout(karar_group)

        self.karar_table = QTableWidget()
        self.karar_table.setColumnCount(4)
        self.karar_table.setHorizontalHeaderLabels(["Hata Turu", "Miktar", "Karar", "Aciklama"])
        self.karar_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.karar_table.setColumnWidth(1, brand.sp(120))
        self.karar_table.setColumnWidth(2, brand.sp(150))
        self.karar_table.setColumnWidth(3, brand.sp(150))
        self.karar_table.verticalHeader().setVisible(False)
        self.karar_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.karar_table.setShowGrid(False)
        self.karar_table.setAlternatingRowColors(True)
        self.karar_table.setStyleSheet(_table_css())

        # Tek satir ekle
        self.karar_table.setRowCount(1)
        self.karar_table.setRowHeight(0, brand.sp(42))

        # Hata Turu
        hata_item = QTableWidgetItem(hata_turu)
        hata_item.setFlags(hata_item.flags() & ~Qt.ItemIsEditable)
        self.karar_table.setItem(0, 0, hata_item)

        # Miktar (SpinBox)
        self.spn_miktar = QSpinBox()
        self.spn_miktar.setRange(1, self.max_miktar)
        self.spn_miktar.setValue(self.max_miktar)
        self.spn_miktar.valueChanged.connect(self._miktar_degisti)
        self.karar_table.setCellWidget(0, 1, self.spn_miktar)

        # Karar (ComboBox)
        self.cmb_karar = QComboBox()
        self.cmb_karar.addItem("SOKUM", "SOKUM")
        self.cmb_karar.addItem("KABUL", "KABUL")
        self.cmb_karar.addItem("MUSTERI ONAYI", "MUSTERI_ONAY")
        self.karar_table.setCellWidget(0, 2, self.cmb_karar)

        # Aciklama
        self.txt_aciklama = QLineEdit()
        self.txt_aciklama.setPlaceholderText("Not...")
        self.karar_table.setCellWidget(0, 3, self.txt_aciklama)

        karar_layout.addWidget(self.karar_table)

        # Kalan miktar bilgisi
        self.lbl_kalan = QLabel("")
        self.lbl_kalan.setStyleSheet(
            f"color: {brand.WARNING}; font-size: {brand.FS_BODY_SM}px;"
        )
        karar_layout.addWidget(self.lbl_kalan)

        layout.addWidget(karar_group)

        # Karar aciklamalari
        aciklama_frame = QFrame()
        aciklama_frame.setStyleSheet(
            f"background: {brand.BG_CARD}; "
            f"border-radius: {brand.R_LG}px; "
            f"padding: {brand.SP_3}px;"
        )
        aciklama_layout = QVBoxLayout(aciklama_frame)
        aciklama_layout.setSpacing(brand.SP_1)

        for txt in [
            "SOKUM - XI deposuna gonderilir, kaplama sokulur",
            "KABUL - FKK'ya geri doner, tekrar kontrol edilir",
            "MUSTERI ONAYI - Karantinaya alinir, musteri karari beklenir",
        ]:
            lbl = QLabel(txt)
            lbl.setStyleSheet(
                f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px;"
            )
            aciklama_layout.addWidget(lbl)

        layout.addWidget(aciklama_frame)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        btn_iptal = QPushButton("Iptal")
        btn_iptal.setCursor(Qt.PointingHandCursor)
        btn_iptal.setFixedHeight(brand.sp(38))
        btn_iptal.setStyleSheet(_ghost_btn())
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)

        btn_onayla = QPushButton("Karari Uygula")
        btn_onayla.setCursor(Qt.PointingHandCursor)
        btn_onayla.setFixedHeight(brand.sp(38))
        btn_onayla.setStyleSheet(_brand_btn(brand.SUCCESS, "#059669"))
        btn_onayla.clicked.connect(self._onayla)
        btn_layout.addWidget(btn_onayla)

        layout.addLayout(btn_layout)

    def _miktar_degisti(self, value):
        """Miktar degistiginde kalan bilgisini guncelle"""
        kalan = self.max_miktar - value
        if kalan > 0:
            self.lbl_kalan.setText(f"{kalan} adet RED deposunda kalacak")
        else:
            self.lbl_kalan.setText("")

    def _onayla(self):
        """Karari onayla"""
        karar_tip = self.cmb_karar.currentData()
        islem_miktar = self.spn_miktar.value()

        if islem_miktar <= 0:
            QMessageBox.warning(self, "Uyari", "Islem miktari 0'dan buyuk olmali!")
            return

        self.karar_data = {
            'tip': karar_tip,
            'miktar': islem_miktar,
            'kalan_miktar': self.max_miktar - islem_miktar,
            'not': self.txt_aciklama.text().strip(),
            'red_kayit': self.red_kayit
        }

        self.accept()

    def get_karar(self):
        """Karar verisini al"""
        return self.karar_data


# =====================================================================
# UYGUNSUZLUK DIALOG
# =====================================================================

class UygunsuzlukDialog(QDialog):
    """Yeni uygunsuzluk kaydi dialog'u — el kitabi uyumlu"""

    def __init__(self, theme: dict, kayit_tipi: str = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.kayit_tipi = kayit_tipi
        self.setWindowTitle("Yeni Uygunsuzluk Kaydi")
        self.setMinimumSize(brand.sp(700), brand.sp(650))
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(_dialog_base_css() + _input_css())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # Baslik
        header = _dialog_header("Yeni Uygunsuzluk Kaydi")
        layout.addLayout(header)

        # Kayit Tipi
        tip_group = QGroupBox("Kayit Tipi")
        tip_layout = QHBoxLayout()
        tip_layout.setSpacing(brand.SP_3)

        self.cmb_kayit_tipi = QComboBox()
        self.cmb_kayit_tipi.addItems([
            'MÜŞTERİ_ŞİKAYETİ',
            'İÇ_RED',
            'TEDARİKÇİ_RED',
            'PROSES_RED',
            'DENETİM_BULGUSU'
        ])
        if self.kayit_tipi:
            idx = self.cmb_kayit_tipi.findText(self.kayit_tipi)
            if idx >= 0:
                self.cmb_kayit_tipi.setCurrentIndex(idx)
        tip_layout.addWidget(self.cmb_kayit_tipi)

        self.cmb_oncelik = QComboBox()
        self.cmb_oncelik.addItems(['DÜŞÜK', 'NORMAL', 'YÜKSEK', 'KRİTİK'])
        self.cmb_oncelik.setCurrentText('NORMAL')
        lbl_oncelik = QLabel("Oncelik:")
        lbl_oncelik.setStyleSheet(f"font-size: {brand.FS_BODY}px;")
        tip_layout.addWidget(lbl_oncelik)
        tip_layout.addWidget(self.cmb_oncelik)

        tip_group.setLayout(tip_layout)
        layout.addWidget(tip_group)

        # Temel Bilgiler
        bilgi_group = QGroupBox("Temel Bilgiler")
        bilgi_form = QFormLayout()
        bilgi_form.setSpacing(brand.SP_3)
        bilgi_form.setLabelAlignment(Qt.AlignRight)

        # Bildiren
        self.cmb_bildiren = QComboBox()
        self._load_personel()
        bilgi_form.addRow("Bildiren:", self.cmb_bildiren)

        # Musteri/Tedarikci
        self.cmb_cari = QComboBox()
        self._load_cariler()
        self.cmb_cari.currentIndexChanged.connect(self._on_cari_changed)
        bilgi_form.addRow("Musteri/Tedarikci:", self.cmb_cari)

        # Urun
        self.cmb_urun = QComboBox()
        bilgi_form.addRow("Urun:", self.cmb_urun)

        # Lot No
        self.txt_lot = QLineEdit()
        self.txt_lot.setPlaceholderText("Lot numarasi")
        bilgi_form.addRow("Lot No:", self.txt_lot)

        # Etkilenen Miktar
        miktar_layout = QHBoxLayout()
        self.txt_miktar = QDoubleSpinBox()
        self.txt_miktar.setRange(0, 9999999)
        self.txt_miktar.setDecimals(2)
        miktar_layout.addWidget(self.txt_miktar)
        lbl_adet = QLabel("Adet")
        lbl_adet.setStyleSheet(f"font-size: {brand.FS_BODY}px;")
        miktar_layout.addWidget(lbl_adet)
        bilgi_form.addRow("Etkilenen Miktar:", miktar_layout)

        # Tespit Yeri
        self.txt_tespit_yeri = QLineEdit()
        self.txt_tespit_yeri.setPlaceholderText("Orn: Final Kontrol, Musteri Sahasi, Giris Kalite")
        bilgi_form.addRow("Tespit Yeri:", self.txt_tespit_yeri)

        bilgi_group.setLayout(bilgi_form)
        layout.addWidget(bilgi_group)

        # Hata Tanimi
        hata_group = QGroupBox("Hata Detaylari")
        hata_layout = QVBoxLayout()
        hata_layout.setSpacing(brand.SP_3)

        hata_tur_layout = QHBoxLayout()
        lbl_ht = QLabel("Hata Turu:")
        lbl_ht.setStyleSheet(f"font-size: {brand.FS_BODY}px;")
        hata_tur_layout.addWidget(lbl_ht)
        self.cmb_hata_turu = QComboBox()
        self._load_hata_turleri()
        hata_tur_layout.addWidget(self.cmb_hata_turu, 1)
        hata_layout.addLayout(hata_tur_layout)

        lbl_tanim = QLabel("Hata Tanimi:")
        lbl_tanim.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        hata_layout.addWidget(lbl_tanim)
        self.txt_hata_tanimi = QTextEdit()
        self.txt_hata_tanimi.setMaximumHeight(brand.sp(100))
        self.txt_hata_tanimi.setStyleSheet(f"""
            QTextEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QTextEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.txt_hata_tanimi.setPlaceholderText("Hatanin detayli aciklamasi...")
        hata_layout.addWidget(self.txt_hata_tanimi)

        hata_group.setLayout(hata_layout)
        layout.addWidget(hata_group)

        # Sorumlu ve Tarih
        sorumluluk_layout = QHBoxLayout()
        sorumluluk_layout.setSpacing(brand.SP_3)

        lbl_sor = QLabel("Sorumlu:")
        lbl_sor.setStyleSheet(f"font-size: {brand.FS_BODY}px;")
        sorumluluk_layout.addWidget(lbl_sor)
        self.cmb_sorumlu = QComboBox()
        self._load_personel_sorumlu()
        sorumluluk_layout.addWidget(self.cmb_sorumlu)

        lbl_hedef = QLabel("Hedef Kapanis:")
        lbl_hedef.setStyleSheet(f"font-size: {brand.FS_BODY}px;")
        sorumluluk_layout.addWidget(lbl_hedef)
        self.date_hedef = QDateEdit()
        self.date_hedef.setDate(QDate.currentDate().addDays(7))
        self.date_hedef.setCalendarPopup(True)
        sorumluluk_layout.addWidget(self.date_hedef)

        layout.addLayout(sorumluluk_layout)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        btn_iptal = QPushButton("Iptal")
        btn_iptal.setCursor(Qt.PointingHandCursor)
        btn_iptal.setFixedHeight(brand.sp(38))
        btn_iptal.setStyleSheet(_ghost_btn())
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)

        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setCursor(Qt.PointingHandCursor)
        btn_kaydet.setFixedHeight(brand.sp(38))
        btn_kaydet.setStyleSheet(_brand_btn(brand.PRIMARY, brand.PRIMARY_HOVER))
        btn_kaydet.clicked.connect(self._kaydet)
        btn_layout.addWidget(btn_kaydet)

        layout.addLayout(btn_layout)

    def _load_personel(self):
        """Personel listesi"""
        self.cmb_bildiren.clear()
        self.cmb_bildiren.addItem("-- Secin --", None)
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_bildiren.addItem(row[1], row[0])
        except Exception as e:
            print(f"Personel yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_personel_sorumlu(self):
        """Sorumlu personel listesi"""
        self.cmb_sorumlu.clear()
        self.cmb_sorumlu.addItem("-- Secin --", None)
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_sorumlu.addItem(row[1], row[0])
        except Exception as e:
            print(f"Personel yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_cariler(self):
        """Cari listesi"""
        self.cmb_cari.clear()
        self.cmb_cari.addItem("-- Musteri/Tedarikci Secin --", None)
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT cari_unvani
                FROM stok.urunler
                WHERE cari_unvani IS NOT NULL AND cari_unvani <> '' AND aktif_mi = 1
                ORDER BY cari_unvani
            """)
            for row in cursor.fetchall():
                self.cmb_cari.addItem(row[0], row[0])
        except Exception as e:
            print(f"Cari yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _on_cari_changed(self):
        """Cari degistiginde urunleri guncelle"""
        cari_id = self.cmb_cari.currentData()
        self._load_urunler(cari_id)

    def _load_urunler(self, cari_unvani=None):
        """Urun listesi"""
        self.cmb_urun.clear()
        self.cmb_urun.addItem("-- Urun Secin --", None)
        if not cari_unvani:
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, ISNULL(s.urun_kodu, '') + ' - ' + ISNULL(s.urun_adi, '')
                FROM stok.urunler s
                LEFT JOIN stok.urunler u ON u.urun_kodu = s.stok_kodu
                WHERE s.cari_unvani = ? AND ISNULL(s.aktif, 1) = 1
                ORDER BY s.stok_kodu
            """, (cari_unvani,))
            rows = cursor.fetchall()
            for row in rows:
                if row[0]:
                    self.cmb_urun.addItem(row[1], row[0])
                else:
                    self.cmb_urun.addItem(row[1], None)
        except Exception as e:
            print(f"Urun yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_hata_turleri(self):
        """Hata turleri"""
        self.cmb_hata_turu.clear()
        self.cmb_hata_turu.addItem("-- Secin --", None)
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod + ' - ' + ad FROM tanim.hata_turleri WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_hata_turu.addItem(row[1], row[0])
        except Exception as e:
            print(f"Hata turleri yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _kaydet(self):
        """Kaydi kaydet"""
        bildiren_id = self.cmb_bildiren.currentData()
        if not bildiren_id:
            QMessageBox.warning(self, "Uyari", "Bildiren kisi secilmelidir!")
            return

        hata_tanimi = self.txt_hata_tanimi.toPlainText().strip()
        if not hata_tanimi:
            QMessageBox.warning(self, "Uyari", "Hata tanimi girilmelidir!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # cari_unvani'den cari_id bul
            cari_unvani = self.cmb_cari.currentData()
            cari_id = None
            if cari_unvani:
                cursor.execute("""
                    SELECT TOP 1 id FROM musteri.cariler
                    WHERE unvan = ? AND aktif_mi = 1 AND silindi_mi = 0
                """, (cari_unvani,))
                row = cursor.fetchone()
                if row:
                    cari_id = row[0]

            # Kayit no olustur
            cursor.execute("""
                SELECT TOP 1 kayit_no FROM kalite.uygunsuzluklar
                WHERE kayit_no LIKE ? ORDER BY kayit_no DESC
            """, (f"NCR-{datetime.now().strftime('%Y%m')}%",))
            row = cursor.fetchone()
            if row:
                last_no = int(row[0].split('-')[-1])
                kayit_no = f"NCR-{datetime.now().strftime('%Y%m')}-{last_no + 1:04d}"
            else:
                kayit_no = f"NCR-{datetime.now().strftime('%Y%m')}-0001"

            cursor.execute("""
                INSERT INTO kalite.uygunsuzluklar (
                    uuid, kayit_no, kayit_tipi, kayit_tarihi, bildiren_id, cari_id, urun_id,
                    lot_no, etkilenen_miktar, hata_turu_id, hata_tanimi, tespit_yeri,
                    oncelik, durum, sorumlu_id, hedef_kapanis_tarihi,
                    olusturma_tarihi, guncelleme_tarihi
                ) VALUES (
                    NEWID(), ?, ?, CAST(GETDATE() AS DATE), ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, 'AÇIK', ?, ?,
                    GETDATE(), GETDATE()
                )
            """, (
                kayit_no,
                self.cmb_kayit_tipi.currentText(),
                bildiren_id,
                cari_id,
                self.cmb_urun.currentData(),
                self.txt_lot.text() or None,
                self.txt_miktar.value() if self.txt_miktar.value() > 0 else None,
                self.cmb_hata_turu.currentData(),
                hata_tanimi,
                self.txt_tespit_yeri.text() or None,
                self.cmb_oncelik.currentText(),
                self.cmb_sorumlu.currentData(),
                self.date_hedef.date().toPython()
            ))

            conn.commit()
            LogManager.log_insert('kalite', 'kalite.uygunsuzluklar', None, 'Uygunsuzluk kaydi olustu')

            # Bildirim: Uygunsuzluk kaydi acildi
            try:
                from core.bildirim_tetikleyici import BildirimTetikleyici
                urun_adi = self.cmb_urun.currentText() if hasattr(self, 'cmb_urun') else ''
                BildirimTetikleyici.uygunsuzluk_acildi(
                    kayit_id=0,
                    kayit_no=kayit_no,
                    urun_adi=urun_adi,
                )
            except Exception as bt_err:
                print(f"Bildirim hatasi: {bt_err}")

            QMessageBox.information(self, "Basarili", f"Uygunsuzluk kaydi olusturuldu!\n\nKayit No: {kayit_no}")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit basarisiz: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# =====================================================================
# UYGUNSUZLUK DETAY DIALOG
# =====================================================================

class UygunsuzlukDetayDialog(QDialog):
    """Uygunsuzluk detay ve aksiyon yonetimi dialog'u — el kitabi uyumlu"""

    def __init__(self, theme: dict, kayit_id: int, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.kayit_id = kayit_id
        self.setWindowTitle("Uygunsuzluk Detayi")
        self.setMinimumSize(brand.sp(900), brand.sp(700))
        self._load_kayit()
        self._setup_ui()

    def _load_kayit(self):
        """Kayit bilgilerini yukle"""
        self.kayit = {}
        self.aksiyonlar = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT u.id, u.kayit_no, u.kayit_tipi, u.kayit_tarihi,
                       p1.ad + ' ' + p1.soyad as bildiren,
                       c.unvan, s.urun_kodu + ' - ' + s.urun_adi as urun,
                       u.lot_no, u.etkilenen_miktar, u.hata_tanimi, u.tespit_yeri,
                       u.oncelik, u.durum, p2.ad + ' ' + p2.soyad as sorumlu,
                       u.hedef_kapanis_tarihi, u.kapanis_tarihi, u.maliyet,
                       ht.ad as hata_turu
                FROM kalite.uygunsuzluklar u
                LEFT JOIN ik.personeller p1 ON u.bildiren_id = p1.id
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN stok.urunler s ON u.urun_id = s.id
                LEFT JOIN ik.personeller p2 ON u.sorumlu_id = p2.id
                LEFT JOIN tanim.hata_turleri ht ON u.hata_turu_id = ht.id
                WHERE u.id = ?
            """, (self.kayit_id,))

            row = cursor.fetchone()
            if row:
                self.kayit = {
                    'id': row[0], 'kayit_no': row[1], 'kayit_tipi': row[2],
                    'kayit_tarihi': row[3], 'bildiren': row[4], 'cari': row[5],
                    'urun': row[6], 'lot_no': row[7], 'miktar': row[8],
                    'hata_tanimi': row[9], 'tespit_yeri': row[10], 'oncelik': row[11],
                    'durum': row[12], 'sorumlu': row[13], 'hedef_kapanis': row[14],
                    'kapanis_tarihi': row[15], 'maliyet': row[16], 'hata_turu': row[17]
                }

            # Aksiyonlari yukle
            cursor.execute("""
                SELECT a.id, a.aksiyon_tipi, a.d_adimi, a.aciklama,
                       p.ad + ' ' + p.soyad as sorumlu, a.hedef_tarih,
                       a.tamamlanma_tarihi, a.durum
                FROM kalite.uygunsuzluk_aksiyonlar a
                LEFT JOIN ik.personeller p ON a.sorumlu_id = p.id
                WHERE a.uygunsuzluk_id = ?
                ORDER BY a.d_adimi, a.olusturma_tarihi
            """, (self.kayit_id,))

            for row in cursor.fetchall():
                self.aksiyonlar.append({
                    'id': row[0], 'tip': row[1], 'd_adimi': row[2],
                    'aciklama': row[3], 'sorumlu': row[4], 'hedef': row[5],
                    'tamamlanma': row[6], 'durum': row[7]
                })

        except Exception as e:
            print(f"Kayit yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _setup_ui(self):
        self.setStyleSheet(_dialog_base_css() + _input_css())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # Baslik
        header = _dialog_header(self.kayit.get('kayit_no', ''))

        durum = self.kayit.get('durum', '')
        durum_colors = {
            'AÇIK': brand.WARNING,
            'İŞLEMDE': brand.INFO,
            'KAPATILDI': brand.SUCCESS,
            'İPTAL': brand.TEXT_MUTED
        }
        durum_lbl = QLabel(durum)
        durum_lbl.setStyleSheet(
            f"background: {durum_colors.get(durum, brand.TEXT_MUTED)}; "
            f"color: white; "
            f"padding: {brand.SP_1}px {brand.SP_3}px; "
            f"border-radius: {brand.R_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_BODY_SM}px;"
        )
        header.addWidget(durum_lbl)
        layout.addLayout(header)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                background: {brand.BG_CARD};
            }}
            QTabBar::tab {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                padding: {brand.SP_3}px {brand.SP_5}px;
                margin-right: {brand.SP_1}px;
                border-top-left-radius: {brand.R_SM}px;
                border-top-right-radius: {brand.R_SM}px;
                font-size: {brand.FS_BODY}px;
            }}
            QTabBar::tab:selected {{
                background: {brand.PRIMARY};
                color: white;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """)

        # Tab 1 - Detay
        detay_widget = QWidget()
        detay_layout = QVBoxLayout(detay_widget)
        detay_layout.setSpacing(brand.SP_4)
        detay_layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)

        # Bilgi grid
        info_grid = QGridLayout()
        info_grid.setSpacing(brand.SP_3)

        labels = [
            ("Kayit Tipi:", self.kayit.get('kayit_tipi', '')),
            ("Tarih:", str(self.kayit.get('kayit_tarihi', ''))),
            ("Bildiren:", self.kayit.get('bildiren', '')),
            ("Musteri/Tedarikci:", self.kayit.get('cari', '') or '-'),
            ("Urun:", self.kayit.get('urun', '') or '-'),
            ("Lot No:", self.kayit.get('lot_no', '') or '-'),
            ("Etkilenen Miktar:", str(self.kayit.get('miktar', 0) or 0)),
            ("Tespit Yeri:", self.kayit.get('tespit_yeri', '') or '-'),
            ("Hata Turu:", self.kayit.get('hata_turu', '') or '-'),
            ("Oncelik:", self.kayit.get('oncelik', '')),
            ("Sorumlu:", self.kayit.get('sorumlu', '') or '-'),
            ("Hedef Kapanis:", str(self.kayit.get('hedef_kapanis', '') or '-'))
        ]

        row = 0
        col = 0
        for label, value in labels:
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color: {brand.TEXT_MUTED}; "
                f"font-weight: {brand.FW_SEMIBOLD}; "
                f"font-size: {brand.FS_BODY}px;"
            )
            info_grid.addWidget(lbl, row, col)

            val = QLabel(str(value))
            val.setStyleSheet(f"color: {brand.TEXT}; font-size: {brand.FS_BODY}px;")
            info_grid.addWidget(val, row, col + 1)

            col += 2
            if col >= 4:
                col = 0
                row += 1

        detay_layout.addLayout(info_grid)

        # Hata tanimi
        ht_lbl = QLabel("Hata Tanimi:")
        ht_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        detay_layout.addWidget(ht_lbl)
        hata_text = QTextEdit()
        hata_text.setPlainText(self.kayit.get('hata_tanimi', ''))
        hata_text.setReadOnly(True)
        hata_text.setMaximumHeight(brand.sp(100))
        hata_text.setStyleSheet(f"""
            QTextEdit {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
        """)
        detay_layout.addWidget(hata_text)

        detay_layout.addStretch()
        tabs.addTab(detay_widget, "Detay")

        # Tab 2 - Aksiyonlar
        aksiyon_widget = QWidget()
        aksiyon_layout = QVBoxLayout(aksiyon_widget)
        aksiyon_layout.setSpacing(brand.SP_4)
        aksiyon_layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)

        # Aksiyon ekle butonu
        btn_aksiyon = QPushButton("Aksiyon Ekle")
        btn_aksiyon.setCursor(Qt.PointingHandCursor)
        btn_aksiyon.setFixedHeight(brand.sp(38))
        btn_aksiyon.setStyleSheet(_brand_btn(brand.PRIMARY, brand.PRIMARY_HOVER))
        btn_aksiyon.clicked.connect(self._aksiyon_ekle)
        aksiyon_layout.addWidget(btn_aksiyon, alignment=Qt.AlignLeft)

        # Aksiyon tablosu
        self.aksiyon_table = QTableWidget()
        self.aksiyon_table.setColumnCount(6)
        self.aksiyon_table.setHorizontalHeaderLabels([
            "Tip", "D Adimi", "Aciklama", "Sorumlu", "Hedef", "Durum"
        ])
        self.aksiyon_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.aksiyon_table.verticalHeader().setVisible(False)
        self.aksiyon_table.setShowGrid(False)
        self.aksiyon_table.setAlternatingRowColors(True)
        self.aksiyon_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.aksiyon_table.setStyleSheet(_table_css())

        self._refresh_aksiyonlar()
        aksiyon_layout.addWidget(self.aksiyon_table)

        tabs.addTab(aksiyon_widget, "Aksiyonlar")

        layout.addWidget(tabs, 1)

        # Alt butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)

        if self.kayit.get('durum') != 'KAPATILDI':
            btn_kapat = QPushButton("Kaydi Kapat")
            btn_kapat.setCursor(Qt.PointingHandCursor)
            btn_kapat.setFixedHeight(brand.sp(38))
            btn_kapat.setStyleSheet(_brand_btn(brand.SUCCESS, "#059669"))
            btn_kapat.clicked.connect(self._kaydi_kapat)
            btn_layout.addWidget(btn_kapat)

        btn_layout.addStretch()

        btn_kapat_dlg = QPushButton("Kapat")
        btn_kapat_dlg.setCursor(Qt.PointingHandCursor)
        btn_kapat_dlg.setFixedHeight(brand.sp(38))
        btn_kapat_dlg.setStyleSheet(_ghost_btn())
        btn_kapat_dlg.clicked.connect(self.accept)
        btn_layout.addWidget(btn_kapat_dlg)

        layout.addLayout(btn_layout)

    def _refresh_aksiyonlar(self):
        """Aksiyon tablosunu guncelle"""
        self.aksiyon_table.setRowCount(len(self.aksiyonlar))
        for i, a in enumerate(self.aksiyonlar):
            self.aksiyon_table.setItem(i, 0, QTableWidgetItem(a.get('tip', '')))

            d_adimi = a.get('d_adimi')
            self.aksiyon_table.setItem(i, 1, QTableWidgetItem(f"D{d_adimi}" if d_adimi else "-"))

            self.aksiyon_table.setItem(i, 2, QTableWidgetItem((a.get('aciklama', '') or '')[:50]))
            self.aksiyon_table.setItem(i, 3, QTableWidgetItem(a.get('sorumlu', '') or ''))

            hedef = a.get('hedef')
            self.aksiyon_table.setItem(i, 4, QTableWidgetItem(str(hedef) if hedef else '-'))

            durum = a.get('durum', '')
            durum_item = QTableWidgetItem(durum)
            if durum == 'TAMAMLANDI':
                durum_item.setForeground(QColor(brand.SUCCESS))
            elif durum == 'AÇIK':
                durum_item.setForeground(QColor(brand.WARNING))
            self.aksiyon_table.setItem(i, 5, durum_item)

    def _aksiyon_ekle(self):
        """Yeni aksiyon ekle"""
        QMessageBox.information(self, "Bilgi", "Aksiyon ekleme ozelligi yakinda eklenecek.")

    def _kaydi_kapat(self):
        """Kaydi kapat"""
        reply = QMessageBox.question(
            self, "Onay",
            "Bu uygunsuzluk kaydini kapatmak istediginize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE kalite.uygunsuzluklar
                    SET durum = 'KAPATILDI', kapanis_tarihi = CAST(GETDATE() AS DATE),
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (self.kayit_id,))
                conn.commit()
                LogManager.log_update('kalite', 'kalite.uygunsuzluklar', None, 'Durum guncellendi')

                QMessageBox.information(self, "Basarili", "Kayit kapatildi.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kayit kapatilamadi: {e}")
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass


# =====================================================================
# ANA SAYFA
# =====================================================================

class KaliteRedPage(BasePage):
    """Red Kayitlari / Uygunsuzluk Yonetimi Sayfasi — el kitabi uyumlu"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_all_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # ── 1. Header ──
        header = self.create_page_header(
            "Red Kayitlari / Uygunsuzluk Yonetimi",
            "Uretim redleri, musteri sikayetleri ve uygunsuzluk takibi"
        )

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_all_data)
        header.addWidget(btn_yenile)

        layout.addLayout(header)

        # ── TAB WIDGET ──
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
            QTabBar::tab {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                padding: {brand.SP_3}px {brand.SP_5}px;
                margin-right: {brand.SP_1}px;
                border-top-left-radius: {brand.R_SM}px;
                border-top-right-radius: {brand.R_SM}px;
                font-size: {brand.FS_BODY}px;
            }}
            QTabBar::tab:selected {{
                background: {brand.PRIMARY};
                color: white;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """)

        # TAB 1: Uretim Redleri
        self.uretim_tab = QWidget()
        self._setup_uretim_redler_tab()
        self.tab_widget.addTab(self.uretim_tab, "Uretim Redleri")

        # TAB 2: Uygunsuzluklar
        self.uygunsuzluk_tab = QWidget()
        self._setup_uygunsuzluk_tab()
        self.tab_widget.addTab(self.uygunsuzluk_tab, "Uygunsuzluklar")

        # TAB 3: Event Log
        self.event_log_tab = QWidget()
        self._setup_event_log_tab()
        self.tab_widget.addTab(self.event_log_tab, "Event Log")

        layout.addWidget(self.tab_widget)

    # -----------------------------------------------------------------
    # TAB 1: Uretim Redleri
    # -----------------------------------------------------------------
    def _setup_uretim_redler_tab(self):
        """Uretim Redleri sekmesi"""
        layout = QVBoxLayout(self.uretim_tab)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_4)

        # Ust bilgi
        info_layout = QHBoxLayout()
        info_lbl = QLabel("Uretimden gelen kalite kontrol red kayitlari")
        info_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;"
        )
        info_layout.addWidget(info_lbl)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # KPI kartlari
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self.uretim_stat_bekleyen = self.create_stat_card("BEKLEYEN", "0", color=brand.WARNING)
        kpi_row.addWidget(self.uretim_stat_bekleyen)

        self.uretim_stat_islenen = self.create_stat_card("ISLENEN", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self.uretim_stat_islenen)

        self.uretim_stat_toplam = self.create_stat_card("TOPLAM", "0", color=brand.PRIMARY)
        kpi_row.addWidget(self.uretim_stat_toplam)

        kpi_row.addStretch()
        layout.addLayout(kpi_row)

        # Filtreler
        filtre_layout = QHBoxLayout()
        filtre_layout.setSpacing(brand.SP_3)

        lbl_durum = QLabel("Durum:")
        lbl_durum.setStyleSheet(f"font-size: {brand.FS_BODY}px;")
        filtre_layout.addWidget(lbl_durum)
        self.uretim_durum_combo = QComboBox()
        self.uretim_durum_combo.addItems(['Tumu', 'BEKLIYOR', 'ISLENDI', 'IADE', 'HURDA'])
        self.uretim_durum_combo.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.uretim_durum_combo.currentIndexChanged.connect(self._load_uretim_redler)
        filtre_layout.addWidget(self.uretim_durum_combo)

        filtre_layout.addStretch()
        layout.addLayout(filtre_layout)

        # Tablo
        self.uretim_table = QTableWidget()
        self.uretim_table.setColumnCount(9)
        self.uretim_table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Is Emri", "Lot No", "Urun", "Red Adet", "Kontrol Eden", "Durum", "Islem"
        ])
        self.uretim_table.setColumnHidden(0, True)
        self.uretim_table.setColumnWidth(1, brand.sp(120))
        self.uretim_table.setColumnWidth(2, brand.sp(100))
        self.uretim_table.setColumnWidth(3, brand.sp(120))
        self.uretim_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.uretim_table.setColumnWidth(5, brand.sp(80))
        self.uretim_table.setColumnWidth(6, brand.sp(100))
        self.uretim_table.setColumnWidth(7, brand.sp(80))
        self.uretim_table.setColumnWidth(8, brand.sp(100))
        self.uretim_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.uretim_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.uretim_table.verticalHeader().setVisible(False)
        self.uretim_table.setShowGrid(False)
        self.uretim_table.setAlternatingRowColors(True)
        self.uretim_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.uretim_table.setStyleSheet(_table_css())
        self.uretim_table.doubleClicked.connect(self._uretim_red_detay)
        layout.addWidget(self.uretim_table)

    # -----------------------------------------------------------------
    # TAB 2: Uygunsuzluklar
    # -----------------------------------------------------------------
    def _setup_uygunsuzluk_tab(self):
        """Uygunsuzluklar sekmesi"""
        layout = QVBoxLayout(self.uygunsuzluk_tab)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_4)

        # Yeni kayit butonlari
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)

        btn_musteri = QPushButton("Musteri Sikayeti")
        btn_musteri.setCursor(Qt.PointingHandCursor)
        btn_musteri.setFixedHeight(brand.sp(38))
        btn_musteri.setStyleSheet(_brand_btn(brand.ERROR, "#DC2626"))
        btn_musteri.clicked.connect(lambda: self._yeni_kayit('MÜŞTERİ_ŞİKAYETİ'))
        btn_layout.addWidget(btn_musteri)

        btn_ic = QPushButton("Ic Red")
        btn_ic.setCursor(Qt.PointingHandCursor)
        btn_ic.setFixedHeight(brand.sp(38))
        btn_ic.setStyleSheet(_brand_btn(brand.WARNING, "#D97706"))
        btn_ic.clicked.connect(lambda: self._yeni_kayit('İÇ_RED'))
        btn_layout.addWidget(btn_ic)

        btn_tedarikci = QPushButton("Tedarikci Red")
        btn_tedarikci.setCursor(Qt.PointingHandCursor)
        btn_tedarikci.setFixedHeight(brand.sp(38))
        btn_tedarikci.setStyleSheet(_brand_btn(brand.INFO, "#2563EB"))
        btn_tedarikci.clicked.connect(lambda: self._yeni_kayit('TEDARİKÇİ_RED'))
        btn_layout.addWidget(btn_tedarikci)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # KPI kartlari
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self.stat_acik = self.create_stat_card("ACIK", "0", color=brand.WARNING)
        kpi_row.addWidget(self.stat_acik)

        self.stat_islemde = self.create_stat_card("ISLEMDE", "0", color=brand.INFO)
        kpi_row.addWidget(self.stat_islemde)

        self.stat_kapatilan = self.create_stat_card("KAPATILAN (BU AY)", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self.stat_kapatilan)

        self.stat_toplam = self.create_stat_card("TOPLAM (BU AY)", "0", color=brand.PRIMARY)
        kpi_row.addWidget(self.stat_toplam)

        kpi_row.addStretch()
        layout.addLayout(kpi_row)

        # Filtre
        filtre_layout = QHBoxLayout()
        filtre_layout.setSpacing(brand.SP_3)

        lbl_d = QLabel("Durum:")
        lbl_d.setStyleSheet(f"font-size: {brand.FS_BODY}px;")
        filtre_layout.addWidget(lbl_d)
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(['Tumu', 'AÇIK', 'İŞLEMDE', 'KAPATILDI'])
        self.cmb_durum.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.cmb_durum.currentIndexChanged.connect(self._load_data)
        filtre_layout.addWidget(self.cmb_durum)

        lbl_t = QLabel("Tip:")
        lbl_t.setStyleSheet(f"font-size: {brand.FS_BODY}px;")
        filtre_layout.addWidget(lbl_t)
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(['Tumu', 'MÜŞTERİ_ŞİKAYETİ', 'İÇ_RED', 'TEDARİKÇİ_RED', 'PROSES_RED', 'DENETİM_BULGUSU'])
        self.cmb_tip.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.cmb_tip.currentIndexChanged.connect(self._load_data)
        filtre_layout.addWidget(self.cmb_tip)

        filtre_layout.addStretch()
        layout.addLayout(filtre_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kayit No", "Tip", "Tarih", "Musteri/Tedarikci", "Urun", "Oncelik", "Durum", "Islem"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setColumnWidth(8, brand.sp(120))
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setStyleSheet(_table_css())
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

    # -----------------------------------------------------------------
    # TAB 3: Event Log
    # -----------------------------------------------------------------
    def _setup_event_log_tab(self):
        """Event Log sekmesi"""
        from .kalite_event_log import EventLogPage

        layout = QVBoxLayout(self.event_log_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        event_log_widget = EventLogPage(self.theme)
        layout.addWidget(event_log_widget)

    # -----------------------------------------------------------------
    # DATA LOADING
    # -----------------------------------------------------------------
    def _load_all_data(self):
        """Tum sekmelerin verilerini yukle"""
        self._load_uretim_redler()
        self._load_data()

    def _load_uretim_redler(self):
        """Uretim redleri verilerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            durum_filtre = self.uretim_durum_combo.currentText()

            # Tablo var mi kontrol et, yoksa olustur
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables t
                              JOIN sys.schemas s ON t.schema_id = s.schema_id
                              WHERE s.name = 'kalite' AND t.name = 'uretim_redler')
                BEGIN
                    CREATE TABLE kalite.uretim_redler (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        is_emri_id INT,
                        lot_no NVARCHAR(50),
                        red_miktar INT,
                        kontrol_id INT,
                        red_tarihi DATETIME DEFAULT GETDATE(),
                        kontrol_eden_id INT,
                        durum NVARCHAR(20) DEFAULT 'BEKLIYOR',
                        islem_tipi NVARCHAR(20),
                        aciklama NVARCHAR(500),
                        olusturma_tarihi DATETIME DEFAULT GETDATE(),
                        guncelleme_tarihi DATETIME
                    )
                END
            """)
            conn.commit()

            # Veri cek
            where_clause = ""
            params = []
            if durum_filtre != 'Tumu':
                where_clause = "WHERE ur.durum = ?"
                params.append(durum_filtre)

            cursor.execute(f"""
                SELECT ur.id, ur.red_tarihi, ie.is_emri_no, ur.lot_no, ie.stok_adi,
                       ur.red_miktar, p.ad + ' ' + p.soyad as kontrolcu, ur.durum
                FROM kalite.uretim_redler ur
                LEFT JOIN siparis.is_emirleri ie ON ur.is_emri_id = ie.id
                LEFT JOIN ik.personeller p ON ur.kontrol_eden_id = p.id
                {where_clause}
                ORDER BY ur.red_tarihi DESC
            """, params)

            rows = cursor.fetchall()
            self.uretim_table.setRowCount(len(rows))

            bekleyen = 0
            islenen = 0

            for i, row in enumerate(rows):
                self.uretim_table.setItem(i, 0, QTableWidgetItem(str(row[0])))

                # Tarih
                tarih = row[1]
                tarih_str = tarih.strftime('%d.%m.%Y') if tarih else '-'
                self.uretim_table.setItem(i, 1, QTableWidgetItem(tarih_str))

                # Is emri
                ie_item = QTableWidgetItem(row[2] or '-')
                ie_item.setForeground(QColor(brand.PRIMARY))
                self.uretim_table.setItem(i, 2, ie_item)

                # Lot no
                self.uretim_table.setItem(i, 3, QTableWidgetItem(row[3] or '-'))

                # Urun
                self.uretim_table.setItem(i, 4, QTableWidgetItem((row[4] or '')[:30]))

                # Red adet
                adet_item = QTableWidgetItem(f"{row[5] or 0:,}")
                adet_item.setTextAlignment(Qt.AlignCenter)
                adet_item.setForeground(QColor(brand.ERROR))
                self.uretim_table.setItem(i, 5, adet_item)

                # Kontrol eden
                self.uretim_table.setItem(i, 6, QTableWidgetItem(row[6] or '-'))

                # Durum
                durum = row[7] or 'BEKLIYOR'
                durum_item = QTableWidgetItem(durum)
                if durum == 'BEKLIYOR':
                    durum_item.setForeground(QColor(brand.WARNING))
                    bekleyen += 1
                elif durum in ('İŞLENDİ', 'İADE', 'HURDA'):
                    durum_item.setForeground(QColor(brand.SUCCESS))
                    islenen += 1
                self.uretim_table.setItem(i, 7, durum_item)

                # Islem butonu
                widget = self.create_action_buttons([
                    ("Isle", "Isle", lambda checked, rid=row[0]: self._isle_uretim_red(rid), "edit"),
                ])
                self.uretim_table.setCellWidget(i, 8, widget)

            # Istatistikleri guncelle
            self.uretim_stat_bekleyen.findChild(QLabel, "stat_value").setText(str(bekleyen))
            self.uretim_stat_islenen.findChild(QLabel, "stat_value").setText(str(islenen))
            self.uretim_stat_toplam.findChild(QLabel, "stat_value").setText(str(len(rows)))

        except Exception as e:
            print(f"Uretim redleri yukleme hatasi: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _isle_uretim_red(self, red_id: int):
        """Uretim red kaydini isle"""
        conn = None
        try:
            # Red kaydini al
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    ur.id, ur.lot_no, ur.red_miktar, ur.is_emri_id,
                    ur.kontrol_eden_id, ur.durum, ur.aciklama,
                    ie.stok_adi, ie.stok_kodu, ie.urun_id, ie.cari_unvani,
                    ur.red_tarihi, ht.ad as hata_turu_adi
                FROM kalite.uretim_redler ur
                LEFT JOIN siparis.is_emirleri ie ON ur.is_emri_id = ie.id
                LEFT JOIN tanim.hata_turleri ht ON ur.hata_turu_id = ht.id
                WHERE ur.id = ?
            """, (red_id,))

            row = cursor.fetchone()
            if not row:
                QMessageBox.warning(self, "Uyari", "Red kaydi bulunamadi!")
                return

            # Red kayit verisi
            red_kayit = {
                'id': row[0],
                'lot_no': row[1],
                'red_miktar': row[2],
                'is_emri_id': row[3],
                'kontrol_eden_id': row[4],
                'durum': row[5],
                'aciklama': row[6],
                'urun_adi': row[7],
                'stok_kodu': row[8],
                'urun_id': row[9],
                'musteri': row[10],
                'red_tarihi': row[11],
                'hata_turu_adi': row[12]
            }

            # Durum kontrolu
            if red_kayit['durum'] not in ['BEKLIYOR', 'MUSTERI_ONAY', None]:
                QMessageBox.information(self, "Bilgi",
                    f"Bu kayit zaten islenmis. Durum: {red_kayit['durum']}")
                return

            conn.close()
            conn = None

            # Karar dialog'unu ac
            dlg = RedKararDialog(self.theme, red_kayit, self)
            if dlg.exec() != QDialog.Accepted:
                return

            karar = dlg.get_karar()
            if not karar:
                return

            # Karari isle
            self._isle_karar(karar)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Islem hatasi: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _get_depo_id(self, kod: str) -> int:
        """Depo kodundan ID al"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tanim.depolar WHERE kod = ?", (kod,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"Depo ID alma hatasi: {e}")
            return None
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _isle_karar(self, karar: dict):
        """Karari isle ve stok hareketini yap"""
        conn = None
        try:
            karar_tip = karar['tip']
            karar_not = karar['not']
            red_kayit = karar['red_kayit']
            islem_miktar = karar.get('miktar', red_kayit['red_miktar'])
            kalan_miktar = karar.get('kalan_miktar', 0)

            conn = get_db_connection()
            cursor = conn.cursor()
            motor = HareketMotoru(conn)

            # Depo ID'leri
            # NOT: Hardcoded id fallback'lari kaldirildi (10/11/12 gibi sabitler depo
            # silinince/deaktive edilince yanlis depoya yazma riski - MAMUL bug'i ornegi).
            # Eksik depo varsa kullaniciya net hata gostermek daha guvenli.
            RED_DEPO_ID = self._get_depo_id('RED')
            FKK_DEPO_ID = self._get_depo_id('FKK')
            SOKUM_DEPO_ID = self._get_depo_id('SOKUM') or self._get_depo_id('Yi')
            KAR_DEPO_ID = self._get_depo_id('KARANTINA') or self._get_depo_id('KAR')

            _eksik = []
            if not RED_DEPO_ID: _eksik.append('RED')
            if not FKK_DEPO_ID: _eksik.append('FKK')
            if karar_tip == 'SOKUM' and not SOKUM_DEPO_ID: _eksik.append('SOKUM/Yi')
            if karar_tip == 'MUSTERI_ONAY' and not KAR_DEPO_ID: _eksik.append('KARANTINA')
            if _eksik:
                raise Exception(f"Eksik/aktif olmayan depolar: {', '.join(_eksik)}")

            # Akis sablonu ID'lerini al
            sablon_id = None
            if karar_tip == 'KABUL':
                sablon_id = self._get_akis_sablon_id(cursor, 'RED-KABUL') or self._get_akis_sablon_id(cursor, 'RED KABUL')
            elif karar_tip == 'SOKUM':
                sablon_id = self._get_akis_sablon_id(cursor, 'söküm') or self._get_akis_sablon_id(cursor, 'SOKUM')
            elif karar_tip == 'MUSTERI_ONAY':
                sablon_id = self._get_akis_sablon_id(cursor, 'RED-KARANTINA') or self._get_akis_sablon_id(cursor, 'RED KARANTINA')

            print(f"DEBUG: Karar tip={karar_tip}, Akis sablonu ID={sablon_id}")

            # Kullanici ID
            user_id = ModernLoginDialog.current_user_id or 1

            if karar_tip == 'KABUL':
                self._isle_kabul(red_kayit, karar_not, motor, cursor, user_id,
                                RED_DEPO_ID, FKK_DEPO_ID, islem_miktar, sablon_id)

            elif karar_tip == 'SOKUM':
                self._isle_sokum(red_kayit, karar_not, motor, cursor, user_id,
                                RED_DEPO_ID, SOKUM_DEPO_ID, islem_miktar, sablon_id)

            elif karar_tip == 'MUSTERI_ONAY':
                self._isle_musteri_onay(red_kayit, karar_not, motor, cursor, user_id,
                                       RED_DEPO_ID, KAR_DEPO_ID, islem_miktar, sablon_id)

            # Kalan miktar varsa red kaydini guncelle
            if kalan_miktar > 0:
                cursor.execute("""
                    UPDATE kalite.uretim_redler
                    SET red_miktar = ?,
                        durum = 'BEKLIYOR',
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (kalan_miktar, red_kayit['id']))
                print(f"DEBUG: Kalan miktar guncellendi: {kalan_miktar}, durum=BEKLIYOR")

            # OBSERVER - EVENT KAYDI
            try:
                from utils.hareket_observer import HareketObserver
                observer = HareketObserver(conn)

                hedef_depo = None
                if karar_tip == 'KABUL':
                    hedef_depo = FKK_DEPO_ID
                elif karar_tip == 'SOKUM':
                    hedef_depo = SOKUM_DEPO_ID
                elif karar_tip == 'MUSTERI_ONAY':
                    hedef_depo = KAR_DEPO_ID

                if hedef_depo:
                    observer.on_hareket_completed(
                        lot_no=red_kayit['lot_no'],
                        depo_id=hedef_depo,
                        miktar=islem_miktar
                    )
            except Exception as e:
                print(f"Observer hatasi (onemsiz): {e}")

            conn.commit()

            karar_mesajlari = {
                'KABUL': f'{islem_miktar} adet Final Kalite deposuna gonderildi.',
                'SOKUM': f'{islem_miktar} adet Sokum Istasyonuna gonderildi.',
                'MUSTERI_ONAY': f'{islem_miktar} adet Karantina deposuna gonderildi.'
            }

            kalan_msg = f"\n\nKalan: {kalan_miktar} adet RED'de bekliyor." if kalan_miktar > 0 else ""

            QMessageBox.information(self, "Basarili",
                f"Karar: {karar_tip}\n\n{karar_mesajlari.get(karar_tip, '')}{kalan_msg}")

            self._load_uretim_redler()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Karar isleme hatasi: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _get_akis_sablon_id(self, cursor, kod: str):
        """Akis sablonu ID'sini al"""
        try:
            cursor.execute("""
                SELECT id FROM tanim.akis_sablon
                WHERE kod = ? AND aktif_mi = 1
            """, (kod,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception:
            return None

    def _isle_kabul(self, red_kayit: dict, karar_not: str, motor, cursor,
                    user_id: int, red_depo_id: int, fkk_depo_id: int,
                    islem_miktar: int = None, sablon_id: int = None):
        """KABUL kararini isle - RED -> FKK transfer"""
        orijinal_lot = red_kayit['lot_no']
        miktar = islem_miktar if islem_miktar else red_kayit['red_miktar']

        lot_prefix = '-'.join(orijinal_lot.split('-')[:3])

        cursor.execute("""
            SELECT lot_no, depo_id, miktar FROM stok.stok_bakiye
            WHERE miktar > 0 AND (
                lot_no = ? OR
                lot_no LIKE ? OR
                lot_no = ?
            )
            ORDER BY
                CASE WHEN depo_id = ? THEN 0 ELSE 1 END,
                CASE WHEN lot_no LIKE '%-RED' AND lot_no NOT LIKE '%-RED-S' THEN 0 ELSE 1 END
        """, (orijinal_lot, f"{lot_prefix}%-RED", f"{orijinal_lot}-RED", red_depo_id))

        red_lot_rows = cursor.fetchall()
        if red_lot_rows:
            red_lot_no = red_lot_rows[0][0]
            kaynak_depo_id = red_lot_rows[0][1]
            mevcut_miktar = red_lot_rows[0][2]
            print(f"DEBUG: Bulunan lot: {red_lot_no}, depo={kaynak_depo_id}, miktar={mevcut_miktar}")
        else:
            raise Exception(f"RED deposunda stok bulunamadi! Lot: {orijinal_lot}")

        if miktar > mevcut_miktar:
            raise Exception(f"Yetersiz stok! Istenen: {miktar}, Mevcut: {mevcut_miktar}")

        cursor.execute("""
            SELECT id, miktar FROM stok.stok_bakiye
            WHERE lot_no = ? AND depo_id = ?
        """, (red_lot_no, fkk_depo_id))
        mevcut_fkk = cursor.fetchall()

        if mevcut_fkk:
            yeni_miktar = mevcut_fkk[0][1] + miktar

            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET miktar = miktar - ?
                WHERE lot_no = ? AND depo_id = ? AND miktar >= ?
            """, (miktar, red_lot_no, kaynak_depo_id, miktar))

            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET miktar = ?,
                    kalite_durumu = 'BEKLIYOR',
                    durum_kodu = 'FKK_BEKLIYOR'
                WHERE lot_no = ? AND depo_id = ?
            """, (yeni_miktar, red_lot_no, fkk_depo_id))

            print(f"DEBUG: Mevcut FKK lot'una eklendi: {red_lot_no}, yeni miktar={yeni_miktar}")
        else:
            sonuc = motor.transfer(
                lot_no=red_lot_no,
                hedef_depo_id=fkk_depo_id,
                miktar=miktar,
                kaynak="KALITE_RED",
                kaynak_id=red_kayit['id'],
                aciklama=f"Red depot kabulu - {karar_not}" if karar_not else "Red depot kabulu"
            )

            if not sonuc.basarili:
                raise Exception(f"Stok hareketi basarisiz: {sonuc.mesaj}")

            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET kalite_durumu = 'BEKLIYOR',
                    durum_kodu = 'FKK_BEKLIYOR'
                WHERE lot_no = ? AND depo_id = ?
            """, (red_lot_no, fkk_depo_id))

        cursor.execute("""
            UPDATE kalite.uretim_redler
            SET durum = 'KABUL',
                karar = 'KABUL',
                karar_veren_id = ?,
                karar_tarihi = GETDATE(),
                karar_notu = ?,
                guncelleme_tarihi = GETDATE()
            WHERE id = ?
        """, (user_id, karar_not, red_kayit['id']))

        print(f"KABUL islemi tamamlandi: {red_lot_no} -> FKK ({miktar} adet)")

    def _isle_sokum(self, red_kayit: dict, karar_not: str, motor, cursor,
                    user_id: int, red_depo_id: int, sokum_depo_id: int,
                    islem_miktar: int = None, sablon_id: int = None):
        """SOKUM kararini isle - RED -> XI, lot'a -S eki"""
        orijinal_lot = red_kayit['lot_no']
        miktar = islem_miktar if islem_miktar else red_kayit['red_miktar']

        lot_prefix = '-'.join(orijinal_lot.split('-')[:3])

        cursor.execute("""
            SELECT lot_no, depo_id, miktar FROM stok.stok_bakiye
            WHERE miktar > 0 AND (
                lot_no = ? OR
                lot_no LIKE ? OR
                lot_no = ?
            ) AND lot_no NOT LIKE '%-RED-S'
            ORDER BY
                CASE WHEN depo_id = ? THEN 0 ELSE 1 END,
                CASE WHEN lot_no LIKE '%-RED' THEN 0 ELSE 1 END
        """, (orijinal_lot, f"{lot_prefix}%-RED", f"{orijinal_lot}-RED", red_depo_id))

        red_lot_rows = cursor.fetchall()
        if red_lot_rows:
            red_lot_no = red_lot_rows[0][0]
            kaynak_depo_id = red_lot_rows[0][1]
            mevcut_miktar = red_lot_rows[0][2]
            print(f"DEBUG: Bulunan lot: {red_lot_no}, depo={kaynak_depo_id}, miktar={mevcut_miktar}")
        else:
            raise Exception(f"RED deposunda stok bulunamadi! Lot: {orijinal_lot}")

        if miktar > mevcut_miktar:
            raise Exception(f"Yetersiz stok! Istenen: {miktar}, Mevcut: {mevcut_miktar}")

        sokum_lot = f"{red_lot_no}-S"

        cursor.execute("""
            SELECT id, miktar FROM stok.stok_bakiye
            WHERE lot_no = ? AND depo_id = ?
        """, (sokum_lot, sokum_depo_id))
        mevcut_sokum = cursor.fetchall()

        if mevcut_sokum:
            yeni_miktar = mevcut_sokum[0][1] + miktar

            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET miktar = miktar - ?
                WHERE lot_no = ? AND depo_id = ? AND miktar >= ?
            """, (miktar, red_lot_no, kaynak_depo_id, miktar))

            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET miktar = ?,
                    durum_kodu = 'SOKUM'
                WHERE lot_no = ? AND depo_id = ?
            """, (yeni_miktar, sokum_lot, sokum_depo_id))

            print(f"DEBUG: Mevcut sokum lot'una eklendi: {sokum_lot}, yeni miktar={yeni_miktar}")
        else:
            sonuc = motor.transfer(
                lot_no=red_lot_no,
                hedef_depo_id=sokum_depo_id,
                miktar=miktar,
                kaynak="KALITE_RED",
                kaynak_id=red_kayit['id'],
                aciklama=f"Sokum icin transfer - {karar_not}" if karar_not else "Sokum icin transfer"
            )

            if not sonuc.basarili:
                raise Exception(f"Stok transferi basarisiz: {sonuc.mesaj}")

            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET lot_no = ?,
                    kalite_durumu = 'SOKUM_BEKLIYOR',
                    durum_kodu = 'SOKUM'
                WHERE lot_no = ? AND depo_id = ?
            """, (sokum_lot, red_lot_no, sokum_depo_id))

        cursor.execute("""
            UPDATE kalite.uretim_redler
            SET durum = 'SOKUM_BEKLIYOR',
                karar = 'SOKUM',
                karar_veren_id = ?,
                karar_tarihi = GETDATE(),
                karar_notu = ?,
                guncelleme_tarihi = GETDATE()
            WHERE id = ?
        """, (user_id, karar_not, red_kayit['id']))

        print(f"Sokum islemi tamamlandi: {red_lot_no} -> {sokum_lot} (XI deposu, {miktar} adet)")

    def _isle_musteri_onay(self, red_kayit: dict, karar_not: str, motor, cursor,
                           user_id: int, red_depo_id: int, kar_depo_id: int,
                           islem_miktar: int = None, sablon_id: int = None):
        """MUSTERI ONAYI kararini isle - RED -> KAR (Karantina) transfer"""
        orijinal_lot = red_kayit['lot_no']
        miktar = islem_miktar if islem_miktar else red_kayit['red_miktar']

        lot_prefix = '-'.join(orijinal_lot.split('-')[:3])

        cursor.execute("""
            SELECT lot_no, depo_id, miktar FROM stok.stok_bakiye
            WHERE miktar > 0 AND (
                lot_no = ? OR
                lot_no LIKE ? OR
                lot_no = ?
            ) AND lot_no NOT LIKE '%-RED-S'
            ORDER BY
                CASE WHEN depo_id = ? THEN 0 ELSE 1 END,
                CASE WHEN lot_no LIKE '%-RED' THEN 0 ELSE 1 END
        """, (orijinal_lot, f"{lot_prefix}%-RED", f"{orijinal_lot}-RED", red_depo_id))

        red_lot_rows = cursor.fetchall()
        if red_lot_rows:
            red_lot_no = red_lot_rows[0][0]
            kaynak_depo_id = red_lot_rows[0][1]
            mevcut_miktar = red_lot_rows[0][2]
            print(f"DEBUG: Bulunan lot: {red_lot_no}, depo={kaynak_depo_id}, miktar={mevcut_miktar}")
        else:
            raise Exception(f"RED deposunda stok bulunamadi! Lot: {orijinal_lot}")

        if miktar > mevcut_miktar:
            raise Exception(f"Yetersiz stok! Istenen: {miktar}, Mevcut: {mevcut_miktar}")

        if kar_depo_id:
            sonuc = motor.transfer(
                lot_no=red_lot_no,
                hedef_depo_id=kar_depo_id,
                miktar=miktar,
                kaynak="KALITE_RED",
                kaynak_id=red_kayit['id'],
                aciklama=f"Musteri onayi icin karantinaya - {karar_not}" if karar_not else "Musteri onayi icin karantinaya"
            )

            if not sonuc.basarili:
                raise Exception(f"Stok hareketi basarisiz: {sonuc.mesaj}")

            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET kalite_durumu = 'MUSTERI_ONAY_BEKLIYOR',
                    durum_kodu = 'KARANTINA'
                WHERE lot_no = ? AND depo_id = ?
            """, (red_lot_no, kar_depo_id))

        cursor.execute("""
            UPDATE kalite.uretim_redler
            SET durum = 'MUSTERI_ONAY',
                karar = 'MUSTERI_ONAY',
                karar_veren_id = ?,
                karar_tarihi = GETDATE(),
                karar_notu = ?,
                guncelleme_tarihi = GETDATE()
            WHERE id = ?
        """, (user_id, karar_not, red_kayit['id']))

        print(f"Musteri onayi icin karantinaya alindi: {red_lot_no} ({miktar} adet)")

    def _uretim_red_detay(self, index):
        """Uretim red detayi goster"""
        row = index.row()
        red_id = int(self.uretim_table.item(row, 0).text())
        QMessageBox.information(self, "Detay", f"Red ID: {red_id} detaylari yakinda eklenecek.")

    def _yeni_kayit(self, tip: str):
        """Yeni uygunsuzluk kaydi"""
        dlg = UygunsuzlukDialog(self.theme, tip, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _on_double_click(self, index):
        """Satira cift tiklama"""
        row = index.row()
        kayit_id = int(self.table.item(row, 0).text())
        dlg = UygunsuzlukDetayDialog(self.theme, kayit_id, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _detay_goster(self, kayit_id: int):
        """Detay dialog'unu goster"""
        dlg = UygunsuzlukDetayDialog(self.theme, kayit_id, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _load_data(self):
        """Verileri yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Filtreler
            durum_filtre = self.cmb_durum.currentText()
            tip_filtre = self.cmb_tip.currentText()

            where_clauses = []
            params = []

            if durum_filtre != 'Tumu':
                where_clauses.append("u.durum = ?")
                params.append(durum_filtre)

            if tip_filtre != 'Tumu':
                where_clauses.append("u.kayit_tipi = ?")
                params.append(tip_filtre)

            where_sql = " AND " + " AND ".join(where_clauses) if where_clauses else ""

            cursor.execute(f"""
                SELECT TOP 200 u.id, u.kayit_no, u.kayit_tipi, u.kayit_tarihi,
                       c.unvan, s.urun_adi, u.oncelik, u.durum
                FROM kalite.uygunsuzluklar u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN stok.urunler s ON u.urun_id = s.id
                WHERE 1=1 {where_sql}
                ORDER BY u.kayit_tarihi DESC, u.id DESC
            """, params)

            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))

                # Tip
                tip = row[2] or ''
                tip_item = QTableWidgetItem(tip.replace('_', ' '))
                self.table.setItem(i, 2, tip_item)

                # Tarih
                tarih = row[3]
                tarih_str = tarih.strftime('%d.%m.%Y') if tarih else '-'
                self.table.setItem(i, 3, QTableWidgetItem(tarih_str))

                self.table.setItem(i, 4, QTableWidgetItem((row[4] or '')[:30]))
                self.table.setItem(i, 5, QTableWidgetItem((row[5] or '')[:30]))

                # Oncelik
                oncelik = row[6] or ''
                oncelik_item = QTableWidgetItem(oncelik)
                oncelik_colors = {
                    'KRİTİK': brand.ERROR,
                    'YÜKSEK': brand.WARNING,
                    'NORMAL': brand.INFO,
                    'DÜŞÜK': brand.TEXT_MUTED
                }
                if oncelik in oncelik_colors:
                    oncelik_item.setForeground(QColor(oncelik_colors[oncelik]))
                self.table.setItem(i, 6, oncelik_item)

                # Durum
                durum = row[7] or ''
                durum_item = QTableWidgetItem(durum)
                durum_colors = {
                    'AÇIK': brand.WARNING,
                    'İŞLEMDE': brand.INFO,
                    'KAPATILDI': brand.SUCCESS,
                    'İPTAL': brand.TEXT_MUTED
                }
                if durum in durum_colors:
                    durum_item.setForeground(QColor(durum_colors[durum]))
                self.table.setItem(i, 7, durum_item)

                # Islem butonu
                widget = self.create_action_buttons([
                    ("Detay", "Detay", lambda checked, kid=row[0]: self._detay_goster(kid), "info"),
                ])
                self.table.setCellWidget(i, 8, widget)

            # Istatistikler
            cursor.execute("SELECT COUNT(*) FROM kalite.uygunsuzluklar WHERE durum = 'AÇIK'")
            self.stat_acik.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM kalite.uygunsuzluklar WHERE durum = 'İŞLEMDE'")
            self.stat_islemde.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            cursor.execute("""
                SELECT COUNT(*) FROM kalite.uygunsuzluklar
                WHERE durum = 'KAPATILDI' AND MONTH(kapanis_tarihi) = MONTH(GETDATE()) AND YEAR(kapanis_tarihi) = YEAR(GETDATE())
            """)
            self.stat_kapatilan.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            cursor.execute("""
                SELECT COUNT(*) FROM kalite.uygunsuzluklar
                WHERE MONTH(kayit_tarihi) = MONTH(GETDATE()) AND YEAR(kayit_tarihi) = YEAR(GETDATE())
            """)
            self.stat_toplam.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

        except Exception as e:
            print(f"Veri yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
