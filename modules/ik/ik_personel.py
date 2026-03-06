# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İK Personel Listesi
Tüm personel yönetimi, detay görüntüleme ve düzenleme
"""
from datetime import datetime, date
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QDateEdit, QTextEdit, QFormLayout, QTabWidget, QWidget,
    QScrollArea, QGridLayout, QSpinBox, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QPixmap, QPainter, QBrush, QFont

from components.base_page import BasePage
from core.database import get_db_connection


class PersonelDetayDialog(QDialog):
    """Personel detay ve düzenleme dialog'u"""
    
    def __init__(self, personel_id: int = None, theme: dict = None, parent=None):
        super().__init__(parent)
        self.personel_id = personel_id
        self.theme = theme
        self.personel_data = {}
        self.is_new = personel_id is None
        
        self.setWindowTitle("Yeni Personel" if self.is_new else "Personel Detayı")
        self.setMinimumSize(900, 650)
        if not self.is_new:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        """Personel verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.*, d.ad as departman_adi, poz.ad as pozisyon_adi
                FROM ik.personeller p
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                LEFT JOIN ik.pozisyonlar poz ON p.pozisyon_id = poz.id
                WHERE p.id = ?
            """, (self.personel_id,))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                self.personel_data = dict(zip(columns, row))
            
            conn.close()
        except Exception as e:
            print(f"Personel yükleme hatası: {e}")
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main', '#1a1f2e')}; }}
            QLabel {{ color: {self.theme.get('text', '#fff')}; }}
            QTabWidget::pane {{ 
                border: 1px solid {self.theme.get('border', '#3d4454')}; 
                background: {self.theme.get('bg_card', '#242938')}; 
                border-radius: 8px; 
            }}
            QTabBar::tab {{ 
                background: {self.theme.get('bg_input', '#2d3548')}; 
                color: {self.theme.get('text', '#fff')}; 
                padding: 10px 20px; 
                border: 1px solid {self.theme.get('border', '#3d4454')}; 
                border-bottom: none; 
                border-radius: 6px 6px 0 0; 
                margin-right: 2px; 
            }}
            QTabBar::tab:selected {{ 
                background: {self.theme.get('bg_card', '#242938')}; 
                border-bottom: 2px solid {self.theme.get('primary', '#6366f1')}; 
            }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit {{
                background: {self.theme.get('bg_input', '#2d3548')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text', '#fff')};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-bottom: 1px solid {self.theme.get('border')};")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 10, 20, 10)
        
        # Avatar
        avatar = QLabel()
        avatar.setFixedSize(60, 60)
        avatar.setStyleSheet(f"""
            background: {self.theme.get('primary', '#6366f1')};
            border-radius: 30px;
            font-size: 20px;
            font-weight: bold;
        """)
        avatar.setAlignment(Qt.AlignCenter)
        
        if self.is_new:
            initials = "+"
            ad, soyad = "Yeni", "Personel"
        else:
            ad = self.personel_data.get('ad', '')
            soyad = self.personel_data.get('soyad', '')
            initials = f"{ad[:1]}{soyad[:1]}".upper() if ad and soyad else "?"
        
        avatar.setText(initials)
        h_layout.addWidget(avatar)
        
        # İsim ve bilgiler
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_label = QLabel(f"{ad} {soyad}")
        name_label.setStyleSheet(f"color: {self.theme.get('text')}; font-size: 18px; font-weight: bold;")
        info_layout.addWidget(name_label)
        
        if not self.is_new:
            dept = self.personel_data.get('departman_adi', '-')
            pos = self.personel_data.get('pozisyon_adi', '-')
            sub_label = QLabel(f"{dept} • {pos}")
            sub_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px;")
            info_layout.addWidget(sub_label)
        else:
            sub_label = QLabel("Yeni kayıt oluşturuluyor...")
            sub_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px;")
            info_layout.addWidget(sub_label)
        
        h_layout.addLayout(info_layout, 1)
        
        # Durum badge (sadece var olan kayıtlar için)
        if not self.is_new:
            aktif = self.personel_data.get('aktif_mi', True)
            durum_label = QLabel("✓ Aktif" if aktif else "✗ Pasif")
            durum_label.setStyleSheet(f"""
                color: {'#22c55e' if aktif else '#ef4444'};
                background: {'rgba(34,197,94,0.2)' if aktif else 'rgba(239,68,68,0.2)'};
                padding: 6px 12px;
                border-radius: 12px;
                font-weight: bold;
            """)
            h_layout.addWidget(durum_label)
        
        # Kapat butonu
        close_btn = QPushButton("Kapat")
        close_btn.setFixedSize(60, 36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.theme.get('text_muted')};
                border: 1px solid {self.theme.get('border', '#555')};
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{ color: {self.theme.get('danger', '#ef4444')}; border-color: {self.theme.get('danger', '#ef4444')}; }}
        """)
        close_btn.clicked.connect(self.close)
        h_layout.addWidget(close_btn)
        
        layout.addWidget(header)
        
        # Tab Widget
        tabs = QTabWidget()
        tabs.addTab(self._create_genel_tab(), "📋 Genel Bilgiler")
        tabs.addTab(self._create_iletisim_tab(), "📞 İletişim")
        tabs.addTab(self._create_calisma_tab(), "💼 Çalışma Bilgileri")
        
        # Diğer sekmeler sadece var olan kayıtlar için
        if not self.is_new:
            tabs.addTab(self._create_izin_tab(), "🏖️ İzin Bilgileri")
            tabs.addTab(self._create_zimmet_tab(), "📦 Zimmetler")
            tabs.addTab(self._create_yetkinlik_tab(), "📊 Yetkinlikler")
        
        layout.addWidget(tabs, 1)
        
        # Alt butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 10, 20, 10)
        btn_layout.addStretch()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#6366f1')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {self.theme.get('primary_hover', '#5558e3')}; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_genel_tab(self) -> QWidget:
        """Genel bilgiler sekmesi"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        self.txt_sicil = QLineEdit(str(self.personel_data.get('sicil_no', '')))
        self.txt_sicil.setPlaceholderText("Personel sicil numarası")
        layout.addRow("Sicil No:", self.txt_sicil)
        
        self.txt_ad = QLineEdit(str(self.personel_data.get('ad', '')))
        self.txt_ad.setPlaceholderText("Adı *")
        layout.addRow("Ad *:", self.txt_ad)
        
        self.txt_soyad = QLineEdit(str(self.personel_data.get('soyad', '')))
        self.txt_soyad.setPlaceholderText("Soyadı *")
        layout.addRow("Soyad *:", self.txt_soyad)
        
        self.txt_tc = QLineEdit(str(self.personel_data.get('tc_kimlik_no', '') or ''))
        self.txt_tc.setPlaceholderText("11 haneli TC Kimlik No")
        self.txt_tc.setMaxLength(11)
        layout.addRow("TC Kimlik No:", self.txt_tc)
        
        self.dt_dogum = QDateEdit()
        self.dt_dogum.setCalendarPopup(True)
        if self.personel_data.get('dogum_tarihi'):
            self.dt_dogum.setDate(QDate(
                self.personel_data['dogum_tarihi'].year,
                self.personel_data['dogum_tarihi'].month,
                self.personel_data['dogum_tarihi'].day
            ))
        elif self.is_new:
            # Yeni kayıt için yaklaşık 30 yaş öncesi
            self.dt_dogum.setDate(QDate.currentDate().addYears(-30))
        layout.addRow("Doğum Tarihi:", self.dt_dogum)
        
        self.cmb_cinsiyet = QComboBox()
        self.cmb_cinsiyet.addItems(["Erkek", "Kadın"])
        if self.personel_data.get('cinsiyet') == 'Kadın':
            self.cmb_cinsiyet.setCurrentIndex(1)
        layout.addRow("Cinsiyet:", self.cmb_cinsiyet)
        
        self.txt_kart = QLineEdit(str(self.personel_data.get('kart_no', '') or ''))
        self.txt_kart.setPlaceholderText("PDKS Kart Numarası")
        layout.addRow("Kart No:", self.txt_kart)
        
        return widget
    
    def _create_iletisim_tab(self) -> QWidget:
        """İletişim bilgileri sekmesi"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        self.txt_telefon = QLineEdit(str(self.personel_data.get('telefon', '') or ''))
        layout.addRow("Telefon:", self.txt_telefon)
        
        self.txt_email = QLineEdit(str(self.personel_data.get('email', '') or ''))
        layout.addRow("E-posta:", self.txt_email)
        
        self.txt_adres = QTextEdit()
        self.txt_adres.setPlainText(str(self.personel_data.get('adres', '') or ''))
        self.txt_adres.setMaximumHeight(100)
        layout.addRow("Adres:", self.txt_adres)
        
        return widget
    
    def _create_calisma_tab(self) -> QWidget:
        """Çalışma bilgileri sekmesi"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Departman
        self.cmb_dept = QComboBox()
        self._load_departmanlar()
        layout.addRow("Departman *:", self.cmb_dept)
        
        # Pozisyon
        self.cmb_poz = QComboBox()
        self._load_pozisyonlar()
        layout.addRow("Pozisyon *:", self.cmb_poz)
        
        # İşe giriş
        self.dt_giris = QDateEdit()
        self.dt_giris.setCalendarPopup(True)
        if self.personel_data.get('ise_giris_tarihi'):
            self.dt_giris.setDate(QDate(
                self.personel_data['ise_giris_tarihi'].year,
                self.personel_data['ise_giris_tarihi'].month,
                self.personel_data['ise_giris_tarihi'].day
            ))
        elif self.is_new:
            # Yeni kayıt için bugün
            self.dt_giris.setDate(QDate.currentDate())
        layout.addRow("İşe Giriş *:", self.dt_giris)
        
        # Çalışma durumu
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Aktif", "İzinli", "Raporlu", "İşten Ayrıldı"])
        if not self.is_new and self.personel_data.get('calisma_durumu'):
            idx = self.cmb_durum.findText(self.personel_data['calisma_durumu'], Qt.MatchFixedString)
            if idx >= 0:
                self.cmb_durum.setCurrentIndex(idx)
        layout.addRow("Çalışma Durumu:", self.cmb_durum)
        
        return widget
    
    def _create_izin_tab(self) -> QWidget:
        """İzin bilgileri sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # İzin özeti
        ozet_frame = QFrame()
        ozet_frame.setStyleSheet(f"background: {self.theme.get('bg_main')}; border-radius: 8px;")
        ozet_layout = QHBoxLayout(ozet_frame)
        ozet_layout.setContentsMargins(16, 16, 16, 16)
        
        # Yıllık izin kartı
        yillik_kart = self._create_izin_kart("Yıllık İzin", "14", "3", "#22c55e")
        ozet_layout.addWidget(yillik_kart)
        
        mazeret_kart = self._create_izin_kart("Mazeret İzni", "3", "1", "#8b5cf6")
        ozet_layout.addWidget(mazeret_kart)
        
        rapor_kart = self._create_izin_kart("Rapor", "-", "5", "#f59e0b")
        ozet_layout.addWidget(rapor_kart)
        
        layout.addWidget(ozet_frame)
        
        # İzin geçmişi tablosu
        layout.addWidget(QLabel("📋 İzin Geçmişi"))
        
        self.izin_table = QTableWidget()
        self.izin_table.setColumnCount(5)
        self.izin_table.setHorizontalHeaderLabels(["Tarih", "İzin Türü", "Gün", "Durum", "Açıklama"])
        self.izin_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.izin_table.setStyleSheet(self._table_style())
        self._load_izin_gecmisi()
        
        layout.addWidget(self.izin_table, 1)
        
        return widget
    
    def _create_zimmet_tab(self) -> QWidget:
        """Zimmet bilgileri sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("📦 Teslim Edilen Zimmetler"))
        toolbar.addStretch()
        
        add_btn = QPushButton("➕ Yeni Zimmet")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
        """)
        add_btn.clicked.connect(self._add_zimmet)
        toolbar.addWidget(add_btn)
        
        layout.addLayout(toolbar)
        
        # Zimmet tablosu
        self.zimmet_table = QTableWidget()
        self.zimmet_table.setColumnCount(6)
        self.zimmet_table.setHorizontalHeaderLabels(["Teslim Tarihi", "Zimmet Türü", "Miktar", "Beden", "Durum", "İşlem"])
        self.zimmet_table.setColumnWidth(5, 120)
        self.zimmet_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.zimmet_table.setStyleSheet(self._table_style())
        self._load_zimmetler()
        
        layout.addWidget(self.zimmet_table, 1)
        
        return widget
    
    def _create_yetkinlik_tab(self) -> QWidget:
        """Yetkinlik bilgileri sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık ve özet
        header = QHBoxLayout()
        header.addWidget(QLabel("📊 Personel Yetkinlikleri"))
        header.addStretch()
        
        self.lbl_yetkinlik_ozet = QLabel()
        self.lbl_yetkinlik_ozet.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px;")
        header.addWidget(self.lbl_yetkinlik_ozet)
        
        layout.addLayout(header)
        
        # Seviye açıklaması
        legend = QHBoxLayout()
        seviye_bilgileri = [
            ("X", "Yok", "#64748b"),
            ("1", "Yetersiz", "#ef4444"),
            ("2", "Eğitimli", "#f97316"),
            ("3", "Bağımsız", "#eab308"),
            ("4", "Uzman", "#22c55e")
        ]
        for kod, ad, renk in seviye_bilgileri:
            box = QLabel(f" {kod} ")
            box.setStyleSheet(f"background: {renk}; color: white; border-radius: 4px; padding: 2px 6px; font-weight: bold; font-size: 10px;")
            legend.addWidget(box)
            txt = QLabel(ad)
            txt.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 10px;")
            legend.addWidget(txt)
        legend.addStretch()
        layout.addLayout(legend)
        
        # Yetkinlik tablosu
        self.yetkinlik_table = QTableWidget()
        self.yetkinlik_table.setColumnCount(5)
        self.yetkinlik_table.setHorizontalHeaderLabels(["Departman", "Kod", "Yetkinlik", "Seviye", "Hedef"])
        self.yetkinlik_table.setStyleSheet(self._table_style())
        self.yetkinlik_table.verticalHeader().setVisible(False)
        self.yetkinlik_table.setColumnWidth(0, 120)
        self.yetkinlik_table.setColumnWidth(1, 80)
        self.yetkinlik_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.yetkinlik_table.setColumnWidth(3, 60)
        self.yetkinlik_table.setColumnWidth(4, 60)
        
        self._load_yetkinlikler()
        
        layout.addWidget(self.yetkinlik_table, 1)
        
        return widget
    
    def _load_yetkinlikler(self):
        """Personel yetkinliklerini yükle"""
        if self.is_new:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT y.kategori, y.kod, y.ad, ISNULL(py.seviye, 0), ISNULL(py.hedef_seviye, 0)
                FROM ik.yetkinlikler y
                LEFT JOIN ik.personel_yetkinlikler py ON py.yetkinlik_id = y.id AND py.personel_id = ?
                WHERE y.aktif_mi = 1
                ORDER BY y.kategori, y.kod
            """, (self.personel_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            print(f"Yetkinlik kayıtları: {len(rows)} kayıt bulundu")
            
            self.yetkinlik_table.setRowCount(len(rows))
            toplam, sayi, eksik = 0, 0, 0
            
            seviye_renkleri = {
                0: "#64748b", 1: "#ef4444", 2: "#f97316", 3: "#eab308", 4: "#22c55e"
            }
            
            for i, (dept, kod, ad, seviye, hedef) in enumerate(rows):
                self.yetkinlik_table.setItem(i, 0, QTableWidgetItem(dept or "-"))
                self.yetkinlik_table.setItem(i, 1, QTableWidgetItem(kod))
                self.yetkinlik_table.setItem(i, 2, QTableWidgetItem(ad))
                
                # Seviye hücresi
                sev_item = QTableWidgetItem(str(seviye) if seviye > 0 else "X")
                sev_item.setTextAlignment(Qt.AlignCenter)
                sev_item.setBackground(QColor(seviye_renkleri.get(seviye, "#64748b")))
                sev_item.setForeground(QColor("white"))
                self.yetkinlik_table.setItem(i, 3, sev_item)
                
                # Hedef hücresi
                hdf_item = QTableWidgetItem(str(hedef) if hedef > 0 else "X")
                hdf_item.setTextAlignment(Qt.AlignCenter)
                self.yetkinlik_table.setItem(i, 4, hdf_item)
                
                toplam += seviye
                sayi += 1
                if hedef > 0 and seviye < hedef:
                    eksik += 1
            
            ort = toplam / sayi if sayi > 0 else 0
            self.lbl_yetkinlik_ozet.setText(f"Toplam: {sayi} | Ortalama: {ort:.1f} | Eksik: {eksik}")
            
            if len(rows) == 0:
                print("Yetkinlik tanımı bulunamadı")
            
        except Exception as e:
            print(f"Yetkinlik yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_izin_kart(self, baslik: str, hak: str, kullanilan: str, renk: str) -> QFrame:
        """İzin özet kartı"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {renk};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        
        title = QLabel(baslik)
        title.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 11px;")
        layout.addWidget(title)
        
        value = QLabel(f"{kullanilan} / {hak} gün")
        value.setStyleSheet(f"color: {renk}; font-size: 18px; font-weight: bold;")
        layout.addWidget(value)
        
        return frame
    
    def _load_departmanlar(self):
        """Departmanları yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY ad")
            
            current_id = self.personel_data.get('departman_id')
            idx = 0
            for i, row in enumerate(cursor.fetchall()):
                self.cmb_dept.addItem(row[1], row[0])
                if row[0] == current_id:
                    idx = i
            
            # Sadece var olan kayıtta seçili index'i ayarla
            if not self.is_new:
                self.cmb_dept.setCurrentIndex(idx)
            
            conn.close()
        except Exception as e:
            print(f"Departman yükleme hatası: {e}")
    
    def _load_pozisyonlar(self):
        """Pozisyonları yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM ik.pozisyonlar WHERE aktif_mi = 1 ORDER BY ad")
            
            current_id = self.personel_data.get('pozisyon_id')
            idx = 0
            for i, row in enumerate(cursor.fetchall()):
                self.cmb_poz.addItem(row[1], row[0])
                if row[0] == current_id:
                    idx = i
            
            # Sadece var olan kayıtta seçili index'i ayarla
            if not self.is_new:
                self.cmb_poz.setCurrentIndex(idx)
            
            conn.close()
        except Exception as e:
            print(f"Pozisyon yükleme hatası: {e}")
    
    def _load_izin_gecmisi(self):
        """İzin geçmişini yükle"""
        if self.is_new:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # İzin verilerini çek
            cursor.execute("""
                SELECT it.baslangic_tarihi, iz.ad, it.gun_sayisi, it.durum, it.aciklama
                FROM ik.izin_talepleri it
                JOIN ik.izin_turleri iz ON it.izin_turu_id = iz.id
                WHERE it.personel_id = ?
                ORDER BY it.baslangic_tarihi DESC
            """, (self.personel_id,))
            
            rows = cursor.fetchall()
            print(f"İzin geçmişi: {len(rows)} kayıt bulundu")
            
            self.izin_table.setRowCount(0)
            for row in rows:
                row_idx = self.izin_table.rowCount()
                self.izin_table.insertRow(row_idx)
                
                tarih = row[0].strftime('%d.%m.%Y') if row[0] else '-'
                self.izin_table.setItem(row_idx, 0, QTableWidgetItem(tarih))
                self.izin_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
                self.izin_table.setItem(row_idx, 2, QTableWidgetItem(str(row[2] or '')))
                
                durum_item = QTableWidgetItem(row[3] or '')
                if row[3] == 'ONAYLANDI':
                    durum_item.setForeground(QColor('#22c55e'))
                elif row[3] == 'REDDEDILDI':
                    durum_item.setForeground(QColor('#ef4444'))
                else:
                    durum_item.setForeground(QColor('#f59e0b'))
                self.izin_table.setItem(row_idx, 3, durum_item)
                
                self.izin_table.setItem(row_idx, 4, QTableWidgetItem(row[4] or ''))
            
            conn.close()
            
            # Eğer kayıt yoksa bilgi mesajı
            if len(rows) == 0:
                print("Bu personel için izin kaydı bulunamadı")
                
        except Exception as e:
            print(f"İzin geçmişi yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_zimmetler(self):
        """Zimmetleri yükle"""
        if self.is_new:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT z.teslim_tarihi, zt.ad, z.miktar, z.beden, z.durum, z.id
                FROM ik.zimmetler z
                JOIN ik.zimmet_turleri zt ON z.zimmet_turu_id = zt.id
                WHERE z.personel_id = ? AND z.durum = 'TESLIM'
                ORDER BY z.teslim_tarihi DESC
            """, (self.personel_id,))
            
            rows = cursor.fetchall()
            print(f"Zimmet kayıtları: {len(rows)} kayıt bulundu")
            
            self.zimmet_table.setRowCount(0)
            for row in rows:
                row_idx = self.zimmet_table.rowCount()
                self.zimmet_table.insertRow(row_idx)
                
                tarih = row[0].strftime('%d.%m.%Y') if row[0] else '-'
                self.zimmet_table.setItem(row_idx, 0, QTableWidgetItem(tarih))
                self.zimmet_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
                self.zimmet_table.setItem(row_idx, 2, QTableWidgetItem(str(row[2] or 1)))
                self.zimmet_table.setItem(row_idx, 3, QTableWidgetItem(row[3] or '-'))
                self.zimmet_table.setItem(row_idx, 4, QTableWidgetItem(row[4] or ''))
                
                # İade butonu
                widget = self.create_action_buttons([
                    ("İade", "İade", lambda checked, zid=row[5]: self._iade_zimmet(zid), "delete"),
                ])
                self.zimmet_table.setCellWidget(row_idx, 5, widget)
                self.zimmet_table.setRowHeight(row_idx, 42)
            
            conn.close()
            
            if len(rows) == 0:
                print("Bu personel için zimmet kaydı bulunamadı")
                
        except Exception as e:
            print(f"Zimmet yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _table_style(self):
        return f"""
            QTableWidget {{
                background: {self.theme.get('bg_main')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """
    
    def _add_zimmet(self):
        """Yeni zimmet ekle"""
        QMessageBox.information(self, "Bilgi", "Zimmet ekleme dialog'u açılacak...")
    
    def _iade_zimmet(self, zimmet_id: int):
        """Zimmet iade et"""
        reply = QMessageBox.question(self, "Onay", "Bu zimmet iade edilecek. Devam edilsin mi?")
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE ik.zimmetler 
                    SET durum = 'IADE', iade_tarihi = GETDATE(), guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (zimmet_id,))
                conn.commit()
                conn.close()
                
                self._load_zimmetler()
                QMessageBox.information(self, "Başarılı", "Zimmet iade edildi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"İade hatası: {e}")
    
    def _save(self):
        """Personel bilgilerini kaydet"""
        try:
            # Validasyon
            ad = self.txt_ad.text().strip()
            soyad = self.txt_soyad.text().strip()
            
            if not ad or not soyad:
                QMessageBox.warning(self, "Uyarı", "Ad ve soyad alanları zorunludur!")
                return
            
            # TC kontrol (girilmişse 11 hane olmalı)
            tc = self.txt_tc.text().strip()
            if tc and len(tc) != 11:
                QMessageBox.warning(self, "Uyarı", "TC Kimlik No 11 haneli olmalıdır!")
                return
            
            # Departman ve pozisyon kontrol
            dept_id = self.cmb_dept.currentData()
            poz_id = self.cmb_poz.currentData()
            
            if not dept_id or not poz_id:
                QMessageBox.warning(self, "Uyarı", "Departman ve pozisyon seçimi zorunludur!")
                return
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.is_new:
                # YENİ KAYIT - INSERT
                calisma_durumu = self.cmb_durum.currentText()
                aktif_mi = 0 if calisma_durumu == "İşten Ayrıldı" else 1

                cursor.execute("""
                    INSERT INTO ik.personeller (
                        sicil_no, ad, soyad, tc_kimlik_no, dogum_tarihi, cinsiyet, kart_no,
                        telefon, email, adres, departman_id, pozisyon_id, ise_giris_tarihi,
                        calisma_durumu, aktif_mi, olusturma_tarihi, guncelleme_tarihi
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
                """, (
                    self.txt_sicil.text().strip() or None,
                    ad,
                    soyad,
                    tc or None,
                    self.dt_dogum.date().toPython(),
                    self.cmb_cinsiyet.currentText(),
                    self.txt_kart.text().strip() or None,
                    self.txt_telefon.text().strip() or None,
                    self.txt_email.text().strip() or None,
                    self.txt_adres.toPlainText().strip() or None,
                    dept_id,
                    poz_id,
                    self.dt_giris.date().toPython(),
                    calisma_durumu,
                    aktif_mi
                ))
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Başarılı", 
                    f"{ad} {soyad} başarıyla sisteme eklendi.\n\n"
                    "Personelin izin hakları, zimmetleri ve yetkinlikleri "
                    "personel detayından yönetilebilir.")
                self.accept()
                
            else:
                # VAR OLAN KAYIT - UPDATE
                calisma_durumu = self.cmb_durum.currentText()
                aktif_mi = 0 if calisma_durumu == "İşten Ayrıldı" else 1

                cursor.execute("""
                    UPDATE ik.personeller SET
                        sicil_no = ?,
                        ad = ?,
                        soyad = ?,
                        tc_kimlik_no = ?,
                        dogum_tarihi = ?,
                        cinsiyet = ?,
                        kart_no = ?,
                        telefon = ?,
                        email = ?,
                        adres = ?,
                        departman_id = ?,
                        pozisyon_id = ?,
                        ise_giris_tarihi = ?,
                        calisma_durumu = ?,
                        aktif_mi = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    self.txt_sicil.text().strip() or None,
                    ad,
                    soyad,
                    tc or None,
                    self.dt_dogum.date().toPython(),
                    self.cmb_cinsiyet.currentText(),
                    self.txt_kart.text().strip() or None,
                    self.txt_telefon.text().strip() or None,
                    self.txt_email.text().strip() or None,
                    self.txt_adres.toPlainText().strip() or None,
                    dept_id,
                    poz_id,
                    self.dt_giris.date().toPython(),
                    calisma_durumu,
                    aktif_mi,
                    self.personel_id
                ))
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Başarılı", "Personel bilgileri güncellendi.")
                self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")


class IKPersonelPage(BasePage):
    """İK Personel Listesi Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.current_page = 1
        self.page_size = 50
        self.total_items = 0
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("👥 Personel Listesi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        header.addWidget(title)
        
        header.addStretch()
        
        # Yeni personel butonu
        new_btn = QPushButton("➕ Yeni Personel")
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #16a34a; }}
        """)
        new_btn.clicked.connect(self._new_personel)
        header.addWidget(new_btn)
        
        layout.addLayout(header)
        
        # Filtreler
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ad, soyad, sicil no ara...")
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.setMinimumWidth(250)
        self.search_input.returnPressed.connect(self._load_data)
        filter_layout.addWidget(self.search_input)
        
        # Departman filtresi
        filter_layout.addWidget(QLabel("Departman:"))
        self.dept_combo = QComboBox()
        self.dept_combo.setStyleSheet(self._combo_style())
        self.dept_combo.setMinimumWidth(150)
        self.dept_combo.addItem("Tümü", None)
        self.dept_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.dept_combo)
        
        # Durum filtresi
        filter_layout.addWidget(QLabel("Durum:"))
        self.status_combo = QComboBox()
        self.status_combo.setStyleSheet(self._combo_style())
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("Aktif", 1)
        self.status_combo.addItem("Pasif", 0)
        self.status_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.status_combo)
        
        filter_layout.addStretch()
        
        # İstatistik
        self.stat_label = QLabel()
        self.stat_label.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        filter_layout.addWidget(self.stat_label)
        
        layout.addWidget(filter_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Sicil No", "Ad Soyad", "Departman", "Pozisyon", "Telefon", "İşe Giriş", "Durum", "İşlem"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 90)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 80)
        self.table.setStyleSheet(self._table_style())
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_double_click)
        
        layout.addWidget(self.table, 1)
        
        # Sayfalama
        paging = QHBoxLayout()
        paging.addStretch()
        
        self.prev_btn = QPushButton("◀ Önceki")
        self.prev_btn.setStyleSheet(self._button_style())
        self.prev_btn.clicked.connect(self._prev_page)
        paging.addWidget(self.prev_btn)
        
        self.page_label = QLabel("Sayfa 1 / 1")
        self.page_label.setStyleSheet(f"color: {self.theme.get('text')}; margin: 0 16px;")
        paging.addWidget(self.page_label)
        
        self.next_btn = QPushButton("Sonraki ▶")
        self.next_btn.setStyleSheet(self._button_style())
        self.next_btn.clicked.connect(self._next_page)
        paging.addWidget(self.next_btn)
        
        layout.addLayout(paging)
        
        # Departmanları yükle
        self._load_departmanlar()
    
    def _input_style(self):
        return f"""
            QLineEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px 12px;
                color: {self.theme.get('text')};
            }}
        """
    
    def _combo_style(self):
        return f"""
            QComboBox {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
        """
    
    def _button_style(self):
        return f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: {self.theme.get('bg_hover')}; }}
            QPushButton:disabled {{ color: {self.theme.get('text_muted')}; }}
        """
    
    def _table_style(self):
        return f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {self.theme.get('border')};
            }}
            QTableWidget::item:selected {{
                background: {self.theme.get('primary')};
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary')};
                font-weight: bold;
            }}
        """
    
    def _load_departmanlar(self):
        """Departman filtresini doldur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.dept_combo.addItem(row[1], row[0])
            conn.close()
        except Exception as e:
            print(f"Departman yükleme hatası: {e}")
    
    def _load_data(self):
        """Personel listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            where = ["1=1"]
            params = []
            
            # Arama
            search = self.search_input.text().strip()
            if search:
                where.append("(p.sicil_no LIKE ? OR p.ad LIKE ? OR p.soyad LIKE ?)")
                params.extend([f"%{search}%"] * 3)
            
            # Departman
            dept_id = self.dept_combo.currentData()
            if dept_id:
                where.append("p.departman_id = ?")
                params.append(dept_id)
            
            # Durum
            status = self.status_combo.currentData()
            if status is not None:
                where.append("p.aktif_mi = ?")
                params.append(status)
            
            where_clause = " AND ".join(where)
            
            # Toplam sayı
            cursor.execute(f"SELECT COUNT(*) FROM ik.personeller p WHERE {where_clause}", params)
            self.total_items = cursor.fetchone()[0]
            self.total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)
            
            # Veri çek
            offset = (self.current_page - 1) * self.page_size
            cursor.execute(f"""
                SELECT p.id, p.sicil_no, p.ad, p.soyad, d.ad as dept, poz.ad as poz, 
                       p.telefon, p.ise_giris_tarihi, p.aktif_mi
                FROM ik.personeller p
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                LEFT JOIN ik.pozisyonlar poz ON p.pozisyon_id = poz.id
                WHERE {where_clause}
                ORDER BY p.ad, p.soyad
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, params + [offset, self.page_size])
            
            self.table.setRowCount(0)
            for row in cursor.fetchall():
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                
                # ID'yi sakla
                item = QTableWidgetItem(row[1] or '')
                item.setData(Qt.UserRole, row[0])
                self.table.setItem(row_idx, 0, item)
                
                # Ad Soyad
                self.table.setItem(row_idx, 1, QTableWidgetItem(f"{row[2]} {row[3]}"))
                
                # Departman
                self.table.setItem(row_idx, 2, QTableWidgetItem(row[4] or '-'))
                
                # Pozisyon
                self.table.setItem(row_idx, 3, QTableWidgetItem(row[5] or '-'))
                
                # Telefon
                self.table.setItem(row_idx, 4, QTableWidgetItem(row[6] or '-'))
                
                # İşe Giriş
                giris = row[7].strftime('%d.%m.%Y') if row[7] else '-'
                self.table.setItem(row_idx, 5, QTableWidgetItem(giris))
                
                # Durum
                aktif = row[8]
                durum_item = QTableWidgetItem("✓ Aktif" if aktif else "✗ Pasif")
                durum_item.setForeground(QColor('#22c55e' if aktif else '#ef4444'))
                self.table.setItem(row_idx, 6, durum_item)
                
                # İşlem butonu
                widget = self.create_action_buttons([
                    ("👁️", "Detay", lambda checked, pid=row[0]: self._show_detail(pid), "view"),
                ])
                self.table.setCellWidget(row_idx, 7, widget)
                self.table.setRowHeight(row_idx, 42)
            
            conn.close()
            
            # İstatistik güncelle
            self.stat_label.setText(f"Toplam: {self.total_items} personel")
            self._update_paging()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenemedi: {e}")
    
    def _update_paging(self):
        self.page_label.setText(f"Sayfa {self.current_page} / {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
    
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load_data()
    
    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._load_data()
    
    def _on_double_click(self, index):
        row = index.row()
        personel_id = self.table.item(row, 0).data(Qt.UserRole)
        self._show_detail(personel_id)
    
    def _show_detail(self, personel_id: int):
        """Personel detay dialog'unu aç"""
        dialog = PersonelDetayDialog(personel_id, self.theme, self)
        dialog.exec()
        self._load_data()
    
    def _new_personel(self):
        """Yeni personel ekle"""
        dialog = PersonelDetayDialog(None, self.theme, self)
        if dialog.exec():
            self._load_data()  # Listeyi yenile
