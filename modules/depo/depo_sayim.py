# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Stok Sayım Sayfası
[MODERNIZED UI - v2.0]
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QWidget, QDialog,
    QFormLayout, QDateEdit, QTextEdit, QCheckBox, QSplitter,
    QListWidget, QListWidgetItem, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
# Sayim tamamlandiginda stok.stok_bakiye ve stok.stok_hareketleri tablolarina direkt yazilir


def _ensure_sayim_tables():
    """stok.sayimlar ve stok.sayim_detaylari tablolarini olusturur (yoksa)"""
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute("SELECT SCHEMA_ID('stok')")
        if cursor.fetchone()[0] is None:
            cursor.execute("EXEC('CREATE SCHEMA stok')")
            conn.commit()
        cursor.execute("SELECT OBJECT_ID('stok.sayimlar')")
        if cursor.fetchone()[0] is None:
            cursor.execute("""CREATE TABLE stok.sayimlar (
                id INT IDENTITY(1,1) PRIMARY KEY,
                sayim_no NVARCHAR(50) NOT NULL,
                sayim_tipi NVARCHAR(30) NOT NULL,
                depo_id INT,
                sayim_tarihi DATE DEFAULT GETDATE(),
                aciklama NVARCHAR(500),
                durum NVARCHAR(20) DEFAULT 'TASLAK',
                olusturma_tarihi DATETIME DEFAULT GETDATE()
            )""")
            conn.commit()
        cursor.execute("SELECT OBJECT_ID('stok.sayim_detaylari')")
        if cursor.fetchone()[0] is None:
            cursor.execute("""CREATE TABLE stok.sayim_detaylari (
                id BIGINT IDENTITY(1,1) PRIMARY KEY,
                sayim_id INT NOT NULL,
                urun_id BIGINT NOT NULL,
                urun_kodu NVARCHAR(50),
                urun_adi NVARCHAR(250),
                urun_tipi NVARCHAR(100),
                birim NVARCHAR(20),
                sistem_miktari DECIMAL(18,4) DEFAULT 0,
                sayilan_miktar DECIMAL(18,4) NULL,
                fark DECIMAL(18,4) NULL,
                notlar NVARCHAR(500),
                durum NVARCHAR(20) DEFAULT 'BEKLIYOR',
                olusturma_tarihi DATETIME DEFAULT GETDATE()
            )""")
            conn.commit()
        conn.close()
    except Exception:
        pass

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

class SayimOlusturDialog(QDialog):
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme; self.s = get_modern_style(theme)
        self.setWindowTitle("Yeni Sayım Oluştur"); self.setMinimumSize(500, 400); self.setModal(True)
        self._setup_ui(); self._load_combos()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }} QLabel {{ color: {s['text']}; }} QLineEdit, QComboBox, QDateEdit, QTextEdit {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; }}")
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        header = QHBoxLayout(); icon = QLabel("📋"); icon.setStyleSheet("font-size: 28px;"); header.addWidget(icon)
        title = QLabel(self.windowTitle()); title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};"); header.addWidget(title); header.addStretch()
        layout.addLayout(header)
        form = QFormLayout(); form.setSpacing(14); label_style = f"color: {s['text_secondary']}; font-size: 13px; font-weight: 500;"
        lbl = QLabel("Sayım Tipi *"); lbl.setStyleSheet(label_style); self.cmb_tip = QComboBox(); self.cmb_tip.addItems(["TAM_SAYIM", "SPOT_SAYIM", "DEVIR_SAYIMI"]); form.addRow(lbl, self.cmb_tip)
        lbl = QLabel("Depo *"); lbl.setStyleSheet(label_style); self.cmb_depo = QComboBox(); form.addRow(lbl, self.cmb_depo)
        lbl = QLabel("Sayım Tarihi"); lbl.setStyleSheet(label_style); self.date_sayim = QDateEdit(); self.date_sayim.setDate(QDate.currentDate()); self.date_sayim.setCalendarPopup(True); form.addRow(lbl, self.date_sayim)
        lbl = QLabel("Açıklama"); lbl.setStyleSheet(label_style); self.txt_aciklama = QTextEdit(); self.txt_aciklama.setMaximumHeight(60); form.addRow(lbl, self.txt_aciklama)
        layout.addLayout(form); layout.addStretch()
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(12); btn_layout.addStretch()
        btn_iptal = QPushButton("İptal"); btn_iptal.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }}"); btn_iptal.clicked.connect(self.reject); btn_layout.addWidget(btn_iptal)
        btn_olustur = QPushButton("📋 Sayım Oluştur"); btn_olustur.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}"); btn_olustur.clicked.connect(self._olustur); btn_layout.addWidget(btn_olustur)
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            self.cmb_depo.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM tanim.depolar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall(): self.cmb_depo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception: pass
    
    def _olustur(self):
        if not self.cmb_depo.currentData(): QMessageBox.warning(self, "⚠️ Uyarı", "Depo seçimi zorunludur!"); return
        try:
            _ensure_sayim_tables()
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT 'SYM-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM stok.sayimlar), 0) + 1 AS VARCHAR), 4)")
            sayim_no = cursor.fetchone()[0]
            cursor.execute("INSERT INTO stok.sayimlar (sayim_no, sayim_tipi, depo_id, sayim_tarihi, aciklama, durum) VALUES (?, ?, ?, ?, ?, 'TASLAK')", (sayim_no, self.cmb_tip.currentText(), self.cmb_depo.currentData(), self.date_sayim.date().toPython(), self.txt_aciklama.toPlainText().strip() or None))
            conn.commit(); conn.close(); self.accept()
            LogManager.log_insert('depo', 'stok.sayimlar', None, 'Sayim kaydi olustu')
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))

class SayimDetayDialog(QDialog):
    """Sayım detay ekranı - Grup bazlı ürün çekme ve miktar girişi"""
    def __init__(self, sayim_id, theme: dict, parent=None):
        super().__init__(parent)
        self.sayim_id = sayim_id
        self.theme = theme; self.s = get_modern_style(theme)
        self.setWindowTitle("Sayım Detay"); self.setMinimumSize(1100, 700); self.setModal(True)
        _ensure_sayim_tables()
        self._setup_ui()
        self._load_header()
        self._load_grup_listesi()
        self._load_detaylar()

    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"""
            QDialog {{ background: {s['bg_main']}; }}
            QLabel {{ color: {s['text']}; }}
            QLineEdit, QComboBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 8px; color: {s['text']}; }}
            QListWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px; color: {s['text']}; }}
            QListWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }}
            QListWidget::item:selected {{ background: {s['primary']}; }}
            QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; color: {s['text']}; }}
            QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {s['border']}; }}
            QTableWidget::item:selected {{ background: {s['primary']}; }}
            QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 10px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 12px; }}
        """)
        layout = QVBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(16)

        # Baslik
        header = QHBoxLayout()
        icon = QLabel("📋"); icon.setStyleSheet("font-size: 28px;"); header.addWidget(icon)
        self.lbl_title = QLabel("Sayım Detay"); self.lbl_title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['text']};"); header.addWidget(self.lbl_title)
        header.addStretch()
        self.lbl_durum = QLabel(""); self.lbl_durum.setStyleSheet(f"padding: 6px 16px; border-radius: 6px; font-weight: 600;"); header.addWidget(self.lbl_durum)
        layout.addLayout(header)

        # Info bar
        self.lbl_info = QLabel(""); self.lbl_info.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px; padding: 8px 12px; background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px;")
        layout.addWidget(self.lbl_info)

        # Ana icerik: Sol grup listesi + Sag tablo
        content = QHBoxLayout(); content.setSpacing(16)

        # Sol panel - Grup secimi
        left_panel = QVBoxLayout(); left_panel.setSpacing(10)
        lbl_grup = QLabel("Ürün Grubu Seç"); lbl_grup.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {s['text']};")
        left_panel.addWidget(lbl_grup)

        self.lst_gruplar = QListWidget()
        self.lst_gruplar.setMaximumWidth(250); self.lst_gruplar.setMinimumWidth(200)
        left_panel.addWidget(self.lst_gruplar, 1)

        btn_ekle = QPushButton("📥 Grubu Sayıma Ekle"); btn_ekle.setCursor(Qt.PointingHandCursor)
        btn_ekle.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px; font-weight: 600; }} QPushButton:hover {{ background: #0EA472; }}")
        btn_ekle.clicked.connect(self._grup_ekle)
        left_panel.addWidget(btn_ekle)

        left_frame = QFrame(); left_frame.setLayout(left_panel)
        content.addWidget(left_frame)

        # Sag panel - Detay tablosu
        right_panel = QVBoxLayout(); right_panel.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout(); toolbar.setSpacing(10)
        self.lbl_satir = QLabel("0 kalem"); self.lbl_satir.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px;")
        toolbar.addWidget(self.lbl_satir)
        toolbar.addStretch()
        self.txt_ara = QLineEdit(); self.txt_ara.setPlaceholderText("Ürün ara..."); self.txt_ara.setMaximumWidth(250)
        self.txt_ara.textChanged.connect(self._filtrele)
        toolbar.addWidget(self.txt_ara)
        right_panel.addLayout(toolbar)

        # Tablo: urun_kodu, urun_adi, urun_tipi, birim, sistem_miktari, sayilan_miktar, fark, durum
        self.tbl_detay = QTableWidget()
        self.tbl_detay.setColumnCount(8)
        self.tbl_detay.setHorizontalHeaderLabels(["Stok Kodu", "Ürün Adı", "Grup", "Birim", "Sistem Stok", "Sayılan", "Fark", "Durum"])
        self.tbl_detay.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_detay.setColumnWidth(0, 120); self.tbl_detay.setColumnWidth(2, 100); self.tbl_detay.setColumnWidth(3, 70)
        self.tbl_detay.setColumnWidth(4, 100); self.tbl_detay.setColumnWidth(5, 110); self.tbl_detay.setColumnWidth(6, 90); self.tbl_detay.setColumnWidth(7, 90)
        self.tbl_detay.verticalHeader().setVisible(False)
        self.tbl_detay.setSelectionBehavior(QAbstractItemView.SelectRows)
        right_panel.addWidget(self.tbl_detay, 1)

        right_frame = QFrame(); right_frame.setLayout(right_panel)
        content.addWidget(right_frame, 1)
        layout.addLayout(content, 1)

        # Alt butonlar
        btn_bar = QHBoxLayout(); btn_bar.setSpacing(12)
        btn_kaydet = QPushButton("💾 Kaydet"); btn_kaydet.setCursor(Qt.PointingHandCursor)
        btn_kaydet.setStyleSheet(f"QPushButton {{ background: {s['info']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_sil_grup = QPushButton("🗑 Seçili Grubu Kaldır"); btn_sil_grup.setCursor(Qt.PointingHandCursor)
        btn_sil_grup.setStyleSheet(f"QPushButton {{ background: {s['danger']}; color: white; border: none; border-radius: 8px; padding: 12px 20px; font-weight: 600; }}")
        btn_sil_grup.clicked.connect(self._grup_kaldir)
        btn_tamamla = QPushButton("✅ Sayımı Tamamla"); btn_tamamla.setCursor(Qt.PointingHandCursor)
        btn_tamamla.setStyleSheet(f"QPushButton {{ background: {s['success']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}")
        btn_tamamla.clicked.connect(self._tamamla)
        btn_kapat = QPushButton("Kapat"); btn_kapat.setCursor(Qt.PointingHandCursor)
        btn_kapat.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }}")
        btn_kapat.clicked.connect(self.accept)
        btn_bar.addWidget(btn_sil_grup); btn_bar.addStretch()
        btn_bar.addWidget(btn_kaydet); btn_bar.addWidget(btn_tamamla); btn_bar.addWidget(btn_kapat)
        layout.addLayout(btn_bar)

    def _load_header(self):
        """Sayim bilgilerini yukle"""
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""SELECT s.sayim_no, s.sayim_tipi, s.durum, d.kod + ' - ' + d.ad, FORMAT(s.sayim_tarihi, 'dd.MM.yyyy')
                FROM stok.sayimlar s LEFT JOIN tanim.depolar d ON s.depo_id = d.id WHERE s.id = ?""", (self.sayim_id,))
            row = cursor.fetchone(); conn.close()
            if row:
                self.lbl_title.setText(f"Sayım: {row[0]}")
                self.lbl_info.setText(f"Tip: {row[1]}  |  Depo: {row[3] or '-'}  |  Tarih: {row[4]}")
                durum = row[2]
                if durum == 'TASLAK':
                    self.lbl_durum.setText("TASLAK"); self.lbl_durum.setStyleSheet(f"padding: 6px 16px; border-radius: 6px; font-weight: 600; background: {s['warning']}; color: #000;")
                elif durum == 'DEVAM_EDIYOR':
                    self.lbl_durum.setText("DEVAM EDİYOR"); self.lbl_durum.setStyleSheet(f"padding: 6px 16px; border-radius: 6px; font-weight: 600; background: {s['info']}; color: white;")
                elif durum == 'TAMAMLANDI':
                    self.lbl_durum.setText("TAMAMLANDI"); self.lbl_durum.setStyleSheet(f"padding: 6px 16px; border-radius: 6px; font-weight: 600; background: {s['success']}; color: white;")
        except Exception as e:
            self.lbl_info.setText(f"Hata: {e}")

    def _load_grup_listesi(self):
        """Urun tiplerini yukle"""
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM stok.urun_tipleri WHERE aktif_mi = 1 ORDER BY sira_no, ad")
            rows = cursor.fetchall(); conn.close()
            for row in rows:
                item = QListWidgetItem(f"{row[1]} - {row[2]}")
                item.setData(Qt.UserRole, row[0])
                item.setData(Qt.UserRole + 1, row[2])
                self.lst_gruplar.addItem(item)
        except Exception:
            # urun_tipleri yoksa urun_tipi string'den unique degerler al
            try:
                conn = get_db_connection(); cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT urun_tipi FROM stok.urunler WHERE urun_tipi IS NOT NULL AND aktif_mi = 1 ORDER BY urun_tipi")
                rows = cursor.fetchall(); conn.close()
                for row in rows:
                    item = QListWidgetItem(row[0])
                    item.setData(Qt.UserRole, row[0])
                    item.setData(Qt.UserRole + 1, row[0])
                    self.lst_gruplar.addItem(item)
            except Exception:
                pass

    def _grup_ekle(self):
        """Secili grubu sayima ekle - o gruptaki urunleri detay tablosuna aktar"""
        sel = self.lst_gruplar.currentItem()
        if not sel:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir ürün grubu seçin!"); return

        grup_id = sel.data(Qt.UserRole)
        grup_adi = sel.data(Qt.UserRole + 1)

        try:
            conn = get_db_connection(); cursor = conn.cursor()

            # Sayimin depo_id'sini al (sistem stok icin)
            cursor.execute("SELECT depo_id FROM stok.sayimlar WHERE id = ?", (self.sayim_id,))
            depo_id = cursor.fetchone()[0]

            # Grup id int mi (urun_tipleri) yoksa string mi (urun_tipi) kontrol et
            if isinstance(grup_id, int):
                cursor.execute("""
                    SELECT u.id, u.urun_kodu, u.urun_adi, ut.ad, b.ad,
                           ISNULL((SELECT SUM(sb.miktar) FROM stok.stok_bakiye sb WHERE sb.urun_id = u.id AND sb.depo_id = ?), 0) as sistem_stok
                    FROM stok.urunler u
                    LEFT JOIN stok.urun_tipleri ut ON u.urun_tipi_id = ut.id
                    LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                    WHERE u.urun_tipi_id = ? AND ISNULL(u.aktif_mi, 1) = 1 AND ISNULL(u.silindi_mi, 0) = 0
                    ORDER BY u.urun_kodu
                """, (depo_id, grup_id))
            else:
                cursor.execute("""
                    SELECT u.id, u.urun_kodu, u.urun_adi, u.urun_tipi, b.ad,
                           ISNULL((SELECT SUM(sb.miktar) FROM stok.stok_bakiye sb WHERE sb.urun_id = u.id AND sb.depo_id = ?), 0) as sistem_stok
                    FROM stok.urunler u
                    LEFT JOIN tanim.birimler b ON u.birim_id = b.id
                    WHERE u.urun_tipi = ? AND ISNULL(u.aktif_mi, 1) = 1 AND ISNULL(u.silindi_mi, 0) = 0
                    ORDER BY u.urun_kodu
                """, (depo_id, grup_id))

            urunler = cursor.fetchall()
            if not urunler:
                QMessageBox.information(self, "Bilgi", f"'{grup_adi}' grubunda ürün bulunamadı.")
                conn.close(); return

            # Zaten eklenmis urunleri kontrol et
            cursor.execute("SELECT urun_id FROM stok.sayim_detaylari WHERE sayim_id = ?", (self.sayim_id,))
            mevcut = {row[0] for row in cursor.fetchall()}

            eklenen = 0
            for urun in urunler:
                urun_id = urun[0]
                if urun_id in mevcut:
                    continue
                sistem_stok = float(urun[5] or 0)
                cursor.execute("""
                    INSERT INTO stok.sayim_detaylari (sayim_id, urun_id, urun_kodu, urun_adi, urun_tipi, birim, sistem_miktari, durum)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'BEKLIYOR')
                """, (self.sayim_id, urun_id, urun[1], urun[2], urun[3], urun[4], sistem_stok))
                eklenen += 1

            # Durumu DEVAM_EDIYOR yap
            if eklenen > 0:
                cursor.execute("UPDATE stok.sayimlar SET durum = 'DEVAM_EDIYOR' WHERE id = ? AND durum = 'TASLAK'", (self.sayim_id,))

            conn.commit(); conn.close()
            self._load_detaylar()
            self._load_header()
            QMessageBox.information(self, "Bilgi", f"'{grup_adi}' grubundan {eklenen} ürün eklendi." + (f" ({len(urunler) - eklenen} zaten mevcut)" if len(urunler) - eklenen > 0 else ""))
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _grup_kaldir(self):
        """Secili gruptaki urunleri sayimdan kaldir"""
        sel = self.lst_gruplar.currentItem()
        if not sel:
            QMessageBox.warning(self, "Uyarı", "Lütfen kaldırılacak grubu seçin!"); return
        grup_adi = sel.data(Qt.UserRole + 1)
        cevap = QMessageBox.question(self, "Onay", f"'{grup_adi}' grubundaki tüm ürünler sayımdan kaldırılsın mı?", QMessageBox.Yes | QMessageBox.No)
        if cevap != QMessageBox.Yes: return
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("DELETE FROM stok.sayim_detaylari WHERE sayim_id = ? AND urun_tipi = ?", (self.sayim_id, grup_adi))
            conn.commit(); conn.close()
            self._load_detaylar()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _load_detaylar(self):
        """Sayim detaylarini tabloya yukle"""
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""
                SELECT id, urun_kodu, urun_adi, urun_tipi, birim, sistem_miktari, sayilan_miktar, fark, durum
                FROM stok.sayim_detaylari WHERE sayim_id = ? ORDER BY urun_tipi, urun_kodu
            """, (self.sayim_id,))
            self.detay_rows = cursor.fetchall(); conn.close()
            self._display_detaylar(self.detay_rows)
        except Exception as e:
            self.detay_rows = []
            self.lbl_satir.setText(f"Hata: {e}")

    def _display_detaylar(self, rows):
        s = self.s
        self.tbl_detay.setRowCount(len(rows))
        bekliyor = sayildi = 0
        for i, row in enumerate(rows):
            # row: id, urun_kodu, urun_adi, urun_tipi, birim, sistem_miktari, sayilan_miktar, fark, durum
            detay_id = row[0]

            # Stok Kodu
            self.tbl_detay.setItem(i, 0, QTableWidgetItem(str(row[1] or "")))
            # Urun Adi
            self.tbl_detay.setItem(i, 1, QTableWidgetItem(str(row[2] or "")))
            # Grup
            self.tbl_detay.setItem(i, 2, QTableWidgetItem(str(row[3] or "")))
            # Birim
            self.tbl_detay.setItem(i, 3, QTableWidgetItem(str(row[4] or "")))
            # Sistem Stok
            sistem = float(row[5] or 0)
            item_sistem = QTableWidgetItem(f"{sistem:,.2f}")
            item_sistem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_detay.setItem(i, 4, item_sistem)

            # Sayilan - editable spinbox
            spin = QDoubleSpinBox()
            spin.setRange(0, 9999999); spin.setDecimals(2)
            spin.setStyleSheet(f"background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 4px; padding: 4px; color: {s['text']};")
            spin.setProperty("detay_id", detay_id)
            spin.setProperty("sistem", sistem)
            if row[6] is not None:
                spin.setValue(float(row[6]))
            spin.valueChanged.connect(lambda val, r=i, sp=spin: self._miktar_degisti(r, sp))
            self.tbl_detay.setCellWidget(i, 5, spin)

            # Fark
            fark_val = float(row[7]) if row[7] is not None else None
            item_fark = QTableWidgetItem(f"{fark_val:,.2f}" if fark_val is not None else "-")
            item_fark.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if fark_val is not None and fark_val != 0:
                item_fark.setForeground(QColor(s['error']) if fark_val < 0 else QColor(s['warning']))
            self.tbl_detay.setItem(i, 6, item_fark)

            # Durum
            durum = row[8]
            item_durum = QTableWidgetItem(durum or "")
            if durum == 'BEKLIYOR': item_durum.setForeground(QColor(s['text_muted'])); bekliyor += 1
            elif durum == 'SAYILDI': item_durum.setForeground(QColor(s['success'])); sayildi += 1
            self.tbl_detay.setItem(i, 7, item_durum)

            self.tbl_detay.setRowHeight(i, 42)

        self.lbl_satir.setText(f"{len(rows)} kalem | Bekliyor: {bekliyor} | Sayıldı: {sayildi}")

    def _miktar_degisti(self, row, spin):
        """Sayilan miktar degistiginde fark hesapla"""
        s = self.s
        sistem = spin.property("sistem") or 0
        sayilan = spin.value()
        fark = sayilan - sistem
        item_fark = QTableWidgetItem(f"{fark:,.2f}")
        item_fark.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if fark != 0:
            item_fark.setForeground(QColor(s['error']) if fark < 0 else QColor(s['warning']))
        self.tbl_detay.setItem(row, 6, item_fark)
        # Durum guncelle
        self.tbl_detay.setItem(row, 7, QTableWidgetItem("SAYILDI"))

    def _filtrele(self, text):
        """Tabloda ara"""
        text = text.lower()
        for i in range(self.tbl_detay.rowCount()):
            kod = (self.tbl_detay.item(i, 0).text() if self.tbl_detay.item(i, 0) else "").lower()
            ad = (self.tbl_detay.item(i, 1).text() if self.tbl_detay.item(i, 1) else "").lower()
            self.tbl_detay.setRowHidden(i, text not in kod and text not in ad)

    def _kaydet(self):
        """Sayilan miktarlari kaydet"""
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            for i in range(self.tbl_detay.rowCount()):
                spin = self.tbl_detay.cellWidget(i, 5)
                if spin is None: continue
                detay_id = spin.property("detay_id")
                sayilan = spin.value()
                sistem = spin.property("sistem") or 0
                fark = sayilan - sistem
                # Eger spin'e dokunulduysa (deger 0 degilse veya fark varsa) kaydet
                cursor.execute("""
                    UPDATE stok.sayim_detaylari SET sayilan_miktar = ?, fark = ?, durum = 'SAYILDI'
                    WHERE id = ?
                """, (sayilan, fark, detay_id))
            conn.commit(); conn.close()
            self._load_detaylar()
            QMessageBox.information(self, "Bilgi", "Sayım verileri kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _tamamla(self):
        """Sayimi tamamla ve fark olan kalemleri stok hareketine yansit"""
        cevap = QMessageBox.question(self, "Onay",
            "Sayım tamamlansın mı?\n\nFark olan kalemler için stok hareketi oluşturulacak.\nTamamlanan sayımda değişiklik yapılamaz.",
            QMessageBox.Yes | QMessageBox.No)
        if cevap != QMessageBox.Yes: return
        try:
            self._kaydet_silent()
            conn = get_db_connection(); cursor = conn.cursor()

            # Sayim bilgilerini al (depo_id, sayim_no)
            cursor.execute("SELECT depo_id, sayim_no FROM stok.sayimlar WHERE id = ?", (self.sayim_id,))
            sayim_row = cursor.fetchone()
            depo_id = sayim_row[0]; sayim_no = sayim_row[1]

            # Fark olan kalemleri al
            cursor.execute("""
                SELECT id, urun_id, urun_kodu, urun_adi, sayilan_miktar, fark
                FROM stok.sayim_detaylari
                WHERE sayim_id = ? AND fark IS NOT NULL AND fark <> 0
            """, (self.sayim_id,))
            fark_rows = cursor.fetchall()

            # Stok bakiyelerini guncelle (lot uretmez, urun+depo bazli duzeltir)
            fazla = eksik = 0
            if fark_rows:
                for row in fark_rows:
                    detay_id, urun_id, urun_kodu, urun_adi, sayilan, fark = row

                    if fark > 0:
                        hareket_tipi = 'SAYIM_FAZLA'
                        fazla += 1
                    else:
                        hareket_tipi = 'SAYIM_EKSIK'
                        eksik += 1

                    # Urun+depo bazli mevcut bakiye var mi?
                    cursor.execute("""
                        SELECT TOP 1 id, lot_no, miktar FROM stok.stok_bakiye
                        WHERE urun_id = ? AND depo_id = ?
                        ORDER BY giris_tarihi ASC
                    """, (urun_id, depo_id))
                    bakiye = cursor.fetchone()

                    if bakiye:
                        # Mevcut bakiyeyi guncelle
                        yeni_miktar = bakiye[2] + fark  # fark pozitif veya negatif
                        if yeni_miktar < 0: yeni_miktar = 0
                        cursor.execute("""UPDATE stok.stok_bakiye SET miktar = ?,
                            son_hareket_tarihi = GETDATE() WHERE id = ?""", (yeni_miktar, bakiye[0]))
                        ref_lot = bakiye[1]
                    else:
                        # Bakiye yoksa ve fazla varsa yeni kayit olustur
                        if fark > 0:
                            ref_lot = f"SAYIM-{sayim_no}-{urun_kodu}"
                            cursor.execute("""
                                INSERT INTO stok.stok_bakiye
                                (urun_id, depo_id, lot_no, miktar, rezerve_miktar,
                                 bloke_mi, kalite_durumu, durum_kodu,
                                 giris_tarihi, son_hareket_tarihi)
                                VALUES (?, ?, ?, ?, 0, 0, 'ONAY', 'SAYIM', GETDATE(), GETDATE())
                            """, (urun_id, depo_id, ref_lot, fark))
                        else:
                            ref_lot = 'YOK'

                    # Hareket kaydı
                    cursor.execute("""
                        INSERT INTO stok.stok_hareketleri
                        (uuid, hareket_tipi, hareket_nedeni, tarih, urun_id, depo_id,
                         miktar, birim_id, lot_no, referans_tip, referans_id, aciklama, olusturma_tarihi)
                        VALUES (NEWID(), ?, 'SAYIM', GETDATE(), ?, ?, ?, 1, ?, 'SAYIM', ?, ?, GETDATE())
                    """, (hareket_tipi, urun_id, depo_id, abs(fark), ref_lot, self.sayim_id,
                          f"Sayım {'fazlası' if fark > 0 else 'eksiği'} - {sayim_no}"))

            # Durumu TAMAMLANDI yap
            cursor.execute("UPDATE stok.sayimlar SET durum = 'TAMAMLANDI' WHERE id = ?", (self.sayim_id,))
            conn.commit(); conn.close()
            self._load_header()

            msg = "Sayım tamamlandı."
            if fark_rows:
                msg += f"\n\nStok hareketleri oluşturuldu:\n  Fazla: {fazla} kalem\n  Eksik: {eksik} kalem"
            QMessageBox.information(self, "Bilgi", msg)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _kaydet_silent(self):
        """Sessiz kaydet (mesaj gostermeden)"""
        conn = get_db_connection(); cursor = conn.cursor()
        for i in range(self.tbl_detay.rowCount()):
            spin = self.tbl_detay.cellWidget(i, 5)
            if spin is None: continue
            detay_id = spin.property("detay_id")
            sayilan = spin.value()
            sistem = spin.property("sistem") or 0
            fark = sayilan - sistem
            cursor.execute("UPDATE stok.sayim_detaylari SET sayilan_miktar = ?, fark = ?, durum = 'SAYILDI' WHERE id = ?", (sayilan, fark, detay_id))
        conn.commit(); conn.close()


class DepoSayimPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        _ensure_sayim_tables()
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        
        header = QHBoxLayout(); title_section = QVBoxLayout(); title_section.setSpacing(4)
        title_row = QHBoxLayout(); icon = QLabel("📋"); icon.setStyleSheet("font-size: 28px;"); title_row.addWidget(icon)
        title = QLabel("Stok Sayım"); title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;"); title_row.addWidget(title); title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Depo sayım işlemleri ve fark raporları"); subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;"); title_section.addWidget(subtitle)
        header.addLayout(title_section); header.addStretch()
        self.stat_label = QLabel(""); self.stat_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px; padding: 8px 16px; background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px;"); header.addWidget(self.stat_label)
        layout.addLayout(header)
        
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        btn_yeni = QPushButton("➕ Yeni Sayım"); btn_yeni.setCursor(Qt.PointingHandCursor); btn_yeni.setStyleSheet(f"QPushButton {{ background: {s['primary']}; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; }}"); btn_yeni.clicked.connect(self._yeni); toolbar.addWidget(btn_yeni)
        toolbar.addStretch()
        self.cmb_durum = QComboBox(); self.cmb_durum.addItems(["Tümü", "TASLAK", "DEVAM_EDIYOR", "TAMAMLANDI"]); self.cmb_durum.setStyleSheet(f"QComboBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; min-width: 140px; }}"); self.cmb_durum.currentIndexChanged.connect(self._filter); toolbar.addWidget(self.cmb_durum)
        btn_yenile = QPushButton("🔄"); btn_yenile.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}"); btn_yenile.clicked.connect(self._load_data); toolbar.addWidget(btn_yenile)
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setStyleSheet(f"QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; color: {s['text']}; }} QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }} QTableWidget::item:selected {{ background: {s['primary']}; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 12px; text-transform: uppercase; }}")
        self.table.setColumnCount(7); self.table.setHorizontalHeaderLabels(["ID", "Sayım No", "Tip", "Depo", "Tarih", "Durum", "İşlem"]); self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 150); self.table.setColumnWidth(2, 120); self.table.setColumnWidth(4, 100); self.table.setColumnWidth(5, 120); self.table.setColumnWidth(6, 120)
        self.table.verticalHeader().setVisible(False); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""SELECT s.id, s.sayim_no, s.sayim_tipi, d.kod + ' - ' + d.ad, FORMAT(s.sayim_tarihi, 'dd.MM.yyyy'), s.durum
                FROM stok.sayimlar s LEFT JOIN tanim.depolar d ON s.depo_id = d.id ORDER BY s.sayim_tarihi DESC""")
            self.all_rows = cursor.fetchall(); conn.close()
            self._display_data(self.all_rows)
        except Exception as e: 
            self.all_rows = []
            self.stat_label.setText("📊 Tablo bulunamadı")
    
    def _display_data(self, rows):
        s = self.s
        self.table.setRowCount(len(rows)); taslak = devam = 0
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "")
                if j == 5:
                    if val == 'TASLAK': item.setForeground(QColor(s['warning'])); taslak += 1
                    elif val == 'DEVAM_EDIYOR': item.setForeground(QColor(s['info'])); devam += 1
                    elif val == 'TAMAMLANDI': item.setForeground(QColor(s['success']))
                self.table.setItem(i, j, item)
            widget = self.create_action_buttons([
                ("📋", "Detay", lambda checked, rid=row[0]: self._detay(rid), "view"),
            ])
            self.table.setCellWidget(i, 6, widget); self.table.setRowHeight(i, 48)
        self.stat_label.setText(f"📊 Toplam: {len(rows)} | Taslak: {taslak} | Devam: {devam}")
    
    def _filter(self):
        durum = self.cmb_durum.currentText()
        if durum == "Tümü": self._display_data(self.all_rows)
        else: self._display_data([r for r in self.all_rows if r[5] == durum])
    
    def _yeni(self):
        dialog = SayimOlusturDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted: self._load_data()
    
    def _detay(self, sayim_id):
        dialog = SayimDetayDialog(sayim_id, self.theme, self)
        dialog.exec()
        self._load_data()
