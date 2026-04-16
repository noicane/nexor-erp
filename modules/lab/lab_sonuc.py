# -*- coding: utf-8 -*-
"""
NEXOR ERP - Analiz Sonuclari Ozet
Banyo analiz sonuclarinin ozet gorunumu
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class LabSonucPage(BasePage):
    """Analiz Sonuclari Ozet Sayfasi"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # ── 1. Header ──
        header = self.create_page_header(
            "Analiz Sonuclari Ozet",
            "Banyolarin son analiz durumlarini takip edin"
        )
        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        header.addWidget(btn_yenile)
        layout.addLayout(header)

        # ── 2. KPI cards ──
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self.toplam_card = self.create_stat_card("TOPLAM BANYO", "0", color=brand.INFO)
        kpi_row.addWidget(self.toplam_card)
        self.normal_card = self.create_stat_card("NORMAL", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self.normal_card)
        self.uyari_card = self.create_stat_card("UYARI", "0", color=brand.WARNING)
        kpi_row.addWidget(self.uyari_card)
        self.kritik_card = self.create_stat_card("KRITIK", "0", color=brand.ERROR)
        kpi_row.addWidget(self.kritik_card)

        layout.addLayout(kpi_row)

        # ── 3. Filtre ──
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(brand.SP_3)

        input_css = f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """

        lbl_hat = QLabel("Hat:")
        lbl_hat.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        filter_layout.addWidget(lbl_hat)

        self.hat_combo = QComboBox()
        self.hat_combo.addItem("Tum Hatlar", None)
        self._load_hat_filter()
        self.hat_combo.setStyleSheet(input_css)
        self.hat_combo.setMinimumWidth(brand.sp(150))
        self.hat_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.hat_combo)

        lbl_durum = QLabel("Durum:")
        lbl_durum.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        filter_layout.addWidget(lbl_durum)

        self.durum_combo = QComboBox()
        self.durum_combo.addItem("Tum Durumlar", None)
        self.durum_combo.addItem("Normal", "NORMAL")
        self.durum_combo.addItem("Uyari", "UYARI")
        self.durum_combo.addItem("Kritik", "KRITIK")
        self.durum_combo.setStyleSheet(input_css)
        self.durum_combo.setMinimumWidth(brand.sp(120))
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.durum_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # ── 4. Tablo ──
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Banyo", "Hat", "Son Analiz", "Sicaklik", "Hedef", "pH", "Hedef", "Durum"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setColumnWidth(1, brand.sp(80))
        self.table.setColumnWidth(2, brand.sp(130))
        self.table.setColumnWidth(3, brand.sp(80))
        self.table.setColumnWidth(4, brand.sp(70))
        self.table.setColumnWidth(5, brand.sp(70))
        self.table.setColumnWidth(6, brand.sp(70))
        self.table.setColumnWidth(7, brand.sp(90))
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
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

    # -----------------------------------------------------------------
    def _load_hat_filter(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, kod FROM tanim.uretim_hatlari "
                "WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no"
            )
            for row in cursor.fetchall():
                self.hat_combo.addItem(row[1], row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # -----------------------------------------------------------------
    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Son analiz sonuclarini al
            sql = """
                WITH SonAnalizler AS (
                    SELECT banyo_id, MAX(tarih) as son_tarih
                    FROM uretim.banyo_analiz_sonuclari
                    GROUP BY banyo_id
                )
                SELECT b.id, b.kod, b.ad, h.kod as hat_kod,
                       a.tarih, a.sicaklik, b.sicaklik_hedef, b.sicaklik_min, b.sicaklik_max,
                       a.ph, b.ph_hedef, b.ph_min, b.ph_max
                FROM uretim.banyo_tanimlari b
                JOIN tanim.uretim_hatlari h ON b.hat_id=h.id
                LEFT JOIN SonAnalizler sa ON b.id=sa.banyo_id
                LEFT JOIN uretim.banyo_analiz_sonuclari a
                    ON a.banyo_id=sa.banyo_id AND a.tarih=sa.son_tarih
                WHERE b.aktif_mi=1
            """
            params = []

            hat_id = self.hat_combo.currentData()
            if hat_id:
                sql += " AND b.hat_id=?"
                params.append(hat_id)

            sql += " ORDER BY h.sira_no, b.kod"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # Durum hesapla ve filtrele
            data = []
            normal_count = 0
            uyari_count = 0
            kritik_count = 0

            for row in rows:
                durum = "NORMAL"

                # Sicaklik kontrolu
                if row[5] and row[7] and row[8]:
                    if row[5] < row[7] or row[5] > row[8]:
                        durum = "KRITIK" if abs(row[5] - (row[6] or 0)) > 10 else "UYARI"

                # pH kontrolu
                if row[9] and row[11] and row[12]:
                    if row[9] < row[11] or row[9] > row[12]:
                        if durum != "KRITIK":
                            durum = "KRITIK" if abs(row[9] - (row[10] or 0)) > 1 else "UYARI"

                # Analiz yapilmamis
                if not row[4]:
                    durum = "UYARI"

                if durum == "NORMAL":
                    normal_count += 1
                elif durum == "UYARI":
                    uyari_count += 1
                else:
                    kritik_count += 1

                data.append((row, durum))

            # Durum filtresi
            durum_filter = self.durum_combo.currentData()
            if durum_filter:
                data = [(r, d) for r, d in data if d == durum_filter]

            # Ozet kartlari guncelle
            self.toplam_card.findChild(QLabel, "stat_value").setText(str(len(rows)))
            self.normal_card.findChild(QLabel, "stat_value").setText(str(normal_count))
            self.uyari_card.findChild(QLabel, "stat_value").setText(str(uyari_count))
            self.kritik_card.findChild(QLabel, "stat_value").setText(str(kritik_count))

            # Tabloyu doldur
            self.table.setRowCount(len(data))

            for i, (row, durum) in enumerate(data):
                # Banyo
                self.table.setItem(i, 0, QTableWidgetItem(f"{row[1]} - {row[2]}"))

                # Hat
                self.table.setItem(i, 1, QTableWidgetItem(row[3] or ''))

                # Son Analiz
                tarih = row[4].strftime("%d.%m.%Y %H:%M") if row[4] else "Analiz Yok"
                tarih_item = QTableWidgetItem(tarih)
                if not row[4]:
                    tarih_item.setForeground(QColor(brand.WARNING))
                self.table.setItem(i, 2, tarih_item)

                # Sicaklik
                sic_item = QTableWidgetItem(f"{row[5]:.1f} C" if row[5] else '-')
                if row[5] and row[7] and row[8]:
                    if row[5] < row[7] or row[5] > row[8]:
                        sic_item.setForeground(QColor(brand.ERROR))
                    else:
                        sic_item.setForeground(QColor(brand.SUCCESS))
                self.table.setItem(i, 3, sic_item)

                # Sicaklik Hedef
                self.table.setItem(i, 4, QTableWidgetItem(f"{row[6]:.0f} C" if row[6] else '-'))

                # pH
                ph_item = QTableWidgetItem(f"{row[9]:.2f}" if row[9] else '-')
                if row[9] and row[11] and row[12]:
                    if row[9] < row[11] or row[9] > row[12]:
                        ph_item.setForeground(QColor(brand.ERROR))
                    else:
                        ph_item.setForeground(QColor(brand.SUCCESS))
                self.table.setItem(i, 5, ph_item)

                # pH Hedef
                self.table.setItem(i, 6, QTableWidgetItem(f"{row[10]:.1f}" if row[10] else '-'))

                # Durum
                durum_map = {"NORMAL": "Normal", "UYARI": "Uyari", "KRITIK": "Kritik"}
                durum_colors = {
                    "NORMAL": QColor(brand.SUCCESS),
                    "UYARI": QColor(brand.WARNING),
                    "KRITIK": QColor(brand.ERROR),
                }
                durum_item = QTableWidgetItem(durum_map[durum])
                durum_item.setForeground(durum_colors[durum])
                self.table.setItem(i, 7, durum_item)

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
