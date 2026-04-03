# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İrsaliye İade Girişi
Müşteriden geri dönen malzeme kaydı
"""
from datetime import datetime, date
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QDateEdit,
    QDialog, QGridLayout, QTextEdit, QSpinBox, QDoubleSpinBox,
    QSplitter, QWidget, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, QDate, Signal
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from components.dialog_minimize_bar import add_minimize_button
from core.database import get_db_connection
from core.log_manager import LogManager


# ============================================================================
# İADE NUMARA ÜRETİCİ
# ============================================================================

def _iade_no_uret(cursor) -> str:
    """Yeni iade numarası üret: IAD-YYYY-NNNN"""
    yil = datetime.now().year
    cursor.execute("""
        SELECT MAX(iade_no) FROM siparis.iade_irsaliyeleri
        WHERE iade_no LIKE ?
    """, (f'IAD-{yil}-%',))
    row = cursor.fetchone()
    if row and row[0]:
        try:
            son_sira = int(row[0].split('-')[-1])
        except (ValueError, IndexError):
            son_sira = 0
    else:
        son_sira = 0
    return f"IAD-{yil}-{son_sira + 1:04d}"


# ============================================================================
# REFERANS İRSALİYE SEÇİM DİALOGU
# ============================================================================

class IrsaliyeSecDialog(QDialog):
    """Çıkış irsaliyesi seçim dialog'u"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.secilen = None
        self.setWindowTitle("Referans İrsaliye Seç")
        self.setMinimumSize(800, 500)
        self._setup_ui()
        self._load_data()
        add_minimize_button(self)

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("📄 Referans Çıkış İrsaliyesi Seçin")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)

        # Arama
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("İrsaliye no, müşteri ara...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
        """)
        self.search_input.textChanged.connect(self._filter)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "İrsaliye No", "Tarih", "Müşteri", "Adet", "Durum"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
            QTableWidget::item:selected {{
                background: {self.theme.get('primary')};
            }}
        """)
        self.table.doubleClicked.connect(self._sec)
        layout.addWidget(self.table, 1)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 10px 20px;
            }}
        """)
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)

        sec_btn = QPushButton("Seç")
        sec_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
        """)
        sec_btn.clicked.connect(self._sec)
        btn_layout.addWidget(sec_btn)

        layout.addLayout(btn_layout)

    def _load_data(self):
        self._all_rows = []
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    ci.id, ci.irsaliye_no, ci.tarih,
                    COALESCE(c.unvan, c.kisa_ad, 'Tanımsız') as musteri,
                    (SELECT ISNULL(SUM(miktar),0) FROM siparis.cikis_irsaliye_satirlar WHERE irsaliye_id = ci.id) as toplam,
                    ci.durum, ci.cari_id
                FROM siparis.cikis_irsaliyeleri ci
                LEFT JOIN musteri.cariler c ON ci.cari_id = c.id
                WHERE ci.durum IN ('SEVK_EDILDI','TESLIM_EDILDI')
                  AND (ci.silindi_mi = 0 OR ci.silindi_mi IS NULL)
                ORDER BY ci.tarih DESC
            """)
            self._all_rows = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"İrsaliye yükleme hatası: {e}")

        self._display(self._all_rows)

    def _display(self, rows):
        self.table.setRowCount(0)
        for row in rows:
            idx = self.table.rowCount()
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(idx, 1, QTableWidgetItem(row[1] or ''))
            tarih = row[2].strftime('%d.%m.%Y') if row[2] else '-'
            self.table.setItem(idx, 2, QTableWidgetItem(tarih))
            self.table.setItem(idx, 3, QTableWidgetItem(row[3] or ''))
            item = QTableWidgetItem(f"{row[4]:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(idx, 4, item)
            durum_map = {'SEVK_EDILDI': '🚚 Sevk Edildi', 'TESLIM_EDILDI': '✅ Teslim Edildi'}
            self.table.setItem(idx, 5, QTableWidgetItem(durum_map.get(row[5], row[5])))

    def _filter(self):
        text = self.search_input.text().lower().strip()
        if not text:
            self._display(self._all_rows)
            return
        filtered = [r for r in self._all_rows if text in f"{r[1]} {r[3]}".lower()]
        self._display(filtered)

    def _sec(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        irsaliye_id = int(self.table.item(row, 0).text())
        # Referans satırından tüm bilgiyi bul
        for r in self._all_rows:
            if r[0] == irsaliye_id:
                self.secilen = {
                    'id': r[0], 'irsaliye_no': r[1], 'tarih': r[2],
                    'musteri': r[3], 'toplam': r[4], 'durum': r[5],
                    'cari_id': r[6]
                }
                break
        self.accept()


# ============================================================================
# ANA SAYFA - İADE İRSALİYE
# ============================================================================

class SevkIadePage(BasePage):
    """İrsaliye İade Girişi Sayfası"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.ref_irsaliye = None
        self.ref_satirlar = []
        self.iade_satirlar = []  # Seçilen iade satırları
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()

        title = QLabel("📦 İrsaliye İade Girişi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        header.addWidget(title)
        header.addStretch()

        temizle_btn = QPushButton("🗑️ Temizle")
        temizle_btn.setStyleSheet(self._button_style())
        temizle_btn.clicked.connect(self._temizle)
        header.addWidget(temizle_btn)

        layout.addLayout(header)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)

        # SOL PANEL - Referans irsaliye & iade bilgileri
        sol = QWidget()
        sol_layout = QVBoxLayout(sol)
        sol_layout.setContentsMargins(0, 0, 0, 0)
        sol_layout.setSpacing(12)

        # Referans irsaliye seçimi
        ref_frame = QFrame()
        ref_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        ref_layout = QVBoxLayout(ref_frame)
        ref_layout.setContentsMargins(16, 16, 16, 16)
        ref_layout.setSpacing(8)

        ref_header = QHBoxLayout()
        ref_title = QLabel("📄 Referans İrsaliye")
        ref_title.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold; font-size: 14px;")
        ref_header.addWidget(ref_title)
        ref_header.addStretch()

        self.ref_sec_btn = QPushButton("İrsaliye Seç")
        self.ref_sec_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
        """)
        self.ref_sec_btn.clicked.connect(self._irsaliye_sec)
        ref_header.addWidget(self.ref_sec_btn)
        ref_layout.addLayout(ref_header)

        # Referans bilgi grid
        ref_grid = QGridLayout()
        ref_grid.setSpacing(6)
        self.ref_labels = {}
        for i, (key, label) in enumerate([
            ('no', 'İrsaliye No:'), ('tarih', 'Tarih:'),
            ('musteri', 'Müşteri:'), ('adet', 'Toplam Adet:')
        ]):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px;")
            ref_grid.addWidget(lbl, i, 0)
            val = QLabel("-")
            val.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold; font-size: 12px;")
            ref_grid.addWidget(val, i, 1)
            self.ref_labels[key] = val
        ref_layout.addLayout(ref_grid)
        sol_layout.addWidget(ref_frame)

        # İade bilgileri
        iade_frame = QFrame()
        iade_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        iade_layout = QVBoxLayout(iade_frame)
        iade_layout.setContentsMargins(16, 16, 16, 16)
        iade_layout.setSpacing(8)

        iade_title = QLabel("📝 İade Bilgileri")
        iade_title.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold; font-size: 14px;")
        iade_layout.addWidget(iade_title)

        input_style = f"""
            QLineEdit, QTextEdit, QDateEdit {{
                background: {self.theme.get('bg_input')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text')};
            }}
        """

        form = QGridLayout()
        form.setSpacing(8)

        form.addWidget(QLabel("Tarih:"), 0, 0)
        self.tarih_input = QDateEdit()
        self.tarih_input.setDate(QDate.currentDate())
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setStyleSheet(input_style)
        form.addWidget(self.tarih_input, 0, 1)

        form.addWidget(QLabel("Araç Plaka:"), 1, 0)
        self.plaka_input = QLineEdit()
        self.plaka_input.setStyleSheet(input_style)
        form.addWidget(self.plaka_input, 1, 1)

        form.addWidget(QLabel("Şoför:"), 2, 0)
        self.sofor_input = QLineEdit()
        self.sofor_input.setStyleSheet(input_style)
        form.addWidget(self.sofor_input, 2, 1)

        form.addWidget(QLabel("Teslim Alan:"), 3, 0)
        self.teslim_alan_input = QLineEdit()
        self.teslim_alan_input.setStyleSheet(input_style)
        form.addWidget(self.teslim_alan_input, 3, 1)

        form.addWidget(QLabel("İade Nedeni:"), 4, 0)
        self.neden_input = QTextEdit()
        self.neden_input.setMaximumHeight(80)
        self.neden_input.setStyleSheet(input_style)
        form.addWidget(self.neden_input, 4, 1)

        for i in range(5):
            lbl = form.itemAtPosition(i, 0)
            if lbl and lbl.widget():
                lbl.widget().setStyleSheet(f"color: {self.theme.get('text')}; font-size: 12px;")

        iade_layout.addLayout(form)
        sol_layout.addWidget(iade_frame)
        sol_layout.addStretch()

        splitter.addWidget(sol)

        # SAĞ PANEL - Satır seçimi
        sag = QWidget()
        sag_layout = QVBoxLayout(sag)
        sag_layout.setContentsMargins(0, 0, 0, 0)
        sag_layout.setSpacing(12)

        satirlar_frame = QFrame()
        satirlar_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        satirlar_layout = QVBoxLayout(satirlar_frame)
        satirlar_layout.setContentsMargins(16, 16, 16, 16)
        satirlar_layout.setSpacing(8)

        sat_header = QHBoxLayout()
        sat_title = QLabel("📋 İade Edilecek Kalemler")
        sat_title.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold; font-size: 14px;")
        sat_header.addWidget(sat_title)

        sat_header.addStretch()

        self.tumunu_sec_btn = QPushButton("Tümünü Seç")
        self.tumunu_sec_btn.setStyleSheet(self._button_style())
        self.tumunu_sec_btn.clicked.connect(self._tumunu_sec)
        sat_header.addWidget(self.tumunu_sec_btn)

        satirlar_layout.addLayout(sat_header)

        # Satır tablosu
        self.satirlar_table = QTableWidget()
        self.satirlar_table.setColumnCount(7)
        self.satirlar_table.setHorizontalHeaderLabels([
            "Seç", "Stok Kodu", "Ürün Adı", "Lot No", "Sevk Mik.", "İade Mik.", "Neden"
        ])
        self.satirlar_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.satirlar_table.setColumnWidth(0, 40)
        self.satirlar_table.setColumnWidth(1, 100)
        self.satirlar_table.setColumnWidth(3, 120)
        self.satirlar_table.setColumnWidth(4, 80)
        self.satirlar_table.setColumnWidth(5, 80)
        self.satirlar_table.setColumnWidth(6, 120)
        self.satirlar_table.verticalHeader().setVisible(False)
        self.satirlar_table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_main')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
        """)
        satirlar_layout.addWidget(self.satirlar_table, 1)

        # Toplam
        toplam_layout = QHBoxLayout()
        toplam_layout.addStretch()
        self.toplam_label = QLabel("Seçili: 0 kalem, 0 adet")
        self.toplam_label.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold;")
        toplam_layout.addWidget(self.toplam_label)
        satirlar_layout.addLayout(toplam_layout)

        sag_layout.addWidget(satirlar_frame, 1)

        # Kaydet butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.kaydet_btn = QPushButton("💾 İade Kaydet")
        self.kaydet_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 32px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_muted')};
            }}
        """)
        self.kaydet_btn.clicked.connect(self._kaydet)
        self.kaydet_btn.setEnabled(False)
        btn_layout.addWidget(self.kaydet_btn)
        sag_layout.addLayout(btn_layout)

        splitter.addWidget(sag)
        splitter.setSizes([350, 650])

        layout.addWidget(splitter, 1)

    # =========================================================================
    # YARDIMCI STYLE
    # =========================================================================

    def _button_style(self):
        return f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {self.theme.get('bg_hover')};
            }}
        """

    # =========================================================================
    # İRSALİYE SEÇ
    # =========================================================================

    def _irsaliye_sec(self):
        dialog = IrsaliyeSecDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted and dialog.secilen:
            self.ref_irsaliye = dialog.secilen
            self._ref_goster()
            self._satirlari_yukle()

    def _ref_goster(self):
        if not self.ref_irsaliye:
            return
        ref = self.ref_irsaliye
        self.ref_labels['no'].setText(ref['irsaliye_no'] or '-')
        tarih = ref['tarih'].strftime('%d.%m.%Y') if ref['tarih'] else '-'
        self.ref_labels['tarih'].setText(tarih)
        self.ref_labels['musteri'].setText(ref['musteri'] or '-')
        self.ref_labels['adet'].setText(f"{ref['toplam']:,.0f}")
        self.kaydet_btn.setEnabled(True)

    def _satirlari_yukle(self):
        """Referans irsaliyenin satırlarını tabloya yükle"""
        if not self.ref_irsaliye:
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    cis.id,
                    COALESCE(ie.stok_kodu, u.urun_kodu, '') as stok_kodu,
                    COALESCE(ie.stok_adi, u.urun_adi, '') as stok_adi,
                    cis.lot_no,
                    cis.miktar,
                    COALESCE(b.kod, 'AD') as birim,
                    cis.urun_id
                FROM siparis.cikis_irsaliye_satirlar cis
                LEFT JOIN siparis.is_emirleri ie ON cis.is_emri_id = ie.id
                LEFT JOIN stok.urunler u ON cis.urun_id = u.id
                LEFT JOIN tanim.birimler b ON cis.birim_id = b.id
                WHERE cis.irsaliye_id = ?
                ORDER BY cis.satir_no
            """, (self.ref_irsaliye['id'],))

            self.ref_satirlar = cursor.fetchall()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Satırlar yüklenemedi: {e}")
            return

        self.satirlar_table.setRowCount(0)
        for row in self.ref_satirlar:
            idx = self.satirlar_table.rowCount()
            self.satirlar_table.insertRow(idx)

            # Checkbox
            chk = QCheckBox()
            chk.stateChanged.connect(self._toplam_guncelle)
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            self.satirlar_table.setCellWidget(idx, 0, chk_widget)

            self.satirlar_table.setItem(idx, 1, QTableWidgetItem(row[1] or ''))
            self.satirlar_table.setItem(idx, 2, QTableWidgetItem(row[2] or ''))
            self.satirlar_table.setItem(idx, 3, QTableWidgetItem(row[3] or ''))

            sevk_item = QTableWidgetItem(f"{row[4]:,.0f}")
            sevk_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.satirlar_table.setItem(idx, 4, sevk_item)

            # İade miktar (SpinBox)
            spin = QDoubleSpinBox()
            spin.setDecimals(0)
            spin.setRange(0, float(row[4] or 0))
            spin.setValue(float(row[4] or 0))
            spin.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background: {self.theme.get('bg_input')};
                    border: 1px solid {self.theme.get('border')};
                    border-radius: 4px;
                    padding: 4px;
                    color: {self.theme.get('text')};
                }}
            """)
            spin.valueChanged.connect(self._toplam_guncelle)
            self.satirlar_table.setCellWidget(idx, 5, spin)

            # Neden
            neden = QLineEdit()
            neden.setPlaceholderText("Neden...")
            neden.setStyleSheet(f"""
                QLineEdit {{
                    background: {self.theme.get('bg_input')};
                    border: 1px solid {self.theme.get('border')};
                    border-radius: 4px;
                    padding: 4px;
                    color: {self.theme.get('text')};
                }}
            """)
            self.satirlar_table.setCellWidget(idx, 6, neden)

            self.satirlar_table.setRowHeight(idx, 40)

    # =========================================================================
    # TOPLU SEÇİM & TOPLAM
    # =========================================================================

    def _tumunu_sec(self):
        all_checked = True
        for i in range(self.satirlar_table.rowCount()):
            chk_widget = self.satirlar_table.cellWidget(i, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk and not chk.isChecked():
                    all_checked = False
                    break

        for i in range(self.satirlar_table.rowCount()):
            chk_widget = self.satirlar_table.cellWidget(i, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk:
                    chk.setChecked(not all_checked)

    def _toplam_guncelle(self):
        kalem = 0
        toplam = 0
        for i in range(self.satirlar_table.rowCount()):
            chk_widget = self.satirlar_table.cellWidget(i, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk and chk.isChecked():
                    spin = self.satirlar_table.cellWidget(i, 5)
                    if spin:
                        kalem += 1
                        toplam += spin.value()
        self.toplam_label.setText(f"Seçili: {kalem} kalem, {toplam:,.0f} adet")

    # =========================================================================
    # KAYDET
    # =========================================================================

    def _kaydet(self):
        if not self.ref_irsaliye:
            QMessageBox.warning(self, "Uyarı", "Önce referans irsaliye seçin!")
            return

        # Seçili satırları topla
        secili = []
        for i in range(self.satirlar_table.rowCount()):
            chk_widget = self.satirlar_table.cellWidget(i, 0)
            if not chk_widget:
                continue
            chk = chk_widget.findChild(QCheckBox)
            if not chk or not chk.isChecked():
                continue

            spin = self.satirlar_table.cellWidget(i, 5)
            miktar = spin.value() if spin else 0
            if miktar <= 0:
                continue

            neden_widget = self.satirlar_table.cellWidget(i, 6)
            neden = neden_widget.text().strip() if neden_widget else ''

            ref_row = self.ref_satirlar[i]
            secili.append({
                'ref_satir_id': ref_row[0],
                'stok_kodu': ref_row[1],
                'stok_adi': ref_row[2],
                'lot_no': ref_row[3],
                'miktar': miktar,
                'birim': ref_row[5],
                'urun_id': ref_row[6],
                'neden': neden
            })

        if not secili:
            QMessageBox.warning(self, "Uyarı", "En az bir kalem seçmelisiniz!")
            return

        # Onay
        toplam_mik = sum(s['miktar'] for s in secili)
        reply = QMessageBox.question(
            self, "İade Onayı",
            f"Referans: {self.ref_irsaliye['irsaliye_no']}\n"
            f"Müşteri: {self.ref_irsaliye['musteri']}\n\n"
            f"{len(secili)} kalem, toplam {toplam_mik:,.0f} adet iade edilecek.\n\n"
            f"Stok girişi otomatik yapılacaktır.\n\nDevam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # İade numarası üret
            iade_no = _iade_no_uret(cursor)

            # Ana kayıt
            cursor.execute("""
                INSERT INTO siparis.iade_irsaliyeleri
                    (iade_no, referans_irsaliye_id, cari_id, tarih, iade_nedeni,
                     arac_plaka, sofor_adi, teslim_alan, durum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'KABUL_EDILDI')
            """, (
                iade_no,
                self.ref_irsaliye['id'],
                self.ref_irsaliye['cari_id'],
                self.tarih_input.date().toPython(),
                self.neden_input.toPlainText().strip() or None,
                self.plaka_input.text().strip() or None,
                self.sofor_input.text().strip() or None,
                self.teslim_alan_input.text().strip() or None,
            ))

            cursor.execute("SELECT SCOPE_IDENTITY()")
            iade_id = int(cursor.fetchone()[0])

            # Stok girişi için HareketMotoru
            from core.hareket_motoru import HareketMotoru
            motor = HareketMotoru(conn)

            # SEVK deposu
            cursor.execute("""
                SELECT TOP 1 id FROM tanim.depolar
                WHERE kod IN ('SEV-01', 'SEVK', 'SEV', 'MAMUL') AND aktif_mi = 1
                ORDER BY id
            """)
            sevk_depo_row = cursor.fetchone()
            sevk_depo_id = sevk_depo_row[0] if sevk_depo_row else None

            # Satırları kaydet ve stok girişi yap
            for satir_no, satir in enumerate(secili, 1):
                cursor.execute("""
                    INSERT INTO siparis.iade_irsaliye_satirlar
                        (irsaliye_id, satir_no, urun_id, stok_kodu, stok_adi,
                         lot_no, miktar, birim, iade_nedeni, referans_satir_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    iade_id, satir_no, satir['urun_id'], satir['stok_kodu'],
                    satir['stok_adi'], satir['lot_no'], satir['miktar'],
                    satir['birim'], satir['neden'], satir['ref_satir_id']
                ))

                # Stok girişi
                if satir['lot_no'] and satir['miktar'] > 0:
                    motor.stok_giris(
                        urun_id=satir['urun_id'] or 1,
                        miktar=satir['miktar'],
                        lot_no=satir['lot_no'],
                        depo_id=sevk_depo_id,
                        kalite_durumu='IADE',
                        aciklama=f"İade girişi - {iade_no} (Ref: {self.ref_irsaliye['irsaliye_no']})"
                    )

            conn.commit()
            conn.close()

            LogManager.log_insert(
                'sevkiyat', 'siparis.iade_irsaliyeleri', iade_id,
                f"İade irsaliye: {iade_no}, {len(secili)} kalem, ref: {self.ref_irsaliye['irsaliye_no']}"
            )

            QMessageBox.information(
                self, "Başarılı",
                f"İade irsaliyesi oluşturuldu!\n\n"
                f"İade No: {iade_no}\n"
                f"Referans: {self.ref_irsaliye['irsaliye_no']}\n"
                f"{len(secili)} kalem, toplam {toplam_mik:,.0f} adet\n\n"
                f"Stok girişleri SEVK deposuna yapıldı."
            )

            self._temizle()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"İade kaydedilemedi:\n{e}")

    # =========================================================================
    # TEMİZLE
    # =========================================================================

    def _temizle(self):
        self.ref_irsaliye = None
        self.ref_satirlar = []
        for key in self.ref_labels:
            self.ref_labels[key].setText("-")
        self.satirlar_table.setRowCount(0)
        self.toplam_label.setText("Seçili: 0 kalem, 0 adet")
        self.plaka_input.clear()
        self.sofor_input.clear()
        self.teslim_alan_input.clear()
        self.neden_input.clear()
        self.tarih_input.setDate(QDate.currentDate())
        self.kaydet_btn.setEnabled(False)
