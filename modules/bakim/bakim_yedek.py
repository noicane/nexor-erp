# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Yedek Parça Sayfası
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt

from components.base_page import BasePage
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


class BakimYedekPage(BasePage):
    """Yedek Parça Sayfası - Modern UI (Yapım Aşamasında)"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)
        
        # Container Card
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 20px;
                padding: 40px;
            }}
        """)
        container.setMaximumSize(500, 400)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(Qt.black)
        container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(20)
        
        # Icon Frame
        icon_frame = QFrame()
        icon_frame.setFixedSize(100, 100)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: {s['gradient']};
                border-radius: 25px;
            }}
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel("🔧")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; background: transparent;")
        icon_layout.addWidget(icon_label)
        
        icon_container = QHBoxLayout()
        icon_container.addStretch()
        icon_container.addWidget(icon_frame)
        icon_container.addStretch()
        container_layout.addLayout(icon_container)
        
        # Title
        title_label = QLabel("Yedek Parça Yönetimi")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            color: {s['text']};
            font-size: 28px;
            font-weight: 700;
        """)
        container_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Bu modül yapım aşamasındadır")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet(f"""
            color: {s['text_secondary']};
            font-size: 15px;
        """)
        container_layout.addWidget(subtitle_label)
        
        # Description
        desc_label = QLabel(
            "Yedek parça stok takibi, minimum stok seviyeleri,\n"
            "parça-ekipman ilişkileri ve sipariş yönetimi\n"
            "yakında eklenecektir."
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet(f"""
            color: {s['text_muted']};
            font-size: 13px;
            line-height: 1.6;
        """)
        container_layout.addWidget(desc_label)
        
        container_layout.addSpacing(10)
        
        # Progress indicator
        progress_frame = QFrame()
        progress_frame.setStyleSheet(f"""
            QFrame {{
                background: {s['border']};
                border-radius: 4px;
            }}
        """)
        progress_frame.setFixedHeight(8)
        progress_frame.setMaximumWidth(300)
        
        progress_fill = QFrame(progress_frame)
        progress_fill.setStyleSheet(f"""
            QFrame {{
                background: {s['primary']};
                border-radius: 4px;
            }}
        """)
        progress_fill.setGeometry(0, 0, 90, 8)  # 30% progress
        
        progress_container = QHBoxLayout()
        progress_container.addStretch()
        progress_container.addWidget(progress_frame)
        progress_container.addStretch()
        container_layout.addLayout(progress_container)
        
        # Progress text
        progress_text = QLabel("Geliştirme: %30")
        progress_text.setAlignment(Qt.AlignCenter)
        progress_text.setStyleSheet(f"""
            color: {s['text_muted']};
            font-size: 12px;
        """)
        container_layout.addWidget(progress_text)
        
        # Add container to main layout
        main_container = QHBoxLayout()
        main_container.addStretch()
        main_container.addWidget(container)
        main_container.addStretch()
        
        layout.addStretch()
        layout.addLayout(main_container)
        layout.addStretch()
