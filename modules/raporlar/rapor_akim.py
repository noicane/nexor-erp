# -*- coding: utf-8 -*-
"""
NEXOR ERP - PLC Akim Raporu (Amper-saat)
Banyo bazli akim analizi: PLC tarihce verisinden A*h hesaplama.
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDateEdit, QAbstractItemView, QGraphicsDropShadowEffect,
    QSplitter, QWidget
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor
from collections import defaultdict

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class RaporAkimPage(BasePage):
    """PLC Akim Raporu - Banyo bazli amper-saat analizi"""

    FILTER_COLS = {1: "Hat"}

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._detail_cache = {}   # kazan_no -> [(tarih, akim, voltaj, sicaklik)]
        self._active_filter = None
        self._setup_ui()

    # =================================================================
    # UI
    # =================================================================
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # -- HEADER --
        header = QHBoxLayout()
        ts = QVBoxLayout(); ts.setSpacing(4)
        tr = QHBoxLayout()
        tr.addWidget(QLabel("⚡", styleSheet="font-size: 28px;"))
        tr.addWidget(QLabel("PLC Akim Raporu", styleSheet=f"color: {brand.TEXT}; font-size: 24px; font-weight: 600;"))
        tr.addStretch()
        ts.addLayout(tr)
        ts.addWidget(QLabel("Banyo bazli amper-saat analizi (PLC verisi)",
                            styleSheet=f"color: {brand.TEXT_MUTED}; font-size: 13px;"))
        header.addLayout(ts); header.addStretch()

        stats = QHBoxLayout(); stats.setSpacing(12)
        self.banyo_card = self._make_stat("Banyo Sayisi", "0", brand.INFO)
        self.ah_card = self._make_stat("Toplam A*h", "0", brand.PRIMARY)
        self.ort_card = self._make_stat("Ort Amper", "0", brand.SUCCESS)
        self.sure_card = self._make_stat("Calisma", "0h", brand.WARNING)
        for c in (self.banyo_card, self.ah_card, self.ort_card, self.sure_card):
            stats.addWidget(c)
        header.addLayout(stats)
        layout.addLayout(header)

        # -- FILTRE --
        ff = QFrame()
        ff.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 10px; }}")
        fl = QHBoxLayout(ff); fl.setContentsMargins(16, 12, 16, 12); fl.setSpacing(12)

        ls = f"color: {brand.TEXT_MUTED}; font-size: 13px; font-weight: 500;"
        ds = f"""QDateEdit {{ background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER};
            border-radius: 8px; padding: 8px 12px; color: {brand.TEXT}; font-size: 13px; }}
            QDateEdit:focus {{ border-color: {brand.PRIMARY}; }}"""
        cs = f"""QComboBox {{ background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER};
            border-radius: 8px; padding: 8px 12px; color: {brand.TEXT}; font-size: 13px; min-width: 140px; }}
            QComboBox:hover {{ border-color: {brand.BORDER_HARD}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER};
                color: {brand.TEXT}; selection-background-color: {brand.PRIMARY}; }}"""
        btn_s = f"""QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT};
            border: 1px solid {brand.BORDER}; border-radius: 8px; padding: 8px 16px;
            font-size: 13px; font-weight: 500; }}
            QPushButton:hover {{ border-color: {brand.PRIMARY}; }}"""

        btn_gunluk = QPushButton("Gunluk")
        btn_gunluk.setStyleSheet(btn_s)
        btn_gunluk.clicked.connect(self._set_gunluk)
        fl.addWidget(btn_gunluk)

        fl.addWidget(QLabel("Tarih:", styleSheet=ls))
        self.tarih = QDateEdit()
        self.tarih.setCalendarPopup(True); self.tarih.setDisplayFormat("dd.MM.yyyy")
        self.tarih.setDate(QDate.currentDate()); self.tarih.setStyleSheet(ds)
        fl.addWidget(self.tarih)

        fl.addWidget(QLabel("Hat:", styleSheet=ls))
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("Tum Hatlar", None)
        self.hat_combo.addItem("CINKO (ZN/ZNNI)", "CINKO")
        self.hat_combo.addItem("KTL", "KTL")
        self.hat_combo.addItem("ON ISLEM", "DIGER")
        self.hat_combo.setStyleSheet(cs)
        fl.addWidget(self.hat_combo)

        fl.addStretch()
        btn = QPushButton("Rapor Olustur")
        btn.setStyleSheet(f"""QPushButton {{ background: {brand.PRIMARY}; color: white; border: none;
            border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}""")
        btn.clicked.connect(self._load_data)
        fl.addWidget(btn)
        fl.addWidget(self.create_export_button(title="PLC Akim Raporu"))
        layout.addWidget(ff)

        # -- FILTRE BAR --
        self.filter_bar = QFrame()
        self.filter_bar.setStyleSheet(f"QFrame {{ background: {brand.PRIMARY_SOFT}; border: 1px solid {brand.PRIMARY}; border-radius: 8px; }}")
        fbl = QHBoxLayout(self.filter_bar); fbl.setContentsMargins(12, 6, 12, 6); fbl.setSpacing(8)
        self.filter_label = QLabel(""); self.filter_label.setStyleSheet(f"color: {brand.TEXT}; font-size: 13px; font-weight: 500;")
        fbl.addWidget(self.filter_label); fbl.addStretch()
        clr = QPushButton("Filtreyi Temizle")
        clr.setStyleSheet(f"QPushButton {{ background: {brand.ERROR}; color: white; border: none; border-radius: 6px; padding: 4px 14px; font-size: 12px; font-weight: 600; }}")
        clr.setCursor(Qt.PointingHandCursor); clr.clicked.connect(self._clear_filter)
        fbl.addWidget(clr)
        self.filter_bar.setVisible(False)
        layout.addWidget(self.filter_bar)

        # -- SPLITTER --
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {brand.BORDER}; height: 3px; }}")

        # UST: Banyo bazli ozet
        self.master_table = self._make_table(
            ["Kazan", "Hat", "Banyo Adi", "Gecis", "Ort Amper", "Max Amper",
             "Ort Volt", "A*h", "Calisma"],
            [70, 90, 200, 70, 100, 100, 90, 110, 90],
            stretch_col=2
        )
        self.master_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.master_table.currentCellChanged.connect(self._on_row_selected)
        self.master_table.cellClicked.connect(self._on_cell_clicked)
        splitter.addWidget(self.master_table)

        # ALT: Detay
        bot = QWidget()
        bl = QVBoxLayout(bot); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(0)
        self.detail_header = QLabel("  Yukaridaki listeden bir banyo secin")
        self.detail_header.setFixedHeight(32)
        self.detail_header.setStyleSheet(f"background: rgba(0,0,0,0.2); color: {brand.TEXT_DIM}; padding: 6px 12px; font-size: 12px; font-style: italic;")
        bl.addWidget(self.detail_header)

        self.detail_table = self._make_table(
            ["Saat", "Akim (A)", "Voltaj (V)", "Sicaklik (C)", "Recete", "Adim"],
            [140, 110, 110, 110, 80, 80],
            stretch_col=0
        )
        bl.addWidget(self.detail_table)
        splitter.addWidget(bot)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

    # =================================================================
    # HELPERS
    # =================================================================
    def _make_table(self, headers, widths, stretch_col=None):
        t = QTableWidget()
        t.setStyleSheet(f"""
            QTableWidget {{ background: {brand.BG_CARD}; border: none; gridline-color: {brand.BORDER}; color: {brand.TEXT}; }}
            QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {brand.BORDER}; }}
            QTableWidget::item:selected {{ background: {brand.PRIMARY}; }}
            QTableWidget::item:hover {{ background: rgba(220,38,38,0.08); }}
            QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {brand.TEXT_MUTED};
                padding: 10px 8px; border: none; border-bottom: 2px solid {brand.PRIMARY};
                font-weight: 600; font-size: 12px; }}
        """)
        t.setColumnCount(len(headers)); t.setHorizontalHeaderLabels(headers)
        for i, w in enumerate(widths):
            t.setColumnWidth(i, w)
        if stretch_col is not None:
            t.horizontalHeader().setSectionResizeMode(stretch_col, QHeaderView.Stretch)
        t.verticalHeader().setVisible(False)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setAlternatingRowColors(True)
        return t

    def _make_stat(self, title, value, color):
        f = QFrame(); f.setFixedSize(130, 70)
        f.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-left: 4px solid {color}; border-radius: 10px; }}")
        sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(10); sh.setXOffset(0); sh.setYOffset(2); sh.setColor(QColor(0,0,0,40))
        f.setGraphicsEffect(sh)
        vl = QVBoxLayout(f); vl.setContentsMargins(12, 8, 12, 8); vl.setSpacing(2)
        vl.addWidget(QLabel(title, styleSheet=f"color: {brand.TEXT_DIM}; font-size: 11px; font-weight: 500;"))
        v = QLabel(value, styleSheet=f"color: {color}; font-size: 20px; font-weight: bold;"); v.setObjectName("value_label")
        vl.addWidget(v)
        return f

    def _set_stat(self, card, value):
        lbl = card.findChild(QLabel, "value_label")
        if lbl: lbl.setText(value)

    def _set_gunluk(self):
        self.tarih.setDate(QDate.currentDate())
        self._load_data()

    # =================================================================
    # TIKLANABILIR FILTRE
    # =================================================================
    def _on_cell_clicked(self, row, col):
        if col in self.FILTER_COLS:
            item = self.master_table.item(row, col)
            if item and item.text() and item.text() != "TOPLAM":
                self._active_filter = (self.FILTER_COLS[col], item.text())
                self.filter_label.setText(f"Filtre: {self.FILTER_COLS[col]} = {item.text()}")
                self.filter_bar.setVisible(True)
                for r in range(self.master_table.rowCount()):
                    it = self.master_table.item(r, col)
                    txt = it.text() if it else ""
                    first = self.master_table.item(r, 0)
                    is_toplam = first and first.text() == "TOPLAM"
                    self.master_table.setRowHidden(r, txt != item.text() and not is_toplam)

    def _clear_filter(self):
        self._active_filter = None
        self.filter_bar.setVisible(False)
        for r in range(self.master_table.rowCount()):
            self.master_table.setRowHidden(r, False)

    # =================================================================
    # DETAY
    # =================================================================
    def _on_row_selected(self, row, col, prev_row, prev_col):
        if row < 0:
            return
        item = self.master_table.item(row, 0)
        if not item or item.text() == "TOPLAM":
            return
        kazan_no = item.data(Qt.UserRole)
        if not kazan_no:
            return

        banyo_item = self.master_table.item(row, 2)
        banyo_adi = banyo_item.text() if banyo_item else ""
        kayitlar = self._detail_cache.get(kazan_no, [])

        self.detail_header.setText(f"  K{kazan_no} - {banyo_adi}  ({len(kayitlar)} kayit)")
        self.detail_header.setStyleSheet(f"background: {brand.PRIMARY_SOFT}; color: {brand.TEXT}; padding: 6px 12px; font-size: 12px; font-weight: 600;")

        self.detail_table.setRowCount(len(kayitlar))
        for i, (tarih, akim, voltaj, sicaklik, recete, adim) in enumerate(kayitlar):
            self.detail_table.setItem(i, 0, QTableWidgetItem(
                tarih.strftime("%H:%M:%S") if tarih else ""))

            a_item = QTableWidgetItem(f"{akim:,.0f}")
            a_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            a_item.setForeground(QColor(brand.PRIMARY))
            self.detail_table.setItem(i, 1, a_item)

            v_item = QTableWidgetItem(f"{voltaj:,.0f}" if voltaj else "-")
            v_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.detail_table.setItem(i, 2, v_item)

            s_item = QTableWidgetItem(f"{sicaklik:.1f}" if sicaklik else "-")
            s_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.detail_table.setItem(i, 3, s_item)

            self.detail_table.setItem(i, 4, QTableWidgetItem(str(recete or '')))
            self.detail_table.setItem(i, 5, QTableWidgetItem(str(adim or '')))
            self.detail_table.setRowHeight(i, 38)

    # =================================================================
    # DATA
    # =================================================================
    def _load_data(self):
        tarih = self.tarih.date().toPython()
        hat_filtre = self.hat_combo.currentData()

        self.detail_table.setRowCount(0)
        self._clear_filter()
        self._detail_cache = {}
        self.detail_header.setText("  Yukaridaki listeden bir banyo secin")
        self.detail_header.setStyleSheet(f"background: rgba(0,0,0,0.2); color: {brand.TEXT_DIM}; padding: 6px 12px; font-size: 12px; font-style: italic;")

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Pozisyon isimleri: hat_pozisyonlar.pozisyon_no = kazan_no
            cur.execute('''
                SELECT hp.pozisyon_no, hp.ad, h.kod AS hat_kod
                FROM tanim.hat_pozisyonlar hp
                JOIN tanim.uretim_hatlari h ON hp.hat_id = h.id
                WHERE hp.aktif_mi = 1 AND (hp.silindi_mi = 0 OR hp.silindi_mi IS NULL)
            ''')
            pozisyon_isimleri = {r[0]: r[1] for r in cur.fetchall()}

            # Hat isimleri (PLC hat_kodu -> tanim adi)
            plc_hat_isimleri = {}
            cur.execute("SELECT kod, ISNULL(kisa_ad, ad) FROM tanim.uretim_hatlari")
            for r in cur.fetchall():
                plc_hat_isimleri[r[0]] = r[1]
            plc_to_hat = {"CINKO": "E-ZNNI", "KTL": "E-KTL", "DIGER": "E-ON"}

            # PLC tarihce - sadece akim > 0
            hat_where = ""
            if hat_filtre:
                hat_where = f" AND hat_kodu = '{hat_filtre}'"

            cur.execute(f'''
                SELECT kazan_no, hat_kodu, kayit_tarihi, akim, voltaj, sicaklik,
                       recete_no, recete_adim, tarih_doldurma
                FROM uretim.plc_tarihce
                WHERE akim IS NOT NULL AND akim > 0
                  AND CAST(kayit_tarihi AS DATE) = ?
                  {hat_where}
                ORDER BY hat_kodu, kazan_no, kayit_tarihi
            ''', (tarih,))
            rows = cur.fetchall()

            # Kazan bazli grupla
            kazan_data = defaultdict(list)
            kazan_gecis = defaultdict(set)
            for r in rows:
                kazan_data[(r[1], r[0])].append({
                    'tarih': r[2], 'akim': float(r[3]),
                    'voltaj': float(r[4]) if r[4] else None,
                    'sicaklik': float(r[5]) if r[5] else None,
                    'recete': r[6], 'adim': r[7]
                })
                if r[8]:
                    kazan_gecis[(r[1], r[0])].add(r[8])

            # Hesapla ve tabloya doldur
            master_rows = []
            for (hat, kazan), kayitlar in sorted(kazan_data.items()):
                # Duplicate temizle
                temiz = [kayitlar[0]]
                for k in kayitlar[1:]:
                    if k['tarih'] != temiz[-1]['tarih']:
                        temiz.append(k)

                # A*h hesabi (sadece akim > 0 olanlar)
                akimli = [k for k in temiz if k['akim'] > 0]
                ah = 0.0
                toplam_saat = 0.0
                if len(akimli) > 1:
                    for i in range(1, len(akimli)):
                        dt = (akimli[i]['tarih'] - akimli[i-1]['tarih']).total_seconds() / 3600
                        if dt > 2:
                            continue
                        ah += akimli[i]['akim'] * dt
                        toplam_saat += dt

                ort_akim = sum(k['akim'] for k in akimli) / len(akimli) if akimli else 0
                max_akim = max((k['akim'] for k in akimli), default=0)
                voltajlar = [k['voltaj'] for k in temiz if k['voltaj']]
                ort_volt = sum(voltajlar) / len(voltajlar) if voltajlar else 0

                gecis = len(kazan_gecis.get((hat, kazan), set()))
                banyo_adi = pozisyon_isimleri.get(kazan, f"Kazan {kazan}")

                master_rows.append({
                    'kazan': kazan, 'hat': hat, 'banyo': banyo_adi,
                    'gecis': gecis, 'ort_akim': ort_akim, 'max_akim': max_akim,
                    'ort_volt': ort_volt, 'ah': ah, 'saat': toplam_saat
                })

                # Detay cache
                self._detail_cache[kazan] = [
                    (k['tarih'], k['akim'], k['voltaj'], k['sicaklik'], k['recete'], k['adim'])
                    for k in temiz
                ]

            # Stat cards
            t_ah = sum(r['ah'] for r in master_rows)
            t_saat = sum(r['saat'] for r in master_rows)
            akimli = [r for r in master_rows if r['ah'] > 0]
            t_ort = sum(r['ort_akim'] for r in akimli) / len(akimli) if akimli else 0

            self._set_stat(self.banyo_card, str(len(master_rows)))
            self._set_stat(self.ah_card, f"{t_ah:,.0f}")
            self._set_stat(self.ort_card, f"{t_ort:,.0f}")
            self._set_stat(self.sure_card, f"{t_saat:.0f}h")

            # Tablo
            row_count = len(master_rows) + (1 if master_rows else 0)
            self.master_table.setRowCount(row_count)

            for i, r in enumerate(master_rows):
                k_item = QTableWidgetItem(f"K{r['kazan']}")
                k_item.setData(Qt.UserRole, r['kazan'])
                self.master_table.setItem(i, 0, k_item)

                hat_kod = plc_to_hat.get(r['hat'], r['hat'])
                hat_label = plc_hat_isimleri.get(hat_kod, r['hat'])
                h_item = QTableWidgetItem(hat_label)
                h_item.setForeground(QColor(brand.INFO))
                self.master_table.setItem(i, 1, h_item)

                self.master_table.setItem(i, 2, QTableWidgetItem(r['banyo']))

                gc = QTableWidgetItem(str(r['gecis']))
                gc.setTextAlignment(Qt.AlignCenter)
                self.master_table.setItem(i, 3, gc)

                for col, val in [(4, r['ort_akim']), (5, r['max_akim']), (6, r['ort_volt'])]:
                    item = QTableWidgetItem(f"{val:,.0f}")
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.master_table.setItem(i, col, item)

                ah_item = QTableWidgetItem(f"{r['ah']:,.0f}")
                ah_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                ah_item.setForeground(QColor(brand.PRIMARY))
                self.master_table.setItem(i, 7, ah_item)

                s_item = QTableWidgetItem(f"{r['saat']:.1f}h")
                s_item.setTextAlignment(Qt.AlignCenter)
                self.master_table.setItem(i, 8, s_item)

                self.master_table.setRowHeight(i, 42)

            # Toplam
            if master_rows:
                tr = len(master_rows)
                tl = QTableWidgetItem("TOPLAM"); tl.setForeground(QColor(brand.PRIMARY))
                self.master_table.setItem(tr, 0, tl)
                for c in range(1, 7):
                    self.master_table.setItem(tr, c, QTableWidgetItem(""))

                ah_t = QTableWidgetItem(f"{t_ah:,.0f}")
                ah_t.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                ah_t.setForeground(QColor(brand.PRIMARY))
                self.master_table.setItem(tr, 7, ah_t)

                s_t = QTableWidgetItem(f"{t_saat:.0f}h")
                s_t.setTextAlignment(Qt.AlignCenter)
                self.master_table.setItem(tr, 8, s_t)
                self.master_table.setRowHeight(tr, 42)

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Hata", f"Veri yuklenirken hata olustu:\n{e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
