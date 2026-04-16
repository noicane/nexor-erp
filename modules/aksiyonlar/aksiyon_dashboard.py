# -*- coding: utf-8 -*-
"""
NEXOR ERP - Aksiyonlar Dashboard
Modern ve kapsamli aksiyon yonetim dashboard'u

Ozellikler:
- KPI istatistik kartlari (Toplam, Bekleyen, Devam Eden, Geciken, Tamamlanan, Ort. Kapanma)
- Duruma gore dagilim (Status distribution)
- Modullere gore dagilim (Module distribution)
- Son geciken aksiyonlar listesi
- Yaklasan hedef tarihleri
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from datetime import datetime, timedelta

from components.base_page import BasePage
from core.database import execute_query
from core.nexor_brand import brand


def get_modern_style(theme: dict) -> dict:
    return {
        'card_bg': brand.BG_CARD,
        'input_bg': brand.BG_INPUT,
        'border': brand.BORDER,
        'text': brand.TEXT,
        'text_secondary': brand.TEXT_MUTED,
        'text_muted': brand.TEXT_DIM,
        'primary': brand.PRIMARY,
        'primary_hover': brand.PRIMARY_HOVER,
        'success': brand.SUCCESS,
        'warning': brand.WARNING,
        'danger': brand.ERROR,
        'bg_main': brand.BG_MAIN,
        'bg_hover': brand.BG_HOVER,
        'border_light': brand.BORDER_HARD,
    }


class AksiyonDashboard(BasePage):
    """
    Aksiyonlar modulu icin dashboard sayfasi

    KPI'lar:
    - Toplam Aksiyon (aktif)
    - Bekleyen
    - Devam Eden
    - Geciken (kirmizi vurgu)
    - Tamamlanan (bu ay)
    - Ortalama Kapanma Suresi

    Grafikler ve Listeler:
    - Duruma gore dagilim
    - Modullere gore dagilim
    - Son geciken aksiyonlar
    - Yaklasan hedef tarihleri
    """

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.style = get_modern_style(theme)

        # Veri cache
        self.stats = {
            'toplam': 0,
            'bekleyen': 0,
            'devam_eden': 0,
            'geciken': 0,
            'tamamlanan': 0,
            'ort_sure': 0
        }
        self.durum_dagilim = []
        self.modul_dagilim = []
        self.geciken_aksiyonlar = []
        self.yaklasan_aksiyonlar = []

        self._setup_ui()

        # Ilk veri yukleme
        QTimer.singleShot(100, self.load_data)

        # Otomatik yenileme - 30 saniye
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_data)
        self.refresh_timer.start(30000)

    def _setup_ui(self):
        """Ana UI olustur"""
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {brand.BG_MAIN};
                border: none;
            }}
        """)

        # Container
        container = QWidget()
        container.setStyleSheet(f"background: {brand.BG_MAIN};")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # KPI Stats Row
        stats_row = self._create_stats_row()
        layout.addWidget(stats_row)

        # Middle Row: Durum Dagilim + Modul Dagilim
        middle_row = QHBoxLayout()
        middle_row.setSpacing(20)

        durum_card = self._create_durum_dagilim_card()
        middle_row.addWidget(durum_card, 1)

        modul_card = self._create_modul_dagilim_card()
        middle_row.addWidget(modul_card, 1)

        layout.addLayout(middle_row)

        # Bottom Row: Geciken + Yaklasan
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)

        geciken_card = self._create_geciken_aksiyonlar_card()
        bottom_row.addWidget(geciken_card, 1)

        yaklasan_card = self._create_yaklasan_aksiyonlar_card()
        bottom_row.addWidget(yaklasan_card, 1)

        layout.addLayout(bottom_row)

        layout.addStretch()

        scroll.setWidget(container)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _create_header(self) -> QWidget:
        """Sayfa basligi olustur"""
        header = QWidget()
        header.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        # Baslik
        title_layout = QVBoxLayout()
        title_layout.setSpacing(6)

        title = QLabel("Aksiyonlar Dashboard")
        title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {self.style['text']};
        """)
        title_layout.addWidget(title)

        self.lbl_update = QLabel("Son guncelleme: -")
        self.lbl_update.setStyleSheet(f"""
            font-size: 13px;
            color: {self.style['text_muted']};
        """)
        title_layout.addWidget(self.lbl_update)

        layout.addLayout(title_layout)
        layout.addStretch()

        return header

    def _create_stats_row(self) -> QWidget:
        """Ust satir KPI kartlari"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")

        layout = QGridLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # 6 adet KPI karti
        self.card_toplam = self.create_stat_card("Toplam Aksiyon", "0", color=self.style['info'])
        self.card_bekleyen = self.create_stat_card("Bekleyen", "0", color=self.style['text_muted'])
        self.card_devam = self.create_stat_card("Devam Eden", "0", color=self.style['warning'])
        self.card_geciken = self.create_stat_card("Geciken", "0", color=self.style['error'])
        self.card_tamamlanan = self.create_stat_card("Tamamlanan (Bu Ay)", "0", color=self.style['success'])
        self.card_ort_sure = self.create_stat_card("Ort. Kapanma Suresi", "0 gun", color=self.style['primary'])

        # 3 sutun, 2 satir
        layout.addWidget(self.card_toplam, 0, 0)
        layout.addWidget(self.card_bekleyen, 0, 1)
        layout.addWidget(self.card_devam, 0, 2)
        layout.addWidget(self.card_geciken, 1, 0)
        layout.addWidget(self.card_tamamlanan, 1, 1)
        layout.addWidget(self.card_ort_sure, 1, 2)

        return container

    def _create_durum_dagilim_card(self) -> QFrame:
        """Duruma gore dagilim karti"""
        card = self.create_card("Duruma Gore Dagilim")
        layout = card.layout()

        # Content container
        self.durum_content = QWidget()
        self.durum_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(self.durum_content)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Placeholder
        placeholder = QLabel("Veri yukleniyor...")
        placeholder.setStyleSheet(f"color: {self.style['text_muted']}; font-size: 13px;")
        placeholder.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(placeholder)

        layout.addWidget(self.durum_content)

        return card

    def _create_modul_dagilim_card(self) -> QFrame:
        """Modullere gore dagilim karti"""
        card = self.create_card("Modullere Gore Dagilim")
        layout = card.layout()

        # Content container
        self.modul_content = QWidget()
        self.modul_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(self.modul_content)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Placeholder
        placeholder = QLabel("Veri yukleniyor...")
        placeholder.setStyleSheet(f"color: {self.style['text_muted']}; font-size: 13px;")
        placeholder.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(placeholder)

        layout.addWidget(self.modul_content)

        return card

    def _create_geciken_aksiyonlar_card(self) -> QFrame:
        """Son geciken aksiyonlar karti"""
        card = self.create_card("Son Geciken Aksiyonlar")
        layout = card.layout()

        # Content container
        self.geciken_content = QWidget()
        self.geciken_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(self.geciken_content)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Placeholder
        placeholder = QLabel("Veri yukleniyor...")
        placeholder.setStyleSheet(f"color: {self.style['text_muted']}; font-size: 13px;")
        placeholder.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(placeholder)

        layout.addWidget(self.geciken_content)

        return card

    def _create_yaklasan_aksiyonlar_card(self) -> QFrame:
        """Yaklasan hedef tarihleri karti"""
        card = self.create_card("Yaklasan Hedef Tarihleri")
        layout = card.layout()

        # Content container
        self.yaklasan_content = QWidget()
        self.yaklasan_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(self.yaklasan_content)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Placeholder
        placeholder = QLabel("Veri yukleniyor...")
        placeholder.setStyleSheet(f"color: {self.style['text_muted']}; font-size: 13px;")
        placeholder.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(placeholder)

        layout.addWidget(self.yaklasan_content)

        return card

    # =========================================================================
    # VERI YUKLEME
    # =========================================================================

    def load_data(self):
        """Tum verileri yukle"""
        try:
            self._load_stats()
            self._load_durum_dagilim()
            self._load_modul_dagilim()
            self._load_geciken_aksiyonlar()
            self._load_yaklasan_aksiyonlar()

            # Update timestamp
            now = datetime.now().strftime("%d.%m.%Y %H:%M")
            self.lbl_update.setText(f"Son guncelleme: {now}")

        except Exception as e:
            print(f"Veri yukleme hatasi: {e}")

    def _load_stats(self):
        """KPI istatistiklerini yukle"""
        try:
            # Toplam aktif aksiyonlar (Bekleyen, Devam Eden, Geciken)
            query_toplam = """
                SELECT COUNT(*) as toplam
                FROM sistem.aksiyonlar
                WHERE durum IN ('BEKLIYOR', 'DEVAM_EDIYOR', 'GECIKTI')
                AND aktif_mi = 1 AND silindi_mi = 0
            """
            result = execute_query(query_toplam)
            self.stats['toplam'] = result[0]['toplam'] if result else 0

            # Duruma gore sayilar
            query_durum = """
                SELECT
                    durum,
                    COUNT(*) as sayi
                FROM sistem.aksiyonlar
                WHERE aktif_mi = 1 AND silindi_mi = 0
                GROUP BY durum
            """
            durum_rows = execute_query(query_durum)

            for row in durum_rows:
                durum = row['durum']
                sayi = row['sayi']

                if durum == 'BEKLIYOR':
                    self.stats['bekleyen'] = sayi
                elif durum == 'DEVAM_EDIYOR':
                    self.stats['devam_eden'] = sayi
                elif durum == 'GECIKTI':
                    self.stats['geciken'] = sayi

            # Tamamlanan (bu ay)
            query_tamamlanan = """
                SELECT COUNT(*) as sayi
                FROM sistem.aksiyonlar
                WHERE durum IN ('TAMAMLANDI', 'DOGRULANDI')
                AND MONTH(tamamlanma_tarihi) = MONTH(GETDATE())
                AND YEAR(tamamlanma_tarihi) = YEAR(GETDATE())
                AND aktif_mi = 1 AND silindi_mi = 0
            """
            result = execute_query(query_tamamlanan)
            self.stats['tamamlanan'] = result[0]['sayi'] if result else 0

            # Ortalama kapanma suresi (gun)
            query_ort = """
                SELECT
                    AVG(DATEDIFF(DAY, olusturma_tarihi, tamamlanma_tarihi)) as ort_sure
                FROM sistem.aksiyonlar
                WHERE durum IN ('TAMAMLANDI', 'DOGRULANDI')
                AND tamamlanma_tarihi IS NOT NULL
                AND aktif_mi = 1 AND silindi_mi = 0
            """
            result = execute_query(query_ort)
            self.stats['ort_sure'] = int(result[0]['ort_sure']) if result and result[0]['ort_sure'] else 0

            # UI'i guncelle
            self._update_stats_ui()

        except Exception as e:
            print(f"Stats yukleme hatasi: {e}")

    def _update_stats_ui(self):
        """KPI kartlarini guncelle"""
        # Toplam
        self._update_stat_card_value(self.card_toplam, str(self.stats['toplam']))

        # Bekleyen
        self._update_stat_card_value(self.card_bekleyen, str(self.stats['bekleyen']))

        # Devam Eden
        self._update_stat_card_value(self.card_devam, str(self.stats['devam_eden']))

        # Geciken (kirmizi)
        self._update_stat_card_value(self.card_geciken, str(self.stats['geciken']))

        # Tamamlanan
        self._update_stat_card_value(self.card_tamamlanan, str(self.stats['tamamlanan']))

        # Ortalama sure
        self._update_stat_card_value(self.card_ort_sure, f"{self.stats['ort_sure']} gun")

    def _update_stat_card_value(self, card: QFrame, value: str):
        """Stat card'in value label'ini guncelle"""
        # Card icindeki layout'u bul
        layout = card.layout()
        if layout and layout.count() >= 2:
            # 2. item value label
            item = layout.itemAt(1)
            if item:
                widget = item.widget()
                if isinstance(widget, QLabel):
                    widget.setText(value)

    def _load_durum_dagilim(self):
        """Duruma gore dagilim yukle"""
        try:
            query = """
                SELECT
                    durum,
                    COUNT(*) as sayi
                FROM sistem.aksiyonlar
                WHERE aktif_mi = 1 AND silindi_mi = 0
                GROUP BY durum
                ORDER BY sayi DESC
            """
            self.durum_dagilim = execute_query(query)
            self._render_durum_dagilim()

        except Exception as e:
            print(f"Durum dagilim yukleme hatasi: {e}")

    def _render_durum_dagilim(self):
        """Durum dagilim gorselini render et"""
        # Eski widget'lari temizle
        layout = self.durum_content.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.durum_dagilim:
            no_data = QLabel("Veri bulunamadi")
            no_data.setStyleSheet(f"color: {self.style['text_muted']}; font-size: 13px;")
            no_data.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_data)
            return

        # Renkler
        durum_colors = {
            'BEKLIYOR': self.style['text_muted'],
            'DEVAM_EDIYOR': self.style['warning'],
            'GECIKTI': self.style['error'],
            'TAMAMLANDI': self.style['success'],
            'DOGRULANDI': self.style['success'],
        }

        durum_labels = {
            'BEKLIYOR': 'Bekleyen',
            'DEVAM_EDIYOR': 'Devam Eden',
            'GECIKTI': 'Geciken',
            'TAMAMLANDI': 'Tamamlandi',
            'DOGRULANDI': 'Dogrulandi',
        }

        for row in self.durum_dagilim:
            durum = row['durum']
            sayi = row['sayi']
            color = durum_colors.get(durum, self.style['info'])
            label = durum_labels.get(durum, durum)

            item = self._create_distribution_item(label, sayi, color)
            layout.addWidget(item)

        layout.addStretch()

    def _load_modul_dagilim(self):
        """Modullere gore dagilim yukle"""
        try:
            query = """
                SELECT
                    kaynak_modul,
                    COUNT(*) as sayi
                FROM sistem.aksiyonlar
                WHERE aktif_mi = 1 AND silindi_mi = 0
                AND durum IN ('BEKLIYOR', 'DEVAM_EDIYOR', 'GECIKTI')
                GROUP BY kaynak_modul
                ORDER BY sayi DESC
            """
            self.modul_dagilim = execute_query(query)
            self._render_modul_dagilim()

        except Exception as e:
            print(f"Modul dagilim yukleme hatasi: {e}")

    def _render_modul_dagilim(self):
        """Modul dagilim gorselini render et"""
        # Eski widget'lari temizle
        layout = self.modul_content.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.modul_dagilim:
            no_data = QLabel("Veri bulunamadi")
            no_data.setStyleSheet(f"color: {self.style['text_muted']}; font-size: 13px;")
            no_data.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_data)
            return

        # Bar chart benzeri gorsel
        max_sayi = max([r['sayi'] for r in self.modul_dagilim]) if self.modul_dagilim else 1

        colors = [self.style['primary'], self.style['info'], self.style['success'],
                  self.style['warning'], self.style['error']]

        for idx, row in enumerate(self.modul_dagilim):
            modul = row['kaynak_modul'] or 'Tanimsiz'
            sayi = row['sayi']
            color = colors[idx % len(colors)]

            bar_item = self._create_bar_item(modul, sayi, max_sayi, color)
            layout.addWidget(bar_item)

        layout.addStretch()

    def _load_geciken_aksiyonlar(self):
        """Son geciken aksiyonlar yukle"""
        try:
            query = """
                SELECT TOP 5
                    id AS aksiyon_id,
                    baslik,
                    kaynak_modul AS modul,
                    hedef_tarih,
                    sorumlu_adi AS sorumlu,
                    gecikme_gun AS gecikme_gunu
                FROM sistem.vw_aksiyon_ozet
                WHERE durum = 'GECIKTI'
                ORDER BY gecikme_gun DESC
            """
            self.geciken_aksiyonlar = execute_query(query)
            self._render_geciken_aksiyonlar()

        except Exception as e:
            print(f"Geciken aksiyonlar yukleme hatasi: {e}")

    def _render_geciken_aksiyonlar(self):
        """Geciken aksiyonlar listesini render et"""
        # Eski widget'lari temizle
        layout = self.geciken_content.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.geciken_aksiyonlar:
            no_data = QLabel("Geciken aksiyon bulunmamaktadir")
            no_data.setStyleSheet(f"color: {self.style['success']}; font-size: 13px;")
            no_data.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_data)
            return

        for aksiyon in self.geciken_aksiyonlar:
            item = self._create_aksiyon_item(aksiyon, 'geciken')
            layout.addWidget(item)

        layout.addStretch()

    def _load_yaklasan_aksiyonlar(self):
        """Yaklasan hedef tarihleri yukle"""
        try:
            # 7 gun icinde biten
            query = """
                SELECT TOP 5
                    id AS aksiyon_id,
                    baslik,
                    kaynak_modul AS modul,
                    hedef_tarih,
                    sorumlu_adi AS sorumlu,
                    kalan_gun
                FROM sistem.vw_aksiyon_ozet
                WHERE durum IN ('BEKLIYOR', 'DEVAM_EDIYOR')
                AND hedef_tarih >= CAST(GETDATE() AS DATE)
                AND hedef_tarih <= DATEADD(DAY, 7, CAST(GETDATE() AS DATE))
                ORDER BY hedef_tarih ASC
            """
            self.yaklasan_aksiyonlar = execute_query(query)
            self._render_yaklasan_aksiyonlar()

        except Exception as e:
            print(f"Yaklasan aksiyonlar yukleme hatasi: {e}")

    def _render_yaklasan_aksiyonlar(self):
        """Yaklasan aksiyonlar listesini render et"""
        # Eski widget'lari temizle
        layout = self.yaklasan_content.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.yaklasan_aksiyonlar:
            no_data = QLabel("Yaklasan aksiyon bulunmamaktadir")
            no_data.setStyleSheet(f"color: {self.style['text_muted']}; font-size: 13px;")
            no_data.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_data)
            return

        for aksiyon in self.yaklasan_aksiyonlar:
            item = self._create_aksiyon_item(aksiyon, 'yaklasan')
            layout.addWidget(item)

        layout.addStretch()

    # =========================================================================
    # UI HELPERS
    # =========================================================================

    def _create_distribution_item(self, label: str, value: int, color: str) -> QWidget:
        """Dagilim item'i olustur (renkli kutu + label + deger)"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Renkli kutu
        color_box = QLabel()
        color_box.setFixedSize(40, 40)
        color_box.setStyleSheet(f"""
            background: {color};
            border-radius: 8px;
        """)
        layout.addWidget(color_box)

        # Label
        lbl = QLabel(label)
        lbl.setStyleSheet(f"""
            color: {self.style['text']};
            font-size: 14px;
            font-weight: 500;
        """)
        layout.addWidget(lbl)

        layout.addStretch()

        # Deger
        val = QLabel(str(value))
        val.setStyleSheet(f"""
            color: {color};
            font-size: 18px;
            font-weight: 700;
        """)
        layout.addWidget(val)

        return container

    def _create_bar_item(self, label: str, value: int, max_value: int, color: str) -> QWidget:
        """Bar chart item'i olustur"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Ust satir: Label + Deger
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"""
            color: {self.style['text']};
            font-size: 13px;
            font-weight: 500;
        """)
        top_layout.addWidget(lbl)

        top_layout.addStretch()

        val = QLabel(str(value))
        val.setStyleSheet(f"""
            color: {color};
            font-size: 14px;
            font-weight: 700;
        """)
        top_layout.addWidget(val)

        layout.addLayout(top_layout)

        # Bar
        bar_container = QWidget()
        bar_container.setFixedHeight(10)
        bar_container.setStyleSheet(f"""
            background: {self.style['border']};
            border-radius: 5px;
        """)

        bar = QLabel(bar_container)
        bar.setFixedHeight(10)
        percentage = (value / max_value) * 100 if max_value > 0 else 0
        bar.setFixedWidth(int(bar_container.width() * percentage / 100)) if percentage > 0 else 0
        bar.setStyleSheet(f"""
            background: {color};
            border-radius: 5px;
        """)

        # Yuzde hesapla ve genislik ayarla (manuel)
        bar.setFixedWidth(int(300 * percentage / 100))

        layout.addWidget(bar_container)

        return container

    def _create_aksiyon_item(self, aksiyon: dict, item_type: str) -> QFrame:
        """Aksiyon item widget'i olustur"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {self.style['input_bg']};
                border: 1px solid {self.style['border']};
                border-radius: 10px;
                padding: 14px;
            }}
            QFrame:hover {{
                border-color: {self.style['primary']};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # Baslik
        baslik = QLabel(aksiyon.get('baslik', 'Baslik yok'))
        baslik.setStyleSheet(f"""
            color: {self.style['text']};
            font-size: 14px;
            font-weight: 600;
        """)
        baslik.setWordWrap(True)
        layout.addWidget(baslik)

        # Alt bilgiler
        info_layout = QHBoxLayout()
        info_layout.setSpacing(12)

        # Modul
        modul = aksiyon.get('modul', '-')
        modul_badge = self.create_badge(modul, "default")
        info_layout.addWidget(modul_badge)

        # Sorumlu
        sorumlu = aksiyon.get('sorumlu', '-')
        sorumlu_lbl = QLabel(f"Sorumlu: {sorumlu}")
        sorumlu_lbl.setStyleSheet(f"color: {self.style['text_secondary']}; font-size: 12px;")
        info_layout.addWidget(sorumlu_lbl)

        info_layout.addStretch()

        # Tarih bilgisi
        if item_type == 'geciken':
            gecikme = aksiyon.get('gecikme_gunu', 0)
            tarih_badge = self.create_badge(f"{gecikme} gun gecikti", "error")
        else:
            kalan = aksiyon.get('kalan_gun', 0)
            variant = "warning" if kalan <= 3 else "info"
            tarih_badge = self.create_badge(f"{kalan} gun kaldi", variant)

        info_layout.addWidget(tarih_badge)

        layout.addLayout(info_layout)

        return frame
