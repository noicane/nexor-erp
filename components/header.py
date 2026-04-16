# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Header Bileşeni
Üst başlık çubuğu + Bildirim entegrasyonu
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QWidget, QScrollArea, QGraphicsDropShadowEffect, QApplication,
    QDialog, QTextBrowser
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QCursor

from core.nexor_brand import brand


# Bildirim önem renkleri
_ONEM_COLORS = {
    'KRITIK': '#ef4444',
    'YUKSEK': '#f97316',
    'NORMAL': '#3b82f6',
    'DUSUK': '#6b7280',
}

_MODUL_ICONS = {
    'KALITE': '✅', 'URETIM': '🏭', 'BAKIM': '🔧', 'IK': '👥',
    'STOK': '📦', 'SEVKIYAT': '🚚', 'SISTEM': '⚙️', 'IS_EMIRLERI': '📋',
    'ISG': '🦺', 'SATINALMA': '🛒', 'LAB': '🔬', 'CEVRE': '🌿',
}


class BildirimDropdownItem(QFrame):
    """Dropdown içindeki tek bildirim satırı"""
    clicked = Signal(dict)

    def __init__(self, bildirim: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.bildirim = bildirim
        self.theme = theme
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        t = self.theme
        okundu = self.bildirim.get('okundu_mu', False)
        onem = self.bildirim.get('onem_derecesi', 'NORMAL')
        border_color = _ONEM_COLORS.get(onem, '#3b82f6')

        bg = t.get('bg_card', t.get('bg_main', '#1A1A1A')) if okundu else t.get('bg_input', t.get('bg_card', '#1E1E1E'))

        self.setStyleSheet(f"""
            BildirimDropdownItem {{
                background: {bg};
                border-left: 3px solid {border_color};
                border-radius: 6px;
                padding: 0px;
            }}
            BildirimDropdownItem:hover {{
                background: {t.get('bg_hover', t.get('bg_card', '#2A2A2A'))};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Modül ikonu
        modul = self.bildirim.get('modul', '')
        icon = QLabel(_MODUL_ICONS.get(modul, '📋'))
        icon.setFixedWidth(20)
        icon.setStyleSheet("font-size: 14px; background: transparent;")
        layout.addWidget(icon)

        # İçerik
        content = QVBoxLayout()
        content.setSpacing(2)

        baslik = QLabel(self.bildirim.get('baslik', ''))
        weight = 'normal' if okundu else 'bold'
        baslik.setStyleSheet(f"color: {t.get('text', '#FFFFFF')}; font-size: 12px; font-weight: {weight}; background: transparent;")
        baslik.setWordWrap(True)
        content.addWidget(baslik)

        tarih = self.bildirim.get('olusturma_tarihi')
        if tarih:
            tarih_str = tarih.strftime("%d.%m %H:%M") if hasattr(tarih, 'strftime') else str(tarih)[:16]
            lbl_tarih = QLabel(tarih_str)
            lbl_tarih.setStyleSheet(f"color: {t.get('text_muted', t.get('text_secondary', '#666'))}; font-size: 10px; background: transparent;")
            content.addWidget(lbl_tarih)

        layout.addLayout(content, 1)

        # Önem noktası
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {border_color}; font-size: 8px; background: transparent;")
        dot.setFixedWidth(12)
        layout.addWidget(dot)

    def mousePressEvent(self, event):
        self.clicked.emit(self.bildirim)


class BildirimDropdown(QFrame):
    """Header'daki bildirim dropdown paneli"""
    bildirim_clicked = Signal(dict)
    tumunu_gor_clicked = Signal()
    tumunu_okundu_clicked = Signal()

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFixedWidth(380)
        self.setMaximumHeight(500)
        self._setup_ui()

    def _setup_ui(self):
        t = self.theme

        self.setStyleSheet(f"""
            BildirimDropdown {{
                background: {t.get('bg_card', t.get('bg_main', '#1E1E1E'))};
                border: 1px solid {t.get('border', t.get('border_light', '#2A2A2A'))};
                border-radius: 12px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)

        # Başlık
        header = QHBoxLayout()
        title = QLabel("Bildirimler")
        title.setStyleSheet(f"color: {t.get('text', '#FFFFFF')}; font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        self.lbl_count = QLabel()
        self.lbl_count.setStyleSheet(f"""
            color: white; background: {t.get('error', '#EF4444')};
            padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;
        """)
        self.lbl_count.hide()
        header.addWidget(self.lbl_count)

        btn_okundu = QPushButton("Tümü okundu")
        btn_okundu.setCursor(Qt.PointingHandCursor)
        btn_okundu.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {t.get('primary', '#DC2626')}; font-size: 12px;
            }}
            QPushButton:hover {{ text-decoration: underline; }}
        """)
        btn_okundu.clicked.connect(self.tumunu_okundu_clicked.emit)
        header.addWidget(btn_okundu)

        layout.addLayout(header)

        # Ayırıcı
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {t.get('border', t.get('border_light', '#2A2A2A'))}; max-height: 1px;")
        layout.addWidget(sep)

        # Bildirim listesi scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(340)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: transparent; width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {t.get('border', t.get('border_light', '#333'))}; border-radius: 3px;
            }}
        """)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.list_container)
        layout.addWidget(scroll, 1)

        # Alt buton
        btn_tumunu_gor = QPushButton("Tüm Bildirimleri Gör")
        btn_tumunu_gor.setCursor(Qt.PointingHandCursor)
        btn_tumunu_gor.setStyleSheet(f"""
            QPushButton {{
                background: {t.get('bg_hover', t.get('bg_card', '#2A2A2A'))};
                border: 1px solid {t.get('border', t.get('border_light', '#333'))};
                border-radius: 8px; padding: 10px;
                color: {t.get('text', '#FFFFFF')}; font-size: 13px; font-weight: 500;
            }}
            QPushButton:hover {{
                background: {t.get('primary', '#DC2626')};
                border-color: {t.get('primary', '#DC2626')};
                color: white;
            }}
        """)
        btn_tumunu_gor.clicked.connect(self._on_tumunu_gor)
        layout.addWidget(btn_tumunu_gor)

    def _on_tumunu_gor(self):
        self.hide()
        self.tumunu_gor_clicked.emit()

    def set_bildirimler(self, bildirimler: list):
        """Dropdown'daki bildirim listesini güncelle."""
        # Eski widget'ları temizle
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not bildirimler:
            empty = QLabel("Bildirim bulunmuyor")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {self.theme.get('text_muted', self.theme.get('text_secondary', '#666'))}; padding: 30px; font-size: 13px;")
            self.list_layout.addWidget(empty)
            self.lbl_count.hide()
            return

        okunmamis = sum(1 for b in bildirimler if not b.get('okundu_mu'))
        if okunmamis > 0:
            self.lbl_count.setText(str(okunmamis))
            self.lbl_count.show()
        else:
            self.lbl_count.hide()

        for b in bildirimler[:10]:  # Max 10 bildirim göster
            item = BildirimDropdownItem(b, self.theme)
            item.clicked.connect(self._on_item_clicked)
            self.list_layout.addWidget(item)

    def _on_item_clicked(self, bildirim: dict):
        self.hide()
        self.bildirim_clicked.emit(bildirim)


class Header(QFrame):
    """Üst başlık çubuğu"""
    toggle_sidebar = Signal()
    bildirim_sayfasi_ac = Signal()       # Bildirim merkezi sayfasını aç
    bildirim_detay_ac = Signal(dict)     # Tek bildirime tıklanınca

    def __init__(self, theme: dict, user_data: dict):
        super().__init__()
        self.theme = theme
        self.user_data = user_data
        self._unread_count = 0
        self._dropdown = None
        self.setFixedHeight(brand.sp(68))
        self._setup_ui()
        self._setup_polling()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(brand.SP_5, 0, brand.SP_6, 0)
        layout.setSpacing(brand.SP_4)

        # Toggle butonu
        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setFixedSize(brand.sp(40), brand.sp(40))
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_sidebar.emit)
        layout.addWidget(self.toggle_btn)

        # Nefes aldirma — toggle ile baslik arasi bosluk
        layout.addSpacing(brand.SP_2)

        # Başlık + Tarih
        title_container = QVBoxLayout()
        title_container.setSpacing(brand.SP_1)
        title_container.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("Dashboard")
        title_container.addWidget(self.title_label)

        now = datetime.now()
        days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz',
                  'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        day_name = days[now.weekday()]
        date_str = f"{now.day} {months[now.month-1]} {now.year}, {day_name}"

        self.date_label = QLabel(date_str)
        title_container.addWidget(self.date_label)

        layout.addLayout(title_container)
        layout.addStretch()

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara... (Ctrl+K)")
        self.search_input.setFixedWidth(brand.sp(280))
        self.search_input.setFixedHeight(brand.sp(38))
        layout.addWidget(self.search_input)

        # =============== YARDIM BUTONU ===============
        self.help_btn = QPushButton("?")
        self.help_btn.setFixedSize(brand.sp(38), brand.sp(38))
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setToolTip("Kullanım Kılavuzu")
        self.help_btn.clicked.connect(self._show_kilavuz)
        layout.addWidget(self.help_btn)

        # =============== BİLDİRİM BUTONU ===============
        self.notif_container = QFrame()
        self.notif_container.setFixedSize(brand.sp(42), brand.sp(42))
        self.notif_container.setStyleSheet("background: transparent; border: none;")
        notif_layout = QVBoxLayout(self.notif_container)
        notif_layout.setContentsMargins(0, 0, 0, 0)

        self.notif_btn = QPushButton("🔔")
        self.notif_btn.setFixedSize(brand.sp(38), brand.sp(38))
        self.notif_btn.setCursor(Qt.PointingHandCursor)
        self.notif_btn.clicked.connect(self._toggle_dropdown)
        notif_layout.addWidget(self.notif_btn)

        # Badge (okunmamış sayı)
        self.badge = QLabel()
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setFixedSize(brand.sp(20), brand.sp(20))
        self.badge.hide()
        self.badge.setParent(self.notif_container)
        self.badge.move(brand.sp(22), brand.sp(2))

        layout.addWidget(self.notif_container)

        # Avatar
        initials = f"{self.user_data.get('ad', 'U')[0]}{self.user_data.get('soyad', 'S')[0]}"
        self.avatar = QFrame()
        self.avatar.setFixedSize(brand.sp(38), brand.sp(38))
        a_layout = QVBoxLayout(self.avatar)
        a_layout.setContentsMargins(0, 0, 0, 0)
        self.avatar_label = QLabel(initials.upper())
        self.avatar_label.setAlignment(Qt.AlignCenter)
        a_layout.addWidget(self.avatar_label)
        layout.addWidget(self.avatar)

        # Tum widget'lara brand stillerini uygula
        self._apply_child_styles()
        self._apply_style()

    def _setup_polling(self):
        """60 saniyede bir bildirim sayısını kontrol et."""
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_bildirimleri)
        self._poll_timer.start(60000)  # 60 saniye

        # İlk yükleme biraz gecikmeliyle
        QTimer.singleShot(2000, self._poll_bildirimleri)

    def _poll_bildirimleri(self):
        """Okunmamış bildirim sayısını güncelle."""
        try:
            from core.bildirim_service import BildirimService
            user_id = self.user_data.get('id')
            if not user_id:
                return

            count = BildirimService.okunmamis_sayisi(user_id)
            self._update_badge(count)

        except Exception as e:
            print(f"[Header] Bildirim polling hatası: {e}")

    def _update_badge(self, count: int):
        """Badge'i güncelle."""
        self._unread_count = count
        if count > 0:
            text = "99+" if count > 99 else str(count)
            self.badge.setText(text)
            self.badge.show()
        else:
            self.badge.hide()

    def _toggle_dropdown(self):
        """Bildirim dropdown'ını aç/kapat."""
        if self._dropdown and self._dropdown.isVisible():
            self._dropdown.hide()
            return

        if not self._dropdown:
            self._dropdown = BildirimDropdown(self.theme)
            self._dropdown.bildirim_clicked.connect(self._on_bildirim_clicked)
            self._dropdown.tumunu_gor_clicked.connect(self._on_tumunu_gor)
            self._dropdown.tumunu_okundu_clicked.connect(self._on_tumunu_okundu)

        # Bildirimleri yükle
        self._load_dropdown_data()

        # Dropdown pozisyonunu hesapla
        btn_pos = self.notif_btn.mapToGlobal(QPoint(0, 0))
        x = btn_pos.x() - self._dropdown.width() + self.notif_btn.width()
        y = btn_pos.y() + self.notif_btn.height() + 8
        self._dropdown.move(x, y)
        self._dropdown.show()

    def _load_dropdown_data(self):
        """Dropdown için bildirim verilerini yükle."""
        try:
            from core.bildirim_service import BildirimService
            user_id = self.user_data.get('id')
            if not user_id:
                return

            bildirimler = BildirimService.kullanici_bildirimleri(
                kullanici_id=user_id,
                limit=10
            )
            if self._dropdown:
                self._dropdown.set_bildirimler(bildirimler)

        except Exception as e:
            print(f"[Header] Dropdown veri yükleme hatası: {e}")

    def _on_bildirim_clicked(self, bildirim: dict):
        """Dropdown'daki bildirime tıklanınca."""
        try:
            from core.bildirim_service import BildirimService
            user_id = self.user_data.get('id')
            BildirimService.okundu_isaretle(bildirim['id'], user_id)
            self._poll_bildirimleri()
        except Exception:
            pass

        self.bildirim_detay_ac.emit(bildirim)

    def _on_tumunu_gor(self):
        """'Tüm Bildirimleri Gör' tıklanınca."""
        self.bildirim_sayfasi_ac.emit()

    def _on_tumunu_okundu(self):
        """'Tümü okundu' tıklanınca."""
        try:
            from core.bildirim_service import BildirimService
            user_id = self.user_data.get('id')
            if user_id:
                BildirimService.tumunu_okundu_isaretle(user_id)
                self._poll_bildirimleri()
                self._load_dropdown_data()
        except Exception as e:
            print(f"[Header] Tümü okundu hatası: {e}")

    def refresh_bildirimler(self):
        """Dışarıdan bildirim sayısını yenilemek için."""
        self._poll_bildirimleri()

    def _show_kilavuz(self):
        """Kullanım kılavuzunu dialog olarak göster."""
        import os, re

        kilavuz_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'KULLANIM_KILAVUZU.md')
        try:
            with open(kilavuz_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
        except FileNotFoundError:
            md_content = "Kullanım kılavuzu dosyası bulunamadı."

        # Basit markdown -> HTML dönüşümü
        html = self._md_to_html(md_content)

        t = self.theme
        dlg = QDialog(self)
        dlg.setWindowTitle("NEXOR ERP — Kullanım Kılavuzu")
        dlg.resize(900, 700)
        dlg.setStyleSheet(f"QDialog {{ background: {t.get('bg_main', '#121212')}; }}")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(html)
        browser.setStyleSheet(f"""
            QTextBrowser {{
                background: {t.get('bg_main', '#121212')};
                color: {t.get('text', '#E0E0E0')};
                border: none;
                padding: 24px 40px;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
            }}
            QScrollBar:vertical {{
                background: {t.get('bg_card', '#1E1E1E')};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {t.get('border', '#333')};
                border-radius: 4px;
                min-height: 30px;
            }}
        """)
        layout.addWidget(browser)
        dlg.exec()

    @staticmethod
    def _md_to_html(md: str) -> str:
        """Basit Markdown -> HTML çevirici."""
        import re
        lines = md.split('\n')
        html_lines = []
        in_table = False
        in_code = False
        in_list = False

        for line in lines:
            # Kod bloğu
            if line.strip().startswith('```'):
                if in_code:
                    html_lines.append('</pre>')
                    in_code = False
                else:
                    html_lines.append('<pre style="background:#1E1E1E; padding:12px; border-radius:8px; font-size:13px; color:#A0D0A0; overflow-x:auto;">')
                    in_code = True
                continue
            if in_code:
                html_lines.append(line.replace('<', '&lt;').replace('>', '&gt;'))
                continue

            stripped = line.strip()

            # Boş satır
            if not stripped:
                if in_list:
                    in_list = False
                if in_table:
                    html_lines.append('</table>')
                    in_table = False
                html_lines.append('<br>')
                continue

            # Yatay çizgi
            if stripped == '---':
                if in_table:
                    html_lines.append('</table>')
                    in_table = False
                html_lines.append('<hr style="border:1px solid #333; margin:16px 0;">')
                continue

            # Başlıklar
            if stripped.startswith('######'):
                html_lines.append(f'<h6 style="color:#DC2626; margin:8px 0 4px;">{stripped[7:]}</h6>')
                continue
            if stripped.startswith('#####'):
                html_lines.append(f'<h5 style="color:#DC2626; margin:8px 0 4px;">{stripped[6:]}</h5>')
                continue
            if stripped.startswith('####'):
                html_lines.append(f'<h4 style="color:#DC2626; margin:10px 0 6px;">{stripped[5:]}</h4>')
                continue
            if stripped.startswith('###'):
                html_lines.append(f'<h3 style="color:#DC2626; margin:12px 0 6px;">{stripped[4:]}</h3>')
                continue
            if stripped.startswith('## '):
                html_lines.append(f'<h2 style="color:#DC2626; margin:20px 0 8px; border-bottom:1px solid #333; padding-bottom:6px;">{stripped[3:]}</h2>')
                continue
            if stripped.startswith('# '):
                html_lines.append(f'<h1 style="color:#DC2626; margin:20px 0 10px;">{stripped[2:]}</h1>')
                continue

            # Tablo ayırıcı satırı (|---|---|)
            if re.match(r'^\|[\s\-:|]+\|$', stripped):
                continue

            # Tablo
            if stripped.startswith('|') and stripped.endswith('|'):
                cells = [c.strip() for c in stripped.strip('|').split('|')]
                if not in_table:
                    html_lines.append('<table style="border-collapse:collapse; width:100%; margin:8px 0;">')
                    tag = 'th'
                    in_table = True
                else:
                    tag = 'td'
                row = ''.join(
                    f'<{tag} style="border:1px solid #333; padding:8px 12px; text-align:left;">{c}</{tag}>'
                    for c in cells
                )
                html_lines.append(f'<tr>{row}</tr>')
                continue

            if in_table:
                html_lines.append('</table>')
                in_table = False

            # Liste
            if stripped.startswith('- ') or stripped.startswith('* '):
                content = stripped[2:]
                content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
                content = re.sub(r'`(.+?)`', r'<code style="background:#1E1E1E; padding:2px 6px; border-radius:4px; font-size:12px;">\1</code>', content)
                html_lines.append(f'<div style="margin:2px 0 2px 16px;">• {content}</div>')
                in_list = True
                continue

            # Numaralı liste
            m = re.match(r'^(\d+)\.\s+(.+)', stripped)
            if m:
                content = m.group(2)
                content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
                content = re.sub(r'`(.+?)`', r'<code style="background:#1E1E1E; padding:2px 6px; border-radius:4px; font-size:12px;">\1</code>', content)
                html_lines.append(f'<div style="margin:2px 0 2px 16px;">{m.group(1)}. {content}</div>')
                in_list = True
                continue

            # Blockquote
            if stripped.startswith('> '):
                html_lines.append(f'<div style="border-left:3px solid #DC2626; padding:4px 12px; margin:8px 0; color:#999;">{stripped[2:]}</div>')
                continue

            # Normal paragraf — inline formatting
            p = stripped
            p = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', p)
            p = re.sub(r'`(.+?)`', r'<code style="background:#1E1E1E; padding:2px 6px; border-radius:4px; font-size:12px;">\1</code>', p)
            html_lines.append(f'<p style="margin:4px 0;">{p}</p>')

        if in_table:
            html_lines.append('</table>')
        if in_code:
            html_lines.append('</pre>')

        return '\n'.join(html_lines)

    def _apply_style(self):
        self.setStyleSheet(
            f"Header {{ "
            f"background: {brand.BG_MAIN}; "
            f"border-bottom: 1px solid {brand.BORDER}; "
            f"}}"
        )

    def _apply_child_styles(self):
        """Tum child widget stillerini brand'den okuyup uygula.
        Tema modu degistiginde bunlarin yeniden uygulanmasi GEREK.
        """
        # Toggle button
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: {brand.fs(20)}px;
                color: {brand.TEXT_MUTED};
                border-radius: {brand.R_SM}px;
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT};
            }}
        """)

        # Title + Date
        self.title_label.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING_LG}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"letter-spacing: -0.3px; "
            f"background: transparent;"
        )
        self.date_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_MEDIUM}; "
            f"background: transparent;"
        )

        # Search
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QLineEdit:focus {{
                border-color: {brand.BORDER_FOCUS};
                background: {brand.BG_HOVER};
            }}
        """)

        # Help button
        self.help_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {brand.BORDER};
                font-size: {brand.fs(16)}px;
                font-weight: {brand.FW_BOLD};
                color: {brand.TEXT_MUTED};
                border-radius: {brand.R_SM}px;
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
                color: {brand.TEXT};
            }}
        """)

        # Notification button
        self.notif_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {brand.BORDER};
                font-size: {brand.fs(16)}px;
                border-radius: {brand.R_SM}px;
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
            }}
        """)

        # Badge
        self.badge.setStyleSheet(f"""
            QLabel {{
                background: {brand.ERROR};
                color: white;
                border-radius: {brand.sp(10)}px;
                font-size: {brand.fs(10)}px;
                font-weight: {brand.FW_BOLD};
                border: 2px solid {brand.BG_MAIN};
            }}
        """)

        # Avatar
        self.avatar.setStyleSheet(
            f"background: {brand.PRIMARY}; "
            f"border-radius: {brand.sp(19)}px; "
            f"border: 2px solid {brand.PRIMARY_HOVER};"
        )
        self.avatar_label.setStyleSheet(
            f"color: white; "
            f"font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"background: transparent; border: none;"
        )

    def set_title(self, title: str):
        self.title_label.setText(title)

    def update_theme(self, theme: dict):
        self.theme = theme
        self._apply_style()
        self._apply_child_styles()
        # Dropdown'ı yeniden oluştur (tema değişikliği)
        if self._dropdown:
            self._dropdown.deleteLater()
            self._dropdown = None
