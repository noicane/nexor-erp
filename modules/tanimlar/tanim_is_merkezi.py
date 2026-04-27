# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Is Merkezi Tanimlari
Hiyerarsik is merkezi yapisi: Kataforez > Kalite, Paketleme vb.
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QMessageBox, QDialog, QFormLayout,
    QComboBox, QTextEdit, QWidget, QGraphicsDropShadowEffect,
    QTreeWidget, QTreeWidgetItem, QCheckBox, QHeaderView, QSplitter
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
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
        'error': brand.ERROR,
        'info': brand.INFO,
        'bg_main': brand.BG_MAIN,
        'bg_hover': brand.BG_HOVER,
        'border_light': brand.BORDER_HARD,
    }


def _ensure_table():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='is_merkezleri' AND schema_id=SCHEMA_ID('tanim'))
            BEGIN
                CREATE TABLE tanim.is_merkezleri (
                    id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    kod NVARCHAR(30) NOT NULL,
                    ad NVARCHAR(150) NOT NULL,
                    ust_merkez_id BIGINT NULL REFERENCES tanim.is_merkezleri(id),
                    hat_id BIGINT NULL,
                    aciklama NVARCHAR(500) NULL,
                    sira INT NULL DEFAULT 0,
                    aktif_mi BIT NOT NULL DEFAULT 1,
                    olusturma_tarihi DATETIME2 NOT NULL DEFAULT GETDATE()
                )
            END
        """)
        conn.commit()
    except Exception:
        pass
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


class IsMerkeziDialog(QDialog):
    """Is Merkezi Ekleme/Duzenleme"""

    def __init__(self, theme: dict, merkez_id=None, ust_merkez_id=None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.merkez_id = merkez_id
        self.default_ust_id = ust_merkez_id
        self.data = {}

        self.setWindowTitle("Yeni Is Merkezi" if not merkez_id else "Is Merkezi Duzenle")
        self.setMinimumSize(500, 480)
        self.setModal(True)

        if merkez_id:
            self._load_data()
        self._setup_ui()

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tanim.is_merkezleri WHERE id=?", (self.merkez_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 12px;
            }}
            QLabel {{ color: {s['text']}; background: transparent; }}
            QLineEdit, QTextEdit, QComboBox {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {s['text']};
                font-size: 13px;
                min-height: 20px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{ border-color: {s['primary']}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                color: {s['text']};
                selection-background-color: {s['primary']};
            }}
            QCheckBox {{ color: {s['text']}; font-size: 13px; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        icon = QLabel("🏭")
        icon.setStyleSheet("font-size: 28px;")
        header.addWidget(icon)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {s['border']}; max-height: 1px;")
        layout.addWidget(sep)

        # Form
        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignRight)
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"

        # Kod
        lbl = QLabel("Merkez Kodu *")
        lbl.setStyleSheet(label_style)
        self.kod_input = QLineEdit(self.data.get('kod', ''))
        self.kod_input.setPlaceholderText("Orn: KTL, TOZ, CINKO, DESTEK")
        self.kod_input.setMaxLength(30)
        form.addRow(lbl, self.kod_input)

        # Ad
        lbl = QLabel("Merkez Adi *")
        lbl.setStyleSheet(label_style)
        self.ad_input = QLineEdit(self.data.get('ad', ''))
        self.ad_input.setPlaceholderText("Orn: Kataforez, Toz Boya, Cinko")
        form.addRow(lbl, self.ad_input)

        # Ust Merkez
        lbl = QLabel("Ust Merkez")
        lbl.setStyleSheet(label_style)
        self.ust_combo = QComboBox()
        self.ust_combo.addItem("-- Ana Merkez (Yok) --", None)
        self._load_ust_merkezler()
        form.addRow(lbl, self.ust_combo)

        # Hat iliskisi
        lbl = QLabel("Bagli Hat")
        lbl.setStyleSheet(label_style)
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("-- Hat Yok --", None)
        self._load_hatlar()
        form.addRow(lbl, self.hat_combo)

        # Sira
        lbl = QLabel("Sira No")
        lbl.setStyleSheet(label_style)
        self.sira_input = QLineEdit(str(self.data.get('sira', 0) or 0))
        self.sira_input.setMaxLength(5)
        form.addRow(lbl, self.sira_input)

        # Aciklama
        lbl = QLabel("Aciklama")
        lbl.setStyleSheet(label_style)
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setMaximumHeight(80)
        self.aciklama_input.setText(self.data.get('aciklama', '') or '')
        form.addRow(lbl, self.aciklama_input)

        # Aktif
        self.aktif_check = QCheckBox("Aktif")
        self.aktif_check.setChecked(self.data.get('aktif_mi', True) if self.data else True)
        form.addRow("", self.aktif_check)

        layout.addLayout(form)
        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']};
                color: {s['text']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {s['border']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 28px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_ust_merkezler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = "SELECT id, kod, ad FROM tanim.is_merkezleri WHERE aktif_mi=1"
            if self.merkez_id:
                sql += f" AND id != {self.merkez_id}"
            sql += " ORDER BY sira, ad"
            cursor.execute(sql)
            for row in cursor.fetchall():
                self.ust_combo.addItem(f"{row[1]} - {row[2]}", row[0])

            target = self.data.get('ust_merkez_id') or self.default_ust_id
            if target:
                idx = self.ust_combo.findData(target)
                if idx >= 0:
                    self.ust_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_hatlar(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ISNULL(kisa_ad, ad) FROM tanim.uretim_hatlari WHERE aktif_mi=1 ORDER BY sira_no")
            for row in cursor.fetchall():
                self.hat_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            if self.data.get('hat_id'):
                idx = self.hat_combo.findData(self.data['hat_id'])
                if idx >= 0:
                    self.hat_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _save(self):
        kod = self.kod_input.text().strip().upper()
        ad = self.ad_input.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Eksik Bilgi", "Merkez Kodu ve Adi zorunludur!")
            return

        ust_id = self.ust_combo.currentData()
        hat_id = self.hat_combo.currentData()
        aciklama = self.aciklama_input.toPlainText().strip() or None
        sira = int(self.sira_input.text() or 0)
        aktif = 1 if self.aktif_check.isChecked() else 0

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            if self.merkez_id:
                cursor.execute("""
                    UPDATE tanim.is_merkezleri
                    SET kod=?, ad=?, ust_merkez_id=?, hat_id=?, aciklama=?, sira=?, aktif_mi=?
                    WHERE id=?
                """, (kod, ad, ust_id, hat_id, aciklama, sira, aktif, self.merkez_id))
            else:
                cursor.execute("""
                    INSERT INTO tanim.is_merkezleri (kod, ad, ust_merkez_id, hat_id, aciklama, sira, aktif_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (kod, ad, ust_id, hat_id, aciklama, sira, aktif))

            conn.commit()
            LogManager.log_insert('tanimlar', 'tanim.is_merkezleri', None, f'Is merkezi: {kod} - {ad}')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class TanimIsMerkeziPage(BasePage):
    """Is Merkezi Tanimlari - Hiyerarsik agac gorunumu"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        _ensure_table()
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

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
        icon = QLabel("🏭")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Is Merkezi Tanimlari")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)

        subtitle = QLabel("Kataforez, Toz Boya, Cinko, Destek ve alt merkezler")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()

        # Stat
        self.toplam_card = self._create_stat_card("Toplam", "0", s['info'])
        self.aktif_card = self._create_stat_card("Aktif", "0", s['success'])
        stats = QHBoxLayout()
        stats.setSpacing(12)
        stats.addWidget(self.toplam_card)
        stats.addWidget(self.aktif_card)
        header.addLayout(stats)

        layout.addLayout(header)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara (Kod, Ad)")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 14px;
                color: {s['text']};
                font-size: 13px;
                min-width: 220px;
            }}
            QLineEdit:focus {{ border-color: {s['primary']}; }}
        """)
        self.search_input.textChanged.connect(self._filter_tree)
        toolbar.addWidget(self.search_input)

        toolbar.addStretch()

        expand_btn = QPushButton("Hepsini Ac")
        expand_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                color: {s['text']};
            }}
            QPushButton:hover {{ background: {s['border']}; }}
        """)
        expand_btn.clicked.connect(lambda: self.tree.expandAll())
        toolbar.addWidget(expand_btn)

        refresh_btn = QPushButton("Yenile")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                color: {s['text']};
            }}
            QPushButton:hover {{ background: {s['border']}; border-color: {s['primary']}; }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(refresh_btn)

        add_sub_btn = QPushButton("+ Alt Merkez")
        add_sub_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['info']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #2563EB; }}
        """)
        add_sub_btn.clicked.connect(self._add_sub)
        toolbar.addWidget(add_sub_btn)

        add_btn = QPushButton("+ Yeni Merkez")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        add_btn.clicked.connect(self._add_new)
        toolbar.addWidget(add_btn)

        layout.addLayout(toolbar)

        # Tree + Detail Split
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {s['border']}; width: 2px; }}")

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Kod", "Is Merkezi Adi", "Bagli Hat", "Durum"])
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 10px;
                color: {s['text']};
                font-size: 13px;
            }}
            QTreeWidget::item {{
                padding: 8px 4px;
                border-bottom: 1px solid {s['border']};
            }}
            QTreeWidget::item:selected {{
                background: {s['primary']};
            }}
            QTreeWidget::item:hover {{
                background: rgba(220, 38, 38, 0.08);
            }}
            QHeaderView::section {{
                background: rgba(0,0,0,0.3);
                color: {s['text_secondary']};
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid {s['primary']};
                font-weight: 600;
                font-size: 12px;
            }}
        """)
        self.tree.setColumnWidth(0, 120)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 150)
        self.tree.setColumnWidth(3, 80)
        self.tree.itemDoubleClicked.connect(self._edit_item)
        splitter.addWidget(self.tree)

        # Detail Panel
        detail_frame = QFrame()
        detail_frame.setStyleSheet(f"""
            QFrame {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 10px;
            }}
        """)
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(20, 20, 20, 20)
        detail_layout.setSpacing(12)

        self.detail_title = QLabel("Is Merkezi Secin")
        self.detail_title.setStyleSheet(f"color: {s['text']}; font-size: 18px; font-weight: 600;")
        detail_layout.addWidget(self.detail_title)

        self.detail_info = QLabel("")
        self.detail_info.setWordWrap(True)
        self.detail_info.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px; line-height: 1.6;")
        detail_layout.addWidget(self.detail_info)

        detail_layout.addStretch()

        # Detail buttons
        detail_btns = QHBoxLayout()
        self.edit_btn = QPushButton("Duzenle")
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['info']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #2563EB; }}
        """)
        self.edit_btn.clicked.connect(self._edit_selected)
        self.edit_btn.setEnabled(False)
        detail_btns.addWidget(self.edit_btn)

        self.del_btn = QPushButton("Sil")
        self.del_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['error']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #DC2626; }}
        """)
        self.del_btn.clicked.connect(self._delete_selected)
        self.del_btn.setEnabled(False)
        detail_btns.addWidget(self.del_btn)

        detail_btns.addStretch()
        detail_layout.addLayout(detail_btns)

        splitter.addWidget(detail_frame)
        splitter.setSizes([600, 300])

        self.tree.currentItemChanged.connect(self._on_selection_changed)

        layout.addWidget(splitter, 1)

    def _create_stat_card(self, title, value, color):
        frame = QFrame()
        frame.setFixedSize(110, 70)
        frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-left: 4px solid {color};
                border-radius: 10px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 40))
        frame.setGraphicsEffect(shadow)
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(12, 8, 12, 8)
        fl.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px; font-weight: 500;")
        fl.addWidget(t)
        v = QLabel(value)
        v.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
        v.setObjectName("stat_value")
        fl.addWidget(v)
        return frame

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.kod, m.ad, m.ust_merkez_id, m.hat_id,
                       ISNULL(h.kod + ' - ' + ISNULL(h.kisa_ad, h.ad), '-') AS hat_adi,
                       m.aktif_mi, m.aciklama, m.sira
                FROM tanim.is_merkezleri m
                LEFT JOIN tanim.uretim_hatlari h ON m.hat_id = h.id
                ORDER BY m.sira, m.ad
            """)
            rows = cursor.fetchall()

            self.tree.clear()
            items_map = {}
            toplam = len(rows)
            aktif = sum(1 for r in rows if r[6])

            self.toplam_card.findChild(QLabel, "stat_value").setText(str(toplam))
            self.aktif_card.findChild(QLabel, "stat_value").setText(str(aktif))

            # İlk geçiş: ana merkezler
            for row in rows:
                if row[3] is None:  # ust_merkez_id NULL = ana merkez
                    item = QTreeWidgetItem([
                        row[1], row[2], row[5] or '-',
                        "Aktif" if row[6] else "Pasif"
                    ])
                    item.setData(0, Qt.UserRole, row[0])
                    item.setData(0, Qt.UserRole + 1, row[7])  # aciklama
                    if not row[6]:
                        for c in range(4):
                            item.setForeground(c, QColor(brand.TEXT_DIM))
                    self.tree.addTopLevelItem(item)
                    items_map[row[0]] = item

            # İkinci geçiş: alt merkezler
            for row in rows:
                if row[3] is not None and row[3] in items_map:
                    parent = items_map[row[3]]
                    item = QTreeWidgetItem([
                        row[1], row[2], row[5] or '-',
                        "Aktif" if row[6] else "Pasif"
                    ])
                    item.setData(0, Qt.UserRole, row[0])
                    item.setData(0, Qt.UserRole + 1, row[7])
                    if not row[6]:
                        for c in range(4):
                            item.setForeground(c, QColor(brand.TEXT_DIM))
                    parent.addChild(item)
                    items_map[row[0]] = item

            # Üçüncü geçiş: daha derin alt merkezler (3. seviye)
            for row in rows:
                if row[3] is not None and row[3] in items_map and row[0] not in items_map:
                    parent = items_map[row[3]]
                    item = QTreeWidgetItem([
                        row[1], row[2], row[5] or '-',
                        "Aktif" if row[6] else "Pasif"
                    ])
                    item.setData(0, Qt.UserRole, row[0])
                    item.setData(0, Qt.UserRole + 1, row[7])
                    parent.addChild(item)
                    items_map[row[0]] = item

            self.tree.expandAll()

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _on_selection_changed(self, current, previous):
        if not current:
            self.detail_title.setText("Is Merkezi Secin")
            self.detail_info.setText("")
            self.edit_btn.setEnabled(False)
            self.del_btn.setEnabled(False)
            return

        self.edit_btn.setEnabled(True)
        self.del_btn.setEnabled(True)

        kod = current.text(0)
        ad = current.text(1)
        hat = current.text(2)
        durum = current.text(3)
        aciklama = current.data(0, Qt.UserRole + 1) or ''
        alt_sayisi = current.childCount()

        self.detail_title.setText(f"{kod} - {ad}")
        info = f"Bagli Hat: {hat}\nDurum: {durum}\nAlt Merkez Sayisi: {alt_sayisi}"
        if aciklama:
            info += f"\n\nAciklama: {aciklama}"
        self.detail_info.setText(info)

    def _filter_tree(self, text):
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            top_match = text in top.text(0).lower() or text in top.text(1).lower()
            child_match = False
            for j in range(top.childCount()):
                child = top.child(j)
                cm = text in child.text(0).lower() or text in child.text(1).lower()
                child.setHidden(not cm and not top_match and bool(text))
                if cm:
                    child_match = True
            top.setHidden(not top_match and not child_match and bool(text))

    def _add_new(self):
        dlg = IsMerkeziDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _add_sub(self):
        current = self.tree.currentItem()
        ust_id = current.data(0, Qt.UserRole) if current else None
        dlg = IsMerkeziDialog(self.theme, ust_merkez_id=ust_id, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _edit_item(self, item, col):
        merkez_id = item.data(0, Qt.UserRole)
        if merkez_id:
            dlg = IsMerkeziDialog(self.theme, merkez_id=merkez_id, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self._load_data()

    def _edit_selected(self):
        current = self.tree.currentItem()
        if current:
            self._edit_item(current, 0)

    def _delete_selected(self):
        current = self.tree.currentItem()
        if not current:
            return

        merkez_id = current.data(0, Qt.UserRole)
        if current.childCount() > 0:
            QMessageBox.warning(self, "Uyari", "Alt merkezleri olan bir merkez silinemez!\nOnce alt merkezleri silin.")
            return

        if QMessageBox.question(
            self, "Silme Onayi",
            f"{current.text(1)} is merkezini silmek istediginize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tanim.is_merkezleri WHERE id=?", (merkez_id,))
                conn.commit()
                LogManager.log_delete('tanimlar', 'tanim.is_merkezleri', None, 'Is merkezi silindi')
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
