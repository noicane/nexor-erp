# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kalite Raporu
Referans bazli kalite analizi: kontrol adetleri, hata turleri dagilimi.
Ust panel: referans (urun) bazli ozet, alt panel: secilen referansin hata kirilimi.
Musteri / Hat tiklanabilir filtre.
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDateEdit, QAbstractItemView, QGraphicsDropShadowEffect,
    QSplitter, QWidget, QLineEdit
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class RaporKalitePage(BasePage):
    """Kalite Raporu - Referans bazli kontrol ozeti + hata turu analizi"""

    FILTER_COLS = {2: "Musteri", 3: "Hat"}  # tiklanabilir kolonlar

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._detail_cache = {}  # stok_kodu -> [(tarih, lot, kaynak, kontrol, saglam, hatali, sonuc)]
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
        tr.addWidget(QLabel("🔬", styleSheet="font-size: 28px;"))
        tr.addWidget(QLabel("Kalite Raporu", styleSheet=f"color: {brand.TEXT}; font-size: 24px; font-weight: 600;"))
        tr.addStretch()
        ts.addLayout(tr)
        ts.addWidget(QLabel("Referans bazli kalite kontrol analizi ve hata turu dagilimi",
                            styleSheet=f"color: {brand.TEXT_MUTED}; font-size: 13px;"))
        header.addLayout(ts); header.addStretch()

        stats = QHBoxLayout(); stats.setSpacing(12)
        self.kontrol_card = self._make_stat("Kontrol", "0", brand.INFO)
        self.saglam_card = self._make_stat("Saglam", "0", brand.SUCCESS)
        self.hatali_card = self._make_stat("Hatali", "0", brand.ERROR)
        self.oran_card = self._make_stat("Red %", "0", brand.WARNING)
        for c in (self.kontrol_card, self.saglam_card, self.hatali_card, self.oran_card):
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

        btn_gunluk = QPushButton("Gunluk")
        btn_gunluk.setStyleSheet(f"""QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT};
            border: 1px solid {brand.BORDER}; border-radius: 8px; padding: 8px 16px;
            font-size: 13px; font-weight: 500; }}
            QPushButton:hover {{ border-color: {brand.PRIMARY}; }}""")
        btn_gunluk.clicked.connect(self._set_gunluk)
        fl.addWidget(btn_gunluk)

        fl.addWidget(QLabel("Baslangic:", styleSheet=ls))
        self.tarih_bas = QDateEdit()
        self.tarih_bas.setCalendarPopup(True); self.tarih_bas.setDisplayFormat("dd.MM.yyyy")
        self.tarih_bas.setDate(QDate.currentDate().addDays(-30)); self.tarih_bas.setStyleSheet(ds)
        fl.addWidget(self.tarih_bas)

        fl.addWidget(QLabel("Bitis:", styleSheet=ls))
        self.tarih_bit = QDateEdit()
        self.tarih_bit.setCalendarPopup(True); self.tarih_bit.setDisplayFormat("dd.MM.yyyy")
        self.tarih_bit.setDate(QDate.currentDate()); self.tarih_bit.setStyleSheet(ds)
        fl.addWidget(self.tarih_bit)

        fl.addWidget(QLabel("Kaynak:", styleSheet=ls))
        self.kaynak_combo = QComboBox()
        self.kaynak_combo.addItem("Tumu", "TUMU")
        self.kaynak_combo.addItem("Final Kontrol", "FINAL")
        self.kaynak_combo.addItem("Proses Kontrol", "PROSES")
        self.kaynak_combo.setStyleSheet(cs)
        fl.addWidget(self.kaynak_combo)

        fl.addWidget(QLabel("Hat Tipi:", styleSheet=ls))
        self.hat_tipi_combo = QComboBox()
        self.hat_tipi_combo.addItem("Tum Tipler", None)
        self.hat_tipi_combo.setStyleSheet(cs)
        fl.addWidget(self.hat_tipi_combo)

        fl.addWidget(QLabel("Kaplama:", styleSheet=ls))
        self.kaplama_combo = QComboBox()
        self.kaplama_combo.addItem("Tum Kaplamalar", None)
        self.kaplama_combo.setStyleSheet(cs)
        fl.addWidget(self.kaplama_combo)

        fl.addWidget(QLabel("Hat:", styleSheet=ls))
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("Tum Hatlar", None)
        self.hat_combo.setStyleSheet(cs)
        fl.addWidget(self.hat_combo)

        fl.addStretch()
        btn = QPushButton("Rapor Olustur")
        btn.setStyleSheet(f"""QPushButton {{ background: {brand.PRIMARY}; color: white; border: none;
            border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}""")
        btn.clicked.connect(self._load_data)
        fl.addWidget(btn)
        fl.addWidget(self.create_export_button(
            title="Kalite Raporu",
            table_provider=lambda: self.ref_table
        ))
        layout.addWidget(ff)

        # -- AKTIF FILTRE CUBUGU --
        self.filter_bar = QFrame()
        self.filter_bar.setStyleSheet(f"QFrame {{ background: {brand.PRIMARY_SOFT}; border: 1px solid {brand.PRIMARY}; border-radius: 8px; }}")
        fbl = QHBoxLayout(self.filter_bar); fbl.setContentsMargins(12, 6, 12, 6); fbl.setSpacing(8)
        self.filter_label = QLabel(""); self.filter_label.setStyleSheet(f"color: {brand.TEXT}; font-size: 13px; font-weight: 500;")
        fbl.addWidget(self.filter_label); fbl.addStretch()
        clr_btn = QPushButton("Filtreyi Temizle")
        clr_btn.setStyleSheet(f"""QPushButton {{ background: {brand.ERROR}; color: white; border: none;
            border-radius: 6px; padding: 4px 14px; font-size: 12px; font-weight: 600; }}""")
        clr_btn.setCursor(Qt.PointingHandCursor); clr_btn.clicked.connect(self._clear_filter)
        fbl.addWidget(clr_btn)
        self.filter_bar.setVisible(False)
        layout.addWidget(self.filter_bar)

        # -- SPLITTER --
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {brand.BORDER}; height: 3px; }}")

        # UST: Referans bazli + suzgec
        top_w = QWidget()
        top_l = QVBoxLayout(top_w); top_l.setContentsMargins(0, 0, 0, 0); top_l.setSpacing(0)

        ref_bar = QFrame()
        ref_bar.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 10px 10px 0 0; }}")
        rbl = QHBoxLayout(ref_bar); rbl.setContentsMargins(12, 8, 12, 8); rbl.setSpacing(8)
        rbl.addWidget(QLabel("🔍", styleSheet="font-size: 14px;"))
        self.ref_search = QLineEdit()
        self.ref_search.setPlaceholderText("Stok kodu, urun adi ile filtrele...")
        self.ref_search.setStyleSheet(f"""QLineEdit {{ background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER};
            border-radius: 6px; padding: 6px 10px; color: {brand.TEXT}; font-size: 13px; }}
            QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}""")
        self.ref_search.textChanged.connect(self._filter_refs)
        rbl.addWidget(self.ref_search, 1)
        self.ref_count = QLabel(""); self.ref_count.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px;")
        rbl.addWidget(self.ref_count)
        top_l.addWidget(ref_bar)

        self.ref_table = self._make_table(
            ["Stok Kodu", "Urun Adi", "Musteri", "Hat",
             "Kontrol", "Saglam", "Hatali", "Red %"],
            [110, 220, 160, 120, 100, 100, 100, 80],
            stretch_col=1
        )
        self.ref_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ref_table.currentCellChanged.connect(self._on_ref_selected)
        self.ref_table.cellClicked.connect(self._on_cell_clicked)
        top_l.addWidget(self.ref_table)
        splitter.addWidget(top_w)

        # ALT: Hata turu detay
        bot = QWidget()
        bl = QVBoxLayout(bot); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(0)
        self.detail_header = QLabel("  Yukaridaki listeden bir referans secin")
        self.detail_header.setFixedHeight(32)
        self.detail_header.setStyleSheet(f"background: rgba(0,0,0,0.2); color: {brand.TEXT_DIM}; padding: 6px 12px; font-size: 12px; font-style: italic;")
        bl.addWidget(self.detail_header)

        self.hata_table = self._make_table(
            ["Tarih", "Lot No", "Kontrol", "Saglam", "Hatali", "Sonuc", "Hata Turu"],
            [100, 160, 90, 90, 90, 90, 200],
            stretch_col=6
        )
        bl.addWidget(self.hata_table)
        splitter.addWidget(bot)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

        QTimer.singleShot(100, self._load_hat_filter)
        QTimer.singleShot(100, self._load_hat_tipi_filter)
        QTimer.singleShot(100, self._load_kaplama_filter)

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
        v = QLabel(value, styleSheet=f"color: {color}; font-size: 20px; font-weight: bold;"); v.setObjectName("stat_value")
        vl.addWidget(v)
        return f

    def _set_stat(self, card, value):
        lbl = card.findChild(QLabel, "stat_value")
        if lbl: lbl.setText(value)

    def _load_hat_filter(self):
        conn = None
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT id, kod, ISNULL(kisa_ad, ad) FROM tanim.uretim_hatlari WHERE aktif_mi=1 ORDER BY sira_no")
            for r in cur.fetchall():
                self.hat_combo.addItem(f"{r[1]} - {r[2]}", r[0])
        except Exception: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_hat_tipi_filter(self):
        conn = None
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT DISTINCT hat_tipi FROM tanim.uretim_hatlari "
                        "WHERE aktif_mi=1 AND hat_tipi IS NOT NULL ORDER BY hat_tipi")
            for r in cur.fetchall():
                self.hat_tipi_combo.addItem(str(r[0]), r[0])
        except Exception: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_kaplama_filter(self):
        conn = None
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT id, kod, ad FROM tanim.kaplama_turleri ORDER BY kod")
            for r in cur.fetchall():
                self.kaplama_combo.addItem(f"{r[1]} - {r[2]}", r[0])
        except Exception: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _set_gunluk(self):
        """Tarihi bugune set et ve rapor olustur"""
        today = QDate.currentDate()
        self.tarih_bas.setDate(today)
        self.tarih_bit.setDate(today)
        self._load_data()

    # =================================================================
    # SUZGEC + TIKLANABILIR FILTRE
    # =================================================================
    def _filter_refs(self, text):
        text = text.strip().lower()
        visible = 0
        for row in range(self.ref_table.rowCount()):
            match = True
            if text:
                match = False
                for col in range(3):  # stok kodu + urun adi + lot
                    item = self.ref_table.item(row, col)
                    if item and text in item.text().lower():
                        match = True; break
            self.ref_table.setRowHidden(row, not match)
            if match: visible += 1
        total = self.ref_table.rowCount()
        self.ref_count.setText(f"{visible}/{total}" if text else f"{total} referans")

    def _on_cell_clicked(self, row, col):
        if col in self.FILTER_COLS:
            item = self.ref_table.item(row, col)
            if item and item.text() and item.text() != "TOPLAM":
                self._apply_col_filter(self.FILTER_COLS[col], item.text())

    def _apply_col_filter(self, col_name, value):
        self._active_filter = (col_name, value)
        self.filter_label.setText(f"Filtre: {col_name} = {value}")
        self.filter_bar.setVisible(True)
        col_idx = {v: k for k, v in self.FILTER_COLS.items()}.get(col_name)
        if col_idx is not None:
            for r in range(self.ref_table.rowCount()):
                item = self.ref_table.item(r, col_idx)
                txt = item.text() if item else ""
                first = self.ref_table.item(r, 0)
                is_toplam = first and first.text() == "TOPLAM"
                self.ref_table.setRowHidden(r, txt != value and not is_toplam)

    def _clear_filter(self):
        self._active_filter = None
        self.filter_bar.setVisible(False)
        for r in range(self.ref_table.rowCount()):
            self.ref_table.setRowHidden(r, False)

    # =================================================================
    # REFERANS SECIMI -> HATA DETAY
    # =================================================================
    def _on_ref_selected(self, row, col, prev_row, prev_col):
        if row < 0:
            return
        item = self.ref_table.item(row, 0)
        if not item or item.text() == "TOPLAM":
            return
        stok_kodu = item.text()
        urun_item = self.ref_table.item(row, 1)
        urun_adi = urun_item.text() if urun_item else ""

        detaylar = self._detail_cache.get(stok_kodu, [])
        toplam_hatali = sum(d[4] for d in detaylar)

        self.detail_header.setText(
            f"  {stok_kodu} - {urun_adi}  ({len(detaylar)} kontrol, {toplam_hatali:,.0f} hatali)")
        self.detail_header.setStyleSheet(
            f"background: {brand.PRIMARY_SOFT}; color: {brand.TEXT}; "
            f"padding: 6px 12px; font-size: 12px; font-weight: 600;")

        sonuc_colors = {"ONAY": brand.SUCCESS, "RED": brand.ERROR, "KISMI": brand.WARNING}

        self.hata_table.setRowCount(len(detaylar))
        for i, (tarih, lot, kontrol, saglam, hatali, sonuc, hata_turu) in enumerate(detaylar):
            self.hata_table.setItem(i, 0, QTableWidgetItem(
                tarih.strftime("%d.%m.%Y") if tarih else ""))
            self.hata_table.setItem(i, 1, QTableWidgetItem(str(lot or '')))

            for c, val in [(2, kontrol), (3, saglam)]:
                it = QTableWidgetItem(f"{val:,.0f}" if val else "0")
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.hata_table.setItem(i, c, it)

            h_item = QTableWidgetItem(f"{hatali:,.0f}" if hatali else "0")
            h_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if hatali and hatali > 0:
                h_item.setForeground(QColor(brand.ERROR))
            self.hata_table.setItem(i, 4, h_item)

            s_item = QTableWidgetItem(str(sonuc or ''))
            s_item.setTextAlignment(Qt.AlignCenter)
            clr = sonuc_colors.get(sonuc)
            if clr:
                s_item.setForeground(QColor(clr))
            self.hata_table.setItem(i, 5, s_item)

            self.hata_table.setItem(i, 6, QTableWidgetItem(str(hata_turu or '')))
            self.hata_table.setRowHeight(i, 40)

    # =================================================================
    # DATA
    # =================================================================
    def _build_hat_kaplama_filters(self, fk_or_pk: str):
        """
        Hat/Hat Tipi/Kaplama filtrelerini build et.
        Returns (join_sql, where_extra_sql, params_in_sql_order).
        Params SQL'deki ? sirasiyla: join params -> (cagri yerinde date) -> where params.
        """
        hat_id = self.hat_combo.currentData()
        hat_tipi = self.hat_tipi_combo.currentData()
        kaplama_id = self.kaplama_combo.currentData()

        join_sql = ""
        join_params = []
        if hat_id or hat_tipi:
            join_sql += (f" JOIN uretim.uretim_kayitlari uk_h "
                         f"ON uk_h.is_emri_id = {fk_or_pk}.is_emri_id")
            if hat_id:
                join_sql += " AND uk_h.hat_id = ?"
                join_params.append(hat_id)
            if hat_tipi:
                join_sql += (" JOIN tanim.uretim_hatlari h_t "
                             "ON h_t.id = uk_h.hat_id AND h_t.hat_tipi = ?")
                join_params.append(hat_tipi)

        where_sql = ""
        where_params = []
        if kaplama_id:
            where_sql = " AND ie.kaplama_turu_id = ?"
            where_params.append(kaplama_id)

        return join_sql, where_sql, join_params, where_params

    def _load_data(self):
        tarih_bas = self.tarih_bas.date().toPython()
        tarih_bit = self.tarih_bit.date().toPython()
        kaynak = self.kaynak_combo.currentData()

        self.hata_table.setRowCount(0)
        self.ref_search.clear()
        self._clear_filter()
        self._detail_cache = {}
        self.detail_header.setText("  Yukaridaki listeden bir referans secin")
        self.detail_header.setStyleSheet(f"background: rgba(0,0,0,0.2); color: {brand.TEXT_DIM}; padding: 6px 12px; font-size: 12px; font-style: italic;")

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # =====================================================
            # REFERANS BAZLI OZET
            # =====================================================
            ref_data = {}  # stok_kodu -> {adi, lot, musteri, hat, kontrol, saglam, hatali}

            if kaynak in ("TUMU", "FINAL"):
                hat_j, kap_w, jp, wp = self._build_hat_kaplama_filters('fk')
                params = jp + [tarih_bas, tarih_bit] + wp
                cur.execute(f"""
                    SELECT
                        ISNULL(ie.stok_kodu, '-'),
                        ISNULL(ie.stok_adi, '-'),
                        ISNULL(ie.cari_unvani, '-'),
                        ISNULL((SELECT TOP 1 h.kod + ' - ' + ISNULL(h.kisa_ad, h.ad)
                                FROM uretim.uretim_kayitlari uk2
                                JOIN tanim.uretim_hatlari h ON uk2.hat_id = h.id
                                WHERE uk2.is_emri_id = ie.id), '-') AS hat,
                        SUM(ISNULL(fk.kontrol_miktar, 0)),
                        SUM(ISNULL(fk.saglam_adet, 0)),
                        SUM(ISNULL(fk.hatali_adet, 0))
                    FROM kalite.final_kontrol fk
                    JOIN siparis.is_emirleri ie ON fk.is_emri_id = ie.id
                    {hat_j}
                    WHERE fk.kontrol_tarihi BETWEEN ? AND DATEADD(day, 1, ?)
                    {kap_w}
                    GROUP BY ie.stok_kodu, ie.stok_adi, ie.cari_unvani, ie.id
                """, params)
                for r in cur.fetchall():
                    key = r[0] or '-'
                    d = ref_data.setdefault(key, {'adi': r[1], 'musteri': r[2], 'hat': r[3],
                                                   'kontrol': 0, 'saglam': 0, 'hatali': 0})
                    d['kontrol'] += (r[4] or 0)
                    d['saglam'] += (r[5] or 0)
                    d['hatali'] += (r[6] or 0)

            if kaynak in ("TUMU", "PROSES"):
                hat_j, kap_w, jp, wp = self._build_hat_kaplama_filters('pk')
                params = jp + [tarih_bas, tarih_bit] + wp
                cur.execute(f"""
                    SELECT
                        ISNULL(ie.stok_kodu, '-'),
                        ISNULL(ie.stok_adi, '-'),
                        ISNULL(ie.cari_unvani, '-'),
                        ISNULL((SELECT TOP 1 h.kod + ' - ' + ISNULL(h.kisa_ad, h.ad)
                                FROM uretim.uretim_kayitlari uk2
                                JOIN tanim.uretim_hatlari h ON uk2.hat_id = h.id
                                WHERE uk2.is_emri_id = ie.id), '-') AS hat,
                        SUM(ISNULL(pk.toplam_adet, 0)),
                        SUM(ISNULL(pk.saglam_adet, 0)),
                        SUM(ISNULL(pk.hatali_adet, 0))
                    FROM kalite.proses_kontrol pk
                    JOIN siparis.is_emirleri ie ON pk.is_emri_id = ie.id
                    {hat_j}
                    WHERE pk.kontrol_tarihi BETWEEN ? AND DATEADD(day, 1, ?)
                    {kap_w}
                    GROUP BY ie.stok_kodu, ie.stok_adi, ie.cari_unvani, ie.id
                """, params)
                for r in cur.fetchall():
                    key = r[0] or '-'
                    d = ref_data.setdefault(key, {'adi': r[1], 'musteri': r[2], 'hat': r[3],
                                                   'kontrol': 0, 'saglam': 0, 'hatali': 0})
                    d['kontrol'] += (r[4] or 0)
                    d['saglam'] += (r[5] or 0)
                    d['hatali'] += (r[6] or 0)

            # Stat cards
            t_k = sum(d['kontrol'] for d in ref_data.values())
            t_s = sum(d['saglam'] for d in ref_data.values())
            t_h = sum(d['hatali'] for d in ref_data.values())
            t_oran = (t_h / t_k * 100) if t_k > 0 else 0
            self._set_stat(self.kontrol_card, f"{t_k:,.0f}")
            self._set_stat(self.saglam_card, f"{t_s:,.0f}")
            self._set_stat(self.hatali_card, f"{t_h:,.0f}")
            self._set_stat(self.oran_card, f"{t_oran:.1f}%")

            # Referans tablosu
            ref_list = sorted(ref_data.items(), key=lambda x: x[1]['hatali'], reverse=True)
            row_count = len(ref_list) + (1 if ref_list else 0)
            self.ref_table.setRowCount(row_count)

            for i, (kod, d) in enumerate(ref_list):
                self.ref_table.setItem(i, 0, QTableWidgetItem(str(kod)))
                self.ref_table.setItem(i, 1, QTableWidgetItem(str(d['adi'])))

                m_item = QTableWidgetItem(str(d['musteri']))
                m_item.setForeground(QColor(brand.INFO))
                self.ref_table.setItem(i, 2, m_item)

                h_item = QTableWidgetItem(str(d['hat']))
                h_item.setForeground(QColor(brand.INFO))
                self.ref_table.setItem(i, 3, h_item)

                for col, val in [(4, d['kontrol']), (5, d['saglam'])]:
                    item = QTableWidgetItem(f"{val:,.0f}")
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.ref_table.setItem(i, col, item)

                hatali_item = QTableWidgetItem(f"{d['hatali']:,.0f}")
                hatali_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if d['hatali'] > 0:
                    hatali_item.setForeground(QColor(brand.ERROR))
                self.ref_table.setItem(i, 6, hatali_item)

                oran = (d['hatali'] / d['kontrol'] * 100) if d['kontrol'] > 0 else 0
                o_item = QTableWidgetItem(f"{oran:.1f}%")
                o_item.setTextAlignment(Qt.AlignCenter)
                if oran > 5:
                    o_item.setForeground(QColor(brand.ERROR))
                elif oran > 2:
                    o_item.setForeground(QColor(brand.WARNING))
                self.ref_table.setItem(i, 7, o_item)
                self.ref_table.setRowHeight(i, 42)

            # Toplam
            if ref_list:
                tr = len(ref_list)
                tl = QTableWidgetItem("TOPLAM"); tl.setForeground(QColor(brand.PRIMARY))
                self.ref_table.setItem(tr, 0, tl)
                for c in range(1, 4):
                    self.ref_table.setItem(tr, c, QTableWidgetItem(""))
                for col, val, clr in [(4, t_k, brand.PRIMARY), (5, t_s, brand.SUCCESS), (6, t_h, brand.ERROR)]:
                    item = QTableWidgetItem(f"{val:,.0f}")
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setForeground(QColor(clr))
                    self.ref_table.setItem(tr, col, item)
                ot = QTableWidgetItem(f"{t_oran:.1f}%"); ot.setTextAlignment(Qt.AlignCenter)
                ot.setForeground(QColor(brand.WARNING))
                self.ref_table.setItem(tr, 7, ot)
                self.ref_table.setRowHeight(tr, 42)

            self.ref_count.setText(f"{len(ref_list)} referans")

            # =====================================================
            # DETAY CACHE: final_kontrol + uretim_redler hata turu
            # =====================================================
            if kaynak in ("TUMU", "FINAL"):
                hat_j, kap_w, jp, wp = self._build_hat_kaplama_filters('fk')
                params = jp + [tarih_bas, tarih_bit] + wp
                cur.execute(f"""
                    SELECT
                        ISNULL(ie.stok_kodu, '-'),
                        CAST(fk.kontrol_tarihi AS DATE),
                        fk.lot_no,
                        fk.kontrol_miktar,
                        fk.saglam_adet,
                        fk.hatali_adet,
                        fk.sonuc,
                        (SELECT TOP 1 ht.kod + ' - ' + ht.ad
                         FROM kalite.uretim_redler ur
                         LEFT JOIN tanim.hata_turleri ht ON ur.hata_turu_id = ht.id
                         WHERE ur.kontrol_id = fk.id) AS hata_turu
                    FROM kalite.final_kontrol fk
                    JOIN siparis.is_emirleri ie ON fk.is_emri_id = ie.id
                    {hat_j}
                    WHERE fk.kontrol_tarihi BETWEEN ? AND DATEADD(day, 1, ?)
                      AND fk.hatali_adet > 0
                      {kap_w}
                    ORDER BY fk.kontrol_tarihi DESC
                """, params)
                for r in cur.fetchall():
                    self._detail_cache.setdefault(r[0] or '-', []).append(
                        (r[1], r[2], r[3] or 0, r[4] or 0, r[5] or 0, r[6], r[7]))

            if kaynak in ("TUMU", "PROSES"):
                hat_j, kap_w, jp, wp = self._build_hat_kaplama_filters('pk')
                params = jp + [tarih_bas, tarih_bit] + wp
                cur.execute(f"""
                    SELECT
                        ISNULL(ie.stok_kodu, '-'),
                        CAST(pk.kontrol_tarihi AS DATE),
                        pk.lot_no,
                        pk.toplam_adet,
                        pk.saglam_adet,
                        pk.hatali_adet,
                        pk.durum,
                        NULL AS hata_turu
                    FROM kalite.proses_kontrol pk
                    JOIN siparis.is_emirleri ie ON pk.is_emri_id = ie.id
                    {hat_j}
                    WHERE pk.kontrol_tarihi BETWEEN ? AND DATEADD(day, 1, ?)
                      AND pk.hatali_adet > 0
                      {kap_w}
                    ORDER BY pk.kontrol_tarihi DESC
                """, params)
                for r in cur.fetchall():
                    self._detail_cache.setdefault(r[0] or '-', []).append(
                        (r[1], r[2], r[3] or 0, r[4] or 0, r[5] or 0, r[6], r[7]))

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Hata", f"Veri yuklenirken hata olustu:\n{e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
