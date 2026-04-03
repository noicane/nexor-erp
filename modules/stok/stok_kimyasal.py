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
        self.txt_not.setMaximumHeight(50)
        form.addRow("Not:", self.txt_not)

        layout.addLayout(form)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_iptal = QPushButton("Iptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 20px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)

        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
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

            cursor.execute("SELECT id, urun_kodu, urun_adi FROM stok.urunler WHERE urun_tipi = 'KIMYASAL' AND aktif_mi = 1 ORDER BY urun_kodu")
            for r in cursor.fetchall():
                self.cmb_kimyasal.addItem(f"{r[1]} - {r[2]}", r[0])
            conn.close()
        except Exception as e:
            print(f"Combo yukleme: {e}")

    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT banyo_id, kimyasal_id, tuketim_orani, tuketim_birimi, hedef_konsantrasyon, konsantrasyon_birimi, kritik_seviye, notlar FROM uretim.banyo_kimyasal_tds WHERE id = ?", (self.formul_id,))
            r = cursor.fetchone()
            conn.close()
            if r:
                idx = self.cmb_banyo.findData(r[0])
                if idx >= 0: self.cmb_banyo.setCurrentIndex(idx)
                idx = self.cmb_kimyasal.findData(r[1])
                if idx >= 0: self.cmb_kimyasal.setCurrentIndex(idx)
                self.spin_oran.setValue(float(r[2] or 0))
                idx = self.cmb_birim.findText(r[3] or "kg/ton")
                if idx >= 0: self.cmb_birim.setCurrentIndex(idx)
                self.spin_hedef.setValue(float(r[4] or 0))
                idx = self.cmb_kons_birim.findText(r[5] or "g/L")
                if idx >= 0: self.cmb_kons_birim.setCurrentIndex(idx)
                self.spin_kritik.setValue(float(r[6] or 0))
                self.txt_not.setPlainText(r[7] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

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
                      self.spin_hedef.value() or None, self.cmb_kons_birim.currentText(),
                      self.spin_kritik.value() or None, self.txt_not.toPlainText()[:500] or None)

            if self.formul_id:
                cursor.execute("""UPDATE uretim.banyo_kimyasal_tds SET
                    banyo_id=?, kimyasal_id=?, tuketim_orani=?, tuketim_birimi=?,
                    hedef_konsantrasyon=?, konsantrasyon_birimi=?, kritik_seviye=?,
                    notlar=?, guncelleme_tarihi=GETDATE() WHERE id=?""",
                    (*params, self.formul_id))
            else:
                cursor.execute("""INSERT INTO uretim.banyo_kimyasal_tds
                    (banyo_id, kimyasal_id, tuketim_orani, tuketim_birimi,
                     hedef_konsantrasyon, konsantrasyon_birimi, kritik_seviye, notlar)
                    VALUES (?,?,?,?,?,?,?,?)""", params)
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# =============================================================================
# TUKETIM KAYIT DIALOG
# =============================================================================
class TuketimDialog(QDialog):
    """Kimyasal tuketim/takviye kaydi"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Kimyasal Tuketim Kaydi")
        self.setMinimumWidth(550)
        self.setModal(True)
        self._banyo_formulleri = {}
        self._setup_ui()
        self._load_combos()

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
        self.cmb_banyo.currentIndexChanged.connect(self._on_banyo_changed)
        form.addRow("Banyo:", self.cmb_banyo)

        self.cmb_kimyasal = QComboBox()
        self.cmb_kimyasal.currentIndexChanged.connect(self._on_kimyasal_changed)
        form.addRow("Kimyasal:", self.cmb_kimyasal)

        self.cmb_islem = QComboBox()
        self.cmb_islem.addItems(["TAKVIYE", "ILK_DOLUM", "DUZELTME"])
        form.addRow("Islem Tipi:", self.cmb_islem)

        self.cmb_neden = QComboBox()
        self.cmb_neden.addItems(["PERIYODIK", "ANALIZ", "ILK_DOLUM", "DUZELTME", "DIGER"])
        form.addRow("Neden:", self.cmb_neden)

        self.spin_miktar = QDoubleSpinBox()
        self.spin_miktar.setRange(0.0001, 99999)
        self.spin_miktar.setDecimals(4)
        self.spin_miktar.setValue(1)
        form.addRow("Miktar:", self.spin_miktar)

        self.cmb_birim = QComboBox()
        self.cmb_birim.addItems(["KG", "LT", "GR", "ML"])
        form.addRow("Birim:", self.cmb_birim)

        # Stok bilgisi
        self.lbl_stok = QLabel("-")
        self.lbl_stok.setStyleSheet(f"color: {self.theme.get('info')}; font-weight: bold;")
        form.addRow("Mevcut Stok:", self.lbl_stok)

        # TDS bilgisi
        self.lbl_tds = QLabel("-")
        self.lbl_tds.setStyleSheet(f"color: {self.theme.get('success')}; font-weight: bold;")
        form.addRow("TDS Orani:", self.lbl_tds)

        self.cmb_yapan = QComboBox()
        form.addRow("Yapan:", self.cmb_yapan)

        self.txt_not = QTextEdit()
        self.txt_not.setMaximumHeight(50)
        form.addRow("Not:", self.txt_not)

        layout.addLayout(form)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_iptal = QPushButton("Iptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 20px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)

        btn_kaydet = QPushButton("Kaydet + Stoktan Dus")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
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

            # TDS formullerini yukle
            cursor.execute("""
                SELECT t.banyo_id, t.kimyasal_id, u.urun_kodu, u.urun_adi,
                       t.tuketim_orani, t.tuketim_birimi
                FROM uretim.banyo_kimyasal_tds t
                JOIN stok.urunler u ON t.kimyasal_id = u.id
                WHERE t.aktif_mi = 1
            """)
            for r in cursor.fetchall():
                key = r[0]  # banyo_id
                if key not in self._banyo_formulleri:
                    self._banyo_formulleri[key] = []
                self._banyo_formulleri[key].append({
                    'kimyasal_id': r[1], 'kod': r[2], 'ad': r[3],
                    'oran': r[4], 'birim': r[5]
                })

            # Yapan personel
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for r in cursor.fetchall():
                self.cmb_yapan.addItem(r[1], r[0])

            conn.close()
        except Exception as e:
            print(f"Combo yukleme: {e}")

    def _on_banyo_changed(self):
        self.cmb_kimyasal.clear()
        banyo_id = self.cmb_banyo.currentData()
        if not banyo_id:
            return

        # TDS'de tanimli kimyasallari goster
        formuller = self._banyo_formulleri.get(banyo_id, [])
        if formuller:
            for f in formuller:
                self.cmb_kimyasal.addItem(f"[TDS] {f['kod']} - {f['ad']}", f['kimyasal_id'])

        # Tum kimyasallari da ekle
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, urun_kodu, urun_adi FROM stok.urunler WHERE urun_tipi = 'KIMYASAL' AND aktif_mi = 1 ORDER BY urun_kodu")
            for r in cursor.fetchall():
                self.cmb_kimyasal.addItem(f"{r[1]} - {r[2]}", r[0])
            conn.close()
        except Exception:
            pass

    def _on_kimyasal_changed(self):
        kimyasal_id = self.cmb_kimyasal.currentData()
        banyo_id = self.cmb_banyo.currentData()
        if not kimyasal_id:
            return

        # Stok bilgisi
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(ISNULL(kullanilabilir_miktar, miktar)), birim
                FROM stok.stok_bakiye WHERE urun_id = ? AND bloke_mi = 0
                GROUP BY birim
            """, (kimyasal_id,))
            r = cursor.fetchone()
            if r:
                self.lbl_stok.setText(f"{float(r[0]):.2f} {r[1]}")
            else:
                self.lbl_stok.setText("Stok yok")
                self.lbl_stok.setStyleSheet(f"color: {self.theme.get('danger')}; font-weight: bold;")
            conn.close()
        except Exception:
            pass

        # TDS bilgisi
        if banyo_id:
            formuller = self._banyo_formulleri.get(banyo_id, [])
            for f in formuller:
                if f['kimyasal_id'] == kimyasal_id:
                    self.lbl_tds.setText(f"{float(f['oran']):.4f} {f['birim']}")
                    return
        self.lbl_tds.setText("TDS tanimli degil")

    def _save(self):
        banyo_id = self.cmb_banyo.currentData()
        kimyasal_id = self.cmb_kimyasal.currentData()
        yapan_id = self.cmb_yapan.currentData()

        if not banyo_id or not kimyasal_id:
            QMessageBox.warning(self, "Uyari", "Banyo ve kimyasal secimi zorunlu!")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            miktar = self.spin_miktar.value()
            birim = self.cmb_birim.currentText()
            islem = self.cmb_islem.currentText()
            neden = self.cmb_neden.currentText()

            # Stoktan lot bul (FIFO)
            lot_no = None
            cursor.execute("""
                SELECT TOP 1 lot_no FROM stok.stok_bakiye
                WHERE urun_id = ? AND bloke_mi = 0
                  AND ISNULL(kullanilabilir_miktar, miktar) > 0
                ORDER BY giris_tarihi ASC
            """, (kimyasal_id,))
            lot_row = cursor.fetchone()
            if lot_row:
                lot_no = lot_row[0]

            # Stok hareketi olustur (lot varsa)
            stok_hareket_id = None
            if lot_no:
                cursor.execute("""
                    INSERT INTO stok.stok_hareketleri
                        (hareket_tipi, hareket_nedeni, tarih, urun_id, lot_no, miktar, birim,
                         referans_tip, aciklama, olusturma_tarihi)
                    OUTPUT INSERTED.id
                    VALUES ('CIKIS', 'KIMYASAL_TUKETIM', GETDATE(), ?, ?, ?, ?,
                            'BANYO_TAKVIYE', ?, GETDATE())
                """, (kimyasal_id, lot_no, miktar, birim,
                      f"Banyo takviye - {self.cmb_banyo.currentText()[:50]}"))
                stok_hareket_id = cursor.fetchone()[0]

                # Stok bakiye guncelle
                cursor.execute("""
                    UPDATE stok.stok_bakiye SET
                        miktar = miktar - ?,
                        kullanilabilir_miktar = ISNULL(kullanilabilir_miktar, miktar) - ?
                    WHERE lot_no = ? AND urun_id = ?
                """, (miktar, miktar, lot_no, kimyasal_id))

            # Tuketim kaydi
            cursor.execute("""
                INSERT INTO uretim.kimyasal_tuketim
                    (banyo_id, kimyasal_id, tarih, islem_tipi, miktar, birim,
                     neden, yapan_id, stok_hareket_id, lot_no, notlar)
                VALUES (?, ?, GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?)
            """, (banyo_id, kimyasal_id, islem, miktar, birim,
                  neden, yapan_id, stok_hareket_id, lot_no,
                  self.txt_not.toPlainText()[:500] or None))

            conn.commit()
            LogManager.log_insert('uretim', 'uretim.kimyasal_tuketim', None,
                                  f'Kimyasal tuketim: {miktar} {birim}')
            conn.close()

            stok_msg = f"Stoktan dusuldu (Lot: {lot_no})" if lot_no else "Stok kaydi bulunamadi - sadece tuketim kaydedildi"
            QMessageBox.information(self, "Basarili", f"Tuketim kaydedildi.\n{stok_msg}")
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

        tabs.addTab(self._create_tds_tab(), "TDS Formulleri")
        tabs.addTab(self._create_tuketim_tab(), "Tuketim Kayitlari")
        tabs.addTab(self._create_stok_tab(), "Stok Durumu")
        tabs.addTab(self._create_rapor_tab(), "Raporlar")
        layout.addWidget(tabs)

    # ─── TAB 1: TDS FORMULLERI ───
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
        h.setDefaultSectionSize(100)
        layout.addWidget(self.tbl_tds)
        return w

    # ─── TAB 2: TUKETIM KAYITLARI ───
    def _create_tuketim_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        toolbar = QHBoxLayout()
        btn_yeni = QPushButton("Yeni Tuketim")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._add_tuketim)
        toolbar.addWidget(btn_yeni)

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
        self.tbl_tuketim.setHorizontalHeaderLabels(["Tarih", "Banyo", "Kimyasal", "Islem", "Miktar", "Birim", "Neden", "Yapan"])
        self.tbl_tuketim.verticalHeader().setVisible(False)
        self.tbl_tuketim.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_tuketim.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._style_table(self.tbl_tuketim)
        h = self.tbl_tuketim.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.tbl_tuketim)
        return w

    # ─── TAB 3: STOK DURUMU ───
    def _create_stok_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        self.tbl_stok = QTableWidget()
        self.tbl_stok.setColumnCount(6)
        self.tbl_stok.setHorizontalHeaderLabels(["Kimyasal Kodu", "Kimyasal Adi", "Mevcut Stok", "Min Stok", "Kritik Stok", "Durum"])
        self.tbl_stok.verticalHeader().setVisible(False)
        self.tbl_stok.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_stok.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._style_table(self.tbl_stok)
        h = self.tbl_stok.horizontalHeader()
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.tbl_stok)
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

    # ─── DATA LOADING ───
    def _load_all(self):
        self._load_tds()
        self._load_tuketim()
        self._load_stok()

    def _load_tds(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, b.kod + ' - ' + b.ad, u.urun_kodu + ' - ' + u.urun_adi,
                       t.tuketim_orani, t.tuketim_birimi, t.hedef_konsantrasyon, t.kritik_seviye
                FROM uretim.banyo_kimyasal_tds t
                JOIN uretim.banyo_tanimlari b ON t.banyo_id = b.id
                JOIN stok.urunler u ON t.kimyasal_id = u.id
                WHERE t.aktif_mi = 1
                ORDER BY b.kod, u.urun_kodu
            """)
            rows = cursor.fetchall()
            conn.close()

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

    def _load_tuketim(self):
        try:
            bas = self.dt_bas.date().toPython()
            bit = self.dt_bit.date().toPython()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.tarih, b.kod, u.urun_kodu + ' - ' + u.urun_adi,
                       t.islem_tipi, t.miktar, t.birim, t.neden,
                       p.ad + ' ' + p.soyad
                FROM uretim.kimyasal_tuketim t
                JOIN uretim.banyo_tanimlari b ON t.banyo_id = b.id
                JOIN stok.urunler u ON t.kimyasal_id = u.id
                LEFT JOIN ik.personeller p ON t.yapan_id = p.id
                WHERE CAST(t.tarih AS DATE) BETWEEN ? AND ?
                ORDER BY t.tarih DESC
            """, (bas, bit))
            rows = cursor.fetchall()
            conn.close()

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

    def _load_stok(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.urun_kodu, u.urun_adi,
                       ISNULL(SUM(s.kullanilabilir_miktar), 0) as stok,
                       u.min_stok, u.kritik_stok
                FROM stok.urunler u
                LEFT JOIN stok.stok_bakiye s ON u.id = s.urun_id AND s.bloke_mi = 0
                WHERE u.urun_tipi = 'KIMYASAL' AND u.aktif_mi = 1
                GROUP BY u.urun_kodu, u.urun_adi, u.min_stok, u.kritik_stok
                ORDER BY u.urun_kodu
            """)
            rows = cursor.fetchall()
            conn.close()

            self.tbl_stok.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.tbl_stok.setItem(i, 0, QTableWidgetItem(r[0] or ""))
                self.tbl_stok.setItem(i, 1, QTableWidgetItem(r[1] or ""))

                stok = float(r[2] or 0)
                min_s = float(r[3] or 0)
                kritik = float(r[4] or 0)

                stok_item = QTableWidgetItem(f"{stok:.2f}")
                self.tbl_stok.setItem(i, 2, stok_item)
                self.tbl_stok.setItem(i, 3, QTableWidgetItem(f"{min_s:.0f}" if min_s else "-"))
                self.tbl_stok.setItem(i, 4, QTableWidgetItem(f"{kritik:.0f}" if kritik else "-"))

                # Durum
                if kritik > 0 and stok <= kritik:
                    durum = "KRITIK"
                    renk = self.theme.get('danger', '#ef4444')
                elif min_s > 0 and stok <= min_s:
                    durum = "DUSUK"
                    renk = self.theme.get('warning', '#f59e0b')
                elif stok <= 0:
                    durum = "YOK"
                    renk = self.theme.get('danger', '#ef4444')
                else:
                    durum = "NORMAL"
                    renk = self.theme.get('success', '#22c55e')

                durum_item = QTableWidgetItem(durum)
                durum_item.setForeground(QColor(renk))
                self.tbl_stok.setItem(i, 5, durum_item)

                if durum in ("KRITIK", "YOK"):
                    stok_item.setForeground(QColor(self.theme.get('danger', '#ef4444')))
        except Exception as e:
            print(f"Stok yukleme: {e}")

    def _load_rapor(self):
        try:
            donem = self.cmb_donem.currentText()
            gun = {"Son 7 Gun": 7, "Son 30 Gun": 30, "Son 90 Gun": 90, "Bu Yil": 365}.get(donem, 30)
            bas = (datetime.now() - timedelta(days=gun)).strftime('%Y-%m-%d')

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.urun_kodu + ' - ' + u.urun_adi,
                       SUM(t.miktar), t.birim, COUNT(*), MAX(t.tarih)
                FROM uretim.kimyasal_tuketim t
                JOIN stok.urunler u ON t.kimyasal_id = u.id
                WHERE t.tarih >= ?
                GROUP BY u.urun_kodu, u.urun_adi, t.birim
                ORDER BY SUM(t.miktar) DESC
            """, (bas,))
            rows = cursor.fetchall()
            conn.close()

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
        if d.exec():
            self._load_tds()

    def _edit_formul(self):
        row = self.tbl_tds.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Bir formul secin!")
            return
        fid = int(self.tbl_tds.item(row, 0).text())
        d = TDSFormulDialog(self.theme, self, fid)
        if d.exec():
            self._load_tds()

    def _del_formul(self):
        row = self.tbl_tds.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Bir formul secin!")
            return
        fid = int(self.tbl_tds.item(row, 0).text())
        reply = QMessageBox.question(self, "Sil", "Bu formul silinecek. Devam?")
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE uretim.banyo_kimyasal_tds SET aktif_mi = 0 WHERE id = ?", (fid,))
                conn.commit()
                conn.close()
                self._load_tds()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _add_tuketim(self):
        d = TuketimDialog(self.theme, self)
        if d.exec():
            self._load_tuketim()
            self._load_stok()
