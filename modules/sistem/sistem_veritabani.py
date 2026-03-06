# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Veritabanı Bağlantı Yönetimi Sayfası
Sistem > Veritabanı Bağlantıları

Özellikler:
- Bağlantı listesi (CRUD)
- Test bağlantı
- Şifre güvenli gösterim
- Aktif/Pasif toggle
- Pool istatistikleri
- Gerçek zamanlı health check

Tarih: 2026-01-23
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QSpinBox,
    QCheckBox, QComboBox, QLabel, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from components.base_page import BasePage
from core.database_manager import db_manager, PasswordManager
import logging

logger = logging.getLogger(__name__)


class VeriTabaniBaglantiDialog(QDialog):
    """Bağlantı Düzenleme Dialog'u"""
    
    def __init__(self, parent=None, baglanti_data=None, edit_mode=False):
        super().__init__(parent)
        self.baglanti_data = baglanti_data
        self.edit_mode = edit_mode
        self.password_manager = PasswordManager()
        
        self.setWindowTitle("Bağlantı Düzenle" if edit_mode else "Yeni Bağlantı")
        self.setModal(True)
        self.setMinimumSize(500, 600)
        
        self.setup_ui()
        
        if baglanti_data:
            self.load_data(baglanti_data)
    
    def setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        # Bağlantı Adı
        self.txt_baglanti_adi = QLineEdit()
        self.txt_baglanti_adi.setPlaceholderText("Örn: ERP, PLC, ZIRVE")
        if self.edit_mode:
            self.txt_baglanti_adi.setEnabled(False)  # Düzenlemede değiştirilemez
        form_layout.addRow("Bağlantı Adı *:", self.txt_baglanti_adi)
        
        # Açıklama
        self.txt_aciklama = QLineEdit()
        self.txt_aciklama.setPlaceholderText("Bağlantı açıklaması")
        form_layout.addRow("Açıklama:", self.txt_aciklama)
        
        # Bağlantı Tipi
        self.cmb_baglanti_tipi = QComboBox()
        self.cmb_baglanti_tipi.addItems(["SQLSERVER", "POSTGRESQL", "MYSQL", "ORACLE"])
        form_layout.addRow("Bağlantı Tipi:", self.cmb_baglanti_tipi)
        
        # Server
        self.txt_server = QLineEdit()
        self.txt_server.setPlaceholderText("Örn: 192.168.1.66\\SQLEXPRESS")
        form_layout.addRow("Server *:", self.txt_server)
        
        # Database
        self.txt_database = QLineEdit()
        self.txt_database.setPlaceholderText("Veritabanı adı")
        form_layout.addRow("Database *:", self.txt_database)
        
        # Kullanıcı Adı
        self.txt_kullanici = QLineEdit()
        self.txt_kullanici.setPlaceholderText("Veritabanı kullanıcı adı")
        form_layout.addRow("Kullanıcı Adı *:", self.txt_kullanici)
        
        # Şifre
        self.txt_sifre = QLineEdit()
        self.txt_sifre.setEchoMode(QLineEdit.Password)
        self.txt_sifre.setPlaceholderText("Veritabanı şifresi")
        
        # Şifre göster/gizle
        sifre_layout = QHBoxLayout()
        sifre_layout.addWidget(self.txt_sifre)
        
        self.chk_sifre_goster = QCheckBox("Göster")
        self.chk_sifre_goster.stateChanged.connect(self.toggle_sifre)
        sifre_layout.addWidget(self.chk_sifre_goster)
        
        form_layout.addRow("Şifre *:", sifre_layout)
        
        # Driver
        self.cmb_driver = QComboBox()
        self.cmb_driver.addItems([
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "SQL Server",
            "PostgreSQL Unicode",
            "MySQL ODBC 8.0 Driver"
        ])
        form_layout.addRow("Driver:", self.cmb_driver)
        
        # Timeout
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(5, 120)
        self.spin_timeout.setValue(10)
        self.spin_timeout.setSuffix(" saniye")
        form_layout.addRow("Timeout:", self.spin_timeout)
        
        # Max Connections
        self.spin_max_conn = QSpinBox()
        self.spin_max_conn.setRange(1, 100)
        self.spin_max_conn.setValue(20)
        form_layout.addRow("Max Pool Size:", self.spin_max_conn)
        
        # Extra Params
        self.txt_extra = QTextEdit()
        self.txt_extra.setMaximumHeight(60)
        self.txt_extra.setPlaceholderText("Ek bağlantı parametreleri (opsiyonel)")
        self.txt_extra.setText("Encrypt=no;TrustServerCertificate=yes;")
        form_layout.addRow("Extra Params:", self.txt_extra)
        
        # Test Query
        self.txt_test_query = QLineEdit()
        self.txt_test_query.setText("SELECT 1")
        form_layout.addRow("Test Query:", self.txt_test_query)
        
        # Aktif
        self.chk_aktif = QCheckBox("Bağlantı Aktif")
        self.chk_aktif.setChecked(True)
        form_layout.addRow("", self.chk_aktif)
        
        layout.addLayout(form_layout)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        self.btn_test = QPushButton("🔍 Test Bağlantı")
        self.btn_test.clicked.connect(self.test_baglanti)
        btn_layout.addWidget(self.btn_test)
        
        btn_layout.addStretch()
        
        self.btn_kaydet = QPushButton("💾 Kaydet")
        self.btn_kaydet.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_kaydet)
        
        self.btn_iptal = QPushButton("❌ İptal")
        self.btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_iptal)
        
        layout.addLayout(btn_layout)
        
        # Test sonucu
        self.lbl_test_sonuc = QLabel()
        self.lbl_test_sonuc.setWordWrap(True)
        layout.addWidget(self.lbl_test_sonuc)
    
    def toggle_sifre(self, state):
        """Şifre göster/gizle"""
        if state == Qt.Checked:
            self.txt_sifre.setEchoMode(QLineEdit.Normal)
        else:
            self.txt_sifre.setEchoMode(QLineEdit.Password)
    
    def load_data(self, data):
        """Mevcut veriyi form'a yükle"""
        self.txt_baglanti_adi.setText(data.get('baglanti_adi', ''))
        self.txt_aciklama.setText(data.get('aciklama', ''))
        self.cmb_baglanti_tipi.setCurrentText(data.get('baglanti_tipi', 'SQLSERVER'))
        self.txt_server.setText(data.get('server', ''))
        self.txt_database.setText(data.get('database_name', ''))
        self.txt_kullanici.setText(data.get('kullanici_adi', ''))
        # Şifre düzenlemede dolu gösterilmez (güvenlik)
        if not self.edit_mode:
            self.txt_sifre.setText(data.get('sifre_plain', ''))
        self.cmb_driver.setCurrentText(data.get('driver', 'ODBC Driver 18 for SQL Server'))
        self.spin_timeout.setValue(data.get('timeout', 10))
        self.spin_max_conn.setValue(data.get('max_connections', 20))
        self.txt_extra.setText(data.get('connection_string_extra', ''))
        self.txt_test_query.setText(data.get('test_query', 'SELECT 1'))
        self.chk_aktif.setChecked(data.get('aktif', True))
    
    def get_data(self):
        """Form verilerini dict olarak döndür"""
        return {
            'baglanti_adi': self.txt_baglanti_adi.text().strip(),
            'aciklama': self.txt_aciklama.text().strip(),
            'baglanti_tipi': self.cmb_baglanti_tipi.currentText(),
            'server': self.txt_server.text().strip(),
            'database_name': self.txt_database.text().strip(),
            'kullanici_adi': self.txt_kullanici.text().strip(),
            'sifre_plain': self.txt_sifre.text(),  # Plain text (SQL'de encrypt edilecek)
            'driver': self.cmb_driver.currentText(),
            'timeout': self.spin_timeout.value(),
            'max_connections': self.spin_max_conn.value(),
            'connection_string_extra': self.txt_extra.toPlainText().strip(),
            'test_query': self.txt_test_query.text().strip(),
            'aktif': self.chk_aktif.isChecked()
        }
    
    def test_baglanti(self):
        """Bağlantıyı test et"""
        data = self.get_data()
        
        # Validasyon
        if not all([data['baglanti_adi'], data['server'], data['database_name'], 
                    data['kullanici_adi'], data['sifre_plain']]):
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen zorunlu alanları doldurun!")
            return
        
        self.lbl_test_sonuc.setText("⏳ Test ediliyor...")
        self.btn_test.setEnabled(False)
        
        try:
            # Geçici connection string oluştur
            import pyodbc
            import time
            
            conn_str = (
                f"DRIVER={{{data['driver']}}};"
                f"SERVER={data['server']};"
                f"DATABASE={data['database_name']};"
                f"UID={data['kullanici_adi']};"
                f"PWD={data['sifre_plain']};"
                f"{data['connection_string_extra']}"
            )
            
            start_time = time.time()
            
            conn = pyodbc.connect(conn_str, timeout=data['timeout'])
            cursor = conn.cursor()
            cursor.execute(data['test_query'])
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self.lbl_test_sonuc.setText(
                f"✅ <span style='color: green;'><b>Bağlantı Başarılı!</b></span><br>"
                f"Test süresi: {duration_ms}ms"
            )
            
        except Exception as e:
            self.lbl_test_sonuc.setText(
                f"❌ <span style='color: red;'><b>Bağlantı Başarısız!</b></span><br>"
                f"Hata: {str(e)}"
            )
        
        finally:
            self.btn_test.setEnabled(True)
    
    def accept(self):
        """Kaydet"""
        data = self.get_data()
        
        # Validasyon
        if not all([data['baglanti_adi'], data['server'], data['database_name'],
                    data['kullanici_adi']]):
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen zorunlu alanları doldurun!")
            return
        
        # Şifre kontrolü (yeni kayıt veya şifre değiştirilmişse)
        if not self.edit_mode and not data['sifre_plain']:
            QMessageBox.warning(self, "Eksik Bilgi", "Şifre boş olamaz!")
            return
        
        super().accept()


class VeriTabaniBaglantiPage(BasePage):
    """Veritabanı Bağlantı Yönetimi Sayfası"""
    
    # İzinli kullanıcılar (sadece bunlar bu sayfayı görebilir)
    ADMIN_USERS = ['M.Aydin', 'admin', 'superadmin', 'Muhammed Aydin', 'muhammed.aydin']
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.password_manager = PasswordManager()
        
        # Kullanıcı kontrolü
        current_user = None
        possible_attrs = [
            'current_username',
            'current_user', 
            'logged_in_user',
            'username',
            'user',
            'kullanici_adi',
            'login_user',
            'user_name'
        ]
        
        for attr in possible_attrs:
            value = getattr(main_window, attr, None)
            if value:
                current_user = value
                break
        
        # Yetki kontrolü (production mod - debug kapalı)
        if current_user and current_user not in self.ADMIN_USERS:
            self._show_access_denied()
            return
        
        # Yetkili kullanıcı - Normal sayfa
        self.init_ui()
        
        # Otomatik yenileme timer (30 saniye)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_health_check)
        self.refresh_timer.start(30000)
    
    def _show_access_denied(self):
        """Yetkisiz erişim mesajı"""
        layout = QVBoxLayout()
        
        error_widget = QWidget()
        error_widget.setStyleSheet("""
            QWidget {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                padding: 30px;
            }
        """)
        
        error_layout = QVBoxLayout(error_widget)
        
        icon_label = QLabel("⛔")
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignCenter)
        error_layout.addWidget(icon_label)
        
        title_label = QLabel("YETKİSİZ ERİŞİM")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #856404;")
        title_label.setAlignment(Qt.AlignCenter)
        error_layout.addWidget(title_label)
        
        msg_label = QLabel(
            "Bu sayfaya sadece sistem yöneticileri erişebilir.\n\n"
            "Veritabanı bağlantı ayarları kritik sistem bilgileri içerir."
        )
        msg_label.setStyleSheet("font-size: 14px; color: #856404; margin-top: 20px;")
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        error_layout.addWidget(msg_label)
        
        layout.addStretch()
        layout.addWidget(error_widget)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Otomatik yenileme timer (30 saniye)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_health_check)
        self.refresh_timer.start(30000)
    
    def init_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel("🗄️ Veritabanı Bağlantı Yönetimi")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        # Açıklama
        desc_label = QLabel(
            "Sistemdeki tüm veritabanı bağlantılarını bu sayfadan yönetebilirsiniz. "
            "Bağlantı ayarlarını değiştirmek için kod düzenlemesine gerek yoktur."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(desc_label)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.btn_yeni = QPushButton("➕ Yeni Bağlantı")
        self.btn_yeni.clicked.connect(self.yeni_baglanti)
        toolbar.addWidget(self.btn_yeni)
        
        self.btn_duzenle = QPushButton("✏️ Düzenle")
        self.btn_duzenle.clicked.connect(self.duzenle)
        self.btn_duzenle.setEnabled(False)
        toolbar.addWidget(self.btn_duzenle)
        
        self.btn_test = QPushButton("🔍 Test")
        self.btn_test.clicked.connect(self.test_baglanti)
        self.btn_test.setEnabled(False)
        toolbar.addWidget(self.btn_test)
        
        self.btn_sil = QPushButton("🗑️ Sil")
        self.btn_sil.clicked.connect(self.sil)
        self.btn_sil.setEnabled(False)
        toolbar.addWidget(self.btn_sil)
        
        toolbar.addStretch()
        
        self.btn_yenile = QPushButton("↻ Yenile")
        self.btn_yenile.clicked.connect(self.yukle_veriler)
        toolbar.addWidget(self.btn_yenile)
        
        self.btn_pool_stats = QPushButton("📊 Pool İstatistikleri")
        self.btn_pool_stats.clicked.connect(self.goster_pool_stats)
        toolbar.addWidget(self.btn_pool_stats)
        
        layout.addLayout(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Bağlantı Adı", "Server", "Database", "Driver",
            "Timeout", "Pool", "Aktif", "Son Test"
        ])
        
        # Tablo ayarları
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.duzenle)
        
        # Kolonları genişlet
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch if i in [1, 2, 3] else QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # Status bar
        self.lbl_status = QLabel("Hazır")
        self.lbl_status.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        layout.addWidget(self.lbl_status)
        
        self.setLayout(layout)
        
        # Verileri yükle
        self.yukle_veriler()
    
    def yukle_veriler(self):
        """Veritabanından bağlantıları yükle"""
        self.lbl_status.setText("⏳ Yükleniyor...")
        
        try:
            from core.database import get_db_connection
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                query = """
                SELECT 
                    id, baglanti_adi, aciklama, server, database_name, 
                    driver, timeout, max_connections, aktif,
                    son_test_tarihi, son_test_basarili, son_test_mesaji, son_test_suresi_ms
                FROM sistem_veritabani_baglantilari
                WHERE silinme_tarihi IS NULL
                ORDER BY baglanti_adi
                """
                cursor.execute(query)
                rows = cursor.fetchall()
                
                self.table.setRowCount(0)
                
                for row in rows:
                    row_pos = self.table.rowCount()
                    self.table.insertRow(row_pos)
                    
                    # ID (hidden)
                    item_id = QTableWidgetItem(str(row.id))
                    self.table.setItem(row_pos, 0, item_id)
                    
                    # Bağlantı Adı
                    item_name = QTableWidgetItem(row.baglanti_adi)
                    if row.son_test_basarili:
                        item_name.setForeground(QColor('green'))
                    elif row.son_test_basarili == 0:  # False
                        item_name.setForeground(QColor('red'))
                    self.table.setItem(row_pos, 1, item_name)
                    
                    # Server
                    self.table.setItem(row_pos, 2, QTableWidgetItem(row.server))
                    
                    # Database
                    self.table.setItem(row_pos, 3, QTableWidgetItem(row.database_name))
                    
                    # Driver
                    driver_short = row.driver.replace("ODBC Driver ", "").replace(" for SQL Server", "")
                    self.table.setItem(row_pos, 4, QTableWidgetItem(driver_short))
                    
                    # Timeout
                    self.table.setItem(row_pos, 5, QTableWidgetItem(f"{row.timeout}s"))
                    
                    # Pool
                    self.table.setItem(row_pos, 6, QTableWidgetItem(str(row.max_connections)))
                    
                    # Aktif
                    aktif_text = "✓ Aktif" if row.aktif else "✗ Pasif"
                    item_aktif = QTableWidgetItem(aktif_text)
                    item_aktif.setForeground(QColor('green') if row.aktif else QColor('gray'))
                    self.table.setItem(row_pos, 7, item_aktif)
                    
                    # Son Test
                    if row.son_test_tarihi:
                        test_icon = "✓" if row.son_test_basarili else "✗"
                        test_text = f"{test_icon} {row.son_test_tarihi.strftime('%d.%m.%Y %H:%M')}"
                        if row.son_test_suresi_ms:
                            test_text += f" ({row.son_test_suresi_ms}ms)"
                        item_test = QTableWidgetItem(test_text)
                        item_test.setForeground(QColor('green') if row.son_test_basarili else QColor('red'))
                        if row.son_test_mesaji:
                            item_test.setToolTip(row.son_test_mesaji)
                    else:
                        item_test = QTableWidgetItem("Test edilmedi")
                        item_test.setForeground(QColor('gray'))
                    
                    self.table.setItem(row_pos, 8, item_test)
                
                cursor.close()
                
                self.lbl_status.setText(f"✓ {len(rows)} bağlantı yüklendi")
                
        except Exception as e:
            logger.error(f"Veri yükleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Veriler yüklenemedi:\n{str(e)}")
            self.lbl_status.setText("✗ Yükleme hatası")
    
    def on_selection_changed(self):
        """Seçim değiştiğinde butonları aktifleştir"""
        has_selection = len(self.table.selectedItems()) > 0
        self.btn_duzenle.setEnabled(has_selection)
        self.btn_test.setEnabled(has_selection)
        self.btn_sil.setEnabled(has_selection)
    
    def yeni_baglanti(self):
        """Yeni bağlantı ekle"""
        dialog = VeriTabaniBaglantiDialog(self, edit_mode=False)
        
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            
            try:
                from core.database import get_db_connection
                
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    query = """
                    INSERT INTO sistem_veritabani_baglantilari
                    (baglanti_adi, aciklama, baglanti_tipi, server, database_name,
                     kullanici_adi, sifre, driver, timeout, max_connections,
                     connection_string_extra, test_query, aktif, olusturma_tarihi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                    """
                    
                    cursor.execute(query, (
                        data['baglanti_adi'],
                        data['aciklama'],
                        data['baglanti_tipi'],
                        data['server'],
                        data['database_name'],
                        data['kullanici_adi'],
                        data['sifre_plain'],  # Plain text - şifreleme yok
                        data['driver'],
                        data['timeout'],
                        data['max_connections'],
                        data['connection_string_extra'],
                        data['test_query'],
                        data['aktif']
                    ))
                    
                    conn.commit()
                    cursor.close()
                    
                    QMessageBox.information(self, "Başarılı", "Bağlantı eklendi!")
                    
                    # Database manager'ı yenile
                    db_manager.reload_configs()
                    
                    self.yukle_veriler()
                    
            except Exception as e:
                logger.error(f"Bağlantı ekleme hatası: {e}")
                QMessageBox.critical(self, "Hata", f"Bağlantı eklenemedi:\n{str(e)}")
    
    def duzenle(self):
        """Seçili bağlantıyı düzenle"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return
        
        baglanti_id = int(self.table.item(selected_row, 0).text())
        
        try:
            from core.database import get_db_connection
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                query = f"""
                SELECT 
                    baglanti_adi, aciklama, baglanti_tipi, server, database_name,
                    kullanici_adi, driver, timeout, max_connections,
                    connection_string_extra, test_query, aktif
                FROM sistem_veritabani_baglantilari
                WHERE id = ?
                """
                cursor.execute(query, (baglanti_id,))
                row = cursor.fetchone()
                cursor.close()
                
                if not row:
                    QMessageBox.warning(self, "Hata", "Bağlantı bulunamadı!")
                    return
                
                data = {
                    'baglanti_adi': row.baglanti_adi,
                    'aciklama': row.aciklama,
                    'baglanti_tipi': row.baglanti_tipi,
                    'server': row.server,
                    'database_name': row.database_name,
                    'kullanici_adi': row.kullanici_adi,
                    'driver': row.driver,
                    'timeout': row.timeout,
                    'max_connections': row.max_connections,
                    'connection_string_extra': row.connection_string_extra,
                    'test_query': row.test_query,
                    'aktif': row.aktif
                }
                
                dialog = VeriTabaniBaglantiDialog(self, data, edit_mode=True)
                
                if dialog.exec() == QDialog.Accepted:
                    new_data = dialog.get_data()
                    
                    # UPDATE query
                    update_query = """
                    UPDATE sistem_veritabani_baglantilari
                    SET aciklama = ?, baglanti_tipi = ?, server = ?, database_name = ?,
                        kullanici_adi = ?, driver = ?, timeout = ?, max_connections = ?,
                        connection_string_extra = ?, test_query = ?, aktif = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                    """
                    
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(update_query, (
                            new_data['aciklama'],
                            new_data['baglanti_tipi'],
                            new_data['server'],
                            new_data['database_name'],
                            new_data['kullanici_adi'],
                            new_data['driver'],
                            new_data['timeout'],
                            new_data['max_connections'],
                            new_data['connection_string_extra'],
                            new_data['test_query'],
                            new_data['aktif'],
                            baglanti_id
                        ))
                        
                        # Şifre değiştirilmişse güncelle
                        if new_data['sifre_plain']:
                            cursor.execute(
                                """
                                UPDATE sistem_veritabani_baglantilari 
                                SET sifre = ?,
                                    guncelleme_tarihi = GETDATE()
                                WHERE id = ?
                                """,
                                (new_data['sifre_plain'], baglanti_id)
                            )
                        
                        conn.commit()
                        cursor.close()
                    
                    QMessageBox.information(self, "Başarılı", "Bağlantı güncellendi!")
                    
                    # Database manager'ı yenile
                    db_manager.reload_configs()
                    
                    self.yukle_veriler()
                    
        except Exception as e:
            logger.error(f"Düzenleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Bağlantı güncellenemedi:\n{str(e)}")
    
    def test_baglanti(self):
        """Seçili bağlantıyı test et"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return
        
        baglanti_adi = self.table.item(selected_row, 1).text()
        
        self.lbl_status.setText(f"⏳ {baglanti_adi} test ediliyor...")
        
        try:
            result = db_manager.test_connection(baglanti_adi)
            
            if result['success']:
                QMessageBox.information(
                    self, "Test Başarılı",
                    f"✅ Bağlantı başarılı!\n\n"
                    f"Süre: {result['duration_ms']}ms"
                )
                self.lbl_status.setText(f"✓ {baglanti_adi} testi başarılı ({result['duration_ms']}ms)")
            else:
                QMessageBox.warning(
                    self, "Test Başarısız",
                    f"❌ Bağlantı başarısız!\n\n"
                    f"Hata: {result.get('error', 'Bilinmeyen hata')}"
                )
                self.lbl_status.setText(f"✗ {baglanti_adi} testi başarısız")
            
            self.yukle_veriler()
            
        except Exception as e:
            logger.error(f"Test hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Test yapılamadı:\n{str(e)}")
            self.lbl_status.setText("✗ Test hatası")
    
    def sil(self):
        """Seçili bağlantıyı sil (soft delete)"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return
        
        baglanti_id = int(self.table.item(selected_row, 0).text())
        baglanti_adi = self.table.item(selected_row, 1).text()
        
        # ERP silinemez
        if baglanti_adi == 'ERP':
            QMessageBox.warning(self, "Uyarı", "ERP bağlantısı silinemez!")
            return
        
        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"'{baglanti_adi}' bağlantısını silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from core.database import get_db_connection
                
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    query = """
                    UPDATE sistem_veritabani_baglantilari
                    SET silinme_tarihi = GETDATE()
                    WHERE id = ?
                    """
                    cursor.execute(query, (baglanti_id,))
                    conn.commit()
                    cursor.close()
                
                QMessageBox.information(self, "Başarılı", "Bağlantı silindi!")
                
                # Database manager'ı yenile
                db_manager.reload_configs()
                
                self.yukle_veriler()
                
            except Exception as e:
                logger.error(f"Silme hatası: {e}")
                QMessageBox.critical(self, "Hata", f"Bağlantı silinemedi:\n{str(e)}")
    
    def goster_pool_stats(self):
        """Pool istatistiklerini göster"""
        try:
            stats = db_manager.get_pool_stats()
            
            msg = "📊 <b>Connection Pool İstatistikleri</b><br><br>"
            
            for name, stat in stats.items():
                msg += f"<b>{name}:</b><br>"
                msg += f"  • Toplam istek: {stat['total_requests']}<br>"
                msg += f"  • Pool hit: {stat['pool_hits']} ({stat['pool_hits']/max(stat['total_requests'],1)*100:.1f}%)<br>"
                msg += f"  • Yeni bağlantı: {stat['new_connections']}<br>"
                msg += f"  • Aktif: {stat['active_connections']}/{stat['max_connections']}<br>"
                msg += f"  • Pool'da: {stat['pool_size']}<br>"
                msg += f"  • Başarısız: {stat['failed_connections']}<br>"
                msg += "<br>"
            
            QMessageBox.information(self, "Pool İstatistikleri", msg)
            
        except Exception as e:
            logger.error(f"Pool stats hatası: {e}")
            QMessageBox.warning(self, "Hata", f"İstatistikler alınamadı:\n{str(e)}")
    
    def refresh_health_check(self):
        """Arka planda health check (30 saniyede bir)"""
        try:
            # Sadece verileri yenile, popup gösterme
            self.yukle_veriler()
        except:
            pass
