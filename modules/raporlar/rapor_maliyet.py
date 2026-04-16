# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Maliyet Raporları Sayfası
"""
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

from components.base_page import BasePage
from core.nexor_brand import brand


class RaporMaliyetPage(BasePage):
    """Maliyet Raporları Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon
        icon_frame = QFrame()
        icon_frame.setFixedSize(80, 80)
        icon_frame.setStyleSheet(f"background: {brand.PRIMARY_SOFT}; border-radius: 20px;")
        i_layout = QVBoxLayout(icon_frame)
        i_layout.setContentsMargins(0, 0, 0, 0)
        i_label = QLabel("📈")
        i_label.setAlignment(Qt.AlignCenter)
        i_label.setStyleSheet("font-size: 36px; background: transparent;")
        i_layout.addWidget(i_label)
        
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(icon_frame)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        layout.addSpacing(16)
        
        # Başlık
        t_label = QLabel("Maliyet Raporları")
        t_label.setAlignment(Qt.AlignCenter)
        t_label.setStyleSheet(f"color: {brand.TEXT}; font-size: 24px; font-weight: bold;")
        layout.addWidget(t_label)
        
        # Alt metin
        d_label = QLabel("Bu sayfa yapım aşamasında...")
        d_label.setAlignment(Qt.AlignCenter)
        d_label.setStyleSheet(f"color: {brand.TEXT_MUTED};")
        layout.addWidget(d_label)
