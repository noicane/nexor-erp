# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Numara Tanımları
İrsaliye no, sipariş no vb. otomatik numara şablonları
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


def get_modern_style(theme: dict) -> dict:
    t = theme or {}
    return {
        'card_bg': t.get('bg_card', '#151B23'),
        'input_bg': t.get('bg_input', '#232C3B'),
        'border': t.get('border', '#1E2736'),
        'text': t.get('text', '#E8ECF1'),
        'text_secondary': t.get('text_secondary', '#8896A6'),
        'text_muted': t.get('text_muted', '#5C6878'),
        'primary': t.get('primary', '#DC2626'),
        'primary_hover': t.get('primary_hover', '#9B1818'),
        'success': t.get('success', '#10B981'),
        'warning': t.get('warning', '#F59E0B'),
        'danger': t.get('error', '#EF4444'),
        'bg_main': t.get('bg_main', '#0F1419'),
        'bg_hover': t.get('bg_hover', '#1C2430'),
        'border_light': t.get('border_light', '#2A3545'),
    }


# Tablo oluşturma SQL'i
ENSURE_TABLE_SQL = """
IF NOT EXISTS (SELECT * FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'tanim' AND t.name = 'numara_tanimlari')
BEGIN
    CREATE TABLE tanim.numara_tanimlari (
        id INT IDENTITY(1,1) PRIMARY KEY,
        kod NVARCHAR(50) NOT NULL UNIQUE,
        ad NVARCHAR(200) NOT NULL,
        prefix NVARCHAR(20) NOT NULL DEFAULT '',
        ayirici NVARCHAR(5) NOT NULL DEFAULT '-',
        basamak_sayisi INT NOT NULL DEFAULT 6,
        son_numara INT NOT NULL DEFAULT 0,
        yil_bazli_mi BIT NOT NULL DEFAULT 1,
        aktif_yil INT NULL,
        aktif_mi BIT NOT NULL DEFAULT 1,
        olusturma_tarihi DATETIME DEFAULT GETDATE(),
        guncelleme_tarihi DATETIME DEFAULT GETDATE()
    )

    -- Varsayılan irsaliye tanımı
    INSERT INTO tanim.numara_tanimlari (kod, ad, prefix, ayirici, basamak_sayisi, son_numara, yil_bazli_mi, aktif_yil)
    VALUES ('IRSALIYE', N'İrsaliye Numarası', 'IRS', '-', 6, 0, 1, YEAR(GETDATE()))
END
"""


class NumaraDialog(QDialog):
    """Numara tanımı ekleme/düzenleme dialogu"""

    def __init__(self, theme: dict, parent=None, numara_id=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.numara_id = numara_id
        self.setWindowTitle("Numara Tanımı Düzenle" if numara_id else "Yeni Numara Tanımı")
        self.setMinimumWidth(500)
        self._setup_ui()
        if numara_id:
            self._load_data()

    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.s['bg_main']}; color: {self.s['text']}; }}")

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        input_style = f"""
            QLineEdit, QComboBox, QSpinBox {{
                background: {self.s['input_bg']};
                border: 1px solid {self.s['border']};
                border-radius: 6px;
                padding: 8px 12px;
                color: {self.s['text']};
                font-size: 13px;
            }}
        """

        # Kod
        self.kod_input = QLineEdit()
        self.kod_input.setPlaceholderText("Örn: IRSALIYE, SIPARIS")
        self.kod_input.setStyleSheet(input_style)
        layout.addRow("Kod:", self.kod_input)

        # Ad
        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderText("Örn: İrsaliye Numarası")
        self.ad_input.setStyleSheet(input_style)
        layout.addRow("Tanım:", self.ad_input)

        # Prefix
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Örn: IRS, SIP")
        self.prefix_input.setStyleSheet(input_style)
        layout.addRow("Ön Ek (Prefix):", self.prefix_input)

        # Ayırıcı
        self.ayirici_input = QComboBox()
        self.ayirici_input.addItems(["-", "/", ".", "_", ""])
        self.ayirici_input.setStyleSheet(input_style)
        layout.addRow("Ayırıcı:", self.ayirici_input)

        # Basamak sayısı
        self.basamak_input = QSpinBox()
        self.basamak_input.setRange(3, 10)
        self.basamak_input.setValue(6)
        self.basamak_input.setStyleSheet(input_style)
        layout.addRow("Basamak Sayısı:", self.basamak_input)

        # Yıl bazlı
        self.yil_bazli_check = QCheckBox("Her yıl başında sıfırla")
        self.yil_bazli_check.setChecked(True)
        self.yil_bazli_check.setStyleSheet(f"color: {self.s['text']};")
        layout.addRow("Yıl Bazlı:", self.yil_bazli_check)

        # Son numara
        self.son_numara_input = QSpinBox()
        self.son_numara_input.setRange(0, 9999999)
        self.son_numara_input.setValue(0)
        self.son_numara_input.setStyleSheet(input_style)
        layout.addRow("Son Numara:", self.son_numara_input)

        # Önizleme
        self.onizleme_label = QLabel()
        self.onizleme_label.setStyleSheet(f"""
            color: {self.s['success']};
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            background: {self.s['card_bg']};
            border-radius: 6px;
        """)
        layout.addRow("Önizleme:", self.onizleme_label)

        # Önizlemeyi güncelle
        self.prefix_input.textChanged.connect(self._update_preview)
        self.ayirici_input.currentTextChanged.connect(self._update_preview)
        self.basamak_input.valueChanged.connect(self._update_preview)
        self.son_numara_input.valueChanged.connect(self._update_preview)
        self._update_preview()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.s['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {self.s['primary_hover']}; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.s['input_bg']};
                color: {self.s['text']};
                border: 1px solid {self.s['border']};
                border-radius: 6px;
                padding: 10px 24px;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addRow("", btn_layout)

    def _update_preview(self):
        prefix = self.prefix_input.text().strip()
        ayirici = self.ayirici_input.currentText()
        basamak = self.basamak_input.value()
        son_no = self.son_numara_input.value()
        next_no = son_no + 1
        numara = f"{prefix}{ayirici}{next_no:0{basamak}d}"
        self.onizleme_label.setText(f"Sonraki: {numara}")

    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kod, ad, prefix, ayirici, basamak_sayisi, son_numara, yil_bazli_mi
                FROM tanim.numara_tanimlari WHERE id = ?
            """, (self.numara_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                self.kod_input.setText(row[0] or '')
                self.ad_input.setText(row[1] or '')
                self.prefix_input.setText(row[2] or '')
                idx = self.ayirici_input.findText(row[3] or '-')
                if idx >= 0:
                    self.ayirici_input.setCurrentIndex(idx)
                self.basamak_input.setValue(row[4] or 6)
                self.son_numara_input.setValue(row[5] or 0)
                self.yil_bazli_check.setChecked(bool(row[6]))
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenemedi: {e}")

    def _save(self):
        kod = self.kod_input.text().strip().upper()
        ad = self.ad_input.text().strip()
        prefix = self.prefix_input.text().strip()
        ayirici = self.ayirici_input.currentText()
        basamak = self.basamak_input.value()
        son_no = self.son_numara_input.value()
        yil_bazli = 1 if self.yil_bazli_check.isChecked() else 0

        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve tanım zorunludur!")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            if self.numara_id:
                cursor.execute("""
                    UPDATE tanim.numara_tanimlari SET
                        kod = ?, ad = ?, prefix = ?, ayirici = ?,
                        basamak_sayisi = ?, son_numara = ?, yil_bazli_mi = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (kod, ad, prefix, ayirici, basamak, son_no, yil_bazli, self.numara_id))
            else:
                cursor.execute("""
                    INSERT INTO tanim.numara_tanimlari
                    (kod, ad, prefix, ayirici, basamak_sayisi, son_numara, yil_bazli_mi, aktif_yil)
                    VALUES (?, ?, ?, ?, ?, ?, ?, YEAR(GETDATE()))
                """, (kod, ad, prefix, ayirici, basamak, son_no, yil_bazli))

            conn.commit()
            conn.close()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")


class TanimNumaraPage(BasePage):
    """Numara Tanımları Sayfası"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._ensure_table()
        self._setup_ui()
        self._load_data()

    def _ensure_table(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(ENSURE_TABLE_SQL)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Numara tablosu oluşturma hatası: {e}")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("🔢 Numara Tanımları")
        title.setStyleSheet(f"color: {self.s['text']}; font-size: 20px; font-weight: bold;")
        header.addWidget(title)

        desc = QLabel("İrsaliye, sipariş vb. otomatik numara şablonları")
        desc.setStyleSheet(f"color: {self.s['text_muted']}; font-size: 12px;")
        header.addWidget(desc)
        header.addStretch()

        # Butonlar
        for text, slot in [("➕ Yeni", self._yeni), ("✏️ Düzenle", self._duzenle),
                           ("🗑️ Sil", self._sil), ("🔄 Yenile", self._load_data)]:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {self.s['input_bg']};
                    color: {self.s['text']};
                    border: 1px solid {self.s['border']};
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background: {self.s['bg_hover']}; }}
            """)
            btn.clicked.connect(slot)
            header.addWidget(btn)

        layout.addLayout(header)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kod", "Tanım", "Prefix", "Ayırıcı", "Basamak", "Son No", "Önizleme"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 70)
        self.table.setColumnWidth(6, 80)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._duzenle)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.s['card_bg']};
                alternate-background-color: {self.s['bg_main']};
                border: 1px solid {self.s['border']};
                border-radius: 8px;
                gridline-color: {self.s['border']};
                color: {self.s['text']};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QTableWidget::item:selected {{
                background-color: {self.s['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {self.s['input_bg']};
                color: {self.s['text']};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.s['primary']};
                font-weight: bold;
            }}
        """)
        layout.addWidget(self.table, 1)

        # Alt bilgi
        self.info_label = QLabel()
        self.info_label.setStyleSheet(f"color: {self.s['text_muted']};")
        layout.addWidget(self.info_label)

    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad, prefix, ayirici, basamak_sayisi, son_numara, yil_bazli_mi
                FROM tanim.numara_tanimlari
                WHERE aktif_mi = 1
                ORDER BY kod
            """)
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(0)
            for row in rows:
                idx = self.table.rowCount()
                self.table.insertRow(idx)

                self.table.setItem(idx, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(idx, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(idx, 2, QTableWidgetItem(row[2] or ''))
                self.table.setItem(idx, 3, QTableWidgetItem(row[3] or ''))
                self.table.setItem(idx, 4, QTableWidgetItem(row[4] or ''))
                self.table.setItem(idx, 5, QTableWidgetItem(str(row[5] or 6)))

                son_no = row[6] or 0
                self.table.setItem(idx, 6, QTableWidgetItem(str(son_no)))

                # Önizleme
                prefix = row[3] or ''
                ayirici = row[4] or '-'
                basamak = row[5] or 6
                onizleme = f"{prefix}{ayirici}{son_no + 1:0{basamak}d}"
                item = QTableWidgetItem(onizleme)
                item.setForeground(QColor(self.s['success']))
                self.table.setItem(idx, 7, item)

            self.info_label.setText(f"Toplam: {len(rows)} tanım")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenemedi: {e}")

    def _get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Bir satır seçin!")
            return None
        return int(self.table.item(row, 0).text())

    def _yeni(self):
        dlg = NumaraDialog(self.theme, self)
        if dlg.exec():
            self._load_data()

    def _duzenle(self):
        numara_id = self._get_selected_id()
        if numara_id:
            dlg = NumaraDialog(self.theme, self, numara_id)
            if dlg.exec():
                self._load_data()

    def _sil(self):
        numara_id = self._get_selected_id()
        if not numara_id:
            return
        reply = QMessageBox.question(
            self, "Onay", "Bu numara tanımını silmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE tanim.numara_tanimlari SET aktif_mi = 0 WHERE id = ?", (numara_id,))
                conn.commit()
                conn.close()
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")


def sonraki_numara_al(kod: str) -> str:
    """Belirtilen kod için sonraki numarayı üret ve kaydet.

    Args:
        kod: Numara tanım kodu (örn: 'IRSALIYE')

    Returns:
        Üretilen numara string'i (örn: 'IRS-000001')
    """
    from datetime import datetime

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, prefix, ayirici, basamak_sayisi, son_numara, yil_bazli_mi, aktif_yil
        FROM tanim.numara_tanimlari
        WHERE kod = ? AND aktif_mi = 1
    """, (kod,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise Exception(f"Numara tanımı bulunamadı: {kod}")

    tanim_id, prefix, ayirici, basamak, son_no, yil_bazli, aktif_yil = row
    current_year = datetime.now().year

    # Yıl bazlı sıfırlama
    if yil_bazli and aktif_yil and aktif_yil < current_year:
        son_no = 0
        cursor.execute("""
            UPDATE tanim.numara_tanimlari
            SET aktif_yil = ?, son_numara = 0
            WHERE id = ?
        """, (current_year, tanim_id))

    yeni_no = son_no + 1

    # Numarayı güncelle
    cursor.execute("""
        UPDATE tanim.numara_tanimlari
        SET son_numara = ?, guncelleme_tarihi = GETDATE()
        WHERE id = ?
    """, (yeni_no, tanim_id))

    conn.commit()
    conn.close()

    return f"{prefix}{ayirici}{yeni_no:0{basamak}d}"
