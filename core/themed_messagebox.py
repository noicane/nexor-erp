# -*- coding: utf-8 -*-
"""
NEXOR ERP - Themed MessageBox
QMessageBox'ı tema uyumlu hale getiren modül.

Kullanım:
    main.py'de uygulama başlarken:
    
    from core.themed_messagebox import patch_messagebox
    patch_messagebox(theme)
    
    Bu çağrı yapıldıktan sonra tüm QMessageBox.warning(), 
    QMessageBox.critical(), QMessageBox.information(), QMessageBox.question()
    çağrıları otomatik olarak tema uyumlu olacak.
"""

from PySide6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QWidget, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon

# Global tema referansı
_current_theme = None


def set_theme(theme: dict):
    """Tema referansını güncelle"""
    global _current_theme
    _current_theme = theme


def get_theme() -> dict:
    """Mevcut temayı döndür, yoksa varsayılan dark tema"""
    global _current_theme
    if _current_theme is None:
        return {
            'bg_card': '#1A1A1A',
            'bg_input': '#252525',
            'bg_hover': '#2A2A2A',
            'text': '#FFFFFF',
            'text_secondary': '#AAAAAA',
            'border': '#2A2A2A',
            'primary': '#DC2626',
            'primary_hover': '#B91C1C',
            'error': '#EF4444',
            'warning': '#F59E0B',
            'info': '#3B82F6',
            'success': '#10B981',
        }
    return _current_theme


class ThemedMessageBox(QDialog):
    """Tema uyumlu özel MessageBox"""
    
    # Icon tipleri
    NoIcon = 0
    Information = 1
    Warning = 2
    Critical = 3
    Question = 4
    
    # Standart butonlar
    Ok = 0x00000400
    Cancel = 0x00400000
    Yes = 0x00004000
    No = 0x00010000
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self._icon_type = self.NoIcon
        self._buttons = self.Ok
        self._result_button = None
        self._clicked_button = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        t = get_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border']};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # Üst kısım: Icon + Mesaj
        top_layout = QHBoxLayout()
        top_layout.setSpacing(16)
        
        # Icon label
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(48, 48)
        self._icon_label.setAlignment(Qt.AlignTop)
        top_layout.addWidget(self._icon_label)
        
        # Mesaj label
        self._text_label = QLabel()
        self._text_label.setWordWrap(True)
        self._text_label.setMinimumWidth(280)
        self._text_label.setMaximumWidth(450)
        self._text_label.setStyleSheet(f"""
            QLabel {{
                color: {t['text']};
                font-size: 13px;
                line-height: 1.5;
                background: transparent;
            }}
        """)
        self._text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top_layout.addWidget(self._text_label, 1)
        
        layout.addLayout(top_layout)
        
        # Buton alanı
        self._button_layout = QHBoxLayout()
        self._button_layout.setSpacing(8)
        self._button_layout.addStretch()
        layout.addLayout(self._button_layout)
    
    def setWindowTitle(self, title: str):
        """Pencere başlığı"""
        super().setWindowTitle(title)
    
    def setText(self, text: str):
        """Ana mesaj metni"""
        self._text_label.setText(text)
    
    def setIcon(self, icon_type: int):
        """Icon tipini ayarla"""
        self._icon_type = icon_type
        self._update_icon()
    
    def _update_icon(self):
        """Icon'u güncelle"""
        t = get_theme()
        
        # SVG icon'ları kullan
        icons = {
            self.Information: ('ℹ️', t.get('info', '#3B82F6')),
            self.Warning: ('⚠️', t.get('warning', '#F59E0B')),
            self.Critical: ('❌', t.get('error', '#EF4444')),
            self.Question: ('❓', t.get('info', '#3B82F6')),
        }
        
        if self._icon_type in icons:
            emoji, color = icons[self._icon_type]
            self._icon_label.setText(emoji)
            self._icon_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 32px;
                    background: transparent;
                }}
            """)
        else:
            self._icon_label.clear()
    
    def setStandardButtons(self, buttons: int):
        """Standart butonları ayarla"""
        self._buttons = buttons
        self._create_buttons()
    
    def _create_buttons(self):
        """Butonları oluştur"""
        t = get_theme()
        
        # Mevcut butonları temizle
        while self._button_layout.count() > 1:
            item = self._button_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        button_style = f"""
            QPushButton {{
                background-color: {t['bg_input']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                padding: 8px 20px;
                min-width: 80px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {t['bg_hover']};
                border-color: {t['primary']};
            }}
            QPushButton:pressed {{
                background-color: {t['primary']};
                color: white;
            }}
        """
        
        primary_button_style = f"""
            QPushButton {{
                background-color: {t['primary']};
                color: white;
                border: 1px solid {t['primary']};
                border-radius: 6px;
                padding: 8px 20px;
                min-width: 80px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {t.get('primary_hover', '#B91C1C')};
            }}
            QPushButton:pressed {{
                background-color: {t.get('primary_hover', '#B91C1C')};
            }}
        """
        
        buttons_config = [
            (self.Yes, "Evet", True),
            (self.No, "Hayır", False),
            (self.Ok, "Tamam", True),
            (self.Cancel, "İptal", False),
        ]
        
        created_buttons = []
        for btn_flag, btn_text, is_primary in buttons_config:
            if self._buttons & btn_flag:
                btn = QPushButton(btn_text)
                btn.setStyleSheet(primary_button_style if is_primary else button_style)
                btn.clicked.connect(lambda checked, f=btn_flag: self._on_button_clicked(f))
                created_buttons.append(btn)
        
        # Butonları ekle (önce secondary, sonra primary)
        for btn in reversed(created_buttons):
            self._button_layout.insertWidget(self._button_layout.count() - 1, btn)
    
    def _on_button_clicked(self, button_flag: int):
        """Buton tıklandığında"""
        self._result_button = button_flag
        
        if button_flag in (self.Ok, self.Yes):
            self.accept()
        else:
            self.reject()
    
    def exec(self) -> int:
        """Dialog'u göster ve sonucu döndür"""
        super().exec()
        return self._result_button if self._result_button else self.Ok
    
    def result(self) -> int:
        """Sonuç butonunu döndür"""
        return self._result_button
    
    # =========================================================================
    # STATIC METHODS - QMessageBox uyumluluğu için
    # =========================================================================
    
    @staticmethod
    def information(parent, title: str, text: str, buttons=None) -> int:
        """Bilgi mesajı göster"""
        if buttons is None:
            buttons = ThemedMessageBox.Ok
        
        msg = ThemedMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(ThemedMessageBox.Information)
        msg.setStandardButtons(buttons)
        return msg.exec()
    
    @staticmethod
    def warning(parent, title: str, text: str, buttons=None) -> int:
        """Uyarı mesajı göster"""
        if buttons is None:
            buttons = ThemedMessageBox.Ok
        
        msg = ThemedMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(ThemedMessageBox.Warning)
        msg.setStandardButtons(buttons)
        return msg.exec()
    
    @staticmethod
    def critical(parent, title: str, text: str, buttons=None) -> int:
        """Hata mesajı göster"""
        if buttons is None:
            buttons = ThemedMessageBox.Ok
        
        msg = ThemedMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(ThemedMessageBox.Critical)
        msg.setStandardButtons(buttons)
        return msg.exec()
    
    @staticmethod
    def question(parent, title: str, text: str, buttons=None) -> int:
        """Soru mesajı göster"""
        if buttons is None:
            buttons = ThemedMessageBox.Yes | ThemedMessageBox.No
        
        msg = ThemedMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(ThemedMessageBox.Question)
        msg.setStandardButtons(buttons)
        return msg.exec()


# =============================================================================
# MONKEY PATCHING - QMessageBox'ı otomatik değiştir
# =============================================================================

# Orijinal QMessageBox metodlarını sakla
_original_information = QMessageBox.information
_original_warning = QMessageBox.warning
_original_critical = QMessageBox.critical
_original_question = QMessageBox.question


def _patched_information(parent, title, text, *args, **kwargs):
    """Patched information metodu"""
    buttons = ThemedMessageBox.Ok
    if args:
        buttons = args[0] if args[0] else ThemedMessageBox.Ok
    return ThemedMessageBox.information(parent, title, text, buttons)


def _patched_warning(parent, title, text, *args, **kwargs):
    """Patched warning metodu"""
    buttons = ThemedMessageBox.Ok
    if args:
        buttons = args[0] if args[0] else ThemedMessageBox.Ok
    return ThemedMessageBox.warning(parent, title, text, buttons)


def _patched_critical(parent, title, text, *args, **kwargs):
    """Patched critical metodu"""
    buttons = ThemedMessageBox.Ok
    if args:
        buttons = args[0] if args[0] else ThemedMessageBox.Ok
    return ThemedMessageBox.critical(parent, title, text, buttons)


def _patched_question(parent, title, text, *args, **kwargs):
    """Patched question metodu"""
    buttons = ThemedMessageBox.Yes | ThemedMessageBox.No
    if args:
        buttons = args[0] if args[0] else buttons
    return ThemedMessageBox.question(parent, title, text, buttons)


def patch_messagebox(theme: dict = None):
    """
    QMessageBox metodlarını ThemedMessageBox ile değiştir.
    Bu fonksiyon çağrıldıktan sonra tüm QMessageBox çağrıları
    otomatik olarak tema uyumlu olacak.
    
    Args:
        theme: Tema dictionary (opsiyonel, None ise varsayılan dark tema)
    """
    if theme:
        set_theme(theme)
    
    # QMessageBox static metodlarını değiştir
    QMessageBox.information = staticmethod(_patched_information)
    QMessageBox.warning = staticmethod(_patched_warning)
    QMessageBox.critical = staticmethod(_patched_critical)
    QMessageBox.question = staticmethod(_patched_question)
    
    print("[INFO] QMessageBox tema desteği aktif edildi")


def unpatch_messagebox():
    """Orijinal QMessageBox metodlarını geri yükle"""
    QMessageBox.information = _original_information
    QMessageBox.warning = _original_warning
    QMessageBox.critical = _original_critical
    QMessageBox.question = _original_question
    
    print("[INFO] QMessageBox orijinal haline döndürüldü")


def update_theme(theme: dict):
    """Temayı güncelle (tema değiştiğinde çağrılmalı)"""
    set_theme(theme)
