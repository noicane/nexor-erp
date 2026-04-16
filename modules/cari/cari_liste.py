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
from core.nexor_brand import brand
from config import DEFAULT_PAGE_SIZE


# ============================================================================
# MODERN STYLE HELPER — artik brand'den okuyor
# ============================================================================
def get_modern_style(theme: dict = None) -> dict:
    """Brand sisteminden snapshot dict uret.

    NOT: Her cagrida taze degerler doner. Tema modu degistiginde self.s'i
    yeniden olusturup update_theme icinde stilleri tekrar uygulamak gerek.
    """
    return {
        # Colors
        'card_bg':        brand.BG_CARD,
        'card_solid':     brand.BG_CARD,
        'input_bg':       brand.BG_INPUT,
        'bg_main':        brand.BG_MAIN,
        'bg_hover':       brand.BG_HOVER,
        'bg_selected':    brand.BG_SELECTED,
        'border':         brand.BORDER,
        'border_light':   brand.BORDER_HARD,
        'border_input':   brand.BORDER,
        'text':           brand.TEXT,
        'text_secondary': brand.TEXT_MUTED,
        'text_muted':     brand.TEXT_DIM,
        'primary':        brand.PRIMARY,
        'primary_hover':  brand.PRIMARY_HOVER,
        'success':        brand.SUCCESS,
        'warning':        brand.WARNING,
        'error':          brand.ERROR,
        'danger':         brand.ERROR,
        'info':           brand.INFO,
        'gradient':       brand.PRIMARY,
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
        header = QFrame()
        header.setFixedHeight(brand.sp(64))
        header.setStyleSheet(
            f"QFrame {{ background: {brand.BG_MAIN}; "
            f"border-bottom: 1px solid {brand.BORDER}; }}"
        )
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(brand.SP_6, 0, brand.SP_4, 0)
        h_layout.setSpacing(brand.SP_3)

        cari_tipi = self.cari_data.get('cari_tipi', 'MUSTERI')
        title = QLabel(
            f"{self.cari_data.get('cari_kodu', '')} — "
            f"{self.cari_data.get('unvan', '')}"
        )
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"letter-spacing: -0.2px; "
            f"background: transparent; border: none;"
        )
        title.setWordWrap(True)
        h_layout.addWidget(title, 1)

        # Tip + Durum — kucuk badge'ler (pill'ler)
        tip_label_text = {
            'MUSTERI': 'Müşteri', 'TEDARIKCI': 'Tedarikçi', 'BOTH': 'İkisi'
        }.get(cari_tipi, cari_tipi or 'Müşteri')
        tip_color = {
            'MUSTERI': brand.INFO, 'TEDARIKCI': brand.SUCCESS, 'BOTH': brand.PRIMARY
        }.get(cari_tipi, brand.TEXT_MUTED)
        tip_label = self._make_pill(tip_label_text, tip_color)
        h_layout.addWidget(tip_label)

        is_aktif = self.cari_data.get('aktif_mi', 1)
        durum_color = brand.SUCCESS if is_aktif else brand.ERROR
        self.aktif_label = self._make_pill(
            "Aktif" if is_aktif else "Pasif", durum_color
        )
        h_layout.addWidget(self.aktif_label)

        h_layout.addSpacing(brand.SP_2)

        # Butonlar — ince ghost + primary
        self.toggle_aktif_btn = QPushButton("Pasif Yap" if is_aktif else "Aktif Yap")
        self.toggle_aktif_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_aktif_btn.setFixedHeight(brand.sp(34))
        self.toggle_aktif_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {brand.TEXT_MUTED};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
                color: {brand.TEXT};
            }}
        """)
        self.toggle_aktif_btn.clicked.connect(self._toggle_aktif)
        h_layout.addWidget(self.toggle_aktif_btn)

        self.edit_btn = QPushButton("Düzenle")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedHeight(brand.sp(34))
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        self.edit_btn.clicked.connect(self._toggle_edit_mode)
        h_layout.addWidget(self.edit_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(brand.sp(34), brand.sp(34))
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {brand.TEXT_DIM};
                border: 1px solid {brand.BORDER};
                font-size: {brand.fs(14)}px;
                border-radius: {brand.R_SM}px;
            }}
            QPushButton:hover {{
                background: {brand.ERROR_SOFT};
                color: {brand.ERROR};
                border-color: {brand.ERROR};
            }}
        """)
        close_btn.clicked.connect(self.close)
        h_layout.addWidget(close_btn)

        return header

    def _make_pill(self, text: str, color: str) -> QLabel:
        """Kucuk, sakin badge — metin + soft arkaplan + ince border."""
        c = QColor(color)
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedHeight(brand.sp(26))
        lbl.setStyleSheet(f"""
            color: {color};
            background: rgba({c.red()},{c.green()},{c.blue()},0.12);
            border: 1px solid rgba({c.red()},{c.green()},{c.blue()},0.35);
            border-radius: {brand.R_SM}px;
            padding: 0 {brand.SP_3}px;
            font-size: {brand.FS_CAPTION}px;
            font-weight: {brand.FW_SEMIBOLD};
        """)
        return lbl
    
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

            # Badge'i yeniden stille (brand pill)
            color = brand.SUCCESS if is_aktif else brand.ERROR
            c = QColor(color)
            self.aktif_label.setText("Aktif" if is_aktif else "Pasif")
            self.aktif_label.setStyleSheet(f"""
                color: {color};
                background: rgba({c.red()},{c.green()},{c.blue()},0.12);
                border: 1px solid rgba({c.red()},{c.green()},{c.blue()},0.35);
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_3}px;
                font-size: {brand.FS_CAPTION}px;
                font-weight: {brand.FW_SEMIBOLD};
            """)

            # Toggle buton — ghost stil korunuyor, sadece yazi degisir
            self.toggle_aktif_btn.setText("Pasif Yap" if is_aktif else "Aktif Yap")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Durum değiştirilemedi: {e}")


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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_8, brand.SP_8, brand.SP_8, brand.SP_8)
        layout.setSpacing(brand.SP_6)

        # ================ HEADER ================
        header = QHBoxLayout()
        header.setSpacing(brand.SP_4)

        title_section = QVBoxLayout()
        title_section.setSpacing(brand.SP_1)

        self.title_label = QLabel("Cari Kartları")
        title_section.addWidget(self.title_label)

        self.subtitle_label = QLabel("Müşteri ve tedarikçi kartlarını yönetin")
        title_section.addWidget(self.subtitle_label)

        header.addLayout(title_section)
        header.addStretch()

        self.stat_label = QLabel("")
        header.addWidget(self.stat_label)

        layout.addLayout(header)

        # ================ TOOLBAR ================
        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara (Kod, Ünvan, Vergi No, Telefon)")
        self.search_input.setFixedHeight(brand.sp(40))
        self.search_input.setMinimumWidth(brand.sp(300))
        self.search_input.returnPressed.connect(self._on_search)
        toolbar.addWidget(self.search_input)

        self.tip_combo = QComboBox()
        self.tip_combo.addItem("Tüm Tipler", None)
        self.tip_combo.addItem("Müşteri", "MUSTERI")
        self.tip_combo.addItem("Tedarikçi", "TEDARIKCI")
        self.tip_combo.addItem("Her İkisi", "BOTH")
        self.tip_combo.setFixedHeight(brand.sp(40))
        self.tip_combo.currentIndexChanged.connect(self._on_filter_change)
        toolbar.addWidget(self.tip_combo)

        self.sehir_combo = QComboBox()
        self.sehir_combo.addItem("Tüm Şehirler", None)
        self.sehir_combo.setFixedHeight(brand.sp(40))
        self.sehir_combo.currentIndexChanged.connect(self._on_filter_change)
        toolbar.addWidget(self.sehir_combo)

        self.aktif_combo = QComboBox()
        self.aktif_combo.addItem("Aktif", True)
        self.aktif_combo.setFixedHeight(brand.sp(40))
        self.aktif_combo.currentIndexChanged.connect(self._on_filter_change)
        toolbar.addWidget(self.aktif_combo)

        toolbar.addStretch()

        toolbar.addWidget(self.create_export_button(title="Cari Kartlari"))

        self.refresh_btn = QPushButton("Yenile")
        self.refresh_btn.setToolTip("Listeyi yenile")
        self.refresh_btn.setFixedHeight(brand.sp(40))
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(self.refresh_btn)

        self.zirve_btn = QPushButton("Zirve Senkron")
        self.zirve_btn.setToolTip("Zirve Ticari'den cari kartlarını senkronize et")
        self.zirve_btn.setFixedHeight(brand.sp(40))
        self.zirve_btn.setCursor(Qt.PointingHandCursor)
        self.zirve_btn.clicked.connect(self._zirve_senkron)
        toolbar.addWidget(self.zirve_btn)

        layout.addLayout(toolbar)

        # ================ TABLE ================
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Cari Kodu", "Ünvan", "Tip", "Şehir", "Telefon", "E-posta", "Vade", "Durum"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, brand.sp(130))
        self.table.setColumnWidth(2, brand.sp(120))
        self.table.setColumnWidth(3, brand.sp(110))
        self.table.setColumnWidth(4, brand.sp(140))
        self.table.setColumnWidth(5, brand.sp(200))
        self.table.setColumnWidth(6, brand.sp(80))
        self.table.setColumnWidth(7, brand.sp(100))
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(44))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.doubleClicked.connect(self._on_row_double_click)
        self.table.setFrameShape(QFrame.NoFrame)
        layout.addWidget(self.table, 1)
        
        # ================ SAYFALAMA ================
        self.paging_frame = QFrame()
        self.paging_frame.setFixedHeight(brand.sp(56))
        p_layout = QHBoxLayout(self.paging_frame)
        p_layout.setContentsMargins(brand.SP_5, 0, brand.SP_5, 0)

        self.total_label = QLabel("")
        p_layout.addWidget(self.total_label)
        p_layout.addStretch()

        self.prev_btn = QPushButton("‹  Önceki")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setFixedHeight(brand.sp(36))
        self.prev_btn.clicked.connect(self._prev_page)
        p_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("Sayfa 1 / 1")
        p_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("Sonraki  ›")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setFixedHeight(brand.sp(36))
        self.next_btn.clicked.connect(self._next_page)
        p_layout.addWidget(self.next_btn)

        layout.addWidget(self.paging_frame)

        # Tum stilleri brand'den uygula
        self._apply_page_styles()
        self._load_filters()

    # =============================================================
    # STIL UYGULAMA (tek noktadan) — tema degiste tekrar cagrilir
    # =============================================================
    def _apply_page_styles(self):
        self.setStyleSheet(f"""
            QWidget {{ background: {brand.BG_MAIN}; color: {brand.TEXT}; }}
        """)

        # Baslik + alt yazi
        self.title_label.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_TITLE_LG}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"letter-spacing: -0.4px; "
            f"background: transparent; border: none;"
        )
        self.subtitle_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY}px; "
            f"background: transparent; border: none;"
        )
        self.stat_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"padding: {brand.SP_2}px {brand.SP_4}px; "
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_SM}px;"
        )

        # Search
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus {{ border-color: {brand.PRIMARY}; background: {brand.BG_HOVER}; }}
        """)

        # Combo stil (tek tanim, hepsine uygulanir)
        combo_style = f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_3}px;
                color: {brand.TEXT};
                min-width: {brand.sp(130)}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:hover {{ border-color: {brand.BORDER_HARD}; }}
            QComboBox::drop-down {{ border: none; width: {brand.sp(28)}px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                color: {brand.TEXT};
                selection-background-color: {brand.PRIMARY};
                outline: 0;
                padding: {brand.SP_1}px;
            }}
        """
        self.tip_combo.setStyleSheet(combo_style)
        self.sehir_combo.setStyleSheet(combo_style)
        self.aktif_combo.setStyleSheet(combo_style)

        # Yenile / Zirve butonlari
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
            }}
        """)
        self.zirve_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)

        # Table
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: 0;
                font-size: {brand.FS_BODY}px;
            }}
            QTableWidget::item {{
                padding: 0 {brand.SP_4}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
            }}
            QTableWidget::item:selected {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT};
            }}
            QHeaderView::section {{
                background: transparent;
                color: {brand.TEXT_DIM};
                padding: {brand.SP_3}px {brand.SP_4}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
                font-size: {brand.FS_CAPTION}px;
                font-weight: {brand.FW_SEMIBOLD};
                text-transform: uppercase;
                letter-spacing: 0.6px;
            }}
            QTableWidget QTableCornerButton::section {{
                background: transparent; border: none;
            }}
        """)

        # Sayfalama
        self.paging_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        self.total_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"background: transparent; border: none;"
        )
        self.page_label.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_MEDIUM}; "
            f"margin: 0 {brand.SP_4}px; "
            f"background: transparent; border: none;"
        )
        page_btn_style = f"""
            QPushButton {{
                background: transparent;
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.PRIMARY};
            }}
            QPushButton:disabled {{
                color: {brand.TEXT_DISABLED};
                border-color: {brand.BORDER};
            }}
        """
        self.prev_btn.setStyleSheet(page_btn_style)
        self.next_btn.setStyleSheet(page_btn_style)

    # =============================================================
    # TEMA DEGISIMI
    # =============================================================
    def update_theme(self, theme: dict = None):
        """Tema modu degistiginde brand'den yeni stilleri uygula."""
        self.theme = theme
        self.s = get_modern_style(theme)
        self._apply_page_styles()
        # Tabloyu yeniden renklendirmek icin satirlari tekrar populate et
        try:
            self._load_data()
        except Exception:
            pass
    
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
            
            where_conditions = ["(c.silindi_mi = 0 OR c.silindi_mi IS NULL)", "ISNULL(c.aktif_mi, 1) = 1"]
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
    
    def _zirve_senkron(self):
        """Zirve'den cari kartlarını senkronize et"""
        reply = QMessageBox.question(
            self, "Zirve Cari Senkron",
            "Zirve Ticari'deki (ATLAS_KATAFOREZ_2026T) tüm cari kartları\n"
            "Nexor'a senkronize edilecek.\n\n"
            "- Yeni cariler eklenecek\n"
            "- Mevcut cariler güncellenecek\n\n"
            "Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            from core.zirve_entegrasyon import zirve_cari_senkronla
            sonuc = zirve_cari_senkronla()

            if sonuc.get('hata'):
                QMessageBox.critical(self, "Hata", f"Senkronizasyon hatası:\n{sonuc['hata']}")
                return

            mesaj = (
                f"Senkronizasyon tamamlandı!\n\n"
                f"Zirve'deki toplam cari: {sonuc['toplam_zirve']}\n"
                f"Yeni eklenen: {sonuc['eklenen']}\n"
                f"Güncellenen: {sonuc['guncellenen']}"
            )
            if sonuc.get('hatalar'):
                mesaj += f"\n\nHatalı kayıtlar ({len(sonuc['hatalar'])}):\n"
                for h in sonuc['hatalar'][:5]:
                    mesaj += f"  - {h}\n"
                if len(sonuc['hatalar']) > 5:
                    mesaj += f"  ... ve {len(sonuc['hatalar']) - 5} daha"

            QMessageBox.information(self, "Zirve Cari Senkron", mesaj)
            self._load_data()

        except ImportError:
            QMessageBox.critical(self, "Hata", "Zirve entegrasyon modülü yüklenemedi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Beklenmeyen hata:\n{e}")

    def _on_row_double_click(self, index):
        row = index.row()
        cari_id = self.table.item(row, 0).data(Qt.UserRole)
        if cari_id:
            dialog = CariDetayDialog(cari_id, self.theme, self)
            dialog.exec()
            self._load_data()
