# -*- coding: utf-8 -*-
"""
NEXOR ERP - Banyo TDS (Technical Data Sheet) Modulu
=====================================================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive

BanyoTDSTab: Ana TDS sekmesi
TDSDialog: TDS tanimlama/duzenleme
TDSAIAnalizPanel: AI destekli analiz paneli
"""

import os
import json
import shutil
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QComboBox, QTabWidget, QDateEdit, QTextEdit, QCheckBox,
    QFileDialog, QGroupBox, QGridLayout, QSpinBox, QScrollArea
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from core.database import get_db_connection
from config import NAS_PATHS
from core.nexor_brand import brand

# Matplotlib opsiyonel
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

NAS_TDS_PATH = NAS_PATHS.get("tds_path", "")

# Standart parametre on tanimlari
STANDART_PARAMETRELER = [
    {"kodu": "sicaklik", "adi": "Sicaklik", "birim": "C", "sira": 1},
    {"kodu": "ph", "adi": "pH", "birim": "", "sira": 2},
    {"kodu": "iletkenlik", "adi": "Iletkenlik", "birim": "mS/cm", "sira": 3},
    {"kodu": "kati_madde", "adi": "Kati Madde", "birim": "%", "sira": 4},
    {"kodu": "pb_orani", "adi": "P/B Orani", "birim": "", "sira": 5},
    {"kodu": "solvent", "adi": "Solvent", "birim": "%", "sira": 6},
    {"kodu": "meq", "adi": "MEQ", "birim": "meq/100g", "sira": 7},
    {"kodu": "toplam_asit", "adi": "Toplam Asit", "birim": "ml", "sira": 8},
    {"kodu": "serbest_asit", "adi": "Serbest Asit", "birim": "ml", "sira": 9},
]


# ============================================================
# ORTAK STIL YARDIMCILARI
# ============================================================

def _table_style():
    """Standart el-kitabi tablo stili"""
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


def _group_style():
    """Standart el-kitabi GroupBox stili"""
    return (
        f"QGroupBox {{ color: {brand.TEXT}; "
        f"font-size: {brand.FS_BODY}px; "
        f"font-weight: {brand.FW_SEMIBOLD}; "
        f"border: 1px solid {brand.BORDER}; "
        f"border-radius: {brand.R_LG}px; "
        f"margin-top: {brand.SP_5}px; "
        f"padding: {brand.SP_5}px; "
        f"padding-top: {brand.SP_8}px; "
        f"background: {brand.BG_CARD}; }}"
        f"QGroupBox::title {{ subcontrol-origin: margin; "
        f"left: {brand.SP_4}px; "
        f"top: {brand.SP_2}px; "
        f"padding: 0 {brand.SP_2}px; "
        f"color: {brand.TEXT_MUTED}; "
        f"background: {brand.BG_CARD}; }}"
    )


def _btn_primary(text: str) -> QPushButton:
    """Birincil aksiyon butonu olustur"""
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(brand.sp(38))
    btn.setStyleSheet(f"""
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
    return btn


def _btn_secondary(text: str) -> QPushButton:
    """Ikincil aksiyon butonu olustur"""
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(brand.sp(38))
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {brand.BG_CARD};
            color: {brand.TEXT};
            border: 1px solid {brand.BORDER};
            border-radius: {brand.R_SM}px;
            padding: 0 {brand.SP_4}px;
            font-size: {brand.FS_BODY}px;
            font-weight: {brand.FW_MEDIUM};
        }}
        QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
    """)
    return btn


def _btn_success(text: str) -> QPushButton:
    """Basari/kaydet butonu olustur"""
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(brand.sp(38))
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {brand.SUCCESS};
            color: white;
            border: none;
            border-radius: {brand.R_SM}px;
            padding: 0 {brand.SP_4}px;
            font-size: {brand.FS_BODY}px;
            font-weight: {brand.FW_SEMIBOLD};
        }}
        QPushButton:hover {{ background: #059669; }}
    """)
    return btn


def _setup_table(table: QTableWidget):
    """Ortak tablo ayarlari"""
    table.verticalHeader().setVisible(False)
    table.setShowGrid(False)
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.verticalHeader().setDefaultSectionSize(brand.sp(42))
    table.setStyleSheet(_table_style())


# ============================================================
# TDS DIALOG - TDS Tanimlama/Duzenleme
# ============================================================

class TDSDialog(QDialog):
    """Yeni TDS tanimlama veya mevcut TDS duzenleme — el kitabi uyumlu"""

    def __init__(self, theme: dict, banyo_id: int, tds_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.banyo_id = banyo_id
        self.tds_id = tds_id
        self.data = {}

        self.setWindowTitle("Yeni TDS" if not tds_id else "TDS Duzenle")
        self.setMinimumSize(brand.sp(500), brand.sp(400))

        if tds_id:
            self._load_data()
        self._setup_ui()

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM uretim.banyo_tds WHERE id = ?", (self.tds_id,))
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
            QLineEdit, QComboBox, QDateEdit, QTextEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{
                border-color: {brand.PRIMARY};
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

        title = QLabel(self.windowTitle())
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        form = QFormLayout()
        form.setSpacing(brand.SP_3)

        self.kod_input = QLineEdit(self.data.get('tds_kodu', ''))
        self.kod_input.setPlaceholderText("Orn: TDS-KTL-001")
        form.addRow("TDS Kodu *:", self.kod_input)

        self.adi_input = QLineEdit(self.data.get('tds_adi', ''))
        self.adi_input.setPlaceholderText("Orn: Cathoguard 500 TDS v3.2")
        form.addRow("TDS Adi *:", self.adi_input)

        self.versiyon_input = QLineEdit(self.data.get('versiyon', '1.0'))
        form.addRow("Versiyon:", self.versiyon_input)

        self.tedarikci_input = QLineEdit(self.data.get('tedarikci', ''))
        self.tedarikci_input.setPlaceholderText("Orn: BASF, PPG, Axalta")
        form.addRow("Tedarikci:", self.tedarikci_input)

        self.baslangic_date = QDateEdit()
        self.baslangic_date.setCalendarPopup(True)
        self.baslangic_date.setDisplayFormat("dd.MM.yyyy")
        if self.data.get('gecerlilik_baslangic'):
            self.baslangic_date.setDate(QDate(
                self.data['gecerlilik_baslangic'].year,
                self.data['gecerlilik_baslangic'].month,
                self.data['gecerlilik_baslangic'].day))
        else:
            self.baslangic_date.setDate(QDate.currentDate())
        form.addRow("Gecerlilik Baslangic:", self.baslangic_date)

        self.bitis_date = QDateEdit()
        self.bitis_date.setCalendarPopup(True)
        self.bitis_date.setDisplayFormat("dd.MM.yyyy")
        if self.data.get('gecerlilik_bitis'):
            self.bitis_date.setDate(QDate(
                self.data['gecerlilik_bitis'].year,
                self.data['gecerlilik_bitis'].month,
                self.data['gecerlilik_bitis'].day))
        else:
            self.bitis_date.setDate(QDate.currentDate().addYears(2))
        form.addRow("Gecerlilik Bitis:", self.bitis_date)

        self.notlar_input = QTextEdit()
        self.notlar_input.setMaximumHeight(brand.sp(80))
        self.notlar_input.setPlainText(self.data.get('notlar', '') or '')
        form.addRow("Notlar:", self.notlar_input)

        layout.addLayout(form)
        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        cancel_btn = _btn_secondary("Iptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = _btn_primary("Kaydet")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _save(self):
        kod = self.kod_input.text().strip()
        adi = self.adi_input.text().strip()
        if not kod or not adi:
            QMessageBox.warning(self, "Uyari", "TDS Kodu ve Adi zorunludur!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            params = (
                self.banyo_id, kod, adi,
                self.versiyon_input.text().strip() or '1.0',
                self.baslangic_date.date().toPython(),
                self.bitis_date.date().toPython(),
                self.tedarikci_input.text().strip() or None,
                self.notlar_input.toPlainText().strip() or None,
            )

            if self.tds_id:
                cursor.execute("""UPDATE uretim.banyo_tds SET
                    banyo_id=?, tds_kodu=?, tds_adi=?, versiyon=?,
                    gecerlilik_baslangic=?, gecerlilik_bitis=?,
                    tedarikci=?, notlar=?, guncelleme_tarihi=GETDATE()
                    WHERE id=?""", params + (self.tds_id,))
            else:
                cursor.execute("""INSERT INTO uretim.banyo_tds
                    (banyo_id, tds_kodu, tds_adi, versiyon,
                     gecerlilik_baslangic, gecerlilik_bitis,
                     tedarikci, notlar)
                    VALUES (?,?,?,?,?,?,?,?)""", params)

            conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# ============================================================
# AI ANALIZ PANELI
# ============================================================

class TDSAIAnalizPanel(QWidget):
    """AI destekli analiz paneli - 4 analiz karti (2x2 grid) — el kitabi uyumlu"""

    def __init__(self, theme: dict, banyo_id: int, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.banyo_id = banyo_id
        self.tds_id = None
        self.tds_parametreler = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_2, brand.SP_2, brand.SP_2, brand.SP_2)
        layout.setSpacing(brand.SP_2)

        # Basla butonu
        top_bar = QHBoxLayout()
        top_bar.setSpacing(brand.SP_3)

        self.analiz_btn = _btn_primary("Analiz Baslat")
        self.analiz_btn.clicked.connect(self._run_analiz)
        top_bar.addWidget(self.analiz_btn)

        self.risk_label = QLabel("")
        self.risk_label.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_BODY_LG}px;"
        )
        top_bar.addWidget(self.risk_label)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # 2x2 Grid
        grid = QGridLayout()
        grid.setSpacing(brand.SP_2)

        # Kart 1: Karsilastirma
        self.karsilastirma_group = QGroupBox("Karsilastirma: TDS Hedef vs Son Olcum")
        self.karsilastirma_group.setStyleSheet(_group_style())
        k_layout = QVBoxLayout(self.karsilastirma_group)
        self.karsilastirma_table = QTableWidget()
        self.karsilastirma_table.setColumnCount(6)
        self.karsilastirma_table.setHorizontalHeaderLabels(["Parametre", "Hedef", "Gercek", "Sapma", "Sapma%", "Durum"])
        self.karsilastirma_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        _setup_table(self.karsilastirma_table)
        self.karsilastirma_table.setMaximumHeight(brand.sp(200))
        k_layout.addWidget(self.karsilastirma_table)
        grid.addWidget(self.karsilastirma_group, 0, 0)

        # Kart 2: Trend Analizi
        self.trend_group = QGroupBox("Trend Analizi (Son 30 Gun)")
        self.trend_group.setStyleSheet(_group_style())
        t_layout = QVBoxLayout(self.trend_group)
        if MATPLOTLIB_AVAILABLE:
            self.trend_figure = Figure(figsize=(4, 2.5), dpi=80)
            self.trend_figure.patch.set_facecolor('#1a1a2e')
            self.trend_canvas = FigureCanvas(self.trend_figure)
            self.trend_canvas.setMaximumHeight(brand.sp(200))
            t_layout.addWidget(self.trend_canvas)
        else:
            self.trend_table = QTableWidget()
            self.trend_table.setColumnCount(5)
            self.trend_table.setHorizontalHeaderLabels(["Parametre", "Son Deger", "Ortalama", "Egim", "Yorum"])
            self.trend_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            _setup_table(self.trend_table)
            self.trend_table.setMaximumHeight(brand.sp(200))
            t_layout.addWidget(self.trend_table)
        grid.addWidget(self.trend_group, 0, 1)

        # Kart 3: Tahmin
        self.tahmin_group = QGroupBox("7 Gunluk Tahmin")
        self.tahmin_group.setStyleSheet(_group_style())
        th_layout = QVBoxLayout(self.tahmin_group)
        self.tahmin_table = QTableWidget()
        self.tahmin_table.setColumnCount(5)
        self.tahmin_table.setHorizontalHeaderLabels(["Parametre", "Mevcut", "7 Gun Tahmini", "Limitler", "Risk"])
        self.tahmin_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        _setup_table(self.tahmin_table)
        self.tahmin_table.setMaximumHeight(brand.sp(200))
        th_layout.addWidget(self.tahmin_table)
        grid.addWidget(self.tahmin_group, 1, 0)

        # Kart 4: Takviye Onerileri
        self.takviye_group = QGroupBox("Kimyasal Takviye Onerileri")
        self.takviye_group.setStyleSheet(_group_style())
        tv_layout = QVBoxLayout(self.takviye_group)
        self.takviye_table = QTableWidget()
        self.takviye_table.setColumnCount(5)
        self.takviye_table.setHorizontalHeaderLabels(["Kimyasal", "Miktar", "Birim", "Oncelik", "Aciklama"])
        self.takviye_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        _setup_table(self.takviye_table)
        self.takviye_table.setMaximumHeight(brand.sp(200))
        tv_layout.addWidget(self.takviye_table)

        self.takviye_olustur_btn = _btn_success("Takviye Olustur")
        self.takviye_olustur_btn.setEnabled(False)
        self.takviye_olustur_btn.clicked.connect(self._takviye_olustur)
        tv_layout.addWidget(self.takviye_olustur_btn)
        grid.addWidget(self.takviye_group, 1, 1)

        layout.addLayout(grid, 1)

    def set_tds(self, tds_id: int, tds_parametreler: list):
        """Aktif TDS ve parametreleri ayarla"""
        self.tds_id = tds_id
        self.tds_parametreler = tds_parametreler

    def _get_son_olcumler(self) -> dict:
        """Banyonun son analiz sonuclarini al"""
        olcumler = {}
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
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
                        olcumler[kod] = float(val)
        except Exception as e:
            print(f"[lab_banyo_tds] Son olcumler alinamadi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        return olcumler

    def _get_veri_serisi(self, gun: int = 30) -> list:
        """Son N gunluk analiz verilerini al"""
        veri = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tarih, sicaklik, ph, iletkenlik, kati_madde_yuzde, pb_orani,
                       solvent_yuzde, meq_degeri, toplam_asitlik, serbest_asitlik
                FROM uretim.banyo_analiz_sonuclari
                WHERE banyo_id = ? AND tarih >= DATEADD(DAY, ?, GETDATE())
                ORDER BY tarih ASC
            """, (self.banyo_id, -gun))
            for row in cursor.fetchall():
                tarih = row[0]
                param_map = {
                    "sicaklik": row[1], "ph": row[2], "iletkenlik": row[3],
                    "kati_madde": row[4], "pb_orani": row[5], "solvent": row[6],
                    "meq": row[7], "toplam_asit": row[8], "serbest_asit": row[9],
                }
                for param, deger in param_map.items():
                    if deger is not None:
                        veri.append({"parametre": param, "tarih": tarih, "deger": float(deger)})
        except Exception as e:
            print(f"[lab_banyo_tds] Veri serisi alinamadi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        return veri

    def _get_banyo_hacim(self) -> float:
        """Banyo hacmini al"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT hacim_lt FROM uretim.banyo_tanimlari WHERE id = ?", (self.banyo_id,))
            row = cursor.fetchone()
            if row and row[0]:
                return float(row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        return 1000.0

    def _run_analiz(self):
        """Tam analiz calistir"""
        if not self.tds_id or not self.tds_parametreler:
            QMessageBox.warning(self, "Uyari", "Lutfen once bir TDS secin ve parametreleri tanimlayin!")
            return

        try:
            from core.ai_analiz_service import AIAnalizService

            service = AIAnalizService()

            son_olcumler = self._get_son_olcumler()
            if not son_olcumler:
                QMessageBox.information(self, "Bilgi", "Bu banyo icin henuz analiz sonucu bulunmuyor.")
                return

            veri_serisi = self._get_veri_serisi()
            hacim = self._get_banyo_hacim()

            tds_params = []
            for p in self.tds_parametreler:
                tds_params.append({
                    "parametre_kodu": p.get("parametre_kodu", ""),
                    "parametre_adi": p.get("parametre_adi", ""),
                    "birim": p.get("birim", ""),
                    "tds_min": p.get("tds_min"),
                    "tds_hedef": p.get("tds_hedef"),
                    "tds_max": p.get("tds_max"),
                    "tolerans_yuzde": p.get("tolerans_yuzde", 10.0),
                })

            sonuclar = service.tam_analiz(
                self.banyo_id, tds_params, son_olcumler, veri_serisi, hacim)

            self._goster_karsilastirma(sonuclar.get("karsilastirma", []))
            self._goster_trend(sonuclar.get("trend", []), veri_serisi)
            self._goster_tahmin(sonuclar.get("tahmin", []))
            self._goster_takviye(sonuclar.get("takviye", []))

            # Risk seviyesi goster
            risk = sonuclar.get("risk_seviyesi", "NORMAL")
            renk_map = {"NORMAL": brand.SUCCESS, "UYARI": brand.WARNING, "KRITIK": brand.ERROR}
            self.risk_label.setText(f"Risk: {risk}")
            self.risk_label.setStyleSheet(
                f"color: {renk_map.get(risk, brand.TEXT)}; "
                f"font-weight: {brand.FW_SEMIBOLD}; "
                f"font-size: {brand.FS_BODY_LG}px;"
            )

            # Kaydet
            service.sonuclari_kaydet(self.banyo_id, self.tds_id, "tam_analiz", sonuclar)

        except Exception as e:
            QMessageBox.critical(self, "Analiz Hatasi", str(e))

    def _goster_karsilastirma(self, data: list):
        self.karsilastirma_table.setRowCount(len(data))
        for i, k in enumerate(data):
            self.karsilastirma_table.setItem(i, 0, QTableWidgetItem(k.get("parametre", "")))
            self.karsilastirma_table.setItem(i, 1, QTableWidgetItem(f"{k.get('tds_hedef', 0):.2f}"))
            self.karsilastirma_table.setItem(i, 2, QTableWidgetItem(f"{k.get('gercek', 0):.2f}"))
            self.karsilastirma_table.setItem(i, 3, QTableWidgetItem(f"{k.get('sapma', 0):.2f}"))
            self.karsilastirma_table.setItem(i, 4, QTableWidgetItem(f"{k.get('sapma_yuzde', 0):.1f}%"))

            durum = k.get("durum", "")
            durum_item = QTableWidgetItem(durum)
            if durum == "NORMAL":
                durum_item.setForeground(QColor(brand.SUCCESS))
            elif durum == "UYARI":
                durum_item.setForeground(QColor(brand.WARNING))
            elif durum == "KRITIK":
                durum_item.setForeground(QColor(brand.ERROR))
            self.karsilastirma_table.setItem(i, 5, durum_item)

    def _goster_trend(self, data: list, veri_serisi: list):
        if MATPLOTLIB_AVAILABLE and veri_serisi:
            self.trend_figure.clear()
            ax = self.trend_figure.add_subplot(111)
            ax.set_facecolor('#1a1a2e')

            param_gruplari = {}
            for v in veri_serisi:
                p = v.get("parametre", "")
                if p not in param_gruplari:
                    param_gruplari[p] = ([], [])
                param_gruplari[p][0].append(v.get("tarih"))
                param_gruplari[p][1].append(v.get("deger"))

            for param, (tarihler, degerler) in param_gruplari.items():
                if len(degerler) > 2:
                    ax.plot(range(len(degerler)), degerler, label=param, marker='o', markersize=3)

            ax.legend(fontsize=7, loc='upper left', facecolor='#1a1a2e',
                      edgecolor='#333', labelcolor='white')
            ax.tick_params(colors='white', labelsize=7)
            ax.set_xlabel('Olcum', color='white', fontsize=8)
            ax.set_ylabel('Deger', color='white', fontsize=8)
            self.trend_figure.tight_layout()
            self.trend_canvas.draw()
        elif not MATPLOTLIB_AVAILABLE:
            self.trend_table.setRowCount(len(data))
            for i, t in enumerate(data):
                self.trend_table.setItem(i, 0, QTableWidgetItem(t.get("parametre", "")))
                self.trend_table.setItem(i, 1, QTableWidgetItem(f"{t.get('son_deger', 0):.2f}"))
                self.trend_table.setItem(i, 2, QTableWidgetItem(f"{t.get('ortalama', 0):.2f}"))
                self.trend_table.setItem(i, 3, QTableWidgetItem(f"{t.get('egim', 0):.4f}"))
                yorum_item = QTableWidgetItem(t.get("yorum", ""))
                self.trend_table.setItem(i, 4, yorum_item)

    def _goster_tahmin(self, data: list):
        self.tahmin_table.setRowCount(len(data))
        for i, t in enumerate(data):
            self.tahmin_table.setItem(i, 0, QTableWidgetItem(t.get("parametre", "")))
            self.tahmin_table.setItem(i, 1, QTableWidgetItem(f"{t.get('mevcut', 0):.2f}"))
            self.tahmin_table.setItem(i, 2, QTableWidgetItem(f"{t.get('tahmini_7gun', 0):.2f}"))
            self.tahmin_table.setItem(i, 3, QTableWidgetItem(
                f"{t.get('tds_min', 0):.1f} - {t.get('tds_max', 0):.1f}"))

            risk = t.get("risk", "")
            risk_item = QTableWidgetItem(risk)
            renk_map = {"NORMAL": brand.SUCCESS, "DUSUK": brand.WARNING, "YUKSEK": brand.ERROR}
            risk_item.setForeground(QColor(renk_map.get(risk, brand.TEXT)))
            self.tahmin_table.setItem(i, 4, risk_item)

    def _goster_takviye(self, data: list):
        self.takviye_table.setRowCount(len(data))
        self.takviye_olustur_btn.setEnabled(len(data) > 0)
        self._takviye_data = data
        for i, t in enumerate(data):
            self.takviye_table.setItem(i, 0, QTableWidgetItem(t.get("kimyasal", "")))
            self.takviye_table.setItem(i, 1, QTableWidgetItem(f"{t.get('miktar', 0):.2f}"))
            self.takviye_table.setItem(i, 2, QTableWidgetItem(t.get("birim", "")))

            oncelik = t.get("oncelik", "")
            oncelik_item = QTableWidgetItem(oncelik)
            oncelik_renk = {"ACIL": brand.ERROR, "YUKSEK": brand.WARNING, "ORTA": brand.INFO, "DUSUK": brand.SUCCESS}
            oncelik_item.setForeground(QColor(oncelik_renk.get(oncelik, brand.TEXT)))
            self.takviye_table.setItem(i, 3, oncelik_item)

            self.takviye_table.setItem(i, 4, QTableWidgetItem(t.get("aciklama", "")))

    def _takviye_olustur(self):
        """Takviye islem emri veya kayit olustur"""
        if not hasattr(self, '_takviye_data') or not self._takviye_data:
            return

        ozet_satirlari = []
        for t in self._takviye_data:
            ozet_satirlari.append(f"- {t['kimyasal']}: {t['miktar']:.2f} {t['birim']} ({t['oncelik']})")

        QMessageBox.information(
            self, "Takviye Onerisi",
            "Onerilen Takviyeler:\n\n" + "\n".join(ozet_satirlari) +
            "\n\nBu bilgiler is emri olarak kaydedilebilir.")


# ============================================================
# ANA TDS TAB WIDGET
# ============================================================

class BanyoTDSTab(QWidget):
    """BanyoDialog icin TDS sekmesi — el kitabi uyumlu"""

    def __init__(self, theme: dict, banyo_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.banyo_id = banyo_id
        self.aktif_tds_id = None
        self._setup_ui()
        if banyo_id:
            self._load_tds_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_3, brand.SP_3, brand.SP_3, brand.SP_3)
        layout.setSpacing(brand.SP_2)

        # Ust kisim: TDS secim
        top_bar = QHBoxLayout()
        top_bar.setSpacing(brand.SP_3)
        top_bar.addWidget(QLabel("TDS:"))
        self.tds_combo = QComboBox()
        self.tds_combo.setMinimumWidth(brand.sp(250))
        self.tds_combo.currentIndexChanged.connect(self._on_tds_changed)
        top_bar.addWidget(self.tds_combo, 1)

        self.yeni_btn = _btn_primary("Yeni TDS")
        self.yeni_btn.clicked.connect(self._yeni_tds)
        top_bar.addWidget(self.yeni_btn)

        self.duzenle_btn = _btn_secondary("TDS Duzenle")
        self.duzenle_btn.clicked.connect(self._duzenle_tds)
        top_bar.addWidget(self.duzenle_btn)
        layout.addLayout(top_bar)

        # Alt sekmeler
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet(f"""
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

        # Alt-tab 1: Dosyalar
        self.dosya_widget = self._create_dosya_tab()
        self.sub_tabs.addTab(self.dosya_widget, "Dosyalar")

        # Alt-tab 2: Parametreler
        self.param_widget = self._create_parametre_tab()
        self.sub_tabs.addTab(self.param_widget, "Parametreler")

        # Alt-tab 3: AI Analiz
        self.ai_panel = TDSAIAnalizPanel(self.theme, self.banyo_id or 0)
        self.sub_tabs.addTab(self.ai_panel, "AI Analiz")

        layout.addWidget(self.sub_tabs, 1)

    # ----- DOSYA TAB -----
    def _create_dosya_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(brand.SP_2, brand.SP_2, brand.SP_2, brand.SP_2)
        layout.setSpacing(brand.SP_2)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)

        self.dosya_yukle_btn = _btn_primary("Dosya Yukle")
        self.dosya_yukle_btn.clicked.connect(self._dosya_yukle)
        toolbar.addWidget(self.dosya_yukle_btn)

        self.dosya_ac_btn = _btn_secondary("Dosya Ac")
        self.dosya_ac_btn.clicked.connect(self._dosya_ac)
        toolbar.addWidget(self.dosya_ac_btn)

        self.dosya_sil_btn = _btn_secondary("Dosya Sil")
        self.dosya_sil_btn.clicked.connect(self._dosya_sil)
        toolbar.addWidget(self.dosya_sil_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.dosya_table = QTableWidget()
        self.dosya_table.setColumnCount(5)
        self.dosya_table.setHorizontalHeaderLabels(["Dosya Adi", "Kategori", "Boyut", "Tarih", "Yol"])
        self.dosya_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.dosya_table.setColumnWidth(1, brand.sp(80))
        self.dosya_table.setColumnWidth(2, brand.sp(80))
        self.dosya_table.setColumnWidth(3, brand.sp(120))
        self.dosya_table.setColumnWidth(4, 0)
        self.dosya_table.setColumnHidden(4, True)
        self.dosya_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        _setup_table(self.dosya_table)
        layout.addWidget(self.dosya_table, 1)
        return w

    # ----- PARAMETRE TAB -----
    def _create_parametre_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(brand.SP_2, brand.SP_2, brand.SP_2, brand.SP_2)
        layout.setSpacing(brand.SP_2)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)

        self.param_ekle_btn = _btn_primary("Parametre Ekle")
        self.param_ekle_btn.clicked.connect(self._param_ekle)
        toolbar.addWidget(self.param_ekle_btn)

        self.standart_ekle_btn = _btn_secondary("Standart Parametreleri Ekle")
        self.standart_ekle_btn.clicked.connect(self._standart_param_ekle)
        toolbar.addWidget(self.standart_ekle_btn)

        self.banyo_kopyala_btn = _btn_secondary("Banyo Tanimlarindan Kopyala")
        self.banyo_kopyala_btn.clicked.connect(self._banyo_param_kopyala)
        toolbar.addWidget(self.banyo_kopyala_btn)

        self.param_kaydet_btn = _btn_success("Parametreleri Kaydet")
        self.param_kaydet_btn.clicked.connect(self._param_kaydet)
        toolbar.addWidget(self.param_kaydet_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.param_table = QTableWidget()
        self.param_table.setColumnCount(8)
        self.param_table.setHorizontalHeaderLabels([
            "Parametre Kodu", "Parametre Adi", "Birim", "TDS Min", "TDS Hedef", "TDS Max", "Tolerans%", "Kritik"])
        self.param_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.param_table.setColumnWidth(0, brand.sp(110))
        self.param_table.setColumnWidth(2, brand.sp(70))
        self.param_table.setColumnWidth(3, brand.sp(80))
        self.param_table.setColumnWidth(4, brand.sp(80))
        self.param_table.setColumnWidth(5, brand.sp(80))
        self.param_table.setColumnWidth(6, brand.sp(80))
        self.param_table.setColumnWidth(7, brand.sp(50))
        self.param_table.verticalHeader().setVisible(False)
        self.param_table.setShowGrid(False)
        self.param_table.setAlternatingRowColors(True)
        self.param_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.param_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.param_table.setStyleSheet(_table_style())
        layout.addWidget(self.param_table, 1)
        return w

    # ===== TDS LISTE YONETIMI =====

    def _load_tds_list(self):
        """Banyoya ait TDS listesini yukle"""
        self.tds_combo.blockSignals(True)
        self.tds_combo.clear()
        self.tds_combo.addItem("-- TDS Seciniz --", None)
        if not self.banyo_id:
            self.tds_combo.blockSignals(False)
            return
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
        except Exception as e:
            print(f"[lab_banyo_tds] TDS listesi yuklenemedi: {e}")
        finally:
            self.tds_combo.blockSignals(False)
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _on_tds_changed(self):
        """TDS secimi degistiginde"""
        tds_id = self.tds_combo.currentData()
        self.aktif_tds_id = tds_id
        if tds_id:
            self._load_dosyalar()
            self._load_parametreler()
            params = self._get_tds_param_dicts()
            self.ai_panel.set_tds(tds_id, params)
        else:
            self.dosya_table.setRowCount(0)
            self.param_table.setRowCount(0)

    def _yeni_tds(self):
        if not self.banyo_id:
            QMessageBox.warning(self, "Uyari", "Lutfen once banyoyu kaydedin!")
            return
        dlg = TDSDialog(self.theme, self.banyo_id, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_tds_list()
            if self.tds_combo.count() > 1:
                self.tds_combo.setCurrentIndex(self.tds_combo.count() - 1)

    def _duzenle_tds(self):
        tds_id = self.tds_combo.currentData()
        if not tds_id:
            QMessageBox.warning(self, "Uyari", "Lutfen bir TDS secin!")
            return
        dlg = TDSDialog(self.theme, self.banyo_id, tds_id, parent=self)
        if dlg.exec() == QDialog.Accepted:
            idx = self.tds_combo.currentIndex()
            self._load_tds_list()
            if idx < self.tds_combo.count():
                self.tds_combo.setCurrentIndex(idx)

    # ===== DOSYA YONETIMI =====

    def _get_tds_nas_path(self) -> str:
        """Aktif TDS icin NAS yolunu olustur"""
        if not self.banyo_id or not self.aktif_tds_id:
            return ""
        banyo_kod = ""
        tds_kod = ""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT kod FROM uretim.banyo_tanimlari WHERE id = ?", (self.banyo_id,))
            row = cursor.fetchone()
            if row:
                banyo_kod = row[0]
            cursor.execute("SELECT tds_kodu FROM uretim.banyo_tds WHERE id = ?", (self.aktif_tds_id,))
            row = cursor.fetchone()
            if row:
                tds_kod = row[0]
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        if not banyo_kod or not tds_kod:
            return ""
        return os.path.join(NAS_TDS_PATH, banyo_kod, tds_kod)

    def _load_dosyalar(self):
        """TDS dosyalarini DB'den yukle"""
        self.dosya_table.setRowCount(0)
        if not self.aktif_tds_id:
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, dosya_adi, kategori, dosya_boyut, yukleme_tarihi, dosya_yolu
                FROM uretim.banyo_tds_dosyalar
                WHERE tds_id = ?
                ORDER BY yukleme_tarihi DESC
            """, (self.aktif_tds_id,))
            rows = cursor.fetchall()

            self.dosya_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.dosya_table.setItem(i, 0, QTableWidgetItem(row[1] or ''))
                self.dosya_table.setItem(i, 1, QTableWidgetItem(row[2] or ''))

                boyut = row[3] or 0
                if boyut > 1024 * 1024:
                    boyut_str = f"{boyut / (1024*1024):.1f} MB"
                elif boyut > 1024:
                    boyut_str = f"{boyut / 1024:.0f} KB"
                else:
                    boyut_str = f"{boyut} B"
                self.dosya_table.setItem(i, 2, QTableWidgetItem(boyut_str))

                tarih = row[4]
                self.dosya_table.setItem(i, 3, QTableWidgetItem(
                    tarih.strftime("%d.%m.%Y %H:%M") if tarih else ""))

                yol_item = QTableWidgetItem(row[5] or '')
                self.dosya_table.setItem(i, 4, yol_item)

                id_item = self.dosya_table.item(i, 0)
                id_item.setData(Qt.UserRole, row[0])

        except Exception as e:
            print(f"[lab_banyo_tds] Dosyalar yuklenemedi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _dosya_yukle(self):
        """Dosya sec ve NAS'a kopyala + DB'ye kaydet"""
        if not self.aktif_tds_id:
            QMessageBox.warning(self, "Uyari", "Lutfen once bir TDS secin!")
            return

        from PySide6.QtWidgets import QInputDialog
        kategoriler = ["TDS", "SDS", "COA", "DIGER"]
        kategori, ok = QInputDialog.getItem(self, "Kategori", "Dosya kategorisi:", kategoriler, 0, False)
        if not ok:
            return

        dosya_yolu, _ = QFileDialog.getOpenFileName(
            self, "Dosya Sec", "",
            "Dokumanlar (*.pdf *.doc *.docx *.xls *.xlsx);;Resimler (*.jpg *.png);;Tum Dosyalar (*.*)")
        if not dosya_yolu:
            return

        nas_path = self._get_tds_nas_path()
        if not nas_path:
            QMessageBox.warning(self, "Uyari", "NAS yolu belirlenemedi!")
            return

        conn = None
        try:
            os.makedirs(nas_path, exist_ok=True)
            dosya_adi = os.path.basename(dosya_yolu)
            hedef_yol = os.path.join(nas_path, dosya_adi)

            base, ext = os.path.splitext(dosya_adi)
            counter = 1
            while os.path.exists(hedef_yol):
                dosya_adi = f"{base}_{counter}{ext}"
                hedef_yol = os.path.join(nas_path, dosya_adi)
                counter += 1

            shutil.copy2(dosya_yolu, hedef_yol)
            dosya_boyut = os.path.getsize(hedef_yol)
            dosya_tipi = ext.lstrip('.').upper()

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO uretim.banyo_tds_dosyalar
                (tds_id, dosya_adi, dosya_yolu, dosya_tipi, dosya_boyut, kategori)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.aktif_tds_id, dosya_adi, hedef_yol, dosya_tipi, dosya_boyut, kategori))
            conn.commit()

            QMessageBox.information(self, "Basarili", f"Dosya yuklendi:\n{hedef_yol}")
            self._load_dosyalar()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya yuklenemedi:\n{e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _dosya_ac(self):
        """Secili dosyayi ac"""
        row = self.dosya_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir dosya secin!")
            return
        yol = self.dosya_table.item(row, 4)
        if yol and yol.text():
            try:
                os.startfile(yol.text())
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Dosya acilamadi:\n{e}")

    def _dosya_sil(self):
        """Secili dosyayi sil"""
        row = self.dosya_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen bir dosya secin!")
            return

        dosya_adi = self.dosya_table.item(row, 0).text()
        if QMessageBox.question(
                self, "Onay", f"'{dosya_adi}' dosyasini silmek istediginize emin misiniz?") != QMessageBox.Yes:
            return

        dosya_db_id = self.dosya_table.item(row, 0).data(Qt.UserRole)
        dosya_yol = self.dosya_table.item(row, 4).text()

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM uretim.banyo_tds_dosyalar WHERE id = ?", (dosya_db_id,))
            conn.commit()

            if dosya_yol and os.path.exists(dosya_yol):
                os.remove(dosya_yol)

            self._load_dosyalar()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya silinemedi:\n{e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # ===== PARAMETRE YONETIMI =====

    def _load_parametreler(self):
        """TDS parametrelerini DB'den yukle"""
        self.param_table.setRowCount(0)
        if not self.aktif_tds_id:
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, parametre_kodu, parametre_adi, birim,
                       tds_min, tds_hedef, tds_max, tolerans_yuzde, kritik_mi, sira_no
                FROM uretim.banyo_tds_parametreler
                WHERE tds_id = ?
                ORDER BY sira_no, parametre_kodu
            """, (self.aktif_tds_id,))
            rows = cursor.fetchall()

            self.param_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                kod_item = QTableWidgetItem(row[1] or '')
                kod_item.setData(Qt.UserRole, row[0])
                self.param_table.setItem(i, 0, kod_item)

                self.param_table.setItem(i, 1, QTableWidgetItem(row[2] or ''))
                self.param_table.setItem(i, 2, QTableWidgetItem(row[3] or ''))
                self.param_table.setItem(i, 3, QTableWidgetItem(f"{row[4]:.4f}" if row[4] else ''))
                self.param_table.setItem(i, 4, QTableWidgetItem(f"{row[5]:.4f}" if row[5] else ''))
                self.param_table.setItem(i, 5, QTableWidgetItem(f"{row[6]:.4f}" if row[6] else ''))
                self.param_table.setItem(i, 6, QTableWidgetItem(f"{row[7]:.2f}" if row[7] else '10.00'))

                kritik_item = QTableWidgetItem("Evet" if row[8] else "Hayir")
                self.param_table.setItem(i, 7, kritik_item)

        except Exception as e:
            print(f"[lab_banyo_tds] Parametreler yuklenemedi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _param_ekle(self):
        """Bos parametre satiri ekle"""
        row = self.param_table.rowCount()
        self.param_table.insertRow(row)
        self.param_table.setItem(row, 0, QTableWidgetItem(""))
        self.param_table.setItem(row, 1, QTableWidgetItem(""))
        self.param_table.setItem(row, 2, QTableWidgetItem(""))
        self.param_table.setItem(row, 3, QTableWidgetItem(""))
        self.param_table.setItem(row, 4, QTableWidgetItem(""))
        self.param_table.setItem(row, 5, QTableWidgetItem(""))
        self.param_table.setItem(row, 6, QTableWidgetItem("10.00"))
        self.param_table.setItem(row, 7, QTableWidgetItem("Hayir"))

    def _standart_param_ekle(self):
        """Standart parametreleri tabloya ekle"""
        if not self.aktif_tds_id:
            QMessageBox.warning(self, "Uyari", "Lutfen once bir TDS secin!")
            return

        for sp in STANDART_PARAMETRELER:
            var_mi = False
            for r in range(self.param_table.rowCount()):
                item = self.param_table.item(r, 0)
                if item and item.text() == sp["kodu"]:
                    var_mi = True
                    break
            if var_mi:
                continue

            row = self.param_table.rowCount()
            self.param_table.insertRow(row)
            self.param_table.setItem(row, 0, QTableWidgetItem(sp["kodu"]))
            self.param_table.setItem(row, 1, QTableWidgetItem(sp["adi"]))
            self.param_table.setItem(row, 2, QTableWidgetItem(sp["birim"]))
            self.param_table.setItem(row, 3, QTableWidgetItem(""))
            self.param_table.setItem(row, 4, QTableWidgetItem(""))
            self.param_table.setItem(row, 5, QTableWidgetItem(""))
            self.param_table.setItem(row, 6, QTableWidgetItem("10.00"))
            self.param_table.setItem(row, 7, QTableWidgetItem("Hayir"))

    def _banyo_param_kopyala(self):
        """Banyo tanimlarindan min/hedef/max degerlerini kopyala"""
        if not self.banyo_id:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
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
            """, (self.banyo_id,))
            row = cursor.fetchone()

            if not row:
                return

            harita = [
                ("sicaklik", 0, 1, 2), ("ph", 3, 4, 5), ("iletkenlik", 6, 7, 8),
                ("kati_madde", 9, 10, 11), ("pb_orani", 12, 13, 14), ("solvent", 15, 16, 17),
                ("meq", 18, 19, 20), ("toplam_asit", 21, 22, 23), ("serbest_asit", 24, 25, 26),
            ]

            for kodu, min_i, hedef_i, max_i in harita:
                for r in range(self.param_table.rowCount()):
                    item = self.param_table.item(r, 0)
                    if item and item.text() == kodu:
                        if row[min_i] is not None:
                            self.param_table.setItem(r, 3, QTableWidgetItem(f"{row[min_i]:.4f}"))
                        if row[hedef_i] is not None:
                            self.param_table.setItem(r, 4, QTableWidgetItem(f"{row[hedef_i]:.4f}"))
                        if row[max_i] is not None:
                            self.param_table.setItem(r, 5, QTableWidgetItem(f"{row[max_i]:.4f}"))
                        break

            QMessageBox.information(self, "Basarili", "Banyo parametreleri kopyalandi!")

        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _param_kaydet(self):
        """Tablodaki parametreleri DB'ye kaydet"""
        if not self.aktif_tds_id:
            QMessageBox.warning(self, "Uyari", "Lutfen once bir TDS secin!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM uretim.banyo_tds_parametreler WHERE tds_id = ?", (self.aktif_tds_id,))

            for r in range(self.param_table.rowCount()):
                kod = (self.param_table.item(r, 0).text() or '').strip()
                adi = (self.param_table.item(r, 1).text() or '').strip()
                if not kod:
                    continue

                birim = (self.param_table.item(r, 2).text() or '').strip()

                def safe_float(item):
                    if not item:
                        return None
                    txt = item.text().strip()
                    if not txt:
                        return None
                    try:
                        return float(txt.replace(',', '.'))
                    except ValueError:
                        return None

                tds_min = safe_float(self.param_table.item(r, 3))
                tds_hedef = safe_float(self.param_table.item(r, 4))
                tds_max = safe_float(self.param_table.item(r, 5))
                tolerans = safe_float(self.param_table.item(r, 6)) or 10.0
                kritik = 1 if (self.param_table.item(r, 7) and self.param_table.item(r, 7).text().lower() in ('evet', 'yes', '1', 'true')) else 0

                cursor.execute("""
                    INSERT INTO uretim.banyo_tds_parametreler
                    (tds_id, parametre_kodu, parametre_adi, birim,
                     tds_min, tds_hedef, tds_max, tolerans_yuzde, kritik_mi, sira_no)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.aktif_tds_id, kod, adi, birim,
                      tds_min, tds_hedef, tds_max, tolerans, kritik, r + 1))

            conn.commit()
            QMessageBox.information(self, "Basarili", "Parametreler kaydedildi!")
            self._load_parametreler()

            params = self._get_tds_param_dicts()
            self.ai_panel.set_tds(self.aktif_tds_id, params)

        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _get_tds_param_dicts(self) -> list:
        """Tablodaki parametreleri dict listesi olarak dondur"""
        params = []
        for r in range(self.param_table.rowCount()):
            kod_item = self.param_table.item(r, 0)
            if not kod_item or not kod_item.text().strip():
                continue

            def safe_float(item):
                if not item:
                    return None
                txt = item.text().strip()
                try:
                    return float(txt.replace(',', '.'))
                except (ValueError, AttributeError):
                    return None

            params.append({
                "parametre_kodu": kod_item.text().strip(),
                "parametre_adi": (self.param_table.item(r, 1).text() or '').strip(),
                "birim": (self.param_table.item(r, 2).text() or '').strip(),
                "tds_min": safe_float(self.param_table.item(r, 3)),
                "tds_hedef": safe_float(self.param_table.item(r, 4)),
                "tds_max": safe_float(self.param_table.item(r, 5)),
                "tolerans_yuzde": safe_float(self.param_table.item(r, 6)) or 10.0,
            })
        return params

    def set_banyo_id(self, banyo_id: int):
        """Banyo ID'yi sonradan ayarla (yeni kayit sonrasi)"""
        self.banyo_id = banyo_id
        self.ai_panel.banyo_id = banyo_id
        self._load_tds_list()

    def save_tds_data(self):
        """BanyoDialog._save() icinden cagrilan kayit metodu"""
        if self.aktif_tds_id and self.param_table.rowCount() > 0:
            self._param_kaydet()
