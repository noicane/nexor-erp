# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Mal Kabul Sayfası
Gelen irsaliye kayıt, ürün kabul ve emanet stok işlemleri
-- Güncellenmiş: Lot yapısı ve stok.stok_bakiye entegrasyonu
"""
import os
from datetime import datetime, date
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QScrollArea, QWidget, QDateEdit, QSpinBox, QDoubleSpinBox,
    QTextEdit, QSplitter, QGroupBox, QGridLayout, QTabWidget,
    QCheckBox
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage, create_action_buttons
from components.dialog_minimize_bar import add_minimize_button
from core.database import get_db_connection
from core.log_manager import LogManager
from config import DEFAULT_PAGE_SIZE

# Etiket yazdırma
import subprocess
import tempfile


# ============================================================================
# LOT NUMARASI YARDIMCI FONKSİYONLARI
# ============================================================================

def lot_no_uret(tarih: datetime, sira: int, palet_no: int = None) -> str:
    """
    Lot numarası oluştur
    
    Format:
        Ana lot: LOT-YYMM-SSSS (örn: LOT-2501-0001)
        Palet lot: LOT-YYMM-SSSS-PP (örn: LOT-2501-0001-01)
    """
    yil_ay = tarih.strftime("%y%m")
    
    if palet_no is None:
        # Ana lot
        return f"LOT-{yil_ay}-{sira:04d}"
    else:
        # Palet lot
        return f"LOT-{yil_ay}-{sira:04d}-{palet_no:02d}"


def get_next_lot_sira(tarih: datetime = None) -> int:
    """Bu ay için sonraki lot sıra numarasını bul"""
    if tarih is None:
        tarih = datetime.now()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        yil_ay = tarih.strftime("%y%m")
        like_pattern = f"LOT-{yil_ay}-%"
        
        # Hem stok_bakiye hem de giris_irsaliye_satirlar'dan kontrol et
        cursor.execute("""
            SELECT MAX(sira) FROM (
                SELECT CAST(
                    CASE 
                        WHEN LEN(lot_no) > 12 THEN SUBSTRING(lot_no, 10, 4)
                        WHEN LEN(lot_no) = 12 THEN SUBSTRING(lot_no, 10, 4)
                        ELSE '0'
                    END AS INT
                ) as sira
                FROM stok.stok_bakiye 
                WHERE parent_lot_no LIKE ?
                
                UNION ALL
                
                SELECT CAST(
                    CASE 
                        WHEN LEN(lot_no) >= 12 THEN SUBSTRING(lot_no, 10, 4)
                        ELSE '0'
                    END AS INT
                ) as sira
                FROM siparis.giris_irsaliye_satirlar 
                WHERE lot_no LIKE ?
            ) t
        """, (like_pattern, like_pattern))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return int(row[0]) + 1
        
        return 1
    except Exception as e:
        print(f"Lot sıra bulma hatası: {e}")
        return 1


# ============================================================================
# PALET BÖLME DIALOG
# ============================================================================

class PaletBolmeDialog(QDialog):
    """Palet bölme ve etiket yazdırma dialogu - Güncellenmiş versiyon"""
    
    def __init__(self, stok_kodu: str, stok_adi: str, musteri: str, kaplama: str,
                 toplam_miktar: float, birim: str, irsaliye_no: str, 
                 irsaliye_satir_id: int, theme: dict, parent=None):
        super().__init__(parent)
        self.stok_kodu = stok_kodu
        self.stok_adi = stok_adi
        self.musteri = musteri
        self.kaplama = kaplama
        self.toplam_miktar = toplam_miktar
        self.birim = birim
        self.irsaliye_no = irsaliye_no
        self.irsaliye_satir_id = irsaliye_satir_id
        self.theme = theme
        self.created_lots = []  # Oluşturulan lot numaraları
        
        self.setWindowTitle("🏷️ Palet Bölme ve Etiket Yazdır")
        self.setMinimumSize(680, 750)
        self.resize(720, 820)

        self._setup_ui()
        add_minimize_button(self)

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QGroupBox {{ 
                color: {self.theme['text']}; font-weight: bold; 
                border: 1px solid {self.theme['border']}; border-radius: 8px; 
                margin-top: 12px; padding-top: 8px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 8px; color: {self.theme['primary']}; }}
            QSpinBox, QLineEdit, QComboBox {{
                background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']};
                border-radius: 6px; padding: 8px; color: {self.theme['text']}; font-size: 14px;
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ===== ÜRÜN BİLGİLERİ =====
        info_group = QGroupBox("📦 Ürün Bilgileri")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(8)
        
        info_layout.addWidget(QLabel("Stok Kodu:"), 0, 0)
        info_layout.addWidget(QLabel(f"<b>{self.stok_kodu}</b>"), 0, 1)
        
        info_layout.addWidget(QLabel("Ürün Adı:"), 1, 0)
        info_layout.addWidget(QLabel(self.stok_adi[:50] if len(self.stok_adi) > 50 else self.stok_adi), 1, 1)
        
        info_layout.addWidget(QLabel("Müşteri:"), 2, 0)
        info_layout.addWidget(QLabel(self.musteri[:40] if len(self.musteri) > 40 else self.musteri), 2, 1)
        
        info_layout.addWidget(QLabel("Kaplama:"), 3, 0)
        info_layout.addWidget(QLabel(self.kaplama or "-"), 3, 1)
        
        info_layout.addWidget(QLabel("Toplam Miktar:"), 4, 0)
        miktar_label = QLabel(f"<b style='color: {self.theme['success']};'>{self.toplam_miktar:,.0f} {self.birim}</b>")
        info_layout.addWidget(miktar_label, 4, 1)
        
        layout.addWidget(info_group)
        
        # ===== PALET BÖLME =====
        bolme_group = QGroupBox("📋 Palet Bölme")
        bolme_layout = QGridLayout(bolme_group)
        bolme_layout.setSpacing(12)
        
        # Hedef Depo seçimi
        bolme_layout.addWidget(QLabel("Hedef Depo:"), 0, 0)
        self.depo_combo = QComboBox()
        self.depo_combo.setMinimumWidth(200)
        bolme_layout.addWidget(self.depo_combo, 0, 1, 1, 3)
        self._load_depolar()
        
        # Palet Kapasitesi (adet/palet)
        bolme_layout.addWidget(QLabel("Palet Kapasitesi:"), 1, 0)
        self.kapasite_spin = QSpinBox()
        self.kapasite_spin.setRange(1, 999999)
        self.kapasite_spin.setValue(600)  # Varsayılan 600 adet/palet
        self.kapasite_spin.setFixedWidth(120)
        self.kapasite_spin.valueChanged.connect(self._hesapla_paletler)
        bolme_layout.addWidget(self.kapasite_spin, 1, 1)
        
        # Otomatik Hesapla butonu
        hesapla_btn = QPushButton("🔄 Hesapla")
        hesapla_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 4px; padding: 6px 12px;")
        hesapla_btn.clicked.connect(self._hesapla_paletler)
        bolme_layout.addWidget(hesapla_btn, 1, 2)
        
        # Hesaplama sonucu
        self.hesap_label = QLabel("")
        self.hesap_label.setStyleSheet(f"color: {self.theme['success']}; font-weight: bold;")
        bolme_layout.addWidget(self.hesap_label, 1, 3)
        
        # Tam Palet Sayısı
        bolme_layout.addWidget(QLabel("Tam Palet:"), 2, 0)
        self.tam_palet_spin = QSpinBox()
        self.tam_palet_spin.setRange(0, 999)
        self.tam_palet_spin.setValue(0)
        self.tam_palet_spin.setFixedWidth(80)
        self.tam_palet_spin.valueChanged.connect(self._update_preview)
        bolme_layout.addWidget(self.tam_palet_spin, 2, 1)
        
        self.tam_palet_info = QLabel("")
        self.tam_palet_info.setStyleSheet(f"color: {self.theme['text']};")
        bolme_layout.addWidget(self.tam_palet_info, 2, 2, 1, 2)
        
        # Bakiye Palet
        bolme_layout.addWidget(QLabel("Bakiye Palet:"), 3, 0)
        self.bakiye_check = QCheckBox("")
        self.bakiye_check.setStyleSheet(f"color: {self.theme['text']};")
        self.bakiye_check.stateChanged.connect(self._update_preview)
        bolme_layout.addWidget(self.bakiye_check, 3, 1)
        
        self.bakiye_miktar_label = QLabel("")
        self.bakiye_miktar_label.setStyleSheet(f"color: {self.theme['warning']}; font-weight: bold;")
        bolme_layout.addWidget(self.bakiye_miktar_label, 3, 2, 1, 2)
        
        # Toplam Özet
        ozet_frame = QFrame()
        ozet_frame.setStyleSheet(f"background: {self.theme['bg_hover']}; border-radius: 6px; padding: 8px;")
        ozet_layout = QHBoxLayout(ozet_frame)
        ozet_layout.setContentsMargins(12, 8, 12, 8)
        
        self.ozet_label = QLabel("")
        self.ozet_label.setStyleSheet(f"color: {self.theme['text']}; font-size: 13px;")
        ozet_layout.addWidget(self.ozet_label)
        
        bolme_layout.addWidget(ozet_frame, 4, 0, 1, 4)
        
        # Lot sıra no
        bolme_layout.addWidget(QLabel("Lot Sıra No:"), 5, 0)
        self.lot_sira_spin = QSpinBox()
        self.lot_sira_spin.setRange(1, 9999)
        self.lot_sira_spin.setValue(get_next_lot_sira())
        self.lot_sira_spin.setFixedWidth(100)
        self.lot_sira_spin.valueChanged.connect(self._update_preview)
        bolme_layout.addWidget(self.lot_sira_spin, 5, 1)
        
        # Lot önizleme
        bolme_layout.addWidget(QLabel("Lot Format:"), 6, 0)
        self.lot_preview = QLabel("")
        self.lot_preview.setStyleSheet(f"font-family: monospace; color: {self.theme['text_muted']}; font-size: 13px;")
        bolme_layout.addWidget(self.lot_preview, 6, 1, 1, 3)
        
        layout.addWidget(bolme_group)
        
        # İlk hesaplamayı yap
        self._hesapla_paletler()
        
        # ===== ETİKET ŞABLONU =====
        etiket_group = QGroupBox("🏷️ Etiket Şablonu")
        etiket_layout = QHBoxLayout(etiket_group)
        
        etiket_layout.addWidget(QLabel("Şablon:"))
        self.sablon_combo = QComboBox()
        self.sablon_combo.setMinimumWidth(250)
        self.sablon_combo.setStyleSheet(f"""
            QComboBox {{ 
                background: {self.theme['bg_input']}; 
                color: {self.theme['text']}; 
                border: 1px solid {self.theme['border']}; 
                border-radius: 6px; 
                padding: 8px; 
            }}
        """)
        self._load_sablonlar()
        etiket_layout.addWidget(self.sablon_combo)
        etiket_layout.addStretch()
        
        layout.addWidget(etiket_group)
        
        # ===== YAZICI SEÇİMİ =====
        yazici_group = QGroupBox("🖨️ Yazıcı Ayarları")
        yazici_layout = QHBoxLayout(yazici_group)
        
        yazici_layout.addWidget(QLabel("Yazıcı:"))
        self.yazici_combo = QComboBox()
        self.yazici_combo.setMinimumWidth(250)
        self.yazici_combo.setStyleSheet(f"""
            QComboBox {{ 
                background: {self.theme['bg_input']}; 
                color: {self.theme['text']}; 
                border: 1px solid {self.theme['border']}; 
                border-radius: 6px; 
                padding: 8px; 
            }}
        """)
        self._load_yazicilar()
        yazici_layout.addWidget(self.yazici_combo)
        
        # Yazdırma modu
        yazici_layout.addWidget(QLabel("Mod:"))
        self.yazici_mod_combo = QComboBox()
        self.yazici_mod_combo.addItem("PDF Yazdır", "PDF")
        self.yazici_mod_combo.addItem("Godex Direkt (ZPL)", "ZPL")
        self.yazici_mod_combo.addItem("Godex Direkt (EZPL)", "EZPL")
        self.yazici_mod_combo.setStyleSheet(self.yazici_combo.styleSheet())
        yazici_layout.addWidget(self.yazici_mod_combo)
        
        # Yenile butonu
        refresh_btn = QPushButton("Yenile")
        refresh_btn.setToolTip("Yazıcıları Yenile")
        refresh_btn.setFixedSize(60, 36)
        refresh_btn.setStyleSheet(f"background: {self.theme['bg_hover']}; color: {self.theme['text']}; border: 1px solid {self.theme['border']}; border-radius: 6px; font-size: 12px;")
        refresh_btn.clicked.connect(self._load_yazicilar)
        yazici_layout.addWidget(refresh_btn)
        
        yazici_layout.addStretch()
        layout.addWidget(yazici_group)
        
        # ===== BUTONLAR =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        preview_btn = QPushButton("👁️ Önizle")
        preview_btn.setCursor(Qt.PointingHandCursor)
        preview_btn.setStyleSheet(f"""
            QPushButton {{ background: {self.theme['bg_input']}; color: {self.theme['text']}; 
                          border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 10px 20px; }}
            QPushButton:hover {{ background: {self.theme['bg_hover']}; }}
        """)
        preview_btn.clicked.connect(self._onizle)
        btn_layout.addWidget(preview_btn)
        
        print_btn = QPushButton("🖨️ Kaydet ve Yazdır")
        print_btn.setCursor(Qt.PointingHandCursor)
        print_btn.setStyleSheet(f"""
            QPushButton {{ background: {self.theme['success']}; color: white; border: none; 
                          border-radius: 6px; padding: 10px 24px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background: #16a34a; }}
        """)
        print_btn.clicked.connect(self._kaydet_ve_yazdir)
        btn_layout.addWidget(print_btn)
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ background: {self.theme['bg_input']}; color: {self.theme['text']}; 
                          border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 10px 20px; }}
        """)
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
    
    def _load_yazicilar(self):
        """Mevcut yazıcıları yükle"""
        self.yazici_combo.clear()
        
        try:
            from utils.etiket_yazdir import get_available_printers, get_godex_printers
            
            all_printers = get_available_printers()
            godex_printers = get_godex_printers()
            
            # Godex yazıcıları öne al
            if godex_printers:
                for p in godex_printers:
                    self.yazici_combo.addItem(f"🏷️ {p}", p)
            
            # Diğer yazıcılar
            for p in all_printers:
                if p not in godex_printers:
                    self.yazici_combo.addItem(p, p)
            
            if self.yazici_combo.count() == 0:
                self.yazici_combo.addItem("Yazıcı bulunamadı", None)
                
        except ImportError:
            self.yazici_combo.addItem("PDF Dosyası Olarak Kaydet", "PDF_ONLY")
        except Exception as e:
            print(f"Yazıcı listesi yüklenemedi: {e}")
            self.yazici_combo.addItem("PDF Dosyası Olarak Kaydet", "PDF_ONLY")
    
    def _load_sablonlar(self):
        """Etiket şablonlarını yükle"""
        self.sablon_combo.clear()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, sablon_kodu, sablon_adi, varsayilan_mi
                FROM tanim.etiket_sablonlari
                WHERE aktif_mi = 1 AND sablon_tipi = 'PALET'
                ORDER BY varsayilan_mi DESC, sablon_adi
            """)
            
            for row in cursor.fetchall():
                varsayilan = " ⭐" if row[3] else ""
                self.sablon_combo.addItem(f"{row[2]}{varsayilan}", row[0])
            
            conn.close()
            
            if self.sablon_combo.count() == 0:
                self.sablon_combo.addItem("Varsayılan Şablon", None)
                
        except Exception as e:
            print(f"Şablon yükleme hatası: {e}")
            self.sablon_combo.addItem("Varsayılan Şablon", None)
    
    def _load_depolar(self):
        """Depoları yükle"""
        self.depo_combo.clear()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, kod, ad
                FROM tanim.depolar
                WHERE aktif_mi = 1 AND silindi_mi = 0
                ORDER BY kod
            """)
            
            kab_index = 0
            idx = 0
            for row in cursor.fetchall():
                self.depo_combo.addItem(f"{row[1]} - {row[2]}", row[0])
                # KAB-01 bulunca index'i kaydet
                if row[1] == 'KAB-01':
                    kab_index = idx
                idx += 1
            
            conn.close()
            
            # Varsayılan olarak KAB-01 seç
            if self.depo_combo.count() > 0:
                self.depo_combo.setCurrentIndex(kab_index)
            else:
                self.depo_combo.addItem("Kabul Alanı", 7)
                
        except Exception as e:
            print(f"Depo yükleme hatası: {e}")
            self.depo_combo.addItem("Kabul Alanı", 7)
    
    def _hesapla_paletler(self):
        """Palet kapasitesine göre tam palet ve bakiye hesapla"""
        kapasite = self.kapasite_spin.value()
        
        if kapasite <= 0:
            return
        
        # Tam palet sayısı
        tam_palet = int(self.toplam_miktar // kapasite)
        
        # Bakiye miktar
        bakiye = self.toplam_miktar % kapasite
        
        # UI güncelle
        self.tam_palet_spin.setValue(tam_palet)
        self.tam_palet_info.setText(f"x {kapasite:,.0f} = {tam_palet * kapasite:,.0f} {self.birim}")
        
        if bakiye > 0:
            self.bakiye_check.setChecked(True)
            self.bakiye_check.setEnabled(True)
            self.bakiye_miktar_label.setText(f"1 palet x {bakiye:,.0f} {self.birim}")
        else:
            self.bakiye_check.setChecked(False)
            self.bakiye_check.setEnabled(False)
            self.bakiye_miktar_label.setText("Bakiye yok")
        
        self.hesap_label.setText(f"✓ {tam_palet} tam" + (f" + 1 bakiye" if bakiye > 0 else ""))
        
        self._update_preview()
    
    def _update_preview(self):
        """Özet ve lot önizlemesini güncelle"""
        kapasite = self.kapasite_spin.value()
        tam_palet = self.tam_palet_spin.value()
        bakiye_var = self.bakiye_check.isChecked()
        bakiye_miktar = self.toplam_miktar - (tam_palet * kapasite)
        
        toplam_palet = tam_palet + (1 if bakiye_var and bakiye_miktar > 0 else 0)
        toplam_adet = (tam_palet * kapasite) + (bakiye_miktar if bakiye_var else 0)
        
        # Özet
        ozet_parts = []
        if tam_palet > 0:
            ozet_parts.append(f"{tam_palet} tam palet x {kapasite:,.0f} = {tam_palet * kapasite:,.0f}")
        if bakiye_var and bakiye_miktar > 0:
            ozet_parts.append(f"1 bakiye palet x {bakiye_miktar:,.0f} = {bakiye_miktar:,.0f}")
        
        self.ozet_label.setText(
            f"📦 Toplam: {toplam_palet} palet, {toplam_adet:,.0f} {self.birim}\n" +
            " + ".join(ozet_parts)
        )
        
        # Lot önizleme
        tarih = datetime.now()
        sira = self.lot_sira_spin.value()
        ana_lot = lot_no_uret(tarih, sira)
        
        if toplam_palet == 1:
            palet_lot = lot_no_uret(tarih, sira, 1)
            self.lot_preview.setText(f"Ana: {ana_lot}\nPalet: {palet_lot}")
        elif toplam_palet > 1:
            palet_lot_1 = lot_no_uret(tarih, sira, 1)
            palet_lot_n = lot_no_uret(tarih, sira, toplam_palet)
            self.lot_preview.setText(f"Ana: {ana_lot}\nPaletler: {palet_lot_1} ... {palet_lot_n}")
        else:
            self.lot_preview.setText("Palet yok")
    
    def _etiketleri_olustur(self) -> list:
        """Etiket verilerini oluştur - tam paletler + bakiye"""
        from utils.etiket_yazdir import urun_resmi_bul
        
        kapasite = self.kapasite_spin.value()
        tam_palet = self.tam_palet_spin.value()
        bakiye_var = self.bakiye_check.isChecked()
        bakiye_miktar = self.toplam_miktar - (tam_palet * kapasite)
        
        toplam_palet = tam_palet + (1 if bakiye_var and bakiye_miktar > 0 else 0)
        
        lot_sira = self.lot_sira_spin.value()
        tarih = datetime.now()
        ana_lot = lot_no_uret(tarih, lot_sira)
        
        resim_path = urun_resmi_bul(self.stok_kodu)
        
        # Seçili şablon bilgisi
        sablon_id = self.sablon_combo.currentData()
        sablon_adi = self.sablon_combo.currentText()
        
        etiketler = []
        palet_no = 0
        
        # Tam paletler
        for i in range(tam_palet):
            palet_no += 1
            palet_lot = lot_no_uret(tarih, lot_sira, palet_no)
            
            etiketler.append({
                'stok_kodu': self.stok_kodu,
                'stok_adi': self.stok_adi,
                'musteri': self.musteri,
                'kaplama': self.kaplama,
                'miktar': kapasite,
                'birim': self.birim,
                'palet_no': palet_no,
                'toplam_palet': toplam_palet,
                'lot_no': palet_lot,
                'parent_lot_no': ana_lot,
                'irsaliye_no': self.irsaliye_no,
                'tarih': tarih,
                'resim_path': resim_path,
                'sablon_id': sablon_id,
                'sablon_adi': sablon_adi
            })
        
        # Bakiye palet (varsa)
        if bakiye_var and bakiye_miktar > 0:
            palet_no += 1
            palet_lot = lot_no_uret(tarih, lot_sira, palet_no)
            
            etiketler.append({
                'stok_kodu': self.stok_kodu,
                'stok_adi': self.stok_adi,
                'musteri': self.musteri,
                'kaplama': self.kaplama,
                'miktar': bakiye_miktar,
                'birim': self.birim,
                'palet_no': palet_no,
                'toplam_palet': toplam_palet,
                'lot_no': palet_lot,
                'parent_lot_no': ana_lot,
                'irsaliye_no': self.irsaliye_no,
                'tarih': tarih,
                'resim_path': resim_path,
                'sablon_id': sablon_id,
                'sablon_adi': sablon_adi
            })
        
        return etiketler
    
    def _onizle(self):
        """PDF önizleme - seçili şablona göre"""
        try:
            from utils.etiket_yazdir import a4_etiket_pdf_olustur
            
            etiketler = self._etiketleri_olustur()
            
            if not etiketler:
                QMessageBox.warning(self, "Uyarı", "Önce palet bölme ayarlarını yapın!")
                return
            
            # Geçici dosya
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='etiket_onizle_')
            temp_path = temp_file.name
            temp_file.close()
            
            # Şablon ID kontrolü
            sablon_id = self.sablon_combo.currentData()
            
            if sablon_id:
                # Veritabanından şablon bilgilerini al ve PDF oluştur
                try:
                    from utils.etiket_yazdir import sablon_ile_etiket_pdf_olustur
                    sablon_ile_etiket_pdf_olustur(temp_path, etiketler, sablon_id)
                except (ImportError, AttributeError) as e:
                    print(f"Şablon fonksiyonu bulunamadı, varsayılana dönülüyor: {e}")
                    a4_etiket_pdf_olustur(temp_path, etiketler)
                except Exception as e:
                    print(f"Şablon ile PDF oluşturma hatası, varsayılana dönülüyor: {e}")
                    a4_etiket_pdf_olustur(temp_path, etiketler)
            else:
                # Varsayılan şablon
                a4_etiket_pdf_olustur(temp_path, etiketler)
            
            # PDF'i aç
            subprocess.Popen(['start', '', temp_path], shell=True)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Önizleme hatası:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _kaydet_ve_yazdir(self):
        """Lotları veritabanına kaydet ve etiket yazdır - Hareket Motoru ile"""
        try:
            # Mükerrer lot kontrolü - Bu satır için zaten lot ve stok girişi var mı?
            if self.irsaliye_satir_id:
                try:
                    conn_chk = get_db_connection()
                    cursor_chk = conn_chk.cursor()
                    cursor_chk.execute("""
                        SELECT lot_no FROM siparis.giris_irsaliye_satirlar
                        WHERE id = ? AND lot_no IS NOT NULL AND lot_no != ''
                    """, (self.irsaliye_satir_id,))
                    mevcut = cursor_chk.fetchone()
                    conn_chk.close()
                    if mevcut:
                        reply = QMessageBox.question(
                            self, "Lot Mevcut",
                            f"Bu satır için zaten lot oluşturulmuş!\n\n"
                            f"Mevcut Lot: {mevcut[0]}\n\n"
                            f"Tekrar yazdırmak mükerrer stok girişine neden olacaktır.\n"
                            f"Devam etmek istediğinize emin misiniz?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply != QMessageBox.Yes:
                            return
                except Exception as e:
                    print(f"Mükerrer kontrol hatası: {e}")

            etiketler = self._etiketleri_olustur()

            if not etiketler:
                QMessageBox.warning(self, "Uyarı", "Etiket oluşturulamadı!")
                return

            conn = get_db_connection()
            cursor = conn.cursor()
            
            # ===== HAREKET MOTORU BAŞLAT =====
            from core.hareket_motoru import HareketMotoru
            motor = HareketMotoru(conn)
            
            ana_lot = etiketler[0]['parent_lot_no']
            depo_id = self.depo_combo.currentData()
            sablon_id = self.sablon_combo.currentData()
            
            # Depo seçilmemişse akış şablonundan veya varsayılan KAB-01 kullan
            if not depo_id:
                print("UYARI: Depo seçilmedi, varsayılan kullanılıyor")
                depo_id = 7  # KAB-01
            
            print(f"DEBUG: Seçilen depo_id = {depo_id}, sablon_id = {sablon_id}")
            tarih = datetime.now()
            
            # urun_id bul veya oluştur
            cursor.execute("""
                SELECT id FROM stok.urunler WHERE urun_kodu = ? AND aktif_mi = 1
            """, (self.stok_kodu,))
            urun_row = cursor.fetchone()
            
            if not urun_row:
                # Ürün yoksa ekle
                cursor.execute("""
                    INSERT INTO stok.urunler (uuid, urun_kodu, urun_adi, urun_tipi, birim_id, aktif_mi, 
                                             olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                    OUTPUT INSERTED.id
                    VALUES (NEWID(), ?, ?, 'MAMUL', 1, 1, GETDATE(), GETDATE(), 0)
                """, (self.stok_kodu, self.stok_adi))
                urun_id = cursor.fetchone()[0]
                print(f"Yeni ürün oluşturuldu: {self.stok_kodu}, ID: {urun_id}")
            else:
                urun_id = urun_row[0]
            
            # ===== HAREKET MOTORU İLE STOK GİRİŞİ =====
            self.created_lots = []
            for etiket in etiketler:
                palet_lot = etiket['lot_no']
                miktar = etiket['miktar']
                palet_no = etiket['palet_no']
                toplam_palet = etiket['toplam_palet']
                
                # Hareket motoru ile stok girişi
                sonuc = motor.stok_giris(
                    urun_id=urun_id,
                    miktar=miktar,
                    lot_no=palet_lot,
                    depo_id=depo_id,
                    parent_lot_no=ana_lot,
                    palet_no=palet_no,
                    toplam_palet=toplam_palet,
                    urun_kodu=self.stok_kodu,  # DÜZELTME: stok_kodu -> urun_kodu
                    urun_adi=self.stok_adi,     # DÜZELTME: stok_adi -> urun_adi
                    cari_unvani=self.musteri,
                    kaplama_tipi=self.kaplama,
                    birim=self.birim,
                    irsaliye_satir_id=self.irsaliye_satir_id,
                    kalite_durumu='BEKLIYOR',
                    durum_kodu='KABUL',  # YENİ: Durum sistemi
                    aciklama=f"İrsaliye girişi - {self.irsaliye_no}"
                )
                
                if not sonuc.basarili:
                    raise Exception(f"Stok girişi hatası: {sonuc.hata or sonuc.mesaj}")
                
                self.created_lots.append(palet_lot)
                print(f"✓ Lot oluşturuldu: {palet_lot}, Bakiye ID: {sonuc.bakiye_id}, Hareket ID: {sonuc.hareket_id}")
            
            # İrsaliye satırına ana lot numarasını kaydet
            cursor.execute("""
                UPDATE siparis.giris_irsaliye_satirlar 
                SET lot_no = ?, kalite_durumu = 'BEKLIYOR'
                WHERE id = ?
            """, (ana_lot, self.irsaliye_satir_id))
            
            # ===== ETİKET YAZDIRMA =====
            
            # Yazıcı ve mod bilgilerini al
            yazici_name = self.yazici_combo.currentData()
            yazici_mod = self.yazici_mod_combo.currentData()
            
            # PDF oluştur
            from utils.etiket_yazdir import a4_etiket_pdf_olustur
            
            output_dir = os.path.join(os.path.expanduser("~"), "Documents", "AtmoERP", "Etiketler")
            os.makedirs(output_dir, exist_ok=True)
            
            tarih_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_stok_kodu = self.stok_kodu.replace("/", "_").replace("\\", "_")
            filename = f"Etiket_{safe_stok_kodu}_{tarih_str}.pdf"
            output_path = os.path.join(output_dir, filename)
            
            # Şablon ID'ye göre PDF oluştur
            if sablon_id:
                try:
                    from utils.etiket_yazdir import sablon_ile_etiket_pdf_olustur
                    sablon_ile_etiket_pdf_olustur(output_path, etiketler, sablon_id)
                except (ImportError, AttributeError) as e:
                    print(f"Şablon fonksiyonu bulunamadı, varsayılana dönülüyor: {e}")
                    a4_etiket_pdf_olustur(output_path, etiketler)
                except Exception as e:
                    print(f"Şablon ile PDF oluşturma hatası, varsayılana dönülüyor: {e}")
                    a4_etiket_pdf_olustur(output_path, etiketler)
            else:
                a4_etiket_pdf_olustur(output_path, etiketler)
            
            # ✅✅✅ OBSERVER - EVENT KAYDI ✅✅✅
            try:
                from utils.hareket_observer import HareketObserver
                observer = HareketObserver(conn)
                # Her palet için event kaydı
                for etiket in etiketler:
                    observer.on_hareket_completed(
                        lot_no=etiket['lot_no'],
                        depo_id=depo_id,
                        miktar=etiket['miktar']
                    )
            except Exception as e:
                print(f"⚠️ Observer hatası (önemsiz): {e}")
            # ✅✅✅ OBSERVER BİTTİ ✅✅✅
            
            conn.commit()  # Tüm işlemler başarılıysa commit
            conn.close()
            
            # Yazdırma işlemi
            yazdir_basarili = False
            yazici_mesaj = ""
            
            if yazici_mod in ("ZPL", "EZPL") and yazici_name and yazici_name != "PDF_ONLY":
                # Godex direkt yazdırma
                try:
                    from utils.etiket_yazdir import godex_yazdir
                    yazdir_basarili = godex_yazdir(etiketler, yazici_name, yazici_mod)
                    if yazdir_basarili:
                        yazici_mesaj = f"🖨️ Yazıcı: {yazici_name} ({yazici_mod})"
                    else:
                        yazici_mesaj = "⚠️ Yazıcıya gönderilemedi, PDF açılıyor"
                        subprocess.Popen(['start', '', output_path], shell=True)
                except ImportError:
                    yazici_mesaj = "⚠️ win32print modülü yok, PDF açılıyor"
                    subprocess.Popen(['start', '', output_path], shell=True)
                except Exception as e:
                    print(f"Godex yazdırma hatası: {e}")
                    yazici_mesaj = f"⚠️ Yazdırma hatası: {str(e)[:30]}"
                    subprocess.Popen(['start', '', output_path], shell=True)
            
            elif yazici_mod == "PDF" and yazici_name and yazici_name != "PDF_ONLY":
                # PDF'i seçili yazıcıya gönder
                try:
                    from utils.etiket_yazdir import pdf_yazdir
                    yazdir_basarili = pdf_yazdir(output_path, yazici_name)
                    if yazdir_basarili:
                        yazici_mesaj = f"🖨️ PDF yazıcıya gönderildi: {yazici_name}"
                    else:
                        yazici_mesaj = "⚠️ PDF gönderilemedi, dosya açılıyor"
                        subprocess.Popen(['start', '', output_path], shell=True)
                except Exception as e:
                    print(f"PDF yazdırma hatası: {e}")
                    subprocess.Popen(['start', '', output_path], shell=True)
                    yazici_mesaj = "📄 PDF dosyası açıldı"
            else:
                # Sadece PDF aç
                subprocess.Popen(['start', '', output_path], shell=True)
                yazici_mesaj = "📄 PDF dosyası açıldı"
            
            sablon_text = self.sablon_combo.currentText()
            QMessageBox.information(self, "Başarılı", 
                f"✅ Lotlar oluşturuldu ve kaydedildi!\n\n"
                f"📦 Ana Lot: {ana_lot}\n"
                f"📋 Palet Sayısı: {len(etiketler)}\n"
                f"🏷️ Şablon: {sablon_text}\n"
                f"📁 PDF: {output_path}\n"
                f"{yazici_mesaj}\n\n"
                f"✓ Stok hareketleri kaydedildi\n"
                f"⏳ Lotlar kalite onayı bekliyor.")
            
            self.accept()  # Dialog'u kapat ve başarılı döndür
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası:\n{str(e)}")
            import traceback
            traceback.print_exc()




# ============================================================================
# ÜRÜN ARAMA DIALOG
# ============================================================================

class UrunAramaDialog(QDialog):
    """Ürün arama ve seçme dialogu"""
    
    def __init__(self, cari_unvani: str, theme: dict, parent=None):
        super().__init__(parent)
        self.cari_unvani = cari_unvani
        self.theme = theme
        self.selected_urun = None
        
        self.setWindowTitle("🔍 Ürün Ara")
        self.setMinimumSize(700, 500)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QLineEdit {{
                background: {self.theme['bg_input']};
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                padding: 10px;
                color: {self.theme['text']};
                font-size: 14px;
            }}
            QTableWidget {{
                background: {self.theme['bg_card']};
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
                gridline-color: {self.theme['border']};
                color: {self.theme['text']};
            }}
            QTableWidget::item {{ padding: 8px; }}
            QTableWidget::item:selected {{ background: {self.theme['primary']}; }}
            QHeaderView::section {{
                background: {self.theme['bg_hover']};
                color: {self.theme['text']};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Başlık
        title = QLabel(f"🔍 Ürün Ara - {self.cari_unvani}")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        # Arama kutusu
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Stok kodu veya ürün adı ile ara...")
        self.search_input.textChanged.connect(self._filter_data)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Stok Kodu", "Ürün Adı", "Kaplama", "Birim"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 80)
        self.table.doubleClicked.connect(self._select_and_close)
        layout.addWidget(self.table, 1)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"background: {self.theme['bg_input']}; color: {self.theme['text']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 10px 20px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        select_btn = QPushButton("✓ Seç")
        select_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold;")
        select_btn.clicked.connect(self._select_and_close)
        btn_layout.addWidget(select_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        """Ürünleri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.urun_kodu, u.urun_adi, kt.ad as kaplama, b.ad as birim
                FROM stok.urunler u
                INNER JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                WHERE c.unvan = ? AND u.aktif_mi = 1
                ORDER BY u.urun_kodu
            """, (self.cari_unvani,))
            
            self.all_data = cursor.fetchall()
            conn.close()
            
            self._display_data(self.all_data)
            
        except Exception as e:
            print(f"Ürün yükleme hatası: {e}")
    
    def _display_data(self, data):
        """Verileri tabloda göster"""
        self.table.setRowCount(len(data))
        for i, row in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(row[0] or ""))
            self.table.setItem(i, 1, QTableWidgetItem(row[1] or ""))
            self.table.setItem(i, 2, QTableWidgetItem(row[2] or "-"))
            self.table.setItem(i, 3, QTableWidgetItem(row[3] or "ADET"))
    
    def _filter_data(self):
        """Arama filtreleme"""
        search = self.search_input.text().strip().lower()
        if not search:
            self._display_data(self.all_data)
            return
        
        filtered = [row for row in self.all_data 
                   if search in (row[0] or "").lower() or search in (row[1] or "").lower()]
        self._display_data(filtered)
    
    def _select_and_close(self):
        """Seçili ürünü al ve kapat"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir ürün seçin!")
            return
        
        self.selected_urun = {
            'stok_kodu': self.table.item(row, 0).text(),
            'stok_adi': self.table.item(row, 1).text(),
            'kaplama': self.table.item(row, 2).text() if self.table.item(row, 2).text() != "-" else "",
            'birim': self.table.item(row, 3).text()
        }
        self.accept()


# ============================================================================
# İRSALİYE DETAY DIALOG
# ============================================================================

class IrsaliyeDetayDialog(QDialog):
    """Giriş İrsaliyesi Detay/Düzenleme Dialog"""
    
    def __init__(self, irsaliye_id: int, theme: dict, parent=None, yeni_kayit=False):
        super().__init__(parent)
        self.irsaliye_id = irsaliye_id
        self.theme = theme
        self.yeni_kayit = yeni_kayit
        self.irsaliye_data = {}
        self.satirlar = []
        self.combo_data = {}
        
        self.setWindowTitle("Yeni Giriş İrsaliyesi" if yeni_kayit else "İrsaliye Detay")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 750)
        
        self._load_combo_data()
        if not yeni_kayit:
            self._load_data()
        self._setup_ui()
        add_minimize_button(self)

    def _load_combo_data(self):
        """Combo box verilerini yükle"""
        self.combo_data = {
            'cariler': [(None, '-- Müşteri Seçin --')],
            'birimler': [(None, '--'), ('ADET', 'ADET'), ('KG', 'KG'), ('M2', 'M²')],
            'kaplamalar': [(None, '--')],
            'personeller': [(None, '-- Teslim Alan --')],
            'soforler': [(None, '-- Şoför Seçin --')],
            'araclar': [(None, '-- Araç Seçin --')]
        }
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Müşteriler - Cari tablosundan
            cursor.execute("SELECT DISTINCT c.unvan FROM stok.urunler u INNER JOIN musteri.cariler c ON u.cari_id = c.id WHERE c.unvan IS NOT NULL AND c.unvan <> '' AND c.aktif_mi = 1 AND u.aktif_mi = 1 ORDER BY c.unvan")
            rows = cursor.fetchall()
            if rows:
                self.combo_data['cariler'] = [(None, '-- Müşteri Seçin --')] + [(r[0], r[0]) for r in rows]
            
            # Kaplama türleri - Kaplama türleri tablosundan
            cursor.execute("SELECT DISTINCT kt.id, kt.ad FROM stok.urunler u INNER JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id WHERE kt.id IS NOT NULL AND kt.ad IS NOT NULL AND u.aktif_mi = 1 ORDER BY kt.ad")
            rows = cursor.fetchall()
            if rows:
                self.combo_data['kaplamalar'] = [(None, '--')] + [(r[0], r[1]) for r in rows]
            
            # Personeller - ik.personeller tablosundan
            cursor.execute("""
                SELECT id, ad + ' ' + soyad as ad_soyad 
                FROM ik.personeller 
                WHERE aktif_mi = 1 
                ORDER BY ad, soyad
            """)
            rows = cursor.fetchall()
            if rows:
                self.combo_data['personeller'] = [(None, '-- Teslim Alan --')] + [(r[0], r[1]) for r in rows]
            
            # Şoförler - lojistik.soforler tablosundan
            try:
                cursor.execute("""
                    SELECT id, ad_soyad, tc_kimlik_no
                    FROM lojistik.soforler 
                    WHERE aktif_mi = 1 
                    ORDER BY ad_soyad
                """)
                rows = cursor.fetchall()
                if rows:
                    self.combo_data['soforler'] = [(None, '-- Şoför Seçin --')] + [(r[0], f"{r[1]} ({r[2][-4:]})") for r in rows]
            except Exception:
                pass  # Tablo yoksa geç
            
            # Araçlar - lojistik.araclar tablosundan
            try:
                cursor.execute("""
                    SELECT id, plaka, arac_tipi
                    FROM lojistik.araclar 
                    WHERE aktif_mi = 1 
                    ORDER BY plaka
                """)
                rows = cursor.fetchall()
                if rows:
                    self.combo_data['araclar'] = [(None, '-- Araç Seçin --')] + [(r[0], f"{r[1]} ({r[2] or ''})") for r in rows]
            except Exception:
                pass  # Tablo yoksa geç
            
            conn.close()
        except Exception as e:
            print(f"Combo yükleme hatası: {e}")
    
    def _load_data(self):
        """İrsaliye verilerini yükle"""
        if not self.irsaliye_id:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Ana irsaliye
            cursor.execute("""
                SELECT id, irsaliye_no, cari_unvani, cari_irsaliye_no, tarih, 
                       teslim_alan, arac_plaka, sofor_adi, durum, notlar
                FROM siparis.giris_irsaliyeleri
                WHERE id = ?
            """, (self.irsaliye_id,))
            row = cursor.fetchone()
            if row:
                self.irsaliye_data = {
                    'id': row[0],
                    'irsaliye_no': row[1],
                    'cari_unvani': row[2],
                    'cari_irsaliye_no': row[3],
                    'tarih': row[4],
                    'teslim_alan': row[5],
                    'arac_plaka': row[6],
                    'sofor_adi': row[7],
                    'durum': row[8],
                    'notlar': row[9]
                }
            
            # Satırlar
            cursor.execute("""
                SELECT id, satir_no, stok_kodu, stok_adi, miktar, birim, kaplama, lot_no, termin_tarihi, kalite_durumu
                FROM siparis.giris_irsaliye_satirlar
                WHERE irsaliye_id = ?
                ORDER BY satir_no
            """, (self.irsaliye_id,))
            
            self.satirlar = []
            for row in cursor.fetchall():
                self.satirlar.append({
                    'id': row[0],
                    'satir_no': row[1],
                    'stok_kodu': row[2],
                    'stok_adi': row[3],
                    'miktar': row[4],
                    'birim': row[5],
                    'kaplama': row[6],
                    'lot_no': row[7],
                    'termin_tarihi': row[8],
                    'kalite_durumu': row[9]
                })
            
            conn.close()
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {self.theme['bg_main']}; }}
            QLabel {{ color: {self.theme['text']}; }}
            QGroupBox {{ 
                color: {self.theme['text']}; 
                font-weight: bold; 
                border: 1px solid {self.theme['border']}; 
                border-radius: 8px; 
                margin-top: 12px; 
                padding-top: 8px;
            }}
            QGroupBox::title {{ 
                subcontrol-origin: margin; 
                left: 12px; 
                padding: 0 8px;
                color: {self.theme['primary']};
            }}
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {{
                background: {self.theme['bg_input']};
                border: 1px solid {self.theme['border']};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme['text']};
            }}
            QTableWidget {{
                background: {self.theme['bg_card']};
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
                gridline-color: {self.theme['border']};
            }}
            QTableWidget::item {{ padding: 6px; }}
            QHeaderView::section {{
                background: {self.theme['bg_hover']};
                color: {self.theme['text']};
                padding: 8px;
                border: none;
                border-right: 1px solid {self.theme['border']};
                font-weight: bold;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Content
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(16, 16, 16, 16)
        c_layout.setSpacing(16)
        
        # Üst kısım - İrsaliye bilgileri
        info_group = self._create_info_group()
        c_layout.addWidget(info_group)
        
        # Alt kısım - Satırlar
        satirlar_group = self._create_satirlar_group()
        c_layout.addWidget(satirlar_group, 1)
        
        layout.addWidget(content, 1)
        
        # Tüm widget'lar oluşturulduktan sonra signal bağlantılarını yap
        self.cari_combo.currentIndexChanged.connect(self._on_cari_changed)
        
        # Mevcut müşteri seçiliyse ürünleri yükle
        if not self.yeni_kayit and self.cari_combo.currentData():
            self._on_cari_changed()
    
    def _create_header(self) -> QFrame:
        """Başlık ve durum"""
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.theme['bg_card']}; padding: 16px; }}")
        
        layout = QHBoxLayout(frame)
        
        title = QLabel("📥 " + ("Yeni Giriş İrsaliyesi" if self.yeni_kayit else f"İrsaliye: {self.irsaliye_data.get('irsaliye_no', '')}"))
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        layout.addStretch()
        
        if not self.yeni_kayit:
            durum = self.irsaliye_data.get('durum', 'TASLAK')
            colors = {'TASLAK': '#f59e0b', 'ONAYLANDI': '#22c55e', 'IPTAL': '#ef4444'}
            badge = QLabel(f"  {durum}  ")
            badge.setStyleSheet(f"background: {colors.get(durum, '#888')}; color: white; padding: 6px 16px; border-radius: 12px; font-weight: bold;")
            layout.addWidget(badge)
        
        return frame
    
    def _create_info_group(self) -> QGroupBox:
        """İrsaliye bilgileri"""
        group = QGroupBox("İrsaliye Bilgileri")
        layout = QGridLayout(group)
        layout.setSpacing(12)
        
        # İrsaliye No
        layout.addWidget(QLabel("İrsaliye No:"), 0, 0)
        self.irsaliye_no_input = QLineEdit()
        self.irsaliye_no_input.setPlaceholderText("Otomatik")
        self.irsaliye_no_input.setReadOnly(True)
        if not self.yeni_kayit:
            self.irsaliye_no_input.setText(self.irsaliye_data.get('irsaliye_no', ''))
        layout.addWidget(self.irsaliye_no_input, 0, 1)
        
        # Tarih
        layout.addWidget(QLabel("Tarih:"), 0, 2)
        self.tarih_input = QDateEdit()
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDisplayFormat("dd.MM.yyyy")
        if not self.yeni_kayit and self.irsaliye_data.get('tarih'):
            self.tarih_input.setDate(QDate(self.irsaliye_data['tarih'].year, self.irsaliye_data['tarih'].month, self.irsaliye_data['tarih'].day))
        else:
            self.tarih_input.setDate(QDate.currentDate())
        layout.addWidget(self.tarih_input, 0, 3)
        
        # Müşteri
        layout.addWidget(QLabel("Müşteri:"), 1, 0)
        self.cari_combo = QComboBox()
        for val, text in self.combo_data['cariler']:
            self.cari_combo.addItem(text, val)
        # NOT: Signal bağlantısını burada YAPMA - _setup_ui sonunda yapılacak
        if not self.yeni_kayit:
            idx = self.cari_combo.findData(self.irsaliye_data.get('cari_unvani'))
            if idx >= 0:
                self.cari_combo.setCurrentIndex(idx)
        layout.addWidget(self.cari_combo, 1, 1, 1, 3)
        
        # Müşteri İrsaliye No
        layout.addWidget(QLabel("Müşteri İrs. No:"), 2, 0)
        self.cari_irsaliye_input = QLineEdit()
        self.cari_irsaliye_input.setPlaceholderText("Müşterinin irsaliye numarası")
        if not self.yeni_kayit:
            self.cari_irsaliye_input.setText(self.irsaliye_data.get('cari_irsaliye_no', '') or '')
        layout.addWidget(self.cari_irsaliye_input, 2, 1)
        
        # Teslim Alan
        layout.addWidget(QLabel("Teslim Alan:"), 2, 2)
        self.teslim_alan_combo = QComboBox()
        self.teslim_alan_combo.setEditable(True)
        # Personelleri combo'ya ekle
        for pid, pname in self.combo_data.get('personeller', [(None, '-- Teslim Alan --')]):
            self.teslim_alan_combo.addItem(pname, pid)
        if not self.yeni_kayit and self.irsaliye_data.get('teslim_alan'):
            self.teslim_alan_combo.setCurrentText(self.irsaliye_data['teslim_alan'])
        layout.addWidget(self.teslim_alan_combo, 2, 3)
        
        # Araç Plaka - Combo
        layout.addWidget(QLabel("Araç Plaka:"), 3, 0)
        self.plaka_combo = QComboBox()
        self.plaka_combo.setEditable(True)  # Manuel giriş de yapılabilsin
        for aid, atext in self.combo_data.get('araclar', [(None, '-- Araç Seçin --')]):
            self.plaka_combo.addItem(atext, aid)
        if not self.yeni_kayit and self.irsaliye_data.get('arac_plaka'):
            self.plaka_combo.setCurrentText(self.irsaliye_data['arac_plaka'])
        layout.addWidget(self.plaka_combo, 3, 1)
        
        # Şoför - Combo
        layout.addWidget(QLabel("Şoför:"), 3, 2)
        self.sofor_combo = QComboBox()
        self.sofor_combo.setEditable(True)  # Manuel giriş de yapılabilsin
        for sid, stext in self.combo_data.get('soforler', [(None, '-- Şoför Seçin --')]):
            self.sofor_combo.addItem(stext, sid)
        if not self.yeni_kayit and self.irsaliye_data.get('sofor_adi'):
            self.sofor_combo.setCurrentText(self.irsaliye_data['sofor_adi'])
        layout.addWidget(self.sofor_combo, 3, 3)
        
        # Notlar
        layout.addWidget(QLabel("Notlar:"), 4, 0)
        self.notlar_input = QLineEdit()
        if not self.yeni_kayit:
            self.notlar_input.setText(self.irsaliye_data.get('notlar', '') or '')
        layout.addWidget(self.notlar_input, 4, 1, 1, 3)
        
        return group
    
    def _create_satirlar_group(self) -> QGroupBox:
        """Satırlar tablosu"""
        group = QGroupBox("İrsaliye Satırları")
        layout = QVBoxLayout(group)
        
        # Araç çubuğu
        toolbar = QHBoxLayout()
        
        # Ürün seçimi
        toolbar.addWidget(QLabel("Ürün:"))
        self.urun_combo = QComboBox()
        self.urun_combo.setMinimumWidth(300)
        self.urun_combo.setEditable(True)  # Arama yapılabilsin
        self.urun_combo.setInsertPolicy(QComboBox.NoInsert)
        self.urun_combo.addItem("-- Önce müşteri seçin --", None)
        toolbar.addWidget(self.urun_combo)
        
        # Ürün Arama butonu
        search_urun_btn = QPushButton("Ara")
        search_urun_btn.setFixedSize(50, 36)
        search_urun_btn.setToolTip("Ürün Ara")
        search_urun_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; font-size: 12px;")
        search_urun_btn.clicked.connect(self._search_urun)
        toolbar.addWidget(search_urun_btn)
        
        # Miktar
        toolbar.addWidget(QLabel("Miktar:"))
        self.miktar_input = QDoubleSpinBox()
        self.miktar_input.setRange(0, 9999999)
        self.miktar_input.setDecimals(0)
        self.miktar_input.setValue(0)
        toolbar.addWidget(self.miktar_input)
        
        # Ekle butonu
        add_btn = QPushButton("➕ Satır Ekle")
        add_btn.setStyleSheet(f"background: {self.theme['success']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        add_btn.clicked.connect(self._add_satir)
        toolbar.addWidget(add_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Tablo
        self.satirlar_table = QTableWidget()
        self.satirlar_table.setColumnCount(10)
        self.satirlar_table.setHorizontalHeaderLabels([
            "ID", "Stok Kodu", "Stok Adı", "Miktar", "Birim", "Kaplama", "Lot No", "Termin", "Kalite", "İşlem"
        ])
        self.satirlar_table.setColumnHidden(0, True)
        self.satirlar_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.satirlar_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.satirlar_table.verticalHeader().setVisible(False)
        
        # İşlem sütunu genişliği - butonların sığması için
        self.satirlar_table.setColumnWidth(9, 170)
        
        # Varsayılan satır yüksekliği
        self.satirlar_table.verticalHeader().setDefaultSectionSize(40)
        
        # Mevcut satırları yükle
        if not self.yeni_kayit:
            self._load_satirlar()
        
        layout.addWidget(self.satirlar_table)
        
        # Alt butonlar
        bottom = QHBoxLayout()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(f"background: {self.theme['primary']}; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold;")
        save_btn.clicked.connect(self._save)
        bottom.addWidget(save_btn)
        
        if not self.yeni_kayit:
            approve_btn = QPushButton("✅ Onayla")
            approve_btn.setStyleSheet(f"background: {self.theme['success']}; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold;")
            approve_btn.clicked.connect(self._approve)
            bottom.addWidget(approve_btn)
        
        bottom.addStretch()
        
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(f"background: {self.theme['bg_input']}; color: {self.theme['text']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 10px 20px;")
        close_btn.clicked.connect(self.close)
        bottom.addWidget(close_btn)
        
        layout.addLayout(bottom)
        
        return group
    
    def _on_cari_changed(self):
        """Müşteri değiştiğinde ürünleri yükle"""
        cari_unvani = self.cari_combo.currentData()
        self.urun_combo.clear()
        
        if not cari_unvani:
            self.urun_combo.addItem("-- Önce müşteri seçin --", None)
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.urun_kodu, u.urun_adi, kt.ad as kaplama_tip_adi, b.ad as birim1, u.yuzey_alani_m2 as m2, u.agirlik_kg as agirlik
                FROM stok.urunler u
                INNER JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                WHERE c.unvan = ? AND u.aktif_mi = 1
                ORDER BY u.urun_kodu
            """, (cari_unvani,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                self.urun_combo.addItem("-- Ürün Seçin --", None)
                for row in rows:
                    stok_kodu = row[0] or ''
                    stok_adi = row[1] or ''
                    kaplama = row[2] or ''
                    birim = row[3] or 'ADET'
                    
                    display_text = f"{stok_kodu} - {stok_adi}"
                    if kaplama:
                        display_text += f" [{kaplama}]"
                    
                    urun_data = {
                        'stok_kodu': stok_kodu,
                        'stok_adi': stok_adi,
                        'kaplama': kaplama,
                        'birim': birim,
                        'm2': row[4],
                        'agirlik': row[5]
                    }
                    self.urun_combo.addItem(display_text, urun_data)
            else:
                self.urun_combo.addItem("-- Bu müşteriye ait ürün yok --", None)
                
        except Exception as e:
            print(f"Stok yükleme hatası: {e}")
            self.urun_combo.addItem("-- Yükleme hatası --", None)
    
    def _load_satirlar(self):
        """Satırları tabloya yükle"""
        self.satirlar_table.setRowCount(len(self.satirlar))
        
        for i, satir in enumerate(self.satirlar):
            self.satirlar_table.setItem(i, 0, QTableWidgetItem(str(satir.get('id', ''))))
            self.satirlar_table.setItem(i, 1, QTableWidgetItem(satir.get('stok_kodu', '')))
            self.satirlar_table.setItem(i, 2, QTableWidgetItem(satir.get('stok_adi', '')))
            self.satirlar_table.setItem(i, 3, QTableWidgetItem(f"{satir.get('miktar', 0):,.0f}"))
            self.satirlar_table.setItem(i, 4, QTableWidgetItem(satir.get('birim', 'ADET')))
            self.satirlar_table.setItem(i, 5, QTableWidgetItem(satir.get('kaplama', '') or ''))
            self.satirlar_table.setItem(i, 6, QTableWidgetItem(satir.get('lot_no', '') or ''))
            
            termin = satir.get('termin_tarihi')
            termin_str = termin.strftime('%d.%m.%Y') if termin else ''
            self.satirlar_table.setItem(i, 7, QTableWidgetItem(termin_str))
            
            kalite = satir.get('kalite_durumu', 'BEKLIYOR')
            kalite_item = QTableWidgetItem(kalite or 'BEKLIYOR')
            self.satirlar_table.setItem(i, 8, kalite_item)
            
            # İşlem butonları - row index'ini closure'da doğru yakalamak için
            self._add_row_buttons(i)
            
            # Satır yüksekliğini ayarla (butonların görünmesi için)
            self.satirlar_table.setRowHeight(i, 40)
    
    def _add_row_buttons(self, row: int):
        """Satır için işlem butonlarını ekle"""
        widget = create_action_buttons(self.theme, [
            ("🏷️", "Palet Böl ve Etiket Yazdır", lambda checked, r=row: self._etiket_yazdir(r), "success"),
            ("🗑️", "Satırı Sil", lambda checked, r=row: self._delete_satir(r), "delete"),
        ])
        self.satirlar_table.setCellWidget(row, 9, widget)
        self.satirlar_table.setRowHeight(row, 42)

    def _add_satir(self):
        """Yeni satır ekle"""
        urun_data = self.urun_combo.currentData()
        if not urun_data:
            QMessageBox.warning(self, "Uyarı", "Lütfen ürün seçin!")
            return
        
        miktar = self.miktar_input.value()
        if miktar <= 0:
            QMessageBox.warning(self, "Uyarı", "Miktar 0'dan büyük olmalı!")
            return
        
        row = self.satirlar_table.rowCount()
        self.satirlar_table.insertRow(row)
        
        self.satirlar_table.setItem(row, 0, QTableWidgetItem(""))  # ID boş (yeni)
        self.satirlar_table.setItem(row, 1, QTableWidgetItem(urun_data.get('stok_kodu', '')))
        self.satirlar_table.setItem(row, 2, QTableWidgetItem(urun_data.get('stok_adi', '')))
        self.satirlar_table.setItem(row, 3, QTableWidgetItem(f"{miktar:,.0f}"))
        self.satirlar_table.setItem(row, 4, QTableWidgetItem(urun_data.get('birim', 'ADET')))
        self.satirlar_table.setItem(row, 5, QTableWidgetItem(urun_data.get('kaplama', '') or ''))
        self.satirlar_table.setItem(row, 6, QTableWidgetItem(""))  # Lot boş
        self.satirlar_table.setItem(row, 7, QTableWidgetItem(""))  # Termin boş
        self.satirlar_table.setItem(row, 8, QTableWidgetItem("BEKLIYOR"))
        
        # İşlem butonları
        self._add_row_buttons(row)
        
        # Satır yüksekliğini ayarla
        self.satirlar_table.setRowHeight(row, 40)
        
        # Miktar sıfırla
        self.miktar_input.setValue(0)
    
    def _delete_satir(self, row: int):
        """Satırı sil"""
        reply = QMessageBox.question(self, "Onay", "Satırı silmek istediğinize emin misiniz?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.satirlar_table.removeRow(row)
    
    def _etiket_yazdir(self, row: int):
        """Seçili satır için etiket yazdırma dialogu aç"""
        stok_kodu = self.satirlar_table.item(row, 1).text()
        stok_adi = self.satirlar_table.item(row, 2).text()
        miktar_text = self.satirlar_table.item(row, 3).text()
        birim = self.satirlar_table.item(row, 4).text()
        kaplama = self.satirlar_table.item(row, 5).text()

        try:
            miktar = float(miktar_text.replace(',', ''))
        except Exception:
            miktar = 0

        if miktar <= 0:
            QMessageBox.warning(self, "Uyarı", "Miktar 0'dan büyük olmalı!")
            return

        musteri = self.cari_combo.currentText()
        irsaliye_no = self.irsaliye_no_input.text()

        # Satır ID'sini al (kayıtlıysa)
        satir_id_text = self.satirlar_table.item(row, 0).text()
        satir_id = int(satir_id_text) if satir_id_text else None

        if not satir_id:
            QMessageBox.warning(self, "Uyarı", "Önce irsaliyeyi kaydedin!")
            return

        # Mükerrer lot kontrolü - Bu satır için zaten lot oluşturulmuş mu?
        mevcut_lot = self.satirlar_table.item(row, 6)
        if mevcut_lot and mevcut_lot.text().strip():
            reply = QMessageBox.question(
                self, "Lot Mevcut",
                f"Bu satır için zaten lot oluşturulmuş!\n\n"
                f"Lot No: {mevcut_lot.text().strip()}\n\n"
                f"Tekrar etiket yazdırmak mevcut lota ek stok girişi yapacaktır.\n"
                f"Sadece etiket tekrar basmak istiyorsanız 'Onaylı Ürünler' sekmesinden yapabilirsiniz.\n\n"
                f"Yeni lot oluşturmak istediğinize emin misiniz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Palet bölme dialogu aç
        dialog = PaletBolmeDialog(
            stok_kodu=stok_kodu,
            stok_adi=stok_adi,
            musteri=musteri,
            kaplama=kaplama,
            toplam_miktar=miktar,
            birim=birim,
            irsaliye_no=irsaliye_no,
            irsaliye_satir_id=satir_id,
            theme=self.theme,
            parent=self
        )
        
        if dialog.exec():
            # Dialog başarıyla kapandı, satırları yenile
            self._load_data()
            self._load_satirlar()
    
    def _save(self):
        """İrsaliyeyi kaydet"""
        cari_unvani = self.cari_combo.currentData()
        print(f"[SAVE DEBUG] Başladı | yeni_kayit={self.yeni_kayit} | irsaliye_id={self.irsaliye_id}")
        print(f"[SAVE DEBUG] cari_unvani data={cari_unvani} | text={self.cari_combo.currentText()}")
        print(f"[SAVE DEBUG] satirlar_table rowCount={self.satirlar_table.rowCount()}")
        
        if not cari_unvani:
            QMessageBox.warning(self, "Uyarı", "Müşteri seçiniz!")
            return
        
        if self.satirlar_table.rowCount() == 0:
            QMessageBox.warning(self, "Uyarı", "En az bir satır ekleyiniz!")
            return
        
        # Miktar kontrolü
        for row in range(self.satirlar_table.rowCount()):
            item = self.satirlar_table.item(row, 3)
            if not item:
                QMessageBox.warning(self, "Uyarı", f"Satır {row+1}: Miktar hücresi boş!")
                return
            miktar_text = item.text()
            try:
                miktar = float(miktar_text.replace(',', ''))
                if miktar <= 0:
                    QMessageBox.warning(self, "Uyarı", f"Satır {row+1}: Miktar 0'dan büyük olmalı!")
                    return
            except Exception:
                QMessageBox.warning(self, "Uyarı", f"Satır {row+1}: Geçersiz miktar!")
                return
        
        # RETRY MEKANİZMASI - Deadlock için
        import time
        max_attempts = 3
        
        for attempt in range(max_attempts):
            conn = None
            cursor = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # DEADLOCK ÖNCELİĞİNİ DÜŞÜR VE TIMEOUT AYARLA
                cursor.execute("SET DEADLOCK_PRIORITY LOW")
                cursor.execute("SET LOCK_TIMEOUT 10000")  # 10 saniye
                
                # Autocommit kapalıysa pyodbc kendi transaction yönetimini kullanır
                # Bu yüzden BEGIN/COMMIT TRANSACTION yerine conn.commit() kullanıyoruz
                
                tarih = self.tarih_input.date().toString("yyyy-MM-dd")
                cari_irsaliye_no = self.cari_irsaliye_input.text().strip() or None
                teslim_alan = self.teslim_alan_combo.currentText()
                if teslim_alan == '-- Teslim Alan --':
                    teslim_alan = None
                
                # Plaka - Combo'dan metin al
                plaka = self.plaka_combo.currentText().strip()
                if plaka == '-- Araç Seçin --' or not plaka:
                    plaka = None
                
                # Şoför - Combo'dan metin al  
                sofor = self.sofor_combo.currentText().strip()
                if sofor == '-- Şoför Seçin --' or not sofor:
                    sofor = None
                
                notlar = self.notlar_input.text().strip() or None

                print(f"[SAVE DEBUG] tarih={tarih} | cari={cari_unvani}")

                # Müşteri irsaliye no tekrar kontrolü
                if cari_irsaliye_no:
                    exclude_id = None if self.yeni_kayit else self.irsaliye_id
                    dup_query = """
                        SELECT irsaliye_no, cari_unvani FROM siparis.giris_irsaliyeleri
                        WHERE cari_irsaliye_no = ?
                    """
                    dup_params = [cari_irsaliye_no]
                    if exclude_id:
                        dup_query += " AND id != ?"
                        dup_params.append(exclude_id)

                    cursor.execute(dup_query, dup_params)
                    dup_row = cursor.fetchone()
                    if dup_row:
                        QMessageBox.warning(
                            self, "Mükerrer İrsaliye No",
                            f"Bu müşteri irsaliye numarası daha önce kullanılmış!\n\n"
                            f"İrsaliye No: {dup_row[0]}\n"
                            f"Müşteri: {dup_row[1]}\n"
                            f"Cari İrsaliye No: {cari_irsaliye_no}"
                        )
                        if conn:
                            conn.close()
                        return

                if self.yeni_kayit:
                    # Yeni irsaliye no oluştur - SEQUENCE kullan (Thread-Safe, Deadlock yok!)
                    try:
                        cursor.execute("SELECT NEXT VALUE FOR siparis.seq_giris_irsaliye_id")
                        next_id = cursor.fetchone()[0]
                    except Exception:
                        # Sequence yoksa eski yöntemi kullan
                        cursor.execute("SELECT ISNULL(MAX(id), 0) FROM siparis.giris_irsaliyeleri WITH (TABLOCKX)")
                        next_id = cursor.fetchone()[0] + 1
                    
                    irsaliye_no = f"GRS-{datetime.now().strftime('%Y%m')}-{next_id:04d}"
                    print(f"[SAVE DEBUG] Yeni irsaliye_no={irsaliye_no} | next_id={next_id}")
                    
                    cursor.execute("""
                        INSERT INTO siparis.giris_irsaliyeleri 
                        (irsaliye_no, cari_unvani, cari_irsaliye_no, tarih, teslim_alan, arac_plaka, sofor_adi, notlar, durum, olusturma_tarihi, guncelleme_tarihi)
                        OUTPUT INSERTED.id
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'TASLAK', GETDATE(), GETDATE())
                    """, (irsaliye_no, cari_unvani, cari_irsaliye_no, tarih, teslim_alan, plaka, sofor, notlar))
                    
                    identity_val = cursor.fetchone()[0]
                    print(f"[SAVE DEBUG] OUTPUT INSERTED.id={identity_val}")
                    
                    if identity_val is None:
                        raise Exception("INSERT başarılı ancak SCOPE_IDENTITY NULL döndü!")
                    
                    self.irsaliye_id = int(identity_val)
                    self.irsaliye_no_input.setText(irsaliye_no)
                    self.yeni_kayit = False
                else:
                    print(f"[SAVE DEBUG] UPDATE irsaliye_id={self.irsaliye_id}")
                    cursor.execute("""
                        UPDATE siparis.giris_irsaliyeleri 
                        SET cari_unvani = ?, cari_irsaliye_no = ?, tarih = ?, teslim_alan = ?,
                            arac_plaka = ?, sofor_adi = ?, notlar = ?, guncelleme_tarihi = GETDATE()
                        WHERE id = ?
                    """, (cari_unvani, cari_irsaliye_no, tarih, teslim_alan, plaka, sofor, notlar, self.irsaliye_id))
                    
                    # Mevcut satırları sil (lot oluşturulmamış olanları)
                    cursor.execute("""
                        DELETE FROM siparis.giris_irsaliye_satirlar 
                        WHERE irsaliye_id = ? AND (lot_no IS NULL OR lot_no = '')
                    """, (self.irsaliye_id,))
                
                # Satırları TOPLU ekle/güncelle (Daha hızlı)
                satirlar_data = []
                for row in range(self.satirlar_table.rowCount()):
                    # None kontrolü ile güvenli okuma
                    def safe_text(r, c, default=''):
                        item = self.satirlar_table.item(r, c)
                        return item.text() if item else default
                    
                    satir_id_text = safe_text(row, 0)
                    satir_no = row + 1
                    stok_kodu = safe_text(row, 1).strip()
                    stok_adi = safe_text(row, 2).strip()
                    miktar_raw = safe_text(row, 3).replace(',', '') or '0'
                    miktar = float(miktar_raw)
                    birim = safe_text(row, 4) or 'ADET'
                    kaplama = safe_text(row, 5).strip() or None
                    lot_no = safe_text(row, 6).strip() or None
                    termin_text = safe_text(row, 7).strip()
                    kalite = safe_text(row, 8) or 'BEKLIYOR'
                    
                    print(f"[SAVE DEBUG] Satır {row}: id={satir_id_text} | kod={stok_kodu} | miktar={miktar} | lot={lot_no}")
                    
                    termin = None
                    if termin_text:
                        try:
                            termin = datetime.strptime(termin_text, '%d.%m.%Y').strftime('%Y-%m-%d')
                        except Exception:
                            pass
                    
                    if satir_id_text:
                        # Mevcut satırı güncelle
                        cursor.execute("""
                            UPDATE siparis.giris_irsaliye_satirlar
                            SET satir_no = ?, stok_kodu = ?, stok_adi = ?, miktar = ?, birim = ?, 
                                kaplama = ?, termin_tarihi = ?, kalite_durumu = ?
                            WHERE id = ?
                        """, (satir_no, stok_kodu, stok_adi, miktar, birim, kaplama, termin, kalite, int(satir_id_text)))
                    else:
                        # Yeni satır için veriyi topla
                        satirlar_data.append((self.irsaliye_id, satir_no, stok_kodu, stok_adi, miktar, birim, kaplama, lot_no, termin, kalite))
                
                # Yeni satırları TOPLU INSERT (Daha hızlı)
                if satirlar_data:
                    print(f"[SAVE DEBUG] {len(satirlar_data)} yeni satır INSERT edilecek")
                    cursor.executemany("""
                        INSERT INTO siparis.giris_irsaliye_satirlar
                        (irsaliye_id, satir_no, stok_kodu, stok_adi, miktar, birim, kaplama, lot_no, termin_tarihi, kalite_durumu)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, satirlar_data)
                
                # COMMIT
                conn.commit()
                LogManager.log_insert('depo', 'siparis.giris_irsaliye_satirlar', None, 'Irsaliye kaydi olustu')
                print(f"[SAVE DEBUG] ✅ conn.commit() başarılı! irsaliye_id={self.irsaliye_id}")
                
                # Satırları yeniden yükle (ID'leri almak için)
                self._load_data()
                self._load_satirlar()
                
                QMessageBox.information(self, "Başarılı", f"İrsaliye kaydedildi!\nİrsaliye No: {self.irsaliye_no_input.text()}")
                
                # Başarılı olduysa döngüden çık
                if conn:
                    conn.close()
                return
                
            except Exception as e:
                # ROLLBACK
                print(f"[SAVE DEBUG] ❌ HATA: {e}")
                import traceback
                traceback.print_exc()
                
                if conn:
                    try:
                        conn.rollback()
                        print("[SAVE DEBUG] ROLLBACK yapıldı")
                    except Exception:
                        pass
                
                if conn:
                    conn.close()
                
                error_msg = str(e).lower()
                
                # Deadlock hatası mı?
                if "deadlock" in error_msg and attempt < max_attempts - 1:
                    # Kısa bekle ve tekrar dene
                    time.sleep(0.3 * (attempt + 1))
                    continue
                
                # Son deneme veya başka bir hata
                QMessageBox.critical(
                    self, 
                    "Hata", 
                    f"Kaydetme hatası (Deneme {attempt + 1}/{max_attempts}):\n{str(e)}\n\n"
                    f"{'Lütfen tekrar deneyin.' if 'deadlock' in error_msg else ''}"
                )
                return
    
    def _search_urun(self):
        """Ürün arama dialogu"""
        cari_unvani = self.cari_combo.currentData()
        if not cari_unvani:
            QMessageBox.warning(self, "Uyarı", "Önce müşteri seçin!")
            return
        
        dialog = UrunAramaDialog(cari_unvani, self.theme, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_urun:
            # Seçilen ürünü combo'da bul ve seç
            urun = dialog.selected_urun
            for i in range(self.urun_combo.count()):
                data = self.urun_combo.itemData(i)
                if data and data.get('stok_kodu') == urun.get('stok_kodu'):
                    self.urun_combo.setCurrentIndex(i)
                    break
    
    def _approve(self):
        """İrsaliyeyi onayla - Artık sadece durum günceller, stok girişi etiket yazdırırken yapılıyor"""
        if not self.irsaliye_id:
            QMessageBox.warning(self, "Uyarı", "Önce irsaliyeyi kaydedin!")
            return

        # Mükerrer onay kontrolü - DB'den güncel durumu kontrol et
        try:
            conn_chk = get_db_connection()
            cursor_chk = conn_chk.cursor()
            cursor_chk.execute(
                "SELECT durum FROM siparis.giris_irsaliyeleri WHERE id = ?",
                (self.irsaliye_id,))
            durum_row = cursor_chk.fetchone()
            conn_chk.close()
            if durum_row and durum_row[0] == 'ONAYLANDI':
                QMessageBox.warning(self, "Uyarı", "Bu irsaliye zaten onaylanmış!")
                return
        except Exception:
            pass

        # Tüm satırlarda lot var mı kontrol et
        lot_eksik = False
        for row in range(self.satirlar_table.rowCount()):
            lot_no = self.satirlar_table.item(row, 6).text().strip()
            if not lot_no:
                lot_eksik = True
                break

        if lot_eksik:
            reply = QMessageBox.question(
                self, "Uyarı",
                "Bazı satırlarda lot numarası oluşturulmamış.\n"
                "Etiket yazdırmadan onaylamak istiyor musunuz?\n\n"
                "Not: Lot oluşturulmayan satırlar için stok girişi yapılmayacak.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # İrsaliye durumunu güncelle (sadece henüz onaylanmamışsa)
            cursor.execute("""
                UPDATE siparis.giris_irsaliyeleri
                SET durum = 'ONAYLANDI', guncelleme_tarihi = GETDATE()
                WHERE id = ? AND durum != 'ONAYLANDI'
            """, (self.irsaliye_id,))

            if cursor.rowcount == 0:
                conn.close()
                QMessageBox.warning(self, "Uyarı", "Bu irsaliye zaten onaylanmış!")
                return

            conn.commit()
            LogManager.log_update('depo', 'siparis.giris_irsaliyeleri', None, 'Durum guncellendi')
            conn.close()

            # Bildirim: İrsaliye onaylandı, kalite kontrole bildir
            try:
                from core.bildirim_tetikleyici import BildirimTetikleyici
                irsaliye_no = self.irsaliye_no_input.text()
                musteri = self.cari_combo.currentText()
                BildirimTetikleyici.onay_bekliyor(
                    onaylayici_id=None,
                    kayit_tipi='Giris Kalite Kontrol',
                    kayit_aciklama=f"{irsaliye_no} - {musteri} irsaliyesi onaylandi, giris kalite kontrolu bekliyor.",
                    kaynak_tablo='siparis.giris_irsaliyeleri',
                    kaynak_id=self.irsaliye_id,
                    sayfa_yonlendirme='kalite_giris_kontrol',
                )
            except Exception as bt_err:
                print(f"Bildirim hatasi: {bt_err}")

            QMessageBox.information(
                self,
                "Başarılı",
                f"İrsaliye onaylandı!\n\n"
                f"Etiket yazdırılan satırlar için lot ve stok kayıtları oluşturuldu.\n"
                f"Bu lotlar şimdi kalite onayı bekliyor."
            )
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Onaylama hatası:\n{str(e)}")
            import traceback
            traceback.print_exc()


# ============================================================================
# ANA SAYFA
# ============================================================================

class DepoKabulPage(BasePage):
    """Mal Kabul Sayfası - Giriş İrsaliyeleri"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.page_size = DEFAULT_PAGE_SIZE
        self.current_page = 1
        self.total_items = 0
        self.total_pages = 1
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Başlık
        header = QHBoxLayout()
        title = QLabel("📥 Mal Kabul - Giriş İrsaliyeleri")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 13px;")
        header.addWidget(self.stat_label)
        
        new_btn = QPushButton("➕ Yeni İrsaliye")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setStyleSheet(f"""
            QPushButton {{ background: {self.theme['success']}; color: white; border: none; 
                          border-radius: 6px; padding: 10px 20px; font-weight: bold; font-size: 13px; }}
            QPushButton:hover {{ background: #16a34a; }}
        """)
        new_btn.clicked.connect(self._new_irsaliye)
        header.addWidget(new_btn)
        
        layout.addLayout(header)
        
        # Filtreler
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {self.theme['bg_card']}; border-radius: 8px;")
        f_layout = QHBoxLayout(filter_frame)
        f_layout.setContentsMargins(12, 12, 12, 12)
        f_layout.setSpacing(12)
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 İrsaliye no veya müşteri ara...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{ background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; 
                        border-radius: 6px; padding: 8px 12px; color: {self.theme['text']}; min-width: 200px; }}
        """)
        self.search_input.returnPressed.connect(self._on_search)
        f_layout.addWidget(self.search_input)
        
        # Tarih aralığı
        f_layout.addWidget(QLabel("Başlangıç:"))
        self.tarih_bas = QDateEdit()
        self.tarih_bas.setCalendarPopup(True)
        self.tarih_bas.setDisplayFormat("dd.MM.yyyy")
        self.tarih_bas.setDate(QDate.currentDate().addMonths(-1))
        self.tarih_bas.setStyleSheet(f"background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; border-radius: 6px; padding: 6px; color: {self.theme['text']};")
        f_layout.addWidget(self.tarih_bas)
        
        f_layout.addWidget(QLabel("Bitiş:"))
        self.tarih_bit = QDateEdit()
        self.tarih_bit.setCalendarPopup(True)
        self.tarih_bit.setDisplayFormat("dd.MM.yyyy")
        self.tarih_bit.setDate(QDate.currentDate())
        self.tarih_bit.setStyleSheet(self.tarih_bas.styleSheet())
        f_layout.addWidget(self.tarih_bit)
        
        # Durum
        self.durum_combo = QComboBox()
        self.durum_combo.addItem("Tüm Durumlar", None)
        self.durum_combo.addItem("Taslak", "TASLAK")
        self.durum_combo.addItem("Onaylı", "ONAYLANDI")
        self.durum_combo.addItem("İptal", "IPTAL")
        self.durum_combo.setStyleSheet(f"""
            QComboBox {{ background: {self.theme['bg_input']}; border: 1px solid {self.theme['border']}; 
                        border-radius: 6px; padding: 6px 10px; color: {self.theme['text']}; min-width: 120px; }}
        """)
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        f_layout.addWidget(self.durum_combo)
        
        f_layout.addStretch()
        
        search_btn = QPushButton("Ara")
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.setStyleSheet(f"""
            QPushButton {{ background: {self.theme['primary']}; color: white; border: none; 
                          border-radius: 6px; padding: 8px 20px; font-weight: bold; }}
        """)
        search_btn.clicked.connect(self._on_search)
        f_layout.addWidget(search_btn)

        f_layout.addWidget(self.create_export_button(title="Depo Kabul"))

        layout.addWidget(filter_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "İrsaliye No", "Cari İrs. No", "Müşteri", "Tarih", "Satır", "Durum", "Lot Durumu", "İşlem"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(f"""
            QTableWidget {{ 
                background: {self.theme['bg_card']}; 
                color: {self.theme['text']}; 
                border: 1px solid {self.theme['border']}; 
                border-radius: 8px; 
                gridline-color: {self.theme['border']}; 
            }}
            QTableWidget::item {{ padding: 8px; }}
            QHeaderView::section {{ 
                background: {self.theme['bg_hover']}; 
                color: {self.theme['text']}; 
                padding: 10px; 
                border: none; 
                font-weight: bold; 
            }}
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 110)
        self.table.setColumnWidth(8, 120)
        self.table.doubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.table)
    
    def _load_data(self):
        """Verileri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            search = self.search_input.text().strip()
            tarih_bas = self.tarih_bas.date().toString("yyyy-MM-dd")
            tarih_bit = self.tarih_bit.date().toString("yyyy-MM-dd")
            durum = self.durum_combo.currentData()
            
            query = """
                SELECT gi.id, gi.irsaliye_no, gi.cari_irsaliye_no, gi.cari_unvani, gi.tarih,
                       (SELECT COUNT(*) FROM siparis.giris_irsaliye_satirlar WHERE irsaliye_id = gi.id) as satir_sayisi,
                       gi.durum,
                       (SELECT COUNT(*) FROM siparis.giris_irsaliye_satirlar WHERE irsaliye_id = gi.id AND lot_no IS NOT NULL AND lot_no <> '') as lot_sayisi
                FROM siparis.giris_irsaliyeleri gi
                WHERE gi.tarih BETWEEN ? AND ?
            """
            params = [tarih_bas, tarih_bit]
            
            if search:
                query += " AND (gi.irsaliye_no LIKE ? OR gi.cari_unvani LIKE ? OR gi.cari_irsaliye_no LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
            
            if durum:
                query += " AND gi.durum = ?"
                params.append(durum)
            
            query += " ORDER BY gi.tarih DESC, gi.id DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or ''))
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or ''))

                tarih = row[4]
                tarih_str = tarih.strftime('%d.%m.%Y') if tarih else ''
                self.table.setItem(i, 4, QTableWidgetItem(tarih_str))

                self.table.setItem(i, 5, QTableWidgetItem(str(row[5] or 0)))

                # Durum badge
                durum = row[6] or 'TASLAK'
                durum_item = QTableWidgetItem(durum)
                colors = {'TASLAK': QColor('#f59e0b'), 'ONAYLANDI': QColor('#22c55e'), 'IPTAL': QColor('#ef4444')}
                durum_item.setForeground(colors.get(durum, QColor('#888')))
                self.table.setItem(i, 6, durum_item)

                # Lot durumu
                satir_sayisi = row[5] or 0
                lot_sayisi = row[7] or 0
                if satir_sayisi > 0:
                    lot_durum = f"{lot_sayisi}/{satir_sayisi}"
                    if lot_sayisi == satir_sayisi:
                        lot_durum += " ✅"
                    elif lot_sayisi > 0:
                        lot_durum += " ⏳"
                    else:
                        lot_durum += " ❌"
                else:
                    lot_durum = "-"
                self.table.setItem(i, 7, QTableWidgetItem(lot_durum))

                # İşlem butonu
                widget = self.create_action_buttons([
                    ("📋", "Detay", lambda checked, iid=row[0]: self._open_detail(iid), "view"),
                ])
                self.table.setCellWidget(i, 8, widget)
                self.table.setRowHeight(i, 42)

            self.stat_label.setText(f"Toplam: {len(rows)} irsaliye")
            
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_search(self):
        """Arama"""
        self._load_data()
    
    def _new_irsaliye(self):
        """Yeni irsaliye"""
        dialog = IrsaliyeDetayDialog(None, self.theme, self, yeni_kayit=True)
        dialog.exec()
        self._load_data()
    
    def _open_detail(self, irsaliye_id: int):
        """İrsaliye detayını aç"""
        dialog = IrsaliyeDetayDialog(irsaliye_id, self.theme, self, yeni_kayit=False)
        dialog.exec()
        self._load_data()
    
    def _on_row_double_click(self, index):
        """Satıra çift tıklama"""
        row = index.row()
        irsaliye_id = int(self.table.item(row, 0).text())
        self._open_detail(irsaliye_id)