# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Polivelans Matrisi Sayfası
[MODERNIZED UI - v3.0]

BASİT KULLANIM:
1. Sol listeden personel seç
2. Sağdaki yetkinlikleri işaretle (1-4 seviye)
3. Otomatik kaydedilir

Seviye: 0=Yok, 1=Yetersiz, 2=Eğitimli, 3=Bağımsız, 4=Uzman
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QWidget,
    QScrollArea, QGridLayout, QSpinBox, QDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage, create_action_buttons
from core.database import get_db_connection
from core.nexor_brand import brand


# Seviye tanımları
SEVIYELER = {
    0: ("Yok", "#64748b"),
    1: ("Yetersiz", "#ef4444"),
    2: ("Eğitimli", "#f97316"),
    3: ("Bağımsız", "#eab308"),
    4: ("Uzman", "#22c55e")
}

# Departman bazlı yetkinlikler
DEPARTMAN_YETKINLIKLERI = {
    "KALİTE-EYS": [
        ("EYS-001", "ISO 9001:2015 EYS"),
        ("EYS-002", "Çevre Takibi (ISO 14001)"),
        ("EYS-003", "İSG Takibi (ISO 45001)"),
        ("EYS-004", "Yeni Ürün Devreye Alma"),
        ("EYS-005", "Teknik Resim Okuma"),
        ("EYS-006", "Ürün Kabul/Red Kriterleri"),
        ("EYS-007", "Doküman Hazırlama"),
        ("EYS-008", "Kumpas Kullanımı"),
        ("EYS-009", "Sonuçları Raporlama"),
        ("EYS-010", "İç Tetkik"),
        ("EYS-011", "8D Raporlama"),
        ("EYS-012", "Müşteri Şikayet Yönetimi"),
        ("EYS-013", "Banyo Analizi"),
    ],
    "LABORATUVAR": [
        ("LAB-001", "Tuz Testi Kabini"),
        ("LAB-002", "Kalınlık Ölçüm"),
        ("LAB-003", "Kumpas"),
        ("LAB-004", "pH Metre"),
        ("LAB-005", "Parlaklık Ölçer"),
        ("LAB-006", "Cross-Cut Testi"),
        ("LAB-007", "Kalite Raporu"),
        ("LAB-008", "X-Ray Ölçüm Cihazı"),
        ("LAB-009", "İletkenlik Ölçer"),
        ("LAB-010", "Hull-Cell"),
        ("LAB-011", "Etüv"),
        ("LAB-012", "KTL Banyo Analizleri"),
        ("LAB-013", "ZN Banyo Analizleri"),
    ],
    "HAT": [
        ("HAT-001", "Banyo İlavelerinin Takibi"),
        ("HAT-002", "Üretim Kontrol"),
        ("HAT-003", "Çinko Hattı"),
        ("HAT-004", "Kataforez Hattı"),
        ("HAT-005", "Üretim Plan Takibi"),
        ("HAT-006", "Üretim Sorumlusu"),
    ],
    "KTL-FKK": [
        ("FKK-001", "Grammer Kontrol"),
        ("FKK-002", "T.M Kontrol"),
        ("FKK-003", "Ermetal Kontrol"),
        ("FKK-004", "HTS Kontrol"),
        ("FKK-005", "Profilsan Kontrol"),
        ("FKK-006", "Başarır Kalıp Kontrol"),
        ("FKK-007", "Rötuş Yetkinliği"),
        ("FKK-008", "Genel Kalite Sorumlusu"),
        ("FKK-009", "Vardiya Sorumlusu"),
        ("FKK-010", "Proses Kalite Sorumlusu"),
    ],
    "LOJİSTİK": [
        ("LOJ-001", "Gelen Malzeme Stoklama"),
        ("LOJ-002", "Sevk Malzeme Stoklama"),
        ("LOJ-003", "Çıkış Kalite Kontrol"),
        ("LOJ-004", "Lojistik Sorumlusu"),
        ("LOJ-005", "GKK Sorumlusu"),
        ("LOJ-006", "Elcometer Kullanımı"),
    ],
    "Final Kalite": [
        ("FNK-001", "Görsel Muayene"),
        ("FNK-002", "Boyutsal Kontrol"),
        ("FNK-003", "Kaplama Kalınlık Ölçümü"),
        ("FNK-004", "Yüzey Kalite Kontrolü"),
        ("FNK-005", "Paketleme Kontrolü"),
        ("FNK-006", "Sevk Öncesi Kontrol"),
        ("FNK-007", "Müşteri Şartnameleri"),
        ("FNK-008", "Red Ürün Yönetimi"),
        ("FNK-009", "Kalite Dokümantasyonu"),
        ("FNK-010", "Elcometer Kullanımı"),
    ],
}


class PolivelansPage(BasePage):
    """Polivelans Matrisi - Basit Kullanım"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.selected_personel_id = None
        self.selected_personel_name = None
        self.yetkinlik_widgets = {}
        self._setup_ui()
        QTimer.singleShot(100, self._load_personeller)
    
    def on_page_shown(self):
        """Sayfa her gösterildiğinde personel listesini yenile"""
        self._load_personeller()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_4)

        # ========== SOL PANEL: Personel Listesi ==========
        sol_panel = QFrame()
        sol_panel.setFixedWidth(brand.sp(320))
        sol_panel.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: {brand.R_LG}px; }}")
        sol_layout = QVBoxLayout(sol_panel)
        sol_layout.setContentsMargins(brand.SP_3, brand.SP_3, brand.SP_3, brand.SP_3)
        sol_layout.setSpacing(brand.SP_2)

        # Baslik
        sol_title = QLabel("Personel Listesi")
        sol_title.setStyleSheet(f"font-size: {brand.FS_BODY_LG}px; font-weight: {brand.FW_SEMIBOLD}; color: {brand.TEXT};")
        sol_layout.addWidget(sol_title)

        # Departman filtresi
        dept_layout = QHBoxLayout()
        dept_layout.addWidget(QLabel("Departman:", styleSheet=f"color: {brand.TEXT_DIM}; font-size: {brand.FS_CAPTION}px;"))
        self.cmb_departman = QComboBox()
        self.cmb_departman.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 11px;
            }}
        """)
        self.cmb_departman.addItem("Tüm Departmanlar", None)
        for dept in DEPARTMAN_YETKINLIKLERI.keys():
            self.cmb_departman.addItem(dept, dept)
        self.cmb_departman.currentIndexChanged.connect(self._load_personeller)
        dept_layout.addWidget(self.cmb_departman, 1)
        sol_layout.addLayout(dept_layout)
        
        # Arama
        self.txt_arama = QLineEdit()
        self.txt_arama.setPlaceholderText("🔍 Personel ara...")
        self.txt_arama.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: 4px;
                padding: 8px 10px;
                font-size: 11px;
            }}
        """)
        self.txt_arama.textChanged.connect(self._filter_personeller)
        sol_layout.addWidget(self.txt_arama)
        
        # Personel tablosu
        self.tbl_personel = QTableWidget()
        self.tbl_personel.setColumnCount(2)
        self.tbl_personel.setHorizontalHeaderLabels(["Ad Soyad", "Departman"])
        self.tbl_personel.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_personel.setColumnWidth(1, 100)
        self.tbl_personel.verticalHeader().setVisible(False)
        self.tbl_personel.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_personel.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_personel.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_personel.itemSelectionChanged.connect(self._on_personel_selected)
        self.tbl_personel.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {brand.BORDER};
            }}
            QTableWidget::item:selected {{
                background: {brand.PRIMARY};
            }}
            QHeaderView::section {{
                background: rgba(0,0,0,0.3);
                color: {brand.TEXT_MUTED};
                padding: 8px;
                border: none;
                font-weight: 600;
                font-size: 10px;
            }}
        """)
        sol_layout.addWidget(self.tbl_personel, 1)
        
        layout.addWidget(sol_panel)
        
        # ========== SAĞ PANEL: Yetkinlikler ==========
        sag_panel = QFrame()
        sag_panel.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: {brand.R_LG}px; }}")
        sag_layout = QVBoxLayout(sag_panel)
        sag_layout.setContentsMargins(brand.SP_3, brand.SP_3, brand.SP_3, brand.SP_3)
        sag_layout.setSpacing(brand.SP_2)
        
        # Başlık
        sag_header = QHBoxLayout()
        self.lbl_personel_adi = QLabel("Personel Secin")
        self.lbl_personel_adi.setStyleSheet(f"font-size: {brand.FS_BODY_LG}px; font-weight: {brand.FW_SEMIBOLD}; color: {brand.TEXT};")
        sag_header.addWidget(self.lbl_personel_adi)
        
        # Yetkinlik Yönetimi butonu
        btn_yetkinlik_yonetim = QPushButton("⚙️ Yetkinlik Tanımları")
        btn_yetkinlik_yonetim.setCursor(Qt.PointingHandCursor)
        btn_yetkinlik_yonetim.setStyleSheet(f"""
            QPushButton {{
                background: {brand.INFO};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        btn_yetkinlik_yonetim.clicked.connect(self._show_yetkinlik_yonetimi)
        sag_header.addWidget(btn_yetkinlik_yonetim)
        
        sag_header.addStretch()
        
        # Seviye açıklaması
        for seviye, (ad, renk) in SEVIYELER.items():
            lbl = QLabel(f"  {seviye}={ad}  ")
            lbl.setStyleSheet(f"background: {renk}; color: white; border-radius: 3px; padding: 2px 6px; font-size: 10px;")
            sag_header.addWidget(lbl)
        
        sag_layout.addLayout(sag_header)
        
        # Yetkinlik scroll alanı
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.yetkinlik_container = QWidget()
        self.yetkinlik_layout = QVBoxLayout(self.yetkinlik_container)
        self.yetkinlik_layout.setContentsMargins(0, 0, 0, 0)
        self.yetkinlik_layout.setSpacing(4)
        
        # Başlangıçta boş mesaj
        self.empty_label = QLabel("👆 Sol taraftan bir personel seçin")
        self.empty_label.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 14px; padding: 40px;")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.yetkinlik_layout.addWidget(self.empty_label)
        self.yetkinlik_layout.addStretch()
        
        scroll.setWidget(self.yetkinlik_container)
        sag_layout.addWidget(scroll, 1)
        
        layout.addWidget(sag_panel, 1)
    
    def _load_personeller(self):
        """Personel listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            dept_filtre = self.cmb_departman.currentData()
            
            if dept_filtre:
                cursor.execute("""
                    SELECT p.id, p.ad + ' ' + p.soyad AS ad_soyad, d.ad AS departman
                    FROM ik.personeller p
                    LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                    WHERE p.aktif_mi = 1 AND d.ad = ?
                    ORDER BY p.ad, p.soyad
                """, (dept_filtre,))
            else:
                cursor.execute("""
                    SELECT p.id, p.ad + ' ' + p.soyad AS ad_soyad, d.ad AS departman
                    FROM ik.personeller p
                    LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                    WHERE p.aktif_mi = 1
                    ORDER BY d.ad, p.ad, p.soyad
                """)
            
            rows = cursor.fetchall()
            conn.close()
            
            self.tbl_personel.setRowCount(len(rows))
            for i, row in enumerate(rows):
                pid, ad, dept = row
                
                item_ad = QTableWidgetItem(ad or "-")
                item_ad.setData(Qt.UserRole, pid)
                self.tbl_personel.setItem(i, 0, item_ad)
                
                item_dept = QTableWidgetItem(dept or "-")
                self.tbl_personel.setItem(i, 1, item_dept)
            
        except Exception as e:
            print(f"Personel yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _filter_personeller(self):
        """Personel listesini filtrele"""
        arama = self.txt_arama.text().lower()
        for i in range(self.tbl_personel.rowCount()):
            item = self.tbl_personel.item(i, 0)
            if item:
                visible = arama in item.text().lower()
                self.tbl_personel.setRowHidden(i, not visible)
    
    def _on_personel_selected(self):
        """Personel seçildiğinde yetkinlikleri göster"""
        selected = self.tbl_personel.selectedItems()
        if not selected:
            return
        
        item = self.tbl_personel.item(selected[0].row(), 0)
        self.selected_personel_id = item.data(Qt.UserRole)
        self.selected_personel_name = item.text()
        
        self.lbl_personel_adi.setText(self.selected_personel_name)
        self._load_yetkinlikler()
    
    def _load_yetkinlikler(self):
        """Seçilen personelin yetkinliklerini yükle"""
        # Önceki widget'ları temizle
        while self.yetkinlik_layout.count():
            child = self.yetkinlik_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.yetkinlik_widgets = {}
        
        if not self.selected_personel_id:
            return
        
        # DB'den yetkinlik tanımlarını ve mevcut seviyeleri al
        yetkinlik_seviyeleri = {}
        yetkinlik_id_map = {}  # kod -> id eşleştirmesi
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Yetkinlik tanımlarını al
            cursor.execute("""
                SELECT id, kod, ad, kategori
                FROM ik.yetkinlikler
                WHERE aktif_mi = 1
                ORDER BY kategori, kod
            """)
            db_yetkinlikler = {}
            for row in cursor.fetchall():
                yid, kod, ad, kategori = row
                yetkinlik_id_map[kod] = yid
                if kategori not in db_yetkinlikler:
                    db_yetkinlikler[kategori] = []
                db_yetkinlikler[kategori].append((kod, ad, yid))
            
            # Personelin mevcut yetkinliklerini al
            cursor.execute("""
                SELECT y.kod, py.seviye
                FROM ik.personel_yetkinlikler py
                JOIN ik.yetkinlikler y ON py.yetkinlik_id = y.id
                WHERE py.personel_id = ?
            """, (self.selected_personel_id,))
            for row in cursor.fetchall():
                yetkinlik_seviyeleri[row[0]] = row[1]
            
            conn.close()
        except Exception as e:
            print(f"Yetkinlik yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
            # Hata durumunda sabit listeyi kullan
            db_yetkinlikler = {}
        
        # Eğer DB'den yetkinlik geldiyse onu kullan, yoksa sabit listeyi kullan
        kullanilacak_yetkinlikler = db_yetkinlikler if db_yetkinlikler else {
            dept: [(kod, ad, None) for kod, ad in yetkinlikler]
            for dept, yetkinlikler in DEPARTMAN_YETKINLIKLERI.items()
        }
        
        # Her departman için yetkinlikleri göster
        for dept, yetkinlikler in kullanilacak_yetkinlikler.items():
            # Departman başlığı
            dept_frame = QFrame()
            dept_frame.setStyleSheet(f"""
                QFrame {{
                    background: rgba(0,0,0,0.2);
                    border: 1px solid {brand.BORDER};
                    border-radius: 6px;
                    margin-top: 4px;
                }}
            """)
            dept_layout = QVBoxLayout(dept_frame)
            dept_layout.setContentsMargins(10, 8, 10, 8)
            dept_layout.setSpacing(4)
            
            dept_title = QLabel(f"📁 {dept}")
            dept_title.setStyleSheet(f"font-weight: 600; color: {brand.PRIMARY}; font-size: 12px;")
            dept_layout.addWidget(dept_title)
            
            # Yetkinlikler grid
            grid = QGridLayout()
            grid.setSpacing(6)
            
            for i, yetkinlik_data in enumerate(yetkinlikler):
                kod = yetkinlik_data[0]
                ad = yetkinlik_data[1]
                yid = yetkinlik_data[2] if len(yetkinlik_data) > 2 else yetkinlik_id_map.get(kod)
                
                row = i // 2
                col = (i % 2) * 2
                
                # Yetkinlik adı
                lbl = QLabel(f"{kod}: {ad}")
                lbl.setStyleSheet(f"color: {brand.TEXT}; font-size: 11px;")
                lbl.setFixedWidth(200)
                grid.addWidget(lbl, row, col)
                
                # Seviye seçici
                spin = QSpinBox()
                spin.setRange(0, 4)
                mevcut_seviye = yetkinlik_seviyeleri.get(kod, 0)
                spin.setValue(mevcut_seviye)
                spin.setFixedWidth(60)
                
                # Mevcut seviyeye göre renk
                _, renk = SEVIYELER.get(mevcut_seviye, ("", "#666"))
                if mevcut_seviye > 0:
                    spin.setStyleSheet(f"""
                        QSpinBox {{
                            background: {renk};
                            color: white;
                            border: 1px solid {renk};
                            border-radius: 4px;
                            padding: 4px 8px;
                            font-size: 12px;
                            font-weight: bold;
                        }}
                        QSpinBox::up-button, QSpinBox::down-button {{ width: 16px; }}
                    """)
                else:
                    spin.setStyleSheet(f"""
                        QSpinBox {{
                            background: {brand.BG_INPUT};
                            color: {brand.TEXT};
                            border: 1px solid {brand.BORDER};
                            border-radius: 4px;
                            padding: 4px 8px;
                            font-size: 12px;
                        }}
                        QSpinBox::up-button, QSpinBox::down-button {{ width: 16px; }}
                    """)
                
                spin.setProperty("yetkinlik_id", yid)
                spin.setProperty("yetkinlik_kodu", kod)
                spin.valueChanged.connect(lambda val, k=kod, yi=yid: self._save_yetkinlik(k, yi, val))
                grid.addWidget(spin, row, col + 1)
                
                self.yetkinlik_widgets[kod] = spin
            
            dept_layout.addLayout(grid)
            self.yetkinlik_layout.addWidget(dept_frame)
        
        self.yetkinlik_layout.addStretch()
    
    def _save_yetkinlik(self, kod: str, yetkinlik_id: int, seviye: int):
        """Yetkinliği kaydet"""
        if not self.selected_personel_id:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Eğer yetkinlik_id yoksa, kod'dan bul
            if not yetkinlik_id:
                cursor.execute("SELECT id FROM ik.yetkinlikler WHERE kod = ?", (kod,))
                row = cursor.fetchone()
                if row:
                    yetkinlik_id = row[0]
                else:
                    conn.close()
                    return
            
            # Önce var mı kontrol et
            cursor.execute("""
                SELECT id FROM ik.personel_yetkinlikler
                WHERE personel_id = ? AND yetkinlik_id = ?
            """, (self.selected_personel_id, yetkinlik_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Güncelle
                cursor.execute("""
                    UPDATE ik.personel_yetkinlikler
                    SET seviye = ?, degerlendirme_tarihi = GETDATE()
                    WHERE personel_id = ? AND yetkinlik_id = ?
                """, (seviye, self.selected_personel_id, yetkinlik_id))
            else:
                # Yeni ekle
                cursor.execute("""
                    INSERT INTO ik.personel_yetkinlikler (personel_id, yetkinlik_id, seviye, degerlendirme_tarihi)
                    VALUES (?, ?, ?, GETDATE())
                """, (self.selected_personel_id, yetkinlik_id, seviye))
            
            conn.commit()
            conn.close()
            
            # Görsel geri bildirim - SpinBox rengini değiştir
            spin = self.yetkinlik_widgets.get(kod)
            if spin:
                _, renk = SEVIYELER.get(seviye, ("", "#666"))
                if seviye > 0:
                    spin.setStyleSheet(f"""
                        QSpinBox {{
                            background: {renk};
                            color: white;
                            border: 1px solid {renk};
                            border-radius: 4px;
                            padding: 4px 8px;
                            font-size: 12px;
                            font-weight: bold;
                        }}
                        QSpinBox::up-button, QSpinBox::down-button {{ width: 16px; }}
                    """)
                else:
                    spin.setStyleSheet(f"""
                        QSpinBox {{
                            background: {brand.BG_INPUT};
                            color: {brand.TEXT};
                            border: 1px solid {brand.BORDER};
                            border-radius: 4px;
                            padding: 4px 8px;
                            font-size: 12px;
                        }}
                        QSpinBox::up-button, QSpinBox::down-button {{ width: 16px; }}
                    """)
            
        except Exception as e:
            print(f"Yetkinlik kaydetme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _show_yetkinlik_yonetimi(self):
        """Yetkinlik yönetimi popup'ını aç"""
        from PySide6.QtWidgets import QDialog, QDialogButtonBox
        
        dlg = YetkinlikYonetimDialog(self.theme, self)
        if dlg.exec() == QDialog.Accepted:
            # Yetkinlikler değiştiyse, mevcut personelin yetkinliklerini yenile
            if self.selected_personel_id:
                self._load_yetkinlikler()


class YetkinlikYonetimDialog(QDialog):
    """Yetkinlik Tanımları Yönetimi - Basit Popup"""
    
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("⚙️ Yetkinlik Tanımları")
        self.setMinimumSize(700, 500)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {brand.BG_CARD}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_4, brand.SP_4, brand.SP_4, brand.SP_4)
        layout.setSpacing(brand.SP_3)

        # Header
        header = QHBoxLayout()
        title = QLabel("Yetkinlik Tanimlari")
        title.setStyleSheet(f"font-size: {brand.FS_HEADING_SM}px; font-weight: {brand.FW_SEMIBOLD}; color: {brand.TEXT};")
        header.addWidget(title)
        header.addStretch()
        
        # Kategori filtresi
        header.addWidget(QLabel("Kategori:", styleSheet=f"color: {brand.TEXT_DIM};"))
        self.cmb_kategori = QComboBox()
        self.cmb_kategori.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                min-width: 150px;
            }}
        """)
        self.cmb_kategori.addItem("Tümü", None)
        for dept in DEPARTMAN_YETKINLIKLERI.keys():
            self.cmb_kategori.addItem(dept, dept)
        self.cmb_kategori.currentIndexChanged.connect(self._load_data)
        header.addWidget(self.cmb_kategori)
        
        # Yeni Ekle butonu
        btn_ekle = QPushButton("Yeni Ekle")
        btn_ekle.setCursor(Qt.PointingHandCursor)
        btn_ekle.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_4}px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        btn_ekle.clicked.connect(self._yeni_ekle)
        header.addWidget(btn_ekle)
        
        layout.addLayout(header)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Kategori", "İşlem"])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 120)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {brand.BORDER};
            }}
            QTableWidget::item:selected {{
                background: {brand.PRIMARY};
            }}
            QHeaderView::section {{
                background: rgba(0,0,0,0.3);
                color: {brand.TEXT_MUTED};
                padding: 8px;
                border: none;
                font-weight: 600;
            }}
        """)
        layout.addWidget(self.table, 1)
        
        # Alt butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_kapat = QPushButton("Kapat")
        btn_kapat.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: 4px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{ background: {brand.BORDER}; }}
        """)
        btn_kapat.clicked.connect(self.accept)
        btn_layout.addWidget(btn_kapat)
        
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        """Yetkinlikleri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            kategori = self.cmb_kategori.currentData()
            
            if kategori:
                cursor.execute("""
                    SELECT id, kod, ad, kategori
                    FROM ik.yetkinlikler
                    WHERE aktif_mi = 1 AND kategori = ?
                    ORDER BY kod
                """, (kategori,))
            else:
                cursor.execute("""
                    SELECT id, kod, ad, kategori
                    FROM ik.yetkinlikler
                    WHERE aktif_mi = 1
                    ORDER BY kategori, kod
                """)
            
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                yid, kod, ad, kategori = row
                
                self.table.setItem(i, 0, QTableWidgetItem(str(yid)))
                self.table.setItem(i, 1, QTableWidgetItem(kod or ""))
                self.table.setItem(i, 2, QTableWidgetItem(ad or ""))
                self.table.setItem(i, 3, QTableWidgetItem(kategori or ""))
                
                # Sil butonu
                widget = create_action_buttons(self.theme, [
                    ("Sil", "Sil", lambda _, y=yid, k=kod: self._sil(y, k), "delete"),
                ])
                self.table.setCellWidget(i, 4, widget)
                self.table.setRowHeight(i, brand.sp(42))
                
        except Exception as e:
            print(f"Yetkinlik yükleme hatası: {e}")
    
    def _yeni_ekle(self):
        """Yeni yetkinlik ekle"""
        from PySide6.QtWidgets import QInputDialog

        # Kod al
        kod, ok1 = QInputDialog.getText(self, "Yeni Yetkinlik", "Yetkinlik Kodu (örn: EYS-014):")
        if not ok1 or not kod.strip():
            return
        
        # Ad al
        ad, ok2 = QInputDialog.getText(self, "Yeni Yetkinlik", "Yetkinlik Adı:")
        if not ok2 or not ad.strip():
            return
        
        # Kategori al
        kategoriler = list(DEPARTMAN_YETKINLIKLERI.keys())
        kategori, ok3 = QInputDialog.getItem(self, "Yeni Yetkinlik", "Kategori:", kategoriler, 0, False)
        if not ok3:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ik.yetkinlikler (kod, ad, kategori, aktif_mi)
                VALUES (?, ?, ?, 1)
            """, (kod.strip(), ad.strip(), kategori))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Başarılı", f"Yetkinlik eklendi: {kod}")
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ekleme hatası: {e}")
    
    def _sil(self, yetkinlik_id: int, kod: str):
        """Yetkinlik sil"""
        reply = QMessageBox.question(
            self, "Silme Onayı", 
            f"'{kod}' yetkinliğini silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                # Soft delete - aktif_mi = 0 yap
                cursor.execute("UPDATE ik.yetkinlikler SET aktif_mi = 0 WHERE id = ?", (yetkinlik_id,))
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Başarılı", f"Yetkinlik silindi: {kod}")
                self._load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
