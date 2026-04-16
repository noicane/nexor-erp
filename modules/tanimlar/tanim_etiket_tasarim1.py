# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Etiket Tasarım Sayfası
Sürükle-bırak etiket şablonu tasarlama - Geliştirilmiş Versiyon
"""
import json
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QScrollArea, QWidget, QSpinBox, QDoubleSpinBox,
    QTextEdit, QSplitter, QGroupBox, QGridLayout, QTabWidget,
    QListWidget, QListWidgetItem, QCheckBox, QColorDialog,
    QFontComboBox, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QMenu, QGraphicsItem,
    QFormLayout, QSlider
)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal
from PySide6.QtGui import (
    QColor, QFont, QPen, QBrush, QPainter, QCursor,
    QAction, QDrag
)

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


# ============================================================================
# ELEMENT EKLEME DIALOG
# ============================================================================

class ElementEkleDialog(QDialog):
    """Element ekleme dialogu"""
    
    def __init__(self, element_type: str, theme: dict, parent=None, element_data: dict = None):
        super().__init__(parent)
        self.element_type = element_type
        self.theme = theme
        self.element_data = element_data  # Düzenleme için
        self.result_data = None
        
        type_names = {
            'TEXT': 'Metin',
            'FIELD': 'Veri Alanı',
            'BARCODE': 'Barkod',
            'IMAGE': 'Resim',
            'LINE': 'Çizgi',
            'RECT': 'Dikdörtgen'
        }
        
        title = "Düzenle" if element_data else "Ekle"
        self.setWindowTitle(f"🏷️ {type_names.get(element_type, element_type)} {title}")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self._setup_ui()
        
        if element_data:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px;
                color: {brand.TEXT};
            }}
            QGroupBox {{ 
                color: {brand.TEXT}; font-weight: bold;
                border: 1px solid {brand.BORDER}; border-radius: 8px;
                margin-top: 12px; padding-top: 8px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 8px; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Pozisyon grubu
        pos_group = QGroupBox("📍 Pozisyon (mm)")
        pos_layout = QGridLayout(pos_group)
        
        pos_layout.addWidget(QLabel("X:"), 0, 0)
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(0, 300)
        self.x_spin.setDecimals(1)
        self.x_spin.setValue(5)
        pos_layout.addWidget(self.x_spin, 0, 1)
        
        pos_layout.addWidget(QLabel("Y:"), 0, 2)
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(0, 200)
        self.y_spin.setDecimals(1)
        self.y_spin.setValue(5)
        pos_layout.addWidget(self.y_spin, 0, 3)
        
        layout.addWidget(pos_group)
        
        # Element tipine göre özel alanlar
        if self.element_type == 'TEXT':
            self._setup_text_fields(layout)
        elif self.element_type == 'FIELD':
            self._setup_field_fields(layout)
        elif self.element_type == 'BARCODE':
            self._setup_barcode_fields(layout)
        elif self.element_type == 'IMAGE':
            self._setup_image_fields(layout)
        elif self.element_type == 'LINE':
            self._setup_line_fields(layout)
        elif self.element_type == 'RECT':
            self._setup_rect_fields(layout)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT};
                          border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 10px 24px; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("✅ Tamam")
        ok_btn.setStyleSheet(f"""
            QPushButton {{ background: {brand.SUCCESS}; color: white;
                          border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold; }}
            QPushButton:hover {{ background: #16a34a; }}
        """)
        ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _setup_text_fields(self, layout):
        """Metin alanları"""
        group = QGroupBox("📝 Metin Özellikleri")
        form = QFormLayout(group)
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Metin içeriği...")
        form.addRow("Metin:", self.text_input)
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Helvetica", "Arial", "Times New Roman", "Courier New", "Verdana"])
        form.addRow("Yazı Tipi:", self.font_combo)
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 72)
        self.size_spin.setValue(10)
        form.addRow("Boyut:", self.size_spin)
        
        self.bold_check = QCheckBox("Kalın")
        self.bold_check.setStyleSheet(f"color: {brand.TEXT};")
        form.addRow("", self.bold_check)
        
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton("⬛ Siyah")
        self.color_btn.setStyleSheet(f"background: #000; color: #fff; border-radius: 4px; padding: 6px 12px;")
        self.color_btn.clicked.connect(self._pick_color)
        self.selected_color = "#000000"
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        form.addRow("Renk:", color_layout)
        
        layout.addWidget(group)
    
    def _setup_field_fields(self, layout):
        """Veri alanı seçimi"""
        group = QGroupBox("📊 Veri Alanı")
        form = QFormLayout(group)
        
        self.field_combo = QComboBox()
        fields = [
            ("{lot_no}", "Lot Numarası"),
            ("{stok_kodu}", "Stok Kodu"),
            ("{stok_adi}", "Stok Adı"),
            ("{musteri}", "Müşteri"),
            ("{kaplama}", "Kaplama Tipi"),
            ("{miktar}", "Miktar"),
            ("{birim}", "Birim"),
            ("{palet_no}", "Palet No"),
            ("{toplam_palet}", "Toplam Palet"),
            ("{irsaliye_no}", "İrsaliye No"),
            ("{tarih}", "Tarih"),
            ("{siparis_no}", "Sipariş No"),
            ("{musteri_siparis_no}", "Müşteri Sipariş No"),
        ]
        for code, name in fields:
            self.field_combo.addItem(f"{name} {code}", code)
        form.addRow("Alan:", self.field_combo)
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Helvetica", "Arial", "Times New Roman", "Courier New", "Verdana"])
        form.addRow("Yazı Tipi:", self.font_combo)
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 72)
        self.size_spin.setValue(10)
        form.addRow("Boyut:", self.size_spin)
        
        self.bold_check = QCheckBox("Kalın")
        self.bold_check.setStyleSheet(f"color: {brand.TEXT};")
        form.addRow("", self.bold_check)
        
        layout.addWidget(group)
    
    def _setup_barcode_fields(self, layout):
        """Barkod alanları"""
        group = QGroupBox("📊 Barkod Özellikleri")
        form = QFormLayout(group)
        
        self.barcode_field_combo = QComboBox()
        self.barcode_field_combo.addItems([
            "lot_no - Lot Numarası",
            "stok_kodu - Stok Kodu",
            "irsaliye_no - İrsaliye No"
        ])
        form.addRow("Barkod Alanı:", self.barcode_field_combo)
        
        self.barcode_type_combo = QComboBox()
        self.barcode_type_combo.addItems(["CODE128", "CODE39", "EAN13", "QR"])
        form.addRow("Barkod Tipi:", self.barcode_type_combo)
        
        self.barcode_height_spin = QSpinBox()
        self.barcode_height_spin.setRange(5, 30)
        self.barcode_height_spin.setValue(8)
        form.addRow("Yükseklik (mm):", self.barcode_height_spin)
        
        self.barcode_width_spin = QSpinBox()
        self.barcode_width_spin.setRange(20, 100)
        self.barcode_width_spin.setValue(40)
        form.addRow("Genişlik (mm):", self.barcode_width_spin)
        
        layout.addWidget(group)
    
    def _setup_image_fields(self, layout):
        """Resim alanları"""
        group = QGroupBox("🖼️ Resim Özellikleri")
        form = QFormLayout(group)
        
        self.image_field_combo = QComboBox()
        self.image_field_combo.addItems([
            "resim_path - Ürün Resmi",
            "logo - Firma Logosu"
        ])
        form.addRow("Resim Kaynağı:", self.image_field_combo)
        
        self.image_width_spin = QSpinBox()
        self.image_width_spin.setRange(5, 100)
        self.image_width_spin.setValue(20)
        form.addRow("Genişlik (mm):", self.image_width_spin)
        
        self.image_height_spin = QSpinBox()
        self.image_height_spin.setRange(5, 100)
        self.image_height_spin.setValue(20)
        form.addRow("Yükseklik (mm):", self.image_height_spin)
        
        layout.addWidget(group)
    
    def _setup_line_fields(self, layout):
        """Çizgi alanları"""
        group = QGroupBox("➖ Çizgi Özellikleri")
        form = QFormLayout(group)
        
        form.addRow(QLabel("Bitiş Noktası:"))
        
        self.x2_spin = QDoubleSpinBox()
        self.x2_spin.setRange(0, 300)
        self.x2_spin.setDecimals(1)
        self.x2_spin.setValue(50)
        form.addRow("X2 (mm):", self.x2_spin)
        
        self.y2_spin = QDoubleSpinBox()
        self.y2_spin.setRange(0, 200)
        self.y2_spin.setDecimals(1)
        self.y2_spin.setValue(5)
        form.addRow("Y2 (mm):", self.y2_spin)
        
        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.1, 5)
        self.line_width_spin.setDecimals(1)
        self.line_width_spin.setValue(0.5)
        form.addRow("Kalınlık (mm):", self.line_width_spin)
        
        layout.addWidget(group)
    
    def _setup_rect_fields(self, layout):
        """Dikdörtgen alanları"""
        group = QGroupBox("⬜ Dikdörtgen Özellikleri")
        form = QFormLayout(group)
        
        self.rect_width_spin = QSpinBox()
        self.rect_width_spin.setRange(5, 200)
        self.rect_width_spin.setValue(30)
        form.addRow("Genişlik (mm):", self.rect_width_spin)
        
        self.rect_height_spin = QSpinBox()
        self.rect_height_spin.setRange(5, 100)
        self.rect_height_spin.setValue(15)
        form.addRow("Yükseklik (mm):", self.rect_height_spin)
        
        self.border_width_spin = QDoubleSpinBox()
        self.border_width_spin.setRange(0.1, 5)
        self.border_width_spin.setDecimals(1)
        self.border_width_spin.setValue(0.5)
        form.addRow("Çerçeve Kalınlığı:", self.border_width_spin)
        
        self.fill_check = QCheckBox("İç dolgu")
        self.fill_check.setStyleSheet(f"color: {brand.TEXT};")
        form.addRow("", self.fill_check)
        
        layout.addWidget(group)
    
    def _pick_color(self):
        """Renk seçici"""
        color = QColorDialog.getColor(QColor(self.selected_color), self)
        if color.isValid():
            self.selected_color = color.name()
            self.color_btn.setStyleSheet(f"background: {self.selected_color}; color: {'#fff' if color.lightness() < 128 else '#000'}; border-radius: 4px; padding: 6px 12px;")
            self.color_btn.setText(f"⬛ {self.selected_color}")
    
    def _load_data(self):
        """Mevcut element verilerini yükle"""
        if not self.element_data:
            return
        
        self.x_spin.setValue(self.element_data.get('x_mm', 5))
        self.y_spin.setValue(self.element_data.get('y_mm', 5))
        
        if self.element_type == 'TEXT':
            self.text_input.setText(self.element_data.get('text', ''))
            idx = self.font_combo.findText(self.element_data.get('font', 'Helvetica'))
            if idx >= 0:
                self.font_combo.setCurrentIndex(idx)
            self.size_spin.setValue(self.element_data.get('size', 10))
            self.bold_check.setChecked(self.element_data.get('bold', False))
            self.selected_color = self.element_data.get('color', '#000000')
    
    def _on_ok(self):
        """Tamam butonuna basıldı"""
        self.result_data = {
            'type': self.element_type if self.element_type != 'FIELD' else 'TEXT',
            'x_mm': self.x_spin.value(),
            'y_mm': self.y_spin.value()
        }
        
        if self.element_type == 'TEXT':
            if not self.text_input.text().strip():
                QMessageBox.warning(self, "Uyarı", "Metin girmelisiniz!")
                return
            self.result_data['text'] = self.text_input.text()
            self.result_data['font'] = self.font_combo.currentText()
            self.result_data['size'] = self.size_spin.value()
            self.result_data['bold'] = self.bold_check.isChecked()
            self.result_data['color'] = self.selected_color
        
        elif self.element_type == 'FIELD':
            self.result_data['text'] = self.field_combo.currentData()
            self.result_data['font'] = self.font_combo.currentText()
            self.result_data['size'] = self.size_spin.value()
            self.result_data['bold'] = self.bold_check.isChecked()
            self.result_data['color'] = '#000000'
        
        elif self.element_type == 'BARCODE':
            field_text = self.barcode_field_combo.currentText()
            self.result_data['field'] = field_text.split(' - ')[0]
            self.result_data['barcode_type'] = self.barcode_type_combo.currentText()
            self.result_data['h_mm'] = self.barcode_height_spin.value()
            self.result_data['w_mm'] = self.barcode_width_spin.value()
        
        elif self.element_type == 'IMAGE':
            field_text = self.image_field_combo.currentText()
            self.result_data['field'] = field_text.split(' - ')[0]
            self.result_data['w_mm'] = self.image_width_spin.value()
            self.result_data['h_mm'] = self.image_height_spin.value()
        
        elif self.element_type == 'LINE':
            self.result_data['x2_mm'] = self.x2_spin.value()
            self.result_data['y2_mm'] = self.y2_spin.value()
            self.result_data['width'] = self.line_width_spin.value()
        
        elif self.element_type == 'RECT':
            self.result_data['w_mm'] = self.rect_width_spin.value()
            self.result_data['h_mm'] = self.rect_height_spin.value()
            self.result_data['border_width'] = self.border_width_spin.value()
            self.result_data['fill'] = self.fill_check.isChecked()
        
        self.accept()


# ============================================================================
# ETIKET ONIZLEME GRAPHICS VIEW
# ============================================================================

class EtiketGraphicsView(QGraphicsView):
    """Etiket önizleme ve tasarım alanı"""
    
    element_selected = Signal(dict)
    element_deleted = Signal()
    
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        self.mm_to_px = 3.78
        self.etiket_w_mm = 100
        self.etiket_h_mm = 50
        
        self.elements = []
        self.selected_element = None
        
        self._setup_view()
        self._draw_etiket_frame()
    
    def _setup_view(self):
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setBackgroundBrush(QBrush(QColor(brand.BG_MAIN)))
        self.setMinimumSize(450, 250)
    
    def _draw_etiket_frame(self):
        self.scene.clear()
        self.elements = []
        
        w = self.etiket_w_mm * self.mm_to_px
        h = self.etiket_h_mm * self.mm_to_px
        
        bg = self.scene.addRect(0, 0, w, h, QPen(QColor('#ccc')), QBrush(QColor('#fff')))
        
        pen = QPen(QColor('#999'), 1, Qt.DashLine)
        self.scene.addRect(-2, -2, w + 4, h + 4, pen)
        
        self.setSceneRect(-20, -20, w + 40, h + 40)
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
    
    def set_etiket_boyut(self, w_mm: float, h_mm: float):
        self.etiket_w_mm = w_mm
        self.etiket_h_mm = h_mm
        self._draw_etiket_frame()
    
    def add_element(self, elem_data: dict):
        """Element ekle"""
        elem_type = elem_data.get('type', 'TEXT')
        x_mm = elem_data.get('x_mm', 5)
        y_mm = elem_data.get('y_mm', 5)
        
        if elem_type == 'TEXT':
            return self._add_text_element(elem_data)
        elif elem_type == 'BARCODE':
            return self._add_barcode_element(elem_data)
        elif elem_type == 'IMAGE':
            return self._add_image_element(elem_data)
        elif elem_type == 'LINE':
            return self._add_line_element(elem_data)
        elif elem_type == 'RECT':
            return self._add_rect_element(elem_data)
    
    def _add_text_element(self, data: dict):
        x = data.get('x_mm', 5) * self.mm_to_px
        y = data.get('y_mm', 5) * self.mm_to_px
        text = data.get('text', 'Metin')
        font_name = data.get('font', 'Helvetica')
        font_size = data.get('size', 10)
        bold = data.get('bold', False)
        color = data.get('color', '#000000')
        
        font = QFont(font_name, font_size)
        font.setBold(bold)
        
        item = self.scene.addText(text, font)
        item.setPos(x, y)
        item.setDefaultTextColor(QColor(color))
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        element = {**data, 'item': item}
        self.elements.append(element)
        return element
    
    def _add_barcode_element(self, data: dict):
        x = data.get('x_mm', 5) * self.mm_to_px
        y = data.get('y_mm', 5) * self.mm_to_px
        w = data.get('w_mm', 40) * self.mm_to_px
        h = data.get('h_mm', 8) * self.mm_to_px
        
        pen = QPen(QColor('#333'), 1)
        brush = QBrush(QColor('#eee'))
        item = self.scene.addRect(x, y, w, h, pen, brush)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        font = QFont("Helvetica", 7)
        field = data.get('field', 'lot_no')
        text_item = self.scene.addText(f"||||| {field} |||||", font)
        text_item.setPos(x + 5, y + 2)
        text_item.setDefaultTextColor(QColor('#666'))
        text_item.setParentItem(item)
        
        element = {**data, 'item': item, 'text_item': text_item}
        self.elements.append(element)
        return element
    
    def _add_image_element(self, data: dict):
        x = data.get('x_mm', 5) * self.mm_to_px
        y = data.get('y_mm', 5) * self.mm_to_px
        w = data.get('w_mm', 20) * self.mm_to_px
        h = data.get('h_mm', 20) * self.mm_to_px
        
        pen = QPen(QColor('#999'), 1, Qt.DashLine)
        brush = QBrush(QColor('#f5f5f5'))
        item = self.scene.addRect(x, y, w, h, pen, brush)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        font = QFont("Helvetica", 8)
        text_item = self.scene.addText("🖼️", font)
        text_item.setPos(x + w/2 - 10, y + h/2 - 10)
        text_item.setParentItem(item)
        
        element = {**data, 'item': item, 'text_item': text_item}
        self.elements.append(element)
        return element
    
    def _add_line_element(self, data: dict):
        x1 = data.get('x_mm', 5) * self.mm_to_px
        y1 = data.get('y_mm', 5) * self.mm_to_px
        x2 = data.get('x2_mm', 50) * self.mm_to_px
        y2 = data.get('y2_mm', 5) * self.mm_to_px
        width = data.get('width', 0.5) * self.mm_to_px
        
        pen = QPen(QColor('#000'), width)
        item = self.scene.addLine(x1, y1, x2, y2, pen)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        element = {**data, 'item': item}
        self.elements.append(element)
        return element
    
    def _add_rect_element(self, data: dict):
        x = data.get('x_mm', 5) * self.mm_to_px
        y = data.get('y_mm', 5) * self.mm_to_px
        w = data.get('w_mm', 30) * self.mm_to_px
        h = data.get('h_mm', 15) * self.mm_to_px
        border_width = data.get('border_width', 0.5) * self.mm_to_px
        fill = data.get('fill', False)
        
        pen = QPen(QColor('#000'), border_width)
        brush = QBrush(QColor('#f0f0f0')) if fill else QBrush(Qt.NoBrush)
        item = self.scene.addRect(x, y, w, h, pen, brush)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        element = {**data, 'item': item}
        self.elements.append(element)
        return element
    
    def delete_selected(self):
        """Seçili elementi sil"""
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            for elem in self.elements[:]:
                if elem.get('item') == item:
                    self.scene.removeItem(item)
                    if 'text_item' in elem:
                        try:
                            self.scene.removeItem(elem['text_item'])
                        except Exception:
                            pass
                    self.elements.remove(elem)
                    break
        self.element_deleted.emit()
    
    def load_from_json(self, json_str: str):
        """JSON'dan yükle"""
        try:
            data = json.loads(json_str)
            self._draw_etiket_frame()
            
            for elem in data.get('elements', []):
                self.add_element(elem)
        except Exception as e:
            print(f"JSON yükleme hatası: {e}")
    
    def export_to_json(self) -> str:
        """JSON'a dışa aktar"""
        elements_data = []
        
        for elem in self.elements:
            item = elem.get('item')
            if not item:
                continue
            
            pos = item.pos() if hasattr(item, 'pos') else QPointF(0, 0)
            x_mm = pos.x() / self.mm_to_px
            y_mm = pos.y() / self.mm_to_px
            
            elem_data = {
                'type': elem.get('type', 'TEXT'),
                'x': round(x_mm, 1),
                'y': round(y_mm, 1)
            }
            
            if elem['type'] == 'TEXT':
                elem_data['text'] = elem.get('text', '')
                elem_data['font'] = elem.get('font', 'Helvetica')
                if elem.get('bold'):
                    elem_data['font'] += '-Bold'
                elem_data['size'] = elem.get('size', 10)
                elem_data['color'] = elem.get('color', '#000000')
            
            elif elem['type'] == 'BARCODE':
                elem_data['height'] = elem.get('h_mm', 8)
                elem_data['width'] = elem.get('w_mm', 40)
                elem_data['field'] = elem.get('field', 'lot_no')
                elem_data['barcode_type'] = elem.get('barcode_type', 'CODE128')
            
            elif elem['type'] == 'IMAGE':
                elem_data['width'] = elem.get('w_mm', 20)
                elem_data['height'] = elem.get('h_mm', 20)
                elem_data['field'] = elem.get('field', 'resim_path')
            
            elif elem['type'] == 'LINE':
                elem_data['x2'] = elem.get('x2_mm', 50)
                elem_data['y2'] = elem.get('y2_mm', 5)
                elem_data['width'] = elem.get('width', 0.5)
            
            elif elem['type'] == 'RECT':
                elem_data['width'] = elem.get('w_mm', 30)
                elem_data['height'] = elem.get('h_mm', 15)
                elem_data['border_width'] = elem.get('border_width', 0.5)
                elem_data['fill'] = elem.get('fill', False)
            
            elements_data.append(elem_data)
        
        return json.dumps({
            'version': '1.0',
            'background': '#FFFFFF',
            'elements': elements_data
        }, indent=2, ensure_ascii=False)
    
    def keyPressEvent(self, event):
        """Delete tuşu ile silme"""
        if event.key() == Qt.Key_Delete:
            self.delete_selected()
        else:
            super().keyPressEvent(event)


# ============================================================================
# ANA SAYFA
# ============================================================================

class EtiketTasarimPage(BasePage):
    """Etiket Tasarım Sayfası - Geliştirilmiş"""
    
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
        header = self._create_header()
        layout.addWidget(header)
        
        # Ana içerik - Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {brand.BORDER}; width: 3px; }}")
        
        # Sol panel - Şablon listesi + Element araçları
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Orta panel - Tasarım alanı
        center_panel = self._create_center_panel()
        splitter.addWidget(center_panel)
        
        # Sağ panel - Özellikler
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([280, 500, 300])
        layout.addWidget(splitter, 1)
    
    def _create_header(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border-radius: 8px; padding: 12px; }}")
        
        layout = QHBoxLayout(frame)
        
        title = QLabel("🏷️ Etiket Tasarım")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {brand.TEXT};")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Yeni şablon
        new_btn = QPushButton("➕ Yeni Şablon")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setStyleSheet(f"""
            QPushButton {{ background: {brand.SUCCESS}; color: white; 
                          border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }}
            QPushButton:hover {{ background: #16a34a; }}
        """)
        new_btn.clicked.connect(self._new_sablon)
        layout.addWidget(new_btn)
        
        # Önizle
        preview_btn = QPushButton("👁️ Önizle")
        preview_btn.setCursor(Qt.PointingHandCursor)
        preview_btn.setStyleSheet(f"""
            QPushButton {{ background: {brand.WARNING}; color: white; 
                          border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }}
            QPushButton:hover {{ background: #d97706; }}
        """)
        preview_btn.clicked.connect(self._preview_etiket)
        layout.addWidget(preview_btn)
        
        # Test Yazdır
        print_btn = QPushButton("🖨️ Test Yazdır")
        print_btn.setCursor(Qt.PointingHandCursor)
        print_btn.setStyleSheet(f"""
            QPushButton {{ background: {brand.INFO}; color: white; 
                          border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        print_btn.clicked.connect(self._test_yazdir)
        layout.addWidget(print_btn)
        
        # Kaydet
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{ background: {brand.PRIMARY}; color: white; 
                          border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }}
            QPushButton:hover {{ background: #4f46e5; }}
        """)
        save_btn.clicked.connect(self._save_sablon)
        layout.addWidget(save_btn)
        
        return frame
    
    def _create_left_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border-radius: 8px; }}")
        frame.setMinimumWidth(260)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # ===== ŞABLON LİSTESİ =====
        lbl = QLabel("📋 Şablonlar")
        lbl.setStyleSheet(f"color: {brand.TEXT}; font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl)
        
        self.sablon_list = QListWidget()
        self.sablon_list.setMaximumHeight(200)
        self.sablon_list.setStyleSheet(f"""
            QListWidget {{ 
                background: {brand.BG_INPUT}; 
                color: {brand.TEXT}; 
                border: 1px solid {brand.BORDER}; 
                border-radius: 6px; 
            }}
            QListWidget::item {{ padding: 8px; border-bottom: 1px solid {brand.BORDER}; }}
            QListWidget::item:selected {{ background: {brand.PRIMARY}; }}
            QListWidget::item:hover {{ background: {brand.BG_HOVER}; }}
        """)
        self.sablon_list.itemClicked.connect(self._on_sablon_selected)
        layout.addWidget(self.sablon_list)
        
        # Sil butonu
        del_btn = QPushButton("🗑️ Şablonu Sil")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{ background: {brand.ERROR}; color: white; 
                          border: none; border-radius: 6px; padding: 8px; }}
            QPushButton:hover {{ background: #dc2626; }}
        """)
        del_btn.clicked.connect(self._delete_sablon)
        layout.addWidget(del_btn)
        
        # ===== ELEMENT ARAÇLARI =====
        layout.addWidget(QLabel(""))  # Boşluk
        
        tools_label = QLabel("🧰 Element Ekle")
        tools_label.setStyleSheet(f"color: {brand.TEXT}; font-weight: bold; font-size: 14px;")
        layout.addWidget(tools_label)
        
        # Element butonları
        btn_style = f"""
            QPushButton {{ 
                background: {brand.BG_INPUT}; 
                color: {brand.TEXT}; 
                border: 1px solid {brand.BORDER}; 
                border-radius: 6px; 
                padding: 12px; 
                text-align: left;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.PRIMARY}; }}
        """
        
        # Metin ekle
        text_btn = QPushButton("📝  Metin Ekle")
        text_btn.setCursor(Qt.PointingHandCursor)
        text_btn.setStyleSheet(btn_style)
        text_btn.clicked.connect(lambda: self._add_element('TEXT'))
        layout.addWidget(text_btn)
        
        # Veri alanı ekle
        field_btn = QPushButton("📊  Veri Alanı Ekle")
        field_btn.setCursor(Qt.PointingHandCursor)
        field_btn.setStyleSheet(btn_style)
        field_btn.clicked.connect(lambda: self._add_element('FIELD'))
        layout.addWidget(field_btn)
        
        # Barkod ekle
        barcode_btn = QPushButton("📊  Barkod Ekle")
        barcode_btn.setCursor(Qt.PointingHandCursor)
        barcode_btn.setStyleSheet(btn_style)
        barcode_btn.clicked.connect(lambda: self._add_element('BARCODE'))
        layout.addWidget(barcode_btn)
        
        # Resim ekle
        image_btn = QPushButton("🖼️  Resim Ekle")
        image_btn.setCursor(Qt.PointingHandCursor)
        image_btn.setStyleSheet(btn_style)
        image_btn.clicked.connect(lambda: self._add_element('IMAGE'))
        layout.addWidget(image_btn)
        
        # Çizgi ekle
        line_btn = QPushButton("➖  Çizgi Ekle")
        line_btn.setCursor(Qt.PointingHandCursor)
        line_btn.setStyleSheet(btn_style)
        line_btn.clicked.connect(lambda: self._add_element('LINE'))
        layout.addWidget(line_btn)
        
        # Dikdörtgen ekle
        rect_btn = QPushButton("⬜  Dikdörtgen Ekle")
        rect_btn.setCursor(Qt.PointingHandCursor)
        rect_btn.setStyleSheet(btn_style)
        rect_btn.clicked.connect(lambda: self._add_element('RECT'))
        layout.addWidget(rect_btn)
        
        layout.addStretch()
        
        # Seçili elementi sil
        delete_elem_btn = QPushButton("🗑️ Seçili Elementi Sil")
        delete_elem_btn.setCursor(Qt.PointingHandCursor)
        delete_elem_btn.setStyleSheet(f"""
            QPushButton {{ background: #dc2626; color: white; 
                          border: none; border-radius: 6px; padding: 10px; }}
            QPushButton:hover {{ background: #b91c1c; }}
        """)
        delete_elem_btn.clicked.connect(self._delete_element)
        layout.addWidget(delete_elem_btn)
        
        return frame
    
    def _create_center_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border-radius: 8px; }}")
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Başlık ve boyut ayarları
        top_bar = QHBoxLayout()
        
        lbl = QLabel("🎨 Tasarım Alanı")
        lbl.setStyleSheet(f"color: {brand.TEXT}; font-weight: bold; font-size: 14px;")
        top_bar.addWidget(lbl)
        
        top_bar.addStretch()
        
        spin_style = f"background: {brand.BG_INPUT}; color: {brand.TEXT}; border: 1px solid {brand.BORDER}; border-radius: 4px; padding: 4px;"
        
        top_bar.addWidget(QLabel("Genişlik:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(20, 300)
        self.width_spin.setValue(100)
        self.width_spin.setSuffix(" mm")
        self.width_spin.setStyleSheet(spin_style)
        self.width_spin.valueChanged.connect(self._on_size_changed)
        top_bar.addWidget(self.width_spin)
        
        top_bar.addWidget(QLabel("Yükseklik:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(20, 200)
        self.height_spin.setValue(50)
        self.height_spin.setSuffix(" mm")
        self.height_spin.setStyleSheet(spin_style)
        self.height_spin.valueChanged.connect(self._on_size_changed)
        top_bar.addWidget(self.height_spin)
        
        layout.addLayout(top_bar)
        
        # Tasarım görünümü
        self.design_view = EtiketGraphicsView(self.theme)
        layout.addWidget(self.design_view, 1)
        
        # Alt bilgi
        info = QLabel("💡 Elementleri sürükleyerek konumlandırın • Delete tuşu ile silin")
        info.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px;")
        layout.addWidget(info)
        
        return frame
    
    def _create_right_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border-radius: 8px; }}")
        frame.setMinimumWidth(280)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        lbl = QLabel("⚙️ Şablon Özellikleri")
        lbl.setStyleSheet(f"color: {brand.TEXT}; font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl)
        
        input_style = f"""
            background: {brand.BG_INPUT}; 
            color: {brand.TEXT}; 
            border: 1px solid {brand.BORDER}; 
            border-radius: 6px; padding: 8px;
        """
        
        # Şablon kodu
        layout.addWidget(QLabel("Şablon Kodu:"))
        self.sablon_kodu_input = QLineEdit()
        self.sablon_kodu_input.setPlaceholderText("Örn: PALET_100x50")
        self.sablon_kodu_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        layout.addWidget(self.sablon_kodu_input)
        
        # Şablon adı
        layout.addWidget(QLabel("Şablon Adı:"))
        self.sablon_adi_input = QLineEdit()
        self.sablon_adi_input.setPlaceholderText("Örn: Standart Palet Etiketi")
        self.sablon_adi_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        layout.addWidget(self.sablon_adi_input)
        
        # Şablon tipi
        layout.addWidget(QLabel("Etiket Tipi:"))
        self.sablon_tipi_combo = QComboBox()
        self.sablon_tipi_combo.addItems(["PALET", "URUN", "KUTU", "SEVKIYAT"])
        self.sablon_tipi_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        layout.addWidget(self.sablon_tipi_combo)
        
        # Açıklama
        layout.addWidget(QLabel("Açıklama:"))
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setMaximumHeight(60)
        self.aciklama_input.setStyleSheet(f"QTextEdit {{ {input_style} }}")
        layout.addWidget(self.aciklama_input)
        
        # A4 Çoklu Etiket Modu checkbox
        self.a4_mode_check = QCheckBox("📄 A4 Sayfa Düzeni (çoklu etiket)")
        self.a4_mode_check.setStyleSheet(f"color: {brand.TEXT}; font-weight: bold;")
        self.a4_mode_check.setChecked(False)  # Varsayılan: tek etiket modu
        self.a4_mode_check.stateChanged.connect(self._on_a4_mode_changed)
        layout.addWidget(self.a4_mode_check)
        
        # Sayfa düzeni (A4 modu için)
        self.sayfa_duzen_widget = QWidget()
        sayfa_layout = QHBoxLayout(self.sayfa_duzen_widget)
        sayfa_layout.setContentsMargins(20, 0, 0, 0)
        spin_style_small = f"background: {brand.BG_INPUT}; color: {brand.TEXT}; border: 1px solid {brand.BORDER}; border-radius: 4px; padding: 4px;"
        
        sayfa_layout.addWidget(QLabel("Sütun:"))
        self.sutun_spin = QSpinBox()
        self.sutun_spin.setRange(1, 5)
        self.sutun_spin.setValue(2)
        self.sutun_spin.setStyleSheet(spin_style_small)
        sayfa_layout.addWidget(self.sutun_spin)
        
        sayfa_layout.addWidget(QLabel("Satır:"))
        self.satir_spin = QSpinBox()
        self.satir_spin.setRange(1, 10)
        self.satir_spin.setValue(5)
        self.satir_spin.setStyleSheet(spin_style_small)
        sayfa_layout.addWidget(self.satir_spin)
        
        layout.addWidget(self.sayfa_duzen_widget)
        self.sayfa_duzen_widget.setVisible(False)  # Başlangıçta gizli
        
        # Varsayılan
        self.varsayilan_check = QCheckBox("Varsayılan şablon olarak ayarla")
        self.varsayilan_check.setStyleSheet(f"color: {brand.TEXT};")
        layout.addWidget(self.varsayilan_check)
        
        layout.addStretch()
        
        # Kullanılabilir alanlar
        layout.addWidget(QLabel("📋 Kullanılabilir Alanlar:"))
        
        alanlar_text = QLabel(
            "{lot_no} - Lot numarası\n"
            "{stok_kodu} - Stok kodu\n"
            "{stok_adi} - Stok adı\n"
            "{musteri} - Müşteri adı\n"
            "{kaplama} - Kaplama tipi\n"
            "{miktar} - Miktar\n"
            "{birim} - Birim\n"
            "{palet_no} - Palet no\n"
            "{toplam_palet} - Toplam palet\n"
            "{irsaliye_no} - İrsaliye no\n"
            "{tarih} - Tarih"
        )
        alanlar_text.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px; font-family: monospace;")
        alanlar_text.setWordWrap(True)
        layout.addWidget(alanlar_text)
        
        return frame
    
    def _add_element(self, element_type: str):
        """Element ekleme dialogunu aç"""
        dialog = ElementEkleDialog(element_type, self.theme, self)
        if dialog.exec() == QDialog.Accepted and dialog.result_data:
            self.design_view.add_element(dialog.result_data)
    
    def _delete_element(self):
        """Seçili elementi sil"""
        self.design_view.delete_selected()
    
    def _on_size_changed(self):
        self.design_view.set_etiket_boyut(
            self.width_spin.value(),
            self.height_spin.value()
        )
    
    def _on_a4_mode_changed(self, state):
        """A4 modu değiştiğinde"""
        a4_mode = state == Qt.Checked
        self.sayfa_duzen_widget.setVisible(a4_mode)
        
        if not a4_mode:
            # Tek etiket modu: 1x1
            self.sutun_spin.setValue(1)
            self.satir_spin.setValue(1)
    
    def _load_sablonlar(self):
        self.sablon_list.clear()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, sablon_kodu, sablon_adi, sablon_tipi, varsayilan_mi
                FROM tanim.etiket_sablonlari
                WHERE aktif_mi = 1
                ORDER BY sablon_tipi, sablon_adi
            """)
            
            for row in cursor.fetchall():
                item = QListWidgetItem()
                varsayilan = "⭐ " if row[4] else ""
                item.setText(f"{varsayilan}[{row[3]}] {row[2]}")
                item.setData(Qt.UserRole, row[0])
                item.setData(Qt.UserRole + 1, row[1])
                self.sablon_list.addItem(item)
            
            conn.close()
            
        except Exception as e:
            print(f"Şablon yükleme hatası: {e}")
    
    def _on_sablon_selected(self, item: QListWidgetItem):
        sablon_id = item.data(Qt.UserRole)
        self.current_sablon_id = sablon_id
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sablon_kodu, sablon_adi, sablon_tipi, aciklama,
                       genislik_mm, yukseklik_mm, sayfa_sutun, sayfa_satir,
                       tasarim_json, varsayilan_mi
                FROM tanim.etiket_sablonlari
                WHERE id = ?
            """, (sablon_id,))
            
            row = cursor.fetchone()
            if row:
                self.sablon_kodu_input.setText(row[0] or '')
                self.sablon_adi_input.setText(row[1] or '')
                
                idx = self.sablon_tipi_combo.findText(row[2] or 'PALET')
                if idx >= 0:
                    self.sablon_tipi_combo.setCurrentIndex(idx)
                
                self.aciklama_input.setPlainText(row[3] or '')
                self.width_spin.setValue(int(float(row[4])) if row[4] else 100)
                self.height_spin.setValue(int(float(row[5])) if row[5] else 50)
                
                # Sütun/Satır değerlerini al
                sutun = int(row[6]) if row[6] else 1
                satir = int(row[7]) if row[7] else 1
                self.sutun_spin.setValue(sutun)
                self.satir_spin.setValue(satir)
                
                # A4 modu: sütun>1 veya satır>1 ise A4 modu aktif
                a4_mode = (sutun > 1 or satir > 1)
                self.a4_mode_check.setChecked(a4_mode)
                self.sayfa_duzen_widget.setVisible(a4_mode)
                
                self.varsayilan_check.setChecked(bool(row[9]))
                
                # Tasarımı yükle
                w = float(row[4]) if row[4] else 100
                h = float(row[5]) if row[5] else 50
                self.design_view.set_etiket_boyut(w, h)
                
                if row[8]:
                    self.design_view.load_from_json(row[8])
            
            conn.close()
            
        except Exception as e:
            print(f"Şablon detay yükleme hatası: {e}")
    
    def _new_sablon(self):
        self.current_sablon_id = None
        self.sablon_kodu_input.clear()
        self.sablon_adi_input.clear()
        self.sablon_tipi_combo.setCurrentIndex(0)
        self.aciklama_input.clear()
        self.width_spin.setValue(100)
        self.height_spin.setValue(50)
        
        # Tek etiket modu varsayılan
        self.a4_mode_check.setChecked(False)
        self.sayfa_duzen_widget.setVisible(False)
        self.sutun_spin.setValue(1)
        self.satir_spin.setValue(1)
        
        self.varsayilan_check.setChecked(False)
        
        self.design_view.set_etiket_boyut(100, 50)
        self.design_view.load_from_json('{"elements": []}')  # Boş tasarım
        self.sablon_kodu_input.setFocus()
    
    def _save_sablon(self):
        sablon_kodu = self.sablon_kodu_input.text().strip()
        sablon_adi = self.sablon_adi_input.text().strip()
        
        if not sablon_kodu or not sablon_adi:
            QMessageBox.warning(self, "Uyarı", "Şablon kodu ve adı zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            tasarim_json = self.design_view.export_to_json()
            
            if self.current_sablon_id:
                cursor.execute("""
                    UPDATE tanim.etiket_sablonlari SET
                        sablon_kodu = ?, sablon_adi = ?, sablon_tipi = ?, aciklama = ?,
                        genislik_mm = ?, yukseklik_mm = ?, sayfa_sutun = ?, sayfa_satir = ?,
                        tasarim_json = ?, varsayilan_mi = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    sablon_kodu, sablon_adi, self.sablon_tipi_combo.currentText(),
                    self.aciklama_input.toPlainText(), self.width_spin.value(),
                    self.height_spin.value(), self.sutun_spin.value(), self.satir_spin.value(),
                    tasarim_json, self.varsayilan_check.isChecked(), self.current_sablon_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO tanim.etiket_sablonlari 
                    (sablon_kodu, sablon_adi, sablon_tipi, aciklama, genislik_mm, yukseklik_mm,
                     sayfa_sutun, sayfa_satir, tasarim_json, varsayilan_mi, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    sablon_kodu, sablon_adi, self.sablon_tipi_combo.currentText(),
                    self.aciklama_input.toPlainText(), self.width_spin.value(),
                    self.height_spin.value(), self.sutun_spin.value(), self.satir_spin.value(),
                    tasarim_json, self.varsayilan_check.isChecked()
                ))
                
                cursor.execute("SELECT @@IDENTITY")
                self.current_sablon_id = cursor.fetchone()[0]
            
            if self.varsayilan_check.isChecked():
                cursor.execute("""
                    UPDATE tanim.etiket_sablonlari 
                    SET varsayilan_mi = 0 
                    WHERE sablon_tipi = ? AND id != ?
                """, (self.sablon_tipi_combo.currentText(), self.current_sablon_id))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Başarılı", "Şablon kaydedildi!")
            self._load_sablonlar()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
    
    def _delete_sablon(self):
        if not self.current_sablon_id:
            QMessageBox.warning(self, "Uyarı", "Silinecek şablon seçin!")
            return
        
        reply = QMessageBox.question(
            self, "Onay", 
            "Şablonu silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE tanim.etiket_sablonlari SET aktif_mi = 0 WHERE id = ?
            """, (self.current_sablon_id,))
            
            conn.commit()
            conn.close()
            
            self.current_sablon_id = None
            self._new_sablon()
            self._load_sablonlar()
            
            QMessageBox.information(self, "Başarılı", "Şablon silindi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
    
    def _preview_etiket(self):
        """Etiket önizleme - tanımlanan boyutlarda PDF oluştur"""
        import tempfile
        import subprocess
        
        try:
            # Şablon boyutları
            etiket_w_mm = self.width_spin.value()
            etiket_h_mm = self.height_spin.value()
            
            # Test verisi oluştur
            from datetime import datetime
            test_etiket = {
                'stok_kodu': 'TEST-001',
                'stok_adi': 'Test Ürün Adı',
                'musteri': 'Test Müşteri A.Ş.',
                'kaplama': 'KATAFOREZ',
                'miktar': 1000,
                'birim': 'ADET',
                'palet_no': 1,
                'toplam_palet': 5,
                'lot_no': 'LOT-2501-0001-01',
                'parent_lot_no': 'LOT-2501-0001',
                'irsaliye_no': 'GRS-202501-0001',
                'tarih': datetime.now(),
                'resim_path': None
            }
            
            # Tasarım JSON'ını al
            tasarim_json = self.design_view.export_to_json()
            
            # Geçici PDF dosyası
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='etiket_onizle_')
            temp_path = temp_file.name
            temp_file.close()
            
            # PDF oluştur - tanımlanan boyutlarda
            self._create_preview_pdf(temp_path, test_etiket, tasarim_json, etiket_w_mm, etiket_h_mm)
            
            # PDF'i aç
            subprocess.Popen(['start', '', temp_path], shell=True)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Önizleme hatası:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _create_preview_pdf(self, output_path: str, etiket: dict, tasarim_json: str, 
                            etiket_w_mm: float, etiket_h_mm: float):
        """Tanımlanan boyutlarda tek etiket PDF'i oluştur"""
        from reportlab.lib.units import mm as mm_unit
        from reportlab.pdfgen import canvas
        from reportlab.graphics.barcode import code128
        import json
        import os
        
        # Sayfa boyutu = etiket boyutu
        page_w = etiket_w_mm * mm_unit
        page_h = etiket_h_mm * mm_unit
        
        c = canvas.Canvas(output_path, pagesize=(page_w, page_h))
        
        # JSON'dan elementleri parse et
        try:
            tasarim = json.loads(tasarim_json)
            elements = tasarim.get('elements', [])
        except Exception:
            elements = []
        
        # Her elementi çiz
        for elem in elements:
            elem_type = elem.get('type', 'TEXT').upper()
            x_mm = elem.get('x', 0)
            y_mm = elem.get('y', 0)
            
            # PDF koordinatları (sol alt köşe 0,0)
            x = x_mm * mm_unit
            y = page_h - y_mm * mm_unit  # Y koordinatını çevir
            
            try:
                if elem_type == 'TEXT':
                    self._draw_text_element(c, elem, etiket, x, y)
                elif elem_type == 'BARCODE':
                    self._draw_barcode_element(c, elem, etiket, x, y)
                elif elem_type == 'IMAGE':
                    self._draw_image_element(c, elem, etiket, x, y)
                elif elem_type == 'LINE':
                    self._draw_line_element(c, elem, x, y, mm_unit)
                elif elem_type in ('RECT', 'RECTANGLE'):
                    self._draw_rect_element(c, elem, x, y, mm_unit)
            except Exception as e:
                print(f"Element çizim hatası: {e}")
        
        # Element yoksa varsayılan etiket çiz
        if not elements:
            self._draw_default_label(c, etiket, page_w, page_h, mm_unit)
        
        c.save()
        print(f"Önizleme PDF oluşturuldu: {output_path} ({etiket_w_mm}x{etiket_h_mm}mm)")
    
    def _draw_text_element(self, c, elem: dict, etiket: dict, x: float, y: float):
        """Metin elementi çiz"""
        from reportlab.lib.units import mm as mm_unit
        
        text = elem.get('text', '')
        
        # Veri alanı ise değeri al
        if text.startswith('{') and text.endswith('}'):
            field = text[1:-1]
            text = self._get_field_value(field, etiket)
        
        if not text:
            return
        
        font = elem.get('font', 'Helvetica')
        size = elem.get('size', 10)
        
        try:
            c.setFont(font, size)
        except Exception:
            c.setFont('Helvetica', size)
        
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x, y - size, str(text))
    
    def _draw_barcode_element(self, c, elem: dict, etiket: dict, x: float, y: float):
        """Barkod elementi çiz"""
        from reportlab.lib.units import mm as mm_unit
        from reportlab.graphics.barcode import code128
        
        field = elem.get('field', 'lot_no')
        if field.startswith('{') and field.endswith('}'):
            field = field[1:-1]
        
        barcode_data = self._get_field_value(field, etiket)
        if not barcode_data:
            barcode_data = 'TEST-BARCODE'
        
        height = elem.get('height', 8) * mm_unit
        
        try:
            barcode = code128.Code128(str(barcode_data), barWidth=0.35 * mm_unit, barHeight=height)
            barcode.drawOn(c, x, y - height - 10)
        except Exception as e:
            print(f"Barkod hatası: {e}")
            c.setFont("Helvetica", 8)
            c.drawString(x, y - 15, f"*{barcode_data}*")
    
    def _draw_image_element(self, c, elem: dict, etiket: dict, x: float, y: float):
        """Resim elementi çiz (placeholder)"""
        from reportlab.lib.units import mm as mm_unit
        
        w = elem.get('width', 20) * mm_unit
        h = elem.get('height', 20) * mm_unit
        
        resim_path = etiket.get('resim_path')
        if resim_path and os.path.exists(resim_path):
            try:
                c.drawImage(resim_path, x, y - h, width=w, height=h, preserveAspectRatio=True)
                return
            except Exception:
                pass
        
        # Placeholder çiz
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.rect(x, y - h, w, h)
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(x + w/2, y - h/2, "Resim")
    
    def _draw_line_element(self, c, elem: dict, x: float, y: float, mm_unit: float):
        """Çizgi elementi çiz"""
        x2 = elem.get('x2', elem.get('x', 0) + 50) * mm_unit
        y2_mm = elem.get('y2', elem.get('y', 0))
        
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.line(x, y, x2, y - (y2_mm - elem.get('y', 0)) * mm_unit)
    
    def _draw_rect_element(self, c, elem: dict, x: float, y: float, mm_unit: float):
        """Dikdörtgen elementi çiz"""
        w = elem.get('width', 30) * mm_unit
        h = elem.get('height', 15) * mm_unit
        
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.rect(x, y - h, w, h)
    
    def _draw_default_label(self, c, etiket: dict, page_w: float, page_h: float, mm_unit: float):
        """Varsayılan etiket içeriği çiz"""
        margin = 3 * mm_unit
        
        # Başlık
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margin, page_h - 6 * mm_unit, "ATMO MANUFACTURING")
        
        c.setFont("Helvetica", 7)
        c.drawRightString(page_w - margin, page_h - 6 * mm_unit, etiket.get('irsaliye_no', ''))
        
        # Çizgi
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.line(margin, page_h - 8 * mm_unit, page_w - margin, page_h - 8 * mm_unit)
        
        # Stok Kodu
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin + 25 * mm_unit, page_h - 14 * mm_unit, str(etiket.get('stok_kodu', ''))[:20])
        
        # Stok Adı
        c.setFont("Helvetica", 8)
        c.drawString(margin + 25 * mm_unit, page_h - 19 * mm_unit, str(etiket.get('stok_adi', ''))[:35])
        
        # Müşteri
        c.setFont("Helvetica", 7)
        c.drawString(margin + 25 * mm_unit, page_h - 23 * mm_unit, f"MÜŞ: {str(etiket.get('musteri', ''))[:28]}")
        
        # Kaplama
        c.drawString(margin + 25 * mm_unit, page_h - 27 * mm_unit, f"KAP: {etiket.get('kaplama', '')}")
        
        # Miktar ve Palet
        c.setFont("Helvetica-Bold", 9)
        miktar = etiket.get('miktar', 0)
        birim = etiket.get('birim', 'ADET')
        c.drawString(margin + 25 * mm_unit, page_h - 33 * mm_unit, f"MİKTAR: {miktar:,.0f} {birim}")
        
        palet_no = etiket.get('palet_no', 1)
        toplam = etiket.get('toplam_palet', 1)
        c.drawString(margin + 65 * mm_unit, page_h - 33 * mm_unit, f"P: {palet_no:02d}/{toplam:02d}")
        
        # Lot No
        c.drawString(margin + 25 * mm_unit, page_h - 38 * mm_unit, f"LOT: {etiket.get('lot_no', '')}")
        
        # Barkod
        try:
            from reportlab.graphics.barcode import code128
            lot_no = etiket.get('lot_no', 'TEST')
            barcode = code128.Code128(lot_no, barWidth=0.35 * mm_unit, barHeight=8 * mm_unit)
            barcode.drawOn(c, margin, 3 * mm_unit)
        except Exception:
            pass
        
        # Tarih
        c.setFont("Helvetica", 7)
        tarih = etiket.get('tarih')
        if tarih:
            tarih_str = tarih.strftime('%d.%m.%Y') if hasattr(tarih, 'strftime') else str(tarih)[:10]
            c.drawRightString(page_w - margin, 4 * mm_unit, tarih_str)
    
    def _get_field_value(self, field: str, etiket: dict) -> str:
        """Veri alanı değerini al"""
        field_map = {
            'lot_no': etiket.get('lot_no', ''),
            'stok_kodu': etiket.get('stok_kodu', ''),
            'stok_adi': etiket.get('stok_adi', ''),
            'musteri': etiket.get('musteri', ''),
            'kaplama': etiket.get('kaplama', ''),
            'miktar': f"{etiket.get('miktar', 0):,.0f}",
            'birim': etiket.get('birim', 'ADET'),
            'palet_no': str(etiket.get('palet_no', '')),
            'toplam_palet': str(etiket.get('toplam_palet', '')),
            'irsaliye_no': etiket.get('irsaliye_no', ''),
            'tarih': etiket.get('tarih').strftime('%d.%m.%Y') if etiket.get('tarih') and hasattr(etiket.get('tarih'), 'strftime') else '',
            'parent_lot_no': etiket.get('parent_lot_no', ''),
        }
        return str(field_map.get(field, ''))
    
    def _test_yazdir(self):
        """Test yazdırma - yazıcı seçimi ile"""
        try:
            from utils.etiket_yazdir import get_available_printers, get_godex_printers
            
            printers = get_available_printers()
            godex_printers = get_godex_printers()
            
            if not printers:
                QMessageBox.warning(self, "Uyarı", "Yazıcı bulunamadı!")
                return
            
            # Yazıcı seçim dialogu
            from PySide6.QtWidgets import QInputDialog
            
            # Godex yazıcıları öne al
            sorted_printers = godex_printers + [p for p in printers if p not in godex_printers]
            
            printer, ok = QInputDialog.getItem(
                self,
                "Yazıcı Seç",
                "Test yazdırma için yazıcı seçin:",
                sorted_printers,
                0,
                False
            )
            
            if not ok or not printer:
                return
            
            # Şablon boyutları
            etiket_w_mm = self.width_spin.value()
            etiket_h_mm = self.height_spin.value()
            
            # Test verisi
            from datetime import datetime
            test_etiket = {
                'stok_kodu': 'TEST-001',
                'stok_adi': 'Test Ürün Adı',
                'musteri': 'Test Müşteri A.Ş.',
                'kaplama': 'KATAFOREZ',
                'miktar': 1000,
                'birim': 'ADET',
                'palet_no': 1,
                'toplam_palet': 5,
                'lot_no': 'LOT-2501-0001-01',
                'parent_lot_no': 'LOT-2501-0001',
                'irsaliye_no': 'GRS-202501-TEST',
                'tarih': datetime.now(),
                'resim_path': None
            }
            
            # Godex yazıcı mı kontrol et
            is_godex = any(g in printer.upper() for g in ['GODEX', 'G500', 'G530'])
            
            if is_godex:
                # Godex direkt yazdırma
                from utils.etiket_yazdir import godex_yazdir
                success = godex_yazdir([test_etiket], printer, "ZPL")
                if success:
                    QMessageBox.information(self, "Başarılı", f"Test etiketi yazıcıya gönderildi:\n{printer}")
                else:
                    QMessageBox.warning(self, "Uyarı", "Yazdırma başarısız oldu!")
            else:
                # PDF oluştur ve yazdır
                import tempfile
                from utils.etiket_yazdir import pdf_yazdir
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='test_etiket_')
                temp_path = temp_file.name
                temp_file.close()
                
                tasarim_json = self.design_view.export_to_json()
                self._create_preview_pdf(temp_path, test_etiket, tasarim_json, etiket_w_mm, etiket_h_mm)
                
                success = pdf_yazdir(temp_path, printer)
                if success:
                    QMessageBox.information(self, "Başarılı", f"Test etiketi yazıcıya gönderildi:\n{printer}")
                else:
                    # PDF'i aç
                    import subprocess
                    subprocess.Popen(['start', '', temp_path], shell=True)
                    QMessageBox.information(self, "Bilgi", "PDF dosyası açıldı.")
                    
        except ImportError as e:
            QMessageBox.warning(self, "Uyarı", f"Modül eksik: {e}\npip install pywin32")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Test yazdırma hatası:\n{str(e)}")
            import traceback
            traceback.print_exc()
