# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İK İzin Yönetimi
İzin talepleri oluşturma, onaylama ve takip
"""
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QDateEdit, QTextEdit, QFormLayout, QWidget, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class IzinTalepDialog(QDialog):
    """Yeni izin talebi oluşturma dialog'u"""
    
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Yeni İzin Talebi")
        self.setMinimumSize(500, 450)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        title = QLabel("🏖️ Yeni İzin Talebi")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)
        
        # Form
        form = QFormLayout()
        form.setSpacing(12)
        
        # Personel seçimi
        self.cmb_personel = QComboBox()
        self.cmb_personel.setMinimumWidth(300)
        form.addRow("Personel:", self.cmb_personel)
        
        # İzin türü
        self.cmb_izin_turu = QComboBox()
        form.addRow("İzin Türü:", self.cmb_izin_turu)
        
        # Başlangıç tarihi
        self.dt_baslangic = QDateEdit()
        self.dt_baslangic.setCalendarPopup(True)
        self.dt_baslangic.setDate(QDate.currentDate())
        self.dt_baslangic.dateChanged.connect(self._calculate_days)
        form.addRow("Başlangıç:", self.dt_baslangic)
        
        # Bitiş tarihi
        self.dt_bitis = QDateEdit()
        self.dt_bitis.setCalendarPopup(True)
        self.dt_bitis.setDate(QDate.currentDate())
        self.dt_bitis.dateChanged.connect(self._calculate_days)
        form.addRow("Bitiş:", self.dt_bitis)
        
        # Gün sayısı
        self.lbl_gun = QLabel("1 gün")
        self.lbl_gun.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold;")
        form.addRow("Süre:", self.lbl_gun)
        
        # Açıklama
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(80)
        self.txt_aciklama.setPlaceholderText("İzin nedeni ve açıklamalar...")
        form.addRow("Açıklama:", self.txt_aciklama)
        
        layout.addLayout(form)
        
        # Kalan izin bilgisi
        self.izin_info = QFrame()
        self.izin_info.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
            }}
        """)
        info_layout = QHBoxLayout(self.izin_info)
        info_layout.setContentsMargins(16, 12, 16, 12)
        
        self.lbl_izin_hak = QLabel("Yıllık İzin Hakkı: 14 gün | Kullanılan: 3 gün | Kalan: 11 gün")
        self.lbl_izin_hak.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px;")
        info_layout.addWidget(self.lbl_izin_hak)
        
        layout.addWidget(self.izin_info)
        
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 10px 24px;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Talep Oluştur")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
            }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        """Personel ve izin türlerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Personeller
            cursor.execute("""
                SELECT id, sicil_no, ad + ' ' + soyad as ad_soyad
                FROM ik.personeller
                WHERE aktif_mi = 1
                ORDER BY ad, soyad
            """)
            for row in cursor.fetchall():
                self.cmb_personel.addItem(f"{row[1]} - {row[2]}", row[0])
            
            # İzin türleri
            cursor.execute("SELECT id, ad FROM ik.izin_turleri WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_izin_turu.addItem(row[1], row[0])
            
            conn.close()
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
    
    def _calculate_days(self):
        """Gün sayısını hesapla"""
        d1 = self.dt_baslangic.date().toPython()
        d2 = self.dt_bitis.date().toPython()
        
        if d2 >= d1:
            days = (d2 - d1).days + 1
            self.lbl_gun.setText(f"{days} gün")
        else:
            self.lbl_gun.setText("Geçersiz tarih")
    
    def _save(self):
        """İzin talebini kaydet"""
        try:
            personel_id = self.cmb_personel.currentData()
            izin_turu_id = self.cmb_izin_turu.currentData()
            baslangic = self.dt_baslangic.date().toPython()
            bitis = self.dt_bitis.date().toPython()
            aciklama = self.txt_aciklama.toPlainText()
            
            if not personel_id:
                QMessageBox.warning(self, "Uyarı", "Lütfen personel seçin.")
                return
            
            if bitis < baslangic:
                QMessageBox.warning(self, "Uyarı", "Bitiş tarihi başlangıçtan önce olamaz.")
                return
            
            gun_sayisi = (bitis - baslangic).days + 1
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # talep_no kolonu yok, sadece gerekli kolonları ekle
            cursor.execute("""
                INSERT INTO ik.izin_talepleri (
                    personel_id, izin_turu_id, baslangic_tarihi, 
                    bitis_tarihi, gun_sayisi, aciklama, durum
                ) VALUES (?, ?, ?, ?, ?, ?, 'BEKLEMEDE')
            """, (personel_id, izin_turu_id, baslangic, bitis, gun_sayisi, aciklama))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Başarılı", "İzin talebi oluşturuldu.")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")


class IKIzinPage(BasePage):
    """İK İzin Yönetimi Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🏖️ İzin Yönetimi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        header.addWidget(title)
        
        header.addStretch()
        
        # Yeni talep butonu
        new_btn = QPushButton("➕ Yeni İzin Talebi")
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
        """)
        new_btn.clicked.connect(self._new_talep)
        header.addWidget(new_btn)
        
        layout.addLayout(header)
        
        # Özet kartları
        ozet_frame = QFrame()
        ozet_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        ozet_layout = QHBoxLayout(ozet_frame)
        ozet_layout.setContentsMargins(16, 16, 16, 16)
        
        self.kart_bekleyen = self._create_ozet_kart("⏳", "Bekleyen", "0", self.theme.get('warning'))
        ozet_layout.addWidget(self.kart_bekleyen)
        
        self.kart_onaylanan = self._create_ozet_kart("✅", "Onaylanan", "0", self.theme.get('success'))
        ozet_layout.addWidget(self.kart_onaylanan)
        
        self.kart_reddedilen = self._create_ozet_kart("❌", "Reddedilen", "0", self.theme.get('danger'))
        ozet_layout.addWidget(self.kart_reddedilen)
        
        self.kart_bu_ay = self._create_ozet_kart("📅", "Bu Ay İzinli", "0", self.theme.get('info'))
        ozet_layout.addWidget(self.kart_bu_ay)
        
        layout.addWidget(ozet_frame)
        
        # Filtreler
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        
        # Durum filtresi
        filter_layout.addWidget(QLabel("Durum:"))
        self.status_combo = QComboBox()
        self.status_combo.setStyleSheet(self._combo_style())
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("⏳ Beklemede", "BEKLEMEDE")
        self.status_combo.addItem("✅ Onaylandı", "ONAYLANDI")
        self.status_combo.addItem("❌ Reddedildi", "REDDEDILDI")
        self.status_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.status_combo)
        
        # Arama
        filter_layout.addWidget(QLabel("Ara:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Personel adı...")
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.setMinimumWidth(200)
        self.search_input.returnPressed.connect(self._load_data)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)
        
        # Tablo - talep_no kolonu kaldırıldı
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Personel", "İzin Türü", "Başlangıç", "Bitiş", 
            "Gün", "Durum", "İşlem"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 120)
        self.table.setStyleSheet(self._table_style())
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        layout.addWidget(self.table, 1)
    
    def _create_ozet_kart(self, icon: str, baslik: str, deger: str, renk: str) -> QFrame:
        """Özet kartı"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_main')};
                border: 1px solid {renk};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        header = QLabel(f"{icon} {baslik}")
        header.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 11px;")
        layout.addWidget(header)
        
        value = QLabel(deger)
        value.setObjectName("value")
        value.setStyleSheet(f"color: {renk}; font-size: 24px; font-weight: bold;")
        layout.addWidget(value)
        
        return frame
    
    def _input_style(self):
        return f"""
            QLineEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px 12px;
                color: {self.theme.get('text')};
            }}
        """
    
    def _combo_style(self):
        return f"""
            QComboBox {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
        """
    
    def _table_style(self):
        return f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {self.theme.get('border')};
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
        """
    
    def _load_data(self):
        """İzin taleplerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            where = ["1=1"]
            params = []
            
            # Durum filtresi
            status = self.status_combo.currentData()
            if status:
                where.append("it.durum = ?")
                params.append(status)
            
            # Arama
            search = self.search_input.text().strip()
            if search:
                where.append("(p.ad LIKE ? OR p.soyad LIKE ?)")
                params.extend([f"%{search}%"] * 2)
            
            where_clause = " AND ".join(where)
            
            # Özet sayıları
            cursor.execute("SELECT COUNT(*) FROM ik.izin_talepleri WHERE durum = 'BEKLEMEDE'")
            bekleyen = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ik.izin_talepleri WHERE durum = 'ONAYLANDI'")
            onaylanan = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ik.izin_talepleri WHERE durum = 'REDDEDILDI'")
            reddedilen = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM ik.izin_talepleri 
                WHERE durum = 'ONAYLANDI' 
                  AND MONTH(baslangic_tarihi) = MONTH(GETDATE())
                  AND YEAR(baslangic_tarihi) = YEAR(GETDATE())
            """)
            bu_ay = cursor.fetchone()[0]
            
            # Kartları güncelle
            self.kart_bekleyen.findChild(QLabel, "value").setText(str(bekleyen))
            self.kart_onaylanan.findChild(QLabel, "value").setText(str(onaylanan))
            self.kart_reddedilen.findChild(QLabel, "value").setText(str(reddedilen))
            self.kart_bu_ay.findChild(QLabel, "value").setText(str(bu_ay))
            
            # Talepler - talep_no yok
            cursor.execute(f"""
                SELECT 
                    it.id, p.ad + ' ' + p.soyad as personel,
                    iz.ad as izin_turu, it.baslangic_tarihi, it.bitis_tarihi,
                    it.gun_sayisi, it.durum
                FROM ik.izin_talepleri it
                JOIN ik.personeller p ON it.personel_id = p.id
                JOIN ik.izin_turleri iz ON it.izin_turu_id = iz.id
                WHERE {where_clause}
                ORDER BY it.olusturma_tarihi DESC
            """, params)
            
            self.table.setRowCount(0)
            
            for row in cursor.fetchall():
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                
                # ID
                item = QTableWidgetItem(str(row[0]))
                item.setData(Qt.UserRole, row[0])
                self.table.setItem(row_idx, 0, item)
                
                # Personel
                self.table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
                
                # İzin türü
                self.table.setItem(row_idx, 2, QTableWidgetItem(row[2] or ''))
                
                # Başlangıç
                baslangic = row[3].strftime('%d.%m.%Y') if row[3] else '-'
                self.table.setItem(row_idx, 3, QTableWidgetItem(baslangic))
                
                # Bitiş
                bitis = row[4].strftime('%d.%m.%Y') if row[4] else '-'
                self.table.setItem(row_idx, 4, QTableWidgetItem(bitis))
                
                # Gün
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(row[5] or 0)))
                
                # Durum
                durum = row[6] or ''
                durum_item = QTableWidgetItem(durum)
                if durum == 'BEKLEMEDE':
                    durum_item.setForeground(QColor(self.theme.get('warning')))
                elif durum == 'ONAYLANDI':
                    durum_item.setForeground(QColor(self.theme.get('success')))
                elif durum == 'REDDEDILDI':
                    durum_item.setForeground(QColor(self.theme.get('danger')))
                self.table.setItem(row_idx, 6, durum_item)
                
                # İşlem butonları
                if durum == 'BEKLEMEDE':
                    widget = self.create_action_buttons([
                        ("✓", "Onayla", lambda checked, tid=row[0]: self._onayla(tid), "success"),
                        ("✕", "Reddet", lambda checked, tid=row[0]: self._reddet(tid), "delete"),
                    ])
                    self.table.setCellWidget(row_idx, 7, widget)
                    self.table.setRowHeight(row_idx, 42)
                else:
                    self.table.setItem(row_idx, 7, QTableWidgetItem("-"))
            
            conn.close()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Veri yüklenemedi: {e}")
    
    def _new_talep(self):
        """Yeni izin talebi oluştur"""
        dialog = IzinTalepDialog(self.theme, self)
        if dialog.exec():
            self._load_data()
    
    def _onayla(self, talep_id: int):
        """İzin talebini onayla"""
        reply = QMessageBox.question(self, "Onay", "Bu izin talebi onaylanacak. Devam edilsin mi?")
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE ik.izin_talepleri 
                    SET durum = 'ONAYLANDI', onay_tarihi = GETDATE()
                    WHERE id = ?
                """, (talep_id,))
                conn.commit()
                conn.close()
                
                self._load_data()
                QMessageBox.information(self, "Başarılı", "İzin talebi onaylandı.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Onay hatası: {e}")
    
    def _reddet(self, talep_id: int):
        """İzin talebini reddet"""
        reply = QMessageBox.question(self, "Red", "Bu izin talebi reddedilecek. Devam edilsin mi?")
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE ik.izin_talepleri 
                    SET durum = 'REDDEDILDI', onay_tarihi = GETDATE()
                    WHERE id = ?
                """, (talep_id,))
                conn.commit()
                conn.close()
                
                self._load_data()
                QMessageBox.information(self, "Bilgi", "İzin talebi reddedildi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Red hatası: {e}")
