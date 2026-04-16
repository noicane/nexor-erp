# -*- coding: utf-8 -*-
"""
NEXOR ERP - Depo Cikis Ekrani
Planlanan is emirleri icin malzeme cikisi
Barkod okutma veya sifreli manuel cikis
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QComboBox, QWidget, QGroupBox, QGridLayout, QInputDialog,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand

MANUEL_CIKIS_SIFRE = "1234"


class ManuelCikisDialog(QDialog):
    def __init__(self, emir_data: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.emir_data = emir_data
        self.onaylandi = False
        self.setWindowTitle("Manuel Cikis Onayi")
        self.setMinimumSize(brand.sp(450), brand.sp(380))
        self._setup_ui()

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

        # Header
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)
        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.WARNING}; border-radius: 2px;")
        header.addWidget(accent)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)
        title = QLabel("Manuel Cikis Onayi")
        title.setStyleSheet(
            f"color: {brand.WARNING}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        title_col.addWidget(title)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)

        warning_lbl = QLabel("Barkod okutulamadigi icin manuel cikis yapilacak.")
        warning_lbl.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px;"
        )
        layout.addWidget(warning_lbl)

        # Info frame
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                padding: {brand.SP_3}px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(brand.SP_2)
        info_layout.addWidget(QLabel(f"Cikis Emri: {self.emir_data.get('emir_no', '-')}"))
        info_layout.addWidget(QLabel(f"Lot No: {self.emir_data.get('lot_no', '-')}"))
        info_layout.addWidget(QLabel(f"Urun: {self.emir_data.get('stok_adi', '-')}"))
        info_layout.addWidget(QLabel(f"Miktar: {self.emir_data.get('talep_miktar', 0):,.0f}"))
        layout.addWidget(info_frame)

        # Password
        sifre_label = QLabel("Yetki Sifresi:")
        sifre_label.setStyleSheet(
            f"font-weight: {brand.FW_SEMIBOLD}; color: {brand.TEXT}; "
            f"font-size: {brand.FS_BODY}px;"
        )
        layout.addWidget(sifre_label)

        self.sifre_input = QLineEdit()
        self.sifre_input.setEchoMode(QLineEdit.Password)
        self.sifre_input.setPlaceholderText("Sifre girin...")
        self.sifre_input.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY_LG}px;
            }}
            QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.sifre_input.returnPressed.connect(self._onay)
        layout.addWidget(self.sifre_input)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        iptal_btn = QPushButton("Iptal")
        iptal_btn.setCursor(Qt.PointingHandCursor)
        iptal_btn.setFixedHeight(brand.sp(38))
        iptal_btn.setStyleSheet(f"""
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
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)

        onay_btn = QPushButton("Onayla")
        onay_btn.setCursor(Qt.PointingHandCursor)
        onay_btn.setFixedHeight(brand.sp(38))
        onay_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.WARNING};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #D97706; }}
        """)
        onay_btn.clicked.connect(self._onay)
        btn_layout.addWidget(onay_btn)
        layout.addLayout(btn_layout)

    def _onay(self):
        if self.sifre_input.text() == MANUEL_CIKIS_SIFRE:
            self.onaylandi = True
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Sifre yanlis!")
            self.sifre_input.clear()
            self.sifre_input.setFocus()


class DepoCikisPage(BasePage):
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
            "Depo Cikis Islemleri",
            "Barkod okutma veya manuel malzeme cikisi"
        )
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"padding: {brand.SP_2}px {brand.SP_4}px; "
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; "
            f"border-radius: {brand.R_SM}px;"
        )
        header.addWidget(self.stat_label)

        toplu_yazdir_btn = self.create_primary_button("Toplu Yazdir")
        toplu_yazdir_btn.clicked.connect(self._toplu_yazdir)
        header.addWidget(toplu_yazdir_btn)

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        header.addWidget(btn_yenile)
        layout.addLayout(header)

        # Barkod okutma alani
        barkod_frame = QFrame()
        barkod_frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 2px solid {brand.INFO};
                border-radius: {brand.R_LG}px;
                padding: {brand.SP_4}px;
            }}
        """)
        barkod_layout = QHBoxLayout(barkod_frame)
        barkod_layout.setSpacing(brand.SP_3)

        barkod_input_layout = QVBoxLayout()
        barkod_label = QLabel("Lot Barkodu Okutun:")
        barkod_label.setStyleSheet(
            f"color: {brand.TEXT}; font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_BODY}px;"
        )
        barkod_input_layout.addWidget(barkod_label)

        self.barkod_input = QLineEdit()
        self.barkod_input.setPlaceholderText("Barkod okutun veya lot no girin...")
        self.barkod_input.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 2px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY_LG}px;
            }}
            QLineEdit:focus {{ border-color: {brand.INFO}; }}
        """)
        self.barkod_input.returnPressed.connect(self._process_barkod)
        barkod_input_layout.addWidget(self.barkod_input)
        barkod_layout.addLayout(barkod_input_layout, 1)
        layout.addWidget(barkod_frame)

        # Filtreler
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(brand.SP_3)

        durum_label = QLabel("Durum:")
        durum_label.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_BODY}px;"
        )
        filter_layout.addWidget(durum_label)

        self.durum_filter = QComboBox()
        self.durum_filter.setMinimumWidth(brand.sp(140))
        self.durum_filter.addItem("Tum Durumlar", None)
        self.durum_filter.addItem("Bekliyor", "BEKLIYOR")
        self.durum_filter.addItem("Tamamlandi", "TAMAMLANDI")
        self.durum_filter.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.durum_filter)

        depo_label = QLabel("Hedef Depo:")
        depo_label.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_BODY}px;"
        )
        filter_layout.addWidget(depo_label)

        self.depo_filter = QComboBox()
        self.depo_filter.setMinimumWidth(brand.sp(160))
        self.depo_filter.addItem("Tum Depolar", None)
        self._load_depolar()
        self.depo_filter.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.depo_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(["ID", "Emir No", "Lot No", "Stok Kodu", "Stok Adi", "Miktar", "Hedef Depo", "Olusturma", "Durum", "Islem"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(1, brand.sp(100))
        self.table.setColumnWidth(2, brand.sp(140))
        self.table.setColumnWidth(3, brand.sp(100))
        self.table.setColumnWidth(5, brand.sp(80))
        self.table.setColumnWidth(6, brand.sp(120))
        self.table.setColumnWidth(7, brand.sp(100))
        self.table.setColumnWidth(8, brand.sp(100))
        self.table.setColumnWidth(9, brand.sp(160))
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
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
            QTableWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_2}px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """)
        layout.addWidget(self.table, 1)

    def _load_depolar(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.depolar WHERE aktif_mi = 1 AND kod LIKE 'URT-%' ORDER BY kod")
            for row in cursor.fetchall():
                self.depo_filter.addItem(f"{row[1]} - {row[2]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            durum = self.durum_filter.currentData()
            depo_id = self.depo_filter.currentData()
            query = """SELECT e.id, e.emir_no, e.lot_no, e.stok_kodu, e.stok_adi, e.talep_miktar, d.kod + ' - ' + d.ad, FORMAT(e.olusturma_tarihi, 'dd.MM.yyyy'), e.durum
                FROM stok.depo_cikis_emirleri e
                LEFT JOIN tanim.depolar d ON e.hedef_depo_id = d.id WHERE 1=1"""
            params = []
            if durum:
                query += " AND e.durum = ?"
                params.append(durum)
            if depo_id:
                query += " AND e.hedef_depo_id = ?"
                params.append(depo_id)
            query += " ORDER BY e.olusturma_tarihi DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            self.table.setRowCount(len(rows))
            bekleyen = 0
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val) if val else "")
                    if j == 8:
                        if val == 'BEKLIYOR':
                            item.setForeground(QColor(brand.WARNING))
                            bekleyen += 1
                        elif val == 'TAMAMLANDI':
                            item.setForeground(QColor(brand.SUCCESS))
                    self.table.setItem(i, j, item)

                btns = []
                if row[8] == 'BEKLIYOR':
                    btns.append(("Cikis", "Cikis Yap", lambda _, eid=row[0]: self._manuel_cikis(eid), "warning"))
                btns.append(("Yazdir", "Yazdir", lambda _, eid=row[0]: self._yazdir_depo_cikis(eid), "print"))
                btn_widget = self.create_action_buttons(btns)
                self.table.setCellWidget(i, 9, btn_widget)
                self.table.setRowHeight(i, brand.sp(42))
            self.stat_label.setText(f"Toplam: {len(rows)} | Bekleyen: {bekleyen}")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _process_barkod(self):
        barkod = self.barkod_input.text().strip()
        if not barkod:
            return
        self.barkod_input.clear()
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT e.id, e.emir_no, e.lot_no, e.stok_adi, e.talep_miktar, e.hedef_depo_id, e.durum
                FROM stok.depo_cikis_emirleri e INNER JOIN stok.stok_bakiye sb ON e.lot_no = sb.lot_no
                WHERE (e.lot_no = ? OR e.emir_no = ?) AND e.durum = 'BEKLIYOR' AND sb.durum_kodu = 'PLANLANDI'""", (barkod, barkod))
            row = cursor.fetchone()
            if row:
                emir_data = {'id': row[0], 'emir_no': row[1], 'lot_no': row[2], 'stok_adi': row[3], 'talep_miktar': row[4], 'hedef_depo_id': row[5], 'durum': row[6]}
                self._do_cikis(emir_data, manuel=False)
            else:
                QMessageBox.warning(self, "Bulunamadi", f"'{barkod}' icin bekleyen cikis emri bulunamadi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        self.barkod_input.setFocus()

    def _manuel_cikis(self, emir_id: int):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT e.id, e.emir_no, e.lot_no, e.stok_adi, e.talep_miktar, e.hedef_depo_id, e.durum
                FROM stok.depo_cikis_emirleri e INNER JOIN stok.stok_bakiye sb ON e.lot_no = sb.lot_no
                WHERE e.id = ? AND sb.durum_kodu = 'PLANLANDI'""", (emir_id,))
            row = cursor.fetchone()
            if row:
                emir_data = {'id': row[0], 'emir_no': row[1], 'lot_no': row[2], 'stok_adi': row[3], 'talep_miktar': row[4], 'hedef_depo_id': row[5], 'durum': row[6]}
                dlg = ManuelCikisDialog(emir_data, self.theme, self)
                if dlg.exec() == QDialog.Accepted and dlg.onaylandi:
                    self._do_cikis(emir_data, manuel=True)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _toplu_yazdir(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Uyari", "Yazdirmak icin tablodan satir secin.\n(Ctrl+tiklama ile coklu secim yapabilirsiniz)")
            return
        emir_ids = []
        for idx in selected_rows:
            item = self.table.item(idx.row(), 0)
            if item:
                emir_ids.append(int(item.text()))
        if not emir_ids:
            return
        cevap = QMessageBox.question(self, "Toplu Yazdir",
            f"{len(emir_ids)} adet depo cikis emri yazdirilacak.\nDevam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if cevap != QMessageBox.Yes:
            return
        try:
            from utils.depo_cikis_pdf import depo_cikis_pdf_olustur
            for eid in emir_ids:
                depo_cikis_pdf_olustur(eid)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF olusturma hatasi:\n{e}")

    def _yazdir_depo_cikis(self, emir_id: int):
        try:
            from utils.depo_cikis_pdf import depo_cikis_pdf_olustur
            depo_cikis_pdf_olustur(emir_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF olusturma hatasi:\n{e}")

    def _do_cikis(self, emir_data: dict, manuel: bool = False):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            from core.hareket_motoru import HareketMotoru
            motor = HareketMotoru(conn)
            emir_id = emir_data['id']
            lot_no = emir_data['lot_no']
            miktar = emir_data['talep_miktar']
            hedef_depo_id = emir_data['hedef_depo_id']
            motor.rezerve_iptal(lot_no, miktar)
            transfer_sonuc = motor.transfer(
                lot_no=lot_no, hedef_depo_id=hedef_depo_id, miktar=None,
                kaynak="DEPO_CIKIS", kaynak_id=emir_id,
                aciklama=f"Depo cikis emri: {emir_data.get('emir_no', '')}",
                durum_kodu='URETIMDE'
            )
            if not transfer_sonuc.basarili:
                raise Exception(f"Transfer basarisiz: {transfer_sonuc.mesaj or transfer_sonuc.hata}")
            cursor.execute("UPDATE stok.depo_cikis_emirleri SET durum = 'TAMAMLANDI', transfer_miktar = ?, tamamlanma_tarihi = GETDATE(), guncelleme_tarihi = GETDATE() WHERE id = ?", (miktar, emir_id))
            cursor.execute("UPDATE siparis.is_emirleri SET durum = 'URETIMDE', guncelleme_tarihi = GETDATE() WHERE id = (SELECT is_emri_id FROM stok.depo_cikis_emirleri WHERE id = ?) AND durum = 'PLANLANDI'", (emir_id,))
            conn.commit()
            LogManager.log_update('depo', 'siparis.is_emirleri', None, 'Durum guncellendi')

            depo_adi = f"ID: {hedef_depo_id}"
            conn2 = None
            try:
                conn2 = get_db_connection()
                cursor2 = conn2.cursor()
                cursor2.execute("SELECT kod, ad FROM tanim.depolar WHERE id = ?", (hedef_depo_id,))
                depo_row = cursor2.fetchone()
                if depo_row:
                    depo_adi = f"{depo_row[0]} - {depo_row[1]}"
            except Exception:
                pass
            finally:
                if conn2:
                    try:
                        conn2.close()
                    except Exception:
                        pass

            cikis_tipi = 'MANUEL' if manuel else 'BARKOD'
            try:
                from core.bildirim_tetikleyici import BildirimTetikleyici
                BildirimTetikleyici.onay_bekliyor(
                    onaylayici_id=None,
                    kayit_tipi='Uretim',
                    kayit_aciklama=f"Lot {lot_no} depo cikisi yapildi, uretim baslatilabilir. Hedef: {depo_adi}",
                    kaynak_tablo='stok.depo_cikis_emirleri',
                    kaynak_id=emir_id,
                    sayfa_yonlendirme='uretim_giris',
                )
            except Exception as bt_err:
                print(f"Bildirim hatasi: {bt_err}")

            QMessageBox.information(self, "Cikis Tamamlandi",
                f"Lot: {lot_no}\nMiktar: {miktar:,.0f}\nHedef Depo: {depo_adi}\n\nCikis Tipi: {cikis_tipi}")
            self._load_data()
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Cikis hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
