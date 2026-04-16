# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İSG Saha Denetimleri
Günlük/Haftalık Kontroller ve Bulgular
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QTabWidget,
    QDateTimeEdit
)
from PySide6.QtCore import Qt, QDate, QDateTime
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class DenetimDialog(QDialog):
    """Denetim kaydı"""
    
    def __init__(self, theme: dict, parent=None, denetim_id=None):
        super().__init__(parent)
        self.theme = theme
        self.denetim_id = denetim_id
        self.setWindowTitle("Saha Denetimi" if not denetim_id else "Denetim Düzenle")
        self.setMinimumSize(800, 550)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if denetim_id:
            self._load_data()
            self._load_bulgular()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QComboBox, QDateTimeEdit, QTextEdit {{
                background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px; color: {brand.TEXT};
            }}
            QTabWidget::pane {{ border: 1px solid {brand.BORDER}; }}
            QTabBar::tab {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 10px 20px; }}
            QTabBar::tab:selected {{ background: {brand.PRIMARY}; color: white; }}
        """)
        
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        
        # Tab 1: Genel
        tab_genel = QWidget()
        genel_layout = QFormLayout(tab_genel)
        
        self.txt_no = QLineEdit()
        self.txt_no.setReadOnly(True)
        genel_layout.addRow("Denetim No:", self.txt_no)
        
        self.dt_denetim = QDateTimeEdit()
        self.dt_denetim.setDateTime(QDateTime.currentDateTime())
        self.dt_denetim.setCalendarPopup(True)
        genel_layout.addRow("Tarih/Saat*:", self.dt_denetim)
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["GUNLUK", "HAFTALIK", "AYLIK", "OZEL"])
        genel_layout.addRow("Denetim Tipi:", self.cmb_tip)
        
        self.cmb_bolum = QComboBox()
        genel_layout.addRow("Bölüm:", self.cmb_bolum)
        
        self.txt_alan = QLineEdit()
        genel_layout.addRow("Denetim Alanı:", self.txt_alan)
        
        self.cmb_denetci = QComboBox()
        genel_layout.addRow("Denetçi:", self.cmb_denetci)
        
        self.txt_degerlendirme = QTextEdit()
        self.txt_degerlendirme.setMaximumHeight(80)
        genel_layout.addRow("Genel Değerlendirme:", self.txt_degerlendirme)
        
        tabs.addTab(tab_genel, "📋 Genel")
        
        # Tab 2: Bulgular
        tab_bulgu = QWidget()
        bulgu_layout = QVBoxLayout(tab_bulgu)
        
        toolbar = QHBoxLayout()
        btn_olumlu = QPushButton("✓ Olumlu Ekle")
        btn_olumlu.setStyleSheet(f"background: {brand.SUCCESS}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_olumlu.clicked.connect(lambda: self._add_bulgu("OLUMLU"))
        toolbar.addWidget(btn_olumlu)
        
        btn_uygunsuz = QPushButton("✗ Uygunsuzluk Ekle")
        btn_uygunsuz.setStyleSheet(f"background: {brand.ERROR}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_uygunsuz.clicked.connect(lambda: self._add_bulgu("UYGUNSUZLUK"))
        toolbar.addWidget(btn_uygunsuz)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.clicked.connect(self._remove_bulgu)
        toolbar.addWidget(btn_sil)
        toolbar.addStretch()
        bulgu_layout.addLayout(toolbar)
        
        self.table_bulgu = QTableWidget()
        self.table_bulgu.setColumnCount(4)
        self.table_bulgu.setHorizontalHeaderLabels(["ID", "Tip", "Bulgu", "Durum"])
        self.table_bulgu.setColumnHidden(0, True)
        self.table_bulgu.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_bulgu.setStyleSheet(f"QTableWidget {{ background: {brand.BG_CARD}; color: {brand.TEXT}; }}")
        header = self.table_bulgu.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        bulgu_layout.addWidget(self.table_bulgu)
        
        tabs.addTab(tab_bulgu, "📝 Bulgular")
        layout.addWidget(tabs)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {brand.SUCCESS}; color: white; padding: 10px 24px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            self.cmb_bolum.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_bolum.addItem(f"{row[1]} - {row[2]}", row[0])
            
            self.cmb_denetci.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_denetci.addItem(f"{row[1]} - {row[2]}", row[0])
            
            conn.close()
        except Exception:
            pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT denetim_no, denetim_tarihi, denetim_tipi, bolum_id, denetim_alani,
                       denetci_id, genel_degerlendirme
                FROM isg.denetimler WHERE id = ?
            """, (self.denetim_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_no.setText(row[0] or "")
                if row[1]: self.dt_denetim.setDateTime(QDateTime(row[1]))
                if row[2]:
                    idx = self.cmb_tip.findText(row[2])
                    if idx >= 0: self.cmb_tip.setCurrentIndex(idx)
                if row[3]:
                    idx = self.cmb_bolum.findData(row[3])
                    if idx >= 0: self.cmb_bolum.setCurrentIndex(idx)
                self.txt_alan.setText(row[4] or "")
                if row[5]:
                    idx = self.cmb_denetci.findData(row[5])
                    if idx >= 0: self.cmb_denetci.setCurrentIndex(idx)
                self.txt_degerlendirme.setPlainText(row[6] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _load_bulgular(self):
        if not self.denetim_id: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, bulgu_tipi, bulgu_tanimi, durum
                FROM isg.denetim_bulgulari WHERE denetim_id = ? ORDER BY satir_no
            """, (self.denetim_id,))
            rows = cursor.fetchall()
            conn.close()
            
            self.table_bulgu.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table_bulgu.setItem(i, 0, QTableWidgetItem(str(row[0])))
                tip_item = QTableWidgetItem(row[1] or "")
                if row[1] == "OLUMLU":
                    tip_item.setForeground(QColor(brand.SUCCESS))
                elif row[1] == "UYGUNSUZLUK":
                    tip_item.setForeground(QColor(brand.ERROR))
                self.table_bulgu.setItem(i, 1, tip_item)
                self.table_bulgu.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.table_bulgu.setItem(i, 3, QTableWidgetItem(row[3] or ""))
        except Exception: pass
    
    def _add_bulgu(self, tip):
        if not self.denetim_id:
            QMessageBox.warning(self, "Uyarı", "Önce denetimi kaydedin!")
            return
        
        bulgu, ok = QMessageBox.getText(self, "Bulgu Ekle", "Bulgu tanımı:")
        if not ok or not bulgu: return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(satir_no), 0) + 1 FROM isg.denetim_bulgulari WHERE denetim_id = ?", (self.denetim_id,))
            satir_no = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO isg.denetim_bulgulari (denetim_id, satir_no, bulgu_tipi, bulgu_tanimi)
                VALUES (?, ?, ?, ?)
            """, (self.denetim_id, satir_no, tip, bulgu))
            conn.commit()
            conn.close()
            self._load_bulgular()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _remove_bulgu(self):
        row = self.table_bulgu.currentRow()
        if row < 0: return
        bulgu_id = int(self.table_bulgu.item(row, 0).text())
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM isg.denetim_bulgulari WHERE id = ?", (bulgu_id,))
            conn.commit()
            conn.close()
            self._load_bulgular()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.denetim_id:
                cursor.execute("""
                    UPDATE isg.denetimler SET
                        denetim_tarihi = ?, denetim_tipi = ?, bolum_id = ?, denetim_alani = ?,
                        denetci_id = ?, genel_degerlendirme = ?
                    WHERE id = ?
                """, (
                    self.dt_denetim.dateTime().toPython(), self.cmb_tip.currentText(),
                    self.cmb_bolum.currentData(), self.txt_alan.text().strip() or None,
                    self.cmb_denetci.currentData(), self.txt_degerlendirme.toPlainText().strip() or None,
                    self.denetim_id
                ))
            else:
                cursor.execute("SELECT 'DN-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM isg.denetimler), 0) + 1 AS VARCHAR), 4)")
                no = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO isg.denetimler
                    (denetim_no, denetim_tarihi, denetim_tipi, bolum_id, denetim_alani, denetci_id, genel_degerlendirme)
                    OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    no, self.dt_denetim.dateTime().toPython(), self.cmb_tip.currentText(),
                    self.cmb_bolum.currentData(), self.txt_alan.text().strip() or None,
                    self.cmb_denetci.currentData(), self.txt_degerlendirme.toPlainText().strip() or None
                ))
                self.denetim_id = cursor.fetchone()[0]
                self.txt_no.setText(no)
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Denetim kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class ISGDenetimlerPage(BasePage):
    """İSG Denetimler Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("🔍 Saha Denetimleri")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {brand.TEXT};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {brand.BG_CARD}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Denetim")
        btn_yeni.setStyleSheet(f"background: {brand.SUCCESS}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar_layout.addWidget(btn_duzenle)
        toolbar_layout.addStretch()
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px 12px; color: {brand.TEXT};")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "No", "Tarih", "Tip", "Alan", "Denetçi", "Uygunsuzluk"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 8px; color: {brand.TEXT}; }}
            QTableWidget::item:selected {{ background: {brand.PRIMARY}; }}
            QHeaderView::section {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 10px; font-weight: bold; }}
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        self.lbl_stat = QLabel()
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.id, d.denetim_no, FORMAT(d.denetim_tarihi, 'dd.MM.yyyy HH:mm'), d.denetim_tipi,
                       d.denetim_alani, p.ad + ' ' + p.soyad,
                       (SELECT COUNT(*) FROM isg.denetim_bulgulari WHERE denetim_id = d.id AND bulgu_tipi = 'UYGUNSUZLUK')
                FROM isg.denetimler d
                LEFT JOIN ik.personeller p ON d.denetci_id = p.id
                ORDER BY d.denetim_tarihi DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    if j == 6 and val:  # Uygunsuzluk
                        item = QTableWidgetItem(str(val))
                        item.setForeground(QColor(brand.ERROR))
                    else:
                        item = QTableWidgetItem(str(val) if val else "")
                    self.table.setItem(i, j, item)
            
            self.lbl_stat.setText(f"Toplam: {len(rows)} denetim")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")
    
    def _yeni(self):
        dialog = DenetimDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        denetim_id = int(self.table.item(row, 0).text())
        dialog = DenetimDialog(self.theme, self, denetim_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
