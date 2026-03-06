# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İK PDKS Canlı Monitör
Anlık personel giriş/çıkış takibi, departman bazlı görünüm
"""
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QWidget, QGridLayout, QMessageBox, QDialog,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QColor, QPixmap, QPainter, QBrush, QFont

from components.base_page import BasePage
from core.database import get_db_connection


class PersonelKart(QFrame):
    """Personel durum kartı"""
    
    def __init__(self, data: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        status = self.data.get('status', 'OUT')
        
        # Renk belirleme
        if status == 'IN':
            border_color = '#22c55e'
            bg_color = 'rgba(34, 197, 94, 0.1)'
        elif status == 'LATE':
            border_color = '#ef4444'
            bg_color = 'rgba(239, 68, 68, 0.1)'
        elif status == 'LEAVE':
            border_color = '#f59e0b'
            bg_color = 'rgba(245, 158, 11, 0.1)'
        else:
            border_color = '#6b7280'
            bg_color = self.theme.get('bg_main')
        
        self.setFixedHeight(60)
        self.setStyleSheet(f"""
            PersonelKart {{
                background: {bg_color};
                border: 1px solid {self.theme.get('border')};
                border-left: 4px solid {border_color};
                border-radius: 6px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        
        # Avatar
        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignCenter)
        
        name = self.data.get('name', '?')
        initials = ''.join([n[0] for n in name.split()[:2]]).upper()
        avatar.setText(initials)
        avatar.setStyleSheet(f"""
            background: {border_color};
            color: white;
            border-radius: 20px;
            font-weight: bold;
            font-size: 12px;
        """)
        layout.addWidget(avatar)
        
        # Bilgi
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold; font-size: 12px;")
        info_layout.addWidget(name_label)
        
        detail_layout = QHBoxLayout()
        detail_layout.setSpacing(8)
        
        status_text = self.data.get('status_text', 'Dışarıda')
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {border_color}; font-size: 11px; font-weight: bold;")
        detail_layout.addWidget(status_label)
        
        time_text = self.data.get('time', '--:--')
        time_label = QLabel(time_text)
        time_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 10px;")
        detail_layout.addWidget(time_label)
        
        detail_layout.addStretch()
        info_layout.addLayout(detail_layout)
        
        layout.addLayout(info_layout, 1)


class DepartmanKolonu(QFrame):
    """Departman kolonu"""
    
    def __init__(self, dept_name: str, persons: list, theme: dict, parent=None):
        super().__init__(parent)
        self.dept_name = dept_name
        self.persons = persons
        self.theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedWidth(280)
        self.setStyleSheet(f"""
            DepartmanKolonu {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel(self.dept_name.upper())
        title.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold; font-size: 13px;")
        header.addWidget(title)
        
        header.addStretch()
        
        count = QLabel(str(len(self.persons)))
        count.setStyleSheet(f"""
            background: {self.theme.get('bg_input')};
            color: {self.theme.get('text')};
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
        """)
        header.addWidget(count)
        
        layout.addLayout(header)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                width: 6px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {self.theme.get('border')};
                border-radius: 3px;
            }}
        """)
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)
        
        for person in self.persons:
            card = PersonelKart(person, self.theme)
            content_layout.addWidget(card)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        
        layout.addWidget(scroll, 1)


class IKPdksPage(BasePage):
    """İK PDKS Canlı Monitör Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        
        # Otomatik yenileme
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_data)
        self.refresh_timer.start(5000)  # 5 saniyede bir
        
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📡 PDKS Canlı Monitör")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        header.addWidget(title)
        
        # Canlı gösterge
        self.live_indicator = QLabel("🔴 CANLI")
        self.live_indicator.setStyleSheet(f"""
            color: #ef4444;
            font-weight: bold;
            font-size: 12px;
            padding: 4px 12px;
            background: rgba(239, 68, 68, 0.1);
            border-radius: 12px;
        """)
        header.addWidget(self.live_indicator)
        
        header.addStretch()
        
        # Saat
        self.time_label = QLabel()
        self.time_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 14px;")
        header.addWidget(self.time_label)
        
        # Saat timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()
        
        # Yenile butonu
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        
        # Hareketler butonu
        movements_btn = QPushButton("📋 Hareketler")
        movements_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px 16px;
            }}
        """)
        movements_btn.clicked.connect(self._show_movements)
        header.addWidget(movements_btn)
        
        layout.addLayout(header)
        
        # Özet kartları
        ozet_frame = QFrame()
        ozet_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        ozet_layout = QHBoxLayout(ozet_frame)
        ozet_layout.setContentsMargins(16, 16, 16, 16)
        
        self.kart_toplam = self._create_ozet_kart("👥", "Toplam", "0", self.theme.get('primary'))
        ozet_layout.addWidget(self.kart_toplam)
        
        self.kart_iceride = self._create_ozet_kart("✅", "İçeride", "0", self.theme.get('success'))
        ozet_layout.addWidget(self.kart_iceride)
        
        self.kart_gelmedi = self._create_ozet_kart("❌", "Gelmedi", "0", self.theme.get('danger'))
        ozet_layout.addWidget(self.kart_gelmedi)
        
        self.kart_izinli = self._create_ozet_kart("🏖️", "İzinli", "0", self.theme.get('warning'))
        ozet_layout.addWidget(self.kart_izinli)
        
        self.kart_vardiya = self._create_ozet_kart("⏰", "Aktif Vardiya", "-", self.theme.get('info'))
        ozet_layout.addWidget(self.kart_vardiya)
        
        layout.addWidget(ozet_frame)
        
        # Departman kolonları
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:horizontal {{
                height: 8px;
                background: transparent;
            }}
            QScrollBar::handle:horizontal {{
                background: {self.theme.get('border')};
                border-radius: 4px;
            }}
        """)
        
        self.columns_container = QWidget()
        self.columns_container.setStyleSheet("background: transparent;")
        self.columns_layout = QHBoxLayout(self.columns_container)
        self.columns_layout.setSpacing(16)
        self.columns_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.columns_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll.setWidget(self.columns_container)
        layout.addWidget(self.scroll, 1)
    
    def _create_ozet_kart(self, icon: str, baslik: str, deger: str, renk: str) -> QFrame:
        """Özet kartı"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_main')};
                border: 1px solid {renk};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        header = QLabel(f"{icon} {baslik}")
        header.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 11px;")
        layout.addWidget(header)
        
        value = QLabel(deger)
        value.setObjectName("value")
        value.setStyleSheet(f"color: {renk}; font-size: 24px; font-weight: bold;")
        layout.addWidget(value)
        
        return frame
    
    def _update_clock(self):
        """Saati güncelle"""
        now = datetime.now()
        self.time_label.setText(now.strftime("%d.%m.%Y %H:%M:%S"))
        
        # Canlı gösterge animasyonu
        if now.second % 2 == 0:
            self.live_indicator.setText("🔴 CANLI")
        else:
            self.live_indicator.setText("⚫ CANLI")
    
    def _load_data(self):
        """PDKS verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            today = date.today()
            
            # Aktif personelleri al
            cursor.execute("""
                SELECT 
                    p.id, p.sicil_no, p.ad, p.soyad, 
                    d.ad as departman,
                    p.gunluk_durum,
                    p.son_giris,
                    p.son_cikis
                FROM ik.personeller p
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                WHERE p.aktif_mi = 1
                ORDER BY d.ad, p.ad
            """)
            
            employees = cursor.fetchall()
            
            # İzinli personelleri al
            cursor.execute("""
                SELECT personel_id FROM ik.izin_talepleri
                WHERE durum = 'ONAYLANDI' 
                  AND ? BETWEEN baslangic_tarihi AND bitis_tarihi
            """, (today,))
            izinli_ids = set(row[0] for row in cursor.fetchall())
            
            # Bugünkü hareketleri al
            cursor.execute("""
                SELECT personel_id, MAX(hareket_zamani) as son_hareket
                FROM ik.pdks_hareketler
                WHERE CAST(hareket_zamani AS DATE) = ?
                GROUP BY personel_id
            """, (today,))
            hareketler = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            # Personelleri departmanlara göre grupla
            dept_map = {}
            counts = {'toplam': 0, 'iceride': 0, 'gelmedi': 0, 'izinli': 0}
            
            for emp in employees:
                emp_id = emp[0]
                dept = emp[4] or 'Tanımsız'
                gunluk_durum = emp[5] or 0
                son_giris = emp[6]
                
                if dept not in dept_map:
                    dept_map[dept] = []
                
                # Durum belirleme
                if emp_id in izinli_ids:
                    status = 'LEAVE'
                    status_text = 'İzinli'
                    counts['izinli'] += 1
                elif gunluk_durum == 1:
                    status = 'IN'
                    status_text = 'İçeride'
                    counts['iceride'] += 1
                else:
                    status = 'OUT'
                    status_text = 'Dışarıda'
                    counts['gelmedi'] += 1
                
                counts['toplam'] += 1
                
                # Son hareket zamanı
                time_str = '--:--'
                if son_giris:
                    time_str = son_giris.strftime('%H:%M')
                
                person_data = {
                    'id': emp_id,
                    'name': f"{emp[2]} {emp[3]}",
                    'status': status,
                    'status_text': status_text,
                    'time': time_str
                }
                
                dept_map[dept].append(person_data)
            
            # Kartları güncelle
            self.kart_toplam.findChild(QLabel, "value").setText(str(counts['toplam']))
            self.kart_iceride.findChild(QLabel, "value").setText(str(counts['iceride']))
            self.kart_gelmedi.findChild(QLabel, "value").setText(str(counts['gelmedi']))
            self.kart_izinli.findChild(QLabel, "value").setText(str(counts['izinli']))
            
            # Kolonları temizle ve yeniden oluştur
            while self.columns_layout.count():
                item = self.columns_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Departman kolonlarını ekle
            for dept_name in sorted(dept_map.keys()):
                column = DepartmanKolonu(dept_name, dept_map[dept_name], self.theme)
                self.columns_layout.addWidget(column)
            
            self.columns_layout.addStretch()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"PDKS veri yükleme hatası: {e}")
    
    def _show_movements(self):
        """Hareket listesi dialog'u"""
        dialog = HareketlerDialog(self.theme, self)
        dialog.exec()


class HareketlerDialog(QDialog):
    """Günlük hareketler dialog'u"""
    
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Günlük Hareketler")
        self.setMinimumSize(800, 500)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık
        title = QLabel("📋 Günlük PDKS Hareketleri")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Tarih/Saat", "Personel", "Kart No", "Hareket", "Cihaz"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)
        
        # Kapat butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 10px 24px;
            }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        """Hareketleri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            today = date.today()
            
            cursor.execute("""
                SELECT 
                    h.hareket_zamani,
                    ISNULL(p.ad + ' ' + p.soyad, 'Bilinmiyor') as personel,
                    h.kart_no,
                    h.hareket_tipi,
                    c.cihaz_adi
                FROM ik.pdks_hareketler h
                LEFT JOIN ik.personeller p ON h.personel_id = p.id
                LEFT JOIN ik.pdks_cihazlari c ON h.cihaz_id = c.id
                WHERE CAST(h.hareket_zamani AS DATE) = ?
                ORDER BY h.hareket_zamani DESC
            """, (today,))
            
            self.table.setRowCount(0)
            for row in cursor.fetchall():
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                
                zaman = row[0].strftime('%d.%m.%Y %H:%M:%S') if row[0] else '-'
                self.table.setItem(row_idx, 0, QTableWidgetItem(zaman))
                self.table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(row_idx, 2, QTableWidgetItem(row[2] or ''))
                
                hareket = row[3] or ''
                hareket_item = QTableWidgetItem(hareket)
                if hareket == 'GIRIS':
                    hareket_item.setForeground(QColor(self.theme.get('success')))
                elif hareket == 'CIKIS':
                    hareket_item.setForeground(QColor(self.theme.get('danger')))
                self.table.setItem(row_idx, 3, hareket_item)
                
                self.table.setItem(row_idx, 4, QTableWidgetItem(row[4] or '-'))
            
            conn.close()
            
        except Exception as e:
            print(f"Hareket yükleme hatası: {e}")
