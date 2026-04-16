# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Dokümantasyon Yönetimi
NAS üzerindeki kalite dokümanlarını görüntüleme ve yönetme

DÜZELTMELER:
1. Sistem klasörleri filtrelendi (#Recycle, @eaDir, $RECYCLE.BIN, vb.)
2. Hata yakalama iyileştirildi
"""

import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QMessageBox, QHeaderView, QSplitter, QFrame, QComboBox, QMenu,
    QFileDialog, QDialog, QFormLayout, QGroupBox, QProgressDialog,
    QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QIcon, QColor, QFont, QCursor

from components.base_page import BasePage


# Varsayılan NAS yolu (config.json'dan)
from config import NAS_PATHS
from core.nexor_brand import brand
DEFAULT_ROOT_PATH = NAS_PATHS["quality_path"]

# ============================================================
# YENİ: Atlanacak sistem klasörleri
# ============================================================
SKIP_FOLDERS = {
    '#recycle', '#Recycle', '#RECYCLE',           # NAS geri dönüşüm
    '@eadir', '@eaDir', '@EADIR',                  # Synology metadata
    '$recycle.bin', '$RECYCLE.BIN',               # Windows geri dönüşüm
    '.snapshot', '.snapshots',                     # NAS snapshot
    '@tmp', '.tmp', 'tmp',                         # Geçici klasörler
    '.ds_store', '.DS_Store',                      # macOS
    'thumbs.db', 'Thumbs.db',                      # Windows thumbnail
    'System Volume Information',                   # Windows sistem
}

def should_skip_folder(folder_name: str) -> bool:
    """Klasörün atlanıp atlanmayacağını kontrol et"""
    # Tam eşleşme
    if folder_name in SKIP_FOLDERS:
        return True
    # . ile başlayan gizli klasörler
    if folder_name.startswith('.'):
        return True
    # # ile başlayan sistem klasörleri
    if folder_name.startswith('#'):
        return True
    # @ ile başlayan metadata klasörleri
    if folder_name.startswith('@'):
        return True
    # $ ile başlayan sistem klasörleri
    if folder_name.startswith('$'):
        return True
    return False
# ============================================================

# Dosya türü ikonları (emoji)
FILE_ICONS = {
    '.pdf': '📕',
    '.doc': '📘',
    '.docx': '📘',
    '.xls': '📗',
    '.xlsx': '📗',
    '.xlsm': '📗',
    '.ppt': '📙',
    '.pptx': '📙',
    '.txt': '📄',
    '.jpg': '🖼️',
    '.jpeg': '🖼️',
    '.png': '🖼️',
    '.dwg': '📐',
    '.dxf': '📐',
    '.zip': '📦',
    '.rar': '📦',
    '.7z': '📦',
}

# Doküman tipi prefixleri
DOC_PREFIXES = {
    'EPS': ('🔷', 'Entegre Proses Süreci'),
    'PR': ('📘', 'Prosedür'),
    'TA': ('📗', 'Talimat'),
    'FR': ('📙', 'Form'),
    'LS': ('📋', 'Liste'),
    'PL': ('📊', 'Plan'),
    'TBL': ('📑', 'Tablo'),
    'SP': ('📝', 'Spesifikasyon'),
    'KK': ('📕', 'Kalite Kaydı'),
}


class FolderScanThread(QThread):
    """Klasör tarama thread'i"""
    finished = Signal(list)
    progress = Signal(str)
    
    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
    
    def run(self):
        folders = []
        try:
            if os.path.exists(self.root_path):
                for item in sorted(os.listdir(self.root_path)):
                    # ============================================================
                    # YENİ: Sistem klasörlerini atla
                    # ============================================================
                    if should_skip_folder(item):
                        continue
                    # ============================================================
                    
                    item_path = os.path.join(self.root_path, item)
                    try:
                        if os.path.isdir(item_path):
                            self.progress.emit(f"Taranıyor: {item}")
                            folders.append({
                                'name': item,
                                'path': item_path,
                                'modified': datetime.fromtimestamp(os.path.getmtime(item_path))
                            })
                    except (PermissionError, OSError) as e:
                        # Erişilemeyen klasörleri sessizce atla
                        self.progress.emit(f"Atlandı (erişim yok): {item}")
                        continue
        except Exception as e:
            self.progress.emit(f"Hata: {str(e)}")
        
        self.finished.emit(folders)


class DokumantasyonYonetimiPage(BasePage):
    """Dokümantasyon Yönetimi Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.root_path = DEFAULT_ROOT_PATH
        self.current_folder = None
        self.all_files = []
        self._setup_ui()
        self._load_folders()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📄 Dokümantasyon Yönetimi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {brand.TEXT};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Kök dizin gösterimi
        self.lbl_root = QLabel(f"📂 {self.root_path}")
        self.lbl_root.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px;")
        header_layout.addWidget(self.lbl_root)
        
        btn_ayarlar = QPushButton("Ayarlar")
        btn_ayarlar.setToolTip("Kök dizini değiştir")
        btn_ayarlar.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 8px 16px;
                color: {brand.TEXT};
            }}
            QPushButton:hover {{
                background: {brand.BG_INPUT};
            }}
        """)
        btn_ayarlar.clicked.connect(self._change_root_path)
        header_layout.addWidget(btn_ayarlar)
        
        layout.addLayout(header_layout)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {brand.BG_CARD}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        
        # Arama
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Dosya ara...")
        self.txt_search.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                color: {brand.TEXT};
                min-width: 250px;
            }}
        """)
        self.txt_search.textChanged.connect(self._filter_files)
        toolbar_layout.addWidget(self.txt_search)
        
        # Dosya türü filtresi
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["Tümü", "PDF", "Word", "Excel", "Diğer"])
        self.cmb_filter.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                color: {brand.TEXT};
                min-width: 100px;
            }}
        """)
        self.cmb_filter.currentIndexChanged.connect(self._filter_files)
        toolbar_layout.addWidget(self.cmb_filter)
        
        toolbar_layout.addStretch()
        
        # Butonlar
        btn_refresh = QPushButton("🔄 Yenile")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {brand.BORDER};
            }}
        """)
        btn_refresh.clicked.connect(self._load_folders)
        toolbar_layout.addWidget(btn_refresh)
        
        btn_open_explorer = QPushButton("📂 Klasörü Aç")
        btn_open_explorer.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {brand.PRIMARY_HOVER};
            }}
        """)
        btn_open_explorer.clicked.connect(self._open_current_folder)
        toolbar_layout.addWidget(btn_open_explorer)
        
        layout.addWidget(toolbar)
        
        # Splitter - Sol: Klasörler, Sağ: Dosyalar
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {brand.BORDER};
                width: 2px;
            }}
        """)
        
        # Sol Panel - Klasör Ağacı
        left_panel = QFrame()
        left_panel.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 8px;
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        
        lbl_folders = QLabel("📁 Süreç Klasörleri")
        lbl_folders.setStyleSheet(f"font-weight: bold; color: {brand.TEXT}; padding: 4px;")
        left_layout.addWidget(lbl_folders)
        
        self.tree_folders = QTreeWidget()
        self.tree_folders.setHeaderHidden(True)
        self.tree_folders.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                border: none;
                color: {brand.TEXT};
            }}
            QTreeWidget::item {{
                padding: 6px 4px;
                border-radius: 4px;
            }}
            QTreeWidget::item:selected {{
                background: {brand.PRIMARY};
                color: white;
            }}
            QTreeWidget::item:hover:!selected {{
                background: {brand.BG_INPUT};
            }}
        """)
        self.tree_folders.itemClicked.connect(self._on_folder_clicked)
        left_layout.addWidget(self.tree_folders)
        
        splitter.addWidget(left_panel)
        
        # Sağ Panel - Dosya Listesi
        right_panel = QFrame()
        right_panel.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 8px;
            }}
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        
        # Dosya sayısı etiketi
        self.lbl_file_count = QLabel("📄 Dosyalar")
        self.lbl_file_count.setStyleSheet(f"font-weight: bold; color: {brand.TEXT}; padding: 4px;")
        right_layout.addWidget(self.lbl_file_count)
        
        self.table_files = QTableWidget()
        self.table_files.setColumnCount(5)
        self.table_files.setHorizontalHeaderLabels(["", "Dosya Adı", "Tür", "Boyut", "Değiştirilme"])
        self.table_files.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_files.setSelectionMode(QTableWidget.SingleSelection)
        self.table_files.verticalHeader().setVisible(False)
        self.table_files.setShowGrid(False)
        self.table_files.setStyleSheet(f"""
            QTableWidget {{
                background: transparent;
                border: none;
                color: {brand.TEXT};
            }}
            QTableWidget::item {{
                padding: 8px 4px;
                border-bottom: 1px solid {brand.BORDER};
            }}
            QTableWidget::item:selected {{
                background: {brand.PRIMARY};
                color: white;
            }}
            QHeaderView::section {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-weight: bold;
            }}
        """)
        
        # Kolon genişlikleri
        header = self.table_files.horizontalHeader()
        self.table_files.setColumnWidth(0, 60)  # İkon
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Dosya adı
        self.table_files.setColumnWidth(2, 80)   # Tür
        self.table_files.setColumnWidth(3, 80)   # Boyut
        self.table_files.setColumnWidth(4, 120)  # Tarih
        
        # Çift tıklama
        self.table_files.doubleClicked.connect(self._open_file)
        # Sağ tık menü
        self.table_files.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_files.customContextMenuRequested.connect(self._show_context_menu)
        
        right_layout.addWidget(self.table_files)
        
        splitter.addWidget(right_panel)
        
        # Splitter oranları
        splitter.setSizes([250, 750])
        
        layout.addWidget(splitter)
        
        # Alt bilgi
        self.lbl_status = QLabel("Klasör seçin...")
        self.lbl_status.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px;")
        layout.addWidget(self.lbl_status)
    
    def _load_folders(self):
        """Klasörleri yükle"""
        self.tree_folders.clear()
        
        if not os.path.exists(self.root_path):
            QMessageBox.warning(
                self, "Uyarı", 
                f"Belirtilen yol bulunamadı:\n{self.root_path}\n\n"
                "Lütfen ayarlardan doğru yolu belirtin."
            )
            return
        
        self.lbl_status.setText("Klasörler yükleniyor...")
        QApplication.processEvents()
        
        skipped_count = 0  # Atlanan klasör sayacı
        error_count = 0    # Hata sayacı
        
        try:
            # Ana klasörleri listele
            for item in sorted(os.listdir(self.root_path)):
                # ============================================================
                # YENİ: Sistem klasörlerini atla
                # ============================================================
                if should_skip_folder(item):
                    skipped_count += 1
                    continue
                # ============================================================
                
                item_path = os.path.join(self.root_path, item)
                
                try:
                    if os.path.isdir(item_path):
                        # Klasör ikonu belirle
                        icon = "📁"
                        if item.startswith("EPS"):
                            # EPS numarasına göre renk
                            icon = "📂"
                        
                        tree_item = QTreeWidgetItem([f"{icon} {item}"])
                        tree_item.setData(0, Qt.UserRole, item_path)
                        
                        # Alt klasörleri ekle (1 seviye)
                        try:
                            for sub_item in sorted(os.listdir(item_path)):
                                # ============================================================
                                # YENİ: Alt klasörlerde de sistem klasörlerini atla
                                # ============================================================
                                if should_skip_folder(sub_item):
                                    continue
                                # ============================================================
                                
                                sub_path = os.path.join(item_path, sub_item)
                                try:
                                    if os.path.isdir(sub_path):
                                        sub_tree = QTreeWidgetItem([f"  📁 {sub_item}"])
                                        sub_tree.setData(0, Qt.UserRole, sub_path)
                                        tree_item.addChild(sub_tree)
                                except (PermissionError, OSError):
                                    # Erişilemeyen alt klasörleri sessizce atla
                                    continue
                        except (PermissionError, OSError):
                            # Alt klasör listelenemiyor - sessizce geç
                            pass
                        
                        self.tree_folders.addTopLevelItem(tree_item)
                        
                except (PermissionError, OSError) as e:
                    # ============================================================
                    # YENİ: Erişilemeyen klasörleri sessizce atla
                    # ============================================================
                    error_count += 1
                    continue
                    # ============================================================
            
            folder_count = self.tree_folders.topLevelItemCount()
            status_msg = f"✅ {folder_count} ana klasör yüklendi"
            if skipped_count > 0:
                status_msg += f" ({skipped_count} sistem klasörü atlandı)"
            self.lbl_status.setText(status_msg)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Klasörler yüklenirken hata:\n{str(e)}")
            self.lbl_status.setText(f"❌ Hata: {str(e)}")
    
    def _on_folder_clicked(self, item):
        """Klasöre tıklandığında dosyaları listele"""
        folder_path = item.data(0, Qt.UserRole)
        if folder_path and os.path.isdir(folder_path):
            self.current_folder = folder_path
            self._load_files(folder_path)
    
    def _load_files(self, folder_path):
        """Dosyaları yükle"""
        self.table_files.setRowCount(0)
        self.all_files = []
        
        try:
            files = []
            for item in os.listdir(folder_path):
                # ============================================================
                # YENİ: Sistem dosyalarını atla
                # ============================================================
                if item.startswith('.') or item.startswith('~$'):
                    continue
                # ============================================================
                
                item_path = os.path.join(folder_path, item)
                try:
                    if os.path.isfile(item_path):
                        stat = os.stat(item_path)
                        ext = os.path.splitext(item)[1].lower()
                        files.append({
                            'name': item,
                            'path': item_path,
                            'ext': ext,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime)
                        })
                except (PermissionError, OSError):
                    # Erişilemeyen dosyaları atla
                    continue
            
            # Tarihe göre sırala (en yeni üstte)
            files.sort(key=lambda x: x['modified'], reverse=True)
            self.all_files = files
            
            self._display_files(files)
            
            folder_name = os.path.basename(folder_path)
            self.lbl_file_count.setText(f"📄 {folder_name} ({len(files)} dosya)")
            self.lbl_status.setText(f"📂 {folder_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosyalar yüklenirken hata:\n{str(e)}")
    
    def _display_files(self, files):
        """Dosyaları tabloda göster"""
        self.table_files.setRowCount(len(files))
        
        for i, file in enumerate(files):
            # İkon
            icon = FILE_ICONS.get(file['ext'], '📄')
            icon_item = QTableWidgetItem(icon)
            icon_item.setTextAlignment(Qt.AlignCenter)
            self.table_files.setItem(i, 0, icon_item)
            
            # Dosya adı
            name_item = QTableWidgetItem(file['name'])
            name_item.setData(Qt.UserRole, file['path'])
            self.table_files.setItem(i, 1, name_item)
            
            # Tür
            type_text = self._get_file_type(file['ext'])
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignCenter)
            self.table_files.setItem(i, 2, type_item)
            
            # Boyut
            size_text = self._format_size(file['size'])
            size_item = QTableWidgetItem(size_text)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_files.setItem(i, 3, size_item)
            
            # Tarih
            date_text = file['modified'].strftime("%d.%m.%Y %H:%M")
            date_item = QTableWidgetItem(date_text)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table_files.setItem(i, 4, date_item)
            
            # Satır yüksekliği
            self.table_files.setRowHeight(i, 40)
    
    def _get_file_type(self, ext):
        """Dosya türü metni"""
        types = {
            '.pdf': 'PDF',
            '.doc': 'Word',
            '.docx': 'Word',
            '.xls': 'Excel',
            '.xlsx': 'Excel',
            '.xlsm': 'Excel',
            '.ppt': 'PPT',
            '.pptx': 'PPT',
            '.txt': 'Metin',
            '.jpg': 'Resim',
            '.jpeg': 'Resim',
            '.png': 'Resim',
            '.dwg': 'CAD',
            '.dxf': 'CAD',
        }
        return types.get(ext, ext.upper().replace('.', '') if ext else '-')
    
    def _format_size(self, size):
        """Boyut formatla"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.0f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    
    def _filter_files(self):
        """Dosyaları filtrele"""
        search_text = self.txt_search.text().lower()
        filter_type = self.cmb_filter.currentText()
        
        filtered = []
        for file in self.all_files:
            # Arama filtresi
            if search_text and search_text not in file['name'].lower():
                continue
            
            # Tür filtresi
            if filter_type == "PDF" and file['ext'] != '.pdf':
                continue
            elif filter_type == "Word" and file['ext'] not in ['.doc', '.docx']:
                continue
            elif filter_type == "Excel" and file['ext'] not in ['.xls', '.xlsx', '.xlsm']:
                continue
            elif filter_type == "Diğer" and file['ext'] in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.xlsm']:
                continue
            
            filtered.append(file)
        
        self._display_files(filtered)
        self.lbl_file_count.setText(f"📄 {len(filtered)} / {len(self.all_files)} dosya")
    
    def _open_file(self):
        """Dosyayı aç"""
        row = self.table_files.currentRow()
        if row < 0:
            return
        
        file_path = self.table_files.item(row, 1).data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Dosya açılamadı:\n{str(e)}")
    
    def _open_current_folder(self):
        """Mevcut klasörü Windows Explorer'da aç"""
        folder = self.current_folder or self.root_path
        if os.path.exists(folder):
            try:
                subprocess.Popen(f'explorer "{folder}"')
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Klasör açılamadı:\n{str(e)}")
    
    def _show_context_menu(self, position):
        """Sağ tık menüsü"""
        row = self.table_files.currentRow()
        if row < 0:
            return
        
        file_path = self.table_files.item(row, 1).data(Qt.UserRole)
        file_name = self.table_files.item(row, 1).text()
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                color: {brand.TEXT};
            }}
            QMenu::item:selected {{
                background: {brand.PRIMARY};
                color: white;
                border-radius: 4px;
            }}
        """)
        
        action_open = menu.addAction("📂 Aç")
        action_open.triggered.connect(self._open_file)
        
        action_folder = menu.addAction("📁 Klasörde Göster")
        action_folder.triggered.connect(lambda: self._show_in_folder(file_path))
        
        menu.addSeparator()
        
        action_copy = menu.addAction("📋 Yolu Kopyala")
        action_copy.triggered.connect(lambda: self._copy_path(file_path))
        
        action_download = menu.addAction("💾 Farklı Kaydet...")
        action_download.triggered.connect(lambda: self._save_as(file_path, file_name))
        
        menu.exec(QCursor.pos())
    
    def _show_in_folder(self, file_path):
        """Dosyayı klasörde göster"""
        if os.path.exists(file_path):
            subprocess.Popen(f'explorer /select,"{file_path}"')
    
    def _copy_path(self, file_path):
        """Dosya yolunu panoya kopyala"""
        QApplication.clipboard().setText(file_path)
        self.lbl_status.setText(f"✅ Yol kopyalandı: {file_path}")
    
    def _save_as(self, file_path, file_name):
        """Dosyayı farklı kaydet"""
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Farklı Kaydet", file_name, "Tüm Dosyalar (*.*)"
        )
        if save_path:
            try:
                shutil.copy2(file_path, save_path)
                QMessageBox.information(self, "Başarılı", f"Dosya kaydedildi:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Dosya kaydedilemedi:\n{str(e)}")
    
    def _change_root_path(self):
        """Kök dizini değiştir"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Kök Dizin Ayarı")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(f"background: {brand.BG_MAIN};")
        
        layout = QVBoxLayout(dialog)
        
        group = QGroupBox("Doküman Kök Dizini")
        group.setStyleSheet(f"color: {brand.TEXT};")
        group_layout = QVBoxLayout(group)
        
        lbl = QLabel("Kalite dokümanlarının bulunduğu ana klasör yolunu girin:")
        lbl.setStyleSheet(f"color: {brand.TEXT};")
        group_layout.addWidget(lbl)
        
        path_layout = QHBoxLayout()
        txt_path = QLineEdit(self.root_path)
        txt_path.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 10px;
                color: {brand.TEXT};
            }}
        """)
        path_layout.addWidget(txt_path)
        
        btn_browse = QPushButton("Gozat")
        btn_browse.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 8px 16px;
                color: {brand.TEXT};
            }}
        """)
        btn_browse.clicked.connect(lambda: self._browse_folder(txt_path))
        path_layout.addWidget(btn_browse)
        
        group_layout.addLayout(path_layout)
        layout.addWidget(group)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("İptal")
        btn_cancel.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 10px 24px; border-radius: 6px;")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_save = QPushButton("💾 Kaydet")
        btn_save.setStyleSheet(f"background: {brand.SUCCESS}; color: white; padding: 10px 24px; border-radius: 6px; font-weight: bold;")
        btn_save.clicked.connect(lambda: self._save_root_path(dialog, txt_path.text()))
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _browse_folder(self, txt_widget):
        """Klasör seç"""
        folder = QFileDialog.getExistingDirectory(self, "Klasör Seç", self.root_path)
        if folder:
            txt_widget.setText(folder)
    
    def _save_root_path(self, dialog, new_path):
        """Yeni kök dizini kaydet"""
        if not new_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir yol girin!")
            return
        
        if not os.path.exists(new_path):
            reply = QMessageBox.question(
                self, "Uyarı",
                f"Belirtilen yol bulunamadı:\n{new_path}\n\nYine de kaydetmek istiyor musunuz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        self.root_path = new_path
        self.lbl_root.setText(f"📂 {self.root_path}")
        dialog.accept()
        self._load_folders()
