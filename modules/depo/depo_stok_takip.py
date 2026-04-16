# -*- coding: utf-8 -*-
"""
NEXOR ERP - Stok Takip Sayfasi
===============================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
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
from core.nexor_brand import brand


class DepoStokTakipPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.secili_urun_id = None
        self.secili_depo_id = None
        self.lot_data = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # ── 1. Header ──
        header = self.create_page_header(
            "Stok Takip",
            "Referans numarasi ile urun stok sorgulama"
        )
        layout.addLayout(header)

        # ── 2. Arama Alani ──
        search_frame = QFrame()
        search_frame.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_LG}px; }}"
        )
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(brand.SP_5, brand.SP_3, brand.SP_5, brand.SP_3)
        search_layout.setSpacing(brand.SP_3)

        search_label = QLabel("Ara:")
        search_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px;"
        )
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Referans no / stok kodu / stok adi giriniz...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.search_input.returnPressed.connect(self._ara)
        search_layout.addWidget(self.search_input, 1)

        ara_btn = self.create_primary_button("Ara")
        ara_btn.clicked.connect(self._ara)
        search_layout.addWidget(ara_btn)

        layout.addWidget(search_frame)

        # ── 3. KPI kartlari ──
        self.ozet_frame = QFrame()
        self.ozet_frame.setVisible(False)
        ozet_layout = QHBoxLayout(self.ozet_frame)
        ozet_layout.setContentsMargins(0, 0, 0, 0)
        ozet_layout.setSpacing(brand.SP_4)

        self.kart_toplam = self.create_stat_card("TOPLAM MIKTAR", "0", color=brand.PRIMARY)
        ozet_layout.addWidget(self.kart_toplam)
        self.kart_kullanilabilir = self.create_stat_card("KULLANILABILIR", "0", color=brand.SUCCESS)
        ozet_layout.addWidget(self.kart_kullanilabilir)
        self.kart_lot = self.create_stat_card("LOT SAYISI", "0", color=brand.WARNING)
        ozet_layout.addWidget(self.kart_lot)
        self.kart_depo = self.create_stat_card("DEPO SAYISI", "0", color=brand.INFO)
        ozet_layout.addWidget(self.kart_depo)
        ozet_layout.addStretch()

        layout.addWidget(self.ozet_frame)

        # ── 4. Urun bilgi satiri ──
        self.urun_info = QLabel("")
        self.urun_info.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px; "
            f"padding: {brand.SP_1}px 0;"
        )
        self.urun_info.setVisible(False)
        layout.addWidget(self.urun_info)

        # ── 5. Splitter: Depo bazli + Lot detay ──
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(brand.SP_1)

        # -- Depo Bazli Ozet Tablosu --
        depo_widget = QFrame()
        depo_widget.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_LG}px; }}"
        )
        depo_layout = QVBoxLayout(depo_widget)
        depo_layout.setContentsMargins(brand.SP_5, brand.SP_5, brand.SP_5, brand.SP_5)
        depo_layout.setSpacing(brand.SP_3)

        depo_header = QHBoxLayout()
        depo_title = QLabel("DEPO BAZLI OZET")
        depo_title.setStyleSheet(
            f"color: {brand.PRIMARY}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY}px;"
        )
        depo_header.addWidget(depo_title)
        depo_header.addStretch()
        self.depo_filter_label = QLabel("")
        self.depo_filter_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"
        )
        depo_header.addWidget(self.depo_filter_label)
        depo_layout.addLayout(depo_header)

        self.depo_table = QTableWidget()
        self.depo_table.setColumnCount(6)
        self.depo_table.setHorizontalHeaderLabels([
            "Depo Kodu", "Depo Adi", "Toplam Miktar", "Rezerve", "Kullanilabilir", "Lot Sayisi"
        ])
        self.depo_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.depo_table.setColumnWidth(0, brand.sp(100))
        self.depo_table.setColumnWidth(2, brand.sp(120))
        self.depo_table.setColumnWidth(3, brand.sp(100))
        self.depo_table.setColumnWidth(4, brand.sp(120))
        self.depo_table.setColumnWidth(5, brand.sp(90))
        self.depo_table.verticalHeader().setVisible(False)
        self.depo_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.depo_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.depo_table.setShowGrid(False)
        self.depo_table.setAlternatingRowColors(True)
        self.depo_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self._apply_table_style(self.depo_table)
        self.depo_table.clicked.connect(self._depo_satir_secildi)
        depo_layout.addWidget(self.depo_table, 1)

        splitter.addWidget(depo_widget)

        # -- Lot Detay Tablosu --
        lot_widget = QFrame()
        lot_widget.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_LG}px; }}"
        )
        lot_layout = QVBoxLayout(lot_widget)
        lot_layout.setContentsMargins(brand.SP_5, brand.SP_5, brand.SP_5, brand.SP_5)
        lot_layout.setSpacing(brand.SP_3)

        lot_header = QHBoxLayout()
        self.lot_title = QLabel("LOT DETAYLARI")
        self.lot_title.setStyleSheet(
            f"color: {brand.PRIMARY}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY}px;"
        )
        lot_header.addWidget(self.lot_title)
        lot_header.addStretch()

        self.lot_filter_btn = QPushButton("Tum Lotlar")
        self.lot_filter_btn.setCursor(Qt.PointingHandCursor)
        self.lot_filter_btn.setFixedHeight(brand.sp(38))
        self.lot_filter_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_3}px;
                color: {brand.TEXT_MUTED};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ border-color: {brand.PRIMARY}; color: {brand.TEXT}; }}
        """)
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
        self.lot_table.setColumnWidth(0, brand.sp(120))
        self.lot_table.setColumnWidth(1, brand.sp(120))
        self.lot_table.setColumnWidth(2, brand.sp(90))
        self.lot_table.setColumnWidth(3, brand.sp(130))
        self.lot_table.setColumnWidth(4, brand.sp(90))
        self.lot_table.setColumnWidth(5, brand.sp(80))
        self.lot_table.setColumnWidth(6, brand.sp(100))
        self.lot_table.setColumnWidth(7, brand.sp(120))
        self.lot_table.setColumnWidth(8, brand.sp(100))
        self.lot_table.setColumnWidth(10, brand.sp(110))
        self.lot_table.setColumnWidth(11, brand.sp(60))
        self.lot_table.verticalHeader().setVisible(False)
        self.lot_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lot_table.setShowGrid(False)
        self.lot_table.setAlternatingRowColors(True)
        self.lot_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self._apply_table_style(self.lot_table)
        lot_layout.addWidget(self.lot_table, 1)

        splitter.addWidget(lot_widget)
        splitter.setSizes([brand.sp(250), brand.sp(450)])
        layout.addWidget(splitter, 1)

    def _apply_table_style(self, table: QTableWidget):
        """Brand uyumlu tablo stili uygula"""
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_3}px {brand.SP_4}px;
                border-bottom: 1px solid {brand.BORDER};
                color: {brand.TEXT};
            }}
            QTableWidget::item:alternate {{ background: {brand.BG_MAIN}; }}
            QTableWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_4}px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """)

    # =========================================================================
    # ARAMA
    # =========================================================================

    def _ara(self):
        arama = self.search_input.text().strip()
        if not arama:
            return

        conn = None
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
            self.kart_toplam.findChild(QLabel, "stat_value").setText(f"{secilen[3]:,.0f}")
            self.kart_kullanilabilir.findChild(QLabel, "stat_value").setText(f"{secilen[5]:,.0f}")
            self.kart_lot.findChild(QLabel, "stat_value").setText(str(secilen[6]))
            self.kart_depo.findChild(QLabel, "stat_value").setText(str(secilen[7]))
            self.ozet_frame.setVisible(True)

            # Urun bilgisi
            self.urun_info.setText(f"Urun: {secilen[1]} - {secilen[2]}")
            self.urun_info.setVisible(True)

            # Tablolari yukle
            self._load_depo_ozet(secilen[0])
            self._load_lot_detay(secilen[0])

        except Exception as e:
            print(f"[depo_stok_takip] Arama hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # =========================================================================
    # DEPO BAZLI OZET
    # =========================================================================

    def _load_depo_ozet(self, urun_id: int):
        conn = None
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
            self._display_depo_table(rows)
        except Exception as e:
            print(f"[depo_stok_takip] Depo ozet hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _display_depo_table(self, rows):
        self.depo_table.setRowCount(0)
        for row in rows:
            idx = self.depo_table.rowCount()
            self.depo_table.insertRow(idx)

            # Depo Kodu
            item = QTableWidgetItem(row[0] or "-")
            item.setForeground(QColor(brand.PRIMARY))
            item.setFont(QFont(brand.FONT_FAMILY, brand.fs(10), QFont.Bold))
            self.depo_table.setItem(idx, 0, item)

            # Depo Adi
            self.depo_table.setItem(idx, 1, QTableWidgetItem(row[1] or "-"))

            # Toplam Miktar
            item = QTableWidgetItem(f"{row[2]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setForeground(QColor(brand.TEXT))
            self.depo_table.setItem(idx, 2, item)

            # Rezerve
            item = QTableWidgetItem(f"{row[3]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if row[3] > 0:
                item.setForeground(QColor(brand.WARNING))
            self.depo_table.setItem(idx, 3, item)

            # Kullanilabilir
            item = QTableWidgetItem(f"{row[4]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setForeground(QColor(brand.SUCCESS))
            self.depo_table.setItem(idx, 4, item)

            # Lot Sayisi
            item = QTableWidgetItem(str(row[5]))
            item.setTextAlignment(Qt.AlignCenter)
            self.depo_table.setItem(idx, 5, item)

    # =========================================================================
    # LOT DETAYLARI
    # =========================================================================

    def _load_lot_detay(self, urun_id: int):
        conn = None
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
            self.lot_data = rows
            self._display_lot_table(rows)
            self.lot_title.setText("LOT DETAYLARI")
            self.depo_filter_label.setText("")
        except Exception as e:
            print(f"[depo_stok_takip] Lot detay hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _display_lot_table(self, rows):
        self.lot_table.setRowCount(0)
        for row in rows:
            idx = self.lot_table.rowCount()
            self.lot_table.insertRow(idx)

            bloke = bool(row[8])
            kalite = row[7] or ""

            # Lot No
            item = QTableWidgetItem(row[0] or "-")
            item.setForeground(QColor(brand.PRIMARY))
            if bloke:
                font = QFont(brand.FONT_FAMILY, brand.fs(10))
                font.setStrikeOut(True)
                item.setFont(font)
                item.setForeground(QColor(brand.TEXT_DIM))
            self.lot_table.setItem(idx, 0, item)

            # Parent Lot
            item = QTableWidgetItem(row[1] or "-")
            if bloke:
                item.setForeground(QColor(brand.TEXT_DIM))
            self.lot_table.setItem(idx, 1, item)

            # Depo Kodu
            item = QTableWidgetItem(row[2] or "-")
            if bloke:
                item.setForeground(QColor(brand.TEXT_DIM))
            self.lot_table.setItem(idx, 2, item)

            # Depo Adi
            item = QTableWidgetItem(row[3] or "-")
            if bloke:
                item.setForeground(QColor(brand.TEXT_DIM))
            self.lot_table.setItem(idx, 3, item)

            # Miktar
            item = QTableWidgetItem(f"{row[4]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if bloke:
                item.setForeground(QColor(brand.TEXT_DIM))
            self.lot_table.setItem(idx, 4, item)

            # Rezerve
            item = QTableWidgetItem(f"{row[5]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if row[5] > 0:
                item.setForeground(QColor(brand.WARNING))
            if bloke:
                item.setForeground(QColor(brand.TEXT_DIM))
            self.lot_table.setItem(idx, 5, item)

            # Kullanilabilir
            item = QTableWidgetItem(f"{row[6]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setForeground(QColor(brand.SUCCESS))
            if bloke:
                item.setForeground(QColor(brand.TEXT_DIM))
            self.lot_table.setItem(idx, 6, item)

            # Kalite Durumu
            item = QTableWidgetItem(kalite)
            if bloke:
                item.setText(f"{kalite} [BLOKE]")
                item.setForeground(QColor(brand.TEXT_DIM))
            elif "ONAY" in kalite.upper():
                item.setForeground(QColor(brand.SUCCESS))
            elif "BEKL" in kalite.upper():
                item.setForeground(QColor(brand.WARNING))
            elif "RED" in kalite.upper():
                item.setForeground(QColor(brand.ERROR))
            self.lot_table.setItem(idx, 7, item)

            # Giris Tarihi
            tarih = row[9]
            tarih_str = tarih.strftime("%d.%m.%Y") if tarih else "-"
            item = QTableWidgetItem(tarih_str)
            if bloke:
                item.setForeground(QColor(brand.TEXT_DIM))
            self.lot_table.setItem(idx, 8, item)

            # Musteri
            item = QTableWidgetItem(row[10] or "-")
            if bloke:
                item.setForeground(QColor(brand.TEXT_DIM))
            self.lot_table.setItem(idx, 9, item)

            # Kaplama Tipi
            item = QTableWidgetItem(row[11] or "-")
            if bloke:
                item.setForeground(QColor(brand.TEXT_DIM))
            self.lot_table.setItem(idx, 10, item)

            # Birim
            item = QTableWidgetItem(row[12] or "ADET")
            if bloke:
                item.setForeground(QColor(brand.TEXT_DIM))
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
        self.lot_title.setText(f"LOT DETAYLARI - {depo_kodu}")
        self.depo_filter_label.setText(f"Filtre: {depo_kodu}")
        self.secili_depo_id = depo_kodu

    def _tum_lotlari_goster(self):
        if self.lot_data:
            self._display_lot_table(self.lot_data)
            self.lot_title.setText("LOT DETAYLARI")
            self.depo_filter_label.setText("")
            self.secili_depo_id = None
            self.depo_table.clearSelection()
