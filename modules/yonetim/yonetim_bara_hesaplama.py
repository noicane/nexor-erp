# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - KTL Bara Hesaplama Modülü
Yönetim > Bara Hesaplama

4 Aşama: Parça & Maliyet, Askı Montajı, Bara Dizilimi, Banyo Simülasyonu
"""

import os
os.environ["QT_API"] = "pyside6"
os.environ["VTK_SILENCE_GET_VOID_POINTER_WARNINGS"] = "1"

import numpy as np

try:
    import trimesh
    import pyvista as pv
    from pyvistaqt import QtInteractor
    HAS_PYVISTA = True
except ImportError:
    HAS_PYVISTA = False

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QLabel,
    QPushButton, QLineEdit, QDoubleSpinBox, QSpinBox, QSlider,
    QScrollArea, QFileDialog, QMessageBox, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QTimer

from components.base_page import BasePage


class SharedData:
    def __init__(self):
        self.part_mesh = None
        self.part_poly = None
        self.hanger_poly = None
        self.rack_poly = None
        self.bath_poly = None
        self.part_area_m2 = 0.0
        self.unit_cost = 0.0
        self.parts_per_hanger = 0
        self.hangers_on_rack = 0
        self.locked_assembly = None
        self.full_rack_assembly = None

DATA = SharedData()
COLOR_BG = "#0f172a"
COLOR_PART = "orange"
COLOR_HANGER = "silver"
COLOR_RACK = "#555555"
COLOR_BATH = "#00FFFF"


def create_styled_btn(text, callback, theme, primary=True):
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumHeight(40)
    if primary:
        btn.setStyleSheet(f"QPushButton {{ background: {theme['gradient_css']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: bold; }} QPushButton:hover {{ background: {theme['gradient_start']}; }}")
    btn.clicked.connect(callback)
    return btn


def create_group_box(title, theme):
    grp = QGroupBox(title)
    grp.setStyleSheet(f"""
        QGroupBox {{ background: {theme['bg_card']}; border: 1px solid {theme['border']}; border-radius: 12px; margin-top: 20px; padding: 16px; padding-top: 28px; font-weight: bold; color: {theme['text']}; }}
        QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: 16px; top: 8px; padding: 0 8px; color: {theme['text']}; background: {theme['bg_card']}; }}
    """)
    return grp


def create_control_row(label, mn, mx, default, callback, theme):
    layout = QHBoxLayout()
    layout.setSpacing(12)
    lbl = QLabel(f"{label}:")
    lbl.setFixedWidth(80)
    lbl.setStyleSheet(f"color: {theme['text_secondary']}; font-weight: 600;")
    slider = QSlider(Qt.Horizontal)
    slider.setRange(mn, mx)
    slider.setValue(default)
    slider.setStyleSheet(f"QSlider::groove:horizontal {{ height: 6px; background: {theme['border']}; border-radius: 3px; }} QSlider::handle:horizontal {{ background: {theme['primary']}; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }}")
    spin = QDoubleSpinBox()
    spin.setRange(mn, mx)
    spin.setValue(default)
    spin.setDecimals(1)
    spin.setFixedWidth(90)
    spin.setStyleSheet(f"QDoubleSpinBox {{ background: {theme['bg_input']}; color: {theme['text']}; border: 1px solid {theme['border']}; border-radius: 6px; padding: 6px; }}")
    slider.valueChanged.connect(lambda v: spin.setValue(v))
    spin.valueChanged.connect(lambda v: slider.setValue(int(v)))
    slider.valueChanged.connect(callback)
    layout.addWidget(lbl)
    layout.addWidget(slider, 1)
    layout.addWidget(spin)
    return layout, spin


def input_style(theme):
    return f"QLineEdit, QSpinBox, QDoubleSpinBox {{ background: {theme['bg_input']}; color: {theme['text']}; border: 1px solid {theme['border']}; border-radius: 6px; padding: 8px; }}"


class TabPart(QWidget):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(360)
        left_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setSpacing(16)
        
        grp_load = create_group_box("1. Parça Yükle", self.theme)
        QVBoxLayout(grp_load).addWidget(create_styled_btn("📁 STL PARÇA YÜKLE", self._load_part, self.theme))
        left_layout.addWidget(grp_load)
        
        grp_info = create_group_box("2. Parça Bilgileri", self.theme)
        info_layout = QGridLayout(grp_info)
        info_layout.setSpacing(10)
        lbl_s = f"color: {self.theme['text_secondary']};"
        info_layout.addWidget(QLabel("Parça Adı:", styleSheet=lbl_s), 0, 0)
        self.ed_name = QLineEdit()
        self.ed_name.setStyleSheet(input_style(self.theme))
        info_layout.addWidget(self.ed_name, 0, 1)
        self.lbl_area = QLabel("Yüzey Alanı: - m²")
        self.lbl_area.setStyleSheet(f"color: {self.theme['primary']}; font-weight: bold; margin-top: 8px;")
        info_layout.addWidget(self.lbl_area, 1, 0, 1, 2)
        left_layout.addWidget(grp_info)
        
        grp_cost = create_group_box("3. Birim Maliyet", self.theme)
        cost_layout = QVBoxLayout(grp_cost)
        cost_row = QHBoxLayout()
        cost_row.addWidget(QLabel("₺/m²:", styleSheet=lbl_s))
        self.sp_cost = QDoubleSpinBox()
        self.sp_cost.setRange(0, 99999)
        self.sp_cost.setValue(50)
        self.sp_cost.setStyleSheet(input_style(self.theme))
        self.sp_cost.valueChanged.connect(self._update_cost)
        cost_row.addWidget(self.sp_cost)
        cost_layout.addLayout(cost_row)
        self.lbl_unit_cost = QLabel("Parça Maliyeti: 0.00 ₺")
        self.lbl_unit_cost.setStyleSheet(f"color: {self.theme['success']}; font-size: 16px; font-weight: bold;")
        cost_layout.addWidget(self.lbl_unit_cost)
        left_layout.addWidget(grp_cost)
        left_layout.addStretch()
        left_scroll.setWidget(left_content)
        layout.addWidget(left_scroll)
        
        if HAS_PYVISTA:
            self.plotter = QtInteractor(self)
            self.plotter.set_background(COLOR_BG)
            layout.addWidget(self.plotter, 1)
        else:
            lbl = QLabel("⚠️ PyVista yüklü değil")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {self.theme['warning']};")
            layout.addWidget(lbl, 1)
    
    def _load_part(self):
        if not HAS_PYVISTA: return
        fname, _ = QFileDialog.getOpenFileName(self, "STL Seç", "", "STL (*.stl)")
        if not fname: return
        try:
            DATA.part_mesh = trimesh.load(fname)
            DATA.part_poly = pv.read(fname)
            c = DATA.part_poly.center
            DATA.part_poly.translate([-c[0], -c[1], -c[2]], inplace=True)
            DATA.part_area_m2 = DATA.part_mesh.area / 1e6
            self.ed_name.setText(os.path.basename(fname).replace(".stl", ""))
            self.lbl_area.setText(f"Yüzey Alanı: {DATA.part_area_m2:.6f} m²")
            self._update_cost()
            self.plotter.clear()
            self.plotter.add_mesh(DATA.part_poly, color=COLOR_PART, smooth_shading=True)
            self.plotter.reset_camera()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _update_cost(self):
        DATA.unit_cost = DATA.part_area_m2 * self.sp_cost.value()
        self.lbl_unit_cost.setText(f"Parça Maliyeti: {DATA.unit_cost:,.2f} ₺")
    
    def close_renderer(self):
        if HAS_PYVISTA:
            try: self.plotter.close()
            except: pass


class TabHanger(QWidget):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(50)
        self.update_timer.timeout.connect(self._perform_update)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(360)
        left_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setSpacing(16)
        
        grp_load = create_group_box("1. Askı Yükle", self.theme)
        QVBoxLayout(grp_load).addWidget(create_styled_btn("📁 ASKI STL YÜKLE", self._load_hanger, self.theme))
        left_layout.addWidget(grp_load)
        
        grp_pos = create_group_box("2. Parça Konumu (İnce Ayar)", self.theme)
        pos_layout = QVBoxLayout(grp_pos)
        self.inputs = {}
        for label, mn, mx, val in [("X Konum", -500, 500, 0), ("Y Konum", -500, 500, 0), ("Z Konum", -500, 500, 100), ("Rot X", -180, 180, 0), ("Rot Y", -180, 180, 0), ("Rot Z", -180, 180, 0)]:
            row, spin = create_control_row(label, mn, mx, val, self._schedule_update, self.theme)
            pos_layout.addLayout(row)
            self.inputs[label] = spin
        left_layout.addWidget(grp_pos)
        
        grp_mult = create_group_box("3. Parça Çoklama", self.theme)
        mult_layout = QGridLayout(grp_mult)
        lbl_s = f"color: {self.theme['text_secondary']};"
        mult_layout.addWidget(QLabel("Adet:", styleSheet=lbl_s), 0, 0)
        self.sp_count = QSpinBox()
        self.sp_count.setRange(1, 50)
        self.sp_count.setValue(4)
        self.sp_count.setStyleSheet(input_style(self.theme))
        self.sp_count.valueChanged.connect(self._schedule_update)
        mult_layout.addWidget(self.sp_count, 0, 1)
        mult_layout.addWidget(QLabel("Mesafe (mm):", styleSheet=lbl_s), 1, 0)
        self.sp_dist = QSpinBox()
        self.sp_dist.setRange(10, 500)
        self.sp_dist.setValue(80)
        self.sp_dist.setStyleSheet(input_style(self.theme))
        self.sp_dist.valueChanged.connect(self._schedule_update)
        mult_layout.addWidget(self.sp_dist, 1, 1)
        left_layout.addWidget(grp_mult)
        
        grp_save = create_group_box("4. Montajı Kaydet", self.theme)
        QVBoxLayout(grp_save).addWidget(create_styled_btn("💾 MONTAJI KİLİTLE", self._lock_assembly, self.theme))
        left_layout.addWidget(grp_save)
        
        left_layout.addStretch()
        left_scroll.setWidget(left_content)
        layout.addWidget(left_scroll)
        
        if HAS_PYVISTA:
            self.plotter = QtInteractor(self)
            self.plotter.set_background(COLOR_BG)
            layout.addWidget(self.plotter, 1)
        else:
            layout.addWidget(QLabel("PyVista yüklü değil"), 1)
    
    def _load_hanger(self):
        if not HAS_PYVISTA: return
        fname, _ = QFileDialog.getOpenFileName(self, "Askı Seç", "", "STL (*.stl)")
        if fname:
            DATA.hanger_poly = pv.read(fname)
            c = DATA.hanger_poly.center
            DATA.hanger_poly.translate([-c[0], -c[1], -c[2]], inplace=True)
            self._schedule_update()
    
    def _schedule_update(self): self.update_timer.start()
    
    def _perform_update(self):
        if not HAS_PYVISTA: return
        self.plotter.clear()
        if DATA.hanger_poly: self.plotter.add_mesh(DATA.hanger_poly, color=COLOR_HANGER)
        if DATA.part_poly:
            base = DATA.part_poly.copy()
            base.rotate_x(self.inputs["Rot X"].value(), inplace=True)
            base.rotate_y(self.inputs["Rot Y"].value(), inplace=True)
            base.rotate_z(self.inputs["Rot Z"].value(), inplace=True)
            sx, sy, sz = self.inputs["X Konum"].value(), self.inputs["Y Konum"].value(), self.inputs["Z Konum"].value()
            for i in range(self.sp_count.value()):
                inst = base.copy()
                inst.translate([sx + (i * self.sp_dist.value()), sy, sz], inplace=True)
                self.plotter.add_mesh(inst, color=COLOR_PART, smooth_shading=True)
            DATA.parts_per_hanger = self.sp_count.value()
    
    def _lock_assembly(self):
        if not HAS_PYVISTA or not DATA.hanger_poly:
            QMessageBox.warning(self, "Uyarı", "Önce askı yükleyin!")
            return
        meshes = [DATA.hanger_poly.copy()]
        if DATA.part_poly:
            base = DATA.part_poly.copy()
            base.rotate_x(self.inputs["Rot X"].value(), inplace=True)
            base.rotate_y(self.inputs["Rot Y"].value(), inplace=True)
            base.rotate_z(self.inputs["Rot Z"].value(), inplace=True)
            for i in range(self.sp_count.value()):
                inst = base.copy()
                inst.translate([self.inputs["X Konum"].value() + (i * self.sp_dist.value()), self.inputs["Y Konum"].value(), self.inputs["Z Konum"].value()], inplace=True)
                meshes.append(inst)
        DATA.locked_assembly = meshes[0].merge(meshes[1:]) if len(meshes) > 1 else meshes[0]
        QMessageBox.information(self, "Başarılı", "Askı montajı kilitlendi!")
    
    def close_renderer(self):
        if HAS_PYVISTA:
            try: self.plotter.close()
            except: pass


class TabRack(QWidget):
    def __init__(self, theme, parent_tabs=None):
        super().__init__()
        self.theme = theme
        self.combined_mesh = None
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(50)
        self.update_timer.timeout.connect(self._perform_update)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(360)
        left_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setSpacing(16)
        
        grp_load = create_group_box("1. Bara Yükle", self.theme)
        QVBoxLayout(grp_load).addWidget(create_styled_btn("📁 BARA STL YÜKLE", self._load_rack, self.theme))
        left_layout.addWidget(grp_load)
        
        grp_pos = create_group_box("2. Askı Konumu (İnce Ayar)", self.theme)
        pos_layout = QVBoxLayout(grp_pos)
        self.inputs = {}
        for label, mn, mx, val in [("X Konum", -3000, 3000, 0), ("Y Konum", -1500, 1500, 0), ("Z Konum", -3000, 3000, 500), ("Rot X", -180, 180, 0), ("Rot Y", -180, 180, 0), ("Rot Z", -180, 180, 0)]:
            row, spin = create_control_row(label, mn, mx, val, self._schedule_update, self.theme)
            pos_layout.addLayout(row)
            self.inputs[label] = spin
        left_layout.addWidget(grp_pos)
        
        grp_mult = create_group_box("3. Askı Çoklama", self.theme)
        mult_layout = QGridLayout(grp_mult)
        lbl_s = f"color: {self.theme['text_secondary']};"
        mult_layout.addWidget(QLabel("Askı Adedi:", styleSheet=lbl_s), 0, 0)
        self.sp_count = QSpinBox()
        self.sp_count.setRange(1, 30)
        self.sp_count.setValue(6)
        self.sp_count.setStyleSheet(input_style(self.theme))
        self.sp_count.valueChanged.connect(self._schedule_update)
        mult_layout.addWidget(self.sp_count, 0, 1)
        mult_layout.addWidget(QLabel("Mesafe (mm):", styleSheet=lbl_s), 1, 0)
        self.sp_dist = QSpinBox()
        self.sp_dist.setRange(50, 1000)
        self.sp_dist.setValue(200)
        self.sp_dist.setStyleSheet(input_style(self.theme))
        self.sp_dist.valueChanged.connect(self._schedule_update)
        mult_layout.addWidget(self.sp_dist, 1, 1)
        left_layout.addWidget(grp_mult)
        
        grp_cost = create_group_box("4. Maliyet Özeti", self.theme)
        cost_layout = QVBoxLayout(grp_cost)
        self.lbl_area_total = QLabel("Toplam Alan: - m²")
        self.lbl_area_total.setStyleSheet(f"color: {self.theme['text']};")
        cost_layout.addWidget(self.lbl_area_total)
        self.lbl_result_total = QLabel("Toplam Maliyet: - ₺")
        self.lbl_result_total.setStyleSheet(f"color: {self.theme['success']}; font-size: 16px; font-weight: bold;")
        cost_layout.addWidget(self.lbl_result_total)
        left_layout.addWidget(grp_cost)
        
        grp_save = create_group_box("5. Bara Grubunu Kaydet", self.theme)
        QVBoxLayout(grp_save).addWidget(create_styled_btn("💾 BARA GRUBUNU KAYDET", self._save_full, self.theme))
        left_layout.addWidget(grp_save)
        
        left_layout.addStretch()
        left_scroll.setWidget(left_content)
        layout.addWidget(left_scroll)
        
        if HAS_PYVISTA:
            self.plotter = QtInteractor(self)
            self.plotter.set_background(COLOR_BG)
            layout.addWidget(self.plotter, 1)
        else:
            layout.addWidget(QLabel("PyVista yüklü değil"), 1)
    
    def _load_rack(self):
        if not HAS_PYVISTA: return
        fname, _ = QFileDialog.getOpenFileName(self, "Bara Seç", "", "STL (*.stl)")
        if fname:
            DATA.rack_poly = pv.read(fname)
            c = DATA.rack_poly.center
            DATA.rack_poly.translate([-c[0], -c[1], -c[2]], inplace=True)
            self._schedule_update()
    
    def _schedule_update(self): self.update_timer.start()
    
    def _perform_update(self):
        if not HAS_PYVISTA: return
        self.plotter.clear()
        if DATA.rack_poly: self.plotter.add_mesh(DATA.rack_poly, color=COLOR_RACK)
        rack_count = self.sp_count.value()
        DATA.hangers_on_rack = rack_count
        total_parts = DATA.parts_per_hanger * rack_count
        total_area = total_parts * DATA.part_area_m2
        self.lbl_area_total.setText(f"Toplam Alan: {total_area:.4f} m²")
        self.lbl_result_total.setText(f"Toplam Maliyet: {total_parts * DATA.unit_cost:,.2f} ₺")
        if DATA.locked_assembly:
            base = DATA.locked_assembly.copy()
            center = base.center
            base.translate([-center[0], -center[1], -center[2]], inplace=True)
            base.rotate_x(self.inputs["Rot X"].value(), inplace=True)
            base.rotate_z(self.inputs["Rot Z"].value(), inplace=True)
            base.rotate_y(self.inputs["Rot Y"].value(), inplace=True)
            sx, sy, sz = self.inputs["X Konum"].value(), self.inputs["Y Konum"].value(), self.inputs["Z Konum"].value()
            meshes = []
            for i in range(self.sp_count.value()):
                inst = base.copy()
                inst.translate([sx + (i * self.sp_dist.value()), sy, sz], inplace=True)
                meshes.append(inst)
            if meshes:
                self.combined_mesh = meshes[0].merge(meshes[1:]) if len(meshes) > 1 else meshes[0]
                self.plotter.add_mesh(self.combined_mesh, color=COLOR_HANGER, smooth_shading=True)
    
    def _save_full(self):
        if DATA.rack_poly and self.combined_mesh:
            DATA.full_rack_assembly = DATA.rack_poly.merge(self.combined_mesh)
            QMessageBox.information(self, "Başarılı", "Bara grubu kaydedildi!")
        else:
            QMessageBox.warning(self, "Uyarı", "Önce bara ve askı yükleyin!")
    
    def close_renderer(self):
        if HAS_PYVISTA:
            try: self.plotter.close()
            except: pass


class TabBath(QWidget):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(50)
        self.update_timer.timeout.connect(self._perform_update)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(360)
        left_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setSpacing(16)
        
        grp_load = create_group_box("1. Banyo Yükle", self.theme)
        QVBoxLayout(grp_load).addWidget(create_styled_btn("📁 BANYO STL YÜKLE", self._load_bath, self.theme))
        left_layout.addWidget(grp_load)
        
        grp_pos = create_group_box("2. Bara Konumu ve Açısı", self.theme)
        pos_layout = QVBoxLayout(grp_pos)
        self.inputs = {}
        for label, mn, mx, val in [("X Konum", -3000, 3000, 0), ("Y Konum", -1500, 1500, 0), ("Z Konum", -3000, 3000, 1000), ("Rot X", -180, 180, 0), ("Rot Y", -180, 180, 0), ("Rot Z", -180, 180, 0)]:
            row, spin = create_control_row(label, mn, mx, val, self._schedule_update, self.theme)
            pos_layout.addLayout(row)
            self.inputs[label] = spin
        left_layout.addWidget(grp_pos)
        
        left_layout.addStretch()
        left_scroll.setWidget(left_content)
        layout.addWidget(left_scroll)
        
        if HAS_PYVISTA:
            self.plotter = QtInteractor(self)
            self.plotter.set_background(COLOR_BG)
            layout.addWidget(self.plotter, 1)
        else:
            layout.addWidget(QLabel("PyVista yüklü değil"), 1)
    
    def _load_bath(self):
        if not HAS_PYVISTA: return
        fname, _ = QFileDialog.getOpenFileName(self, "Banyo Seç", "", "STL (*.stl)")
        if fname:
            DATA.bath_poly = pv.read(fname)
            self._schedule_update()
    
    def _schedule_update(self): self.update_timer.start()
    
    def _perform_update(self):
        if not HAS_PYVISTA: return
        self.plotter.clear()
        if DATA.bath_poly:
            self.plotter.add_mesh(DATA.bath_poly, color=COLOR_BATH, opacity=0.2, style="wireframe")
            self.plotter.add_mesh(DATA.bath_poly, color=COLOR_BATH, opacity=0.1)
        if DATA.full_rack_assembly:
            rack = DATA.full_rack_assembly.copy()
            center = rack.center
            rack.translate([-center[0], -center[1], -center[2]], inplace=True)
            rack.rotate_x(self.inputs["Rot X"].value(), inplace=True)
            rack.rotate_y(self.inputs["Rot Y"].value(), inplace=True)
            rack.rotate_z(self.inputs["Rot Z"].value(), inplace=True)
            rack.translate([self.inputs["X Konum"].value(), self.inputs["Y Konum"].value(), self.inputs["Z Konum"].value()], inplace=True)
            self.plotter.add_mesh(rack, color=COLOR_RACK)
    
    def close_renderer(self):
        if HAS_PYVISTA:
            try: self.plotter.close()
            except: pass


class BaraHesaplamaPage(BasePage):
    def __init__(self, theme):
        super().__init__(theme)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ background: {self.theme['bg_main']}; border: none; }}
            QTabBar::tab {{ background: {self.theme['bg_card']}; color: {self.theme['text_secondary']}; padding: 12px 24px; margin-right: 2px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: bold; }}
            QTabBar::tab:selected {{ background: {self.theme['bg_main']}; color: {self.theme['primary']}; }}
            QTabBar::tab:hover:!selected {{ background: {self.theme['bg_hover']}; }}
        """)
        
        self.tab_part = TabPart(self.theme)
        self.tab_hanger = TabHanger(self.theme)
        self.tab_rack = TabRack(self.theme)
        self.tab_bath = TabBath(self.theme)
        
        self.tabs.addTab(self.tab_part, "1. Parça & Maliyet")
        self.tabs.addTab(self.tab_hanger, "2. Askı Montajı")
        self.tabs.addTab(self.tab_rack, "3. Bara Dizilimi")
        self.tabs.addTab(self.tab_bath, "4. Banyo Simülasyonu")
        
        layout.addWidget(self.tabs)
    
    def closeEvent(self, event):
        try:
            self.tab_part.close_renderer()
            self.tab_hanger.close_renderer()
            self.tab_rack.close_renderer()
            self.tab_bath.close_renderer()
        except: pass
        event.accept()
