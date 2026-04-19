# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Arıza Bildirimleri
bakim.ariza_bildirimleri tablosu için CRUD
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QTextEdit, QComboBox, QDateTimeEdit, QWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand


# ============================================================================
# MODERN STYLE HELPER
# ============================================================================
def get_modern_style(theme: dict) -> dict:
    """Brand-based style helper (backward compat)"""
    return {
        'card_bg': brand.BG_CARD,
        'input_bg': brand.BG_INPUT,
        'border': brand.BORDER,
        'text': brand.TEXT,
        'text_secondary': brand.TEXT_MUTED,
        'text_muted': brand.TEXT_DIM,
        'primary': brand.PRIMARY,
        'primary_hover': brand.PRIMARY_HOVER,
        'success': brand.SUCCESS,
        'warning': brand.WARNING,
        'error': brand.ERROR,
        'danger': brand.ERROR,
        'info': brand.INFO,
        'bg_main': brand.BG_MAIN,
        'bg_hover': brand.BG_HOVER,
        'bg_selected': brand.BG_SELECTED,
        'border_light': brand.BORDER_HARD,
        'border_input': brand.BORDER,
        'card_solid': brand.BG_CARD,
        'gradient': '',
    }


class ArizaDialog(QDialog):
    """Arıza Bildirimi Ekleme/Düzenleme - Modern UI"""
    
    def __init__(self, theme: dict, ariza_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.ariza_id = ariza_id
        self.data = {}
        
        self.setWindowTitle("Yeni Arıza Bildirimi" if not ariza_id else "Arıza Düzenle")
        self.setMinimumSize(560, 620)
        self.setModal(True)
        
        if ariza_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bakim.ariza_bildirimleri WHERE id = ?", (self.ariza_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 12px;
            }}
            QLabel {{
                color: {s['text']};
                background: transparent;
            }}
            QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {s['text']};
                font-size: 13px;
                min-height: 20px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
                border-color: {s['primary']};
            }}
            QLineEdit:disabled {{
                background: {s['border']};
                color: {s['text_muted']};
            }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                color: {s['text']};
                selection-background-color: {s['primary']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        icon = QLabel("⚠️")
        icon.setStyleSheet("font-size: 28px;")
        header.addWidget(icon)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {s['border']}; max-height: 1px;")
        layout.addWidget(sep)
        
        # Form
        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignRight)
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        
        # Bildirim No
        lbl = QLabel("Bildirim No")
        lbl.setStyleSheet(label_style)
        self.no_input = QLineEdit(self.data.get('bildirim_no', ''))
        self.no_input.setPlaceholderText("Otomatik oluşturulur")
        self.no_input.setEnabled(False)
        form.addRow(lbl, self.no_input)
        
        # Ekipman
        lbl = QLabel("Ekipman *")
        lbl.setStyleSheet(label_style)
        self.ekipman_combo = QComboBox()
        self.ekipman_combo.addItem("-- Ekipman Seçin --", None)
        self._load_ekipmanlar()
        form.addRow(lbl, self.ekipman_combo)
        
        # Bildirim Zamanı
        lbl = QLabel("Bildirim Zamanı")
        lbl.setStyleSheet(label_style)
        self.bildirim_zamani = QDateTimeEdit()
        self.bildirim_zamani.setCalendarPopup(True)
        self.bildirim_zamani.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.bildirim_zamani.setDateTime(self.data.get('bildirim_zamani') or QDateTime.currentDateTime())
        form.addRow(lbl, self.bildirim_zamani)
        
        # Arıza Tanımı
        lbl = QLabel("Arıza Tanımı *")
        lbl.setStyleSheet(label_style)
        self.tanim_input = QTextEdit()
        self.tanim_input.setMaximumHeight(100)
        self.tanim_input.setPlaceholderText("Arızayı detaylı açıklayın...")
        self.tanim_input.setText(self.data.get('ariza_tanimi', '') or '')
        form.addRow(lbl, self.tanim_input)
        
        # Bildiren
        lbl = QLabel("Bildiren *")
        lbl.setStyleSheet(label_style)
        self.bildiren_combo = QComboBox()
        self.bildiren_combo.addItem("-- Personel Seçin --", None)
        self._load_personel()
        form.addRow(lbl, self.bildiren_combo)
        
        # Öncelik
        lbl = QLabel("Öncelik")
        lbl.setStyleSheet(label_style)
        self.oncelik_combo = QComboBox()
        for o, label in [("DUSUK", "🟢 Düşük"), ("NORMAL", "🟡 Normal"), ("YUKSEK", "🟠 Yüksek"), ("KRITIK", "🔴 Kritik")]:
            self.oncelik_combo.addItem(label, o)
        if self.data.get('oncelik'):
            idx = self.oncelik_combo.findData(self.data['oncelik'])
            if idx >= 0: self.oncelik_combo.setCurrentIndex(idx)
        else:
            self.oncelik_combo.setCurrentIndex(1)
        form.addRow(lbl, self.oncelik_combo)
        
        # Durum
        lbl = QLabel("Durum")
        lbl.setStyleSheet(label_style)
        self.durum_combo = QComboBox()
        for d, label in [("ACIK", "📋 Açık"), ("ISLEMDE", "🔧 İşlemde"), ("BEKLEMEDE", "⏸️ Beklemede"), ("KAPALI", "✅ Kapalı")]:
            self.durum_combo.addItem(label, d)
        if self.data.get('durum'):
            idx = self.durum_combo.findData(self.data['durum'])
            if idx >= 0: self.durum_combo.setCurrentIndex(idx)
        form.addRow(lbl, self.durum_combo)
        
        # Çözüm Zamanı
        lbl = QLabel("Çözüm Zamanı")
        lbl.setStyleSheet(label_style)
        self.cozum_zamani = QDateTimeEdit()
        self.cozum_zamani.setCalendarPopup(True)
        self.cozum_zamani.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.cozum_zamani.setDateTime(self.data.get('cozum_zamani') or QDateTime.currentDateTime())
        form.addRow(lbl, self.cozum_zamani)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {s['border']};
                border-color: {s['primary']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾  Kaydet")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 28px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {s['primary_hover']};
            }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    # ========== DATA METHODS (UNCHANGED) ==========
    def _load_ekipmanlar(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ekipman_kodu, ekipman_adi FROM bakim.ekipmanlar WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY ekipman_kodu")
            for row in cursor.fetchall():
                self.ekipman_combo.addItem(f"{row[1]} - {row[2]}", row[0])

            if self.data.get('ekipman_id'):
                idx = self.ekipman_combo.findData(self.data['ekipman_id'])
                if idx >= 0: self.ekipman_combo.setCurrentIndex(idx)
        except Exception: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _load_personel(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad, soyad FROM ik.personeller WHERE aktif_mi=1 ORDER BY ad, soyad")
            for row in cursor.fetchall():
                self.bildiren_combo.addItem(f"{row[1]} {row[2]}", row[0])

            if self.data.get('bildiren_id'):
                idx = self.bildiren_combo.findData(self.data['bildiren_id'])
                if idx >= 0: self.bildiren_combo.setCurrentIndex(idx)
        except Exception: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _save(self):
        ekipman_id = self.ekipman_combo.currentData()
        bildiren_id = self.bildiren_combo.currentData()
        ariza_tanimi = self.tanim_input.toPlainText().strip()
        
        if not ekipman_id or not bildiren_id or not ariza_tanimi:
            QMessageBox.warning(self, "⚠️ Eksik Bilgi", "Ekipman, Bildiren ve Arıza Tanımı zorunludur!")
            return
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            params = (
                ekipman_id, self.bildirim_zamani.dateTime().toPython(),
                ariza_tanimi, bildiren_id,
                self.oncelik_combo.currentData(), self.durum_combo.currentData(),
                self.cozum_zamani.dateTime().toPython() if self.durum_combo.currentData() == 'KAPALI' else None
            )

            if self.ariza_id:
                cursor.execute("""UPDATE bakim.ariza_bildirimleri SET ekipman_id=?, bildirim_zamani=?,
                    ariza_tanimi=?, bildiren_id=?, oncelik=?, durum=?, cozum_zamani=? WHERE id=?""",
                    params + (self.ariza_id,))
            else:
                cursor.execute("""
                    DECLARE @no NVARCHAR(20) = 'ARZ-' + FORMAT(GETDATE(),'yyyyMMdd') + '-' + RIGHT('000'+CAST((SELECT ISNULL(MAX(id),0)+1 FROM bakim.ariza_bildirimleri) AS VARCHAR),3);
                    INSERT INTO bakim.ariza_bildirimleri (bildirim_no, ekipman_id, bildirim_zamani, ariza_tanimi, bildiren_id, oncelik, durum, cozum_zamani)
                    VALUES (@no, ?, ?, ?, ?, ?, ?, ?)
                """, params)

            conn.commit()
            LogManager.log_insert('bakim', 'bakim.ariza_bildirimleri', None, 'Ariza bildirimi olusturuldu')

            # Bildirim: Arıza bildirimi (sadece yeni kayıt)
            if not self.ariza_id:
                try:
                    from core.bildirim_tetikleyici import BildirimTetikleyici
                    ekipman_adi = self.ekipman_combo.currentText() if hasattr(self, 'ekipman_combo') else ''
                    ariza_aciklama = params[2] if len(params) > 2 else ''
                    BildirimTetikleyici.ariza_bildirildi(
                        ariza_id=0,
                        ekipman_adi=ekipman_adi,
                        ariza_aciklama=str(ariza_aciklama)[:100],
                    )
                except Exception as bt_err:
                    print(f"Bildirim hatasi: {bt_err}")

            QMessageBox.information(self, "Basarili", "Ariza bildirimi kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass


class BakimArizaPage(BasePage):
    """Arıza Bildirimleri Listesi - Modern UI"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        
        title_row = QHBoxLayout()
        icon = QLabel("⚠️")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Arıza Bildirimleri")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        
        subtitle = QLabel("Ekipman arızalarını bildirin ve takip edin")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()
        
        # Stat Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        self.acik_label = self._create_stat_card("Açık", "0", s['error'])
        self.islemde_label = self._create_stat_card("İşlemde", "0", s['warning'])
        self.kritik_label = self._create_stat_card("Kritik", "0", "#DC2626")
        stats_layout.addWidget(self.acik_label)
        stats_layout.addWidget(self.islemde_label)
        stats_layout.addWidget(self.kritik_label)
        header.addLayout(stats_layout)
        
        layout.addLayout(header)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara (No, Ekipman, Tanım)")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 14px;
                color: {s['text']};
                font-size: 13px;
                min-width: 220px;
            }}
            QLineEdit:focus {{ border-color: {s['primary']}; }}
        """)
        self.search_input.returnPressed.connect(self._load_data)
        toolbar.addWidget(self.search_input)
        
        combo_style = f"""
            QComboBox {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {s['text']};
                min-width: 130px;
                font-size: 13px;
            }}
            QComboBox:hover {{ border-color: {s['border_light']}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                color: {s['text']};
                selection-background-color: {s['primary']};
            }}
        """
        
        self.durum_combo = QComboBox()
        self.durum_combo.addItem("📊 Tüm Durumlar", None)
        self.durum_combo.addItem("📋 Açık", "ACIK")
        self.durum_combo.addItem("🔧 İşlemde", "ISLEMDE")
        self.durum_combo.addItem("⏸️ Beklemede", "BEKLEMEDE")
        self.durum_combo.addItem("✅ Kapalı", "KAPALI")
        self.durum_combo.setStyleSheet(combo_style)
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.durum_combo)
        
        self.oncelik_combo = QComboBox()
        self.oncelik_combo.addItem("⚡ Tüm Öncelikler", None)
        self.oncelik_combo.addItem("🔴 Kritik", "KRITIK")
        self.oncelik_combo.addItem("🟠 Yüksek", "YUKSEK")
        self.oncelik_combo.addItem("🟡 Normal", "NORMAL")
        self.oncelik_combo.addItem("🟢 Düşük", "DUSUK")
        self.oncelik_combo.setStyleSheet(combo_style)
        self.oncelik_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.oncelik_combo)
        
        toolbar.addStretch()

        toolbar.addWidget(self.create_export_button(title="Ariza Bildirimleri"))

        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Yenile")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {s['border']};
                border-color: {s['primary']};
            }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(refresh_btn)
        
        add_btn = QPushButton("➕  Yeni Arıza")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        add_btn.clicked.connect(self._add_new)
        toolbar.addWidget(add_btn)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 10px;
                gridline-color: {s['border']};
                color: {s['text']};
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {s['border']};
            }}
            QTableWidget::item:selected {{
                background: {s['primary']};
            }}
            QTableWidget::item:hover {{
                background: rgba(220, 38, 38, 0.1);
            }}
            QHeaderView::section {{
                background: rgba(0,0,0,0.3);
                color: {s['text_secondary']};
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid {s['primary']};
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }}
        """)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Bildirim No", "Ekipman", "Arıza", "Öncelik", "Durum", "Tarih", "İşlem"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(4, 85)
        self.table.setColumnWidth(5, 95)
        self.table.setColumnWidth(6, 110)
        self.table.setColumnWidth(7, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setFixedSize(110, 70)
        frame.setStyleSheet(f"""
            QFrame {{
                background: {self.s['card_bg']};
                border: 1px solid {self.s['border']};
                border-left: 4px solid {color};
                border-radius: 10px;
            }}
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 40))
        frame.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)
        
        t_label = QLabel(title)
        t_label.setStyleSheet(f"color: {self.s['text_muted']}; font-size: 11px; font-weight: 500;")
        layout.addWidget(t_label)
        
        v_label = QLabel(value)
        v_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
        v_label.setObjectName("stat_value")
        layout.addWidget(v_label)
        
        return frame
    
    # ========== DATA METHODS (UNCHANGED) ==========
    def _load_data(self):
        s = self.s
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Stats
            cursor.execute("SELECT COUNT(*) FROM bakim.ariza_bildirimleri WHERE durum='ACIK'")
            self.acik_label.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM bakim.ariza_bildirimleri WHERE durum='ISLEMDE'")
            self.islemde_label.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM bakim.ariza_bildirimleri WHERE oncelik='KRITIK' AND durum IN ('ACIK','ISLEMDE')")
            self.kritik_label.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            # List
            sql = """SELECT a.id, a.bildirim_no, e.ekipman_kodu + ' - ' + e.ekipman_adi,
                     a.ariza_tanimi, a.oncelik, a.durum, a.bildirim_zamani
                     FROM bakim.ariza_bildirimleri a
                     JOIN bakim.ekipmanlar e ON a.ekipman_id=e.id
                     WHERE 1=1"""
            params = []

            search = self.search_input.text().strip()
            if search:
                sql += " AND (a.bildirim_no LIKE ? OR e.ekipman_kodu LIKE ? OR a.ariza_tanimi LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

            durum = self.durum_combo.currentData()
            if durum:
                sql += " AND a.durum=?"
                params.append(durum)

            oncelik = self.oncelik_combo.currentData()
            if oncelik:
                sql += " AND a.oncelik=?"
                params.append(oncelik)

            sql += " ORDER BY a.bildirim_zamani DESC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            oncelik_colors = {
                "KRITIK": s['error'], 
                "YUKSEK": s['warning'], 
                "NORMAL": "#EAB308", 
                "DUSUK": s['success']
            }
            durum_map = {
                "ACIK": "📋 Açık", 
                "ISLEMDE": "🔧 İşlemde", 
                "BEKLEMEDE": "⏸️ Beklemede", 
                "KAPALI": "✅ Kapalı"
            }
            
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # ID
                item = QTableWidgetItem(str(row[0]))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor(s['text_muted']))
                self.table.setItem(i, 0, item)
                
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                
                tanim = (row[3] or '')[:50] + ('...' if len(row[3] or '') > 50 else '')
                self.table.setItem(i, 3, QTableWidgetItem(tanim))
                
                oncelik_item = QTableWidgetItem(row[4] or '')
                if row[4] in oncelik_colors:
                    oncelik_item.setForeground(QColor(oncelik_colors[row[4]]))
                oncelik_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 4, oncelik_item)
                
                durum_item = QTableWidgetItem(durum_map.get(row[5], row[5] or ''))
                durum_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 5, durum_item)
                
                tarih = row[6].strftime("%d.%m.%Y %H:%M") if row[6] else '-'
                tarih_item = QTableWidgetItem(tarih)
                tarih_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 6, tarih_item)
                
                # Action Buttons
                btn_widget = self.create_action_buttons([
                    ("", "Düzenle", lambda _, rid=row[0]: self._edit_item(rid), "edit"),
                    ("", "Sil", lambda _, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 7, btn_widget)
                self.table.setRowHeight(i, 48)
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _add_new(self):
        dlg = ArizaDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _edit_item(self, aid):
        dlg = ArizaDialog(self.theme, aid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _delete_item(self, aid):
        if QMessageBox.question(self, "🗑️ Silme Onayı", 
            "Bu arıza bildirimini silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM bakim.ariza_bildirimleri WHERE id=?", (aid,))
                conn.commit()
                LogManager.log_delete('bakim', 'bakim.ariza_bildirimleri', None, 'Kayit silindi')
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass
