# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Ilk Kurulum Wizard
Veritabani baglanti ayarlarini yapilandirir
"""

import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QSpinBox, QMessageBox, QFrame, QWidget, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont

# Import config manager
try:
    from core.external_config import config_manager, CONFIG_FILE
except ImportError:
    from external_config import config_manager, CONFIG_FILE


class ConnectionTestThread(QThread):
    """Baglanti testi icin ayri thread"""
    finished = Signal(bool, str)
    
    def __init__(self, for_plc=False):
        super().__init__()
        self.for_plc = for_plc
    
    def run(self):
        success, message = config_manager.test_connection(self.for_plc)
        self.finished.emit(success, message)


class SetupWizard(QDialog):
    """Ilk Kurulum Wizard - Basit Versiyon"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NEXOR ERP - Veritabani Ayarlari")
        self.setFixedSize(500, 550)
        self.setModal(True)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QLabel#title {
                font-size: 24px;
                font-weight: bold;
                color: #e94560;
            }
            QLabel#subtitle {
                font-size: 12px;
                color: #888888;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #16213e;
                border: 2px solid #0f3460;
                border-radius: 6px;
                padding: 10px;
                color: #ffffff;
                font-size: 13px;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 2px solid #e94560;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #0f3460;
                background-color: #16213e;
            }
            QCheckBox::indicator:checked {
                background-color: #e94560;
                border-color: #e94560;
            }
            QPushButton {
                background-color: #0f3460;
                border: none;
                border-radius: 6px;
                padding: 12px 30px;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #1a4a7a;
            }
            QPushButton#primaryBtn {
                background-color: #e94560;
            }
            QPushButton#primaryBtn:hover {
                background-color: #ff6b6b;
            }
            QPushButton#primaryBtn:disabled {
                background-color: #555555;
            }
            QFrame#separator {
                background-color: #0f3460;
                max-height: 2px;
            }
        """)
        
        self._setup_ui()
        self._load_existing_config()
    
    def _setup_ui(self):
        """UI olustur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Baslik
        title = QLabel("NEXOR ERP")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Veritabani Baglanti Ayarlari")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Ayirici
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)
        
        layout.addSpacing(10)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # Server
        self.txt_server = QLineEdit()
        self.txt_server.setPlaceholderText("ornek: localhost\\SQLEXPRESS")
        form_layout.addRow("Sunucu:", self.txt_server)
        
        # Database
        self.txt_database = QLineEdit()
        self.txt_database.setPlaceholderText("ornek: NexorERP")
        form_layout.addRow("Veritabani:", self.txt_database)
        
        # Driver
        self.cmb_driver = QComboBox()
        self.cmb_driver.addItems([
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server"
        ])
        form_layout.addRow("ODBC Driver:", self.cmb_driver)
        
        layout.addLayout(form_layout)
        
        # Ayirici
        sep2 = QFrame()
        sep2.setObjectName("separator")
        sep2.setFrameShape(QFrame.HLine)
        layout.addWidget(sep2)
        
        # Windows Auth checkbox
        self.chk_windows_auth = QCheckBox("Windows Kimlik Dogrulamasi Kullan")
        self.chk_windows_auth.toggled.connect(self._toggle_auth_fields)
        layout.addWidget(self.chk_windows_auth)
        
        # SQL Auth fields
        self.auth_widget = QWidget()
        auth_layout = QFormLayout(self.auth_widget)
        auth_layout.setContentsMargins(0, 0, 0, 0)
        auth_layout.setSpacing(12)
        
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("SQL Server kullanici adi")
        auth_layout.addRow("Kullanici:", self.txt_user)
        
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.txt_password.setPlaceholderText("SQL Server sifresi")
        auth_layout.addRow("Sifre:", self.txt_password)
        
        layout.addWidget(self.auth_widget)
        
        # Ayirici
        sep3 = QFrame()
        sep3.setObjectName("separator")
        sep3.setFrameShape(QFrame.HLine)
        layout.addWidget(sep3)
        
        # Gelismis ayarlar
        adv_layout = QHBoxLayout()
        
        timeout_label = QLabel("Timeout:")
        self.spn_timeout = QSpinBox()
        self.spn_timeout.setRange(5, 60)
        self.spn_timeout.setValue(10)
        self.spn_timeout.setSuffix(" sn")
        self.spn_timeout.setFixedWidth(100)
        
        adv_layout.addWidget(timeout_label)
        adv_layout.addWidget(self.spn_timeout)
        adv_layout.addStretch()
        
        layout.addLayout(adv_layout)
        
        layout.addStretch()
        
        # Durum mesaji
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        self.btn_test = QPushButton("Baglanti Test")
        self.btn_test.clicked.connect(self._test_connection)
        btn_layout.addWidget(self.btn_test)
        
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Iptal")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_save = QPushButton("Kaydet ve Baslat")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.clicked.connect(self._save_and_start)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)
    
    def _load_existing_config(self):
        """Mevcut config varsa yukle"""
        try:
            self.txt_server.setText(config_manager.get('database.server', ''))
            self.txt_database.setText(config_manager.get('database.database', ''))
            
            driver = config_manager.get('database.driver', 'ODBC Driver 18 for SQL Server')
            index = self.cmb_driver.findText(driver)
            if index >= 0:
                self.cmb_driver.setCurrentIndex(index)
            
            trusted = config_manager.get('database.trusted_connection', False)
            self.chk_windows_auth.setChecked(trusted)
            
            if not trusted:
                self.txt_user.setText(config_manager.get('database.user', ''))
                # Sifreyi gosterme
            
            self.spn_timeout.setValue(config_manager.get('database.timeout', 10))
            
        except Exception as e:
            print(f"Config yukleme hatasi: {e}")
    
    def _toggle_auth_fields(self, windows_auth: bool):
        """Windows/SQL auth arasinda gecis"""
        self.auth_widget.setVisible(not windows_auth)
    
    def _test_connection(self):
        """Baglanti testini calistir"""
        if not self._validate_and_save_config():
            return
        
        self.lbl_status.setText("Baglanti test ediliyor...")
        self.lbl_status.setStyleSheet("color: #888888;")
        self.btn_test.setEnabled(False)
        self.btn_save.setEnabled(False)
        
        # Thread'de test et
        self.test_thread = ConnectionTestThread()
        self.test_thread.finished.connect(self._on_test_complete)
        self.test_thread.start()
    
    def _on_test_complete(self, success: bool, message: str):
        """Test tamamlandi"""
        self.btn_test.setEnabled(True)
        self.btn_save.setEnabled(True)
        
        if success:
            self.lbl_status.setText("Baglanti basarili!")
            self.lbl_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.lbl_status.setText(f"Baglanti hatasi: {message}")
            self.lbl_status.setStyleSheet("color: #e94560;")
    
    def _validate_and_save_config(self) -> bool:
        """Config'i dogrula ve kaydet"""
        server = self.txt_server.text().strip()
        database = self.txt_database.text().strip()
        
        if not server:
            QMessageBox.warning(self, "Hata", "Sunucu adresi bos olamaz!")
            self.txt_server.setFocus()
            return False
        
        if not database:
            QMessageBox.warning(self, "Hata", "Veritabani adi bos olamaz!")
            self.txt_database.setFocus()
            return False
        
        windows_auth = self.chk_windows_auth.isChecked()
        
        if not windows_auth:
            user = self.txt_user.text().strip()
            if not user:
                QMessageBox.warning(self, "Hata", "Kullanici adi bos olamaz!")
                self.txt_user.setFocus()
                return False
            password = self.txt_password.text()
        else:
            user = ""
            password = ""
        
        # Config'e kaydet
        config_manager.set_db_config(
            server=server,
            database=database,
            user=user,
            password=password,
            trusted_connection=windows_auth,
            driver=self.cmb_driver.currentText(),
            timeout=self.spn_timeout.value()
        )
        
        return True
    
    def _save_and_start(self):
        """Kaydet ve baslat"""
        if not self._validate_and_save_config():
            return
        
        # Once test et
        self.lbl_status.setText("Baglanti test ediliyor...")
        self.lbl_status.setStyleSheet("color: #888888;")
        self.btn_save.setEnabled(False)
        
        success, message = config_manager.test_connection()
        
        if success:
            # Kaydet
            if config_manager.save():
                self.accept()
            else:
                QMessageBox.critical(self, "Hata", "Config kaydedilemedi!")
                self.btn_save.setEnabled(True)
        else:
            self.lbl_status.setText(f"Baglanti hatasi: {message}")
            self.lbl_status.setStyleSheet("color: #e94560;")
            self.btn_save.setEnabled(True)
            
            # Yine de kaydetmek istiyor mu?
            reply = QMessageBox.question(
                self, 
                "Baglanti Hatasi",
                "Veritabani baglantiisi kurulamadi.\n\nYine de ayarlari kaydetmek istiyor musunuz?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if config_manager.save():
                    self.accept()


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    wizard = SetupWizard()
    result = wizard.exec()
    
    if result == QDialog.Accepted:
        print("Kurulum tamamlandi!")
        print(f"Config: {CONFIG_FILE}")
    else:
        print("Kurulum iptal edildi")
    
    sys.exit(0)
