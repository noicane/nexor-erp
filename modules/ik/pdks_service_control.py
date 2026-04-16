# -*- coding: utf-8 -*-
"""
NEXOR ERP - PDKS Servis Kontrol Sayfasi
=========================================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
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
from core.nexor_brand import brand
try:
    from core.pdks_reader_service import get_pdks_service, is_service_running
    ZK_SERVICE_AVAILABLE = True
except ImportError:
    ZK_SERVICE_AVAILABLE = False
    def get_pdks_service(): return None
    def is_service_running(): return False


class PDKSServiceControlPage(BasePage):
    """PDKS Servis Kontrol Sayfasi — el kitabi uyumlu"""

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
        self.refresh_timer.start(5000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # Header
        header = self.create_page_header(
            "PDKS Otomatik Okuma Servisi",
            "Servis baslatma/durdurma ve izleme"
        )
        layout.addLayout(header)

        # Servis Durumu Karti
        status_card = QFrame()
        status_card.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 2px solid {brand.PRIMARY};
                border-radius: {brand.R_LG}px;
            }}
        """)
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(brand.SP_6, brand.SP_5, brand.SP_6, brand.SP_5)
        status_layout.setSpacing(brand.SP_4)

        # Durum basligi
        status_title = QLabel("Servis Durumu")
        status_title.setStyleSheet(
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"color: {brand.PRIMARY};"
        )
        status_layout.addWidget(status_title)

        # Durum gostergesi
        status_row = QHBoxLayout()

        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(brand.sp(24), brand.sp(24))
        self.status_indicator.setStyleSheet(f"""
            background: {brand.ERROR};
            border-radius: {brand.sp(12)}px;
        """)
        status_row.addWidget(self.status_indicator)

        status_info = QVBoxLayout()
        self.status_label = QLabel("Servis Durdu")
        self.status_label.setStyleSheet(
            f"font-size: {brand.FS_HEADING_LG}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"color: {brand.TEXT};"
        )
        status_info.addWidget(self.status_label)

        self.status_detail = QLabel("Otomatik okuma yapilmiyor")
        self.status_detail.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_LG}px;"
        )
        status_info.addWidget(self.status_detail)

        status_row.addLayout(status_info)
        status_row.addStretch()

        status_layout.addLayout(status_row)

        # Kontrol butonlari
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)

        self.btn_start = QPushButton("Servisi Baslat")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFixedHeight(brand.sp(38))
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #059669; }}
            QPushButton:disabled {{ background: {brand.BG_HOVER}; color: {brand.TEXT_DISABLED}; }}
        """)
        self.btn_start.clicked.connect(self._start_service)
        btn_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Servisi Durdur")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setFixedHeight(brand.sp(38))
        self.btn_stop.setStyleSheet(f"""
            QPushButton {{
                background: {brand.ERROR};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #DC2626; }}
            QPushButton:disabled {{ background: {brand.BG_HOVER}; color: {brand.TEXT_DISABLED}; }}
        """)
        self.btn_stop.clicked.connect(self._stop_service)
        btn_layout.addWidget(self.btn_stop)

        self.btn_read_all = QPushButton("Tum Cihazlari Oku")
        self.btn_read_all.setCursor(Qt.PointingHandCursor)
        self.btn_read_all.setFixedHeight(brand.sp(38))
        self.btn_read_all.setStyleSheet(f"""
            QPushButton {{
                background: {brand.INFO};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #2563EB; }}
        """)
        self.btn_read_all.clicked.connect(self._read_all_devices)
        btn_layout.addWidget(self.btn_read_all)

        status_layout.addLayout(btn_layout)

        # Bilgi
        info_text = QLabel(
            "Servis aktif oldugunda, tum aktif PDKS cihazlari belirli periyotlarla "
            "otomatik olarak okunur. Manuel okuma servis durumundan bagimsizdir."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY}px; "
            f"padding: {brand.SP_3}px;"
        )
        status_layout.addWidget(info_text)

        layout.addWidget(status_card)

        # --- GroupBox ortak stili ---
        grp_css = f"""
            QGroupBox {{
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                margin-top: {brand.SP_5}px;
                padding: {brand.SP_5}px;
                padding-top: {brand.SP_8}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {brand.SP_4}px;
                top: {brand.SP_2}px;
                padding: 0 {brand.SP_2}px;
                color: {brand.TEXT_MUTED};
                background: transparent;
            }}
        """

        # --- Tablo ortak stili ---
        tbl_css = f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_2}px {brand.SP_3}px;
                border-bottom: 1px solid {brand.BORDER};
                color: {brand.TEXT};
            }}
            QTableWidget::item:alternate {{ background: {brand.BG_MAIN}; }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """

        # Istatistikler
        stats_group = QGroupBox("Cihaz Istatistikleri")
        stats_group.setStyleSheet(grp_css)
        stats_layout_g = QVBoxLayout(stats_group)

        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(8)
        self.stats_table.setHorizontalHeaderLabels([
            "Cihaz", "Durum", "Son Okuma", "Toplam", "Basarili", "Basari %",
            "Son Kayit", "Hata Mesaji"
        ])
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.setShowGrid(False)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.stats_table.setStyleSheet(tbl_css)

        sh = self.stats_table.horizontalHeader()
        sh.setSectionResizeMode(0, QHeaderView.Stretch)
        sh.setSectionResizeMode(7, QHeaderView.Stretch)

        stats_layout_g.addWidget(self.stats_table)
        layout.addWidget(stats_group)

        # Son Okuma Loglari
        logs_group = QGroupBox("Son Okuma Loglari")
        logs_group.setStyleSheet(grp_css)
        logs_layout = QVBoxLayout(logs_group)

        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(7)
        self.logs_table.setHorizontalHeaderLabels([
            "Zaman", "Cihaz", "Tip", "Toplam Kayit", "Yeni Kayit", "Durum", "Hata"
        ])
        self.logs_table.verticalHeader().setVisible(False)
        self.logs_table.setShowGrid(False)
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.logs_table.setStyleSheet(tbl_css)
        self.logs_table.setMaximumHeight(brand.sp(200))

        lh = self.logs_table.horizontalHeader()
        lh.setSectionResizeMode(1, QHeaderView.Stretch)
        lh.setSectionResizeMode(6, QHeaderView.Stretch)

        logs_layout.addWidget(self.logs_table)
        layout.addWidget(logs_group)

        # Turnike Durumu
        turnike_group = QGroupBox("Turnike Sistemi")
        turnike_group.setStyleSheet(grp_css)
        turnike_layout = QVBoxLayout(turnike_group)

        # Turnike durum satiri
        turnike_status_row = QHBoxLayout()

        self.turnike_indicator = QLabel()
        self.turnike_indicator.setFixedSize(brand.sp(16), brand.sp(16))
        self.turnike_indicator.setStyleSheet(f"""
            background: {brand.TEXT_DIM};
            border-radius: {brand.sp(8)}px;
        """)
        turnike_status_row.addWidget(self.turnike_indicator)

        turnike_info = QVBoxLayout()
        self.turnike_label = QLabel("Turnike Durumu Kontrol Ediliyor...")
        self.turnike_label.setStyleSheet(
            f"font-size: {brand.FS_HEADING_SM}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"color: {brand.TEXT};"
        )
        turnike_info.addWidget(self.turnike_label)

        self.turnike_detail = QLabel("")
        self.turnike_detail.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px;"
        )
        turnike_info.addWidget(self.turnike_detail)

        turnike_status_row.addLayout(turnike_info)
        turnike_status_row.addStretch()

        # Turnike kontrol butonlari
        self.btn_turnike_servis = QPushButton("Servis Yeniden Baslat")
        self.btn_turnike_servis.setCursor(Qt.PointingHandCursor)
        self.btn_turnike_servis.setFixedHeight(brand.sp(38))
        self.btn_turnike_servis.setStyleSheet(f"""
            QPushButton {{
                background: {brand.WARNING};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QPushButton:hover {{ background: #D97706; }}
        """)
        self.btn_turnike_servis.clicked.connect(self._turnike_servis_restart)
        turnike_status_row.addWidget(self.btn_turnike_servis)

        self.btn_turnike_durdur = QPushButton("Servis Durdur")
        self.btn_turnike_durdur.setCursor(Qt.PointingHandCursor)
        self.btn_turnike_durdur.setFixedHeight(brand.sp(38))
        self.btn_turnike_durdur.setStyleSheet(f"""
            QPushButton {{
                background: {brand.ERROR};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QPushButton:hover {{ background: #DC2626; }}
        """)
        self.btn_turnike_durdur.clicked.connect(self._turnike_servis_durdur)
        turnike_status_row.addWidget(self.btn_turnike_durdur)

        turnike_layout.addLayout(turnike_status_row)

        # Son turnike gecisleri tablosu
        self.turnike_table = QTableWidget()
        self.turnike_table.setColumnCount(4)
        self.turnike_table.setHorizontalHeaderLabels(["Zaman", "Personel", "Kart No", "Yon"])
        self.turnike_table.verticalHeader().setVisible(False)
        self.turnike_table.setShowGrid(False)
        self.turnike_table.setAlternatingRowColors(True)
        self.turnike_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.turnike_table.setStyleSheet(tbl_css)
        self.turnike_table.setMaximumHeight(brand.sp(200))

        t_header = self.turnike_table.horizontalHeader()
        t_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t_header.setSectionResizeMode(1, QHeaderView.Stretch)
        t_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        t_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        turnike_layout.addWidget(self.turnike_table)
        layout.addWidget(turnike_group)

    def _connect_signals(self):
        """Servis signal'lerini bagla"""
        if not self.service:
            return
        self.service.service_started.connect(self._on_service_started)
        self.service.service_stopped.connect(self._on_service_stopped)
        self.service.device_read_completed.connect(self._on_device_read_completed)
        self.service.device_read_failed.connect(self._on_device_read_failed)
        self.service.device_status_changed.connect(self._on_device_status_changed)

    def _update_status(self):
        """Servis durumunu guncelle"""
        running = is_service_running()

        if running:
            self.status_indicator.setStyleSheet(f"""
                background: {brand.SUCCESS};
                border-radius: {brand.sp(12)}px;
            """)
            self.status_label.setText("Servis Calisiyor")
            self.status_detail.setText("Cihazlar otomatik olarak okunuyor")
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
        else:
            self.status_indicator.setStyleSheet(f"""
                background: {brand.ERROR};
                border-radius: {brand.sp(12)}px;
            """)
            self.status_label.setText("Servis Durdu")
            self.status_detail.setText("Otomatik okuma yapilmiyor")
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)

    def _load_data(self):
        """Cihaz istatistiklerini yukle"""
        conn = None
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
                    'AKTIF': brand.SUCCESS,
                    'BAGLI': brand.INFO,
                    'HATA': brand.ERROR,
                    'PASIF': brand.TEXT_MUTED
                }
                durum_item.setForeground(QColor(durum_colors.get(durum, brand.TEXT_MUTED)))
                self.stats_table.setItem(i, 1, durum_item)

                # Son okuma
                son_okuma = row[2].strftime('%d.%m %H:%M') if row[2] else '-'
                self.stats_table.setItem(i, 2, QTableWidgetItem(son_okuma))

                # Sayilar
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
                basarili_mi = row[5]
                durum_item = QTableWidgetItem("Basarili" if basarili_mi else "Hata")
                durum_item.setForeground(QColor(
                    brand.SUCCESS if basarili_mi else brand.ERROR
                ))
                self.logs_table.setItem(i, 5, durum_item)

                self.logs_table.setItem(i, 6, QTableWidgetItem(row[6] or "-"))

            # Turnike durumu
            cursor.execute("""
                SELECT COUNT(*) FROM ik.pdks_hareketler h
                JOIN ik.pdks_cihazlari c ON c.id = h.cihaz_id
                WHERE c.cihaz_tipi = 'TURNIKE'
                  AND h.hareket_zamani >= DATEADD(MINUTE, -5, GETDATE())
            """)
            son5dk = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM ik.pdks_hareketler h
                JOIN ik.pdks_cihazlari c ON c.id = h.cihaz_id
                WHERE c.cihaz_tipi = 'TURNIKE'
                  AND CAST(h.hareket_zamani AS DATE) = CAST(GETDATE() AS DATE)
            """)
            bugun_toplam = cursor.fetchone()[0]

            if son5dk > 0:
                self.turnike_indicator.setStyleSheet(f"""
                    background: {brand.SUCCESS};
                    border-radius: {brand.sp(8)}px;
                """)
                self.turnike_label.setText("Turnike Aktif - Canli")
                self.turnike_detail.setText(f"Son 5dk: {son5dk} gecis | Bugun toplam: {bugun_toplam}")
            elif bugun_toplam > 0:
                self.turnike_indicator.setStyleSheet(f"""
                    background: {brand.WARNING};
                    border-radius: {brand.sp(8)}px;
                """)
                self.turnike_label.setText("Turnike Bagli - Bekleniyor")
                self.turnike_detail.setText(f"Bugun toplam: {bugun_toplam} gecis")
            else:
                self.turnike_indicator.setStyleSheet(f"""
                    background: {brand.ERROR};
                    border-radius: {brand.sp(8)}px;
                """)
                self.turnike_label.setText("Turnike - Gecis Yok")
                self.turnike_detail.setText("Bugun henuz gecis kaydedilmedi")

            # Son 20 turnike gecisi
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
                    yon_item.setForeground(QColor(brand.SUCCESS))
                else:
                    yon_item.setForeground(QColor(brand.WARNING))
                self.turnike_table.setItem(i, 3, yon_item)

        except Exception as e:
            print(f"[pdks_service] Veri yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _start_service(self):
        """Servisi baslat"""
        try:
            self.service.start_service()
            QMessageBox.information(self, "Basarili",
                "PDKS okuma servisi baslatildi.\n"
                "Cihazlar otomatik olarak okunmaya baslayacak."
            )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Servis baslatma hatasi:\n{e}")

    def _stop_service(self):
        """Servisi durdur"""
        reply = QMessageBox.question(
            self, "Onay",
            "PDKS okuma servisini durdurmak istediginize emin misiniz?\n\n"
            "Otomatik okuma islemi duracak.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.service.stop_service()
                QMessageBox.information(self, "Basarili", "PDKS okuma servisi durduruldu.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Servis durdurma hatasi:\n{e}")

    def _read_all_devices(self):
        """Tum cihazlari manuel oku"""
        try:
            self.service.read_all_devices(manual=True)
            QMessageBox.information(self, "Bilgi",
                "Tum aktif cihazlar icin manuel okuma baslatildi.\n"
                "Islem tamamlandiginda tablo otomatik guncellenecek."
            )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Manuel okuma hatasi:\n{e}")

    def _on_service_started(self):
        self._update_status()

    def _on_service_stopped(self):
        self._update_status()

    def _on_device_read_completed(self, cihaz_id: int, toplam: int, yeni: int):
        self._load_data()

    def _on_device_read_failed(self, cihaz_id: int, hata: str):
        self._load_data()

    def _on_device_status_changed(self, cihaz_id: int, durum: str, mesaj: str):
        self._load_data()

    # ===== TURNIKE KONTROL =====

    def _turnike_servis_restart(self):
        """Turnike servisini yeniden baslat"""
        import threading as th
        from core.turnike_kontrol import servis_yeniden_baslat
        self.turnike_detail.setText("Servis yeniden baslatiliyor...")

        def _exec():
            ok, msg = servis_yeniden_baslat()
            result = "Servis yeniden baslatildi" if ok else msg
            QTimer.singleShot(0, lambda: self._turnike_sonuc(result))
        th.Thread(target=_exec, daemon=True).start()

    def _turnike_servis_durdur(self):
        """Turnike servisini durdur"""
        reply = QMessageBox.question(self, "Onay",
            "Turnike servisini durdurmak istediginize emin misiniz?\n"
            "Kart okuma ve gecis islemleri duracak!",
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        import threading as th
        from core.turnike_kontrol import servis_durdur
        self.turnike_detail.setText("Servis durduruluyor...")

        def _exec():
            ok, msg = servis_durdur()
            result = "Servis durduruldu" if ok else msg
            QTimer.singleShot(0, lambda: self._turnike_sonuc(result))
        th.Thread(target=_exec, daemon=True).start()

    def _turnike_sonuc(self, msg: str):
        """Turnike islem sonucu (UI thread)"""
        self.turnike_detail.setText(msg)
        self._load_data()
