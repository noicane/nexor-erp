# -*- coding: utf-8 -*-
"""
NEXOR ERP - Proses Kalite / Ilk Urun Onay Formu (FR.75)
========================================================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QSpinBox, QTextEdit, QSplitter, QWidget, QGridLayout,
    QGroupBox, QFormLayout, QCheckBox, QDoubleSpinBox, QFileDialog,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QColor, QFont, QPixmap

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand


# =====================================================================
# DIALOG: Ilk Urun Onay
# =====================================================================

class IlkUrunOnayDialog(QDialog):
    """Ilk Urun Onay detay dialog'u — el kitabi uyumlu"""

    def __init__(self, theme: dict, is_emri_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.is_emri_data = is_emri_data
        self.test_sonuclari = []
        self.foto_paths = []
        self.setWindowTitle("Ilk Urun Onay Formu - FR.75")
        self.setMinimumSize(brand.sp(900), brand.sp(700))
        self._load_test_turleri()
        self._setup_ui()

    # -----------------------------------------------------------------
    def _load_test_turleri(self):
        self.test_turleri = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad, min_deger, max_deger, birim
                FROM tanim.kalite_testleri
                WHERE aktif_mi = 1
                ORDER BY sira_no, kod
            """)
            for row in cursor.fetchall():
                self.test_turleri.append({
                    'id': row[0], 'kod': row[1], 'ad': row[2],
                    'min': row[3], 'max': row[4], 'birim': row[5]
                })
        except Exception:
            self.test_turleri = [
                {'id': 1, 'kod': 'KAL', 'ad': 'Kalinlik Olcumu', 'min': 8, 'max': 25, 'birim': 'um'},
                {'id': 2, 'kod': 'YAP', 'ad': 'Yapisma Testi', 'min': None, 'max': None, 'birim': 'OK/NOK'},
                {'id': 3, 'kod': 'GOR', 'ad': 'Gorsel Kontrol', 'min': None, 'max': None, 'birim': 'OK/NOK'},
                {'id': 4, 'kod': 'TUZ', 'ad': 'Tuz Testi', 'min': 72, 'max': None, 'birim': 'saat'},
            ]
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # -----------------------------------------------------------------
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

        # ── Header ──
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)

        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        title = QLabel("Ilk Urun Onay Formu (FR.75)")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(title)
        sub = QLabel(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        sub.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        title_col.addWidget(sub)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)

        # ── Splitter: Sol bilgi / Sag test ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(brand.SP_1)

        # --- SOL PANEL ---
        sol = QWidget()
        sol_lay = QVBoxLayout(sol)
        sol_lay.setContentsMargins(0, 0, 0, 0)
        sol_lay.setSpacing(brand.SP_4)

        # Is Emri Bilgileri
        bilgi_grp = QGroupBox("Is Emri Bilgileri")
        bilgi_form = QFormLayout()
        bilgi_form.setSpacing(brand.SP_2)
        bilgi_form.setLabelAlignment(Qt.AlignRight)

        def _info_val(text, bold=False, color=None):
            lbl = QLabel(str(text))
            c = color or brand.TEXT
            w = brand.FW_SEMIBOLD if bold else brand.FW_REGULAR
            lbl.setStyleSheet(f"color: {c}; font-size: {brand.FS_BODY}px; font-weight: {w};")
            lbl.setWordWrap(True)
            return lbl

        bilgi_form.addRow("Musteri:", _info_val(self.is_emri_data.get('cari_unvani', '-'), bold=True))
        bilgi_form.addRow("Urun:", _info_val(
            f"{self.is_emri_data.get('stok_kodu', '')} - {self.is_emri_data.get('stok_adi', '')}"))
        bilgi_form.addRow("Is Emri:", _info_val(self.is_emri_data.get('is_emri_no', '-'), bold=True, color=brand.PRIMARY))
        bilgi_form.addRow("Lot No:", _info_val(self.is_emri_data.get('lot_no', '-'), bold=True, color=brand.WARNING))
        bilgi_form.addRow("Miktar:", _info_val(self.is_emri_data.get('toplam_miktar', 0)))
        bilgi_form.addRow("Hat:", _info_val(self.is_emri_data.get('hat_adi', '-')))
        bilgi_grp.setLayout(bilgi_form)
        sol_lay.addWidget(bilgi_grp)

        # Kontrol Bilgileri
        kontrol_grp = QGroupBox("Kontrol Bilgileri")
        kontrol_form = QFormLayout()
        kontrol_form.setSpacing(brand.SP_2)

        input_css = f"""
            QComboBox, QSpinBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus, QSpinBox:focus {{ border-color: {brand.PRIMARY}; }}
        """

        self.cmb_operator = QComboBox()
        self.cmb_operator.setStyleSheet(input_css)
        self._load_personel(self.cmb_operator)
        kontrol_form.addRow("Operator:", self.cmb_operator)

        self.cmb_kalite = QComboBox()
        self.cmb_kalite.setStyleSheet(input_css)
        self._load_personel(self.cmb_kalite)
        kontrol_form.addRow("Kalite Sor.:", self.cmb_kalite)

        self.txt_test_adedi = QSpinBox()
        self.txt_test_adedi.setRange(1, 100)
        self.txt_test_adedi.setValue(3)
        self.txt_test_adedi.setStyleSheet(input_css)
        kontrol_form.addRow("Test Adedi:", self.txt_test_adedi)

        kontrol_grp.setLayout(kontrol_form)
        sol_lay.addWidget(kontrol_grp)

        # Fotograflar
        foto_grp = QGroupBox("Fotograflar")
        foto_lay = QVBoxLayout()
        foto_lay.setSpacing(brand.SP_2)

        ghost_btn_css = f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT_MUTED};
                border: 1px dashed {brand.BORDER_HARD};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px;
                font-size: {brand.FS_BODY_SM}px;
            }}
            QPushButton:hover {{ border-color: {brand.PRIMARY}; color: {brand.TEXT}; }}
        """

        self.foto_btns = []
        for i in range(3):
            btn = QPushButton(f"+ Fotograf {i+1}")
            btn.setStyleSheet(ghost_btn_css)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i: self._foto_ekle(idx))
            foto_lay.addWidget(btn)
            self.foto_btns.append(btn)

        foto_grp.setLayout(foto_lay)
        sol_lay.addWidget(foto_grp)
        sol_lay.addStretch()
        splitter.addWidget(sol)

        # --- SAG PANEL ---
        sag = QWidget()
        sag_lay = QVBoxLayout(sag)
        sag_lay.setContentsMargins(0, 0, 0, 0)
        sag_lay.setSpacing(brand.SP_4)

        # Test Sonuclari
        test_grp = QGroupBox("Test Sonuclari")
        test_lay = QVBoxLayout()
        test_lay.setSpacing(brand.SP_3)

        self.test_table = QTableWidget()
        self.test_table.setColumnCount(6)
        self.test_table.setHorizontalHeaderLabels(["Test", "Kriter", "Min", "Max", "Olcum", "Sonuc"])
        self.test_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.test_table.setColumnWidth(1, brand.sp(70))
        self.test_table.setColumnWidth(2, brand.sp(55))
        self.test_table.setColumnWidth(3, brand.sp(55))
        self.test_table.setColumnWidth(4, brand.sp(120))
        self.test_table.setColumnWidth(5, brand.sp(120))
        self.test_table.verticalHeader().setVisible(False)
        self.test_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.test_table.setShowGrid(False)
        self.test_table.setAlternatingRowColors(True)
        self.test_table.setStyleSheet(f"""
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

        cell_input_css = f"""
            background: {brand.BG_INPUT};
            color: {brand.TEXT};
            border: 1px solid {brand.BORDER};
            border-radius: {brand.R_SM}px;
            padding: {brand.SP_1}px {brand.SP_2}px;
            font-size: {brand.FS_BODY}px;
        """

        self.test_table.setRowCount(len(self.test_turleri))
        self.test_inputs = []
        self.test_combos = []

        for i, test in enumerate(self.test_turleri):
            self.test_table.setRowHeight(i, brand.sp(42))

            self.test_table.setItem(i, 0, QTableWidgetItem(test['ad']))
            self.test_table.setItem(i, 1, QTableWidgetItem(test.get('birim', '')))
            self.test_table.setItem(i, 2, QTableWidgetItem(str(test.get('min', '-') or '-')))
            self.test_table.setItem(i, 3, QTableWidgetItem(str(test.get('max', '-') or '-')))

            if test.get('birim') == 'OK/NOK':
                inp = QComboBox()
                inp.addItems(['', 'OK', 'NOK'])
                inp.setStyleSheet(cell_input_css)
            else:
                inp = QLineEdit()
                inp.setStyleSheet(cell_input_css)
                inp.setPlaceholderText("Deger")
            inp.setMinimumWidth(brand.sp(90))
            self.test_table.setCellWidget(i, 4, inp)
            self.test_inputs.append(inp)

            sonuc = QComboBox()
            sonuc.addItems(['', 'UYGUN', 'UYGUN DEGIL'])
            sonuc.setStyleSheet(cell_input_css)
            sonuc.setMinimumWidth(brand.sp(90))
            self.test_table.setCellWidget(i, 5, sonuc)
            self.test_combos.append(sonuc)

        test_lay.addWidget(self.test_table)
        test_grp.setLayout(test_lay)
        sag_lay.addWidget(test_grp)

        # Gorsel Kontrol
        gorsel_grp = QGroupBox("Gorsel Kontrol")
        gorsel_lay = QVBoxLayout()
        gorsel_lay.setSpacing(brand.SP_1)

        self.gorsel_checks = {}
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
        for item in ['Renk Uygunlugu', 'Yuzey Kalitesi', 'Leke/Cizik',
                      'Deformasyon', 'Kaplama Homojenligi']:
            cb = QCheckBox(item)
            cb.setStyleSheet(cb_css)
            gorsel_lay.addWidget(cb)
            self.gorsel_checks[item] = cb

        gorsel_grp.setLayout(gorsel_lay)
        sag_lay.addWidget(gorsel_grp)

        # Aciklama
        aciklama_lbl = QLabel("Aciklama / Not")
        aciklama_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        sag_lay.addWidget(aciklama_lbl)

        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(brand.sp(80))
        self.txt_aciklama.setStyleSheet(f"""
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
        self.txt_aciklama.setPlaceholderText("Varsa aciklama yazin...")
        sag_lay.addWidget(self.txt_aciklama)

        splitter.addWidget(sag)
        splitter.setSizes([brand.sp(300), brand.sp(700)])
        layout.addWidget(splitter, 1)

        # ── Alt butonlar ──
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(brand.SP_3)
        btn_lay.addStretch()

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
        btn_lay.addWidget(btn_iptal)

        btn_red = QPushButton("Reddet")
        btn_red.setCursor(Qt.PointingHandCursor)
        btn_red.setFixedHeight(brand.sp(38))
        btn_red.setStyleSheet(f"""
            QPushButton {{
                background: {brand.ERROR};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #DC2626; }}
        """)
        btn_red.clicked.connect(lambda: self._kaydet('RED'))
        btn_lay.addWidget(btn_red)

        btn_onayla = QPushButton("Onayla")
        btn_onayla.setCursor(Qt.PointingHandCursor)
        btn_onayla.setFixedHeight(brand.sp(38))
        btn_onayla.setStyleSheet(f"""
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
        btn_onayla.clicked.connect(lambda: self._kaydet('ONAY'))
        btn_lay.addWidget(btn_onayla)

        layout.addLayout(btn_lay)

    # -----------------------------------------------------------------
    def _load_personel(self, combo: QComboBox):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ad + ' ' + soyad FROM ik.personeller
                WHERE aktif_mi = 1 ORDER BY ad, soyad
            """)
            combo.clear()
            combo.addItem("-- Secin --", None)
            for row in cursor.fetchall():
                combo.addItem(row[1], row[0])
        except Exception as e:
            print(f"[kalite_proses] Personel yuklenemedi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _foto_ekle(self, idx: int):
        path, _ = QFileDialog.getOpenFileName(
            self, "Fotograf Sec", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            if len(self.foto_paths) <= idx:
                self.foto_paths.extend([''] * (idx + 1 - len(self.foto_paths)))
            self.foto_paths[idx] = path
            self.foto_btns[idx].setText(f"Fotograf {idx+1} Secildi")
            self.foto_btns[idx].setStyleSheet(f"""
                QPushButton {{
                    background: {brand.SUCCESS_SOFT};
                    color: {brand.SUCCESS};
                    border: 1px solid {brand.SUCCESS};
                    border-radius: {brand.R_SM}px;
                    padding: {brand.SP_2}px;
                    font-size: {brand.FS_BODY_SM}px;
                    font-weight: {brand.FW_SEMIBOLD};
                }}
            """)

    # -----------------------------------------------------------------
    def _kaydet(self, karar: str):
        operator_id = self.cmb_operator.currentData()
        kalite_id = self.cmb_kalite.currentData()

        if not operator_id or not kalite_id:
            QMessageBox.warning(self, "Uyari", "Lutfen operator ve kalite sorumlusunu secin!")
            return

        test_sonuclari = []
        for i, test in enumerate(self.test_turleri):
            inp = self.test_inputs[i]
            deger = inp.currentText() if isinstance(inp, QComboBox) else inp.text()
            sonuc = self.test_combos[i].currentText()
            test_sonuclari.append({
                'test_id': test['id'], 'test_adi': test['ad'],
                'olcum': deger, 'sonuc': sonuc
            })

        gorsel_sonuc = {k: v.isChecked() for k, v in self.gorsel_checks.items()}

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO kalite.muayeneler
                (uuid, muayene_no, muayene_tipi, tarih, is_emri_id, urun_id, lot_no,
                 muayeneci_id, numune_miktari, sonuc, notlar, olusturma_tarihi, guncelleme_tarihi)
                OUTPUT INSERTED.id
                VALUES (NEWID(), ?, 'ILK_URUN', GETDATE(), ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (
                f"IU-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                self.is_emri_data.get('id'),
                self.is_emri_data.get('stok_id'),
                self.is_emri_data.get('lot_no'),
                kalite_id,
                self.txt_test_adedi.value(),
                'KABUL' if karar == 'ONAY' else 'RED',
                self.txt_aciklama.toPlainText()
            ))

            muayene_id = cursor.fetchone()[0]

            for ts in test_sonuclari:
                if ts['olcum']:
                    cursor.execute("""
                        INSERT INTO kalite.muayene_detaylar
                        (uuid, muayene_id, kontrol_ozelligi, olcum_degeri_metin, sonuc)
                        VALUES (NEWID(), ?, ?, ?, ?)
                    """, (muayene_id, ts['test_adi'], ts['olcum'], ts['sonuc'] or 'BEKLEMEDE'))

            new_durum = 'URETIMDE' if karar == 'ONAY' else 'ILK_URUN_RED'
            cursor.execute("""
                UPDATE siparis.is_emirleri
                SET durum = ?, guncelleme_tarihi = GETDATE()
                WHERE id = ?
            """, (new_durum, self.is_emri_data.get('id')))

            conn.commit()
            LogManager.log_update('kalite', 'siparis.is_emirleri', None, 'Durum guncellendi')

            try:
                pdf_path = self._create_pdf_report(karar, test_sonuclari, gorsel_sonuc, muayene_id)
                msg = f"Ilk urun {'ONAYLANDI' if karar == 'ONAY' else 'REDDEDILDI'}!\n\nPDF: {pdf_path}"
            except Exception as pdf_err:
                print(f"[kalite_proses] PDF olusturma hatasi: {pdf_err}")
                msg = f"Ilk urun {'ONAYLANDI' if karar == 'ONAY' else 'REDDEDILDI'}!\n\nPDF olusturulamadi: {pdf_err}"

            QMessageBox.information(self, "Basarili", msg)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # -----------------------------------------------------------------
    def _create_pdf_report(self, karar, test_sonuclari, gorsel_sonuc, muayene_id):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import re

        default_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'

        for fp in [r'C:\Windows\Fonts\DejaVuSans.ttf', r'C:\Windows\Fonts\arial.ttf',
                    r'C:\Windows\Fonts\calibri.ttf', r'C:\Windows\Fonts\tahoma.ttf']:
            try:
                if os.path.exists(fp):
                    pdfmetrics.registerFont(TTFont('TurkceFont', fp))
                    default_font = 'TurkceFont'
                    break
            except Exception:
                continue

        for fp in [r'C:\Windows\Fonts\DejaVuSans-Bold.ttf', r'C:\Windows\Fonts\arialbd.ttf',
                    r'C:\Windows\Fonts\calibrib.ttf', r'C:\Windows\Fonts\tahomabd.ttf']:
            try:
                if os.path.exists(fp):
                    pdfmetrics.registerFont(TTFont('TurkceFontBold', fp))
                    bold_font = 'TurkceFontBold'
                    break
            except Exception:
                continue

        cari_safe = re.sub(r'[<>:"/\\|?*]', '_', self.is_emri_data.get('cari_unvani', 'GENEL'))
        stok_kodu = self.is_emri_data.get('stok_kodu', 'UNKNOWN')
        lot_no = self.is_emri_data.get('lot_no', 'LOT')

        from config import NAS_PATHS
        nas_base = NAS_PATHS["product_path"]
        klasor = os.path.join(nas_base, cari_safe, stok_kodu, "06_Ilk_Urun_Onaylari")
        try:
            if not os.path.exists(klasor):
                os.makedirs(klasor)
        except Exception:
            klasor = os.path.expanduser("~/Desktop")

        pdf_path = os.path.join(klasor, f"FR75_{lot_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('T', parent=styles['Heading1'], fontSize=16,
                                     textColor=colors.HexColor('#1e40af'), spaceAfter=20,
                                     alignment=TA_CENTER, fontName=bold_font)
        story.append(Paragraph("ILK URUN ONAY FORMU (FR.75)", title_style))
        story.append(Spacer(1, 0.5 * cm))

        bilgi_data = [
            ['Musteri:', self.is_emri_data.get('cari_unvani', '-')],
            ['Urun:', f"{stok_kodu} - {self.is_emri_data.get('stok_adi', '')}"],
            ['Is Emri No:', self.is_emri_data.get('is_emri_no', '-')],
            ['Lot No:', lot_no],
            ['Miktar:', str(self.is_emri_data.get('toplam_miktar', 0))],
            ['Hat:', self.is_emri_data.get('hat_adi', '-')],
            ['Tarih:', datetime.now().strftime('%d.%m.%Y %H:%M')],
            ['Karar:', 'ONAYLANDI' if karar == 'ONAY' else 'REDDEDILDI']
        ]
        t = Table(bilgi_data, colWidths=[5 * cm, 12 * cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), bold_font),
            ('FONTNAME', (1, 0), (1, -1), default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph("<b>Test Sonuclari:</b>", ParagraphStyle(
            'TH', parent=styles['Heading2'], fontName=bold_font)))

        td = [['Test', 'Kriter', 'Min', 'Max', 'Olcum', 'Sonuc']]
        for i, test in enumerate(self.test_turleri):
            inp = self.test_inputs[i]
            olcum = inp.currentText() if isinstance(inp, QComboBox) else inp.text()
            sonuc = self.test_combos[i].currentText()
            td.append([test['ad'], test.get('birim', ''),
                        str(test.get('min', '-') or '-'), str(test.get('max', '-') or '-'),
                        olcum or '-', sonuc or '-'])
        tt = Table(td, colWidths=[4 * cm, 2 * cm, 2 * cm, 2 * cm, 3 * cm, 3 * cm])
        tt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('FONTNAME', (0, 1), (-1, -1), default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(tt)
        story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph("<b>Gorsel Kontrol:</b>", ParagraphStyle(
            'GH', parent=styles['Heading2'], fontName=bold_font)))
        gd = [['Kontrol', 'Durum']]
        for k, v in gorsel_sonuc.items():
            gd.append([k, 'UYGUN' if v else '-'])
        gt = Table(gd, colWidths=[10 * cm, 5 * cm])
        gt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('FONTNAME', (0, 1), (-1, -1), default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(gt)

        doc.build(story)
        return pdf_path


# =====================================================================
# ANA SAYFA
# =====================================================================

class KaliteProsesPage(BasePage):
    """Proses Kalite / Ilk Urun Onay — el kitabi uyumlu sayfa"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
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
            "Proses Kalite - Ilk Urun Onay",
            "Hat basindaki lotlar icin kalite kontrol"
        )
        # Saat label + Yenile buton (saga)
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

        # ── 3. Tablo ──
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Is Emri No", "Musteri", "Urun", "Lot No", "Miktar", "Hat", "Islem"
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
        layout.addWidget(self.table, 1)

    # -----------------------------------------------------------------
    def _tick(self):
        self._saat_lbl.setText(QTime.currentTime().toString("HH:mm:ss"))

    # -----------------------------------------------------------------
    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    ie.id, ie.is_emri_no, ie.cari_unvani, ie.stok_adi,
                    sb.lot_no, sb.miktar, d.ad, ie.stok_kodu, ie.urun_id,
                    sb.giris_tarihi
                FROM stok.stok_bakiye sb
                INNER JOIN tanim.depolar d ON sb.depo_id = d.id
                INNER JOIN siparis.is_emirleri ie ON sb.lot_no = ie.lot_no
                WHERE d.kod LIKE 'HB-%%'
                  AND sb.miktar > 0
                  AND sb.durum_kodu = 'URETIMDE'
                  AND NOT EXISTS (
                      SELECT 1 FROM kalite.proses_kontrol pc
                      WHERE pc.lot_no = sb.lot_no
                  )
                ORDER BY sb.giris_tarihi DESC
            """)
            rows = cursor.fetchall()

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                data = {
                    'id': row[0], 'is_emri_no': row[1], 'cari_unvani': row[2],
                    'stok_adi': row[3], 'lot_no': row[4], 'toplam_miktar': row[5],
                    'hat_adi': row[6], 'stok_kodu': row[7], 'stok_id': row[8]
                }

                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem((row[2] or '')[:25]))
                self.table.setItem(i, 3, QTableWidgetItem((row[3] or '')[:30]))
                self.table.setItem(i, 4, QTableWidgetItem(row[4] or ''))

                miktar_item = QTableWidgetItem(str(row[5] or 0))
                miktar_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 5, miktar_item)

                self.table.setItem(i, 6, QTableWidgetItem(row[6] or '-'))

                widget = self.create_action_buttons([
                    ("Kontrol", "Kontrol Et", lambda _, d=data: self._kontrol_et(d), "view"),
                ])
                self.table.setCellWidget(i, 7, widget)

            # KPI guncelle
            self._kpi_bekleyen.findChild(QLabel, "stat_value").setText(str(len(rows)))

            cursor.execute("""
                SELECT COUNT(*) FROM kalite.proses_kontrol
                WHERE CAST(kontrol_tarihi AS DATE) = CAST(GETDATE() AS DATE)
                  AND durum = 'TAMAMLANDI'
            """)
            self._kpi_onay.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            cursor.execute("""
                SELECT COUNT(*) FROM kalite.proses_kontrol
                WHERE CAST(kontrol_tarihi AS DATE) = CAST(GETDATE() AS DATE)
                  AND durum = 'RED'
            """)
            self._kpi_red.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

        except Exception as e:
            print(f"[kalite_proses] Veri yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # -----------------------------------------------------------------
    def _kontrol_et(self, data: dict):
        dlg = IlkUrunOnayDialog(self.theme, data, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
