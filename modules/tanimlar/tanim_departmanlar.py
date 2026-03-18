# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Departman Tanımları
ik.departmanlar tablosu için CRUD işlemleri
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QGroupBox, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class DepartmanDialog(QDialog):
    """Departman ekleme/düzenleme dialogu"""
    
    def __init__(self, theme: dict, parent=None, departman_id=None):
        super().__init__(parent)
        self.theme = theme
        self.departman_id = departman_id
        self.setWindowTitle("Departman Ekle" if not departman_id else "Departman Düzenle")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        
        if departman_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
            QGroupBox {{
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Form
        form_group = QGroupBox("Departman Bilgileri")
        form_layout = QFormLayout()
        
        # Kod
        self.txt_kod = QLineEdit()
        self.txt_kod.setMaxLength(20)
        self.txt_kod.setPlaceholderText("Örn: URETIM, KALITE")
        form_layout.addRow("Departman Kodu*:", self.txt_kod)
        
        # Ad
        self.txt_ad = QLineEdit()
        self.txt_ad.setMaxLength(100)
        self.txt_ad.setPlaceholderText("Örn: Üretim Departmanı")
        form_layout.addRow("Departman Adı*:", self.txt_ad)
        
        # Üst Departman
        ust_layout = QHBoxLayout()
        self.cmb_ust = QComboBox()
        self.cmb_ust.addItem("-- Ana Departman --", None)
        ust_layout.addWidget(self.cmb_ust, 1)
        
        btn_ust_ekle = QPushButton("+")
        btn_ust_ekle.setFixedSize(32, 32)
        btn_ust_ekle.setToolTip("Yeni Üst Departman Ekle")
        btn_ust_ekle.setStyleSheet(f"background: {self.theme.get('success')}; color: white; font-weight: bold; border-radius: 4px;")
        btn_ust_ekle.clicked.connect(self._hizli_departman_ekle)
        ust_layout.addWidget(btn_ust_ekle)
        
        form_layout.addRow("Üst Departman:", ust_layout)
        
        # Yönetici
        self.cmb_yonetici = QComboBox()
        self.cmb_yonetici.addItem("-- Seçiniz --", None)
        form_layout.addRow("Departman Yöneticisi:", self.cmb_yonetici)
        
        # Aktif
        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        self.chk_aktif.setStyleSheet(f"color: {self.theme.get('text')};")
        form_layout.addRow("", self.chk_aktif)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
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
            
            # Üst departmanlar
            cursor.execute("SELECT id, kod, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                if row[0] != self.departman_id:  # Kendisini üst olarak seçemez
                    self.cmb_ust.addItem(f"{row[1]} - {row[2]}", row[0])
            
            # Yöneticiler (personeller)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_yonetici.addItem(f"{row[1]} - {row[2]}", row[0])
            
            conn.close()
        except Exception as e:
            print(f"Combo yükleme hatası: {e}")
    
    def _hizli_departman_ekle(self):
        """Hızlı üst departman ekleme"""
        from PySide6.QtWidgets import QInputDialog
        
        # Kod al
        kod, ok1 = QInputDialog.getText(self, "Yeni Üst Departman", "Departman Kodu (örn: YONETIM):")
        if not ok1 or not kod.strip():
            return
        kod = kod.strip().upper()
        
        # Ad al
        ad, ok2 = QInputDialog.getText(self, "Yeni Üst Departman", "Departman Adı:")
        if not ok2 or not ad.strip():
            return
        ad = ad.strip()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Kod kontrolü
            cursor.execute("SELECT COUNT(*) FROM ik.departmanlar WHERE kod = ?", (kod,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Uyarı", "Bu departman kodu zaten kullanılıyor!")
                conn.close()
                return
            
            # Ekle
            cursor.execute("""
                INSERT INTO ik.departmanlar (kod, ad, aktif_mi)
                VALUES (?, ?, 1)
            """, (kod, ad))
            
            # Yeni eklenen ID'yi al
            cursor.execute("SELECT @@IDENTITY")
            yeni_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            # Combo'ya ekle ve seç
            self.cmb_ust.addItem(f"{kod} - {ad}", int(yeni_id))
            self.cmb_ust.setCurrentIndex(self.cmb_ust.count() - 1)
            
            QMessageBox.information(self, "Başarılı", f"'{kod} - {ad}' üst departman olarak eklendi.")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ekleme hatası: {str(e)}")
    
    def _load_data(self):
        """Mevcut departman verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kod, ad, ust_departman_id, yonetici_id, aktif_mi
                FROM ik.departmanlar WHERE id = ?
            """, (self.departman_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_kod.setText(row[0] or "")
                self.txt_kod.setEnabled(False)
                self.txt_ad.setText(row[1] or "")
                
                # Üst departman
                if row[2]:
                    idx = self.cmb_ust.findData(row[2])
                    if idx >= 0:
                        self.cmb_ust.setCurrentIndex(idx)
                
                # Yönetici
                if row[3]:
                    idx = self.cmb_yonetici.findData(row[3])
                    if idx >= 0:
                        self.cmb_yonetici.setCurrentIndex(idx)
                
                self.chk_aktif.setChecked(row[4] if row[4] is not None else True)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _save(self):
        """Departmanı kaydet"""
        kod = self.txt_kod.text().strip().upper()
        ad = self.txt_ad.text().strip()
        
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad alanları zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            ust_id = self.cmb_ust.currentData()
            yonetici_id = self.cmb_yonetici.currentData()
            
            if self.departman_id:
                cursor.execute("""
                    UPDATE ik.departmanlar 
                    SET ad = ?, ust_departman_id = ?, yonetici_id = ?, aktif_mi = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (ad, ust_id, yonetici_id, self.chk_aktif.isChecked(), self.departman_id))
            else:
                # Kod kontrolü
                cursor.execute("SELECT COUNT(*) FROM ik.departmanlar WHERE kod = ?", (kod,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu departman kodu zaten kullanılıyor!")
                    conn.close()
                    return
                
                cursor.execute("""
                    INSERT INTO ik.departmanlar (kod, ad, ust_departman_id, yonetici_id, aktif_mi)
                    VALUES (?, ?, ?, ?, ?)
                """, (kod, ad, ust_id, yonetici_id, self.chk_aktif.isChecked()))
            
            conn.commit()
            conn.close()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")


class TanimDepartmanlarPage(BasePage):
    """Departman Tanımları Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("🏢 Departman Tanımları")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        layout.addWidget(header)
        
        # Toolbar
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(16, 12, 16, 12)
        
        btn_ekle = QPushButton("➕ Yeni Departman")
        btn_ekle.setStyleSheet(f"background: {self.theme.get('success')}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_ekle.clicked.connect(self._yeni_departman)
        toolbar.addWidget(btn_ekle)
        
        btn_duzenle = QPushButton("✏️ Düzenle")
        btn_duzenle.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_duzenle.clicked.connect(self._duzenle)
        toolbar.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("🗑️ Sil")
        btn_sil.setStyleSheet(f"background: {self.theme.get('danger')}; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_sil.clicked.connect(self._sil)
        toolbar.addWidget(btn_sil)
        
        btn_kalici_sil = QPushButton("❌ Kalıcı Sil")
        btn_kalici_sil.setStyleSheet(f"background: #7f1d1d; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_kalici_sil.clicked.connect(self._kalici_sil)
        toolbar.addWidget(btn_kalici_sil)
        
        toolbar.addStretch()
        
        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px 16px; border-radius: 6px;")
        btn_yenile.clicked.connect(self._load_data)
        toolbar.addWidget(btn_yenile)
        
        layout.addWidget(toolbar_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kod", "Departman Adı", "Üst Departman", "Yönetici", "Durum"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background: {self.theme.get('primary')};
            }}
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
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(5, 80)
        
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        # İstatistik
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(f"color: {self.theme.get('text_muted')};")
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        """Departman listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    d.id, d.kod, d.ad, 
                    ust.ad as ust_ad,
                    p.ad + ' ' + p.soyad as yonetici,
                    d.aktif_mi
                FROM ik.departmanlar d
                LEFT JOIN ik.departmanlar ust ON d.ust_departman_id = ust.id
                LEFT JOIN ik.personeller p ON d.yonetici_id = p.id
                ORDER BY d.kod
            """)
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            aktif_sayisi = 0
            
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or "-"))
                self.table.setItem(i, 4, QTableWidgetItem(row[4] or "-"))
                
                # Durum
                aktif = row[5]
                durum_item = QTableWidgetItem("✓ Aktif" if aktif else "✗ Pasif")
                durum_item.setForeground(QColor(self.theme.get('success') if aktif else self.theme.get('danger')))
                self.table.setItem(i, 5, durum_item)
                
                if aktif:
                    aktif_sayisi += 1
            
            self.lbl_stat.setText(f"Toplam: {len(rows)} departman | Aktif: {aktif_sayisi}")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def _yeni_departman(self):
        """Yeni departman ekle"""
        dialog = DepartmanDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        """Seçili departmanı düzenle"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir departman seçin!")
            return
        
        departman_id = int(self.table.item(row, 0).text())
        dialog = DepartmanDialog(self.theme, self, departman_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _sil(self):
        """Seçili departmanı sil (soft delete)"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir departman seçin!")
            return
        
        departman_id = int(self.table.item(row, 0).text())
        kod = self.table.item(row, 1).text()
        
        # Bağlı personel kontrolü
        personel_sayisi = 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ik.personeller WHERE departman_id = ? AND aktif_mi = 1", (departman_id,))
            personel_sayisi = cursor.fetchone()[0]
            conn.close()
        except Exception:
            pass
        
        if personel_sayisi > 0:
            # Zorla silme seçeneği sun
            reply = QMessageBox.question(
                self, "Uyarı",
                f"Bu departmanda {personel_sayisi} aktif personel bulunuyor.\n\n"
                f"Yine de '{kod}' departmanını pasif yapmak istiyor musunuz?\n"
                "(Personeller departmansız kalacak)",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        else:
            reply = QMessageBox.question(
                self, "Onay",
                f"'{kod}' departmanını silmek istediğinize emin misiniz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE ik.departmanlar SET aktif_mi = 0 WHERE id = ?", (departman_id,))
            conn.commit()
            conn.close()
            self._load_data()
            QMessageBox.information(self, "Başarılı", "Departman pasif yapıldı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
    
    def _kalici_sil(self):
        """Seçili departmanı kalıcı olarak sil (hard delete)"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir departman seçin!")
            return
        
        departman_id = int(self.table.item(row, 0).text())
        kod = self.table.item(row, 1).text()
        
        # Bağlı kayıt kontrolü
        personel_sayisi = 0
        pozisyon_sayisi = 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ik.personeller WHERE departman_id = ?", (departman_id,))
            personel_sayisi = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM ik.pozisyonlar WHERE departman_id = ?", (departman_id,))
            pozisyon_sayisi = cursor.fetchone()[0]
            conn.close()
        except Exception:
            pass
        
        bagli_kayit_msg = ""
        if personel_sayisi > 0 or pozisyon_sayisi > 0:
            bagli_kayit_msg = f"\n\nBağlı kayıtlar:\n"
            if personel_sayisi > 0:
                bagli_kayit_msg += f"• {personel_sayisi} personel\n"
            if pozisyon_sayisi > 0:
                bagli_kayit_msg += f"• {pozisyon_sayisi} pozisyon\n"
            bagli_kayit_msg += "\n(Bu kayıtların departman bilgisi boşaltılacak)"
        
        reply = QMessageBox.question(
            self, "⚠️ DİKKAT - KALICI SİLME",
            f"'{kod}' departmanını KALICI olarak silmek istiyor musunuz?\n\n"
            f"⚠️ Bu işlem GERİ ALINAMAZ!{bagli_kayit_msg}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Önce bağlı pozisyonların departman_id'sini NULL yap
            cursor.execute("UPDATE ik.pozisyonlar SET departman_id = NULL WHERE departman_id = ?", (departman_id,))
            
            # Bağlı personellerin departman_id'sini NULL yap
            cursor.execute("UPDATE ik.personeller SET departman_id = NULL WHERE departman_id = ?", (departman_id,))
            
            # Sonra departmanı sil
            cursor.execute("DELETE FROM ik.departmanlar WHERE id = ?", (departman_id,))
            
            conn.commit()
            conn.close()
            self._load_data()
            QMessageBox.information(self, "Başarılı", f"'{kod}' departmanı kalıcı olarak silindi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kalıcı silme hatası: {str(e)}")
