# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Sistem İşlem Logları Sayfası
log.islem_log tablosu için görüntüleme ve filtreleme
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDateEdit, QGroupBox, QFormLayout, QTextEdit, QDialog, QSplitter, QFrame
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class LogDetayDialog(QDialog):
    """Log detay görüntüleme dialogu"""
    
    def __init__(self, parent=None, log_data=None, theme=None):
        super().__init__(parent)
        self.log_data = log_data or {}
        self.theme = theme or {}
        self.setWindowTitle("Log Detayı")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Genel bilgiler
        info_group = QGroupBox("Genel Bilgiler")
        info_layout = QFormLayout()
        
        info_layout.addRow("Tarih:", QLabel(str(self.log_data.get('tarih', ''))))
        info_layout.addRow("Kullanıcı:", QLabel(self.log_data.get('kullanici_adi', '-')))
        info_layout.addRow("IP Adresi:", QLabel(self.log_data.get('ip_adresi', '-')))
        info_layout.addRow("Modül:", QLabel(self.log_data.get('modul', '-')))
        info_layout.addRow("İşlem:", QLabel(self.log_data.get('islem', '-')))
        info_layout.addRow("Tablo:", QLabel(self.log_data.get('tablo_adi', '-')))
        info_layout.addRow("Kayıt ID:", QLabel(str(self.log_data.get('kayit_id', '-'))))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Açıklama
        if self.log_data.get('aciklama'):
            aciklama_group = QGroupBox("Açıklama")
            aciklama_layout = QVBoxLayout()
            lbl_aciklama = QLabel(self.log_data.get('aciklama', ''))
            lbl_aciklama.setWordWrap(True)
            aciklama_layout.addWidget(lbl_aciklama)
            aciklama_group.setLayout(aciklama_layout)
            layout.addWidget(aciklama_group)
        
        # Eski ve yeni değerler
        splitter = QSplitter(Qt.Horizontal)
        
        # Eski değer
        eski_group = QGroupBox("Eski Değer")
        eski_layout = QVBoxLayout()
        txt_eski = QTextEdit()
        txt_eski.setPlainText(self.log_data.get('eski_deger', ''))
        txt_eski.setReadOnly(True)
        eski_layout.addWidget(txt_eski)
        eski_group.setLayout(eski_layout)
        splitter.addWidget(eski_group)
        
        # Yeni değer
        yeni_group = QGroupBox("Yeni Değer")
        yeni_layout = QVBoxLayout()
        txt_yeni = QTextEdit()
        txt_yeni.setPlainText(self.log_data.get('yeni_deger', ''))
        txt_yeni.setReadOnly(True)
        yeni_layout.addWidget(txt_yeni)
        yeni_group.setLayout(yeni_layout)
        splitter.addWidget(yeni_group)
        
        layout.addWidget(splitter)
        
        # Kapat butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_kapat = QPushButton("Kapat")
        btn_kapat.clicked.connect(self.close)
        btn_layout.addWidget(btn_kapat)
        layout.addLayout(btn_layout)


class SistemLogPage(BasePage):
    """Sistem İşlem Logları Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.log_data = []
        self._setup_ui()
        QTimer.singleShot(100, self.load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        header = QFrame()
        header.setStyleSheet(f"QFrame{{background:{self.theme.get('bg_card', '#1e293b')};border-radius:8px;padding:16px;}}")
        hl = QHBoxLayout(header)
        
        title = QLabel("📋 Sistem İşlem Logları")
        title.setStyleSheet(f"font-size:20px;font-weight:bold;color:{self.theme.get('text', '#ffffff')};")
        hl.addWidget(title)
        hl.addStretch()
        
        btn_refresh = QPushButton("🔄 Yenile")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.load_data)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#3b82f6')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        hl.addWidget(btn_refresh)
        
        layout.addWidget(header)
        
        # Filtre alanı
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"QFrame{{background:{self.theme.get('bg_card', '#1e293b')};border-radius:8px;padding:12px;}}")
        filter_layout = QHBoxLayout(filter_frame)
        
        # Tarih aralığı
        filter_layout.addWidget(QLabel("Başlangıç:"))
        self.date_baslangic = QDateEdit()
        self.date_baslangic.setCalendarPopup(True)
        self.date_baslangic.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(self.date_baslangic)
        
        filter_layout.addWidget(QLabel("Bitiş:"))
        self.date_bitis = QDateEdit()
        self.date_bitis.setCalendarPopup(True)
        self.date_bitis.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_bitis)
        
        # Modül filtresi
        filter_layout.addWidget(QLabel("Modül:"))
        self.cmb_modul = QComboBox()
        self.cmb_modul.addItem("Tümü", "")
        self.cmb_modul.setMinimumWidth(120)
        filter_layout.addWidget(self.cmb_modul)
        
        # İşlem filtresi
        filter_layout.addWidget(QLabel("İşlem:"))
        self.cmb_islem = QComboBox()
        self.cmb_islem.addItem("Tümü", "")
        self.cmb_islem.addItems(["INSERT", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "VIEW", "EXPORT"])
        filter_layout.addWidget(self.cmb_islem)
        
        # Kullanıcı filtresi
        filter_layout.addWidget(QLabel("Kullanıcı:"))
        self.txt_kullanici = QLineEdit()
        self.txt_kullanici.setPlaceholderText("Kullanıcı adı...")
        self.txt_kullanici.setMaximumWidth(150)
        filter_layout.addWidget(self.txt_kullanici)
        
        filter_layout.addStretch()
        
        btn_filtrele = QPushButton("🔍 Filtrele")
        btn_filtrele.clicked.connect(self.load_data)
        btn_filtrele.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#3b82f6')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        filter_layout.addWidget(btn_filtrele)
        
        btn_temizle = QPushButton("🗑️ Temizle")
        btn_temizle.clicked.connect(self.temizle_filtre)
        btn_temizle.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('warning', '#f59e0b')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: #d97706; }}
        """)
        filter_layout.addWidget(btn_temizle)
        
        layout.addWidget(filter_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Kullanıcı", "IP Adresi", "Modül", "İşlem", "Tablo", "Açıklama"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.detay_goster)
        
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
        
        layout.addWidget(self.table)
        
        # Modül listesini yükle
        self.load_moduller()
    
    def load_moduller(self):
        """Mevcut modülleri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT modul FROM log.islem_log WHERE modul IS NOT NULL ORDER BY modul")
            for row in cursor.fetchall():
                self.cmb_modul.addItem(row.modul, row.modul)
            conn.close()
        except Exception as e:
            print(f"Modül listesi yükleme hatası: {e}")
    
    def temizle_filtre(self):
        """Filtreleri temizle"""
        self.date_baslangic.setDate(QDate.currentDate().addDays(-7))
        self.date_bitis.setDate(QDate.currentDate())
        self.cmb_modul.setCurrentIndex(0)
        self.cmb_islem.setCurrentIndex(0)
        self.txt_kullanici.clear()
        self.load_data()
    
    def load_data(self):
        """Verileri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Filtre parametreleri
            baslangic = self.date_baslangic.date().toString("yyyy-MM-dd")
            bitis = self.date_bitis.date().addDays(1).toString("yyyy-MM-dd")
            modul = self.cmb_modul.currentData()
            islem = self.cmb_islem.currentText() if self.cmb_islem.currentIndex() > 0 else None
            kullanici = self.txt_kullanici.text().strip()
            
            query = """
                SELECT TOP 1000 id, tarih, kullanici_adi, ip_adresi, modul, islem, 
                       tablo_adi, kayit_id, aciklama, eski_deger, yeni_deger
                FROM log.islem_log
                WHERE tarih >= ? AND tarih < ?
            """
            params = [baslangic, bitis]
            
            if modul:
                query += " AND modul = ?"
                params.append(modul)
            
            if islem:
                query += " AND islem = ?"
                params.append(islem)
            
            if kullanici:
                query += " AND kullanici_adi LIKE ?"
                params.append(f"%{kullanici}%")
            
            query += " ORDER BY tarih DESC"
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            # Veriyi sakla
            self.log_data = [dict(zip(columns, row)) for row in rows]
            
            # Tabloyu doldur
            self.table.setRowCount(len(self.log_data))
            
            for row_idx, data in enumerate(self.log_data):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(data.get('id', ''))))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(data.get('tarih', ''))))
                self.table.setItem(row_idx, 2, QTableWidgetItem(data.get('kullanici_adi', '')))
                self.table.setItem(row_idx, 3, QTableWidgetItem(data.get('ip_adresi', '')))
                self.table.setItem(row_idx, 4, QTableWidgetItem(data.get('modul', '')))
                
                # İşlem tipi renkli
                islem_item = QTableWidgetItem(data.get('islem', ''))
                islem_tipi = data.get('islem', '')
                if islem_tipi == 'DELETE':
                    islem_item.setForeground(QColor('#ef4444'))
                elif islem_tipi == 'INSERT':
                    islem_item.setForeground(QColor('#22c55e'))
                elif islem_tipi == 'UPDATE':
                    islem_item.setForeground(QColor('#f59e0b'))
                self.table.setItem(row_idx, 5, islem_item)
                
                self.table.setItem(row_idx, 6, QTableWidgetItem(data.get('tablo_adi', '')))
                
                aciklama = data.get('aciklama', '') or ''
                if len(aciklama) > 50:
                    aciklama = aciklama[:50] + '...'
                self.table.setItem(row_idx, 7, QTableWidgetItem(aciklama))
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def detay_goster(self):
        """Seçili log kaydının detayını göster"""
        row = self.table.currentRow()
        if row >= 0 and row < len(self.log_data):
            dialog = LogDetayDialog(self, self.log_data[row], self.theme)
            dialog.exec()
