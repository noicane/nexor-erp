# -*- coding: utf-8 -*-
"""
NEXOR ERP - Modern Sidebar v3.0
Kompakt tasarim, tam uyumluluk

Eski Sidebar ile %100 uyumlu:
- Ayni __init__ parametreleri
- Ayni sinyaller (menu_clicked, theme_toggle_requested)
- Ayni metodlar (set_logo, set_dark_mode, set_active, update_theme, set_expanded, set_menu_expanded)
"""

import math

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QWidget, QSizePolicy, QPushButton, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QCursor, QPainter, QColor, QPen, QFont

from core.menu_structure import MENU_STRUCTURE, get_page_title, get_page_icon
from core.modul_servisi import ModulServisi
from core.yetki_manager import YetkiManager
from core.nexor_brand import brand
from core.nexor_icons import NexorIcon, _DRAW_MAP as _NEXOR_ICON_KINDS


# =============================================================================
# SUN / MOON ICON (QPainter)
# =============================================================================

class _SunMoonIcon(QLabel):
    """Tema toggle icin guneş/ay ikonu — QPainter, scale-aware."""
    def __init__(self, is_dark: bool, color: str, size: int, parent=None):
        super().__init__(parent)
        self.is_dark = is_dark
        self.color = color
        self.size_px = size
        self.setFixedSize(size, size)

    def set_dark(self, is_dark: bool):
        self.is_dark = is_dark
        self.update()

    def set_color(self, color: str):
        self.color = color
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(self.color))
        pen.setWidthF(max(1.5, self.size_px * 0.09))
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        s = self.size_px
        cx, cy = s / 2, s / 2

        if self.is_dark:
            # GUNES: daire + 8 isin
            r = s * 0.24
            p.drawEllipse(int(cx - r), int(cy - r), int(2 * r), int(2 * r))
            import math
            for i in range(8):
                angle = i * math.pi / 4
                x1 = cx + math.cos(angle) * (r + s * 0.07)
                y1 = cy + math.sin(angle) * (r + s * 0.07)
                x2 = cx + math.cos(angle) * (r + s * 0.18)
                y2 = cy + math.sin(angle) * (r + s * 0.18)
                p.drawLine(int(x1), int(y1), int(x2), int(y2))
        else:
            # AY: crescent (iki arc ile)
            import math
            from PySide6.QtGui import QPainterPath
            r = s * 0.34
            path = QPainterPath()
            # Dis daire
            path.addEllipse(int(cx - r), int(cy - r), int(2 * r), int(2 * r))
            # Ic daire (kesme)
            offset = r * 0.45
            path2 = QPainterPath()
            path2.addEllipse(int(cx - r + offset), int(cy - r - offset * 0.2),
                             int(2 * r), int(2 * r))
            path = path.subtracted(path2)
            p.setBrush(QColor(self.color))
            p.setPen(Qt.NoPen)
            p.drawPath(path)
        p.end()


# =============================================================================
# NEXOR BRAND MARK — oval N + -32deg kirmizi diagonal
# =============================================================================

class NexorBrandMark(QWidget):
    """
    Sidebar ustundeki Nexor brand mark'i.
    Oval cerceve + Fraunces italic N + sol-ust kosesinden -32 derece kirmizi cizgi.
    """

    def __init__(self, size: int = 40, parent=None):
        super().__init__(parent)
        self._size = brand.sp(size)
        self.setFixedSize(self._size, self._size)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self._size

        # Oval — dikey hafif uzun
        ox0, ox1 = int(s * 0.18), int(s * 0.82)
        oy0, oy1 = int(s * 0.15), int(s * 0.89)
        pen = QPen(QColor(brand.TEXT_MUTED))
        pen.setWidthF(max(1.0, s / 48))
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(ox0, oy0, ox1 - ox0, oy1 - oy0)

        # N harfi (Fraunces italic)
        f = QFont('Fraunces')
        f.setItalic(True)
        f.setPixelSize(int(s * 0.52))
        f.setWeight(QFont.Medium)
        p.setFont(f)
        p.setPen(QColor(brand.TEXT))
        from PySide6.QtCore import QRect
        p.drawText(QRect(0, 0, s, s), Qt.AlignCenter, "N")

        # -32 derece kirmizi diagonal cizgi (oval sol ust kosesinden disa)
        p.setRenderHint(QPainter.Antialiasing)
        red_pen = QPen(QColor(brand.PRIMARY))
        red_pen.setWidthF(max(2.0, s / 20))
        red_pen.setCapStyle(Qt.FlatCap)
        p.setPen(red_pen)
        a = math.radians(-32)
        length = int(s * 0.34)
        x0 = int(s * 0.12)
        y0 = int(s * 0.18)
        x1 = x0 + int(length * math.cos(a))
        y1 = y0 + int(length * math.sin(a))
        p.drawLine(x0, y0, x1, y1)

        p.end()


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
            self.setFixedHeight(brand.sp(44) if not self.is_child else brand.sp(36))
            layout = QHBoxLayout(self)
            left_pad = brand.SP_4 if not self.is_child else brand.sp(44)
            layout.setContentsMargins(left_pad, 0, brand.SP_3, 0)
            layout.setSpacing(brand.SP_3)

            # Active indicator (sol bar, sadece aktifken gosterilir)
            self.active_bar = QFrame(self)
            self.active_bar.setFixedWidth(brand.sp(3))
            self.active_bar.setStyleSheet(
                f"background: {brand.PRIMARY}; border: none; border-radius: 2px;"
            )
            self.active_bar.setVisible(False)

            # Icon — ozgun NexorIcon set'i (emoji / text fallback)
            if self.icon:
                if self.icon in _NEXOR_ICON_KINDS:
                    self.icon_label = NexorIcon(self.icon, size=18)
                else:
                    self.icon_label = QLabel(self.icon)
                    self.icon_label.setFixedWidth(brand.sp(22))
                    self.icon_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(self.icon_label)

            # Text
            self.text_label = QLabel(self.label)
            self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            layout.addWidget(self.text_label)

            # Arrow
            if self.has_children:
                self.arrow = QLabel("›")
                self.arrow.setFixedWidth(brand.sp(14))
                layout.addWidget(self.arrow)
        else:
            # Compact mode
            self.setFixedSize(brand.sp(52), brand.sp(48))
            self.setToolTip(self.label)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            if self.icon and self.icon in _NEXOR_ICON_KINDS:
                self.icon_label = NexorIcon(self.icon, size=22)
            else:
                self.icon_label = QLabel(self.icon if self.icon else "•")
                self.icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)

        self._apply_style()

    def resizeEvent(self, event):
        """Active bar'i sol kenarda konumlandir."""
        super().resizeEvent(event)
        if hasattr(self, 'active_bar'):
            bar_h = int(self.height() * 0.5)
            self.active_bar.setGeometry(0, (self.height() - bar_h) // 2,
                                        brand.sp(3), bar_h)

    def _apply_style(self):
        if self.is_active:
            bg = brand.PRIMARY_SOFT
            text_color = brand.TEXT
            icon_color = brand.PRIMARY
        else:
            bg = "transparent"
            text_color = brand.TEXT_MUTED
            icon_color = brand.TEXT_DIM

        hover_bg = brand.BG_HOVER

        if self.expanded_mode:
            self.setStyleSheet(f"""
                MenuItem {{
                    background: {bg};
                    border-radius: {brand.R_MD}px;
                    margin: {brand.SP_1}px {brand.SP_2}px;
                }}
                MenuItem:hover {{
                    background: {hover_bg if not self.is_active else bg};
                }}
                MenuItem QLabel {{ background: transparent; border: none; }}
            """)

            if hasattr(self, 'active_bar'):
                self.active_bar.setVisible(self.is_active)
                self.active_bar.raise_()

            if hasattr(self, 'text_label'):
                fw = brand.FW_SEMIBOLD if self.is_active else brand.FW_MEDIUM
                self.text_label.setStyleSheet(
                    f"color: {text_color}; "
                    f"font-size: {brand.FS_BODY}px; "
                    f"font-weight: {fw};"
                )

            if hasattr(self, 'icon_label'):
                if isinstance(self.icon_label, NexorIcon):
                    self.icon_label.setActive(self.is_active)
                else:
                    self.icon_label.setStyleSheet(
                        f"font-size: {brand.fs(17)}px; color: {icon_color};"
                    )

            if self.has_children and hasattr(self, 'arrow'):
                arrow_char = "⌄" if self.is_expanded else "›"
                self.arrow.setText(arrow_char)
                self.arrow.setStyleSheet(
                    f"color: {brand.TEXT_DIM}; "
                    f"font-size: {brand.fs(14)}px; "
                    f"font-weight: {brand.FW_BOLD};"
                )
        else:
            # Compact mode
            self.setStyleSheet(f"""
                MenuItem {{
                    background: {bg};
                    border-radius: {brand.R_MD}px;
                    margin: {brand.SP_1}px {brand.SP_2}px;
                }}
                MenuItem:hover {{
                    background: {hover_bg if not self.is_active else bg};
                }}
            """)

            if hasattr(self, 'icon_label'):
                if isinstance(self.icon_label, NexorIcon):
                    self.icon_label.setActive(self.is_active)
                else:
                    self.icon_label.setStyleSheet(
                        f"font-size: {brand.fs(20)}px; "
                        f"color: {brand.PRIMARY if self.is_active else icon_color};"
                    )
    
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
            self.setFixedHeight(brand.sp(46))
            layout = QHBoxLayout(self)
            layout.setContentsMargins(brand.SP_4, brand.SP_2, brand.SP_4, brand.SP_2)
            layout.setSpacing(brand.SP_3)

            self.icon = _SunMoonIcon(self.is_dark, brand.TEXT_MUTED, brand.sp(20))
            layout.addWidget(self.icon, 0, Qt.AlignVCenter)

            self.text_label = QLabel()
            self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            layout.addWidget(self.text_label)
        else:
            self.setFixedSize(brand.sp(52), brand.sp(48))
            self.setToolTip("Tema Değiştir")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.icon = _SunMoonIcon(self.is_dark, brand.TEXT_MUTED, brand.sp(22))
            layout.addWidget(self.icon, 0, Qt.AlignCenter)

        self._apply_style()

    def _apply_style(self):
        text = "Açık Tema" if self.is_dark else "Koyu Tema"

        if hasattr(self, 'icon'):
            self.icon.set_dark(self.is_dark)
            self.icon.set_color(brand.TEXT_MUTED)

        if self.expanded_mode and hasattr(self, 'text_label'):
            self.text_label.setText(text)
            self.text_label.setStyleSheet(
                f"color: {brand.TEXT_MUTED}; "
                f"font-size: {brand.FS_BODY}px; "
                f"font-weight: {brand.FW_MEDIUM}; "
                f"background: transparent;"
            )

        self.setStyleSheet(f"""
            ThemeToggleButton {{
                background: transparent;
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_MD}px;
                margin: {brand.SP_2}px;
            }}
            ThemeToggleButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
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

    # Responsive — scale faktoru ile carpilir
    @property
    def EXPANDED_WIDTH(self) -> int:
        return brand.sp(240)

    @property
    def COMPACT_WIDTH(self) -> int:
        return brand.sp(68)
    
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
        self._recent_pages = []  # Son kullanilan sayfalar (max 5)
        self._unlocked_menus = set()  # Şifre girilen menüler (oturum boyunca)

        # Yetki manager
        self.yetki_manager = YetkiManager()

        self._setup_ui()
    
    def _setup_ui(self):
        width = self.EXPANDED_WIDTH if self.expanded_mode else self.COMPACT_WIDTH
        self.setFixedWidth(width)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ================ LOGO BASLIGI ================
        self.logo_frame = QFrame()
        self.logo_frame.setFixedHeight(brand.sp(72))

        logo_layout = QHBoxLayout(self.logo_frame)
        logo_layout.setContentsMargins(brand.SP_4, 0, brand.SP_4, 0)
        logo_layout.setSpacing(brand.SP_3)

        # Redline brand mark — oval N + kirmizi diagonal
        self.logo_icon = NexorBrandMark(size=42)
        logo_layout.addWidget(self.logo_icon)

        self.brand_label = None
        self.erp_label = None
        if self.expanded_mode:
            brand_col = QVBoxLayout()
            brand_col.setSpacing(-2)
            brand_col.setContentsMargins(brand.sp(6), 0, 0, 0)

            self.brand_label = QLabel("Nexor")
            brand_col.addWidget(self.brand_label)

            self.erp_label = QLabel("ERP")
            brand_col.addWidget(self.erp_label)

            logo_layout.addLayout(brand_col)

        logo_layout.addStretch()
        layout.addWidget(self.logo_frame)

        # SON KULLANILANLAR kaldirildi (istege gore)

        # ================ MENU SCROLL ================
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.menu_widget = QWidget()
        self.menu_layout = QVBoxLayout(self.menu_widget)
        self.menu_layout.setContentsMargins(0, brand.SP_3, 0, brand.SP_3)
        self.menu_layout.setSpacing(brand.sp(2))

        self._build_menu()

        self.menu_layout.addStretch()
        self.scroll_area.setWidget(self.menu_widget)
        layout.addWidget(self.scroll_area, 1)

        # ================ FOOTER ================
        self.footer_frame = QFrame()

        footer_layout = QVBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(0, brand.SP_2, 0, brand.SP_2)
        footer_layout.setSpacing(0)

        self.theme_btn = ThemeToggleButton(self.theme, self.expanded_mode, self.is_dark_mode)
        self.theme_btn.theme_toggled.connect(self.theme_toggle_requested.emit)
        footer_layout.addWidget(self.theme_btn)

        layout.addWidget(self.footer_frame)

        # Tum child stillerini brand'den uygula
        self._apply_child_styles()
    
    def _build_menu(self):
        """Menu yapisini olustur"""
        modul_servisi = ModulServisi.instance()
        for item_data in MENU_STRUCTURE:
            item_id = item_data['id']

            # Modul lisans kontrolu (ana modul seviyesi)
            # Not: granulerlik ana seviyede - alt sayfalar ust modulun durumunu miras alir
            if not modul_servisi.is_aktif(item_id):
                continue

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

                    # Gelistirici-only sayfalar (musteri yonetimi vb.)
                    if child_data.get('gelistirici_only') and not modul_servisi.gelistirici_modu:
                        continue

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
            # Şifre korumalı menü kontrolü
            if item_id not in self._unlocked_menus:
                menu_def = next((m for m in MENU_STRUCTURE if m['id'] == item_id), None)
                if menu_def and menu_def.get('password'):
                    pwd, ok = QInputDialog.getText(
                        self, "Şifre Gerekli",
                        f"'{menu_def['label']}' menüsüne erişim için şifre girin:",
                        QLineEdit.Password
                    )
                    if not ok or pwd != menu_def['password']:
                        return
                    self._unlocked_menus.add(item_id)

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
            # Child sayfa — parent sifre korumali mi kontrol et
            parent_menu = next(
                (m for m in MENU_STRUCTURE
                 if m.get('children') and any(ch['id'] == item_id for ch in m['children'])),
                None
            )
            if parent_menu and parent_menu.get('password'):
                parent_id = parent_menu['id']
                if parent_id not in self._unlocked_menus:
                    pwd, ok = QInputDialog.getText(
                        self, "Sifre Gerekli",
                        f"'{parent_menu['label']}' menusune erisim icin sifre girin:",
                        QLineEdit.Password
                    )
                    if not ok or pwd != parent_menu['password']:
                        return
                    self._unlocked_menus.add(parent_id)

            # Sayfa sec
            self.set_active(item_id)
            self.add_recent_page(item_id)
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
    
    def add_recent_page(self, page_id: str):
        """Son kullanilan sayfalara ekle"""
        if not self.expanded_mode or not hasattr(self, 'recent_frame'):
            return
        if page_id == 'dashboard':
            return

        # Listede varsa kaldir (en basa almak icin)
        if page_id in self._recent_pages:
            self._recent_pages.remove(page_id)
        self._recent_pages.insert(0, page_id)
        self._recent_pages = self._recent_pages[:5]
        self._update_recent_ui()

    def _update_recent_ui(self):
        """Son kullanilanlar alanini guncelle"""
        if not hasattr(self, 'recent_layout'):
            return

        # Eski butonlari temizle (baslik haric)
        while self.recent_layout.count() > 1:
            item = self.recent_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        for page_id in self._recent_pages:
            title = get_page_title(page_id)
            icon = get_page_icon(page_id)

            btn = QPushButton(f"  {icon}  {title}")
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {brand.TEXT_MUTED};
                    border: none;
                    text-align: left;
                    padding: {brand.SP_1}px {brand.SP_2}px;
                    border-radius: {brand.R_SM}px;
                    font-size: {brand.FS_CAPTION}px;
                }}
                QPushButton:hover {{
                    background: {brand.BG_HOVER};
                    color: {brand.TEXT};
                }}
            """)
            btn.clicked.connect(lambda checked, pid=page_id: self._on_recent_clicked(pid))
            self.recent_layout.addWidget(btn)

        self.recent_frame.setVisible(len(self._recent_pages) > 0)

    def _on_recent_clicked(self, page_id: str):
        """Son kullanilanlardan tiklandiginda"""
        self.set_active(page_id)
        self.menu_clicked.emit(page_id)

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
            except Exception:
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
    
    def _apply_child_styles(self):
        """Tum sidebar child widget stillerini brand'den okuyup uygula.
        Tema modu degistiginde yeniden uygulanmasi GEREK."""
        # Ana frame — ana arka plan ile ayni renk, sadece sag border ayirici
        self.setStyleSheet(f"""
            Sidebar {{
                background: {brand.BG_MAIN};
                border-right: 1px solid {brand.BORDER};
            }}
        """)

        # Logo frame
        if hasattr(self, 'logo_frame'):
            self.logo_frame.setStyleSheet(
                f"background: transparent; "
                f"border-bottom: 1px solid {brand.BORDER};"
            )

        # Logo icon — NexorBrandMark paintEvent kendi cizer, stylesheet sadece arka plani temiz tutar
        if hasattr(self, 'logo_icon') and not self.logo_path:
            if isinstance(self.logo_icon, NexorBrandMark):
                self.logo_icon.setStyleSheet("background: transparent;")
                self.logo_icon.update()
            else:
                self.logo_icon.setStyleSheet(
                    f"background: {brand.PRIMARY}; "
                    f"color: white; "
                    f"font-size: {brand.fs(18)}px; "
                    f"font-weight: {brand.FW_BOLD}; "
                    f"border-radius: {brand.R_MD}px;"
                )

        if getattr(self, 'brand_label', None):
            # "Nexor" — Fraunces italic kirmizi
            self.brand_label.setStyleSheet(
                f"font-family: {brand.FONT_DISPLAY}; "
                f"font-size: {brand.fs(22)}px; "
                f"font-style: italic; "
                f"font-weight: {brand.FW_MEDIUM}; "
                f"color: {brand.PRIMARY}; "
                f"background: transparent; "
                f"border: none;"
            )

        if getattr(self, 'erp_label', None):
            # "ERP" — Fraunces regular, beyaz
            self.erp_label.setStyleSheet(
                f"font-family: {brand.FONT_DISPLAY}; "
                f"font-size: {brand.fs(18)}px; "
                f"font-weight: {brand.FW_REGULAR}; "
                f"color: {brand.TEXT}; "
                f"letter-spacing: 1px; "
                f"background: transparent; "
                f"border: none;"
            )

        # Recent frame
        if getattr(self, 'recent_frame', None):
            self.recent_frame.setStyleSheet("background: transparent; border: none;")
        if getattr(self, 'recent_title', None):
            self.recent_title.setStyleSheet(
                f"color: {brand.TEXT_DIM}; "
                f"font-size: {brand.fs(9)}px; "
                f"font-weight: {brand.FW_BOLD}; "
                f"letter-spacing: 1.2px; "
                f"padding: {brand.SP_1}px; "
                f"background: transparent; "
                f"border: none;"
            )

        # Scroll area
        if hasattr(self, 'scroll_area'):
            self.scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    background: transparent;
                    border: none;
                }}
                QScrollBar:vertical {{
                    background: transparent;
                    width: {brand.sp(6)}px;
                    margin: 0;
                }}
                QScrollBar::handle:vertical {{
                    background: {brand.BORDER_HARD};
                    border-radius: {brand.sp(3)}px;
                    min-height: {brand.sp(30)}px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {brand.TEXT_DIM};
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0;
                }}
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: transparent;
                }}
            """)
        if hasattr(self, 'menu_widget'):
            self.menu_widget.setStyleSheet("background: transparent;")

        # Footer
        if hasattr(self, 'footer_frame'):
            self.footer_frame.setStyleSheet(
                f"background: transparent; "
                f"border-top: 1px solid {brand.BORDER};"
            )

        # Menu items
        for item in self.menu_items.values():
            item._apply_style()

        # Theme button
        if hasattr(self, 'theme_btn'):
            self.theme_btn._apply_style()

        # Son kullanilanlar butonlarini yeniden yukle
        if hasattr(self, '_update_recent_ui'):
            try:
                self._update_recent_ui()
            except Exception:
                pass

    def update_theme(self, theme: dict):
        """Temayi guncelle — tum child stilleri yeniden uygulanir."""
        self.theme = theme
        self._apply_child_styles()


# Geriye uyumluluk icin alias
SidebarMenuItem = MenuItem
