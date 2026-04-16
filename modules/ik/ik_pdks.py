# -*- coding: utf-8 -*-
"""
NEXOR ERP - IK PDKS Canli Monitor
===================================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QWidget, QGridLayout, QMessageBox, QDialog,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QColor, QPixmap, QPainter, QBrush, QFont

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class PersonelChip(QFrame):
    """Kompakt personel karti - chip gorunumu"""

    def __init__(self, data: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.theme = theme
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(brand.sp(200), brand.sp(44))
        self.setStyleSheet(f"""
            PersonelChip {{
                background: rgba(34, 197, 94, 0.08);
                border: 1px solid rgba(34, 197, 94, 0.3);
                border-radius: {brand.sp(22)}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(brand.SP_1, brand.SP_1, brand.SP_3, brand.SP_1)
        layout.setSpacing(brand.SP_2)

        # Avatar
        avatar = QLabel()
        avatar.setFixedSize(brand.sp(36), brand.sp(36))
        avatar.setAlignment(Qt.AlignCenter)

        name = self.data.get('name', '?')
        initials = ''.join([n[0] for n in name.split()[:2]]).upper()
        avatar.setText(initials)
        avatar.setStyleSheet(f"""
            background: #22c55e;
            color: white;
            border-radius: {brand.sp(18)}px;
            font-weight: {brand.FW_BOLD};
            font-size: {brand.FS_CAPTION}px;
        """)
        layout.addWidget(avatar)

        # Isim + saat
        info = QVBoxLayout()
        info.setSpacing(0)
        info.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(name)
        name_label.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-weight: {brand.FW_BOLD}; "
            f"font-size: {brand.FS_CAPTION}px;"
        )
        info.addWidget(name_label)

        time_label = QLabel(self.data.get('time', '--:--'))
        time_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.fs(10)}px;"
        )
        info.addWidget(time_label)

        layout.addLayout(info, 1)


class IKPdksPage(BasePage):
    """IK PDKS Canli Monitor Sayfasi — el kitabi uyumlu"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()

        # Otomatik yenileme
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_data)
        self.refresh_timer.start(3000)

        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # Header
        header = self.create_page_header(
            "PDKS Canli Monitor",
            "Anlik personel giris/cikis takibi"
        )

        # Canli gosterge
        self.live_indicator = QLabel("CANLI")
        self.live_indicator.setStyleSheet(f"""
            color: {brand.ERROR};
            font-weight: {brand.FW_BOLD};
            font-size: {brand.FS_BODY_SM}px;
            padding: {brand.SP_1}px {brand.SP_3}px;
            background: {brand.ERROR_SOFT};
            border-radius: {brand.R_SM}px;
        """)
        header.addWidget(self.live_indicator)

        # Saat
        self.time_label = QLabel()
        self.time_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_LG}px;"
        )
        header.addWidget(self.time_label)

        # Saat timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        # Yenile butonu
        refresh_btn = self.create_primary_button("Yenile")
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)

        # Hareketler butonu
        movements_btn = QPushButton("Hareketler")
        movements_btn.setCursor(Qt.PointingHandCursor)
        movements_btn.setFixedHeight(brand.sp(38))
        movements_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
        """)
        movements_btn.clicked.connect(self._show_movements)
        header.addWidget(movements_btn)

        layout.addLayout(header)

        # KPI kartlari
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self.kart_toplam = self.create_stat_card("PLANLANAN", "0", color=brand.PRIMARY)
        kpi_row.addWidget(self.kart_toplam)

        self.kart_iceride = self.create_stat_card("ICERIDE", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self.kart_iceride)

        self.kart_gelmedi = self.create_stat_card("GELMEDI", "0", color=brand.ERROR)
        kpi_row.addWidget(self.kart_gelmedi)

        self.kart_izinli = self.create_stat_card("IZINLI", "0", color=brand.WARNING)
        kpi_row.addWidget(self.kart_izinli)

        self.kart_vardiya = self.create_stat_card("VARDIYA DAGILIMI", "-", color=brand.INFO)
        kpi_row.addWidget(self.kart_vardiya)

        kpi_row.addStretch()
        layout.addLayout(kpi_row)

        # Pozisyon bazli dikey akis alani
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                width: {brand.SP_2}px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {brand.BORDER};
                border-radius: {brand.SP_1}px;
            }}
        """)

        self.content_container = QWidget()
        self.content_container.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setSpacing(brand.SP_4)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll.setWidget(self.content_container)
        layout.addWidget(self.scroll, 1)

    def _update_clock(self):
        """Saati guncelle"""
        now = datetime.now()
        self.time_label.setText(now.strftime("%d.%m.%Y %H:%M:%S"))

        # Canli gosterge animasyonu
        if now.second % 2 == 0:
            self.live_indicator.setStyleSheet(f"""
                color: {brand.ERROR};
                font-weight: {brand.FW_BOLD};
                font-size: {brand.FS_BODY_SM}px;
                padding: {brand.SP_1}px {brand.SP_3}px;
                background: {brand.ERROR_SOFT};
                border-radius: {brand.R_SM}px;
            """)
        else:
            self.live_indicator.setStyleSheet(f"""
                color: {brand.TEXT_DIM};
                font-weight: {brand.FW_BOLD};
                font-size: {brand.FS_BODY_SM}px;
                padding: {brand.SP_1}px {brand.SP_3}px;
                background: transparent;
                border-radius: {brand.R_SM}px;
            """)

    def _load_data(self):
        """PDKS verilerini yukle - Turnike tabanli"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            today = date.today()

            # Tum aktif personelleri al
            cursor.execute("""
                SELECT
                    p.id, p.sicil_no, p.ad, p.soyad,
                    ISNULL(poz.ad, 'Tanimsiz') as pozisyon,
                    d.ad as departman
                FROM ik.personeller p
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                LEFT JOIN ik.pozisyonlar poz ON p.pozisyon_id = poz.id
                WHERE p.aktif_mi = 1
                ORDER BY poz.ad, p.ad
            """)

            employees = cursor.fetchall()

            # Izinli personelleri al
            cursor.execute("""
                SELECT personel_id FROM ik.izin_talepleri
                WHERE durum = 'ONAYLANDI'
                  AND ? BETWEEN baslangic_tarihi AND bitis_tarihi
            """, (today,))
            izinli_ids = set(row[0] for row in cursor.fetchall())

            # Bugunku son hareketleri turnike'den al
            cursor.execute("""
                SELECT h.personel_id,
                       MAX(h.hareket_zamani) as son_hareket,
                       (SELECT TOP 1 h2.hareket_tipi
                        FROM ik.pdks_hareketler h2
                        JOIN ik.pdks_cihazlari c2 ON h2.cihaz_id = c2.id AND c2.cihaz_tipi = 'TURNIKE'
                        WHERE h2.personel_id = h.personel_id
                          AND CAST(h2.hareket_zamani AS DATE) = ?
                        ORDER BY h2.hareket_zamani DESC) as son_tip,
                       MIN(CASE WHEN h.hareket_tipi = 'GIRIS' THEN h.hareket_zamani END) as ilk_giris
                FROM ik.pdks_hareketler h
                JOIN ik.pdks_cihazlari c ON h.cihaz_id = c.id AND c.cihaz_tipi = 'TURNIKE'
                WHERE CAST(h.hareket_zamani AS DATE) = ?
                GROUP BY h.personel_id
            """, (today, today))
            hareketler = {}
            for row in cursor.fetchall():
                hareketler[row[0]] = {
                    'son_hareket': row[1],
                    'son_tip': row[2],
                    'ilk_giris': row[3]
                }

            # Bugunku vardiya planini al
            cursor.execute("""
                SELECT vp.personel_id, v.kod, v.ad
                FROM ik.vardiya_planlama vp
                JOIN tanim.vardiyalar v ON vp.vardiya_id = v.id
                WHERE vp.tarih = ?
            """, (today,))
            vardiya_plan = {}
            vardiya_sayilari = {}
            for row in cursor.fetchall():
                vardiya_plan[row[0]] = {'kod': row[1], 'ad': row[2]}
                vardiya_sayilari[row[1]] = vardiya_sayilari.get(row[1], 0) + 1

            # Personelleri pozisyonlara gore grupla
            poz_map = {}
            gelmedi_list = []
            counts = {'toplam': 0, 'iceride': 0, 'gelmedi': 0, 'izinli': 0, 'planlanan': len(vardiya_plan), 'plan_gelmedi': 0}

            for emp in employees:
                emp_id = emp[0]
                pozisyon = emp[4] or 'Tanimsiz'

                hareket = hareketler.get(emp_id)

                # Durum belirleme
                if emp_id in izinli_ids:
                    status = 'LEAVE'
                    status_text = 'Izinli'
                    counts['izinli'] += 1
                elif hareket and hareket['son_tip'] == 'GIRIS':
                    status = 'IN'
                    status_text = 'Iceride'
                    counts['iceride'] += 1
                else:
                    status = 'OUT'
                    status_text = 'Disarida'
                    counts['gelmedi'] += 1

                counts['toplam'] += 1

                # Planlanan ama gelmeyen
                if emp_id in vardiya_plan and status == 'OUT':
                    counts['plan_gelmedi'] += 1
                    gelmedi_list.append({
                        'name': f"{emp[2]} {emp[3]}",
                        'pozisyon': pozisyon,
                        'vardiya': vardiya_plan[emp_id]['kod']
                    })

                # Sadece iceride olanlari kartlarda goster
                if status != 'IN':
                    continue

                time_str = '--:--'
                if hareket and hareket['son_hareket']:
                    time_str = hareket['son_hareket'].strftime('%H:%M')

                person_data = {
                    'id': emp_id,
                    'name': f"{emp[2]} {emp[3]}",
                    'status': status,
                    'status_text': status_text,
                    'time': time_str
                }

                if pozisyon not in poz_map:
                    poz_map[pozisyon] = []
                poz_map[pozisyon].append(person_data)

            # Kartlari guncelle
            self.kart_toplam.findChild(QLabel, "stat_value").setText(str(counts['planlanan']))
            self.kart_iceride.findChild(QLabel, "stat_value").setText(str(counts['iceride']))
            self.kart_gelmedi.findChild(QLabel, "stat_value").setText(str(counts['plan_gelmedi']))
            self.kart_izinli.findChild(QLabel, "stat_value").setText(str(counts['izinli']))

            # Vardiya ozeti
            vardiya_text = " | ".join([f"{k}:{v}" for k, v in sorted(vardiya_sayilari.items())])
            self.kart_vardiya.findChild(QLabel, "stat_value").setText(vardiya_text or "-")

            # Icerigi temizle ve yeniden olustur
            while self.content_layout.count():
                item = self.content_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Pozisyon bolumlerini ekle
            COLS = 5
            for poz_name in sorted(poz_map.keys()):
                persons = poz_map[poz_name]

                # Pozisyon basligi
                header_frame = QFrame()
                header_frame.setStyleSheet(f"""
                    QFrame {{
                        background: {brand.BG_CARD};
                        border: 1px solid {brand.BORDER};
                        border-left: {brand.SP_1}px solid {brand.PRIMARY};
                        border-radius: {brand.R_SM}px;
                    }}
                """)
                header_layout = QHBoxLayout(header_frame)
                header_layout.setContentsMargins(brand.SP_3, brand.SP_2, brand.SP_3, brand.SP_2)

                title = QLabel(poz_name.upper())
                title.setStyleSheet(
                    f"color: {brand.PRIMARY}; "
                    f"font-weight: {brand.FW_BOLD}; "
                    f"font-size: {brand.FS_BODY}px;"
                )
                header_layout.addWidget(title)

                header_layout.addStretch()

                badge = QLabel(str(len(persons)))
                badge.setStyleSheet(f"""
                    background: {brand.PRIMARY};
                    color: white;
                    padding: {brand.SP_1}px {brand.SP_3}px;
                    border-radius: {brand.R_SM}px;
                    font-size: {brand.FS_CAPTION}px;
                    font-weight: {brand.FW_BOLD};
                """)
                header_layout.addWidget(badge)

                self.content_layout.addWidget(header_frame)

                # Kartlari grid olarak yerlestir
                grid_widget = QWidget()
                grid_widget.setStyleSheet("background: transparent;")
                grid = QGridLayout(grid_widget)
                grid.setContentsMargins(0, 0, 0, 0)
                grid.setSpacing(brand.SP_2)

                for i, person in enumerate(persons):
                    chip = PersonelChip(person, self.theme)
                    grid.addWidget(chip, i // COLS, i % COLS)

                self.content_layout.addWidget(grid_widget)

            # Gelmeyenler bolumu
            if gelmedi_list:
                gelmedi_frame = QFrame()
                gelmedi_frame.setStyleSheet(f"""
                    QFrame {{
                        background: {brand.BG_CARD};
                        border: 1px solid {brand.ERROR};
                        border-left: {brand.SP_1}px solid {brand.ERROR};
                        border-radius: {brand.R_SM}px;
                    }}
                """)
                gelmedi_header = QHBoxLayout()
                gelmedi_header.setContentsMargins(brand.SP_3, brand.SP_2, brand.SP_3, brand.SP_2)

                gelmedi_title = QLabel("GELMEYENLER (Vardiya Planinda Olup Giris Yapmayan)")
                gelmedi_title.setStyleSheet(
                    f"color: {brand.ERROR}; "
                    f"font-weight: {brand.FW_BOLD}; "
                    f"font-size: {brand.FS_BODY}px;"
                )
                gelmedi_header.addWidget(gelmedi_title)
                gelmedi_header.addStretch()

                gelmedi_badge = QLabel(str(len(gelmedi_list)))
                gelmedi_badge.setStyleSheet(f"""
                    background: {brand.ERROR};
                    color: white;
                    padding: {brand.SP_1}px {brand.SP_3}px;
                    border-radius: {brand.R_SM}px;
                    font-size: {brand.FS_CAPTION}px;
                    font-weight: {brand.FW_BOLD};
                """)
                gelmedi_header.addWidget(gelmedi_badge)

                gelmedi_layout = QVBoxLayout(gelmedi_frame)
                gelmedi_layout.setContentsMargins(0, 0, 0, brand.SP_2)
                gelmedi_layout.setSpacing(brand.SP_1)
                gelmedi_layout.addLayout(gelmedi_header)

                # Gelmeyenleri vardiyaya gore grupla
                gelmedi_by_vardiya = {}
                for g in gelmedi_list:
                    v = g['vardiya']
                    if v not in gelmedi_by_vardiya:
                        gelmedi_by_vardiya[v] = []
                    gelmedi_by_vardiya[v].append(g)

                for v_kod in sorted(gelmedi_by_vardiya.keys()):
                    kisiler = gelmedi_by_vardiya[v_kod]
                    isimler = ", ".join([k['name'] for k in kisiler])
                    row_label = QLabel(f"  {v_kod} ({len(kisiler)}): {isimler}")
                    row_label.setWordWrap(True)
                    row_label.setStyleSheet(
                        f"color: {brand.TEXT_MUTED}; "
                        f"font-size: {brand.FS_BODY_SM}px; "
                        f"padding: {brand.SP_1}px {brand.SP_3}px;"
                    )
                    gelmedi_layout.addWidget(row_label)

                self.content_layout.addWidget(gelmedi_frame)

            self.content_layout.addStretch()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[ik_pdks] PDKS veri yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _show_movements(self):
        """Hareket listesi dialog'u"""
        dialog = HareketlerDialog(self.theme, self)
        dialog.exec()


class HareketlerDialog(QDialog):
    """Gunluk hareketler dialog'u — el kitabi uyumlu"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Gunluk Hareketler")
        self.setMinimumSize(brand.sp(800), brand.sp(500))
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # Baslik
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)
        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title = QLabel("Gunluk PDKS Hareketleri")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Tarih/Saat", "Personel", "Kart No", "Hareket", "Cihaz"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_3}px {brand.SP_4}px;
                border-bottom: 1px solid {brand.BORDER};
                color: {brand.TEXT};
            }}
            QTableWidget::item:alternate {{ background: {brand.BG_MAIN}; }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_4}px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """)
        layout.addWidget(self.table, 1)

        # Kapat butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedHeight(brand.sp(38))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _load_data(self):
        """Hareketleri yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            today = date.today()

            cursor.execute("""
                SELECT
                    h.hareket_zamani,
                    ISNULL(p.ad + ' ' + p.soyad, 'Bilinmiyor') as personel,
                    h.kart_no,
                    h.hareket_tipi,
                    c.cihaz_adi
                FROM ik.pdks_hareketler h
                LEFT JOIN ik.personeller p ON h.personel_id = p.id
                LEFT JOIN ik.pdks_cihazlari c ON h.cihaz_id = c.id
                WHERE CAST(h.hareket_zamani AS DATE) = ?
                ORDER BY h.hareket_zamani DESC
            """, (today,))

            self.table.setRowCount(0)
            for row in cursor.fetchall():
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)

                zaman = row[0].strftime('%d.%m.%Y %H:%M:%S') if row[0] else '-'
                self.table.setItem(row_idx, 0, QTableWidgetItem(zaman))
                self.table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(row_idx, 2, QTableWidgetItem(row[2] or ''))

                hareket = row[3] or ''
                hareket_item = QTableWidgetItem(hareket)
                if hareket == 'GIRIS':
                    hareket_item.setForeground(QColor(brand.SUCCESS))
                elif hareket == 'CIKIS':
                    hareket_item.setForeground(QColor(brand.ERROR))
                self.table.setItem(row_idx, 3, hareket_item)

                self.table.setItem(row_idx, 4, QTableWidgetItem(row[4] or '-'))

        except Exception as e:
            print(f"[ik_pdks] Hareket yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
