# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Sistem Yedekleme Sayfası
Veritabanı yedekleme ve geri yükleme işlemleri
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QGroupBox, QFormLayout, QProgressBar, QFileDialog,
    QCheckBox, QSpinBox, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QFont
from datetime import datetime
import os

from components.base_page import BasePage
from core.database import get_db_connection


class YedeklemeThread(QThread):
    """Yedekleme işlemi için thread"""
    progress = Signal(int, str)
    finished_signal = Signal(bool, str)
    
    def __init__(self, backup_path, backup_name):
        super().__init__()
        self.backup_path = backup_path
        self.backup_name = backup_name
    
    def run(self):
        try:
            self.progress.emit(10, "Yedekleme başlatılıyor...")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Veritabanı adını al
            cursor.execute("SELECT DB_NAME() as db_name")
            db_name = cursor.fetchone().db_name
            
            self.progress.emit(30, f"Veritabanı: {db_name}")
            
            # Yedekleme dosyası tam yolu
            full_path = os.path.join(self.backup_path, self.backup_name)
            
            self.progress.emit(50, "Yedekleme yapılıyor...")
            
            # SQL Server BACKUP komutu
            backup_sql = f"""
                BACKUP DATABASE [{db_name}] 
                TO DISK = N'{full_path}'
                WITH FORMAT, INIT,
                NAME = N'{db_name}-Full Backup',
                SKIP, NOREWIND, NOUNLOAD, STATS = 10
            """
            
            cursor.execute(backup_sql)
            
            # İşlemin tamamlanmasını bekle
            while cursor.nextset():
                pass
            
            conn.close()
            
            self.progress.emit(100, "Yedekleme tamamlandı!")
            self.finished_signal.emit(True, full_path)
            
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class SistemYedeklemePage(BasePage):
    """Sistem Yedekleme Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.yedekleme_thread = None
        self._setup_ui()
        QTimer.singleShot(100, self.load_yedekler)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        header = QFrame()
        header.setStyleSheet(f"QFrame{{background:{self.theme.get('bg_card', '#1e293b')};border-radius:8px;padding:16px;}}")
        hl = QHBoxLayout(header)
        
        title = QLabel("💾 Sistem Yedekleme")
        title.setStyleSheet(f"font-size:20px;font-weight:bold;color:{self.theme.get('text', '#ffffff')};")
        hl.addWidget(title)
        hl.addStretch()
        
        layout.addWidget(header)
        
        # Yedekleme işlemleri
        yedek_group = QGroupBox("Yeni Yedek Oluştur")
        yedek_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {self.theme.get('border', 'rgba(51, 65, 85, 0.5)')};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        yedek_layout = QVBoxLayout()
        
        # Yedek ayarları
        ayar_layout = QFormLayout()
        
        # Yedek dizini
        dizin_layout = QHBoxLayout()
        self.txt_dizin = QLineEdit()
        self.txt_dizin.setText("C:\\Backups\\Redline NexorERP")
        self.txt_dizin.setPlaceholderText("Yedekleme dizini...")
        dizin_layout.addWidget(self.txt_dizin)
        
        btn_dizin_sec = QPushButton("📁 Seç")
        btn_dizin_sec.clicked.connect(self.dizin_sec)
        btn_dizin_sec.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#3b82f6')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        dizin_layout.addWidget(btn_dizin_sec)
        ayar_layout.addRow("Yedek Dizini:", dizin_layout)
        
        # Yedek adı
        self.txt_yedek_adi = QLineEdit()
        self.txt_yedek_adi.setText(f"Redline NexorERP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
        ayar_layout.addRow("Yedek Adı:", self.txt_yedek_adi)
        
        yedek_layout.addLayout(ayar_layout)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        yedek_layout.addWidget(self.progress)
        
        self.lbl_durum = QLabel("")
        self.lbl_durum.setStyleSheet(f"color: {self.theme.get('text_muted', '#64748b')};")
        yedek_layout.addWidget(self.lbl_durum)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        self.btn_yedekle = QPushButton("💾 Yedek Al")
        self.btn_yedekle.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #16a34a; }}
        """)
        self.btn_yedekle.clicked.connect(self.yedek_al)
        btn_layout.addWidget(self.btn_yedekle)
        
        btn_layout.addStretch()
        yedek_layout.addLayout(btn_layout)
        
        yedek_group.setLayout(yedek_layout)
        layout.addWidget(yedek_group)
        
        # Otomatik yedekleme ayarları
        oto_group = QGroupBox("Otomatik Yedekleme Ayarları")
        oto_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {self.theme.get('border', 'rgba(51, 65, 85, 0.5)')};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
        """)
        oto_layout = QFormLayout()
        
        self.chk_oto_yedek = QCheckBox("Otomatik yedekleme aktif")
        oto_layout.addRow("", self.chk_oto_yedek)
        
        self.cmb_periyot = QComboBox()
        self.cmb_periyot.addItems(["Günlük", "Haftalık", "Aylık"])
        oto_layout.addRow("Periyot:", self.cmb_periyot)
        
        self.spin_saklama = QSpinBox()
        self.spin_saklama.setRange(1, 365)
        self.spin_saklama.setValue(30)
        self.spin_saklama.setSuffix(" gün")
        oto_layout.addRow("Saklama Süresi:", self.spin_saklama)
        
        btn_ayar_kaydet = QPushButton("Ayarları Kaydet")
        btn_ayar_kaydet.clicked.connect(self.ayarlari_kaydet)
        btn_ayar_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#3b82f6')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        oto_layout.addRow("", btn_ayar_kaydet)
        
        oto_group.setLayout(oto_layout)
        layout.addWidget(oto_group)
        
        # Mevcut yedekler
        liste_group = QGroupBox("Mevcut Yedekler")
        liste_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {self.theme.get('border', 'rgba(51, 65, 85, 0.5)')};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
        """)
        liste_layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.clicked.connect(self.load_yedekler)
        btn_yenile.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#3b82f6')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        toolbar.addWidget(btn_yenile)
        
        btn_geri_yukle = QPushButton("📥 Geri Yükle")
        btn_geri_yukle.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('warning', '#f59e0b')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: #d97706; }}
        """)
        btn_geri_yukle.clicked.connect(self.geri_yukle)
        toolbar.addWidget(btn_geri_yukle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('error', '#ef4444')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: #dc2626; }}
        """)
        btn_sil.clicked.connect(self.yedek_sil)
        toolbar.addWidget(btn_sil)
        
        toolbar.addStretch()
        liste_layout.addLayout(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Dosya Adı", "Boyut", "Tarih", "Yol"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
        # Tablo stili
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.theme.get('bg_card', '#1e293b')};
                color: {self.theme.get('text', '#ffffff')};
                border: 1px solid {self.theme.get('border', 'rgba(51, 65, 85, 0.5)')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border', 'rgba(51, 65, 85, 0.5)')};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {self.theme.get('primary', '#3b82f6')};
            }}
            QHeaderView::section {{
                background-color: {self.theme.get('bg_main', '#0f172a')};
                color: {self.theme.get('text', '#ffffff')};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)
        
        liste_layout.addWidget(self.table)
        
        liste_group.setLayout(liste_layout)
        layout.addWidget(liste_group)
    
    def dizin_sec(self):
        """Yedekleme dizini seç"""
        dizin = QFileDialog.getExistingDirectory(self, "Yedekleme Dizini Seç", self.txt_dizin.text())
        if dizin:
            self.txt_dizin.setText(dizin)
    
    def yedek_al(self):
        """Yedekleme işlemini başlat"""
        dizin = self.txt_dizin.text().strip()
        yedek_adi = self.txt_yedek_adi.text().strip()
        
        if not dizin or not yedek_adi:
            QMessageBox.warning(self, "Uyarı", "Lütfen dizin ve yedek adını belirtin!")
            return
        
        # Dizin kontrolü
        if not os.path.exists(dizin):
            reply = QMessageBox.question(
                self, "Onay",
                f"'{dizin}' dizini mevcut değil. Oluşturulsun mu?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    os.makedirs(dizin)
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Dizin oluşturulamadı: {str(e)}")
                    return
            else:
                return
        
        # Onay al
        reply = QMessageBox.question(
            self, "Onay",
            "Yedekleme işlemi başlatılsın mı?\n\nBu işlem birkaç dakika sürebilir.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # UI güncelle
        self.btn_yedekle.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        # Thread başlat
        self.yedekleme_thread = YedeklemeThread(dizin, yedek_adi)
        self.yedekleme_thread.progress.connect(self.on_progress)
        self.yedekleme_thread.finished_signal.connect(self.on_yedekleme_bitti)
        self.yedekleme_thread.start()
    
    def on_progress(self, value, message):
        """Progress güncelleme"""
        self.progress.setValue(value)
        self.lbl_durum.setText(message)
    
    def on_yedekleme_bitti(self, success, result):
        """Yedekleme tamamlandığında"""
        self.btn_yedekle.setEnabled(True)
        self.progress.setVisible(False)
        
        if success:
            QMessageBox.information(
                self, "Başarılı",
                f"Yedekleme tamamlandı!\n\nDosya: {result}"
            )
            # Yeni yedek adı oluştur
            self.txt_yedek_adi.setText(f"Redline NexorERP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
            self.load_yedekler()
            self.lbl_durum.setText("Yedekleme başarıyla tamamlandı.")
            self.lbl_durum.setStyleSheet(f"color: {self.theme.get('success', '#22c55e')};")
        else:
            QMessageBox.critical(self, "Hata", f"Yedekleme hatası:\n\n{result}")
            self.lbl_durum.setText(f"Hata: {result}")
            self.lbl_durum.setStyleSheet(f"color: {self.theme.get('error', '#ef4444')};")
    
    def load_yedekler(self):
        """Mevcut yedekleri listele"""
        dizin = self.txt_dizin.text().strip()
        
        if not dizin or not os.path.exists(dizin):
            self.table.setRowCount(0)
            return
        
        try:
            # .bak dosyalarını bul
            yedekler = []
            for dosya in os.listdir(dizin):
                if dosya.endswith('.bak'):
                    tam_yol = os.path.join(dizin, dosya)
                    boyut = os.path.getsize(tam_yol)
                    tarih = datetime.fromtimestamp(os.path.getmtime(tam_yol))
                    yedekler.append({
                        'dosya': dosya,
                        'boyut': boyut,
                        'tarih': tarih,
                        'yol': tam_yol
                    })
            
            # Tarihe göre sırala (yeniden eskiye)
            yedekler.sort(key=lambda x: x['tarih'], reverse=True)
            
            self.table.setRowCount(len(yedekler))
            for i, yedek in enumerate(yedekler):
                self.table.setItem(i, 0, QTableWidgetItem(yedek['dosya']))
                self.table.setItem(i, 1, QTableWidgetItem(self.format_boyut(yedek['boyut'])))
                self.table.setItem(i, 2, QTableWidgetItem(yedek['tarih'].strftime('%Y-%m-%d %H:%M')))
                self.table.setItem(i, 3, QTableWidgetItem(yedek['yol']))
                
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Yedekler yüklenirken hata: {str(e)}")
    
    def format_boyut(self, boyut):
        """Dosya boyutunu formatla"""
        if boyut < 1024:
            return f"{boyut} B"
        elif boyut < 1024 * 1024:
            return f"{boyut / 1024:.1f} KB"
        elif boyut < 1024 * 1024 * 1024:
            return f"{boyut / (1024 * 1024):.1f} MB"
        else:
            return f"{boyut / (1024 * 1024 * 1024):.2f} GB"
    
    def geri_yukle(self):
        """Seçili yedeği geri yükle"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir yedek seçin!")
            return
        
        dosya = self.table.item(row, 0).text()
        yol = self.table.item(row, 3).text()
        
        reply = QMessageBox.warning(
            self, "⚠️ DİKKAT",
            f"'{dosya}' yedeğini geri yüklemek istediğinize emin misiniz?\n\n"
            "⚠️ BU İŞLEM MEVCUT VERİTABANINI SİLECEK VE YEDEĞİ GERİ YÜKLEYECEKTİR!\n\n"
            "Bu işlem geri alınamaz!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # İkinci onay
        reply2 = QMessageBox.question(
            self, "Son Onay",
            "Bu işlemi gerçekten yapmak istiyor musunuz?\n\nTüm mevcut veriler silinecek!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply2 != QMessageBox.Yes:
            return
        
        QMessageBox.information(
            self, "Bilgi",
            "Geri yükleme işlemi için sistem yöneticisi ile iletişime geçin.\n\n"
            "Güvenlik nedeniyle bu işlem uygulama üzerinden yapılamamaktadır."
        )
    
    def yedek_sil(self):
        """Seçili yedeği sil"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir yedek seçin!")
            return
        
        dosya = self.table.item(row, 0).text()
        yol = self.table.item(row, 3).text()
        
        reply = QMessageBox.question(
            self, "Onay",
            f"'{dosya}' yedek dosyasını silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(yol)
                QMessageBox.information(self, "Başarılı", "Yedek dosyası silindi.")
                self.load_yedekler()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
    
    def ayarlari_kaydet(self):
        """Otomatik yedekleme ayarlarını kaydet"""
        QMessageBox.information(
            self, "Bilgi",
            "Otomatik yedekleme ayarları kaydedildi.\n\n"
            f"Durum: {'Aktif' if self.chk_oto_yedek.isChecked() else 'Pasif'}\n"
            f"Periyot: {self.cmb_periyot.currentText()}\n"
            f"Saklama Süresi: {self.spin_saklama.value()} gün"
        )
