# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Rol İzin Yönetimi
Rollere izin atama sayfası
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QComboBox,
    QFrame, QGroupBox, QTreeWidget, QTreeWidgetItem, QSplitter,
    QCheckBox, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager


class SistemRolIzinPage(BasePage):
    """Rol İzin Yönetimi Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.roller = []
        self.izinler = []
        self.current_rol_id = None
        self._setup_ui()
        QTimer.singleShot(100, self.load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        header = QFrame()
        header.setStyleSheet(f"QFrame{{background:{self.theme.get('bg_card', '#1e293b')};border-radius:8px;padding:16px;}}")
        hl = QHBoxLayout(header)
        
        title = QLabel("🔐 Rol İzin Yönetimi")
        title.setStyleSheet(f"font-size:20px;font-weight:bold;color:{self.theme.get('text', '#ffffff')};")
        hl.addWidget(title)
        hl.addStretch()
        
        # Rol seçimi
        lbl_rol = QLabel("Rol Seçin:")
        lbl_rol.setStyleSheet(f"color:{self.theme.get('text', '#ffffff')};font-weight:bold;")
        hl.addWidget(lbl_rol)
        
        self.cmb_rol = QComboBox()
        self.cmb_rol.setMinimumWidth(200)
        self.cmb_rol.currentIndexChanged.connect(self.on_rol_changed)
        self.cmb_rol.setStyleSheet(f"""
            QComboBox {{
                background: {self.theme.get('bg_input', '#1e293b')};
                border: 1px solid {self.theme.get('border', 'rgba(51, 65, 85, 0.5)')};
                border-radius: 6px;
                padding: 8px 12px;
                color: {self.theme.get('text', '#ffffff')};
                min-width: 200px;
            }}
        """)
        hl.addWidget(self.cmb_rol)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setCursor(Qt.PointingHandCursor)
        btn_kaydet.clicked.connect(self.kaydet)
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #16a34a; }}
        """)
        hl.addWidget(btn_kaydet)
        
        btn_refresh = QPushButton("🔄")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.load_data)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#3b82f6')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        hl.addWidget(btn_refresh)
        
        layout.addWidget(header)
        
        # Ana içerik - Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Sol: Rol bilgisi
        left_widget = QFrame()
        left_widget.setStyleSheet(f"QFrame{{background:{self.theme.get('bg_card', '#1e293b')};border-radius:8px;}}")
        left_layout = QVBoxLayout(left_widget)
        
        lbl_info = QLabel("📋 Seçili Rol Bilgisi")
        lbl_info.setStyleSheet(f"font-size:14px;font-weight:bold;color:{self.theme.get('text', '#ffffff')};padding:10px;")
        left_layout.addWidget(lbl_info)
        
        self.lbl_rol_detay = QLabel("Rol seçiniz...")
        self.lbl_rol_detay.setStyleSheet(f"color:{self.theme.get('text_secondary', '#94a3b8')};padding:10px;")
        self.lbl_rol_detay.setWordWrap(True)
        left_layout.addWidget(self.lbl_rol_detay)
        
        # Hızlı seçim butonları
        quick_group = QGroupBox("Hızlı İşlemler")
        quick_group.setStyleSheet(f"QGroupBox{{color:{self.theme.get('text', '#ffffff')};font-weight:bold;border:1px solid {self.theme.get('border', 'rgba(51, 65, 85, 0.5)')};border-radius:6px;margin-top:10px;padding-top:10px;}}")
        quick_layout = QVBoxLayout()
        
        btn_select_all = QPushButton("✅ Tümünü Seç")
        btn_select_all.clicked.connect(self.select_all)
        btn_select_all.setStyleSheet(f"background:{self.theme.get('primary', '#3b82f6')};color:white;border:none;border-radius:4px;padding:8px;")
        quick_layout.addWidget(btn_select_all)
        
        btn_deselect_all = QPushButton("⬜ Tümünü Kaldır")
        btn_deselect_all.clicked.connect(self.deselect_all)
        btn_deselect_all.setStyleSheet(f"background:{self.theme.get('warning', '#f59e0b')};color:white;border:none;border-radius:4px;padding:8px;")
        quick_layout.addWidget(btn_deselect_all)
        
        btn_select_view = QPushButton("👁️ Sadece Görüntüleme")
        btn_select_view.clicked.connect(self.select_view_only)
        btn_select_view.setStyleSheet(f"background:{self.theme.get('info', '#06b6d4')};color:white;border:none;border-radius:4px;padding:8px;")
        quick_layout.addWidget(btn_select_view)
        
        quick_group.setLayout(quick_layout)
        left_layout.addWidget(quick_group)
        
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        
        # Sağ: İzin ağacı
        right_widget = QFrame()
        right_widget.setStyleSheet(f"QFrame{{background:{self.theme.get('bg_card', '#1e293b')};border-radius:8px;}}")
        right_layout = QVBoxLayout(right_widget)
        
        lbl_izinler = QLabel("🔑 İzinler")
        lbl_izinler.setStyleSheet(f"font-size:14px;font-weight:bold;color:{self.theme.get('text', '#ffffff')};padding:10px;")
        right_layout.addWidget(lbl_izinler)
        
        self.tree_izinler = QTreeWidget()
        self.tree_izinler.setHeaderLabels(["İzin", "Açıklama"])
        self.tree_izinler.setAlternatingRowColors(True)
        self.tree_izinler.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree_izinler.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree_izinler.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {self.theme.get('bg_main', '#0f172a')};
                color: {self.theme.get('text', '#ffffff')};
                border: 1px solid {self.theme.get('border', 'rgba(51, 65, 85, 0.5)')};
                border-radius: 6px;
            }}
            QTreeWidget::item {{
                padding: 6px;
            }}
            QTreeWidget::item:selected {{
                background-color: {self.theme.get('primary', '#3b82f6')};
            }}
            QHeaderView::section {{
                background-color: {self.theme.get('bg_card', '#1e293b')};
                color: {self.theme.get('text', '#ffffff')};
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
        """)
        right_layout.addWidget(self.tree_izinler)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
    
    def load_data(self):
        """Verileri yükle"""
        self.load_roller()
        self.load_izinler()
    
    def load_roller(self):
        """Rolleri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, rol_kodu, rol_adi, aciklama, seviye
                FROM sistem.roller
                WHERE ISNULL(aktif_mi, 1) = 1
                ORDER BY seviye DESC, rol_adi
            """)
            
            self.roller = []
            self.cmb_rol.clear()
            self.cmb_rol.addItem("-- Rol Seçin --", None)
            
            for row in cursor.fetchall():
                rol = {
                    'id': row.id,
                    'kod': row.rol_kodu,
                    'ad': row.rol_adi,
                    'aciklama': row.aciklama,
                    'seviye': row.seviye
                }
                self.roller.append(rol)
                self.cmb_rol.addItem(f"{row.rol_adi} ({row.rol_kodu})", row.id)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Roller yüklenirken hata: {str(e)}")
    
    def load_izinler(self):
        """İzinleri modül bazlı ağaç yapısında yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, kod, modul, aciklama
                FROM sistem.izinler
                WHERE ISNULL(aktif_mi, 1) = 1
                ORDER BY modul, kod
            """)
            
            self.izinler = []
            self.tree_izinler.clear()
            
            # Modül bazlı gruplama
            moduller = {}
            for row in cursor.fetchall():
                izin = {
                    'id': row.id,
                    'kod': row.kod,
                    'modul': row.modul,
                    'aciklama': row.aciklama
                }
                self.izinler.append(izin)
                
                if row.modul not in moduller:
                    moduller[row.modul] = []
                moduller[row.modul].append(izin)
            
            conn.close()
            
            # Ağaç oluştur
            for modul, izin_list in sorted(moduller.items()):
                modul_item = QTreeWidgetItem([f"📁 {modul.upper()}", f"{len(izin_list)} izin"])
                modul_item.setFlags(modul_item.flags() | Qt.ItemIsAutoTristate | Qt.ItemIsUserCheckable)
                
                for izin in izin_list:
                    izin_item = QTreeWidgetItem([izin['kod'], izin['aciklama'] or ''])
                    izin_item.setFlags(izin_item.flags() | Qt.ItemIsUserCheckable)
                    izin_item.setCheckState(0, Qt.Unchecked)
                    izin_item.setData(0, Qt.UserRole, izin['id'])
                    modul_item.addChild(izin_item)
                
                self.tree_izinler.addTopLevelItem(modul_item)
                modul_item.setExpanded(True)
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"İzinler yüklenirken hata: {str(e)}")
    
    def on_rol_changed(self, index):
        """Rol seçildiğinde"""
        rol_id = self.cmb_rol.currentData()
        self.current_rol_id = rol_id
        
        if not rol_id:
            self.lbl_rol_detay.setText("Rol seçiniz...")
            self.deselect_all()
            return
        
        # Rol bilgisini göster
        for rol in self.roller:
            if rol['id'] == rol_id:
                self.lbl_rol_detay.setText(
                    f"<b>Kod:</b> {rol['kod']}<br>"
                    f"<b>Ad:</b> {rol['ad']}<br>"
                    f"<b>Seviye:</b> {rol['seviye'] or 0}<br>"
                    f"<b>Açıklama:</b> {rol['aciklama'] or '-'}"
                )
                break
        
        # Rol izinlerini yükle
        self.load_rol_izinleri(rol_id)
    
    def load_rol_izinleri(self, rol_id):
        """Seçili rolün izinlerini işaretle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT izin_id FROM sistem.rol_izinler WHERE rol_id = ?
            """, [rol_id])
            
            rol_izin_ids = set(row.izin_id for row in cursor.fetchall())
            conn.close()
            
            # Tüm checkbox'ları güncelle
            self.deselect_all()
            
            root = self.tree_izinler.invisibleRootItem()
            for i in range(root.childCount()):
                modul_item = root.child(i)
                for j in range(modul_item.childCount()):
                    izin_item = modul_item.child(j)
                    izin_id = izin_item.data(0, Qt.UserRole)
                    if izin_id in rol_izin_ids:
                        izin_item.setCheckState(0, Qt.Checked)
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Rol izinleri yüklenirken hata: {str(e)}")
    
    def get_selected_izin_ids(self):
        """Seçili izin ID'lerini al"""
        selected = []
        root = self.tree_izinler.invisibleRootItem()
        for i in range(root.childCount()):
            modul_item = root.child(i)
            for j in range(modul_item.childCount()):
                izin_item = modul_item.child(j)
                if izin_item.checkState(0) == Qt.Checked:
                    izin_id = izin_item.data(0, Qt.UserRole)
                    if izin_id:
                        selected.append(izin_id)
        return selected
    
    def select_all(self):
        """Tüm izinleri seç"""
        root = self.tree_izinler.invisibleRootItem()
        for i in range(root.childCount()):
            modul_item = root.child(i)
            for j in range(modul_item.childCount()):
                modul_item.child(j).setCheckState(0, Qt.Checked)
    
    def deselect_all(self):
        """Tüm izinleri kaldır"""
        root = self.tree_izinler.invisibleRootItem()
        for i in range(root.childCount()):
            modul_item = root.child(i)
            for j in range(modul_item.childCount()):
                modul_item.child(j).setCheckState(0, Qt.Unchecked)
    
    def select_view_only(self):
        """Sadece görüntüleme izinlerini seç"""
        self.deselect_all()
        root = self.tree_izinler.invisibleRootItem()
        for i in range(root.childCount()):
            modul_item = root.child(i)
            for j in range(modul_item.childCount()):
                izin_item = modul_item.child(j)
                kod = izin_item.text(0)
                if 'goruntule' in kod.lower() or 'view' in kod.lower():
                    izin_item.setCheckState(0, Qt.Checked)
    
    def kaydet(self):
        """Rol izinlerini kaydet"""
        if not self.current_rol_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir rol seçin!")
            return
        
        selected_ids = self.get_selected_izin_ids()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Mevcut izinleri sil
            cursor.execute("DELETE FROM sistem.rol_izinler WHERE rol_id = ?", [self.current_rol_id])
            
            # Yeni izinleri ekle
            for izin_id in selected_ids:
                cursor.execute("""
                    INSERT INTO sistem.rol_izinler (rol_id, izin_id)
                    VALUES (?, ?)
                """, [self.current_rol_id, izin_id])
            
            conn.commit()
            conn.close()
            
            # Log kaydet
            rol_adi = self.cmb_rol.currentText()
            LogManager.log_update('sistem', 'rol_izinler', self.current_rol_id,
                                 aciklama=f'Rol izinleri güncellendi: {rol_adi} ({len(selected_ids)} izin)')
            
            QMessageBox.information(self, "Başarılı", f"{len(selected_ids)} izin kaydedildi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {str(e)}")
