# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İSG Olay Kayıtları
İş Kazası / Ramak Kala / Meslek Hastalığı
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox,
    QDialog, QFormLayout, QFrame, QDateEdit, QTextEdit, QSpinBox,
    QCheckBox, QTabWidget, QDateTimeEdit
)
from PySide6.QtCore import Qt, QDate, QDateTime
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


class OlayDialog(QDialog):
    """Olay kaydı oluşturma/düzenleme"""
    
    def __init__(self, theme: dict, parent=None, olay_id=None):
        super().__init__(parent)
        self.theme = theme
        self.olay_id = olay_id
        self.setWindowTitle("Olay Kaydı" if not olay_id else "Olay Düzenle")
        self.setMinimumSize(800, 650)
        self.setModal(True)
        self._setup_ui()
        self._load_combos()
        if olay_id:
            self._load_data()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QComboBox, QDateEdit, QDateTimeEdit, QTextEdit, QSpinBox {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px;
                color: {brand.TEXT};
            }}
            QTabWidget::pane {{ border: 1px solid {brand.BORDER}; }}
            QTabBar::tab {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 10px 20px; }}
            QTabBar::tab:selected {{ background: {brand.PRIMARY}; color: white; }}
            QCheckBox {{ color: {brand.TEXT}; }}
        """)
        
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        
        # Tab 1: Olay Bilgileri
        tab_olay = QWidget()
        olay_layout = QFormLayout(tab_olay)
        
        self.txt_olay_no = QLineEdit()
        self.txt_olay_no.setReadOnly(True)
        olay_layout.addRow("Olay No:", self.txt_olay_no)
        
        self.cmb_olay_tipi = QComboBox()
        self.cmb_olay_tipi.addItems(["IS_KAZASI", "RAMAK_KALA", "MESLEK_HASTALIGI"])
        olay_layout.addRow("Olay Tipi*:", self.cmb_olay_tipi)
        
        self.dt_olay = QDateTimeEdit()
        self.dt_olay.setDateTime(QDateTime.currentDateTime())
        self.dt_olay.setCalendarPopup(True)
        olay_layout.addRow("Tarih/Saat*:", self.dt_olay)
        
        self.txt_olay_yeri = QLineEdit()
        olay_layout.addRow("Olay Yeri*:", self.txt_olay_yeri)
        
        self.cmb_bolum = QComboBox()
        olay_layout.addRow("Bölüm:", self.cmb_bolum)
        
        self.txt_olay_tanimi = QTextEdit()
        self.txt_olay_tanimi.setMaximumHeight(80)
        olay_layout.addRow("Olay Tanımı*:", self.txt_olay_tanimi)
        
        self.txt_taniklar = QLineEdit()
        olay_layout.addRow("Tanıklar:", self.txt_taniklar)
        
        tabs.addTab(tab_olay, "📋 Olay")
        
        # Tab 2: Kazazede
        tab_kazazede = QWidget()
        kazazede_layout = QFormLayout(tab_kazazede)
        
        self.cmb_kazazede = QComboBox()
        kazazede_layout.addRow("Kazazede:", self.cmb_kazazede)
        
        self.txt_kazazede_adi = QLineEdit()
        kazazede_layout.addRow("Kazazede Adı:", self.txt_kazazede_adi)
        
        self.txt_yaralanma_tipi = QLineEdit()
        kazazede_layout.addRow("Yaralanma Tipi:", self.txt_yaralanma_tipi)
        
        self.txt_yaralanan_bolge = QLineEdit()
        kazazede_layout.addRow("Yaralanan Bölge:", self.txt_yaralanan_bolge)
        
        self.chk_kayip_gun = QCheckBox("Kayıp Günlü İş Kazası")
        kazazede_layout.addRow("", self.chk_kayip_gun)
        
        self.spin_kayip_gun = QSpinBox()
        self.spin_kayip_gun.setRange(0, 365)
        self.spin_kayip_gun.setSuffix(" gün")
        kazazede_layout.addRow("Kayıp Gün:", self.spin_kayip_gun)
        
        self.chk_sgk = QCheckBox("SGK'ya Bildirildi")
        kazazede_layout.addRow("", self.chk_sgk)
        
        self.txt_sgk_belge = QLineEdit()
        kazazede_layout.addRow("SGK Belge No:", self.txt_sgk_belge)
        
        tabs.addTab(tab_kazazede, "🤕 Kazazede")
        
        # Tab 3: Kök Neden
        tab_kok = QWidget()
        kok_layout = QFormLayout(tab_kok)
        
        self.cmb_analiz = QComboBox()
        self.cmb_analiz.addItems(["", "5N1K", "BALIK_KILCIGI", "5_NEDEN"])
        kok_layout.addRow("Analiz Yöntemi:", self.cmb_analiz)
        
        self.txt_kok_neden = QTextEdit()
        self.txt_kok_neden.setMaximumHeight(100)
        kok_layout.addRow("Kök Neden:", self.txt_kok_neden)
        
        self.txt_duzeltici = QTextEdit()
        self.txt_duzeltici.setMaximumHeight(80)
        kok_layout.addRow("Düzeltici Faaliyet:", self.txt_duzeltici)
        
        self.cmb_sorumlu = QComboBox()
        kok_layout.addRow("Sorumlu:", self.cmb_sorumlu)
        
        self.date_hedef = QDateEdit()
        self.date_hedef.setDate(QDate.currentDate().addDays(14))
        self.date_hedef.setCalendarPopup(True)
        kok_layout.addRow("Hedef Tarih:", self.date_hedef)
        
        tabs.addTab(tab_kok, "🔍 Kök Neden")
        layout.addWidget(tabs)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 10px 24px; border-radius: 6px;")
        btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(btn_iptal)
        
        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"background: {brand.SUCCESS}; color: white; padding: 10px 24px; border-radius: 6px;")
        btn_kaydet.clicked.connect(self._save)
        btn_layout.addWidget(btn_kaydet)
        
        layout.addLayout(btn_layout)
    
    def _load_combos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            self.cmb_bolum.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, kod, ad FROM ik.departmanlar WHERE aktif_mi = 1 ORDER BY kod")
            for row in cursor.fetchall():
                self.cmb_bolum.addItem(f"{row[1]} - {row[2]}", row[0])
            
            self.cmb_kazazede.addItem("-- Seçiniz --", None)
            self.cmb_sorumlu.addItem("-- Seçiniz --", None)
            cursor.execute("SELECT id, sicil_no, ad + ' ' + soyad FROM ik.personeller WHERE aktif_mi = 1 ORDER BY ad")
            for row in cursor.fetchall():
                self.cmb_kazazede.addItem(f"{row[1]} - {row[2]}", row[0])
                self.cmb_sorumlu.addItem(f"{row[1]} - {row[2]}", row[0])
            
            conn.close()
        except Exception:
            pass
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT olay_no, olay_tipi, olay_tarihi, olay_yeri, bolum_id, olay_tanimi,
                       tanik_isimleri, kazazede_id, kazazede_adi, yaralanma_tipi, yaralanan_bolge,
                       kayip_gun_var_mi, kayip_gun_sayisi, sgk_bildirildi_mi, sgk_belge_no,
                       analiz_yontemi, kok_neden, duzeltici_faaliyet, faaliyet_sorumlu_id, faaliyet_hedef_tarih
                FROM isg.olay_kayitlari WHERE id = ?
            """, (self.olay_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.txt_olay_no.setText(row[0] or "")
                idx = self.cmb_olay_tipi.findText(row[1] or "IS_KAZASI")
                if idx >= 0: self.cmb_olay_tipi.setCurrentIndex(idx)
                if row[2]: self.dt_olay.setDateTime(QDateTime(row[2]))
                self.txt_olay_yeri.setText(row[3] or "")
                if row[4]:
                    idx = self.cmb_bolum.findData(row[4])
                    if idx >= 0: self.cmb_bolum.setCurrentIndex(idx)
                self.txt_olay_tanimi.setPlainText(row[5] or "")
                self.txt_taniklar.setText(row[6] or "")
                if row[7]:
                    idx = self.cmb_kazazede.findData(row[7])
                    if idx >= 0: self.cmb_kazazede.setCurrentIndex(idx)
                self.txt_kazazede_adi.setText(row[8] or "")
                self.txt_yaralanma_tipi.setText(row[9] or "")
                self.txt_yaralanan_bolge.setText(row[10] or "")
                self.chk_kayip_gun.setChecked(row[11] or False)
                self.spin_kayip_gun.setValue(row[12] or 0)
                self.chk_sgk.setChecked(row[13] or False)
                self.txt_sgk_belge.setText(row[14] or "")
                if row[15]:
                    idx = self.cmb_analiz.findText(row[15])
                    if idx >= 0: self.cmb_analiz.setCurrentIndex(idx)
                self.txt_kok_neden.setPlainText(row[16] or "")
                self.txt_duzeltici.setPlainText(row[17] or "")
                if row[18]:
                    idx = self.cmb_sorumlu.findData(row[18])
                    if idx >= 0: self.cmb_sorumlu.setCurrentIndex(idx)
                if row[19]: self.date_hedef.setDate(QDate(row[19].year, row[19].month, row[19].day))
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
    
    def _save(self):
        if not self.txt_olay_yeri.text().strip() or not self.txt_olay_tanimi.toPlainText().strip():
            QMessageBox.warning(self, "Uyarı", "Olay yeri ve tanımı zorunludur!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if self.olay_id:
                cursor.execute("""
                    UPDATE isg.olay_kayitlari SET
                        olay_tipi = ?, olay_tarihi = ?, olay_yeri = ?, bolum_id = ?, olay_tanimi = ?,
                        tanik_isimleri = ?, kazazede_id = ?, kazazede_adi = ?, yaralanma_tipi = ?,
                        yaralanan_bolge = ?, kayip_gun_var_mi = ?, kayip_gun_sayisi = ?,
                        sgk_bildirildi_mi = ?, sgk_belge_no = ?, analiz_yontemi = ?, kok_neden = ?,
                        duzeltici_faaliyet = ?, faaliyet_sorumlu_id = ?, faaliyet_hedef_tarih = ?,
                        guncelleme_tarihi = GETDATE()
                    WHERE id = ?
                """, (
                    self.cmb_olay_tipi.currentText(), self.dt_olay.dateTime().toPython(),
                    self.txt_olay_yeri.text().strip(), self.cmb_bolum.currentData(),
                    self.txt_olay_tanimi.toPlainText().strip(), self.txt_taniklar.text().strip() or None,
                    self.cmb_kazazede.currentData(), self.txt_kazazede_adi.text().strip() or None,
                    self.txt_yaralanma_tipi.text().strip() or None, self.txt_yaralanan_bolge.text().strip() or None,
                    self.chk_kayip_gun.isChecked(), self.spin_kayip_gun.value() if self.chk_kayip_gun.isChecked() else None,
                    self.chk_sgk.isChecked(), self.txt_sgk_belge.text().strip() or None,
                    self.cmb_analiz.currentText() or None, self.txt_kok_neden.toPlainText().strip() or None,
                    self.txt_duzeltici.toPlainText().strip() or None, self.cmb_sorumlu.currentData(),
                    self.date_hedef.date().toPython(), self.olay_id
                ))
            else:
                tip_kisa = {"IS_KAZASI": "IK", "RAMAK_KALA": "RK", "MESLEK_HASTALIGI": "MH"}
                tip = tip_kisa.get(self.cmb_olay_tipi.currentText(), "OL")
                cursor.execute(f"SELECT '{tip}-' + FORMAT(GETDATE(), 'yyyyMMdd') + '-' + RIGHT('000' + CAST(ISNULL((SELECT MAX(id) FROM isg.olay_kayitlari), 0) + 1 AS VARCHAR), 4)")
                olay_no = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO isg.olay_kayitlari
                    (olay_no, olay_tipi, olay_tarihi, olay_yeri, bolum_id, olay_tanimi, tanik_isimleri,
                     kazazede_id, kazazede_adi, yaralanma_tipi, yaralanan_bolge, kayip_gun_var_mi,
                     kayip_gun_sayisi, sgk_bildirildi_mi, sgk_belge_no, analiz_yontemi, kok_neden,
                     duzeltici_faaliyet, faaliyet_sorumlu_id, faaliyet_hedef_tarih)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    olay_no, self.cmb_olay_tipi.currentText(), self.dt_olay.dateTime().toPython(),
                    self.txt_olay_yeri.text().strip(), self.cmb_bolum.currentData(),
                    self.txt_olay_tanimi.toPlainText().strip(), self.txt_taniklar.text().strip() or None,
                    self.cmb_kazazede.currentData(), self.txt_kazazede_adi.text().strip() or None,
                    self.txt_yaralanma_tipi.text().strip() or None, self.txt_yaralanan_bolge.text().strip() or None,
                    self.chk_kayip_gun.isChecked(), self.spin_kayip_gun.value() if self.chk_kayip_gun.isChecked() else None,
                    self.chk_sgk.isChecked(), self.txt_sgk_belge.text().strip() or None,
                    self.cmb_analiz.currentText() or None, self.txt_kok_neden.toPlainText().strip() or None,
                    self.txt_duzeltici.toPlainText().strip() or None, self.cmb_sorumlu.currentData(),
                    self.date_hedef.date().toPython()
                ))
                self.olay_id = cursor.fetchone()[0]
                self.txt_olay_no.setText(olay_no)
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Başarılı", "Olay kaydedildi.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class ISGOlayKayitlariPage(BasePage):
    """İSG Olay Kayıtları Ana Sayfası"""
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("🚨 Olay Kayıtları (Kaza / Ramak Kala)")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {brand.TEXT};")
        layout.addWidget(header)
        
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {brand.BG_CARD}; border-radius: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        btn_yeni = QPushButton("➕ Yeni Olay")
        btn_yeni.setStyleSheet(f"background: {brand.ERROR}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_yeni.clicked.connect(self._yeni)
        toolbar_layout.addWidget(btn_yeni)
        
        toolbar_layout.addStretch()
        
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["Tümü", "IS_KAZASI", "RAMAK_KALA", "MESLEK_HASTALIGI"])
        self.cmb_tip.setStyleSheet(f"background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px; color: {brand.TEXT};")
        self.cmb_tip.currentIndexChanged.connect(self._filter)
        toolbar_layout.addWidget(self.cmb_tip)
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.setStyleSheet(f"background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 8px 12px; color: {brand.TEXT};")
        btn_yenile.clicked.connect(self._load_data)
        toolbar_layout.addWidget(btn_yenile)
        
        layout.addWidget(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Olay No", "Tip", "Tarih", "Yer", "Kazazede", "Kayıp Gün", "Durum", "İşlem"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; border-radius: 8px; color: {brand.TEXT}; }}
            QTableWidget::item:selected {{ background: {brand.PRIMARY}; }}
            QHeaderView::section {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; padding: 10px; font-weight: bold; }}
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(8, 120)
        self.table.doubleClicked.connect(self._duzenle)
        layout.addWidget(self.table)
        
        self.lbl_stat = QLabel()
        self.lbl_stat.setStyleSheet(f"color: {brand.TEXT_DIM};")
        layout.addWidget(self.lbl_stat)
    
    def _load_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.id, o.olay_no, o.olay_tipi, FORMAT(o.olay_tarihi, 'dd.MM.yyyy'),
                       o.olay_yeri, ISNULL(p.ad + ' ' + p.soyad, o.kazazede_adi),
                       o.kayip_gun_sayisi, o.durum
                FROM isg.olay_kayitlari o
                LEFT JOIN ik.personeller p ON o.kazazede_id = p.id
                ORDER BY o.olay_tarihi DESC
            """)
            self.all_rows = cursor.fetchall()
            conn.close()
            self._display_data(self.all_rows)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")
    
    def _display_data(self, rows):
        self.table.setRowCount(len(rows))
        tip_colors = {'IS_KAZASI': brand.ERROR, 'RAMAK_KALA': brand.WARNING}
        
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if j == 2:
                    item = QTableWidgetItem(str(val) if val else "")
                    item.setForeground(QColor(tip_colors.get(val, brand.TEXT)))
                elif j == 6 and val:
                    item = QTableWidgetItem(str(val))
                    item.setForeground(QColor(brand.ERROR))
                else:
                    item = QTableWidgetItem(str(val) if val else "")
                self.table.setItem(i, j, item)

            rid = row[0]
            widget = self.create_action_buttons([
                ("✏️", "Duzenle", lambda checked, rid=rid: self._duzenle_by_id(rid), "edit"),
            ])
            self.table.setCellWidget(i, 8, widget)
            self.table.setRowHeight(i, 42)

        kaza = len([r for r in rows if r[2] == "IS_KAZASI"])
        ramak = len([r for r in rows if r[2] == "RAMAK_KALA"])
        self.lbl_stat.setText(f"Toplam: {len(rows)} | İş Kazası: {kaza} | Ramak Kala: {ramak}")
    
    def _duzenle_by_id(self, olay_id):
        """ID ile olay düzenleme (satır butonundan)"""
        dialog = OlayDialog(self.theme, self, olay_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()

    def _filter(self):
        tip = self.cmb_tip.currentText()
        if tip == "Tümü":
            self._display_data(self.all_rows)
        else:
            self._display_data([r for r in self.all_rows if r[2] == tip])
    
    def _yeni(self):
        dialog = OlayDialog(self.theme, self)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
    
    def _duzenle(self):
        row = self.table.currentRow()
        if row < 0: return
        olay_id = int(self.table.item(row, 0).text())
        dialog = OlayDialog(self.theme, self, olay_id)
        if dialog.exec() == QDialog.Accepted:
            self._load_data()
