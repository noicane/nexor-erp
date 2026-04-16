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
        'bg_main': brand.BG_MAIN,
        'bg_hover': brand.BG_HOVER,
        'border_light': brand.BORDER_HARD,
    }


class RaporUretimPage(BasePage):
    """Uretim Raporu - Urun bazli m2/adet ozet ve detay"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
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
        self.urun_cesit_card = self._create_stat_card("Urun Cesidi", "0", s['warning'])
        stats_layout.addWidget(self.toplam_adet_card)
        stats_layout.addWidget(self.toplam_m2_card)
        stats_layout.addWidget(self.toplam_fire_card)
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
             "Fire Adet", "m2/Adet", "Toplam m2", "Aski Sayisi"],
            [100, 200, 150, 100, 90, 80, 80, 100, 80],
            stretch_col=1
        )
        self.tabs.addTab(self.ozet_table, "Urun Bazli Ozet")

        # Tab 2: Gunluk Detay
        self.detay_table = self._create_table(
            ["Tarih", "Is Emri", "Urun Kodu", "Urun Adi", "Musteri", "Hat",
             "Vardiya", "Adet", "Fire", "m2/Adet", "Toplam m2", "Aski"],
            [90, 100, 100, 180, 130, 90, 70, 70, 60, 70, 90, 60],
            stretch_col=3
        )
        self.tabs.addTab(self.detay_table, "Detayli Kayitlar")

        # Tab 3: Hat Bazli Ozet
        self.hat_table = self._create_table(
            ["Hat", "Urun Cesidi", "Toplam Adet", "Toplam Fire", "Toplam m2",
             "Fire Orani %", "Ort. m2/Gun"],
            [150, 90, 100, 100, 110, 90, 100],
            stretch_col=0
        )
        self.tabs.addTab(self.hat_table, "Hat Bazli Ozet")

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
        v_label.setObjectName("value_label")
        fl.addWidget(v_label)

        return frame

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
                    ISNULL(u.yuzey_alani_m2, 0) AS m2_adet,
                    SUM(ISNULL(uk.uretilen_miktar, 0)) * ISNULL(u.yuzey_alani_m2, 0) AS toplam_m2,
                    SUM(ISNULL(uk.aski_sayisi, 0)) AS aski_sayisi
                FROM uretim.uretim_kayitlari uk
                JOIN siparis.is_emirleri ie ON uk.is_emri_id = ie.id
                LEFT JOIN stok.urunler u ON ie.urun_id = u.id
                JOIN tanim.uretim_hatlari h ON uk.hat_id = h.id
                WHERE uk.tarih BETWEEN ? AND ?
                {hat_filter}
                GROUP BY ie.stok_kodu, ie.stok_adi, ie.cari_unvani,
                         h.kod, h.kisa_ad, h.ad, u.yuzey_alani_m2
                ORDER BY toplam_m2 DESC
            """
            cursor.execute(sql_ozet, params_base)
            ozet_rows = cursor.fetchall()

            # Istatistikler
            toplam_adet = sum(r[4] or 0 for r in ozet_rows)
            toplam_m2 = sum(r[7] or 0 for r in ozet_rows)
            toplam_fire = sum(r[5] or 0 for r in ozet_rows)
            urun_cesidi = len(set((r[0], r[1]) for r in ozet_rows))

            self.toplam_adet_card.findChild(QLabel, "value_label").setText(f"{toplam_adet:,.0f}")
            self.toplam_m2_card.findChild(QLabel, "value_label").setText(f"{toplam_m2:,.1f}")
            self.toplam_fire_card.findChild(QLabel, "value_label").setText(f"{toplam_fire:,.0f}")
            self.urun_cesit_card.findChild(QLabel, "value_label").setText(str(urun_cesidi))

            self.ozet_table.setRowCount(len(ozet_rows))
            for i, row in enumerate(ozet_rows):
                self.ozet_table.setItem(i, 0, QTableWidgetItem(str(row[0] or '')))
                self.ozet_table.setItem(i, 1, QTableWidgetItem(str(row[1] or '')))
                self.ozet_table.setItem(i, 2, QTableWidgetItem(str(row[2] or '')))
                self.ozet_table.setItem(i, 3, QTableWidgetItem(str(row[3] or '')))

                adet_item = QTableWidgetItem(f"{row[4]:,.0f}" if row[4] else "0")
                adet_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.ozet_table.setItem(i, 4, adet_item)

                fire_item = QTableWidgetItem(f"{row[5]:,.0f}" if row[5] else "0")
                fire_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row[5] and row[5] > 0:
                    fire_item.setForeground(QColor(s['error']))
                self.ozet_table.setItem(i, 5, fire_item)

                m2_birim = QTableWidgetItem(f"{row[6]:,.4f}" if row[6] else "-")
                m2_birim.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.ozet_table.setItem(i, 6, m2_birim)

                m2_item = QTableWidgetItem(f"{row[7]:,.2f}" if row[7] else "0")
                m2_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                m2_item.setForeground(QColor(s['success']))
                self.ozet_table.setItem(i, 7, m2_item)

                aski_item = QTableWidgetItem(f"{row[8]:,.0f}" if row[8] else "0")
                aski_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.ozet_table.setItem(i, 8, aski_item)

                self.ozet_table.setRowHeight(i, 42)

            # Ozet tablosuna toplam satiri ekle
            if ozet_rows:
                total_row = len(ozet_rows)
                self.ozet_table.setRowCount(total_row + 1)
                bold_style = f"font-weight: bold; color: {s['text']};"

                toplam_label = QTableWidgetItem("TOPLAM")
                toplam_label.setForeground(QColor(s['primary']))
                self.ozet_table.setItem(total_row, 0, toplam_label)
                for c in range(1, 4):
                    self.ozet_table.setItem(total_row, c, QTableWidgetItem(""))

                t_adet = QTableWidgetItem(f"{toplam_adet:,.0f}")
                t_adet.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                t_adet.setForeground(QColor(s['primary']))
                self.ozet_table.setItem(total_row, 4, t_adet)

                t_fire = QTableWidgetItem(f"{toplam_fire:,.0f}")
                t_fire.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                t_fire.setForeground(QColor(s['error']))
                self.ozet_table.setItem(total_row, 5, t_fire)

                self.ozet_table.setItem(total_row, 6, QTableWidgetItem(""))

                t_m2 = QTableWidgetItem(f"{toplam_m2:,.2f}")
                t_m2.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                t_m2.setForeground(QColor(s['success']))
                self.ozet_table.setItem(total_row, 7, t_m2)

                t_aski = QTableWidgetItem(f"{sum(r[8] or 0 for r in ozet_rows):,.0f}")
                t_aski.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.ozet_table.setItem(total_row, 8, t_aski)

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

            self.detay_table.setRowCount(len(detay_rows))
            for i, row in enumerate(detay_rows):
                tarih_str = row[0].strftime("%d.%m.%Y") if row[0] else '-'
                self.detay_table.setItem(i, 0, QTableWidgetItem(tarih_str))
                self.detay_table.setItem(i, 1, QTableWidgetItem(str(row[1] or '')))
                self.detay_table.setItem(i, 2, QTableWidgetItem(str(row[2] or '')))
                self.detay_table.setItem(i, 3, QTableWidgetItem(str(row[3] or '')))
                self.detay_table.setItem(i, 4, QTableWidgetItem(str(row[4] or '')))
                self.detay_table.setItem(i, 5, QTableWidgetItem(str(row[5] or '')))
                self.detay_table.setItem(i, 6, QTableWidgetItem(str(row[6] or '')))

                adet_item = QTableWidgetItem(f"{row[7]:,.0f}" if row[7] else "0")
                adet_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.detay_table.setItem(i, 7, adet_item)

                fire_item = QTableWidgetItem(f"{row[8]:,.0f}" if row[8] else "0")
                fire_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row[8] and row[8] > 0:
                    fire_item.setForeground(QColor(s['error']))
                self.detay_table.setItem(i, 8, fire_item)

                m2b = QTableWidgetItem(f"{row[9]:,.4f}" if row[9] else "-")
                m2b.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.detay_table.setItem(i, 9, m2b)

                m2t = QTableWidgetItem(f"{row[10]:,.2f}" if row[10] else "0")
                m2t.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                m2t.setForeground(QColor(s['success']))
                self.detay_table.setItem(i, 10, m2t)

                aski = QTableWidgetItem(f"{row[11]:,.0f}" if row[11] else "0")
                aski.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.detay_table.setItem(i, 11, aski)

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
                    SUM(ISNULL(uk.uretilen_miktar, 0) * ISNULL(u.yuzey_alani_m2, 0)) AS toplam_m2
                FROM uretim.uretim_kayitlari uk
                JOIN siparis.is_emirleri ie ON uk.is_emri_id = ie.id
                LEFT JOIN stok.urunler u ON ie.urun_id = u.id
                JOIN tanim.uretim_hatlari h ON uk.hat_id = h.id
                WHERE uk.tarih BETWEEN ? AND ?
                {hat_filter}
                GROUP BY h.kod, h.kisa_ad, h.ad
                ORDER BY toplam_m2 DESC
            """
            cursor.execute(sql_hat, params_base)
            hat_rows = cursor.fetchall()

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

                m2 = QTableWidgetItem(f"{row[4]:,.2f}" if row[4] else "0")
                m2.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                m2.setForeground(QColor(s['success']))
                self.hat_table.setItem(i, 4, m2)

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
                self.hat_table.setItem(i, 5, fire_oran_item)

                # Ort m2/gun
                ort_m2 = (row[4] or 0) / gun_sayisi
                ort_item = QTableWidgetItem(f"{ort_m2:,.1f}")
                ort_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.hat_table.setItem(i, 6, ort_item)

                self.hat_table.setRowHeight(i, 42)

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
