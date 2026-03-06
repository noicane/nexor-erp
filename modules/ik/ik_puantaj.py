# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İK Puantaj Sayfası
Günlük ve aylık devam takibi, giriş-çıkış kayıtları
PDKS hareketlerinden otomatik puantaj hesaplama
"""
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QDateEdit, QCalendarWidget, QGridLayout, QWidget,
    QScrollArea, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection


class IKPuantajPage(BasePage):
    """İK Puantaj Sayfası"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._ilk_yukleme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()

        title = QLabel("📋 Puantaj Takibi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        header.addWidget(title)

        header.addStretch()

        # Excel export
        export_btn = QPushButton("📊 Excel İndir")
        export_btn.setStyleSheet(self._button_style())
        export_btn.clicked.connect(self._export_excel)
        header.addWidget(export_btn)

        layout.addLayout(header)

        # Filtreler
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)

        # Tarih aralığı
        filter_layout.addWidget(QLabel("Başlangıç:"))
        self.dt_start = QDateEdit()
        self.dt_start.setCalendarPopup(True)
        self.dt_start.setDate(QDate.currentDate().addDays(-QDate.currentDate().day() + 1))  # Ayın ilk günü
        self.dt_start.setStyleSheet(self._input_style())
        filter_layout.addWidget(self.dt_start)

        filter_layout.addWidget(QLabel("Bitiş:"))
        self.dt_end = QDateEdit()
        self.dt_end.setCalendarPopup(True)
        self.dt_end.setDate(QDate.currentDate())
        self.dt_end.setStyleSheet(self._input_style())
        filter_layout.addWidget(self.dt_end)

        # Departman
        filter_layout.addWidget(QLabel("Departman:"))
        self.dept_combo = QComboBox()
        self.dept_combo.setStyleSheet(self._combo_style())
        self.dept_combo.setMinimumWidth(150)
        self.dept_combo.addItem("Tümü", None)
        filter_layout.addWidget(self.dept_combo)

        # Hesapla butonu - PDKS'den puantaj oluştur + yükle
        calc_btn = QPushButton("🔄 Hesapla")
        calc_btn.setToolTip("PDKS verilerinden puantaj hesapla ve göster")
        calc_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
        """)
        calc_btn.clicked.connect(self._hesapla_ve_yukle)
        filter_layout.addWidget(calc_btn)

        filter_layout.addStretch()

        layout.addWidget(filter_frame)

        # Özet kartları
        ozet_frame = QFrame()
        ozet_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        ozet_layout = QHBoxLayout(ozet_frame)
        ozet_layout.setContentsMargins(16, 16, 16, 16)

        self.kart_personel = self._create_ozet_kart("👥", "Toplam Personel", "0", self.theme.get('primary'))
        ozet_layout.addWidget(self.kart_personel)

        self.kart_tam = self._create_ozet_kart("✅", "Tam Gün", "0", self.theme.get('success'))
        ozet_layout.addWidget(self.kart_tam)

        self.kart_gec = self._create_ozet_kart("⏰", "Geç Gelen", "0", self.theme.get('warning'))
        ozet_layout.addWidget(self.kart_gec)

        self.kart_yok = self._create_ozet_kart("❌", "Gelmedi", "0", self.theme.get('error'))
        ozet_layout.addWidget(self.kart_yok)

        self.kart_izin = self._create_ozet_kart("🏖️", "İzinli", "0", self.theme.get('info'))
        ozet_layout.addWidget(self.kart_izin)

        layout.addWidget(ozet_frame)

        # Tab Widget
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
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
        """)

        tabs.addTab(self._create_gunluk_tab(), "📅 Günlük Detay")
        tabs.addTab(self._create_aylik_tab(), "📊 Aylık Özet")

        layout.addWidget(tabs, 1)

        # Departmanları yükle
        self._load_departmanlar()

    def _create_ozet_kart(self, icon: str, baslik: str, deger: str, renk: str) -> QFrame:
        """Özet kartı"""
        renk = renk or '#6B7280'
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

    def _create_gunluk_tab(self) -> QWidget:
        """Günlük detay sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)

        self.gunluk_table = QTableWidget()
        self.gunluk_table.setColumnCount(9)
        self.gunluk_table.setHorizontalHeaderLabels([
            "Tarih", "Personel", "Departman", "Vardiya", "Giriş",
            "Çıkış", "Normal Saat", "Mesai Saat", "Durum"
        ])
        self.gunluk_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.gunluk_table.setColumnWidth(0, 90)
        self.gunluk_table.setColumnWidth(2, 120)
        self.gunluk_table.setColumnWidth(3, 80)
        self.gunluk_table.setColumnWidth(4, 70)
        self.gunluk_table.setColumnWidth(5, 70)
        self.gunluk_table.setColumnWidth(6, 90)
        self.gunluk_table.setColumnWidth(7, 90)
        self.gunluk_table.setColumnWidth(8, 100)
        self.gunluk_table.setStyleSheet(self._table_style())
        self.gunluk_table.verticalHeader().setVisible(False)
        self.gunluk_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.gunluk_table.doubleClicked.connect(self._on_gunluk_double_click)

        layout.addWidget(self.gunluk_table)

        return widget

    def _create_aylik_tab(self) -> QWidget:
        """Aylık özet sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)

        self.aylik_table = QTableWidget()
        self.aylik_table.setColumnCount(8)
        self.aylik_table.setHorizontalHeaderLabels([
            "Personel", "Departman", "Çalışılan Gün", "İzinli Gün",
            "Devamsız Gün", "Normal Saat", "Mesai Saat", "Durum"
        ])
        self.aylik_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.aylik_table.setColumnWidth(1, 120)
        self.aylik_table.setColumnWidth(2, 100)
        self.aylik_table.setColumnWidth(3, 90)
        self.aylik_table.setColumnWidth(4, 100)
        self.aylik_table.setColumnWidth(5, 100)
        self.aylik_table.setColumnWidth(6, 90)
        self.aylik_table.setColumnWidth(7, 100)
        self.aylik_table.setStyleSheet(self._table_style())
        self.aylik_table.verticalHeader().setVisible(False)
        self.aylik_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.aylik_table.doubleClicked.connect(self._on_aylik_double_click)

        layout.addWidget(self.aylik_table)

        return widget

    def _input_style(self):
        return f"""
            QDateEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
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

    def _button_style(self):
        return f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: {self.theme.get('bg_hover')}; }}
        """

    def _table_style(self):
        return f"""
            QTableWidget {{
                background: {self.theme.get('bg_main')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {self.theme.get('border')};
            }}
            QTableWidget::item:selected {{
                background: {self.theme.get('primary')};
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary')};
                font-weight: bold;
            }}
        """

    def _load_departmanlar(self):
        """Departman listesini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.dept_combo.addItem(row[1], row[0])
            conn.close()
        except Exception as e:
            print(f"Departman yükleme hatası: {e}")

    def _ilk_yukleme(self):
        """İlk açılışta puantaj hesapla ve yükle"""
        self._hesapla_ve_yukle()

    def _hesapla_ve_yukle(self):
        """PDKS hareketlerinden puantaj oluştur, sonra tabloları doldur"""
        try:
            self._generate_puantaj_from_pdks()
        except Exception as e:
            print(f"Puantaj hesaplama hatası: {e}")
        self._load_data()

    def _generate_puantaj_from_pdks(self):
        """PDKS hareketlerinden ik.puantaj tablosuna veri oluştur"""
        d_start = self.dt_start.date().toPython()
        d_end = self.dt_end.date().toPython()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 1. Vardiya saat bilgilerini al
            cursor.execute("""
                SELECT id, baslangic_saati, bitis_saati
                FROM tanim.vardiyalar WHERE aktif_mi = 1
            """)
            vardiya_map = {}
            for r in cursor.fetchall():
                normal_dk = 480  # 8 saat varsayılan
                if r[1] and r[2]:
                    try:
                        t1 = datetime.combine(date.today(), r[1]) if not isinstance(r[1], datetime) else r[1]
                        t2 = datetime.combine(date.today(), r[2]) if not isinstance(r[2], datetime) else r[2]
                        if isinstance(r[1], timedelta):
                            t1 = datetime.combine(date.today(), (datetime.min + r[1]).time())
                        if isinstance(r[2], timedelta):
                            t2 = datetime.combine(date.today(), (datetime.min + r[2]).time())
                        diff = (t2 - t1).total_seconds() / 60
                        if diff > 0:
                            normal_dk = diff
                    except:
                        pass
                vardiya_map[r[0]] = normal_dk

            # 2. PDKS hareketlerini gruplanmış getir (personel + tarih bazında)
            cursor.execute("""
                SELECT
                    h.personel_id,
                    CAST(h.hareket_zamani AS DATE) as tarih,
                    MIN(CASE WHEN h.hareket_tipi = 'GIRIS' THEN CAST(h.hareket_zamani AS TIME) END),
                    MAX(CASE WHEN h.hareket_tipi = 'CIKIS' THEN CAST(h.hareket_zamani AS TIME) END),
                    DATEDIFF(MINUTE,
                        MIN(CASE WHEN h.hareket_tipi = 'GIRIS' THEN h.hareket_zamani END),
                        MAX(CASE WHEN h.hareket_tipi = 'CIKIS' THEN h.hareket_zamani END)
                    ),
                    p.varsayilan_vardiya_id
                FROM ik.pdks_hareketler h
                JOIN ik.personeller p ON h.personel_id = p.id
                WHERE CAST(h.hareket_zamani AS DATE) BETWEEN ? AND ?
                  AND h.personel_id IS NOT NULL
                  AND p.aktif_mi = 1
                GROUP BY h.personel_id, CAST(h.hareket_zamani AS DATE), p.varsayilan_vardiya_id
            """, (d_start, d_end))
            pdks_rows = cursor.fetchall()

            if not pdks_rows:
                conn.close()
                return

            # 3. Her PDKS kaydı için puantaj MERGE
            inserted = 0
            for row in pdks_rows:
                per_id, tarih, giris, cikis, dakika, vardiya_id = row

                toplam_dk = dakika or 0

                # Vardiya normal dakikası
                normal_dk_limit = vardiya_map.get(vardiya_id, 480) if vardiya_id else 480

                normal_saat = min(toplam_dk, normal_dk_limit) / 60.0
                mesai_saat = max(0, toplam_dk - normal_dk_limit) / 60.0

                # Vardiya planlamasını kontrol et (override)
                try:
                    cursor.execute("""
                        SELECT vardiya_id FROM ik.vardiya_planlama
                        WHERE personel_id = ? AND tarih = ?
                    """, (per_id, tarih))
                    vp = cursor.fetchone()
                    if vp and vp[0]:
                        vardiya_id = vp[0]
                        vp_normal_dk = vardiya_map.get(vardiya_id, 480)
                        normal_saat = min(toplam_dk, vp_normal_dk) / 60.0
                        mesai_saat = max(0, toplam_dk - vp_normal_dk) / 60.0
                except:
                    pass

                # MERGE: varsa güncelle, yoksa ekle (izinli/raporlu kayıtları ezmez)
                cursor.execute("""
                    MERGE ik.puantaj AS tgt
                    USING (SELECT ? AS pid, ? AS tarih) AS src
                    ON tgt.personel_id = src.pid AND tgt.tarih = src.tarih
                    WHEN MATCHED AND tgt.durum NOT IN ('IZINLI', 'RAPORLU', 'MAZERETLI') THEN
                        UPDATE SET
                            giris_saati = ?, cikis_saati = ?,
                            normal_saat = ROUND(?, 2), mesai_saat = ROUND(?, 2),
                            vardiya_id = ?, durum = 'NORMAL',
                            guncelleme_tarihi = GETDATE()
                    WHEN NOT MATCHED THEN
                        INSERT (uuid, personel_id, tarih, vardiya_id, giris_saati, cikis_saati,
                                normal_saat, mesai_saat, durum, olusturma_tarihi)
                        VALUES (NEWID(), ?, ?, ?, ?, ?, ROUND(?, 2), ROUND(?, 2), 'NORMAL', GETDATE());
                """, (
                    per_id, tarih,
                    giris, cikis, normal_saat, mesai_saat, vardiya_id,
                    per_id, tarih, vardiya_id, giris, cikis, normal_saat, mesai_saat
                ))
                inserted += 1

            # 4. İzin taleplerini puantaja yansıt
            cursor.execute("""
                SELECT it.personel_id, it.baslangic_tarihi, it.bitis_tarihi
                FROM ik.izin_talepleri it
                JOIN ik.personeller p ON it.personel_id = p.id
                WHERE it.durum = 'ONAYLANDI'
                  AND it.baslangic_tarihi <= ? AND it.bitis_tarihi >= ?
                  AND p.aktif_mi = 1
            """, (d_end, d_start))
            izin_rows = cursor.fetchall()

            for izin in izin_rows:
                per_id = izin[0]
                izin_start = max(izin[1], d_start) if izin[1] else d_start
                izin_end = min(izin[2], d_end) if izin[2] else d_end
                current = izin_start
                while current <= izin_end:
                    if current.weekday() < 6:  # Pazartesi-Cumartesi
                        cursor.execute("""
                            MERGE ik.puantaj AS tgt
                            USING (SELECT ? AS pid, ? AS tarih) AS src
                            ON tgt.personel_id = src.pid AND tgt.tarih = src.tarih
                            WHEN MATCHED AND tgt.durum NOT IN ('NORMAL') THEN
                                UPDATE SET durum = 'IZINLI', guncelleme_tarihi = GETDATE()
                            WHEN NOT MATCHED THEN
                                INSERT (uuid, personel_id, tarih, normal_saat, mesai_saat, durum, olusturma_tarihi)
                                VALUES (NEWID(), ?, ?, 0, 0, 'IZINLI', GETDATE());
                        """, (per_id, current, per_id, current))
                    current += timedelta(days=1)

            conn.commit()
            if inserted > 0:
                print(f"✓ Puantaj: {inserted} kayıt PDKS'den oluşturuldu/güncellendi")
        except Exception as e:
            print(f"Puantaj generate hatası: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()

    def _load_data(self):
        """Puantaj verilerini yükle ve tabloları doldur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            d_start = self.dt_start.date().toPython()
            d_end = self.dt_end.date().toPython()
            dept_id = self.dept_combo.currentData()

            # Filtre koşulları
            where = ["p.aktif_mi = 1"]
            params = []

            if dept_id:
                where.append("p.departman_id = ?")
                params.append(dept_id)

            where_clause = " AND ".join(where)

            # Günlük puantaj verilerini çek
            cursor.execute(f"""
                SELECT
                    pu.tarih,
                    p.ad + ' ' + p.soyad as personel,
                    d.ad as departman,
                    v.ad as vardiya,
                    pu.giris_saati,
                    pu.cikis_saati,
                    pu.normal_saat,
                    pu.mesai_saat,
                    pu.durum,
                    p.id as personel_id
                FROM ik.puantaj pu
                JOIN ik.personeller p ON pu.personel_id = p.id
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                LEFT JOIN tanim.vardiyalar v ON pu.vardiya_id = v.id
                WHERE pu.tarih BETWEEN ? AND ? AND {where_clause}
                ORDER BY pu.tarih DESC, p.ad
            """, [d_start, d_end] + params)

            self.gunluk_table.setRowCount(0)

            # Sayaçlar
            toplam_tam = 0
            toplam_gec = 0
            toplam_yok = 0
            toplam_izin = 0
            personel_set = set()

            for row in cursor.fetchall():
                row_idx = self.gunluk_table.rowCount()
                self.gunluk_table.insertRow(row_idx)

                personel_set.add(row[1])
                per_id = row[9]

                # Tarih
                tarih = row[0].strftime('%d.%m.%Y') if row[0] else '-'
                tarih_item = QTableWidgetItem(tarih)
                tarih_item.setData(Qt.UserRole, per_id)
                self.gunluk_table.setItem(row_idx, 0, tarih_item)

                # Personel
                self.gunluk_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))

                # Departman
                self.gunluk_table.setItem(row_idx, 2, QTableWidgetItem(row[2] or '-'))

                # Vardiya
                self.gunluk_table.setItem(row_idx, 3, QTableWidgetItem(row[3] or '-'))

                # Giriş saati
                giris = str(row[4])[:5] if row[4] else '-'
                self.gunluk_table.setItem(row_idx, 4, QTableWidgetItem(giris))

                # Çıkış saati
                cikis = str(row[5])[:5] if row[5] else '-'
                self.gunluk_table.setItem(row_idx, 5, QTableWidgetItem(cikis))

                # Normal saat
                normal_saat = row[6] or 0
                self.gunluk_table.setItem(row_idx, 6, QTableWidgetItem(f"{normal_saat:.1f} saat"))

                # Mesai saat
                mesai_saat = row[7] or 0
                mesai_item = QTableWidgetItem(f"{mesai_saat:.1f} saat")
                if mesai_saat > 0:
                    mesai_item.setForeground(QColor(self.theme.get('warning', '#f59e0b')))
                self.gunluk_table.setItem(row_idx, 7, mesai_item)

                # Durum
                durum = row[8] or 'NORMAL'
                durum_item = QTableWidgetItem(durum)

                if durum == 'NORMAL':
                    durum_item.setForeground(QColor(self.theme.get('success', '#10B981')))
                    toplam_tam += 1
                elif durum == 'DEVAMSIZ':
                    durum_item.setForeground(QColor(self.theme.get('error', '#EF4444')))
                    toplam_yok += 1
                elif durum in ('IZINLI', 'RAPORLU', 'MAZERETLI'):
                    durum_item.setForeground(QColor(self.theme.get('info', '#3B82F6')))
                    toplam_izin += 1

                self.gunluk_table.setItem(row_idx, 8, durum_item)

            # Aylık özet hesapla
            self._load_aylik_ozet(cursor, d_start, d_end, where_clause, params)

            conn.close()

            # Özet kartları güncelle
            self.kart_personel.findChild(QLabel, "value").setText(str(len(personel_set)))
            self.kart_tam.findChild(QLabel, "value").setText(str(toplam_tam))
            self.kart_gec.findChild(QLabel, "value").setText(str(toplam_gec))
            self.kart_yok.findChild(QLabel, "value").setText(str(toplam_yok))
            self.kart_izin.findChild(QLabel, "value").setText(str(toplam_izin))

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Veri yüklenemedi: {e}")

    def _load_aylik_ozet(self, cursor, d_start, d_end, where_clause, params):
        """Aylık özet tablosunu doldur"""
        try:
            cursor.execute(f"""
                SELECT
                    p.ad + ' ' + p.soyad as personel,
                    d.ad as departman,
                    SUM(CASE WHEN pu.durum = 'NORMAL' THEN 1 ELSE 0 END) as calisilan_gun,
                    SUM(CASE WHEN pu.durum IN ('IZINLI', 'RAPORLU', 'MAZERETLI') THEN 1 ELSE 0 END) as izinli_gun,
                    SUM(CASE WHEN pu.durum = 'DEVAMSIZ' THEN 1 ELSE 0 END) as devamsiz_gun,
                    SUM(ISNULL(pu.normal_saat, 0)) as toplam_normal,
                    SUM(ISNULL(pu.mesai_saat, 0)) as toplam_mesai,
                    p.id as personel_id
                FROM ik.personeller p
                LEFT JOIN ik.puantaj pu ON p.id = pu.personel_id AND pu.tarih BETWEEN ? AND ?
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                WHERE {where_clause}
                GROUP BY p.id, p.ad, p.soyad, d.ad
                ORDER BY p.ad
            """, [d_start, d_end] + params)

            self.aylik_table.setRowCount(0)

            for row in cursor.fetchall():
                row_idx = self.aylik_table.rowCount()
                self.aylik_table.insertRow(row_idx)

                # Personel
                per_item = QTableWidgetItem(row[0] or '')
                per_item.setData(Qt.UserRole, row[7])
                self.aylik_table.setItem(row_idx, 0, per_item)

                # Departman
                self.aylik_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or '-'))

                # Çalışılan gün
                self.aylik_table.setItem(row_idx, 2, QTableWidgetItem(str(row[2] or 0)))

                # İzinli gün
                self.aylik_table.setItem(row_idx, 3, QTableWidgetItem(str(row[3] or 0)))

                # Devamsız gün
                devamsiz = row[4] or 0
                devamsiz_item = QTableWidgetItem(str(devamsiz))
                if devamsiz > 0:
                    devamsiz_item.setForeground(QColor(self.theme.get('error', '#EF4444')))
                self.aylik_table.setItem(row_idx, 4, devamsiz_item)

                # Normal saat
                toplam_normal = row[5] or 0
                self.aylik_table.setItem(row_idx, 5, QTableWidgetItem(f"{toplam_normal:.1f} saat"))

                # Mesai saat
                toplam_mesai = row[6] or 0
                self.aylik_table.setItem(row_idx, 6, QTableWidgetItem(f"{toplam_mesai:.1f} saat"))

                # Durum
                if devamsiz > 0:
                    self.aylik_table.setItem(row_idx, 7, QTableWidgetItem("⚠️ Devamsız"))
                else:
                    self.aylik_table.setItem(row_idx, 7, QTableWidgetItem("✓ Normal"))

        except Exception as e:
            print(f"Aylık özet hatası: {e}")

    def _on_gunluk_double_click(self, index):
        """Günlük tablodan personel detay aç"""
        row = index.row()
        item = self.gunluk_table.item(row, 0)
        if item:
            per_id = item.data(Qt.UserRole)
            if per_id:
                self._show_personel_detay(per_id)

    def _on_aylik_double_click(self, index):
        """Aylık tablodan personel detay aç"""
        row = index.row()
        item = self.aylik_table.item(row, 0)
        if item:
            per_id = item.data(Qt.UserRole)
            if per_id:
                self._show_personel_detay(per_id)

    def _show_personel_detay(self, personel_id: int):
        """Personel puantaj detay dialogunu aç"""
        d_start = self.dt_start.date().toPython()
        d_end = self.dt_end.date().toPython()
        dlg = PersonelPuantajDialog(personel_id, d_start, d_end, self.theme, self)
        dlg.exec()

    def _export_excel(self):
        """Excel'e aktar"""
        try:
            import csv
            from PySide6.QtWidgets import QFileDialog

            fname, _ = QFileDialog.getSaveFileName(
                self, "Excel Kaydet",
                f"Puantaj_{datetime.now().strftime('%Y%m%d')}.csv",
                "CSV Dosyası (*.csv)"
            )

            if not fname:
                return

            with open(fname, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')

                # Başlıklar
                headers = []
                for col in range(self.gunluk_table.columnCount()):
                    headers.append(self.gunluk_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)

                # Veriler
                for row in range(self.gunluk_table.rowCount()):
                    row_data = []
                    for col in range(self.gunluk_table.columnCount()):
                        item = self.gunluk_table.item(row, col)
                        row_data.append(item.text() if item else '')
                    writer.writerow(row_data)

            QMessageBox.information(self, "Başarılı", f"Dosya kaydedildi:\n{fname}")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Export hatası: {e}")


TURKCE_GUNLER = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']


class PersonelPuantajDialog(QDialog):
    """Personel bazlı puantaj detay dialogu"""

    def __init__(self, personel_id: int, d_start: date, d_end: date, theme: dict, parent=None):
        super().__init__(parent)
        self.personel_id = personel_id
        self.d_start = d_start
        self.d_end = d_end
        self.theme = theme
        self.setWindowTitle("Personel Puantaj Detayı")
        self.setMinimumSize(850, 600)
        self.setModal(True)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        t = self.theme
        bg = t.get('bg_card', '#1E1E1E')
        inp = t.get('bg_input', '#1A1A1A')
        txt = t.get('text', '#FFFFFF')
        brd = t.get('border', '#2A2A2A')
        pri = t.get('primary', '#DC2626')
        suc = t.get('success', '#10B981')
        wrn = t.get('warning', '#F59E0B')
        err = t.get('error', '#EF4444')
        inf = t.get('info', '#3B82F6')
        muted = t.get('text_muted', '#666666')

        self.setStyleSheet(f"QDialog {{ background: {bg}; }} QLabel {{ color: {txt}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header - personel bilgileri
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background: {inp}; border: 1px solid {brd}; border-radius: 10px;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 16, 20, 16)

        self.lbl_name = QLabel("...")
        self.lbl_name.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {txt};")
        header_layout.addWidget(self.lbl_name)

        self.lbl_dept = QLabel("")
        self.lbl_dept.setStyleSheet(f"font-size: 13px; color: {muted};")
        header_layout.addWidget(self.lbl_dept)

        header_layout.addStretch()

        self.lbl_period = QLabel(f"{self.d_start.strftime('%d.%m.%Y')} - {self.d_end.strftime('%d.%m.%Y')}")
        self.lbl_period.setStyleSheet(f"font-size: 12px; color: {inf}; font-weight: 600;")
        header_layout.addWidget(self.lbl_period)

        layout.addWidget(header_frame)

        # Özet kartları
        ozet_layout = QHBoxLayout()
        ozet_layout.setSpacing(10)

        self.oz_calisma = self._mini_kart("Çalışılan Gün", "0", suc)
        ozet_layout.addWidget(self.oz_calisma)
        self.oz_izin = self._mini_kart("İzin Günü", "0", inf)
        ozet_layout.addWidget(self.oz_izin)
        self.oz_devamsiz = self._mini_kart("Devamsız", "0", err)
        ozet_layout.addWidget(self.oz_devamsiz)
        self.oz_normal = self._mini_kart("Normal Saat", "0", txt)
        ozet_layout.addWidget(self.oz_normal)
        self.oz_mesai = self._mini_kart("Mesai Saat", "0", wrn)
        ozet_layout.addWidget(self.oz_mesai)

        layout.addLayout(ozet_layout)

        # Detay tablosu
        self.detay_table = QTableWidget()
        self.detay_table.setColumnCount(8)
        self.detay_table.setHorizontalHeaderLabels([
            "Tarih", "Gün", "Vardiya", "Giriş", "Çıkış",
            "Normal Saat", "Mesai Saat", "Durum"
        ])
        self.detay_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.detay_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.detay_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.detay_table.setColumnWidth(3, 65)
        self.detay_table.setColumnWidth(4, 65)
        self.detay_table.setColumnWidth(5, 90)
        self.detay_table.setColumnWidth(6, 90)
        self.detay_table.setColumnWidth(7, 110)
        self.detay_table.setStyleSheet(f"""
            QTableWidget {{
                background: {t.get('bg_main', '#0F1419')};
                border: 1px solid {brd};
                border-radius: 8px;
                gridline-color: {brd};
                color: {txt};
            }}
            QTableWidget::item {{ padding: 6px; border-bottom: 1px solid {brd}; }}
            QTableWidget::item:selected {{ background: {pri}; }}
            QHeaderView::section {{
                background: {inp}; color: {txt}; padding: 8px;
                border: none; border-bottom: 2px solid {pri}; font-weight: bold;
            }}
        """)
        self.detay_table.verticalHeader().setVisible(False)
        self.detay_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.detay_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.detay_table, 1)

        # Kapat butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(f"QPushButton {{ background: {inp}; color: {txt}; border: 1px solid {brd}; border-radius: 8px; padding: 10px 28px; }} QPushButton:hover {{ background: {brd}; }}")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _mini_kart(self, baslik: str, deger: str, renk: str) -> QFrame:
        t = self.theme
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {t.get('bg_input', '#1A1A1A')}; border: 1px solid {renk}; border-radius: 8px; }}")
        ly = QVBoxLayout(frame)
        ly.setContentsMargins(12, 8, 12, 8)
        ly.setSpacing(2)
        lbl = QLabel(baslik)
        lbl.setStyleSheet(f"font-size: 10px; color: {t.get('text_muted', '#666')};")
        ly.addWidget(lbl)
        val = QLabel(deger)
        val.setObjectName("value")
        val.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {renk};")
        ly.addWidget(val)
        return frame

    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Personel bilgisi
            cursor.execute("""
                SELECT p.ad + ' ' + p.soyad, d.ad, poz.ad, p.sicil_no
                FROM ik.personeller p
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                LEFT JOIN ik.pozisyonlar poz ON p.pozisyon_id = poz.id
                WHERE p.id = ?
            """, (self.personel_id,))
            per = cursor.fetchone()
            if per:
                self.lbl_name.setText(f"👤 {per[0]}")
                parts = []
                if per[1]:
                    parts.append(per[1])
                if per[2]:
                    parts.append(per[2])
                if per[3]:
                    parts.append(f"Sicil: {per[3]}")
                self.lbl_dept.setText(" | ".join(parts))
                self.setWindowTitle(f"Puantaj - {per[0]}")

            # Puantaj kayıtları
            cursor.execute("""
                SELECT
                    pu.tarih, v.ad, pu.giris_saati, pu.cikis_saati,
                    pu.normal_saat, pu.mesai_saat, pu.durum, pu.aciklama
                FROM ik.puantaj pu
                LEFT JOIN tanim.vardiyalar v ON pu.vardiya_id = v.id
                WHERE pu.personel_id = ? AND pu.tarih BETWEEN ? AND ?
                ORDER BY pu.tarih
            """, (self.personel_id, self.d_start, self.d_end))
            rows = cursor.fetchall()

            # İzin taleplerini al
            cursor.execute("""
                SELECT it.baslangic_tarihi, it.bitis_tarihi, izt.ad
                FROM ik.izin_talepleri it
                LEFT JOIN ik.izin_turleri izt ON it.izin_turu_id = izt.id
                WHERE it.personel_id = ? AND it.durum = 'ONAYLANDI'
                  AND it.baslangic_tarihi <= ? AND it.bitis_tarihi >= ?
            """, (self.personel_id, self.d_end, self.d_start))
            izinler = cursor.fetchall()
            conn.close()

            # İzin günleri sözlüğü
            izin_map = {}
            for iz in izinler:
                cur = max(iz[0], self.d_start) if iz[0] else self.d_start
                end = min(iz[1], self.d_end) if iz[1] else self.d_end
                while cur <= end:
                    izin_map[cur] = iz[2] or 'İzin'
                    cur += timedelta(days=1)

            # Puantaj kayıtlarını tarih sözlüğüne al
            puantaj_map = {}
            for r in rows:
                puantaj_map[r[0]] = r

            # Tüm günleri listele
            t = self.theme
            suc = t.get('success', '#10B981')
            wrn = t.get('warning', '#F59E0B')
            err = t.get('error', '#EF4444')
            inf = t.get('info', '#3B82F6')
            muted = t.get('text_muted', '#666666')
            txt = t.get('text', '#FFFFFF')

            toplam_calisma = 0
            toplam_izin_gun = 0
            toplam_devamsiz = 0
            toplam_normal = 0.0
            toplam_mesai = 0.0

            current = self.d_start
            table_rows = []
            while current <= self.d_end:
                gun_adi = TURKCE_GUNLER[current.weekday()]
                is_weekend = current.weekday() == 6  # Pazar

                pu = puantaj_map.get(current)
                izin_adi = izin_map.get(current)

                if pu:
                    vardiya = pu[1] or '-'
                    giris = str(pu[2])[:5] if pu[2] else '-'
                    cikis = str(pu[3])[:5] if pu[3] else '-'
                    normal_s = float(pu[4] or 0)
                    mesai_s = float(pu[5] or 0)
                    durum = pu[6] or 'NORMAL'
                    aciklama = pu[7] or ''
                else:
                    vardiya = '-'
                    giris = '-'
                    cikis = '-'
                    normal_s = 0
                    mesai_s = 0
                    if izin_adi:
                        durum = 'IZINLI'
                    elif is_weekend:
                        durum = 'HAFTA_SONU'
                    else:
                        durum = ''
                    aciklama = ''

                # Sayaçlar
                if durum == 'NORMAL':
                    toplam_calisma += 1
                    toplam_normal += normal_s
                    toplam_mesai += mesai_s
                elif durum in ('IZINLI', 'RAPORLU', 'MAZERETLI'):
                    toplam_izin_gun += 1
                elif durum == 'DEVAMSIZ':
                    toplam_devamsiz += 1

                # Durum metni
                if durum == 'NORMAL':
                    durum_text = "✓ Normal"
                    durum_color = suc
                elif durum in ('IZINLI', 'RAPORLU', 'MAZERETLI'):
                    durum_text = f"🏖️ {izin_adi or durum.capitalize()}"
                    durum_color = inf
                elif durum == 'DEVAMSIZ':
                    durum_text = "❌ Devamsız"
                    durum_color = err
                elif durum == 'HAFTA_SONU':
                    durum_text = "— Hafta Sonu"
                    durum_color = muted
                else:
                    durum_text = "-"
                    durum_color = muted

                table_rows.append({
                    'tarih': current.strftime('%d.%m.%Y'),
                    'gun': gun_adi,
                    'vardiya': vardiya,
                    'giris': giris,
                    'cikis': cikis,
                    'normal': f"{normal_s:.1f}" if normal_s > 0 else "-",
                    'mesai': f"{mesai_s:.1f}" if mesai_s > 0 else "-",
                    'durum_text': durum_text,
                    'durum_color': durum_color,
                    'is_weekend': is_weekend,
                    'has_mesai': mesai_s > 0,
                })
                current += timedelta(days=1)

            # Tabloyu doldur
            self.detay_table.setRowCount(len(table_rows))
            for i, r in enumerate(table_rows):
                row_color = QColor(muted) if r['is_weekend'] else None

                for j, val in enumerate([r['tarih'], r['gun'], r['vardiya'], r['giris'], r['cikis'], r['normal'], r['mesai'], r['durum_text']]):
                    item = QTableWidgetItem(val)
                    if j == 7:
                        item.setForeground(QColor(r['durum_color']))
                        item.setFont(QFont("", -1, QFont.Bold))
                    elif j == 6 and r['has_mesai']:
                        item.setForeground(QColor(wrn))
                        item.setFont(QFont("", -1, QFont.Bold))
                    elif r['is_weekend']:
                        item.setForeground(QColor(muted))
                    self.detay_table.setItem(i, j, item)

                self.detay_table.setRowHeight(i, 32)

            # Özet kartları güncelle
            self.oz_calisma.findChild(QLabel, "value").setText(str(toplam_calisma))
            self.oz_izin.findChild(QLabel, "value").setText(str(toplam_izin_gun))
            self.oz_devamsiz.findChild(QLabel, "value").setText(str(toplam_devamsiz))
            self.oz_normal.findChild(QLabel, "value").setText(f"{toplam_normal:.1f}")
            self.oz_mesai.findChild(QLabel, "value").setText(f"{toplam_mesai:.1f}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Detay yüklenemedi: {e}")
