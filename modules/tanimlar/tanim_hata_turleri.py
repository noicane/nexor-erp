# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Hata Türleri Tanım Ekranı
Kalite kontrol hata türleri yönetimi
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QTextEdit, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class HataTuruDialog(QDialog):
    """Hata Türü Ekleme/Düzenleme Dialog"""
    
    def __init__(self, theme: dict, hata_data: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.hata_data = hata_data or {}
        self.setWindowTitle("Hata Türü Ekle" if not hata_data else "Hata Türü Düzenle")
        self.setMinimumSize(500, 500)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main', '#1a1f2e')}; }}
            QLabel {{ color: {self.theme.get('text', '#fff')}; }}
            QLineEdit, QTextEdit, QComboBox, QSpinBox {{
                background: {self.theme.get('bg_input', '#2d3548')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 8px 12px;
                color: {self.theme.get('text', '#fff')};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Kod
        layout.addWidget(QLabel("Kod:"))
        self.kod_input = QLineEdit()
        self.kod_input.setPlaceholderText("Örn: KPL-001")
        self.kod_input.setText(self.hata_data.get('kod', ''))
        layout.addWidget(self.kod_input)
        
        # Ad
        layout.addWidget(QLabel("Hata Adı:"))
        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderText("Örn: Kaplama eksikliği")
        self.ad_input.setText(self.hata_data.get('ad', ''))
        layout.addWidget(self.ad_input)
        
        # Kategori
        layout.addWidget(QLabel("Kategori:"))
        self.kategori_combo = QComboBox()
        self.kategori_combo.addItems([
            "KAPLAMA", "YUZEY", "OLCU", "PAKETLEME", "MALZEME", "DIGER"
        ])
        if self.hata_data.get('kategori'):
            idx = self.kategori_combo.findText(self.hata_data['kategori'])
            if idx >= 0:
                self.kategori_combo.setCurrentIndex(idx)
        layout.addWidget(self.kategori_combo)
        
        # Önem Derecesi
        layout.addWidget(QLabel("Önem Derecesi:"))
        self.onem_combo = QComboBox()
        self.onem_combo.addItem("1 - Düşük", 1)
        self.onem_combo.addItem("2 - Orta", 2)
        self.onem_combo.addItem("3 - Yüksek", 3)
        self.onem_combo.addItem("4 - Kritik", 4)
        onem = self.hata_data.get('onem_derecesi', 1)
        self.onem_combo.setCurrentIndex(onem - 1 if onem else 0)
        layout.addWidget(self.onem_combo)
        
        # Sıra No
        layout.addWidget(QLabel("Sıra No:"))
        self.sira_input = QSpinBox()
        self.sira_input.setRange(0, 999)
        self.sira_input.setValue(self.hata_data.get('sira_no', 0) or 0)
        layout.addWidget(self.sira_input)
        
        # Açıklama
        layout.addWidget(QLabel("Açıklama:"))
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setMaximumHeight(80)
        self.aciklama_input.setPlaceholderText("Hata türü açıklaması...")
        self.aciklama_input.setText(self.hata_data.get('aciklama', '') or '')
        layout.addWidget(self.aciklama_input)
        
        # Aktif
        self.aktif_check = QComboBox()
        self.aktif_check.addItem("Aktif", True)
        self.aktif_check.addItem("Pasif", False)
        if not self.hata_data.get('aktif_mi', True):
            self.aktif_check.setCurrentIndex(1)
        layout.addWidget(QLabel("Durum:"))
        layout.addWidget(self.aktif_check)
        
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 10px 24px;
            }}
        """)
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)
        
        kaydet_btn = QPushButton("💾 Kaydet")
        kaydet_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
            }}
        """)
        kaydet_btn.clicked.connect(self._save)
        btn_layout.addWidget(kaydet_btn)
        
        layout.addLayout(btn_layout)
    
    def _save(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()
        
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad alanları zorunludur!")
            return
        
        self.result_data = {
            'kod': kod,
            'ad': ad,
            'kategori': self.kategori_combo.currentText(),
            'onem_derecesi': self.onem_combo.currentData(),
            'sira_no': self.sira_input.value(),
            'aciklama': self.aciklama_input.toPlainText().strip(),
            'aktif_mi': self.aktif_check.currentData()
        }
        self.accept()


class HataTurleriPage(BasePage):
    """Hata Türleri Tanım Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("⚠️ Hata Türleri Tanımları")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text', '#fff')};")
        header.addWidget(title)
        header.addStretch()
        
        # Filtre
        self.kategori_filter = QComboBox()
        self.kategori_filter.setStyleSheet(self._combo_style())
        self.kategori_filter.setMinimumWidth(150)
        self.kategori_filter.addItem("Tüm Kategoriler", None)
        self.kategori_filter.addItem("KAPLAMA", "KAPLAMA")
        self.kategori_filter.addItem("YUZEY", "YUZEY")
        self.kategori_filter.addItem("OLCU", "OLCU")
        self.kategori_filter.addItem("PAKETLEME", "PAKETLEME")
        self.kategori_filter.addItem("MALZEME", "MALZEME")
        self.kategori_filter.addItem("DIGER", "DIGER")
        self.kategori_filter.currentIndexChanged.connect(self._load_data)
        header.addWidget(self.kategori_filter)
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(self._button_style())
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        
        add_btn = QPushButton("➕ Yeni Hata Türü")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
        """)
        add_btn.clicked.connect(self._add_new)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kod", "Hata Adı", "Kategori", "Önem", "Sıra", "Durum", "İşlem"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 140)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(self._table_style())
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Alt bilgi
        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {self.theme.get('text_muted', '#8a94a6')};")
        layout.addWidget(self.info_label)
    
    def _combo_style(self):
        return f"""
            QComboBox {{
                background: {self.theme.get('bg_input', '#2d3548')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 8px 12px;
                color: {self.theme.get('text', '#fff')};
            }}
        """
    
    def _button_style(self):
        return f"""
            QPushButton {{
                background: {self.theme.get('bg_input', '#2d3548')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {self.theme.get('bg_hover', '#3d4454')};
            }}
        """
    
    def _table_style(self):
        return f"""
            QTableWidget {{
                background: {self.theme.get('bg_card', '#242938')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border', '#3d4454')};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_hover', '#2d3548')};
                color: {self.theme.get('text', '#fff')};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            kategori = self.kategori_filter.currentData()
            
            if kategori:
                cursor.execute("""
                    SELECT id, kod, ad, kategori, onem_derecesi, sira_no, aktif_mi
                    FROM tanim.hata_turleri
                    WHERE kategori = ?
                    ORDER BY sira_no, kod
                """, (kategori,))
            else:
                cursor.execute("""
                    SELECT id, kod, ad, kategori, onem_derecesi, sira_no, aktif_mi
                    FROM tanim.hata_turleri
                    ORDER BY sira_no, kod
                """)
            
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            
            onem_labels = {1: "Düşük", 2: "Orta", 3: "Yüksek", 4: "Kritik"}
            onem_colors = {1: "#22c55e", 2: "#f59e0b", 3: "#ef4444", 4: "#dc2626"}
            
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or ''))
                
                # Önem derecesi
                onem = row[4] or 1
                onem_item = QTableWidgetItem(onem_labels.get(onem, str(onem)))
                onem_item.setForeground(QColor(onem_colors.get(onem, '#fff')))
                onem_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 4, onem_item)
                
                # Sıra
                sira_item = QTableWidgetItem(str(row[5] or 0))
                sira_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 5, sira_item)
                
                # Durum
                aktif = row[6] if row[6] is not None else True
                durum_item = QTableWidgetItem("✓ Aktif" if aktif else "✗ Pasif")
                durum_item.setForeground(QColor('#22c55e' if aktif else '#ef4444'))
                durum_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 6, durum_item)
                
                # İşlem butonları
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, rid=row[0]: self._edit_item(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 7, widget)
                self.table.setRowHeight(i, 42)
            
            self.info_label.setText(f"Toplam {len(rows)} hata türü")
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yüklenemedi: {e}")
    
    def _add_new(self):
        dlg = HataTuruDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                data = dlg.result_data
                cursor.execute("""
                    INSERT INTO tanim.hata_turleri (kod, ad, kategori, onem_derecesi, sira_no, aciklama, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data['kod'], data['ad'], data['kategori'], data['onem_derecesi'], 
                      data['sira_no'], data['aciklama'], data['aktif_mi']))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "✓ Başarılı", "Hata türü eklendi!")
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kayıt eklenemedi: {e}")
    
    def _edit_item(self, hata_id: int):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad, kategori, onem_derecesi, sira_no, aciklama, aktif_mi
                FROM tanim.hata_turleri WHERE id = ?
            """, (hata_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                hata_data = {
                    'id': row[0], 'kod': row[1], 'ad': row[2], 'kategori': row[3],
                    'onem_derecesi': row[4], 'sira_no': row[5], 'aciklama': row[6], 'aktif_mi': row[7]
                }
                dlg = HataTuruDialog(self.theme, hata_data, parent=self)
                if dlg.exec() == QDialog.Accepted:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        data = dlg.result_data
                        cursor.execute("""
                            UPDATE tanim.hata_turleri 
                            SET kod = ?, ad = ?, kategori = ?, onem_derecesi = ?, 
                                sira_no = ?, aciklama = ?, aktif_mi = ?
                            WHERE id = ?
                        """, (data['kod'], data['ad'], data['kategori'], data['onem_derecesi'],
                              data['sira_no'], data['aciklama'], data['aktif_mi'], hata_id))
                        conn.commit()
                        conn.close()
                        QMessageBox.information(self, "✓ Başarılı", "Hata türü güncellendi!")
                        self._load_data()
                    except Exception as e:
                        QMessageBox.critical(self, "Hata", f"Güncelleme başarısız: {e}")
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri alınamadı: {e}")
    
    def _delete_item(self, hata_id: int):
        reply = QMessageBox.question(
            self, "Silme Onayı", 
            "Bu hata türünü silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tanim.hata_turleri WHERE id = ?", (hata_id,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "✓ Başarılı", "Hata türü silindi!")
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme başarısız: {e}")
