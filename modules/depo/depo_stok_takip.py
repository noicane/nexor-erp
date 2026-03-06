# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Stok Takip Sayfasi
Urun bazinda lot detayli stok sorgulama
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QSplitter, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection


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


class DepoStokTakipPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.secili_urun_id = None
        self.secili_depo_id = None
        self.lot_data = []
        self._setup_ui()

    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # === HEADER ===
        header = QHBoxLayout()
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        title_row = QHBoxLayout()
        icon = QLabel("\U0001F4E6")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Stok Takip")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Referans numarasi ile urun stok sorgulama")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()
        layout.addLayout(header)

        # === ARAMA ALANI ===
        search_frame = QFrame()
        search_frame.setStyleSheet(
            f"QFrame {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }}"
        )
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(16, 12, 16, 12)
        search_layout.setSpacing(12)

        search_label = QLabel("\U0001F50D")
        search_label.setStyleSheet("font-size: 18px;")
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Referans no / stok kodu / stok adi giriniz...")
        self.search_input.setStyleSheet(
            f"QLineEdit {{ background: {s['input_bg']}; border: 1px solid {s['border']}; "
            f"border-radius: 8px; padding: 10px 14px; color: {s['text']}; font-size: 14px; }}"
        )
        self.search_input.returnPressed.connect(self._ara)
        search_layout.addWidget(self.search_input, 1)

        ara_btn = QPushButton("\U0001F50D Ara")
        ara_btn.setCursor(Qt.PointingHandCursor)
        ara_btn.setStyleSheet(
            f"QPushButton {{ background: {s['primary']}; border: none; border-radius: 8px; "
            f"padding: 10px 24px; color: white; font-weight: 600; font-size: 13px; }} "
            f"QPushButton:hover {{ background: #B91C1C; }}"
        )
        ara_btn.clicked.connect(self._ara)
        search_layout.addWidget(ara_btn)

        layout.addWidget(search_frame)

        # === OZET KARTLARI ===
        self.ozet_frame = QFrame()
        self.ozet_frame.setStyleSheet(
            f"QFrame {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }}"
        )
        self.ozet_frame.setVisible(False)
        ozet_layout = QHBoxLayout(self.ozet_frame)
        ozet_layout.setContentsMargins(16, 16, 16, 16)
        ozet_layout.setSpacing(16)

        self.kart_toplam = self._create_ozet_kart("\U0001F4E6", "Toplam Miktar", "0", s['primary'])
        ozet_layout.addWidget(self.kart_toplam)
        self.kart_kullanilabilir = self._create_ozet_kart("\u2705", "Kullanilabilir", "0", s['success'])
        ozet_layout.addWidget(self.kart_kullanilabilir)
        self.kart_lot = self._create_ozet_kart("\U0001F3F7\uFE0F", "Lot Sayisi", "0", s['warning'])
        ozet_layout.addWidget(self.kart_lot)
        self.kart_depo = self._create_ozet_kart("\U0001F3ED", "Depo Sayisi", "0", s['info'])
        ozet_layout.addWidget(self.kart_depo)

        layout.addWidget(self.ozet_frame)

        # === URUN BILGI SATIRI ===
        self.urun_info = QLabel("")
        self.urun_info.setStyleSheet(
            f"color: {s['text_secondary']}; font-size: 13px; padding: 4px 0;"
        )
        self.urun_info.setVisible(False)
        layout.addWidget(self.urun_info)

        # === SPLITTER: DEPO BAZLI + LOT DETAY ===
        splitter = QSplitter(Qt.Vertical)

        # -- Depo Bazli Ozet Tablosu --
        depo_widget = QFrame()
        depo_widget.setStyleSheet(
            f"QFrame {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; }}"
        )
        depo_layout = QVBoxLayout(depo_widget)
        depo_layout.setContentsMargins(16, 16, 16, 16)
        depo_layout.setSpacing(8)

        depo_header = QHBoxLayout()
        depo_title = QLabel("\U0001F3ED DEPO BAZLI OZET")
        depo_title.setStyleSheet(f"color: {s['primary']}; font-weight: bold; font-size: 14px;")
        depo_header.addWidget(depo_title)
        depo_header.addStretch()
        self.depo_filter_label = QLabel("")
        self.depo_filter_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 12px;")
        depo_header.addWidget(self.depo_filter_label)
        depo_layout.addLayout(depo_header)

        self.depo_table = QTableWidget()
        self.depo_table.setColumnCount(6)
        self.depo_table.setHorizontalHeaderLabels([
            "Depo Kodu", "Depo Adi", "Toplam Miktar", "Rezerve", "Kullanilabilir", "Lot Sayisi"
        ])
        self.depo_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.depo_table.setColumnWidth(0, 100)
        self.depo_table.setColumnWidth(2, 120)
        self.depo_table.setColumnWidth(3, 100)
        self.depo_table.setColumnWidth(4, 120)
        self.depo_table.setColumnWidth(5, 90)
        self.depo_table.verticalHeader().setVisible(False)
        self.depo_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.depo_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.depo_table.clicked.connect(self._depo_satir_secildi)
        depo_layout.addWidget(self.depo_table, 1)

        splitter.addWidget(depo_widget)

        # -- Lot Detay Tablosu --
        lot_widget = QFrame()
        lot_widget.setStyleSheet(
            f"QFrame {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; }}"
        )
        lot_layout = QVBoxLayout(lot_widget)
        lot_layout.setContentsMargins(16, 16, 16, 16)
        lot_layout.setSpacing(8)

        lot_header = QHBoxLayout()
        self.lot_title = QLabel("\U0001F3F7\uFE0F LOT DETAYLARI")
        self.lot_title.setStyleSheet(f"color: {s['primary']}; font-weight: bold; font-size: 14px;")
        lot_header.addWidget(self.lot_title)
        lot_header.addStretch()

        self.lot_filter_btn = QPushButton("Tum Lotlar")
        self.lot_filter_btn.setCursor(Qt.PointingHandCursor)
        self.lot_filter_btn.setStyleSheet(
            f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; "
            f"border-radius: 6px; padding: 6px 12px; color: {s['text_secondary']}; font-size: 12px; }} "
            f"QPushButton:hover {{ border-color: {s['primary']}; }}"
        )
        self.lot_filter_btn.clicked.connect(self._tum_lotlari_goster)
        lot_header.addWidget(self.lot_filter_btn)
        lot_layout.addLayout(lot_header)

        self.lot_table = QTableWidget()
        self.lot_table.setColumnCount(12)
        self.lot_table.setHorizontalHeaderLabels([
            "Lot No", "Parent Lot", "Depo Kodu", "Depo Adi", "Miktar", "Rezerve",
            "Kullanilabilir", "Kalite Durumu", "Giris Tarihi", "Musteri", "Kaplama Tipi", "Birim"
        ])
        self.lot_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Stretch)
        self.lot_table.setColumnWidth(0, 120)
        self.lot_table.setColumnWidth(1, 120)
        self.lot_table.setColumnWidth(2, 90)
        self.lot_table.setColumnWidth(3, 130)
        self.lot_table.setColumnWidth(4, 90)
        self.lot_table.setColumnWidth(5, 80)
        self.lot_table.setColumnWidth(6, 100)
        self.lot_table.setColumnWidth(7, 120)
        self.lot_table.setColumnWidth(8, 100)
        self.lot_table.setColumnWidth(10, 110)
        self.lot_table.setColumnWidth(11, 60)
        self.lot_table.verticalHeader().setVisible(False)
        self.lot_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        lot_layout.addWidget(self.lot_table, 1)

        splitter.addWidget(lot_widget)
        splitter.setSizes([250, 450])
        layout.addWidget(splitter, 1)

    def _create_ozet_kart(self, icon: str, baslik: str, deger: str, renk: str) -> QFrame:
        s = self.s
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background: {s['input_bg']}; border: 1px solid {renk}; border-radius: 10px; }}"
        )
        v_layout = QVBoxLayout(frame)
        v_layout.setContentsMargins(16, 12, 16, 12)
        v_layout.setSpacing(6)
        header = QLabel(f"{icon} {baslik}")
        header.setStyleSheet(f"color: {s['text_muted']}; font-size: 12px;")
        v_layout.addWidget(header)
        value = QLabel(deger)
        value.setObjectName("value")
        value.setStyleSheet(f"color: {renk}; font-size: 26px; font-weight: bold;")
        v_layout.addWidget(value)
        return frame

    # =========================================================================
    # ARAMA
    # =========================================================================

    def _ara(self):
        arama = self.search_input.text().strip()
        if not arama:
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            like_param = f"%{arama}%"
            cursor.execute(
                """
                SELECT
                    u.id, u.urun_kodu, u.urun_adi,
                    SUM(sb.miktar) as toplam,
                    SUM(ISNULL(sb.rezerve_miktar, 0)) as rezerve,
                    SUM(sb.miktar - ISNULL(sb.rezerve_miktar, 0)) as kullanilabilir,
                    COUNT(DISTINCT sb.lot_no) as lot_sayisi,
                    COUNT(DISTINCT sb.depo_id) as depo_sayisi
                FROM stok.stok_bakiye sb
                JOIN stok.urunler u ON sb.urun_id = u.id
                WHERE (u.urun_kodu LIKE ? OR u.urun_adi LIKE ? OR sb.stok_kodu LIKE ?)
                    AND sb.miktar > 0
                GROUP BY u.id, u.urun_kodu, u.urun_adi
                """,
                (like_param, like_param, like_param),
            )
            sonuclar = cursor.fetchall()
            conn.close()

            if not sonuclar:
                self.ozet_frame.setVisible(False)
                self.urun_info.setText("Sonuc bulunamadi.")
                self.urun_info.setVisible(True)
                self.depo_table.setRowCount(0)
                self.lot_table.setRowCount(0)
                self.secili_urun_id = None
                return

            # Tam eslesen varsa onu sec, yoksa ilk sonuc
            secilen = sonuclar[0]
            for s_row in sonuclar:
                if s_row[1] and s_row[1].upper() == arama.upper():
                    secilen = s_row
                    break

            self.secili_urun_id = secilen[0]
            self.secili_depo_id = None

            # Ozet kartlarini guncelle
            self.kart_toplam.findChild(QLabel, "value").setText(f"{secilen[3]:,.0f}")
            self.kart_kullanilabilir.findChild(QLabel, "value").setText(f"{secilen[5]:,.0f}")
            self.kart_lot.findChild(QLabel, "value").setText(str(secilen[6]))
            self.kart_depo.findChild(QLabel, "value").setText(str(secilen[7]))
            self.ozet_frame.setVisible(True)

            # Urun bilgisi
            self.urun_info.setText(f"Urun: {secilen[1]} - {secilen[2]}")
            self.urun_info.setVisible(True)

            # Tablolari yukle
            self._load_depo_ozet(secilen[0])
            self._load_lot_detay(secilen[0])

        except Exception as e:
            print(f"Stok takip arama hatasi: {e}")

    # =========================================================================
    # DEPO BAZLI OZET
    # =========================================================================

    def _load_depo_ozet(self, urun_id: int):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    d.kod, d.ad,
                    SUM(sb.miktar) as toplam_miktar,
                    SUM(ISNULL(sb.rezerve_miktar, 0)) as rezerve,
                    SUM(sb.miktar - ISNULL(sb.rezerve_miktar, 0)) as kullanilabilir,
                    COUNT(DISTINCT sb.lot_no) as lot_sayisi
                FROM stok.stok_bakiye sb
                LEFT JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE sb.urun_id = ? AND sb.miktar > 0
                GROUP BY d.kod, d.ad
                ORDER BY toplam_miktar DESC
                """,
                (urun_id,),
            )
            rows = cursor.fetchall()
            conn.close()
            self._display_depo_table(rows)
        except Exception as e:
            print(f"Depo ozet hatasi: {e}")

    def _display_depo_table(self, rows):
        s = self.s
        self.depo_table.setRowCount(0)
        for row in rows:
            idx = self.depo_table.rowCount()
            self.depo_table.insertRow(idx)

            # Depo Kodu
            item = QTableWidgetItem(row[0] or "-")
            item.setForeground(QColor(s['primary']))
            item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.depo_table.setItem(idx, 0, item)

            # Depo Adi
            self.depo_table.setItem(idx, 1, QTableWidgetItem(row[1] or "-"))

            # Toplam Miktar
            item = QTableWidgetItem(f"{row[2]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setForeground(QColor(s['text']))
            self.depo_table.setItem(idx, 2, item)

            # Rezerve
            item = QTableWidgetItem(f"{row[3]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if row[3] > 0:
                item.setForeground(QColor(s['warning']))
            self.depo_table.setItem(idx, 3, item)

            # Kullanilabilir
            item = QTableWidgetItem(f"{row[4]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setForeground(QColor(s['success']))
            self.depo_table.setItem(idx, 4, item)

            # Lot Sayisi
            item = QTableWidgetItem(str(row[5]))
            item.setTextAlignment(Qt.AlignCenter)
            self.depo_table.setItem(idx, 5, item)

    # =========================================================================
    # LOT DETAYLARI
    # =========================================================================

    def _load_lot_detay(self, urun_id: int):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    sb.lot_no, sb.parent_lot_no, d.kod, d.ad,
                    sb.miktar, ISNULL(sb.rezerve_miktar, 0),
                    sb.miktar - ISNULL(sb.rezerve_miktar, 0),
                    ISNULL(sb.kalite_durumu_v2, sb.kalite_durumu),
                    ISNULL(sb.bloke_mi, 0),
                    sb.giris_tarihi, sb.cari_unvani, sb.kaplama_tipi,
                    ISNULL(sb.birim, 'ADET'), sb.palet_no, sb.toplam_palet
                FROM stok.stok_bakiye sb
                LEFT JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE sb.urun_id = ? AND sb.miktar > 0
                ORDER BY d.kod, sb.lot_no
                """,
                (urun_id,),
            )
            rows = cursor.fetchall()
            conn.close()
            self.lot_data = rows
            self._display_lot_table(rows)
            self.lot_title.setText("\U0001F3F7\uFE0F LOT DETAYLARI")
            self.depo_filter_label.setText("")
        except Exception as e:
            print(f"Lot detay hatasi: {e}")

    def _display_lot_table(self, rows):
        s = self.s
        self.lot_table.setRowCount(0)
        for row in rows:
            idx = self.lot_table.rowCount()
            self.lot_table.insertRow(idx)

            bloke = bool(row[8])
            kalite = row[7] or ""

            # Lot No
            item = QTableWidgetItem(row[0] or "-")
            item.setForeground(QColor(s['primary']))
            if bloke:
                font = QFont("Segoe UI", 10)
                font.setStrikeOut(True)
                item.setFont(font)
                item.setForeground(QColor(s['text_muted']))
            self.lot_table.setItem(idx, 0, item)

            # Parent Lot
            item = QTableWidgetItem(row[1] or "-")
            if bloke:
                item.setForeground(QColor(s['text_muted']))
            self.lot_table.setItem(idx, 1, item)

            # Depo Kodu
            item = QTableWidgetItem(row[2] or "-")
            if bloke:
                item.setForeground(QColor(s['text_muted']))
            self.lot_table.setItem(idx, 2, item)

            # Depo Adi
            item = QTableWidgetItem(row[3] or "-")
            if bloke:
                item.setForeground(QColor(s['text_muted']))
            self.lot_table.setItem(idx, 3, item)

            # Miktar
            item = QTableWidgetItem(f"{row[4]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if bloke:
                item.setForeground(QColor(s['text_muted']))
            self.lot_table.setItem(idx, 4, item)

            # Rezerve
            item = QTableWidgetItem(f"{row[5]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if row[5] > 0:
                item.setForeground(QColor(s['warning']))
            if bloke:
                item.setForeground(QColor(s['text_muted']))
            self.lot_table.setItem(idx, 5, item)

            # Kullanilabilir
            item = QTableWidgetItem(f"{row[6]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setForeground(QColor(s['success']))
            if bloke:
                item.setForeground(QColor(s['text_muted']))
            self.lot_table.setItem(idx, 6, item)

            # Kalite Durumu
            item = QTableWidgetItem(kalite)
            if bloke:
                item.setText(f"{kalite} [BLOKE]")
                item.setForeground(QColor(s['text_muted']))
            elif "ONAY" in kalite.upper():
                item.setForeground(QColor(s['success']))
            elif "BEKL" in kalite.upper():
                item.setForeground(QColor(s['warning']))
            elif "RED" in kalite.upper():
                item.setForeground(QColor(s['error']))
            self.lot_table.setItem(idx, 7, item)

            # Giris Tarihi
            tarih = row[9]
            tarih_str = tarih.strftime("%d.%m.%Y") if tarih else "-"
            item = QTableWidgetItem(tarih_str)
            if bloke:
                item.setForeground(QColor(s['text_muted']))
            self.lot_table.setItem(idx, 8, item)

            # Musteri
            item = QTableWidgetItem(row[10] or "-")
            if bloke:
                item.setForeground(QColor(s['text_muted']))
            self.lot_table.setItem(idx, 9, item)

            # Kaplama Tipi
            item = QTableWidgetItem(row[11] or "-")
            if bloke:
                item.setForeground(QColor(s['text_muted']))
            self.lot_table.setItem(idx, 10, item)

            # Birim
            item = QTableWidgetItem(row[12] or "ADET")
            if bloke:
                item.setForeground(QColor(s['text_muted']))
            self.lot_table.setItem(idx, 11, item)

    # =========================================================================
    # DEPO FILTRESI
    # =========================================================================

    def _depo_satir_secildi(self, index):
        row = index.row()
        depo_kodu = self.depo_table.item(row, 0).text()
        if depo_kodu == "-":
            return

        # Lot tablosunu secilen depoya filtrele
        filtered = [r for r in self.lot_data if (r[2] or "-") == depo_kodu]
        self._display_lot_table(filtered)
        self.lot_title.setText(f"\U0001F3F7\uFE0F LOT DETAYLARI - {depo_kodu}")
        self.depo_filter_label.setText(f"Filtre: {depo_kodu}")
        self.secili_depo_id = depo_kodu

    def _tum_lotlari_goster(self):
        if self.lot_data:
            self._display_lot_table(self.lot_data)
            self.lot_title.setText("\U0001F3F7\uFE0F LOT DETAYLARI")
            self.depo_filter_label.setText("")
            self.secili_depo_id = None
            self.depo_table.clearSelection()
