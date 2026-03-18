# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Depo Çıkış Ekranı
Planlanan iş emirleri için malzeme çıkışı
Barkod okutma veya şifreli manuel çıkış
[MODERNIZED UI - v2.0]
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QFormLayout,
    QComboBox, QWidget, QGroupBox, QGridLayout, QInputDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager

MANUEL_CIKIS_SIFRE = "1234"

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

class ManuelCikisDialog(QDialog):
    def __init__(self, emir_data: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.s = get_modern_style(theme)
        self.emir_data = emir_data
        self.onaylandi = False
        self.setWindowTitle("Manuel Çıkış Onayı")
        self.setMinimumSize(450, 380)
        self._setup_ui()
    
    def _setup_ui(self):
        s = self.s
        self.setStyleSheet(f"QDialog {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 12px; }} QLabel {{ color: {s['text']}; }} QLineEdit {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px; color: {s['text']}; font-size: 14px; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        icon = QLabel("🔐"); icon.setStyleSheet("font-size: 28px;"); header.addWidget(icon)
        title = QLabel("Manuel Çıkış Onayı"); title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {s['warning']};"); header.addWidget(title); header.addStretch()
        layout.addLayout(header)
        
        warning = QLabel("⚠️ Barkod okutulamadığı için manuel çıkış yapılacak."); warning.setStyleSheet(f"color: {s['text_muted']}; font-size: 12px;"); layout.addWidget(warning)
        
        info_frame = QFrame(); info_frame.setStyleSheet(f"background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 10px; padding: 12px;")
        info_layout = QVBoxLayout(info_frame); info_layout.setSpacing(8)
        info_layout.addWidget(QLabel(f"📋 Çıkış Emri: {self.emir_data.get('emir_no', '-')}"))
        info_layout.addWidget(QLabel(f"🏷️ Lot No: {self.emir_data.get('lot_no', '-')}"))
        info_layout.addWidget(QLabel(f"📦 Ürün: {self.emir_data.get('stok_adi', '-')}"))
        info_layout.addWidget(QLabel(f"📊 Miktar: {self.emir_data.get('talep_miktar', 0):,.0f}"))
        layout.addWidget(info_frame)
        
        sifre_label = QLabel("🔑 Yetki Şifresi:"); sifre_label.setStyleSheet(f"font-weight: 600; color: {s['text']};"); layout.addWidget(sifre_label)
        self.sifre_input = QLineEdit(); self.sifre_input.setEchoMode(QLineEdit.Password); self.sifre_input.setPlaceholderText("Şifre girin..."); self.sifre_input.returnPressed.connect(self._onay); layout.addWidget(self.sifre_input)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(12); btn_layout.addStretch()
        iptal_btn = QPushButton("İptal"); iptal_btn.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; color: {s['text']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 12px 24px; }}"); iptal_btn.clicked.connect(self.reject); btn_layout.addWidget(iptal_btn)
        onay_btn = QPushButton("✓ Onayla"); onay_btn.setStyleSheet(f"QPushButton {{ background: {s['warning']}; color: white; border: none; border-radius: 8px; padding: 12px 28px; font-weight: 600; }}"); onay_btn.clicked.connect(self._onay); btn_layout.addWidget(onay_btn)
        layout.addLayout(btn_layout)
    
    def _onay(self):
        if self.sifre_input.text() == MANUEL_CIKIS_SIFRE:
            self.onaylandi = True; self.accept()
        else:
            QMessageBox.warning(self, "❌ Hata", "Şifre yanlış!"); self.sifre_input.clear(); self.sifre_input.setFocus()

class DepoCikisPage(BasePage):
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.s = get_modern_style(theme)
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
    
    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout(); title_section = QVBoxLayout(); title_section.setSpacing(4)
        title_row = QHBoxLayout(); icon = QLabel("📤"); icon.setStyleSheet("font-size: 28px;"); title_row.addWidget(icon)
        title = QLabel("Depo Çıkış İşlemleri"); title.setStyleSheet(f"color: {s['text']}; font-size: 24px; font-weight: 600;"); title_row.addWidget(title); title_row.addStretch()
        title_section.addLayout(title_row)
        subtitle = QLabel("Barkod okutma veya manuel malzeme çıkışı"); subtitle.setStyleSheet(f"color: {s['text_secondary']}; font-size: 13px;"); title_section.addWidget(subtitle)
        header.addLayout(title_section); header.addStretch()
        self.stat_label = QLabel(""); self.stat_label.setStyleSheet(f"color: {s['text_muted']}; font-size: 13px; padding: 8px 16px; background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 8px;"); header.addWidget(self.stat_label)
        toplu_yazdir_btn = QPushButton("🖨️ Toplu Yazdır"); toplu_yazdir_btn.setCursor(Qt.PointingHandCursor)
        toplu_yazdir_btn.setStyleSheet(f"QPushButton {{ background: {s['info']}; color: white; border: none; border-radius: 8px; padding: 10px 18px; font-weight: 600; }} QPushButton:hover {{ background: #2563EB; }}")
        toplu_yazdir_btn.clicked.connect(self._toplu_yazdir); header.addWidget(toplu_yazdir_btn)
        refresh_btn = QPushButton("🔄"); refresh_btn.setStyleSheet(f"QPushButton {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px 14px; }}"); refresh_btn.clicked.connect(self._load_data); header.addWidget(refresh_btn)
        layout.addLayout(header)
        
        # Barkod okutma alanı
        barkod_frame = QFrame(); barkod_frame.setStyleSheet(f"QFrame {{ background: {s['card_bg']}; border: 2px solid {s['info']}; border-radius: 12px; padding: 16px; }}")
        barkod_layout = QHBoxLayout(barkod_frame)
        barkod_icon = QLabel("📷"); barkod_icon.setStyleSheet("font-size: 32px;"); barkod_layout.addWidget(barkod_icon)
        barkod_input_layout = QVBoxLayout()
        barkod_label = QLabel("Lot Barkodu Okutun:"); barkod_label.setStyleSheet(f"color: {s['text']}; font-weight: 600;"); barkod_input_layout.addWidget(barkod_label)
        self.barkod_input = QLineEdit(); self.barkod_input.setPlaceholderText("Barkod okutun veya lot no girin...")
        self.barkod_input.setStyleSheet(f"QLineEdit {{ background: {s['input_bg']}; border: 2px solid {s['border']}; border-radius: 8px; padding: 12px; color: {s['text']}; font-size: 16px; }} QLineEdit:focus {{ border-color: {s['info']}; }}")
        self.barkod_input.returnPressed.connect(self._process_barkod); barkod_input_layout.addWidget(self.barkod_input)
        barkod_layout.addLayout(barkod_input_layout, 1)
        layout.addWidget(barkod_frame)
        
        # Filtreler
        filter_layout = QHBoxLayout(); filter_layout.setSpacing(12)
        durum_label = QLabel("Durum:"); durum_label.setStyleSheet(f"color: {s['text']};"); filter_layout.addWidget(durum_label)
        self.durum_filter = QComboBox(); self.durum_filter.setStyleSheet(f"QComboBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; min-width: 140px; }}")
        self.durum_filter.addItem("Tüm Durumlar", None); self.durum_filter.addItem("🟡 Bekliyor", "BEKLIYOR"); self.durum_filter.addItem("🟢 Tamamlandı", "TAMAMLANDI")
        self.durum_filter.currentIndexChanged.connect(self._load_data); filter_layout.addWidget(self.durum_filter)
        
        depo_label = QLabel("Hedef Depo:"); depo_label.setStyleSheet(f"color: {s['text']};"); filter_layout.addWidget(depo_label)
        self.depo_filter = QComboBox(); self.depo_filter.setStyleSheet(f"QComboBox {{ background: {s['input_bg']}; border: 1px solid {s['border']}; border-radius: 8px; padding: 10px; color: {s['text']}; min-width: 160px; }}")
        self.depo_filter.addItem("Tüm Depolar", None); self._load_depolar()
        self.depo_filter.currentIndexChanged.connect(self._load_data); filter_layout.addWidget(self.depo_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setStyleSheet(f"QTableWidget {{ background: {s['card_bg']}; border: 1px solid {s['border']}; border-radius: 10px; gridline-color: {s['border']}; color: {s['text']}; }} QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {s['border']}; }} QTableWidget::item:selected {{ background: {s['primary']}; }} QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {s['text_secondary']}; padding: 12px 8px; border: none; border-bottom: 2px solid {s['primary']}; font-weight: 600; font-size: 12px; text-transform: uppercase; }}")
        self.table.setColumnCount(10); self.table.setHorizontalHeaderLabels(["ID", "Emir No", "Lot No", "Stok Kodu", "Stok Adı", "Miktar", "Hedef Depo", "Oluşturma", "Durum", "İşlem"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 100); self.table.setColumnWidth(2, 140); self.table.setColumnWidth(3, 100); self.table.setColumnWidth(5, 80); self.table.setColumnWidth(6, 120); self.table.setColumnWidth(7, 100); self.table.setColumnWidth(8, 100); self.table.setColumnWidth(9, 160)
        self.table.verticalHeader().setVisible(False); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setSelectionMode(QAbstractItemView.ExtendedSelection); self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)
    
    def _load_depolar(self):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.depolar WHERE aktif_mi = 1 AND kod LIKE 'URT-%' ORDER BY kod")
            for row in cursor.fetchall(): self.depo_filter.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()
        except Exception: pass
    
    def _load_data(self):
        s = self.s
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            durum = self.durum_filter.currentData(); depo_id = self.depo_filter.currentData()
            query = """SELECT e.id, e.emir_no, e.lot_no, e.stok_kodu, e.stok_adi, e.talep_miktar, d.kod + ' - ' + d.ad, FORMAT(e.olusturma_tarihi, 'dd.MM.yyyy'), e.durum
                FROM stok.depo_cikis_emirleri e
                LEFT JOIN tanim.depolar d ON e.hedef_depo_id = d.id WHERE 1=1"""
            params = []
            if durum: query += " AND e.durum = ?"; params.append(durum)
            if depo_id: query += " AND e.hedef_depo_id = ?"; params.append(depo_id)
            query += " ORDER BY e.olusturma_tarihi DESC"
            cursor.execute(query, params); rows = cursor.fetchall(); conn.close()
            
            self.table.setRowCount(len(rows)); bekleyen = 0
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val) if val else "")
                    if j == 8:
                        if val == 'BEKLIYOR': item.setForeground(QColor(s['warning'])); bekleyen += 1
                        elif val == 'TAMAMLANDI': item.setForeground(QColor(s['success']))
                    self.table.setItem(i, j, item)
                
                btns = []
                if row[8] == 'BEKLIYOR':
                    btns.append(("", "Çıkış Yap", lambda _, eid=row[0]: self._manuel_cikis(eid), "warning"))
                btns.append(("", "Yazdır", lambda _, eid=row[0]: self._yazdir_depo_cikis(eid), "print"))
                btn_widget = self.create_action_buttons(btns)
                self.table.setCellWidget(i, 9, btn_widget)
                self.table.setRowHeight(i, 48)
            self.stat_label.setText(f"📊 Toplam: {len(rows)} | Bekleyen: {bekleyen}")
        except Exception as e: QMessageBox.warning(self, "❌ Hata", str(e))
    
    def _process_barkod(self):
        barkod = self.barkod_input.text().strip()
        if not barkod: return
        self.barkod_input.clear()
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""SELECT e.id, e.emir_no, e.lot_no, e.stok_adi, e.talep_miktar, e.hedef_depo_id, e.durum 
                FROM stok.depo_cikis_emirleri e INNER JOIN stok.stok_bakiye sb ON e.lot_no = sb.lot_no
                WHERE (e.lot_no = ? OR e.emir_no = ?) AND e.durum = 'BEKLIYOR' AND sb.durum_kodu = 'PLANLANDI'""", (barkod, barkod))
            row = cursor.fetchone(); conn.close()
            if row:
                emir_data = {'id': row[0], 'emir_no': row[1], 'lot_no': row[2], 'stok_adi': row[3], 'talep_miktar': row[4], 'hedef_depo_id': row[5], 'durum': row[6]}
                self._do_cikis(emir_data, manuel=False)
            else: QMessageBox.warning(self, "⚠️ Bulunamadı", f"'{barkod}' için bekleyen çıkış emri bulunamadı!")
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
        self.barkod_input.setFocus()
    
    def _manuel_cikis(self, emir_id: int):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute("""SELECT e.id, e.emir_no, e.lot_no, e.stok_adi, e.talep_miktar, e.hedef_depo_id, e.durum 
                FROM stok.depo_cikis_emirleri e INNER JOIN stok.stok_bakiye sb ON e.lot_no = sb.lot_no
                WHERE e.id = ? AND sb.durum_kodu = 'PLANLANDI'""", (emir_id,))
            row = cursor.fetchone(); conn.close()
            if row:
                emir_data = {'id': row[0], 'emir_no': row[1], 'lot_no': row[2], 'stok_adi': row[3], 'talep_miktar': row[4], 'hedef_depo_id': row[5], 'durum': row[6]}
                dlg = ManuelCikisDialog(emir_data, self.theme, self)
                if dlg.exec() == QDialog.Accepted and dlg.onaylandi: self._do_cikis(emir_data, manuel=True)
        except Exception as e: QMessageBox.critical(self, "❌ Hata", str(e))
    
    def _toplu_yazdir(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "⚠️ Uyarı", "Yazdırmak için tablodan satır seçin.\n(Ctrl+tıklama ile çoklu seçim yapabilirsiniz)")
            return
        emir_ids = []
        for idx in selected_rows:
            item = self.table.item(idx.row(), 0)
            if item:
                emir_ids.append(int(item.text()))
        if not emir_ids:
            return
        cevap = QMessageBox.question(self, "🖨️ Toplu Yazdır",
            f"{len(emir_ids)} adet depo çıkış emri yazdırılacak.\nDevam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if cevap != QMessageBox.Yes:
            return
        try:
            from utils.depo_cikis_pdf import depo_cikis_pdf_olustur
            for eid in emir_ids:
                depo_cikis_pdf_olustur(eid)
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", f"PDF oluşturma hatası:\n{e}")

    def _yazdir_depo_cikis(self, emir_id: int):
        try:
            from utils.depo_cikis_pdf import depo_cikis_pdf_olustur
            depo_cikis_pdf_olustur(emir_id)
        except Exception as e:
            QMessageBox.critical(self, "❌ Hata", f"PDF oluşturma hatası:\n{e}")

    def _do_cikis(self, emir_data: dict, manuel: bool = False):
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            from core.hareket_motoru import HareketMotoru
            motor = HareketMotoru(conn)
            emir_id = emir_data['id']; lot_no = emir_data['lot_no']; miktar = emir_data['talep_miktar']; hedef_depo_id = emir_data['hedef_depo_id']
            motor.rezerve_iptal(lot_no, miktar)
            transfer_sonuc = motor.transfer(lot_no=lot_no, hedef_depo_id=hedef_depo_id, miktar=None, kaynak="DEPO_CIKIS", kaynak_id=emir_id, aciklama=f"Depo çıkış emri: {emir_data.get('emir_no', '')}", durum_kodu='URETIMDE')
            if not transfer_sonuc.basarili: raise Exception(f"Transfer başarısız: {transfer_sonuc.mesaj or transfer_sonuc.hata}")
            cursor.execute("UPDATE stok.depo_cikis_emirleri SET durum = 'TAMAMLANDI', transfer_miktar = ?, tamamlanma_tarihi = GETDATE(), guncelleme_tarihi = GETDATE() WHERE id = ?", (miktar, emir_id))
            cursor.execute("UPDATE siparis.is_emirleri SET durum = 'URETIMDE', guncelleme_tarihi = GETDATE() WHERE id = (SELECT is_emri_id FROM stok.depo_cikis_emirleri WHERE id = ?) AND durum = 'PLANLANDI'", (emir_id,))
            conn.commit(); conn.close()
            LogManager.log_update('depo', 'siparis.is_emirleri', None, 'Durum guncellendi')
            try:
                conn2 = get_db_connection(); cursor2 = conn2.cursor()
                cursor2.execute("SELECT kod, ad FROM tanim.depolar WHERE id = ?", (hedef_depo_id,))
                depo_row = cursor2.fetchone(); depo_adi = f"{depo_row[0]} - {depo_row[1]}" if depo_row else f"ID: {hedef_depo_id}"; conn2.close()
            except Exception: depo_adi = f"ID: {hedef_depo_id}"
            cikis_tipi = 'MANUEL' if manuel else 'BARKOD'
            QMessageBox.information(self, "✓ Çıkış Tamamlandı", f"Lot: {lot_no}\nMiktar: {miktar:,.0f}\nHedef Depo: {depo_adi}\n\nÇıkış Tipi: {cikis_tipi}")
            self._load_data()
        except Exception as e:
            import traceback; traceback.print_exc()
            QMessageBox.critical(self, "❌ Hata", f"Çıkış hatası: {e}")
