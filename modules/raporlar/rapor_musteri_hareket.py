# -*- coding: utf-8 -*-
"""
NEXOR ERP - Musteri Giden/Gelen Hareket Raporu
Referans (urun) bazli gorunum: ust tabloda referanslar, alt tabloda
secilen referansin tum irsaliye hareketleri (giden/gelen/iade).
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDateEdit, QAbstractItemView, QGraphicsDropShadowEffect,
    QCompleter, QLineEdit, QSplitter, QWidget
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class RaporMusteriHareketPage(BasePage):
    """Musteri bazli referans-irsaliye hareket raporu"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._ref_rows = []      # [(stok_kodu, urun_adi, giden, gelen, iade), ...]
        self._hareket_cache = {} # stok_kodu -> [(tarih, irs_no, yon, miktar, durum), ...]
        self._setup_ui()
        QTimer.singleShot(100, self._load_cariler)

    # =================================================================
    # UI
    # =================================================================
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # -- HEADER --
        header = QHBoxLayout()
        title_sec = QVBoxLayout()
        title_sec.setSpacing(4)
        tr = QHBoxLayout()
        ic = QLabel("📊")
        ic.setStyleSheet("font-size: 28px;")
        tr.addWidget(ic)
        t = QLabel("Musteri Hareket Raporu")
        t.setStyleSheet(f"color: {brand.TEXT}; font-size: 24px; font-weight: 600;")
        tr.addWidget(t)
        tr.addStretch()
        title_sec.addLayout(tr)
        sub = QLabel("Referans sec, altinda tum giden/gelen/iade hareketlerini gor")
        sub.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: 13px;")
        title_sec.addWidget(sub)
        header.addLayout(title_sec)
        header.addStretch()

        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.giden_card = self._create_stat_card("Giden", "0", brand.PRIMARY)
        self.gelen_card = self._create_stat_card("Gelen", "0", brand.SUCCESS)
        self.iade_card = self._create_stat_card("Iade", "0", brand.WARNING)
        self.net_card = self._create_stat_card("Net", "0", brand.INFO)
        for c in (self.giden_card, self.gelen_card, self.iade_card, self.net_card):
            stats.addWidget(c)
        header.addLayout(stats)
        layout.addLayout(header)

        # -- FILTRE --
        ff = QFrame()
        ff.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 10px; }}")
        fl = QHBoxLayout(ff)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(12)

        combo_style = f"""
            QComboBox {{
                background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER};
                border-radius: 8px; padding: 8px 12px; color: {brand.TEXT};
                font-size: 13px; min-width: 250px;
            }}
            QComboBox:hover {{ border-color: {brand.BORDER_HARD}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_CARD}; border: 1px solid {brand.BORDER};
                color: {brand.TEXT}; selection-background-color: {brand.PRIMARY};
            }}
        """
        date_style = f"""
            QDateEdit {{
                background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER};
                border-radius: 8px; padding: 8px 12px; color: {brand.TEXT}; font-size: 13px;
            }}
            QDateEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """
        lbl_style = f"color: {brand.TEXT_MUTED}; font-size: 13px; font-weight: 500;"

        fl.addWidget(QLabel("Musteri:", styleSheet=lbl_style))
        self.cari_combo = QComboBox()
        self.cari_combo.setEditable(True)
        self.cari_combo.setStyleSheet(combo_style)
        self.cari_combo.setInsertPolicy(QComboBox.NoInsert)
        self.cari_combo.lineEdit().setPlaceholderText("Musteri secin veya arayin...")
        fl.addWidget(self.cari_combo)

        fl.addWidget(QLabel("Baslangic:", styleSheet=lbl_style))
        self.tarih_bas = QDateEdit()
        self.tarih_bas.setCalendarPopup(True)
        self.tarih_bas.setDisplayFormat("dd.MM.yyyy")
        self.tarih_bas.setDate(QDate.currentDate().addMonths(-1))
        self.tarih_bas.setStyleSheet(date_style)
        fl.addWidget(self.tarih_bas)

        fl.addWidget(QLabel("Bitis:", styleSheet=lbl_style))
        self.tarih_bit = QDateEdit()
        self.tarih_bit.setCalendarPopup(True)
        self.tarih_bit.setDisplayFormat("dd.MM.yyyy")
        self.tarih_bit.setDate(QDate.currentDate())
        self.tarih_bit.setStyleSheet(date_style)
        fl.addWidget(self.tarih_bit)

        fl.addStretch()
        btn = QPushButton("Rapor Olustur")
        btn.setStyleSheet(f"""
            QPushButton {{ background: {brand.PRIMARY}; color: white; border: none;
                border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        btn.clicked.connect(self._load_data)
        fl.addWidget(btn)
        fl.addWidget(self.create_export_button(title="Musteri Hareket Raporu"))
        layout.addWidget(ff)

        # -- MASTER-DETAIL SPLITTER --
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {brand.BORDER}; height: 3px; }}")

        # UST: Referans tablosu + suzgec
        top_w = QWidget()
        top_l = QVBoxLayout(top_w)
        top_l.setContentsMargins(0, 0, 0, 0)
        top_l.setSpacing(0)

        # Referans suzgec
        ref_bar = QFrame()
        ref_bar.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 10px 10px 0 0; }}")
        rb_l = QHBoxLayout(ref_bar)
        rb_l.setContentsMargins(12, 8, 12, 8)
        rb_l.setSpacing(8)
        rb_l.addWidget(QLabel("🔍", styleSheet="font-size: 14px;"))
        self.ref_search = QLineEdit()
        self.ref_search.setPlaceholderText("Stok kodu veya urun adi ile filtrele...")
        self.ref_search.setStyleSheet(f"""
            QLineEdit {{ background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 6px 10px; color: {brand.TEXT}; font-size: 13px; }}
            QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.ref_search.textChanged.connect(self._filter_refs)
        rb_l.addWidget(self.ref_search, 1)
        self.ref_count = QLabel("")
        self.ref_count.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px;")
        rb_l.addWidget(self.ref_count)
        top_l.addWidget(ref_bar)

        self.ref_table = self._create_table(
            ["Stok Kodu", "Urun Adi", "Giden", "Gelen", "Iade", "Net"],
            [130, 260, 100, 100, 100, 100],
            stretch_col=1
        )
        self.ref_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ref_table.currentCellChanged.connect(self._on_ref_selected)
        top_l.addWidget(self.ref_table)
        splitter.addWidget(top_w)

        # ALT: Hareket detaylari
        bot_w = QWidget()
        bot_l = QVBoxLayout(bot_w)
        bot_l.setContentsMargins(0, 0, 0, 0)
        bot_l.setSpacing(0)

        self.detail_header = QLabel("  Yukaridaki listeden bir referans secin")
        self.detail_header.setFixedHeight(32)
        self.detail_header.setStyleSheet(f"""
            background: rgba(0,0,0,0.2); color: {brand.TEXT_DIM};
            padding: 6px 12px; font-size: 12px; font-style: italic;
        """)
        bot_l.addWidget(self.detail_header)

        self.hareket_table = self._create_table(
            ["Tarih", "Irsaliye No", "Yon", "Miktar", "Durum"],
            [110, 160, 100, 130, 130],
            stretch_col=1
        )
        bot_l.addWidget(self.hareket_table)
        splitter.addWidget(bot_w)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

    # =================================================================
    # HELPERS
    # =================================================================
    def _create_table(self, headers, widths, stretch_col=None):
        t = QTableWidget()
        t.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD}; border: none;
                gridline-color: {brand.BORDER}; color: {brand.TEXT};
            }}
            QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {brand.BORDER}; }}
            QTableWidget::item:selected {{ background: {brand.PRIMARY}; }}
            QTableWidget::item:hover {{ background: rgba(220,38,38,0.08); }}
            QHeaderView::section {{
                background: rgba(0,0,0,0.3); color: {brand.TEXT_MUTED};
                padding: 10px 8px; border: none; border-bottom: 2px solid {brand.PRIMARY};
                font-weight: 600; font-size: 12px;
            }}
        """)
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        for i, w in enumerate(widths):
            t.setColumnWidth(i, w)
        if stretch_col is not None:
            t.horizontalHeader().setSectionResizeMode(stretch_col, QHeaderView.Stretch)
        t.verticalHeader().setVisible(False)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setAlternatingRowColors(True)
        return t

    def _create_stat_card(self, title, value, color):
        f = QFrame()
        f.setFixedSize(130, 70)
        f.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-left: 4px solid {color}; border-radius: 10px; }}")
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(10); sh.setXOffset(0); sh.setYOffset(2); sh.setColor(QColor(0,0,0,40))
        f.setGraphicsEffect(sh)
        vl = QVBoxLayout(f)
        vl.setContentsMargins(12, 8, 12, 8); vl.setSpacing(2)
        vl.addWidget(QLabel(title, styleSheet=f"color: {brand.TEXT_DIM}; font-size: 11px; font-weight: 500;"))
        v = QLabel(value, styleSheet=f"color: {color}; font-size: 20px; font-weight: bold;")
        v.setObjectName("stat_value")
        vl.addWidget(v)
        return f

    def _update_stat(self, card, value):
        lbl = card.findChild(QLabel, "stat_value")
        if lbl:
            lbl.setText(value)

    def _on_completer_activated(self, text):
        for i in range(self.cari_combo.count()):
            if self.cari_combo.itemText(i) == text:
                self.cari_combo.setCurrentIndex(i)
                break

    # =================================================================
    # REFERANS SUZGEC
    # =================================================================
    def _filter_refs(self, text):
        text = text.strip().lower()
        visible = 0
        for row in range(self.ref_table.rowCount()):
            match = True
            if text:
                match = False
                for col in range(2):  # sadece stok kodu + urun adi
                    item = self.ref_table.item(row, col)
                    if item and text in item.text().lower():
                        match = True
                        break
            self.ref_table.setRowHidden(row, not match)
            if match:
                visible += 1
        total = self.ref_table.rowCount()
        self.ref_count.setText(f"{visible}/{total}" if text else f"{total} referans")

    # =================================================================
    # REFERANS SECIMI -> HAREKET DETAYI
    # =================================================================
    def _on_ref_selected(self, row, col, prev_row, prev_col):
        if row < 0:
            return
        item = self.ref_table.item(row, 0)
        if not item:
            return
        stok_kodu = item.text()
        urun_adi_item = self.ref_table.item(row, 1)
        urun_adi = urun_adi_item.text() if urun_adi_item else ""

        hareketler = self._hareket_cache.get(stok_kodu, [])

        self.detail_header.setText(f"  {stok_kodu} - {urun_adi}  ({len(hareketler)} hareket)")
        self.detail_header.setStyleSheet(f"""
            background: {brand.PRIMARY_SOFT}; color: {brand.TEXT};
            padding: 6px 12px; font-size: 12px; font-weight: 600;
        """)

        self.hareket_table.setRowCount(len(hareketler))
        yon_colors = {
            "GIDEN": brand.PRIMARY,
            "GELEN": brand.SUCCESS,
            "IADE": brand.WARNING,
        }
        for i, (tarih, irs_no, yon, miktar, durum) in enumerate(hareketler):
            self.hareket_table.setItem(i, 0, QTableWidgetItem(
                tarih.strftime("%d.%m.%Y") if tarih else ""
            ))
            self.hareket_table.setItem(i, 1, QTableWidgetItem(str(irs_no or '')))

            yon_item = QTableWidgetItem(yon)
            yon_item.setTextAlignment(Qt.AlignCenter)
            yon_item.setForeground(QColor(yon_colors.get(yon, brand.TEXT)))
            self.hareket_table.setItem(i, 2, yon_item)

            m_item = QTableWidgetItem(f"{miktar:,.0f}" if miktar else "0")
            m_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.hareket_table.setItem(i, 3, m_item)

            self.hareket_table.setItem(i, 4, QTableWidgetItem(str(durum or '')))
            self.hareket_table.setRowHeight(i, 40)

    # =================================================================
    # DATA
    # =================================================================
    def _load_cariler(self):
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            self.cari_combo.clear()
            self.cari_combo.addItem("-- Musteri Secin --", None)
            cur.execute("""
                SELECT id, cari_kodu, unvan FROM musteri.cariler
                WHERE aktif_mi = 1 AND (silindi_mi = 0 OR silindi_mi IS NULL)
                ORDER BY unvan
            """)
            for r in cur.fetchall():
                self.cari_combo.addItem(f"{r[1]} - {r[2]}", r[0])
            comp = QCompleter(
                [self.cari_combo.itemText(i) for i in range(self.cari_combo.count())], self
            )
            comp.setCaseSensitivity(Qt.CaseInsensitive)
            comp.setFilterMode(Qt.MatchContains)
            comp.activated.connect(self._on_completer_activated)
            self.cari_combo.setCompleter(comp)
        except Exception:
            pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _load_data(self):
        cari_id = self.cari_combo.currentData()
        cari_text = self.cari_combo.currentText()

        if not cari_id and cari_text:
            for i in range(self.cari_combo.count()):
                if self.cari_combo.itemText(i) == cari_text:
                    self.cari_combo.setCurrentIndex(i)
                    cari_id = self.cari_combo.itemData(i)
                    break
        if not cari_id:
            return

        tarih_bas = self.tarih_bas.date().toPython()
        tarih_bit = self.tarih_bit.date().toPython()
        cari_unvan = cari_text.split(" - ", 1)[1] if " - " in cari_text else cari_text

        self.ref_search.clear()
        self.hareket_table.setRowCount(0)
        self.detail_header.setText("  Yukaridaki listeden bir referans secin")
        self.detail_header.setStyleSheet(f"background: rgba(0,0,0,0.2); color: {brand.TEXT_DIM}; padding: 6px 12px; font-size: 12px; font-style: italic;")

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # -- Tum hareketleri tek seferde cek, referans bazli grupla --
            hareket_cache = {}  # stok_kodu -> [(tarih, irs_no, yon, miktar, durum)]
            ref_totals = {}     # stok_kodu -> {adi, giden, gelen, iade}

            # GIDEN
            cur.execute("""
                SELECT
                    ISNULL(u.urun_kodu, '-'), ISNULL(u.urun_adi, '-'),
                    ci.tarih, ci.irsaliye_no, cs.miktar, ci.durum
                FROM siparis.cikis_irsaliyeleri ci
                JOIN siparis.cikis_irsaliye_satirlar cs ON cs.irsaliye_id = ci.id
                LEFT JOIN stok.urunler u ON cs.urun_id = u.id
                WHERE ci.cari_id = ? AND ci.tarih BETWEEN ? AND ? AND ci.silindi_mi = 0
                ORDER BY ci.tarih DESC
            """, (cari_id, tarih_bas, tarih_bit))
            for r in cur.fetchall():
                kod, adi, tarih, irs_no, miktar, durum = r
                hareket_cache.setdefault(kod, []).append((tarih, irs_no, "GIDEN", miktar or 0, durum))
                d = ref_totals.setdefault(kod, {'adi': adi, 'giden': 0, 'gelen': 0, 'iade': 0})
                d['giden'] += (miktar or 0)

            # GELEN
            cur.execute("""
                SELECT
                    ISNULL(gs.stok_kodu, '-'), ISNULL(gs.stok_adi, '-'),
                    gi.tarih, gi.irsaliye_no, gs.miktar, gi.durum
                FROM siparis.giris_irsaliyeleri gi
                JOIN siparis.giris_irsaliye_satirlar gs ON gs.irsaliye_id = gi.id
                WHERE gi.cari_unvani LIKE ? AND gi.tarih BETWEEN ? AND ?
                ORDER BY gi.tarih DESC
            """, (f"%{cari_unvan}%", tarih_bas, tarih_bit))
            for r in cur.fetchall():
                kod, adi, tarih, irs_no, miktar, durum = r
                hareket_cache.setdefault(kod, []).append((tarih, irs_no, "GELEN", miktar or 0, durum))
                d = ref_totals.setdefault(kod, {'adi': adi, 'giden': 0, 'gelen': 0, 'iade': 0})
                d['gelen'] += (miktar or 0)

            # IADE
            cur.execute("""
                SELECT
                    ISNULL(iis.stok_kodu, '-'), ISNULL(iis.stok_adi, '-'),
                    ii.tarih, ii.iade_no, iis.miktar, ii.durum
                FROM siparis.iade_irsaliyeleri ii
                JOIN siparis.iade_irsaliye_satirlar iis ON iis.irsaliye_id = ii.id
                WHERE ii.cari_id = ? AND ii.tarih BETWEEN ? AND ? AND ii.silindi_mi = 0
                ORDER BY ii.tarih DESC
            """, (cari_id, tarih_bas, tarih_bit))
            for r in cur.fetchall():
                kod, adi, tarih, irs_no, miktar, durum = r
                hareket_cache.setdefault(kod, []).append((tarih, irs_no, "IADE", miktar or 0, durum))
                d = ref_totals.setdefault(kod, {'adi': adi, 'giden': 0, 'gelen': 0, 'iade': 0})
                d['iade'] += (miktar or 0)

            # Her referansin hareketlerini tarihe gore sirala
            for kod in hareket_cache:
                hareket_cache[kod].sort(key=lambda x: x[0] or '', reverse=True)
            self._hareket_cache = hareket_cache

            # -- STAT CARDS --
            toplam_giden = sum(d['giden'] for d in ref_totals.values())
            toplam_gelen = sum(d['gelen'] for d in ref_totals.values())
            toplam_iade = sum(d['iade'] for d in ref_totals.values())
            net = toplam_giden - toplam_gelen - toplam_iade
            self._update_stat(self.giden_card, f"{toplam_giden:,.0f}")
            self._update_stat(self.gelen_card, f"{toplam_gelen:,.0f}")
            self._update_stat(self.iade_card, f"{toplam_iade:,.0f}")
            self._update_stat(self.net_card, f"{net:,.0f}")

            # -- REFERANS TABLOSU --
            ref_list = sorted(ref_totals.items(), key=lambda x: x[1]['giden'], reverse=True)
            row_count = len(ref_list) + (1 if ref_list else 0)  # +1 toplam
            self.ref_table.setRowCount(row_count)

            for i, (kod, d) in enumerate(ref_list):
                n = d['giden'] - d['gelen'] - d['iade']
                self.ref_table.setItem(i, 0, QTableWidgetItem(str(kod)))
                self.ref_table.setItem(i, 1, QTableWidgetItem(str(d['adi'])))
                for col, val, clr in [
                    (2, d['giden'], None), (3, d['gelen'], brand.SUCCESS),
                    (4, d['iade'], brand.WARNING), (5, n, brand.INFO)
                ]:
                    item = QTableWidgetItem(f"{val:,.0f}")
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if clr:
                        item.setForeground(QColor(clr))
                    self.ref_table.setItem(i, col, item)
                self.ref_table.setRowHeight(i, 42)

            # Toplam satiri
            if ref_list:
                tr = len(ref_list)
                tl = QTableWidgetItem("TOPLAM")
                tl.setForeground(QColor(brand.PRIMARY))
                self.ref_table.setItem(tr, 0, tl)
                self.ref_table.setItem(tr, 1, QTableWidgetItem(""))
                for col, val, clr in [
                    (2, toplam_giden, brand.TEXT), (3, toplam_gelen, brand.SUCCESS),
                    (4, toplam_iade, brand.WARNING), (5, net, brand.INFO)
                ]:
                    item = QTableWidgetItem(f"{val:,.0f}")
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setForeground(QColor(clr))
                    self.ref_table.setItem(tr, col, item)
                self.ref_table.setRowHeight(tr, 42)

            self.ref_count.setText(f"{len(ref_list)} referans")

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Hata", f"Veri yuklenirken hata olustu:\n{e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
