# -*- coding: utf-8 -*-
"""
NEXOR ERP - Merkezi UI Stil Fonksiyonlari
[KURUMSAL UI - v2.0]

Tum modullerin kullanacagi standart stil fonksiyonlari.
PRAXIS KYS kurallarina uyumlu, NEXOR tema sistemiyle entegre.

Kullanim:
    from core.ui_styles import Ns  # Nexor Styles

    table.setStyleSheet(Ns.table(self.theme))
    btn.setStyleSheet(Ns.btn_primary(self.theme))
    frame.setStyleSheet(Ns.card(self.theme, accent='#10B981'))
"""


# ── Sabitler ──
MARGIN = 24
SPACING = 20
CARD_SPACING = 16
CARD_PADDING = 20
CARD_RADIUS = 10
INPUT_RADIUS = 8
BUTTON_RADIUS = 8

TITLE_SIZE = 22
SUBTITLE_SIZE = 13
HEADER_SIZE = 16
BODY_SIZE = 13
SMALL_SIZE = 11
LABEL_SIZE = 10

ROW_HEIGHT = 48
HEADER_HEIGHT = 44


class Ns:
    """Nexor Styles - Merkezi stil fonksiyonlari"""

    # ── Tablo ──
    @staticmethod
    def table(t: dict) -> str:
        return f"""
            QTableWidget, QTableView {{
                background: {t['bg_card']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: {CARD_RADIUS}px;
                gridline-color: {t['border']};
                font-size: {BODY_SIZE}px;
                outline: none;
            }}
            QTableWidget::item, QTableView::item {{
                padding: 10px;
                border-bottom: 1px solid {t['border']};
            }}
            QTableWidget::item:selected, QTableView::item:selected {{
                background: {t.get('table_row_selected', t['primary'] + '22')};
                color: {t['text']};
            }}
            QTableWidget::item:hover, QTableView::item:hover {{
                background: {t.get('table_row_hover', t['primary'] + '0A')};
            }}
            QHeaderView::section {{
                background: {t.get('table_header_bg', '#111822')};
                color: {t.get('table_header_text', t['text_secondary'])};
                padding: 12px 10px;
                border: none;
                border-bottom: 2px solid {t['primary']};
                font-weight: 600;
                font-size: {SMALL_SIZE}px;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {t.get('scrollbar_thumb', t['border'])};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {t.get('scrollbar_thumb_hover', '#2A3545')};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """

    # ── Kucuk Tablo (sol panel, dialog icinde) ──
    @staticmethod
    def table_compact(t: dict) -> str:
        return f"""
            QTableWidget {{
                background: {t['bg_card']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: {CARD_RADIUS}px;
                gridline-color: {t['border']};
                font-size: {SMALL_SIZE}px;
            }}
            QTableWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {t['border']};
            }}
            QTableWidget::item:selected {{
                background: {t['primary']}22;
                color: {t['text']};
            }}
            QTableWidget::item:hover {{
                background: {t['primary']}0A;
            }}
            QHeaderView::section {{
                background: {t.get('table_header_bg', '#111822')};
                color: {t.get('table_header_text', t['text_secondary'])};
                padding: 8px 6px;
                border: none;
                border-bottom: 2px solid {t['primary']};
                font-weight: 600;
                font-size: {LABEL_SIZE}px;
            }}
            QScrollBar:vertical {{
                background: transparent; width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {t.get('scrollbar_thumb', t['border'])}; border-radius: 3px; min-height: 20px;
            }}
        """

    # ── Inputlar ──
    @staticmethod
    def input(t: dict) -> str:
        return f"""
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTimeEdit {{
                background: {t.get('bg_input', t['bg_card'])};
                color: {t['text']};
                border: 1px solid {t.get('border_input', t['border'])};
                border-radius: {INPUT_RADIUS}px;
                padding: 10px 14px;
                font-size: {BODY_SIZE}px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {t['primary']};
            }}
        """

    # ── Butonlar ──
    @staticmethod
    def btn_primary(t: dict) -> str:
        return f"""
            QPushButton {{
                background: {t['primary']};
                color: white;
                border: none;
                border-radius: {BUTTON_RADIUS}px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: {BODY_SIZE}px;
            }}
            QPushButton:hover {{ background: {t.get('primary_hover', '#D42A2A')}; }}
            QPushButton:pressed {{ background: {t.get('primary_hover', '#9B1818')}; }}
            QPushButton:disabled {{ background: {t['border']}; color: {t['text_muted']}; }}
        """

    @staticmethod
    def btn_secondary(t: dict) -> str:
        return f"""
            QPushButton {{
                background: transparent;
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: {BUTTON_RADIUS}px;
                padding: 10px 20px;
                font-size: {BODY_SIZE}px;
            }}
            QPushButton:hover {{ background: {t.get('bg_hover', t['border'])}; }}
            QPushButton:pressed {{ background: {t.get('bg_selected', t['bg_card'])}; }}
        """

    @staticmethod
    def btn_success(t: dict) -> str:
        return f"""
            QPushButton {{
                background: {t['success']};
                color: white;
                border: none;
                border-radius: {BUTTON_RADIUS}px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: {BODY_SIZE}px;
            }}
            QPushButton:hover {{ background: {t.get('success_dark', '#059669')}; }}
            QPushButton:pressed {{ background: #047857; }}
        """

    @staticmethod
    def btn_danger(t: dict) -> str:
        return f"""
            QPushButton {{
                background: transparent;
                color: {t['error']};
                border: 1px solid {t['error']}44;
                border-radius: {BUTTON_RADIUS}px;
                padding: 8px 16px;
                font-size: {SMALL_SIZE}px;
            }}
            QPushButton:hover {{ background: {t['error']}22; }}
            QPushButton:pressed {{ background: {t['error']}33; }}
        """

    @staticmethod
    def btn_icon(t: dict, color: str = None) -> str:
        c = color or t['info']
        return f"""
            QPushButton {{
                background: {c}22;
                color: {c};
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {c}44; }}
        """

    # ── Kartlar ──
    @staticmethod
    def card(t: dict, accent: str = None) -> str:
        border_left = f"border-left: 3px solid {accent};" if accent else ""
        return f"""
            QFrame {{
                background: {t['bg_card']};
                border: 1px solid {t['border']};
                {border_left}
                border-radius: {CARD_RADIUS}px;
            }}
        """

    @staticmethod
    def card_hover(t: dict, accent: str = None) -> str:
        border_left = f"border-left: 3px solid {accent};" if accent else ""
        return f"""
            QFrame {{
                background: {t['bg_card']};
                border: 1px solid {t['border']};
                {border_left}
                border-radius: {CARD_RADIUS}px;
            }}
            QFrame:hover {{
                border-color: {accent or t['primary']};
            }}
        """

    # ── Tablar ──
    @staticmethod
    def tabs(t: dict) -> str:
        return f"""
            QTabWidget::pane {{
                border: none;
                background: {t['bg_card']};
            }}
            QTabBar::tab {{
                background: {t.get('bg_input', t['bg_card'])};
                color: {t['text_secondary']};
                padding: 10px 22px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: {BODY_SIZE}px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                color: {t['text']};
                border-bottom: 2px solid {t['primary']};
                background: {t['bg_card']};
            }}
            QTabBar::tab:hover {{
                color: {t['text']};
            }}
        """

    # ── Dialog ──
    @staticmethod
    def dialog(t: dict) -> str:
        return f"QDialog {{ background: {t['bg_card']}; color: {t['text']}; }}"

    # ── ScrollArea ──
    @staticmethod
    def scroll_area(t: dict) -> str:
        return f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: transparent; width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {t.get('scrollbar_thumb', t['border'])}; border-radius: 4px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {t.get('scrollbar_thumb_hover', '#2A3545')};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """

    @staticmethod
    def scroll_horizontal(t: dict) -> str:
        return f"""
            QScrollBar:horizontal {{
                height: 8px; background: transparent;
            }}
            QScrollBar::handle:horizontal {{
                background: {t.get('scrollbar_thumb', t['border'])}; border-radius: 4px; min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {t.get('scrollbar_thumb_hover', '#2A3545')};
            }}
        """

    # ── Label Stilleri ──
    @staticmethod
    def title(t: dict) -> str:
        return f"color: {t['text']}; font-size: {TITLE_SIZE}px; font-weight: 600;"

    @staticmethod
    def subtitle(t: dict) -> str:
        return f"color: {t['text_secondary']}; font-size: {SUBTITLE_SIZE}px;"

    @staticmethod
    def section_label(t: dict) -> str:
        return f"""
            color: {t['text_muted']};
            font-size: {LABEL_SIZE}px;
            font-weight: 600;
            letter-spacing: 1px;
        """

    @staticmethod
    def body(t: dict) -> str:
        return f"color: {t['text']}; font-size: {BODY_SIZE}px;"

    @staticmethod
    def small(t: dict) -> str:
        return f"color: {t['text_secondary']}; font-size: {SMALL_SIZE}px;"

    @staticmethod
    def muted(t: dict) -> str:
        return f"color: {t['text_muted']}; font-size: {LABEL_SIZE}px;"

    # ── Toolbar / Bar ──
    @staticmethod
    def toolbar(t: dict) -> str:
        return f"""
            QFrame {{
                background: {t['bg_card']};
                border-bottom: 1px solid {t['border']};
            }}
        """

    @staticmethod
    def bottom_bar(t: dict) -> str:
        return f"""
            QFrame {{
                background: {t['bg_card']};
                border-top: 1px solid {t['border']};
            }}
        """

    # ── Badge / Canli Gosterge ──
    @staticmethod
    def badge(t: dict, color: str = None) -> str:
        c = color or t['success']
        return f"""
            color: {c};
            font-size: {LABEL_SIZE}px;
            font-weight: 600;
            background: {c}22;
            border: 1px solid {c}44;
            border-radius: 4px;
            padding: 3px 10px;
            letter-spacing: 1px;
        """

    # ── Uyari Kutusu (darbogaz vb.) ──
    @staticmethod
    def alert(t: dict, color: str = None) -> str:
        c = color or t['warning']
        return f"""
            color: {c};
            font-size: {SMALL_SIZE}px;
            padding: 10px 14px;
            background: {t['bg_card']};
            border: 1px solid {c}33;
            border-left: 3px solid {c};
            border-radius: {CARD_RADIUS}px;
        """

    # ── Tablo Ici Aksiyon Butonlari ──
    @staticmethod
    def action_edit(t: dict) -> str:
        c = t.get('info', '#3B82F6')
        return f"""
            QPushButton {{
                background: {c}22;
                color: {c};
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 0px;
            }}
            QPushButton:hover {{ background: {c}44; }}
            QPushButton:pressed {{ background: {c}66; }}
        """

    @staticmethod
    def action_delete(t: dict) -> str:
        c = t.get('error', '#EF4444')
        return f"""
            QPushButton {{
                background: {c}22;
                color: {c};
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 0px;
            }}
            QPushButton:hover {{ background: {c}44; }}
            QPushButton:pressed {{ background: {c}66; }}
        """

    @staticmethod
    def action_detail(t: dict) -> str:
        c = t.get('success', '#10B981')
        return f"""
            QPushButton {{
                background: {c}22;
                color: {c};
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 0px;
            }}
            QPushButton:hover {{ background: {c}44; }}
            QPushButton:pressed {{ background: {c}66; }}
        """

    @staticmethod
    def action_view(t: dict) -> str:
        c = t.get('warning', '#F59E0B')
        return f"""
            QPushButton {{
                background: {c}22;
                color: {c};
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 0px;
            }}
            QPushButton:hover {{ background: {c}44; }}
            QPushButton:pressed {{ background: {c}66; }}
        """

    # ── Splitter ──
    @staticmethod
    def splitter(t: dict) -> str:
        return f"QSplitter::handle {{ background: {t['border']}; width: 2px; }}"
