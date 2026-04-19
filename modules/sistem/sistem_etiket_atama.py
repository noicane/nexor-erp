# -*- coding: utf-8 -*-
"""
NEXOR ERP - Etiket Sablon Atamalari Sekmesi
============================================
Sistem > Firma Ayarlari > 📄 Etiket Sablonlari

Her kullanim yerine (kalite_final, depo_giris vb.) bir etiket sablonu,
kopya adedi ve otomatik bas tercihi atanir. GLOBAL ayar - tum PC'lere uygulanir.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QSpinBox,
    QCheckBox, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt

from core.database import get_db_connection
from core.nexor_brand import brand
from core import etiket_servisi as svc


class SistemEtiketAtamaTab(QWidget):
    """Etiket Sablon Atamalari sekmesi"""

    def __init__(self, theme: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme or {}
        self._sablonlar = []  # tanim.etiket_sablonlari listesi
        self.setMinimumWidth(920)  # Kaymaya karsi onlem
        self._setup_ui()
        self._load_sablonlar()
        self._load_table()

    # ------------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header / aciklama
        info_frame = QFrame()
        info_frame.setStyleSheet(
            f"background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 12px;"
        )
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 14, 20, 14)

        icon_lbl = QLabel("📄")
        icon_lbl.setStyleSheet("font-size: 24px; background: transparent;")
        info_layout.addWidget(icon_lbl)

        info_text = QVBoxLayout()
        title = QLabel("Etiket Sablonlari")
        title.setStyleSheet(
            f"color: {brand.TEXT}; font-size: 18px; font-weight: bold;"
        )
        info_text.addWidget(title)
        sub = QLabel(
            "Her kullanim yerine bir etiket sablonu, kopya adedi ve otomatik bas "
            "tercihi atayin. Bu ayarlar TUM PC'lere uygulanir."
        )
        sub.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: 12px;")
        sub.setWordWrap(True)
        info_text.addWidget(sub)
        info_layout.addLayout(info_text, 1)
        layout.addWidget(info_frame)

        # Tablo - sabit kolon genisligi ile yatay kaymalardan koruma
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Kullanim Yeri", "Etiket Sablonu", "Kopya", "Otomatik Bas", "Durum"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)  # Secim yok - vurgulama kaymasin
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setMinimumWidth(880)  # Kaymayi onler
        self.table.setMinimumHeight(420)
        self.table.setStyleSheet(
            f"QTableWidget {{ background: {brand.BG_CARD}; "
            f"color: {brand.TEXT}; "
            f"gridline-color: {brand.BORDER}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 8px; }}"
            f"QTableWidget::item {{ padding: 6px 10px; }}"
            f"QHeaderView::section {{ background: {brand.BG_INPUT}; "
            f"color: {brand.TEXT}; "
            f"padding: 10px 8px; border: none; "
            f"border-bottom: 1px solid {brand.BORDER}; "
            f"font-weight: bold; font-size: 13px; }}"
        )

        h = self.table.horizontalHeader()
        h.setMinimumSectionSize(80)
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QHeaderView.Interactive)  # Kullanim yeri
        h.setSectionResizeMode(1, QHeaderView.Stretch)       # Sablon (kalani al)
        h.setSectionResizeMode(2, QHeaderView.Fixed)         # Kopya
        h.setSectionResizeMode(3, QHeaderView.Fixed)         # Otomatik
        h.setSectionResizeMode(4, QHeaderView.Fixed)         # Durum
        self.table.setColumnWidth(0, 240)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 110)

        # Satir yuksekligi - combo/spinbox sigacak
        self.table.verticalHeader().setDefaultSectionSize(44)
        layout.addWidget(self.table, 1)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_yenile = QPushButton("🔄  Yenile")
        self.btn_yenile.setCursor(Qt.PointingHandCursor)
        self.btn_yenile.setStyleSheet(self._normal_btn_style())
        self.btn_yenile.clicked.connect(self._load_table)
        btn_layout.addWidget(self.btn_yenile)

        btn_layout.addStretch()

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
        btn_layout.addWidget(self.btn_kaydet)
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    def _normal_btn_style(self) -> str:
        return (
            f"QPushButton {{ background: {brand.BG_INPUT}; "
            f"color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 8px; "
            f"padding: 10px 16px; font-size: 13px; }}"
            f"QPushButton:hover {{ border-color: {brand.PRIMARY}; "
            f"background: {brand.BG_HOVER}; }}"
        )

    # ------------------------------------------------------------------
    def _load_sablonlar(self):
        """tanim.etiket_sablonlari listesini cek"""
        self._sablonlar = []
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, sablon_kodu, sablon_adi, ISNULL(varsayilan_mi, 0)
                    FROM tanim.etiket_sablonlari
                    WHERE aktif_mi = 1
                    ORDER BY varsayilan_mi DESC, sablon_adi
                """)
                for r in cursor.fetchall():
                    self._sablonlar.append({
                        'id': r[0], 'kod': r[1] or '',
                        'ad': r[2] or '', 'varsayilan': bool(r[3])
                    })
        except Exception as e:
            print(f"[SistemEtiketAtamaTab] Sablon yukleme hatasi: {e}")

    # ------------------------------------------------------------------
    def _load_table(self):
        """Tabloyu KULLANIM_YERLERI'ne gore satir doldur, mevcut kayitlari oku"""
        atamalar = {a['kullanim_yeri']: a for a in svc.list_sablon_atamalari()}

        rows = list(svc.KULLANIM_YERLERI.items())
        self.table.setRowCount(len(rows))

        for row_idx, (yer_key, yer_label) in enumerate(rows):
            mevcut = atamalar.get(yer_key)

            # Col 0: Kullanim yeri (label)
            item = QTableWidgetItem(yer_label)
            item.setData(Qt.UserRole, yer_key)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 0, item)

            # Col 1: Sablon combo
            combo = QComboBox()
            combo.addItem("(Sablon secilmemis)", None)
            for s in self._sablonlar:
                prefix = "⭐ " if s['varsayilan'] else ""
                combo.addItem(f"{prefix}{s['ad']} [{s['kod']}]", s['id'])

            if mevcut and mevcut['sablon_id']:
                for i in range(combo.count()):
                    if combo.itemData(i) == mevcut['sablon_id']:
                        combo.setCurrentIndex(i)
                        break
            combo.setStyleSheet(
                f"QComboBox {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
                f"border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 4px 8px; }}"
            )
            self.table.setCellWidget(row_idx, 1, combo)

            # Col 2: Kopya
            spin = QSpinBox()
            spin.setRange(1, 99)
            spin.setValue(mevcut['kopya_adedi'] if mevcut else 1)
            spin.setStyleSheet(
                f"QSpinBox {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
                f"border: 1px solid {brand.BORDER}; border-radius: 6px; padding: 4px; }}"
            )
            self.table.setCellWidget(row_idx, 2, spin)

            # Col 3: Otomatik bas (buyuk, net checkbox)
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk_layout.setAlignment(Qt.AlignCenter)
            chk = QCheckBox()
            chk.setChecked(mevcut['otomatik_bas'] if mevcut else True)
            success_color = getattr(brand, 'SUCCESS', '#22c55e')
            chk.setStyleSheet(f"""
                QCheckBox::indicator {{
                    width: 22px; height: 22px;
                    border-radius: 4px;
                    border: 2px solid {brand.BORDER};
                    background: {brand.BG_INPUT};
                }}
                QCheckBox::indicator:checked {{
                    background: {success_color};
                    border-color: {success_color};
                }}
                QCheckBox::indicator:hover {{ border-color: {brand.PRIMARY}; }}
            """)
            chk_layout.addWidget(chk)
            self.table.setCellWidget(row_idx, 3, chk_widget)

            # Col 4: Durum
            if mevcut and mevcut['sablon_id']:
                durum = "✓ Tanimli"
                text_color = success_color
            else:
                durum = "— Eksik"
                text_color = brand.TEXT_MUTED
            durum_lbl = QLabel(durum)
            durum_lbl.setAlignment(Qt.AlignCenter)
            durum_lbl.setStyleSheet(
                f"color: {text_color}; font-weight: bold; background: transparent;"
            )
            self.table.setCellWidget(row_idx, 4, durum_lbl)

    # ------------------------------------------------------------------
    def _save_all(self):
        """Tum satirlari MERGE ile kaydet"""
        basarili = 0
        hatali = 0
        for row_idx in range(self.table.rowCount()):
            yer_item = self.table.item(row_idx, 0)
            if not yer_item:
                continue
            yer_key = yer_item.data(Qt.UserRole)

            sablon_combo: QComboBox = self.table.cellWidget(row_idx, 1)
            kopya_spin: QSpinBox = self.table.cellWidget(row_idx, 2)
            chk_widget: QWidget = self.table.cellWidget(row_idx, 3)
            chk = chk_widget.findChild(QCheckBox) if chk_widget else None

            sablon_id = sablon_combo.currentData() if sablon_combo else None
            kopya = kopya_spin.value() if kopya_spin else 1
            otomatik = chk.isChecked() if chk else True

            ok = svc.upsert_sablon_atama(
                kullanim_yeri=yer_key,
                sablon_id=sablon_id,
                kopya_adedi=kopya,
                otomatik_bas=otomatik,
                aciklama=svc.KULLANIM_YERLERI.get(yer_key, ''),
            )
            if ok:
                basarili += 1
            else:
                hatali += 1

        if hatali == 0:
            QMessageBox.information(
                self, "Kaydedildi",
                f"{basarili} kullanim yeri icin sablon atamalari kaydedildi."
            )
        else:
            QMessageBox.warning(
                self, "Kismi Basari",
                f"{basarili} kayit basarili, {hatali} kayit hatali.\n"
                "Detaylar icin konsolu kontrol edin."
            )
        self._load_table()
