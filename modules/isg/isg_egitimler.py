# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İSG Eğitimler
Eğitim Planı ve Katılımcı Takibi
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QTimeEdit,
    QDoubleSpinBox, QTabWidget
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class EgitimDialog(QDialog):
    """İSG Eğitim planı"""
    
    def __init__(self, theme: dict, parent=None, egitim_id=None):
        super().__init__(parent)
        self.theme = theme
        self.egitim_id = egitim_id
        self.setWindowTitle("Eğitim Planı" if not egitim_id else "Eğitim Düzenle")
        self.setMinimumSize(850, 550)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if egitim_id:
            self._load_data()
            self._load_katilimcilar()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTimeEdit, QTextEdit, QDoubleSpinBox {{
                background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')};
                border-radius: 6px; padding: 8px; color: {self.theme.get('text')};
            }}
            QTabWidget::pane {{ border: 1px solid {self.theme.get('border')}; }}
            QTabBar::tab {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 20px; }}
            QTabBar::tab:selected {{ background: {self.theme.get('primary')}; color: white; }}
        """)
        
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        
        # Tab 1: Genel
        tab_genel = QWidget()
        genel_layout = QFormLayout(tab_genel)
        
        self.txt_no = QLineEdit()
        self.txt_no.setReadOnly(True)
        genel_layout.addRow("Eğitim No:", self.txt_no)
        
        self.cmb_egitim = QComboBox()
        genel_layout.addRow("Eğitim Tanımı*:", self.cmb_egitim)
        
        self.date_egitim = QDateEdit()
        self.date_egitim.setDate(QDate.currentDate())
        self.date_egitim.setCalendarPopup(True)
        genel_layout.addRow("Tarih*:", self.date_egitim)
        
        self.spin_sure = QDoubleSpinBox()
        self.spin_sure.setRange(0.5, 40)
        self.spin_sure.setValue(8)
        self.spin_sure.setSuffix(" saat")
        genel_layout.addRow("Süre:", self.spin_sure)
        
        self.cmb_egitmen_tipi = QComboBox()
        self.cmb_egitmen_tipi.addItems(["IC", "DIS", "OSGB"])
        genel_layout.addRow("Eğitmen Tipi:", self.cmb_egitmen_tipi)
        
        self.txt_egitmen = QLineEdit()
        genel_layout.addRow("Eğitmen:", self.txt_egitmen)
        
        self.txt_yer = QLineEdit()
        genel_layout.addRow("Yer:", self.txt_yer)
        
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["PLANLI", "TAMAMLANDI", "IPTAL"])
        genel_layout.addRow("Durum:", self.cmb_durum)
        
        tabs.addTab(tab_genel, "📋 Genel")
        
        # Tab 2: Katılımcılar
        tab_katilimci = QWidget()
        katilimci_layout = QVBoxLayout(tab_katilimci)
        
        toolbar = QHBoxLayout()
        btn_ekle = QPushButton("➕ Ekle")
        btn_ekle.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_ekle.clicked.connect(self._add_katilimci)
        toolbar.addWidget(btn_ekle)
        
        btn_sil = QPushButton("🗑️ Kaldır")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._remove_katilimci)
        toolbar.addWidget(btn_sil)
        
        toolbar.addStretch()
        
        btn_katildi = QPushButton("✓ Katıldı")
        btn_katildi.clicked.connect(lambda: self._set_katilim(True))
        toolbar.addWidget(btn_katildi)
        
        btn_katilmadi = QPushButton("✗ Katılmadı")
        btn_katilmadi.clicked.connect(lambda: self._set_katilim(False))
        toolbar.addWidget(btn_katilmadi)
        
        katilimci_layout.addLayout(toolbar)
        
        self.table_katilimci = QTableWidget()
        self.table_katilimci.setColumnCount(4)
        self.table_katilimci.setHorizontalHeaderLabels(["ID", "Sicil", "Ad Soyad", "Katıldı"])
        self.table_katilimci.setColumnHidden(0, True)
        self.table_katilimci.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_katilimci.setStyleSheet(f"QTableWidget {{ background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; }}")
        header = self.table_katilimci.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        katilimci_layout.addWidget(self.table_katilimci)
        
        self.lbl_katilimci = QLabel("0 katılımcı")
        katilimci_layout.addWidget(self.lbl_katilimci)
        
        tabs.addTab(tab_katilimci, "👥 Katılımcılar")
        layout.addWidget(tabs)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 24px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            self.cmb_egitim.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, egitim_adi, sure_saat FROM isg.egitim_tanimlari WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_egitim.addItem(f"{row[1]} - {row[2]}", (row[0], row[3]))
            conn.close()
        except:
            pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT egitim_no, egitim_tanim_id, egitim_tarihi, sure_saat, egitmen_tipi,
                       egitmen_adi, egitim_yeri, durum
                FROM isg.egitim_planlari WHERE id = ?
            """, (self.egitim_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_no.setText(row[0] or "")
                if row[1]:
                    for i in range(self.cmb_egitim.count()):
                        data = self.cmb_egitim.itemData(i)
                        if data and data[0] == row[1]:
                            self.cmb_egitim.setCurrentIndex(i)
                            break
                if row[2]: self.date_egitim.setDate(QDate(row[2].year, row[2].month, row[2].day))
                if row[3]: self.spin_sure.setValue(float(row[3]))
                if row[4]:
                    idx = self.cmb_egitmen_tipi.findText(row[4])
                    if idx >= 0: self.cmb_egitmen_tipi.setCurrentIndex(idx)
                self.txt_egitmen.setText(row[5] or "")
                self.txt_yer.setText(row[6] or "")
                if row[7]:
                    idx = self.cmb_durum.findText(row[7])
                    if idx >= 0: self.cmb_durum.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _load_katilimcilar(self):
        if not self.egitim_id: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT k.id, p.sicil_no, p.ad + ' ' + p.soyad, k.katildi_mi
                FROM isg.egitim_katilimcilari k
                JOIN ik.personeller p ON k.personel_id = p.id
                WHERE k.egitim_plan_id = ? ORDER BY p.ad
            """, (self.egitim_id,))
            rows = cursor.fetchall()
            conn.close()
            
            self.table_katilimci.setRowCount(len(rows))
            katilan = 0
            for i, row in enumerate(rows):
                self.table_katilimci.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table_katilimci.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                self.table_katilimci.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                katildi = "✓" if row[3] else "✗"
                item = QTableWidgetItem(katildi)
                item.setForeground(QColor(self.theme.get('success') if row[3] else self.theme.get('danger')))
                self.table_katilimci.setItem(i, 3, item)
                if row[3]: katilan += 1
            
            self.lbl_katilimci.setText(f"{len(rows)} katılımcı | {katilan} katıldı")
        except: pass
    
    def _add_katilimci(self):
        if not self.egitim_id:
            QMessageBox.warning(self, "Uyarı", "Önce eğitimi kaydedin!")
            return
        
        # Basit personel seçimi
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 p.id FROM ik.personeller p
                WHERE p.aktif_mi = 1 AND p.id NOT IN 
                (SELECT personel_id FROM isg.egitim_katilimcilari WHERE egitim_plan_id = ?)
            """, (self.egitim_id,))
            row = cursor.fetchone()
            if not row:
                QMessageBox.information(self, "Bilgi", "Tüm personel zaten eklenmiş!")
                conn.close()
                return
            
            # Tüm personeli ekle
            cursor.execute("""
                INSERT INTO isg.egitim_katilimcilari (egitim_plan_id, personel_id)
                SELECT ?, p.id FROM ik.personeller p
                WHERE p.aktif_mi = 1 AND p.id NOT IN 
                (SELECT personel_id FROM isg.egitim_katilimcilari WHERE egitim_plan_id = ?)
            """, (self.egitim_id, self.egitim_id))
            conn.commit()
            conn.close()
            self._load_katilimcilar()
            QMessageBox.information(self, "Başarılı", "Tüm aktif personel eklendi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _remove_katilimci(self):
        row = self.table_katilimci.currentRow()
        if row < 0: return
        katilimci_id = int(self.table_katilimci.item(row, 0).text())
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM isg.egitim_katilimcilari WHERE id = ?", (katilimci_id,))
            conn.commit()
            conn.close()
            self._load_katilimcilar()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _set_katilim(self, katildi):
        row = self.table_katilimci.currentRow()
        if row < 0: return
        katilimci_id = int(self.table_katilimci.item(row, 0).text())
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE isg.egitim_katilimcilari SET katildi_mi = ?, basari_durumu = ? WHERE id = ?",
                          (katildi, 'BASARILI' if katildi else 'KATILMADI', katilimci_id))
            conn.commit()
            conn.close()
            self._load_katilimcilar()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        data = self.cmb_egitim.currentData()
        if not data:
            QMessageBox.warning(self, "Uyarı", "Eğitim tanımı seçin!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            egitim_tanim_id = data[0]
            
            if self.egitim_id:
                cursor.execute("""
                    UPDATE isg.egitim_planlari SET
                        egitim_tanim_id = ?, egitim_tarihi = ?, sure_saat = ?,
                        egitmen_tipi = ?, egitmen_adi = ?, egitim_yeri = ?, durum = ?
                    WHERE id = ?
                """, (
                    egitim_tanim_id, self.date_egitim.date().toPython(), self.spin_sure.value(),
                    self.cmb_egitmen_tipi.currentText(), self.txt_egitmen.text().strip() or None,
                    self.txt_yer.text().strip() or None, self.cmb_durum.currentText(),
                    self.egitim_id
                ))
            else:
                cursor.execute("SELECT 'EGT-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM isg.egitim_planlari), 0) + 1 AS VARCHAR), 4)")
                no = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO isg.egitim_planlari
                    (egitim_no, egitim_tanim_id, egitim_tarihi, sure_saat, egitmen_tipi, egitmen_adi, egitim_yeri, durum)
                    OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    no, egitim_tanim_id, self.date_egitim.date().toPython(), self.spin_sure.value(),
                    self.cmb_egitmen_tipi.currentText(), self.txt_egitmen.text().strip() or None,
                    self.txt_yer.text().strip() or None, self.cmb_durum.currentText()
                ))
                self.egitim_id = cursor.fetchone()[0]
                self.txt_no.setText(no)
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Eğitim kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class ISGEgitimlerPage(BasePage):
    """İSG Eğitimler Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("📚 İSG Eğitimleri")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Eğitim")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)
        
        toolbar_layout.addStretch()
        
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tümü", "PLANLI", "TAMAMLANDI", "IPTAL"])
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_durum)
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px 12px; color: {self.theme.get('text')};")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "No", "Eğitim", "Tarih", "Süre", "Katılımcı", "Durum", "İşlem"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: 8px; color: {self.theme.get('text')}; }}
            QTableWidget::item:selected {{ background: {self.theme.get('primary')}; }}
            QHeaderView::section {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px; font-weight: bold; }}
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(7, 120)
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        self.lbl_stat = QLabel()
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.id, e.egitim_no, t.egitim_adi, FORMAT(e.egitim_tarihi, 'dd.MM.yyyy'),
                       CAST(e.sure_saat AS VARCHAR) + ' saat',
                       (SELECT COUNT(*) FROM isg.egitim_katilimcilari WHERE egitim_plan_id = e.id),
                       e.durum
                FROM isg.egitim_planlari e
                JOIN isg.egitim_tanimlari t ON e.egitim_tanim_id = t.id
                ORDER BY e.egitim_tarihi DESC
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")
    
    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 6:
                    item = QTableWidgetItem(str(val) if val else "")
                    if val == "TAMAMLANDI":
                        item.setForeground(QColor(self.theme.get('success')))
                    elif val == "IPTAL":
                        item.setForeground(QColor(self.theme.get('danger')))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)

            rid = row[0]
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=rid: self._duzenle_by_id(rid), "edit"),
            ])
            self.table.setCellWidget(i, 7, widget)
            self.table.setRowHeight(i, 42)

        self.lbl_stat.setText(f"Toplam: {len(rows)} eğitim")

    def _duzenle_by_id(self, egitim_id):
        """ID ile eğitim düzenleme (satır butonundan)"""
        dialog = EgitimDialog(self.theme, self, egitim_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _filter(self):
        durum = self.cmb_durum.currentText()
        if durum == "Tümü":
            self._display_data(self.all_rows)
        else:
            self._display_data([r for r in self.all_rows if r[6] == durum])
    
    def _yeni(self):
        dialog = EgitimDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        egitim_id = int(self.table.item(row, 0).text())
        dialog = EgitimDialog(self.theme, self, egitim_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
