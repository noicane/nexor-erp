# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Yeni İş Emri Dialog
[MODERNIZED UI - v3.0]
"""
import os
import sys
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QGroupBox,
    QHeaderView, QMessageBox, QDateEdit, QDoubleSpinBox, QTextEdit, 
    QGridLayout, QCheckBox, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, QDate

from core.database import get_db_connection


def get_modern_style(theme: dict) -> dict:
    """Modern tema renkleri"""
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


class IsEmriYeniPage(QDialog):
    """Yeni İş Emri Dialog'u"""
    
    def __init__(self, is_emri_id = None, theme: dict = None, selected_lots: list = None, parent=None):
        super().__init__(parent)
        
        # is_emri_id güvenli dönüşüm
        self.is_emri_id = None
        if is_emri_id is not None:
            try:
                self.is_emri_id = int(is_emri_id)
            except:
                self.is_emri_id = None
        
        self.yeni_kayit = self.is_emri_id is None
        self.theme = theme or {}
        self.s = get_modern_style(self.theme)
        self.is_emri_data = {}
        self.urun_data_cache = {}
        self.hat_data = None
        self.selected_lots = selected_lots or []
        self.from_stok_havuzu = len(self.selected_lots) > 0
        
        # Tema değişkenleri (eski kod uyumluluğu için)
        self.bg_card = self.s['card_bg']
        self.bg_input = self.s['input_bg']
        self.bg_main = self.s['card_bg']
        self.text = self.s['text']
        self.text_muted = self.s['text_muted']
        self.border = self.s['border']
        self.primary = self.s['primary']
        self.success = self.s['success']
        
        self.setWindowTitle("Yeni İş Emri" if self.yeni_kayit else "İş Emri Detay")
        self.setMinimumSize(850, 650)
        self.resize(900, 700)
        
        if not self.yeni_kayit:
            self._load_data()
        
        self._setup_ui()
        self._load_combo_data()
        
        if not self.yeni_kayit:
            self._fill_form()
        elif self.from_stok_havuzu:
            self._fill_from_selected_lots()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {self.bg_main}; }}
            QLabel {{ color: {self.text}; font-size: 13px; }}
            QGroupBox {{ 
                color: {self.text}; font-weight: bold; font-size: 14px;
                border: 1px solid {self.border}; border-radius: 8px; 
                margin-top: 12px; padding-top: 12px;
                background: {self.bg_card};
            }}
            QGroupBox::title {{ 
                subcontrol-origin: margin; left: 16px; padding: 0 8px; 
                background: {self.bg_card}; color: {self.text};
            }}
            QScrollBar:vertical {{
                background: {self.bg_input}; width: 10px; border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.border}; border-radius: 5px; min-height: 20px;
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(16)
        
        # Header
        content_layout.addWidget(self._create_header())
        
        # Bilgiler
        content_layout.addWidget(self._create_bilgi_group())
        
        # Hesaplama
        content_layout.addWidget(self._create_hesap_group())
        
        # Lot seçimi
        content_layout.addWidget(self._create_lot_group())
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Footer
        main_layout.addWidget(self._create_footer())
    
    def _create_header(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.bg_card}; border-radius: 8px; padding: 20px; }}")
        
        layout = QHBoxLayout(frame)
        
        title_text = "➕ Yeni İş Emri" if self.yeni_kayit else f"📋 {self.is_emri_data.get('is_emri_no', '')}"
        title = QLabel(title_text)
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.text};")
        layout.addWidget(title)
        
        layout.addStretch()
        
        if not self.yeni_kayit:
            durum = self.is_emri_data.get('durum', 'BEKLIYOR')
            colors = {'BEKLIYOR': '#f59e0b', 'PLANLI': '#3b82f6', 'URETIMDE': '#22c55e', 'TAMAMLANDI': '#10b981'}
            badge = QLabel(f"  {durum}  ")
            badge.setStyleSheet(f"background: {colors.get(durum, '#888')}; color: white; padding: 10px 24px; border-radius: 16px; font-weight: bold; font-size: 13px;")
            layout.addWidget(badge)
        
        return frame
    
    def _create_bilgi_group(self) -> QGroupBox:
        group = QGroupBox("📋 İş Emri Bilgileri")
        layout = QGridLayout(group)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 28, 20, 20)
        
        input_style = f"""
            background: {self.bg_input}; border: 1px solid {self.border};
            border-radius: 6px; padding: 10px 14px; color: {self.text}; font-size: 14px;
            min-height: 20px;
        """
        label_style = f"color: {self.text}; font-weight: bold; font-size: 13px;"
        
        # İş Emri No
        lbl = QLabel("İş Emri No:")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl, 0, 0)
        
        self.is_emri_no_input = QLineEdit()
        self.is_emri_no_input.setPlaceholderText("Otomatik")
        self.is_emri_no_input.setReadOnly(True)
        self.is_emri_no_input.setStyleSheet(f"QLineEdit {{ {input_style} }}")
        layout.addWidget(self.is_emri_no_input, 0, 1)
        
        # Termin
        lbl2 = QLabel("Termin:")
        lbl2.setStyleSheet(label_style)
        layout.addWidget(lbl2, 0, 2)
        
        self.termin_input = QDateEdit()
        self.termin_input.setDate(QDate.currentDate().addDays(7))
        self.termin_input.setCalendarPopup(True)
        self.termin_input.setStyleSheet(f"QDateEdit {{ {input_style} }}")
        layout.addWidget(self.termin_input, 0, 3)
        
        # Müşteri
        lbl3 = QLabel("Müşteri:")
        lbl3.setStyleSheet(label_style)
        layout.addWidget(lbl3, 1, 0)
        
        self.cari_combo = QComboBox()
        self.cari_combo.addItem("-- Müşteri Seçin --", "")
        self.cari_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.cari_combo.currentIndexChanged.connect(self._on_cari_changed)
        layout.addWidget(self.cari_combo, 1, 1, 1, 3)
        
        # Ürün
        lbl4 = QLabel("Ürün:")
        lbl4.setStyleSheet(label_style)
        layout.addWidget(lbl4, 2, 0)
        
        self.urun_combo = QComboBox()
        self.urun_combo.addItem("-- Önce müşteri seçin --", "")
        self.urun_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.urun_combo.currentIndexChanged.connect(self._on_urun_changed)
        layout.addWidget(self.urun_combo, 2, 1, 1, 3)
        
        # Miktar
        lbl5 = QLabel("Miktar:")
        lbl5.setStyleSheet(label_style)
        layout.addWidget(lbl5, 3, 0)
        
        self.miktar_input = QDoubleSpinBox()
        self.miktar_input.setRange(0, 999999999)
        self.miktar_input.setDecimals(0)
        self.miktar_input.setStyleSheet(f"QDoubleSpinBox {{ {input_style} }}")
        self.miktar_input.valueChanged.connect(self._hesapla)
        layout.addWidget(self.miktar_input, 3, 1)
        
        # Öncelik
        lbl6 = QLabel("Öncelik:")
        lbl6.setStyleSheet(label_style)
        layout.addWidget(lbl6, 3, 2)
        
        self.oncelik_combo = QComboBox()
        self.oncelik_combo.addItem("Acil (1)", 1)
        self.oncelik_combo.addItem("Yüksek (3)", 3)
        self.oncelik_combo.addItem("Normal (5)", 5)
        self.oncelik_combo.addItem("Düşük (7)", 7)
        self.oncelik_combo.setCurrentIndex(2)
        self.oncelik_combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        layout.addWidget(self.oncelik_combo, 3, 3)
        
        # Not
        lbl7 = QLabel("Not:")
        lbl7.setStyleSheet(label_style)
        layout.addWidget(lbl7, 4, 0)
        
        self.not_input = QTextEdit()
        self.not_input.setMaximumHeight(70)
        self.not_input.setPlaceholderText("İş emri ile ilgili notlar...")
        self.not_input.setStyleSheet(f"QTextEdit {{ {input_style} }}")
        layout.addWidget(self.not_input, 4, 1, 1, 3)
        
        return group
    
    def _create_hesap_group(self) -> QGroupBox:
        group = QGroupBox("📊 Otomatik Hesaplama")
        layout = QGridLayout(group)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 28, 20, 20)
        
        label_style = f"color: {self.text_muted}; font-size: 13px;"
        value_style = f"font-size: 16px; font-weight: bold; color: {self.primary};"
        
        # Hat
        hat_lbl = QLabel("Hat:")
        hat_lbl.setStyleSheet(label_style)
        layout.addWidget(hat_lbl, 0, 0)
        self.hat_label = QLabel("-")
        self.hat_label.setStyleSheet(value_style)
        layout.addWidget(self.hat_label, 0, 1)
        
        aski_lbl = QLabel("Askı Adedi:")
        aski_lbl.setStyleSheet(label_style)
        layout.addWidget(aski_lbl, 0, 2)
        self.aski_label = QLabel("-")
        self.aski_label.setStyleSheet(value_style)
        layout.addWidget(self.aski_label, 0, 3)
        
        bara_lbl = QLabel("Bara Adedi:")
        bara_lbl.setStyleSheet(label_style)
        layout.addWidget(bara_lbl, 1, 0)
        self.bara_label = QLabel("-")
        self.bara_label.setStyleSheet(value_style)
        layout.addWidget(self.bara_label, 1, 1)
        
        toplam_lbl = QLabel("Toplam Bara:")
        toplam_lbl.setStyleSheet(label_style)
        layout.addWidget(toplam_lbl, 1, 2)
        self.toplam_bara_label = QLabel("-")
        self.toplam_bara_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.success};")
        layout.addWidget(self.toplam_bara_label, 1, 3)
        
        sure_lbl = QLabel("Tahmini Süre:")
        sure_lbl.setStyleSheet(label_style)
        layout.addWidget(sure_lbl, 2, 0)
        self.sure_label = QLabel("-")
        self.sure_label.setStyleSheet(value_style)
        layout.addWidget(self.sure_label, 2, 1)
        
        kaplama_lbl = QLabel("Kaplama:")
        kaplama_lbl.setStyleSheet(label_style)
        layout.addWidget(kaplama_lbl, 2, 2)
        self.kaplama_label = QLabel("-")
        self.kaplama_label.setStyleSheet(value_style)
        layout.addWidget(self.kaplama_label, 2, 3)
        
        return group
    
    def _create_lot_group(self) -> QGroupBox:
        group = QGroupBox("📦 Lot Seçimi")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 28, 20, 20)
        layout.setSpacing(12)
        
        info = QLabel("Giriş irsaliyesinden lot seçin:")
        info.setStyleSheet(f"color: {self.text_muted}; font-size: 13px;")
        layout.addWidget(info)
        
        self.lot_table = QTableWidget()
        self.lot_table.setColumnCount(5)
        self.lot_table.setHorizontalHeaderLabels(["Seç", "Lot No", "Miktar", "Tarih", "İrsaliye"])
        self.lot_table.setStyleSheet(f"""
            QTableWidget {{ 
                background-color: {self.bg_input}; 
                border: 1px solid {self.border}; 
                border-radius: 6px; 
                color: {self.text};
                gridline-color: {self.border};
            }}
            QTableWidget::item {{ padding: 8px; color: {self.text}; }}
            QTableWidget::item:selected {{ background: {self.primary}; }}
            QHeaderView::section {{ 
                background-color: {self.bg_card}; 
                color: {self.text}; 
                padding: 10px; 
                border: none;
                font-weight: bold;
            }}
        """)
        
        header = self.lot_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.lot_table.setColumnWidth(0, 60)
        self.lot_table.setColumnWidth(2, 80)
        self.lot_table.setColumnWidth(3, 90)
        self.lot_table.setColumnWidth(4, 100)
        self.lot_table.setMaximumHeight(150)
        self.lot_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.lot_table)
        
        self.lot_ozet_label = QLabel("Seçili: 0 lot")
        self.lot_ozet_label.setStyleSheet(f"color: {self.text_muted};")
        layout.addWidget(self.lot_ozet_label)
        
        return group
    
    def _create_footer(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {self.bg_card}; border-radius: 8px; padding: 16px; }}")
        
        layout = QHBoxLayout(frame)
        layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: {self.bg_input}; color: {self.text}; 
                border: 1px solid {self.border}; border-radius: 6px; 
                padding: 12px 28px; font-size: 14px;
            }}
            QPushButton:hover {{ background: {self.border}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: {self.success}; color: white; border: none; 
                border-radius: 6px; padding: 12px 36px; 
                font-weight: bold; font-size: 14px; 
            }}
            QPushButton:hover {{ background: #16a34a; }}
        """)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)
        
        return frame
    
    def _load_combo_data(self):
        """Müşterileri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT c.unvan 
                FROM musteri.cariler c
                INNER JOIN stok.urunler u ON c.id = u.cari_id
                WHERE c.unvan IS NOT NULL AND c.unvan != ''
                ORDER BY c.unvan
            """)
            
            for row in cursor.fetchall():
                try:
                    cari = str(row[0])
                    self.cari_combo.addItem(cari, cari)
                except:
                    pass
            
            conn.close()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _on_cari_changed(self):
        """Müşteri değişince ürünleri yükle"""
        self.urun_combo.clear()
        self.urun_data_cache.clear()
        self._clear_hesaplama()
        
        cari = self.cari_combo.currentData()
        if not cari or not isinstance(cari, str) or len(cari) == 0:
            self.urun_combo.addItem("-- Önce müşteri seçin --", "")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Tüm stokları çek
            cursor.execute("""
                SELECT u.urun_kodu, u.urun_adi, kt.ad as kaplama_tip_adi, 
                       b.ad as birim1, u.aski_adedi as aski_miktar, 
                       u.bara_adedi as bara_miktar, c.unvan as cari_unvani
                FROM stok.urunler u
                LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                WHERE u.aktif_mi = 1
            """)
            
            # Row'ları list olarak al
            all_rows = []
            for row in cursor.fetchall():
                item = []
                for i in range(7):
                    try:
                        item.append(row[i])
                    except:
                        item.append(None)
                all_rows.append(item)
            
            conn.close()
            
            # Python'da filtrele
            rows = [r for r in all_rows if str(r[6] or '') == cari]
            
            if rows:
                self.urun_combo.addItem(f"-- {len(rows)} ürün --", "")
                for row in rows:
                    stok_kodu = str(row[0] or '')
                    stok_adi = str(row[1] or '')
                    kaplama = str(row[2] or '')
                    
                    display = f"{stok_kodu} - {stok_adi}"
                    if kaplama:
                        display += f" [{kaplama}]"
                    
                    # Güvenli tip dönüşümü
                    try:
                        aski_val = int(row[4]) if row[4] is not None else 0
                    except:
                        aski_val = 0
                    
                    try:
                        bara_val = int(row[5]) if row[5] is not None else 0
                    except:
                        bara_val = 0
                    
                    self.urun_data_cache[stok_kodu] = {
                        'stok_kodu': stok_kodu,
                        'stok_adi': stok_adi,
                        'kaplama': kaplama,
                        'birim': str(row[3] or 'ADET'),
                        'aski_adet': aski_val,
                        'bara_adet': bara_val
                    }
                    
                    self.urun_combo.addItem(display, stok_kodu)
            else:
                self.urun_combo.addItem("-- Ürün yok --", "")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.urun_combo.addItem("-- Hata --", "")
    
    def _on_urun_changed(self):
        """Ürün değişince hesapla"""
        stok_kodu = self.urun_combo.currentData()
        
        if not stok_kodu or stok_kodu not in self.urun_data_cache:
            self._clear_hesaplama()
            self.lot_table.setRowCount(0)
            return
        
        data = self.urun_data_cache[stok_kodu]
        
        self.kaplama_label.setText(data.get('kaplama', '-') or '-')
        
        aski = data.get('aski_adet', 0)
        bara = data.get('bara_adet', 0)
        self.aski_label.setText(f"{aski}/askı" if aski else "-")
        self.bara_label.setText(f"{bara}/bara" if bara else "-")
        
        self._find_hat(data.get('kaplama', ''))
        self._load_lots(stok_kodu)
        self._hesapla()
    
    def _find_hat(self, kaplama: str):
        """Kaplama'dan hat bul"""
        self.hat_data = None
        self.hat_label.setText("-")
        
        if not kaplama:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Tüm hatları çek, Python'da filtrele
            cursor.execute("""
                SELECT h.kod, h.ad, h.devir_suresi_dk, h.id, k.ad as kaplama_adi
                FROM tanim.uretim_hatlari h
                LEFT JOIN tanim.kaplama_turleri k ON h.kaplama_turu_id = k.id
                WHERE h.aktif_mi = 1
            """)
            
            rows = []
            for row in cursor.fetchall():
                item = []
                for i in range(5):
                    try:
                        item.append(row[i])
                    except:
                        item.append(None)
                rows.append(item)
            
            conn.close()
            
            kaplama_lower = str(kaplama).lower()
            for row in rows:
                hat_ad = str(row[1] or '').lower()
                kaplama_ad = str(row[4] or '').lower()
                
                if kaplama_lower in hat_ad or kaplama_lower in kaplama_ad:
                    devir = 0
                    try:
                        devir = int(row[2]) if row[2] else 0
                    except:
                        devir = 0
                    
                    self.hat_label.setText(f"{row[0]} - {row[1]}")
                    self.hat_data = {'id': row[3], 'kod': str(row[0] or ''), 'ad': str(row[1] or ''), 'devir_suresi': devir}
                    break
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _load_lots(self, stok_kodu: str):
        """Lot'ları yükle"""
        self.lot_table.setRowCount(0)
        
        if not stok_kodu:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Tüm lot'ları çek
            cursor.execute("""
                SELECT s.lot_no, s.miktar, i.tarih, i.irsaliye_no, s.id, s.stok_kodu
                FROM siparis.giris_irsaliye_satirlar s
                INNER JOIN siparis.giris_irsaliyeleri i ON s.irsaliye_id = i.id
                WHERE i.durum = 'ONAYLANDI'
            """)
            
            all_rows = []
            for row in cursor.fetchall():
                item = []
                for i in range(6):
                    try:
                        item.append(row[i])
                    except:
                        item.append(None)
                all_rows.append(item)
            
            conn.close()
            
            # Python'da filtrele
            rows = [r for r in all_rows if str(r[5] or '') == str(stok_kodu)]
            
            self.lot_table.setRowCount(len(rows))
            
            for idx, row in enumerate(rows):
                cb = QCheckBox()
                cb.setStyleSheet("margin-left: 15px;")
                cb.stateChanged.connect(self._update_lot_ozet)
                self.lot_table.setCellWidget(idx, 0, cb)
                
                lot_item = QTableWidgetItem(str(row[0] or ''))
                lot_item.setData(Qt.UserRole, row[4])
                self.lot_table.setItem(idx, 1, lot_item)
                
                # Miktar güvenli dönüşüm
                try:
                    miktar_val = float(row[1]) if row[1] else 0
                except:
                    miktar_val = 0
                self.lot_table.setItem(idx, 2, QTableWidgetItem(f"{miktar_val:,.0f}"))
                
                self.lot_table.setItem(idx, 3, QTableWidgetItem(str(row[2])[:10] if row[2] else ""))
                self.lot_table.setItem(idx, 4, QTableWidgetItem(str(row[3] or '')))
                
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _update_lot_ozet(self):
        toplam = 0
        for row in range(self.lot_table.rowCount()):
            cb = self.lot_table.cellWidget(row, 0)
            if cb and cb.isChecked():
                toplam += 1
        self.lot_ozet_label.setText(f"Seçili: {toplam} lot")
    
    def _clear_hesaplama(self):
        self.hat_label.setText("-")
        self.aski_label.setText("-")
        self.bara_label.setText("-")
        self.toplam_bara_label.setText("-")
        self.sure_label.setText("-")
        self.kaplama_label.setText("-")
        self.hat_data = None
    
    def _hesapla(self):
        stok_kodu = self.urun_combo.currentData()
        miktar = self.miktar_input.value()
        
        if not stok_kodu or stok_kodu not in self.urun_data_cache or miktar <= 0:
            self.toplam_bara_label.setText("-")
            self.sure_label.setText("-")
            return
        
        data = self.urun_data_cache[stok_kodu]
        bara_miktar = data.get('bara_adet', 1) or 1  # Bir barada kaç adet
        
        # İş Emri Miktarı / Bara Adeti = Yapılacak Bara Adedi
        import math
        toplam_bara = math.ceil(miktar / bara_miktar)
        
        self.toplam_bara_label.setText(f"{toplam_bara} bara")
        
        if self.hat_data:
            devir = self.hat_data.get('devir_suresi', 0)
            sure_dk = toplam_bara * devir
            self.sure_label.setText(f"{sure_dk // 60}s {sure_dk % 60}dk")
        else:
            self.sure_label.setText("-")
    
    def _fill_from_selected_lots(self):
        """Stok havuzundan seçilen lotlarla formu doldur"""
        if not self.selected_lots:
            return
        
        # İlk lottan müşteri ve ürün bilgisini al (hepsi aynı olmalı)
        first_lot = self.selected_lots[0]
        musteri = first_lot.get('musteri', '')
        urun_kodu = first_lot.get('urun_kodu', '')
        urun_adi = first_lot.get('urun_adi', '')
        bara_miktar = first_lot.get('bara_miktar', 1)
        
        # Toplam miktar hesapla
        toplam_miktar = sum(lot.get('kullanilabilir', 0) for lot in self.selected_lots)
        
        # Müşteri combo'yu seç ve kilitle
        if musteri:
            for i in range(self.cari_combo.count()):
                if self.cari_combo.itemText(i) == musteri:
                    self.cari_combo.setCurrentIndex(i)
                    break
            self.cari_combo.setEnabled(False)
        
        # Ürün listesini güncelle (müşteriye göre)
        self._on_cari_changed()
        
        # Ürün seç ve kilitle
        if urun_kodu:
            for i in range(self.urun_combo.count()):
                if self.urun_combo.itemData(i) == urun_kodu:
                    self.urun_combo.setCurrentIndex(i)
                    break
            self.urun_combo.setEnabled(False)
        
        # Miktar set et
        self.miktar_input.setValue(toplam_miktar)
        
        # Lot tablosunu seçili lotlarla doldur
        self._fill_lot_table_from_selection()
        
        # Hesapla
        self._hesapla()
    
    def _fill_lot_table_from_selection(self):
        """Lot tablosunu seçili lotlarla doldur"""
        self.lot_table.setRowCount(len(self.selected_lots))
        
        for i, lot in enumerate(self.selected_lots):
            # Checkbox - seçili ve kilitli
            cb = QCheckBox()
            cb.setChecked(True)
            cb.setEnabled(False)  # Değiştirilemez
            cb.setStyleSheet("QCheckBox { margin-left: 10px; }")
            self.lot_table.setCellWidget(i, 0, cb)
            
            # Lot No
            lot_item = QTableWidgetItem(str(lot.get('lot_no', '')))
            self.lot_table.setItem(i, 1, lot_item)
            
            # Miktar
            miktar = lot.get('kullanilabilir', 0)
            miktar_item = QTableWidgetItem(f"{miktar:,.0f}")
            miktar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lot_table.setItem(i, 2, miktar_item)
            
            # Tarih (stok_bakiye'de son_hareket_tarihi)
            self.lot_table.setItem(i, 3, QTableWidgetItem("-"))
            
            # İrsaliye
            self.lot_table.setItem(i, 4, QTableWidgetItem("-"))
        
        self._update_lot_ozet()
    
    def _load_data(self):
        """Mevcut veriyi yükle"""
        if self.is_emri_id is None:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT id, is_emri_no, cari_unvani, stok_kodu, stok_adi, kaplama_tipi,
                       toplam_miktar, birim, toplam_bara, tahmini_sure_dk, hat_id,
                       termin_tarihi, oncelik, durum, uretim_notu
                FROM siparis.is_emirleri WHERE id = {self.is_emri_id}
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # Her kolonu tek tek al
                row = []
                for i in range(15):
                    try:
                        row.append(result[i])
                    except:
                        row.append(None)
                
                self.is_emri_data = {
                    'id': row[0], 
                    'is_emri_no': str(row[1] or ''), 
                    'cari_unvani': str(row[2] or ''),
                    'stok_kodu': str(row[3] or ''), 
                    'stok_adi': str(row[4] or ''), 
                    'kaplama_tipi': str(row[5] or ''),
                    'toplam_miktar': row[6], 
                    'birim': str(row[7] or ''), 
                    'toplam_bara': row[8],
                    'tahmini_sure_dk': row[9], 
                    'hat_id': row[10], 
                    'termin_tarihi': row[11],
                    'oncelik': row[12], 
                    'durum': str(row[13] or ''), 
                    'uretim_notu': str(row[14] or '')
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _fill_form(self):
        if not self.is_emri_data:
            return
        
        self.is_emri_no_input.setText(str(self.is_emri_data.get('is_emri_no', '')))
        
        termin = self.is_emri_data.get('termin_tarihi')
        if termin:
            self.termin_input.setDate(QDate(termin.year, termin.month, termin.day))
        
        cari = self.is_emri_data.get('cari_unvani')
        if cari:
            for i in range(self.cari_combo.count()):
                if self.cari_combo.itemData(i) == cari:
                    self.cari_combo.setCurrentIndex(i)
                    break
        
        miktar = self.is_emri_data.get('toplam_miktar')
        if miktar:
            self.miktar_input.setValue(float(miktar))
        
        oncelik = self.is_emri_data.get('oncelik', 5)
        for i in range(self.oncelik_combo.count()):
            if self.oncelik_combo.itemData(i) == oncelik:
                self.oncelik_combo.setCurrentIndex(i)
                break
        
        not_text = self.is_emri_data.get('uretim_notu')
        if not_text:
            self.not_input.setPlainText(str(not_text))
    
    def _save(self):
        cari = self.cari_combo.currentData()
        if not cari or not isinstance(cari, str) or len(cari) == 0:
            QMessageBox.warning(self, "Uyarı", "Müşteri seçin!")
            return
        
        stok_kodu = self.urun_combo.currentData()
        if not stok_kodu or stok_kodu not in self.urun_data_cache:
            QMessageBox.warning(self, "Uyarı", "Ürün seçin!")
            return
        
        miktar = self.miktar_input.value()
        if miktar <= 0:
            QMessageBox.warning(self, "Uyarı", "Miktar girin!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            data = self.urun_data_cache[stok_kodu]
            termin = self.termin_input.date().toString("yyyy-MM-dd")
            oncelik_data = self.oncelik_combo.currentData()
            try:
                oncelik = int(oncelik_data) if oncelik_data is not None else 5
            except:
                oncelik = 5
            uretim_notu = self.not_input.toPlainText().strip()
            
            stok_adi = data.get('stok_adi', '')
            kaplama = data.get('kaplama', '')
            birim = data.get('birim', 'ADET')
            aski = data.get('aski_adet', 0)
            bara = data.get('bara_adet', 0)
            
            toplam_aski = miktar / aski if aski > 0 else 0
            toplam_bara = int(toplam_aski / bara) + (1 if bara > 0 and (toplam_aski / bara) % 1 > 0 else 0) if bara > 0 else 0
            
            tahmini_sure = 0
            hat_id = 'NULL'
            if self.hat_data:
                tahmini_sure = toplam_bara * self.hat_data.get('devir_suresi', 0)
                hat_id = self.hat_data.get('id') or 'NULL'
            
            if self.yeni_kayit:
                # Cari ID bul
                cursor.execute(f"SELECT TOP 1 id FROM musteri.cariler WHERE unvan LIKE N'%{cari}%'")
                cari_result = cursor.fetchone()
                cari_id = int(cari_result[0]) if cari_result else 1
                
                # Ürün ID bul
                cursor.execute(f"SELECT id FROM StokKartlari WHERE stok_kodu = N'{stok_kodu}'")
                urun_result = cursor.fetchone()
                urun_id = 1
                if urun_result:
                    try:
                        urun_id = int(urun_result[0])
                    except:
                        urun_id = 1
                
                # Kaplama türü ID bul
                cursor.execute(f"SELECT id FROM tanim.kaplama_turleri WHERE ad LIKE N'%{kaplama}%'")
                kaplama_result = cursor.fetchone()
                kaplama_id = 1
                if kaplama_result:
                    try:
                        kaplama_id = int(kaplama_result[0])
                    except:
                        kaplama_id = 1
                
                # Birim ID bul
                cursor.execute(f"SELECT id FROM tanim.birimler WHERE kod = N'{birim}' OR ad = N'{birim}'")
                birim_result = cursor.fetchone()
                birim_id = 1
                if birim_result:
                    try:
                        birim_id = int(birim_result[0])
                    except:
                        birim_id = 1
                
                cursor.execute("SELECT ISNULL(MAX(id), 0) FROM siparis.is_emirleri")
                max_result = cursor.fetchone()
                max_id = 0
                if max_result:
                    try:
                        max_id = int(max_result[0])
                    except:
                        max_id = 0
                is_emri_no = f"IE-{datetime.now().strftime('%Y%m')}-{max_id + 1:04d}"
                
                # String interpolation ile SQL
                sql = f"""
                    INSERT INTO siparis.is_emirleri 
                    (is_emri_no, tarih, cari_id, cari_unvani, urun_id, stok_kodu, stok_adi, 
                     kaplama_turu_id, kaplama_tipi, planlanan_miktar, toplam_miktar, birim_id, birim, 
                     aski_adet, bara_adet, toplam_bara, tahmini_sure_dk,
                     hat_id, termin_tarihi, oncelik, durum, uretim_notu, silindi_mi)
                    VALUES (
                        N'{is_emri_no}', GETDATE(), {cari_id}, N'{cari}', {urun_id}, N'{stok_kodu}', N'{stok_adi}', 
                        {kaplama_id}, N'{kaplama}', {miktar}, {miktar}, {birim_id}, N'{birim}',
                        {aski}, {bara}, {toplam_bara}, {tahmini_sure},
                        {hat_id}, '{termin}', {oncelik}, 'BEKLIYOR', N'{uretim_notu}', 0
                    )
                """
                cursor.execute(sql)
                
                cursor.execute("SELECT @@IDENTITY")
                id_result = cursor.fetchone()
                self.is_emri_id = 0
                if id_result:
                    try:
                        self.is_emri_id = int(id_result[0])
                    except:
                        self.is_emri_id = 0
                
                self._save_lots(cursor)
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Başarılı", f"İş emri: {is_emri_no}")
                self.accept()
            else:
                # Cari ID bul
                cursor.execute(f"SELECT TOP 1 id FROM musteri.cariler WHERE unvan LIKE N'%{cari}%'")
                cari_result = cursor.fetchone()
                cari_id = int(cari_result[0]) if cari_result else 1
                
                # Ürün ID bul
                cursor.execute(f"SELECT id FROM StokKartlari WHERE stok_kodu = N'{stok_kodu}'")
                urun_result = cursor.fetchone()
                urun_id = 1
                if urun_result:
                    try:
                        urun_id = int(urun_result[0])
                    except:
                        urun_id = 1
                
                # Kaplama türü ID bul
                cursor.execute(f"SELECT id FROM tanim.kaplama_turleri WHERE ad LIKE N'%{kaplama}%'")
                kaplama_result = cursor.fetchone()
                kaplama_id = 1
                if kaplama_result:
                    try:
                        kaplama_id = int(kaplama_result[0])
                    except:
                        kaplama_id = 1
                
                sql = f"""
                    UPDATE siparis.is_emirleri SET
                        cari_id = {cari_id}, cari_unvani = N'{cari}', 
                        urun_id = {urun_id}, stok_kodu = N'{stok_kodu}', stok_adi = N'{stok_adi}',
                        kaplama_turu_id = {kaplama_id}, kaplama_tipi = N'{kaplama}', 
                        planlanan_miktar = {miktar}, toplam_miktar = {miktar}, birim = N'{birim}',
                        aski_adet = {aski}, bara_adet = {bara}, toplam_bara = {toplam_bara},
                        tahmini_sure_dk = {tahmini_sure}, hat_id = {hat_id}, termin_tarihi = '{termin}',
                        oncelik = {oncelik}, uretim_notu = N'{uretim_notu}', guncelleme_tarihi = GETDATE()
                    WHERE id = {self.is_emri_id}
                """
                cursor.execute(sql)
                
                cursor.execute(f"DELETE FROM siparis.is_emri_lotlar WHERE is_emri_id = {self.is_emri_id}")
                self._save_lots(cursor)
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Başarılı", "Güncellendi!")
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası:\n{str(e)}")
    
    def _save_lots(self, cursor):
        for row in range(self.lot_table.rowCount()):
            cb = self.lot_table.cellWidget(row, 0)
            if cb and cb.isChecked():
                lot_item = self.lot_table.item(row, 1)
                miktar_item = self.lot_table.item(row, 2)
                
                if lot_item and miktar_item:
                    lot_no = lot_item.text()
                    try:
                        miktar = float(miktar_item.text().replace(',', ''))
                    except:
                        miktar = 0
                    
                    sql = f"""
                        INSERT INTO siparis.is_emri_lotlar (is_emri_id, lot_no, miktar, birim)
                        VALUES ({self.is_emri_id}, N'{lot_no}', {miktar}, 'ADET')
                    """
                    cursor.execute(sql)
