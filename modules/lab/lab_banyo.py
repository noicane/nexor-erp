# -*- coding: utf-8 -*-
"""
NEXOR ERP - Banyo Tanimlari
=============================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
uretim.banyo_tanimlari tablosu icin CRUD
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QDoubleSpinBox, QComboBox, QTabWidget, QWidget, QScrollArea,
    QGroupBox, QGridLayout, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand


class BanyoDialog(QDialog):
    """Banyo Tanimi Ekleme/Duzenleme — el kitabi uyumlu"""

    def __init__(self, theme: dict, banyo_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.banyo_id = banyo_id
        self.data = {}

        self.setWindowTitle("Yeni Banyo" if not banyo_id else "Banyo Duzenle")
        self.setMinimumSize(brand.sp(850), brand.sp(700))

        if banyo_id:
            self._load_data()
        self._setup_ui()

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM uretim.banyo_tanimlari WHERE id = ?", (self.banyo_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
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
            QLineEdit, QDoubleSpinBox, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border-color: {brand.PRIMARY};
            }}
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                background: {brand.BG_CARD};
                border-radius: {brand.R_LG}px;
            }}
            QTabBar::tab {{
                background: {brand.BG_INPUT};
                padding: {brand.SP_2}px {brand.SP_4}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QTabBar::tab:selected {{
                background: {brand.BG_CARD};
                border-bottom: 2px solid {brand.PRIMARY};
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

        tabs = QTabWidget()
        tabs.addTab(self._create_genel_tab(), "Genel")
        tabs.addTab(self._create_parametre_tab(), "Parametreler")
        tabs.addTab(self._create_plc_tab(), "PLC Eslestirme")

        # TDS sekmesi
        from modules.lab.lab_banyo_tds import BanyoTDSTab
        self.tds_tab = BanyoTDSTab(self.theme, self.banyo_id, parent=self)
        tabs.addTab(self.tds_tab, "TDS")

        layout.addWidget(tabs, 1)

        # -- Alt butonlar --
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(brand.sp(38))
        cancel_btn.setStyleSheet(f"""
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
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _create_genel_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        form.setSpacing(brand.SP_3)

        self.kod_input = QLineEdit(self.data.get('kod', ''))
        self.kod_input.setPlaceholderText("Orn: E-KTL-01")
        form.addRow("Kod *:", self.kod_input)

        self.ad_input = QLineEdit(self.data.get('ad', ''))
        self.ad_input.setPlaceholderText("Orn: Kataforez Banyosu 1")
        form.addRow("Ad *:", self.ad_input)

        self.hat_combo = QComboBox()
        self.hat_combo.addItem("-- Seciniz --", None)
        self._load_hatlar()
        form.addRow("Hat *:", self.hat_combo)

        self.pozisyon_combo = QComboBox()
        self.pozisyon_combo.addItem("-- Seciniz --", None)
        self.hat_combo.currentIndexChanged.connect(self._load_pozisyonlar)
        form.addRow("Pozisyon:", self.pozisyon_combo)

        self.banyo_tipi_combo = QComboBox()
        self.banyo_tipi_combo.addItem("-- Seciniz --", None)
        self._load_banyo_tipleri()
        form.addRow("Banyo Tipi *:", self.banyo_tipi_combo)

        self.hacim_input = QDoubleSpinBox()
        self.hacim_input.setRange(0, 999999)
        self.hacim_input.setSuffix(" lt")
        self.hacim_input.setValue(self.data.get('hacim_lt', 0) or 0)
        form.addRow("Hacim:", self.hacim_input)

        self.aktif_combo = QComboBox()
        self.aktif_combo.addItem("Aktif", True)
        self.aktif_combo.addItem("Pasif", False)
        self.aktif_combo.setCurrentIndex(0 if self.data.get('aktif_mi', True) else 1)
        form.addRow("Durum:", self.aktif_combo)

        return widget

    def _create_param_row(self, label, prefix, data_prefix, range_min, range_max, decimals=2):
        """Parametre satiri olustur (Min/Hedef/Max)"""
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_LG}px;"
        )
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(brand.SP_3, brand.SP_2, brand.SP_3, brand.SP_2)
        frame_layout.setSpacing(brand.SP_1)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        frame_layout.addWidget(lbl)

        grid = QHBoxLayout()
        spin_min = QDoubleSpinBox(); spin_min.setRange(range_min, range_max); spin_min.setDecimals(decimals)
        spin_min.setValue(self.data.get(f'{data_prefix}_min', 0) or 0)
        spin_hedef = QDoubleSpinBox(); spin_hedef.setRange(range_min, range_max); spin_hedef.setDecimals(decimals)
        spin_hedef.setValue(self.data.get(f'{data_prefix}_hedef', 0) or 0)
        spin_max = QDoubleSpinBox(); spin_max.setRange(range_min, range_max); spin_max.setDecimals(decimals)
        spin_max.setValue(self.data.get(f'{data_prefix}_max', 0) or 0)

        grid.addWidget(QLabel("Min:")); grid.addWidget(spin_min)
        grid.addWidget(QLabel("Hedef:")); grid.addWidget(spin_hedef)
        grid.addWidget(QLabel("Max:")); grid.addWidget(spin_max)
        frame_layout.addLayout(grid)

        setattr(self, f'{prefix}_min', spin_min)
        setattr(self, f'{prefix}_hedef', spin_hedef)
        setattr(self, f'{prefix}_max', spin_max)

        return frame

    def _create_parametre_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_2)

        # TDS'den Parametre Alma Toolbar
        tds_toolbar = QHBoxLayout()
        tds_import_btn = QPushButton("TDS'den Parametreleri Al (AI Destekli)")
        tds_import_btn.setCursor(Qt.PointingHandCursor)
        tds_import_btn.setFixedHeight(brand.sp(38))
        tds_import_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        tds_import_btn.clicked.connect(self._tds_parametre_al)
        tds_toolbar.addWidget(tds_import_btn)
        tds_toolbar.addStretch()
        layout.addLayout(tds_toolbar)

        # Parametreler
        layout.addWidget(self._create_param_row("Sicaklik (C)", "sic", "sicaklik", 0, 500, 1))
        layout.addWidget(self._create_param_row("pH", "ph", "ph", 0, 14, 2))
        layout.addWidget(self._create_param_row("Iletkenlik (mS/cm)", "iletkenlik", "iletkenlik", 0, 99999, 2))
        layout.addWidget(self._create_param_row("Kati Madde (%)", "kati_madde", "kati_madde", 0, 100, 2))
        layout.addWidget(self._create_param_row("P/B Orani", "pb_orani", "pb_orani", 0, 100, 2))
        layout.addWidget(self._create_param_row("Solvent (%)", "solvent", "solvent", 0, 100, 2))
        layout.addWidget(self._create_param_row("MEQ (meq/100g)", "meq", "meq", 0, 999, 2))
        layout.addWidget(self._create_param_row("Toplam Asit (ml)", "toplam_asit", "toplam_asit", 0, 9999, 4))
        layout.addWidget(self._create_param_row("Serbest Asit (ml)", "serbest_asit", "serbest_asit", 0, 9999, 4))

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def _create_plc_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        form.setSpacing(brand.SP_3)

        self.sql_sic_input = QLineEdit(self.data.get('sql_sicaklik_tag', '') or '')
        self.sql_sic_input.setPlaceholderText("PLC Sicaklik Tag Adi")
        form.addRow("Sicaklik Tag:", self.sql_sic_input)

        self.sql_ph_input = QLineEdit(self.data.get('sql_ph_tag', '') or '')
        self.sql_ph_input.setPlaceholderText("PLC pH Tag Adi")
        form.addRow("pH Tag:", self.sql_ph_input)

        self.sql_akim_input = QLineEdit(self.data.get('sql_akim_tag', '') or '')
        self.sql_akim_input.setPlaceholderText("PLC Akim Tag Adi")
        form.addRow("Akim Tag:", self.sql_akim_input)

        scroll.setWidget(widget)
        return scroll

    def _load_hatlar(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.uretim_hatlari WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no, kod")
            for row in cursor.fetchall():
                self.hat_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            if self.data.get('hat_id'):
                idx = self.hat_combo.findData(self.data['hat_id'])
                if idx >= 0:
                    self.hat_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_pozisyonlar(self):
        self.pozisyon_combo.clear()
        self.pozisyon_combo.addItem("-- Seciniz --", None)
        hat_id = self.hat_combo.currentData()
        if not hat_id:
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, pozisyon_no, ad FROM tanim.hat_pozisyonlar WHERE hat_id=? AND aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no", (hat_id,))
            rows = cursor.fetchall()
            for row in rows:
                label = f"Poz {row[1]}: {row[2]}"
                self.pozisyon_combo.addItem(label, row[0])
            if self.data.get('pozisyon_id'):
                idx = self.pozisyon_combo.findData(self.data['pozisyon_id'])
                if idx >= 0:
                    self.pozisyon_combo.setCurrentIndex(idx)
        except Exception as e:
            print(f"[lab_banyo] Pozisyon yuklenemedi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_banyo_tipleri(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad, kategori FROM tanim.banyo_tipleri WHERE aktif_mi=1 ORDER BY kategori, ad")
            for row in cursor.fetchall():
                self.banyo_tipi_combo.addItem(f"{row[1]} ({row[2]})", row[0])
            if self.data.get('banyo_tipi_id'):
                idx = self.banyo_tipi_combo.findData(self.data['banyo_tipi_id'])
                if idx >= 0:
                    self.banyo_tipi_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _tds_parametre_al(self):
        """TDS'den AI destekli parametre alma diyalogu ac"""
        if not self.banyo_id:
            QMessageBox.warning(self, "Uyari", "Lutfen once banyoyu kaydedin, sonra TDS'den parametre alabilirsiniz!")
            return

        dlg = TDSParametreAlDialog(self.theme, self.banyo_id, parent=self)
        if dlg.exec() == QDialog.Accepted and dlg.secilen_parametreler:
            self._parametreleri_uygula(dlg.secilen_parametreler)

    def _parametreleri_uygula(self, parametreler: list):
        """AI onerdigi parametreleri spinbox'lara uygula"""
        param_spin_map = {
            "sicaklik": "sic",
            "ph": "ph",
            "iletkenlik": "iletkenlik",
            "kati_madde": "kati_madde",
            "pb_orani": "pb_orani",
            "solvent": "solvent",
            "meq": "meq",
            "toplam_asit": "toplam_asit",
            "serbest_asit": "serbest_asit",
        }

        uygulanan = 0
        for p in parametreler:
            kod = p.get("parametre_kodu", "")
            prefix = param_spin_map.get(kod)
            if not prefix:
                continue

            min_val = p.get("onerilen_min") or p.get("tds_min") or 0
            hedef_val = p.get("onerilen_hedef") or p.get("tds_hedef") or 0
            max_val = p.get("onerilen_max") or p.get("tds_max") or 0

            min_spin = getattr(self, f'{prefix}_min', None)
            hedef_spin = getattr(self, f'{prefix}_hedef', None)
            max_spin = getattr(self, f'{prefix}_max', None)

            if min_spin and hedef_spin and max_spin:
                min_spin.setValue(float(min_val))
                hedef_spin.setValue(float(hedef_val))
                max_spin.setValue(float(max_val))
                uygulanan += 1

        QMessageBox.information(
            self, "Basarili",
            f"{uygulanan} parametre TDS'den basariyla aktarildi!\n"
            f"Kaydetmek icin 'Kaydet' butonuna basin.")

    def _spin_val(self, spin):
        """SpinBox degerini al, 0 ise None dondur"""
        v = spin.value()
        return v if v else None

    def _save(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()
        hat_id = self.hat_combo.currentData()
        banyo_tipi_id = self.banyo_tipi_combo.currentData()

        if not kod or not ad or not hat_id or not banyo_tipi_id:
            QMessageBox.warning(self, "Uyari", "Kod, Ad, Hat ve Banyo Tipi zorunludur!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            params = (
                kod, ad, hat_id, self.pozisyon_combo.currentData(), banyo_tipi_id,
                self.hacim_input.value() or None,
                # Sicaklik
                self._spin_val(self.sic_min), self._spin_val(self.sic_max), self._spin_val(self.sic_hedef),
                # pH
                self._spin_val(self.ph_min), self._spin_val(self.ph_max), self._spin_val(self.ph_hedef),
                # Iletkenlik
                self._spin_val(self.iletkenlik_min), self._spin_val(self.iletkenlik_max), self._spin_val(self.iletkenlik_hedef),
                # Kati Madde
                self._spin_val(self.kati_madde_min), self._spin_val(self.kati_madde_max), self._spin_val(self.kati_madde_hedef),
                # P/B Orani
                self._spin_val(self.pb_orani_min), self._spin_val(self.pb_orani_max), self._spin_val(self.pb_orani_hedef),
                # Solvent
                self._spin_val(self.solvent_min), self._spin_val(self.solvent_max), self._spin_val(self.solvent_hedef),
                # MEQ
                self._spin_val(self.meq_min), self._spin_val(self.meq_max), self._spin_val(self.meq_hedef),
                # Toplam Asit
                self._spin_val(self.toplam_asit_min), self._spin_val(self.toplam_asit_max), self._spin_val(self.toplam_asit_hedef),
                # Serbest Asit
                self._spin_val(self.serbest_asit_min), self._spin_val(self.serbest_asit_max), self._spin_val(self.serbest_asit_hedef),
                # PLC Tags
                self.sql_sic_input.text().strip() or None,
                self.sql_ph_input.text().strip() or None,
                self.sql_akim_input.text().strip() or None,
                # Durum
                self.aktif_combo.currentData()
            )

            if self.banyo_id:
                cursor.execute("""UPDATE uretim.banyo_tanimlari SET
                    kod=?, ad=?, hat_id=?, pozisyon_id=?, banyo_tipi_id=?, hacim_lt=?,
                    sicaklik_min=?, sicaklik_max=?, sicaklik_hedef=?,
                    ph_min=?, ph_max=?, ph_hedef=?,
                    iletkenlik_min=?, iletkenlik_max=?, iletkenlik_hedef=?,
                    kati_madde_min=?, kati_madde_max=?, kati_madde_hedef=?,
                    pb_orani_min=?, pb_orani_max=?, pb_orani_hedef=?,
                    solvent_min=?, solvent_max=?, solvent_hedef=?,
                    meq_min=?, meq_max=?, meq_hedef=?,
                    toplam_asit_min=?, toplam_asit_max=?, toplam_asit_hedef=?,
                    serbest_asit_min=?, serbest_asit_max=?, serbest_asit_hedef=?,
                    sql_sicaklik_tag=?, sql_ph_tag=?, sql_akim_tag=?,
                    aktif_mi=?, guncelleme_tarihi=GETDATE()
                    WHERE id=?""", params + (self.banyo_id,))
            else:
                cursor.execute("""INSERT INTO uretim.banyo_tanimlari (
                    kod, ad, hat_id, pozisyon_id, banyo_tipi_id, hacim_lt,
                    sicaklik_min, sicaklik_max, sicaklik_hedef,
                    ph_min, ph_max, ph_hedef,
                    iletkenlik_min, iletkenlik_max, iletkenlik_hedef,
                    kati_madde_min, kati_madde_max, kati_madde_hedef,
                    pb_orani_min, pb_orani_max, pb_orani_hedef,
                    solvent_min, solvent_max, solvent_hedef,
                    meq_min, meq_max, meq_hedef,
                    toplam_asit_min, toplam_asit_max, toplam_asit_hedef,
                    serbest_asit_min, serbest_asit_max, serbest_asit_hedef,
                    sql_sicaklik_tag, sql_ph_tag, sql_akim_tag,
                    aktif_mi)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", params)

            # Yeni kayitta olusan ID'yi al
            if not self.banyo_id:
                cursor.execute("SELECT SCOPE_IDENTITY()")
                new_id = cursor.fetchone()
                if new_id and new_id[0]:
                    self.banyo_id = int(new_id[0])

            conn.commit()
            LogManager.log_insert('lab', 'uretim.banyo_tanimlari', None, 'Yeni kayit eklendi')

            # TDS tab'a banyo_id ilet (yeni kayit sonrasi)
            if hasattr(self, 'tds_tab') and self.banyo_id:
                self.tds_tab.set_banyo_id(self.banyo_id)

            QMessageBox.information(self, "Basarili", "Kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class TDSParametreAlDialog(QDialog):
    """TDS'den AI destekli parametre alma diyalogu — el kitabi uyumlu"""

    def __init__(self, theme: dict, banyo_id: int, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.banyo_id = banyo_id
        self.secilen_parametreler = []
        self.ai_sonuc = None

        self.setWindowTitle("TDS'den Parametre Al - AI Destekli")
        self.setMinimumSize(brand.sp(1000), brand.sp(700))
        self._setup_ui()
        self._load_tds_listesi()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QComboBox, QTextEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
                border-color: {brand.PRIMARY};
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_4)

        # Header
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)

        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        title = QLabel("TDS'den Kontrol Parametreleri Al")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(title)

        desc = QLabel("TDS'deki parametreleri AI analizi ile optimize ederek banyo kartina aktarin.")
        desc.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        title_col.addWidget(desc)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)

        # TDS Secim
        tds_bar = QHBoxLayout()
        tds_bar.addWidget(QLabel("TDS Kaydi:"))
        self.tds_combo = QComboBox()
        self.tds_combo.setMinimumWidth(brand.sp(350))
        self.tds_combo.currentIndexChanged.connect(self._on_tds_changed)
        tds_bar.addWidget(self.tds_combo, 1)

        self.analiz_btn = QPushButton("AI Analiz Baslat")
        self.analiz_btn.setCursor(Qt.PointingHandCursor)
        self.analiz_btn.setFixedHeight(brand.sp(38))
        self.analiz_btn.setStyleSheet(f"""
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
        self.analiz_btn.clicked.connect(self._ai_analiz_baslat)
        self.analiz_btn.setEnabled(False)
        tds_bar.addWidget(self.analiz_btn)
        layout.addLayout(tds_bar)

        # Durum gostergesi
        self.durum_label = QLabel("")
        self.durum_label.setStyleSheet(f"color: {brand.TEXT_DIM}; font-style: italic;")
        layout.addWidget(self.durum_label)

        # Parametre Tablosu
        param_group = QGroupBox("Parametre Karsilastirma ve AI Onerileri")
        param_layout = QVBoxLayout(param_group)

        self.param_table = QTableWidget()
        self.param_table.setColumnCount(11)
        self.param_table.setHorizontalHeaderLabels([
            "Parametre", "Birim",
            "TDS Min", "TDS Hedef", "TDS Max",
            "Gercek", "Trend",
            "AI Min", "AI Hedef", "AI Max",
            "Durum"
        ])
        self.param_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.param_table.setColumnWidth(1, brand.sp(65))
        self.param_table.setColumnWidth(2, brand.sp(70))
        self.param_table.setColumnWidth(3, brand.sp(75))
        self.param_table.setColumnWidth(4, brand.sp(70))
        self.param_table.setColumnWidth(5, brand.sp(70))
        self.param_table.setColumnWidth(6, brand.sp(70))
        self.param_table.setColumnWidth(7, brand.sp(70))
        self.param_table.setColumnWidth(8, brand.sp(120))
        self.param_table.setColumnWidth(9, brand.sp(70))
        self.param_table.setColumnWidth(10, brand.sp(70))
        self.param_table.verticalHeader().setVisible(False)
        self.param_table.setShowGrid(False)
        self.param_table.setAlternatingRowColors(True)
        self.param_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.param_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.param_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.param_table.setStyleSheet(f"""
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
        param_layout.addWidget(self.param_table)
        layout.addWidget(param_group, 1)

        # AI Yorum Paneli
        ai_group = QGroupBox("AI Degerlendirme")
        ai_layout = QVBoxLayout(ai_group)
        self.ai_yorum_text = QTextEdit()
        self.ai_yorum_text.setReadOnly(True)
        self.ai_yorum_text.setMaximumHeight(brand.sp(120))
        self.ai_yorum_text.setStyleSheet(f"""
            QTextEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_MD}px;
                color: {brand.TEXT};
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QTextEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.ai_yorum_text.setPlaceholderText("AI analizi baslatildiginda degerlendirme burada gosterilecek...")
        ai_layout.addWidget(self.ai_yorum_text)
        layout.addWidget(ai_group)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)

        self.mod_label = QLabel("Uygulama modu:")
        self.mod_label.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        btn_layout.addWidget(self.mod_label)

        self.mod_combo = QComboBox()
        self.mod_combo.addItem("AI Onerisi (Optimize)", "ai")
        self.mod_combo.addItem("TDS Degerleri (Orijinal)", "tds")
        self.mod_combo.setMinimumWidth(brand.sp(200))
        btn_layout.addWidget(self.mod_combo)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(brand.sp(38))
        cancel_btn.setStyleSheet(f"""
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
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.uygula_btn = QPushButton("Parametreleri Uygula")
        self.uygula_btn.setCursor(Qt.PointingHandCursor)
        self.uygula_btn.setFixedHeight(brand.sp(38))
        self.uygula_btn.setStyleSheet(f"""
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
        self.uygula_btn.clicked.connect(self._uygula)
        self.uygula_btn.setEnabled(False)
        btn_layout.addWidget(self.uygula_btn)
        layout.addLayout(btn_layout)

    def _load_tds_listesi(self):
        """Banyoya ait TDS kayitlarini yukle"""
        self.tds_combo.clear()
        self.tds_combo.addItem("-- TDS Seciniz --", None)
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, tds_kodu, tds_adi, versiyon, tedarikci
                FROM uretim.banyo_tds
                WHERE banyo_id = ? AND aktif_mi = 1
                ORDER BY tds_kodu
            """, (self.banyo_id,))
            for row in cursor.fetchall():
                label = f"{row[1]} - {row[2]} (v{row[3]})"
                if row[4]:
                    label += f" [{row[4]}]"
                self.tds_combo.addItem(label, row[0])

            if self.tds_combo.count() <= 1:
                self.durum_label.setText("Bu banyo icin tanimli TDS kaydi bulunamadi.")
                self.durum_label.setStyleSheet(f"color: {brand.WARNING}; font-style: italic;")
        except Exception as e:
            self.durum_label.setText(f"TDS listesi yuklenemedi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _on_tds_changed(self):
        """TDS secimi degistiginde"""
        tds_id = self.tds_combo.currentData()
        if tds_id:
            self.analiz_btn.setEnabled(True)
            self._load_tds_parametreleri(tds_id)
        else:
            self.analiz_btn.setEnabled(False)
            self.param_table.setRowCount(0)

    def _load_tds_parametreleri(self, tds_id: int):
        """Secilen TDS'in parametrelerini tabloya yukle (sadece TDS degerleri)"""
        self.param_table.setRowCount(0)
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT parametre_kodu, parametre_adi, birim,
                       tds_min, tds_hedef, tds_max, tolerans_yuzde
                FROM uretim.banyo_tds_parametreler
                WHERE tds_id = ?
                ORDER BY sira_no, parametre_kodu
            """, (tds_id,))
            rows = cursor.fetchall()

            self.param_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.param_table.setItem(i, 0, QTableWidgetItem(row[1] or row[0]))
                self.param_table.setItem(i, 1, QTableWidgetItem(row[2] or ''))

                item0 = self.param_table.item(i, 0)
                item0.setData(Qt.UserRole, row[0])

                self.param_table.setItem(i, 2, QTableWidgetItem(f"{row[3]:.2f}" if row[3] else '-'))
                self.param_table.setItem(i, 3, QTableWidgetItem(f"{row[4]:.2f}" if row[4] else '-'))
                self.param_table.setItem(i, 4, QTableWidgetItem(f"{row[5]:.2f}" if row[5] else '-'))

                for col in range(5, 11):
                    self.param_table.setItem(i, col, QTableWidgetItem("-"))

            self.uygula_btn.setEnabled(len(rows) > 0)
            self.durum_label.setText(f"{len(rows)} parametre yuklendi. AI analizi icin butona basin.")
            self.durum_label.setStyleSheet(f"color: {brand.TEXT_DIM}; font-style: italic;")

        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Parametreler yuklenemedi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _ai_analiz_baslat(self):
        """AI destekli parametre optimizasyonu baslat"""
        tds_id = self.tds_combo.currentData()
        if not tds_id:
            return

        self.durum_label.setText("AI analizi calisiyor...")
        self.durum_label.setStyleSheet(
            f"color: {brand.PRIMARY}; font-style: italic; "
            f"font-weight: {brand.FW_SEMIBOLD};")
        self.analiz_btn.setEnabled(False)

        conn = None
        try:
            from core.ai_analiz_service import AIAnalizService

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT parametre_kodu, parametre_adi, birim,
                       tds_min, tds_hedef, tds_max, tolerans_yuzde
                FROM uretim.banyo_tds_parametreler
                WHERE tds_id = ?
                ORDER BY sira_no
            """, (tds_id,))
            tds_params = []
            for row in cursor.fetchall():
                tds_params.append({
                    "parametre_kodu": row[0],
                    "parametre_adi": row[1] or row[0],
                    "birim": row[2] or "",
                    "tds_min": float(row[3]) if row[3] else 0,
                    "tds_hedef": float(row[4]) if row[4] else 0,
                    "tds_max": float(row[5]) if row[5] else 0,
                    "tolerans_yuzde": float(row[6]) if row[6] else 10.0,
                })

            # Son olcumler
            son_olcumler = {}
            cursor.execute("""
                SELECT TOP 1 sicaklik, ph, iletkenlik, kati_madde_yuzde, pb_orani,
                       solvent_yuzde, meq_degeri, toplam_asitlik, serbest_asitlik
                FROM uretim.banyo_analiz_sonuclari
                WHERE banyo_id = ?
                ORDER BY tarih DESC
            """, (self.banyo_id,))
            row = cursor.fetchone()
            if row:
                kolon_map = {
                    "sicaklik": "sicaklik", "ph": "ph", "iletkenlik": "iletkenlik",
                    "kati_madde_yuzde": "kati_madde", "pb_orani": "pb_orani",
                    "solvent_yuzde": "solvent", "meq_degeri": "meq",
                    "toplam_asitlik": "toplam_asit", "serbest_asitlik": "serbest_asit",
                }
                cols = [d[0] for d in cursor.description]
                for col, val in zip(cols, row):
                    if val is not None:
                        kod = kolon_map.get(col, col)
                        son_olcumler[kod] = float(val)

            # Veri serisi (30 gun)
            veri_serisi = []
            cursor.execute("""
                SELECT tarih, sicaklik, ph, iletkenlik, kati_madde_yuzde, pb_orani,
                       solvent_yuzde, meq_degeri, toplam_asitlik, serbest_asitlik
                FROM uretim.banyo_analiz_sonuclari
                WHERE banyo_id = ? AND tarih >= DATEADD(DAY, -30, GETDATE())
                ORDER BY tarih ASC
            """, (self.banyo_id,))
            for row in cursor.fetchall():
                param_map = {
                    "sicaklik": row[1], "ph": row[2], "iletkenlik": row[3],
                    "kati_madde": row[4], "pb_orani": row[5], "solvent": row[6],
                    "meq": row[7], "toplam_asit": row[8], "serbest_asit": row[9],
                }
                for param, deger in param_map.items():
                    if deger is not None:
                        veri_serisi.append({"parametre": param, "tarih": row[0], "deger": float(deger)})

            # AI analiz calistir
            service = AIAnalizService()
            self.ai_sonuc = service.parametre_optimizasyonu(
                self.banyo_id, tds_params, son_olcumler, veri_serisi)

            # Tabloyu guncelle
            self._tabloyu_guncelle(self.ai_sonuc.get("parametreler", []))

            # AI yorum
            ai_yorum = self.ai_sonuc.get("ai_yorum")
            if ai_yorum:
                self.ai_yorum_text.setPlainText(ai_yorum)
            else:
                ozet_satirlari = []
                for p in self.ai_sonuc.get("parametreler", []):
                    if p.get("aciklama"):
                        ozet_satirlari.append(f"- {p['parametre_adi']}: {p['aciklama']}")
                if ozet_satirlari:
                    self.ai_yorum_text.setPlainText(
                        "Kural Tabanli AI Degerlendirmesi:\n\n" + "\n".join(ozet_satirlari))
                else:
                    self.ai_yorum_text.setPlainText("Tum parametreler TDS hedeflerine uygun durumda.")

            # Durum
            kritik = sum(1 for p in self.ai_sonuc.get("parametreler", []) if p.get("durum") == "KRITIK")
            uyari = sum(1 for p in self.ai_sonuc.get("parametreler", []) if p.get("durum") == "UYARI")
            normal = sum(1 for p in self.ai_sonuc.get("parametreler", []) if p.get("durum") == "NORMAL")

            if kritik > 0:
                durum_txt = f"AI analizi tamamlandi - {kritik} KRITIK, {uyari} UYARI, {normal} NORMAL"
                self.durum_label.setStyleSheet(f"color: {brand.ERROR}; font-weight: {brand.FW_SEMIBOLD};")
            elif uyari > 0:
                durum_txt = f"AI analizi tamamlandi - {uyari} UYARI, {normal} NORMAL"
                self.durum_label.setStyleSheet(f"color: {brand.WARNING}; font-weight: {brand.FW_SEMIBOLD};")
            else:
                durum_txt = f"AI analizi tamamlandi - Tum parametreler uygun"
                self.durum_label.setStyleSheet(f"color: {brand.SUCCESS}; font-weight: {brand.FW_SEMIBOLD};")
            self.durum_label.setText(durum_txt)

        except Exception as e:
            QMessageBox.critical(self, "AI Analiz Hatasi", str(e))
            self.durum_label.setText(f"Hata: {e}")
            self.durum_label.setStyleSheet(f"color: {brand.ERROR}; font-style: italic;")
        finally:
            self.analiz_btn.setEnabled(True)
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _tabloyu_guncelle(self, parametreler: list):
        """AI sonuclariyla tabloyu guncelle"""
        self.param_table.setRowCount(len(parametreler))

        durum_renk = {
            "NORMAL": brand.SUCCESS,
            "UYARI": brand.WARNING,
            "KRITIK": brand.ERROR,
            "BILGI_YOK": brand.TEXT_DIM,
        }
        trend_ikon = {
            "artan": "Artan",
            "azalan": "Azalan",
            "stabil": "Stabil",
            "veri_yok": "Veri Yok",
        }

        for i, p in enumerate(parametreler):
            item0 = QTableWidgetItem(p.get("parametre_adi", ""))
            item0.setData(Qt.UserRole, p.get("parametre_kodu", ""))
            self.param_table.setItem(i, 0, item0)

            self.param_table.setItem(i, 1, QTableWidgetItem(p.get("birim", "")))

            self.param_table.setItem(i, 2, QTableWidgetItem(
                f"{p['tds_min']:.2f}" if p.get('tds_min') else '-'))
            self.param_table.setItem(i, 3, QTableWidgetItem(
                f"{p['tds_hedef']:.2f}" if p.get('tds_hedef') else '-'))
            self.param_table.setItem(i, 4, QTableWidgetItem(
                f"{p['tds_max']:.2f}" if p.get('tds_max') else '-'))

            gercek_item = QTableWidgetItem(
                f"{p['gercek']:.2f}" if p.get('gercek') is not None else '-')
            self.param_table.setItem(i, 5, gercek_item)

            trend = p.get("trend", "veri_yok")
            trend_item = QTableWidgetItem(trend_ikon.get(trend, trend))
            if trend == "artan":
                trend_item.setForeground(QColor(brand.WARNING))
            elif trend == "azalan":
                trend_item.setForeground(QColor(brand.INFO))
            elif trend == "stabil":
                trend_item.setForeground(QColor(brand.SUCCESS))
            self.param_table.setItem(i, 6, trend_item)

            ai_min_item = QTableWidgetItem(
                f"{p['onerilen_min']:.2f}" if p.get('onerilen_min') else '-')
            ai_min_item.setForeground(QColor("#8B5CF6"))
            self.param_table.setItem(i, 7, ai_min_item)

            ai_hedef_item = QTableWidgetItem(
                f"{p['onerilen_hedef']:.2f}" if p.get('onerilen_hedef') else '-')
            ai_hedef_item.setForeground(QColor("#8B5CF6"))
            self.param_table.setItem(i, 8, ai_hedef_item)

            ai_max_item = QTableWidgetItem(
                f"{p['onerilen_max']:.2f}" if p.get('onerilen_max') else '-')
            ai_max_item.setForeground(QColor("#8B5CF6"))
            self.param_table.setItem(i, 9, ai_max_item)

            durum = p.get("durum", "BILGI_YOK")
            durum_item = QTableWidgetItem(durum)
            durum_item.setForeground(QColor(durum_renk.get(durum, brand.TEXT)))
            self.param_table.setItem(i, 10, durum_item)

    def _uygula(self):
        """Secilen parametreleri banyo kartina aktar"""
        mod = self.mod_combo.currentData()

        if self.ai_sonuc and mod == "ai":
            self.secilen_parametreler = self.ai_sonuc.get("parametreler", [])
        else:
            self.secilen_parametreler = []
            for i in range(self.param_table.rowCount()):
                item0 = self.param_table.item(i, 0)
                if not item0:
                    continue
                kod = item0.data(Qt.UserRole) or ""

                def safe_float(item):
                    if not item:
                        return 0
                    txt = item.text().strip().replace('-', '')
                    try:
                        return float(txt)
                    except (ValueError, AttributeError):
                        return 0

                self.secilen_parametreler.append({
                    "parametre_kodu": kod,
                    "parametre_adi": item0.text(),
                    "tds_min": safe_float(self.param_table.item(i, 2)),
                    "tds_hedef": safe_float(self.param_table.item(i, 3)),
                    "tds_max": safe_float(self.param_table.item(i, 4)),
                    "onerilen_min": safe_float(self.param_table.item(i, 2)),
                    "onerilen_hedef": safe_float(self.param_table.item(i, 3)),
                    "onerilen_max": safe_float(self.param_table.item(i, 4)),
                })

        if not self.secilen_parametreler:
            QMessageBox.warning(self, "Uyari", "Uygulanacak parametre bulunamadi!")
            return

        mod_text = "AI Optimize" if mod == "ai" else "TDS Orijinal"
        if QMessageBox.question(
                self, "Onay",
                f"{len(self.secilen_parametreler)} parametre '{mod_text}' modunda uygulanacak.\n\n"
                f"Mevcut parametre degerleri degistirilecek.\nDevam etmek istiyor musunuz?") == QMessageBox.Yes:
            self.accept()


class LabBanyoPage(BasePage):
    """Banyo Tanimlari Listesi — el kitabi uyumlu sayfa"""

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
            "Banyo Tanimlari",
            "Uretim hatti banyo tanimlari ve parametreleri"
        )
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        header.addWidget(self.stat_label)

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        header.addWidget(btn_yenile)

        layout.addLayout(header)

        # -- 2. Toolbar --
        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara...")
        self.search_input.setStyleSheet(f"""
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
        self.search_input.setMaximumWidth(brand.sp(200))
        self.search_input.returnPressed.connect(self._load_data)
        toolbar.addWidget(self.search_input)

        self.hat_combo = QComboBox()
        self.hat_combo.addItem("Tum Hatlar", None)
        self._load_hat_filter()
        self.hat_combo.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
                min-width: {brand.sp(120)}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.hat_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.hat_combo)
        toolbar.addStretch()

        add_btn = QPushButton("Yeni Banyo")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(brand.sp(38))
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_new)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        # -- 3. Tablo --
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Hat", "Tip", "Hacim", "Sicaklik", "pH", "Islem"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, brand.sp(60))
        self.table.setColumnWidth(1, brand.sp(100))
        self.table.setColumnWidth(3, brand.sp(100))
        self.table.setColumnWidth(4, brand.sp(100))
        self.table.setColumnWidth(5, brand.sp(80))
        self.table.setColumnWidth(6, brand.sp(80))
        self.table.setColumnWidth(7, brand.sp(60))
        self.table.setColumnWidth(8, brand.sp(120))
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
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

    def _load_hat_filter(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod FROM tanim.uretim_hatlari WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no")
            for row in cursor.fetchall():
                self.hat_combo.addItem(row[1], row[0])
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
            cursor = conn.cursor()

            sql = """SELECT b.id, b.kod, b.ad, h.kod, bt.ad, b.hacim_lt, b.sicaklik_hedef, b.ph_hedef
                     FROM uretim.banyo_tanimlari b
                     JOIN tanim.uretim_hatlari h ON b.hat_id=h.id
                     JOIN tanim.banyo_tipleri bt ON b.banyo_tipi_id=bt.id
                     WHERE b.aktif_mi=1"""
            params = []

            search = self.search_input.text().strip()
            if search:
                sql += " AND (b.kod LIKE ? OR b.ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            hat_id = self.hat_combo.currentData()
            if hat_id:
                sql += " AND b.hat_id=?"
                params.append(hat_id)

            sql += " ORDER BY h.sira_no, b.kod"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or ''))
                self.table.setItem(i, 4, QTableWidgetItem(row[4] or ''))
                self.table.setItem(i, 5, QTableWidgetItem(f"{row[5]:.0f}" if row[5] else '-'))
                self.table.setItem(i, 6, QTableWidgetItem(f"{row[6]:.0f} C" if row[6] else '-'))
                self.table.setItem(i, 7, QTableWidgetItem(f"{row[7]:.1f}" if row[7] else '-'))

                widget = self.create_action_buttons([
                    ("Duzenle", "Duzenle", lambda checked, rid=row[0]: self._edit_item(rid), "edit"),
                    ("Sil", "Sil", lambda checked, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 8, widget)

            self.stat_label.setText(f"Toplam: {len(rows)} banyo")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _add_new(self):
        dlg = BanyoDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _edit_item(self, bid):
        dlg = BanyoDialog(self.theme, bid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _delete_item(self, bid):
        if QMessageBox.question(self, "Onay", "Bu banyoyu silmek istediginize emin misiniz?") == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM uretim.banyo_tanimlari WHERE id=?", (bid,))
                conn.commit()
                LogManager.log_delete('lab', 'uretim.banyo_tanimlari', None, 'Kayit silindi')
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
