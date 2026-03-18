# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İSG Acil Durum Ekipleri
Yangın, Tahliye, İlk Yardım, Arama Kurtarma Ekipleri
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QTextEdit, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class EkipDialog(QDialog):
    """Acil durum ekibi yönetimi"""
    
    def __init__(self, theme: dict, parent=None, ekip_id=None):
        super().__init__(parent)
        self.theme = theme
        self.ekip_id = ekip_id
        self.setWindowTitle("Acil Durum Ekibi" if not ekip_id else "Ekip Düzenle")
        self.setMinimumSize(750, 500)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if ekip_id:
            self._load_data()
            self._load_uyeler()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QTextEdit {{
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
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["YANGIN", "TAHLIYE", "ILK_YARDIM", "ARAMA_KURTARMA"])
        genel_layout.addRow("Ekip Tipi*:", self.cmb_tip)
        
        self.txt_ad = QLineEdit()
        genel_layout.addRow("Ekip Adı*:", self.txt_ad)
        
        self.cmb_bolum = QComboBox()
        genel_layout.addRow("Bölüm:", self.cmb_bolum)
        
        self.cmb_lider = QComboBox()
        genel_layout.addRow("Ekip Lideri:", self.cmb_lider)
        
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(80)
        genel_layout.addRow("Açıklama:", self.txt_aciklama)
        
        tabs.addTab(tab_genel, "📋 Genel")
        
        # Tab 2: Üyeler
        tab_uye = QWidget()
        uye_layout = QVBoxLayout(tab_uye)
        
        toolbar = QHBoxLayout()
        btn_ekle = QPushButton("➕ Üye Ekle")
        btn_ekle.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_ekle.clicked.connect(self._add_uye)
        toolbar.addWidget(btn_ekle)
        
        btn_sil = QPushButton("🗑️ Kaldır")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._remove_uye)
        toolbar.addWidget(btn_sil)
        toolbar.addStretch()
        uye_layout.addLayout(toolbar)
        
        self.table_uye = QTableWidget()
        self.table_uye.setColumnCount(4)
        self.table_uye.setHorizontalHeaderLabels(["ID", "Sicil", "Ad Soyad", "Görev"])
        self.table_uye.setColumnHidden(0, True)
        self.table_uye.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_uye.setStyleSheet(f"QTableWidget {{ background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; }}")
        header = self.table_uye.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        uye_layout.addWidget(self.table_uye)
        
        self.lbl_uye = QLabel("0 üye")
        uye_layout.addWidget(self.lbl_uye)
        
        tabs.addTab(tab_uye, "👥 Üyeler")
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
            
            self.cmb_bolum.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_bolum.addItem(f"{row[1]} - {row[2]}", row[0])
            
            self.cmb_lider.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_lider.addItem(f"{row[1]} - {row[2]}", row[0])
            
            conn.close()
        except Exception:
            pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ekip_tipi, ekip_adi, bolum_id, ekip_lideri_id, aciklama
                FROM isg.acil_durum_ekipleri WHERE id = ?
            """, (self.ekip_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                if row[0]:
                    idx = self.cmb_tip.findText(row[0])
                    if idx >= 0: self.cmb_tip.setCurrentIndex(idx)
                self.txt_ad.setText(row[1] or "")
                if row[2]:
                    idx = self.cmb_bolum.findData(row[2])
                    if idx >= 0: self.cmb_bolum.setCurrentIndex(idx)
                if row[3]:
                    idx = self.cmb_lider.findData(row[3])
                    if idx >= 0: self.cmb_lider.setCurrentIndex(idx)
                self.txt_aciklama.setPlainText(row[4] or "")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _load_uyeler(self):
        if not self.ekip_id: return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, p.sicil_no, p.ad + ' ' + p.soyad, u.gorev
                FROM isg.acil_durum_uyeleri u
                JOIN ik.personeller p ON u.personel_id = p.id
                WHERE u.ekip_id = ? AND u.aktif_mi = 1 ORDER BY p.ad
            """, (self.ekip_id,))
            rows = cursor.fetchall()
            conn.close()
            
            self.table_uye.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    self.table_uye.setItem(i, j, QTableWidgetItem(str(val) if val else ""))
            self.lbl_uye.setText(f"{len(rows)} üye")
        except Exception: pass
    
    def _add_uye(self):
        if not self.ekip_id:
            QMessageBox.warning(self, "Uyarı", "Önce ekibi kaydedin!")
            return
        
        # Basit ekleme - tüm personelden seçim için ayrı dialog yapılabilir
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Eklenmemiş personelleri bul
            cursor.execute("""
                SELECT TOP 1 p.id FROM ik.personeller p
                WHERE p.aktif_mi = 1 AND p.id NOT IN 
                (SELECT personel_id FROM isg.acil_durum_uyeleri WHERE ekip_id = ? AND aktif_mi = 1)
            """, (self.ekip_id,))
            row = cursor.fetchone()
            
            if not row:
                QMessageBox.information(self, "Bilgi", "Tüm personel zaten eklenmiş!")
                conn.close()
                return
            
            # İlk uygun personeli ekle (gerçek uygulamada seçim dialog'u olmalı)
            cursor.execute("""
                INSERT INTO isg.acil_durum_uyeleri (ekip_id, personel_id, gorev)
                SELECT ?, p.id, 'Üye' FROM ik.personeller p
                WHERE p.aktif_mi = 1 AND p.id NOT IN 
                (SELECT personel_id FROM isg.acil_durum_uyeleri WHERE ekip_id = ? AND aktif_mi = 1)
            """, (self.ekip_id, self.ekip_id))
            conn.commit()
            conn.close()
            self._load_uyeler()
            QMessageBox.information(self, "Başarılı", "Tüm uygun personel eklendi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _remove_uye(self):
        row = self.table_uye.currentRow()
        if row < 0: return
        uye_id = int(self.table_uye.item(row, 0).text())
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE isg.acil_durum_uyeleri SET aktif_mi = 0 WHERE id = ?", (uye_id,))
            conn.commit()
            conn.close()
            self._load_uyeler()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        ad = self.txt_ad.text().strip()
        if not ad:
            QMessageBox.warning(self, "Uyarı", "Ekip adı zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.ekip_id:
                cursor.execute("""
                    UPDATE isg.acil_durum_ekipleri SET
                        ekip_tipi = ?, ekip_adi = ?, bolum_id = ?, ekip_lideri_id = ?, aciklama = ?
                    WHERE id = ?
                """, (self.cmb_tip.currentText(), ad, self.cmb_bolum.currentData(),
                      self.cmb_lider.currentData(), self.txt_aciklama.toPlainText().strip() or None,
                      self.ekip_id))
            else:
                cursor.execute("""
                    INSERT INTO isg.acil_durum_ekipleri (ekip_tipi, ekip_adi, bolum_id, ekip_lideri_id, aciklama)
                    OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?)
                """, (self.cmb_tip.currentText(), ad, self.cmb_bolum.currentData(),
                      self.cmb_lider.currentData(), self.txt_aciklama.toPlainText().strip() or None))
                self.ekip_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Ekip kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class ISGAcilDurumEkipleriPage(BasePage):
    """İSG Acil Durum Ekipleri Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("🚨 Acil Durum Ekipleri")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Ekip")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)
        
        toolbar_layout.addStretch()
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["Tümü", "YANGIN", "TAHLIYE", "ILK_YARDIM", "ARAMA_KURTARMA"])
        self.cmb_tip.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_tip)
        
        btn_yenile = QPushButton("🔄")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Tip", "Ekip Adı", "Lider", "Üye Sayısı", "Durum", "İşlem"])
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
        self.table.setColumnWidth(6, 120)
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        self.lbl_stat = QLabel()
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.id, e.ekip_tipi, e.ekip_adi, p.ad + ' ' + p.soyad,
                       (SELECT COUNT(*) FROM isg.acil_durum_uyeleri WHERE ekip_id = e.id AND aktif_mi = 1),
                       CASE WHEN e.aktif_mi = 1 THEN 'AKTİF' ELSE 'PASİF' END
                FROM isg.acil_durum_ekipleri e
                LEFT JOIN ik.personeller p ON e.ekip_lideri_id = p.id
                WHERE e.aktif_mi = 1
                ORDER BY e.ekip_tipi
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")
    
    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        tip_colors = {"YANGIN": "#e74c3c", "TAHLIYE": "#f39c12", "ILK_YARDIM": "#27ae60", "ARAMA_KURTARMA": "#3498db"}
        
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 1:  # Tip
                    item = QTableWidgetItem(str(val) if val else "")
                    item.setForeground(QColor(tip_colors.get(val, self.theme.get('text'))))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)

            rid = row[0]
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=rid: self._duzenle_by_id(rid), "edit"),
            ])
            self.table.setCellWidget(i, 6, widget)
            self.table.setRowHeight(i, 42)

        self.lbl_stat.setText(f"Toplam: {len(rows)} ekip")
    
    def _duzenle_by_id(self, ekip_id):
        """ID ile ekip düzenleme (satır butonundan)"""
        dialog = EkipDialog(self.theme, self, ekip_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _filter(self):
        tip = self.cmb_tip.currentText()
        if tip == "Tümü":
            self._display_data(self.all_rows)
        else:
            self._display_data([r for r in self.all_rows if r[1] == tip])
    
    def _yeni(self):
        dialog = EkipDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        ekip_id = int(self.table.item(row, 0).text())
        dialog = EkipDialog(self.theme, self, ekip_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
