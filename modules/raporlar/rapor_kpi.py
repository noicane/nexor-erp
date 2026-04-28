# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Uretim KPI Formu (EPS.03 / FR.171)

Sureç: Uretim ve Planlama (EPS.03)
Form:  FR.171 Rev.4 (Yayin 2021-04-01)

7 gosterge:
    GSTR-1: Gerceklesen uretim adetleri (KTL/CINKO/TOZ BOYA)
    GSTR-2: Bara sayisi + adam basi aski (KTL/CINKO)
    GSTR-3: Hammadde tuketim (CINKO/KATAFOREZ/TOZ BOYA, kg)
    GSTR-4: Tuketim / m2 alan (KTL/CINKO/TOZ BOYA)
    GSTR-5: Bozuk parca / uretim orani
    GSTR-6: Enerji tuketim (Su/Elektrik/Dogalgaz)
    GSTR-7: Plan adherence (Gerceklesen/Planlanan*100)

NOT: Bu ekran su an YAPI olarak hazir, veriler bos goruntuleniyor.
Asamali olarak NEXOR uretim/kalite/PLC/lab/enerji modullerinden otomatik dolacak.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QGroupBox, QGridLayout, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QFont
from datetime import datetime

from components.base_page import BasePage
from core.nexor_brand import brand


AYLAR_KISA = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
              "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]


# ---- Gosterge tanimlari (formdan) ------------------------------------------
GOSTERGELER = [
    {
        "kod": "GSTR-1",
        "baslik": "Gerçekleşen Üretim Adetleri",
        "formul": "META ERP Gerçekleşen Üretim Analizi",
        "satirlar": [
            ("KTL Gerçekleşen Üretim Miktarı", "Adet"),
            ("Çinko Gerçekleşen Üretim Miktarı", "Adet"),
            ("Toz Boya Gerçekleşen Üretim Miktarı", "Adet"),
        ],
    },
    {
        "kod": "GSTR-2",
        "baslik": "Bara Sayısı / Personel Oranı",
        "formul": "Aylık ortalama bara + adam başı askı sayısı",
        "satirlar": [
            ("Bara Sayısı KATAFOREZ Aylık Ortalama", "Adet"),
            ("Bara/Personel KATAFOREZ (adam başı askı)", "Adet"),
            ("Bara Sayısı ÇİNKO Aylık Ortalama", "Adet"),
            ("Bara/Personel ÇİNKO (adam başı askı)", "Adet"),
        ],
    },
    {
        "kod": "GSTR-3",
        "baslik": "Hammadde Tüketim",
        "formul": "Banyo İlave Takip Formu (Lab)",
        "satirlar": [
            ("Çinko Hammadde Tüketim Aylık", "kg"),
            ("Kataforez Hammadde Tüketim Aylık", "kg"),
            ("Toz Boya Tüketim Aylık", "kg"),
        ],
    },
    {
        "kod": "GSTR-4",
        "baslik": "Aylık m² Alan + Tüketim / m²",
        "formul": "Kaplanan m² alan + Hammadde tüketim / m²",
        "satirlar": [
            ("KTL Aylık m² Alan", "m²"),
            ("Çinko Aylık m² Alan", "m²"),
            ("Toz Boya Aylık m² Alan", "m²"),
            ("KTL Tüketim / m² Alan", "kg/m²"),
            ("Çinko Tüketim / m² Alan", "kg/m²"),
            ("Toz Boya Tüketim / m² Alan", "kg/m²"),
        ],
    },
    {
        "kod": "GSTR-5",
        "baslik": "Bozuk Parça Oranı",
        "formul": "Bozuk Parça Miktarı / Üretim Miktarı",
        "satirlar": [
            ("Bozuk Parça Oranı KATAFOREZ", "%"),
            ("Bozuk Parça Oranı ÇİNKO", "%"),
            ("Bozuk Parça Oranı TOZ BOYA", "%"),
        ],
    },
    {
        "kod": "GSTR-6",
        "baslik": "Enerji Tüketim",
        "formul": "Faturalar (Su / Elektrik / Doğalgaz)",
        "satirlar": [
            ("Su Tüketim", "m³"),
            ("Elektrik Tüketim", "TL"),
            ("Doğalgaz", "Sm³"),
        ],
    },
    {
        "kod": "GSTR-7",
        "baslik": "Üretim Planına Uyum",
        "formul": "Gerçekleşen Üretim / Planlanan Üretim × 100",
        "satirlar": [
            ("Gerçekleşen Üretim", "Adet"),
            ("Planlanan Üretim", "Adet"),
            ("Plan Uyum Oranı", "%"),
        ],
    },
]


def _format_sayi(val) -> str:
    if val is None or val == "":
        return "—"
    try:
        f = float(val)
        if f == int(f):
            return f"{int(f):,}".replace(",", ".")
        return f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(val)


class GostergeKarti(QFrame):
    """Tek bir gosterge: baslik + 12 ayli tablo."""

    def __init__(self, gosterge: dict, parent=None):
        super().__init__(parent)
        self.gosterge = gosterge
        self.setObjectName("gosterge_karti")
        self.setStyleSheet(
            f"QFrame#gosterge_karti {{ background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 10px; }}"
        )
        self._setup_ui()

    def _setup_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(8)

        # Baslik satiri
        head = QHBoxLayout()
        head.setSpacing(10)

        kod_lbl = QLabel(self.gosterge["kod"])
        kod_lbl.setStyleSheet(
            f"background: {brand.PRIMARY_SOFT}; color: {brand.PRIMARY}; "
            f"font-weight: bold; font-size: 11px; padding: 3px 8px; border-radius: 4px;"
        )
        head.addWidget(kod_lbl)

        baslik_lbl = QLabel(self.gosterge["baslik"])
        baslik_lbl.setStyleSheet(f"color: {brand.TEXT}; font-size: 14px; font-weight: bold;")
        head.addWidget(baslik_lbl)

        head.addStretch()

        formul_lbl = QLabel(self.gosterge["formul"])
        formul_lbl.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px; font-style: italic;")
        head.addWidget(formul_lbl)

        v.addLayout(head)

        # Tablo: Detay | Birim | Hedef | 12 ay
        kolonlar = ["Detay Gelişim Göstergesi", "Birim", "Hedef"] + AYLAR_KISA
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(len(kolonlar))
        self.tbl.setHorizontalHeaderLabels(kolonlar)
        self.tbl.setRowCount(len(self.gosterge["satirlar"]))
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSelectionMode(QAbstractItemView.NoSelection)
        self.tbl.setFocusPolicy(Qt.NoFocus)
        self.tbl.setShowGrid(True)
        self.tbl.setStyleSheet(
            f"QTableWidget {{ background: {brand.BG_MAIN}; color: {brand.TEXT}; "
            f"gridline-color: {brand.BORDER}; border: 1px solid {brand.BORDER}; }}"
            f"QHeaderView::section {{ background: {brand.BG_CARD}; color: {brand.TEXT}; "
            f"padding: 6px; border: none; border-bottom: 2px solid {brand.PRIMARY}; "
            f"font-weight: bold; font-size: 11px; }}"
            f"QTableWidget::item {{ padding: 4px 6px; border-bottom: 1px solid {brand.BORDER}; }}"
        )

        # Kolon genislikleri
        h = self.tbl.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)        # Detay
        h.setSectionResizeMode(1, QHeaderView.Fixed)          # Birim
        h.setSectionResizeMode(2, QHeaderView.Fixed)          # Hedef
        self.tbl.setColumnWidth(1, 70)
        self.tbl.setColumnWidth(2, 90)
        for i in range(3, len(kolonlar)):
            h.setSectionResizeMode(i, QHeaderView.Fixed)
            self.tbl.setColumnWidth(i, 75)

        # Satirlari doldur (veriler bos)
        for r, (detay, birim) in enumerate(self.gosterge["satirlar"]):
            self.tbl.setItem(r, 0, QTableWidgetItem(detay))
            it = QTableWidgetItem(birim)
            it.setTextAlignment(Qt.AlignCenter)
            it.setForeground(QBrush(QColor(brand.TEXT_DIM)))
            self.tbl.setItem(r, 1, it)
            # Hedef bos
            it = QTableWidgetItem("—")
            it.setTextAlignment(Qt.AlignCenter)
            it.setForeground(QBrush(QColor(brand.TEXT_DIM)))
            self.tbl.setItem(r, 2, it)
            # 12 ay bos
            for c in range(12):
                it = QTableWidgetItem("—")
                it.setTextAlignment(Qt.AlignCenter)
                it.setForeground(QBrush(QColor(brand.TEXT_DIM)))
                self.tbl.setItem(r, 3 + c, it)
            self.tbl.setRowHeight(r, 30)

        self.tbl.setMinimumHeight(self.tbl.verticalHeader().length() +
                                   self.tbl.horizontalHeader().height() + 4)
        v.addWidget(self.tbl)

    def set_aylik_deger(self, satir_idx: int, ay_no: int, deger):
        """ay_no: 1..12. None/0 ise '—'."""
        if 1 <= ay_no <= 12 and 0 <= satir_idx < self.tbl.rowCount():
            it = QTableWidgetItem(_format_sayi(deger))
            it.setTextAlignment(Qt.AlignCenter)
            if deger is None or deger == "" or deger == 0:
                it.setForeground(QBrush(QColor(brand.TEXT_DIM)))
            else:
                it.setForeground(QBrush(QColor(brand.TEXT)))
            self.tbl.setItem(satir_idx, 2 + ay_no, it)

    def set_hedef(self, satir_idx: int, hedef):
        if 0 <= satir_idx < self.tbl.rowCount():
            it = QTableWidgetItem(_format_sayi(hedef))
            it.setTextAlignment(Qt.AlignCenter)
            it.setForeground(QBrush(QColor(brand.WARNING)))
            font = QFont(); font.setBold(True); it.setFont(font)
            self.tbl.setItem(satir_idx, 2, it)


class RaporKPIPage(BasePage):
    """EPS.03 Uretim KPI Formu (FR.171)."""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.kartlar = {}
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ---- Baslik / meta ----
        header = QFrame()
        header.setStyleSheet(f"background: {brand.BG_CARD}; border-radius: 12px;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 14, 20, 14)

        icon_frame = QFrame()
        icon_frame.setFixedSize(48, 48)
        icon_frame.setStyleSheet(f"background: {brand.PRIMARY_SOFT}; border-radius: 12px;")
        il = QVBoxLayout(icon_frame); il.setContentsMargins(0, 0, 0, 0)
        ic = QLabel("📈"); ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet("font-size: 22px; background: transparent;")
        il.addWidget(ic)
        hl.addWidget(icon_frame)

        title_box = QVBoxLayout()
        t = QLabel("Üretim KPI Formu")
        t.setStyleSheet(f"color: {brand.TEXT}; font-size: 18px; font-weight: bold;")
        title_box.addWidget(t)
        s = QLabel("Süreç: EPS.03 Üretim ve Planlama  |  Form: FR.171 Rev.4")
        s.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: 12px;")
        title_box.addWidget(s)
        hl.addLayout(title_box)
        hl.addStretch()

        # Yil secici
        hl.addWidget(QLabel("Yıl:", styleSheet=f"color: {brand.TEXT_MUTED}; font-weight: bold;"))
        self.yil_combo = QComboBox()
        gun = datetime.now().year
        for y in range(gun, gun - 6, -1):
            self.yil_combo.addItem(str(y), y)
        self.yil_combo.setStyleSheet(
            f"background: {brand.BG_MAIN}; color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 6px;"
        )
        hl.addWidget(self.yil_combo)

        btn_yenile = QPushButton("🔄 Veriyi Yenile")
        btn_yenile.setCursor(Qt.PointingHandCursor)
        btn_yenile.setStyleSheet(
            f"QPushButton {{ background: {brand.PRIMARY}; color: white; "
            f"font-weight: bold; padding: 8px 16px; border-radius: 8px; border: none; }}"
            f"QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}"
        )
        btn_yenile.clicked.connect(self._yenile)
        hl.addWidget(btn_yenile)

        # Yil degisince otomatik yenile
        self.yil_combo.currentIndexChanged.connect(lambda _: self._yenile())

        root.addWidget(header)

        # ---- Bilgi banner ----
        info = QLabel(
            "ℹ️  Bu ekran EPS.03 / FR.171 Rev.4 KPI formunun yapısıdır. "
            "Veriler aşamalı olarak NEXOR üretim, kalite, lab, PLC ve enerji modüllerinden otomatik bağlanacaktır."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            f"background: {brand.PRIMARY_SOFT}; color: {brand.TEXT}; "
            f"border-left: 4px solid {brand.PRIMARY}; padding: 10px 14px; border-radius: 6px;"
        )
        root.addWidget(info)

        # ---- Surec sekmesi (su an sadece Uretim, ileride baska surecler eklenebilir) ----
        self.surec_tabs = QTabWidget()
        self.surec_tabs.setStyleSheet(
            f"QTabWidget::pane {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; "
            f"border-radius: 10px; padding: 6px; }}"
            f"QTabBar::tab {{ background: {brand.BG_MAIN}; color: {brand.TEXT_MUTED}; "
            f"padding: 9px 18px; margin-right: 4px; border-top-left-radius: 8px; "
            f"border-top-right-radius: 8px; font-weight: bold; font-size: 12px; }}"
            f"QTabBar::tab:selected {{ background: {brand.BG_CARD}; color: {brand.PRIMARY}; }}"
        )

        # Uretim sekmesi: icinde GSTR-1..7 alt sekmeleri
        uretim_widget = QWidget()
        uretim_layout = QVBoxLayout(uretim_widget)
        uretim_layout.setContentsMargins(8, 8, 8, 8)
        uretim_layout.setSpacing(8)

        gosterge_tabs = QTabWidget()
        gosterge_tabs.setStyleSheet(
            f"QTabWidget::pane {{ background: {brand.BG_MAIN}; border: 1px solid {brand.BORDER}; "
            f"border-radius: 8px; padding: 8px; }}"
            f"QTabBar::tab {{ background: {brand.BG_CARD}; color: {brand.TEXT_MUTED}; "
            f"padding: 7px 14px; margin-right: 3px; border-top-left-radius: 6px; "
            f"border-top-right-radius: 6px; font-size: 11px; font-weight: bold; }}"
            f"QTabBar::tab:selected {{ background: {brand.BG_MAIN}; color: {brand.PRIMARY}; "
            f"border-bottom: 2px solid {brand.PRIMARY}; }}"
        )

        for g in GOSTERGELER:
            kart = GostergeKarti(g)
            self.kartlar[g["kod"]] = kart

            wrap = QWidget()
            wlay = QVBoxLayout(wrap)
            wlay.setContentsMargins(4, 4, 4, 4)
            wlay.addWidget(kart)
            wlay.addStretch()

            tab_label = f"{g['kod']}  {g['baslik']}"
            gosterge_tabs.addTab(wrap, tab_label)

        uretim_layout.addWidget(gosterge_tabs)
        self.surec_tabs.addTab(uretim_widget, "🏭  Üretim (EPS.03)")

        root.addWidget(self.surec_tabs, 1)

        # Acilista bir kez yenile
        self._yenile()

    def _yenile(self):
        """Secili yilin verilerini NEXOR'dan cek ve gostergelere doldur."""
        yil = self.yil_combo.currentData() or datetime.now().year

        try:
            from core.database import get_db_connection
            conn = get_db_connection()
            cur = conn.cursor()

            hat_case = """
                CASE
                    WHEN h.kod LIKE '%KTL%' THEN 'KTL'
                    WHEN h.kod LIKE '%ZNNI%' OR h.kod LIKE '%CINKO%' THEN 'CINKO'
                    WHEN h.kod LIKE '%Toz%' OR h.kod LIKE '%TOZ%' THEN 'TOZBOYA'
                    ELSE 'DIGER'
                END
            """
            hat_satir = {'KTL': 0, 'CINKO': 1, 'TOZBOYA': 2}

            # ============================================================
            # GSTR-1, GSTR-2 (asķı), GSTR-5 (fire): uretim.uretim_kayitlari
            # ============================================================
            cur.execute(f"""
                SELECT
                    MONTH(uk.tarih) AS ay,
                    {hat_case} AS hat_tipi,
                    SUM(uk.uretilen_miktar) AS uretim,
                    SUM(uk.fire_miktar)     AS fire,
                    SUM(uk.aski_sayisi)     AS aski
                FROM uretim.uretim_kayitlari uk
                LEFT JOIN tanim.uretim_hatlari h ON h.id = uk.hat_id
                WHERE YEAR(uk.tarih) = ?
                GROUP BY MONTH(uk.tarih), {hat_case}
            """, (yil,))

            uk_data = {}
            for ay, hat, uretim, fire, aski in cur.fetchall():
                uk_data[(hat, ay)] = {
                    'uretim': float(uretim) if uretim else 0,
                    'fire':   float(fire) if fire else 0,
                    'aski':   int(aski) if aski else 0,
                }

            gstr1 = self.kartlar.get('GSTR-1')
            gstr2 = self.kartlar.get('GSTR-2')
            gstr5 = self.kartlar.get('GSTR-5')

            for (hat, ay), v in uk_data.items():
                if hat in hat_satir:
                    if gstr1:
                        gstr1.set_aylik_deger(hat_satir[hat], ay, v['uretim'])
                if gstr2:
                    if hat == 'KTL':
                        gstr2.set_aylik_deger(0, ay, v['aski'])
                    elif hat == 'CINKO':
                        gstr2.set_aylik_deger(2, ay, v['aski'])

            # ============================================================
            # GSTR-5 Bozuk parca / Uretim - GERCEK kaynak: kalite.uretim_redler
            # ============================================================
            try:
                cur.execute(f"""
                    SELECT MONTH(ur.red_tarihi) AS ay,
                           {hat_case} AS hat,
                           SUM(ur.red_miktar) AS red
                    FROM kalite.uretim_redler ur
                    LEFT JOIN siparis.is_emirleri ie ON ie.id = ur.is_emri_id
                    LEFT JOIN tanim.uretim_hatlari h ON h.id = ie.hat_id
                    WHERE YEAR(ur.red_tarihi) = ?
                    GROUP BY MONTH(ur.red_tarihi), {hat_case}
                """, (yil,))
                if gstr5:
                    for ay, hat, red in cur.fetchall():
                        if hat in hat_satir and red:
                            uretim = uk_data.get((hat, ay), {}).get('uretim', 0)
                            if uretim > 0:
                                oran = float(red) / uretim * 100
                                gstr5.set_aylik_deger(hat_satir[hat], ay, round(oran, 3))
            except Exception:
                pass

            # ============================================================
            # GSTR-2 personel: ik.pdks_hareketler aktif personel sayisi
            # ============================================================
            try:
                cur.execute("""
                    SELECT MONTH(hareket_zamani) AS ay,
                           COUNT(DISTINCT personel_id) AS personel
                    FROM ik.pdks_hareketler
                    WHERE YEAR(hareket_zamani) = ?
                    GROUP BY MONTH(hareket_zamani)
                """, (yil,))
                personel_ay = {ay: int(p) for ay, p in cur.fetchall() if p}
                if gstr2 and personel_ay:
                    for ay, p in personel_ay.items():
                        if p > 0:
                            ktl_aski = uk_data.get(('KTL', ay), {}).get('aski', 0)
                            cnk_aski = uk_data.get(('CINKO', ay), {}).get('aski', 0)
                            if ktl_aski:
                                gstr2.set_aylik_deger(1, ay, round(ktl_aski / p, 2))
                            if cnk_aski:
                                gstr2.set_aylik_deger(3, ay, round(cnk_aski / p, 2))
            except Exception:
                pass  # PDKS verisi yok ise sessiz gec

            # ============================================================
            # GSTR-3 Hammadde tuketim: uretim.kimyasal_tuketim
            # banyo kod uzerinden hat tipi cikar
            # ============================================================
            kt_hat_case = """
                CASE
                    WHEN bt.kod LIKE '%KTL%' OR bt.kod LIKE '%KAT%' THEN 'KATAFOREZ'
                    WHEN bt.kod LIKE '%ZN%' OR bt.kod LIKE '%CINKO%' THEN 'CINKO'
                    WHEN bt.kod LIKE '%TOZ%' OR bt.kod LIKE '%BOYA%' THEN 'TOZBOYA'
                    ELSE 'DIGER'
                END
            """
            try:
                cur.execute(f"""
                    SELECT MONTH(kt.tarih) AS ay,
                           {kt_hat_case} AS hat,
                           SUM(kt.miktar) AS toplam_kg
                    FROM uretim.kimyasal_tuketim kt
                    LEFT JOIN uretim.banyo_tanimlari bt ON bt.id = kt.banyo_id
                    WHERE YEAR(kt.tarih) = ?
                    GROUP BY MONTH(kt.tarih), {kt_hat_case}
                """, (yil,))
                gstr3 = self.kartlar.get('GSTR-3')
                # GSTR-3 satir: 0=Cinko, 1=Kataforez, 2=Toz Boya
                kt_satir = {'CINKO': 0, 'KATAFOREZ': 1, 'TOZBOYA': 2}
                kt_data = {}
                for ay, hat, kg in cur.fetchall():
                    if hat in kt_satir:
                        kt_data[(hat, ay)] = float(kg) if kg else 0
                        if gstr3:
                            gstr3.set_aylik_deger(kt_satir[hat], ay, float(kg) if kg else 0)
            except Exception:
                kt_data = {}

            # ============================================================
            # GSTR-4 Tuketim / m2 alan
            # m2 alan = SUM(uretilen_miktar * urun.yuzey_alani_m2) by hat x ay
            # ============================================================
            try:
                cur.execute(f"""
                    SELECT MONTH(uk.tarih) AS ay,
                           {hat_case} AS hat_tipi,
                           SUM(uk.uretilen_miktar * ISNULL(u.yuzey_alani_m2, 0)) AS m2_alan
                    FROM uretim.uretim_kayitlari uk
                    LEFT JOIN tanim.uretim_hatlari h ON h.id = uk.hat_id
                    LEFT JOIN siparis.is_emirleri ie ON ie.id = uk.is_emri_id
                    LEFT JOIN stok.urunler u ON u.id = ie.urun_id
                    WHERE YEAR(uk.tarih) = ?
                    GROUP BY MONTH(uk.tarih), {hat_case}
                """, (yil,))
                m2_data = {}
                for ay, hat, m2 in cur.fetchall():
                    m2_data[(hat, ay)] = float(m2) if m2 else 0

                gstr4 = self.kartlar.get('GSTR-4')
                # GSTR-4 satirlar: 0=KTL m², 1=CINKO m², 2=TOZBOYA m²,
                #                  3=KTL kg/m², 4=CINKO kg/m², 5=TOZBOYA kg/m²
                if gstr4:
                    # m² alan satirlari (0, 1, 2)
                    for (uk_hat, ay), m2 in m2_data.items():
                        if uk_hat in hat_satir and m2 > 0:
                            gstr4.set_aylik_deger(hat_satir[uk_hat], ay, round(m2, 2))

                    # Tuketim/m² oran satirlari (3, 4, 5)
                    kt_to_uk = {'KATAFOREZ': 'KTL', 'CINKO': 'CINKO', 'TOZBOYA': 'TOZBOYA'}
                    for (kt_hat, ay), kg in kt_data.items():
                        uk_hat = kt_to_uk.get(kt_hat)
                        m2 = m2_data.get((uk_hat, ay), 0) if uk_hat else 0
                        if m2 > 0 and uk_hat in hat_satir:
                            gstr4.set_aylik_deger(3 + hat_satir[uk_hat], ay, round(kg / m2, 6))
            except Exception:
                pass

            # ============================================================
            # GSTR-6 Enerji: cevre.su_tuketimi + cevre.enerji_tuketimi
            # Satir: 0=Su (m3), 1=Elektrik (TL/kWh), 2=Dogalgaz (Sm3)
            # ============================================================
            gstr6 = self.kartlar.get('GSTR-6')
            try:
                cur.execute("""
                    SELECT MONTH(okuma_tarihi) AS ay,
                           SUM(guncel_okuma - ISNULL(onceki_okuma, 0)) AS m3
                    FROM cevre.su_tuketimi
                    WHERE YEAR(okuma_tarihi) = ?
                    GROUP BY MONTH(okuma_tarihi)
                """, (yil,))
                if gstr6:
                    for ay, m3 in cur.fetchall():
                        gstr6.set_aylik_deger(0, ay, float(m3) if m3 else 0)
            except Exception:
                pass

            try:
                cur.execute("""
                    SELECT MONTH(okuma_tarihi) AS ay,
                           CASE
                               WHEN enerji_tipi LIKE '%ELEK%' THEN 'ELEKTRIK'
                               WHEN enerji_tipi LIKE '%DOGAL%' OR enerji_tipi LIKE '%GAZ%' THEN 'DOGALGAZ'
                               ELSE 'DIGER'
                           END AS tip,
                           SUM(guncel_okuma - ISNULL(onceki_okuma, 0)) AS toplam
                    FROM cevre.enerji_tuketimi
                    WHERE YEAR(okuma_tarihi) = ?
                    GROUP BY MONTH(okuma_tarihi),
                           CASE
                               WHEN enerji_tipi LIKE '%ELEK%' THEN 'ELEKTRIK'
                               WHEN enerji_tipi LIKE '%DOGAL%' OR enerji_tipi LIKE '%GAZ%' THEN 'DOGALGAZ'
                               ELSE 'DIGER'
                           END
                """, (yil,))
                if gstr6:
                    en_satir = {'ELEKTRIK': 1, 'DOGALGAZ': 2}
                    for ay, tip, toplam in cur.fetchall():
                        if tip in en_satir:
                            gstr6.set_aylik_deger(en_satir[tip], ay, float(toplam) if toplam else 0)
            except Exception:
                pass

            # ============================================================
            # GSTR-7 Plan Uyumu: kaplama.plan_gorevler vs uretim_kayitlari
            # Plan: aski_sayisi (haftalik plan)
            # Gerceklesen: aski toplami uretim_kayitlari'ndan
            # Aylik: plan_haftalik.baslangic_tarihi'ne gore
            # ============================================================
            try:
                cur.execute("""
                    SELECT MONTH(ph.hafta_baslangic) AS ay,
                           SUM(pg.aski_sayisi) AS plan_aski
                    FROM kaplama.plan_gorevler pg
                    INNER JOIN kaplama.plan_haftalik ph ON ph.id = pg.plan_id
                    WHERE YEAR(ph.hafta_baslangic) = ?
                    GROUP BY MONTH(ph.hafta_baslangic)
                """, (yil,))
                plan_aylik = {ay: int(p) for ay, p in cur.fetchall() if p}

                gstr7 = self.kartlar.get('GSTR-7')
                if gstr7:
                    # Aylik gerceklesen toplam aski
                    gerc_aylik = {}
                    for (hat, ay), v in uk_data.items():
                        gerc_aylik[ay] = gerc_aylik.get(ay, 0) + v['aski']
                    for ay in range(1, 13):
                        gerc = gerc_aylik.get(ay, 0)
                        plan = plan_aylik.get(ay, 0)
                        if gerc:
                            gstr7.set_aylik_deger(0, ay, gerc)
                        if plan:
                            gstr7.set_aylik_deger(1, ay, plan)
                        if plan > 0:
                            gstr7.set_aylik_deger(2, ay, round(gerc / plan * 100, 2))
            except Exception:
                pass

            conn.close()

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Veri Yenile Hatasi", f"KPI verileri cekilemedi:\n{e}")
