# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Kullanıcı Menü Yetkileri
Kullanıcı bazlı hangi menüleri görebileceğini ayarlama
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QComboBox,
    QFrame, QGroupBox, QTreeWidget, QTreeWidgetItem, QSplitter,
    QPushButton, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection
from core.menu_structure import MENU_STRUCTURE
from core.log_manager import LogManager
from core.nexor_brand import brand


class SistemKullaniciYetkiPage(BasePage):
    """Kullanıcı Menü Yetkileri Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.kullanicilar = []
        self.current_kullanici_id = None
        self._setup_ui()
        QTimer.singleShot(100, self.load_kullanicilar)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        header = QFrame()
        header.setStyleSheet(f"QFrame{{background:{brand.BG_CARD};border-radius:8px;padding:16px;}}")
        hl = QHBoxLayout(header)
        
        title = QLabel("🔐 Kullanıcı Menü Yetkileri")
        title.setStyleSheet(f"font-size:20px;font-weight:bold;color:{brand.TEXT};")
        hl.addWidget(title)
        hl.addStretch()
        
        # Kullanıcı seçimi
        lbl_kullanici = QLabel("Kullanıcı:")
        lbl_kullanici.setStyleSheet(f"color:{brand.TEXT};font-weight:bold;")
        hl.addWidget(lbl_kullanici)
        
        self.cmb_kullanici = QComboBox()
        self.cmb_kullanici.setMinimumWidth(250)
        self.cmb_kullanici.currentIndexChanged.connect(self.on_kullanici_changed)
        self.cmb_kullanici.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                color: {brand.TEXT};
            }}
        """)
        hl.addWidget(self.cmb_kullanici)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setCursor(Qt.PointingHandCursor)
        btn_kaydet.clicked.connect(self.kaydet)
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #16a34a; }}
        """)
        hl.addWidget(btn_kaydet)
        
        layout.addWidget(header)
        
        # Ana içerik - Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Sol: Kullanıcı bilgisi ve hızlı işlemler
        left_widget = QFrame()
        left_widget.setStyleSheet(f"QFrame{{background:{brand.BG_CARD};border-radius:8px;}}")
        left_layout = QVBoxLayout(left_widget)
        
        lbl_info = QLabel("👤 Seçili Kullanıcı")
        lbl_info.setStyleSheet(f"font-size:14px;font-weight:bold;color:{brand.TEXT};padding:10px;")
        left_layout.addWidget(lbl_info)
        
        self.lbl_kullanici_detay = QLabel("Kullanıcı seçiniz...")
        self.lbl_kullanici_detay.setStyleSheet(f"color:{brand.TEXT_MUTED};padding:10px;")
        self.lbl_kullanici_detay.setWordWrap(True)
        left_layout.addWidget(self.lbl_kullanici_detay)
        
        # Hızlı işlemler
        quick_group = QGroupBox("Hızlı İşlemler")
        quick_group.setStyleSheet(f"QGroupBox{{color:{brand.TEXT};font-weight:bold;border:1px solid {brand.BORDER};border-radius:6px;margin-top:10px;padding-top:10px;}}")
        quick_layout = QVBoxLayout()
        
        btn_select_all = QPushButton("✅ Tümünü Seç")
        btn_select_all.clicked.connect(self.select_all)
        btn_select_all.setStyleSheet(f"background:{brand.PRIMARY};color:white;border:none;border-radius:4px;padding:8px;")
        quick_layout.addWidget(btn_select_all)
        
        btn_deselect_all = QPushButton("⬜ Tümünü Kaldır")
        btn_deselect_all.clicked.connect(self.deselect_all)
        btn_deselect_all.setStyleSheet(f"background:{brand.WARNING};color:white;border:none;border-radius:4px;padding:8px;")
        quick_layout.addWidget(btn_deselect_all)
        
        btn_select_view = QPushButton("👁️ Sadece Ana Menüler")
        btn_select_view.clicked.connect(self.select_main_only)
        btn_select_view.setStyleSheet(f"background:{brand.INFO};color:white;border:none;border-radius:4px;padding:8px;")
        quick_layout.addWidget(btn_select_view)
        
        quick_group.setLayout(quick_layout)
        left_layout.addWidget(quick_group)
        
        # İstatistik
        self.lbl_stats = QLabel("Seçili: 0 menü")
        self.lbl_stats.setStyleSheet(f"color:{brand.TEXT_MUTED};padding:10px;font-size:12px;")
        left_layout.addWidget(self.lbl_stats)
        
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        
        # Sağ: Menü ağacı
        right_widget = QFrame()
        right_widget.setStyleSheet(f"QFrame{{background:{brand.BG_CARD};border-radius:8px;}}")
        right_layout = QVBoxLayout(right_widget)
        
        lbl_menuler = QLabel("📋 Menüler")
        lbl_menuler.setStyleSheet(f"font-size:14px;font-weight:bold;color:{brand.TEXT};padding:10px;")
        right_layout.addWidget(lbl_menuler)
        
        self.tree_menuler = QTreeWidget()
        self.tree_menuler.setHeaderLabels(["Menü", "Açıklama"])
        self.tree_menuler.setAlternatingRowColors(True)
        self.tree_menuler.itemChanged.connect(self.on_item_changed)
        self.tree_menuler.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {brand.BG_MAIN};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
            }}
            QTreeWidget::item {{
                padding: 6px;
            }}
            QTreeWidget::item:selected {{
                background-color: {brand.PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {brand.BG_CARD};
                color: {brand.TEXT};
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
        """)
        right_layout.addWidget(self.tree_menuler)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
        
        # Menü ağacını oluştur
        self.build_menu_tree()
    
    def build_menu_tree(self):
        """Menü ağacını oluştur"""
        self.tree_menuler.clear()
        
        for menu in MENU_STRUCTURE:
            # Ana menü
            parent_item = QTreeWidgetItem([f"{menu['icon']} {menu['label']}", "Ana Menü"])
            parent_item.setFlags(parent_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            parent_item.setCheckState(0, Qt.Unchecked)
            parent_item.setData(0, Qt.UserRole, menu['id'])
            
            # Font bold yap
            font = parent_item.font(0)
            font.setBold(True)
            parent_item.setFont(0, font)
            
            # Alt menüler
            for child in menu.get('children', []):
                child_item = QTreeWidgetItem([f"    {child['label']}", child['id']])
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.Unchecked)
                child_item.setData(0, Qt.UserRole, child['id'])
                parent_item.addChild(child_item)
            
            self.tree_menuler.addTopLevelItem(parent_item)
            parent_item.setExpanded(True)
    
    def load_kullanicilar(self):
        """Kullanıcıları yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT k.id, k.kullanici_adi, k.ad, k.soyad, r.rol_adi
                FROM sistem.kullanicilar k
                LEFT JOIN sistem.roller r ON k.rol_id = r.id
                WHERE ISNULL(k.silindi_mi, 0) = 0 AND ISNULL(k.aktif_mi, 1) = 1
                ORDER BY k.kullanici_adi
            """)
            
            self.kullanicilar = []
            self.cmb_kullanici.clear()
            self.cmb_kullanici.addItem("-- Kullanıcı Seçin --", None)
            
            for row in cursor.fetchall():
                kullanici = {
                    'id': row.id,
                    'kullanici_adi': row.kullanici_adi,
                    'ad': row.ad,
                    'soyad': row.soyad,
                    'rol': row.rol_adi
                }
                self.kullanicilar.append(kullanici)
                
                display = f"{row.kullanici_adi} - {row.ad or ''} {row.soyad or ''}"
                if row.rol_adi:
                    display += f" ({row.rol_adi})"
                self.cmb_kullanici.addItem(display, row.id)
            
            conn.close()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kullanıcılar yüklenirken hata: {str(e)}")
    
    def on_kullanici_changed(self, index):
        """Kullanıcı seçildiğinde"""
        kullanici_id = self.cmb_kullanici.currentData()
        self.current_kullanici_id = kullanici_id
        
        if not kullanici_id:
            self.lbl_kullanici_detay.setText("Kullanıcı seçiniz...")
            self.deselect_all()
            return
        
        # Kullanıcı bilgisini göster
        for k in self.kullanicilar:
            if k['id'] == kullanici_id:
                self.lbl_kullanici_detay.setText(
                    f"<b>Kullanıcı Adı:</b> {k['kullanici_adi']}<br>"
                    f"<b>Ad Soyad:</b> {k['ad'] or ''} {k['soyad'] or ''}<br>"
                    f"<b>Rol:</b> {k['rol'] or '-'}"
                )
                break
        
        # Kullanıcının menü yetkilerini yükle
        self.load_kullanici_yetkileri(kullanici_id)
    
    def load_kullanici_yetkileri(self, kullanici_id):
        """Kullanıcının menü yetkilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Tablo var mı kontrol et, yoksa oluştur
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES 
                               WHERE TABLE_SCHEMA = 'sistem' AND TABLE_NAME = 'kullanici_menu_yetkileri')
                BEGIN
                    CREATE TABLE sistem.kullanici_menu_yetkileri (
                        id BIGINT IDENTITY(1,1) PRIMARY KEY,
                        kullanici_id BIGINT NOT NULL,
                        menu_id NVARCHAR(100) NOT NULL,
                        olusturma_tarihi DATETIME DEFAULT GETDATE(),
                        CONSTRAINT FK_kmy_kullanici FOREIGN KEY (kullanici_id) 
                            REFERENCES sistem.kullanicilar(id)
                    )
                END
            """)
            conn.commit()
            
            # Kullanıcının yetkilerini al
            cursor.execute("""
                SELECT menu_id FROM sistem.kullanici_menu_yetkileri WHERE kullanici_id = ?
            """, [kullanici_id])
            
            yetkili_menuler = set(row.menu_id for row in cursor.fetchall())
            conn.close()
            
            # Checkbox'ları güncelle
            self.deselect_all()
            
            root = self.tree_menuler.invisibleRootItem()
            for i in range(root.childCount()):
                parent_item = root.child(i)
                parent_id = parent_item.data(0, Qt.UserRole)
                
                # Alt menüleri kontrol et
                for j in range(parent_item.childCount()):
                    child_item = parent_item.child(j)
                    child_id = child_item.data(0, Qt.UserRole)
                    if child_id in yetkili_menuler:
                        child_item.setCheckState(0, Qt.Checked)
            
            self.update_stats()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Yetkiler yüklenirken hata: {str(e)}")

    
    def get_selected_menu_ids(self):
        """Seçili menü ID'lerini al (ana menüler + alt menüler)"""
        selected = []
        root = self.tree_menuler.invisibleRootItem()
        
        for i in range(root.childCount()):
            parent_item = root.child(i)
            parent_id = parent_item.data(0, Qt.UserRole)
            
            # Alt menüleri kontrol et
            has_selected_child = False
            for j in range(parent_item.childCount()):
                child_item = parent_item.child(j)
                if child_item.checkState(0) == Qt.Checked:
                    menu_id = child_item.data(0, Qt.UserRole)
                    if menu_id:
                        selected.append(menu_id)
                        has_selected_child = True
            
            # Eğer alt menülerden en az biri seçiliyse, ana menüyü de ekle
            if has_selected_child and parent_id:
                selected.append(parent_id)
        
        return selected
    
    def select_all(self):
        """Tümünü seç"""
        self.tree_menuler.blockSignals(True)
        root = self.tree_menuler.invisibleRootItem()
        for i in range(root.childCount()):
            parent_item = root.child(i)
            parent_item.setCheckState(0, Qt.Checked)
        self.tree_menuler.blockSignals(False)
        self.update_stats()
    
    def deselect_all(self):
        """Tümünü kaldır"""
        self.tree_menuler.blockSignals(True)
        root = self.tree_menuler.invisibleRootItem()
        for i in range(root.childCount()):
            parent_item = root.child(i)
            parent_item.setCheckState(0, Qt.Unchecked)
        self.tree_menuler.blockSignals(False)
        self.update_stats()
    
    def select_main_only(self):
        """Sadece ana menülerin ilk alt menüsünü seç"""
        self.tree_menuler.blockSignals(True)
        self.deselect_all()
        
        root = self.tree_menuler.invisibleRootItem()
        for i in range(root.childCount()):
            parent_item = root.child(i)
            if parent_item.childCount() > 0:
                parent_item.child(0).setCheckState(0, Qt.Checked)
        
        self.tree_menuler.blockSignals(False)
        self.update_stats()
    
    def on_item_changed(self, item, column):
        """Checkbox değiştiğinde"""
        self.update_stats()
    
    def update_stats(self):
        """İstatistikleri güncelle"""
        selected = self.get_selected_menu_ids()
        self.lbl_stats.setText(f"Seçili: {len(selected)} menü")
    
    def kaydet(self):
        """Yetkileri kaydet"""
        if not self.current_kullanici_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kullanıcı seçin!")
            return
        
        selected_ids = self.get_selected_menu_ids()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Mevcut yetkileri sil
            cursor.execute("DELETE FROM sistem.kullanici_menu_yetkileri WHERE kullanici_id = ?", 
                          [self.current_kullanici_id])
            
            # Yeni yetkileri ekle
            for menu_id in selected_ids:
                cursor.execute("""
                    INSERT INTO sistem.kullanici_menu_yetkileri (kullanici_id, menu_id)
                    VALUES (?, ?)
                """, [self.current_kullanici_id, menu_id])
            
            conn.commit()
            conn.close()
            
            # Log kaydet
            kullanici_adi = self.cmb_kullanici.currentText()
            LogManager.log_update('sistem', 'kullanici_menu_yetkileri', self.current_kullanici_id,
                                 aciklama=f'Kullanıcı menü yetkileri güncellendi: {kullanici_adi} ({len(selected_ids)} menü)')
            
            QMessageBox.information(self, "Başarılı", f"{len(selected_ids)} menü yetkisi kaydedildi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {str(e)}")
