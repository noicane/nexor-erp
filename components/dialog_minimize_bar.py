# -*- coding: utf-8 -*-
"""
NEXOR ERP - Dialog Minimize Bar
Acik dialog'lari alt cubuga minimize edip geri getirme ozelligi.

Kullanim:
    from components.dialog_minimize_bar import add_minimize_button
    add_minimize_button(dialog)
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QScrollArea, QDialog
)
from PySide6.QtCore import Qt

_bar_instance = None


def get_minimize_bar():
    """Global minimize bar instance'ini dondur."""
    return _bar_instance


def add_minimize_button(dialog: QDialog):
    """
    Herhangi bir QDialog'a minimize butonu ekler.
    Layout'un en ustune kucuk bir header ekler.
    """
    bar = get_minimize_bar()
    if bar is None:
        return

    layout = dialog.layout()
    if layout is None:
        return

    theme = getattr(dialog, 'theme', {})

    header = QWidget()
    header.setFixedHeight(22)
    header.setStyleSheet("background: transparent;")
    h_layout = QHBoxLayout(header)
    h_layout.setContentsMargins(0, 0, 0, 0)
    h_layout.setSpacing(0)
    h_layout.addStretch()

    min_btn = QPushButton("_")
    min_btn.setFixedSize(28, 18)
    min_btn.setCursor(Qt.PointingHandCursor)
    min_btn.setToolTip("Asagi Al")
    min_btn.setStyleSheet(f"""
        QPushButton {{
            background: {theme.get('bg_input', '#232C3B')};
            color: {theme.get('text', '#E8ECF1')};
            border: 1px solid {theme.get('border', '#1E2736')};
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: {theme.get('warning', '#F59E0B')};
            color: #000;
        }}
    """)
    min_btn.clicked.connect(lambda: bar.minimize_dialog(dialog))
    h_layout.addWidget(min_btn)

    layout.insertWidget(0, header)


class DialogMinimizeBar(QWidget):
    """
    Ana pencerenin altinda yer alan bar.
    Minimize edilen dialog'lar burada kucuk buton olarak gorunur.
    """

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._dialogs = {}  # {did: (dialog, button, was_modal)}
        self.setFixedHeight(0)
        self._setup_ui()

        global _bar_instance
        _bar_instance = self

    def _setup_ui(self):
        t = self.theme
        self.setStyleSheet(f"""
            QWidget#minimizeBar {{
                background: {t.get('bg_card', '#151B23')};
                border-top: 2px solid {t.get('primary', '#DC2626')};
            }}
        """)
        self.setObjectName("minimizeBar")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(36)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._btn_container = QWidget()
        self._btn_layout = QHBoxLayout(self._btn_container)
        self._btn_layout.setContentsMargins(0, 0, 0, 0)
        self._btn_layout.setSpacing(6)
        self._btn_layout.setAlignment(Qt.AlignLeft)

        scroll.setWidget(self._btn_container)
        main_layout.addWidget(scroll)

    def minimize_dialog(self, dialog: QDialog):
        """Dialog'u minimize et - gizle ve bar'a buton ekle."""
        did = id(dialog)
        if did in self._dialogs:
            return

        # Modal durumunu kaydet, sonra kaldir ki ana pencere kullanilabilsin
        was_modal = dialog.isModal()
        if was_modal:
            dialog.setModal(False)

        dialog.hide()

        title = dialog.windowTitle() or "Dialog"
        if len(title) > 30:
            title = title[:27] + "..."

        t = self.theme
        btn = QPushButton(f"  {title}  ")
        btn.setFixedHeight(28)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(f"{dialog.windowTitle()}\nTikla: Geri getir")
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.get('bg_input', '#232C3B')};
                color: {t.get('text', '#E8ECF1')};
                border: 1px solid {t.get('border', '#1E2736')};
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background: {t.get('primary', '#DC2626')};
                color: white;
                border-color: {t.get('primary', '#DC2626')};
            }}
        """)

        btn.clicked.connect(lambda: self._restore_dialog(did))
        dialog.destroyed.connect(lambda: self._remove_dialog(did))

        self._btn_layout.addWidget(btn)
        self._dialogs[did] = (dialog, btn, was_modal)
        self._update_visibility()

    def _restore_dialog(self, did):
        """Dialog'u geri getir."""
        if did not in self._dialogs:
            return
        dialog, btn, was_modal = self._dialogs.pop(did)
        btn.deleteLater()
        self._update_visibility()

        # Modal durumunu geri yukle
        if was_modal:
            dialog.setModal(True)

        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _remove_dialog(self, did):
        """Dialog kapandiginda temizle."""
        if did not in self._dialogs:
            return
        _, btn, _ = self._dialogs.pop(did)
        btn.deleteLater()
        self._update_visibility()

    def _update_visibility(self):
        if self._dialogs:
            self.setFixedHeight(44)
        else:
            self.setFixedHeight(0)

    def count(self):
        return len(self._dialogs)
