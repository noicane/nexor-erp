# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Sistem > Modül Yönetimi
Musteri bazli modul aktivasyon ekrani.

Kaynaklar:
- lisans.moduller (sabit tanim, 20 ana modul)
- lisans.modul_durumlari (aktif + bitis_tarihi + notlar)

Kurallar:
- Granulerlik: ana modul seviyesi (alt sayfalar ust modulun durumunu miras alir)
- Zorunlu moduller (dashboard, tanimlar, sistem) toggle edilemez
- Bitis tarihi gecmis modul otomatik pasif sayilir
- Degisiklik sonrasi uygulama yeniden baslatilmadan sidebar guncellensin
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox, QDateEdit, QDialog, QFrame, QGroupBox, QFormLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
    QWidget,
)

from components.base_page import BasePage
from core.log_manager import LogManager
from core.modul_servisi import ModulServisi
from core.nexor_brand import brand


# ============================================================================
# DURUM DUZENLEME DIALOGU
# ============================================================================

class ModulDurumDialog(QDialog):
    """Bir modulun durumunu duzenle: aktif, bitis tarihi, notlar"""

    def __init__(self, modul: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.modul = modul
        self.setWindowTitle(f"Modül: {modul['ad']}")
        self.setMinimumSize(460, 380)
        self.setModal(True)
        self._build_ui()
        self._fill()

    def _build_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {brand.BG_MAIN}; }}
            QLabel {{ color: {brand.TEXT}; }}
            QLineEdit, QTextEdit, QDateEdit {{
                background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER};
                border-radius: 6px; padding: 8px; color: {brand.TEXT};
            }}
            QCheckBox {{ color: {brand.TEXT}; }}
            QGroupBox {{
                color: {brand.TEXT}; border: 1px solid {brand.BORDER};
                border-radius: 8px; padding-top: 12px; margin-top: 8px;
                font-weight: bold;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        # Kod + Ad bilgi
        info = QLabel(
            f"<b style='font-size:14px;'>{self.modul['ad']}</b><br>"
            f"<span style='color:{brand.TEXT_DIM}; font-size:11px;'>"
            f"Kod: <code>{self.modul['kod']}</code>"
            + (" · <b style='color:#F59E0B;'>ZORUNLU</b>" if self.modul.get('zorunlu') else "")
            + "</span>"
        )
        info.setTextFormat(Qt.RichText)
        lay.addWidget(info)

        grp = QGroupBox("Lisans Durumu")
        form = QFormLayout()
        form.setSpacing(10)

        self.chk_aktif = QCheckBox("Modül aktif")
        self.chk_aktif.setChecked(self.modul.get('aktif', True))
        if self.modul.get('zorunlu'):
            self.chk_aktif.setEnabled(False)
            self.chk_aktif.setToolTip("Zorunlu modüller pasifleştirilemez")
        form.addRow("Durum:", self.chk_aktif)

        self.dt_bitis = QDateEdit()
        self.dt_bitis.setCalendarPopup(True)
        self.dt_bitis.setSpecialValueText("Süresiz")
        self.dt_bitis.setMinimumDate(QDate(2000, 1, 1))
        self.dt_bitis.setDate(self.dt_bitis.minimumDate())  # default: süresiz
        if self.modul.get('zorunlu'):
            self.dt_bitis.setEnabled(False)
        form.addRow("Bitiş Tarihi:", self.dt_bitis)

        self.chk_sinirsiz = QCheckBox("Süresiz (bitiş tarihi yok)")
        self.chk_sinirsiz.setChecked(True)
        self.chk_sinirsiz.stateChanged.connect(
            lambda s: self.dt_bitis.setEnabled(not bool(s) and not self.modul.get('zorunlu'))
        )
        form.addRow("", self.chk_sinirsiz)

        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(80)
        self.txt_notlar.setPlaceholderText("Lisans notu, sözleşme no, vs. (opsiyonel)")
        form.addRow("Notlar:", self.txt_notlar)

        grp.setLayout(form)
        lay.addWidget(grp)

        lay.addStretch()

        # Butonlar
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet(f"""
            QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT};
                          border: 1px solid {brand.BORDER}; border-radius: 6px;
                          padding: 10px 18px; }}
        """)
        btn_iptal.clicked.connect(self.reject)
        btn_row.addWidget(btn_iptal)

        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet(f"""
            QPushButton {{ background: {brand.PRIMARY}; color: white;
                          border: none; border-radius: 6px;
                          padding: 10px 22px; font-weight: bold; }}
        """)
        btn_kaydet.clicked.connect(self._kaydet)
        btn_row.addWidget(btn_kaydet)

        lay.addLayout(btn_row)

    def _fill(self):
        bitis = self.modul.get('bitis_tarihi')
        if bitis and isinstance(bitis, datetime):
            self.dt_bitis.setDate(QDate(bitis.year, bitis.month, bitis.day))
            self.chk_sinirsiz.setChecked(False)
            if not self.modul.get('zorunlu'):
                self.dt_bitis.setEnabled(True)
        notlar = self.modul.get('notlar') or ''
        self.txt_notlar.setPlainText(notlar)

    def _kaydet(self):
        aktif = self.chk_aktif.isChecked()
        bitis: Optional[datetime] = None
        if not self.chk_sinirsiz.isChecked():
            qd = self.dt_bitis.date()
            bitis = datetime(qd.year(), qd.month(), qd.day(), 23, 59, 59)
        notlar = self.txt_notlar.toPlainText().strip() or None

        try:
            ModulServisi.instance().durum_guncelle(
                modul_kodu=self.modul['kod'],
                aktif=aktif,
                bitis_tarihi=bitis,
                notlar=notlar,
            )
            try:
                LogManager.log_update(
                    'sistem', 'lisans.modul_durumlari', self.modul['kod'],
                    f"{self.modul['ad']} -> aktif={aktif}, bitis={bitis}"
                )
            except Exception:
                pass
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt başarısız:\n{e}")


# ============================================================================
# ANA SAYFA
# ============================================================================

class SistemModulLisansPage(BasePage):
    """Sistem > Modül Yönetimi"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self.theme = theme
        self._setup_ui()
        self._yukle()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("🔑 Modül Yönetimi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {brand.TEXT};")
        header.addWidget(title)
        header.addStretch()

        self.durum_label = QLabel("")
        self.durum_label.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px; margin-right: 14px;")
        header.addWidget(self.durum_label)

        btn_yenile = QPushButton("🔄 Yenile")
        btn_yenile.setStyleSheet(self._btn_stil())
        btn_yenile.clicked.connect(self._yukle)
        header.addWidget(btn_yenile)

        layout.addLayout(header)

        # Uyari cercevesi
        uyari = QLabel(
            "⚠ Granülerlik: Ana modül seviyesindedir. Kapatılan modülün tüm alt sayfaları gizlenir. "
            "Zorunlu modüller (Dashboard, Tanımlar, Sistem) kapatılamaz. "
            "Bitiş tarihi geçmiş modül otomatik pasif sayılır."
        )
        uyari.setWordWrap(True)
        uyari.setStyleSheet(f"""
            background: {brand.BG_CARD}; color: {brand.TEXT_DIM};
            border: 1px solid {brand.BORDER}; border-radius: 8px;
            padding: 10px 14px; font-size: 12px;
        """)
        layout.addWidget(uyari)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Kod", "Modül Adı", "Kategori", "Durum", "Bitiş", "Notlar", "İşlem"
        ])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(5, QHeaderView.Stretch)  # Notlar esne
        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(6, 90)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {brand.BG_CARD}; border: 1px solid {brand.BORDER};
                border-radius: 8px; gridline-color: {brand.BORDER};
                color: {brand.TEXT};
            }}
            QHeaderView::section {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                padding: 8px; border: none; font-weight: bold;
            }}
            QTableWidget::item:selected {{
                background: {brand.PRIMARY_SOFT}; color: {brand.TEXT};
            }}
        """)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.doubleClicked.connect(lambda: self._duzenle())
        layout.addWidget(self.table, 1)

    def _btn_stil(self) -> str:
        return f"""
            QPushButton {{
                background: {brand.BG_INPUT}; color: {brand.TEXT};
                border: 1px solid {brand.BORDER}; border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: {brand.BG_HOVER}; }}
        """

    def _yukle(self):
        servis = ModulServisi.instance()
        servis.yenile()
        moduller = servis.tumunu_getir()

        self.table.setRowCount(0)
        aktif_sayisi = 0
        for m in moduller:
            r = self.table.rowCount()
            self.table.insertRow(r)

            # 0: kod
            it = QTableWidgetItem(m['kod'])
            it.setData(Qt.UserRole, m)
            self.table.setItem(r, 0, it)

            # 1: ad
            self.table.setItem(r, 1, QTableWidgetItem(m.get('ad', '')))

            # 2: kategori
            self.table.setItem(r, 2, QTableWidgetItem(m.get('kategori') or '-'))

            # 3: durum badge (aktif/pasif/zorunlu)
            durum_text, durum_bg = self._durum_rozet(m)
            it_d = QTableWidgetItem(durum_text)
            it_d.setTextAlignment(Qt.AlignCenter)
            it_d.setBackground(QColor(durum_bg))
            it_d.setForeground(QColor('#FFFFFF'))
            self.table.setItem(r, 3, it_d)
            if m.get('aktif', False):
                aktif_sayisi += 1

            # 4: bitis
            bitis = m.get('bitis_tarihi')
            bitis_txt = bitis.strftime('%d.%m.%Y') if isinstance(bitis, datetime) else 'Süresiz'
            self.table.setItem(r, 4, QTableWidgetItem(bitis_txt))

            # 5: notlar
            self.table.setItem(r, 5, QTableWidgetItem(m.get('notlar') or ''))

            # 6: duzenle butonu
            btn = QPushButton("Düzenle")
            if m.get('zorunlu'):
                btn.setText("🔒 Zorunlu")
                btn.setEnabled(False)
                btn.setToolTip("Zorunlu modüller pasifleştirilemez")
                btn.setStyleSheet(f"""
                    QPushButton {{ background: {brand.BG_HOVER}; color: {brand.TEXT_DIM};
                                  border: 1px solid {brand.BORDER}; border-radius: 4px;
                                  padding: 4px 10px; }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{ background: {brand.PRIMARY}; color: white;
                                  border: none; border-radius: 4px;
                                  padding: 4px 10px; font-weight: bold; }}
                    QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
                """)
                btn.clicked.connect(lambda _c=False, kod=m['kod']: self._duzenle(kod))
            w = QWidget()
            wl = QHBoxLayout(w)
            wl.setContentsMargins(2, 2, 2, 2)
            wl.addWidget(btn)
            self.table.setCellWidget(r, 6, w)

        self.durum_label.setText(f"{aktif_sayisi} aktif / {len(moduller)} toplam")

    def _durum_rozet(self, m: dict) -> tuple:
        bitis = m.get('bitis_tarihi')
        suresi_gecmis = (
            isinstance(bitis, datetime) and bitis < datetime.now()
        )
        if m.get('zorunlu'):
            return ("ZORUNLU", brand.INFO)
        if suresi_gecmis:
            return ("SÜRE DOLMUŞ", brand.WARNING)
        if m.get('aktif', False):
            return ("✓ AKTİF", brand.SUCCESS)
        return ("✗ PASİF", brand.ERROR)

    def _duzenle(self, kod: Optional[str] = None):
        if kod is None:
            r = self.table.currentRow()
            if r < 0:
                return
            it = self.table.item(r, 0)
            if not it:
                return
            kod = it.text()

        m = ModulServisi.instance().getir(kod)
        if m is None:
            return
        if m.get('zorunlu'):
            QMessageBox.information(
                self, "Zorunlu Modül",
                f"'{m['ad']}' zorunlu bir modüldür, pasifleştirilemez."
            )
            return

        dlg = ModulDurumDialog(m, self.theme, self)
        if dlg.exec() == QDialog.Accepted:
            self._yukle()
            self._sidebar_yenile()

    def _sidebar_yenile(self):
        """
        Sidebar'ı yeniden oluştur - değişiklik anında görünür olsun.
        Main window'daki sidebar'a ulaşmak için üst widget'ı aramakça.
        """
        try:
            parent = self.window()
            if parent and hasattr(parent, 'sidebar'):
                sb = parent.sidebar
                if hasattr(sb, '_build_menu'):
                    # Mevcut item'ları temizle
                    if hasattr(sb, 'menu_items'):
                        for it in list(sb.menu_items.values()):
                            it.setParent(None)
                            it.deleteLater()
                        sb.menu_items.clear()
                    if hasattr(sb, 'child_containers'):
                        for c in list(sb.child_containers.values()):
                            c.setParent(None)
                            c.deleteLater()
                        sb.child_containers.clear()
                    sb._build_menu()
        except Exception:
            # Sidebar yenileme kritik degil - kullanici F5 yapabilir
            pass
