# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Duruş Kayıtları Sayfası
Üretim hattı duruş kayıtları: ekipman seçimi, arıza girişi, bakım entegrasyonu
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QTextEdit, QComboBox, QDateTimeEdit, QWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor

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


def _ensure_columns():
    """Gerekli kolonları kontrol et ve yoksa ekle"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        additions = [
            ("ekipman_id", "BIGINT NULL"),
            ("durum", "NVARCHAR(20) NOT NULL DEFAULT 'ACIK'"),
            ("kapatan_id", "BIGINT NULL"),
            ("kapatma_notu", "NVARCHAR(1000) NULL"),
        ]
        for col_name, col_def in additions:
            cursor.execute(f"""
                IF NOT EXISTS (
                    SELECT 1 FROM sys.columns
                    WHERE object_id = OBJECT_ID('uretim.durus_kayitlari')
                    AND name = '{col_name}'
                )
                ALTER TABLE uretim.durus_kayitlari ADD {col_name} {col_def}
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


class DurusDialog(QDialog):
    """Duruş Kaydı Ekleme/Düzenleme"""

    def __init__(self, theme: dict, durus_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.durus_id = durus_id
        self.data = {}

        self.setWindowTitle("Yeni Duruş Kaydı" if not durus_id else "Duruş Düzenle")
        self.setMinimumSize(580, 680)
        self.setModal(True)

        if durus_id:
            self._load_data()
        self._setup_ui()

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM uretim.durus_kayitlari WHERE id = ?", (self.durus_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
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
            QLabel {{
                color: {s['text']};
                background: transparent;
            }}
            QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {s['text']};
                font-size: 13px;
                min-height: 20px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
                border-color: {s['primary']};
            }}
            QLineEdit:disabled {{
                background: {s['border']};
                color: {s['text_muted']};
            }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                color: {s['text']};
                selection-background-color: {s['primary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        icon = QLabel("🛑")
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

        # Hat Seçimi
        lbl = QLabel("Hat *")
        lbl.setStyleSheet(label_style)
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("-- Hat Seçin --", None)
        self._load_hatlar()
        self.hat_combo.currentIndexChanged.connect(self._on_hat_changed)
        form.addRow(lbl, self.hat_combo)

        # Ekipman Seçimi
        lbl = QLabel("Ekipman")
        lbl.setStyleSheet(label_style)
        self.ekipman_combo = QComboBox()
        self.ekipman_combo.addItem("-- Ekipman Seçin (opsiyonel) --", None)
        form.addRow(lbl, self.ekipman_combo)

        # Duruş Nedeni
        lbl = QLabel("Duruş Nedeni *")
        lbl.setStyleSheet(label_style)
        self.neden_combo = QComboBox()
        self.neden_combo.addItem("-- Neden Seçin --", None)
        self._load_nedenler()
        form.addRow(lbl, self.neden_combo)

        # Başlama Zamanı
        lbl = QLabel("Başlama Zamanı *")
        lbl.setStyleSheet(label_style)
        self.baslama_zamani = QDateTimeEdit()
        self.baslama_zamani.setCalendarPopup(True)
        self.baslama_zamani.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.baslama_zamani.setDateTime(
            self.data.get('baslama_zamani') or QDateTime.currentDateTime()
        )
        form.addRow(lbl, self.baslama_zamani)

        # Bitiş Zamanı
        lbl = QLabel("Bitiş Zamanı")
        lbl.setStyleSheet(label_style)
        self.bitis_zamani = QDateTimeEdit()
        self.bitis_zamani.setCalendarPopup(True)
        self.bitis_zamani.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.bitis_zamani.setDateTime(
            self.data.get('bitis_zamani') or QDateTime.currentDateTime()
        )
        self.bitis_check = QPushButton("Devam Ediyor")
        self.bitis_check.setCheckable(True)
        self.bitis_check.setStyleSheet(f"""
            QPushButton {{
                background: {s['warning']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:checked {{
                background: {s['error']};
            }}
        """)
        self.bitis_check.toggled.connect(lambda c: self.bitis_zamani.setEnabled(not c))
        if not self.data.get('bitis_zamani') and self.durus_id:
            self.bitis_check.setChecked(True)

        bitis_row = QHBoxLayout()
        bitis_row.addWidget(self.bitis_zamani, 1)
        bitis_row.addWidget(self.bitis_check)
        bitis_widget = QWidget()
        bitis_widget.setLayout(bitis_row)
        form.addRow(lbl, bitis_widget)

        # Açıklama (elle arıza girişi)
        lbl = QLabel("Arıza / Açıklama *")
        lbl.setStyleSheet(label_style)
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setMaximumHeight(100)
        self.aciklama_input.setPlaceholderText("Arıza detayını veya duruş nedenini yazın...")
        self.aciklama_input.setText(self.data.get('aciklama', '') or '')
        form.addRow(lbl, self.aciklama_input)

        layout.addLayout(form)
        layout.addStretch()

        # Eğer düzenleme modunda ise, mevcut verileri seç
        if self.data:
            self._set_combo_data()

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
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {s['border']};
                border-color: {s['primary']};
            }}
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
            QPushButton:hover {{
                background: {s['primary_hover']};
            }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_hatlar(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, kod, ad FROM tanim.uretim_hatlari WHERE aktif_mi=1 ORDER BY sira_no"
            )
            for row in cursor.fetchall():
                self.hat_combo.addItem(f"{row[1]} - {row[2]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _on_hat_changed(self):
        """Hat değiştiğinde ekipmanları filtrele"""
        hat_id = self.hat_combo.currentData()
        self.ekipman_combo.clear()
        self.ekipman_combo.addItem("-- Ekipman Seçin (opsiyonel) --", None)
        if not hat_id:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ekipman_kodu, ekipman_adi, durum
                FROM bakim.ekipmanlar
                WHERE hat_id = ? AND aktif_mi = 1 AND silindi_mi = 0
                ORDER BY ekipman_kodu
            """, (hat_id,))
            for row in cursor.fetchall():
                durum_icon = {"CALISIR": "", "ARIZALI": " [ARIZALI]", "BAKIMDA": " [BAKIMDA]"}.get(row[3], "")
                self.ekipman_combo.addItem(f"{row[1]} - {row[2]}{durum_icon}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_nedenler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, kod, ad, kategori FROM tanim.durus_nedenleri WHERE aktif_mi=1 ORDER BY kategori, ad"
            )
            current_cat = None
            for row in cursor.fetchall():
                cat = row[3] or ''
                if cat != current_cat:
                    self.neden_combo.addItem(f"--- {cat} ---", None)
                    idx = self.neden_combo.count() - 1
                    model = self.neden_combo.model()
                    item = model.item(idx)
                    item.setEnabled(False)
                    current_cat = cat
                self.neden_combo.addItem(f"  {row[2]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _set_combo_data(self):
        """Mevcut veriyi combolara yansıt"""
        if self.data.get('hat_id'):
            idx = self.hat_combo.findData(self.data['hat_id'])
            if idx >= 0:
                self.hat_combo.setCurrentIndex(idx)
                # Ekipmanları yükle (hat seçildikten sonra)
                QTimer.singleShot(100, self._set_ekipman)

        if self.data.get('durus_nedeni_id'):
            idx = self.neden_combo.findData(self.data['durus_nedeni_id'])
            if idx >= 0:
                self.neden_combo.setCurrentIndex(idx)

    def _set_ekipman(self):
        if self.data.get('ekipman_id'):
            idx = self.ekipman_combo.findData(self.data['ekipman_id'])
            if idx >= 0:
                self.ekipman_combo.setCurrentIndex(idx)

    def _save(self):
        hat_id = self.hat_combo.currentData()
        neden_id = self.neden_combo.currentData()
        aciklama = self.aciklama_input.toPlainText().strip()

        if not hat_id or not neden_id or not aciklama:
            QMessageBox.warning(self, "Eksik Bilgi", "Hat, Duruş Nedeni ve Açıklama zorunludur!")
            return

        ekipman_id = self.ekipman_combo.currentData()
        baslama = self.baslama_zamani.dateTime().toPython()
        bitis = None if self.bitis_check.isChecked() else self.bitis_zamani.dateTime().toPython()
        sure_dk = None
        if bitis:
            delta = bitis - baslama
            sure_dk = max(1, int(delta.total_seconds() / 60))

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            if self.durus_id:
                cursor.execute("""
                    UPDATE uretim.durus_kayitlari
                    SET hat_id=?, ekipman_id=?, durus_nedeni_id=?,
                        baslama_zamani=?, bitis_zamani=?, sure_dk=?, aciklama=?
                    WHERE id=?
                """, (hat_id, ekipman_id, neden_id, baslama, bitis, sure_dk, aciklama, self.durus_id))
            else:
                cursor.execute("""
                    INSERT INTO uretim.durus_kayitlari
                    (hat_id, ekipman_id, durus_nedeni_id, baslama_zamani, bitis_zamani,
                     sure_dk, aciklama, durum, olusturma_tarihi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'ACIK', GETDATE())
                """, (hat_id, ekipman_id, neden_id, baslama, bitis, sure_dk, aciklama))

                # Ekipman seçildiyse arıza bildirimine de düşür
                if ekipman_id:
                    cursor.execute("""
                        DECLARE @no NVARCHAR(20) = 'DRS-' + FORMAT(GETDATE(),'yyyyMMdd') + '-'
                            + RIGHT('000'+CAST((SELECT ISNULL(MAX(id),0)+1 FROM bakim.ariza_bildirimleri) AS VARCHAR),3);
                        INSERT INTO bakim.ariza_bildirimleri
                        (bildirim_no, ekipman_id, bildirim_zamani, ariza_tanimi, oncelik, durum)
                        VALUES (@no, ?, ?, ?, 'NORMAL', 'ACIK')
                    """, (ekipman_id, baslama, f"[Uretim Durus] {aciklama}"))

            conn.commit()
            LogManager.log_insert('uretim', 'uretim.durus_kayitlari', None, 'Durus kaydi olusturuldu')
            msg = "Durus kaydi kaydedildi!"
            if ekipman_id and not self.durus_id:
                msg += "\nAriza bildirimi de olusturuldu."
            QMessageBox.information(self, "Basarili", msg)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class UretimDurusPage(BasePage):
    """Duruş Kayıtları Sayfası - Tam Implementasyon"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        _ensure_columns()
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # ===== HEADER =====
        header = QHBoxLayout()
        title_section = QVBoxLayout()
        title_section.setSpacing(4)

        title_row = QHBoxLayout()
        icon = QLabel("🛑")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Durus Kayitlari")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)

        subtitle = QLabel("Uretim hatti durus ve ariza kayitlarini yonetin")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()

        # Stat Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        self.acik_label = self._create_stat_card("Acik", "0", s['error'])
        self.devam_label = self._create_stat_card("Devam Eden", "0", s['warning'])
        self.bugun_label = self._create_stat_card("Bugun", "0", s['info'])
        stats_layout.addWidget(self.acik_label)
        stats_layout.addWidget(self.devam_label)
        stats_layout.addWidget(self.bugun_label)
        header.addLayout(stats_layout)

        layout.addLayout(header)

        # ===== TOOLBAR =====
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara (Hat, Ekipman, Aciklama)")
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
        self.search_input.returnPressed.connect(self._load_data)
        toolbar.addWidget(self.search_input)

        combo_style = f"""
            QComboBox {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {s['text']};
                min-width: 130px;
                font-size: 13px;
            }}
            QComboBox:hover {{ border-color: {s['border_light']}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                color: {s['text']};
                selection-background-color: {s['primary']};
            }}
        """

        self.durum_combo = QComboBox()
        self.durum_combo.addItem("Tum Durumlar", None)
        self.durum_combo.addItem("Acik", "ACIK")
        self.durum_combo.addItem("Bakimda", "BAKIMDA")
        self.durum_combo.addItem("Kapali", "KAPALI")
        self.durum_combo.setStyleSheet(combo_style)
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.durum_combo)

        self.hat_filter = QComboBox()
        self.hat_filter.addItem("Tum Hatlar", None)
        self._load_hat_filter()
        self.hat_filter.setStyleSheet(combo_style)
        self.hat_filter.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.hat_filter)

        toolbar.addStretch()

        toolbar.addWidget(self.create_export_button(title="Durus Kayitlari"))

        refresh_btn = QPushButton("Yenile")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {s['border']};
                border-color: {s['primary']};
            }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(refresh_btn)

        add_btn = QPushButton("+ Yeni Durus")
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

        # ===== TABLE =====
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {s['card_bg']};
                border: 1px solid {s['border']};
                border-radius: 10px;
                gridline-color: {s['border']};
                color: {s['text']};
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
                background: rgba(0,0,0,0.3);
                color: {s['text_secondary']};
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid {s['primary']};
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }}
        """)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Hat", "Ekipman", "Durus Nedeni", "Aciklama",
            "Baslama", "Sure (dk)", "Durum", "Islem"
        ])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 130)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 95)
        self.table.setColumnWidth(8, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setFixedSize(120, 70)
        frame.setStyleSheet(f"""
            QFrame {{
                background: {self.s['card_bg']};
                border: 1px solid {self.s['border']};
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

        t_label = QLabel(title)
        t_label.setStyleSheet(f"color: {self.s['text_muted']}; font-size: 11px; font-weight: 500;")
        fl.addWidget(t_label)

        v_label = QLabel(value)
        v_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
        v_label.setObjectName("value_label")
        fl.addWidget(v_label)

        return frame

    def _load_hat_filter(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, kisa_ad FROM tanim.uretim_hatlari WHERE aktif_mi=1 ORDER BY sira_no")
            for row in cursor.fetchall():
                self.hat_filter.addItem(f"{row[1]} - {row[2] or ''}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_data(self):
        s = self.s
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Stats
            cursor.execute("SELECT COUNT(*) FROM uretim.durus_kayitlari WHERE durum='ACIK'")
            self.acik_label.findChild(QLabel, "value_label").setText(str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM uretim.durus_kayitlari WHERE durum='ACIK' AND bitis_zamani IS NULL")
            self.devam_label.findChild(QLabel, "value_label").setText(str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM uretim.durus_kayitlari WHERE CAST(olusturma_tarihi AS DATE) = CAST(GETDATE() AS DATE)")
            self.bugun_label.findChild(QLabel, "value_label").setText(str(cursor.fetchone()[0]))

            # List
            sql = """
                SELECT d.id,
                       h.kod + ' - ' + ISNULL(h.kisa_ad, h.ad) AS hat_adi,
                       ISNULL(e.ekipman_kodu + ' - ' + e.ekipman_adi, '-') AS ekipman,
                       ISNULL(n.ad, '-') AS neden,
                       d.aciklama,
                       d.baslama_zamani,
                       d.sure_dk,
                       d.durum
                FROM uretim.durus_kayitlari d
                JOIN tanim.uretim_hatlari h ON d.hat_id = h.id
                LEFT JOIN bakim.ekipmanlar e ON d.ekipman_id = e.id
                LEFT JOIN tanim.durus_nedenleri n ON d.durus_nedeni_id = n.id
                WHERE 1=1
            """
            params = []

            search = self.search_input.text().strip()
            if search:
                sql += " AND (h.kod LIKE ? OR ISNULL(e.ekipman_kodu,'') LIKE ? OR d.aciklama LIKE ?)"
                params.extend([f"%{search}%"] * 3)

            durum = self.durum_combo.currentData()
            if durum:
                sql += " AND d.durum = ?"
                params.append(durum)

            hat_id = self.hat_filter.currentData()
            if hat_id:
                sql += " AND d.hat_id = ?"
                params.append(hat_id)

            sql += " ORDER BY d.baslama_zamani DESC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            durum_map = {"ACIK": "Acik", "BAKIMDA": "Bakimda", "KAPALI": "Kapali"}
            durum_colors = {"ACIK": s['error'], "BAKIMDA": s['warning'], "KAPALI": s['success']}

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # ID
                item = QTableWidgetItem(str(row[0]))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor(s['text_muted']))
                self.table.setItem(i, 0, item)

                # Hat
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))

                # Ekipman
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or '-'))

                # Neden
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or '-'))

                # Açıklama
                aciklama_text = (row[4] or '')[:60] + ('...' if len(row[4] or '') > 60 else '')
                self.table.setItem(i, 4, QTableWidgetItem(aciklama_text))

                # Başlama
                tarih = row[5].strftime("%d.%m.%Y %H:%M") if row[5] else '-'
                tarih_item = QTableWidgetItem(tarih)
                tarih_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 5, tarih_item)

                # Süre
                sure_text = str(row[6]) if row[6] else "Devam"
                sure_item = QTableWidgetItem(sure_text)
                sure_item.setTextAlignment(Qt.AlignCenter)
                if not row[6]:
                    sure_item.setForeground(QColor(s['warning']))
                self.table.setItem(i, 6, sure_item)

                # Durum
                durum_val = row[7] or 'ACIK'
                durum_item = QTableWidgetItem(durum_map.get(durum_val, durum_val))
                durum_item.setTextAlignment(Qt.AlignCenter)
                durum_item.setForeground(QColor(durum_colors.get(durum_val, s['text'])))
                self.table.setItem(i, 7, durum_item)

                # Action Buttons
                btn_widget = self.create_action_buttons([
                    ("", "Duzenle", lambda _, rid=row[0]: self._edit_item(rid), "edit"),
                    ("", "Sil", lambda _, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 8, btn_widget)
                self.table.setRowHeight(i, 48)

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _add_new(self):
        dlg = DurusDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _edit_item(self, did):
        dlg = DurusDialog(self.theme, did, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _delete_item(self, did):
        if QMessageBox.question(
            self, "Silme Onayi",
            "Bu durus kaydini silmek istediginize emin misiniz?\n\nBu islem geri alinamaz.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM uretim.durus_kayitlari WHERE id=?", (did,))
                conn.commit()
                LogManager.log_delete('uretim', 'uretim.durus_kayitlari', None, 'Durus kaydi silindi')
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
