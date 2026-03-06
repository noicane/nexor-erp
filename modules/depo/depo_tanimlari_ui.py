"""
Depo Tanımları Modülü
Redline NexorERP - Tanımlamalar / Depo Yönetimi
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLineEdit, QLabel, QComboBox,
    QFormLayout, QGroupBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QCheckBox, QMessageBox, QDialog,
    QDialogButtonBox, QFrame, QSplitter, QMenu,
    QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from datetime import datetime

from core.database import get_db_connection


class DepoTanimlariWidget(QWidget):
    """Ana Depo Tanımları Widget'ı"""
    
    def __init__(self, theme=None, parent=None):
        super().__init__(parent)
        self.theme = theme or {}
        self.current_depo_id = None
        self.setup_ui()
        self.load_data()
    
    @property
    def conn(self):
        """Her çağrıda yeni veritabanı bağlantısı döndür"""
        return get_db_connection()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Üst Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Ana içerik - Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Sol Panel - Depo Listesi
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Sağ Panel - Detaylar (Tab)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([350, 650])
        layout.addWidget(splitter)
    
    def create_toolbar(self):
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.StyledPanel)
        toolbar.setStyleSheet("""
            QFrame { background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; padding: 5px; }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Depo ara...")
        self.txt_search.setMinimumWidth(200)
        self.txt_search.textChanged.connect(self.filter_list)
        layout.addWidget(self.txt_search)
        
        layout.addStretch()
        
        btn_style = "QPushButton { padding: 8px 16px; border-radius: 4px; font-weight: bold; }"
        
        self.btn_new = QPushButton("➕ Yeni Depo")
        self.btn_new.setStyleSheet(btn_style + "QPushButton { background-color: #4CAF50; color: white; }")
        self.btn_new.clicked.connect(self.new_depo)
        layout.addWidget(self.btn_new)
        
        self.btn_edit = QPushButton("✏️ Düzenle")
        self.btn_edit.setStyleSheet(btn_style + "QPushButton { background-color: #2196F3; color: white; }")
        self.btn_edit.clicked.connect(self.edit_depo)
        self.btn_edit.setEnabled(False)
        layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("🗑️ Sil")
        self.btn_delete.setStyleSheet(btn_style + "QPushButton { background-color: #f44336; color: white; }")
        self.btn_delete.clicked.connect(self.delete_depo)
        self.btn_delete.setEnabled(False)
        layout.addWidget(self.btn_delete)
        
        self.btn_refresh = QPushButton("🔄 Yenile")
        self.btn_refresh.setStyleSheet(btn_style + "QPushButton { background-color: #607D8B; color: white; }")
        self.btn_refresh.clicked.connect(self.load_data)
        layout.addWidget(self.btn_refresh)
        
        return toolbar
    
    def create_left_panel(self):
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        lbl_title = QLabel("📦 Depolar")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(lbl_title)
        
        self.tbl_depolar = QTableWidget()
        self.tbl_depolar.setColumnCount(5)
        self.tbl_depolar.setHorizontalHeaderLabels(["Kod", "Depo Adı", "Tip", "Durum", "id"])
        self.tbl_depolar.setColumnHidden(4, True)
        
        self.tbl_depolar.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_depolar.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_depolar.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_depolar.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.tbl_depolar.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_depolar.setSelectionMode(QTableWidget.SingleSelection)
        self.tbl_depolar.setAlternatingRowColors(True)
        self.setup_table_style(self.tbl_depolar)
        
        self.tbl_depolar.itemSelectionChanged.connect(self.on_selection_changed)
        self.tbl_depolar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tbl_depolar.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.tbl_depolar)
        return panel
    
    def create_right_panel(self):
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ddd; border-radius: 4px; }
            QTabBar::tab { padding: 8px 16px; margin-right: 2px; }
            QTabBar::tab:selected { background-color: #1976D2; color: white; }
        """)
        
        self.tab_genel = self.create_tab_genel()
        self.tabs.addTab(self.tab_genel, "📋 Genel Bilgiler")
        
        self.tab_bolumler = self.create_tab_bolumler()
        self.tabs.addTab(self.tab_bolumler, "🗂️ Bölümler")
        
        self.tab_raflar = self.create_tab_raflar()
        self.tabs.addTab(self.tab_raflar, "📚 Raflar")
        
        self.tab_sorumlular = self.create_tab_sorumlular()
        self.tabs.addTab(self.tab_sorumlular, "👥 Sorumlular")
        
        layout.addWidget(self.tabs)
        return panel
    
    def create_tab_genel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        self.lbl_no_selection = QLabel("← Listeden bir depo seçin")
        self.lbl_no_selection.setStyleSheet("font-size: 16px; color: #757575; padding: 50px;")
        self.lbl_no_selection.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_no_selection)
        
        self.detail_container = QWidget()
        detail_layout = QVBoxLayout(self.detail_container)
        self.detail_container.hide()
        
        # Temel Bilgiler
        grp_temel = QGroupBox("Temel Bilgiler")
        form1 = QFormLayout(grp_temel)
        self.lbl_kod = QLabel("-")
        self.lbl_ad = QLabel("-")
        self.lbl_tip = QLabel("-")
        self.lbl_durum = QLabel("-")
        form1.addRow("Depo Kodu:", self.lbl_kod)
        form1.addRow("Depo Adı:", self.lbl_ad)
        form1.addRow("Depo Tipi:", self.lbl_tip)
        form1.addRow("Durum:", self.lbl_durum)
        detail_layout.addWidget(grp_temel)
        
        # Kapasite
        grp_kapasite = QGroupBox("Kapasite Bilgileri")
        form2 = QFormLayout(grp_kapasite)
        self.lbl_alan = QLabel("-")
        self.lbl_palet = QLabel("-")
        self.lbl_ton = QLabel("-")
        form2.addRow("Alan (m²):", self.lbl_alan)
        form2.addRow("Palet Kapasitesi:", self.lbl_palet)
        form2.addRow("Ton Kapasitesi:", self.lbl_ton)
        detail_layout.addWidget(grp_kapasite)
        
        # İstatistikler
        grp_istat = QGroupBox("İstatistikler")
        form3 = QFormLayout(grp_istat)
        self.lbl_bolum_sayisi = QLabel("-")
        self.lbl_raf_sayisi = QLabel("-")
        self.lbl_sorumlu_sayisi = QLabel("-")
        form3.addRow("Bölüm Sayısı:", self.lbl_bolum_sayisi)
        form3.addRow("Raf Sayısı:", self.lbl_raf_sayisi)
        form3.addRow("Sorumlu Sayısı:", self.lbl_sorumlu_sayisi)
        detail_layout.addWidget(grp_istat)
        
        detail_layout.addStretch()
        layout.addWidget(self.detail_container)
        return widget
    
    def create_tab_bolumler(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        toolbar = QHBoxLayout()
        btn_add = QPushButton("➕ Bölüm Ekle")
        btn_add.clicked.connect(self.add_bolum)
        toolbar.addWidget(btn_add)
        btn_edit = QPushButton("✏️ Düzenle")
        btn_edit.clicked.connect(self.edit_bolum)
        toolbar.addWidget(btn_edit)
        btn_del = QPushButton("🗑️ Sil")
        btn_del.clicked.connect(self.delete_bolum)
        toolbar.addWidget(btn_del)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.tbl_bolumler = QTableWidget()
        self.tbl_bolumler.setColumnCount(6)
        self.tbl_bolumler.setHorizontalHeaderLabels(["Kod", "Bölüm Adı", "Kat", "Tip", "Alan (m²)", "id"])
        self.tbl_bolumler.setColumnHidden(5, True)
        self.tbl_bolumler.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_bolumler.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_bolumler.setAlternatingRowColors(True)
        self.setup_table_style(self.tbl_bolumler)
        layout.addWidget(self.tbl_bolumler)
        return widget
    
    def create_tab_raflar(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        toolbar = QHBoxLayout()
        btn_add = QPushButton("➕ Raf Ekle")
        btn_add.clicked.connect(self.add_raf)
        toolbar.addWidget(btn_add)
        btn_bulk = QPushButton("📊 Toplu Raf Oluştur")
        btn_bulk.clicked.connect(self.bulk_create_raflar)
        toolbar.addWidget(btn_bulk)
        btn_edit = QPushButton("✏️ Düzenle")
        btn_edit.clicked.connect(self.edit_raf)
        toolbar.addWidget(btn_edit)
        btn_del = QPushButton("🗑️ Sil")
        btn_del.clicked.connect(self.delete_raf)
        toolbar.addWidget(btn_del)
        toolbar.addStretch()
        
        toolbar.addWidget(QLabel("Bölüm:"))
        self.cmb_bolum_filter = QComboBox()
        self.cmb_bolum_filter.addItem("Tümü", None)
        self.cmb_bolum_filter.currentIndexChanged.connect(self.load_raflar)
        toolbar.addWidget(self.cmb_bolum_filter)
        layout.addLayout(toolbar)
        
        self.tbl_raflar = QTableWidget()
        self.tbl_raflar.setColumnCount(9)
        self.tbl_raflar.setHorizontalHeaderLabels(["Kod", "Barkod", "Bölüm", "Koridor", "Sıra", "Kat", "Dolu", "Rezerve", "id"])
        self.tbl_raflar.setColumnHidden(8, True)
        self.tbl_raflar.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_raflar.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_raflar.setAlternatingRowColors(True)
        self.setup_table_style(self.tbl_raflar)
        layout.addWidget(self.tbl_raflar)
        return widget
    
    def create_tab_sorumlular(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        toolbar = QHBoxLayout()
        btn_add = QPushButton("➕ Sorumlu Ekle")
        btn_add.clicked.connect(self.add_sorumlu)
        toolbar.addWidget(btn_add)
        btn_edit = QPushButton("✏️ Düzenle")
        btn_edit.clicked.connect(self.edit_sorumlu)
        toolbar.addWidget(btn_edit)
        btn_del = QPushButton("🗑️ Kaldır")
        btn_del.clicked.connect(self.delete_sorumlu)
        toolbar.addWidget(btn_del)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.tbl_sorumlular = QTableWidget()
        self.tbl_sorumlular.setColumnCount(7)
        self.tbl_sorumlular.setHorizontalHeaderLabels(["Personel", "Sorumluluk Tipi", "Başlangıç", "Bitiş", "Yetki", "Durum", "id"])
        self.tbl_sorumlular.setColumnHidden(6, True)
        self.tbl_sorumlular.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_sorumlular.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_sorumlular.setAlternatingRowColors(True)
        self.setup_table_style(self.tbl_sorumlular)
        layout.addWidget(self.tbl_sorumlular)
        return widget
    
    def setup_table_style(self, table):
        table.setStyleSheet("""
            QTableWidget { gridline-color: #e0e0e0; font-size: 12px; }
            QTableWidget::item:selected { background-color: #1976D2; color: white; }
            QHeaderView::section { background-color: #37474F; color: white; padding: 8px; font-weight: bold; border: none; }
        """)
    
    # ==================== VERİ İŞLEMLERİ ====================
    
    def load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, depo_kodu, depo_adi, depo_tipi, aktif_mi, renk_kodu
                FROM tanim.vw_depolar ORDER BY sira_no, depo_kodu
            """)
            
            rows = cursor.fetchall()
            self.tbl_depolar.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.tbl_depolar.setItem(i, 0, QTableWidgetItem(row.depo_kodu))
                self.tbl_depolar.setItem(i, 1, QTableWidgetItem(row.depo_adi))
                self.tbl_depolar.setItem(i, 2, QTableWidgetItem(row.depo_tipi or "-"))
                
                durum = "✅ Aktif" if row.aktif_mi else "❌ Pasif"
                item_durum = QTableWidgetItem(durum)
                if not row.aktif_mi:
                    item_durum.setForeground(QColor("#9E9E9E"))
                self.tbl_depolar.setItem(i, 3, item_durum)
                self.tbl_depolar.setItem(i, 4, QTableWidgetItem(str(row.id)))
                
                if row.renk_kodu:
                    item = self.tbl_depolar.item(i, 0)
                    if item:
                        item.setBackground(QColor(row.renk_kodu).lighter(180))
            
            cursor.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def on_selection_changed(self):
        selected = self.tbl_depolar.selectedItems()
        if selected:
            row = selected[0].row()
            self.current_depo_id = int(self.tbl_depolar.item(row, 4).text())
            self.btn_edit.setEnabled(True)
            self.btn_delete.setEnabled(True)
            self.load_depo_details()
        else:
            self.current_depo_id = None
            self.btn_edit.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.lbl_no_selection.show()
            self.detail_container.hide()
    
    def load_depo_details(self):
        if not self.current_depo_id:
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tanim.vw_depolar WHERE id = ?", (self.current_depo_id,))
            row = cursor.fetchone()
            
            if row:
                self.lbl_no_selection.hide()
                self.detail_container.show()
                
                self.lbl_kod.setText(row.depo_kodu)
                self.lbl_ad.setText(row.depo_adi)
                self.lbl_tip.setText(row.depo_tipi or "-")
                self.lbl_durum.setText("✅ Aktif" if row.aktif_mi else "❌ Pasif")
                self.lbl_alan.setText(f"{row.alan_m2:,.2f}" if row.alan_m2 else "-")
                self.lbl_palet.setText(f"{row.kapasite_palet:,}" if row.kapasite_palet else "-")
                self.lbl_ton.setText(f"{row.kapasite_ton:,.2f}" if row.kapasite_ton else "-")
                self.lbl_bolum_sayisi.setText(str(row.bolum_sayisi or 0))
                self.lbl_raf_sayisi.setText(str(row.raf_sayisi or 0))
                self.lbl_sorumlu_sayisi.setText(str(row.sorumlu_sayisi or 0))
            
            cursor.close()
            self.load_bolumler()
            self.load_raflar()
            self.load_sorumlular()
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Detay yüklenirken hata: {str(e)}")
    
    def load_bolumler(self):
        if not self.current_depo_id:
            self.tbl_bolumler.setRowCount(0)
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad, kat_no, bolum_tipi, alan_m2
                FROM tanim.depo_bolumleri WHERE depo_id = ? AND aktif_mi = 1 ORDER BY sira_no, kod
            """, (self.current_depo_id,))
            
            rows = cursor.fetchall()
            self.tbl_bolumler.setRowCount(len(rows))
            
            self.cmb_bolum_filter.clear()
            self.cmb_bolum_filter.addItem("Tümü", None)
            
            for i, row in enumerate(rows):
                self.tbl_bolumler.setItem(i, 0, QTableWidgetItem(row.kod))
                self.tbl_bolumler.setItem(i, 1, QTableWidgetItem(row.ad))
                self.tbl_bolumler.setItem(i, 2, QTableWidgetItem(str(row.kat_no) if row.kat_no is not None else "-"))
                self.tbl_bolumler.setItem(i, 3, QTableWidgetItem(row.bolum_tipi or "-"))
                self.tbl_bolumler.setItem(i, 4, QTableWidgetItem(f"{row.alan_m2:,.2f}" if row.alan_m2 else "-"))
                self.tbl_bolumler.setItem(i, 5, QTableWidgetItem(str(row.id)))
                self.cmb_bolum_filter.addItem(f"{row.kod} - {row.ad}", row.id)
            
            cursor.close()
        except Exception as e:
            print(f"Bölüm yükleme hatası: {e}")
    
    def load_raflar(self):
        if not self.current_depo_id:
            self.tbl_raflar.setRowCount(0)
            return
        
        try:
            cursor = self.conn.cursor()
            bolum_id = self.cmb_bolum_filter.currentData()
            
            query = """
                SELECT r.id, r.kod, r.barkod, b.ad as bolum_adi, r.koridor, r.sira, r.kat, r.dolu_mu, r.rezerve_mi
                FROM tanim.depo_raflari r
                LEFT JOIN tanim.depo_bolumleri b ON r.bolum_id = b.id
                WHERE r.depo_id = ? AND r.aktif_mi = 1
            """
            params = [self.current_depo_id]
            
            if bolum_id:
                query += " AND r.bolum_id = ?"
                params.append(bolum_id)
            
            query += " ORDER BY r.koridor, r.sira, r.kat"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            self.tbl_raflar.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.tbl_raflar.setItem(i, 0, QTableWidgetItem(row.kod))
                self.tbl_raflar.setItem(i, 1, QTableWidgetItem(row.barkod or "-"))
                self.tbl_raflar.setItem(i, 2, QTableWidgetItem(row.bolum_adi or "-"))
                self.tbl_raflar.setItem(i, 3, QTableWidgetItem(row.koridor or "-"))
                self.tbl_raflar.setItem(i, 4, QTableWidgetItem(str(row.sira) if row.sira else "-"))
                self.tbl_raflar.setItem(i, 5, QTableWidgetItem(str(row.kat) if row.kat else "-"))
                self.tbl_raflar.setItem(i, 6, QTableWidgetItem("✅" if row.dolu_mu else "➖"))
                self.tbl_raflar.setItem(i, 7, QTableWidgetItem("🔒" if row.rezerve_mi else "➖"))
                self.tbl_raflar.setItem(i, 8, QTableWidgetItem(str(row.id)))
            
            cursor.close()
        except Exception as e:
            print(f"Raf yükleme hatası: {e}")
    
    def load_sorumlular(self):
        if not self.current_depo_id:
            self.tbl_sorumlular.setRowCount(0)
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT ds.id, ds.personel_id, ds.sorumluluk_tipi, ds.baslangic_tarihi, ds.bitis_tarihi,
                       ds.tam_yetki_mi, ds.giris_yetkisi, ds.cikis_yetkisi, ds.transfer_yetkisi, ds.sayim_yetkisi, ds.aktif_mi
                FROM tanim.depo_sorumlulari ds WHERE ds.depo_id = ? ORDER BY ds.aktif_mi DESC, ds.sorumluluk_tipi
            """, (self.current_depo_id,))
            
            rows = cursor.fetchall()
            self.tbl_sorumlular.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.tbl_sorumlular.setItem(i, 0, QTableWidgetItem(f"Personel #{row.personel_id}"))
                self.tbl_sorumlular.setItem(i, 1, QTableWidgetItem(row.sorumluluk_tipi))
                self.tbl_sorumlular.setItem(i, 2, QTableWidgetItem(row.baslangic_tarihi.strftime("%d.%m.%Y") if row.baslangic_tarihi else "-"))
                self.tbl_sorumlular.setItem(i, 3, QTableWidgetItem(row.bitis_tarihi.strftime("%d.%m.%Y") if row.bitis_tarihi else "-"))
                
                yetkiler = []
                if row.tam_yetki_mi:
                    yetkiler.append("Tam")
                else:
                    if row.giris_yetkisi: yetkiler.append("G")
                    if row.cikis_yetkisi: yetkiler.append("Ç")
                    if row.transfer_yetkisi: yetkiler.append("T")
                    if row.sayim_yetkisi: yetkiler.append("S")
                
                self.tbl_sorumlular.setItem(i, 4, QTableWidgetItem("/".join(yetkiler) or "-"))
                self.tbl_sorumlular.setItem(i, 5, QTableWidgetItem("✅ Aktif" if row.aktif_mi else "❌ Pasif"))
                self.tbl_sorumlular.setItem(i, 6, QTableWidgetItem(str(row.id)))
            
            cursor.close()
        except Exception as e:
            print(f"Sorumlu yükleme hatası: {e}")
    
    def filter_list(self, text):
        for row in range(self.tbl_depolar.rowCount()):
            match = False
            for col in range(3):
                item = self.tbl_depolar.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.tbl_depolar.setRowHidden(row, not match)
    
    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("✏️ Düzenle", self.edit_depo)
        menu.addSeparator()
        menu.addAction("🔄 Aktif/Pasif Yap", self.toggle_status)
        menu.addSeparator()
        menu.addAction("🗑️ Sil", self.delete_depo)
        menu.exec_(self.tbl_depolar.mapToGlobal(pos))
    
    # ==================== CRUD ====================
    
    def new_depo(self):
        dialog = DepoEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
    
    def edit_depo(self):
        if not self.current_depo_id:
            return
        dialog = DepoEditDialog(depo_id=self.current_depo_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
            self.load_depo_details()
    
    def delete_depo(self):
        if not self.current_depo_id:
            return
        reply = QMessageBox.question(self, "Depo Sil", "Bu depoyu silmek istediğinizden emin misiniz?")
        if reply == QMessageBox.Yes:
            try:
                cursor = self.conn.cursor()
                cursor.execute("UPDATE tanim.depolar SET silindi_mi = 1, silinme_tarihi = GETDATE() WHERE id = ?", (self.current_depo_id,))
                self.conn.commit()
                cursor.close()
                QMessageBox.information(self, "Başarılı", "Depo silindi.")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
    
    def toggle_status(self):
        if not self.current_depo_id:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE tanim.depolar SET aktif_mi = CASE WHEN aktif_mi = 1 THEN 0 ELSE 1 END WHERE id = ?", (self.current_depo_id,))
            self.conn.commit()
            cursor.close()
            self.load_data()
            self.load_depo_details()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    # Bölüm işlemleri
    def add_bolum(self):
        if not self.current_depo_id:
            QMessageBox.warning(self, "Uyarı", "Önce bir depo seçin.")
            return
        dialog = BolumEditDialog(self.current_depo_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_bolumler()
            self.load_depo_details()
    
    def edit_bolum(self):
        selected = self.tbl_bolumler.selectedItems()
        if not selected:
            return
        bolum_id = int(self.tbl_bolumler.item(selected[0].row(), 5).text())
        dialog = BolumEditDialog(self.current_depo_id, bolum_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_bolumler()
    
    def delete_bolum(self):
        selected = self.tbl_bolumler.selectedItems()
        if not selected:
            return
        reply = QMessageBox.question(self, "Bölüm Sil", "Bu bölümü silmek istiyor musunuz?")
        if reply == QMessageBox.Yes:
            bolum_id = int(self.tbl_bolumler.item(selected[0].row(), 5).text())
            try:
                cursor = self.conn.cursor()
                cursor.execute("UPDATE tanim.depo_bolumleri SET aktif_mi = 0 WHERE id = ?", (bolum_id,))
                self.conn.commit()
                cursor.close()
                self.load_bolumler()
                self.load_depo_details()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    # Raf işlemleri
    def add_raf(self):
        if not self.current_depo_id:
            QMessageBox.warning(self, "Uyarı", "Önce bir depo seçin.")
            return
        dialog = RafEditDialog(self.current_depo_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_raflar()
            self.load_depo_details()
    
    def edit_raf(self):
        selected = self.tbl_raflar.selectedItems()
        if not selected:
            return
        raf_id = int(self.tbl_raflar.item(selected[0].row(), 8).text())
        dialog = RafEditDialog(self.current_depo_id, raf_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_raflar()
    
    def delete_raf(self):
        selected = self.tbl_raflar.selectedItems()
        if not selected:
            return
        reply = QMessageBox.question(self, "Raf Sil", "Bu rafı silmek istiyor musunuz?")
        if reply == QMessageBox.Yes:
            raf_id = int(self.tbl_raflar.item(selected[0].row(), 8).text())
            try:
                cursor = self.conn.cursor()
                cursor.execute("UPDATE tanim.depo_raflari SET aktif_mi = 0 WHERE id = ?", (raf_id,))
                self.conn.commit()
                cursor.close()
                self.load_raflar()
                self.load_depo_details()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def bulk_create_raflar(self):
        if not self.current_depo_id:
            QMessageBox.warning(self, "Uyarı", "Önce bir depo seçin.")
            return
        dialog = BulkRafDialog(self.current_depo_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_raflar()
            self.load_depo_details()
    
    # Sorumlu işlemleri
    def add_sorumlu(self):
        if not self.current_depo_id:
            QMessageBox.warning(self, "Uyarı", "Önce bir depo seçin.")
            return
        dialog = SorumluEditDialog(self.current_depo_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_sorumlular()
            self.load_depo_details()
    
    def edit_sorumlu(self):
        selected = self.tbl_sorumlular.selectedItems()
        if not selected:
            return
        sorumlu_id = int(self.tbl_sorumlular.item(selected[0].row(), 6).text())
        dialog = SorumluEditDialog(self.current_depo_id, sorumlu_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_sorumlular()
    
    def delete_sorumlu(self):
        selected = self.tbl_sorumlular.selectedItems()
        if not selected:
            return
        reply = QMessageBox.question(self, "Sorumlu Kaldır", "Bu sorumluyu kaldırmak istiyor musunuz?")
        if reply == QMessageBox.Yes:
            sorumlu_id = int(self.tbl_sorumlular.item(selected[0].row(), 6).text())
            try:
                cursor = self.conn.cursor()
                cursor.execute("UPDATE tanim.depo_sorumlulari SET aktif_mi = 0 WHERE id = ?", (sorumlu_id,))
                self.conn.commit()
                cursor.close()
                self.load_sorumlular()
                self.load_depo_details()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))


# ==================== DİYALOGLAR ====================

class DepoEditDialog(QDialog):
    def __init__(self, depo_id=None, parent=None):
        super().__init__(parent)
        self.depo_id = depo_id
        self.setWindowTitle("Yeni Depo" if not depo_id else "Depo Düzenle")
        self.setMinimumWidth(500)
        self.setup_ui()
        if depo_id:
            self.load_data()
    
    @property
    def conn(self):
        """Her çağrıda yeni veritabanı bağlantısı döndür"""
        return get_db_connection()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.txt_kod = QLineEdit()
        self.txt_kod.setMaxLength(20)
        form.addRow("Depo Kodu*:", self.txt_kod)
        
        self.txt_ad = QLineEdit()
        self.txt_ad.setMaxLength(100)
        form.addRow("Depo Adı*:", self.txt_ad)
        
        self.txt_kisa_ad = QLineEdit()
        self.txt_kisa_ad.setMaxLength(30)
        form.addRow("Kısa Ad:", self.txt_kisa_ad)
        
        self.cmb_tip = QComboBox()
        self.load_depo_tipleri()
        form.addRow("Depo Tipi*:", self.cmb_tip)
        
        self.spn_alan = QDoubleSpinBox()
        self.spn_alan.setRange(0, 999999)
        self.spn_alan.setSuffix(" m²")
        form.addRow("Alan:", self.spn_alan)
        
        self.spn_palet = QSpinBox()
        self.spn_palet.setRange(0, 99999)
        form.addRow("Palet Kapasitesi:", self.spn_palet)
        
        self.spn_sira = QSpinBox()
        self.spn_sira.setRange(0, 999)
        form.addRow("Sıra No:", self.spn_sira)
        
        self.txt_renk = QLineEdit()
        self.txt_renk.setPlaceholderText("#RRGGBB")
        form.addRow("Renk Kodu:", self.txt_renk)
        
        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        form.addRow("", self.chk_aktif)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_depo_tipleri(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, ad FROM tanim.depo_tipleri WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_tip.addItem(row.ad, row.id)
            cursor.close()
        except:
            pass
    
    def load_data(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tanim.depolar WHERE id = ?", (self.depo_id,))
            row = cursor.fetchone()
            if row:
                self.txt_kod.setText(row.kod)
                self.txt_ad.setText(row.ad)
                self.txt_kisa_ad.setText(row.kisa_ad or "")
                idx = self.cmb_tip.findData(row.depo_tipi_id)
                if idx >= 0:
                    self.cmb_tip.setCurrentIndex(idx)
                self.spn_alan.setValue(float(row.alan_m2 or 0))
                self.spn_palet.setValue(int(row.kapasite_palet or 0))
                self.spn_sira.setValue(int(row.sira_no or 0))
                self.txt_renk.setText(row.renk_kodu or "")
                self.chk_aktif.setChecked(row.aktif_mi)
            cursor.close()
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Veri yüklenemedi: {e}")
    
    def save(self):
        if not self.txt_kod.text().strip():
            QMessageBox.warning(self, "Uyarı", "Depo kodu zorunludur.")
            return
        if not self.txt_ad.text().strip():
            QMessageBox.warning(self, "Uyarı", "Depo adı zorunludur.")
            return
        
        try:
            cursor = self.conn.cursor()
            if self.depo_id:
                cursor.execute("""
                    UPDATE tanim.depolar SET kod = ?, ad = ?, kisa_ad = ?, depo_tipi_id = ?,
                        alan_m2 = ?, kapasite_palet = ?, sira_no = ?, renk_kodu = ?, aktif_mi = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    self.txt_kod.text().strip(), self.txt_ad.text().strip(),
                    self.txt_kisa_ad.text().strip() or None, self.cmb_tip.currentData(),
                    self.spn_alan.value() or None, self.spn_palet.value() or None,
                    self.spn_sira.value() or None, self.txt_renk.text().strip() or None,
                    self.chk_aktif.isChecked(), self.depo_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO tanim.depolar (kod, ad, kisa_ad, depo_tipi_id, alan_m2, kapasite_palet, sira_no, renk_kodu, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.txt_kod.text().strip(), self.txt_ad.text().strip(),
                    self.txt_kisa_ad.text().strip() or None, self.cmb_tip.currentData(),
                    self.spn_alan.value() or None, self.spn_palet.value() or None,
                    self.spn_sira.value() or None, self.txt_renk.text().strip() or None,
                    self.chk_aktif.isChecked()
                ))
            
            self.conn.commit()
            cursor.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {str(e)}")


class BolumEditDialog(QDialog):
    def __init__(self, depo_id, bolum_id=None, parent=None):
        super().__init__(parent)
        self.depo_id = depo_id
        self.bolum_id = bolum_id
        self.setWindowTitle("Yeni Bölüm" if not bolum_id else "Bölüm Düzenle")
        self.setMinimumWidth(400)
        self.setup_ui()
        if bolum_id:
            self.load_data()
    
    @property
    def conn(self):
        """Her çağrıda yeni veritabanı bağlantısı döndür"""
        return get_db_connection()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.txt_kod = QLineEdit()
        form.addRow("Bölüm Kodu*:", self.txt_kod)
        
        self.txt_ad = QLineEdit()
        form.addRow("Bölüm Adı*:", self.txt_ad)
        
        self.spn_kat = QSpinBox()
        self.spn_kat.setRange(-5, 20)
        form.addRow("Kat No:", self.spn_kat)
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["Depolama", "Sevkiyat", "Kabul", "Hazırlık", "Karantina"])
        form.addRow("Bölüm Tipi:", self.cmb_tip)
        
        self.spn_alan = QDoubleSpinBox()
        self.spn_alan.setRange(0, 99999)
        self.spn_alan.setSuffix(" m²")
        form.addRow("Alan:", self.spn_alan)
        
        self.spn_sira = QSpinBox()
        self.spn_sira.setRange(0, 999)
        form.addRow("Sıra No:", self.spn_sira)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_data(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tanim.depo_bolumleri WHERE id = ?", (self.bolum_id,))
            row = cursor.fetchone()
            if row:
                self.txt_kod.setText(row.kod)
                self.txt_ad.setText(row.ad)
                self.spn_kat.setValue(row.kat_no or 0)
                idx = self.cmb_tip.findText(row.bolum_tipi or "Depolama")
                self.cmb_tip.setCurrentIndex(max(0, idx))
                self.spn_alan.setValue(float(row.alan_m2 or 0))
                self.spn_sira.setValue(row.sira_no or 0)
            cursor.close()
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", str(e))
    
    def save(self):
        if not self.txt_kod.text().strip() or not self.txt_ad.text().strip():
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad zorunludur.")
            return
        
        try:
            cursor = self.conn.cursor()
            if self.bolum_id:
                cursor.execute("""
                    UPDATE tanim.depo_bolumleri SET kod = ?, ad = ?, kat_no = ?, bolum_tipi = ?,
                        alan_m2 = ?, sira_no = ?, guncelleme_tarihi = GETDATE() WHERE id = ?
                """, (self.txt_kod.text().strip(), self.txt_ad.text().strip(), self.spn_kat.value(),
                      self.cmb_tip.currentText(), self.spn_alan.value() or None, self.spn_sira.value(), self.bolum_id))
            else:
                cursor.execute("""
                    INSERT INTO tanim.depo_bolumleri (depo_id, kod, ad, kat_no, bolum_tipi, alan_m2, sira_no)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (self.depo_id, self.txt_kod.text().strip(), self.txt_ad.text().strip(),
                      self.spn_kat.value(), self.cmb_tip.currentText(), self.spn_alan.value() or None, self.spn_sira.value()))
            self.conn.commit()
            cursor.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class RafEditDialog(QDialog):
    def __init__(self, depo_id, raf_id=None, parent=None):
        super().__init__(parent)
        self.depo_id = depo_id
        self.raf_id = raf_id
        self.setWindowTitle("Yeni Raf" if not raf_id else "Raf Düzenle")
        self.setMinimumWidth(400)
        self.setup_ui()
        self.load_bolumler()
        if raf_id:
            self.load_data()
    
    @property
    def conn(self):
        """Her çağrıda yeni veritabanı bağlantısı döndür"""
        return get_db_connection()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.txt_kod = QLineEdit()
        self.txt_kod.setPlaceholderText("Örn: A-01-03")
        form.addRow("Raf Kodu*:", self.txt_kod)
        
        self.txt_barkod = QLineEdit()
        form.addRow("Barkod:", self.txt_barkod)
        
        self.cmb_bolum = QComboBox()
        form.addRow("Bölüm:", self.cmb_bolum)
        
        self.txt_koridor = QLineEdit()
        form.addRow("Koridor:", self.txt_koridor)
        
        self.spn_sira = QSpinBox()
        self.spn_sira.setRange(0, 999)
        form.addRow("Sıra:", self.spn_sira)
        
        self.spn_kat = QSpinBox()
        self.spn_kat.setRange(0, 20)
        form.addRow("Kat:", self.spn_kat)
        
        self.spn_max_kg = QDoubleSpinBox()
        self.spn_max_kg.setRange(0, 9999)
        self.spn_max_kg.setSuffix(" kg")
        form.addRow("Max Ağırlık:", self.spn_max_kg)
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["Palet", "Kutu", "Küçük Parça", "Özel"])
        form.addRow("Raf Tipi:", self.cmb_tip)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_bolumler(self):
        self.cmb_bolum.clear()
        self.cmb_bolum.addItem("(Bölüm Seçilmedi)", None)
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.depo_bolumleri WHERE depo_id = ? AND aktif_mi = 1 ORDER BY sira_no", (self.depo_id,))
            for row in cursor.fetchall():
                self.cmb_bolum.addItem(f"{row.kod} - {row.ad}", row.id)
            cursor.close()
        except:
            pass
    
    def load_data(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tanim.depo_raflari WHERE id = ?", (self.raf_id,))
            row = cursor.fetchone()
            if row:
                self.txt_kod.setText(row.kod)
                self.txt_barkod.setText(row.barkod or "")
                idx = self.cmb_bolum.findData(row.bolum_id)
                self.cmb_bolum.setCurrentIndex(max(0, idx))
                self.txt_koridor.setText(row.koridor or "")
                self.spn_sira.setValue(row.sira or 0)
                self.spn_kat.setValue(row.kat or 0)
                self.spn_max_kg.setValue(float(row.max_agirlik_kg or 0))
                idx = self.cmb_tip.findText(row.raf_tipi or "Palet")
                self.cmb_tip.setCurrentIndex(max(0, idx))
            cursor.close()
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", str(e))
    
    def save(self):
        if not self.txt_kod.text().strip():
            QMessageBox.warning(self, "Uyarı", "Raf kodu zorunludur.")
            return
        
        try:
            cursor = self.conn.cursor()
            if self.raf_id:
                cursor.execute("""
                    UPDATE tanim.depo_raflari SET kod = ?, barkod = ?, bolum_id = ?, koridor = ?,
                        sira = ?, kat = ?, max_agirlik_kg = ?, raf_tipi = ?, guncelleme_tarihi = GETDATE() WHERE id = ?
                """, (self.txt_kod.text().strip(), self.txt_barkod.text().strip() or None, self.cmb_bolum.currentData(),
                      self.txt_koridor.text().strip() or None, self.spn_sira.value() or None, self.spn_kat.value() or None,
                      self.spn_max_kg.value() or None, self.cmb_tip.currentText(), self.raf_id))
            else:
                cursor.execute("""
                    INSERT INTO tanim.depo_raflari (depo_id, kod, barkod, bolum_id, koridor, sira, kat, max_agirlik_kg, raf_tipi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.depo_id, self.txt_kod.text().strip(), self.txt_barkod.text().strip() or None, self.cmb_bolum.currentData(),
                      self.txt_koridor.text().strip() or None, self.spn_sira.value() or None, self.spn_kat.value() or None,
                      self.spn_max_kg.value() or None, self.cmb_tip.currentText()))
            self.conn.commit()
            cursor.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class BulkRafDialog(QDialog):
    def __init__(self, depo_id, parent=None):
        super().__init__(parent)
        self.depo_id = depo_id
        self.setWindowTitle("Toplu Raf Oluştur")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    @property
    def conn(self):
        """Her çağrıda yeni veritabanı bağlantısı döndür"""
        return get_db_connection()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        info = QLabel("Belirttiğiniz parametrelere göre otomatik raf kodları oluşturulur.")
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)
        
        form = QFormLayout()
        
        self.txt_koridor = QLineEdit()
        self.txt_koridor.setPlaceholderText("Örn: A,B,C veya A-D")
        form.addRow("Koridorlar*:", self.txt_koridor)
        
        layout_sira = QHBoxLayout()
        self.spn_sira_bas = QSpinBox()
        self.spn_sira_bas.setRange(1, 99)
        self.spn_sira_bas.setValue(1)
        self.spn_sira_son = QSpinBox()
        self.spn_sira_son.setRange(1, 99)
        self.spn_sira_son.setValue(10)
        layout_sira.addWidget(self.spn_sira_bas)
        layout_sira.addWidget(QLabel("-"))
        layout_sira.addWidget(self.spn_sira_son)
        form.addRow("Sıra Aralığı*:", layout_sira)
        
        layout_kat = QHBoxLayout()
        self.spn_kat_bas = QSpinBox()
        self.spn_kat_bas.setRange(1, 10)
        self.spn_kat_bas.setValue(1)
        self.spn_kat_son = QSpinBox()
        self.spn_kat_son.setRange(1, 10)
        self.spn_kat_son.setValue(3)
        layout_kat.addWidget(self.spn_kat_bas)
        layout_kat.addWidget(QLabel("-"))
        layout_kat.addWidget(self.spn_kat_son)
        form.addRow("Kat Aralığı*:", layout_kat)
        
        self.txt_format = QLineEdit()
        self.txt_format.setText("{koridor}-{sira:02d}-{kat:02d}")
        form.addRow("Kod Formatı:", self.txt_format)
        
        layout.addLayout(form)
        
        self.lbl_preview = QLabel("Önizleme: -")
        self.lbl_preview.setStyleSheet("background: #f5f5f5; padding: 10px; border-radius: 4px;")
        layout.addWidget(self.lbl_preview)
        
        self.txt_koridor.textChanged.connect(self.update_preview)
        self.spn_sira_bas.valueChanged.connect(self.update_preview)
        self.spn_sira_son.valueChanged.connect(self.update_preview)
        self.spn_kat_bas.valueChanged.connect(self.update_preview)
        self.spn_kat_son.valueChanged.connect(self.update_preview)
        self.update_preview()
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.create_raflar)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def update_preview(self):
        koridorlar = self.parse_koridorlar()
        sira_count = self.spn_sira_son.value() - self.spn_sira_bas.value() + 1
        kat_count = self.spn_kat_son.value() - self.spn_kat_bas.value() + 1
        total = len(koridorlar) * sira_count * kat_count
        
        preview = f"Toplam {total} raf oluşturulacak"
        if koridorlar:
            try:
                first = self.txt_format.text().format(koridor=koridorlar[0], sira=self.spn_sira_bas.value(), kat=self.spn_kat_bas.value())
                last = self.txt_format.text().format(koridor=koridorlar[-1], sira=self.spn_sira_son.value(), kat=self.spn_kat_son.value())
                preview += f"\nİlk: {first}, Son: {last}"
            except:
                preview += "\nFormat hatası!"
        self.lbl_preview.setText(preview)
    
    def parse_koridorlar(self):
        text = self.txt_koridor.text().strip().upper()
        if not text:
            return []
        if ',' in text:
            return [k.strip() for k in text.split(',')]
        if '-' in text:
            parts = text.split('-')
            if len(parts) == 2 and len(parts[0]) == 1 and len(parts[1]) == 1:
                return [chr(i) for i in range(ord(parts[0]), ord(parts[1]) + 1)]
        return [text]
    
    def create_raflar(self):
        koridorlar = self.parse_koridorlar()
        if not koridorlar:
            QMessageBox.warning(self, "Uyarı", "Koridor belirtiniz.")
            return
        
        try:
            cursor = self.conn.cursor()
            count = 0
            for koridor in koridorlar:
                for sira in range(self.spn_sira_bas.value(), self.spn_sira_son.value() + 1):
                    for kat in range(self.spn_kat_bas.value(), self.spn_kat_son.value() + 1):
                        kod = self.txt_format.text().format(koridor=koridor, sira=sira, kat=kat)
                        cursor.execute("INSERT INTO tanim.depo_raflari (depo_id, kod, koridor, sira, kat) VALUES (?, ?, ?, ?, ?)",
                                       (self.depo_id, kod, koridor, sira, kat))
                        count += 1
            self.conn.commit()
            cursor.close()
            QMessageBox.information(self, "Başarılı", f"{count} raf oluşturuldu.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class SorumluEditDialog(QDialog):
    def __init__(self, depo_id, sorumlu_id=None, parent=None):
        super().__init__(parent)
        self.depo_id = depo_id
        self.sorumlu_id = sorumlu_id
        self.setWindowTitle("Yeni Sorumlu" if not sorumlu_id else "Sorumlu Düzenle")
        self.setMinimumWidth(400)
        self.setup_ui()
        if sorumlu_id:
            self.load_data()
    
    @property
    def conn(self):
        """Her çağrıda yeni veritabanı bağlantısı döndür"""
        return get_db_connection()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.cmb_personel = QComboBox()
        self.load_personeller()
        form.addRow("Personel*:", self.cmb_personel)
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["Ana Sorumlu", "Yardımcı", "Vardiya Sorumlusu"])
        form.addRow("Sorumluluk Tipi*:", self.cmb_tip)
        
        self.date_baslangic = QDateEdit()
        self.date_baslangic.setDate(QDate.currentDate())
        self.date_baslangic.setCalendarPopup(True)
        form.addRow("Başlangıç Tarihi:", self.date_baslangic)
        
        self.date_bitis = QDateEdit()
        self.date_bitis.setSpecialValueText("Belirsiz")
        self.date_bitis.setCalendarPopup(True)
        form.addRow("Bitiş Tarihi:", self.date_bitis)
        
        # Yetkiler
        grp_yetki = QGroupBox("Yetkiler")
        yetki_layout = QVBoxLayout(grp_yetki)
        
        self.chk_tam_yetki = QCheckBox("Tam Yetki")
        self.chk_tam_yetki.stateChanged.connect(self.toggle_yetkiler)
        yetki_layout.addWidget(self.chk_tam_yetki)
        
        self.chk_giris = QCheckBox("Giriş Yetkisi")
        self.chk_giris.setChecked(True)
        yetki_layout.addWidget(self.chk_giris)
        
        self.chk_cikis = QCheckBox("Çıkış Yetkisi")
        self.chk_cikis.setChecked(True)
        yetki_layout.addWidget(self.chk_cikis)
        
        self.chk_transfer = QCheckBox("Transfer Yetkisi")
        yetki_layout.addWidget(self.chk_transfer)
        
        self.chk_sayim = QCheckBox("Sayım Yetkisi")
        yetki_layout.addWidget(self.chk_sayim)
        
        form.addRow(grp_yetki)
        
        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        form.addRow("", self.chk_aktif)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_personeller(self):
        self.cmb_personel.clear()
        # Personel tablosu olmadığı için örnek veri
        for i in range(1, 11):
            self.cmb_personel.addItem(f"Personel #{i}", i)
    
    def toggle_yetkiler(self, state):
        enabled = state != Qt.Checked
        self.chk_giris.setEnabled(enabled)
        self.chk_cikis.setEnabled(enabled)
        self.chk_transfer.setEnabled(enabled)
        self.chk_sayim.setEnabled(enabled)
    
    def load_data(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tanim.depo_sorumlulari WHERE id = ?", (self.sorumlu_id,))
            row = cursor.fetchone()
            if row:
                idx = self.cmb_personel.findData(row.personel_id)
                self.cmb_personel.setCurrentIndex(max(0, idx))
                idx = self.cmb_tip.findText(row.sorumluluk_tipi)
                self.cmb_tip.setCurrentIndex(max(0, idx))
                if row.baslangic_tarihi:
                    self.date_baslangic.setDate(QDate(row.baslangic_tarihi.year, row.baslangic_tarihi.month, row.baslangic_tarihi.day))
                self.chk_tam_yetki.setChecked(row.tam_yetki_mi)
                self.chk_giris.setChecked(row.giris_yetkisi)
                self.chk_cikis.setChecked(row.cikis_yetkisi)
                self.chk_transfer.setChecked(row.transfer_yetkisi)
                self.chk_sayim.setChecked(row.sayim_yetkisi)
                self.chk_aktif.setChecked(row.aktif_mi)
            cursor.close()
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", str(e))
    
    def save(self):
        if self.cmb_personel.currentIndex() < 0:
            QMessageBox.warning(self, "Uyarı", "Personel seçiniz.")
            return
        
        try:
            cursor = self.conn.cursor()
            baslangic = self.date_baslangic.date().toPython()
            
            if self.sorumlu_id:
                cursor.execute("""
                    UPDATE tanim.depo_sorumlulari SET personel_id = ?, sorumluluk_tipi = ?,
                        baslangic_tarihi = ?, tam_yetki_mi = ?, giris_yetkisi = ?, cikis_yetkisi = ?,
                        transfer_yetkisi = ?, sayim_yetkisi = ?, aktif_mi = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (self.cmb_personel.currentData(), self.cmb_tip.currentText(), baslangic,
                      self.chk_tam_yetki.isChecked(), self.chk_giris.isChecked(), self.chk_cikis.isChecked(),
                      self.chk_transfer.isChecked(), self.chk_sayim.isChecked(), self.chk_aktif.isChecked(), self.sorumlu_id))
            else:
                cursor.execute("""
                    INSERT INTO tanim.depo_sorumlulari (depo_id, personel_id, sorumluluk_tipi, baslangic_tarihi,
                        tam_yetki_mi, giris_yetkisi, cikis_yetkisi, transfer_yetkisi, sayim_yetkisi, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.depo_id, self.cmb_personel.currentData(), self.cmb_tip.currentText(), baslangic,
                      self.chk_tam_yetki.isChecked(), self.chk_giris.isChecked(), self.chk_cikis.isChecked(),
                      self.chk_transfer.isChecked(), self.chk_sayim.isChecked(), self.chk_aktif.isChecked()))
            
            self.conn.commit()
            cursor.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
