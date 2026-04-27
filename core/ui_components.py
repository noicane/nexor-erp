# -*- coding: utf-8 -*-
"""
NEXOR ERP - Standart UI Bilesenleri

Tum ekranlarda tutarli gorsel: form layout, input stilleri, KPI kartlari,
ScrollArea, tablo standartlari.

Kullanim:
    from core.ui_components import (
        setup_form, standart_stylesheet, make_kpi_card,
        make_scrollable_form, setup_data_table
    )

    # 1. Form layout standart
    form = QFormLayout()
    setup_form(form)
    form.addRow("Etiket:", widget)

    # 2. Sayfa stylesheet (input min-height vb.)
    self.setStyleSheet(standart_stylesheet())

    # 3. Uzun formu scrollable yap (KPI ve butonlar disinda kalir)
    scroll = make_scrollable_form()
    inner_layout = scroll.widget().layout()  # buraya gruplari ekle

    # 4. KPI kart
    card = make_kpi_card("Genel OEE", "%82.3", brand.SUCCESS, alt="Iyi seviyede")

    # 5. Standart tablo (5+ kolon icin)
    setup_data_table(self.tbl, stretch_kolonu=2)
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout, QFrame, QHeaderView, QLabel, QScrollArea, QTableWidget,
    QVBoxLayout, QWidget,
)

from core.nexor_brand import brand


# ============================================================================
# 1. FORM LAYOUT (QFormLayout standart)
# ============================================================================

def setup_form(form: QFormLayout, kompakt: bool = False) -> None:
    """QFormLayout'u tutarli hale getir.

    - Label sol, field genis ve ayni hizada
    - Satirlar yukari binmesin (DontWrapRows)
    - Field'lar yatayda doldurur (AllNonFixedFieldsGrow)

    Args:
        kompakt: True ise daha az padding (modal dialog vb. icin)
    """
    form.setRowWrapPolicy(QFormLayout.DontWrapRows)
    form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
    if kompakt:
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setContentsMargins(10, 12, 10, 10)
    else:
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)
        form.setContentsMargins(14, 18, 14, 14)


# ============================================================================
# 2. SAYFA STYLESHEET (input, groupbox, label)
# ============================================================================

def standart_stylesheet() -> str:
    """Tum sayfalarin uzerinde uygulayacagi temel stylesheet.

    QGroupBox title hizalama, input min-height, focus highlight, label renk.
    """
    return f"""
        QLabel {{
            color: {brand.TEXT};
            background: transparent;
        }}
        QGroupBox {{
            color: {brand.TEXT};
            border: 1px solid {brand.BORDER};
            border-radius: 8px;
            margin-top: 14px;
            font-weight: bold;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px; padding: 0 6px;
            background: {brand.BG_MAIN};
            color: {brand.TEXT};
        }}
        QLineEdit, QDoubleSpinBox, QSpinBox, QDateEdit, QDateTimeEdit,
        QComboBox, QTextEdit {{
            background: {brand.BG_INPUT};
            color: {brand.TEXT};
            border: 1px solid {brand.BORDER};
            border-radius: 6px;
            padding: 5px 8px;
            min-height: 22px;
            selection-background-color: {brand.PRIMARY};
        }}
        QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus,
        QDateEdit:focus, QDateTimeEdit:focus, QComboBox:focus, QTextEdit:focus {{
            border-color: {brand.PRIMARY};
        }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox QAbstractItemView {{
            background: {brand.BG_CARD};
            color: {brand.TEXT};
            selection-background-color: {brand.PRIMARY};
            border: 1px solid {brand.BORDER};
        }}
        QCheckBox {{
            color: {brand.TEXT};
            spacing: 6px;
            background: transparent;
        }}
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
        QPushButton {{
            background: {brand.BG_INPUT};
            color: {brand.TEXT};
            border: 1px solid {brand.BORDER};
            border-radius: 6px;
            padding: 8px 14px;
            min-width: 90px;
        }}
        QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        QPushButton:disabled {{
            background: {brand.BG_HOVER};
            color: {brand.TEXT_DIM};
        }}
        QPushButton#primary {{
            background: {brand.PRIMARY};
            color: white;
            border: none;
            font-weight: bold;
        }}
        QPushButton#primary:hover {{ background: {brand.PRIMARY_HOVER}; }}
        QPushButton#danger {{
            background: {brand.ERROR};
            color: white;
            border: none;
            font-weight: bold;
        }}
        QPushButton#success {{
            background: {brand.SUCCESS};
            color: white;
            border: none;
            font-weight: bold;
        }}
    """


# ============================================================================
# 3. KPI KART (KPI / sayisal ozet kartlari)
# ============================================================================

def make_kpi_card(
    baslik: str,
    deger: str,
    renk: str,
    alt: Optional[str] = None,
    deger_font_px: int = 22,
) -> QFrame:
    """Standart KPI ozet karti.

    Args:
        baslik: Kart ust etiketi (kucuk, gri)
        deger: Buyuk metin (renk parametresinde)
        renk: brand.SUCCESS / brand.WARNING / brand.PRIMARY vb.
        alt: Optional alt aciklama (kucuk, gri)
        deger_font_px: Buyuk degerin font boyutu (default 22)
    """
    f = QFrame()
    f.setObjectName("kpi_card")
    f.setStyleSheet(
        f"QFrame#kpi_card {{ background: {brand.BG_CARD}; "
        f"border: 1px solid {brand.BORDER}; border-radius: 10px; "
        f"padding: 10px 14px; }}"
    )
    v = QVBoxLayout(f)
    v.setContentsMargins(12, 8, 12, 8)
    v.setSpacing(2)

    b = QLabel(baslik)
    b.setObjectName("kpi_baslik")
    b.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px; font-weight: bold;")
    v.addWidget(b)

    d = QLabel(deger)
    d.setObjectName("kpi_deger")
    d.setStyleSheet(f"color: {renk}; font-size: {deger_font_px}px; font-weight: bold;")
    v.addWidget(d)

    if alt:
        a = QLabel(alt)
        a.setObjectName("kpi_alt")
        a.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 10px;")
        a.setWordWrap(True)
        v.addWidget(a)

    return f


# ============================================================================
# 4. SCROLLABLE FORM WRAPPER
# ============================================================================

def make_scrollable_form() -> QScrollArea:
    """Uzun formlar icin standart ScrollArea sarmali.

    Donus degeri ScrollArea — `.widget().layout()` ile icine widget eklersin.
    Alttaki KPI kartlari ve butonlar bu wrapper'in DISINDA kalmalı (sticky).

    Ornek:
        scroll = make_scrollable_form()
        inner = scroll.widget()
        layout = inner.layout()  # zaten QVBoxLayout
        layout.addWidget(group_hammadde)
        layout.addWidget(group_iscilik)
        ...
        layout.addStretch()
    """
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet(
        f"QScrollArea {{ border: none; background: transparent; }}"
        f"QScrollBar:vertical {{ background: {brand.BG_CARD}; width: 10px; }}"
        f"QScrollBar::handle:vertical {{ background: {brand.BORDER}; border-radius: 5px; }}"
        f"QScrollBar::handle:vertical:hover {{ background: {brand.BORDER_HARD}; }}"
        f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}"
    )

    inner = QWidget()
    layout = QVBoxLayout(inner)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    scroll.setWidget(inner)

    return scroll


# ============================================================================
# 5. TABLO STANDART (5+ kolonlu QTableWidget icin)
# ============================================================================

def setup_data_table(
    tbl: QTableWidget,
    stretch_kolon_indexi: Optional[int] = None,
    satir_yuksekligi: int = 34,
    secim_modu: str = "row",  # "row", "single", "none"
) -> None:
    """Standart QTableWidget gorunumu.

    - Vertical header gizli
    - NoEditTriggers (read-only)
    - Alternating row colors
    - Selection mode: row (varsayilan)
    - Default row height
    - Stylesheet (BG_CARD + alternating BG_INPUT + selected PRIMARY_SOFT)

    Args:
        tbl: Stillenecek tablo
        stretch_kolon_indexi: Bu kolon kalan alani doldurur (None: hicbiri)
        satir_yuksekligi: Default row height (px)
        secim_modu: "row" (satir secimi), "single" (tek hucre), "none"
    """
    h = tbl.horizontalHeader()
    if stretch_kolon_indexi is not None:
        h.setSectionResizeMode(stretch_kolon_indexi, QHeaderView.Stretch)

    tbl.verticalHeader().setVisible(False)
    tbl.verticalHeader().setDefaultSectionSize(satir_yuksekligi)
    tbl.setEditTriggers(QTableWidget.NoEditTriggers)
    tbl.setAlternatingRowColors(True)

    if secim_modu == "row":
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.setSelectionMode(QTableWidget.SingleSelection)
    elif secim_modu == "single":
        tbl.setSelectionBehavior(QTableWidget.SelectItems)
        tbl.setSelectionMode(QTableWidget.SingleSelection)
    else:
        tbl.setSelectionMode(QTableWidget.NoSelection)

    tbl.setStyleSheet(f"""
        QTableWidget {{
            background: {brand.BG_CARD};
            color: {brand.TEXT};
            border: 1px solid {brand.BORDER};
            border-radius: 8px;
            gridline-color: {brand.BORDER};
            alternate-background-color: {brand.BG_INPUT};
        }}
        QHeaderView::section {{
            background: {brand.BG_INPUT};
            color: {brand.TEXT};
            padding: 8px;
            border: none;
            font-weight: bold;
        }}
        QTableWidget::item:selected {{
            background: {brand.PRIMARY_SOFT};
            color: {brand.TEXT};
        }}
    """)


# ============================================================================
# 6. RENK KODLARI - PERFORMANS YUZDESI
# ============================================================================

def renk_yuzde(yuzde: float) -> str:
    """0.0 - 1.0 araligindaki performans yuzdesine gore brand renk kodu.

    %85+: SUCCESS (yesil)
    %60-85: WARNING (sari)
    %40-60: turuncu (#F97316)
    <%40: ERROR (kirmizi)
    """
    if yuzde >= 0.85:
        return brand.SUCCESS
    if yuzde >= 0.60:
        return brand.WARNING
    if yuzde >= 0.40:
        return "#F97316"
    return brand.ERROR


# ============================================================================
# 7. BILGI BANNERI (sayfa ust kismindaki aciklama serit)
# ============================================================================

def make_info_banner(metin: str) -> QLabel:
    """Sayfa ustundeki kucuk gri aciklama bannera.

    HTML destekler (b, code, br vs.).
    """
    lbl = QLabel(metin)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"background: {brand.BG_CARD}; color: {brand.TEXT_DIM}; "
        f"border: 1px solid {brand.BORDER}; border-radius: 6px; "
        f"padding: 8px 12px; font-size: 11px;"
    )
    return lbl
