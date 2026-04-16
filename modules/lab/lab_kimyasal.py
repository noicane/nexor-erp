# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kimyasal Takviye Kayitlari
========================================
El Kitabi v3 uyumlu: brand token, emoji-free, responsive
stok.urunler (kimyasal tipi) + ik.personeller
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QDoubleSpinBox, QTextEdit, QComboBox,
    QDateTimeEdit, QWidget, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand


class TakviyeDialog(QDialog):
    """Kimyasal Takviye Ekleme/Duzenleme — el kitabi uyumlu"""

    def __init__(self, theme: dict, takviye_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.takviye_id = takviye_id
        self.data = {}

        self.setWindowTitle("Yeni Takviye" if not takviye_id else "Takviye Duzenle")
        self.setMinimumSize(brand.sp(550), brand.sp(580))
        self.setModal(True)

        if takviye_id:
            self._load_data()
        self._setup_ui()

    def _load_data(self):
        """Mevcut takviye verisini yukle"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM uretim.banyo_takviyeler WHERE id = ?", (self.takviye_id,))
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
        """UI olustur"""
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
                font-family: {brand.FONT_FAMILY};
            }}
            QLabel {{ color: {brand.TEXT}; background: transparent; }}
            QComboBox, QDoubleSpinBox, QDateTimeEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:hover, QDoubleSpinBox:hover, QDateTimeEdit:hover {{
                border-color: {brand.BORDER_HARD};
            }}
            QComboBox:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus {{
                border-color: {brand.PRIMARY};
            }}
            QComboBox::drop-down {{ border: none; width: {brand.sp(30)}px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                color: {brand.TEXT};
                selection-background-color: {brand.PRIMARY};
            }}
            QTextEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
            }}
            QTextEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # Header
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)

        accent = QFrame()
        accent.setFixedSize(brand.SP_1, brand.sp(32))
        accent.setStyleSheet(f"background: {brand.PRIMARY}; border-radius: 2px;")
        header.addWidget(accent)

        title = QLabel(self.windowTitle())
        title.setStyleSheet(
            f"color: {brand.TEXT}; "
            f"font-size: {brand.FS_HEADING}px; "
            f"font-weight: {brand.FW_SEMIBOLD};"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Ayirici
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {brand.BORDER}; max-height: 1px;")
        layout.addWidget(sep)

        # Form
        form = QFormLayout()
        form.setSpacing(brand.SP_4)
        form.setLabelAlignment(Qt.AlignRight)
        label_style = (
            f"color: {brand.TEXT_MUTED}; "
            f"font-size: {brand.FS_BODY}px; "
            f"font-weight: {brand.FW_MEDIUM};"
        )

        # Banyo
        lbl = QLabel("Banyo *")
        lbl.setStyleSheet(label_style)
        self.banyo_combo = QComboBox()
        self.banyo_combo.addItem("-- Banyo Secin --", None)
        self._load_banyolar()
        form.addRow(lbl, self.banyo_combo)

        # Kimyasal
        lbl = QLabel("Kimyasal *")
        lbl.setStyleSheet(label_style)
        self.kimyasal_combo = QComboBox()
        self.kimyasal_combo.addItem("-- Kimyasal Secin --", None)
        self._load_kimyasallar()
        form.addRow(lbl, self.kimyasal_combo)

        # Tarih
        lbl = QLabel("Tarih")
        lbl.setStyleSheet(label_style)
        self.tarih_input = QDateTimeEdit()
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.tarih_input.setDateTime(self.data.get('tarih') or QDateTime.currentDateTime())
        form.addRow(lbl, self.tarih_input)

        # Miktar
        lbl = QLabel("Miktar *")
        lbl.setStyleSheet(label_style)
        self.miktar_input = QDoubleSpinBox()
        self.miktar_input.setRange(0, 99999)
        self.miktar_input.setDecimals(2)
        self.miktar_input.setValue(self.data.get('miktar', 0) or 0)
        form.addRow(lbl, self.miktar_input)

        # Birim
        lbl = QLabel("Birim *")
        lbl.setStyleSheet(label_style)
        self.birim_combo = QComboBox()
        self.birim_combo.addItem("-- Birim Secin --", None)
        self._load_birimler()
        form.addRow(lbl, self.birim_combo)

        # Neden
        lbl = QLabel("Takviye Nedeni")
        lbl.setStyleSheet(label_style)
        self.neden_combo = QComboBox()
        self.neden_combo.addItem("-- Seciniz --", None)
        self.neden_combo.addItem("Periyodik Takviye", "PERIYODIK")
        self.neden_combo.addItem("Analiz Sonucu", "ANALIZ")
        self.neden_combo.addItem("Ilk Dolum", "ILK_DOLUM")
        self.neden_combo.addItem("Duzeltme", "DUZELTME")
        self.neden_combo.addItem("Diger", "DIGER")
        if self.data.get('takviye_nedeni'):
            idx = self.neden_combo.findData(self.data['takviye_nedeni'])
            if idx >= 0:
                self.neden_combo.setCurrentIndex(idx)
        form.addRow(lbl, self.neden_combo)

        # Yapan
        lbl = QLabel("Yapan Personel *")
        lbl.setStyleSheet(label_style)
        self.yapan_combo = QComboBox()
        self.yapan_combo.addItem("-- Personel Secin --", None)
        self._load_personel()
        form.addRow(lbl, self.yapan_combo)

        # Notlar
        lbl = QLabel("Notlar")
        lbl.setStyleSheet(label_style)
        self.notlar_input = QTextEdit()
        self.notlar_input.setMaximumHeight(brand.sp(80))
        self.notlar_input.setPlaceholderText("Ek notlar...")
        self.notlar_input.setText(self.data.get('notlar', '') or '')
        form.addRow(lbl, self.notlar_input)

        layout.addLayout(form)
        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(brand.sp(38))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; border-color: {brand.BORDER_HARD}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(brand.sp(38))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_banyolar(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.id, b.kod, b.ad, h.kod as hat_kodu
                FROM uretim.banyo_tanimlari b
                LEFT JOIN tanim.uretim_hatlari h ON b.hat_id = h.id
                WHERE b.aktif_mi = 1 ORDER BY h.sira_no, b.kod
            """)
            for row in cursor.fetchall():
                self.banyo_combo.addItem(f"{row[3] or 'N/A'} / {row[1]} - {row[2]}", row[0])
            if self.data.get('banyo_id'):
                idx = self.banyo_combo.findData(self.data['banyo_id'])
                if idx >= 0:
                    self.banyo_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_kimyasallar(self):
        """Kimyasal tipindeki urunler - stokta olanlar onde"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.urun_kodu, u.urun_adi,
                       ISNULL((SELECT SUM(ISNULL(sb.miktar,0)) FROM stok.stok_bakiye sb WHERE sb.urun_id = u.id AND ISNULL(sb.bloke_mi,0) = 0), 0) as stok
                FROM stok.urunler u
                LEFT JOIN stok.urun_tipleri ut ON u.urun_tipi_id = ut.id
                WHERE (ut.kod IN ('KIMYASAL','HAMMADDE','YARDIMCI') OR u.urun_tipi IN ('KIMYASAL','HAMMADDE','YARDIMCI'))
                  AND ISNULL(u.aktif_mi, 1) = 1 AND ISNULL(u.silindi_mi, 0) = 0
                ORDER BY u.urun_kodu
            """)
            for row in cursor.fetchall():
                stok = float(row[3] or 0)
                stok_txt = f" [{stok:.0f}]" if stok > 0 else ""
                self.kimyasal_combo.addItem(f"{row[1]} - {row[2]}{stok_txt}", row[0])
            if self.data.get('kimyasal_id'):
                idx = self.kimyasal_combo.findData(self.data['kimyasal_id'])
                if idx >= 0:
                    self.kimyasal_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_birimler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.birimler WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.birim_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            if self.data.get('birim_id'):
                idx = self.birim_combo.findData(self.data['birim_id'])
                if idx >= 0:
                    self.birim_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_personel(self):
        """ik.personeller tablosu"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ad, soyad, sicil_no
                FROM ik.personeller
                WHERE aktif_mi = 1 AND silindi_mi = 0
                ORDER BY ad, soyad
            """)
            for row in cursor.fetchall():
                display = f"{row[1]} {row[2]}" + (f" ({row[3]})" if row[3] else "")
                self.yapan_combo.addItem(display, row[0])
            if self.data.get('yapan_id'):
                idx = self.yapan_combo.findData(self.data['yapan_id'])
                if idx >= 0:
                    self.yapan_combo.setCurrentIndex(idx)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _save(self):
        banyo_id = self.banyo_combo.currentData()
        kimyasal_id = self.kimyasal_combo.currentData()
        miktar = self.miktar_input.value()
        birim_id = self.birim_combo.currentData()
        yapan_id = self.yapan_combo.currentData()

        if not banyo_id or not kimyasal_id or not miktar or not birim_id or not yapan_id:
            QMessageBox.warning(self, "Eksik Bilgi",
                "Zorunlu alanlar:\n- Banyo\n- Kimyasal\n- Miktar\n- Birim\n- Yapan Personel")
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            params = (banyo_id, self.tarih_input.dateTime().toPython(), kimyasal_id,
                     miktar, birim_id, self.neden_combo.currentData(), yapan_id,
                     self.notlar_input.toPlainText().strip() or None)

            if self.takviye_id:
                cursor.execute("""UPDATE uretim.banyo_takviyeler SET banyo_id=?, tarih=?, kimyasal_id=?,
                    miktar=?, birim_id=?, takviye_nedeni=?, yapan_id=?, notlar=? WHERE id=?""",
                    params + (self.takviye_id,))
            else:
                cursor.execute("""INSERT INTO uretim.banyo_takviyeler
                    (banyo_id, tarih, kimyasal_id, miktar, birim_id, takviye_nedeni, yapan_id, notlar)
                    VALUES (?,?,?,?,?,?,?,?)""", params)

            # Stoktan dus (FIFO lot bul)
            stok_msg = ""
            if not self.takviye_id:
                cursor.execute("SELECT kod FROM tanim.birimler WHERE id = ?", (birim_id,))
                birim_row = cursor.fetchone()
                birim_kod = birim_row[0] if birim_row else 'KG'

                cursor.execute("""
                    SELECT TOP 1 id, lot_no, miktar FROM stok.stok_bakiye
                    WHERE urun_id = ? AND ISNULL(bloke_mi, 0) = 0
                      AND ISNULL(ISNULL(kullanilabilir_miktar, miktar), 0) > 0
                    ORDER BY giris_tarihi ASC
                """, (kimyasal_id,))
                bakiye = cursor.fetchone()

                if bakiye:
                    bakiye_id, lot_no = bakiye[0], bakiye[1]
                    cursor.execute("""
                        INSERT INTO stok.stok_hareketleri
                        (uuid, hareket_tipi, hareket_nedeni, tarih, urun_id, depo_id,
                         miktar, birim_id, lot_no, referans_tip, aciklama, olusturma_tarihi)
                        VALUES (NEWID(), 'CIKIS', 'KIMYASAL_TUKETIM', GETDATE(), ?,
                                (SELECT depo_id FROM stok.stok_bakiye WHERE id = ?),
                                ?, ?, ?, 'BANYO_TAKVIYE', ?, GETDATE())
                    """, (kimyasal_id, bakiye_id, miktar, birim_id, lot_no,
                          f"Banyo takviye - {self.banyo_combo.currentText()[:50]}"))

                    cursor.execute("""
                        UPDATE stok.stok_bakiye SET miktar = miktar - ?,
                            son_hareket_tarihi = GETDATE()
                        WHERE id = ?
                    """, (miktar, bakiye_id))
                    stok_msg = f"\nStoktan dusuldu (Lot: {lot_no})"
                else:
                    stok_msg = "\nStok kaydi bulunamadi - sadece takviye kaydedildi"

            conn.commit()
            LogManager.log_insert('lab', 'uretim.banyo_takviyeler', None, 'Kimyasal takviye kaydedildi')
            QMessageBox.information(self, "Basarili", f"Takviye kaydedildi!{stok_msg if not self.takviye_id else ''}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class LabKimyasalPage(BasePage):
    """Kimyasal Takviye Kayitlari Listesi — el kitabi uyumlu sayfa"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # -- 1. Header --
        header = self.create_page_header(
            "Kimyasal Takviyeler",
            "Banyo kimyasal takviye kayitlarini yonetin"
        )
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(
            f"color: {brand.TEXT_DIM}; font-size: {brand.FS_BODY_SM}px; "
            f"padding: {brand.SP_2}px {brand.SP_4}px; "
            f"background: {brand.BG_CARD}; border-radius: {brand.R_SM}px;"
        )
        header.addWidget(self.stat_label)

        btn_yenile = self.create_primary_button("Yenile")
        btn_yenile.clicked.connect(self._load_data)
        header.addWidget(btn_yenile)

        layout.addLayout(header)

        # -- 2. Toolbar --
        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)

        fl = QLabel("Filtre:")
        fl.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px;")
        toolbar.addWidget(fl)

        self.banyo_combo = QComboBox()
        self.banyo_combo.addItem("Tum Banyolar", None)
        self._load_banyo_filter()
        self.banyo_combo.setStyleSheet(f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                min-width: {brand.sp(220)}px;
                font-size: {brand.FS_BODY}px;
            }}
            QComboBox:hover {{ border-color: {brand.BORDER_HARD}; }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
            QComboBox::drop-down {{ border: none; width: {brand.sp(30)}px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                color: {brand.TEXT};
                selection-background-color: {brand.PRIMARY};
            }}
        """)
        self.banyo_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.banyo_combo)
        toolbar.addStretch()

        add_btn = QPushButton("Yeni Takviye")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(brand.sp(38))
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                border-radius: {brand.R_SM}px;
                padding: 0 {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_new)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        # -- 3. Table --
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Banyo", "Kimyasal", "Tarih", "Miktar", "Neden", "Yapan", "Islem"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, brand.sp(60))
        self.table.setColumnWidth(1, brand.sp(100))
        self.table.setColumnWidth(3, brand.sp(140))
        self.table.setColumnWidth(4, brand.sp(100))
        self.table.setColumnWidth(5, brand.sp(120))
        self.table.setColumnWidth(6, brand.sp(130))
        self.table.setColumnWidth(7, brand.sp(120))
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(42))
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_2}px {brand.SP_3}px;
                border-bottom: 1px solid {brand.BORDER};
                color: {brand.TEXT};
            }}
            QTableWidget::item:alternate {{ background: {brand.BG_MAIN}; }}
            QTableWidget::item:selected {{ background: {brand.BG_SELECTED}; }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_2}px;
                border: none;
                border-bottom: 2px solid {brand.PRIMARY};
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
        """)
        layout.addWidget(self.table, 1)

    def _load_banyo_filter(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.id, b.kod, h.kod as hat_kodu
                FROM uretim.banyo_tanimlari b
                LEFT JOIN tanim.uretim_hatlari h ON b.hat_id = h.id
                WHERE b.aktif_mi = 1 ORDER BY h.sira_no, b.kod
            """)
            for row in cursor.fetchall():
                self.banyo_combo.addItem(f"{row[2] or 'N/A'} / {row[1]}", row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """
                SELECT t.id, b.kod, u.urun_kodu + ' - ' + u.urun_adi, t.tarih,
                       CONCAT(CAST(t.miktar AS VARCHAR), ' ', br.kod), t.takviye_nedeni,
                       p.ad + ' ' + p.soyad
                FROM uretim.banyo_takviyeler t
                JOIN uretim.banyo_tanimlari b ON t.banyo_id = b.id
                JOIN stok.urunler u ON t.kimyasal_id = u.id
                JOIN tanim.birimler br ON t.birim_id = br.id
                JOIN ik.personeller p ON t.yapan_id = p.id
                WHERE 1=1
            """
            params = []
            banyo_id = self.banyo_combo.currentData()
            if banyo_id:
                sql += " AND t.banyo_id = ?"
                params.append(banyo_id)
            sql += " ORDER BY t.tarih DESC"

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            neden_map = {
                "PERIYODIK": ("Periyodik", brand.INFO),
                "ANALIZ": ("Analiz", brand.WARNING),
                "ILK_DOLUM": ("Ilk Dolum", brand.SUCCESS),
                "DUZELTME": ("Duzeltme", brand.ERROR),
                "DIGER": ("Diger", brand.TEXT_DIM)
            }

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # ID
                item = QTableWidgetItem(str(row[0]))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor(brand.TEXT_DIM))
                self.table.setItem(i, 0, item)

                self.table.setItem(i, 1, QTableWidgetItem(row[1] or '-'))
                self.table.setItem(i, 2, QTableWidgetItem(row[2] or '-'))

                tarih = row[3].strftime("%d.%m.%Y %H:%M") if row[3] else '-'
                item = QTableWidgetItem(tarih)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 3, item)

                item = QTableWidgetItem(row[4] or '-')
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, 4, item)

                neden_info = neden_map.get(row[5], ("-", brand.TEXT_DIM))
                item = QTableWidgetItem(neden_info[0])
                item.setForeground(QColor(neden_info[1]))
                self.table.setItem(i, 5, item)

                self.table.setItem(i, 6, QTableWidgetItem(row[6] or '-'))

                # Butonlar
                widget = self.create_action_buttons([
                    ("Duzenle", "Duzenle", lambda checked, rid=row[0]: self._edit_item(rid), "edit"),
                    ("Sil", "Sil", lambda checked, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 7, widget)

            self.stat_label.setText(f"Toplam: {len(rows)} kayit")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _add_new(self):
        dlg = TakviyeDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _edit_item(self, tid):
        dlg = TakviyeDialog(self.theme, tid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _delete_item(self, tid):
        if QMessageBox.question(self, "Sil?", "Bu kaydi silmek istediginize emin misiniz?",
                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM uretim.banyo_takviyeler WHERE id=?", (tid,))
                conn.commit()
                LogManager.log_delete('lab', 'uretim.banyo_takviyeler', None, 'Kayit silindi')
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
