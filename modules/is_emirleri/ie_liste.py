# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İş Emri Liste Sayfası
[MODERNIZED UI - v3.0]
"""
import os
import sys
from datetime import datetime, date

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QDateEdit, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand
from config import DEFAULT_PAGE_SIZE


class IsEmriListePage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.page_size = DEFAULT_PAGE_SIZE
        self.current_page = 1
        self.total_pages = 1
        self.total_items = 0
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    # ── ORTAK STİL HELPER'LARI ──
    def _input_style(self) -> str:
        return f"""
            QLineEdit, QDateEdit, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY_SM}px;
            }}
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {{
                border-color: {brand.PRIMARY};
                background: {brand.BG_HOVER};
            }}
            QComboBox:hover {{ border-color: {brand.BORDER_HARD}; }}
            QComboBox::drop-down {{ border: none; width: {brand.sp(24)}px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                selection-background-color: {brand.PRIMARY};
                outline: 0;
                padding: {brand.SP_1}px;
            }}
        """

    def _secondary_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background: {brand.BG_INPUT};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
            }}
            QPushButton:pressed {{ background: {brand.BG_SELECTED}; }}
            QPushButton:disabled {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_DISABLED};
            }}
        """

    def _setup_ui(self):
        self.setStyleSheet(f"IsEmriListePage {{ background: {brand.BG_MAIN}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        layout.addWidget(self._create_header())
        layout.addWidget(self._create_toolbar())
        self.table = self._create_table()
        layout.addWidget(self.table, 1)
        layout.addWidget(self._create_bottom_bar())

    def _create_header(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(brand.SP_1, 0, brand.SP_1, 0)
        layout.setSpacing(brand.SP_3)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_1)

        title = QLabel("İş Emirleri")
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_TITLE_LG}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"letter-spacing: -0.4px; "
            f"background: transparent;"
        )
        title_col.addWidget(title)

        subtitle = QLabel("Tüm iş emirlerini görüntüleyin ve yönetin")
        subtitle.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY}px; "
            f"background: transparent;"
        )
        title_col.addWidget(subtitle)

        layout.addLayout(title_col)
        layout.addStretch()

        new_btn = QPushButton("+ Yeni İş Emri")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setFixedHeight(brand.sp(40))
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        new_btn.clicked.connect(self._new_is_emri)
        layout.addWidget(new_btn)
        return wrapper

    def _create_toolbar(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(brand.SP_3)

        input_style = self._input_style()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara (iş emri, müşteri, stok)")
        self.search_input.setFixedHeight(brand.sp(40))
        self.search_input.setMinimumWidth(brand.sp(260))
        self.search_input.setStyleSheet(input_style)
        self.search_input.returnPressed.connect(self._load_data)
        layout.addWidget(self.search_input)

        self.tarih_bas = QDateEdit()
        self.tarih_bas.setDate(QDate.currentDate().addDays(-30))
        self.tarih_bas.setCalendarPopup(True)
        self.tarih_bas.setFixedHeight(brand.sp(40))
        self.tarih_bas.setFixedWidth(brand.sp(130))
        self.tarih_bas.setStyleSheet(input_style)
        self.tarih_bas.dateChanged.connect(self._filter_changed)
        layout.addWidget(self.tarih_bas)

        sep = QLabel("—")
        sep.setStyleSheet(f"color: {brand.TEXT_DIM}; background: transparent;")
        layout.addWidget(sep)

        self.tarih_bit = QDateEdit()
        self.tarih_bit.setDate(QDate.currentDate().addDays(30))
        self.tarih_bit.setCalendarPopup(True)
        self.tarih_bit.setFixedHeight(brand.sp(40))
        self.tarih_bit.setFixedWidth(brand.sp(130))
        self.tarih_bit.setStyleSheet(input_style)
        self.tarih_bit.dateChanged.connect(self._filter_changed)
        layout.addWidget(self.tarih_bit)

        self.durum_combo = QComboBox()
        self.durum_combo.addItem("Tüm Durumlar", "")
        self.durum_combo.addItem("Bekliyor", "BEKLIYOR")
        self.durum_combo.addItem("Planlandı", "PLANLI")
        self.durum_combo.addItem("Üretimde", "URETIMDE")
        self.durum_combo.addItem("Tamamlandı", "TAMAMLANDI")
        self.durum_combo.setFixedHeight(brand.sp(40))
        self.durum_combo.setMinimumWidth(brand.sp(150))
        self.durum_combo.setStyleSheet(input_style)
        self.durum_combo.currentIndexChanged.connect(self._filter_changed)
        layout.addWidget(self.durum_combo)

        search_btn = QPushButton("Ara")
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.setFixedHeight(brand.sp(40))
        search_btn.setStyleSheet(self._secondary_btn_style())
        search_btn.clicked.connect(self._load_data)
        layout.addWidget(search_btn)

        pdf_btn = QPushButton("PDF")
        pdf_btn.setCursor(Qt.PointingHandCursor)
        pdf_btn.setFixedHeight(brand.sp(40))
        pdf_btn.setStyleSheet(self._secondary_btn_style())
        pdf_btn.clicked.connect(self._export_pdf)
        layout.addWidget(pdf_btn)

        birlesik_btn = QPushButton("Birleşik Çıktı")
        birlesik_btn.setCursor(Qt.PointingHandCursor)
        birlesik_btn.setFixedHeight(brand.sp(40))
        birlesik_btn.setToolTip("Seçili iş emirleri + depo çıkış emirlerini tek kağıtta listele")
        birlesik_btn.setStyleSheet(self._secondary_btn_style())
        birlesik_btn.clicked.connect(self._birlesik_cikti)
        layout.addWidget(birlesik_btn)

        layout.addWidget(self.create_export_button(title="Is Emirleri"))

        layout.addStretch()
        return wrapper

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels([
            "İş Emri No", "Termin", "Müşteri", "Ürün", "Kaplama",
            "Miktar", "Bara", "Hat", "Durum", "Oluşturma"
        ])
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                gridline-color: {brand.BORDER};
                font-size: {brand.FS_BODY_SM}px;
                outline: 0;
            }}
            QTableWidget::item {{
                padding: {brand.SP_2}px {brand.SP_3}px;
                background: transparent;
            }}
            QTableWidget::item:selected {{
                background: {brand.PRIMARY_SOFT};
                color: {brand.TEXT};
            }}
            QHeaderView::section {{
                background: {brand.BG_ELEVATED};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_2}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_CAPTION}px;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }}
        """)
        header = table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        table.setColumnWidth(0, brand.sp(140))
        table.setColumnWidth(1, brand.sp(100))
        table.setColumnWidth(4, brand.sp(100))
        table.setColumnWidth(5, brand.sp(80))
        table.setColumnWidth(6, brand.sp(70))
        table.setColumnWidth(7, brand.sp(80))
        table.setColumnWidth(8, brand.sp(100))
        table.setColumnWidth(9, brand.sp(100))
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(brand.sp(40))
        table.setAlternatingRowColors(False)
        table.setShowGrid(False)
        table.setFrameShape(QFrame.NoFrame)
        table.doubleClicked.connect(self._open_detail)
        return table

    def _create_bottom_bar(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(brand.SP_1, 0, brand.SP_1, 0)

        self.stat_label = QLabel("Yükleniyor...")
        self.stat_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"background: transparent;"
        )
        layout.addWidget(self.stat_label)
        layout.addStretch()

        btn_style = self._secondary_btn_style()

        self.prev_btn = QPushButton("◀  Önceki")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setFixedHeight(brand.sp(32))
        self.prev_btn.setStyleSheet(btn_style)
        self.prev_btn.clicked.connect(self._prev_page)
        layout.addWidget(self.prev_btn)

        self.page_label = QLabel("1 / 1")
        self.page_label.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"padding: 0 {brand.SP_3}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"background: transparent;"
        )
        layout.addWidget(self.page_label)

        self.next_btn = QPushButton("Sonraki  ▶")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setFixedHeight(brand.sp(32))
        self.next_btn.setStyleSheet(btn_style)
        self.next_btn.clicked.connect(self._next_page)
        layout.addWidget(self.next_btn)
        return wrapper
    
    def _load_data(self):
        self.stat_label.setText("Yükleniyor...")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """SELECT id, is_emri_no, termin_tarihi, cari_unvani, stok_kodu, stok_adi, kaplama_tipi, toplam_miktar, birim, toplam_bara, hat_id, durum, olusturma_tarihi FROM siparis.is_emirleri WHERE silindi_mi = 0 ORDER BY id DESC"""
            cursor.execute(sql)
            items = []
            for row in cursor.fetchall():
                item = []
                for i in range(13):
                    try:
                        item.append(row[i])
                    except Exception:
                        item.append(None)
                items.append(item)
            conn.close()
            
            arama = self.search_input.text().strip().lower()
            durum_filtre = self.durum_combo.currentData() or ""
            tarih_bas = self.tarih_bas.date().toPython()
            tarih_bit = self.tarih_bit.date().toPython()

            filtered = []
            for item in items:
                # Arama filtresi
                if arama:
                    is_emri_no = str(item[1] or '').lower()
                    cari = str(item[3] or '').lower()
                    stok = str(item[4] or '').lower()
                    if arama not in is_emri_no and arama not in cari and arama not in stok:
                        continue
                # Durum filtresi
                if durum_filtre:
                    if str(item[11] or '') != durum_filtre:
                        continue
                # Tarih filtresi (termin tarihine göre)
                termin = item[2]
                if termin:
                    if hasattr(termin, 'date'):
                        termin = termin.date()
                    if termin < tarih_bas or termin > tarih_bit:
                        continue
                filtered.append(item)
            
            self.total_items = len(filtered)
            self.total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)
            start = (self.current_page - 1) * self.page_size
            end = start + self.page_size
            page_items = filtered[start:end]
            self._populate_table(page_items)
            self._update_paging()
            self.stat_label.setText(f"Toplam: {self.total_items} iş emri")
        except Exception as e:
            self.stat_label.setText(f"Hata: {str(e)[:50]}")
            self.table.setRowCount(0)
    
    def _populate_table(self, items):
        self.table.clearSelection()
        self.table.setRowCount(0)
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            no_item = QTableWidgetItem(str(item[1] or ''))
            try:
                id_val = int(item[0]) if item[0] else 0
            except Exception:
                id_val = 0
            no_item.setData(Qt.UserRole, id_val)
            self.table.setItem(row, 0, no_item)

            termin = item[2]
            termin_str = str(termin)[:10] if termin else '-'
            termin_item = QTableWidgetItem(termin_str)
            if termin and termin < date.today():
                termin_item.setForeground(QColor(brand.ERROR))
            self.table.setItem(row, 1, termin_item)

            self.table.setItem(row, 2, QTableWidgetItem(str(item[3] or '')[:25]))
            self.table.setItem(row, 3, QTableWidgetItem(str(item[4] or '')))
            self.table.setItem(row, 4, QTableWidgetItem(str(item[6] or '')))

            miktar = item[7] or 0
            miktar_item = QTableWidgetItem(f"{miktar:,.0f}")
            miktar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, miktar_item)
            self.table.setItem(row, 6, QTableWidgetItem(str(item[9] or '')))
            self.table.setItem(row, 7, QTableWidgetItem('-'))

            durum = item[11] or 'BEKLIYOR'
            durum_item = QTableWidgetItem(durum)
            colors = {
                'BEKLIYOR': brand.WARNING,
                'PLANLI': brand.INFO,
                'URETIMDE': brand.SUCCESS,
                'TAMAMLANDI': brand.SUCCESS,
            }
            durum_item.setForeground(QColor(colors.get(durum, brand.TEXT_DIM)))
            self.table.setItem(row, 8, durum_item)

            olusturma = item[12]
            self.table.setItem(row, 9, QTableWidgetItem(str(olusturma)[:10] if olusturma else ''))
    
    def _update_paging(self):
        self.page_label.setText(f"{self.current_page} / {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
    
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load_data()
    
    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._load_data()
    
    def _filter_changed(self):
        """Filtre değiştiğinde sayfayı sıfırla ve yeniden yükle"""
        self.current_page = 1
        self._load_data()

    def _export_pdf(self):
        """Seçili iş emrini PDF olarak dışa aktar"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen PDF çıktısı almak için bir iş emri seçin.")
            return
        item = self.table.item(current_row, 0)
        if not item:
            return
        is_emri_id = item.data(Qt.UserRole)
        try:
            is_emri_id = int(is_emri_id) if is_emri_id else None
        except Exception:
            is_emri_id = None
        if not is_emri_id:
            return
        try:
            from utils.is_emri_pdf import is_emri_pdf_olustur
            is_emri_pdf_olustur(is_emri_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturma hatası: {e}")

    def _birlesik_cikti(self):
        """Seçili iş emirleri + depo çıkış emirlerini tek kağıtta listele"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir iş emri seçin.\n(Ctrl+Click ile çoklu seçim yapabilirsiniz)")
            return

        is_emri_ids = []
        for row in sorted(selected_rows):
            item = self.table.item(row, 0)
            if item:
                ie_id = item.data(Qt.UserRole)
                if ie_id:
                    try:
                        is_emri_ids.append(int(ie_id))
                    except (ValueError, TypeError):
                        pass

        if not is_emri_ids:
            return

        try:
            from utils.birlesik_is_emri_depo_cikis_pdf import birlesik_pdf_olustur_ve_ac
            birlesik_pdf_olustur_ve_ac(is_emri_ids)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Birleşik PDF hatası: {e}")

    def _new_is_emri(self):
        from modules.is_emirleri.ie_yeni import IsEmriYeniPage
        dialog = IsEmriYeniPage(theme=self.theme, parent=self)
        if dialog.exec():
            self._load_data()
    
    def _open_detail(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        item = self.table.item(current_row, 0)
        if not item:
            return
        is_emri_id = item.data(Qt.UserRole)
        try:
            is_emri_id = int(is_emri_id) if is_emri_id else None
        except Exception:
            is_emri_id = None
        if is_emri_id:
            from modules.is_emirleri.ie_yeni import IsEmriYeniPage
            dialog = IsEmriYeniPage(is_emri_id=is_emri_id, theme=self.theme, parent=self)
            if dialog.exec():
                self._load_data()
