# -*- coding: utf-8 -*-
"""
NEXOR ERP - Durus Kayitlari Sayfasi (Brand System)
==================================================
Uretim hatti durus kayitlari: ekipman secimi, ariza girisi, bakim entegrasyonu.
Tum stiller core.nexor_brand uzerinden gelir; sabit px/hex yazilmaz.
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QTextEdit, QComboBox, QDateTimeEdit, QWidget,
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor, QPainter, QPen, QBrush

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand


# =============================================================================
# BRAND ICON - kompakt, bu dosyaya ozel
# =============================================================================

class BrandIcon(QLabel):
    def __init__(self, kind: str, color: str = None, size: int = None, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.color = color or brand.TEXT
        self.size_px = size or brand.ICON_MD
        self.setFixedSize(self.size_px, self.size_px)
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(self.color))
        pen.setWidthF(max(1.4, self.size_px / 12))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        s = self.size_px
        m = s * 0.18
        k = self.kind

        if k == "stop":
            p.setBrush(QBrush(QColor(self.color)))
            p.drawRoundedRect(int(m), int(m), int(s - 2 * m), int(s - 2 * m),
                              int(s * 0.08), int(s * 0.08))
        elif k == "alert":
            p.drawLine(int(s * 0.5), int(m), int(s - m), int(s - m))
            p.drawLine(int(s - m), int(s - m), int(m), int(s - m))
            p.drawLine(int(m), int(s - m), int(s * 0.5), int(m))
            p.drawLine(int(s * 0.5), int(s * 0.38), int(s * 0.5), int(s * 0.62))
            p.setBrush(QBrush(QColor(self.color)))
            p.drawEllipse(int(s * 0.46), int(s * 0.7), int(s * 0.08), int(s * 0.08))
        elif k == "plus":
            p.drawLine(int(s * 0.5), int(m), int(s * 0.5), int(s - m))
            p.drawLine(int(m), int(s * 0.5), int(s - m), int(s * 0.5))
        elif k == "refresh":
            from PySide6.QtCore import QRectF
            rect = QRectF(m, m, s - 2 * m, s - 2 * m)
            p.drawArc(rect, 45 * 16, 270 * 16)
            p.drawLine(int(s - m * 1.2), int(m), int(s - m * 1.2), int(m * 2.2))
            p.drawLine(int(s - m * 1.2), int(m * 2.2), int(s - m * 2.4), int(m * 2.2))
        p.end()


def _soft(color_hex: str, alpha: float = 0.12) -> str:
    c = QColor(color_hex)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


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
    """Durus Kaydi Ekleme/Duzenleme"""

    def __init__(self, theme: dict, durus_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.durus_id = durus_id
        self.data = {}

        self.setWindowTitle("Yeni Durus Kaydi" if not durus_id else "Durus Duzenle")
        self.setMinimumSize(brand.sp(580), brand.sp(680))
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
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_ELEVATED};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
            }}
            QLabel {{
                color: {brand.TEXT};
                background: transparent;
            }}
            QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY}px;
                min-height: {brand.sp(20)}px;
            }}
            QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QDateTimeEdit:hover {{
                border-color: {brand.BORDER_HARD};
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
                border-color: {brand.PRIMARY};
            }}
            QLineEdit:disabled, QDateTimeEdit:disabled {{
                background: {brand.BG_HOVER};
                color: {brand.TEXT_DISABLED};
            }}
            QComboBox::drop-down {{ border: none; width: {brand.sp(28)}px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_ELEVATED};
                border: 1px solid {brand.BORDER};
                color: {brand.TEXT};
                selection-background-color: {brand.PRIMARY};
                selection-color: white;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_6, brand.SP_6, brand.SP_6, brand.SP_6)
        layout.setSpacing(brand.SP_5)

        # Header
        header = QHBoxLayout()
        header.setSpacing(brand.SP_3)

        icon_box = QFrame()
        icon_box.setFixedSize(brand.sp(36), brand.sp(36))
        icon_box.setStyleSheet(
            f"background: {_soft(brand.ERROR, 0.12)}; "
            f"border: 1px solid {_soft(brand.ERROR, 0.35)}; "
            f"border-radius: {brand.R_SM}px;"
        )
        ib = QVBoxLayout(icon_box)
        ib.setContentsMargins(0, 0, 0, 0)
        ib.addWidget(BrandIcon("stop", brand.ERROR, brand.sp(18)), 0, Qt.AlignCenter)
        header.addWidget(icon_box)

        title = QLabel(self.windowTitle())
        title.setStyleSheet(
            f"font-size: {brand.FS_HEADING_LG}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; "
            f"color: {brand.TEXT};"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

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
            f"font-size: {brand.FS_BODY_SM}px; "
            f"font-weight: {brand.FW_MEDIUM};"
        )

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
        self.bitis_check.setCursor(Qt.PointingHandCursor)
        self.bitis_check.setStyleSheet(f"""
            QPushButton {{
                background: {brand.WARNING};
                color: white;
                border: 1px solid {brand.WARNING};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:checked {{
                background: {brand.ERROR};
                border-color: {brand.ERROR};
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
        btn_layout.setSpacing(brand.SP_3)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_3}px {brand.SP_5}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: 1px solid {brand.PRIMARY};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_3}px {brand.SP_6}px;
                font-size: {brand.FS_BODY}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{
                background: {brand.PRIMARY_HOVER};
                border-color: {brand.PRIMARY_HOVER};
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
                ariza_id = None
                ekipman_adi = ""
                if ekipman_id:
                    cursor.execute("""
                        DECLARE @no NVARCHAR(20) = 'DRS-' + FORMAT(GETDATE(),'yyyyMMdd') + '-'
                            + RIGHT('000'+CAST((SELECT ISNULL(MAX(id),0)+1 FROM bakim.ariza_bildirimleri) AS VARCHAR),3);
                        INSERT INTO bakim.ariza_bildirimleri
                        (bildirim_no, ekipman_id, bildirim_zamani, ariza_tanimi, oncelik, durum)
                        OUTPUT INSERTED.id
                        VALUES (@no, ?, ?, ?, 'NORMAL', 'ACIK')
                    """, (ekipman_id, baslama, f"[Uretim Durus] {aciklama}"))
                    row = cursor.fetchone()
                    if row:
                        ariza_id = int(row[0])

                    # Ekipman adini cek (bildirim mesaji icin)
                    try:
                        cursor.execute(
                            "SELECT ekipman_adi FROM bakim.ekipmanlar WHERE id = ?",
                            (ekipman_id,),
                        )
                        er = cursor.fetchone()
                        if er:
                            ekipman_adi = er[0] or ""
                    except Exception:
                        ekipman_adi = ""

            conn.commit()
            LogManager.log_insert('uretim', 'uretim.durus_kayitlari', None, 'Durus kaydi olusturuldu')

            # Nexor kullanicilarina bildirim dus (sadece yeni kayitta)
            bildirilen = 0
            if ekipman_id and ariza_id and not self.durus_id:
                try:
                    from core.bildirim_service import BildirimService
                    from core.database import execute_query
                    kullanicilar = execute_query(
                        "SELECT id FROM sistem.kullanicilar "
                        "WHERE aktif_mi = 1 AND silindi_mi = 0"
                    )
                    baslik = f"Uretim Ariza: {ekipman_adi or 'Ekipman'}"
                    mesaj = (
                        f"Uretim durus kaydi ile ariza bildirildi.\n"
                        f"Ekipman: {ekipman_adi or '-'}\n"
                        f"Aciklama: {aciklama or '-'}"
                    )
                    for k in kullanicilar:
                        if BildirimService.gonder(
                            kullanici_id=k['id'],
                            baslik=baslik, mesaj=mesaj,
                            modul='URETIM', onem='YUKSEK', tip='UYARI',
                            kaynak_tablo='bakim.ariza_bildirimleri',
                            kaynak_id=ariza_id,
                            sayfa_yonlendirme='bakim_ariza',
                        ):
                            bildirilen += 1
                except Exception as bild_err:
                    print(f"[UretimDurus] Bildirim gonderme hatasi: {bild_err}")

            msg = "Durus kaydi kaydedildi!"
            if ekipman_id and not self.durus_id:
                msg += "\nAriza bildirimi de olusturuldu."
                if bildirilen:
                    msg += f"\n{bildirilen} Nexor kullanicisina bildirim dusuruldu."
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
    """Durus Kayitlari Sayfasi"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        _ensure_columns()
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: {brand.BG_MAIN};
                color: {brand.TEXT};
                font-family: {brand.FONT_FAMILY};
                font-size: {brand.FS_BODY}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(brand.SP_10, brand.SP_10, brand.SP_10, brand.SP_10)
        layout.setSpacing(brand.SP_6)

        # ===== HEADER =====
        header = QHBoxLayout()
        header.setSpacing(brand.SP_4)

        title_col = QVBoxLayout()
        title_col.setSpacing(brand.SP_2)

        title_row = QHBoxLayout()
        title_row.setSpacing(brand.SP_3)
        title_row.setContentsMargins(0, 0, 0, 0)

        icon_box = QFrame()
        icon_box.setFixedSize(brand.sp(40), brand.sp(40))
        icon_box.setStyleSheet(
            f"background: {_soft(brand.ERROR, 0.12)}; "
            f"border: 1px solid {_soft(brand.ERROR, 0.35)}; "
            f"border-radius: {brand.R_SM}px;"
        )
        ib = QVBoxLayout(icon_box)
        ib.setContentsMargins(0, 0, 0, 0)
        ib.addWidget(BrandIcon("stop", brand.ERROR, brand.sp(20)), 0, Qt.AlignCenter)
        title_row.addWidget(icon_box)

        title = QLabel("Durus Kayitlari")
        title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: {brand.FS_TITLE}px; "
            f"font-weight: {brand.FW_BOLD}; letter-spacing: -0.4px;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        title_col.addLayout(title_row)

        subtitle = QLabel("Uretim hatti durus ve ariza kayitlarini yonetin")
        subtitle.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_BODY}px;"
        )
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        # Stat Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(brand.SP_3)
        self.acik_label = self._create_stat_card("Acik", "0", brand.ERROR)
        self.devam_label = self._create_stat_card("Devam Eden", "0", brand.WARNING)
        self.bugun_label = self._create_stat_card("Bugun", "0", brand.INFO)
        stats_layout.addWidget(self.acik_label)
        stats_layout.addWidget(self.devam_label)
        stats_layout.addWidget(self.bugun_label)
        header.addLayout(stats_layout)

        layout.addLayout(header)

        # ===== TOOLBAR =====
        toolbar = QHBoxLayout()
        toolbar.setSpacing(brand.SP_3)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara (Hat, Ekipman, Aciklama)")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                font-size: {brand.FS_BODY_SM}px;
                min-width: {brand.sp(240)}px;
            }}
            QLineEdit:hover {{ border-color: {brand.BORDER_HARD}; }}
            QLineEdit:focus {{ border-color: {brand.PRIMARY}; }}
        """)
        self.search_input.returnPressed.connect(self._load_data)
        toolbar.addWidget(self.search_input)

        combo_style = f"""
            QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_3}px;
                color: {brand.TEXT};
                min-width: {brand.sp(140)}px;
                font-size: {brand.FS_BODY_SM}px;
            }}
            QComboBox:hover {{ border-color: {brand.BORDER_HARD}; }}
            QComboBox:focus {{ border-color: {brand.PRIMARY}; }}
            QComboBox::drop-down {{ border: none; width: {brand.sp(28)}px; }}
            QComboBox QAbstractItemView {{
                background: {brand.BG_ELEVATED};
                border: 1px solid {brand.BORDER};
                color: {brand.TEXT};
                selection-background-color: {brand.PRIMARY};
                selection-color: white;
            }}
        """

        self.durum_combo = QComboBox()
        self.durum_combo.addItem("Tum Durumlar", None)
        self.durum_combo.addItem("Acik", "ACIK")
        self.durum_combo.addItem("Bakimda", "BAKIMDA")
        self.durum_combo.addItem("Kapali", "KAPALI")
        self.durum_combo.setStyleSheet(combo_style)
        self.durum_combo.setCursor(Qt.PointingHandCursor)
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.durum_combo)

        self.hat_filter = QComboBox()
        self.hat_filter.addItem("Tum Hatlar", None)
        self._load_hat_filter()
        self.hat_filter.setStyleSheet(combo_style)
        self.hat_filter.setCursor(Qt.PointingHandCursor)
        self.hat_filter.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.hat_filter)

        toolbar.addStretch()

        toolbar.addWidget(self.create_export_button(title="Durus Kayitlari"))

        refresh_btn = QPushButton("Yenile")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_4}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_MEDIUM};
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
                border-color: {brand.BORDER_HARD};
            }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        toolbar.addWidget(refresh_btn)

        add_btn = QPushButton("Yeni Durus")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {brand.PRIMARY};
                color: white;
                border: 1px solid {brand.PRIMARY};
                border-radius: {brand.R_SM}px;
                padding: {brand.SP_2}px {brand.SP_5}px;
                font-size: {brand.FS_BODY_SM}px;
                font-weight: {brand.FW_SEMIBOLD};
            }}
            QPushButton:hover {{
                background: {brand.PRIMARY_HOVER};
                border-color: {brand.PRIMARY_HOVER};
            }}
        """)
        add_btn.clicked.connect(self._add_new)
        toolbar.addWidget(add_btn)

        layout.addLayout(toolbar)

        # ===== TABLE =====
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD};
                color: {brand.TEXT};
                border: 1px solid {brand.BORDER};
                border-radius: {brand.R_LG}px;
                gridline-color: transparent;
                font-size: {brand.FS_BODY}px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: {brand.SP_2}px {brand.SP_3}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
            }}
            QTableWidget::item:selected {{
                background: {_soft(brand.PRIMARY, 0.18)};
                color: {brand.TEXT};
            }}
            QTableWidget::item:hover {{
                background: {brand.BG_HOVER};
            }}
            QHeaderView::section {{
                background: {brand.BG_SURFACE};
                color: {brand.TEXT_MUTED};
                padding: {brand.SP_3}px {brand.SP_3}px;
                border: none;
                border-bottom: 1px solid {brand.BORDER};
                font-weight: {brand.FW_SEMIBOLD};
                font-size: {brand.FS_CAPTION}px;
                letter-spacing: 0.5px;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: {brand.sp(8)}px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {brand.BORDER_HARD};
                border-radius: {brand.sp(4)}px;
                min-height: {brand.sp(30)}px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "HAT", "EKIPMAN", "DURUS NEDENI", "ACIKLAMA",
            "BASLAMA", "SURE (DK)", "DURUM", "ISLEM"
        ])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.setColumnWidth(0, brand.sp(50))
        self.table.setColumnWidth(1, brand.sp(140))
        self.table.setColumnWidth(2, brand.sp(170))
        self.table.setColumnWidth(3, brand.sp(140))
        self.table.setColumnWidth(5, brand.sp(130))
        self.table.setColumnWidth(6, brand.sp(90))
        self.table.setColumnWidth(7, brand.sp(100))
        self.table.setColumnWidth(8, brand.sp(140))
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(brand.sp(44))
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.NoFrame)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table, 1)

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setFixedSize(brand.sp(140), brand.sp(76))
        frame.setStyleSheet(f"""
            QFrame {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-left: 3px solid {color};
                border-radius: {brand.R_MD}px;
            }}
        """)

        fl = QVBoxLayout(frame)
        fl.setContentsMargins(brand.SP_3, brand.SP_2, brand.SP_3, brand.SP_2)
        fl.setSpacing(brand.SP_1)

        t_label = QLabel(title.upper())
        t_label.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: {brand.FS_CAPTION}px; "
            f"font-weight: {brand.FW_SEMIBOLD}; letter-spacing: 0.6px; "
            f"background: transparent; border: none;"
        )
        fl.addWidget(t_label)

        v_label = QLabel(value)
        v_label.setStyleSheet(
            f"color: {color}; font-size: {brand.FS_HEADING_LG}px; "
            f"font-weight: {brand.FW_BOLD}; "
            f"background: transparent; border: none;"
        )
        v_label.setObjectName("stat_value")
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
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Stats
            cursor.execute("SELECT COUNT(*) FROM uretim.durus_kayitlari WHERE durum='ACIK'")
            self.acik_label.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM uretim.durus_kayitlari WHERE durum='ACIK' AND bitis_zamani IS NULL")
            self.devam_label.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM uretim.durus_kayitlari WHERE CAST(olusturma_tarihi AS DATE) = CAST(GETDATE() AS DATE)")
            self.bugun_label.findChild(QLabel, "stat_value").setText(str(cursor.fetchone()[0]))

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
            durum_colors = {"ACIK": brand.ERROR, "BAKIMDA": brand.WARNING, "KAPALI": brand.SUCCESS}

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # ID
                item = QTableWidgetItem(str(row[0]))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor(brand.TEXT_DIM))
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

                # Sure
                sure_text = str(row[6]) if row[6] else "Devam"
                sure_item = QTableWidgetItem(sure_text)
                sure_item.setTextAlignment(Qt.AlignCenter)
                if not row[6]:
                    sure_item.setForeground(QColor(brand.WARNING))
                self.table.setItem(i, 6, sure_item)

                # Durum
                durum_val = row[7] or 'ACIK'
                durum_item = QTableWidgetItem(durum_map.get(durum_val, durum_val))
                durum_item.setTextAlignment(Qt.AlignCenter)
                durum_item.setForeground(QColor(durum_colors.get(durum_val, brand.TEXT)))
                self.table.setItem(i, 7, durum_item)

                # Action Buttons
                btn_widget = self.create_action_buttons([
                    ("", "Duzenle", lambda _, rid=row[0]: self._edit_item(rid), "edit"),
                    ("", "Sil", lambda _, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 8, btn_widget)

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
