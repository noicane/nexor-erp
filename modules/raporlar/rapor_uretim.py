# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Uretim Raporu
Uretilen urunler, m2, adet bilgileri - gunluk/haftalik/aylik/tarih arasi
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QComboBox, QDateEdit,
    QWidget, QGraphicsDropShadowEffect, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


def get_modern_style(theme: dict) -> dict:
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
        'danger': brand.ERROR,
        'error': brand.ERROR,
        'info': brand.INFO,
        'bg_main': brand.BG_MAIN,
        'bg_hover': brand.BG_HOVER,
        'border_light': brand.BORDER_HARD,
    }


class RaporUretimPage(BasePage):
    """Uretim Raporu - Urun bazli m2/adet ozet ve detay"""

    # Tiklanabilir filtre kolonlari: (tablo_adi, kolon_idx, kolon_adi)
    FILTER_COLS_OZET = {2: "Musteri", 3: "Hat"}
    FILTER_COLS_DETAY = {4: "Musteri", 5: "Hat"}

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._active_filter = None   # (kolon_adi, deger)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ===== HEADER =====
        header = QHBoxLayout()
        title_section = QVBoxLayout()
        title_section.setSpacing(4)

        title_row = QHBoxLayout()
        icon = QLabel("📈")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Uretim Raporu")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)

        subtitle = QLabel("Uretilen urunler, m2, adet ve fire bilgileri")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()

        # Summary stat cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        self.toplam_adet_card = self._create_stat_card("Toplam Adet", "0", s['info'])
        self.toplam_m2_card = self._create_stat_card("Toplam m2", "0", s['success'])
        self.toplam_fire_card = self._create_stat_card("Fire Adet", "0", s['error'])
        self.toplam_red_card = self._create_stat_card("Red Adet", "0", s['warning'])
        self.urun_cesit_card = self._create_stat_card("Urun Cesidi", "0", s['primary'])
        stats_layout.addWidget(self.toplam_adet_card)
        stats_layout.addWidget(self.toplam_m2_card)
        stats_layout.addWidget(self.toplam_fire_card)
        stats_layout.addWidget(self.toplam_red_card)
        stats_layout.addWidget(self.urun_cesit_card)
        header.addLayout(stats_layout)

        layout.addLayout(header)

        # ===== FILTERS =====
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 10px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(12)

        input_style = f"""
            QLineEdit, QDateEdit {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 8px 12px;
                color: {s['text']};
                font-size: 13px;
            }}
            QLineEdit:focus, QDateEdit:focus {{ border-color: {s['primary']}; }}
        """
        combo_style = f"""
            QComboBox {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 8px 12px;
                color: {s['text']};
                font-size: 13px;
                min-width: 120px;
            }}
            QComboBox:hover {{ border-color: {s['border_light']}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                color: {s['text']};
                selection-background-color: {s['primary']};
            }}
        """

        # Periyot secimi
        lbl = QLabel("Periyot:")
        lbl.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;")
        filter_layout.addWidget(lbl)

        self.periyot_combo = QComboBox()
        self.periyot_combo.addItem("Gunluk", "GUNLUK")
        self.periyot_combo.addItem("Haftalik", "HAFTALIK")
        self.periyot_combo.addItem("Aylik", "AYLIK")
        self.periyot_combo.addItem("Tarih Arasi", "TARIH_ARASI")
        self.periyot_combo.setStyleSheet(combo_style)
        self.periyot_combo.setCurrentIndex(0)
        self.periyot_combo.currentIndexChanged.connect(self._on_periyot_changed)
        filter_layout.addWidget(self.periyot_combo)

        # Tarih alanlari
        lbl = QLabel("Baslangic:")
        lbl.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;")
        filter_layout.addWidget(lbl)

        self.tarih_bas = QDateEdit()
        self.tarih_bas.setCalendarPopup(True)
        self.tarih_bas.setDisplayFormat("dd.MM.yyyy")
        self.tarih_bas.setDate(QDate.currentDate())
        self.tarih_bas.setStyleSheet(input_style)
        filter_layout.addWidget(self.tarih_bas)

        self.tarih_bitis_label = QLabel("Bitis:")
        self.tarih_bitis_label.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;")
        filter_layout.addWidget(self.tarih_bitis_label)

        self.tarih_bit = QDateEdit()
        self.tarih_bit.setCalendarPopup(True)
        self.tarih_bit.setDisplayFormat("dd.MM.yyyy")
        self.tarih_bit.setDate(QDate.currentDate())
        self.tarih_bit.setStyleSheet(input_style)
        filter_layout.addWidget(self.tarih_bit)

        # Baslangicta tarih arasi gizli
        self.tarih_bitis_label.setVisible(False)
        self.tarih_bit.setVisible(False)

        # Hat filtresi
        lbl = QLabel("Hat:")
        lbl.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;")
        filter_layout.addWidget(lbl)

        self.hat_combo = QComboBox()
        self.hat_combo.addItem("Tum Hatlar", None)
        self._load_hat_filter()
        self.hat_combo.setStyleSheet(combo_style)
        filter_layout.addWidget(self.hat_combo)

        filter_layout.addStretch()

        # Ara butonu
        search_btn = QPushButton("Rapor Olustur")
        search_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        search_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(search_btn)

        filter_layout.addWidget(self.create_export_button(title="Uretim Raporu"))

        layout.addWidget(filter_frame)

        # ===== AKTIF FILTRE CUBUGU =====
        self.filter_bar = QFrame()
        self.filter_bar.setStyleSheet(f"""
            QFrame {{
                background: {brand.PRIMARY_SOFT};
                border: 1px solid {brand.PRIMARY};
                border-radius: 8px;
            }}
        """)
        fb_l = QHBoxLayout(self.filter_bar)
        fb_l.setContentsMargins(12, 6, 12, 6)
        fb_l.setSpacing(8)
        self.filter_label = QLabel("")
        self.filter_label.setStyleSheet(f"color: {brand.TEXT}; font-size: 13px; font-weight: 500;")
        fb_l.addWidget(self.filter_label)
        fb_l.addStretch()
        clear_btn = QPushButton("Filtreyi Temizle")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.ERROR}; color: white; border: none;
                border-radius: 6px; padding: 4px 14px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {brand.ERROR}; opacity: 0.8; }}
        """)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_filter)
        fb_l.addWidget(clear_btn)
        self.filter_bar.setVisible(False)
        layout.addWidget(self.filter_bar)

        # ===== TABS =====
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 10px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {s['input_bg']};
                color: {s['text_secondary']};
                border: 1px solid {s['border']};
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                padding: 10px 20px;
                margin-right: 2px;
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {s['card_bg']};
                color: {s['text']};
                border-bottom: 2px solid {s['primary']};
            }}
            QTabBar::tab:hover {{
                color: {s['text']};
            }}
        """)

        # Tab 1: Urun Ozet
        self.ozet_table = self._create_table(
            ["Urun Kodu", "Urun Adi", "Musteri", "Hat", "Toplam Adet",
             "Fire Adet", "Red Adet", "m2/Adet", "Toplam m2", "Aski Sayisi"],
            [100, 200, 150, 100, 90, 80, 80, 80, 100, 80],
            stretch_col=1
        )
        self.tabs.addTab(self.ozet_table, "Urun Bazli Ozet")

        # Tab 2: Gunluk Detay
        self.detay_table = self._create_table(
            ["Tarih", "Is Emri", "Urun Kodu", "Urun Adi", "Musteri", "Hat",
             "Vardiya", "Adet", "Fire", "Red", "m2/Adet", "Toplam m2", "Aski"],
            [90, 100, 100, 180, 130, 90, 70, 70, 60, 60, 70, 90, 60],
            stretch_col=3
        )
        self.tabs.addTab(self.detay_table, "Detayli Kayitlar")

        # Tab 3: Hat Bazli Ozet
        self.hat_table = self._create_table(
            ["Hat", "Urun Cesidi", "Toplam Adet", "Toplam Fire", "Toplam Red",
             "Toplam m2", "Fire %", "Ort. m2/Gun"],
            [150, 90, 100, 100, 100, 110, 80, 100],
            stretch_col=0
        )
        self.tabs.addTab(self.hat_table, "Hat Bazli Ozet")

        # Tiklanabilir filtre: Musteri veya Hat hucresine tikla -> filtrele
        self.ozet_table.cellClicked.connect(self._on_ozet_cell_clicked)
        self.detay_table.cellClicked.connect(self._on_detay_cell_clicked)

        layout.addWidget(self.tabs, 1)

    def _create_table(self, headers, widths, stretch_col=None):
        s = self.s
        table = QTableWidget()
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {s['card_bg']};
                border: none;
                gridline-color: {s['border']};
                color: {s['text']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {s['border']};
            }}
            QTableWidget::item:selected {{
                background: {s['primary']};
            }}
            QTableWidget::item:hover {{
                background: rgba(220, 38, 38, 0.08);
            }}
            QHeaderView::section {{
                background: rgba(0,0,0,0.3);
                color: {s['text_secondary']};
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid {s['primary']};
                font-weight: 600;
                font-size: 12px;
            }}
        """)
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        for i, w in enumerate(widths):
            table.setColumnWidth(i, w)
        if stretch_col is not None:
            table.horizontalHeader().setSectionResizeMode(stretch_col, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        return table

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setFixedSize(130, 70)
        frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-left: 4px solid {color};
                border-radius: 10px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 40))
        frame.setGraphicsEffect(shadow)

        fl = QVBoxLayout(frame)
        fl.setContentsMargins(12, 8, 12, 8)
        fl.setSpacing(2)

        t_label = QLabel(title)
        t_label.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px; font-weight: 500;")
        fl.addWidget(t_label)

        v_label = QLabel(value)
        v_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        v_label.setObjectName("stat_value")
        fl.addWidget(v_label)

        return frame

    # -----------------------------------------------------------------
    # TIKLANABILIR FILTRE
    # -----------------------------------------------------------------
    def _on_ozet_cell_clicked(self, row, col):
        if col in self.FILTER_COLS_OZET:
            item = self.ozet_table.item(row, col)
            if item and item.text() and item.text() != "TOPLAM":
                self._apply_table_filter(self.FILTER_COLS_OZET[col], item.text())

    def _on_detay_cell_clicked(self, row, col):
        if col in self.FILTER_COLS_DETAY:
            item = self.detay_table.item(row, col)
            if item and item.text():
                self._apply_table_filter(self.FILTER_COLS_DETAY[col], item.text())

    def _apply_table_filter(self, col_name, value):
        """Tum tablolarda belirli kolonu filtrele"""
        self._active_filter = (col_name, value)
        self.filter_label.setText(f"Filtre: {col_name} = {value}")
        self.filter_bar.setVisible(True)

        # Ozet tablosu (Musteri=2, Hat=3)
        ozet_col = {v: k for k, v in self.FILTER_COLS_OZET.items()}.get(col_name)
        if ozet_col is not None:
            for r in range(self.ozet_table.rowCount()):
                item = self.ozet_table.item(r, ozet_col)
                txt = item.text() if item else ""
                # TOPLAM satirini da gizle filtrede
                first = self.ozet_table.item(r, 0)
                is_toplam = first and first.text() == "TOPLAM"
                self.ozet_table.setRowHidden(r, txt != value and not is_toplam)

        # Detay tablosu (Musteri=4, Hat=5)
        detay_col = {v: k for k, v in self.FILTER_COLS_DETAY.items()}.get(col_name)
        if detay_col is not None:
            for r in range(self.detay_table.rowCount()):
                item = self.detay_table.item(r, detay_col)
                txt = item.text() if item else ""
                self.detay_table.setRowHidden(r, txt != value)

    def _clear_filter(self):
        """Filtreyi temizle, tum satirlari goster"""
        self._active_filter = None
        self.filter_bar.setVisible(False)
        for r in range(self.ozet_table.rowCount()):
            self.ozet_table.setRowHidden(r, False)
        for r in range(self.detay_table.rowCount()):
            self.detay_table.setRowHidden(r, False)

    def _load_hat_filter(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, kod, ISNULL(kisa_ad, ad) FROM tanim.uretim_hatlari WHERE aktif_mi=1 ORDER BY sira_no"
            )
            for row in cursor.fetchall():
                self.hat_combo.addItem(f"{row[1]} - {row[2]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _on_periyot_changed(self):
        periyot = self.periyot_combo.currentData()
        is_tarih_arasi = periyot == "TARIH_ARASI"
        self.tarih_bitis_label.setVisible(is_tarih_arasi)
        self.tarih_bit.setVisible(is_tarih_arasi)

        today = QDate.currentDate()
        if periyot == "GUNLUK":
            self.tarih_bas.setDate(today)
        elif periyot == "HAFTALIK":
            # Haftanin pazartesisi
            day_of_week = today.dayOfWeek()
            self.tarih_bas.setDate(today.addDays(-(day_of_week - 1)))
        elif periyot == "AYLIK":
            self.tarih_bas.setDate(QDate(today.year(), today.month(), 1))

    def _get_date_range(self):
        """Secilen periyoda gore tarih araligini dondur"""
        periyot = self.periyot_combo.currentData()
        bas = self.tarih_bas.date().toPython()

        if periyot == "GUNLUK":
            return bas, bas
        elif periyot == "HAFTALIK":
            from datetime import timedelta
            return bas, bas + timedelta(days=6)
        elif periyot == "AYLIK":
            import calendar
            last_day = calendar.monthrange(bas.year, bas.month)[1]
            from datetime import date
            return bas, date(bas.year, bas.month, last_day)
        elif periyot == "TARIH_ARASI":
            bit = self.tarih_bit.date().toPython()
            return bas, bit

        return bas, bas

    def _load_data(self):
        s = self.s
        tarih_bas, tarih_bit = self._get_date_range()
        hat_id = self.hat_combo.currentData()

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            hat_filter = ""
            params_base = [tarih_bas, tarih_bit]
            if hat_id:
                hat_filter = " AND uk.hat_id = ?"
                params_base.append(hat_id)

            # ===== TAB 1: URUN BAZLI OZET =====
            sql_ozet = f"""
                SELECT
                    ISNULL(ie.stok_kodu, '-') AS urun_kodu,
                    ISNULL(ie.stok_adi, '-') AS urun_adi,
                    ISNULL(ie.cari_unvani, '-') AS musteri,
                    h.kod + ' - ' + ISNULL(h.kisa_ad, h.ad) AS hat,
                    SUM(ISNULL(uk.uretilen_miktar, 0)) AS toplam_adet,
                    SUM(ISNULL(uk.fire_miktar, 0)) AS fire_adet,
                    ISNULL((
                        SELECT SUM(ISNULL(fk.hatali_adet, 0))
                        FROM kalite.final_kontrol fk
                        WHERE fk.is_emri_id = ie.id
                          AND fk.kontrol_tarihi BETWEEN ? AND DATEADD(day, 1, ?)
                    ), 0) AS red_adet,
                    ISNULL(u.yuzey_alani_m2, 0) AS m2_adet,
                    SUM(ISNULL(uk.uretilen_miktar, 0)) * ISNULL(u.yuzey_alani_m2, 0) AS toplam_m2,
                    SUM(ISNULL(uk.aski_sayisi, 0)) AS aski_sayisi
                FROM uretim.uretim_kayitlari uk
                JOIN siparis.is_emirleri ie ON uk.is_emri_id = ie.id
                LEFT JOIN stok.urunler u ON ie.urun_id = u.id
                JOIN tanim.uretim_hatlari h ON uk.hat_id = h.id
                WHERE uk.tarih BETWEEN ? AND ?
                {hat_filter}
                GROUP BY ie.id, ie.stok_kodu, ie.stok_adi, ie.cari_unvani,
                         h.kod, h.kisa_ad, h.ad, u.yuzey_alani_m2
                ORDER BY toplam_m2 DESC
            """
            ozet_params = [tarih_bas, tarih_bit] + params_base
            cursor.execute(sql_ozet, ozet_params)
            ozet_rows = cursor.fetchall()

            # Istatistikler  (red_adet = col 6)
            toplam_adet = sum(r[4] or 0 for r in ozet_rows)
            toplam_m2 = sum(r[8] or 0 for r in ozet_rows)
            toplam_fire = sum(r[5] or 0 for r in ozet_rows)
            toplam_red = sum(r[6] or 0 for r in ozet_rows)
            urun_cesidi = len(set((r[0], r[1]) for r in ozet_rows))

            self.toplam_adet_card.findChild(QLabel, "stat_value").setText(f"{toplam_adet:,.0f}")
            self.toplam_m2_card.findChild(QLabel, "stat_value").setText(f"{toplam_m2:,.1f}")
            self.toplam_fire_card.findChild(QLabel, "stat_value").setText(f"{toplam_fire:,.0f}")
            self.toplam_red_card.findChild(QLabel, "stat_value").setText(f"{toplam_red:,.0f}")
            self.urun_cesit_card.findChild(QLabel, "stat_value").setText(str(urun_cesidi))

            self._clear_filter()
            self.ozet_table.setRowCount(len(ozet_rows))
            for i, row in enumerate(ozet_rows):
                # row: [kodu, adi, musteri, hat, adet, fire, red, m2_birim, m2_toplam, aski]
                self.ozet_table.setItem(i, 0, QTableWidgetItem(str(row[0] or '')))
                self.ozet_table.setItem(i, 1, QTableWidgetItem(str(row[1] or '')))

                musteri_item = QTableWidgetItem(str(row[2] or ''))
                musteri_item.setForeground(QColor(brand.INFO))
                self.ozet_table.setItem(i, 2, musteri_item)

                hat_item = QTableWidgetItem(str(row[3] or ''))
                hat_item.setForeground(QColor(brand.INFO))
                self.ozet_table.setItem(i, 3, hat_item)

                adet_item = QTableWidgetItem(f"{row[4]:,.0f}" if row[4] else "0")
                adet_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.ozet_table.setItem(i, 4, adet_item)

                fire_item = QTableWidgetItem(f"{row[5]:,.0f}" if row[5] else "0")
                fire_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row[5] and row[5] > 0:
                    fire_item.setForeground(QColor(s['error']))
                self.ozet_table.setItem(i, 5, fire_item)

                red_item = QTableWidgetItem(f"{row[6]:,.0f}" if row[6] else "0")
                red_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row[6] and row[6] > 0:
                    red_item.setForeground(QColor(s['warning']))
                self.ozet_table.setItem(i, 6, red_item)

                m2_birim = QTableWidgetItem(f"{row[7]:,.4f}" if row[7] else "-")
                m2_birim.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.ozet_table.setItem(i, 7, m2_birim)

                m2_item = QTableWidgetItem(f"{row[8]:,.2f}" if row[8] else "0")
                m2_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                m2_item.setForeground(QColor(s['success']))
                self.ozet_table.setItem(i, 8, m2_item)

                aski_item = QTableWidgetItem(f"{row[9]:,.0f}" if row[9] else "0")
                aski_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.ozet_table.setItem(i, 9, aski_item)

                self.ozet_table.setRowHeight(i, 42)

            # Ozet tablosuna toplam satiri ekle
            if ozet_rows:
                total_row = len(ozet_rows)
                self.ozet_table.setRowCount(total_row + 1)

                toplam_label = QTableWidgetItem("TOPLAM")
                toplam_label.setForeground(QColor(s['primary']))
                self.ozet_table.setItem(total_row, 0, toplam_label)
                for c in range(1, 4):
                    self.ozet_table.setItem(total_row, c, QTableWidgetItem(""))

                for col, val, clr in [
                    (4, toplam_adet, s['primary']),
                    (5, toplam_fire, s['error']),
                    (6, toplam_red, s['warning']),
                ]:
                    item = QTableWidgetItem(f"{val:,.0f}")
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setForeground(QColor(clr))
                    self.ozet_table.setItem(total_row, col, item)

                self.ozet_table.setItem(total_row, 7, QTableWidgetItem(""))

                t_m2 = QTableWidgetItem(f"{toplam_m2:,.2f}")
                t_m2.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                t_m2.setForeground(QColor(s['success']))
                self.ozet_table.setItem(total_row, 8, t_m2)

                t_aski = QTableWidgetItem(f"{sum(r[9] or 0 for r in ozet_rows):,.0f}")
                t_aski.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.ozet_table.setItem(total_row, 9, t_aski)

                self.ozet_table.setRowHeight(total_row, 42)

            # ===== TAB 2: DETAYLI KAYITLAR =====
            sql_detay = f"""
                SELECT
                    uk.tarih,
                    ie.is_emri_no,
                    ISNULL(ie.stok_kodu, '-'),
                    ISNULL(ie.stok_adi, '-'),
                    ISNULL(ie.cari_unvani, '-'),
                    h.kod + ' - ' + ISNULL(h.kisa_ad, h.ad),
                    ISNULL(v.ad, '-'),
                    ISNULL(uk.uretilen_miktar, 0),
                    ISNULL(uk.fire_miktar, 0),
                    ISNULL((
                        SELECT SUM(ISNULL(fk2.hatali_adet, 0))
                        FROM kalite.final_kontrol fk2
                        WHERE fk2.is_emri_id = uk.is_emri_id
                          AND CAST(fk2.kontrol_tarihi AS DATE) = uk.tarih
                    ), 0) AS red_adet,
                    ISNULL(u.yuzey_alani_m2, 0),
                    ISNULL(uk.uretilen_miktar, 0) * ISNULL(u.yuzey_alani_m2, 0),
                    ISNULL(uk.aski_sayisi, 0)
                FROM uretim.uretim_kayitlari uk
                JOIN siparis.is_emirleri ie ON uk.is_emri_id = ie.id
                LEFT JOIN stok.urunler u ON ie.urun_id = u.id
                JOIN tanim.uretim_hatlari h ON uk.hat_id = h.id
                LEFT JOIN tanim.vardiyalar v ON uk.vardiya_id = v.id
                WHERE uk.tarih BETWEEN ? AND ?
                {hat_filter}
                ORDER BY uk.tarih DESC, uk.baslama_zamani DESC
            """
            cursor.execute(sql_detay, params_base)
            detay_rows = cursor.fetchall()

            # row: [tarih, is_emri, kodu, adi, musteri, hat, vardiya, adet, fire, red, m2b, m2t, aski]
            self.detay_table.setRowCount(len(detay_rows))
            for i, row in enumerate(detay_rows):
                tarih_str = row[0].strftime("%d.%m.%Y") if row[0] else '-'
                self.detay_table.setItem(i, 0, QTableWidgetItem(tarih_str))
                self.detay_table.setItem(i, 1, QTableWidgetItem(str(row[1] or '')))
                self.detay_table.setItem(i, 2, QTableWidgetItem(str(row[2] or '')))
                self.detay_table.setItem(i, 3, QTableWidgetItem(str(row[3] or '')))

                d_musteri = QTableWidgetItem(str(row[4] or ''))
                d_musteri.setForeground(QColor(brand.INFO))
                self.detay_table.setItem(i, 4, d_musteri)

                d_hat = QTableWidgetItem(str(row[5] or ''))
                d_hat.setForeground(QColor(brand.INFO))
                self.detay_table.setItem(i, 5, d_hat)
                self.detay_table.setItem(i, 6, QTableWidgetItem(str(row[6] or '')))

                adet_item = QTableWidgetItem(f"{row[7]:,.0f}" if row[7] else "0")
                adet_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.detay_table.setItem(i, 7, adet_item)

                fire_item = QTableWidgetItem(f"{row[8]:,.0f}" if row[8] else "0")
                fire_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row[8] and row[8] > 0:
                    fire_item.setForeground(QColor(s['error']))
                self.detay_table.setItem(i, 8, fire_item)

                red_item = QTableWidgetItem(f"{row[9]:,.0f}" if row[9] else "0")
                red_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row[9] and row[9] > 0:
                    red_item.setForeground(QColor(s['warning']))
                self.detay_table.setItem(i, 9, red_item)

                m2b = QTableWidgetItem(f"{row[10]:,.4f}" if row[10] else "-")
                m2b.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.detay_table.setItem(i, 10, m2b)

                m2t = QTableWidgetItem(f"{row[11]:,.2f}" if row[11] else "0")
                m2t.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                m2t.setForeground(QColor(s['success']))
                self.detay_table.setItem(i, 11, m2t)

                aski = QTableWidgetItem(f"{row[12]:,.0f}" if row[12] else "0")
                aski.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.detay_table.setItem(i, 12, aski)

                self.detay_table.setRowHeight(i, 40)

            # ===== TAB 3: HAT BAZLI OZET =====
            from datetime import date
            gun_sayisi = max(1, (tarih_bit - tarih_bas).days + 1)

            sql_hat = f"""
                SELECT
                    h.kod + ' - ' + ISNULL(h.kisa_ad, h.ad) AS hat,
                    COUNT(DISTINCT ISNULL(ie.stok_kodu, '')) AS urun_cesidi,
                    SUM(ISNULL(uk.uretilen_miktar, 0)) AS toplam_adet,
                    SUM(ISNULL(uk.fire_miktar, 0)) AS toplam_fire,
                    ISNULL((
                        SELECT SUM(ISNULL(fk3.hatali_adet, 0))
                        FROM kalite.final_kontrol fk3
                        JOIN siparis.is_emirleri ie3 ON fk3.is_emri_id = ie3.id
                        JOIN uretim.uretim_kayitlari uk3 ON uk3.is_emri_id = ie3.id
                            AND uk3.hat_id = h.id
                        WHERE uk3.tarih BETWEEN ? AND ?
                          AND fk3.kontrol_tarihi BETWEEN ? AND DATEADD(day, 1, ?)
                    ), 0) AS toplam_red,
                    SUM(ISNULL(uk.uretilen_miktar, 0) * ISNULL(u.yuzey_alani_m2, 0)) AS toplam_m2
                FROM uretim.uretim_kayitlari uk
                JOIN siparis.is_emirleri ie ON uk.is_emri_id = ie.id
                LEFT JOIN stok.urunler u ON ie.urun_id = u.id
                JOIN tanim.uretim_hatlari h ON uk.hat_id = h.id
                WHERE uk.tarih BETWEEN ? AND ?
                {hat_filter}
                GROUP BY h.id, h.kod, h.kisa_ad, h.ad
                ORDER BY toplam_m2 DESC
            """
            hat_params = [tarih_bas, tarih_bit, tarih_bas, tarih_bit] + params_base
            cursor.execute(sql_hat, hat_params)
            hat_rows = cursor.fetchall()

            # row: [hat, cesit, adet, fire, red, m2]
            self.hat_table.setRowCount(len(hat_rows))
            for i, row in enumerate(hat_rows):
                self.hat_table.setItem(i, 0, QTableWidgetItem(str(row[0] or '')))

                cesit = QTableWidgetItem(str(row[1] or 0))
                cesit.setTextAlignment(Qt.AlignCenter)
                self.hat_table.setItem(i, 1, cesit)

                adet = QTableWidgetItem(f"{row[2]:,.0f}" if row[2] else "0")
                adet.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.hat_table.setItem(i, 2, adet)

                fire = QTableWidgetItem(f"{row[3]:,.0f}" if row[3] else "0")
                fire.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row[3] and row[3] > 0:
                    fire.setForeground(QColor(s['error']))
                self.hat_table.setItem(i, 3, fire)

                red = QTableWidgetItem(f"{row[4]:,.0f}" if row[4] else "0")
                red.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row[4] and row[4] > 0:
                    red.setForeground(QColor(s['warning']))
                self.hat_table.setItem(i, 4, red)

                m2 = QTableWidgetItem(f"{row[5]:,.2f}" if row[5] else "0")
                m2.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                m2.setForeground(QColor(s['success']))
                self.hat_table.setItem(i, 5, m2)

                # Fire orani
                fire_oran = 0
                if row[2] and row[2] > 0 and row[3]:
                    fire_oran = (row[3] / (row[2] + row[3])) * 100
                fire_oran_item = QTableWidgetItem(f"{fire_oran:.1f}%")
                fire_oran_item.setTextAlignment(Qt.AlignCenter)
                if fire_oran > 5:
                    fire_oran_item.setForeground(QColor(s['error']))
                elif fire_oran > 2:
                    fire_oran_item.setForeground(QColor(s['warning']))
                self.hat_table.setItem(i, 6, fire_oran_item)

                # Ort m2/gun
                ort_m2 = (row[5] or 0) / gun_sayisi
                ort_item = QTableWidgetItem(f"{ort_m2:,.1f}")
                ort_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.hat_table.setItem(i, 7, ort_item)

                self.hat_table.setRowHeight(i, 42)

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
