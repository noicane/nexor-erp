# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Teklif Şablon Yönetim Sayfası
Kaplama sektörü teklif şablonları
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QSplitter, QWidget, QGridLayout, QTextEdit, QDoubleSpinBox,
    QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


KAPLAMA_TIPLERI = [
    "", "Çinko", "Nikel", "Krom", "Kataforez", "Fosfat",
    "Bakır", "Kalay", "Altın", "Gümüş", "Anodize",
    "Pasivizasyon", "Siyah Oksit",
]

BIRIMLER = ["ADET", "KG", "M2", "DM2", "LT", "MT"]


class TeklifSablonlarPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.selected_sablon_id = None
        self._setup_ui()
        QTimer.singleShot(100, self._load_sablonlar)

    def _setup_ui(self):
        t = self.theme
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        layout.addWidget(self._create_header())

        # Splitter: Sol (liste) | Sağ (detay)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {t['border']}; width: 2px; }}
        """)

        splitter.addWidget(self._create_left_panel())
        splitter.addWidget(self._create_right_panel())
        splitter.setSizes([350, 650])

        layout.addWidget(splitter)

    def _create_header(self) -> QFrame:
        t = self.theme
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)

        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        title_row = QHBoxLayout()
        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 24px;")
        title_row.addWidget(icon)
        title = QLabel("Teklif Şablonları")
        title.setStyleSheet(f"color: {t['text']}; font-size: 20px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Teklif şablonlarını yönetin ve düzenleyin")
        subtitle.setStyleSheet(f"color: {t['text_secondary']}; font-size: 12px;")
        title_section.addWidget(subtitle)
        layout.addLayout(title_section)
        layout.addStretch()

        new_btn = self.create_success_button("➕ Yeni Şablon")
        new_btn.clicked.connect(self._yeni_sablon)
        layout.addWidget(new_btn)

        return frame

    # ── SOL PANEL (Liste) ──
    def _create_left_panel(self) -> QWidget:
        t = self.theme
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(12)

        lbl = QLabel("Şablon Listesi")
        lbl.setStyleSheet(f"color: {t['text']}; font-size: 14px; font-weight: 600;")
        layout.addWidget(lbl)

        self.sablon_table = QTableWidget()
        self.sablon_table.setColumnCount(3)
        self.sablon_table.setHorizontalHeaderLabels(["Şablon Adı", "Durum", ""])
        header = self.sablon_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.sablon_table.setColumnWidth(1, 60)
        self.sablon_table.setColumnWidth(2, 40)
        self.sablon_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sablon_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sablon_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sablon_table.verticalHeader().setVisible(False)
        self.sablon_table.setAlternatingRowColors(True)
        self.sablon_table.clicked.connect(self._on_sablon_selected)
        layout.addWidget(self.sablon_table)

        return panel

    # ── SAĞ PANEL (Detay) ──
    def _create_right_panel(self) -> QWidget:
        t = self.theme
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(12)

        self.detail_title = QLabel("Şablon seçin...")
        self.detail_title.setStyleSheet(f"color: {t['text']}; font-size: 14px; font-weight: 600;")
        layout.addWidget(self.detail_title)

        self.detail_frame = QFrame()
        self.detail_frame.setFrameShape(QFrame.StyledPanel)
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(20, 20, 20, 20)
        detail_layout.setSpacing(12)

        input_style = f"""
            background: {t.get('bg_input', '#1A1A1A')}; border: 1px solid {t['border']};
            border-radius: 6px; padding: 8px 12px; color: {t['text']}; font-size: 13px;
        """
        label_style = f"color: {t['text']}; font-weight: bold; font-size: 12px;"

        # Şablon bilgileri
        info_grid = QGridLayout()
        info_grid.setSpacing(10)

        lbl = QLabel("Şablon Adı:")
        lbl.setStyleSheet(label_style)
        info_grid.addWidget(lbl, 0, 0)
        self.sablon_adi_input = QLineEdit()
        self.sablon_adi_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        info_grid.addWidget(self.sablon_adi_input, 0, 1, 1, 3)

        lbl = QLabel("Açıklama:")
        lbl.setStyleSheet(label_style)
        info_grid.addWidget(lbl, 1, 0)
        self.sablon_aciklama_input = QLineEdit()
        self.sablon_aciklama_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        info_grid.addWidget(self.sablon_aciklama_input, 1, 1, 1, 3)

        lbl = QLabel("KDV (%):")
        lbl.setStyleSheet(label_style)
        info_grid.addWidget(lbl, 2, 0)
        self.sablon_kdv = QDoubleSpinBox()
        self.sablon_kdv.setRange(0, 100)
        self.sablon_kdv.setValue(20)
        self.sablon_kdv.setStyleSheet(f"QDoubleSpinBox {{ {input_style} }}")
        info_grid.addWidget(self.sablon_kdv, 2, 1)

        lbl = QLabel("İskonto (%):")
        lbl.setStyleSheet(label_style)
        info_grid.addWidget(lbl, 2, 2)
        self.sablon_iskonto = QDoubleSpinBox()
        self.sablon_iskonto.setRange(0, 100)
        self.sablon_iskonto.setStyleSheet(f"QDoubleSpinBox {{ {input_style} }}")
        info_grid.addWidget(self.sablon_iskonto, 2, 3)

        lbl = QLabel("Teslim Süresi:")
        lbl.setStyleSheet(label_style)
        info_grid.addWidget(lbl, 3, 0)
        self.sablon_teslim = QLineEdit()
        self.sablon_teslim.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        info_grid.addWidget(self.sablon_teslim, 3, 1)

        lbl = QLabel("Ödeme Koşulları:")
        lbl.setStyleSheet(label_style)
        info_grid.addWidget(lbl, 3, 2)
        self.sablon_odeme = QLineEdit()
        self.sablon_odeme.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        info_grid.addWidget(self.sablon_odeme, 3, 3)

        lbl = QLabel("Geçerlilik (gün):")
        lbl.setStyleSheet(label_style)
        info_grid.addWidget(lbl, 4, 0)
        self.sablon_gecerlilik = QSpinBox()
        self.sablon_gecerlilik.setRange(1, 365)
        self.sablon_gecerlilik.setValue(30)
        self.sablon_gecerlilik.setStyleSheet(f"QSpinBox {{ {input_style} }}")
        info_grid.addWidget(self.sablon_gecerlilik, 4, 1)

        self.sablon_aktif = QCheckBox("Aktif")
        self.sablon_aktif.setChecked(True)
        self.sablon_aktif.setStyleSheet(f"color: {t['text']}; font-size: 13px;")
        info_grid.addWidget(self.sablon_aktif, 4, 2)

        detail_layout.addLayout(info_grid)

        # Özel Koşullar
        lbl = QLabel("Özel Koşullar:")
        lbl.setStyleSheet(label_style)
        detail_layout.addWidget(lbl)
        self.sablon_ozel = QTextEdit()
        self.sablon_ozel.setMaximumHeight(60)
        self.sablon_ozel.setStyleSheet(f"QTextEdit {{ {input_style} }}")
        detail_layout.addWidget(self.sablon_ozel)

        # Şablon Satırları
        lbl = QLabel("Şablon Satırları:")
        lbl.setStyleSheet(label_style)
        detail_layout.addWidget(lbl)

        # Satır butonları
        satir_btn_row = QHBoxLayout()
        btn_style = f"""
            QPushButton {{ background: {t.get('bg_input', '#1A1A1A')}; color: {t['text']};
                border: 1px solid {t['border']}; border-radius: 6px;
                padding: 6px 14px; font-size: 11px; }}
            QPushButton:hover {{ background: {t['border']}; }}
        """
        add_satir_btn = QPushButton("➕ Satır Ekle")
        add_satir_btn.setCursor(Qt.PointingHandCursor)
        add_satir_btn.setStyleSheet(btn_style)
        add_satir_btn.clicked.connect(self._add_sablon_satir)
        satir_btn_row.addWidget(add_satir_btn)

        del_satir_btn = QPushButton("🗑️ Satır Sil")
        del_satir_btn.setCursor(Qt.PointingHandCursor)
        del_satir_btn.setStyleSheet(btn_style)
        del_satir_btn.clicked.connect(self._del_sablon_satir)
        satir_btn_row.addWidget(del_satir_btn)
        satir_btn_row.addStretch()
        detail_layout.addLayout(satir_btn_row)

        self.satir_table = QTableWidget()
        self.satir_table.setColumnCount(6)
        self.satir_table.setHorizontalHeaderLabels([
            "#", "Kaplama Tipi", "Kalınlık(µm)", "Malzeme", "Birim", "Vars. Fiyat"
        ])
        self.satir_table.setColumnWidth(0, 35)
        self.satir_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.satir_table.setColumnWidth(2, 80)
        self.satir_table.setColumnWidth(3, 80)
        self.satir_table.setColumnWidth(4, 70)
        self.satir_table.setColumnWidth(5, 90)
        self.satir_table.verticalHeader().setVisible(False)
        self.satir_table.setMinimumHeight(120)
        detail_layout.addWidget(self.satir_table)

        # Kaydet / Sil butonları
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        sil_btn = self.create_danger_button("🗑️ Şablonu Sil")
        sil_btn.clicked.connect(self._sil_sablon)
        btn_row.addWidget(sil_btn)

        kaydet_btn = self.create_success_button("💾 Kaydet")
        kaydet_btn.clicked.connect(self._kaydet_sablon)
        btn_row.addWidget(kaydet_btn)

        detail_layout.addLayout(btn_row)

        layout.addWidget(self.detail_frame)
        self.detail_frame.setVisible(False)

        return panel

    # ── VERİ YÜKLEME ──
    def _load_sablonlar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sablon_adi, aktif_mi FROM satislar.teklif_sablonlari
                ORDER BY sablon_adi
            """)
            rows = cursor.fetchall()
            conn.close()

            self.sablon_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                name_item = QTableWidgetItem(str(row[1] or ''))
                name_item.setData(Qt.UserRole, int(row[0]))
                self.sablon_table.setItem(i, 0, name_item)

                aktif = row[2]
                durum_item = QTableWidgetItem("Aktif" if aktif else "Pasif")
                durum_item.setForeground(QColor(self.theme['success'] if aktif else self.theme['error']))
                self.sablon_table.setItem(i, 1, durum_item)

                self.sablon_table.setItem(i, 2, QTableWidgetItem(""))

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Şablon yükleme hatası: {e}")

    def _on_sablon_selected(self):
        current_row = self.sablon_table.currentRow()
        if current_row < 0:
            return
        item = self.sablon_table.item(current_row, 0)
        if not item:
            return
        sablon_id = item.data(Qt.UserRole)
        self.selected_sablon_id = sablon_id
        self._load_sablon_detail(sablon_id)

    def _load_sablon_detail(self, sablon_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sablon_adi, aciklama, varsayilan_kdv_oran, varsayilan_iskonto_oran,
                       varsayilan_teslim_suresi, varsayilan_odeme_kosullari,
                       varsayilan_gecerlilik_gun, varsayilan_ozel_kosullar, aktif_mi
                FROM satislar.teklif_sablonlari WHERE id = ?
            """, (sablon_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return

            self.detail_title.setText(f"📋 {row[0]}")
            self.sablon_adi_input.setText(str(row[0] or ''))
            self.sablon_aciklama_input.setText(str(row[1] or ''))
            self.sablon_kdv.setValue(float(row[2] or 20))
            self.sablon_iskonto.setValue(float(row[3] or 0))
            self.sablon_teslim.setText(str(row[4] or ''))
            self.sablon_odeme.setText(str(row[5] or ''))
            self.sablon_gecerlilik.setValue(int(row[6] or 30))
            self.sablon_ozel.setPlainText(str(row[7] or ''))
            self.sablon_aktif.setChecked(bool(row[8]))

            # Satırları yükle
            cursor.execute("""
                SELECT id, satir_no, kaplama_tipi_adi, kalinlik_mikron,
                       malzeme_tipi, birim, varsayilan_birim_fiyat
                FROM satislar.teklif_sablon_satirlari WHERE sablon_id = ? ORDER BY satir_no
            """, (sablon_id,))
            satirlar = cursor.fetchall()
            conn.close()

            self.satir_table.setRowCount(0)
            for s in satirlar:
                self._add_sablon_satir_data(
                    kaplama=str(s[2] or ''), kalinlik=s[3],
                    malzeme=str(s[4] or ''), birim=str(s[5] or 'ADET'),
                    fiyat=float(s[6] or 0)
                )

            self.detail_frame.setVisible(True)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Şablon detay hatası: {e}")

    def _add_sablon_satir(self):
        self._add_sablon_satir_data()

    def _add_sablon_satir_data(self, kaplama='', kalinlik=None, malzeme='', birim='ADET', fiyat=0):
        t = self.theme
        row = self.satir_table.rowCount()
        self.satir_table.setRowCount(row + 1)

        no_item = QTableWidgetItem(str(row + 1))
        no_item.setFlags(no_item.flags() & ~Qt.ItemIsEditable)
        no_item.setTextAlignment(Qt.AlignCenter)
        self.satir_table.setItem(row, 0, no_item)

        # Kaplama combo
        kaplama_combo = QComboBox()
        kaplama_combo.addItems(KAPLAMA_TIPLERI)
        kaplama_combo.setStyleSheet(f"background: {t.get('bg_input', '#1A1A1A')}; color: {t['text']}; border: none; padding: 4px;")
        if kaplama:
            idx = kaplama_combo.findText(kaplama)
            if idx >= 0:
                kaplama_combo.setCurrentIndex(idx)
        self.satir_table.setCellWidget(row, 1, kaplama_combo)

        self.satir_table.setItem(row, 2, QTableWidgetItem(str(kalinlik) if kalinlik else ''))
        self.satir_table.setItem(row, 3, QTableWidgetItem(malzeme))

        birim_combo = QComboBox()
        birim_combo.addItems(BIRIMLER)
        birim_combo.setStyleSheet(f"background: {t.get('bg_input', '#1A1A1A')}; color: {t['text']}; border: none; padding: 4px;")
        idx = birim_combo.findText(birim)
        if idx >= 0:
            birim_combo.setCurrentIndex(idx)
        self.satir_table.setCellWidget(row, 4, birim_combo)

        self.satir_table.setItem(row, 5, QTableWidgetItem(f"{fiyat:.4f}"))

    def _del_sablon_satir(self):
        current = self.satir_table.currentRow()
        if current >= 0:
            self.satir_table.removeRow(current)
            # Renumber
            for i in range(self.satir_table.rowCount()):
                item = self.satir_table.item(i, 0)
                if item:
                    item.setText(str(i + 1))

    # ── KAYDETME ──
    def _yeni_sablon(self):
        self.selected_sablon_id = None
        self.detail_title.setText("➕ Yeni Şablon")
        self.sablon_adi_input.setText("")
        self.sablon_aciklama_input.setText("")
        self.sablon_kdv.setValue(20)
        self.sablon_iskonto.setValue(0)
        self.sablon_teslim.setText("")
        self.sablon_odeme.setText("")
        self.sablon_gecerlilik.setValue(30)
        self.sablon_ozel.setPlainText("")
        self.sablon_aktif.setChecked(True)
        self.satir_table.setRowCount(0)
        self.detail_frame.setVisible(True)

    def _kaydet_sablon(self):
        sablon_adi = self.sablon_adi_input.text().strip()
        if not sablon_adi:
            QMessageBox.warning(self, "Uyarı", "Şablon adı gereklidir!")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            aciklama = self.sablon_aciklama_input.text().strip()
            kdv = self.sablon_kdv.value()
            iskonto = self.sablon_iskonto.value()
            teslim = self.sablon_teslim.text().strip()
            odeme = self.sablon_odeme.text().strip()
            gecerlilik = self.sablon_gecerlilik.value()
            ozel = self.sablon_ozel.toPlainText().strip()
            aktif = 1 if self.sablon_aktif.isChecked() else 0

            if self.selected_sablon_id:
                cursor.execute("""
                    UPDATE satislar.teklif_sablonlari SET
                        sablon_adi = ?, aciklama = ?, varsayilan_kdv_oran = ?,
                        varsayilan_iskonto_oran = ?, varsayilan_teslim_suresi = ?,
                        varsayilan_odeme_kosullari = ?, varsayilan_gecerlilik_gun = ?,
                        varsayilan_ozel_kosullar = ?, aktif_mi = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (sablon_adi, aciklama, kdv, iskonto, teslim, odeme, gecerlilik, ozel, aktif, self.selected_sablon_id))

                cursor.execute("DELETE FROM satislar.teklif_sablon_satirlari WHERE sablon_id = ?", (self.selected_sablon_id,))
                sablon_id = self.selected_sablon_id
            else:
                cursor.execute("""
                    INSERT INTO satislar.teklif_sablonlari (
                        sablon_adi, aciklama, varsayilan_kdv_oran, varsayilan_iskonto_oran,
                        varsayilan_teslim_suresi, varsayilan_odeme_kosullari,
                        varsayilan_gecerlilik_gun, varsayilan_ozel_kosullar, aktif_mi
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (sablon_adi, aciklama, kdv, iskonto, teslim, odeme, gecerlilik, ozel, aktif))

                cursor.execute("SELECT @@IDENTITY")
                sablon_id = int(cursor.fetchone()[0])
                self.selected_sablon_id = sablon_id

            # Satırları kaydet
            for row in range(self.satir_table.rowCount()):
                kaplama_combo = self.satir_table.cellWidget(row, 1)
                kaplama = kaplama_combo.currentText() if kaplama_combo else ''

                kalinlik_text = self.satir_table.item(row, 2).text() if self.satir_table.item(row, 2) else ''
                malzeme = self.satir_table.item(row, 3).text() if self.satir_table.item(row, 3) else ''

                birim_combo = self.satir_table.cellWidget(row, 4)
                birim = birim_combo.currentText() if birim_combo else 'ADET'

                fiyat_text = self.satir_table.item(row, 5).text().replace(',', '.') if self.satir_table.item(row, 5) else '0'

                try:
                    kalinlik = float(kalinlik_text) if kalinlik_text else None
                except Exception:
                    kalinlik = None
                try:
                    fiyat = float(fiyat_text) if fiyat_text else 0
                except Exception:
                    fiyat = 0

                cursor.execute("""
                    INSERT INTO satislar.teklif_sablon_satirlari (
                        sablon_id, satir_no, kaplama_tipi_adi, kalinlik_mikron,
                        malzeme_tipi, birim, varsayilan_birim_fiyat
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (sablon_id, row + 1, kaplama, kalinlik, malzeme, birim, fiyat))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Başarılı", f"Şablon '{sablon_adi}' kaydedildi.")
            self._load_sablonlar()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Şablon kayıt hatası: {e}")

    def _sil_sablon(self):
        if not self.selected_sablon_id:
            return

        cevap = QMessageBox.question(
            self, "Şablon Sil",
            "Bu şablonu silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        if cevap != QMessageBox.Yes:
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM satislar.teklif_sablon_satirlari WHERE sablon_id = ?", (self.selected_sablon_id,))
            cursor.execute("DELETE FROM satislar.teklif_sablonlari WHERE id = ?", (self.selected_sablon_id,))
            conn.commit()
            conn.close()

            self.selected_sablon_id = None
            self.detail_frame.setVisible(False)
            self.detail_title.setText("Şablon seçin...")
            self._load_sablonlar()
            QMessageBox.information(self, "Başarılı", "Şablon silindi.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Şablon silme hatası: {e}")
