# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - WhatsApp Bildirim Yönetimi
Kullanıcıların hangi bildirimleri WhatsApp'tan alacağını yönetir
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QAbstractItemView, QMessageBox, QCheckBox, QTabWidget, QWidget,
    QTextEdit, QLineEdit, QDialog, QFormLayout, QListWidget, 
    QListWidgetItem, QDialogButtonBox, QSpinBox, QRadioButton, 
    QButtonGroup, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor
from datetime import datetime

from components.base_page import BasePage
from core.database import get_db_connection


def get_modern_style(theme: dict) -> dict:
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


class SistemWhatsappPage(BasePage):
    """WhatsApp Bildirim Yönetimi"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; padding: 16px;")
        header_layout = QHBoxLayout(header_frame)
        
        title = QLabel("📱 WhatsApp Bildirim Yönetimi")
        title.setStyleSheet(f"color: {s['text']}; font-size: 20px; font-weight: 600;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        kaydet_btn = QPushButton("💾 Değişiklikleri Kaydet")
        kaydet_btn.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }} QPushButton:hover {{ background: #059669; }}")
        kaydet_btn.clicked.connect(self._kaydet)
        header_layout.addWidget(kaydet_btn)
        
        layout.addWidget(header_frame)
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ 
                border: 1px solid {s['border']}; 
                background: {s['card_bg']}; 
                border-radius: 8px;
            }}
            QTabBar::tab {{ 
                background: {s['input_bg']}; 
                color: {s['text_secondary']}; 
                padding: 12px 24px; 
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{ 
                background: {s['card_bg']}; 
                color: {s['text']};
                border-bottom: 3px solid {s['primary']}; 
            }}
        """)
        
        # Tab 1: Kullanıcı Abonelikleri
        self.tab_abonelikler = QWidget()
        self._setup_abonelikler_tab()
        self.tabs.addTab(self.tab_abonelikler, "👥 Kullanıcı Abonelikleri")
        
        # Tab 2: Grup Yönetimi
        self.tab_gruplar = QWidget()
        self._setup_gruplar_tab()
        self.tabs.addTab(self.tab_gruplar, "👨‍👩‍👧‍👦 Grup Yönetimi")
        
        # Tab 3: Bildirim Tanımları
        self.tab_tanimlar = QWidget()
        self._setup_tanimlar_tab()
        self.tabs.addTab(self.tab_tanimlar, "📋 Bildirim Tanımları")
        
        # Tab 4: Servis Ayarları (YENİ)
        self.tab_ayarlar = QWidget()
        self._setup_ayarlar_tab()
        self.tabs.addTab(self.tab_ayarlar, "⚙️ Servis Ayarları")
        
        # Tab 5: Gönderim Geçmişi
        self.tab_gecmis = QWidget()
        self._setup_gecmis_tab()
        self.tabs.addTab(self.tab_gecmis, "📊 Gönderim Geçmişi")
        
        layout.addWidget(self.tabs)
    
    def _setup_abonelikler_tab(self):
        """Kullanıcı abonelikleri tab'ı"""
        s = self.s
        layout = QVBoxLayout(self.tab_abonelikler)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Açıklama
        info_label = QLabel("Kullanıcıların hangi bildirimleri WhatsApp'tan alacağını belirleyin")
        info_label.setStyleSheet(f"color: {s['text_secondary']}; font-size: 12px; padding: 8px;")
        layout.addWidget(info_label)
        
        # Tablo
        self.table_abonelik = QTableWidget()
        self.table_abonelik.setColumnCount(6)
        self.table_abonelik.setHorizontalHeaderLabels([
            "Kullanıcı", "E-posta", "Telefon", "Sistem", "E-posta", "WhatsApp"
        ])
        
        self.table_abonelik.setStyleSheet(f"""
            QTableWidget {{ 
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: 1px solid {s['border']}; 
                border-radius: 8px;
                gridline-color: {s['border']};
            }}
            QHeaderView::section {{ 
                background: rgba(0,0,0,0.3); 
                color: {s['text_secondary']}; 
                padding: 10px; 
                border: none;
                font-weight: 600;
            }}
        """)
        
        self.table_abonelik.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_abonelik.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_abonelik.setColumnWidth(2, 120)
        self.table_abonelik.setColumnWidth(3, 120)
        self.table_abonelik.setColumnWidth(4, 80)
        self.table_abonelik.setColumnWidth(5, 80)
        
        self.table_abonelik.verticalHeader().setVisible(False)
        self.table_abonelik.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_abonelik.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        layout.addWidget(self.table_abonelik)
    
    def _setup_gruplar_tab(self):
        """Grup yönetimi tab'ı"""
        s = self.s
        layout = QVBoxLayout(self.tab_gruplar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        info_label = QLabel("Bildirim grupları oluşturun ve üye ekleyin")
        info_label.setStyleSheet(f"color: {s['text_secondary']}; font-size: 12px;")
        toolbar.addWidget(info_label)
        
        toolbar.addStretch()
        
        yeni_grup_btn = QPushButton("➕ Yeni Grup")
        yeni_grup_btn.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; }} QPushButton:hover {{ background: {s['primary']}; }}")
        yeni_grup_btn.clicked.connect(self._yeni_grup)
        toolbar.addWidget(yeni_grup_btn)
        
        layout.addLayout(toolbar)
        
        # Grup listesi
        self.table_grup = QTableWidget()
        self.table_grup.setColumnCount(4)
        self.table_grup.setHorizontalHeaderLabels([
            "Grup Adı", "Açıklama", "Üye Sayısı", "İşlemler"
        ])
        
        self.table_grup.setStyleSheet(f"""
            QTableWidget {{ 
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: 1px solid {s['border']}; 
                border-radius: 8px;
            }}
            QHeaderView::section {{ 
                background: rgba(0,0,0,0.3); 
                color: {s['text_secondary']}; 
                padding: 10px; 
                border: none;
            }}
        """)
        
        self.table_grup.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_grup.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_grup.setColumnWidth(2, 100)
        self.table_grup.setColumnWidth(3, 120)
        self.table_grup.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table_grup)
    
    def _setup_tanimlar_tab(self):
        """Bildirim tanımları tab'ı"""
        s = self.s
        layout = QVBoxLayout(self.tab_tanimlar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Filtre
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Modül:"))
        self.modul_filter = QComboBox()
        self.modul_filter.addItem("Tümü", None)
        self.modul_filter.addItems(["STOK", "KALITE", "URETIM", "SEVKIYAT", "SISTEM"])
        self.modul_filter.currentIndexChanged.connect(self._load_tanimlar)
        filter_layout.addWidget(self.modul_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Tablo
        self.table_tanim = QTableWidget()
        self.table_tanim.setColumnCount(6)
        self.table_tanim.setHorizontalHeaderLabels([
            "Kod", "Başlık", "Modül", "Önem", "Tip", "Aktif"
        ])
        
        self.table_tanim.setStyleSheet(f"""
            QTableWidget {{ 
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: 1px solid {s['border']}; 
                border-radius: 8px;
            }}
            QHeaderView::section {{ 
                background: rgba(0,0,0,0.3); 
                color: {s['text_secondary']}; 
                padding: 10px; 
                border: none;
            }}
        """)
        
        self.table_tanim.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_tanim.setColumnWidth(0, 200)
        self.table_tanim.setColumnWidth(2, 100)
        self.table_tanim.setColumnWidth(3, 120)
        self.table_tanim.setColumnWidth(4, 80)
        self.table_tanim.setColumnWidth(5, 60)
        self.table_tanim.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table_tanim)
    
    def _setup_ayarlar_tab(self):
        """Servis ayarları tab'ı"""
        s = self.s
        layout = QVBoxLayout(self.tab_ayarlar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Açıklama
        info_label = QLabel("WhatsApp gönderim servisi seçin ve yapılandırın")
        info_label.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px; padding: 8px;")
        layout.addWidget(info_label)
        
        # Servis Seçimi
        servis_frame = QFrame()
        servis_frame.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; padding: 20px;")
        servis_layout = QVBoxLayout(servis_frame)
        
        servis_title = QLabel("📱 WhatsApp Servisi Seçimi")
        servis_title.setStyleSheet(f"color: {s['text']}; font-size: 16px; font-weight: 600; margin-bottom: 12px;")
        servis_layout.addWidget(servis_title)
        
        # Radio buttons için grup
        from PySide6.QtWidgets import QRadioButton, QButtonGroup
        
        self.servis_group = QButtonGroup()
        
        # Twilio Radio
        self.radio_twilio = QRadioButton("Twilio WhatsApp API (Önerilen - Profesyonel)")
        self.radio_twilio.setStyleSheet(f"color: {s['text']}; font-size: 13px; padding: 8px;")
        self.servis_group.addButton(self.radio_twilio, 1)
        servis_layout.addWidget(self.radio_twilio)
        
        twilio_info = QLabel("   ✅ Güvenilir, toplu gönderim\n   ✅ API bazlı, otomasyon friendly\n   ⚠️ Ücretli (~$0.005/mesaj)")
        twilio_info.setStyleSheet(f"color: {s['text_muted']}; font-size: 11px; margin-left: 20px;")
        servis_layout.addWidget(twilio_info)
        
        # pywhatkit Radio
        self.radio_pywhatkit = QRadioButton("pywhatkit (Test için - Ücretsiz)")
        self.radio_pywhatkit.setStyleSheet(f"color: {s['text']}; font-size: 13px; padding: 8px; margin-top: 12px;")
        self.servis_group.addButton(self.radio_pywhatkit, 2)
        servis_layout.addWidget(self.radio_pywhatkit)
        
        pywhatkit_info = QLabel("   ✅ Ücretsiz\n   ⚠️ WhatsApp Web açık olmalı\n   ⚠️ Manuel QR kod girişi gerekir")
        pywhatkit_info.setStyleSheet(f"color: {s['text_muted']}; font-size: 11px; margin-left: 20px;")
        servis_layout.addWidget(pywhatkit_info)
        
        layout.addWidget(servis_frame)
        
        # Twilio Ayarları
        self.twilio_frame = QFrame()
        self.twilio_frame.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; padding: 20px;")
        twilio_layout = QVBoxLayout(self.twilio_frame)
        
        twilio_title = QLabel("🔑 Twilio API Ayarları")
        twilio_title.setStyleSheet(f"color: {s['text']}; font-size: 16px; font-weight: 600; margin-bottom: 12px;")
        twilio_layout.addWidget(twilio_title)
        
        from PySide6.QtWidgets import QGridLayout
        grid = QGridLayout()
        grid.setSpacing(12)
        
        input_style = f"background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 6px; padding: 10px; font-size: 13px;"
        
        # Account SID
        grid.addWidget(QLabel("Account SID:", styleSheet=f"color: {s['text']}; font-size: 13px;"), 0, 0)
        self.txt_twilio_sid = QLineEdit()
        self.txt_twilio_sid.setPlaceholderText("ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.txt_twilio_sid.setStyleSheet(input_style)
        grid.addWidget(self.txt_twilio_sid, 0, 1)
        
        # Auth Token
        grid.addWidget(QLabel("Auth Token:", styleSheet=f"color: {s['text']}; font-size: 13px;"), 1, 0)
        self.txt_twilio_token = QLineEdit()
        self.txt_twilio_token.setPlaceholderText("********************************")
        self.txt_twilio_token.setEchoMode(QLineEdit.Password)
        self.txt_twilio_token.setStyleSheet(input_style)
        grid.addWidget(self.txt_twilio_token, 1, 1)
        
        # WhatsApp Number
        grid.addWidget(QLabel("Twilio WhatsApp No:", styleSheet=f"color: {s['text']}; font-size: 13px;"), 2, 0)
        self.txt_twilio_number = QLineEdit()
        self.txt_twilio_number.setPlaceholderText("+14155238886")
        self.txt_twilio_number.setStyleSheet(input_style)
        grid.addWidget(self.txt_twilio_number, 2, 1)
        
        twilio_layout.addLayout(grid)
        
        # Test butonu
        test_twilio_btn = QPushButton("🧪 Bağlantıyı Test Et")
        test_twilio_btn.setStyleSheet(f"QPushButton {{ background: {s['info']}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }} QPushButton:hover {{ background: #2563EB; }}")
        test_twilio_btn.clicked.connect(self._test_twilio)
        twilio_layout.addWidget(test_twilio_btn)
        
        layout.addWidget(self.twilio_frame)
        
        # pywhatkit Ayarları
        self.pywhatkit_frame = QFrame()
        self.pywhatkit_frame.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; padding: 20px;")
        pywhatkit_layout = QVBoxLayout(self.pywhatkit_frame)
        
        pywhatkit_title = QLabel("⚙️ pywhatkit Ayarları")
        pywhatkit_title.setStyleSheet(f"color: {s['text']}; font-size: 16px; font-weight: 600; margin-bottom: 12px;")
        pywhatkit_layout.addWidget(pywhatkit_title)
        
        grid2 = QGridLayout()
        grid2.setSpacing(12)
        
        # Wait Time
        grid2.addWidget(QLabel("Bekleme Süresi (sn):", styleSheet=f"color: {s['text']}; font-size: 13px;"), 0, 0)
        from PySide6.QtWidgets import QSpinBox
        self.spn_wait_time = QSpinBox()
        self.spn_wait_time.setRange(5, 60)
        self.spn_wait_time.setValue(10)
        self.spn_wait_time.setStyleSheet(input_style)
        grid2.addWidget(self.spn_wait_time, 0, 1)
        
        # Close Time
        grid2.addWidget(QLabel("Kapanma Süresi (sn):", styleSheet=f"color: {s['text']}; font-size: 13px;"), 1, 0)
        self.spn_close_time = QSpinBox()
        self.spn_close_time.setRange(2, 30)
        self.spn_close_time.setValue(5)
        self.spn_close_time.setStyleSheet(input_style)
        grid2.addWidget(self.spn_close_time, 1, 1)
        
        pywhatkit_layout.addLayout(grid2)
        
        info_pwk = QLabel("ℹ️ pywhatkit kullanmadan önce:\n1. WhatsApp Web'de oturum açın\n2. QR kod ile bağlantı kurun\n3. Tarayıcı açık kalmalı")
        info_pwk.setStyleSheet(f"color: {s['warning']}; font-size: 12px; padding: 12px; background: rgba(245, 158, 11, 0.1); border-radius: 6px; margin-top: 8px;")
        pywhatkit_layout.addWidget(info_pwk)
        
        layout.addWidget(self.pywhatkit_frame)
        
        # Genel Ayarlar
        genel_frame = QFrame()
        genel_frame.setStyleSheet(f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; padding: 20px;")
        genel_layout = QVBoxLayout(genel_frame)
        
        genel_title = QLabel("🔧 Genel Ayarlar")
        genel_title.setStyleSheet(f"color: {s['text']}; font-size: 16px; font-weight: 600; margin-bottom: 12px;")
        genel_layout.addWidget(genel_title)
        
        # Test modu
        self.chk_test_modu = QCheckBox("Test Modu (Tüm mesajlar test numarasına gönderilir)")
        self.chk_test_modu.setStyleSheet(f"color: {s['text']}; font-size: 13px; padding: 8px;")
        self.chk_test_modu.setChecked(True)
        genel_layout.addWidget(self.chk_test_modu)
        
        # Test telefon
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Test Telefonu:", styleSheet=f"color: {s['text']}; font-size: 13px;"))
        self.txt_test_telefon = QLineEdit()
        self.txt_test_telefon.setPlaceholderText("+905321234567")
        self.txt_test_telefon.setStyleSheet(input_style)
        test_layout.addWidget(self.txt_test_telefon)
        genel_layout.addLayout(test_layout)
        
        layout.addWidget(genel_frame)
        
        # Test Mesajı butonu
        test_mesaj_btn = QPushButton("🧪 Test Mesajı Gönder")
        test_mesaj_btn.setStyleSheet(f"QPushButton {{ background: {s['info']}; color: white; border: none; border-radius: 6px; padding: 12px 24px; font-size: 14px; font-weight: 600; }} QPushButton:hover {{ background: #2563EB; }}")
        test_mesaj_btn.clicked.connect(self._test_mesaj_gonder)
        layout.addWidget(test_mesaj_btn)
        
        # Kaydet butonu
        kaydet_ayar_btn = QPushButton("💾 Ayarları Kaydet")
        kaydet_ayar_btn.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 6px; padding: 12px 24px; font-size: 14px; font-weight: 600; }} QPushButton:hover {{ background: #059669; }}")
        kaydet_ayar_btn.clicked.connect(self._kaydet_ayarlar)
        layout.addWidget(kaydet_ayar_btn)
        
        layout.addStretch()
        
        # Radio değişimi dinle
        self.radio_twilio.toggled.connect(self._servis_degisti)
        self.radio_pywhatkit.toggled.connect(self._servis_degisti)
        
        # Başlangıçta ayarları yükle
        QTimer.singleShot(100, self._load_ayarlar)
    
    def _servis_degisti(self):
        """Servis seçimi değiştiğinde frame'leri göster/gizle"""
        self.twilio_frame.setVisible(self.radio_twilio.isChecked())
        self.pywhatkit_frame.setVisible(self.radio_pywhatkit.isChecked())
    
    def _load_ayarlar(self):
        """Mevcut ayarları yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sistem.whatsapp_ayarlari WHERE id = 1")
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # Servis tipi
                if row[1] == 'TWILIO':
                    self.radio_twilio.setChecked(True)
                else:
                    self.radio_pywhatkit.setChecked(True)
                
                # Twilio ayarları
                self.txt_twilio_sid.setText(row[3] or '')
                self.txt_twilio_token.setText(row[4] or '')
                self.txt_twilio_number.setText(row[5] or '')
                
                # pywhatkit ayarları
                self.spn_wait_time.setValue(row[6] or 10)
                self.spn_close_time.setValue(row[7] or 5)
                
                # Genel
                self.chk_test_modu.setChecked(bool(row[8]))
                self.txt_test_telefon.setText(row[9] or '')
            else:
                # Varsayılan
                self.radio_twilio.setChecked(True)
                self.chk_test_modu.setChecked(True)
            
            self._servis_degisti()
            
        except Exception as e:
            print(f"Ayarlar yükleme hatası: {e}")
            self.radio_twilio.setChecked(True)
            self._servis_degisti()
    
    def _kaydet_ayarlar(self):
        """Ayarları kaydet"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            servis_tipi = 'TWILIO' if self.radio_twilio.isChecked() else 'PYWHATKIT'
            
            # Var mı kontrol et
            cursor.execute("SELECT id FROM sistem.whatsapp_ayarlari WHERE id = 1")
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute("""
                    UPDATE sistem.whatsapp_ayarlari SET
                        servis_tipi = ?,
                        aktif_mi = 1,
                        twilio_account_sid = ?,
                        twilio_auth_token = ?,
                        twilio_whatsapp_number = ?,
                        pywhatkit_wait_time = ?,
                        pywhatkit_close_time = ?,
                        test_modu = ?,
                        test_telefon = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = 1
                """, (
                    servis_tipi,
                    self.txt_twilio_sid.text().strip() or None,
                    self.txt_twilio_token.text().strip() or None,
                    self.txt_twilio_number.text().strip() or None,
                    self.spn_wait_time.value(),
                    self.spn_close_time.value(),
                    self.chk_test_modu.isChecked(),
                    self.txt_test_telefon.text().strip() or None
                ))
            else:
                cursor.execute("""
                    INSERT INTO sistem.whatsapp_ayarlari 
                    (servis_tipi, aktif_mi, twilio_account_sid, twilio_auth_token, 
                     twilio_whatsapp_number, pywhatkit_wait_time, pywhatkit_close_time,
                     test_modu, test_telefon)
                    VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    servis_tipi,
                    self.txt_twilio_sid.text().strip() or None,
                    self.txt_twilio_token.text().strip() or None,
                    self.txt_twilio_number.text().strip() or None,
                    self.spn_wait_time.value(),
                    self.spn_close_time.value(),
                    self.chk_test_modu.isChecked(),
                    self.txt_test_telefon.text().strip() or None
                ))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Başarılı", f"WhatsApp ayarları kaydedildi!\n\nAktif Servis: {servis_tipi}")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ayar kaydetme hatası:\n{str(e)}")
    
    def _test_mesaj_gonder(self):
        """Test mesajı gönder"""
        # Önce ayarları kaydet
        self._kaydet_ayarlar()
        
        test_telefon = self.txt_test_telefon.text().strip()
        
        if not test_telefon:
            QMessageBox.warning(self, "Uyarı", "Test telefon numarası boş!")
            return
        
        # Onay al
        reply = QMessageBox.question(self, "Test Mesajı", 
            f"Test mesajı gönderilecek:\n\n📱 {test_telefon}\n\nDevam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # WhatsApp servisini import et
            from utils.whatsapp_service import gonder_whatsapp
            
            # Test mesajı
            mesaj = """🧪 NEXOR ERP - Test Mesajı

✅ WhatsApp bildirim sistemi çalışıyor!

Tarih: {tarih}
Servis: {servis}

Bu bir test mesajıdır.""".format(
                tarih=datetime.now().strftime('%d.%m.%Y %H:%M'),
                servis='Twilio' if self.radio_twilio.isChecked() else 'pywhatkit'
            )
            
            # Gönder
            success, msg = gonder_whatsapp(test_telefon, mesaj)
            
            if success:
                QMessageBox.information(self, "Başarılı", 
                    f"✅ Test mesajı gönderildi!\n\n📱 {test_telefon}\n\nSonuç: {msg}")
            else:
                QMessageBox.warning(self, "Hata", 
                    f"❌ Test mesajı gönderilemedi!\n\n{msg}")
            
        except ImportError as e:
            QMessageBox.critical(self, "Eksik Kütüphane", 
                f"WhatsApp servisi bulunamadı!\n\n{str(e)}\n\nwhatsapp_service.py dosyası utils/ klasöründe olmalı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Test mesajı hatası:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _test_twilio(self):
        """Twilio bağlantısını test et"""
        try:
            from twilio.rest import Client
            
            sid = self.txt_twilio_sid.text().strip()
            token = self.txt_twilio_token.text().strip()
            
            if not sid or not token:
                QMessageBox.warning(self, "Uyarı", "Account SID ve Auth Token gerekli!")
                return
            
            # Test bağlantısı
            client = Client(sid, token)
            account = client.api.accounts(sid).fetch()
            
            QMessageBox.information(self, "Başarılı", 
                f"✅ Twilio bağlantısı başarılı!\n\nHesap: {account.friendly_name}\nDurum: {account.status}")
            
        except ImportError:
            QMessageBox.warning(self, "Eksik Kütüphane", 
                "Twilio kütüphanesi yüklü değil!\n\nTerminalde çalıştırın:\npip install twilio --break-system-packages")
        except Exception as e:
            QMessageBox.critical(self, "Bağlantı Hatası", f"Twilio bağlantı hatası:\n{str(e)}")
    
    def _setup_gecmis_tab(self):
        """Gönderim geçmişi tab'ı"""
        s = self.s
        layout = QVBoxLayout(self.tab_gecmis)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # İstatistikler
        stats_layout = QHBoxLayout()
        
        self.stat_bekleyen = self._create_stat_card("⏳ Bekleyen", "0", s['warning'])
        self.stat_gonderildi = self._create_stat_card("✅ Gönderildi", "0", s['success'])
        self.stat_hata = self._create_stat_card("❌ Hata", "0", s['error'])
        
        stats_layout.addWidget(self.stat_bekleyen)
        stats_layout.addWidget(self.stat_gonderildi)
        stats_layout.addWidget(self.stat_hata)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        # Tablo
        self.table_gecmis = QTableWidget()
        self.table_gecmis.setColumnCount(6)
        self.table_gecmis.setHorizontalHeaderLabels([
            "Tarih", "Alıcı", "Telefon", "Modül", "Mesaj", "Durum"
        ])
        
        self.table_gecmis.setStyleSheet(f"""
            QTableWidget {{ 
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: 1px solid {s['border']}; 
                border-radius: 8px;
            }}
            QHeaderView::section {{ 
                background: rgba(0,0,0,0.3); 
                color: {s['text_secondary']}; 
                padding: 10px; 
                border: none;
            }}
        """)
        
        self.table_gecmis.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_gecmis.setColumnWidth(0, 140)
        self.table_gecmis.setColumnWidth(1, 150)
        self.table_gecmis.setColumnWidth(2, 120)
        self.table_gecmis.setColumnWidth(3, 120)
        self.table_gecmis.setColumnWidth(5, 100)
        self.table_gecmis.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table_gecmis)
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """İstatistik kartı oluştur"""
        s = self.s
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                border-left: 4px solid {color};
                padding: 12px;
            }}
        """)
        card.setMinimumWidth(150)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {s['text_muted']}; font-size: 11px;")
        layout.addWidget(title_lbl)
        
        value_lbl = QLabel(value)
        value_lbl.setObjectName("value_label")
        value_lbl.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_lbl)
        
        return card
    
    def _load_data(self):
        """Tüm verileri yükle"""
        self._load_abonelikler()
        self._load_gruplar()
        self._load_tanimlar()
        self._load_gecmis()
    
    def _load_abonelikler(self):
        """Kullanıcı aboneliklerini yükle"""
        s = self.s
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    k.id,
                    k.kullanici_adi,
                    k.email,
                    k.telefon,
                    ISNULL(a.sistem_bildirim, 0) AS sistem,
                    ISNULL(a.email_bildirim, 0) AS email,
                    ISNULL(a.whatsapp_bildirim, 0) AS whatsapp
                FROM sistem.kullanicilar k
                LEFT JOIN sistem.bildirim_abonelikleri a ON k.id = a.kullanici_id
                WHERE k.aktif_mi = 1
                ORDER BY k.kullanici_adi
            """)
            rows = cursor.fetchall()
            conn.close()
            
            self.table_abonelik.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # Kullanıcı adı
                self.table_abonelik.setItem(i, 0, QTableWidgetItem(row[1] or ''))
                
                # E-posta
                self.table_abonelik.setItem(i, 1, QTableWidgetItem(row[2] or ''))
                
                # Telefon
                self.table_abonelik.setItem(i, 2, QTableWidgetItem(row[3] or ''))
                
                # Checkboxlar
                for col, val in [(3, row[4]), (4, row[5]), (5, row[6])]:
                    chk = QCheckBox()
                    chk.setChecked(bool(val))
                    chk.setStyleSheet(f"QCheckBox {{ padding-left: 30px; }}")
                    chk.setProperty("kullanici_id", row[0])
                    chk.setProperty("tip", ['sistem', 'email', 'whatsapp'][col-3])
                    self.table_abonelik.setCellWidget(i, col, chk)
                    self.table_abonelik.setRowHeight(i, 42)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Abonelikler yüklenirken hata:\n{str(e)}")
    
    def _load_gruplar(self):
        """Grupları yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    g.id,
                    g.grup_adi,
                    g.aciklama,
                    COUNT(gu.id) AS uye_sayisi
                FROM sistem.bildirim_gruplari g
                LEFT JOIN sistem.bildirim_grup_uyeleri gu ON g.id = gu.grup_id AND gu.aktif_mi = 1
                WHERE g.aktif_mi = 1
                GROUP BY g.id, g.grup_adi, g.aciklama
                ORDER BY g.grup_adi
            """)
            rows = cursor.fetchall()
            conn.close()
            
            self.table_grup.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table_grup.setItem(i, 0, QTableWidgetItem(row[1] or ''))
                self.table_grup.setItem(i, 1, QTableWidgetItem(row[2] or ''))
                self.table_grup.setItem(i, 2, QTableWidgetItem(str(row[3])))
                
                # İşlem butonları
                widget = self.create_action_buttons([
                    ("✏️", "Duzenle", lambda checked, gid=row[0]: self._duzenle_grup(gid), "edit"),
                    ("🗑️", "Sil", lambda checked, gid=row[0]: self._sil_grup(gid), "delete"),
                ])
                self.table_grup.setCellWidget(i, 3, widget)
                self.table_grup.setRowHeight(i, 42)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Gruplar yüklenirken hata:\n{str(e)}")
    
    def _load_tanimlar(self):
        """Bildirim tanımlarını yükle"""
        s = self.s
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            modul = self.modul_filter.currentText()
            if modul == "Tümü":
                cursor.execute("""
                    SELECT kod, baslik, modul, onem_derecesi, bildirim_tipi, aktif_mi
                    FROM sistem.bildirim_tanimlari
                    ORDER BY modul, kod
                """)
            else:
                cursor.execute("""
                    SELECT kod, baslik, modul, onem_derecesi, bildirim_tipi, aktif_mi
                    FROM sistem.bildirim_tanimlari
                    WHERE modul = ?
                    ORDER BY kod
                """, (modul,))
            
            rows = cursor.fetchall()
            conn.close()
            
            self.table_tanim.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table_tanim.setItem(i, 0, QTableWidgetItem(row[0] or ''))
                self.table_tanim.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table_tanim.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                
                # Önem derecesi - renkli
                onem_item = QTableWidgetItem(row[3] or '')
                if row[3] == 'KRITIK':
                    onem_item.setForeground(QColor(s['error']))
                elif row[3] == 'YUKSEK':
                    onem_item.setForeground(QColor(s['warning']))
                self.table_tanim.setItem(i, 3, onem_item)
                
                self.table_tanim.setItem(i, 4, QTableWidgetItem(row[4] or ''))
                
                # Aktif checkbox
                chk = QCheckBox()
                chk.setChecked(bool(row[5]))
                self.table_tanim.setCellWidget(i, 5, chk)
                self.table_tanim.setRowHeight(i, 42)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Tanımlar yüklenirken hata:\n{str(e)}")
    
    def _load_gecmis(self):
        """Gönderim geçmişini yükle"""
        s = self.s
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # İstatistikler
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN whatsapp_gonderildi_mi = 0 THEN 1 ELSE 0 END) AS bekleyen,
                    SUM(CASE WHEN whatsapp_gonderildi_mi = 1 THEN 1 ELSE 0 END) AS gonderildi,
                    SUM(CASE WHEN whatsapp_hata_mesaji IS NOT NULL THEN 1 ELSE 0 END) AS hata
                FROM sistem.bildirimler
                WHERE whatsapp_telefon IS NOT NULL
            """)
            stats = cursor.fetchone()
            if stats:
                self.stat_bekleyen.findChild(QLabel, "value_label").setText(str(stats[0] or 0))
                self.stat_gonderildi.findChild(QLabel, "value_label").setText(str(stats[1] or 0))
                self.stat_hata.findChild(QLabel, "value_label").setText(str(stats[2] or 0))
            
            # Son 100 kayıt
            cursor.execute("""
                SELECT TOP 100
                    b.olusturma_tarihi,
                    k.kullanici_adi,
                    b.whatsapp_telefon,
                    b.modul,
                    LEFT(b.mesaj, 100) AS mesaj_kismi,
                    CASE 
                        WHEN b.whatsapp_hata_mesaji IS NOT NULL THEN 'HATA'
                        WHEN b.whatsapp_gonderildi_mi = 1 THEN 'GÖNDERİLDİ'
                        ELSE 'BEKLIYOR'
                    END AS durum
                FROM sistem.bildirimler b
                LEFT JOIN sistem.kullanicilar k ON b.hedef_kullanici_id = k.id
                WHERE b.whatsapp_telefon IS NOT NULL
                ORDER BY b.olusturma_tarihi DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            
            self.table_gecmis.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # Tarih
                tarih_str = row[0].strftime('%d.%m.%Y %H:%M') if row[0] else ''
                self.table_gecmis.setItem(i, 0, QTableWidgetItem(tarih_str))
                
                self.table_gecmis.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table_gecmis.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.table_gecmis.setItem(i, 3, QTableWidgetItem(row[3] or ''))
                self.table_gecmis.setItem(i, 4, QTableWidgetItem(row[4] or ''))
                
                # Durum - renkli
                durum_item = QTableWidgetItem(row[5] or '')
                if row[5] == 'GÖNDERİLDİ':
                    durum_item.setForeground(QColor(s['success']))
                elif row[5] == 'HATA':
                    durum_item.setForeground(QColor(s['error']))
                else:
                    durum_item.setForeground(QColor(s['warning']))
                self.table_gecmis.setItem(i, 5, durum_item)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Geçmiş yüklenirken hata:\n{str(e)}")
    
    def _kaydet(self):
        """Abonelik değişikliklerini kaydet"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # İlk bildirim tanımını al (varsayılan)
            cursor.execute("SELECT TOP 1 id FROM sistem.bildirim_tanimlari WHERE aktif_mi = 1")
            default_tanim = cursor.fetchone()
            default_tanim_id = default_tanim[0] if default_tanim else 1
            
            # Tüm checkbox'ları tara
            for row in range(self.table_abonelik.rowCount()):
                kullanici_id = None
                sistem_checked = False
                email_checked = False
                whatsapp_checked = False
                
                # Kullanıcı ID'sini al
                for col in [3, 4, 5]:
                    widget = self.table_abonelik.cellWidget(row, col)
                    if isinstance(widget, QCheckBox):
                        kullanici_id = widget.property("kullanici_id")
                        tip = widget.property("tip")
                        
                        if tip == 'sistem':
                            sistem_checked = widget.isChecked()
                        elif tip == 'email':
                            email_checked = widget.isChecked()
                        elif tip == 'whatsapp':
                            whatsapp_checked = widget.isChecked()
                
                if not kullanici_id:
                    continue
                
                # Kayıt var mı kontrol et
                cursor.execute("""
                    SELECT id FROM sistem.bildirim_abonelikleri
                    WHERE kullanici_id = ?
                """, (kullanici_id,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Güncelle
                    cursor.execute("""
                        UPDATE sistem.bildirim_abonelikleri SET
                            sistem_bildirim = ?,
                            email_bildirim = ?,
                            whatsapp_bildirim = ?
                        WHERE kullanici_id = ?
                    """, (sistem_checked, email_checked, whatsapp_checked, kullanici_id))
                else:
                    # Yeni kayıt
                    cursor.execute("""
                        INSERT INTO sistem.bildirim_abonelikleri 
                        (kullanici_id, bildirim_tanim_id, sistem_bildirim, email_bildirim, whatsapp_bildirim, aktif_mi)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """, (kullanici_id, default_tanim_id, sistem_checked, email_checked, whatsapp_checked))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Başarılı", "Değişiklikler kaydedildi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _yeni_grup(self):
        """Yeni grup oluştur"""
        from PySide6.QtWidgets import QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Grup Oluştur")
        dialog.setMinimumSize(500, 400)
        
        s = self.s
        dialog.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; }}")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # Grup bilgileri
        from PySide6.QtWidgets import QFormLayout
        form = QFormLayout()
        
        input_style = f"background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 6px; padding: 8px;"
        
        txt_grup_adi = QLineEdit()
        txt_grup_adi.setPlaceholderText("Örn: Laboratuvar Ekibi")
        txt_grup_adi.setStyleSheet(input_style)
        form.addRow(QLabel("Grup Adı:", styleSheet=f"color: {s['text']};"), txt_grup_adi)
        
        txt_aciklama = QTextEdit()
        txt_aciklama.setPlaceholderText("Grup açıklaması...")
        txt_aciklama.setMaximumHeight(80)
        txt_aciklama.setStyleSheet(input_style)
        form.addRow(QLabel("Açıklama:", styleSheet=f"color: {s['text']};"), txt_aciklama)
        
        layout.addLayout(form)
        
        # Üye seçimi
        layout.addWidget(QLabel("Grup Üyeleri:", styleSheet=f"color: {s['text']}; font-weight: 600;"))
        
        from PySide6.QtWidgets import QListWidget
        list_kullanicilar = QListWidget()
        list_kullanicilar.setStyleSheet(f"""
            QListWidget {{ 
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: 1px solid {s['border']}; 
                border-radius: 6px;
            }}
        """)
        
        # Kullanıcıları yükle
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kullanici_adi, ad, soyad, telefon
                FROM sistem.kullanicilar
                WHERE aktif_mi = 1
                ORDER BY kullanici_adi
            """)
            for row in cursor.fetchall():
                item = QListWidgetItem(f"{row[1]} ({row[2]} {row[3]}) - {row[4] or 'Tel yok'}")
                item.setData(Qt.UserRole, row[0])  # kullanici_id
                item.setCheckState(Qt.Unchecked)
                list_kullanicilar.addItem(item)
            conn.close()
        except Exception as e:
            QMessageBox.warning(dialog, "Hata", f"Kullanıcılar yüklenemedi:\n{str(e)}")
        
        layout.addWidget(list_kullanicilar)
        
        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Dialog göster
        if dialog.exec() == QDialog.Accepted:
            grup_adi = txt_grup_adi.text().strip()
            aciklama = txt_aciklama.toPlainText().strip()
            
            if not grup_adi:
                QMessageBox.warning(self, "Uyarı", "Grup adı boş olamaz!")
                return
            
            # Seçili üyeleri topla
            secili_uyeler = []
            for i in range(list_kullanicilar.count()):
                item = list_kullanicilar.item(i)
                if item.checkState() == Qt.Checked:
                    secili_uyeler.append(item.data(Qt.UserRole))
            
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Grup ekle
                cursor.execute("""
                    INSERT INTO sistem.bildirim_gruplari (grup_adi, aciklama, aktif_mi)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, 1)
                """, (grup_adi, aciklama))
                
                grup_id = cursor.fetchone()[0]
                
                # Üyeleri ekle
                for kullanici_id in secili_uyeler:
                    cursor.execute("""
                        INSERT INTO sistem.bildirim_grup_uyeleri (grup_id, kullanici_id, aktif_mi)
                        VALUES (?, ?, 1)
                    """, (grup_id, kullanici_id))
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Başarılı", 
                    f"✅ Grup oluşturuldu!\n\nGrup: {grup_adi}\nÜye Sayısı: {len(secili_uyeler)}")
                
                self._load_gruplar()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Grup oluşturma hatası:\n{str(e)}")
                import traceback
                traceback.print_exc()
    
    def _duzenle_grup(self, grup_id):
        """Grubu düzenle"""
        from PySide6.QtWidgets import QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Grup Düzenle")
        dialog.setMinimumSize(500, 400)
        
        s = self.s
        dialog.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; }}")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # Mevcut grup bilgilerini yükle
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT grup_adi, aciklama
                FROM sistem.bildirim_gruplari
                WHERE id = ?
            """, (grup_id,))
            grup_bilgi = cursor.fetchone()
            
            if not grup_bilgi:
                QMessageBox.warning(self, "Hata", "Grup bulunamadı!")
                return
            
            # Mevcut üyeleri al
            cursor.execute("""
                SELECT kullanici_id
                FROM sistem.bildirim_grup_uyeleri
                WHERE grup_id = ? AND aktif_mi = 1
            """, (grup_id,))
            mevcut_uyeler = [row[0] for row in cursor.fetchall()]
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Grup bilgileri yüklenemedi:\n{str(e)}")
            return
        
        # Form
        from PySide6.QtWidgets import QFormLayout
        form = QFormLayout()
        
        input_style = f"background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 6px; padding: 8px;"
        
        txt_grup_adi = QLineEdit()
        txt_grup_adi.setText(grup_bilgi[0])
        txt_grup_adi.setStyleSheet(input_style)
        form.addRow(QLabel("Grup Adı:", styleSheet=f"color: {s['text']};"), txt_grup_adi)
        
        txt_aciklama = QTextEdit()
        txt_aciklama.setPlainText(grup_bilgi[1] or '')
        txt_aciklama.setMaximumHeight(80)
        txt_aciklama.setStyleSheet(input_style)
        form.addRow(QLabel("Açıklama:", styleSheet=f"color: {s['text']};"), txt_aciklama)
        
        layout.addLayout(form)
        
        # Üye seçimi
        layout.addWidget(QLabel("Grup Üyeleri:", styleSheet=f"color: {s['text']}; font-weight: 600;"))
        
        from PySide6.QtWidgets import QListWidget
        list_kullanicilar = QListWidget()
        list_kullanicilar.setStyleSheet(f"""
            QListWidget {{ 
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: 1px solid {s['border']}; 
                border-radius: 6px;
            }}
        """)
        
        # Kullanıcıları yükle
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kullanici_adi, ad, soyad, telefon
                FROM sistem.kullanicilar
                WHERE aktif_mi = 1
                ORDER BY kullanici_adi
            """)
            for row in cursor.fetchall():
                item = QListWidgetItem(f"{row[1]} ({row[2]} {row[3]}) - {row[4] or 'Tel yok'}")
                item.setData(Qt.UserRole, row[0])
                
                # Mevcut üyeyse işaretle
                if row[0] in mevcut_uyeler:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                
                list_kullanicilar.addItem(item)
            conn.close()
        except Exception as e:
            QMessageBox.warning(dialog, "Hata", f"Kullanıcılar yüklenemedi:\n{str(e)}")
        
        layout.addWidget(list_kullanicilar)
        
        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Dialog göster
        if dialog.exec() == QDialog.Accepted:
            grup_adi = txt_grup_adi.text().strip()
            aciklama = txt_aciklama.toPlainText().strip()
            
            if not grup_adi:
                QMessageBox.warning(self, "Uyarı", "Grup adı boş olamaz!")
                return
            
            # Seçili üyeleri topla
            secili_uyeler = []
            for i in range(list_kullanicilar.count()):
                item = list_kullanicilar.item(i)
                if item.checkState() == Qt.Checked:
                    secili_uyeler.append(item.data(Qt.UserRole))
            
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Grup güncelle
                cursor.execute("""
                    UPDATE sistem.bildirim_gruplari SET
                        grup_adi = ?,
                        aciklama = ?
                    WHERE id = ?
                """, (grup_adi, aciklama, grup_id))
                
                # Eski üyeleri pasif yap
                cursor.execute("""
                    UPDATE sistem.bildirim_grup_uyeleri
                    SET aktif_mi = 0
                    WHERE grup_id = ?
                """, (grup_id,))
                
                # Yeni üyeleri ekle/aktifleştir
                for kullanici_id in secili_uyeler:
                    # Var mı kontrol et
                    cursor.execute("""
                        SELECT id FROM sistem.bildirim_grup_uyeleri
                        WHERE grup_id = ? AND kullanici_id = ?
                    """, (grup_id, kullanici_id))
                    
                    if cursor.fetchone():
                        # Aktifleştir
                        cursor.execute("""
                            UPDATE sistem.bildirim_grup_uyeleri
                            SET aktif_mi = 1
                            WHERE grup_id = ? AND kullanici_id = ?
                        """, (grup_id, kullanici_id))
                    else:
                        # Yeni ekle
                        cursor.execute("""
                            INSERT INTO sistem.bildirim_grup_uyeleri (grup_id, kullanici_id, aktif_mi)
                            VALUES (?, ?, 1)
                        """, (grup_id, kullanici_id))
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Başarılı", 
                    f"✅ Grup güncellendi!\n\nGrup: {grup_adi}\nÜye Sayısı: {len(secili_uyeler)}")
                
                self._load_gruplar()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Grup güncelleme hatası:\n{str(e)}")
                import traceback
                traceback.print_exc()
    
    def _sil_grup(self, grup_id):
        """Grubu sil"""
        reply = QMessageBox.question(self, "Emin misiniz?", 
            "Bu grubu silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE sistem.bildirim_gruplari SET aktif_mi = 0 WHERE id = ?", (grup_id,))
                conn.commit()
                conn.close()
                self._load_gruplar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası:\n{str(e)}")
