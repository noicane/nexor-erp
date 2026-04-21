# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kalite Giris Kontrol Sayfasi
=========================================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QWidget, QDoubleSpinBox, QGroupBox, QGridLayout,
    QCheckBox, QScrollArea, QFormLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage, create_action_buttons
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand


# =====================================================================
# DIALOG: Kriter Kontrol
# =====================================================================

class KriterKontrolDialog(QDialog):
    """Kriterlere gore kalite kontrol dialogu — el kitabi uyumlu"""

    def __init__(self, theme: dict, lot_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.lot_data = lot_data
        self.kriterler = []
        self.kriter_widgets = {}
        self.setWindowTitle(f"Kalite Kontrol - {lot_data.get('lot_no', '')}")
        self.setMinimumSize(brand.sp(750), brand.sp(620))
        self._load_kriterler()
        self._setup_ui()

    def _load_kriterler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ad, kategori, kontrol_tipi, birim,
                       min_deger, max_deger, secenekler, zorunlu_mu, kritik_mi
                FROM kalite.giris_kontrol_kriterleri
                WHERE aktif_mi = 1
                ORDER BY sira_no
            """)
            for row in cursor.fetchall():
                self.kriterler.append({
                    'id': row[0], 'ad': row[1], 'kategori': row[2],
                    'kontrol_tipi': row[3], 'birim': row[4],
                    'min_deger': row[5], 'max_deger': row[6],
                    'secenekler': row[7], 'zorunlu_mu': row[8],
                    'kritik_mi': row[9]
                })
        except Exception as e:
            print(f"[kalite_giris] Kriter yukleme hatasi: {e}")
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
        title = QLabel("Kalite Giris Kontrol")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(title)
        sub = QLabel(f"Lot: {self.lot_data.get('lot_no', '')} | Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        sub.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        title_col.addWidget(sub)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)

        # -- Lot Bilgi Karti --
        bilgi_grp = QGroupBox("Lot Bilgileri")
        bilgi_form = QFormLayout()
        bilgi_form.setSpacing(brand.SP_2)
        bilgi_form.setLabelAlignment(Qt.AlignRight)

        def _info_val(text, bold=False, color=None):
            lbl = QLabel(str(text))
            c = color or brand.TEXT
            w = brand.FW_SEMIBOLD if bold else brand.FW_MEDIUM
            lbl.setStyleSheet(f"color: {c}; font-size: {brand.FS_BODY}px; font-weight: {w};")
            lbl.setWordWrap(True)
            return lbl

        bilgi_form.addRow("Lot No:", _info_val(self.lot_data.get('lot_no', '-'), bold=True, color=brand.WARNING))
        bilgi_form.addRow("Musteri:", _info_val(self.lot_data.get('cari_unvani', '-'), bold=True))
        bilgi_form.addRow("Miktar:", _info_val(f"{self.lot_data.get('miktar', 0):,.0f}"))
        bilgi_grp.setLayout(bilgi_form)
        layout.addWidget(bilgi_grp)

        # -- Kriter Scroll --
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
        """)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(brand.SP_3)

        input_css = f"""
            QComboBox, QDoubleSpinBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus, QDoubleSpinBox:focus {{ border-color: {brand.PRIMARY}; }}
        """

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

        if not self.kriterler:
            empty_lbl = QLabel("Tanimli kriter bulunamadi")
            empty_lbl.setStyleSheet(
                f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px; "
                f"padding: {brand.SP_4}px;"
            )
            scroll_layout.addWidget(empty_lbl)
        else:
            for kriter in self.kriterler:
                frame = QFrame()
                frame.setStyleSheet(f"""
                    QFrame {{
                        background: {brand.BG_CARD};
                        border: 1px solid {brand.BORDER};
                        border-radius: {brand.R_SM}px;
                        padding: {brand.SP_2}px;
                    }}
                """)
                h = QHBoxLayout(frame)
                h.setContentsMargins(brand.SP_3, brand.SP_2, brand.SP_3, brand.SP_2)
                h.setSpacing(brand.SP_3)

                kriter_label = f"{'[Z] ' if kriter['zorunlu_mu'] else ''}{kriter['ad']}"
                lbl = QLabel(kriter_label)
                lbl.setStyleSheet(
                    f"color: {brand.TEXT}; font-size: {brand.FS_BODY}px; "
                    f"font-weight: {brand.FW_MEDIUM}; border: none;"
                )
                h.addWidget(lbl, 1)

                if kriter['kontrol_tipi'] == 'CHECKBOX':
                    cb = QCheckBox("Uygun")
                    cb.setStyleSheet(cb_css)
                    self.kriter_widgets[kriter['id']] = ('CHECKBOX', cb)
                    h.addWidget(cb)
                elif kriter['kontrol_tipi'] == 'OLCUM':
                    spin = QDoubleSpinBox()
                    spin.setRange(-999999, 999999)
                    spin.setStyleSheet(input_css)
                    spin.setFixedWidth(brand.sp(120))
                    self.kriter_widgets[kriter['id']] = ('OLCUM', spin, kriter['min_deger'], kriter['max_deger'])
                    h.addWidget(spin)
                    if kriter['birim']:
                        birim_lbl = QLabel(kriter['birim'])
                        birim_lbl.setStyleSheet(
                            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; border: none;"
                        )
                        h.addWidget(birim_lbl)
                elif kriter['kontrol_tipi'] == 'SECIM':
                    combo = QComboBox()
                    combo.addItem("-- Secin --", "")
                    for s in (kriter['secenekler'] or '').split('|'):
                        if s.strip():
                            combo.addItem(s.strip(), s.strip())
                    combo.setStyleSheet(input_css)
                    combo.setFixedWidth(brand.sp(160))
                    self.kriter_widgets[kriter['id']] = ('SECIM', combo)
                    h.addWidget(combo)

                scroll_layout.addWidget(frame)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # -- Not --
        not_lbl = QLabel("Aciklama / Not")
        not_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        layout.addWidget(not_lbl)

        self.not_input = QLineEdit()
        self.not_input.setPlaceholderText("Varsa aciklama yazin...")
        self.not_input.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        layout.addWidget(self.not_input)

        # -- Alt butonlar --
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
        btn_red.clicked.connect(lambda: self._save('RED'))
        btn_lay.addWidget(btn_red)

        btn_kosullu = QPushButton("Kosullu Onay")
        btn_kosullu.setCursor(Qt.PointingHandCursor)
        btn_kosullu.setFixedHeight(brand.sp(38))
        btn_kosullu.setStyleSheet(f"""
            QPushButton {{
                background: {brand.INFO};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #2563EB; }}
        """)
        btn_kosullu.clicked.connect(lambda: self._save('KOSULLU'))
        btn_lay.addWidget(btn_kosullu)

        btn_onayla = QPushButton("Onayla")
        btn_onayla.setCursor(Qt.PointingHandCursor)
        btn_onayla.setFixedHeight(brand.sp(38))
        btn_onayla.setDefault(True)
        btn_onayla.setAutoDefault(True)
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
        btn_onayla.clicked.connect(lambda: self._save('ONAYLANDI'))
        btn_lay.addWidget(btn_onayla)

        layout.addLayout(btn_lay)

    def _save(self, durum):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            lot_no = self.lot_data.get('lot_no')

            # Durum belirleme
            if durum == 'ONAYLANDI':
                kalite_durumu = 'ONAYLANDI'
                durum_kodu = 'GIRIS_ONAY'
            elif durum == 'RED':
                kalite_durumu = 'RED'
                durum_kodu = 'RED'
            else:  # KOSULLU
                kalite_durumu = 'KOSULLU'
                durum_kodu = 'GIRIS_KALITE'

            # Mevcut depo_id'yi bul
            cursor.execute("""
                SELECT depo_id FROM stok.stok_bakiye
                WHERE lot_no = ?
                  AND durum_kodu IN ('KABUL', 'GIRIS_KALITE')
                  AND miktar > 0
            """, (lot_no,))
            depo_result = cursor.fetchone()

            if not depo_result:
                QMessageBox.warning(self, "Uyari", f"Lot bulunamadi veya islem yapilmis: {lot_no}")
                return

            depo_id = depo_result[0]

            # Durum guncelleme
            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET kalite_durumu = ?,
                    durum_kodu = ?,
                    son_hareket_tarihi = GETDATE()
                WHERE lot_no = ? AND depo_id = ?
            """, (kalite_durumu, durum_kodu, lot_no, depo_id))

            if cursor.rowcount == 0:
                QMessageBox.warning(self, "Uyari", f"Lot guncellenemedi: {lot_no}")
                return

            if durum == 'RED':
                print(f"[kalite_giris] LOT {lot_no} RED durumuna alindi.")

            conn.commit()
            LogManager.log_update('kalite', 'stok.stok_bakiye', None, 'Durum guncellendi')

            durum_text = {
                'ONAYLANDI': 'onaylandi',
                'RED': 'reddedildi',
                'KOSULLU': 'kosullu onaylandi'
            }
            QMessageBox.information(
                self, "Basarili",
                f"Kalite kontrol {durum_text.get(durum, durum)}!\n\n"
                f"Lot: {lot_no}\n"
                f"Yeni Durum: {durum_kodu}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# =====================================================================
# DIALOG: Palet Detay
# =====================================================================

class PaletDetayDialog(QDialog):
    """Palet detay dialogu — el kitabi uyumlu"""

    def __init__(self, theme: dict, palet_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.palet_data = palet_data
        self.setWindowTitle(f"Palet - {palet_data.get('lot_no', '')}")
        self.setMinimumSize(brand.sp(520), brand.sp(420))
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

        # -- Header --
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)

        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        title = QLabel("Palet Detay")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(title)
        sub = QLabel(f"Lot: {self.palet_data.get('lot_no', '')}")
        sub.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        title_col.addWidget(sub)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)

        # -- Bilgi Grp --
        bilgi_grp = QGroupBox("Palet Bilgileri")
        bilgi_form = QFormLayout()
        bilgi_form.setSpacing(brand.SP_2)
        bilgi_form.setLabelAlignment(Qt.AlignRight)

        def _info_val(text, bold=False, color=None):
            lbl = QLabel(str(text))
            c = color or brand.TEXT
            w = brand.FW_SEMIBOLD if bold else brand.FW_MEDIUM
            lbl.setStyleSheet(f"color: {c}; font-size: {brand.FS_BODY}px; font-weight: {w};")
            lbl.setWordWrap(True)
            return lbl

        bilgi_form.addRow("Lot No:", _info_val(self.palet_data.get('lot_no', '-'), bold=True, color=brand.PRIMARY))
        bilgi_form.addRow("Stok Kodu:", _info_val(self.palet_data.get('stok_kodu', '-')))
        bilgi_form.addRow("Musteri:", _info_val(self.palet_data.get('cari_unvani', '-'), bold=True))
        bilgi_form.addRow("Miktar:", _info_val(f"{self.palet_data.get('miktar', 0):,.0f}", color=brand.SUCCESS))

        durum = self.palet_data.get('kalite_durumu', 'BEKLIYOR')
        durum_colors = {'BEKLIYOR': brand.WARNING, 'ONAYLANDI': brand.SUCCESS, 'RED': brand.ERROR, 'KOSULLU': brand.INFO}
        bilgi_form.addRow("Durum:", _info_val(durum, bold=True, color=durum_colors.get(durum, brand.TEXT_MUTED)))

        bilgi_grp.setLayout(bilgi_form)
        layout.addWidget(bilgi_grp)

        layout.addStretch()

        # -- Butonlar --
        if durum == 'BEKLIYOR':
            btn_kriter = QPushButton("Kriter Kontrol")
            btn_kriter.setCursor(Qt.PointingHandCursor)
            btn_kriter.setFixedHeight(brand.sp(38))
            btn_kriter.setStyleSheet(f"""
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
            btn_kriter.clicked.connect(self._kriter_kontrol)
            layout.addWidget(btn_kriter)

            quick_lay = QHBoxLayout()
            quick_lay.setSpacing(brand.SP_3)

            btn_onayla = QPushButton("Hizli Onayla")
            btn_onayla.setCursor(Qt.PointingHandCursor)
            btn_onayla.setFixedHeight(brand.sp(38))
            btn_onayla.setDefault(True)
            btn_onayla.setAutoDefault(True)
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
            btn_onayla.clicked.connect(lambda: self._quick_update('ONAYLANDI'))
            quick_lay.addWidget(btn_onayla)

            btn_red = QPushButton("Hizli Red")
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
            btn_red.clicked.connect(lambda: self._quick_update('RED'))
            quick_lay.addWidget(btn_red)

            layout.addLayout(quick_lay)

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
        btn_kapat.clicked.connect(self.close)
        layout.addWidget(btn_kapat)

    def _kriter_kontrol(self):
        dlg = KriterKontrolDialog(self.theme, self.palet_data, self)
        if dlg.exec():
            self.accept()

    def _quick_update(self, durum):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            lot_no = self.palet_data.get('lot_no')

            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET kalite_durumu = ?, son_hareket_tarihi = GETDATE()
                WHERE lot_no = ?
            """, (durum, lot_no))

            if cursor.rowcount == 0:
                QMessageBox.warning(self, "Uyari", f"Lot bulunamadi: {lot_no}")
                return

            conn.commit()
            LogManager.log_update('kalite', 'stok.stok_bakiye', None, 'Durum guncellendi')

            durum_text = {'ONAYLANDI': 'onaylandi', 'RED': 'reddedildi'}
            QMessageBox.information(self, "Basarili", f"Palet {durum_text.get(durum, 'guncellendi')}!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# =====================================================================
# DIALOG: Ana Lot Detay
# =====================================================================

class AnaLotDetayDialog(QDialog):
    """Ana lot detay dialogu — el kitabi uyumlu"""

    def __init__(self, theme: dict, parent_lot_no: str, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.parent_lot_no = parent_lot_no
        self.paletler = []
        self.setWindowTitle(f"Ana Lot - {parent_lot_no}")
        self.setMinimumSize(brand.sp(920), brand.sp(620))
        self._load_data()
        self._setup_ui()

    def _load_data(self):
        self.paletler = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sb.lot_no, sb.palet_no, sb.toplam_palet,
                       u.urun_kodu, u.urun_adi,
                       sb.miktar, sb.kalite_durumu
                FROM stok.stok_bakiye sb
                LEFT JOIN stok.urunler u ON sb.urun_id = u.id
                WHERE sb.parent_lot_no = ?
                ORDER BY sb.palet_no
            """, (self.parent_lot_no,))
            for row in cursor.fetchall():
                self.paletler.append({
                    'lot_no': row[0], 'palet_no': row[1],
                    'toplam_palet': row[2], 'stok_kodu': row[3],
                    'stok_adi': row[4], 'miktar': row[5],
                    'kalite_durumu': row[6]
                })
        except Exception as e:
            print(f"[kalite_giris] Veri yukleme hatasi: {e}")
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
        title = QLabel(f"Ana Lot Detay")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(title)
        sub = QLabel(self.parent_lot_no)
        sub.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        title_col.addWidget(sub)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)

        # -- Istatistik --
        bekleyen = sum(1 for p in self.paletler if p['kalite_durumu'] == 'BEKLIYOR')
        onaylanan = sum(1 for p in self.paletler if p['kalite_durumu'] == 'ONAYLANDI')
        stat_lbl = QLabel(
            f"Toplam: {len(self.paletler)} palet  |  "
            f"Bekleyen: {bekleyen}  |  Onaylanan: {onaylanan}"
        )
        stat_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px; "
            f"padding: {brand.SP_2}px 0;"
        )
        layout.addWidget(stat_lbl)

        # -- Tablo --
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Palet", "Lot No", "Miktar", "Durum", "Sec", "Islem"])
        self.table.setColumnWidth(5, brand.sp(120))

        tbl_header = self.table.horizontalHeader()
        tbl_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl_header.setSectionResizeMode(1, QHeaderView.Stretch)
        tbl_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tbl_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        tbl_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        tbl_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
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

        self._fill_table()
        layout.addWidget(self.table, 1)

        # -- Alt butonlar --
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(brand.SP_3)

        btn_tumunu = QPushButton("Tumunu Sec")
        btn_tumunu.setCursor(Qt.PointingHandCursor)
        btn_tumunu.setFixedHeight(brand.sp(38))
        btn_tumunu.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
        """)
        btn_tumunu.clicked.connect(self._tumunu_sec)
        btn_lay.addWidget(btn_tumunu)

        btn_sec_onayla = QPushButton("Secilenleri Onayla")
        btn_sec_onayla.setCursor(Qt.PointingHandCursor)
        btn_sec_onayla.setFixedHeight(brand.sp(38))
        btn_sec_onayla.setStyleSheet(f"""
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
        btn_sec_onayla.clicked.connect(lambda: self._bulk_update('ONAYLANDI'))
        btn_lay.addWidget(btn_sec_onayla)

        btn_sec_red = QPushButton("Secilenleri Reddet")
        btn_sec_red.setCursor(Qt.PointingHandCursor)
        btn_sec_red.setFixedHeight(brand.sp(38))
        btn_sec_red.setStyleSheet(f"""
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
        btn_sec_red.clicked.connect(lambda: self._bulk_update('RED'))
        btn_lay.addWidget(btn_sec_red)

        btn_lay.addStretch()

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
        btn_kapat.clicked.connect(self.close)
        btn_lay.addWidget(btn_kapat)

        layout.addLayout(btn_lay)

    def _fill_table(self):
        self.table.setRowCount(len(self.paletler))
        durum_colors = {
            'BEKLIYOR': QColor(brand.WARNING),
            'ONAYLANDI': QColor(brand.SUCCESS),
            'RED': QColor(brand.ERROR)
        }

        cb_css = f"""
            QCheckBox {{
                spacing: {brand.SP_2}px;
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

        for i, p in enumerate(self.paletler):
            self.table.setRowHeight(i, brand.sp(42))

            self.table.setItem(i, 0, QTableWidgetItem(f"{p['palet_no']}/{p['toplam_palet']}"))
            self.table.setItem(i, 1, QTableWidgetItem(p['lot_no']))

            miktar_item = QTableWidgetItem(f"{p['miktar']:,.0f}")
            miktar_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, miktar_item)

            durum_item = QTableWidgetItem(p['kalite_durumu'] or 'BEKLIYOR')
            durum_item.setForeground(durum_colors.get(p['kalite_durumu'], QColor(brand.TEXT_MUTED)))
            self.table.setItem(i, 3, durum_item)

            cb = QCheckBox()
            cb.setEnabled(p['kalite_durumu'] == 'BEKLIYOR')
            cb.setProperty('lot_no', p['lot_no'])
            cb.setStyleSheet(cb_css)
            w = QWidget()
            l = QHBoxLayout(w)
            l.addWidget(cb)
            l.setAlignment(Qt.AlignCenter)
            l.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(i, 4, w)

            widget = create_action_buttons(self.theme, [
                ("Detay", "Detay", lambda _, palet=p: self._open_palet(palet), "view"),
            ])
            self.table.setCellWidget(i, 5, widget)

    def _open_palet(self, palet):
        dlg = PaletDetayDialog(self.theme, palet, self)
        if dlg.exec():
            self._load_data()
            self._fill_table()

    def _tumunu_sec(self):
        """Bekleyen tum paletleri sec/birak toggle"""
        tumu_secili = True
        for i in range(self.table.rowCount()):
            w = self.table.cellWidget(i, 4)
            if w:
                cb = w.findChild(QCheckBox) if not isinstance(w, QCheckBox) else w
                if cb and cb.isEnabled() and not cb.isChecked():
                    tumu_secili = False
                    break

        for i in range(self.table.rowCount()):
            w = self.table.cellWidget(i, 4)
            if w:
                cb = w.findChild(QCheckBox) if not isinstance(w, QCheckBox) else w
                if cb and cb.isEnabled():
                    cb.setChecked(not tumu_secili)

    def _bulk_update(self, durum):
        selected = []
        for i in range(self.table.rowCount()):
            w = self.table.cellWidget(i, 4)
            if w:
                # Checkbox container icinde veya direkt olabilir
                cb = w.findChild(QCheckBox) if not isinstance(w, QCheckBox) else w
                if cb and cb.isChecked():
                    lot_no = cb.property('lot_no')
                    if lot_no:
                        selected.append(lot_no)

        if not selected:
            QMessageBox.warning(self, "Uyari", "Lutfen en az bir palet secin!")
            return

        durum_text = {'ONAYLANDI': 'onaylamak', 'RED': 'reddetmek'}
        reply = QMessageBox.question(
            self, "Onay",
            f"{len(selected)} paleti {durum_text.get(durum, 'guncellemek')} istediginize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            if durum == 'ONAYLANDI':
                kalite_durumu = 'ONAYLANDI'
                durum_kodu = 'GIRIS_ONAY'
            else:
                kalite_durumu = 'RED'
                durum_kodu = 'RED'

            updated = 0
            for lot in selected:
                cursor.execute("""
                    UPDATE stok.stok_bakiye
                    SET kalite_durumu = ?,
                        durum_kodu = ?,
                        son_hareket_tarihi = GETDATE()
                    WHERE lot_no = ?
                """, (kalite_durumu, durum_kodu, lot))
                updated += cursor.rowcount

            conn.commit()
            LogManager.log_update('kalite', 'stok.stok_bakiye', None, 'Durum guncellendi')

            durum_text2 = {'ONAYLANDI': 'onaylandi', 'RED': 'reddedildi'}
            QMessageBox.information(
                self, "Basarili",
                f"{updated} palet {durum_text2.get(durum, 'guncellendi')}!\n\n"
                f"Yeni Durum: {durum_kodu}"
            )

            self._load_data()
            self._fill_table()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# =====================================================================
# ANA SAYFA
# =====================================================================

class KaliteGirisPage(BasePage):
    """Kalite Giris Kontrol — el kitabi uyumlu sayfa"""

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
            "Kalite Giris Kontrol",
            "Gelen malzeme kalite kontrol islemleri"
        )

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        header.addWidget(btn_yenile)

        layout.addLayout(header)

        # -- 2. KPI cards --
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self._kpi_bekleyen = self.create_stat_card("BEKLEYEN", "0", color=brand.WARNING)
        kpi_row.addWidget(self._kpi_bekleyen)

        self._kpi_onaylanan = self.create_stat_card("ONAYLANAN", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self._kpi_onaylanan)

        self._kpi_toplam = self.create_stat_card("TOPLAM PALET", "0", color=brand.PRIMARY)
        kpi_row.addWidget(self._kpi_toplam)

        kpi_row.addStretch()
        layout.addLayout(kpi_row)

        # -- Filter bar --
        filter_row = QHBoxLayout()
        filter_row.setSpacing(brand.SP_3)

        input_css = f"""
            QComboBox, QLineEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus, QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """

        self.firma_combo = QComboBox()
        self.firma_combo.setFixedWidth(brand.sp(220))
        self.firma_combo.setFixedHeight(brand.sp(34))
        self.firma_combo.setStyleSheet(input_css)
        self.firma_combo.addItem("Tum Firmalar", None)
        self.firma_combo.currentIndexChanged.connect(self._load_data)
        filter_row.addWidget(self.firma_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Lot / Stok Kodu Ara...")
        self.search_input.setFixedWidth(brand.sp(200))
        self.search_input.setFixedHeight(brand.sp(34))
        self.search_input.setStyleSheet(input_css)
        self.search_input.returnPressed.connect(self._load_data)
        filter_row.addWidget(self.search_input)

        self.durum_combo = QComboBox()
        self.durum_combo.setFixedWidth(brand.sp(140))
        self.durum_combo.setFixedHeight(brand.sp(34))
        self.durum_combo.setStyleSheet(input_css)
        self.durum_combo.addItem("Bekleyenler", "BEKLIYOR")
        self.durum_combo.addItem("Tumu", None)
        self.durum_combo.addItem("Onaylananlar", "ONAYLANDI")
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        filter_row.addWidget(self.durum_combo)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # -- 3. Tablo --
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Ana Lot", "Stok Kodu", "Musteri", "Palet", "Bekleyen", "Durum", "Islem"
        ])
        self.table.setColumnWidth(6, brand.sp(120))
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_double_click)
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
    def _load_firmalar(self, cursor):
        """Firma combo'sunu doldur (mevcut secimi koru)"""
        mevcut = self.firma_combo.currentData()
        self.firma_combo.blockSignals(True)
        self.firma_combo.clear()
        self.firma_combo.addItem("Tum Firmalar", None)
        try:
            cursor.execute("""
                SELECT DISTINCT COALESCE(gi.cari_unvani, sb.cari_unvani) as firma
                FROM stok.stok_bakiye sb
                LEFT JOIN siparis.giris_irsaliye_satirlar gis ON sb.irsaliye_satir_id = gis.id
                LEFT JOIN siparis.giris_irsaliyeleri gi ON gis.irsaliye_id = gi.id
                WHERE sb.parent_lot_no IS NOT NULL
                  AND sb.durum_kodu IN ('KABUL', 'GIRIS_KALITE', 'GIRIS_ONAY')
                  AND COALESCE(gi.cari_unvani, sb.cari_unvani) IS NOT NULL
                ORDER BY firma
            """)
            for row in cursor.fetchall():
                if row[0]:
                    kisa = row[0][:40] if len(row[0]) > 40 else row[0]
                    self.firma_combo.addItem(kisa, row[0])
        except Exception:
            pass
        # Onceki secimi geri yukle
        if mevcut:
            for i in range(self.firma_combo.count()):
                if self.firma_combo.itemData(i) == mevcut:
                    self.firma_combo.setCurrentIndex(i)
                    break
        self.firma_combo.blockSignals(False)

    # -----------------------------------------------------------------
    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Firma listesini guncelle
            self._load_firmalar(cursor)

            search = self.search_input.text().strip()
            durum = self.durum_combo.currentData()
            firma = self.firma_combo.currentData()

            query = """
                SELECT sb.parent_lot_no, MAX(u.urun_kodu), COUNT(*),
                    SUM(CASE WHEN sb.kalite_durumu = 'BEKLIYOR' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sb.kalite_durumu = 'ONAYLANDI' THEN 1 ELSE 0 END),
                    MAX(COALESCE(gi.cari_unvani, sb.cari_unvani))
                FROM stok.stok_bakiye sb
                LEFT JOIN stok.urunler u ON sb.urun_id = u.id
                LEFT JOIN siparis.giris_irsaliye_satirlar gis ON sb.irsaliye_satir_id = gis.id
                LEFT JOIN siparis.giris_irsaliyeleri gi ON gis.irsaliye_id = gi.id
                WHERE sb.parent_lot_no IS NOT NULL
                  AND sb.durum_kodu IN ('KABUL', 'GIRIS_KALITE', 'GIRIS_ONAY')
            """
            params = []
            if search:
                query += " AND (sb.parent_lot_no LIKE ? OR u.urun_kodu LIKE ?)"
                params.extend([f"%{search}%"] * 2)
            if firma:
                query += " AND COALESCE(gi.cari_unvani, sb.cari_unvani) = ?"
                params.append(firma)
            query += " GROUP BY sb.parent_lot_no"
            if durum == 'BEKLIYOR':
                query += " HAVING SUM(CASE WHEN sb.kalite_durumu = 'BEKLIYOR' THEN 1 ELSE 0 END) > 0"
            elif durum == 'ONAYLANDI':
                query += " HAVING SUM(CASE WHEN sb.kalite_durumu = 'BEKLIYOR' THEN 1 ELSE 0 END) = 0"
            query += " ORDER BY sb.parent_lot_no DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Istatistikler
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN kalite_durumu = 'BEKLIYOR' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN kalite_durumu = 'ONAYLANDI' THEN 1 ELSE 0 END),
                    COUNT(*)
                FROM stok.stok_bakiye
                WHERE parent_lot_no IS NOT NULL
                  AND durum_kodu IN ('KABUL', 'GIRIS_KALITE', 'GIRIS_ONAY')
            """)
            stats = cursor.fetchone()

            if stats:
                self._kpi_bekleyen.findChild(QLabel, "stat_value").setText(str(stats[0] or 0))
                self._kpi_onaylanan.findChild(QLabel, "stat_value").setText(str(stats[1] or 0))
                self._kpi_toplam.findChild(QLabel, "stat_value").setText(str(stats[2] or 0))

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(row[0] or ''))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(row[5] or ''))

                palet_item = QTableWidgetItem(str(row[2] or 0))
                palet_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 3, palet_item)

                bekleyen_item = QTableWidgetItem(str(row[3] or 0))
                bekleyen_item.setTextAlignment(Qt.AlignCenter)
                if row[3] and row[3] > 0:
                    bekleyen_item.setForeground(QColor(brand.WARNING))
                    bekleyen_item.setFont(QFont(brand.FONT_FAMILY, -1, QFont.Bold))
                self.table.setItem(i, 4, bekleyen_item)

                if row[3] == row[2]:
                    durum_text, durum_color = "Bekliyor", QColor(brand.WARNING)
                elif row[3] == 0:
                    durum_text, durum_color = "Tamamlandi", QColor(brand.SUCCESS)
                else:
                    durum_text, durum_color = f"{row[4]}/{row[2]}", QColor(brand.INFO)
                durum_item = QTableWidgetItem(durum_text)
                durum_item.setForeground(durum_color)
                self.table.setItem(i, 5, durum_item)

                widget = self.create_action_buttons([
                    ("Detay", "Detay Gor", lambda checked, pl=row[0]: self._open_detail(pl), "info"),
                ])
                self.table.setCellWidget(i, 6, widget)

        except Exception as e:
            print(f"[kalite_giris] Veri yukleme hatasi: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # -----------------------------------------------------------------
    def _open_detail(self, parent_lot):
        dlg = AnaLotDetayDialog(self.theme, parent_lot, self)
        dlg.exec()
        self._load_data()

    def _on_double_click(self, index):
        parent_lot = self.table.item(index.row(), 0).text()
        self._open_detail(parent_lot)
