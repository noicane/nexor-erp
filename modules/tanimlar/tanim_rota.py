# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Rota Tanım Ekranı
Üretim rotalarının tanımlanması ve adım yönetimi
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QDialog, QComboBox,
    QSpinBox, QFormLayout, QColorDialog, QWidget, QSplitter,
    QTextEdit, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from components.base_page import BasePage
from core.database import get_db_connection


class RotaAdimDialog(QDialog):
    """Rota adımı ekleme/düzenleme"""
    
    def __init__(self, theme: dict, rota_id: int, adim_data: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.rota_id = rota_id
        self.adim_data = adim_data or {}
        self.is_edit = bool(adim_data)
        
        self.setWindowTitle("Adım Düzenle" if self.is_edit else "Yeni Adım")
        self.setMinimumSize(450, 380)
        self._setup_ui()
        if self.is_edit:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QComboBox, QSpinBox {{ background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px; color: {self.theme.get('text')}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.proses_combo = QComboBox()
        self._load_prosesler()
        form.addRow("Proses *:", self.proses_combo)
        
        self.sira_input = QSpinBox()
        self.sira_input.setRange(1, 99)
        self.sira_input.setValue(1)
        form.addRow("Sıra No *:", self.sira_input)
        
        self.giris_depo_combo = QComboBox()
        self.giris_depo_combo.addItem("-- Proses Varsayılanı --", None)
        self._load_depolar(self.giris_depo_combo)
        form.addRow("Giriş Depo:", self.giris_depo_combo)
        
        self.cikis_depo_combo = QComboBox()
        self.cikis_depo_combo.addItem("-- Proses Varsayılanı --", None)
        self._load_depolar(self.cikis_depo_combo)
        form.addRow("Çıkış Depo:", self.cikis_depo_combo)
        
        self.ara_kalite_check = QCheckBox("Ara kalite kontrol")
        self.ara_kalite_check.setStyleSheet(f"color: {self.theme.get('text')};")
        form.addRow("", self.ara_kalite_check)
        
        self.final_check = QCheckBox("Final (son) adım")
        self.final_check.setStyleSheet(f"color: {self.theme.get('text')};")
        form.addRow("", self.final_check)
        
        self.bekleme_input = QSpinBox()
        self.bekleme_input.setRange(0, 9999)
        self.bekleme_input.setSuffix(" dk")
        form.addRow("Min Bekleme:", self.bekleme_input)
        
        layout.addLayout(form)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 20px;")
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)
        
        kaydet_btn = QPushButton("💾 Kaydet")
        kaydet_btn.setStyleSheet(f"background: {self.theme.get('success')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        kaydet_btn.clicked.connect(self._save)
        btn_layout.addWidget(kaydet_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_prosesler(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.prosesler WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no")
            for r in cursor.fetchall():
                self.proses_combo.addItem(f"{r[1]} - {r[2]}", r[0])
            conn.close()
        except Exception:
            pass
    
    def _load_depolar(self, combo):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, kod, ad FROM tanim.depolar WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY kod")
            for r in cursor.fetchall():
                combo.addItem(f"{r[1]} - {r[2]}", r[0])
            conn.close()
        except Exception:
            pass
    
    def _load_data(self):
        pid = self.adim_data.get('proses_id')
        for i in range(self.proses_combo.count()):
            if self.proses_combo.itemData(i) == pid:
                self.proses_combo.setCurrentIndex(i)
                break
        self.sira_input.setValue(self.adim_data.get('sira_no', 1) or 1)
        
        gid = self.adim_data.get('giris_depo_id')
        if gid:
            for i in range(self.giris_depo_combo.count()):
                if self.giris_depo_combo.itemData(i) == gid:
                    self.giris_depo_combo.setCurrentIndex(i)
                    break
        
        cid = self.adim_data.get('cikis_depo_id')
        if cid:
            for i in range(self.cikis_depo_combo.count()):
                if self.cikis_depo_combo.itemData(i) == cid:
                    self.cikis_depo_combo.setCurrentIndex(i)
                    break
        
        self.ara_kalite_check.setChecked(bool(self.adim_data.get('ara_kalite_kontrol')))
        self.final_check.setChecked(bool(self.adim_data.get('final_adim_mi')))
        self.bekleme_input.setValue(self.adim_data.get('min_bekleme_dk', 0) or 0)
    
    def _save(self):
        if not self.proses_combo.currentData():
            QMessageBox.warning(self, "Uyarı", "Proses seçin!")
            return
        self.result_data = {
            'proses_id': self.proses_combo.currentData(),
            'sira_no': self.sira_input.value(),
            'giris_depo_id': self.giris_depo_combo.currentData(),
            'cikis_depo_id': self.cikis_depo_combo.currentData(),
            'ara_kalite_kontrol': self.ara_kalite_check.isChecked(),
            'final_adim_mi': self.final_check.isChecked(),
            'min_bekleme_dk': self.bekleme_input.value()
        }
        self.accept()


class RotaDialog(QDialog):
    """Rota ekleme/düzenleme"""
    
    def __init__(self, theme: dict, rota_data: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.rota_data = rota_data or {}
        self.is_edit = bool(rota_data)
        
        self.setWindowTitle("Rota Düzenle" if self.is_edit else "Yeni Rota")
        self.setMinimumSize(400, 300)
        self._setup_ui()
        if self.is_edit:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main')}; }}
            QLabel {{ color: {self.theme.get('text')}; }}
            QLineEdit, QTextEdit, QSpinBox {{ background: {self.theme.get('bg_input')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 8px; color: {self.theme.get('text')}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.kod_input = QLineEdit()
        self.kod_input.setPlaceholderText("Örn: KTL-TOZ")
        form.addRow("Kod *:", self.kod_input)
        
        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderText("Örn: Kataforez + Toz Boya")
        form.addRow("Ad *:", self.ad_input)
        
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setMaximumHeight(60)
        form.addRow("Açıklama:", self.aciklama_input)
        
        renk_layout = QHBoxLayout()
        self.renk_btn = QPushButton()
        self.renk_btn.setFixedSize(40, 28)
        self.renk_kodu = "#22c55e"
        self._update_renk()
        self.renk_btn.clicked.connect(self._pick_color)
        renk_layout.addWidget(self.renk_btn)
        renk_layout.addStretch()
        form.addRow("Renk:", renk_layout)
        
        self.sira_input = QSpinBox()
        self.sira_input.setRange(0, 999)
        form.addRow("Sıra:", self.sira_input)
        
        layout.addLayout(form)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 20px;")
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)
        
        kaydet_btn = QPushButton("💾 Kaydet")
        kaydet_btn.setStyleSheet(f"background: {self.theme.get('success')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        kaydet_btn.clicked.connect(self._save)
        btn_layout.addWidget(kaydet_btn)
        
        layout.addLayout(btn_layout)
    
    def _update_renk(self):
        self.renk_btn.setStyleSheet(f"background: {self.renk_kodu}; border: 1px solid #fff; border-radius: 4px;")
    
    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self.renk_kodu), self)
        if c.isValid():
            self.renk_kodu = c.name()
            self._update_renk()
    
    def _load_data(self):
        self.kod_input.setText(self.rota_data.get('kod', ''))
        self.ad_input.setText(self.rota_data.get('ad', ''))
        self.aciklama_input.setPlainText(self.rota_data.get('aciklama', '') or '')
        self.renk_kodu = self.rota_data.get('renk_kodu', '#22c55e') or '#22c55e'
        self._update_renk()
        self.sira_input.setValue(self.rota_data.get('sira_no', 0) or 0)
    
    def _save(self):
        kod = self.kod_input.text().strip().upper()
        ad = self.ad_input.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad zorunlu!")
            return
        self.result_data = {
            'kod': kod,
            'ad': ad,
            'aciklama': self.aciklama_input.toPlainText().strip() or None,
            'renk_kodu': self.renk_kodu,
            'sira_no': self.sira_input.value()
        }
        self.accept()


class TanimRotaPage(BasePage):
    """Rota Tanım Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.secili_rota_id = None
        self._setup_ui()
        QTimer.singleShot(100, self._load_rotalar)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("🔄 Rota Tanımları")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text')};")
        header.addWidget(title)
        header.addStretch()
        
        yeni_btn = QPushButton("➕ Yeni Rota")
        yeni_btn.setStyleSheet(f"background: {self.theme.get('success')}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        yeni_btn.clicked.connect(self._yeni_rota)
        header.addWidget(yeni_btn)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setStyleSheet(f"background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; padding: 10px 14px;")
        refresh_btn.clicked.connect(self._load_rotalar)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: #3d4454; width: 3px; }")
        
        # Sol - Rotalar
        sol = QWidget()
        sol_layout = QVBoxLayout(sol)
        sol_layout.setContentsMargins(0, 0, 0, 0)
        
        sol_layout.addWidget(QLabel("📋 Rotalar"))
        
        self.rota_table = QTableWidget()
        self.rota_table.setColumnCount(6)
        self.rota_table.setHorizontalHeaderLabels(["ID", "Kod", "Ad", "Adım", "Süre", "İşlem"])
        self.rota_table.setColumnHidden(0, True)
        self._style_table(self.rota_table)
        self.rota_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rota_table.setColumnWidth(5, 170)
        self.rota_table.itemSelectionChanged.connect(self._on_rota_select)
        sol_layout.addWidget(self.rota_table)
        
        splitter.addWidget(sol)
        
        # Sağ - Adımlar
        sag = QWidget()
        sag_layout = QVBoxLayout(sag)
        sag_layout.setContentsMargins(0, 0, 0, 0)
        
        sag_header = QHBoxLayout()
        self.adim_title = QLabel("📌 Adımlar")
        sag_header.addWidget(self.adim_title)
        sag_header.addStretch()
        
        self.adim_ekle_btn = QPushButton("➕ Adım")
        self.adim_ekle_btn.setEnabled(False)
        self.adim_ekle_btn.setStyleSheet(f"background: {self.theme.get('primary')}; color: white; border: none; border-radius: 4px; padding: 6px 12px;")
        self.adim_ekle_btn.clicked.connect(self._yeni_adim)
        sag_header.addWidget(self.adim_ekle_btn)
        
        sag_layout.addLayout(sag_header)
        
        self.adim_table = QTableWidget()
        self.adim_table.setColumnCount(8)
        self.adim_table.setHorizontalHeaderLabels(["ID", "Sıra", "Proses", "Hat", "Çıkış", "AraKK", "Final", "İşlem"])
        self.adim_table.setColumnHidden(0, True)
        self._style_table(self.adim_table)
        self.adim_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.adim_table.setColumnWidth(7, 90)
        sag_layout.addWidget(self.adim_table)
        
        splitter.addWidget(sag)
        splitter.setSizes([350, 500])
        
        layout.addWidget(splitter, 1)
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px;")
        layout.addWidget(self.info_label)
    
    def _style_table(self, t):
        t.setStyleSheet(f"""
            QTableWidget {{ background: {self.theme.get('bg_card')}; color: {self.theme.get('text')}; border: 1px solid {self.theme.get('border')}; border-radius: 6px; gridline-color: {self.theme.get('border')}; }}
            QTableWidget::item {{ padding: 6px; }}
            QHeaderView::section {{ background: {self.theme.get('bg_input')}; color: {self.theme.get('text')}; padding: 8px; border: none; font-weight: bold; }}
        """)
        t.verticalHeader().setVisible(False)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setAlternatingRowColors(True)
    
    def _load_rotalar(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, kod, ad, adim_sayisi, toplam_sure_dk, renk_kodu, sira_no, aciklama
                FROM tanim.rotalar WHERE aktif_mi=1 AND silindi_mi=0 ORDER BY sira_no, kod
            """)
            rows = cursor.fetchall()
            conn.close()
            
            self.rota_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.rota_table.setItem(i, 0, QTableWidgetItem(str(r[0])))
                
                kod_item = QTableWidgetItem(r[1])
                kod_item.setForeground(QColor(r[5] or '#22c55e'))
                kod_item.setFont(QFont("", -1, QFont.Bold))
                self.rota_table.setItem(i, 1, kod_item)
                
                self.rota_table.setItem(i, 2, QTableWidgetItem(r[2] or ''))
                
                adim_item = QTableWidgetItem(str(r[3] or 0))
                adim_item.setTextAlignment(Qt.AlignCenter)
                self.rota_table.setItem(i, 3, adim_item)
                
                sure_item = QTableWidgetItem(f"{r[4] or 0} dk")
                sure_item.setTextAlignment(Qt.AlignCenter)
                self.rota_table.setItem(i, 4, sure_item)
                
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, row=r: self._edit_rota(row), "edit"),
                    ("🗑️", "Sil", lambda checked, rid=r[0], rkod=r[1]: self._delete_rota(rid, rkod), "delete"),
                ])
                self.rota_table.setCellWidget(i, 5, widget)
                self.rota_table.setRowHeight(i, 36)
            
            self.info_label.setText(f"Toplam {len(rows)} rota")
            
            if self.secili_rota_id:
                for i in range(self.rota_table.rowCount()):
                    if int(self.rota_table.item(i, 0).text()) == self.secili_rota_id:
                        self.rota_table.selectRow(i)
                        break
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _on_rota_select(self):
        sel = self.rota_table.selectedItems()
        if sel:
            self.secili_rota_id = int(self.rota_table.item(sel[0].row(), 0).text())
            kod = self.rota_table.item(sel[0].row(), 1).text()
            self.adim_title.setText(f"📌 {kod} Adımları")
            self.adim_ekle_btn.setEnabled(True)
            self._load_adimlar()
        else:
            self.secili_rota_id = None
            self.adim_title.setText("📌 Adımlar")
            self.adim_ekle_btn.setEnabled(False)
            self.adim_table.setRowCount(0)
    
    def _load_adimlar(self):
        if not self.secili_rota_id:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ra.id, ra.sira_no, p.kod, p.ad, h.kod, 
                       COALESCE(cd.kod, pcd.kod), ra.ara_kalite_kontrol, ra.final_adim_mi,
                       ra.proses_id, ra.giris_depo_id, ra.cikis_depo_id, ra.min_bekleme_dk
                FROM tanim.rota_adimlar ra
                JOIN tanim.prosesler p ON ra.proses_id = p.id
                LEFT JOIN tanim.uretim_hatlari h ON p.hat_id = h.id
                LEFT JOIN tanim.depolar cd ON ra.cikis_depo_id = cd.id
                LEFT JOIN tanim.depolar pcd ON p.cikis_depo_id = pcd.id
                WHERE ra.rota_id = ? AND ra.aktif_mi = 1
                ORDER BY ra.sira_no
            """, (self.secili_rota_id,))
            rows = cursor.fetchall()
            conn.close()
            
            self.adim_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.adim_table.setItem(i, 0, QTableWidgetItem(str(r[0])))
                
                sira = QTableWidgetItem(str(r[1]))
                sira.setTextAlignment(Qt.AlignCenter)
                sira.setFont(QFont("", -1, QFont.Bold))
                self.adim_table.setItem(i, 1, sira)
                
                proses = QTableWidgetItem(f"{r[2]} - {r[3]}")
                proses.setForeground(QColor(self.theme.get('primary')))
                self.adim_table.setItem(i, 2, proses)
                
                self.adim_table.setItem(i, 3, QTableWidgetItem(r[4] or '-'))
                self.adim_table.setItem(i, 4, QTableWidgetItem(r[5] or '-'))
                
                ara = QTableWidgetItem("✓" if r[6] else "-")
                ara.setTextAlignment(Qt.AlignCenter)
                self.adim_table.setItem(i, 5, ara)
                
                final = QTableWidgetItem("✓" if r[7] else "-")
                final.setTextAlignment(Qt.AlignCenter)
                if r[7]:
                    final.setForeground(QColor(self.theme.get('success')))
                self.adim_table.setItem(i, 6, final)
                
                widget = self.create_action_buttons([
                    ("✏️", "Düzenle", lambda checked, row=r: self._edit_adim(row), "edit"),
                    ("🗑️", "Sil", lambda checked, aid=r[0]: self._delete_adim(aid), "delete"),
                ])
                self.adim_table.setCellWidget(i, 7, widget)
                self.adim_table.setRowHeight(i, 32)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _yeni_rota(self):
        dlg = RotaDialog(self.theme, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._save_rota(dlg.result_data)
    
    def _edit_rota(self, row):
        data = {'id': row[0], 'kod': row[1], 'ad': row[2], 'adim_sayisi': row[3], 'toplam_sure_dk': row[4], 'renk_kodu': row[5], 'sira_no': row[6], 'aciklama': row[7]}
        dlg = RotaDialog(self.theme, data, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._save_rota(dlg.result_data, data['id'])
    
    def _save_rota(self, data, rota_id=None):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if rota_id:
                cursor.execute("UPDATE tanim.rotalar SET kod=?, ad=?, aciklama=?, renk_kodu=?, sira_no=?, guncelleme_tarihi=GETDATE() WHERE id=?",
                               (data['kod'], data['ad'], data['aciklama'], data['renk_kodu'], data['sira_no'], rota_id))
            else:
                cursor.execute("INSERT INTO tanim.rotalar (kod, ad, aciklama, renk_kodu, sira_no, adim_sayisi, toplam_sure_dk) VALUES (?,?,?,?,?,0,0)",
                               (data['kod'], data['ad'], data['aciklama'], data['renk_kodu'], data['sira_no']))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "✓", "Rota kaydedildi!")
            self._load_rotalar()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _delete_rota(self, rota_id, rota_kod):
        if QMessageBox.question(self, "Sil?", f"'{rota_kod}' silinsin mi?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM stok.urunler WHERE varsayilan_hat_id IN (SELECT hat_id FROM tanim.rota_adimlar WHERE rota_id=?) AND silindi_mi=0", (rota_id,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Uyarı", "Bu rota ürünlerde kullanılıyor!")
                    conn.close()
                    return
                cursor.execute("UPDATE tanim.rota_adimlar SET aktif_mi=0 WHERE rota_id=?", (rota_id,))
                cursor.execute("UPDATE tanim.rotalar SET silindi_mi=1 WHERE id=?", (rota_id,))
                conn.commit()
                conn.close()
                self.secili_rota_id = None
                self._load_rotalar()
                self.adim_table.setRowCount(0)
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
    
    def _yeni_adim(self):
        if not self.secili_rota_id:
            return
        dlg = RotaAdimDialog(self.theme, self.secili_rota_id, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._save_adim(dlg.result_data)
    
    def _edit_adim(self, row):
        data = {'id': row[0], 'sira_no': row[1], 'proses_id': row[8], 'giris_depo_id': row[9], 'cikis_depo_id': row[10], 'ara_kalite_kontrol': row[6], 'final_adim_mi': row[7], 'min_bekleme_dk': row[11]}
        dlg = RotaAdimDialog(self.theme, self.secili_rota_id, data, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._save_adim(dlg.result_data, data['id'])
    
    def _save_adim(self, data, adim_id=None):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if adim_id:
                cursor.execute("""
                    UPDATE tanim.rota_adimlar SET proses_id=?, sira_no=?, giris_depo_id=?, cikis_depo_id=?, 
                    ara_kalite_kontrol=?, final_adim_mi=?, min_bekleme_dk=? WHERE id=?
                """, (data['proses_id'], data['sira_no'], data['giris_depo_id'], data['cikis_depo_id'],
                      data['ara_kalite_kontrol'], data['final_adim_mi'], data['min_bekleme_dk'], adim_id))
            else:
                cursor.execute("""
                    INSERT INTO tanim.rota_adimlar (rota_id, proses_id, sira_no, giris_depo_id, cikis_depo_id,
                    ara_kalite_kontrol, final_adim_mi, min_bekleme_dk) VALUES (?,?,?,?,?,?,?,?)
                """, (self.secili_rota_id, data['proses_id'], data['sira_no'], data['giris_depo_id'],
                      data['cikis_depo_id'], data['ara_kalite_kontrol'], data['final_adim_mi'], data['min_bekleme_dk']))
            
            # Rota istatistiklerini güncelle
            cursor.execute("""
                UPDATE tanim.rotalar SET 
                    adim_sayisi = (SELECT COUNT(*) FROM tanim.rota_adimlar WHERE rota_id=? AND aktif_mi=1),
                    toplam_sure_dk = (SELECT ISNULL(SUM(p.standart_sure_dk),0) FROM tanim.rota_adimlar ra 
                                      JOIN tanim.prosesler p ON ra.proses_id=p.id WHERE ra.rota_id=? AND ra.aktif_mi=1)
                WHERE id=?
            """, (self.secili_rota_id, self.secili_rota_id, self.secili_rota_id))
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "✓", "Adım kaydedildi!")
            self._load_adimlar()
            self._load_rotalar()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _delete_adim(self, adim_id):
        if QMessageBox.question(self, "Sil?", "Bu adım silinsin mi?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE tanim.rota_adimlar SET aktif_mi=0 WHERE id=?", (adim_id,))
                cursor.execute("""
                    UPDATE tanim.rotalar SET 
                        adim_sayisi = (SELECT COUNT(*) FROM tanim.rota_adimlar WHERE rota_id=? AND aktif_mi=1),
                        toplam_sure_dk = (SELECT ISNULL(SUM(p.standart_sure_dk),0) FROM tanim.rota_adimlar ra 
                                          JOIN tanim.prosesler p ON ra.proses_id=p.id WHERE ra.rota_id=? AND ra.aktif_mi=1)
                    WHERE id=?
                """, (self.secili_rota_id, self.secili_rota_id, self.secili_rota_id))
                conn.commit()
                conn.close()
                self._load_adimlar()
                self._load_rotalar()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
