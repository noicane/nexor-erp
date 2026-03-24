# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Bakım Duruş Talepleri
Üretimden gelen duruş kayıtlarını bakımcının takip ettiği ve kapattığı ekran
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
        'info': t.get('info', '#3B82F6'),
        'bg_main': t.get('bg_main', '#0F1419'),
        'bg_hover': t.get('bg_hover', '#1C2430'),
        'border_light': t.get('border_light', '#2A3545'),
        'card_solid': t.get('bg_card_solid', '#151B23'),
    }


class KapatDialog(QDialog):
    """Duruş Kaydını Kapatma Dialogu"""

    def __init__(self, theme: dict, durus_id: int, durus_bilgi: str, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.durus_id = durus_id

        self.setWindowTitle("Durus Kaydini Kapat")
        self.setMinimumSize(500, 420)
        self.setModal(True)
        self._setup_ui(durus_bilgi)

    def _setup_ui(self, durus_bilgi: str):
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
            QTextEdit, QComboBox, QDateTimeEdit {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {s['text']};
                font-size: 13px;
                min-height: 20px;
            }}
            QTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
                border-color: {s['primary']};
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
        icon = QLabel("✅")
        icon.setStyleSheet("font-size: 28px;")
        header.addWidget(icon)
        title = QLabel("Durus Kaydini Kapat")
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Duruş bilgisi
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background: {s['input_bg']};
                border: 1px solid {s['border']};
                border-left: 4px solid {s['warning']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_label = QLabel(durus_bilgi)
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {s['text_secondary']}; font-size: 12px;")
        info_layout.addWidget(info_label)
        layout.addWidget(info_frame)

        # Form
        form = QFormLayout()
        form.setSpacing(16)
        label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"

        # Bitis zamani
        lbl = QLabel("Bitis Zamani")
        lbl.setStyleSheet(label_style)
        self.bitis_zamani = QDateTimeEdit()
        self.bitis_zamani.setCalendarPopup(True)
        self.bitis_zamani.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.bitis_zamani.setDateTime(QDateTime.currentDateTime())
        form.addRow(lbl, self.bitis_zamani)

        # Yapılan işlem
        lbl = QLabel("Yapilan Islem *")
        lbl.setStyleSheet(label_style)
        self.kapatma_notu = QTextEdit()
        self.kapatma_notu.setMaximumHeight(100)
        self.kapatma_notu.setPlaceholderText("Yapilan bakim/onarim islemini aciklayin...")
        form.addRow(lbl, self.kapatma_notu)

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

        save_btn = QPushButton("Kapat ve Tamamla")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {s['success']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 28px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _save(self):
        kapatma_notu = self.kapatma_notu.toPlainText().strip()
        if not kapatma_notu:
            QMessageBox.warning(self, "Eksik Bilgi", "Yapilan islemi aciklamaniz gerekiyor!")
            return

        bitis = self.bitis_zamani.dateTime().toPython()
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Süreyi hesapla
            cursor.execute("SELECT baslama_zamani FROM uretim.durus_kayitlari WHERE id=?", (self.durus_id,))
            row = cursor.fetchone()
            sure_dk = None
            if row and row[0]:
                delta = bitis - row[0]
                sure_dk = max(1, int(delta.total_seconds() / 60))

            # Duruş kaydını kapat
            cursor.execute("""
                UPDATE uretim.durus_kayitlari
                SET durum = 'KAPALI',
                    bitis_zamani = ?,
                    sure_dk = ?,
                    kapatma_notu = ?,
                    kapatan_id = NULL
                WHERE id = ?
            """, (bitis, sure_dk, kapatma_notu, self.durus_id))

            # İlgili arıza bildirimini de kapat (varsa)
            cursor.execute("""
                UPDATE ab SET ab.durum = 'KAPALI', ab.cozum_zamani = ?
                FROM bakim.ariza_bildirimleri ab
                JOIN uretim.durus_kayitlari dk ON dk.ekipman_id = ab.ekipman_id
                WHERE dk.id = ?
                  AND ab.ariza_tanimi LIKE '%[Uretim Durus]%'
                  AND ab.durum IN ('ACIK', 'ISLEMDE')
                  AND CAST(ab.bildirim_zamani AS DATE) = CAST(dk.baslama_zamani AS DATE)
            """, (bitis, self.durus_id))

            conn.commit()
            LogManager.log_update('bakim', 'uretim.durus_kayitlari', None, 'Durus kaydi kapatildi')
            QMessageBox.information(self, "Basarili", "Durus kaydi kapatildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class BakimDurusTalepPage(BasePage):
    """Bakım Duruş Talepleri - Üretimden gelen açık duruş kayıtları"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
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
        icon = QLabel("🔧")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Durus Talepleri")
        title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)

        subtitle = QLabel("Uretimden gelen durus kayitlarini takip edin ve kapatin")
        subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()

        # Stat Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        self.acik_label = self._create_stat_card("Acik", "0", s['error'])
        self.bakimda_label = self._create_stat_card("Bakimda", "0", s['warning'])
        self.bugun_kapanan = self._create_stat_card("Bugun Kapanan", "0", s['success'])
        stats_layout.addWidget(self.acik_label)
        stats_layout.addWidget(self.bakimda_label)
        stats_layout.addWidget(self.bugun_kapanan)
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
        self.durum_combo.addItem("Acik + Bakimda", "ACIK_BAKIMDA")
        self.durum_combo.addItem("Sadece Acik", "ACIK")
        self.durum_combo.addItem("Sadece Bakimda", "BAKIMDA")
        self.durum_combo.addItem("Kapali", "KAPALI")
        self.durum_combo.addItem("Tumunu Goster", None)
        self.durum_combo.setStyleSheet(combo_style)
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.durum_combo)

        toolbar.addStretch()

        toolbar.addWidget(self.create_export_button(title="Durus Talepleri"))

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
            "Baslama", "Bekleme (dk)", "Durum", "Islem"
        ])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 170)
        self.table.setColumnWidth(3, 130)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 95)
        self.table.setColumnWidth(8, 180)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setFixedSize(130, 70)
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

    def _load_data(self):
        s = self.s
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Stats
            cursor.execute("SELECT COUNT(*) FROM uretim.durus_kayitlari WHERE durum='ACIK'")
            self.acik_label.findChild(QLabel, "value_label").setText(str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM uretim.durus_kayitlari WHERE durum='BAKIMDA'")
            self.bakimda_label.findChild(QLabel, "value_label").setText(str(cursor.fetchone()[0]))

            cursor.execute("""
                SELECT COUNT(*) FROM uretim.durus_kayitlari
                WHERE durum='KAPALI' AND CAST(bitis_zamani AS DATE) = CAST(GETDATE() AS DATE)
            """)
            self.bugun_kapanan.findChild(QLabel, "value_label").setText(str(cursor.fetchone()[0]))

            # List
            sql = """
                SELECT d.id,
                       h.kod + ' - ' + ISNULL(h.kisa_ad, h.ad) AS hat_adi,
                       ISNULL(e.ekipman_kodu + ' - ' + e.ekipman_adi, '-') AS ekipman,
                       ISNULL(n.ad, '-') AS neden,
                       d.aciklama,
                       d.baslama_zamani,
                       CASE WHEN d.bitis_zamani IS NULL
                            THEN DATEDIFF(MINUTE, d.baslama_zamani, GETDATE())
                            ELSE d.sure_dk END AS bekleme_dk,
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
            if durum == "ACIK_BAKIMDA":
                sql += " AND d.durum IN ('ACIK', 'BAKIMDA')"
            elif durum:
                sql += " AND d.durum = ?"
                params.append(durum)

            sql += " ORDER BY CASE d.durum WHEN 'ACIK' THEN 1 WHEN 'BAKIMDA' THEN 2 ELSE 3 END, d.baslama_zamani DESC"
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

                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or '-'))
                self.table.setItem(i, 3, QTableWidgetItem(row[3] or '-'))

                aciklama_text = (row[4] or '')[:60] + ('...' if len(row[4] or '') > 60 else '')
                self.table.setItem(i, 4, QTableWidgetItem(aciklama_text))

                tarih = row[5].strftime("%d.%m.%Y %H:%M") if row[5] else '-'
                tarih_item = QTableWidgetItem(tarih)
                tarih_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 5, tarih_item)

                # Bekleme süresi
                bekleme = row[6]
                if bekleme is not None:
                    if bekleme >= 60:
                        bekleme_text = f"{bekleme // 60}s {bekleme % 60}dk"
                    else:
                        bekleme_text = f"{bekleme} dk"
                else:
                    bekleme_text = "-"
                bekleme_item = QTableWidgetItem(bekleme_text)
                bekleme_item.setTextAlignment(Qt.AlignCenter)
                # Kırmızıya boya eğer uzun süredir açıksa (>120 dk)
                if bekleme and bekleme > 120:
                    bekleme_item.setForeground(QColor(s['error']))
                elif bekleme and bekleme > 60:
                    bekleme_item.setForeground(QColor(s['warning']))
                self.table.setItem(i, 6, bekleme_item)

                # Durum
                durum_val = row[7] or 'ACIK'
                durum_item = QTableWidgetItem(durum_map.get(durum_val, durum_val))
                durum_item.setTextAlignment(Qt.AlignCenter)
                durum_item.setForeground(QColor(durum_colors.get(durum_val, s['text'])))
                self.table.setItem(i, 7, durum_item)

                # Action buttons
                buttons = []
                if durum_val == 'ACIK':
                    buttons.append(("", "Bakima Al", lambda _, rid=row[0]: self._bakima_al(rid), "warning"))
                    buttons.append(("", "Kapat", lambda _, rid=row[0], info=f"{row[1]} | {row[2]}\n{row[4] or ''}": self._kapat(rid, info), "success"))
                elif durum_val == 'BAKIMDA':
                    buttons.append(("", "Kapat", lambda _, rid=row[0], info=f"{row[1]} | {row[2]}\n{row[4] or ''}": self._kapat(rid, info), "success"))

                if buttons:
                    btn_widget = self.create_action_buttons(buttons)
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

    def _bakima_al(self, durus_id):
        """Duruş kaydını 'BAKIMDA' durumuna al"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE uretim.durus_kayitlari SET durum='BAKIMDA' WHERE id=?",
                (durus_id,)
            )
            conn.commit()
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _kapat(self, durus_id, durus_bilgi):
        """Duruş kaydını kapat"""
        dlg = KapatDialog(self.theme, durus_id, durus_bilgi, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
