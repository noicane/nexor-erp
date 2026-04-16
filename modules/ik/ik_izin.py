# -*- coding: utf-8 -*-
"""
NEXOR ERP - IK Izin Yonetimi
=============================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
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
from core.log_manager import LogManager
from core.nexor_brand import brand


class IzinTalepDialog(QDialog):
    """Yeni izin talebi olusturma dialog'u — el kitabi uyumlu"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Yeni Izin Talebi")
        self.setMinimumSize(brand.sp(500), brand.sp(450))
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
            QTextEdit:focus, QSpinBox:focus {{
                border-color: {brand.PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_4)

        # Baslik
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)
        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title = QLabel("Yeni Izin Talebi")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Form
        form = QFormLayout()
        form.setSpacing(brand.SP_3)

        # Personel secimi
        self.cmb_personel = QComboBox()
        self.cmb_personel.setMinimumWidth(brand.sp(300))
        form.addRow("Personel:", self.cmb_personel)

        # Izin turu
        self.cmb_izin_turu = QComboBox()
        form.addRow("Izin Turu:", self.cmb_izin_turu)

        # Baslangic tarihi
        self.dt_baslangic = QDateEdit()
        self.dt_baslangic.setCalendarPopup(True)
        self.dt_baslangic.setDate(QDate.currentDate())
        self.dt_baslangic.dateChanged.connect(self._calculate_days)
        form.addRow("Baslangic:", self.dt_baslangic)

        # Bitis tarihi
        self.dt_bitis = QDateEdit()
        self.dt_bitis.setCalendarPopup(True)
        self.dt_bitis.setDate(QDate.currentDate())
        self.dt_bitis.dateChanged.connect(self._calculate_days)
        form.addRow("Bitis:", self.dt_bitis)

        # Gun sayisi
        self.lbl_gun = QLabel("1 gun")
        self.lbl_gun.setStyleSheet(
            f"color: {brand.PRIMARY}; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_BODY}px;"
        )
        form.addRow("Sure:", self.lbl_gun)

        # Aciklama
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(brand.sp(80))
        self.txt_aciklama.setPlaceholderText("Izin nedeni ve aciklamalar...")
        form.addRow("Aciklama:", self.txt_aciklama)

        layout.addLayout(form)

        # Kalan izin bilgisi
        self.izin_info = QFrame()
        self.izin_info.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        info_layout = QHBoxLayout(self.izin_info)
        info_layout.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)

        self.lbl_izin_hak = QLabel("Yillik Izin Hakki: 14 gun | Kullanilan: 3 gun | Kalan: 11 gun")
        self.lbl_izin_hak.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;"
        )
        info_layout.addWidget(self.lbl_izin_hak)

        layout.addWidget(self.izin_info)
        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(brand.sp(38))
        cancel_btn.setStyleSheet(f"""
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
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Talep Olustur")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(brand.sp(38))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_data(self):
        """Personel ve izin turlerini yukle"""
        conn = None
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

            # Izin turleri
            cursor.execute("SELECT id, ad FROM ik.izin_turleri WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_izin_turu.addItem(row[1], row[0])
        except Exception as e:
            print(f"[ik_izin] Veri yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _calculate_days(self):
        """Gun sayisini hesapla"""
        d1 = self.dt_baslangic.date().toPython()
        d2 = self.dt_bitis.date().toPython()

        if d2 >= d1:
            days = (d2 - d1).days + 1
            self.lbl_gun.setText(f"{days} gun")
        else:
            self.lbl_gun.setText("Gecersiz tarih")

    def _save(self):
        """Izin talebini kaydet"""
        conn = None
        try:
            personel_id = self.cmb_personel.currentData()
            izin_turu_id = self.cmb_izin_turu.currentData()
            baslangic = self.dt_baslangic.date().toPython()
            bitis = self.dt_bitis.date().toPython()
            aciklama = self.txt_aciklama.toPlainText()

            if not personel_id:
                QMessageBox.warning(self, "Uyari", "Lutfen personel secin.")
                return

            if bitis < baslangic:
                QMessageBox.warning(self, "Uyari", "Bitis tarihi baslangictan once olamaz.")
                return

            gun_sayisi = (bitis - baslangic).days + 1

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO ik.izin_talepleri (
                    personel_id, izin_turu_id, baslangic_tarihi,
                    bitis_tarihi, gun_sayisi, aciklama, durum
                ) VALUES (?, ?, ?, ?, ?, ?, 'BEKLEMEDE')
            """, (personel_id, izin_turu_id, baslangic, bitis, gun_sayisi, aciklama))

            conn.commit()
            LogManager.log_insert('ik', 'ik.izin_talepleri', None,
                                  f'Izin talebi olusturuldu: {gun_sayisi} gun')

            QMessageBox.information(self, "Basarili", "Izin talebi olusturuldu.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class IKIzinPage(BasePage):
    """IK Izin Yonetimi Sayfasi — el kitabi uyumlu"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # Header
        header = self.create_page_header(
            "Izin Yonetimi",
            "Izin talepleri olusturma, onaylama ve takip"
        )

        new_btn = self.create_primary_button("Yeni Izin Talebi")
        new_btn.clicked.connect(self._new_talep)
        header.addWidget(new_btn)

        layout.addLayout(header)

        # KPI kartlari
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self.kart_bekleyen = self.create_stat_card("BEKLEYEN", "0", color=brand.WARNING)
        kpi_row.addWidget(self.kart_bekleyen)

        self.kart_onaylanan = self.create_stat_card("ONAYLANAN", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self.kart_onaylanan)

        self.kart_reddedilen = self.create_stat_card("REDDEDILEN", "0", color=brand.ERROR)
        kpi_row.addWidget(self.kart_reddedilen)

        self.kart_bu_ay = self.create_stat_card("BU AY IZINLI", "0", color=brand.INFO)
        kpi_row.addWidget(self.kart_bu_ay)

        kpi_row.addStretch()
        layout.addLayout(kpi_row)

        # Filtreler
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)

        input_css = f"""
            QComboBox, QLineEdit {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus, QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """

        durum_lbl = QLabel("Durum:")
        durum_lbl.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        filter_layout.addWidget(durum_lbl)

        self.status_combo = QComboBox()
        self.status_combo.setStyleSheet(input_css)
        self.status_combo.addItem("Tumu", None)
        self.status_combo.addItem("Beklemede", "BEKLEMEDE")
        self.status_combo.addItem("Onaylandi", "ONAYLANDI")
        self.status_combo.addItem("Reddedildi", "REDDEDILDI")
        self.status_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.status_combo)

        ara_lbl = QLabel("Ara:")
        ara_lbl.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        filter_layout.addWidget(ara_lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Personel adi...")
        self.search_input.setStyleSheet(input_css)
        self.search_input.setMinimumWidth(brand.sp(200))
        self.search_input.returnPressed.connect(self._load_data)
        filter_layout.addWidget(self.search_input)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Personel", "Izin Turu", "Baslangic", "Bitis",
            "Gun", "Durum", "Islem"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, brand.sp(60))
        self.table.setColumnWidth(2, brand.sp(100))
        self.table.setColumnWidth(3, brand.sp(90))
        self.table.setColumnWidth(4, brand.sp(90))
        self.table.setColumnWidth(5, brand.sp(60))
        self.table.setColumnWidth(6, brand.sp(100))
        self.table.setColumnWidth(7, brand.sp(120))
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
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
            QTableWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
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

    def _load_data(self):
        """Izin taleplerini yukle"""
        conn = None
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

            # Ozet sayilari
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

            # Kartlari guncelle
            self.kart_bekleyen.findChild(QLabel, "stat_value").setText(str(bekleyen))
            self.kart_onaylanan.findChild(QLabel, "stat_value").setText(str(onaylanan))
            self.kart_reddedilen.findChild(QLabel, "stat_value").setText(str(reddedilen))
            self.kart_bu_ay.findChild(QLabel, "stat_value").setText(str(bu_ay))

            # Talepler
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

                # Izin turu
                self.table.setItem(row_idx, 2, QTableWidgetItem(row[2] or ''))

                # Baslangic
                baslangic = row[3].strftime('%d.%m.%Y') if row[3] else '-'
                self.table.setItem(row_idx, 3, QTableWidgetItem(baslangic))

                # Bitis
                bitis = row[4].strftime('%d.%m.%Y') if row[4] else '-'
                self.table.setItem(row_idx, 4, QTableWidgetItem(bitis))

                # Gun
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(row[5] or 0)))

                # Durum
                durum = row[6] or ''
                durum_item = QTableWidgetItem(durum)
                if durum == 'BEKLEMEDE':
                    durum_item.setForeground(QColor(brand.WARNING))
                elif durum == 'ONAYLANDI':
                    durum_item.setForeground(QColor(brand.SUCCESS))
                elif durum == 'REDDEDILDI':
                    durum_item.setForeground(QColor(brand.ERROR))
                self.table.setItem(row_idx, 6, durum_item)

                # Islem butonlari
                if durum == 'BEKLEMEDE':
                    widget = self.create_action_buttons([
                        ("Onayla", "Onayla", lambda checked, tid=row[0]: self._onayla(tid), "success"),
                        ("Reddet", "Reddet", lambda checked, tid=row[0]: self._reddet(tid), "delete"),
                    ])
                    self.table.setCellWidget(row_idx, 7, widget)
                elif durum == 'ONAYLANDI':
                    widget = self.create_action_buttons([
                        ("Yazdir", "Yazdir", lambda checked, tid=row[0]: self._yazdir(tid), "print"),
                    ])
                    self.table.setCellWidget(row_idx, 7, widget)
                else:
                    self.table.setItem(row_idx, 7, QTableWidgetItem("-"))

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Veri yuklenemedi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _new_talep(self):
        """Yeni izin talebi olustur"""
        dialog = IzinTalepDialog(self.theme, self)
        if dialog.exec():
            self._load_data()

    def _onayla(self, talep_id: int):
        """Izin talebini onayla"""
        reply = QMessageBox.question(self, "Onay", "Bu izin talebi onaylanacak. Devam edilsin mi?")
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE ik.izin_talepleri
                    SET durum = 'ONAYLANDI', onay_tarihi = GETDATE()
                    WHERE id = ?
                """, (talep_id,))
                conn.commit()
                LogManager.log_update('ik', 'ik.izin_talepleri', talep_id, 'Izin talebi onaylandi')

                self._load_data()
                QMessageBox.information(self, "Basarili", "Izin talebi onaylandi.")
                # Onay sonrasi formu yazdir
                self._yazdir(talep_id)
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Onay hatasi: {e}")
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    def _yazdir(self, talep_id: int):
        """Izin formunu PDF olarak yazdir"""
        try:
            from utils.izin_formu_pdf import izin_formu_pdf
            pdf_path = izin_formu_pdf(talep_id)
            if pdf_path:
                QMessageBox.information(self, "Yazdir", "Izin formu olusturuldu.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF olusturulamadi: {e}")

    def _reddet(self, talep_id: int):
        """Izin talebini reddet"""
        reply = QMessageBox.question(self, "Red", "Bu izin talebi reddedilecek. Devam edilsin mi?")
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE ik.izin_talepleri
                    SET durum = 'REDDEDILDI', onay_tarihi = GETDATE()
                    WHERE id = ?
                """, (talep_id,))
                conn.commit()
                LogManager.log_update('ik', 'ik.izin_talepleri', talep_id, 'Izin talebi reddedildi')

                self._load_data()
                QMessageBox.information(self, "Bilgi", "Izin talebi reddedildi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Red hatasi: {e}")
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
