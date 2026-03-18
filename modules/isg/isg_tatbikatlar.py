# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İSG Tatbikatlar
Acil Durum Tatbikatları Planı ve Değerlendirme
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateTimeEdit, QTextEdit, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class TatbikatDialog(QDialog):
    """Tatbikat kaydı"""
    
    def __init__(self, theme: dict, parent=None, tatbikat_id=None):
        super().__init__(parent)
        self.theme = theme
        self.tatbikat_id = tatbikat_id
        self.setWindowTitle("Tatbikat" if not tatbikat_id else "Tatbikat Düzenle")
        self.setMinimumWidth(550)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if tatbikat_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateTimeEdit, QTextEdit, QSpinBox {{
                background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')};
                border-radius: 6px; padding: 8px; color: {self.theme.get('text')};
            }}
            QCheckBox {{ color: {self.theme.get('text')}; }}
        """)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.txt_no = QLineEdit()
        self.txt_no.setReadOnly(True)
        form.addRow("Tatbikat No:", self.txt_no)
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["YANGIN", "DEPREM", "KIMYASAL_SIZINTI", "GENEL_TAHLIYE"])
        form.addRow("Tatbikat Tipi*:", self.cmb_tip)
        
        self.dt_tatbikat = QDateTimeEdit()
        self.dt_tatbikat.setDateTime(QDateTime.currentDateTime())
        self.dt_tatbikat.setCalendarPopup(True)
        form.addRow("Tarih/Saat*:", self.dt_tatbikat)
        
        self.chk_tum_tesis = QCheckBox("Tüm Tesis")
        self.chk_tum_tesis.setChecked(True)
        form.addRow("", self.chk_tum_tesis)
        
        self.txt_kapsam = QLineEdit()
        self.txt_kapsam.setPlaceholderText("Belirli bölümler için...")
        form.addRow("Kapsam:", self.txt_kapsam)
        
        self.cmb_sorumlu = QComboBox()
        form.addRow("Sorumlu:", self.cmb_sorumlu)
        
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["PLANLI", "TAMAMLANDI", "IPTAL"])
        form.addRow("Durum:", self.cmb_durum)
        
        # Sonuçlar (tamamlandı için)
        lbl_sonuc = QLabel("📊 Sonuçlar")
        lbl_sonuc.setStyleSheet(f"font-weight: bold; color: {self.theme.get('primary')}; margin-top: 10px;")
        form.addRow("", lbl_sonuc)
        
        self.spin_katilimci = QSpinBox()
        self.spin_katilimci.setRange(0, 1000)
        form.addRow("Katılımcı Sayısı:", self.spin_katilimci)
        
        self.spin_sure = QSpinBox()
        self.spin_sure.setRange(0, 60)
        self.spin_sure.setSuffix(" dk")
        form.addRow("Tahliye Süresi:", self.spin_sure)
        
        self.chk_basarili = QCheckBox("Başarılı")
        form.addRow("", self.chk_basarili)
        
        self.txt_eksik = QTextEdit()
        self.txt_eksik.setMaximumHeight(60)
        self.txt_eksik.setPlaceholderText("Tespit edilen eksiklikler...")
        form.addRow("Eksiklikler:", self.txt_eksik)
        
        self.txt_onlem = QTextEdit()
        self.txt_onlem.setMaximumHeight(60)
        self.txt_onlem.setPlaceholderText("Alınacak önlemler...")
        form.addRow("Önlemler:", self.txt_onlem)
        
        layout.addLayout(form)
        
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
            self.cmb_sorumlu.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_sorumlu.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception:
            pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tatbikat_no, tatbikat_tipi, tatbikat_tarihi, tum_tesis_mi, kapsam_aciklama,
                       sorumlu_id, durum, katilimci_sayisi, tahliye_suresi_dk, basarili_mi,
                       tespit_edilen_eksikler, alinacak_onlemler
                FROM isg.tatbikatlar WHERE id = ?
            """, (self.tatbikat_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_no.setText(row[0] or "")
                if row[1]:
                    idx = self.cmb_tip.findText(row[1])
                    if idx >= 0: self.cmb_tip.setCurrentIndex(idx)
                if row[2]: self.dt_tatbikat.setDateTime(QDateTime(row[2]))
                self.chk_tum_tesis.setChecked(row[3] if row[3] is not None else True)
                self.txt_kapsam.setText(row[4] or "")
                if row[5]:
                    idx = self.cmb_sorumlu.findData(row[5])
                    if idx >= 0: self.cmb_sorumlu.setCurrentIndex(idx)
                if row[6]:
                    idx = self.cmb_durum.findText(row[6])
                    if idx >= 0: self.cmb_durum.setCurrentIndex(idx)
                self.spin_katilimci.setValue(row[7] or 0)
                self.spin_sure.setValue(row[8] or 0)
                self.chk_basarili.setChecked(row[9] if row[9] is not None else False)
                self.txt_eksik.setPlainText(row[10] or "")
                self.txt_onlem.setPlainText(row[11] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.tatbikat_id:
                cursor.execute("""
                    UPDATE isg.tatbikatlar SET
                        tatbikat_tipi = ?, tatbikat_tarihi = ?, tum_tesis_mi = ?, kapsam_aciklama = ?,
                        sorumlu_id = ?, durum = ?, katilimci_sayisi = ?, tahliye_suresi_dk = ?,
                        basarili_mi = ?, tespit_edilen_eksikler = ?, alinacak_onlemler = ?
                    WHERE id = ?
                """, (
                    self.cmb_tip.currentText(), self.dt_tatbikat.dateTime().toPython(),
                    self.chk_tum_tesis.isChecked(), self.txt_kapsam.text().strip() or None,
                    self.cmb_sorumlu.currentData(), self.cmb_durum.currentText(),
                    self.spin_katilimci.value() or None, self.spin_sure.value() or None,
                    self.chk_basarili.isChecked() if self.cmb_durum.currentText() == "TAMAMLANDI" else None,
                    self.txt_eksik.toPlainText().strip() or None,
                    self.txt_onlem.toPlainText().strip() or None,
                    self.tatbikat_id
                ))
            else:
                cursor.execute("SELECT 'TAT-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM isg.tatbikatlar), 0) + 1 AS VARCHAR), 4)")
                no = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO isg.tatbikatlar
                    (tatbikat_no, tatbikat_tipi, tatbikat_tarihi, tum_tesis_mi, kapsam_aciklama,
                     sorumlu_id, durum, katilimci_sayisi, tahliye_suresi_dk, basarili_mi,
                     tespit_edilen_eksikler, alinacak_onlemler)
                    OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    no, self.cmb_tip.currentText(), self.dt_tatbikat.dateTime().toPython(),
                    self.chk_tum_tesis.isChecked(), self.txt_kapsam.text().strip() or None,
                    self.cmb_sorumlu.currentData(), self.cmb_durum.currentText(),
                    self.spin_katilimci.value() or None, self.spin_sure.value() or None,
                    self.chk_basarili.isChecked() if self.cmb_durum.currentText() == "TAMAMLANDI" else None,
                    self.txt_eksik.toPlainText().strip() or None,
                    self.txt_onlem.toPlainText().strip() or None
                ))
                self.tatbikat_id = cursor.fetchone()[0]
                self.txt_no.setText(no)
            
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class ISGTatbikatlarPage(BasePage):
    """İSG Tatbikatlar Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("🔥 Acil Durum Tatbikatları")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Tatbikat")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar_layout.addWidget(btn_duzenle)
        
        toolbar_layout.addStretch()
        
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tümü", "PLANLI", "TAMAMLANDI", "IPTAL"])
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_durum)
        
        btn_yenile = QPushButton("🔄")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "No", "Tip", "Tarih", "Katılımcı", "Süre", "Durum"])
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
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        self.lbl_stat = QLabel()
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, tatbikat_no, tatbikat_tipi, FORMAT(tatbikat_tarihi, 'dd.MM.yyyy HH:mm'),
                       katilimci_sayisi, CAST(tahliye_suresi_dk AS VARCHAR) + ' dk', durum
                FROM isg.tatbikatlar
                ORDER BY tatbikat_tarihi DESC
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
                if j == 6:  # Durum
                    item = QTableWidgetItem(str(val) if val else "")
                    if val == "TAMAMLANDI":
                        item.setForeground(QColor(self.theme.get('success')))
                    elif val == "PLANLI":
                        item.setForeground(QColor(self.theme.get('warning')))
                    elif val == "IPTAL":
                        item.setForeground(QColor(self.theme.get('danger')))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)
        
        tamamlanan = len([r for r in rows if r[6] == "TAMAMLANDI"])
        self.lbl_stat.setText(f"Toplam: {len(rows)} tatbikat | Tamamlanan: {tamamlanan}")
    
    def _filter(self):
        durum = self.cmb_durum.currentText()
        if durum == "Tümü":
            self._display_data(self.all_rows)
        else:
            self._display_data([r for r in self.all_rows if r[6] == durum])
    
    def _yeni(self):
        dialog = TatbikatDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        tatbikat_id = int(self.table.item(row, 0).text())
        dialog = TatbikatDialog(self.theme, self, tatbikat_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
