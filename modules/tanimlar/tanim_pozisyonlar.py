# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Pozisyon Tanımları
ik.pozisyonlar tablosu için CRUD işlemleri
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class PozisyonDialog(QDialog):
    """Pozisyon ekleme/düzenleme dialogu"""
    
    def __init__(self, theme: dict, parent=None, pozisyon_id=None):
        super().__init__(parent)
        self.theme = theme
        self.pozisyon_id = pozisyon_id
        self.setWindowTitle("Pozisyon Ekle" if not pozisyon_id else "Pozisyon Düzenle")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        
        if pozisyon_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QTextEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Kod
        self.txt_kod = QLineEdit()
        self.txt_kod.setMaxLength(20)
        self.txt_kod.setPlaceholderText("Örn: OPERTOR, KALITE_UZM")
        form.addRow("Pozisyon Kodu*:", self.txt_kod)
        
        # Ad
        self.txt_ad = QLineEdit()
        self.txt_ad.setMaxLength(100)
        self.txt_ad.setPlaceholderText("Örn: Üretim Operatörü")
        form.addRow("Pozisyon Adı*:", self.txt_ad)
        
        # Departman
        self.cmb_departman = QComboBox()
        form.addRow("Departman*:", self.cmb_departman)
        
        # Açıklama
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(80)
        self.txt_aciklama.setPlaceholderText("Görev tanımı, sorumluluklar...")
        form.addRow("Açıklama:", self.txt_aciklama)
        
        # Aktif
        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        self.chk_aktif.setStyleSheet(f"color: {self.theme.get('text')};")
        form.addRow("", self.chk_aktif)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 10px 24px; border-radius: 6px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        """Combo listelerini doldur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Departmanlar
            self.cmb_departman.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_departman.addItem(f"{row[1]} - {row[2]}", row[0])
            
            conn.close()
        except Exception as e:
            print(f"Combo yükleme hatası: {e}")
    
    def _load_data(self):
        """Mevcut pozisyon verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kod, ad, departman_id, aktif_mi
                FROM ik.pozisyonlar WHERE id = ?
            """, (self.pozisyon_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_kod.setText(row[0] or "")
                self.txt_kod.setEnabled(False)
                self.txt_ad.setText(row[1] or "")
                
                if row[2]:
                    idx = self.cmb_departman.findData(row[2])
                    if idx >= 0:
                        self.cmb_departman.setCurrentIndex(idx)
                
                self.chk_aktif.setChecked(row[3] if row[3] is not None else True)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _save(self):
        """Pozisyonu kaydet"""
        kod = self.txt_kod.text().strip().upper()
        ad = self.txt_ad.text().strip()
        departman_id = self.cmb_departman.currentData()
        
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad alanları zorunludur!")
            return
        
        if not departman_id:
            QMessageBox.warning(self, "Uyarı", "Departman seçimi zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.pozisyon_id:
                cursor.execute("""
                    UPDATE ik.pozisyonlar SET
                        ad = ?, departman_id = ?, aktif_mi = ?
                    WHERE id = ?
                """, (ad, departman_id, self.chk_aktif.isChecked(), self.pozisyon_id))
            else:
                # Kod kontrolü
                cursor.execute("SELECT COUNT(*) FROM ik.pozisyonlar WHERE kod = ?", (kod,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu pozisyon kodu zaten kullanılıyor!")
                    conn.close()
                    return
                
                cursor.execute("""
                    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi)
                    VALUES (?, ?, ?, ?)
                """, (kod, ad, departman_id, self.chk_aktif.isChecked()))
            
            conn.commit()
            conn.close()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class TanimPozisyonlarPage(BasePage):
    """Pozisyon Tanımları Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("🎯 Pozisyon Tanımları")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Pozisyon")
        btn_yeni.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar_layout.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._sil)
        toolbar_layout.addWidget(btn_sil)
        
        btn_kalici_sil = QPushButton("❌ Kalıcı Sil")
        btn_kalici_sil.setStyleSheet(f"background: #7f1d1d; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_kalici_sil.clicked.connect(self._kalici_sil)
        toolbar_layout.addWidget(btn_kalici_sil)
        
        toolbar_layout.addStretch()
        
        # Departman filtresi
        self.cmb_departman = QComboBox()
        self.cmb_departman.addItem("Tüm Departmanlar", None)
        self.cmb_departman.setStyleSheet(f"""
            QComboBox {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
                min-width: 150px;
            }}
        """)
        self.cmb_departman.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_departman)
        
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kod", "Pozisyon Adı", "Departman", "Durum"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                color: {self.theme.get('text')};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QTableWidget::item:selected {{ background: {self.theme.get('primary')}; }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary')};
                font-weight: bold;
            }}
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(4, 80)
        
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        # İstatistik
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        layout.addWidget(self.lbl_stat)
        
        # Departman combosunu doldur
        self._load_departmanlar()
    
    def _load_departmanlar(self):
        """Departman filtresini doldur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_departman.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except:
            pass
    
    def _load_data(self):
        """Pozisyonları yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.id, p.kod, p.ad,
                    d.ad as departman,
                    p.aktif_mi,
                    p.departman_id
                FROM ik.pozisyonlar p
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                ORDER BY d.kod, p.kod
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            
            self._display_data(self.all_rows)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _display_data(self, rows):
        """Verileri tabloda göster"""
        self.table.setRowCount(len(rows))
        aktif_sayisi = 0
        
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(i, 1, QTableWidgetItem(row[1] or ""))
            self.table.setItem(i, 2, QTableWidgetItem(row[2] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(row[3] or "-"))
            
            aktif = row[4]
            durum_item = QTableWidgetItem("✓ Aktif" if aktif else "✗ Pasif")
            durum_item.setForeground(QColor(self.theme.get('success') if aktif else self.theme.get('danger')))
            self.table.setItem(i, 4, durum_item)
            
            if aktif:
                aktif_sayisi += 1
        
        self.lbl_stat.setText(f"Toplam: {len(rows)} pozisyon | Aktif: {aktif_sayisi}")
    
    def _filter(self):
        """Departmana göre filtrele"""
        dept_id = self.cmb_departman.currentData()
        
        if dept_id is None:
            self._display_data(self.all_rows)
        else:
            filtered = [r for r in self.all_rows if r[5] == dept_id]
            self._display_data(filtered)
    
    def _yeni(self):
        """Yeni pozisyon ekle"""
        dialog = PozisyonDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        """Pozisyon düzenle"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir pozisyon seçin!")
            return
        
        pozisyon_id = int(self.table.item(row, 0).text())
        dialog = PozisyonDialog(self.theme, self, pozisyon_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _sil(self):
        """Pozisyon sil"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir pozisyon seçin!")
            return
        
        pozisyon_id = int(self.table.item(row, 0).text())
        kod = self.table.item(row, 1).text()
        
        # Bağlı personel kontrolü
        personel_sayisi = 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ik.personeller WHERE pozisyon_id = ? AND aktif_mi = 1", (pozisyon_id,))
            personel_sayisi = cursor.fetchone()[0]
            conn.close()
        except:
            pass
        
        if personel_sayisi > 0:
            # Zorla silme seçeneği sun
            reply = QMessageBox.question(
                self, "Uyarı",
                f"Bu pozisyonda {personel_sayisi} aktif personel bulunuyor.\n\n"
                f"Yine de '{kod}' pozisyonunu pasif yapmak istiyor musunuz?\n"
                "(Personeller pozisyonsuz kalacak)",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        else:
            reply = QMessageBox.question(
                self, "Onay", f"'{kod}' pozisyonunu silmek istediğinize emin misiniz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE ik.pozisyonlar SET aktif_mi = 0 WHERE id = ?", (pozisyon_id,))
            conn.commit()
            conn.close()
            self._load_data()
            QMessageBox.information(self, "Başarılı", "Pozisyon pasif yapıldı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
    
    def _kalici_sil(self):
        """Pozisyonu kalıcı olarak sil (hard delete)"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir pozisyon seçin!")
            return
        
        pozisyon_id = int(self.table.item(row, 0).text())
        kod = self.table.item(row, 1).text()
        
        # Bağlı personel kontrolü
        personel_sayisi = 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ik.personeller WHERE pozisyon_id = ?", (pozisyon_id,))
            personel_sayisi = cursor.fetchone()[0]
            conn.close()
        except:
            pass
        
        if personel_sayisi > 0:
            reply = QMessageBox.question(
                self, "⚠️ DİKKAT - KALICI SİLME",
                f"Bu pozisyonda {personel_sayisi} personel kaydı bulunuyor.\n\n"
                f"'{kod}' pozisyonunu KALICI olarak silmek istiyor musunuz?\n\n"
                "⚠️ Bu işlem GERİ ALINAMAZ!\n"
                "(Personellerin pozisyon bilgisi boşaltılacak)",
                QMessageBox.Yes | QMessageBox.No
            )
        else:
            reply = QMessageBox.question(
                self, "⚠️ DİKKAT - KALICI SİLME",
                f"'{kod}' pozisyonunu KALICI olarak silmek istiyor musunuz?\n\n"
                "⚠️ Bu işlem GERİ ALINAMAZ!",
                QMessageBox.Yes | QMessageBox.No
            )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Önce bağlı personellerin pozisyon_id'sini NULL yap
            cursor.execute("UPDATE ik.personeller SET pozisyon_id = NULL WHERE pozisyon_id = ?", (pozisyon_id,))
            
            # Sonra pozisyonu sil
            cursor.execute("DELETE FROM ik.pozisyonlar WHERE id = ?", (pozisyon_id,))
            
            conn.commit()
            conn.close()
            self._load_data()
            QMessageBox.information(self, "Başarılı", f"'{kod}' pozisyonu kalıcı olarak silindi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kalıcı silme hatası: {str(e)}")
