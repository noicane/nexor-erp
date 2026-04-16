# -*- coding: utf-8 -*-
"""
NEXOR ERP - Aksiyon Detay Dialog (Sekmeli)
3 sekmeli dialog: Bilgiler, Aktiviteler, Dosyalar
"""

import os
import subprocess
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QGridLayout, QLineEdit, QTextEdit,
    QComboBox, QDateEdit, QSpinBox, QMessageBox, QFrame,
    QScrollArea, QFileDialog
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QFont, QCursor

from core.database import execute_query, execute_non_query
from core.yetki_manager import YetkiManager
from core.aksiyon_service import AksiyonService
from core.nexor_brand import brand


class AksiyonDetayDialog(QDialog):
    """Sekmeli aksiyon detay ve duzenleme dialogu"""

    def __init__(self, theme: dict, aksiyon_id: int = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.aksiyon_id = aksiyon_id
        self.is_edit_mode = aksiyon_id is not None
        self.aksiyon_data = None

        self.setWindowTitle("Aksiyon Detayı" if self.is_edit_mode else "Yeni Aksiyon")
        self.setMinimumSize(900, 700)
        self.setModal(True)

        self._setup_ui()
        self._apply_styles()

        if self.is_edit_mode:
            self._load_data()

    # =========================================================================
    # UI KURULUMU
    # =========================================================================

    def _setup_ui(self):
        """Ana dialog arayuzunu olustur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Baslik
        title_text = "Aksiyon Detayı" if self.is_edit_mode else "Yeni Aksiyon"
        title = QLabel(title_text)
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {brand.TEXT};
            padding-bottom: 8px;
            border-bottom: 2px solid {brand.BORDER};
        """)
        layout.addWidget(title)

        # Tab Widget
        self.tabs = QTabWidget()
        self._setup_bilgiler_tab()
        self._setup_aktiviteler_tab()
        self._setup_dosyalar_tab()
        layout.addWidget(self.tabs, 1)

        # Alt butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Kaydet")
        btn_save.setProperty("class", "primary")
        btn_save.clicked.connect(self._save_data)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    # =========================================================================
    # SEKME 1: BILGILER
    # =========================================================================

    def _setup_bilgiler_tab(self):
        """Bilgiler sekmesini olustur"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        form = QGridLayout()
        form.setSpacing(12)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(3, 1)

        row = 0

        # Baslik
        form.addWidget(self._form_label("Başlık:"), row, 0)
        self.txt_baslik = QLineEdit()
        self.txt_baslik.setPlaceholderText("Aksiyon başlığı")
        form.addWidget(self.txt_baslik, row, 1, 1, 3)
        row += 1

        # Aciklama
        form.addWidget(self._form_label("Açıklama:"), row, 0, Qt.AlignTop)
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setPlaceholderText("Aksiyon detayları...")
        self.txt_aciklama.setMaximumHeight(100)
        form.addWidget(self.txt_aciklama, row, 1, 1, 3)
        row += 1

        # Kategori + Modul
        form.addWidget(self._form_label("Kategori:"), row, 0)
        self.cmb_kategori = QComboBox()
        self.cmb_kategori.addItems(['DUZELTICI', 'ONLEYICI', 'IYILESTIRME', 'GENEL'])
        form.addWidget(self.cmb_kategori, row, 1)

        form.addWidget(self._form_label("Kaynak Modül:"), row, 2)
        self.cmb_modul = QComboBox()
        self.cmb_modul.addItems(['KALITE', 'URETIM', 'BAKIM', 'ISG', 'IK', 'STOK', 'SEVKIYAT', 'GENEL'])
        form.addWidget(self.cmb_modul, row, 3)
        row += 1

        # Oncelik + Durum
        form.addWidget(self._form_label("Öncelik:"), row, 0)
        self.cmb_oncelik = QComboBox()
        self.cmb_oncelik.addItems(['KRITIK', 'YUKSEK', 'NORMAL', 'DUSUK'])
        self.cmb_oncelik.setCurrentText('NORMAL')
        form.addWidget(self.cmb_oncelik, row, 1)

        form.addWidget(self._form_label("Durum:"), row, 2)
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(['BEKLIYOR', 'DEVAM_EDIYOR', 'TAMAMLANDI', 'DOGRULANDI', 'IPTAL'])
        form.addWidget(self.cmb_durum, row, 3)
        row += 1

        # Sorumlu + Departman
        form.addWidget(self._form_label("Sorumlu:"), row, 0)
        self.cmb_sorumlu = QComboBox()
        self._load_personel_list()
        form.addWidget(self.cmb_sorumlu, row, 1)

        form.addWidget(self._form_label("Departman:"), row, 2)
        self.cmb_departman = QComboBox()
        self._load_departman_list()
        form.addWidget(self.cmb_departman, row, 3)
        row += 1

        # Hedef tarih + Tamamlanma orani
        form.addWidget(self._form_label("Hedef Tarih:"), row, 0)
        self.dt_hedef = QDateEdit()
        self.dt_hedef.setCalendarPopup(True)
        self.dt_hedef.setDate(QDate.currentDate().addDays(30))
        form.addWidget(self.dt_hedef, row, 1)

        form.addWidget(self._form_label("Tamamlanma (%):"), row, 2)
        self.spn_oran = QSpinBox()
        self.spn_oran.setRange(0, 100)
        self.spn_oran.setSuffix("%")
        self.spn_oran.setValue(0)
        form.addWidget(self.spn_oran, row, 3)

        layout.addLayout(form)
        layout.addStretch()

        self.tabs.addTab(tab, "Bilgiler")

    # =========================================================================
    # SEKME 2: AKTIVITELER
    # =========================================================================

    def _setup_aktiviteler_tab(self):
        """Aktiviteler (yorum/timeline) sekmesini olustur"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Yorum ekleme alani
        yorum_header = QLabel("Yeni Yorum / İlerleme Notu")
        yorum_header.setStyleSheet(f"font-weight: 600; font-size: 14px; color: {brand.TEXT};")
        layout.addWidget(yorum_header)

        self.txt_yorum = QTextEdit()
        self.txt_yorum.setPlaceholderText("Yorum veya ilerleme notu ekleyin...")
        self.txt_yorum.setMaximumHeight(80)
        layout.addWidget(self.txt_yorum)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_yorum_ekle = QPushButton("Yorum Ekle")
        btn_yorum_ekle.setProperty("class", "primary")
        btn_yorum_ekle.clicked.connect(self._yorum_ekle)
        btn_row.addWidget(btn_yorum_ekle)
        layout.addLayout(btn_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {brand.BORDER}; max-height: 1px;")
        layout.addWidget(sep)

        # Timeline scroll alani
        timeline_header = QLabel("Aktivite Geçmişi")
        timeline_header.setStyleSheet(f"font-weight: 600; font-size: 14px; color: {brand.TEXT};")
        layout.addWidget(timeline_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.timeline_container = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_container)
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_layout.setSpacing(8)
        self.timeline_layout.addStretch()

        scroll.setWidget(self.timeline_container)
        layout.addWidget(scroll, 1)

        self.tabs.addTab(tab, "Aktiviteler")

    # =========================================================================
    # SEKME 3: DOSYALAR
    # =========================================================================

    def _setup_dosyalar_tab(self):
        """Dosyalar sekmesini olustur"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Ust butonlar
        btn_row = QHBoxLayout()

        btn_dosya_ekle = QPushButton("Dosya Ekle")
        btn_dosya_ekle.setProperty("class", "primary")
        btn_dosya_ekle.clicked.connect(self._dosya_ekle)
        btn_row.addWidget(btn_dosya_ekle)

        btn_klasor_ac = QPushButton("NAS Klasörü Aç")
        btn_klasor_ac.clicked.connect(self._nas_klasor_ac)
        btn_row.addWidget(btn_klasor_ac)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Dosya listesi scroll alani
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.dosya_container = QWidget()
        self.dosya_layout = QVBoxLayout(self.dosya_container)
        self.dosya_layout.setContentsMargins(0, 0, 0, 0)
        self.dosya_layout.setSpacing(8)
        self.dosya_layout.addStretch()

        scroll.setWidget(self.dosya_container)
        layout.addWidget(scroll, 1)

        self.tabs.addTab(tab, "Dosyalar")

    # =========================================================================
    # VERI YUKLEME
    # =========================================================================

    def _load_data(self):
        """Mevcut aksiyon verilerini yukle"""
        try:
            query = """
                SELECT
                    baslik, aciklama, kategori, kaynak_modul, oncelik,
                    sorumlu_id, sorumlu_departman_id, hedef_tarih,
                    durum, tamamlanma_orani, aksiyon_no
                FROM sistem.aksiyonlar
                WHERE id = ?
            """
            results = execute_query(query, [self.aksiyon_id])
            if not results:
                QMessageBox.warning(self, "Uyarı", "Aksiyon bulunamadı!")
                self.reject()
                return

            data = results[0]
            self.aksiyon_data = data

            self.txt_baslik.setText(data.get('baslik', ''))
            self.txt_aciklama.setPlainText(data.get('aciklama', '') or '')

            for combo, key in [
                (self.cmb_kategori, 'kategori'),
                (self.cmb_modul, 'kaynak_modul'),
                (self.cmb_oncelik, 'oncelik'),
                (self.cmb_durum, 'durum'),
            ]:
                val = data.get(key, '')
                idx = combo.findText(val)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

            sorumlu_id = data.get('sorumlu_id')
            if sorumlu_id:
                idx = self.cmb_sorumlu.findData(sorumlu_id)
                if idx >= 0:
                    self.cmb_sorumlu.setCurrentIndex(idx)

            dept_id = data.get('sorumlu_departman_id')
            if dept_id:
                idx = self.cmb_departman.findData(dept_id)
                if idx >= 0:
                    self.cmb_departman.setCurrentIndex(idx)

            hedef = data.get('hedef_tarih')
            if hedef:
                self.dt_hedef.setDate(QDate(hedef.year, hedef.month, hedef.day))

            oran = data.get('tamamlanma_orani', 0) or 0
            self.spn_oran.setValue(oran)

            # Aktiviteler ve dosyalari yukle
            self._load_yorumlar()
            self._load_ekler()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata:\n{str(e)}")
            self.reject()

    def _load_personel_list(self):
        """Personel listesini yukle"""
        try:
            results = execute_query("""
                SELECT id, ad + ' ' + soyad AS tam_adi
                FROM ik.personeller
                WHERE aktif_mi = 1
                ORDER BY ad, soyad
            """)
            self.cmb_sorumlu.clear()
            self.cmb_sorumlu.addItem("Seçiniz...", None)
            for row in results:
                self.cmb_sorumlu.addItem(row['tam_adi'], row['id'])
        except Exception as e:
            print(f"[AksiyonDetayDialog] Personel listesi hatasi: {e}")

    def _load_departman_list(self):
        """Departman listesini yukle"""
        try:
            results = execute_query("""
                SELECT id, ad
                FROM ik.departmanlar
                WHERE aktif_mi = 1
                ORDER BY ad
            """)
            self.cmb_departman.clear()
            self.cmb_departman.addItem("Seçiniz...", None)
            for row in results:
                self.cmb_departman.addItem(row['ad'], row['id'])
        except Exception as e:
            print(f"[AksiyonDetayDialog] Departman listesi hatasi: {e}")

    # =========================================================================
    # AKTIVITELER
    # =========================================================================

    def _load_yorumlar(self):
        """Yorumlari/aktiviteleri timeline olarak yukle"""
        # Mevcut itemlari temizle
        while self.timeline_layout.count() > 1:
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        yorumlar = AksiyonService.yorumlari_getir(self.aksiyon_id)

        if not yorumlar:
            empty_label = QLabel("Henüz aktivite kaydı yok")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet(f"color: {brand.TEXT_MUTED}; padding: 20px;")
            self.timeline_layout.insertWidget(0, empty_label)
            return

        for i, yorum in enumerate(yorumlar):
            card = self._create_timeline_card(yorum)
            self.timeline_layout.insertWidget(i, card)

    def _create_timeline_card(self, yorum: dict) -> QFrame:
        """Timeline karti olustur"""
        t = self.theme
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {t['bg_card']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Ust satir: Tip badge + yazan + tarih
        top = QHBoxLayout()
        top.setSpacing(8)

        yorum_tipi = yorum.get('yorum_tipi', 'YORUM')
        tip_colors = {
            'YORUM': '#3b82f6',
            'DURUM_DEGISIKLIGI': '#f59e0b',
            'ILERLEME': '#10b981',
            'DOGRULAMA': '#8b5cf6',
        }
        tip_texts = {
            'YORUM': 'Yorum',
            'DURUM_DEGISIKLIGI': 'Durum Değişikliği',
            'ILERLEME': 'İlerleme',
            'DOGRULAMA': 'Doğrulama',
        }
        color = tip_colors.get(yorum_tipi, '#6b7280')
        tip_badge = QLabel(tip_texts.get(yorum_tipi, yorum_tipi))
        tip_badge.setStyleSheet(f"""
            background: {color};
            color: white;
            border-radius: 3px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: bold;
        """)
        top.addWidget(tip_badge)

        yazan = QLabel(yorum.get('yazan_adi', 'Bilinmiyor'))
        yazan.setStyleSheet(f"color: {t['text']}; font-weight: 600; font-size: 12px;")
        top.addWidget(yazan)

        top.addStretch()

        tarih = yorum.get('olusturma_tarihi')
        tarih_str = tarih.strftime('%d.%m.%Y %H:%M') if tarih else ''
        tarih_label = QLabel(tarih_str)
        tarih_label.setStyleSheet(f"color: {t['text_secondary']}; font-size: 11px;")
        top.addWidget(tarih_label)

        layout.addLayout(top)

        # Durum degisikligi gosterimi
        if yorum_tipi == 'DURUM_DEGISIKLIGI':
            eski = yorum.get('eski_durum', '')
            yeni = yorum.get('yeni_durum', '')
            if eski and yeni:
                durum_label = QLabel(f"{eski}  →  {yeni}")
                durum_label.setStyleSheet(f"color: {color}; font-weight: 600; font-size: 12px;")
                layout.addWidget(durum_label)

        # Yorum metni
        metin = yorum.get('yorum', '')
        if metin:
            metin_label = QLabel(metin)
            metin_label.setWordWrap(True)
            metin_label.setStyleSheet(f"color: {t['text']}; font-size: 13px;")
            layout.addWidget(metin_label)

        return card

    def _yorum_ekle(self):
        """Yeni yorum ekle"""
        if not self.aksiyon_id:
            QMessageBox.warning(self, "Uyarı", "Önce aksiyonu kaydedin!")
            return

        yorum_text = self.txt_yorum.toPlainText().strip()
        if not yorum_text:
            QMessageBox.warning(self, "Uyarı", "Yorum alanı boş olamaz!")
            self.txt_yorum.setFocus()
            return

        result = AksiyonService.yorum_ekle(
            aksiyon_id=self.aksiyon_id,
            yorum=yorum_text,
            yorum_tipi='YORUM',
        )

        if result:
            self.txt_yorum.clear()
            self._load_yorumlar()
        else:
            QMessageBox.critical(self, "Hata", "Yorum eklenemedi!")

    # =========================================================================
    # DOSYALAR
    # =========================================================================

    def _load_ekler(self):
        """Dosya eklerini yukle ve goster"""
        # Mevcut itemlari temizle
        while self.dosya_layout.count() > 1:
            item = self.dosya_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        ekler = AksiyonService.ekleri_getir(self.aksiyon_id)

        if not ekler:
            empty_label = QLabel("Henüz dosya eklenmemiş")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet(f"color: {brand.TEXT_MUTED}; padding: 20px;")
            self.dosya_layout.insertWidget(0, empty_label)
            return

        for i, ek in enumerate(ekler):
            card = self._create_dosya_card(ek)
            self.dosya_layout.insertWidget(i, card)

    def _create_dosya_card(self, ek: dict) -> QFrame:
        """Dosya karti olustur"""
        t = self.theme
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {t['bg_card']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame:hover {{
                border-color: {t['primary']};
            }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Dosya tipi ikonu
        dosya_tipi = ek.get('dosya_tipi', '').lower()
        tip_icon = self._get_dosya_icon(dosya_tipi)
        icon_label = QLabel(tip_icon)
        icon_label.setStyleSheet(f"font-size: 20px; min-width: 30px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Dosya bilgileri
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        dosya_adi = QLabel(ek.get('dosya_adi', ''))
        dosya_adi.setStyleSheet(f"color: {t['text']}; font-weight: 600; font-size: 13px;")
        info_layout.addWidget(dosya_adi)

        detay_parts = []
        boyut = ek.get('dosya_boyutu', 0)
        if boyut:
            detay_parts.append(self._format_boyut(boyut))
        yukleyen = ek.get('yukleyen_adi', '')
        if yukleyen:
            detay_parts.append(yukleyen)
        tarih = ek.get('olusturma_tarihi')
        if tarih:
            detay_parts.append(tarih.strftime('%d.%m.%Y %H:%M'))

        if detay_parts:
            detay = QLabel(' | '.join(detay_parts))
            detay.setStyleSheet(f"color: {t['text_secondary']}; font-size: 11px;")
            info_layout.addWidget(detay)

        aciklama = ek.get('aciklama', '')
        if aciklama:
            aciklama_label = QLabel(aciklama)
            aciklama_label.setStyleSheet(f"color: {t['text_secondary']}; font-size: 12px;")
            info_layout.addWidget(aciklama_label)

        layout.addLayout(info_layout, 1)

        # Ac butonu
        btn_ac = QPushButton("Aç")
        btn_ac.setMaximumWidth(60)
        btn_ac.setCursor(QCursor(Qt.PointingHandCursor))
        dosya_yolu = ek.get('dosya_yolu', '')
        btn_ac.clicked.connect(lambda checked, p=dosya_yolu: self._dosya_ac(p))
        layout.addWidget(btn_ac)

        # Sil butonu
        btn_sil = QPushButton("Sil")
        btn_sil.setMaximumWidth(50)
        btn_sil.setProperty("class", "danger")
        btn_sil.setCursor(QCursor(Qt.PointingHandCursor))
        ek_id = ek.get('id')
        btn_sil.clicked.connect(lambda checked, eid=ek_id: self._ek_sil(eid))
        layout.addWidget(btn_sil)

        return card

    def _dosya_ekle(self):
        """Dosya secme dialogu ac ve yukle"""
        if not self.aksiyon_id or not self.aksiyon_data:
            QMessageBox.warning(self, "Uyarı", "Önce aksiyonu kaydedin!")
            return

        dosya_yollari, _ = QFileDialog.getOpenFileNames(
            self,
            "Dosya Seç",
            "",
            "Tüm Dosyalar (*);;Resimler (*.png *.jpg *.jpeg *.bmp);;PDF (*.pdf);;Excel (*.xlsx *.xls);;Word (*.docx *.doc)"
        )

        if not dosya_yollari:
            return

        aksiyon_no = self.aksiyon_data.get('aksiyon_no', '')
        basarili = 0
        for dosya in dosya_yollari:
            result = AksiyonService.dosya_yukle(
                aksiyon_id=self.aksiyon_id,
                aksiyon_no=aksiyon_no,
                kaynak_dosya=dosya,
            )
            if result:
                basarili += 1

        if basarili > 0:
            QMessageBox.information(
                self, "Başarılı",
                f"{basarili} dosya başarıyla yüklendi."
            )
            self._load_ekler()
        else:
            QMessageBox.critical(self, "Hata", "Dosya yüklenemedi!")

    def _ek_sil(self, ek_id: int):
        """Eki sil (onay ile)"""
        reply = QMessageBox.question(
            self, "Onay",
            "Bu dosyayı silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if AksiyonService.ek_sil(ek_id):
                self._load_ekler()
            else:
                QMessageBox.critical(self, "Hata", "Dosya silinemedi!")

    def _dosya_ac(self, dosya_yolu: str):
        """Dosyayi varsayilan uygulama ile ac"""
        if not dosya_yolu or not os.path.exists(dosya_yolu):
            QMessageBox.warning(self, "Uyarı", "Dosya bulunamadı!")
            return
        try:
            os.startfile(dosya_yolu)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya açılamadı:\n{e}")

    def _nas_klasor_ac(self):
        """NAS uzerindeki aksiyon klasorunu Explorer ile ac"""
        if not self.aksiyon_data:
            QMessageBox.warning(self, "Uyarı", "Aksiyon verisi yüklenmedi!")
            return

        aksiyon_no = self.aksiyon_data.get('aksiyon_no', '')
        klasor = AksiyonService.klasor_olustur(aksiyon_no)

        if klasor and os.path.exists(klasor):
            subprocess.Popen(['explorer', klasor])
        else:
            QMessageBox.warning(self, "Uyarı", "NAS klasörüne erişilemiyor!")

    # =========================================================================
    # KAYDETME
    # =========================================================================

    def _save_data(self):
        """Aksiyonu kaydet"""
        if not self.txt_baslik.text().strip():
            QMessageBox.warning(self, "Uyarı", "Başlık alanı zorunludur!")
            self.txt_baslik.setFocus()
            return

        if self.cmb_sorumlu.currentData() is None:
            QMessageBox.warning(self, "Uyarı", "Sorumlu personel seçmelisiniz!")
            return

        try:
            baslik = self.txt_baslik.text().strip()
            aciklama = self.txt_aciklama.toPlainText().strip()
            kategori = self.cmb_kategori.currentText()
            kaynak_modul = self.cmb_modul.currentText()
            oncelik = self.cmb_oncelik.currentText()
            durum = self.cmb_durum.currentText()
            sorumlu_id = self.cmb_sorumlu.currentData()
            dept_id = self.cmb_departman.currentData()
            hedef_tarih = self.dt_hedef.date().toPython()
            oran = self.spn_oran.value()

            user_id = YetkiManager._current_user_id or 1

            if self.is_edit_mode:
                # Durum degisikligi kontrolu
                eski_durum = self.aksiyon_data.get('durum', '') if self.aksiyon_data else ''
                if eski_durum and eski_durum != durum:
                    AksiyonService.durum_guncelle(self.aksiyon_id, durum)

                query = """
                    UPDATE sistem.aksiyonlar
                    SET baslik = ?, aciklama = ?, kategori = ?,
                        kaynak_modul = ?, oncelik = ?, durum = ?,
                        sorumlu_id = ?, sorumlu_departman_id = ?,
                        hedef_tarih = ?, tamamlanma_orani = ?,
                        guncelleme_tarihi = GETDATE(), guncelleyen_id = ?
                    WHERE id = ?
                """
                params = [
                    baslik, aciklama, kategori, kaynak_modul, oncelik,
                    durum, sorumlu_id, dept_id, hedef_tarih, oran,
                    user_id, self.aksiyon_id
                ]
                execute_non_query(query, params)
                QMessageBox.information(self, "Başarılı", "Aksiyon güncellendi!")

            else:
                # Yeni aksiyon - AksiyonService kullan
                aksiyon_id = AksiyonService.olustur(
                    baslik=baslik,
                    aciklama=aciklama,
                    kategori=kategori,
                    kaynak_modul=kaynak_modul,
                    oncelik=oncelik,
                    sorumlu_id=sorumlu_id,
                    sorumlu_departman_id=dept_id,
                    hedef_tarih=str(hedef_tarih),
                )
                if aksiyon_id:
                    # Durum ve oran guncelle (varsayilan BEKLIYOR degilse)
                    if durum != 'BEKLIYOR':
                        AksiyonService.durum_guncelle(aksiyon_id, durum)
                    if oran > 0:
                        AksiyonService.guncelle(aksiyon_id, tamamlanma_orani=oran)
                    QMessageBox.information(self, "Başarılı", "Aksiyon oluşturuldu!")
                else:
                    QMessageBox.critical(self, "Hata", "Aksiyon oluşturulamadı!")
                    return

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt sırasında hata:\n{str(e)}")

    # =========================================================================
    # YARDIMCI
    # =========================================================================

    def _form_label(self, text: str) -> QLabel:
        """Form etiketi olustur"""
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-weight: 500;")
        return lbl

    def _get_dosya_icon(self, dosya_tipi: str) -> str:
        """Dosya tipine gore ikon dondur"""
        icon_map = {
            '.pdf': 'PDF',
            '.xlsx': 'XLS',
            '.xls': 'XLS',
            '.docx': 'DOC',
            '.doc': 'DOC',
            '.png': 'IMG',
            '.jpg': 'IMG',
            '.jpeg': 'IMG',
            '.bmp': 'IMG',
            '.gif': 'IMG',
            '.txt': 'TXT',
            '.csv': 'CSV',
            '.zip': 'ZIP',
            '.rar': 'ZIP',
        }
        return icon_map.get(dosya_tipi, 'FILE')

    @staticmethod
    def _format_boyut(boyut: int) -> str:
        """Dosya boyutunu okunabilir formata cevir"""
        if boyut < 1024:
            return f"{boyut} B"
        elif boyut < 1024 * 1024:
            return f"{boyut / 1024:.1f} KB"
        elif boyut < 1024 * 1024 * 1024:
            return f"{boyut / (1024 * 1024):.1f} MB"
        else:
            return f"{boyut / (1024 * 1024 * 1024):.1f} GB"

    def _apply_styles(self):
        """Dialog stillerini uygula"""
        self.setStyleSheet(f"""
            QDialog {{
                background: {brand.BG_MAIN};
            }}
            QLabel {{
                color: {brand.TEXT};
            }}
            QPushButton {{
                min-width: 80px;
                padding: 8px 16px;
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 8px;
                color: {brand.TEXT};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {brand.BG_HOVER};
            }}
            QPushButton[class="primary"] {{
                background: {brand.PRIMARY};
                color: white;
                border: none;
                font-weight: 600;
            }}
            QPushButton[class="primary"]:hover {{
                background: {brand.PRIMARY_HOVER};
            }}
            QPushButton[class="danger"] {{
                background: {brand.ERROR};
                color: white;
                border: none;
                font-weight: 600;
            }}
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit {{
                background: {brand.BG_INPUT};
                border: 1px solid {brand.BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                color: {brand.TEXT};
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
                border-color: {brand.PRIMARY};
            }}
            QTabWidget::pane {{
                background: {brand.BG_CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 12px;
                padding: 8px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {brand.TEXT_DIM};
                padding: 10px 20px;
                border: none;
                border-bottom: 2px solid transparent;
                font-weight: 500;
            }}
            QTabBar::tab:hover {{
                color: {brand.TEXT};
            }}
            QTabBar::tab:selected {{
                color: {brand.PRIMARY};
                border-bottom-color: {brand.PRIMARY};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
        """)
