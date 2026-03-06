# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Kontrol Planı Yönetimi
kalite.kontrol_planlari ve kalite.kontrol_plan_satirlar tabloları
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QGroupBox, QDateEdit,
    QSpinBox, QTextEdit, QTabWidget, QSplitter
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class KontrolPlanSatirDialog(QDialog):
    """Kontrol planı satırı ekleme/düzenleme"""
    
    def __init__(self, theme: dict, plan_id: int, parent=None, satir_id=None):
        super().__init__(parent)
        self.theme = theme
        self.plan_id = plan_id
        self.satir_id = satir_id
        self.setWindowTitle("Kontrol Satırı Ekle" if not satir_id else "Kontrol Satırı Düzenle")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        self._setup_ui()
        
        if satir_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QSpinBox, QComboBox, QTextEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
            QGroupBox {{
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }}
            QCheckBox {{ color: {self.theme.get('text')}; }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        
        self.spin_sira = QSpinBox()
        self.spin_sira.setRange(1, 999)
        self.spin_sira.setValue(1)
        form.addRow("Sıra No*:", self.spin_sira)
        
        self.txt_operasyon = QLineEdit()
        self.txt_operasyon.setPlaceholderText("Örn: Kaplama, Paketleme, Montaj")
        form.addRow("Operasyon*:", self.txt_operasyon)
        
        self.txt_kontrol = QLineEdit()
        self.txt_kontrol.setPlaceholderText("Örn: Kaplama Kalınlığı, Görsel Kontrol")
        form.addRow("Kontrol Özelliği*:", self.txt_kontrol)
        
        self.txt_spesifikasyon = QLineEdit()
        self.txt_spesifikasyon.setPlaceholderText("Örn: 8-12 µm, Çizik/Çatlak yok")
        form.addRow("Spesifikasyon:", self.txt_spesifikasyon)
        
        # Min-Max
        minmax_layout = QHBoxLayout()
        self.txt_min = QLineEdit()
        self.txt_min.setPlaceholderText("Min")
        minmax_layout.addWidget(self.txt_min)
        minmax_layout.addWidget(QLabel("-"))
        self.txt_max = QLineEdit()
        self.txt_max.setPlaceholderText("Max")
        minmax_layout.addWidget(self.txt_max)
        form.addRow("Min - Max:", minmax_layout)
        
        self.txt_metod = QLineEdit()
        self.txt_metod.setPlaceholderText("Örn: XRF, Görsel, Kaliper")
        form.addRow("Ölçüm Metodu:", self.txt_metod)
        
        self.txt_cihaz = QLineEdit()
        self.txt_cihaz.setPlaceholderText("Örn: XRF-001, Kaliper-05")
        form.addRow("Ölçüm Cihazı:", self.txt_cihaz)
        
        self.txt_numune = QLineEdit()
        self.txt_numune.setPlaceholderText("Örn: 5 adet, %10, İlk parça")
        form.addRow("Numune Boyutu:", self.txt_numune)
        
        self.txt_frekans = QLineEdit()
        self.txt_frekans.setPlaceholderText("Örn: Her parti, Saatlik, Vardiya başı")
        form.addRow("Kontrol Frekansı:", self.txt_frekans)
        
        self.txt_reaksiyon = QTextEdit()
        self.txt_reaksiyon.setMaximumHeight(60)
        self.txt_reaksiyon.setPlaceholderText("Uygunsuzluk durumunda yapılacak işlem")
        form.addRow("Reaksiyon Planı:", self.txt_reaksiyon)
        
        self.txt_form = QLineEdit()
        self.txt_form.setPlaceholderText("Örn: FR-KAL-001")
        form.addRow("Kayıt Formu:", self.txt_form)
        
        # Checkbox'lar
        check_layout = QHBoxLayout()
        self.chk_kritik = QCheckBox("Kritik Özellik (CC)")
        self.chk_spc = QCheckBox("SPC Uygulanacak")
        check_layout.addWidget(self.chk_kritik)
        check_layout.addWidget(self.chk_spc)
        check_layout.addStretch()
        form.addRow("", check_layout)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 24px; border-radius: 6px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        """Mevcut satır verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sira_no, operasyon, kontrol_ozelligi, spesifikasyon,
                       min_deger, max_deger, olcum_metodu, olcum_cihazi,
                       numune_boyutu, frekans, reaksiyon_plani, kayit_formu,
                       kritik_mi, spc_uygulanacak_mi
                FROM kalite.kontrol_plan_satirlar WHERE id = ?
            """, (self.satir_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.spin_sira.setValue(row[0] or 1)
                self.txt_operasyon.setText(row[1] or "")
                self.txt_kontrol.setText(row[2] or "")
                self.txt_spesifikasyon.setText(row[3] or "")
                self.txt_min.setText(str(row[4]) if row[4] else "")
                self.txt_max.setText(str(row[5]) if row[5] else "")
                self.txt_metod.setText(row[6] or "")
                self.txt_cihaz.setText(row[7] or "")
                self.txt_numune.setText(row[8] or "")
                self.txt_frekans.setText(row[9] or "")
                self.txt_reaksiyon.setPlainText(row[10] or "")
                self.txt_form.setText(row[11] or "")
                self.chk_kritik.setChecked(row[12] or False)
                self.chk_spc.setChecked(row[13] or False)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _save(self):
        """Satırı kaydet"""
        operasyon = self.txt_operasyon.text().strip()
        kontrol = self.txt_kontrol.text().strip()
        
        if not operasyon or not kontrol:
            QMessageBox.warning(self, "Uyarı", "Operasyon ve Kontrol Özelliği zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            min_val = float(self.txt_min.text()) if self.txt_min.text().strip() else None
            max_val = float(self.txt_max.text()) if self.txt_max.text().strip() else None
            
            if self.satir_id:
                cursor.execute("""
                    UPDATE kalite.kontrol_plan_satirlar SET
                        sira_no = ?, operasyon = ?, kontrol_ozelligi = ?, spesifikasyon = ?,
                        min_deger = ?, max_deger = ?, olcum_metodu = ?, olcum_cihazi = ?,
                        numune_boyutu = ?, frekans = ?, reaksiyon_plani = ?, kayit_formu = ?,
                        kritik_mi = ?, spc_uygulanacak_mi = ?
                    WHERE id = ?
                """, (
                    self.spin_sira.value(), operasyon, kontrol,
                    self.txt_spesifikasyon.text().strip() or None,
                    min_val, max_val,
                    self.txt_metod.text().strip() or None,
                    self.txt_cihaz.text().strip() or None,
                    self.txt_numune.text().strip() or None,
                    self.txt_frekans.text().strip() or None,
                    self.txt_reaksiyon.toPlainText().strip() or None,
                    self.txt_form.text().strip() or None,
                    self.chk_kritik.isChecked(), self.chk_spc.isChecked(),
                    self.satir_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO kalite.kontrol_plan_satirlar
                    (plan_id, sira_no, operasyon, kontrol_ozelligi, spesifikasyon,
                     min_deger, max_deger, olcum_metodu, olcum_cihazi,
                     numune_boyutu, frekans, reaksiyon_plani, kayit_formu,
                     kritik_mi, spc_uygulanacak_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.plan_id, self.spin_sira.value(), operasyon, kontrol,
                    self.txt_spesifikasyon.text().strip() or None,
                    min_val, max_val,
                    self.txt_metod.text().strip() or None,
                    self.txt_cihaz.text().strip() or None,
                    self.txt_numune.text().strip() or None,
                    self.txt_frekans.text().strip() or None,
                    self.txt_reaksiyon.toPlainText().strip() or None,
                    self.txt_form.text().strip() or None,
                    self.chk_kritik.isChecked(), self.chk_spc.isChecked()
                ))
            
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class KontrolPlanDialog(QDialog):
    """Kontrol planı ekleme/düzenleme"""
    
    def __init__(self, theme: dict, parent=None, plan_id=None):
        super().__init__(parent)
        self.theme = theme
        self.plan_id = plan_id
        self.setWindowTitle("Kontrol Planı Ekle" if not plan_id else "Kontrol Planı Düzenle")
        self.setMinimumSize(900, 600)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        
        if plan_id:
            self._load_data()
            self._load_satirlar()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QSpinBox, QComboBox, QDateEdit, QTextEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
            QTabWidget::pane {{ border: 1px solid {self.theme.get('border')}; border-radius: 8px; }}
            QTabBar::tab {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
            QTabBar::tab:selected {{ background: {self.theme.get('primary')}; color: white; }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Tab 1: Genel Bilgiler
        tab_genel = QWidget()
        genel_layout = QFormLayout(tab_genel)
        genel_layout.setSpacing(12)
        
        self.txt_plan_no = QLineEdit()
        self.txt_plan_no.setPlaceholderText("Örn: CP-001, KP-2024-001")
        genel_layout.addRow("Plan No*:", self.txt_plan_no)
        
        self.spin_revizyon = QSpinBox()
        self.spin_revizyon.setRange(1, 99)
        self.spin_revizyon.setValue(1)
        genel_layout.addRow("Revizyon:", self.spin_revizyon)
        
        self.cmb_musteri = QComboBox()
        genel_layout.addRow("Müşteri:", self.cmb_musteri)
        
        self.cmb_urun = QComboBox()
        genel_layout.addRow("Ürün:", self.cmb_urun)
        
        self.cmb_kaplama = QComboBox()
        genel_layout.addRow("Kaplama Türü:", self.cmb_kaplama)
        
        self.date_baslangic = QDateEdit()
        self.date_baslangic.setDate(QDate.currentDate())
        self.date_baslangic.setCalendarPopup(True)
        genel_layout.addRow("Geçerlilik Başlangıç*:", self.date_baslangic)
        
        self.date_bitis = QDateEdit()
        self.date_bitis.setDate(QDate.currentDate().addYears(1))
        self.date_bitis.setCalendarPopup(True)
        genel_layout.addRow("Geçerlilik Bitiş:", self.date_bitis)
        
        self.cmb_hazirlayan = QComboBox()
        genel_layout.addRow("Hazırlayan:", self.cmb_hazirlayan)
        
        self.cmb_onaylayan = QComboBox()
        genel_layout.addRow("Onaylayan:", self.cmb_onaylayan)
        
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["TASLAK", "ONAY_BEKLIYOR", "ONAYLANDI", "IPTAL"])
        genel_layout.addRow("Durum:", self.cmb_durum)
        
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(80)
        genel_layout.addRow("Notlar:", self.txt_notlar)
        
        tabs.addTab(tab_genel, "📋 Genel Bilgiler")
        
        # Tab 2: Kontrol Satırları
        tab_satirlar = QWidget()
        satirlar_layout = QVBoxLayout(tab_satirlar)
        
        # Toolbar
        satir_toolbar = QHBoxLayout()
        btn_satir_ekle = QPushButton("➕ Satır Ekle")
        btn_satir_ekle.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_satir_ekle.clicked.connect(self._add_satir)
        satir_toolbar.addWidget(btn_satir_ekle)
        
        btn_satir_duzenle = QPushButton("✏️ Düzenle")
        btn_satir_duzenle.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_satir_duzenle.clicked.connect(self._edit_satir)
        satir_toolbar.addWidget(btn_satir_duzenle)
        
        btn_satir_sil = QPushButton("🗑️ Sil")
        btn_satir_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_satir_sil.clicked.connect(self._delete_satir)
        satir_toolbar.addWidget(btn_satir_sil)
        
        satir_toolbar.addStretch()
        satirlar_layout.addLayout(satir_toolbar)
        
        # Tablo
        self.table_satirlar = QTableWidget()
        self.table_satirlar.setColumnCount(9)
        self.table_satirlar.setHorizontalHeaderLabels([
            "ID", "Sıra", "Operasyon", "Kontrol Özelliği", "Spesifikasyon",
            "Metod", "Frekans", "Kritik", "SPC"
        ])
        self.table_satirlar.setColumnHidden(0, True)
        self.table_satirlar.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_satirlar.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 8px;
                border: none;
            }}
        """)
        header = self.table_satirlar.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        
        satirlar_layout.addWidget(self.table_satirlar)
        tabs.addTab(tab_satirlar, "📝 Kontrol Satırları")
        
        layout.addWidget(tabs)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 24px; border-radius: 6px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        """Combo listelerini doldur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Önce Müşteriler - StokKartlari'ndan benzersiz müşteriler
            self.cmb_musteri.addItem("-- Müşteri Seçiniz --", None)
            cursor.execute("""
                SELECT DISTINCT cari_unvani 
                FROM stok.urunler 
                WHERE cari_unvani IS NOT NULL AND cari_unvani <> ''
                ORDER BY cari_unvani
            """)
            for row in cursor.fetchall():
                self.cmb_musteri.addItem(row[0], row[0])
            
            # Müşteri değişince ürünleri güncelle
            self.cmb_musteri.currentIndexChanged.connect(self._on_musteri_changed)
            
            # Ürünler - boş başlar
            self.cmb_urun.addItem("-- Önce Müşteri Seçin --", None)
            
            # Kaplama türleri
            self.cmb_kaplama.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM tanim.kaplama_turleri WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_kaplama.addItem(f"{row[1]} - {row[2]}", row[0])
            
            # Personeller
            self.cmb_hazirlayan.addItem("-- Seçiniz --", None)
            self.cmb_onaylayan.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_hazirlayan.addItem(row[1], row[0])
                self.cmb_onaylayan.addItem(row[1], row[0])
            
            conn.close()
        except Exception as e:
            print(f"Combo yükleme hatası: {e}")
    
    def _on_musteri_changed(self):
        """Müşteri değiştiğinde ürünleri güncelle"""
        cari_unvani = self.cmb_musteri.currentData()
        self._load_urunler(cari_unvani)
    
    def _load_urunler(self, cari_unvani=None):
        """Seçilen müşteriye ait ürün listesi"""
        self.cmb_urun.clear()
        self.cmb_urun.addItem("-- Ürün Seçin --", None)
        if not cari_unvani:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # StokKartlari'ndan urun_kodu al, stok.urunler'den id'yi bul
            cursor.execute("""
                SELECT u.id, ISNULL(s.urun_kodu, '') + ' - ' + ISNULL(s.urun_adi, '') 
                FROM stok.urunler s
                LEFT JOIN stok.urunler u ON u.urun_kodu = s.stok_kodu
                WHERE s.cari_unvani = ? AND ISNULL(s.aktif, 1) = 1
                ORDER BY s.stok_kodu
            """, (cari_unvani,))
            for row in cursor.fetchall():
                if row[0]:
                    self.cmb_urun.addItem(row[1], row[0])
            conn.close()
        except:
            pass
    
    def _load_data(self):
        """Plan verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kp.plan_no, kp.revizyon, kp.urun_id, kp.kaplama_turu_id, kp.cari_id,
                       kp.gecerlilik_baslangic, kp.gecerlilik_bitis,
                       kp.hazirlayan_id, kp.onaylayan_id, kp.durum, kp.notlar, c.unvan
                FROM kalite.kontrol_planlari kp
                LEFT JOIN musteri.cariler c ON kp.cari_id = c.id
                WHERE kp.id = ?
            """, (self.plan_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_plan_no.setText(row[0] or "")
                self.txt_plan_no.setEnabled(False)
                self.spin_revizyon.setValue(row[1] or 1)
                
                # Önce müşteriyi set et (cari_unvani ile)
                cari_unvani = row[11]  # JOIN'den gelen unvan
                if cari_unvani:
                    idx = self.cmb_musteri.findData(cari_unvani)
                    if idx >= 0: 
                        self.cmb_musteri.setCurrentIndex(idx)
                        # Ürünleri yükle
                        self._load_urunler(cari_unvani)
                
                # Sonra ürünü set et
                if row[2]:
                    idx = self.cmb_urun.findData(row[2])
                    if idx >= 0: self.cmb_urun.setCurrentIndex(idx)
                
                if row[3]:
                    idx = self.cmb_kaplama.findData(row[3])
                    if idx >= 0: self.cmb_kaplama.setCurrentIndex(idx)
                
                if row[5]:
                    self.date_baslangic.setDate(QDate(row[5].year, row[5].month, row[5].day))
                if row[6]:
                    self.date_bitis.setDate(QDate(row[6].year, row[6].month, row[6].day))
                
                if row[7]:
                    idx = self.cmb_hazirlayan.findData(row[7])
                    if idx >= 0: self.cmb_hazirlayan.setCurrentIndex(idx)
                
                if row[8]:
                    idx = self.cmb_onaylayan.findData(row[8])
                    if idx >= 0: self.cmb_onaylayan.setCurrentIndex(idx)
                
                if row[9]:
                    idx = self.cmb_durum.findText(row[9])
                    if idx >= 0: self.cmb_durum.setCurrentIndex(idx)
                
                self.txt_notlar.setPlainText(row[10] or "")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _load_satirlar(self):
        """Kontrol satırlarını yükle"""
        if not self.plan_id:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sira_no, operasyon, kontrol_ozelligi, spesifikasyon,
                       olcum_metodu, frekans, kritik_mi, spc_uygulanacak_mi
                FROM kalite.kontrol_plan_satirlar
                WHERE plan_id = ? AND aktif_mi = 1
                ORDER BY sira_no
            """, (self.plan_id,))
            rows = cursor.fetchall()
            conn.close()
            
            self.table_satirlar.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table_satirlar.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_satirlar.setItem(i, 1, QTableWidgetItem(str(row[1])))
                self.table_satirlar.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.table_satirlar.setItem(i, 3, QTableWidgetItem(row[3] or ""))
                self.table_satirlar.setItem(i, 4, QTableWidgetItem(row[4] or ""))
                self.table_satirlar.setItem(i, 5, QTableWidgetItem(row[5] or ""))
                self.table_satirlar.setItem(i, 6, QTableWidgetItem(row[6] or ""))
                self.table_satirlar.setItem(i, 7, QTableWidgetItem("✓" if row[7] else ""))
                self.table_satirlar.setItem(i, 8, QTableWidgetItem("✓" if row[8] else ""))
                
        except Exception as e:
            print(f"Satır yükleme hatası: {e}")
    
    def _add_satir(self):
        """Yeni satır ekle"""
        if not self.plan_id:
            QMessageBox.warning(self, "Uyarı", "Önce planı kaydedin!")
            return
        
        dialog = KontrolPlanSatirDialog(self.theme, self.plan_id, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
    
    def _edit_satir(self):
        """Satır düzenle"""
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir satır seçin!")
            return
        
        satir_id = int(self.table_satirlar.item(row, 0).text())
        dialog = KontrolPlanSatirDialog(self.theme, self.plan_id, self, satir_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
    
    def _delete_satir(self):
        """Satır sil"""
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir satır seçin!")
            return
        
        satir_id = int(self.table_satirlar.item(row, 0).text())
        
        reply = QMessageBox.question(self, "Onay", "Bu satırı silmek istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE kalite.kontrol_plan_satirlar SET aktif_mi = 0 WHERE id = ?", (satir_id,))
                conn.commit()
                conn.close()
                self._load_satirlar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
    
    def _save(self):
        """Planı kaydet"""
        plan_no = self.txt_plan_no.text().strip()
        
        if not plan_no:
            QMessageBox.warning(self, "Uyarı", "Plan No zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # cari_unvani'den cari_id bul
            cari_unvani = self.cmb_musteri.currentData()
            cari_id = None
            if cari_unvani:
                cursor.execute("""
                    SELECT TOP 1 id FROM musteri.cariler 
                    WHERE unvan = ? AND aktif_mi = 1 AND silindi_mi = 0
                """, (cari_unvani,))
                row = cursor.fetchone()
                if row:
                    cari_id = row[0]
            
            if self.plan_id:
                cursor.execute("""
                    UPDATE kalite.kontrol_planlari SET
                        revizyon = ?, urun_id = ?, kaplama_turu_id = ?, cari_id = ?,
                        gecerlilik_baslangic = ?, gecerlilik_bitis = ?,
                        hazirlayan_id = ?, onaylayan_id = ?, durum = ?, notlar = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    self.spin_revizyon.value(),
                    self.cmb_urun.currentData(),
                    self.cmb_kaplama.currentData(),
                    cari_id,
                    self.date_baslangic.date().toPython(),
                    self.date_bitis.date().toPython(),
                    self.cmb_hazirlayan.currentData(),
                    self.cmb_onaylayan.currentData(),
                    self.cmb_durum.currentText(),
                    self.txt_notlar.toPlainText().strip() or None,
                    self.plan_id
                ))
            else:
                # Plan no kontrolü
                cursor.execute("SELECT COUNT(*) FROM kalite.kontrol_planlari WHERE plan_no = ?", (plan_no,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu Plan No zaten kullanılıyor!")
                    conn.close()
                    return
                
                cursor.execute("""
                    INSERT INTO kalite.kontrol_planlari
                    (plan_no, revizyon, urun_id, kaplama_turu_id, cari_id,
                     gecerlilik_baslangic, gecerlilik_bitis,
                     hazirlayan_id, onaylayan_id, durum, notlar)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    plan_no, self.spin_revizyon.value(),
                    self.cmb_urun.currentData(),
                    self.cmb_kaplama.currentData(),
                    cari_id,
                    self.date_baslangic.date().toPython(),
                    self.date_bitis.date().toPython(),
                    self.cmb_hazirlayan.currentData(),
                    self.cmb_onaylayan.currentData(),
                    self.cmb_durum.currentText(),
                    self.txt_notlar.toPlainText().strip() or None
                ))
                self.plan_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Başarılı", "Plan kaydedildi!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class KontrolPlaniPage(BasePage):
    """Kontrol Planı Yönetimi Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("📋 Kontrol Planı Yönetimi")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Plan")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni_plan)
        toolbar_layout.addWidget(btn_yeni)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar_layout.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._sil)
        toolbar_layout.addWidget(btn_sil)
        
        toolbar_layout.addStretch()
        
        # Arama
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Plan No veya Ürün ara...")
        self.txt_search.setStyleSheet(f"""
            QLineEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
                min-width: 200px;
            }}
        """)
        self.txt_search.textChanged.connect(self._filter)
        toolbar_layout.addWidget(self.txt_search)
        
        # Durum filtresi
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tümü", "TASLAK", "ONAY_BEKLIYOR", "ONAYLANDI", "IPTAL"])
        self.cmb_durum.setStyleSheet(f"""
            QComboBox {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
        """)
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_durum)
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setFixedSize(60, 36)
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border-radius: 6px; font-size: 12px;")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Plan No", "Rev", "Ürün/Kaplama", "Müşteri", 
            "Geçerlilik", "Durum", "Satır", "Oluşturma"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                color: {self.theme.get('text')};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QTableWidget::item:selected {{ background: {self.theme.get('primary')}; }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary')};
                font-weight: bold;
            }}
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 60)
        self.table.setColumnWidth(8, 100)
        
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        # İstatistik
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        """Verileri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    kp.id, kp.plan_no, kp.revizyon,
                    ISNULL(u.urun_kodu, '') + ' / ' + ISNULL(kt.kod, '') as urun_kaplama,
                    c.unvan,
                    FORMAT(kp.gecerlilik_baslangic, 'dd.MM.yyyy') + ' - ' + ISNULL(FORMAT(kp.gecerlilik_bitis, 'dd.MM.yyyy'), '∞'),
                    kp.durum,
                    (SELECT COUNT(*) FROM kalite.kontrol_plan_satirlar WHERE plan_id = kp.id AND aktif_mi = 1),
                    FORMAT(kp.olusturma_tarihi, 'dd.MM.yyyy')
                FROM kalite.kontrol_planlari kp
                LEFT JOIN stok.urunler u ON kp.urun_id = u.id
                LEFT JOIN tanim.kaplama_turleri kt ON kp.kaplama_turu_id = kt.id
                LEFT JOIN musteri.cariler c ON kp.cari_id = c.id
                ORDER BY kp.olusturma_tarihi DESC
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            
            self._display_data(self.all_rows)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _display_data(self, rows):
        """Verileri tabloda göster"""
        self.table.setRowCount(len(rows))
        
        durum_colors = {
            'TASLAK': self.theme.get('warning'),
            'ONAY_BEKLIYOR': self.theme.get('info'),
            'ONAYLANDI': self.theme.get('success'),
            'IPTAL': self.theme.get('danger'),
        }
        
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "")
                
                # Durum rengi
                if j == 6 and val:
                    item.setForeground(QColor(durum_colors.get(val, self.theme.get('text'))))
                
                self.table.setItem(i, j, item)
        
        self.lbl_stat.setText(f"Toplam: {len(rows)} kontrol planı")
    
    def _filter(self):
        """Filtrele"""
        search = self.txt_search.text().lower()
        durum = self.cmb_durum.currentText()
        
        filtered = []
        for row in self.all_rows:
            # Arama
            if search:
                if search not in str(row[1]).lower() and search not in str(row[3]).lower():
                    continue
            # Durum
            if durum != "Tümü" and row[6] != durum:
                continue
            filtered.append(row)
        
        self._display_data(filtered)
    
    def _yeni_plan(self):
        """Yeni plan ekle"""
        dialog = KontrolPlanDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        """Plan düzenle"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir plan seçin!")
            return
        
        plan_id = int(self.table.item(row, 0).text())
        dialog = KontrolPlanDialog(self.theme, self, plan_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _sil(self):
        """Plan sil"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir plan seçin!")
            return
        
        plan_id = int(self.table.item(row, 0).text())
        plan_no = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Onay", f"'{plan_no}' planını silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM kalite.kontrol_planlari WHERE id = ?", (plan_id,))
                conn.commit()
                conn.close()
                self._load_data()
                QMessageBox.information(self, "Başarılı", "Plan silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
