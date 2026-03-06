# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Cari Adresler Yönetimi
musteri.cari_adresler tablosu üzerinden çoklu adres yönetimi
[MODERNIZED UI - v2.0]

Tablo: musteri.cari_adresler
- id, uuid, cari_id, adres_tipi, adres_adi
- ulke_id, sehir_id, ilce_id, adres, posta_kodu
- telefon, faks, email
- varsayilan_mi, aktif_mi
- olusturma_tarihi, guncelleme_tarihi
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QCheckBox, QTextEdit, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
import uuid


# ============================================================================
# MODERN STYLE HELPER
# ============================================================================
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
        'error': t.get('error', '#EF4444'),
        'danger': t.get('error', '#EF4444'),
        'info': t.get('info', '#3B82F6'),
        'bg_main': t.get('bg_main', '#0F1419'),
        'bg_hover': t.get('bg_hover', '#1C2430'),
        'bg_selected': t.get('bg_selected', '#1E1215'),
        'border_light': t.get('border_light', '#2A3545'),
        'border_input': t.get('border_input', '#1E2736'),
        'card_solid': t.get('bg_card_solid', '#151B23'),
        'gradient': t.get('gradient_css', ''),
    }


class AdresDialog(QDialog):
    """Adres Ekleme/Düzenleme Dialog - Modern UI"""
    
    def __init__(self, theme: dict, cari_id: int, adres_data: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.cari_id = cari_id
        self.adres_data = adres_data or {}
        self.is_edit = bool(adres_data)
        
        self.setWindowTitle("Adres Düzenle" if self.is_edit else "Yeni Adres")
        self.setMinimumWidth(550)
        self.setModal(True)
        self._setup_ui()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 12px;
            }}
            QLabel {{
                color: {s['text']};
                background: transparent;
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {s['text']};
                font-size: 13px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border-color: {s['primary']};
            }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                color: {s['text']};
                selection-background-color: {s['primary']};
            }}
            QCheckBox {{
                color: {s['text']};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {s['border']};
                background: {s['input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background: {s['primary']};
                border-color: {s['primary']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        icon = QLabel("📍")
        icon.setStyleSheet("font-size: 24px;")
        header.addWidget(icon)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {s['text']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {s['border']}; max-height: 1px;")
        layout.addWidget(sep)
        
        # Form
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        
        # Adres Tipi
        lbl = QLabel("Adres Tipi")
        lbl.setStyleSheet(label_style)
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItem("📄 FATURA", "FATURA")
        self.cmb_tip.addItem("🚚 SEVK", "SEVK")
        self.cmb_tip.addItem("🏢 İŞ", "IS")
        self.cmb_tip.addItem("📋 DİĞER", "DIGER")
        if self.adres_data.get('adres_tipi'):
            idx = self.cmb_tip.findData(self.adres_data['adres_tipi'])
            if idx >= 0:
                self.cmb_tip.setCurrentIndex(idx)
        form.addRow(lbl, self.cmb_tip)
        
        # Adres Adı
        lbl = QLabel("Adres Adı *")
        lbl.setStyleSheet(label_style)
        self.txt_ad = QLineEdit()
        self.txt_ad.setText(self.adres_data.get('adres_adi', ''))
        self.txt_ad.setPlaceholderText("Örn: Merkez Ofis, Fabrika, ...")
        form.addRow(lbl, self.txt_ad)
        
        # Şehir
        lbl = QLabel("Şehir")
        lbl.setStyleSheet(label_style)
        self.cmb_sehir = QComboBox()
        self.cmb_sehir.addItem("-- Şehir Seçiniz --", None)
        self._load_sehirler()
        self.cmb_sehir.currentIndexChanged.connect(self._on_sehir_changed)
        form.addRow(lbl, self.cmb_sehir)
        
        # İlçe
        lbl = QLabel("İlçe")
        lbl.setStyleSheet(label_style)
        self.cmb_ilce = QComboBox()
        self.cmb_ilce.addItem("-- İlçe Seçiniz --", None)
        form.addRow(lbl, self.cmb_ilce)
        
        # Adres
        lbl = QLabel("Adres")
        lbl.setStyleSheet(label_style)
        self.txt_adres = QTextEdit()
        self.txt_adres.setPlainText(self.adres_data.get('adres', ''))
        self.txt_adres.setMaximumHeight(80)
        self.txt_adres.setPlaceholderText("Sokak, mahalle, cadde, bina no...")
        form.addRow(lbl, self.txt_adres)
        
        # Posta Kodu
        lbl = QLabel("Posta Kodu")
        lbl.setStyleSheet(label_style)
        self.txt_posta = QLineEdit()
        self.txt_posta.setText(self.adres_data.get('posta_kodu', ''))
        self.txt_posta.setPlaceholderText("34000")
        form.addRow(lbl, self.txt_posta)
        
        # Telefon
        lbl = QLabel("Telefon")
        lbl.setStyleSheet(label_style)
        self.txt_telefon = QLineEdit()
        self.txt_telefon.setText(self.adres_data.get('telefon', ''))
        self.txt_telefon.setPlaceholderText("0212 XXX XX XX")
        form.addRow(lbl, self.txt_telefon)
        
        # E-posta
        lbl = QLabel("E-posta")
        lbl.setStyleSheet(label_style)
        self.txt_email = QLineEdit()
        self.txt_email.setText(self.adres_data.get('email', ''))
        self.txt_email.setPlaceholderText("email@firma.com")
        form.addRow(lbl, self.txt_email)
        
        # Varsayılan
        self.chk_varsayilan = QCheckBox("⭐ Bu adresi varsayılan yap")
        self.chk_varsayilan.setChecked(self.adres_data.get('varsayilan_mi', False))
        form.addRow("", self.chk_varsayilan)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {s['border']}; border-color: {s['primary']}; }}
        """)
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾  Kaydet")
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 28px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
        
        # Mevcut şehir/ilçe seç
        if self.adres_data.get('sehir_id'):
            for i in range(self.cmb_sehir.count()):
                if self.cmb_sehir.itemData(i) == self.adres_data['sehir_id']:
                    self.cmb_sehir.setCurrentIndex(i)
                    break
    
    # ========== DATA METHODS (UNCHANGED) ==========
    def _load_sehirler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM tanim.sehirler WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_sehir.addItem(row[1], row[0])
        except:
            pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _on_sehir_changed(self):
        self.cmb_ilce.clear()
        self.cmb_ilce.addItem("-- İlçe Seçiniz --", None)
        sehir_id = self.cmb_sehir.currentData()
        if not sehir_id:
            return
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad FROM tanim.ilceler WHERE sehir_id = ? AND aktif_mi = 1 ORDER BY ad", (sehir_id,))
            for row in cursor.fetchall():
                self.cmb_ilce.addItem(row[1], row[0])

            if self.adres_data.get('ilce_id'):
                for i in range(self.cmb_ilce.count()):
                    if self.cmb_ilce.itemData(i) == self.adres_data['ilce_id']:
                        self.cmb_ilce.setCurrentIndex(i)
                        break
        except:
            pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _save(self):
        adres_tipi = self.cmb_tip.currentData()
        adres_adi = self.txt_ad.text().strip()
        
        if not adres_adi:
            QMessageBox.warning(self, "⚠️ Uyarı", "Adres adı zorunludur!")
            return
        
        self.result_data = {
            'adres_tipi': adres_tipi,
            'adres_adi': adres_adi,
            'sehir_id': self.cmb_sehir.currentData(),
            'ilce_id': self.cmb_ilce.currentData(),
            'adres': self.txt_adres.toPlainText().strip(),
            'posta_kodu': self.txt_posta.text().strip() or None,
            'telefon': self.txt_telefon.text().strip() or None,
            'email': self.txt_email.text().strip() or None,
            'varsayilan_mi': 1 if self.chk_varsayilan.isChecked() else 0
        }
        self.accept()
    
    def get_data(self):
        return self.result_data


class CariAdreslerPage(BasePage):
    """Cari Adresler Yönetimi Sayfası - Modern UI"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.selected_cari_id = None
        self._setup_ui()
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        
        title_row = QHBoxLayout()
        icon = QLabel("📍")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Cari Adresler")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        
        subtitle = QLabel("Cari kartlarına ait çoklu adres yönetimi")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        
        layout.addLayout(header)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        lbl = QLabel("Cari Seç:")
        lbl.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        toolbar.addWidget(lbl)
        
        self.cmb_cari = QComboBox()
        self.cmb_cari.setMinimumWidth(400)
        self.cmb_cari.setStyleSheet(f"""
            QComboBox {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 14px;
                color: {s['text']};
                font-size: 13px;
            }}
            QComboBox:focus {{ border-color: {s['primary']}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                color: {s['text']};
                selection-background-color: {s['primary']};
            }}
        """)
        self.cmb_cari.currentIndexChanged.connect(self._on_cari_changed)
        toolbar.addWidget(self.cmb_cari)
        
        toolbar.addStretch()
        
        btn_yeni = QPushButton("➕  Yeni Adres")
        btn_yeni.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        btn_yeni.clicked.connect(self._yeni_adres)
        toolbar.addWidget(btn_yeni)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 10px;
                gridline-color: {s['border']};
                color: {s['text']};
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {s['border']};
            }}
            QTableWidget::item:selected {{ background: {s['primary']}; }}
            QTableWidget::item:hover {{ background: rgba(220, 38, 38, 0.1); }}
            QHeaderView::section {{
                background: rgba(0,0,0,0.3);
                color: {s['text_secondary']};
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid {s['primary']};
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }}
        """)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Tip", "Adres Adı", "Şehir", "İlçe", "Telefon", "Varsayılan", "Durum", "İşlem"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 140)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 90)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setColumnWidth(8, 170)
        self.table.doubleClicked.connect(self._duzenle_adres)
        layout.addWidget(self.table, 1)
        
        self._load_cariler()
    
    # ========== DATA METHODS (UNCHANGED) ==========
    def _load_cariler(self):
        self.cmb_cari.clear()
        self.cmb_cari.addItem("-- Cari Seçiniz --", None)
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, cari_kodu, unvan FROM musteri.cariler WHERE aktif_mi = 1 AND (silindi_mi = 0 OR silindi_mi IS NULL) ORDER BY unvan")
            for row in cursor.fetchall():
                self.cmb_cari.addItem(f"{row[1]} - {row[2]}", row[0])
        except Exception as e:
            QMessageBox.warning(self, "⚠️ Hata", f"Cariler yüklenemedi: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _on_cari_changed(self):
        self.selected_cari_id = self.cmb_cari.currentData()
        self._load_adresler()
    
    def _load_adresler(self):
        s = self.s
        self.table.setRowCount(0)
        if not self.selected_cari_id:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.id, a.adres_tipi, a.adres_adi, s.ad, i.ad, a.telefon, a.varsayilan_mi, a.aktif_mi
                FROM musteri.cari_adresler a
                LEFT JOIN tanim.sehirler s ON a.sehir_id = s.id
                LEFT JOIN tanim.ilceler i ON a.ilce_id = i.id
                WHERE a.cari_id = ? AND (a.silindi_mi = 0 OR a.silindi_mi IS NULL)
                ORDER BY a.varsayilan_mi DESC, a.adres_adi
            """, (self.selected_cari_id,))

            for row in cursor.fetchall():
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(r, 1, QTableWidgetItem(row[1] or ""))
                self.table.setItem(r, 2, QTableWidgetItem(row[2] or ""))
                self.table.setItem(r, 3, QTableWidgetItem(row[3] or ""))
                self.table.setItem(r, 4, QTableWidgetItem(row[4] or ""))
                self.table.setItem(r, 5, QTableWidgetItem(row[5] or ""))

                varsayilan = QTableWidgetItem("⭐" if row[6] else "")
                varsayilan.setForeground(QColor(s['warning']))
                varsayilan.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, 6, varsayilan)

                durum = QTableWidgetItem("✓ Aktif" if row[7] else "✗ Pasif")
                durum.setForeground(QColor(s['success']) if row[7] else QColor(s['error']))
                durum.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, 7, durum)

                rid = row[0]
                widget = self.create_action_buttons([
                    ("✏️", "Duzenle", lambda checked, rid=rid: self._duzenle_adres_by_id(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=rid: self._sil_adres_by_id(rid), "delete"),
                ])
                self.table.setCellWidget(r, 8, widget)

                self.table.setRowHeight(r, 48)
        except Exception as e:
            QMessageBox.warning(self, "⚠️ Hata", f"Adresler yüklenemedi: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _yeni_adres(self):
        if not self.selected_cari_id:
            QMessageBox.warning(self, "⚠️ Uyarı", "Lütfen önce bir cari seçin!")
            return

        dialog = AdresDialog(self.theme, self.selected_cari_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                if data['varsayilan_mi']:
                    cursor.execute("UPDATE musteri.cari_adresler SET varsayilan_mi = 0 WHERE cari_id = ?", (self.selected_cari_id,))

                cursor.execute("""
                    INSERT INTO musteri.cari_adresler (uuid, cari_id, adres_tipi, adres_adi, sehir_id, ilce_id, adres, posta_kodu, telefon, email, varsayilan_mi, aktif_mi, olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, GETDATE(), GETDATE(), 0)
                """, (str(uuid.uuid4()), self.selected_cari_id, data['adres_tipi'], data['adres_adi'], data['sehir_id'], data['ilce_id'], data['adres'], data['posta_kodu'], data['telefon'], data['email'], data['varsayilan_mi']))

                conn.commit()
                self._load_adresler()
                QMessageBox.information(self, "✓ Başarılı", "Adres eklendi!")
            except Exception as e:
                QMessageBox.critical(self, "❌ Hata", f"Adres eklenemedi: {e}")
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass
    
    def _duzenle_adres_by_id(self, adres_id):
        """ID ile adres düzenleme (satır butonundan)"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT adres_tipi, adres_adi, sehir_id, ilce_id, adres, posta_kodu, telefon, email, varsayilan_mi
                FROM musteri.cari_adresler WHERE id = ?
            """, (adres_id,))
            row = cursor.fetchone()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {e}")
            return
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

        if not row:
            return

        mevcut = {
            'adres_tipi': row[0], 'adres_adi': row[1], 'sehir_id': row[2], 'ilce_id': row[3],
            'adres': row[4], 'posta_kodu': row[5], 'telefon': row[6], 'email': row[7], 'varsayilan_mi': row[8]
        }

        dialog = AdresDialog(self.theme, self.selected_cari_id, mevcut, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                if data['varsayilan_mi']:
                    cursor.execute("UPDATE musteri.cari_adresler SET varsayilan_mi = 0 WHERE cari_id = ?", (self.selected_cari_id,))

                cursor.execute("""
                    UPDATE musteri.cari_adresler SET adres_tipi = ?, adres_adi = ?, sehir_id = ?, ilce_id = ?, adres = ?, posta_kodu = ?, telefon = ?, email = ?, varsayilan_mi = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (data['adres_tipi'], data['adres_adi'], data['sehir_id'], data['ilce_id'], data['adres'], data['posta_kodu'], data['telefon'], data['email'], data['varsayilan_mi'], adres_id))

                conn.commit()
                self._load_adresler()
                QMessageBox.information(self, "Başarılı", "Adres güncellendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {e}")
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass

    def _sil_adres_by_id(self, adres_id):
        """ID ile adres silme (satır butonundan)"""
        reply = QMessageBox.question(self, "Silme Onayı",
            "Bu adresi silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE musteri.cari_adresler SET silindi_mi = 1, silinme_tarihi = GETDATE() WHERE id = ?", (adres_id,))
                conn.commit()
                self._load_adresler()
                QMessageBox.information(self, "Başarılı", "Adres silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass

    def _duzenle_adres(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "⚠️ Uyarı", "Lütfen bir adres seçin!")
            return

        adres_id = int(self.table.item(selected[0].row(), 0).text())

        # First connection: read existing address data
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT adres_tipi, adres_adi, sehir_id, ilce_id, adres, posta_kodu, telefon, email, varsayilan_mi
                FROM musteri.cari_adresler WHERE id = ?
            """, (adres_id,))
            row = cursor.fetchone()
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", f"Güncelleme hatası: {e}")
            return
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

        if not row:
            return

        mevcut = {
            'adres_tipi': row[0], 'adres_adi': row[1], 'sehir_id': row[2], 'ilce_id': row[3],
            'adres': row[4], 'posta_kodu': row[5], 'telefon': row[6], 'email': row[7], 'varsayilan_mi': row[8]
        }

        dialog = AdresDialog(self.theme, self.selected_cari_id, mevcut, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            # Second connection: update address data
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                if data['varsayilan_mi']:
                    cursor.execute("UPDATE musteri.cari_adresler SET varsayilan_mi = 0 WHERE cari_id = ?", (self.selected_cari_id,))

                cursor.execute("""
                    UPDATE musteri.cari_adresler SET adres_tipi = ?, adres_adi = ?, sehir_id = ?, ilce_id = ?, adres = ?, posta_kodu = ?, telefon = ?, email = ?, varsayilan_mi = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (data['adres_tipi'], data['adres_adi'], data['sehir_id'], data['ilce_id'], data['adres'], data['posta_kodu'], data['telefon'], data['email'], data['varsayilan_mi'], adres_id))

                conn.commit()
                self._load_adresler()
                QMessageBox.information(self, "✓ Başarılı", "Adres güncellendi!")
            except Exception as e:
                QMessageBox.critical(self, "❌ Hata", f"Güncelleme hatası: {e}")
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass
    
    def _sil_adres(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "⚠️ Uyarı", "Lütfen bir adres seçin!")
            return
        
        adres_id = int(self.table.item(selected[0].row(), 0).text())
        
        reply = QMessageBox.question(self, "🗑️ Silme Onayı", 
            "Bu adresi silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE musteri.cari_adresler SET silindi_mi = 1, silinme_tarihi = GETDATE() WHERE id = ?", (adres_id,))
                conn.commit()
                self._load_adresler()
                QMessageBox.information(self, "✓ Başarılı", "Adres silindi!")
            except Exception as e:
                QMessageBox.critical(self, "❌ Hata", f"Silme hatası: {e}")
            finally:
                if conn:
                    try: conn.close()
                    except Exception: pass
