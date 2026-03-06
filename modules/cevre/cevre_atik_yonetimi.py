# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Çevre Atık Yönetimi
Atık Giriş/Çıkış ve UATF Takibi
[MODERNIZED UI - v2.0]
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QDoubleSpinBox,
    QTabWidget, QDateTimeEdit, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate, QDateTime, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


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


class AtikHareketDialog(QDialog):
    def __init__(self, theme: dict, parent=None, hareket_id=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.hareket_id = hareket_id
        self.setWindowTitle("Atık Hareketi")
        self.setMinimumSize(600, 650)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if hareket_id:
            self._load_data()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }}
            QLabel {{ color: {s['text']}; background: transparent; }}
            QLineEdit, QComboBox, QDateTimeEdit, QDoubleSpinBox, QTextEdit {{
                background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px;
                padding: 10px 12px; color: {s['text']}; font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus {{ border-color: {s['primary']}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{ background: {s['card_bg']}; border: 1px solid {s['border']}; color: {s['text']}; selection-background-color: {s['primary']}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        icon = QLabel("♻️")
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
        
        lbl = QLabel("Hareket No")
        lbl.setStyleSheet(label_style)
        self.txt_no = QLineEdit()
        self.txt_no.setReadOnly(True)
        self.txt_no.setPlaceholderText("Otomatik oluşturulur")
        form.addRow(lbl, self.txt_no)
        
        lbl = QLabel("Hareket Tipi *")
        lbl.setStyleSheet(label_style)
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItem("📥 GİRİŞ", "GIRIS")
        self.cmb_tip.addItem("📤 ÇIKIŞ", "CIKIS")
        self.cmb_tip.addItem("🔄 TRANSFER", "TRANSFER")
        self.cmb_tip.currentIndexChanged.connect(self._on_tip_changed)
        form.addRow(lbl, self.cmb_tip)
        
        lbl = QLabel("Tarih/Saat *")
        lbl.setStyleSheet(label_style)
        self.dt_hareket = QDateTimeEdit()
        self.dt_hareket.setDateTime(QDateTime.currentDateTime())
        self.dt_hareket.setCalendarPopup(True)
        form.addRow(lbl, self.dt_hareket)
        
        lbl = QLabel("Atık *")
        lbl.setStyleSheet(label_style)
        self.cmb_atik = QComboBox()
        form.addRow(lbl, self.cmb_atik)
        
        lbl = QLabel("Depo")
        lbl.setStyleSheet(label_style)
        self.cmb_depo = QComboBox()
        form.addRow(lbl, self.cmb_depo)
        
        lbl = QLabel("Miktar *")
        lbl.setStyleSheet(label_style)
        self.spin_miktar = QDoubleSpinBox()
        self.spin_miktar.setRange(0.001, 999999)
        self.spin_miktar.setDecimals(3)
        self.spin_miktar.setSuffix(" KG")
        form.addRow(lbl, self.spin_miktar)
        
        self.lbl_cikis = QLabel("📤 Çıkış Bilgileri")
        self.lbl_cikis.setStyleSheet(f"font-weight: bold; color: {s['warning']}; margin-top: 10px; font-size: 14px;")
        form.addRow("", self.lbl_cikis)
        
        lbl = QLabel("Lisanslı Firma")
        lbl.setStyleSheet(label_style)
        self.cmb_firma = QComboBox()
        form.addRow(lbl, self.cmb_firma)
        
        lbl = QLabel("UATF No")
        lbl.setStyleSheet(label_style)
        self.txt_uatf = QLineEdit()
        self.txt_uatf.setPlaceholderText("UATF numarası")
        form.addRow(lbl, self.txt_uatf)
        
        lbl = QLabel("Araç Plaka")
        lbl.setStyleSheet(label_style)
        self.txt_plaka = QLineEdit()
        form.addRow(lbl, self.txt_plaka)
        
        lbl = QLabel("Şoför")
        lbl.setStyleSheet(label_style)
        self.txt_sofor = QLineEdit()
        form.addRow(lbl, self.txt_sofor)
        
        lbl = QLabel("Kaynak Bölüm")
        lbl.setStyleSheet(label_style)
        self.cmb_kaynak = QComboBox()
        form.addRow(lbl, self.cmb_kaynak)
        
        lbl = QLabel("Notlar")
        lbl.setStyleSheet(label_style)
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(60)
        form.addRow(lbl, self.txt_notlar)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"""
            QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; font-size: 13px; font-weight: 500; }}
            QPushButton:hover {{ background: {s['border']}; border-color: {s['primary']}; }}
        """)
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾  Kaydet")
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: #059669; }}
        """)
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
        self._on_tip_changed()
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            self.cmb_atik.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, atik_kodu, atik_adi, tehlikeli_mi FROM cevre.atik_tanimlari WHERE aktif_mi = 1 ORDER BY atik_kodu")
            for row in cursor.fetchall():
                tehlike = "⚠️ " if row[3] else ""
                self.cmb_atik.addItem(f"{tehlike}{row[1]} - {row[2][:50]}", row[0])
            self.cmb_depo.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, alan_adi FROM cevre.atik_depolama_alanlari WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_depo.addItem(f"{row[1]} - {row[2]}", row[0])
            self.cmb_firma.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, firma_adi, lisans_no FROM cevre.lisansli_firmalar WHERE aktif_mi = 1 ORDER BY firma_adi")
            for row in cursor.fetchall():
                self.cmb_firma.addItem(f"{row[1]} ({row[2]})", row[0])
            self.cmb_kaynak.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_kaynak.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except: pass
    
    def _on_tip_changed(self):
        is_cikis = self.cmb_tip.currentData() == "CIKIS"
        self.lbl_cikis.setVisible(is_cikis)
        self.cmb_firma.setVisible(is_cikis)
        self.txt_uatf.setVisible(is_cikis)
        self.txt_plaka.setVisible(is_cikis)
        self.txt_sofor.setVisible(is_cikis)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT hareket_no, hareket_tipi, hareket_tarihi, atik_id, depo_id, miktar, firma_id, tasima_formu_no, arac_plaka, sofor_adi, kaynak_bolum_id, notlar FROM cevre.atik_hareketleri WHERE id = ?", (self.hareket_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.txt_no.setText(row[0] or "")
                if row[1]:
                    idx = self.cmb_tip.findData(row[1])
                    if idx >= 0: self.cmb_tip.setCurrentIndex(idx)
                if row[2]: self.dt_hareket.setDateTime(QDateTime(row[2]))
                if row[3]:
                    idx = self.cmb_atik.findData(row[3])
                    if idx >= 0: self.cmb_atik.setCurrentIndex(idx)
                if row[4]:
                    idx = self.cmb_depo.findData(row[4])
                    if idx >= 0: self.cmb_depo.setCurrentIndex(idx)
                self.spin_miktar.setValue(float(row[5] or 0))
                if row[6]:
                    idx = self.cmb_firma.findData(row[6])
                    if idx >= 0: self.cmb_firma.setCurrentIndex(idx)
                self.txt_uatf.setText(row[7] or "")
                self.txt_plaka.setText(row[8] or "")
                self.txt_sofor.setText(row[9] or "")
                if row[10]:
                    idx = self.cmb_kaynak.findData(row[10])
                    if idx >= 0: self.cmb_kaynak.setCurrentIndex(idx)
                self.txt_notlar.setPlainText(row[11] or "")
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _save(self):
        if not self.cmb_atik.currentData():
            QMessageBox.warning(self, "⚠️ Uyarı", "Atık seçimi zorunludur!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            tip = self.cmb_tip.currentData()
            if self.hareket_id:
                cursor.execute("UPDATE cevre.atik_hareketleri SET hareket_tipi = ?, hareket_tarihi = ?, atik_id = ?, depo_id = ?, miktar = ?, firma_id = ?, tasima_formu_no = ?, arac_plaka = ?, sofor_adi = ?, kaynak_bolum_id = ?, notlar = ? WHERE id = ?",
                    (tip, self.dt_hareket.dateTime().toPython(), self.cmb_atik.currentData(), self.cmb_depo.currentData(), self.spin_miktar.value(),
                     self.cmb_firma.currentData() if tip == "CIKIS" else None, self.txt_uatf.text().strip() or None,
                     self.txt_plaka.text().strip() or None, self.txt_sofor.text().strip() or None,
                     self.cmb_kaynak.currentData(), self.txt_notlar.toPlainText().strip() or None, self.hareket_id))
            else:
                tip_kisa = {"GIRIS": "AG", "CIKIS": "AC", "TRANSFER": "AT"}
                cursor.execute(f"SELECT '{tip_kisa.get(tip, 'AH')}-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('0000' + CAST(ISNULL((SELECT MAX(id) FROM cevre.atik_hareketleri), 0) + 1 AS VARCHAR), 4)")
                no = cursor.fetchone()[0]
                cursor.execute("INSERT INTO cevre.atik_hareketleri (hareket_no, hareket_tipi, hareket_tarihi, atik_id, depo_id, miktar, firma_id, tasima_formu_no, arac_plaka, sofor_adi, kaynak_bolum_id, notlar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (no, tip, self.dt_hareket.dateTime().toPython(), self.cmb_atik.currentData(), self.cmb_depo.currentData(), self.spin_miktar.value(),
                     self.cmb_firma.currentData() if tip == "CIKIS" else None, self.txt_uatf.text().strip() or None,
                     self.txt_plaka.text().strip() or None, self.txt_sofor.text().strip() or None,
                     self.cmb_kaynak.currentData(), self.txt_notlar.toPlainText().strip() or None))
                self.txt_no.setText(no)
            conn.commit()
            conn.close()
            QMessageBox.information(self, "✓ Başarılı", "Atık hareketi kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))


class CevreAtikYonetimiPage(BasePage):
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
        icon = QLabel("♻️")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Atık Yönetimi")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Atık giriş/çıkış ve UATF takibi")
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
        
        btn_giris = QPushButton("📥 Atık Girişi")
        btn_giris.setCursor(Qt.PointingHandCursor)
        btn_giris.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: 600; }} QPushButton:hover {{ background: #059669; }}")
        btn_giris.clicked.connect(lambda: self._yeni("GIRIS"))
        toolbar.addWidget(btn_giris)
        
        btn_cikis = QPushButton("📤 Atık Çıkışı")
        btn_cikis.setCursor(Qt.PointingHandCursor)
        btn_cikis.setStyleSheet(f"QPushButton {{ background: {s['warning']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: 600; }} QPushButton:hover {{ background: #D97706; }}")
        btn_cikis.clicked.connect(lambda: self._yeni("CIKIS"))
        toolbar.addWidget(btn_cikis)
        
        toolbar.addStretch()
        
        combo_style = f"QComboBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 12px; color: {s['text']}; min-width: 120px; font-size: 13px; }} QComboBox::drop-down {{ border: none; width: 30px; }} QComboBox QAbstractItemView {{ background: {s['card_bg']}; border: 1px solid {s['border']}; color: {s['text']}; selection-background-color: {s['primary']}; }}"
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItem("📊 Tümü", None)
        self.cmb_tip.addItem("📥 Giriş", "GIRIS")
        self.cmb_tip.addItem("📤 Çıkış", "CIKIS")
        self.cmb_tip.addItem("🔄 Transfer", "TRANSFER")
        self.cmb_tip.setStyleSheet(combo_style)
        self.cmb_tip.currentIndexChanged.connect(self._filter)
        toolbar.addWidget(self.cmb_tip)
        
        btn_yenile = QPushButton("🔄")
        btn_yenile.setToolTip("Yenile")
        btn_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; font-size: 14px; }} QPushButton:hover {{ background: {s['border']}; }}")
        btn_yenile.clicked.connect(self._load_data)
        toolbar.addWidget(btn_yenile)
        
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
        self.table.setHorizontalHeaderLabels(["ID", "No", "Tip", "Tarih", "Atık Kodu", "Atık Adı", "Miktar", "Firma/UATF", "İşlem"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 150)
        self.table.setColumnWidth(8, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT h.id, h.hareket_no, h.hareket_tipi, FORMAT(h.hareket_tarihi, 'dd.MM.yyyy'),
                       a.atik_kodu, a.atik_adi, CAST(h.miktar AS VARCHAR) + ' ' + ISNULL(h.birim, 'KG'),
                       ISNULL(f.firma_adi, h.tasima_formu_no)
                FROM cevre.atik_hareketleri h
                JOIN cevre.atik_tanimlari a ON h.atik_id = a.id
                LEFT JOIN cevre.lisansli_firmalar f ON h.firma_id = f.id
                ORDER BY h.hareket_tarihi DESC
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", f"Hata: {str(e)}")
    
    def _display_data(self, rows):
        s = self.s
        tip_colors = {"GIRIS": s['success'], "CIKIS": s['warning'], "TRANSFER": s['info']}
        tip_text = {"GIRIS": "📥 Giriş", "CIKIS": "📤 Çıkış", "TRANSFER": "🔄 Transfer"}
        toplam_giris = toplam_cikis = 0
        
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 2:
                    item = QTableWidgetItem(tip_text.get(val, val or ""))
                    item.setForeground(QColor(tip_colors.get(val, s['text'])))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)
            
            if row[2] == "GIRIS":
                try: toplam_giris += float(str(row[6]).split()[0])
                except: pass
            elif row[2] == "CIKIS":
                try: toplam_cikis += float(str(row[6]).split()[0])
                except: pass
            
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=row[0]: self._duzenle(rid), "edit"),
            ])
            self.table.setCellWidget(i, 8, widget)
            self.table.setRowHeight(i, 48)
        
        self.stat_label.setText(f"📊 Toplam: {len(rows)} | Giriş: {toplam_giris:.0f} KG | Çıkış: {toplam_cikis:.0f} KG")
    
    def _filter(self):
        tip = self.cmb_tip.currentData()
        if tip is None:
            self._display_data(self.all_rows)
        else:
            self._display_data([r for r in self.all_rows if r[2] == tip])
    
    def _yeni(self, tip="GIRIS"):
        dialog = AtikHareketDialog(self.theme, self)
        idx = dialog.cmb_tip.findData(tip)
        if idx >= 0: dialog.cmb_tip.setCurrentIndex(idx)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self, hareket_id):
        dialog = AtikHareketDialog(self.theme, self, hareket_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
