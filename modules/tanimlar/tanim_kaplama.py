# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Kaplama Tipleri Tanım Sayfası
Kaplama tipi ve üretim deposu eşleştirmesi
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QSpinBox, QComboBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class KaplamaTipiDialog(QDialog):
    """Kaplama Tipi Ekleme/Düzenleme"""
    
    def __init__(self, theme: dict, tip_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.tip_id = tip_id
        self.data = {}
        self.setWindowTitle("Yeni Kaplama Tipi" if not tip_id else "Kaplama Tipi Düzenle")
        self.setMinimumSize(450, 350)
        if tip_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.kaplama_tipleri WHERE id = ?", (self.tip_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QSpinBox, QComboBox {{
                background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px; color: {brand.TEXT};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("🎨 " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {brand.TEXT};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.kod_input = QLineEdit(self.data.get('kod', ''))
        self.kod_input.setMaxLength(20)
        self.kod_input.setPlaceholderText("Örn: KTF, CINKO, TB")
        form.addRow("Kod *:", self.kod_input)
        
        self.ad_input = QLineEdit(self.data.get('ad', ''))
        self.ad_input.setMaxLength(100)
        self.ad_input.setPlaceholderText("Örn: Kataforez, Çinko Nikel")
        form.addRow("Ad *:", self.ad_input)
        
        # Üretim Deposu seçimi
        self.depo_combo = QComboBox()
        self._load_depolar()
        form.addRow("Üretim Deposu *:", self.depo_combo)
        
        # Bilgi label
        info = QLabel("⚠️ Üretim deposu: Bu kaplama tipindeki\nmalzemeler hangi depoya gidecek?")
        info.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px;")
        form.addRow("", info)
        
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
        save_btn.setStyleSheet(f"background: {brand.PRIMARY}; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def _load_depolar(self):
        self.depo_combo.clear()
        self.depo_combo.addItem("-- Depo Seçin --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Sadece üretim depoları (hat yanı depolar)
            cursor.execute("""
                SELECT id, kod, ad FROM tanim.depolar 
                WHERE aktif_mi=1 AND silindi_mi=0 
                ORDER BY sira_no, kod
            """)
            for row in cursor.fetchall():
                self.depo_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
            
            if self.data.get('uretim_depo_id'):
                idx = self.depo_combo.findData(self.data['uretim_depo_id'])
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
        
        depo_id = self.depo_combo.currentData()
        if not depo_id:
            QMessageBox.warning(self, "Uyarı", "Üretim deposu seçiniz!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            params = (kod, ad, depo_id, self.sira_input.value(), self.aktif_combo.currentData())
            
            if self.tip_id:
                cursor.execute("""UPDATE tanim.kaplama_tipleri SET kod=?, ad=?, uretim_depo_id=?,
                    sira_no=?, aktif_mi=?, guncelleme_tarihi=GETDATE() WHERE id=?""", params + (self.tip_id,))
            else:
                cursor.execute("""INSERT INTO tanim.kaplama_tipleri (kod, ad, uretim_depo_id, sira_no, aktif_mi)
                    VALUES (?,?,?,?,?)""", params)
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class TanimKaplamaPage(BasePage):
    """Kaplama Tipleri Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("🎨 Kaplama Tipleri")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {brand.TEXT};")
        header.addWidget(title)
        
        subtitle = QLabel("Kaplama tipi ve üretim deposu eşleştirmesi")
        subtitle.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px;")
        header.addWidget(subtitle)
        header.addStretch()
        
        add_btn = QPushButton("➕ Yeni Kaplama Tipi")
        add_btn.setStyleSheet(self._primary_button_style())
        add_btn.clicked.connect(self._add_tip)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara...")
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self._load_data)
        toolbar.addWidget(self.search_input)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Üretim Deposu", "Durum", "İşlem"])
        self.table.setColumnWidth(5, 170)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(self._table_style())
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Info
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background: {brand.BG_CARD}; border-radius: 8px; padding: 8px;")
        info_layout = QHBoxLayout(info_frame)
        info_label = QLabel("💡 Mal kabul ve planlama işlemlerinde bu eşleştirme kullanılarak malzeme otomatik olarak doğru depoya yönlendirilir.")
        info_label.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px;")
        info_layout.addWidget(info_label)
        layout.addWidget(info_frame)
        
        self._load_data()

    def _primary_button_style(self):
        return f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: #fff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """

    def _input_style(self):
        return f"""
            QLineEdit, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                color: {brand.TEXT};
            }}
        """

    def _table_style(self):
        return f"""
            QTableWidget {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; gridline-color: {brand.BORDER}; }}
            QTableWidget::item {{ padding: 8px; color: {brand.TEXT}; }}
            QHeaderView::section {{ background: {brand.BG_CARD}; color: {brand.TEXT}; padding: 10px; border: none; border-bottom: 2px solid {brand.PRIMARY}; font-weight: bold; }}
        """

    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            search = self.search_input.text().strip()
            
            sql = """
                SELECT k.id, k.kod, k.ad, d.kod, d.ad, k.aktif_mi
                FROM tanim.kaplama_tipleri k
                LEFT JOIN tanim.depolar d ON k.uretim_depo_id = d.id
                WHERE 1=1
            """
            params = []
            if search:
                sql += " AND (k.kod LIKE ? OR k.ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            sql += " ORDER BY k.sira_no, k.ad"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                
                # Depo
                depo_text = f"{row[3]} - {row[4]}" if row[3] else "⚠️ Tanımsız"
                depo_item = QTableWidgetItem(depo_text)
                if not row[3]:
                    depo_item.setForeground(QColor("#EF4444"))
                else:
                    depo_item.setForeground(QColor("#10B981"))
                self.table.setItem(i, 3, depo_item)
                
                # Durum
                durum = QTableWidgetItem("✓ Aktif" if row[5] else "✗ Pasif")
                durum.setForeground(QColor("#10B981") if row[5] else QColor("#EF4444"))
                self.table.setItem(i, 4, durum)
                
                # İşlem butonları
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, rid=row[0]: self._edit_tip(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_tip(rid), "delete"),
                ])
                self.table.setCellWidget(i, 5, widget)
                self.table.setRowHeight(i, 42)
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _add_tip(self):
        dlg = KaplamaTipiDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _edit_tip(self, tid):
        dlg = KaplamaTipiDialog(self.theme, tid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _delete_tip(self, tid):
        if QMessageBox.question(self, "Onay", "Bu kaplama tipini silmek istediğinize emin misiniz?") == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tanim.kaplama_tipleri WHERE id=?", (tid,))
                conn.commit()
                conn.close()
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
