# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İK Zimmet Takip
KKD ve ekipman zimmet yönetimi, teslim/iade işlemleri
"""
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QDateEdit, QTextEdit, QFormLayout, QWidget, QSpinBox,
    QTabWidget, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager


class ZimmetTeslimDialog(QDialog):
    """Yeni zimmet teslim dialog'u"""
    
    def __init__(self, theme: dict, personel_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.personel_id = personel_id
        self.setWindowTitle("Zimmet Teslim")
        self.setMinimumSize(550, 500)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        title = QLabel("📦 Zimmet Teslim")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)
        
        # Form
        form = QFormLayout()
        form.setSpacing(12)
        
        # Personel seçimi
        self.cmb_personel = QComboBox()
        self.cmb_personel.setMinimumWidth(300)
        form.addRow("Personel:", self.cmb_personel)
        
        # Zimmet türü
        self.cmb_zimmet_turu = QComboBox()
        self.cmb_zimmet_turu.currentIndexChanged.connect(self._on_tur_changed)
        form.addRow("Zimmet Türü:", self.cmb_zimmet_turu)
        
        # Teslim tarihi
        self.dt_teslim = QDateEdit()
        self.dt_teslim.setCalendarPopup(True)
        self.dt_teslim.setDate(QDate.currentDate())
        form.addRow("Teslim Tarihi:", self.dt_teslim)
        
        # Miktar
        self.spn_miktar = QSpinBox()
        self.spn_miktar.setRange(1, 100)
        self.spn_miktar.setValue(1)
        form.addRow("Miktar:", self.spn_miktar)
        
        # Beden
        self.cmb_beden = QComboBox()
        self.cmb_beden.setEditable(True)
        self.cmb_beden.addItems(["", "XS", "S", "M", "L", "XL", "XXL", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45"])
        form.addRow("Beden:", self.cmb_beden)
        
        # Seri no
        self.txt_seri = QLineEdit()
        self.txt_seri.setPlaceholderText("Varsa seri/barkod numarası")
        form.addRow("Seri No:", self.txt_seri)
        
        # Açıklama
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(60)
        self.txt_aciklama.setPlaceholderText("Ek notlar...")
        form.addRow("Açıklama:", self.txt_aciklama)
        
        layout.addLayout(form)
        
        # Yenileme bilgisi
        self.lbl_yenileme = QLabel("")
        self.lbl_yenileme.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 11px;")
        layout.addWidget(self.lbl_yenileme)
        
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 10px 24px;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Teslim Et")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
            }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        """Verileri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Personeller
            cursor.execute("""
                SELECT id, sicil_no, ad + ' ' + soyad as ad_soyad
                FROM ik.personeller
                WHERE aktif_mi = 1
                ORDER BY ad, soyad
            """)
            
            idx = 0
            for i, row in enumerate(cursor.fetchall()):
                self.cmb_personel.addItem(f"{row[1]} - {row[2]}", row[0])
                if self.personel_id and row[0] == self.personel_id:
                    idx = i
            
            if self.personel_id:
                self.cmb_personel.setCurrentIndex(idx)
            
            # Zimmet türleri
            cursor.execute("SELECT id, ad, periyot_gun FROM ik.zimmet_turleri WHERE aktif_mi = 1 ORDER BY kategori, ad")
            for row in cursor.fetchall():
                self.cmb_zimmet_turu.addItem(row[1], {"id": row[0], "periyot": row[2]})
            
            conn.close()
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
    
    def _on_tur_changed(self):
        """Zimmet türü değiştiğinde"""
        data = self.cmb_zimmet_turu.currentData()
        if data and data.get('periyot'):
            periyot = data['periyot']
            sonraki = date.today() + timedelta(days=periyot)
            self.lbl_yenileme.setText(f"ℹ️ Yenileme periyodu: {periyot} gün | Sonraki yenileme: {sonraki.strftime('%d.%m.%Y')}")
        else:
            self.lbl_yenileme.setText("")
    
    def _save(self):
        """Zimmet teslim et"""
        try:
            personel_id = self.cmb_personel.currentData()
            zimmet_data = self.cmb_zimmet_turu.currentData()
            
            if not personel_id:
                QMessageBox.warning(self, "Uyarı", "Lütfen personel seçin.")
                return
            
            if not zimmet_data:
                QMessageBox.warning(self, "Uyarı", "Lütfen zimmet türü seçin.")
                return
            
            zimmet_turu_id = zimmet_data['id']
            periyot = zimmet_data.get('periyot')
            teslim_tarihi = self.dt_teslim.date().toPython()
            miktar = self.spn_miktar.value()
            beden = self.cmb_beden.currentText() or None
            seri_no = self.txt_seri.text() or None
            aciklama = self.txt_aciklama.toPlainText() or None
            
            # Sonraki yenileme tarihi
            sonraki_yenileme = None
            if periyot:
                sonraki_yenileme = teslim_tarihi + timedelta(days=periyot)
            
            # Zimmet no oluştur
            zimmet_no = f"ZMT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ik.zimmetler (
                    zimmet_no, personel_id, zimmet_turu_id, teslim_tarihi,
                    miktar, beden, seri_no, durum, sonraki_yenileme, aciklama
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'TESLIM', ?, ?)
            """, (zimmet_no, personel_id, zimmet_turu_id, teslim_tarihi,
                  miktar, beden, seri_no, sonraki_yenileme, aciklama))
            
            conn.commit()
            LogManager.log_insert('ik', 'ik.zimmetler', None, f'Zimmet teslim edildi: {zimmet_no}')
            conn.close()

            QMessageBox.information(self, "Başarılı", f"Zimmet teslim edildi.\nZimmet No: {zimmet_no}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")


class IKZimmetPage(BasePage):
    """İK Zimmet Takip Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📦 Zimmet Takip")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        header.addWidget(title)
        
        header.addStretch()
        
        # PDF Form butonu
        pdf_btn = QPushButton("📄 Zimmet Formu")
        pdf_btn.setStyleSheet(self._button_style())
        pdf_btn.clicked.connect(self._print_form)
        header.addWidget(pdf_btn)
        
        # Yeni teslim butonu
        new_btn = QPushButton("➕ Yeni Teslim")
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
        """)
        new_btn.clicked.connect(self._new_teslim)
        header.addWidget(new_btn)
        
        layout.addLayout(header)
        
        # Özet kartları
        ozet_frame = QFrame()
        ozet_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        ozet_layout = QHBoxLayout(ozet_frame)
        ozet_layout.setContentsMargins(16, 16, 16, 16)
        
        self.kart_teslim = self._create_ozet_kart("📦", "Teslim Edilen", "0", self.theme.get('primary'))
        ozet_layout.addWidget(self.kart_teslim)
        
        self.kart_iade = self._create_ozet_kart("↩️", "İade Edilen", "0", self.theme.get('success'))
        ozet_layout.addWidget(self.kart_iade)
        
        self.kart_yenileme = self._create_ozet_kart("⚠️", "Yenileme Bekleyen", "0", self.theme.get('warning'))
        ozet_layout.addWidget(self.kart_yenileme)
        
        self.kart_kayip = self._create_ozet_kart("❌", "Kayıp/Hasarlı", "0", self.theme.get('danger'))
        ozet_layout.addWidget(self.kart_kayip)
        
        layout.addWidget(ozet_frame)
        
        # Filtreler
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        
        # Arama
        filter_layout.addWidget(QLabel("Ara:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Personel adı, zimmet türü...")
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.setMinimumWidth(200)
        self.search_input.returnPressed.connect(self._load_data)
        filter_layout.addWidget(self.search_input)
        
        # Durum filtresi
        filter_layout.addWidget(QLabel("Durum:"))
        self.status_combo = QComboBox()
        self.status_combo.setStyleSheet(self._combo_style())
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("📦 Teslim Edildi", "TESLIM")
        self.status_combo.addItem("↩️ İade Edildi", "IADE")
        self.status_combo.addItem("❌ Kayıp", "KAYIP")
        self.status_combo.addItem("⚠️ Hasarlı", "HASARLI")
        self.status_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.status_combo)
        
        # Kategori filtresi
        filter_layout.addWidget(QLabel("Kategori:"))
        self.kategori_combo = QComboBox()
        self.kategori_combo.setStyleSheet(self._combo_style())
        self.kategori_combo.addItem("Tümü", None)
        self.kategori_combo.addItem("🦺 KKD", "KKD")
        self.kategori_combo.addItem("🔧 Ekipman", "EKIPMAN")
        self.kategori_combo.addItem("🚗 Araç", "ARAC")
        self.kategori_combo.addItem("📁 Diğer", "DIGER")
        self.kategori_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.kategori_combo)
        
        filter_layout.addStretch()

        # Disa Aktar
        filter_layout.addWidget(self.create_export_button(title="Zimmet Takip", table_attr="aktif_table"))

        layout.addWidget(filter_frame)

        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet(self._tab_style())
        
        tabs.addTab(self._create_aktif_tab(), "📦 Aktif Zimmetler")
        tabs.addTab(self._create_yenileme_tab(), "⚠️ Yenileme Bekleyenler")
        tabs.addTab(self._create_gecmis_tab(), "📋 Tüm Geçmiş")
        
        layout.addWidget(tabs, 1)
    
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
    
    def _create_aktif_tab(self) -> QWidget:
        """Aktif zimmetler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        self.aktif_table = QTableWidget()
        self.aktif_table.setColumnCount(9)
        self.aktif_table.setHorizontalHeaderLabels([
            "Zimmet No", "Personel", "Zimmet Türü", "Kategori", "Teslim Tarihi", 
            "Miktar", "Beden", "Yenileme", "İşlem"
        ])
        self.aktif_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.aktif_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.aktif_table.setColumnWidth(0, 140)
        self.aktif_table.setColumnWidth(3, 80)
        self.aktif_table.setColumnWidth(4, 100)
        self.aktif_table.setColumnWidth(5, 60)
        self.aktif_table.setColumnWidth(6, 60)
        self.aktif_table.setColumnWidth(7, 100)
        self.aktif_table.setColumnWidth(8, 120)
        self.aktif_table.setStyleSheet(self._table_style())
        self.aktif_table.verticalHeader().setVisible(False)
        self.aktif_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.aktif_table)
        return widget
    
    def _create_yenileme_tab(self) -> QWidget:
        """Yenileme bekleyenler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        self.yenileme_table = QTableWidget()
        self.yenileme_table.setColumnCount(7)
        self.yenileme_table.setHorizontalHeaderLabels([
            "Personel", "Zimmet Türü", "Teslim Tarihi", "Yenileme Tarihi",
            "Gecikme (Gün)", "Durum", "İşlem"
        ])
        self.yenileme_table.setColumnWidth(6, 120)
        self.yenileme_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.yenileme_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.yenileme_table.setStyleSheet(self._table_style())
        self.yenileme_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.yenileme_table)
        return widget
    
    def _create_gecmis_tab(self) -> QWidget:
        """Tüm geçmiş sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        self.gecmis_table = QTableWidget()
        self.gecmis_table.setColumnCount(8)
        self.gecmis_table.setHorizontalHeaderLabels([
            "Zimmet No", "Personel", "Zimmet Türü", "Teslim", "İade", 
            "Miktar", "Durum", "Açıklama"
        ])
        self.gecmis_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.gecmis_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.gecmis_table.setStyleSheet(self._table_style())
        self.gecmis_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.gecmis_table)
        return widget
    
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
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary')};
                font-weight: bold;
            }}
        """
    
    def _tab_style(self):
        return f"""
            QTabWidget::pane {{ 
                border: 1px solid {self.theme.get('border')}; 
                background: {self.theme.get('bg_card')}; 
                border-radius: 8px; 
            }}
            QTabBar::tab {{ 
                background: {self.theme.get('bg_input')}; 
                color: {self.theme.get('text')}; 
                padding: 10px 20px; 
                border: 1px solid {self.theme.get('border')}; 
                border-bottom: none; 
                border-radius: 6px 6px 0 0; 
                margin-right: 2px; 
            }}
            QTabBar::tab:selected {{ 
                background: {self.theme.get('bg_card')}; 
                border-bottom: 2px solid {self.theme.get('primary')}; 
            }}
        """
    
    def _load_data(self):
        """Zimmet verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            where = ["1=1"]
            params = []
            
            # Durum filtresi
            status = self.status_combo.currentData()
            if status:
                where.append("z.durum = ?")
                params.append(status)
            
            # Kategori filtresi
            kategori = self.kategori_combo.currentData()
            if kategori:
                where.append("zt.kategori = ?")
                params.append(kategori)
            
            # Arama
            search = self.search_input.text().strip()
            if search:
                where.append("(p.ad LIKE ? OR p.soyad LIKE ? OR zt.ad LIKE ?)")
                params.extend([f"%{search}%"] * 3)
            
            where_clause = " AND ".join(where)
            
            # Özet sayıları
            cursor.execute("SELECT COUNT(*) FROM ik.zimmetler WHERE durum = 'TESLIM'")
            teslim = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ik.zimmetler WHERE durum = 'IADE'")
            iade = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM ik.zimmetler 
                WHERE durum = 'TESLIM' AND sonraki_yenileme IS NOT NULL AND sonraki_yenileme <= GETDATE()
            """)
            yenileme = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ik.zimmetler WHERE durum IN ('KAYIP', 'HASARLI')")
            kayip = cursor.fetchone()[0]
            
            # Kartları güncelle
            self.kart_teslim.findChild(QLabel, "value").setText(str(teslim))
            self.kart_iade.findChild(QLabel, "value").setText(str(iade))
            self.kart_yenileme.findChild(QLabel, "value").setText(str(yenileme))
            self.kart_kayip.findChild(QLabel, "value").setText(str(kayip))
            
            # Aktif zimmetler
            cursor.execute(f"""
                SELECT 
                    z.id, z.zimmet_no, p.ad + ' ' + p.soyad as personel,
                    zt.ad as zimmet_adi, zt.kategori, z.teslim_tarihi,
                    z.miktar, z.beden, z.sonraki_yenileme
                FROM ik.zimmetler z
                JOIN ik.personeller p ON z.personel_id = p.id
                JOIN ik.zimmet_turleri zt ON z.zimmet_turu_id = zt.id
                WHERE z.durum = 'TESLIM' AND {where_clause}
                ORDER BY z.teslim_tarihi DESC
            """, params)
            
            self.aktif_table.setRowCount(0)
            for row in cursor.fetchall():
                row_idx = self.aktif_table.rowCount()
                self.aktif_table.insertRow(row_idx)
                
                # ID sakla
                item = QTableWidgetItem(row[1] or '')
                item.setData(Qt.UserRole, row[0])
                self.aktif_table.setItem(row_idx, 0, item)
                
                self.aktif_table.setItem(row_idx, 1, QTableWidgetItem(row[2] or ''))
                self.aktif_table.setItem(row_idx, 2, QTableWidgetItem(row[3] or ''))
                self.aktif_table.setItem(row_idx, 3, QTableWidgetItem(row[4] or ''))
                
                teslim_tarihi = row[5].strftime('%d.%m.%Y') if row[5] else '-'
                self.aktif_table.setItem(row_idx, 4, QTableWidgetItem(teslim_tarihi))
                
                self.aktif_table.setItem(row_idx, 5, QTableWidgetItem(str(row[6] or 1)))
                self.aktif_table.setItem(row_idx, 6, QTableWidgetItem(row[7] or '-'))
                
                # Yenileme
                if row[8]:
                    yenileme_str = row[8].strftime('%d.%m.%Y')
                    yenileme_item = QTableWidgetItem(yenileme_str)
                    if row[8] <= date.today():
                        yenileme_item.setForeground(QColor(self.theme.get('danger')))
                    self.aktif_table.setItem(row_idx, 7, yenileme_item)
                else:
                    self.aktif_table.setItem(row_idx, 7, QTableWidgetItem('-'))
                
                # İade butonu
                widget = self.create_action_buttons([
                    ("↩️", "İade Al", lambda checked, zid=row[0]: self._iade_zimmet(zid), "delete"),
                ])
                self.aktif_table.setCellWidget(row_idx, 8, widget)
                self.aktif_table.setRowHeight(row_idx, 42)
            
            # Yenileme bekleyenler
            self._load_yenileme_data(cursor)
            
            # Geçmiş
            self._load_gecmis_data(cursor, where_clause, params)
            
            conn.close()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Veri yüklenemedi: {e}")
    
    def _load_yenileme_data(self, cursor):
        """Yenileme bekleyenleri yükle"""
        cursor.execute("""
            SELECT 
                p.ad + ' ' + p.soyad as personel,
                zt.ad as zimmet_adi,
                z.teslim_tarihi,
                z.sonraki_yenileme,
                z.id
            FROM ik.zimmetler z
            JOIN ik.personeller p ON z.personel_id = p.id
            JOIN ik.zimmet_turleri zt ON z.zimmet_turu_id = zt.id
            WHERE z.durum = 'TESLIM' 
              AND z.sonraki_yenileme IS NOT NULL 
              AND z.sonraki_yenileme <= DATEADD(day, 7, GETDATE())
            ORDER BY z.sonraki_yenileme
        """)
        
        self.yenileme_table.setRowCount(0)
        today = date.today()
        
        for row in cursor.fetchall():
            row_idx = self.yenileme_table.rowCount()
            self.yenileme_table.insertRow(row_idx)
            
            self.yenileme_table.setItem(row_idx, 0, QTableWidgetItem(row[0] or ''))
            self.yenileme_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
            
            teslim = row[2].strftime('%d.%m.%Y') if row[2] else '-'
            self.yenileme_table.setItem(row_idx, 2, QTableWidgetItem(teslim))
            
            yenileme = row[3].strftime('%d.%m.%Y') if row[3] else '-'
            self.yenileme_table.setItem(row_idx, 3, QTableWidgetItem(yenileme))
            
            # Gecikme
            if row[3]:
                gecikme = (today - row[3]).days
                gecikme_item = QTableWidgetItem(str(gecikme) if gecikme > 0 else "0")
                if gecikme > 0:
                    gecikme_item.setForeground(QColor(self.theme.get('danger')))
                self.yenileme_table.setItem(row_idx, 4, gecikme_item)
            
            # Durum
            if row[3] and row[3] < today:
                durum = "⚠️ GECİKMİŞ"
                durum_item = QTableWidgetItem(durum)
                durum_item.setForeground(QColor(self.theme.get('danger')))
            else:
                durum = "⏳ Yaklaşıyor"
                durum_item = QTableWidgetItem(durum)
                durum_item.setForeground(QColor(self.theme.get('warning')))
            self.yenileme_table.setItem(row_idx, 5, durum_item)
            
            # Yenile butonu
            widget = self.create_action_buttons([
                ("🔄", "Yenile", lambda checked, zid=row[4]: self._yenile_zimmet(zid), "success"),
            ])
            self.yenileme_table.setCellWidget(row_idx, 6, widget)
            self.yenileme_table.setRowHeight(row_idx, 42)
    
    def _load_gecmis_data(self, cursor, where_clause, params):
        """Geçmiş verileri yükle"""
        cursor.execute(f"""
            SELECT 
                z.zimmet_no, p.ad + ' ' + p.soyad as personel,
                zt.ad as zimmet_adi, z.teslim_tarihi, z.iade_tarihi,
                z.miktar, z.durum, z.aciklama
            FROM ik.zimmetler z
            JOIN ik.personeller p ON z.personel_id = p.id
            JOIN ik.zimmet_turleri zt ON z.zimmet_turu_id = zt.id
            WHERE {where_clause}
            ORDER BY z.teslim_tarihi DESC
        """, params)
        
        self.gecmis_table.setRowCount(0)
        for row in cursor.fetchall():
            row_idx = self.gecmis_table.rowCount()
            self.gecmis_table.insertRow(row_idx)
            
            self.gecmis_table.setItem(row_idx, 0, QTableWidgetItem(row[0] or ''))
            self.gecmis_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
            self.gecmis_table.setItem(row_idx, 2, QTableWidgetItem(row[2] or ''))
            
            teslim = row[3].strftime('%d.%m.%Y') if row[3] else '-'
            self.gecmis_table.setItem(row_idx, 3, QTableWidgetItem(teslim))
            
            iade = row[4].strftime('%d.%m.%Y') if row[4] else '-'
            self.gecmis_table.setItem(row_idx, 4, QTableWidgetItem(iade))
            
            self.gecmis_table.setItem(row_idx, 5, QTableWidgetItem(str(row[5] or 1)))
            
            durum_item = QTableWidgetItem(row[6] or '')
            if row[6] == 'TESLIM':
                durum_item.setForeground(QColor(self.theme.get('primary')))
            elif row[6] == 'IADE':
                durum_item.setForeground(QColor(self.theme.get('success')))
            elif row[6] in ('KAYIP', 'HASARLI'):
                durum_item.setForeground(QColor(self.theme.get('danger')))
            self.gecmis_table.setItem(row_idx, 6, durum_item)
            
            self.gecmis_table.setItem(row_idx, 7, QTableWidgetItem(row[7] or ''))
    
    def _new_teslim(self):
        """Yeni zimmet teslim"""
        dialog = ZimmetTeslimDialog(self.theme, parent=self)
        if dialog.exec():
            self._load_data()
    
    def _iade_zimmet(self, zimmet_id: int):
        """Zimmet iade al"""
        reply = QMessageBox.question(self, "Onay", "Bu zimmet iade alınacak. Devam edilsin mi?")
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
                LogManager.log_update('ik', 'ik.zimmetler', zimmet_id, 'Zimmet iade alindi')
                conn.close()

                self._load_data()
                QMessageBox.information(self, "Başarılı", "Zimmet iade alındı.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"İade hatası: {e}")
    
    def _yenile_zimmet(self, zimmet_id: int):
        """Zimmeti yenile - yeni teslim oluştur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Eski zimmeti al
            cursor.execute("""
                SELECT personel_id, zimmet_turu_id, beden FROM ik.zimmetler WHERE id = ?
            """, (zimmet_id,))
            row = cursor.fetchone()
            
            if row:
                # Eskiyi iade et
                cursor.execute("""
                    UPDATE ik.zimmetler 
                    SET durum = 'IADE', iade_tarihi = GETDATE(), guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (zimmet_id,))
                
                conn.commit()
                LogManager.log_update('ik', 'ik.zimmetler', zimmet_id, 'Zimmet yenileme icin iade edildi')
                conn.close()

                # Yeni teslim dialog'u aç
                dialog = ZimmetTeslimDialog(self.theme, personel_id=row[0], parent=self)
                if dialog.exec():
                    self._load_data()
                else:
                    self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yenileme hatası: {e}")
    
    def _print_form(self):
        """Zimmet formu yazdır - secili personelin aktif zimmetleri"""
        # Aktif sekmeden secili satirin personel ID'sini al
        table = self.aktif_table
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen tablodan bir zimmet satiri secin.")
            return

        zimmet_id = table.item(row, 0).data(Qt.UserRole)
        if not zimmet_id:
            return

        try:
            # Zimmet'ten personel_id bul
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT personel_id FROM ik.zimmetler WHERE id = ?", (zimmet_id,))
            prow = cursor.fetchone()
            conn.close()

            if not prow:
                QMessageBox.warning(self, "Uyari", "Zimmet kaydi bulunamadi.")
                return

            personel_id = prow[0]

            from utils.zimmet_pdf import zimmet_formu_pdf
            pdf_path = zimmet_formu_pdf(personel_id)
            QMessageBox.information(self, "Basarili", f"Zimmet formu olusturuldu:\n{pdf_path}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"PDF olusturma hatasi:\n{e}")
