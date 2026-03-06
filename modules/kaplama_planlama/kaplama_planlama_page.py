# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kaplama Hatti Haftalik Planlama
Sol panel (ozet + banyo kartlari + urun listesi) + Sag panel (Toolbar + Tabs: Gantt + Hat Durumu)
"""
from datetime import date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QFrame,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QDialog, QFormLayout, QLineEdit,
    QComboBox, QSpinBox, QMessageBox, QAbstractItemView, QGridLayout,
    QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QFont, QColor

from components.base_page import BasePage
from .models import (
    KaplamaUrun, PlanGorev,
    BARA_SAYISI, VARDIYA_SURE_DK, VARDIYA_SAYISI, GUN_SAYISI
)
from .gantt_widget import GanttWidget
from .planlama_motoru import otomatik_planla
from .widgets import (
    BanyoCard, HatCanliWidget, BaraDurumStrip,
    HatIstatistikCard, ReceteAdimWidget
)
from . import db_operations as db


def _monday_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _get_style(theme: dict) -> dict:
    return {
        'card_bg': theme.get('bg_card', '#1E1E1E'),
        'input_bg': theme.get('bg_input', '#1A1A1A'),
        'border': theme.get('border', '#2A2A2A'),
        'text': theme.get('text', '#FFFFFF'),
        'text_secondary': theme.get('text_secondary', '#AAAAAA'),
        'text_muted': theme.get('text_muted', '#666666'),
        'primary': theme.get('primary', '#DC2626'),
        'success': theme.get('success', '#10B981'),
        'warning': theme.get('warning', '#F59E0B'),
        'error': theme.get('error', '#EF4444'),
        'info': theme.get('info', '#3B82F6'),
        'gradient_css': theme.get('gradient_css', 'linear-gradient(135deg, #DC2626, #B91C1C)'),
        'gradient_start': theme.get('gradient_start', '#DC2626'),
    }


class KaplamaPlanlamaPage(BasePage):
    """Kaplama Hatti Haftalik Planlama Sayfasi"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = _get_style(theme)
        self.plan_id: int = 0
        self.urunler: list[KaplamaUrun] = []
        self.gorevler: list[PlanGorev] = []
        self._plc_data: list = []
        self._setup_ui()
        QTimer.singleShot(200, self._init_data)

    # ══════════════════════════════════════════════════════
    #  UI KURULUMU
    # ══════════════════════════════════════════════════════

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {self.s['border']}; width: 2px; }}")

        left_widget = self._build_left_panel()
        splitter.addWidget(left_widget)

        right_widget = self._build_right_panel()
        splitter.addWidget(right_widget)

        splitter.setSizes([380, 850])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    # ── SOL PANEL ──

    def _build_left_panel(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(f"background: {self.s['card_bg']};")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Baslik
        title = QLabel("Kaplama Planlama")
        title.setStyleSheet(f"color: {self.s['text']}; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Ozet kartlari
        self._build_summary_cards(layout)

        # Hat istatistik kartlari (KTL + ZNNI)
        self._build_hat_istatistik(layout)

        # Banyo kartlari
        self._build_banyo_cards(layout)

        # Urun listesi
        self._build_urun_table(layout)

        # Recete goruntuleme
        self._build_recete_viewer(layout)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return container

    def _build_summary_cards(self, parent_layout: QVBoxLayout):
        self._section_label(parent_layout, "Ozet")
        grid = QGridLayout()
        grid.setSpacing(8)

        self.lbl_toplam_aski = self._stat_card("Toplam Yukleme", "0", self.s['info'])
        self.lbl_toplam_parca = self._stat_card("Toplam Parca", "0", self.s['success'])
        self.lbl_bara_kullanim = self._stat_card("Bara Kullanim", "%0", self.s['warning'])
        self.lbl_plan_durum = self._stat_card("Durum", "Taslak", self.s['text_muted'])

        grid.addWidget(self.lbl_toplam_aski, 0, 0)
        grid.addWidget(self.lbl_toplam_parca, 0, 1)
        grid.addWidget(self.lbl_bara_kullanim, 1, 0)
        grid.addWidget(self.lbl_plan_durum, 1, 1)
        parent_layout.addLayout(grid)

    def _build_hat_istatistik(self, parent_layout: QVBoxLayout):
        self._section_label(parent_layout, "Hat Durumu (Canli)")
        hat_layout = QHBoxLayout()
        hat_layout.setSpacing(8)

        self.card_ktl = HatIstatistikCard(self.s)
        self.card_cinko = HatIstatistikCard(self.s)

        hat_layout.addWidget(self.card_ktl)
        hat_layout.addWidget(self.card_cinko)
        parent_layout.addLayout(hat_layout)

    def _build_banyo_cards(self, parent_layout: QVBoxLayout):
        self._section_label(parent_layout, "Banyolar (Canli PLC)")

        self.banyo_scroll = QScrollArea()
        self.banyo_scroll.setWidgetResizable(True)
        self.banyo_scroll.setFixedHeight(190)
        self.banyo_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.banyo_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.banyo_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:horizontal {{
                height: 6px; background: {self.s['input_bg']};
            }}
            QScrollBar::handle:horizontal {{
                background: {self.s['border']}; border-radius: 3px; min-width: 30px;
            }}
        """)

        self.banyo_container = QWidget()
        self.banyo_cards_layout = QHBoxLayout(self.banyo_container)
        self.banyo_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.banyo_cards_layout.setSpacing(8)

        self.banyo_cards: list[BanyoCard] = []
        self.banyo_scroll.setWidget(self.banyo_container)
        parent_layout.addWidget(self.banyo_scroll)

    def _build_urun_table(self, parent_layout: QVBoxLayout):
        header_layout = QHBoxLayout()
        self._section_label(header_layout, "Urun Ihtiyaclari")
        header_layout.addStretch()

        btn_ekle = QPushButton("+ Urun Ekle")
        btn_ekle.setCursor(Qt.PointingHandCursor)
        btn_ekle.setFixedHeight(28)
        btn_ekle.setStyleSheet(f"""
            QPushButton {{ background: {self.s['primary']}; color: white; border: none;
                border-radius: 6px; padding: 4px 12px; font-weight: bold; font-size: 11px; }}
            QPushButton:hover {{ background: {self.s['gradient_start']}; }}
        """)
        btn_ekle.clicked.connect(self._on_urun_ekle)
        header_layout.addWidget(btn_ekle)
        parent_layout.addLayout(header_layout)

        self.urun_table = QTableWidget()
        self.urun_table.setColumnCount(7)
        self.urun_table.setHorizontalHeaderLabels(["Ref", "Tip", "Ihtiyac", "Aski", "Bara", "Cevrim", "Oncelik"])
        self.urun_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.urun_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.urun_table.verticalHeader().setVisible(False)
        self.urun_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.urun_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.urun_table.setMaximumHeight(200)
        self.urun_table.setStyleSheet(f"""
            QTableWidget {{ background: {self.s['input_bg']}; border: 1px solid {self.s['border']};
                border-radius: 8px; gridline-color: {self.s['border']}; color: {self.s['text']}; font-size: 11px; }}
            QHeaderView::section {{ background: {self.s['card_bg']}; color: {self.s['text_secondary']};
                border: none; border-bottom: 1px solid {self.s['border']}; padding: 5px; font-weight: bold; font-size: 10px; }}
            QTableWidget::item {{ padding: 3px 6px; }}
            QTableWidget::item:selected {{ background: {self.s['primary']}33; }}
        """)
        self.urun_table.clicked.connect(self._on_urun_table_clicked)
        parent_layout.addWidget(self.urun_table)

        # Sil butonu
        btn_sil = QPushButton("Secili Urunu Sil")
        btn_sil.setCursor(Qt.PointingHandCursor)
        btn_sil.setFixedHeight(26)
        btn_sil.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {self.s['error']}; border: 1px solid {self.s['error']}44;
                border-radius: 6px; padding: 3px 10px; font-size: 10px; }}
            QPushButton:hover {{ background: {self.s['error']}22; }}
        """)
        btn_sil.clicked.connect(self._on_urun_sil)
        parent_layout.addWidget(btn_sil)

    def _build_recete_viewer(self, parent_layout: QVBoxLayout):
        self._section_label(parent_layout, "Recete Adimlari")
        self.recete_widget = ReceteAdimWidget()
        parent_layout.addWidget(self.recete_widget)

        self.lbl_recete_toplam = QLabel("Urun secin")
        self.lbl_recete_toplam.setStyleSheet(f"color: {self.s['text_muted']}; font-size: 10px;")
        parent_layout.addWidget(self.lbl_recete_toplam)

    # ── SAG PANEL ──

    def _build_right_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        # Bara durum strip
        self.bara_strip = BaraDurumStrip()
        layout.addWidget(self.bara_strip)

        # Tab widget: Planlama + Hat Durumu
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: {self.s['card_bg']}; }}
            QTabBar::tab {{
                background: {self.s['input_bg']}; color: {self.s['text_secondary']};
                padding: 8px 20px; border: none; border-bottom: 2px solid transparent;
                font-size: 12px; font-weight: bold;
            }}
            QTabBar::tab:selected {{
                color: {self.s['text']}; border-bottom: 2px solid {self.s['primary']};
                background: {self.s['card_bg']};
            }}
            QTabBar::tab:hover {{ color: {self.s['text']}; }}
        """)

        # Tab 1: Gantt Planlama
        gantt_container = QWidget()
        gantt_layout = QVBoxLayout(gantt_container)
        gantt_layout.setContentsMargins(0, 0, 0, 0)
        gantt_layout.setSpacing(0)
        self.gantt = GanttWidget()
        self.gantt.gorev_silindi.connect(self._on_gorev_silindi)
        gantt_layout.addWidget(self.gantt, 1)
        self.tab_widget.addTab(gantt_container, "Haftalik Plan")

        # Tab 2: Hat Canli Gorunum
        hat_container = QWidget()
        hat_layout = QVBoxLayout(hat_container)
        hat_layout.setContentsMargins(8, 8, 8, 8)
        hat_layout.setSpacing(8)

        # KTL hatti
        lbl_ktl = QLabel("KTL Hatti (101-143)")
        lbl_ktl.setStyleSheet(f"color: {self.s['text']}; font-size: 14px; font-weight: bold;")
        hat_layout.addWidget(lbl_ktl)
        self.hat_ktl = HatCanliWidget()
        self.hat_ktl.setMinimumHeight(220)
        hat_layout.addWidget(self.hat_ktl)

        # ZNNI hatti
        lbl_cinko = QLabel("Cinko-Nikel Hatti (201-247)")
        lbl_cinko.setStyleSheet(f"color: {self.s['text']}; font-size: 14px; font-weight: bold;")
        hat_layout.addWidget(lbl_cinko)
        self.hat_cinko = HatCanliWidget()
        self.hat_cinko.setMinimumHeight(220)
        hat_layout.addWidget(self.hat_cinko)

        hat_layout.addStretch()
        self.tab_widget.addTab(hat_container, "Hat Canli Gorunum")

        layout.addWidget(self.tab_widget, 1)

        # Alt bilgi bari
        bottom_bar = self._build_bottom_bar()
        layout.addWidget(bottom_bar)

        return container

    def _build_toolbar(self) -> QFrame:
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet(f"QFrame {{ background: {self.s['card_bg']}; border-bottom: 1px solid {self.s['border']}; }}")

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        lbl = QLabel("Hafta:")
        lbl.setStyleSheet(f"color: {self.s['text_secondary']}; font-size: 12px;")
        layout.addWidget(lbl)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        monday = _monday_of_week(date.today())
        self.date_edit.setDate(QDate(monday.year, monday.month, monday.day))
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setStyleSheet(f"""
            QDateEdit {{ background: {self.s['input_bg']}; color: {self.s['text']};
                border: 1px solid {self.s['border']}; border-radius: 6px; padding: 4px 8px; min-width: 110px; }}
        """)
        self.date_edit.dateChanged.connect(self._on_hafta_degisti)
        layout.addWidget(self.date_edit)

        # Canli gosterge
        self.lbl_canli = QLabel("CANLI")
        self.lbl_canli.setStyleSheet(f"""
            color: {self.s['success']}; font-size: 10px; font-weight: bold;
            background: {self.s['success']}22; border: 1px solid {self.s['success']}44;
            border-radius: 4px; padding: 2px 8px;
        """)
        layout.addWidget(self.lbl_canli)

        layout.addStretch()

        # Butonlar
        btn_style = f"""QPushButton {{ background: {self.s['input_bg']}; color: {self.s['text']};
            border: 1px solid {self.s['border']}; border-radius: 6px; padding: 6px 14px;
            font-size: 12px; font-weight: bold; }}
            QPushButton:hover {{ background: {self.s['border']}; }}"""
        primary_btn = f"""QPushButton {{ background: {self.s['primary']}; color: white; border: none;
            border-radius: 6px; padding: 6px 14px; font-size: 12px; font-weight: bold; }}
            QPushButton:hover {{ background: {self.s['gradient_start']}; }}"""
        success_btn = f"""QPushButton {{ background: {self.s['success']}; color: white; border: none;
            border-radius: 6px; padding: 6px 14px; font-size: 12px; font-weight: bold; }}
            QPushButton:hover {{ opacity: 0.9; }}"""

        for text, style, handler in [
            ("Temizle", btn_style, self._on_temizle),
            ("Otomatik Planla", primary_btn, self._on_otomatik_planla),
            ("Kaydet", success_btn, self._on_kaydet),
        ]:
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(style)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        return toolbar

    def _build_bottom_bar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(36)
        bar.setStyleSheet(f"QFrame {{ background: {self.s['card_bg']}; border-top: 1px solid {self.s['border']}; }}")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(24)

        self.lbl_planlanan = QLabel("Planlanan: 0 adet")
        self.lbl_planlanan.setStyleSheet(f"color: {self.s['text_secondary']}; font-size: 11px;")
        layout.addWidget(self.lbl_planlanan)

        self.lbl_bekleyen = QLabel("Bekleyen: 0dk")
        self.lbl_bekleyen.setStyleSheet(f"color: {self.s['warning']}; font-size: 11px;")
        layout.addWidget(self.lbl_bekleyen)

        self.lbl_acil = QLabel("Acil: 0")
        self.lbl_acil.setStyleSheet(f"color: {self.s['error']}; font-size: 11px;")
        layout.addWidget(self.lbl_acil)

        layout.addStretch()
        for label, color in [("Cinko", "#F59E0B"), ("Cinko-Nikel", "#3B82F6"), ("Acil", "#EF4444")]:
            dot = QLabel(f"* {label}")
            dot.setStyleSheet(f"color: {color}; font-size: 11px;")
            layout.addWidget(dot)

        return bar

    # ── YARDIMCI UI ──

    def _section_label(self, parent, text: str):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {self.s['text_secondary']}; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;")
        if isinstance(parent, QVBoxLayout):
            parent.addWidget(lbl)
        elif isinstance(parent, QHBoxLayout):
            parent.addWidget(lbl)

    def _stat_card(self, label: str, value: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(f"""
            QFrame[frameShape="StyledPanel"] {{ background: {self.s['input_bg']};
                border: 1px solid {self.s['border']}; border-radius: 8px; padding: 8px; }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {self.s['text_muted']}; font-size: 10px;")
        layout.addWidget(lbl)
        val = QLabel(value)
        val.setObjectName("stat_value")
        val.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
        layout.addWidget(val)
        return frame

    def _update_stat(self, frame: QFrame, value: str):
        lbl = frame.findChild(QLabel, "stat_value")
        if lbl:
            lbl.setText(value)

    # ══════════════════════════════════════════════════════
    #  VERI ISLEMLERI
    # ══════════════════════════════════════════════════════

    def _init_data(self):
        db.ensure_tables()
        db.seed_recete_tanimlari()
        db.fix_hat_kodlari()
        db.sync_recete_sureleri()
        self._refresh_plc_data()
        self._load_plan()

        # 10sn'de bir PLC verisi yenile
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_plc_data)
        self._refresh_timer.start(10000)

    def _refresh_plc_data(self):
        """PLC cache'den canli verileri al ve tum gorsel bilesenleri guncelle"""
        try:
            # PLC canli veri
            self._plc_data = db.get_plc_canli()

            # Hat istatistikleri
            hat_stats = db.get_hat_istatistik()
            self.card_ktl.set_data("KTL Hatti", hat_stats.get('KTL', {}))
            self.card_cinko.set_data("Cinko-Nikel Hatti", hat_stats.get('ZNNI', {}))

            # Banyo kartlari
            self._update_banyo_cards()

            # Hat canli gorunum (tab 2)
            ktl_kazanlar = [k for k in self._plc_data if k.get('hat_kodu') == 'KTL']
            cinko_kazanlar = [k for k in self._plc_data if k.get('hat_kodu') == 'ZNNI']
            self.hat_ktl.set_kazanlar(ktl_kazanlar)
            self.hat_cinko.set_kazanlar(cinko_kazanlar)

            # Bara durum strip
            self._update_bara_strip()

            # Canli gosterge animasyonu
            self.lbl_canli.setStyleSheet(f"""
                color: {self.s['success']}; font-size: 10px; font-weight: bold;
                background: {self.s['success']}33; border: 1px solid {self.s['success']}66;
                border-radius: 4px; padding: 2px 8px;
            """)
            QTimer.singleShot(500, lambda: self.lbl_canli.setStyleSheet(f"""
                color: {self.s['success']}; font-size: 10px; font-weight: bold;
                background: {self.s['success']}22; border: 1px solid {self.s['success']}44;
                border-radius: 4px; padding: 2px 8px;
            """))

        except Exception as e:
            print(f"[KaplamaPlanlama] PLC veri guncelleme hatasi: {e}")

    def _update_banyo_cards(self):
        """Banyo kartlarini PLC verisinden olustur/guncelle"""
        # Onceki kartlari temizle
        for card in self.banyo_cards:
            card.deleteLater()
        self.banyo_cards.clear()

        # PLC verisinden banyo kartlari olustur (sadece aktif veya onemli kazanlar)
        for kz in self._plc_data:
            kazan_no = kz.get('kazan_no', 0)
            # Sadece ana hatlari goster (101+ veya 201+)
            if kazan_no < 100:
                continue

            # Banyo adi: pozisyon_adi (PLC'den otomatik)
            banyo_adi = kz.get('banyo_adi', f"K{kazan_no}")
            recete_adi = kz.get('recete_adi', '')
            recete_acik = kz.get('recete_aciklama', '')

            card = BanyoCard(self.s)
            card.set_data({
                'ad': banyo_adi,
                'kazan_no': kazan_no,
                'sicaklik': kz.get('sicaklik', 0),
                'sicaklik_min': kz.get('sicaklik_min', 0),
                'sicaklik_max': kz.get('sicaklik_max', 100),
                'sicaklik_hedef': kz.get('sicaklik_hedef', 0),
                'durum': kz.get('durum', 'BELIRSIZ'),
                'durum_dakika': kz.get('durum_dakika', 0),
                'recete_no': kz.get('recete_no'),
                'recete_adi': recete_adi,
                'recete_aciklama': recete_acik,
                'recete_sure_dk': kz.get('recete_sure_dk'),
                'akim': kz.get('akim', 0),
                'son_bara': kz.get('son_bara'),
                'hat_kodu': kz.get('hat_kodu', ''),
                'aktif_aski': 1 if kz.get('durum') == 'AKTIF' else 0,
                'max_aski': 4,
            })
            self.banyo_cards.append(card)
            self.banyo_cards_layout.addWidget(card)

        if not self.banyo_cards:
            # PLC verisi yoksa placeholder
            lbl = QLabel("PLC verisi bekleniyor...")
            lbl.setStyleSheet(f"color: {self.s['text_muted']}; font-size: 11px; padding: 20px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.banyo_cards_layout.addWidget(lbl)

    def _update_bara_strip(self):
        """11 bara icin durum strip'ini guncelle"""
        bara_data = []
        for i in range(1, BARA_SAYISI + 1):
            # Mevcut gorevlerden bu baradaki aktif gorev
            aktif_gorev = None
            for g in self.gorevler:
                if g.bara_no == i:
                    aktif_gorev = g
                    break

            if aktif_gorev:
                bara_data.append({
                    'bara_no': i,
                    'durum': 'PLANLANDI',
                    'urun_ref': aktif_gorev.urun_ref,
                })
            else:
                bara_data.append({'bara_no': i, 'durum': 'BOS'})

        self.bara_strip.set_data(bara_data)

    def _get_selected_monday(self) -> date:
        qd = self.date_edit.date()
        d = date(qd.year(), qd.month(), qd.day())
        return _monday_of_week(d)

    def _load_plan(self):
        monday = self._get_selected_monday()
        self.plan_id = db.get_or_create_plan(monday) or 0
        if self.plan_id:
            self.urunler = db.load_urunler(self.plan_id)
            self.gorevler = db.load_gorevler(self.plan_id)
        else:
            self.urunler = []
            self.gorevler = []
        self._refresh_ui()

    def _refresh_ui(self):
        self._refresh_urun_table()
        self.gantt.set_gorevler(self.gorevler)
        self._refresh_summary()
        self._update_bara_strip()

    def _refresh_urun_table(self):
        self.urun_table.setRowCount(len(self.urunler))
        for i, u in enumerate(self.urunler):
            self.urun_table.setItem(i, 0, QTableWidgetItem(u.ref))

            tip_item = QTableWidgetItem("ZnNi" if u.tip == "zn-ni" else "Zn")
            tip_item.setForeground(QColor("#3B82F6") if u.tip == "zn-ni" else QColor("#F59E0B"))
            self.urun_table.setItem(i, 1, tip_item)

            self.urun_table.setItem(i, 2, QTableWidgetItem(f"{u.haftalik_ihtiyac:,}"))

            aski_item = QTableWidgetItem(f"{u.stok_aski}x{u.kapasite}")
            if not u.aski_yeterli:
                aski_item.setForeground(QColor("#EF4444"))
            self.urun_table.setItem(i, 3, aski_item)

            self.urun_table.setItem(i, 4, QTableWidgetItem(f"{u.gerekli_bara}"))
            self.urun_table.setItem(i, 5, QTableWidgetItem(f"{u.toplam_cevrim}x{u.cevrim_suresi}dk"))

            oncelik_item = QTableWidgetItem(u.oncelik.upper())
            if u.oncelik == "acil":
                oncelik_item.setForeground(QColor("#EF4444"))
            self.urun_table.setItem(i, 6, oncelik_item)

    def _refresh_summary(self):
        toplam_aski_yukleme = sum(g.aski_sayisi for g in self.gorevler)
        toplam_parca = 0
        for u in self.urunler:
            urun_gorevleri = [g for g in self.gorevler if g.urun_ref == u.ref]
            toplam_gorev_sure = sum(g.sure_dk for g in urun_gorevleri)
            cevrim_sayisi = toplam_gorev_sure // u.cevrim_suresi if u.cevrim_suresi > 0 else 0
            toplam_parca += cevrim_sayisi * u.stok_aski * u.kapasite

        kullanilan_slotlar = set()
        for g in self.gorevler:
            kullanilan_slotlar.add((g.bara_no, g.gun, g.vardiya))
        max_slots = BARA_SAYISI * GUN_SAYISI * VARDIYA_SAYISI
        kullanim = int((len(kullanilan_slotlar) / max_slots * 100)) if max_slots > 0 else 0

        self._update_stat(self.lbl_toplam_aski, f"{toplam_aski_yukleme:,}")
        self._update_stat(self.lbl_toplam_parca, f"{toplam_parca:,}")
        self._update_stat(self.lbl_bara_kullanim, f"%{kullanim}")
        durum = db.get_plan_durum(self.plan_id) if self.plan_id else "taslak"
        self._update_stat(self.lbl_plan_durum, durum.capitalize())

        planlanan_sure = sum(g.sure_dk for g in self.gorevler)
        toplam_ihtiyac_sure = sum(u.toplam_sure_dk for u in self.urunler)
        bekleyen_sure = max(0, toplam_ihtiyac_sure - planlanan_sure)
        acil_sayisi = sum(1 for g in self.gorevler if g.acil)

        self.lbl_planlanan.setText(f"Planlanan: {toplam_parca:,} adet")
        self.lbl_bekleyen.setText(f"Bekleyen: {bekleyen_sure}dk")
        self.lbl_acil.setText(f"Acil: {acil_sayisi}")

    # ══════════════════════════════════════════════════════
    #  OLAY ISLEYICILERI
    # ══════════════════════════════════════════════════════

    def _on_hafta_degisti(self):
        self._load_plan()

    def _on_urun_ekle(self):
        dialog = UrunEkleDialog(self.s, self)
        if dialog.exec() == QDialog.Accepted:
            urun = dialog.get_urun()
            urun.id = len(self.urunler) + 1
            self.urunler.append(urun)
            self._refresh_ui()

    def _on_urun_sil(self):
        row = self.urun_table.currentRow()
        if row < 0:
            return
        ref = self.urunler[row].ref
        self.gorevler = [g for g in self.gorevler if g.urun_ref != ref]
        self.urunler.pop(row)
        self._refresh_ui()

    def _on_urun_table_clicked(self):
        """Urun tablosunda satir secildiginde recete goster"""
        row = self.urun_table.currentRow()
        if row < 0 or row >= len(self.urunler):
            return
        urun = self.urunler[row]
        recete = db.get_urun_recete(urun.ref)
        if recete:
            self.recete_widget.set_adimlar(recete)
            toplam_sn = sum(a['sure_sn'] for a in recete)
            self.lbl_recete_toplam.setText(
                f"{urun.ref}: {len(recete)} adim, toplam {toplam_sn}sn ({toplam_sn // 60}dk {toplam_sn % 60}sn)"
            )
        else:
            self.recete_widget.set_adimlar([])
            self.lbl_recete_toplam.setText(f"{urun.ref}: Recete bulunamadi")

    def _on_temizle(self):
        reply = QMessageBox.question(self, "Temizle", "Tum gorevler silinecek. Emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.gorevler = []
            self._refresh_ui()

    def _on_otomatik_planla(self):
        if not self.urunler:
            QMessageBox.warning(self, "Uyari", "Planlamak icin once urun ekleyin.")
            return
        sonuc = otomatik_planla(self.urunler)
        self.gorevler = sonuc.gorevler
        self._refresh_ui()
        if sonuc.uyarilar:
            msg = "\n".join(sonuc.uyarilar)
            QMessageBox.information(self, "Planlama Sonucu", msg)

    def _on_kaydet(self):
        if not self.plan_id:
            QMessageBox.warning(self, "Hata", "Plan olusturulamadi.")
            return
        ok1 = db.save_urunler(self.plan_id, self.urunler)
        if ok1:
            self.urunler = db.load_urunler(self.plan_id)
            ok2 = db.save_gorevler(self.plan_id, self.urunler, self.gorevler)
            if ok2:
                QMessageBox.information(self, "Basarili", "Plan kaydedildi.")
                self._load_plan()
                return
        QMessageBox.warning(self, "Hata", "Plan kaydedilemedi.")

    def _on_gorev_silindi(self, gorev: PlanGorev):
        self.gorevler = self.gantt.get_gorevler()
        self._refresh_summary()


# ══════════════════════════════════════════════════════════════
#  URUN EKLE DIALOG
# ══════════════════════════════════════════════════════════════

class UrunEkleDialog(QDialog):
    """Urun ekleme dialog'u - Stok kartindan arama ile"""

    def __init__(self, style: dict, parent=None):
        super().__init__(parent)
        self.s = style
        self.selected_urun = None
        self._sonuclar = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(400)
        self._search_timer.timeout.connect(self._do_search)
        self.setWindowTitle("Stok Kartindan Urun Ekle")
        self.setMinimumWidth(650)
        self.setMinimumHeight(580)
        self.setStyleSheet(f"QDialog {{ background: {self.s['card_bg']}; color: {self.s['text']}; }}")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        input_style = f"""
            QLineEdit, QSpinBox, QComboBox {{ background: {self.s['input_bg']}; color: {self.s['text']};
                border: 1px solid {self.s['border']}; border-radius: 6px; padding: 7px; min-height: 18px; }}
        """
        label_style = f"color: {self.s['text_secondary']}; font-size: 11px;"

        # Arama
        lbl_ara = QLabel("Urun Ara (Kod / Ad)")
        lbl_ara.setStyleSheet(f"color: {self.s['text']}; font-size: 13px; font-weight: bold;")
        layout.addWidget(lbl_ara)

        self.txt_arama = QLineEdit()
        self.txt_arama.setPlaceholderText("Urun kodu veya adi yazin...")
        self.txt_arama.setStyleSheet(input_style)
        self.txt_arama.textChanged.connect(lambda: self._search_timer.start())
        layout.addWidget(self.txt_arama)

        # Sonuc tablosu
        self.sonuc_table = QTableWidget()
        self.sonuc_table.setColumnCount(5)
        self.sonuc_table.setHorizontalHeaderLabels(["Urun Kodu", "Urun Adi", "Kaplama", "Aski", "Bara"])
        self.sonuc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sonuc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.sonuc_table.verticalHeader().setVisible(False)
        self.sonuc_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sonuc_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sonuc_table.setMaximumHeight(160)
        self.sonuc_table.setStyleSheet(f"""
            QTableWidget {{ background: {self.s['input_bg']}; border: 1px solid {self.s['border']};
                border-radius: 8px; gridline-color: {self.s['border']}; color: {self.s['text']}; font-size: 11px; }}
            QHeaderView::section {{ background: {self.s['card_bg']}; color: {self.s['text_secondary']};
                border: none; border-bottom: 1px solid {self.s['border']}; padding: 5px; font-weight: bold; font-size: 10px; }}
            QTableWidget::item:selected {{ background: {self.s['primary']}33; }}
        """)
        self.sonuc_table.cellClicked.connect(self._on_sonuc_secildi)
        layout.addWidget(self.sonuc_table)

        # Secilen urun + recete onizleme
        self.lbl_secilen = QLabel("Henuz urun secilmedi")
        self.lbl_secilen.setStyleSheet(f"color: {self.s['text_muted']}; font-size: 11px; padding: 2px;")
        layout.addWidget(self.lbl_secilen)

        # Recete adimlari
        self.recete_preview = ReceteAdimWidget()
        layout.addWidget(self.recete_preview)

        # Stok karti bilgileri
        info_frame = QFrame()
        info_frame.setStyleSheet(f"QFrame {{ background: {self.s['input_bg']}; border: 1px solid {self.s['border']}; border-radius: 8px; padding: 6px; }}")
        info_layout = QGridLayout(info_frame)
        info_layout.setSpacing(6)

        def add_info(row, col, label_text, obj_name):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            val = QLabel("-")
            val.setObjectName(obj_name)
            val.setStyleSheet(f"color: {self.s['text']}; font-size: 11px; font-weight: bold;")
            info_layout.addWidget(lbl, row, col * 2)
            info_layout.addWidget(val, row, col * 2 + 1)

        add_info(0, 0, "Recete:", "info_recete")
        add_info(0, 1, "Kaplama:", "info_kaplama")
        add_info(1, 0, "Aski Tipi:", "info_aski_tip")
        add_info(1, 1, "Aski Adedi:", "info_aski_adedi")

        layout.addWidget(info_frame)

        # Recete secimi
        lbl_rec = QLabel("Recete Sec")
        lbl_rec.setStyleSheet(f"color: {self.s['text']}; font-size: 12px; font-weight: bold; margin-top: 4px;")
        layout.addWidget(lbl_rec)

        self.cmb_recete = QComboBox()
        self.cmb_recete.setStyleSheet(input_style)
        self.cmb_recete.currentIndexChanged.connect(self._on_recete_secildi)
        layout.addWidget(self.cmb_recete)

        self.lbl_cevrim_info = QLabel("")
        self.lbl_cevrim_info.setStyleSheet(f"color: {self.s['text_muted']}; font-size: 10px;")
        layout.addWidget(self.lbl_cevrim_info)

        # Kullanici alanlari
        form_layout = QFormLayout()
        form_layout.setSpacing(6)

        self.spn_cevrim = QSpinBox()
        self.spn_cevrim.setRange(1, 480)
        self.spn_cevrim.setValue(45)
        self.spn_cevrim.setSuffix(" dk")
        self.spn_cevrim.setStyleSheet(input_style)

        self.spn_stok_aski = QSpinBox()
        self.spn_stok_aski.setRange(0, 9999)
        self.spn_stok_aski.setValue(0)
        self.spn_stok_aski.setStyleSheet(input_style)

        self.spn_bara_aski = QSpinBox()
        self.spn_bara_aski.setRange(1, 99)
        self.spn_bara_aski.setValue(2)
        self.spn_bara_aski.setStyleSheet(input_style)

        self.spn_kapasite = QSpinBox()
        self.spn_kapasite.setRange(1, 9999)
        self.spn_kapasite.setValue(1)
        self.spn_kapasite.setToolTip("Bir askiya kac adet urun asilir")
        self.spn_kapasite.setStyleSheet(input_style)

        self.spn_ihtiyac = QSpinBox()
        self.spn_ihtiyac.setRange(0, 999999)
        self.spn_ihtiyac.setValue(100)
        self.spn_ihtiyac.setStyleSheet(input_style)

        self.cmb_oncelik = QComboBox()
        self.cmb_oncelik.addItems(["Normal", "Acil"])
        self.cmb_oncelik.setStyleSheet(input_style)

        for label, widget in [
            ("Cevrim Suresi:", self.spn_cevrim),
            ("Aski Stoku (adet):", self.spn_stok_aski),
            ("Bara Basina Aski:", self.spn_bara_aski),
            ("Aski Kapasitesi:", self.spn_kapasite),
            ("Haftalik Ihtiyac:", self.spn_ihtiyac),
            ("Oncelik:", self.cmb_oncelik),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(label_style)
            form_layout.addRow(lbl, widget)

        layout.addLayout(form_layout)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_iptal = QPushButton("Iptal")
        btn_iptal.setCursor(Qt.PointingHandCursor)
        btn_iptal.setStyleSheet(f"QPushButton {{ background: transparent; color: {self.s['text_secondary']}; border: 1px solid {self.s['border']}; border-radius: 6px; padding: 8px 20px; }}")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)

        btn_ekle = QPushButton("Ekle")
        btn_ekle.setCursor(Qt.PointingHandCursor)
        btn_ekle.setStyleSheet(f"QPushButton {{ background: {self.s['primary']}; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: bold; }}")
        btn_ekle.clicked.connect(self._on_ekle)
        btn_layout.addWidget(btn_ekle)

        layout.addLayout(btn_layout)

    def _do_search(self):
        arama = self.txt_arama.text().strip()
        if len(arama) < 2:
            self.sonuc_table.setRowCount(0)
            return
        sonuclar = db.search_stok_kartlari(arama)
        self._sonuclar = sonuclar
        self.sonuc_table.setRowCount(len(sonuclar))
        for i, s in enumerate(sonuclar):
            self.sonuc_table.setItem(i, 0, QTableWidgetItem(s['urun_kodu']))
            self.sonuc_table.setItem(i, 1, QTableWidgetItem(s['urun_adi'] or ''))
            self.sonuc_table.setItem(i, 2, QTableWidgetItem(s['kaplama_adi'] or '-'))
            self.sonuc_table.setItem(i, 3, QTableWidgetItem(str(s['aski_adedi'])))
            self.sonuc_table.setItem(i, 4, QTableWidgetItem(str(s['bara_adedi'])))

    def _on_sonuc_secildi(self, row, col):
        if row < 0 or row >= len(self._sonuclar):
            return
        s = self._sonuclar[row]
        self.selected_urun = s

        self.lbl_secilen.setText(f"Secilen: {s['urun_kodu']} - {s['urun_adi'] or ''}")
        self.lbl_secilen.setStyleSheet(f"color: {self.s['success']}; font-size: 11px; font-weight: bold; padding: 2px;")

        self.findChild(QLabel, "info_recete").setText(s['recete_no'] or '-')
        self.findChild(QLabel, "info_kaplama").setText(s['kaplama_adi'] or '-')
        self.findChild(QLabel, "info_aski_tip").setText(s['aski_tip_adi'] or '-')
        self.findChild(QLabel, "info_aski_adedi").setText(str(s['aski_adedi']) if s['aski_adedi'] else '-')

        # Stok kartından askı/bara otomatik doldur
        if s['aski_adedi'] and s['aski_adedi'] > 0:
            self.spn_stok_aski.setValue(s['aski_adedi'])
        if s['bara_adedi'] and s['bara_adedi'] > 0:
            self.spn_bara_aski.setValue(s['bara_adedi'])

        # Recete secimi icin combobox'u doldur
        self.cmb_recete.clear()
        recete_no_str = s.get('recete_no', '')
        # Stok kartindaki recete no
        if recete_no_str:
            try:
                rec_no = int(recete_no_str)
                tanim = db.get_recete_by_no(rec_no)
                if tanim:
                    self.cmb_recete.addItem(
                        f"R{rec_no} - {tanim.get('recete_adi', '')} / {tanim.get('recete_aciklama', '')} ({tanim.get('toplam_sure_dk', '?')}dk)",
                        rec_no
                    )
            except (ValueError, TypeError):
                pass

        # Kaplama turune gore diger receteler
        kaplama = (s.get('kaplama_kodu') or '').lower()
        if 'ni' in kaplama or 'nikel' in kaplama:
            hat_tipi = 'ZNNI'
        elif 'ktl' in kaplama or 'kat' in kaplama:
            hat_tipi = 'KTL'
        else:
            hat_tipi = None

        if hat_tipi:
            tum_receteler = db.get_recete_tanimlari(hat_tipi)
            existing_nos = [self.cmb_recete.itemData(i) for i in range(self.cmb_recete.count())]
            for rt in tum_receteler:
                if rt['recete_no'] not in existing_nos:
                    sure_str = f"{rt['toplam_sure_dk']}dk" if rt['toplam_sure_dk'] else "?"
                    self.cmb_recete.addItem(
                        f"R{rt['recete_no']} - {rt['recete_adi']} / {rt['recete_aciklama']} ({sure_str})",
                        rt['recete_no']
                    )

        # Ilk receteyi sec ve suresi otomatik ayarla
        self._on_recete_secildi()

        # ERP recete adimlari (stok.urun_recete)
        recete = db.get_urun_recete(s['urun_kodu'])
        if recete:
            self.recete_preview.set_adimlar(recete)
        else:
            self.recete_preview.set_adimlar([])

    def _on_recete_secildi(self):
        """Recete combobox secildiginde cevrim suresini otomatik ayarla"""
        rec_no = self.cmb_recete.currentData()
        if rec_no is None:
            return
        tanim = db.get_recete_by_no(rec_no)
        if tanim and tanim.get('toplam_sure_dk'):
            self.spn_cevrim.setValue(tanim['toplam_sure_dk'])
            self.lbl_cevrim_info.setText(
                f"PLC'den hesaplanan: {tanim['toplam_sure_dk']} dk (adim toplami)"
            )
            self.lbl_cevrim_info.setStyleSheet(f"color: {self.s['success']}; font-size: 10px;")
        else:
            self.lbl_cevrim_info.setText("PLC verisi bulunamadi - manuel girin")
            self.lbl_cevrim_info.setStyleSheet(f"color: {self.s['warning']}; font-size: 10px;")

    def _on_ekle(self):
        if not self.selected_urun:
            QMessageBox.warning(self, "Uyari", "Lutfen listeden bir urun secin.")
            return
        self.accept()

    def get_urun(self) -> KaplamaUrun:
        s = self.selected_urun
        kaplama = (s.get('kaplama_kodu') or '').lower()
        tip = "zn-ni" if ('ni' in kaplama or 'nikel' in kaplama) else "zn"
        oncelik = "acil" if self.cmb_oncelik.currentIndex() == 1 else "normal"

        # Secilen recete no
        rec_no = self.cmb_recete.currentData()
        recete_str = str(rec_no) if rec_no else s.get('recete_no', '')

        return KaplamaUrun(
            ref=s['urun_kodu'],
            recete_no=recete_str,
            tip=tip,
            aski_tip=s.get('aski_tip_kodu', ''),
            kapasite=self.spn_kapasite.value(),
            cevrim_suresi=self.spn_cevrim.value(),
            stok_aski=self.spn_stok_aski.value(),
            bara_aski=self.spn_bara_aski.value(),
            haftalik_ihtiyac=self.spn_ihtiyac.value(),
            oncelik=oncelik,
        )
