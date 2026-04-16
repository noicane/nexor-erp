# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İK Zimmet Takip
KKD ve ekipman zimmet yönetimi, teslim/iade işlemleri
"""
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QDateEdit, QTextEdit, QFormLayout, QWidget, QSpinBox,
    QTabWidget, QFileDialog, QCheckBox, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand


class ZimmetTeslimDialog(QDialog):
    """Coklu zimmet teslim dialog'u - birden fazla malzeme secilip tek seferde teslim edilir"""

    def __init__(self, theme: dict, personel_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.personel_id = personel_id
        self.setWindowTitle("Zimmet Teslim")
        self.setMinimumSize(brand.sp(750), brand.sp(650))
        self._malzeme_rows = []
        self._zimmet_turleri = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; font-family: {brand.FONT_FAMILY}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus, QSpinBox:focus {{
                border-color: {brand.PRIMARY};
            }}
            QCheckBox {{ color: {brand.TEXT}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_5, brand.SP_5, brand.SP_5, brand.SP_5)
        layout.setSpacing(brand.SP_3)

        # Baslik
        title = QLabel("Zimmet Teslim (Coklu Malzeme)")
        title.setStyleSheet(
            f"font-size: {brand.FS_HEADING}px; font-weight: {brand.FW_SEMIBOLD}; color: {brand.PRIMARY};"
        )
        layout.addWidget(title)

        # Ust form: Personel + Tarih
        top_form = QHBoxLayout()
        top_form.addWidget(QLabel("Personel:"))
        self.cmb_personel = QComboBox()
        self.cmb_personel.setMinimumWidth(300)
        top_form.addWidget(self.cmb_personel, 1)
        top_form.addWidget(QLabel("Teslim Tarihi:"))
        self.dt_teslim = QDateEdit()
        self.dt_teslim.setCalendarPopup(True)
        self.dt_teslim.setDate(QDate.currentDate())
        top_form.addWidget(self.dt_teslim)
        layout.addLayout(top_form)

        # Malzeme secim tablosu
        lbl = QLabel("Teslim edilecek malzemeleri secin:")
        lbl.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        layout.addWidget(lbl)

        self.malzeme_table = QTableWidget()
        self.malzeme_table.setColumnCount(5)
        self.malzeme_table.setHorizontalHeaderLabels(["Sec", "Malzeme", "Miktar", "Beden", "Seri No"])
        self.malzeme_table.verticalHeader().setVisible(False)
        self.malzeme_table.setShowGrid(False)
        self.malzeme_table.setAlternatingRowColors(True)
        self.malzeme_table.setStyleSheet(f"""
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
        """)
        h = self.malzeme_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.resizeSection(0, brand.sp(40))
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Fixed)
        h.resizeSection(2, brand.sp(70))
        h.setSectionResizeMode(3, QHeaderView.Fixed)
        h.resizeSection(3, brand.sp(80))
        h.setSectionResizeMode(4, QHeaderView.Fixed)
        h.resizeSection(4, brand.sp(140))
        layout.addWidget(self.malzeme_table, 1)

        # Secim ozet
        self.lbl_secim = QLabel("0 malzeme secili")
        self.lbl_secim.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        layout.addWidget(self.lbl_secim)

        # Aciklama
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(brand.sp(50))
        self.txt_aciklama.setPlaceholderText("Genel not (opsiyonel)...")
        layout.addWidget(self.txt_aciklama)

        # Butonlar
        btn_layout = QHBoxLayout()

        tumunu_sec = QPushButton("Tumunu Sec")
        tumunu_sec.setCursor(Qt.PointingHandCursor)
        tumunu_sec.setFixedHeight(brand.sp(38))
        tumunu_sec.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
        """)
        tumunu_sec.clicked.connect(self._tumunu_sec)
        btn_layout.addWidget(tumunu_sec)

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

        save_btn = QPushButton("Teslim Et")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(brand.sp(38))
        save_btn.setStyleSheet(f"""
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
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_data(self):
        """Verileri yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Personeller
            cursor.execute("""
                SELECT id, sicil_no, ad + ' ' + soyad as ad_soyad
                FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad, soyad
            """)
            idx = 0
            for i, row in enumerate(cursor.fetchall()):
                self.cmb_personel.addItem(f"{row[1]} - {row[2]}", row[0])
                if self.personel_id and row[0] == self.personel_id:
                    idx = i
            if self.personel_id:
                self.cmb_personel.setCurrentIndex(idx)

            # Zimmet turleri -> tabloya ekle
            cursor.execute("""
                SELECT id, ad, kategori, periyot_gun
                FROM ik.zimmet_turleri WHERE aktif_mi = 1
                ORDER BY kategori, ad
            """)
            self._zimmet_turleri = cursor.fetchall()

            self._fill_malzeme_table()

        except Exception as e:
            print(f"Veri yukleme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _fill_malzeme_table(self):
        """Malzeme tablosunu doldur"""
        self._malzeme_rows = []
        self.malzeme_table.setRowCount(len(self._zimmet_turleri))

        bedenler = ["", "XS", "S", "M", "L", "XL", "XXL", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45"]

        for i, tur in enumerate(self._zimmet_turleri):
            tur_id, tur_ad, kategori, periyot = tur[0], tur[1], tur[2] or '', tur[3]

            # Checkbox
            chk = QCheckBox()
            chk.stateChanged.connect(self._update_secim_sayisi)
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            self.malzeme_table.setCellWidget(i, 0, chk_widget)

            # Malzeme adi (kategori ile)
            display = f"[{kategori}] {tur_ad}" if kategori else tur_ad
            item = QTableWidgetItem(display)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.malzeme_table.setItem(i, 1, item)

            # Miktar
            spn = QSpinBox()
            spn.setRange(1, 100)
            spn.setValue(1)
            self.malzeme_table.setCellWidget(i, 2, spn)

            # Beden
            cmb = QComboBox()
            cmb.setEditable(True)
            cmb.addItems(bedenler)
            self.malzeme_table.setCellWidget(i, 3, cmb)

            # Seri no
            txt = QLineEdit()
            txt.setPlaceholderText("Opsiyonel")
            self.malzeme_table.setCellWidget(i, 4, txt)

            self._malzeme_rows.append({
                'tur_id': tur_id,
                'tur_ad': tur_ad,
                'periyot': periyot,
                'chk': chk,
                'spn': spn,
                'cmb_beden': cmb,
                'txt_seri': txt,
            })

            self.malzeme_table.setRowHeight(i, brand.sp(42))

    def _update_secim_sayisi(self):
        secili = sum(1 for r in self._malzeme_rows if r['chk'].isChecked())
        self.lbl_secim.setText(f"{secili} malzeme secili")

    def _tumunu_sec(self):
        herhangi = any(r['chk'].isChecked() for r in self._malzeme_rows)
        for r in self._malzeme_rows:
            r['chk'].setChecked(not herhangi)
        self._update_secim_sayisi()

    def _save(self):
        """Secili malzemeleri toplu teslim et"""
        personel_id = self.cmb_personel.currentData()
        if not personel_id:
            QMessageBox.warning(self, "Uyari", "Lutfen personel secin.")
            return

        secili = [r for r in self._malzeme_rows if r['chk'].isChecked()]
        if not secili:
            QMessageBox.warning(self, "Uyari", "Lutfen en az bir malzeme secin.")
            return

        conn = None
        try:
            teslim_tarihi = self.dt_teslim.date().toPython()
            aciklama = self.txt_aciklama.toPlainText() or None
            ts = datetime.now().strftime('%Y%m%d%H%M%S')

            conn = get_db_connection()
            cursor = conn.cursor()

            eklenen = 0
            for idx, r in enumerate(secili):
                periyot = r['periyot']
                sonraki = None
                if periyot:
                    sonraki = teslim_tarihi + timedelta(days=periyot)

                zimmet_no = f"Z{ts}{idx + 1:02d}"
                beden = (r['cmb_beden'].currentText() or "")[:20] or None
                seri_no = (r['txt_seri'].text() or "")[:50] or None
                aciklama_val = (aciklama or "")[:500] or None

                cursor.execute("""
                    INSERT INTO ik.zimmetler (
                        zimmet_no, personel_id, zimmet_turu_id, teslim_tarihi,
                        miktar, beden, seri_no, durum, sonraki_yenileme, aciklama
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'TESLIM', ?, ?)
                """, (zimmet_no, personel_id, r['tur_id'], teslim_tarihi,
                      r['spn'].value(), beden, seri_no, sonraki, aciklama_val))

                eklenen += 1

            conn.commit()
            LogManager.log_insert('ik', 'ik.zimmetler', None,
                                  f'Toplu zimmet teslim: {eklenen} kalem')

            malzeme_list = ", ".join(r['tur_ad'] for r in secili)
            QMessageBox.information(self, "Basarili",
                                    f"{eklenen} kalem zimmet teslim edildi.\n\n{malzeme_list}")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class IKZimmetPage(BasePage):
    """İK Zimmet Takip Sayfası"""
    
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
            "Zimmet Takip",
            "KKD ve ekipman zimmet yonetimi"
        )

        # PDF Form butonu
        pdf_btn = QPushButton("Zimmet Formu")
        pdf_btn.setCursor(Qt.PointingHandCursor)
        pdf_btn.setFixedHeight(brand.sp(38))
        pdf_btn.setStyleSheet(self._button_style())
        pdf_btn.clicked.connect(self._print_form)
        header.addWidget(pdf_btn)

        # Yeni teslim butonu
        new_btn = QPushButton("Yeni Teslim")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setFixedHeight(brand.sp(38))
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.SUCCESS};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        new_btn.clicked.connect(self._new_teslim)
        header.addWidget(new_btn)

        layout.addLayout(header)

        # KPI kartlari
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(brand.SP_4)

        self.kart_teslim = self.create_stat_card("TESLIM EDILEN", "0", color=brand.PRIMARY)
        kpi_row.addWidget(self.kart_teslim)

        self.kart_iade = self.create_stat_card("IADE EDILEN", "0", color=brand.SUCCESS)
        kpi_row.addWidget(self.kart_iade)

        self.kart_yenileme = self.create_stat_card("YENILEME BEKLEYEN", "0", color=brand.WARNING)
        kpi_row.addWidget(self.kart_yenileme)

        self.kart_kayip = self.create_stat_card("KAYIP / HASARLI", "0", color=brand.ERROR)
        kpi_row.addWidget(self.kart_kayip)

        layout.addLayout(kpi_row)
        
        # Filtreler
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {brand.BG_CARD}; border-radius: {brand.R_LG}px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(brand.SP_4, brand.SP_3, brand.SP_4, brand.SP_3)

        # Arama
        lbl_ara = QLabel("Ara:")
        lbl_ara.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        filter_layout.addWidget(lbl_ara)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Personel adi, zimmet turu...")
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.setMinimumWidth(brand.sp(200))
        self.search_input.returnPressed.connect(self._load_data)
        filter_layout.addWidget(self.search_input)

        # Durum filtresi
        lbl_dur = QLabel("Durum:")
        lbl_dur.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        filter_layout.addWidget(lbl_dur)
        self.status_combo = QComboBox()
        self.status_combo.setStyleSheet(self._combo_style())
        self.status_combo.addItem("Tumu", None)
        self.status_combo.addItem("Teslim Edildi", "TESLIM")
        self.status_combo.addItem("Iade Edildi", "IADE")
        self.status_combo.addItem("Kayip", "KAYIP")
        self.status_combo.addItem("Hasarli", "HASARLI")
        self.status_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.status_combo)

        # Kategori filtresi
        lbl_kat = QLabel("Kategori:")
        lbl_kat.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY_SM}px;")
        filter_layout.addWidget(lbl_kat)
        self.kategori_combo = QComboBox()
        self.kategori_combo.setStyleSheet(self._combo_style())
        self.kategori_combo.addItem("Tumu", None)
        self.kategori_combo.addItem("KKD", "KKD")
        self.kategori_combo.addItem("Ekipman", "EKIPMAN")
        self.kategori_combo.addItem("Arac", "ARAC")
        self.kategori_combo.addItem("Diger", "DIGER")
        self.kategori_combo.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.kategori_combo)

        filter_layout.addStretch()

        # Disa Aktar
        filter_layout.addWidget(self.create_export_button(title="Zimmet Takip", table_attr="aktif_table"))

        layout.addWidget(filter_frame)

        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet(self._tab_style())

        tabs.addTab(self._create_aktif_tab(), "Aktif Zimmetler")
        tabs.addTab(self._create_yenileme_tab(), "Yenileme Bekleyenler")
        tabs.addTab(self._create_gecmis_tab(), "Tum Gecmis")

        layout.addWidget(tabs, 1)
    
    def _create_aktif_tab(self) -> QWidget:
        """Aktif zimmetler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        self.aktif_table = QTableWidget()
        self.aktif_table.setColumnCount(9)
        self.aktif_table.setHorizontalHeaderLabels([
            "Zimmet No", "Personel", "Zimmet Türü", "Kategori", "Teslim Tarihi", 
            "Miktar", "Beden", "Yenileme", "İşlem"
        ])
        self.aktif_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.aktif_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.aktif_table.setColumnWidth(0, brand.sp(140))
        self.aktif_table.setColumnWidth(3, brand.sp(80))
        self.aktif_table.setColumnWidth(4, brand.sp(100))
        self.aktif_table.setColumnWidth(5, brand.sp(60))
        self.aktif_table.setColumnWidth(6, brand.sp(60))
        self.aktif_table.setColumnWidth(7, brand.sp(100))
        self.aktif_table.setColumnWidth(8, brand.sp(120))
        self.aktif_table.setStyleSheet(self._table_style())
        self.aktif_table.verticalHeader().setVisible(False)
        self.aktif_table.setShowGrid(False)
        self.aktif_table.setAlternatingRowColors(True)
        self.aktif_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.aktif_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.aktif_table)
        return widget
    
    def _create_yenileme_tab(self) -> QWidget:
        """Yenileme bekleyenler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        self.yenileme_table = QTableWidget()
        self.yenileme_table.setColumnCount(7)
        self.yenileme_table.setHorizontalHeaderLabels([
            "Personel", "Zimmet Türü", "Teslim Tarihi", "Yenileme Tarihi",
            "Gecikme (Gün)", "Durum", "İşlem"
        ])
        self.yenileme_table.setColumnWidth(6, brand.sp(120))
        self.yenileme_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.yenileme_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.yenileme_table.setStyleSheet(self._table_style())
        self.yenileme_table.verticalHeader().setVisible(False)
        self.yenileme_table.setShowGrid(False)
        self.yenileme_table.setAlternatingRowColors(True)
        self.yenileme_table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        
        layout.addWidget(self.yenileme_table)
        return widget
    
    def _create_gecmis_tab(self) -> QWidget:
        """Tüm geçmiş sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        self.gecmis_table = QTableWidget()
        self.gecmis_table.setColumnCount(8)
        self.gecmis_table.setHorizontalHeaderLabels([
            "Zimmet No", "Personel", "Zimmet Türü", "Teslim", "İade", 
            "Miktar", "Durum", "Açıklama"
        ])
        self.gecmis_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.gecmis_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.gecmis_table.setStyleSheet(self._table_style())
        self.gecmis_table.verticalHeader().setVisible(False)
        self.gecmis_table.setShowGrid(False)
        self.gecmis_table.setAlternatingRowColors(True)
        self.gecmis_table.verticalHeader().setDefaultSectionSize(brand.sp(42))

        layout.addWidget(self.gecmis_table)
        return widget
    
    def _input_style(self):
        return f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """

    def _combo_style(self):
        return f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
        """

    def _button_style(self):
        return f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
                min-height: {brand.sp(38)}px;
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
        """

    def _table_style(self):
        return f"""
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
        """

    def _tab_style(self):
        return f"""
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                background: {brand.BG_CARD};
                border-radius: {brand.R_LG}px;
            }}
            QTabBar::tab {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                padding: {brand.SP_3}px {brand.SP_5}px;
                border: 1px solid {brand.BORDER};
                border-bottom: none;
                border-radius: {brand.R_SM}px {brand.R_SM}px 0 0;
                margin-right: {brand.SP_1}px;
                font-size: {brand.FS_BODY}px;
            }}
            QTabBar::tab:selected {{
                background: {brand.BG_CARD};
                border-bottom: 2px solid {brand.PRIMARY};
            }}
        """
    
    def _load_data(self):
        """Zimmet verilerini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            where = ["1=1"]
            params = []
            
            # Durum filtresi
            status = self.status_combo.currentData()
            if status:
                where.append("z.durum = ?")
                params.append(status)
            
            # Kategori filtresi
            kategori = self.kategori_combo.currentData()
            if kategori:
                where.append("zt.kategori = ?")
                params.append(kategori)
            
            # Arama
            search = self.search_input.text().strip()
            if search:
                where.append("(p.ad LIKE ? OR p.soyad LIKE ? OR zt.ad LIKE ?)")
                params.extend([f"%{search}%"] * 3)
            
            where_clause = " AND ".join(where)
            
            # Özet sayıları
            cursor.execute("SELECT COUNT(*) FROM ik.zimmetler WHERE durum = 'TESLIM'")
            teslim = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ik.zimmetler WHERE durum = 'IADE'")
            iade = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM ik.zimmetler 
                WHERE durum = 'TESLIM' AND sonraki_yenileme IS NOT NULL AND sonraki_yenileme <= GETDATE()
            """)
            yenileme = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ik.zimmetler WHERE durum IN ('KAYIP', 'HASARLI')")
            kayip = cursor.fetchone()[0]
            
            # Kartlari guncelle
            self.kart_teslim.findChild(QLabel, "stat_value").setText(str(teslim))
            self.kart_iade.findChild(QLabel, "stat_value").setText(str(iade))
            self.kart_yenileme.findChild(QLabel, "stat_value").setText(str(yenileme))
            self.kart_kayip.findChild(QLabel, "stat_value").setText(str(kayip))
            
            # Aktif zimmetler
            cursor.execute(f"""
                SELECT 
                    z.id, z.zimmet_no, p.ad + ' ' + p.soyad as personel,
                    zt.ad as zimmet_adi, zt.kategori, z.teslim_tarihi,
                    z.miktar, z.beden, z.sonraki_yenileme
                FROM ik.zimmetler z
                JOIN ik.personeller p ON z.personel_id = p.id
                JOIN ik.zimmet_turleri zt ON z.zimmet_turu_id = zt.id
                WHERE z.durum = 'TESLIM' AND {where_clause}
                ORDER BY z.teslim_tarihi DESC
            """, params)
            
            self.aktif_table.setRowCount(0)
            for row in cursor.fetchall():
                row_idx = self.aktif_table.rowCount()
                self.aktif_table.insertRow(row_idx)
                
                # ID sakla
                item = QTableWidgetItem(row[1] or '')
                item.setData(Qt.UserRole, row[0])
                self.aktif_table.setItem(row_idx, 0, item)
                
                self.aktif_table.setItem(row_idx, 1, QTableWidgetItem(row[2] or ''))
                self.aktif_table.setItem(row_idx, 2, QTableWidgetItem(row[3] or ''))
                self.aktif_table.setItem(row_idx, 3, QTableWidgetItem(row[4] or ''))
                
                teslim_tarihi = row[5].strftime('%d.%m.%Y') if row[5] else '-'
                self.aktif_table.setItem(row_idx, 4, QTableWidgetItem(teslim_tarihi))
                
                self.aktif_table.setItem(row_idx, 5, QTableWidgetItem(str(row[6] or 1)))
                self.aktif_table.setItem(row_idx, 6, QTableWidgetItem(row[7] or '-'))
                
                # Yenileme
                if row[8]:
                    yenileme_str = row[8].strftime('%d.%m.%Y')
                    yenileme_item = QTableWidgetItem(yenileme_str)
                    if row[8] <= date.today():
                        yenileme_item.setForeground(QColor(brand.ERROR))
                    self.aktif_table.setItem(row_idx, 7, yenileme_item)
                else:
                    self.aktif_table.setItem(row_idx, 7, QTableWidgetItem('-'))
                
                # Iade butonu
                widget = self.create_action_buttons([
                    ("Iade", "Iade Al", lambda checked, zid=row[0]: self._iade_zimmet(zid), "delete"),
                ])
                self.aktif_table.setCellWidget(row_idx, 8, widget)
            
            # Yenileme bekleyenler
            self._load_yenileme_data(cursor)
            
            # Geçmiş
            self._load_gecmis_data(cursor, where_clause, params)
            
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
    
    def _load_yenileme_data(self, cursor):
        """Yenileme bekleyenleri yükle"""
        cursor.execute("""
            SELECT 
                p.ad + ' ' + p.soyad as personel,
                zt.ad as zimmet_adi,
                z.teslim_tarihi,
                z.sonraki_yenileme,
                z.id
            FROM ik.zimmetler z
            JOIN ik.personeller p ON z.personel_id = p.id
            JOIN ik.zimmet_turleri zt ON z.zimmet_turu_id = zt.id
            WHERE z.durum = 'TESLIM' 
              AND z.sonraki_yenileme IS NOT NULL 
              AND z.sonraki_yenileme <= DATEADD(day, 7, GETDATE())
            ORDER BY z.sonraki_yenileme
        """)
        
        self.yenileme_table.setRowCount(0)
        today = date.today()
        
        for row in cursor.fetchall():
            row_idx = self.yenileme_table.rowCount()
            self.yenileme_table.insertRow(row_idx)
            
            self.yenileme_table.setItem(row_idx, 0, QTableWidgetItem(row[0] or ''))
            self.yenileme_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
            
            teslim = row[2].strftime('%d.%m.%Y') if row[2] else '-'
            self.yenileme_table.setItem(row_idx, 2, QTableWidgetItem(teslim))
            
            yenileme = row[3].strftime('%d.%m.%Y') if row[3] else '-'
            self.yenileme_table.setItem(row_idx, 3, QTableWidgetItem(yenileme))
            
            # Gecikme
            if row[3]:
                gecikme = (today - row[3]).days
                gecikme_item = QTableWidgetItem(str(gecikme) if gecikme > 0 else "0")
                if gecikme > 0:
                    gecikme_item.setForeground(QColor(brand.ERROR))
                self.yenileme_table.setItem(row_idx, 4, gecikme_item)
            
            # Durum
            if row[3] and row[3] < today:
                durum = "GECIKMIS"
                durum_item = QTableWidgetItem(durum)
                durum_item.setForeground(QColor(brand.ERROR))
            else:
                durum = "Yaklasiyor"
                durum_item = QTableWidgetItem(durum)
                durum_item.setForeground(QColor(brand.WARNING))
            self.yenileme_table.setItem(row_idx, 5, durum_item)

            # Yenile butonu
            widget = self.create_action_buttons([
                ("Yenile", "Yenile", lambda checked, zid=row[4]: self._yenile_zimmet(zid), "success"),
            ])
            self.yenileme_table.setCellWidget(row_idx, 6, widget)
    
    def _load_gecmis_data(self, cursor, where_clause, params):
        """Geçmiş verileri yükle"""
        cursor.execute(f"""
            SELECT 
                z.zimmet_no, p.ad + ' ' + p.soyad as personel,
                zt.ad as zimmet_adi, z.teslim_tarihi, z.iade_tarihi,
                z.miktar, z.durum, z.aciklama
            FROM ik.zimmetler z
            JOIN ik.personeller p ON z.personel_id = p.id
            JOIN ik.zimmet_turleri zt ON z.zimmet_turu_id = zt.id
            WHERE {where_clause}
            ORDER BY z.teslim_tarihi DESC
        """, params)
        
        self.gecmis_table.setRowCount(0)
        for row in cursor.fetchall():
            row_idx = self.gecmis_table.rowCount()
            self.gecmis_table.insertRow(row_idx)
            
            self.gecmis_table.setItem(row_idx, 0, QTableWidgetItem(row[0] or ''))
            self.gecmis_table.setItem(row_idx, 1, QTableWidgetItem(row[1] or ''))
            self.gecmis_table.setItem(row_idx, 2, QTableWidgetItem(row[2] or ''))
            
            teslim = row[3].strftime('%d.%m.%Y') if row[3] else '-'
            self.gecmis_table.setItem(row_idx, 3, QTableWidgetItem(teslim))
            
            iade = row[4].strftime('%d.%m.%Y') if row[4] else '-'
            self.gecmis_table.setItem(row_idx, 4, QTableWidgetItem(iade))
            
            self.gecmis_table.setItem(row_idx, 5, QTableWidgetItem(str(row[5] or 1)))
            
            durum_item = QTableWidgetItem(row[6] or '')
            if row[6] == 'TESLIM':
                durum_item.setForeground(QColor(brand.PRIMARY))
            elif row[6] == 'IADE':
                durum_item.setForeground(QColor(brand.SUCCESS))
            elif row[6] in ('KAYIP', 'HASARLI'):
                durum_item.setForeground(QColor(brand.ERROR))
            self.gecmis_table.setItem(row_idx, 6, durum_item)
            
            self.gecmis_table.setItem(row_idx, 7, QTableWidgetItem(row[7] or ''))
    
    def _new_teslim(self):
        """Yeni zimmet teslim"""
        dialog = ZimmetTeslimDialog(self.theme, parent=self)
        if dialog.exec():
            self._load_data()
    
    def _iade_zimmet(self, zimmet_id: int):
        """Zimmet iade al"""
        reply = QMessageBox.question(self, "Onay", "Bu zimmet iade alinacak. Devam edilsin mi?")
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE ik.zimmetler
                    SET durum = 'IADE', iade_tarihi = GETDATE(), guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (zimmet_id,))
                conn.commit()
                LogManager.log_update('ik', 'ik.zimmetler', zimmet_id, 'Zimmet iade alindi')

                self._load_data()
                QMessageBox.information(self, "Basarili", "Zimmet iade alindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Iade hatasi: {e}")
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
    
    def _yenile_zimmet(self, zimmet_id: int):
        """Zimmeti yenile - yeni teslim olustur"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT personel_id, zimmet_turu_id, beden FROM ik.zimmetler WHERE id = ?
            """, (zimmet_id,))
            row = cursor.fetchone()

            if row:
                cursor.execute("""
                    UPDATE ik.zimmetler
                    SET durum = 'IADE', iade_tarihi = GETDATE(), guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (zimmet_id,))

                conn.commit()
                LogManager.log_update('ik', 'ik.zimmetler', zimmet_id, 'Zimmet yenileme icin iade edildi')

                personel_id = row[0]
                # Connection'i kapat, dialog acmadan once
                conn.close()
                conn = None

                dialog = ZimmetTeslimDialog(self.theme, personel_id=personel_id, parent=self)
                if dialog.exec():
                    self._load_data()
                else:
                    self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yenileme hatasi: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def _print_form(self):
        """Zimmet formu yazdır - secili personelin aktif zimmetleri"""
        # Aktif sekmeden secili satirin personel ID'sini al
        table = self.aktif_table
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Lutfen tablodan bir zimmet satiri secin.")
            return

        zimmet_id = table.item(row, 0).data(Qt.UserRole)
        if not zimmet_id:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT personel_id FROM ik.zimmetler WHERE id = ?", (zimmet_id,))
            prow = cursor.fetchone()

            if not prow:
                QMessageBox.warning(self, "Uyari", "Zimmet kaydi bulunamadi.")
                return

            personel_id = prow[0]

            from utils.zimmet_pdf import zimmet_formu_pdf
            pdf_path = zimmet_formu_pdf(personel_id)
            QMessageBox.information(self, "Basarili", f"Zimmet formu olusturuldu:\n{pdf_path}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"PDF olusturma hatasi:\n{e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
