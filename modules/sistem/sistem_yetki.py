# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Sistem İzin/Yetki Yönetimi
sistem.izinler tablosu
Kolonlar: id, uuid, kod, modul, aciklama, aktif_mi
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


# Modül listesi
MODULLER = [
    "is_emri",
    "uretim", 
    "kalite",
    "depo",
    "sevkiyat",
    "stok",
    "cari",
    "bakim",
    "laboratuvar",
    "satinalma",
    "ik",
    "isg",
    "cevre",
    "rapor",
    "sistem",
    "tanim"
]


class IzinDialog(QDialog):
    """İzin ekleme/düzenleme dialogu"""
    
    def __init__(self, parent=None, theme=None, izin_id=None):
        super().__init__(parent)
        self.theme = theme or {}
        self.izin_id = izin_id
        self.setWindowTitle("Yeni İzin" if not izin_id else "İzin Düzenle")
        self.setMinimumSize(450, 350)
        self.setModal(True)
        self.setup_ui()
        if izin_id:
            self.load_izin()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        form_layout = QFormLayout()
        
        # Modül
        self.cmb_modul = QComboBox()
        self.cmb_modul.addItems(MODULLER)
        form_layout.addRow("Modül:", self.cmb_modul)
        
        # İzin kodu
        self.txt_kod = QLineEdit()
        self.txt_kod.setPlaceholderText("ornek: is_emri.olustur, rapor.goruntule")
        self.txt_kod.setMaxLength(100)
        form_layout.addRow("İzin Kodu:", self.txt_kod)
        
        # Açıklama
        self.txt_aciklama = QLineEdit()
        self.txt_aciklama.setPlaceholderText("İzin açıklaması...")
        self.txt_aciklama.setMaxLength(400)
        form_layout.addRow("Açıklama:", self.txt_aciklama)
        
        # Aktif
        self.chk_aktif = QCheckBox("Aktif")
        self.chk_aktif.setChecked(True)
        form_layout.addRow("", self.chk_aktif)
        
        layout.addLayout(form_layout)
        
        # Ön tanımlı izinler hızlı seçim
        hizli_group = QGroupBox("Hızlı Ekle")
        hizli_layout = QHBoxLayout()
        
        btn_goruntule = QPushButton("+ Görüntüle")
        btn_goruntule.clicked.connect(lambda: self.hizli_ekle("goruntule", "Görüntüleme izni"))
        hizli_layout.addWidget(btn_goruntule)
        
        btn_olustur = QPushButton("+ Oluştur")
        btn_olustur.clicked.connect(lambda: self.hizli_ekle("olustur", "Oluşturma izni"))
        hizli_layout.addWidget(btn_olustur)
        
        btn_duzenle = QPushButton("+ Düzenle")
        btn_duzenle.clicked.connect(lambda: self.hizli_ekle("duzenle", "Düzenleme izni"))
        hizli_layout.addWidget(btn_duzenle)
        
        btn_sil = QPushButton("+ Sil")
        btn_sil.clicked.connect(lambda: self.hizli_ekle("sil", "Silme izni"))
        hizli_layout.addWidget(btn_sil)
        
        hizli_group.setLayout(hizli_layout)
        layout.addWidget(hizli_group)
        
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
    
    def hizli_ekle(self, islem, aciklama):
        """Hızlı izin kodu oluştur"""
        modul = self.cmb_modul.currentText()
        self.txt_kod.setText(f"{modul}.{islem}")
        self.txt_aciklama.setText(f"{modul.replace('_', ' ').title()} - {aciklama}")
    
    def load_izin(self):
        """Mevcut izin bilgilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM sistem.izinler WHERE id = ?", [self.izin_id])
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # Modül seçimi
                modul = row.modul or ''
                idx = self.cmb_modul.findText(modul)
                if idx >= 0:
                    self.cmb_modul.setCurrentIndex(idx)
                
                self.txt_kod.setText(row.kod or '')
                self.txt_aciklama.setText(row.aciklama or '')
                self.chk_aktif.setChecked(bool(row.aktif_mi) if row.aktif_mi is not None else True)
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"İzin yüklenirken hata: {str(e)}")
    
    def kaydet(self):
        """İzni kaydet"""
        modul = self.cmb_modul.currentText()
        kod = self.txt_kod.text().strip()
        aciklama = self.txt_aciklama.text().strip()
        aktif_mi = 1 if self.chk_aktif.isChecked() else 0
        
        if not kod:
            QMessageBox.warning(self, "Uyarı", "İzin kodu zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Kod unique kontrolü
            if self.izin_id:
                cursor.execute("SELECT id FROM sistem.izinler WHERE kod = ? AND id != ?", [kod, self.izin_id])
            else:
                cursor.execute("SELECT id FROM sistem.izinler WHERE kod = ?", [kod])
            
            if cursor.fetchone():
                QMessageBox.warning(self, "Uyarı", "Bu izin kodu zaten kullanılıyor!")
                conn.close()
                return
            
            if self.izin_id:
                # Güncelleme
                cursor.execute("""
                    UPDATE sistem.izinler SET
                        kod = ?, modul = ?, aciklama = ?, aktif_mi = ?
                    WHERE id = ?
                """, [kod, modul, aciklama, aktif_mi, self.izin_id])
            else:
                # Yeni kayıt
                import uuid
                new_uuid = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sistem.izinler (uuid, kod, modul, aciklama, aktif_mi)
                    VALUES (?, ?, ?, ?, ?)
                """, [new_uuid, kod, modul, aciklama, aktif_mi])
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Başarılı", "İzin kaydedildi!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {str(e)}")


class SistemYetkiPage(BasePage):
    """Sistem İzin/Yetki Yönetimi Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.izinler = []
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
        
        title = QLabel("🔐 İzin/Yetki Yönetimi")
        title.setStyleSheet(f"font-size:20px;font-weight:bold;color:{self.theme.get('text', '#ffffff')};")
        hl.addWidget(title)
        hl.addStretch()
        
        # Modül filtresi
        lbl_modul = QLabel("Modül:")
        lbl_modul.setStyleSheet(f"color:{self.theme.get('text', '#ffffff')};")
        hl.addWidget(lbl_modul)
        
        self.cmb_modul_filtre = QComboBox()
        self.cmb_modul_filtre.addItem("Tümü", "")
        for m in MODULLER:
            self.cmb_modul_filtre.addItem(m, m)
        self.cmb_modul_filtre.currentIndexChanged.connect(self.filter_data)
        self.cmb_modul_filtre.setMinimumWidth(150)
        hl.addWidget(self.cmb_modul_filtre)
        
        btn_yeni = QPushButton("➕ Yeni İzin")
        btn_yeni.setCursor(Qt.PointingHandCursor)
        btn_yeni.clicked.connect(self.yeni_izin)
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
        
        btn_toplu = QPushButton("📦 Toplu Ekle")
        btn_toplu.setCursor(Qt.PointingHandCursor)
        btn_toplu.clicked.connect(self.toplu_ekle)
        btn_toplu.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('warning', '#f59e0b')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #d97706; }}
        """)
        hl.addWidget(btn_toplu)
        
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
            "ID", "Modül", "İzin Kodu", "Açıklama", "Durum", "İşlemler"
        ])
        self.table.setColumnWidth(5, 170)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.duzenle_izin)
        
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
        """İzinleri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, kod, modul, aciklama, aktif_mi
                FROM sistem.izinler
                ORDER BY modul, kod
            """)
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            self.izinler = [dict(zip(columns, row)) for row in rows]
            print(f"DEBUG: {len(self.izinler)} izin bulundu")
            self.filter_data()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yüklenirken hata: {str(e)}")
    
    def filter_data(self):
        """Modül filtresine göre filtrele"""
        modul_filtre = self.cmb_modul_filtre.currentData()
        
        if modul_filtre:
            filtered = [i for i in self.izinler if i.get('modul') == modul_filtre]
        else:
            filtered = self.izinler
        
        self.display_data(filtered)
    
    def display_data(self, data):
        """Verileri tabloda göster"""
        self.table.setRowCount(len(data))
        
        for row_idx, i in enumerate(data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(i.get('id', ''))))
            
            modul_item = QTableWidgetItem(i.get('modul', ''))
            modul_item.setForeground(QColor(self.theme.get('primary', '#3b82f6')))
            self.table.setItem(row_idx, 1, modul_item)
            
            self.table.setItem(row_idx, 2, QTableWidgetItem(i.get('kod', '')))
            self.table.setItem(row_idx, 3, QTableWidgetItem(i.get('aciklama', '') or '-'))
            
            # Durum
            if i.get('aktif_mi'):
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
                ("✏️", "Duzenle", lambda checked, iid=i.get('id'): self.duzenle_by_id(iid), "edit"),
                ("🗑️", "Sil", lambda checked, iid=i.get('id'): self.sil_izin(iid), "delete"),
            ])
            self.table.setCellWidget(row_idx, 5, widget)
            self.table.setRowHeight(row_idx, 42)
    
    def yeni_izin(self):
        """Yeni izin ekle"""
        dialog = IzinDialog(self, self.theme)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
    
    def duzenle_izin(self):
        """Seçili izni düzenle"""
        row = self.table.currentRow()
        if row >= 0:
            izin_id = int(self.table.item(row, 0).text())
            self.duzenle_by_id(izin_id)
    
    def duzenle_by_id(self, izin_id):
        """ID ile izin düzenle"""
        dialog = IzinDialog(self, self.theme, izin_id)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
    
    def sil_izin(self, izin_id):
        """İzni sil"""
        reply = QMessageBox.question(
            self, "İzin Sil",
            "Bu izni silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # İzni sil
                cursor.execute("DELETE FROM sistem.izinler WHERE id = ?", [izin_id])
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Başarılı", "İzin silindi!")
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
    
    def toplu_ekle(self):
        """Bir modül için standart izinleri toplu ekle"""
        modul = self.cmb_modul_filtre.currentData()
        if not modul:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir modül seçin!")
            return
        
        standart_izinler = [
            ("goruntule", "Görüntüleme izni"),
            ("olustur", "Oluşturma izni"),
            ("duzenle", "Düzenleme izni"),
            ("sil", "Silme izni"),
            ("export", "Dışa aktarma izni")
        ]
        
        reply = QMessageBox.question(
            self, "Toplu Ekle",
            f"'{modul}' modülü için standart izinler eklensin mi?\n\n"
            "- görüntüle\n- oluştur\n- düzenle\n- sil\n- export",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import uuid
                conn = get_db_connection()
                cursor = conn.cursor()
                
                eklenen = 0
                for islem, aciklama in standart_izinler:
                    kod = f"{modul}.{islem}"
                    
                    # Zaten var mı kontrol et
                    cursor.execute("SELECT id FROM sistem.izinler WHERE kod = ?", [kod])
                    if cursor.fetchone():
                        continue
                    
                    new_uuid = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO sistem.izinler (uuid, kod, modul, aciklama, aktif_mi)
                        VALUES (?, ?, ?, ?, 1)
                    """, [new_uuid, kod, modul, f"{modul.replace('_', ' ').title()} - {aciklama}"])
                    eklenen += 1
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Başarılı", f"{eklenen} yeni izin eklendi!")
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Toplu ekleme hatası: {str(e)}")
