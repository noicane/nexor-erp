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
