# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Verimlilik Analizi Modülü
[MODERNIZED UI - v3.0]

Banyo grupları verimlilik, bara takip ve reçete sapma analizi
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QPushButton, QFrame, QTabWidget, QHeaderView,
    QMessageBox, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QBrush
from datetime import datetime, timedelta
from core.database import get_db_connection, get_plc_connection


def get_modern_style(theme: dict = None) -> dict:
    """Modern tema renkleri - TÜM MODÜLLERDE AYNI"""
    if theme is None:
        theme = {}
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


class VerimlilikAnalizPage(QWidget):
    """Verimlilik Analizi Sayfası"""
    
    def __init__(self, page_id=None, theme: dict = None):
        super().__init__()
        self.page_id = page_id
        self.plc_conn = None
        self.erp_conn = None
        self.pozisyon_tanimlari = {}
        
        # Modern stil sistemi
        self.s = get_modern_style(theme)
        
        # Tema değişkenleri (eski kod uyumluluğu için)
        self.bg = self.s['card_bg']
        self.bg_card = self.s['card_bg']
        self.bg_input = self.s['input_bg']
        self.primary = self.s['primary']
        self.success = self.s['success']
        self.warning = self.s['warning']
        self.error = self.s['error']
        self.text = self.s['text']
        self.text_muted = self.s['text_muted']
        self.border = self.s['border']
        
        # Banyo grupları tanımı
        self.BANYO_GRUPLARI = {
            'AYA': ([14, 15], 2, 'ORTAK'),
            'SYA': ([5, 6, 7, 8], 4, 'ORTAK'),
            'FIRIN': ([114, 115, 116, 117], 4, 'KTL'),
            'YUKLEME_KTL': ([131, 132, 133, 134, 135, 136, 137, 138, 139, 140], 10, 'KTL'),
            'ALKALI_CINKO': ([210, 211, 212, 213, 214], 5, 'CINKO'),
            'KURUTMA': ([235, 237], 2, 'CINKO'),
            'YUKLEME_CINKO': ([238, 239, 240, 241, 242, 243, 244, 245, 246, 247], 10, 'CINKO'),
        }
        
        # Tank -> Grup eşleştirmesi
        self.tank_grup = {}
        for grup_adi, (tanklar, adet, hat) in self.BANYO_GRUPLARI.items():
            for tank in tanklar:
                self.tank_grup[tank] = (grup_adi, adet, hat)
        
        self._init_ui()
        self._load_pozisyon_tanimlari()
    
    def _init_ui(self):
        """Arayüzü oluştur"""
        self.setStyleSheet(f"background:{self.bg}; color:{self.text};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Başlık
        header = QHBoxLayout()
        title = QLabel("📊 Verimlilik Analizi")
        title.setStyleSheet(f"font-size:24px;font-weight:bold;color:{self.text};")
        header.addWidget(title)
        header.addStretch()
        
        # Yenile butonu
        btn_refresh = QPushButton("🔄 Yenile")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background:{self.primary};color:white;border:none;
                border-radius:8px;padding:10px 20px;font-weight:bold;font-size:14px;
            }}
            QPushButton:hover {{background:#3651d4;}}
        """)
        btn_refresh.clicked.connect(self._refresh_all)
        header.addWidget(btn_refresh)
        layout.addLayout(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {self.border};border-radius:8px;background:{self.bg_card};}}
            QTabBar::tab {{
                background:{self.bg_input};color:{self.text_muted};
                padding:12px 24px;margin-right:4px;border-top-left-radius:8px;border-top-right-radius:8px;
                font-weight:bold;
            }}
            QTabBar::tab:selected {{background:{self.primary};color:white;}}
            QTabBar::tab:hover:!selected {{background:{self.border};}}
        """)
        
        # Tab 1: Grup Verimlilik
        self._create_grup_verimlilik_tab()
        
        # Tab 2: Bara Takip
        self._create_bara_takip_tab()
        
        # Tab 3: Reçete Sapma
        self._create_recete_sapma_tab()
        
        layout.addWidget(self.tabs)
    
    def _create_grup_verimlilik_tab(self):
        """Tab 1: Grup Verimlilik"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 15, 10, 10)
        
        # Filtreler
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Dönem:", styleSheet=f"color:{self.text};font-weight:bold;"))
        self.cmb_grup_tarih = QComboBox()
        self.cmb_grup_tarih.setStyleSheet(self._combo_style())
        self.cmb_grup_tarih.addItem("Bugün (Vardiya)", "bugun")
        self.cmb_grup_tarih.addItem("Dün", "dun")
        self.cmb_grup_tarih.addItem("Son 7 Gün", "hafta")
        filter_layout.addWidget(self.cmb_grup_tarih)
        
        filter_layout.addWidget(QLabel("Hat:", styleSheet=f"color:{self.text};font-weight:bold;margin-left:15px;"))
        self.cmb_grup_hat = QComboBox()
        self.cmb_grup_hat.setStyleSheet(self._combo_style())
        self.cmb_grup_hat.addItem("Tüm Hatlar", None)
        self.cmb_grup_hat.addItem("KTL", "KTL")
        self.cmb_grup_hat.addItem("CINKO", "CINKO")
        self.cmb_grup_hat.addItem("ORTAK", "ORTAK")
        filter_layout.addWidget(self.cmb_grup_hat)
        
        btn_hesapla = QPushButton("📊 Hesapla")
        btn_hesapla.setStyleSheet(f"QPushButton{{background:{self.success};color:white;border:none;border-radius:6px;padding:10px 20px;font-weight:bold;}}")
        btn_hesapla.clicked.connect(self._load_grup_verimlilik)
        filter_layout.addWidget(btn_hesapla)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Özet kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.card_toplam_kapasite = self._create_card("📦 TOPLAM KAPASİTE", "0 dk", self.primary)
        self.card_toplam_kullanim = self._create_card("⚡ TOPLAM KULLANIM", "0 dk", self.success)
        self.card_ort_verimlilik = self._create_card("📊 ORT. VERİMLİLİK", "%0", self.warning)
        self.card_kritik_grup = self._create_card("🚨 KRİTİK GRUP", "-", self.error)
        
        cards_layout.addWidget(self.card_toplam_kapasite)
        cards_layout.addWidget(self.card_toplam_kullanim)
        cards_layout.addWidget(self.card_ort_verimlilik)
        cards_layout.addWidget(self.card_kritik_grup)
        layout.addLayout(cards_layout)
        
        # Tablo
        self.tbl_grup_verimlilik = QTableWidget()
        self.tbl_grup_verimlilik.setColumnCount(11)
        self.tbl_grup_verimlilik.setHorizontalHeaderLabels([
            "Grup Adı", "Hat", "Pozisyonlar", "Banyo Adet", "Toplam İşlem",
            "Ort. Reçete (dk)", "Kapasite (dk)", "Kullanım (dk)", "Dar Boğaz (dk)", "Verimlilik %", "Durum"
        ])
        self._style_table(self.tbl_grup_verimlilik)
        layout.addWidget(self.tbl_grup_verimlilik)
        
        self.tabs.addTab(tab, "📊 Grup Verimlilik")
    
    def _create_bara_takip_tab(self):
        """Tab 2: Bara Takip"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 15, 10, 10)
        
        # Filtreler
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Dönem:", styleSheet=f"color:{self.text};font-weight:bold;"))
        self.cmb_bara_tarih = QComboBox()
        self.cmb_bara_tarih.setStyleSheet(self._combo_style())
        self.cmb_bara_tarih.addItem("Bugün (Vardiya)", "bugun")
        self.cmb_bara_tarih.addItem("Dün", "dun")
        self.cmb_bara_tarih.addItem("Son 2 Saat", "2saat")
        filter_layout.addWidget(self.cmb_bara_tarih)
        
        filter_layout.addWidget(QLabel("Hat:", styleSheet=f"color:{self.text};font-weight:bold;margin-left:15px;"))
        self.cmb_bara_hat = QComboBox()
        self.cmb_bara_hat.setStyleSheet(self._combo_style())
        self.cmb_bara_hat.addItem("KTL (118→101)", "KTL")
        self.cmb_bara_hat.addItem("CINKO (236→201)", "CINKO")
        filter_layout.addWidget(self.cmb_bara_hat)
        
        btn_ara = QPushButton("🔍 Ara")
        btn_ara.setStyleSheet(f"QPushButton{{background:{self.success};color:white;border:none;border-radius:6px;padding:10px 20px;font-weight:bold;}}")
        btn_ara.clicked.connect(self._load_bara_takip)
        filter_layout.addWidget(btn_ara)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Splitter - üst bara listesi, alt detay
        splitter = QSplitter(Qt.Vertical)
        
        # Üst: Bara listesi
        bara_group = QGroupBox("🏭 Bara Listesi")
        bara_group.setStyleSheet(f"QGroupBox{{color:{self.text};font-weight:bold;border:1px solid {self.border};border-radius:8px;padding-top:15px;}}")
        bara_layout = QVBoxLayout(bara_group)
        
        self.tbl_bara_listesi = QTableWidget()
        self.tbl_bara_listesi.setColumnCount(8)
        self.tbl_bara_listesi.setHorizontalHeaderLabels([
            "Bara No", "Reçete", "Reçete Adı", "Giriş Saati", "Çıkış Saati",
            "Toplam Süre (dk)", "Beklenen (dk)", "Sapma (dk)"
        ])
        self._style_table(self.tbl_bara_listesi)
        self.tbl_bara_listesi.itemSelectionChanged.connect(self._on_bara_selected)
        bara_layout.addWidget(self.tbl_bara_listesi)
        splitter.addWidget(bara_group)
        
        # Alt: Bara detay
        detay_group = QGroupBox("📋 Bara Detay (Pozisyon Geçişleri)")
        detay_group.setStyleSheet(f"QGroupBox{{color:{self.text};font-weight:bold;border:1px solid {self.border};border-radius:8px;padding-top:15px;}}")
        detay_layout = QVBoxLayout(detay_group)
        
        self.tbl_bara_detay = QTableWidget()
        self.tbl_bara_detay.setColumnCount(7)
        self.tbl_bara_detay.setHorizontalHeaderLabels([
            "Sıra", "Pozisyon No", "Pozisyon Adı", "Giriş Saati",
            "Kalış Süresi (sn)", "Reçete Süresi (sn)", "Sapma"
        ])
        self._style_table(self.tbl_bara_detay)
        detay_layout.addWidget(self.tbl_bara_detay)
        splitter.addWidget(detay_group)
        
        splitter.setSizes([300, 200])
        layout.addWidget(splitter)
        
        self.tabs.addTab(tab, "🏭 Bara Takip")
    
    def _create_recete_sapma_tab(self):
        """Tab 3: Reçete Sapma Analizi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 15, 10, 10)
        
        # Filtreler
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Dönem:", styleSheet=f"color:{self.text};font-weight:bold;"))
        self.cmb_sapma_tarih = QComboBox()
        self.cmb_sapma_tarih.setStyleSheet(self._combo_style())
        self.cmb_sapma_tarih.addItem("Bugün (Vardiya)", "bugun")
        self.cmb_sapma_tarih.addItem("Dün", "dun")
        self.cmb_sapma_tarih.addItem("Son 7 Gün", "hafta")
        filter_layout.addWidget(self.cmb_sapma_tarih)
        
        filter_layout.addWidget(QLabel("Sapma Tipi:", styleSheet=f"color:{self.text};font-weight:bold;margin-left:15px;"))
        self.cmb_sapma_tipi = QComboBox()
        self.cmb_sapma_tipi.setStyleSheet(self._combo_style())
        self.cmb_sapma_tipi.addItem("Tümü", None)
        self.cmb_sapma_tipi.addItem("Sadece Gecikmeler (+)", "pozitif")
        self.cmb_sapma_tipi.addItem("Sadece Hızlılar (-)", "negatif")
        filter_layout.addWidget(self.cmb_sapma_tipi)
        
        btn_analiz = QPushButton("📈 Analiz Et")
        btn_analiz.setStyleSheet(f"QPushButton{{background:{self.success};color:white;border:none;border-radius:6px;padding:10px 20px;font-weight:bold;}}")
        btn_analiz.clicked.connect(self._load_recete_sapma)
        filter_layout.addWidget(btn_analiz)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Özet kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.card_toplam_sapma = self._create_card("⏱️ TOPLAM SAPMA", "0 dk", self.warning)
        self.card_ort_sapma = self._create_card("📊 ORT. SAPMA", "0 sn", self.primary)
        self.card_en_cok_geciken = self._create_card("🔴 EN ÇOK GECİKEN", "-", self.error)
        self.card_en_hizli = self._create_card("🟢 EN HIZLI", "-", self.success)
        
        cards_layout.addWidget(self.card_toplam_sapma)
        cards_layout.addWidget(self.card_ort_sapma)
        cards_layout.addWidget(self.card_en_cok_geciken)
        cards_layout.addWidget(self.card_en_hizli)
        layout.addLayout(cards_layout)
        
        # Tablo
        self.tbl_recete_sapma = QTableWidget()
        self.tbl_recete_sapma.setColumnCount(9)
        self.tbl_recete_sapma.setHorizontalHeaderLabels([
            "Pozisyon No", "Pozisyon Adı", "Reçete", "İşlem Sayısı",
            "Ort. Reçete (sn)", "Ort. Gerçek (sn)", "Ort. Sapma (sn)", "Sapma %", "Durum"
        ])
        self._style_table(self.tbl_recete_sapma)
        layout.addWidget(self.tbl_recete_sapma)
        
        self.tabs.addTab(tab, "📈 Reçete Sapma")
    
    def _create_card(self, title, value, color):
        """Özet kartı oluştur"""
        card = QFrame()
        card.setFixedHeight(90)
        card.setMinimumWidth(200)
        card.setStyleSheet(f"QFrame{{background:{self.bg_card};border-radius:10px;border-left:4px solid {color};}}")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(5)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color:{self.text_muted};font-size:11px;font-weight:bold;")
        layout.addWidget(lbl_title)
        
        lbl_value = QLabel(value)
        lbl_value.setObjectName("val")
        lbl_value.setStyleSheet(f"color:{color};font-size:22px;font-weight:bold;")
        layout.addWidget(lbl_value)
        
        return card
    
    def _combo_style(self):
        return f"QComboBox{{background:{self.bg_input};color:{self.text};border:1px solid {self.border};border-radius:6px;padding:8px 12px;min-width:140px;}}"
    
    def _style_table(self, table):
        """Tablo stilini uygula"""
        table.setStyleSheet(f"""
            QTableWidget {{
                background:{self.bg_card};
                color:{self.text};
                border:1px solid {self.border};
                border-radius:8px;
                gridline-color:{self.border};
            }}
            QTableWidget::item {{padding:8px;}}
            QTableWidget::item:selected {{background:{self.primary};}}
            QHeaderView::section {{
                background:{self.bg_input};
                color:{self.text};
                padding:10px;
                border:none;
                border-bottom:2px solid {self.primary};
                font-weight:bold;
            }}
        """)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setDefaultSectionSize(40)
    
    def _load_pozisyon_tanimlari(self):
        """ERP'den pozisyon tanımlarını yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.pozisyon_no,
                    p.ad,
                    h.kod as hat_kodu,
                    h.ad as hat_adi
                FROM tanim.hat_pozisyonlar p
                JOIN tanim.uretim_hatlari h ON p.hat_id = h.id
                WHERE p.aktif_mi = 1 AND p.silindi_mi = 0 AND h.aktif_mi = 1 AND h.silindi_mi = 0
            """)
            for row in cursor.fetchall():
                self.pozisyon_tanimlari[row[0]] = {
                    'pozisyon_adi': row[1], 
                    'hat_kodu': row[2],
                    'hat_adi': row[3]
                }
            conn.close()
        except Exception as e:
            print(f"Pozisyon tanımları yüklenemedi: {e}")
    
    def _get_tarih_aralik(self, tarih_secim):
        """Tarih aralığını hesapla"""
        now = datetime.now()
        
        if tarih_secim == "bugun":
            if now.hour < 7 or (now.hour == 7 and now.minute < 30):
                baslangic = now.replace(hour=7, minute=30, second=0, microsecond=0) - timedelta(days=1)
            else:
                baslangic = now.replace(hour=7, minute=30, second=0, microsecond=0)
            bitis = now
        elif tarih_secim == "dun":
            dun = now - timedelta(days=1)
            baslangic = dun.replace(hour=7, minute=30, second=0, microsecond=0)
            bitis = baslangic + timedelta(days=1)
        elif tarih_secim == "2saat":
            baslangic = now - timedelta(hours=2)
            bitis = now
        else:  # hafta
            baslangic = now - timedelta(days=7)
            bitis = now
        
        return baslangic, bitis
    
    def _refresh_all(self):
        """Tüm verileri yenile"""
        current_tab = self.tabs.currentIndex()
        if current_tab == 0:
            self._load_grup_verimlilik()
        elif current_tab == 1:
            self._load_bara_takip()
        elif current_tab == 2:
            self._load_recete_sapma()
    
    def _load_grup_verimlilik(self):
        """Grup bazlı verimlilik analizi"""
        if not self.plc_conn:
            try:
                self.plc_conn = get_plc_connection()
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"PLC bağlantısı kurulamadı: {e}")
                return
        
        tarih_secim = self.cmb_grup_tarih.currentData()
        hat_secim = self.cmb_grup_hat.currentData()
        baslangic, bitis = self._get_tarih_aralik(tarih_secim)
        vardiya_sure = (bitis - baslangic).total_seconds() / 60
        
        try:
            cursor = self.plc_conn.cursor()
            
            # Her pozisyon-reçete için veri çek
            cursor.execute("""
                SELECT 
                    d.KznNo,
                    d.ReceteNo,
                    COUNT(*) as islem_sayisi,
                    DATEDIFF(MINUTE, MIN(d.TarihDoldurma), MAX(d.TarihDoldurma)) as aktif_sure_dk,
                    ISNULL(ra.Zamanlar, 0) as zamanlar_sn,
                    ISNULL(ra.Suzulme_Zamanlari, 0) as suzulme_sn
                FROM dbo.data d
                LEFT JOIN ReceteAdimlar ra ON ra.Panel_Recete_No = d.ReceteNo AND ra.Kazan_No = d.KznNo
                WHERE d.TarihDoldurma >= ? AND d.TarihDoldurma <= ?
                GROUP BY d.KznNo, d.ReceteNo, ra.Zamanlar, ra.Suzulme_Zamanlari
                HAVING COUNT(*) > 1
            """, (baslangic, bitis))
            rows = cursor.fetchall()
            
            # Grup bazlı toplama
            grup_data = {}
            
            for row in rows:
                kzn_no, recete_no, islem_sayisi, aktif_sure, zamanlar_sn, suzulme_sn = row
                
                aktif_sure = float(aktif_sure) if aktif_sure else 0
                zamanlar_sn = float(zamanlar_sn) if zamanlar_sn else 0
                suzulme_sn = float(suzulme_sn) if suzulme_sn else 0
                
                recete_sure_dk = (zamanlar_sn + suzulme_sn) / 60
                if recete_sure_dk == 0 and islem_sayisi > 1 and aktif_sure > 0:
                    recete_sure_dk = aktif_sure / (islem_sayisi - 1)
                
                beklenen = recete_sure_dk * islem_sayisi
                
                # Grup belirleme
                if kzn_no in self.tank_grup:
                    grup_adi, grup_adet, grup_hat = self.tank_grup[kzn_no]
                else:
                    # Pozisyon adını ERP tanımından al
                    tanim = self.pozisyon_tanimlari.get(kzn_no, {})
                    poz_adi = tanim.get('pozisyon_adi', f'Tanımsız ({kzn_no})')
                    grup_adi = f"POZ_{kzn_no}"  # İç kullanım için
                    grup_adet = 1
                    if 101 <= kzn_no <= 143:
                        grup_hat = "KTL"
                    elif 201 <= kzn_no <= 247:
                        grup_hat = "CINKO"
                    else:
                        grup_hat = "ORTAK"
                
                # Hat filtresi
                if hat_secim and grup_hat != hat_secim:
                    continue
                
                if grup_adi not in grup_data:
                    grup_data[grup_adi] = {
                        'pozisyonlar': set(),
                        'grup_adet': grup_adet,
                        'hat': grup_hat,
                        'toplam_islem': 0,
                        'toplam_beklenen': 0,
                        'aktif_sure': 0,
                        'recete_sureler': []
                    }
                
                grup_data[grup_adi]['pozisyonlar'].add(kzn_no)
                grup_data[grup_adi]['toplam_islem'] += islem_sayisi
                grup_data[grup_adi]['toplam_beklenen'] += beklenen
                if recete_sure_dk > 0:
                    grup_data[grup_adi]['recete_sureler'].append(recete_sure_dk)
                if aktif_sure > grup_data[grup_adi]['aktif_sure']:
                    grup_data[grup_adi]['aktif_sure'] = aktif_sure
            
            # Verimlilik hesapla ve tabloya aktar
            verimlilik_data = []
            toplam_kapasite = 0
            toplam_kullanim = 0
            
            for grup_adi, data in grup_data.items():
                aktif_sure = data['aktif_sure']
                if aktif_sure <= 0:
                    continue
                
                grup_adet = data['grup_adet']
                kapasite = grup_adet * aktif_sure
                kullanim = data['toplam_beklenen']
                
                # Verimlilik - %100'ü aşabilir (dar boğaz göstergesi)
                verimlilik_gercek = (kullanim / kapasite * 100) if kapasite > 0 else 0
                verimlilik = verimlilik_gercek  # Sınırlama yok
                
                # Kapasite aşımı (dar boğaz)
                kapasite_asimi = max(0, kullanim - kapasite)
                
                ort_recete = sum(data['recete_sureler']) / len(data['recete_sureler']) if data['recete_sureler'] else 0
                
                toplam_kapasite += kapasite
                toplam_kullanim += kullanim
                
                # Grup adını belirle
                if grup_adi.startswith('POZ_'):
                    poz_no = int(grup_adi.split('_')[1])
                    tanim = self.pozisyon_tanimlari.get(poz_no, {})
                    gosterilecek_ad = tanim.get('pozisyon_adi', f'Tanımsız ({poz_no})')
                else:
                    gosterilecek_ad = grup_adi.replace('_', ' ')
                
                verimlilik_data.append({
                    'grup_adi': gosterilecek_ad,
                    'hat': data['hat'],
                    'pozisyonlar': sorted(data['pozisyonlar']),
                    'grup_adet': grup_adet,
                    'toplam_islem': data['toplam_islem'],
                    'ort_recete': ort_recete,
                    'kapasite': kapasite,
                    'kullanim': kullanim,
                    'verimlilik': verimlilik,
                    'kapasite_asimi': kapasite_asimi
                })
            
            # Sıralama: Önce kapasite aşımı olanlar (dar boğaz), sonra düşük verimlilikler
            verimlilik_data.sort(key=lambda x: (-x['kapasite_asimi'], x['verimlilik']))
            
            # Kartları güncelle
            self.card_toplam_kapasite.findChild(QLabel, "val").setText(f"{toplam_kapasite:.0f} dk")
            self.card_toplam_kullanim.findChild(QLabel, "val").setText(f"{toplam_kullanim:.0f} dk")
            
            ort_verimlilik = (toplam_kullanim / toplam_kapasite * 100) if toplam_kapasite > 0 else 0
            self.card_ort_verimlilik.findChild(QLabel, "val").setText(f"%{ort_verimlilik:.1f}")
            
            if verimlilik_data:
                # Dar boğaz olanı veya en düşük verimliliği göster
                kritik = verimlilik_data[0]
                if kritik['kapasite_asimi'] > 0:
                    self.card_kritik_grup.findChild(QLabel, "val").setText(f"⚠️ {kritik['grup_adi'][:12]}")
                else:
                    self.card_kritik_grup.findChild(QLabel, "val").setText(kritik['grup_adi'][:15])
            
            # Tabloya aktar
            self.tbl_grup_verimlilik.setRowCount(len(verimlilik_data))
            
            for i, data in enumerate(verimlilik_data):
                self.tbl_grup_verimlilik.setItem(i, 0, QTableWidgetItem(data['grup_adi']))
                self.tbl_grup_verimlilik.setItem(i, 1, QTableWidgetItem(data['hat']))
                
                poz_str = ','.join(str(p) for p in data['pozisyonlar'][:4])
                if len(data['pozisyonlar']) > 4:
                    poz_str += '...'
                self.tbl_grup_verimlilik.setItem(i, 2, QTableWidgetItem(poz_str))
                
                self.tbl_grup_verimlilik.setItem(i, 3, QTableWidgetItem(str(data['grup_adet'])))
                self.tbl_grup_verimlilik.setItem(i, 4, QTableWidgetItem(f"{data['toplam_islem']:,}"))
                self.tbl_grup_verimlilik.setItem(i, 5, QTableWidgetItem(f"{data['ort_recete']:.1f}"))
                self.tbl_grup_verimlilik.setItem(i, 6, QTableWidgetItem(f"{data['kapasite']:.0f}"))
                self.tbl_grup_verimlilik.setItem(i, 7, QTableWidgetItem(f"{data['kullanim']:.0f}"))
                
                # Dar Boğaz (kapasite aşımı) - renklendirme
                darbogaz_item = QTableWidgetItem(f"{data['kapasite_asimi']:.0f}")
                if data['kapasite_asimi'] > 0:
                    darbogaz_item.setForeground(QBrush(QColor(self.error)))
                    darbogaz_item.setFont(QFont("", -1, QFont.Bold))
                else:
                    darbogaz_item.setForeground(QBrush(QColor(self.text_muted)))
                self.tbl_grup_verimlilik.setItem(i, 8, darbogaz_item)
                
                # Verimlilik renklendirme
                verim_item = QTableWidgetItem(f"%{data['verimlilik']:.1f}")
                if data['verimlilik'] > 100:
                    # Kapasite aşımı - dar boğaz!
                    verim_item.setForeground(QBrush(QColor(self.error)))
                    verim_item.setFont(QFont("", -1, QFont.Bold))
                elif data['verimlilik'] >= 70:
                    verim_item.setForeground(QBrush(QColor(self.success)))
                elif data['verimlilik'] >= 50:
                    verim_item.setForeground(QBrush(QColor(self.warning)))
                else:
                    verim_item.setForeground(QBrush(QColor(self.error)))
                self.tbl_grup_verimlilik.setItem(i, 9, verim_item)
                
                # Durum
                if data['verimlilik'] > 100:
                    durum = "🔴 DAR BOĞAZ"
                elif data['verimlilik'] >= 70:
                    durum = "🟢 Verimli"
                elif data['verimlilik'] >= 50:
                    durum = "🟡 Orta"
                else:
                    durum = "⚪ Düşük"
                self.tbl_grup_verimlilik.setItem(i, 10, QTableWidgetItem(durum))
                
        except Exception as e:
            print(f"Grup verimlilik hatası: {e}")
            QMessageBox.warning(self, "Hata", f"Veri yüklenirken hata: {e}")
    
    def _load_bara_takip(self):
        """Bara takip verilerini yükle"""
        if not self.plc_conn:
            try:
                self.plc_conn = get_plc_connection()
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"PLC bağlantısı kurulamadı: {e}")
                return
        
        tarih_secim = self.cmb_bara_tarih.currentData()
        hat_secim = self.cmb_bara_hat.currentData()
        baslangic, bitis = self._get_tarih_aralik(tarih_secim)
        
        # Giriş/çıkış pozisyonları
        if hat_secim == "KTL":
            giris_poz, cikis_poz = 118, 101
        else:  # CINKO
            giris_poz, cikis_poz = 236, 201
        
        try:
            cursor = self.plc_conn.cursor()
            
            # Giriş ve çıkış yapan baraları bul
            cursor.execute("""
                WITH GirenBaralar AS (
                    SELECT BaraNo, ReceteNo, MIN(TarihDoldurma) as giris_zamani
                    FROM dbo.data
                    WHERE KznNo = ? AND TarihDoldurma >= ? AND TarihDoldurma <= ?
                    GROUP BY BaraNo, ReceteNo
                ),
                CikanBaralar AS (
                    SELECT BaraNo, ReceteNo, MAX(TarihDoldurma) as cikis_zamani
                    FROM dbo.data
                    WHERE KznNo = ? AND TarihDoldurma >= ? AND TarihDoldurma <= ?
                    GROUP BY BaraNo, ReceteNo
                )
                SELECT 
                    g.BaraNo,
                    g.ReceteNo,
                    r.ReceteAciklamasi,
                    g.giris_zamani,
                    c.cikis_zamani,
                    DATEDIFF(MINUTE, g.giris_zamani, c.cikis_zamani) as toplam_sure_dk
                FROM GirenBaralar g
                JOIN CikanBaralar c ON g.BaraNo = c.BaraNo AND g.ReceteNo = c.ReceteNo
                LEFT JOIN Receteler r ON r.ReceteNo = g.ReceteNo
                WHERE c.cikis_zamani > g.giris_zamani
                ORDER BY g.giris_zamani DESC
            """, (giris_poz, baslangic, bitis, cikis_poz, baslangic, bitis))
            
            rows = cursor.fetchall()
            
            # Reçete toplam sürelerini hesapla
            recete_sureleri = {}
            cursor.execute("""
                SELECT Panel_Recete_No, SUM(Zamanlar + Suzulme_Zamanlari) / 60.0 as toplam_dk
                FROM ReceteAdimlar
                GROUP BY Panel_Recete_No
            """)
            for row in cursor.fetchall():
                recete_sureleri[row[0]] = float(row[1]) if row[1] else 0
            
            # Tabloya aktar
            self.tbl_bara_listesi.setRowCount(len(rows))
            self.bara_data = []  # Detay için sakla
            
            for i, row in enumerate(rows):
                bara_no, recete_no, recete_adi, giris, cikis, toplam_dk = row
                
                beklenen = recete_sureleri.get(recete_no, 0)
                sapma = (toplam_dk - beklenen) if toplam_dk and beklenen else 0
                
                self.bara_data.append({
                    'bara_no': bara_no,
                    'recete_no': recete_no,
                    'giris': giris,
                    'cikis': cikis
                })
                
                self.tbl_bara_listesi.setItem(i, 0, QTableWidgetItem(str(bara_no)))
                self.tbl_bara_listesi.setItem(i, 1, QTableWidgetItem(str(recete_no)))
                self.tbl_bara_listesi.setItem(i, 2, QTableWidgetItem(recete_adi or "-"))
                self.tbl_bara_listesi.setItem(i, 3, QTableWidgetItem(giris.strftime("%H:%M:%S") if giris else "-"))
                self.tbl_bara_listesi.setItem(i, 4, QTableWidgetItem(cikis.strftime("%H:%M:%S") if cikis else "-"))
                self.tbl_bara_listesi.setItem(i, 5, QTableWidgetItem(f"{toplam_dk:.0f}" if toplam_dk else "-"))
                self.tbl_bara_listesi.setItem(i, 6, QTableWidgetItem(f"{beklenen:.0f}"))
                
                # Sapma renklendirme
                sapma_item = QTableWidgetItem(f"{sapma:+.0f}")
                if sapma > 10:
                    sapma_item.setForeground(QBrush(QColor(self.error)))
                elif sapma < -5:
                    sapma_item.setForeground(QBrush(QColor(self.success)))
                else:
                    sapma_item.setForeground(QBrush(QColor(self.warning)))
                self.tbl_bara_listesi.setItem(i, 7, sapma_item)
                
        except Exception as e:
            print(f"Bara takip hatası: {e}")
            QMessageBox.warning(self, "Hata", f"Veri yüklenirken hata: {e}")
    
    def _on_bara_selected(self):
        """Bara seçildiğinde detayları göster"""
        selected = self.tbl_bara_listesi.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        if row >= len(self.bara_data):
            return
        
        bara = self.bara_data[row]
        
        try:
            cursor = self.plc_conn.cursor()
            
            # Bara'nın tüm pozisyon geçişlerini al
            cursor.execute("""
                SELECT 
                    d.KznNo,
                    d.TarihDoldurma,
                    ISNULL(ra.Zamanlar, 0) + ISNULL(ra.Suzulme_Zamanlari, 0) as recete_sure_sn
                FROM dbo.data d
                LEFT JOIN ReceteAdimlar ra ON ra.Panel_Recete_No = d.ReceteNo AND ra.Kazan_No = d.KznNo
                WHERE d.BaraNo = ? AND d.ReceteNo = ?
                    AND d.TarihDoldurma >= ? AND d.TarihDoldurma <= ?
                ORDER BY d.TarihDoldurma
            """, (bara['bara_no'], bara['recete_no'], bara['giris'], bara['cikis']))
            
            rows = cursor.fetchall()
            
            self.tbl_bara_detay.setRowCount(len(rows))
            
            prev_time = None
            for i, row in enumerate(rows):
                kzn_no, tarih, recete_sure = row
                
                # Kalış süresi (bir önceki pozisyondan bu pozisyona)
                if prev_time:
                    kalis_sure = (tarih - prev_time).total_seconds()
                else:
                    kalis_sure = 0
                prev_time = tarih
                
                recete_sure = float(recete_sure) if recete_sure else 0
                sapma = kalis_sure - recete_sure if i > 0 else 0
                
                tanim = self.pozisyon_tanimlari.get(kzn_no, {})
                poz_adi = tanim.get('pozisyon_adi', f'Tanımsız ({kzn_no})')
                
                self.tbl_bara_detay.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.tbl_bara_detay.setItem(i, 1, QTableWidgetItem(str(kzn_no)))
                self.tbl_bara_detay.setItem(i, 2, QTableWidgetItem(poz_adi))
                self.tbl_bara_detay.setItem(i, 3, QTableWidgetItem(tarih.strftime("%H:%M:%S")))
                self.tbl_bara_detay.setItem(i, 4, QTableWidgetItem(f"{kalis_sure:.0f}" if i > 0 else "-"))
                self.tbl_bara_detay.setItem(i, 5, QTableWidgetItem(f"{recete_sure:.0f}" if recete_sure > 0 else "-"))
                
                # Sapma renklendirme
                if i > 0:
                    sapma_item = QTableWidgetItem(f"{sapma:+.0f}")
                    if sapma > 60:
                        sapma_item.setForeground(QBrush(QColor(self.error)))
                    elif sapma < -30:
                        sapma_item.setForeground(QBrush(QColor(self.success)))
                    else:
                        sapma_item.setForeground(QBrush(QColor(self.text_muted)))
                    self.tbl_bara_detay.setItem(i, 6, sapma_item)
                else:
                    self.tbl_bara_detay.setItem(i, 6, QTableWidgetItem("-"))
                    
        except Exception as e:
            print(f"Bara detay hatası: {e}")
    
    def _load_recete_sapma(self):
        """Reçete sapma analizi"""
        if not self.plc_conn:
            try:
                self.plc_conn = get_plc_connection()
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"PLC bağlantısı kurulamadı: {e}")
                return
        
        tarih_secim = self.cmb_sapma_tarih.currentData()
        sapma_tipi = self.cmb_sapma_tipi.currentData()
        baslangic, bitis = self._get_tarih_aralik(tarih_secim)
        
        try:
            cursor = self.plc_conn.cursor()
            
            # Ardışık pozisyonlar arasındaki süreleri hesapla
            cursor.execute("""
                WITH SiraliData AS (
                    SELECT 
                        BaraNo, ReceteNo, KznNo, TarihDoldurma,
                        ROW_NUMBER() OVER (PARTITION BY BaraNo, ReceteNo ORDER BY TarihDoldurma) as sira
                    FROM dbo.data
                    WHERE TarihDoldurma >= ? AND TarihDoldurma <= ?
                )
                SELECT 
                    d1.KznNo,
                    d1.ReceteNo,
                    COUNT(*) as islem_sayisi,
                    AVG(CAST(ISNULL(ra.Zamanlar, 0) + ISNULL(ra.Suzulme_Zamanlari, 0) AS FLOAT)) as ort_recete_sn,
                    AVG(CAST(DATEDIFF(SECOND, d1.TarihDoldurma, d2.TarihDoldurma) AS FLOAT)) as ort_gercek_sn
                FROM SiraliData d1
                JOIN SiraliData d2 ON d1.BaraNo = d2.BaraNo AND d1.ReceteNo = d2.ReceteNo AND d2.sira = d1.sira + 1
                LEFT JOIN ReceteAdimlar ra ON ra.Panel_Recete_No = d1.ReceteNo AND ra.Kazan_No = d1.KznNo
                GROUP BY d1.KznNo, d1.ReceteNo
                HAVING COUNT(*) >= 3
                ORDER BY d1.KznNo
            """, (baslangic, bitis))
            
            rows = cursor.fetchall()
            
            # Pozisyon bazlı toplama
            poz_sapma = {}
            
            for row in rows:
                kzn_no, recete_no, islem, ort_recete, ort_gercek = row
                
                ort_recete = float(ort_recete) if ort_recete else 0
                ort_gercek = float(ort_gercek) if ort_gercek else 0
                sapma = ort_gercek - ort_recete
                
                # Sapma filtresi
                if sapma_tipi == "pozitif" and sapma <= 0:
                    continue
                if sapma_tipi == "negatif" and sapma >= 0:
                    continue
                
                if kzn_no not in poz_sapma:
                    poz_sapma[kzn_no] = {
                        'receteler': [],
                        'toplam_islem': 0,
                        'toplam_recete': 0,
                        'toplam_gercek': 0
                    }
                
                poz_sapma[kzn_no]['receteler'].append(recete_no)
                poz_sapma[kzn_no]['toplam_islem'] += islem
                poz_sapma[kzn_no]['toplam_recete'] += ort_recete * islem
                poz_sapma[kzn_no]['toplam_gercek'] += ort_gercek * islem
            
            # Sapma hesapla
            sapma_data = []
            toplam_sapma = 0
            
            for kzn_no, data in poz_sapma.items():
                islem = data['toplam_islem']
                if islem == 0:
                    continue
                
                ort_recete = data['toplam_recete'] / islem
                ort_gercek = data['toplam_gercek'] / islem
                sapma = ort_gercek - ort_recete
                sapma_yuzde = (sapma / ort_recete * 100) if ort_recete > 0 else 0
                
                toplam_sapma += abs(sapma) * islem
                
                tanim = self.pozisyon_tanimlari.get(kzn_no, {})
                
                sapma_data.append({
                    'poz_no': kzn_no,
                    'poz_adi': tanim.get('pozisyon_adi', f'Tanımsız ({kzn_no})'),
                    'receteler': data['receteler'],
                    'islem': islem,
                    'ort_recete': ort_recete,
                    'ort_gercek': ort_gercek,
                    'sapma': sapma,
                    'sapma_yuzde': sapma_yuzde
                })
            
            # Sapmaya göre sırala (en çok gecikmeden en hızlıya)
            sapma_data.sort(key=lambda x: x['sapma'], reverse=True)
            
            # Kartları güncelle
            self.card_toplam_sapma.findChild(QLabel, "val").setText(f"{toplam_sapma / 60:.0f} dk")
            
            if sapma_data:
                ort_sapma = sum(d['sapma'] for d in sapma_data) / len(sapma_data)
                self.card_ort_sapma.findChild(QLabel, "val").setText(f"{ort_sapma:+.0f} sn")
                
                self.card_en_cok_geciken.findChild(QLabel, "val").setText(f"P{sapma_data[0]['poz_no']}")
                self.card_en_hizli.findChild(QLabel, "val").setText(f"P{sapma_data[-1]['poz_no']}")
            
            # Tabloya aktar
            self.tbl_recete_sapma.setRowCount(len(sapma_data))
            
            for i, data in enumerate(sapma_data):
                self.tbl_recete_sapma.setItem(i, 0, QTableWidgetItem(str(data['poz_no'])))
                self.tbl_recete_sapma.setItem(i, 1, QTableWidgetItem(data['poz_adi']))
                
                rec_str = ','.join(str(r) for r in data['receteler'][:3])
                if len(data['receteler']) > 3:
                    rec_str += '...'
                self.tbl_recete_sapma.setItem(i, 2, QTableWidgetItem(rec_str))
                
                self.tbl_recete_sapma.setItem(i, 3, QTableWidgetItem(f"{data['islem']:,}"))
                self.tbl_recete_sapma.setItem(i, 4, QTableWidgetItem(f"{data['ort_recete']:.0f}"))
                self.tbl_recete_sapma.setItem(i, 5, QTableWidgetItem(f"{data['ort_gercek']:.0f}"))
                
                # Sapma renklendirme
                sapma_item = QTableWidgetItem(f"{data['sapma']:+.0f}")
                if data['sapma'] > 60:
                    sapma_item.setForeground(QBrush(QColor(self.error)))
                    sapma_item.setFont(QFont("", -1, QFont.Bold))
                elif data['sapma'] < -30:
                    sapma_item.setForeground(QBrush(QColor(self.success)))
                else:
                    sapma_item.setForeground(QBrush(QColor(self.warning)))
                self.tbl_recete_sapma.setItem(i, 6, sapma_item)
                
                # Sapma yüzdesi
                yuzde_item = QTableWidgetItem(f"{data['sapma_yuzde']:+.1f}%")
                if data['sapma_yuzde'] > 50:
                    yuzde_item.setForeground(QBrush(QColor(self.error)))
                elif data['sapma_yuzde'] < -20:
                    yuzde_item.setForeground(QBrush(QColor(self.success)))
                self.tbl_recete_sapma.setItem(i, 7, yuzde_item)
                
                # Durum
                if data['sapma'] > 60:
                    durum = "🔴 Gecikme"
                elif data['sapma'] < -30:
                    durum = "🟢 Hızlı"
                else:
                    durum = "🟡 Normal"
                self.tbl_recete_sapma.setItem(i, 8, QTableWidgetItem(durum))
                
        except Exception as e:
            print(f"Reçete sapma hatası: {e}")
            QMessageBox.warning(self, "Hata", f"Veri yüklenirken hata: {e}")
    
    def closeEvent(self, event):
        """Sayfa kapatılırken"""
        if self.plc_conn:
            try:
                self.plc_conn.close()
            except:
                pass
        super().closeEvent(event)