# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Cari Yetkililer Yönetimi
musteri.cari_yetkililer tablosu üzerinden iletişim kişileri yönetimi

Tablo: musteri.cari_yetkililer
- id, uuid, cari_id, ad_soyad, unvan, departman
- telefon, cep_telefon, dahili, email
- birincil_yetkili_mi, aktif_mi
- olusturma_tarihi, guncelleme_tarihi
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QCheckBox, QDialogButtonBox, QListWidget, QListWidgetItem,
    QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.log_manager import LogManager
from core.nexor_brand import brand
import os
import uuid


class YetkiliDialog(QDialog):
    """Yetkili Ekleme/Düzenleme Dialog"""
    
    def __init__(self, theme: dict, cari_id: int, yetkili_data: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.cari_id = cari_id
        self.yetkili_data = yetkili_data or {}
        self.is_edit = bool(yetkili_data)
        
        self.setWindowTitle("Yetkili Düzenle" if self.is_edit else "Yeni Yetkili")
        self.setMinimumWidth(450)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QComboBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px;
                padding: 8px;
                color: {brand.TEXT};
            }}
            QCheckBox {{ color: {brand.TEXT}; }}
        """)
        
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Ad Soyad
        self.txt_ad_soyad = QLineEdit()
        self.txt_ad_soyad.setText(self.yetkili_data.get('ad_soyad', ''))
        self.txt_ad_soyad.setPlaceholderText("Ad Soyad")
        layout.addRow("Ad Soyad *:", self.txt_ad_soyad)
        
        # Ünvan
        self.txt_unvan = QLineEdit()
        self.txt_unvan.setText(self.yetkili_data.get('unvan', ''))
        self.txt_unvan.setPlaceholderText("Örn: Satın Alma Müdürü")
        layout.addRow("Ünvan:", self.txt_unvan)
        
        # Departman
        self.cmb_departman = QComboBox()
        self.cmb_departman.setEditable(True)
        self.cmb_departman.addItems(["", "Satın Alma", "Kalite", "Üretim", "Muhasebe", "Sevkiyat", "Genel Müdürlük", "Teknik", "Diğer"])
        if self.yetkili_data.get('departman'):
            self.cmb_departman.setCurrentText(self.yetkili_data['departman'])
        layout.addRow("Departman:", self.cmb_departman)
        
        # Telefon
        self.txt_telefon = QLineEdit()
        self.txt_telefon.setText(self.yetkili_data.get('telefon', ''))
        self.txt_telefon.setPlaceholderText("Sabit telefon")
        layout.addRow("Telefon:", self.txt_telefon)
        
        # Cep Telefon
        self.txt_cep = QLineEdit()
        self.txt_cep.setText(self.yetkili_data.get('cep_telefon', ''))
        self.txt_cep.setPlaceholderText("Cep telefonu")
        layout.addRow("Cep Telefon:", self.txt_cep)
        
        # Dahili
        self.txt_dahili = QLineEdit()
        self.txt_dahili.setText(self.yetkili_data.get('dahili', ''))
        self.txt_dahili.setPlaceholderText("Dahili numara")
        layout.addRow("Dahili:", self.txt_dahili)
        
        # E-posta
        self.txt_email = QLineEdit()
        self.txt_email.setText(self.yetkili_data.get('email', ''))
        self.txt_email.setPlaceholderText("E-posta adresi")
        layout.addRow("E-posta:", self.txt_email)
        
        # Varsayilan
        self.chk_varsayilan = QCheckBox("Ana iletisim kisisi")
        self.chk_varsayilan.setChecked(self.yetkili_data.get('birincil_yetkili_mi', False))
        layout.addRow("", self.chk_varsayilan)

        # FKK Mail Alacak
        self.chk_fkk_mail = QCheckBox("Final Kalite Raporlarini email ile alsin")
        self.chk_fkk_mail.setChecked(bool(self.yetkili_data.get('fkk_mail_alacak', False)))
        layout.addRow("", self.chk_fkk_mail)

        # Irsaliye Mail Alacak
        self.chk_irsaliye_mail = QCheckBox("Sevkiyat / Irsaliye email ile alsin")
        self.chk_irsaliye_mail.setChecked(bool(self.yetkili_data.get('irsaliye_mail_alacak', False)))
        layout.addRow("", self.chk_irsaliye_mail)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_iptal = QPushButton("İptal")
        btn_iptal.clicked.connect(self.reject)
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {brand.PRIMARY}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_iptal)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_kaydet)
        layout.addRow("", btn_layout)
    
    def _save(self):
        ad_soyad = self.txt_ad_soyad.text().strip()
        
        if not ad_soyad:
            QMessageBox.warning(self, "Uyarı", "Ad soyad zorunludur!")
            return
        
        self.result_data = {
            'ad_soyad': ad_soyad,
            'unvan': self.txt_unvan.text().strip() or None,
            'departman': self.cmb_departman.currentText().strip() or None,
            'telefon': self.txt_telefon.text().strip() or None,
            'cep_telefon': self.txt_cep.text().strip() or None,
            'dahili': self.txt_dahili.text().strip() or None,
            'email': self.txt_email.text().strip() or None,
            'birincil_yetkili_mi': 1 if self.chk_varsayilan.isChecked() else 0,
            'fkk_mail_alacak': 1 if self.chk_fkk_mail.isChecked() else 0,
            'irsaliye_mail_alacak': 1 if self.chk_irsaliye_mail.isChecked() else 0,
        }
        self.accept()
    
    def get_data(self):
        return getattr(self, 'result_data', {})


class CariYetkililerPage(BasePage):
    """Cari Yetkililer Yönetimi Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.selected_cari_id = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("👥 Cari Yetkililer Yönetimi")
        title.setStyleSheet(f"color: {brand.TEXT}; font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Cari Seçimi
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {brand.BG_CARD}; border-radius: 8px; padding: 12px;")
        f_layout = QHBoxLayout(filter_frame)
        
        f_layout.addWidget(QLabel("Cari Sec:"))
        self.cmb_cari = QComboBox()
        self.cmb_cari.setMinimumWidth(450)
        self.cmb_cari.setEditable(True)
        self.cmb_cari.setInsertPolicy(QComboBox.NoInsert)
        from PySide6.QtWidgets import QCompleter
        self.cmb_cari.setStyleSheet(f"background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px; color: {brand.TEXT};")
        self.cmb_cari.currentIndexChanged.connect(self._on_cari_changed)
        f_layout.addWidget(self.cmb_cari)
        f_layout.addStretch()
        
        btn_yeni = QPushButton("+ Yeni Yetkili")
        btn_yeni.setCursor(Qt.PointingHandCursor)
        btn_yeni.setStyleSheet(f"background: {brand.PRIMARY}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni_yetkili)
        f_layout.addWidget(btn_yeni)
        
        layout.addWidget(filter_frame)
        
        # Yetkili Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "ID", "Cari", "Ad Soyad", "Unvan", "Departman", "Telefon", "Cep",
            "E-posta", "Ana", "FKK Mail", "Irs Mail", "Durum", "Islem"
        ])
        self.table.setStyleSheet(self._table_style())
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(8, 50)
        self.table.setColumnWidth(9, 80)
        self.table.setColumnWidth(10, 80)
        self.table.setColumnWidth(11, 60)
        self.table.setColumnWidth(12, 170)
        self.table.doubleClicked.connect(self._duzenle_yetkili)
        layout.addWidget(self.table, 1)

        self._load_cariler()
        self._load_yetkililer()
    
    def _table_style(self):
        return f"""
            QTableWidget {{ background: {brand.BG_MAIN}; border: 1px solid {brand.BORDER}; gridline-color: {brand.BORDER}; }}
            QTableWidget::item {{ padding: 8px; color: {brand.TEXT}; }}
            QHeaderView::section {{ background: {brand.BG_CARD}; color: {brand.TEXT}; padding: 10px; border: none; border-bottom: 2px solid {brand.PRIMARY}; font-weight: bold; }}
        """
    
    def _button_style(self):
        return f"QPushButton {{ background: {brand.BG_CARD}; color: {brand.TEXT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px 16px; }} QPushButton:hover {{ background: {brand.BG_HOVER}; }}"
    
    def _load_cariler(self):
        self.cmb_cari.clear()
        self.cmb_cari.addItem("-- Cari Seciniz --", None)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, cari_kodu, unvan FROM musteri.cariler WHERE aktif_mi = 1 AND (silindi_mi = 0 OR silindi_mi IS NULL) ORDER BY unvan")
            for row in cursor.fetchall():
                self.cmb_cari.addItem(f"{row[1]} - {row[2]}", row[0])
            conn.close()

            # Arama: QCompleter ile case-insensitive contains
            from PySide6.QtWidgets import QCompleter
            from PySide6.QtCore import Qt as _Qt
            completer = QCompleter([self.cmb_cari.itemText(i) for i in range(self.cmb_cari.count())], self)
            completer.setCaseSensitivity(_Qt.CaseInsensitive)
            completer.setFilterMode(_Qt.MatchContains)
            self.cmb_cari.setCompleter(completer)
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Cariler yuklenemedi: {e}")
    
    def _on_cari_changed(self):
        self.selected_cari_id = self.cmb_cari.currentData()
        self._load_yetkililer()
    
    def _load_yetkililer(self):
        self.table.setRowCount(0)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if self.selected_cari_id:
                cursor.execute("""
                    SELECT y.id, c.unvan, y.ad_soyad, y.unvan, y.departman, y.telefon, y.cep_telefon, y.email,
                           y.birincil_yetkili_mi, ISNULL(y.fkk_mail_alacak, 0), ISNULL(y.irsaliye_mail_alacak, 0), y.aktif_mi
                    FROM musteri.cari_yetkililer y
                    INNER JOIN musteri.cariler c ON c.id = y.cari_id
                    WHERE y.cari_id = ? AND (y.silindi_mi = 0 OR y.silindi_mi IS NULL)
                    ORDER BY y.birincil_yetkili_mi DESC, y.ad_soyad
                """, (self.selected_cari_id,))
            else:
                cursor.execute("""
                    SELECT y.id, c.unvan, y.ad_soyad, y.unvan, y.departman, y.telefon, y.cep_telefon, y.email,
                           y.birincil_yetkili_mi, ISNULL(y.fkk_mail_alacak, 0), ISNULL(y.irsaliye_mail_alacak, 0), y.aktif_mi
                    FROM musteri.cari_yetkililer y
                    INNER JOIN musteri.cariler c ON c.id = y.cari_id
                    WHERE (y.silindi_mi = 0 OR y.silindi_mi IS NULL)
                      AND (c.silindi_mi = 0 OR c.silindi_mi IS NULL)
                    ORDER BY c.unvan, y.birincil_yetkili_mi DESC, y.ad_soyad
                """)

            for row in cursor.fetchall():
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(r, 1, QTableWidgetItem(row[1] or ""))
                self.table.setItem(r, 2, QTableWidgetItem(row[2] or ""))
                self.table.setItem(r, 3, QTableWidgetItem(row[3] or ""))
                self.table.setItem(r, 4, QTableWidgetItem(row[4] or ""))
                self.table.setItem(r, 5, QTableWidgetItem(row[5] or ""))
                self.table.setItem(r, 6, QTableWidgetItem(row[6] or ""))
                self.table.setItem(r, 7, QTableWidgetItem(row[7] or ""))

                varsayilan = QTableWidgetItem("*" if row[8] else "")
                varsayilan.setForeground(QColor('#f59e0b'))
                varsayilan.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, 8, varsayilan)

                fkk_mail = QTableWidgetItem("EVET" if row[9] else "")
                fkk_mail.setForeground(QColor('#22c55e') if row[9] else QColor('#666'))
                fkk_mail.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, 9, fkk_mail)

                irs_mail = QTableWidgetItem("EVET" if row[10] else "")
                irs_mail.setForeground(QColor('#22c55e') if row[10] else QColor('#666'))
                irs_mail.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, 10, irs_mail)

                durum = QTableWidgetItem("Aktif" if row[11] else "Pasif")
                durum.setForeground(QColor('#22c55e') if row[11] else QColor('#ef4444'))
                self.table.setItem(r, 11, durum)

                rid = row[0]
                widget = self.create_action_buttons([
                    ("WhatsApp", "WhatsApp ile Irsaliye PDF gonder", lambda checked, rid=rid: self._whatsapp_irsaliye_gonder(rid), "message"),
                    ("Duzenle", "Duzenle", lambda checked, rid=rid: self._duzenle_yetkili_by_id(rid), "edit"),
                    ("Sil", "Sil", lambda checked, rid=rid: self._sil_yetkili_by_id(rid), "delete"),
                ])
                self.table.setCellWidget(r, 12, widget)
                self.table.setRowHeight(r, 42)

            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Yetkililer yüklenemedi: {e}")
    
    def _yeni_yetkili(self):
        if not self.selected_cari_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir cari seçin!")
            return
        
        dialog = YetkiliDialog(self.theme, self.selected_cari_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                if data['birincil_yetkili_mi']:
                    cursor.execute("UPDATE musteri.cari_yetkililer SET birincil_yetkili_mi = 0 WHERE cari_id = ?", (self.selected_cari_id,))
                
                cursor.execute("""
                    INSERT INTO musteri.cari_yetkililer (uuid, cari_id, ad_soyad, unvan, departman, telefon, cep_telefon, dahili, email, birincil_yetkili_mi, fkk_mail_alacak, irsaliye_mail_alacak, aktif_mi, olusturma_tarihi, guncelleme_tarihi, silindi_mi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, GETDATE(), GETDATE(), 0)
                """, (str(uuid.uuid4()), self.selected_cari_id, data['ad_soyad'], data['unvan'], data['departman'], data['telefon'], data['cep_telefon'], data['dahili'], data['email'], data['birincil_yetkili_mi'], data['fkk_mail_alacak'], data['irsaliye_mail_alacak']))
                
                conn.commit()
                LogManager.log_insert('cari', 'musteri.cari_yetkililer', None, 'Yetkili eklendi')
                conn.close()
                self._load_yetkililer()
                QMessageBox.information(self, "Başarılı", "Yetkili eklendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Yetkili eklenemedi: {e}")
    
    def _duzenle_yetkili_by_id(self, yetkili_id):
        """ID ile yetkili düzenleme (satır butonundan)"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ad_soyad, unvan, departman, telefon, cep_telefon, dahili, email,
                       birincil_yetkili_mi, fkk_mail_alacak, irsaliye_mail_alacak
                FROM musteri.cari_yetkililer WHERE id = ?
            """, (yetkili_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return

            mevcut = {
                'ad_soyad': row[0], 'unvan': row[1], 'departman': row[2], 'telefon': row[3],
                'cep_telefon': row[4], 'dahili': row[5], 'email': row[6],
                'birincil_yetkili_mi': row[7],
                'fkk_mail_alacak': row[8], 'irsaliye_mail_alacak': row[9],
            }

            dialog = YetkiliDialog(self.theme, self.selected_cari_id, mevcut, self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                conn = get_db_connection()
                cursor = conn.cursor()

                if data['birincil_yetkili_mi']:
                    cursor.execute("UPDATE musteri.cari_yetkililer SET birincil_yetkili_mi = 0 WHERE cari_id = ?", (self.selected_cari_id,))

                cursor.execute("""
                    UPDATE musteri.cari_yetkililer SET
                        ad_soyad = ?, unvan = ?, departman = ?, telefon = ?, cep_telefon = ?,
                        dahili = ?, email = ?, birincil_yetkili_mi = ?,
                        fkk_mail_alacak = ?, irsaliye_mail_alacak = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (data['ad_soyad'], data['unvan'], data['departman'], data['telefon'],
                      data['cep_telefon'], data['dahili'], data['email'], data['birincil_yetkili_mi'],
                      data['fkk_mail_alacak'], data['irsaliye_mail_alacak'], yetkili_id))

                conn.commit()
                LogManager.log_update('cari', 'musteri.cari_yetkililer', None, 'Kayit guncellendi')
                conn.close()
                self._load_yetkililer()
                QMessageBox.information(self, "Başarılı", "Yetkili güncellendi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {e}")

    def _sil_yetkili_by_id(self, yetkili_id):
        """ID ile yetkili silme (satır butonundan)"""
        reply = QMessageBox.question(self, "Onay", "Bu yetkiliyi silmek istediğinize emin misiniz?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE musteri.cari_yetkililer SET silindi_mi = 1, silinme_tarihi = GETDATE() WHERE id = ?", (yetkili_id,))
                conn.commit()
                LogManager.log_delete('cari', 'musteri.cari_yetkililer', None, 'Kayit silindi (soft delete)')
                conn.close()
                self._load_yetkililer()
                QMessageBox.information(self, "Başarılı", "Yetkili silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    def _duzenle_yetkili(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyari", "Lutfen bir yetkili secin!")
            return
        yetkili_id = int(self.table.item(selected[0].row(), 0).text())
        self._duzenle_yetkili_by_id(yetkili_id)
        return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ad_soyad, unvan, departman, telefon, cep_telefon, dahili, email, birincil_yetkili_mi
                FROM musteri.cari_yetkililer WHERE id = ?
            """, (yetkili_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return

            mevcut = {
                'ad_soyad': row[0], 'unvan': row[1], 'departman': row[2], 'telefon': row[3],
                'cep_telefon': row[4], 'dahili': row[5], 'email': row[6], 'birincil_yetkili_mi': row[7]
            }

            dialog = YetkiliDialog(self.theme, self.selected_cari_id, mevcut, self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                conn = get_db_connection()
                cursor = conn.cursor()

                if data['birincil_yetkili_mi']:
                    cursor.execute("UPDATE musteri.cari_yetkililer SET birincil_yetkili_mi = 0 WHERE cari_id = ?", (self.selected_cari_id,))

                cursor.execute("""
                    UPDATE musteri.cari_yetkililer SET ad_soyad = ?, unvan = ?, departman = ?, telefon = ?, cep_telefon = ?, dahili = ?, email = ?, birincil_yetkili_mi = ?, guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (data['ad_soyad'], data['unvan'], data['departman'], data['telefon'], data['cep_telefon'], data['dahili'], data['email'], data['birincil_yetkili_mi'], yetkili_id))
                
                conn.commit()
                LogManager.log_update('cari', 'musteri.cari_yetkililer', None, 'Kayit guncellendi')
                conn.close()
                self._load_yetkililer()
                QMessageBox.information(self, "Başarılı", "Yetkili güncellendi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {e}")
    
    def _sil_yetkili(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir yetkili seçin!")
            return

        yetkili_id = int(self.table.item(selected[0].row(), 0).text())

        reply = QMessageBox.question(self, "Onay", "Bu yetkiliyi silmek istediğinize emin misiniz?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE musteri.cari_yetkililer SET silindi_mi = 1, silinme_tarihi = GETDATE() WHERE id = ?", (yetkili_id,))
                conn.commit()
                LogManager.log_delete('cari', 'musteri.cari_yetkililer', None, 'Kayit silindi (soft delete)')
                conn.close()
                self._load_yetkililer()
                QMessageBox.information(self, "Başarılı", "Yetkili silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    # ==============================================================
    # WHATSAPP ILE IRSALIYE GONDERIMI
    # ==============================================================

    def _ensure_whatsapp_log_table(self):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'whatsapp_log' AND schema_id = SCHEMA_ID('sistem'))
                BEGIN
                    CREATE TABLE sistem.whatsapp_log (
                        id BIGINT IDENTITY(1,1) PRIMARY KEY,
                        yetkili_id BIGINT NULL,
                        cari_id BIGINT NULL,
                        telefon NVARCHAR(30) NULL,
                        alici_adi NVARCHAR(200) NULL,
                        belge_tipi NVARCHAR(30) NULL,
                        belge_no NVARCHAR(50) NULL,
                        belge_ref_id BIGINT NULL,
                        dosya_adi NVARCHAR(300) NULL,
                        caption NVARCHAR(1000) NULL,
                        durum NVARCHAR(20) NOT NULL,
                        hata_mesaji NVARCHAR(2000) NULL,
                        gonderen_id BIGINT NULL,
                        gonderim_tarihi DATETIME2 NOT NULL DEFAULT SYSDATETIME()
                    )
                    CREATE INDEX IX_whatsapp_log_yetkili ON sistem.whatsapp_log(yetkili_id)
                    CREATE INDEX IX_whatsapp_log_cari ON sistem.whatsapp_log(cari_id)
                END
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[WhatsApp] Log tablo olusturulamadi: {e}")

    def _whatsapp_log_yaz(self, yetkili_id, cari_id, telefon, alici_adi,
                          belge_tipi, belge_no, belge_ref_id, dosya_adi,
                          caption, durum, hata_mesaji=None):
        try:
            from core.yetki_manager import YetkiManager
            gonderen_id = YetkiManager._current_user_id
        except Exception:
            gonderen_id = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO sistem.whatsapp_log
                    (yetkili_id, cari_id, telefon, alici_adi, belge_tipi,
                     belge_no, belge_ref_id, dosya_adi, caption, durum,
                     hata_mesaji, gonderen_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                yetkili_id, cari_id, telefon, alici_adi, belge_tipi,
                belge_no, belge_ref_id, dosya_adi,
                (caption[:1000] if caption else None),
                durum,
                (hata_mesaji[:2000] if hata_mesaji else None),
                gonderen_id,
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[WhatsApp] Log yazilamadi: {e}")

    def _yetkili_bilgileri(self, yetkili_id):
        """Yetkili + cari bilgilerini dondurur."""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT y.id, y.cari_id, y.ad_soyad, y.cep_telefon, y.telefon,
                       c.unvan
                FROM musteri.cari_yetkililer y
                LEFT JOIN musteri.cariler c ON c.id = y.cari_id
                WHERE y.id = ?
            """, (yetkili_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return {
                'id': row[0], 'cari_id': row[1], 'ad_soyad': row[2] or '',
                'cep_telefon': (row[3] or '').strip(),
                'telefon': (row[4] or '').strip(),
                'cari_unvan': row[5] or '',
            }
        except Exception as e:
            print(f"[WhatsApp] Yetkili okunamadi: {e}")
            return None

    def _cari_irsaliyelerini_getir(self, cari_id, limit=30):
        """Cari'nin son irsaliyelerini dondurur."""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT TOP (?) id, irsaliye_no, tarih, durum
                FROM siparis.cikis_irsaliyeleri
                WHERE cari_id = ? AND ISNULL(silindi_mi, 0) = 0
                ORDER BY id DESC
            """, (limit, cari_id))
            rows = cur.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"[WhatsApp] Irsaliye listesi alinamadi: {e}")
            return []

    @staticmethod
    def _telefon_normalize(tel: str) -> str:
        """'+905321234567' formatina donustur. Bos/gecersiz ise '' dondur."""
        if not tel:
            return ""
        t = ''.join(ch for ch in tel if ch.isdigit() or ch == '+')
        if not t:
            return ""
        if t.startswith('+'):
            return t
        if t.startswith('00'):
            return '+' + t[2:]
        if t.startswith('0') and len(t) >= 10:
            return '+90' + t[1:]
        if t.startswith('90') and len(t) >= 11:
            return '+' + t
        if len(t) == 10:
            return '+90' + t
        return '+' + t

    def _whatsapp_irsaliye_gonder(self, yetkili_id: int):
        """Secili yetkiliye WhatsApp ile irsaliye PDF gonder."""
        self._ensure_whatsapp_log_table()

        yetkili = self._yetkili_bilgileri(yetkili_id)
        if not yetkili:
            QMessageBox.warning(self, "Uyari", "Yetkili bilgileri alinamadi.")
            return

        telefon_raw = yetkili['cep_telefon'] or yetkili['telefon']
        telefon = self._telefon_normalize(telefon_raw)
        if not telefon:
            QMessageBox.warning(
                self, "Telefon Yok",
                f"{yetkili['ad_soyad']} icin gecerli bir telefon numarasi tanimli degil.\n"
                "Yetkiliyi duzenleyip cep telefonu alanini doldurun."
            )
            return

        # Irsaliye secim dialogu
        dlg = IrsaliyeSecDialog(self.theme, yetkili, self)
        if dlg.exec() != QDialog.Accepted:
            return

        irsaliye_id = dlg.secilen_irsaliye_id
        irsaliye_no = dlg.secilen_irsaliye_no
        caption = dlg.caption
        if not irsaliye_id:
            return

        # PDF uret
        try:
            from utils.irsaliye_pdf import generate_irsaliye_pdf
            import tempfile
            tmp = tempfile.gettempdir()
            safe_no = ''.join(ch if ch.isalnum() or ch in '-_' else '_' for ch in irsaliye_no)
            pdf_path = os.path.join(tmp, f"Irsaliye_{safe_no}.pdf")
            generate_irsaliye_pdf(irsaliye_id, pdf_path)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Irsaliye PDF olusturulamadi:\n{e}")
            self._whatsapp_log_yaz(
                yetkili_id, yetkili['cari_id'], telefon, yetkili['ad_soyad'],
                'IRSALIYE', irsaliye_no, irsaliye_id, None, caption,
                'HATA', f"PDF: {e}")
            return

        dosya_adi = os.path.basename(pdf_path)

        # WhatsApp gonder
        try:
            from utils.whatsapp_service import get_whatsapp_service
            svc = get_whatsapp_service()
            if not svc.ayarlar:
                QMessageBox.warning(
                    self, "WhatsApp Ayarlari",
                    "WhatsApp ayarlari yapilandirilmamis.\n"
                    "Sistem > WhatsApp Ayarlari menusunden ayarlayin."
                )
                self._whatsapp_log_yaz(
                    yetkili_id, yetkili['cari_id'], telefon, yetkili['ad_soyad'],
                    'IRSALIYE', irsaliye_no, irsaliye_id, dosya_adi, caption,
                    'HATA', 'Ayar yok')
                return

            basarili, mesaj = svc.gonder_dokuman(
                telefon=telefon,
                dosya_path=pdf_path,
                caption=caption,
                filename=dosya_adi,
            )
        except Exception as e:
            basarili, mesaj = False, str(e)

        durum = "BASARILI" if basarili else "HATA"
        self._whatsapp_log_yaz(
            yetkili_id, yetkili['cari_id'], telefon, yetkili['ad_soyad'],
            'IRSALIYE', irsaliye_no, irsaliye_id, dosya_adi, caption,
            durum, (None if basarili else mesaj))

        if basarili:
            QMessageBox.information(
                self, "Gonderildi",
                f"{irsaliye_no} irsaliyesi WhatsApp ile gonderildi.\n\n"
                f"Alici: {yetkili['ad_soyad']}\n"
                f"Telefon: {telefon}"
            )
        else:
            QMessageBox.critical(
                self, "Gonderilemedi",
                f"WhatsApp gonderimi basarisiz:\n\n{mesaj}"
            )


class IrsaliyeSecDialog(QDialog):
    """Bir yetkiliye gonderilecek irsaliyeyi secme ve aciklama yazma dialogu."""

    def __init__(self, theme, yetkili_info, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.yetkili = yetkili_info
        self.parent_page = parent
        self.secilen_irsaliye_id = None
        self.secilen_irsaliye_no = None
        self.caption = ""
        self.setWindowTitle(f"WhatsApp - {yetkili_info['ad_soyad']}")
        self.setMinimumSize(560, 520)
        self._setup_ui()
        self._load_irsaliyeler()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QTextEdit, QListWidget {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px;
                color: {brand.TEXT};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        baslik = QLabel(
            f"<b>Alici:</b> {self.yetkili['ad_soyad']} &nbsp;|&nbsp; "
            f"<b>Cari:</b> {self.yetkili['cari_unvan']}"
        )
        layout.addWidget(baslik)

        tel_raw = self.yetkili['cep_telefon'] or self.yetkili['telefon']
        tel_normal = self.parent_page._telefon_normalize(tel_raw) if self.parent_page else tel_raw
        tel_lbl = QLabel(f"<b>Telefon:</b> {tel_normal}")
        layout.addWidget(tel_lbl)

        layout.addWidget(QLabel("Gonderilecek Irsaliye:"))
        self.lst_irsaliye = QListWidget()
        self.lst_irsaliye.itemDoubleClicked.connect(self._accept)
        layout.addWidget(self.lst_irsaliye, 1)

        layout.addWidget(QLabel("Mesaj (opsiyonel):"))
        self.txt_mesaj = QTextEdit()
        self.txt_mesaj.setMaximumHeight(100)
        self.txt_mesaj.setPlainText(
            f"Sayin {self.yetkili['ad_soyad']},\n\n"
            f"Irsaliyeniz ektedir.\n\nATLAS KATAFOREZ"
        )
        layout.addWidget(self.txt_mesaj)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Gonder")
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_irsaliyeler(self):
        if not self.parent_page:
            return
        rows = self.parent_page._cari_irsaliyelerini_getir(self.yetkili['cari_id'])
        if not rows:
            item = QListWidgetItem("(Bu cari icin irsaliye bulunamadi)")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.lst_irsaliye.addItem(item)
            return
        for _id, _no, _tarih, _durum in rows:
            tarih_str = _tarih.strftime('%d.%m.%Y') if hasattr(_tarih, 'strftime') else str(_tarih or '')
            item = QListWidgetItem(f"{_no}  •  {tarih_str}  •  {_durum or ''}")
            item.setData(Qt.UserRole, (_id, _no))
            self.lst_irsaliye.addItem(item)
        self.lst_irsaliye.setCurrentRow(0)

    def _accept(self):
        item = self.lst_irsaliye.currentItem()
        if not item or not item.data(Qt.UserRole):
            QMessageBox.warning(self, "Uyari", "Lutfen bir irsaliye secin.")
            return
        self.secilen_irsaliye_id, self.secilen_irsaliye_no = item.data(Qt.UserRole)
        self.caption = self.txt_mesaj.toPlainText().strip()
        self.accept()
