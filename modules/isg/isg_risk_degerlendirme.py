# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İSG Risk Değerlendirme
5x5 Matris ile Risk Değerlendirme
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QSpinBox, QTabWidget
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush

from components.base_page import BasePage
from core.database import get_db_connection


def get_risk_color(skor):
    """Risk skoruna göre renk döndür"""
    if skor <= 4:
        return "#27ae60"  # Yeşil - Kabul Edilebilir
    elif skor <= 9:
        return "#f1c40f"  # Sarı - Düşük
    elif skor <= 14:
        return "#e67e22"  # Turuncu - Orta
    elif skor <= 19:
        return "#e74c3c"  # Kırmızı - Yüksek
    else:
        return "#8e44ad"  # Mor - Çok Yüksek


def get_risk_seviye(skor):
    """Risk skoruna göre seviye döndür"""
    if skor <= 4:
        return "KABUL EDİLEBİLİR"
    elif skor <= 9:
        return "DÜŞÜK"
    elif skor <= 14:
        return "ORTA"
    elif skor <= 19:
        return "YÜKSEK"
    else:
        return "ÇOK YÜKSEK"


class RiskSatirDialog(QDialog):
    """Risk değerlendirme satırı ekleme/düzenleme"""
    
    def __init__(self, theme: dict, risk_id: int, parent=None, satir_id=None):
        super().__init__(parent)
        self.theme = theme
        self.risk_id = risk_id
        self.satir_id = satir_id
        self.setWindowTitle("Risk Kalemi Ekle" if not satir_id else "Risk Kalemi Düzenle")
        self.setMinimumSize(700, 650)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if satir_id:
            self._load_data()
        self._update_risk_display()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QSpinBox, QTextEdit, QDateEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px; padding: 8px;
                color: {self.theme.get('text')};
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Tehlike tanımı
        form1 = QFormLayout()
        
        self.cmb_tehlike = QComboBox()
        self.cmb_tehlike.currentIndexChanged.connect(self._on_tehlike_changed)
        form1.addRow("Tehlike:", self.cmb_tehlike)
        
        self.txt_tehlike = QTextEdit()
        self.txt_tehlike.setMaximumHeight(60)
        self.txt_tehlike.setPlaceholderText("Tehlike tanımını detaylandırın...")
        form1.addRow("Tehlike Tanımı*:", self.txt_tehlike)
        
        self.txt_etkilenen = QLineEdit()
        self.txt_etkilenen.setPlaceholderText("Örn: Tüm üretim çalışanları")
        form1.addRow("Etkilenen Kişiler:", self.txt_etkilenen)
        
        self.txt_mevcut = QTextEdit()
        self.txt_mevcut.setMaximumHeight(50)
        self.txt_mevcut.setPlaceholderText("Mevcut kontrol önlemleri...")
        form1.addRow("Mevcut Önlemler:", self.txt_mevcut)
        
        layout.addLayout(form1)
        
        # 5x5 Matris - Mevcut Durum
        lbl_mevcut = QLabel("📊 MEVCUT DURUM (5x5 MATRİS)")
        lbl_mevcut.setStyleSheet(f"font-weight: bold; color: {self.theme.get('primary')}; margin-top: 10px;")
        layout.addWidget(lbl_mevcut)
        
        matris_layout = QHBoxLayout()
        
        olasilik_layout = QVBoxLayout()
        olasilik_layout.addWidget(QLabel("Olasılık (1-5):"))
        self.spin_olasilik = QSpinBox()
        self.spin_olasilik.setRange(1, 5)
        self.spin_olasilik.setValue(3)
        self.spin_olasilik.valueChanged.connect(self._update_risk_display)
        olasilik_layout.addWidget(self.spin_olasilik)
        olasilik_layout.addWidget(QLabel("1: Çok Düşük\n2: Düşük\n3: Orta\n4: Yüksek\n5: Çok Yüksek"))
        matris_layout.addLayout(olasilik_layout)
        
        siddet_layout = QVBoxLayout()
        siddet_layout.addWidget(QLabel("Şiddet (1-5):"))
        self.spin_siddet = QSpinBox()
        self.spin_siddet.setRange(1, 5)
        self.spin_siddet.setValue(3)
        self.spin_siddet.valueChanged.connect(self._update_risk_display)
        siddet_layout.addWidget(self.spin_siddet)
        siddet_layout.addWidget(QLabel("1: Önemsiz\n2: Az\n3: Orta\n4: Ciddi\n5: Çok Ciddi"))
        matris_layout.addLayout(siddet_layout)
        
        # Risk skoru gösterimi
        skor_layout = QVBoxLayout()
        skor_layout.addWidget(QLabel("Risk Skoru:"))
        self.lbl_skor = QLabel("9")
        self.lbl_skor.setStyleSheet("font-size: 32px; font-weight: bold;")
        self.lbl_skor.setAlignment(Qt.AlignCenter)
        skor_layout.addWidget(self.lbl_skor)
        self.lbl_seviye = QLabel("ORTA")
        self.lbl_seviye.setAlignment(Qt.AlignCenter)
        self.lbl_seviye.setStyleSheet("font-weight: bold;")
        skor_layout.addWidget(self.lbl_seviye)
        matris_layout.addLayout(skor_layout)
        
        layout.addLayout(matris_layout)
        
        # Alınacak önlemler
        lbl_onlem = QLabel("🛡️ ALINACAK ÖNLEMLER")
        lbl_onlem.setStyleSheet(f"font-weight: bold; color: {self.theme.get('primary')}; margin-top: 10px;")
        layout.addWidget(lbl_onlem)
        
        form2 = QFormLayout()
        
        self.txt_alinacak = QTextEdit()
        self.txt_alinacak.setMaximumHeight(60)
        self.txt_alinacak.setPlaceholderText("Alınacak önlemler ve aksiyonlar...")
        form2.addRow("Alınacak Önlemler:", self.txt_alinacak)
        
        self.cmb_sorumlu = QComboBox()
        form2.addRow("Sorumlu:", self.cmb_sorumlu)
        
        self.date_hedef = QDateEdit()
        self.date_hedef.setDate(QDate.currentDate().addDays(30))
        self.date_hedef.setCalendarPopup(True)
        form2.addRow("Hedef Tarih:", self.date_hedef)
        
        layout.addLayout(form2)
        
        # Artık risk (önlem sonrası)
        lbl_artik = QLabel("📉 ARTIK RİSK (Önlem Sonrası)")
        lbl_artik.setStyleSheet(f"font-weight: bold; color: {self.theme.get('success')}; margin-top: 10px;")
        layout.addWidget(lbl_artik)
        
        artik_layout = QHBoxLayout()
        artik_layout.addWidget(QLabel("Olasılık:"))
        self.spin_artik_olasilik = QSpinBox()
        self.spin_artik_olasilik.setRange(1, 5)
        self.spin_artik_olasilik.setValue(1)
        self.spin_artik_olasilik.valueChanged.connect(self._update_risk_display)
        artik_layout.addWidget(self.spin_artik_olasilik)
        
        artik_layout.addWidget(QLabel("Şiddet:"))
        self.spin_artik_siddet = QSpinBox()
        self.spin_artik_siddet.setRange(1, 5)
        self.spin_artik_siddet.setValue(1)
        self.spin_artik_siddet.valueChanged.connect(self._update_risk_display)
        artik_layout.addWidget(self.spin_artik_siddet)
        
        self.lbl_artik_skor = QLabel("= 1 (KABUL EDİLEBİLİR)")
        self.lbl_artik_skor.setStyleSheet(f"font-weight: bold; color: {self.theme.get('success')};")
        artik_layout.addWidget(self.lbl_artik_skor)
        artik_layout.addStretch()
        
        layout.addLayout(artik_layout)
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 20px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 20px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            self.cmb_tehlike.addItem("-- Manuel Giriş --", None)
            cursor.execute("SELECT id, kod, tehlike_adi, kategori FROM isg.tehlike_tanimlari WHERE aktif_mi = 1 ORDER BY kategori, kod")
            for row in cursor.fetchall():
                self.cmb_tehlike.addItem(f"[{row[3]}] {row[1]} - {row[2]}", row[0])
            
            self.cmb_sorumlu.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_sorumlu.addItem(f"{row[1]} - {row[2]}", row[0])
            
            conn.close()
        except:
            pass
    
    def _on_tehlike_changed(self, index):
        if index > 0:
            text = self.cmb_tehlike.currentText()
            if " - " in text:
                tehlike = text.split(" - ", 1)[1]
                self.txt_tehlike.setPlainText(tehlike)
    
    def _update_risk_display(self):
        # Mevcut risk
        olasilik = self.spin_olasilik.value()
        siddet = self.spin_siddet.value()
        skor = olasilik * siddet
        seviye = get_risk_seviye(skor)
        renk = get_risk_color(skor)
        
        self.lbl_skor.setText(str(skor))
        self.lbl_skor.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {renk};")
        self.lbl_seviye.setText(seviye)
        self.lbl_seviye.setStyleSheet(f"font-weight: bold; color: {renk};")
        
        # Artık risk
        artik_olasilik = self.spin_artik_olasilik.value()
        artik_siddet = self.spin_artik_siddet.value()
        artik_skor = artik_olasilik * artik_siddet
        artik_seviye = get_risk_seviye(artik_skor)
        artik_renk = get_risk_color(artik_skor)
        
        self.lbl_artik_skor.setText(f"= {artik_skor} ({artik_seviye})")
        self.lbl_artik_skor.setStyleSheet(f"font-weight: bold; color: {artik_renk};")
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tehlike_id, tehlike_tanimi, etkilenen_kisiler, mevcut_onlemler,
                       olasilik, siddet, alinacak_onlemler, sorumlu_id, hedef_tarih,
                       artik_olasilik, artik_siddet
                FROM isg.risk_degerlendirme_satirlari WHERE id = ?
            """, (self.satir_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                if row[0]:
                    idx = self.cmb_tehlike.findData(row[0])
                    if idx >= 0: self.cmb_tehlike.setCurrentIndex(idx)
                self.txt_tehlike.setPlainText(row[1] or "")
                self.txt_etkilenen.setText(row[2] or "")
                self.txt_mevcut.setPlainText(row[3] or "")
                self.spin_olasilik.setValue(row[4] or 3)
                self.spin_siddet.setValue(row[5] or 3)
                self.txt_alinacak.setPlainText(row[6] or "")
                if row[7]:
                    idx = self.cmb_sorumlu.findData(row[7])
                    if idx >= 0: self.cmb_sorumlu.setCurrentIndex(idx)
                if row[8]:
                    self.date_hedef.setDate(QDate(row[8].year, row[8].month, row[8].day))
                self.spin_artik_olasilik.setValue(row[9] or 1)
                self.spin_artik_siddet.setValue(row[10] or 1)
                self._update_risk_display()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        tehlike = self.txt_tehlike.toPlainText().strip()
        if not tehlike:
            QMessageBox.warning(self, "Uyarı", "Tehlike tanımı zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            tehlike_id = self.cmb_tehlike.currentData()
            
            if self.satir_id:
                cursor.execute("""
                    UPDATE isg.risk_degerlendirme_satirlari SET
                        tehlike_id = ?, tehlike_tanimi = ?, etkilenen_kisiler = ?, mevcut_onlemler = ?,
                        olasilik = ?, siddet = ?, alinacak_onlemler = ?, sorumlu_id = ?, hedef_tarih = ?,
                        artik_olasilik = ?, artik_siddet = ?
                    WHERE id = ?
                """, (
                    tehlike_id, tehlike, self.txt_etkilenen.text().strip() or None,
                    self.txt_mevcut.toPlainText().strip() or None,
                    self.spin_olasilik.value(), self.spin_siddet.value(),
                    self.txt_alinacak.toPlainText().strip() or None,
                    self.cmb_sorumlu.currentData(),
                    self.date_hedef.date().toPython(),
                    self.spin_artik_olasilik.value(), self.spin_artik_siddet.value(),
                    self.satir_id
                ))
            else:
                cursor.execute("SELECT ISNULL(MAX(satir_no), 0) + 1 FROM isg.risk_degerlendirme_satirlari WHERE risk_degerlendirme_id = ?", (self.risk_id,))
                satir_no = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO isg.risk_degerlendirme_satirlari
                    (risk_degerlendirme_id, satir_no, tehlike_id, tehlike_tanimi, etkilenen_kisiler,
                     mevcut_onlemler, olasilik, siddet, alinacak_onlemler, sorumlu_id, hedef_tarih,
                     artik_olasilik, artik_siddet)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.risk_id, satir_no, tehlike_id, tehlike,
                    self.txt_etkilenen.text().strip() or None,
                    self.txt_mevcut.toPlainText().strip() or None,
                    self.spin_olasilik.value(), self.spin_siddet.value(),
                    self.txt_alinacak.toPlainText().strip() or None,
                    self.cmb_sorumlu.currentData(),
                    self.date_hedef.date().toPython(),
                    self.spin_artik_olasilik.value(), self.spin_artik_siddet.value()
                ))
            
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class RiskDegerlendirmeDialog(QDialog):
    """Risk değerlendirme ana dialog"""
    
    def __init__(self, theme: dict, parent=None, risk_id=None):
        super().__init__(parent)
        self.theme = theme
        self.risk_id = risk_id
        self.setWindowTitle("Risk Değerlendirme" if not risk_id else "Risk Değerlendirme Düzenle")
        self.setMinimumSize(1000, 650)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if risk_id:
            self._load_data()
            self._load_satirlar()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px; padding: 8px;
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
        
        self.txt_no = QLineEdit()
        self.txt_no.setReadOnly(True)
        self.txt_no.setPlaceholderText("Otomatik")
        genel_layout.addRow("Değerlendirme No:", self.txt_no)
        
        self.date_tarih = QDateEdit()
        self.date_tarih.setDate(QDate.currentDate())
        self.date_tarih.setCalendarPopup(True)
        genel_layout.addRow("Tarih:", self.date_tarih)
        
        self.cmb_bolum = QComboBox()
        genel_layout.addRow("Bölüm/Departman:", self.cmb_bolum)
        
        self.txt_alan = QLineEdit()
        self.txt_alan.setPlaceholderText("Örn: Kataforez Hattı, Kimyasal Depo...")
        genel_layout.addRow("Alan Tanımı*:", self.txt_alan)
        
        self.cmb_hazirlayan = QComboBox()
        genel_layout.addRow("Hazırlayan:", self.cmb_hazirlayan)
        
        self.date_gecerlilik = QDateEdit()
        self.date_gecerlilik.setDate(QDate.currentDate().addYears(1))
        self.date_gecerlilik.setCalendarPopup(True)
        genel_layout.addRow("Geçerlilik Tarihi:", self.date_gecerlilik)
        
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(60)
        genel_layout.addRow("Notlar:", self.txt_notlar)
        
        tabs.addTab(tab_genel, "📋 Genel")
        
        # Tab 2: Riskler
        tab_riskler = QWidget()
        risk_layout = QVBoxLayout(tab_riskler)
        
        toolbar = QHBoxLayout()
        btn_ekle = QPushButton("➕ Risk Ekle")
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
        risk_layout.addLayout(toolbar)
        
        self.table_satirlar = QTableWidget()
        self.table_satirlar.setColumnCount(8)
        self.table_satirlar.setHorizontalHeaderLabels(["ID", "Tehlike", "O", "Ş", "Skor", "Seviye", "Artık", "Durum"])
        self.table_satirlar.setColumnHidden(0, True)
        self.table_satirlar.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_satirlar.setStyleSheet(f"QTableWidget {{ background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; }}")
        header = self.table_satirlar.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_satirlar.setColumnWidth(2, 60)
        self.table_satirlar.setColumnWidth(3, 60)
        self.table_satirlar.setColumnWidth(4, 60)
        self.table_satirlar.setColumnWidth(5, 120)
        self.table_satirlar.setColumnWidth(6, 60)
        self.table_satirlar.setColumnWidth(7, 120)
        self.table_satirlar.doubleClicked.connect(self._edit_satir)
        risk_layout.addWidget(self.table_satirlar)
        
        # İstatistik
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        risk_layout.addWidget(self.lbl_stat)
        
        tabs.addTab(tab_riskler, "⚠️ Risk Kalemleri")
        layout.addWidget(tabs)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 24px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            self.cmb_bolum.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_bolum.addItem(f"{row[1]} - {row[2]}", row[0])
            
            self.cmb_hazirlayan.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_hazirlayan.addItem(f"{row[1]} - {row[2]}", row[0])
            
            conn.close()
        except:
            pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT degerlendirme_no, tarih, bolum_id, alan_tanimi, hazirlayan_id, gecerlilik_tarihi, notlar
                FROM isg.risk_degerlendirme WHERE id = ?
            """, (self.risk_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_no.setText(row[0] or "")
                if row[1]: self.date_tarih.setDate(QDate(row[1].year, row[1].month, row[1].day))
                if row[2]:
                    idx = self.cmb_bolum.findData(row[2])
                    if idx >= 0: self.cmb_bolum.setCurrentIndex(idx)
                self.txt_alan.setText(row[3] or "")
                if row[4]:
                    idx = self.cmb_hazirlayan.findData(row[4])
                    if idx >= 0: self.cmb_hazirlayan.setCurrentIndex(idx)
                if row[5]: self.date_gecerlilik.setDate(QDate(row[5].year, row[5].month, row[5].day))
                self.txt_notlar.setPlainText(row[6] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _load_satirlar(self):
        if not self.risk_id: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, tehlike_tanimi, olasilik, siddet, (olasilik * siddet) as skor,
                       (artik_olasilik * artik_siddet) as artik_skor, onlem_durumu
                FROM isg.risk_degerlendirme_satirlari WHERE risk_degerlendirme_id = ? ORDER BY satir_no
            """, (self.risk_id,))
            rows = cursor.fetchall()
            conn.close()
            
            self.table_satirlar.setRowCount(len(rows))
            yuksek_risk = 0
            
            for i, row in enumerate(rows):
                self.table_satirlar.setItem(i, 0, QTableWidgetItem(str(row[0])))
                
                tehlike = row[1][:50] + "..." if row[1] and len(row[1]) > 50 else row[1]
                self.table_satirlar.setItem(i, 1, QTableWidgetItem(tehlike or ""))
                self.table_satirlar.setItem(i, 2, QTableWidgetItem(str(row[2])))
                self.table_satirlar.setItem(i, 3, QTableWidgetItem(str(row[3])))
                
                skor = row[4] or 0
                skor_item = QTableWidgetItem(str(skor))
                skor_item.setForeground(QColor(get_risk_color(skor)))
                skor_item.setBackground(QBrush(QColor(get_risk_color(skor) + "30")))
                self.table_satirlar.setItem(i, 4, skor_item)
                
                seviye = get_risk_seviye(skor)
                seviye_item = QTableWidgetItem(seviye)
                seviye_item.setForeground(QColor(get_risk_color(skor)))
                self.table_satirlar.setItem(i, 5, seviye_item)
                
                artik = row[5] or 0
                artik_item = QTableWidgetItem(str(artik))
                artik_item.setForeground(QColor(get_risk_color(artik)))
                self.table_satirlar.setItem(i, 6, artik_item)
                
                self.table_satirlar.setItem(i, 7, QTableWidgetItem(row[6] or ""))
                
                if skor >= 15:
                    yuksek_risk += 1
            
            self.lbl_stat.setText(f"Toplam: {len(rows)} risk | Yüksek/Çok Yüksek: {yuksek_risk}")
        except: pass
    
    def _add_satir(self):
        if not self.risk_id:
            QMessageBox.warning(self, "Uyarı", "Önce değerlendirmeyi kaydedin!")
            return
        dialog = RiskSatirDialog(self.theme, self.risk_id, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
    
    def _edit_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0: return
        satir_id = int(self.table_satirlar.item(row, 0).text())
        dialog = RiskSatirDialog(self.theme, self.risk_id, self, satir_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
    
    def _delete_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0: return
        satir_id = int(self.table_satirlar.item(row, 0).text())
        if QMessageBox.question(self, "Onay", "Bu riski silmek istiyor musunuz?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM isg.risk_degerlendirme_satirlari WHERE id = ?", (satir_id,))
                conn.commit()
                conn.close()
                self._load_satirlar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        alan = self.txt_alan.text().strip()
        if not alan:
            QMessageBox.warning(self, "Uyarı", "Alan tanımı zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.risk_id:
                cursor.execute("""
                    UPDATE isg.risk_degerlendirme SET
                        bolum_id = ?, alan_tanimi = ?, hazirlayan_id = ?, gecerlilik_tarihi = ?,
                        notlar = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    self.cmb_bolum.currentData(), alan, self.cmb_hazirlayan.currentData(),
                    self.date_gecerlilik.date().toPython(),
                    self.txt_notlar.toPlainText().strip() or None, self.risk_id
                ))
            else:
                cursor.execute("SELECT 'RD-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM isg.risk_degerlendirme), 0) + 1 AS VARCHAR), 4)")
                no = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO isg.risk_degerlendirme
                    (degerlendirme_no, tarih, bolum_id, alan_tanimi, hazirlayan_id, gecerlilik_tarihi, notlar)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    no, self.date_tarih.date().toPython(), self.cmb_bolum.currentData(), alan,
                    self.cmb_hazirlayan.currentData(), self.date_gecerlilik.date().toPython(),
                    self.txt_notlar.toPlainText().strip() or None
                ))
                self.risk_id = cursor.fetchone()[0]
                self.txt_no.setText(no)
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Risk değerlendirme kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class ISGRiskDegerlendirmePage(BasePage):
    """İSG Risk Değerlendirme Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("⚠️ Risk Değerlendirme (5x5 Matris)")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Değerlendirme")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)

        toolbar_layout.addStretch()
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 12px; color: {self.theme.get('text')};")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "No", "Tarih", "Alan", "Risk Sayısı", "Yüksek Risk", "Durum", "İşlem"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; color: {self.theme.get('text')}; }}
            QTableWidget::item:selected {{ background: {self.theme.get('primary')}; }}
            QHeaderView::section {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px; font-weight: bold; }}
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 120)
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rd.id, rd.degerlendirme_no, FORMAT(rd.tarih, 'dd.MM.yyyy'), rd.alan_tanimi,
                       (SELECT COUNT(*) FROM isg.risk_degerlendirme_satirlari WHERE risk_degerlendirme_id = rd.id),
                       (SELECT COUNT(*) FROM isg.risk_degerlendirme_satirlari WHERE risk_degerlendirme_id = rd.id AND (olasilik * siddet) >= 15),
                       rd.durum
                FROM isg.risk_degerlendirme rd
                ORDER BY rd.tarih DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    if j == 5 and val:  # Yüksek risk
                        item = QTableWidgetItem(str(val))
                        if val > 0:
                            item.setForeground(QColor(self.theme.get('danger')))
                    else:
                        item = QTableWidgetItem(str(val) if val else "")
                    self.table.setItem(i, j, item)

                rid = row[0]
                widget = self.create_action_buttons([
                    ("✏️", "Duzenle", lambda checked, rid=rid: self._duzenle_by_id(rid), "edit"),
                ])
                self.table.setCellWidget(i, 7, widget)
                self.table.setRowHeight(i, 42)

            self.lbl_stat.setText(f"Toplam: {len(rows)} değerlendirme")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}\n\nÖnce SQL tabloları oluşturun!")

    def _duzenle_by_id(self, risk_id):
        """ID ile risk değerlendirme düzenleme (satır butonundan)"""
        dialog = RiskDegerlendirmeDialog(self.theme, self, risk_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _yeni(self):
        dialog = RiskDegerlendirmeDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        risk_id = int(self.table.item(row, 0).text())
        dialog = RiskDegerlendirmeDialog(self.theme, self, risk_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
