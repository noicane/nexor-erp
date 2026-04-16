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
from core.nexor_brand import brand


def get_modern_style(theme: dict = None) -> dict:
    """Brand-based style dict for backward compat."""
    return {
        'card_bg': brand.BG_CARD,
        'input_bg': brand.BG_INPUT,
        'border': brand.BORDER,
        'text': brand.TEXT,
        'text_secondary': brand.TEXT_MUTED,
        'text_muted': brand.TEXT_DIM,
        'primary': brand.PRIMARY,
        'primary_hover': brand.PRIMARY_HOVER,
        'success': brand.SUCCESS,
        'warning': brand.WARNING,
        'error': brand.ERROR,
        'danger': brand.ERROR,
        'info': brand.INFO,
        'bg_main': brand.BG_MAIN,
        'bg_hover': brand.BG_HOVER,
        'bg_selected': brand.BG_SELECTED,
        'border_light': brand.BORDER_HARD,
        'border_input': brand.BORDER,
        'card_solid': brand.BG_CARD,
        'gradient': brand.PRIMARY,
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
        
        title = QLabel("Bildirim Kanal Yonetimi")
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
        self.tabs.addTab(self.tab_ayarlar, "WhatsApp + SMTP Ayarlari")
        
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

        btn_kaydet_tanim = QPushButton("Kaydet")
        btn_kaydet_tanim.setStyleSheet(f"background: {s['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: bold;")
        btn_kaydet_tanim.clicked.connect(self._save_tanimlar)
        filter_layout.addWidget(btn_kaydet_tanim)

        layout.addLayout(filter_layout)

        # Tablo
        self.table_tanim = QTableWidget()
        self.table_tanim.setColumnCount(9)
        self.table_tanim.setHorizontalHeaderLabels([
            "Kod", "Baslik", "Modul", "Onem", "Tip", "Uygulama", "E-Posta", "WhatsApp", "Aktif"
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
        self.table_tanim.setColumnWidth(0, 180)
        self.table_tanim.setColumnWidth(2, 100)
        self.table_tanim.setColumnWidth(3, 80)
        self.table_tanim.setColumnWidth(4, 70)
        self.table_tanim.setColumnWidth(5, 70)
        self.table_tanim.setColumnWidth(6, 70)
        self.table_tanim.setColumnWidth(7, 70)
        self.table_tanim.setColumnWidth(8, 50)
        self.table_tanim.verticalHeader().setVisible(False)

        layout.addWidget(self.table_tanim)
    
    def _setup_ayarlar_tab(self):
        """Servis ayarlari tab'i - WhatsApp + SMTP"""
        s = self.s
        layout = QVBoxLayout(self.tab_ayarlar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        input_style = f"background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 6px; padding: 10px; font-size: 13px;"
        card_style = f"background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; padding: 20px;"
        title_style = f"color: {s['text']}; font-size: 15px; font-weight: 600; margin-bottom: 8px;"
        label_style = f"color: {s['text']}; font-size: 13px;"

        # ========== WHATSAPP AYARLARI ==========
        wa_frame = QFrame()
        wa_frame.setStyleSheet(card_style)
        wa_layout = QVBoxLayout(wa_frame)

        wa_title = QLabel("WhatsApp Ayarlari")
        wa_title.setStyleSheet(title_style)
        wa_layout.addWidget(wa_title)

        self.servis_group = QButtonGroup()

        self.radio_whapi = QRadioButton("WHAPI Cloud (Onerilen)")
        self.radio_whapi.setStyleSheet(f"color: {s['text']}; font-size: 13px; padding: 4px;")
        self.servis_group.addButton(self.radio_whapi, 0)
        wa_layout.addWidget(self.radio_whapi)

        self.radio_twilio = QRadioButton("Twilio WhatsApp API")
        self.radio_twilio.setStyleSheet(f"color: {s['text']}; font-size: 13px; padding: 4px;")
        self.servis_group.addButton(self.radio_twilio, 1)
        wa_layout.addWidget(self.radio_twilio)

        self.radio_pywhatkit = QRadioButton("pywhatkit (Tarayici bazli)")
        self.radio_pywhatkit.setStyleSheet(f"color: {s['text']}; font-size: 13px; padding: 4px;")
        self.servis_group.addButton(self.radio_pywhatkit, 2)
        wa_layout.addWidget(self.radio_pywhatkit)

        # WHAPI Token
        wa_grid = QGridLayout()
        wa_grid.setSpacing(10)

        wa_grid.addWidget(QLabel("WHAPI Token:", styleSheet=label_style), 0, 0)
        self.txt_whapi_token = QLineEdit()
        self.txt_whapi_token.setPlaceholderText("whapi.cloud API token")
        self.txt_whapi_token.setStyleSheet(input_style)
        wa_grid.addWidget(self.txt_whapi_token, 0, 1)

        # Twilio alanlar
        wa_grid.addWidget(QLabel("Twilio SID:", styleSheet=label_style), 1, 0)
        self.txt_twilio_sid = QLineEdit()
        self.txt_twilio_sid.setPlaceholderText("ACxxxxxxxx")
        self.txt_twilio_sid.setStyleSheet(input_style)
        wa_grid.addWidget(self.txt_twilio_sid, 1, 1)

        wa_grid.addWidget(QLabel("Twilio Token:", styleSheet=label_style), 2, 0)
        self.txt_twilio_token = QLineEdit()
        self.txt_twilio_token.setEchoMode(QLineEdit.Password)
        self.txt_twilio_token.setStyleSheet(input_style)
        wa_grid.addWidget(self.txt_twilio_token, 2, 1)

        wa_grid.addWidget(QLabel("Twilio WA No:", styleSheet=label_style), 3, 0)
        self.txt_twilio_number = QLineEdit()
        self.txt_twilio_number.setPlaceholderText("+14155238886")
        self.txt_twilio_number.setStyleSheet(input_style)
        wa_grid.addWidget(self.txt_twilio_number, 3, 1)

        wa_layout.addLayout(wa_grid)

        # Test modu
        test_wa_layout = QHBoxLayout()
        self.chk_test_modu = QCheckBox("Test Modu")
        self.chk_test_modu.setStyleSheet(f"color: {s['text']}; font-size: 13px;")
        test_wa_layout.addWidget(self.chk_test_modu)
        self.txt_test_telefon = QLineEdit()
        self.txt_test_telefon.setPlaceholderText("Test telefon: +905xxxxxxxxx")
        self.txt_test_telefon.setStyleSheet(input_style)
        self.txt_test_telefon.setMaximumWidth(250)
        test_wa_layout.addWidget(self.txt_test_telefon)
        test_wa_layout.addStretch()
        wa_layout.addLayout(test_wa_layout)

        layout.addWidget(wa_frame)

        # ========== SMTP / E-MAIL AYARLARI ==========
        smtp_frame = QFrame()
        smtp_frame.setStyleSheet(card_style)
        smtp_layout = QVBoxLayout(smtp_frame)

        smtp_title = QLabel("E-Posta (SMTP) Ayarlari")
        smtp_title.setStyleSheet(title_style)
        smtp_layout.addWidget(smtp_title)

        smtp_grid = QGridLayout()
        smtp_grid.setSpacing(10)

        smtp_grid.addWidget(QLabel("SMTP Sunucu:", styleSheet=label_style), 0, 0)
        self.txt_smtp_server = QLineEdit()
        self.txt_smtp_server.setPlaceholderText("mail.domain.com")
        self.txt_smtp_server.setStyleSheet(input_style)
        smtp_grid.addWidget(self.txt_smtp_server, 0, 1)

        smtp_grid.addWidget(QLabel("Port:", styleSheet=label_style), 0, 2)
        self.spn_smtp_port = QSpinBox()
        self.spn_smtp_port.setRange(25, 9999)
        self.spn_smtp_port.setValue(465)
        self.spn_smtp_port.setStyleSheet(input_style)
        self.spn_smtp_port.setMaximumWidth(100)
        smtp_grid.addWidget(self.spn_smtp_port, 0, 3)

        smtp_grid.addWidget(QLabel("Gonderen E-Posta:", styleSheet=label_style), 1, 0)
        self.txt_smtp_email = QLineEdit()
        self.txt_smtp_email.setPlaceholderText("nexor@domain.com")
        self.txt_smtp_email.setStyleSheet(input_style)
        smtp_grid.addWidget(self.txt_smtp_email, 1, 1)

        smtp_grid.addWidget(QLabel("SSL/TLS:", styleSheet=label_style), 1, 2)
        self.chk_smtp_ssl = QCheckBox()
        self.chk_smtp_ssl.setChecked(True)
        smtp_grid.addWidget(self.chk_smtp_ssl, 1, 3)

        smtp_grid.addWidget(QLabel("Sifre:", styleSheet=label_style), 2, 0)
        self.txt_smtp_sifre = QLineEdit()
        self.txt_smtp_sifre.setEchoMode(QLineEdit.Password)
        self.txt_smtp_sifre.setStyleSheet(input_style)
        smtp_grid.addWidget(self.txt_smtp_sifre, 2, 1)

        smtp_grid.addWidget(QLabel("Gonderen Adi:", styleSheet=label_style), 2, 2)
        self.txt_smtp_adi = QLineEdit()
        self.txt_smtp_adi.setText("NEXOR ERP")
        self.txt_smtp_adi.setStyleSheet(input_style)
        smtp_grid.addWidget(self.txt_smtp_adi, 2, 3)

        smtp_layout.addLayout(smtp_grid)
        layout.addWidget(smtp_frame)

        # ========== BUTONLAR ==========
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_test = QPushButton("Test Mesaji Gonder")
        btn_test.setStyleSheet(f"QPushButton {{ background: {s['info']}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }} QPushButton:hover {{ background: #2563EB; }}")
        btn_test.clicked.connect(self._test_mesaj_gonder)
        btn_layout.addWidget(btn_test)

        btn_kaydet = QPushButton("Ayarlari Kaydet")
        btn_kaydet.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }} QPushButton:hover {{ background: #059669; }}")
        btn_kaydet.clicked.connect(self._kaydet_ayarlar)
        btn_layout.addWidget(btn_kaydet)

        layout.addLayout(btn_layout)
        layout.addStretch()

        # Radio degisimi
        self.radio_whapi.toggled.connect(self._servis_degisti)
        self.radio_twilio.toggled.connect(self._servis_degisti)
        self.radio_pywhatkit.toggled.connect(self._servis_degisti)

        QTimer.singleShot(100, self._load_ayarlar)

    def _servis_degisti(self):
        """Servis secimi degistiginde alanlari goster/gizle"""
        is_whapi = self.radio_whapi.isChecked()
        is_twilio = self.radio_twilio.isChecked()
        self.txt_whapi_token.setEnabled(is_whapi)
        self.txt_twilio_sid.setEnabled(is_twilio)
        self.txt_twilio_token.setEnabled(is_twilio)
        self.txt_twilio_number.setEnabled(is_twilio)

    def _load_ayarlar(self):
        """Mevcut ayarlari yukle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # WhatsApp ayarlari
            cursor.execute("""
                SELECT servis_tipi, twilio_account_sid, twilio_auth_token, twilio_whatsapp_number,
                       test_modu, test_telefon, whapi_token
                FROM sistem.whatsapp_ayarlari WHERE aktif_mi = 1
            """)
            row = cursor.fetchone()
            if row:
                if row[0] == 'WHAPI':
                    self.radio_whapi.setChecked(True)
                elif row[0] == 'TWILIO':
                    self.radio_twilio.setChecked(True)
                else:
                    self.radio_pywhatkit.setChecked(True)
                self.txt_twilio_sid.setText(row[1] or '')
                self.txt_twilio_token.setText(row[2] or '')
                self.txt_twilio_number.setText(row[3] or '')
                self.chk_test_modu.setChecked(bool(row[4]))
                self.txt_test_telefon.setText(row[5] or '')
                self.txt_whapi_token.setText(row[6] or '')
            else:
                self.radio_whapi.setChecked(True)

            # SMTP ayarlari
            cursor.execute("""
                SELECT smtp_server, smtp_port, smtp_ssl, gonderen_email, gonderen_sifre, gonderen_adi
                FROM sistem.email_ayarlari WHERE aktif_mi = 1
            """)
            smtp = cursor.fetchone()
            if smtp:
                self.txt_smtp_server.setText(smtp[0] or '')
                self.spn_smtp_port.setValue(smtp[1] or 465)
                self.chk_smtp_ssl.setChecked(bool(smtp[2]))
                self.txt_smtp_email.setText(smtp[3] or '')
                self.txt_smtp_sifre.setText(smtp[4] or '')
                self.txt_smtp_adi.setText(smtp[5] or 'NEXOR ERP')

            conn.close()
            self._servis_degisti()

        except Exception as e:
            print(f"Ayarlar yukleme hatasi: {e}")
            self.radio_whapi.setChecked(True)
            self._servis_degisti()

    def _kaydet_ayarlar(self):
        """WhatsApp + SMTP ayarlarini kaydet"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # WhatsApp servis tipi
            if self.radio_whapi.isChecked():
                servis_tipi = 'WHAPI'
            elif self.radio_twilio.isChecked():
                servis_tipi = 'TWILIO'
            else:
                servis_tipi = 'PYWHATKIT'

            cursor.execute("SELECT id FROM sistem.whatsapp_ayarlari WHERE aktif_mi = 1")
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE sistem.whatsapp_ayarlari SET
                        servis_tipi = ?, whapi_token = ?,
                        twilio_account_sid = ?, twilio_auth_token = ?, twilio_whatsapp_number = ?,
                        test_modu = ?, test_telefon = ?, guncelleme_tarihi = GETDATE()
                    WHERE aktif_mi = 1
                """, (servis_tipi, self.txt_whapi_token.text().strip() or None,
                      self.txt_twilio_sid.text().strip() or None,
                      self.txt_twilio_token.text().strip() or None,
                      self.txt_twilio_number.text().strip() or None,
                      self.chk_test_modu.isChecked(),
                      self.txt_test_telefon.text().strip() or None))
            else:
                cursor.execute("""
                    INSERT INTO sistem.whatsapp_ayarlari
                    (servis_tipi, aktif_mi, whapi_token, twilio_account_sid, twilio_auth_token,
                     twilio_whatsapp_number, test_modu, test_telefon)
                    VALUES (?, 1, ?, ?, ?, ?, ?, ?)
                """, (servis_tipi, self.txt_whapi_token.text().strip() or None,
                      self.txt_twilio_sid.text().strip() or None,
                      self.txt_twilio_token.text().strip() or None,
                      self.txt_twilio_number.text().strip() or None,
                      self.chk_test_modu.isChecked(),
                      self.txt_test_telefon.text().strip() or None))

            # SMTP kaydet
            cursor.execute("SELECT id FROM sistem.email_ayarlari WHERE aktif_mi = 1")
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE sistem.email_ayarlari SET
                        smtp_server = ?, smtp_port = ?, smtp_ssl = ?,
                        gonderen_email = ?, gonderen_sifre = ?, gonderen_adi = ?
                    WHERE aktif_mi = 1
                """, (self.txt_smtp_server.text().strip(),
                      self.spn_smtp_port.value(),
                      self.chk_smtp_ssl.isChecked(),
                      self.txt_smtp_email.text().strip(),
                      self.txt_smtp_sifre.text().strip() or None,
                      self.txt_smtp_adi.text().strip() or 'NEXOR ERP'))
            else:
                cursor.execute("""
                    INSERT INTO sistem.email_ayarlari
                    (smtp_server, smtp_port, smtp_ssl, gonderen_email, gonderen_sifre, gonderen_adi, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (self.txt_smtp_server.text().strip(),
                      self.spn_smtp_port.value(),
                      self.chk_smtp_ssl.isChecked(),
                      self.txt_smtp_email.text().strip(),
                      self.txt_smtp_sifre.text().strip() or None,
                      self.txt_smtp_adi.text().strip() or 'NEXOR ERP'))

            conn.commit()
            conn.close()

            # Singleton cache temizle
            import utils.whatsapp_service as ws_mod
            ws_mod._whatsapp_service = None
            import utils.email_service as es_mod
            es_mod._email_service = None

            QMessageBox.information(self, "Basarili",
                f"Ayarlar kaydedildi!\n\nWhatsApp: {servis_tipi}\nSMTP: {self.txt_smtp_server.text()}")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ayar kaydetme hatası:\n{str(e)}")
    
    def _test_mesaj_gonder(self):
        """WhatsApp + Email test mesaji gonder"""
        self._kaydet_ayarlar()

        sonuclar = []

        # WhatsApp test
        test_telefon = self.txt_test_telefon.text().strip()
        if test_telefon:
            try:
                from utils.whatsapp_service import WhatsAppService
                ws = WhatsAppService()
                ok, msg = ws.gonder(test_telefon, f"[NEXOR] Test mesaji - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
                sonuclar.append(f"WhatsApp: {'OK' if ok else 'HATA'} - {msg}")
            except Exception as e:
                sonuclar.append(f"WhatsApp: HATA - {e}")
        else:
            sonuclar.append("WhatsApp: Test telefon bos")

        # Email test
        test_email = self.txt_smtp_email.text().strip()
        if test_email and self.txt_smtp_server.text().strip():
            try:
                from utils.email_service import EmailService
                es = EmailService()
                ok, msg = es.gonder(test_email,
                    "NEXOR ERP - E-Mail Test",
                    f"<h2>NEXOR ERP</h2><p>E-mail bildirim sistemi calisiyor!</p><p>{datetime.now().strftime('%d.%m.%Y %H:%M')}</p>")
                sonuclar.append(f"E-Mail: {'OK' if ok else 'HATA'} - {msg}")
            except Exception as e:
                sonuclar.append(f"E-Mail: HATA - {e}")
        else:
            sonuclar.append("E-Mail: SMTP ayarlari eksik")

        QMessageBox.information(self, "Test Sonucu", "\n".join(sonuclar))
    
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
                    SELECT kod, baslik, modul, onem_derecesi, bildirim_tipi,
                           ISNULL(uygulama_ici_varsayilan, 1), ISNULL(email_varsayilan, 0),
                           ISNULL(whatsapp_varsayilan, 0), aktif_mi
                    FROM sistem.bildirim_tanimlari
                    ORDER BY modul, kod
                """)
            else:
                cursor.execute("""
                    SELECT kod, baslik, modul, onem_derecesi, bildirim_tipi,
                           ISNULL(uygulama_ici_varsayilan, 1), ISNULL(email_varsayilan, 0),
                           ISNULL(whatsapp_varsayilan, 0), aktif_mi
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

                onem_item = QTableWidgetItem(row[3] or '')
                if row[3] == 'KRITIK':
                    onem_item.setForeground(QColor(s['error']))
                elif row[3] == 'YUKSEK':
                    onem_item.setForeground(QColor(s['warning']))
                self.table_tanim.setItem(i, 3, onem_item)

                self.table_tanim.setItem(i, 4, QTableWidgetItem(row[4] or ''))

                # Kanal checkbox'lari
                for col, val in [(5, row[5]), (6, row[6]), (7, row[7]), (8, row[8])]:
                    chk = QCheckBox()
                    chk.setChecked(bool(val))
                    chk.setStyleSheet("QCheckBox { margin-left: 20px; }")
                    self.table_tanim.setCellWidget(i, col, chk)

                self.table_tanim.setRowHeight(i, 42)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Tanimlar yuklenirken hata:\n{str(e)}")

    def _save_tanimlar(self):
        """Bildirim tanim kanal ayarlarini kaydet"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            degisen = 0

            for i in range(self.table_tanim.rowCount()):
                kod_item = self.table_tanim.item(i, 0)
                if not kod_item:
                    continue
                kod = kod_item.text()

                uygulama = self.table_tanim.cellWidget(i, 5)
                email = self.table_tanim.cellWidget(i, 6)
                whatsapp = self.table_tanim.cellWidget(i, 7)
                aktif = self.table_tanim.cellWidget(i, 8)

                cursor.execute("""
                    UPDATE sistem.bildirim_tanimlari
                    SET uygulama_ici_varsayilan = ?, email_varsayilan = ?,
                        whatsapp_varsayilan = ?, aktif_mi = ?
                    WHERE kod = ?
                """, (
                    1 if uygulama and uygulama.isChecked() else 0,
                    1 if email and email.isChecked() else 0,
                    1 if whatsapp and whatsapp.isChecked() else 0,
                    1 if aktif and aktif.isChecked() else 0,
                    kod
                ))
                degisen += cursor.rowcount

            conn.commit()
            conn.close()
            QMessageBox.information(self, "Basarili", f"{degisen} tanim guncellendi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatasi:\n{str(e)}")
    
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
