# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Kimyasal Takviye Kayıtları
Modernize edilmiş versiyon - NexorComponents kullanılarak

Değişiklikler:
- dbo.StokKartlari → stok.urunler (kimyasal tipi ürünler)
- dbo.Personel → ik.personeller
- NexorComponents entegrasyonu
- Modern UI/UX
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

# Modern component'ları import et
try:
    from components.nexor_components import (
        NexorCard, NexorButton, NexorTable, NexorPageHeader,
        NexorSelect, NexorModal, NexorBadge, NexorInput,
        get_theme_colors, Spacing, BorderRadius, FontSize
    )
    NEXOR_COMPONENTS = True
except ImportError:
    NEXOR_COMPONENTS = False
    print("[WARNING] NexorComponents yüklenemedi, fallback modda çalışılıyor")


def _get_theme(theme):
    """Tema renklerini al"""
    if NEXOR_COMPONENTS:
        return get_theme_colors(theme)
    return theme


class TakviyeDialog(QDialog):
    """Kimyasal Takviye Ekleme/Düzenleme - Modern Dialog"""
    
    def __init__(self, theme: dict, takviye_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = _get_theme(theme)
        self.takviye_id = takviye_id
        self.data = {}
        
        self.setWindowTitle("Yeni Takviye" if not takviye_id else "Takviye Düzenle")
        self.setMinimumSize(550, 580)
        self.setModal(True)
        
        if takviye_id:
            self._load_data()
        self._setup_ui()
    
    def _load_data(self):
        """Mevcut takviye verisini yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM uretim.banyo_takviyeler WHERE id = ?", (self.takviye_id,))
            row = cursor.fetchone()
            if row:
                self.data = dict(zip([d[0] for d in cursor.description], row))
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
    
    def _setup_ui(self):
        """UI oluştur"""
        t = self.theme
        br = BorderRadius.LG if NEXOR_COMPONENTS else 12
        
        self.setStyleSheet(f"""
            QDialog {{
                background: {t.get('bg_card', '#1A1A1A')};
                border: 1px solid {t.get('border', '#2A2A2A')};
                border-radius: {br}px;
            }}
            QLabel {{
                color: {t.get('text', '#FFFFFF')};
                background: transparent;
            }}
            QComboBox, QDoubleSpinBox, QDateTimeEdit {{
                background: {t.get('bg_input', '#1A1A1A')};
                border: 1px solid {t.get('border', '#2A2A2A')};
                border-radius: 6px;
                padding: 10px 12px;
                color: {t.get('text', '#FFFFFF')};
                font-size: 13px;
                min-height: 20px;
            }}
            QComboBox:hover, QDoubleSpinBox:hover, QDateTimeEdit:hover {{
                border-color: {t.get('border_light', '#333333')};
            }}
            QComboBox:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus {{
                border-color: {t.get('primary', '#DC2626')};
            }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {t.get('bg_card', '#1A1A1A')};
                border: 1px solid {t.get('border', '#2A2A2A')};
                color: {t.get('text', '#FFFFFF')};
                selection-background-color: {t.get('primary', '#DC2626')};
            }}
            QTextEdit {{
                background: {t.get('bg_input', '#1A1A1A')};
                border: 1px solid {t.get('border', '#2A2A2A')};
                border-radius: 6px;
                padding: 10px;
                color: {t.get('text', '#FFFFFF')};
                font-size: 13px;
            }}
            QTextEdit:focus {{ border-color: {t.get('primary', '#DC2626')}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Başlık
        header = QHBoxLayout()
        icon_label = QLabel("💧")
        icon_label.setStyleSheet("font-size: 28px;")
        header.addWidget(icon_label)
        
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {t.get('text', '#FFFFFF')};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Ayırıcı
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {t.get('border', '#2A2A2A')}; max-height: 1px;")
        layout.addWidget(sep)
        
        # Form
        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignRight)
        label_style = f"color: {t.get('text_secondary', '#AAAAAA')}; font-size: 13px; font-weight: 500;"
        
        # Banyo
        lbl = QLabel("Banyo *")
        lbl.setStyleSheet(label_style)
        self.banyo_combo = QComboBox()
        self.banyo_combo.addItem("-- Banyo Seçin --", None)
        self._load_banyolar()
        form.addRow(lbl, self.banyo_combo)
        
        # Kimyasal
        lbl = QLabel("Kimyasal *")
        lbl.setStyleSheet(label_style)
        self.kimyasal_combo = QComboBox()
        self.kimyasal_combo.addItem("-- Kimyasal Seçin --", None)
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
        self.birim_combo.addItem("-- Birim Seçin --", None)
        self._load_birimler()
        form.addRow(lbl, self.birim_combo)
        
        # Neden
        lbl = QLabel("Takviye Nedeni")
        lbl.setStyleSheet(label_style)
        self.neden_combo = QComboBox()
        self.neden_combo.addItem("-- Seçiniz --", None)
        self.neden_combo.addItem("📅 Periyodik Takviye", "PERIYODIK")
        self.neden_combo.addItem("🔬 Analiz Sonucu", "ANALIZ")
        self.neden_combo.addItem("🆕 İlk Dolum", "ILK_DOLUM")
        self.neden_combo.addItem("🔧 Düzeltme", "DUZELTME")
        self.neden_combo.addItem("📝 Diğer", "DIGER")
        if self.data.get('takviye_nedeni'):
            idx = self.neden_combo.findData(self.data['takviye_nedeni'])
            if idx >= 0:
                self.neden_combo.setCurrentIndex(idx)
        form.addRow(lbl, self.neden_combo)
        
        # Yapan
        lbl = QLabel("Yapan Personel *")
        lbl.setStyleSheet(label_style)
        self.yapan_combo = QComboBox()
        self.yapan_combo.addItem("-- Personel Seçin --", None)
        self._load_personel()
        form.addRow(lbl, self.yapan_combo)
        
        # Notlar
        lbl = QLabel("Notlar")
        lbl.setStyleSheet(label_style)
        self.notlar_input = QTextEdit()
        self.notlar_input.setMaximumHeight(80)
        self.notlar_input.setPlaceholderText("Ek notlar...")
        self.notlar_input.setText(self.data.get('notlar', '') or '')
        form.addRow(lbl, self.notlar_input)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.get('bg_input', '#1A1A1A')};
                color: {t.get('text', '#FFFFFF')};
                border: 1px solid {t.get('border', '#2A2A2A')};
                border-radius: 6px; padding: 12px 24px; font-size: 13px; font-weight: 500;
            }}
            QPushButton:hover {{ background: {t.get('bg_hover', '#252525')}; border-color: {t.get('primary', '#DC2626')}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾  Kaydet")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.get('primary', '#DC2626')};
                color: white; border: none; border-radius: 6px;
                padding: 12px 28px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {t.get('primary_hover', '#B91C1C')}; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_banyolar(self):
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
            conn.close()
            if self.data.get('banyo_id'):
                idx = self.banyo_combo.findData(self.data['banyo_id'])
                if idx >= 0: self.banyo_combo.setCurrentIndex(idx)
        except Exception: pass
    
    def _load_kimyasallar(self):
        """Kimyasal tipindeki urunler - stokta olanlar onde"""
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
            conn.close()
            if self.data.get('kimyasal_id'):
                idx = self.kimyasal_combo.findData(self.data['kimyasal_id'])
                if idx >= 0: self.kimyasal_combo.setCurrentIndex(idx)
        except Exception: pass
    
    def _load_birimler(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.birimler WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.birim_combo.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
            if self.data.get('birim_id'):
                idx = self.birim_combo.findData(self.data['birim_id'])
                if idx >= 0: self.birim_combo.setCurrentIndex(idx)
        except Exception: pass
    
    def _load_personel(self):
        """YENİ: ik.personeller tablosu"""
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
            conn.close()
            if self.data.get('yapan_id'):
                idx = self.yapan_combo.findData(self.data['yapan_id'])
                if idx >= 0: self.yapan_combo.setCurrentIndex(idx)
        except Exception: pass
    
    def _save(self):
        banyo_id = self.banyo_combo.currentData()
        kimyasal_id = self.kimyasal_combo.currentData()
        miktar = self.miktar_input.value()
        birim_id = self.birim_combo.currentData()
        yapan_id = self.yapan_combo.currentData()
        
        if not banyo_id or not kimyasal_id or not miktar or not birim_id or not yapan_id:
            QMessageBox.warning(self, "⚠️ Eksik Bilgi", 
                "Zorunlu alanlar:\n• Banyo\n• Kimyasal\n• Miktar\n• Birim\n• Yapan Personel")
            return
        
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
            if not self.takviye_id:  # sadece yeni takviyede
                # Birim adini al
                cursor.execute("SELECT kod FROM tanim.birimler WHERE id = ?", (birim_id,))
                birim_row = cursor.fetchone()
                birim_kod = birim_row[0] if birim_row else 'KG'

                # FIFO lot bul
                cursor.execute("""
                    SELECT TOP 1 id, lot_no, miktar FROM stok.stok_bakiye
                    WHERE urun_id = ? AND ISNULL(bloke_mi, 0) = 0
                      AND ISNULL(ISNULL(kullanilabilir_miktar, miktar), 0) > 0
                    ORDER BY giris_tarihi ASC
                """, (kimyasal_id,))
                bakiye = cursor.fetchone()

                stok_msg = ""
                if bakiye:
                    bakiye_id, lot_no = bakiye[0], bakiye[1]
                    # Stok hareketi olustur
                    cursor.execute("""
                        INSERT INTO stok.stok_hareketleri
                        (uuid, hareket_tipi, hareket_nedeni, tarih, urun_id, depo_id,
                         miktar, birim_id, lot_no, referans_tip, aciklama, olusturma_tarihi)
                        VALUES (NEWID(), 'CIKIS', 'KIMYASAL_TUKETIM', GETDATE(), ?,
                                (SELECT depo_id FROM stok.stok_bakiye WHERE id = ?),
                                ?, ?, ?, 'BANYO_TAKVIYE', ?, GETDATE())
                    """, (kimyasal_id, bakiye_id, miktar, birim_id, lot_no,
                          f"Banyo takviye - {self.banyo_combo.currentText()[:50]}"))

                    # Bakiye guncelle
                    cursor.execute("""
                        UPDATE stok.stok_bakiye SET miktar = miktar - ?,
                            son_hareket_tarihi = GETDATE()
                        WHERE id = ?
                    """, (miktar, bakiye_id))
                    stok_msg = f"\nStoktan düşüldü (Lot: {lot_no})"
                else:
                    stok_msg = "\nStok kaydı bulunamadı - sadece takviye kaydedildi"

            conn.commit()
            LogManager.log_insert('lab', 'uretim.banyo_takviyeler', None, 'Kimyasal takviye kaydedildi')
            conn.close()
            QMessageBox.information(self, "Başarılı", f"Takviye kaydedildi!{stok_msg if not self.takviye_id else ''}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", str(e))


class LabKimyasalPage(BasePage):
    """Kimyasal Takviye Kayıtları Listesi - Modern"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.t = _get_theme(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        t = self.t
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title_sec = QVBoxLayout()
        title_sec.setSpacing(4)
        
        title_row = QHBoxLayout()
        icon = QLabel("💧")
        icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(icon)
        title = QLabel("Kimyasal Takviyeler")
        title.setStyleSheet(f"color: {t.get('text', '#FFF')}; font-size: 24px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_sec.addLayout(title_row)
        
        sub = QLabel("Banyo kimyasal takviye kayıtlarını yönetin")
        sub.setStyleSheet(f"color: {t.get('text_secondary', '#AAA')}; font-size: 13px;")
        title_sec.addWidget(sub)
        header.addLayout(title_sec)
        header.addStretch()
        
        self.stat_label = QLabel("")
        self.stat_label.setStyleSheet(f"""
            color: {t.get('text_muted', '#666')}; font-size: 13px;
            padding: 8px 16px; background: {t.get('bg_card', '#1A1A1A')}; border-radius: 6px;
        """)
        header.addWidget(self.stat_label)
        layout.addLayout(header)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        fl = QLabel("Filtre:")
        fl.setStyleSheet(f"color: {t.get('text_secondary', '#AAA')}; font-size: 13px;")
        toolbar.addWidget(fl)
        
        self.banyo_combo = QComboBox()
        self.banyo_combo.addItem("🏭 Tüm Banyolar", None)
        self._load_banyo_filter()
        self.banyo_combo.setStyleSheet(f"""
            QComboBox {{
                background: {t.get('bg_input', '#1A1A1A')}; border: 1px solid {t.get('border', '#2A2A2A')};
                border-radius: 6px; padding: 8px 12px; color: {t.get('text', '#FFF')};
                min-width: 220px; font-size: 13px;
            }}
            QComboBox:hover {{ border-color: {t.get('border_light', '#333')}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background: {t.get('bg_card', '#1A1A1A')}; border: 1px solid {t.get('border', '#2A2A2A')};
                color: {t.get('text', '#FFF')}; selection-background-color: {t.get('primary', '#DC2626')};
            }}
        """)
        self.banyo_combo.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(self.banyo_combo)
        toolbar.addStretch()
        
        ref_btn = QPushButton("🔄")
        ref_btn.setToolTip("Yenile")
        ref_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.get('bg_input', '#1A1A1A')}; color: {t.get('text', '#FFF')};
                border: 1px solid {t.get('border', '#2A2A2A')}; border-radius: 6px;
                padding: 8px 12px; font-size: 14px;
            }}
            QPushButton:hover {{ background: {t.get('bg_hover', '#252525')}; border-color: {t.get('primary', '#DC2626')}; }}
        """)
        ref_btn.clicked.connect(self._load_data)
        toolbar.addWidget(ref_btn)
        
        add_btn = QPushButton("➕  Yeni Takviye")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.get('primary', '#DC2626')}; color: white;
                border: none; border-radius: 6px; padding: 10px 20px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {t.get('primary_hover', '#B91C1C')}; }}
        """)
        add_btn.clicked.connect(self._add_new)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {t.get('bg_card', '#1A1A1A')}; border: 1px solid {t.get('border', '#2A2A2A')};
                border-radius: 8px; gridline-color: {t.get('border', '#2A2A2A')}; color: {t.get('text', '#FFF')};
            }}
            QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {t.get('border', '#2A2A2A')}; }}
            QTableWidget::item:selected {{ background: {t.get('primary', '#DC2626')}; }}
            QTableWidget::item:hover {{ background: {t.get('bg_hover', '#252525')}; }}
            QHeaderView::section {{
                background: {t.get('bg_main', '#0F0F0F')}; color: {t.get('text_secondary', '#AAA')};
                padding: 12px 8px; border: none; border-bottom: 2px solid {t.get('primary', '#DC2626')};
                font-weight: 600; font-size: 12px; text-transform: uppercase;
            }}
        """)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Banyo", "Kimyasal", "Tarih", "Miktar", "Neden", "Yapan", "İşlem"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 130)
        self.table.setColumnWidth(7, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_banyo_filter(self):
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
            conn.close()
        except Exception: pass
    
    def _load_data(self):
        t = self.t
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # YENİ SORGU: stok.urunler ve ik.personeller
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
            conn.close()
            
            neden_map = {
                "PERIYODIK": ("📅 Periyodik", t.get('info', '#3B82F6')),
                "ANALIZ": ("🔬 Analiz", t.get('warning', '#F59E0B')),
                "ILK_DOLUM": ("🆕 İlk Dolum", t.get('success', '#10B981')),
                "DUZELTME": ("🔧 Düzeltme", t.get('error', '#EF4444')),
                "DIGER": ("📝 Diğer", t.get('text_muted', '#666'))
            }
            
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # ID
                item = QTableWidgetItem(str(row[0]))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor(t.get('text_muted', '#666')))
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
                
                neden_info = neden_map.get(row[5], ("❓ -", t.get('text_muted', '#666')))
                item = QTableWidgetItem(neden_info[0])
                item.setForeground(QColor(neden_info[1]))
                self.table.setItem(i, 5, item)
                
                self.table.setItem(i, 6, QTableWidgetItem(row[6] or '-'))
                
                # Butonlar
                widget = self.create_action_buttons([
                    ("✏️", "Duzenle", lambda checked, rid=row[0]: self._edit_item(rid), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=row[0]: self._delete_item(rid), "delete"),
                ])
                self.table.setCellWidget(i, 7, widget)
                self.table.setRowHeight(i, 44)
            
            self.stat_label.setText(f"📊 Toplam: {len(rows)} kayıt")
        except Exception as e:
            QMessageBox.warning(self, "⚠️ Hata", str(e))
    
    def _add_new(self):
        dlg = TakviyeDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _edit_item(self, tid):
        dlg = TakviyeDialog(self.theme, tid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()
    
    def _delete_item(self, tid):
        if QMessageBox.question(self, "🗑️ Sil?", "Bu kaydı silmek istediğinize emin misiniz?",
                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM uretim.banyo_takviyeler WHERE id=?", (tid,))
                conn.commit()
                LogManager.log_delete('lab', 'uretim.banyo_takviyeler', None, 'Kayit silindi')
                conn.close()
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "❌ Hata", str(e))
