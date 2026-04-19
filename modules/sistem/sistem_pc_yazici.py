# -*- coding: utf-8 -*-
"""
NEXOR ERP - PC Yazici Atamalari Sekmesi
========================================
Sistem > Firma Ayarlari > 🖨️ PC Yazici Atamalari

Her bilgisayar (COMPUTERNAME) icin kullanim yeri bazinda yazici atanir.
Cok PC + cok yazici senaryosu icin (5 farkli PC'de 5 farkli Godex).

UX:
- Ust: "Bu Bilgisayar: PC-XX" + "Bu PC icin Hizli Ekle" butonu (KULLANIM_YERLERI'ni
  current PC'ye otomatik satirlasir)
- Tablo: PC | Aciklama | Kullanim Yeri | Yazici | Format | Test | Sil
- Alt: + Yeni Satir, Kaydet, Yenile
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit,
    QMessageBox, QAbstractItemView, QInputDialog
)
from PySide6.QtCore import Qt

from core.nexor_brand import brand
from core import etiket_servisi as svc


def _get_windows_yazicilar() -> list:
    """Yerel Windows yazicilarini al (combo dropdown icin)"""
    try:
        from utils.etiket_yazdir1 import get_available_printers
        return get_available_printers() or []
    except Exception as e:
        print(f"[PCYazici] Yazici listesi alinamadi: {e}")
        return []


class SistemPCYaziciTab(QWidget):
    """PC Yazici Atamalari sekmesi"""

    def __init__(self, theme: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme or {}
        self._silinen_ids = []  # Kaydedilirken silinecek id'ler
        self._win_printers = _get_windows_yazicilar()
        self.setMinimumWidth(1060)  # Kaymaya karsi onlem (7 kolon)
        self._setup_ui()
        self._load_table()

    # ------------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # === Header (info + bu PC) ===
        header = QFrame()
        header.setStyleSheet(
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 12px;"
        )
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 14, 20, 14)
        h_layout.setSpacing(14)

        icon = QLabel("🖨️")
        icon.setStyleSheet("font-size: 24px; background: transparent;")
        h_layout.addWidget(icon)

        info = QVBoxLayout()
        title = QLabel("PC Yazici Atamalari")
        title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: 18px; font-weight: bold;"
        )
        info.addWidget(title)
        sub = QLabel(
            "Her bilgisayara kullanim yeri bazinda yazici atayin. "
            "Bu ayar PC-bazlidir, her makinenin kendi yazicisi olur."
        )
        sub.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: 12px;")
        sub.setWordWrap(True)
        info.addWidget(sub)
        h_layout.addLayout(info, 1)

        # Bu PC bilgisi
        pc_box = QFrame()
        pc_box.setStyleSheet(
            f"background: {brand.BG_INPUT}; "
            f"border: 1px solid {brand.PRIMARY}; border-radius: 8px;"
        )
        pc_layout = QVBoxLayout(pc_box)
        pc_layout.setContentsMargins(14, 8, 14, 8)
        pc_layout.setSpacing(2)
        pc_lbl1 = QLabel("Bu Bilgisayar")
        pc_lbl1.setStyleSheet(
            f"color: {brand.TEXT_MUTED}; font-size: 11px;"
        )
        pc_layout.addWidget(pc_lbl1)
        pc_name = QLabel(svc.get_pc_adi())
        pc_name.setStyleSheet(
            f"color: {brand.PRIMARY}; font-size: 14px; font-weight: bold;"
        )
        pc_layout.addWidget(pc_name)
        h_layout.addWidget(pc_box)

        layout.addWidget(header)

        # === Filtreler ve aksiyon butonlari ===
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        toolbar.addWidget(QLabel("Filtre:"))
        self.cmb_filter_pc = QComboBox()
        self.cmb_filter_pc.setMinimumWidth(200)
        self.cmb_filter_pc.setStyleSheet(self._combo_css())
        self.cmb_filter_pc.currentIndexChanged.connect(self._load_table)
        toolbar.addWidget(self.cmb_filter_pc)

        toolbar.addStretch()

        self.btn_quick = QPushButton("⚡  Bu PC icin Hizli Ekle")
        self.btn_quick.setCursor(Qt.PointingHandCursor)
        self.btn_quick.setStyleSheet(self._normal_btn_css())
        self.btn_quick.setToolTip(
            "Tum kullanim yerleri icin bu PC'ye satir ekler. "
            "Yazici seciminin tamamlanmasi gerekir."
        )
        self.btn_quick.clicked.connect(self._quick_setup_this_pc)
        toolbar.addWidget(self.btn_quick)

        self.btn_yeni = QPushButton("+ Yeni Atama")
        self.btn_yeni.setCursor(Qt.PointingHandCursor)
        self.btn_yeni.setStyleSheet(self._normal_btn_css())
        self.btn_yeni.clicked.connect(self._add_empty_row)
        toolbar.addWidget(self.btn_yeni)

        layout.addLayout(toolbar)

        # === Tablo - sabit kolonlar, yatay scroll ===
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Bilgisayar", "Aciklama", "Kullanim Yeri",
            "Yazici", "Format", "Test", "Sil"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setMinimumWidth(1020)  # 7 kolona sigacak minimum
        self.table.setMinimumHeight(380)
        self.table.setStyleSheet(
            f"QTableWidget {{ background: {brand.BG_CARD}; "
            f"color: {brand.TEXT}; gridline-color: {brand.BORDER}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 8px; }}"
            f"QTableWidget::item {{ padding: 4px 8px; }}"
            f"QHeaderView::section {{ background: {brand.BG_INPUT}; "
            f"color: {brand.TEXT}; padding: 10px 8px; border: none; "
            f"border-bottom: 1px solid {brand.BORDER}; "
            f"font-weight: bold; font-size: 13px; }}"
        )
        h = self.table.horizontalHeader()
        h.setMinimumSectionSize(60)
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QHeaderView.Interactive)  # Bilgisayar
        h.setSectionResizeMode(1, QHeaderView.Stretch)       # Aciklama
        h.setSectionResizeMode(2, QHeaderView.Interactive)  # Kullanim yeri
        h.setSectionResizeMode(3, QHeaderView.Stretch)       # Yazici
        h.setSectionResizeMode(4, QHeaderView.Fixed)         # Format
        h.setSectionResizeMode(5, QHeaderView.Fixed)         # Test
        h.setSectionResizeMode(6, QHeaderView.Fixed)         # Sil
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 60)

        self.table.verticalHeader().setDefaultSectionSize(44)
        layout.addWidget(self.table, 1)

        # === Alt buton bar ===
        bottom = QHBoxLayout()
        bottom.addStretch()

        self.btn_yenile = QPushButton("🔄  Yenile")
        self.btn_yenile.setCursor(Qt.PointingHandCursor)
        self.btn_yenile.setStyleSheet(self._normal_btn_css())
        self.btn_yenile.clicked.connect(self._reload_all)
        bottom.addWidget(self.btn_yenile)

        self.btn_kaydet = QPushButton("💾  Tumunu Kaydet")
        self.btn_kaydet.setCursor(Qt.PointingHandCursor)
        self.btn_kaydet.setFixedHeight(40)
        self.btn_kaydet.setMinimumWidth(180)
        self.btn_kaydet.setStyleSheet(
            f"QPushButton {{ background: {brand.PRIMARY}; "
            f"color: white; border: none; border-radius: 8px; "
            f"padding: 10px 24px; font-weight: bold; font-size: 13px; }}"
            f"QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}"
        )
        self.btn_kaydet.clicked.connect(self._save_all)
        bottom.addWidget(self.btn_kaydet)

        layout.addLayout(bottom)

    # ------------------------------------------------------------------
    def _combo_css(self) -> str:
        return (
            f"QComboBox {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 6px; "
            f"padding: 4px 8px; }}"
        )

    def _input_css(self) -> str:
        return (
            f"QLineEdit {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 6px; "
            f"padding: 4px 8px; }}"
        )

    def _normal_btn_css(self) -> str:
        return (
            f"QPushButton {{ background: {brand.BG_INPUT}; "
            f"color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 8px; "
            f"padding: 8px 14px; font-size: 13px; }}"
            f"QPushButton:hover {{ border-color: {brand.PRIMARY}; "
            f"background: {brand.BG_HOVER}; }}"
        )

    # ------------------------------------------------------------------
    def _reload_all(self):
        self._silinen_ids.clear()
        self._load_table()

    def _load_table(self):
        """Tabloyu DB'den oku ve doldur"""
        # Filter combo
        self.cmb_filter_pc.blockSignals(True)
        self.cmb_filter_pc.clear()
        self.cmb_filter_pc.addItem("Tum Bilgisayarlar", None)
        for pc in svc.list_distinct_pcler():
            label = f"{pc['bilgisayar_adi']}"
            if pc['pc_aciklama']:
                label += f" — {pc['pc_aciklama']}"
            self.cmb_filter_pc.addItem(label, pc['bilgisayar_adi'])
        self.cmb_filter_pc.blockSignals(False)

        secili_pc = self.cmb_filter_pc.currentData()
        rows = svc.list_pc_yazici_atamalari(bilgisayar_adi=secili_pc)

        self.table.setRowCount(0)
        for r in rows:
            self._add_row(
                pc=r['bilgisayar_adi'],
                aciklama=r['pc_aciklama'],
                kullanim_yeri=r['kullanim_yeri'],
                yazici=r['yazici_adi'],
                format_tipi=r['format_tipi'],
                row_id=r['id'],
            )

    # ------------------------------------------------------------------
    def _add_row(self, pc: str = '', aciklama: str = '',
                 kullanim_yeri: str = '', yazici: str = '',
                 format_tipi: str = svc.DEFAULT_FORMAT,
                 row_id=None):
        """Tabloya bir satir ekle. row_id varsa varolan kaydi gosterir."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Col 0: PC adi (lineedit)
        pc_edit = QLineEdit(pc or svc.get_pc_adi())
        pc_edit.setStyleSheet(self._input_css())
        self.table.setCellWidget(row, 0, pc_edit)

        # Col 1: Aciklama (lineedit)
        ac_edit = QLineEdit(aciklama or '')
        ac_edit.setPlaceholderText("Ornek: Final Kalite Masasi")
        ac_edit.setStyleSheet(self._input_css())
        self.table.setCellWidget(row, 1, ac_edit)

        # Col 2: Kullanim yeri combo
        kul_combo = QComboBox()
        for k, v in svc.KULLANIM_YERLERI.items():
            kul_combo.addItem(v, k)
        if kullanim_yeri:
            for i in range(kul_combo.count()):
                if kul_combo.itemData(i) == kullanim_yeri:
                    kul_combo.setCurrentIndex(i)
                    break
        kul_combo.setStyleSheet(self._combo_css())
        self.table.setCellWidget(row, 2, kul_combo)

        # Col 3: Yazici (editable combo - listeden sec veya elle yaz)
        yaz_combo = QComboBox()
        yaz_combo.setEditable(True)
        for p in self._win_printers:
            yaz_combo.addItem(p)
        if yazici:
            yaz_combo.setCurrentText(yazici)
        yaz_combo.setStyleSheet(self._combo_css())
        self.table.setCellWidget(row, 3, yaz_combo)

        # Col 4: Format (EZPL/ZPL/PDF)
        fmt_combo = QComboBox()
        for f in svc.FORMAT_TIPLERI:
            fmt_combo.addItem(f, f)
        for i in range(fmt_combo.count()):
            if fmt_combo.itemData(i) == (format_tipi or svc.DEFAULT_FORMAT):
                fmt_combo.setCurrentIndex(i)
                break
        fmt_combo.setStyleSheet(self._combo_css())
        self.table.setCellWidget(row, 4, fmt_combo)

        # Col 5: Test butonu
        test_btn = QPushButton("🧪")
        test_btn.setCursor(Qt.PointingHandCursor)
        test_btn.setToolTip("Bu yazici icin test etiketi bas")
        test_btn.setFixedSize(36, 32)
        test_btn.setStyleSheet(self._normal_btn_css())
        test_btn.clicked.connect(lambda _=False, r=row: self._test_row(r))
        test_widget = QWidget()
        test_lay = QHBoxLayout(test_widget)
        test_lay.setContentsMargins(0, 0, 0, 0)
        test_lay.setAlignment(Qt.AlignCenter)
        test_lay.addWidget(test_btn)
        self.table.setCellWidget(row, 5, test_widget)

        # Col 6: Sil butonu
        del_btn = QPushButton("🗑️")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setToolTip("Satiri sil")
        del_btn.setFixedSize(36, 32)
        del_btn.setStyleSheet(self._normal_btn_css())
        del_btn.clicked.connect(lambda _=False, b=del_btn: self._delete_row(b))
        del_widget = QWidget()
        del_lay = QHBoxLayout(del_widget)
        del_lay.setContentsMargins(0, 0, 0, 0)
        del_lay.setAlignment(Qt.AlignCenter)
        del_lay.addWidget(del_btn)
        self.table.setCellWidget(row, 6, del_widget)

        # Row id (edit/insert ayrimi icin)
        item = QTableWidgetItem("")
        item.setData(Qt.UserRole, row_id)
        self.table.setVerticalHeaderItem(row, item)

    # ------------------------------------------------------------------
    def _add_empty_row(self):
        self._add_row(pc=svc.get_pc_adi())

    def _quick_setup_this_pc(self):
        """Bu PC icin tum KULLANIM_YERLERI satirlarini otomatik olustur"""
        bu_pc = svc.get_pc_adi()
        mevcut = svc.list_pc_yazici_atamalari(bilgisayar_adi=bu_pc)
        mevcut_yerler = {a['kullanim_yeri'] for a in mevcut}

        eksik = [(k, v) for k, v in svc.KULLANIM_YERLERI.items() if k not in mevcut_yerler]
        if not eksik:
            QMessageBox.information(
                self, "Bilgi",
                f"{bu_pc} icin tum kullanim yerleri zaten tanimli."
            )
            return

        # Aciklama sor (opsiyonel)
        aciklama, ok = QInputDialog.getText(
            self, "PC Aciklamasi",
            f"Bu PC ({bu_pc}) icin aciklama (opsiyonel):",
            text="" if not mevcut else (mevcut[0].get('pc_aciklama') or '')
        )
        if not ok:
            return

        # Eksik yerler icin satir ekle
        for k, _ in eksik:
            self._add_row(
                pc=bu_pc,
                aciklama=aciklama,
                kullanim_yeri=k,
                yazici='',
                format_tipi=svc.DEFAULT_FORMAT,
            )

        QMessageBox.information(
            self, "Hazir",
            f"{len(eksik)} adet bos satir eklendi.\n"
            "Her satir icin yaziciyi secin ve KAYDET'e basin."
        )

    # ------------------------------------------------------------------
    def _delete_row(self, button: QPushButton):
        """Sil butonu icin: ilgili satiri bulup sil"""
        for row in range(self.table.rowCount()):
            del_widget = self.table.cellWidget(row, 6)
            if del_widget and button in del_widget.findChildren(QPushButton):
                # Mevcut bir kayit ise silinecekler listesine ekle
                vh_item = self.table.verticalHeaderItem(row)
                row_id = vh_item.data(Qt.UserRole) if vh_item else None
                if row_id:
                    self._silinen_ids.append(row_id)
                self.table.removeRow(row)
                return

    def _test_row(self, row: int):
        """Test etiketi bas"""
        yaz_combo: QComboBox = self.table.cellWidget(row, 3)
        fmt_combo: QComboBox = self.table.cellWidget(row, 4)
        if not yaz_combo or not fmt_combo:
            return

        yazici = yaz_combo.currentText().strip()
        if not yazici:
            QMessageBox.warning(self, "Uyari", "Once yazici secin.")
            return

        format_tipi = fmt_combo.currentData() or svc.DEFAULT_FORMAT

        ok = svc.EtiketServisi.test_yazici(yazici, format_tipi)
        if ok:
            QMessageBox.information(
                self, "Test",
                f"Test etiketi gonderildi:\n{yazici} ({format_tipi})"
            )
        else:
            QMessageBox.warning(
                self, "Test Hatasi",
                f"Test etiketi gonderilemedi:\n{yazici}\n\n"
                "Yazici aciksa ve baglandiysa kontrol edin."
            )

    # ------------------------------------------------------------------
    def _save_all(self):
        """Tum satirlari kaydet (silinenler dahil)"""
        # Once silinenleri sil
        for sid in self._silinen_ids:
            svc.delete_pc_yazici_atama(sid)
        self._silinen_ids.clear()

        # Sonra tum satirlari upsert et
        basarili = 0
        atlanan = 0
        gorulen = set()  # (pc, kullanim_yeri) duplicate kontrol

        for row in range(self.table.rowCount()):
            pc_edit: QLineEdit = self.table.cellWidget(row, 0)
            ac_edit: QLineEdit = self.table.cellWidget(row, 1)
            kul_combo: QComboBox = self.table.cellWidget(row, 2)
            yaz_combo: QComboBox = self.table.cellWidget(row, 3)
            fmt_combo: QComboBox = self.table.cellWidget(row, 4)

            pc = pc_edit.text().strip().upper() if pc_edit else ''
            aciklama = ac_edit.text().strip() if ac_edit else ''
            kullanim_yeri = kul_combo.currentData() if kul_combo else None
            yazici = yaz_combo.currentText().strip() if yaz_combo else ''
            format_tipi = fmt_combo.currentData() if fmt_combo else svc.DEFAULT_FORMAT

            # Eksik veri varsa atla
            if not pc or not kullanim_yeri or not yazici:
                atlanan += 1
                continue

            key = (pc, kullanim_yeri)
            if key in gorulen:
                atlanan += 1
                continue
            gorulen.add(key)

            ok = svc.upsert_pc_yazici_atama(
                bilgisayar_adi=pc,
                kullanim_yeri=kullanim_yeri,
                yazici_adi=yazici,
                format_tipi=format_tipi,
                pc_aciklama=aciklama,
            )
            if ok:
                basarili += 1

        msg = f"{basarili} kayit kaydedildi."
        if atlanan:
            msg += f"\n{atlanan} satir atlandi (eksik veri veya duplicate)."
        QMessageBox.information(self, "Kaydedildi", msg)

        # Tabloyu yeniden yukle
        self._load_table()
