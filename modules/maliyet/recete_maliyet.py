# -*- coding: utf-8 -*-
"""
NEXOR ERP - Recete Maliyet Karti (A2)

Her recete icin standart birim parca maliyetini bilesen bilesen tanimla:
hammadde + iscilik + enerji + kimyasal + MOH = toplam.
"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDoubleSpinBox, QFormLayout, QFrame, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton,
    QScrollArea, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from components.base_page import BasePage
from core.database import get_db_connection
from core.maliyet_calculator import ReceteMaliyetCalculator, ReceteMaliyetSonuc
from core.nexor_brand import brand
from core.ui_components import (
    make_kpi_card, make_scrollable_form, setup_data_table,
    setup_form, standart_stylesheet,
)


_PARA_BIRIMLERI = ["TRY", "USD", "EUR"]


class ReceteMaliyetPage(BasePage):
    """Recete maliyet karti - liste + bilesen formu."""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.theme = theme
        self.calc = ReceteMaliyetCalculator()
        self._aktif_recete_no = None
        self._setup_ui()
        self._listeyi_yukle()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        # NEXOR standart stylesheet (input min-height, groupbox, focus, vb.)
        self.setStyleSheet(standart_stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Baslik + ust toolbar
        h_top = QHBoxLayout()
        baslik = QLabel("Recete Maliyet Karti")
        baslik.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {brand.TEXT};")
        h_top.addWidget(baslik)
        h_top.addStretch()

        self.btn_cache_yenile = QPushButton("Tum Receteler Icin Cache Yenile")
        self.btn_cache_yenile.setStyleSheet(self._btn_primary())
        self.btn_cache_yenile.clicked.connect(self._cache_yenile)
        h_top.addWidget(self.btn_cache_yenile)
        layout.addLayout(h_top)

        # Splitter: sol liste, sag form
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)

        # ============ SOL: Liste (sadelestirildi 4 kolon) ============
        sol = QWidget()
        v_sol = QVBoxLayout(sol)
        v_sol.setContentsMargins(0, 0, 4, 0)
        v_sol.setSpacing(0)

        self.tbl = QTableWidget(0, 4)
        self.tbl.setHorizontalHeaderLabels([
            "Recete No", "Adi", "Cevrim", "Toplam Maliyet"
        ])
        # Sabit kolonlar
        self.tbl.setColumnWidth(0, 70)
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.tbl.setColumnWidth(2, 75)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tbl.setColumnWidth(3, 130)
        self.tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        # Standart tablo stili + selection mode + alternating
        setup_data_table(self.tbl, stretch_kolon_indexi=1, satir_yuksekligi=32)
        self.tbl.itemSelectionChanged.connect(self._secim_degisti)
        v_sol.addWidget(self.tbl)
        splitter.addWidget(sol)

        # ============ SAG: Form (ScrollArea icinde) ============
        sag = QWidget()
        v_sag = QVBoxLayout(sag)
        v_sag.setContentsMargins(4, 0, 0, 0)
        v_sag.setSpacing(10)

        # Recete bilgi seridi (sticky top)
        self.lbl_recete_basinda = QLabel("Soldan bir recete secin")
        self.lbl_recete_basinda.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {brand.PRIMARY}; "
            f"padding: 8px 12px; background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 6px;"
        )
        v_sag.addWidget(self.lbl_recete_basinda)

        # ScrollArea standart wrapper
        scroll = make_scrollable_form()
        v_inner = scroll.widget().layout()

        # 1. Hammadde
        gb_h = QGroupBox("Hammadde")
        f_h = QFormLayout(gb_h)
        setup_form(f_h)
        self.sp_hammadde_fiyat = self._money_spin()
        f_h.addRow("Birim Fiyat (TL/kg):", self.sp_hammadde_fiyat)
        self.sp_hammadde_tuketim = self._kg_spin()
        f_h.addRow("Tuketim (kg/parca):", self.sp_hammadde_tuketim)
        v_inner.addWidget(gb_h)

        # 2. Iscilik
        gb_i = QGroupBox("Iscilik")
        f_i = QFormLayout(gb_i)
        setup_form(f_i)
        self.sp_iscilik_ucret = self._money_spin()
        f_i.addRow("Saat Ucreti (TL/saat):", self.sp_iscilik_ucret)
        self.sp_iscilik_kisi = QDoubleSpinBox()
        self.sp_iscilik_kisi.setRange(0.5, 20)
        self.sp_iscilik_kisi.setDecimals(2)
        self.sp_iscilik_kisi.setValue(1)
        f_i.addRow("Eszamanli Kisi:", self.sp_iscilik_kisi)
        self.sp_aski_kapasite = QSpinBox()
        self.sp_aski_kapasite.setRange(1, 9999)
        self.sp_aski_kapasite.setValue(1)
        f_i.addRow("1 Askıdaki Parca:", self.sp_aski_kapasite)
        v_inner.addWidget(gb_i)

        # 3. Enerji
        gb_e = QGroupBox("Enerji")
        f_e = QFormLayout(gb_e)
        setup_form(f_e)
        self.sp_enerji_kwh = self._kg_spin()
        f_e.addRow("Ortalama kWh/saat:", self.sp_enerji_kwh)
        self.sp_enerji_fiyat = self._money_spin()
        f_e.addRow("Birim Fiyat (TL/kWh):", self.sp_enerji_fiyat)
        v_inner.addWidget(gb_e)

        # 4. Kimyasal
        gb_k = QGroupBox("Kimyasal")
        f_k = QFormLayout(gb_k)
        setup_form(f_k)
        self.sp_kim_tuketim = self._kg_spin()
        f_k.addRow("Tuketim (kg/parca):", self.sp_kim_tuketim)
        self.sp_kim_fiyat = self._money_spin()
        f_k.addRow("Birim Fiyat (TL/kg):", self.sp_kim_fiyat)
        v_inner.addWidget(gb_k)

        # 5. MOH + Marj
        gb_m = QGroupBox("Genel Uretim Gideri (MOH) + Kar Marji")
        f_m = QFormLayout(gb_m)
        setup_form(f_m)
        self.sp_moh_yuzde = QDoubleSpinBox()
        self.sp_moh_yuzde.setRange(0, 200)
        self.sp_moh_yuzde.setDecimals(2)
        self.sp_moh_yuzde.setSuffix(" %")
        f_m.addRow("MOH Yuzdesi (DM+DL+E+K uzerine):", self.sp_moh_yuzde)
        self.sp_moh_sabit = self._money_spin()
        f_m.addRow("MOH Sabit (TL/parca):", self.sp_moh_sabit)
        self.sp_kar_marj = QDoubleSpinBox()
        self.sp_kar_marj.setRange(0, 1000)
        self.sp_kar_marj.setDecimals(2)
        self.sp_kar_marj.setSuffix(" %")
        f_m.addRow("Kar Marji (Satis icin):", self.sp_kar_marj)
        self.cb_para = QComboBox()
        self.cb_para.addItems(_PARA_BIRIMLERI)
        f_m.addRow("Para Birimi:", self.cb_para)
        self.dt_baslangic = QDateEdit()
        self.dt_baslangic.setCalendarPopup(True)
        self.dt_baslangic.setDisplayFormat("dd.MM.yyyy")
        self.dt_baslangic.setDate(QDate.currentDate())
        f_m.addRow("Gecerlilik Baslangic:", self.dt_baslangic)
        v_inner.addWidget(gb_m)

        # Notlar
        gb_n = QGroupBox("Notlar")
        v_n = QVBoxLayout(gb_n)
        v_n.setContentsMargins(14, 18, 14, 14)
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(70)
        self.txt_notlar.setPlaceholderText("Notlar (opsiyonel)")
        v_n.addWidget(self.txt_notlar)
        v_inner.addWidget(gb_n)

        v_inner.addStretch()
        v_sag.addWidget(scroll, 1)

        # Hesap onizleme kartlari (sticky bottom)
        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(8)
        v_sag.addLayout(self.kpi_row)

        # Butonlar (sticky bottom)
        h_btn = QHBoxLayout()
        h_btn.addStretch()
        self.btn_hesapla = QPushButton("Onizle")
        self.btn_hesapla.setStyleSheet(self._btn_minor())
        self.btn_hesapla.clicked.connect(self._onizle)
        h_btn.addWidget(self.btn_hesapla)

        self.btn_kaydet = QPushButton("Kaydet ve Cache Yenile")
        self.btn_kaydet.setStyleSheet(self._btn_primary())
        self.btn_kaydet.clicked.connect(self._kaydet)
        h_btn.addWidget(self.btn_kaydet)
        v_sag.addLayout(h_btn)

        splitter.addWidget(sag)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([400, 800])
        layout.addWidget(splitter, 1)

        # Baslangicta form devre disi
        self._form_disable(True)

    def _money_spin(self) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(0, 99_999_999)
        s.setDecimals(4)
        s.setSuffix(" TL")
        return s

    def _kg_spin(self) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(0, 999_999)
        s.setDecimals(4)
        return s

    def _btn_primary(self) -> str:
        return (
            f"QPushButton {{ background: {brand.PRIMARY}; color: white; border: none; "
            f"border-radius: 6px; padding: 8px 14px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}"
            f"QPushButton:disabled {{ background: {brand.BG_HOVER}; color: {brand.TEXT_DIM}; }}"
        )

    def _btn_minor(self) -> str:
        return (
            f"QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 6px; "
            f"padding: 8px 12px; }}"
            f"QPushButton:hover {{ background: {brand.BG_HOVER}; }}"
        )

    def _tbl_style(self) -> str:
        return f"""
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
            QTableWidget::item:selected {{
                background: {brand.PRIMARY_SOFT};
                color: {brand.TEXT};
            }}
        """

    # ------------------------------------------------------------------
    # LISTE
    # ------------------------------------------------------------------

    def _listeyi_yukle(self):
        """Recete listesi: 4 kolon (No / Adi / Cevrim / Toplam Maliyet)."""
        self.tbl.setRowCount(0)
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT r.recete_no,
                       ISNULL(NULLIF(LTRIM(RTRIM(r.recete_adi)), ''), '(adsiz)') AS adi,
                       ISNULL(r.toplam_sure_dk, 0) AS sure,
                       c.m_toplam, c.para_birimi
                FROM kaplama.plc_recete_tanimlari r
                LEFT JOIN maliyet.recete_maliyet_cache c ON c.recete_no = r.recete_no
                ORDER BY r.recete_no
            """)
            for row in cur.fetchall():
                r = self.tbl.rowCount()
                self.tbl.insertRow(r)
                self.tbl.setItem(r, 0, self._sayi_item(str(row[0])))
                self.tbl.setItem(r, 1, QTableWidgetItem(row[1] or ''))
                self.tbl.setItem(r, 2, self._sayi_item(f"{float(row[2]):.0f} dk"))
                if row[3] is not None:
                    para = row[4] or 'TRY'
                    txt = f"{float(row[3]):,.4f} {para}".replace(",", "X").replace(".", ",").replace("X", ".")
                    self.tbl.setItem(r, 3, self._toplam_item_text(txt))
                else:
                    it = QTableWidgetItem("- (bilesen yok)")
                    it.setForeground(QColor(brand.TEXT_DIM))
                    it.setTextAlignment(Qt.AlignCenter)
                    self.tbl.setItem(r, 3, it)
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Recete listesi yuklenemedi:\n{e}")

    def _sayi_item(self, txt: str) -> QTableWidgetItem:
        it = QTableWidgetItem(txt)
        it.setTextAlignment(Qt.AlignCenter)
        return it

    def _tl_item(self, v: float) -> QTableWidgetItem:
        it = QTableWidgetItem(f"{v:,.4f}".replace(",", "X").replace(".", ",").replace("X", "."))
        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return it

    def _toplam_item(self, v: float) -> QTableWidgetItem:
        it = self._tl_item(v)
        f = it.font()
        f.setBold(True)
        it.setFont(f)
        it.setForeground(QColor(brand.PRIMARY))
        return it

    def _toplam_item_text(self, txt: str) -> QTableWidgetItem:
        it = QTableWidgetItem(txt)
        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        f = it.font()
        f.setBold(True)
        it.setFont(f)
        it.setForeground(QColor(brand.PRIMARY))
        return it

    # ------------------------------------------------------------------
    # SECIM + FORM YUKLE
    # ------------------------------------------------------------------

    def _secim_degisti(self):
        r = self.tbl.currentRow()
        if r < 0:
            return
        recete_no_item = self.tbl.item(r, 0)
        if not recete_no_item:
            return
        try:
            recete_no = int(recete_no_item.text())
        except ValueError:
            return
        self._aktif_recete_no = recete_no
        self._form_disable(False)
        self._formu_yukle(recete_no)

    def _form_disable(self, disabled: bool):
        for w in [self.sp_hammadde_fiyat, self.sp_hammadde_tuketim,
                  self.sp_iscilik_ucret, self.sp_iscilik_kisi, self.sp_aski_kapasite,
                  self.sp_enerji_kwh, self.sp_enerji_fiyat,
                  self.sp_kim_tuketim, self.sp_kim_fiyat,
                  self.sp_moh_yuzde, self.sp_moh_sabit, self.sp_kar_marj,
                  self.cb_para, self.dt_baslangic, self.txt_notlar,
                  self.btn_hesapla, self.btn_kaydet]:
            w.setDisabled(disabled)

    def _formu_yukle(self, recete_no: int):
        """Mevcut aktif bileseni form alanlarina yerlestir."""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT TOP 1 hammadde_birim_fiyat, hammadde_tuketim_kg,
                       iscilik_saat_ucreti, iscilik_kisi_sayisi, aski_parca_kapasitesi,
                       enerji_kwh_per_saat, enerji_birim_fiyat,
                       kimyasal_tuketim_kg, kimyasal_birim_fiyat,
                       moh_yuzde, moh_sabit_tutar, kar_marj_yuzde, para_birimi,
                       gecerlilik_baslangic, ISNULL(notlar, ''),
                       recete_adi, ISNULL(toplam_sure_dk, 0)
                FROM maliyet.recete_bilesenleri b
                INNER JOIN kaplama.plc_recete_tanimlari r ON r.recete_no = b.recete_no
                WHERE b.recete_no = ?
                  AND (b.gecerlilik_bitis IS NULL OR b.gecerlilik_bitis >= CAST(GETDATE() AS date))
                ORDER BY b.gecerlilik_baslangic DESC
            """, recete_no)
            r = cur.fetchone()
            if r:
                self.sp_hammadde_fiyat.setValue(float(r[0] or 0))
                self.sp_hammadde_tuketim.setValue(float(r[1] or 0))
                self.sp_iscilik_ucret.setValue(float(r[2] or 0))
                self.sp_iscilik_kisi.setValue(float(r[3] or 1))
                self.sp_aski_kapasite.setValue(int(r[4] or 1))
                self.sp_enerji_kwh.setValue(float(r[5] or 0))
                self.sp_enerji_fiyat.setValue(float(r[6] or 0))
                self.sp_kim_tuketim.setValue(float(r[7] or 0))
                self.sp_kim_fiyat.setValue(float(r[8] or 0))
                self.sp_moh_yuzde.setValue(float(r[9] or 0))
                self.sp_moh_sabit.setValue(float(r[10] or 0))
                self.sp_kar_marj.setValue(float(r[11] or 0))
                self.cb_para.setCurrentText(r[12] or 'TRY')
                if r[13]:
                    qd = QDate(r[13].year, r[13].month, r[13].day)
                    self.dt_baslangic.setDate(qd)
                self.txt_notlar.setPlainText(r[14] or '')
                self.lbl_recete_basinda.setText(
                    f"Recete {recete_no} - {r[15] or ''}  ·  Cevrim: {float(r[16]):.0f} dk"
                )
            else:
                # Sifirla
                for s in [self.sp_hammadde_fiyat, self.sp_hammadde_tuketim,
                          self.sp_iscilik_ucret,
                          self.sp_enerji_kwh, self.sp_enerji_fiyat,
                          self.sp_kim_tuketim, self.sp_kim_fiyat,
                          self.sp_moh_yuzde, self.sp_moh_sabit, self.sp_kar_marj]:
                    s.setValue(0)
                self.sp_iscilik_kisi.setValue(1)
                self.sp_aski_kapasite.setValue(1)
                self.cb_para.setCurrentText('TRY')
                self.dt_baslangic.setDate(QDate.currentDate())
                self.txt_notlar.clear()

                # Recete bilgisi
                cur.execute("""
                    SELECT recete_adi, ISNULL(toplam_sure_dk, 0)
                    FROM kaplama.plc_recete_tanimlari WHERE recete_no = ?
                """, recete_no)
                rr = cur.fetchone()
                if rr:
                    self.lbl_recete_basinda.setText(
                        f"Recete {recete_no} - {rr[0] or ''}  ·  Cevrim: {float(rr[1]):.0f} dk  (yeni bilesen kaydi)"
                    )
                else:
                    self.lbl_recete_basinda.setText(f"Recete {recete_no} (yeni)")
            conn.close()
            self._onizle()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Form yuklenemedi: {e}")

    # ------------------------------------------------------------------
    # ONIZLE / KAYDET
    # ------------------------------------------------------------------

    def _onizle(self):
        if self._aktif_recete_no is None:
            return
        # Onizleme: form degerlerini bir gecici ReceteMaliyetSonuc'a hesaplat
        # En basit yol: bilesen DB'ye yaz kaydetmeden -> calculator cagir
        # Bu UI'da: form'dan dogrudan formul ile hesap, DB'ye gitmeden
        recete_no = self._aktif_recete_no
        cevrim_dk = self._cevrim_dk(recete_no)
        aski_kap = max(1, self.sp_aski_kapasite.value())

        m_hammadde = self.sp_hammadde_fiyat.value() * self.sp_hammadde_tuketim.value()
        m_iscilik = (self.sp_iscilik_ucret.value() * cevrim_dk * self.sp_iscilik_kisi.value()) / (60.0 * aski_kap) if cevrim_dk > 0 else 0.0
        m_enerji = (self.sp_enerji_kwh.value() * (cevrim_dk / 60.0) * self.sp_enerji_fiyat.value()) / aski_kap if cevrim_dk > 0 else 0.0
        m_kimyasal = self.sp_kim_tuketim.value() * self.sp_kim_fiyat.value()
        ara = m_hammadde + m_iscilik + m_enerji + m_kimyasal
        m_moh = (ara * self.sp_moh_yuzde.value() / 100.0) + self.sp_moh_sabit.value()
        m_toplam = ara + m_moh
        m_satis = m_toplam * (1 + self.sp_kar_marj.value() / 100.0)

        para = self.cb_para.currentText()
        # KPI kartlarini yenile
        while self.kpi_row.count():
            it = self.kpi_row.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)
        self.kpi_row.addWidget(make_kpi_card("Hammadde", f"{m_hammadde:,.4f} {para}".replace(",", "X").replace(".", ",").replace("X", "."), brand.INFO))
        self.kpi_row.addWidget(make_kpi_card("Iscilik", f"{m_iscilik:,.4f} {para}".replace(",", "X").replace(".", ",").replace("X", "."), brand.INFO))
        self.kpi_row.addWidget(make_kpi_card("Enerji", f"{m_enerji:,.4f} {para}".replace(",", "X").replace(".", ",").replace("X", "."), brand.WARNING))
        self.kpi_row.addWidget(make_kpi_card("Kimyasal", f"{m_kimyasal:,.4f} {para}".replace(",", "X").replace(".", ",").replace("X", "."), brand.INFO))
        self.kpi_row.addWidget(make_kpi_card("MOH", f"{m_moh:,.4f} {para}".replace(",", "X").replace(".", ",").replace("X", "."), brand.TEXT_DIM))
        self.kpi_row.addWidget(make_kpi_card("TOPLAM", f"{m_toplam:,.4f} {para}".replace(",", "X").replace(".", ",").replace("X", "."), brand.PRIMARY))
        self.kpi_row.addWidget(make_kpi_card(f"Satis (+%{self.sp_kar_marj.value():.1f})", f"{m_satis:,.4f} {para}".replace(",", "X").replace(".", ",").replace("X", "."), brand.SUCCESS))

    def _cevrim_dk(self, recete_no: int) -> float:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT ISNULL(toplam_sure_dk, 0) FROM kaplama.plc_recete_tanimlari WHERE recete_no = ?", recete_no)
            r = cur.fetchone()
            conn.close()
            return float(r[0]) if r else 0.0
        except Exception:
            return 0.0

    def _kaydet(self):
        if self._aktif_recete_no is None:
            return
        bas_qd = self.dt_baslangic.date()
        bas_d = bas_qd.toPython()
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # Mevcut aktif bileseni kapat (gecerlilik_bitis = bas-1 gun)
            cur.execute("""
                UPDATE maliyet.recete_bilesenleri
                SET gecerlilik_bitis = DATEADD(day, -1, ?)
                WHERE recete_no = ? AND gecerlilik_bitis IS NULL
                  AND gecerlilik_baslangic < ?
            """, bas_d, self._aktif_recete_no, bas_d)

            # Mevcut aktif bilesen ayni baslangic_tarihine sahipse update
            cur.execute("""
                SELECT id FROM maliyet.recete_bilesenleri
                WHERE recete_no = ? AND gecerlilik_baslangic = ?
            """, self._aktif_recete_no, bas_d)
            r = cur.fetchone()

            params = [
                float(self.sp_hammadde_fiyat.value()),
                float(self.sp_hammadde_tuketim.value()),
                float(self.sp_iscilik_ucret.value()),
                float(self.sp_iscilik_kisi.value()),
                int(self.sp_aski_kapasite.value()),
                float(self.sp_enerji_kwh.value()),
                float(self.sp_enerji_fiyat.value()),
                float(self.sp_kim_tuketim.value()),
                float(self.sp_kim_fiyat.value()),
                float(self.sp_moh_yuzde.value()),
                float(self.sp_moh_sabit.value()),
                float(self.sp_kar_marj.value()),
                self.cb_para.currentText(),
                self.txt_notlar.toPlainText().strip() or None,
            ]

            if r:
                cur.execute("""
                    UPDATE maliyet.recete_bilesenleri
                    SET hammadde_birim_fiyat=?, hammadde_tuketim_kg=?,
                        iscilik_saat_ucreti=?, iscilik_kisi_sayisi=?, aski_parca_kapasitesi=?,
                        enerji_kwh_per_saat=?, enerji_birim_fiyat=?,
                        kimyasal_tuketim_kg=?, kimyasal_birim_fiyat=?,
                        moh_yuzde=?, moh_sabit_tutar=?, kar_marj_yuzde=?,
                        para_birimi=?, notlar=?, guncelleme_tarihi=SYSDATETIME(),
                        gecerlilik_bitis=NULL
                    WHERE id = ?
                """, *params, r[0])
            else:
                cur.execute("""
                    INSERT INTO maliyet.recete_bilesenleri
                    (recete_no, gecerlilik_baslangic, gecerlilik_bitis,
                     hammadde_birim_fiyat, hammadde_tuketim_kg,
                     iscilik_saat_ucreti, iscilik_kisi_sayisi, aski_parca_kapasitesi,
                     enerji_kwh_per_saat, enerji_birim_fiyat,
                     kimyasal_tuketim_kg, kimyasal_birim_fiyat,
                     moh_yuzde, moh_sabit_tutar, kar_marj_yuzde,
                     para_birimi, notlar)
                    VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, self._aktif_recete_no, bas_d, *params)
            conn.commit()
            conn.close()

            # Cache'i bu recete icin yenile
            sonuc = self.calc.hesapla_tek(self._aktif_recete_no, bas_d)
            if sonuc.tamamlandi_mi:
                self.calc._cache_yaz(sonuc)

            QMessageBox.information(self, "Kaydedildi",
                f"Recete {self._aktif_recete_no} maliyet bilesenleri kaydedildi.\n"
                f"Birim toplam: {sonuc.m_toplam:,.4f} {sonuc.para_birimi}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            self._listeyi_yukle()
            # Aktif kalsin (secim kaybolur)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatasi:\n{e}")

    def _cache_yenile(self):
        try:
            sonuc = self.calc.cache_doldur()
            QMessageBox.information(
                self, "Cache Yenilendi",
                f"Toplam: {sonuc['toplam']}, Basari: {sonuc['basari']}, "
                f"Eksik bilesen: {sonuc['eksik_bilesen']}"
            )
            self._listeyi_yukle()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
