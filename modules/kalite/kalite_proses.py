# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Proses Kalite / İlk Ürün Onay Formu (FR.75)
[MODERNIZED UI - v3.0]

Üretim başında ilk ürün kontrolü
"""
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QSpinBox, QTextEdit, QSplitter, QWidget, QGridLayout,
    QGroupBox, QFormLayout, QCheckBox, QDoubleSpinBox, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QColor, QFont, QPixmap

from components.base_page import BasePage
from core.database import get_db_connection


def get_modern_style(theme: dict) -> dict:
    """Modern tema renkleri - TÜM MODÜLLERDE AYNI"""
    t = theme or {}
    return {
        'card_bg': t.get('bg_card', '#151B23'),
        'input_bg': t.get('bg_input', '#232C3B'),
        'border': t.get('border', '#1E2736'),
        'text': t.get('text', '#E8ECF1'),
        'text_secondary': t.get('text_secondary', '#8896A6'),
        'text_muted': t.get('text_muted', '#5C6878'),
        'primary': t.get('primary', '#DC2626'),
        'primary_hover': t.get('primary_hover', '#9B1818'),
        'success': t.get('success', '#10B981'),
        'warning': t.get('warning', '#F59E0B'),
        'error': t.get('error', '#EF4444'),
        'danger': t.get('error', '#EF4444'),
        'info': t.get('info', '#3B82F6'),
        'bg_main': t.get('bg_main', '#0F1419'),
        'bg_hover': t.get('bg_hover', '#1C2430'),
        'bg_selected': t.get('bg_selected', '#1E1215'),
        'border_light': t.get('border_light', '#2A3545'),
        'border_input': t.get('border_input', '#1E2736'),
        'card_solid': t.get('bg_card_solid', '#151B23'),
        'gradient': t.get('gradient_css', ''),
    }


class IlkUrunOnayDialog(QDialog):
    """İlk Ürün Onay detay dialog'u"""
    
    def __init__(self, theme: dict, is_emri_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.is_emri_data = is_emri_data
        self.test_sonuclari = []
        self.foto_paths = []
        self.setWindowTitle("İlk Ürün Onay Formu - FR.75")
        self.setMinimumSize(900, 700)
        self._load_test_turleri()
        self._setup_ui()
    
    def _load_test_turleri(self):
        """Test türlerini yükle"""
        self.test_turleri = []
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Kalite test türleri tablosu varsa
            cursor.execute("""
                SELECT id, kod, ad, min_deger, max_deger, birim
                FROM tanim.kalite_testleri
                WHERE aktif_mi = 1
                ORDER BY sira_no, kod
            """)
            for row in cursor.fetchall():
                self.test_turleri.append({
                    'id': row[0], 'kod': row[1], 'ad': row[2],
                    'min': row[3], 'max': row[4], 'birim': row[5]
                })
            conn.close()
        except:
            # Varsayılan testler
            self.test_turleri = [
                {'id': 1, 'kod': 'KAL', 'ad': 'Kalınlık Ölçümü', 'min': 8, 'max': 25, 'birim': 'µm'},
                {'id': 2, 'kod': 'YAP', 'ad': 'Yapışma Testi', 'min': None, 'max': None, 'birim': 'OK/NOK'},
                {'id': 3, 'kod': 'GOR', 'ad': 'Görsel Kontrol', 'min': None, 'max': None, 'birim': 'OK/NOK'},
                {'id': 4, 'kod': 'TUZ', 'ad': 'Tuz Testi', 'min': 72, 'max': None, 'birim': 'saat'},
            ]
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main', '#0f172a')}; }}
            QLabel {{ color: {self.theme.get('text', '#ffffff')}; }}
            QGroupBox {{ 
                color: {self.theme.get('primary', '#3b82f6')}; 
                font-weight: bold; 
                border: 1px solid {self.theme.get('border', 'rgba(51, 65, 85, 0.5)')}; 
                border-radius: 8px; 
                margin-top: 12px; 
                padding-top: 12px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        header = QHBoxLayout()
        title = QLabel("📋 İLK ÜRÜN ONAY FORMU (FR.75)")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary', '#3b82f6')};")
        header.addWidget(title)
        header.addStretch()
        
        tarih_lbl = QLabel(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        tarih_lbl.setStyleSheet(f"color: {self.theme.get('text_secondary', '#94a3b8')};")
        header.addWidget(tarih_lbl)
        layout.addLayout(header)
        
        # Ana içerik - Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # SOL - İş Emri Bilgileri
        sol_widget = QWidget()
        sol_layout = QVBoxLayout(sol_widget)
        sol_layout.setContentsMargins(0, 0, 0, 0)
        
        # İş Emri Bilgileri
        bilgi_group = QGroupBox("📦 İş Emri Bilgileri")
        bilgi_form = QFormLayout()
        bilgi_form.setSpacing(8)
        
        self.lbl_musteri = QLabel(self.is_emri_data.get('cari_unvani', '-'))
        self.lbl_musteri.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold;")
        bilgi_form.addRow("Müşteri:", self.lbl_musteri)
        
        self.lbl_stok = QLabel(f"{self.is_emri_data.get('stok_kodu', '')} - {self.is_emri_data.get('stok_adi', '')}")
        self.lbl_stok.setStyleSheet(f"color: {self.theme.get('text')};")
        self.lbl_stok.setWordWrap(True)
        bilgi_form.addRow("Ürün:", self.lbl_stok)
        
        self.lbl_is_emri = QLabel(self.is_emri_data.get('is_emri_no', '-'))
        self.lbl_is_emri.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold;")
        bilgi_form.addRow("İş Emri No:", self.lbl_is_emri)
        
        self.lbl_lot = QLabel(self.is_emri_data.get('lot_no', '-'))
        self.lbl_lot.setStyleSheet(f"color: {self.theme.get('warning', '#f59e0b')}; font-weight: bold;")
        bilgi_form.addRow("Lot No:", self.lbl_lot)
        
        self.lbl_miktar = QLabel(str(self.is_emri_data.get('toplam_miktar', 0)))
        bilgi_form.addRow("Planlanan Miktar:", self.lbl_miktar)
        
        self.lbl_hat = QLabel(self.is_emri_data.get('hat_adi', '-'))
        bilgi_form.addRow("Üretim Hattı:", self.lbl_hat)
        
        bilgi_group.setLayout(bilgi_form)
        sol_layout.addWidget(bilgi_group)
        
        # Kontrol Eden
        kontrol_group = QGroupBox("👤 Kontrol Bilgileri")
        kontrol_form = QFormLayout()
        
        self.cmb_operator = QComboBox()
        self.cmb_operator.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self._load_personel(self.cmb_operator)
        kontrol_form.addRow("Hat Operatörü:", self.cmb_operator)
        
        self.cmb_kalite = QComboBox()
        self.cmb_kalite.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self._load_personel(self.cmb_kalite)
        kontrol_form.addRow("Kalite Sorumlusu:", self.cmb_kalite)
        
        self.txt_test_adedi = QSpinBox()
        self.txt_test_adedi.setRange(1, 100)
        self.txt_test_adedi.setValue(3)
        self.txt_test_adedi.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        kontrol_form.addRow("Test Adedi:", self.txt_test_adedi)
        
        kontrol_group.setLayout(kontrol_form)
        sol_layout.addWidget(kontrol_group)
        
        # Fotoğraflar
        foto_group = QGroupBox("📷 Fotoğraflar")
        foto_layout = QVBoxLayout()
        
        self.foto_btns = []
        for i in range(3):
            btn = QPushButton(f"📷 Fotoğraf {i+1} Ekle")
            btn.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px;")
            btn.clicked.connect(lambda _, idx=i: self._foto_ekle(idx))
            foto_layout.addWidget(btn)
            self.foto_btns.append(btn)
        
        foto_group.setLayout(foto_layout)
        sol_layout.addWidget(foto_group)
        
        sol_layout.addStretch()
        splitter.addWidget(sol_widget)
        
        # SAĞ - Test Sonuçları
        sag_widget = QWidget()
        sag_layout = QVBoxLayout(sag_widget)
        sag_layout.setContentsMargins(0, 0, 0, 0)
        
        test_group = QGroupBox("🔬 Test Sonuçları")
        test_layout = QVBoxLayout()
        
        # Test tablosu
        self.test_table = QTableWidget()
        self.test_table.setColumnCount(6)
        self.test_table.setHorizontalHeaderLabels([
            "Test", "Kriter", "Min", "Max", "Ölçüm", "Sonuç"
        ])
        
        # Sütun genişliklerini ayarla - Ölçüm ve Sonuç için DAHA GENİŞ
        self.test_table.setColumnWidth(0, 120)  # Test
        self.test_table.setColumnWidth(1, 70)   # Kriter
        self.test_table.setColumnWidth(2, 50)   # Min
        self.test_table.setColumnWidth(3, 50)   # Max
        self.test_table.setColumnWidth(4, 120)  # Ölçüm - GENİŞ
        self.test_table.setColumnWidth(5, 120)  # Sonuç - GENİŞ
        self.test_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        
        self.test_table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card', '#1e293b')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                gridline-color: {self.theme.get('border')};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QHeaderView::section {{
                background: {self.theme.get('bg_sidebar')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)
        
        # Input stili - orijinal koyu tema
        input_style = f"""
            background: {self.theme.get('bg_input', '#2d3548')};
            color: {self.theme.get('text', '#fff')};
            border: 1px solid {self.theme.get('border', '#3d4454')};
            border-radius: 4px;
            padding: 8px 10px;
            min-width: 80px;
        """
        
        # Test satırlarını ekle
        self.test_table.setRowCount(len(self.test_turleri))
        self.test_inputs = []
        self.test_combos = []
        
        for i, test in enumerate(self.test_turleri):
            # Satır yüksekliğini artır
            self.test_table.setRowHeight(i, 45)
            
            self.test_table.setItem(i, 0, QTableWidgetItem(test['ad']))
            self.test_table.setItem(i, 1, QTableWidgetItem(test.get('birim', '')))
            self.test_table.setItem(i, 2, QTableWidgetItem(str(test.get('min', '-') or '-')))
            self.test_table.setItem(i, 3, QTableWidgetItem(str(test.get('max', '-') or '-')))
            
            # Ölçüm input
            if test.get('birim') == 'OK/NOK':
                inp = QComboBox()
                inp.addItems(['', 'OK', 'NOK'])
                inp.setStyleSheet(input_style)
                inp.setMinimumWidth(100)
            else:
                inp = QLineEdit()
                inp.setStyleSheet(input_style)
                inp.setPlaceholderText("Değer girin")
                inp.setMinimumWidth(100)
            self.test_table.setCellWidget(i, 4, inp)
            self.test_inputs.append(inp)
            
            # Sonuç combo
            sonuc = QComboBox()
            sonuc.addItems(['', 'UYGUN', 'UYGUN DEĞİL'])
            sonuc.setStyleSheet(input_style)
            sonuc.setMinimumWidth(100)
            self.test_table.setCellWidget(i, 5, sonuc)
            self.test_combos.append(sonuc)
        
        test_layout.addWidget(self.test_table)
        test_group.setLayout(test_layout)
        sag_layout.addWidget(test_group)
        
        # Görsel Kontrol
        gorsel_group = QGroupBox("👁️ Görsel Kontrol")
        gorsel_layout = QVBoxLayout()
        
        self.gorsel_checks = {}
        gorsel_items = [
            'Renk Uygunluğu', 'Yüzey Kalitesi', 'Leke/Çizik', 
            'Deformasyon', 'Kaplama Homojenliği'
        ]
        
        for item in gorsel_items:
            cb = QCheckBox(item)
            cb.setStyleSheet(f"color: {self.theme.get('text')}; padding: 4px;")
            gorsel_layout.addWidget(cb)
            self.gorsel_checks[item] = cb
        
        gorsel_group.setLayout(gorsel_layout)
        sag_layout.addWidget(gorsel_group)
        
        # Açıklama
        aciklama_lbl = QLabel("📝 Açıklama / Not:")
        sag_layout.addWidget(aciklama_lbl)
        
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(80)
        self.txt_aciklama.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        self.txt_aciklama.setPlaceholderText("Varsa açıklama yazın...")
        sag_layout.addWidget(self.txt_aciklama)
        
        splitter.addWidget(sag_widget)
        splitter.setSizes([300, 700])  # Sol 300px, Sağ 700px (daha geniş)
        
        layout.addWidget(splitter, 1)
        
        # Alt butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 24px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_red = QPushButton("❌ Reddet")
        btn_red.setStyleSheet(f"background: {self.theme.get('danger', '#ef4444')}; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold;")
        btn_red.clicked.connect(lambda: self._kaydet('RED'))
        btn_layout.addWidget(btn_red)
        
        btn_onayla = QPushButton("✅ Onayla")
        btn_onayla.setStyleSheet(f"background: {self.theme.get('success', '#22c55e')}; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold;")
        btn_onayla.clicked.connect(lambda: self._kaydet('ONAY'))
        btn_layout.addWidget(btn_onayla)
        
        layout.addLayout(btn_layout)
    
    def _load_personel(self, combo: QComboBox):
        """Personel listesi yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ad + ' ' + soyad FROM ik.personeller 
                WHERE aktif_mi = 1 ORDER BY ad, soyad
            """)
            combo.clear()
            combo.addItem("-- Seçin --", None)
            for row in cursor.fetchall():
                combo.addItem(row[1], row[0])
            conn.close()
        except Exception as e:
            print(f"Personel yüklenemedi: {e}")
    
    def _foto_ekle(self, idx: int):
        """Fotoğraf ekle"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Fotoğraf Seç", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            if len(self.foto_paths) <= idx:
                self.foto_paths.extend([''] * (idx + 1 - len(self.foto_paths)))
            self.foto_paths[idx] = path
            self.foto_btns[idx].setText(f"✅ Fotoğraf {idx+1} Seçildi")
            self.foto_btns[idx].setStyleSheet(f"background: {self.theme.get('success', '#22c55e')}; color: white; border: none; border-radius: 6px; padding: 10px;")
    
    def _kaydet(self, karar: str):
        """Kaydet"""
        operator_id = self.cmb_operator.currentData()
        kalite_id = self.cmb_kalite.currentData()
        
        if not operator_id or not kalite_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen operatör ve kalite sorumlusunu seçin!")
            return
        
        # Test sonuçlarını topla
        test_sonuclari = []
        for i, test in enumerate(self.test_turleri):
            inp = self.test_inputs[i]
            if isinstance(inp, QComboBox):
                deger = inp.currentText()
            else:
                deger = inp.text()
            
            sonuc = self.test_combos[i].currentText()
            test_sonuclari.append({
                'test_id': test['id'],
                'test_adi': test['ad'],
                'olcum': deger,
                'sonuc': sonuc
            })
        
        # Görsel kontrol
        gorsel_sonuc = {k: v.isChecked() for k, v in self.gorsel_checks.items()}
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Muayene kaydı
            cursor.execute("""
                INSERT INTO kalite.muayeneler 
                (uuid, muayene_no, muayene_tipi, tarih, is_emri_id, urun_id, lot_no, 
                 muayeneci_id, numune_miktari, sonuc, notlar, olusturma_tarihi, guncelleme_tarihi)
                OUTPUT INSERTED.id
                VALUES (NEWID(), ?, 'ILK_URUN', GETDATE(), ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (
                f"IU-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                self.is_emri_data.get('id'),
                self.is_emri_data.get('stok_id'),
                self.is_emri_data.get('lot_no'),
                kalite_id,
                self.txt_test_adedi.value(),
                'KABUL' if karar == 'ONAY' else 'RED',
                self.txt_aciklama.toPlainText()
            ))
            
            muayene_id = cursor.fetchone()[0]
            
            # Test detayları
            for ts in test_sonuclari:
                if ts['olcum']:
                    cursor.execute("""
                        INSERT INTO kalite.muayene_detaylar 
                        (uuid, muayene_id, kontrol_ozelligi, olcum_degeri_metin, sonuc)
                        VALUES (NEWID(), ?, ?, ?, ?)
                    """, (muayene_id, ts['test_adi'], ts['olcum'], ts['sonuc'] or 'BEKLEMEDE'))
            
            # İş emri durumunu güncelle (ilk_urun_onay kolonu YOK)
            if karar == 'ONAY':
                cursor.execute("""
                    UPDATE siparis.is_emirleri 
                    SET durum = 'URETIMDE', guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (self.is_emri_data.get('id'),))
            else:
                cursor.execute("""
                    UPDATE siparis.is_emirleri 
                    SET durum = 'ILK_URUN_RED', guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (self.is_emri_data.get('id'),))
            
            conn.commit()
            conn.close()
            
            # PDF RAPORU OLUŞTUR
            try:
                pdf_path = self._create_pdf_report(karar, test_sonuclari, gorsel_sonuc, muayene_id)
                msg = f"İlk ürün {'ONAYLANDI' if karar == 'ONAY' else 'REDDEDİLDİ'}!\n\nPDF raporu oluşturuldu:\n{pdf_path}"
            except Exception as pdf_err:
                print(f"PDF oluşturma hatası: {pdf_err}")
                msg = f"İlk ürün {'ONAYLANDI' if karar == 'ONAY' else 'REDDEDİLDİ'}!\n\n⚠️ PDF oluşturulamadı: {pdf_err}"
            
            QMessageBox.information(self, "✓ Başarılı", msg)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")
    
    def _create_pdf_report(self, karar: str, test_sonuclari: list, gorsel_sonuc: dict, muayene_id: int) -> str:
        """PDF raporu oluştur ve NAS'a kaydet"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # Türkçe karakter desteği için font kaydet
        default_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'
        
        # Birden fazla font yolu dene
        font_paths = [
            # Windows font yolları
            r'C:\Windows\Fonts\DejaVuSans.ttf',
            r'C:\Windows\Fonts\arial.ttf',
            r'C:\Windows\Fonts\calibri.ttf',
            r'C:\Windows\Fonts\tahoma.ttf',
            # Linux font yolları
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/TTF/DejaVuSans.ttf',
            # Relative paths
            'DejaVuSans.ttf',
            'arial.ttf',
        ]
        
        font_bold_paths = [
            r'C:\Windows\Fonts\DejaVuSans-Bold.ttf',
            r'C:\Windows\Fonts\arialbd.ttf',
            r'C:\Windows\Fonts\calibrib.ttf',
            r'C:\Windows\Fonts\tahomabd.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
            'DejaVuSans-Bold.ttf',
            'arialbd.ttf',
        ]
        
        # Normal font bul ve kaydet
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('TurkceFont', font_path))
                    default_font = 'TurkceFont'
                    print(f"✓ PDF Font yüklendi: {font_path}")
                    break
            except Exception as e:
                continue
        
        # Bold font bul ve kaydet
        for font_path in font_bold_paths:
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('TurkceFontBold', font_path))
                    bold_font = 'TurkceFontBold'
                    print(f"✓ PDF Bold Font yüklendi: {font_path}")
                    break
            except Exception as e:
                continue
        
        if default_font == 'Helvetica':
            print("⚠️ Türkçe destekli font bulunamadı, Helvetica kullanılıyor")
        
        # NAS yolu oluştur
        cari_adi = self.is_emri_data.get('cari_unvani', 'GENEL')
        stok_kodu = self.is_emri_data.get('stok_kodu', 'UNKNOWN')
        lot_no = self.is_emri_data.get('lot_no', 'LOT')
        
        # Geçersiz karakterleri temizle
        import re
        cari_safe = re.sub(r'[<>:"/\\|?*]', '_', cari_adi)
        
        from config import NAS_PATHS
        nas_base = NAS_PATHS["product_path"]
        klasor_yolu = os.path.join(nas_base, cari_safe, stok_kodu, "06_Ilk_Urun_Onaylari")
        
        # Klasör yoksa oluştur
        try:
            if not os.path.exists(klasor_yolu):
                os.makedirs(klasor_yolu)
        except Exception as e:
            print(f"Klasör oluşturma hatası: {e}")
            # Yedek yol - local
            klasor_yolu = os.path.expanduser("~/Desktop")
        
        # PDF dosya adı
        tarih_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"FR75_{lot_no}_{tarih_str}.pdf"
        pdf_path = os.path.join(klasor_yolu, pdf_filename)
        
        # PDF oluştur
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Başlık stili
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName=bold_font
        )
        
        # Başlık
        story.append(Paragraph("ILK URUN ONAY FORMU (FR.75)", title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # İş Emri Bilgileri Tablosu
        bilgi_data = [
            ['Musteri:', self.is_emri_data.get('cari_unvani', '-')],
            ['Urun:', f"{stok_kodu} - {self.is_emri_data.get('stok_adi', '')}"],
            ['Is Emri No:', self.is_emri_data.get('is_emri_no', '-')],
            ['Lot No:', lot_no],
            ['Planlanan Miktar:', str(self.is_emri_data.get('toplam_miktar', 0))],
            ['Uretim Hatti:', self.is_emri_data.get('hat_adi', '-')],
            ['Tarih:', datetime.now().strftime('%d.%m.%Y %H:%M')],
            ['Karar:', 'ONAYLANDI' if karar == 'ONAY' else 'REDDEDILDI']
        ]
        
        bilgi_table = Table(bilgi_data, colWidths=[5*cm, 12*cm])
        bilgi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), bold_font),
            ('FONTNAME', (1, 0), (1, -1), default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(bilgi_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Test Sonuçları
        test_header = Paragraph("<b>Test Sonuclari:</b>", ParagraphStyle(
            'TestHeader', parent=styles['Heading2'], fontName=bold_font))
        story.append(test_header)
        
        test_data = [['Test', 'Kriter', 'Min', 'Max', 'Olcum', 'Sonuc']]
        
        # Test sonuçlarını tabloya ekle
        for i, test in enumerate(self.test_turleri):
            # Ölçüm değerini al
            inp = self.test_inputs[i]
            if isinstance(inp, QComboBox):
                olcum = inp.currentText()
            else:
                olcum = inp.text()
            
            # Sonuç değerini al
            sonuc_combo = self.test_combos[i]
            sonuc = sonuc_combo.currentText()
            
            test_data.append([
                test['ad'],
                test.get('birim', ''),
                str(test.get('min', '-') or '-'),
                str(test.get('max', '-') or '-'),
                olcum or '-',
                sonuc or '-'
            ])
        
        test_table = Table(test_data, colWidths=[4*cm, 2*cm, 2*cm, 2*cm, 3*cm, 3*cm])
        test_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('FONTNAME', (0, 1), (-1, -1), default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(test_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Görsel Kontrol
        gorsel_header = Paragraph("<b>Gorsel Kontrol:</b>", ParagraphStyle(
            'GorselHeader', parent=styles['Heading2'], fontName=bold_font))
        story.append(gorsel_header)
        
        gorsel_data = [['Kontrol', 'Durum']]
        for k, v in gorsel_sonuc.items():
            gorsel_data.append([k, '✓' if v else '✗'])
        
        gorsel_table = Table(gorsel_data, colWidths=[10*cm, 5*cm])
        gorsel_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('FONTNAME', (0, 1), (-1, -1), default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(gorsel_table)
        
        # PDF'i kaydet
        doc.build(story)
        
        return pdf_path



class KaliteProsesPage(BasePage):
    """Proses Kalite / İlk Ürün Onay Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
        
        # Saat
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("🔬 Proses Kalite - İlk Ürün Onay")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text', '#fff')};")
        header.addWidget(title)
        header.addStretch()
        
        self.saat_label = QLabel()
        self.saat_label.setStyleSheet(f"color: {self.theme.get('text_muted', '#8a94a6')}; font-size: 18px; font-weight: bold;")
        header.addWidget(self.saat_label)
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 16px;")
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        layout.addLayout(header)
        
        # Bilgi kartı
        info_card = QFrame()
        info_card.setStyleSheet(f"background: {self.theme.get('bg_card', '#1e293b')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; padding: 12px;")
        info_layout = QHBoxLayout(info_card)
        
        info_text = QLabel("📋 İlk ürün onayı bekleyen iş emirleri aşağıda listelenmektedir. Üretim başlamadan önce ilk parçanın kalite kontrolü yapılmalıdır.")
        info_text.setStyleSheet(f"color: {self.theme.get('text_secondary', '#94a3b8')};")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_card)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "İş Emri No", "Müşteri", "Ürün", "Lot No", "Miktar", "Hat", "İşlem"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setColumnWidth(7, 120)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card', '#1e293b')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QHeaderView::section {{
                background: {self.theme.get('bg_sidebar')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)
        
        # İstatistik
        stat_layout = QHBoxLayout()
        
        self.stat_bekleyen = self._create_stat_card("⏳ Bekleyen", "0", self.theme.get('warning', '#f59e0b'))
        stat_layout.addWidget(self.stat_bekleyen)
        
        self.stat_onaylanan = self._create_stat_card("✅ Bugün Onaylanan", "0", self.theme.get('success', '#22c55e'))
        stat_layout.addWidget(self.stat_onaylanan)
        
        self.stat_red = self._create_stat_card("❌ Bugün Red", "0", self.theme.get('danger', '#ef4444'))
        stat_layout.addWidget(self.stat_red)
        
        stat_layout.addStretch()
        layout.addLayout(stat_layout)
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """İstatistik kartı oluştur"""
        card = QFrame()
        card.setFixedSize(150, 70)
        card.setStyleSheet(f"background: {self.theme.get('bg_card', '#1e293b')}; border: 1px solid {color}; border-radius: 8px;")
        
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
    
    def _update_time(self):
        self.saat_label.setText(QTime.currentTime().toString("HH:mm:ss"))
    
    def _load_data(self):
        """İlk ürün onay bekleyen iş emirlerini yükle - Hat başındaki lotlar"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Hat başına transfer edilmiş, henüz proses kontrolü yapılmamış lotlar
            # HB-* depolarında bulunan ve kalite.proses_kontrol'de kaydı olmayan
            cursor.execute("""
                SELECT 
                    ie.id, 
                    ie.is_emri_no, 
                    ie.cari_unvani, 
                    ie.stok_adi, 
                    sb.lot_no,
                    sb.miktar as toplam_miktar,
                    d.ad as hat_adi,
                    ie.stok_kodu,
                    ie.urun_id,
                    sb.giris_tarihi
                FROM stok.stok_bakiye sb
                INNER JOIN tanim.depolar d ON sb.depo_id = d.id
                INNER JOIN siparis.is_emirleri ie ON sb.lot_no = ie.lot_no
                WHERE d.kod LIKE 'HB-%'  -- Hat başı depoları
                  AND sb.miktar > 0
                  AND sb.durum_kodu = 'URETIMDE'
                  AND NOT EXISTS (
                      -- Henüz proses kontrolü yapılmamış
                      SELECT 1 FROM kalite.proses_kontrol pc 
                      WHERE pc.lot_no = sb.lot_no
                  )
                ORDER BY sb.giris_tarihi DESC
            """)
            
            rows = cursor.fetchall()
            
            self.table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                data = {
                    'id': row[0], 'is_emri_no': row[1], 'cari_unvani': row[2],
                    'stok_adi': row[3], 'lot_no': row[4], 'toplam_miktar': row[5],
                    'hat_adi': row[6], 'stok_kodu': row[7], 'stok_id': row[8]
                }
                
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem((row[2] or '')[:25]))
                self.table.setItem(i, 3, QTableWidgetItem((row[3] or '')[:30]))
                self.table.setItem(i, 4, QTableWidgetItem(row[4] or ''))
                
                miktar_item = QTableWidgetItem(str(row[5] or 0))
                miktar_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 5, miktar_item)
                
                self.table.setItem(i, 6, QTableWidgetItem(row[6] or '-'))
                
                # Kontrol butonu
                widget = self.create_action_buttons([
                    ("🔬", "Kontrol Et", lambda checked, d=data: self._kontrol_et(d), "view"),
                ])
                self.table.setCellWidget(i, 7, widget)
                self.table.setRowHeight(i, 42)

            # İstatistikleri güncelle
            self.stat_bekleyen.findChild(QLabel, "stat_value").setText(str(len(rows)))
            
            # Bugün onaylanan
            cursor.execute("""
                SELECT COUNT(*) FROM kalite.proses_kontrol
                WHERE CAST(kontrol_tarihi AS DATE) = CAST(GETDATE() AS DATE)
                  AND durum = 'TAMAMLANDI'
            """)
            onay = cursor.fetchone()[0]
            self.stat_onaylanan.findChild(QLabel, "stat_value").setText(str(onay))
            
            # Bugün red (varsa)
            cursor.execute("""
                SELECT COUNT(*) FROM kalite.proses_kontrol
                WHERE CAST(kontrol_tarihi AS DATE) = CAST(GETDATE() AS DATE)
                  AND durum = 'RED'
            """)
            red = cursor.fetchone()[0]
            self.stat_red.findChild(QLabel, "stat_value").setText(str(red))
            
            conn.close()
            
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
    
    def _kontrol_et(self, data: dict):
        """İlk ürün kontrol dialog'unu aç"""
        dlg = IlkUrunOnayDialog(self.theme, data, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()