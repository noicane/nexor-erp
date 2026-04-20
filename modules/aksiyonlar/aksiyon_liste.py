# -*- coding: utf-8 -*-
"""
NEXOR ERP - Aksiyon Yönetimi Sistemi
Aksiyon takibi, düzeltici/önleyici faaliyetler, iyileştirme aksiyonları

Özellikler:
- Tüm aksiyonların listelenmesi
- Durum ve öncelik bazlı filtreleme
- Kategori ve modül bazlı filtreleme
- İstatistiksel özet kartları
- Yeni aksiyon oluşturma
- Aksiyon detaylarını görüntüleme ve düzenleme
- Tamamlanma oranı takibi
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen


class _FillBar(QWidget):
    """Pill fill bar — soft arkaplan + accent dolgu + ortada mono yuzde yazisi."""

    def __init__(self, value: int = 0, parent=None):
        from core.nexor_brand import brand as _b
        super().__init__(parent)
        self._b = _b
        self._value = max(0, min(100, int(value)))
        self.setFixedHeight(20)
        self.setMinimumWidth(110)

    def _accent(self) -> str:
        v = self._value
        if v >= 100: return self._b.SUCCESS
        if v >= 60:  return self._b.INFO
        if v > 0:    return self._b.WARNING
        return self._b.TEXT_DIM

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = h / 2.0
        accent = self._accent()

        # Arka plan pill — hafif koyu, kenarı ince accent
        bg = QColor(accent)
        bg.setAlphaF(0.10)
        p.setPen(QPen(QColor(self._b.BORDER_HARD), 1.0))
        p.setBrush(bg)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

        # Dolgu pill
        if self._value > 0:
            fw = max(h, w * self._value / 100.0)
            fill = QColor(accent)
            fill.setAlphaF(0.75)
            p.setPen(Qt.NoPen)
            p.setBrush(fill)
            p.drawRoundedRect(QRectF(0.5, 0.5, fw - 1, h - 1), r, r)

        # Yuzde yazisi — uzerinde varsa beyaz, aksi koyu
        if self._value >= 50:
            text_col = QColor('#FFFFFF')
        else:
            text_col = QColor(self._b.TEXT)
        p.setPen(text_col)
        f = QFont('JetBrains Mono')
        f.setPixelSize(11)
        f.setBold(True)
        p.setFont(f)
        p.drawText(self.rect(), Qt.AlignCenter, f"%{self._value}")
        p.end()

from components.base_page import BasePage
from core.database import execute_query
from modules.aksiyonlar.aksiyon_detay_dialog import AksiyonDetayDialog
from core.nexor_brand import brand


class AksiyonListePage(BasePage):
    """Aksiyon yönetimi ana sayfası"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.theme = theme
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Arayüz oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Başlık
        header = QHBoxLayout()
        title = self.create_section_title("Aksiyon Yönetimi")
        header.addWidget(title)
        header.addStretch()

        # Yeni Aksiyon butonu
        btn_new = self.create_primary_button("+ Yeni Aksiyon")
        btn_new.clicked.connect(self.open_new_aksiyon)
        header.addWidget(btn_new)

        layout.addLayout(header)

        # İstatistik kartları
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(16)

        self.card_toplam = self.create_stat_card("Toplam", "0", color=brand.INFO)
        self.card_bekliyor = self.create_stat_card("Bekliyor", "0", color=brand.WARNING)
        self.card_devam = self.create_stat_card("Devam Ediyor", "0", color=brand.INFO)
        self.card_geciken = self.create_stat_card("Geciken", "0", color=brand.ERROR)
        self.card_tamamlandi = self.create_stat_card("Tamamlandı", "0", color=brand.SUCCESS)

        self.stats_layout.addWidget(self.card_toplam)
        self.stats_layout.addWidget(self.card_bekliyor)
        self.stats_layout.addWidget(self.card_devam)
        self.stats_layout.addWidget(self.card_geciken)
        self.stats_layout.addWidget(self.card_tamamlandi)

        layout.addLayout(self.stats_layout)

        # Filtreler
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        # Durum filtresi
        lbl_durum = QLabel("Durum:")
        lbl_durum.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-weight: 500;")
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems([
            "Tümü",
            "BEKLIYOR",
            "DEVAM_EDIYOR",
            "TAMAMLANDI",
            "DOGRULANDI",
            "GECIKTI",
            "IPTAL"
        ])
        self.cmb_durum.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(lbl_durum)
        filter_layout.addWidget(self.cmb_durum)

        # Öncelik filtresi
        lbl_oncelik = QLabel("Öncelik:")
        lbl_oncelik.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-weight: 500;")
        self.cmb_oncelik = QComboBox()
        self.cmb_oncelik.addItems([
            "Tümü",
            "KRITIK",
            "YUKSEK",
            "NORMAL",
            "DUSUK"
        ])
        self.cmb_oncelik.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(lbl_oncelik)
        filter_layout.addWidget(self.cmb_oncelik)

        # Kategori filtresi
        lbl_kategori = QLabel("Kategori:")
        lbl_kategori.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-weight: 500;")
        self.cmb_kategori = QComboBox()
        self.cmb_kategori.addItems([
            "Tümü",
            "DUZELTICI",
            "ONLEYICI",
            "IYILESTIRME",
            "GENEL"
        ])
        self.cmb_kategori.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(lbl_kategori)
        filter_layout.addWidget(self.cmb_kategori)

        # Modül filtresi
        lbl_modul = QLabel("Modül:")
        lbl_modul.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-weight: 500;")
        self.cmb_modul = QComboBox()
        self.cmb_modul.addItems([
            "Tümü",
            "KALITE",
            "URETIM",
            "BAKIM",
            "ISG",
            "IK",
            "STOK",
            "SEVKIYAT",
            "GENEL"
        ])
        self.cmb_modul.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(lbl_modul)
        filter_layout.addWidget(self.cmb_modul)

        filter_layout.addStretch()

        # Yenile butonu
        btn_refresh = QPushButton("Yenile")
        btn_refresh.clicked.connect(self.load_data)
        filter_layout.addWidget(btn_refresh)

        layout.addLayout(filter_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Aksiyon No",
            "Başlık",
            "Kategori",
            "Modül",
            "Öncelik",
            "Sorumlu",
            "Hedef Tarih",
            "Durum",
            "%",
            "Gecikme (Gün)"
        ])

        # Tablo ayarları
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)  # sol satir numarasi ic ice gorunumu kaldirildi
        self.table.doubleClicked.connect(self.open_edit_aksiyon)

        layout.addWidget(self.table)

    def load_data(self):
        """Aksiyon verilerini yükle"""
        try:
            query = """
                SELECT
                    id AS aksiyon_id,
                    aksiyon_no,
                    baslik,
                    kategori,
                    kaynak_modul,
                    oncelik,
                    sorumlu_adi,
                    hedef_tarih,
                    durum,
                    tamamlanma_orani,
                    gecikme_gun
                FROM sistem.vw_aksiyon_ozet
                ORDER BY
                    CASE durum
                        WHEN 'GECIKTI' THEN 1
                        WHEN 'DEVAM_EDIYOR' THEN 2
                        WHEN 'BEKLIYOR' THEN 3
                        WHEN 'TAMAMLANDI' THEN 4
                        WHEN 'DOGRULANDI' THEN 5
                        ELSE 6
                    END,
                    hedef_tarih ASC
            """
            results = execute_query(query)

            self.all_data = results
            self.apply_filters()
            self.update_stats()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata:\n{str(e)}")

    def apply_filters(self):
        """Filtreleri uygula"""
        if not hasattr(self, 'all_data'):
            return

        filtered_data = self.all_data

        # Durum filtresi
        durum = self.cmb_durum.currentText()
        if durum != "Tümü":
            filtered_data = [r for r in filtered_data if r.get('durum') == durum]

        # Öncelik filtresi
        oncelik = self.cmb_oncelik.currentText()
        if oncelik != "Tümü":
            filtered_data = [r for r in filtered_data if r.get('oncelik') == oncelik]

        # Kategori filtresi
        kategori = self.cmb_kategori.currentText()
        if kategori != "Tümü":
            filtered_data = [r for r in filtered_data if r.get('kategori') == kategori]

        # Modül filtresi
        modul = self.cmb_modul.currentText()
        if modul != "Tümü":
            filtered_data = [r for r in filtered_data if r.get('kaynak_modul') == modul]

        self.populate_table(filtered_data)

    def populate_table(self, data):
        """Tabloyu doldur"""
        self.table.setRowCount(0)

        for row_idx, row_data in enumerate(data):
            self.table.insertRow(row_idx)

            # Aksiyon No
            item = QTableWidgetItem(str(row_data.get('aksiyon_no', '')))
            item.setData(Qt.UserRole, row_data.get('aksiyon_id'))
            self.table.setItem(row_idx, 0, item)

            # Başlık
            item = QTableWidgetItem(str(row_data.get('baslik', '')))
            self.table.setItem(row_idx, 1, item)

            # Kategori
            kategori = str(row_data.get('kategori', ''))
            item = QTableWidgetItem(self.format_kategori(kategori))
            self.table.setItem(row_idx, 2, item)

            # Modül
            item = QTableWidgetItem(str(row_data.get('kaynak_modul', '')))
            self.table.setItem(row_idx, 3, item)

            # Öncelik
            oncelik = str(row_data.get('oncelik', ''))
            item = QTableWidgetItem(self.format_oncelik(oncelik))
            item.setForeground(QColor(self.get_oncelik_color(oncelik)))
            font = QFont()
            font.setBold(True)
            item.setFont(font)
            self.table.setItem(row_idx, 4, item)

            # Sorumlu
            item = QTableWidgetItem(str(row_data.get('sorumlu_adi', '')))
            self.table.setItem(row_idx, 5, item)

            # Hedef Tarih
            hedef = row_data.get('hedef_tarih')
            hedef_str = hedef.strftime('%d.%m.%Y') if hedef else ''
            item = QTableWidgetItem(hedef_str)
            self.table.setItem(row_idx, 6, item)

            # Durum
            durum = str(row_data.get('durum', ''))
            item = QTableWidgetItem(self.format_durum(durum))
            item.setForeground(QColor(self.get_durum_color(durum)))
            font = QFont()
            font.setBold(True)
            item.setFont(font)
            self.table.setItem(row_idx, 7, item)

            # Tamamlanma oranı — pill fill bar (arka plan + soft accent dolgu + mono yuzde)
            oran = int(row_data.get('tamamlanma_orani', 0) or 0)
            bar = _FillBar(oran)
            cell = QWidget()
            cl = QHBoxLayout(cell); cl.setContentsMargins(8, 4, 8, 4); cl.addWidget(bar)
            self.table.setCellWidget(row_idx, 8, cell)

            # Gecikme
            gecikme = row_data.get('gecikme_gun', 0) or 0
            if gecikme > 0:
                item = QTableWidgetItem(str(int(gecikme)))
                item.setForeground(QColor(brand.ERROR))
                font = QFont()
                font.setBold(True)
                item.setFont(font)
            else:
                item = QTableWidgetItem("-")
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 9, item)

    def update_stats(self):
        """İstatistik kartlarını güncelle"""
        if not hasattr(self, 'all_data'):
            return

        data = self.all_data

        toplam = len(data)
        bekliyor = len([r for r in data if r.get('durum') == 'BEKLIYOR'])
        devam = len([r for r in data if r.get('durum') == 'DEVAM_EDIYOR'])
        geciken = len([r for r in data if r.get('durum') == 'GECIKTI'])
        tamamlandi = len([r for r in data if r.get('durum') in ('TAMAMLANDI', 'DOGRULANDI')])

        self.update_stat_card_value(self.card_toplam, str(toplam))
        self.update_stat_card_value(self.card_bekliyor, str(bekliyor))
        self.update_stat_card_value(self.card_devam, str(devam))
        self.update_stat_card_value(self.card_geciken, str(geciken))
        self.update_stat_card_value(self.card_tamamlandi, str(tamamlandi))

    def update_stat_card_value(self, card: QFrame, value: str):
        """Stat kartının değerini güncelle (stat_value objectName üzerinden)."""
        value_label = card.findChild(QLabel, "stat_value")
        if value_label is not None:
            value_label.setText(value)

    def format_kategori(self, kategori: str) -> str:
        """Kategori formatlama"""
        mapping = {
            'DUZELTICI': 'Düzeltici',
            'ONLEYICI': 'Önleyici',
            'IYILESTIRME': 'İyileştirme',
            'GENEL': 'Genel'
        }
        return mapping.get(kategori, kategori)

    def format_oncelik(self, oncelik: str) -> str:
        """Öncelik formatlama"""
        mapping = {
            'KRITIK': 'KRİTİK',
            'YUKSEK': 'YÜKSEK',
            'NORMAL': 'NORMAL',
            'DUSUK': 'DÜŞÜK'
        }
        return mapping.get(oncelik, oncelik)

    def format_durum(self, durum: str) -> str:
        """Durum formatlama"""
        mapping = {
            'BEKLIYOR': 'Bekliyor',
            'DEVAM_EDIYOR': 'Devam Ediyor',
            'TAMAMLANDI': 'Tamamlandı',
            'DOGRULANDI': 'Doğrulandı',
            'GECIKTI': 'Gecikti',
            'IPTAL': 'İptal'
        }
        return mapping.get(durum, durum)

    def get_oncelik_color(self, oncelik: str) -> str:
        """Öncelik rengi"""
        colors = {
            'KRITIK': brand.ERROR,
            'YUKSEK': brand.WARNING,
            'NORMAL': brand.INFO,
            'DUSUK': brand.TEXT_DIM
        }
        return colors.get(oncelik, brand.TEXT)

    def get_durum_color(self, durum: str) -> str:
        """Durum rengi"""
        colors = {
            'BEKLIYOR': brand.INFO,
            'DEVAM_EDIYOR': brand.WARNING,
            'TAMAMLANDI': brand.SUCCESS,
            'DOGRULANDI': brand.SUCCESS,
            'GECIKTI': brand.ERROR,
            'IPTAL': brand.TEXT_DIM
        }
        return colors.get(durum, brand.TEXT)

    def open_new_aksiyon(self):
        """Yeni aksiyon oluştur"""
        dialog = AksiyonDetayDialog(self.theme, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()

    def open_edit_aksiyon(self):
        """Aksiyon düzenle"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        aksiyon_id = self.table.item(current_row, 0).data(Qt.UserRole)
        dialog = AksiyonDetayDialog(self.theme, aksiyon_id=aksiyon_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
