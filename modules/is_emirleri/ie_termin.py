# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Termin Takip Sayfası
[MODERNIZED UI - v3.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QComboBox, QLineEdit, QTabWidget, QWidget,
    QProgressBar, QMessageBox, QMenu, QSplitter, QCheckBox, QDialog, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QBrush, QFont, QCursor
from datetime import datetime
from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


# Row highlight renkleri (durum bazlı subtle background)
ROW_TINT_LATE     = QColor(220, 38, 38, 38)    # Geciken
ROW_TINT_TODAY    = QColor(245, 158, 11, 38)   # Bugün
ROW_TINT_SOON     = QColor(59, 130, 246, 38)   # Yaklaşan
ROW_TINT_KALAN    = QColor(168, 85, 247, 40)   # Eksik parça
PURPLE_ACCENT     = "#A855F7"                  # Kalan parça vurgusu


class IsEmriTerminPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.conn = None

        self._setup_ui()
        QTimer.singleShot(100, self._load_initial)

    # ── ORTAK STİL HELPER'LARI ──
    def _input_style(self) -> str:
        return f"""
            QLineEdit, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {brand.PRIMARY};
                background: {brand.BG_HOVER};
            }}
            QComboBox:hover {{ border-color: {brand.BORDER_HARD}; }}
            QComboBox::drop-down {{ border: none; width: {brand.sp(24)}px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                selection-background-color: {brand.PRIMARY};
                outline: 0;
                padding: {brand.SP_1}px;
            }}
        """

    def _secondary_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
            }}
        """

    def _card_style(self) -> str:
        return (
            f"QFrame#card {{"
            f" background: {brand.BG_CARD};"
            f" border: 1px solid {brand.BORDER};"
            f" border-radius: {brand.R_LG}px;"
            f" }}"
        )

    def _setup_ui(self):
        self.setStyleSheet(f"IsEmriTerminPage {{ background: {brand.BG_MAIN}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # Hero header
        layout.addWidget(self._create_hero_header())

        # Özet Kartları
        cards = QHBoxLayout()
        cards.setSpacing(brand.SP_3)
        self.card_geciken = self._card("GECİKEN",     "0", brand.ERROR)
        self.card_bugun   = self._card("BUGÜN",       "0", brand.WARNING)
        self.card_yaklasan = self._card("YAKINLAŞAN", "0", brand.PRIMARY)
        self.card_kalan   = self._card("KALAN PARÇA", "0", PURPLE_ACCENT)
        self.card_devam   = self._card("DEVAM EDEN",  "0", brand.SUCCESS)
        for c in [self.card_geciken, self.card_bugun, self.card_yaklasan, self.card_kalan, self.card_devam]:
            cards.addWidget(c)
        layout.addLayout(cards)

        # Filtre barı
        fl = QHBoxLayout()
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(brand.SP_2)

        input_style = self._input_style()

        self.cmb_musteri = QComboBox()
        self.cmb_musteri.setMinimumWidth(brand.sp(200))
        self.cmb_musteri.setFixedHeight(brand.sp(40))
        self.cmb_musteri.setStyleSheet(input_style)
        self.cmb_musteri.addItem("Tüm Müşteriler", None)
        self.cmb_musteri.currentIndexChanged.connect(self._filter)
        fl.addWidget(self.cmb_musteri)

        self.cmb_hat = QComboBox()
        self.cmb_hat.setMinimumWidth(brand.sp(150))
        self.cmb_hat.setFixedHeight(brand.sp(40))
        self.cmb_hat.setStyleSheet(input_style)
        self.cmb_hat.addItem("Tüm Hatlar", None)
        self.cmb_hat.currentIndexChanged.connect(self._filter)
        fl.addWidget(self.cmb_hat)

        self.cmb_durum = QComboBox()
        self.cmb_durum.setMinimumWidth(brand.sp(150))
        self.cmb_durum.setFixedHeight(brand.sp(40))
        self.cmb_durum.setStyleSheet(input_style)
        self.cmb_durum.addItems(["Tümü", "Geciken", "Bugün", "Yaklaşan", "Kalan Parça", "Üretimde"])
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        fl.addWidget(self.cmb_durum)

        self.txt_ara = QLineEdit()
        self.txt_ara.setPlaceholderText("Ara (iş emri, stok)")
        self.txt_ara.setMinimumWidth(brand.sp(200))
        self.txt_ara.setFixedHeight(brand.sp(40))
        self.txt_ara.setStyleSheet(input_style)
        self.txt_ara.textChanged.connect(self._filter)
        fl.addWidget(self.txt_ara)

        self.chk_eksik = QCheckBox("Sadece eksik")
        self.chk_eksik.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"spacing: {brand.SP_2}px; "
            f"background: transparent;"
        )
        self.chk_eksik.stateChanged.connect(self._filter)
        fl.addWidget(self.chk_eksik)
        fl.addStretch()

        btn_ref = QPushButton("Yenile")
        btn_ref.setCursor(Qt.PointingHandCursor)
        btn_ref.setFixedHeight(brand.sp(40))
        btn_ref.clicked.connect(self._load_data)
        btn_ref.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        fl.addWidget(btn_ref)
        layout.addLayout(fl)
        
        # Splitter
        sp = QSplitter(Qt.Horizontal)
        sp.setHandleWidth(brand.sp(6))
        sp.setStyleSheet(f"""
            QSplitter::handle {{ background: transparent; }}
            QSplitter::handle:hover {{ background: {brand.PRIMARY_SOFT}; }}
        """)

        # Sol - Müşteriler
        lf = QFrame()
        lf.setObjectName("card")
        lf.setMinimumWidth(brand.sp(280))
        lf.setMaximumWidth(brand.sp(340))
        lf.setStyleSheet(self._card_style())
        ll = QVBoxLayout(lf)
        ll.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        ll.setSpacing(brand.SP_3)

        lh = QLabel("Müşteri Özeti")
        lh.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_BODY_LG}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"background: transparent;"
        )
        ll.addWidget(lh)

        self.tbl_must = QTableWidget()
        self.tbl_must.setColumnCount(4)
        self.tbl_must.setHorizontalHeaderLabels(["Müşteri", "Bek", "Gec", "Kal"])
        self.tbl_must.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 4):
            self.tbl_must.horizontalHeader().setSectionResizeMode(i, QHeaderView.Fixed)
            self.tbl_must.setColumnWidth(i, brand.sp(48))
        self.tbl_must.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_must.verticalHeader().setVisible(False)
        self.tbl_must.itemSelectionChanged.connect(self._must_sec)
        self._tbl_style(self.tbl_must)
        ll.addWidget(self.tbl_must, 1)
        sp.addWidget(lf)

        # Sağ - İş Emirleri
        rf = QFrame()
        rf.setObjectName("card")
        rf.setStyleSheet(self._card_style())
        rl = QVBoxLayout(rf)
        rl.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_3)
        rl.setSpacing(brand.SP_3)

        self.lbl_baslik = QLabel("Tüm İş Emirleri")
        self.lbl_baslik.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_BODY_LG}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"background: transparent;"
        )
        rl.addWidget(self.lbl_baslik)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
                top: -1px;
            }}
            QTabBar {{ background: transparent; }}
            QTabBar::tab {{
                background: transparent;
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_2}px {brand.SP_4}px;
                margin-right: {brand.SP_2}px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QTabBar::tab:hover {{ color: {brand.TEXT}; }}
            QTabBar::tab:selected {{
                color: {brand.PRIMARY};
                border-bottom-color: {brand.PRIMARY};
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """)

        # Liste Tab
        t1 = QWidget()
        t1.setStyleSheet("background: transparent;")
        t1l = QVBoxLayout(t1)
        t1l.setContentsMargins(0, brand.SP_2, 0, 0)
        self.tbl_ie = QTableWidget()
        self.tbl_ie.setColumnCount(12)
        self.tbl_ie.setHorizontalHeaderLabels(["İş Emri", "Müşteri", "Stok Kodu", "Stok Adı", "Kaplama", "Miktar", "Üretilen", "Kalan", "Termin", "Gün", "Durum", "İlerleme"])
        for i, w in enumerate([110, 140, 100, 160, 90, 70, 70, 60, 90, 50, 90, 110]):
            self.tbl_ie.setColumnWidth(i, brand.sp(w))
        self.tbl_ie.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_ie.verticalHeader().setVisible(False)
        self.tbl_ie.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tbl_ie.customContextMenuRequested.connect(self._ctx_menu)
        self.tbl_ie.doubleClicked.connect(self._detay)
        self._tbl_style(self.tbl_ie)
        t1l.addWidget(self.tbl_ie)
        self.tabs.addTab(t1, "Liste")

        # Kalan Tab
        t2 = QWidget()
        t2.setStyleSheet("background: transparent;")
        t2l = QVBoxLayout(t2)
        t2l.setContentsMargins(0, brand.SP_2, 0, 0)
        t2l.setSpacing(brand.SP_3)

        wf = QFrame()
        wf.setStyleSheet(
            f"QFrame {{"
            f" background: {brand.WARNING_SOFT};"
            f" border: 1px solid rgba(245,158,11,0.35);"
            f" border-radius: {brand.R_MD}px;"
            f" }}"
        )
        wfl = QHBoxLayout(wf)
        wfl.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)
        uyari = QLabel("Eksik parça kalan iş emirleri")
        uyari.setStyleSheet(
            f"color: {brand.WARNING}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"background: transparent;"
        )
        wfl.addWidget(uyari)
        wfl.addStretch()
        t2l.addWidget(wf)

        self.tbl_kalan = QTableWidget()
        self.tbl_kalan.setColumnCount(9)
        self.tbl_kalan.setHorizontalHeaderLabels(["İş Emri", "Müşteri", "Stok Kodu", "Toplam", "Üretilen", "Kalan", "Termin", "Bekleme", "Aksiyon"])
        for i, w in enumerate([110, 150, 110, 70, 70, 65, 90, 80, 95]):
            self.tbl_kalan.setColumnWidth(i, brand.sp(w))
        self.tbl_kalan.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_kalan.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_kalan)
        t2l.addWidget(self.tbl_kalan, 1)
        self.tabs.addTab(t2, "Kalan Parçalar")

        # Takvim Tab
        t3 = QWidget()
        t3.setStyleSheet("background: transparent;")
        t3l = QVBoxLayout(t3)
        t3l.setContentsMargins(0, brand.SP_2, 0, 0)
        self.tbl_tak = QTableWidget()
        self.tbl_tak.setColumnCount(7)
        today = QDate.currentDate()
        hdrs = [f"{['Pzt','Sal','Çar','Per','Cum','Cmt','Paz'][today.addDays(i).dayOfWeek()-1]}\n{today.addDays(i).toString('dd.MM')}" for i in range(7)]
        self.tbl_tak.setHorizontalHeaderLabels(hdrs)
        self.tbl_tak.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_tak.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_tak)
        t3l.addWidget(self.tbl_tak)
        self.tabs.addTab(t3, "Takvim")

        rl.addWidget(self.tabs, 1)

        # Alt Bar
        bb = QWidget()
        bb.setStyleSheet("background: transparent;")
        bbl = QHBoxLayout(bb)
        bbl.setContentsMargins(0, brand.SP_2, 0, 0)
        bbl.setSpacing(brand.SP_2)

        self.lbl_gunc = QLabel("Son güncelleme: -")
        self.lbl_gunc.setStyleSheet(
            f"color: {brand.TEXT_DIM}; "
            f"font-size: {brand.FS_CAPTION}px; "
            f"background: transparent;"
        )
        bbl.addWidget(self.lbl_gunc)
        bbl.addStretch()

        btn_bild = QPushButton("Toplu Bildirim")
        btn_bild.setCursor(Qt.PointingHandCursor)
        btn_bild.setFixedHeight(brand.sp(34))
        btn_bild.setStyleSheet(f"""
            QPushButton {{
                background: {brand.WARNING_SOFT};
                color: {brand.WARNING};
                border: 1px solid rgba(245,158,11,0.35);
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{
                background: {brand.WARNING};
                color: white;
            }}
        """)
        btn_bild.clicked.connect(lambda: QMessageBox.information(self, "Bilgi", "Toplu bildirim özelliği aktif edilecek."))
        bbl.addWidget(btn_bild)

        btn_exc = QPushButton("Excel")
        btn_exc.setCursor(Qt.PointingHandCursor)
        btn_exc.setFixedHeight(brand.sp(34))
        btn_exc.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS_SOFT};
                color: {brand.SUCCESS};
                border: 1px solid rgba(16,185,129,0.35);
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{
                background: {brand.SUCCESS};
                color: white;
            }}
        """)
        btn_exc.clicked.connect(self._excel)
        bbl.addWidget(btn_exc)

        rl.addWidget(bb)
        sp.addWidget(rf)
        sp.setStretchFactor(0, 22)
        sp.setStretchFactor(1, 78)
        sp.setSizes([brand.sp(300), brand.sp(980)])
        layout.addWidget(sp, 1)

    def _create_hero_header(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(brand.SP_1, 0, brand.SP_1, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)

        title = QLabel("Termin Takip")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_TITLE_LG}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"letter-spacing: -0.4px; "
            f"background: transparent;"
        )
        title_col.addWidget(title)

        subtitle = QLabel("Termin durumunu ve kalan parçaları takip edin")
        subtitle.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY}px; "
            f"background: transparent;"
        )
        title_col.addWidget(subtitle)

        layout.addLayout(title_col)
        layout.addStretch()
        return wrapper

    def _card(self, title, val, color):
        c = QFrame()
        c.setFixedHeight(brand.sp(92))
        c.setMinimumWidth(brand.sp(160))
        c.setStyleSheet(
            f"QFrame {{"
            f" background: {brand.BG_CARD};"
            f" border: 1px solid {brand.BORDER};"
            f" border-left: 3px solid {color};"
            f" border-radius: {brand.R_LG}px;"
            f" }}"
            f"QFrame:hover {{ background: {brand.BG_HOVER}; }}"
        )
        l = QVBoxLayout(c)
        l.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)
        l.setSpacing(brand.SP_1)

        caption = QLabel(title)
        caption.setStyleSheet(
            f"color: {brand.TEXT_DIM}; "
            f"font-size: {brand.FS_CAPTION}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"letter-spacing: 0.6px; "
            f"background: transparent;"
        )
        l.addWidget(caption)

        lv = QLabel(val)
        lv.setObjectName("val")
        lv.setStyleSheet(
            f"color: {color}; "
            f"font-size: {brand.FS_DISPLAY}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"background: transparent;"
        )
        l.addWidget(lv)
        l.addStretch()
        return c

    def _tbl_style(self, t):
        t.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                gridline-color: {brand.BORDER};
                font-size: {brand.FS_BODY_SM}px;
                outline: 0;
            }}
            QTableWidget::item {{
                padding: {brand.SP_2}px {brand.SP_2}px;
                background: transparent;
            }}
            QTableWidget::item:selected {{
                background: {brand.PRIMARY_SOFT};
                color: {brand.TEXT};
            }}
            QHeaderView::section {{
                background: {brand.BG_ELEVATED};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_2}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_CAPTION}px;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }}
        """)
        t.setFrameShape(QFrame.NoFrame)
        t.setShowGrid(False)
        t.verticalHeader().setDefaultSectionSize(brand.sp(38))

    def _load_initial(self):
        try:
            self.conn = get_db_connection()
            self._load_hatlar()
            self._load_data()
        except Exception as e:
            print(f"Bağlantı hatası: {e}")

    def _load_hatlar(self):
        if not self.conn: return
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT id, ad FROM tanim.hat_bolumleri WHERE aktif_mi=1 ORDER BY sira,ad")
            for r in cur.fetchall():
                self.cmb_hat.addItem(r[1], r[0])
        except Exception: pass

    def _load_data(self):
        if not self.conn:
            try: self.conn = get_db_connection()
            except Exception: return
        try:
            cur = self.conn.cursor()
            self._load_must(cur)
            self._load_ie(cur)
            self._load_kalan(cur)
            self._load_cards(cur)
            self._load_tak(cur)
            self.lbl_gunc.setText(f"Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Veri hatası: {e}")

    def _load_must(self, cur):
        try:
            cur.execute("""SELECT ISNULL(cari_unvani,'Belirtilmemiş'),COUNT(*),
                SUM(CASE WHEN termin_tarihi<CAST(GETDATE() AS DATE) THEN 1 ELSE 0 END),
                SUM(CASE WHEN ISNULL(toplam_miktar,planlanan_miktar)-ISNULL(uretilen_miktar,0)>0 AND ISNULL(uretilen_miktar,0)>0 THEN 1 ELSE 0 END)
                FROM siparis.is_emirleri WHERE silindi_mi=0 AND durum NOT IN('Tamamlandı','İptal','TAMAMLANDI','IPTAL')
                GROUP BY cari_unvani ORDER BY 3 DESC,2 DESC""")
            rows = cur.fetchall()
            self.tbl_must.setRowCount(len(rows))
            cur_d = self.cmb_musteri.currentData()
            self.cmb_musteri.blockSignals(True)
            self.cmb_musteri.clear()
            self.cmb_musteri.addItem("Tüm Müşteriler", None)
            for i, r in enumerate(rows):
                m, t, g, k = r[0] or "?", r[1] or 0, r[2] or 0, r[3] or 0
                it0 = QTableWidgetItem(m[:18]+"..." if len(m)>18 else m)
                it0.setToolTip(m)
                it0.setData(Qt.UserRole, m)
                it1 = QTableWidgetItem(str(t))
                it1.setTextAlignment(Qt.AlignCenter)
                it2 = QTableWidgetItem(str(g))
                it2.setTextAlignment(Qt.AlignCenter)
                if g > 0:
                    it2.setForeground(QBrush(QColor(brand.ERROR)))
                    it2.setFont(QFont("", -1, QFont.Bold))
                it3 = QTableWidgetItem(str(k))
                it3.setTextAlignment(Qt.AlignCenter)
                if k > 0:
                    it3.setForeground(QBrush(QColor(PURPLE_ACCENT)))
                    it3.setFont(QFont("", -1, QFont.Bold))
                self.tbl_must.setItem(i, 0, it0)
                self.tbl_must.setItem(i, 1, it1)
                self.tbl_must.setItem(i, 2, it2)
                self.tbl_must.setItem(i, 3, it3)
                self.cmb_musteri.addItem(m[:22]+"..." if len(m)>22 else m, m)
            if cur_d:
                idx = self.cmb_musteri.findData(cur_d)
                if idx >= 0: self.cmb_musteri.setCurrentIndex(idx)
            self.cmb_musteri.blockSignals(False)
        except Exception as e:
            print(f"Müşteri hatası: {e}")

    def _load_ie(self, cur):
        try:
            wh = ["silindi_mi=0", "durum NOT IN('Tamamlandı','İptal','TAMAMLANDI','IPTAL')"]
            pr = []
            m = self.cmb_musteri.currentData()
            if m: wh.append("cari_unvani=?"); pr.append(m)
            h = self.cmb_hat.currentData()
            if h: wh.append("hat_id=?"); pr.append(h)
            a = self.txt_ara.text().strip()
            if a: wh.append("(is_emri_no LIKE ? OR stok_kodu LIKE ?)"); pr.extend([f"%{a}%"]*2)
            if self.chk_eksik.isChecked():
                wh.append("ISNULL(toplam_miktar,planlanan_miktar)-ISNULL(uretilen_miktar,0)>0 AND ISNULL(uretilen_miktar,0)>0")
            d = self.cmb_durum.currentText()
            if d == "Geciken": wh.append("termin_tarihi<CAST(GETDATE() AS DATE)")
            elif d == "Bugün": wh.append("termin_tarihi=CAST(GETDATE() AS DATE)")
            elif d == "Yaklaşan": wh.append("termin_tarihi>CAST(GETDATE() AS DATE) AND termin_tarihi<=DATEADD(day,3,CAST(GETDATE() AS DATE))")
            elif d == "Kalan Parça": wh.append("ISNULL(toplam_miktar,planlanan_miktar)-ISNULL(uretilen_miktar,0)>0 AND ISNULL(uretilen_miktar,0)>0")
            elif d == "Üretimde": wh.append("durum IN('Üretimde','URETIMDE')")
            q = f"SELECT id,is_emri_no,cari_unvani,stok_kodu,stok_adi,kaplama_tipi,ISNULL(toplam_miktar,planlanan_miktar),ISNULL(uretilen_miktar,0),termin_tarihi,durum FROM siparis.is_emirleri WHERE {' AND '.join(wh)} ORDER BY CASE WHEN termin_tarihi<CAST(GETDATE() AS DATE) THEN 0 ELSE 1 END,termin_tarihi"
            cur.execute(q, pr)
            rows = cur.fetchall()
            self.tbl_ie.setRowCount(len(rows))
            today = datetime.now().date()
            for i, r in enumerate(rows):
                ie_id, no, mu, sk, sa, kp, tp, ur, tr, du = r
                kl = (tp or 0) - (ur or 0)
                il = (ur / tp * 100) if tp and tp > 0 else 0
                gf = None
                if tr:
                    td = tr.date() if hasattr(tr, 'date') else tr
                    gf = (td - today).days
                rc = None
                if gf is not None:
                    if gf < 0: rc = ROW_TINT_LATE
                    elif gf == 0: rc = ROW_TINT_TODAY
                    elif gf <= 3: rc = ROW_TINT_SOON
                if kl > 0 and ur and ur > 0: rc = ROW_TINT_KALAN
                its = [QTableWidgetItem(no or ""), QTableWidgetItem((mu or "")[:16]), QTableWidgetItem(sk or ""),
                       QTableWidgetItem((sa or "")[:18]), QTableWidgetItem(kp or ""), QTableWidgetItem(f"{tp:,.0f}" if tp else "0"),
                       QTableWidgetItem(f"{ur:,.0f}" if ur else "0"), QTableWidgetItem(f"{kl:,.0f}"),
                       QTableWidgetItem(tr.strftime("%d.%m.%Y") if tr else "-"), QTableWidgetItem(str(gf) if gf is not None else "-"),
                       QTableWidgetItem(du or "")]
                for j, it in enumerate(its):
                    it.setData(Qt.UserRole, ie_id)
                    if rc: it.setBackground(QBrush(rc))
                    if j in [5,6,7,9]: it.setTextAlignment(Qt.AlignCenter)
                    if j == 7 and kl > 0 and ur:
                        it.setForeground(QBrush(QColor(PURPLE_ACCENT)))
                        it.setFont(QFont("", -1, QFont.Bold))
                    if j == 9 and gf is not None and gf < 0:
                        it.setForeground(QBrush(QColor(brand.ERROR)))
                        it.setFont(QFont("", -1, QFont.Bold))
                    self.tbl_ie.setItem(i, j, it)

                if il >= 90:
                    chunk_color = brand.SUCCESS
                elif il >= 50:
                    chunk_color = brand.PRIMARY
                else:
                    chunk_color = brand.WARNING

                pb = QProgressBar()
                pb.setRange(0, 100)
                pb.setValue(int(il))
                pb.setFormat(f"{il:.0f}%")
                pb.setStyleSheet(f"""
                    QProgressBar {{
                        border: 1px solid {brand.BORDER};
                        border-radius: {brand.sp(4)}px;
                        text-align: center;
                        background: {brand.BG_INPUT};
                        color: {brand.TEXT};
                        font-size: {brand.FS_CAPTION}px;
                        font-weight: {brand.FW_SEMIBOLD};
                    }}
                    QProgressBar::chunk {{
                        background: {chunk_color};
                        border-radius: {brand.sp(3)}px;
                    }}
                """)
                self.tbl_ie.setCellWidget(i, 11, pb)
        except Exception as e:
            print(f"İş emri hatası: {e}")
            import traceback; traceback.print_exc()

    def _load_kalan(self, cur):
        try:
            cur.execute("""SELECT id,is_emri_no,cari_unvani,stok_kodu,ISNULL(toplam_miktar,planlanan_miktar),ISNULL(uretilen_miktar,0),termin_tarihi
                FROM siparis.is_emirleri WHERE silindi_mi=0 AND durum NOT IN('Tamamlandı','İptal','TAMAMLANDI','IPTAL')
                AND ISNULL(toplam_miktar,planlanan_miktar)-ISNULL(uretilen_miktar,0)>0 AND ISNULL(uretilen_miktar,0)>0
                ORDER BY ISNULL(toplam_miktar,planlanan_miktar)-ISNULL(uretilen_miktar,0),termin_tarihi""")
            rows = cur.fetchall()
            self.tbl_kalan.setRowCount(len(rows))
            today = datetime.now().date()
            for i, r in enumerate(rows):
                ie_id, no, mu, sk, tp, ur, tr = r
                kl = (tp or 0) - (ur or 0)
                bk = 0
                if tr:
                    td = tr.date() if hasattr(tr, 'date') else tr
                    gf = (today - td).days
                    bk = gf if gf > 0 else 0
                rc = ROW_TINT_KALAN if kl <= 5 else ROW_TINT_TODAY
                its = [QTableWidgetItem(no or ""), QTableWidgetItem((mu or "")[:18]), QTableWidgetItem(sk or ""),
                       QTableWidgetItem(f"{tp:,.0f}" if tp else "0"), QTableWidgetItem(f"{ur:,.0f}" if ur else "0"),
                       QTableWidgetItem(f"{kl:,.0f}"), QTableWidgetItem(tr.strftime("%d.%m.%Y") if tr else "-"),
                       QTableWidgetItem(f"{bk} gün" if bk > 0 else "-")]
                for j, it in enumerate(its):
                    it.setData(Qt.UserRole, ie_id)
                    it.setBackground(QBrush(rc))
                    if j in [3,4,5]: it.setTextAlignment(Qt.AlignCenter)
                    if j == 5:
                        it.setForeground(QBrush(QColor(PURPLE_ACCENT)))
                        it.setFont(QFont("", -1, QFont.Bold))
                    self.tbl_kalan.setItem(i, j, it)
                btn = QPushButton("Bildir")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setFixedHeight(brand.sp(26))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(168, 85, 247, 0.15);
                        color: {PURPLE_ACCENT};
                        border: 1px solid rgba(168, 85, 247, 0.35);
                        border-radius: {brand.R_SM}px;
                        padding: 0 {brand.SP_3}px;
                        font-size: {brand.FS_CAPTION}px;
                        font-weight: {brand.FW_SEMIBOLD};
                    }}
                    QPushButton:hover {{
                        background: {PURPLE_ACCENT};
                        color: white;
                    }}
                """)
                btn.clicked.connect(lambda c, n=no, m=mu, k=kl: QMessageBox.information(self, "Bildirim", f"Müşteri: {m}\nİş Emri: {n}\nKalan: {k} adet\n\nBildirim kaydedildi."))
                self.tbl_kalan.setCellWidget(i, 8, btn)
        except Exception as e:
            print(f"Kalan hatası: {e}")

    def _load_cards(self, cur):
        try:
            cur.execute("SELECT COUNT(*) FROM siparis.is_emirleri WHERE silindi_mi=0 AND durum NOT IN('Tamamlandı','İptal','TAMAMLANDI','IPTAL') AND termin_tarihi<CAST(GETDATE() AS DATE)")
            self.card_geciken.findChild(QLabel, "val").setText(str(cur.fetchone()[0] or 0))
            cur.execute("SELECT COUNT(*) FROM siparis.is_emirleri WHERE silindi_mi=0 AND durum NOT IN('Tamamlandı','İptal','TAMAMLANDI','IPTAL') AND termin_tarihi=CAST(GETDATE() AS DATE)")
            self.card_bugun.findChild(QLabel, "val").setText(str(cur.fetchone()[0] or 0))
            cur.execute("SELECT COUNT(*) FROM siparis.is_emirleri WHERE silindi_mi=0 AND durum NOT IN('Tamamlandı','İptal','TAMAMLANDI','IPTAL') AND termin_tarihi>CAST(GETDATE() AS DATE) AND termin_tarihi<=DATEADD(day,3,CAST(GETDATE() AS DATE))")
            self.card_yaklasan.findChild(QLabel, "val").setText(str(cur.fetchone()[0] or 0))
            cur.execute("SELECT COUNT(*) FROM siparis.is_emirleri WHERE silindi_mi=0 AND durum NOT IN('Tamamlandı','İptal','TAMAMLANDI','IPTAL') AND ISNULL(toplam_miktar,planlanan_miktar)-ISNULL(uretilen_miktar,0)>0 AND ISNULL(uretilen_miktar,0)>0")
            self.card_kalan.findChild(QLabel, "val").setText(str(cur.fetchone()[0] or 0))
            cur.execute("SELECT COUNT(*) FROM siparis.is_emirleri WHERE silindi_mi=0 AND durum IN('Üretimde','URETIMDE')")
            self.card_devam.findChild(QLabel, "val").setText(str(cur.fetchone()[0] or 0))
        except Exception: pass

    def _load_tak(self, cur):
        try:
            today = QDate.currentDate()
            dd = {today.addDays(i).toString("yyyy-MM-dd"): [] for i in range(7)}
            cur.execute("""SELECT termin_tarihi,is_emri_no,cari_unvani FROM siparis.is_emirleri
                WHERE silindi_mi=0 AND durum NOT IN('Tamamlandı','İptal','TAMAMLANDI','IPTAL')
                AND termin_tarihi>=CAST(GETDATE() AS DATE) AND termin_tarihi<DATEADD(day,7,CAST(GETDATE() AS DATE))
                ORDER BY termin_tarihi""")
            for r in cur.fetchall():
                if r[0]:
                    ds = r[0].strftime("%Y-%m-%d") if hasattr(r[0], 'strftime') else str(r[0])[:10]
                    if ds in dd: dd[ds].append({'no': r[1], 'mu': r[2]})
            mx = max(len(v) for v in dd.values()) if dd else 1
            mx = max(mx, 5)
            self.tbl_tak.setRowCount(mx)
            for col, (ds, its) in enumerate(dd.items()):
                for row in range(mx):
                    if row < len(its):
                        d = its[row]
                        it = QTableWidgetItem(f"{d['no']}\n{(d['mu'] or '')[:10]}...")
                        it.setBackground(QBrush(ROW_TINT_SOON))
                    else:
                        it = QTableWidgetItem("")
                    self.tbl_tak.setItem(row, col, it)
            self.tbl_tak.verticalHeader().setDefaultSectionSize(brand.sp(56))
        except Exception: pass

    def _filter(self):
        if self.conn:
            cur = self.conn.cursor()
            self._load_ie(cur)

    def _must_sec(self):
        sel = self.tbl_must.selectedItems()
        if sel:
            m = sel[0].data(Qt.UserRole)
            self.lbl_baslik.setText((m[:28] + "…") if len(m) > 28 else m)
            idx = self.cmb_musteri.findData(m)
            if idx >= 0:
                self.cmb_musteri.blockSignals(True)
                self.cmb_musteri.setCurrentIndex(idx)
                self.cmb_musteri.blockSignals(False)
            self._filter()

    def _ctx_menu(self, pos):
        it = self.tbl_ie.itemAt(pos)
        if not it: return
        ie_id = it.data(Qt.UserRole)
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_1}px;
            }}
            QMenu::item {{
                padding: {brand.SP_2}px {brand.SP_5}px;
                color: {brand.TEXT};
                border-radius: {brand.R_SM}px;
            }}
            QMenu::item:selected {{
                background: {brand.PRIMARY_SOFT};
                color: {brand.TEXT};
            }}
            QMenu::separator {{
                height: 1px;
                background: {brand.BORDER};
                margin: {brand.SP_1}px {brand.SP_2}px;
            }}
        """)
        menu.addAction("Detay").triggered.connect(lambda: self._show_det(ie_id))
        menu.addSeparator()
        menu.addAction("Not Ekle").triggered.connect(lambda: self._add_not(ie_id))
        menu.addAction("Tamamlandı").triggered.connect(lambda: self._tamam(ie_id))
        menu.exec_(QCursor.pos())

    def _detay(self, idx):
        it = self.tbl_ie.item(idx.row(), 0)
        if it: self._show_det(it.data(Qt.UserRole))

    def _show_det(self, ie_id):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT is_emri_no,cari_unvani,stok_kodu,stok_adi,kaplama_tipi,ISNULL(toplam_miktar,planlanan_miktar),ISNULL(uretilen_miktar,0),termin_tarihi,durum,uretim_notu FROM siparis.is_emirleri WHERE id=?", (ie_id,))
            r = cur.fetchone()
            if r:
                kl = (r[5] or 0) - (r[6] or 0)
                QMessageBox.information(self, f"İş Emri - {r[0]}", f"İş Emri: {r[0]}\nMüşteri: {r[1]}\nStok: {r[2]} - {r[3]}\nKaplama: {r[4]}\n\nToplam: {r[5]:,.0f}\nÜretilen: {r[6]:,.0f}\nKalan: {kl:,.0f}\n\nTermin: {r[7].strftime('%d.%m.%Y') if r[7] else '-'}\nDurum: {r[8]}\n\nNot: {r[9] or '-'}")
        except Exception: pass

    def _add_not(self, ie_id):
        dlg = QDialog(self)
        dlg.setWindowTitle("Not Ekle")
        dlg.setMinimumSize(350, 180)
        l = QVBoxLayout(dlg)
        txt = QTextEdit()
        txt.setPlaceholderText("Notunuzu yazın...")
        l.addWidget(txt)
        bl = QHBoxLayout()
        bk = QPushButton("Kaydet")
        bk.clicked.connect(dlg.accept)
        bi = QPushButton("İptal")
        bi.clicked.connect(dlg.reject)
        bl.addWidget(bk)
        bl.addWidget(bi)
        l.addLayout(bl)
        if dlg.exec_() == QDialog.Accepted and txt.toPlainText().strip():
            try:
                cur = self.conn.cursor()
                cur.execute("UPDATE siparis.is_emirleri SET uretim_notu=ISNULL(uretim_notu,'')+CHAR(10)+? WHERE id=?", (f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}] {txt.toPlainText().strip()}", ie_id))
                self.conn.commit()
                QMessageBox.information(self, "Bilgi", "Not eklendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _tamam(self, ie_id):
        if QMessageBox.question(self, "Onay", "Tamamlandı olarak işaretlensin mi?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                cur = self.conn.cursor()
                cur.execute("UPDATE siparis.is_emirleri SET durum='Tamamlandı' WHERE id=?", (ie_id,))
                self.conn.commit()
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _excel(self):
        try:
            import pandas as pd
            from PySide6.QtWidgets import QFileDialog
            rows = [[self.tbl_ie.item(i, j).text() if self.tbl_ie.item(i, j) else "" for j in range(11)] for i in range(self.tbl_ie.rowCount())]
            df = pd.DataFrame(rows, columns=["İş Emri", "Müşteri", "Stok Kodu", "Stok Adı", "Kaplama", "Miktar", "Üretilen", "Kalan", "Termin", "Gün", "Durum"])
            p, _ = QFileDialog.getSaveFileName(self, "Kaydet", f"termin_{datetime.now().strftime('%Y%m%d')}.xlsx", "Excel (*.xlsx)")
            if p:
                df.to_excel(p, index=False)
                QMessageBox.information(self, "Bilgi", f"Kaydedildi: {p}")
        except ImportError:
            QMessageBox.warning(self, "Uyarı", "pandas ve openpyxl gerekli.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
