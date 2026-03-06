# -*- coding: utf-8 -*-
"""
NEXOR ERP - Modern Sidebar v3.0
Kompakt tasarim, tam uyumluluk

Eski Sidebar ile %100 uyumlu:
- Ayni __init__ parametreleri
- Ayni sinyaller (menu_clicked, theme_toggle_requested)
- Ayni metodlar (set_logo, set_dark_mode, set_active, update_theme, set_expanded, set_menu_expanded)
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
    QWidget, QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QCursor

from core.menu_structure import MENU_STRUCTURE
from core.yetki_manager import YetkiManager


# =============================================================================
# MENU ITEM
# =============================================================================

class MenuItem(QFrame):
    """Menu ogesi"""
    
    clicked = Signal(str)
    
    def __init__(self, item_id: str, label: str, icon: str, has_children: bool, 
                 is_child: bool, theme: dict, expanded_mode: bool):
        super().__init__()
        self.item_id = item_id
        self.label = label
        self.icon = icon
        self.has_children = has_children
        self.is_child = is_child
        self.theme = theme
        self.expanded_mode = expanded_mode
        self.is_active = False
        self.is_expanded = False
        self._setup_ui()
    
    def _setup_ui(self):
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        if self.expanded_mode:
            self.setFixedHeight(42 if not self.is_child else 38)
            layout = QHBoxLayout(self)
            layout.setContentsMargins(16 if not self.is_child else 48, 0, 12, 0)
            layout.setSpacing(12)
            
            # Icon
            if self.icon:
                self.icon_label = QLabel(self.icon)
                self.icon_label.setFixedWidth(24)
                self.icon_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(self.icon_label)
            
            # Text
            self.text_label = QLabel(self.label)
            self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            layout.addWidget(self.text_label)
            
            # Arrow
            if self.has_children:
                self.arrow = QLabel("›")
                self.arrow.setFixedWidth(16)
                layout.addWidget(self.arrow)
        else:
            # Compact mode
            self.setFixedSize(50, 50)
            self.setToolTip(self.label)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.icon_label = QLabel(self.icon if self.icon else "•")
            self.icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.icon_label)
        
        self._apply_style()
    
    def _apply_style(self):
        t = self.theme
        primary = t.get('primary', '#DC2626')
        
        if self.is_active:
            bg = primary
            text_color = "#FFFFFF"
            icon_color = "#FFFFFF"
        else:
            bg = "transparent"
            text_color = t.get('text_secondary', t.get('text', '#AAAAAA'))
            icon_color = t.get('text_muted', t.get('text_secondary', '#666666'))
        
        hover_bg = t.get('bg_hover', t.get('bg_card', '#252525'))

        if self.expanded_mode:
            self.setStyleSheet(f"""
                MenuItem {{
                    background: {bg};
                    border-radius: 10px;
                    margin: 2px 8px;
                }}
                MenuItem:hover {{
                    background: {hover_bg if not self.is_active else bg};
                }}
            """)
            
            if hasattr(self, 'text_label'):
                font_weight = '600' if self.is_active else '400'
                self.text_label.setStyleSheet(f"""
                    color: {text_color};
                    font-size: 13px;
                    font-weight: {font_weight};
                    background: transparent;
                """)
            
            if hasattr(self, 'icon_label'):
                self.icon_label.setStyleSheet(f"""
                    font-size: 18px;
                    color: {icon_color};
                    background: transparent;
                """)
            
            if self.has_children and hasattr(self, 'arrow'):
                arrow_char = "⌄" if self.is_expanded else "›"
                self.arrow.setText(arrow_char)
                self.arrow.setStyleSheet(f"""
                    color: {t.get('text_muted', t.get('text_secondary', '#666666'))};
                    font-size: 14px;
                    font-weight: bold;
                    background: transparent;
                """)
        else:
            # Compact mode
            self.setStyleSheet(f"""
                MenuItem {{
                    background: {bg};
                    border-radius: 12px;
                    margin: 4px;
                }}
                MenuItem:hover {{
                    background: {hover_bg if not self.is_active else bg};
                }}
            """)
            
            if hasattr(self, 'icon_label'):
                self.icon_label.setStyleSheet(f"""
                    font-size: 20px;
                    color: {icon_color if not self.is_active else '#FFFFFF'};
                    background: transparent;
                """)
    
    def set_active(self, active: bool):
        self.is_active = active
        self._apply_style()
    
    def set_expanded(self, expanded: bool):
        self.is_expanded = expanded
        self._apply_style()
    
    def update_theme(self, theme: dict):
        self.theme = theme
        self._apply_style()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.item_id)
        super().mousePressEvent(event)


# =============================================================================
# THEME TOGGLE BUTTON
# =============================================================================

class ThemeToggleButton(QFrame):
    """Tema degistirme butonu"""
    
    theme_toggled = Signal()
    
    def __init__(self, theme: dict, expanded_mode: bool, is_dark: bool):
        super().__init__()
        self.theme = theme
        self.expanded_mode = expanded_mode
        self.is_dark = is_dark
        self._setup_ui()
    
    def _setup_ui(self):
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        if self.expanded_mode:
            self.setFixedHeight(44)
            layout = QHBoxLayout(self)
            layout.setContentsMargins(16, 8, 16, 8)
            layout.setSpacing(12)
            
            # Icon
            self.icon_label = QLabel()
            self.icon_label.setFixedWidth(24)
            self.icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.icon_label)
            
            # Text
            self.text_label = QLabel()
            self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            layout.addWidget(self.text_label)
        else:
            self.setFixedSize(50, 50)
            self.setToolTip("Tema Değiştir")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.icon_label = QLabel()
            self.icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.icon_label)
        
        self._apply_style()
    
    def _apply_style(self):
        t = self.theme
        
        if self.is_dark:
            icon = "☀️"
            text = "Açık Tema"
        else:
            icon = "🌙"
            text = "Koyu Tema"
        
        self.icon_label.setText(icon)
        self.icon_label.setStyleSheet(f"""
            font-size: {'18px' if self.expanded_mode else '22px'};
            background: transparent;
        """)
        
        if self.expanded_mode and hasattr(self, 'text_label'):
            self.text_label.setText(text)
            self.text_label.setStyleSheet(f"""
                color: {t.get('text_secondary', t.get('text', '#AAAAAA'))};
                font-size: 13px;
                background: transparent;
            """)
        
        hover_bg = t.get('bg_hover', t.get('bg_card', '#252525'))
        border_color = t.get('border', t.get('border_light', '#2A2A2A'))
        
        self.setStyleSheet(f"""
            ThemeToggleButton {{
                background: {t.get('bg_card', t.get('bg_main', '#1A1A1A'))};
                border: 1px solid {border_color};
                border-radius: 10px;
                margin: 8px;
            }}
            ThemeToggleButton:hover {{
                background: {hover_bg};
            }}
        """)
    
    def set_dark_mode(self, is_dark: bool):
        self.is_dark = is_dark
        self._apply_style()
    
    def update_theme(self, theme: dict):
        self.theme = theme
        self._apply_style()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.theme_toggled.emit()
        super().mousePressEvent(event)


# =============================================================================
# SIDEBAR
# =============================================================================

class Sidebar(QFrame):
    """
    Modern Sidebar
    
    Eski Sidebar ile tam uyumlu.
    """
    
    menu_clicked = Signal(str)
    theme_toggle_requested = Signal()
    
    EXPANDED_WIDTH = 220
    COMPACT_WIDTH = 70
    
    def __init__(self, theme: dict, expanded_mode: bool = True, 
                 logo_path: str = None, is_dark_mode: bool = True):
        super().__init__()
        self.theme = theme
        self.expanded_mode = expanded_mode
        self.logo_path = logo_path
        self.is_dark_mode = is_dark_mode
        
        self.menu_items = {}
        self.child_containers = {}
        self.active_item_id = None
        
        # Yetki manager
        self.yetki_manager = YetkiManager()
        
        self._setup_ui()
    
    def _setup_ui(self):
        t = self.theme
        
        width = self.EXPANDED_WIDTH if self.expanded_mode else self.COMPACT_WIDTH
        self.setFixedWidth(width)
        
        self.setStyleSheet(f"""
            Sidebar {{
                background: {t.get('bg_sidebar', t.get('bg_main', '#0A0A0A'))};
                border-right: 1px solid {t.get('border', t.get('border_light', '#2A2A2A'))};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # === LOGO ===
        logo_frame = QFrame()
        logo_frame.setFixedHeight(70)
        logo_frame.setStyleSheet(f"""
            background: transparent;
            border-bottom: 1px solid {t.get('border', t.get('border_light', '#2A2A2A'))};
        """)
        
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 0, 16, 0)
        logo_layout.setSpacing(12)
        
        # Logo icon
        self.logo_icon = QLabel("N")
        self.logo_icon.setFixedSize(40, 40)
        self.logo_icon.setAlignment(Qt.AlignCenter)
        primary = t.get('primary', '#DC2626')
        self.logo_icon.setStyleSheet(f"""
            background: {primary};
            color: white;
            font-size: 20px;
            font-weight: 700;
            border-radius: 10px;
        """)
        logo_layout.addWidget(self.logo_icon)
        
        if self.expanded_mode:
            self.brand_label = QLabel("NEXOR")
            self.brand_label.setStyleSheet(f"""
                font-size: 20px;
                font-weight: 700;
                color: {t.get('text', '#FFFFFF')};
                background: transparent;
            """)
            logo_layout.addWidget(self.brand_label)
        
        logo_layout.addStretch()
        layout.addWidget(logo_frame)
        
        # === MENU SCROLL ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {t.get('border', t.get('border_light', '#2A2A2A'))};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {t.get('border_light', t.get('border', '#333333'))};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        menu_widget = QWidget()
        menu_widget.setStyleSheet("background: transparent;")
        self.menu_layout = QVBoxLayout(menu_widget)
        self.menu_layout.setContentsMargins(0, 12, 0, 12)
        self.menu_layout.setSpacing(2)
        
        self._build_menu()
        
        self.menu_layout.addStretch()
        scroll.setWidget(menu_widget)
        layout.addWidget(scroll, 1)
        
        # === FOOTER ===
        footer = QFrame()
        footer.setStyleSheet(f"""
            background: transparent;
            border-top: 1px solid {t.get('border', t.get('border_light', '#2A2A2A'))};
        """)
        
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 8)
        footer_layout.setSpacing(0)
        
        # Theme toggle
        self.theme_btn = ThemeToggleButton(self.theme, self.expanded_mode, self.is_dark_mode)
        self.theme_btn.theme_toggled.connect(self.theme_toggle_requested.emit)
        footer_layout.addWidget(self.theme_btn)
        
        layout.addWidget(footer)
    
    def _build_menu(self):
        """Menu yapisini olustur"""
        for item_data in MENU_STRUCTURE:
            item_id = item_data['id']
            
            # Yetki kontrolu
            if not self.yetki_manager.can_access_menu(item_id):
                continue
            
            has_children = bool(item_data.get('children'))
            
            item = MenuItem(
                item_id=item_id,
                label=item_data.get('label', item_id),
                icon=item_data.get('icon', '📄'),
                has_children=has_children,
                is_child=False,
                theme=self.theme,
                expanded_mode=self.expanded_mode
            )
            item.clicked.connect(self._on_item_clicked)
            
            self.menu_items[item_id] = item
            self.menu_layout.addWidget(item)
            
            # Alt menuler
            if has_children and self.expanded_mode:
                child_container = QWidget()
                child_container.setStyleSheet("background: transparent;")
                child_container.setVisible(False)
                
                child_layout = QVBoxLayout(child_container)
                child_layout.setContentsMargins(0, 0, 0, 0)
                child_layout.setSpacing(0)
                
                for child_data in item_data.get('children', []):
                    child_id = child_data['id']
                    
                    # Alt menu yetki kontrolu
                    if not self.yetki_manager.can_access_menu(child_id):
                        continue
                    
                    child_item = MenuItem(
                        item_id=child_id,
                        label=child_data.get('label', child_id),
                        icon="",
                        has_children=False,
                        is_child=True,
                        theme=self.theme,
                        expanded_mode=self.expanded_mode
                    )
                    child_item.clicked.connect(self._on_item_clicked)
                    
                    self.menu_items[child_id] = child_item
                    child_layout.addWidget(child_item)
                
                self.child_containers[item_id] = child_container
                self.menu_layout.addWidget(child_container)
    
    def _on_item_clicked(self, item_id: str):
        """Menu tiklandiginda"""
        item = self.menu_items.get(item_id)
        if not item:
            return

        if item.has_children:
            # Alt menuyu animasyonlu ac/kapat
            item.is_expanded = not item.is_expanded
            item._apply_style()

            if item_id in self.child_containers:
                container = self.child_containers[item_id]
                if item.is_expanded:
                    self._animate_expand(container)
                else:
                    self._animate_collapse(container)
        else:
            # Sayfa sec
            self.set_active(item_id)
            self.menu_clicked.emit(item_id)

    def _animate_expand(self, container: QWidget):
        """Alt menuyu animasyonlu ac"""
        container.setVisible(True)
        container.setMaximumHeight(0)
        target_height = container.sizeHint().height()
        if target_height < 10:
            target_height = 200

        anim = QPropertyAnimation(container, b"maximumHeight")
        anim.setDuration(200)
        anim.setStartValue(0)
        anim.setEndValue(target_height)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: container.setMaximumHeight(16777215))
        anim.start()
        container._expand_anim = anim

    def _animate_collapse(self, container: QWidget):
        """Alt menuyu animasyonlu kapat"""
        current_height = container.height()

        anim = QPropertyAnimation(container, b"maximumHeight")
        anim.setDuration(200)
        anim.setStartValue(current_height)
        anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: container.setVisible(False))
        anim.start()
        container._collapse_anim = anim
    
    def set_active(self, item_id: str):
        """Aktif menuyu ayarla"""
        # Onceki aktifi kaldir
        if self.active_item_id and self.active_item_id in self.menu_items:
            self.menu_items[self.active_item_id].set_active(False)
        
        # Yeni aktifi ayarla
        if item_id in self.menu_items:
            self.menu_items[item_id].set_active(True)
            self.active_item_id = item_id
            
            # Parent varsa ac
            for parent_id, container in self.child_containers.items():
                for i in range(container.layout().count()):
                    child_widget = container.layout().itemAt(i).widget()
                    if isinstance(child_widget, MenuItem) and child_widget.item_id == item_id:
                        container.setVisible(True)
                        if parent_id in self.menu_items:
                            self.menu_items[parent_id].is_expanded = True
                            self.menu_items[parent_id]._apply_style()
                        break
    
    def set_logo(self, logo_path: str):
        """Logo ayarla"""
        self.logo_path = logo_path
        if logo_path and hasattr(self, 'logo_icon'):
            try:
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.logo_icon.setPixmap(scaled)
                    self.logo_icon.setText("")
            except:
                pass
    
    def set_dark_mode(self, is_dark: bool):
        """Dark mode ayarla"""
        self.is_dark_mode = is_dark
        if hasattr(self, 'theme_btn'):
            self.theme_btn.set_dark_mode(is_dark)
    
    def set_expanded(self, expanded: bool):
        """Sidebar genislik modu (yeniden olusturma gerektirir)"""
        self.expanded_mode = expanded
    
    def set_menu_expanded(self, expanded: bool):
        """Menu genislik modu"""
        self.expanded_mode = expanded
    
    def update_theme(self, theme: dict):
        """Temayi guncelle"""
        self.theme = theme
        
        t = theme
        
        # Ana frame
        self.setStyleSheet(f"""
            Sidebar {{
                background: {t.get('bg_sidebar', t.get('bg_main', '#0A0A0A'))};
                border-right: 1px solid {t.get('border', t.get('border_light', '#2A2A2A'))};
            }}
        """)
        
        # Logo
        primary = t.get('primary', '#DC2626')
        if hasattr(self, 'logo_icon') and not self.logo_path:
            self.logo_icon.setStyleSheet(f"""
                background: {primary};
                color: white;
                font-size: 20px;
                font-weight: 700;
                border-radius: 10px;
            """)
        
        if hasattr(self, 'brand_label'):
            self.brand_label.setStyleSheet(f"""
                font-size: 20px;
                font-weight: 700;
                color: {t.get('text', '#FFFFFF')};
                background: transparent;
            """)
        
        # Menu items
        for item in self.menu_items.values():
            item.update_theme(theme)
        
        # Theme button
        if hasattr(self, 'theme_btn'):
            self.theme_btn.update_theme(theme)


# Geriye uyumluluk icin alias
SidebarMenuItem = MenuItem
