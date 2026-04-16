# -*- coding: utf-8 -*-
"""
NEXOR ERP - Global Arama Dialog (Ctrl+K)
Tum modullere hizli erisim icin spotlight-tarzi arama
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QHBoxLayout, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QShortcut, QKeySequence

from core.menu_structure import MENU_STRUCTURE
from core.nexor_brand import brand


class GlobalSearchDialog(QDialog):
    """Spotlight tarzi global arama dialog"""

    page_selected = Signal(str)  # menu_id

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._all_items = []
        self._build_search_index()
        self._init_ui()

    def _build_search_index(self):
        """Menu yapisindan arama index'i olustur"""
        for menu in MENU_STRUCTURE:
            parent_label = menu['label']
            icon = menu.get('icon', '')

            if not menu.get('children'):
                self._all_items.append({
                    'id': menu['id'],
                    'label': parent_label,
                    'icon': icon,
                    'parent': '',
                    'search_text': parent_label.lower(),
                })

            for child in menu.get('children', []):
                self._all_items.append({
                    'id': child['id'],
                    'label': child['label'],
                    'icon': icon,
                    'parent': parent_label,
                    'search_text': f"{parent_label} {child['label']}".lower(),
                })

    def _init_ui(self):
        t = self.theme

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(560)
        self.setMaximumHeight(480)

        # Ana container
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget#search_container {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        container.setObjectName("search_container")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_3)
        layout.setSpacing(brand.SP_2)

        # Arama input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Sayfa ara... (ornek: personel, kalite, stok)")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT};
                border: 2px solid {brand.PRIMARY};
                border-radius: {brand.R_MD}px;
                padding: {brand.SP_3}px {brand.SP_4}px;
                font-size: {brand.FS_BODY_LG}px;
            }}
        """)
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        # Ipucu
        hint = QLabel("Ctrl+K ile acin  |  Enter ile secin  |  Esc ile kapatin")
        hint.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px; padding: 0 {brand.SP_1}px;")
        layout.addWidget(hint)

        # Sonuc listesi
        self.result_list = QListWidget()
        self.result_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background: transparent;
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_3}px {brand.SP_3}px;
                margin: 1px 0;
                color: {brand.TEXT};
            }}
            QListWidget::item:selected {{
                background: {brand.BG_HOVER};
            }}
            QListWidget::item:hover {{
                background: {brand.BG_HOVER};
            }}
        """)
        self.result_list.itemActivated.connect(self._on_item_selected)
        self.result_list.itemDoubleClicked.connect(self._on_item_selected)
        layout.addWidget(self.result_list)

        # Baslangicta tum sayfalari goster
        self._on_search("")

    def _on_search(self, text: str):
        """Arama metnine gore filtrele"""
        self.result_list.clear()
        query = text.strip().lower()

        results = []
        for item in self._all_items:
            if not query or query in item['search_text']:
                score = 0
                if query:
                    if item['label'].lower().startswith(query):
                        score = 100
                    elif query in item['label'].lower():
                        score = 50
                    else:
                        score = 10
                results.append((score, item))

        results.sort(key=lambda x: (-x[0], x[1]['label']))

        for _, item in results[:20]:
            display = f"{item['icon']}  {item['label']}"
            if item['parent']:
                display += f"   ({item['parent']})"

            list_item = QListWidgetItem(display)
            list_item.setData(Qt.UserRole, item['id'])
            self.result_list.addItem(list_item)

        if self.result_list.count() > 0:
            self.result_list.setCurrentRow(0)

        # Dialog yuksekligini ayarla
        item_count = min(self.result_list.count(), 12)
        list_height = max(item_count * 38, 80)
        self.result_list.setFixedHeight(list_height)

    def _on_item_selected(self, item: QListWidgetItem):
        """Secilen sayfaya git"""
        page_id = item.data(Qt.UserRole)
        if page_id:
            self.page_selected.emit(page_id)
            self.accept()

    def keyPressEvent(self, event):
        """Klavye yonetimi"""
        key = event.key()

        if key == Qt.Key_Escape:
            self.reject()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            current = self.result_list.currentItem()
            if current:
                self._on_item_selected(current)
        elif key == Qt.Key_Down:
            row = self.result_list.currentRow()
            if row < self.result_list.count() - 1:
                self.result_list.setCurrentRow(row + 1)
        elif key == Qt.Key_Up:
            row = self.result_list.currentRow()
            if row > 0:
                self.result_list.setCurrentRow(row - 1)
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        """Dialog acildiginda input'a focus ver"""
        super().showEvent(event)
        self.search_input.setFocus()
        self.search_input.selectAll()

        # Ekranin ortasina yerlestirilsin - biraz yukarda
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + int(parent_rect.height() * 0.2)
            self.move(x, y)
