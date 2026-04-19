# -*- coding: utf-8 -*-
"""
NEXOR ERP - Firma Bilgileri Sayfasi
Programi kullanan firmanin bilgilerini yonetir (PDF ciktilari icin)
"""
import os
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTextEdit, QFileDialog, QScrollArea, QWidget, QMessageBox, QComboBox,
    QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from components.base_page import BasePage
from core.firma_bilgileri import get_firma_bilgileri, set_firma_bilgileri
from core.nexor_brand import brand


class SistemFirmaPage(BasePage):
    """Firma Bilgileri Ayar Sayfasi"""

    def __init__(self, theme: dict, **kwargs):
        super().__init__(theme)
        self._logo_path = ""
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Tab kapsayicisi - 3 sekme: Firma + Etiket Sablonlari + PC Yazici"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            f"QTabWidget::pane {{ border: 1px solid {brand.BORDER}; "
            f"border-radius: 8px; background: {brand.BG_MAIN}; }}"
            f"QTabBar::tab {{ background: {brand.BG_CARD}; color: {brand.TEXT_MUTED}; "
            f"padding: 10px 18px; border: 1px solid {brand.BORDER}; "
            f"border-bottom: none; border-top-left-radius: 8px; "
            f"border-top-right-radius: 8px; margin-right: 2px; "
            f"font-size: 13px; font-weight: bold; }}"
            f"QTabBar::tab:selected {{ background: {brand.PRIMARY}; color: white; }}"
            f"QTabBar::tab:hover:!selected {{ background: {brand.BG_HOVER}; "
            f"color: {brand.TEXT}; }}"
        )

        # Tab 1: Firma Bilgileri (mevcut sayfa)
        firma_widget = self._build_firma_tab()
        tabs.addTab(firma_widget, "🏢 Firma Bilgileri")

        # Tab 2: Etiket Sablonlari (kullanim yeri -> sablon atamalari, GLOBAL)
        try:
            from modules.sistem.sistem_etiket_atama import SistemEtiketAtamaTab
            self.etiket_tab = SistemEtiketAtamaTab(self.theme)
            tabs.addTab(self.etiket_tab, "📄 Etiket Sablonlari")
        except Exception as e:
            print(f"[sistem_firma] Etiket sablon sekmesi yuklenemedi: {e}")

        # Tab 3: PC Yazici Atamalari (PC bazli yazici atamalari)
        try:
            from modules.sistem.sistem_pc_yazici import SistemPCYaziciTab
            self.yazici_tab = SistemPCYaziciTab(self.theme)
            tabs.addTab(self.yazici_tab, "🖨️ PC Yazici Atamalari")
        except Exception as e:
            print(f"[sistem_firma] PC yazici sekmesi yuklenemedi: {e}")

        main_layout.addWidget(tabs)

    def _build_firma_tab(self) -> QScrollArea:
        """Firma bilgileri sekmesi (mevcut sayfa - aynen korundu)"""
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
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 12px;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)

        title_icon = QLabel("🏢")
        title_icon.setStyleSheet("font-size: 28px; background: transparent;")
        header_layout.addWidget(title_icon)

        title_text = QVBoxLayout()
        title = QLabel("Firma Bilgileri")
        title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: 22px; font-weight: bold;"
        )
        subtitle = QLabel("PDF ve raporlarda gorunecek firma bilgilerini duzenleyin")
        subtitle.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: 13px;"
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
            f"background: {brand.BG_INPUT}; "
            f"border: 2px dashed {brand.BORDER}; border-radius: 8px;"
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
            f"color: {brand.TEXT_MUTED}; font-size: 12px;"
        )
        btn_layout.addWidget(self.lbl_logo_path)
        btn_layout.addStretch()

        logo_layout.addLayout(btn_layout)
        logo_group.layout().addLayout(logo_layout)
        layout.addWidget(logo_group)

        # === PDF TEMA SECIMI ===
        pdf_group = self._create_section(
            "", "PDF Sablon Temasi", "Tum PDF ciktilarinda kullanilacak gorunum temasi"
        )
        pdf_layout = QVBoxLayout()
        pdf_layout.setSpacing(brand.SP_3)

        tema_row = QHBoxLayout()
        tema_row.setSpacing(brand.SP_3)
        tema_lbl = QLabel("Aktif Tema:")
        tema_lbl.setStyleSheet(f"color: {brand.TEXT}; font-size: {brand.FS_BODY}px;")
        tema_row.addWidget(tema_lbl)

        self.cmb_pdf_tema = QComboBox()
        self.cmb_pdf_tema.setStyleSheet(
            f"QComboBox {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: {brand.R_SM}px; "
            f"padding: {brand.SP_2}px {brand.SP_3}px; font-size: {brand.FS_BODY}px; }}"
        )
        tema_isimleri = {
            "kurumsal": "Kurumsal (Koyu header, kirmizi accent)",
            "profesyonel": "Profesyonel (Mavi ton, modern)",
            "minimal": "Minimal (Sade siyah-beyaz)",
        }
        from utils.pdf_template import get_available_themes, get_pdf_theme_name
        for key in get_available_themes():
            self.cmb_pdf_tema.addItem(tema_isimleri.get(key, key), key)
        # Aktif temayi sec
        aktif = get_pdf_theme_name()
        for i in range(self.cmb_pdf_tema.count()):
            if self.cmb_pdf_tema.itemData(i) == aktif:
                self.cmb_pdf_tema.setCurrentIndex(i)
                break
        tema_row.addWidget(self.cmb_pdf_tema)

        btn_onizle = QPushButton("Onizle")
        btn_onizle.setCursor(Qt.PointingHandCursor)
        btn_onizle.setStyleSheet(
            f"QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: {brand.R_SM}px; "
            f"padding: {brand.SP_2}px {brand.SP_4}px; font-size: {brand.FS_BODY}px; }}"
            f"QPushButton:hover {{ border-color: {brand.PRIMARY}; }}"
        )
        btn_onizle.clicked.connect(self._preview_pdf_tema)
        tema_row.addWidget(btn_onizle)
        tema_row.addStretch()

        pdf_layout.addLayout(tema_row)

        tema_desc = QLabel(
            "Kurumsal: Satis odakli firmalar icin koyu ve profesyonel\n"
            "Profesyonel: Mavi tonlu, modern ve temiz gorunum\n"
            "Minimal: Sade ve ekonomik baski icin uygun"
        )
        tema_desc.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;")
        pdf_layout.addWidget(tema_desc)

        pdf_group.layout().addLayout(pdf_layout)
        layout.addWidget(pdf_group)

        # === KAYDET BUTONU ===
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.btn_kaydet = QPushButton("💾  Kaydet")
        self.btn_kaydet.setCursor(Qt.PointingHandCursor)
        self.btn_kaydet.setFixedHeight(44)
        self.btn_kaydet.setMinimumWidth(160)
        self.btn_kaydet.setStyleSheet(
            f"QPushButton {{ background: {brand.PRIMARY}; "
            f"color: white; border: none; border-radius: 10px; padding: 10px 32px; "
            f"font-weight: bold; font-size: 14px; }}"
            f"QPushButton:hover {{ background: {brand.PRIMARY}; }}"
        )
        self.btn_kaydet.clicked.connect(self._on_save)
        save_layout.addWidget(self.btn_kaydet)
        layout.addLayout(save_layout)

        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _create_section(self, icon: str, title: str, subtitle: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 12px;"
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
            f"color: {brand.TEXT}; font-weight: bold; font-size: 15px;"
        )
        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: 12px;"
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
            f"color: {brand.TEXT}; font-size: 13px; font-weight: bold;"
        )
        row.addWidget(lbl)

        txt = QLineEdit()
        txt.setFixedHeight(36)
        txt.setStyleSheet(
            f"QLineEdit {{ background: {brand.BG_INPUT}; "
            f"color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 8px; "
            f"padding: 4px 12px; font-size: 13px; }}"
            f"QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}"
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
            f"color: {brand.TEXT}; font-size: 13px; font-weight: bold;"
        )
        row.addWidget(lbl)

        txt = QTextEdit()
        txt.setFixedHeight(72)
        txt.setStyleSheet(
            f"QTextEdit {{ background: {brand.BG_INPUT}; "
            f"color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 8px; "
            f"padding: 8px 12px; font-size: 13px; }}"
            f"QTextEdit:focus {{ border-color: {brand.PRIMARY}; }}"
        )
        row.addWidget(txt)
        parent_layout.addLayout(row)
        return txt

    def _normal_btn_style(self) -> str:
        return (
            f"QPushButton {{ background: {brand.BG_INPUT}; "
            f"color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 8px; "
            f"padding: 10px 16px; font-size: 13px; }}"
            f"QPushButton:hover {{ border-color: {brand.PRIMARY}; "
            f"background: {brand.BG_HOVER}; }}"
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

        # PDF tema kaydet
        try:
            from utils.pdf_template import set_pdf_theme_name
            secilen_tema = self.cmb_pdf_tema.currentData()
            if secilen_tema:
                set_pdf_theme_name(secilen_tema)
        except Exception as e:
            print(f"[sistem_firma] PDF tema kaydetme hatasi: {e}")

        if ok:
            QMessageBox.information(self, "Basarili", "Firma bilgileri ve PDF tema ayarlari kaydedildi.")
        else:
            QMessageBox.critical(self, "Hata", "Firma bilgileri kaydedilemedi!")

    def _preview_pdf_tema(self):
        """Secili PDF temasinin onizlemesini olustur ve ac."""
        try:
            from utils.pdf_template import PDFTemplate
            from reportlab.lib.units import mm

            tema = self.cmb_pdf_tema.currentData() or "kurumsal"

            tpl = PDFTemplate(
                title="ORNEK FORM ONIZLEME",
                form_no="DEMO-001",
                filename=f"PDF_Onizleme_{tema}.pdf",
                theme=tema,
            )
            y = tpl.content_top

            y = tpl.section("PERSONEL BILGILERI", y)
            y = tpl.field_row(y, "Ad Soyad", "Ahmet Yilmaz", "Sicil No", "NXR001")
            y = tpl.field_row(y, "Departman", "Uretim", "Pozisyon", "Operator")

            y = tpl.section("FORM DETAYLARI", y)
            y = tpl.field_row(y, "Tarih", "16.04.2026", "Durum", "ONAYLANDI")
            y = tpl.big_value(tpl.margin + 4*mm, y, "Toplam", "5 Gun", color=tpl.theme['success'])
            y -= 6 * mm

            y = tpl.section("KALEM LISTESI", y)
            y = tpl.table(y,
                ["#", "Malzeme", "Miktar", "Birim", "Tutar"],
                [
                    ["1", "Cinko Nikel Kimyasal", "100", "kg", "2.500,00"],
                    ["2", "Kataforez Boyasi", "50", "lt", "1.750,00"],
                    ["3", "Aski Teli 2mm", "500", "mt", "850,00"],
                ],
                col_widths=[15*mm, 60*mm, 25*mm, 20*mm, 35*mm]
            )

            y = tpl.section("ONAY VE IMZA", y)
            tpl.signature_row(y, ["Hazirlayan", "Onaylayan", "Mudur"])

            path = tpl.finish(open_file=True)
            print(f"[sistem_firma] PDF onizleme: {path}")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF onizleme olusturulamadi:\n{e}")

    def update_theme(self, theme: dict):
        self.theme = theme
        self._apply_global_style()
