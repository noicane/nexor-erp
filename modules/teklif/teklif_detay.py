# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Teklif Detay/Düzenleme Dialog
Kaplama sektörü teklif oluşturma ve düzenleme
"""
import os
import sys
import shutil
from datetime import datetime, date, timedelta
from decimal import Decimal

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QGroupBox,
    QHeaderView, QMessageBox, QDateEdit, QDoubleSpinBox, QTextEdit,
    QGridLayout, QScrollArea, QWidget, QSpinBox, QAbstractItemView,
    QFileDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap, QColor

from core.database import get_db_connection
from config import REPORT_OUTPUT_DIR


DURUM_RENKLER = {
    'TASLAK': '#6B7280',
    'GONDERILDI': '#3B82F6',
    'ONAYLANDI': '#10B981',
    'REDDEDILDI': '#EF4444',
    'IPTAL': '#9CA3AF',
    'IS_EMRINE_DONUSTURULDU': '#8B5CF6',
}

DURUM_METINLER = {
    'TASLAK': 'Taslak',
    'GONDERILDI': 'Gönderildi',
    'ONAYLANDI': 'Onaylandı',
    'REDDEDILDI': 'Reddedildi',
    'IPTAL': 'İptal',
    'IS_EMRINE_DONUSTURULDU': 'İş Emrine Dönüştürüldü',
}

KAPLAMA_TIPLERI = [
    "", "Çinko", "Nikel", "Krom", "Kataforez", "Fosfat",
    "Bakır", "Kalay", "Altın", "Gümüş", "Anodize",
    "Pasivizasyon", "Siyah Oksit",
]

BIRIMLER = ["ADET", "KG", "M2", "DM2", "LT", "MT"]

PARA_BIRIMLERI = [("TRY", "₺ TRY"), ("EUR", "€ EUR"), ("USD", "$ USD")]


class TeklifDetayDialog(QDialog):
    def __init__(self, teklif_id=None, sablon_id=None, theme=None, parent=None):
        super().__init__(parent)

        self.teklif_id = None
        if teklif_id is not None:
            try:
                self.teklif_id = int(teklif_id)
            except:
                self.teklif_id = None

        self.sablon_id = sablon_id
        self.yeni_kayit = self.teklif_id is None
        self.theme = theme or {}
        self.teklif_data = {}
        self.teklif_satirlari = []
        self.kaplama_sartnamesi_path = None
        self.parca_gorseli_path = None
        self.satir_gorselleri = {}  # {row_index: dosya_yolu}

        t = self.theme
        self.bg_card = t.get('bg_card', '#1E1E1E')
        self.bg_input = t.get('bg_input', '#1A1A1A')
        self.text_color = t.get('text', '#FFFFFF')
        self.text_muted = t.get('text_muted', '#666666')
        self.border = t.get('border', '#2A2A2A')
        self.primary = t.get('primary', '#DC2626')
        self.success = t.get('success', '#10B981')
        self.info = t.get('info', '#3B82F6')
        self.warning = t.get('warning', '#F59E0B')
        self.error = t.get('error', '#EF4444')

        self.setWindowTitle("Yeni Teklif" if self.yeni_kayit else "Teklif Detay")
        self.setMinimumSize(1100, 800)
        self.resize(1200, 850)

        if not self.yeni_kayit:
            self._load_data()

        self._setup_ui()
        self._load_combo_data()

        if not self.yeni_kayit:
            self._fill_form()
        elif self.sablon_id:
            self._fill_from_sablon()

    def _setup_ui(self):
        t = self.theme
        self.setStyleSheet(f"""
            QDialog {{ background-color: {self.bg_card}; }}
            QLabel {{ color: {self.text_color}; font-size: 13px; }}
            QGroupBox {{
                color: {self.text_color}; font-weight: bold; font-size: 14px;
                border: 1px solid {self.border}; border-radius: 8px;
                margin-top: 12px; padding-top: 12px;
                background: {self.bg_card};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 16px; padding: 0 8px;
                background: {self.bg_card}; color: {self.text_color};
            }}
            QScrollBar:vertical {{
                background: {self.bg_input}; width: 10px; border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.border}; border-radius: 5px; min-height: 20px;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(12)

        content_layout.addWidget(self._create_header())
        content_layout.addWidget(self._create_musteri_group())
        content_layout.addWidget(self._create_kalemler_group())
        content_layout.addWidget(self._create_dosyalar_group())
        content_layout.addWidget(self._create_dahili_group())
        content_layout.addWidget(self._create_notlar_group())

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        main_layout.addWidget(self._create_footer())

    # ── HEADER ──
    def _create_header(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.bg_card}; border-radius: 8px; padding: 16px; }}")

        layout = QHBoxLayout(frame)

        if self.yeni_kayit:
            title_text = "➕ Yeni Teklif"
        else:
            teklif_no = self.teklif_data.get('teklif_no', '')
            rev = self.teklif_data.get('revizyon_no', 0)
            title_text = f"📝 {teklif_no} - Rev.{rev:02d}"

        title = QLabel(title_text)
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.text_color};")
        layout.addWidget(title)

        layout.addStretch()

        if not self.yeni_kayit:
            durum = self.teklif_data.get('durum', 'TASLAK')
            color = DURUM_RENKLER.get(durum, '#888')
            metin = DURUM_METINLER.get(durum, durum)
            badge = QLabel(f"  {metin}  ")
            badge.setStyleSheet(f"""
                background: {color}; color: white; padding: 8px 20px;
                border-radius: 14px; font-weight: bold; font-size: 13px;
            """)
            layout.addWidget(badge)

        return frame

    # ── MÜŞTERİ BİLGİLERİ ──
    def _create_musteri_group(self) -> QGroupBox:
        group = QGroupBox("👤 Müşteri ve Teklif Bilgileri")
        layout = QGridLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 28, 20, 20)

        input_style = f"""
            background: {self.bg_input}; border: 1px solid {self.border};
            border-radius: 6px; padding: 8px 12px; color: {self.text_color}; font-size: 13px;
        """
        label_style = f"color: {self.text_color}; font-weight: bold; font-size: 12px;"

        row = 0
        # Cari
        lbl = QLabel("Müşteri:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, row, 0)
        self.cari_combo = QComboBox()
        self.cari_combo.addItem("-- Müşteri Seçin --", "")
        self.cari_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.cari_combo.setEditable(True)
        self.cari_combo.currentIndexChanged.connect(self._on_cari_changed)
        layout.addWidget(self.cari_combo, row, 1, 1, 3)

        row += 1
        # Yetkili + Telefon
        lbl = QLabel("Yetkili:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, row, 0)
        self.yetkili_input = QLineEdit()
        self.yetkili_input.setPlaceholderText("İlgili kişi")
        self.yetkili_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        layout.addWidget(self.yetkili_input, row, 1)

        lbl = QLabel("Telefon:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, row, 2)
        self.telefon_input = QLineEdit()
        self.telefon_input.setPlaceholderText("0xxx xxx xx xx")
        self.telefon_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        layout.addWidget(self.telefon_input, row, 3)

        row += 1
        # Email + Referans
        lbl = QLabel("E-posta:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, row, 0)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@firma.com")
        self.email_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        layout.addWidget(self.email_input, row, 1)

        lbl = QLabel("Referans No:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, row, 2)
        self.referans_input = QLineEdit()
        self.referans_input.setPlaceholderText("Müşteri referans no")
        self.referans_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        layout.addWidget(self.referans_input, row, 3)

        row += 1
        # Proje + Teslim
        lbl = QLabel("Proje Adı:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, row, 0)
        self.proje_input = QLineEdit()
        self.proje_input.setPlaceholderText("Proje/iş adı")
        self.proje_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        layout.addWidget(self.proje_input, row, 1)

        lbl = QLabel("Teslim Süresi:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, row, 2)
        self.teslim_input = QLineEdit()
        self.teslim_input.setPlaceholderText("ör: 5-7 iş günü")
        self.teslim_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        layout.addWidget(self.teslim_input, row, 3)

        row += 1
        # Ödeme + Geçerlilik + Para Birimi
        lbl = QLabel("Ödeme Koşulları:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, row, 0)
        self.odeme_input = QLineEdit()
        self.odeme_input.setPlaceholderText("ör: 30 gün vadeli")
        self.odeme_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        layout.addWidget(self.odeme_input, row, 1)

        lbl = QLabel("Geçerlilik:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, row, 2)
        self.gecerlilik_input = QDateEdit()
        self.gecerlilik_input.setDate(QDate.currentDate().addDays(30))
        self.gecerlilik_input.setCalendarPopup(True)
        self.gecerlilik_input.setStyleSheet(f"QDateEdit {{ {input_style} }}")
        layout.addWidget(self.gecerlilik_input, row, 3)

        row += 1
        lbl = QLabel("Para Birimi:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, row, 0)
        self.para_combo = QComboBox()
        for kod, etiket in PARA_BIRIMLERI:
            self.para_combo.addItem(etiket, kod)
        self.para_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        layout.addWidget(self.para_combo, row, 1)

        return group

    # ── TEKLİF KALEMLERİ ──
    def _create_kalemler_group(self) -> QGroupBox:
        group = QGroupBox("📦 Teklif Kalemleri")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 28, 20, 20)
        layout.setSpacing(12)

        # Butonlar
        btn_row = QHBoxLayout()
        btn_style = f"""
            QPushButton {{ background: {self.bg_input}; color: {self.text_color};
                border: 1px solid {self.border}; border-radius: 6px;
                padding: 8px 16px; font-size: 12px; font-weight: 600; }}
            QPushButton:hover {{ background: {self.border}; }}
        """
        add_btn = QPushButton("➕ Satır Ekle")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(btn_style)
        add_btn.clicked.connect(self._add_row)
        btn_row.addWidget(add_btn)

        del_btn = QPushButton("🗑️ Satır Sil")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(btn_style)
        del_btn.clicked.connect(self._delete_row)
        btn_row.addWidget(del_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Tablo
        self.kalem_table = QTableWidget()
        self.kalem_table.setColumnCount(14)
        self.kalem_table.setHorizontalHeaderLabels([
            "#", "Stok Kodu", "Ürün Adı", "Kaplama Tipi", "Kalınlık(µm)",
            "Malzeme", "Yüzey Alanı", "Birim", "Miktar", "Birim Fiyat",
            "Y.Adet", "Y.Ciro", "Açıklama", "Görsel"
        ])
        self.kalem_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.bg_input}; border: 1px solid {self.border};
                border-radius: 6px; color: {self.text_color}; gridline-color: {self.border}; font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px; color: {self.text_color};
                background-color: {self.bg_input};
            }}
            QTableWidget::item:alternate {{
                background-color: {self.bg_card};
            }}
            QTableWidget::item:selected {{
                background-color: #2A3A5C; color: {self.text_color};
            }}
            QComboBox {{
                background: {self.bg_input}; color: {self.text_color};
                border: 1px solid {self.border}; border-radius: 4px;
                padding: 4px 8px; font-size: 12px; min-height: 24px;
            }}
            QComboBox::drop-down {{
                border: none; width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background: {self.bg_card}; color: {self.text_color};
                border: 1px solid {self.border}; selection-background-color: #2A3A5C;
            }}
            QLineEdit {{
                background: {self.bg_input}; color: {self.text_color};
                border: 1px solid {self.border}; border-radius: 4px;
                padding: 4px 8px; font-size: 12px;
                selection-background-color: #2A3A5C;
            }}
            QHeaderView::section {{
                background-color: {self.bg_card}; color: {self.text_color};
                padding: 8px; border: none; border-bottom: 2px solid {self.primary};
                font-weight: bold; font-size: 11px;
            }}
        """)

        header = self.kalem_table.horizontalHeader()
        self.kalem_table.setColumnWidth(0, 35)   # #
        self.kalem_table.setColumnWidth(1, 90)   # Stok Kodu
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Ürün Adı
        self.kalem_table.setColumnWidth(3, 100)  # Kaplama Tipi
        self.kalem_table.setColumnWidth(4, 80)   # Kalınlık
        self.kalem_table.setColumnWidth(5, 80)   # Malzeme
        self.kalem_table.setColumnWidth(6, 80)   # Yüzey Alanı
        self.kalem_table.setColumnWidth(7, 70)   # Birim
        self.kalem_table.setColumnWidth(8, 70)   # Miktar
        self.kalem_table.setColumnWidth(9, 90)   # Birim Fiyat
        self.kalem_table.setColumnWidth(10, 70)  # Y.Adet
        self.kalem_table.setColumnWidth(11, 90)  # Y.Ciro
        self.kalem_table.setColumnWidth(12, 150) # Açıklama
        self.kalem_table.setColumnWidth(13, 80)  # Görsel

        self.kalem_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.kalem_table.verticalHeader().setVisible(False)
        self.kalem_table.verticalHeader().setDefaultSectionSize(38)
        self.kalem_table.setAlternatingRowColors(True)
        self.kalem_table.setMinimumHeight(200)
        self.kalem_table.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self.kalem_table)

        # Toplam ciro etiketi
        ciro_row = QHBoxLayout()
        ciro_row.addStretch()
        ciro_lbl = QLabel("Toplam Yıllık Ciro:")
        ciro_lbl.setStyleSheet(f"color: {self.warning}; font-weight: bold; font-size: 13px;")
        ciro_row.addWidget(ciro_lbl)
        self.toplam_ciro_label = QLabel("0,00")
        self.toplam_ciro_label.setStyleSheet(f"color: {self.warning}; font-weight: bold; font-size: 14px;")
        ciro_row.addWidget(self.toplam_ciro_label)
        info_lbl = QLabel("(PDF'de görünmez)")
        info_lbl.setStyleSheet(f"color: {self.text_muted}; font-size: 11px;")
        ciro_row.addWidget(info_lbl)
        layout.addLayout(ciro_row)

        return group

    # ── DOSYALAR ──
    def _create_dosyalar_group(self) -> QGroupBox:
        group = QGroupBox("📎 Kaplama Şartnamesi ve Parça Görseli")
        layout = QGridLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 28, 20, 20)

        btn_style = f"""
            QPushButton {{ background: {self.bg_input}; color: {self.text_color};
                border: 1px solid {self.border}; border-radius: 6px;
                padding: 8px 16px; font-size: 12px; font-weight: 600; }}
            QPushButton:hover {{ background: {self.border}; }}
        """
        label_style = f"color: {self.text_color}; font-weight: bold; font-size: 12px;"

        # Kaplama Şartnamesi
        lbl = QLabel("Kaplama Şartnamesi:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, 0, 0)

        self.sartname_label = QLabel("Dosya seçilmedi")
        self.sartname_label.setStyleSheet(f"color: {self.text_muted}; font-size: 12px;")
        layout.addWidget(self.sartname_label, 0, 1)

        sartname_btn = QPushButton("📄 Dosya Seç")
        sartname_btn.setCursor(Qt.PointingHandCursor)
        sartname_btn.setStyleSheet(btn_style)
        sartname_btn.clicked.connect(self._select_sartname)
        layout.addWidget(sartname_btn, 0, 2)

        sartname_clear_btn = QPushButton("✕")
        sartname_clear_btn.setCursor(Qt.PointingHandCursor)
        sartname_clear_btn.setStyleSheet(btn_style)
        sartname_clear_btn.setFixedWidth(40)
        sartname_clear_btn.clicked.connect(self._clear_sartname)
        layout.addWidget(sartname_clear_btn, 0, 3)

        # Parça Görseli
        lbl = QLabel("Parça Görseli:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, 1, 0)

        self.gorsel_label = QLabel("Görsel seçilmedi")
        self.gorsel_label.setStyleSheet(f"color: {self.text_muted}; font-size: 12px;")
        layout.addWidget(self.gorsel_label, 1, 1)

        gorsel_btn = QPushButton("🖼️ Görsel Seç")
        gorsel_btn.setCursor(Qt.PointingHandCursor)
        gorsel_btn.setStyleSheet(btn_style)
        gorsel_btn.clicked.connect(self._select_gorsel)
        layout.addWidget(gorsel_btn, 1, 2)

        gorsel_clear_btn = QPushButton("✕")
        gorsel_clear_btn.setCursor(Qt.PointingHandCursor)
        gorsel_clear_btn.setStyleSheet(btn_style)
        gorsel_clear_btn.setFixedWidth(40)
        gorsel_clear_btn.clicked.connect(self._clear_gorsel)
        layout.addWidget(gorsel_clear_btn, 1, 3)

        # Görsel Önizleme
        self.gorsel_preview = QLabel()
        self.gorsel_preview.setFixedSize(200, 200)
        self.gorsel_preview.setStyleSheet(f"""
            background: {self.bg_input}; border: 1px dashed {self.border};
            border-radius: 8px;
        """)
        self.gorsel_preview.setAlignment(Qt.AlignCenter)
        self.gorsel_preview.setText("Önizleme")
        layout.addWidget(self.gorsel_preview, 2, 0, 1, 4, Qt.AlignCenter)

        return group

    def _select_sartname(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Kaplama Şartnamesi Seç", "",
            "Dökümanlar (*.pdf *.doc *.docx *.xls *.xlsx *.png *.jpg);;Tüm Dosyalar (*)"
        )
        if path:
            self.kaplama_sartnamesi_path = path
            self.sartname_label.setText(os.path.basename(path))
            self.sartname_label.setStyleSheet(f"color: {self.success}; font-size: 12px; font-weight: 600;")

    def _clear_sartname(self):
        self.kaplama_sartnamesi_path = None
        self.sartname_label.setText("Dosya seçilmedi")
        self.sartname_label.setStyleSheet(f"color: {self.text_muted}; font-size: 12px;")

    def _select_gorsel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Parça Görseli Seç", "",
            "Görseller (*.png *.jpg *.jpeg *.bmp);;Tüm Dosyalar (*)"
        )
        if path:
            self.parca_gorseli_path = path
            self.gorsel_label.setText(os.path.basename(path))
            self.gorsel_label.setStyleSheet(f"color: {self.success}; font-size: 12px; font-weight: 600;")
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.gorsel_preview.setPixmap(
                    pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

    def _clear_gorsel(self):
        self.parca_gorseli_path = None
        self.gorsel_label.setText("Görsel seçilmedi")
        self.gorsel_label.setStyleSheet(f"color: {self.text_muted}; font-size: 12px;")
        self.gorsel_preview.clear()
        self.gorsel_preview.setText("Önizleme")

    # ── DAHİLİ BİLGİLER (müşteri görmez) ──
    def _create_dahili_group(self) -> QGroupBox:
        group = QGroupBox("🔒 Dahili Bilgiler (PDF'de görünmez)")
        layout = QGridLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 28, 20, 20)

        input_style = f"""
            background: {self.bg_input}; border: 1px solid {self.border};
            border-radius: 6px; padding: 8px 12px; color: {self.text_color}; font-size: 13px;
        """
        label_style = f"color: {self.text_color}; font-weight: bold; font-size: 12px;"

        lbl = QLabel("Dahili Not:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, 0, 0, Qt.AlignTop)
        self.dahili_not_input = QTextEdit()
        self.dahili_not_input.setMaximumHeight(60)
        self.dahili_not_input.setPlaceholderText("Sadece iç kullanım için notlar...")
        self.dahili_not_input.setStyleSheet(f"QTextEdit {{ {input_style} }}")
        layout.addWidget(self.dahili_not_input, 0, 1, 1, 3)

        return group

    # ── NOTLAR ──
    def _create_notlar_group(self) -> QGroupBox:
        group = QGroupBox("📝 Notlar ve Özel Koşullar")
        layout = QGridLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 28, 20, 20)

        input_style = f"""
            background: {self.bg_input}; border: 1px solid {self.border};
            border-radius: 6px; padding: 8px 12px; color: {self.text_color}; font-size: 13px;
        """
        label_style = f"color: {self.text_color}; font-weight: bold; font-size: 12px;"

        lbl = QLabel("Notlar:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, 0, 0, Qt.AlignTop)
        self.notlar_input = QTextEdit()
        self.notlar_input.setMaximumHeight(80)
        self.notlar_input.setPlaceholderText("Genel notlar...")
        self.notlar_input.setStyleSheet(f"QTextEdit {{ {input_style} }}")
        layout.addWidget(self.notlar_input, 0, 1)

        lbl = QLabel("Özel Koşullar:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, 1, 0, Qt.AlignTop)
        self.ozel_kosullar_input = QTextEdit()
        self.ozel_kosullar_input.setMaximumHeight(80)
        self.ozel_kosullar_input.setPlaceholderText("Özel koşullar ve şartlar...")
        self.ozel_kosullar_input.setStyleSheet(f"QTextEdit {{ {input_style} }}")
        layout.addWidget(self.ozel_kosullar_input, 1, 1)

        return group

    # ── FOOTER ──
    def _create_footer(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.bg_card}; border-radius: 8px; padding: 12px; }}")

        layout = QHBoxLayout(frame)

        btn_style_secondary = f"""
            QPushButton {{ background: {self.bg_input}; color: {self.text_color};
                border: 1px solid {self.border}; border-radius: 6px;
                padding: 10px 20px; font-size: 13px; }}
            QPushButton:hover {{ background: {self.border}; }}
        """

        if not self.yeni_kayit:
            rev_btn = QPushButton("🔄 Revizyon Geçmişi")
            rev_btn.setCursor(Qt.PointingHandCursor)
            rev_btn.setStyleSheet(btn_style_secondary)
            rev_btn.clicked.connect(self._show_revision_history)
            layout.addWidget(rev_btn)

        pdf_btn = QPushButton("📄 PDF Çıktı")
        pdf_btn.setCursor(Qt.PointingHandCursor)
        pdf_btn.setStyleSheet(f"""
            QPushButton {{ background: {self.info}; color: white; border: none;
                border-radius: 6px; padding: 10px 20px; font-weight: 600; font-size: 13px; }}
            QPushButton:hover {{ background: #2563EB; }}
        """)
        pdf_btn.clicked.connect(self._export_pdf)
        layout.addWidget(pdf_btn)

        layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(btn_style_secondary)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{ background: {self.success}; color: white; border: none;
                border-radius: 6px; padding: 10px 28px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background: #059669; }}
        """)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

        send_btn = QPushButton("📤 Kaydet ve Gönder")
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{ background: {self.primary}; color: white; border: none;
                border-radius: 6px; padding: 10px 28px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background: #B91C1C; }}
        """)
        send_btn.clicked.connect(self._save_and_send)
        layout.addWidget(send_btn)

        return frame

    # ── COMBO DATA ──
    def _load_combo_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, unvan FROM musteri.cariler
                WHERE unvan IS NOT NULL AND unvan != ''
                ORDER BY unvan
            """)
            for row in cursor.fetchall():
                self.cari_combo.addItem(str(row[1]), int(row[0]))
            conn.close()
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _on_cari_changed(self):
        cari_id = self.cari_combo.currentData()
        if not cari_id:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 y.ad_soyad, y.telefon, y.email
                FROM musteri.cari_yetkililer y
                WHERE y.cari_id = ? AND y.aktif_mi = 1
                ORDER BY y.id
            """, (cari_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                if row[0] and not self.yetkili_input.text():
                    self.yetkili_input.setText(str(row[0] or ''))
                if row[1] and not self.telefon_input.text():
                    self.telefon_input.setText(str(row[1] or ''))
                if row[2] and not self.email_input.text():
                    self.email_input.setText(str(row[2] or ''))
        except:
            pass

    # ── SATIR İŞLEMLERİ ──
    def _add_row(self):
        self.kalem_table.blockSignals(True)
        row = self.kalem_table.rowCount()
        self.kalem_table.setRowCount(row + 1)

        # Satır no
        no_item = QTableWidgetItem(str(row + 1))
        no_item.setFlags(no_item.flags() & ~Qt.ItemIsEditable)
        no_item.setTextAlignment(Qt.AlignCenter)
        self.kalem_table.setItem(row, 0, no_item)

        # Stok Kodu
        self.kalem_table.setItem(row, 1, QTableWidgetItem(""))
        # Ürün Adı
        self.kalem_table.setItem(row, 2, QTableWidgetItem(""))

        # Kaplama Tipi (ComboBox)
        kaplama_combo = QComboBox()
        kaplama_combo.addItems(KAPLAMA_TIPLERI)
        kaplama_combo.setStyleSheet(f"background: {self.bg_input}; color: {self.text_color}; border: none; padding: 4px;")
        self.kalem_table.setCellWidget(row, 3, kaplama_combo)

        # Kalınlık
        self.kalem_table.setItem(row, 4, QTableWidgetItem(""))
        # Malzeme
        self.kalem_table.setItem(row, 5, QTableWidgetItem(""))
        # Yüzey Alanı
        self.kalem_table.setItem(row, 6, QTableWidgetItem(""))

        # Birim (ComboBox)
        birim_combo = QComboBox()
        birim_combo.addItems(BIRIMLER)
        birim_combo.setStyleSheet(f"background: {self.bg_input}; color: {self.text_color}; border: none; padding: 4px;")
        self.kalem_table.setCellWidget(row, 7, birim_combo)

        # Miktar
        self.kalem_table.setItem(row, 8, QTableWidgetItem("0"))
        # Birim Fiyat
        self.kalem_table.setItem(row, 9, QTableWidgetItem("0.00"))

        # Y.Adet
        self.kalem_table.setItem(row, 10, QTableWidgetItem("0"))

        # Y.Ciro (otomatik hesaplanır, read-only)
        ciro_item = QTableWidgetItem("0,00")
        ciro_item.setFlags(ciro_item.flags() & ~Qt.ItemIsEditable)
        ciro_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.kalem_table.setItem(row, 11, ciro_item)

        # Açıklama
        self.kalem_table.setItem(row, 12, QTableWidgetItem(""))

        # Görsel butonu
        gorsel_btn = QPushButton("Gorsel")
        gorsel_btn.setFixedSize(50, 26)
        gorsel_btn.setCursor(Qt.PointingHandCursor)
        gorsel_btn.setToolTip("Satır görseli seç")
        c = '#0EA5E9'
        gorsel_btn.setStyleSheet(f"QPushButton {{ background: {c}18; color: {c}; border: 1px solid {c}30; border-radius: 6px; font-size: 11px; }} QPushButton:hover {{ background: {c}35; border-color: {c}55; }} QPushButton:pressed {{ background: {c}50; }}")
        gorsel_btn.clicked.connect(lambda checked, r=row: self._select_satir_gorsel(r))
        self.kalem_table.setCellWidget(row, 13, gorsel_btn)

        self.kalem_table.blockSignals(False)

    def _on_cell_changed(self, row, col):
        """B.Fiyat(9) veya Y.Adet(10) değiştiğinde Y.Ciro(11) güncelle"""
        if col in (9, 10):
            self.kalem_table.blockSignals(True)
            try:
                fiyat_text = self.kalem_table.item(row, 9).text().replace(',', '.') if self.kalem_table.item(row, 9) else '0'
                adet_text = self.kalem_table.item(row, 10).text().replace(',', '.') if self.kalem_table.item(row, 10) else '0'
                birim_fiyat = float(fiyat_text) if fiyat_text else 0
                yillik_adet = float(adet_text) if adet_text else 0
                ciro = birim_fiyat * yillik_adet
                ciro_item = self.kalem_table.item(row, 11)
                if ciro_item:
                    ciro_item.setText(f"{ciro:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            except:
                pass
            self.kalem_table.blockSignals(False)
            self._update_toplam_ciro()

    def _update_toplam_ciro(self):
        """Tüm satırların Y.Ciro toplamını güncelle"""
        toplam = 0
        for row in range(self.kalem_table.rowCount()):
            try:
                ciro_text = self.kalem_table.item(row, 11).text().replace('.', '').replace(',', '.') if self.kalem_table.item(row, 11) else '0'
                toplam += float(ciro_text)
            except:
                pass
        self.toplam_ciro_label.setText(f"{toplam:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    def _select_satir_gorsel(self, row):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Satır {row + 1} Görseli Seç", "",
            "Görseller (*.png *.jpg *.jpeg *.bmp);;Tüm Dosyalar (*)"
        )
        if path:
            self.satir_gorselleri[row] = path
            btn = self.kalem_table.cellWidget(row, 13)
            if btn:
                btn.setText("✅")
                btn.setToolTip(os.path.basename(path))

    def _delete_row(self):
        current = self.kalem_table.currentRow()
        if current >= 0:
            # Görsel referansını kaldır ve yeniden numaralandır
            if current in self.satir_gorselleri:
                del self.satir_gorselleri[current]
            self.kalem_table.removeRow(current)
            self._renumber_rows()
            self._renumber_satir_gorselleri()

    def _renumber_satir_gorselleri(self):
        """Satır silindikten sonra görsel indekslerini yeniden düzenle"""
        new_map = {}
        old_keys = sorted(self.satir_gorselleri.keys())
        for old_row in old_keys:
            # Silinmiş satırın üstündeki satırlar aynı kalır, altındakiler 1 azalır
            # Ama removeRow zaten çağrıldı, bu yüzden widget row'larına bakıyoruz
            pass
        # En güvenli yol: buton tooltip'lerinden yeniden oku
        new_map = {}
        for r in range(self.kalem_table.rowCount()):
            btn = self.kalem_table.cellWidget(r, 13)
            if btn and btn.text() == "✅":
                tip = btn.toolTip()
                # Eski map'ten dosya yolunu bul
                for old_r, old_path in self.satir_gorselleri.items():
                    if os.path.basename(old_path) == tip:
                        new_map[r] = old_path
                        break
        self.satir_gorselleri = new_map
        # Butonların lambda bağlantılarını güncelle
        for r in range(self.kalem_table.rowCount()):
            btn = self.kalem_table.cellWidget(r, 13)
            if btn:
                try:
                    btn.clicked.disconnect()
                except:
                    pass
                btn.clicked.connect(lambda checked, row=r: self._select_satir_gorsel(row))

    def _renumber_rows(self):
        self.kalem_table.blockSignals(True)
        for i in range(self.kalem_table.rowCount()):
            item = self.kalem_table.item(i, 0)
            if item:
                item.setText(str(i + 1))
        self.kalem_table.blockSignals(False)

    # ── VERİ YÜKLEME ──
    def _load_data(self):
        if self.teklif_id is None:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, teklif_no, revizyon_no, tarih, gecerlilik_tarihi,
                       cari_id, cari_unvani, cari_yetkili, cari_telefon, cari_email,
                       ara_toplam, iskonto_oran, iskonto_tutar, kdv_oran, kdv_tutar,
                       genel_toplam, para_birimi, durum, referans_no, proje_adi,
                       teslim_suresi, odeme_kosullari, notlar, ozel_kosullar,
                       ana_teklif_id
                FROM satislar.teklifler WHERE id = ?
            """, (self.teklif_id,))
            row = cursor.fetchone()
            if row:
                self.teklif_data = {
                    'id': row[0], 'teklif_no': str(row[1] or ''),
                    'revizyon_no': row[2] or 0, 'tarih': row[3],
                    'gecerlilik_tarihi': row[4],
                    'cari_id': row[5], 'cari_unvani': str(row[6] or ''),
                    'cari_yetkili': str(row[7] or ''), 'cari_telefon': str(row[8] or ''),
                    'cari_email': str(row[9] or ''),
                    'ara_toplam': float(row[10] or 0), 'iskonto_oran': float(row[11] or 0),
                    'iskonto_tutar': float(row[12] or 0), 'kdv_oran': float(row[13] or 20),
                    'kdv_tutar': float(row[14] or 0), 'genel_toplam': float(row[15] or 0),
                    'para_birimi': str(row[16] or 'TRY'), 'durum': str(row[17] or 'TASLAK'),
                    'referans_no': str(row[18] or ''), 'proje_adi': str(row[19] or ''),
                    'teslim_suresi': str(row[20] or ''), 'odeme_kosullari': str(row[21] or ''),
                    'notlar': str(row[22] or ''), 'ozel_kosullar': str(row[23] or ''),
                    'ana_teklif_id': row[24],
                }

            # Dosya yollarını yükle
            try:
                cursor.execute("""
                    SELECT kaplama_sartnamesi_dosya, parca_gorseli_dosya
                    FROM satislar.teklifler WHERE id = ?
                """, (self.teklif_id,))
                dosya_row = cursor.fetchone()
                if dosya_row:
                    self.teklif_data['kaplama_sartnamesi_dosya'] = str(dosya_row[0] or '')
                    self.teklif_data['parca_gorseli_dosya'] = str(dosya_row[1] or '')
                else:
                    self.teklif_data['kaplama_sartnamesi_dosya'] = ''
                    self.teklif_data['parca_gorseli_dosya'] = ''
            except:
                self.teklif_data['kaplama_sartnamesi_dosya'] = ''
                self.teklif_data['parca_gorseli_dosya'] = ''

            # Dahili notu yükle
            try:
                cursor.execute("""
                    SELECT dahili_not
                    FROM satislar.teklifler WHERE id = ?
                """, (self.teklif_id,))
                dahili_row = cursor.fetchone()
                if dahili_row:
                    self.teklif_data['dahili_not'] = str(dahili_row[0] or '')
                else:
                    self.teklif_data['dahili_not'] = ''
            except:
                self.teklif_data['dahili_not'] = ''

            # Satırları yükle
            try:
                cursor.execute("""
                    SELECT id, satir_no, stok_kodu, stok_adi, kaplama_tipi_adi,
                           kalinlik_mikron, malzeme_tipi, yuzey_alani, yuzey_birimi,
                           miktar, birim, birim_fiyat, iskonto_oran, tutar, aciklama, teknik_not,
                           gorsel_dosya, yillik_adet
                    FROM satislar.teklif_satirlari WHERE teklif_id = ? ORDER BY satir_no
                """, (self.teklif_id,))
                extra_cols = 2
            except:
                try:
                    cursor.execute("""
                        SELECT id, satir_no, stok_kodu, stok_adi, kaplama_tipi_adi,
                               kalinlik_mikron, malzeme_tipi, yuzey_alani, yuzey_birimi,
                               miktar, birim, birim_fiyat, iskonto_oran, tutar, aciklama, teknik_not,
                               gorsel_dosya
                        FROM satislar.teklif_satirlari WHERE teklif_id = ? ORDER BY satir_no
                    """, (self.teklif_id,))
                    extra_cols = 1
                except:
                    cursor.execute("""
                        SELECT id, satir_no, stok_kodu, stok_adi, kaplama_tipi_adi,
                               kalinlik_mikron, malzeme_tipi, yuzey_alani, yuzey_birimi,
                               miktar, birim, birim_fiyat, iskonto_oran, tutar, aciklama, teknik_not
                        FROM satislar.teklif_satirlari WHERE teklif_id = ? ORDER BY satir_no
                    """, (self.teklif_id,))
                    extra_cols = 0
            self.teklif_satirlari = []
            for srow in cursor.fetchall():
                satir_dict = {
                    'id': srow[0], 'satir_no': srow[1], 'stok_kodu': str(srow[2] or ''),
                    'stok_adi': str(srow[3] or ''), 'kaplama_tipi_adi': str(srow[4] or ''),
                    'kalinlik_mikron': srow[5], 'malzeme_tipi': str(srow[6] or ''),
                    'yuzey_alani': srow[7], 'yuzey_birimi': str(srow[8] or 'dm2'),
                    'miktar': float(srow[9] or 0), 'birim': str(srow[10] or 'ADET'),
                    'birim_fiyat': float(srow[11] or 0), 'iskonto_oran': float(srow[12] or 0),
                    'tutar': float(srow[13] or 0), 'aciklama': str(srow[14] or ''),
                    'teknik_not': str(srow[15] or ''),
                    'gorsel_dosya': str(srow[16] or '') if extra_cols >= 1 else '',
                    'yillik_adet': int(srow[17] or 0) if extra_cols >= 2 else 0,
                }
                self.teklif_satirlari.append(satir_dict)
            conn.close()
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _fill_form(self):
        if not self.teklif_data:
            return

        d = self.teklif_data

        # Cari
        cari_id = d.get('cari_id')
        if cari_id:
            for i in range(self.cari_combo.count()):
                if self.cari_combo.itemData(i) == cari_id:
                    self.cari_combo.setCurrentIndex(i)
                    break

        self.yetkili_input.setText(d.get('cari_yetkili', ''))
        self.telefon_input.setText(d.get('cari_telefon', ''))
        self.email_input.setText(d.get('cari_email', ''))
        self.referans_input.setText(d.get('referans_no', ''))
        self.proje_input.setText(d.get('proje_adi', ''))
        self.teslim_input.setText(d.get('teslim_suresi', ''))
        self.odeme_input.setText(d.get('odeme_kosullari', ''))

        gecerlilik = d.get('gecerlilik_tarihi')
        if gecerlilik:
            if hasattr(gecerlilik, 'year'):
                self.gecerlilik_input.setDate(QDate(gecerlilik.year, gecerlilik.month, gecerlilik.day))

        # Para birimi
        para = d.get('para_birimi', 'TRY')
        for i in range(self.para_combo.count()):
            if self.para_combo.itemData(i) == para:
                self.para_combo.setCurrentIndex(i)
                break

        self.notlar_input.setPlainText(d.get('notlar', ''))
        self.ozel_kosullar_input.setPlainText(d.get('ozel_kosullar', ''))

        # Dahili bilgiler
        self.dahili_not_input.setPlainText(d.get('dahili_not', ''))

        # Dosyalar
        sartname = d.get('kaplama_sartnamesi_dosya', '')
        if sartname and os.path.isfile(sartname):
            self.kaplama_sartnamesi_path = sartname
            self.sartname_label.setText(os.path.basename(sartname))
            self.sartname_label.setStyleSheet(f"color: {self.success}; font-size: 12px; font-weight: 600;")

        gorsel = d.get('parca_gorseli_dosya', '')
        if gorsel and os.path.isfile(gorsel):
            self.parca_gorseli_path = gorsel
            self.gorsel_label.setText(os.path.basename(gorsel))
            self.gorsel_label.setStyleSheet(f"color: {self.success}; font-size: 12px; font-weight: 600;")
            pixmap = QPixmap(gorsel)
            if not pixmap.isNull():
                self.gorsel_preview.setPixmap(
                    pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

        # Satırları doldur
        for satir in self.teklif_satirlari:
            self._add_row()
            row = self.kalem_table.rowCount() - 1
            self.kalem_table.blockSignals(True)

            self.kalem_table.item(row, 1).setText(satir.get('stok_kodu', ''))
            self.kalem_table.item(row, 2).setText(satir.get('stok_adi', ''))

            # Kaplama combo
            kaplama_combo = self.kalem_table.cellWidget(row, 3)
            if kaplama_combo:
                idx = kaplama_combo.findText(satir.get('kaplama_tipi_adi', ''))
                if idx >= 0:
                    kaplama_combo.setCurrentIndex(idx)

            kalinlik = satir.get('kalinlik_mikron')
            self.kalem_table.item(row, 4).setText(str(kalinlik) if kalinlik else '')
            self.kalem_table.item(row, 5).setText(satir.get('malzeme_tipi', ''))
            yuzey = satir.get('yuzey_alani')
            self.kalem_table.item(row, 6).setText(str(yuzey) if yuzey else '')

            # Birim combo
            birim_combo = self.kalem_table.cellWidget(row, 7)
            if birim_combo:
                idx = birim_combo.findText(satir.get('birim', 'ADET'))
                if idx >= 0:
                    birim_combo.setCurrentIndex(idx)

            self.kalem_table.item(row, 8).setText(str(satir.get('miktar', 0)))
            self.kalem_table.item(row, 9).setText(f"{satir.get('birim_fiyat', 0):.4f}")

            # Y.Adet
            yillik_adet = satir.get('yillik_adet', 0) or 0
            self.kalem_table.item(row, 10).setText(str(int(yillik_adet)) if yillik_adet else "0")

            # Y.Ciro otomatik
            birim_fiyat = float(satir.get('birim_fiyat', 0) or 0)
            ciro = float(yillik_adet) * birim_fiyat
            ciro_item = self.kalem_table.item(row, 11)
            if ciro_item:
                ciro_item.setText(f"{ciro:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            self.kalem_table.item(row, 12).setText(satir.get('aciklama', ''))

            # Satır görseli
            gorsel_path = satir.get('gorsel_dosya', '')
            if gorsel_path and os.path.isfile(gorsel_path):
                self.satir_gorselleri[row] = gorsel_path
                btn = self.kalem_table.cellWidget(row, 13)
                if btn:
                    btn.setText("✅")
                    btn.setToolTip(os.path.basename(gorsel_path))

            self.kalem_table.blockSignals(False)

        self._update_toplam_ciro()

    def _fill_from_sablon(self):
        """Şablondan doldur"""
        if not self.sablon_id:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT sablon_adi, varsayilan_kdv_oran, varsayilan_iskonto_oran,
                       varsayilan_para_birimi, varsayilan_teslim_suresi,
                       varsayilan_odeme_kosullari, varsayilan_gecerlilik_gun,
                       varsayilan_ozel_kosullar
                FROM satislar.teklif_sablonlari WHERE id = ?
            """, (self.sablon_id,))
            sablon = cursor.fetchone()
            if sablon:
                para = str(sablon[3] or 'TRY')
                for i in range(self.para_combo.count()):
                    if self.para_combo.itemData(i) == para:
                        self.para_combo.setCurrentIndex(i)
                        break

                if sablon[4]:
                    self.teslim_input.setText(str(sablon[4]))
                if sablon[5]:
                    self.odeme_input.setText(str(sablon[5]))
                gun = int(sablon[6] or 30)
                self.gecerlilik_input.setDate(QDate.currentDate().addDays(gun))
                if sablon[7]:
                    self.ozel_kosullar_input.setPlainText(str(sablon[7]))

            # Şablon satırları
            cursor.execute("""
                SELECT satir_no, kaplama_tipi_adi, kalinlik_mikron, malzeme_tipi,
                       birim, varsayilan_birim_fiyat, aciklama
                FROM satislar.teklif_sablon_satirlari WHERE sablon_id = ? ORDER BY satir_no
            """, (self.sablon_id,))
            for srow in cursor.fetchall():
                self._add_row()
                row = self.kalem_table.rowCount() - 1
                self.kalem_table.blockSignals(True)

                kaplama_combo = self.kalem_table.cellWidget(row, 3)
                if kaplama_combo:
                    idx = kaplama_combo.findText(str(srow[1] or ''))
                    if idx >= 0:
                        kaplama_combo.setCurrentIndex(idx)

                kalinlik = srow[2]
                self.kalem_table.item(row, 4).setText(str(kalinlik) if kalinlik else '')
                self.kalem_table.item(row, 5).setText(str(srow[3] or ''))

                birim_combo = self.kalem_table.cellWidget(row, 7)
                if birim_combo:
                    idx = birim_combo.findText(str(srow[4] or 'ADET'))
                    if idx >= 0:
                        birim_combo.setCurrentIndex(idx)

                fiyat = float(srow[5] or 0)
                self.kalem_table.item(row, 9).setText(f"{fiyat:.4f}")
                self.kalem_table.item(row, 12).setText(str(srow[6] or ''))

                self.kalem_table.blockSignals(False)

            conn.close()
        except Exception as e:
            import traceback
            traceback.print_exc()

    # ── KAYDETME ──
    def _save(self, durum_override=None):
        cari_id = self.cari_combo.currentData()
        cari_unvani = self.cari_combo.currentText()

        if not cari_id or cari_unvani.startswith("--"):
            QMessageBox.warning(self, "Uyarı", "Lütfen müşteri seçin!")
            return

        if self.kalem_table.rowCount() == 0:
            QMessageBox.warning(self, "Uyarı", "En az bir teklif kalemi ekleyin!")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Satırlardan veri topla
            satirlar = self._collect_rows()

            # Sadece birim fiyat veriliyor, toplam hesaplaması yok
            ara_toplam = sum(s['tutar'] for s in satirlar)
            iskonto_oran = 0
            iskonto_tutar = 0
            kdv_oran = 0
            kdv_tutar = 0
            genel_toplam = ara_toplam

            para_birimi = self.para_combo.currentData() or 'TRY'
            durum = durum_override or (self.teklif_data.get('durum', 'TASLAK') if not self.yeni_kayit else 'TASLAK')

            gecerlilik = self.gecerlilik_input.date().toString("yyyy-MM-dd")
            yetkili = self.yetkili_input.text().strip()
            telefon = self.telefon_input.text().strip()
            email = self.email_input.text().strip()
            referans = self.referans_input.text().strip()
            proje = self.proje_input.text().strip()
            teslim = self.teslim_input.text().strip()
            odeme = self.odeme_input.text().strip()
            notlar = self.notlar_input.toPlainText().strip()
            ozel = self.ozel_kosullar_input.toPlainText().strip()

            if self.yeni_kayit:
                # Yeni teklif no al
                cursor.execute("EXEC satislar.sp_yeni_teklif_no @teklif_no = NULL")
                # sp output parametresi kullanamayacağımız için manuel hesapla
                cursor.execute("""
                    DECLARE @no NVARCHAR(20);
                    EXEC satislar.sp_yeni_teklif_no @teklif_no = @no OUTPUT;
                    SELECT @no;
                """)
                result = cursor.fetchone()
                teklif_no = str(result[0]) if result else f"TEK-{datetime.now().strftime('%Y')}-0001"

                cursor.execute("""
                    INSERT INTO satislar.teklifler (
                        teklif_no, revizyon_no, tarih, gecerlilik_tarihi,
                        cari_id, cari_unvani, cari_yetkili, cari_telefon, cari_email,
                        ara_toplam, iskonto_oran, iskonto_tutar, kdv_oran, kdv_tutar,
                        genel_toplam, para_birimi, durum,
                        referans_no, proje_adi, teslim_suresi, odeme_kosullari,
                        notlar, ozel_kosullar, sablon_id
                    ) VALUES (?, 0, GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    teklif_no, gecerlilik,
                    cari_id, cari_unvani, yetkili, telefon, email,
                    ara_toplam, iskonto_oran, iskonto_tutar, kdv_oran, kdv_tutar,
                    genel_toplam, para_birimi, durum,
                    referans, proje, teslim, odeme, notlar, ozel, self.sablon_id
                ))

                cursor.execute("SELECT @@IDENTITY")
                self.teklif_id = int(cursor.fetchone()[0])
            else:
                teklif_no = self.teklif_data.get('teklif_no', '')
                cursor.execute("""
                    UPDATE satislar.teklifler SET
                        cari_id = ?, cari_unvani = ?, cari_yetkili = ?, cari_telefon = ?, cari_email = ?,
                        ara_toplam = ?, iskonto_oran = ?, iskonto_tutar = ?, kdv_oran = ?, kdv_tutar = ?,
                        genel_toplam = ?, para_birimi = ?, durum = ?, gecerlilik_tarihi = ?,
                        referans_no = ?, proje_adi = ?, teslim_suresi = ?, odeme_kosullari = ?,
                        notlar = ?, ozel_kosullar = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    cari_id, cari_unvani, yetkili, telefon, email,
                    ara_toplam, iskonto_oran, iskonto_tutar, kdv_oran, kdv_tutar,
                    genel_toplam, para_birimi, durum, gecerlilik,
                    referans, proje, teslim, odeme, notlar, ozel,
                    self.teklif_id
                ))

                # Eski satırları sil
                cursor.execute("DELETE FROM satislar.teklif_satirlari WHERE teklif_id = ?", (self.teklif_id,))

            # Dosya dizinini hazırla
            dosya_dir = os.path.join(str(REPORT_OUTPUT_DIR.parent), "teklif_dosyalar", str(self.teklif_id))
            os.makedirs(dosya_dir, exist_ok=True)

            # Satırları kaydet
            for idx, satir in enumerate(satirlar):
                # Satır görselini kopyala
                gorsel_db_path = None
                if idx in self.satir_gorselleri and os.path.isfile(self.satir_gorselleri[idx]):
                    src = self.satir_gorselleri[idx]
                    ext = os.path.splitext(src)[1]
                    dest = os.path.join(dosya_dir, f"satir_{idx + 1}_gorsel{ext}")
                    if os.path.abspath(src) != os.path.abspath(dest):
                        shutil.copy2(src, dest)
                    gorsel_db_path = dest

                try:
                    cursor.execute("""
                        INSERT INTO satislar.teklif_satirlari (
                            teklif_id, satir_no, stok_kodu, stok_adi,
                            kaplama_tipi_adi, kalinlik_mikron, malzeme_tipi,
                            yuzey_alani, birim, miktar, birim_fiyat,
                            iskonto_oran, tutar, aciklama, gorsel_dosya, yillik_adet
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.teklif_id, idx + 1, satir['stok_kodu'], satir['stok_adi'],
                        satir['kaplama_tipi'], satir['kalinlik'], satir['malzeme'],
                        satir['yuzey_alani'], satir['birim'], satir['miktar'],
                        satir['birim_fiyat'], satir['iskonto_oran'], satir['tutar'],
                        satir['aciklama'], gorsel_db_path, satir.get('yillik_adet') or None
                    ))
                except:
                    # gorsel_dosya/yillik_adet sütunları henüz yoksa
                    cursor.execute("""
                        INSERT INTO satislar.teklif_satirlari (
                            teklif_id, satir_no, stok_kodu, stok_adi,
                            kaplama_tipi_adi, kalinlik_mikron, malzeme_tipi,
                            yuzey_alani, birim, miktar, birim_fiyat,
                            iskonto_oran, tutar, aciklama
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.teklif_id, idx + 1, satir['stok_kodu'], satir['stok_adi'],
                        satir['kaplama_tipi'], satir['kalinlik'], satir['malzeme'],
                        satir['yuzey_alani'], satir['birim'], satir['miktar'],
                        satir['birim_fiyat'], satir['iskonto_oran'], satir['tutar'],
                        satir['aciklama']
                    ))

            # Teklif dosyalarını kaydet
            sartname_db = self.teklif_data.get('kaplama_sartnamesi_dosya', '') if not self.yeni_kayit else ''
            gorsel_db = self.teklif_data.get('parca_gorseli_dosya', '') if not self.yeni_kayit else ''

            if self.kaplama_sartnamesi_path and os.path.isfile(self.kaplama_sartnamesi_path):
                ext = os.path.splitext(self.kaplama_sartnamesi_path)[1]
                dest = os.path.join(dosya_dir, f"sartname{ext}")
                if os.path.abspath(self.kaplama_sartnamesi_path) != os.path.abspath(dest):
                    shutil.copy2(self.kaplama_sartnamesi_path, dest)
                sartname_db = dest

            if self.parca_gorseli_path and os.path.isfile(self.parca_gorseli_path):
                ext = os.path.splitext(self.parca_gorseli_path)[1]
                dest = os.path.join(dosya_dir, f"parca_gorseli{ext}")
                if os.path.abspath(self.parca_gorseli_path) != os.path.abspath(dest):
                    shutil.copy2(self.parca_gorseli_path, dest)
                gorsel_db = dest

            try:
                cursor.execute("""
                    UPDATE satislar.teklifler SET
                        kaplama_sartnamesi_dosya = ?, parca_gorseli_dosya = ?
                    WHERE id = ?
                """, (sartname_db or None, gorsel_db or None, self.teklif_id))
            except:
                pass  # Sütunlar henüz eklenmemişse

            # Dahili notu kaydet
            dahili_not = self.dahili_not_input.toPlainText().strip()
            try:
                cursor.execute("""
                    UPDATE satislar.teklifler SET dahili_not = ?
                    WHERE id = ?
                """, (dahili_not or None, self.teklif_id))
            except:
                pass  # Sütun henüz eklenmemişse

            conn.commit()
            conn.close()

            durum_metin = "kaydedildi" if durum == 'TASLAK' else "kaydedildi ve gönderildi"
            QMessageBox.information(self, "Başarılı", f"Teklif {teklif_no} {durum_metin}.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası:\n{str(e)}")

    def _save_and_send(self):
        self._save(durum_override='GONDERILDI')

    def _collect_rows(self):
        satirlar = []
        for row in range(self.kalem_table.rowCount()):
            stok_kodu = self.kalem_table.item(row, 1).text().strip() if self.kalem_table.item(row, 1) else ''
            stok_adi = self.kalem_table.item(row, 2).text().strip() if self.kalem_table.item(row, 2) else ''

            kaplama_combo = self.kalem_table.cellWidget(row, 3)
            kaplama = kaplama_combo.currentText() if kaplama_combo else ''

            kalinlik_text = self.kalem_table.item(row, 4).text().strip() if self.kalem_table.item(row, 4) else ''
            malzeme = self.kalem_table.item(row, 5).text().strip() if self.kalem_table.item(row, 5) else ''
            yuzey_text = self.kalem_table.item(row, 6).text().strip() if self.kalem_table.item(row, 6) else ''

            birim_combo = self.kalem_table.cellWidget(row, 7)
            birim = birim_combo.currentText() if birim_combo else 'ADET'

            miktar_text = self.kalem_table.item(row, 8).text().replace(',', '.') if self.kalem_table.item(row, 8) else '0'
            fiyat_text = self.kalem_table.item(row, 9).text().replace(',', '.') if self.kalem_table.item(row, 9) else '0'
            yadet_text = self.kalem_table.item(row, 10).text().replace(',', '.') if self.kalem_table.item(row, 10) else '0'
            aciklama = self.kalem_table.item(row, 12).text().strip() if self.kalem_table.item(row, 12) else ''

            try:
                miktar = float(miktar_text) if miktar_text else 0
            except:
                miktar = 0
            try:
                birim_fiyat = float(fiyat_text) if fiyat_text else 0
            except:
                birim_fiyat = 0
            try:
                kalinlik = float(kalinlik_text) if kalinlik_text else None
            except:
                kalinlik = None
            try:
                yuzey_alani = float(yuzey_text) if yuzey_text else None
            except:
                yuzey_alani = None

            try:
                yillik_adet = int(float(yadet_text)) if yadet_text else 0
            except:
                yillik_adet = 0

            tutar = miktar * birim_fiyat

            satirlar.append({
                'stok_kodu': stok_kodu, 'stok_adi': stok_adi,
                'kaplama_tipi': kaplama, 'kalinlik': kalinlik,
                'malzeme': malzeme, 'yuzey_alani': yuzey_alani,
                'birim': birim, 'miktar': miktar,
                'birim_fiyat': birim_fiyat, 'iskonto_oran': 0,
                'tutar': tutar, 'aciklama': aciklama,
                'yillik_adet': yillik_adet,
            })
        return satirlar

    # ── PDF ──
    def _export_pdf(self):
        if self.yeni_kayit or not self.teklif_id:
            QMessageBox.warning(self, "Uyarı", "Önce teklifi kaydedin.")
            return
        try:
            from utils.teklif_pdf import teklif_pdf_olustur
            teklif_pdf_olustur(self.teklif_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturma hatası: {e}")

    # ── REVİZYON GEÇMİŞİ ──
    def _show_revision_history(self):
        if not self.teklif_data:
            return

        teklif_no = self.teklif_data.get('teklif_no', '')
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, revizyon_no, tarih, durum, genel_toplam, para_birimi
                FROM satislar.teklifler
                WHERE teklif_no = ? AND silindi_mi = 0
                ORDER BY revizyon_no
            """, (teklif_no,))

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                QMessageBox.information(self, "Revizyon Geçmişi", "Revizyon bulunamadı.")
                return

            # Basit dialog
            dlg = QDialog(self)
            dlg.setWindowTitle(f"Revizyon Geçmişi - {teklif_no}")
            dlg.setMinimumSize(600, 300)
            dlg.setStyleSheet(f"QDialog {{ background: {self.bg_card}; }}")

            layout = QVBoxLayout(dlg)
            layout.setContentsMargins(20, 20, 20, 20)

            title = QLabel(f"📋 {teklif_no} - Revizyon Geçmişi")
            title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.text_color};")
            layout.addWidget(title)

            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Rev", "Tarih", "Durum", "Genel Toplam", ""])
            table.setStyleSheet(f"""
                QTableWidget {{ background: {self.bg_input}; color: {self.text_color};
                    border: 1px solid {self.border}; border-radius: 6px; }}
                QTableWidget::item {{ padding: 8px; }}
                QHeaderView::section {{ background: {self.bg_card}; color: {self.text_color};
                    padding: 8px; border: none; font-weight: bold; }}
            """)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
            table.verticalHeader().setVisible(False)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setRowCount(len(rows))

            for i, r in enumerate(rows):
                rev = r[1] or 0
                table.setItem(i, 0, QTableWidgetItem(f"Rev.{rev:02d}"))

                tarih = r[2]
                table.setItem(i, 1, QTableWidgetItem(str(tarih)[:10] if tarih else '-'))

                durum = str(r[3] or 'TASLAK')
                durum_item = QTableWidgetItem(DURUM_METINLER.get(durum, durum))
                durum_item.setForeground(QColor(DURUM_RENKLER.get(durum, '#888')))
                table.setItem(i, 2, durum_item)

                toplam = float(r[4] or 0)
                para = str(r[5] or 'TRY')
                simge = '₺' if para == 'TRY' else ('€' if para == 'EUR' else '$')
                toplam_item = QTableWidgetItem(f"{simge}{toplam:,.2f}")
                toplam_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(i, 3, toplam_item)

                aktif = " ◄" if r[0] == self.teklif_id else ""
                table.setItem(i, 4, QTableWidgetItem(aktif))

            layout.addWidget(table)

            close_btn = QPushButton("Kapat")
            close_btn.setCursor(Qt.PointingHandCursor)
            close_btn.setStyleSheet(f"""
                QPushButton {{ background: {self.bg_input}; color: {self.text_color};
                    border: 1px solid {self.border}; border-radius: 6px; padding: 10px 24px; }}
            """)
            close_btn.clicked.connect(dlg.accept)
            btn_row = QHBoxLayout()
            btn_row.addStretch()
            btn_row.addWidget(close_btn)
            layout.addLayout(btn_row)

            dlg.exec()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Revizyon geçmişi hatası: {e}")
