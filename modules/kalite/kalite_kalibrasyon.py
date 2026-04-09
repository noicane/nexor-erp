# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Kalibrasyon Sayfası
Ölçüm cihazları ve kalibrasyon planı yönetimi
"""
from datetime import datetime, date
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QTextEdit, QFormLayout, QDateEdit, QTabWidget, QWidget,
    QDoubleSpinBox, QFileDialog, QGroupBox
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager


class CihazDialog(QDialog):
    """Ölçüm cihazı ekleme/düzenleme dialog'u"""

    def __init__(self, theme: dict, cihaz_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.cihaz_id = cihaz_id
        self.cihaz = {}
        self.setWindowTitle("Ölçüm Cihazı" if not cihaz_id else "Cihaz Düzenle")
        self.setMinimumSize(550, 500)
        if cihaz_id:
            self._load_cihaz()
        self._setup_ui()

    def _load_cihaz(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cihaz_kodu, cihaz_adi, marka, model, seri_no,
                       olcum_araligi, cozunurluk, lokasyon, sorumlu_id, durum
                FROM kalite.olcum_cihazlari WHERE id = ?
            """, (self.cihaz_id,))
            row = cursor.fetchone()
            if row:
                self.cihaz = {'kod': row[0], 'ad': row[1], 'marka': row[2], 'model': row[3],
                              'seri_no': row[4], 'aralik': row[5], 'cozunurluk': row[6],
                              'lokasyon': row[7], 'sorumlu_id': row[8], 'durum': row[9]}
            conn.close()
        except Exception as e:
            print(f"Cihaz yukleme hatasi: {e}")

    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main')}; }} QLabel {{ color: {self.theme.get('text')}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        input_style = f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;"

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_kod = QLineEdit(self.cihaz.get('kod', ''))
        self.txt_kod.setStyleSheet(input_style)
        self.txt_kod.setPlaceholderText("Ör: OC-001")
        form.addRow("Cihaz Kodu:", self.txt_kod)

        self.txt_ad = QLineEdit(self.cihaz.get('ad', ''))
        self.txt_ad.setStyleSheet(input_style)
        form.addRow("Cihaz Adi:", self.txt_ad)

        self.txt_marka = QLineEdit(self.cihaz.get('marka', ''))
        self.txt_marka.setStyleSheet(input_style)
        form.addRow("Marka:", self.txt_marka)

        self.txt_model = QLineEdit(self.cihaz.get('model', ''))
        self.txt_model.setStyleSheet(input_style)
        form.addRow("Model:", self.txt_model)

        self.txt_seri = QLineEdit(self.cihaz.get('seri_no', ''))
        self.txt_seri.setStyleSheet(input_style)
        form.addRow("Seri No:", self.txt_seri)

        self.txt_aralik = QLineEdit(self.cihaz.get('aralik', ''))
        self.txt_aralik.setStyleSheet(input_style)
        self.txt_aralik.setPlaceholderText("Ör: 0-1000 um")
        form.addRow("Olcum Araligi:", self.txt_aralik)

        self.txt_lokasyon = QLineEdit(self.cihaz.get('lokasyon', ''))
        self.txt_lokasyon.setStyleSheet(input_style)
        form.addRow("Lokasyon:", self.txt_lokasyon)

        self.cmb_sorumlu = QComboBox()
        self.cmb_sorumlu.setStyleSheet(input_style)
        self._load_personel()
        form.addRow("Sorumlu:", self.cmb_sorumlu)

        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(['AKTIF', 'PASIF', 'ARIZALI', 'KALIBRASYONDA'])
        self.cmb_durum.setStyleSheet(input_style)
        if self.cihaz.get('durum'):
            idx = self.cmb_durum.findText(self.cihaz.get('durum'))
            if idx >= 0:
                self.cmb_durum.setCurrentIndex(idx)
        form.addRow("Durum:", self.cmb_durum)

        layout.addLayout(form)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_iptal = QPushButton("Iptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 10px 24px;")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)

    def _load_personel(self):
        self.cmb_sorumlu.clear()
        self.cmb_sorumlu.addItem("-- Secin --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_sorumlu.addItem(row[1], row[0])
            conn.close()
            if self.cihaz.get('sorumlu_id'):
                for i in range(self.cmb_sorumlu.count()):
                    if self.cmb_sorumlu.itemData(i) == self.cihaz.get('sorumlu_id'):
                        self.cmb_sorumlu.setCurrentIndex(i)
                        break
        except Exception:
            pass

    def _kaydet(self):
        kod = self.txt_kod.text().strip()
        ad = self.txt_ad.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyari", "Cihaz kodu ve adi zorunludur!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if self.cihaz_id:
                cursor.execute("""
                    UPDATE kalite.olcum_cihazlari SET cihaz_kodu=?, cihaz_adi=?, marka=?, model=?, seri_no=?,
                    olcum_araligi=?, lokasyon=?, sorumlu_id=?, durum=?, guncelleme_tarihi=GETDATE() WHERE id=?
                """, (kod, ad, self.txt_marka.text() or None, self.txt_model.text() or None, self.txt_seri.text() or None,
                      self.txt_aralik.text() or None, self.txt_lokasyon.text() or None,
                      self.cmb_sorumlu.currentData(), self.cmb_durum.currentText(), self.cihaz_id))
            else:
                cursor.execute("""
                    INSERT INTO kalite.olcum_cihazlari (uuid, cihaz_kodu, cihaz_adi, marka, model, seri_no,
                    olcum_araligi, lokasyon, sorumlu_id, durum, aktif_mi, olusturma_tarihi, guncelleme_tarihi)
                    VALUES (NEWID(), ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, GETDATE(), GETDATE())
                """, (kod, ad, self.txt_marka.text() or None, self.txt_model.text() or None, self.txt_seri.text() or None,
                      self.txt_aralik.text() or None, self.txt_lokasyon.text() or None,
                      self.cmb_sorumlu.currentData(), self.cmb_durum.currentText()))
            conn.commit()
            conn.close()
            LogManager.log_insert('kalite', 'kalite.olcum_cihazlari', None, 'Cihaz kaydedildi')
            QMessageBox.information(self, "Basarili", "Cihaz kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit basarisiz: {e}")


class KalibrasyonKayitDialog(QDialog):
    """Kalibrasyon kaydı ekleme dialog'u"""

    def __init__(self, theme: dict, cihaz_id: int, cihaz_adi: str, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.cihaz_id = cihaz_id
        self.cihaz_adi = cihaz_adi
        self.setWindowTitle("Kalibrasyon Kaydi Ekle")
        self.setMinimumSize(500, 450)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main')}; }} QLabel {{ color: {self.theme.get('text')}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        input_style = f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;"

        title = QLabel(f"{self.cihaz_adi}")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self.date_kalibrasyon = QDateEdit()
        self.date_kalibrasyon.setDate(QDate.currentDate())
        self.date_kalibrasyon.setCalendarPopup(True)
        self.date_kalibrasyon.setDisplayFormat("dd.MM.yyyy")
        self.date_kalibrasyon.setStyleSheet(input_style)
        form.addRow("Kalibrasyon Tarihi:", self.date_kalibrasyon)

        self.date_gecerlilik = QDateEdit()
        self.date_gecerlilik.setDate(QDate.currentDate().addYears(1))
        self.date_gecerlilik.setCalendarPopup(True)
        self.date_gecerlilik.setDisplayFormat("dd.MM.yyyy")
        self.date_gecerlilik.setStyleSheet(input_style)
        form.addRow("Gecerlilik Tarihi:", self.date_gecerlilik)

        self.cmb_firma = QComboBox()
        self.cmb_firma.setEditable(True)
        self.cmb_firma.setStyleSheet(input_style)
        self.cmb_firma.addItem("")
        self._load_firmalar()
        form.addRow("Yapan Firma:", self.cmb_firma)

        self.txt_sertifika = QLineEdit()
        self.txt_sertifika.setStyleSheet(input_style)
        form.addRow("Sertifika No:", self.txt_sertifika)

        self.cmb_sonuc = QComboBox()
        self.cmb_sonuc.addItems(['UYGUN', 'UYGUN DEGIL', 'SINIRLI KULLANIM'])
        self.cmb_sonuc.setStyleSheet(input_style)
        form.addRow("Sonuc:", self.cmb_sonuc)

        self.txt_maliyet = QDoubleSpinBox()
        self.txt_maliyet.setRange(0, 999999)
        self.txt_maliyet.setSuffix(" TL")
        self.txt_maliyet.setStyleSheet(input_style)
        form.addRow("Maliyet:", self.txt_maliyet)

        layout.addLayout(form)

        layout.addWidget(QLabel("Notlar:"))
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(80)
        self.txt_notlar.setStyleSheet(input_style)
        layout.addWidget(self.txt_notlar)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_iptal = QPushButton("Iptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 10px 24px;")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)

    def _load_firmalar(self):
        """Tedarikci cariler + daha once kullanilan firmalar"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Daha once kullanilan firmalar
            cursor.execute("""
                SELECT DISTINCT yapan_firma FROM kalite.kalibrasyon_kayitlari
                WHERE yapan_firma IS NOT NULL AND yapan_firma != ''
                ORDER BY yapan_firma
            """)
            firmalar = set()
            for r in cursor.fetchall():
                firmalar.add(r[0])
            # Tedarikci cariler
            cursor.execute("""
                SELECT DISTINCT unvan FROM musteri.cariler
                WHERE cari_tipi IN ('TEDARIKCI', 'TEDARIKCI_MUSTERI')
                  AND aktif_mi = 1 AND silindi_mi = 0
                ORDER BY unvan
            """)
            for r in cursor.fetchall():
                firmalar.add(r[0])
            conn.close()
            for f in sorted(firmalar):
                self.cmb_firma.addItem(f)
        except Exception as e:
            print(f"Firma yukleme hatasi: {e}")

    def _kaydet(self):
        firma = self.cmb_firma.currentText().strip()
        if not firma:
            QMessageBox.warning(self, "Uyari", "Yapan firma zorunludur!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO kalite.kalibrasyon_kayitlari (uuid, cihaz_id, kalibrasyon_tarihi, gecerlilik_tarihi,
                yapan_firma, sertifika_no, sonuc, maliyet, notlar, olusturma_tarihi)
                VALUES (NEWID(), ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (self.cihaz_id, self.date_kalibrasyon.date().toPython(), self.date_gecerlilik.date().toPython(),
                  firma, self.txt_sertifika.text() or None, self.cmb_sonuc.currentText(),
                  self.txt_maliyet.value() if self.txt_maliyet.value() > 0 else None, self.txt_notlar.toPlainText() or None))

            # Kalibrasyon planını güncelle
            sonraki_tarih = self.date_gecerlilik.date().toPython()
            kal_tarih = self.date_kalibrasyon.date().toPython()

            cursor.execute("""
                UPDATE kalite.kalibrasyon_planlari
                SET son_kalibrasyon_tarihi = ?, sonraki_kalibrasyon_tarihi = ?,
                    kalibrasyon_firma = ?
                WHERE cihaz_id = ? AND aktif_mi = 1
            """, (kal_tarih, sonraki_tarih, firma, self.cihaz_id))

            # Plan yoksa otomatik oluştur
            if cursor.rowcount == 0:
                ay_fark = (sonraki_tarih.year - kal_tarih.year) * 12 + (sonraki_tarih.month - kal_tarih.month)
                if ay_fark < 1:
                    ay_fark = 12
                cursor.execute("""
                    INSERT INTO kalite.kalibrasyon_planlari
                    (uuid, cihaz_id, kalibrasyon_periyodu_ay, son_kalibrasyon_tarihi,
                     sonraki_kalibrasyon_tarihi, kalibrasyon_firma, aktif_mi)
                    VALUES (NEWID(), ?, ?, ?, ?, ?, 1)
                """, (self.cihaz_id, ay_fark, kal_tarih, sonraki_tarih, firma))

            conn.commit()
            conn.close()
            LogManager.log_insert('kalite', 'kalite.kalibrasyon_kayitlari', None, 'Kalibrasyon kaydi eklendi')
            QMessageBox.information(self, "Basarili", "Kalibrasyon kaydi eklendi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit basarisiz: {e}")


class KaliteKalibrasyonPage(BasePage):
    """Kalibrasyon Sayfası - Modern UI"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._data_rows = []
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        t = self.theme

        # === HEADER ===
        header = QHBoxLayout()
        title = QLabel("Kalibrasyon Yonetimi")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {t.get('text')};")
        header.addWidget(title)
        header.addStretch()

        btn_style = f"""
            QPushButton {{
                background: {t.get('bg_card')};
                color: {t.get('text')};
                border: 1px solid {t.get('border')};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {t.get('bg_hover')}; }}
        """

        btn_rapor = QPushButton("PDF Rapor")
        btn_rapor.setStyleSheet(btn_style)
        btn_rapor.clicked.connect(self._pdf_rapor)
        header.addWidget(btn_rapor)

        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(btn_style)
        btn_yenile.clicked.connect(self._load_data)
        header.addWidget(btn_yenile)

        btn_yeni = QPushButton("+ Yeni Cihaz")
        btn_yeni.setStyleSheet(f"background: {t.get('primary')}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni_cihaz)
        header.addWidget(btn_yeni)

        layout.addLayout(header)

        # === ISTATISTIK KARTLARI ===
        stat_layout = QHBoxLayout()
        stat_layout.setSpacing(12)
        self.stat_toplam = self._stat_card("Toplam Cihaz", "0", t.get('primary', '#3b82f6'))
        self.stat_guncel = self._stat_card("Guncel", "0", t.get('success', '#22c55e'))
        self.stat_yaklasan = self._stat_card("30 Gun Icinde", "0", t.get('warning', '#f59e0b'))
        self.stat_geciken = self._stat_card("Suresi Gecmis", "0", t.get('error', '#ef4444'))
        stat_layout.addWidget(self.stat_toplam)
        stat_layout.addWidget(self.stat_guncel)
        stat_layout.addWidget(self.stat_yaklasan)
        stat_layout.addWidget(self.stat_geciken)
        stat_layout.addStretch()
        layout.addLayout(stat_layout)

        # === FILTRE ===
        filtre = QHBoxLayout()
        filtre.setSpacing(10)

        self.txt_ara = QLineEdit()
        self.txt_ara.setPlaceholderText("Cihaz ara...")
        self.txt_ara.setMaximumWidth(250)
        self.txt_ara.setStyleSheet(f"background: {t.get('bg_input')}; color: {t.get('text')}; border: 1px solid {t.get('border')}; border-radius: 6px; padding: 8px;")
        self.txt_ara.textChanged.connect(self._filtrele)
        filtre.addWidget(self.txt_ara)

        lbl = QLabel("Durum:")
        lbl.setStyleSheet(f"color: {t.get('text_secondary')};")
        filtre.addWidget(lbl)

        self.cmb_kal_durum = QComboBox()
        self.cmb_kal_durum.addItems(['Tumu', 'Suresi Gecmis', '30 Gun Icinde', 'Guncel', 'Plansiz'])
        self.cmb_kal_durum.setStyleSheet(f"background: {t.get('bg_input')}; color: {t.get('text')}; border: 1px solid {t.get('border')}; border-radius: 6px; padding: 6px 12px;")
        self.cmb_kal_durum.currentIndexChanged.connect(self._filtrele)
        filtre.addWidget(self.cmb_kal_durum)
        filtre.addStretch()

        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet(f"color: {t.get('text_muted')}; font-size: 12px;")
        filtre.addWidget(self.lbl_info)

        layout.addLayout(filtre)

        # === TABLO ===
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Cihaz Kodu", "Cihaz Adi", "Marka / Model",
            "Lokasyon", "Son Kalibrasyon", "Sonraki Kalibrasyon",
            "Kalan Gun", "Yapan Firma", "Islem"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 130)
        self.table.setColumnWidth(7, 90)
        self.table.setColumnWidth(8, 130)
        self.table.setColumnWidth(9, 170)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {t.get('bg_card')};
                color: {t.get('text')};
                border: 1px solid {t.get('border')};
                border-radius: 8px;
                gridline-color: {t.get('border')};
            }}
            QTableWidget::item {{ padding: 4px 8px; }}
            QTableWidget::item:selected {{ background: {t.get('bg_selected', '#1E1215')}; }}
            QHeaderView::section {{
                background: {t.get('bg_sidebar', '#0D1117')};
                color: {t.get('text')};
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid {t.get('border')};
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.table, 1)

    def _stat_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(160, 72)
        card.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card')};
                border-left: 3px solid {color};
                border-radius: 8px;
            }}
        """)
        lo = QVBoxLayout(card)
        lo.setContentsMargins(14, 8, 14, 8)
        lo.setSpacing(2)
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet(f"color: {self.theme.get('text_secondary')}; font-size: 11px;")
        lo.addWidget(lbl_t)
        lbl_v = QLabel(value)
        lbl_v.setObjectName("stat_value")
        lbl_v.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
        lo.addWidget(lbl_v)
        return card

    def _yeni_cihaz(self):
        dlg = CihazDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _duzenle_cihaz(self, cihaz_id: int):
        dlg = CihazDialog(self.theme, cihaz_id, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _kalibrasyon_ekle(self, cihaz_id: int, cihaz_adi: str):
        dlg = KalibrasyonKayitDialog(self.theme, cihaz_id, cihaz_adi, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT c.id, c.cihaz_kodu, c.cihaz_adi,
                       ISNULL(c.marka, '') + CASE WHEN c.model IS NOT NULL THEN ' ' + c.model ELSE '' END,
                       c.lokasyon,
                       p.son_kalibrasyon_tarihi,
                       p.sonraki_kalibrasyon_tarihi,
                       c.durum,
                       ISNULL(p.kalibrasyon_firma,
                           (SELECT TOP 1 yapan_firma FROM kalite.kalibrasyon_kayitlari WHERE cihaz_id = c.id ORDER BY kalibrasyon_tarihi DESC))
                FROM kalite.olcum_cihazlari c
                LEFT JOIN kalite.kalibrasyon_planlari p ON c.id = p.cihaz_id AND p.aktif_mi = 1
                WHERE c.aktif_mi = 1
                ORDER BY
                    CASE WHEN p.sonraki_kalibrasyon_tarihi IS NULL THEN 1 ELSE 0 END,
                    p.sonraki_kalibrasyon_tarihi
            """)

            self._data_rows = cursor.fetchall()
            conn.close()

            self._filtrele()

        except Exception as e:
            print(f"Veri yukleme hatasi: {e}")

    def _filtrele(self):
        today = date.today()
        arama = self.txt_ara.text().strip().lower()
        kal_filtre = self.cmb_kal_durum.currentText()

        filtered = []
        toplam = len(self._data_rows)
        guncel = yaklasan = geciken = plansiz = 0

        for row in self._data_rows:
            sonraki = row[6]

            # Kalibrasyon durumu hesapla
            if not sonraki:
                kal_durum = 'Plansiz'
                plansiz += 1
            else:
                sonraki_d = sonraki.date() if hasattr(sonraki, 'date') else sonraki
                kalan_gun = (sonraki_d - today).days
                if kalan_gun < 0:
                    kal_durum = 'Suresi Gecmis'
                    geciken += 1
                elif kalan_gun <= 30:
                    kal_durum = '30 Gun Icinde'
                    yaklasan += 1
                else:
                    kal_durum = 'Guncel'
                    guncel += 1

            # Filtre uygula
            if kal_filtre != 'Tumu' and kal_durum != kal_filtre:
                continue

            # Arama filtresi
            if arama:
                text = f"{row[1]} {row[2]} {row[3]} {row[4]} {row[8] or ''}".lower()
                if arama not in text:
                    continue

            filtered.append((row, kal_durum))

        # Istatistikleri guncelle
        self.stat_toplam.findChild(QLabel, "stat_value").setText(str(toplam))
        self.stat_guncel.findChild(QLabel, "stat_value").setText(str(guncel))
        self.stat_yaklasan.findChild(QLabel, "stat_value").setText(str(yaklasan))
        self.stat_geciken.findChild(QLabel, "stat_value").setText(str(geciken))

        # Tabloyu doldur
        self.table.setRowCount(len(filtered))
        t = self.theme

        for i, (row, kal_durum) in enumerate(filtered):
            self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))

            # Cihaz kodu
            kod_item = QTableWidgetItem(row[1] or '')
            kod_item.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(i, 1, kod_item)

            # Cihaz adi
            self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))

            # Marka/Model
            self.table.setItem(i, 3, QTableWidgetItem((row[3] or '').strip()))

            # Lokasyon
            self.table.setItem(i, 4, QTableWidgetItem(row[4] or ''))

            # Son kalibrasyon
            son_kal = row[5]
            son_text = son_kal.strftime('%d.%m.%Y') if son_kal else '-'
            self.table.setItem(i, 5, QTableWidgetItem(son_text))

            # Sonraki kalibrasyon
            sonraki = row[6]
            if sonraki:
                sonraki_d = sonraki.date() if hasattr(sonraki, 'date') else sonraki
                sonraki_text = sonraki_d.strftime('%d.%m.%Y')
                kalan = (sonraki_d - today).days
            else:
                sonraki_text = 'Plan Yok'
                kalan = None

            sonraki_item = QTableWidgetItem(sonraki_text)
            sonraki_item.setTextAlignment(Qt.AlignCenter)

            # Kalan gun
            if kalan is not None:
                kalan_item = QTableWidgetItem(f"{kalan} gun")
                kalan_item.setTextAlignment(Qt.AlignCenter)

                if kalan < 0:
                    color = t.get('error', '#ef4444')
                    kalan_item.setText(f"{abs(kalan)} gun gecti")
                elif kalan <= 30:
                    color = t.get('warning', '#f59e0b')
                else:
                    color = t.get('success', '#22c55e')

                sonraki_item.setForeground(QColor(color))
                kalan_item.setForeground(QColor(color))
            else:
                kalan_item = QTableWidgetItem('-')
                kalan_item.setTextAlignment(Qt.AlignCenter)
                kalan_item.setForeground(QColor(t.get('text_muted', '#666')))
                sonraki_item.setForeground(QColor(t.get('text_muted', '#666')))

            self.table.setItem(i, 6, sonraki_item)
            self.table.setItem(i, 7, kalan_item)

            # Yapan firma
            self.table.setItem(i, 8, QTableWidgetItem(row[8] or '-'))

            # Islem butonlari
            widget = self.create_action_buttons([
                ("Kalibrasyon", "Kalibrasyon Ekle", lambda checked, cid=row[0], cad=row[2]: self._kalibrasyon_ekle(cid, cad), "info"),
                ("Duzenle", "Cihaz Duzenle", lambda checked, cid=row[0]: self._duzenle_cihaz(cid), "edit"),
            ])
            self.table.setCellWidget(i, 9, widget)
            self.table.setRowHeight(i, 42)

        self.lbl_info.setText(f"{len(filtered)} / {toplam} cihaz")

    def _pdf_rapor(self):
        """Kalibrasyon durumu PDF raporu"""
        try:
            import os
            import subprocess
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            # Font kaydet
            font_registered = False
            for font_path in [
                "C:/Windows/Fonts/calibri.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/tahoma.ttf",
            ]:
                if os.path.exists(font_path):
                    try:
                        font_name = os.path.splitext(os.path.basename(font_path))[0]
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        font_registered = True
                        break
                    except Exception:
                        continue

            if not font_registered:
                font_name = 'Helvetica'

            output_dir = os.path.join(os.path.expanduser("~"), "Documents", "AtmoERP", "Raporlar")
            os.makedirs(output_dir, exist_ok=True)
            tarih_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(output_dir, f"Kalibrasyon_Raporu_{tarih_str}.pdf")

            doc = SimpleDocTemplate(filepath, pagesize=landscape(A4),
                                    leftMargin=15*mm, rightMargin=15*mm,
                                    topMargin=15*mm, bottomMargin=15*mm)

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('Title', fontName=font_name, fontSize=16, leading=20, alignment=1, spaceAfter=4*mm)
            subtitle_style = ParagraphStyle('Subtitle', fontName=font_name, fontSize=9, leading=12, alignment=1, textColor=colors.grey, spaceAfter=8*mm)
            cell_style = ParagraphStyle('Cell', fontName=font_name, fontSize=8, leading=10)

            today = date.today()
            elements = []
            elements.append(Paragraph("NEXOR ERP - Kalibrasyon Durum Raporu", title_style))
            elements.append(Paragraph(f"Rapor Tarihi: {today.strftime('%d.%m.%Y')} | Toplam: {len(self._data_rows)} Cihaz", subtitle_style))

            # Tablo verisi
            header = ['#', 'Cihaz Kodu', 'Cihaz Adi', 'Marka/Model', 'Lokasyon',
                       'Son Kalibrasyon', 'Sonraki', 'Kalan', 'Yapan Firma', 'Durum']
            data = [header]

            for idx, row in enumerate(self._data_rows, 1):
                son_kal = row[5]
                sonraki = row[6]

                son_text = son_kal.strftime('%d.%m.%Y') if son_kal else '-'

                if sonraki:
                    sonraki_d = sonraki.date() if hasattr(sonraki, 'date') else sonraki
                    sonraki_text = sonraki_d.strftime('%d.%m.%Y')
                    kalan = (sonraki_d - today).days
                    if kalan < 0:
                        kalan_text = f"{abs(kalan)} gun gecti"
                        durum = "GECMIS"
                    elif kalan <= 30:
                        kalan_text = f"{kalan} gun"
                        durum = "YAKIN"
                    else:
                        kalan_text = f"{kalan} gun"
                        durum = "GUNCEL"
                else:
                    sonraki_text = '-'
                    kalan_text = '-'
                    durum = "PLANSIZ"

                data.append([
                    str(idx),
                    row[1] or '',
                    Paragraph(row[2] or '', cell_style),
                    Paragraph((row[3] or '').strip(), cell_style),
                    row[4] or '',
                    son_text,
                    sonraki_text,
                    kalan_text,
                    Paragraph(row[8] or '-', cell_style),
                    durum,
                ])

            col_widths = [20*mm, 28*mm, 50*mm, 40*mm, 28*mm, 28*mm, 28*mm, 22*mm, 35*mm, 22*mm]
            tbl = Table(data, colWidths=col_widths, repeatRows=1)

            # Renklendirme
            style_cmds = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),
                ('ALIGN', (8, 1), (8, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]

            # Durum kolonunu renklendir
            for r_idx in range(1, len(data)):
                durum_val = data[r_idx][-1]
                if durum_val == 'GECMIS':
                    style_cmds.append(('TEXTCOLOR', (-1, r_idx), (-1, r_idx), colors.red))
                    style_cmds.append(('TEXTCOLOR', (-3, r_idx), (-3, r_idx), colors.red))
                elif durum_val == 'YAKIN':
                    style_cmds.append(('TEXTCOLOR', (-1, r_idx), (-1, r_idx), colors.HexColor('#d97706')))
                    style_cmds.append(('TEXTCOLOR', (-3, r_idx), (-3, r_idx), colors.HexColor('#d97706')))
                elif durum_val == 'GUNCEL':
                    style_cmds.append(('TEXTCOLOR', (-1, r_idx), (-1, r_idx), colors.HexColor('#16a34a')))

            tbl.setStyle(TableStyle(style_cmds))
            elements.append(tbl)

            doc.build(elements)

            subprocess.Popen(['start', '', filepath], shell=True)
            QMessageBox.information(self, "PDF Rapor", f"Rapor olusturuldu:\n{filepath}")

        except ImportError:
            QMessageBox.warning(self, "Hata", "PDF rapor icin reportlab kutuphanesi gerekli.\n\npip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Rapor olusturma hatasi:\n{e}")
            import traceback
            traceback.print_exc()
