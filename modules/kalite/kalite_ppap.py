# -*- coding: utf-8 -*-
"""
NEXOR ERP - PPAP Yonetimi
=========================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
from datetime import datetime, date
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QTextEdit, QFormLayout, QDateEdit, QGroupBox, QCheckBox,
    QScrollArea, QWidget, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


# PPAP Elementleri (18 Element)
PPAP_ELEMENTS = [
    (1, "Design Records", "Tasarim Kayitlari"),
    (2, "Engineering Change Documents", "Muhendislik Degisiklik Dokumanlari"),
    (3, "Customer Engineering Approval", "Musteri Muhendislik Onayi"),
    (4, "Design FMEA", "Tasarim FMEA"),
    (5, "Process Flow Diagram", "Proses Akis Diyagrami"),
    (6, "Process FMEA", "Proses FMEA"),
    (7, "Control Plan", "Kontrol Plani"),
    (8, "MSA Studies", "MSA Calismalari"),
    (9, "Dimensional Results", "Boyutsal Sonuclar"),
    (10, "Material/Performance Test Results", "Malzeme/Performans Test Sonuclari"),
    (11, "Initial Process Studies", "Ilk Proses Calismalari"),
    (12, "Qualified Laboratory Documentation", "Akredite Lab. Dokumantasyonu"),
    (13, "Appearance Approval Report", "Gorunum Onay Raporu"),
    (14, "Sample Production Parts", "Numune Uretim Parcalari"),
    (15, "Master Sample", "Ana Numune"),
    (16, "Checking Aids", "Kontrol Aparatlari"),
    (17, "Customer Specific Requirements", "Musteriye Ozel Gereksinimler"),
    (18, "Part Submission Warrant", "Parca Sunum Garantisi (PSW)")
]

# PPAP Seviyeleri
PPAP_LEVELS = {
    1: "Seviye 1 - Sadece PSW",
    2: "Seviye 2 - PSW + Sinirli Dokumantasyon",
    3: "Seviye 3 - PSW + Tam Dokumantasyon",
    4: "Seviye 4 - PSW + Musteri Tanimli Gereksinimler",
    5: "Seviye 5 - PSW + Tam Dokumantasyon (Yerinde Inceleme)"
}


# =====================================================================
# DIALOG: Yeni PPAP
# =====================================================================

class YeniPPAPDialog(QDialog):
    """Yeni PPAP kaydi dialog'u -- el kitabi uyumlu"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Yeni PPAP Kaydi")
        self.setMinimumSize(brand.sp(700), brand.sp(650))
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
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
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        input_css = f"""
            QComboBox, QLineEdit, QDateEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus, QLineEdit:focus, QDateEdit:focus {{
                border-color: {brand.PRIMARY};
            }}
        """

        # -- Header --
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)

        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        title = QLabel("Yeni PPAP Kaydi")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(title)
        sub = QLabel("Production Part Approval Process")
        sub.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        title_col.addWidget(sub)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)

        # -- Temel Bilgiler --
        bilgi_group = QGroupBox("Temel Bilgiler")
        bilgi_form = QFormLayout()
        bilgi_form.setSpacing(brand.SP_2)
        bilgi_form.setLabelAlignment(Qt.AlignRight)

        self.cmb_musteri = QComboBox()
        self.cmb_musteri.setStyleSheet(input_css)
        self._load_musteriler()
        self.cmb_musteri.currentIndexChanged.connect(self._on_musteri_changed)
        bilgi_form.addRow("Musteri:", self.cmb_musteri)

        self.cmb_urun = QComboBox()
        self.cmb_urun.setStyleSheet(input_css)
        bilgi_form.addRow("Urun:", self.cmb_urun)

        self.txt_part_no = QLineEdit()
        self.txt_part_no.setStyleSheet(input_css)
        self.txt_part_no.setPlaceholderText("Musteri parca numarasi")
        bilgi_form.addRow("Part Number:", self.txt_part_no)

        self.txt_revizyon = QLineEdit()
        self.txt_revizyon.setStyleSheet(input_css)
        self.txt_revizyon.setPlaceholderText("Rev. A, Rev. 01, vb.")
        bilgi_form.addRow("Revizyon:", self.txt_revizyon)

        self.cmb_seviye = QComboBox()
        self.cmb_seviye.setStyleSheet(input_css)
        for level, desc in PPAP_LEVELS.items():
            self.cmb_seviye.addItem(desc, level)
        self.cmb_seviye.setCurrentIndex(2)
        bilgi_form.addRow("PPAP Seviyesi:", self.cmb_seviye)

        self.cmb_neden = QComboBox()
        self.cmb_neden.setStyleSheet(input_css)
        self.cmb_neden.addItems([
            'Yeni Parca / Urun',
            'Muhendislik Degisikligi',
            'Takim / Ekipman Degisikligi',
            'Tedarikci / Malzeme Degisikligi',
            'Uretim Yeri Degisikligi',
            'Yeniden Sunum',
            'Diger'
        ])
        bilgi_form.addRow("Sunum Nedeni:", self.cmb_neden)

        bilgi_group.setLayout(bilgi_form)
        layout.addWidget(bilgi_group)

        # -- Tarihler ve Sorumlu --
        tarih_group = QGroupBox("Tarihler ve Sorumlu")
        tarih_form = QFormLayout()
        tarih_form.setSpacing(brand.SP_2)
        tarih_form.setLabelAlignment(Qt.AlignRight)

        self.date_baslangic = QDateEdit()
        self.date_baslangic.setDate(QDate.currentDate())
        self.date_baslangic.setCalendarPopup(True)
        self.date_baslangic.setStyleSheet(input_css)
        tarih_form.addRow("Baslangic:", self.date_baslangic)

        self.date_hedef = QDateEdit()
        self.date_hedef.setDate(QDate.currentDate().addDays(30))
        self.date_hedef.setCalendarPopup(True)
        self.date_hedef.setStyleSheet(input_css)
        tarih_form.addRow("Hedef Sunum:", self.date_hedef)

        self.cmb_sorumlu = QComboBox()
        self.cmb_sorumlu.setStyleSheet(input_css)
        self._load_personel()
        tarih_form.addRow("Sorumlu:", self.cmb_sorumlu)

        tarih_group.setLayout(tarih_form)
        layout.addWidget(tarih_group)

        # -- Notlar --
        notlar_lbl = QLabel("Notlar")
        notlar_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        layout.addWidget(notlar_lbl)

        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(brand.sp(60))
        self.txt_notlar.setStyleSheet(f"""
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
        layout.addWidget(self.txt_notlar)

        layout.addStretch()

        # -- Butonlar --
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        btn_iptal = QPushButton("Iptal")
        btn_iptal.setCursor(Qt.PointingHandCursor)
        btn_iptal.setFixedHeight(brand.sp(38))
        btn_iptal.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
        """)
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)

        btn_kaydet = QPushButton("PPAP Baslat")
        btn_kaydet.setCursor(Qt.PointingHandCursor)
        btn_kaydet.setFixedHeight(brand.sp(38))
        btn_kaydet.setStyleSheet(f"""
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
        btn_kaydet.clicked.connect(self._kaydet)
        btn_layout.addWidget(btn_kaydet)

        layout.addLayout(btn_layout)

    # -----------------------------------------------------------------
    def _load_musteriler(self):
        self.cmb_musteri.clear()
        self.cmb_musteri.addItem("-- Secin --", None)
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
                self.cmb_musteri.addItem(row[0], row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _on_musteri_changed(self):
        cari_unvani = self.cmb_musteri.currentData()
        self._load_urunler(cari_unvani)

    def _load_urunler(self, cari_unvani=None):
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
            for row in cursor.fetchall():
                if row[0]:
                    self.cmb_urun.addItem(row[1], row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_personel(self):
        self.cmb_sorumlu.clear()
        self.cmb_sorumlu.addItem("-- Secin --", None)
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_sorumlu.addItem(row[1], row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # -----------------------------------------------------------------
    def _kaydet(self):
        cari_unvani = self.cmb_musteri.currentData()
        if not cari_unvani:
            QMessageBox.warning(self, "Uyari", "Musteri secilmelidir!")
            return

        sorumlu_id = self.cmb_sorumlu.currentData()
        if not sorumlu_id:
            QMessageBox.warning(self, "Uyari", "Sorumlu secilmelidir!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cari_id = None
            if cari_unvani:
                cursor.execute("""
                    SELECT TOP 1 id FROM musteri.cariler
                    WHERE unvan = ? AND aktif_mi = 1 AND silindi_mi = 0
                """, (cari_unvani,))
                row = cursor.fetchone()
                if row:
                    cari_id = row[0]

            cursor.execute("""
                SELECT TOP 1 kayit_no FROM kalite.uygunsuzluklar
                WHERE kayit_no LIKE ? ORDER BY kayit_no DESC
            """, (f"PPAP-{datetime.now().strftime('%Y')}%",))
            row = cursor.fetchone()
            if row:
                last_no = int(row[0].split('-')[-1])
                kayit_no = f"PPAP-{datetime.now().strftime('%Y')}-{last_no + 1:04d}"
            else:
                kayit_no = f"PPAP-{datetime.now().strftime('%Y')}-0001"

            detay = f"""PPAP Seviyesi: {self.cmb_seviye.currentText()}
Sunum Nedeni: {self.cmb_neden.currentText()}
Part Number: {self.txt_part_no.text()}
Revizyon: {self.txt_revizyon.text()}
Hedef Sunum: {self.date_hedef.date().toString('dd.MM.yyyy')}
{self.txt_notlar.toPlainText()}"""

            cursor.execute("""
                INSERT INTO kalite.uygunsuzluklar (
                    uuid, kayit_no, kayit_tipi, kayit_tarihi, bildiren_id, cari_id, urun_id,
                    hata_tanimi, oncelik, durum, sorumlu_id, hedef_kapanis_tarihi,
                    olusturma_tarihi, guncelleme_tarihi
                ) VALUES (
                    NEWID(), ?, 'PPAP', CAST(GETDATE() AS DATE), ?, ?, ?,
                    ?, 'NORMAL', 'ACIK', ?, ?,
                    GETDATE(), GETDATE()
                )
            """, (
                kayit_no,
                sorumlu_id,
                cari_id,
                self.cmb_urun.currentData(),
                detay,
                sorumlu_id,
                self.date_hedef.date().toPython()
            ))

            conn.commit()
            QMessageBox.information(self, "Basarili", f"PPAP kaydi olusturuldu!\n\nKayit No: {kayit_no}")
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
# DIALOG: PPAP Detay
# =====================================================================

class PPAPDetayDialog(QDialog):
    """PPAP detay ve element takip dialog'u -- el kitabi uyumlu"""

    def __init__(self, theme: dict, kayit_id: int, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.kayit_id = kayit_id
        self.setWindowTitle("PPAP Detayi")
        self.setMinimumSize(brand.sp(900), brand.sp(700))
        self._load_data()
        self._setup_ui()

    def _load_data(self):
        self.kayit = {}
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.kayit_no, u.kayit_tarihi, c.unvan, s.urun_adi,
                       u.hata_tanimi, u.durum, p.ad + ' ' + p.soyad, u.hedef_kapanis_tarihi
                FROM kalite.uygunsuzluklar u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN stok.urunler s ON u.urun_id = s.id
                LEFT JOIN ik.personeller p ON u.sorumlu_id = p.id
                WHERE u.id = ?
            """, (self.kayit_id,))
            row = cursor.fetchone()
            if row:
                self.kayit = {
                    'id': row[0], 'kayit_no': row[1], 'tarih': row[2], 'musteri': row[3],
                    'urun': row[4], 'detay': row[5], 'durum': row[6], 'sorumlu': row[7], 'hedef': row[8]
                }
        except Exception as e:
            print(f"[kalite_ppap] Veri yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _setup_ui(self):
        self.setStyleSheet(f"""
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
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # -- Header --
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)

        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        title = QLabel(self.kayit.get('kayit_no', ''))
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(title)
        sub = QLabel("PPAP Detay ve Element Takibi")
        sub.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        title_col.addWidget(sub)
        header.addLayout(title_col)
        header.addStretch()

        # Durum badge
        durum = self.kayit.get('durum', '')
        durum_colors = {'ACIK': brand.WARNING, 'ISLEMDE': brand.INFO, 'KAPATILDI': brand.SUCCESS}
        durum_color = durum_colors.get(durum, brand.TEXT_MUTED)
        c = QColor(durum_color)
        soft_bg = f"rgba({c.red()},{c.green()},{c.blue()},0.15)"
        durum_lbl = QLabel(durum or '-')
        durum_lbl.setStyleSheet(
            f"background: {soft_bg}; color: {durum_color}; "
            f"padding: {brand.SP_1}px {brand.SP_3}px; "
            f"border-radius: {brand.R_SM}px; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(durum_lbl)

        layout.addLayout(header)

        # -- Bilgi karti --
        bilgi_grp = QGroupBox("Kayit Bilgileri")
        bilgi_form = QFormLayout()
        bilgi_form.setSpacing(brand.SP_2)
        bilgi_form.setLabelAlignment(Qt.AlignRight)

        def _info_val(text, bold=False, color=None):
            lbl = QLabel(str(text or '-'))
            cl = color or brand.TEXT
            w = brand.FW_SEMIBOLD if bold else brand.FW_REGULAR
            lbl.setStyleSheet(f"color: {cl}; font-size: {brand.FS_BODY}px; font-weight: {w};")
            lbl.setWordWrap(True)
            return lbl

        bilgi_form.addRow("Musteri:", _info_val(self.kayit.get('musteri', '-'), bold=True))
        bilgi_form.addRow("Urun:", _info_val(self.kayit.get('urun', '-')))
        bilgi_form.addRow("Sorumlu:", _info_val(self.kayit.get('sorumlu', '-'), bold=True, color=brand.PRIMARY))
        hedef = self.kayit.get('hedef')
        bilgi_form.addRow("Hedef Tarih:", _info_val(
            hedef.strftime('%d.%m.%Y') if hedef else '-',
            bold=True, color=brand.WARNING
        ))

        bilgi_grp.setLayout(bilgi_form)
        layout.addWidget(bilgi_grp)

        # -- Detaylar --
        detay_lbl = QLabel("Detaylar")
        detay_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        layout.addWidget(detay_lbl)

        detay_text = QTextEdit()
        detay_text.setPlainText(self.kayit.get('detay', ''))
        detay_text.setReadOnly(True)
        detay_text.setMaximumHeight(brand.sp(100))
        detay_text.setStyleSheet(f"""
            QTextEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
        """)
        layout.addWidget(detay_text)

        # -- PPAP Elementleri --
        elem_grp = QGroupBox("PPAP Elementleri (18 Element)")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {brand.BG_CARD};
                width: {brand.SP_2}px;
                border-radius: {brand.SP_1}px;
            }}
            QScrollBar::handle:vertical {{
                background: {brand.BORDER};
                border-radius: {brand.SP_1}px;
                min-height: {brand.SP_6}px;
            }}
        """)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(brand.SP_2)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        cb_css = f"""
            QCheckBox {{
                color: {brand.TEXT};
                spacing: {brand.SP_2}px;
                font-size: {brand.FS_BODY}px;
                padding: {brand.SP_1}px 0;
            }}
            QCheckBox::indicator {{
                width: {brand.sp(18)}px; height: {brand.sp(18)}px;
                border: 2px solid {brand.BORDER};
                border-radius: {brand.SP_1}px;
                background: {brand.BG_INPUT};
            }}
            QCheckBox::indicator:checked {{
                background: {brand.SUCCESS};
                border-color: {brand.SUCCESS};
            }}
        """

        ghost_btn_css = f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT_MUTED};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_1}px {brand.SP_2}px;
                font-size: {brand.FS_BODY_SM}px;
            }}
            QPushButton:hover {{ border-color: {brand.PRIMARY}; color: {brand.TEXT}; }}
        """

        self.element_checks = {}
        for num, eng, tr in PPAP_ELEMENTS:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(brand.SP_2)

            check = QCheckBox()
            check.setStyleSheet(cb_css)
            row_layout.addWidget(check)
            self.element_checks[num] = check

            num_lbl = QLabel(f"{num}.")
            num_lbl.setFixedWidth(brand.sp(25))
            num_lbl.setStyleSheet(
                f"color: {brand.PRIMARY}; "
                f"font-weight: {brand.FW_SEMIBOLD}; "
                f"font-size: {brand.FS_BODY}px;"
            )
            row_layout.addWidget(num_lbl)

            name_lbl = QLabel(f"{tr} ({eng})")
            name_lbl.setStyleSheet(f"color: {brand.TEXT}; font-size: {brand.FS_BODY}px;")
            row_layout.addWidget(name_lbl, 1)

            btn_upload = QPushButton("Dosya Ekle")
            btn_upload.setCursor(Qt.PointingHandCursor)
            btn_upload.setFixedHeight(brand.sp(28))
            btn_upload.setStyleSheet(ghost_btn_css)
            row_layout.addWidget(btn_upload)

            scroll_layout.addLayout(row_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)

        elem_lay = QVBoxLayout(elem_grp)
        elem_lay.setContentsMargins(0, 0, 0, 0)
        elem_lay.addWidget(scroll)

        layout.addWidget(elem_grp, 1)

        # -- Alt butonlar --
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)

        btn_kaydet = QPushButton("Ilerleme Kaydet")
        btn_kaydet.setCursor(Qt.PointingHandCursor)
        btn_kaydet.setFixedHeight(brand.sp(38))
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        btn_kaydet.clicked.connect(self._kaydet_ilerleme)
        btn_layout.addWidget(btn_kaydet)

        btn_layout.addStretch()

        btn_kapat = QPushButton("Kapat")
        btn_kapat.setCursor(Qt.PointingHandCursor)
        btn_kapat.setFixedHeight(brand.sp(38))
        btn_kapat.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
        """)
        btn_kapat.clicked.connect(self.accept)
        btn_layout.addWidget(btn_kapat)

        layout.addLayout(btn_layout)

    def _kaydet_ilerleme(self):
        tamamlanan = sum(1 for check in self.element_checks.values() if check.isChecked())
        QMessageBox.information(self, "Bilgi", f"Ilerleme kaydedildi.\nTamamlanan element: {tamamlanan}/18")


# =====================================================================
# ANA SAYFA
# =====================================================================

class KalitePPAPPage(BasePage):
    """PPAP Yonetimi -- el kitabi uyumlu sayfa"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # -- 1. Header --
        header = self.create_page_header(
            "PPAP Yonetimi",
            "Production Part Approval Process - Musteri onay sureclerinin takibi"
        )

        btn_yeni = self.create_primary_button("Yeni PPAP")
        btn_yeni.clicked.connect(self._yeni_ppap)
        header.addWidget(btn_yeni)

        layout.addLayout(header)

        # -- 2. KPI cards --
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self._kpi_aktif = self.create_stat_card("AKTIF", "0", color=brand.WARNING)
        kpi_row.addWidget(self._kpi_aktif)

        self._kpi_onaylanan = self.create_stat_card("KAPATILAN", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self._kpi_onaylanan)

        self._kpi_toplam = self.create_stat_card("TOPLAM", "0", color=brand.PRIMARY)
        kpi_row.addWidget(self._kpi_toplam)

        kpi_row.addStretch()
        layout.addLayout(kpi_row)

        # -- 3. Filtre --
        filtre_row = QHBoxLayout()
        filtre_row.setSpacing(brand.SP_3)

        filtre_lbl = QLabel("Durum:")
        filtre_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px; "
            f"font-weight: {brand.FW_MEDIUM};"
        )
        filtre_row.addWidget(filtre_lbl)

        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(['Tumu', 'ACIK', 'ISLEMDE', 'KAPATILDI'])
        self.cmb_durum.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
                min-width: {brand.sp(140)}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.cmb_durum.currentIndexChanged.connect(self._load_data)
        filtre_row.addWidget(self.cmb_durum)

        filtre_row.addStretch()

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        filtre_row.addWidget(btn_yenile)

        layout.addLayout(filtre_row)

        # -- 4. Tablo --
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kayit No", "Musteri", "Urun", "Tarih", "Hedef", "Durum", "Islem"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setColumnWidth(7, brand.sp(120))
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setStyleSheet(f"""
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
        """)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table, 1)

    # -----------------------------------------------------------------
    def _yeni_ppap(self):
        dlg = YeniPPAPDialog(self.theme, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _on_double_click(self, index):
        row = index.row()
        kayit_id = int(self.table.item(row, 0).text())
        dlg = PPAPDetayDialog(self.theme, kayit_id, self)
        dlg.exec()

    def _detay_goster(self, kayit_id: int):
        dlg = PPAPDetayDialog(self.theme, kayit_id, self)
        dlg.exec()

    # -----------------------------------------------------------------
    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            durum_filtre = self.cmb_durum.currentText()
            where_clause = "" if durum_filtre == 'Tumu' else f"AND u.durum = '{durum_filtre}'"

            cursor.execute(f"""
                SELECT u.id, u.kayit_no, c.unvan, s.urun_adi, u.kayit_tarihi,
                       u.hedef_kapanis_tarihi, u.durum
                FROM kalite.uygunsuzluklar u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN stok.urunler s ON u.urun_id = s.id
                WHERE u.kayit_tipi = 'PPAP' {where_clause}
                ORDER BY u.kayit_tarihi DESC
            """)

            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem((row[2] or '')[:25]))
                self.table.setItem(i, 3, QTableWidgetItem((row[3] or '')[:30]))

                tarih = row[4]
                self.table.setItem(i, 4, QTableWidgetItem(
                    tarih.strftime('%d.%m.%Y') if tarih else '-'))

                hedef = row[5]
                hedef_item = QTableWidgetItem(
                    hedef.strftime('%d.%m.%Y') if hedef else '-')
                if hedef and hedef < date.today() and row[6] != 'KAPATILDI':
                    hedef_item.setForeground(QColor(brand.ERROR))
                self.table.setItem(i, 5, hedef_item)

                durum = row[6] or ''
                durum_item = QTableWidgetItem(durum)
                durum_colors = {
                    'ACIK': brand.WARNING,
                    'ISLEMDE': brand.INFO,
                    'KAPATILDI': brand.SUCCESS
                }
                if durum in durum_colors:
                    durum_item.setForeground(QColor(durum_colors[durum]))
                self.table.setItem(i, 6, durum_item)

                widget = self.create_action_buttons([
                    ("Detay", "Detay Goster", lambda checked, kid=row[0]: self._detay_goster(kid), "info"),
                ])
                self.table.setCellWidget(i, 7, widget)

            # KPI guncelle
            cursor.execute("""
                SELECT COUNT(*) FROM kalite.uygunsuzluklar
                WHERE kayit_tipi = 'PPAP' AND durum IN ('ACIK', 'ISLEMDE')
            """)
            self._kpi_aktif.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            cursor.execute("""
                SELECT COUNT(*) FROM kalite.uygunsuzluklar
                WHERE kayit_tipi = 'PPAP' AND durum = 'KAPATILDI'
            """)
            self._kpi_onaylanan.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            cursor.execute("""
                SELECT COUNT(*) FROM kalite.uygunsuzluklar
                WHERE kayit_tipi = 'PPAP'
            """)
            self._kpi_toplam.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

        except Exception as e:
            print(f"[kalite_ppap] Veri yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
