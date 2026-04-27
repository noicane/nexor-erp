# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Table Cell Widgets
QTableWidget hucrelerine yerlesecek duzenlenebilir widget'lar icin fabrika fonksiyonlari.

Neden merkezi: Hucrenin icinde QSpinBox/QDoubleSpinBox/QLineEdit kullanildiginda
varsayilan stil + buton oklari hucreye sigmiyor, sayilar kesiliyor. Bu modul
standart boyut + padding + no-buttons + saga hiza kurallarini tek yerde tutar.

Kullanim:
    from components.table_cell_widgets import make_cell_spinbox, make_cell_lineedit, col_width_for_number

    # Miktar kolonu (max 9999 -> min 100px)
    table.setColumnWidth(5, col_width_for_number(9999))
    spin = make_cell_spinbox(max_val=9999, initial=160)
    table.setCellWidget(row, 5, spin)

    # Neden / metin kolonu
    table.setColumnWidth(6, 220)
    neden = make_cell_lineedit(placeholder="Neden...")
    table.setCellWidget(row, 6, neden)
"""
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox, QCheckBox, QDoubleSpinBox, QHBoxLayout,
    QLineEdit, QSpinBox, QWidget
)

from core.nexor_brand import brand


# Sabitler - tum tablo hucre widget'lari ayni metrikleri kullansin
CELL_HEIGHT = 32
CELL_PADDING = "4px 8px"
MIN_WIDTH_NUMBER = 100  # 4 haneli sayi + hafif pay (no-buttons modunda)
MIN_WIDTH_TEXT = 160


def _base_input_style(extra: str = "") -> str:
    """Hucre icine yerlesecek QLineEdit / QSpinBox icin ortak stil."""
    return f"""
        background: {brand.BG_INPUT};
        border: 1px solid {brand.BORDER};
        border-radius: 4px;
        padding: {CELL_PADDING};
        color: {brand.TEXT};
        font-size: 13px;
        {extra}
    """


def make_cell_spinbox(
    max_val: float,
    initial: float = 0,
    min_val: float = 0,
    decimals: int = 0,
    show_buttons: bool = False,
    parent: Optional[QWidget] = None,
) -> QDoubleSpinBox:
    """
    Tablo hucresi icin standart sayisal giris.

    Varsayilan: buton oklari gizli (sayilar kesilmesin), saga hizali, 32px yukseklik.
    Kullanici dogrudan yazip deger degistirir. Buton gerekli ise show_buttons=True.
    """
    spin = QDoubleSpinBox(parent)
    spin.setDecimals(decimals)
    spin.setRange(min_val, float(max_val))
    spin.setValue(float(initial))
    spin.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    spin.setMinimumHeight(CELL_HEIGHT)
    if not show_buttons:
        spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
    spin.setStyleSheet(f"QDoubleSpinBox {{ {_base_input_style()} }}")
    return spin


def make_cell_intspinbox(
    max_val: int,
    initial: int = 0,
    min_val: int = 0,
    show_buttons: bool = False,
    parent: Optional[QWidget] = None,
) -> QSpinBox:
    """Integer varyant - decimals=0 ile QSpinBox kullanir."""
    spin = QSpinBox(parent)
    spin.setRange(int(min_val), int(max_val))
    spin.setValue(int(initial))
    spin.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    spin.setMinimumHeight(CELL_HEIGHT)
    if not show_buttons:
        spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
    spin.setStyleSheet(f"QSpinBox {{ {_base_input_style()} }}")
    return spin


def make_cell_lineedit(
    placeholder: str = "",
    text: str = "",
    parent: Optional[QWidget] = None,
) -> QLineEdit:
    """Tablo hucresi icin standart tek satir metin girisi."""
    le = QLineEdit(parent)
    if placeholder:
        le.setPlaceholderText(placeholder)
    if text:
        le.setText(text)
    le.setMinimumHeight(CELL_HEIGHT)
    le.setStyleSheet(f"QLineEdit {{ {_base_input_style()} }}")
    return le


def make_cell_checkbox(
    checked: bool = False,
    parent: Optional[QWidget] = None,
) -> tuple:
    """
    Ortalanmis checkbox + wrapper. setCellWidget'a wrapper verilir,
    deger erisimi icin chk donulur.

    Returns: (wrapper_widget, checkbox)
    """
    wrapper = QWidget(parent)
    layout = QHBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignCenter)
    chk = QCheckBox()
    chk.setChecked(checked)
    chk.setStyleSheet("""
        QCheckBox::indicator { width: 22px; height: 22px; }
    """)
    layout.addWidget(chk)
    return wrapper, chk


def col_width_for_number(max_val: float, show_buttons: bool = False) -> int:
    """
    Bir sayi kolonu icin tavsiye edilen minimum genislik.

    Kural: basamak sayisi * 10 + 40 padding, en az MIN_WIDTH_NUMBER.
    Butonlu ise +24 ekle.
    """
    digits = len(f"{int(max_val):,}")  # 1.000 -> "1,000" -> 5 karakter
    base = digits * 10 + 40
    if show_buttons:
        base += 24
    return max(MIN_WIDTH_NUMBER, base)
