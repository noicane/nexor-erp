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


def get_modern_style(theme: dict) -> dict:
    t = theme or {}
    return {
        'card_bg': t.get('bg_card', '#151B23'),
        'input_bg': t.get('bg_input', '#232C3B'),
        'border': t.get('border', '#1E2736'),
        'text': t.get('text', '#E8ECF1'),
        'text_secondary': t.get('text_secondary', '#8896A6'),
        'text_muted': t.get('text_muted', '#5C6878'),
        'primary': t.get('primary', '#DC2626'),
        'primary_hover': t.get('primary_hover', '#9B1818'),
        'success': t.get('success', '#10B981'),
        'warning': t.get('warning', '#F59E0B'),
        'error': t.get('error', '#EF4444'),
        'danger': t.get('error', '#EF4444'),
        'info': t.get('info', '#3B82F6'),
        'bg_main': t.get('bg_main', '#0F1419'),
        'bg_hover': t.get('bg_hover', '#1C2430'),
        'bg_selected': t.get('bg_selected', '#1E1215'),
        'border_light': t.get('border_light', '#2A3545'),
        'border_input': t.get('border_input', '#1E2736'),
        'card_solid': t.get('bg_card_solid', '#151B23'),
        'gradient': t.get('gradient_css', ''),
    }


class IsEmriTerminPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.conn = None
        
        # Eski değişken isimleri için uyumluluk
        self.bg_card = self.s['card_bg']
        self.bg_input = self.s['input_bg']
        self.bg_main = self.s['card_bg']
        self.bg_hover = 'rgba(51, 65, 85, 0.5)'
        self.text = self.s['text']
        self.text_secondary = self.s['text_secondary']
        self.text_muted = self.s['text_muted']
        self.border = self.s['border']
        self.primary = self.s['primary']
        self.success = self.s['success']
        self.warning = self.s['warning']
        self.error = self.s['error']
        
        self._setup_ui()
        QTimer.singleShot(100, self._load_initial)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Özet Kartları
        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_geciken = self._card("⚠️ GECİKEN", "0", self.error)
        self.card_bugun = self._card("📅 BUGÜN", "0", self.warning)
        self.card_yaklasan = self._card("⏰ YAKINLAŞAN", "0", self.primary)
        self.card_kalan = self._card("🔴 KALAN PARÇA", "0", "#9b59b6")
        self.card_devam = self._card("🔄 DEVAM EDEN", "0", self.success)
        for c in [self.card_geciken, self.card_bugun, self.card_yaklasan, self.card_kalan, self.card_devam]:
            cards.addWidget(c)
        layout.addLayout(cards)
        
        # Filtreler
        ff = QFrame()
        ff.setStyleSheet(f"QFrame{{background:{self.bg_card};border-radius:8px;padding:12px;}}")
        fl = QHBoxLayout(ff)
        fl.setContentsMargins(12, 8, 12, 8)
        fl.setSpacing(12)
        inp = f"background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;padding:6px 10px;"
        
        fl.addWidget(QLabel("Müşteri:", styleSheet=f"color:{self.text};"))
        self.cmb_musteri = QComboBox()
        self.cmb_musteri.setMinimumWidth(180)
        self.cmb_musteri.setStyleSheet(f"QComboBox{{{inp}}}")
        self.cmb_musteri.addItem("Tüm Müşteriler", None)
        self.cmb_musteri.currentIndexChanged.connect(self._filter)
        fl.addWidget(self.cmb_musteri)
        
        fl.addWidget(QLabel("Hat:", styleSheet=f"color:{self.text};"))
        self.cmb_hat = QComboBox()
        self.cmb_hat.setMinimumWidth(140)
        self.cmb_hat.setStyleSheet(f"QComboBox{{{inp}}}")
        self.cmb_hat.addItem("Tüm Hatlar", None)
        self.cmb_hat.currentIndexChanged.connect(self._filter)
        fl.addWidget(self.cmb_hat)
        
        fl.addWidget(QLabel("Durum:", styleSheet=f"color:{self.text};"))
        self.cmb_durum = QComboBox()
        self.cmb_durum.setMinimumWidth(140)
        self.cmb_durum.setStyleSheet(f"QComboBox{{{inp}}}")
        self.cmb_durum.addItems(["Tümü", "Geciken", "Bugün", "Yaklaşan", "Kalan Parça", "Üretimde"])
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        fl.addWidget(self.cmb_durum)
        
        fl.addWidget(QLabel("🔍", styleSheet=f"color:{self.text};"))
        self.txt_ara = QLineEdit()
        self.txt_ara.setPlaceholderText("Ara...")
        self.txt_ara.setMinimumWidth(150)
        self.txt_ara.setStyleSheet(f"QLineEdit{{{inp}}}")
        self.txt_ara.textChanged.connect(self._filter)
        fl.addWidget(self.txt_ara)
        
        self.chk_eksik = QCheckBox("Sadece Eksik")
        self.chk_eksik.setStyleSheet(f"color:{self.text};")
        self.chk_eksik.stateChanged.connect(self._filter)
        fl.addWidget(self.chk_eksik)
        fl.addStretch()
        
        btn_ref = QPushButton("🔄 Yenile")
        btn_ref.setCursor(Qt.PointingHandCursor)
        btn_ref.clicked.connect(self._load_data)
        btn_ref.setStyleSheet(f"QPushButton{{background:{self.primary};color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:bold;}}QPushButton:hover{{background:#06b6d4;}}")
        fl.addWidget(btn_ref)
        layout.addWidget(ff)
        
        # Splitter
        sp = QSplitter(Qt.Horizontal)
        sp.setStyleSheet(f"QSplitter::handle{{background:{self.border};width:2px;}}")
        
        # Sol - Müşteriler
        lf = QFrame()
        lf.setMinimumWidth(260)
        lf.setMaximumWidth(320)
        lf.setStyleSheet(f"QFrame{{background:{self.bg_card};border-radius:8px;}}")
        ll = QVBoxLayout(lf)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(0)
        lh = QLabel("  📊 MÜŞTERİ ÖZET")
        lh.setFixedHeight(40)
        lh.setStyleSheet(f"background:{self.primary};color:white;font-weight:bold;padding-left:12px;border-radius:8px 8px 0 0;")
        ll.addWidget(lh)
        self.tbl_must = QTableWidget()
        self.tbl_must.setColumnCount(4)
        self.tbl_must.setHorizontalHeaderLabels(["Müşteri", "Bek", "Gec", "Kal"])
        self.tbl_must.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 4):
            self.tbl_must.horizontalHeader().setSectionResizeMode(i, QHeaderView.Fixed)
            self.tbl_must.setColumnWidth(i, 45)
        self.tbl_must.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_must.verticalHeader().setVisible(False)
        self.tbl_must.itemSelectionChanged.connect(self._must_sec)
        self._tbl_style(self.tbl_must)
        ll.addWidget(self.tbl_must)
        sp.addWidget(lf)
        
        # Sağ - İş Emirleri
        rf = QFrame()
        rf.setStyleSheet(f"QFrame{{background:{self.bg_card};border-radius:8px;}}")
        rl = QVBoxLayout(rf)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        self.lbl_baslik = QLabel("  📋 TÜM İŞ EMİRLERİ")
        self.lbl_baslik.setFixedHeight(40)
        self.lbl_baslik.setStyleSheet(f"background:{self.primary};color:white;font-weight:bold;padding-left:12px;border-radius:8px 8px 0 0;")
        rl.addWidget(self.lbl_baslik)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"QTabWidget::pane{{border:none;background:{self.bg_card};}}QTabBar::tab{{background:{self.bg_main};color:{self.text_secondary};padding:10px 20px;}}QTabBar::tab:selected{{background:{self.bg_card};color:{self.primary};font-weight:bold;}}")
        
        # Liste Tab
        t1 = QWidget()
        t1l = QVBoxLayout(t1)
        t1l.setContentsMargins(0, 8, 0, 0)
        self.tbl_ie = QTableWidget()
        self.tbl_ie.setColumnCount(12)
        self.tbl_ie.setHorizontalHeaderLabels(["İş Emri", "Müşteri", "Stok Kodu", "Stok Adı", "Kaplama", "Miktar", "Üretilen", "Kalan", "Termin", "Gün", "Durum", "İlerleme"])
        for i, w in enumerate([100, 130, 90, 150, 80, 65, 65, 55, 80, 40, 80, 95]):
            self.tbl_ie.setColumnWidth(i, w)
        self.tbl_ie.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_ie.verticalHeader().setVisible(False)
        self.tbl_ie.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tbl_ie.customContextMenuRequested.connect(self._ctx_menu)
        self.tbl_ie.doubleClicked.connect(self._detay)
        self._tbl_style(self.tbl_ie)
        t1l.addWidget(self.tbl_ie)
        self.tabs.addTab(t1, "📋 Liste")
        
        # Kalan Tab
        t2 = QWidget()
        t2l = QVBoxLayout(t2)
        t2l.setContentsMargins(8, 8, 8, 8)
        wf = QFrame()
        wf.setStyleSheet(f"QFrame{{background:rgba(245,158,11,0.2);border:1px solid {self.warning};border-radius:6px;}}")
        wfl = QHBoxLayout(wf)
        wfl.setContentsMargins(12, 8, 12, 8)
        wfl.addWidget(QLabel(f"⚠️ <b>DİKKAT:</b> Eksik parça kalan işler!", styleSheet=f"color:{self.warning};"))
        wfl.addStretch()
        t2l.addWidget(wf)
        self.tbl_kalan = QTableWidget()
        self.tbl_kalan.setColumnCount(9)
        self.tbl_kalan.setHorizontalHeaderLabels(["İş Emri", "Müşteri", "Stok Kodu", "Toplam", "Üretilen", "Kalan", "Termin", "Bekleme", "Aksiyon"])
        for i, w in enumerate([100, 140, 100, 65, 65, 60, 80, 70, 85]):
            self.tbl_kalan.setColumnWidth(i, w)
        self.tbl_kalan.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_kalan.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_kalan)
        t2l.addWidget(self.tbl_kalan)
        self.tabs.addTab(t2, "🔴 Kalan Parçalar")
        
        # Takvim Tab
        t3 = QWidget()
        t3l = QVBoxLayout(t3)
        t3l.setContentsMargins(8, 8, 8, 8)
        self.tbl_tak = QTableWidget()
        self.tbl_tak.setColumnCount(7)
        today = QDate.currentDate()
        hdrs = [f"{['Pzt','Sal','Çar','Per','Cum','Cmt','Paz'][today.addDays(i).dayOfWeek()-1]}\n{today.addDays(i).toString('dd.MM')}" for i in range(7)]
        self.tbl_tak.setHorizontalHeaderLabels(hdrs)
        self.tbl_tak.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_tak.verticalHeader().setVisible(False)
        self._tbl_style(self.tbl_tak)
        t3l.addWidget(self.tbl_tak)
        self.tabs.addTab(t3, "📅 Takvim")
        
        rl.addWidget(self.tabs)
        
        # Alt Bar
        bb = QFrame()
        bb.setFixedHeight(50)
        bb.setStyleSheet(f"QFrame{{background:{self.bg_main};border-radius:0 0 8px 8px;}}")
        bbl = QHBoxLayout(bb)
        bbl.setContentsMargins(16, 8, 16, 8)
        self.lbl_gunc = QLabel("Son güncelleme: -", styleSheet=f"color:{self.text_muted};")
        bbl.addWidget(self.lbl_gunc)
        bbl.addStretch()
        btn_bild = QPushButton("📧 Toplu Bildirim")
        btn_bild.setCursor(Qt.PointingHandCursor)
        btn_bild.setStyleSheet(f"QPushButton{{background:{self.warning};color:white;border:none;border-radius:4px;padding:8px 16px;font-weight:bold;}}")
        btn_bild.clicked.connect(lambda: QMessageBox.information(self, "Bilgi", "Toplu bildirim özelliği aktif edilecek."))
        bbl.addWidget(btn_bild)
        btn_exc = QPushButton("📊 Excel")
        btn_exc.setCursor(Qt.PointingHandCursor)
        btn_exc.setStyleSheet(f"QPushButton{{background:{self.success};color:white;border:none;border-radius:4px;padding:8px 16px;font-weight:bold;}}")
        btn_exc.clicked.connect(self._excel)
        bbl.addWidget(btn_exc)
        rl.addWidget(bb)
        sp.addWidget(rf)
        sp.setSizes([280, 920])
        layout.addWidget(sp, 1)

    def _card(self, title, val, color):
        c = QFrame()
        c.setFixedHeight(85)
        c.setMinimumWidth(150)
        c.setStyleSheet(f"QFrame{{background:{self.bg_card};border-radius:10px;border-left:4px solid {color};}}QFrame:hover{{background:{self.bg_hover};}}")
        l = QVBoxLayout(c)
        l.setContentsMargins(12, 10, 12, 10)
        l.setSpacing(4)
        l.addWidget(QLabel(title, styleSheet=f"color:{self.text_muted};font-size:11px;font-weight:bold;"))
        lv = QLabel(val)
        lv.setObjectName("val")
        lv.setStyleSheet(f"color:{color};font-size:28px;font-weight:bold;")
        l.addWidget(lv)
        l.addStretch()
        return c

    def _tbl_style(self, t):
        t.setStyleSheet(f"QTableWidget{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:4px;gridline-color:{self.border};}}QTableWidget::item{{padding:6px;color:{self.text};}}QTableWidget::item:selected{{background:{self.primary};color:white;}}QHeaderView::section{{background:{self.bg_card};color:{self.text};padding:8px;border:none;font-weight:bold;border-bottom:2px solid {self.primary};}}")
        t.verticalHeader().setDefaultSectionSize(36)

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
        except: pass

    def _load_data(self):
        if not self.conn:
            try: self.conn = get_db_connection()
            except: return
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
                    it2.setForeground(QBrush(QColor(self.error)))
                    it2.setFont(QFont("", -1, QFont.Bold))
                it3 = QTableWidgetItem(str(k))
                it3.setTextAlignment(Qt.AlignCenter)
                if k > 0:
                    it3.setForeground(QBrush(QColor("#9b59b6")))
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
                    if gf < 0: rc = QColor("#3d1f1f")
                    elif gf == 0: rc = QColor("#3d3520")
                    elif gf <= 3: rc = QColor("#1f2d3d")
                if kl > 0 and ur and ur > 0: rc = QColor("#2d1f3d")
                its = [QTableWidgetItem(no or ""), QTableWidgetItem((mu or "")[:16]), QTableWidgetItem(sk or ""),
                       QTableWidgetItem((sa or "")[:18]), QTableWidgetItem(kp or ""), QTableWidgetItem(f"{tp:,.0f}" if tp else "0"),
                       QTableWidgetItem(f"{ur:,.0f}" if ur else "0"), QTableWidgetItem(f"{kl:,.0f}"),
                       QTableWidgetItem(tr.strftime("%d.%m.%Y") if tr else "-"), QTableWidgetItem(str(gf) if gf is not None else "-"),
                       QTableWidgetItem(du or "")]
                for j, it in enumerate(its):
                    it.setData(Qt.UserRole, ie_id)
                    if rc: it.setBackground(QBrush(rc))
                    if j in [5,6,7,9]: it.setTextAlignment(Qt.AlignCenter)
                    if j == 7 and kl > 0 and ur: it.setForeground(QBrush(QColor("#9b59b6"))); it.setFont(QFont("", -1, QFont.Bold))
                    if j == 9 and gf is not None and gf < 0: it.setForeground(QBrush(QColor(self.error))); it.setFont(QFont("", -1, QFont.Bold))
                    self.tbl_ie.setItem(i, j, it)
                pb = QProgressBar()
                pb.setRange(0, 100)
                pb.setValue(int(il))
                pb.setFormat(f"{il:.0f}%")
                pb.setStyleSheet(f"QProgressBar{{border:1px solid {self.border};border-radius:4px;text-align:center;background:{self.bg_main};color:{self.text};}}QProgressBar::chunk{{background:{self.success if il>=90 else self.primary if il>=50 else self.warning};border-radius:3px;}}")
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
                rc = QColor("#2d1f3d") if kl <= 5 else QColor("#3d3520")
                its = [QTableWidgetItem(no or ""), QTableWidgetItem((mu or "")[:18]), QTableWidgetItem(sk or ""),
                       QTableWidgetItem(f"{tp:,.0f}" if tp else "0"), QTableWidgetItem(f"{ur:,.0f}" if ur else "0"),
                       QTableWidgetItem(f"{kl:,.0f}"), QTableWidgetItem(tr.strftime("%d.%m.%Y") if tr else "-"),
                       QTableWidgetItem(f"{bk} gün" if bk > 0 else "-")]
                for j, it in enumerate(its):
                    it.setData(Qt.UserRole, ie_id)
                    it.setBackground(QBrush(rc))
                    if j in [3,4,5]: it.setTextAlignment(Qt.AlignCenter)
                    if j == 5: it.setForeground(QBrush(QColor("#9b59b6"))); it.setFont(QFont("", -1, QFont.Bold))
                    self.tbl_kalan.setItem(i, j, it)
                btn = QPushButton("🔔 Bildir")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet("QPushButton{background:#9b59b6;color:white;border:none;border-radius:4px;padding:4px 8px;font-size:11px;}QPushButton:hover{background:#8e44ad;}")
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
        except: pass

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
                        it.setBackground(QBrush(QColor("#1f2d3d")))
                    else:
                        it = QTableWidgetItem("")
                    self.tbl_tak.setItem(row, col, it)
            self.tbl_tak.verticalHeader().setDefaultSectionSize(50)
        except: pass

    def _filter(self):
        if self.conn:
            cur = self.conn.cursor()
            self._load_ie(cur)

    def _must_sec(self):
        sel = self.tbl_must.selectedItems()
        if sel:
            m = sel[0].data(Qt.UserRole)
            self.lbl_baslik.setText(f"  📋 {m[:25]}..." if len(m) > 25 else f"  📋 {m}")
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
        menu.setStyleSheet(f"QMenu{{background:{self.bg_card};border:1px solid {self.border};border-radius:4px;}}QMenu::item{{padding:8px 20px;color:{self.text};}}QMenu::item:selected{{background:{self.primary};color:white;}}")
        menu.addAction("📋 Detay").triggered.connect(lambda: self._show_det(ie_id))
        menu.addSeparator()
        menu.addAction("📝 Not Ekle").triggered.connect(lambda: self._add_not(ie_id))
        menu.addAction("✅ Tamamlandı").triggered.connect(lambda: self._tamam(ie_id))
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
        except: pass

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
