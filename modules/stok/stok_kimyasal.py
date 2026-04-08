# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Kimyasal Tuketim Takip
TDS bazli tuketim formulasyonu, tuketim kaydi, stok durumu ve raporlama
"""
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QDateEdit, QTextEdit, QFormLayout, QWidget, QDoubleSpinBox,
    QTabWidget, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager


# =============================================================================
# TDS FORMUL DIALOG
# =============================================================================
class TDSFormulDialog(QDialog):
    """Banyo kimyasal TDS formulu tanimlama"""

    def __init__(self, theme: dict, parent=None, formul_id=None):
        super().__init__(parent)
        self.theme = theme
        self.formul_id = formul_id
        self.setWindowTitle("TDS Formul Tanimla" if not formul_id else "TDS Formul Duzenle")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if formul_id:
            self._load_data()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px; padding: 8px;
                color: {self.theme.get('text')};
            }}
        """)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.cmb_banyo = QComboBox()
        form.addRow("Banyo:", self.cmb_banyo)

        self.cmb_kimyasal = QComboBox()
        self.cmb_kimyasal.setEditable(True)
        form.addRow("Kimyasal:", self.cmb_kimyasal)

        self.spin_oran = QDoubleSpinBox()
        self.spin_oran.setRange(0.000001, 99999)
        self.spin_oran.setDecimals(6)
        form.addRow("Tuketim Orani:", self.spin_oran)

        self.cmb_birim = QComboBox()
        self.cmb_birim.addItems(["kg/ton", "lt/ton", "lt/1000lt", "ml/m2", "gr/adet", "kg/1000adet"])
        form.addRow("Tuketim Birimi:", self.cmb_birim)

        self.spin_hedef = QDoubleSpinBox()
        self.spin_hedef.setRange(0, 99999)
        self.spin_hedef.setDecimals(4)
        form.addRow("Hedef Konsantrasyon:", self.spin_hedef)

        self.cmb_kons_birim = QComboBox()
        self.cmb_kons_birim.addItems(["g/L", "ml/L", "%", "ppm"])
        form.addRow("Konsantrasyon Birimi:", self.cmb_kons_birim)

        self.spin_kritik = QDoubleSpinBox()
        self.spin_kritik.setRange(0, 99999)
        self.spin_kritik.setDecimals(4)
        form.addRow("Kritik Seviye:", self.spin_kritik)

        self.txt_not = QTextEdit()
        self.txt_not.setMaximumHeight(60)
        form.addRow("Not:", self.txt_not)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_iptal = QPushButton("Iptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 20px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)

    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM uretim.banyo_tanimlari WHERE aktif_mi = 1 ORDER BY kod")
            for r in cursor.fetchall():
                self.cmb_banyo.addItem(f"{r[1]} - {r[2]}", r[0])

            cursor.execute("""SELECT u.id, u.urun_kodu, u.urun_adi FROM stok.urunler u
                LEFT JOIN stok.urun_tipleri ut ON u.urun_tipi_id = ut.id
                WHERE (ut.kod IN ('KIMYASAL','HAMMADDE','YARDIMCI') OR u.urun_tipi IN ('KIMYASAL','HAMMADDE','YARDIMCI'))
                  AND ISNULL(u.aktif_mi, 1) = 1 AND ISNULL(u.silindi_mi, 0) = 0
                ORDER BY u.urun_kodu""")
            for r in cursor.fetchall():
                self.cmb_kimyasal.addItem(f"{r[1]} - {r[2]}", r[0])
            conn.close()
        except Exception as e:
            print(f"Combo yukleme: {e}")

    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT banyo_id, kimyasal_id, tuketim_orani, tuketim_birimi,
                hedef_konsantrasyon, konsantrasyon_birimi, kritik_seviye, notlar
                FROM uretim.banyo_kimyasal_tds WHERE id = ?""", (self.formul_id,))
            r = cursor.fetchone()
            conn.close()
            if r:
                idx = self.cmb_banyo.findData(r[0])
                if idx >= 0: self.cmb_banyo.setCurrentIndex(idx)
                idx = self.cmb_kimyasal.findData(r[1])
                if idx >= 0: self.cmb_kimyasal.setCurrentIndex(idx)
                self.spin_oran.setValue(float(r[2] or 0))
                idx = self.cmb_birim.findText(r[3] or "")
                if idx >= 0: self.cmb_birim.setCurrentIndex(idx)
                self.spin_hedef.setValue(float(r[4] or 0))
                idx = self.cmb_kons_birim.findText(r[5] or "")
                if idx >= 0: self.cmb_kons_birim.setCurrentIndex(idx)
                self.spin_kritik.setValue(float(r[6] or 0))
                self.txt_not.setPlainText(r[7] or "")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _save(self):
        banyo_id = self.cmb_banyo.currentData()
        kimyasal_id = self.cmb_kimyasal.currentData()
        if not banyo_id or not kimyasal_id:
            QMessageBox.warning(self, "Uyari", "Banyo ve kimyasal secimi zorunlu!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            params = (banyo_id, kimyasal_id, self.spin_oran.value(), self.cmb_birim.currentText(),
                      self.spin_hedef.value(), self.cmb_kons_birim.currentText(),
                      self.spin_kritik.value(), self.txt_not.toPlainText()[:500] or None)
            if self.formul_id:
                cursor.execute("""UPDATE uretim.banyo_kimyasal_tds SET banyo_id=?, kimyasal_id=?,
                    tuketim_orani=?, tuketim_birimi=?, hedef_konsantrasyon=?, konsantrasyon_birimi=?,
                    kritik_seviye=?, notlar=?, guncelleme_tarihi=GETDATE() WHERE id=?""",
                    params + (self.formul_id,))
            else:
                cursor.execute("""INSERT INTO uretim.banyo_kimyasal_tds
                    (banyo_id, kimyasal_id, tuketim_orani, tuketim_birimi,
                     hedef_konsantrasyon, konsantrasyon_birimi, kritik_seviye, notlar)
                    VALUES (?,?,?,?,?,?,?,?)""", params)
            conn.commit(); conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# =============================================================================
# ANA SAYFA
# =============================================================================
class StokKimyasalPage(BasePage):
    """Kimyasal Tuketim Takip Sayfasi"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_all)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Kimyasal Tuketim Takip")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {self.theme.get('border')}; }}
            QTabBar::tab {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 20px; }}
            QTabBar::tab:selected {{ background: {self.theme.get('primary')}; color: white; }}
        """)

        tabs.addTab(self._create_stok_tab(), "Kimyasal Stok")
        tabs.addTab(self._create_tuketim_tab(), "Tuketim Kayitlari")
        tabs.addTab(self._create_tds_tab(), "TDS Formulleri")
        tabs.addTab(self._create_rapor_tab(), "Raporlar")
        layout.addWidget(tabs)

    # ─── TAB 1: KİMYASAL STOK (YENİ - ANA TAB) ───
    def _create_stok_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        t = self.theme

        # Toolbar
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        lbl_info = QLabel("Kimyasal deposundaki stoklar - Satira cift tiklayarak tuketim kaydi girebilirsiniz")
        lbl_info.setStyleSheet(f"color: {t.get('text_secondary', '#888')}; font-size: 12px;")
        toolbar.addWidget(lbl_info)
        toolbar.addStretch()
        self.txt_stok_ara = QLineEdit()
        self.txt_stok_ara.setPlaceholderText("Ara (stok kodu, adi, lot)...")
        self.txt_stok_ara.setMaximumWidth(250)
        self.txt_stok_ara.setStyleSheet(f"background: {t.get('bg_input')}; border: 1px solid {t.get('border')}; border-radius: 6px; padding: 8px; color: {t.get('text')};")
        self.txt_stok_ara.textChanged.connect(self._stok_filtrele)
        toolbar.addWidget(self.txt_stok_ara)
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"QPushButton {{ background: {t.get('bg_input')}; color: {t.get('text')}; border: 1px solid {t.get('border')}; border-radius: 6px; padding: 8px 14px; }}")
        btn_yenile.clicked.connect(self._load_stok)
        toolbar.addWidget(btn_yenile)
        btn_yazdir = QPushButton("Yazdir")
        btn_yazdir.setStyleSheet(f"QPushButton {{ background: {t.get('info', '#3B82F6')}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; }}")
        btn_yazdir.clicked.connect(self._stok_yazdir)
        toolbar.addWidget(btn_yazdir)
        layout.addLayout(toolbar)

        self.tbl_stok = QTableWidget()
        self.tbl_stok.setColumnCount(7)
        self.tbl_stok.setHorizontalHeaderLabels(["Lot No", "Stok Kodu", "Stok Adi", "Miktar", "Birim", "Son Hareket", "Durum"])
        self.tbl_stok.verticalHeader().setVisible(False)
        self.tbl_stok.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_stok.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_stok.doubleClicked.connect(self._stok_ilave)
        self._style_table(self.tbl_stok)
        h = self.tbl_stok.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_stok.setColumnWidth(0, 160); self.tbl_stok.setColumnWidth(1, 120)
        self.tbl_stok.setColumnWidth(3, 100); self.tbl_stok.setColumnWidth(4, 70)
        self.tbl_stok.setColumnWidth(5, 110); self.tbl_stok.setColumnWidth(6, 80)
        layout.addWidget(self.tbl_stok)

        self.lbl_stok_ozet = QLabel("")
        self.lbl_stok_ozet.setStyleSheet(f"color: {t.get('text_muted', '#666')}; font-size: 12px; padding: 4px;")
        layout.addWidget(self.lbl_stok_ozet)
        return w

    # ─── TAB 2: TUKETIM KAYITLARI ───
    def _create_tuketim_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Tarih:"))
        self.dt_bas = QDateEdit()
        self.dt_bas.setCalendarPopup(True)
        self.dt_bas.setDate(QDate.currentDate().addDays(-30))
        toolbar.addWidget(self.dt_bas)
        toolbar.addWidget(QLabel("-"))
        self.dt_bit = QDateEdit()
        self.dt_bit.setCalendarPopup(True)
        self.dt_bit.setDate(QDate.currentDate())
        toolbar.addWidget(self.dt_bit)

        btn_filtre = QPushButton("Filtrele")
        btn_filtre.setStyleSheet(f"background: {self.theme.get('info')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_filtre.clicked.connect(self._load_tuketim)
        toolbar.addWidget(btn_filtre)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tbl_tuketim = QTableWidget()
        self.tbl_tuketim.setColumnCount(8)
        self.tbl_tuketim.setHorizontalHeaderLabels(["Tarih", "Banyo", "Kimyasal", "Islem", "Miktar", "Birim", "Neden", "Lot No"])
        self.tbl_tuketim.verticalHeader().setVisible(False)
        self.tbl_tuketim.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_tuketim.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._style_table(self.tbl_tuketim)
        h = self.tbl_tuketim.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.tbl_tuketim)
        return w

    # ─── TAB 3: TDS FORMULLERI ───
    def _create_tds_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        toolbar = QHBoxLayout()
        btn_ekle = QPushButton("Yeni Formul")
        btn_ekle.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_ekle.clicked.connect(self._add_formul)
        toolbar.addWidget(btn_ekle)
        btn_duzenle = QPushButton("Duzenle")
        btn_duzenle.setStyleSheet(f"background: {self.theme.get('info')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._edit_formul)
        toolbar.addWidget(btn_duzenle)
        btn_sil = QPushButton("Sil")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._del_formul)
        toolbar.addWidget(btn_sil)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tbl_tds = QTableWidget()
        self.tbl_tds.setColumnCount(7)
        self.tbl_tds.setHorizontalHeaderLabels(["ID", "Banyo", "Kimyasal", "Tuketim Orani", "Birim", "Hedef Kons.", "Kritik"])
        self.tbl_tds.verticalHeader().setVisible(False)
        self.tbl_tds.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_tds.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._style_table(self.tbl_tds)
        h = self.tbl_tds.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.tbl_tds)
        return w

    # ─── TAB 4: RAPORLAR ───
    def _create_rapor_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Donem:"))
        self.cmb_donem = QComboBox()
        self.cmb_donem.addItems(["Son 7 Gun", "Son 30 Gun", "Son 90 Gun", "Bu Yil"])
        toolbar.addWidget(self.cmb_donem)
        btn_rapor = QPushButton("Rapor Olustur")
        btn_rapor.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_rapor.clicked.connect(self._load_rapor)
        toolbar.addWidget(btn_rapor)
        toolbar.addStretch()
        toolbar.addWidget(self.create_export_button(title="Kimyasal Tuketim Raporu"))
        layout.addLayout(toolbar)

        self.tbl_rapor = QTableWidget()
        self.tbl_rapor.setColumnCount(5)
        self.tbl_rapor.setHorizontalHeaderLabels(["Kimyasal", "Toplam Tuketim", "Birim", "Islem Sayisi", "Son Tuketim"])
        self.tbl_rapor.verticalHeader().setVisible(False)
        self.tbl_rapor.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._style_table(self.tbl_rapor)
        h = self.tbl_rapor.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.tbl_rapor)
        return w

    # ─── STYLE ───
    def _style_table(self, tbl):
        tbl.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QTableWidget::item {{ padding: 6px; }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary')};
                font-weight: bold;
            }}
        """)

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def _load_all(self):
        self._load_stok()
        self._load_tuketim()
        self._load_tds()

    def _load_stok(self):
        """Kimyasal deposundaki lot bazli stoklari yukle - depo_takip.py ile ayni sorgu"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # depo_takip.py _load_stok_detay ile AYNI sorgu
            cursor.execute("""
                SELECT sb.id, sb.lot_no,
                       COALESCE(sb.stok_kodu, u.urun_kodu, '') as stok_kodu,
                       COALESCE(sb.stok_adi, u.urun_adi, '') as stok_adi,
                       sb.miktar,
                       COALESCE(sb.birim, b.kod, 'AD') as birim,
                       sb.son_hareket_tarihi,
                       sb.kalite_durumu,
                       sb.urun_id, sb.depo_id
                FROM stok.stok_bakiye sb
                LEFT JOIN stok.urunler u ON sb.urun_id = u.id
                LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                WHERE sb.depo_id IN (SELECT id FROM tanim.depolar WHERE kod LIKE 'KIM%')
                  AND sb.miktar > 0
                ORDER BY COALESCE(sb.stok_kodu, u.urun_kodu, ''), sb.son_hareket_tarihi DESC
            """)
            rows = cursor.fetchall()
            conn.close()

            self._stok_bakiye_data = {}
            self.tbl_stok.setRowCount(len(rows))
            toplam_miktar = 0
            for i, r in enumerate(rows):
                self._stok_bakiye_data[i] = {
                    'bakiye_id': r[0], 'lot_no': r[1], 'urun_kodu': r[2], 'urun_adi': r[3],
                    'miktar': float(r[4] or 0), 'birim': r[5], 'urun_id': r[8], 'depo_id': r[9]
                }

                lot_item = QTableWidgetItem(str(r[1] or ""))
                lot_item.setForeground(QColor(self.theme.get('info', '#3B82F6')))
                self.tbl_stok.setItem(i, 0, lot_item)
                self.tbl_stok.setItem(i, 1, QTableWidgetItem(str(r[2] or "")))
                self.tbl_stok.setItem(i, 2, QTableWidgetItem(str(r[3] or "")))

                miktar = float(r[4] or 0)
                toplam_miktar += miktar
                miktar_item = QTableWidgetItem(f"{miktar:,.2f}")
                miktar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tbl_stok.setItem(i, 3, miktar_item)
                self.tbl_stok.setItem(i, 4, QTableWidgetItem(str(r[5] or "")))

                tarih_str = r[6].strftime('%d.%m.%Y') if r[6] else ""
                self.tbl_stok.setItem(i, 5, QTableWidgetItem(tarih_str))

                durum = str(r[7] or "")
                durum_item = QTableWidgetItem(durum)
                if durum == 'ONAY':
                    durum_item.setForeground(QColor(self.theme.get('success', '#22c55e')))
                self.tbl_stok.setItem(i, 6, durum_item)
                self.tbl_stok.setRowHeight(i, 38)

            self.lbl_stok_ozet.setText(f"Toplam: {len(rows)} kalem | {toplam_miktar:,.2f} birim")
        except Exception as e:
            self.lbl_stok_ozet.setText(f"HATA: {e}")

    def _stok_filtrele(self, text):
        text = text.lower()
        for i in range(self.tbl_stok.rowCount()):
            visible = False
            for col in range(3):
                item = self.tbl_stok.item(i, col)
                if item and text in item.text().lower():
                    visible = True; break
            self.tbl_stok.setRowHidden(i, not visible)

    def _stok_ilave(self):
        """Secili stok kalemine tuketim kaydi gir"""
        row = self.tbl_stok.currentRow()
        if row < 0: return
        data = self._stok_bakiye_data.get(row)
        if not data: return

        t = self.theme
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Tuketim - {data['urun_kodu']}")
        dlg.setMinimumWidth(500); dlg.setModal(True)
        dlg.setStyleSheet(f"""
            QDialog {{ background: {t.get('bg_main', '#0F1419')}; }}
            QLabel {{ color: {t.get('text', '#fff')}; }}
            QComboBox, QDoubleSpinBox, QTextEdit {{ background: {t.get('bg_input', '#232C3B')};
                border: 1px solid {t.get('border', '#333')}; border-radius: 6px; padding: 8px; color: {t.get('text', '#fff')}; }}
        """)

        lay = QVBoxLayout(dlg); lay.setContentsMargins(24, 24, 24, 24); lay.setSpacing(16)

        hdr = QLabel(f"{data['urun_kodu']} - {data['urun_adi']}")
        hdr.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {t.get('text')};")
        lay.addWidget(hdr)

        info = QLabel(f"Lot: {data['lot_no']}  |  Mevcut: {data['miktar']:.2f} {data['birim']}")
        info.setStyleSheet(f"color: {t.get('text_secondary', '#888')}; font-size: 13px; padding: 8px 12px; background: {t.get('bg_card', '#151B23')}; border-radius: 6px;")
        lay.addWidget(info)

        form = QFormLayout(); form.setSpacing(12)
        lbl_s = f"color: {t.get('text_secondary', '#888')}; font-size: 13px;"

        lbl = QLabel("Banyo *"); lbl.setStyleSheet(lbl_s)
        cmb_banyo = QComboBox(); cmb_banyo.addItem("-- Banyo Secin --", None)
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM uretim.banyo_tanimlari WHERE aktif_mi = 1 ORDER BY kod")
            for r in cursor.fetchall(): cmb_banyo.addItem(f"{r[1]} - {r[2]}", r[0])
            conn.close()
        except: pass
        form.addRow(lbl, cmb_banyo)

        lbl = QLabel("Miktar *"); lbl.setStyleSheet(lbl_s)
        spin_miktar = QDoubleSpinBox(); spin_miktar.setRange(0.01, 99999); spin_miktar.setDecimals(2)
        form.addRow(lbl, spin_miktar)

        lbl = QLabel("Neden *"); lbl.setStyleSheet(lbl_s)
        cmb_neden = QComboBox()
        cmb_neden.addItem("Periyodik Takviye", "PERIYODIK")
        cmb_neden.addItem("Analiz Sonucu", "ANALIZ")
        cmb_neden.addItem("Ilk Dolum", "ILK_DOLUM")
        cmb_neden.addItem("Duzeltme", "DUZELTME")
        cmb_neden.addItem("Diger", "DIGER")
        form.addRow(lbl, cmb_neden)

        lbl = QLabel("Yapan *"); lbl.setStyleSheet(lbl_s)
        cmb_yapan = QComboBox(); cmb_yapan.addItem("-- Secin --", None)
        try:
            conn2 = get_db_connection(); cur2 = conn2.cursor()
            cur2.execute("SELECT id, ad, soyad FROM ik.personeller WHERE aktif_mi = 1 AND ISNULL(silindi_mi,0) = 0 ORDER BY ad")
            for r in cur2.fetchall(): cmb_yapan.addItem(f"{r[1]} {r[2]}", r[0])
            conn2.close()
        except: pass
        form.addRow(lbl, cmb_yapan)

        lbl = QLabel("Not"); lbl.setStyleSheet(lbl_s)
        txt_not = QTextEdit(); txt_not.setMaximumHeight(60)
        form.addRow(lbl, txt_not)
        lay.addLayout(form)

        btn_bar = QHBoxLayout(); btn_bar.addStretch()
        btn_iptal = QPushButton("Iptal")
        btn_iptal.setStyleSheet(f"QPushButton {{ background: {t.get('bg_input')}; color: {t.get('text')}; border: 1px solid {t.get('border')}; border-radius: 6px; padding: 10px 20px; }}")
        btn_iptal.clicked.connect(dlg.reject)
        btn_kaydet = QPushButton("Kaydet ve Stoktan Dus")
        btn_kaydet.setStyleSheet(f"QPushButton {{ background: {t.get('success', '#10B981')}; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 600; }}")

        def _kaydet():
            banyo_id = cmb_banyo.currentData()
            miktar = spin_miktar.value()
            neden = cmb_neden.currentData()
            yapan_id = cmb_yapan.currentData()
            if not banyo_id:
                QMessageBox.warning(dlg, "Uyari", "Banyo secimi zorunlu!"); return
            if not yapan_id:
                QMessageBox.warning(dlg, "Uyari", "Yapan personel secimi zorunlu!"); return
            if miktar > data['miktar']:
                QMessageBox.warning(dlg, "Uyari", f"Stokta {data['miktar']:.2f} var!"); return
            try:
                conn = get_db_connection(); cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO stok.stok_hareketleri
                    (uuid, hareket_tipi, hareket_nedeni, tarih, urun_id, depo_id,
                     miktar, birim_id, lot_no, referans_tip, aciklama, olusturma_tarihi)
                    VALUES (NEWID(), 'CIKIS', 'KIMYASAL_TUKETIM', GETDATE(), ?, ?,
                            ?, 1, ?, 'BANYO_TAKVIYE', ?, GETDATE())
                """, (data['urun_id'], data['depo_id'], miktar, data['lot_no'],
                      f"Banyo takviye - {cmb_banyo.currentText()[:50]} - {neden}"))
                cursor.execute("UPDATE stok.stok_bakiye SET miktar = miktar - ?, son_hareket_tarihi = GETDATE() WHERE id = ?",
                               (miktar, data['bakiye_id']))
                cursor.execute("""
                    INSERT INTO uretim.kimyasal_tuketim
                    (banyo_id, kimyasal_id, tarih, islem_tipi, miktar, birim, neden, yapan_id, lot_no, notlar)
                    VALUES (?, ?, GETDATE(), 'TAKVIYE', ?, ?, ?, ?, ?, ?)
                """, (banyo_id, data['urun_id'], miktar, data['birim'],
                      neden, yapan_id, data['lot_no'], txt_not.toPlainText().strip() or None))
                conn.commit(); conn.close()
                QMessageBox.information(dlg, "Basarili", f"{miktar:.2f} {data['birim']} stoktan dusuldu.\nLot: {data['lot_no']}")
                dlg.accept()
                self._load_stok()
                self._load_tuketim()
            except Exception as e:
                QMessageBox.critical(dlg, "Hata", str(e))

        btn_kaydet.clicked.connect(_kaydet)
        btn_bar.addWidget(btn_iptal); btn_bar.addWidget(btn_kaydet)
        lay.addLayout(btn_bar)
        dlg.exec()

    def _stok_yazdir(self):
        try:
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            from PySide6.QtGui import QTextDocument
            printer = QPrinter(QPrinter.HighResolution)
            dlg = QPrintDialog(printer, self)
            if dlg.exec() != QDialog.Accepted: return
            html = "<h2>Kimyasal Stok Durumu</h2>"
            html += f"<p>Tarih: {date.today().strftime('%d.%m.%Y')}</p>"
            html += "<table border='1' cellpadding='5' cellspacing='0' width='100%' style='border-collapse:collapse;'>"
            html += "<tr style='background:#333;color:#fff;'>"
            for c in range(self.tbl_stok.columnCount()):
                html += f"<th>{self.tbl_stok.horizontalHeaderItem(c).text()}</th>"
            html += "</tr>"
            for r in range(self.tbl_stok.rowCount()):
                if self.tbl_stok.isRowHidden(r): continue
                html += "<tr>"
                for c in range(self.tbl_stok.columnCount()):
                    item = self.tbl_stok.item(r, c)
                    html += f"<td>{item.text() if item else ''}</td>"
                html += "</tr>"
            html += f"</table><p>{self.lbl_stok_ozet.text()}</p>"
            doc = QTextDocument(); doc.setHtml(html); doc.print_(printer)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _load_tuketim(self):
        try:
            bas = self.dt_bas.date().toPython()
            bit = self.dt_bit.date().toPython()
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""
                SELECT t.tarih, b.kod, u.urun_kodu + ' - ' + u.urun_adi,
                       t.islem_tipi, t.miktar, t.birim, t.neden, t.lot_no
                FROM uretim.kimyasal_tuketim t
                JOIN uretim.banyo_tanimlari b ON t.banyo_id = b.id
                JOIN stok.urunler u ON t.kimyasal_id = u.id
                WHERE CAST(t.tarih AS DATE) BETWEEN ? AND ?
                ORDER BY t.tarih DESC
            """, (bas, bit))
            rows = cursor.fetchall(); conn.close()
            self.tbl_tuketim.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.tbl_tuketim.setItem(i, 0, QTableWidgetItem(r[0].strftime('%d.%m.%Y %H:%M') if r[0] else ""))
                self.tbl_tuketim.setItem(i, 1, QTableWidgetItem(r[1] or ""))
                self.tbl_tuketim.setItem(i, 2, QTableWidgetItem(r[2] or ""))
                self.tbl_tuketim.setItem(i, 3, QTableWidgetItem(r[3] or ""))
                self.tbl_tuketim.setItem(i, 4, QTableWidgetItem(f"{float(r[4]):.2f}" if r[4] else ""))
                self.tbl_tuketim.setItem(i, 5, QTableWidgetItem(r[5] or ""))
                self.tbl_tuketim.setItem(i, 6, QTableWidgetItem(r[6] or ""))
                self.tbl_tuketim.setItem(i, 7, QTableWidgetItem(r[7] or ""))
        except Exception as e:
            print(f"Tuketim yukleme: {e}")

    def _load_tds(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, b.kod + ' - ' + b.ad, u.urun_kodu + ' - ' + u.urun_adi,
                       t.tuketim_orani, t.tuketim_birimi, t.hedef_konsantrasyon, t.kritik_seviye
                FROM uretim.banyo_kimyasal_tds t
                JOIN uretim.banyo_tanimlari b ON t.banyo_id = b.id
                JOIN stok.urunler u ON t.kimyasal_id = u.id
                WHERE t.aktif_mi = 1 ORDER BY b.kod, u.urun_kodu
            """)
            rows = cursor.fetchall(); conn.close()
            self.tbl_tds.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.tbl_tds.setItem(i, 0, QTableWidgetItem(str(r[0])))
                self.tbl_tds.setItem(i, 1, QTableWidgetItem(r[1] or ""))
                self.tbl_tds.setItem(i, 2, QTableWidgetItem(r[2] or ""))
                self.tbl_tds.setItem(i, 3, QTableWidgetItem(f"{float(r[3]):.4f}" if r[3] else ""))
                self.tbl_tds.setItem(i, 4, QTableWidgetItem(r[4] or ""))
                self.tbl_tds.setItem(i, 5, QTableWidgetItem(f"{float(r[5]):.2f}" if r[5] else "-"))
                self.tbl_tds.setItem(i, 6, QTableWidgetItem(f"{float(r[6]):.2f}" if r[6] else "-"))
        except Exception as e:
            print(f"TDS yukleme: {e}")

    def _load_rapor(self):
        try:
            donem = self.cmb_donem.currentText()
            gun = {"Son 7 Gun": 7, "Son 30 Gun": 30, "Son 90 Gun": 90, "Bu Yil": 365}.get(donem, 30)
            bas = (datetime.now() - timedelta(days=gun)).strftime('%Y-%m-%d')
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""
                SELECT u.urun_kodu + ' - ' + u.urun_adi, SUM(t.miktar), t.birim, COUNT(*), MAX(t.tarih)
                FROM uretim.kimyasal_tuketim t
                JOIN stok.urunler u ON t.kimyasal_id = u.id
                WHERE t.tarih >= ?
                GROUP BY u.urun_kodu, u.urun_adi, t.birim
                ORDER BY SUM(t.miktar) DESC
            """, (bas,))
            rows = cursor.fetchall(); conn.close()
            self.tbl_rapor.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.tbl_rapor.setItem(i, 0, QTableWidgetItem(r[0] or ""))
                self.tbl_rapor.setItem(i, 1, QTableWidgetItem(f"{float(r[1]):.2f}" if r[1] else "0"))
                self.tbl_rapor.setItem(i, 2, QTableWidgetItem(r[2] or ""))
                self.tbl_rapor.setItem(i, 3, QTableWidgetItem(str(r[3] or 0)))
                self.tbl_rapor.setItem(i, 4, QTableWidgetItem(r[4].strftime('%d.%m.%Y') if r[4] else ""))
        except Exception as e:
            print(f"Rapor yukleme: {e}")

    # ─── ACTIONS ───
    def _add_formul(self):
        d = TDSFormulDialog(self.theme, self)
        if d.exec(): self._load_tds()

    def _edit_formul(self):
        row = self.tbl_tds.currentRow()
        if row < 0: QMessageBox.warning(self, "Uyari", "Bir formul secin!"); return
        fid = int(self.tbl_tds.item(row, 0).text())
        d = TDSFormulDialog(self.theme, self, fid)
        if d.exec(): self._load_tds()

    def _del_formul(self):
        row = self.tbl_tds.currentRow()
        if row < 0: QMessageBox.warning(self, "Uyari", "Bir formul secin!"); return
        fid = int(self.tbl_tds.item(row, 0).text())
        if QMessageBox.question(self, "Sil", "Bu formul silinecek. Devam?") == QMessageBox.Yes:
            try:
                conn = get_db_connection(); cursor = conn.cursor()
                cursor.execute("UPDATE uretim.banyo_kimyasal_tds SET aktif_mi = 0 WHERE id = ?", (fid,))
                conn.commit(); conn.close(); self._load_tds()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
