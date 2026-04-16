# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Giriş Kalite Kriterleri Tanım Sayfası
Mal kabulden gelen ürünlerin kalite kontrolünde bakılacak kriterlerin tanımı
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QWidget, QSpinBox, QDoubleSpinBox, QTextEdit, QCheckBox,
    QGridLayout, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class KriterEkleDialog(QDialog):
    """Yeni kriter ekleme/düzenleme dialogu"""
    
    def __init__(self, theme: dict, kriter_data: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.kriter_data = kriter_data
        self.result_data = None
        
        title = "Kriter Düzenle" if kriter_data else "Yeni Kriter Ekle"
        self.setWindowTitle(title)
        self.setMinimumSize(550, 500)
        self.resize(600, 550)
        
        self._setup_ui()
        
        if kriter_data:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QGroupBox {{ 
                color: {brand.TEXT}; font-weight: bold; 
                border: 1px solid {brand.BORDER}; border-radius: 8px; 
                margin-top: 12px; padding-top: 8px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 8px; color: {brand.PRIMARY}; }}
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background: {brand.BG_INPUT}; 
                border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px; color: {brand.TEXT};
            }}
            QCheckBox {{ color: {brand.TEXT}; spacing: 8px; }}
            QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 4px; border: 2px solid {brand.BORDER}; }}
            QCheckBox::indicator:checked {{ background: {brand.PRIMARY}; border-color: {brand.PRIMARY}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Temel Bilgiler
        temel_group = QGroupBox("📋 Kriter Bilgileri")
        temel_layout = QGridLayout(temel_group)
        temel_layout.setSpacing(12)
        
        temel_layout.addWidget(QLabel("Kriter Adı *:"), 0, 0)
        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderText("Örn: Görsel Kontrol, Boyut Ölçümü...")
        temel_layout.addWidget(self.ad_input, 0, 1, 1, 2)
        
        temel_layout.addWidget(QLabel("Kategori:"), 1, 0)
        self.kategori_combo = QComboBox()
        self.kategori_combo.addItem("Tümü", "")
        self.kategori_combo.addItem("Görsel Kontrol", "GORSEL")
        self.kategori_combo.addItem("Boyut Ölçüm", "BOYUT")
        self.kategori_combo.addItem("Yüzey Kalite", "YUZEY")
        self.kategori_combo.addItem("Malzeme Kontrol", "MALZEME")
        self.kategori_combo.addItem("Ambalaj Kontrol", "AMBALAJ")
        self.kategori_combo.addItem("Dokümantasyon", "DOKUMAN")
        self.kategori_combo.addItem("Diğer", "DIGER")
        temel_layout.addWidget(self.kategori_combo, 1, 1, 1, 2)
        
        temel_layout.addWidget(QLabel("Kontrol Tipi:"), 2, 0)
        self.tip_combo = QComboBox()
        self.tip_combo.addItem("Var/Yok (Checkbox)", "CHECKBOX")
        self.tip_combo.addItem("Sayısal Ölçüm", "OLCUM")
        self.tip_combo.addItem("Seçenekli", "SECIM")
        self.tip_combo.currentIndexChanged.connect(self._on_tip_changed)
        temel_layout.addWidget(self.tip_combo, 2, 1, 1, 2)
        
        temel_layout.addWidget(QLabel("Açıklama:"), 3, 0, Qt.AlignTop)
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setMaximumHeight(60)
        self.aciklama_input.setPlaceholderText("Kontrol kriteri hakkında detaylı açıklama...")
        temel_layout.addWidget(self.aciklama_input, 3, 1, 1, 2)
        
        layout.addWidget(temel_group)
        
        # Ölçüm Ayarları
        self.olcum_group = QGroupBox("📏 Ölçüm Ayarları")
        olcum_layout = QGridLayout(self.olcum_group)
        olcum_layout.setSpacing(12)
        
        olcum_layout.addWidget(QLabel("Birim:"), 0, 0)
        self.birim_input = QLineEdit()
        self.birim_input.setPlaceholderText("mm, μm, %, adet...")
        olcum_layout.addWidget(self.birim_input, 0, 1)
        
        olcum_layout.addWidget(QLabel("Min Değer:"), 1, 0)
        self.min_input = QDoubleSpinBox()
        self.min_input.setRange(-999999, 999999)
        self.min_input.setDecimals(4)
        olcum_layout.addWidget(self.min_input, 1, 1)
        
        olcum_layout.addWidget(QLabel("Max Değer:"), 2, 0)
        self.max_input = QDoubleSpinBox()
        self.max_input.setRange(-999999, 999999)
        self.max_input.setDecimals(4)
        olcum_layout.addWidget(self.max_input, 2, 1)
        
        olcum_layout.addWidget(QLabel("Hedef Değer:"), 3, 0)
        self.hedef_input = QDoubleSpinBox()
        self.hedef_input.setRange(-999999, 999999)
        self.hedef_input.setDecimals(4)
        olcum_layout.addWidget(self.hedef_input, 3, 1)
        
        self.olcum_group.setVisible(False)
        layout.addWidget(self.olcum_group)
        
        # Seçenek Ayarları
        self.secim_group = QGroupBox("📝 Seçenek Ayarları")
        secim_layout = QVBoxLayout(self.secim_group)
        secim_layout.addWidget(QLabel("Seçenekler (her satıra bir seçenek):"))
        self.secenekler_input = QTextEdit()
        self.secenekler_input.setMaximumHeight(80)
        self.secenekler_input.setPlaceholderText("Uygun\nUygun Değil\nKoşullu Kabul")
        secim_layout.addWidget(self.secenekler_input)
        self.secim_group.setVisible(False)
        layout.addWidget(self.secim_group)
        
        # Ek Ayarlar
        ayar_group = QGroupBox("⚙️ Ek Ayarlar")
        ayar_layout = QGridLayout(ayar_group)
        ayar_layout.setSpacing(12)
        
        self.zorunlu_check = QCheckBox("Zorunlu Kriter")
        self.zorunlu_check.setChecked(True)
        ayar_layout.addWidget(self.zorunlu_check, 0, 0)
        
        self.kritik_check = QCheckBox("Kritik Kriter")
        self.kritik_check.setToolTip("Bu kriterin başarısız olması durumunda otomatik RED")
        ayar_layout.addWidget(self.kritik_check, 0, 1)
        
        self.aktif_check = QCheckBox("Aktif")
        self.aktif_check.setChecked(True)
        ayar_layout.addWidget(self.aktif_check, 1, 0)
        
        ayar_layout.addWidget(QLabel("Sıra No:"), 1, 1)
        self.sira_input = QSpinBox()
        self.sira_input.setRange(1, 999)
        self.sira_input.setValue(1)
        ayar_layout.addWidget(self.sira_input, 1, 2)
        
        layout.addWidget(ayar_group)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 10px 24px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(f"background: {brand.PRIMARY}; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_tip_changed(self, index):
        tip = self.tip_combo.currentData()
        self.olcum_group.setVisible(tip == "OLCUM")
        self.secim_group.setVisible(tip == "SECIM")
    
    def _load_data(self):
        if not self.kriter_data:
            return
        self.ad_input.setText(self.kriter_data.get('ad', ''))
        self.aciklama_input.setPlainText(self.kriter_data.get('aciklama', ''))
        
        for i in range(self.kategori_combo.count()):
            if self.kategori_combo.itemData(i) == self.kriter_data.get('kategori', ''):
                self.kategori_combo.setCurrentIndex(i)
                break
        
        for i in range(self.tip_combo.count()):
            if self.tip_combo.itemData(i) == self.kriter_data.get('kontrol_tipi', 'CHECKBOX'):
                self.tip_combo.setCurrentIndex(i)
                break
        
        self.birim_input.setText(self.kriter_data.get('birim', ''))
        self.min_input.setValue(self.kriter_data.get('min_deger', 0) or 0)
        self.max_input.setValue(self.kriter_data.get('max_deger', 0) or 0)
        self.hedef_input.setValue(self.kriter_data.get('hedef_deger', 0) or 0)
        
        secenekler = self.kriter_data.get('secenekler', '')
        if secenekler:
            self.secenekler_input.setPlainText(secenekler.replace('|', '\n'))
        
        self.zorunlu_check.setChecked(self.kriter_data.get('zorunlu_mu', True))
        self.kritik_check.setChecked(self.kriter_data.get('kritik_mi', False))
        self.aktif_check.setChecked(self.kriter_data.get('aktif_mi', True))
        self.sira_input.setValue(self.kriter_data.get('sira_no', 1) or 1)
    
    def _save(self):
        ad = self.ad_input.text().strip()
        if not ad:
            QMessageBox.warning(self, "Uyarı", "Kriter adı zorunludur!")
            return
        
        tip = self.tip_combo.currentData()
        secenekler = ""
        if tip == "SECIM":
            secenekler_list = [s.strip() for s in self.secenekler_input.toPlainText().split('\n') if s.strip()]
            if len(secenekler_list) < 2:
                QMessageBox.warning(self, "Uyarı", "En az 2 seçenek girmelisiniz!")
                return
            secenekler = "|".join(secenekler_list)
        
        self.result_data = {
            'ad': ad, 'kategori': self.kategori_combo.currentData(), 'kontrol_tipi': tip,
            'aciklama': self.aciklama_input.toPlainText().strip(),
            'birim': self.birim_input.text().strip() if tip == "OLCUM" else None,
            'min_deger': self.min_input.value() if tip == "OLCUM" else None,
            'max_deger': self.max_input.value() if tip == "OLCUM" else None,
            'hedef_deger': self.hedef_input.value() if tip == "OLCUM" else None,
            'secenekler': secenekler if tip == "SECIM" else None,
            'zorunlu_mu': self.zorunlu_check.isChecked(), 'kritik_mi': self.kritik_check.isChecked(),
            'aktif_mi': self.aktif_check.isChecked(), 'sira_no': self.sira_input.value()
        }
        self.accept()


class GirisKaliteKriterleriPage(BasePage):
    """Giriş Kalite Kontrol Kriterleri Tanım Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Başlık
        header = QHBoxLayout()
        title = QLabel("📋 Giriş Kalite Kriterleri Tanımları")
        title.setStyleSheet(f"color: {brand.TEXT}; font-size: 22px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        
        add_btn = QPushButton("➕ Yeni Kriter")
        add_btn.setStyleSheet(f"background: {brand.SUCCESS}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: bold;")
        add_btn.clicked.connect(self._add_kriter)
        header.addWidget(add_btn)
        layout.addLayout(header)
        
        # Filtre
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border-radius: 10px; padding: 12px; }}")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(12)
        
        filter_layout.addWidget(QLabel("🔍"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Kriter adı ara...")
        self.search_input.setStyleSheet(f"background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px 12px; color: {brand.TEXT}; min-width: 200px;")
        self.search_input.textChanged.connect(self._load_data)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addWidget(QLabel("Kategori:"))
        self.kategori_filter = QComboBox()
        self.kategori_filter.setStyleSheet(f"background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px; color: {brand.TEXT}; min-width: 150px;")
        self.kategori_filter.addItem("Tümü", "")
        self.kategori_filter.addItem("Görsel Kontrol", "GORSEL")
        self.kategori_filter.addItem("Boyut Ölçüm", "BOYUT")
        self.kategori_filter.addItem("Yüzey Kalite", "YUZEY")
        self.kategori_filter.addItem("Malzeme Kontrol", "MALZEME")
        self.kategori_filter.addItem("Ambalaj Kontrol", "AMBALAJ")
        self.kategori_filter.addItem("Dokümantasyon", "DOKUMAN")
        self.kategori_filter.addItem("Diğer", "DIGER")
        self.kategori_filter.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.kategori_filter)
        
        filter_layout.addWidget(QLabel("Durum:"))
        self.durum_filter = QComboBox()
        self.durum_filter.setStyleSheet(f"background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px; color: {brand.TEXT}; min-width: 100px;")
        self.durum_filter.addItem("Tümü", "")
        self.durum_filter.addItem("Aktif", "1")
        self.durum_filter.addItem("Pasif", "0")
        self.durum_filter.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.durum_filter)
        
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px 16px;")
        refresh_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(refresh_btn)
        layout.addWidget(filter_frame)
        
        # İstatistik
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        self.stat_widgets = {}
        for key, label, color in [("toplam", "📋 Toplam Kriter", brand.PRIMARY), ("aktif", "✅ Aktif", brand.SUCCESS), ("kritik", "⚠️ Kritik", brand.WARNING), ("zorunlu", "🔒 Zorunlu", brand.INFO)]:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {color}15; border: 1px solid {color}50; border-radius: 10px; padding: 16px; }}")
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(4)
            value_label = QLabel("0")
            value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
            value_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(value_label)
            title_label = QLabel(label)
            title_label.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: 12px;")
            title_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(title_label)
            self.stat_widgets[key] = value_label
            stats_layout.addWidget(card)
        layout.addLayout(stats_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Sıra", "Kriter Adı", "Kategori", "Kontrol Tipi", "Zorunlu", "Kritik", "Aktif", "İşlemler"])
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 250)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 80)
        self.table.setColumnWidth(8, 150)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 10px; gridline-color: {brand.BORDER}; color: {brand.TEXT}; }}
            QTableWidget::item {{ padding: 8px; }}
            QTableWidget::item:selected {{ background: {brand.PRIMARY}30; }}
            QTableWidget::item:alternate {{ background: {brand.BG_HOVER}; }}
            QHeaderView::section {{ background: {brand.BG_HOVER}; color: {brand.TEXT}; padding: 12px; border: none; font-weight: bold; }}
        """)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'giris_kontrol_kriterleri' AND schema_id = SCHEMA_ID('kalite'))
                BEGIN
                    CREATE TABLE kalite.giris_kontrol_kriterleri (
                        id BIGINT IDENTITY(1,1) PRIMARY KEY, uuid UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
                        sira_no INT NOT NULL DEFAULT 1, ad NVARCHAR(200) NOT NULL, kategori NVARCHAR(40) NULL,
                        kontrol_tipi NVARCHAR(40) NOT NULL DEFAULT 'CHECKBOX', aciklama NVARCHAR(1000) NULL,
                        birim NVARCHAR(40) NULL, min_deger DECIMAL(18,4) NULL, max_deger DECIMAL(18,4) NULL,
                        hedef_deger DECIMAL(18,4) NULL, secenekler NVARCHAR(1000) NULL,
                        zorunlu_mu BIT NOT NULL DEFAULT 1, kritik_mi BIT NOT NULL DEFAULT 0, aktif_mi BIT NOT NULL DEFAULT 1,
                        olusturma_tarihi DATETIME2 NOT NULL DEFAULT GETDATE(), guncelleme_tarihi DATETIME2 NOT NULL DEFAULT GETDATE(),
                        olusturan_id BIGINT NULL, guncelleyen_id BIGINT NULL
                    )
                END
            """)
            conn.commit()
            
            search, kategori, durum = self.search_input.text().strip(), self.kategori_filter.currentData(), self.durum_filter.currentData()
            query = "SELECT id, sira_no, ad, kategori, kontrol_tipi, zorunlu_mu, kritik_mi, aktif_mi FROM kalite.giris_kontrol_kriterleri WHERE 1=1"
            params = []
            if search:
                query += " AND ad LIKE ?"
                params.append(f"%{search}%")
            if kategori:
                query += " AND kategori = ?"
                params.append(kategori)
            if durum:
                query += " AND aktif_mi = ?"
                params.append(int(durum))
            query += " ORDER BY sira_no, ad"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN aktif_mi = 1 THEN 1 ELSE 0 END), SUM(CASE WHEN kritik_mi = 1 THEN 1 ELSE 0 END), SUM(CASE WHEN zorunlu_mu = 1 THEN 1 ELSE 0 END) FROM kalite.giris_kontrol_kriterleri")
            stats = cursor.fetchone()
            conn.close()
            
            if stats:
                self.stat_widgets['toplam'].setText(str(stats[0] or 0))
                self.stat_widgets['aktif'].setText(str(stats[1] or 0))
                self.stat_widgets['kritik'].setText(str(stats[2] or 0))
                self.stat_widgets['zorunlu'].setText(str(stats[3] or 0))
            
            self.table.setRowCount(len(rows))
            kategori_labels = {'GORSEL': 'Görsel Kontrol', 'BOYUT': 'Boyut Ölçüm', 'YUZEY': 'Yüzey Kalite', 'MALZEME': 'Malzeme Kontrol', 'AMBALAJ': 'Ambalaj Kontrol', 'DOKUMAN': 'Dokümantasyon', 'DIGER': 'Diğer'}
            tip_labels = {'CHECKBOX': 'Var/Yok', 'OLCUM': 'Sayısal Ölçüm', 'SECIM': 'Seçenekli'}
            
            for i, row in enumerate(rows):
                id_item = QTableWidgetItem(str(row[0]))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 0, id_item)
                sira_item = QTableWidgetItem(str(row[1] or 1))
                sira_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 1, sira_item)
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.table.setItem(i, 3, QTableWidgetItem(kategori_labels.get(row[3] or '', row[3] or '')))
                self.table.setItem(i, 4, QTableWidgetItem(tip_labels.get(row[4] or 'CHECKBOX', row[4] or '')))
                
                for col, val in [(5, row[5]), (6, row[6]), (7, row[7])]:
                    item = QTableWidgetItem("✅" if val else ("❌" if col == 7 else ""))
                    item.setTextAlignment(Qt.AlignCenter)
                    if col == 7 and not val:
                        item.setForeground(QColor(brand.ERROR))
                    self.table.setItem(i, col, item)
                
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, rid=row[0]: self._edit_kriter(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_kriter(rid), "delete"),
                ])
                self.table.setCellWidget(i, 8, widget)
                self.table.setRowHeight(i, 42)
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
    
    def _add_kriter(self):
        dialog = KriterEkleDialog(self.theme, parent=self)
        if dialog.exec() == QDialog.Accepted and dialog.result_data:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                data = dialog.result_data
                cursor.execute("INSERT INTO kalite.giris_kontrol_kriterleri (sira_no, ad, kategori, kontrol_tipi, aciklama, birim, min_deger, max_deger, hedef_deger, secenekler, zorunlu_mu, kritik_mi, aktif_mi) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (data['sira_no'], data['ad'], data['kategori'], data['kontrol_tipi'], data['aciklama'], data['birim'], data['min_deger'], data['max_deger'], data['hedef_deger'], data['secenekler'], data['zorunlu_mu'], data['kritik_mi'], data['aktif_mi']))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Başarılı", "Kriter başarıyla eklendi!")
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kriter eklenemedi: {e}")
    
    def _edit_kriter(self, kriter_id: int):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, sira_no, ad, kategori, kontrol_tipi, aciklama, birim, min_deger, max_deger, hedef_deger, secenekler, zorunlu_mu, kritik_mi, aktif_mi FROM kalite.giris_kontrol_kriterleri WHERE id = ?", (kriter_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                QMessageBox.warning(self, "Uyarı", "Kriter bulunamadı!")
                return
            kriter_data = {'id': row[0], 'sira_no': row[1], 'ad': row[2], 'kategori': row[3], 'kontrol_tipi': row[4], 'aciklama': row[5], 'birim': row[6], 'min_deger': row[7], 'max_deger': row[8], 'hedef_deger': row[9], 'secenekler': row[10], 'zorunlu_mu': row[11], 'kritik_mi': row[12], 'aktif_mi': row[13]}
            dialog = KriterEkleDialog(self.theme, kriter_data, parent=self)
            if dialog.exec() == QDialog.Accepted and dialog.result_data:
                conn = get_db_connection()
                cursor = conn.cursor()
                data = dialog.result_data
                cursor.execute("UPDATE kalite.giris_kontrol_kriterleri SET sira_no = ?, ad = ?, kategori = ?, kontrol_tipi = ?, aciklama = ?, birim = ?, min_deger = ?, max_deger = ?, hedef_deger = ?, secenekler = ?, zorunlu_mu = ?, kritik_mi = ?, aktif_mi = ?, guncelleme_tarihi = GETDATE() WHERE id = ?",
                    (data['sira_no'], data['ad'], data['kategori'], data['kontrol_tipi'], data['aciklama'], data['birim'], data['min_deger'], data['max_deger'], data['hedef_deger'], data['secenekler'], data['zorunlu_mu'], data['kritik_mi'], data['aktif_mi'], kriter_id))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Başarılı", "Kriter güncellendi!")
                self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kriter güncellenemedi: {e}")
    
    def _delete_kriter(self, kriter_id: int):
        if QMessageBox.question(self, "Onay", "Bu kriteri silmek istediğinize emin misiniz?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM kalite.giris_kontrol_kriterleri WHERE id = ?", (kriter_id,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Başarılı", "Kriter silindi!")
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kriter silinemedi: {e}")
