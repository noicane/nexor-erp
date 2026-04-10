# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Final Kalite Kontrol Sayfası (v4)
=====================================================
Yeni akış:
- Personel kart/barkod/sicil ile giriş yapar
- Yetki kontrolü (Polivelans: "Finak Kalite", seviye >= 3)
- FKK deposundaki bekleyen ürünleri görür
- Ürün seçip kontrole başlar
- Sağlam → SEVK, Hatalı → RED depoya
- Etiket yazdırma (Şablon bazlı PDF)
- Onaylı ürünler sekmesi + tekrar etiket basma
"""
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QSpinBox, QWidget, QGridLayout, QStackedWidget,
    QSplitter, QListWidget, QListWidgetItem, QTabWidget,
    QGroupBox, QDateEdit, QScrollArea, QApplication, QSlider
)
from PySide6.QtCore import Qt, QTimer, QTime, QEvent, QDate
from PySide6.QtGui import QColor, QFont, QPixmap

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.rfid_reader import RFIDCardReader
from config import NAS_PATHS

ETIKET_YAZICI = "Godex G500"


def _kalite_scale() -> float:
    """Kalite ekranları için UI ölçek faktörü. config.json -> kalite_ui_scale (varsayılan 1.4)"""
    try:
        from core.external_config import config_manager
        return float(config_manager.get('kalite_ui_scale', 1.4))
    except Exception:
        return 1.4


def _sz(px: int) -> int:
    """Piksel değerini scale faktörüne göre ölçekle"""
    return int(px * _kalite_scale())


def _fs(px: int) -> str:
    """font-size CSS değeri üret (scale'li)"""
    return f"{_sz(px)}px"


class EtiketOnizlemeDialog(QDialog):
    """Gelişmiş etiket önizleme - Şablon seçimi + yazıcı + PDF"""

    def __init__(self, theme: dict, etiket_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.etiket_data = etiket_data
        self.setWindowTitle("Etiket Önizleme ve Yazdır")
        self.setMinimumSize(550, 550)
        self._setup_ui()
        self._load_sablonlar()
        self._load_yazicilar()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QGroupBox {{
                color: {self.theme.get('primary', '#DC2626')};
                font-weight: bold;
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 8px; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Etiket Önizleme")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)

        # Etiket önizleme frame
        etiket_frame = QFrame()
        etiket_frame.setFixedSize(400, 200)
        etiket_frame.setStyleSheet(f"QFrame {{ background: white; border: 2px solid {self.theme.get('border')}; border-radius: 8px; }}")
        etiket_layout = QVBoxLayout(etiket_frame)
        etiket_layout.setContentsMargins(15, 10, 15, 10)
        etiket_layout.setSpacing(4)

        musteri_lbl = QLabel(str(self.etiket_data.get('musteri', ''))[:35])
        musteri_lbl.setStyleSheet("color: #000; font-size: 16px; font-weight: bold;")
        musteri_lbl.setAlignment(Qt.AlignCenter)
        etiket_layout.addWidget(musteri_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #333;")
        line.setFixedHeight(1)
        etiket_layout.addWidget(line)

        urun_text = self.etiket_data.get('stok_adi', '') or self.etiket_data.get('urun', '')
        etiket_layout.addWidget(QLabel(f"Ürün: {str(urun_text)[:30]}"))
        etiket_layout.addWidget(QLabel(f"Lot: {self.etiket_data.get('lot_no', '')}"))

        info_row = QHBoxLayout()
        info_row.addWidget(QLabel(f"Sağlam: {self.etiket_data.get('saglam_adet', self.etiket_data.get('miktar', 0)):,}"))
        sonuc = self.etiket_data.get('sonuc', '')
        sonuc_renk = {'ONAY': '#22c55e', 'RED': '#ef4444', 'KISMI': '#f59e0b'}.get(sonuc, '#000')
        sonuc_lbl = QLabel(f"Sonuç: {sonuc}")
        sonuc_lbl.setStyleSheet(f"color: {sonuc_renk}; font-weight: bold;")
        info_row.addWidget(sonuc_lbl)
        etiket_layout.addLayout(info_row)

        etiket_layout.addWidget(QLabel(f"Kontrol: {str(self.etiket_data.get('kontrolcu', ''))[:20]}"))

        barkod_lbl = QLabel("|||||||||||||||||||||||||||||||||||")
        barkod_lbl.setStyleSheet("color: #000; font-size: 20px; font-family: monospace;")
        barkod_lbl.setAlignment(Qt.AlignCenter)
        etiket_layout.addWidget(barkod_lbl)

        for w in etiket_frame.findChildren(QLabel):
            if "|||" not in w.text():
                w.setStyleSheet(w.styleSheet() + "color: #000; font-size: 12px;")

        layout.addWidget(etiket_frame, alignment=Qt.AlignCenter)

        # Şablon seçimi
        sablon_group = QGroupBox("Etiket Şablonu")
        sablon_layout = QHBoxLayout(sablon_group)
        sablon_layout.addWidget(QLabel("Şablon:"))
        self.sablon_combo = QComboBox()
        self.sablon_combo.setMinimumWidth(250)
        self.sablon_combo.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        sablon_layout.addWidget(self.sablon_combo)
        sablon_layout.addStretch()
        layout.addWidget(sablon_group)

        # Yazıcı seçimi
        yazici_group = QGroupBox("Yazıcı Ayarları")
        yazici_layout = QHBoxLayout(yazici_group)
        yazici_layout.addWidget(QLabel("Yazıcı:"))
        self.yazici_combo = QComboBox()
        self.yazici_combo.setMinimumWidth(200)
        self.yazici_combo.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px;")
        yazici_layout.addWidget(self.yazici_combo)
        yazici_layout.addWidget(QLabel("Mod:"))
        self.mod_combo = QComboBox()
        self.mod_combo.addItem("PDF Yazdır", "PDF")
        self.mod_combo.addItem("Godex ZPL", "ZPL")
        self.mod_combo.addItem("Godex EZPL", "EZPL")
        self.mod_combo.setStyleSheet(self.yazici_combo.styleSheet())
        yazici_layout.addWidget(self.mod_combo)
        yazici_layout.addStretch()
        layout.addWidget(yazici_group)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        onizle_btn = QPushButton("PDF Önizle")
        onizle_btn.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 20px;")
        onizle_btn.clicked.connect(self._pdf_onizle)
        btn_layout.addWidget(onizle_btn)

        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 20px;")
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)

        yazdir_btn = QPushButton("Yazdır")
        yazdir_btn.setStyleSheet(f"background: {self.theme.get('success')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        yazdir_btn.clicked.connect(self.accept)
        btn_layout.addWidget(yazdir_btn)
        layout.addLayout(btn_layout)

    def _load_sablonlar(self):
        self.sablon_combo.clear()
        varsayilan_index = 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sablon_kodu, sablon_adi, ISNULL(varsayilan_mi, 0) as varsayilan_mi
                FROM tanim.etiket_sablonlari
                WHERE aktif_mi = 1
                ORDER BY varsayilan_mi DESC, sablon_adi
            """)
            for i, row in enumerate(cursor.fetchall()):
                prefix = "⭐ " if row[3] else ""
                self.sablon_combo.addItem(f"{prefix}{row[2]}", row[0])
                if row[3]:
                    varsayilan_index = i
            conn.close()
            if self.sablon_combo.count() == 0:
                self.sablon_combo.addItem("Varsayılan Şablon", None)
            else:
                self.sablon_combo.setCurrentIndex(varsayilan_index)
        except Exception as e:
            print(f"Şablon yükleme hatası: {e}")
            self.sablon_combo.addItem("Varsayılan Şablon", None)

    def _load_yazicilar(self):
        self.yazici_combo.clear()
        try:
            from utils.etiket_yazdir import get_available_printers, get_godex_printers
            all_printers = get_available_printers()
            godex_printers = get_godex_printers()
            if godex_printers:
                for p in godex_printers:
                    self.yazici_combo.addItem(f"{p}", p)
            for p in all_printers:
                if p not in godex_printers:
                    self.yazici_combo.addItem(p, p)
            if self.yazici_combo.count() == 0:
                self.yazici_combo.addItem("PDF Dosyası Olarak Kaydet", "PDF_ONLY")
        except ImportError:
            self.yazici_combo.addItem("PDF Dosyası Olarak Kaydet", "PDF_ONLY")
        except Exception as e:
            print(f"Yazıcı listesi yüklenemedi: {e}")
            self.yazici_combo.addItem("PDF Dosyası Olarak Kaydet", "PDF_ONLY")

    def _pdf_onizle(self):
        try:
            sablon_id = self.sablon_combo.currentData()
            etiketler = [self.etiket_data]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='fk_etiket_')
            temp_path = temp_file.name
            temp_file.close()
            if sablon_id:
                from utils.etiket_yazdir import sablon_ile_etiket_pdf_olustur
                sablon_ile_etiket_pdf_olustur(temp_path, etiketler, sablon_id)
            else:
                from utils.etiket_yazdir import a4_etiket_pdf_olustur
                a4_etiket_pdf_olustur(temp_path, etiketler)
            subprocess.Popen(['start', '', temp_path], shell=True)
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"PDF önizleme hatası: {e}")

    def get_sablon_id(self):
        return self.sablon_combo.currentData()

    def get_yazici(self):
        return self.yazici_combo.currentData()

    def get_mod(self):
        return self.mod_combo.currentData()


class FinalKontrolDialog(QDialog):
    def __init__(self, gorev_data, personel_data, theme, parent=None):
        super().__init__(parent)
        self.gorev = gorev_data
        self.personel = personel_data
        self.theme = theme
        self.result_data = None
        self.baslangic_zamani = datetime.now()
        self.hata_listesi = []
        self.hata_turleri = []
        self.setWindowTitle(f"Kontrol - {gorev_data.get('is_emri_no', '')}")
        # Ekran boyutuna göre dialog boyutu ayarla
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            w = min(_sz(700), int(sg.width() * 0.92))
            h = min(_sz(620), int(sg.height() * 0.92))
            self.resize(w, h)
        else:
            self.setMinimumSize(_sz(700), _sz(620))
        self._load_hata_turleri()
        self._setup_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_sure)
        self.timer.start(1000)

    def _load_hata_turleri(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.hata_turleri WHERE aktif_mi = 1 ORDER BY sira_no, kod")
            self.hata_turleri = [{'id': r[0], 'kod': r[1], 'ad': r[2]} for r in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"Hata türleri yükleme hatası: {e}")
            self.hata_turleri = []

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; font-size: {_fs(14)}; }}
        """)

        # ScrollArea ile sar - küçük ekranlarda kaydırılabilir
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(_sz(20), _sz(16), _sz(20), _sz(10))
        layout.setSpacing(_sz(10))

        input_style = f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: {_sz(6)}px; padding: {_sz(10)}px; font-size: {_fs(14)};"

        header = QHBoxLayout()
        title = QLabel("Final Kalite Kontrol")
        title.setStyleSheet(f"font-size: {_fs(20)}; font-weight: bold; color: {self.theme.get('primary')};")
        header.addWidget(title)
        header.addStretch()
        self.sure_label = QLabel("00:00")
        self.sure_label.setStyleSheet(f"color: {self.theme.get('text')}; font-size: {_fs(22)}; font-weight: bold; background: {self.theme.get('bg_card')}; padding: {_sz(6)}px {_sz(12)}px; border-radius: {_sz(6)}px;")
        header.addWidget(self.sure_label)
        layout.addLayout(header)

        info_frame = QFrame()
        info_frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: {_sz(8)}px; padding: {_sz(10)}px; }}")
        info_grid = QGridLayout(info_frame)
        info_grid.setSpacing(_sz(8))
        lbl_style = f"font-size: {_fs(14)};"
        val_style = f"font-size: {_fs(15)}; font-weight: bold;"
        ie_lbl = QLabel("İş Emri:")
        ie_lbl.setStyleSheet(lbl_style)
        info_grid.addWidget(ie_lbl, 0, 0)
        ie_val = QLabel(f"{self.gorev.get('is_emri_no', '')}")
        ie_val.setStyleSheet(val_style)
        info_grid.addWidget(ie_val, 0, 1)
        ke_lbl = QLabel("Kontrol Eden:")
        ke_lbl.setStyleSheet(lbl_style)
        info_grid.addWidget(ke_lbl, 0, 2)
        ke_val = QLabel(f"{self.personel.get('ad_soyad', '')}")
        ke_val.setStyleSheet(val_style)
        info_grid.addWidget(ke_val, 0, 3)
        lot_lbl = QLabel("Lot:")
        lot_lbl.setStyleSheet(lbl_style)
        info_grid.addWidget(lot_lbl, 1, 0)
        lot_val = QLabel(self.gorev.get('lot_no', ''))
        lot_val.setStyleSheet(val_style)
        info_grid.addWidget(lot_val, 1, 1)
        mus_lbl = QLabel("Müşteri:")
        mus_lbl.setStyleSheet(lbl_style)
        info_grid.addWidget(mus_lbl, 1, 2)
        mus_val = QLabel((self.gorev.get('cari_unvani', '') or '')[:30])
        mus_val.setStyleSheet(val_style)
        mus_val.setWordWrap(True)
        info_grid.addWidget(mus_val, 1, 3)
        layout.addWidget(info_frame)

        kontrol_frame = QFrame()
        kontrol_frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: {_sz(8)}px; padding: {_sz(12)}px; }}")
        kontrol_layout = QGridLayout(kontrol_frame)
        kontrol_layout.setSpacing(_sz(10))
        kontrol_adet = self.gorev.get('kontrol_adet', 0) or self.gorev.get('miktar', 0)

        ke2_lbl = QLabel("Kontrol Edilecek:")
        ke2_lbl.setStyleSheet(f"font-size: {_fs(14)};")
        kontrol_layout.addWidget(ke2_lbl, 0, 0)
        toplam_lbl = QLabel(f"<b>{kontrol_adet:,}</b> adet")
        toplam_lbl.setStyleSheet(f"color: {self.theme.get('primary')}; font-size: {_fs(16)};")
        kontrol_layout.addWidget(toplam_lbl, 0, 1)

        ked_lbl = QLabel("Kontrol Edilen:")
        ked_lbl.setStyleSheet(f"font-size: {_fs(14)};")
        kontrol_layout.addWidget(ked_lbl, 1, 0)
        self.kontrol_spin = QSpinBox()
        self.kontrol_spin.setRange(0, int(kontrol_adet))
        self.kontrol_spin.setValue(int(kontrol_adet))
        self.kontrol_spin.setStyleSheet(f"QSpinBox {{ {input_style} }}")
        self.kontrol_spin.valueChanged.connect(self._update_hesap)
        kontrol_layout.addWidget(self.kontrol_spin, 1, 1)

        sa_lbl = QLabel("Sağlam Adet:")
        sa_lbl.setStyleSheet(f"font-size: {_fs(14)};")
        kontrol_layout.addWidget(sa_lbl, 2, 0)
        self.saglam_spin = QSpinBox()
        self.saglam_spin.setRange(0, int(kontrol_adet))
        self.saglam_spin.setValue(int(kontrol_adet))
        self.saglam_spin.setStyleSheet(f"QSpinBox {{ {input_style} }}")
        self.saglam_spin.valueChanged.connect(self._update_hesap)
        kontrol_layout.addWidget(self.saglam_spin, 2, 1)

        ha_lbl = QLabel("Hatalı Adet:")
        ha_lbl.setStyleSheet(f"font-size: {_fs(14)};")
        kontrol_layout.addWidget(ha_lbl, 3, 0)
        self.hatali_lbl = QLabel("0")
        self.hatali_lbl.setStyleSheet(f"color: {self.theme.get('error')}; font-size: {_fs(20)}; font-weight: bold;")
        kontrol_layout.addWidget(self.hatali_lbl, 3, 1)
        layout.addWidget(kontrol_frame)

        hata_frame = QFrame()
        hata_frame.setStyleSheet(f"QFrame {{ background: {self.theme.get('bg_card')}; border: 1px solid {self.theme.get('border')}; border-radius: {_sz(8)}px; padding: {_sz(10)}px; }}")
        hata_layout = QVBoxLayout(hata_frame)
        hata_header = QHBoxLayout()
        rs_lbl = QLabel("Red Sebepleri:")
        rs_lbl.setStyleSheet(f"font-size: {_fs(14)};")
        hata_header.addWidget(rs_lbl)
        hata_header.addStretch()
        self.hata_combo = QComboBox()
        self.hata_combo.setMinimumWidth(_sz(200))
        self.hata_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        for hata in self.hata_turleri:
            self.hata_combo.addItem(f"{hata['kod']} - {hata['ad']}", hata['id'])
        hata_header.addWidget(self.hata_combo)
        self.hata_adet_spin = QSpinBox()
        self.hata_adet_spin.setRange(1, 99999)
        self.hata_adet_spin.setValue(1)
        self.hata_adet_spin.setStyleSheet(f"QSpinBox {{ {input_style} min-width: {_sz(70)}px; }}")
        hata_header.addWidget(self.hata_adet_spin)
        hata_ekle_btn = QPushButton("+ Ekle")
        hata_ekle_btn.setStyleSheet(f"QPushButton {{ background: {self.theme.get('warning')}; color: white; border: none; border-radius: {_sz(6)}px; padding: {_sz(10)}px {_sz(16)}px; font-weight: bold; font-size: {_fs(14)}; }}")
        hata_ekle_btn.clicked.connect(self._hata_ekle)
        hata_header.addWidget(hata_ekle_btn)
        hata_layout.addLayout(hata_header)

        self.hata_list = QListWidget()
        self.hata_list.setMaximumHeight(_sz(80))
        self.hata_list.setStyleSheet(f"QListWidget {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: {_sz(6)}px; font-size: {_fs(13)}; }}")
        hata_layout.addWidget(self.hata_list)

        hata_sil_btn = QPushButton("Seçili Hatayı Sil")
        hata_sil_btn.setStyleSheet(f"QPushButton {{ background: {self.theme.get('error')}; color: white; border: none; border-radius: {_sz(6)}px; padding: {_sz(8)}px {_sz(14)}px; font-size: {_fs(13)}; }}")
        hata_sil_btn.clicked.connect(self._hata_sil)
        hata_layout.addWidget(hata_sil_btn)
        layout.addWidget(hata_frame)

        not_layout = QHBoxLayout()
        not_lbl = QLabel("Not:")
        not_lbl.setStyleSheet(f"font-size: {_fs(14)};")
        not_layout.addWidget(not_lbl)
        self.not_input = QLineEdit()
        self.not_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        not_layout.addWidget(self.not_input)
        layout.addLayout(not_layout)

        layout.addStretch()

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll, 1)

        # Butonlar scroll dışında - her zaman görünür
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(_sz(20), _sz(8), _sz(20), _sz(12))
        btn_layout.addStretch()
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"QPushButton {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: {_sz(8)}px; padding: {_sz(14)}px {_sz(24)}px; font-size: {_fs(14)}; }}")
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)
        kaydet_btn = QPushButton("Kaydet ve Etiket Bas")
        kaydet_btn.setStyleSheet(f"QPushButton {{ background: {self.theme.get('success')}; color: white; border: none; border-radius: {_sz(8)}px; padding: {_sz(14)}px {_sz(24)}px; font-weight: bold; font-size: {_fs(15)}; }}")
        kaydet_btn.clicked.connect(self._save)
        kaydet_btn.setDefault(True)
        kaydet_btn.setAutoDefault(True)
        btn_layout.addWidget(kaydet_btn)
        outer_layout.addLayout(btn_layout)

    def _update_sure(self):
        gecen = datetime.now() - self.baslangic_zamani
        dk = int(gecen.total_seconds() // 60)
        sn = int(gecen.total_seconds() % 60)
        self.sure_label.setText(f"{dk:02d}:{sn:02d}")

    def _update_hesap(self):
        kontrol = self.kontrol_spin.value()
        saglam = self.saglam_spin.value()
        if saglam > kontrol:
            self.saglam_spin.setValue(kontrol)
            saglam = kontrol
        self.hatali_lbl.setText(str(kontrol - saglam))

    def _hata_ekle(self):
        hata_id = self.hata_combo.currentData()
        hata_adi = self.hata_combo.currentText()
        adet = self.hata_adet_spin.value()
        self.hata_listesi.append({'hata_turu_id': hata_id, 'hata_adi': hata_adi, 'adet': adet})
        self.hata_list.addItem(QListWidgetItem(f"{hata_adi} - {adet} adet"))
        toplam_hata = sum(h['adet'] for h in self.hata_listesi)
        kontrol = self.kontrol_spin.value()
        self.saglam_spin.setValue(max(0, kontrol - toplam_hata))

    def _hata_sil(self):
        current = self.hata_list.currentRow()
        if current >= 0:
            self.hata_list.takeItem(current)
            self.hata_listesi.pop(current)
            toplam_hata = sum(h['adet'] for h in self.hata_listesi)
            kontrol = self.kontrol_spin.value()
            self.saglam_spin.setValue(max(0, kontrol - toplam_hata))

    def _save(self):
        self.timer.stop()
        gecen = datetime.now() - self.baslangic_zamani
        kontrol = self.kontrol_spin.value()
        saglam = self.saglam_spin.value()
        hatali = kontrol - saglam
        if hatali > 0:
            hata_toplam = sum(h['adet'] for h in self.hata_listesi)
            if hata_toplam != hatali:
                QMessageBox.warning(self, "Uyarı", f"Hata adetleri toplamı ({hata_toplam}) ile hatalı adet ({hatali}) eşleşmiyor!")
                self.timer.start(1000)
                return
        self.result_data = {
            'kontrol_miktar': kontrol, 'saglam_miktar': saglam, 'hatali_miktar': hatali,
            'kontrolcu_id': self.personel.get('uuid'), 'kontrolcu_ad': self.personel.get('ad_soyad'),
            'not': self.not_input.text(), 'sure_saniye': int(gecen.total_seconds()), 'hata_listesi': self.hata_listesi
        }
        self.accept()


# =============================================================================
# ANA SAYFA
# =============================================================================

class KaliteFinalKontrolPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.personel_data = None
        self._products = []
        self._selected_product = None
        self._ambalaj_full_paths = [None, None, None]

        # RFID kart okuyucu (lokal - global servis yoksa fallback)
        self._rfid_reader = RFIDCardReader(self)
        self._rfid_reader.card_detected.connect(self._on_card_detected)

        # Global RFID servisine bağlan (lazy load nedeniyle showEvent'te de denenecek)
        self._global_rfid_connected = False
        self._try_connect_global_rfid()

        self._setup_ui()

        # Timerlar
        self.saat_timer = QTimer()
        self.saat_timer.timeout.connect(self._update_time)
        self.saat_timer.start(1000)


    # =========================================================================
    # UI SETUP
    # =========================================================================

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stacked = QStackedWidget()
        layout.addWidget(self.stacked)

        # Sayfa 0: Giriş Paneli
        self._setup_login_page()
        # Sayfa 1: Ana Ekran
        self._setup_main_page()

        self.stacked.setCurrentIndex(0)

    # -------------------------------------------------------------------------
    # Sayfa 0 - Giriş Paneli
    # -------------------------------------------------------------------------

    def _setup_login_page(self):
        login_page = QWidget()
        login_layout = QVBoxLayout(login_page)
        login_layout.setContentsMargins(0, 0, 0, 0)

        # Üst sağ köşe: Yazı boyutu ayarı
        scale_row = QHBoxLayout()
        scale_row.setContentsMargins(0, 8, 16, 0)
        scale_row.addStretch()

        scale_icon = QLabel("Aa")
        scale_icon.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 13px; font-weight: bold;")
        scale_row.addWidget(scale_icon)

        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(6, 25)  # 0.6 - 2.5 arası (10'a bölünecek)
        self.scale_slider.setValue(int(_kalite_scale() * 10))
        self.scale_slider.setFixedWidth(120)
        self.scale_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {self.theme.get('border')};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {self.theme.get('primary')};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
        """)
        self.scale_slider.valueChanged.connect(self._on_scale_changed)
        scale_row.addWidget(self.scale_slider)

        self.scale_value_label = QLabel(f"%{int(_kalite_scale() * 100)}")
        self.scale_value_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px; min-width: 36px;")
        scale_row.addWidget(self.scale_value_label)

        scale_icon_big = QLabel("Aa")
        scale_icon_big.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 18px; font-weight: bold;")
        scale_row.addWidget(scale_icon_big)

        scale_apply_btn = QPushButton("Uygula")
        scale_apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {self.theme.get('primary_hover', self.theme.get('primary'))}; }}
        """)
        scale_apply_btn.setCursor(Qt.PointingHandCursor)
        scale_apply_btn.clicked.connect(self._apply_scale)
        scale_row.addWidget(scale_apply_btn)

        login_layout.addLayout(scale_row)

        # Ortala
        login_layout.addStretch(2)

        center_frame = QFrame()
        center_frame.setFixedWidth(_sz(460))
        center_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 16px;
            }}
        """)
        center_layout = QVBoxLayout(center_frame)
        center_layout.setContentsMargins(40, 40, 40, 40)
        center_layout.setSpacing(20)

        # Başlık
        title = QLabel("Final Kalite Kontrol")
        title.setStyleSheet(f"font-size: {_fs(26)}; font-weight: bold; color: {self.theme.get('primary')}; border: none;")
        title.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(title)

        desc = QLabel("Kartınızı okutun veya sicil numaranızı girin")
        desc.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: {_fs(14)}; border: none;")
        desc.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(desc)

        # Ayırıcı çizgi
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {self.theme.get('border')}; border: none;")
        sep.setFixedHeight(1)
        center_layout.addWidget(sep)

        # Sicil input
        self.sicil_input = QLineEdit()
        self.sicil_input.setPlaceholderText("Sicil No / Kart ID")
        self.sicil_input.setStyleSheet(f"""
            QLineEdit {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 2px solid {self.theme.get('border')};
                border-radius: 10px;
                padding: {_sz(14)}px {_sz(18)}px;
                font-size: {_fs(17)};
            }}
            QLineEdit:focus {{
                border-color: {self.theme.get('primary')};
            }}
        """)
        self.sicil_input.returnPressed.connect(self._login)
        self.sicil_input.installEventFilter(self)
        center_layout.addWidget(self.sicil_input)

        # Giriş butonu
        giris_btn = QPushButton("Giriş Yap")
        giris_btn.setCursor(Qt.PointingHandCursor)
        giris_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: {_sz(10)}px;
                padding: {_sz(14)}px;
                font-size: {_fs(16)};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {self.theme.get('primary_hover', self.theme.get('primary'))};
            }}
        """)
        giris_btn.clicked.connect(self._login)
        center_layout.addWidget(giris_btn)

        # Durum mesajı
        self.login_status = QLabel("")
        self.login_status.setStyleSheet(f"color: {self.theme.get('error')}; font-size: {_fs(13)}; border: none;")
        self.login_status.setAlignment(Qt.AlignCenter)
        self.login_status.setWordWrap(True)
        center_layout.addWidget(self.login_status)

        login_layout.addWidget(center_frame, alignment=Qt.AlignCenter)
        login_layout.addStretch(3)

        self.stacked.addWidget(login_page)

    # -------------------------------------------------------------------------
    # Sayfa 1 - Ana Ekran
    # -------------------------------------------------------------------------

    def _setup_main_page(self):
        main_page = QWidget()
        main_layout = QVBoxLayout(main_page)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # --- Header ---
        header = QHBoxLayout()
        header.setSpacing(12)

        self.personel_label = QLabel("")
        self.personel_label.setStyleSheet(f"""
            color: {self.theme.get('text')};
            font-size: {_fs(15)};
            font-weight: 600;
            background: {self.theme.get('bg_card')};
            border: 1px solid {self.theme.get('border')};
            border-radius: 8px;
            padding: {_sz(8)}px {_sz(14)}px;
        """)
        header.addWidget(self.personel_label)

        header.addStretch()

        self.saat_label = QLabel()
        self.saat_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: {_fs(16)}; font-weight: bold;")
        header.addWidget(self.saat_label)

        refresh_btn = QPushButton("Yenile")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_card')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                padding: {_sz(8)}px {_sz(16)}px;
                font-weight: 500;
                font-size: {_fs(13)};
            }}
            QPushButton:hover {{ background: {self.theme.get('bg_hover')}; }}
        """)
        refresh_btn.clicked.connect(self._manual_refresh)
        header.addWidget(refresh_btn)

        cikis_btn = QPushButton("Çıkış")
        cikis_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('error')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: {_sz(8)}px {_sz(16)}px;
                font-weight: 600;
                font-size: {_fs(13)};
            }}
            QPushButton:hover {{ background: {self.theme.get('error_dark', self.theme.get('error'))}; }}
        """)
        cikis_btn.clicked.connect(self._logout)
        header.addWidget(cikis_btn)

        main_layout.addLayout(header)

        # --- Tab Widget ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                background: transparent;
            }}
            QTabBar::tab {{
                background: {self.theme.get('bg_card')};
                color: {self.theme.get('text_muted')};
                border: 1px solid {self.theme.get('border')};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: {_sz(10)}px {_sz(24)}px;
                font-size: {_fs(14)};
                font-weight: 600;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {self.theme.get('bg_main')};
                color: {self.theme.get('primary')};
                border-bottom: 2px solid {self.theme.get('primary')};
            }}
            QTabBar::tab:hover {{
                color: {self.theme.get('text')};
            }}
        """)

        # ===== TAB 1: Bekleyen Ürünler =====
        bekleyen_tab = QWidget()
        bek_layout = QVBoxLayout(bekleyen_tab)
        bek_layout.setContentsMargins(0, 8, 0, 0)
        bek_layout.setSpacing(10)

        # İstatistik Kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        self.stat_bekleyen = self._create_stat_card_ui("Bekleyen", "0", "#3b82f6")
        self.stat_bugun = self._create_stat_card_ui("Bugün Kontrol", "0", "#22c55e")
        self.stat_saglam = self._create_stat_card_ui("Sağlam %", "-", "#10b981")
        self.stat_ret = self._create_stat_card_ui("Ret %", "-", "#ef4444")
        stats_layout.addWidget(self.stat_bekleyen)
        stats_layout.addWidget(self.stat_bugun)
        stats_layout.addWidget(self.stat_saglam)
        stats_layout.addWidget(self.stat_ret)
        bek_layout.addLayout(stats_layout)

        # Filtreler
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara... (İş Emri, Lot, Ürün)")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                padding: {_sz(8)}px {_sz(14)}px;
                font-size: {_fs(14)};
            }}
            QLineEdit:focus {{ border-color: {self.theme.get('primary')}; }}
        """)
        self.search_input.textChanged.connect(self._filter_products)
        filter_layout.addWidget(self.search_input, 1)

        self.musteri_filter = QComboBox()
        self.musteri_filter.setMinimumWidth(200)
        self.musteri_filter.addItem("Tüm Müşteriler", None)
        self.musteri_filter.currentIndexChanged.connect(self._filter_products)
        filter_layout.addWidget(self.musteri_filter)

        bek_layout.addLayout(filter_layout)

        # Ürün Tablosu (tam genişlik)
        self.product_table = QTableWidget()
        self.product_table.setStyleSheet(f"""
            QTableWidget {{
                font-size: {_fs(13)};
            }}
            QHeaderView::section {{
                font-size: {_fs(13)};
                font-weight: bold;
                padding: {_sz(6)}px;
            }}
        """)
        self.product_table.setColumnCount(8)
        self.product_table.setHorizontalHeaderLabels([
            "ID", "İş Emri", "Lot No", "Müşteri", "Ürün", "Miktar", "Bekleme", "urun_id"
        ])
        self.product_table.setColumnHidden(0, True)
        self.product_table.setColumnHidden(7, True)
        self.product_table.setColumnWidth(1, _sz(110))
        self.product_table.setColumnWidth(2, _sz(120))
        self.product_table.setColumnWidth(3, _sz(180))
        self.product_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.product_table.setColumnWidth(5, _sz(90))
        self.product_table.setColumnWidth(6, _sz(90))
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.product_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.setAlternatingRowColors(True)
        self.product_table.currentCellChanged.connect(self._on_product_selected)
        self.product_table.doubleClicked.connect(self._show_product_detail_dialog)
        bek_layout.addWidget(self.product_table, 1)

        # Alt bar: Detay butonu + Kontrole Başla
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(12)

        detail_btn = QPushButton("📋 Ürün Detay / Ambalaj")
        detail_btn.setCursor(Qt.PointingHandCursor)
        detail_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_card')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: {_sz(10)}px;
                padding: {_sz(12)}px {_sz(20)}px;
                font-size: {_fs(15)};
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {self.theme.get('primary')};
                color: {self.theme.get('primary')};
            }}
        """)
        detail_btn.clicked.connect(self._show_product_detail_dialog)
        bottom_bar.addWidget(detail_btn)

        bottom_bar.addStretch()

        self.basla_btn = QPushButton("KONTROLE BAŞLA")
        self.basla_btn.setEnabled(False)
        self.basla_btn.setCursor(Qt.PointingHandCursor)
        self.basla_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: {_sz(10)}px;
                padding: {_sz(12)}px {_sz(40)}px;
                font-size: {_fs(16)};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {self.theme.get('primary_hover', self.theme.get('primary'))};
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_disabled', self.theme.get('text_muted'))};
            }}
        """)
        self.basla_btn.clicked.connect(self._basla_kontrol)
        bottom_bar.addWidget(self.basla_btn)

        bek_layout.addLayout(bottom_bar)

        self.son_islem_label = QLabel("")
        self.son_islem_label.setStyleSheet(f"""
            color: {self.theme.get('text_muted')};
            font-size: {_fs(13)};
            background: {self.theme.get('bg_card')};
            border: 1px solid {self.theme.get('border')};
            border-radius: 6px;
            padding: {_sz(6)}px {_sz(12)}px;
        """)
        bek_layout.addWidget(self.son_islem_label)

        self.tab_widget.addTab(bekleyen_tab, "Bekleyen Ürünler")

        # ===== TAB 2: Onaylı Ürünler =====
        onayli_tab = self._build_onayli_tab()
        self.tab_widget.addTab(onayli_tab, "Onaylı Ürünler")

        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(self.tab_widget, 1)

        self.stacked.addWidget(main_page)

    # -------------------------------------------------------------------------
    # İstatistik kartı helper
    # -------------------------------------------------------------------------

    def _create_stat_card_ui(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-left: 4px solid {color};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(_sz(14), _sz(8), _sz(14), _sz(8))
        layout.setSpacing(_sz(4))

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: {_fs(13)}; border: none;")
        layout.addWidget(title_lbl)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("stat_value")
        val_lbl.setStyleSheet(f"color: {color}; font-size: {_fs(24)}; font-weight: bold; border: none;")
        layout.addWidget(val_lbl)

        return card

    # =========================================================================
    # GLOBAL RFID BAĞLANTISI
    # =========================================================================

    def _try_connect_global_rfid(self):
        """Global RFID servisine bağlanmaya çalış."""
        if self._global_rfid_connected:
            return
        try:
            from core.rfid_service import RFIDService
            svc = RFIDService.instance()
            svc.card_detected.connect(self._on_card_detected_global)
            self._global_rfid_connected = True
            print("[KALITE] Global RFID servisine bağlandı")
        except Exception as e:
            print(f"[KALITE] Global RFID bağlantı hatası: {e}")

    def showEvent(self, event):
        """Sayfa gösterildiğinde global RFID bağlantısını kontrol et."""
        super().showEvent(event)
        self._try_connect_global_rfid()

    # =========================================================================
    # EVENT FILTER - RFID / Barkod
    # =========================================================================

    def eventFilter(self, watched, event):
        # Global servis aktifse lokal reader'a gerek yok (Enter zaten global tarafından tüketiliyor)
        if not self._global_rfid_connected and event.type() == QEvent.Type.KeyPress:
            if self._rfid_reader.process_key(event):
                return True
        return super().eventFilter(watched, event)

    def _on_card_detected_global(self, card_id):
        """Global RFID servisinden kart algılandığında."""
        # Sadece bu sayfa görünürse işle
        if self.isVisible():
            print(f"[KALITE] Global RFID kart: {card_id}")
            self._on_card_detected(card_id)

    def _on_card_detected(self, card_id):
        """RFID/barkod kart okunduğunda"""
        if self.stacked.currentIndex() == 0:
            # Giriş ekranında - otomatik giriş
            self.sicil_input.clear()
            self._do_login(card_id)
        # Ana ekrandaysa bir şey yapma (zaten giriş yapılmış)

    # =========================================================================
    # YAZI BOYUTU AYARI
    # =========================================================================

    def _on_scale_changed(self, value):
        """Slider değiştiğinde label güncelle"""
        scale = value / 10.0
        self.scale_value_label.setText(f"%{int(scale * 100)}")

    def _apply_scale(self):
        """Yazı boyutunu kaydet ve sayfayı yeniden oluştur"""
        scale = self.scale_slider.value() / 10.0
        try:
            from core.external_config import config_manager
            config_manager.set('kalite_ui_scale', scale)
            config_manager.save()
        except Exception:
            pass

        # Mevcut layout ve içeriğini tamamen temizle
        old_layout = self.layout()
        if old_layout:
            # Önce stacked widget'ı sil
            if self.stacked:
                self.stacked.setParent(None)
                self.stacked.deleteLater()
                self.stacked = None
            # Layout'u kaldır
            QWidget().setLayout(old_layout)

        # Yeniden oluştur
        self._setup_ui()
        self.stacked.setCurrentIndex(0)
        self.sicil_input.setFocus()

    # =========================================================================
    # GİRİŞ / ÇIKIŞ
    # =========================================================================

    def _login(self):
        """Manuel giriş (Enter veya buton ile)"""
        sicil = self.sicil_input.text().strip()
        if not sicil:
            self.login_status.setText("Sicil numarası veya kart ID giriniz!")
            return
        self._do_login(sicil)

    def _do_login(self, sicil_or_card):
        """Personel doğrulama ve yetki kontrolü"""
        self.login_status.setText("")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Personel bul (sicil_no, kart_no veya kart_id ile)
            cursor.execute("""
                SELECT id, uuid, ad, soyad, sicil_no, departman_id, kart_no
                FROM ik.personeller
                WHERE (sicil_no = ? OR kart_no = ? OR kart_id = ?) AND aktif_mi = 1
            """, (sicil_or_card, sicil_or_card, sicil_or_card))
            personel = cursor.fetchone()

            if not personel:
                self.login_status.setText("Personel bulunamadı!")
                conn.close()
                return

            personel_id = personel[0]

            # Yetki kontrolü (Polivelans: "Finak Kalite" seviye >= 3)
            cursor.execute("""
                SELECT MAX(py.seviye) as max_seviye
                FROM ik.personel_yetkinlikler py
                INNER JOIN ik.yetkinlikler y ON py.yetkinlik_id = y.id
                WHERE py.personel_id = ? AND y.kategori = 'Finak Kalite' AND py.seviye >= 3
            """, (personel_id,))
            yetki = cursor.fetchone()

            if not yetki or not yetki[0]:
                self.login_status.setText(
                    f"{personel[2]} {personel[3]} - Final Kalite yetkisi yok!\n(Polivelans seviye 3+ gerekli)"
                )
                conn.close()
                return

            conn.close()

            # Başarılı giriş
            self.personel_data = {
                'id': personel_id,
                'uuid': str(personel[1]),
                'ad': personel[2],
                'soyad': personel[3],
                'sicil_no': personel[4],
                'ad_soyad': f"{personel[2]} {personel[3]}"
            }

            self.personel_label.setText(f"{self.personel_data['ad_soyad']}")
            self.sicil_input.clear()

            # Ana ekrana geç
            self.stacked.setCurrentIndex(1)
            self._load_products()
            self._load_stats()
            self._load_filters()
            self._load_son_islemler()

        except Exception as e:
            self.login_status.setText(f"Giriş hatası: {e}")

    def _logout(self):
        """Çıkış - giriş ekranına dön"""
        self.personel_data = None
        self._selected_product = None
        self._products = []
        self.product_table.setRowCount(0)
        self.basla_btn.setEnabled(False)
        self.stacked.setCurrentIndex(0)
        self.sicil_input.setFocus()

    # =========================================================================
    # VERİ YÜKLEME
    # =========================================================================

    def _load_products(self):
        """FKK deposundaki bekleyen ürünleri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT
                    ie.id as is_emri_id, ie.is_emri_no, sb.lot_no,
                    ie.cari_unvani, ie.stok_kodu, ie.stok_adi,
                    sb.miktar as kalan_miktar, sb.son_hareket_tarihi, sb.urun_id
                FROM stok.stok_bakiye sb
                INNER JOIN tanim.depolar d ON sb.depo_id = d.id
                LEFT JOIN siparis.is_emirleri ie ON (sb.lot_no = ie.lot_no OR sb.parent_lot_no = ie.lot_no)
                WHERE d.kod = 'FKK'
                  AND sb.miktar > 0
                  AND sb.durum_kodu = 'FKK_BEKLIYOR'
                  AND sb.kalite_durumu IN ('KONTROL_BEKLIYOR', 'BEKLIYOR', 'OK')
                ORDER BY sb.son_hareket_tarihi ASC
            """)
            rows = cursor.fetchall()
            conn.close()

            self._products = []
            for row in rows:
                self._products.append({
                    'is_emri_id': row[0],
                    'is_emri_no': row[1] or '',
                    'lot_no': row[2] or '',
                    'cari_unvani': row[3] or '',
                    'stok_kodu': row[4] or '',
                    'stok_adi': row[5] or '',
                    'miktar': float(row[6] or 0),
                    'son_hareket_tarihi': row[7],
                    'urun_id': row[8],
                })

            self._display_products(self._products)
            self._load_stats()

        except Exception as e:
            print(f"Ürün yükleme hatası: {e}")
            import traceback
            traceback.print_exc()

    def _display_products(self, products):
        """Ürünleri tabloda göster"""
        self.product_table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.product_table.setItem(i, 0, QTableWidgetItem(str(p['is_emri_id'] or '')))

            ie_item = QTableWidgetItem(p['is_emri_no'])
            ie_item.setForeground(QColor(self.theme.get('primary')))
            ie_item.setFont(QFont("", -1, QFont.Bold))
            self.product_table.setItem(i, 1, ie_item)

            self.product_table.setItem(i, 2, QTableWidgetItem(p['lot_no']))
            self.product_table.setItem(i, 3, QTableWidgetItem(p['cari_unvani'][:25]))

            urun = f"{p['stok_kodu']} - {p['stok_adi']}" if p['stok_kodu'] else p['stok_adi']
            self.product_table.setItem(i, 4, QTableWidgetItem(urun[:40]))

            miktar_item = QTableWidgetItem(f"{p['miktar']:,.0f}")
            miktar_item.setTextAlignment(Qt.AlignCenter)
            self.product_table.setItem(i, 5, miktar_item)

            # Bekleme süresi
            if p['son_hareket_tarihi']:
                delta = datetime.now() - p['son_hareket_tarihi']
                h = int(delta.total_seconds() // 3600)
                m = int((delta.total_seconds() % 3600) // 60)
                bekleme_text = f"{h}s {m}dk"
                if h >= 24:
                    color = self.theme.get('error')
                elif h >= 8:
                    color = self.theme.get('warning')
                else:
                    color = self.theme.get('text_muted')
            else:
                bekleme_text = '-'
                color = self.theme.get('text_muted')

            bekleme_item = QTableWidgetItem(bekleme_text)
            bekleme_item.setForeground(QColor(color))
            bekleme_item.setTextAlignment(Qt.AlignCenter)
            self.product_table.setItem(i, 6, bekleme_item)

            self.product_table.setItem(i, 7, QTableWidgetItem(str(p.get('urun_id', '') or '')))

            self.product_table.setRowHeight(i, _sz(40))

    def _load_stats(self):
        """İstatistik kartlarını güncelle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Bekleyen sayısı
            cursor.execute("""
                SELECT COUNT(*), ISNULL(SUM(sb.miktar), 0)
                FROM stok.stok_bakiye sb
                INNER JOIN tanim.depolar d ON sb.depo_id = d.id
                WHERE d.kod = 'FKK' AND sb.miktar > 0 AND sb.durum_kodu = 'FKK_BEKLIYOR'
            """)
            bek_row = cursor.fetchone()
            bekleyen_count = bek_row[0] or 0

            # Bugün tamamlanan
            cursor.execute("""
                SELECT COUNT(*), ISNULL(SUM(saglam_adet), 0), ISNULL(SUM(hatali_adet), 0)
                FROM kalite.final_kontrol
                WHERE CAST(kontrol_tarihi AS DATE) = CAST(GETDATE() AS DATE)
            """)
            tam_row = cursor.fetchone()
            bugun_count = tam_row[0] or 0
            bugun_saglam = tam_row[1] or 0
            bugun_hatali = tam_row[2] or 0

            conn.close()

            # Kartları güncelle
            self.stat_bekleyen.findChild(QLabel, "stat_value").setText(str(bekleyen_count))
            self.stat_bugun.findChild(QLabel, "stat_value").setText(str(bugun_count))

            toplam = bugun_saglam + bugun_hatali
            if toplam > 0:
                saglam_pct = (bugun_saglam / toplam) * 100
                ret_pct = (bugun_hatali / toplam) * 100
                self.stat_saglam.findChild(QLabel, "stat_value").setText(f"{saglam_pct:.1f}%")
                self.stat_ret.findChild(QLabel, "stat_value").setText(f"{ret_pct:.1f}%")
            else:
                self.stat_saglam.findChild(QLabel, "stat_value").setText("-")
                self.stat_ret.findChild(QLabel, "stat_value").setText("-")

        except Exception as e:
            print(f"İstatistik yükleme hatası: {e}")

    def _load_filters(self):
        """Müşteri filtresini yükle"""
        try:
            if self.musteri_filter.count() > 1:
                return  # Zaten yüklü

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT ie.cari_unvani
                FROM stok.stok_bakiye sb
                INNER JOIN tanim.depolar d ON sb.depo_id = d.id
                LEFT JOIN siparis.is_emirleri ie ON (sb.lot_no = ie.lot_no OR sb.parent_lot_no = ie.lot_no)
                WHERE d.kod = 'FKK'
                  AND sb.miktar > 0
                  AND ie.cari_unvani IS NOT NULL
                ORDER BY ie.cari_unvani
            """)
            for row in cursor.fetchall():
                if row[0]:
                    self.musteri_filter.addItem(row[0][:30], row[0])
            conn.close()
        except Exception as e:
            print(f"Filtre yükleme hatası: {e}")

    def _load_son_islemler(self):
        """Son işlemleri göster"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 3
                    fk.lot_no, fk.saglam_adet, fk.hatali_adet, fk.sonuc
                FROM kalite.final_kontrol fk
                WHERE CAST(fk.kontrol_tarihi AS DATE) = CAST(GETDATE() AS DATE)
                ORDER BY fk.kontrol_tarihi DESC
            """)
            rows = cursor.fetchall()
            conn.close()

            if rows:
                parts = []
                for row in rows:
                    lot = row[0] or ''
                    saglam = row[1] or 0
                    hatali = row[2] or 0
                    sonuc = row[3] or ''
                    if sonuc == 'ONAY':
                        parts.append(f"{lot} - {saglam} adet sağlam")
                    elif sonuc == 'RED':
                        parts.append(f"{lot} - {hatali} ret")
                    else:
                        parts.append(f"{lot} - {saglam} sağlam, {hatali} ret")
                self.son_islem_label.setText("Son: " + " | ".join(parts))
            else:
                self.son_islem_label.setText("Bugün henüz kontrol yapılmadı")
        except Exception as e:
            self.son_islem_label.setText("")
            print(f"Son işlem yükleme hatası: {e}")

    # =========================================================================
    # ÜRÜN SEÇİMİ VE DETAY
    # =========================================================================

    def _on_product_selected(self, row, col, prev_row, prev_col):
        """Tablo satırı seçildiğinde ürünü seç"""
        if row < 0 or row >= self.product_table.rowCount():
            self._selected_product = None
            self.basla_btn.setEnabled(False)
            return

        is_emri_id_item = self.product_table.item(row, 0)
        lot_no_item = self.product_table.item(row, 2)

        if not is_emri_id_item:
            return

        is_emri_id_text = is_emri_id_item.text()
        lot_no_text = lot_no_item.text() if lot_no_item else ''

        selected = None
        for p in self._products:
            if str(p.get('is_emri_id', '')) == is_emri_id_text and p.get('lot_no', '') == lot_no_text:
                selected = p
                break

        if not selected:
            self._selected_product = None
            self.basla_btn.setEnabled(False)
            return

        self._selected_product = selected
        self.basla_btn.setEnabled(True)

    def _show_product_detail_dialog(self, *args):
        """Seçili ürünün detayını dialog olarak göster"""
        if not self._selected_product:
            return

        p = self._selected_product
        t = self.theme

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Ürün Detay — {p.get('stok_kodu', '')}")
        dlg.setMinimumSize(_sz(700), _sz(550))
        dlg.setStyleSheet(f"QDialog {{ background: {t.get('bg_main')}; }}")

        main_layout = QVBoxLayout(dlg)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Üst: Resim + Bilgiler yan yana
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)

        # Sol: Ürün Resmi
        img_label = QLabel("Resim bulunamadı")
        img_label.setFixedSize(_sz(320), _sz(240))
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet(f"""
            background: {t.get('bg_input')};
            border: 1px solid {t.get('border')};
            border-radius: 10px;
            color: {t.get('text_muted')};
            font-size: {_fs(14)};
        """)

        # Resmi yükle
        stok_kodu = p.get('stok_kodu', '')
        if stok_kodu:
            base = NAS_PATHS.get("image_path", "")
            for ext in ['.jpg', '.JPG', '.jpeg', '.png', '.PNG']:
                path = os.path.join(base, f"{stok_kodu}{ext}")
                if os.path.exists(path):
                    pixmap = QPixmap(path).scaled(_sz(320), _sz(240), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    img_label.setPixmap(pixmap)
                    break

        top_layout.addWidget(img_label)

        # Sağ: Bilgiler
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background: {t.get('bg_card')};
                border: 1px solid {t.get('border')};
                border-radius: 10px;
            }}
        """)
        info_layout = QGridLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(8)

        detail_data = [
            ("Müşteri", p.get('cari_unvani', '-')),
            ("Stok Kodu", stok_kodu or '-'),
            ("Kontrol Miktarı", f"{p.get('miktar', 0):,.0f} adet"),
        ]

        # DB'den ürün detaylarını çek
        urun_id = p.get('urun_id')
        if urun_id:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        u.teknik_resim_no,
                        u.en_mm, u.boy_mm, u.yukseklik_mm, u.agirlik_kg,
                        u.yuzey_alani_m2, u.renk_kodu, u.ral_kodu,
                        u.kalinlik_min_um, u.kalinlik_hedef_um, u.kalinlik_max_um,
                        kt.ad as kaplama_turu_adi
                    FROM stok.urunler u
                    LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                    WHERE u.id = ?
                """, (urun_id,))
                row = cursor.fetchone()
                conn.close()

                if row:
                    detail_data.append(("Teknik Resim", row[0] or '-'))

                    parts = []
                    if row[1]: parts.append(str(row[1]))
                    if row[2]: parts.append(str(row[2]))
                    if row[3]: parts.append(str(row[3]))
                    detail_data.append(("Boyut", (" x ".join(parts) + " mm") if parts else '-'))

                    detail_data.append(("Ağırlık", f"{row[4]} kg" if row[4] else '-'))
                    detail_data.append(("Kaplama", row[11] or '-'))

                    kal = []
                    if row[8]: kal.append(str(row[8]))
                    if row[9]: kal.append(str(row[9]))
                    if row[10]: kal.append(str(row[10]))
                    detail_data.append(("Kalınlık", ("/".join(kal) + " µm") if kal else '-'))

                    renk = []
                    if row[6]: renk.append(row[6])
                    if row[7]: renk.append(f"RAL {row[7]}")
                    detail_data.append(("Renk", " / ".join(renk) if renk else '-'))

                    detail_data.append(("Yüzey Alanı", f"{row[5]} m²" if row[5] else '-'))
            except Exception as e:
                print(f"Detay dialog DB hatası: {e}")

        for i, (label, value) in enumerate(detail_data):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {t.get('text_muted')}; font-size: {_fs(13)}; border: none;")
            val = QLabel(str(value))
            val.setStyleSheet(f"color: {t.get('text')}; font-size: {_fs(14)}; font-weight: 600; border: none;")
            val.setWordWrap(True)
            info_layout.addWidget(lbl, i, 0)
            info_layout.addWidget(val, i, 1)

        info_layout.setRowStretch(len(detail_data), 1)
        top_layout.addWidget(info_frame, 1)
        main_layout.addLayout(top_layout)

        # Alt: Ambalajlama Talimatları
        ambalaj_header = QLabel("📦 Ambalajlama Talimatları")
        ambalaj_header.setStyleSheet(f"color: {t.get('primary')}; font-size: {_fs(15)}; font-weight: bold;")
        main_layout.addWidget(ambalaj_header)

        ambalaj_row = QHBoxLayout()
        ambalaj_row.setSpacing(12)

        cari_unvani = p.get('cari_unvani', '')
        cari_temiz = cari_unvani
        kod_temiz = stok_kodu
        for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            cari_temiz = cari_temiz.replace(char, '_') if cari_temiz else 'Genel'
            kod_temiz = kod_temiz.replace(char, '_') if kod_temiz else ''

        base_path = NAS_PATHS.get("product_path", "")
        klasor = os.path.join(base_path, cari_temiz, kod_temiz, '10_Ambalajlama_Talimatlari')

        ambalaj_paths = []
        for i in range(3):
            found_path = None
            for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.JPG', '.JPEG', '.PNG', '.BMP']:
                dosya = os.path.join(klasor, f"ambalaj_{i + 1}{ext}")
                if os.path.exists(dosya):
                    found_path = dosya
                    break
            ambalaj_paths.append(found_path)

            thumb_frame = QFrame()
            thumb_frame.setStyleSheet(f"""
                QFrame {{
                    background: {t.get('bg_card')};
                    border: 1px solid {t.get('border') if not found_path else t.get('success', '#10B981')};
                    border-radius: 8px;
                }}
            """)
            thumb_layout = QVBoxLayout(thumb_frame)
            thumb_layout.setContentsMargins(8, 8, 8, 8)
            thumb_layout.setSpacing(4)

            thumb_label = QLabel()
            thumb_label.setFixedSize(_sz(180), _sz(130))
            thumb_label.setAlignment(Qt.AlignCenter)

            if found_path:
                pix = QPixmap(found_path)
                if not pix.isNull():
                    thumb_label.setPixmap(pix.scaled(_sz(180), _sz(130), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    thumb_label.setCursor(Qt.PointingHandCursor)
                    fp = found_path
                    idx = i
                    thumb_label.mousePressEvent = lambda ev, f=fp, n=idx: self._show_ambalaj_dialog(f, n, dlg)
            else:
                thumb_label.setText(f"Adım {i + 1}\n(yok)")
                thumb_label.setStyleSheet(f"color: {t.get('text_muted')}; font-size: {_fs(12)};")

            thumb_layout.addWidget(thumb_label, alignment=Qt.AlignCenter)

            step_lbl = QLabel(f"Adım {i + 1}")
            step_lbl.setAlignment(Qt.AlignCenter)
            step_lbl.setStyleSheet(f"color: {t.get('text_secondary')}; font-size: {_fs(12)}; font-weight: bold;")
            thumb_layout.addWidget(step_lbl)

            ambalaj_row.addWidget(thumb_frame)

        ambalaj_row.addStretch()
        main_layout.addLayout(ambalaj_row)

        # Kapat butonu
        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.get('bg_card')};
                color: {t.get('text')};
                border: 1px solid {t.get('border')};
                border-radius: 8px;
                padding: 10px 30px;
                font-size: {_fs(14)};
                font-weight: bold;
            }}
            QPushButton:hover {{ border-color: {t.get('primary')}; color: {t.get('primary')}; }}
        """)
        close_btn.clicked.connect(dlg.close)
        main_layout.addWidget(close_btn, alignment=Qt.AlignRight)

        dlg.exec()

    def _show_ambalaj_dialog(self, dosya, index, parent_dlg):
        """Ambalaj fotoğrafını tam boyut göster"""
        pixmap = QPixmap(dosya)
        if pixmap.isNull():
            return

        dlg = QDialog(parent_dlg)
        dlg.setWindowTitle(f"Ambalajlama — Adım {index + 1}")
        dlg.setMinimumSize(700, 520)
        dlg.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main')}; }}")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        scaled = pixmap.scaled(660, 460, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_label.setPixmap(scaled)
        layout.addWidget(img_label)

        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: bold;")
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        dlg.exec()

    # Eski detay panel metodları kaldırıldı — artık dialog kullanılıyor

    # =========================================================================
    # FİLTRELEME
    # =========================================================================

    def _filter_products(self):
        """Arama ve müşteri filtresi"""
        search = self.search_input.text().strip().lower()
        musteri = self.musteri_filter.currentData()

        filtered = []
        for p in self._products:
            # Müşteri filtresi
            if musteri and p.get('cari_unvani', '') != musteri:
                continue
            # Arama filtresi
            if search:
                searchable = f"{p.get('is_emri_no', '')} {p.get('lot_no', '')} {p.get('stok_kodu', '')} {p.get('stok_adi', '')} {p.get('cari_unvani', '')}".lower()
                if search not in searchable:
                    continue
            filtered.append(p)

        self._display_products(filtered)

    # =========================================================================
    # KONTROL İŞLEMİ
    # =========================================================================

    def _basla_kontrol(self):
        """Seçili ürün için kontrol başlat"""
        if not self._selected_product or not self.personel_data:
            return

        p = self._selected_product

        # gorev_data oluştur (eski formata uyumlu)
        gorev_data = {
            'is_emri_id': p.get('is_emri_id'),
            'is_emri_no': p.get('is_emri_no', ''),
            'lot_no': p.get('lot_no', ''),
            'cari_unvani': p.get('cari_unvani', ''),
            'stok_kodu': p.get('stok_kodu', ''),
            'stok_adi': p.get('stok_adi', ''),
            'miktar': p.get('miktar', 0),
            'kontrol_adet': p.get('miktar', 0),
            'urun_id': p.get('urun_id'),
        }

        kontrol_dlg = FinalKontrolDialog(gorev_data, self.personel_data, self.theme, self)
        if kontrol_dlg.exec() == QDialog.Accepted and kontrol_dlg.result_data:
            self._kaydet_kontrol(gorev_data, kontrol_dlg.result_data)

    def _kaydet_kontrol(self, gorev_data, result):
        """Kontrol sonucunu kaydet - kontrol_is_emirleri bağımlılığı kaldırıldı"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            from core.hareket_motoru import HareketMotoru
            motor = HareketMotoru(conn)

            saglam = result['saglam_miktar']
            hatali = result['hatali_miktar']
            kontrol = result['kontrol_miktar']
            sure_dk = result['sure_saniye'] // 60

            if hatali == 0:
                sonuc = 'ONAY'
            elif saglam == 0:
                sonuc = 'RED'
            else:
                sonuc = 'KISMI'

            # 1. kalite.final_kontrol tablosuna kayıt ekle
            kontrol_id = None
            try:
                # kontrol_eden_adi kolonu yoksa ekle
                try:
                    cursor.execute("""
                        IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('kalite.final_kontrol') AND name = 'kontrol_eden_adi')
                        ALTER TABLE kalite.final_kontrol ADD kontrol_eden_adi NVARCHAR(100) NULL
                    """)
                except Exception:
                    pass

                cursor.execute("""
                    INSERT INTO kalite.final_kontrol
                    (is_emri_id, lot_no, kontrol_miktar, saglam_adet, hatali_adet,
                     kontrol_eden_id, kontrol_eden_adi, kontrol_tarihi, sonuc, aciklama, olusturma_tarihi)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, ?, GETDATE())
                """, (
                    gorev_data['is_emri_id'],
                    gorev_data.get('lot_no', ''),
                    kontrol,
                    saglam,
                    hatali,
                    self.personel_data['id'],
                    self.personel_data.get('ad_soyad', ''),
                    sonuc,
                    result.get('not', '')
                ))
                kontrol_id = cursor.fetchone()[0]
            except Exception as fc_err:
                print(f"final_kontrol kayıt hatası: {fc_err}")

            is_emri_id = gorev_data['is_emri_id']
            lot_no = gorev_data.get('lot_no', '')
            stok_kodu = gorev_data.get('stok_kodu', '')
            stok_adi = gorev_data.get('stok_adi', '')

            # Toplam tamamlanmış miktarı hesapla (final_kontrol'den)
            cursor.execute("""
                SELECT ISNULL(SUM(kontrol_miktar), 0)
                FROM kalite.final_kontrol
                WHERE is_emri_id = ?
            """, (is_emri_id,))
            tamamlanan_toplam = cursor.fetchone()[0] or 0

            # Orijinal toplam miktarı al
            cursor.execute(
                "SELECT ISNULL(uretilen_miktar, toplam_miktar) FROM siparis.is_emirleri WHERE id = ?",
                (is_emri_id,)
            )
            orijinal_toplam = cursor.fetchone()[0] or 0
            kalan = orijinal_toplam - tamamlanan_toplam

            # 2. Hata kayıtları (kontrol_id = final_kontrol'den dönen id)
            if kontrol_id:
                for hata in result.get('hata_listesi', []):
                    try:
                        cursor.execute("""
                            INSERT INTO kalite.kontrol_hatalar (kontrol_id, hata_turu_id, adet)
                            VALUES (?, ?, ?)
                        """, (kontrol_id, hata.get('hata_turu_id'), hata.get('adet')))
                    except Exception as he:
                        print(f"Hata kaydı eklenemedi: {he}")

            # 3. Depo ID'lerini bul (SEVK ve RED)
            sevk_depo_id = motor.get_depo_by_tip('SEVK')
            if not sevk_depo_id:
                cursor.execute("""
                    SELECT id FROM tanim.depolar
                    WHERE kod IN ('SEVK', 'MAMUL') AND aktif_mi = 1
                    ORDER BY CASE WHEN kod = 'SEVK' THEN 0 ELSE 1 END
                """)
                row = cursor.fetchone()
                sevk_depo_id = row[0] if row else 11

            red_depo_id = motor.get_depo_by_tip('RED')
            if not red_depo_id:
                cursor.execute("SELECT id FROM tanim.depolar WHERE kod = 'RED' AND aktif_mi = 1")
                row = cursor.fetchone()
                red_depo_id = row[0] if row else 12

            # 4. urun_id bul
            urun_id = gorev_data.get('urun_id')
            if not urun_id and stok_kodu:
                cursor.execute("SELECT id FROM stok.urunler WHERE urun_kodu = ? AND aktif_mi = 1", (stok_kodu,))
                urun_row = cursor.fetchone()
                if urun_row:
                    urun_id = urun_row[0]

            if not urun_id:
                cursor.execute("""
                    INSERT INTO stok.urunler (uuid, urun_kodu, urun_adi, urun_tipi, birim_id, aktif_mi,
                                             olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                    OUTPUT INSERTED.id
                    VALUES (NEWID(), ?, ?, 'MAMUL', 1, 1, GETDATE(), GETDATE(), 0)
                """, (stok_kodu or f"URN-{is_emri_id}", stok_adi or f"Ürün {is_emri_id}"))
                urun_id = cursor.fetchone()[0]

            # 5. İş emri durumunu güncelle
            if kalan <= 0:
                if hatali == 0:
                    ie_durum = 'ONAYLANDI'
                elif saglam == 0:
                    ie_durum = 'REDDEDILDI'
                else:
                    ie_durum = 'KISMI_RED'
                cursor.execute("""
                    UPDATE siparis.is_emirleri
                    SET durum = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (ie_durum, is_emri_id))
            else:
                cursor.execute("""
                    UPDATE siparis.is_emirleri
                    SET guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (is_emri_id,))

            # 6. STOK HAREKETLERİ
            if lot_no:
                # FKK deposunun ID'sini al
                cursor.execute("SELECT id FROM tanim.depolar WHERE kod = 'FKK'")
                fkk_row = cursor.fetchone()
                fkk_depo_id = fkk_row[0] if fkk_row else 10

                # Mevcut bakiyeyi kontrol et
                cursor.execute("""
                    SELECT miktar, depo_id FROM stok.stok_bakiye
                    WHERE lot_no = ? AND depo_id = ?
                """, (lot_no, fkk_depo_id))
                bakiye_row = cursor.fetchone()
                mevcut_miktar = float(bakiye_row[0]) if bakiye_row else 0

                kontrol_toplam = saglam + hatali

                # Sağlam -> SEVK DEPO
                if saglam > 0 and sevk_depo_id:
                    sevk_lot = f"{lot_no}-SEV"
                    sevk_sonuc = motor.stok_giris(
                        urun_id=urun_id,
                        miktar=saglam,
                        lot_no=sevk_lot,
                        depo_id=sevk_depo_id,
                        urun_kodu=stok_kodu,
                        urun_adi=stok_adi,
                        kalite_durumu='ONAYLANDI',
                        durum_kodu='SEVK_HAZIR',
                        aciklama=f"Final kalite onay - Sağlam: {saglam}"
                    )
                    if not sevk_sonuc.basarili:
                        print(f"Sevk giriş hatası: {sevk_sonuc.mesaj}")

                # Hatalı -> RED DEPO
                if hatali > 0 and red_depo_id:
                    lot_prefix = '-'.join(lot_no.split('-')[:3]) if lot_no else ''
                    red_lot = f"{lot_prefix}-RED" if lot_prefix else f"RED-{is_emri_id}"
                    red_sonuc = motor.stok_giris(
                        urun_id=urun_id,
                        miktar=hatali,
                        lot_no=red_lot,
                        depo_id=red_depo_id,
                        urun_kodu=stok_kodu,
                        urun_adi=stok_adi,
                        kalite_durumu='REDDEDILDI',
                        durum_kodu='RED',
                        aciklama=f"Final kalite red - Hatalı: {hatali}"
                    )
                    if not red_sonuc.basarili:
                        print(f"Red stok girişi hatası: {red_sonuc.mesaj}")

                # Orijinal lot bakiyesini güncelle
                kalan_bakiye = mevcut_miktar - kontrol_toplam

                if kalan_bakiye > 0:
                    cursor.execute("""
                        UPDATE stok.stok_bakiye
                        SET miktar = ?,
                            kalite_durumu = 'KONTROL_BEKLIYOR',
                            durum_kodu = 'FKK_BEKLIYOR'
                        WHERE lot_no = ? AND depo_id = ?
                    """, (kalan_bakiye, lot_no, fkk_depo_id))
                else:
                    cursor.execute("""
                        UPDATE stok.stok_bakiye
                        SET miktar = 0,
                            kalite_durumu = 'TAMAMLANDI',
                            durum_kodu = 'SEVK_EDILDI'
                        WHERE lot_no = ? AND depo_id = ?
                    """, (lot_no, fkk_depo_id))

                    # kalite.uretim_redler tablosuna kayıt
                    if hatali > 0:
                        try:
                            hata_listesi = result.get('hata_listesi', [])
                            ilk_hata_turu_id = hata_listesi[0].get('hata_turu_id') if hata_listesi else None

                            cursor.execute("""
                                INSERT INTO kalite.uretim_redler
                                (is_emri_id, lot_no, red_miktar, kontrol_id, red_tarihi,
                                 kontrol_eden_id, durum, aciklama, hata_turu_id, olusturma_tarihi)
                                VALUES (?, ?, ?, ?, GETDATE(), ?, 'BEKLIYOR', ?, ?, GETDATE())
                            """, (is_emri_id, lot_no, hatali, kontrol_id,
                                  self.personel_data['id'], result.get('not', ''), ilk_hata_turu_id))
                        except Exception as red_err:
                            print(f"Üretim red kaydı hatası: {red_err}")

            conn.commit()
            LogManager.log_insert('kalite', 'kalite.uretim_redler', None, 'Yeni kayit eklendi')
            conn.close()

            # Bildirim: Kalite kontrol sonucu
            try:
                from core.bildirim_tetikleyici import BildirimTetikleyici
                ie_no = gorev_data.get('is_emri_no', '')
                if sonuc == 'RED' or hatali > 0:
                    # Red veya kısmi red durumunda uygunsuzluk bildirimi
                    BildirimTetikleyici.uygunsuzluk_acildi(
                        kayit_id=kontrol_id or is_emri_id,
                        kayit_no=ie_no,
                        urun_adi=f"{stok_kodu} - Saglam:{saglam} Hatali:{hatali}",
                    )
                if kalan <= 0 and sonuc == 'ONAY':
                    # Tamamı onaylandıysa sevkiyata bildirim
                    BildirimTetikleyici.onay_bekliyor(
                        onaylayici_id=None,
                        kayit_tipi='Sevkiyat',
                        kayit_aciklama=f"{ie_no} - {stok_adi} kalite onayi tamamlandi, sevkiyata hazir.",
                        kaynak_tablo='siparis.is_emirleri',
                        kaynak_id=is_emri_id,
                        sayfa_yonlendirme='sevk_liste',
                    )
            except Exception as bt_err:
                print(f"Bildirim hatasi: {bt_err}")

            # Etiket bas
            if saglam > 0:
                self._bas_etiket(gorev_data, result)

            # Sonuç mesajı
            msg = f"Kontrol Tamamlandı!\n\nKontrol: {kontrol:,} adet\nSağlam: {saglam:,} -> SEVK DEPO\n"
            if hatali > 0:
                msg += f"Hatalı: {hatali:,} -> RED DEPO\n"
            if kalan > 0:
                msg += f"\nKalan Bakiye: {kalan:,} adet (Beklemede)"
            QMessageBox.information(self, "Başarılı", msg)

            # Verileri yenile
            self._load_products()
            self._load_son_islemler()
            self._selected_product = None
            self.basla_btn.setEnabled(False)

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")

    # =========================================================================
    # ETİKET BASIMI
    # =========================================================================

    def _bas_etiket(self, gorev_data, result):
        try:
            hatali = result['hatali_miktar']
            saglam = result['saglam_miktar']
            if hatali == 0:
                sonuc = 'ONAY'
            elif saglam == 0:
                sonuc = 'RED'
            else:
                sonuc = 'KISMI'

            etiket_data = {
                'musteri': gorev_data.get('cari_unvani', '') or '',
                'stok_adi': gorev_data.get('stok_adi', '') or '',
                'stok_kodu': gorev_data.get('stok_kodu', '') or '',
                'lot_no': gorev_data.get('lot_no', '') or '',
                'miktar': saglam,
                'tarih': datetime.now(),
                'kontrolcu': result.get('kontrolcu_ad', ''),
                'is_emri_no': gorev_data.get('is_emri_no', ''),
                'kontrol_tarihi': datetime.now(),
                'saglam_adet': saglam,
                'hatali_adet': hatali,
                'sonuc': sonuc,
            }
            dlg = EtiketOnizlemeDialog(self.theme, etiket_data, self)
            if dlg.exec() != QDialog.Accepted:
                return

            sablon_id = dlg.get_sablon_id()
            yazici = dlg.get_yazici()
            mod = dlg.get_mod()

            etiketler = [etiket_data]
            if sablon_id:
                etiketler[0]['sablon_id'] = sablon_id

            if mod in ("ZPL", "EZPL") and yazici and yazici != 'PDF_ONLY':
                # Godex direkt yazdirma (giris kalite ile ayni)
                from utils.etiket_yazdir import godex_yazdir
                basarili = godex_yazdir(etiketler, yazici, mod)
                if basarili:
                    print(f"Etiket Godex yaziciya gonderildi: {yazici}")
                else:
                    print("Godex gonderilemedi, PDF aciliyor")
                    self._fallback_pdf_etiket(etiketler, sablon_id)
            else:
                # PDF mod
                self._fallback_pdf_etiket(etiketler, sablon_id)
        except Exception as e:
            print(f"Etiket hatası: {e}")
            import traceback
            traceback.print_exc()

    def _fallback_pdf_etiket(self, etiketler, sablon_id=None):
        """PDF olarak etiket olustur ve ac"""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='fk_etiket_')
            temp_path = temp_file.name
            temp_file.close()
            if sablon_id:
                from utils.etiket_yazdir import sablon_ile_etiket_pdf_olustur
                sablon_ile_etiket_pdf_olustur(temp_path, etiketler, sablon_id)
            else:
                from utils.etiket_yazdir import a4_etiket_pdf_olustur
                a4_etiket_pdf_olustur(temp_path, etiketler)
            subprocess.Popen(['start', '', temp_path], shell=True)
        except Exception as e:
            print(f"PDF etiket hatasi: {e}")

    # =========================================================================
    # ONAYLI ÜRÜNLER SEKMESİ
    # =========================================================================

    def _build_onayli_tab(self):
        """Onaylı ürünler sekmesini oluştur"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        input_style = f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: {_sz(6)}px {_sz(10)}px; font-size: {_fs(13)};"

        # Filtre satırı
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        bas_lbl = QLabel("Başlangıç:")
        bas_lbl.setStyleSheet(f"font-size: {_fs(13)};")
        filter_row.addWidget(bas_lbl)
        self.onayli_tarih_bas = QDateEdit()
        self.onayli_tarih_bas.setDate(QDate.currentDate())
        self.onayli_tarih_bas.setCalendarPopup(True)
        self.onayli_tarih_bas.setDisplayFormat("dd.MM.yyyy")
        self.onayli_tarih_bas.setStyleSheet(input_style)
        self.onayli_tarih_bas.dateChanged.connect(self._load_onayli_urunler)
        filter_row.addWidget(self.onayli_tarih_bas)

        bit_lbl = QLabel("Bitiş:")
        bit_lbl.setStyleSheet(f"font-size: {_fs(13)};")
        filter_row.addWidget(bit_lbl)
        self.onayli_tarih_bit = QDateEdit()
        self.onayli_tarih_bit.setDate(QDate.currentDate())
        self.onayli_tarih_bit.setCalendarPopup(True)
        self.onayli_tarih_bit.setDisplayFormat("dd.MM.yyyy")
        self.onayli_tarih_bit.setStyleSheet(input_style)
        self.onayli_tarih_bit.dateChanged.connect(self._load_onayli_urunler)
        filter_row.addWidget(self.onayli_tarih_bit)

        self.onayli_search = QLineEdit()
        self.onayli_search.setPlaceholderText("Ara... (İş Emri, Lot, Ürün)")
        self.onayli_search.setStyleSheet(input_style)
        self.onayli_search.returnPressed.connect(self._load_onayli_urunler)
        filter_row.addWidget(self.onayli_search, 1)

        onayli_yenile_btn = QPushButton("Yenile")
        onayli_yenile_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_card')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: {_sz(6)}px {_sz(16)}px;
                font-weight: 500;
                font-size: {_fs(13)};
            }}
            QPushButton:hover {{ background: {self.theme.get('bg_hover')}; }}
        """)
        onayli_yenile_btn.clicked.connect(self._load_onayli_urunler)
        filter_row.addWidget(onayli_yenile_btn)

        layout.addLayout(filter_row)

        # Tablo
        self.onayli_table = QTableWidget()
        self.onayli_table.setStyleSheet(f"""
            QTableWidget {{
                font-size: {_fs(13)};
            }}
            QHeaderView::section {{
                font-size: {_fs(13)};
                font-weight: bold;
                padding: {_sz(6)}px;
            }}
        """)
        self.onayli_table.setColumnCount(10)
        self.onayli_table.setHorizontalHeaderLabels([
            "ID", "İş Emri", "Lot No", "Müşteri", "Ürün",
            "Sağlam", "Hatalı", "Sonuç", "Tarih", "Kontrol Eden"
        ])
        self.onayli_table.setColumnHidden(0, True)
        self.onayli_table.setColumnWidth(1, _sz(110))
        self.onayli_table.setColumnWidth(2, _sz(130))
        self.onayli_table.setColumnWidth(3, _sz(150))
        self.onayli_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.onayli_table.setColumnWidth(5, _sz(80))
        self.onayli_table.setColumnWidth(6, _sz(80))
        self.onayli_table.setColumnWidth(7, _sz(80))
        self.onayli_table.setColumnWidth(8, _sz(130))
        self.onayli_table.setColumnWidth(9, _sz(140))
        self.onayli_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.onayli_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.onayli_table.verticalHeader().setVisible(False)
        self.onayli_table.setAlternatingRowColors(True)
        self.onayli_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.onayli_table, 1)

        # Alt butonlar
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.onayli_info_label = QLabel("")
        self.onayli_info_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: {_fs(13)};")
        btn_row.addWidget(self.onayli_info_label)
        btn_row.addStretch()

        etiket_btn = QPushButton("Tekrar Etiket Bas")
        etiket_btn.setCursor(Qt.PointingHandCursor)
        etiket_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: {_sz(10)}px {_sz(24)}px;
                font-size: {_fs(14)};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {self.theme.get('primary_hover', self.theme.get('primary'))};
            }}
        """)
        etiket_btn.clicked.connect(self._tekrar_etiket_bas)
        btn_row.addWidget(etiket_btn)

        red_etiket_btn = QPushButton("Red Etiketi Bas")
        red_etiket_btn.setCursor(Qt.PointingHandCursor)
        red_etiket_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('danger', '#ef4444')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: {_sz(10)}px {_sz(24)}px;
                font-size: {_fs(14)};
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #dc2626; }}
        """)
        red_etiket_btn.clicked.connect(self._red_etiket_bas)
        btn_row.addWidget(red_etiket_btn)

        layout.addLayout(btn_row)

        return tab

    def _on_tab_changed(self, index):
        """Tab değiştiğinde onaylı ürünleri yükle"""
        if index == 1:
            self._load_onayli_urunler()

    def _load_onayli_urunler(self):
        """Onaylı ürünler tablosunu doldur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            tarih_bas = self.onayli_tarih_bas.date().toString("yyyy-MM-dd")
            tarih_bit = self.onayli_tarih_bit.date().toString("yyyy-MM-dd")
            search = self.onayli_search.text().strip()

            query = """
                SELECT fk.id, ie.is_emri_no, fk.lot_no,
                       ie.cari_unvani, CONCAT(ie.stok_kodu, ' - ', ie.stok_adi),
                       fk.saglam_adet, fk.hatali_adet, fk.sonuc,
                       fk.kontrol_tarihi,
                       ISNULL(fk.kontrol_eden_adi, CONCAT(p.ad, ' ', p.soyad)) as kontrolcu
                FROM kalite.final_kontrol fk
                LEFT JOIN siparis.is_emirleri ie ON fk.is_emri_id = ie.id
                LEFT JOIN ik.personeller p ON p.id = fk.kontrol_eden_id
                WHERE CAST(fk.kontrol_tarihi AS DATE) >= ?
                  AND CAST(fk.kontrol_tarihi AS DATE) <= ?
            """
            params = [tarih_bas, tarih_bit]

            if search:
                query += " AND (ie.is_emri_no LIKE ? OR fk.lot_no LIKE ? OR ie.stok_kodu LIKE ? OR ie.cari_unvani LIKE ?)"
                params.extend([f"%{search}%"] * 4)

            query += " ORDER BY fk.kontrol_tarihi DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            self.onayli_table.setRowCount(len(rows))
            sonuc_renk = {'ONAY': '#22c55e', 'RED': '#ef4444', 'KISMI': '#f59e0b'}

            for i, row in enumerate(rows):
                self.onayli_table.setItem(i, 0, QTableWidgetItem(str(row[0] or '')))

                ie_item = QTableWidgetItem(str(row[1] or ''))
                ie_item.setForeground(QColor(self.theme.get('primary')))
                ie_item.setFont(QFont("", -1, QFont.Bold))
                self.onayli_table.setItem(i, 1, ie_item)

                self.onayli_table.setItem(i, 2, QTableWidgetItem(str(row[2] or '')))
                self.onayli_table.setItem(i, 3, QTableWidgetItem(str(row[3] or '')[:25]))
                self.onayli_table.setItem(i, 4, QTableWidgetItem(str(row[4] or '')[:40]))

                saglam_item = QTableWidgetItem(f"{row[5] or 0:,.0f}")
                saglam_item.setTextAlignment(Qt.AlignCenter)
                self.onayli_table.setItem(i, 5, saglam_item)

                hatali_item = QTableWidgetItem(f"{row[6] or 0:,.0f}")
                hatali_item.setTextAlignment(Qt.AlignCenter)
                if row[6] and row[6] > 0:
                    hatali_item.setForeground(QColor('#ef4444'))
                self.onayli_table.setItem(i, 6, hatali_item)

                sonuc = str(row[7] or '')
                sonuc_item = QTableWidgetItem(sonuc)
                sonuc_item.setForeground(QColor(sonuc_renk.get(sonuc, '#888')))
                sonuc_item.setFont(QFont("", -1, QFont.Bold))
                sonuc_item.setTextAlignment(Qt.AlignCenter)
                self.onayli_table.setItem(i, 7, sonuc_item)

                tarih_str = row[8].strftime('%d.%m.%Y %H:%M') if row[8] else ''
                self.onayli_table.setItem(i, 8, QTableWidgetItem(tarih_str))
                self.onayli_table.setItem(i, 9, QTableWidgetItem(str(row[9] or '')))

                self.onayli_table.setRowHeight(i, 40)

            self.onayli_info_label.setText(f"Toplam {len(rows)} kayıt")

        except Exception as e:
            print(f"Onaylı ürünler yükleme hatası: {e}")
            import traceback
            traceback.print_exc()

    def _tekrar_etiket_bas(self):
        """Seçili onaylı ürün için tekrar etiket bas"""
        row = self.onayli_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kayıt seçin!")
            return

        # Tablodan verileri al
        lot_no = self.onayli_table.item(row, 2).text() if self.onayli_table.item(row, 2) else ''
        musteri = self.onayli_table.item(row, 3).text() if self.onayli_table.item(row, 3) else ''
        urun = self.onayli_table.item(row, 4).text() if self.onayli_table.item(row, 4) else ''
        saglam = self.onayli_table.item(row, 5).text() if self.onayli_table.item(row, 5) else '0'
        hatali = self.onayli_table.item(row, 6).text() if self.onayli_table.item(row, 6) else '0'
        sonuc = self.onayli_table.item(row, 7).text() if self.onayli_table.item(row, 7) else ''
        kontrolcu = self.onayli_table.item(row, 9).text() if self.onayli_table.item(row, 9) else ''
        is_emri_no = self.onayli_table.item(row, 1).text() if self.onayli_table.item(row, 1) else ''

        # stok_kodu ve stok_adi ayır
        parts = urun.split(' - ', 1)
        stok_kodu = parts[0].strip() if parts else ''
        stok_adi = parts[1].strip() if len(parts) > 1 else urun

        # Miktar string -> float
        try:
            saglam_adet = float(saglam.replace(',', ''))
        except ValueError:
            saglam_adet = 0
        try:
            hatali_adet = float(hatali.replace(',', ''))
        except ValueError:
            hatali_adet = 0

        etiket_data = {
            'musteri': musteri,
            'stok_adi': stok_adi,
            'stok_kodu': stok_kodu,
            'lot_no': lot_no,
            'miktar': saglam_adet,
            'tarih': datetime.now(),
            'kontrolcu': kontrolcu,
            'is_emri_no': is_emri_no,
            'kontrol_tarihi': datetime.now(),
            'saglam_adet': saglam_adet,
            'hatali_adet': hatali_adet,
            'sonuc': sonuc,
        }

        dlg = EtiketOnizlemeDialog(self.theme, etiket_data, self)
        if dlg.exec() != QDialog.Accepted:
            return

        sablon_id = dlg.get_sablon_id()
        yazici = dlg.get_yazici()
        mod = dlg.get_mod()

        try:
            etiketler = [etiket_data]
            if sablon_id:
                etiketler[0]['sablon_id'] = sablon_id

            if mod in ("ZPL", "EZPL") and yazici and yazici != 'PDF_ONLY':
                from utils.etiket_yazdir import godex_yazdir
                basarili = godex_yazdir(etiketler, yazici, mod)
                if basarili:
                    print(f"Tekrar etiket Godex yaziciya gonderildi: {yazici}")
                else:
                    print("Godex gonderilemedi, PDF aciliyor")
                    self._fallback_pdf_etiket(etiketler, sablon_id)
            else:
                self._fallback_pdf_etiket(etiketler, sablon_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Etiket oluşturma hatası: {e}")

    def _red_etiket_bas(self):
        """Seçili kayıt için RED etiketi bas"""
        row = self.onayli_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kayıt seçin!")
            return

        sonuc = self.onayli_table.item(row, 7).text() if self.onayli_table.item(row, 7) else ''
        if sonuc != 'RED':
            QMessageBox.warning(self, "Uyarı", "Red etiketi sadece RED sonuçlu kayıtlar için basılabilir!")
            return

        lot_no = self.onayli_table.item(row, 2).text() if self.onayli_table.item(row, 2) else ''
        musteri = self.onayli_table.item(row, 3).text() if self.onayli_table.item(row, 3) else ''
        urun = self.onayli_table.item(row, 4).text() if self.onayli_table.item(row, 4) else ''
        saglam = self.onayli_table.item(row, 5).text() if self.onayli_table.item(row, 5) else '0'
        hatali = self.onayli_table.item(row, 6).text() if self.onayli_table.item(row, 6) else '0'
        kontrolcu = self.onayli_table.item(row, 9).text() if self.onayli_table.item(row, 9) else ''

        parts = urun.split(' - ', 1)
        stok_kodu = parts[0].strip() if parts else ''
        stok_adi = parts[1].strip() if len(parts) > 1 else urun

        try:
            hatali_adet = float(hatali.replace(',', ''))
        except ValueError:
            hatali_adet = 0

        etiket_data = {
            'musteri': musteri,
            'stok_kodu': stok_kodu,
            'stok_adi': stok_adi,
            'lot_no': lot_no,
            'miktar': hatali_adet,
            'birim': 'ADET',
            'kontrolcu': kontrolcu,
            'tarih': datetime.now(),
            'sonuc': 'RED',
        }

        dlg = EtiketOnizlemeDialog(self.theme, etiket_data, self)
        if dlg.exec() != QDialog.Accepted:
            return

        yazici = dlg.get_yazici()
        mod = dlg.get_mod()

        try:
            if mod in ("ZPL", "EZPL") and yazici and yazici != 'PDF_ONLY':
                from utils.etiket_yazdir import godex_yazdir
                etiket_data['sonuc'] = 'RED'
                basarili = godex_yazdir([etiket_data], yazici, mod)
                if basarili:
                    print(f"Red etiketi Godex yaziciya gonderildi: {yazici}")
                else:
                    print("Godex gonderilemedi, PDF aciliyor")
                    self._red_etiket_pdf(etiket_data)
            else:
                self._red_etiket_pdf(etiket_data)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Red etiketi oluşturma hatası: {e}")

    def _red_etiket_pdf(self, etiket_data):
        """PDF olarak red etiketi olustur ve ac"""
        try:
            from utils.etiket_yazdir import red_etiket_pdf_olustur
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='fk_red_')
            temp_path = temp_file.name
            temp_file.close()
            red_etiket_pdf_olustur(temp_path, [etiket_data])
            subprocess.Popen(['start', '', temp_path], shell=True)
        except Exception as e:
            print(f"Red PDF etiket hatasi: {e}")

    # =========================================================================
    # TIMER / OTOMATİK YENİLEME
    # =========================================================================

    def _update_time(self):
        self.saat_label.setText(QTime.currentTime().toString("HH:mm:ss"))

    def _manual_refresh(self):
        """Yenile butonuyla manuel yenileme"""
        if self.personel_data:
            self._load_products()
            self._load_son_islemler()

    def closeEvent(self, event):
        self.saat_timer.stop()
        super().closeEvent(event)
