# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Üretim Girişi Sayfası
[MODERNIZED UI - v3.0]

Açıklama:
- Üstte iş emri listesi, altta giriş formu yapısı
- Hat bazlı sekmeli görünüm
- Vardiya ve operatör takibi
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QAbstractItemView, QMessageBox, QWidget, QSpinBox, QLineEdit,
    QComboBox, QTextEdit, QGridLayout, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager


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


class UretimGirisPage(BasePage):
    """Üretim Girişi - Üstte Liste, Altta Form"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)  # Modern stil
        self.selected_row_data = None
        self.baslama_zamani = None  # 🆕 FAZ 2: Başlama zamanı
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
        
        # Saat güncelleme
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
        
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)  # Standart: 24px
        layout.setSpacing(20)  # Standart: 20px
        
        # ===== HEADER =====
        header = QHBoxLayout()
        
        # Sol: Başlık
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        
        title_row = QHBoxLayout()
        icon = QLabel("🏭")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        
        title = QLabel("Üretim Girişi")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        
        subtitle = QLabel("İş emri bazlı üretim giriş ve takip ekranı")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        
        header.addLayout(title_section)
        header.addStretch()
        
        # Sağ: Saat ve Yenile butonu
        self.saat_label = QLabel()
        self.saat_label.setStyleSheet(f"color: {s['primary']}; font-size: 20px; font-weight: bold;")
        header.addWidget(self.saat_label)
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {s['border']}; }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        layout.addLayout(header)
        
        # ===== HAT SEKMELERİ =====
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{ 
                border: 1px solid {s['border']}; 
                border-radius: 12px;
                background: {s['card_bg']};
            }}
            QTabBar::tab {{ 
                background: {s['input_bg']}; 
                color: {s['text_secondary']}; 
                padding: 14px 28px; 
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{ 
                background: {s['primary']}; 
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background: {s['border']};
            }}
        """)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tab_widget, 1)
    
    def _update_time(self):
        self.saat_label.setText(QTime.currentTime().toString("HH:mm:ss"))
    
    def _load_data(self):
        """Tüm verileri yükle"""
        self._load_hatlar()
    
    def _load_hatlar(self):
        """Hat sekmelerini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, kod, ad 
                FROM tanim.uretim_hatlari 
                WHERE aktif_mi = 1 
                ORDER BY kod
            """)
            
            hatlar = cursor.fetchall()
            conn.close()
            
            current_tab = self.tab_widget.currentIndex()
            self.tab_widget.clear()
            
            for hat in hatlar:
                hat_id, kod, ad = hat
                tab_content = self._create_tab_content(hat_id)
                self.tab_widget.addTab(tab_content, f"{kod}")
            
            if self.tab_widget.count() > 0:
                if current_tab >= 0 and current_tab < self.tab_widget.count():
                    self.tab_widget.setCurrentIndex(current_tab)
                self._load_is_emirleri(self.tab_widget.currentIndex())
                
        except Exception as e:
            print(f"Hat yükleme hatası: {e}")
    
    def _create_tab_content(self, hat_id):
        """Her hat için içerik oluştur - üstte tablo, altta form"""
        s = self.s
        container = QWidget()
        container.setProperty("hat_id", hat_id)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Splitter ile üst-alt ayırma
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {s['border']};
                height: 4px;
            }}
        """)
        
        # ===== ÜST KISIM: İŞ EMRİ TABLOSU =====
        table_frame = QFrame()
        table_frame.setStyleSheet(f"""
            QFrame {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 12px;
            }}
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(16, 16, 16, 16)
        
        # Tablo
        table = QTableWidget()
        table.setProperty("hat_id", hat_id)
        table.setObjectName("is_emri_table")
        table.setColumnCount(13)
        table.setHorizontalHeaderLabels([
            "ID", "Acil", "İş Emri No", "Stok Kodu", "Stok Adı", "Müşteri",
            "Bakiye Miktar", "Üretilen Adet", "Kalan Adet", 
            "Parça/Bara", "Hedef Bara", "Kalan Bara", "İşlem Tarihi",
            "Teknik Resim No", "Reçete No"
        ])
        table.setColumnHidden(0, True)  # ID gizli
        
        # Kolon genişlikleri
        table.setColumnWidth(1, 50)    # Acil
        table.setColumnWidth(2, 110)   # İş Emri No
        table.setColumnWidth(3, 100)   # Stok Kodu
        table.setColumnWidth(4, 200)   # Stok Adı
        table.setColumnWidth(5, 220)   # Müşteri
        table.setColumnWidth(6, 90)    # Bakiye Miktar
        table.setColumnWidth(7, 90)    # Üretilen Adet
        table.setColumnWidth(8, 90)    # Kalan Adet
        table.setColumnWidth(9, 80)    # Parça/Bara
        table.setColumnWidth(10, 80)   # Hedef Bara
        table.setColumnWidth(11, 80)   # Kalan Bara
        table.setColumnWidth(12, 130)  # İşlem Tarihi
        table.setColumnWidth(13, 120)  # Teknik Resim No
        table.setColumnWidth(14, 100)  # Reçete No
        
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 10px;
                gridline-color: {s['border']};
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {s['border']};
            }}
            QTableWidget::item:selected {{
                background: {s['primary']};
            }}
            QTableWidget::item:hover {{
                background: rgba(220, 38, 38, 0.1);
            }}
            QHeaderView::section {{
                background: rgba(0, 0, 0, 0.3);
                color: {s['text_secondary']};
                padding: 12px 10px;
                border: none;
                border-bottom: 2px solid {s['primary']};
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }}
        """)
        
        table.clicked.connect(lambda idx, t=table: self._on_row_selected(t, idx.row()))
        table_layout.addWidget(table)
        splitter.addWidget(table_frame)
        
        # ===== ALT KISIM: GİRİŞ FORMU =====
        form_frame = QFrame()
        form_frame.setObjectName("form_frame")
        form_frame.setStyleSheet(f"""
            QFrame#form_frame {{
                background: {s['card_bg']};
                border: 2px solid {s['success']};
                border-radius: 12px;
            }}
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(12, 10, 12, 10)
        form_layout.setSpacing(6)
        
        # Seçim Bilgi Etiketi
        selection_label = QLabel("⚠️ Seçim: Lütfen yukarıdan bir iş emri seçin")
        selection_label.setObjectName("selection_label")
        selection_label.setStyleSheet(f"""
            font-size: 13px; 
            font-weight: 600; 
            color: {s['warning']};
            padding: 8px;
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid {s['warning']};
            border-radius: 6px;
        """)
        form_layout.addWidget(selection_label)
        
        # Detay Bilgileri
        detail_label = QLabel("Bakiye: - | Üretilen: - | Kalan: - | Parça/Bara: - | Kalan Bara: -")
        detail_label.setObjectName("detail_label")
        detail_label.setStyleSheet(f"""
            font-size: 12px; 
            color: {s['text_secondary']};
            padding: 4px;
        """)
        form_layout.addWidget(detail_label)
        
        # Reçete Bilgileri (Teknik Resim No & Reçete No)
        recete_label = QLabel("📐 Teknik Resim No: - | 📋 Reçete No: -")
        recete_label.setObjectName("recete_label")
        recete_label.setStyleSheet(f"""
            font-size: 12px; 
            color: {s['info']};
            padding: 4px;
            font-weight: 500;
        """)
        form_layout.addWidget(recete_label)
        
        # Form Grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)
        
        label_style = f"color: {s['text']}; font-size: 12px; font-weight: 600;"
        input_style = f"""
            QLineEdit, QSpinBox, QComboBox {{
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: 1px solid {s['border']}; 
                border-radius: 6px; 
                padding: 6px 10px;
                font-size: 12px;
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {s['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
        """
        
        # ========== VARDIYA SEÇİMİ ==========
        vardiya_lbl = QLabel("Vardiya:")
        vardiya_lbl.setStyleSheet(label_style)
        grid.addWidget(vardiya_lbl, 0, 0)
        
        vardiya_combo = QComboBox()
        vardiya_combo.setObjectName("vardiya_combo")
        vardiya_combo.setStyleSheet(input_style)
        
        # Vardiyaları yükle
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad, baslangic_saati, bitis_saati
                FROM tanim.vardiyalar
                WHERE aktif_mi = 1
                ORDER BY baslangic_saati
            """)
            
            vardiya_combo.addItem("-- Vardiya Seçin --", None)
            for row in cursor.fetchall():
                v_id, v_kod, v_ad, v_bas, v_bit = row
                
                # Saat formatı
                bas_str = v_bas.strftime("%H:%M") if v_bas else ""
                bit_str = v_bit.strftime("%H:%M") if v_bit else ""
                
                # Gösterim: "1. Vardiya (08:00-16:00)"
                display_text = f"{v_ad} ({bas_str}-{bit_str})"
                vardiya_combo.addItem(display_text, v_id)
            
            conn.close()
        except Exception as e:
            print(f"Vardiya yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
        
        grid.addWidget(vardiya_combo, 0, 1)
        
        # ========== OPERATÖR SEÇİMİ ==========
        operator_lbl = QLabel("Operatör:")
        operator_lbl.setStyleSheet(label_style)
        grid.addWidget(operator_lbl, 1, 0)
        
        operator_combo = QComboBox()
        operator_combo.setObjectName("operator_combo")
        operator_combo.setStyleSheet(input_style)
        
        # Operatörleri yükle
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ad + ' ' + soyad AS ad_soyad, sicil_no
                FROM ik.personeller
                WHERE aktif_mi = 1
                  AND silindi_mi = 0
                ORDER BY ad, soyad
            """)
            
            operator_combo.addItem("-- Operatör Seçin --", None)
            for row in cursor.fetchall():
                p_id, p_ad, p_sicil = row
                
                # Gösterim: "Ahmet Yılmaz (12345)"
                if p_sicil:
                    display_text = f"{p_ad} ({p_sicil})"
                else:
                    display_text = p_ad
                
                operator_combo.addItem(display_text, p_id)
            
            conn.close()
        except Exception as e:
            print(f"Operatör yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
        
        grid.addWidget(operator_combo, 1, 1)
        
        # Parça / Bara (Otomatik)
        lbl2 = QLabel("Parça / Bara (Otomatik):")
        lbl2.setStyleSheet(label_style)
        grid.addWidget(lbl2, 2, 0)
        
        parca_bara_input = QLineEdit()
        parca_bara_input.setObjectName("parca_bara_input")
        parca_bara_input.setReadOnly(True)
        parca_bara_input.setStyleSheet(input_style + f"""
            QLineEdit {{ background: {s['border']}; }}
        """)
        grid.addWidget(parca_bara_input, 2, 1)
        
        # Üretilen Adet (kullanıcı bunu girer)
        lbl3 = QLabel("Üretilen Adet:")
        lbl3.setStyleSheet(label_style)
        grid.addWidget(lbl3, 3, 0)
        
        adet_spin = QSpinBox()
        adet_spin.setObjectName("adet_spin")
        adet_spin.setRange(0, 9999999)
        adet_spin.setButtonSymbols(QSpinBox.NoButtons)
        adet_spin.setStyleSheet(input_style)
        grid.addWidget(adet_spin, 3, 1)
        
        # Basılacak Bara (otomatik hesaplanır)
        lbl3b = QLabel("Basılacak Bara:")
        lbl3b.setStyleSheet(label_style)
        grid.addWidget(lbl3b, 4, 0)
        
        bara_label = QLabel("0")
        bara_label.setObjectName("bara_label")
        bara_label.setStyleSheet(f"""
            color: {s['primary']}; 
            font-size: 14px; 
            font-weight: bold;
            padding: 6px;
            background: rgba(220, 38, 38, 0.1);
            border-radius: 6px;
        """)
        grid.addWidget(bara_label, 4, 1)
        
        # Adet değişince bara otomatik hesaplansın
        adet_spin.valueChanged.connect(
            lambda val: self._update_bara_label(container, val)
        )
        
        # Kalite
        lbl4 = QLabel("Kalite:")
        lbl4.setStyleSheet(label_style)
        grid.addWidget(lbl4, 5, 0)
        
        kalite_combo = QComboBox()
        kalite_combo.setObjectName("kalite_combo")
        kalite_combo.addItems(["OK", "NOK", "KONTROL_BEKLIYOR"])
        kalite_combo.setStyleSheet(input_style)
        grid.addWidget(kalite_combo, 5, 1)
        
        # Açıklama
        lbl5 = QLabel("Açıklama:")
        lbl5.setStyleSheet(label_style)
        grid.addWidget(lbl5, 6, 0)
        
        aciklama_input = QTextEdit()
        aciklama_input.setObjectName("aciklama_input")
        aciklama_input.setMaximumHeight(50)
        aciklama_input.setStyleSheet(f"""
            QTextEdit {{
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: 1px solid {s['border']}; 
                border-radius: 6px; 
                padding: 6px;
                font-size: 12px;
            }}
            QTextEdit:focus {{
                border-color: {s['primary']};
            }}
        """)
        grid.addWidget(aciklama_input, 6, 1)
        
        form_layout.addLayout(grid)
        
        # Kaydet Butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setObjectName("save_btn")
        save_btn.setEnabled(False)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['success']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: #059669; }}
            QPushButton:disabled {{ background: {s['border']}; color: {s['text_muted']}; }}
        """)
        save_btn.clicked.connect(lambda: self._save_production(container))
        btn_layout.addWidget(save_btn)
        
        form_layout.addLayout(btn_layout)
        splitter.addWidget(form_frame)
        
        # Splitter oranları (üst %75, alt %25)
        splitter.setSizes([500, 160])
        
        layout.addWidget(splitter)
        return container
    
    def _on_tab_changed(self, index):
        """Sekme değiştiğinde"""
        if index >= 0:
            self._load_is_emirleri(index)
    
    def _load_is_emirleri(self, tab_index):
        """Seçili hat için iş emirlerini yükle"""
        try:
            container = self.tab_widget.widget(tab_index)
            if not container:
                return
            
            hat_id = container.property("hat_id")
            table = container.findChild(QTableWidget, "is_emri_table")
            if not table:
                return
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Hat kodunu al
            cursor.execute("SELECT kod FROM tanim.uretim_hatlari WHERE id = ?", (hat_id,))
            hat_row = cursor.fetchone()
            hat_kodu = hat_row[0] if hat_row else ''
            
            # İş emirlerini çek - Bu hatta üretilecek olanlar
            # İş emirlerini çek - Bu hatta üretilecek olanlar
            cursor.execute("""
                SELECT DISTINCT
                    ie.id,
                    CASE WHEN ie.oncelik = 1 THEN 1 ELSE 0 END as acil,
                    ie.is_emri_no,
                    ie.stok_kodu,
                    LEFT(ie.stok_adi, 50) as stok_adi,
                    LEFT(ie.cari_unvani, 45) as cari_unvani,
                    ISNULL(ie.toplam_miktar, 0) as bakiye_miktar,
                    ISNULL(ie.uretilen_miktar, 0) as uretilen_adet,
                    ISNULL(ie.toplam_miktar, 0) - ISNULL(ie.uretilen_miktar, 0) as kalan_adet,
                    ISNULL(ie.bara_adet, ISNULL(u.bara_adedi, 1)) as parca_bara,
                    CASE 
                        WHEN ISNULL(ie.bara_adet, ISNULL(u.bara_adedi, 1)) > 0 
                        THEN CEILING(CAST(ISNULL(ie.toplam_miktar, 0) AS FLOAT) / ISNULL(ie.bara_adet, ISNULL(u.bara_adedi, 1)))
                        ELSE 0 
                    END as hedef_bara,
                    CASE 
                        WHEN ISNULL(ie.bara_adet, ISNULL(u.bara_adedi, 1)) > 0 
                        THEN CEILING(CAST(ISNULL(ie.toplam_miktar, 0) - ISNULL(ie.uretilen_miktar, 0) AS FLOAT) / ISNULL(ie.bara_adet, ISNULL(u.bara_adedi, 1)))
                        ELSE 0 
                    END as kalan_bara,
                    ISNULL(ie.guncelleme_tarihi, ie.olusturma_tarihi) as islem_tarihi,
                    ie.durum,
                    ie.lot_no,
                    ISNULL(ie.aski_adet, ISNULL(u.aski_adedi, 0)) as aski_miktar,
                    u.teknik_resim_no,
                    u.recete_no
                FROM siparis.is_emirleri ie
                LEFT JOIN stok.urunler u ON ie.urun_id = u.id
                WHERE ie.hat_id = ?
                  AND ie.durum IN ('URETIMDE', 'KALITE_BEKLIYOR')
                  AND ISNULL(ie.silindi_mi, 0) = 0
                  AND (ISNULL(ie.toplam_miktar, 0) - ISNULL(ie.uretilen_miktar, 0)) > 0
                ORDER BY acil DESC, islem_tarihi DESC
            """, (hat_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                table.setRowHeight(i, 40)
                
                # ID (gizli)
                id_item = QTableWidgetItem(str(row[0]))
                table.setItem(i, 0, id_item)
                
                # Acil
                acil_item = QTableWidgetItem("🔴" if row[1] == 1 else "")
                acil_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i, 1, acil_item)
                
                # İş Emri No
                table.setItem(i, 2, QTableWidgetItem(str(row[2] or '')))
                
                # Stok Kodu
                table.setItem(i, 3, QTableWidgetItem(str(row[3] or '')))
                
                # Stok Adı
                table.setItem(i, 4, QTableWidgetItem(str(row[4] or '')))
                
                # Müşteri
                table.setItem(i, 5, QTableWidgetItem(str(row[5] or '')))
                
                # Bakiye Miktar
                bakiye_item = QTableWidgetItem(f"{row[6]:,.0f}")
                bakiye_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(i, 6, bakiye_item)
                
                # Üretilen Adet
                uretilen_item = QTableWidgetItem(f"{row[7]:,.0f}")
                uretilen_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row[7] > 0:
                    uretilen_item.setForeground(QColor("#22c55e"))  # Yeşil
                table.setItem(i, 7, uretilen_item)
                
                # Kalan Adet
                kalan_item = QTableWidgetItem(f"{row[8]:,.0f}")
                kalan_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row[8] > 0:
                    kalan_item.setForeground(QColor("#f59e0b"))  # Turuncu
                table.setItem(i, 8, kalan_item)
                
                # Parça/Bara
                parca_item = QTableWidgetItem(f"{row[9]:,.0f}")
                parca_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(i, 9, parca_item)
                
                # Hedef Bara
                hedef_item = QTableWidgetItem(f"{int(row[10])}")
                hedef_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(i, 10, hedef_item)
                
                # Kalan Bara
                kalan_bara_item = QTableWidgetItem(f"{int(row[11])}")
                kalan_bara_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row[11] > 0:
                    kalan_bara_item.setForeground(QColor("#f59e0b"))
                table.setItem(i, 11, kalan_bara_item)
                
                # İşlem Tarihi
                tarih = row[12]
                if tarih:
                    tarih_str = tarih.strftime("%d.%m.%Y %H:%M") if hasattr(tarih, 'strftime') else str(tarih)
                else:
                    tarih_str = ""
                table.setItem(i, 12, QTableWidgetItem(tarih_str))
                
                # Teknik Resim No
                teknik_resim = row[16] if len(row) > 16 and row[16] else ""
                table.setItem(i, 13, QTableWidgetItem(str(teknik_resim)))
                
                # Reçete No
                recete = row[17] if len(row) > 17 and row[17] else ""
                table.setItem(i, 14, QTableWidgetItem(str(recete)))
                
                # Ek veri sakla (satırda)
                id_item.setData(Qt.UserRole, {
                    'id': row[0],
                    'is_emri_no': row[2],
                    'stok_kodu': row[3],
                    'stok_adi': row[4],
                    'cari_unvani': row[5],
                    'bakiye_miktar': row[6],
                    'uretilen_adet': row[7],
                    'kalan_adet': row[8],
                    'parca_bara': row[9],
                    'hedef_bara': row[10],
                    'kalan_bara': row[11],
                    'durum': row[13],
                    'lot_no': row[14],
                    'aski_miktar': row[15],
                    'teknik_resim_no': teknik_resim,
                    'recete_no': recete
                })
                
        except Exception as e:
            print(f"İş emirleri yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_bara_label(self, container, adet_value):
        """Girilen adete göre bara sayısını hesapla ve göster"""
        bara_label = container.findChild(QLabel, "bara_label")
        if not bara_label or not self.selected_row_data:
            return
        
        parca_bara = self.selected_row_data.get('parca_bara', 1) or 1
        if parca_bara > 0:
            bara = adet_value / parca_bara
            bara_label.setText(f"{bara:.2f}")
        else:
            bara_label.setText("0")
    
    def _on_row_selected(self, table, row):
        """Satır seçildiğinde formu doldur"""
        s = self.s
        try:
            container = table.parent().parent().parent()  # table -> frame -> splitter -> container
            
            # Veri al
            id_item = table.item(row, 0)
            if not id_item:
                return
            
            data = id_item.data(Qt.UserRole)
            if not data:
                return
            
            self.selected_row_data = data
            
            # Form elemanlarını bul
            selection_label = container.findChild(QLabel, "selection_label")
            detail_label = container.findChild(QLabel, "detail_label")
            parca_bara_input = container.findChild(QLineEdit, "parca_bara_input")
            adet_spin = container.findChild(QSpinBox, "adet_spin")
            bara_label = container.findChild(QLabel, "bara_label")
            save_btn = container.findChild(QPushButton, "save_btn")
            
            # Seçim etiketini güncelle
            if selection_label:
                hat_kodu = self.tab_widget.tabText(self.tab_widget.currentIndex())
                selection_label.setText(
                    f"✅ Seçim: {hat_kodu} | İşEmri: {data['is_emri_no']} | Stok: {data['stok_kodu']}"
                )
                selection_label.setStyleSheet(f"""
                    font-size: 13px; 
                    font-weight: 600; 
                    color: {s['success']};
                    padding: 8px;
                    background: rgba(16, 185, 129, 0.1);
                    border: 1px solid {s['success']};
                    border-radius: 6px;
                """)
            
            # Detay etiketini güncelle
            if detail_label:
                detail_label.setText(
                    f"Bakiye: {data['bakiye_miktar']:,.0f} | "
                    f"Üretilen: {data['uretilen_adet']:,.0f} | "
                    f"Kalan: {data['kalan_adet']:,.0f} | "
                    f"Parça/Bara: {data['parca_bara']:,.0f} | "
                    f"Kalan Bara: {int(data['kalan_bara'])}"
                )
            
            # Reçete bilgilerini güncelle
            recete_label = container.findChild(QLabel, "recete_label")
            if recete_label:
                teknik_resim = data.get('teknik_resim_no', '-') or '-'
                recete = data.get('recete_no', '-') or '-'
                recete_label.setText(
                    f"📐 Teknik Resim No: {teknik_resim} | 📋 Reçete No: {recete}"
                )
            
            # Parça/Bara otomatik
            if parca_bara_input:
                parca_bara_input.setText(f"{data['parca_bara']:,.0f}")
            
            # Adet varsayılan değer (kalan miktar)
            if adet_spin:
                kalan = int(data['kalan_adet'])
                adet_spin.setMaximum(kalan)  # Maksimumu kalan miktar yap
                adet_spin.setValue(kalan)
            
            # Bara label güncelle
            if bara_label and data['parca_bara'] > 0:
                bara = data['kalan_adet'] / data['parca_bara']
                bara_label.setText(f"{bara:.2f}")
            
            # 🆕 FAZ 2: Başlama zamanını kaydet
            from datetime import datetime
            self.baslama_zamani = datetime.now()
            print(f"✓ Başlama zamanı kaydedildi: {self.baslama_zamani.strftime('%H:%M:%S')}")
            
            # Kaydet butonunu aktif et
            if save_btn:
                save_btn.setEnabled(True)
                
        except Exception as e:
            print(f"Satır seçim hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_production(self, container):
        """Üretim kaydını kaydet"""
        try:
            if not self.selected_row_data:
                QMessageBox.warning(self, "Uyarı", "Lütfen bir iş emri seçin!")
                return
            
            data = self.selected_row_data
            
            # Form verilerini al
            vardiya_combo = container.findChild(QComboBox, "vardiya_combo")
            operator_combo = container.findChild(QComboBox, "operator_combo")
            adet_spin = container.findChild(QSpinBox, "adet_spin")
            kalite_combo = container.findChild(QComboBox, "kalite_combo")
            aciklama_input = container.findChild(QTextEdit, "aciklama_input")
            
            # Veri çek
            vardiya_id = vardiya_combo.currentData() if vardiya_combo else None
            vardiya_adi = vardiya_combo.currentText() if vardiya_combo else ""
            
            operator_id = operator_combo.currentData() if operator_combo else None
            operator_adi = operator_combo.currentText() if operator_combo else ""
            
            uretilen_adet = adet_spin.value() if adet_spin else 0
            kalite = kalite_combo.currentText() if kalite_combo else "OK"
            aciklama = aciklama_input.toPlainText().strip() if aciklama_input else ""
            
            # Validasyonlar
            if not vardiya_id:
                QMessageBox.warning(self, "Uyarı", "Lütfen vardiya seçin!")
                if vardiya_combo:
                    vardiya_combo.setFocus()
                return
            
            if not operator_id:
                QMessageBox.warning(self, "Uyarı", "Lütfen operatör seçin!")
                if operator_combo:
                    operator_combo.setFocus()
                return
            
            if uretilen_adet <= 0:
                QMessageBox.warning(self, "Uyarı", "Lütfen üretilen adet girin!")
                adet_spin.setFocus()
                return
            
            # Bara hesapla
            parca_bara = data['parca_bara'] or 1
            bara = uretilen_adet / parca_bara if parca_bara > 0 else 0
            
            is_emri_id = data['id']
            
            # Veritabanından güncel değerleri al (mükerrer kontrolü için)
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Güncel iş emri bilgisini çek
            cursor.execute("""
                SELECT 
                    ISNULL(uretilen_miktar, 0) as uretilen,
                    ISNULL(toplam_miktar, 0) as toplam,
                    lot_no,
                    durum
                FROM siparis.is_emirleri 
                WHERE id = ?
            """, (is_emri_id,))
            
            ie_row = cursor.fetchone()
            if not ie_row:
                conn.close()
                QMessageBox.warning(self, "Uyarı", "İş emri bulunamadı!")
                return
            
            mevcut_uretilen = ie_row[0] or 0
            toplam_miktar = ie_row[1] or 0
            lot_no = ie_row[2] or ''
            ie_durum = ie_row[3] or ''
            
            # ⚠️ GÜVENLİK KONTROLÜ: Depo çıkışı yapılmamış iş emirlerine üretim girişi engelle
            if ie_durum == 'PLANLANDI':
                conn.close()
                QMessageBox.warning(
                    self, 
                    "⚠️ Depo Çıkışı Gerekli", 
                    f"Bu iş emri için henüz depo çıkışı yapılmamış!\n\n"
                    f"İş Emri: {data['is_emri_no']}\n"
                    f"Durum: PLANLANDI\n\n"
                    f"Önce 'Depo Çıkış' modülünden malzeme çıkışı yapılmalıdır.\n"
                    f"Depo çıkışı yapıldığında iş emri durumu 'URETIMDE' olacaktır."
                )
                self._load_is_emirleri(self.tab_widget.currentIndex())
                return
            
            # Sadece URETIMDE veya KALITE_BEKLIYOR durumunda üretim girişi yapılabilir
            if ie_durum not in ('URETIMDE', 'KALITE_BEKLIYOR'):
                conn.close()
                QMessageBox.warning(
                    self, 
                    "⚠️ Uygun Olmayan Durum", 
                    f"Bu iş emrine üretim girişi yapılamaz!\n\n"
                    f"İş Emri: {data['is_emri_no']}\n"
                    f"Mevcut Durum: {ie_durum}\n\n"
                    f"Üretim girişi sadece 'URETIMDE' veya 'KALITE_BEKLIYOR' durumundaki iş emirleri için yapılabilir."
                )
                self._load_is_emirleri(self.tab_widget.currentIndex())
                return
            
            # Kalan miktar kontrolü
            kalan_miktar = toplam_miktar - mevcut_uretilen
            
            if kalan_miktar <= 0:
                conn.close()
                QMessageBox.warning(
                    self, 
                    "Uyarı", 
                    f"Bu iş emrinin üretimi tamamlanmış!\n\n"
                    f"Toplam: {toplam_miktar:,.0f}\n"
                    f"Üretilen: {mevcut_uretilen:,.0f}\n"
                    f"Kalan: 0"
                )
                self._load_is_emirleri(self.tab_widget.currentIndex())
                return
            
            # Üretilecek miktar kalan miktarı aşıyor mu?
            if uretilen_adet > kalan_miktar:
                conn.close()
                QMessageBox.warning(
                    self, 
                    "Miktar Aşımı", 
                    f"Girilen miktar kalan miktarı aşıyor!\n\n"
                    f"Kalan miktar: {kalan_miktar:,.0f}\n"
                    f"Girilen miktar: {uretilen_adet:,.0f}\n\n"
                    f"Maksimum girebileceğiniz adet: {kalan_miktar:,.0f}"
                )
                adet_spin.setValue(int(kalan_miktar))
                return
            
            # Onay iste
            yeni_uretilen = mevcut_uretilen + uretilen_adet
            reply = QMessageBox.question(
                self,
                "Üretim Kaydı Onayı",
                f"Aşağıdaki üretim kaydedilecek:\n\n"
                f"İş Emri: {data['is_emri_no']}\n"
                f"Stok: {data['stok_kodu']}\n"
                f"Üretilen Adet: {uretilen_adet:,.0f}\n"
                f"Bara: {bara:.2f}\n"
                f"Kalite: {kalite}\n"
                f"Vardiya: {vardiya_adi}\n"
                f"Operatör: {operator_adi}\n\n"
                f"Mevcut üretilen: {mevcut_uretilen:,.0f}\n"
                f"Yeni toplam: {yeni_uretilen:,.0f} / {toplam_miktar:,.0f}\n\n"
                f"Onaylıyor musunuz?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                conn.close()
                return
            
            # Eğer toplam tamamlandıysa durum değiştir
            if yeni_uretilen >= toplam_miktar:
                yeni_durum = 'KALITE_BEKLIYOR'
            else:
                yeni_durum = 'URETIMDE'
            
            # İş emrini güncelle
            cursor.execute("""
                UPDATE siparis.is_emirleri 
                SET durum = ?,
                    uretilen_miktar = ?,
                    giren_bara = ISNULL(giren_bara, 0) + ?,
                    guncelleme_tarihi = GETDATE()
                WHERE id = ?
            """, (yeni_durum, yeni_uretilen, int(bara + 0.5), is_emri_id))  # bara yuvarla
            
            # bara_takip tablosuna kayıt ekle - sıradaki bara_no'yu bul
            hat_id = container.property("hat_id")
            
            cursor.execute("""
                SELECT ISNULL(MAX(bara_no), 0) + 1 
                FROM uretim.bara_takip 
                WHERE is_emri_id = ?
            """, (is_emri_id,))
            next_bara_no = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO uretim.bara_takip (
                    is_emri_id, bara_no, aski_miktar, bara_miktar, 
                    giris_zamani, durum, hat_id, olusturma_tarihi
                ) VALUES (?, ?, ?, ?, GETDATE(), ?, ?, GETDATE())
            """, (is_emri_id, next_bara_no, data['aski_miktar'], uretilen_adet, kalite, hat_id))
            
            # 🆕 FAZ 2: Bitiş zamanını hesapla
            from datetime import datetime
            bitis_zamani = datetime.now()
            
            # Başlama zamanı yoksa şimdi kullan (fallback)
            if not self.baslama_zamani:
                self.baslama_zamani = bitis_zamani
                print("⚠️ Başlama zamanı bulunamadı, bitiş zamanı kullanıldı")
            
            # Süreyi hesapla
            sure_sn = (bitis_zamani - self.baslama_zamani).total_seconds()
            sure_dk = sure_sn / 60
            
            print(f"✓ Süre hesaplandı: {sure_dk:.1f} dakika")
            
            # 🆕 FAZ 1A + 2: Üretim kaydı oluştur
            try:
                cursor.execute("""
                    INSERT INTO uretim.uretim_kayitlari (
                        uuid,
                        is_emri_id,
                        hat_id,
                        vardiya_id,
                        tarih,
                        baslama_zamani,
                        bitis_zamani,
                        operator_id,
                        uretilen_miktar,
                        fire_miktar,
                        aski_sayisi,
                        durum,
                        olusturan_id
                    ) VALUES (
                        NEWID(),
                        ?,  -- is_emri_id
                        ?,  -- hat_id
                        ?,  -- vardiya_id
                        CAST(? AS DATE),  -- tarih
                        ?,  -- baslama_zamani (gerçek başlama)
                        ?,  -- bitis_zamani (gerçek bitiş)
                        ?,  -- operator_id
                        ?,  -- uretilen_miktar
                        0,  -- fire_miktar (FKK'da kontrol edilecek)
                        ?,  -- aski_sayisi (bara)
                        'TAMAMLANDI',  -- durum
                        NULL  -- olusturan_id (login sistemi eklenince)
                    )
                """, (
                    is_emri_id,
                    hat_id,
                    vardiya_id,
                    self.baslama_zamani,  # 🆕 Gerçek başlama
                    self.baslama_zamani,  # 🆕 Tarih için
                    bitis_zamani,          # 🆕 Gerçek bitiş
                    operator_id,
                    uretilen_adet,
                    int(bara + 0.5)  # Bara sayısı yuvarlanmış
                ))
                
                print(f"✓ Üretim kaydı oluşturuldu:")
                print(f"  - Vardiya: {vardiya_id}")
                print(f"  - Operatör: {operator_id}")
                print(f"  - Başlama: {self.baslama_zamani.strftime('%H:%M:%S')}")
                print(f"  - Bitiş: {bitis_zamani.strftime('%H:%M:%S')}")
                print(f"  - Süre: {sure_dk:.1f} dakika")
                
            except Exception as e:
                print(f"⚠️ Üretim kaydı hatası: {e}")
                import traceback
                traceback.print_exc()
                # Hata olsa da devam et (bara_takip ve is_emirleri zaten kaydedildi)
            
            # 🆕 FAZ 3: HareketMotoru ile stok transfer
            if lot_no:
                try:
                    from core.hareket_motoru import HareketMotoru
                    
                    motor = HareketMotoru(conn)
                    
                    # FKK deposunu bul (akış şemasından)
                    fkk_id = motor.get_depo_by_tip('FKK')
                    if not fkk_id:
                        print("⚠️ FKK deposu bulunamadı, kod ile bulunuyor")
                        cursor.execute("SELECT id FROM tanim.depolar WHERE kod = 'FKK'")
                        fkk = cursor.fetchone()
                        fkk_id = fkk[0] if fkk else 10
                    
                    # DÜZELTME: Sadece üretilen lot'u transfer et, tüm prefix'i değil!
                    # Lot bazında bakiye bul (SADECE bu lot!)
                    cursor.execute("""
                        SELECT id, miktar, depo_id, urun_id, lot_no
                        FROM stok.stok_bakiye 
                        WHERE lot_no = ?
                          AND depo_id != ?
                          AND miktar > 0
                        ORDER BY id
                    """, (lot_no, fkk_id))
                    
                    bakiye = cursor.fetchone()
                    
                    if not bakiye:
                        print(f"⚠️ Transfer yapılamadı: {lot_no} FKK dışında bulunamadı")
                    else:
                        bakiye_id = bakiye[0]
                        bakiye_miktar = float(bakiye[1] or 0)
                        bakiye_lot_no = bakiye[4]
                        kaynak_depo_id = bakiye[2]
                        
                        print(f"📦 Transfer hazırlanıyor:")
                        print(f"   Lot: {bakiye_lot_no}")
                        print(f"   Kaynak Depo ID: {kaynak_depo_id}")
                        print(f"   Hedef Depo ID: {fkk_id} (FKK)")
                        print(f"   Miktar: {uretilen_adet}")
                        
                        transfer_miktar = min(bakiye_miktar, uretilen_adet)
                        
                        # HareketMotoru ile transfer
                        # DÜZELTME: FKK'ya giderken kalite_durumu = 'KONTROL_BEKLIYOR' olmalı
                        sonuc = motor.transfer(
                            lot_no=bakiye_lot_no,
                            hedef_depo_id=fkk_id,
                            miktar=transfer_miktar,
                            kaynak="URETIM",
                            kaynak_id=data['id'],
                            aciklama=f"Üretim çıkışı - İş Emri: {data['is_emri_no']}",
                            kalite_durumu='KONTROL_BEKLIYOR',  # ← FKK'da kontrol bekleyecek
                            durum_kodu='FKK_BEKLIYOR'  # ← FKK deposunda
                        )
                        
                        if sonuc.basarili:
                            print(f"✅ Transfer başarılı: {bakiye_lot_no} → FKK ({transfer_miktar} adet)")
                        else:
                            print(f"❌ Transfer hatası: {sonuc.hata}")
                    
                except Exception as e:
                    print(f"⚠️ HareketMotoru hatası: {e}")
                    import traceback
                    traceback.print_exc()
                    # Hata olsa da devam et
            
            conn.commit()
            LogManager.log_insert('uretim', 'uretim.uretim_kayitlari', is_emri_id,
                                  f'Uretim girisi: Is Emri #{data.get("is_emri_no", "")}, {uretilen_adet} adet, Lot: {lot_no or "-"}')
            conn.close()

            # Formu temizle
            if vardiya_combo:
                vardiya_combo.setCurrentIndex(0)  # "-- Vardiya Seçin --"
            if operator_combo:
                operator_combo.setCurrentIndex(0)  # "-- Operatör Seçin --"
            if adet_spin:
                adet_spin.setValue(0)
            if aciklama_input:
                aciklama_input.clear()
            
            bara_label = container.findChild(QLabel, "bara_label")
            if bara_label:
                bara_label.setText("0")
            
            self.selected_row_data = None
            
            # Kaydet butonunu deaktif et
            save_btn = container.findChild(QPushButton, "save_btn")
            if save_btn:
                save_btn.setEnabled(False)
            
            # Seçim etiketini sıfırla
            selection_label = container.findChild(QLabel, "selection_label")
            if selection_label:
                selection_label.setText("⚠️ Seçim: Lütfen yukarıdan bir iş emri seçin")
                selection_label.setStyleSheet(f"""
                    font-size: 13px; 
                    font-weight: 600; 
                    color: {self.s['warning']};
                    padding: 8px;
                    background: rgba(245, 158, 11, 0.1);
                    border: 1px solid {self.s['warning']};
                    border-radius: 6px;
                """)
            
            detail_label = container.findChild(QLabel, "detail_label")
            if detail_label:
                detail_label.setText("Bakiye: - | Üretilen: - | Kalan: - | Parça/Bara: - | Kalan Bara: -")
            
            # Listeyi yenile
            self._load_is_emirleri(self.tab_widget.currentIndex())
            
            # Bilgi mesajı
            # 🆕 FAZ 2: Süreyi formatla
            sure_saat = int(sure_dk // 60)
            sure_kalan_dk = int(sure_dk % 60)
            if sure_saat > 0:
                sure_str = f"{sure_saat} saat {sure_kalan_dk} dakika"
            else:
                sure_str = f"{sure_kalan_dk} dakika"
            
            if yeni_durum == 'KALITE_BEKLIYOR':
                QMessageBox.information(
                    self,
                    "✅ Üretim Tamamlandı",
                    f"Üretim tamamlandı!\n\n"
                    f"Toplam üretilen: {yeni_uretilen:,.0f} adet\n"
                    f"Vardiya: {vardiya_adi}\n"
                    f"Operatör: {operator_adi}\n"
                    f"⏱️ Süre: {sure_str}\n\n"
                    f"İş emri kalite kontrole gönderildi."
                )
            else:
                kalan = toplam_miktar - yeni_uretilen
                QMessageBox.information(
                    self,
                    "📦 Kısmi Giriş Kaydedildi",
                    f"Üretim kaydedildi!\n\n"
                    f"Bu giriş: {uretilen_adet:,.0f} adet ({bara:.2f} bara)\n"
                    f"Toplam üretilen: {yeni_uretilen:,.0f} / {toplam_miktar:,.0f}\n"
                    f"Kalan: {kalan:,.0f} adet\n\n"
                    f"Vardiya: {vardiya_adi}\n"
                    f"Operatör: {operator_adi}\n"
                    f"⏱️ Süre: {sure_str}"
                )
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")
            import traceback
            traceback.print_exc()
