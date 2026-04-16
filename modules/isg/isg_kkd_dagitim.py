# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İSG KKD Dağıtım
Kişisel Koruyucu Donanım Dağıtım Takibi
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QSpinBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class KKDDagitimDialog(QDialog):
    """KKD dağıtım kaydı"""
    
    def __init__(self, theme: dict, parent=None, dagitim_id=None):
        super().__init__(parent)
        self.theme = theme
        self.dagitim_id = dagitim_id
        self.setWindowTitle("KKD Dağıtım" if not dagitim_id else "Dağıtım Düzenle")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if dagitim_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QComboBox, QDateEdit, QSpinBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px;
                color: {brand.TEXT};
            }}
        """)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.cmb_personel = QComboBox()
        form.addRow("Personel*:", self.cmb_personel)
        
        self.cmb_kkd = QComboBox()
        self.cmb_kkd.currentIndexChanged.connect(self._on_kkd_changed)
        form.addRow("KKD*:", self.cmb_kkd)
        
        self.date_dagitim = QDateEdit()
        self.date_dagitim.setDate(QDate.currentDate())
        self.date_dagitim.setCalendarPopup(True)
        form.addRow("Dağıtım Tarihi:", self.date_dagitim)
        
        self.spin_miktar = QSpinBox()
        self.spin_miktar.setRange(1, 100)
        self.spin_miktar.setValue(1)
        form.addRow("Miktar:", self.spin_miktar)
        
        self.cmb_beden = QComboBox()
        self.cmb_beden.addItems(["", "XS", "S", "M", "L", "XL", "XXL", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45"])
        form.addRow("Beden/Numara:", self.cmb_beden)
        
        self.date_sonraki = QDateEdit()
        self.date_sonraki.setDate(QDate.currentDate().addDays(30))
        self.date_sonraki.setCalendarPopup(True)
        form.addRow("Sonraki Dağıtım:", self.date_sonraki)
        
        self.txt_notlar = QLineEdit()
        form.addRow("Notlar:", self.txt_notlar)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 10px 20px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {brand.SUCCESS}; color: white; padding: 10px 20px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            self.cmb_personel.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_personel.addItem(f"{row[1]} - {row[2]}", row[0])
            
            self.cmb_kkd.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, kkd_adi, dagilim_periyot_gun FROM isg.kkd_tanimlari WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_kkd.addItem(f"{row[1]} - {row[2]}", (row[0], row[3]))
            
            conn.close()
        except Exception:
            pass
    
    def _on_kkd_changed(self, index):
        data = self.cmb_kkd.currentData()
        if data and data[1]:
            self.date_sonraki.setDate(QDate.currentDate().addDays(data[1]))
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT personel_id, kkd_id, dagitim_tarihi, miktar, beden, sonraki_dagitim_tarihi, notlar
                FROM isg.kkd_dagitim WHERE id = ?
            """, (self.dagitim_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                if row[0]:
                    idx = self.cmb_personel.findData(row[0])
                    if idx >= 0: self.cmb_personel.setCurrentIndex(idx)
                if row[1]:
                    for i in range(self.cmb_kkd.count()):
                        data = self.cmb_kkd.itemData(i)
                        if data and data[0] == row[1]:
                            self.cmb_kkd.setCurrentIndex(i)
                            break
                if row[2]: self.date_dagitim.setDate(QDate(row[2].year, row[2].month, row[2].day))
                self.spin_miktar.setValue(row[3] or 1)
                if row[4]:
                    idx = self.cmb_beden.findText(row[4])
                    if idx >= 0: self.cmb_beden.setCurrentIndex(idx)
                if row[5]: self.date_sonraki.setDate(QDate(row[5].year, row[5].month, row[5].day))
                self.txt_notlar.setText(row[6] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        if not self.cmb_personel.currentData():
            QMessageBox.warning(self, "Uyarı", "Personel seçimi zorunludur!")
            return
        data = self.cmb_kkd.currentData()
        if not data:
            QMessageBox.warning(self, "Uyarı", "KKD seçimi zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            kkd_id = data[0]
            
            if self.dagitim_id:
                cursor.execute("""
                    UPDATE isg.kkd_dagitim SET
                        personel_id = ?, kkd_id = ?, dagitim_tarihi = ?, miktar = ?, beden = ?,
                        sonraki_dagitim_tarihi = ?, notlar = ?
                    WHERE id = ?
                """, (
                    self.cmb_personel.currentData(), kkd_id, self.date_dagitim.date().toPython(),
                    self.spin_miktar.value(), self.cmb_beden.currentText() or None,
                    self.date_sonraki.date().toPython(), self.txt_notlar.text().strip() or None,
                    self.dagitim_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO isg.kkd_dagitim
                    (personel_id, kkd_id, dagitim_tarihi, miktar, beden, sonraki_dagitim_tarihi, notlar)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.cmb_personel.currentData(), kkd_id, self.date_dagitim.date().toPython(),
                    self.spin_miktar.value(), self.cmb_beden.currentText() or None,
                    self.date_sonraki.date().toPython(), self.txt_notlar.text().strip() or None
                ))
            
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class ISGKKDDagitimPage(BasePage):
    """İSG KKD Dağıtım Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("🦺 KKD Dağıtım Takibi")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {brand.TEXT};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {brand.BG_CARD}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ KKD Dağıt")
        btn_yeni.setStyleSheet(f"background: {brand.SUCCESS}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)
        
        btn_geciken = QPushButton("⚠️ Geciken Dağıtımlar")
        btn_geciken.setStyleSheet(f"background: {brand.WARNING}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_geciken.clicked.connect(self._show_geciken)
        toolbar_layout.addWidget(btn_geciken)
        
        toolbar_layout.addStretch()
        
        self.txt_arama = QLineEdit()
        self.txt_arama.setPlaceholderText("🔍 Personel ara...")
        self.txt_arama.setFixedWidth(200)
        self.txt_arama.setStyleSheet(f"background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px; color: {brand.TEXT};")
        self.txt_arama.textChanged.connect(self._filter)
        toolbar_layout.addWidget(self.txt_arama)
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px 12px; color: {brand.TEXT};")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Personel", "KKD", "Dağıtım", "Miktar", "Beden", "Sonraki", "Kalan Gün"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 8px; color: {brand.TEXT}; }}
            QTableWidget::item:selected {{ background: {brand.PRIMARY}; }}
            QHeaderView::section {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 10px; font-weight: bold; }}
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 80)
        layout.addWidget(self.table)
        
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(f"color: {brand.TEXT_DIM};")
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.id, p.ad + ' ' + p.soyad, k.kkd_adi,
                       FORMAT(d.dagitim_tarihi, 'dd.MM.yyyy'), d.miktar, d.beden,
                       FORMAT(d.sonraki_dagitim_tarihi, 'dd.MM.yyyy'),
                       DATEDIFF(DAY, GETDATE(), d.sonraki_dagitim_tarihi) as kalan_gun
                FROM isg.kkd_dagitim d
                JOIN ik.personeller p ON d.personel_id = p.id
                JOIN isg.kkd_tanimlari k ON d.kkd_id = k.id
                ORDER BY d.sonraki_dagitim_tarihi ASC
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")
    
    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        geciken = 0
        
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 7:  # Kalan gün
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    if val is not None and val < 0:
                        item.setForeground(QColor(brand.ERROR))
                        item.setText(f"{val} (GECİKMİŞ)")
                        geciken += 1
                    elif val is not None and val <= 7:
                        item.setForeground(QColor(brand.WARNING))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)
        
        self.lbl_stat.setText(f"Toplam: {len(rows)} dağıtım | Gecikmiş: {geciken}")
    
    def _filter(self):
        arama = self.txt_arama.text().lower()
        if not arama:
            self._display_data(self.all_rows)
        else:
            filtered = [r for r in self.all_rows if arama in str(r[1]).lower() or arama in str(r[2]).lower()]
            self._display_data(filtered)
    
    def _show_geciken(self):
        geciken = [r for r in self.all_rows if r[7] is not None and r[7] < 0]
        self._display_data(geciken)
    
    def _yeni(self):
        dialog = KKDDagitimDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
