# -*- coding: utf-8 -*-
"""
NEXOR ERP - Lab Event Log
Laboratuvar analiz event'lerini listeler ve yonetir
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class LabEventLogPage(BasePage):
    """Lab Event Log - Laboratuvar olaylari takip ekrani"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

        # Otomatik yenileme (30 saniye)
        self.auto_refresh = QTimer()
        self.auto_refresh.timeout.connect(self._load_data)
        self.auto_refresh.start(30000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # ── 1. Header ──
        header = self.create_page_header(
            "Lab Event Log",
            "Laboratuvar analiz olaylari ve uyarilar"
        )

        # KPI widgets in header
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self._kpi_toplam = self.create_stat_card("TOPLAM", "0", color=brand.INFO)
        kpi_row.addWidget(self._kpi_toplam)
        self._kpi_bekleyen = self.create_stat_card("BEKLEYEN", "0", color=brand.WARNING)
        kpi_row.addWidget(self._kpi_bekleyen)
        self._kpi_kritik = self.create_stat_card("KRITIK", "0", color=brand.ERROR)
        kpi_row.addWidget(self._kpi_kritik)
        kpi_row.addStretch()

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        header.addWidget(btn_yenile)

        layout.addLayout(header)
        layout.addLayout(kpi_row)

        # ── 2. Filtreler ──
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)
        filter_layout.setSpacing(brand.SP_3)

        input_css = f"""
            QComboBox, QDateEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus, QDateEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """

        # Banyo
        lbl_banyo = QLabel("Banyo:")
        lbl_banyo.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        filter_layout.addWidget(lbl_banyo)
        self.banyo_combo = QComboBox()
        self.banyo_combo.setFixedWidth(brand.sp(180))
        self.banyo_combo.setStyleSheet(input_css)
        self.banyo_combo.addItem("Tumu", None)
        self._load_banyo_filter()
        self.banyo_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.banyo_combo)

        # Event Tipi
        lbl_tip = QLabel("Tip:")
        lbl_tip.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        filter_layout.addWidget(lbl_tip)
        self.event_combo = QComboBox()
        self.event_combo.setFixedWidth(brand.sp(150))
        self.event_combo.setStyleSheet(input_css)
        self.event_combo.addItem("Tumu", None)
        self.event_combo.addItem("Uyari", "LAB_ANALIZ_UYARI")
        self.event_combo.addItem("Kritik", "LAB_ANALIZ_KRITIK")
        self.event_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.event_combo)

        # Durum
        lbl_durum = QLabel("Durum:")
        lbl_durum.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        filter_layout.addWidget(lbl_durum)
        self.durum_combo = QComboBox()
        self.durum_combo.setFixedWidth(brand.sp(120))
        self.durum_combo.setStyleSheet(input_css)
        self.durum_combo.addItem("Tumu", None)
        self.durum_combo.addItem("Bekleyen", "BEKLIYOR")
        self.durum_combo.addItem("Okundu", "OKUNDU")
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.durum_combo)

        # Tarih
        lbl_tarih = QLabel("Tarih:")
        lbl_tarih.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        filter_layout.addWidget(lbl_tarih)

        self.tarih_bas = QDateEdit()
        self.tarih_bas.setDate(QDate.currentDate().addDays(-7))
        self.tarih_bas.setCalendarPopup(True)
        self.tarih_bas.setFixedWidth(brand.sp(110))
        self.tarih_bas.setStyleSheet(input_css)
        filter_layout.addWidget(self.tarih_bas)

        sep_lbl = QLabel("-")
        sep_lbl.setStyleSheet(f"color: {brand.TEXT_DIM};")
        filter_layout.addWidget(sep_lbl)

        self.tarih_bit = QDateEdit()
        self.tarih_bit.setDate(QDate.currentDate())
        self.tarih_bit.setCalendarPopup(True)
        self.tarih_bit.setFixedWidth(brand.sp(110))
        self.tarih_bit.setStyleSheet(input_css)
        filter_layout.addWidget(self.tarih_bit)

        ara_btn = self.create_primary_button("Ara")
        ara_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(ara_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        # ── 3. Tablo ──
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Banyo", "Event", "Sicaklik", "pH", "Analist", "Zaman", "Durum", "Islem"
        ])

        self.table.setColumnWidth(0, brand.sp(60))
        self.table.setColumnWidth(1, brand.sp(150))
        self.table.setColumnWidth(2, brand.sp(150))
        self.table.setColumnWidth(3, brand.sp(80))
        self.table.setColumnWidth(4, brand.sp(70))
        self.table.setColumnWidth(5, brand.sp(120))
        self.table.setColumnWidth(6, brand.sp(140))
        self.table.setColumnWidth(7, brand.sp(100))
        self.table.setColumnWidth(8, brand.sp(100))

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet(f"""
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

        layout.addWidget(self.table, 1)

        # ── 4. Footer ──
        self.footer_label = QLabel("Yukleniyor...")
        self.footer_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;"
        )
        layout.addWidget(self.footer_label)

    # -----------------------------------------------------------------
    def _load_banyo_filter(self):
        """Banyo filtresi yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad
                FROM uretim.banyo_tanimlari
                WHERE aktif_mi = 1
                ORDER BY kod
            """)
            for row in cursor.fetchall():
                self.banyo_combo.addItem(f"{row[1]} - {row[2]}", row[0])
        except Exception as e:
            print(f"Banyo filtresi yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # -----------------------------------------------------------------
    def _load_data(self):
        """Event log verilerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Filtreler
            banyo_id = self.banyo_combo.currentData()
            event_tipi = self.event_combo.currentData()
            durum = self.durum_combo.currentData()
            tarih_bas = self.tarih_bas.date().toPython()
            tarih_bit = self.tarih_bit.date().toPython()

            # Ana sorgu
            query = """
                SELECT
                    e.id,
                    b.kod + ' - ' + b.ad AS banyo,
                    e.event_tipi,
                    e.sicaklik,
                    e.ph,
                    p.ad + ' ' + p.soyad AS analist,
                    e.event_zamani,
                    e.event_durumu,
                    e.banyo_id
                FROM uretim.lab_event_log e
                LEFT JOIN uretim.banyo_tanimlari b ON e.banyo_id = b.id
                LEFT JOIN ik.personeller p ON e.analist_id = p.id
                WHERE e.event_zamani >= ? AND e.event_zamani < DATEADD(DAY, 1, ?)
            """
            params = [tarih_bas, tarih_bit]

            if banyo_id:
                query += " AND e.banyo_id = ?"
                params.append(banyo_id)

            if event_tipi:
                query += " AND e.event_tipi = ?"
                params.append(event_tipi)

            if durum:
                query += " AND e.event_durumu = ?"
                params.append(durum)

            query += " ORDER BY e.event_zamani DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Istatistikler
            cursor.execute("""
                SELECT
                    COUNT(*) AS toplam,
                    SUM(CASE WHEN event_durumu = 'BEKLIYOR' THEN 1 ELSE 0 END) AS bekleyen,
                    SUM(CASE WHEN event_tipi = 'LAB_ANALIZ_KRITIK' THEN 1 ELSE 0 END) AS kritik
                FROM uretim.lab_event_log
                WHERE event_zamani >= ? AND event_zamani < DATEADD(DAY, 1, ?)
            """, (tarih_bas, tarih_bit))
            stats = cursor.fetchone()

            # Istatistikleri guncelle
            if stats:
                self._kpi_toplam.findChild(QLabel, "stat_value").setText(str(stats[0] or 0))
                self._kpi_bekleyen.findChild(QLabel, "stat_value").setText(str(stats[1] or 0))
                self._kpi_kritik.findChild(QLabel, "stat_value").setText(str(stats[2] or 0))

            # Tabloyu doldur
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # ID
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))

                # Banyo
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))

                # Event Tipi
                event_text = row[2] or ''
                event_item = QTableWidgetItem(event_text.replace('LAB_ANALIZ_', ''))
                if 'KRITIK' in event_text:
                    event_item.setForeground(QColor(brand.ERROR))
                elif 'UYARI' in event_text:
                    event_item.setForeground(QColor(brand.WARNING))
                self.table.setItem(i, 2, event_item)

                # Sicaklik
                sic_item = QTableWidgetItem(f"{row[3]:.1f} C" if row[3] else "-")
                self.table.setItem(i, 3, sic_item)

                # pH
                ph_item = QTableWidgetItem(f"{row[4]:.2f}" if row[4] else "-")
                self.table.setItem(i, 4, ph_item)

                # Analist
                self.table.setItem(i, 5, QTableWidgetItem(row[5] or "-"))

                # Zaman
                zaman_str = row[6].strftime('%d.%m.%Y %H:%M') if row[6] else ''
                self.table.setItem(i, 6, QTableWidgetItem(zaman_str))

                # Durum
                durum_text = row[7] or ''
                durum_item = QTableWidgetItem(durum_text)
                if durum_text == 'BEKLIYOR':
                    durum_item.setForeground(QColor(brand.WARNING))
                    durum_item.setText("Bekliyor")
                elif durum_text == 'OKUNDU':
                    durum_item.setForeground(QColor(brand.SUCCESS))
                    durum_item.setText("Okundu")
                self.table.setItem(i, 7, durum_item)

                # Islem butonu
                if durum_text == 'BEKLIYOR':
                    widget = self.create_action_buttons([
                        ("Okundu", "Okundu Isaretle", lambda _, eid=row[0]: self._mark_read(eid), "success"),
                    ])
                    self.table.setCellWidget(i, 8, widget)

            # Footer guncelle
            self.footer_label.setText(
                f"Toplam {len(rows)} kayit | Son guncelleme: {datetime.now().strftime('%H:%M:%S')}"
            )

        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yukleme hatasi:\n{str(e)}")
            print(f"Lab event log yukleme hatasi: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # -----------------------------------------------------------------
    def _mark_read(self, event_id: int):
        """Event'i okundu olarak isaretle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE uretim.lab_event_log
                SET event_durumu = 'OKUNDU',
                    okundu_mu = 1,
                    okunma_zamani = GETDATE()
                WHERE id = ?
            """, (event_id,))
            conn.commit()

            self._load_data()  # Yenile

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Isaretleme hatasi:\n{str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
