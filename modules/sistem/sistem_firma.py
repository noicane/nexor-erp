# -*- coding: utf-8 -*-
"""
NEXOR ERP - Firma Bilgileri Sayfasi
Programi kullanan firmanin bilgilerini yonetir (PDF ciktilari icin)
"""
import os
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTextEdit, QFileDialog, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from components.base_page import BasePage
from core.firma_bilgileri import get_firma_bilgileri, set_firma_bilgileri


class SistemFirmaPage(BasePage):
    """Firma Bilgileri Ayar Sayfasi"""

    def __init__(self, theme: dict, **kwargs):
        super().__init__(theme)
        self._logo_path = ""
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Baslik
        header = QFrame()
        header.setStyleSheet(
            f"background: {self.theme['bg_card']}; "
            f"border: 1px solid {self.theme['border']}; border-radius: 12px;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)

        title_icon = QLabel("🏢")
        title_icon.setStyleSheet("font-size: 28px; background: transparent;")
        header_layout.addWidget(title_icon)

        title_text = QVBoxLayout()
        title = QLabel("Firma Bilgileri")
        title.setStyleSheet(
            f"color: {self.theme['text']}; font-size: 22px; font-weight: bold;"
        )
        subtitle = QLabel("PDF ve raporlarda gorunecek firma bilgilerini duzenleyin")
        subtitle.setStyleSheet(
            f"color: {self.theme['text_secondary']}; font-size: 13px;"
        )
        title_text.addWidget(title)
        title_text.addWidget(subtitle)
        header_layout.addLayout(title_text)
        header_layout.addStretch()
        layout.addWidget(header)

        # === FIRMA BILGILERI ===
        firma_group = self._create_section(
            "📋", "Genel Bilgiler", "Firma adi, vergi no ve iletisim bilgileri"
        )
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)

        self.txt_firma_adi = self._add_form_field(form_layout, "Firma Adi *")
        self.txt_vergi_no = self._add_form_field(form_layout, "Vergi No")
        self.txt_telefon = self._add_form_field(form_layout, "Telefon")
        self.txt_email = self._add_form_field(form_layout, "E-posta")
        self.txt_adres = self._add_form_textarea(form_layout, "Adres")

        firma_group.layout().addLayout(form_layout)
        layout.addWidget(firma_group)

        # === LOGO ===
        logo_group = self._create_section(
            "🖼️", "Firma Logosu", "PDF ve raporlarda kullanilacak logo"
        )
        logo_layout = QVBoxLayout()
        logo_layout.setSpacing(12)

        # Logo onizleme
        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(200, 100)
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setStyleSheet(
            f"background: {self.theme['bg_input']}; "
            f"border: 2px dashed {self.theme['border']}; border-radius: 8px;"
        )
        self.logo_preview.setText("Logo secilmedi")
        logo_layout.addWidget(self.logo_preview)

        # Logo butonlari
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_logo_sec = QPushButton("📁 Logo Sec")
        self.btn_logo_sec.setCursor(Qt.PointingHandCursor)
        self.btn_logo_sec.setStyleSheet(self._normal_btn_style())
        self.btn_logo_sec.clicked.connect(self._on_logo_select)
        btn_layout.addWidget(self.btn_logo_sec)

        self.btn_logo_temizle = QPushButton("🗑️ Temizle")
        self.btn_logo_temizle.setCursor(Qt.PointingHandCursor)
        self.btn_logo_temizle.setStyleSheet(self._normal_btn_style())
        self.btn_logo_temizle.clicked.connect(self._on_logo_clear)
        btn_layout.addWidget(self.btn_logo_temizle)

        self.lbl_logo_path = QLabel("Logo secilmedi")
        self.lbl_logo_path.setStyleSheet(
            f"color: {self.theme['text_muted']}; font-size: 12px;"
        )
        btn_layout.addWidget(self.lbl_logo_path)
        btn_layout.addStretch()

        logo_layout.addLayout(btn_layout)
        logo_group.layout().addLayout(logo_layout)
        layout.addWidget(logo_group)

        # === KAYDET BUTONU ===
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.btn_kaydet = QPushButton("💾  Kaydet")
        self.btn_kaydet.setCursor(Qt.PointingHandCursor)
        self.btn_kaydet.setFixedHeight(44)
        self.btn_kaydet.setMinimumWidth(160)
        self.btn_kaydet.setStyleSheet(
            f"QPushButton {{ background: {self.theme.get('gradient_css', self.theme.get('primary', '#DC2626'))}; "
            f"color: white; border: none; border-radius: 10px; padding: 10px 32px; "
            f"font-weight: bold; font-size: 14px; }}"
            f"QPushButton:hover {{ background: {self.theme.get('primary', '#DC2626')}; }}"
        )
        self.btn_kaydet.clicked.connect(self._on_save)
        save_layout.addWidget(self.btn_kaydet)
        layout.addLayout(save_layout)

        layout.addStretch()
        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _create_section(self, icon: str, title: str, subtitle: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {self.theme['bg_card']}; "
            f"border: 1px solid {self.theme['border']}; border-radius: 12px;"
        )
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
        title_lbl.setStyleSheet(
            f"color: {self.theme['text']}; font-weight: bold; font-size: 15px;"
        )
        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setStyleSheet(
            f"color: {self.theme['text_muted']}; font-size: 12px;"
        )
        title_layout.addWidget(title_lbl)
        title_layout.addWidget(subtitle_lbl)
        header.addLayout(title_layout)
        header.addStretch()
        layout.addLayout(header)
        return frame

    def _add_form_field(self, parent_layout: QVBoxLayout, label_text: str) -> QLineEdit:
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setFixedWidth(120)
        lbl.setStyleSheet(
            f"color: {self.theme['text']}; font-size: 13px; font-weight: bold;"
        )
        row.addWidget(lbl)

        txt = QLineEdit()
        txt.setFixedHeight(36)
        txt.setStyleSheet(
            f"QLineEdit {{ background: {self.theme['bg_input']}; "
            f"color: {self.theme['text']}; "
            f"border: 1px solid {self.theme['border']}; border-radius: 8px; "
            f"padding: 4px 12px; font-size: 13px; }}"
            f"QLineEdit:focus {{ border-color: {self.theme.get('primary', '#DC2626')}; }}"
        )
        row.addWidget(txt)
        parent_layout.addLayout(row)
        return txt

    def _add_form_textarea(self, parent_layout: QVBoxLayout, label_text: str) -> QTextEdit:
        row = QHBoxLayout()
        row.setAlignment(Qt.AlignTop)
        lbl = QLabel(label_text)
        lbl.setFixedWidth(120)
        lbl.setStyleSheet(
            f"color: {self.theme['text']}; font-size: 13px; font-weight: bold;"
        )
        row.addWidget(lbl)

        txt = QTextEdit()
        txt.setFixedHeight(72)
        txt.setStyleSheet(
            f"QTextEdit {{ background: {self.theme['bg_input']}; "
            f"color: {self.theme['text']}; "
            f"border: 1px solid {self.theme['border']}; border-radius: 8px; "
            f"padding: 8px 12px; font-size: 13px; }}"
            f"QTextEdit:focus {{ border-color: {self.theme.get('primary', '#DC2626')}; }}"
        )
        row.addWidget(txt)
        parent_layout.addLayout(row)
        return txt

    def _normal_btn_style(self) -> str:
        return (
            f"QPushButton {{ background: {self.theme['bg_input']}; "
            f"color: {self.theme['text']}; "
            f"border: 1px solid {self.theme['border']}; border-radius: 8px; "
            f"padding: 10px 16px; font-size: 13px; }}"
            f"QPushButton:hover {{ border-color: {self.theme.get('primary', '#DC2626')}; "
            f"background: {self.theme.get('bg_hover', self.theme['bg_input'])}; }}"
        )

    def _load_data(self):
        data = get_firma_bilgileri()
        self.txt_firma_adi.setText(data.get('name', ''))
        self.txt_vergi_no.setText(data.get('tax_id', ''))
        self.txt_telefon.setText(data.get('phone', ''))
        self.txt_email.setText(data.get('email', ''))
        self.txt_adres.setPlainText(data.get('address', ''))
        self._logo_path = data.get('logo_path', '')
        self._update_logo_preview()

    def _update_logo_preview(self):
        if self._logo_path and os.path.isfile(self._logo_path):
            pixmap = QPixmap(self._logo_path)
            if not pixmap.isNull():
                self.logo_preview.setPixmap(
                    pixmap.scaled(196, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self.lbl_logo_path.setText(os.path.basename(self._logo_path))
                return
        self.logo_preview.clear()
        self.logo_preview.setText("Logo secilmedi")
        self.lbl_logo_path.setText("Logo secilmedi")

    def _on_logo_select(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Logo Sec", "", "Resim Dosyalari (*.png *.jpg *.jpeg *.bmp)"
        )
        if file:
            self._logo_path = file
            self._update_logo_preview()

    def _on_logo_clear(self):
        self._logo_path = ""
        self._update_logo_preview()

    def _on_save(self):
        data = {
            'name': self.txt_firma_adi.text().strip(),
            'address': self.txt_adres.toPlainText().strip(),
            'phone': self.txt_telefon.text().strip(),
            'email': self.txt_email.text().strip(),
            'tax_id': self.txt_vergi_no.text().strip(),
            'logo_path': self._logo_path,
        }

        if not data['name']:
            QMessageBox.warning(self, "Uyari", "Firma adi bos birakilamaz!")
            self.txt_firma_adi.setFocus()
            return

        ok = set_firma_bilgileri(data)
        if ok:
            QMessageBox.information(self, "Basarili", "Firma bilgileri kaydedildi.")
        else:
            QMessageBox.critical(self, "Hata", "Firma bilgileri kaydedilemedi!")

    def update_theme(self, theme: dict):
        self.theme = theme
        self._apply_global_style()
