# -*- coding: utf-8 -*-
"""
NEXOR ERP - Banyo Analiz Sonuclari (KATAFOREZ PARAMETRELERI ILE)
================================================================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
uretim.banyo_analiz_sonuclari tablosu icin CRUD
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QDoubleSpinBox, QTextEdit, QComboBox, QDateTimeEdit, QTabWidget, QWidget, QGroupBox
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class AnalizDialog(QDialog):
    """Analiz Sonucu Ekleme/Duzenleme - KATAFOREZ PARAMETRELERI ILE"""

    def __init__(self, theme: dict, analiz_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.analiz_id = analiz_id
        self.data = {}
        self.banyo_limitleri = {}

        self.setWindowTitle("Yeni Kataforez Analiz" if not analiz_id else "Kataforez Analiz Duzenle")
        self.setMinimumSize(brand.sp(700), brand.sp(750))

        if analiz_id:
            self._load_data()
        self._setup_ui()

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM uretim.banyo_analiz_sonuclari WHERE id = ?", (self.analiz_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QTextEdit, QDoubleSpinBox, QComboBox, QDateTimeEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus,
            QComboBox:focus, QDateTimeEdit:focus {{
                border-color: {brand.PRIMARY};
            }}
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                background: {brand.BG_CARD};
                border-radius: {brand.R_LG}px;
            }}
            QTabBar::tab {{
                background: {brand.BG_INPUT};
                padding: {brand.SP_2}px {brand.SP_5}px;
                color: {brand.TEXT};
                border-top-left-radius: {brand.R_SM}px;
                border-top-right-radius: {brand.R_SM}px;
                font-size: {brand.FS_BODY}px;
            }}
            QTabBar::tab:selected {{
                background: {brand.BG_CARD};
                border-bottom: 3px solid {brand.PRIMARY};
            }}
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

        # Temel Bilgiler
        temel_form = QFormLayout()
        temel_form.setSpacing(brand.SP_2)

        self.banyo_combo = QComboBox()
        self.banyo_combo.addItem("-- Seciniz --", None)
        self._load_banyolar()
        self.banyo_combo.currentIndexChanged.connect(self._load_banyo_limitleri)
        temel_form.addRow("Banyo *:", self.banyo_combo)

        self.tarih_input = QDateTimeEdit()
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        if self.data.get('tarih'):
            self.tarih_input.setDateTime(self.data['tarih'])
        else:
            self.tarih_input.setDateTime(QDateTime.currentDateTime())
        temel_form.addRow("Tarih *:", self.tarih_input)

        self.analist_combo = QComboBox()
        self.analist_combo.addItem("-- Seciniz --", None)
        self._load_analistler()
        temel_form.addRow("Analist *:", self.analist_combo)

        layout.addLayout(temel_form)

        # Parametreler - Tab Widget
        tabs = QTabWidget()
        tabs.addTab(self._create_temel_tab(), "Temel Parametreler")
        tabs.addTab(self._create_kataforez_tab(), "Kataforez Parametreleri")
        tabs.addTab(self._create_notlar_tab(), "Notlar")
        layout.addWidget(tabs, 1)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Iptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                padding: {brand.SP_2}px {brand.SP_5}px;
                border-radius: {brand.R_SM}px;
                min-height: {brand.sp(38)}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{
                background: {brand.BORDER};
            }}
        """)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                padding: {brand.SP_2}px {brand.SP_8}px;
                border-radius: {brand.R_SM}px;
                min-height: {brand.sp(38)}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _create_temel_tab(self):
        """Temel parametreler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)

        # Sicaklik ve pH Group
        sic_ph_group = QGroupBox("Sicaklik ve pH")
        sic_ph_form = QFormLayout(sic_ph_group)

        self.sicaklik_input = self._create_param_spinbox(0, 200, " C", self.data.get('sicaklik', 0))
        sic_ph_form.addRow("Sicaklik:", self.sicaklik_input)

        self.ph_input = self._create_param_spinbox(0, 14, "", self.data.get('ph', 0), decimals=2)
        sic_ph_form.addRow("pH:", self.ph_input)

        layout.addWidget(sic_ph_group)

        # Iletkenlik ve Asitlik Group
        ilet_asit_group = QGroupBox("Iletkenlik ve Asitlik")
        ilet_asit_form = QFormLayout(ilet_asit_group)

        self.iletkenlik_input = self._create_param_spinbox(0, 99999, " uS/cm", self.data.get('iletkenlik', 0))
        ilet_asit_form.addRow("Iletkenlik:", self.iletkenlik_input)

        self.toplam_asit_input = self._create_param_spinbox(0, 999, "", self.data.get('toplam_asitlik', 0), decimals=2)
        ilet_asit_form.addRow("Toplam Asitlik:", self.toplam_asit_input)

        self.serbest_asit_input = self._create_param_spinbox(0, 999, "", self.data.get('serbest_asitlik', 0), decimals=2)
        ilet_asit_form.addRow("Serbest Asitlik:", self.serbest_asit_input)

        layout.addWidget(ilet_asit_group)

        # Metal Icerikleri Group
        metal_group = QGroupBox("Metal Icerikleri")
        metal_form = QFormLayout(metal_group)

        self.demir_input = self._create_param_spinbox(0, 9999, " ppm", self.data.get('demir_ppm', 0), decimals=4)
        metal_form.addRow("Demir (Fe):", self.demir_input)

        self.cinko_input = self._create_param_spinbox(0, 9999, " ppm", self.data.get('cinko_ppm', 0), decimals=4)
        metal_form.addRow("Cinko (Zn):", self.cinko_input)

        layout.addWidget(metal_group)
        layout.addStretch()

        return widget

    def _create_kataforez_tab(self):
        """Kataforez ozel parametreleri sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)

        # Kati Madde Group
        kati_group = QGroupBox("Kati Madde Olcumu")
        kati_form = QFormLayout(kati_group)

        self.kati_madde_input = self._create_param_spinbox(0, 100, " %", self.data.get('kati_madde_yuzde', 0), decimals=2)
        kati_form.addRow("Kati Madde:", self.kati_madde_input)

        kati_info = QLabel("Ideal: 15.0 - 20.0 % (Gravimetrik, 110 C, 3 saat)")
        kati_info.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; font-style: italic;")
        kati_form.addRow("", kati_info)

        layout.addWidget(kati_group)

        # P/B Orani Group
        pb_group = QGroupBox("Pigment / Baglayici Orani")
        pb_form = QFormLayout(pb_group)

        self.pb_orani_input = self._create_param_spinbox(0, 10, "", self.data.get('pb_orani', 0), decimals=2)
        pb_form.addRow("P/B Orani:", self.pb_orani_input)

        pb_info = QLabel("Ideal: 0.15 - 0.40 (Kul testi, 450-500 C)")
        pb_info.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; font-style: italic;")
        pb_form.addRow("", pb_info)

        layout.addWidget(pb_group)

        # Solvent Group
        solvent_group = QGroupBox("Solvent Icerigi")
        solvent_form = QFormLayout(solvent_group)

        self.solvent_input = self._create_param_spinbox(0, 100, " %", self.data.get('solvent_yuzde', 0), decimals=2)
        solvent_form.addRow("Solvent:", self.solvent_input)

        solvent_info = QLabel("Ideal: 1.0 - 3.0 % (GC Analizi)")
        solvent_info.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; font-style: italic;")
        solvent_form.addRow("", solvent_info)

        layout.addWidget(solvent_group)

        # MEQ Group
        meq_group = QGroupBox("MEQ Degeri")
        meq_form = QFormLayout(meq_group)

        self.meq_input = self._create_param_spinbox(0, 999, " meq", self.data.get('meq_degeri', 0), decimals=2)
        meq_form.addRow("MEQ:", self.meq_input)

        meq_info = QLabel("Ideal: 30 - 40 meq (Titrasyon)")
        meq_info.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; font-style: italic;")
        meq_form.addRow("", meq_info)

        layout.addWidget(meq_group)
        layout.addStretch()

        return widget

    def _create_notlar_tab(self):
        """Notlar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)

        self.notlar_input = QTextEdit()
        self.notlar_input.setPlaceholderText("Analiz ile ilgili notlarinizi buraya yazabilirsiniz...")
        self.notlar_input.setText(self.data.get('notlar', '') or '')
        self.notlar_input.setStyleSheet(f"""
            QTextEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QTextEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        layout.addWidget(self.notlar_input)

        return widget

    def _create_param_spinbox(self, min_val, max_val, suffix, value, decimals=0):
        """Parametre spinbox olusturur"""
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setDecimals(decimals)
        if suffix:
            spinbox.setSuffix(suffix)
        spinbox.setValue(value or 0)
        spinbox.setMinimumWidth(brand.sp(150))
        return spinbox

    def _load_banyolar(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT b.id, b.kod, b.ad, h.kod
                FROM uretim.banyo_tanimlari b
                JOIN tanim.uretim_hatlari h ON b.hat_id=h.id
                WHERE b.aktif_mi=1 ORDER BY h.sira_no, b.kod""")
            for row in cursor.fetchall():
                self.banyo_combo.addItem(f"{row[3]} / {row[1]} - {row[2]}", row[0])
            if self.data.get('banyo_id'):
                idx = self.banyo_combo.findData(self.data['banyo_id'])
                if idx >= 0:
                    self.banyo_combo.setCurrentIndex(idx)
                    self._load_banyo_limitleri()
        except Exception:
            pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_analistler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad, soyad FROM ik.personeller WHERE aktif_mi=1 ORDER BY ad")
            for row in cursor.fetchall():
                self.analist_combo.addItem(f"{row[1]} {row[2]}", row[0])
            if self.data.get('analist_id'):
                idx = self.analist_combo.findData(self.data['analist_id'])
                if idx >= 0: self.analist_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_banyo_limitleri(self):
        """Secili banyonun limit degerlerini yukler"""
        banyo_id = self.banyo_combo.currentData()
        if not banyo_id:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sicaklik_min, sicaklik_max, sicaklik_hedef,
                       ph_min, ph_max, ph_hedef,
                       iletkenlik_min, iletkenlik_max, iletkenlik_hedef,
                       kati_madde_min, kati_madde_max, kati_madde_hedef,
                       pb_orani_min, pb_orani_max, pb_orani_hedef,
                       solvent_min, solvent_max, solvent_hedef,
                       meq_min, meq_max, meq_hedef
                FROM uretim.banyo_tanimlari WHERE id = ?
            """, (banyo_id,))
            row = cursor.fetchone()
            if row:
                self.banyo_limitleri = dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            print(f"Limit yukleme hatasi: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _validate_limits(self):
        """Parametre limitlerini kontrol eder ve uyari verir"""
        if not self.banyo_limitleri:
            return True

        uyarilar = []

        # Sicaklik kontrolu
        sic = self.sicaklik_input.value()
        if self.banyo_limitleri.get('sicaklik_min') and sic < self.banyo_limitleri['sicaklik_min']:
            uyarilar.append(f"Sicaklik limit altinda! (Min: {self.banyo_limitleri['sicaklik_min']} C)")
        if self.banyo_limitleri.get('sicaklik_max') and sic > self.banyo_limitleri['sicaklik_max']:
            uyarilar.append(f"Sicaklik limit ustunde! (Max: {self.banyo_limitleri['sicaklik_max']} C)")

        # pH kontrolu
        ph = self.ph_input.value()
        if self.banyo_limitleri.get('ph_min') and ph < self.banyo_limitleri['ph_min']:
            uyarilar.append(f"pH limit altinda! (Min: {self.banyo_limitleri['ph_min']})")
        if self.banyo_limitleri.get('ph_max') and ph > self.banyo_limitleri['ph_max']:
            uyarilar.append(f"pH limit ustunde! (Max: {self.banyo_limitleri['ph_max']})")

        # Iletkenlik kontrolu
        ilet = self.iletkenlik_input.value()
        if self.banyo_limitleri.get('iletkenlik_min') and ilet < self.banyo_limitleri['iletkenlik_min']:
            uyarilar.append(f"Iletkenlik limit altinda! (Min: {self.banyo_limitleri['iletkenlik_min']} uS/cm)")
        if self.banyo_limitleri.get('iletkenlik_max') and ilet > self.banyo_limitleri['iletkenlik_max']:
            uyarilar.append(f"Iletkenlik limit ustunde! (Max: {self.banyo_limitleri['iletkenlik_max']} uS/cm)")

        # Kati madde kontrolu
        kati = self.kati_madde_input.value()
        if self.banyo_limitleri.get('kati_madde_min') and kati < self.banyo_limitleri['kati_madde_min']:
            uyarilar.append(f"Kati madde limit altinda! (Min: {self.banyo_limitleri['kati_madde_min']}%)")
        if self.banyo_limitleri.get('kati_madde_max') and kati > self.banyo_limitleri['kati_madde_max']:
            uyarilar.append(f"Kati madde limit ustunde! (Max: {self.banyo_limitleri['kati_madde_max']}%)")

        if uyarilar:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Parametre Limitleri Disinda!")
            msg.setText("Bazi parametreler limit degerlerin disinda:\n\n" + "\n".join(uyarilar))
            msg.setInformativeText("\nYine de kaydetmek istiyor musunuz?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            return msg.exec() == QMessageBox.Yes

        return True

    def _save(self):
        banyo_id = self.banyo_combo.currentData()
        analist_id = self.analist_combo.currentData()

        if not banyo_id or not analist_id:
            QMessageBox.warning(self, "Uyari", "Banyo ve Analist secimi zorunludur!")
            return

        # Limit kontrolu
        if not self._validate_limits():
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            params = (
                banyo_id,
                self.tarih_input.dateTime().toPython(),
                analist_id,
                self.sicaklik_input.value() or None,
                self.ph_input.value() or None,
                self.iletkenlik_input.value() or None,
                self.toplam_asit_input.value() or None,
                self.serbest_asit_input.value() or None,
                self.notlar_input.toPlainText().strip() or None
            )

            if self.analiz_id:
                cursor.execute("""UPDATE uretim.banyo_analiz_sonuclari SET
                    banyo_id=?, tarih=?, analist_id=?, sicaklik=?, ph=?, iletkenlik=?,
                    toplam_asitlik=?, serbest_asitlik=?, notlar=?
                    WHERE id=?""", params + (self.analiz_id,))
            else:
                cursor.execute("""INSERT INTO uretim.banyo_analiz_sonuclari
                    (banyo_id, tarih, analist_id, sicaklik, ph, iletkenlik,
                     toplam_asitlik, serbest_asitlik, notlar)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", params)

                # Analiz ID'yi al (yeni eklenen kayit)
                cursor.execute("SELECT @@IDENTITY")
                analiz_id = cursor.fetchone()[0]

            conn.commit()

            # LAB EVENT KAYDI
            try:
                # Durum kontrolu
                durum = self._check_analiz_durum(banyo_id, params)

                if durum in ['UYARI', 'KRITIK']:
                    # Lab event tablosuna yaz
                    cursor.execute("""
                        INSERT INTO uretim.lab_event_log
                        (banyo_id, analiz_id, event_tipi, sicaklik, ph,
                         iletkenlik, toplam_asitlik, serbest_asitlik, notlar, analist_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        banyo_id,
                        analiz_id if not self.analiz_id else self.analiz_id,
                        f'LAB_ANALIZ_{durum}',
                        params[3],  # sicaklik
                        params[4],  # ph
                        params[5],  # iletkenlik
                        params[6],  # toplam_asitlik
                        params[7],  # serbest_asitlik
                        params[8],  # notlar
                        analist_id
                    ))
                    conn.commit()
                    print(f"Lab event kaydedildi: BANYO-{banyo_id} -> {durum}")

                    # NEXOR BILDIRIM SISTEMI (WhatsApp + Email otomatik)
                    try:
                        from core.bildirim_tetikleyici import BildirimTetikleyici
                        cursor.execute("""
                            SELECT kod + ' - ' + ad,
                                   sicaklik_min, sicaklik_max, sicaklik_hedef,
                                   ph_min, ph_max, ph_hedef,
                                   toplam_asit_min, toplam_asit_max
                            FROM uretim.banyo_tanimlari WHERE id = ?
                        """, (banyo_id,))
                        b_row = cursor.fetchone()
                        b_adi = b_row[0] if b_row else f"Banyo-{banyo_id}"

                        detay_parts = []

                        if params[3]:
                            sic = float(params[3])
                            s_min = float(b_row[1]) if b_row and b_row[1] else None
                            s_max = float(b_row[2]) if b_row and b_row[2] else None
                            limit = ""
                            if s_min is not None and s_max is not None:
                                limit = f" [Limit: {s_min:.1f}-{s_max:.1f}]"
                                if sic < s_min or sic > s_max:
                                    limit += " LIMIT DISI!"
                            detay_parts.append(f"Sicaklik: {sic:.1f} C{limit}")

                        if params[4]:
                            ph_v = float(params[4])
                            ph_min_v = float(b_row[4]) if b_row and b_row[4] else None
                            ph_max_v = float(b_row[5]) if b_row and b_row[5] else None
                            limit = ""
                            if ph_min_v is not None and ph_max_v is not None:
                                limit = f" [Limit: {ph_min_v:.2f}-{ph_max_v:.2f}]"
                                if ph_v < ph_min_v or ph_v > ph_max_v:
                                    limit += " LIMIT DISI!"
                            detay_parts.append(f"pH: {ph_v:.2f}{limit}")

                        if params[5]:
                            detay_parts.append(f"Iletkenlik: {float(params[5]):.0f}")

                        if params[6]:
                            asit = float(params[6])
                            a_min = float(b_row[7]) if b_row and b_row[7] else None
                            a_max = float(b_row[8]) if b_row and b_row[8] else None
                            limit = ""
                            if a_min is not None and a_max is not None:
                                limit = f" [Limit: {a_min:.2f}-{a_max:.2f}]"
                                if asit < a_min or asit > a_max:
                                    limit += " LIMIT DISI!"
                            detay_parts.append(f"Toplam Asit: {asit:.2f}{limit}")

                        BildirimTetikleyici.lab_analiz_hatali(
                            analiz_id=analiz_id if not self.analiz_id else self.analiz_id,
                            banyo_adi=b_adi,
                            durum=durum,
                            detay='\n'.join(detay_parts),
                        )
                    except Exception as bt_err:
                        print(f"Bildirim tetikleyici hatasi: {bt_err}")

            except Exception as e:
                print(f"Lab event hatasi (onemsiz): {e}")
                import traceback
                traceback.print_exc()

            QMessageBox.information(self, "Basarili", "Analiz sonucu kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit sirasinda hata:\n{str(e)}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _check_analiz_durum(self, banyo_id, params):
        """Analiz sonucuna gore durum belirle: NORMAL / UYARI / KRITIK"""
        try:
            # Banyo limitlerini al
            if not self.banyo_limitleri or self.banyo_limitleri.get('banyo_id') != banyo_id:
                conn = None
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT sicaklik_min, sicaklik_max, sicaklik_hedef,
                               ph_min, ph_max, ph_hedef,
                               toplam_asit_min, toplam_asit_max
                        FROM uretim.banyo_tanimlari WHERE id = ?
                    """, (banyo_id,))
                    row = cursor.fetchone()
                finally:
                    if conn:
                        try: conn.close()
                        except Exception: pass

                if row:
                    self.banyo_limitleri = {
                        'banyo_id': banyo_id,
                        'sicaklik_min': row[0], 'sicaklik_max': row[1], 'sicaklik_hedef': row[2],
                        'ph_min': row[3], 'ph_max': row[4], 'ph_hedef': row[5],
                        'asit_min': row[6], 'asit_max': row[7]
                    }

            # Parametrelerden degerleri al
            sicaklik = float(params[3]) if params[3] else None
            ph = float(params[4]) if params[4] else None
            asit = float(params[6]) if params[6] else None

            durum = 'NORMAL'

            # Sicaklik kontrolu
            if sicaklik and self.banyo_limitleri.get('sicaklik_min') and self.banyo_limitleri.get('sicaklik_max'):
                s_min = float(self.banyo_limitleri['sicaklik_min'])
                s_max = float(self.banyo_limitleri['sicaklik_max'])

                if sicaklik < s_min or sicaklik > s_max:
                    hedef = float(self.banyo_limitleri.get('sicaklik_hedef') or (s_min + s_max) / 2)
                    if abs(sicaklik - hedef) > 10:
                        durum = 'KRITIK'
                    else:
                        durum = 'UYARI'

            # pH kontrolu
            if ph and self.banyo_limitleri.get('ph_min') and self.banyo_limitleri.get('ph_max'):
                ph_min = float(self.banyo_limitleri['ph_min'])
                ph_max = float(self.banyo_limitleri['ph_max'])

                if ph < ph_min or ph > ph_max:
                    hedef = float(self.banyo_limitleri.get('ph_hedef') or (ph_min + ph_max) / 2)
                    if abs(ph - hedef) > 1:
                        durum = 'KRITIK'
                    elif durum != 'KRITIK':
                        durum = 'UYARI'

            # Asitlik kontrolu
            if asit and self.banyo_limitleri.get('asit_min') and self.banyo_limitleri.get('asit_max'):
                a_min = float(self.banyo_limitleri['asit_min'])
                a_max = float(self.banyo_limitleri['asit_max'])

                if asit < a_min or asit > a_max:
                    if durum != 'KRITIK':
                        durum = 'UYARI'

            return durum

        except Exception as e:
            print(f"Durum kontrol hatasi: {e}")
            return 'NORMAL'


class LabAnalizPage(BasePage):
    """Banyo Analiz Sonuclari Listesi"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_4)

        # -- Page Header --
        header = self.create_page_header("Banyo Analiz Sonuclari", "Kataforez banyo parametreleri takibi")
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        header.addWidget(self.stat_label)
        layout.addLayout(header)

        # -- Toolbar --
        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)
        self.banyo_combo = QComboBox()
        self.banyo_combo.addItem("Tum Banyolar", None)
        self._load_banyo_filter()
        self.banyo_combo.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                min-width: {brand.sp(200)}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.banyo_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.banyo_combo)
        toolbar.addStretch()

        add_btn = QPushButton("Yeni Analiz")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_4}px;
                min-height: {brand.sp(38)}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ opacity: 0.8; }}
        """)
        add_btn.clicked.connect(self._add_new)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        # -- Table --
        self.table = QTableWidget()
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
            QTableWidget::item:selected {{ background: {brand.PRIMARY}; }}
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
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "ID", "Banyo", "Tarih", "Sicaklik", "pH", "Iletkenlik",
            "Kati Madde", "P/B", "Solvent", "MEQ", "Demir", "Cinko", "Islem"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, brand.sp(50))
        self.table.setColumnWidth(2, brand.sp(130))
        self.table.setColumnWidth(3, brand.sp(80))
        self.table.setColumnWidth(4, brand.sp(60))
        self.table.setColumnWidth(5, brand.sp(90))
        self.table.setColumnWidth(6, brand.sp(80))
        self.table.setColumnWidth(7, brand.sp(60))
        self.table.setColumnWidth(8, brand.sp(70))
        self.table.setColumnWidth(9, brand.sp(60))
        self.table.setColumnWidth(10, brand.sp(60))
        self.table.setColumnWidth(11, brand.sp(60))
        self.table.setColumnWidth(12, brand.sp(120))
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table, 1)

    def _load_banyo_filter(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT b.id, b.kod, h.kod FROM uretim.banyo_tanimlari b
                JOIN tanim.uretim_hatlari h ON b.hat_id=h.id WHERE b.aktif_mi=1 ORDER BY h.sira_no, b.kod""")
            for row in cursor.fetchall():
                self.banyo_combo.addItem(f"{row[2]} / {row[1]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """SELECT a.id, b.kod, a.tarih, a.sicaklik, a.ph, a.iletkenlik,
                     a.kati_madde_yuzde, a.pb_orani, a.solvent_yuzde, a.meq_degeri,
                     a.demir_ppm, a.cinko_ppm,
                     b.sicaklik_min, b.sicaklik_max, b.ph_min, b.ph_max,
                     b.kati_madde_min, b.kati_madde_max
                     FROM uretim.banyo_analiz_sonuclari a
                     JOIN uretim.banyo_tanimlari b ON a.banyo_id=b.id
                     WHERE 1=1"""
            params = []

            banyo_id = self.banyo_combo.currentData()
            if banyo_id:
                sql += " AND a.banyo_id=?"
                params.append(banyo_id)

            sql += " ORDER BY a.tarih DESC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))

                tarih = row[2].strftime("%d.%m.%Y %H:%M") if row[2] else '-'
                self.table.setItem(i, 2, QTableWidgetItem(tarih))

                # Sicaklik (limit kontrolu)
                sic_item = QTableWidgetItem(f"{row[3]:.1f} C" if row[3] else '-')
                if row[3] and row[12] and row[13]:
                    if row[3] < row[12] or row[3] > row[13]:
                        sic_item.setForeground(QColor(brand.ERROR))
                    else:
                        sic_item.setForeground(QColor(brand.SUCCESS))
                self.table.setItem(i, 3, sic_item)

                # pH (limit kontrolu)
                ph_item = QTableWidgetItem(f"{row[4]:.2f}" if row[4] else '-')
                if row[4] and row[14] and row[15]:
                    if row[4] < row[14] or row[4] > row[15]:
                        ph_item.setForeground(QColor(brand.ERROR))
                    else:
                        ph_item.setForeground(QColor(brand.SUCCESS))
                self.table.setItem(i, 4, ph_item)

                self.table.setItem(i, 5, QTableWidgetItem(f"{row[5]:.0f}" if row[5] else '-'))

                # Kati Madde (limit kontrolu)
                km_item = QTableWidgetItem(f"{row[6]:.2f}%" if row[6] else '-')
                if row[6] and row[16] and row[17]:
                    if row[6] < row[16] or row[6] > row[17]:
                        km_item.setForeground(QColor(brand.ERROR))
                    else:
                        km_item.setForeground(QColor(brand.SUCCESS))
                self.table.setItem(i, 6, km_item)

                # P/B Orani
                self.table.setItem(i, 7, QTableWidgetItem(f"{row[7]:.2f}" if row[7] else '-'))

                # Solvent
                self.table.setItem(i, 8, QTableWidgetItem(f"{row[8]:.2f}%" if row[8] else '-'))

                # MEQ
                self.table.setItem(i, 9, QTableWidgetItem(f"{row[9]:.0f}" if row[9] else '-'))

                self.table.setItem(i, 10, QTableWidgetItem(f"{row[10]:.0f}" if row[10] else '-'))
                self.table.setItem(i, 11, QTableWidgetItem(f"{row[11]:.0f}" if row[11] else '-'))

                widget = self.create_action_buttons([
                    ("Duzenle", "Duzenle", lambda checked, rid=row[0]: self._edit_item(rid), "edit"),
                    ("Sil", "Sil", lambda checked, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 12, widget)
                self.table.setRowHeight(i, brand.sp(42))

            self.stat_label.setText(f"Toplam: {len(rows)} analiz")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _add_new(self):
        dlg = AnalizDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _edit_item(self, aid):
        dlg = AnalizDialog(self.theme, aid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _delete_item(self, aid):
        if QMessageBox.question(self, "Onay", "Bu analiz kaydini silmek istediginize emin misiniz?") == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM uretim.banyo_analiz_sonuclari WHERE id=?", (aid,))
                conn.commit()
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass

    def _gonder_whatsapp_bildirimi(self, cursor, banyo_id, durum, params):
        """WhatsApp bildirimi gonder"""
        try:
            # WhatsApp abonesi kullanicilari bul
            cursor.execute("""
                SELECT k.id, k.telefon, k.ad, k.soyad
                FROM sistem.kullanicilar k
                JOIN sistem.bildirim_abonelikleri a ON k.id = a.kullanici_id
                WHERE a.whatsapp_bildirim = 1
                  AND k.aktif_mi = 1
                  AND k.telefon IS NOT NULL
            """)

            alicilar = cursor.fetchall()

            if not alicilar:
                print("WhatsApp abonesi bulunamadi")
                return

            # Banyo bilgisini al
            cursor.execute("SELECT kod, ad FROM uretim.banyo_tanimlari WHERE id = ?", (banyo_id,))
            banyo_bilgi = cursor.fetchone()
            banyo_adi = f"{banyo_bilgi[0]} - {banyo_bilgi[1]}" if banyo_bilgi else f"Banyo-{banyo_id}"

            # Mesaj sablonu
            from datetime import datetime
            durum_isaret = "[KRITIK]" if durum == "KRITIK" else "[UYARI]"
            mesaj = f"""{durum_isaret} NEXOR ERP - Lab Analiz {durum}!

Banyo: {banyo_adi}
Sicaklik: {params[3]:.1f} C
pH: {params[4]:.2f}
Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}

Lutfen kontrol edin!"""

            # WhatsApp servisini import et ve gonder
            from utils.whatsapp_service import gonder_whatsapp

            basarili = 0
            for kullanici_id, telefon, ad, soyad in alicilar:
                success, msg = gonder_whatsapp(telefon, mesaj)
                if success:
                    basarili += 1
                    print(f"WhatsApp gonderildi: {ad} {soyad} ({telefon})")
                else:
                    print(f"WhatsApp gonderilemedi: {ad} {soyad} - {msg}")

            print(f"WhatsApp bildirimi: {basarili}/{len(alicilar)} basarili")

        except ImportError:
            print("WhatsApp servisi bulunamadi (whatsapp_service.py)")
        except Exception as e:
            print(f"WhatsApp bildirim hatasi: {e}")
            import traceback
            traceback.print_exc()
