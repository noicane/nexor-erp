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
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


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
            print(f"Cihaz yükleme hatası: {e}")
    
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
        form.addRow("Cihaz Adı:", self.txt_ad)
        
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
        self.txt_aralik.setPlaceholderText("Ör: 0-1000 µm")
        form.addRow("Ölçüm Aralığı:", self.txt_aralik)
        
        self.txt_lokasyon = QLineEdit(self.cihaz.get('lokasyon', ''))
        self.txt_lokasyon.setStyleSheet(input_style)
        form.addRow("Lokasyon:", self.txt_lokasyon)
        
        self.cmb_sorumlu = QComboBox()
        self.cmb_sorumlu.setStyleSheet(input_style)
        self._load_personel()
        form.addRow("Sorumlu:", self.cmb_sorumlu)
        
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(['AKTİF', 'PASİF', 'ARIZALI', 'KALİBRASYONDA'])
        self.cmb_durum.setStyleSheet(input_style)
        if self.cihaz.get('durum'):
            idx = self.cmb_durum.findText(self.cihaz.get('durum'))
            if idx >= 0: self.cmb_durum.setCurrentIndex(idx)
        form.addRow("Durum:", self.cmb_durum)
        
        layout.addLayout(form)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 10px 24px;")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _load_personel(self):
        self.cmb_sorumlu.clear()
        self.cmb_sorumlu.addItem("-- Seçin --", None)
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
        except Exception: pass
    
    def _kaydet(self):
        kod = self.txt_kod.text().strip()
        ad = self.txt_ad.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Cihaz kodu ve adı zorunludur!")
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
            QMessageBox.information(self, "Başarılı", "Cihaz kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt başarısız: {e}")


class KalibrasyonKayitDialog(QDialog):
    """Kalibrasyon kaydı ekleme dialog'u"""
    
    def __init__(self, theme: dict, cihaz_id: int, cihaz_adi: str, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.cihaz_id = cihaz_id
        self.cihaz_adi = cihaz_adi
        self.setWindowTitle("Kalibrasyon Kaydı Ekle")
        self.setMinimumSize(500, 450)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main')}; }} QLabel {{ color: {self.theme.get('text')}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        input_style = f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;"
        
        title = QLabel(f"📋 {self.cihaz_adi}")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.date_kalibrasyon = QDateEdit()
        self.date_kalibrasyon.setDate(QDate.currentDate())
        self.date_kalibrasyon.setCalendarPopup(True)
        self.date_kalibrasyon.setStyleSheet(input_style)
        form.addRow("Kalibrasyon Tarihi:", self.date_kalibrasyon)
        
        self.date_gecerlilik = QDateEdit()
        self.date_gecerlilik.setDate(QDate.currentDate().addYears(1))
        self.date_gecerlilik.setCalendarPopup(True)
        self.date_gecerlilik.setStyleSheet(input_style)
        form.addRow("Geçerlilik Tarihi:", self.date_gecerlilik)
        
        self.txt_firma = QLineEdit()
        self.txt_firma.setStyleSheet(input_style)
        self.txt_firma.setPlaceholderText("Kalibrasyon yapan kuruluş")
        form.addRow("Yapan Firma:", self.txt_firma)
        
        self.txt_sertifika = QLineEdit()
        self.txt_sertifika.setStyleSheet(input_style)
        form.addRow("Sertifika No:", self.txt_sertifika)
        
        self.cmb_sonuc = QComboBox()
        self.cmb_sonuc.addItems(['UYGUN', 'UYGUN DEĞİL', 'SINIRLI KULLANIM'])
        self.cmb_sonuc.setStyleSheet(input_style)
        form.addRow("Sonuç:", self.cmb_sonuc)
        
        self.txt_maliyet = QDoubleSpinBox()
        self.txt_maliyet.setRange(0, 999999)
        self.txt_maliyet.setSuffix(" ₺")
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
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 10px 24px;")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _kaydet(self):
        firma = self.txt_firma.text().strip()
        if not firma:
            QMessageBox.warning(self, "Uyarı", "Yapan firma zorunludur!")
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
            cursor.execute("""
                UPDATE kalite.kalibrasyon_planlari SET son_kalibrasyon_tarihi = ?, 
                sonraki_kalibrasyon_tarihi = DATEADD(MONTH, kalibrasyon_periyodu_ay, ?)
                WHERE cihaz_id = ? AND aktif_mi = 1
            """, (self.date_kalibrasyon.date().toPython(), self.date_kalibrasyon.date().toPython(), self.cihaz_id))
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Kalibrasyon kaydı eklendi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt başarısız: {e}")


class KaliteKalibrasyonPage(BasePage):
    """Kalibrasyon Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📏 Kalibrasyon Yönetimi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text', '#fff')};")
        header.addWidget(title)
        header.addStretch()
        
        btn_yeni = QPushButton("➕ Yeni Cihaz")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni_cihaz)
        header.addWidget(btn_yeni)
        layout.addLayout(header)
        
        # İstatistik kartları
        stat_layout = QHBoxLayout()
        self.stat_toplam = self._create_stat_card("📏 Toplam", "0", self.theme.get('primary', '#3b82f6'))
        stat_layout.addWidget(self.stat_toplam)
        self.stat_yaklasan = self._create_stat_card("⚠️ Yaklaşan", "0", self.theme.get('warning', '#f59e0b'))
        stat_layout.addWidget(self.stat_yaklasan)
        self.stat_geciken = self._create_stat_card("❌ Geciken", "0", self.theme.get('danger', '#ef4444'))
        stat_layout.addWidget(self.stat_geciken)
        self.stat_guncel = self._create_stat_card("✅ Güncel", "0", self.theme.get('success', '#22c55e'))
        stat_layout.addWidget(self.stat_guncel)
        stat_layout.addStretch()
        layout.addLayout(stat_layout)
        
        # Filtre
        filtre_layout = QHBoxLayout()
        filtre_layout.addWidget(QLabel("Durum:"))
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(['Tümü', 'AKTİF', 'PASİF', 'ARIZALI'])
        self.cmb_durum.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 6px;")
        self.cmb_durum.currentIndexChanged.connect(self._load_data)
        filtre_layout.addWidget(self.cmb_durum)
        filtre_layout.addStretch()
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.clicked.connect(self._load_data)
        filtre_layout.addWidget(btn_yenile)
        layout.addLayout(filtre_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Kod", "Cihaz Adı", "Marka/Model", "Lokasyon", "Son Kalibrasyon", "Sonraki", "Durum", "İşlem"])
        self.table.setColumnWidth(8, 170)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; }}
            QHeaderView::section {{ background: {self.theme.get('bg_sidebar')}; color: {self.theme.get('text')}; padding: 10px; border: none; font-weight: bold; }}
        """)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(140, 70)
        card.setStyleSheet(f"background: {self.theme.get('bg_card')}; border: 1px solid {color}; border-radius: 8px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {self.theme.get('text_secondary')}; font-size: 11px;")
        layout.addWidget(lbl_title)
        lbl_value = QLabel(value)
        lbl_value.setObjectName("stat_value")
        lbl_value.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        layout.addWidget(lbl_value)
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
            
            durum_filtre = self.cmb_durum.currentText()
            where_clause = "" if durum_filtre == 'Tümü' else f"AND c.durum = '{durum_filtre}'"
            
            cursor.execute(f"""
                SELECT c.id, c.cihaz_kodu, c.cihaz_adi, 
                       ISNULL(c.marka, '') + ' ' + ISNULL(c.model, ''), c.lokasyon,
                       (SELECT TOP 1 kalibrasyon_tarihi FROM kalite.kalibrasyon_kayitlari WHERE cihaz_id = c.id ORDER BY kalibrasyon_tarihi DESC),
                       p.sonraki_kalibrasyon_tarihi, c.durum
                FROM kalite.olcum_cihazlari c
                LEFT JOIN kalite.kalibrasyon_planlari p ON c.id = p.cihaz_id AND p.aktif_mi = 1
                WHERE c.aktif_mi = 1 {where_clause}
                ORDER BY p.sonraki_kalibrasyon_tarihi, c.cihaz_kodu
            """)
            
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            
            today = date.today()
            
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.table.setItem(i, 3, QTableWidgetItem((row[3] or '').strip()))
                self.table.setItem(i, 4, QTableWidgetItem(row[4] or ''))
                
                son_kal = row[5]
                self.table.setItem(i, 5, QTableWidgetItem(son_kal.strftime('%d.%m.%Y') if son_kal else '-'))
                
                sonraki = row[6]
                sonraki_item = QTableWidgetItem(sonraki.strftime('%d.%m.%Y') if sonraki else '-')
                if sonraki:
                    if sonraki < today:
                        sonraki_item.setForeground(QColor(self.theme.get('danger')))
                    elif (sonraki - today).days <= 30:
                        sonraki_item.setForeground(QColor(self.theme.get('warning')))
                self.table.setItem(i, 6, sonraki_item)
                
                self.table.setItem(i, 7, QTableWidgetItem(row[7] or ''))
                
                # İşlem butonları
                widget = self.create_action_buttons([
                    ("📋", "Kalibrasyon Ekle", lambda checked, cid=row[0], cad=row[2]: self._kalibrasyon_ekle(cid, cad), "info"),
                    ("✏️", "Düzenle", lambda checked, cid=row[0]: self._duzenle_cihaz(cid), "edit"),
                ])
                self.table.setCellWidget(i, 8, widget)
                self.table.setRowHeight(i, 42)
            
            # İstatistikler
            cursor.execute("SELECT COUNT(*) FROM kalite.olcum_cihazlari WHERE aktif_mi = 1")
            self.stat_toplam.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            cursor.execute("""
                SELECT COUNT(*) FROM kalite.kalibrasyon_planlari p
                JOIN kalite.olcum_cihazlari c ON p.cihaz_id = c.id
                WHERE p.aktif_mi = 1 AND c.aktif_mi = 1
                AND p.sonraki_kalibrasyon_tarihi BETWEEN CAST(GETDATE() AS DATE) AND DATEADD(DAY, 30, CAST(GETDATE() AS DATE))
            """)
            self.stat_yaklasan.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            cursor.execute("""
                SELECT COUNT(*) FROM kalite.kalibrasyon_planlari p
                JOIN kalite.olcum_cihazlari c ON p.cihaz_id = c.id
                WHERE p.aktif_mi = 1 AND c.aktif_mi = 1 AND p.sonraki_kalibrasyon_tarihi < CAST(GETDATE() AS DATE)
            """)
            self.stat_geciken.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            cursor.execute("""
                SELECT COUNT(*) FROM kalite.kalibrasyon_planlari p
                JOIN kalite.olcum_cihazlari c ON p.cihaz_id = c.id
                WHERE p.aktif_mi = 1 AND c.aktif_mi = 1 AND p.sonraki_kalibrasyon_tarihi > DATEADD(DAY, 30, CAST(GETDATE() AS DATE))
            """)
            self.stat_guncel.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))
            
            conn.close()
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
