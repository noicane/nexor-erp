# -*- coding: utf-8 -*-
"""
NEXOR ERP - OEE Dashboard (Genel Ekipman Etkinligi)

Kullanilabilirlik x Performans x Kalite. Hat/donem/vardiya filtreli.
6 buyuk kayip pareto'su altta.
"""
from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand
from core.oee_calculator import DurusKayipPareto, OEECalculator, OEESonuc


# ============================================================================
# YARDIMCILAR
# ============================================================================

def _renk_oee(yuzde: float) -> str:
    """OEE yuzdesine gore renk kodu."""
    if yuzde >= 0.85:
        return brand.SUCCESS  # Dunya klasi (>%85)
    if yuzde >= 0.60:
        return brand.WARNING  # Iyi
    if yuzde >= 0.40:
        return "#F97316"  # Orta
    return brand.ERROR  # Dusuk


def _format_dakika(dk: int) -> str:
    """Dakikayi 'X sa Y dk' formatinda goster."""
    if dk <= 0:
        return "-"
    sa = dk // 60
    d = dk % 60
    if sa > 0:
        return f"{sa} sa {d} dk"
    return f"{d} dk"


def _kpi_card(baslik: str, deger: str, renk: str, alt: str = "") -> QFrame:
    f = QFrame()
    f.setStyleSheet(
        f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; "
        f"border-radius: 10px; padding: 14px 18px; }}"
    )
    v = QVBoxLayout(f)
    v.setContentsMargins(12, 10, 12, 10)
    v.setSpacing(2)
    b = QLabel(baslik)
    b.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px; font-weight: bold;")
    d = QLabel(deger)
    d.setStyleSheet(f"color: {renk}; font-size: 28px; font-weight: bold;")
    v.addWidget(b)
    v.addWidget(d)
    if alt:
        a = QLabel(alt)
        a.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 10px;")
        a.setWordWrap(True)
        v.addWidget(a)
    return f


# ============================================================================
# ANA SAYFA
# ============================================================================

class UretimOEEPage(BasePage):
    """OEE Dashboard sayfasi."""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.theme = theme
        self.calc = OEECalculator()
        self._setup_ui()
        self._yukle()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Baslik
        baslik = QLabel("OEE Dashboard - Genel Ekipman Etkinligi")
        baslik.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {brand.TEXT};")
        layout.addWidget(baslik)

        # Filtre cubuğu
        filtre_frame = QFrame()
        filtre_frame.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; "
            f"border-radius: 8px; padding: 8px 12px; }}"
        )
        h = QHBoxLayout(filtre_frame)
        h.setContentsMargins(10, 6, 10, 6)
        h.setSpacing(10)

        h.addWidget(QLabel("Tarih:"))
        self.dt_baslangic = QDateEdit()
        self.dt_baslangic.setCalendarPopup(True)
        self.dt_baslangic.setDisplayFormat("dd.MM.yyyy")
        self.dt_baslangic.setDate(QDate.currentDate().addDays(-7))
        h.addWidget(self.dt_baslangic)

        h.addWidget(QLabel("-"))
        self.dt_bitis = QDateEdit()
        self.dt_bitis.setCalendarPopup(True)
        self.dt_bitis.setDisplayFormat("dd.MM.yyyy")
        self.dt_bitis.setDate(QDate.currentDate())
        h.addWidget(self.dt_bitis)

        h.addSpacing(20)
        h.addWidget(QLabel("Hat:"))
        self.cb_hat = QComboBox()
        self.cb_hat.addItem("Tum Hatlar", 0)
        self._hatlari_yukle_cb()
        h.addWidget(self.cb_hat, 1)

        h.addSpacing(10)
        h.addWidget(QLabel("Vardiya:"))
        self.cb_vardiya = QComboBox()
        self.cb_vardiya.addItem("Tum Vardiyalar", 0)
        self._vardiyalari_yukle_cb()
        h.addWidget(self.cb_vardiya)

        # Hizli butonlar
        h.addSpacing(10)
        for label, gun in [("Bugun", 0), ("7 gun", 7), ("30 gun", 30), ("90 gun", 90)]:
            b = QPushButton(label)
            b.setStyleSheet(self._btn_minor())
            b.clicked.connect(lambda _, g=gun: self._hizli_tarih(g))
            h.addWidget(b)

        b_uygula = QPushButton("UYGULA")
        b_uygula.setStyleSheet(
            f"QPushButton {{ background: {brand.PRIMARY}; color: white; border: none; "
            f"border-radius: 6px; padding: 8px 18px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}"
        )
        b_uygula.clicked.connect(self._yukle)
        h.addWidget(b_uygula)

        layout.addWidget(filtre_frame)

        # KPI ozet kartlari (donem geneli)
        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(10)
        layout.addLayout(self.kpi_row)

        # Hat bazli OEE tablosu
        gb_tbl = QGroupBox("Hat Bazli OEE Detayi")
        v_tbl = QVBoxLayout(gb_tbl)
        self.tbl = QTableWidget(0, 11)
        self.tbl.setHorizontalHeaderLabels([
            "Hat Kodu", "Hat Adi", "Plan", "Calisma", "Durus (OEE)",
            "Uretim", "Red", "Kullanilabilirlik", "Performans", "Kalite", "OEE"
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 8px;
                gridline-color: {brand.BORDER};
                alternate-background-color: {brand.BG_INPUT};
            }}
            QHeaderView::section {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                padding: 8px; border: none; font-weight: bold;
            }}
        """)
        self.tbl.verticalHeader().setDefaultSectionSize(38)
        v_tbl.addWidget(self.tbl)
        layout.addWidget(gb_tbl, 2)

        # Pareto tablosu
        gb_p = QGroupBox("6 Buyuk Kayip - Durus Pareto")
        v_p = QVBoxLayout(gb_p)
        self.tbl_pareto = QTableWidget(0, 6)
        self.tbl_pareto.setHorizontalHeaderLabels([
            "#", "Kategori", "Neden Kodu", "Aciklama", "Sure", "Pay"
        ])
        self.tbl_pareto.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tbl_pareto.verticalHeader().setVisible(False)
        self.tbl_pareto.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_pareto.setStyleSheet(self.tbl.styleSheet())
        v_p.addWidget(self.tbl_pareto)
        layout.addWidget(gb_p, 1)

    def _btn_minor(self) -> str:
        return (
            f"QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 6px; "
            f"padding: 6px 12px; font-size: 11px; }}"
            f"QPushButton:hover {{ background: {brand.BG_HOVER}; }}"
        )

    # ------------------------------------------------------------------
    # COMBO LOAD
    # ------------------------------------------------------------------

    def _hatlari_yukle_cb(self):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, kod, ad
                FROM tanim.uretim_hatlari
                WHERE aktif_mi = 1
                ORDER BY sira_no, id
            """)
            for r in cur.fetchall():
                self.cb_hat.addItem(f"{r[1]} - {r[2]}", r[0])
            conn.close()
        except Exception:
            pass

    def _vardiyalari_yukle_cb(self):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, kod, ad FROM tanim.vardiyalar
                WHERE aktif_mi = 1 ORDER BY id
            """)
            for r in cur.fetchall():
                self.cb_vardiya.addItem(f"{r[1]} - {r[2]}", r[0])
            conn.close()
        except Exception:
            pass

    def _hizli_tarih(self, gun: int):
        if gun == 0:
            self.dt_baslangic.setDate(QDate.currentDate())
            self.dt_bitis.setDate(QDate.currentDate())
        else:
            self.dt_bitis.setDate(QDate.currentDate())
            self.dt_baslangic.setDate(QDate.currentDate().addDays(-gun))
        self._yukle()

    # ------------------------------------------------------------------
    # VERI YUKLEME
    # ------------------------------------------------------------------

    def _yukle(self):
        bas = self.dt_baslangic.date().toPython()
        bit = self.dt_bitis.date().toPython()
        hat_id = self.cb_hat.currentData()
        vardiya_id = self.cb_vardiya.currentData()

        try:
            sonuclar = self.calc.hesapla(
                baslangic_tarihi=bas,
                bitis_tarihi=bit,
                hat_id=(hat_id if hat_id else None),
                vardiya_id=(vardiya_id if vardiya_id else None),
            )
            pareto = self.calc.pareto(
                baslangic_tarihi=bas,
                bitis_tarihi=bit,
                hat_id=(hat_id if hat_id else None),
            )
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hata", f"OEE hesaplama hatasi:\n{e}")
            return

        # KPI ozet
        self._kpi_yukle(sonuclar)
        # Tablo
        self._tablo_yukle(sonuclar)
        # Pareto
        self._pareto_yukle(pareto)

    def _kpi_yukle(self, sonuclar: list[OEESonuc]):
        # Eski kartlari temizle
        while self.kpi_row.count():
            it = self.kpi_row.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)

        # Donem geneli ortalama (agirlikli planli sure ile)
        toplam_plan = sum(s.planlanan_sure_dk for s in sonuclar) or 1
        ort_oee = sum(s.oee * s.planlanan_sure_dk for s in sonuclar) / toplam_plan
        ort_k = sum(s.kullanilabilirlik * s.planlanan_sure_dk for s in sonuclar) / toplam_plan
        ort_p = sum(s.performans * s.planlanan_sure_dk for s in sonuclar) / toplam_plan
        ort_q = sum(s.kalite * s.planlanan_sure_dk for s in sonuclar) / toplam_plan
        toplam_uretim = sum(s.uretilen_adet for s in sonuclar)
        toplam_red = sum(s.red_adet for s in sonuclar)
        toplam_durus = sum(s.durus_oee_etkili_dk for s in sonuclar)

        kartlar = [
            ("Genel OEE", f"%{ort_oee*100:.1f}", _renk_oee(ort_oee), self._oee_yorum(ort_oee)),
            ("Kullanilabilirlik", f"%{ort_k*100:.1f}", _renk_oee(ort_k), f"Toplam durus: {_format_dakika(toplam_durus)}"),
            ("Performans", f"%{ort_p*100:.1f}", _renk_oee(ort_p), f"Toplam uretim: {toplam_uretim}"),
            ("Kalite", f"%{ort_q*100:.1f}", _renk_oee(ort_q), f"Red: {toplam_red}"),
        ]
        for b, d, r, a in kartlar:
            self.kpi_row.addWidget(_kpi_card(b, d, r, a))
        self.kpi_row.addStretch()

    def _oee_yorum(self, oee: float) -> str:
        if oee >= 0.85:
            return "Dunya klasi (>%85)"
        if oee >= 0.60:
            return "Iyi seviyede"
        if oee >= 0.40:
            return "Orta - iyilestirme alani"
        return "Dusuk - acil aksiyon"

    def _tablo_yukle(self, sonuclar: list[OEESonuc]):
        self.tbl.setRowCount(0)
        for s in sonuclar:
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)

            self.tbl.setItem(r, 0, QTableWidgetItem(s.hat_kodu))
            self.tbl.setItem(r, 1, QTableWidgetItem(s.hat_adi))
            self.tbl.setItem(r, 2, self._sayi_item(_format_dakika(s.planlanan_sure_dk)))
            self.tbl.setItem(r, 3, self._sayi_item(_format_dakika(s.calisma_sure_dk)))
            self.tbl.setItem(r, 4, self._sayi_item(_format_dakika(s.durus_oee_etkili_dk)))
            self.tbl.setItem(r, 5, self._sayi_item(str(s.uretilen_adet)))
            self.tbl.setItem(r, 6, self._sayi_item(str(s.red_adet)))
            self.tbl.setItem(r, 7, self._yuzde_item(s.kullanilabilirlik))
            self.tbl.setItem(r, 8, self._yuzde_item(s.performans))
            self.tbl.setItem(r, 9, self._yuzde_item(s.kalite))
            self.tbl.setItem(r, 10, self._oee_item(s.oee))

    def _sayi_item(self, txt: str) -> QTableWidgetItem:
        it = QTableWidgetItem(txt)
        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return it

    def _yuzde_item(self, oran: float) -> QTableWidgetItem:
        it = QTableWidgetItem(f"%{oran*100:.1f}")
        it.setTextAlignment(Qt.AlignCenter)
        renk = _renk_oee(oran)
        it.setForeground(QColor(renk))
        return it

    def _oee_item(self, oee: float) -> QTableWidgetItem:
        it = QTableWidgetItem(f"%{oee*100:.1f}")
        it.setTextAlignment(Qt.AlignCenter)
        renk = _renk_oee(oee)
        it.setForeground(QColor(renk))
        f = it.font()
        f.setBold(True)
        it.setFont(f)
        return it

    def _pareto_yukle(self, kayitlar: list[DurusKayipPareto]):
        self.tbl_pareto.setRowCount(0)
        for i, p in enumerate(kayitlar, start=1):
            r = self.tbl_pareto.rowCount()
            self.tbl_pareto.insertRow(r)
            self.tbl_pareto.setItem(r, 0, self._sayi_item(str(i)))

            kat_it = QTableWidgetItem(p.kategori)
            kat_renk = {
                "ARIZA": brand.ERROR, "KALITE": brand.WARNING,
                "PLANLI": brand.INFO, "MALZEME": "#A855F7",
            }.get(p.kategori, brand.TEXT_DIM)
            kat_it.setForeground(QColor(kat_renk))
            self.tbl_pareto.setItem(r, 1, kat_it)

            self.tbl_pareto.setItem(r, 2, QTableWidgetItem(p.neden_kodu))
            self.tbl_pareto.setItem(r, 3, QTableWidgetItem(p.neden_adi))
            self.tbl_pareto.setItem(r, 4, self._sayi_item(_format_dakika(p.sure_dk)))
            self.tbl_pareto.setItem(r, 5, self._sayi_item(f"%{p.yuzde*100:.1f}"))
