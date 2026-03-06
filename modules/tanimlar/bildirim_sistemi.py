# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Bildirim ve Uyarı Sistemi
Kullanıcı bazlı bildirim merkezi
[MODERNIZED UI - v3.0 - Kullanıcı bazlı]
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QCheckBox, QFrame, QScrollArea,
    QListWidget, QListWidgetItem, QTextEdit, QTabWidget,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection


# ============================================================================
# STYLE & CONSTANTS
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


ONEM_COLORS = {
    'KRITIK': '#ef4444',
    'YUKSEK': '#f97316',
    'NORMAL': '#3b82f6',
    'DUSUK': '#6b7280',
}

MODUL_ICONS = {
    'KALITE': '✅', 'URETIM': '🏭', 'BAKIM': '🔧', 'IK': '👥',
    'STOK': '📦', 'SEVKIYAT': '🚚', 'SISTEM': '⚙️', 'IS_EMIRLERI': '📋',
    'ISG': '🦺', 'SATINALMA': '🛒', 'LAB': '🔬', 'CEVRE': '🌿',
}

TIP_ICONS = {
    'BILGI': '💬',
    'UYARI': '⚠️',
    'GOREV': '📌',
    'ONAY_BEKLIYOR': '✋',
    'HATIRLATMA': '🔔',
}


# ============================================================================
# BİLDİRİM DETAY DIALOG
# ============================================================================
class BildirimDetayDialog(QDialog):
    """Bildirim detay dialogu"""

    def __init__(self, theme: dict, bildirim_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.data = bildirim_data
        self.setWindowTitle("Bildirim Detayi")
        self.setMinimumSize(550, 450)
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
            QLabel {{ color: {s['text']}; background: transparent; }}
            QTextEdit {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 14px;
                color: {s['text']};
                font-size: 13px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        lbl_baslik = QLabel(self.data.get('baslik', ''))
        lbl_baslik.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {s['text']};")
        lbl_baslik.setWordWrap(True)
        layout.addWidget(lbl_baslik)

        # Meta bilgiler
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(12)

        modul = self.data.get('modul', '')
        icon = MODUL_ICONS.get(modul, '📋')
        lbl_modul = QLabel(f"{icon} {modul}")
        lbl_modul.setStyleSheet(f"""
            color: {s['text']}; background: {s['border']};
            padding: 6px 12px; border-radius: 6px; font-size: 12px;
        """)
        meta_layout.addWidget(lbl_modul)

        onem = self.data.get('onem_derecesi', 'NORMAL')
        color = ONEM_COLORS.get(onem, '#6b7280')
        lbl_onem = QLabel(f"● {onem}")
        lbl_onem.setStyleSheet(f"""
            color: white; background: {color};
            padding: 6px 12px; border-radius: 6px;
            font-size: 12px; font-weight: bold;
        """)
        meta_layout.addWidget(lbl_onem)

        tip = self.data.get('tip', '')
        if tip:
            tip_icon = TIP_ICONS.get(tip, '')
            lbl_tip = QLabel(f"{tip_icon} {tip}")
            lbl_tip.setStyleSheet(f"""
                color: {s['text_secondary']}; background: {s['border']};
                padding: 6px 12px; border-radius: 6px; font-size: 12px;
            """)
            meta_layout.addWidget(lbl_tip)

        tarih = self.data.get('olusturma_tarihi')
        if tarih:
            tarih_str = tarih.strftime("%d.%m.%Y %H:%M") if hasattr(tarih, 'strftime') else str(tarih)
            lbl_tarih = QLabel(tarih_str)
            lbl_tarih.setStyleSheet(f"color: {s['text_muted']}; font-size: 12px;")
            meta_layout.addWidget(lbl_tarih)

        meta_layout.addStretch()
        layout.addLayout(meta_layout)

        # Gönderen bilgisi
        gonderen = self.data.get('gonderen_adi')
        if gonderen:
            lbl_gonderen = QLabel(f"Gonderen: {gonderen}")
            lbl_gonderen.setStyleSheet(f"color: {s['text_secondary']}; font-size: 12px;")
            layout.addWidget(lbl_gonderen)

        # Ayırıcı
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {s['border']}; max-height: 1px;")
        layout.addWidget(sep)

        # Mesaj
        txt_mesaj = QTextEdit()
        txt_mesaj.setReadOnly(True)
        txt_mesaj.setPlainText(self.data.get('mesaj') or 'Detay bilgisi yok.')
        layout.addWidget(txt_mesaj, 1)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_kapat = QPushButton("Kapat")
        btn_kapat.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']}; color: white;
                border: none; border-radius: 8px;
                padding: 12px 28px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        btn_kapat.clicked.connect(self.accept)
        btn_layout.addWidget(btn_kapat)
        layout.addLayout(btn_layout)


# ============================================================================
# BİLDİRİM KART WIDGET
# ============================================================================
class BildirimWidget(QFrame):
    """Tek bildirim kartı"""
    clicked = Signal(dict)

    def __init__(self, bildirim_data: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.data = bildirim_data
        self.okundu = bildirim_data.get('okundu_mu', False)
        self._setup_ui()

    def _setup_ui(self):
        s = self.s
        bg = s['card_bg'] if self.okundu else s['input_bg']
        onem = self.data.get('onem_derecesi', 'NORMAL')
        border_color = s['border'] if self.okundu else ONEM_COLORS.get(onem, '#3b82f6')

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {s['border']};
                border-left: 4px solid {border_color};
                border-radius: 10px;
            }}
            QFrame:hover {{ background: {s['border']}; }}
        """)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(70)

        if not self.okundu:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setXOffset(0)
            shadow.setYOffset(2)
            shadow.setColor(QColor(0, 0, 0, 40))
            self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(6)

        # Üst satır: ikon + başlık + önem + tip
        header_layout = QHBoxLayout()
        modul = self.data.get('modul', '')
        icon = MODUL_ICONS.get(modul, '📋')
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 18px;")
        header_layout.addWidget(lbl_icon)

        lbl_baslik = QLabel(self.data.get('baslik', ''))
        weight = 'normal' if self.okundu else 'bold'
        lbl_baslik.setStyleSheet(f"font-weight: {weight}; color: {s['text']}; font-size: 14px;")
        header_layout.addWidget(lbl_baslik)
        header_layout.addStretch()

        # Tip badge
        tip = self.data.get('tip', '')
        if tip:
            tip_icon = TIP_ICONS.get(tip, '')
            lbl_tip = QLabel(tip_icon)
            lbl_tip.setStyleSheet("font-size: 14px;")
            lbl_tip.setToolTip(tip)
            header_layout.addWidget(lbl_tip)

        color = ONEM_COLORS.get(onem, '#6b7280')
        lbl_onem = QLabel(f"● {onem}")
        lbl_onem.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(lbl_onem)

        content_layout.addLayout(header_layout)

        # Alt satır: tarih + gönderen
        alt_layout = QHBoxLayout()
        tarih = self.data.get('olusturma_tarihi')
        if tarih:
            tarih_str = tarih.strftime("%d.%m.%Y %H:%M") if hasattr(tarih, 'strftime') else str(tarih)
            lbl_tarih = QLabel(tarih_str)
            lbl_tarih.setStyleSheet(f"color: {s['text_muted']}; font-size: 11px;")
            alt_layout.addWidget(lbl_tarih)

        gonderen = self.data.get('gonderen_adi')
        if gonderen:
            lbl_gonderen = QLabel(f"— {gonderen}")
            lbl_gonderen.setStyleSheet(f"color: {s['text_muted']}; font-size: 11px;")
            alt_layout.addWidget(lbl_gonderen)

        alt_layout.addStretch()
        content_layout.addLayout(alt_layout)

        layout.addLayout(content_layout)

    def mousePressEvent(self, event):
        self.clicked.emit(self.data)


# ============================================================================
# ANA SAYFA
# ============================================================================
class BildirimSistemiPage(BasePage):
    """Bildirim Merkezi Sayfasi - Kullanici bazli"""
    bildirim_sayisi_degisti = Signal(int)

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.all_bildirimler = []
        self._current_user_id = None
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def set_user(self, user_id: int):
        """Aktif kullanıcıyı ayarla ve bildirimleri yükle."""
        self._current_user_id = user_id
        self._load_data()

    def _get_user_id(self) -> int:
        """Aktif kullanıcı ID'sini al."""
        if self._current_user_id:
            return self._current_user_id
        try:
            from core.yetki_manager import YetkiManager
            return YetkiManager._current_user_id
        except Exception:
            return None

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
        icon = QLabel("🔔")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Bildirim Merkezi")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)

        self.lbl_unread = QLabel()
        self.lbl_unread.setStyleSheet(f"""
            color: white; background: {s['error']};
            padding: 4px 12px; border-radius: 12px;
            font-size: 12px; font-weight: bold;
        """)
        self.lbl_unread.hide()
        title_row.addWidget(self.lbl_unread)
        title_row.addStretch()
        title_section.addLayout(title_row)

        subtitle = QLabel("Kisisel bildirimlerinizi yonetin")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        layout.addLayout(header)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {s['border']};
                background: {s['card_bg']};
                border-radius: 10px; padding: 16px;
            }}
            QTabBar::tab {{
                background: transparent; padding: 12px 24px;
                color: {s['text_muted']}; font-weight: 500;
                border: none; border-bottom: 3px solid transparent;
            }}
            QTabBar::tab:hover {{
                color: {s['text']}; background: rgba(255,255,255,0.05);
            }}
            QTabBar::tab:selected {{
                color: {s['primary']}; border-bottom-color: {s['primary']};
            }}
        """)

        # Tab 1: Bildirimler
        tab_bildirimler = QWidget()
        bildirim_layout = QVBoxLayout(tab_bildirimler)
        bildirim_layout.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        combo_style = f"""
            QComboBox {{
                background: {s['input_bg']}; border: 1px solid {s['border']};
                border-radius: 8px; padding: 8px 12px;
                color: {s['text']}; min-width: 120px; font-size: 13px;
            }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']}; border: 1px solid {s['border']};
                color: {s['text']}; selection-background-color: {s['primary']};
            }}
        """

        self.cmb_modul = QComboBox()
        self.cmb_modul.addItem("Tum Moduller", None)
        for kod, m_icon in MODUL_ICONS.items():
            self.cmb_modul.addItem(f"{m_icon} {kod}", kod)
        self.cmb_modul.setStyleSheet(combo_style)
        self.cmb_modul.currentIndexChanged.connect(self._filter)
        toolbar.addWidget(self.cmb_modul)

        self.cmb_durum = QComboBox()
        self.cmb_durum.addItem("Tumu")
        self.cmb_durum.addItem("Okunmamis")
        self.cmb_durum.addItem("Okunmus")
        self.cmb_durum.setStyleSheet(combo_style)
        self.cmb_durum.currentIndexChanged.connect(self._filter)
        toolbar.addWidget(self.cmb_durum)

        self.cmb_tip = QComboBox()
        self.cmb_tip.addItem("Tum Tipler", None)
        for tip_kod, tip_icon in TIP_ICONS.items():
            self.cmb_tip.addItem(f"{tip_icon} {tip_kod}", tip_kod)
        self.cmb_tip.setStyleSheet(combo_style)
        self.cmb_tip.currentIndexChanged.connect(self._filter)
        toolbar.addWidget(self.cmb_tip)

        toolbar.addStretch()

        btn_style = f"""
            QPushButton {{
                background: {s['input_bg']}; color: {s['text']};
                border: 1px solid {s['border']}; border-radius: 8px;
                padding: 8px 16px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {s['border']}; border-color: {s['primary']}; }}
        """

        btn_tumunu_oku = QPushButton("Tumunu Okundu Isaretle")
        btn_tumunu_oku.setStyleSheet(btn_style)
        btn_tumunu_oku.clicked.connect(self._mark_all_read)
        toolbar.addWidget(btn_tumunu_oku)

        btn_temizle = QPushButton("Eski Temizle")
        btn_temizle.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']}; color: {s['text']};
                border: 1px solid {s['border']}; border-radius: 8px;
                padding: 8px 16px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {s['error']}; border-color: {s['error']}; }}
        """)
        btn_temizle.clicked.connect(self._clear_old)
        toolbar.addWidget(btn_temizle)

        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']}; border: 1px solid {s['border']};
                border-radius: 8px; padding: 8px 16px; color: {s['text']};
            }}
            QPushButton:hover {{ background: {s['border']}; }}
        """)
        btn_yenile.clicked.connect(self._load_data)
        toolbar.addWidget(btn_yenile)
        bildirim_layout.addLayout(toolbar)

        # Bildirim listesi scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {s['card_bg']}; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {s['border']}; border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {s['primary']}; }}
        """)

        self.bildirim_container = QWidget()
        self.bildirim_list_layout = QVBoxLayout(self.bildirim_container)
        self.bildirim_list_layout.setSpacing(10)
        self.bildirim_list_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.bildirim_container)
        bildirim_layout.addWidget(scroll)
        tabs.addTab(tab_bildirimler, "Bildirimler")

        # Tab 2: Sistem Durumu
        tab_durum = QWidget()
        durum_layout = QVBoxLayout(tab_durum)
        durum_layout.setSpacing(16)

        durum_label = QLabel("Sistemdeki aktif uyarilar ve durumlar")
        durum_label.setStyleSheet(f"font-weight: bold; color: {s['text']}; font-size: 14px;")
        durum_layout.addWidget(durum_label)

        self.durum_list = QListWidget()
        self.durum_list.setStyleSheet(f"""
            QListWidget {{
                background: {s['card_bg']}; border: 1px solid {s['border']};
                border-radius: 10px; color: {s['text']};
            }}
            QListWidget::item {{
                padding: 16px; border-bottom: 1px solid {s['border']};
            }}
            QListWidget::item:hover {{ background: {s['border']}; }}
        """)
        durum_layout.addWidget(self.durum_list)

        btn_kontrol = QPushButton("Sistem Kontrolu Yap")
        btn_kontrol.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']}; color: white;
                border: none; border-radius: 8px;
                padding: 12px 24px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        btn_kontrol.clicked.connect(self._run_system_check)
        durum_layout.addWidget(btn_kontrol)
        tabs.addTab(tab_durum, "Sistem Durumu")

        layout.addWidget(tabs)

    # ========================================================================
    # DATA METHODS - KULLANICI BAZLI
    # ========================================================================

    def _load_data(self):
        self._load_bildirimler()

    def _load_bildirimler(self):
        s = self.s

        # Eski widget'ları temizle
        while self.bildirim_list_layout.count():
            item = self.bildirim_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        user_id = self._get_user_id()
        if not user_id:
            lbl = QLabel("Kullanici bilgisi alinamadi. Tekrar giris yapiniz.")
            lbl.setStyleSheet(f"color: {s['text_muted']}; padding: 40px; font-size: 14px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.bildirim_list_layout.addWidget(lbl)
            return

        try:
            from core.bildirim_service import BildirimService

            self.all_bildirimler = BildirimService.kullanici_bildirimleri(
                kullanici_id=user_id, limit=100
            )
            unread_count = BildirimService.okunmamis_sayisi(user_id)

            self._display_bildirimler(self.all_bildirimler)

            if unread_count > 0:
                self.lbl_unread.setText(f"{unread_count} Okunmamis")
                self.lbl_unread.show()
            else:
                self.lbl_unread.hide()

            self.bildirim_sayisi_degisti.emit(unread_count)

        except Exception as e:
            lbl_empty = QLabel(f"Bildirim yuklenirken hata: {str(e)[:80]}")
            lbl_empty.setStyleSheet(f"color: {s['text_muted']}; padding: 40px; font-size: 14px;")
            lbl_empty.setAlignment(Qt.AlignCenter)
            self.bildirim_list_layout.addWidget(lbl_empty)

    def _display_bildirimler(self, bildirimler):
        s = self.s
        if not bildirimler:
            lbl_empty = QLabel("Bildirim bulunamadi")
            lbl_empty.setStyleSheet(f"color: {s['text_muted']}; padding: 40px; font-size: 14px;")
            lbl_empty.setAlignment(Qt.AlignCenter)
            self.bildirim_list_layout.addWidget(lbl_empty)
            return

        for b in bildirimler:
            widget = BildirimWidget(b, self.theme)
            widget.clicked.connect(self._show_bildirim_detay)
            self.bildirim_list_layout.addWidget(widget)
        self.bildirim_list_layout.addStretch()

    def _filter(self):
        modul = self.cmb_modul.currentData()
        durum = self.cmb_durum.currentText()
        tip = self.cmb_tip.currentData()

        filtered = []
        for b in self.all_bildirimler:
            if modul and b.get('modul') != modul:
                continue
            if durum == "Okunmamis" and b.get('okundu_mu'):
                continue
            if durum == "Okunmus" and not b.get('okundu_mu'):
                continue
            if tip and b.get('tip') != tip:
                continue
            filtered.append(b)

        while self.bildirim_list_layout.count():
            item = self.bildirim_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._display_bildirimler(filtered)

    def _show_bildirim_detay(self, bildirim_data: dict):
        # Okundu işaretle
        user_id = self._get_user_id()
        if user_id and not bildirim_data.get('okundu_mu'):
            try:
                from core.bildirim_service import BildirimService
                BildirimService.okundu_isaretle(bildirim_data['id'], user_id)
            except Exception:
                pass

        dialog = BildirimDetayDialog(self.theme, bildirim_data, self)
        dialog.exec()
        self._load_bildirimler()

    def _mark_all_read(self):
        user_id = self._get_user_id()
        if not user_id:
            return

        try:
            from core.bildirim_service import BildirimService
            BildirimService.tumunu_okundu_isaretle(user_id)
            self._load_bildirimler()
            QMessageBox.information(self, "Basarili", "Tum bildirimler okundu olarak isaretlendi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")

    def _clear_old(self):
        reply = QMessageBox.question(
            self, "Temizleme Onayi",
            "30 gunden eski ve okunmus bildirimleri silmek istediginize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                from core.bildirim_service import BildirimService
                deleted = BildirimService.eski_temizle(30)
                self._load_bildirimler()
                QMessageBox.information(self, "Basarili", f"{deleted} eski bildirim temizlendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")

    def _run_system_check(self):
        s = self.s
        self.durum_list.clear()
        checks = []

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM kalite.kalibrasyon_planlari
                    WHERE sonraki_kalibrasyon_tarihi < GETDATE() AND aktif_mi = 1
                """)
                count = cursor.fetchone()[0]
                if count > 0:
                    checks.append(('KRITIK', f'{count} cihazin kalibrasyon suresi dolmus!'))
            except Exception:
                pass

            try:
                cursor.execute("SELECT COUNT(*) FROM kalite.uygunsuzluklar WHERE durum = 'ACIK'")
                count = cursor.fetchone()[0]
                if count > 0:
                    checks.append(('YUKSEK', f'{count} acik uygunsuzluk kaydi var'))
            except Exception:
                pass

            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM sistem.aksiyonlar
                    WHERE durum = 'GECIKTI' AND aktif_mi = 1 AND silindi_mi = 0
                """)
                count = cursor.fetchone()[0]
                if count > 0:
                    checks.append(('KRITIK', f'{count} geciken aksiyon var!'))
            except Exception:
                pass

            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM sistem.aksiyonlar
                    WHERE durum IN ('BEKLIYOR', 'DEVAM_EDIYOR')
                      AND hedef_tarih BETWEEN CAST(GETDATE() AS DATE) AND DATEADD(day, 3, CAST(GETDATE() AS DATE))
                      AND aktif_mi = 1 AND silindi_mi = 0
                """)
                count = cursor.fetchone()[0]
                if count > 0:
                    checks.append(('YUKSEK', f'{count} aksiyonun hedef tarihi yaklasti (3 gun icinde)'))
            except Exception:
                pass

            conn.close()
        except Exception as e:
            checks.append(('DUSUK', f'Bazi kontroller yapilamadi: {str(e)[:50]}'))

        if not checks:
            checks.append(('NORMAL', 'Sistem durumu normal, kritik uyari yok'))

        for onem, mesaj in checks:
            item = QListWidgetItem(mesaj)
            item.setForeground(QColor(ONEM_COLORS.get(onem, '#6b7280')))
            self.durum_list.addItem(item)

    def get_unread_count(self):
        user_id = self._get_user_id()
        if not user_id:
            return 0
        try:
            from core.bildirim_service import BildirimService
            return BildirimService.okunmamis_sayisi(user_id)
        except Exception:
            return 0
