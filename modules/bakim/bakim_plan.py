# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Periyodik Bakım Planları
bakim.periyodik_bakim_planlari tablosu için CRUD
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QSpinBox, QDoubleSpinBox, QTextEdit, QComboBox, QDateEdit,
    QCheckBox, QWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager


def get_modern_style(theme: dict) -> dict:
    t = theme or {}
    return {
        'card_bg': t.get('bg_card', '#151B23'),
        'input_bg': t.get('bg_input', '#232C3B'),
        'border': t.get('border', '#1E2736'),
        'text': t.get('text', '#E8ECF1'),
        'text_secondary': t.get('text_secondary', '#8896A6'),
        'text_muted': t.get('text_muted', '#5C6878'),
        'primary': t.get('primary', '#DC2626'),
        'primary_hover': t.get('primary_hover', '#9B1818'),
        'success': t.get('success', '#10B981'),
        'warning': t.get('warning', '#F59E0B'),
        'error': t.get('error', '#EF4444'),
        'danger': t.get('error', '#EF4444'),
        'info': t.get('info', '#3B82F6'),
        'bg_main': t.get('bg_main', '#0F1419'),
        'bg_hover': t.get('bg_hover', '#1C2430'),
        'bg_selected': t.get('bg_selected', '#1E1215'),
        'border_light': t.get('border_light', '#2A3545'),
        'border_input': t.get('border_input', '#1E2736'),
        'card_solid': t.get('bg_card_solid', '#151B23'),
        'gradient': t.get('gradient_css', ''),
    }


class BakimPlanDialog(QDialog):
    def __init__(self, theme: dict, plan_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.plan_id = plan_id
        self.data = {}
        
        self.setWindowTitle("Yeni Bakım Planı" if not plan_id else "Bakım Planı Düzenle")
        self.setMinimumSize(600, 720)
        self.setModal(True)
        
        if plan_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bakim.periyodik_bakim_planlari WHERE id = ?", (self.plan_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }}
            QLabel {{ color: {s['text']}; background: transparent; }}
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
                background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px;
                padding: 10px 12px; color: {s['text']}; font-size: 13px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{ border-color: {s['primary']}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{ background: {s['card_bg']}; border: 1px solid {s['border']}; color: {s['text']}; selection-background-color: {s['primary']}; }}
            QCheckBox {{ color: {s['text']}; font-size: 13px; spacing: 8px; }}
            QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 4px; border: 2px solid {s['border']}; background: {s['input_bg']}; }}
            QCheckBox::indicator:checked {{ background: {s['primary']}; border-color: {s['primary']}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 28px;")
        header.addWidget(icon)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {s['border']}; max-height: 1px;")
        layout.addWidget(sep)
        
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        
        lbl = QLabel("Plan Kodu *")
        lbl.setStyleSheet(label_style)
        self.kod_input = QLineEdit(self.data.get('plan_kodu', ''))
        self.kod_input.setPlaceholderText("Örn: PBP-001")
        form.addRow(lbl, self.kod_input)
        
        lbl = QLabel("Plan Adı *")
        lbl.setStyleSheet(label_style)
        self.ad_input = QLineEdit(self.data.get('plan_adi', ''))
        self.ad_input.setPlaceholderText("Örn: Pompa Haftalık Bakım")
        form.addRow(lbl, self.ad_input)
        
        lbl = QLabel("Hedef Tipi")
        lbl.setStyleSheet(label_style)
        self.hedef_combo = QComboBox()
        self.hedef_combo.addItem("🔧 Ekipman", "ekipman")
        self.hedef_combo.addItem("📍 Pozisyon", "pozisyon")
        self.hedef_combo.addItem("🤖 Robot", "robot")
        self.hedef_combo.currentIndexChanged.connect(self._on_hedef_change)
        form.addRow(lbl, self.hedef_combo)
        
        lbl = QLabel("Hedef Seçimi *")
        lbl.setStyleSheet(label_style)
        self.hedef_secim_combo = QComboBox()
        self.hedef_secim_combo.addItem("-- Seçiniz --", None)
        form.addRow(lbl, self.hedef_secim_combo)
        
        lbl = QLabel("Bakım Tipi *")
        lbl.setStyleSheet(label_style)
        self.bakim_tipi_combo = QComboBox()
        self.bakim_tipi_combo.addItem("📅 Periyodik (Gün)", "PERIYODIK")
        self.bakim_tipi_combo.addItem("⏱️ Çalışma Saati", "CALISMA_SAATI")
        self.bakim_tipi_combo.addItem("🔢 Sayaç Bazlı", "SAYAC")
        if self.data.get('bakim_tipi'):
            idx = self.bakim_tipi_combo.findData(self.data['bakim_tipi'])
            if idx >= 0: self.bakim_tipi_combo.setCurrentIndex(idx)
        self.bakim_tipi_combo.currentIndexChanged.connect(self._on_bakim_tipi_change)
        form.addRow(lbl, self.bakim_tipi_combo)
        
        lbl = QLabel("Periyot (Gün)")
        lbl.setStyleSheet(label_style)
        self.periyot_gun_input = QSpinBox()
        self.periyot_gun_input.setRange(1, 9999)
        self.periyot_gun_input.setSuffix(" gün")
        self.periyot_gun_input.setValue(self.data.get('periyot_gun', 30) or 30)
        form.addRow(lbl, self.periyot_gun_input)
        
        lbl = QLabel("Periyot (Saat)")
        lbl.setStyleSheet(label_style)
        self.periyot_saat_input = QSpinBox()
        self.periyot_saat_input.setRange(1, 99999)
        self.periyot_saat_input.setSuffix(" saat")
        self.periyot_saat_input.setValue(self.data.get('periyot_calisma_saati', 500) or 500)
        form.addRow(lbl, self.periyot_saat_input)
        
        lbl = QLabel("Periyot (Sayaç)")
        lbl.setStyleSheet(label_style)
        self.periyot_sayac_input = QDoubleSpinBox()
        self.periyot_sayac_input.setRange(1, 9999999)
        self.periyot_sayac_input.setValue(self.data.get('periyot_sayac', 1000) or 1000)
        form.addRow(lbl, self.periyot_sayac_input)
        
        lbl = QLabel("Sonraki Bakım *")
        lbl.setStyleSheet(label_style)
        self.sonraki_tarih = QDateEdit()
        self.sonraki_tarih.setCalendarPopup(True)
        self.sonraki_tarih.setDisplayFormat("dd.MM.yyyy")
        if self.data.get('sonraki_bakim_tarihi'):
            self.sonraki_tarih.setDate(self.data['sonraki_bakim_tarihi'])
        else:
            self.sonraki_tarih.setDate(QDate.currentDate().addDays(30))
        form.addRow(lbl, self.sonraki_tarih)
        
        lbl = QLabel("Tahmini Süre")
        lbl.setStyleSheet(label_style)
        self.sure_input = QSpinBox()
        self.sure_input.setRange(0, 9999)
        self.sure_input.setSuffix(" dk")
        self.sure_input.setValue(self.data.get('tahmini_sure_dk', 60) or 60)
        form.addRow(lbl, self.sure_input)
        
        lbl = QLabel("Uyarı")
        lbl.setStyleSheet(label_style)
        self.uyari_gun_input = QSpinBox()
        self.uyari_gun_input.setRange(0, 365)
        self.uyari_gun_input.setSuffix(" gün önce")
        self.uyari_gun_input.setValue(self.data.get('uyari_gun_oncesi', 7) or 7)
        form.addRow(lbl, self.uyari_gun_input)
        
        self.kritik_check = QCheckBox("🔴 Bu bakım kritik")
        self.kritik_check.setChecked(self.data.get('kritik_mi', False) or False)
        form.addRow("", self.kritik_check)
        
        lbl = QLabel("Talimat")
        lbl.setStyleSheet(label_style)
        self.talimat_input = QTextEdit()
        self.talimat_input.setMaximumHeight(80)
        self.talimat_input.setPlaceholderText("Bakım talimatları...")
        self.talimat_input.setText(self.data.get('talimat', '') or '')
        form.addRow(lbl, self.talimat_input)
        
        lbl = QLabel("Durum")
        lbl.setStyleSheet(label_style)
        self.aktif_combo = QComboBox()
        self.aktif_combo.addItem("✅ Aktif", True)
        self.aktif_combo.addItem("❌ Pasif", False)
        self.aktif_combo.setCurrentIndex(0 if self.data.get('aktif_mi', True) else 1)
        form.addRow(lbl, self.aktif_combo)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; font-size: 13px; font-weight: 500; }}
            QPushButton:hover {{ background: {s['border']}; border-color: {s['primary']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾  Kaydet")
        save_btn.setStyleSheet(f"""
            QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        self._on_hedef_change()
        self._on_bakim_tipi_change()
    
    def _on_hedef_change(self):
        self.hedef_secim_combo.clear()
        self.hedef_secim_combo.addItem("-- Seçiniz --", None)
        hedef = self.hedef_combo.currentData()
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if hedef == "ekipman":
                cursor.execute("SELECT id, ekipman_kodu + ' - ' + ekipman_adi FROM bakim.ekipmanlar WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY ekipman_kodu")
            elif hedef == "pozisyon":
                cursor.execute("SELECT id, ad FROM tanim.hat_pozisyonlar WHERE aktif_mi=1 ORDER BY sira_no")
            elif hedef == "robot":
                cursor.execute("SELECT id, ad FROM tanim.hat_robotlar WHERE aktif_mi=1 ORDER BY ad")
            for row in cursor.fetchall():
                self.hedef_secim_combo.addItem(row[1], row[0])
            if hedef == "ekipman" and self.data.get('ekipman_id'):
                idx = self.hedef_secim_combo.findData(self.data['ekipman_id'])
                if idx >= 0: self.hedef_secim_combo.setCurrentIndex(idx)
            elif hedef == "pozisyon" and self.data.get('pozisyon_id'):
                idx = self.hedef_secim_combo.findData(self.data['pozisyon_id'])
                if idx >= 0: self.hedef_secim_combo.setCurrentIndex(idx)
            elif hedef == "robot" and self.data.get('robot_id'):
                idx = self.hedef_secim_combo.findData(self.data['robot_id'])
                if idx >= 0: self.hedef_secim_combo.setCurrentIndex(idx)
        except Exception: pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _on_bakim_tipi_change(self):
        tip = self.bakim_tipi_combo.currentData()
        self.periyot_gun_input.setEnabled(tip == "PERIYODIK")
        self.periyot_saat_input.setEnabled(tip == "CALISMA_SAATI")
        self.periyot_sayac_input.setEnabled(tip == "SAYAC")
    
    def _save(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()
        hedef_id = self.hedef_secim_combo.currentData()
        if not kod or not ad or not hedef_id:
            QMessageBox.warning(self, "⚠️ Eksik Bilgi", "Plan Kodu, Adı ve Hedef zorunludur!")
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            hedef_tip = self.hedef_combo.currentData()
            ekipman_id = hedef_id if hedef_tip == "ekipman" else None
            pozisyon_id = hedef_id if hedef_tip == "pozisyon" else None
            robot_id = hedef_id if hedef_tip == "robot" else None
            params = (
                kod, ad, ekipman_id, pozisyon_id, robot_id, self.bakim_tipi_combo.currentData(),
                self.periyot_gun_input.value() if self.bakim_tipi_combo.currentData() == "PERIYODIK" else None,
                self.periyot_saat_input.value() if self.bakim_tipi_combo.currentData() == "CALISMA_SAATI" else None,
                self.periyot_sayac_input.value() if self.bakim_tipi_combo.currentData() == "SAYAC" else None,
                self.sonraki_tarih.date().toPython(), self.sure_input.value(), self.uyari_gun_input.value(),
                self.kritik_check.isChecked(), self.talimat_input.toPlainText().strip() or None, self.aktif_combo.currentData()
            )
            if self.plan_id:
                cursor.execute("""UPDATE bakim.periyodik_bakim_planlari SET plan_kodu=?, plan_adi=?,
                    ekipman_id=?, pozisyon_id=?, robot_id=?, bakim_tipi=?, periyot_gun=?, periyot_calisma_saati=?, periyot_sayac=?,
                    sonraki_bakim_tarihi=?, tahmini_sure_dk=?, uyari_gun_oncesi=?, kritik_mi=?, talimat=?, aktif_mi=?, guncelleme_tarihi=GETDATE() WHERE id=?""",
                    params + (self.plan_id,))
            else:
                cursor.execute("""INSERT INTO bakim.periyodik_bakim_planlari (plan_kodu, plan_adi,
                    ekipman_id, pozisyon_id, robot_id, bakim_tipi, periyot_gun, periyot_calisma_saati, periyot_sayac,
                    sonraki_bakim_tarihi, tahmini_sure_dk, uyari_gun_oncesi, kritik_mi, talimat, aktif_mi) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", params)
            conn.commit()
            LogManager.log_insert('bakim', 'bakim.periyodik_bakim_planlari', None, 'Bakim plani eklendi')
            QMessageBox.information(self, "✓ Başarılı", "Bakım planı kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass


class BakimPlanPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        title_row = QHBoxLayout()
        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Periyodik Bakım Planları")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Periyodik bakım planlarını oluşturun ve takip edin")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px; padding: 8px 16px; background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px;")
        header.addWidget(self.stat_label)
        layout.addLayout(header)
        
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara (Kod, Ad)")
        self.search_input.setStyleSheet(f"QLineEdit {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; color: {s['text']}; font-size: 13px; min-width: 200px; }} QLineEdit:focus {{ border-color: {s['primary']}; }}")
        self.search_input.returnPressed.connect(self._load_data)
        toolbar.addWidget(self.search_input)
        
        combo_style = f"QComboBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 12px; color: {s['text']}; min-width: 130px; font-size: 13px; }} QComboBox:hover {{ border-color: {s['border_light']}; }} QComboBox::drop-down {{ border: none; width: 30px; }} QComboBox QAbstractItemView {{ background: {s['card_bg']}; border: 1px solid {s['border']}; color: {s['text']}; selection-background-color: {s['primary']}; }}"
        self.tip_combo = QComboBox()
        self.tip_combo.addItem("📊 Tüm Tipler", None)
        self.tip_combo.addItem("📅 Periyodik", "PERIYODIK")
        self.tip_combo.addItem("⏱️ Çalışma Saati", "CALISMA_SAATI")
        self.tip_combo.addItem("🔢 Sayaç", "SAYAC")
        self.tip_combo.setStyleSheet(combo_style)
        self.tip_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.tip_combo)
        toolbar.addStretch()
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Yenile")
        refresh_btn.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; font-size: 14px; }} QPushButton:hover {{ background: {s['border']}; border-color: {s['primary']}; }}")
        refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(refresh_btn)
        
        add_btn = QPushButton("➕  Yeni Plan")
        add_btn.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: 600; }} QPushButton:hover {{ background: {s['primary_hover']}; }}")
        add_btn.clicked.connect(self._add_new)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; color: {s['text']}; }}
            QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }}
            QTableWidget::item:selected {{ background: {s['primary']}; }}
            QTableWidget::item:hover {{ background: rgba(220, 38, 38, 0.1); }}
            QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
        """)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Kod", "Plan Adı", "Hedef", "Tip", "Periyot", "Sonraki", "Kalan", "İşlem"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 85)
        self.table.setColumnWidth(6, 95)
        self.table.setColumnWidth(7, 75)
        self.table.setColumnWidth(8, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_data(self):
        s = self.s
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """SELECT p.id, p.plan_kodu, p.plan_adi,
                     COALESCE(e.ekipman_kodu + ' - ' + e.ekipman_adi, pz.ad, r.ad, '-') as hedef,
                     p.bakim_tipi, p.periyot_gun, p.periyot_calisma_saati, p.periyot_sayac,
                     p.sonraki_bakim_tarihi, DATEDIFF(day, GETDATE(), p.sonraki_bakim_tarihi) as kalan_gun, p.kritik_mi
                     FROM bakim.periyodik_bakim_planlari p
                     LEFT JOIN bakim.ekipmanlar e ON p.ekipman_id=e.id
                     LEFT JOIN tanim.hat_pozisyonlar pz ON p.pozisyon_id=pz.id
                     LEFT JOIN tanim.hat_robotlar r ON p.robot_id=r.id
                     WHERE p.aktif_mi=1"""
            params = []
            search = self.search_input.text().strip()
            if search:
                sql += " AND (p.plan_kodu LIKE ? OR p.plan_adi LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            tip = self.tip_combo.currentData()
            if tip:
                sql += " AND p.bakim_tipi=?"
                params.append(tip)
            sql += " ORDER BY p.sonraki_bakim_tarihi"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            tip_map = {"PERIYODIK": "📅 Periyodik", "CALISMA_SAATI": "⏱️ Saat", "SAYAC": "🔢 Sayaç"}
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                item = QTableWidgetItem(str(row[0]))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor(s['text_muted']))
                self.table.setItem(i, 0, item)
                kod_item = QTableWidgetItem(row[1] or '')
                if row[10]: kod_item.setForeground(QColor(s['error']))
                self.table.setItem(i, 1, kod_item)
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or '-'))
                tip_item = QTableWidgetItem(tip_map.get(row[4], row[4] or ''))
                tip_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 4, tip_item)
                if row[4] == "PERIYODIK": periyot = f"{row[5]} gün"
                elif row[4] == "CALISMA_SAATI": periyot = f"{row[6]} saat"
                else: periyot = f"{row[7]}"
                periyot_item = QTableWidgetItem(periyot)
                periyot_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 5, periyot_item)
                sonraki = row[8].strftime("%d.%m.%Y") if row[8] else '-'
                sonraki_item = QTableWidgetItem(sonraki)
                sonraki_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 6, sonraki_item)
                kalan = row[9] or 0
                kalan_item = QTableWidgetItem(f"{kalan} gün")
                kalan_item.setTextAlignment(Qt.AlignCenter)
                if kalan < 0: kalan_item.setForeground(QColor(s['error']))
                elif kalan <= 7: kalan_item.setForeground(QColor(s['warning']))
                else: kalan_item.setForeground(QColor(s['success']))
                self.table.setItem(i, 7, kalan_item)
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, rid=row[0]: self._edit_item(rid), "edit"),
                    ("🗑️", "Pasif Yap", lambda checked, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 8, widget)
                self.table.setRowHeight(i, 48)
            self.stat_label.setText(f"📊 Toplam: {len(rows)} plan")
        except Exception as e:
            QMessageBox.warning(self, "⚠️ Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

    def _add_new(self):
        dlg = BakimPlanDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _edit_item(self, pid):
        dlg = BakimPlanDialog(self.theme, pid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _delete_item(self, pid):
        if QMessageBox.question(self, "🗑️ Pasif Yapma Onayı", "Bu planı pasif yapmak istediğinize emin misiniz?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE bakim.periyodik_bakim_planlari SET aktif_mi=0 WHERE id=?", (pid,))
                conn.commit()
                LogManager.log_update('bakim', 'bakim.periyodik_bakim_planlari', None, 'Aktiflik durumu degistirildi')
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "❌ Hata", str(e))
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass
