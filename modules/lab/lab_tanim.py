# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Laboratuvar Tanımları
Banyo Tipleri ve Pozisyon Tipleri yönetimi
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QSpinBox, QTextEdit, QComboBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QTimer

from components.base_page import BasePage
from core.database import get_db_connection


# ==================== BANYO TİPLERİ ====================
class BanyoTipiDialog(QDialog):
    """Banyo Tipi Ekleme/Düzenleme"""
    
    def __init__(self, theme: dict, tip_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.tip_id = tip_id
        self.data = {}
        
        self.setWindowTitle("Yeni Banyo Tipi" if not tip_id else "Banyo Tipi Düzenle")
        self.setMinimumSize(400, 400)
        
        if tip_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.banyo_tipleri WHERE id = ?", (self.tip_id,))
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
        
        title = QLabel("🧪 " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.kod_input = QLineEdit(self.data.get('kod', ''))
        self.kod_input.setPlaceholderText("Örn: KATAFOREZ, ALKALI_ZN")
        form.addRow("Kod *:", self.kod_input)
        
        self.ad_input = QLineEdit(self.data.get('ad', ''))
        self.ad_input.setPlaceholderText("Örn: Kataforez Banyosu")
        form.addRow("Ad *:", self.ad_input)
        
        self.kategori_combo = QComboBox()
        self.kategori_combo.addItem("Ön İşlem", "ON_ISLEM")
        self.kategori_combo.addItem("Kaplama", "KAPLAMA")
        self.kategori_combo.addItem("Son İşlem", "SON_ISLEM")
        self.kategori_combo.addItem("Yıkama", "YIKAMA")
        self.kategori_combo.addItem("Diğer", "DIGER")
        if self.data.get('kategori'):
            idx = self.kategori_combo.findData(self.data['kategori'])
            if idx >= 0: self.kategori_combo.setCurrentIndex(idx)
        form.addRow("Kategori *:", self.kategori_combo)
        
        # Gereklilik bayrakları
        gerekli_label = QLabel("── Gereklilik Ayarları ──")
        gerekli_label.setStyleSheet(f"color: {self.theme['primary']}; margin-top: 10px;")
        form.addRow("", gerekli_label)
        
        self.kimyasal_check = QComboBox()
        self.kimyasal_check.addItem("Evet", True)
        self.kimyasal_check.addItem("Hayır", False)
        self.kimyasal_check.setCurrentIndex(0 if self.data.get('kimyasal_gerekli_mi', True) else 1)
        form.addRow("Kimyasal Gerekli:", self.kimyasal_check)
        
        self.sicaklik_check = QComboBox()
        self.sicaklik_check.addItem("Evet", True)
        self.sicaklik_check.addItem("Hayır", False)
        self.sicaklik_check.setCurrentIndex(0 if self.data.get('sicaklik_gerekli_mi', True) else 1)
        form.addRow("Sıcaklık Gerekli:", self.sicaklik_check)
        
        self.ph_check = QComboBox()
        self.ph_check.addItem("Evet", True)
        self.ph_check.addItem("Hayır", False)
        self.ph_check.setCurrentIndex(0 if self.data.get('ph_gerekli_mi', True) else 1)
        form.addRow("pH Gerekli:", self.ph_check)
        
        self.akim_check = QComboBox()
        self.akim_check.addItem("Evet", True)
        self.akim_check.addItem("Hayır", False)
        self.akim_check.setCurrentIndex(0 if self.data.get('akim_gerekli_mi', False) else 1)
        form.addRow("Akım Gerekli:", self.akim_check)
        
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
            
            params = (kod, ad, self.kategori_combo.currentData(),
                     self.kimyasal_check.currentData(), self.sicaklik_check.currentData(),
                     self.ph_check.currentData(), self.akim_check.currentData(),
                     self.aktif_combo.currentData())
            
            if self.tip_id:
                cursor.execute("""UPDATE tanim.banyo_tipleri SET kod=?, ad=?, kategori=?,
                    kimyasal_gerekli_mi=?, sicaklik_gerekli_mi=?, ph_gerekli_mi=?, akim_gerekli_mi=?,
                    aktif_mi=? WHERE id=?""", params + (self.tip_id,))
            else:
                cursor.execute("""INSERT INTO tanim.banyo_tipleri (kod, ad, kategori,
                    kimyasal_gerekli_mi, sicaklik_gerekli_mi, ph_gerekli_mi, akim_gerekli_mi, aktif_mi)
                    VALUES (?,?,?,?,?,?,?,?)""", params)
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ==================== POZİSYON TİPLERİ ====================
class PozisyonTipiDialog(QDialog):
    """Pozisyon Tipi Ekleme/Düzenleme"""
    
    def __init__(self, theme: dict, tip_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.tip_id = tip_id
        self.data = {}
        
        self.setWindowTitle("Yeni Pozisyon Tipi" if not tip_id else "Pozisyon Tipi Düzenle")
        self.setMinimumSize(400, 350)
        
        if tip_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.pozisyon_tipleri WHERE id = ?", (self.tip_id,))
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
        
        title = QLabel("📍 " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.kod_input = QLineEdit(self.data.get('kod', ''))
        self.kod_input.setPlaceholderText("Örn: BANYO, FIRIN, KURUTMA")
        form.addRow("Kod *:", self.kod_input)
        
        self.ad_input = QLineEdit(self.data.get('ad', ''))
        self.ad_input.setPlaceholderText("Örn: Banyo Pozisyonu")
        form.addRow("Ad *:", self.ad_input)
        
        self.ikon_input = QLineEdit(self.data.get('ikon', '') or '')
        self.ikon_input.setPlaceholderText("Örn: 🧪 veya icon adı")
        form.addRow("İkon:", self.ikon_input)
        
        self.renk_input = QLineEdit(self.data.get('renk_kodu', '') or '')
        self.renk_input.setPlaceholderText("Örn: #3B82F6")
        form.addRow("Renk Kodu:", self.renk_input)
        
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
            
            params = (kod, ad, self.ikon_input.text().strip() or None,
                     self.renk_input.text().strip() or None,
                     self.aktif_combo.currentData())
            
            if self.tip_id:
                cursor.execute("""UPDATE tanim.pozisyon_tipleri SET kod=?, ad=?, ikon=?, renk_kodu=?, aktif_mi=?
                    WHERE id=?""", params + (self.tip_id,))
            else:
                cursor.execute("""INSERT INTO tanim.pozisyon_tipleri (kod, ad, ikon, renk_kodu, aktif_mi)
                    VALUES (?,?,?,?,?)""", params)
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ==================== ANA SAYFA ====================
class LabTanimPage(BasePage):
    """Laboratuvar Tanımları Ana Sayfası"""
    
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
        title = QLabel("⚗️ Laboratuvar Tanımları")
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
        
        self.tabs.addTab(self._create_banyo_tipleri_tab(), "🧪 Banyo Tipleri")
        self.tabs.addTab(self._create_pozisyon_tipleri_tab(), "📍 Pozisyon Tipleri")
        self.tabs.currentChanged.connect(self._on_tab_change)
        
        layout.addWidget(self.tabs, 1)
    
    def _create_banyo_tipleri_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        toolbar = QHBoxLayout()
        self.banyo_search = QLineEdit()
        self.banyo_search.setPlaceholderText("🔍 Ara...")
        self.banyo_search.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']};")
        self.banyo_search.setMaximumWidth(250)
        self.banyo_search.returnPressed.connect(self._load_banyo_tipleri)
        toolbar.addWidget(self.banyo_search)
        
        self.banyo_kategori_combo = QComboBox()
        self.banyo_kategori_combo.addItem("Tüm Kategoriler", None)
        self.banyo_kategori_combo.addItem("Ön İşlem", "ON_ISLEM")
        self.banyo_kategori_combo.addItem("Kaplama", "KAPLAMA")
        self.banyo_kategori_combo.addItem("Son İşlem", "SON_ISLEM")
        self.banyo_kategori_combo.addItem("Yıkama", "YIKAMA")
        self.banyo_kategori_combo.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']}; min-width: 120px;")
        self.banyo_kategori_combo.currentIndexChanged.connect(self._load_banyo_tipleri)
        toolbar.addWidget(self.banyo_kategori_combo)
        
        toolbar.addStretch()
        
        add_btn = QPushButton("➕ Yeni Banyo Tipi")
        add_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        add_btn.clicked.connect(self._add_banyo_tipi)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.banyo_table = QTableWidget()
        self.banyo_table.setColumnCount(6)
        self.banyo_table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Kategori", "Durum", "İşlem"])
        self.banyo_table.setColumnWidth(5, 170)
        self.banyo_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.banyo_table.setStyleSheet(self._table_style())
        self.banyo_table.verticalHeader().setVisible(False)
        self.banyo_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.banyo_table, 1)
        
        return widget
    
    def _create_pozisyon_tipleri_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        toolbar = QHBoxLayout()
        self.poz_search = QLineEdit()
        self.poz_search.setPlaceholderText("🔍 Ara...")
        self.poz_search.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']};")
        self.poz_search.setMaximumWidth(250)
        self.poz_search.returnPressed.connect(self._load_pozisyon_tipleri)
        toolbar.addWidget(self.poz_search)
        toolbar.addStretch()
        
        add_btn = QPushButton("➕ Yeni Pozisyon Tipi")
        add_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        add_btn.clicked.connect(self._add_pozisyon_tipi)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.poz_table = QTableWidget()
        self.poz_table.setColumnCount(5)
        self.poz_table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Durum", "İşlem"])
        self.poz_table.setColumnWidth(4, 170)
        self.poz_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.poz_table.setStyleSheet(self._table_style())
        self.poz_table.verticalHeader().setVisible(False)
        self.poz_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.poz_table, 1)
        
        return widget
    
    def _load_all(self):
        self._load_banyo_tipleri()
        self._load_pozisyon_tipleri()
    
    def _on_tab_change(self, idx):
        if idx == 0:
            self._load_banyo_tipleri()
        elif idx == 1:
            self._load_pozisyon_tipleri()
    
    def _load_banyo_tipleri(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = "SELECT id, kod, ad, kategori, aktif_mi FROM tanim.banyo_tipleri WHERE 1=1"
            params = []
            
            search = self.banyo_search.text().strip()
            if search:
                sql += " AND (kod LIKE ? OR ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            
            kategori = self.banyo_kategori_combo.currentData()
            if kategori:
                sql += " AND kategori=?"
                params.append(kategori)
            
            sql += " ORDER BY kod"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            kategori_map = {"ON_ISLEM": "Ön İşlem", "KAPLAMA": "Kaplama", "SON_ISLEM": "Son İşlem", "YIKAMA": "Yıkama", "DIGER": "Diğer"}
            
            self.banyo_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.banyo_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.banyo_table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.banyo_table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.banyo_table.setItem(i, 3, QTableWidgetItem(kategori_map.get(row[3], row[3] or '')))
                
                durum = QTableWidgetItem("✓" if row[4] else "✗")
                durum.setForeground(Qt.green if row[4] else Qt.red)
                self.banyo_table.setItem(i, 4, durum)
                
                widget = self.create_action_buttons([
                    ("✏️", "Duzenle", lambda checked, rid=row[0]: self._edit_banyo_tipi(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_banyo_tipi(rid), "delete"),
                ])
                self.banyo_table.setCellWidget(i, 5, widget)
                self.banyo_table.setRowHeight(i, 42)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _load_pozisyon_tipleri(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = "SELECT id, kod, ad, aktif_mi FROM tanim.pozisyon_tipleri WHERE 1=1"
            params = []
            
            search = self.poz_search.text().strip()
            if search:
                sql += " AND (kod LIKE ? OR ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            
            sql += " ORDER BY kod"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.poz_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.poz_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.poz_table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.poz_table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                
                durum = QTableWidgetItem("✓" if row[3] else "✗")
                durum.setForeground(Qt.green if row[3] else Qt.red)
                self.poz_table.setItem(i, 3, durum)
                
                widget = self.create_action_buttons([
                    ("✏️", "Duzenle", lambda checked, rid=row[0]: self._edit_pozisyon_tipi(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_pozisyon_tipi(rid), "delete"),
                ])
                self.poz_table.setCellWidget(i, 4, widget)
                self.poz_table.setRowHeight(i, 42)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _add_banyo_tipi(self):
        dlg = BanyoTipiDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_banyo_tipleri()
    
    def _edit_banyo_tipi(self, tid):
        dlg = BanyoTipiDialog(self.theme, tid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_banyo_tipleri()
    
    def _delete_banyo_tipi(self, tid):
        if QMessageBox.question(self, "Onay", "Bu banyo tipini silmek istediğinize emin misiniz?") == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM uretim.banyo_tanimlari WHERE banyo_tipi_id=?", (tid,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu tipe bağlı banyolar var!")
                    conn.close()
                    return
                cursor.execute("DELETE FROM tanim.banyo_tipleri WHERE id=?", (tid,))
                conn.commit()
                conn.close()
                self._load_banyo_tipleri()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _add_pozisyon_tipi(self):
        dlg = PozisyonTipiDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_pozisyon_tipleri()
    
    def _edit_pozisyon_tipi(self, tid):
        dlg = PozisyonTipiDialog(self.theme, tid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_pozisyon_tipleri()
    
    def _delete_pozisyon_tipi(self, tid):
        if QMessageBox.question(self, "Onay", "Bu pozisyon tipini silmek istediğinize emin misiniz?") == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tanim.hat_pozisyonlar WHERE pozisyon_tipi_id=?", (tid,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu tipe bağlı pozisyonlar var!")
                    conn.close()
                    return
                cursor.execute("DELETE FROM tanim.pozisyon_tipleri WHERE id=?", (tid,))
                conn.commit()
                conn.close()
                self._load_pozisyon_tipleri()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _table_style(self):
        return f"""
            QTableWidget {{ background: {self.theme['bg_card_solid']}; border: 1px solid {self.theme['border']}; border-radius: 8px; gridline-color: {self.theme['border']}; color: {self.theme['text']}; }}
            QTableWidget::item {{ padding: 6px; }}
            QTableWidget::item:selected {{ background: {self.theme['primary']}; }}
            QHeaderView::section {{ background: {self.theme['bg_main']}; color: {self.theme['text']}; padding: 8px; border: none; border-bottom: 2px solid {self.theme['primary']}; font-weight: bold; }}
        """
