# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - PDKS Servis Kontrol Sayfası
Otomatik okuma servisini başlatma/durdurma ve izleme
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QGridLayout, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.pdks_reader_service import get_pdks_service, is_service_running


class PDKSServiceControlPage(BasePage):
    """PDKS Servis Kontrol Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.service = get_pdks_service()
        self._setup_ui()
        self._connect_signals()
        self._load_data()
        
        # Auto refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._update_status)
        self.refresh_timer.timeout.connect(self._load_data)
        self.refresh_timer.start(5000)  # 5 saniyede bir
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🤖 PDKS Otomatik Okuma Servisi")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {self.theme.get('text')};")
        header.addWidget(title)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Servis Durumu Kartı
        status_card = QFrame()
        status_card.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card')};
                border: 2px solid {self.theme.get('primary')};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        status_layout = QVBoxLayout(status_card)
        status_layout.setSpacing(16)
        
        # Durum başlığı
        status_title = QLabel("📊 Servis Durumu")
        status_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        status_layout.addWidget(status_title)
        
        # Durum göstergesi
        status_row = QHBoxLayout()
        
        self.status_indicator = QLabel("🔴")
        self.status_indicator.setStyleSheet("font-size: 48px;")
        status_row.addWidget(self.status_indicator)
        
        status_info = QVBoxLayout()
        self.status_label = QLabel("Servis Durdu")
        self.status_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        status_info.addWidget(self.status_label)
        
        self.status_detail = QLabel("Otomatik okuma yapılmıyor")
        self.status_detail.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 14px;")
        status_info.addWidget(self.status_detail)
        
        status_row.addLayout(status_info)
        status_row.addStretch()
        
        status_layout.addLayout(status_row)
        
        # Kontrol butonları
        btn_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶️ Servisi Başlat")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #16a34a; }}
            QPushButton:disabled {{ background: #6b7280; }}
        """)
        self.btn_start.clicked.connect(self._start_service)
        btn_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏸️ Servisi Durdur")
        self.btn_stop.setFixedHeight(50)
        self.btn_stop.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('danger')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #dc2626; }}
            QPushButton:disabled {{ background: #6b7280; }}
        """)
        self.btn_stop.clicked.connect(self._stop_service)
        btn_layout.addWidget(self.btn_stop)
        
        self.btn_read_all = QPushButton("🔄 Tüm Cihazları Oku")
        self.btn_read_all.setFixedHeight(50)
        self.btn_read_all.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('info')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #0284c7; }}
        """)
        self.btn_read_all.clicked.connect(self._read_all_devices)
        btn_layout.addWidget(self.btn_read_all)
        
        status_layout.addLayout(btn_layout)
        
        # Bilgi
        info_text = QLabel(
            "ℹ️ Servis aktif olduğunda, tüm aktif PDKS cihazları belirli periyotlarla "
            "otomatik olarak okunur. Manuel okuma servis durumundan bağımsızdır."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 13px; padding: 12px;")
        status_layout.addWidget(info_text)
        
        layout.addWidget(status_card)
        
        # İstatistikler
        stats_group = QGroupBox("📊 Cihaz İstatistikleri")
        stats_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: bold;
                color: {self.theme.get('text')};
                border: 2px solid {self.theme.get('border')};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """)
        stats_layout = QVBoxLayout(stats_group)
        
        # Tablo
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(8)
        self.stats_table.setHorizontalHeaderLabels([
            "Cihaz", "Durum", "Son Okuma", "Toplam", "Başarılı", "Başarı %", 
            "Son Kayıt", "Hata Mesajı"
        ])
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary')};
                font-weight: bold;
            }}
        """)
        
        header = self.stats_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        
        stats_layout.addWidget(self.stats_table)
        layout.addWidget(stats_group)
        
        # Son Okuma Logları
        logs_group = QGroupBox("📝 Son Okuma Logları")
        logs_group.setStyleSheet(stats_group.styleSheet())
        logs_layout = QVBoxLayout(logs_group)
        
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(7)
        self.logs_table.setHorizontalHeaderLabels([
            "Zaman", "Cihaz", "Tip", "Toplam Kayıt", "Yeni Kayıt", "Durum", "Hata"
        ])
        self.logs_table.verticalHeader().setVisible(False)
        self.logs_table.setStyleSheet(self.stats_table.styleSheet())
        self.logs_table.setMaximumHeight(200)
        
        header = self.logs_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        
        logs_layout.addWidget(self.logs_table)
        layout.addWidget(logs_group)

        # Turnike Durumu
        turnike_group = QGroupBox("🚪 Turnike Sistemi")
        turnike_group.setStyleSheet(stats_group.styleSheet())
        turnike_layout = QVBoxLayout(turnike_group)

        # Turnike durum satırı
        turnike_status_row = QHBoxLayout()
        self.turnike_indicator = QLabel("⚫")
        self.turnike_indicator.setStyleSheet("font-size: 28px;")
        turnike_status_row.addWidget(self.turnike_indicator)

        turnike_info = QVBoxLayout()
        self.turnike_label = QLabel("Turnike Durumu Kontrol Ediliyor...")
        self.turnike_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme.get('text')};")
        turnike_info.addWidget(self.turnike_label)

        self.turnike_detail = QLabel("")
        self.turnike_detail.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 13px;")
        turnike_info.addWidget(self.turnike_detail)

        turnike_status_row.addLayout(turnike_info)
        turnike_status_row.addStretch()
        turnike_layout.addLayout(turnike_status_row)

        # Son turnike geçişleri tablosu
        self.turnike_table = QTableWidget()
        self.turnike_table.setColumnCount(4)
        self.turnike_table.setHorizontalHeaderLabels(["Zaman", "Personel", "Kart No", "Yon"])
        self.turnike_table.verticalHeader().setVisible(False)
        self.turnike_table.setStyleSheet(self.stats_table.styleSheet())
        self.turnike_table.setMaximumHeight(200)

        t_header = self.turnike_table.horizontalHeader()
        t_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t_header.setSectionResizeMode(1, QHeaderView.Stretch)
        t_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        t_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        turnike_layout.addWidget(self.turnike_table)
        layout.addWidget(turnike_group)
    
    def _connect_signals(self):
        """Servis signal'lerini bağla"""
        self.service.service_started.connect(self._on_service_started)
        self.service.service_stopped.connect(self._on_service_stopped)
        self.service.device_read_completed.connect(self._on_device_read_completed)
        self.service.device_read_failed.connect(self._on_device_read_failed)
        self.service.device_status_changed.connect(self._on_device_status_changed)
    
    def _update_status(self):
        """Servis durumunu güncelle"""
        running = is_service_running()
        
        if running:
            self.status_indicator.setText("🟢")
            self.status_label.setText("Servis Çalışıyor")
            self.status_detail.setText("Cihazlar otomatik olarak okunuyor")
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
        else:
            self.status_indicator.setText("🔴")
            self.status_label.setText("Servis Durdu")
            self.status_detail.setText("Otomatik okuma yapılmıyor")
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
    
    def _load_data(self):
        """Cihaz istatistiklerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Cihaz istatistikleri
            cursor.execute("""
                SELECT
                    cihaz_adi, durum, son_okuma_zamani,
                    toplam_okuma, basarili_okuma, son_kayit_sayisi, hata_mesaji
                FROM ik.pdks_cihazlari
                WHERE aktif_mi = 1 AND cihaz_tipi = 'ZK'
                ORDER BY cihaz_kodu
            """)
            
            stats = cursor.fetchall()
            self.stats_table.setRowCount(len(stats))
            
            for i, row in enumerate(stats):
                self.stats_table.setItem(i, 0, QTableWidgetItem(row[0] or ""))
                
                # Durum
                durum = row[1] or "PASIF"
                durum_item = QTableWidgetItem(durum)
                durum_colors = {
                    'AKTIF': self.theme.get('success'),
                    'BAGLI': self.theme.get('info'),
                    'HATA': self.theme.get('danger'),
                    'PASIF': self.theme.get('text_muted')
                }
                durum_item.setForeground(QColor(durum_colors.get(durum, self.theme.get('text_muted'))))
                self.stats_table.setItem(i, 1, durum_item)
                
                # Son okuma
                son_okuma = row[2].strftime('%d.%m %H:%M') if row[2] else '-'
                self.stats_table.setItem(i, 2, QTableWidgetItem(son_okuma))
                
                # Sayılar
                toplam = row[3] or 0
                basarili = row[4] or 0
                basari_yuzde = (basarili / toplam * 100) if toplam > 0 else 0
                
                self.stats_table.setItem(i, 3, QTableWidgetItem(str(toplam)))
                self.stats_table.setItem(i, 4, QTableWidgetItem(str(basarili)))
                self.stats_table.setItem(i, 5, QTableWidgetItem(f"{basari_yuzde:.1f}%"))
                self.stats_table.setItem(i, 6, QTableWidgetItem(str(row[5] or 0)))
                self.stats_table.setItem(i, 7, QTableWidgetItem(row[6] or "-"))
            
            # Son loglar
            cursor.execute("""
                SELECT TOP 20
                    l.okuma_zamani, c.cihaz_adi, l.okuma_tipi,
                    l.kayit_sayisi, l.yeni_kayit_sayisi, l.basarili, l.hata_mesaji
                FROM ik.pdks_okuma_loglari l
                INNER JOIN ik.pdks_cihazlari c ON l.cihaz_id = c.id
                ORDER BY l.okuma_zamani DESC
            """)
            
            logs = cursor.fetchall()
            self.logs_table.setRowCount(len(logs))
            
            for i, row in enumerate(logs):
                zaman = row[0].strftime('%d.%m %H:%M:%S') if row[0] else '-'
                self.logs_table.setItem(i, 0, QTableWidgetItem(zaman))
                self.logs_table.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                self.logs_table.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.logs_table.setItem(i, 3, QTableWidgetItem(str(row[3] or 0)))
                self.logs_table.setItem(i, 4, QTableWidgetItem(str(row[4] or 0)))
                
                # Durum
                basarili = row[5]
                durum_item = QTableWidgetItem("✓ Başarılı" if basarili else "✗ Hata")
                durum_item.setForeground(QColor(
                    self.theme.get('success') if basarili else self.theme.get('danger')
                ))
                self.logs_table.setItem(i, 5, durum_item)
                
                self.logs_table.setItem(i, 6, QTableWidgetItem(row[6] or "-"))
            
            # Turnike durumu ve son geçişler
            cursor = conn.cursor()
            cursor.execute("""
                SELECT durum, son_okuma_zamani
                FROM ik.pdks_cihazlari
                WHERE cihaz_tipi = 'TURNIKE' AND aktif_mi = 1
            """)
            turnike_row = cursor.fetchone()

            if turnike_row:
                durum = turnike_row[0] or "PASIF"
                son = turnike_row[1]

                # Son 5 dakika içinde geçiş var mı? (canlı kontrolü)
                cursor.execute("""
                    SELECT COUNT(*) FROM ik.pdks_hareketler h
                    JOIN ik.pdks_cihazlari c ON c.id = h.cihaz_id
                    WHERE c.cihaz_tipi = 'TURNIKE'
                      AND h.hareket_zamani >= DATEADD(MINUTE, -5, GETDATE())
                """)
                son5dk = cursor.fetchone()[0]

                if son5dk > 0:
                    self.turnike_indicator.setText("🟢")
                    self.turnike_label.setText("Turnike Aktif - Canlı")
                    self.turnike_detail.setText(f"Son 5 dakikada {son5dk} gecis")
                else:
                    self.turnike_indicator.setText("🟡")
                    self.turnike_label.setText("Turnike Bagli - Bekleniyor")
                    self.turnike_detail.setText("Son 5 dakikada gecis yok")
            else:
                self.turnike_indicator.setText("🔴")
                self.turnike_label.setText("Turnike Tanimli Degil")
                self.turnike_detail.setText("Henuz turnike cihazi kaydedilmemis")

            # Son 20 turnike geçişi
            cursor.execute("""
                SELECT TOP 20
                    h.hareket_zamani, h.personel_adi_soyadi, h.kart_no, h.hareket_tipi
                FROM ik.pdks_hareketler h
                JOIN ik.pdks_cihazlari c ON c.id = h.cihaz_id
                WHERE c.cihaz_tipi = 'TURNIKE'
                ORDER BY h.hareket_zamani DESC
            """)
            gecisler = cursor.fetchall()
            self.turnike_table.setRowCount(len(gecisler))

            for i, row in enumerate(gecisler):
                zaman = row[0].strftime('%d.%m %H:%M:%S') if row[0] else '-'
                self.turnike_table.setItem(i, 0, QTableWidgetItem(zaman))
                self.turnike_table.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                self.turnike_table.setItem(i, 2, QTableWidgetItem(row[2] or ""))

                yon_item = QTableWidgetItem(row[3] or "")
                if row[3] == "GIRIS":
                    yon_item.setForeground(QColor(self.theme.get('success', '#22c55e')))
                else:
                    yon_item.setForeground(QColor(self.theme.get('warning', '#f59e0b')))
                self.turnike_table.setItem(i, 3, yon_item)

            conn.close()

        except Exception as e:
            print(f"Veri yükleme hatası: {e}")

    def _start_service(self):
        """Servisi başlat"""
        try:
            self.service.start_service()
            QMessageBox.information(self, "Başarılı", 
                "PDKS okuma servisi başlatıldı.\n"
                "Cihazlar otomatik olarak okunmaya başlayacak."
            )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Servis başlatma hatası:\n{e}")
    
    def _stop_service(self):
        """Servisi durdur"""
        reply = QMessageBox.question(
            self, "Onay",
            "PDKS okuma servisini durdurmak istediğinize emin misiniz?\n\n"
            "Otomatik okuma işlemi duracak.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.service.stop_service()
                QMessageBox.information(self, "Başarılı", "PDKS okuma servisi durduruldu.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Servis durdurma hatası:\n{e}")
    
    def _read_all_devices(self):
        """Tüm cihazları manuel oku"""
        try:
            self.service.read_all_devices(manual=True)
            QMessageBox.information(self, "Bilgi", 
                "Tüm aktif cihazlar için manuel okuma başlatıldı.\n"
                "İşlem tamamlandığında tablo otomatik güncellenecek."
            )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Manuel okuma hatası:\n{e}")
    
    def _on_service_started(self):
        """Servis başladı"""
        self._update_status()
    
    def _on_service_stopped(self):
        """Servis durdu"""
        self._update_status()
    
    def _on_device_read_completed(self, cihaz_id: int, toplam: int, yeni: int):
        """Cihaz okuma tamamlandı"""
        self._load_data()
    
    def _on_device_read_failed(self, cihaz_id: int, hata: str):
        """Cihaz okuma başarısız"""
        self._load_data()
    
    def _on_device_status_changed(self, cihaz_id: int, durum: str, mesaj: str):
        """Cihaz durumu değişti"""
        self._load_data()
