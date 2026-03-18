# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Banyo Tanımları
uretim.banyo_tanimlari tablosu için CRUD
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QDoubleSpinBox, QComboBox, QTabWidget, QWidget, QScrollArea,
    QGroupBox, QGridLayout, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager


class BanyoDialog(QDialog):
    """Banyo Tanımı Ekleme/Düzenleme"""
    
    def __init__(self, theme: dict, banyo_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.banyo_id = banyo_id
        self.data = {}
        
        self.setWindowTitle("Yeni Banyo" if not banyo_id else "Banyo Düzenle")
        self.setMinimumSize(850, 700)
        
        if banyo_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM uretim.banyo_tanimlari WHERE id = ?", (self.banyo_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit, QDoubleSpinBox, QComboBox {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']};
                border-radius: 6px; padding: 6px; color: {self.theme['text']};
            }}
            QTabWidget::pane {{ border: 1px solid {self.theme['border']}; background: {self.theme['bg_card_solid']}; }}
            QTabBar::tab {{ background: {self.theme['bg_input']}; padding: 8px 16px; color: {self.theme['text']}; }}
            QTabBar::tab:selected {{ background: {self.theme['bg_card_solid']}; border-bottom: 2px solid {self.theme['primary']}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("🧪 " + self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        tabs = QTabWidget()
        tabs.addTab(self._create_genel_tab(), "Genel")
        tabs.addTab(self._create_parametre_tab(), "Parametreler")
        tabs.addTab(self._create_plc_tab(), "PLC Eşleştirme")

        # TDS sekmesi
        from modules.lab.lab_banyo_tds import BanyoTDSTab
        self.tds_tab = BanyoTDSTab(self.theme, self.banyo_id, parent=self)
        tabs.addTab(self.tds_tab, "TDS")

        layout.addWidget(tabs, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def _create_genel_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)
        
        self.kod_input = QLineEdit(self.data.get('kod', ''))
        self.kod_input.setPlaceholderText("Örn: E-KTL-01")
        form.addRow("Kod *:", self.kod_input)
        
        self.ad_input = QLineEdit(self.data.get('ad', ''))
        self.ad_input.setPlaceholderText("Örn: Kataforez Banyosu 1")
        form.addRow("Ad *:", self.ad_input)
        
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("-- Seçiniz --", None)
        self._load_hatlar()
        form.addRow("Hat *:", self.hat_combo)
        
        self.pozisyon_combo = QComboBox()
        self.pozisyon_combo.addItem("-- Seçiniz --", None)
        self.hat_combo.currentIndexChanged.connect(self._load_pozisyonlar)
        form.addRow("Pozisyon:", self.pozisyon_combo)
        
        self.banyo_tipi_combo = QComboBox()
        self.banyo_tipi_combo.addItem("-- Seçiniz --", None)
        self._load_banyo_tipleri()
        form.addRow("Banyo Tipi *:", self.banyo_tipi_combo)
        
        self.hacim_input = QDoubleSpinBox()
        self.hacim_input.setRange(0, 999999)
        self.hacim_input.setSuffix(" lt")
        self.hacim_input.setValue(self.data.get('hacim_lt', 0) or 0)
        form.addRow("Hacim:", self.hacim_input)
        
        self.aktif_combo = QComboBox()
        self.aktif_combo.addItem("✓ Aktif", True)
        self.aktif_combo.addItem("✗ Pasif", False)
        self.aktif_combo.setCurrentIndex(0 if self.data.get('aktif_mi', True) else 1)
        form.addRow("Durum:", self.aktif_combo)
        
        return widget
    
    def _create_param_row(self, label, prefix, data_prefix, range_min, range_max, decimals=2):
        """Parametre satırı oluştur (Min/Hedef/Max)"""
        frame = QFrame()
        frame.setStyleSheet(f"background: {self.theme['bg_card_solid']}; border: 1px solid {self.theme['border']}; border-radius: 8px;")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(10, 6, 10, 6)
        frame_layout.setSpacing(4)
        frame_layout.addWidget(QLabel(label))

        grid = QHBoxLayout()
        spin_min = QDoubleSpinBox(); spin_min.setRange(range_min, range_max); spin_min.setDecimals(decimals)
        spin_min.setValue(self.data.get(f'{data_prefix}_min', 0) or 0)
        spin_hedef = QDoubleSpinBox(); spin_hedef.setRange(range_min, range_max); spin_hedef.setDecimals(decimals)
        spin_hedef.setValue(self.data.get(f'{data_prefix}_hedef', 0) or 0)
        spin_max = QDoubleSpinBox(); spin_max.setRange(range_min, range_max); spin_max.setDecimals(decimals)
        spin_max.setValue(self.data.get(f'{data_prefix}_max', 0) or 0)

        grid.addWidget(QLabel("Min:")); grid.addWidget(spin_min)
        grid.addWidget(QLabel("Hedef:")); grid.addWidget(spin_hedef)
        grid.addWidget(QLabel("Max:")); grid.addWidget(spin_max)
        frame_layout.addLayout(grid)

        setattr(self, f'{prefix}_min', spin_min)
        setattr(self, f'{prefix}_hedef', spin_hedef)
        setattr(self, f'{prefix}_max', spin_max)

        return frame

    def _create_parametre_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # TDS'den Parametre Alma Toolbar
        tds_toolbar = QHBoxLayout()
        tds_import_btn = QPushButton("📥 TDS'den Parametreleri Al (AI Destekli)")
        tds_import_btn.setStyleSheet(
            f"background: {self.theme['primary']}; color: white; border: none; "
            f"padding: 10px 20px; border-radius: 6px; font-weight: bold; font-size: 13px;")
        tds_import_btn.clicked.connect(self._tds_parametre_al)
        tds_toolbar.addWidget(tds_import_btn)
        tds_toolbar.addStretch()
        layout.addLayout(tds_toolbar)

        # Sıcaklık
        layout.addWidget(self._create_param_row("🌡️ Sıcaklık (°C)", "sic", "sicaklik", 0, 500, 1))

        # pH
        layout.addWidget(self._create_param_row("🧪 pH", "ph", "ph", 0, 14, 2))

        # İletkenlik
        layout.addWidget(self._create_param_row("⚡ İletkenlik (mS/cm)", "iletkenlik", "iletkenlik", 0, 99999, 2))

        # Katı Madde
        layout.addWidget(self._create_param_row("📦 Katı Madde (%)", "kati_madde", "kati_madde", 0, 100, 2))

        # P/B Oranı
        layout.addWidget(self._create_param_row("⚖️ P/B Oranı", "pb_orani", "pb_orani", 0, 100, 2))

        # Solvent
        layout.addWidget(self._create_param_row("💧 Solvent (%)", "solvent", "solvent", 0, 100, 2))

        # MEQ
        layout.addWidget(self._create_param_row("📊 MEQ (meq/100g)", "meq", "meq", 0, 999, 2))

        # Toplam Asit
        layout.addWidget(self._create_param_row("🔬 Toplam Asit (ml)", "toplam_asit", "toplam_asit", 0, 9999, 4))

        # Serbest Asit
        layout.addWidget(self._create_param_row("🧫 Serbest Asit (ml)", "serbest_asit", "serbest_asit", 0, 9999, 4))

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def _create_plc_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.sql_sic_input = QLineEdit(self.data.get('sql_sicaklik_tag', '') or '')
        self.sql_sic_input.setPlaceholderText("PLC Sıcaklık Tag Adı")
        form.addRow("Sıcaklık Tag:", self.sql_sic_input)

        self.sql_ph_input = QLineEdit(self.data.get('sql_ph_tag', '') or '')
        self.sql_ph_input.setPlaceholderText("PLC pH Tag Adı")
        form.addRow("pH Tag:", self.sql_ph_input)

        self.sql_akim_input = QLineEdit(self.data.get('sql_akim_tag', '') or '')
        self.sql_akim_input.setPlaceholderText("PLC Akım Tag Adı")
        form.addRow("Akım Tag:", self.sql_akim_input)

        scroll.setWidget(widget)
        return scroll
    
    def _load_hatlar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.uretim_hatlari WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no, kod")
            for row in cursor.fetchall():
                self.hat_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
            if self.data.get('hat_id'):
                idx = self.hat_combo.findData(self.data['hat_id'])
                if idx >= 0: self.hat_combo.setCurrentIndex(idx)
        except Exception: pass
    
    def _load_pozisyonlar(self):
        self.pozisyon_combo.clear()
        self.pozisyon_combo.addItem("-- Seçiniz --", None)
        hat_id = self.hat_combo.currentData()
        print(f"🔍 DEBUG: Hat ID seçildi: {hat_id}")
        if not hat_id: 
            print("⚠️  DEBUG: Hat ID None, pozisyonlar yüklenmedi")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, pozisyon_no, ad FROM tanim.hat_pozisyonlar WHERE hat_id=? AND aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no", (hat_id,))
            rows = cursor.fetchall()
            print(f"✅ DEBUG: {len(rows)} pozisyon bulundu")
            for row in rows:
                label = f"Poz {row[1]}: {row[2]}"
                self.pozisyon_combo.addItem(label, row[0])
                print(f"   - {label} (ID: {row[0]})")
            conn.close()
            if self.data.get('pozisyon_id'):
                idx = self.pozisyon_combo.findData(self.data['pozisyon_id'])
                if idx >= 0: 
                    self.pozisyon_combo.setCurrentIndex(idx)
                    print(f"✅ DEBUG: Pozisyon seçildi: {self.data['pozisyon_id']}")
        except Exception as e:
            print(f"❌ DEBUG HATA: {e}")
    
    def _load_banyo_tipleri(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad, kategori FROM tanim.banyo_tipleri WHERE aktif_mi=1 ORDER BY kategori, ad")
            for row in cursor.fetchall():
                self.banyo_tipi_combo.addItem(f"{row[1]} ({row[2]})", row[0])
            conn.close()
            if self.data.get('banyo_tipi_id'):
                idx = self.banyo_tipi_combo.findData(self.data['banyo_tipi_id'])
                if idx >= 0: self.banyo_tipi_combo.setCurrentIndex(idx)
        except Exception: pass
    
    def _tds_parametre_al(self):
        """TDS'den AI destekli parametre alma diyalogu ac"""
        if not self.banyo_id:
            QMessageBox.warning(self, "Uyari", "Lutfen once banyoyu kaydedin, sonra TDS'den parametre alabilirsiniz!")
            return

        dlg = TDSParametreAlDialog(self.theme, self.banyo_id, parent=self)
        if dlg.exec() == QDialog.Accepted and dlg.secilen_parametreler:
            self._parametreleri_uygula(dlg.secilen_parametreler)

    def _parametreleri_uygula(self, parametreler: list):
        """AI onerdigi parametreleri spinbox'lara uygula"""
        # Parametre kodu -> spinbox prefix haritalama
        param_spin_map = {
            "sicaklik": "sic",
            "ph": "ph",
            "iletkenlik": "iletkenlik",
            "kati_madde": "kati_madde",
            "pb_orani": "pb_orani",
            "solvent": "solvent",
            "meq": "meq",
            "toplam_asit": "toplam_asit",
            "serbest_asit": "serbest_asit",
        }

        uygulanan = 0
        for p in parametreler:
            kod = p.get("parametre_kodu", "")
            prefix = param_spin_map.get(kod)
            if not prefix:
                continue

            min_val = p.get("onerilen_min") or p.get("tds_min") or 0
            hedef_val = p.get("onerilen_hedef") or p.get("tds_hedef") or 0
            max_val = p.get("onerilen_max") or p.get("tds_max") or 0

            min_spin = getattr(self, f'{prefix}_min', None)
            hedef_spin = getattr(self, f'{prefix}_hedef', None)
            max_spin = getattr(self, f'{prefix}_max', None)

            if min_spin and hedef_spin and max_spin:
                min_spin.setValue(float(min_val))
                hedef_spin.setValue(float(hedef_val))
                max_spin.setValue(float(max_val))
                uygulanan += 1

        QMessageBox.information(
            self, "Basarili",
            f"{uygulanan} parametre TDS'den basariyla aktarildi!\n"
            f"Kaydetmek icin 'Kaydet' butonuna basin.")

    def _spin_val(self, spin):
        """SpinBox değerini al, 0 ise None döndür"""
        v = spin.value()
        return v if v else None

    def _save(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()
        hat_id = self.hat_combo.currentData()
        banyo_tipi_id = self.banyo_tipi_combo.currentData()

        if not kod or not ad or not hat_id or not banyo_tipi_id:
            QMessageBox.warning(self, "Uyarı", "Kod, Ad, Hat ve Banyo Tipi zorunludur!")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            params = (
                kod, ad, hat_id, self.pozisyon_combo.currentData(), banyo_tipi_id,
                self.hacim_input.value() or None,
                # Sıcaklık
                self._spin_val(self.sic_min), self._spin_val(self.sic_max), self._spin_val(self.sic_hedef),
                # pH
                self._spin_val(self.ph_min), self._spin_val(self.ph_max), self._spin_val(self.ph_hedef),
                # İletkenlik
                self._spin_val(self.iletkenlik_min), self._spin_val(self.iletkenlik_max), self._spin_val(self.iletkenlik_hedef),
                # Katı Madde
                self._spin_val(self.kati_madde_min), self._spin_val(self.kati_madde_max), self._spin_val(self.kati_madde_hedef),
                # P/B Oranı
                self._spin_val(self.pb_orani_min), self._spin_val(self.pb_orani_max), self._spin_val(self.pb_orani_hedef),
                # Solvent
                self._spin_val(self.solvent_min), self._spin_val(self.solvent_max), self._spin_val(self.solvent_hedef),
                # MEQ
                self._spin_val(self.meq_min), self._spin_val(self.meq_max), self._spin_val(self.meq_hedef),
                # Toplam Asit
                self._spin_val(self.toplam_asit_min), self._spin_val(self.toplam_asit_max), self._spin_val(self.toplam_asit_hedef),
                # Serbest Asit
                self._spin_val(self.serbest_asit_min), self._spin_val(self.serbest_asit_max), self._spin_val(self.serbest_asit_hedef),
                # PLC Tags
                self.sql_sic_input.text().strip() or None,
                self.sql_ph_input.text().strip() or None,
                self.sql_akim_input.text().strip() or None,
                # Durum
                self.aktif_combo.currentData()
            )

            if self.banyo_id:
                cursor.execute("""UPDATE uretim.banyo_tanimlari SET
                    kod=?, ad=?, hat_id=?, pozisyon_id=?, banyo_tipi_id=?, hacim_lt=?,
                    sicaklik_min=?, sicaklik_max=?, sicaklik_hedef=?,
                    ph_min=?, ph_max=?, ph_hedef=?,
                    iletkenlik_min=?, iletkenlik_max=?, iletkenlik_hedef=?,
                    kati_madde_min=?, kati_madde_max=?, kati_madde_hedef=?,
                    pb_orani_min=?, pb_orani_max=?, pb_orani_hedef=?,
                    solvent_min=?, solvent_max=?, solvent_hedef=?,
                    meq_min=?, meq_max=?, meq_hedef=?,
                    toplam_asit_min=?, toplam_asit_max=?, toplam_asit_hedef=?,
                    serbest_asit_min=?, serbest_asit_max=?, serbest_asit_hedef=?,
                    sql_sicaklik_tag=?, sql_ph_tag=?, sql_akim_tag=?,
                    aktif_mi=?, guncelleme_tarihi=GETDATE()
                    WHERE id=?""", params + (self.banyo_id,))
            else:
                cursor.execute("""INSERT INTO uretim.banyo_tanimlari (
                    kod, ad, hat_id, pozisyon_id, banyo_tipi_id, hacim_lt,
                    sicaklik_min, sicaklik_max, sicaklik_hedef,
                    ph_min, ph_max, ph_hedef,
                    iletkenlik_min, iletkenlik_max, iletkenlik_hedef,
                    kati_madde_min, kati_madde_max, kati_madde_hedef,
                    pb_orani_min, pb_orani_max, pb_orani_hedef,
                    solvent_min, solvent_max, solvent_hedef,
                    meq_min, meq_max, meq_hedef,
                    toplam_asit_min, toplam_asit_max, toplam_asit_hedef,
                    serbest_asit_min, serbest_asit_max, serbest_asit_hedef,
                    sql_sicaklik_tag, sql_ph_tag, sql_akim_tag,
                    aktif_mi)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", params)

            # Yeni kayıtta oluşan ID'yi al
            if not self.banyo_id:
                cursor.execute("SELECT SCOPE_IDENTITY()")
                new_id = cursor.fetchone()
                if new_id and new_id[0]:
                    self.banyo_id = int(new_id[0])

            conn.commit()
            LogManager.log_insert('lab', 'uretim.banyo_tanimlari', None, 'Yeni kayit eklendi')
            conn.close()

            # TDS tab'a banyo_id ilet (yeni kayıt sonrası)
            if hasattr(self, 'tds_tab') and self.banyo_id:
                self.tds_tab.set_banyo_id(self.banyo_id)

            QMessageBox.information(self, "Başarılı", "Kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class TDSParametreAlDialog(QDialog):
    """TDS'den AI destekli parametre alma diyalogu"""

    def __init__(self, theme: dict, banyo_id: int, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.banyo_id = banyo_id
        self.secilen_parametreler = []
        self.ai_sonuc = None

        self.setWindowTitle("TDS'den Parametre Al - AI Destekli")
        self.setMinimumSize(1000, 700)
        self._setup_ui()
        self._load_tds_listesi()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit, QComboBox, QTextEdit {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']};
                border-radius: 6px; padding: 6px; color: {self.theme['text']};
            }}
            QGroupBox {{
                color: {self.theme['text']}; font-weight: bold;
                border: 1px solid {self.theme['border']}; border-radius: 8px;
                margin-top: 10px; padding-top: 14px; background: {self.theme['bg_card_solid']};
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Baslik
        title = QLabel("📥 TDS'den Kontrol Parametreleri Al")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)

        desc = QLabel("TDS'deki parametreleri AI analizi ile optimize ederek banyo kartina aktarin.")
        desc.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 12px;")
        layout.addWidget(desc)

        # TDS Secim
        tds_bar = QHBoxLayout()
        tds_bar.addWidget(QLabel("TDS Kaydi:"))
        self.tds_combo = QComboBox()
        self.tds_combo.setMinimumWidth(350)
        self.tds_combo.currentIndexChanged.connect(self._on_tds_changed)
        tds_bar.addWidget(self.tds_combo, 1)

        self.analiz_btn = QPushButton("AI Analiz Baslat")
        self.analiz_btn.setStyleSheet(
            f"background: {self.theme['primary']}; color: white; border: none; "
            f"padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        self.analiz_btn.clicked.connect(self._ai_analiz_baslat)
        self.analiz_btn.setEnabled(False)
        tds_bar.addWidget(self.analiz_btn)
        layout.addLayout(tds_bar)

        # Durum gostergesi
        self.durum_label = QLabel("")
        self.durum_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-style: italic;")
        layout.addWidget(self.durum_label)

        # Parametre Tablosu
        param_group = QGroupBox("Parametre Karsilastirma ve AI Onerileri")
        param_layout = QVBoxLayout(param_group)

        self.param_table = QTableWidget()
        self.param_table.setColumnCount(11)
        self.param_table.setHorizontalHeaderLabels([
            "Parametre", "Birim",
            "TDS Min", "TDS Hedef", "TDS Max",
            "Gercek", "Trend",
            "AI Min", "AI Hedef", "AI Max",
            "Durum"
        ])
        self.param_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.param_table.setColumnWidth(1, 65)
        self.param_table.setColumnWidth(2, 70)
        self.param_table.setColumnWidth(3, 75)
        self.param_table.setColumnWidth(4, 70)
        self.param_table.setColumnWidth(5, 70)
        self.param_table.setColumnWidth(6, 70)
        self.param_table.setColumnWidth(7, 70)
        self.param_table.setColumnWidth(8, 120)
        self.param_table.setColumnWidth(9, 70)
        self.param_table.setColumnWidth(10, 70)
        self.param_table.verticalHeader().setVisible(False)
        self.param_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.param_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.param_table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme['bg_card_solid']}; border: none;
                            gridline-color: {self.theme['border']}; color: {self.theme['text']}; }}
            QTableWidget::item {{ padding: 4px; }}
            QTableWidget::item:selected {{ background: {self.theme['primary']}33; }}
            QHeaderView::section {{ background: {self.theme['bg_main']}; color: {self.theme['text']};
                                    padding: 6px; border: none;
                                    border-bottom: 2px solid {self.theme['primary']}; font-weight: bold; }}
        """)
        param_layout.addWidget(self.param_table)
        layout.addWidget(param_group, 1)

        # AI Yorum Paneli
        ai_group = QGroupBox("AI Degerlendirme")
        ai_layout = QVBoxLayout(ai_group)
        self.ai_yorum_text = QTextEdit()
        self.ai_yorum_text.setReadOnly(True)
        self.ai_yorum_text.setMaximumHeight(120)
        self.ai_yorum_text.setStyleSheet(
            f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; "
            f"border-radius: 6px; color: {self.theme['text']}; padding: 8px;")
        self.ai_yorum_text.setPlaceholderText("AI analizi baslatildiginda degerlendirme burada gosterilecek...")
        ai_layout.addWidget(self.ai_yorum_text)
        layout.addWidget(ai_group)

        # Butonlar
        btn_layout = QHBoxLayout()

        self.mod_label = QLabel("Uygulama modu:")
        self.mod_label.setStyleSheet(f"color: {self.theme['text']};")
        btn_layout.addWidget(self.mod_label)

        self.mod_combo = QComboBox()
        self.mod_combo.addItem("AI Onerisi (Optimize)", "ai")
        self.mod_combo.addItem("TDS Degerleri (Orijinal)", "tds")
        self.mod_combo.setMinimumWidth(200)
        btn_layout.addWidget(self.mod_combo)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setStyleSheet(
            f"padding: 10px 20px; border-radius: 6px; "
            f"border: 1px solid {self.theme['border']}; color: {self.theme['text']};")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.uygula_btn = QPushButton("Parametreleri Uygula")
        self.uygula_btn.setStyleSheet(
            f"background: {self.theme.get('success', '#10B981')}; color: white; border: none; "
            f"padding: 10px 24px; border-radius: 6px; font-weight: bold; font-size: 13px;")
        self.uygula_btn.clicked.connect(self._uygula)
        self.uygula_btn.setEnabled(False)
        btn_layout.addWidget(self.uygula_btn)
        layout.addLayout(btn_layout)

    def _load_tds_listesi(self):
        """Banyoya ait TDS kayitlarini yukle"""
        self.tds_combo.clear()
        self.tds_combo.addItem("-- TDS Seciniz --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, tds_kodu, tds_adi, versiyon, tedarikci
                FROM uretim.banyo_tds
                WHERE banyo_id = ? AND aktif_mi = 1
                ORDER BY tds_kodu
            """, (self.banyo_id,))
            for row in cursor.fetchall():
                label = f"{row[1]} - {row[2]} (v{row[3]})"
                if row[4]:
                    label += f" [{row[4]}]"
                self.tds_combo.addItem(label, row[0])
            conn.close()

            if self.tds_combo.count() <= 1:
                self.durum_label.setText("Bu banyo icin tanimli TDS kaydı bulunamadi.")
                self.durum_label.setStyleSheet(f"color: #F59E0B; font-style: italic;")
        except Exception as e:
            self.durum_label.setText(f"TDS listesi yuklenemedi: {e}")

    def _on_tds_changed(self):
        """TDS secimi degistiginde"""
        tds_id = self.tds_combo.currentData()
        if tds_id:
            self.analiz_btn.setEnabled(True)
            self._load_tds_parametreleri(tds_id)
        else:
            self.analiz_btn.setEnabled(False)
            self.param_table.setRowCount(0)

    def _load_tds_parametreleri(self, tds_id: int):
        """Secilen TDS'in parametrelerini tabloya yukle (sadece TDS degerleri)"""
        self.param_table.setRowCount(0)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT parametre_kodu, parametre_adi, birim,
                       tds_min, tds_hedef, tds_max, tolerans_yuzde
                FROM uretim.banyo_tds_parametreler
                WHERE tds_id = ?
                ORDER BY sira_no, parametre_kodu
            """, (tds_id,))
            rows = cursor.fetchall()
            conn.close()

            self.param_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.param_table.setItem(i, 0, QTableWidgetItem(row[1] or row[0]))  # Ad veya Kod
                self.param_table.setItem(i, 1, QTableWidgetItem(row[2] or ''))

                # UserRole'da parametre kodunu sakla
                item0 = self.param_table.item(i, 0)
                item0.setData(Qt.UserRole, row[0])

                # TDS degerleri
                self.param_table.setItem(i, 2, QTableWidgetItem(f"{row[3]:.2f}" if row[3] else '-'))
                self.param_table.setItem(i, 3, QTableWidgetItem(f"{row[4]:.2f}" if row[4] else '-'))
                self.param_table.setItem(i, 4, QTableWidgetItem(f"{row[5]:.2f}" if row[5] else '-'))

                # Gercek, Trend, AI kolonlari bos
                for col in range(5, 11):
                    self.param_table.setItem(i, col, QTableWidgetItem("-"))

            self.uygula_btn.setEnabled(len(rows) > 0)
            self.durum_label.setText(f"{len(rows)} parametre yuklendi. AI analizi icin butona basin.")
            self.durum_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-style: italic;")

        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Parametreler yuklenemedi: {e}")

    def _ai_analiz_baslat(self):
        """AI destekli parametre optimizasyonu baslat"""
        tds_id = self.tds_combo.currentData()
        if not tds_id:
            return

        self.durum_label.setText("AI analizi calisiyor...")
        self.durum_label.setStyleSheet(f"color: {self.theme['primary']}; font-style: italic; font-weight: bold;")
        self.analiz_btn.setEnabled(False)

        try:
            from core.ai_analiz_service import AIAnalizService

            # TDS parametreleri al
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT parametre_kodu, parametre_adi, birim,
                       tds_min, tds_hedef, tds_max, tolerans_yuzde
                FROM uretim.banyo_tds_parametreler
                WHERE tds_id = ?
                ORDER BY sira_no
            """, (tds_id,))
            tds_params = []
            for row in cursor.fetchall():
                tds_params.append({
                    "parametre_kodu": row[0],
                    "parametre_adi": row[1] or row[0],
                    "birim": row[2] or "",
                    "tds_min": float(row[3]) if row[3] else 0,
                    "tds_hedef": float(row[4]) if row[4] else 0,
                    "tds_max": float(row[5]) if row[5] else 0,
                    "tolerans_yuzde": float(row[6]) if row[6] else 10.0,
                })

            # Son olcumler
            son_olcumler = {}
            cursor.execute("""
                SELECT TOP 1 sicaklik, ph, iletkenlik, kati_madde_yuzde, pb_orani,
                       solvent_yuzde, meq_degeri, toplam_asitlik, serbest_asitlik
                FROM uretim.banyo_analiz_sonuclari
                WHERE banyo_id = ?
                ORDER BY tarih DESC
            """, (self.banyo_id,))
            row = cursor.fetchone()
            if row:
                # Kolon adini parametre koduna maple
                kolon_map = {
                    "sicaklik": "sicaklik", "ph": "ph", "iletkenlik": "iletkenlik",
                    "kati_madde_yuzde": "kati_madde", "pb_orani": "pb_orani",
                    "solvent_yuzde": "solvent", "meq_degeri": "meq",
                    "toplam_asitlik": "toplam_asit", "serbest_asitlik": "serbest_asit",
                }
                cols = [d[0] for d in cursor.description]
                for col, val in zip(cols, row):
                    if val is not None:
                        kod = kolon_map.get(col, col)
                        son_olcumler[kod] = float(val)

            # Veri serisi (30 gun)
            veri_serisi = []
            cursor.execute("""
                SELECT tarih, sicaklik, ph, iletkenlik, kati_madde_yuzde, pb_orani,
                       solvent_yuzde, meq_degeri, toplam_asitlik, serbest_asitlik
                FROM uretim.banyo_analiz_sonuclari
                WHERE banyo_id = ? AND tarih >= DATEADD(DAY, -30, GETDATE())
                ORDER BY tarih ASC
            """, (self.banyo_id,))
            for row in cursor.fetchall():
                param_map = {
                    "sicaklik": row[1], "ph": row[2], "iletkenlik": row[3],
                    "kati_madde": row[4], "pb_orani": row[5], "solvent": row[6],
                    "meq": row[7], "toplam_asit": row[8], "serbest_asit": row[9],
                }
                for param, deger in param_map.items():
                    if deger is not None:
                        veri_serisi.append({"parametre": param, "tarih": row[0], "deger": float(deger)})

            conn.close()

            # AI analiz calistir
            service = AIAnalizService()
            self.ai_sonuc = service.parametre_optimizasyonu(
                self.banyo_id, tds_params, son_olcumler, veri_serisi)

            # Tabloyu guncelle
            self._tabloyu_guncelle(self.ai_sonuc.get("parametreler", []))

            # AI yorum
            ai_yorum = self.ai_sonuc.get("ai_yorum")
            if ai_yorum:
                self.ai_yorum_text.setPlainText(ai_yorum)
            else:
                # Kural tabanli ozet
                ozet_satirlari = []
                for p in self.ai_sonuc.get("parametreler", []):
                    if p.get("aciklama"):
                        ozet_satirlari.append(f"• {p['parametre_adi']}: {p['aciklama']}")
                if ozet_satirlari:
                    self.ai_yorum_text.setPlainText(
                        "Kural Tabanli AI Degerlendirmesi:\n\n" + "\n".join(ozet_satirlari))
                else:
                    self.ai_yorum_text.setPlainText("Tum parametreler TDS hedeflerine uygun durumda.")

            # Durum
            kritik = sum(1 for p in self.ai_sonuc.get("parametreler", []) if p.get("durum") == "KRITIK")
            uyari = sum(1 for p in self.ai_sonuc.get("parametreler", []) if p.get("durum") == "UYARI")
            normal = sum(1 for p in self.ai_sonuc.get("parametreler", []) if p.get("durum") == "NORMAL")

            if kritik > 0:
                durum_txt = f"AI analizi tamamlandi - {kritik} KRITIK, {uyari} UYARI, {normal} NORMAL"
                self.durum_label.setStyleSheet(f"color: #E2130D; font-weight: bold;")
            elif uyari > 0:
                durum_txt = f"AI analizi tamamlandi - {uyari} UYARI, {normal} NORMAL"
                self.durum_label.setStyleSheet(f"color: #F59E0B; font-weight: bold;")
            else:
                durum_txt = f"AI analizi tamamlandi - Tum parametreler uygun"
                self.durum_label.setStyleSheet(f"color: #10B981; font-weight: bold;")
            self.durum_label.setText(durum_txt)

        except Exception as e:
            QMessageBox.critical(self, "AI Analiz Hatasi", str(e))
            self.durum_label.setText(f"Hata: {e}")
            self.durum_label.setStyleSheet(f"color: #E2130D; font-style: italic;")
        finally:
            self.analiz_btn.setEnabled(True)

    def _tabloyu_guncelle(self, parametreler: list):
        """AI sonuclariyla tabloyu guncelle"""
        self.param_table.setRowCount(len(parametreler))

        durum_renk = {
            "NORMAL": "#10B981",
            "UYARI": "#F59E0B",
            "KRITIK": "#E2130D",
            "BILGI_YOK": "#6B7280",
        }
        trend_ikon = {
            "artan": "↗ Artan",
            "azalan": "↘ Azalan",
            "stabil": "→ Stabil",
            "veri_yok": "- Veri Yok",
        }

        for i, p in enumerate(parametreler):
            # Parametre adi
            item0 = QTableWidgetItem(p.get("parametre_adi", ""))
            item0.setData(Qt.UserRole, p.get("parametre_kodu", ""))
            self.param_table.setItem(i, 0, item0)

            # Birim
            self.param_table.setItem(i, 1, QTableWidgetItem(p.get("birim", "")))

            # TDS degerleri
            self.param_table.setItem(i, 2, QTableWidgetItem(
                f"{p['tds_min']:.2f}" if p.get('tds_min') else '-'))
            self.param_table.setItem(i, 3, QTableWidgetItem(
                f"{p['tds_hedef']:.2f}" if p.get('tds_hedef') else '-'))
            self.param_table.setItem(i, 4, QTableWidgetItem(
                f"{p['tds_max']:.2f}" if p.get('tds_max') else '-'))

            # Gercek deger
            gercek_item = QTableWidgetItem(
                f"{p['gercek']:.2f}" if p.get('gercek') is not None else '-')
            self.param_table.setItem(i, 5, gercek_item)

            # Trend
            trend = p.get("trend", "veri_yok")
            trend_item = QTableWidgetItem(trend_ikon.get(trend, trend))
            if trend == "artan":
                trend_item.setForeground(QColor("#F59E0B"))
            elif trend == "azalan":
                trend_item.setForeground(QColor("#3B82F6"))
            elif trend == "stabil":
                trend_item.setForeground(QColor("#10B981"))
            self.param_table.setItem(i, 6, trend_item)

            # AI onerilen degerler
            ai_min_item = QTableWidgetItem(
                f"{p['onerilen_min']:.2f}" if p.get('onerilen_min') else '-')
            ai_min_item.setForeground(QColor("#8B5CF6"))
            self.param_table.setItem(i, 7, ai_min_item)

            ai_hedef_item = QTableWidgetItem(
                f"{p['onerilen_hedef']:.2f}" if p.get('onerilen_hedef') else '-')
            ai_hedef_item.setForeground(QColor("#8B5CF6"))
            self.param_table.setItem(i, 8, ai_hedef_item)

            ai_max_item = QTableWidgetItem(
                f"{p['onerilen_max']:.2f}" if p.get('onerilen_max') else '-')
            ai_max_item.setForeground(QColor("#8B5CF6"))
            self.param_table.setItem(i, 9, ai_max_item)

            # Durum
            durum = p.get("durum", "BILGI_YOK")
            durum_item = QTableWidgetItem(durum)
            durum_item.setForeground(QColor(durum_renk.get(durum, "#ffffff")))
            self.param_table.setItem(i, 10, durum_item)

    def _uygula(self):
        """Secilen parametreleri banyo kartina aktar"""
        mod = self.mod_combo.currentData()

        if self.ai_sonuc and mod == "ai":
            self.secilen_parametreler = self.ai_sonuc.get("parametreler", [])
        else:
            # TDS orijinal degerleri kullan
            self.secilen_parametreler = []
            for i in range(self.param_table.rowCount()):
                item0 = self.param_table.item(i, 0)
                if not item0:
                    continue
                kod = item0.data(Qt.UserRole) or ""

                def safe_float(item):
                    if not item:
                        return 0
                    txt = item.text().strip().replace('-', '')
                    try:
                        return float(txt)
                    except (ValueError, AttributeError):
                        return 0

                self.secilen_parametreler.append({
                    "parametre_kodu": kod,
                    "parametre_adi": item0.text(),
                    "tds_min": safe_float(self.param_table.item(i, 2)),
                    "tds_hedef": safe_float(self.param_table.item(i, 3)),
                    "tds_max": safe_float(self.param_table.item(i, 4)),
                    "onerilen_min": safe_float(self.param_table.item(i, 2)),
                    "onerilen_hedef": safe_float(self.param_table.item(i, 3)),
                    "onerilen_max": safe_float(self.param_table.item(i, 4)),
                })

        if not self.secilen_parametreler:
            QMessageBox.warning(self, "Uyari", "Uygulanacak parametre bulunamadi!")
            return

        mod_text = "AI Optimize" if mod == "ai" else "TDS Orijinal"
        if QMessageBox.question(
                self, "Onay",
                f"{len(self.secilen_parametreler)} parametre '{mod_text}' modunda uygulanacak.\n\n"
                f"Mevcut parametre degerleri degistirilecek.\nDevam etmek istiyor musunuz?") == QMessageBox.Yes:
            self.accept()


class LabBanyoPage(BasePage):
    """Banyo Tanımları Listesi"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        header = QHBoxLayout()
        title = QLabel("🧪 Banyo Tanımları")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 24px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(f"color: {self.theme['text_muted']};")
        header.addWidget(self.stat_label)
        layout.addLayout(header)
        
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara")
        self.search_input.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']};")
        self.search_input.setMaximumWidth(200)
        self.search_input.returnPressed.connect(self._load_data)
        toolbar.addWidget(self.search_input)
        
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("Tüm Hatlar", None)
        self._load_hat_filter()
        self.hat_combo.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']}; min-width: 120px;")
        self.hat_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.hat_combo)
        toolbar.addStretch()
        
        add_btn = QPushButton("➕ Yeni Banyo")
        add_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        add_btn.clicked.connect(self._add_new)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme['bg_card_solid']}; border: 1px solid {self.theme['border']}; border-radius: 8px; gridline-color: {self.theme['border']}; color: {self.theme['text']}; }}
            QTableWidget::item {{ padding: 6px; }}
            QTableWidget::item:selected {{ background: {self.theme['primary']}; }}
            QHeaderView::section {{ background: {self.theme['bg_main']}; color: {self.theme['text']}; padding: 8px; border: none; border-bottom: 2px solid {self.theme['primary']}; font-weight: bold; }}
        """)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Hat", "Tip", "Hacim", "Sıcaklık", "pH", "İşlem"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 60)
        self.table.setColumnWidth(8, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table, 1)
    
    def _load_hat_filter(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod FROM tanim.uretim_hatlari WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no")
            for row in cursor.fetchall():
                self.hat_combo.addItem(row[1], row[0])
            conn.close()
        except Exception: pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = """SELECT b.id, b.kod, b.ad, h.kod, bt.ad, b.hacim_lt, b.sicaklik_hedef, b.ph_hedef
                     FROM uretim.banyo_tanimlari b
                     JOIN tanim.uretim_hatlari h ON b.hat_id=h.id
                     JOIN tanim.banyo_tipleri bt ON b.banyo_tipi_id=bt.id
                     WHERE b.aktif_mi=1"""
            params = []
            
            search = self.search_input.text().strip()
            if search:
                sql += " AND (b.kod LIKE ? OR b.ad LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            
            hat_id = self.hat_combo.currentData()
            if hat_id:
                sql += " AND b.hat_id=?"
                params.append(hat_id)
            
            sql += " ORDER BY h.sira_no, b.kod"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or ''))
                self.table.setItem(i, 4, QTableWidgetItem(row[4] or ''))
                self.table.setItem(i, 5, QTableWidgetItem(f"{row[5]:.0f}" if row[5] else '-'))
                self.table.setItem(i, 6, QTableWidgetItem(f"{row[6]:.0f}°C" if row[6] else '-'))
                self.table.setItem(i, 7, QTableWidgetItem(f"{row[7]:.1f}" if row[7] else '-'))
                
                widget = self.create_action_buttons([
                    ("✏️", "Duzenle", lambda checked, rid=row[0]: self._edit_item(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 8, widget)
                self.table.setRowHeight(i, 42)
            
            self.stat_label.setText(f"Toplam: {len(rows)} banyo")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _add_new(self):
        dlg = BanyoDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _edit_item(self, bid):
        dlg = BanyoDialog(self.theme, bid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _delete_item(self, bid):
        if QMessageBox.question(self, "Onay", "Bu banyoyu silmek istediğinize emin misiniz?") == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM uretim.banyo_tanimlari WHERE id=?", (bid,))
                conn.commit()
                LogManager.log_delete('lab', 'uretim.banyo_tanimlari', None, 'Kayit silindi')
                conn.close()
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))