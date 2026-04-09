# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Teklif Liste Sayfası
Kaplama sektörü teklif yönetimi
"""
import os
import sys
from datetime import datetime, date

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QDateEdit, QMessageBox,
    QMenu, QDialog
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QAction

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from config import DEFAULT_PAGE_SIZE


DURUM_RENKLER = {
    'TASLAK': '#6B7280',
    'GONDERILDI': '#3B82F6',
    'ONAYLANDI': '#10B981',
    'REDDEDILDI': '#EF4444',
    'IPTAL': '#9CA3AF',
    'IS_EMRINE_DONUSTURULDU': '#8B5CF6',
}

DURUM_METINLER = {
    'TASLAK': 'Taslak',
    'GONDERILDI': 'Gönderildi',
    'ONAYLANDI': 'Onaylandı',
    'REDDEDILDI': 'Reddedildi',
    'IPTAL': 'İptal',
    'IS_EMRINE_DONUSTURULDU': 'İş Emrine Dönüştürüldü',
}


class TeklifListePage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.page_size = DEFAULT_PAGE_SIZE
        self.current_page = 1
        self.total_pages = 1
        self.total_items = 0
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        layout.addWidget(self._create_header())
        layout.addLayout(self._create_stat_cards())
        layout.addWidget(self._create_toolbar())
        self.table = self._create_table()
        layout.addWidget(self.table)
        layout.addWidget(self._create_bottom_bar())

    # ── HEADER ──
    def _create_header(self) -> QFrame:
        t = self.theme
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)

        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        title_row = QHBoxLayout()
        icon = QLabel("📝")
        icon.setStyleSheet("font-size: 24px;")
        title_row.addWidget(icon)
        title = QLabel("Teklifler")
        title.setStyleSheet(f"color: {t['text']}; font-size: 20px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Kaplama tekliflerini görüntüleyin ve yönetin")
        subtitle.setStyleSheet(f"color: {t['text_secondary']}; font-size: 12px;")
        title_section.addWidget(subtitle)
        layout.addLayout(title_section)
        layout.addStretch()

        sablon_btn = self.create_primary_button("📋 Şablondan Oluştur")
        sablon_btn.clicked.connect(self._yeni_teklif_sablondan)
        layout.addWidget(sablon_btn)

        new_btn = self.create_success_button("➕ Yeni Teklif")
        new_btn.clicked.connect(self._yeni_teklif)
        layout.addWidget(new_btn)
        return frame

    # ── İSTATİSTİK KARTLARI ──
    def _create_stat_cards(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)

        self.stat_toplam = self.create_stat_card("Toplam Teklif", "0", "📝", self.theme['primary'])
        self.stat_bekleyen = self.create_stat_card("Bekleyen", "0", "⏳", self.theme['warning'])
        self.stat_onaylanan = self.create_stat_card("Onaylanan", "0", "✅", self.theme['success'])
        self.stat_bu_ay = self.create_stat_card("Bu Ay Teklif", "0", "📅", self.theme['info'])

        row.addWidget(self.stat_toplam)
        row.addWidget(self.stat_bekleyen)
        row.addWidget(self.stat_onaylanan)
        row.addWidget(self.stat_bu_ay)
        return row

    def _update_stat_value(self, card: QFrame, value: str):
        for child in card.findChildren(QLabel):
            style = child.styleSheet()
            if 'font-size: 28px' in style:
                child.setText(value)
                break

    # ── FİLTRE ÇUBUĞU ──
    def _create_toolbar(self) -> QFrame:
        t = self.theme
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        lbl = QLabel("🔍 Arama:")
        lbl.setStyleSheet(f"font-weight: 600; font-size: 12px;")
        layout.addWidget(lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Teklif no, müşteri, proje...")
        self.search_input.setFixedWidth(200)
        self.search_input.returnPressed.connect(self._load_data)
        layout.addWidget(self.search_input)

        lbl2 = QLabel("📅 Tarih:")
        lbl2.setStyleSheet(f"font-weight: 600; font-size: 12px;")
        layout.addWidget(lbl2)

        self.tarih_bas = QDateEdit()
        self.tarih_bas.setDate(QDate.currentDate().addMonths(-3))
        self.tarih_bas.setCalendarPopup(True)
        self.tarih_bas.setFixedWidth(120)
        self.tarih_bas.dateChanged.connect(self._filter_changed)
        layout.addWidget(self.tarih_bas)

        layout.addWidget(QLabel("-"))

        self.tarih_bit = QDateEdit()
        self.tarih_bit.setDate(QDate.currentDate().addDays(30))
        self.tarih_bit.setCalendarPopup(True)
        self.tarih_bit.setFixedWidth(120)
        self.tarih_bit.dateChanged.connect(self._filter_changed)
        layout.addWidget(self.tarih_bit)

        lbl3 = QLabel("Durum:")
        lbl3.setStyleSheet(f"font-weight: 600; font-size: 12px;")
        layout.addWidget(lbl3)

        self.durum_combo = QComboBox()
        self.durum_combo.addItem("Tümü", "")
        for key, val in DURUM_METINLER.items():
            self.durum_combo.addItem(val, key)
        self.durum_combo.currentIndexChanged.connect(self._filter_changed)
        layout.addWidget(self.durum_combo)

        search_btn = self.create_primary_button("🔍 Ara")
        search_btn.clicked.connect(self._load_data)
        layout.addWidget(search_btn)

        layout.addStretch()
        return frame

    # ── TABLO ──
    def _create_table(self) -> QTableWidget:
        t = self.theme
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Teklif No", "Rev", "Tarih", "Müşteri", "Proje",
            "Durum", "Geçerlilik"
        ])

        header = table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        table.setColumnWidth(0, 130)
        table.setColumnWidth(1, 60)
        table.setColumnWidth(2, 90)
        table.setColumnWidth(5, 130)
        table.setColumnWidth(6, 100)

        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.doubleClicked.connect(self._open_detail)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self._show_context_menu)
        return table

    # ── ALT ÇUBUK ──
    def _create_bottom_bar(self) -> QFrame:
        t = self.theme
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)

        self.stat_label = QLabel("Yükleniyor...")
        self.stat_label.setStyleSheet(f"color: {t['text_secondary']}; font-size: 12px;")
        layout.addWidget(self.stat_label)
        layout.addStretch()

        self.prev_btn = QPushButton("◀ Önceki")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(self._prev_page)
        layout.addWidget(self.prev_btn)

        self.page_label = QLabel("1 / 1")
        self.page_label.setStyleSheet(f"color: {t['text']}; padding: 0 12px; font-weight: 600;")
        layout.addWidget(self.page_label)

        self.next_btn = QPushButton("Sonraki ▶")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self._next_page)
        layout.addWidget(self.next_btn)
        return frame

    # ── VERİ YÜKLEME ──
    def _load_data(self):
        self.stat_label.setText("Yükleniyor...")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Son revizyonları getir (ana_teklif_id NULL olanlar + her zincirin son revizyonu)
            sql = """
                SELECT t.id, t.teklif_no, t.revizyon_no, t.tarih, t.cari_unvani,
                       t.proje_adi, t.ara_toplam, t.kdv_tutar, t.genel_toplam,
                       t.durum, t.gecerlilik_tarihi, t.para_birimi
                FROM satislar.teklifler t
                WHERE t.silindi_mi = 0
                  AND t.revizyon_no = (
                      SELECT MAX(t2.revizyon_no) FROM satislar.teklifler t2
                      WHERE t2.teklif_no = t.teklif_no AND t2.silindi_mi = 0
                  )
                ORDER BY t.id DESC
            """
            cursor.execute(sql)
            items = []
            for row in cursor.fetchall():
                item = []
                for i in range(12):
                    try:
                        item.append(row[i])
                    except Exception:
                        item.append(None)
                items.append(item)

            # İstatistik sorguları
            cursor.execute("SELECT COUNT(*) FROM satislar.teklifler WHERE silindi_mi = 0")
            stat_toplam = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM satislar.teklifler WHERE silindi_mi = 0 AND durum IN ('TASLAK', 'GONDERILDI')")
            stat_bekleyen = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM satislar.teklifler WHERE silindi_mi = 0 AND durum = 'ONAYLANDI'")
            stat_onaylanan = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT COUNT(*) FROM satislar.teklifler
                WHERE silindi_mi = 0 AND MONTH(tarih) = MONTH(GETDATE()) AND YEAR(tarih) = YEAR(GETDATE())
            """)
            stat_bu_ay = cursor.fetchone()[0] or 0

            conn.close()

            # İstatistikleri güncelle
            self._update_stat_value(self.stat_toplam, str(stat_toplam))
            self._update_stat_value(self.stat_bekleyen, str(stat_bekleyen))
            self._update_stat_value(self.stat_onaylanan, str(stat_onaylanan))
            self._update_stat_value(self.stat_bu_ay, str(stat_bu_ay))

            # Filtreleme
            arama = self.search_input.text().strip().lower()
            durum_filtre = self.durum_combo.currentData() or ""
            tarih_bas = self.tarih_bas.date().toPython()
            tarih_bit = self.tarih_bit.date().toPython()

            filtered = []
            for item in items:
                if arama:
                    teklif_no = str(item[1] or '').lower()
                    cari = str(item[4] or '').lower()
                    proje = str(item[5] or '').lower()
                    if arama not in teklif_no and arama not in cari and arama not in proje:
                        continue
                if durum_filtre:
                    if str(item[9] or '') != durum_filtre:
                        continue
                tarih = item[3]
                if tarih:
                    if hasattr(tarih, 'date'):
                        tarih = tarih.date()
                    if tarih < tarih_bas or tarih > tarih_bit:
                        continue
                filtered.append(item)

            self.total_items = len(filtered)
            self.total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)
            start = (self.current_page - 1) * self.page_size
            end = start + self.page_size
            page_items = filtered[start:end]
            self._populate_table(page_items)
            self._update_paging()
            self.stat_label.setText(f"Toplam: {self.total_items} teklif")
        except Exception as e:
            self.stat_label.setText(f"Hata: {str(e)[:80]}")
            self.table.setRowCount(0)

    def _populate_table(self, items):
        t = self.theme
        self.table.clearSelection()
        self.table.setRowCount(0)
        self.table.setRowCount(len(items))

        for row, item in enumerate(items):
            # Teklif No
            no_item = QTableWidgetItem(str(item[1] or ''))
            try:
                id_val = int(item[0]) if item[0] else 0
            except Exception:
                id_val = 0
            no_item.setData(Qt.UserRole, id_val)
            self.table.setItem(row, 0, no_item)

            # Rev
            rev_no = item[2] or 0
            rev_item = QTableWidgetItem(f"Rev.{rev_no:02d}")
            self.table.setItem(row, 1, rev_item)

            # Tarih
            tarih = item[3]
            tarih_str = str(tarih)[:10] if tarih else '-'
            self.table.setItem(row, 2, QTableWidgetItem(tarih_str))

            # Müşteri
            self.table.setItem(row, 3, QTableWidgetItem(str(item[4] or '')[:30]))

            # Proje
            self.table.setItem(row, 4, QTableWidgetItem(str(item[5] or '')[:25]))

            # Durum
            durum = str(item[9] or 'TASLAK')
            durum_metin = DURUM_METINLER.get(durum, durum)
            durum_item = QTableWidgetItem(durum_metin)
            durum_item.setForeground(QColor(DURUM_RENKLER.get(durum, '#888')))
            durum_item.setData(Qt.UserRole + 1, durum)
            self.table.setItem(row, 5, durum_item)

            # Geçerlilik
            gecerlilik = item[10]
            gecerlilik_str = str(gecerlilik)[:10] if gecerlilik else '-'
            gecerlilik_item = QTableWidgetItem(gecerlilik_str)
            if gecerlilik:
                g = gecerlilik
                if hasattr(g, 'date'):
                    g = g.date()
                if g < date.today():
                    gecerlilik_item.setForeground(QColor(t['error']))
            self.table.setItem(row, 6, gecerlilik_item)

    # ── SAYFALAMA ──
    def _update_paging(self):
        self.page_label.setText(f"{self.current_page} / {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load_data()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._load_data()

    def _filter_changed(self):
        self.current_page = 1
        self._load_data()

    # ── CONTEXT MENU ──
    def _show_context_menu(self, pos):
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        item = self.table.item(current_row, 0)
        if not item:
            return

        durum_item = self.table.item(current_row, 5)
        durum = durum_item.data(Qt.UserRole + 1) if durum_item else ''

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {self.theme['bg_card']}; border: 1px solid {self.theme['border']}; border-radius: 8px; padding: 6px; }}
            QMenu::item {{ padding: 10px 20px; border-radius: 4px; color: {self.theme['text']}; }}
            QMenu::item:selected {{ background: {self.theme['bg_hover']}; }}
        """)

        ac = menu.addAction("📋 Detay Aç")
        ac.triggered.connect(self._open_detail)

        pdf = menu.addAction("📄 PDF Çıktı")
        pdf.triggered.connect(self._export_pdf)

        menu.addSeparator()

        rev = menu.addAction("🔄 Yeni Revizyon")
        rev.triggered.connect(self._create_revision)

        if durum == 'ONAYLANDI':
            ie = menu.addAction("🔀 İş Emrine Dönüştür")
            ie.triggered.connect(self._convert_to_is_emri)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    # ── AKSIYONLAR ──
    def _yeni_teklif(self):
        from modules.teklif.teklif_detay import TeklifDetayDialog
        dialog = TeklifDetayDialog(theme=self.theme, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _yeni_teklif_sablondan(self):
        """Şablondan teklif oluştur"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sablon_adi FROM satislar.teklif_sablonlari
                WHERE aktif_mi = 1 ORDER BY sablon_adi
            """)
            sablonlar = cursor.fetchall()
            conn.close()

            if not sablonlar:
                QMessageBox.warning(self, "Uyarı", "Aktif şablon bulunamadı.")
                return

            # Şablon seçim menüsü
            menu = QMenu(self)
            menu.setStyleSheet(f"""
                QMenu {{ background: {self.theme['bg_card']}; border: 1px solid {self.theme['border']}; border-radius: 8px; padding: 6px; }}
                QMenu::item {{ padding: 10px 20px; border-radius: 4px; color: {self.theme['text']}; }}
                QMenu::item:selected {{ background: {self.theme['bg_hover']}; }}
            """)
            for s in sablonlar:
                action = menu.addAction(f"📋 {s[1]}")
                action.setData(s[0])
                action.triggered.connect(lambda checked, sid=s[0]: self._open_from_sablon(sid))

            # Butonun altında göster
            sender = self.sender()
            if sender:
                menu.exec(sender.mapToGlobal(sender.rect().bottomLeft()))
            else:
                menu.exec(self.mapToGlobal(self.rect().center()))

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Şablon yükleme hatası: {e}")

    def _open_from_sablon(self, sablon_id):
        from modules.teklif.teklif_detay import TeklifDetayDialog
        dialog = TeklifDetayDialog(sablon_id=sablon_id, theme=self.theme, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _open_detail(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        item = self.table.item(current_row, 0)
        if not item:
            return
        teklif_id = item.data(Qt.UserRole)
        try:
            teklif_id = int(teklif_id) if teklif_id else None
        except Exception:
            teklif_id = None
        if teklif_id:
            from modules.teklif.teklif_detay import TeklifDetayDialog
            dialog = TeklifDetayDialog(teklif_id=teklif_id, theme=self.theme, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self._load_data()

    def _export_pdf(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen PDF çıktısı almak için bir teklif seçin.")
            return
        item = self.table.item(current_row, 0)
        if not item:
            return
        teklif_id = item.data(Qt.UserRole)
        try:
            teklif_id = int(teklif_id) if teklif_id else None
        except Exception:
            teklif_id = None
        if not teklif_id:
            return
        try:
            from utils.teklif_pdf import teklif_pdf_olustur
            teklif_pdf_olustur(teklif_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturma hatası: {e}")

    def _create_revision(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        item = self.table.item(current_row, 0)
        if not item:
            return
        teklif_id = item.data(Qt.UserRole)
        try:
            teklif_id = int(teklif_id) if teklif_id else None
        except Exception:
            teklif_id = None
        if not teklif_id:
            return

        cevap = QMessageBox.question(
            self, "Revizyon Oluştur",
            "Bu teklifin yeni bir revizyonunu oluşturmak istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No
        )
        if cevap != QMessageBox.Yes:
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Mevcut teklifi oku
            cursor.execute("""
                SELECT teklif_no, revizyon_no, ana_teklif_id, cari_id, cari_unvani,
                       cari_yetkili, cari_telefon, cari_email, iskonto_oran, kdv_oran,
                       para_birimi, referans_no, proje_adi, teslim_suresi,
                       odeme_kosullari, notlar, ozel_kosullar, gecerlilik_tarihi
                FROM satislar.teklifler WHERE id = ?
            """, (teklif_id,))
            teklif = cursor.fetchone()
            if not teklif:
                conn.close()
                QMessageBox.warning(self, "Uyarı", "Teklif bulunamadı.")
                return

            teklif_no = teklif[0]
            yeni_rev = (teklif[1] or 0) + 1
            ana_id = teklif[2] or teklif_id

            # Yeni revizyon ekle
            cursor.execute("""
                INSERT INTO satislar.teklifler (
                    teklif_no, revizyon_no, ana_teklif_id, tarih, gecerlilik_tarihi,
                    cari_id, cari_unvani, cari_yetkili, cari_telefon, cari_email,
                    iskonto_oran, kdv_oran, para_birimi, durum,
                    referans_no, proje_adi, teslim_suresi, odeme_kosullari, notlar, ozel_kosullar
                ) VALUES (?, ?, ?, GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?, 'TASLAK', ?, ?, ?, ?, ?, ?)
            """, (
                teklif_no, yeni_rev, ana_id, teklif[17],
                teklif[3], teklif[4], teklif[5], teklif[6], teklif[7],
                teklif[8], teklif[9], teklif[10],
                teklif[11], teklif[12], teklif[13], teklif[14], teklif[15], teklif[16]
            ))

            cursor.execute("SELECT @@IDENTITY")
            yeni_id = int(cursor.fetchone()[0])

            # Satırları kopyala
            cursor.execute("""
                INSERT INTO satislar.teklif_satirlari (
                    teklif_id, satir_no, urun_id, stok_kodu, stok_adi,
                    kaplama_tipi_id, kaplama_tipi_adi, kalinlik_mikron, malzeme_tipi,
                    yuzey_alani, yuzey_birimi, miktar, birim, birim_fiyat,
                    iskonto_oran, tutar, aciklama, teknik_not
                )
                SELECT ?, satir_no, urun_id, stok_kodu, stok_adi,
                       kaplama_tipi_id, kaplama_tipi_adi, kalinlik_mikron, malzeme_tipi,
                       yuzey_alani, yuzey_birimi, miktar, birim, birim_fiyat,
                       iskonto_oran, tutar, aciklama, teknik_not
                FROM satislar.teklif_satirlari WHERE teklif_id = ?
            """, (yeni_id, teklif_id))

            # Toplamları yeniden hesapla
            cursor.execute("""
                SELECT ISNULL(SUM(tutar), 0) FROM satislar.teklif_satirlari WHERE teklif_id = ?
            """, (yeni_id,))
            ara_toplam = float(cursor.fetchone()[0])
            iskonto_oran = float(teklif[8] or 0)
            iskonto_tutar = ara_toplam * iskonto_oran / 100
            kdv_oran = float(teklif[9] or 20)
            kdv_tutar = (ara_toplam - iskonto_tutar) * kdv_oran / 100
            genel_toplam = ara_toplam - iskonto_tutar + kdv_tutar

            cursor.execute("""
                UPDATE satislar.teklifler SET
                    ara_toplam = ?, iskonto_tutar = ?, kdv_tutar = ?, genel_toplam = ?
                WHERE id = ?
            """, (ara_toplam, iskonto_tutar, kdv_tutar, genel_toplam, yeni_id))

            conn.commit()
            LogManager.log_update('teklif', 'satislar.teklifler', None, 'Kayit guncellendi')
            conn.close()

            QMessageBox.information(self, "Başarılı", f"Yeni revizyon oluşturuldu: {teklif_no} Rev.{yeni_rev:02d}")
            self._load_data()

            # Yeni revizyonu aç
            from modules.teklif.teklif_detay import TeklifDetayDialog
            dialog = TeklifDetayDialog(teklif_id=yeni_id, theme=self.theme, parent=self)
            dialog.exec()
            self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Revizyon oluşturma hatası: {e}")

    def _convert_to_is_emri(self):
        """Onaylanan teklifi iş emrine dönüştür"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        item = self.table.item(current_row, 0)
        if not item:
            return
        teklif_id = item.data(Qt.UserRole)
        try:
            teklif_id = int(teklif_id) if teklif_id else None
        except Exception:
            teklif_id = None
        if not teklif_id:
            return

        durum_item = self.table.item(current_row, 5)
        durum = durum_item.data(Qt.UserRole + 1) if durum_item else ''
        if durum != 'ONAYLANDI':
            QMessageBox.warning(self, "Uyarı", "Sadece onaylanmış teklifler iş emrine dönüştürülebilir.")
            return

        cevap = QMessageBox.question(
            self, "İş Emrine Dönüştür",
            "Bu teklifi iş emrine dönüştürmek istiyor musunuz?\nHer teklif kalemi için ayrı iş emri oluşturulacaktır.",
            QMessageBox.Yes | QMessageBox.No
        )
        if cevap != QMessageBox.Yes:
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Teklif bilgilerini oku
            cursor.execute("""
                SELECT t.cari_id, t.cari_unvani, t.proje_adi
                FROM satislar.teklifler t WHERE t.id = ?
            """, (teklif_id,))
            teklif = cursor.fetchone()
            if not teklif:
                conn.close()
                return

            cari_id = teklif[0]
            cari_unvani = teklif[1] or ''

            # Teklif satırlarını oku
            cursor.execute("""
                SELECT stok_kodu, stok_adi, kaplama_tipi_adi, miktar, birim
                FROM satislar.teklif_satirlari WHERE teklif_id = ?
            """, (teklif_id,))
            satirlar = cursor.fetchall()

            if not satirlar:
                conn.close()
                QMessageBox.warning(self, "Uyarı", "Teklif kalemleri bulunamadı.")
                return

            olusturulan = 0
            for satir in satirlar:
                stok_kodu = satir[0] or ''
                stok_adi = satir[1] or ''
                kaplama = satir[2] or ''
                miktar = float(satir[3] or 0)
                birim = satir[4] or 'ADET'

                # İş emri no oluştur
                cursor.execute("SELECT ISNULL(MAX(id), 0) FROM siparis.is_emirleri")
                max_id = int(cursor.fetchone()[0])
                is_emri_no = f"IE-{datetime.now().strftime('%Y%m')}-{max_id + 1:04d}"

                cursor.execute("""
                    INSERT INTO siparis.is_emirleri (
                        is_emri_no, tarih, cari_id, cari_unvani, stok_kodu, stok_adi,
                        kaplama_tipi, planlanan_miktar, toplam_miktar, birim,
                        termin_tarihi, oncelik, durum, silindi_mi,
                        uretim_notu
                    ) VALUES (?, GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?,
                              DATEADD(DAY, 7, GETDATE()), 5, 'BEKLIYOR', 0, ?)
                """, (
                    is_emri_no, cari_id, cari_unvani, stok_kodu, stok_adi,
                    kaplama, miktar, miktar, birim,
                    f"Teklif'ten dönüştürüldü (Teklif ID: {teklif_id})"
                ))
                olusturulan += 1

            # Teklif durumunu güncelle
            cursor.execute("""
                UPDATE satislar.teklifler SET
                    durum = 'IS_EMRINE_DONUSTURULDU',
                    is_emrine_donus_tarihi = GETDATE(),
                    guncelleme_tarihi = GETDATE()
                WHERE id = ?
            """, (teklif_id,))

            conn.commit()
            LogManager.log_delete('teklif', 'satislar.teklifler', None, 'Kayit silindi (soft delete)')
            conn.close()

            # Bildirim: Tekliften iş emri oluşturuldu
            try:
                from core.bildirim_tetikleyici import BildirimTetikleyici
                BildirimTetikleyici.is_emri_olusturuldu(
                    ie_id=0,
                    ie_no=f"{olusturulan} IE (Teklif #{teklif_id})",
                    musteri_adi=cari_unvani,
                )
            except Exception as bt_err:
                print(f"Bildirim hatasi: {bt_err}")

            QMessageBox.information(
                self, "Başarılı",
                f"{olusturulan} adet iş emri oluşturuldu."
            )
            self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İş emri dönüşüm hatası: {e}")
