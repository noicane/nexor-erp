# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Kalite Giriş Kontrol Sayfası
[MODERNIZED UI - v3.0]
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QWidget, QDoubleSpinBox, QGroupBox, QGridLayout,
    QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage, create_action_buttons
from components.dialog_minimize_bar import add_minimize_button
from core.database import get_db_connection
from core.log_manager import LogManager


def get_modern_style(theme: dict) -> dict:
    """Modern tema renkleri - TÜM MODÜLLERDE AYNI"""
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


class KriterKontrolDialog(QDialog):
    """Kriterlere göre kalite kontrol dialogu"""
    
    def __init__(self, theme: dict, lot_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.lot_data = lot_data
        self.kriterler = []
        self.kriter_widgets = {}
        self.setWindowTitle(f"Kalite Kontrol - {lot_data.get('lot_no', '')}")
        self.setMinimumSize(700, 600)
        self._load_kriterler()
        self._setup_ui()
        add_minimize_button(self)

    def _load_kriterler(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad, kategori, kontrol_tipi, birim, min_deger, max_deger, secenekler, zorunlu_mu, kritik_mi FROM kalite.giris_kontrol_kriterleri WHERE aktif_mi = 1 ORDER BY sira_no")
            for row in cursor.fetchall():
                self.kriterler.append({'id': row[0], 'ad': row[1], 'kategori': row[2], 'kontrol_tipi': row[3], 'birim': row[4], 'min_deger': row[5], 'max_deger': row[6], 'secenekler': row[7], 'zorunlu_mu': row[8], 'kritik_mi': row[9]})
        except Exception as e:
            print(f"Kriter yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main', '#1a1f2e')}; }} QLabel {{ color: {self.theme.get('text', '#fff')}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Lot bilgi
        info = QLabel(f"<b>Lot:</b> {self.lot_data.get('lot_no', '')} | <b>Müşteri:</b> {self.lot_data.get('cari_unvani', '')} | <b>Miktar:</b> {self.lot_data.get('miktar', 0):,.0f}")
        info.setStyleSheet(f"background: {self.theme.get('bg_card', '#242938')}; padding: 12px; border-radius: 8px;")
        layout.addWidget(info)
        
        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        if not self.kriterler:
            scroll_layout.addWidget(QLabel("⚠️ Tanımlı kriter bulunamadı"))
        else:
            for kriter in self.kriterler:
                frame = QFrame()
                frame.setStyleSheet(f"background: {self.theme.get('bg_card', '#242938')}; border: 1px solid {self.theme.get('border', '#3d4454')}; border-radius: 6px; padding: 8px;")
                h = QHBoxLayout(frame)
                h.addWidget(QLabel(f"{'🔒' if kriter['zorunlu_mu'] else ''} {kriter['ad']}"))
                
                if kriter['kontrol_tipi'] == 'CHECKBOX':
                    cb = QCheckBox("Uygun")
                    self.kriter_widgets[kriter['id']] = ('CHECKBOX', cb)
                    h.addWidget(cb)
                elif kriter['kontrol_tipi'] == 'OLCUM':
                    spin = QDoubleSpinBox()
                    spin.setRange(-999999, 999999)
                    self.kriter_widgets[kriter['id']] = ('OLCUM', spin, kriter['min_deger'], kriter['max_deger'])
                    h.addWidget(spin)
                    if kriter['birim']:
                        h.addWidget(QLabel(kriter['birim']))
                elif kriter['kontrol_tipi'] == 'SECIM':
                    combo = QComboBox()
                    combo.addItem("-- Seçiniz --", "")
                    for s in (kriter['secenekler'] or '').split('|'):
                        if s.strip():
                            combo.addItem(s.strip(), s.strip())
                    self.kriter_widgets[kriter['id']] = ('SECIM', combo)
                    h.addWidget(combo)
                scroll_layout.addWidget(frame)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Not
        h = QHBoxLayout()
        h.addWidget(QLabel("Not:"))
        self.not_input = QLineEdit()
        h.addWidget(self.not_input)
        layout.addLayout(h)
        
        # Butonlar
        btn = QHBoxLayout()
        for text, color, durum in [("✅ Onayla", self.theme.get('success', '#22c55e'), 'ONAYLANDI'), ("⚠️ Koşullu", '#3b82f6', 'KOSULLU'), ("❌ Red", self.theme.get('error', '#ef4444'), 'RED')]:
            b = QPushButton(text)
            b.setStyleSheet(f"background: {color}; color: white; border: none; border-radius: 6px; padding: 12px 20px; font-weight: bold;")
            b.clicked.connect(lambda _, d=durum: self._save(d))
            btn.addWidget(b)
        btn.addStretch()
        cancel = QPushButton("İptal")
        cancel.setStyleSheet(f"background: {self.theme.get('bg_input', '#2d3548')}; color: {self.theme.get('text', '#fff')}; border: 1px solid {self.theme.get('border', '#3d4454')}; border-radius: 6px; padding: 12px 20px;")
        cancel.clicked.connect(self.reject)
        btn.addWidget(cancel)
        layout.addLayout(btn)
    
    def _save(self, durum):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            lot_no = self.lot_data.get('lot_no')

            # Durum belirleme
            if durum == 'ONAYLANDI':
                kalite_durumu = 'ONAY'
                durum_kodu = 'GIRIS_ONAY'  # YENİ: Giriş kalite onaylandı
            elif durum == 'RED':
                kalite_durumu = 'RED'
                durum_kodu = 'RED'  # YENİ: Red deposuna gidecek
            else:  # KOSULLU
                kalite_durumu = 'KOSULLU'
                durum_kodu = 'GIRIS_KALITE'  # YENİ: Hala giriş kalitede

            # DÜZELTME: Önce mevcut depo_id'yi bul
            cursor.execute("""
                SELECT depo_id FROM stok.stok_bakiye
                WHERE lot_no = ?
                  AND durum_kodu IN ('KABUL', 'GIRIS_KALITE')
                  AND miktar > 0
            """, (lot_no,))
            depo_result = cursor.fetchone()

            if not depo_result:
                QMessageBox.warning(self, "Uyarı", f"Lot bulunamadı veya işlem yapılmış: {lot_no}")
                return

            depo_id = depo_result[0]

            # Durum güncelleme - DÜZELTME: WHERE'e depo_id eklendi
            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET kalite_durumu = ?,
                    durum_kodu = ?,
                    son_hareket_tarihi = GETDATE()
                WHERE lot_no = ? AND depo_id = ?
            """, (kalite_durumu, durum_kodu, lot_no, depo_id))

            # Etkilenen satır sayısını kontrol et
            if cursor.rowcount == 0:
                QMessageBox.warning(self, "Uyarı", f"Lot güncellenemedi: {lot_no}")
                return

            # RED durumunda transfer gerekebilir (opsiyonel - şimdilik sadece durum güncelliyoruz)
            if durum == 'RED':
                print(f"⚠️ LOT {lot_no} RED durumuna alındı. RED deposuna transfer yapılmalı.")
                # TODO: Gelecekte hareket_motoru.transfer() ile RED deposuna taşı

            conn.commit()
            LogManager.log_update('kalite', 'stok.stok_bakiye', None, 'Durum guncellendi')

            durum_text = {
                'ONAYLANDI': 'onaylandı ✅',
                'RED': 'reddedildi ❌',
                'KOSULLU': 'koşullu onaylandı ⚠️'
            }
            QMessageBox.information(
                self, "Başarılı",
                f"Kalite kontrol {durum_text.get(durum, durum)}!\n\n"
                f"Lot: {lot_no}\n"
                f"Yeni Durum: {durum_kodu}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass


class PaletDetayDialog(QDialog):
    """Palet detay dialogu"""
    
    def __init__(self, theme: dict, palet_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.palet_data = palet_data
        self.setWindowTitle(f"Palet - {palet_data.get('lot_no', '')}")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        add_minimize_button(self)
    
    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main', '#1a1f2e')}; }} QLabel {{ color: {self.theme.get('text', '#fff')}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Bilgiler
        for label, key in [("Lot No:", 'lot_no'), ("Stok Kodu:", 'stok_kodu'), ("Müşteri:", 'cari_unvani')]:
            h = QHBoxLayout()
            h.addWidget(QLabel(f"<b>{label}</b>"))
            h.addWidget(QLabel(str(self.palet_data.get(key, ''))))
            h.addStretch()
            layout.addLayout(h)
        
        miktar = self.palet_data.get('miktar', 0)
        layout.addWidget(QLabel(f"<b>Miktar:</b> <span style='color: {self.theme.get('success', '#22c55e')}'>{miktar:,.0f}</span>"))
        
        durum = self.palet_data.get('kalite_durumu', 'BEKLIYOR')
        colors = {'BEKLIYOR': '#f59e0b', 'ONAYLANDI': '#22c55e', 'RED': '#ef4444', 'KOSULLU': '#3b82f6'}
        layout.addWidget(QLabel(f"<b>Durum:</b> <span style='color: {colors.get(durum, '#888')}'>{durum}</span>"))
        
        layout.addStretch()
        
        # Butonlar
        if durum == 'BEKLIYOR':
            kriter_btn = QPushButton("📋 Kriter Kontrol")
            kriter_btn.setStyleSheet(f"background: {self.theme.get('primary', '#6366f1')}; color: white; border: none; border-radius: 6px; padding: 12px 20px; font-weight: bold;")
            kriter_btn.clicked.connect(self._kriter_kontrol)
            layout.addWidget(kriter_btn)
            
            h = QHBoxLayout()
            for text, color, durum_val in [("✅ Hızlı Onayla", self.theme.get('success', '#22c55e'), 'ONAYLANDI'), ("❌ Hızlı Red", self.theme.get('error', '#ef4444'), 'RED')]:
                b = QPushButton(text)
                b.setStyleSheet(f"background: {color}; color: white; border: none; border-radius: 6px; padding: 10px 16px;")
                b.clicked.connect(lambda _, d=durum_val: self._quick_update(d))
                h.addWidget(b)
            layout.addLayout(h)
        
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(f"background: {self.theme.get('bg_input', '#2d3548')}; color: {self.theme.get('text', '#fff')}; border: 1px solid {self.theme.get('border', '#3d4454')}; border-radius: 6px; padding: 10px 20px;")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def _kriter_kontrol(self):
        dlg = KriterKontrolDialog(self.theme, self.palet_data, self)
        if dlg.exec():
            self.accept()
    
    def _quick_update(self, durum):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            lot_no = self.palet_data.get('lot_no')

            # Sadece UPDATE yap!
            cursor.execute("""
                UPDATE stok.stok_bakiye
                SET kalite_durumu = ?, son_hareket_tarihi = GETDATE()
                WHERE lot_no = ?
            """, (durum, lot_no))

            if cursor.rowcount == 0:
                QMessageBox.warning(self, "Uyarı", f"Lot bulunamadı: {lot_no}")
                return

            conn.commit()
            LogManager.log_update('kalite', 'stok.stok_bakiye', None, 'Durum guncellendi')

            durum_text = {'ONAYLANDI': 'onaylandı', 'RED': 'reddedildi'}
            QMessageBox.information(self, "Başarılı", f"Palet {durum_text.get(durum, 'güncellendi')}!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass


class AnaLotDetayDialog(QDialog):
    """Ana lot detay dialogu"""
    
    def __init__(self, theme: dict, parent_lot_no: str, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.parent_lot_no = parent_lot_no
        self.paletler = []
        self.setWindowTitle(f"Ana Lot - {parent_lot_no}")
        self.setMinimumSize(900, 600)
        self._load_data()
        self._setup_ui()
        add_minimize_button(self)

    def _load_data(self):
        self.paletler = []  # ÖNCEKİ VERİLERİ TEMİZLE!
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sb.lot_no, sb.palet_no, sb.toplam_palet,
                       u.urun_kodu, u.urun_adi,
                       sb.miktar, sb.kalite_durumu
                FROM stok.stok_bakiye sb
                LEFT JOIN stok.urunler u ON sb.urun_id = u.id
                WHERE sb.parent_lot_no = ?
                ORDER BY sb.palet_no
            """, (self.parent_lot_no,))
            for row in cursor.fetchall():
                self.paletler.append({
                    'lot_no': row[0],
                    'palet_no': row[1],
                    'toplam_palet': row[2],
                    'stok_kodu': row[3],
                    'stok_adi': row[4],
                    'miktar': row[5],
                    'kalite_durumu': row[6]
                })
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main', '#1a1f2e')}; }} QLabel {{ color: {self.theme.get('text', '#fff')}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Başlık
        layout.addWidget(QLabel(f"<h2>📋 {self.parent_lot_no}</h2>"))
        
        # İstatistik
        bekleyen = sum(1 for p in self.paletler if p['kalite_durumu'] == 'BEKLIYOR')
        onaylanan = sum(1 for p in self.paletler if p['kalite_durumu'] == 'ONAYLANDI')
        layout.addWidget(QLabel(f"Toplam: {len(self.paletler)} palet | Bekleyen: {bekleyen} | Onaylanan: {onaylanan}"))
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Palet", "Lot No", "Miktar", "Durum", "Seç", "İşlem"])
        self.table.setColumnWidth(5, 120)

        # Otomatik ölçülendirme: LOT NO esnek, diğerleri içeriğe göre
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # PALET
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # LOT NO
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # MİKTAR
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # DURUM
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # SEÇ
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # İŞLEM
        
        self.table.setStyleSheet(f"""
            QTableWidget {{ 
                background: {self.theme.get('bg_card', '#242938')}; 
                color: {self.theme.get('text', '#fff')}; 
                border: 1px solid {self.theme.get('border', '#3d4454')};
                gridline-color: {self.theme.get('border', '#3d4454')};
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {self.theme.get('border', '#3d4454')};
            }}
            QHeaderView::section {{ 
                background: {self.theme.get('bg_hover', '#2d3548')}; 
                color: {self.theme.get('text', '#fff')}; 
                padding: 8px 10px; 
                border: none;
                font-weight: 600;
                font-size: 11px;
            }}
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._fill_table()
        layout.addWidget(self.table)
        
        # Butonlar
        h = QHBoxLayout()
        for text, color, durum in [("✅ Seçilenleri Onayla", self.theme.get('success', '#22c55e'), 'ONAYLANDI'), ("❌ Seçilenleri Reddet", self.theme.get('error', '#ef4444'), 'RED')]:
            b = QPushButton(text)
            b.setStyleSheet(f"background: {color}; color: white; border: none; border-radius: 6px; padding: 10px 16px; font-weight: bold;")
            b.clicked.connect(lambda _, d=durum: self._bulk_update(d))
            h.addWidget(b)
        h.addStretch()
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(f"background: {self.theme.get('bg_input', '#2d3548')}; color: {self.theme.get('text', '#fff')}; border: 1px solid {self.theme.get('border', '#3d4454')}; border-radius: 6px; padding: 10px 20px;")
        close_btn.clicked.connect(self.close)
        h.addWidget(close_btn)
        layout.addLayout(h)
    
    def _fill_table(self):
        self.table.setRowCount(len(self.paletler))
        colors = {'BEKLIYOR': QColor('#f59e0b'), 'ONAYLANDI': QColor('#22c55e'), 'RED': QColor('#ef4444')}
        for i, p in enumerate(self.paletler):
            self.table.setItem(i, 0, QTableWidgetItem(f"{p['palet_no']}/{p['toplam_palet']}"))
            self.table.setItem(i, 1, QTableWidgetItem(p['lot_no']))
            self.table.setItem(i, 2, QTableWidgetItem(f"{p['miktar']:,.0f}"))
            durum_item = QTableWidgetItem(p['kalite_durumu'] or 'BEKLIYOR')
            durum_item.setForeground(colors.get(p['kalite_durumu'], QColor('#888')))
            self.table.setItem(i, 3, durum_item)

            cb = QCheckBox()
            cb.setEnabled(p['kalite_durumu'] == 'BEKLIYOR')
            cb.setProperty('lot_no', p['lot_no'])
            w = QWidget()
            l = QHBoxLayout(w)
            l.addWidget(cb)
            l.setAlignment(Qt.AlignCenter)
            l.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(i, 4, w)
            self.table.setRowHeight(i, 42)

            widget = create_action_buttons(self.theme, [
                ("📋", "Detay", lambda _, palet=p: self._open_palet(palet), "view"),
            ])
            self.table.setCellWidget(i, 5, widget)
            self.table.setRowHeight(i, 42)
    
    def _open_palet(self, palet):
        dlg = PaletDetayDialog(self.theme, palet, self)
        if dlg.exec():
            # Verileri yeniden yükle (liste _load_data içinde temizleniyor)
            self._load_data()
            self._fill_table()
    
    def _bulk_update(self, durum):
        selected = []
        for i in range(self.table.rowCount()):
            w = self.table.cellWidget(i, 4)
            if w:
                cb = w.findChild(QCheckBox)
                if cb and cb.isChecked():
                    selected.append(cb.property('lot_no'))
        
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir palet seçin!")
            return
        
        durum_text = {'ONAYLANDI': 'onaylamak', 'RED': 'reddetmek'}
        reply = QMessageBox.question(
            self, "Onay",
            f"{len(selected)} paleti {durum_text.get(durum, 'güncellemek')} istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Durum belirleme
            if durum == 'ONAYLANDI':
                kalite_durumu = 'ONAY'
                durum_kodu = 'GIRIS_ONAY'
            else:  # RED
                kalite_durumu = 'RED'
                durum_kodu = 'RED'

            updated = 0
            for lot in selected:
                cursor.execute("""
                    UPDATE stok.stok_bakiye
                    SET kalite_durumu = ?,
                        durum_kodu = ?,
                        son_hareket_tarihi = GETDATE()
                    WHERE lot_no = ?
                """, (kalite_durumu, durum_kodu, lot))
                updated += cursor.rowcount

            conn.commit()
            LogManager.log_update('kalite', 'stok.stok_bakiye', None, 'Durum guncellendi')

            durum_text2 = {'ONAYLANDI': 'onaylandı ✅', 'RED': 'reddedildi ❌'}
            QMessageBox.information(
                self, "Başarılı",
                f"{updated} palet {durum_text2.get(durum, 'güncellendi')}!\n\n"
                f"Yeni Durum: {durum_kodu}"
            )

            # Verileri yeniden yükle
            self._load_data()
            self._fill_table()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            if conn:
                try: conn.close()
                except Exception: pass


class KaliteGirisPage(BasePage):
    """Kalite Giriş Kontrol Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)
        
        # Kompakt Header - Tek satır
        header_frame = QFrame()
        header_frame.setFixedHeight(50)
        header_frame.setStyleSheet(f"QFrame {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px; }}")
        h = QHBoxLayout(header_frame)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(12)
        
        title = QLabel("🔬 Kalite Giriş Kontrol")
        title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {s['text']};")
        h.addWidget(title)
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara...")
        self.search_input.setFixedWidth(180)
        self.search_input.setFixedHeight(28)
        self.search_input.setStyleSheet(f"background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 4px; padding: 0 8px; color: {s['text']}; font-size: 11px;")
        self.search_input.returnPressed.connect(self._load_data)
        h.addWidget(self.search_input)
        
        # Durum combo
        self.durum_combo = QComboBox()
        self.durum_combo.setFixedWidth(120)
        self.durum_combo.setFixedHeight(28)
        self.durum_combo.setStyleSheet(f"QComboBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 4px; padding: 0 8px; color: {s['text']}; font-size: 11px; }}")
        self.durum_combo.addItem("Bekleyenler", "BEKLIYOR")
        self.durum_combo.addItem("Tümü", None)
        self.durum_combo.addItem("Onaylananlar", "ONAYLANDI")
        self.durum_combo.currentIndexChanged.connect(self._load_data)
        h.addWidget(self.durum_combo)
        
        h.addStretch()
        
        # İstatistikler - header içinde kompakt
        self.stat_widgets = {}
        for key, label, color in [('bekleyen', '⏳', s['warning']), ('onaylanan', '✅', s['success']), ('toplam', '📦', s['primary'])]:
            stat_frame = QFrame()
            stat_frame.setStyleSheet(f"background: transparent;")
            sl = QHBoxLayout(stat_frame)
            sl.setContentsMargins(8, 0, 8, 0)
            sl.setSpacing(4)
            icon = QLabel(label)
            icon.setStyleSheet("font-size: 14px;")
            sl.addWidget(icon)
            val = QLabel("0")
            val.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 600;")
            self.stat_widgets[key] = val
            sl.addWidget(val)
            h.addWidget(stat_frame)
        
        refresh_btn = QPushButton("Yenile")
        refresh_btn.setFixedSize(60, 28)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 4px; font-size: 12px; }} QPushButton:hover {{ background: {s['border']}; }}")
        refresh_btn.clicked.connect(self._load_data)
        h.addWidget(refresh_btn)
        
        layout.addWidget(header_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Ana Lot", "Stok Kodu", "Müşteri", "Palet", "Bekleyen", "Durum", "İşlem"])
        self.table.setColumnWidth(6, 120)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setStyleSheet(f"""
            QTableWidget {{ 
                background: {s['input_bg']}; 
                color: {s['text']}; 
                border: 1px solid {s['border']}; 
                border-radius: 8px;
                gridline-color: {s['border']};
                font-size: 12px;
            }}
            QTableWidget::item {{ 
                padding: 6px; 
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
                padding: 8px 6px; 
                border: none; 
                border-bottom: 2px solid {s['primary']};
                font-weight: 600;
                font-size: 11px;
            }}
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)
    
    def _load_data(self):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            search = self.search_input.text().strip()
            durum = self.durum_combo.currentData()

            query = """
                SELECT sb.parent_lot_no, MAX(u.urun_kodu), COUNT(*),
                    SUM(CASE WHEN sb.kalite_durumu = 'BEKLIYOR' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN sb.kalite_durumu = 'ONAY' THEN 1 ELSE 0 END)
                FROM stok.stok_bakiye sb
                LEFT JOIN stok.urunler u ON sb.urun_id = u.id
                WHERE sb.parent_lot_no IS NOT NULL
                  AND sb.durum_kodu IN ('KABUL', 'GIRIS_KALITE', 'GIRIS_ONAY')
            """
            params = []
            if search:
                query += " AND (sb.parent_lot_no LIKE ? OR u.urun_kodu LIKE ?)"
                params.extend([f"%{search}%"] * 2)
            query += " GROUP BY sb.parent_lot_no"
            if durum == 'BEKLIYOR':
                query += " HAVING SUM(CASE WHEN sb.kalite_durumu = 'BEKLIYOR' THEN 1 ELSE 0 END) > 0"
            elif durum == 'ONAYLANDI':
                query += " HAVING SUM(CASE WHEN sb.kalite_durumu = 'BEKLIYOR' THEN 1 ELSE 0 END) = 0"
            query += " ORDER BY sb.parent_lot_no DESC"

            print(f"DEBUG - Giriş Kalite Sorgusu:")
            print(f"Query: {query}")
            print(f"Params: {params}")

            cursor.execute(query, params)
            rows = cursor.fetchall()

            print(f"DEBUG - Bulunan kayıt sayısı: {len(rows)}")
            if rows:
                print(f"DEBUG - İlk kayıt: {rows[0]}")

            cursor.execute("""
                SELECT
                    SUM(CASE WHEN kalite_durumu = 'BEKLIYOR' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN kalite_durumu = 'ONAY' THEN 1 ELSE 0 END),
                    COUNT(*)
                FROM stok.stok_bakiye
                WHERE parent_lot_no IS NOT NULL
                  AND durum_kodu IN ('KABUL', 'GIRIS_KALITE', 'GIRIS_ONAY')
            """)
            stats = cursor.fetchone()
            print(f"DEBUG - İstatistikler: {stats}")

            if stats:
                self.stat_widgets['bekleyen'].setText(str(stats[0] or 0))
                self.stat_widgets['onaylanan'].setText(str(stats[1] or 0))
                self.stat_widgets['toplam'].setText(str(stats[2] or 0))

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(row[0] or ''))
                self.table.setItem(i, 1, QTableWidgetItem(row[1] or ''))
                self.table.setItem(i, 2, QTableWidgetItem(''))  # Müşteri - şimdilik boş
                self.table.setItem(i, 3, QTableWidgetItem(str(row[2] or 0)))

                bekleyen_item = QTableWidgetItem(str(row[3] or 0))
                if row[3] and row[3] > 0:
                    bekleyen_item.setForeground(QColor('#f59e0b'))
                    bekleyen_item.setFont(QFont("", -1, QFont.Bold))
                self.table.setItem(i, 4, bekleyen_item)

                if row[3] == row[2]:
                    durum_text, durum_color = "⏳ Bekliyor", QColor('#f59e0b')
                elif row[3] == 0:
                    durum_text, durum_color = "✅ Tamamlandı", QColor('#22c55e')
                else:
                    durum_text, durum_color = f"🔄 {row[4]}/{row[2]}", QColor('#3b82f6')
                durum_item = QTableWidgetItem(durum_text)
                durum_item.setForeground(durum_color)
                self.table.setItem(i, 5, durum_item)

                widget = self.create_action_buttons([
                    ("📋", "Detay", lambda checked, pl=row[0]: self._open_detail(pl), "info"),
                ])
                self.table.setCellWidget(i, 6, widget)
                self.table.setRowHeight(i, 42)
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def _open_detail(self, parent_lot):
        dlg = AnaLotDetayDialog(self.theme, parent_lot, self)
        dlg.exec()
        self._load_data()
    
    def _on_double_click(self, index):
        parent_lot = self.table.item(index.row(), 0).text()
        self._open_detail(parent_lot)
