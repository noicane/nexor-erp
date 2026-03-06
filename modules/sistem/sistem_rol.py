# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Sistem Rol Yönetimi
sistem.roller tablosu
Kolonlar: id, rol_kodu, rol_adi, aciklama, seviye, aktif_mi, olusturma_tarihi, guncelleme_tarihi, uuid
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView,
    QDialog, QFormLayout, QCheckBox, QFrame, QGroupBox, QTextEdit, QSpinBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager


class RolDialog(QDialog):
    """Rol ekleme/düzenleme dialogu"""
    
    def __init__(self, parent=None, theme=None, rol_id=None):
        super().__init__(parent)
        self.theme = theme or {}
        self.rol_id = rol_id
        self.setWindowTitle("Yeni Rol" if not rol_id else "Rol Düzenle")
        self.setMinimumSize(450, 400)
        self.setModal(True)
        self.setup_ui()
        if rol_id:
            self.load_rol()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Temel Bilgiler
        temel_group = QGroupBox("Rol Bilgileri")
        temel_layout = QFormLayout()
        
        self.txt_kod = QLineEdit()
        self.txt_kod.setPlaceholderText("ADMIN, OPERATOR, URETIM_MD...")
        self.txt_kod.setMaxLength(50)
        temel_layout.addRow("Rol Kodu:", self.txt_kod)
        
        self.txt_ad = QLineEdit()
        self.txt_ad.setPlaceholderText("Rol adı...")
        self.txt_ad.setMaxLength(200)
        temel_layout.addRow("Rol Adı:", self.txt_ad)
        
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setPlaceholderText("Rol açıklaması...")
        self.txt_aciklama.setMaximumHeight(80)
        temel_layout.addRow("Açıklama:", self.txt_aciklama)
        
        self.spn_seviye = QSpinBox()
        self.spn_seviye.setRange(0, 100)
        self.spn_seviye.setValue(10)
        temel_layout.addRow("Seviye:", self.spn_seviye)
        
        self.chk_aktif = QCheckBox("Rol aktif")
        self.chk_aktif.setChecked(True)
        temel_layout.addRow("", self.chk_aktif)
        
        temel_group.setLayout(temel_layout)
        layout.addWidget(temel_group)
        
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#3b82f6')};
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
        """)
        btn_kaydet.clicked.connect(self.kaydet)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def load_rol(self):
        """Mevcut rol bilgilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM sistem.roller WHERE id = ?", [self.rol_id])
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_kod.setText(row.rol_kodu or '')
                self.txt_ad.setText(row.rol_adi or '')
                self.txt_aciklama.setPlainText(row.aciklama or '')
                if row.seviye:
                    self.spn_seviye.setValue(row.seviye)
                self.chk_aktif.setChecked(bool(row.aktif_mi) if row.aktif_mi is not None else True)
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Rol yüklenirken hata: {str(e)}")
    
    def kaydet(self):
        """Rolü kaydet"""
        kod = self.txt_kod.text().strip().upper()
        ad = self.txt_ad.text().strip()
        aciklama = self.txt_aciklama.toPlainText().strip()
        seviye = self.spn_seviye.value()
        
        if not kod:
            QMessageBox.warning(self, "Uyarı", "Rol kodu zorunludur!")
            return
        
        if not ad:
            QMessageBox.warning(self, "Uyarı", "Rol adı zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Kod unique kontrolü
            if self.rol_id:
                cursor.execute("""
                    SELECT id FROM sistem.roller WHERE rol_kodu = ? AND id != ?
                """, [kod, self.rol_id])
            else:
                cursor.execute("SELECT id FROM sistem.roller WHERE rol_kodu = ?", [kod])
            
            if cursor.fetchone():
                QMessageBox.warning(self, "Uyarı", "Bu rol kodu zaten kullanılıyor!")
                conn.close()
                return
            
            aktif_mi = 1 if self.chk_aktif.isChecked() else 0
            
            if self.rol_id:
                # Güncelleme
                cursor.execute("""
                    UPDATE sistem.roller SET
                        rol_kodu = ?, rol_adi = ?, aciklama = ?, seviye = ?,
                        aktif_mi = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, [kod, ad, aciklama, seviye, aktif_mi, self.rol_id])
            else:
                # Yeni kayıt
                import uuid
                new_uuid = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sistem.roller 
                    (uuid, rol_kodu, rol_adi, aciklama, seviye, aktif_mi, olusturma_tarihi)
                    VALUES (?, ?, ?, ?, ?, ?, GETDATE())
                """, [new_uuid, kod, ad, aciklama, seviye, aktif_mi])
            
            conn.commit()
            
            # Log kaydet
            if self.rol_id:
                LogManager.log_update('sistem', 'roller', self.rol_id,
                                     aciklama=f'Rol güncellendi: {ad} ({kod})')
            else:
                cursor.execute("SELECT MAX(id) FROM sistem.roller WHERE rol_kodu = ?", [kod])
                yeni_id = cursor.fetchone()[0]
                LogManager.log_insert('sistem', 'roller', yeni_id,
                                     aciklama=f'Yeni rol eklendi: {ad} ({kod})')
            
            conn.close()
            
            QMessageBox.information(self, "Başarılı", "Rol kaydedildi!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {str(e)}")


class SistemRolPage(BasePage):
    """Sistem Rol Yönetimi Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.roller = []
        self._setup_ui()
        QTimer.singleShot(100, self.load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        header = QFrame()
        header.setStyleSheet(f"QFrame{{background:{self.theme.get('bg_card', '#1e293b')};border-radius:8px;padding:16px;}}")
        hl = QHBoxLayout(header)
        
        title = QLabel("🎭 Rol Yönetimi")
        title.setStyleSheet(f"font-size:20px;font-weight:bold;color:{self.theme.get('text', '#ffffff')};")
        hl.addWidget(title)
        hl.addStretch()
        
        btn_yeni = QPushButton("➕ Yeni Rol")
        btn_yeni.setCursor(Qt.PointingHandCursor)
        btn_yeni.clicked.connect(self.yeni_rol)
        btn_yeni.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #16a34a; }}
        """)
        hl.addWidget(btn_yeni)
        
        btn_refresh = QPushButton("🔄")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.load_data)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#3b82f6')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        hl.addWidget(btn_refresh)
        
        layout.addWidget(header)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kod", "Rol Adı", "Seviye", "Durum", "İşlemler"
        ])
        self.table.setColumnWidth(5, 170)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.duzenle_rol)
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.theme.get('bg_card', '#1e293b')};
                color: {self.theme.get('text', '#ffffff')};
                border: 1px solid {self.theme.get('border', 'rgba(51, 65, 85, 0.5)')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border', 'rgba(51, 65, 85, 0.5)')};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {self.theme.get('primary', '#3b82f6')};
            }}
            QHeaderView::section {{
                background-color: {self.theme.get('bg_main', '#0f172a')};
                color: {self.theme.get('text', '#ffffff')};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)
        
        layout.addWidget(self.table)
    
    def load_data(self):
        """Rolleri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, rol_kodu, rol_adi, aciklama, seviye, aktif_mi
                FROM sistem.roller
                ORDER BY seviye DESC, rol_adi
            """)
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            self.roller = [dict(zip(columns, row)) for row in rows]
            print(f"DEBUG: {len(self.roller)} rol bulundu")
            self.display_data()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def display_data(self):
        """Verileri tabloda göster"""
        self.table.setRowCount(len(self.roller))
        
        for row_idx, r in enumerate(self.roller):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(r.get('id', ''))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(r.get('rol_kodu', '')))
            self.table.setItem(row_idx, 2, QTableWidgetItem(r.get('rol_adi', '')))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(r.get('seviye', 0) or 0)))
            
            # Durum
            if r.get('aktif_mi'):
                durum = "✅ Aktif"
                durum_renk = self.theme.get('success', '#22c55e')
            else:
                durum = "⏸️ Pasif"
                durum_renk = self.theme.get('warning', '#f59e0b')
            
            durum_item = QTableWidgetItem(durum)
            durum_item.setForeground(QColor(durum_renk))
            self.table.setItem(row_idx, 4, durum_item)
            
            # İşlem butonları
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=r.get('id'): self.duzenle_by_id(rid), "edit"),
                ("🗑️", "Sil", lambda checked, rid=r.get('id'): self.sil_rol(rid), "delete"),
            ])
            self.table.setCellWidget(row_idx, 5, widget)
            self.table.setRowHeight(row_idx, 42)
    
    def yeni_rol(self):
        """Yeni rol ekle"""
        dialog = RolDialog(self, self.theme)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
    
    def duzenle_rol(self):
        """Seçili rolü düzenle"""
        row = self.table.currentRow()
        if row >= 0:
            rol_id = int(self.table.item(row, 0).text())
            self.duzenle_by_id(rol_id)
    
    def duzenle_by_id(self, rol_id):
        """ID ile rol düzenle"""
        dialog = RolDialog(self, self.theme, rol_id)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
    
    def sil_rol(self, rol_id):
        """Rolü sil"""
        reply = QMessageBox.question(
            self, "Rol Sil",
            "Bu rolü silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Kullanıcıda kullanılıyor mu kontrol et
                cursor.execute("SELECT COUNT(*) FROM sistem.kullanicilar WHERE rol_id = ?", [rol_id])
                count = cursor.fetchone()[0]
                
                if count > 0:
                    QMessageBox.warning(self, "Uyarı", f"Bu rol {count} kullanıcıya atanmış. Önce kullanıcılardan kaldırın.")
                    conn.close()
                    return
                
                # Rol adını al
                cursor.execute("SELECT rol_adi, rol_kodu FROM sistem.roller WHERE id = ?", [rol_id])
                row = cursor.fetchone()
                rol_adi = f"{row.rol_adi} ({row.rol_kodu})" if row else str(rol_id)
                
                # Rolü sil
                cursor.execute("DELETE FROM sistem.roller WHERE id = ?", [rol_id])
                
                conn.commit()
                conn.close()
                
                # Log kaydet
                LogManager.log_delete('sistem', 'roller', rol_id,
                                     aciklama=f'Rol silindi: {rol_adi}')
                
                QMessageBox.information(self, "Başarılı", "Rol silindi!")
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
