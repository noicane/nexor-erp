# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Event Log Ekranı
Tüm sistem event'lerini gösterir ve yönetir
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class EventLogPage(BasePage):
    """Event Log - Sistem olayları takip ekranı"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
        
        # Otomatik yenileme (30 saniye)
        self.auto_refresh = QTimer()
        self.auto_refresh.timeout.connect(self._load_data)
        self.auto_refresh.start(30000)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # Header
        header = self.create_page_header("Event Log", "Sistem olaylari ve bildirimler")
        refresh_btn = self.create_primary_button("Yenile")
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # KPI kartlari
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)
        self._kpi_toplam = self.create_stat_card("TOPLAM", "0", color=brand.INFO)
        self._kpi_bekleyen = self.create_stat_card("BEKLEYEN", "0", color=brand.WARNING)
        self._kpi_tamamlanan = self.create_stat_card("TAMAMLANAN", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self._kpi_toplam)
        kpi_row.addWidget(self._kpi_bekleyen)
        kpi_row.addWidget(self._kpi_tamamlanan)
        kpi_row.addStretch()
        layout.addLayout(kpi_row)

        # stat_widgets uyumluluk - findChild ile guncelleme
        self.stat_widgets = {
            'toplam': self._kpi_toplam.findChild(QLabel, "stat_value"),
            'bekleyen': self._kpi_bekleyen.findChild(QLabel, "stat_value"),
            'tamamlanan': self._kpi_tamamlanan.findChild(QLabel, "stat_value"),
        }

        # Filtreler
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: {brand.R_LG}px; padding: {brand.SP_3}px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(brand.SP_3)

        input_css = f"background: {brand.BG_INPUT}; color: {brand.TEXT}; border: 1px solid {brand.BORDER}; border-radius: {brand.R_SM}px; padding: {brand.SP_2}px {brand.SP_3}px; font-size: {brand.FS_BODY_SM}px;"

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Lot no ara...")
        self.search_input.setFixedWidth(brand.sp(150))
        self.search_input.setStyleSheet(f"QLineEdit {{ {input_css} }}")
        self.search_input.returnPressed.connect(self._load_data)
        filter_layout.addWidget(self.search_input)

        lbl_css = f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;"
        filter_layout.addWidget(QLabel("Tip:", styleSheet=lbl_css))
        self.event_combo = QComboBox()
        self.event_combo.setFixedWidth(brand.sp(180))
        self.event_combo.setStyleSheet(f"QComboBox {{ {input_css} }}")
        self.event_combo.addItem("Tumu", None)
        self.event_combo.addItem("Giris Kontrol", "GIRIS_KONTROL_GEREKLI")
        self.event_combo.addItem("Final Kontrol", "FINAL_KONTROL_GEREKLI")
        self.event_combo.addItem("Uretime Hazir", "URETIM_HAZIR")
        self.event_combo.addItem("Sevk Hazir", "SEVK_HAZIR")
        self.event_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.event_combo)

        filter_layout.addWidget(QLabel("Durum:", styleSheet=lbl_css))
        self.durum_combo = QComboBox()
        self.durum_combo.setFixedWidth(brand.sp(120))
        self.durum_combo.setStyleSheet(f"QComboBox {{ {input_css} }}")
        self.durum_combo.addItem("Tumu", None)
        self.durum_combo.addItem("Bekleyen", "BEKLIYOR")
        self.durum_combo.addItem("Tamamlanan", "TAMAMLANDI")
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.durum_combo)

        filter_layout.addWidget(QLabel("Tarih:", styleSheet=lbl_css))
        self.tarih_bas = QDateEdit()
        self.tarih_bas.setDate(QDate.currentDate().addDays(-7))
        self.tarih_bas.setCalendarPopup(True)
        self.tarih_bas.setFixedWidth(brand.sp(110))
        self.tarih_bas.setStyleSheet(f"QDateEdit {{ {input_css} }}")
        filter_layout.addWidget(self.tarih_bas)

        filter_layout.addWidget(QLabel("-", styleSheet=f"color: {brand.TEXT_DIM};"))
        self.tarih_bit = QDateEdit()
        self.tarih_bit.setDate(QDate.currentDate())
        self.tarih_bit.setCalendarPopup(True)
        self.tarih_bit.setFixedWidth(brand.sp(110))
        self.tarih_bit.setStyleSheet(f"QDateEdit {{ {input_css} }}")
        filter_layout.addWidget(self.tarih_bit)
        
        ara_btn = QPushButton("🔍 Ara")
        ara_btn.setCursor(Qt.PointingHandCursor)
        ara_btn.setStyleSheet(f"QPushButton {{ background: {brand.PRIMARY}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; }} QPushButton:hover {{ background: #B91C1C; }}")
        ara_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(ara_btn)
        
        filter_layout.addStretch()
        layout.addWidget(filter_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Lot No", "Event Tipi", "Durum", "Depo", "Miktar", "Zaman", "Süre"
        ])
        
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, brand.sp(140))
        self.table.setColumnWidth(2, brand.sp(180))
        self.table.setColumnWidth(3, brand.sp(100))
        self.table.setColumnWidth(4, brand.sp(120))
        self.table.setColumnWidth(5, brand.sp(80))
        self.table.setColumnWidth(6, brand.sp(140))
        self.table.setColumnWidth(7, brand.sp(80))

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD}; border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px; outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_3}px {brand.SP_4}px;
                border-bottom: 1px solid {brand.BORDER}; color: {brand.TEXT};
            }}
            QTableWidget::item:alternate {{ background: {brand.BG_MAIN}; }}
            QTableWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE}; color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_4}px; border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px; font-weight: {brand.FW_SEMIBOLD};
            }}
        """)

        layout.addWidget(self.table, 1)

        # Footer
        footer_layout = QHBoxLayout()
        self.footer_label = QLabel("Yukleniyor...")
        self.footer_label.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;")
        footer_layout.addWidget(self.footer_label)
        footer_layout.addStretch()

        temizle_btn = self.create_danger_button("Eski Kayitlari Temizle")
        temizle_btn.clicked.connect(self._temizle_eski)
        footer_layout.addWidget(temizle_btn)

        layout.addLayout(footer_layout)
    
    def _load_data(self):
        """Event log verilerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Filtreler
            search = self.search_input.text().strip()
            event_tipi = self.event_combo.currentData()
            durum = self.durum_combo.currentData()
            tarih_bas = self.tarih_bas.date().toPython()
            tarih_bit = self.tarih_bit.date().toPython()
            
            # Ana sorgu
            query = """
                SELECT 
                    e.id,
                    e.lot_no,
                    e.event_tipi,
                    e.event_durumu,
                    COALESCE(d.kod + ' - ' + d.ad, 'Bilinmiyor') AS depo,
                    e.miktar,
                    e.event_zamani,
                    CASE 
                        WHEN e.event_durumu = 'BEKLIYOR' 
                        THEN DATEDIFF(HOUR, e.event_zamani, GETDATE())
                        ELSE NULL
                    END AS bekleme_saat
                FROM stok.hareket_event_log e
                LEFT JOIN tanim.depolar d ON e.depo_id = d.id
                WHERE e.event_zamani >= ? AND e.event_zamani < DATEADD(DAY, 1, ?)
            """
            params = [tarih_bas, tarih_bit]
            
            if search:
                query += " AND e.lot_no LIKE ?"
                params.append(f"%{search}%")
            
            if event_tipi:
                query += " AND e.event_tipi = ?"
                params.append(event_tipi)
            
            if durum:
                query += " AND e.event_durumu = ?"
                params.append(durum)
            
            query += " ORDER BY e.event_zamani DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # İstatistikler
            cursor.execute("""
                SELECT 
                    COUNT(*) AS toplam,
                    SUM(CASE WHEN event_durumu = 'BEKLIYOR' THEN 1 ELSE 0 END) AS bekleyen,
                    SUM(CASE WHEN event_durumu = 'TAMAMLANDI' THEN 1 ELSE 0 END) AS tamamlanan
                FROM stok.hareket_event_log
                WHERE event_zamani >= ? AND event_zamani < DATEADD(DAY, 1, ?)
            """, (tarih_bas, tarih_bit))
            stats = cursor.fetchone()
            
            conn.close()
            
            # İstatistikleri güncelle
            if stats:
                self.stat_widgets['toplam'].setText(str(stats[0] or 0))
                self.stat_widgets['bekleyen'].setText(str(stats[1] or 0))
                self.stat_widgets['tamamlanan'].setText(str(stats[2] or 0))
            
            # Tabloyu doldur
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # ID
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                
                # Lot No
                lot_item = QTableWidgetItem(row[1] or '')
                lot_item.setForeground(QColor(brand.INFO))
                self.table.setItem(i, 1, lot_item)
                
                # Event Tipi
                event_text = self._format_event_tipi(row[2])
                self.table.setItem(i, 2, QTableWidgetItem(event_text))
                
                # Durum
                durum_item = QTableWidgetItem(row[3] or '')
                if row[3] == 'BEKLIYOR':
                    durum_item.setForeground(QColor(brand.WARNING))
                    durum_item.setText("⏳ Bekleyen")
                elif row[3] == 'TAMAMLANDI':
                    durum_item.setForeground(QColor(brand.SUCCESS))
                    durum_item.setText("✅ Tamam")
                self.table.setItem(i, 3, durum_item)
                
                # Depo
                self.table.setItem(i, 4, QTableWidgetItem(row[4] or ''))
                
                # Miktar
                miktar_item = QTableWidgetItem(f"{row[5]:,.0f}" if row[5] else "")
                miktar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, 5, miktar_item)
                
                # Zaman
                zaman_str = row[6].strftime('%d.%m.%Y %H:%M') if row[6] else ''
                self.table.setItem(i, 6, QTableWidgetItem(zaman_str))
                
                # Bekleme Süresi
                if row[7] is not None:
                    sure_item = QTableWidgetItem(f"{row[7]}h")
                    if row[7] > 24:
                        sure_item.setForeground(QColor(brand.ERROR))
                    elif row[7] > 8:
                        sure_item.setForeground(QColor(brand.WARNING))
                    self.table.setItem(i, 7, sure_item)
                else:
                    self.table.setItem(i, 7, QTableWidgetItem("-"))
            
            # Footer güncelle
            self.footer_label.setText(f"Toplam {len(rows)} kayıt | Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Veri yükleme hatası:\n{str(e)}")
            print(f"Event log yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _format_event_tipi(self, tip: str) -> str:
        """Event tipini güzel formatta göster"""
        formatlar = {
            'GIRIS_KONTROL_GEREKLI': '🔍 Giriş Kontrol Gerekli',
            'FINAL_KONTROL_GEREKLI': '✅ Final Kontrol Gerekli',
            'URETIM_HAZIR': '⚙️ Üretime Hazır',
            'SEVK_HAZIR': '🚚 Sevk Hazır',
            'RED_KARAR_GEREKLI': '❌ Red Karar Gerekli',
        }
        return formatlar.get(tip, tip or '')
    
    def _temizle_eski(self):
        """30 günden eski kayıtları temizle"""
        reply = QMessageBox.question(
            self,
            "Onay",
            "30 günden eski event kayıtları silinecek.\nEmin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM stok.hareket_event_log
                    WHERE event_zamani < DATEADD(DAY, -30, GETDATE())
                      AND event_durumu = 'TAMAMLANDI'
                """)
                
                silinen = cursor.rowcount
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Başarılı", f"{silinen} eski kayıt temizlendi.")
                self._load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Temizleme hatası:\n{str(e)}")
