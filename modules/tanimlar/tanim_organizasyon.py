# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Organizasyon Tanımları
Departman / Bölüm / Görev tanımları tek sayfada birleşik
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QGroupBox, QTextEdit,
    QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


# ══════════════════════════════════════════════════════════
#  DIALOG: Departman / Bölüm Ekle-Düzenle
# ══════════════════════════════════════════════════════════

class DepartmanBolumDialog(QDialog):
    """Departman veya bölüm ekleme/düzenleme"""

    def __init__(self, theme, parent=None, departman_id=None):
        super().__init__(parent)
        self.theme = theme
        self.departman_id = departman_id
        self.setWindowTitle("Departman/Bölüm Ekle" if not departman_id else "Departman/Bölüm Düzenle")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if departman_id:
            self._load_data()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px;
                color: {brand.TEXT};
            }}
            QGroupBox {{
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: 8px; margin-top: 12px; padding-top: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        form_group = QGroupBox("Bilgiler")
        form = QFormLayout()

        self.txt_kod = QLineEdit()
        self.txt_kod.setMaxLength(20)
        self.txt_kod.setPlaceholderText("Örn: URETIM, KTL, ZNNI")
        form.addRow("Kod*:", self.txt_kod)

        self.txt_ad = QLineEdit()
        self.txt_ad.setMaxLength(100)
        self.txt_ad.setPlaceholderText("Örn: Üretim, Kataforez")
        form.addRow("Ad*:", self.txt_ad)

        self.cmb_ust = QComboBox()
        self.cmb_ust.addItem("-- Ana Departman (üst yok) --", None)
        form.addRow("Üst Departman:", self.cmb_ust)

        self.cmb_yonetici = QComboBox()
        self.cmb_yonetici.addItem("-- Seçiniz --", None)
        form.addRow("Yönetici:", self.cmb_yonetici)

        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        self.chk_aktif.setStyleSheet(f"color: {brand.TEXT};")
        form.addRow("", self.chk_aktif)

        form_group.setLayout(form)
        layout.addWidget(form_group)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setStyleSheet(f"background: {brand.SUCCESS}; color: white; padding: 10px 24px; border-radius: 6px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)

    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY ad")
            for r in cursor.fetchall():
                if r[0] != self.departman_id:
                    self.cmb_ust.addItem(f"{r[2]} ({r[1]})", r[0])
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for r in cursor.fetchall():
                self.cmb_yonetici.addItem(f"{r[1]} - {r[2]}", r[0])
            conn.close()
        except Exception as e:
            print(f"Combo yükleme hatası: {e}")

    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT kod, ad, ust_departman_id, yonetici_id, aktif_mi FROM ik.departmanlar WHERE id = ?", (self.departman_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.txt_kod.setText(row[0] or "")
                self.txt_kod.setEnabled(False)
                self.txt_ad.setText(row[1] or "")
                if row[2]:
                    idx = self.cmb_ust.findData(row[2])
                    if idx >= 0:
                        self.cmb_ust.setCurrentIndex(idx)
                if row[3]:
                    idx = self.cmb_yonetici.findData(row[3])
                    if idx >= 0:
                        self.cmb_yonetici.setCurrentIndex(idx)
                self.chk_aktif.setChecked(row[4] if row[4] is not None else True)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _save(self):
        kod = self.txt_kod.text().strip().upper()
        ad = self.txt_ad.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad zorunludur!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            ust_id = self.cmb_ust.currentData()
            yon_id = self.cmb_yonetici.currentData()
            if self.departman_id:
                cursor.execute("""
                    UPDATE ik.departmanlar SET ad=?, ust_departman_id=?, yonetici_id=?, aktif_mi=?, guncelleme_tarihi=GETDATE()
                    WHERE id=?
                """, (ad, ust_id, yon_id, self.chk_aktif.isChecked(), self.departman_id))
            else:
                cursor.execute("SELECT COUNT(*) FROM ik.departmanlar WHERE kod=?", (kod,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu kod zaten kullanılıyor!")
                    conn.close()
                    return
                cursor.execute("INSERT INTO ik.departmanlar (kod,ad,ust_departman_id,yonetici_id,aktif_mi) VALUES (?,?,?,?,?)",
                               (kod, ad, ust_id, yon_id, self.chk_aktif.isChecked()))
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ══════════════════════════════════════════════════════════
#  DIALOG: Görev Ekle-Düzenle
# ══════════════════════════════════════════════════════════

class GorevDialog(QDialog):
    """Görev ekleme/düzenleme"""

    def __init__(self, theme, parent=None, gorev_id=None):
        super().__init__(parent)
        self.theme = theme
        self.gorev_id = gorev_id
        self.setWindowTitle("Görev Ekle" if not gorev_id else "Görev Düzenle")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if gorev_id:
            self._load_data()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QComboBox, QTextEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px;
                color: {brand.TEXT};
            }}
        """)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.txt_kod = QLineEdit()
        self.txt_kod.setMaxLength(20)
        self.txt_kod.setPlaceholderText("Örn: KTL_ASK, ZN_OPR")
        form.addRow("Görev Kodu*:", self.txt_kod)

        self.txt_ad = QLineEdit()
        self.txt_ad.setMaxLength(100)
        self.txt_ad.setPlaceholderText("Örn: Kataforez Askılama")
        form.addRow("Görev Adı*:", self.txt_ad)

        self.cmb_bolum = QComboBox()
        form.addRow("Bölüm*:", self.cmb_bolum)

        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(80)
        self.txt_aciklama.setPlaceholderText("Görev tanımı, sorumluluklar...")
        form.addRow("Açıklama:", self.txt_aciklama)

        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        self.chk_aktif.setStyleSheet(f"color: {brand.TEXT};")
        form.addRow("", self.chk_aktif)

        layout.addLayout(form)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setStyleSheet(f"background: {brand.SUCCESS}; color: white; padding: 10px 24px; border-radius: 6px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)

    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            self.cmb_bolum.addItem("-- Seçiniz --", None)
            cursor.execute("""
                SELECT d.id, d.ad, ISNULL(ust.ad, '') as ust_ad
                FROM ik.departmanlar d
                LEFT JOIN ik.departmanlar ust ON d.ust_departman_id = ust.id
                WHERE d.aktif_mi = 1 ORDER BY ISNULL(ust.ad, d.ad), d.ad
            """)
            for r in cursor.fetchall():
                label = f"{r[2]} > {r[1]}" if r[2] else r[1]
                self.cmb_bolum.addItem(label, r[0])
            conn.close()
        except Exception as e:
            print(f"Combo yükleme hatası: {e}")

    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT kod, ad, departman_id, aktif_mi FROM ik.pozisyonlar WHERE id=?", (self.gorev_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.txt_kod.setText(row[0] or "")
                self.txt_kod.setEnabled(False)
                self.txt_ad.setText(row[1] or "")
                if row[2]:
                    idx = self.cmb_bolum.findData(row[2])
                    if idx >= 0:
                        self.cmb_bolum.setCurrentIndex(idx)
                self.chk_aktif.setChecked(row[3] if row[3] is not None else True)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _save(self):
        kod = self.txt_kod.text().strip().upper()
        ad = self.txt_ad.text().strip()
        bolum_id = self.cmb_bolum.currentData()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad zorunludur!")
            return
        if not bolum_id:
            QMessageBox.warning(self, "Uyarı", "Bölüm seçimi zorunludur!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if self.gorev_id:
                cursor.execute("UPDATE ik.pozisyonlar SET ad=?, departman_id=?, aktif_mi=? WHERE id=?",
                               (ad, bolum_id, self.chk_aktif.isChecked(), self.gorev_id))
            else:
                cursor.execute("SELECT COUNT(*) FROM ik.pozisyonlar WHERE kod=?", (kod,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu görev kodu zaten kullanılıyor!")
                    conn.close()
                    return
                cursor.execute("INSERT INTO ik.pozisyonlar (kod,ad,departman_id,aktif_mi) VALUES (?,?,?,?)",
                               (kod, ad, bolum_id, self.chk_aktif.isChecked()))
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ══════════════════════════════════════════════════════════
#  ANA SAYFA: Organizasyon Tanımları
# ══════════════════════════════════════════════════════════

class TanimOrganizasyonPage(BasePage):
    """Departman / Bölüm / Görev - Birleşik Tanım Sayfası"""

    def __init__(self, theme):
        super().__init__(theme)
        self._setup_ui()
        self._load_dept_data()
        self._load_gorev_data()

    # ─── Stil yardımcıları ────────────────────────────

    def _btn_style(self, bg=None, color=None):
        bg = bg or brand.BG_INPUT
        color = color or brand.TEXT
        return (f"QPushButton {{ background:{bg}; color:{color}; padding:8px 16px; "
                f"border-radius:6px; font-weight:bold; border:none; }}"
                f"QPushButton:hover {{ opacity:0.85; }}")

    def _table_style(self):
        return f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 8px;
                gridline-color: {brand.BORDER};
                color: {brand.TEXT};
            }}
            QTableWidget::item {{ padding: 6px; }}
            QTableWidget::item:selected {{ background: {brand.PRIMARY}; }}
            QHeaderView::section {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                padding: 8px; border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-weight: bold;
            }}
        """

    def _combo_style(self):
        return f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px;
                color: {brand.TEXT}; min-width: 150px;
            }}
        """

    # ─── UI Setup ─────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Organizasyon Tanımları")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {brand.TEXT};")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                background: {brand.BG_CARD};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                padding: 10px 24px; border: 1px solid {brand.BORDER};
                border-bottom: none; border-radius: 6px 6px 0 0; margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {brand.BG_CARD};
                border-bottom: 2px solid {brand.PRIMARY};
            }}
        """)
        tabs.addTab(self._create_dept_tab(), "Departman / Bölüm")
        tabs.addTab(self._create_gorev_tab(), "Görev")
        layout.addWidget(tabs, 1)

    # ═══════════════════════════════════════════════════
    #  TAB 1: Departman / Bölüm
    # ═══════════════════════════════════════════════════

    def _create_dept_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 8, 0, 0)

        # Toolbar
        tb = QHBoxLayout()
        btn_ekle = QPushButton("Yeni Departman/Bölüm")
        btn_ekle.setStyleSheet(self._btn_style(brand.SUCCESS, 'white'))
        btn_ekle.clicked.connect(self._dept_yeni)
        tb.addWidget(btn_ekle)

        btn_duzenle = QPushButton("Düzenle")
        btn_duzenle.setStyleSheet(self._btn_style())
        btn_duzenle.clicked.connect(self._dept_duzenle)
        tb.addWidget(btn_duzenle)

        btn_sil = QPushButton("Pasif Yap")
        btn_sil.setStyleSheet(self._btn_style(brand.ERROR, 'white'))
        btn_sil.clicked.connect(self._dept_sil)
        tb.addWidget(btn_sil)

        tb.addStretch()

        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(self._btn_style())
        btn_yenile.clicked.connect(self._load_dept_data)
        tb.addWidget(btn_yenile)
        layout.addLayout(tb)

        # Tablo
        self.dept_table = QTableWidget()
        self.dept_table.setColumnCount(7)
        self.dept_table.setHorizontalHeaderLabels([
            "ID", "Kod", "Ad", "Üst Departman", "Personel", "Görev", "Durum"
        ])
        self.dept_table.setColumnHidden(0, True)
        self.dept_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.dept_table.setSelectionMode(QTableWidget.SingleSelection)
        self.dept_table.verticalHeader().setVisible(False)
        self.dept_table.setStyleSheet(self._table_style())
        h = self.dept_table.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        self.dept_table.setColumnWidth(1, 100)
        self.dept_table.setColumnWidth(3, 140)
        self.dept_table.setColumnWidth(4, 70)
        self.dept_table.setColumnWidth(5, 70)
        self.dept_table.setColumnWidth(6, 70)
        self.dept_table.doubleClicked.connect(self._dept_duzenle)
        layout.addWidget(self.dept_table, 1)

        self.dept_stat = QLabel()
        self.dept_stat.setStyleSheet(f"color: {brand.TEXT_DIM};")
        layout.addWidget(self.dept_stat)
        return w

    def _load_dept_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.id, d.kod, d.ad, ust.ad as ust_ad, d.aktif_mi, d.ust_departman_id,
                    (SELECT COUNT(*) FROM ik.personeller WHERE departman_id=d.id AND aktif_mi=1) AS per,
                    (SELECT COUNT(*) FROM ik.pozisyonlar WHERE departman_id=d.id AND aktif_mi=1) AS poz
                FROM ik.departmanlar d
                LEFT JOIN ik.departmanlar ust ON d.ust_departman_id = ust.id
                ORDER BY d.kod
            """)
            all_rows = cursor.fetchall()
            conn.close()

            # Hiyerarşik sırala
            ana = [r for r in all_rows if r[5] is None]
            alt = [r for r in all_rows if r[5] is not None]
            sorted_rows = []
            for a in ana:
                sorted_rows.append((a, 0))
                for s in alt:
                    if s[5] == a[0]:
                        sorted_rows.append((s, 1))

            bold = QFont()
            bold.setBold(True)

            self.dept_table.setRowCount(len(sorted_rows))
            aktif = 0
            for i, (r, seviye) in enumerate(sorted_rows):
                self.dept_table.setItem(i, 0, QTableWidgetItem(str(r[0])))
                self.dept_table.setItem(i, 1, QTableWidgetItem(r[1] or ""))
                indent = "      " * seviye
                prefix = "└─ " if seviye > 0 else ""
                ad_item = QTableWidgetItem(f"{indent}{prefix}{r[2] or ''}")
                if seviye == 0:
                    ad_item.setFont(bold)
                self.dept_table.setItem(i, 2, ad_item)
                self.dept_table.setItem(i, 3, QTableWidgetItem(r[3] or "-"))

                per_item = QTableWidgetItem(str(r[6]) if r[6] else "-")
                per_item.setTextAlignment(Qt.AlignCenter)
                if r[6] and r[6] > 0:
                    per_item.setForeground(QColor(brand.INFO))
                self.dept_table.setItem(i, 4, per_item)

                poz_item = QTableWidgetItem(str(r[7]) if r[7] else "-")
                poz_item.setTextAlignment(Qt.AlignCenter)
                self.dept_table.setItem(i, 5, poz_item)

                d_item = QTableWidgetItem("Aktif" if r[4] else "Pasif")
                d_item.setForeground(QColor(brand.SUCCESS if r[4] else brand.ERROR))
                d_item.setTextAlignment(Qt.AlignCenter)
                self.dept_table.setItem(i, 6, d_item)
                if r[4]:
                    aktif += 1

            self.dept_stat.setText(f"Toplam: {len(sorted_rows)}  |  Aktif: {aktif}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _dept_yeni(self):
        if DepartmanBolumDialog(self.theme, self).exec() == QDialog.Accepted:
            self._load_dept_data()
            self._load_gorev_data()

    def _dept_duzenle(self):
        row = self.dept_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir satır seçin!")
            return
        did = int(self.dept_table.item(row, 0).text())
        if DepartmanBolumDialog(self.theme, self, did).exec() == QDialog.Accepted:
            self._load_dept_data()
            self._load_gorev_data()

    def _dept_sil(self):
        row = self.dept_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir satır seçin!")
            return
        did = int(self.dept_table.item(row, 0).text())
        kod = self.dept_table.item(row, 1).text()
        reply = QMessageBox.question(self, "Onay", f"'{kod}' departmanını pasif yapmak istiyor musunuz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE ik.departmanlar SET aktif_mi=0 WHERE id=?", (did,))
            conn.commit()
            conn.close()
            self._load_dept_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    # ═══════════════════════════════════════════════════
    #  TAB 2: Görev
    # ═══════════════════════════════════════════════════

    def _create_gorev_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 8, 0, 0)

        # Toolbar
        tb = QHBoxLayout()
        btn_ekle = QPushButton("Yeni Görev")
        btn_ekle.setStyleSheet(self._btn_style(brand.SUCCESS, 'white'))
        btn_ekle.clicked.connect(self._gorev_yeni)
        tb.addWidget(btn_ekle)

        btn_duzenle = QPushButton("Düzenle")
        btn_duzenle.setStyleSheet(self._btn_style())
        btn_duzenle.clicked.connect(self._gorev_duzenle)
        tb.addWidget(btn_duzenle)

        btn_sil = QPushButton("Pasif Yap")
        btn_sil.setStyleSheet(self._btn_style(brand.ERROR, 'white'))
        btn_sil.clicked.connect(self._gorev_sil)
        tb.addWidget(btn_sil)

        tb.addStretch()

        # Bölüm filtresi
        self.gorev_filtre = QComboBox()
        self.gorev_filtre.addItem("Tüm Bölümler", None)
        self.gorev_filtre.setStyleSheet(self._combo_style())
        self.gorev_filtre.currentIndexChanged.connect(self._gorev_filter)
        tb.addWidget(self.gorev_filtre)

        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(self._btn_style())
        btn_yenile.clicked.connect(self._load_gorev_data)
        tb.addWidget(btn_yenile)
        layout.addLayout(tb)

        # Tablo
        self.gorev_table = QTableWidget()
        self.gorev_table.setColumnCount(7)
        self.gorev_table.setHorizontalHeaderLabels([
            "ID", "Kod", "Görev Adı", "Departman", "Bölüm", "Personel", "Durum"
        ])
        self.gorev_table.setColumnHidden(0, True)
        self.gorev_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.gorev_table.setSelectionMode(QTableWidget.SingleSelection)
        self.gorev_table.verticalHeader().setVisible(False)
        self.gorev_table.setStyleSheet(self._table_style())
        h = self.gorev_table.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        self.gorev_table.setColumnWidth(1, 110)
        self.gorev_table.setColumnWidth(3, 110)
        self.gorev_table.setColumnWidth(4, 130)
        self.gorev_table.setColumnWidth(5, 70)
        self.gorev_table.setColumnWidth(6, 70)
        self.gorev_table.doubleClicked.connect(self._gorev_duzenle)
        layout.addWidget(self.gorev_table, 1)

        self.gorev_stat = QLabel()
        self.gorev_stat.setStyleSheet(f"color: {brand.TEXT_DIM};")
        layout.addWidget(self.gorev_stat)
        return w

    def _load_gorev_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.kod, p.ad,
                    ISNULL(ust.ad, d.ad) as departman,
                    CASE WHEN ust.id IS NOT NULL THEN d.ad ELSE NULL END as bolum,
                    p.aktif_mi, p.departman_id,
                    (SELECT COUNT(*) FROM ik.personeller per WHERE per.pozisyon_id=p.id AND per.aktif_mi=1) AS per_say
                FROM ik.pozisyonlar p
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                LEFT JOIN ik.departmanlar ust ON d.ust_departman_id = ust.id
                ORDER BY ISNULL(ust.ad, d.ad), d.ad, p.ad
            """)
            self._gorev_all = cursor.fetchall()

            # Filtre combo'yu güncelle
            self.gorev_filtre.blockSignals(True)
            current_data = self.gorev_filtre.currentData()
            self.gorev_filtre.clear()
            self.gorev_filtre.addItem("Tüm Bölümler", None)
            cursor.execute("""
                SELECT d.id, d.ad, ISNULL(ust.ad,'') as ust_ad
                FROM ik.departmanlar d
                LEFT JOIN ik.departmanlar ust ON d.ust_departman_id = ust.id
                WHERE d.aktif_mi = 1 ORDER BY ISNULL(ust.ad, d.ad), d.ad
            """)
            for r in cursor.fetchall():
                label = f"{r[2]} > {r[1]}" if r[2] else r[1]
                self.gorev_filtre.addItem(label, r[0])
            # Önceki seçimi koru
            if current_data:
                idx = self.gorev_filtre.findData(current_data)
                if idx >= 0:
                    self.gorev_filtre.setCurrentIndex(idx)
            self.gorev_filtre.blockSignals(False)

            conn.close()
            self._gorev_display(self._gorev_all)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _gorev_display(self, rows):
        self.gorev_table.setRowCount(len(rows))
        aktif = 0
        for i, r in enumerate(rows):
            self.gorev_table.setItem(i, 0, QTableWidgetItem(str(r[0])))
            self.gorev_table.setItem(i, 1, QTableWidgetItem(r[1] or ""))
            self.gorev_table.setItem(i, 2, QTableWidgetItem(r[2] or ""))
            self.gorev_table.setItem(i, 3, QTableWidgetItem(r[3] or "-"))
            self.gorev_table.setItem(i, 4, QTableWidgetItem(r[4] or "-"))
            per_item = QTableWidgetItem(str(r[7]) if r[7] else "0")
            per_item.setTextAlignment(Qt.AlignCenter)
            if r[7] and r[7] > 0:
                per_item.setForeground(QColor(brand.INFO))
            self.gorev_table.setItem(i, 5, per_item)
            d_item = QTableWidgetItem("Aktif" if r[5] else "Pasif")
            d_item.setForeground(QColor(brand.SUCCESS if r[5] else brand.ERROR))
            d_item.setTextAlignment(Qt.AlignCenter)
            self.gorev_table.setItem(i, 6, d_item)
            if r[5]:
                aktif += 1
        self.gorev_stat.setText(f"Toplam: {len(rows)} görev  |  Aktif: {aktif}")

    def _gorev_filter(self):
        dept_id = self.gorev_filtre.currentData()
        if dept_id is None:
            self._gorev_display(self._gorev_all)
        else:
            self._gorev_display([r for r in self._gorev_all if r[6] == dept_id])

    def _gorev_yeni(self):
        if GorevDialog(self.theme, self).exec() == QDialog.Accepted:
            self._load_gorev_data()

    def _gorev_duzenle(self):
        row = self.gorev_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir satır seçin!")
            return
        gid = int(self.gorev_table.item(row, 0).text())
        if GorevDialog(self.theme, self, gid).exec() == QDialog.Accepted:
            self._load_gorev_data()

    def _gorev_sil(self):
        row = self.gorev_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir satır seçin!")
            return
        gid = int(self.gorev_table.item(row, 0).text())
        kod = self.gorev_table.item(row, 1).text()
        reply = QMessageBox.question(self, "Onay", f"'{kod}' görevini pasif yapmak istiyor musunuz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE ik.pozisyonlar SET aktif_mi=0 WHERE id=?", (gid,))
            conn.commit()
            conn.close()
            self._load_gorev_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
