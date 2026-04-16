# -*- coding: utf-8 -*-
"""
NEXOR ERP - Modern Component Kutuphanesi
Faz 1: Temel Altyapi

Tum sayfalarda kullanilacak standart bilesenler.
Bu dosya mevcut kodlara dokunmaz, yeni bir katman ekler.

Bilesenler:
- NexorCard: Standart kart container
- NexorStatsCard: Istatistik karti
- NexorTable: Modern tablo
- NexorButton: Buton cesitleri
- NexorBadge: Durum etiketleri
- NexorInput: Text input
- NexorSelect: Dropdown/ComboBox
- NexorForm: Form container
- NexorTabs: Tab navigasyonu
- NexorModal: Dialog/Popup
- NexorPageHeader: Sayfa basligi

Kullanim:
    from components.nexor_components import NexorCard, NexorButton, NexorTable
"""

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QCheckBox, QRadioButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QDialog, QDialogButtonBox, QScrollArea,
    QSizePolicy, QGraphicsDropShadowEffect, QDateEdit, QTimeEdit,
    QMessageBox, QAbstractItemView, QStyledItemDelegate, QStyle
)
from PySide6.QtCore import Qt, Signal, QSize, QDate, QTime, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QPen, QBrush

from core.nexor_brand import brand


# =============================================================================
# TEMA RENKLERI (Deprecated - brand kullan)
# =============================================================================

def get_theme_colors(theme: dict = None) -> dict:
    """DEPRECATED: Geriye uyumluluk icin brand degerlerini dict olarak dondurur."""
    return {
        "bg_main": brand.BG_MAIN,
        "bg_card": brand.BG_CARD,
        "bg_card_hover": brand.BG_HOVER,
        "bg_input": brand.BG_INPUT,
        "bg_hover": brand.BG_HOVER,
        "bg_selected": brand.BG_SELECTED,
        "border": brand.BORDER,
        "border_light": brand.BORDER_HARD,
        "border_focus": brand.PRIMARY,
        "text": brand.TEXT,
        "text_secondary": brand.TEXT_MUTED,
        "text_muted": brand.TEXT_DIM,
        "text_disabled": brand.TEXT_DISABLED,
        "primary": brand.PRIMARY,
        "primary_hover": brand.PRIMARY_HOVER,
        "success": brand.SUCCESS,
        "success_bg": brand.SUCCESS_SOFT,
        "success_text": brand.SUCCESS,
        "warning": brand.WARNING,
        "warning_bg": brand.WARNING_SOFT,
        "warning_text": brand.WARNING,
        "error": brand.ERROR,
        "error_bg": brand.ERROR_SOFT,
        "error_text": brand.ERROR,
        "info": brand.INFO,
        "info_bg": brand.INFO_SOFT,
        "info_text": brand.INFO,
        "table_header_bg": brand.BG_SURFACE,
        "table_header_text": brand.TEXT_MUTED,
        "table_row_bg": brand.BG_CARD,
        "table_row_alt": brand.BG_MAIN,
        "table_row_hover": brand.BG_HOVER,
        "table_border": brand.BORDER,
    }


# =============================================================================
# SPACING & SIZING CONSTANTS (Deprecated - brand kullan)
# =============================================================================

class Spacing:
    """DEPRECATED: brand.SP_* kullan"""
    @property
    def XS(self): return brand.SP_1
    @property
    def SM(self): return brand.SP_2
    @property
    def MD(self): return brand.SP_3
    @property
    def LG(self): return brand.SP_4
    @property
    def XL(self): return brand.SP_6
    @property
    def XXL(self): return brand.SP_8

# Sinif uzerinden de erisilsin diye class-level tanimlama
Spacing.XS = brand.SP_1
Spacing.SM = brand.SP_2
Spacing.MD = brand.SP_3
Spacing.LG = brand.SP_4
Spacing.XL = brand.SP_6
Spacing.XXL = brand.SP_8


class BorderRadius:
    """DEPRECATED: brand.R_* kullan"""
    pass

BorderRadius.SM = brand.R_SM
BorderRadius.MD = brand.R_MD
BorderRadius.LG = brand.R_LG
BorderRadius.XL = brand.R_XL


class FontSize:
    """DEPRECATED: brand.FS_* kullan"""
    pass

FontSize.XS = brand.FS_CAPTION
FontSize.SM = brand.FS_BODY_SM
FontSize.MD = brand.FS_BODY
FontSize.LG = brand.fs(14)
FontSize.XL = brand.FS_HEADING_SM
FontSize.XXL = brand.FS_HEADING_LG
FontSize.XXXL = brand.FS_TITLE
FontSize.TITLE = brand.FS_DISPLAY


# =============================================================================
# NEXOR CARD
# =============================================================================

class NexorCard(QFrame):
    """
    Standart kart container

    Kullanim:
        card = NexorCard(theme)
        card.set_title("Baslik")
        card.add_widget(my_widget)
    """

    def __init__(self, theme: dict = None, title: str = None, parent=None):
        super().__init__(parent)
        self.theme = theme  # backward compat
        self._title = title
        self._setup_ui()
        self._add_shadow()

    def _add_shadow(self):
        """Karta golge efekti ekle"""
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(20)
        self._shadow.setXOffset(0)
        self._shadow.setYOffset(4)
        self._shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self._shadow)

    def enterEvent(self, event):
        if hasattr(self, '_shadow') and self._shadow:
            anim = QPropertyAnimation(self._shadow, b"blurRadius")
            anim.setDuration(200)
            anim.setStartValue(self._shadow.blurRadius())
            anim.setEndValue(35)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
            self._hover_anim = anim
        super().enterEvent(event)

    def leaveEvent(self, event):
        if hasattr(self, '_shadow') and self._shadow:
            anim = QPropertyAnimation(self._shadow, b"blurRadius")
            anim.setDuration(200)
            anim.setStartValue(self._shadow.blurRadius())
            anim.setEndValue(20)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
            self._hover_anim = anim
        super().leaveEvent(event)

    def _setup_ui(self):
        self.setStyleSheet(f"""
            NexorCard {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        self._layout.setSpacing(brand.SP_4)

        # Baslik varsa ekle
        if self._title:
            self._title_label = QLabel(self._title)
            self._title_label.setStyleSheet(f"""
                font-size: {brand.FS_HEADING_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
                color: {brand.TEXT};
                padding-bottom: {brand.SP_2}px;
                border-bottom: 1px solid {brand.BORDER};
                background: transparent;
            """)
            self._layout.addWidget(self._title_label)

        # Icerik alani
        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(brand.SP_3)
        self._layout.addWidget(self._content)

    def set_title(self, title: str):
        """Baslik ayarla"""
        if hasattr(self, '_title_label'):
            self._title_label.setText(title)

    def add_widget(self, widget: QWidget):
        """Icerik ekle"""
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Layout ekle"""
        self._content_layout.addLayout(layout)

    def content_layout(self):
        """Icerik layout'unu dondur"""
        return self._content_layout


# =============================================================================
# NEXOR STATS CARD
# =============================================================================

class NexorStatsCard(QFrame):
    """
    Istatistik karti (Dashboard icin)

    Kullanim:
        card = NexorStatsCard(
            theme=theme,
            title="Gunluk Uretim",
            value="1,247",
            icon="🏭",
            trend="+12.5%",
            trend_up=True
        )
    """

    clicked = Signal()

    def __init__(self, theme: dict = None, title: str = "", value: str = "",
                 icon: str = None, trend: str = None, trend_up: bool = True,
                 color: str = None, parent=None):
        super().__init__(parent)
        self.theme = theme  # backward compat
        self._title = title
        self._value = value
        self._icon = icon
        self._trend = trend
        self._trend_up = trend_up
        self._color = color or brand.PRIMARY
        self._setup_ui()
        self._add_shadow()

    def _add_shadow(self):
        """Karta golge efekti ekle"""
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(20)
        self._shadow.setXOffset(0)
        self._shadow.setYOffset(4)
        self._shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self._shadow)

    def enterEvent(self, event):
        if hasattr(self, '_shadow') and self._shadow:
            anim = QPropertyAnimation(self._shadow, b"blurRadius")
            anim.setDuration(200)
            anim.setStartValue(self._shadow.blurRadius())
            anim.setEndValue(35)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
            self._hover_anim = anim
        super().enterEvent(event)

    def leaveEvent(self, event):
        if hasattr(self, '_shadow') and self._shadow:
            anim = QPropertyAnimation(self._shadow, b"blurRadius")
            anim.setDuration(200)
            anim.setStartValue(self._shadow.blurRadius())
            anim.setEndValue(20)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
            self._hover_anim = anim
        super().leaveEvent(event)

    def _setup_ui(self):
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            NexorStatsCard {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
            NexorStatsCard:hover {{
                border-color: {self._color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_3)

        # Ust kisim: Label + Icon
        header = QHBoxLayout()

        title_label = QLabel(self._title)
        title_label.setStyleSheet(f"""
            font-size: {brand.FS_BODY}px;
            color: {brand.TEXT_MUTED};
            background: transparent;
        """)
        header.addWidget(title_label)
        header.addStretch()

        if self._icon:
            # Daha belirgin ikon container - tema bazli renk
            icon_container = QFrame()
            icon_container.setFixedSize(44, 44)

            icon_bg = self._hex_to_rgba(self._color, 0.15)

            icon_container.setStyleSheet(f"""
                background: {icon_bg};
                border-radius: {brand.R_MD}px;
            """)

            icon_layout = QHBoxLayout(icon_container)
            icon_layout.setContentsMargins(0, 0, 0, 0)

            icon_label = QLabel(self._icon)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet(f"""
                font-size: 22px;
                background: transparent;
            """)
            icon_layout.addWidget(icon_label)

            header.addWidget(icon_container)

        layout.addLayout(header)

        # Deger
        value_label = QLabel(self._value)
        value_label.setStyleSheet(f"""
            font-size: {brand.FS_DISPLAY}px;
            font-weight: {brand.FW_BOLD};
            color: {brand.TEXT};
            background: transparent;
        """)
        layout.addWidget(value_label)
        self._value_label = value_label

        # Trend
        if self._trend:
            trend_color = brand.SUCCESS if self._trend_up else brand.ERROR
            arrow = "↑" if self._trend_up else "↓"
            trend_label = QLabel(f"{arrow} {self._trend}")
            trend_label.setStyleSheet(f"""
                font-size: {brand.FS_BODY_SM}px;
                color: {trend_color};
                background: transparent;
            """)
            layout.addWidget(trend_label)
            self._trend_label = trend_label

    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """HEX rengi koyu arka plan icin koyulastir"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        # Koyu tema icin: rengi koyulastir
        factor = alpha
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _hex_lighten(self, hex_color: str, factor: float) -> str:
        """HEX rengi acik arka plan icin aciklastir"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        # Light tema icin: beyaza dogru karistir
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def set_value(self, value: str):
        """Degeri guncelle"""
        self._value_label.setText(value)

    def set_trend(self, trend: str, trend_up: bool):
        """Trendi guncelle"""
        if hasattr(self, '_trend_label'):
            trend_color = brand.SUCCESS if trend_up else brand.ERROR
            arrow = "↑" if trend_up else "↓"
            self._trend_label.setText(f"{arrow} {trend}")
            self._trend_label.setStyleSheet(f"""
                font-size: {brand.FS_BODY_SM}px;
                color: {trend_color};
                background: transparent;
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# =============================================================================
# NEXOR BUTTON
# =============================================================================

class NexorButton(QPushButton):
    """
    Standart buton

    Variants: primary, secondary, success, danger, ghost

    Kullanim:
        btn = NexorButton("Kaydet", theme, variant="primary")
        btn = NexorButton("Iptal", theme, variant="secondary")
        btn = NexorButton("Sil", theme, variant="danger", icon="🗑️")
    """

    def __init__(self, text: str, theme: dict = None, variant: str = "secondary",
                 icon: str = None, parent=None):
        super().__init__(parent)
        self.theme = theme  # backward compat
        self._variant = variant
        self._icon = icon

        if icon:
            self.setText(f"{icon}  {text}")
        else:
            self.setText(text)

        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)
        self._apply_style()

    def _apply_style(self):
        styles = {
            "primary": f"""
                QPushButton {{
                    background: {brand.PRIMARY};
                    color: white;
                    border: none;
                    border-radius: {brand.R_MD}px;
                    padding: {brand.SP_3}px {brand.SP_6}px;
                    font-size: {brand.FS_BODY}px;
                    font-weight: {brand.FW_SEMIBOLD};
                }}
                QPushButton:hover {{
                    background: {brand.PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    background: {brand.PRIMARY_HOVER};
                }}
                QPushButton:disabled {{
                    background: {brand.TEXT_DISABLED};
                    color: {brand.TEXT_DIM};
                }}
            """,
            "secondary": f"""
                QPushButton {{
                    background: {brand.BG_CARD};
                    color: {brand.TEXT};
                    border: 1px solid {brand.BORDER};
                    border-radius: {brand.R_MD}px;
                    padding: {brand.SP_3}px {brand.SP_6}px;
                    font-size: {brand.FS_BODY}px;
                    font-weight: {brand.FW_MEDIUM};
                }}
                QPushButton:hover {{
                    background: {brand.BG_HOVER};
                    border-color: {brand.BORDER_HARD};
                }}
                QPushButton:pressed {{
                    background: {brand.BG_SELECTED};
                }}
                QPushButton:disabled {{
                    background: {brand.BG_HOVER};
                    color: {brand.TEXT_DISABLED};
                }}
            """,
            "success": f"""
                QPushButton {{
                    background: {brand.SUCCESS};
                    color: white;
                    border: none;
                    border-radius: {brand.R_MD}px;
                    padding: {brand.SP_3}px {brand.SP_6}px;
                    font-size: {brand.FS_BODY}px;
                    font-weight: {brand.FW_SEMIBOLD};
                }}
                QPushButton:hover {{
                    background: #059669;
                }}
                QPushButton:disabled {{
                    background: {brand.TEXT_DISABLED};
                }}
            """,
            "danger": f"""
                QPushButton {{
                    background: {brand.ERROR};
                    color: white;
                    border: none;
                    border-radius: {brand.R_MD}px;
                    padding: {brand.SP_3}px {brand.SP_6}px;
                    font-size: {brand.FS_BODY}px;
                    font-weight: {brand.FW_SEMIBOLD};
                }}
                QPushButton:hover {{
                    background: #DC2626;
                }}
                QPushButton:disabled {{
                    background: {brand.TEXT_DISABLED};
                }}
            """,
            "ghost": f"""
                QPushButton {{
                    background: transparent;
                    color: {brand.TEXT_MUTED};
                    border: none;
                    border-radius: {brand.R_MD}px;
                    padding: {brand.SP_3}px {brand.SP_6}px;
                    font-size: {brand.FS_BODY}px;
                }}
                QPushButton:hover {{
                    background: {brand.BG_HOVER};
                    color: {brand.TEXT};
                }}
            """,
        }

        self.setStyleSheet(styles.get(self._variant, styles["secondary"]))

    def set_variant(self, variant: str):
        """Variant degistir"""
        self._variant = variant
        self._apply_style()


# =============================================================================
# NEXOR BADGE
# =============================================================================

class NexorBadge(QLabel):
    """
    Durum etiketi

    Variants: success, warning, error, info, default

    Kullanim:
        badge = NexorBadge("Aktif", theme, variant="success")
        badge = NexorBadge("Bekliyor", theme, variant="warning")
    """

    def __init__(self, text: str, theme: dict = None, variant: str = "default", parent=None):
        super().__init__(text, parent)
        self.theme = theme  # backward compat
        self._variant = variant
        self._apply_style()

    def _apply_style(self):
        colors = {
            "success": (brand.SUCCESS_SOFT, brand.SUCCESS),
            "warning": (brand.WARNING_SOFT, brand.WARNING),
            "error": (brand.ERROR_SOFT, brand.ERROR),
            "info": (brand.INFO_SOFT, brand.INFO),
            "default": (brand.BG_HOVER, brand.TEXT_MUTED),
        }

        bg, fg = colors.get(self._variant, colors["default"])

        self.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {fg};
                padding: {brand.SP_1}px {brand.SP_3}px;
                border-radius: {brand.R_SM}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
        """)
        self.setAlignment(Qt.AlignCenter)

    def set_variant(self, variant: str):
        """Variant degistir"""
        self._variant = variant
        self._apply_style()


# =============================================================================
# NEXOR INPUT
# =============================================================================

class NexorInput(QLineEdit):
    """
    Standart text input

    Kullanim:
        input = NexorInput(theme, placeholder="Ara...")
        input = NexorInput(theme, label="Urun Kodu")
    """

    def __init__(self, theme: dict = None, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.theme = theme  # backward compat
        self.setPlaceholderText(placeholder)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_MD}px;
                padding: {brand.SP_3}px {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                selection-background-color: {brand.PRIMARY};
            }}
            QLineEdit:hover {{
                border-color: {brand.BORDER_HARD};
            }}
            QLineEdit:focus {{
                border-color: {brand.PRIMARY};
            }}
            QLineEdit:disabled {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT_DISABLED};
            }}
        """)
        self.setMinimumHeight(42)


# =============================================================================
# NEXOR SELECT (ComboBox)
# =============================================================================

class NexorSelect(QComboBox):
    """
    Standart dropdown/combobox

    Kullanim:
        select = NexorSelect(theme)
        select.addItems(["Secenek 1", "Secenek 2"])
    """

    def __init__(self, theme: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme  # backward compat
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_MD}px;
                padding: {brand.SP_3}px {brand.SP_4}px;
                padding-right: 30px;
                font-size: {brand.FS_BODY}px;
                min-height: 22px;
            }}
            QComboBox:hover {{
                border-color: {brand.BORDER_HARD};
            }}
            QComboBox:focus {{
                border-color: {brand.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {brand.TEXT_DIM};
                width: 0;
                height: 0;
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_MD}px;
                padding: {brand.SP_1}px;
                selection-background-color: {brand.BG_HOVER};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: {brand.SP_3}px;
                border-radius: {brand.R_SM}px;
                min-height: 24px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: {brand.BG_HOVER};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: {brand.BG_SELECTED};
            }}
        """)
        self.setMinimumHeight(42)


# =============================================================================
# NEXOR TABLE
# =============================================================================

class NexorTable(QTableWidget):
    """
    Modern tablo

    Kullanim:
        table = NexorTable(theme)
        table.set_columns(["ID", "Urun", "Miktar", "Durum"])
        table.add_row(["001", "Motor", "100", NexorBadge("Aktif", theme, "success")])
    """

    row_clicked = Signal(int)
    row_double_clicked = Signal(int)

    def __init__(self, theme: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme  # backward compat
        self._setup_ui()

    def _setup_ui(self):
        # Temel ayarlar
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Header ayarlari
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setMinimumSectionSize(80)

        # Satir yuksekligi
        self.verticalHeader().setDefaultSectionSize(48)

        # Stil
        self.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                gridline-color: transparent;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_3}px {brand.SP_4}px;
                border: none;
                color: {brand.TEXT};
            }}
            QTableWidget::item:hover {{
                background: {brand.BG_HOVER};
            }}
            QTableWidget::item:selected {{
                background: {brand.BG_SELECTED};
                color: {brand.TEXT};
            }}
            QTableWidget::item:alternate {{
                background: {brand.BG_MAIN};
            }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_4}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_BODY_SM}px;
                text-transform: uppercase;
            }}
            QHeaderView::section:first {{
                border-top-left-radius: {brand.R_LG}px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: {brand.R_LG}px;
            }}
            QScrollBar:vertical {{
                background: {brand.BG_CARD};
                width: 10px;
                border-radius: 5px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {brand.BORDER};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {brand.BORDER_HARD};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        # Sinyaller
        self.cellClicked.connect(lambda row, col: self.row_clicked.emit(row))
        self.cellDoubleClicked.connect(lambda row, col: self.row_double_clicked.emit(row))

    def set_columns(self, columns: list):
        """Kolonlari ayarla"""
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)

    def add_row(self, data: list):
        """Satir ekle"""
        row = self.rowCount()
        self.insertRow(row)

        for col, item in enumerate(data):
            if isinstance(item, QWidget):
                # Widget ise (Badge vs.)
                self.setCellWidget(row, col, item)
            else:
                # Text ise
                cell = QTableWidgetItem(str(item))
                cell.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.setItem(row, col, cell)

    def clear_rows(self):
        """Tum satirlari temizle"""
        self.setRowCount(0)

    def get_selected_row(self) -> int:
        """Secili satiri dondur"""
        items = self.selectedItems()
        if items:
            return items[0].row()
        return -1

    def get_row_data(self, row: int) -> list:
        """Satir verisini dondur"""
        data = []
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                data.append(item.text())
            else:
                widget = self.cellWidget(row, col)
                if widget and isinstance(widget, QLabel):
                    data.append(widget.text())
                else:
                    data.append("")
        return data


# =============================================================================
# NEXOR FORM
# =============================================================================

class NexorFormField(QWidget):
    """
    Form alani (label + input)

    Kullanim:
        field = NexorFormField("Urun Kodu", NexorInput(theme), theme)
    """

    def __init__(self, label: str, widget: QWidget, theme: dict = None,
                 required: bool = False, parent=None):
        super().__init__(parent)
        self.theme = theme  # backward compat
        self._widget = widget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(brand.SP_2)

        # Label
        label_text = f"{label} *" if required else label
        self._label = QLabel(label_text)
        self._label.setStyleSheet(f"""
            font-size: {brand.FS_BODY}px;
            font-weight: {brand.FW_MEDIUM};
            color: {brand.TEXT};
            background: transparent;
        """)
        layout.addWidget(self._label)

        # Widget
        layout.addWidget(widget)

    def get_widget(self):
        return self._widget

    def get_value(self):
        if isinstance(self._widget, QLineEdit):
            return self._widget.text()
        elif isinstance(self._widget, QComboBox):
            return self._widget.currentText()
        elif isinstance(self._widget, (QSpinBox, QDoubleSpinBox)):
            return self._widget.value()
        elif isinstance(self._widget, QCheckBox):
            return self._widget.isChecked()
        return None


class NexorForm(NexorCard):
    """
    Form container

    Kullanim:
        form = NexorForm(theme, "Yeni Kayit")
        form.add_field("Urun Kodu", NexorInput(theme))
        form.add_field("Miktar", NexorInput(theme))
        form.add_buttons(["Kaydet", "Iptal"])
    """

    submitted = Signal(dict)
    cancelled = Signal()

    def __init__(self, theme: dict = None, title: str = None, columns: int = 2, parent=None):
        super().__init__(theme, title, parent)
        self._columns = columns
        self._fields = {}
        self._current_row = 0
        self._current_col = 0

        # Grid layout for fields
        self._grid = QGridLayout()
        self._grid.setSpacing(brand.SP_4)
        self._grid.setColumnStretch(0, 1)
        if columns > 1:
            self._grid.setColumnStretch(1, 1)
        self._content_layout.addLayout(self._grid)

    def add_field(self, label: str, widget: QWidget, required: bool = False,
                  full_width: bool = False):
        """Form alani ekle"""
        field = NexorFormField(label, widget, self.theme, required)
        self._fields[label] = field

        if full_width or self._columns == 1:
            self._grid.addWidget(field, self._current_row, 0, 1, self._columns)
            self._current_row += 1
            self._current_col = 0
        else:
            self._grid.addWidget(field, self._current_row, self._current_col)
            self._current_col += 1
            if self._current_col >= self._columns:
                self._current_col = 0
                self._current_row += 1

    def add_buttons(self, submit_text: str = "Kaydet", cancel_text: str = "Iptal"):
        """Form butonlari ekle"""
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        if cancel_text:
            cancel_btn = NexorButton(cancel_text, self.theme, "secondary")
            cancel_btn.clicked.connect(self.cancelled.emit)
            btn_layout.addWidget(cancel_btn)

        submit_btn = NexorButton(submit_text, self.theme, "primary")
        submit_btn.clicked.connect(self._on_submit)
        btn_layout.addWidget(submit_btn)

        self._content_layout.addLayout(btn_layout)

    def _on_submit(self):
        """Form gonderildiginde"""
        data = {}
        for label, field in self._fields.items():
            data[label] = field.get_value()
        self.submitted.emit(data)

    def get_values(self) -> dict:
        """Tum degerleri dondur"""
        return {label: field.get_value() for label, field in self._fields.items()}

    def get_field(self, label: str):
        """Belirli bir alani dondur"""
        return self._fields.get(label)


# =============================================================================
# NEXOR PAGE HEADER
# =============================================================================

class NexorPageHeader(QWidget):
    """
    Sayfa basligi

    Kullanim:
        header = NexorPageHeader(
            theme=theme,
            title="Dashboard",
            subtitle="27 Ocak 2026, Sali",
            actions=[
                ("+ Yeni", "primary", on_new_click),
                ("Yenile", "secondary", on_refresh_click),
            ]
        )
    """

    def __init__(self, theme: dict = None, title: str = "", subtitle: str = None,
                 actions: list = None, parent=None):
        super().__init__(parent)
        self.theme = theme  # backward compat

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, brand.SP_6)

        # Sol: Baslik ve alt baslik
        title_layout = QVBoxLayout()
        title_layout.setSpacing(brand.SP_1)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {brand.FS_TITLE}px;
            font-weight: {brand.FW_SEMIBOLD};
            color: {brand.TEXT};
            background: transparent;
        """)
        title_layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(f"""
                font-size: {brand.FS_BODY}px;
                color: {brand.TEXT_DIM};
                background: transparent;
            """)
            title_layout.addWidget(subtitle_label)

        layout.addLayout(title_layout)
        layout.addStretch()

        # Sag: Butonlar
        if actions:
            for action in actions:
                text, variant, callback = action
                btn = NexorButton(text, theme, variant)
                btn.clicked.connect(callback)
                layout.addWidget(btn)


# =============================================================================
# NEXOR TABS
# =============================================================================

class NexorTabs(QTabWidget):
    """
    Tab navigasyonu

    Kullanim:
        tabs = NexorTabs(theme)
        tabs.add_tab("Genel", general_widget)
        tabs.add_tab("Detay", detail_widget)
    """

    def __init__(self, theme: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme  # backward compat
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                padding: {brand.SP_4}px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {brand.TEXT_DIM};
                padding: {brand.SP_3}px {brand.SP_6}px;
                margin-right: {brand.SP_1}px;
                border: none;
                border-bottom: 2px solid transparent;
                font-weight: {brand.FW_MEDIUM};
                font-size: {brand.FS_BODY}px;
            }}
            QTabBar::tab:hover {{
                color: {brand.TEXT};
                background: {brand.BG_HOVER};
            }}
            QTabBar::tab:selected {{
                color: {brand.PRIMARY};
                border-bottom-color: {brand.PRIMARY};
            }}
        """)

    def add_tab(self, title: str, widget: QWidget, icon: str = None):
        """Tab ekle"""
        if icon:
            self.addTab(widget, f"{icon}  {title}")
        else:
            self.addTab(widget, title)


# =============================================================================
# NEXOR MODAL (Dialog)
# =============================================================================

class NexorModal(QDialog):
    """
    Modal dialog

    Kullanim:
        modal = NexorModal(theme, "Onay", "Bu kaydi silmek istediginize emin misiniz?")
        if modal.exec() == QDialog.Accepted:
            # Silme islemi
    """

    def __init__(self, theme: dict = None, title: str = "", message: str = None,
                 modal_type: str = "confirm", parent=None):
        super().__init__(parent)
        self.theme = theme  # backward compat
        self._modal_type = modal_type

        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)

        self._setup_ui(title, message)

    def _setup_ui(self, title: str, message: str):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_CARD};
            }}
            QLabel {{
                color: {brand.TEXT};
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_4)

        # Baslik
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {brand.FS_HEADING_SM}px;
            font-weight: {brand.FW_SEMIBOLD};
            color: {brand.TEXT};
        """)
        layout.addWidget(title_label)

        # Mesaj
        if message:
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            msg_label.setStyleSheet(f"""
                font-size: {brand.FS_BODY}px;
                color: {brand.TEXT_MUTED};
            """)
            layout.addWidget(msg_label)

        # Icerik alani (ozel widget eklemek icin)
        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._content)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        if self._modal_type == "confirm":
            cancel_btn = NexorButton("Iptal", self.theme, "secondary")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)

            confirm_btn = NexorButton("Onayla", self.theme, "primary")
            confirm_btn.clicked.connect(self.accept)
            btn_layout.addWidget(confirm_btn)

        elif self._modal_type == "delete":
            cancel_btn = NexorButton("Iptal", self.theme, "secondary")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)

            delete_btn = NexorButton("Sil", self.theme, "danger")
            delete_btn.clicked.connect(self.accept)
            btn_layout.addWidget(delete_btn)

        else:  # info
            ok_btn = NexorButton("Tamam", self.theme, "primary")
            ok_btn.clicked.connect(self.accept)
            btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def add_widget(self, widget: QWidget):
        """Icerik ekle"""
        self._content_layout.addWidget(widget)

    @staticmethod
    def confirm(theme: dict, title: str, message: str, parent=None) -> bool:
        """Onay dialog'u goster"""
        modal = NexorModal(theme, title, message, "confirm", parent)
        return modal.exec() == QDialog.Accepted

    @staticmethod
    def delete_confirm(theme: dict, title: str, message: str, parent=None) -> bool:
        """Silme onay dialog'u goster"""
        modal = NexorModal(theme, title, message, "delete", parent)
        return modal.exec() == QDialog.Accepted

    @staticmethod
    def info(theme: dict, title: str, message: str, parent=None):
        """Bilgi dialog'u goster"""
        modal = NexorModal(theme, title, message, "info", parent)
        modal.exec()


# =============================================================================
# NEXOR SEARCH BOX
# =============================================================================

class NexorSearchBox(QLineEdit):
    """
    Arama kutusu

    Kullanim:
        search = NexorSearchBox(theme)
        search.search_triggered.connect(on_search)
    """

    search_triggered = Signal(str)

    def __init__(self, theme: dict = None, placeholder: str = "Ara... (Ctrl+K)", parent=None):
        super().__init__(parent)
        self.theme = theme  # backward compat
        self.setPlaceholderText(f"🔍  {placeholder}")
        self._apply_style()

        # Enter'a basildiginda arama yap
        self.returnPressed.connect(lambda: self.search_triggered.emit(self.text()))

    def _apply_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_MD}px;
                padding: {brand.SP_3}px {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                min-width: 250px;
            }}
            QLineEdit:hover {{
                border-color: {brand.BORDER_HARD};
            }}
            QLineEdit:focus {{
                border-color: {brand.PRIMARY};
            }}
        """)
        self.setMinimumHeight(42)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    # Constants (deprecated - brand kullan)
    'Spacing',
    'BorderRadius',
    'FontSize',
    'get_theme_colors',

    # Components
    'NexorCard',
    'NexorStatsCard',
    'NexorButton',
    'NexorBadge',
    'NexorInput',
    'NexorSelect',
    'NexorTable',
    'NexorForm',
    'NexorFormField',
    'NexorPageHeader',
    'NexorTabs',
    'NexorModal',
    'NexorSearchBox',
]
