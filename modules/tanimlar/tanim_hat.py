# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Hat Tanımları Sayfası
Hat Bölümleri, Üretim Hatları, Hat Pozisyonları, Robotlar
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QSpinBox, QDoubleSpinBox, QTextEdit, QComboBox, QTabWidget,
    QWidget, QGridLayout, QColorDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


# ==================== HAT BÖLÜMLERİ ====================
class HatBolumDialog(QDialog):
    """Hat Bölümü Ekleme/Düzenleme"""
    
    def __init__(self, theme: dict, bolum_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.bolum_id = bolum_id
        self.data = {}
        
        self.setWindowTitle("Yeni Hat Bölümü" if not bolum_id else "Hat Bölümü Düzenle")
        self.setMinimumSize(450, 500)
        
        if bolum_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.hat_bolumleri WHERE id = ?", (self.bolum_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']};
                border-radius: 6px; padding: 8px; color: {self.theme['text']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("🏭 " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.kod_input = QLineEdit(self.data.get('kod', ''))
        self.kod_input.setMaxLength(20)
        form.addRow("Kod *:", self.kod_input)
        
        self.ad_input = QLineEdit(self.data.get('ad', ''))
        self.ad_input.setMaxLength(100)
        form.addRow("Ad *:", self.ad_input)
        
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setMaximumHeight(60)
        self.aciklama_input.setText(self.data.get('aciklama', '') or '')
        form.addRow("Açıklama:", self.aciklama_input)
        
        self.plc_ip_input = QLineEdit(self.data.get('plc_ip_adresi', '') or '')
        form.addRow("PLC IP:", self.plc_ip_input)
        
        rack_slot = QHBoxLayout()
        self.rack_input = QSpinBox()
        self.rack_input.setRange(0, 99)
        self.rack_input.setValue(self.data.get('plc_rack', 0) or 0)
        rack_slot.addWidget(QLabel("Rack:"))
        rack_slot.addWidget(self.rack_input)
        self.slot_input = QSpinBox()
        self.slot_input.setRange(0, 99)
        self.slot_input.setValue(self.data.get('plc_slot', 0) or 0)
        rack_slot.addWidget(QLabel("Slot:"))
        rack_slot.addWidget(self.slot_input)
        rack_slot.addStretch()
        form.addRow("PLC:", rack_slot)
        
        self.sql_kaynak_input = QLineEdit(self.data.get('sql_veri_kaynagi', '') or '')
        form.addRow("SQL Kaynak:", self.sql_kaynak_input)
        
        self.sql_db_input = QLineEdit(self.data.get('sql_veritabani', '') or '')
        form.addRow("SQL Veritabanı:", self.sql_db_input)
        
        self.sira_input = QSpinBox()
        self.sira_input.setRange(0, 999)
        self.sira_input.setValue(self.data.get('sira', 0) or 0)
        form.addRow("Sıra:", self.sira_input)
        
        self.aktif_combo = QComboBox()
        self.aktif_combo.addItem("✓ Aktif", True)
        self.aktif_combo.addItem("✗ Pasif", False)
        self.aktif_combo.setCurrentIndex(0 if self.data.get('aktif_mi', True) else 1)
        form.addRow("Durum:", self.aktif_combo)
        
        layout.addLayout(form)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _save(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            params = (kod, ad, self.aciklama_input.toPlainText().strip() or None,
                     self.plc_ip_input.text().strip() or None, self.rack_input.value(),
                     self.slot_input.value(), self.sql_kaynak_input.text().strip() or None,
                     self.sql_db_input.text().strip() or None, self.sira_input.value(),
                     self.aktif_combo.currentData())
            
            if self.bolum_id:
                cursor.execute("""UPDATE tanim.hat_bolumleri SET kod=?, ad=?, aciklama=?,
                    plc_ip_adresi=?, plc_rack=?, plc_slot=?, sql_veri_kaynagi=?, sql_veritabani=?,
                    sira=?, aktif_mi=?, guncelleme_tarihi=GETDATE() WHERE id=?""", params + (self.bolum_id,))
            else:
                cursor.execute("""INSERT INTO tanim.hat_bolumleri (kod, ad, aciklama, plc_ip_adresi,
                    plc_rack, plc_slot, sql_veri_kaynagi, sql_veritabani, sira, aktif_mi)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""", params)
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ==================== ÜRETİM HATLARI ====================
class UretimHatDialog(QDialog):
    """Üretim Hattı Ekleme/Düzenleme"""
    
    def __init__(self, theme: dict, hat_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.hat_id = hat_id
        self.data = {}
        self.selected_color = "#3B82F6"
        
        self.setWindowTitle("Yeni Üretim Hattı" if not hat_id else "Üretim Hattı Düzenle")
        self.setMinimumSize(500, 600)
        
        if hat_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.uretim_hatlari WHERE id = ?", (self.hat_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
                if self.data.get('renk_kodu'):
                    self.selected_color = self.data['renk_kodu']
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']};
                border-radius: 6px; padding: 8px; color: {self.theme['text']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("🔧 " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.bolum_combo = QComboBox()
        self.bolum_combo.addItem("-- Seçiniz --", None)
        self._load_bolumler()
        form.addRow("Hat Bölümü:", self.bolum_combo)
        
        self.kod_input = QLineEdit(self.data.get('kod', ''))
        form.addRow("Kod *:", self.kod_input)
        
        self.ad_input = QLineEdit(self.data.get('ad', ''))
        form.addRow("Ad *:", self.ad_input)
        
        self.kisa_ad_input = QLineEdit(self.data.get('kisa_ad', '') or '')
        form.addRow("Kısa Ad:", self.kisa_ad_input)
        
        self.kaplama_combo = QComboBox()
        self.kaplama_combo.addItem("-- Seçiniz --", None)
        self._load_kaplama_turleri()
        form.addRow("Kaplama Türü:", self.kaplama_combo)
        
        self.hat_tipi_combo = QComboBox()
        for tip, kod in [("Ön İşlem", "ON_ISLEM"), ("Kaplama", "KAPLAMA"), ("Kurutma", "KURUTMA"), ("Fırın", "FIRIN")]:
            self.hat_tipi_combo.addItem(tip, kod)
        idx = self.hat_tipi_combo.findData(self.data.get('hat_tipi', 'KAPLAMA'))
        if idx >= 0: self.hat_tipi_combo.setCurrentIndex(idx)
        form.addRow("Hat Tipi *:", self.hat_tipi_combo)
        
        self.sira_input = QSpinBox()
        self.sira_input.setRange(0, 999)
        self.sira_input.setValue(self.data.get('sira_no', 0) or 0)
        form.addRow("Sıra No:", self.sira_input)
        
        self.robot_input = QSpinBox()
        self.robot_input.setRange(0, 50)
        self.robot_input.setValue(self.data.get('robot_sayisi', 0) or 0)
        form.addRow("Robot Sayısı:", self.robot_input)
        
        self.pozisyon_input = QSpinBox()
        self.pozisyon_input.setRange(0, 500)
        self.pozisyon_input.setValue(self.data.get('toplam_pozisyon', 0) or 0)
        form.addRow("Toplam Pozisyon:", self.pozisyon_input)
        
        self.devir_input = QSpinBox()
        self.devir_input.setRange(0, 9999)
        self.devir_input.setSuffix(" dk")
        self.devir_input.setValue(self.data.get('devir_suresi_dk', 0) or 0)
        form.addRow("Devir Süresi:", self.devir_input)
        
        self.kapasite_input = QDoubleSpinBox()
        self.kapasite_input.setRange(0, 99999)
        self.kapasite_input.setDecimals(2)
        self.kapasite_input.setSuffix(" m²/saat")
        self.kapasite_input.setValue(self.data.get('kapasite_saat_m2', 0) or 0)
        form.addRow("Kapasite:", self.kapasite_input)
        
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(40, 30)
        self.color_btn.setStyleSheet(f"background: {self.selected_color}; border-radius: 4px;")
        self.color_btn.clicked.connect(self._pick_color)
        color_layout.addWidget(self.color_btn)
        self.color_label = QLabel(self.selected_color)
        color_layout.addWidget(self.color_label)
        color_layout.addStretch()
        form.addRow("Renk:", color_layout)
        
        self.aktif_combo = QComboBox()
        self.aktif_combo.addItem("✓ Aktif", True)
        self.aktif_combo.addItem("✗ Pasif", False)
        self.aktif_combo.setCurrentIndex(0 if self.data.get('aktif_mi', True) else 1)
        form.addRow("Durum:", self.aktif_combo)
        
        layout.addLayout(form)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def _load_bolumler(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.hat_bolumleri WHERE aktif_mi=1 ORDER BY sira, kod")
            for row in cursor.fetchall():
                self.bolum_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
            if self.data.get('hat_bolum_id'):
                idx = self.bolum_combo.findData(self.data['hat_bolum_id'])
                if idx >= 0: self.bolum_combo.setCurrentIndex(idx)
        except Exception: pass
    
    def _load_kaplama_turleri(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.kaplama_turleri WHERE aktif_mi=1 ORDER BY sira, kod")
            for row in cursor.fetchall():
                self.kaplama_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
            if self.data.get('kaplama_turu_id'):
                idx = self.kaplama_combo.findData(self.data['kaplama_turu_id'])
                if idx >= 0: self.kaplama_combo.setCurrentIndex(idx)
        except Exception: pass
    
    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self)
        if color.isValid():
            self.selected_color = color.name()
            self.color_btn.setStyleSheet(f"background: {self.selected_color}; border-radius: 4px;")
            self.color_label.setText(self.selected_color)
    
    def _save(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            params = (self.bolum_combo.currentData(), kod, ad, self.kisa_ad_input.text().strip() or None,
                     self.kaplama_combo.currentData(), self.hat_tipi_combo.currentData(),
                     self.sira_input.value(), self.robot_input.value(), self.pozisyon_input.value(),
                     self.devir_input.value(), self.kapasite_input.value(), self.selected_color,
                     self.aktif_combo.currentData())
            
            if self.hat_id:
                cursor.execute("""UPDATE tanim.uretim_hatlari SET hat_bolum_id=?, kod=?, ad=?, kisa_ad=?,
                    kaplama_turu_id=?, hat_tipi=?, sira_no=?, robot_sayisi=?, toplam_pozisyon=?,
                    devir_suresi_dk=?, kapasite_saat_m2=?, renk_kodu=?, aktif_mi=?, guncelleme_tarihi=GETDATE()
                    WHERE id=?""", params + (self.hat_id,))
            else:
                cursor.execute("""INSERT INTO tanim.uretim_hatlari (hat_bolum_id, kod, ad, kisa_ad,
                    kaplama_turu_id, hat_tipi, sira_no, robot_sayisi, toplam_pozisyon, devir_suresi_dk,
                    kapasite_saat_m2, renk_kodu, aktif_mi) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", params)
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ==================== HAT POZİSYONLARI ====================
class HatPozisyonDialog(QDialog):
    """Hat Pozisyonu Ekleme/Düzenleme"""
    
    def __init__(self, theme: dict, poz_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.poz_id = poz_id
        self.data = {}
        
        self.setWindowTitle("Yeni Pozisyon" if not poz_id else "Pozisyon Düzenle")
        self.setMinimumSize(600, 700)
        
        if poz_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.hat_pozisyonlar WHERE id = ?", (self.poz_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']};
                border-radius: 6px; padding: 6px; color: {self.theme['text']};
            }}
            QTabWidget::pane {{ border: 1px solid {self.theme['border']}; background: {self.theme['bg_card_solid']}; }}
            QTabBar::tab {{ background: {self.theme['bg_input']}; padding: 8px 16px; color: {self.theme['text']}; }}
            QTabBar::tab:selected {{ background: {self.theme['bg_card_solid']}; border-bottom: 2px solid {self.theme['primary']}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("📍 " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        tabs = QTabWidget()
        tabs.addTab(self._create_genel_tab(), "Genel")
        tabs.addTab(self._create_parametre_tab(), "Parametreler")
        tabs.addTab(self._create_plc_tab(), "PLC")
        layout.addWidget(tabs, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def _create_genel_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)
        
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("-- Seçiniz --", None)
        self._load_hatlar()
        form.addRow("Üretim Hattı *:", self.hat_combo)
        
        self.pozisyon_no_input = QSpinBox()
        self.pozisyon_no_input.setRange(1, 9999)
        self.pozisyon_no_input.setValue(self.data.get('pozisyon_no', 1) or 1)
        form.addRow("Pozisyon No *:", self.pozisyon_no_input)
        
        self.sensor_no_input = QSpinBox()
        self.sensor_no_input.setRange(0, 9999)
        self.sensor_no_input.setValue(self.data.get('sensor_no', 0) or 0)
        form.addRow("Sensör No:", self.sensor_no_input)
        
        self.plc_poz_input = QLineEdit(self.data.get('plc_pozisyon_adi', '') or '')
        form.addRow("PLC Poz. Adı:", self.plc_poz_input)
        
        self.ad_input = QLineEdit(self.data.get('ad', ''))
        form.addRow("Ad *:", self.ad_input)
        
        self.kisa_ad_input = QLineEdit(self.data.get('kisa_ad', '') or '')
        form.addRow("Kısa Ad:", self.kisa_ad_input)
        
        self.poz_tipi_combo = QComboBox()
        self._load_pozisyon_tipleri()
        form.addRow("Pozisyon Tipi *:", self.poz_tipi_combo)
        
        self.banyo_tipi_combo = QComboBox()
        self.banyo_tipi_combo.addItem("-- Seçiniz --", None)
        self._load_banyo_tipleri()
        form.addRow("Banyo Tipi:", self.banyo_tipi_combo)
        
        self.tank_tipi_combo = QComboBox()
        self.tank_tipi_combo.addItem("-- Seçiniz --", None)
        self.tank_tipi_combo.addItem("Tekli", "TEKLI")
        self.tank_tipi_combo.addItem("Çiftli", "CIFTLI")
        if self.data.get('tank_tipi'):
            idx = self.tank_tipi_combo.findData(self.data['tank_tipi'])
            if idx >= 0: self.tank_tipi_combo.setCurrentIndex(idx)
        form.addRow("Tank Tipi:", self.tank_tipi_combo)
        
        self.sira_input = QSpinBox()
        self.sira_input.setRange(1, 9999)
        self.sira_input.setValue(self.data.get('sira_no', 1) or 1)
        form.addRow("Sıra No *:", self.sira_input)
        
        self.hacim_input = QDoubleSpinBox()
        self.hacim_input.setRange(0, 999999)
        self.hacim_input.setSuffix(" lt")
        self.hacim_input.setValue(self.data.get('hacim_lt', 0) or 0)
        form.addRow("Hacim:", self.hacim_input)
        
        self.bekleme_input = QSpinBox()
        self.bekleme_input.setRange(0, 99999)
        self.bekleme_input.setSuffix(" sn")
        self.bekleme_input.setValue(self.data.get('bekleme_suresi_sn', 0) or 0)
        form.addRow("Bekleme Süresi:", self.bekleme_input)
        
        self.notlar_input = QTextEdit()
        self.notlar_input.setMaximumHeight(50)
        self.notlar_input.setText(self.data.get('notlar', '') or '')
        form.addRow("Notlar:", self.notlar_input)
        
        self.aktif_combo = QComboBox()
        self.aktif_combo.addItem("✓ Aktif", True)
        self.aktif_combo.addItem("✗ Pasif", False)
        self.aktif_combo.setCurrentIndex(0 if self.data.get('aktif_mi', True) else 1)
        form.addRow("Durum:", self.aktif_combo)
        
        return widget
    
    def _create_parametre_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Sıcaklık
        sic_frame = QFrame()
        sic_frame.setStyleSheet(f"background: {self.theme['bg_card_solid']}; border: 1px solid {self.theme['border']}; border-radius: 8px;")
        sic_layout = QVBoxLayout(sic_frame)
        sic_layout.addWidget(QLabel("🌡️ Sıcaklık (°C)"))
        sic_grid = QHBoxLayout()
        self.sic_min = QDoubleSpinBox(); self.sic_min.setRange(0, 999); self.sic_min.setValue(self.data.get('sicaklik_min', 0) or 0)
        self.sic_hedef = QDoubleSpinBox(); self.sic_hedef.setRange(0, 999); self.sic_hedef.setValue(self.data.get('sicaklik_hedef', 0) or 0)
        self.sic_max = QDoubleSpinBox(); self.sic_max.setRange(0, 999); self.sic_max.setValue(self.data.get('sicaklik_max', 0) or 0)
        sic_grid.addWidget(QLabel("Min:")); sic_grid.addWidget(self.sic_min)
        sic_grid.addWidget(QLabel("Hedef:")); sic_grid.addWidget(self.sic_hedef)
        sic_grid.addWidget(QLabel("Max:")); sic_grid.addWidget(self.sic_max)
        sic_layout.addLayout(sic_grid)
        layout.addWidget(sic_frame)
        
        # pH
        ph_frame = QFrame()
        ph_frame.setStyleSheet(f"background: {self.theme['bg_card_solid']}; border: 1px solid {self.theme['border']}; border-radius: 8px;")
        ph_layout = QVBoxLayout(ph_frame)
        ph_layout.addWidget(QLabel("🧪 pH"))
        ph_grid = QHBoxLayout()
        self.ph_min = QDoubleSpinBox(); self.ph_min.setRange(0, 14); self.ph_min.setDecimals(2); self.ph_min.setValue(self.data.get('ph_min', 0) or 0)
        self.ph_hedef = QDoubleSpinBox(); self.ph_hedef.setRange(0, 14); self.ph_hedef.setDecimals(2); self.ph_hedef.setValue(self.data.get('ph_hedef', 0) or 0)
        self.ph_max = QDoubleSpinBox(); self.ph_max.setRange(0, 14); self.ph_max.setDecimals(2); self.ph_max.setValue(self.data.get('ph_max', 0) or 0)
        ph_grid.addWidget(QLabel("Min:")); ph_grid.addWidget(self.ph_min)
        ph_grid.addWidget(QLabel("Hedef:")); ph_grid.addWidget(self.ph_hedef)
        ph_grid.addWidget(QLabel("Max:")); ph_grid.addWidget(self.ph_max)
        ph_layout.addLayout(ph_grid)
        layout.addWidget(ph_frame)
        
        # Akım
        akim_frame = QFrame()
        akim_frame.setStyleSheet(f"background: {self.theme['bg_card_solid']}; border: 1px solid {self.theme['border']}; border-radius: 8px;")
        akim_layout = QVBoxLayout(akim_frame)
        akim_layout.addWidget(QLabel("⚡ Akım (A)"))
        akim_grid = QHBoxLayout()
        self.akim_min = QDoubleSpinBox(); self.akim_min.setRange(0, 9999); self.akim_min.setValue(self.data.get('akim_min', 0) or 0)
        self.akim_hedef = QDoubleSpinBox(); self.akim_hedef.setRange(0, 9999); self.akim_hedef.setValue(self.data.get('akim_hedef', 0) or 0)
        self.akim_max = QDoubleSpinBox(); self.akim_max.setRange(0, 9999); self.akim_max.setValue(self.data.get('akim_max', 0) or 0)
        akim_grid.addWidget(QLabel("Min:")); akim_grid.addWidget(self.akim_min)
        akim_grid.addWidget(QLabel("Hedef:")); akim_grid.addWidget(self.akim_hedef)
        akim_grid.addWidget(QLabel("Max:")); akim_grid.addWidget(self.akim_max)
        akim_layout.addLayout(akim_grid)
        layout.addWidget(akim_frame)
        
        layout.addStretch()
        return widget
    
    def _create_plc_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(16, 16, 16, 16)
        
        self.sql_tablo_input = QLineEdit(self.data.get('sql_tablo_adi', '') or '')
        form.addRow("SQL Tablo:", self.sql_tablo_input)
        
        self.sql_sic_input = QLineEdit(self.data.get('sql_sicaklik_kolon', '') or '')
        form.addRow("Sıcaklık Kolonu:", self.sql_sic_input)
        
        self.sql_ph_input = QLineEdit(self.data.get('sql_ph_kolon', '') or '')
        form.addRow("pH Kolonu:", self.sql_ph_input)
        
        self.sql_akim_input = QLineEdit(self.data.get('sql_akim_kolon', '') or '')
        form.addRow("Akım Kolonu:", self.sql_akim_input)
        
        self.sql_durum_input = QLineEdit(self.data.get('sql_durum_kolon', '') or '')
        form.addRow("Durum Kolonu:", self.sql_durum_input)
        
        return widget
    
    def _load_hatlar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.uretim_hatlari WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no, kod")
            for row in cursor.fetchall():
                self.hat_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
            if self.data.get('hat_id'):
                idx = self.hat_combo.findData(self.data['hat_id'])
                if idx >= 0: self.hat_combo.setCurrentIndex(idx)
        except Exception: pass
    
    def _load_pozisyon_tipleri(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM tanim.pozisyon_tipleri WHERE aktif_mi=1 ORDER BY ad")
            for row in cursor.fetchall():
                self.poz_tipi_combo.addItem(row[1], row[0])
            conn.close()
            if self.data.get('pozisyon_tipi_id'):
                idx = self.poz_tipi_combo.findData(self.data['pozisyon_tipi_id'])
                if idx >= 0: self.poz_tipi_combo.setCurrentIndex(idx)
        except Exception: pass
    
    def _load_banyo_tipleri(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad, kategori FROM tanim.banyo_tipleri WHERE aktif_mi=1 ORDER BY kategori, ad")
            for row in cursor.fetchall():
                self.banyo_tipi_combo.addItem(f"{row[1]} ({row[2]})", row[0])
            conn.close()
            if self.data.get('banyo_tipi_id'):
                idx = self.banyo_tipi_combo.findData(self.data['banyo_tipi_id'])
                if idx >= 0: self.banyo_tipi_combo.setCurrentIndex(idx)
        except Exception: pass
    
    def _save(self):
        hat_id = self.hat_combo.currentData()
        ad = self.ad_input.text().strip()
        poz_tipi = self.poz_tipi_combo.currentData()
        
        if not hat_id or not ad or not poz_tipi:
            QMessageBox.warning(self, "Uyarı", "Hat, Ad ve Pozisyon Tipi zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            params = (hat_id, self.pozisyon_no_input.value(), self.sensor_no_input.value() or None,
                     self.plc_poz_input.text().strip() or None, ad, self.kisa_ad_input.text().strip() or None,
                     poz_tipi, self.banyo_tipi_combo.currentData(), self.tank_tipi_combo.currentData(),
                     None, self.sira_input.value(), self.hacim_input.value() or None,
                     self.sic_min.value() or None, self.sic_max.value() or None, self.sic_hedef.value() or None,
                     self.ph_min.value() or None, self.ph_max.value() or None, self.ph_hedef.value() or None,
                     self.akim_min.value() or None, self.akim_max.value() or None, self.akim_hedef.value() or None,
                     self.bekleme_input.value() or None, self.sql_tablo_input.text().strip() or None,
                     self.sql_sic_input.text().strip() or None, self.sql_ph_input.text().strip() or None,
                     self.sql_akim_input.text().strip() or None, self.sql_durum_input.text().strip() or None,
                     self.notlar_input.toPlainText().strip() or None, self.aktif_combo.currentData())
            
            if self.poz_id:
                cursor.execute("""UPDATE tanim.hat_pozisyonlar SET hat_id=?, pozisyon_no=?, sensor_no=?,
                    plc_pozisyon_adi=?, ad=?, kisa_ad=?, pozisyon_tipi_id=?, banyo_tipi_id=?, tank_tipi=?,
                    gecis_tipi=?, sira_no=?, hacim_lt=?, sicaklik_min=?, sicaklik_max=?, sicaklik_hedef=?,
                    ph_min=?, ph_max=?, ph_hedef=?, akim_min=?, akim_max=?, akim_hedef=?, bekleme_suresi_sn=?,
                    sql_tablo_adi=?, sql_sicaklik_kolon=?, sql_ph_kolon=?, sql_akim_kolon=?, sql_durum_kolon=?,
                    notlar=?, aktif_mi=?, guncelleme_tarihi=GETDATE() WHERE id=?""", params + (self.poz_id,))
            else:
                cursor.execute("""INSERT INTO tanim.hat_pozisyonlar (hat_id, pozisyon_no, sensor_no,
                    plc_pozisyon_adi, ad, kisa_ad, pozisyon_tipi_id, banyo_tipi_id, tank_tipi, gecis_tipi,
                    sira_no, hacim_lt, sicaklik_min, sicaklik_max, sicaklik_hedef, ph_min, ph_max, ph_hedef,
                    akim_min, akim_max, akim_hedef, bekleme_suresi_sn, sql_tablo_adi, sql_sicaklik_kolon,
                    sql_ph_kolon, sql_akim_kolon, sql_durum_kolon, notlar, aktif_mi)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", params)
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ==================== ANA SAYFA ====================
class TanimHatPage(BasePage):
    """Hat Tanımları Ana Sayfası - Tabbed"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_all)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("⚙️ Hat Tanımları")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 24px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {self.theme['border']}; background: {self.theme['bg_card_solid']}; border-radius: 8px; }}
            QTabBar::tab {{ background: {self.theme['bg_input']}; color: {self.theme['text']}; padding: 10px 20px; margin-right: 2px; border-radius: 4px 4px 0 0; }}
            QTabBar::tab:selected {{ background: {self.theme['bg_card_solid']}; border-bottom: 2px solid {self.theme['primary']}; }}
        """)
        
        self.tabs.addTab(self._create_bolumler_tab(), "🏭 Hat Bölümleri")
        self.tabs.addTab(self._create_hatlar_tab(), "🔧 Üretim Hatları")
        self.tabs.addTab(self._create_pozisyonlar_tab(), "📍 Pozisyonlar")
        self.tabs.currentChanged.connect(self._on_tab_change)
        
        layout.addWidget(self.tabs, 1)
    
    def _create_bolumler_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        toolbar = QHBoxLayout()
        self.bolum_search = QLineEdit()
        self.bolum_search.setPlaceholderText("🔍 Ara...")
        self.bolum_search.setStyleSheet(self._input_style())
        self.bolum_search.setMaximumWidth(250)
        self.bolum_search.returnPressed.connect(self._load_bolumler)
        toolbar.addWidget(self.bolum_search)
        toolbar.addStretch()
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self._load_bolumler)
        toolbar.addWidget(refresh_btn)
        
        add_btn = QPushButton("➕ Yeni Bölüm")
        add_btn.setStyleSheet(self._primary_btn_style())
        add_btn.clicked.connect(lambda: self._add_bolum())
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.bolum_table = QTableWidget()
        self.bolum_table.setColumnCount(7)
        self.bolum_table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "PLC IP", "SQL Kaynak", "Durum", "İşlem"])
        self.bolum_table.setColumnWidth(6, 170)
        self.bolum_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.bolum_table.setStyleSheet(self._table_style())
        self.bolum_table.verticalHeader().setVisible(False)
        self.bolum_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.bolum_table, 1)
        
        return widget
    
    def _create_hatlar_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        toolbar = QHBoxLayout()
        self.hat_search = QLineEdit()
        self.hat_search.setPlaceholderText("🔍 Ara...")
        self.hat_search.setStyleSheet(self._input_style())
        self.hat_search.setMaximumWidth(200)
        self.hat_search.returnPressed.connect(self._load_hatlar)
        toolbar.addWidget(self.hat_search)
        
        self.hat_bolum_filter = QComboBox()
        self.hat_bolum_filter.addItem("Tüm Bölümler", None)
        self.hat_bolum_filter.setStyleSheet(self._combo_style())
        self.hat_bolum_filter.currentIndexChanged.connect(self._load_hatlar)
        toolbar.addWidget(self.hat_bolum_filter)
        toolbar.addStretch()
        
        add_btn = QPushButton("➕ Yeni Hat")
        add_btn.setStyleSheet(self._primary_btn_style())
        add_btn.clicked.connect(lambda: self._add_hat())
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.hat_table = QTableWidget()
        self.hat_table.setColumnCount(9)
        self.hat_table.setHorizontalHeaderLabels(["ID", "Bölüm", "Kod", "Ad", "Tip", "Robot", "Pozisyon", "Durum", "İşlem"])
        self.hat_table.setColumnWidth(8, 170)
        self.hat_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.hat_table.setStyleSheet(self._table_style())
        self.hat_table.verticalHeader().setVisible(False)
        self.hat_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.hat_table, 1)
        
        return widget
    
    def _create_pozisyonlar_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        toolbar = QHBoxLayout()
        self.poz_search = QLineEdit()
        self.poz_search.setPlaceholderText("🔍 Ara...")
        self.poz_search.setStyleSheet(self._input_style())
        self.poz_search.setMaximumWidth(200)
        self.poz_search.returnPressed.connect(self._load_pozisyonlar)
        toolbar.addWidget(self.poz_search)
        
        self.poz_hat_filter = QComboBox()
        self.poz_hat_filter.addItem("Tüm Hatlar", None)
        self.poz_hat_filter.setStyleSheet(self._combo_style())
        self.poz_hat_filter.currentIndexChanged.connect(self._load_pozisyonlar)
        toolbar.addWidget(self.poz_hat_filter)
        toolbar.addStretch()
        
        add_btn = QPushButton("➕ Yeni Pozisyon")
        add_btn.setStyleSheet(self._primary_btn_style())
        add_btn.clicked.connect(lambda: self._add_pozisyon())
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.poz_table = QTableWidget()
        self.poz_table.setColumnCount(10)
        self.poz_table.setHorizontalHeaderLabels(["ID", "Hat", "No", "Ad", "Tip", "Banyo", "Hacim", "Sıcaklık", "Durum", "İşlem"])
        self.poz_table.setColumnWidth(9, 170)
        self.poz_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.poz_table.setStyleSheet(self._table_style())
        self.poz_table.verticalHeader().setVisible(False)
        self.poz_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.poz_table, 1)
        
        return widget
    
    def _load_all(self):
        self._load_bolumler()
        self._load_bolum_filter()
        self._load_hat_filter()
    
    def _on_tab_change(self, idx):
        if idx == 0: self._load_bolumler()
        elif idx == 1: self._load_hatlar()
        elif idx == 2: self._load_pozisyonlar()
    
    def _load_bolumler(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            search = self.bolum_search.text().strip()
            sql = "SELECT id, kod, ad, plc_ip_adresi, sql_veri_kaynagi, aktif_mi FROM tanim.hat_bolumleri WHERE 1=1"
            params = []
            if search:
                sql += " AND (kod LIKE ? OR ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            sql += " ORDER BY sira, kod"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.bolum_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.bolum_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.bolum_table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.bolum_table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.bolum_table.setItem(i, 3, QTableWidgetItem(row[3] or '-'))
                self.bolum_table.setItem(i, 4, QTableWidgetItem(row[4] or '-'))
                
                durum = QTableWidgetItem("✓" if row[5] else "✗")
                durum.setForeground(Qt.green if row[5] else Qt.red)
                self.bolum_table.setItem(i, 5, durum)
                
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, rid=row[0]: self._edit_bolum(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_bolum(rid), "delete"),
                ])
                self.bolum_table.setCellWidget(i, 6, widget)
                self.bolum_table.setRowHeight(i, 42)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _load_hatlar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            search = self.hat_search.text().strip()
            bolum_id = self.hat_bolum_filter.currentData()
            
            sql = """SELECT h.id, b.kod, h.kod, h.ad, h.hat_tipi, h.robot_sayisi, h.toplam_pozisyon, h.aktif_mi
                     FROM tanim.uretim_hatlari h LEFT JOIN tanim.hat_bolumleri b ON h.hat_bolum_id=b.id
                     WHERE h.silindi_mi=0"""
            params = []
            if search:
                sql += " AND (h.kod LIKE ? OR h.ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            if bolum_id:
                sql += " AND h.hat_bolum_id=?"
                params.append(bolum_id)
            sql += " ORDER BY b.sira, h.sira_no"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            tip_map = {'ON_ISLEM': 'Ön İşlem', 'KAPLAMA': 'Kaplama', 'KURUTMA': 'Kurutma', 'FIRIN': 'Fırın'}
            self.hat_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.hat_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.hat_table.setItem(i, 1, QTableWidgetItem(row[1] or '-'))
                self.hat_table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.hat_table.setItem(i, 3, QTableWidgetItem(row[3] or ''))
                self.hat_table.setItem(i, 4, QTableWidgetItem(tip_map.get(row[4], row[4] or '')))
                self.hat_table.setItem(i, 5, QTableWidgetItem(str(row[5] or 0)))
                self.hat_table.setItem(i, 6, QTableWidgetItem(str(row[6] or 0)))
                
                durum = QTableWidgetItem("✓" if row[7] else "✗")
                durum.setForeground(Qt.green if row[7] else Qt.red)
                self.hat_table.setItem(i, 7, durum)
                
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, rid=row[0]: self._edit_hat(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_hat(rid), "delete"),
                ])
                self.hat_table.setCellWidget(i, 8, widget)
                self.hat_table.setRowHeight(i, 42)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _load_pozisyonlar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            search = self.poz_search.text().strip()
            hat_id = self.poz_hat_filter.currentData()
            
            sql = """SELECT p.id, h.kod, p.pozisyon_no, p.ad, pt.ad, bt.ad, p.hacim_lt, p.sicaklik_hedef, p.aktif_mi
                     FROM tanim.hat_pozisyonlar p
                     JOIN tanim.uretim_hatlari h ON p.hat_id=h.id
                     JOIN tanim.pozisyon_tipleri pt ON p.pozisyon_tipi_id=pt.id
                     LEFT JOIN tanim.banyo_tipleri bt ON p.banyo_tipi_id=bt.id
                     WHERE p.silindi_mi=0"""
            params = []
            if search:
                sql += " AND (p.ad LIKE ? OR p.kisa_ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            if hat_id:
                sql += " AND p.hat_id=?"
                params.append(hat_id)
            sql += " ORDER BY h.sira_no, p.sira_no"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.poz_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.poz_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.poz_table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.poz_table.setItem(i, 2, QTableWidgetItem(str(row[2])))
                self.poz_table.setItem(i, 3, QTableWidgetItem(row[3] or ''))
                self.poz_table.setItem(i, 4, QTableWidgetItem(row[4] or ''))
                self.poz_table.setItem(i, 5, QTableWidgetItem(row[5] or '-'))
                self.poz_table.setItem(i, 6, QTableWidgetItem(f"{row[6]:.0f} lt" if row[6] else '-'))
                self.poz_table.setItem(i, 7, QTableWidgetItem(f"{row[7]:.0f}°C" if row[7] else '-'))
                
                durum = QTableWidgetItem("✓" if row[8] else "✗")
                durum.setForeground(Qt.green if row[8] else Qt.red)
                self.poz_table.setItem(i, 8, durum)
                
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, rid=row[0]: self._edit_pozisyon(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_pozisyon(rid), "delete"),
                ])
                self.poz_table.setCellWidget(i, 9, widget)
                self.poz_table.setRowHeight(i, 42)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _load_bolum_filter(self):
        try:
            self.hat_bolum_filter.clear()
            self.hat_bolum_filter.addItem("Tüm Bölümler", None)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod FROM tanim.hat_bolumleri WHERE aktif_mi=1 ORDER BY sira, kod")
            for row in cursor.fetchall():
                self.hat_bolum_filter.addItem(row[1], row[0])
            conn.close()
        except Exception: pass
    
    def _load_hat_filter(self):
        try:
            self.poz_hat_filter.clear()
            self.poz_hat_filter.addItem("Tüm Hatlar", None)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod FROM tanim.uretim_hatlari WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no, kod")
            for row in cursor.fetchall():
                self.poz_hat_filter.addItem(row[1], row[0])
            conn.close()
        except Exception: pass
    
    def _add_bolum(self):
        dlg = HatBolumDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_bolumler()
            self._load_bolum_filter()
    
    def _edit_bolum(self, bid):
        dlg = HatBolumDialog(self.theme, bid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_bolumler()
            self._load_bolum_filter()
    
    def _delete_bolum(self, bid):
        if QMessageBox.question(self, "Onay", "Silmek istediğinize emin misiniz?") == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tanim.uretim_hatlari WHERE hat_bolum_id=?", (bid,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu bölüme bağlı hatlar var!")
                    conn.close()
                    return
                cursor.execute("DELETE FROM tanim.hat_bolumleri WHERE id=?", (bid,))
                conn.commit()
                conn.close()
                self._load_bolumler()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _add_hat(self):
        dlg = UretimHatDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_hatlar()
            self._load_hat_filter()
    
    def _edit_hat(self, hid):
        dlg = UretimHatDialog(self.theme, hid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_hatlar()
    
    def _delete_hat(self, hid):
        if QMessageBox.question(self, "Onay", "Silmek istediğinize emin misiniz?") == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tanim.hat_pozisyonlar WHERE hat_id=? AND silindi_mi=0", (hid,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu hatta bağlı pozisyonlar var!")
                    conn.close()
                    return
                cursor.execute("UPDATE tanim.uretim_hatlari SET silindi_mi=1, silinme_tarihi=GETDATE() WHERE id=?", (hid,))
                conn.commit()
                conn.close()
                self._load_hatlar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _add_pozisyon(self):
        dlg = HatPozisyonDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_pozisyonlar()
    
    def _edit_pozisyon(self, pid):
        dlg = HatPozisyonDialog(self.theme, pid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_pozisyonlar()
    
    def _delete_pozisyon(self, pid):
        if QMessageBox.question(self, "Onay", "Silmek istediğinize emin misiniz?") == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE tanim.hat_pozisyonlar SET silindi_mi=1, silinme_tarihi=GETDATE() WHERE id=?", (pid,))
                conn.commit()
                conn.close()
                self._load_pozisyonlar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _input_style(self):
        return f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']};"
    
    def _combo_style(self):
        return f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']}; min-width: 120px;"
    
    def _primary_btn_style(self):
        return f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold;"
    
    def _table_style(self):
        return f"""
            QTableWidget {{ background: {self.theme['bg_card_solid']}; border: 1px solid {self.theme['border']}; border-radius: 8px; gridline-color: {self.theme['border']}; color: {self.theme['text']}; }}
            QTableWidget::item {{ padding: 6px; }}
            QTableWidget::item:selected {{ background: {self.theme['primary']}; }}
            QHeaderView::section {{ background: {self.theme['bg_main']}; color: {self.theme['text']}; padding: 8px; border: none; border-bottom: 2px solid {self.theme['primary']}; font-weight: bold; }}
        """
