# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Etiket Tasarım v3.0
Pro-level WYSIWYG label designer with logo support
Canvas ↔ PDF coordinate mapping fixed for pixel-perfect output
"""
import json
import os
import base64
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QMessageBox, QScrollArea, QWidget,
    QSpinBox, QDoubleSpinBox, QSplitter, QGroupBox, QGridLayout,
    QListWidget, QListWidgetItem, QCheckBox, QGraphicsView,
    QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsLineItem, QGraphicsItem, QSlider, QToolButton,
    QButtonGroup, QRadioButton, QGraphicsPixmapItem, QFileDialog,
    QInputDialog, QToolBar, QSizePolicy, QGraphicsProxyWidget
)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal, QLineF, QSizeF
from PySide6.QtGui import (
    QColor, QFont, QPen, QBrush, QPainter, QCursor, QTransform,
    QPixmap, QImage, QFontMetrics, QIcon, QAction
)

from components.base_page import BasePage
from core.database import get_db_connection


# ============================================================================
# CONSTANTS - Shared conversion factor
# ============================================================================
# 1 mm = 72/25.4 points (PDF)
# We use 96 DPI for screen: 1 mm = 96/25.4 = 3.7795 px
MM_TO_PX = 96.0 / 25.4  # 3.7795275591
MM_TO_PT = 72.0 / 25.4  # 2.8346456693
PT_TO_MM = 25.4 / 72.0  # 0.3527777778

# NAS resim yolu - Ürün görselleri için (config.json'dan)
from config import NAS_PATHS
NAS_IMAGE_PATH = NAS_PATHS["image_path"]
NAS_IMAGE_EXTENSIONS = ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG', '.bmp', '.BMP']


def find_product_image(stok_kodu: str) -> str:
    """NAS üzerinden ürün görselini bul. Bulamazsa boş string döner."""
    if not stok_kodu:
        return ''
    base = os.path.join(NAS_IMAGE_PATH, stok_kodu)
    for ext in NAS_IMAGE_EXTENSIONS:
        path = base + ext
        if os.path.exists(path):
            return path
    return ''


# ============================================================================
# PROPERTIES PANEL
# ============================================================================
class PropertiesPanel(QFrame):
    """Professional properties panel with full element editing"""

    properties_changed = Signal(dict)

    def __init__(self, theme: dict, canvas=None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.canvas = canvas
        self.current_element = None
        self._block_signals = False
        self._setup_ui()

    # ── Styles ──────────────────────────────────────────────────────────
    def _group_style(self):
        return f"""
            QGroupBox {{
                color: {self.theme.get('text', '#fff')}; font-weight: bold;
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px; margin-top: 12px; padding: 12px 8px 8px 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 12px; padding: 0 6px;
            }}
        """

    def _input_style(self):
        return f"""
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background: {self.theme.get('bg_input', '#1e2330')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 4px; padding: 5px 8px;
                color: {self.theme.get('text', '#fff')};
                min-height: 24px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {self.theme.get('primary', '#6366f1')};
            }}
            QCheckBox {{ color: {self.theme.get('text', '#fff')}; spacing: 6px; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 3px;
                border: 1px solid {self.theme.get('border', '#3d4454')};
                background: {self.theme.get('bg_input', '#1e2330')};
            }}
            QCheckBox::indicator:checked {{
                background: {self.theme.get('primary', '#6366f1')};
                border-color: {self.theme.get('primary', '#6366f1')};
            }}
        """

    # ── UI Setup ────────────────────────────────────────────────────────
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{ background: {self.theme.get('bg_card', '#242938')}; border-radius: 8px; }}
            QLabel {{ color: {self.theme.get('text', '#fff')}; background: transparent; border: none; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel("⚙️ Özellikler")
        title.setStyleSheet("font-weight: bold; font-size: 14px; background: transparent;")
        layout.addWidget(title)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        self.props_layout = QVBoxLayout(scroll_widget)
        self.props_layout.setSpacing(4)
        self.props_layout.setContentsMargins(0, 0, 0, 0)

        # ── Position Group (always visible) ──
        pos_group = QGroupBox("📍 Pozisyon ve Boyut")
        pos_group.setStyleSheet(self._group_style() + self._input_style())
        pos_layout = QGridLayout(pos_group)
        pos_layout.setSpacing(6)

        for col, (label, attr, lo, hi) in enumerate([
            ("X (mm):", "x_spin", 0, 300),
            ("Y (mm):", "y_spin", 0, 200),
        ]):
            r = col
            pos_layout.addWidget(QLabel(label), r, 0)
            spin = QDoubleSpinBox()
            spin.setRange(lo, hi)
            spin.setDecimals(1)
            spin.setSingleStep(0.5)
            spin.valueChanged.connect(self._on_position_changed)
            pos_layout.addWidget(spin, r, 1)
            setattr(self, attr, spin)

        # W/H for resizable elements
        pos_layout.addWidget(QLabel("Genişlik:"), 2, 0)
        self.w_spin = QDoubleSpinBox()
        self.w_spin.setRange(1, 300)
        self.w_spin.setDecimals(1)
        self.w_spin.setSuffix(" mm")
        self.w_spin.valueChanged.connect(lambda v: self._update_prop('w_mm', v))
        pos_layout.addWidget(self.w_spin, 2, 1)

        pos_layout.addWidget(QLabel("Yükseklik:"), 3, 0)
        self.h_spin = QDoubleSpinBox()
        self.h_spin.setRange(1, 200)
        self.h_spin.setDecimals(1)
        self.h_spin.setSuffix(" mm")
        self.h_spin.valueChanged.connect(lambda v: self._update_prop('h_mm', v))
        pos_layout.addWidget(self.h_spin, 3, 1)

        self.w_label = pos_layout.itemAtPosition(2, 0).widget()
        self.h_label = pos_layout.itemAtPosition(3, 0).widget()

        self.props_layout.addWidget(pos_group)

        # Dynamic area for type-specific properties
        self.dynamic_container = QVBoxLayout()
        self.dynamic_container.setSpacing(4)
        self.props_layout.addLayout(self.dynamic_container)

        self.props_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        # Empty state
        self.empty_label = QLabel("Bir element seçin\nveya yeni ekleyin")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(f"color: {self.theme.get('text_secondary', '#9ca3af')}; font-size: 13px;")
        layout.addWidget(self.empty_label)

        self._show_empty()

    def _show_empty(self):
        self.empty_label.show()

    def _hide_empty(self):
        self.empty_label.hide()

    # ── Load element properties ────────────────────────────────────────
    def load_element(self, element: dict):
        if not element or not element.get('type'):
            self.clear()
            return

        self._block_signals = True
        self.current_element = element
        self._hide_empty()

        # Position
        self.x_spin.setValue(element.get('x_mm', 0))
        self.y_spin.setValue(element.get('y_mm', 0))

        # Show/hide W/H based on type
        has_size = element['type'] in ('BARCODE', 'RECT', 'IMAGE', 'PRODUCT_IMAGE')
        for w in (self.w_spin, self.h_spin, self.w_label, self.h_label):
            w.setVisible(has_size)
        if has_size:
            self.w_spin.setValue(element.get('w_mm', 30))
            self.h_spin.setValue(element.get('h_mm', 15))

        # Clear dynamic widgets
        while self.dynamic_container.count():
            item = self.dynamic_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Type-specific properties
        builders = {
            'TEXT': self._build_text_props,
            'FIELD': self._build_field_props,
            'BARCODE': self._build_barcode_props,
            'LINE': self._build_line_props,
            'RECT': self._build_rect_props,
            'IMAGE': self._build_image_props,
            'PRODUCT_IMAGE': self._build_product_image_props,
        }
        builder = builders.get(element['type'])
        if builder:
            builder(element)

        self._block_signals = False

    def _make_group(self, title: str) -> tuple:
        group = QGroupBox(title)
        group.setStyleSheet(self._group_style() + self._input_style())
        lay = QGridLayout(group)
        lay.setSpacing(6)
        self.dynamic_container.addWidget(group)
        return group, lay

    # ── Text properties ────────────────────────────────────────────────
    def _build_text_props(self, elem):
        grp, lay = self._make_group("📝 Metin")

        lay.addWidget(QLabel("Metin:"), 0, 0)
        inp = QLineEdit(elem.get('text', ''))
        inp.textChanged.connect(lambda t: self._update_prop('text', t))
        lay.addWidget(inp, 0, 1, 1, 3)

        self._add_font_controls(lay, elem, start_row=1)

    def _build_field_props(self, elem):
        grp, lay = self._make_group("📊 Veri Alanı")

        lay.addWidget(QLabel("Alan:"), 0, 0)
        combo = QComboBox()
        fields = [
            "lot_no - Lot Numarası",
            "stok_kodu - Stok Kodu",
            "stok_adi - Stok Adı",
            "musteri - Müşteri",
            "kaplama - Kaplama Tipi",
            "miktar - Miktar",
            "birim - Birim",
            "palet_no - Palet No",
            "toplam_palet - Toplam Palet",
            "irsaliye_no - İrsaliye No",
            "tarih - Tarih",
            "siparis_no - Sipariş No",
            "is_emri_no - İş Emri No",
            "kontrolcu - Kontrol Eden",
            "kontrol_tarihi - Kontrol Tarihi",
            "saglam_adet - Sağlam Adet",
            "hatali_adet - Hatalı Adet",
            "sonuc - Sonuç",
        ]
        combo.addItems(fields)
        cur = elem.get('field', 'lot_no')
        for i in range(combo.count()):
            if combo.itemText(i).startswith(cur):
                combo.setCurrentIndex(i)
                break
        combo.currentTextChanged.connect(lambda t: self._update_prop('field', t.split(' - ')[0]))
        lay.addWidget(combo, 0, 1, 1, 3)

        self._add_font_controls(lay, elem, start_row=1)

    def _add_font_controls(self, lay, elem, start_row=1):
        """Shared font size + bold controls for text/field"""
        lay.addWidget(QLabel("Boyut:"), start_row, 0)
        size_spin = QSpinBox()
        size_spin.setRange(6, 72)
        size_spin.setValue(elem.get('size', 10))
        size_spin.valueChanged.connect(lambda v: self._update_prop('size', v))
        lay.addWidget(size_spin, start_row, 1)

        bold = QCheckBox("Kalın")
        bold.setChecked(elem.get('bold', False))
        bold.toggled.connect(lambda c: self._update_prop('bold', c))
        lay.addWidget(bold, start_row, 2)

        italic = QCheckBox("İtalik")
        italic.setChecked(elem.get('italic', False))
        italic.toggled.connect(lambda c: self._update_prop('italic', c))
        lay.addWidget(italic, start_row, 3)

        # Alignment
        lay.addWidget(QLabel("Hizalama:"), start_row + 1, 0)
        align_combo = QComboBox()
        align_combo.addItems(["Sol", "Orta", "Sağ"])
        align_map = {'left': 'Sol', 'center': 'Orta', 'right': 'Sağ'}
        align_combo.setCurrentText(align_map.get(elem.get('align', 'left'), 'Sol'))
        align_combo.currentTextChanged.connect(
            lambda t: self._update_prop('align', {'Sol': 'left', 'Orta': 'center', 'Sağ': 'right'}.get(t, 'left'))
        )
        lay.addWidget(align_combo, start_row + 1, 1, 1, 3)

    def _build_barcode_props(self, elem):
        grp, lay = self._make_group("▪️ Barkod")

        lay.addWidget(QLabel("Veri:"), 0, 0)
        combo = QComboBox()
        combo.addItems([
            "lot_no - Lot Numarası", "stok_kodu - Stok Kodu",
            "palet_no - Palet No", "irsaliye_no - İrsaliye No",
            "siparis_no - Sipariş No"
        ])
        cur = elem.get('field', 'lot_no')
        for i in range(combo.count()):
            if combo.itemText(i).startswith(cur):
                combo.setCurrentIndex(i)
                break
        combo.currentTextChanged.connect(lambda t: self._update_prop('field', t.split(' - ')[0]))
        lay.addWidget(combo, 0, 1, 1, 3)

        # Show text under barcode
        show_text = QCheckBox("Altında metin göster")
        show_text.setChecked(elem.get('show_text', True))
        show_text.toggled.connect(lambda c: self._update_prop('show_text', c))
        lay.addWidget(show_text, 1, 0, 1, 4)

    def _build_line_props(self, elem):
        grp, lay = self._make_group("➖ Çizgi")

        lay.addWidget(QLabel("Uzunluk:"), 0, 0)
        s = QDoubleSpinBox()
        s.setRange(1, 300)
        s.setSuffix(" mm")
        s.setValue(elem.get('length', 50))
        s.valueChanged.connect(lambda v: self._update_prop('length', v))
        lay.addWidget(s, 0, 1)

        lay.addWidget(QLabel("Kalınlık:"), 0, 2)
        w = QDoubleSpinBox()
        w.setRange(0.1, 5)
        w.setDecimals(1)
        w.setSingleStep(0.1)
        w.setSuffix(" pt")
        w.setValue(elem.get('width', 0.5))
        w.valueChanged.connect(lambda v: self._update_prop('width', v))
        lay.addWidget(w, 0, 3)

        lay.addWidget(QLabel("Yön:"), 1, 0)
        d = QComboBox()
        d.addItems(["Yatay", "Dikey"])
        d.setCurrentText(elem.get('direction', 'Yatay'))
        d.currentTextChanged.connect(lambda t: self._update_prop('direction', t))
        lay.addWidget(d, 1, 1)

        # Dash style
        lay.addWidget(QLabel("Stil:"), 1, 2)
        st = QComboBox()
        st.addItems(["Düz", "Kesikli", "Noktalı"])
        style_map = {'solid': 'Düz', 'dashed': 'Kesikli', 'dotted': 'Noktalı'}
        st.setCurrentText(style_map.get(elem.get('line_style', 'solid'), 'Düz'))
        st.currentTextChanged.connect(lambda t: self._update_prop(
            'line_style', {'Düz': 'solid', 'Kesikli': 'dashed', 'Noktalı': 'dotted'}.get(t, 'solid')
        ))
        lay.addWidget(st, 1, 3)

    def _build_rect_props(self, elem):
        grp, lay = self._make_group("▭ Dikdörtgen")

        lay.addWidget(QLabel("Kenarlık:"), 0, 0)
        b = QDoubleSpinBox()
        b.setRange(0, 5)
        b.setDecimals(1)
        b.setSuffix(" pt")
        b.setValue(elem.get('border_width', 0.5))
        b.valueChanged.connect(lambda v: self._update_prop('border_width', v))
        lay.addWidget(b, 0, 1)

        fill = QCheckBox("Dolgulu")
        fill.setChecked(elem.get('fill', False))
        fill.toggled.connect(lambda c: self._update_prop('fill', c))
        lay.addWidget(fill, 0, 2)

        corner = QCheckBox("Yuvarlatılmış Köşe")
        corner.setChecked(elem.get('rounded', False))
        corner.toggled.connect(lambda c: self._update_prop('rounded', c))
        lay.addWidget(corner, 0, 3)

    def _build_image_props(self, elem):
        grp, lay = self._make_group("🖼️ Logo / Resim")

        lay.addWidget(QLabel("Dosya:"), 0, 0)
        path_label = QLabel(os.path.basename(elem.get('image_path', '')) or "(Seçilmedi)")
        path_label.setStyleSheet(f"color: {self.theme.get('text_secondary', '#9ca3af')}; font-size: 11px;")
        lay.addWidget(path_label, 0, 1, 1, 2)

        btn = QPushButton("📂 Değiştir")
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#6366f1')};
                color: white; border: none; border-radius: 4px; padding: 5px 10px;
            }}
            QPushButton:hover {{ background: #818cf8; }}
        """)
        btn.clicked.connect(lambda: self._change_image(elem, path_label))
        lay.addWidget(btn, 0, 3)

        # Keep aspect ratio
        aspect = QCheckBox("Oranı Koru")
        aspect.setChecked(elem.get('keep_aspect', True))
        aspect.toggled.connect(lambda c: self._update_prop('keep_aspect', c))
        lay.addWidget(aspect, 1, 0, 1, 2)

        # Opacity
        lay.addWidget(QLabel("Opaklık:"), 1, 2)
        op = QSpinBox()
        op.setRange(10, 100)
        op.setSuffix("%")
        op.setValue(elem.get('opacity', 100))
        op.valueChanged.connect(lambda v: self._update_prop('opacity', v))
        lay.addWidget(op, 1, 3)

    def _change_image(self, elem, path_label):
        path, _ = QFileDialog.getOpenFileName(
            self, "Logo / Resim Seç", "",
            "Resimler (*.png *.jpg *.jpeg *.bmp *.svg);;Tüm Dosyalar (*)"
        )
        if path:
            elem['image_path'] = path
            # Store base64 for portability
            try:
                with open(path, 'rb') as f:
                    elem['image_data'] = base64.b64encode(f.read()).decode('utf-8')
                elem['image_ext'] = os.path.splitext(path)[1].lower()
            except Exception as e:
                print(f"Image read error: {e}")
            path_label.setText(os.path.basename(path))
            self.properties_changed.emit({'image_path': path})

    def _build_product_image_props(self, elem):
        """Ürün görseli özellikleri - NAS'tan stok koduna göre otomatik çekilir"""
        grp, lay = self._make_group("📸 Ürün Görseli")

        lay.addWidget(QLabel("Kaynak:"), 0, 0)
        src_label = QLabel(f"NAS: {NAS_IMAGE_PATH}")
        src_label.setStyleSheet(f"color: {self.theme.get('text_secondary', '#9ca3af')}; font-size: 10px;")
        src_label.setWordWrap(True)
        lay.addWidget(src_label, 0, 1, 1, 3)

        # Info label
        info = QLabel("ℹ️ Yazdırırken stok koduna göre\notomatik olarak NAS'tan çekilir")
        info.setStyleSheet(f"color: {self.theme.get('text_secondary', '#9ca3af')}; font-size: 11px;")
        info.setWordWrap(True)
        lay.addWidget(info, 1, 0, 1, 4)

        # Test with specific stok_kodu
        lay.addWidget(QLabel("Test Kodu:"), 2, 0)
        test_input = QLineEdit(elem.get('test_stok_kodu', ''))
        test_input.setPlaceholderText("Stok kodu girin...")
        test_input.textChanged.connect(lambda t: self._update_prop('test_stok_kodu', t))
        lay.addWidget(test_input, 2, 1, 1, 2)

        test_btn = QPushButton("🔍")
        test_btn.setFixedWidth(36)
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#6366f1')};
                color: white; border: none; border-radius: 4px; padding: 5px;
            }}
            QPushButton:hover {{ background: #818cf8; }}
        """)
        test_btn.clicked.connect(lambda: self._test_product_image(elem, test_input.text()))
        lay.addWidget(test_btn, 2, 3)

        # Keep aspect ratio
        aspect = QCheckBox("Oranı Koru")
        aspect.setChecked(elem.get('keep_aspect', True))
        aspect.toggled.connect(lambda c: self._update_prop('keep_aspect', c))
        lay.addWidget(aspect, 3, 0, 1, 2)

        # Border
        border = QCheckBox("Kenarlık")
        border.setChecked(elem.get('show_border', False))
        border.toggled.connect(lambda c: self._update_prop('show_border', c))
        lay.addWidget(border, 3, 2, 1, 2)

    def _test_product_image(self, elem, stok_kodu):
        """Test: belirtilen stok kodunun görselini NAS'tan bul ve canvas'ta göster"""
        if not stok_kodu:
            QMessageBox.warning(self, "Uyarı", "Test için bir stok kodu girin!")
            return
        img_path = find_product_image(stok_kodu)
        if img_path:
            elem['image_path'] = img_path
            elem['test_stok_kodu'] = stok_kodu
            self.properties_changed.emit({'image_path': img_path})
            QMessageBox.information(self, "Bulundu", f"✓ Görsel bulundu:\n{img_path}")
        else:
            QMessageBox.warning(self, "Bulunamadı",
                                f"'{stok_kodu}' için görsel bulunamadı.\n\n"
                                f"Aranan konum:\n{NAS_IMAGE_PATH}\\{stok_kodu}.[jpg/png/...]")

    # ── Property update helpers ────────────────────────────────────────
    def _update_prop(self, key, value):
        if self._block_signals or not self.current_element:
            return
        self.current_element[key] = value
        if self.canvas and self.canvas.selected_element:
            self.canvas.selected_element[key] = value
        self.properties_changed.emit({key: value})

    def _on_position_changed(self):
        if self._block_signals or not self.current_element:
            return
        x_mm = self.x_spin.value()
        y_mm = self.y_spin.value()
        self.current_element['x_mm'] = x_mm
        self.current_element['y_mm'] = y_mm
        if self.canvas and self.canvas.selected_element:
            self.canvas.selected_element['x_mm'] = x_mm
            self.canvas.selected_element['y_mm'] = y_mm
        self.properties_changed.emit({'x_mm': x_mm, 'y_mm': y_mm})

    def update_position_display(self, element):
        """Update position spinboxes from element (after drag)"""
        self._block_signals = True
        self.x_spin.setValue(element.get('x_mm', 0))
        self.y_spin.setValue(element.get('y_mm', 0))
        self._block_signals = False

    def clear(self):
        self.current_element = None
        self._show_empty()
        while self.dynamic_container.count():
            item = self.dynamic_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ============================================================================
# DESIGN CANVAS - WYSIWYG with precise mm-based positioning
# ============================================================================
class DesignCanvas(QGraphicsView):
    """WYSIWYG label design canvas with accurate mm positioning"""

    element_selected = Signal(dict)
    element_moved = Signal(dict)

    def __init__(self, width_mm=100, height_mm=50, theme=None, parent=None):
        super().__init__(parent)
        self.theme = theme or {}
        self.width_mm = width_mm
        self.height_mm = height_mm

        self.elements = []
        self.selected_element = None
        self._drag_start = None

        self._setup_scene()
        self._setup_view()

    def _setup_scene(self):
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        w_px = self.width_mm * MM_TO_PX
        h_px = self.height_mm * MM_TO_PX

        # White background
        self.scene.addRect(0, 0, w_px, h_px, QPen(Qt.NoPen), QBrush(QColor('#FFFFFF')))

        # Border
        border_pen = QPen(QColor('#94a3b8'), 1.5)
        self.border_rect = self.scene.addRect(0, 0, w_px, h_px, border_pen, QBrush(Qt.NoBrush))

        # Grid - 5mm spacing, lighter
        grid_pen = QPen(QColor('#e2e8f0'), 0.5, Qt.DotLine)
        for x in range(5, int(self.width_mm), 5):
            xp = x * MM_TO_PX
            self.scene.addLine(xp, 0, xp, h_px, grid_pen)
        for y in range(5, int(self.height_mm), 5):
            yp = y * MM_TO_PX
            self.scene.addLine(0, yp, w_px, yp, grid_pen)

        # 10mm grid - slightly visible
        grid_pen2 = QPen(QColor('#cbd5e1'), 0.5, Qt.DashDotLine)
        for x in range(10, int(self.width_mm), 10):
            xp = x * MM_TO_PX
            self.scene.addLine(xp, 0, xp, h_px, grid_pen2)
        for y in range(10, int(self.height_mm), 10):
            yp = y * MM_TO_PX
            self.scene.addLine(0, yp, w_px, yp, grid_pen2)

    def _setup_view(self):
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        bg_color = self.theme.get('bg_secondary', '#1a1f2e')
        self.setStyleSheet(f"QGraphicsView {{ background: {bg_color}; border: none; border-radius: 6px; }}")

        QTimer.singleShot(50, self._fit_view)

    def _fit_view(self):
        margin = 20
        rect = QRectF(-margin, -margin,
                       self.width_mm * MM_TO_PX + 2 * margin,
                       self.height_mm * MM_TO_PX + 2 * margin)
        self.fitInView(rect, Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_view()

    # ── Element Add ────────────────────────────────────────────────────
    def add_element(self, elem_type: str, x_mm=None, y_mm=None, **kwargs):
        if x_mm is None:
            x_mm = 5.0
        if y_mm is None:
            y_mm = 5.0 + len(self.elements) * 8

        element = {
            'type': elem_type,
            'x_mm': x_mm,
            'y_mm': y_mm,
            'id': f"{elem_type}_{len(self.elements)}_{id(self)}",
        }

        defaults = {
            'TEXT': {'text': 'Metin', 'size': 10, 'bold': False, 'italic': False, 'align': 'left'},
            'FIELD': {'field': 'lot_no', 'size': 10, 'bold': False, 'italic': False, 'align': 'left'},
            'BARCODE': {'field': 'lot_no', 'w_mm': 50, 'h_mm': 10, 'show_text': True},
            'LINE': {'length': 50, 'width': 0.5, 'direction': 'Yatay', 'line_style': 'solid'},
            'RECT': {'w_mm': 30, 'h_mm': 15, 'border_width': 0.5, 'fill': False, 'rounded': False},
            'IMAGE': {'w_mm': 25, 'h_mm': 20, 'image_path': '', 'image_data': '', 'image_ext': '',
                      'keep_aspect': True, 'opacity': 100},
            'PRODUCT_IMAGE': {'w_mm': 60, 'h_mm': 50, 'keep_aspect': True, 'show_border': False,
                              'test_stok_kodu': '', 'image_path': ''},
        }
        element.update(defaults.get(elem_type, {}))
        element.update(kwargs)

        self.elements.append(element)
        self._draw_element(element)
        self.select_element(element)
        return element

    # ── Drawing ────────────────────────────────────────────────────────
    def _draw_element(self, elem):
        drawers = {
            'TEXT': self._draw_text,
            'FIELD': self._draw_field,
            'BARCODE': self._draw_barcode,
            'LINE': self._draw_line,
            'RECT': self._draw_rect,
            'IMAGE': self._draw_image,
            'PRODUCT_IMAGE': self._draw_product_image,
        }
        drawer = drawers.get(elem['type'])
        if drawer:
            drawer(elem)

    def _make_font(self, elem):
        """Create QFont matching PDF output"""
        # Use DejaVu Sans for Turkish character support (same as PDF)
        font = QFont("DejaVu Sans", elem.get('size', 10))
        font.setBold(elem.get('bold', False))
        font.setItalic(elem.get('italic', False))
        return font

    def _make_movable(self, item):
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setCursor(Qt.OpenHandCursor)

    def _draw_text(self, elem):
        x = elem['x_mm'] * MM_TO_PX
        y = elem['y_mm'] * MM_TO_PX
        font = self._make_font(elem)
        item = self.scene.addText(elem.get('text', 'Metin'), font)
        item.setDefaultTextColor(QColor('#000000'))
        item.setPos(x, y)
        # Remove internal margin of QGraphicsTextItem
        doc = item.document()
        doc.setDocumentMargin(0)
        self._make_movable(item)
        elem['item'] = item

    def _draw_field(self, elem):
        x = elem['x_mm'] * MM_TO_PX
        y = elem['y_mm'] * MM_TO_PX
        font = self._make_font(elem)
        field_name = elem.get('field', 'lot_no')
        item = self.scene.addText(f"{{{field_name}}}", font)
        item.setDefaultTextColor(QColor('#2563eb'))
        item.setPos(x, y)
        doc = item.document()
        doc.setDocumentMargin(0)
        self._make_movable(item)
        elem['item'] = item

    def _draw_barcode(self, elem):
        x = elem['x_mm'] * MM_TO_PX
        y = elem['y_mm'] * MM_TO_PX
        w = elem.get('w_mm', 50) * MM_TO_PX
        h = elem.get('h_mm', 10) * MM_TO_PX

        # Container rect
        pen = QPen(QColor('#1e293b'), 1)
        brush = QBrush(QColor('#f8fafc'))
        rect_item = self.scene.addRect(0, 0, w, h, pen, brush)
        rect_item.setPos(x, y)
        self._make_movable(rect_item)

        # Draw barcode lines simulation
        bar_count = int(w / 3)
        import random
        for i in range(bar_count):
            bx = 4 + i * 3
            if bx > w - 4:
                break
            bw = random.choice([1, 1.5, 2])
            bh_actual = h * 0.7
            bar = self.scene.addRect(0, 0, bw, bh_actual, QPen(Qt.NoPen), QBrush(QColor('#1e293b')))
            bar.setPos(bx, 2)
            bar.setParentItem(rect_item)

        # Label
        font = QFont("DejaVu Sans", 6)
        text = self.scene.addText(f"{elem.get('field', 'lot_no')}", font)
        text.setDefaultTextColor(QColor('#475569'))
        text.setPos(4, h * 0.72)
        text.setParentItem(rect_item)

        elem['item'] = rect_item

    def _draw_line(self, elem):
        x = elem['x_mm'] * MM_TO_PX
        y = elem['y_mm'] * MM_TO_PX
        length = elem.get('length', 50) * MM_TO_PX
        width = elem.get('width', 0.5)
        direction = elem.get('direction', 'Yatay')
        style = elem.get('line_style', 'solid')

        pen = QPen(QColor('#000'), width)
        if style == 'dashed':
            pen.setStyle(Qt.DashLine)
        elif style == 'dotted':
            pen.setStyle(Qt.DotLine)

        if direction == 'Yatay':
            item = self.scene.addLine(0, 0, length, 0, pen)
        else:
            item = self.scene.addLine(0, 0, 0, length, pen)

        item.setPos(x, y)
        self._make_movable(item)
        elem['item'] = item

    def _draw_rect(self, elem):
        x = elem['x_mm'] * MM_TO_PX
        y = elem['y_mm'] * MM_TO_PX
        w = elem.get('w_mm', 30) * MM_TO_PX
        h = elem.get('h_mm', 15) * MM_TO_PX
        border = elem.get('border_width', 0.5)
        fill = elem.get('fill', False)

        pen = QPen(QColor('#000'), border)
        brush = QBrush(QColor('#f1f5f9') if fill else Qt.NoBrush)

        if elem.get('rounded', False):
            item = self.scene.addRect(0, 0, w, h, pen, brush)
            # Note: QGraphicsRectItem doesn't support rounded natively in addRect
            # We'll handle rounded in PDF output
        else:
            item = self.scene.addRect(0, 0, w, h, pen, brush)

        item.setPos(x, y)
        self._make_movable(item)
        elem['item'] = item

    def _draw_image(self, elem):
        x = elem['x_mm'] * MM_TO_PX
        y = elem['y_mm'] * MM_TO_PX
        w = elem.get('w_mm', 25) * MM_TO_PX
        h = elem.get('h_mm', 20) * MM_TO_PX

        pixmap = None
        # Try loading from file path first
        if elem.get('image_path') and os.path.exists(elem['image_path']):
            pixmap = QPixmap(elem['image_path'])
        # Try from base64
        elif elem.get('image_data'):
            try:
                img_bytes = base64.b64decode(elem['image_data'])
                img = QImage()
                img.loadFromData(img_bytes)
                pixmap = QPixmap.fromImage(img)
            except Exception:
                pass

        if pixmap and not pixmap.isNull():
            if elem.get('keep_aspect', True):
                pixmap = pixmap.scaled(int(w), int(h), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                pixmap = pixmap.scaled(int(w), int(h), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            item = self.scene.addPixmap(pixmap)
            item.setPos(x, y)
            opacity = elem.get('opacity', 100) / 100.0
            item.setOpacity(opacity)
        else:
            # Placeholder
            pen = QPen(QColor('#94a3b8'), 1, Qt.DashLine)
            brush = QBrush(QColor('#f1f5f9'))
            item = self.scene.addRect(0, 0, w, h, pen, brush)
            item.setPos(x, y)
            # Icon
            font = QFont("DejaVu Sans", 9)
            text = self.scene.addText("🖼️ Logo", font)
            text.setDefaultTextColor(QColor('#94a3b8'))
            text.setPos(w / 2 - 20, h / 2 - 8)
            text.setParentItem(item)

        self._make_movable(item)
        elem['item'] = item

    def _draw_product_image(self, elem):
        """Draw product image - from NAS path or test stok kodu"""
        x = elem['x_mm'] * MM_TO_PX
        y = elem['y_mm'] * MM_TO_PX
        w = elem.get('w_mm', 60) * MM_TO_PX
        h = elem.get('h_mm', 50) * MM_TO_PX

        pixmap = None

        # Try loading from resolved image_path (set by test or real data)
        if elem.get('image_path') and os.path.exists(elem['image_path']):
            pixmap = QPixmap(elem['image_path'])

        # Try finding by test stok kodu
        if (not pixmap or pixmap.isNull()) and elem.get('test_stok_kodu'):
            img_path = find_product_image(elem['test_stok_kodu'])
            if img_path:
                pixmap = QPixmap(img_path)
                elem['image_path'] = img_path

        if pixmap and not pixmap.isNull():
            if elem.get('keep_aspect', True):
                pixmap = pixmap.scaled(int(w), int(h), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                pixmap = pixmap.scaled(int(w), int(h), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            item = self.scene.addPixmap(pixmap)
            item.setPos(x, y)

            # Optional border
            if elem.get('show_border', False):
                border = self.scene.addRect(0, 0, pixmap.width(), pixmap.height(),
                                            QPen(QColor('#64748b'), 1), QBrush(Qt.NoBrush))
                border.setParentItem(item)
        else:
            # Placeholder with product icon
            pen = QPen(QColor('#0ea5e9'), 1.5, Qt.DashLine)
            brush = QBrush(QColor('#f0f9ff'))
            item = self.scene.addRect(0, 0, w, h, pen, brush)
            item.setPos(x, y)

            font = QFont("DejaVu Sans", 8)
            text = self.scene.addText("📸 Ürün Görseli\n{stok_kodu}", font)
            text.setDefaultTextColor(QColor('#0369a1'))
            doc = text.document()
            doc.setDocumentMargin(0)
            text.setPos(4, h / 2 - 14)
            text.setParentItem(item)

        self._make_movable(item)
        elem['item'] = item

    # ── Redraw ─────────────────────────────────────────────────────────
    def redraw_element(self, element):
        if not element:
            return
        old_item = element.get('item')
        if old_item:
            try:
                if old_item.scene() == self.scene:
                    self.scene.removeItem(old_item)
            except (RuntimeError, AttributeError):
                pass

        self._draw_element(element)

        if self.selected_element == element and element.get('item'):
            try:
                element['item'].setSelected(True)
            except (RuntimeError, AttributeError):
                pass

    def select_element(self, element):
        if self.selected_element and self.selected_element.get('item'):
            try:
                self.selected_element['item'].setSelected(False)
            except (RuntimeError, AttributeError):
                pass

        self.selected_element = element
        if element and element.get('item'):
            try:
                element['item'].setSelected(True)
            except (RuntimeError, AttributeError):
                pass

        self.element_selected.emit(element if element else {})

    def delete_selected(self):
        if not self.selected_element:
            return
        item = self.selected_element.get('item')
        if item:
            try:
                self.scene.removeItem(item)
            except (RuntimeError, AttributeError):
                pass
        if self.selected_element in self.elements:
            self.elements.remove(self.selected_element)
        self.selected_element = None
        self.element_selected.emit({})

    def clear_all(self):
        for elem in self.elements[:]:
            item = elem.get('item')
            if item:
                try:
                    if item.scene() == self.scene:
                        self.scene.removeItem(item)
                except (RuntimeError, AttributeError):
                    pass
        self.elements.clear()
        self.selected_element = None

    def duplicate_selected(self):
        """Duplicate selected element with offset"""
        if not self.selected_element:
            return
        elem = self.selected_element
        new_elem = dict(elem)
        new_elem.pop('item', None)
        new_elem['x_mm'] = elem.get('x_mm', 0) + 3
        new_elem['y_mm'] = elem.get('y_mm', 0) + 3
        new_elem['id'] = f"{elem['type']}_{len(self.elements)}_{id(self)}"
        self.elements.append(new_elem)
        self._draw_element(new_elem)
        self.select_element(new_elem)

    # ── Mouse events ───────────────────────────────────────────────────
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        pos = self.mapToScene(event.pos())
        items = self.scene.items(pos)

        for item in items:
            if item == self.border_rect:
                continue
            # Check if movable
            if item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable:
                for elem in self.elements:
                    if elem.get('item') == item:
                        self.select_element(elem)
                        return
                    # Check parent items (for barcode etc)
                    parent = item.parentItem()
                    if parent and elem.get('item') == parent:
                        self.select_element(elem)
                        return

        # Clicked on empty space
        self.select_element(None)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.selected_element and self.selected_element.get('item'):
            item = self.selected_element['item']
            try:
                pos = item.pos()
                self.selected_element['x_mm'] = round(pos.x() / MM_TO_PX, 1)
                self.selected_element['y_mm'] = round(pos.y() / MM_TO_PX, 1)
                self.element_moved.emit(self.selected_element)
            except (RuntimeError, AttributeError):
                pass

    def wheelEvent(self, event):
        """Zoom with mouse wheel"""
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)

    # ── JSON Export/Import ─────────────────────────────────────────────
    def export_to_json(self) -> str:
        export_elements = []
        for elem in self.elements:
            item = elem.get('item')
            if item:
                try:
                    pos = item.pos()
                    x_mm = round(pos.x() / MM_TO_PX, 1)
                    y_mm = round(pos.y() / MM_TO_PX, 1)
                except (RuntimeError, AttributeError):
                    x_mm = elem.get('x_mm', 0)
                    y_mm = elem.get('y_mm', 0)
            else:
                x_mm = elem.get('x_mm', 0)
                y_mm = elem.get('y_mm', 0)

            e = {'type': elem['type'], 'x': x_mm, 'y': y_mm}

            if elem['type'] == 'TEXT':
                e.update({'text': elem.get('text', ''), 'size': elem.get('size', 10),
                          'bold': elem.get('bold', False), 'italic': elem.get('italic', False),
                          'align': elem.get('align', 'left')})
            elif elem['type'] == 'FIELD':
                e.update({'field': elem.get('field', 'lot_no'), 'size': elem.get('size', 10),
                          'bold': elem.get('bold', False), 'italic': elem.get('italic', False),
                          'align': elem.get('align', 'left')})
            elif elem['type'] == 'BARCODE':
                e.update({'field': elem.get('field', 'lot_no'),
                          'width': elem.get('w_mm', 50), 'height': elem.get('h_mm', 10),
                          'show_text': elem.get('show_text', True)})
            elif elem['type'] == 'LINE':
                e.update({'length': elem.get('length', 50), 'width': elem.get('width', 0.5),
                          'direction': elem.get('direction', 'Yatay'),
                          'line_style': elem.get('line_style', 'solid')})
            elif elem['type'] == 'RECT':
                e.update({'width': elem.get('w_mm', 30), 'height': elem.get('h_mm', 15),
                          'border_width': elem.get('border_width', 0.5),
                          'fill': elem.get('fill', False), 'rounded': elem.get('rounded', False)})
            elif elem['type'] == 'IMAGE':
                e.update({'width': elem.get('w_mm', 25), 'height': elem.get('h_mm', 20),
                          'image_data': elem.get('image_data', ''),
                          'image_ext': elem.get('image_ext', ''),
                          'keep_aspect': elem.get('keep_aspect', True),
                          'opacity': elem.get('opacity', 100)})
            elif elem['type'] == 'PRODUCT_IMAGE':
                e.update({'width': elem.get('w_mm', 60), 'height': elem.get('h_mm', 50),
                          'keep_aspect': elem.get('keep_aspect', True),
                          'show_border': elem.get('show_border', False),
                          'test_stok_kodu': elem.get('test_stok_kodu', '')})

            export_elements.append(e)

        return json.dumps({
            'version': '3.0',
            'background': '#FFFFFF',
            'elements': export_elements
        }, indent=2, ensure_ascii=False)

    def load_from_json(self, json_str: str):
        try:
            self.clear_all()
            data = json.loads(json_str)

            for ed in data.get('elements', []):
                et = ed.get('type')
                x = ed.get('x', 5)
                y = ed.get('y', 5)

                kwargs = {}
                if et == 'TEXT':
                    kwargs = {k: ed[k] for k in ('text', 'size', 'bold', 'italic', 'align') if k in ed}
                elif et == 'FIELD':
                    kwargs = {k: ed[k] for k in ('field', 'size', 'bold', 'italic', 'align') if k in ed}
                elif et == 'BARCODE':
                    kwargs = {'field': ed.get('field', 'lot_no'),
                              'w_mm': ed.get('width', 50), 'h_mm': ed.get('height', 10),
                              'show_text': ed.get('show_text', True)}
                elif et == 'LINE':
                    kwargs = {k: ed[k] for k in ('length', 'width', 'direction', 'line_style') if k in ed}
                elif et == 'RECT':
                    kwargs = {'w_mm': ed.get('width', 30), 'h_mm': ed.get('height', 15),
                              'border_width': ed.get('border_width', 0.5),
                              'fill': ed.get('fill', False), 'rounded': ed.get('rounded', False)}
                elif et == 'IMAGE':
                    kwargs = {'w_mm': ed.get('width', 25), 'h_mm': ed.get('height', 20),
                              'image_data': ed.get('image_data', ''),
                              'image_ext': ed.get('image_ext', ''),
                              'keep_aspect': ed.get('keep_aspect', True),
                              'opacity': ed.get('opacity', 100)}
                elif et == 'PRODUCT_IMAGE':
                    kwargs = {'w_mm': ed.get('width', 60), 'h_mm': ed.get('height', 50),
                              'keep_aspect': ed.get('keep_aspect', True),
                              'show_border': ed.get('show_border', False),
                              'test_stok_kodu': ed.get('test_stok_kodu', '')}

                self.add_element(et, x, y, **kwargs)

        except Exception as e:
            print(f"JSON load error: {e}")
            import traceback
            traceback.print_exc()


# ============================================================================
# PDF RENDERER - Pixel-perfect output matching canvas
# ============================================================================
class PDFRenderer:
    """Renders label elements to PDF with exact coordinate mapping"""

    # Class-level cache to avoid re-registering fonts
    _fonts_registered = False
    _available_fonts = {}  # maps logical name -> registered PDF font name

    @staticmethod
    def _register_fonts():
        """Register Unicode fonts for Turkish character support (İ, Ş, Ğ, Ü, Ö, Ç)"""
        if PDFRenderer._fonts_registered:
            return bool(PDFRenderer._available_fonts)

        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # Find utils/ttf directory - try multiple paths
        this_file = os.path.abspath(__file__)
        font_path = None

        # Strategy 1: Walk up from this file until we find utils/ttf
        check_dir = os.path.dirname(this_file)
        for _ in range(6):  # max 6 levels up
            candidate = os.path.join(check_dir, 'utils', 'ttf')
            if os.path.isdir(candidate):
                font_path = candidate
                break
            check_dir = os.path.dirname(check_dir)

        # Strategy 2: Check common known paths
        if not font_path:
            known_paths = [
                r'D:\PROJELER\ALL\NEXOR_CORE_DATA\utils\ttf',
                os.path.join(os.path.dirname(this_file), '..', '..', 'utils', 'ttf'),
                os.path.join(os.path.dirname(this_file), '..', 'utils', 'ttf'),
            ]
            for kp in known_paths:
                kp = os.path.normpath(kp)
                if os.path.isdir(kp):
                    font_path = kp
                    break

        if not font_path:
            print(f"⚠ Font dizini bulunamadı! Aranan: utils/ttf (başlangıç: {os.path.dirname(this_file)})")
            PDFRenderer._fonts_registered = True
            return False

        print(f"  Font dizini: {font_path}")

        # Map: logical name -> list of possible filenames (in priority order)
        font_candidates = {
            'regular': [
                'DejaVuSans.ttf',
            ],
            'bold': [
                'DejaVuSans-Bold.ttf',
            ],
            'italic': [
                'DejaVuSans-Oblique.ttf',
                'DejaVuSans-BoldOblique.ttf',  # fallback: use bold-oblique for italic
            ],
            'bolditalic': [
                'DejaVuSans-BoldOblique.ttf',
                'DejaVuSans-Bold.ttf',  # fallback: just bold
            ],
        }

        # Register name mapping
        register_names = {
            'regular': 'NexorFont',
            'bold': 'NexorFont-Bold',
            'italic': 'NexorFont-Italic',
            'bolditalic': 'NexorFont-BoldItalic',
        }

        PDFRenderer._available_fonts = {}

        for logical, candidates in font_candidates.items():
            registered = False
            for filename in candidates:
                fpath = os.path.join(font_path, filename)
                if os.path.exists(fpath):
                    try:
                        reg_name = register_names[logical]
                        pdfmetrics.registerFont(TTFont(reg_name, fpath))
                        PDFRenderer._available_fonts[logical] = reg_name
                        registered = True
                        print(f"  ✓ Font registered: {reg_name} <- {filename}")
                        break
                    except Exception as e:
                        print(f"  ✗ Font register failed: {filename} -> {e}")

            # If this variant wasn't registered, fallback to regular
            if not registered and logical != 'regular':
                if 'regular' in PDFRenderer._available_fonts:
                    PDFRenderer._available_fonts[logical] = PDFRenderer._available_fonts['regular']
                    print(f"  ⚠ Font fallback: {logical} -> regular (NexorFont)")

        # Register font family for automatic bold/italic switching
        if 'regular' in PDFRenderer._available_fonts:
            try:
                from reportlab.pdfbase.pdfmetrics import registerFontFamily
                registerFontFamily(
                    'NexorFont',
                    normal=PDFRenderer._available_fonts.get('regular', 'NexorFont'),
                    bold=PDFRenderer._available_fonts.get('bold', 'NexorFont'),
                    italic=PDFRenderer._available_fonts.get('italic', 'NexorFont'),
                    boldItalic=PDFRenderer._available_fonts.get('bolditalic', 'NexorFont'),
                )
                print("  ✓ Font family 'NexorFont' registered")
            except Exception as e:
                print(f"  ⚠ Font family registration failed: {e}")

        PDFRenderer._fonts_registered = True
        has_fonts = bool(PDFRenderer._available_fonts)
        if has_fonts:
            print(f"✓ Türkçe karakter desteği aktif ({len(PDFRenderer._available_fonts)} font varyantı)")
        else:
            print(f"⚠ DejaVuSans bulunamadı: {font_path}")
            # List what IS in the directory
            if os.path.isdir(font_path):
                files = os.listdir(font_path)
                print(f"  Mevcut dosyalar: {', '.join(f for f in files if f.endswith('.ttf'))}")

        return has_fonts

    @staticmethod
    def _get_font_name(elem, has_dejavu):
        bold = elem.get('bold', False)
        italic = elem.get('italic', False)
        if has_dejavu and PDFRenderer._available_fonts:
            if bold and italic:
                return PDFRenderer._available_fonts.get('bolditalic', 'NexorFont')
            elif bold:
                return PDFRenderer._available_fonts.get('bold', 'NexorFont')
            elif italic:
                return PDFRenderer._available_fonts.get('italic', 'NexorFont')
            return PDFRenderer._available_fonts.get('regular', 'NexorFont')
        else:
            if bold and italic:
                return 'Helvetica-BoldOblique'
            elif bold:
                return 'Helvetica-Bold'
            elif italic:
                return 'Helvetica-Oblique'
            return 'Helvetica'

    @staticmethod
    def render(canvas_widget, test_data=None):
        """Render canvas elements to PDF and return file path"""
        import tempfile
        from reportlab.lib.pagesizes import mm
        from reportlab.pdfgen import canvas as pdf_canvas

        has_dejavu = PDFRenderer._register_fonts()

        w_mm = canvas_widget.width_mm
        h_mm = canvas_widget.height_mm

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='etiket_')
        temp_path = temp_file.name
        temp_file.close()

        c = pdf_canvas.Canvas(temp_path, pagesize=(w_mm * mm, h_mm * mm))

        if test_data is None:
            test_data = {
                'lot_no': 'LOT-2501-0001-01',
                'stok_kodu': 'TEST-12345',
                'stok_adi': 'Test Ürün Adı Örnek Parça',
                'musteri': 'Test Müşteri A.Ş.',
                'kaplama': 'KATAFOREZ',
                'miktar': 1000,
                'birim': 'ADET',
                'palet_no': 1,
                'toplam_palet': 5,
                'irsaliye_no': 'IRS-2501-001',
                'tarih': datetime.now().strftime('%d.%m.%Y'),
                'siparis_no': 'SIP-2501-001'
            }

        # Sync element positions from canvas items
        for elem in canvas_widget.elements:
            item = elem.get('item')
            if item:
                try:
                    pos = item.pos()
                    elem['x_mm'] = round(pos.x() / MM_TO_PX, 1)
                    elem['y_mm'] = round(pos.y() / MM_TO_PX, 1)
                except (RuntimeError, AttributeError):
                    pass

        # Draw each element
        for elem in canvas_widget.elements:
            PDFRenderer._draw_element(c, elem, test_data, w_mm, h_mm, has_dejavu)

        c.save()
        return temp_path

    @staticmethod
    def _draw_element(c, elem, data, page_w, page_h, has_dejavu):
        from reportlab.lib.pagesizes import mm as mm_unit

        x_mm = elem.get('x_mm', 0)
        y_mm = elem.get('y_mm', 0)
        t = elem.get('type')

        # ─── TEXT / FIELD ───────────────────────────────────────────
        if t in ('TEXT', 'FIELD'):
            font_name = PDFRenderer._get_font_name(elem, has_dejavu)
            size = elem.get('size', 10)

            # Try setting font, with robust fallback chain
            try:
                c.setFont(font_name, size)
            except Exception:
                # Fallback: try regular NexorFont (which supports Turkish)
                try:
                    font_name = PDFRenderer._available_fonts.get('regular', 'Helvetica')
                    c.setFont(font_name, size)
                except Exception:
                    font_name = 'Helvetica'
                    c.setFont(font_name, size)

            text = elem.get('text', '') if t == 'TEXT' else str(data.get(elem.get('field', ''), ''))

            # QGraphicsTextItem positions at top-left of the text bounding box
            # PDF drawString positions at baseline
            # Convert: PDF_y = page_height - (y_mm + ascent_in_mm)
            # Font ascent ≈ size * 0.75 (in points), convert to mm
            ascent_mm = (size * 0.75) * PT_TO_MM

            x_pt = x_mm * mm_unit
            y_pt = (page_h - y_mm - ascent_mm) * mm_unit

            align = elem.get('align', 'left')
            if align == 'center':
                tw = c.stringWidth(text, font_name, size)
                x_pt -= tw / 2
            elif align == 'right':
                tw = c.stringWidth(text, font_name, size)
                x_pt -= tw

            c.drawString(x_pt, y_pt, text)

        # ─── BARCODE ────────────────────────────────────────────────
        elif t == 'BARCODE':
            try:
                from reportlab.graphics.barcode import code128

                w_bc = elem.get('w_mm', 50)
                h_bc = elem.get('h_mm', 10)
                value = str(data.get(elem.get('field', 'lot_no'), 'NODATA'))

                bar_height = h_bc * mm_unit
                if elem.get('show_text', True):
                    bar_height = h_bc * 0.75 * mm_unit

                barcode = code128.Code128(
                    value,
                    barWidth=0.5 * mm_unit,
                    barHeight=bar_height,
                    humanReadable=elem.get('show_text', True),
                )

                x_pt = x_mm * mm_unit
                y_pt = (page_h - y_mm - h_bc) * mm_unit

                barcode.drawOn(c, x_pt, y_pt)
            except Exception as e:
                print(f"Barcode render error: {e}")

        # ─── LINE ──────────────────────────────────────────────────
        elif t == 'LINE':
            width = elem.get('width', 0.5)
            length = elem.get('length', 50)
            direction = elem.get('direction', 'Yatay')
            style = elem.get('line_style', 'solid')

            c.setLineWidth(width)

            if style == 'dashed':
                c.setDash(3, 2)
            elif style == 'dotted':
                c.setDash(1, 2)
            else:
                c.setDash()

            x1 = x_mm * mm_unit
            y1 = (page_h - y_mm) * mm_unit

            if direction == 'Yatay':
                c.line(x1, y1, (x_mm + length) * mm_unit, y1)
            else:
                c.line(x1, y1, x1, (page_h - y_mm - length) * mm_unit)

            c.setDash()  # Reset

        # ─── RECT ──────────────────────────────────────────────────
        elif t == 'RECT':
            w_r = elem.get('w_mm', 30)
            h_r = elem.get('h_mm', 15)
            border = elem.get('border_width', 0.5)

            c.setLineWidth(border)

            x_pt = x_mm * mm_unit
            y_pt = (page_h - y_mm - h_r) * mm_unit

            if elem.get('fill', False):
                c.setFillGray(0.95)
                if elem.get('rounded', False):
                    c.roundRect(x_pt, y_pt, w_r * mm_unit, h_r * mm_unit, 3 * mm_unit, stroke=1, fill=1)
                else:
                    c.rect(x_pt, y_pt, w_r * mm_unit, h_r * mm_unit, stroke=1, fill=1)
                c.setFillGray(0)
            else:
                if elem.get('rounded', False):
                    c.roundRect(x_pt, y_pt, w_r * mm_unit, h_r * mm_unit, 3 * mm_unit, stroke=1, fill=0)
                else:
                    c.rect(x_pt, y_pt, w_r * mm_unit, h_r * mm_unit, stroke=1, fill=0)

        # ─── IMAGE ─────────────────────────────────────────────────
        elif t == 'IMAGE':
            w_img = elem.get('w_mm', 25)
            h_img = elem.get('h_mm', 20)
            opacity = elem.get('opacity', 100) / 100.0

            x_pt = x_mm * mm_unit
            y_pt = (page_h - y_mm - h_img) * mm_unit

            image_drawn = False

            # Try file path
            if elem.get('image_path') and os.path.exists(elem['image_path']):
                try:
                    from reportlab.lib.utils import ImageReader
                    img = ImageReader(elem['image_path'])

                    if opacity < 1.0:
                        c.saveState()
                        c.setFillAlpha(opacity)

                    if elem.get('keep_aspect', True):
                        iw, ih = img.getSize()
                        ratio = min(w_img * mm_unit / iw, h_img * mm_unit / ih)
                        c.drawImage(img, x_pt, y_pt, iw * ratio, ih * ratio, mask='auto')
                    else:
                        c.drawImage(img, x_pt, y_pt, w_img * mm_unit, h_img * mm_unit, mask='auto')

                    if opacity < 1.0:
                        c.restoreState()

                    image_drawn = True
                except Exception as e:
                    print(f"Image file render error: {e}")

            # Try base64
            if not image_drawn and elem.get('image_data'):
                try:
                    import io
                    from reportlab.lib.utils import ImageReader
                    img_bytes = base64.b64decode(elem['image_data'])
                    img = ImageReader(io.BytesIO(img_bytes))

                    if opacity < 1.0:
                        c.saveState()
                        c.setFillAlpha(opacity)

                    if elem.get('keep_aspect', True):
                        iw, ih = img.getSize()
                        ratio = min(w_img * mm_unit / iw, h_img * mm_unit / ih)
                        c.drawImage(img, x_pt, y_pt, iw * ratio, ih * ratio, mask='auto')
                    else:
                        c.drawImage(img, x_pt, y_pt, w_img * mm_unit, h_img * mm_unit, mask='auto')

                    if opacity < 1.0:
                        c.restoreState()

                    image_drawn = True
                except Exception as e:
                    print(f"Image base64 render error: {e}")

            if not image_drawn:
                # Draw placeholder rectangle
                c.setStrokeGray(0.7)
                c.setDash(3, 2)
                c.rect(x_pt, y_pt, w_img * mm_unit, h_img * mm_unit)
                c.setDash()

        # ─── PRODUCT_IMAGE ─────────────────────────────────────────
        elif t == 'PRODUCT_IMAGE':
            w_img = elem.get('w_mm', 60)
            h_img = elem.get('h_mm', 50)

            x_pt = x_mm * mm_unit
            y_pt = (page_h - y_mm - h_img) * mm_unit

            image_drawn = False

            # Resolve image path: from data (stok_kodu) or test_stok_kodu
            img_path = None
            stok_kodu = data.get('stok_kodu', '')

            # First try with real stok_kodu from data
            if stok_kodu:
                img_path = find_product_image(str(stok_kodu))

            # Fallback to test stok_kodu or saved image_path
            if not img_path:
                if elem.get('test_stok_kodu'):
                    img_path = find_product_image(elem['test_stok_kodu'])
                elif elem.get('image_path') and os.path.exists(elem.get('image_path', '')):
                    img_path = elem['image_path']

            if img_path and os.path.exists(img_path):
                try:
                    from reportlab.lib.utils import ImageReader
                    img = ImageReader(img_path)

                    if elem.get('keep_aspect', True):
                        iw, ih = img.getSize()
                        ratio = min(w_img * mm_unit / iw, h_img * mm_unit / ih)
                        draw_w = iw * ratio
                        draw_h = ih * ratio
                    else:
                        draw_w = w_img * mm_unit
                        draw_h = h_img * mm_unit

                    c.drawImage(img, x_pt, y_pt, draw_w, draw_h, mask='auto')

                    # Optional border
                    if elem.get('show_border', False):
                        c.setStrokeGray(0.4)
                        c.setLineWidth(0.5)
                        c.rect(x_pt, y_pt, draw_w, draw_h)

                    image_drawn = True
                except Exception as e:
                    print(f"Product image render error: {e}")

            if not image_drawn:
                # Draw placeholder
                c.setStrokeColor(HexColor('#0ea5e9') if 'HexColor' in dir() else '#0ea5e9')
                c.setStrokeGray(0.5)
                c.setDash(3, 2)
                c.rect(x_pt, y_pt, w_img * mm_unit, h_img * mm_unit)
                c.setDash()
                # Label
                try:
                    font_name = PDFRenderer._available_fonts.get('regular', 'Helvetica')
                    c.setFont(font_name, 7)
                except Exception:
                    c.setFont('Helvetica', 7)
                c.setFillGray(0.5)
                c.drawString(x_pt + 2, y_pt + h_img * mm_unit - 10, f"Görsel: {stok_kodu or '?'}")
                c.setFillGray(0)


# ============================================================================
# MAIN PAGE
# ============================================================================
class EtiketTasarimPage(BasePage):
    """Label Design v3.0 - Professional WYSIWYG designer"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.current_sablon_id = None
        self._setup_ui()
        QTimer.singleShot(100, self._load_sablonlar)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        layout.addWidget(self._create_header())

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {self.theme.get('border', '#3d4454')}; width: 2px; }}
        """)

        # Left - Templates & Tools
        splitter.addWidget(self._create_left_panel())

        # Center - Canvas
        splitter.addWidget(self._create_center_panel())

        # Right - Properties
        splitter.addWidget(self._create_right_panel())

        splitter.setSizes([260, 580, 300])
        layout.addWidget(splitter, 1)

    # ── Header ─────────────────────────────────────────────────────────
    def _create_header(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.theme.get('bg_card', '#242938')},
                    stop:1 {self.theme.get('bg_secondary', '#1e2330')});
                border-radius: 10px; padding: 12px;
            }}
        """)
        layout = QHBoxLayout(frame)

        title = QLabel("🏷️ Etiket Tasarım v3.0")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(title)
        layout.addStretch()

        btn_base = f"""
            QPushButton {{
                border: none; border-radius: 6px; padding: 8px 18px;
                font-weight: bold; color: white; font-size: 13px;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
            QPushButton:pressed {{ padding-top: 9px; padding-bottom: 7px; }}
        """

        buttons = [
            ("➕ Yeni", self.theme.get('success', '#22c55e'), self._new_sablon),
            ("💾 Kaydet", self.theme.get('primary', '#6366f1'), self._save_sablon),
            ("📋 Kopyala", '#0ea5e9', self._duplicate_element),
            ("👁️ Önizle (PDF)", self.theme.get('warning', '#f59e0b'), self._preview_pdf),
        ]

        for text, color, handler in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(btn_base + f"QPushButton {{ background: {color}; }}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        return frame

    # ── Left panel ─────────────────────────────────────────────────────
    def _create_left_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card', '#242938')}; border-radius: 8px; }}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Templates ──
        lbl = QLabel("📋 Şablonlar")
        lbl.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl)

        self.sablon_list = QListWidget()
        self.sablon_list.setMaximumHeight(160)
        self.sablon_list.setStyleSheet(f"""
            QListWidget {{
                background: {self.theme.get('bg_input', '#1e2330')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
            }}
            QListWidget::item {{ padding: 7px; border-bottom: 1px solid {self.theme.get('border', '#3d4454')}; }}
            QListWidget::item:selected {{ background: {self.theme.get('primary', '#6366f1')}; color: white; }}
            QListWidget::item:hover {{ background: {self.theme.get('bg_hover', '#2d3548')}; }}
        """)
        self.sablon_list.itemClicked.connect(self._on_sablon_selected)
        layout.addWidget(self.sablon_list)

        # Delete template button
        del_tmpl_btn = QPushButton("🗑️ Şablonu Sil")
        del_tmpl_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {self.theme.get('error', '#ef4444')};
                border: 1px solid {self.theme.get('error', '#ef4444')};
                border-radius: 4px; padding: 4px 8px; font-size: 11px;
            }}
            QPushButton:hover {{ background: {self.theme.get('error', '#ef4444')}; color: white; }}
        """)
        del_tmpl_btn.clicked.connect(self._delete_sablon)
        layout.addWidget(del_tmpl_btn)

        # Varsayılan yap butonu
        varsayilan_btn = QPushButton("⭐ Final Kalite Varsayılanı Yap")
        varsayilan_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {self.theme.get('warning', '#f59e0b')};
                border: 1px solid {self.theme.get('warning', '#f59e0b')};
                border-radius: 4px; padding: 4px 8px; font-size: 11px;
            }}
            QPushButton:hover {{ background: {self.theme.get('warning', '#f59e0b')}; color: black; }}
        """)
        varsayilan_btn.clicked.connect(self._set_varsayilan)
        layout.addWidget(varsayilan_btn)

        # ── Label Size ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {self.theme.get('border', '#3d4454')}; max-height: 1px;")
        layout.addWidget(sep)

        lbl2 = QLabel("📐 Etiket Boyutu")
        lbl2.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl2)

        spin_style = f"""
            QDoubleSpinBox {{
                background: {self.theme.get('bg_input', '#1e2330')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 4px; padding: 5px;
            }}
        """

        size_layout = QGridLayout()
        size_layout.setSpacing(6)

        size_layout.addWidget(QLabel("En:"), 0, 0)
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(30, 300)
        self.width_spin.setValue(100)
        self.width_spin.setSuffix(" mm")
        self.width_spin.setStyleSheet(spin_style)
        size_layout.addWidget(self.width_spin, 0, 1)

        size_layout.addWidget(QLabel("Boy:"), 1, 0)
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(20, 200)
        self.height_spin.setValue(50)
        self.height_spin.setSuffix(" mm")
        self.height_spin.setStyleSheet(spin_style)
        size_layout.addWidget(self.height_spin, 1, 1)

        # Apply size button
        apply_btn = QPushButton("↻ Boyut Uygula")
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input', '#1e2330')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 4px; padding: 5px;
            }}
            QPushButton:hover {{ border-color: {self.theme.get('primary', '#6366f1')}; }}
        """)
        apply_btn.clicked.connect(self._apply_label_size)
        size_layout.addWidget(apply_btn, 2, 0, 1, 2)

        layout.addLayout(size_layout)

        # ── Tools ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"background: {self.theme.get('border', '#3d4454')}; max-height: 1px;")
        layout.addWidget(sep2)

        lbl3 = QLabel("🧰 Element Ekle")
        lbl3.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl3)

        tool_style = f"""
            QPushButton {{
                background: {self.theme.get('bg_input', '#1e2330')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px; padding: 9px 12px;
                text-align: left; font-weight: 500; font-size: 13px;
            }}
            QPushButton:hover {{
                background: {self.theme.get('bg_hover', '#2d3548')};
                border-color: {self.theme.get('primary', '#6366f1')};
            }}
        """

        tools = [
            ("📝  Metin", 'TEXT'),
            ("📊  Veri Alanı", 'FIELD'),
            ("▪️  Barkod", 'BARCODE'),
            ("📸  Ürün Görseli", 'PRODUCT_IMAGE'),
            ("🖼️  Logo / Resim", 'IMAGE'),
            ("➖  Çizgi", 'LINE'),
            ("▭  Dikdörtgen", 'RECT'),
        ]

        for label, etype in tools:
            btn = QPushButton(label)
            btn.setStyleSheet(tool_style)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, t=etype: self._add_element(t))
            layout.addWidget(btn)

        layout.addStretch()
        return frame

    # ── Center panel ───────────────────────────────────────────────────
    def _create_center_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card', '#242938')}; border-radius: 8px; }}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("🎨 Tasarım Alanı")
        title.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold; font-size: 14px;")
        title_row.addWidget(title)
        title_row.addStretch()

        # Zoom controls
        zoom_in = QPushButton("Yaklas")
        zoom_in.setFixedSize(52, 28)
        zoom_in.setStyleSheet(f"""
            QPushButton {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')}; border-radius: 4px; font-size: 11px; }}
            QPushButton:hover {{ border-color: {self.theme.get('primary')}; }}
        """)
        zoom_in.clicked.connect(lambda: self.canvas.scale(1.2, 1.2))
        title_row.addWidget(zoom_in)

        zoom_out = QPushButton("Uzaklas")
        zoom_out.setFixedSize(56, 28)
        zoom_out.setStyleSheet(zoom_in.styleSheet())
        zoom_out.clicked.connect(lambda: self.canvas.scale(1 / 1.2, 1 / 1.2))
        title_row.addWidget(zoom_out)

        zoom_fit = QPushButton("Sigdir")
        zoom_fit.setFixedSize(48, 28)
        zoom_fit.setToolTip("Sığdır")
        zoom_fit.setStyleSheet(zoom_in.styleSheet())
        zoom_fit.clicked.connect(lambda: self.canvas._fit_view())
        title_row.addWidget(zoom_fit)

        layout.addLayout(title_row)

        # Canvas
        self.canvas = DesignCanvas(
            width_mm=self.width_spin.value(),
            height_mm=self.height_spin.value(),
            theme=self.theme
        )
        self.canvas.element_selected.connect(self._on_element_selected)
        self.canvas.element_moved.connect(self._on_element_moved)
        layout.addWidget(self.canvas, 1)

        # Bottom toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{ background: {self.theme.get('bg_input', '#1e2330')};
                border-radius: 6px; padding: 6px; }}
        """)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setSpacing(8)

        # Delete button
        del_btn = QPushButton("🗑️ Seçili Sil")
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('error', '#ef4444')};
                color: white; border: none; border-radius: 4px; padding: 6px 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #dc2626; }}
        """)
        del_btn.clicked.connect(self.canvas.delete_selected)
        tb_layout.addWidget(del_btn)

        # Clear all
        clear_btn = QPushButton("🧹 Tümünü Temizle")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.theme.get('text_secondary', '#9ca3af')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 4px; padding: 6px 14px;
            }}
            QPushButton:hover {{ border-color: {self.theme.get('error', '#ef4444')}; color: {self.theme.get('error', '#ef4444')}; }}
        """)
        clear_btn.clicked.connect(self._clear_all_confirm)
        tb_layout.addWidget(clear_btn)

        tb_layout.addStretch()

        # Coordinate display
        self.coord_label = QLabel("📍 Hazır")
        self.coord_label.setStyleSheet(f"color: {self.theme.get('text_secondary', '#9ca3af')}; font-size: 12px;")
        tb_layout.addWidget(self.coord_label)

        layout.addWidget(toolbar)
        return frame

    # ── Right panel ────────────────────────────────────────────────────
    def _create_right_panel(self) -> QFrame:
        self.properties_panel = PropertiesPanel(self.theme, canvas=self.canvas)
        self.properties_panel.properties_changed.connect(self._on_properties_changed)
        return self.properties_panel

    # ── Element actions ────────────────────────────────────────────────
    def _add_element(self, elem_type: str):
        elem = self.canvas.add_element(elem_type)
        # If IMAGE, immediately ask for file
        if elem_type == 'IMAGE':
            path, _ = QFileDialog.getOpenFileName(
                self, "Logo / Resim Seç", "",
                "Resimler (*.png *.jpg *.jpeg *.bmp *.svg);;Tüm Dosyalar (*)"
            )
            if path:
                elem['image_path'] = path
                try:
                    with open(path, 'rb') as f:
                        elem['image_data'] = base64.b64encode(f.read()).decode('utf-8')
                    elem['image_ext'] = os.path.splitext(path)[1].lower()
                except Exception as e:
                    print(f"Image read error: {e}")
                self.canvas.redraw_element(elem)

    def _duplicate_element(self):
        self.canvas.duplicate_selected()

    def _clear_all_confirm(self):
        if not self.canvas.elements:
            return
        reply = QMessageBox.question(
            self, "Onay",
            "Tüm elementler silinecek.\nDevam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.canvas.clear_all()
            self.properties_panel.clear()

    # ── Selection & move callbacks ─────────────────────────────────────
    def _on_element_selected(self, element: dict):
        if element and element.get('type'):
            self.properties_panel.load_element(element)
            self.coord_label.setText(
                f"📍 {element['type']} @ ({element.get('x_mm', 0):.1f}, {element.get('y_mm', 0):.1f}) mm"
            )
        else:
            self.properties_panel.clear()
            self.coord_label.setText("📍 Hazır")

    def _on_element_moved(self, element: dict):
        self.properties_panel.update_position_display(element)
        self.coord_label.setText(
            f"📍 {element['type']} @ ({element.get('x_mm', 0):.1f}, {element.get('y_mm', 0):.1f}) mm"
        )

    def _on_properties_changed(self, props: dict):
        if self.canvas.selected_element:
            self.canvas.redraw_element(self.canvas.selected_element)

    # ── Label size ─────────────────────────────────────────────────────
    def _apply_label_size(self):
        """Apply new label size - re-create canvas scene"""
        w = self.width_spin.value()
        h = self.height_spin.value()

        # Save elements
        elements_backup = []
        for elem in self.canvas.elements:
            item = elem.get('item')
            if item:
                try:
                    pos = item.pos()
                    elem['x_mm'] = round(pos.x() / MM_TO_PX, 1)
                    elem['y_mm'] = round(pos.y() / MM_TO_PX, 1)
                except (RuntimeError, AttributeError):
                    pass
            backup = {k: v for k, v in elem.items() if k != 'item'}
            elements_backup.append(backup)

        # Rebuild
        self.canvas.width_mm = w
        self.canvas.height_mm = h
        self.canvas.scene.clear()
        self.canvas.elements.clear()
        self.canvas.selected_element = None
        self.canvas._setup_scene()

        # Restore elements
        for eb in elements_backup:
            et = eb.pop('type')
            x = eb.pop('x_mm', 5)
            y = eb.pop('y_mm', 5)
            eb.pop('id', None)
            self.canvas.add_element(et, x, y, **eb)

        self.canvas._fit_view()

    # ── Template CRUD ──────────────────────────────────────────────────
    def _load_sablonlar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sablon_kodu, sablon_adi, sablon_tipi, genislik_mm, yukseklik_mm,
                       ISNULL(varsayilan_mi, 0) as varsayilan_mi
                FROM tanim.etiket_sablonlari
                WHERE aktif_mi = 1
                ORDER BY varsayilan_mi DESC, sablon_adi
            """)

            self.sablon_list.clear()
            for row in cursor.fetchall():
                sid, kod, adi, tip, w, h = row[0], row[1], row[2], row[3], row[4], row[5]
                varsayilan = row[6] if len(row) > 6 else 0
                w = float(w) if w else 100.0
                h = float(h) if h else 50.0
                display = f"{adi} ({w:.0f}×{h:.0f}mm)"
                prefix = "⭐ " if varsayilan else ""
                item = QListWidgetItem(f"{prefix}{display}")
                item.setData(Qt.UserRole, {
                    'sablon_id': sid, 'kod': kod, 'adi': adi,
                    'genislik': w, 'yukseklik': h
                })
                self.sablon_list.addItem(item)
            conn.close()
        except Exception as e:
            print(f"Template load error: {e}")

    def _on_sablon_selected(self, item: QListWidgetItem):
        try:
            data = item.data(Qt.UserRole)
            sid = data['sablon_id']

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT genislik_mm, yukseklik_mm, tasarim_json
                FROM tanim.etiket_sablonlari WHERE id = ?
            """, (sid,))

            row = cursor.fetchone()
            if row:
                w, h, json_str = row
                w = float(w) if w else 100.0
                h = float(h) if h else 50.0

                self.width_spin.setValue(w)
                self.height_spin.setValue(h)

                self.canvas.width_mm = w
                self.canvas.height_mm = h
                self.canvas.scene.clear()
                self.canvas.elements.clear()
                self.canvas.selected_element = None
                self.canvas._setup_scene()

                if json_str:
                    self.canvas.load_from_json(json_str)

                self.canvas._fit_view()
                self.current_sablon_id = sid

            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Şablon yüklenemedi:\n{str(e)}")

    def _new_sablon(self):
        name, ok = QInputDialog.getText(self, "Yeni Şablon", "Şablon adı:")
        if ok and name:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("SELECT MAX(id) FROM tanim.etiket_sablonlari")
                max_id = cursor.fetchone()[0] or 0
                kod = f"SBLNV3_{max_id + 1:03d}"

                cursor.execute("""
                    INSERT INTO tanim.etiket_sablonlari
                    (sablon_kodu, sablon_adi, sablon_tipi, genislik_mm, yukseklik_mm, aktif_mi, olusturma_tarihi)
                    VALUES (?, ?, 'PALET', ?, ?, 1, GETDATE())
                """, (kod, name, self.width_spin.value(), self.height_spin.value()))
                conn.commit()

                cursor.execute("SELECT @@IDENTITY")
                self.current_sablon_id = cursor.fetchone()[0]
                conn.close()

                # Clear canvas for new template
                self.canvas.clear_all()
                self._apply_label_size()

                self._load_sablonlar()
                QMessageBox.information(self, "Başarılı", f"Yeni şablon oluşturuldu: {name}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Şablon oluşturulamadı:\n{str(e)}")

    def _save_sablon(self):
        if not self.current_sablon_id:
            QMessageBox.warning(self, "Uyarı", "Önce bir şablon seçin veya yeni şablon oluşturun!")
            return
        try:
            json_str = self.canvas.export_to_json()

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tanim.etiket_sablonlari
                SET tasarim_json = ?,
                    genislik_mm = ?,
                    yukseklik_mm = ?,
                    guncelleme_tarihi = GETDATE()
                WHERE id = ?
            """, (json_str, self.width_spin.value(), self.height_spin.value(), self.current_sablon_id))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Başarılı", "Şablon kaydedildi! ✓")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası:\n{str(e)}")

    def _set_varsayilan(self):
        """Seçili şablonu Final Kalite varsayılanı yap"""
        if not self.current_sablon_id:
            QMessageBox.warning(self, "Uyarı", "Önce bir şablon seçin!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # varsayilan_mi kolonu yoksa ekle
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('tanim.etiket_sablonlari') AND name = 'varsayilan_mi')
                ALTER TABLE tanim.etiket_sablonlari ADD varsayilan_mi BIT DEFAULT 0
            """)

            # Önce hepsini sıfırla
            cursor.execute("UPDATE tanim.etiket_sablonlari SET varsayilan_mi = 0")
            # Seçileni varsayılan yap
            cursor.execute("UPDATE tanim.etiket_sablonlari SET varsayilan_mi = 1 WHERE id = ?", (self.current_sablon_id,))
            conn.commit()
            conn.close()

            self._load_sablonlar()
            QMessageBox.information(self, "Başarılı", "Bu şablon Final Kalite varsayılanı olarak ayarlandı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Varsayılan ayarlanamadı:\n{str(e)}")

    def _delete_sablon(self):
        if not self.current_sablon_id:
            QMessageBox.warning(self, "Uyarı", "Silinecek şablonu seçin!")
            return

        reply = QMessageBox.question(
            self, "Şablon Silme",
            "Bu şablon kalıcı olarak silinecek.\nDevam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tanim.etiket_sablonlari
                    SET aktif_mi = 0 WHERE id = ?
                """, (self.current_sablon_id,))
                conn.commit()
                conn.close()

                self.current_sablon_id = None
                self.canvas.clear_all()
                self._load_sablonlar()
                QMessageBox.information(self, "Silindi", "Şablon silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası:\n{str(e)}")

    # ── PDF Preview ────────────────────────────────────────────────────
    def _preview_pdf(self):
        """Generate PDF preview using PDFRenderer"""
        try:
            temp_path = PDFRenderer.render(self.canvas)

            import subprocess
            subprocess.Popen(['start', '', temp_path], shell=True)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturma hatası:\n{str(e)}")
            import traceback
            traceback.print_exc()
