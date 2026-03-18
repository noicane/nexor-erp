# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Analiz Sonuçları Özet
Banyo analiz sonuçlarının özet görünümü
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


class LabSonucPage(BasePage):
    """Analiz Sonuçları Özet Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title_layout = QVBoxLayout()
        title = QLabel("📊 Analiz Sonuçları Özet")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 24px; font-weight: bold;")
        title_layout.addWidget(title)
        subtitle = QLabel("Banyoların son analiz durumlarını takip edin")
        subtitle.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 13px;")
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)
        header.addStretch()
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(f"background: {self.theme['bg_card_solid']}; color: {self.theme['text']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px 16px;")
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Özet Kartları
        summary_layout = QHBoxLayout()
        
        self.toplam_card = self._create_summary_card("Toplam Banyo", "0", "🧪", "#3B82F6")
        self.normal_card = self._create_summary_card("Normal", "0", "✅", "#22C55E")
        self.uyari_card = self._create_summary_card("Uyarı", "0", "⚠️", "#F59E0B")
        self.kritik_card = self._create_summary_card("Kritik", "0", "🔴", "#EF4444")
        
        summary_layout.addWidget(self.toplam_card)
        summary_layout.addWidget(self.normal_card)
        summary_layout.addWidget(self.uyari_card)
        summary_layout.addWidget(self.kritik_card)
        
        layout.addLayout(summary_layout)
        
        # Filtre
        filter_layout = QHBoxLayout()
        
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("Tüm Hatlar", None)
        self._load_hat_filter()
        self.hat_combo.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']}; min-width: 150px;")
        self.hat_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(QLabel("Hat:"))
        filter_layout.addWidget(self.hat_combo)
        
        self.durum_combo = QComboBox()
        self.durum_combo.addItem("Tüm Durumlar", None)
        self.durum_combo.addItem("✅ Normal", "NORMAL")
        self.durum_combo.addItem("⚠️ Uyarı", "UYARI")
        self.durum_combo.addItem("🔴 Kritik", "KRITIK")
        self.durum_combo.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 8px; color: {self.theme['text']}; min-width: 120px;")
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(QLabel("Durum:"))
        filter_layout.addWidget(self.durum_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme['bg_card_solid']}; border: 1px solid {self.theme['border']}; border-radius: 8px; gridline-color: {self.theme['border']}; color: {self.theme['text']}; }}
            QTableWidget::item {{ padding: 8px; }}
            QTableWidget::item:selected {{ background: {self.theme['primary']}; }}
            QHeaderView::section {{ background: {self.theme['bg_main']}; color: {self.theme['text']}; padding: 10px; border: none; border-bottom: 2px solid {self.theme['primary']}; font-weight: bold; }}
        """)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Banyo", "Hat", "Son Analiz", "Sıcaklık", "Hedef", "pH", "Hedef", "Durum"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 70)
        self.table.setColumnWidth(6, 70)
        self.table.setColumnWidth(7, 90)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _create_summary_card(self, title: str, value: str, icon: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {self.theme['bg_card_solid']};
                border: 1px solid {self.theme['border']};
                border-radius: 12px;
                border-left: 4px solid {color};
            }}
        """)
        card.setMinimumSize(150, 80)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 12px;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        layout.addWidget(value_label)
        
        return card
    
    def _load_hat_filter(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod FROM tanim.uretim_hatlari WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no")
            for row in cursor.fetchall():
                self.hat_combo.addItem(row[1], row[0])
            conn.close()
        except Exception: pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Son analiz sonuçlarını al
            sql = """
                WITH SonAnalizler AS (
                    SELECT banyo_id, MAX(tarih) as son_tarih
                    FROM uretim.banyo_analiz_sonuclari
                    GROUP BY banyo_id
                )
                SELECT b.id, b.kod, b.ad, h.kod as hat_kod,
                       a.tarih, a.sicaklik, b.sicaklik_hedef, b.sicaklik_min, b.sicaklik_max,
                       a.ph, b.ph_hedef, b.ph_min, b.ph_max
                FROM uretim.banyo_tanimlari b
                JOIN tanim.uretim_hatlari h ON b.hat_id=h.id
                LEFT JOIN SonAnalizler sa ON b.id=sa.banyo_id
                LEFT JOIN uretim.banyo_analiz_sonuclari a ON a.banyo_id=sa.banyo_id AND a.tarih=sa.son_tarih
                WHERE b.aktif_mi=1
            """
            params = []
            
            hat_id = self.hat_combo.currentData()
            if hat_id:
                sql += " AND b.hat_id=?"
                params.append(hat_id)
            
            sql += " ORDER BY h.sira_no, b.kod"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            # Durum hesapla ve filtrele
            data = []
            normal_count = 0
            uyari_count = 0
            kritik_count = 0
            
            for row in rows:
                durum = "NORMAL"
                
                # Sıcaklık kontrolü
                if row[5] and row[7] and row[8]:
                    if row[5] < row[7] or row[5] > row[8]:
                        durum = "KRITIK" if abs(row[5] - (row[6] or 0)) > 10 else "UYARI"
                
                # pH kontrolü
                if row[9] and row[11] and row[12]:
                    if row[9] < row[11] or row[9] > row[12]:
                        if durum != "KRITIK":
                            durum = "KRITIK" if abs(row[9] - (row[10] or 0)) > 1 else "UYARI"
                
                # Analiz yapılmamış
                if not row[4]:
                    durum = "UYARI"
                
                if durum == "NORMAL":
                    normal_count += 1
                elif durum == "UYARI":
                    uyari_count += 1
                else:
                    kritik_count += 1
                
                data.append((row, durum))
            
            # Durum filtresi
            durum_filter = self.durum_combo.currentData()
            if durum_filter:
                data = [(r, d) for r, d in data if d == durum_filter]
            
            # Özet kartları güncelle
            self.toplam_card.findChild(QLabel, "value_label").setText(str(len(rows)))
            self.normal_card.findChild(QLabel, "value_label").setText(str(normal_count))
            self.uyari_card.findChild(QLabel, "value_label").setText(str(uyari_count))
            self.kritik_card.findChild(QLabel, "value_label").setText(str(kritik_count))
            
            # Tabloyu doldur
            self.table.setRowCount(len(data))
            
            for i, (row, durum) in enumerate(data):
                # Banyo
                self.table.setItem(i, 0, QTableWidgetItem(f"{row[1]} - {row[2]}"))
                
                # Hat
                self.table.setItem(i, 1, QTableWidgetItem(row[3] or ''))
                
                # Son Analiz
                tarih = row[4].strftime("%d.%m.%Y %H:%M") if row[4] else "Analiz Yok"
                tarih_item = QTableWidgetItem(tarih)
                if not row[4]:
                    tarih_item.setForeground(QColor("#F59E0B"))
                self.table.setItem(i, 2, tarih_item)
                
                # Sıcaklık
                sic_item = QTableWidgetItem(f"{row[5]:.1f}°C" if row[5] else '-')
                if row[5] and row[7] and row[8]:
                    if row[5] < row[7] or row[5] > row[8]:
                        sic_item.setForeground(Qt.red)
                    else:
                        sic_item.setForeground(Qt.green)
                self.table.setItem(i, 3, sic_item)
                
                # Sıcaklık Hedef
                self.table.setItem(i, 4, QTableWidgetItem(f"{row[6]:.0f}°C" if row[6] else '-'))
                
                # pH
                ph_item = QTableWidgetItem(f"{row[9]:.2f}" if row[9] else '-')
                if row[9] and row[11] and row[12]:
                    if row[9] < row[11] or row[9] > row[12]:
                        ph_item.setForeground(Qt.red)
                    else:
                        ph_item.setForeground(Qt.green)
                self.table.setItem(i, 5, ph_item)
                
                # pH Hedef
                self.table.setItem(i, 6, QTableWidgetItem(f"{row[10]:.1f}" if row[10] else '-'))
                
                # Durum
                durum_map = {"NORMAL": "✅ Normal", "UYARI": "⚠️ Uyarı", "KRITIK": "🔴 Kritik"}
                durum_colors = {"NORMAL": Qt.green, "UYARI": QColor("#F59E0B"), "KRITIK": Qt.red}
                durum_item = QTableWidgetItem(durum_map[durum])
                durum_item.setForeground(durum_colors[durum])
                self.table.setItem(i, 7, durum_item)
                
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Hata", str(e))
