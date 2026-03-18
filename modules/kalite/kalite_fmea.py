# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - FMEA Yönetimi
Failure Mode and Effects Analysis (Hata Türü ve Etkileri Analizi)
kalite.fmea ve kalite.fmea_satirlar tabloları
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QGroupBox, QDateEdit,
    QSpinBox, QTextEdit, QTabWidget, QProgressBar
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush, QFont

from components.base_page import BasePage
from core.database import get_db_connection


def get_rpn_color(rpn):
    """RPN değerine göre renk döndür"""
    if rpn >= 200:
        return "#ef4444"  # Kırmızı - Kritik
    elif rpn >= 120:
        return "#f97316"  # Turuncu - Yüksek
    elif rpn >= 80:
        return "#eab308"  # Sarı - Orta
    else:
        return "#22c55e"  # Yeşil - Düşük


class FMEASatirDialog(QDialog):
    """FMEA satırı (hata modu) ekleme/düzenleme"""
    
    def __init__(self, theme: dict, fmea_id: int, parent=None, satir_id=None):
        super().__init__(parent)
        self.theme = theme
        self.fmea_id = fmea_id
        self.satir_id = satir_id
        self.setWindowTitle("Hata Modu Ekle" if not satir_id else "Hata Modu Düzenle")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        self._setup_ui()
        
        if satir_id:
            self._load_data()
        
        self._calculate_rpn()
    
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
                font-weight: bold;
            }}
            QCheckBox {{ color: {self.theme.get('text')}; }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {self.theme.get('border')}; border-radius: 8px; }}
            QTabBar::tab {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; }}
            QTabBar::tab:selected {{ background: {self.theme.get('primary')}; color: white; }}
        """)
        
        # Tab 1: Hata Bilgileri
        tab1 = QWidget()
        tab1_layout = QFormLayout(tab1)
        
        self.spin_sira = QSpinBox()
        self.spin_sira.setRange(1, 999)
        tab1_layout.addRow("Sıra No*:", self.spin_sira)
        
        self.txt_proses = QLineEdit()
        self.txt_proses.setPlaceholderText("Proses adımı veya fonksiyon")
        tab1_layout.addRow("Proses/Fonksiyon*:", self.txt_proses)
        
        self.txt_hata_modu = QTextEdit()
        self.txt_hata_modu.setMaximumHeight(60)
        self.txt_hata_modu.setPlaceholderText("Potansiyel hata modu nedir?")
        tab1_layout.addRow("Hata Modu*:", self.txt_hata_modu)
        
        self.txt_hata_etkisi = QTextEdit()
        self.txt_hata_etkisi.setMaximumHeight(60)
        self.txt_hata_etkisi.setPlaceholderText("Hatanın müşteri/süreç üzerindeki etkisi")
        tab1_layout.addRow("Hata Etkisi:", self.txt_hata_etkisi)
        
        self.txt_hata_nedeni = QTextEdit()
        self.txt_hata_nedeni.setMaximumHeight(60)
        self.txt_hata_nedeni.setPlaceholderText("Hatanın potansiyel nedeni")
        tab1_layout.addRow("Hata Nedeni:", self.txt_hata_nedeni)
        
        tabs.addTab(tab1, "📋 Hata Bilgileri")
        
        # Tab 2: RPN Değerlendirmesi
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        
        # Mevcut RPN
        rpn_group = QGroupBox("RPN Değerlendirmesi (1-10)")
        rpn_layout = QHBoxLayout(rpn_group)
        
        # Şiddet
        siddet_layout = QVBoxLayout()
        siddet_layout.addWidget(QLabel("Şiddet (S)"))
        self.spin_siddet = QSpinBox()
        self.spin_siddet.setRange(1, 10)
        self.spin_siddet.setValue(5)
        self.spin_siddet.valueChanged.connect(self._calculate_rpn)
        siddet_layout.addWidget(self.spin_siddet)
        rpn_layout.addLayout(siddet_layout)
        
        rpn_layout.addWidget(QLabel("×"))
        
        # Olasılık
        olasilik_layout = QVBoxLayout()
        olasilik_layout.addWidget(QLabel("Olasılık (O)"))
        self.spin_olasilik = QSpinBox()
        self.spin_olasilik.setRange(1, 10)
        self.spin_olasilik.setValue(5)
        self.spin_olasilik.valueChanged.connect(self._calculate_rpn)
        olasilik_layout.addWidget(self.spin_olasilik)
        rpn_layout.addLayout(olasilik_layout)
        
        rpn_layout.addWidget(QLabel("×"))
        
        # Tespit
        tespit_layout = QVBoxLayout()
        tespit_layout.addWidget(QLabel("Tespit (D)"))
        self.spin_tespit = QSpinBox()
        self.spin_tespit.setRange(1, 10)
        self.spin_tespit.setValue(5)
        self.spin_tespit.valueChanged.connect(self._calculate_rpn)
        tespit_layout.addWidget(self.spin_tespit)
        rpn_layout.addLayout(tespit_layout)
        
        rpn_layout.addWidget(QLabel("="))
        
        # RPN
        rpn_result_layout = QVBoxLayout()
        rpn_result_layout.addWidget(QLabel("RPN"))
        self.lbl_rpn = QLabel("125")
        self.lbl_rpn.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        rpn_result_layout.addWidget(self.lbl_rpn)
        rpn_layout.addLayout(rpn_result_layout)
        
        tab2_layout.addWidget(rpn_group)
        
        # Mevcut kontroller
        kontrol_group = QGroupBox("Mevcut Kontroller")
        kontrol_layout = QFormLayout(kontrol_group)
        
        self.txt_onleme = QTextEdit()
        self.txt_onleme.setMaximumHeight(50)
        self.txt_onleme.setPlaceholderText("Mevcut önleme kontrolü")
        kontrol_layout.addRow("Önleme:", self.txt_onleme)
        
        self.txt_tespit_kontrol = QTextEdit()
        self.txt_tespit_kontrol.setMaximumHeight(50)
        self.txt_tespit_kontrol.setPlaceholderText("Mevcut tespit kontrolü")
        kontrol_layout.addRow("Tespit:", self.txt_tespit_kontrol)
        
        tab2_layout.addWidget(kontrol_group)
        tab2_layout.addStretch()
        
        tabs.addTab(tab2, "📊 RPN Değerlendirmesi")
        
        # Tab 3: Aksiyonlar
        tab3 = QWidget()
        tab3_layout = QFormLayout(tab3)
        
        self.txt_aksiyon = QTextEdit()
        self.txt_aksiyon.setMaximumHeight(80)
        self.txt_aksiyon.setPlaceholderText("Önerilen düzeltici/önleyici aksiyon")
        tab3_layout.addRow("Önerilen Aksiyon:", self.txt_aksiyon)
        
        self.cmb_sorumlu = QComboBox()
        self.cmb_sorumlu.addItem("-- Seçiniz --", None)
        self._load_personeller()
        tab3_layout.addRow("Sorumlu:", self.cmb_sorumlu)
        
        self.date_hedef = QDateEdit()
        self.date_hedef.setDate(QDate.currentDate().addMonths(1))
        self.date_hedef.setCalendarPopup(True)
        tab3_layout.addRow("Hedef Tarih:", self.date_hedef)
        
        # Aksiyon sonrası RPN
        yeni_rpn_group = QGroupBox("Aksiyon Sonrası Beklenen RPN")
        yeni_rpn_layout = QHBoxLayout(yeni_rpn_group)
        
        self.spin_yeni_siddet = QSpinBox()
        self.spin_yeni_siddet.setRange(1, 10)
        self.spin_yeni_siddet.valueChanged.connect(self._calculate_yeni_rpn)
        yeni_rpn_layout.addWidget(QLabel("S:"))
        yeni_rpn_layout.addWidget(self.spin_yeni_siddet)
        
        self.spin_yeni_olasilik = QSpinBox()
        self.spin_yeni_olasilik.setRange(1, 10)
        self.spin_yeni_olasilik.valueChanged.connect(self._calculate_yeni_rpn)
        yeni_rpn_layout.addWidget(QLabel("O:"))
        yeni_rpn_layout.addWidget(self.spin_yeni_olasilik)
        
        self.spin_yeni_tespit = QSpinBox()
        self.spin_yeni_tespit.setRange(1, 10)
        self.spin_yeni_tespit.valueChanged.connect(self._calculate_yeni_rpn)
        yeni_rpn_layout.addWidget(QLabel("D:"))
        yeni_rpn_layout.addWidget(self.spin_yeni_tespit)
        
        self.lbl_yeni_rpn = QLabel("= 0")
        self.lbl_yeni_rpn.setStyleSheet("font-weight: bold;")
        yeni_rpn_layout.addWidget(self.lbl_yeni_rpn)
        
        tab3_layout.addRow(yeni_rpn_group)
        
        # Sınıflandırma
        sinif_layout = QHBoxLayout()
        self.chk_ozel = QCheckBox("Özel Karakteristik")
        sinif_layout.addWidget(self.chk_ozel)
        
        self.cmb_sinif = QComboBox()
        self.cmb_sinif.addItems(["", "CC", "SC", "HI", "SI"])
        sinif_layout.addWidget(QLabel("Sınıf:"))
        sinif_layout.addWidget(self.cmb_sinif)
        sinif_layout.addStretch()
        tab3_layout.addRow("", sinif_layout)
        
        tabs.addTab(tab3, "🎯 Aksiyonlar")
        
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
    
    def _load_personeller(self):
        """Personel listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_sorumlu.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception:
            pass
    
    def _calculate_rpn(self):
        """RPN hesapla ve göster"""
        rpn = self.spin_siddet.value() * self.spin_olasilik.value() * self.spin_tespit.value()
        self.lbl_rpn.setText(str(rpn))
        self.lbl_rpn.setStyleSheet(f"font-size: 24px; font-weight: bold; padding: 10px; color: {get_rpn_color(rpn)};")
    
    def _calculate_yeni_rpn(self):
        """Yeni RPN hesapla"""
        s = self.spin_yeni_siddet.value()
        o = self.spin_yeni_olasilik.value()
        d = self.spin_yeni_tespit.value()
        if s and o and d:
            rpn = s * o * d
            self.lbl_yeni_rpn.setText(f"= {rpn}")
            self.lbl_yeni_rpn.setStyleSheet(f"font-weight: bold; color: {get_rpn_color(rpn)};")
        else:
            self.lbl_yeni_rpn.setText("= 0")
    
    def _load_data(self):
        """Mevcut satır verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sira_no, proses_adimi, potansiyel_hata_modu, potansiyel_hata_etkisi,
                       potansiyel_hata_nedeni, siddet, olasilik, tespit,
                       mevcut_onleme_kontrolu, mevcut_tespit_kontrolu,
                       onerilen_aksiyon, aksiyon_sorumlu_id, aksiyon_hedef_tarih,
                       yeni_siddet, yeni_olasilik, yeni_tespit,
                       ozel_karakteristik, sinif
                FROM kalite.fmea_satirlar WHERE id = ?
            """, (self.satir_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.spin_sira.setValue(row[0] or 1)
                self.txt_proses.setText(row[1] or "")
                self.txt_hata_modu.setPlainText(row[2] or "")
                self.txt_hata_etkisi.setPlainText(row[3] or "")
                self.txt_hata_nedeni.setPlainText(row[4] or "")
                self.spin_siddet.setValue(row[5] or 1)
                self.spin_olasilik.setValue(row[6] or 1)
                self.spin_tespit.setValue(row[7] or 1)
                self.txt_onleme.setPlainText(row[8] or "")
                self.txt_tespit_kontrol.setPlainText(row[9] or "")
                self.txt_aksiyon.setPlainText(row[10] or "")
                
                if row[11]:
                    idx = self.cmb_sorumlu.findData(row[11])
                    if idx >= 0: self.cmb_sorumlu.setCurrentIndex(idx)
                
                if row[12]:
                    self.date_hedef.setDate(QDate(row[12].year, row[12].month, row[12].day))
                
                self.spin_yeni_siddet.setValue(row[13] or 0)
                self.spin_yeni_olasilik.setValue(row[14] or 0)
                self.spin_yeni_tespit.setValue(row[15] or 0)
                self.chk_ozel.setChecked(row[16] or False)
                
                if row[17]:
                    idx = self.cmb_sinif.findText(row[17])
                    if idx >= 0: self.cmb_sinif.setCurrentIndex(idx)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _save(self):
        """Satırı kaydet"""
        proses = self.txt_proses.text().strip()
        hata_modu = self.txt_hata_modu.toPlainText().strip()
        
        if not proses or not hata_modu:
            QMessageBox.warning(self, "Uyarı", "Proses ve Hata Modu zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            yeni_s = self.spin_yeni_siddet.value() if self.spin_yeni_siddet.value() > 0 else None
            yeni_o = self.spin_yeni_olasilik.value() if self.spin_yeni_olasilik.value() > 0 else None
            yeni_d = self.spin_yeni_tespit.value() if self.spin_yeni_tespit.value() > 0 else None
            
            if self.satir_id:
                cursor.execute("""
                    UPDATE kalite.fmea_satirlar SET
                        sira_no = ?, proses_adimi = ?, potansiyel_hata_modu = ?,
                        potansiyel_hata_etkisi = ?, potansiyel_hata_nedeni = ?,
                        siddet = ?, olasilik = ?, tespit = ?,
                        mevcut_onleme_kontrolu = ?, mevcut_tespit_kontrolu = ?,
                        onerilen_aksiyon = ?, aksiyon_sorumlu_id = ?, aksiyon_hedef_tarih = ?,
                        yeni_siddet = ?, yeni_olasilik = ?, yeni_tespit = ?,
                        ozel_karakteristik = ?, sinif = ?
                    WHERE id = ?
                """, (
                    self.spin_sira.value(), proses, hata_modu,
                    self.txt_hata_etkisi.toPlainText().strip() or None,
                    self.txt_hata_nedeni.toPlainText().strip() or None,
                    self.spin_siddet.value(), self.spin_olasilik.value(), self.spin_tespit.value(),
                    self.txt_onleme.toPlainText().strip() or None,
                    self.txt_tespit_kontrol.toPlainText().strip() or None,
                    self.txt_aksiyon.toPlainText().strip() or None,
                    self.cmb_sorumlu.currentData(),
                    self.date_hedef.date().toPython() if self.txt_aksiyon.toPlainText().strip() else None,
                    yeni_s, yeni_o, yeni_d,
                    self.chk_ozel.isChecked(),
                    self.cmb_sinif.currentText() or None,
                    self.satir_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO kalite.fmea_satirlar
                    (fmea_id, sira_no, proses_adimi, potansiyel_hata_modu,
                     potansiyel_hata_etkisi, potansiyel_hata_nedeni,
                     siddet, olasilik, tespit,
                     mevcut_onleme_kontrolu, mevcut_tespit_kontrolu,
                     onerilen_aksiyon, aksiyon_sorumlu_id, aksiyon_hedef_tarih,
                     yeni_siddet, yeni_olasilik, yeni_tespit,
                     ozel_karakteristik, sinif)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.fmea_id, self.spin_sira.value(), proses, hata_modu,
                    self.txt_hata_etkisi.toPlainText().strip() or None,
                    self.txt_hata_nedeni.toPlainText().strip() or None,
                    self.spin_siddet.value(), self.spin_olasilik.value(), self.spin_tespit.value(),
                    self.txt_onleme.toPlainText().strip() or None,
                    self.txt_tespit_kontrol.toPlainText().strip() or None,
                    self.txt_aksiyon.toPlainText().strip() or None,
                    self.cmb_sorumlu.currentData(),
                    self.date_hedef.date().toPython() if self.txt_aksiyon.toPlainText().strip() else None,
                    yeni_s, yeni_o, yeni_d,
                    self.chk_ozel.isChecked(),
                    self.cmb_sinif.currentText() or None
                ))
            
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class FMEADialog(QDialog):
    """FMEA ekleme/düzenleme ana dialog"""
    
    def __init__(self, theme: dict, parent=None, fmea_id=None):
        super().__init__(parent)
        self.theme = theme
        self.fmea_id = fmea_id
        self.setWindowTitle("FMEA Oluştur" if not fmea_id else "FMEA Düzenle")
        self.setMinimumSize(1000, 700)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        
        if fmea_id:
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
            QTabWidget::pane {{ border: 1px solid {self.theme.get('border')}; }}
            QTabBar::tab {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 20px; }}
            QTabBar::tab:selected {{ background: {self.theme.get('primary')}; color: white; }}
        """)
        
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        # Tab 1: Genel Bilgiler
        tab_genel = QWidget()
        genel_layout = QFormLayout(tab_genel)
        
        self.txt_fmea_no = QLineEdit()
        self.txt_fmea_no.setPlaceholderText("Örn: FMEA-2024-001")
        genel_layout.addRow("FMEA No*:", self.txt_fmea_no)
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["PROSES", "TASARIM", "SISTEM"])
        genel_layout.addRow("FMEA Tipi:", self.cmb_tip)
        
        self.spin_revizyon = QSpinBox()
        self.spin_revizyon.setRange(1, 99)
        genel_layout.addRow("Revizyon:", self.spin_revizyon)
        
        self.txt_baslik = QLineEdit()
        self.txt_baslik.setPlaceholderText("FMEA başlığı")
        genel_layout.addRow("Başlık*:", self.txt_baslik)
        
        self.cmb_musteri = QComboBox()
        genel_layout.addRow("Müşteri:", self.cmb_musteri)
        
        self.cmb_urun = QComboBox()
        genel_layout.addRow("Ürün:", self.cmb_urun)
        
        self.cmb_hazirlayan = QComboBox()
        genel_layout.addRow("Hazırlayan:", self.cmb_hazirlayan)
        
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["TASLAK", "ONAY_BEKLIYOR", "ONAYLANDI", "IPTAL"])
        genel_layout.addRow("Durum:", self.cmb_durum)
        
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(80)
        genel_layout.addRow("Açıklama:", self.txt_aciklama)
        
        tabs.addTab(tab_genel, "📋 Genel Bilgiler")
        
        # Tab 2: Hata Modları
        tab_satirlar = QWidget()
        satirlar_layout = QVBoxLayout(tab_satirlar)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        btn_ekle = QPushButton("➕ Hata Modu Ekle")
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
        
        # RPN özeti
        self.lbl_rpn_ozet = QLabel("Toplam: 0 | Kritik (≥200): 0 | Yüksek (≥120): 0")
        self.lbl_rpn_ozet.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        toolbar.addWidget(self.lbl_rpn_ozet)
        
        satirlar_layout.addLayout(toolbar)
        
        # Tablo
        self.table_satirlar = QTableWidget()
        self.table_satirlar.setColumnCount(10)
        self.table_satirlar.setHorizontalHeaderLabels([
            "ID", "Sıra", "Proses", "Hata Modu", "S", "O", "D", "RPN", "Aksiyon", "Yeni RPN"
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
            }}
        """)
        
        header = self.table_satirlar.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(8, QHeaderView.Stretch)
        self.table_satirlar.setColumnWidth(1, 60)
        self.table_satirlar.setColumnWidth(2, 120)
        self.table_satirlar.setColumnWidth(4, 60)
        self.table_satirlar.setColumnWidth(5, 60)
        self.table_satirlar.setColumnWidth(6, 60)
        self.table_satirlar.setColumnWidth(7, 60)
        self.table_satirlar.setColumnWidth(9, 70)
        
        self.table_satirlar.doubleClicked.connect(self._edit_satir)
        satirlar_layout.addWidget(self.table_satirlar)
        
        tabs.addTab(tab_satirlar, "⚠️ Hata Modları")
        
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
            
            # Önce müşteri listesi - StokKartlari'ndan benzersiz müşteriler
            self.cmb_musteri.addItem("-- Müşteri Seçiniz --", None)
            cursor.execute("""
                SELECT DISTINCT c.id, c.unvan 
                FROM musteri.cariler c
                INNER JOIN stok.urunler u ON c.id = u.cari_id
                WHERE c.unvan IS NOT NULL AND c.unvan <> ''
                ORDER BY c.unvan
            """)
            for row in cursor.fetchall():
                self.cmb_musteri.addItem(row[1], row[0])  # unvan göster, id sakla
            
            # Müşteri değişince ürünleri güncelle
            self.cmb_musteri.currentIndexChanged.connect(self._on_musteri_changed)
            
            # Ürün listesi boş başlar
            self.cmb_urun.addItem("-- Önce Müşteri Seçin --", None)
            
            self.cmb_hazirlayan.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_hazirlayan.addItem(row[1], row[0])
            
            conn.close()
        except Exception:
            pass
    
    def _on_musteri_changed(self):
        """Müşteri değiştiğinde ürünleri güncelle"""
        cari_id = self.cmb_musteri.currentData()
        self._load_urunler(cari_id)
    
    def _load_urunler(self, cari_id=None):
        """Seçilen müşteriye ait ürün listesi"""
        self.cmb_urun.clear()
        self.cmb_urun.addItem("-- Ürün Seçin --", None)
        if not cari_id:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.urun_kodu + ' - ' + u.urun_adi 
                FROM stok.urunler u
                WHERE u.cari_id = ? AND u.aktif_mi = 1
                ORDER BY u.urun_kodu
            """, (cari_id,))
            for row in cursor.fetchall():
                if row[0]:
                    self.cmb_urun.addItem(row[1], row[0])
            conn.close()
        except Exception:
            pass
    
    def _load_data(self):
        """FMEA verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.fmea_no, f.fmea_tipi, f.revizyon, f.baslik, f.urun_id, f.cari_id,
                       f.hazirlayan_id, f.durum, f.aciklama, c.unvan
                FROM kalite.fmea f
                LEFT JOIN musteri.cariler c ON f.cari_id = c.id
                WHERE f.id = ?
            """, (self.fmea_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_fmea_no.setText(row[0] or "")
                self.txt_fmea_no.setEnabled(False)
                
                idx = self.cmb_tip.findText(row[1] or "PROSES")
                if idx >= 0: self.cmb_tip.setCurrentIndex(idx)
                
                self.spin_revizyon.setValue(row[2] or 1)
                self.txt_baslik.setText(row[3] or "")
                
                # Önce müşteriyi set et (cari_unvani ile)
                cari_unvani = row[9]  # JOIN'den gelen unvan
                if cari_unvani:
                    idx = self.cmb_musteri.findData(cari_unvani)
                    if idx >= 0: 
                        self.cmb_musteri.setCurrentIndex(idx)
                        # Ürünleri yükle
                        self._load_urunler(cari_unvani)
                
                # Sonra ürünü set et
                if row[4]:
                    idx = self.cmb_urun.findData(row[4])
                    if idx >= 0: self.cmb_urun.setCurrentIndex(idx)
                
                if row[6]:
                    idx = self.cmb_hazirlayan.findData(row[6])
                    if idx >= 0: self.cmb_hazirlayan.setCurrentIndex(idx)
                
                if row[7]:
                    idx = self.cmb_durum.findText(row[7])
                    if idx >= 0: self.cmb_durum.setCurrentIndex(idx)
                
                self.txt_aciklama.setPlainText(row[8] or "")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _load_satirlar(self):
        """Hata modlarını yükle"""
        if not self.fmea_id:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sira_no, proses_adimi, potansiyel_hata_modu,
                       siddet, olasilik, tespit,
                       onerilen_aksiyon, yeni_siddet, yeni_olasilik, yeni_tespit
                FROM kalite.fmea_satirlar
                WHERE fmea_id = ? AND aktif_mi = 1
                ORDER BY sira_no
            """, (self.fmea_id,))
            rows = cursor.fetchall()
            conn.close()
            
            self.table_satirlar.setRowCount(len(rows))
            kritik = 0
            yuksek = 0
            
            for i, row in enumerate(rows):
                self.table_satirlar.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_satirlar.setItem(i, 1, QTableWidgetItem(str(row[1])))
                self.table_satirlar.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.table_satirlar.setItem(i, 3, QTableWidgetItem(row[3][:50] + "..." if len(row[3] or "") > 50 else row[3] or ""))
                self.table_satirlar.setItem(i, 4, QTableWidgetItem(str(row[4])))
                self.table_satirlar.setItem(i, 5, QTableWidgetItem(str(row[5])))
                self.table_satirlar.setItem(i, 6, QTableWidgetItem(str(row[6])))
                
                rpn = row[4] * row[5] * row[6]
                rpn_item = QTableWidgetItem(str(rpn))
                rpn_item.setForeground(QColor(get_rpn_color(rpn)))
                rpn_item.setData(Qt.FontRole, QFont("", -1, QFont.Bold))
                self.table_satirlar.setItem(i, 7, rpn_item)
                
                if rpn >= 200: kritik += 1
                elif rpn >= 120: yuksek += 1
                
                self.table_satirlar.setItem(i, 8, QTableWidgetItem(row[7][:30] + "..." if row[7] and len(row[7]) > 30 else row[7] or "-"))
                
                # Yeni RPN
                if row[8] and row[9] and row[10]:
                    yeni_rpn = row[8] * row[9] * row[10]
                    yeni_rpn_item = QTableWidgetItem(str(yeni_rpn))
                    yeni_rpn_item.setForeground(QColor(get_rpn_color(yeni_rpn)))
                    self.table_satirlar.setItem(i, 9, yeni_rpn_item)
                else:
                    self.table_satirlar.setItem(i, 9, QTableWidgetItem("-"))
            
            self.lbl_rpn_ozet.setText(f"Toplam: {len(rows)} | Kritik (≥200): {kritik} | Yüksek (≥120): {yuksek}")
            
        except Exception as e:
            print(f"Satır yükleme hatası: {e}")
    
    def _add_satir(self):
        if not self.fmea_id:
            QMessageBox.warning(self, "Uyarı", "Önce FMEA'yı kaydedin!")
            return
        dialog = FMEASatirDialog(self.theme, self.fmea_id, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
    
    def _edit_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir satır seçin!")
            return
        satir_id = int(self.table_satirlar.item(row, 0).text())
        dialog = FMEASatirDialog(self.theme, self.fmea_id, self, satir_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_satirlar()
    
    def _delete_satir(self):
        row = self.table_satirlar.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir satır seçin!")
            return
        
        satir_id = int(self.table_satirlar.item(row, 0).text())
        reply = QMessageBox.question(self, "Onay", "Bu hata modunu silmek istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE kalite.fmea_satirlar SET aktif_mi = 0 WHERE id = ?", (satir_id,))
                conn.commit()
                conn.close()
                self._load_satirlar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
    
    def _save(self):
        fmea_no = self.txt_fmea_no.text().strip()
        baslik = self.txt_baslik.text().strip()
        
        if not fmea_no or not baslik:
            QMessageBox.warning(self, "Uyarı", "FMEA No ve Başlık zorunludur!")
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
            
            if self.fmea_id:
                cursor.execute("""
                    UPDATE kalite.fmea SET
                        fmea_tipi = ?, revizyon = ?, baslik = ?, urun_id = ?,
                        cari_id = ?, hazirlayan_id = ?, durum = ?, aciklama = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    self.cmb_tip.currentText(), self.spin_revizyon.value(), baslik,
                    self.cmb_urun.currentData(), cari_id,
                    self.cmb_hazirlayan.currentData(), self.cmb_durum.currentText(),
                    self.txt_aciklama.toPlainText().strip() or None,
                    self.fmea_id
                ))
            else:
                cursor.execute("SELECT COUNT(*) FROM kalite.fmea WHERE fmea_no = ?", (fmea_no,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu FMEA No zaten kullanılıyor!")
                    conn.close()
                    return
                
                cursor.execute("""
                    INSERT INTO kalite.fmea
                    (fmea_no, fmea_tipi, revizyon, baslik, urun_id, cari_id,
                     hazirlayan_id, durum, aciklama)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fmea_no, self.cmb_tip.currentText(), self.spin_revizyon.value(), baslik,
                    self.cmb_urun.currentData(), cari_id,
                    self.cmb_hazirlayan.currentData(), self.cmb_durum.currentText(),
                    self.txt_aciklama.toPlainText().strip() or None
                ))
                self.fmea_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "FMEA kaydedildi!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class FMEAYonetimiPage(BasePage):
    """FMEA Yönetimi Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("📊 FMEA Yönetimi")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni FMEA")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
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
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["Tüm Tipler", "PROSES", "TASARIM", "SISTEM"])
        self.cmb_tip.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px; color: {self.theme.get('text')};")
        self.cmb_tip.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_tip)
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setFixedSize(60, 36)
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border-radius: 6px; font-size: 12px;")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "FMEA No", "Tip", "Başlık", "Ürün", "Satır", "Max RPN", "Durum"
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
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 100)
        
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
                SELECT 
                    f.id, f.fmea_no, f.fmea_tipi, f.baslik,
                    u.urun_kodu,
                    (SELECT COUNT(*) FROM kalite.fmea_satirlar WHERE fmea_id = f.id AND aktif_mi = 1),
                    (SELECT MAX(siddet * olasilik * tespit) FROM kalite.fmea_satirlar WHERE fmea_id = f.id AND aktif_mi = 1),
                    f.durum
                FROM kalite.fmea f
                LEFT JOIN stok.urunler u ON f.urun_id = u.id
                WHERE f.aktif_mi = 1
                ORDER BY f.olusturma_tarihi DESC
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 6 and val:  # Max RPN
                    item = QTableWidgetItem(str(val))
                    item.setForeground(QColor(get_rpn_color(val)))
                    item.setData(Qt.FontRole, QFont("", -1, QFont.Bold))
                elif j == 7:  # Durum
                    item = QTableWidgetItem(str(val) if val else "")
                    colors = {'TASLAK': self.theme.get('warning'), 'ONAYLANDI': self.theme.get('success'), 'IPTAL': self.theme.get('danger')}
                    item.setForeground(QColor(colors.get(val, self.theme.get('text'))))
                else:
                    item = QTableWidgetItem(str(val) if val else "-")
                self.table.setItem(i, j, item)
        
        self.lbl_stat.setText(f"Toplam: {len(rows)} FMEA")
    
    def _filter(self):
        tip = self.cmb_tip.currentText()
        if tip == "Tüm Tipler":
            self._display_data(self.all_rows)
        else:
            filtered = [r for r in self.all_rows if r[2] == tip]
            self._display_data(filtered)
    
    def _yeni(self):
        dialog = FMEADialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir FMEA seçin!")
            return
        fmea_id = int(self.table.item(row, 0).text())
        dialog = FMEADialog(self.theme, self, fmea_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _sil(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir FMEA seçin!")
            return
        
        fmea_id = int(self.table.item(row, 0).text())
        fmea_no = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(self, "Onay", f"'{fmea_no}' FMEA'yı silmek istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE kalite.fmea SET aktif_mi = 0 WHERE id = ?", (fmea_id,))
                conn.commit()
                conn.close()
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
