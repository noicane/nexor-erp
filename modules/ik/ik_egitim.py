# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İK Eğitim Takip
Personel eğitim kayıtları ve planlama
"""
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QDateEdit, QTextEdit, QFormLayout, QWidget, QTabWidget,
    QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class EgitimKayitDialog(QDialog):
    """Eğitim kaydı ekleme dialog'u"""
    
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Eğitim Kaydı Ekle")
        self.setMinimumSize(500, 450)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
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
        
        title = QLabel("📚 Eğitim Kaydı Ekle")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.cmb_personel = QComboBox()
        form.addRow("Personel:", self.cmb_personel)
        
        self.cmb_egitim = QComboBox()
        form.addRow("Eğitim:", self.cmb_egitim)
        
        self.dt_tarih = QDateEdit()
        self.dt_tarih.setCalendarPopup(True)
        self.dt_tarih.setDate(QDate.currentDate())
        form.addRow("Eğitim Tarihi:", self.dt_tarih)
        
        self.txt_egitmen = QLineEdit()
        self.txt_egitmen.setPlaceholderText("Eğitimi veren kişi/kurum")
        form.addRow("Eğitmen:", self.txt_egitmen)
        
        self.spn_sure = QDoubleSpinBox()
        self.spn_sure.setRange(0.5, 100)
        self.spn_sure.setValue(1)
        self.spn_sure.setSuffix(" saat")
        form.addRow("Süre:", self.spn_sure)
        
        self.cmb_sonuc = QComboBox()
        self.cmb_sonuc.addItems(["Başarılı", "Başarısız", "Katıldı", "Devam Ediyor"])
        form.addRow("Sonuç:", self.cmb_sonuc)
        
        self.spn_puan = QSpinBox()
        self.spn_puan.setRange(0, 100)
        self.spn_puan.setValue(0)
        self.spn_puan.setSpecialValueText("Değerlendirilmedi")
        form.addRow("Puan:", self.spn_puan)
        
        self.txt_not = QTextEdit()
        self.txt_not.setMaximumHeight(60)
        form.addRow("Notlar:", self.txt_not)
        
        layout.addLayout(form)
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
        
        save_btn = QPushButton("💾 Kaydet")
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
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_personel.addItem(row[1], row[0])
            
            cursor.execute("SELECT id, egitim_adi FROM ik.egitimler WHERE aktif_mi = 1 ORDER BY egitim_adi")
            for row in cursor.fetchall():
                self.cmb_egitim.addItem(row[1], row[0])
            
            conn.close()
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
    
    def _save(self):
        try:
            personel_id = self.cmb_personel.currentData()
            egitim_id = self.cmb_egitim.currentData()
            
            if not personel_id or not egitim_id:
                QMessageBox.warning(self, "Uyarı", "Personel ve eğitim seçilmelidir.")
                return
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ik.egitim_kayitlari (
                    egitim_id, personel_id, egitim_tarihi, egitmen,
                    sure_saat, sonuc, puan, notlar
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                egitim_id, personel_id, self.dt_tarih.date().toPython(),
                self.txt_egitmen.text() or None, self.spn_sure.value(),
                self.cmb_sonuc.currentText(), 
                self.spn_puan.value() if self.spn_puan.value() > 0 else None,
                self.txt_not.toPlainText() or None
            ))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Başarılı", "Eğitim kaydı eklendi.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")


class IKEgitimPage(BasePage):
    """İK Eğitim Takip Sayfası"""
    
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
        
        title = QLabel("📚 Eğitim Takip")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        header.addWidget(title)
        
        header.addStretch()
        
        new_btn = QPushButton("➕ Eğitim Kaydı Ekle")
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
        new_btn.clicked.connect(self._new_kayit)
        header.addWidget(new_btn)
        
        layout.addLayout(header)
        
        # Özet kartları
        ozet_frame = QFrame()
        ozet_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        ozet_layout = QHBoxLayout(ozet_frame)
        ozet_layout.setContentsMargins(16, 16, 16, 16)
        
        self.kart_egitim = self._create_ozet_kart("📚", "Toplam Eğitim", "0", self.theme.get('primary'))
        ozet_layout.addWidget(self.kart_egitim)
        
        self.kart_katilim = self._create_ozet_kart("👥", "Katılımcı", "0", self.theme.get('success'))
        ozet_layout.addWidget(self.kart_katilim)
        
        self.kart_saat = self._create_ozet_kart("⏱️", "Toplam Saat", "0", self.theme.get('info'))
        ozet_layout.addWidget(self.kart_saat)
        
        self.kart_yaklasan = self._create_ozet_kart("📅", "Yenileme Bekleyen", "0", self.theme.get('warning'))
        ozet_layout.addWidget(self.kart_yaklasan)
        
        layout.addWidget(ozet_frame)
        
        # Filtreler
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        
        filter_layout.addWidget(QLabel("Ara:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Personel adı, eğitim adı...")
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.setMinimumWidth(200)
        self.search_input.returnPressed.connect(self._load_data)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addWidget(QLabel("Eğitim:"))
        self.egitim_combo = QComboBox()
        self.egitim_combo.setStyleSheet(self._combo_style())
        self.egitim_combo.setMinimumWidth(150)
        self.egitim_combo.addItem("Tümü", None)
        self.egitim_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.egitim_combo)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet(self._tab_style())
        
        tabs.addTab(self._create_kayitlar_tab(), "📋 Eğitim Kayıtları")
        tabs.addTab(self._create_yenileme_tab(), "⚠️ Yenileme Bekleyenler")
        tabs.addTab(self._create_matris_tab(), "📊 Eğitim Matrisi")
        
        layout.addWidget(tabs, 1)
        
        # Eğitimleri yükle
        self._load_egitimler()
    
    def _create_ozet_kart(self, icon: str, baslik: str, deger: str, renk: str) -> QFrame:
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
    
    def _create_kayitlar_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        self.kayit_table = QTableWidget()
        self.kayit_table.setColumnCount(8)
        self.kayit_table.setHorizontalHeaderLabels([
            "Tarih", "Personel", "Eğitim", "Eğitmen", "Süre", "Sonuç", "Puan", "Sonraki"
        ])
        self.kayit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.kayit_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.kayit_table.setStyleSheet(self._table_style())
        self.kayit_table.verticalHeader().setVisible(False)
        self.kayit_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.kayit_table)
        return widget
    
    def _create_yenileme_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        self.yenileme_table = QTableWidget()
        self.yenileme_table.setColumnCount(6)
        self.yenileme_table.setHorizontalHeaderLabels([
            "Personel", "Eğitim", "Son Eğitim", "Yenileme Tarihi", "Gecikme", "Durum"
        ])
        self.yenileme_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.yenileme_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.yenileme_table.setStyleSheet(self._table_style())
        self.yenileme_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.yenileme_table)
        return widget
    
    def _create_matris_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        info = QLabel("📊 Eğitim matrisi: Personel x Eğitim bazında tamamlanma durumu")
        info.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px; padding: 10px;")
        layout.addWidget(info)
        
        self.matris_table = QTableWidget()
        self.matris_table.setStyleSheet(self._table_style())
        self.matris_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.matris_table)
        return widget
    
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
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary')};
                font-weight: bold;
            }}
        """
    
    def _tab_style(self):
        return f"""
            QTabWidget::pane {{ 
                border: 1px solid {self.theme.get('border')}; 
                background: {self.theme.get('bg_card')}; 
                border-radius: 8px; 
            }}
            QTabBar::tab {{ 
                background: {self.theme.get('bg_input')}; 
                color: {self.theme.get('text')}; 
                padding: 10px 20px; 
                border: 1px solid {self.theme.get('border')}; 
                border-bottom: none; 
                border-radius: 6px 6px 0 0; 
                margin-right: 2px; 
            }}
            QTabBar::tab:selected {{ 
                background: {self.theme.get('bg_card')}; 
                border-bottom: 2px solid {self.theme.get('primary')}; 
            }}
        """
    
    def _load_egitimler(self):
        """Eğitim listesini combo'ya yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, egitim_adi FROM ik.egitimler WHERE aktif_mi = 1 ORDER BY egitim_adi")
            for row in cursor.fetchall():
                self.egitim_combo.addItem(row[1], row[0])
            conn.close()
        except Exception as e:
            print(f"Eğitim yükleme hatası: {e}")
    
    def _load_data(self):
        """Eğitim verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Özet istatistikler
            cursor.execute("SELECT COUNT(DISTINCT egitim_id) FROM ik.egitim_kayitlari")
            egitim_sayisi = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT personel_id) FROM ik.egitim_kayitlari")
            katilimci = cursor.fetchone()[0]
            
            cursor.execute("SELECT ISNULL(SUM(sure_saat), 0) FROM ik.egitim_kayitlari")
            toplam_saat = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM ik.egitim_kayitlari ek
                JOIN ik.egitimler e ON ek.egitim_id = e.id
                WHERE e.periyot_ay IS NOT NULL 
                  AND ek.sonraki_egitim_tarihi IS NOT NULL
                  AND ek.sonraki_egitim_tarihi <= GETDATE()
            """)
            yaklasan = cursor.fetchone()[0]
            
            # Kartları güncelle
            self.kart_egitim.findChild(QLabel, "value").setText(str(egitim_sayisi))
            self.kart_katilim.findChild(QLabel, "value").setText(str(katilimci))
            self.kart_saat.findChild(QLabel, "value").setText(f"{toplam_saat:.1f}")
            self.kart_yaklasan.findChild(QLabel, "value").setText(str(yaklasan))
            
            # Filtreler
            where = ["1=1"]
            params = []
            
            search = self.search_input.text().strip()
            if search:
                where.append("(p.ad LIKE ? OR p.soyad LIKE ? OR e.egitim_adi LIKE ?)")
                params.extend([f"%{search}%"] * 3)
            
            egitim_id = self.egitim_combo.currentData()
            if egitim_id:
                where.append("ek.egitim_id = ?")
                params.append(egitim_id)
            
            where_clause = " AND ".join(where)
            
            # Eğitim kayıtları
            cursor.execute(f"""
                SELECT 
                    ek.egitim_tarihi, p.ad + ' ' + p.soyad as personel,
                    e.egitim_adi, ek.egitmen, ek.sure_saat, ek.sonuc,
                    ek.puan, ek.sonraki_egitim_tarihi
                FROM ik.egitim_kayitlari ek
                JOIN ik.personeller p ON ek.personel_id = p.id
                JOIN ik.egitimler e ON ek.egitim_id = e.id
                WHERE {where_clause}
                ORDER BY ek.egitim_tarihi DESC
            """, params)
            
            self.kayit_table.setRowCount(0)
            for row in cursor.fetchall():
                row_idx = self.kayit_table.rowCount()
                self.kayit_table.insertRow(row_idx)
                
                tarih = row[0].strftime('%d.%m.%Y') if row[0] else '-'
                self.kayit_table.setItem(row_idx, 0, QTableWidgetItem(tarih))
                self.kayit_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
                self.kayit_table.setItem(row_idx, 2, QTableWidgetItem(row[2] or ''))
                self.kayit_table.setItem(row_idx, 3, QTableWidgetItem(row[3] or '-'))
                self.kayit_table.setItem(row_idx, 4, QTableWidgetItem(f"{row[4]:.1f} saat" if row[4] else '-'))
                
                # Sonuç
                sonuc = row[5] or ''
                sonuc_item = QTableWidgetItem(sonuc)
                if sonuc == 'Başarılı':
                    sonuc_item.setForeground(QColor(self.theme.get('success')))
                elif sonuc == 'Başarısız':
                    sonuc_item.setForeground(QColor(self.theme.get('danger')))
                self.kayit_table.setItem(row_idx, 5, sonuc_item)
                
                self.kayit_table.setItem(row_idx, 6, QTableWidgetItem(str(row[6]) if row[6] else '-'))
                
                sonraki = row[7].strftime('%d.%m.%Y') if row[7] else '-'
                self.kayit_table.setItem(row_idx, 7, QTableWidgetItem(sonraki))
            
            # Yenileme bekleyenler
            self._load_yenileme_data(cursor)
            
            conn.close()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Veri yüklenemedi: {e}")
    
    def _load_yenileme_data(self, cursor):
        """Yenileme bekleyenleri yükle"""
        cursor.execute("""
            SELECT 
                p.ad + ' ' + p.soyad as personel,
                e.egitim_adi,
                ek.egitim_tarihi,
                ek.sonraki_egitim_tarihi
            FROM ik.egitim_kayitlari ek
            JOIN ik.personeller p ON ek.personel_id = p.id
            JOIN ik.egitimler e ON ek.egitim_id = e.id
            WHERE ek.sonraki_egitim_tarihi IS NOT NULL
              AND ek.sonraki_egitim_tarihi <= DATEADD(day, 30, GETDATE())
            ORDER BY ek.sonraki_egitim_tarihi
        """)
        
        self.yenileme_table.setRowCount(0)
        today = date.today()
        
        for row in cursor.fetchall():
            row_idx = self.yenileme_table.rowCount()
            self.yenileme_table.insertRow(row_idx)
            
            self.yenileme_table.setItem(row_idx, 0, QTableWidgetItem(row[0] or ''))
            self.yenileme_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
            
            son_egitim = row[2].strftime('%d.%m.%Y') if row[2] else '-'
            self.yenileme_table.setItem(row_idx, 2, QTableWidgetItem(son_egitim))
            
            yenileme = row[3].strftime('%d.%m.%Y') if row[3] else '-'
            self.yenileme_table.setItem(row_idx, 3, QTableWidgetItem(yenileme))
            
            # Gecikme
            if row[3]:
                gecikme = (today - row[3]).days
                gecikme_item = QTableWidgetItem(str(gecikme) if gecikme > 0 else "0")
                if gecikme > 0:
                    gecikme_item.setForeground(QColor(self.theme.get('danger')))
                self.yenileme_table.setItem(row_idx, 4, gecikme_item)
                
                # Durum
                if gecikme > 0:
                    durum = "⚠️ GECİKMİŞ"
                    durum_item = QTableWidgetItem(durum)
                    durum_item.setForeground(QColor(self.theme.get('danger')))
                else:
                    durum = "⏳ Yaklaşıyor"
                    durum_item = QTableWidgetItem(durum)
                    durum_item.setForeground(QColor(self.theme.get('warning')))
                self.yenileme_table.setItem(row_idx, 5, durum_item)
    
    def _new_kayit(self):
        """Yeni eğitim kaydı ekle"""
        dialog = EgitimKayitDialog(self.theme, self)
        if dialog.exec():
            self._load_data()
