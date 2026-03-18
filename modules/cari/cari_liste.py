# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Cari Kartları Listesi Sayfası
Müşteri/Tedarikçi kartları yönetimi - musteri.cariler tablosu
[MODERNIZED UI - v2.0]

Tablo: musteri.cariler (32 sütun)
İlişkili: musteri.cari_adresler, musteri.cari_yetkililer, musteri.cari_spesifikasyonlar
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog, 
    QScrollArea, QWidget, QTabWidget, QDoubleSpinBox, QSpinBox,
    QTextEdit, QSplitter, QCheckBox, QFormLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from config import DEFAULT_PAGE_SIZE


# ============================================================================
# MODERN STYLE HELPER
# ============================================================================
def get_modern_style(theme: dict) -> dict:
    t = theme or {}
    return {
        'card_bg': t.get('bg_card', '#151B23'),
        'input_bg': t.get('bg_input', '#232C3B'),
        'border': t.get('border', '#1E2736'),
        'text': t.get('text', '#E8ECF1'),
        'text_secondary': t.get('text_secondary', '#8896A6'),
        'text_muted': t.get('text_muted', '#5C6878'),
        'primary': t.get('primary', '#DC2626'),
        'primary_hover': t.get('primary_hover', '#9B1818'),
        'success': t.get('success', '#10B981'),
        'warning': t.get('warning', '#F59E0B'),
        'error': t.get('error', '#EF4444'),
        'danger': t.get('error', '#EF4444'),
        'info': t.get('info', '#3B82F6'),
        'bg_main': t.get('bg_main', '#0F1419'),
        'bg_hover': t.get('bg_hover', '#1C2430'),
        'bg_selected': t.get('bg_selected', '#1E1215'),
        'border_light': t.get('border_light', '#2A3545'),
        'border_input': t.get('border_input', '#1E2736'),
        'card_solid': t.get('bg_card_solid', '#151B23'),
        'gradient': t.get('gradient_css', ''),
    }


class CariDetayDialog(QDialog):
    """Cari Kartı Detay ve Düzenleme Dialog - Modern UI"""
    
    def __init__(self, cari_id: int, theme: dict, parent=None):
        super().__init__(parent)
        self.cari_id = cari_id
        self.theme = theme
        self.s = get_modern_style(theme)
        self.cari_data = {}
        self.edit_mode = False
        self.edit_widgets = {}
        self.combo_data = {}
        
        self._load_data()
        self.setWindowTitle(f"Cari Kartı - {self.cari_data.get('unvan', '')}")
        self.setMinimumSize(1050, 750)
        self.setModal(True)
        self._setup_ui()
    
    def _load_data(self):
        """Veritabanından cari bilgilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.*,
                       s.ad as sehir_adi,
                       i.ad as ilce_adi
                FROM musteri.cariler c
                LEFT JOIN tanim.sehirler s ON c.sehir_id = s.id
                LEFT JOIN tanim.ilceler i ON c.ilce_id = i.id
                WHERE c.id = ?
            """, (self.cari_id,))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                self.cari_data = dict(zip(columns, row))
            
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yüklenemedi: {e}")
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{ background-color: {s['bg_main']}; }}
            QLabel {{ color: {s['text']}; }}
            QScrollArea {{ background: transparent; border: none; }}
            QTabWidget::pane {{ 
                border: 1px solid {s['border']}; 
                background: {s['card_solid']}; 
                border-radius: 10px;
                padding: 16px;
            }}
            QTabBar::tab {{ 
                background: transparent; 
                color: {s['text_muted']}; 
                padding: 12px 24px; 
                border: none;
                border-bottom: 3px solid transparent;
                font-weight: 500;
            }}
            QTabBar::tab:hover {{
                color: {s['text']};
                background: rgba(255,255,255,0.05);
            }}
            QTabBar::tab:selected {{ 
                color: {s['primary']}; 
                border-bottom-color: {s['primary']};
            }}
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {s['text']};
                font-size: 13px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border-color: {s['primary']};
            }}
            QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
                background: {s['bg_hover']};
                color: {s['text_muted']};
            }}
            QCheckBox {{ color: {s['text']}; font-size: 13px; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Ana içerik
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: transparent; }")
        
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 750])
        layout.addWidget(splitter, 1)
        
        self._set_edit_enabled(False)
    
    def _create_header(self) -> QFrame:
        s = self.s
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"""
            QFrame {{
                background: {s['card_solid']};
                border-bottom: 1px solid {s['border']};
            }}
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        cari_tipi = self.cari_data.get('cari_tipi', 'MUSTERI')
        icon = "🏭" if cari_tipi == 'TEDARIKCI' else "🏢"
        
        title = QLabel(f"{icon} {self.cari_data.get('cari_kodu', '')} - {self.cari_data.get('unvan', '')}")
        title.setStyleSheet(f"color: {s['text']}; font-size: 18px; font-weight: 600;")
        title.setWordWrap(True)
        h_layout.addWidget(title, 1)
        
        tip_colors = {'MUSTERI': s['info'], 'TEDARIKCI': s['success'], 'BOTH': '#a855f7'}
        tip_label = QLabel(cari_tipi or "MUSTERI")
        tip_label.setStyleSheet(f"""
            color: white;
            font-weight: bold;
            padding: 6px 16px;
            background: {tip_colors.get(cari_tipi, '#6b7280')};
            border-radius: 16px;
            font-size: 12px;
        """)
        h_layout.addWidget(tip_label)
        
        h_layout.addSpacing(12)
        
        is_aktif = self.cari_data.get('aktif_mi', 1)
        self.aktif_label = QLabel("✓ Aktif" if is_aktif else "✗ Pasif")
        self.aktif_label.setStyleSheet(f"""
            color: {s['success'] if is_aktif else s['error']};
            font-weight: bold;
            padding: 6px 16px;
            background: {'rgba(16,185,129,0.2)' if is_aktif else 'rgba(239,68,68,0.2)'};
            border-radius: 16px;
            font-size: 12px;
        """)
        h_layout.addWidget(self.aktif_label)
        
        h_layout.addSpacing(12)
        
        self.toggle_aktif_btn = QPushButton("Pasif Yap" if is_aktif else "Aktif Yap")
        self.toggle_aktif_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_aktif_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['error'] if is_aktif else s['success']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {'#DC2626' if is_aktif else '#059669'};
            }}
        """)
        self.toggle_aktif_btn.clicked.connect(self._toggle_aktif)
        h_layout.addWidget(self.toggle_aktif_btn)
        
        self.edit_btn = QPushButton("✏️ Düzenle")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        self.edit_btn.clicked.connect(self._toggle_edit_mode)
        h_layout.addWidget(self.edit_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(40, 40)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {s['text_muted']};
                border: none;
                font-size: 20px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                color: {s['error']};
                background: rgba(239,68,68,0.1);
            }}
        """)
        close_btn.clicked.connect(self.close)
        h_layout.addWidget(close_btn)
        
        return header
    
    def _create_left_panel(self) -> QFrame:
        s = self.s
        left_panel = QFrame()
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(340)
        left_panel.setStyleSheet(f"""
            QFrame {{
                background: {s['card_solid']};
                border-right: 1px solid {s['border']};
            }}
        """)
        l_layout = QVBoxLayout(left_panel)
        l_layout.setContentsMargins(20, 20, 20, 20)
        l_layout.setSpacing(16)
        
        cari_tipi = self.cari_data.get('cari_tipi', 'MUSTERI')
        icon = "🏭" if cari_tipi == 'TEDARIKCI' else "🏢"
        
        # Avatar
        avatar = QFrame()
        avatar.setFixedSize(80, 80)
        avatar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {s['primary']},stop:1 #7F1D1D);
                border-radius: 20px;
            }}
        """)
        avatar_layout = QVBoxLayout(avatar)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_label = QLabel(icon)
        avatar_label.setStyleSheet("font-size: 36px; background: transparent;")
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_layout.addWidget(avatar_label)
        
        avatar_container = QHBoxLayout()
        avatar_container.addStretch()
        avatar_container.addWidget(avatar)
        avatar_container.addStretch()
        l_layout.addLayout(avatar_container)
        
        # İletişim bilgileri
        info_items = [
            ("📞", "Telefon", self.cari_data.get('telefon', '-') or '-'),
            ("📱", "Cep", self.cari_data.get('cep_telefonu', '-') or '-'),
            ("📧", "E-posta", self.cari_data.get('email', '-') or '-'),
            ("🌐", "Web", self.cari_data.get('web_sitesi', '-') or '-'),
            ("📍", "Şehir", self.cari_data.get('sehir_adi', '-') or '-'),
        ]
        
        for icon, label, value in info_items:
            item_frame = QFrame()
            item_frame.setStyleSheet(f"""
                QFrame {{
                    background: {s['bg_main']};
                    border: 1px solid {s['border']};
                    border-radius: 8px;
                    padding: 8px;
                }}
            """)
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(12, 8, 12, 8)
            item_layout.setSpacing(12)
            
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size: 16px;")
            item_layout.addWidget(icon_lbl)
            
            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)
            
            label_lbl = QLabel(label)
            label_lbl.setStyleSheet(f"color: {s['text_muted']}; font-size: 11px;")
            text_layout.addWidget(label_lbl)
            
            value_lbl = QLabel(value[:30] + "..." if len(value) > 30 else value)
            value_lbl.setStyleSheet(f"color: {s['text']}; font-size: 13px;")
            text_layout.addWidget(value_lbl)
            
            item_layout.addLayout(text_layout, 1)
            l_layout.addWidget(item_frame)
        
        l_layout.addStretch()
        return left_panel
    
    def _create_right_panel(self) -> QFrame:
        s = self.s
        right_panel = QFrame()
        right_panel.setStyleSheet(f"background: {s['bg_main']};")
        r_layout = QVBoxLayout(right_panel)
        r_layout.setContentsMargins(20, 20, 20, 20)
        
        tabs = QTabWidget()
        tabs.addTab(self._create_genel_tab(), "📋 Genel Bilgiler")
        tabs.addTab(self._create_finans_tab(), "💰 Finansal")
        tabs.addTab(self._create_adres_tab(), "📍 Adresler")
        r_layout.addWidget(tabs)
        
        return right_panel
    
    def _create_genel_tab(self) -> QWidget:
        s = self.s
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.setLabelAlignment(Qt.AlignRight)
        
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        
        fields = [
            ("Cari Kodu", "cari_kodu"),
            ("Ünvan", "unvan"),
            ("Vergi Dairesi", "vergi_dairesi"),
            ("Vergi No", "vergi_no"),
            ("Telefon", "telefon"),
            ("E-posta", "email"),
        ]
        
        for label, key in fields:
            lbl = QLabel(label)
            lbl.setStyleSheet(label_style)
            inp = QLineEdit(str(self.cari_data.get(key, '') or ''))
            inp.setEnabled(False)
            self.edit_widgets[key] = inp
            layout.addRow(lbl, inp)
        
        return widget
    
    def _create_finans_tab(self) -> QWidget:
        s = self.s
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.setLabelAlignment(Qt.AlignRight)
        
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        
        lbl = QLabel("Ödeme Vadesi")
        lbl.setStyleSheet(label_style)
        vade_spin = QSpinBox()
        vade_spin.setRange(0, 365)
        vade_spin.setSuffix(" gün")
        vade_spin.setValue(self.cari_data.get('odeme_vade_gun', 0) or 0)
        vade_spin.setEnabled(False)
        self.edit_widgets['odeme_vade_gun'] = vade_spin
        layout.addRow(lbl, vade_spin)
        
        lbl = QLabel("Kredi Limiti")
        lbl.setStyleSheet(label_style)
        limit_spin = QDoubleSpinBox()
        limit_spin.setRange(0, 9999999999)
        limit_spin.setSuffix(" ₺")
        limit_spin.setDecimals(2)
        limit_spin.setValue(self.cari_data.get('kredi_limiti', 0) or 0)
        limit_spin.setEnabled(False)
        self.edit_widgets['kredi_limiti'] = limit_spin
        layout.addRow(lbl, limit_spin)
        
        return widget
    
    def _create_adres_tab(self) -> QWidget:
        s = self.s
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl = QLabel("Bu carideki adresleri 'Cari Adresler' sayfasından yönetebilirsiniz.")
        lbl.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px;")
        layout.addWidget(lbl)
        layout.addStretch()
        
        return widget
    
    def _set_edit_enabled(self, enabled: bool):
        for widget in self.edit_widgets.values():
            widget.setEnabled(enabled)
    
    def _toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        self._set_edit_enabled(self.edit_mode)
        
        s = self.s
        if self.edit_mode:
            self.edit_btn.setText("💾 Kaydet")
            self.edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {s['success']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 18px;
                    font-weight: 600;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background: #059669; }}
            """)
        else:
            self._save_changes()
            self.edit_btn.setText("✏️ Düzenle")
            self.edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {s['primary']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 18px;
                    font-weight: 600;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background: {s['primary_hover']}; }}
            """)
    
    def _save_changes(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE musteri.cariler SET
                    unvan = ?, vergi_dairesi = ?, vergi_no = ?,
                    telefon = ?, email = ?, odeme_vade_gun = ?, kredi_limiti = ?,
                    guncelleme_tarihi = GETDATE()
                WHERE id = ?
            """, (
                self.edit_widgets['unvan'].text(),
                self.edit_widgets['vergi_dairesi'].text(),
                self.edit_widgets['vergi_no'].text(),
                self.edit_widgets['telefon'].text(),
                self.edit_widgets['email'].text(),
                self.edit_widgets['odeme_vade_gun'].value(),
                self.edit_widgets['kredi_limiti'].value(),
                self.cari_id
            ))
            
            conn.commit()
            LogManager.log_update('cari', 'musteri.cariler', None, 'Kayit guncellendi')
            conn.close()
            QMessageBox.information(self, "✓ Başarılı", "Değişiklikler kaydedildi!")
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", f"Kayıt hatası: {e}")
    
    def _toggle_aktif(self):
        s = self.s
        is_aktif = self.cari_data.get('aktif_mi', 1)
        new_status = 0 if is_aktif else 1
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE musteri.cariler SET aktif_mi = ?, guncelleme_tarihi = GETDATE() WHERE id = ?", (new_status, self.cari_id))
            conn.commit()
            LogManager.log_update('cari', 'musteri.cariler', None, 'Aktiflik durumu degistirildi')
            conn.close()
            
            self.cari_data['aktif_mi'] = new_status
            is_aktif = new_status
            
            self.aktif_label.setText("✓ Aktif" if is_aktif else "✗ Pasif")
            self.aktif_label.setStyleSheet(f"""
                color: {s['success'] if is_aktif else s['error']};
                font-weight: bold;
                padding: 6px 16px;
                background: {'rgba(16,185,129,0.2)' if is_aktif else 'rgba(239,68,68,0.2)'};
                border-radius: 16px;
                font-size: 12px;
            """)
            
            self.toggle_aktif_btn.setText("Pasif Yap" if is_aktif else "Aktif Yap")
            self.toggle_aktif_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {s['error'] if is_aktif else s['success']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 18px;
                    font-weight: 600;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: {'#DC2626' if is_aktif else '#059669'};
                }}
            """)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", f"Durum değiştirilemedi: {e}")


class CariListePage(BasePage):
    """Cari Kartları Listesi - Modern UI"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.current_page = 1
        self.page_size = DEFAULT_PAGE_SIZE
        self.total_items = 0
        self.total_pages = 1
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
        icon = QLabel("🏢")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Cari Kartları")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        
        subtitle = QLabel("Müşteri ve tedarikçi kartlarını yönetin")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()
        
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(f"""
            color: {s['text_muted']};
            font-size: 13px;
            padding: 8px 16px;
            background: {s['card_bg']};
            border: 1px solid {s['border']};
            border-radius: 8px;
        """)
        header.addWidget(self.stat_label)
        
        layout.addLayout(header)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara (Kod, Ünvan, Vergi No, Telefon)")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 14px;
                color: {s['text']};
                font-size: 13px;
                min-width: 280px;
            }}
            QLineEdit:focus {{ border-color: {s['primary']}; }}
        """)
        self.search_input.returnPressed.connect(self._on_search)
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
        
        self.tip_combo = QComboBox()
        self.tip_combo.addItem("📊 Tüm Tipler", None)
        self.tip_combo.addItem("🏢 Müşteri", "MUSTERI")
        self.tip_combo.addItem("🏭 Tedarikçi", "TEDARIKCI")
        self.tip_combo.addItem("🔄 Her İkisi", "BOTH")
        self.tip_combo.setStyleSheet(combo_style)
        self.tip_combo.currentIndexChanged.connect(self._on_filter_change)
        toolbar.addWidget(self.tip_combo)
        
        self.sehir_combo = QComboBox()
        self.sehir_combo.addItem("📍 Tüm Şehirler", None)
        self.sehir_combo.setStyleSheet(combo_style)
        self.sehir_combo.currentIndexChanged.connect(self._on_filter_change)
        toolbar.addWidget(self.sehir_combo)
        
        self.aktif_combo = QComboBox()
        self.aktif_combo.addItem("📊 Tüm Durumlar", None)
        self.aktif_combo.addItem("✅ Aktif", True)
        self.aktif_combo.addItem("❌ Pasif", False)
        self.aktif_combo.setStyleSheet(combo_style)
        self.aktif_combo.currentIndexChanged.connect(self._on_filter_change)
        toolbar.addWidget(self.aktif_combo)
        
        toolbar.addStretch()

        toolbar.addWidget(self.create_export_button(title="Cari Kartlari"))

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
            QPushButton:hover {{ background: {s['border']}; border-color: {s['primary']}; }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(refresh_btn)

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
            QTableWidget::item:selected {{ background: {s['primary']}; }}
            QTableWidget::item:hover {{ background: rgba(220, 38, 38, 0.1); }}
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
        self.table.setHorizontalHeaderLabels(["Cari Kodu", "Ünvan", "Tip", "Şehir", "Telefon", "E-posta", "Vade", "Durum"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 180)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 90)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.table, 1)
        
        # Sayfalama
        paging = QFrame()
        paging.setFixedHeight(60)
        paging.setStyleSheet(f"""
            QFrame {{
                background: {s['card_solid']};
                border: 1px solid {s['border']};
                border-radius: 10px;
            }}
        """)
        p_layout = QHBoxLayout(paging)
        p_layout.setContentsMargins(20, 0, 20, 0)
        
        self.total_label = QLabel("")
        self.total_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px;")
        p_layout.addWidget(self.total_label)
        p_layout.addStretch()
        
        btn_style = f"""
            QPushButton {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {s['border']}; border-color: {s['primary']}; }}
            QPushButton:disabled {{ color: {s['text_muted']}; background: {s['bg_main']}; }}
        """
        
        self.prev_btn = QPushButton("◀ Önceki")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet(btn_style)
        self.prev_btn.clicked.connect(self._prev_page)
        p_layout.addWidget(self.prev_btn)
        
        self.page_label = QLabel("Sayfa 1 / 1")
        self.page_label.setStyleSheet(f"color: {s['text']}; margin: 0 16px; font-size: 13px;")
        p_layout.addWidget(self.page_label)
        
        self.next_btn = QPushButton("Sonraki ▶")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(btn_style)
        self.next_btn.clicked.connect(self._next_page)
        p_layout.addWidget(self.next_btn)
        
        layout.addWidget(paging)
        self._load_filters()
    
    # ========== DATA METHODS (UNCHANGED) ==========
    def _load_filters(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT DISTINCT s.id, s.ad FROM musteri.cariler c JOIN tanim.sehirler s ON c.sehir_id = s.id WHERE c.aktif_mi = 1 ORDER BY s.ad""")
            for row in cursor.fetchall():
                self.sehir_combo.addItem(row[1], row[0])
            conn.close()
        except Exception as e:
            print(f"Filtre yükleme hatası: {e}")
    
    def _load_data(self):
        s = self.s
        self.stat_label.setText("Yükleniyor...")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            where_conditions = ["(c.silindi_mi = 0 OR c.silindi_mi IS NULL)"]
            params = []
            
            arama = self.search_input.text().strip()
            if arama:
                where_conditions.append("(c.cari_kodu LIKE ? OR c.unvan LIKE ? OR c.vergi_no LIKE ? OR c.telefon LIKE ? OR c.zirve_cari_kodu LIKE ?)")
                params.extend([f"%{arama}%"] * 5)
            
            tip = self.tip_combo.currentData()
            if tip:
                where_conditions.append("c.cari_tipi = ?")
                params.append(tip)
            
            sehir = self.sehir_combo.currentData()
            if sehir:
                where_conditions.append("c.sehir_id = ?")
                params.append(sehir)
            
            aktif = self.aktif_combo.currentData()
            if aktif is not None:
                where_conditions.append("ISNULL(c.aktif_mi, 1) = ?")
                params.append(1 if aktif else 0)
            
            where_clause = " AND ".join(where_conditions)
            
            cursor.execute(f"SELECT COUNT(*) FROM musteri.cariler c WHERE {where_clause}", params)
            self.total_items = cursor.fetchone()[0]
            self.total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)
            
            offset = (self.current_page - 1) * self.page_size
            cursor.execute(f"""
                SELECT c.id, c.cari_kodu, c.unvan, c.cari_tipi, s.ad, c.telefon, c.email, c.odeme_vade_gun, c.aktif_mi
                FROM musteri.cariler c
                LEFT JOIN tanim.sehirler s ON c.sehir_id = s.id
                WHERE {where_clause}
                ORDER BY c.unvan
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, params + [offset, self.page_size])
            
            items = []
            for row in cursor.fetchall():
                items.append({'id': row[0], 'cari_kodu': row[1], 'unvan': row[2], 'cari_tipi': row[3], 'sehir': row[4], 'telefon': row[5], 'email': row[6], 'vade': row[7], 'aktif': row[8] if row[8] is not None else 1})
            
            conn.close()
            self._populate_table(items)
            self._update_paging()
            self.stat_label.setText(f"📊 Toplam: {self.total_items:,} kayıt")
        except Exception as e:
            self.stat_label.setText(f"⚠️ Hata: {str(e)}")
    
    def _populate_table(self, items):
        s = self.s
        tip_display = {'MUSTERI': '🏢 Müşteri', 'TEDARIKCI': '🏭 Tedarikçi', 'BOTH': '🔄 Her İkisi'}
        
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('cari_kodu') or '')))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('unvan') or '')))
            self.table.setItem(row, 2, QTableWidgetItem(tip_display.get(item.get('cari_tipi'), item.get('cari_tipi') or '')))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('sehir') or '')))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('telefon') or '')))
            self.table.setItem(row, 5, QTableWidgetItem(str(item.get('email') or '')))
            
            vade_item = QTableWidgetItem(f"{item.get('vade') or 0} gün")
            vade_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, vade_item)
            
            aktif = item.get('aktif', 1)
            durum = QTableWidgetItem("✓ Aktif" if aktif else "✗ Pasif")
            durum.setForeground(QColor(s['success']) if aktif else QColor(s['error']))
            durum.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 7, durum)
            
            self.table.item(row, 0).setData(Qt.UserRole, item.get('id'))
            self.table.setRowHeight(row, 48)
    
    def _update_paging(self):
        self.page_label.setText(f"Sayfa {self.current_page} / {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
        start = (self.current_page - 1) * self.page_size + 1
        end = min(self.current_page * self.page_size, self.total_items)
        self.total_label.setText(f"{start:,} - {end:,} / {self.total_items:,}")
    
    def _on_search(self):
        self.current_page = 1
        self._load_data()
    
    def _on_filter_change(self):
        self.current_page = 1
        self._load_data()
    
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load_data()
    
    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._load_data()
    
    def _on_row_double_click(self, index):
        row = index.row()
        cari_id = self.table.item(row, 0).data(Qt.UserRole)
        if cari_id:
            dialog = CariDetayDialog(cari_id, self.theme, self)
            dialog.exec()
            self._load_data()
