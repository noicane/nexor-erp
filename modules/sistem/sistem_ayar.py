# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Sistem Ayarları Sayfası
Tema, renk, menü stili ve logo ayarları
"""
import os

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QFileDialog, QScrollArea, QWidget, QLineEdit, QMessageBox
)
from PySide6.QtCore import Signal, Qt

from components.base_page import BasePage
from themes import COLOR_PRESETS
from core.external_config import config_manager


class SistemAyarPage(BasePage):
    """Sistem Ayarları Sayfası"""
    settings_changed = Signal(str, str, bool, str)  # mode, color, expanded, logo
    
    def __init__(self, theme: dict, mode: str = "dark", color: str = "blue", expanded: bool = True, logo: str = None):
        super().__init__(theme)
        self.current_mode = mode
        self.current_color = color
        self.expanded = expanded
        self.logo = logo
        self._setup_ui()
    
    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Başlık
        header = QFrame()
        header.setStyleSheet(f"background: {self.theme['bg_card']}; border: 1px solid {self.theme['border']}; border-radius: 12px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        title_icon = QLabel("⚙️")
        title_icon.setStyleSheet("font-size: 28px; background: transparent;")
        header_layout.addWidget(title_icon)
        
        title_text = QVBoxLayout()
        title = QLabel("Sistem Ayarları")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 22px; font-weight: bold;")
        subtitle = QLabel("Tema, renkler ve görünüm ayarları")
        subtitle.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 13px;")
        title_text.addWidget(title)
        title_text.addWidget(subtitle)
        header_layout.addLayout(title_text)
        header_layout.addStretch()
        layout.addWidget(header)
        
        # === TEMA MODU ===
        tema_group = self._create_section("🌓", "Tema Modu", "Aydınlık veya karanlık tema seçin")
        t_content = QHBoxLayout()
        t_content.setSpacing(12)
        
        self.dark_btn = self._create_toggle_btn("🌙 Koyu Tema", self.current_mode == "dark")
        self.dark_btn.clicked.connect(lambda: self._on_mode_change("dark"))
        t_content.addWidget(self.dark_btn)
        
        self.light_btn = self._create_toggle_btn("☀️ Açık Tema", self.current_mode == "light")
        self.light_btn.clicked.connect(lambda: self._on_mode_change("light"))
        t_content.addWidget(self.light_btn)
        t_content.addStretch()
        tema_group.layout().addLayout(t_content)
        layout.addWidget(tema_group)
        
        # === RENK PALETİ ===
        renk_group = self._create_section("🎨", "Renk Paleti", "Uygulamanın ana rengini seçin")
        r_content = QHBoxLayout()
        r_content.setSpacing(12)
        
        self.color_btns = {}
        for key, val in COLOR_PRESETS.items():
            btn = QPushButton(val['name'])
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(44)
            btn.setMinimumWidth(100)
            self._style_color_btn(btn, val, key == self.current_color)
            btn.clicked.connect(lambda checked, k=key: self._on_color_change(k))
            self.color_btns[key] = btn
            r_content.addWidget(btn)
        r_content.addStretch()
        renk_group.layout().addLayout(r_content)
        layout.addWidget(renk_group)
        
        # === MENÜ STİLİ ===
        menu_group = self._create_section("📐", "Menü Stili", "Sidebar görünümünü ayarlayın")
        m_content = QHBoxLayout()
        m_content.setSpacing(12)
        
        self.expanded_btn = self._create_toggle_btn("📖 Genişletilmiş", self.expanded)
        self.expanded_btn.clicked.connect(lambda: self._on_menu_change(True))
        m_content.addWidget(self.expanded_btn)
        
        self.compact_btn = self._create_toggle_btn("📱 Kompakt", not self.expanded)
        self.compact_btn.clicked.connect(lambda: self._on_menu_change(False))
        m_content.addWidget(self.compact_btn)
        m_content.addStretch()
        menu_group.layout().addLayout(m_content)
        layout.addWidget(menu_group)
        
        # === LOGO ===
        logo_group = self._create_section("🖼️", "Logo", "Uygulama logosu ayarlayın")
        l_content = QHBoxLayout()
        l_content.setSpacing(12)
        
        self.logo_btn = QPushButton("📁 Logo Seç")
        self.logo_btn.setCursor(Qt.PointingHandCursor)
        self.logo_btn.setStyleSheet(self._normal_btn_style())
        self.logo_btn.clicked.connect(self._on_logo_select)
        l_content.addWidget(self.logo_btn)
        
        self.logo_clear = QPushButton("🗑️ Temizle")
        self.logo_clear.setCursor(Qt.PointingHandCursor)
        self.logo_clear.setStyleSheet(self._normal_btn_style())
        self.logo_clear.clicked.connect(self._on_logo_clear)
        l_content.addWidget(self.logo_clear)
        
        self.logo_label = QLabel(self.logo.split("/")[-1] if self.logo else "Logo seçilmedi")
        self.logo_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 12px;")
        l_content.addWidget(self.logo_label)
        l_content.addStretch()
        logo_group.layout().addLayout(l_content)
        layout.addWidget(logo_group)
        
        # === NAS SUNUCU AYARLARI ===
        nas_group = self._create_section("🖥️", "NAS Sunucu Ayarları", "NAS sunucu adresi (hostname veya IP)")
        nas_content = QVBoxLayout()
        nas_content.setSpacing(12)

        nas_row1 = QHBoxLayout()
        nas_row1.setSpacing(12)

        nas_label = QLabel("Sunucu Adresi:")
        nas_label.setStyleSheet(f"color: {self.theme['text']}; font-size: 13px; background: transparent;")
        nas_label.setFixedWidth(120)
        nas_row1.addWidget(nas_label)

        self.nas_server_edit = QLineEdit()
        self.nas_server_edit.setText(config_manager.get_nas_server())
        self.nas_server_edit.setPlaceholderText("AtlasNAS veya 192.168.10.x")
        self.nas_server_edit.setFixedHeight(40)
        self.nas_server_edit.setStyleSheet(
            f"QLineEdit {{ background: {self.theme['bg_input']}; color: {self.theme['text']}; "
            f"border: 1px solid {self.theme['border']}; border-radius: 8px; padding: 8px 12px; font-size: 13px; }}"
            f"QLineEdit:focus {{ border-color: {self.theme['primary']}; }}"
        )
        nas_row1.addWidget(self.nas_server_edit)
        nas_content.addLayout(nas_row1)

        nas_row2 = QHBoxLayout()
        nas_row2.setSpacing(12)

        self.nas_test_btn = QPushButton("Baglantiyi Test Et")
        self.nas_test_btn.setCursor(Qt.PointingHandCursor)
        self.nas_test_btn.setFixedHeight(40)
        self.nas_test_btn.setStyleSheet(self._normal_btn_style())
        self.nas_test_btn.clicked.connect(self._on_nas_test)
        nas_row2.addWidget(self.nas_test_btn)

        self.nas_save_btn = QPushButton("Kaydet")
        self.nas_save_btn.setCursor(Qt.PointingHandCursor)
        self.nas_save_btn.setFixedHeight(40)
        self.nas_save_btn.setStyleSheet(
            f"QPushButton {{ background: {self.theme['primary']}; color: white; "
            f"border: none; border-radius: 8px; padding: 10px 24px; font-weight: bold; font-size: 13px; }}"
            f"QPushButton:hover {{ background: {self.theme.get('primary_dark', self.theme['primary'])}; }}"
        )
        self.nas_save_btn.clicked.connect(self._on_nas_save)
        nas_row2.addWidget(self.nas_save_btn)

        self.nas_status_label = QLabel("")
        self.nas_status_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 12px; background: transparent;")
        nas_row2.addWidget(self.nas_status_label)
        nas_row2.addStretch()
        nas_content.addLayout(nas_row2)

        nas_group.layout().addLayout(nas_content)
        layout.addWidget(nas_group)

        # === ÖNİZLEME ===
        preview_group = self._create_section("👁️", "Renk Önizleme", "Seçilen renk paletinin önizlemesi")
        self.preview_widget = QWidget()
        self.preview_widget.setStyleSheet("background: transparent;")
        self._update_preview()
        preview_group.layout().addWidget(self.preview_widget)
        layout.addWidget(preview_group)
        
        layout.addStretch()
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def _create_section(self, icon: str, title: str, subtitle: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"background: {self.theme['bg_card']}; border: 1px solid {self.theme['border']}; border-radius: 12px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px; background: transparent;")
        header.addWidget(icon_lbl)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {self.theme['text']}; font-weight: bold; font-size: 15px;")
        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 12px;")
        title_layout.addWidget(title_lbl)
        title_layout.addWidget(subtitle_lbl)
        header.addLayout(title_layout)
        header.addStretch()
        layout.addLayout(header)
        return frame
    
    def _create_toggle_btn(self, text: str, active: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(44)
        btn.setMinimumWidth(140)
        self._style_toggle_btn(btn, active)
        return btn
    
    def _style_toggle_btn(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet(f"QPushButton {{ background: {self.theme['gradient_css']}; color: white; border: none; border-radius: 10px; padding: 10px 24px; font-weight: bold; font-size: 13px; }} QPushButton:hover {{ background: {self.theme['primary']}; }}")
        else:
            btn.setStyleSheet(f"QPushButton {{ background: {self.theme['bg_input']}; color: {self.theme['text']}; border: 1px solid {self.theme['border']}; border-radius: 10px; padding: 10px 24px; font-size: 13px; }} QPushButton:hover {{ border-color: {self.theme['primary']}; background: {self.theme['bg_hover']}; }}")
    
    def _style_color_btn(self, btn: QPushButton, preset: dict, active: bool):
        border = "3px solid white" if active else "3px solid transparent"
        btn.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {preset['start']}, stop:1 {preset['end']}); color: white; border: {border}; border-radius: 10px; padding: 10px 20px; font-weight: bold; font-size: 13px; }} QPushButton:hover {{ border: 3px solid #DDDDDD; }}")
    
    def _normal_btn_style(self) -> str:
        return f"QPushButton {{ background: {self.theme['bg_input']}; color: {self.theme['text']}; border: 1px solid {self.theme['border']}; border-radius: 8px; padding: 10px 16px; font-size: 13px; }} QPushButton:hover {{ border-color: {self.theme['primary']}; background: {self.theme['bg_hover']}; }}"
    
    def _update_buttons(self):
        self._style_toggle_btn(self.dark_btn, self.current_mode == "dark")
        self._style_toggle_btn(self.light_btn, self.current_mode == "light")
        self._style_toggle_btn(self.expanded_btn, self.expanded)
        self._style_toggle_btn(self.compact_btn, not self.expanded)
        for key, btn in self.color_btns.items():
            self._style_color_btn(btn, COLOR_PRESETS[key], key == self.current_color)
    
    def _update_preview(self):
        # Eski layout'u sil
        if self.preview_widget.layout():
            old_layout = self.preview_widget.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old_layout)
        
        # Yeni layout oluştur
        new_layout = QHBoxLayout(self.preview_widget)
        new_layout.setContentsMargins(0, 0, 0, 0)
        new_layout.setSpacing(12)
        
        preset = COLOR_PRESETS.get(self.current_color, COLOR_PRESETS['blue'])
        colors = [
            ("Gradient", f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {preset['start']}, stop:1 {preset['end']})"),
            ("Primary", preset['start']),
            ("Secondary", preset['end']),
            ("Success", "#22c55e"),
            ("Warning", "#f59e0b"),
            ("Error", "#ef4444"),
        ]
        
        for name, color in colors:
            card = QFrame()
            card.setFixedSize(100, 70)
            card.setStyleSheet(f"background: {color}; border-radius: 10px;")
            card_layout = QVBoxLayout(card)
            card_layout.setAlignment(Qt.AlignCenter)
            lbl = QLabel(name)
            lbl.setStyleSheet("color: white; font-weight: bold; font-size: 11px; background: transparent;")
            lbl.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(lbl)
            new_layout.addWidget(card)
        new_layout.addStretch()
    
    def _on_mode_change(self, mode: str):
        self.current_mode = mode
        self._update_buttons()
        self.settings_changed.emit(self.current_mode, self.current_color, self.expanded, self.logo)
    
    def _on_color_change(self, color: str):
        self.current_color = color
        self._update_buttons()
        self._update_preview()
        self.settings_changed.emit(self.current_mode, self.current_color, self.expanded, self.logo)
    
    def _on_menu_change(self, expanded: bool):
        self.expanded = expanded
        self._update_buttons()
        self.settings_changed.emit(self.current_mode, self.current_color, self.expanded, self.logo)
    
    def _on_logo_select(self):
        file, _ = QFileDialog.getOpenFileName(self, "Logo Seç", "", "Images (*.png *.jpg *.jpeg *.svg)")
        if file:
            self.logo = file
            self.logo_label.setText(file.split("/")[-1])
            self.settings_changed.emit(self.current_mode, self.current_color, self.expanded, self.logo)
    
    def _on_logo_clear(self):
        self.logo = None
        self.logo_label.setText("Logo seçilmedi")
        self.settings_changed.emit(self.current_mode, self.current_color, self.expanded, self.logo)
    
    def _on_nas_test(self):
        """NAS baglanti testi"""
        server = self.nas_server_edit.text().strip()
        if not server:
            self.nas_status_label.setText("Sunucu adresi bos!")
            self.nas_status_label.setStyleSheet(f"color: #ef4444; font-size: 12px; background: transparent;")
            return

        self.nas_status_label.setText("Test ediliyor...")
        self.nas_status_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 12px; background: transparent;")
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        nas_path = rf"\\{server}"
        if os.path.exists(nas_path):
            self.nas_status_label.setText(f"Baglanti basarili: {nas_path}")
            self.nas_status_label.setStyleSheet("color: #22c55e; font-size: 12px; background: transparent;")
        else:
            self.nas_status_label.setText(f"Baglanti kurulamadi: {nas_path}")
            self.nas_status_label.setStyleSheet("color: #ef4444; font-size: 12px; background: transparent;")

    def _on_nas_save(self):
        """NAS sunucu adresini kaydet"""
        server = self.nas_server_edit.text().strip()
        if not server:
            QMessageBox.warning(self, "Uyari", "Sunucu adresi bos olamaz!")
            return

        config_manager.set_nas_server(server)
        if config_manager.save():
            self.nas_status_label.setText(f"Kaydedildi: {server} (Yeniden baslatma gerekir)")
            self.nas_status_label.setStyleSheet("color: #22c55e; font-size: 12px; background: transparent;")
            QMessageBox.information(
                self, "Basarili",
                f"NAS sunucu adresi '{server}' olarak kaydedildi.\n\n"
                "Degisikliklerin etkin olmasi icin programi yeniden baslatin."
            )
        else:
            self.nas_status_label.setText("Kaydetme hatasi!")
            self.nas_status_label.setStyleSheet("color: #ef4444; font-size: 12px; background: transparent;")

    def update_theme(self, theme: dict):
        self.theme = theme
        self._apply_global_style()
