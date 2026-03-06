# -*- coding: utf-8 -*-
"""
NEXOR ERP - Dashboard Sayfasi v2.0
Modern UI ile yeniden tasarlandi
Is mantigi aynen korundu

Degisiklikler:
- NexorComponents kullaniliyor
- Tutarli renk paleti
- Responsive tasarim
- Temiz layout
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Yeni component sistemi
from components.nexor_components import (
    NexorCard, NexorStatsCard, NexorButton, NexorBadge,
    NexorTable, NexorPageHeader, Spacing, BorderRadius, FontSize,
    get_theme_colors
)

# Mevcut baglantilar (degismiyor)
from core.database import get_db_connection, get_plc_connection


class DashboardPageV2(QWidget):
    """
    Modern Dashboard Sayfasi
    
    Ozellikler:
    - 4 adet vardiya uretim karti (KTL Giren/Cikan, Cinko Giren/Cikan)
    - 4 adet KPI karti (Aktif Pozisyon, Gunluk Uretim, Uyari, Verimlilik)
    - Hat durumu tablosu
    - Son islemler tablosu
    - Otomatik yenileme (10 saniye)
    """
    
    def __init__(self, theme: dict):
        super().__init__()
        self.theme = get_theme_colors(theme)
        self.plc_conn = None
        
        # Veri cache
        self.ktl_giren = 0
        self.ktl_cikan = 0
        self.cinko_giren = 0
        self.cinko_cikan = 0
        self.aktif_pozisyon = 0
        self.toplam_uretim = 0
        self.uyari_sayisi = 0
        
        self._setup_ui()
        
        # Ilk veri yukleme
        QTimer.singleShot(100, self._load_all_data)
        
        # Otomatik yenileme - 10 saniye
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_all_data)
        self.refresh_timer.start(10000)
    
    def _setup_ui(self):
        """Ana UI'i olustur"""
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {self.theme['bg_main']};
                border: none;
            }}
        """)
        
        # Ana container
        container = QWidget()
        container.setStyleSheet(f"background: {self.theme['bg_main']};")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.XL)
        
        # === HEADER ===
        header = self._create_header()
        layout.addWidget(header)
        
        # === VARDIYA URETIM KARTLARI ===
        vardiya_section = self._create_vardiya_section()
        layout.addWidget(vardiya_section)
        
        # === KPI KARTLARI ===
        kpi_section = self._create_kpi_section()
        layout.addWidget(kpi_section)
        
        # === ALT ICERIK (Hat Durumu + Son Islemler) ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(Spacing.XL)
        
        # Sol: Hat Durumu
        hat_card = self._create_hat_durumu_card()
        content_layout.addWidget(hat_card, 1)
        
        # Sag: Son Islemler
        islem_card = self._create_son_islemler_card()
        content_layout.addWidget(islem_card, 1)
        
        layout.addLayout(content_layout)
        
        layout.addStretch()
        
        scroll.setWidget(container)
        
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def _create_header(self) -> QWidget:
        """Sayfa basligini olustur"""
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Sol: Baslik
        title_layout = QVBoxLayout()
        title_layout.setSpacing(Spacing.XS)
        
        title = QLabel("📊 Dashboard")
        title.setStyleSheet(f"""
            font-size: {FontSize.XXXL}px;
            font-weight: 600;
            color: {self.theme['text']};
            background: transparent;
        """)
        title_layout.addWidget(title)
        
        self.lbl_update = QLabel("Son güncelleme: -")
        self.lbl_update.setStyleSheet(f"""
            font-size: {FontSize.MD}px;
            color: {self.theme['text_muted']};
            background: transparent;
        """)
        title_layout.addWidget(self.lbl_update)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Sag: Yenile butonu
        btn_refresh = NexorButton("🔄 Yenile", self.theme, "primary")
        btn_refresh.clicked.connect(self._load_all_data)
        layout.addWidget(btn_refresh)
        
        return header
    
    def _create_vardiya_section(self) -> QWidget:
        """Vardiya uretim kartlarini olustur"""
        section = QWidget()
        section.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.LG)
        
        # Baslik
        title = QLabel("📦 Vardiya Üretim (07:30 - 07:30)")
        title.setStyleSheet(f"""
            font-size: {FontSize.XL}px;
            font-weight: 600;
            color: {self.theme['text']};
            background: transparent;
        """)
        layout.addWidget(title)
        
        # Kartlar
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(Spacing.LG)
        
        # KTL Giren
        self.card_ktl_giren = NexorStatsCard(
            self.theme,
            title="KTL GİREN",
            value="0",
            icon="🔵",
            color="#3B82F6"
        )
        cards_layout.addWidget(self.card_ktl_giren)
        
        # KTL Cikan
        self.card_ktl_cikan = NexorStatsCard(
            self.theme,
            title="KTL ÇIKAN",
            value="0",
            icon="✅",
            color="#10B981"
        )
        cards_layout.addWidget(self.card_ktl_cikan)
        
        # Cinko Giren
        self.card_cinko_giren = NexorStatsCard(
            self.theme,
            title="ÇİNKO GİREN",
            value="0",
            icon="🟡",
            color="#F59E0B"
        )
        cards_layout.addWidget(self.card_cinko_giren)
        
        # Cinko Cikan
        self.card_cinko_cikan = NexorStatsCard(
            self.theme,
            title="ÇİNKO ÇIKAN",
            value="0",
            icon="✅",
            color="#10B981"
        )
        cards_layout.addWidget(self.card_cinko_cikan)
        
        layout.addLayout(cards_layout)
        
        return section
    
    def _create_kpi_section(self) -> QWidget:
        """KPI kartlarini olustur"""
        section = QWidget()
        section.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.LG)
        
        # Baslik
        title = QLabel("📈 Anlık Durum")
        title.setStyleSheet(f"""
            font-size: {FontSize.XL}px;
            font-weight: 600;
            color: {self.theme['text']};
            background: transparent;
        """)
        layout.addWidget(title)
        
        # Kartlar
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(Spacing.LG)
        
        # Aktif Pozisyon
        self.card_aktif = NexorStatsCard(
            self.theme,
            title="Aktif Pozisyon",
            value="0",
            icon="🟢",
            trend="Son 5 dk",
            trend_up=True,
            color="#10B981"
        )
        cards_layout.addWidget(self.card_aktif)
        
        # Gunluk Uretim
        self.card_uretim = NexorStatsCard(
            self.theme,
            title="Günlük Üretim",
            value="0",
            icon="📦",
            trend="Bugün",
            trend_up=True,
            color="#3B82F6"
        )
        cards_layout.addWidget(self.card_uretim)
        
        # Uyari
        self.card_uyari = NexorStatsCard(
            self.theme,
            title="Uyarı",
            value="0",
            icon="⚠️",
            color="#EF4444"
        )
        cards_layout.addWidget(self.card_uyari)
        
        # Verimlilik
        self.card_verimlilik = NexorStatsCard(
            self.theme,
            title="Verimlilik",
            value="-%",
            icon="📊",
            color="#8B5CF6"
        )
        cards_layout.addWidget(self.card_verimlilik)
        
        layout.addLayout(cards_layout)
        
        return section
    
    def _create_hat_durumu_card(self) -> NexorCard:
        """Hat durumu kartini olustur"""
        card = NexorCard(self.theme, "🏭 Hat Durumu")
        
        # Tablo
        self.hat_table = NexorTable(self.theme)
        self.hat_table.set_columns(["Hat", "Durum", "Verimlilik"])
        self.hat_table.setMinimumHeight(200)
        
        card.add_widget(self.hat_table)
        
        return card
    
    def _create_son_islemler_card(self) -> NexorCard:
        """Son islemler kartini olustur"""
        card = NexorCard(self.theme, "📋 Son İşlemler")
        
        # Tablo
        self.islem_table = NexorTable(self.theme)
        self.islem_table.set_columns(["Saat", "Hat", "Ürün", "Miktar"])
        self.islem_table.setMinimumHeight(200)
        
        card.add_widget(self.islem_table)
        
        return card
    
    # =========================================================================
    # VERI YUKLEME (Is mantigi aynen korundu)
    # =========================================================================
    
    def _load_all_data(self):
        """Tum verileri arka planda yukle"""
        # Eger zaten yukleme yapiliyorsa tekrar baslatma
        if hasattr(self, '_bg_thread') and self._bg_thread and self._bg_thread.isRunning():
            return

        from core.db_worker import run_in_background
        self._bg_thread, self._bg_worker = run_in_background(
            self._fetch_all_data,
            on_success=self._on_data_loaded,
            on_error=self._on_data_error
        )

    def _fetch_all_data(self) -> dict:
        """Arka plan thread'inde calisan veri toplama (UI erisimi yok!)"""
        result = {
            'vardiya': [],
            'plc': None,
            'son_islemler': [],
        }

        # Vardiya verileri
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM uretim.vw_guncel_vardiya")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                conn.close()
                result['vardiya'] = [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.warning("Vardiya veri hatasi: %s", e)

        # PLC verileri
        try:
            plc_conn = get_plc_connection()
            if plc_conn:
                cursor = plc_conn.cursor()
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT KznNo) as aktif_poz,
                        SUM(ISNULL(Miktar, 0)) as toplam_miktar,
                        COUNT(*) as toplam_islem
                    FROM dbo.data
                    WHERE TarihDoldurma >= DATEADD(MINUTE, -5, GETDATE())
                """)
                row = cursor.fetchone()
                if row:
                    result['plc'] = {
                        'aktif_poz': row[0] or 0,
                        'toplam_miktar': row[1] or 0,
                    }
        except Exception as e:
            logger.warning("PLC veri hatasi: %s", e)

        # Son islemler
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT TOP 10
                        FORMAT(kayit_tarihi, 'HH:mm') as saat,
                        hat_adi,
                        urun_kodu,
                        miktar
                    FROM uretim.uretim_kayitlari
                    ORDER BY kayit_tarihi DESC
                """)
                result['son_islemler'] = cursor.fetchall()
                conn.close()
        except Exception as e:
            logger.warning("Son islemler hatasi: %s", e)

        return result

    def _on_data_loaded(self, data: dict):
        """Veriler yuklendi - UI thread'inde guncelle"""
        # Vardiya
        for item in data.get('vardiya', []):
            hat_tipi = item.get('hat_tipi')
            giren = item.get('giren_bara', 0) or 0
            cikan = item.get('cikan_bara', 0) or 0

            if hat_tipi == 'KTL':
                self.ktl_giren = giren
                self.ktl_cikan = cikan
                self.card_ktl_giren.set_value(str(giren))
                self.card_ktl_cikan.set_value(str(cikan))
            elif hat_tipi == 'CINKO':
                self.cinko_giren = giren
                self.cinko_cikan = cikan
                self.card_cinko_giren.set_value(str(giren))
                self.card_cinko_cikan.set_value(str(cikan))

        # PLC
        plc = data.get('plc')
        if plc:
            self.aktif_pozisyon = plc['aktif_poz']
            self.toplam_uretim = plc['toplam_miktar']
            self.card_aktif.set_value(str(self.aktif_pozisyon))
            self.card_uretim.set_value(f"{self.toplam_uretim:,.0f}")

        self.card_uyari.set_value(str(self.uyari_sayisi))
        self.card_verimlilik.set_value("-%")

        # Hat durumu
        self._update_hat_durumu()

        # Son islemler
        self.islem_table.clear_rows()
        for row in data.get('son_islemler', []):
            self.islem_table.add_row([
                row[0] or "-",
                row[1] or "-",
                row[2] or "-",
                str(row[3] or 0)
            ])

        self.lbl_update.setText(f"Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")

    def _on_data_error(self, error_str: str):
        """Veri yukleme hatasi"""
        logger.error("Dashboard veri hatasi: %s", error_str)

    def _update_hat_durumu(self):
        """Hat durumu tablosunu guncelle"""
        try:
            self.hat_table.clear_rows()

            hatlar = [
                ("E-KTL Hattı", "Çalışıyor", 85),
                ("Çinko-Nikel Hattı", "Çalışıyor", 78),
                ("Toz Boya Hattı", "Beklemede", 0),
            ]

            for hat, durum, verimlilik in hatlar:
                if durum == "Çalışıyor":
                    badge = NexorBadge(durum, self.theme, "success")
                elif durum == "Beklemede":
                    badge = NexorBadge(durum, self.theme, "warning")
                else:
                    badge = NexorBadge(durum, self.theme, "error")

                self.hat_table.add_row([hat, badge, f"%{verimlilik}"])

        except Exception as e:
            logger.warning("Hat durumu hatasi: %s", e)
    
    def update_theme(self, theme: dict):
        """Temayi guncelle"""
        self.theme = get_theme_colors(theme)
        # TODO: Tum bileşenleri güncelle


# =============================================================================
# GERIYE UYUMLULUK - Eski DashboardPage sinifini koruyalim
# =============================================================================

# Eger eski sinif kullaniliyorsa bu import calisir
# Yeni sinifi kullanmak icin PAGE_CLASSES'ta degisiklik yapilmali
