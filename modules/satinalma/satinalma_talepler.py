# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Satınalma Talepleri (Onay Sistemi Entegrasyonlu)
satinalma.talepler ve satinalma.talep_satirlari
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QSpinBox,
    QDoubleSpinBox, QTabWidget, QGroupBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtGui import QPainter, QFont, QTextDocument

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from datetime import datetime


class TalepSatirDialog(QDialog):
    """Talep satiri ekleme/duzenleme - Tedarikci, depo stok ve anlasma fiyati destekli"""

    def __init__(self, theme: dict, talep_id: int, parent=None, satir_id=None, tedarikci_id=None):
        super().__init__(parent)
        self.theme = theme
        self.talep_id = talep_id
        self.satir_id = satir_id
        self.tedarikci_id = tedarikci_id
        self._urun_stok = {}  # urun_id -> depo stok bilgisi
        self._anlasma_fiyat = {}  # urun_id -> anlasma fiyati
        self.setWindowTitle("Kalem Ekle" if not satir_id else "Kalem Duzenle")
        self.setMinimumWidth(600)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()

        if satir_id:
            self._load_data()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
        """)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Urun tipi filtresi
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["Tumu", "KIMYASAL", "HAMMADDE", "PARCA", "YEDEK_PARCA"])
        self.cmb_tip.currentIndexChanged.connect(self._filter_urunler)
        form.addRow("Urun Tipi:", self.cmb_tip)

        # Urun secimi
        self.cmb_urun = QComboBox()
        self.cmb_urun.setEditable(True)
        self.cmb_urun.setMinimumWidth(400)
        self.cmb_urun.currentIndexChanged.connect(self._on_urun_changed)
        form.addRow("Urun:", self.cmb_urun)

        self.txt_urun_adi = QLineEdit()
        self.txt_urun_adi.setPlaceholderText("Urun/Malzeme adi")
        form.addRow("Urun Adi*:", self.txt_urun_adi)

        # Stok bilgisi (read-only)
        self.lbl_stok = QLabel("-")
        self.lbl_stok.setStyleSheet(f"color: {self.theme.get('info')}; font-size: 12px; font-weight: bold; padding: 4px;")
        form.addRow("Depo Stok:", self.lbl_stok)

        # Anlasma fiyati (read-only)
        self.lbl_anlasma = QLabel("-")
        self.lbl_anlasma.setStyleSheet(f"color: {self.theme.get('success')}; font-size: 12px; font-weight: bold; padding: 4px;")
        form.addRow("Anlasma Fiyati:", self.lbl_anlasma)

        # Miktar
        miktar_layout = QHBoxLayout()
        self.spin_miktar = QDoubleSpinBox()
        self.spin_miktar.setRange(0.01, 9999999)
        self.spin_miktar.setDecimals(2)
        self.spin_miktar.setValue(1)
        miktar_layout.addWidget(self.spin_miktar)

        self.cmb_birim = QComboBox()
        self.cmb_birim.addItems(["ADET", "KG", "LT", "MT", "M2", "M3", "PAKET", "KUTU", "VARIL"])
        miktar_layout.addWidget(self.cmb_birim)
        form.addRow("Miktar*:", miktar_layout)

        # Tahmini fiyat + para birimi
        fiyat_layout = QHBoxLayout()
        self.spin_fiyat = QDoubleSpinBox()
        self.spin_fiyat.setRange(0, 9999999)
        self.spin_fiyat.setDecimals(4)
        fiyat_layout.addWidget(self.spin_fiyat)
        self.cmb_para_birimi = QComboBox()
        self.cmb_para_birimi.setMinimumWidth(80)
        self._load_para_birimleri()
        fiyat_layout.addWidget(self.cmb_para_birimi)
        form.addRow("Birim Fiyat:", fiyat_layout)

        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(60)
        form.addRow("Aciklama:", self.txt_aciklama)

        layout.addLayout(form)
        layout.addStretch()

        # Butonlar
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

    def _load_para_birimleri(self):
        """Para birimleri combosunu doldur"""
        self.cmb_para_birimi.clear()
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT kod, sembol FROM tanim.para_birimleri WHERE aktif_mi = 1 ORDER BY CASE WHEN varsayilan_mi = 1 THEN 0 ELSE 1 END, kod")
            rows = cursor.fetchall(); conn.close()
            for r in rows:
                self.cmb_para_birimi.addItem(f"{r[0]} ({r[1]})" if r[1] else r[0], r[0])
        except Exception:
            self.cmb_para_birimi.addItem("TRY", "TRY")
            self.cmb_para_birimi.addItem("USD", "USD")
            self.cmb_para_birimi.addItem("EUR", "EUR")

    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Tum urunleri yukle (dahili cache)
            cursor.execute("""
                SELECT u.id, u.urun_kodu, u.urun_adi, u.urun_tipi, u.birim_id
                FROM stok.urunler u WHERE u.aktif_mi = 1 ORDER BY u.urun_kodu
            """)
            self._all_urunler = cursor.fetchall()

            # Depo stok bilgileri
            cursor.execute("""
                SELECT urun_id, SUM(ISNULL(kullanilabilir_miktar, miktar)) as toplam, birim
                FROM stok.stok_bakiye
                WHERE bloke_mi = 0
                GROUP BY urun_id, birim
            """)
            for r in cursor.fetchall():
                self._urun_stok[r[0]] = {'miktar': float(r[1] or 0), 'birim': r[2] or ''}

            # Tedarikci anlasma fiyatlari
            if self.tedarikci_id:
                cursor.execute("""
                    SELECT tf.urun_id, tf.urun_adi, tf.birim_fiyat,
                           ISNULL(pb.kod, 'TRY') as para_birimi
                    FROM satinalma.tedarikci_fiyatlari tf
                    LEFT JOIN tanim.para_birimleri pb ON tf.para_birimi_id = pb.id
                    WHERE tf.tedarikci_id = ? AND tf.aktif_mi = 1
                      AND GETDATE() BETWEEN tf.gecerlilik_baslangic AND ISNULL(tf.gecerlilik_bitis, '2099-12-31')
                """, (self.tedarikci_id,))
                for r in cursor.fetchall():
                    if r[0]:
                        self._anlasma_fiyat[r[0]] = {'fiyat': float(r[2] or 0), 'urun_adi': r[1], 'para_birimi': r[3] or 'TRY'}

            conn.close()
            self._filter_urunler()
        except Exception as e:
            print(f"Combo yukleme hatasi: {e}")

    def _filter_urunler(self):
        """Urun tipine gore filtrele"""
        self.cmb_urun.blockSignals(True)
        self.cmb_urun.clear()
        self.cmb_urun.addItem("-- Manuel Giris --", None)

        tip = self.cmb_tip.currentText()
        for row in self._all_urunler:
            urun_id, kod, ad, urun_tipi = row[0], row[1], row[2], row[3] or ''
            if tip != "Tumu" and urun_tipi != tip:
                continue

            # Stok ve anlasma bilgisi goster
            etiketler = []
            stok = self._urun_stok.get(urun_id)
            if stok and stok['miktar'] > 0:
                etiketler.append(f"Stok:{stok['miktar']:.0f}")
            anlasma = self._anlasma_fiyat.get(urun_id)
            if anlasma:
                etiketler.append(f"{anlasma.get('para_birimi', 'TRY')} {anlasma['fiyat']:.2f}")

            suffix = f" ({', '.join(etiketler)})" if etiketler else ""
            self.cmb_urun.addItem(f"{kod} - {ad}{suffix}", urun_id)

        self.cmb_urun.blockSignals(False)

    def _on_urun_changed(self, index):
        urun_id = self.cmb_urun.currentData()
        if not urun_id:
            self.lbl_stok.setText("-")
            self.lbl_anlasma.setText("-")
            return

        text = self.cmb_urun.currentText()
        if " - " in text:
            ad = text.split(" - ", 1)[1].split(" (")[0]
            self.txt_urun_adi.setText(ad)

        # Stok goster
        stok = self._urun_stok.get(urun_id)
        if stok and stok['miktar'] > 0:
            self.lbl_stok.setText(f"{stok['miktar']:.2f} {stok['birim']}")
            self.lbl_stok.setStyleSheet(f"color: {self.theme.get('success')}; font-size: 12px; font-weight: bold;")
        else:
            self.lbl_stok.setText("Stok yok")
            self.lbl_stok.setStyleSheet(f"color: {self.theme.get('danger')}; font-size: 12px; font-weight: bold;")

        # Anlasma fiyati goster ve otomatik doldur
        anlasma = self._anlasma_fiyat.get(urun_id)
        if anlasma:
            self.lbl_anlasma.setText(f"{anlasma.get('para_birimi', 'TRY')} {anlasma['fiyat']:.4f} (Anlasma)")
            self.spin_fiyat.setValue(anlasma['fiyat'])
        else:
            self.lbl_anlasma.setText("Anlasma fiyati yok")
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # para_birimi kolonunu kontrol et, yoksa ekle
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = 'satinalma' AND TABLE_NAME = 'talep_satirlari' AND COLUMN_NAME = 'para_birimi')
                ALTER TABLE satinalma.talep_satirlari ADD para_birimi NVARCHAR(10) DEFAULT 'TRY'
            """)
            conn.commit()
            cursor.execute("""
                SELECT urun_id, urun_adi, talep_miktar, birim, tahmini_birim_fiyat, aciklama, para_birimi
                FROM satinalma.talep_satirlari WHERE id = ?
            """, (self.satir_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                if row[0]:
                    idx = self.cmb_urun.findData(row[0])
                    if idx >= 0:
                        self.cmb_urun.setCurrentIndex(idx)
                self.txt_urun_adi.setText(row[1] or "")
                self.spin_miktar.setValue(float(row[2]) if row[2] else 1)
                idx = self.cmb_birim.findText(row[3] or "ADET")
                if idx >= 0:
                    self.cmb_birim.setCurrentIndex(idx)
                self.spin_fiyat.setValue(float(row[4]) if row[4] else 0)
                self.txt_aciklama.setPlainText(row[5] or "")
                if row[6]:
                    idx = self.cmb_para_birimi.findData(row[6])
                    if idx >= 0:
                        self.cmb_para_birimi.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        urun_adi = self.txt_urun_adi.text().strip()
        if not urun_adi:
            QMessageBox.warning(self, "Uyarı", "Ürün adı zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            urun_id = self.cmb_urun.currentData()
            miktar = self.spin_miktar.value()
            fiyat = self.spin_fiyat.value()
            tutar = miktar * fiyat if fiyat else None
            para_birimi = self.cmb_para_birimi.currentData() or 'TRY'

            # para_birimi kolonu yoksa ekle
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = 'satinalma' AND TABLE_NAME = 'talep_satirlari' AND COLUMN_NAME = 'para_birimi')
                ALTER TABLE satinalma.talep_satirlari ADD para_birimi NVARCHAR(10) DEFAULT 'TRY'
            """)

            if self.satir_id:
                cursor.execute("""
                    UPDATE satinalma.talep_satirlari SET
                        urun_id = ?, urun_adi = ?, talep_miktar = ?, birim = ?,
                        tahmini_birim_fiyat = ?, tahmini_tutar = ?, para_birimi = ?, aciklama = ?
                    WHERE id = ?
                """, (urun_id, urun_adi, miktar, self.cmb_birim.currentText(),
                      fiyat if fiyat else None, tutar, para_birimi,
                      self.txt_aciklama.toPlainText().strip() or None, self.satir_id))
            else:
                cursor.execute("SELECT ISNULL(MAX(satir_no), 0) + 1 FROM satinalma.talep_satirlari WHERE talep_id = ?", (self.talep_id,))
                satir_no = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO satinalma.talep_satirlari
                    (talep_id, satir_no, urun_id, urun_adi, talep_miktar, birim, tahmini_birim_fiyat, tahmini_tutar, para_birimi, aciklama)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.talep_id, satir_no, urun_id, urun_adi, miktar, self.cmb_birim.currentText(),
                      fiyat if fiyat else None, tutar, para_birimi, self.txt_aciklama.toPlainText().strip() or None))
            
            conn.commit()
            LogManager.log_insert('satinalma', 'satinalma.talep_satirlari', None, 'Talep kaydi olustu')
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class TalepDialog(QDialog):
    """Satınalma talebi oluşturma/düzenleme"""
    
    def __init__(self, theme: dict, parent=None, talep_id=None, kullanici_id=None):
        super().__init__(parent)
        self.theme = theme
        self.talep_id = talep_id
        self.kullanici_id = kullanici_id
        self.setWindowTitle("Satınalma Talebi" if not talep_id else "Talep Düzenle")
        self.setMinimumSize(900, 600)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        
        if talep_id:
            self._load_data()
            self._load_satirlar()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
            QTabWidget::pane {{ border: 1px solid {self.theme.get('border')}; }}
            QTabBar::tab {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 20px; }}
            QTabBar::tab:selected {{ background: {self.theme.get('primary')}; color: white; }}
        """)
        
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        
        # Tab 1: Genel
        tab_genel = QWidget()
        genel_layout = QFormLayout(tab_genel)
        
        self.txt_talep_no = QLineEdit()
        self.txt_talep_no.setReadOnly(True)
        self.txt_talep_no.setPlaceholderText("Otomatik oluşturulacak")
        genel_layout.addRow("Talep No:", self.txt_talep_no)
        
        # Talep Eden (Personel seçimi)
        self.cmb_talep_eden = QComboBox()
        self.cmb_talep_eden.setEditable(True)
        genel_layout.addRow("Talep Eden*:", self.cmb_talep_eden)
        
        self.date_tarih = QDateEdit()
        self.date_tarih.setDate(QDate.currentDate())
        self.date_tarih.setCalendarPopup(True)
        genel_layout.addRow("Tarih:", self.date_tarih)
        
        self.cmb_departman = QComboBox()
        genel_layout.addRow("Departman*:", self.cmb_departman)
        
        self.cmb_oncelik = QComboBox()
        self.cmb_oncelik.addItems(["DUSUK", "NORMAL", "YUKSEK", "ACIL"])
        self.cmb_oncelik.setCurrentText("NORMAL")
        genel_layout.addRow("Öncelik:", self.cmb_oncelik)
        
        self.date_termin = QDateEdit()
        self.date_termin.setDate(QDate.currentDate().addDays(14))
        self.date_termin.setCalendarPopup(True)
        genel_layout.addRow("İstenen Termin:", self.date_termin)
        
        # Tedarikci secimi (opsiyonel - fiyat ve stok bilgisi icin)
        self.cmb_tedarikci = QComboBox()
        self.cmb_tedarikci.setEditable(True)
        genel_layout.addRow("Tedarikci:", self.cmb_tedarikci)

        self.txt_neden = QTextEdit()
        self.txt_neden.setMaximumHeight(60)
        self.txt_neden.setPlaceholderText("Talep nedeni/aciklamasi")
        genel_layout.addRow("Talep Nedeni:", self.txt_neden)
        
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(60)
        genel_layout.addRow("Notlar:", self.txt_notlar)
        
        # Durum bilgisi
        durum_group = QGroupBox("Onay Durumu")
        durum_layout = QFormLayout()
        
        self.lbl_durum = QLabel("-")
        durum_layout.addRow("Talep Durumu:", self.lbl_durum)
        
        self.lbl_amir_onay = QLabel("-")
        durum_layout.addRow("Amir Onayı:", self.lbl_amir_onay)
        
        self.lbl_satinalma_onay = QLabel("-")
        durum_layout.addRow("Satın Alma Onayı:", self.lbl_satinalma_onay)
        
        durum_group.setLayout(durum_layout)
        genel_layout.addRow(durum_group)
        
        tabs.addTab(tab_genel, "📋 Genel Bilgiler")
        
        # Tab 2: Kalemler
        tab_kalemler = QWidget()
        kalem_layout = QVBoxLayout(tab_kalemler)
        
        toolbar = QHBoxLayout()
        btn_ekle = QPushButton("➕ Kalem Ekle")
        btn_ekle.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_ekle.clicked.connect(self._add_satir)
        toolbar.addWidget(btn_ekle)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._edit_satir)
        toolbar.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._delete_satir)
        toolbar.addWidget(btn_sil)
        
        toolbar.addStretch()
        self.lbl_toplam = QLabel("Tahmini Toplam: 0.00")
        self.lbl_toplam.setStyleSheet(f"font-weight: bold; color: {self.theme.get('text')};")
        toolbar.addWidget(self.lbl_toplam)
        kalem_layout.addLayout(toolbar)
        
        self.table_satirlar = QTableWidget()
        self.table_satirlar.setColumnCount(8)
        self.table_satirlar.setHorizontalHeaderLabels(["ID", "Sıra", "Ürün Adı", "Miktar", "Birim", "Birim Fiyat", "P.Birimi", "Tutar"])
        self.table_satirlar.setColumnHidden(0, True)
        self.table_satirlar.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_satirlar.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; color: {self.theme.get('text')}; }}
            QHeaderView::section {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px; }}
        """)
        header = self.table_satirlar.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_satirlar.setColumnWidth(1, 60)
        self.table_satirlar.setColumnWidth(3, 80)
        self.table_satirlar.setColumnWidth(4, 60)
        self.table_satirlar.setColumnWidth(5, 100)
        self.table_satirlar.setColumnWidth(6, 100)
        kalem_layout.addWidget(self.table_satirlar)
        
        tabs.addTab(tab_kalemler, "📦 Talep Kalemleri")
        
        layout.addWidget(tabs)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_yazdir = QPushButton("🖨️ Yazdır")
        btn_yazdir.setStyleSheet(f"background: {self.theme.get('info')}; color: white; padding: 10px 24px; border-radius: 6px;")
        btn_yazdir.clicked.connect(self._print_talep)
        btn_layout.addWidget(btn_yazdir)
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 24px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        self.btn_onaya = QPushButton("📤 Onaya Gönder")
        self.btn_onaya.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; padding: 10px 24px; border-radius: 6px;")
        self.btn_onaya.clicked.connect(self._send_approval)
        self.btn_onaya.setVisible(False)  # İlk başta gizli
        btn_layout.addWidget(self.btn_onaya)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Departmanları yükle
            self.cmb_departman.addItem("-- Departman Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_departman.addItem(f"{row[1]} - {row[2]}", row[0])
            
            # PERSONEL LİSTESİ - Direkt personeller tablosundan çek
            self.cmb_talep_eden.addItem("-- Talep Eden Seçiniz --", None)
            cursor.execute("""
                SELECT p.id, p.ad, p.soyad, p.sicil_no, d.ad as departman
                FROM ik.personeller p
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                WHERE p.aktif_mi = 1
                ORDER BY p.ad, p.soyad
            """)
            for row in cursor.fetchall():
                personel_id = row[0]
                ad = row[1] or ""
                soyad = row[2] or ""
                sicil = row[3] or ""
                departman = row[4] or ""
                
                # Label oluştur
                label = f"{ad} {soyad}"
                if sicil:
                    label += f" ({sicil})"
                if departman:
                    label += f" - {departman}"
                
                self.cmb_talep_eden.addItem(label, personel_id)
            
            # Mevcut kullanıcının personel_id'sini bul ve seç
            if self.kullanici_id:
                cursor.execute("""
                    SELECT personel_id 
                    FROM sistem.kullanicilar 
                    WHERE id = ? AND personel_id IS NOT NULL
                """, (self.kullanici_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    personel_id = row[0]
                    # Combo'da bu personel_id'yi bul
                    for i in range(self.cmb_talep_eden.count()):
                        if self.cmb_talep_eden.itemData(i) == personel_id:
                            self.cmb_talep_eden.setCurrentIndex(i)
                            break

            # Tedarikciler
            self.cmb_tedarikci.addItem("-- Tedarikci (Opsiyonel) --", None)
            cursor.execute("""
                SELECT id, cari_kodu, unvan FROM musteri.cariler
                WHERE cari_tipi IN ('TEDARIKCI', 'HER_IKISI') AND aktif_mi = 1
                ORDER BY unvan
            """)
            for row in cursor.fetchall():
                self.cmb_tedarikci.addItem(f"{row[1]} - {row[2]}", row[0])

            conn.close()
        except Exception as e:
            print(f"Combo yukleme hatasi: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Hata", f"Personel listesi yüklenemedi:\n{str(e)}")
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT talep_no, tarih, talep_eden_id, departman_id, oncelik, istenen_termin, talep_nedeni, notlar, 
                       durum, amir_onay_durumu, satinalma_onay_durumu
                FROM satinalma.talepler WHERE id = ?
            """, (self.talep_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_talep_no.setText(row[0] or "")
                if row[1]:
                    self.date_tarih.setDate(QDate(row[1].year, row[1].month, row[1].day))
                # Talep eden seç
                if row[2]:
                    idx = self.cmb_talep_eden.findData(row[2])
                    if idx >= 0:
                        self.cmb_talep_eden.setCurrentIndex(idx)
                # Departman seç
                if row[3]:
                    idx = self.cmb_departman.findData(row[3])
                    if idx >= 0:
                        self.cmb_departman.setCurrentIndex(idx)
                if row[4]:
                    idx = self.cmb_oncelik.findText(row[4])
                    if idx >= 0:
                        self.cmb_oncelik.setCurrentIndex(idx)
                if row[5]:
                    self.date_termin.setDate(QDate(row[5].year, row[5].month, row[5].day))
                self.txt_neden.setPlainText(row[6] or "")
                self.txt_notlar.setPlainText(row[7] or "")
                
                # Durum bilgilerini güncelle
                durum = row[8] or "TASLAK"
                self.lbl_durum.setText(durum)
                self.lbl_durum.setStyleSheet(f"color: {self._get_durum_color(durum)}; font-weight: bold;")
                
                amir_onay = row[9] or "-"
                self.lbl_amir_onay.setText(amir_onay)
                self.lbl_amir_onay.setStyleSheet(f"color: {self._get_onay_color(amir_onay)}; font-weight: bold;")
                
                satinalma_onay = row[10] or "-"
                self.lbl_satinalma_onay.setText(satinalma_onay)
                self.lbl_satinalma_onay.setStyleSheet(f"color: {self._get_onay_color(satinalma_onay)}; font-weight: bold;")
                
                # Onaya gönder butonunu göster/gizle
                if durum == "TASLAK":
                    self.btn_onaya.setVisible(True)
                else:
                    self.btn_onaya.setVisible(False)
                    
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _get_durum_color(self, durum):
        colors = {
            'TASLAK': self.theme.get('text_muted'),
            'ONAY_BEKLIYOR': self.theme.get('warning'),
            'AMIR_ONAYLADI': self.theme.get('info'),
            'SATINALMA_ONAYLANDI': self.theme.get('success'),
            'REDDEDILDI': self.theme.get('danger'),
        }
        return colors.get(durum, self.theme.get('text'))
    
    def _get_onay_color(self, onay):
        if onay == "ONAYLANDI":
            return self.theme.get('success')
        elif onay == "REDDEDILDI":
            return self.theme.get('danger')
        return self.theme.get('text_muted')
    
    def _load_satirlar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # para_birimi kolonu yoksa ekle
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = 'satinalma' AND TABLE_NAME = 'talep_satirlari' AND COLUMN_NAME = 'para_birimi')
                ALTER TABLE satinalma.talep_satirlari ADD para_birimi NVARCHAR(10) DEFAULT 'TRY'
            """)
            conn.commit()
            cursor.execute("""
                SELECT id, satir_no, urun_adi, talep_miktar, birim, tahmini_birim_fiyat, ISNULL(para_birimi, 'TRY'), tahmini_tutar
                FROM satinalma.talep_satirlari WHERE talep_id = ? ORDER BY satir_no
            """, (self.talep_id,))
            rows = cursor.fetchall()
            conn.close()

            self.table_satirlar.setRowCount(len(rows))
            toplam = 0

            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    if j == 5 and val:  # Birim fiyat
                        item = QTableWidgetItem(f"{val:,.4f}")
                    elif j == 7 and val:  # Tutar
                        pb = row[6] or 'TRY'
                        item = QTableWidgetItem(f"{val:,.2f} {pb}")
                        toplam += val
                    else:
                        item = QTableWidgetItem(str(val) if val else "")
                    self.table_satirlar.setItem(i, j, item)

            # Para birimi belirle (ilk satirdan)
            pb_text = ''
            if rows:
                pb_text = f" {rows[0][6]}" if rows[0][6] else ''
            self.lbl_toplam.setText(f"Tahmini Toplam: {toplam:,.2f}{pb_text}")
        except Exception as e:
            print(f"Satır yükleme hatası: {e}")
    
    def _add_satir(self):
        if not self.talep_id:
            QMessageBox.warning(self, "Uyarı", "Önce talebi kaydedin!")
            return
        
        tedarikci_id = self.cmb_tedarikci.currentData() if hasattr(self, 'cmb_tedarikci') else None
        dialog = TalepSatirDialog(self.theme, self.talep_id, self, tedarikci_id=tedarikci_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
            self._update_talep_tutar()

    def _edit_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Bir satir secin!")
            return

        satir_id = int(self.table_satirlar.item(row, 0).text())
        tedarikci_id = self.cmb_tedarikci.currentData() if hasattr(self, 'cmb_tedarikci') else None
        dialog = TalepSatirDialog(self.theme, self.talep_id, self, satir_id, tedarikci_id=tedarikci_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
            self._update_talep_tutar()
    
    def _delete_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir satır seçin!")
            return
        
        satir_id = int(self.table_satirlar.item(row, 0).text())
        reply = QMessageBox.question(self, "Onay", "Bu satırı silmek istediğinize emin misiniz?", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM satinalma.talep_satirlari WHERE id = ?", (satir_id,))
                conn.commit()
                LogManager.log_delete('satinalma', 'satinalma.talep_satirlari', None, 'Kayit silindi')
                conn.close()
                self._load_satirlar()
                self._update_talep_tutar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _update_talep_tutar(self):
        """Talep toplam tutarını güncelle"""
        if not self.talep_id:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE satinalma.talepler 
                SET tahmini_tutar = (
                    SELECT SUM(ISNULL(tahmini_tutar, 0)) 
                    FROM satinalma.talep_satirlari 
                    WHERE talep_id = ?
                ),
                guncelleme_tarihi = GETDATE()
                WHERE id = ?
            """, (self.talep_id, self.talep_id))
            conn.commit()
            LogManager.log_update('satinalma', 'satinalma.talepler', None, 'Kayit guncellendi')
            conn.close()
        except Exception as e:
            print(f"Tutar güncelleme hatası: {e}")
    
    def _save(self):
        # Talep eden kontrolü
        talep_eden_id = self.cmb_talep_eden.currentData()
        if not talep_eden_id:
            QMessageBox.warning(self, "Uyarı", "Talep eden seçiniz!")
            return
        
        # Departman kontrolü
        departman_id = self.cmb_departman.currentData()
        if not departman_id:
            QMessageBox.warning(self, "Uyarı", "Departman seçiniz!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            tarih = self.date_tarih.date().toPython()
            termin = self.date_termin.date().toPython()
            
            if self.talep_id:
                # Güncelleme
                cursor.execute("""
                    UPDATE satinalma.talepler SET
                        tarih = ?, talep_eden_id = ?, departman_id = ?, oncelik = ?, istenen_termin = ?,
                        talep_nedeni = ?, notlar = ?, guncelleme_tarihi = GETDATE(),
                        guncelleyen_id = ?
                    WHERE id = ?
                """, (tarih, talep_eden_id, departman_id, self.cmb_oncelik.currentText(), termin,
                      self.txt_neden.toPlainText().strip() or None,
                      self.txt_notlar.toPlainText().strip() or None,
                      self.kullanici_id, self.talep_id))
            else:
                # Yeni talep
                # Talep numarası oluştur
                tarih_str = datetime.now().strftime('%Y%m%d')
                cursor.execute("""
                    SELECT ISNULL(MAX(CAST(RIGHT(talep_no, 4) AS INT)), 0) + 1
                    FROM satinalma.talepler
                    WHERE talep_no LIKE ?
                """, (f"TLP-{tarih_str}-%",))
                sira = cursor.fetchone()[0]
                talep_no = f"TLP-{tarih_str}-{sira:04d}"
                
                cursor.execute("""
                    INSERT INTO satinalma.talepler 
                    (talep_no, tarih, talep_eden_id, departman_id, oncelik, istenen_termin,
                     talep_nedeni, notlar, durum, olusturan_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'TASLAK', ?)
                """, (talep_no, tarih, talep_eden_id, departman_id, 
                      self.cmb_oncelik.currentText(), termin,
                      self.txt_neden.toPlainText().strip() or None,
                      self.txt_notlar.toPlainText().strip() or None,
                      self.kullanici_id))
                
                # Yeni ID'yi al
                cursor.execute("SELECT @@IDENTITY")
                self.talep_id = cursor.fetchone()[0]
                self.txt_talep_no.setText(talep_no)
                self.btn_onaya.setVisible(True)  # Onaya gönder butonunu göster
            
            conn.commit()
            LogManager.log_insert('satinalma', 'satinalma.talepler', None, 'Talep kaydi olustu')
            conn.close()
            
            QMessageBox.information(self, "Başarılı", "Talep kaydedildi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _send_approval(self):
        """Talebi onaya gönder"""
        if not self.talep_id:
            QMessageBox.warning(self, "Uyarı", "Önce talebi kaydedin!")
            return
        
        # Satır kontrolü
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM satinalma.talep_satirlari WHERE talep_id = ?", (self.talep_id,))
            satir_sayisi = cursor.fetchone()[0]
            
            if satir_sayisi == 0:
                QMessageBox.warning(self, "Uyarı", "Onaya göndermek için en az bir kalem eklemelisiniz!")
                conn.close()
                return
            
            # Onay prosedürünü çağır
            reply = QMessageBox.question(
                self, "Onay", 
                "Bu talebi onaya göndermek istediğinize emin misiniz?\n\n"
                "Onaya gönderildikten sonra değişiklik yapamazsınız.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor.execute("EXEC satinalma.sp_TalepOnayaGonder ?, ?", (self.talep_id, self.kullanici_id))
                conn.commit()
                LogManager.log_update('satinalma', 'satinalma.sp_TalepOnayaGonder', None, 'satinalma.sp_TalepOnayaGonder islemi yapildi')
                conn.close()
                
                QMessageBox.information(
                    self, "Başarılı", 
                    "Talep onaya gönderildi!\n\n"
                    "Yetkili kişilere bildirim gönderildi."
                )
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Onaya gönderme hatası: {str(e)}")
    
    def _print_talep(self):
        """Talebi yazdır"""
        if not self.talep_id:
            QMessageBox.warning(self, "Uyarı", "Önce talebi kaydedin!")
            return
        
        try:
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec() == QDialog.Accepted:
                # HTML formatında talep formu oluştur
                html = self._generate_talep_html()
                
                document = QTextDocument()
                document.setHtml(html)
                
                # QPainter kullanarak yazdır
                painter = QPainter(printer)
                document.drawContents(painter)
                painter.end()
                
                QMessageBox.information(self, "Başarılı", "Talep yazdırıldı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yazdırma hatası: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _generate_talep_html(self):
        """Talep formu HTML'i oluştur - Resmi format"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Talep bilgilerini al
            cursor.execute("""
                SELECT t.talep_no, t.tarih, t.oncelik, t.istenen_termin, t.talep_nedeni,
                       d.ad as departman, p.ad + ' ' + p.soyad as talep_eden, t.tahmini_tutar,
                       t.durum, t.amir_onay_durumu, t.satinalma_onay_durumu
                FROM satinalma.talepler t
                LEFT JOIN ik.departmanlar d ON t.departman_id = d.id
                LEFT JOIN ik.personeller p ON t.talep_eden_id = p.id
                WHERE t.id = ?
            """, (self.talep_id,))
            talep = cursor.fetchone()
            
            # Satırları al
            cursor.execute("""
                SELECT satir_no, urun_adi, urun_kodu, talep_miktar, birim, aciklama
                FROM satinalma.talep_satirlari
                WHERE talep_id = ?
                ORDER BY satir_no
            """, (self.talep_id,))
            satirlar = cursor.fetchall()
            conn.close()
            
            # Tarih formatı
            tarih_str = talep[1].strftime('%d/%m/%Y') if talep[1] else '..../...../ 200'
            termin_str = talep[3].strftime('%d/%m/%Y') if talep[3] else ''
            
            # HTML - Resmi form formatı
            html = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{
                        size: A4;
                        margin: 15mm;
                    }}
                    body {{
                        font-family: Arial, sans-serif;
                        font-size: 10pt;
                        margin: 0;
                        padding: 0;
                    }}
                    .header-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 10px;
                    }}
                    .header-table td {{
                        border: 2px solid #000;
                        padding: 10px;
                        text-align: center;
                        font-weight: bold;
                    }}
                    .header-table .logo {{
                        width: 35%;
                        font-size: 14pt;
                    }}
                    .header-table .title {{
                        width: 35%;
                        font-size: 14pt;
                    }}
                    .header-table .date {{
                        width: 30%;
                        font-size: 10pt;
                    }}
                    .section-title {{
                        font-weight: bold;
                        font-size: 11pt;
                        margin-top: 15px;
                        margin-bottom: 5px;
                    }}
                    .content-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 10px;
                    }}
                    .content-table th,
                    .content-table td {{
                        border: 1px solid #000;
                        padding: 6px 4px;
                        font-size: 9pt;
                        text-align: left;
                        vertical-align: top;
                    }}
                    .content-table th {{
                        background-color: #f0f0f0;
                        font-weight: bold;
                        text-align: center;
                    }}
                    .content-table .sira {{
                        width: 30px;
                        text-align: center;
                    }}
                    .content-table .malzeme {{
                        width: 25%;
                    }}
                    .content-table .teknik {{
                        width: 20%;
                    }}
                    .content-table .miktar {{
                        width: 80px;
                        text-align: center;
                    }}
                    .content-table .tarih {{
                        width: 90px;
                        text-align: center;
                    }}
                    .content-table .aciklama {{
                        width: auto;
                    }}
                    .signature-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                    }}
                    .signature-table td {{
                        border: 1px solid #000;
                        padding: 40px 10px 10px 10px;
                        text-align: center;
                        font-weight: bold;
                        width: 33.33%;
                    }}
                    .footer {{
                        margin-top: 10px;
                        font-size: 8pt;
                        display: flex;
                        justify-content: space-between;
                    }}
                </style>
            </head>
            <body>
                <!-- Başlık -->
                <table class="header-table">
                    <tr>
                        <td class="logo">FİRMA<br/>LOGO</td>
                        <td class="title">SATINALMA<br/>TALEP<br/>FORMU</td>
                        <td class="date">
                            TARİH: {tarih_str}<br/><br/>
                            SIRA NO: {talep[0] or ''}
                        </td>
                    </tr>
                </table>
                
                <!-- Talep Eden Bölüm -->
                <div class="section-title">TALEP EDEN BÖLÜM:</div>
                <div style="margin-bottom: 10px; padding: 5px; border: 1px solid #ccc;">
                    <strong>Departman:</strong> {talep[5] or ''} &nbsp;&nbsp;&nbsp;
                    <strong>Talep Eden:</strong> {talep[6] or ''} &nbsp;&nbsp;&nbsp;
                    <strong>İstenen Termin:</strong> {termin_str}
                </div>
                
                <!-- Malzeme Listesi -->
                <table class="content-table">
                    <thead>
                        <tr>
                            <th class="sira">S/N</th>
                            <th class="malzeme">MALZEMENİN CİNSİ</th>
                            <th class="teknik">TEKNİK ÖZELLİK<br/>LOT/KOD NO</th>
                            <th class="miktar">MİKTAR</th>
                            <th class="tarih">İSTENİLEN<br/>TARİH</th>
                            <th class="aciklama">AÇIKLAMA</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Satırları ekle
            for i in range(25):  # 25 satır (formda görünen)
                if i < len(satirlar):
                    satir = satirlar[i]
                    html += f"""
                        <tr>
                            <td class="sira">{satir[0]}</td>
                            <td class="malzeme">{satir[1] or ''}</td>
                            <td class="teknik">{satir[2] or ''}</td>
                            <td class="miktar">{satir[3]} {satir[4]}</td>
                            <td class="tarih">{termin_str}</td>
                            <td class="aciklama">{satir[5] or ''}</td>
                        </tr>
                    """
                else:
                    html += f"""
                        <tr>
                            <td class="sira">{i+1}</td>
                            <td class="malzeme">&nbsp;</td>
                            <td class="teknik">&nbsp;</td>
                            <td class="miktar">&nbsp;</td>
                            <td class="tarih">&nbsp;</td>
                            <td class="aciklama">&nbsp;</td>
                        </tr>
                    """
            
            html += """
                    </tbody>
                </table>
                
                <!-- Onay Bölümü -->
                <div class="section-title">ONAY SONUCU:</div>
                <table class="signature-table">
                    <tr>
                        <td>TALEP EDEN/KİSİM AMİRİ<br/>TARİH/İMZA</td>
                        <td>ONAY<br/>TARİH/İMZA</td>
                        <td>SATINALMA<br/>TARİH/İMZA</td>
                    </tr>
                </table>
                
                <!-- Footer -->
                <div class="footer">
                    <span>FORM NO.:</span>
                    <span>REV.NO.:</span>
                    <span>REV.TAR.:</span>
                    <span>İLK YAY.TAR.:</span>
                </div>
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            print(f"HTML oluşturma hatası: {e}")
            import traceback
            traceback.print_exc()
            return "<html><body><h1>Hata: Form oluşturulamadı</h1></body></html>"
    

class SatinalmaTaleplerPage(BasePage):
    """Satınalma Talepleri Ana Sayfa"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.kullanici_id = 1  # Varsayılan kullanıcı
        self.all_rows = []
        self.has_approval_authority = True  # Herkes onaylayabilir
        self._setup_ui()
        self._load_data()
    
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Başlık
        header = QLabel("📋 Satınalma Talepleri")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px; padding: 12px;")
        toolbar_layout = QHBoxLayout(toolbar)
        
        btn_yeni = QPushButton("➕ Yeni Talep")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)

        # Onay butonları - BU SAYFAYI GÖREBİLİYORSANIZ ZATEN YETKİNİZ VAR
        # Menü yetkileri zaten kontrol ediyor
        btn_onayla = QPushButton("✅ Onayla")
        btn_onayla.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_onayla.clicked.connect(self._onayla)
        toolbar_layout.addWidget(btn_onayla)

        btn_reddet = QPushButton("❌ Reddet")
        btn_reddet.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_reddet.clicked.connect(self._reddet)
        toolbar_layout.addWidget(btn_reddet)

        btn_yazdir = QPushButton("Yazdir")
        btn_yazdir.setStyleSheet(f"background: {self.theme.get('info')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_yazdir.clicked.connect(lambda: self._yazdir())
        toolbar_layout.addWidget(btn_yazdir)

        btn_siparise = QPushButton("Siparise Donustur")
        btn_siparise.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_siparise.clicked.connect(self._siparise_donustur)
        toolbar_layout.addWidget(btn_siparise)

        toolbar_layout.addStretch()

        toolbar_layout.addWidget(self.create_export_button(title="Satinalma Talepleri"))

        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tümü", "TASLAK", "ONAY_BEKLIYOR", "AMIR_ONAYLADI", 
                                 "SATINALMA_ONAYLANDI", "REDDEDILDI"])
        self.cmb_durum.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px; color: {self.theme.get('text')};")
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_durum)
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 16px; color: {self.theme.get('text')};")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels(["ID", "Talep No", "Tarih", "Departman", "Talep Eden", "Oncelik", "Tahmini Tutar", "Durum", "Amir Onay", "Onaylayan", "Islem"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; color: {self.theme.get('text')}; }}
            QTableWidget::item {{ padding: 8px; }}
            QTableWidget::item:selected {{ background: {self.theme.get('primary')}; }}
            QHeaderView::section {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px; border: none; font-weight: bold; }}
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 150)
        self.table.setColumnWidth(7, 120)
        self.table.setColumnWidth(8, 120)

        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # TÜM TALEPLERİ GÖSTER (test için - sonra filtre ekleriz)
            cursor.execute("""
                SELECT t.id, t.talep_no, FORMAT(t.tarih, 'dd.MM.yyyy'),
                       d.ad, p.ad + ' ' + p.soyad as talep_eden,
                       t.oncelik, t.tahmini_tutar, t.durum, t.amir_onay_durumu,
                       po.ad + ' ' + po.soyad as onaylayan
                FROM satinalma.talepler t
                LEFT JOIN ik.departmanlar d ON t.departman_id = d.id
                LEFT JOIN ik.personeller p ON t.talep_eden_id = p.id
                LEFT JOIN ik.personeller po ON t.satinalma_onaylayan_id = po.id
                ORDER BY t.tarih DESC, t.id DESC
            """)
            
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        
        durum_colors = {
            'TASLAK': self.theme.get('text_muted'),
            'ONAY_BEKLIYOR': self.theme.get('warning'),
            'AMIR_ONAYLADI': self.theme.get('info'),
            'SATINALMA_ONAYLANDI': self.theme.get('success'),
            'REDDEDILDI': self.theme.get('danger'),
        }
        
        for i, row in enumerate(rows):
            # row: 0=id, 1=talep_no, 2=tarih, 3=departman, 4=talep_eden, 5=oncelik, 6=tutar, 7=durum, 8=amir_onay, 9=onaylayan
            for j, val in enumerate(row):
                if j == 6 and val:  # Tutar
                    item = QTableWidgetItem(f"{val:,.2f}")
                elif j == 7:  # Durum
                    item = QTableWidgetItem(str(val) if val else "")
                    item.setForeground(QColor(durum_colors.get(val, self.theme.get('text'))))
                elif j == 8:  # Amir onay
                    item = QTableWidgetItem(str(val) if val else "-")
                    if val == "ONAYLANDI":
                        item.setForeground(QColor(self.theme.get('success')))
                    elif val == "REDDEDILDI":
                        item.setForeground(QColor(self.theme.get('danger')))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)

            rid = row[0]
            widget = self.create_action_buttons([
                ("Duzenle", "Duzenle", lambda checked, rid=rid: self._duzenle_by_id(rid), "edit"),
            ])
            self.table.setCellWidget(i, 10, widget)
            self.table.setRowHeight(i, 42)

        self.lbl_stat.setText(f"Toplam: {len(rows)} talep")

    def _duzenle_by_id(self, talep_id):
        """ID ile talep düzenleme (satır butonundan)"""
        dialog = TalepDialog(self.theme, self, talep_id, self.kullanici_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _filter(self):
        durum = self.cmb_durum.currentText()
        if durum == "Tümü":
            self._display_data(self.all_rows)
        else:
            filtered = [r for r in self.all_rows if r[7] == durum]
            self._display_data(filtered)
    
    def _yeni(self):
        dialog = TalepDialog(self.theme, self, kullanici_id=self.kullanici_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir talep seçin!")
            return
        talep_id = int(self.table.item(row, 0).text())
        dialog = TalepDialog(self.theme, self, talep_id, self.kullanici_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _onayla(self):
        """Seçili talebi onayla"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir talep seçin!")
            return
        
        talep_id = int(self.table.item(row, 0).text())
        durum = self.table.item(row, 7).text()
        
        if durum not in ("ONAY_BEKLIYOR", "AMIR_ONAYLADI"):
            QMessageBox.warning(self, "Uyarı", "Sadece onay bekleyen talepler onaylanabilir!")
            return
        
        # Onay notu al
        from PySide6.QtWidgets import QInputDialog
        onay_notu, ok = QInputDialog.getMultiLineText(
            self, "Onay Notu", 
            "Onay notu (opsiyonel):"
        )
        
        if not ok:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("EXEC satinalma.sp_TalepOnayla ?, ?, ?", 
                          (talep_id, self.kullanici_id, onay_notu or None))
            conn.commit()
            LogManager.log_update('satinalma', 'satinalma.sp_TalepOnayla', None, 'satinalma.sp_TalepOnayla islemi yapildi')
            conn.close()
            
            self._load_data()
            QMessageBox.information(self, "Başarılı", "Talep onaylandı ve ilgili kişilere bildirim gönderildi!")
            self._yazdir(talep_id)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Onaylama hatası: {str(e)}")

    def _yazdir(self, talep_id: int = None):
        """Satinalma talep formunu PDF olarak yazdir"""
        if talep_id is None:
            row = self.table.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Uyarı", "Bir talep seçin!")
                return
            talep_id = int(self.table.item(row, 0).text())
        try:
            from utils.satinalma_talep_pdf import satinalma_talep_pdf
            satinalma_talep_pdf(talep_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF olusturulamadi: {e}")
    
    def _siparise_donustur(self):
        """Onaylanan talebi satin alma siparisine donustur"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Bir talep secin!")
            return

        talep_id = int(self.table.item(row, 0).text())

        # DB'den gercek durumu kontrol et (tablo gorunumune guvenme)
        try:
            conn_chk = get_db_connection()
            cursor_chk = conn_chk.cursor()
            cursor_chk.execute("SELECT durum FROM satinalma.talepler WHERE id = ?", (talep_id,))
            db_durum = cursor_chk.fetchone()
            conn_chk.close()
            if not db_durum or db_durum[0] not in ("SATINALMA_ONAYLANDI", "AMIR_ONAYLADI", "ONAY_BEKLIYOR"):
                QMessageBox.warning(self, "Uyari", f"Bu talep siparise donusturulemez!\nDurum: {db_durum[0] if db_durum else 'Bilinmiyor'}")
                return
        except Exception:
            pass

        # Tedarikci secimi - Siparis icin zorunlu
        from PySide6.QtWidgets import QInputDialog
        try:
            conn_t = get_db_connection()
            cursor_t = conn_t.cursor()
            cursor_t.execute("SELECT id, unvan FROM musteri.cariler WHERE cari_tipi IN ('TEDARIKCI', 'TEDARIKCI_MUSTERI') AND aktif_mi = 1 ORDER BY unvan")
            tedarikci_rows = cursor_t.fetchall()
            conn_t.close()
        except Exception:
            tedarikci_rows = []

        if not tedarikci_rows:
            QMessageBox.warning(self, "Uyari", "Tanimli tedarikci bulunamadi!")
            return

        tedarikci_listesi = [f"{r[1]}" for r in tedarikci_rows]
        secim, ok = QInputDialog.getItem(self, "Tedarikci Sec", "Siparis icin tedarikci secin:", tedarikci_listesi, 0, False)
        if not ok:
            return

        secilen_idx = tedarikci_listesi.index(secim)
        tedarikci_id = tedarikci_rows[secilen_idx][0]

        reply = QMessageBox.question(self, "Siparis Olustur",
                                     f"Tedarikci: {secim}\n\nBu talep satirlari siparis formuna aktarilacak. Devam edilsin mi?")
        if reply != QMessageBox.Yes:
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Talep bilgilerini al
            cursor.execute("""
                SELECT t.departman_id, t.istenen_termin, t.notlar
                FROM satinalma.talepler t WHERE t.id = ?
            """, (talep_id,))
            talep = cursor.fetchone()

            # Siparis no olustur
            cursor.execute("""
                SELECT ISNULL(MAX(CAST(RIGHT(siparis_no, 4) AS INT)), 0) + 1
                FROM satinalma.siparisler
                WHERE siparis_no LIKE ?
            """, (f"SIP-{datetime.now().strftime('%Y%m%d')}-%",))
            sira = cursor.fetchone()[0]
            siparis_no = f"SIP-{datetime.now().strftime('%Y%m%d')}-{sira:04d}"

            # Siparis olustur - tedarikci_id ile
            notlar_text = talep[2] or f"Talep #{talep_id}"
            if len(str(notlar_text)) > 500:
                notlar_text = str(notlar_text)[:500]
            print(f"[SIPARIS DEBUG] no={siparis_no} ted={tedarikci_id} termin={talep[1]} notlar_len={len(str(notlar_text))}")
            cursor.execute("""
                INSERT INTO satinalma.siparisler
                    (siparis_no, tarih, tedarikci_id, istenen_teslim_tarihi, notlar, durum)
                OUTPUT INSERTED.id
                VALUES (?, GETDATE(), ?, ?, ?, 'TASLAK')
            """, (siparis_no, tedarikci_id, talep[1], notlar_text))
            siparis_id = int(cursor.fetchone()[0])

            # Talep satirlarini siparis satirlarina aktar
            cursor.execute("""
                SELECT satir_no, urun_id, urun_adi, talep_miktar, birim,
                       tahmini_birim_fiyat, tahmini_tutar, aciklama
                FROM satinalma.talep_satirlari WHERE talep_id = ?
                ORDER BY satir_no
            """, (talep_id,))
            satirlar = cursor.fetchall()

            for s in satirlar:
                fiyat = float(s[5]) if s[5] else 0
                miktar = float(s[3]) if s[3] else 0
                tutar = fiyat * miktar
                kdv_orani = 20.0
                kdv_tutari = tutar * kdv_orani / 100
                toplam = tutar + kdv_tutari
                urun_adi = str(s[2] or '')[:200]
                birim = str(s[4] or 'ADET')[:20]
                aciklama = str(s[7] or '')[:500] if s[7] else None

                print(f"[SATIR DEBUG] urun_adi({len(urun_adi)})={urun_adi[:30]} birim({len(birim)})={birim} aciklama={len(str(aciklama)) if aciklama else 0}")

                cursor.execute("""
                    INSERT INTO satinalma.siparis_satirlari
                        (siparis_id, satir_no, urun_id, urun_adi, siparis_miktar,
                         birim, birim_fiyat, tutar, kdv_orani, kdv_tutari, toplam, aciklama)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (siparis_id, s[0], s[1], urun_adi, miktar,
                      birim, fiyat, tutar, kdv_orani, kdv_tutari, toplam, aciklama))

            # Siparis toplamlarini guncelle
            cursor.execute("""
                UPDATE satinalma.siparisler SET
                    ara_toplam = (SELECT ISNULL(SUM(tutar), 0) FROM satinalma.siparis_satirlari WHERE siparis_id = ?),
                    kdv_toplam = (SELECT ISNULL(SUM(kdv_tutari), 0) FROM satinalma.siparis_satirlari WHERE siparis_id = ?),
                    genel_toplam = (SELECT ISNULL(SUM(toplam), 0) FROM satinalma.siparis_satirlari WHERE siparis_id = ?)
                WHERE id = ?
            """, (siparis_id, siparis_id, siparis_id, siparis_id))

            # Talep satirlarini siparis ile iliskilendir
            print(f"[UPDATE DEBUG] siparis_id={siparis_id} type={type(siparis_id)} talep_id={talep_id} type={type(talep_id)}")
            cursor.execute("""
                UPDATE satinalma.talep_satirlari
                SET siparis_id = ?, siparis_durumu = ?
                WHERE talep_id = ?
            """, (int(siparis_id), 'SIPARIS_DONUSTU', int(talep_id)))

            conn.commit()
            LogManager.log_insert('satinalma', 'satinalma.siparisler', siparis_id,
                                  f'Talep #{talep_id} siparise donusturuldu: {siparis_no}')
            conn.close()

            QMessageBox.information(self, "Basarili",
                                    f"Siparis olusturuldu!\n\nSiparis No: {siparis_no}\n"
                                    f"Aktarilan kalem: {len(satirlar)}\n\n"
                                    "Satinalma Siparisleri sayfasindan duzenleyebilirsiniz.")
            self._load_data()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Siparis olusturma hatasi: {e}")

    def _reddet(self):
        """Secili talebi reddet"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Bir talep secin!")
            return
        
        talep_id = int(self.table.item(row, 0).text())
        durum = self.table.item(row, 7).text()
        
        if durum not in ("ONAY_BEKLIYOR", "AMIR_ONAYLADI"):
            QMessageBox.warning(self, "Uyarı", "Sadece onay bekleyen talepler reddedilebilir!")
            return
        
        # Red nedeni al
        from PySide6.QtWidgets import QInputDialog
        red_nedeni, ok = QInputDialog.getMultiLineText(
            self, "Red Nedeni", 
            "Red nedeni (zorunlu):"
        )
        
        if not ok or not red_nedeni.strip():
            QMessageBox.warning(self, "Uyarı", "Red nedeni girilmeli!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("EXEC satinalma.sp_TalepReddet ?, ?, ?", 
                          (talep_id, self.kullanici_id, red_nedeni))
            conn.commit()
            LogManager.log_update('satinalma', 'satinalma.sp_TalepReddet', None, 'satinalma.sp_TalepReddet islemi yapildi')
            conn.close()
            
            self._load_data()
            QMessageBox.information(self, "Başarılı", "Talep reddedildi ve talep edene bildirim gönderildi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Reddetme hatası: {str(e)}")
