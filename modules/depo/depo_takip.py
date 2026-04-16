# -*- coding: utf-8 -*-
"""
NEXOR ERP - Depo Takip Sayfasi
===============================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QSplitter, QWidget,
    QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class DepoTakipPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.secili_depo_id = None
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
        self.auto_refresh = QTimer()
        self.auto_refresh.timeout.connect(self._load_data)
        self.auto_refresh.start(10000)
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # ── 1. Header ──
        header = self.create_page_header(
            "Depo Takip",
            "Anlik depo stok durumlari"
        )
        self.auto_label = QLabel("Otomatik yenileme: 10sn")
        self.auto_label.setStyleSheet(
            f"color: {brand.SUCCESS}; font-size: {brand.FS_CAPTION}px;"
        )
        header.addWidget(self.auto_label)

        self.saat_label = QLabel()
        self.saat_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(self.saat_label)

        btn_refresh = self.create_primary_button("Yenile")
        btn_refresh.clicked.connect(self._load_data)
        header.addWidget(btn_refresh)

        layout.addLayout(header)

        # ── 2. KPI cards ──
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self.kart_depo = self.create_stat_card("TOPLAM DEPO", "0", color=brand.PRIMARY)
        kpi_row.addWidget(self.kart_depo)

        self.kart_dolu = self.create_stat_card("STOKLU DEPO", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self.kart_dolu)

        self.kart_toplam = self.create_stat_card("TOPLAM STOK", "0", color=brand.WARNING)
        kpi_row.addWidget(self.kart_toplam)

        self.kart_lot = self.create_stat_card("TOPLAM LOT", "0", color=brand.INFO)
        kpi_row.addWidget(self.kart_lot)

        kpi_row.addStretch()
        layout.addLayout(kpi_row)

        # ── 3. Splitter ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(brand.SP_1)

        # Sol - Depo kartlari
        sol_widget = QWidget()
        sol_layout = QVBoxLayout(sol_widget)
        sol_layout.setContentsMargins(0, 0, 0, 0)
        sol_layout.setSpacing(brand.SP_3)

        sol_title = QLabel("DEPOLAR")
        sol_title.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_CAPTION}px; letter-spacing: 0.8px;"
        )
        sol_layout.addWidget(sol_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.depo_container = QWidget()
        self.depo_grid = QGridLayout(self.depo_container)
        self.depo_grid.setSpacing(brand.SP_3)
        scroll.setWidget(self.depo_container)
        sol_layout.addWidget(scroll, 1)
        splitter.addWidget(sol_widget)

        # Sag - Stok detay
        sag_widget = QFrame()
        sag_widget.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_LG}px; }}"
        )
        sag_layout = QVBoxLayout(sag_widget)
        sag_layout.setContentsMargins(brand.SP_5, brand.SP_5, brand.SP_5, brand.SP_5)
        sag_layout.setSpacing(brand.SP_3)

        self.detay_title = QLabel("STOK DETAYI")
        self.detay_title.setStyleSheet(
            f"color: {brand.PRIMARY}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY}px;"
        )
        sag_layout.addWidget(self.detay_title)

        search_layout = QHBoxLayout()
        search_layout.setSpacing(brand.SP_3)
        ara_lbl = QLabel("Ara:")
        ara_lbl.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px;")
        search_layout.addWidget(ara_lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Lot no, stok kodu...")
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
        self.search_input.textChanged.connect(self._apply_filter)
        search_layout.addWidget(self.search_input)
        sag_layout.addLayout(search_layout)

        self.stok_table = QTableWidget()
        self.stok_table.setColumnCount(7)
        self.stok_table.setHorizontalHeaderLabels([
            "Lot No", "Stok Kodu", "Stok Adi", "Miktar", "Birim", "Son Hareket", "Durum"
        ])
        self.stok_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.stok_table.setColumnWidth(0, brand.sp(120))
        self.stok_table.setColumnWidth(1, brand.sp(100))
        self.stok_table.setColumnWidth(3, brand.sp(80))
        self.stok_table.setColumnWidth(4, brand.sp(60))
        self.stok_table.setColumnWidth(5, brand.sp(100))
        self.stok_table.setColumnWidth(6, brand.sp(100))
        self.stok_table.verticalHeader().setVisible(False)
        self.stok_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stok_table.setShowGrid(False)
        self.stok_table.setAlternatingRowColors(True)
        self.stok_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.stok_table.setStyleSheet(f"""
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
        sag_layout.addWidget(self.stok_table, 1)

        splitter.addWidget(sag_widget)
        splitter.setSizes([brand.sp(400), brand.sp(600)])
        layout.addWidget(splitter, 1)

    def _create_depo_kart(self, depo_id: int, kod: str, ad: str, miktar: float, lot_sayisi: int) -> QFrame:
        border_color = brand.SUCCESS if miktar > 0 else brand.BORDER
        bg_color = brand.SUCCESS_SOFT if miktar > 0 else brand.BG_INPUT

        frame = QFrame()
        frame.setObjectName(f"depo_{depo_id}")
        frame.setStyleSheet(f"""
            QFrame#depo_{depo_id} {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: {brand.R_LG}px;
            }}
            QFrame#depo_{depo_id}:hover {{
                border: 2px solid {brand.PRIMARY};
            }}
        """)
        frame.setCursor(Qt.PointingHandCursor)
        frame.setMinimumHeight(brand.sp(100))
        frame.mousePressEvent = lambda e, did=depo_id, dk=kod: self._depo_secildi(did, dk)

        vlayout = QVBoxLayout(frame)
        vlayout.setContentsMargins(brand.SP_3, brand.SP_3, brand.SP_3, brand.SP_3)
        vlayout.setSpacing(brand.SP_1)

        kod_label = QLabel(kod)
        kod_label.setStyleSheet(
            f"color: {brand.PRIMARY}; font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_BODY}px;"
        )
        vlayout.addWidget(kod_label)

        ad_label = QLabel(ad[:20] + "..." if len(ad) > 20 else ad)
        ad_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"
        )
        vlayout.addWidget(ad_label)

        miktar_label = QLabel(f"{miktar:,.0f}")
        miktar_label.setStyleSheet(
            f"color: {brand.SUCCESS if miktar > 0 else brand.TEXT_DIM}; "
            f"font-size: {brand.FS_HEADING}px; font-weight: {brand.FW_BOLD};"
        )
        vlayout.addWidget(miktar_label)

        lot_label = QLabel(f"{lot_sayisi} lot")
        lot_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"
        )
        vlayout.addWidget(lot_label)

        return frame

    def _update_time(self):
        self.saat_label.setText(datetime.now().strftime("%H:%M:%S"))

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT d.id, d.kod, d.ad, COALESCE(SUM(sb.miktar), 0), COUNT(DISTINCT sb.lot_no)
                FROM tanim.depolar d LEFT JOIN stok.stok_bakiye sb ON d.id = sb.depo_id AND sb.miktar > 0
                WHERE d.aktif_mi = 1 AND d.kod NOT LIKE 'URT-%' AND d.kod NOT LIKE 'ZN-%' AND d.kod NOT IN ('Yi')
                GROUP BY d.id, d.kod, d.ad ORDER BY d.kod""")
            depolar = cursor.fetchall()

            toplam_depo = len(depolar)
            dolu_depo = sum(1 for d in depolar if d[3] > 0)
            toplam_stok = sum(d[3] for d in depolar)
            toplam_lot = sum(d[4] for d in depolar)

            self.kart_depo.findChild(QLabel, "stat_value").setText(str(toplam_depo))
            self.kart_dolu.findChild(QLabel, "stat_value").setText(str(dolu_depo))
            self.kart_toplam.findChild(QLabel, "stat_value").setText(f"{toplam_stok:,.0f}")
            self.kart_lot.findChild(QLabel, "stat_value").setText(str(toplam_lot))

            while self.depo_grid.count():
                item = self.depo_grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            row, col, max_col = 0, 0, 3
            for depo in depolar:
                kart = self._create_depo_kart(depo[0], depo[1], depo[2], depo[3], depo[4])
                self.depo_grid.addWidget(kart, row, col)
                col += 1
                if col >= max_col:
                    col = 0
                    row += 1

            if depolar and not self.secili_depo_id:
                self._depo_secildi(depolar[0][0], depolar[0][1])
            elif self.secili_depo_id:
                self._load_stok_detay(self.secili_depo_id)
        except Exception as e:
            print(f"[depo_takip] Veri yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _depo_secildi(self, depo_id: int, depo_kod: str):
        self.secili_depo_id = depo_id
        self.detay_title.setText(f"STOK DETAYI - {depo_kod}")
        self._load_stok_detay(depo_id)

    def _load_stok_detay(self, depo_id: int):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT sb.lot_no, COALESCE(sb.stok_kodu, u.urun_kodu, ''), COALESCE(sb.stok_adi, u.urun_adi, ''),
                sb.miktar, COALESCE(sb.birim, b.kod, 'AD'), sb.son_hareket_tarihi, sb.kalite_durumu
                FROM stok.stok_bakiye sb LEFT JOIN stok.urunler u ON sb.urun_id = u.id LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                WHERE sb.depo_id = ? AND sb.miktar > 0 ORDER BY sb.son_hareket_tarihi DESC""", (depo_id,))
            rows = cursor.fetchall()
            self.stok_data = rows
            self._display_stok(rows)
        except Exception as e:
            print(f"[depo_takip] Stok detay hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _display_stok(self, rows):
        self.stok_table.setRowCount(0)
        for row in rows:
            row_idx = self.stok_table.rowCount()
            self.stok_table.insertRow(row_idx)

            item = QTableWidgetItem(row[0] or '')
            item.setForeground(QColor(brand.PRIMARY))
            self.stok_table.setItem(row_idx, 0, item)

            self.stok_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
            self.stok_table.setItem(row_idx, 2, QTableWidgetItem(row[2] or ''))

            item = QTableWidgetItem(f"{row[3]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.stok_table.setItem(row_idx, 3, item)

            self.stok_table.setItem(row_idx, 4, QTableWidgetItem(row[4] or 'AD'))
            self.stok_table.setItem(row_idx, 5, QTableWidgetItem(
                row[5].strftime('%d.%m.%Y') if row[5] else '-'))

            durum = row[6] or ''
            item = QTableWidgetItem(durum)
            if durum in ('ONAYLANDI', 'SEVKE_HAZIR'):
                item.setForeground(QColor(brand.SUCCESS))
            elif durum in ('BEKLIYOR', 'KALITE_BEKLIYOR', 'URETIMDE'):
                item.setForeground(QColor(brand.WARNING))
            elif 'RED' in durum.upper():
                item.setForeground(QColor(brand.ERROR))
            self.stok_table.setItem(row_idx, 6, item)

    def _apply_filter(self):
        search = self.search_input.text().lower().strip()
        if not search:
            self._display_stok(self.stok_data)
            return
        filtered = [r for r in self.stok_data if search in f"{r[0]} {r[1]} {r[2]}".lower()]
        self._display_stok(filtered)
