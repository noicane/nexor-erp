# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Sistem > Musteri Yonetimi
=============================================
Bayi tarafinda musterilerin (= NEXOR profillerinin) tek bir ekrandan yonetilmesi.

Her musteri = config.json'daki bir profil. Tablo profilleri listeler;
Yeni/Duzenle dialog'u 5 sekme ile tum kimlik/anlasma/iletisim/kurulum/belge
bilgilerini saklar. "Bu Musteriye Gec" butonu aktif profili degistirir,
NEXOR yeniden baslatma onerir.

Goruntu kosulu: ModulServisi.gelistirici_modu == True. Production musteride
gizlidir (sidebar guard + page guard).
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QDoubleSpinBox, QFileDialog,
    QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from components.base_page import BasePage
from core.external_config import config_manager, encode_password, decode_password
from core.nexor_brand import brand


# ============================================================================
# YARDIMCILAR
# ============================================================================

_MUSTERI_TIPLERI = ["DEMO", "AKTIF", "ESKI", "PILOT"]
_DURUMLAR = ["AKTIF", "PASIF", "ASKIDA"]
_SEGMENTLER = ["", "Mikro", "KOBI", "Kurumsal"]
_LISANS_TIPLERI = ["YILLIK", "AYLIK", "PERPETUAL"]
_YENILEME_TIPLERI = ["MANUEL", "OTOMATIK"]
_ODEME_PERIYOTLARI = ["YILLIK", "AYLIK", "TEK"]
_PARA_BIRIMLERI = ["TRY", "USD", "EUR", "GBP"]
_KURULUM_TIPLERI = ["ON_PREM", "CLOUD"]
_ADRES_TIPLERI = ["MERKEZ", "SUBE", "FATURA", "SEVK"]
_KISI_ROLLERI = ["KARAR", "MALI", "TEKNIK", "DIGER"]
_BELGE_TIPLERI = ["SOZLESME", "VERGI_LEVHASI", "IMZA_SIRKULERI", "FAALIYET_BELGESI", "KVKK", "DIGER"]

# M2.1 - Aktivite tipleri
_AKTIVITE_TIPLERI = ["NOT", "ARAMA", "ZIYARET", "MAIL", "EGITIM", "KURULUM", "DESTEK", "ANLASMA", "DIGER"]
_AKTIVITE_IKONLARI = {
    "NOT": "📝", "ARAMA": "📞", "ZIYARET": "🚗", "MAIL": "✉️",
    "EGITIM": "🎓", "KURULUM": "🔧", "DESTEK": "🆘", "ANLASMA": "📑", "DIGER": "•",
}

# M2.2 - Destek ticket parametreleri
_TICKET_DURUMLARI = ["ACIK", "BEKLEMEDE", "COZULDU", "KAPATILDI", "IPTAL"]
_TICKET_ONCELIKLERI = ["DUSUK", "NORMAL", "YUKSEK", "KRITIK"]

# M2.5 - Audit log kategorileri
_AUDIT_KATEGORILERI = ["ANLASMA", "BAKIM", "LISANS", "ILETISIM", "DB", "FINANSAL", "DIGER"]
# Audit log'a otomatik kayit edilen alanlar (alan_yolu, kategori, gosterim_etiketi)
_AUDIT_ALANLARI = [
    ("anlasma.bedel", "ANLASMA", "Bedel"),
    ("anlasma.lisans_tipi", "LISANS", "Lisans Tipi"),
    ("anlasma.bitis_tarihi", "ANLASMA", "Anlasma Bitis"),
    ("anlasma.kullanici_limiti", "LISANS", "Kullanici Limiti"),
    ("bakim.var", "BAKIM", "Bakim Anlasmasi"),
    ("bakim.aylik_ucret", "BAKIM", "Bakim Aylik Ucret"),
    ("bakim.bitis_tarihi", "BAKIM", "Bakim Bitis"),
    ("bakim.destek_7_24", "BAKIM", "7-24 Destek"),
    ("durum", "DIGER", "Musteri Durumu"),
    ("musteri_tipi", "DIGER", "Musteri Tipi"),
    ("iletisim.telefon", "ILETISIM", "Telefon"),
    ("iletisim.email", "ILETISIM", "E-posta"),
    ("database.server", "DB", "DB Sunucu"),
    ("database.database", "DB", "Veritabani"),
    ("finansal.cari_bakiye", "FINANSAL", "Cari Bakiye"),
    ("finansal.kredi_limiti", "FINANSAL", "Kredi Limiti"),
    ("finansal.zirve_cari_kodu", "FINANSAL", "Zirve Cari Kodu"),
]


def _str_to_qdate(s: str) -> QDate:
    if not s:
        return QDate.currentDate()
    try:
        d = datetime.strptime(s[:10], "%Y-%m-%d")
        return QDate(d.year, d.month, d.day)
    except Exception:
        return QDate.currentDate()


def _qdate_to_str(qd: QDate) -> str:
    return qd.toString("yyyy-MM-dd") if qd and qd.isValid() else ""


def _safe_int(v, default=0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _safe_float(v, default=0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _setup_form(form: 'QFormLayout') -> None:
    """QFormLayout'u tutarli sekilde ayarla: label sol, field genis, satir wrap yok."""
    from PySide6.QtWidgets import QFormLayout
    form.setRowWrapPolicy(QFormLayout.DontWrapRows)
    form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
    form.setHorizontalSpacing(14)
    form.setVerticalSpacing(8)
    form.setContentsMargins(14, 18, 14, 14)


# ============================================================================
# MUSTERI DETAY DIALOG (5 SEKME)
# ============================================================================

class MusteriDetayDialog(QDialog):
    """Musteri profilini olustur veya duzenle."""

    def __init__(self, theme: dict, profil_adi: str = "", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.original_kod = profil_adi
        self.yeni_kayit = (profil_adi == "")

        if self.yeni_kayit:
            self.profil = {}
            self.setWindowTitle("Yeni Musteri")
        else:
            self.profil = (config_manager.get_profile(profil_adi) or {}).copy()
            self.setWindowTitle(f"Musteri: {self.profil.get('musteri_adi') or profil_adi}")

        self.setModal(True)
        self.setMinimumSize(820, 640)
        self._build_ui()
        self._fill()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _stil(self) -> str:
        return f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                padding: 6px 8px; min-height: 22px;
                selection-background-color: {brand.PRIMARY};
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
            QDateEdit:focus, QComboBox:focus {{
                border-color: {brand.PRIMARY};
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_CARD}; color: {brand.TEXT};
                selection-background-color: {brand.PRIMARY};
                border: 1px solid {brand.BORDER};
            }}
            QCheckBox {{ color: {brand.TEXT}; spacing: 6px; background: transparent; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 1.5px solid {brand.BORDER_HARD};
                border-radius: 4px;
                background: {brand.BG_INPUT};
            }}
            QCheckBox::indicator:hover {{ border-color: {brand.PRIMARY}; }}
            QCheckBox::indicator:checked {{
                background: {brand.PRIMARY};
                border: 1.5px solid {brand.PRIMARY};
            }}
            QCheckBox::indicator:disabled {{
                background: {brand.BG_HOVER};
                border-color: {brand.TEXT_DISABLED};
            }}
            QCheckBox::indicator:checked:disabled {{
                background: {brand.PRIMARY_HOVER};
            }}
            QGroupBox {{
                color: {brand.TEXT}; border: 1px solid {brand.BORDER};
                border-radius: 8px; margin-top: 14px;
                font-weight: bold; padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; subcontrol-position: top left;
                left: 12px; padding: 0 6px;
                background: {brand.BG_MAIN};
            }}
            QTabWidget::pane {{ border: 1px solid {brand.BORDER}; border-radius: 8px; }}
            QTabBar::tab {{
                background: {brand.BG_CARD}; color: {brand.TEXT_MUTED};
                padding: 8px 16px; border: 1px solid {brand.BORDER};
                border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
            }}
            QPushButton {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                padding: 8px 14px; min-width: 90px;
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
            QPushButton#primary {{
                background: {brand.PRIMARY}; color: white; border: none;
            }}
            QPushButton#primary:hover {{ background: {brand.PRIMARY_HOVER}; }}
            QTableWidget {{
                background: {brand.BG_CARD}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                gridline-color: {brand.BORDER};
            }}
            QHeaderView::section {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                padding: 6px; border: none; font-weight: bold;
            }}
        """

    def _build_ui(self):
        self.setStyleSheet(self._stil())

        ana = QVBoxLayout(self)
        ana.setContentsMargins(16, 16, 16, 16)
        ana.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_genel(), "Genel")
        self.tabs.addTab(self._tab_iletisim(), "Adresler & Kisiler")
        self.tabs.addTab(self._tab_anlasma(), "Anlasma & Lisans")
        self.tabs.addTab(self._tab_finansal(), "Finansal")
        self.tabs.addTab(self._tab_kurulum(), "DB & Kurulum")
        self.tabs.addTab(self._tab_nas(), "NAS Yolları")
        self.tabs.addTab(self._tab_belgeler(), "Belgeler")
        self.tabs.addTab(self._tab_aktiviteler(), "Aktivite & Notlar")
        self.tabs.addTab(self._tab_destek(), "Destek Geçmişi")
        self.tabs.addTab(self._tab_audit(), "Audit Log")
        ana.addWidget(self.tabs, 1)

        # Alt buton row
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_iptal = QPushButton("Iptal")
        self.btn_iptal.clicked.connect(self.reject)
        self.btn_kaydet = QPushButton("Kaydet")
        self.btn_kaydet.setObjectName("primary")
        self.btn_kaydet.clicked.connect(self._kaydet)
        btn_row.addWidget(self.btn_iptal)
        btn_row.addWidget(self.btn_kaydet)
        ana.addLayout(btn_row)

    # ------------------------------------------------------------------
    # SEKME 1 - GENEL
    # ------------------------------------------------------------------

    def _tab_genel(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        # Sol: form, Sag: logo
        h = QHBoxLayout()
        h.setSpacing(16)

        # FORM
        gb = QGroupBox("Kimlik Bilgileri")
        form = QFormLayout(gb)
        _setup_form(form)

        self.ed_kod = QLineEdit()
        self.ed_kod.setPlaceholderText("ornek: musteri_x")
        form.addRow("Musteri Kodu *", self.ed_kod)

        self.ed_adi = QLineEdit()
        form.addRow("Unvan *", self.ed_adi)

        self.ed_kisa = QLineEdit()
        form.addRow("Kisa Ad", self.ed_kisa)

        self.cb_tip = QComboBox()
        self.cb_tip.addItems(_MUSTERI_TIPLERI)
        form.addRow("Musteri Tipi", self.cb_tip)

        self.cb_durum = QComboBox()
        self.cb_durum.addItems(_DURUMLAR)
        form.addRow("Durum", self.cb_durum)

        self.cb_segment = QComboBox()
        self.cb_segment.addItems(_SEGMENTLER)
        self.cb_segment.setEditable(True)
        form.addRow("Segment", self.cb_segment)

        self.ed_sektor = QLineEdit()
        form.addRow("Sektor", self.ed_sektor)

        h.addWidget(gb, 2)

        # LOGO panel
        gb_logo = QGroupBox("Logo")
        v_logo = QVBoxLayout(gb_logo)
        self.logo_preview = QLabel("(logo yok)")
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setMinimumSize(180, 180)
        self.logo_preview.setStyleSheet(
            f"background: {brand.BG_INPUT}; border: 1px dashed {brand.BORDER}; border-radius: 6px; color: {brand.TEXT_DIM};"
        )
        v_logo.addWidget(self.logo_preview)
        btn_logo = QPushButton("Logo Sec")
        btn_logo.clicked.connect(self._logo_sec)
        v_logo.addWidget(btn_logo)
        btn_logo_temizle = QPushButton("Temizle")
        btn_logo_temizle.clicked.connect(self._logo_temizle)
        v_logo.addWidget(btn_logo_temizle)
        v_logo.addStretch()
        h.addWidget(gb_logo, 1)

        lay.addLayout(h)

        # VERGI BLOGU
        gb_vergi = QGroupBox("Vergi & Yasal Bilgiler")
        f_vergi = QFormLayout(gb_vergi)
        _setup_form(f_vergi)
        self.ed_vergi_dairesi = QLineEdit()
        f_vergi.addRow("Vergi Dairesi", self.ed_vergi_dairesi)
        self.ed_vkn = QLineEdit()
        self.ed_vkn.setMaxLength(11)
        f_vergi.addRow("VKN / TCKN", self.ed_vkn)
        self.ed_mersis = QLineEdit()
        self.ed_mersis.setMaxLength(16)
        f_vergi.addRow("MERSIS No", self.ed_mersis)
        lay.addWidget(gb_vergi)

        # ILETISIM BLOGU
        gb_iletisim = QGroupBox("Iletisim")
        f_il = QFormLayout(gb_iletisim)
        _setup_form(f_il)
        self.ed_telefon = QLineEdit()
        f_il.addRow("Telefon", self.ed_telefon)
        self.ed_email = QLineEdit()
        f_il.addRow("E-posta", self.ed_email)
        self.ed_web = QLineEdit()
        f_il.addRow("Web Sitesi", self.ed_web)
        lay.addWidget(gb_iletisim)

        # RAPORLAMA
        gb_rep = QGroupBox("Raporlama")
        f_rep = QFormLayout(gb_rep)
        _setup_form(f_rep)
        self.ed_sorumlu = QLineEdit()
        f_rep.addRow("Sorumlu Bayi Personeli", self.ed_sorumlu)
        self.ed_etiketler = QLineEdit()
        self.ed_etiketler.setPlaceholderText("virgulle ayir: vip, kataforez, bursa")
        f_rep.addRow("Etiketler", self.ed_etiketler)
        self.ed_kazanim = QLineEdit()
        self.ed_kazanim.setPlaceholderText("Tavsiye / Web / Fuar / ...")
        f_rep.addRow("Kazanim Kanali", self.ed_kazanim)
        self.dt_ilk_satis = QDateEdit()
        self.dt_ilk_satis.setCalendarPopup(True)
        self.dt_ilk_satis.setDisplayFormat("dd.MM.yyyy")
        f_rep.addRow("Ilk Satis Tarihi", self.dt_ilk_satis)
        lay.addWidget(gb_rep)

        lay.addStretch()
        return w

    def _logo_sec(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Logo Sec", "", "Resim (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if path:
            self._logo_path = path
            self._logo_onizle(path)

    def _logo_temizle(self):
        self._logo_path = ""
        self.logo_preview.setText("(logo yok)")
        self.logo_preview.setPixmap(QPixmap())

    def _logo_onizle(self, path: str):
        if path and os.path.exists(path):
            pm = QPixmap(path)
            if not pm.isNull():
                pm = pm.scaled(176, 176, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_preview.setPixmap(pm)
                self.logo_preview.setText("")
                return
        self.logo_preview.setText("(logo yok)")

    # ------------------------------------------------------------------
    # SEKME 2 - ADRESLER & KISILER
    # ------------------------------------------------------------------

    def _tab_iletisim(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        # Adresler
        gb_adr = QGroupBox("Adresler")
        v = QVBoxLayout(gb_adr)
        self.tbl_adresler = QTableWidget(0, 6)
        self.tbl_adresler.setHorizontalHeaderLabels(
            ["Tip", "Baslik", "Adres", "Sehir", "Ilce", "Posta Kodu"]
        )
        self.tbl_adresler.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_adresler.verticalHeader().setVisible(False)
        v.addWidget(self.tbl_adresler)
        h = QHBoxLayout()
        h.addStretch()
        b1 = QPushButton("+ Adres Ekle")
        b1.clicked.connect(lambda: self._satir_ekle_adres())
        b2 = QPushButton("- Sec Sil")
        b2.clicked.connect(lambda: self._satir_sil(self.tbl_adresler))
        h.addWidget(b1)
        h.addWidget(b2)
        v.addLayout(h)
        lay.addWidget(gb_adr, 1)

        # Kisiler
        gb_kis = QGroupBox("Ilgili Kisiler")
        v2 = QVBoxLayout(gb_kis)
        self.tbl_kisiler = QTableWidget(0, 5)
        self.tbl_kisiler.setHorizontalHeaderLabels(
            ["Ad Soyad", "Unvan", "Telefon", "E-posta", "Rol"]
        )
        self.tbl_kisiler.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_kisiler.verticalHeader().setVisible(False)
        v2.addWidget(self.tbl_kisiler)
        h2 = QHBoxLayout()
        h2.addStretch()
        b3 = QPushButton("+ Kisi Ekle")
        b3.clicked.connect(lambda: self._satir_ekle_kisi())
        b4 = QPushButton("- Sec Sil")
        b4.clicked.connect(lambda: self._satir_sil(self.tbl_kisiler))
        h2.addWidget(b3)
        h2.addWidget(b4)
        v2.addLayout(h2)
        lay.addWidget(gb_kis, 1)

        return w

    def _satir_ekle_adres(self, data: Optional[dict] = None):
        data = data or {}
        r = self.tbl_adresler.rowCount()
        self.tbl_adresler.insertRow(r)

        cb = QComboBox()
        cb.addItems(_ADRES_TIPLERI)
        if data.get('tip') in _ADRES_TIPLERI:
            cb.setCurrentText(data['tip'])
        self.tbl_adresler.setCellWidget(r, 0, cb)

        for col, key in enumerate(['baslik', 'adres', 'sehir', 'ilce', 'posta_kodu'], start=1):
            self.tbl_adresler.setItem(r, col, QTableWidgetItem(str(data.get(key, ''))))

    def _satir_ekle_kisi(self, data: Optional[dict] = None):
        data = data or {}
        r = self.tbl_kisiler.rowCount()
        self.tbl_kisiler.insertRow(r)

        for col, key in enumerate(['ad', 'unvan', 'telefon', 'email'], start=0):
            self.tbl_kisiler.setItem(r, col, QTableWidgetItem(str(data.get(key, ''))))

        cb = QComboBox()
        cb.addItems(_KISI_ROLLERI)
        if data.get('rol') in _KISI_ROLLERI:
            cb.setCurrentText(data['rol'])
        self.tbl_kisiler.setCellWidget(r, 4, cb)

    def _satir_sil(self, tbl: QTableWidget):
        r = tbl.currentRow()
        if r >= 0:
            tbl.removeRow(r)

    # ------------------------------------------------------------------
    # SEKME 3 - ANLASMA & LISANS
    # ------------------------------------------------------------------

    def _tab_anlasma(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        # Sozlesme
        gb_s = QGroupBox("Sozlesme")
        f = QFormLayout(gb_s)
        _setup_form(f)
        self.ed_sozlesme_no = QLineEdit()
        f.addRow("Sozlesme No", self.ed_sozlesme_no)
        self.dt_baslangic = QDateEdit()
        self.dt_baslangic.setCalendarPopup(True)
        self.dt_baslangic.setDisplayFormat("dd.MM.yyyy")
        f.addRow("Baslangic Tarihi", self.dt_baslangic)
        self.dt_bitis = QDateEdit()
        self.dt_bitis.setCalendarPopup(True)
        self.dt_bitis.setDisplayFormat("dd.MM.yyyy")
        f.addRow("Bitis Tarihi", self.dt_bitis)
        self.cb_yenileme = QComboBox()
        self.cb_yenileme.addItems(_YENILEME_TIPLERI)
        f.addRow("Yenileme Tipi", self.cb_yenileme)
        self.ed_imza_pdf = QLineEdit()
        self.ed_imza_pdf.setReadOnly(True)
        h_pdf = QHBoxLayout()
        h_pdf.addWidget(self.ed_imza_pdf, 1)
        b_pdf = QPushButton("Sec...")
        b_pdf.clicked.connect(self._imza_sec)
        h_pdf.addWidget(b_pdf)
        wrap = QWidget()
        wrap.setLayout(h_pdf)
        f.addRow("Imza PDF", wrap)
        lay.addWidget(gb_s)

        # Lisans
        gb_l = QGroupBox("Lisans & Bedel")
        gl = QGridLayout(gb_l)
        gl.setHorizontalSpacing(12)
        gl.setVerticalSpacing(8)

        gl.addWidget(QLabel("Lisans Tipi"), 0, 0)
        self.cb_lisans = QComboBox()
        self.cb_lisans.addItems(_LISANS_TIPLERI)
        gl.addWidget(self.cb_lisans, 0, 1)

        gl.addWidget(QLabel("Odeme Periyodu"), 0, 2)
        self.cb_odeme = QComboBox()
        self.cb_odeme.addItems(_ODEME_PERIYOTLARI)
        gl.addWidget(self.cb_odeme, 0, 3)

        gl.addWidget(QLabel("Bedel"), 1, 0)
        self.sp_bedel = QDoubleSpinBox()
        self.sp_bedel.setMaximum(99_999_999.0)
        self.sp_bedel.setDecimals(2)
        self.sp_bedel.setSuffix(" ")
        gl.addWidget(self.sp_bedel, 1, 1)

        gl.addWidget(QLabel("Para Birimi"), 1, 2)
        self.cb_para = QComboBox()
        self.cb_para.addItems(_PARA_BIRIMLERI)
        gl.addWidget(self.cb_para, 1, 3)

        self.chk_kdv_dahil = QCheckBox("Bedele KDV Dahil")
        gl.addWidget(self.chk_kdv_dahil, 2, 0, 1, 2)

        gl.addWidget(QLabel("Kullanici Limiti"), 2, 2)
        self.sp_user_limit = QSpinBox()
        self.sp_user_limit.setMaximum(9999)
        gl.addWidget(self.sp_user_limit, 2, 3)

        gl.addWidget(QLabel("Ek Kullanici Birim Ucreti"), 3, 0)
        self.sp_ek_user = QDoubleSpinBox()
        self.sp_ek_user.setMaximum(999_999.0)
        self.sp_ek_user.setDecimals(2)
        gl.addWidget(self.sp_ek_user, 3, 1)

        lay.addWidget(gb_l)

        # Bakim
        gb_b = QGroupBox("Aylik Bakim Anlasmasi")
        gb2 = QGridLayout(gb_b)
        gb2.setHorizontalSpacing(12)
        gb2.setVerticalSpacing(8)

        self.chk_bakim_var = QCheckBox("Aylik bakim anlasmasi var")
        gb2.addWidget(self.chk_bakim_var, 0, 0, 1, 4)

        gb2.addWidget(QLabel("Aylik Ucret"), 1, 0)
        self.sp_bakim_ucret = QDoubleSpinBox()
        self.sp_bakim_ucret.setMaximum(999_999.0)
        self.sp_bakim_ucret.setDecimals(2)
        gb2.addWidget(self.sp_bakim_ucret, 1, 1)

        gb2.addWidget(QLabel("Sonraki Fatura Tarihi"), 1, 2)
        self.dt_sonraki_fatura = QDateEdit()
        self.dt_sonraki_fatura.setCalendarPopup(True)
        self.dt_sonraki_fatura.setDisplayFormat("dd.MM.yyyy")
        gb2.addWidget(self.dt_sonraki_fatura, 1, 3)

        gb2.addWidget(QLabel("Bakim Bitis Tarihi"), 2, 0)
        self.dt_bakim_bitis = QDateEdit()
        self.dt_bakim_bitis.setCalendarPopup(True)
        self.dt_bakim_bitis.setDisplayFormat("dd.MM.yyyy")
        gb2.addWidget(self.dt_bakim_bitis, 2, 1)

        gb2.addWidget(QLabel("SLA Yanit (saat)"), 2, 2)
        self.sp_yanit = QSpinBox()
        self.sp_yanit.setMaximum(720)
        gb2.addWidget(self.sp_yanit, 2, 3)

        gb2.addWidget(QLabel("SLA Cozum (saat)"), 3, 0)
        self.sp_cozum = QSpinBox()
        self.sp_cozum.setMaximum(720)
        gb2.addWidget(self.sp_cozum, 3, 1)

        self.chk_destek_724 = QCheckBox("7-24 Destek")
        gb2.addWidget(self.chk_destek_724, 3, 2, 1, 2)

        lay.addWidget(gb_b)

        gb_n = QGroupBox("Notlar")
        v = QVBoxLayout(gb_n)
        self.txt_anlasma_notlar = QTextEdit()
        self.txt_anlasma_notlar.setMaximumHeight(80)
        v.addWidget(self.txt_anlasma_notlar)
        lay.addWidget(gb_n)

        lay.addStretch()
        return w

    def _imza_sec(self):
        path, _ = QFileDialog.getOpenFileName(self, "Imza PDF Sec", "", "PDF (*.pdf)")
        if path:
            self.ed_imza_pdf.setText(path)

    # ------------------------------------------------------------------
    # SEKME 4 - DB & KURULUM
    # ------------------------------------------------------------------

    def _tab_kurulum(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        # ERP DB
        gb_erp = QGroupBox("ERP Veritabani")
        f = QFormLayout(gb_erp)
        _setup_form(f)
        self.ed_db_server = QLineEdit()
        self.ed_db_server.setPlaceholderText("ornek: 192.168.10.66\\SQLEXPRESS")
        f.addRow("Sunucu", self.ed_db_server)
        self.ed_db_name = QLineEdit()
        f.addRow("Veritabani", self.ed_db_name)
        self.ed_db_user = QLineEdit()
        f.addRow("Kullanici", self.ed_db_user)
        self.ed_db_pwd = QLineEdit()
        self.ed_db_pwd.setEchoMode(QLineEdit.Password)
        f.addRow("Sifre", self.ed_db_pwd)
        self.chk_trusted = QCheckBox("Windows Authentication (Trusted)")
        f.addRow("", self.chk_trusted)
        h_test = QHBoxLayout()
        h_test.addStretch()
        self.btn_db_test = QPushButton("Baglantiyi Test Et")
        self.btn_db_test.clicked.connect(self._db_test)
        h_test.addWidget(self.btn_db_test)
        wrap_test = QWidget()
        wrap_test.setLayout(h_test)
        f.addRow("", wrap_test)
        lay.addWidget(gb_erp)

        # Kurulum metadata
        gb_k = QGroupBox("Kurulum Bilgisi")
        f2 = QFormLayout(gb_k)
        _setup_form(f2)
        self.cb_kurulum_tip = QComboBox()
        self.cb_kurulum_tip.addItems(_KURULUM_TIPLERI)
        f2.addRow("Tip", self.cb_kurulum_tip)
        self.ed_sql_surumu = QLineEdit()
        self.ed_sql_surumu.setPlaceholderText("ornek: SQL Server 2022 Express")
        f2.addRow("SQL Surumu", self.ed_sql_surumu)
        self.ed_nexor_v = QLineEdit()
        self.ed_nexor_v.setPlaceholderText("ornek: 1.8.0")
        f2.addRow("NEXOR Versiyonu", self.ed_nexor_v)
        self.dt_son_guncelleme = QDateEdit()
        self.dt_son_guncelleme.setCalendarPopup(True)
        self.dt_son_guncelleme.setDisplayFormat("dd.MM.yyyy")
        f2.addRow("Son Guncelleme Tarihi", self.dt_son_guncelleme)
        lay.addWidget(gb_k)

        lay.addStretch()
        return w

    def _db_test(self):
        import pyodbc
        server = self.ed_db_server.text().strip()
        db = self.ed_db_name.text().strip()
        if not server or not db:
            QMessageBox.warning(self, "Eksik Bilgi", "Sunucu ve veritabani zorunlu.")
            return
        try:
            if self.chk_trusted.isChecked():
                cs = (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};"
                    f"DATABASE={db};Trusted_Connection=yes;"
                    "Encrypt=no;TrustServerCertificate=yes;"
                )
            else:
                cs = (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};"
                    f"DATABASE={db};UID={self.ed_db_user.text()};"
                    f"PWD={self.ed_db_pwd.text()};"
                    "Encrypt=no;TrustServerCertificate=yes;"
                )
            conn = pyodbc.connect(cs, timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
            conn.close()
            QMessageBox.information(self, "Baglanti OK", f"{server} / {db} baglantisi basarili.")
        except Exception as e:
            QMessageBox.critical(self, "Baglanti Hatasi", str(e))

    # ------------------------------------------------------------------
    # SEKME 5 - NAS YOLLARI
    # ------------------------------------------------------------------

    # Profil 'nas.shares' anahtarlari ve UI'da gosterilecek aciklamalar.
    # (kod, etiket, varsayilan_alt_yol, aciklama)
    _NAS_KEYS = [
        ("mamul_resim",   "Mamul Resim",       "Data Yönetimi/MAMUL_RESIM",         "Ürün görselleri (kalite/stok)"),
        ("urunler",       "Ürünler",           "Data Yönetimi/Urunler",             "Cari/UrunKodu klasörleri"),
        ("kimyasallar",   "Kimyasallar",       "Data Yönetimi/Kimyasallar",         "Kimyasal belgeleri"),
        ("logo",          "Logo Dosyası",      "Data Yönetimi/LOGO/atlas_logo.png", "Şirket logosu (tam dosya yolu)"),
        ("tds",           "TDS Dökümanları",   "Data Yönetimi/TDS_Dokumanlari",     "Lab TDS belgeleri"),
        ("aksiyonlar",    "Aksiyonlar",        "Data Yönetimi/Aksiyonlar",          "Aksiyon ekleri"),
        ("kalite",        "Kalite Klasörü",    "Kalite",                            "Kalite dokümantasyonu"),
        ("update_server", "Update Server",     "Atmo_Logic",                        "Otomatik güncelleme paylaşımı"),
        ("personel",      "Personel",          "Personel",                          "Özlük dosyaları, fotoğraflar"),
    ]

    def _tab_nas(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        # Sunucu blogu
        gb_srv = QGroupBox("NAS Sunucusu")
        f = QFormLayout(gb_srv)
        _setup_form(f)
        self.ed_nas_server = QLineEdit()
        self.ed_nas_server.setPlaceholderText("ornek: AtlasNAS  veya  192.168.10.50")
        f.addRow("Sunucu (UNC adı / IP)", self.ed_nas_server)

        h_test = QHBoxLayout()
        h_test.addStretch()
        btn_test = QPushButton("Sunucuyu Test Et (ping)")
        btn_test.clicked.connect(self._nas_test)
        h_test.addWidget(btn_test)
        wt = QWidget(); wt.setLayout(h_test)
        f.addRow("", wt)
        lay.addWidget(gb_srv)

        # Aciklama
        bilgi = QLabel(
            "Her müşterinin NAS sunucusu farklı olabilir. Aşağıdaki paylaşım yolları "
            "<b>sunucudan sonraki kısım</b>dır (örn: <code>Data Yönetimi/MAMUL_RESIM</code>). "
            "Boş bırakılan yollar varsayılana döner. Logo dosyası tam dosya yolu olmalı."
        )
        bilgi.setWordWrap(True)
        bilgi.setStyleSheet(
            f"background: {brand.BG_CARD}; color: {brand.TEXT_DIM}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px 12px; font-size: 11px;"
        )
        lay.addWidget(bilgi)

        # Paylasimlar
        gb_sh = QGroupBox("Paylaşım Yolları")
        f2 = QFormLayout(gb_sh)
        _setup_form(f2)
        self._nas_inputs: dict[str, QLineEdit] = {}
        for key, etiket, varsayilan, aciklama in self._NAS_KEYS:
            ed = QLineEdit()
            ed.setPlaceholderText(f"Varsayılan: {varsayilan}")
            ed.setToolTip(aciklama)
            self._nas_inputs[key] = ed
            f2.addRow(f"{etiket}", ed)
        lay.addWidget(gb_sh)

        lay.addStretch()
        return w

    def _nas_test(self):
        import subprocess
        srv = self.ed_nas_server.text().strip()
        if not srv:
            QMessageBox.warning(self, "Eksik", "Sunucu adı veya IP girin.")
            return
        try:
            r = subprocess.run(
                ["ping", "-n", "1", "-w", "1500", srv],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0:
                QMessageBox.information(self, "Bağlantı OK", f"{srv} ping yanıt verdi.")
            else:
                QMessageBox.warning(self, "Yanıt Yok", f"{srv} ping yanıt vermedi.\n\n{r.stdout[:300]}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    # ------------------------------------------------------------------
    # SEKME 6 - BELGELER
    # ------------------------------------------------------------------

    def _tab_belgeler(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)

        gb = QGroupBox("Yuklenen Belgeler")
        v = QVBoxLayout(gb)

        self.tbl_belgeler = QTableWidget(0, 4)
        self.tbl_belgeler.setHorizontalHeaderLabels(
            ["Tip", "Dosya", "Eklenme Tarihi", "Aciklama"]
        )
        self.tbl_belgeler.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_belgeler.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tbl_belgeler.verticalHeader().setVisible(False)
        v.addWidget(self.tbl_belgeler)

        h = QHBoxLayout()
        h.addStretch()
        b1 = QPushButton("+ Belge Ekle")
        b1.clicked.connect(self._belge_ekle)
        b2 = QPushButton("- Sec Sil")
        b2.clicked.connect(lambda: self._satir_sil(self.tbl_belgeler))
        h.addWidget(b1)
        h.addWidget(b2)
        v.addLayout(h)

        lay.addWidget(gb)
        return w

    def _belge_ekle(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Belge Sec", "", "Tum Dosyalar (*.*)"
        )
        if not path:
            return
        r = self.tbl_belgeler.rowCount()
        self.tbl_belgeler.insertRow(r)

        cb = QComboBox()
        cb.addItems(_BELGE_TIPLERI)
        self.tbl_belgeler.setCellWidget(r, 0, cb)
        self.tbl_belgeler.setItem(r, 1, QTableWidgetItem(path))
        self.tbl_belgeler.setItem(r, 2, QTableWidgetItem(datetime.now().strftime("%Y-%m-%d")))
        self.tbl_belgeler.setItem(r, 3, QTableWidgetItem(""))

    # ------------------------------------------------------------------
    # SEKME 7 - AKTIVITE & NOTLAR (M2.1 - Chatter timeline)
    # ------------------------------------------------------------------

    def _tab_aktiviteler(self) -> QWidget:
        from PySide6.QtWidgets import QListWidget, QListWidgetItem
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        # Bilgi seridi
        bilgi = QLabel(
            "Müşteri ile yapılan tüm görüşme, ziyaret, eğitim ve önemli notların "
            "kronolojik kaydı. Yeni etkinlik için sağ üstten ekleyin."
        )
        bilgi.setWordWrap(True)
        bilgi.setStyleSheet(
            f"background: {brand.BG_CARD}; color: {brand.TEXT_DIM}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px 12px; font-size: 11px;"
        )
        lay.addWidget(bilgi)

        # Toolbar
        h = QHBoxLayout()
        from PySide6.QtWidgets import QListWidget
        self.cb_aktivite_filtre = QComboBox()
        self.cb_aktivite_filtre.addItem("Tüm Tipler", "")
        for t in _AKTIVITE_TIPLERI:
            self.cb_aktivite_filtre.addItem(f"{_AKTIVITE_IKONLARI.get(t,'')} {t}", t)
        self.cb_aktivite_filtre.currentIndexChanged.connect(self._aktivite_filtrele)
        h.addWidget(QLabel("Filtre:"))
        h.addWidget(self.cb_aktivite_filtre)
        h.addStretch()

        b_yeni = QPushButton("+ Etkinlik Ekle")
        b_yeni.setObjectName("primary")
        b_yeni.clicked.connect(self._aktivite_yeni)
        h.addWidget(b_yeni)
        b_duz = QPushButton("Düzenle")
        b_duz.clicked.connect(self._aktivite_duzenle)
        h.addWidget(b_duz)
        b_sil = QPushButton("- Sec Sil")
        b_sil.clicked.connect(self._aktivite_sil)
        h.addWidget(b_sil)
        lay.addLayout(h)

        # Timeline (QListWidget)
        self.lst_aktivite = QListWidget()
        self.lst_aktivite.setStyleSheet(f"""
            QListWidget {{
                background: {brand.BG_CARD}; border: 1px solid {brand.BORDER};
                border-radius: 8px; color: {brand.TEXT};
            }}
            QListWidget::item {{
                border-bottom: 1px solid {brand.BORDER};
                padding: 10px 12px;
            }}
            QListWidget::item:selected {{
                background: {brand.PRIMARY_SOFT}; color: {brand.TEXT};
            }}
            QListWidget::item:hover {{ background: {brand.BG_HOVER}; }}
        """)
        self.lst_aktivite.itemDoubleClicked.connect(lambda _: self._aktivite_duzenle())
        lay.addWidget(self.lst_aktivite, 1)

        # Memory'de tutulan aktivite listesi (kaydet'e kadar)
        self._aktiviteler: list = []

        return w

    def _aktivite_yenile(self):
        """Listeyi `self._aktiviteler` icerigiyle yeniden cizdir (filtre uygulayarak)."""
        from PySide6.QtWidgets import QListWidgetItem
        self.lst_aktivite.clear()
        filtre = self.cb_aktivite_filtre.currentData() or ""
        # Yeniyi uste al
        sirali = sorted(self._aktiviteler, key=lambda a: a.get('zaman', ''), reverse=True)
        for a in sirali:
            tip = a.get('tip', 'NOT')
            if filtre and tip != filtre:
                continue
            ikon = _AKTIVITE_IKONLARI.get(tip, '•')
            zaman = (a.get('zaman') or '')[:16].replace('T', ' ')
            kullanici = a.get('kullanici') or '-'
            baslik = a.get('baslik') or '(başlıksız)'
            icerik = (a.get('icerik') or '').strip()
            if len(icerik) > 180:
                icerik = icerik[:178] + '...'
            ek = a.get('ek_dosyalar') or []
            ek_str = f"  📎 {len(ek)} ek" if ek else ""
            text = f"{ikon}  [{tip}]  {zaman}   ·  {kullanici}{ek_str}\n   {baslik}"
            if icerik:
                text += f"\n   {icerik}"
            it = QListWidgetItem(text)
            it.setData(Qt.UserRole, a)
            self.lst_aktivite.addItem(it)

    def _aktivite_filtrele(self):
        self._aktivite_yenile()

    def _aktivite_yeni(self):
        dlg = AktiviteDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._aktiviteler.append(dlg.veri())
            self._aktivite_yenile()

    def _aktivite_duzenle(self):
        it = self.lst_aktivite.currentItem()
        if not it:
            QMessageBox.information(self, "Seçim", "Düzenlemek için bir etkinlik seçin.")
            return
        mevcut = it.data(Qt.UserRole) or {}
        dlg = AktiviteDialog(parent=self, mevcut=mevcut)
        if dlg.exec() == QDialog.Accepted:
            yeni = dlg.veri()
            for i, a in enumerate(self._aktiviteler):
                if a is mevcut or (a.get('zaman') == mevcut.get('zaman') and a.get('baslik') == mevcut.get('baslik')):
                    self._aktiviteler[i] = yeni
                    break
            self._aktivite_yenile()

    def _aktivite_sil(self):
        it = self.lst_aktivite.currentItem()
        if not it:
            return
        if QMessageBox.question(self, "Sil", "Seçili etkinlik silinsin mi?") != QMessageBox.Yes:
            return
        mevcut = it.data(Qt.UserRole) or {}
        self._aktiviteler = [
            a for a in self._aktiviteler
            if not (a.get('zaman') == mevcut.get('zaman') and a.get('baslik') == mevcut.get('baslik'))
        ]
        self._aktivite_yenile()

    # ------------------------------------------------------------------
    # SEKME 8 - DESTEK GECMISI (M2.2)
    # ------------------------------------------------------------------

    def _tab_destek(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        # Ust KPI kartlari
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)
        self.lbl_destek_acik = self._kpi_card("Açık Talep", "0", brand.WARNING)
        self.lbl_destek_kapali = self._kpi_card("Kapalı Talep", "0", brand.SUCCESS)
        self.lbl_destek_yanit = self._kpi_card("Ort. Yanıt (dk)", "0", brand.INFO)
        self.lbl_destek_cozum = self._kpi_card("Ort. Çözüm (dk)", "0", brand.INFO)
        self.lbl_destek_memnuniyet = self._kpi_card("Memnuniyet", "0.0/5", brand.PRIMARY)
        for c in (self.lbl_destek_acik, self.lbl_destek_kapali,
                  self.lbl_destek_yanit, self.lbl_destek_cozum,
                  self.lbl_destek_memnuniyet):
            kpi_row.addWidget(c['wrap'])
        kpi_row.addStretch()
        lay.addLayout(kpi_row)

        # Ozet bilgi
        gb_ozet = QGroupBox("Genel Bilgi")
        f = QFormLayout(gb_ozet)
        _setup_form(f)
        self.dt_son_ziyaret = QDateEdit()
        self.dt_son_ziyaret.setCalendarPopup(True)
        self.dt_son_ziyaret.setDisplayFormat("dd.MM.yyyy")
        self.dt_son_ziyaret.setMinimumDate(QDate(2000, 1, 1))
        self.dt_son_ziyaret.setSpecialValueText("Yok")
        f.addRow("Son Ziyaret Tarihi", self.dt_son_ziyaret)
        self.sp_memnuniyet = QDoubleSpinBox()
        self.sp_memnuniyet.setRange(0.0, 5.0)
        self.sp_memnuniyet.setDecimals(1)
        self.sp_memnuniyet.setSingleStep(0.1)
        f.addRow("Memnuniyet Skoru (0-5)", self.sp_memnuniyet)
        lay.addWidget(gb_ozet)

        # Talep listesi
        gb_t = QGroupBox("Talepler")
        v = QVBoxLayout(gb_t)
        self.tbl_destek = QTableWidget(0, 8)
        self.tbl_destek.setHorizontalHeaderLabels([
            "No", "Tarih", "Başlık", "Durum", "Öncelik",
            "Yanıt (dk)", "Çözüm (dk)", "Memnuniyet"
        ])
        self.tbl_destek.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_destek.verticalHeader().setVisible(False)
        v.addWidget(self.tbl_destek)
        h = QHBoxLayout()
        h.addStretch()
        b1 = QPushButton("+ Talep Ekle")
        b1.clicked.connect(self._destek_ekle)
        b2 = QPushButton("- Sec Sil")
        b2.clicked.connect(lambda: self._satir_sil(self.tbl_destek))
        b3 = QPushButton("Özeti Yenile")
        b3.clicked.connect(self._destek_kpi_hesapla)
        h.addWidget(b1)
        h.addWidget(b2)
        h.addWidget(b3)
        v.addLayout(h)
        lay.addWidget(gb_t, 1)

        return w

    def _kpi_card(self, baslik: str, deger: str, renk: str) -> dict:
        wrap = QFrame()
        wrap.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; "
            f"border-radius: 8px; padding: 10px 14px; }}"
        )
        v = QVBoxLayout(wrap)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(2)
        b = QLabel(baslik)
        b.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px;")
        d = QLabel(deger)
        d.setStyleSheet(f"color: {renk}; font-size: 18px; font-weight: bold;")
        v.addWidget(b)
        v.addWidget(d)
        return {'wrap': wrap, 'value': d}

    def _destek_ekle(self):
        r = self.tbl_destek.rowCount()
        self.tbl_destek.insertRow(r)
        # No
        next_no = f"D-{datetime.now().strftime('%Y%m%d')}-{r+1:03d}"
        self.tbl_destek.setItem(r, 0, QTableWidgetItem(next_no))
        # Tarih
        self.tbl_destek.setItem(r, 1, QTableWidgetItem(datetime.now().strftime("%Y-%m-%d")))
        # Baslik
        self.tbl_destek.setItem(r, 2, QTableWidgetItem(""))
        # Durum
        cb_d = QComboBox()
        cb_d.addItems(_TICKET_DURUMLARI)
        cb_d.setCurrentText("ACIK")
        self.tbl_destek.setCellWidget(r, 3, cb_d)
        # Oncelik
        cb_o = QComboBox()
        cb_o.addItems(_TICKET_ONCELIKLERI)
        cb_o.setCurrentText("NORMAL")
        self.tbl_destek.setCellWidget(r, 4, cb_o)
        # Yanit dk
        sp_y = QSpinBox()
        sp_y.setMaximum(99999)
        self.tbl_destek.setCellWidget(r, 5, sp_y)
        # Cozum dk
        sp_c = QSpinBox()
        sp_c.setMaximum(99999)
        self.tbl_destek.setCellWidget(r, 6, sp_c)
        # Memnuniyet
        sp_m = QDoubleSpinBox()
        sp_m.setRange(0.0, 5.0)
        sp_m.setDecimals(1)
        sp_m.setSingleStep(0.5)
        self.tbl_destek.setCellWidget(r, 7, sp_m)

    def _destek_kpi_hesapla(self):
        """Tablodaki ticketlardan KPI'lari hesapla."""
        n = self.tbl_destek.rowCount()
        acik = kapali = 0
        yanit_t = cozum_t = mem_t = 0.0
        yanit_n = cozum_n = mem_n = 0
        for r in range(n):
            cb_d = self.tbl_destek.cellWidget(r, 3)
            durum = cb_d.currentText() if cb_d else 'ACIK'
            if durum in ('ACIK', 'BEKLEMEDE'):
                acik += 1
            else:
                kapali += 1
            sp_y = self.tbl_destek.cellWidget(r, 5)
            sp_c = self.tbl_destek.cellWidget(r, 6)
            sp_m = self.tbl_destek.cellWidget(r, 7)
            if sp_y and sp_y.value() > 0:
                yanit_t += sp_y.value(); yanit_n += 1
            if sp_c and sp_c.value() > 0:
                cozum_t += sp_c.value(); cozum_n += 1
            if sp_m and sp_m.value() > 0:
                mem_t += sp_m.value(); mem_n += 1
        self.lbl_destek_acik['value'].setText(str(acik))
        self.lbl_destek_kapali['value'].setText(str(kapali))
        self.lbl_destek_yanit['value'].setText(f"{int(yanit_t/yanit_n) if yanit_n else 0}")
        self.lbl_destek_cozum['value'].setText(f"{int(cozum_t/cozum_n) if cozum_n else 0}")
        avg_mem = (mem_t / mem_n) if mem_n else 0.0
        self.lbl_destek_memnuniyet['value'].setText(f"{avg_mem:.1f}/5")
        self.sp_memnuniyet.setValue(avg_mem)

    # ------------------------------------------------------------------
    # SEKME 4 - FINANSAL (M2.3)
    # ------------------------------------------------------------------

    def _tab_finansal(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        # Ana finansal bilgiler
        gb = QGroupBox("Cari & Risk")
        gl = QGridLayout(gb)
        gl.setHorizontalSpacing(12)
        gl.setVerticalSpacing(8)

        gl.addWidget(QLabel("Zirve Cari Kodu"), 0, 0)
        self.ed_zirve_cari = QLineEdit()
        self.ed_zirve_cari.setPlaceholderText("ATLAS_KATAFOREZ_2026T.CARIGEN.CRK")
        gl.addWidget(self.ed_zirve_cari, 0, 1)

        gl.addWidget(QLabel("Para Birimi"), 0, 2)
        self.cb_fin_para = QComboBox()
        self.cb_fin_para.addItems(_PARA_BIRIMLERI)
        gl.addWidget(self.cb_fin_para, 0, 3)

        gl.addWidget(QLabel("Cari Bakiye"), 1, 0)
        self.sp_cari_bakiye = QDoubleSpinBox()
        self.sp_cari_bakiye.setRange(-99_999_999.0, 99_999_999.0)
        self.sp_cari_bakiye.setDecimals(2)
        gl.addWidget(self.sp_cari_bakiye, 1, 1)

        gl.addWidget(QLabel("Kredi Limiti"), 1, 2)
        self.sp_kredi_limit = QDoubleSpinBox()
        self.sp_kredi_limit.setMaximum(99_999_999.0)
        self.sp_kredi_limit.setDecimals(2)
        gl.addWidget(self.sp_kredi_limit, 1, 3)

        gl.addWidget(QLabel("Vade (gün)"), 2, 0)
        self.sp_vade = QSpinBox()
        self.sp_vade.setMaximum(365)
        gl.addWidget(self.sp_vade, 2, 1)

        gl.addWidget(QLabel("Risk Skoru"), 2, 2)
        self.cb_risk = QComboBox()
        self.cb_risk.setEditable(True)
        self.cb_risk.addItems(["", "DUSUK", "ORTA", "YUKSEK", "KRITIK"])
        gl.addWidget(self.cb_risk, 2, 3)

        gl.addWidget(QLabel("Son Ödeme Tarihi"), 3, 0)
        self.dt_son_odeme = QDateEdit()
        self.dt_son_odeme.setCalendarPopup(True)
        self.dt_son_odeme.setDisplayFormat("dd.MM.yyyy")
        self.dt_son_odeme.setMinimumDate(QDate(2000, 1, 1))
        self.dt_son_odeme.setSpecialValueText("Yok")
        gl.addWidget(self.dt_son_odeme, 3, 1)

        gl.addWidget(QLabel("Son Ödeme Tutarı"), 3, 2)
        self.sp_son_odeme_t = QDoubleSpinBox()
        self.sp_son_odeme_t.setMaximum(99_999_999.0)
        self.sp_son_odeme_t.setDecimals(2)
        gl.addWidget(self.sp_son_odeme_t, 3, 3)

        lay.addWidget(gb)

        # Banka bilgileri
        gb_b = QGroupBox("Banka Hesapları / IBAN")
        v = QVBoxLayout(gb_b)
        self.tbl_bankalar = QTableWidget(0, 5)
        self.tbl_bankalar.setHorizontalHeaderLabels([
            "Banka", "Şube", "Hesap No", "IBAN", "Para Birimi"
        ])
        self.tbl_bankalar.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tbl_bankalar.verticalHeader().setVisible(False)
        v.addWidget(self.tbl_bankalar)
        h = QHBoxLayout()
        h.addStretch()
        b1 = QPushButton("+ Banka Ekle")
        b1.clicked.connect(self._banka_ekle)
        b2 = QPushButton("- Sec Sil")
        b2.clicked.connect(lambda: self._satir_sil(self.tbl_bankalar))
        h.addWidget(b1)
        h.addWidget(b2)
        v.addLayout(h)
        lay.addWidget(gb_b, 1)

        # Notlar
        gb_n = QGroupBox("Finansal Notlar")
        vn = QVBoxLayout(gb_n)
        self.txt_finansal_notlar = QTextEdit()
        self.txt_finansal_notlar.setMaximumHeight(80)
        vn.addWidget(self.txt_finansal_notlar)
        lay.addWidget(gb_n)

        return w

    def _banka_ekle(self, data: Optional[dict] = None):
        data = data or {}
        r = self.tbl_bankalar.rowCount()
        self.tbl_bankalar.insertRow(r)
        for col, key in enumerate(['banka_adi', 'sube', 'hesap_no', 'iban'], start=0):
            self.tbl_bankalar.setItem(r, col, QTableWidgetItem(str(data.get(key, ''))))
        cb = QComboBox()
        cb.addItems(_PARA_BIRIMLERI)
        if data.get('para_birimi') in _PARA_BIRIMLERI:
            cb.setCurrentText(data['para_birimi'])
        else:
            cb.setCurrentText('TRY')
        self.tbl_bankalar.setCellWidget(r, 4, cb)

    # ------------------------------------------------------------------
    # SEKME 9 - AUDIT LOG (M2.5)
    # ------------------------------------------------------------------

    def _tab_audit(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        bilgi = QLabel(
            "Müşteri profilinde yapılan kritik değişiklikler (anlaşma, lisans, "
            "bakım, finansal, DB) burada otomatik kayıt altına alınır. Salt okunur."
        )
        bilgi.setWordWrap(True)
        bilgi.setStyleSheet(
            f"background: {brand.BG_CARD}; color: {brand.TEXT_DIM}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px 12px; font-size: 11px;"
        )
        lay.addWidget(bilgi)

        # Filtre
        h = QHBoxLayout()
        h.addWidget(QLabel("Kategori:"))
        self.cb_audit_filtre = QComboBox()
        self.cb_audit_filtre.addItem("Tümü", "")
        for k in _AUDIT_KATEGORILERI:
            self.cb_audit_filtre.addItem(k, k)
        self.cb_audit_filtre.currentIndexChanged.connect(self._audit_filtrele)
        h.addWidget(self.cb_audit_filtre)
        h.addStretch()
        b_temizle = QPushButton("Tümünü Temizle")
        b_temizle.setStyleSheet(f"QPushButton {{ background: {brand.ERROR}; color: white; border: none; "
                                f"border-radius: 6px; padding: 8px 14px; }}")
        b_temizle.clicked.connect(self._audit_temizle)
        h.addWidget(b_temizle)
        lay.addLayout(h)

        # Tablo
        self.tbl_audit = QTableWidget(0, 6)
        self.tbl_audit.setHorizontalHeaderLabels([
            "Tarih", "Kullanıcı", "Kategori", "Alan", "Eski Değer", "Yeni Değer"
        ])
        self.tbl_audit.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tbl_audit.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tbl_audit.verticalHeader().setVisible(False)
        self.tbl_audit.setEditTriggers(QTableWidget.NoEditTriggers)
        lay.addWidget(self.tbl_audit, 1)

        # Memory
        self._audit_log: list = []

        return w

    def _audit_yenile(self):
        kategori = self.cb_audit_filtre.currentData() or ""
        sirali = sorted(self._audit_log, key=lambda a: a.get('zaman', ''), reverse=True)
        self.tbl_audit.setRowCount(0)
        for a in sirali:
            if kategori and a.get('kategori') != kategori:
                continue
            r = self.tbl_audit.rowCount()
            self.tbl_audit.insertRow(r)
            zaman = (a.get('zaman') or '')[:16].replace('T', ' ')
            self.tbl_audit.setItem(r, 0, QTableWidgetItem(zaman))
            self.tbl_audit.setItem(r, 1, QTableWidgetItem(a.get('kullanici', '')))
            self.tbl_audit.setItem(r, 2, QTableWidgetItem(a.get('kategori', '')))
            self.tbl_audit.setItem(r, 3, QTableWidgetItem(a.get('alan', '')))
            self.tbl_audit.setItem(r, 4, QTableWidgetItem(str(a.get('eski', ''))))
            self.tbl_audit.setItem(r, 5, QTableWidgetItem(str(a.get('yeni', ''))))

    def _audit_filtrele(self):
        self._audit_yenile()

    def _audit_temizle(self):
        if QMessageBox.question(
            self, "Audit Log Temizle",
            "Tüm audit log kayıtları silinsin mi?\n\nBu işlem geri alınamaz."
        ) != QMessageBox.Yes:
            return
        self._audit_log = []
        self._audit_yenile()

    # ------------------------------------------------------------------
    # FILL & KAYDET
    # ------------------------------------------------------------------

    def _fill(self):
        p = self.profil

        # GENEL
        self.ed_kod.setText(self.original_kod)
        if not self.yeni_kayit:
            self.ed_kod.setReadOnly(True)
            self.ed_kod.setStyleSheet(f"background: {brand.BG_CARD}; color: {brand.TEXT_DIM};")
        self.ed_adi.setText(p.get('musteri_adi', ''))
        self.ed_kisa.setText(p.get('kisa_ad', ''))
        self.cb_tip.setCurrentText(p.get('musteri_tipi', 'AKTIF'))
        self.cb_durum.setCurrentText(p.get('durum', 'AKTIF'))
        self.cb_segment.setCurrentText(p.get('segment', ''))
        self.ed_sektor.setText(p.get('sektor', ''))

        self._logo_path = p.get('logo_path', '') or (p.get('company') or {}).get('logo_path', '')
        self._logo_onizle(self._logo_path)

        v = p.get('vergi') or {}
        self.ed_vergi_dairesi.setText(v.get('vergi_dairesi', ''))
        self.ed_vkn.setText(v.get('vkn_tckn', '') or (p.get('company') or {}).get('tax_id', ''))
        self.ed_mersis.setText(v.get('mersis_no', ''))

        il = p.get('iletisim') or {}
        self.ed_telefon.setText(il.get('telefon', '') or (p.get('company') or {}).get('phone', ''))
        self.ed_email.setText(il.get('email', '') or (p.get('company') or {}).get('email', ''))
        self.ed_web.setText(il.get('web', ''))

        rep = p.get('raporlama') or {}
        self.ed_sorumlu.setText(rep.get('sorumlu_personel', ''))
        et = rep.get('etiketler') or []
        self.ed_etiketler.setText(", ".join(et) if isinstance(et, list) else str(et))
        self.ed_kazanim.setText(rep.get('kazanim_kanali', ''))
        self.dt_ilk_satis.setDate(_str_to_qdate(rep.get('ilk_satis_tarihi', '')))

        # ADRESLER & KISILER
        for adr in (p.get('adresler') or []):
            if isinstance(adr, dict):
                self._satir_ekle_adres(adr)
        for k in (p.get('kisiler') or []):
            if isinstance(k, dict):
                self._satir_ekle_kisi(k)

        # ANLASMA
        a = p.get('anlasma') or {}
        self.ed_sozlesme_no.setText(a.get('sozlesme_no', ''))
        self.dt_baslangic.setDate(_str_to_qdate(a.get('baslangic_tarihi', '')))
        self.dt_bitis.setDate(_str_to_qdate(a.get('bitis_tarihi', '')))
        self.cb_yenileme.setCurrentText(a.get('yenileme_tipi', 'MANUEL'))
        self.ed_imza_pdf.setText(a.get('imza_pdf_path', ''))

        self.cb_lisans.setCurrentText(a.get('lisans_tipi', 'YILLIK'))
        self.cb_odeme.setCurrentText(a.get('odeme_periyodu', 'YILLIK'))
        self.sp_bedel.setValue(_safe_float(a.get('bedel', 0)))
        self.cb_para.setCurrentText(a.get('para_birimi', 'TRY'))
        self.chk_kdv_dahil.setChecked(bool(a.get('kdv_dahil', False)))
        self.sp_user_limit.setValue(_safe_int(a.get('kullanici_limiti', 0)))
        self.sp_ek_user.setValue(_safe_float(a.get('ek_kullanici_ucreti', 0)))
        self.txt_anlasma_notlar.setPlainText(a.get('notlar', ''))

        # BAKIM
        b = p.get('bakim') or {}
        self.chk_bakim_var.setChecked(bool(b.get('var', True)))
        self.sp_bakim_ucret.setValue(_safe_float(b.get('aylik_ucret', 0)))
        self.dt_sonraki_fatura.setDate(_str_to_qdate(b.get('sonraki_fatura_tarihi', '')))
        self.dt_bakim_bitis.setDate(_str_to_qdate(b.get('bitis_tarihi', '')))
        self.sp_yanit.setValue(_safe_int(b.get('yanit_suresi_saat', 4)))
        self.sp_cozum.setValue(_safe_int(b.get('cozum_suresi_saat', 24)))
        self.chk_destek_724.setChecked(bool(b.get('destek_7_24', False)))

        # DB & KURULUM
        db = p.get('database') or {}
        self.ed_db_server.setText(db.get('server', ''))
        self.ed_db_name.setText(db.get('database', ''))
        self.ed_db_user.setText(db.get('user', ''))
        self.ed_db_pwd.setText(decode_password(db.get('password', '')))
        self.chk_trusted.setChecked(bool(db.get('trusted_connection', False)))

        k = p.get('kurulum') or {}
        self.cb_kurulum_tip.setCurrentText(k.get('tip', 'ON_PREM'))
        self.ed_sql_surumu.setText(k.get('sql_surumu', ''))
        self.ed_nexor_v.setText(k.get('nexor_versiyonu', ''))
        self.dt_son_guncelleme.setDate(_str_to_qdate(k.get('son_guncelleme_tarihi', '')))

        # NAS
        nas = p.get('nas') or {}
        self.ed_nas_server.setText(nas.get('server', '') or '')
        nas_shares = nas.get('shares') or {}
        for key, _et, varsayilan, _ac in self._NAS_KEYS:
            ed = self._nas_inputs.get(key)
            if ed is not None:
                ed.setText(nas_shares.get(key, '') or '')

        # BELGELER
        for bg in (p.get('belgeler') or []):
            if not isinstance(bg, dict):
                continue
            r = self.tbl_belgeler.rowCount()
            self.tbl_belgeler.insertRow(r)
            cb = QComboBox()
            cb.addItems(_BELGE_TIPLERI)
            if bg.get('tip') in _BELGE_TIPLERI:
                cb.setCurrentText(bg['tip'])
            self.tbl_belgeler.setCellWidget(r, 0, cb)
            self.tbl_belgeler.setItem(r, 1, QTableWidgetItem(bg.get('dosya_yolu', '')))
            self.tbl_belgeler.setItem(r, 2, QTableWidgetItem(bg.get('eklenme_tarihi', '')))
            self.tbl_belgeler.setItem(r, 3, QTableWidgetItem(bg.get('aciklama', '')))

        # AKTIVITELER (M2.1)
        akt_list = p.get('aktiviteler') or []
        self._aktiviteler = [a for a in akt_list if isinstance(a, dict)]
        self._aktivite_yenile()

        # DESTEK (M2.2)
        d = p.get('destek') or {}
        ozet = d.get('ozet') or {}
        sz = (ozet.get('son_ziyaret_tarihi') or '').strip()
        if sz:
            self.dt_son_ziyaret.setDate(_str_to_qdate(sz))
        else:
            self.dt_son_ziyaret.setDate(QDate(2000, 1, 1))
        self.sp_memnuniyet.setValue(_safe_float(ozet.get('memnuniyet_skoru', 0)))
        for tk in (d.get('ticketlar') or []):
            if not isinstance(tk, dict):
                continue
            self._destek_ekle()
            r = self.tbl_destek.rowCount() - 1
            self.tbl_destek.setItem(r, 0, QTableWidgetItem(tk.get('no', '')))
            self.tbl_destek.setItem(r, 1, QTableWidgetItem(tk.get('tarih', '')))
            self.tbl_destek.setItem(r, 2, QTableWidgetItem(tk.get('baslik', '')))
            cb_d = self.tbl_destek.cellWidget(r, 3)
            if cb_d and tk.get('durum') in _TICKET_DURUMLARI:
                cb_d.setCurrentText(tk['durum'])
            cb_o = self.tbl_destek.cellWidget(r, 4)
            if cb_o and tk.get('oncelik') in _TICKET_ONCELIKLERI:
                cb_o.setCurrentText(tk['oncelik'])
            sp_y = self.tbl_destek.cellWidget(r, 5)
            if sp_y:
                sp_y.setValue(_safe_int(tk.get('yanit_dk', 0)))
            sp_c = self.tbl_destek.cellWidget(r, 6)
            if sp_c:
                sp_c.setValue(_safe_int(tk.get('cozum_dk', 0)))
            sp_m = self.tbl_destek.cellWidget(r, 7)
            if sp_m:
                sp_m.setValue(_safe_float(tk.get('memnuniyet', 0)))
        self._destek_kpi_hesapla()

        # FINANSAL (M2.3)
        fin = p.get('finansal') or {}
        self.ed_zirve_cari.setText(fin.get('zirve_cari_kodu', ''))
        self.cb_fin_para.setCurrentText(fin.get('para_birimi', 'TRY'))
        self.sp_cari_bakiye.setValue(_safe_float(fin.get('cari_bakiye', 0)))
        self.sp_kredi_limit.setValue(_safe_float(fin.get('kredi_limiti', 0)))
        self.sp_vade.setValue(_safe_int(fin.get('vade_gun', 30)))
        risk = fin.get('risk_skoru', '')
        self.cb_risk.setCurrentText(risk)
        so = (fin.get('son_odeme_tarihi') or '').strip()
        if so:
            self.dt_son_odeme.setDate(_str_to_qdate(so))
        else:
            self.dt_son_odeme.setDate(QDate(2000, 1, 1))
        self.sp_son_odeme_t.setValue(_safe_float(fin.get('son_odeme_tutari', 0)))
        self.txt_finansal_notlar.setPlainText(fin.get('notlar', ''))
        for bnk in (fin.get('bankalar') or []):
            if isinstance(bnk, dict):
                self._banka_ekle(bnk)

        # AUDIT LOG (M2.5)
        self._audit_log = [a for a in (p.get('audit_log') or []) if isinstance(a, dict)]
        self._audit_yenile()

    def _topla(self) -> dict:
        """Form alanlarini DEFAULT_PROFILE semasina uygun dict olarak topla."""
        kod = self.ed_kod.text().strip()
        adi = self.ed_adi.text().strip()
        if not kod or not adi:
            return {}

        # Adresler
        adresler = []
        for r in range(self.tbl_adresler.rowCount()):
            cb = self.tbl_adresler.cellWidget(r, 0)
            tip = cb.currentText() if cb else 'MERKEZ'
            adresler.append({
                'tip': tip,
                'baslik': self.tbl_adresler.item(r, 1).text() if self.tbl_adresler.item(r, 1) else '',
                'adres': self.tbl_adresler.item(r, 2).text() if self.tbl_adresler.item(r, 2) else '',
                'sehir': self.tbl_adresler.item(r, 3).text() if self.tbl_adresler.item(r, 3) else '',
                'ilce': self.tbl_adresler.item(r, 4).text() if self.tbl_adresler.item(r, 4) else '',
                'posta_kodu': self.tbl_adresler.item(r, 5).text() if self.tbl_adresler.item(r, 5) else '',
            })

        # Kisiler
        kisiler = []
        for r in range(self.tbl_kisiler.rowCount()):
            cb = self.tbl_kisiler.cellWidget(r, 4)
            rol = cb.currentText() if cb else 'DIGER'
            kisiler.append({
                'ad': self.tbl_kisiler.item(r, 0).text() if self.tbl_kisiler.item(r, 0) else '',
                'unvan': self.tbl_kisiler.item(r, 1).text() if self.tbl_kisiler.item(r, 1) else '',
                'telefon': self.tbl_kisiler.item(r, 2).text() if self.tbl_kisiler.item(r, 2) else '',
                'email': self.tbl_kisiler.item(r, 3).text() if self.tbl_kisiler.item(r, 3) else '',
                'rol': rol,
            })

        # Belgeler
        belgeler = []
        for r in range(self.tbl_belgeler.rowCount()):
            cb = self.tbl_belgeler.cellWidget(r, 0)
            tip = cb.currentText() if cb else 'DIGER'
            belgeler.append({
                'tip': tip,
                'dosya_yolu': self.tbl_belgeler.item(r, 1).text() if self.tbl_belgeler.item(r, 1) else '',
                'eklenme_tarihi': self.tbl_belgeler.item(r, 2).text() if self.tbl_belgeler.item(r, 2) else '',
                'aciklama': self.tbl_belgeler.item(r, 3).text() if self.tbl_belgeler.item(r, 3) else '',
            })

        etiketler_raw = self.ed_etiketler.text().strip()
        etiketler = [t.strip() for t in etiketler_raw.split(',') if t.strip()] if etiketler_raw else []

        return {
            'musteri_kodu': kod,
            'musteri_adi': adi,
            'kisa_ad': self.ed_kisa.text().strip(),
            'musteri_tipi': self.cb_tip.currentText(),
            'segment': self.cb_segment.currentText().strip(),
            'sektor': self.ed_sektor.text().strip(),
            'durum': self.cb_durum.currentText(),
            'logo_path': getattr(self, '_logo_path', '') or '',
            'udl_path': (self.profil.get('udl_path', '') if self.profil else ''),

            'vergi': {
                'vergi_dairesi': self.ed_vergi_dairesi.text().strip(),
                'vkn_tckn': self.ed_vkn.text().strip(),
                'mersis_no': self.ed_mersis.text().strip(),
            },
            'iletisim': {
                'telefon': self.ed_telefon.text().strip(),
                'email': self.ed_email.text().strip(),
                'web': self.ed_web.text().strip(),
            },
            'adresler': adresler,
            'kisiler': kisiler,

            'database': {
                'server': self.ed_db_server.text().strip(),
                'database': self.ed_db_name.text().strip(),
                'user': self.ed_db_user.text() if not self.chk_trusted.isChecked() else '',
                'password': encode_password(self.ed_db_pwd.text()) if not self.chk_trusted.isChecked() else '',
                'driver': 'ODBC Driver 18 for SQL Server',
                'timeout': 10,
                'max_connections': 20,
                'trusted_connection': self.chk_trusted.isChecked(),
            },
            'plc_database': self.profil.get('plc_database') or dict_default_plc(),
            'pdks': self.profil.get('pdks') or dict_default_pdks(),
            'company': {
                **(self.profil.get('company') or {}),
                'name': adi,
                'phone': self.ed_telefon.text().strip(),
                'email': self.ed_email.text().strip(),
                'tax_id': self.ed_vkn.text().strip(),
                'logo_path': getattr(self, '_logo_path', '') or '',
            },

            'anlasma': {
                'sozlesme_no': self.ed_sozlesme_no.text().strip(),
                'baslangic_tarihi': _qdate_to_str(self.dt_baslangic.date()),
                'bitis_tarihi': _qdate_to_str(self.dt_bitis.date()),
                'yenileme_tipi': self.cb_yenileme.currentText(),
                'lisans_tipi': self.cb_lisans.currentText(),
                'bedel': float(self.sp_bedel.value()),
                'para_birimi': self.cb_para.currentText(),
                'kdv_dahil': self.chk_kdv_dahil.isChecked(),
                'odeme_periyodu': self.cb_odeme.currentText(),
                'kullanici_limiti': int(self.sp_user_limit.value()),
                'ek_kullanici_ucreti': float(self.sp_ek_user.value()),
                'imza_pdf_path': self.ed_imza_pdf.text().strip(),
                'notlar': self.txt_anlasma_notlar.toPlainText().strip(),
            },
            'bakim': {
                'var': self.chk_bakim_var.isChecked(),
                'aylik_ucret': float(self.sp_bakim_ucret.value()),
                'sonraki_fatura_tarihi': _qdate_to_str(self.dt_sonraki_fatura.date()),
                'bitis_tarihi': _qdate_to_str(self.dt_bakim_bitis.date()),
                'yanit_suresi_saat': int(self.sp_yanit.value()),
                'cozum_suresi_saat': int(self.sp_cozum.value()),
                'destek_7_24': self.chk_destek_724.isChecked(),
            },
            'kurulum': {
                'tip': self.cb_kurulum_tip.currentText(),
                'sql_surumu': self.ed_sql_surumu.text().strip(),
                'nexor_versiyonu': self.ed_nexor_v.text().strip(),
                'son_guncelleme_tarihi': _qdate_to_str(self.dt_son_guncelleme.date()),
            },
            'belgeler': belgeler,
            'raporlama': {
                'sorumlu_personel': self.ed_sorumlu.text().strip(),
                'etiketler': etiketler,
                'kazanim_kanali': self.ed_kazanim.text().strip(),
                'ilk_satis_tarihi': _qdate_to_str(self.dt_ilk_satis.date()),
                'son_yenileme_tarihi': (self.profil.get('raporlama') or {}).get('son_yenileme_tarihi', ''),
            },
            'nas': {
                'server': self.ed_nas_server.text().strip() or 'AtlasNAS',
                'shares': {
                    key: (self._nas_inputs[key].text().strip() if self._nas_inputs.get(key) else '')
                    for key, _et, _var, _ac in self._NAS_KEYS
                },
            },

            # M2.1 - Aktiviteler (Chatter timeline)
            'aktiviteler': list(getattr(self, '_aktiviteler', [])),

            # M2.2 - Destek
            'destek': self._destek_topla(),

            # M2.3 - Finansal
            'finansal': self._finansal_topla(),

            # M2.5 - Audit log
            'audit_log': list(getattr(self, '_audit_log', [])),
        }

    def _destek_topla(self) -> dict:
        ticketlar = []
        for r in range(self.tbl_destek.rowCount()):
            cb_d = self.tbl_destek.cellWidget(r, 3)
            cb_o = self.tbl_destek.cellWidget(r, 4)
            sp_y = self.tbl_destek.cellWidget(r, 5)
            sp_c = self.tbl_destek.cellWidget(r, 6)
            sp_m = self.tbl_destek.cellWidget(r, 7)
            ticketlar.append({
                'no': self.tbl_destek.item(r, 0).text() if self.tbl_destek.item(r, 0) else '',
                'tarih': self.tbl_destek.item(r, 1).text() if self.tbl_destek.item(r, 1) else '',
                'baslik': self.tbl_destek.item(r, 2).text() if self.tbl_destek.item(r, 2) else '',
                'durum': cb_d.currentText() if cb_d else 'ACIK',
                'oncelik': cb_o.currentText() if cb_o else 'NORMAL',
                'yanit_dk': sp_y.value() if sp_y else 0,
                'cozum_dk': sp_c.value() if sp_c else 0,
                'memnuniyet': float(sp_m.value()) if sp_m else 0.0,
            })
        sz_d = self.dt_son_ziyaret.date()
        sz = '' if sz_d == QDate(2000, 1, 1) else _qdate_to_str(sz_d)

        # KPI'lari yeniden hesapla
        n = self.tbl_destek.rowCount()
        yanit_t = cozum_t = mem_t = 0.0
        yanit_n = cozum_n = mem_n = 0
        for r in range(n):
            sp_y = self.tbl_destek.cellWidget(r, 5)
            sp_c = self.tbl_destek.cellWidget(r, 6)
            sp_m = self.tbl_destek.cellWidget(r, 7)
            if sp_y and sp_y.value() > 0:
                yanit_t += sp_y.value(); yanit_n += 1
            if sp_c and sp_c.value() > 0:
                cozum_t += sp_c.value(); cozum_n += 1
            if sp_m and sp_m.value() > 0:
                mem_t += sp_m.value(); mem_n += 1

        return {
            'ozet': {
                'son_ziyaret_tarihi': sz,
                'memnuniyet_skoru': float(self.sp_memnuniyet.value()),
                'ortalama_yanit_dk': int(yanit_t / yanit_n) if yanit_n else 0,
                'ortalama_cozum_dk': int(cozum_t / cozum_n) if cozum_n else 0,
            },
            'ticketlar': ticketlar,
        }

    def _finansal_topla(self) -> dict:
        bankalar = []
        for r in range(self.tbl_bankalar.rowCount()):
            cb = self.tbl_bankalar.cellWidget(r, 4)
            bankalar.append({
                'banka_adi': self.tbl_bankalar.item(r, 0).text() if self.tbl_bankalar.item(r, 0) else '',
                'sube': self.tbl_bankalar.item(r, 1).text() if self.tbl_bankalar.item(r, 1) else '',
                'hesap_no': self.tbl_bankalar.item(r, 2).text() if self.tbl_bankalar.item(r, 2) else '',
                'iban': self.tbl_bankalar.item(r, 3).text() if self.tbl_bankalar.item(r, 3) else '',
                'para_birimi': cb.currentText() if cb else 'TRY',
            })
        so_d = self.dt_son_odeme.date()
        so = '' if so_d == QDate(2000, 1, 1) else _qdate_to_str(so_d)
        return {
            'zirve_cari_kodu': self.ed_zirve_cari.text().strip(),
            'cari_bakiye': float(self.sp_cari_bakiye.value()),
            'kredi_limiti': float(self.sp_kredi_limit.value()),
            'vade_gun': int(self.sp_vade.value()),
            'risk_skoru': self.cb_risk.currentText().strip(),
            'para_birimi': self.cb_fin_para.currentText(),
            'son_odeme_tarihi': so,
            'son_odeme_tutari': float(self.sp_son_odeme_t.value()),
            'notlar': self.txt_finansal_notlar.toPlainText().strip(),
            'bankalar': bankalar,
        }

    def _kaydet(self):
        data = self._topla()
        if not data:
            QMessageBox.warning(self, "Eksik Bilgi", "Musteri Kodu ve Unvan zorunlu.")
            return

        kod = data['musteri_kodu']

        # M2.6 - Logo dosyasini standart konuma kopyala (varsa)
        try:
            yeni_logo = self._logo_persiste(kod, getattr(self, '_logo_path', '') or '')
            if yeni_logo is not None:
                data['logo_path'] = yeni_logo
                if isinstance(data.get('company'), dict):
                    data['company']['logo_path'] = yeni_logo
        except Exception as e:
            QMessageBox.warning(self, "Logo Uyarisi", f"Logo kopyalanamadi:\n{e}")

        # M2.5 - Otomatik audit log: eski/yeni karsilastir
        if not self.yeni_kayit:
            eski_profil = config_manager.get_profile(kod) or {}
            yeni_audit = self._audit_kayitlari_uret(eski_profil, data)
            if yeni_audit:
                # Mevcut audit_log + yeni kayitlar
                mevcut = list(data.get('audit_log') or [])
                mevcut.extend(yeni_audit)
                # Son 500 kayitla sinirla
                data['audit_log'] = mevcut[-500:]

        # Yeni profil ise duplicate kontrolu
        if self.yeni_kayit:
            if kod in config_manager.list_profiles():
                QMessageBox.warning(self, "Mukerrer Kod", f"'{kod}' kodlu profil zaten mevcut.")
                return
            # Olusturma kaydi
            data['audit_log'] = [{
                'zaman': datetime.now().isoformat(timespec='seconds'),
                'kullanici': self._kim(),
                'kategori': 'DIGER',
                'alan': '_olusturma',
                'eski': '',
                'yeni': f'Profil olusturuldu: {kod}',
            }]
            ok = config_manager.add_profile(kod, data)
            if not ok:
                QMessageBox.critical(self, "Hata", "Profil olusturulamadi.")
                return
        else:
            # Mevcut profili guncelle (kod degismez, yeni_kayit=False oldugu icin readonly)
            profile_dict = config_manager.get_profile(kod)
            if profile_dict is None:
                QMessageBox.critical(self, "Hata", f"'{kod}' profili bulunamadi.")
                return
            profile_dict.clear()
            profile_dict.update(data)
            if not config_manager.save():
                QMessageBox.critical(self, "Hata", "Kaydetme basarisiz.")
                return

        # M2.7 - Master cloud tablosuna sync (best-effort, silent)
        try:
            from core.redline_master_sync import push_musteri
            push_musteri(kod)
        except Exception as e:
            # Cloud sync zorunlu degil; sessiz log
            print(f"[REDLINE_MASTER] Sync atlandi (kod={kod}): {e}")

        QMessageBox.information(self, "Kaydedildi", f"{kod} musterisi kaydedildi.")
        self.accept()

    # ------------------------------------------------------------------
    # YARDIMCI: AUDIT, LOGO, KIM
    # ------------------------------------------------------------------

    def _kim(self) -> str:
        """Aktif kullanici bilgisi (oturum varsa)."""
        try:
            import os
            return os.environ.get('USERNAME') or os.environ.get('USER') or 'bayi'
        except Exception:
            return 'bayi'

    def _gnested(self, d: dict, yol: str):
        """'a.b.c' yoluyla nested dict erisim."""
        cur = d
        for k in yol.split('.'):
            if not isinstance(cur, dict):
                return None
            cur = cur.get(k)
        return cur

    def _audit_kayitlari_uret(self, eski: dict, yeni: dict) -> list:
        """_AUDIT_ALANLARI listesinde tanimli alanlar icin eski!=yeni karsilastirip
        otomatik audit_log girisleri uret."""
        kayitlar = []
        kim = self._kim()
        zaman = datetime.now().isoformat(timespec='seconds')
        for yol, kategori, etiket in _AUDIT_ALANLARI:
            e = self._gnested(eski, yol)
            y = self._gnested(yeni, yol)
            # None vs '' ayni kabul et
            e_norm = '' if e is None else e
            y_norm = '' if y is None else y
            if e_norm == y_norm:
                continue
            kayitlar.append({
                'zaman': zaman,
                'kullanici': kim,
                'kategori': kategori,
                'alan': etiket,
                'eski': str(e_norm),
                'yeni': str(y_norm),
            })
        return kayitlar

    def _logo_persiste(self, kod: str, src: str) -> Optional[str]:
        """Logo dosyasini config/logos/{kod}.{ext} altina kopyala. None donerse degisiklik yok."""
        if not src:
            # Logo temizlendi mi?
            eski = (self.profil.get('logo_path') if not self.yeni_kayit else '') or ''
            if eski and os.path.exists(eski) and os.path.basename(eski).startswith(f"{kod}."):
                # Standart konumdaki logo silindi
                try:
                    os.remove(eski)
                except Exception:
                    pass
            return ''
        if not os.path.exists(src):
            return None  # path yok ama orijinal kayit; degistirme

        from pathlib import Path
        import shutil
        # Hedef dizin: config dizini altinda logos/
        try:
            from core.external_config import CONFIG_DIR
            hedef_dir = Path(CONFIG_DIR) / "logos"
        except Exception:
            hedef_dir = Path("logos")
        hedef_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(src).suffix.lower() or '.png'
        if ext not in {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}:
            ext = '.png'
        hedef = hedef_dir / f"{kod}{ext}"

        # Eger src zaten standart konumdaysa kopyalama
        try:
            if Path(src).resolve() == hedef.resolve():
                return str(hedef)
        except Exception:
            pass

        # Eski logoyu temizle (farkli ext olabilir)
        for old_ext in ('.png', '.jpg', '.jpeg', '.bmp', '.gif'):
            old = hedef_dir / f"{kod}{old_ext}"
            if old != hedef and old.exists():
                try:
                    old.unlink()
                except Exception:
                    pass

        shutil.copy2(src, hedef)
        return str(hedef)


def dict_default_plc() -> dict:
    from core.external_config import DEFAULT_PROFILE
    import copy
    return copy.deepcopy(DEFAULT_PROFILE['plc_database'])


def dict_default_pdks() -> dict:
    from core.external_config import DEFAULT_PROFILE
    import copy
    return copy.deepcopy(DEFAULT_PROFILE['pdks'])


# ============================================================================
# ANA SAYFA
# ============================================================================

class SistemMusteriYonetimiPage(BasePage):
    """Sistem > Musteri Yonetimi (sadece gelistirici_modu)"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.theme = theme
        self._setup_ui()
        self._yukle()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Musteri Yonetimi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {brand.TEXT};")
        header.addWidget(title)
        header.addStretch()

        self.lbl_durum = QLabel("")
        self.lbl_durum.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px; margin-right: 14px;")
        header.addWidget(self.lbl_durum)

        btn_yeni = QPushButton("+ Yeni Musteri")
        btn_yeni.setObjectName("primary")
        btn_yeni.setStyleSheet(f"""
            QPushButton#primary {{
                background: {brand.PRIMARY}; color: white; border: none;
                border-radius: 6px; padding: 8px 16px;
            }}
            QPushButton#primary:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        btn_yeni.clicked.connect(self._yeni)
        header.addWidget(btn_yeni)

        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(self._btn_stil())
        btn_yenile.clicked.connect(self._yukle)
        header.addWidget(btn_yenile)

        layout.addLayout(header)

        # Aktif profil bilgi seridi
        self.lbl_aktif = QLabel("")
        self.lbl_aktif.setWordWrap(True)
        self.lbl_aktif.setStyleSheet(f"""
            background: {brand.BG_CARD}; color: {brand.TEXT};
            border: 1px solid {brand.BORDER}; border-radius: 8px;
            padding: 10px 14px; font-size: 12px;
        """)
        layout.addWidget(self.lbl_aktif)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Aktif", "Kod", "Musteri Adi", "Tip", "Durum",
            "Bakim", "Bedel", "Bitis", "Islem"
        ])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 130)
        self.table.setColumnWidth(7, 110)
        self.table.setColumnWidth(8, 380)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD}; border: 1px solid {brand.BORDER};
                border-radius: 8px; gridline-color: {brand.BORDER};
                color: {brand.TEXT};
            }}
            QHeaderView::section {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                padding: 8px; border: none; font-weight: bold;
            }}
            QTableWidget::item:selected {{
                background: {brand.PRIMARY_SOFT}; color: {brand.TEXT};
            }}
        """)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.doubleClicked.connect(lambda: self._duzenle())
        layout.addWidget(self.table, 1)

    def _btn_stil(self) -> str:
        return f"""
            QPushButton {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                padding: 8px 14px;
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        """

    # ------------------------------------------------------------------
    # YUKLE
    # ------------------------------------------------------------------

    def _yukle(self):
        profiller = config_manager.list_profiles()
        aktif = config_manager.get_active_profile()

        # Aktif bilgi
        ap = config_manager.get_profile(aktif) or {}
        ap_db = ap.get('database') or {}
        self.lbl_aktif.setText(
            f"<b>Aktif Musteri:</b> {ap.get('musteri_adi') or aktif} "
            f"&nbsp;|&nbsp; <b>Profil Kodu:</b> {aktif} "
            f"&nbsp;|&nbsp; <b>DB:</b> {ap_db.get('server') or '?'} / {ap_db.get('database') or '?'}"
        )

        self.table.setRowCount(0)
        for kod in profiller:
            p = config_manager.get_profile(kod) or {}
            r = self.table.rowCount()
            self.table.insertRow(r)

            # Aktif badge
            aktif_lbl = QLabel("AKTIF" if kod == aktif else "")
            aktif_lbl.setAlignment(Qt.AlignCenter)
            if kod == aktif:
                aktif_lbl.setStyleSheet(
                    f"background: {brand.PRIMARY}; color: white; border-radius: 10px; "
                    "padding: 3px 8px; font-weight: bold; font-size: 10px;"
                )
            self.table.setCellWidget(r, 0, aktif_lbl)

            self.table.setItem(r, 1, QTableWidgetItem(kod))
            self.table.setItem(r, 2, QTableWidgetItem(p.get('musteri_adi', '')))
            self.table.setItem(r, 3, QTableWidgetItem(p.get('musteri_tipi', '')))
            self.table.setItem(r, 4, QTableWidgetItem(p.get('durum', '')))

            bakim = (p.get('bakim') or {}).get('var')
            self.table.setItem(r, 5, QTableWidgetItem("Var" if bakim else "Yok"))

            a = p.get('anlasma') or {}
            bedel = a.get('bedel') or 0
            para = a.get('para_birimi') or ''
            self.table.setItem(r, 6, QTableWidgetItem(f"{bedel:,.2f} {para}".strip()))
            self.table.setItem(r, 7, QTableWidgetItem(a.get('bitis_tarihi', '')))

            # Islem butonlari
            wrap = QWidget()
            hl = QHBoxLayout(wrap)
            hl.setContentsMargins(4, 2, 4, 2)
            hl.setSpacing(6)
            b_gec = QPushButton("Bu Musteriye Gec")
            b_gec.setStyleSheet(self._btn_islem_stil("#16A34A"))
            b_gec.clicked.connect(lambda _, k=kod: self._gec(k))
            if kod == aktif:
                b_gec.setEnabled(False)
            hl.addWidget(b_gec)

            b_d = QPushButton("Duzenle")
            b_d.setStyleSheet(self._btn_islem_stil("#2563EB"))
            b_d.clicked.connect(lambda _, k=kod: self._duzenle(k))
            hl.addWidget(b_d)

            b_m = QPushButton("Moduller")
            b_m.setStyleSheet(self._btn_islem_stil("#8B5CF6"))
            b_m.clicked.connect(lambda _, k=kod: self._moduller(k))
            hl.addWidget(b_m)

            b_s = QPushButton("Sil")
            b_s.setStyleSheet(self._btn_islem_stil("#DC2626"))
            b_s.clicked.connect(lambda _, k=kod: self._sil(k))
            if kod == aktif or len(profiller) <= 1:
                b_s.setEnabled(False)
            hl.addWidget(b_s)

            self.table.setCellWidget(r, 8, wrap)

        self.lbl_durum.setText(f"Toplam {len(profiller)} musteri")

    def _btn_islem_stil(self, color: str) -> str:
        return f"""
            QPushButton {{
                background: {color}; color: white; border: none;
                border-radius: 4px; padding: 4px 8px; font-size: 11px;
                font-weight: 600; min-width: 60px;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
            QPushButton:disabled {{ background: {brand.BG_HOVER}; color: {brand.TEXT_DIM}; }}
        """

    # ------------------------------------------------------------------
    # ISLEMLER
    # ------------------------------------------------------------------

    def _yeni(self):
        dlg = MusteriDetayDialog(self.theme, profil_adi="", parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._yukle()

    def _duzenle(self, kod: str = ""):
        if not kod:
            r = self.table.currentRow()
            if r < 0:
                return
            it = self.table.item(r, 1)
            kod = it.text() if it else ""
        if not kod:
            return
        dlg = MusteriDetayDialog(self.theme, profil_adi=kod, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._yukle()

    def _sil(self, kod: str):
        if QMessageBox.question(
            self, "Profil Sil",
            f"'{kod}' musteri profili silinsin mi?\n\nDB icerigi etkilenmez; sadece config'ten kaldirilir."
        ) != QMessageBox.Yes:
            return
        if config_manager.remove_profile(kod):
            QMessageBox.information(self, "Silindi", f"{kod} silindi.")
            self._yukle()
        else:
            QMessageBox.warning(self, "Silinemedi", "Aktif profil veya tek profil silinemez.")

    def _moduller(self, kod: str):
        """Bu musterinin modul lisanslarini yonet.

        Profile'in moduller_aktif config'i uzerinde calisir (her profile icin).
        Aktif profile ise degisiklikler aninda DB'deki lisans.modul_durumlari'na
        da yansitilir; pasif profillerde sadece config'e yazilir ve o musteri
        NEXOR'u acinca startup sync uygulanir.
        """
        dlg = MusteriModullerDialog(self.theme, profil_kodu=kod, parent=self)
        dlg.exec()
        self._yukle()

    def _gec(self, kod: str):
        if QMessageBox.question(
            self, "Profil Degistir",
            f"Aktif profil '{kod}' yapilacak.\n\n"
            "NEXOR'u kapatip yeniden acmaniz gerekecek (DB baglantisi yenilensin diye).\n\n"
            "Devam edilsin mi?"
        ) != QMessageBox.Yes:
            return
        if config_manager.set_active_profile(kod):
            QMessageBox.information(
                self, "Profil Degisti",
                f"Aktif profil: {kod}\n\nLutfen NEXOR'u kapatip yeniden acin."
            )
            self._yukle()
        else:
            QMessageBox.critical(self, "Hata", "Profil degistirilemedi.")


# ============================================================================
# MUSTERI MODULLER DIALOG (her profile icin config-bazli)
# ============================================================================

class MusteriModullerDialog(QDialog):
    """Bir musterinin modul lisanslarini yonet (config + opsiyonel DB sync).

    Tasarim:
    - Modul metadata (kod, ad, kategori, zorunlu) AKTIF DB'deki lisans.moduller'den
      okunur (bayinin mevcut kurulumunda 20 modul seed'i var).
    - Modul durumu (aktif/bitis/notlar) profile'in config'inde tutulur:
      profiles[X].moduller_aktif = {kod: {aktif, bitis_tarihi, notlar}, ...}
    - Aktif profile DUZENLENDIGINDE: degisiklikler DB'deki lisans.modul_durumlari'na
      DA UPSERT edilir (anlik etki).
    - Aktif olmayan profile DUZENLENDIGINDE: sadece config'e yazilir; o musteri
      NEXOR'u acinca startup sync (core/modul_lisans_sync.py) DB'ye yansitir.
    """

    def __init__(self, theme: dict, profil_kodu: str, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.profil_kodu = profil_kodu
        self.aktif_profil = (profil_kodu == config_manager.get_active_profile())
        profil = config_manager.get_profile(profil_kodu) or {}
        self.musteri_adi = profil.get('musteri_adi') or profil_kodu
        self._mevcut = (profil.get('moduller_aktif') or {}).copy()

        self.setWindowTitle(f"Modul Yonetimi - {self.musteri_adi}")
        self.setModal(True)
        self.setMinimumSize(900, 600)
        self._build_ui()
        self._fill_table()

    def _build_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QDateEdit {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 4px;
                padding: 4px 8px; min-height: 22px;
                selection-background-color: {brand.PRIMARY};
            }}
            QLineEdit:focus, QDateEdit:focus {{ border-color: {brand.PRIMARY}; }}
            QDateEdit::drop-down {{ border: none; width: 18px; }}
            QCheckBox {{ color: {brand.TEXT}; spacing: 6px; background: transparent; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 1.5px solid {brand.BORDER_HARD};
                border-radius: 4px;
                background: {brand.BG_INPUT};
            }}
            QCheckBox::indicator:hover {{ border-color: {brand.PRIMARY}; }}
            QCheckBox::indicator:checked {{
                background: {brand.PRIMARY};
                border: 1.5px solid {brand.PRIMARY};
            }}
            QCheckBox::indicator:disabled {{
                background: {brand.BG_HOVER};
                border-color: {brand.TEXT_DISABLED};
            }}
            QCheckBox::indicator:checked:disabled {{
                background: {brand.PRIMARY_HOVER};
                border-color: {brand.PRIMARY_HOVER};
            }}
            QPushButton {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                padding: 8px 16px; min-width: 100px;
            }}
            QPushButton#primary {{
                background: {brand.PRIMARY}; color: white; border: none;
            }}
            QPushButton#primary:hover {{ background: {brand.PRIMARY_HOVER}; }}
            QTableWidget {{
                background: {brand.BG_CARD}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                gridline-color: {brand.BORDER};
            }}
            QTableWidget::item {{ padding: 4px; }}
            QHeaderView::section {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                padding: 6px; border: none; font-weight: bold;
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        baslik = QLabel(f"<b style='font-size: 16px;'>{self.musteri_adi}</b>")
        lay.addWidget(baslik)

        if self.aktif_profil:
            bilgi_metni = (
                f"<b>Aktif musteri profili:</b> {self.profil_kodu}. "
                "Yapilan degisiklikler hem config.json'a hem DB'deki "
                "<code>lisans.modul_durumlari</code> tablosuna ANINDA yansir."
            )
            renk = brand.PRIMARY_SOFT
        else:
            bilgi_metni = (
                f"<b>Pasif musteri profili:</b> {self.profil_kodu}. "
                "Degisiklikler sadece config.json'a yazilir; bu musteri "
                "NEXOR'u acinca startup sync ile kendi DB'sine yansir."
            )
            renk = brand.BG_CARD

        bilgi = QLabel(bilgi_metni)
        bilgi.setWordWrap(True)
        bilgi.setStyleSheet(f"""
            background: {renk}; color: {brand.TEXT};
            border: 1px solid {brand.BORDER}; border-radius: 6px;
            padding: 8px 12px; font-size: 11px;
        """)
        lay.addWidget(bilgi)

        # Tablo
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(7)
        self.tbl.setHorizontalHeaderLabels([
            "Kod", "Modul Adi", "Kategori", "Zorunlu",
            "Aktif", "Bitis Tarihi", "Notlar"
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.tbl.setColumnWidth(0, 130)
        self.tbl.setColumnWidth(2, 110)
        self.tbl.setColumnWidth(3, 70)
        self.tbl.setColumnWidth(4, 60)
        self.tbl.setColumnWidth(5, 130)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QTableWidget.AllEditTriggers)
        self.tbl.verticalHeader().setDefaultSectionSize(38)
        lay.addWidget(self.tbl, 1)

        # Butonlar
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_iptal = QPushButton("Iptal")
        btn_iptal.clicked.connect(self.reject)
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setObjectName("primary")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_row.addWidget(btn_iptal)
        btn_row.addWidget(btn_kaydet)
        lay.addLayout(btn_row)

    def _modul_metadata(self) -> list:
        """lisans.moduller tablosundan modul listesini cek (aktif DB)."""
        from core.database import get_db_connection
        rows = []
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT modul_kodu, modul_adi, ISNULL(kategori, ''), ISNULL(zorunlu, 0), ISNULL(sira, 0)
                FROM lisans.moduller
                ORDER BY sira, modul_kodu
            """)
            for r in cur.fetchall():
                rows.append({
                    'kod': r[0],
                    'ad': r[1],
                    'kategori': r[2],
                    'zorunlu': bool(r[3]),
                })
            conn.close()
        except Exception as e:
            QMessageBox.critical(
                self, "Modul Listesi Hatasi",
                f"lisans.moduller tablosundan veri okunamadi:\n{e}"
            )
        return rows

    def _fill_table(self):
        moduller = self._modul_metadata()
        self.tbl.setRowCount(0)
        for m in moduller:
            kod = m['kod']
            mevcut = self._mevcut.get(kod) or {}
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)

            # Kod / Ad / Kategori (read-only)
            it_kod = QTableWidgetItem(kod)
            it_kod.setFlags(it_kod.flags() & ~Qt.ItemIsEditable)
            self.tbl.setItem(r, 0, it_kod)

            it_ad = QTableWidgetItem(m['ad'])
            it_ad.setFlags(it_ad.flags() & ~Qt.ItemIsEditable)
            self.tbl.setItem(r, 1, it_ad)

            it_kat = QTableWidgetItem(m['kategori'])
            it_kat.setFlags(it_kat.flags() & ~Qt.ItemIsEditable)
            self.tbl.setItem(r, 2, it_kat)

            # Zorunlu badge
            zorunlu_lbl = QLabel("EVET" if m['zorunlu'] else "")
            zorunlu_lbl.setAlignment(Qt.AlignCenter)
            if m['zorunlu']:
                zorunlu_lbl.setStyleSheet(
                    "background: #F59E0B; color: white; border-radius: 8px; "
                    "padding: 2px 8px; font-weight: bold; font-size: 10px;"
                )
            self.tbl.setCellWidget(r, 3, zorunlu_lbl)

            # Aktif checkbox
            chk = QCheckBox()
            # Mevcut yoksa varsayilan: zorunlu modul True, digerleri True (DB seed default)
            varsayilan_aktif = True
            chk.setChecked(bool(mevcut.get('aktif', varsayilan_aktif)))
            if m['zorunlu']:
                chk.setChecked(True)
                chk.setEnabled(False)
            wrap = QWidget()
            hl = QHBoxLayout(wrap)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.addStretch()
            hl.addWidget(chk)
            hl.addStretch()
            self.tbl.setCellWidget(r, 4, wrap)
            # Sonradan toplama icin sakla
            chk.setProperty('modul_kodu', kod)
            chk.setProperty('zorunlu', m['zorunlu'])

            # Bitis tarihi (bos = sinirsiz, sentinel: QDate(2000,1,1))
            de = QDateEdit()
            de.setCalendarPopup(True)
            de.setDisplayFormat("dd.MM.yyyy")
            de.setMinimumDate(QDate(2000, 1, 1))
            de.setSpecialValueText("Sinirsiz")
            bitis_str = (mevcut.get('bitis_tarihi') or '').strip()
            if bitis_str:
                de.setDate(_str_to_qdate(bitis_str))
            else:
                de.setDate(QDate(2000, 1, 1))  # "Sinirsiz" gosterilir
            self.tbl.setCellWidget(r, 5, de)

            # Notlar
            ed = QLineEdit()
            ed.setText(mevcut.get('notlar', '') or '')
            self.tbl.setCellWidget(r, 6, ed)

    def _kaydet(self):
        yeni: dict = {}
        for r in range(self.tbl.rowCount()):
            kod_item = self.tbl.item(r, 0)
            if not kod_item:
                continue
            kod = kod_item.text()

            chk_wrap = self.tbl.cellWidget(r, 4)
            chk = chk_wrap.findChild(QCheckBox) if chk_wrap else None
            zorunlu = bool(chk.property('zorunlu')) if chk else False
            aktif = bool(chk.isChecked()) if chk else True

            de = self.tbl.cellWidget(r, 5)
            bitis = ''
            if de:
                qd = de.date()
                if qd and qd.isValid() and qd != QDate(2000, 1, 1):
                    bitis = qd.toString("yyyy-MM-dd")

            ed = self.tbl.cellWidget(r, 6)
            notlar = ed.text().strip() if ed else ''

            # Zorunlu modul her zaman aktif (config'e yazmiyoruz)
            if zorunlu:
                continue

            yeni[kod] = {
                'aktif': aktif,
                'bitis_tarihi': bitis,
                'notlar': notlar,
            }

        # Profile'a yaz (aktif profile config_manager.set yonlendirir)
        if self.aktif_profil:
            config_manager.set('moduller_aktif', yeni)
        else:
            # Aktif olmayan profilin moduller_aktif'i icin direkt profile dict'i guncelle
            profile = config_manager.get_profile(self.profil_kodu)
            if profile is None:
                QMessageBox.critical(self, "Hata", f"'{self.profil_kodu}' profili bulunamadi.")
                return
            profile['moduller_aktif'] = yeni

        if not config_manager.save():
            QMessageBox.critical(self, "Hata", "Config dosyasi yazilamadi.")
            return

        # Aktif profile ise ANINDA DB'ye yansit + ModulServisi cache yenile
        if self.aktif_profil:
            try:
                from core.modul_lisans_sync import sync_config_to_db
                from core.modul_servisi import ModulServisi
                sync_config_to_db()
                ModulServisi.instance().yenile()
            except Exception as e:
                QMessageBox.warning(
                    self, "DB Sync Uyarisi",
                    f"Config kaydedildi ancak DB'ye yansitilamadi:\n{e}\n\n"
                    "NEXOR'u yeniden baslatip kontrol edin."
                )

        QMessageBox.information(
            self, "Kaydedildi",
            f"{len(yeni)} modul ayari kaydedildi.\n\n"
            + ("Aktif kurulumda anlik etkili." if self.aktif_profil
               else "Bu musteri NEXOR'u acinca DB'ye yansiyacak.")
        )
        self.accept()


# ============================================================================
# AKTIVITE DIALOG (M2.1 - Chatter ekleme/duzenleme)
# ============================================================================

class AktiviteDialog(QDialog):
    """Tek bir aktivite/notu ekleme/duzenleme."""

    def __init__(self, parent=None, mevcut: Optional[dict] = None):
        super().__init__(parent)
        self.mevcut = mevcut or {}
        self.setWindowTitle("Aktivite / Not" if not mevcut else "Aktivite Düzenle")
        self.setModal(True)
        self.setMinimumSize(560, 480)
        self._ek_dosyalar: list = list(self.mevcut.get('ek_dosyalar') or [])
        self._build_ui()
        self._fill()

    def _build_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QTextEdit, QComboBox, QDateEdit {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                padding: 6px 8px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border-color: {brand.PRIMARY};
            }}
            QPushButton {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                padding: 8px 14px; min-width: 80px;
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
            QPushButton#primary {{ background: {brand.PRIMARY}; color: white; border: none; }}
            QPushButton#primary:hover {{ background: {brand.PRIMARY_HOVER}; }}
            QListWidget {{
                background: {brand.BG_CARD}; border: 1px solid {brand.BORDER};
                color: {brand.TEXT}; border-radius: 6px;
            }}
        """)
        from PySide6.QtWidgets import QListWidget, QDateTimeEdit
        from PySide6.QtCore import QDateTime

        ana = QVBoxLayout(self)
        ana.setContentsMargins(16, 16, 16, 16)
        ana.setSpacing(10)

        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.DontWrapRows)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.cb_tip = QComboBox()
        for t in _AKTIVITE_TIPLERI:
            self.cb_tip.addItem(f"{_AKTIVITE_IKONLARI.get(t,'')} {t}", t)
        form.addRow("Tip", self.cb_tip)

        self.dt_zaman = QDateTimeEdit()
        self.dt_zaman.setCalendarPopup(True)
        self.dt_zaman.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.dt_zaman.setDateTime(QDateTime.currentDateTime())
        form.addRow("Zaman", self.dt_zaman)

        self.ed_kullanici = QLineEdit()
        try:
            import os
            self.ed_kullanici.setText(os.environ.get('USERNAME') or os.environ.get('USER') or '')
        except Exception:
            pass
        form.addRow("Kullanıcı", self.ed_kullanici)

        self.ed_baslik = QLineEdit()
        self.ed_baslik.setPlaceholderText("Kısa başlık...")
        form.addRow("Başlık *", self.ed_baslik)

        self.txt_icerik = QTextEdit()
        self.txt_icerik.setPlaceholderText("Detaylı not / görüşme özeti...")
        form.addRow("İçerik", self.txt_icerik)

        ana.addLayout(form)

        # Ek dosyalar
        gb = QGroupBox("Ek Dosyalar")
        v = QVBoxLayout(gb)
        self.lst_ek = QListWidget()
        self.lst_ek.setMaximumHeight(110)
        v.addWidget(self.lst_ek)
        eh = QHBoxLayout()
        eh.addStretch()
        b_e = QPushButton("+ Dosya Ekle")
        b_e.clicked.connect(self._ek_ekle)
        b_s = QPushButton("- Sec Sil")
        b_s.clicked.connect(self._ek_sil)
        eh.addWidget(b_e)
        eh.addWidget(b_s)
        v.addLayout(eh)
        ana.addWidget(gb)

        # Butonlar
        h = QHBoxLayout()
        h.addStretch()
        b_iptal = QPushButton("İptal")
        b_iptal.clicked.connect(self.reject)
        b_kaydet = QPushButton("Kaydet")
        b_kaydet.setObjectName("primary")
        b_kaydet.clicked.connect(self._kaydet)
        h.addWidget(b_iptal)
        h.addWidget(b_kaydet)
        ana.addLayout(h)

    def _fill(self):
        if not self.mevcut:
            return
        from PySide6.QtCore import QDateTime
        m = self.mevcut
        tip = m.get('tip', 'NOT')
        idx = self.cb_tip.findData(tip)
        if idx >= 0:
            self.cb_tip.setCurrentIndex(idx)
        zaman = m.get('zaman') or ''
        if zaman:
            try:
                dt = QDateTime.fromString(zaman[:19], "yyyy-MM-ddTHH:mm:ss")
                if dt.isValid():
                    self.dt_zaman.setDateTime(dt)
            except Exception:
                pass
        self.ed_kullanici.setText(m.get('kullanici', ''))
        self.ed_baslik.setText(m.get('baslik', ''))
        self.txt_icerik.setPlainText(m.get('icerik', ''))
        self._ek_dosyalar_yenile()

    def _ek_ekle(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Ek Dosya Sec", "", "Tum Dosyalar (*.*)")
        if not paths:
            return
        for p in paths:
            if p and p not in self._ek_dosyalar:
                self._ek_dosyalar.append(p)
        self._ek_dosyalar_yenile()

    def _ek_sil(self):
        r = self.lst_ek.currentRow()
        if 0 <= r < len(self._ek_dosyalar):
            self._ek_dosyalar.pop(r)
            self._ek_dosyalar_yenile()

    def _ek_dosyalar_yenile(self):
        self.lst_ek.clear()
        for p in self._ek_dosyalar:
            self.lst_ek.addItem(os.path.basename(p) + "  -  " + p)

    def _kaydet(self):
        baslik = self.ed_baslik.text().strip()
        if not baslik:
            QMessageBox.warning(self, "Eksik", "Başlık zorunludur.")
            return
        self.accept()

    def veri(self) -> dict:
        zaman = self.dt_zaman.dateTime().toString("yyyy-MM-ddTHH:mm:ss")
        return {
            'zaman': zaman,
            'tip': self.cb_tip.currentData() or 'NOT',
            'kullanici': self.ed_kullanici.text().strip(),
            'baslik': self.ed_baslik.text().strip(),
            'icerik': self.txt_icerik.toPlainText().strip(),
            'ek_dosyalar': list(self._ek_dosyalar),
        }
