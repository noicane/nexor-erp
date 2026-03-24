# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Maliyet: Personel Maas & Is Merkezi Atama
Sifre korumali giris, brut/net maas, personeli is merkezine dagitma
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QComboBox, QWidget, QGraphicsDropShadowEffect,
    QCheckBox, QInputDialog, QTabWidget, QSpinBox,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager

# Maliyet modulu sifre (ileride config'den alinabilir)
MALIYET_SIFRE = "nexor2026"


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
        'info': t.get('info', '#3B82F6'),
        'bg_main': t.get('bg_main', '#0F1419'),
        'border_light': t.get('border_light', '#2A3545'),
    }


def _ensure_columns():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for col, defn in [("brut_maas", "DECIMAL(18,2) NULL"), ("net_maas", "DECIMAL(18,2) NULL")]:
            cursor.execute(f"""
                IF NOT EXISTS (
                    SELECT 1 FROM sys.columns
                    WHERE object_id = OBJECT_ID('ik.personeller') AND name = '{col}'
                )
                ALTER TABLE ik.personeller ADD {col} {defn}
            """)

        # maliyet schema + atama tablosu
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name='maliyet')
                EXEC('CREATE SCHEMA maliyet')
        """)
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='personel_is_merkezi' AND schema_id=SCHEMA_ID('maliyet'))
            CREATE TABLE maliyet.personel_is_merkezi (
                id BIGINT IDENTITY(1,1) PRIMARY KEY,
                personel_id BIGINT NOT NULL,
                is_merkezi_id BIGINT NOT NULL,
                yil INT NOT NULL,
                ay INT NOT NULL,
                oran DECIMAL(5,2) NOT NULL DEFAULT 100.00,
                olusturma_tarihi DATETIME2 NOT NULL DEFAULT GETDATE()
            )
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


class MaasDialog(QDialog):
    """Personel Maas Girisi"""

    def __init__(self, theme, personel_id, personel_adi, brut, net, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.personel_id = personel_id

        self.setWindowTitle(f"Maas Girisi - {personel_adi}")
        self.setMinimumSize(420, 320)
        self.setModal(True)
        self._setup_ui(personel_adi, brut, net)

    def _setup_ui(self, personel_adi, brut, net):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }}
            QLabel {{ color: {s['text']}; background: transparent; }}
            QLineEdit {{
                background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px;
                padding: 10px 12px; color: {s['text']}; font-size: 14px; min-height: 20px;
            }}
            QLineEdit:focus {{ border-color: {s['primary']}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header = QHBoxLayout()
        icon = QLabel("💰")
        icon.setStyleSheet("font-size: 28px;")
        header.addWidget(icon)
        title = QLabel(personel_adi)
        title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {s['text']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {s['border']}; max-height: 1px;")
        layout.addWidget(sep)

        form = QFormLayout()
        form.setSpacing(16)
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"

        lbl = QLabel("Brut Maas (TL)")
        lbl.setStyleSheet(label_style)
        self.brut_input = QLineEdit(f"{brut:.2f}" if brut else "")
        self.brut_input.setPlaceholderText("0.00")
        form.addRow(lbl, self.brut_input)

        lbl = QLabel("Net Maas (TL)")
        lbl.setStyleSheet(label_style)
        self.net_input = QLineEdit(f"{net:.2f}" if net else "")
        self.net_input.setPlaceholderText("0.00")
        form.addRow(lbl, self.net_input)

        layout.addLayout(form)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel = QPushButton("Iptal")
        cancel.setStyleSheet(f"""
            QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']};
                border-radius: 8px; padding: 12px 24px; font-size: 13px; }}
            QPushButton:hover {{ background: {s['border']}; }}
        """)
        cancel.clicked.connect(self.reject)
        btn_layout.addWidget(cancel)

        save = QPushButton("Kaydet")
        save.setStyleSheet(f"""
            QPushButton {{ background: {s['primary']}; color: white; border: none;
                border-radius: 8px; padding: 12px 28px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        save.clicked.connect(self._save)
        btn_layout.addWidget(save)
        layout.addLayout(btn_layout)

    def _save(self):
        try:
            brut = float(self.brut_input.text().replace(',', '.')) if self.brut_input.text().strip() else None
            net = float(self.net_input.text().replace(',', '.')) if self.net_input.text().strip() else None
        except ValueError:
            QMessageBox.warning(self, "Hata", "Gecerli bir sayi girin!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE ik.personeller SET brut_maas=?, net_maas=? WHERE id=?",
                           (brut, net, self.personel_id))
            conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class AtamaDialog(QDialog):
    """Personel Is Merkezi Atama"""

    def __init__(self, theme, personel_id, personel_adi, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.personel_id = personel_id

        self.setWindowTitle(f"Is Merkezi Atama - {personel_adi}")
        self.setMinimumSize(480, 400)
        self.setModal(True)
        self._setup_ui(personel_adi)

    def _setup_ui(self, personel_adi):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }}
            QLabel {{ color: {s['text']}; background: transparent; }}
            QComboBox, QSpinBox {{
                background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px;
                padding: 10px 12px; color: {s['text']}; font-size: 13px; min-height: 20px;
            }}
            QComboBox:focus, QSpinBox:focus {{ border-color: {s['primary']}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']}; border: 1px solid {s['border']};
                color: {s['text']}; selection-background-color: {s['primary']};
            }}
            QLineEdit {{
                background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px;
                padding: 10px 12px; color: {s['text']}; font-size: 13px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        icon = QLabel("🏭")
        icon.setStyleSheet("font-size: 24px;")
        header.addWidget(icon)
        title = QLabel(personel_adi)
        title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {s['text']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        form = QFormLayout()
        form.setSpacing(14)
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"

        # Is Merkezi
        lbl = QLabel("Is Merkezi *")
        lbl.setStyleSheet(label_style)
        self.merkez_combo = QComboBox()
        self.merkez_combo.addItem("-- Secin --", None)
        self._load_merkezler()
        form.addRow(lbl, self.merkez_combo)

        # Yil
        lbl = QLabel("Yil")
        lbl.setStyleSheet(label_style)
        self.yil_spin = QSpinBox()
        self.yil_spin.setRange(2020, 2040)
        self.yil_spin.setValue(QDate.currentDate().year())
        form.addRow(lbl, self.yil_spin)

        # Ay
        lbl = QLabel("Ay")
        lbl.setStyleSheet(label_style)
        self.ay_spin = QSpinBox()
        self.ay_spin.setRange(1, 12)
        self.ay_spin.setValue(QDate.currentDate().month())
        form.addRow(lbl, self.ay_spin)

        # Oran
        lbl = QLabel("Oran (%)")
        lbl.setStyleSheet(label_style)
        self.oran_input = QLineEdit("100")
        self.oran_input.setPlaceholderText("100")
        form.addRow(lbl, self.oran_input)

        layout.addLayout(form)

        # Mevcut atamalar
        info = QLabel("Not: Bir personel ayni ayda birden fazla is merkezine oranlara gore dagitilabilir.")
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {s['text_muted']}; font-size: 12px;")
        layout.addWidget(info)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel = QPushButton("Iptal")
        cancel.setStyleSheet(f"""
            QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']};
                border-radius: 8px; padding: 12px 24px; font-size: 13px; }}
        """)
        cancel.clicked.connect(self.reject)
        btn_layout.addWidget(cancel)

        save = QPushButton("Ata")
        save.setStyleSheet(f"""
            QPushButton {{ background: {s['success']}; color: white; border: none;
                border-radius: 8px; padding: 12px 28px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: #059669; }}
        """)
        save.clicked.connect(self._save)
        btn_layout.addWidget(save)
        layout.addLayout(btn_layout)

    def _load_merkezler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.kod, m.ad,
                       ISNULL(p.kod + ' > ', '') AS parent_prefix
                FROM tanim.is_merkezleri m
                LEFT JOIN tanim.is_merkezleri p ON m.ust_merkez_id = p.id
                WHERE m.aktif_mi = 1
                ORDER BY ISNULL(p.sira, m.sira), m.sira, m.ad
            """)
            for row in cursor.fetchall():
                prefix = row[3] if row[3] else ''
                self.merkez_combo.addItem(f"{prefix}{row[1]} - {row[2]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _save(self):
        merkez_id = self.merkez_combo.currentData()
        if not merkez_id:
            QMessageBox.warning(self, "Eksik", "Is merkezi secin!")
            return

        try:
            oran = float(self.oran_input.text().replace(',', '.'))
        except ValueError:
            QMessageBox.warning(self, "Hata", "Gecerli bir oran girin!")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO maliyet.personel_is_merkezi (personel_id, is_merkezi_id, yil, ay, oran)
                VALUES (?, ?, ?, ?, ?)
            """, (self.personel_id, merkez_id, self.yil_spin.value(), self.ay_spin.value(), oran))
            conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class TopluAtamaDialog(QDialog):
    """Is Merkezi Sec -> Personelleri Coklu Sec -> Toplu Ata"""

    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.setWindowTitle("Toplu Is Merkezi Atama")
        self.setMinimumSize(600, 600)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }}
            QLabel {{ color: {s['text']}; background: transparent; }}
            QComboBox, QSpinBox, QLineEdit {{
                background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px;
                padding: 10px 12px; color: {s['text']}; font-size: 13px; min-height: 20px;
            }}
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{ border-color: {s['primary']}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']}; border: 1px solid {s['border']};
                color: {s['text']}; selection-background-color: {s['primary']};
            }}
            QListWidget {{
                background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px;
                color: {s['text']}; font-size: 13px;
            }}
            QListWidget::item {{ padding: 6px 10px; }}
            QListWidget::item:selected {{ background: {s['primary']}; }}
            QCheckBox {{ color: {s['text']}; font-size: 13px; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        icon = QLabel("🏭")
        icon.setStyleSheet("font-size: 28px;")
        header.addWidget(icon)
        title = QLabel("Toplu Is Merkezi Atama")
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {s['border']}; max-height: 1px;")
        layout.addWidget(sep)

        # Is Merkezi + Yil/Ay/Oran
        form = QFormLayout()
        form.setSpacing(12)
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"

        lbl = QLabel("Is Merkezi *")
        lbl.setStyleSheet(label_style)
        self.merkez_combo = QComboBox()
        self.merkez_combo.addItem("-- Secin --", None)
        self._load_merkezler()
        form.addRow(lbl, self.merkez_combo)

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)

        self.yil_spin = QSpinBox()
        self.yil_spin.setRange(2020, 2040)
        self.yil_spin.setValue(QDate.currentDate().year())
        self.yil_spin.setPrefix("Yil: ")
        row_layout.addWidget(self.yil_spin)

        self.ay_spin = QSpinBox()
        self.ay_spin.setRange(1, 12)
        self.ay_spin.setValue(QDate.currentDate().month())
        self.ay_spin.setPrefix("Ay: ")
        row_layout.addWidget(self.ay_spin)

        self.oran_input = QLineEdit("100")
        self.oran_input.setFixedWidth(80)
        self.oran_input.setPlaceholderText("%")
        row_layout.addWidget(QLabel("Oran:"))
        row_layout.addWidget(self.oran_input)

        lbl = QLabel("Donem / Oran")
        lbl.setStyleSheet(label_style)
        form.addRow(lbl, row_widget)

        layout.addLayout(form)

        # Personel arama + liste
        search_row = QHBoxLayout()
        self.p_search = QLineEdit()
        self.p_search.setPlaceholderText("Personel ara...")
        self.p_search.textChanged.connect(self._filter_personel)
        search_row.addWidget(self.p_search)

        select_all_btn = QPushButton("Hepsini Sec")
        select_all_btn.setStyleSheet(f"""
            QPushButton {{ background: {s['info']}; color: white; border: none;
                border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: 600; }}
            QPushButton:hover {{ background: #2563EB; }}
        """)
        select_all_btn.clicked.connect(self._select_all)
        search_row.addWidget(select_all_btn)

        clear_btn = QPushButton("Temizle")
        clear_btn.setStyleSheet(f"""
            QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']};
                border-radius: 6px; padding: 8px 16px; font-size: 12px; }}
        """)
        clear_btn.clicked.connect(self._clear_all)
        search_row.addWidget(clear_btn)

        layout.addLayout(search_row)

        self.personel_list = QListWidget()
        self.personel_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self._load_personeller()
        layout.addWidget(self.personel_list, 1)

        # Secim sayisi
        self.secim_label = QLabel("0 personel secili")
        self.secim_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 12px;")
        self.personel_list.itemSelectionChanged.connect(self._update_secim)
        layout.addWidget(self.secim_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel = QPushButton("Iptal")
        cancel.setStyleSheet(f"""
            QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']};
                border-radius: 8px; padding: 12px 24px; font-size: 13px; }}
        """)
        cancel.clicked.connect(self.reject)
        btn_layout.addWidget(cancel)

        save = QPushButton("Secilenleri Ata")
        save.setStyleSheet(f"""
            QPushButton {{ background: {s['success']}; color: white; border: none;
                border-radius: 8px; padding: 12px 28px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: #059669; }}
        """)
        save.clicked.connect(self._save)
        btn_layout.addWidget(save)
        layout.addLayout(btn_layout)

    def _load_merkezler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.kod, m.ad,
                       ISNULL(p.kod + ' > ', '') AS parent_prefix
                FROM tanim.is_merkezleri m
                LEFT JOIN tanim.is_merkezleri p ON m.ust_merkez_id = p.id
                WHERE m.aktif_mi = 1
                ORDER BY ISNULL(p.sira, m.sira), m.sira, m.ad
            """)
            for row in cursor.fetchall():
                prefix = row[3] if row[3] else ''
                self.merkez_combo.addItem(f"{prefix}{row[1]} - {row[2]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_personeller(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.sicil_no, p.ad + ' ' + p.soyad, ISNULL(d.ad, '')
                FROM ik.personeller p
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                WHERE p.aktif_mi = 1
                ORDER BY p.ad, p.soyad
            """)
            for row in cursor.fetchall():
                dept = f" ({row[3]})" if row[3] else ''
                item = QListWidgetItem(f"{row[1]} - {row[2]}{dept}")
                item.setData(Qt.UserRole, row[0])
                self.personel_list.addItem(item)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _filter_personel(self, text):
        text = text.lower()
        for i in range(self.personel_list.count()):
            item = self.personel_list.item(i)
            item.setHidden(bool(text) and text not in item.text().lower())

    def _select_all(self):
        for i in range(self.personel_list.count()):
            item = self.personel_list.item(i)
            if not item.isHidden():
                item.setSelected(True)
        self._update_secim()

    def _clear_all(self):
        self.personel_list.clearSelection()
        self._update_secim()

    def _update_secim(self):
        count = len(self.personel_list.selectedItems())
        self.secim_label.setText(f"{count} personel secili")

    def _save(self):
        merkez_id = self.merkez_combo.currentData()
        if not merkez_id:
            QMessageBox.warning(self, "Eksik", "Is merkezi secin!")
            return

        selected = self.personel_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Eksik", "En az bir personel secin!")
            return

        try:
            oran = float(self.oran_input.text().replace(',', '.'))
        except ValueError:
            QMessageBox.warning(self, "Hata", "Gecerli bir oran girin!")
            return

        yil = self.yil_spin.value()
        ay = self.ay_spin.value()

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            count = 0
            for item in selected:
                pid = item.data(Qt.UserRole)
                # Ayni ay/merkez varsa guncelle, yoksa ekle
                cursor.execute("""
                    IF EXISTS (
                        SELECT 1 FROM maliyet.personel_is_merkezi
                        WHERE personel_id=? AND is_merkezi_id=? AND yil=? AND ay=?
                    )
                        UPDATE maliyet.personel_is_merkezi SET oran=?
                        WHERE personel_id=? AND is_merkezi_id=? AND yil=? AND ay=?
                    ELSE
                        INSERT INTO maliyet.personel_is_merkezi (personel_id, is_merkezi_id, yil, ay, oran)
                        VALUES (?, ?, ?, ?, ?)
                """, (pid, merkez_id, yil, ay,
                      oran, pid, merkez_id, yil, ay,
                      pid, merkez_id, yil, ay, oran))
                count += 1
            conn.commit()
            QMessageBox.information(self, "Basarili", f"{count} personel is merkezine atandi.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class MaliyetPersonelPage(BasePage):
    """Personel Maas & Is Merkezi Atama - Sifre Korumali"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self.authenticated = False
        self.maas_gorunum = "brut"  # brut veya net
        _ensure_columns()
        self._setup_ui()

    def _setup_ui(self):
        s = self.s
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)

        # Sifre ekrani
        self.lock_widget = QWidget()
        lock_layout = QVBoxLayout(self.lock_widget)
        lock_layout.setAlignment(Qt.AlignCenter)
        lock_layout.setSpacing(16)

        lock_icon = QLabel("🔒")
        lock_icon.setAlignment(Qt.AlignCenter)
        lock_icon.setStyleSheet("font-size: 48px;")
        lock_layout.addWidget(lock_icon)

        lock_title = QLabel("Maliyet Modulu - Sifre Gerekli")
        lock_title.setAlignment(Qt.AlignCenter)
        lock_title.setStyleSheet(f"color: {s['text']}; font-size: 20px; font-weight: 600;")
        lock_layout.addWidget(lock_title)

        lock_sub = QLabel("Bu bolum hassas maas bilgileri icerir")
        lock_sub.setAlignment(Qt.AlignCenter)
        lock_sub.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        lock_layout.addWidget(lock_sub)

        pw_row = QHBoxLayout()
        pw_row.addStretch()
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setPlaceholderText("Sifre girin...")
        self.pw_input.setFixedWidth(280)
        self.pw_input.setStyleSheet(f"""
            QLineEdit {{
                background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px;
                padding: 12px 16px; color: {s['text']}; font-size: 14px;
            }}
            QLineEdit:focus {{ border-color: {s['primary']}; }}
        """)
        self.pw_input.returnPressed.connect(self._check_password)
        pw_row.addWidget(self.pw_input)

        pw_btn = QPushButton("Giris")
        pw_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['primary']}; color: white; border: none;
                border-radius: 8px; padding: 12px 24px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {s['primary_hover']}; }}
        """)
        pw_btn.clicked.connect(self._check_password)
        pw_row.addWidget(pw_btn)
        pw_row.addStretch()
        lock_layout.addLayout(pw_row)

        self.main_layout.addWidget(self.lock_widget)

        # Icerik (gizli baslar)
        self.content_widget = QWidget()
        self.content_widget.setVisible(False)
        self._setup_content()
        self.main_layout.addWidget(self.content_widget, 1)

    def _check_password(self):
        if self.pw_input.text() == MALIYET_SIFRE:
            self.authenticated = True
            self.lock_widget.setVisible(False)
            self.content_widget.setVisible(True)
            self._load_data()
        else:
            QMessageBox.warning(self, "Hata", "Yanlis sifre!")
            self.pw_input.clear()

    def _setup_content(self):
        s = self.s
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title_section = QVBoxLayout()
        title_section.setSpacing(4)

        title_row = QHBoxLayout()
        icon = QLabel("💰")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Personel Maliyet Yonetimi")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)

        subtitle = QLabel("Maas girisi, brut/net secimi ve is merkezi dagitimi")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()

        # Stat cards
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.personel_card = self._create_stat_card("Personel", "0", s['info'])
        self.atanmis_card = self._create_stat_card("Atanmis", "0", s['success'])
        self.toplam_maas_card = self._create_stat_card("Toplam Maas", "0", s['warning'])
        stats.addWidget(self.personel_card)
        stats.addWidget(self.atanmis_card)
        stats.addWidget(self.toplam_maas_card)
        header.addLayout(stats)

        layout.addLayout(header)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara (Sicil, Ad, Soyad)")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px;
                padding: 10px 14px; color: {s['text']}; font-size: 13px; min-width: 220px;
            }}
            QLineEdit:focus {{ border-color: {s['primary']}; }}
        """)
        self.search_input.returnPressed.connect(self._load_data)
        toolbar.addWidget(self.search_input)

        combo_style = f"""
            QComboBox {{
                background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px;
                padding: 10px 12px; color: {s['text']}; font-size: 13px; min-width: 120px;
            }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']}; border: 1px solid {s['border']};
                color: {s['text']}; selection-background-color: {s['primary']};
            }}
        """

        # Brut/Net secimi
        self.maas_tipi_combo = QComboBox()
        self.maas_tipi_combo.addItem("Brut Maas Goster", "brut")
        self.maas_tipi_combo.addItem("Net Maas Goster", "net")
        self.maas_tipi_combo.setStyleSheet(combo_style)
        self.maas_tipi_combo.currentIndexChanged.connect(self._on_maas_tipi_changed)
        toolbar.addWidget(self.maas_tipi_combo)

        # Departman filtresi
        self.dept_combo = QComboBox()
        self.dept_combo.addItem("Tum Departmanlar", None)
        self.dept_combo.setStyleSheet(combo_style)
        self.dept_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.dept_combo)

        toolbar.addStretch()

        refresh_btn = QPushButton("Yenile")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']};
                border-radius: 8px; padding: 10px 14px; font-size: 13px; color: {s['text']}; }}
            QPushButton:hover {{ background: {s['border']}; }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(refresh_btn)

        toplu_btn = QPushButton("Toplu Is Merkezi Ata")
        toplu_btn.setStyleSheet(f"""
            QPushButton {{ background: {s['success']}; color: white; border: none;
                border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: #059669; }}
        """)
        toplu_btn.clicked.connect(self._toplu_atama)
        toolbar.addWidget(toplu_btn)

        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px;
                gridline-color: {s['border']}; color: {s['text']};
            }}
            QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }}
            QTableWidget::item:selected {{ background: {s['primary']}; }}
            QTableWidget::item:hover {{ background: rgba(220, 38, 38, 0.08); }}
            QHeaderView::section {{
                background: rgba(0,0,0,0.3); color: {s['text_secondary']};
                padding: 12px 8px; border: none; border-bottom: 2px solid {s['primary']};
                font-weight: 600; font-size: 12px;
            }}
        """)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Sicil No", "Ad Soyad", "Departman", "Maas (TL)",
            "Is Merkezi", "Atama Ay", "Oran %", "Islem"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 70)
        self.table.setColumnWidth(7, 180)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

    def _create_stat_card(self, title, value, color):
        frame = QFrame()
        frame.setFixedSize(130, 70)
        frame.setStyleSheet(f"""
            QFrame {{ background: {self.s['card_bg']}; border: 1px solid {self.s['border']};
                border-left: 4px solid {color}; border-radius: 10px; }}
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
        t.setStyleSheet(f"color: {self.s['text_muted']}; font-size: 11px; font-weight: 500;")
        fl.addWidget(t)
        v = QLabel(value)
        v.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        v.setObjectName("value_label")
        fl.addWidget(v)
        return frame

    def _on_maas_tipi_changed(self):
        self.maas_gorunum = self.maas_tipi_combo.currentData()
        if self.authenticated:
            self._load_data()

    def _load_data(self):
        s = self.s
        maas_col = "brut_maas" if self.maas_gorunum == "brut" else "net_maas"

        # Load departmanlar (once)
        if self.dept_combo.count() <= 1:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, ad FROM ik.departmanlar WHERE aktif_mi=1 ORDER BY ad")
                for row in cursor.fetchall():
                    self.dept_combo.addItem(row[1], row[0])
            except Exception:
                pass
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            dept_filter = ""
            params = []
            dept_id = self.dept_combo.currentData()
            if dept_id:
                dept_filter = " AND p.departman_id = ?"
                params.append(dept_id)

            search = self.search_input.text().strip()
            search_filter = ""
            if search:
                search_filter = " AND (p.sicil_no LIKE ? OR p.ad LIKE ? OR p.soyad LIKE ?)"
                params.extend([f"%{search}%"] * 3)

            # Personel + son atama
            sql = f"""
                SELECT p.id, p.sicil_no, p.ad + ' ' + p.soyad AS ad_soyad,
                       ISNULL(d.ad, '-') AS departman,
                       p.{maas_col},
                       m.merkez_adi, m.yil, m.ay, m.oran
                FROM ik.personeller p
                LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
                OUTER APPLY (
                    SELECT TOP 1 im.kod + ' - ' + im.ad AS merkez_adi,
                           pim.yil, pim.ay, pim.oran
                    FROM maliyet.personel_is_merkezi pim
                    JOIN tanim.is_merkezleri im ON pim.is_merkezi_id = im.id
                    WHERE pim.personel_id = p.id
                    ORDER BY pim.yil DESC, pim.ay DESC
                ) m
                WHERE p.aktif_mi = 1
                {dept_filter}
                {search_filter}
                ORDER BY p.ad, p.soyad
            """
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # Stats
            personel_count = len(rows)
            atanmis_count = sum(1 for r in rows if r[5])
            toplam_maas = sum(r[4] or 0 for r in rows)

            self.personel_card.findChild(QLabel, "value_label").setText(str(personel_count))
            self.atanmis_card.findChild(QLabel, "value_label").setText(str(atanmis_count))
            self.toplam_maas_card.findChild(QLabel, "value_label").setText(f"{toplam_maas:,.0f}")

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # Sicil
                item = QTableWidgetItem(str(row[1] or ''))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 0, item)

                # Ad Soyad
                self.table.setItem(i, 1, QTableWidgetItem(row[2] or ''))

                # Departman
                self.table.setItem(i, 2, QTableWidgetItem(row[3] or '-'))

                # Maas
                maas_val = row[4]
                maas_text = f"{maas_val:,.2f}" if maas_val else "-"
                maas_item = QTableWidgetItem(maas_text)
                maas_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if maas_val:
                    maas_item.setForeground(QColor(s['success']))
                else:
                    maas_item.setForeground(QColor(s['text_muted']))
                self.table.setItem(i, 3, maas_item)

                # Is Merkezi
                merkez_text = row[5] or "Atanmamis"
                merkez_item = QTableWidgetItem(merkez_text)
                if not row[5]:
                    merkez_item.setForeground(QColor(s['text_muted']))
                self.table.setItem(i, 4, merkez_item)

                # Ay
                ay_text = f"{row[7]:02d}/{row[6]}" if row[6] else "-"
                ay_item = QTableWidgetItem(ay_text)
                ay_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 5, ay_item)

                # Oran
                oran_text = f"{row[8]:.0f}%" if row[8] else "-"
                oran_item = QTableWidgetItem(oran_text)
                oran_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 6, oran_item)

                # Buttons
                btn_widget = self.create_action_buttons([
                    ("", "Maas Gir", lambda _, pid=row[0], pn=row[2], b=row[4] if self.maas_gorunum == 'brut' else None, n=row[4] if self.maas_gorunum == 'net' else None: self._edit_maas(pid, pn), "edit"),
                    ("", "Is Merkezi Ata", lambda _, pid=row[0], pn=row[2]: self._atama(pid, pn), "success"),
                ])
                self.table.setCellWidget(i, 7, btn_widget)
                self.table.setRowHeight(i, 46)

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _edit_maas(self, personel_id, personel_adi):
        conn = None
        brut = net = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT brut_maas, net_maas FROM ik.personeller WHERE id=?", (personel_id,))
            row = cursor.fetchone()
            if row:
                brut, net = row[0], row[1]
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        dlg = MaasDialog(self.theme, personel_id, personel_adi or '', brut, net, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _atama(self, personel_id, personel_adi):
        dlg = AtamaDialog(self.theme, personel_id, personel_adi or '', parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _toplu_atama(self):
        dlg = TopluAtamaDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
