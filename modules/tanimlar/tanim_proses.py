# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Proses Tanım Ekranı
Üretim proseslerinin (KTL, ZN, TOZ vs.) tanımlanması
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QSpinBox, QFormLayout, QColorDialog, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class ProsesDialog(QDialog):
    """Proses ekleme/düzenleme dialog'u"""
    
    def __init__(self, theme: dict, proses_data: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.proses_data = proses_data or {}
        self.is_edit = bool(proses_data)
        
        self.setWindowTitle("Proses Düzenle" if self.is_edit else "Yeni Proses")
        self.setMinimumSize(500, 450)
        self._setup_ui()
        
        if self.is_edit:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QComboBox, QSpinBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px;
                color: {brand.TEXT};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Form
        form = QFormLayout()
        form.setSpacing(12)
        
        # Kod
        self.kod_input = QLineEdit()
        self.kod_input.setPlaceholderText("Örn: KTL, ZN, TOZ")
        self.kod_input.setMaxLength(40)
        form.addRow("Kod *:", self.kod_input)
        
        # Ad
        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderText("Örn: Kataforez Kaplama")
        self.ad_input.setMaxLength(200)
        form.addRow("Ad *:", self.ad_input)
        
        # Kısa Ad
        self.kisa_ad_input = QLineEdit()
        self.kisa_ad_input.setPlaceholderText("Örn: Kataforez")
        self.kisa_ad_input.setMaxLength(60)
        form.addRow("Kısa Ad:", self.kisa_ad_input)
        
        # Hat
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("-- Hat Seçin --", None)
        self._load_hatlar()
        form.addRow("Üretim Hattı:", self.hat_combo)
        
        # Giriş Depo
        self.giris_depo_combo = QComboBox()
        self.giris_depo_combo.addItem("-- Giriş Deposu --", None)
        self._load_depolar(self.giris_depo_combo)
        form.addRow("Giriş Deposu:", self.giris_depo_combo)
        
        # Çıkış Depo
        self.cikis_depo_combo = QComboBox()
        self.cikis_depo_combo.addItem("-- Çıkış Deposu --", None)
        self._load_depolar(self.cikis_depo_combo)
        form.addRow("Çıkış Deposu:", self.cikis_depo_combo)
        
        # Standart Süre
        self.sure_input = QSpinBox()
        self.sure_input.setRange(1, 9999)
        self.sure_input.setValue(60)
        self.sure_input.setSuffix(" dk")
        form.addRow("Standart Süre:", self.sure_input)
        
        # Kapasite
        self.kapasite_input = QSpinBox()
        self.kapasite_input.setRange(1, 9999)
        self.kapasite_input.setValue(300)
        self.kapasite_input.setSuffix(" bara/vardiya")
        form.addRow("Vardiya Kapasite:", self.kapasite_input)
        
        # Renk
        renk_layout = QHBoxLayout()
        self.renk_btn = QPushButton()
        self.renk_btn.setFixedSize(40, 30)
        self.renk_kodu = "#6366f1"
        self._update_renk_btn()
        self.renk_btn.clicked.connect(self._pick_color)
        renk_layout.addWidget(self.renk_btn)
        renk_layout.addStretch()
        form.addRow("Renk:", renk_layout)
        
        # Sıra No
        self.sira_input = QSpinBox()
        self.sira_input.setRange(0, 999)
        self.sira_input.setValue(0)
        form.addRow("Sıra No:", self.sira_input)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                padding: 10px 24px;
            }}
        """)
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)
        
        kaydet_btn = QPushButton("💾 Kaydet")
        kaydet_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: {brand.SUCCESS}; color: white;
                border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold;
            }}
        """)
        kaydet_btn.clicked.connect(self._save)
        btn_layout.addWidget(kaydet_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_hatlar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.uretim_hatlari WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.hat_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception as e:
            print(f"Hat yükleme hatası: {e}")
    
    def _load_depolar(self, combo: QComboBox):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.depolar WHERE aktif_mi = 1 AND silindi_mi = 0 ORDER BY kod")
            for row in cursor.fetchall():
                combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception as e:
            print(f"Depo yükleme hatası: {e}")
    
    def _update_renk_btn(self):
        self.renk_btn.setStyleSheet(f"background: {self.renk_kodu}; border: 1px solid #fff; border-radius: 4px;")
    
    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.renk_kodu), self, "Renk Seçin")
        if color.isValid():
            self.renk_kodu = color.name()
            self._update_renk_btn()
    
    def _load_data(self):
        self.kod_input.setText(self.proses_data.get('kod', ''))
        self.ad_input.setText(self.proses_data.get('ad', ''))
        self.kisa_ad_input.setText(self.proses_data.get('kisa_ad', '') or '')
        
        hat_id = self.proses_data.get('hat_id')
        if hat_id:
            for i in range(self.hat_combo.count()):
                if self.hat_combo.itemData(i) == hat_id:
                    self.hat_combo.setCurrentIndex(i)
                    break
        
        giris_depo_id = self.proses_data.get('giris_depo_id')
        if giris_depo_id:
            for i in range(self.giris_depo_combo.count()):
                if self.giris_depo_combo.itemData(i) == giris_depo_id:
                    self.giris_depo_combo.setCurrentIndex(i)
                    break
        
        cikis_depo_id = self.proses_data.get('cikis_depo_id')
        if cikis_depo_id:
            for i in range(self.cikis_depo_combo.count()):
                if self.cikis_depo_combo.itemData(i) == cikis_depo_id:
                    self.cikis_depo_combo.setCurrentIndex(i)
                    break
        
        self.sure_input.setValue(self.proses_data.get('standart_sure_dk', 60) or 60)
        self.kapasite_input.setValue(self.proses_data.get('vardiya_kapasite_bara', 300) or 300)
        self.renk_kodu = self.proses_data.get('renk_kodu', '#6366f1') or '#6366f1'
        self._update_renk_btn()
        self.sira_input.setValue(self.proses_data.get('sira_no', 0) or 0)
    
    def _save(self):
        kod = self.kod_input.text().strip().upper()
        ad = self.ad_input.text().strip()
        
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad alanları zorunludur!")
            return
        
        self.result_data = {
            'kod': kod,
            'ad': ad,
            'kisa_ad': self.kisa_ad_input.text().strip() or None,
            'hat_id': self.hat_combo.currentData(),
            'giris_depo_id': self.giris_depo_combo.currentData(),
            'cikis_depo_id': self.cikis_depo_combo.currentData(),
            'standart_sure_dk': self.sure_input.value(),
            'vardiya_kapasite_bara': self.kapasite_input.value(),
            'renk_kodu': self.renk_kodu,
            'sira_no': self.sira_input.value()
        }
        self.accept()


class TanimProsesPage(BasePage):
    """Proses Tanım Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("⚙️ Proses Tanımları")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {brand.TEXT};")
        header.addWidget(title)
        
        header.addStretch()
        
        # Yeni Proses butonu
        yeni_btn = QPushButton("➕ Yeni Proses")
        yeni_btn.setCursor(Qt.PointingHandCursor)
        yeni_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS}; color: white;
                border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #1da34d; }}
        """)
        yeni_btn.clicked.connect(self._yeni_proses)
        header.addWidget(yeni_btn)
        
        # Yenile butonu
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 10px 16px;
            }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kod", "Ad", "Hat", "Giriş Depo", "Çıkış Depo", 
            "Süre (dk)", "Kapasite", "Sıra", "İşlem"
        ])
        self.table.setColumnHidden(0, True)
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 8px;
                gridline-color: {brand.BORDER};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QHeaderView::section {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                padding: 10px; border: none; font-weight: bold;
            }}
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(9, QHeaderView.Fixed)
        self.table.setColumnWidth(9, 170)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table, 1)
        
        # Alt bilgi
        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px;")
        layout.addWidget(self.info_label)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.id, p.kod, p.ad, p.kisa_ad,
                    h.kod as hat_kodu, h.ad as hat_adi,
                    gd.kod as giris_depo, cd.kod as cikis_depo,
                    p.standart_sure_dk, p.vardiya_kapasite_bara,
                    p.renk_kodu, p.sira_no,
                    p.hat_id, p.giris_depo_id, p.cikis_depo_id
                FROM tanim.prosesler p
                LEFT JOIN tanim.uretim_hatlari h ON p.hat_id = h.id
                LEFT JOIN tanim.depolar gd ON p.giris_depo_id = gd.id
                LEFT JOIN tanim.depolar cd ON p.cikis_depo_id = cd.id
                WHERE p.aktif_mi = 1 AND p.silindi_mi = 0
                ORDER BY p.sira_no, p.kod
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                # ID
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                
                # Kod (renkli)
                kod_item = QTableWidgetItem(row[1])
                renk = row[10] or '#6366f1'
                kod_item.setForeground(QColor(renk))
                kod_item.setFont(kod_item.font())
                self.table.setItem(i, 1, kod_item)
                
                # Ad
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                
                # Hat
                hat_text = row[4] if row[4] else '-'
                self.table.setItem(i, 3, QTableWidgetItem(hat_text))
                
                # Giriş Depo
                self.table.setItem(i, 4, QTableWidgetItem(row[6] or '-'))
                
                # Çıkış Depo
                self.table.setItem(i, 5, QTableWidgetItem(row[7] or '-'))
                
                # Süre
                sure_item = QTableWidgetItem(str(row[8] or 0))
                sure_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 6, sure_item)
                
                # Kapasite
                kap_item = QTableWidgetItem(str(row[9] or 0))
                kap_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 7, kap_item)
                
                # Sıra
                sira_item = QTableWidgetItem(str(row[11] or 0))
                sira_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 8, sira_item)
                
                # İşlem butonları
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, r=row: self._edit_proses(r), "edit"),
                    ("🗑️", "Sil", lambda checked, pid=row[0], pkod=row[1]: self._delete_proses(pid, pkod), "delete"),
                ])
                self.table.setCellWidget(i, 9, widget)
                self.table.setRowHeight(i, 45)
            
            self.info_label.setText(f"Toplam {len(rows)} proses tanımı")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yükleme hatası: {e}")
    
    def _yeni_proses(self):
        dialog = ProsesDialog(self.theme, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._save_proses(dialog.result_data)
    
    def _edit_proses(self, row_data):
        proses_data = {
            'id': row_data[0],
            'kod': row_data[1],
            'ad': row_data[2],
            'kisa_ad': row_data[3],
            'hat_id': row_data[12],
            'giris_depo_id': row_data[13],
            'cikis_depo_id': row_data[14],
            'standart_sure_dk': row_data[8],
            'vardiya_kapasite_bara': row_data[9],
            'renk_kodu': row_data[10],
            'sira_no': row_data[11]
        }
        
        dialog = ProsesDialog(self.theme, proses_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._save_proses(dialog.result_data, proses_data['id'])
    
    def _save_proses(self, data: dict, proses_id: int = None):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if proses_id:
                # Update
                cursor.execute("""
                    UPDATE tanim.prosesler SET
                        kod = ?, ad = ?, kisa_ad = ?, hat_id = ?,
                        giris_depo_id = ?, cikis_depo_id = ?,
                        standart_sure_dk = ?, vardiya_kapasite_bara = ?,
                        renk_kodu = ?, sira_no = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    data['kod'], data['ad'], data['kisa_ad'], data['hat_id'],
                    data['giris_depo_id'], data['cikis_depo_id'],
                    data['standart_sure_dk'], data['vardiya_kapasite_bara'],
                    data['renk_kodu'], data['sira_no'], proses_id
                ))
                msg = "Proses güncellendi!"
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO tanim.prosesler 
                    (kod, ad, kisa_ad, hat_id, giris_depo_id, cikis_depo_id,
                     standart_sure_dk, vardiya_kapasite_bara, renk_kodu, sira_no)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['kod'], data['ad'], data['kisa_ad'], data['hat_id'],
                    data['giris_depo_id'], data['cikis_depo_id'],
                    data['standart_sure_dk'], data['vardiya_kapasite_bara'],
                    data['renk_kodu'], data['sira_no']
                ))
                msg = "Yeni proses eklendi!"
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "✓ Başarılı", msg)
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")
    
    def _delete_proses(self, proses_id: int, proses_kod: str):
        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"'{proses_kod}' prosesini silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Rota adımlarında kullanılıyor mu kontrol et
                cursor.execute("SELECT COUNT(*) FROM tanim.rota_adimlar WHERE proses_id = ? AND aktif_mi = 1", (proses_id,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    conn.close()
                    QMessageBox.warning(self, "Uyarı", f"Bu proses {count} rota adımında kullanılıyor. Önce rotalardan kaldırın!")
                    return
                
                cursor.execute("""
                    UPDATE tanim.prosesler SET silindi_mi = 1, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (proses_id,))
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "✓ Silindi", f"'{proses_kod}' prosesi silindi.")
                self._load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
