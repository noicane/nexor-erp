# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Depo Tanımları Sayfası
Depo Tipleri, Depolar, Bölümler, Raflar
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QSpinBox, QDoubleSpinBox, QTextEdit, QComboBox, QTabWidget,
    QWidget, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


# ==================== DEPO TİPİ DİALOG ====================
class DepoTipiDialog(QDialog):
    def __init__(self, theme: dict, tip_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.tip_id = tip_id
        self.data = {}
        self.setWindowTitle("Yeni Depo Tipi" if not tip_id else "Depo Tipi Düzenle")
        self.setMinimumSize(400, 350)
        if tip_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.depo_tipleri WHERE id = ?", (self.tip_id,))
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
        
        title = QLabel("🏷️ " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.kod_input = QLineEdit(self.data.get('kod', ''))
        form.addRow("Kod *:", self.kod_input)
        
        self.ad_input = QLineEdit(self.data.get('ad', ''))
        form.addRow("Ad *:", self.ad_input)
        
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setMaximumHeight(60)
        self.aciklama_input.setText(self.data.get('aciklama', '') or '')
        form.addRow("Açıklama:", self.aciklama_input)
        
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
            params = (kod, ad, self.aciklama_input.toPlainText().strip() or None, self.aktif_combo.currentData())
            if self.tip_id:
                cursor.execute("UPDATE tanim.depo_tipleri SET kod=?, ad=?, aciklama=?, aktif_mi=?, guncelleme_tarihi=GETDATE() WHERE id=?", params + (self.tip_id,))
            else:
                cursor.execute("INSERT INTO tanim.depo_tipleri (kod, ad, aciklama, aktif_mi) VALUES (?,?,?,?)", params)
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ==================== DEPO DİALOG ====================
class DepoDialog(QDialog):
    def __init__(self, theme: dict, depo_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.depo_id = depo_id
        self.data = {}
        self.setWindowTitle("Yeni Depo" if not depo_id else "Depo Düzenle")
        self.setMinimumSize(450, 500)
        if depo_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.depolar WHERE id = ?", (self.depo_id,))
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
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']};
                border-radius: 6px; padding: 8px; color: {self.theme['text']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("📦 " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.kod_input = QLineEdit(self.data.get('kod', ''))
        form.addRow("Kod *:", self.kod_input)
        
        self.ad_input = QLineEdit(self.data.get('ad', ''))
        form.addRow("Ad *:", self.ad_input)
        
        self.kisa_ad_input = QLineEdit(self.data.get('kisa_ad', '') or '')
        form.addRow("Kısa Ad:", self.kisa_ad_input)
        
        self.tip_combo = QComboBox()
        self._load_tipler()
        form.addRow("Depo Tipi *:", self.tip_combo)
        
        self.alan_input = QDoubleSpinBox()
        self.alan_input.setRange(0, 999999)
        self.alan_input.setSuffix(" m²")
        self.alan_input.setValue(float(self.data.get('alan_m2') or 0))
        form.addRow("Alan:", self.alan_input)
        
        self.palet_input = QSpinBox()
        self.palet_input.setRange(0, 99999)
        self.palet_input.setValue(int(self.data.get('kapasite_palet') or 0))
        form.addRow("Palet Kapasitesi:", self.palet_input)
        
        self.sira_input = QSpinBox()
        self.sira_input.setRange(0, 999)
        self.sira_input.setValue(int(self.data.get('sira_no') or 0))
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
    
    def _load_tipler(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM tanim.depo_tipleri WHERE aktif_mi=1 ORDER BY ad")
            for row in cursor.fetchall():
                self.tip_combo.addItem(row[1], row[0])
            conn.close()
            if self.data.get('depo_tipi_id'):
                idx = self.tip_combo.findData(self.data['depo_tipi_id'])
                if idx >= 0:
                    self.tip_combo.setCurrentIndex(idx)
        except Exception:
            pass
    
    def _save(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad zorunludur!")
            return
        if self.tip_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Uyarı", "Depo Tipi seçiniz!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            params = (kod, ad, self.kisa_ad_input.text().strip() or None, self.tip_combo.currentData(),
                     self.alan_input.value() or None, self.palet_input.value() or None,
                     self.sira_input.value(), self.aktif_combo.currentData())
            if self.depo_id:
                cursor.execute("""UPDATE tanim.depolar SET kod=?, ad=?, kisa_ad=?, depo_tipi_id=?,
                    alan_m2=?, kapasite_palet=?, sira_no=?, aktif_mi=?, guncelleme_tarihi=GETDATE() WHERE id=?""", params + (self.depo_id,))
            else:
                cursor.execute("""INSERT INTO tanim.depolar (kod, ad, kisa_ad, depo_tipi_id, alan_m2, kapasite_palet, sira_no, aktif_mi)
                    VALUES (?,?,?,?,?,?,?,?)""", params)
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ==================== BÖLÜM DİALOG ====================
class BolumDialog(QDialog):
    def __init__(self, theme: dict, bolum_id: int = None, depo_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.bolum_id = bolum_id
        self.preset_depo_id = depo_id
        self.data = {}
        self.setWindowTitle("Yeni Bölüm" if not bolum_id else "Bölüm Düzenle")
        self.setMinimumSize(400, 400)
        if bolum_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.depo_bolumleri WHERE id = ?", (self.bolum_id,))
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
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']};
                border-radius: 6px; padding: 8px; color: {self.theme['text']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("🗂️ " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.depo_combo = QComboBox()
        self._load_depolar()
        form.addRow("Depo *:", self.depo_combo)
        
        self.kod_input = QLineEdit(self.data.get('kod', ''))
        form.addRow("Kod *:", self.kod_input)
        
        self.ad_input = QLineEdit(self.data.get('ad', ''))
        form.addRow("Ad *:", self.ad_input)
        
        self.kat_input = QSpinBox()
        self.kat_input.setRange(-5, 20)
        self.kat_input.setValue(int(self.data.get('kat_no') or 0))
        form.addRow("Kat No:", self.kat_input)
        
        self.tip_combo = QComboBox()
        self.tip_combo.addItems(["Depolama", "Sevkiyat", "Kabul", "Hazırlık", "Karantina"])
        if self.data.get('bolum_tipi'):
            idx = self.tip_combo.findText(self.data['bolum_tipi'])
            if idx >= 0:
                self.tip_combo.setCurrentIndex(idx)
        form.addRow("Bölüm Tipi:", self.tip_combo)
        
        self.alan_input = QDoubleSpinBox()
        self.alan_input.setRange(0, 99999)
        self.alan_input.setSuffix(" m²")
        self.alan_input.setValue(float(self.data.get('alan_m2') or 0))
        form.addRow("Alan:", self.alan_input)
        
        self.sira_input = QSpinBox()
        self.sira_input.setRange(0, 999)
        self.sira_input.setValue(int(self.data.get('sira_no') or 0))
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
    
    def _load_depolar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.depolar WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no, kod")
            for row in cursor.fetchall():
                self.depo_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
            depo_id = self.data.get('depo_id') or self.preset_depo_id
            if depo_id:
                idx = self.depo_combo.findData(depo_id)
                if idx >= 0:
                    self.depo_combo.setCurrentIndex(idx)
        except Exception:
            pass
    
    def _save(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad zorunludur!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            params = (self.depo_combo.currentData(), kod, ad, self.kat_input.value(),
                     self.tip_combo.currentText(), self.alan_input.value() or None,
                     self.sira_input.value(), self.aktif_combo.currentData())
            if self.bolum_id:
                cursor.execute("""UPDATE tanim.depo_bolumleri SET depo_id=?, kod=?, ad=?, kat_no=?, bolum_tipi=?,
                    alan_m2=?, sira_no=?, aktif_mi=?, guncelleme_tarihi=GETDATE() WHERE id=?""", params + (self.bolum_id,))
            else:
                cursor.execute("""INSERT INTO tanim.depo_bolumleri (depo_id, kod, ad, kat_no, bolum_tipi, alan_m2, sira_no, aktif_mi)
                    VALUES (?,?,?,?,?,?,?,?)""", params)
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ==================== RAF DİALOG ====================
class RafDialog(QDialog):
    def __init__(self, theme: dict, raf_id: int = None, depo_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.raf_id = raf_id
        self.preset_depo_id = depo_id
        self.data = {}
        self.setWindowTitle("Yeni Raf" if not raf_id else "Raf Düzenle")
        self.setMinimumSize(400, 450)
        if raf_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.depo_raflari WHERE id = ?", (self.raf_id,))
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
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']};
                border-radius: 6px; padding: 8px; color: {self.theme['text']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("📚 " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.depo_combo = QComboBox()
        self.depo_combo.currentIndexChanged.connect(self._load_bolumler)
        self._load_depolar()
        form.addRow("Depo *:", self.depo_combo)
        
        self.bolum_combo = QComboBox()
        form.addRow("Bölüm:", self.bolum_combo)
        
        self.kod_input = QLineEdit(self.data.get('kod', ''))
        self.kod_input.setPlaceholderText("Örn: A-01-03")
        form.addRow("Kod *:", self.kod_input)
        
        self.barkod_input = QLineEdit(self.data.get('barkod', '') or '')
        form.addRow("Barkod:", self.barkod_input)
        
        self.koridor_input = QLineEdit(self.data.get('koridor', '') or '')
        form.addRow("Koridor:", self.koridor_input)
        
        self.sira_input = QSpinBox()
        self.sira_input.setRange(0, 999)
        self.sira_input.setValue(int(self.data.get('sira') or 0))
        form.addRow("Sıra:", self.sira_input)
        
        self.kat_input = QSpinBox()
        self.kat_input.setRange(0, 20)
        self.kat_input.setValue(int(self.data.get('kat') or 0))
        form.addRow("Kat:", self.kat_input)
        
        self.tip_combo = QComboBox()
        self.tip_combo.addItems(["Palet", "Kutu", "Küçük Parça", "Özel"])
        if self.data.get('raf_tipi'):
            idx = self.tip_combo.findText(self.data['raf_tipi'])
            if idx >= 0:
                self.tip_combo.setCurrentIndex(idx)
        form.addRow("Raf Tipi:", self.tip_combo)
        
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
    
    def _load_depolar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.depolar WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no")
            for row in cursor.fetchall():
                self.depo_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
            depo_id = self.data.get('depo_id') or self.preset_depo_id
            if depo_id:
                idx = self.depo_combo.findData(depo_id)
                if idx >= 0:
                    self.depo_combo.setCurrentIndex(idx)
        except Exception:
            pass
    
    def _load_bolumler(self):
        self.bolum_combo.clear()
        self.bolum_combo.addItem("(Seçilmedi)", None)
        depo_id = self.depo_combo.currentData()
        if not depo_id:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.depo_bolumleri WHERE depo_id=? AND aktif_mi=1 ORDER BY sira_no", (depo_id,))
            for row in cursor.fetchall():
                self.bolum_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
            if self.data.get('bolum_id'):
                idx = self.bolum_combo.findData(self.data['bolum_id'])
                if idx >= 0:
                    self.bolum_combo.setCurrentIndex(idx)
        except Exception:
            pass
    
    def _save(self):
        kod = self.kod_input.text().strip()
        if not kod:
            QMessageBox.warning(self, "Uyarı", "Kod zorunludur!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            params = (self.depo_combo.currentData(), self.bolum_combo.currentData(), kod,
                     self.barkod_input.text().strip() or None, self.koridor_input.text().strip() or None,
                     self.sira_input.value() or None, self.kat_input.value() or None,
                     self.tip_combo.currentText(), self.aktif_combo.currentData())
            if self.raf_id:
                cursor.execute("""UPDATE tanim.depo_raflari SET depo_id=?, bolum_id=?, kod=?, barkod=?, koridor=?,
                    sira=?, kat=?, raf_tipi=?, aktif_mi=?, guncelleme_tarihi=GETDATE() WHERE id=?""", params + (self.raf_id,))
            else:
                cursor.execute("""INSERT INTO tanim.depo_raflari (depo_id, bolum_id, kod, barkod, koridor, sira, kat, raf_tipi, aktif_mi)
                    VALUES (?,?,?,?,?,?,?,?,?)""", params)
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ==================== TOPLU RAF DİALOG ====================
class TopluRafDialog(QDialog):
    def __init__(self, theme: dict, depo_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.preset_depo_id = depo_id
        self.setWindowTitle("Toplu Raf Oluştur")
        self.setMinimumSize(450, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit, QSpinBox, QComboBox {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']};
                border-radius: 6px; padding: 8px; color: {self.theme['text']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("📊 Toplu Raf Oluştur")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.depo_combo = QComboBox()
        self._load_depolar()
        form.addRow("Depo *:", self.depo_combo)
        
        self.koridor_input = QLineEdit()
        self.koridor_input.setPlaceholderText("A,B,C veya A-D")
        self.koridor_input.textChanged.connect(self._update_preview)
        form.addRow("Koridorlar *:", self.koridor_input)
        
        sira_layout = QHBoxLayout()
        self.sira_bas = QSpinBox()
        self.sira_bas.setRange(1, 99)
        self.sira_bas.setValue(1)
        self.sira_bas.valueChanged.connect(self._update_preview)
        sira_layout.addWidget(self.sira_bas)
        sira_layout.addWidget(QLabel("-"))
        self.sira_son = QSpinBox()
        self.sira_son.setRange(1, 99)
        self.sira_son.setValue(10)
        self.sira_son.valueChanged.connect(self._update_preview)
        sira_layout.addWidget(self.sira_son)
        form.addRow("Sıra Aralığı *:", sira_layout)
        
        kat_layout = QHBoxLayout()
        self.kat_bas = QSpinBox()
        self.kat_bas.setRange(1, 10)
        self.kat_bas.setValue(1)
        self.kat_bas.valueChanged.connect(self._update_preview)
        kat_layout.addWidget(self.kat_bas)
        kat_layout.addWidget(QLabel("-"))
        self.kat_son = QSpinBox()
        self.kat_son.setRange(1, 10)
        self.kat_son.setValue(3)
        self.kat_son.valueChanged.connect(self._update_preview)
        kat_layout.addWidget(self.kat_son)
        form.addRow("Kat Aralığı *:", kat_layout)
        
        self.format_input = QLineEdit("{koridor}-{sira:02d}-{kat:02d}")
        form.addRow("Kod Formatı:", self.format_input)
        
        layout.addLayout(form)
        
        self.preview_label = QLabel("Önizleme: -")
        self.preview_label.setStyleSheet(f"background: {self.theme['bg_card']}; padding: 12px; border-radius: 6px; color: {self.theme['text']};")
        layout.addWidget(self.preview_label)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        create_btn = QPushButton("🔨 Oluştur")
        create_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
        create_btn.clicked.connect(self._create)
        btn_layout.addWidget(create_btn)
        layout.addLayout(btn_layout)
        
        self._update_preview()
    
    def _load_depolar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.depolar WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no")
            for row in cursor.fetchall():
                self.depo_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
            if self.preset_depo_id:
                idx = self.depo_combo.findData(self.preset_depo_id)
                if idx >= 0:
                    self.depo_combo.setCurrentIndex(idx)
        except Exception:
            pass
    
    def _parse_koridorlar(self):
        text = self.koridor_input.text().strip().upper()
        if not text:
            return []
        if ',' in text:
            return [k.strip() for k in text.split(',')]
        if '-' in text:
            parts = text.split('-')
            if len(parts) == 2 and len(parts[0]) == 1 and len(parts[1]) == 1:
                return [chr(i) for i in range(ord(parts[0]), ord(parts[1]) + 1)]
        return [text]
    
    def _update_preview(self):
        koridorlar = self._parse_koridorlar()
        sira_count = self.sira_son.value() - self.sira_bas.value() + 1
        kat_count = self.kat_son.value() - self.kat_bas.value() + 1
        total = len(koridorlar) * sira_count * kat_count
        preview = f"Toplam {total} raf oluşturulacak"
        if koridorlar:
            try:
                first = self.format_input.text().format(koridor=koridorlar[0], sira=self.sira_bas.value(), kat=self.kat_bas.value())
                last = self.format_input.text().format(koridor=koridorlar[-1], sira=self.sira_son.value(), kat=self.kat_son.value())
                preview += f"\nİlk: {first}  →  Son: {last}"
            except Exception:
                preview += "\n⚠️ Format hatası!"
        self.preview_label.setText(preview)
    
    def _create(self):
        koridorlar = self._parse_koridorlar()
        if not koridorlar:
            QMessageBox.warning(self, "Uyarı", "Koridor belirtiniz!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            count = 0
            depo_id = self.depo_combo.currentData()
            for koridor in koridorlar:
                for sira in range(self.sira_bas.value(), self.sira_son.value() + 1):
                    for kat in range(self.kat_bas.value(), self.kat_son.value() + 1):
                        kod = self.format_input.text().format(koridor=koridor, sira=sira, kat=kat)
                        cursor.execute("INSERT INTO tanim.depo_raflari (depo_id, kod, koridor, sira, kat) VALUES (?,?,?,?,?)", (depo_id, kod, koridor, sira, kat))
                        count += 1
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", f"{count} raf oluşturuldu!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


# ==================== ANA SAYFA ====================
class TanimDepoPage(BasePage):
    """Depo Tanımları Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {self.theme['border']}; border-radius: 8px; background: {self.theme['bg_card']}; }}
            QTabBar::tab {{ padding: 10px 20px; margin-right: 2px; background: {self.theme['bg_main']}; color: {self.theme['text']}; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
            QTabBar::tab:selected {{ background: {self.theme['primary']}; color: white; }}
        """)
        
        self.tabs.addTab(self._create_tipler_tab(), "🏷️ Depo Tipleri")
        self.tabs.addTab(self._create_depolar_tab(), "📦 Depolar")
        self.tabs.addTab(self._create_bolumler_tab(), "🗂️ Bölümler")
        self.tabs.addTab(self._create_raflar_tab(), "📚 Raflar")
        
        layout.addWidget(self.tabs)
        
        self._load_tipler()
        self._load_depolar()
        self._load_bolumler()
        self._load_raflar()
        self._load_depo_filters()
    
    def _create_tipler_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        toolbar = QHBoxLayout()
        self.tip_search = QLineEdit()
        self.tip_search.setPlaceholderText("🔍 Ara...")
        self.tip_search.setStyleSheet(self._input_style())
        self.tip_search.setMaximumWidth(250)
        self.tip_search.textChanged.connect(self._load_tipler)
        toolbar.addWidget(self.tip_search)
        toolbar.addStretch()
        add_btn = QPushButton("➕ Yeni Tip")
        add_btn.setStyleSheet(self._primary_btn_style())
        add_btn.clicked.connect(self._add_tip)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.tip_table = QTableWidget()
        self.tip_table.setColumnCount(5)
        self.tip_table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Durum", "İşlem"])
        self.tip_table.setColumnWidth(4, 170)
        self.tip_table.setColumnWidth(0, 60)
        self.tip_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tip_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tip_table.setStyleSheet(self._table_style())
        layout.addWidget(self.tip_table)
        return widget
    
    def _create_depolar_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        toolbar = QHBoxLayout()
        self.depo_search = QLineEdit()
        self.depo_search.setPlaceholderText("🔍 Ara...")
        self.depo_search.setStyleSheet(self._input_style())
        self.depo_search.setMaximumWidth(250)
        self.depo_search.textChanged.connect(self._load_depolar)
        toolbar.addWidget(self.depo_search)
        self.depo_tip_filter = QComboBox()
        self.depo_tip_filter.setStyleSheet(self._combo_style())
        self.depo_tip_filter.currentIndexChanged.connect(self._load_depolar)
        toolbar.addWidget(self.depo_tip_filter)
        toolbar.addStretch()
        add_btn = QPushButton("➕ Yeni Depo")
        add_btn.setStyleSheet(self._primary_btn_style())
        add_btn.clicked.connect(self._add_depo)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.depo_table = QTableWidget()
        self.depo_table.setColumnCount(8)
        self.depo_table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Tip", "Alan", "Palet", "Durum", "İşlem"])
        self.depo_table.setColumnWidth(7, 170)
        self.depo_table.setColumnWidth(0, 60)
        self.depo_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.depo_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.depo_table.setStyleSheet(self._table_style())
        layout.addWidget(self.depo_table)
        return widget
    
    def _create_bolumler_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        toolbar = QHBoxLayout()
        self.bolum_search = QLineEdit()
        self.bolum_search.setPlaceholderText("🔍 Ara...")
        self.bolum_search.setStyleSheet(self._input_style())
        self.bolum_search.setMaximumWidth(250)
        self.bolum_search.textChanged.connect(self._load_bolumler)
        toolbar.addWidget(self.bolum_search)
        self.bolum_depo_filter = QComboBox()
        self.bolum_depo_filter.setStyleSheet(self._combo_style())
        self.bolum_depo_filter.currentIndexChanged.connect(self._load_bolumler)
        toolbar.addWidget(self.bolum_depo_filter)
        toolbar.addStretch()
        add_btn = QPushButton("➕ Yeni Bölüm")
        add_btn.setStyleSheet(self._primary_btn_style())
        add_btn.clicked.connect(self._add_bolum)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.bolum_table = QTableWidget()
        self.bolum_table.setColumnCount(7)
        self.bolum_table.setHorizontalHeaderLabels(["ID", "Depo", "Kod", "Ad", "Tip", "Durum", "İşlem"])
        self.bolum_table.setColumnWidth(6, 170)
        self.bolum_table.setColumnWidth(0, 60)
        self.bolum_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.bolum_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bolum_table.setStyleSheet(self._table_style())
        layout.addWidget(self.bolum_table)
        return widget
    
    def _create_raflar_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        toolbar = QHBoxLayout()
        self.raf_search = QLineEdit()
        self.raf_search.setPlaceholderText("🔍 Ara...")
        self.raf_search.setStyleSheet(self._input_style())
        self.raf_search.setMaximumWidth(250)
        self.raf_search.textChanged.connect(self._load_raflar)
        toolbar.addWidget(self.raf_search)
        self.raf_depo_filter = QComboBox()
        self.raf_depo_filter.setStyleSheet(self._combo_style())
        self.raf_depo_filter.currentIndexChanged.connect(self._load_raflar)
        toolbar.addWidget(self.raf_depo_filter)
        toolbar.addStretch()
        bulk_btn = QPushButton("📊 Toplu Raf")
        bulk_btn.setStyleSheet(self._primary_btn_style().replace(self.theme['primary'], '#10B981'))
        bulk_btn.clicked.connect(self._add_bulk_raf)
        toolbar.addWidget(bulk_btn)
        add_btn = QPushButton("➕ Yeni Raf")
        add_btn.setStyleSheet(self._primary_btn_style())
        add_btn.clicked.connect(self._add_raf)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.raf_table = QTableWidget()
        self.raf_table.setColumnCount(8)
        self.raf_table.setHorizontalHeaderLabels(["ID", "Depo", "Kod", "Koridor", "Sıra", "Kat", "Durum", "İşlem"])
        self.raf_table.setColumnWidth(7, 170)
        self.raf_table.setColumnWidth(0, 60)
        self.raf_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.raf_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.raf_table.setStyleSheet(self._table_style())
        layout.addWidget(self.raf_table)
        return widget
    
    # ==================== VERİ YÜKLEME ====================
    def _load_tipler(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            search = self.tip_search.text().strip()
            sql = "SELECT id, kod, ad, aktif_mi FROM tanim.depo_tipleri WHERE 1=1"
            params = []
            if search:
                sql += " AND (kod LIKE ? OR ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            sql += " ORDER BY ad"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.tip_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.tip_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.tip_table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.tip_table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                durum = QTableWidgetItem("✓" if row[3] else "✗")
                durum.setForeground(QColor("#10B981") if row[3] else QColor("#EF4444"))
                self.tip_table.setItem(i, 3, durum)
                
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, rid=row[0]: self._edit_tip(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_tip(rid), "delete"),
                ])
                self.tip_table.setCellWidget(i, 4, widget)
                self.tip_table.setRowHeight(i, 42)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _load_depolar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            search = self.depo_search.text().strip()
            tip_id = self.depo_tip_filter.currentData()
            sql = """SELECT d.id, d.kod, d.ad, t.ad, d.alan_m2, d.kapasite_palet, d.aktif_mi
                     FROM tanim.depolar d LEFT JOIN tanim.depo_tipleri t ON d.depo_tipi_id=t.id WHERE d.silindi_mi=0"""
            params = []
            if search:
                sql += " AND (d.kod LIKE ? OR d.ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            if tip_id:
                sql += " AND d.depo_tipi_id=?"
                params.append(tip_id)
            sql += " ORDER BY d.sira_no, d.kod"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.depo_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.depo_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.depo_table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.depo_table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.depo_table.setItem(i, 3, QTableWidgetItem(row[3] or ''))
                self.depo_table.setItem(i, 4, QTableWidgetItem(f"{row[4]:.0f} m²" if row[4] else '-'))
                self.depo_table.setItem(i, 5, QTableWidgetItem(str(row[5]) if row[5] else '-'))
                durum = QTableWidgetItem("✓" if row[6] else "✗")
                durum.setForeground(QColor("#10B981") if row[6] else QColor("#EF4444"))
                self.depo_table.setItem(i, 6, durum)
                
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, rid=row[0]: self._edit_depo(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_depo(rid), "delete"),
                ])
                self.depo_table.setCellWidget(i, 7, widget)
                self.depo_table.setRowHeight(i, 42)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _load_bolumler(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            search = self.bolum_search.text().strip()
            depo_id = self.bolum_depo_filter.currentData()
            sql = """SELECT b.id, d.kod, b.kod, b.ad, b.bolum_tipi, b.aktif_mi
                     FROM tanim.depo_bolumleri b JOIN tanim.depolar d ON b.depo_id=d.id WHERE d.silindi_mi=0"""
            params = []
            if search:
                sql += " AND (b.kod LIKE ? OR b.ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            if depo_id:
                sql += " AND b.depo_id=?"
                params.append(depo_id)
            sql += " ORDER BY d.sira_no, b.sira_no"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.bolum_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.bolum_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.bolum_table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.bolum_table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.bolum_table.setItem(i, 3, QTableWidgetItem(row[3] or ''))
                self.bolum_table.setItem(i, 4, QTableWidgetItem(row[4] or '-'))
                durum = QTableWidgetItem("✓" if row[5] else "✗")
                durum.setForeground(QColor("#10B981") if row[5] else QColor("#EF4444"))
                self.bolum_table.setItem(i, 5, durum)
                
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, rid=row[0]: self._edit_bolum(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_bolum(rid), "delete"),
                ])
                self.bolum_table.setCellWidget(i, 6, widget)
                self.bolum_table.setRowHeight(i, 42)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _load_raflar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            search = self.raf_search.text().strip()
            depo_id = self.raf_depo_filter.currentData()
            sql = """SELECT r.id, d.kod, r.kod, r.koridor, r.sira, r.kat, r.aktif_mi
                     FROM tanim.depo_raflari r JOIN tanim.depolar d ON r.depo_id=d.id WHERE d.silindi_mi=0"""
            params = []
            if search:
                sql += " AND (r.kod LIKE ? OR r.barkod LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            if depo_id:
                sql += " AND r.depo_id=?"
                params.append(depo_id)
            sql += " ORDER BY d.sira_no, r.koridor, r.sira, r.kat"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.raf_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.raf_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.raf_table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.raf_table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.raf_table.setItem(i, 3, QTableWidgetItem(row[3] or '-'))
                self.raf_table.setItem(i, 4, QTableWidgetItem(str(row[4]) if row[4] else '-'))
                self.raf_table.setItem(i, 5, QTableWidgetItem(str(row[5]) if row[5] else '-'))
                durum = QTableWidgetItem("✓" if row[6] else "✗")
                durum.setForeground(QColor("#10B981") if row[6] else QColor("#EF4444"))
                self.raf_table.setItem(i, 6, durum)
                
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, rid=row[0]: self._edit_raf(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_raf(rid), "delete"),
                ])
                self.raf_table.setCellWidget(i, 7, widget)
                self.raf_table.setRowHeight(i, 42)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _load_depo_filters(self):
        try:
            self.depo_tip_filter.clear()
            self.depo_tip_filter.addItem("Tüm Tipler", None)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM tanim.depo_tipleri WHERE aktif_mi=1 ORDER BY ad")
            for row in cursor.fetchall():
                self.depo_tip_filter.addItem(row[1], row[0])
            
            self.bolum_depo_filter.clear()
            self.bolum_depo_filter.addItem("Tüm Depolar", None)
            self.raf_depo_filter.clear()
            self.raf_depo_filter.addItem("Tüm Depolar", None)
            cursor.execute("SELECT id, kod FROM tanim.depolar WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no")
            for row in cursor.fetchall():
                self.bolum_depo_filter.addItem(row[1], row[0])
                self.raf_depo_filter.addItem(row[1], row[0])
            conn.close()
        except Exception:
            pass
    
    # ==================== CRUD ====================
    def _add_tip(self):
        dlg = DepoTipiDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_tipler()
            self._load_depo_filters()
    
    def _edit_tip(self, tid):
        dlg = DepoTipiDialog(self.theme, tid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_tipler()
    
    def _delete_tip(self, tid):
        if QMessageBox.question(self, "Onay", "Silmek istediğinize emin misiniz?") == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tanim.depolar WHERE depo_tipi_id=?", (tid,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu tipe bağlı depolar var!")
                    conn.close()
                    return
                cursor.execute("DELETE FROM tanim.depo_tipleri WHERE id=?", (tid,))
                conn.commit()
                conn.close()
                self._load_tipler()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _add_depo(self):
        dlg = DepoDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_depolar()
            self._load_depo_filters()
    
    def _edit_depo(self, did):
        dlg = DepoDialog(self.theme, did, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_depolar()
    
    def _delete_depo(self, did):
        if QMessageBox.question(self, "Onay", "Silmek istediğinize emin misiniz?") == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE tanim.depolar SET silindi_mi=1, silinme_tarihi=GETDATE() WHERE id=?", (did,))
                conn.commit()
                conn.close()
                self._load_depolar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _add_bolum(self):
        depo_id = self.bolum_depo_filter.currentData()
        dlg = BolumDialog(self.theme, depo_id=depo_id, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_bolumler()
    
    def _edit_bolum(self, bid):
        dlg = BolumDialog(self.theme, bid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_bolumler()
    
    def _delete_bolum(self, bid):
        if QMessageBox.question(self, "Onay", "Silmek istediğinize emin misiniz?") == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE tanim.depo_bolumleri SET aktif_mi=0 WHERE id=?", (bid,))
                conn.commit()
                conn.close()
                self._load_bolumler()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _add_raf(self):
        depo_id = self.raf_depo_filter.currentData()
        dlg = RafDialog(self.theme, depo_id=depo_id, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_raflar()
    
    def _edit_raf(self, rid):
        dlg = RafDialog(self.theme, rid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_raflar()
    
    def _delete_raf(self, rid):
        if QMessageBox.question(self, "Onay", "Silmek istediğinize emin misiniz?") == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE tanim.depo_raflari SET aktif_mi=0 WHERE id=?", (rid,))
                conn.commit()
                conn.close()
                self._load_raflar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _add_bulk_raf(self):
        depo_id = self.raf_depo_filter.currentData()
        dlg = TopluRafDialog(self.theme, depo_id, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_raflar()
    
    # ==================== STİLLER ====================
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
