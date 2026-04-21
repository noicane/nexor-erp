# -*- coding: utf-8 -*-
"""
NEXOR ERP - Gunluk Uretim Planlama

Akis:
    1. Tarih sec -> Olustur (stok.urunler'den gunluk_ihtiyac_adet > 0
       olan MAMUL urunlerden taslak satirlar uretir)
    2. Her satir: adet/bara_adedi = yapilacak_bara
                  plc_recete_tanimlari.toplam_sure_dk = bara sure
                  toplam_sure = bara_adedi x bara_sure
    3. Vardiyaya otomatik dagitim (kaplama turune gore)
    4. Kullanici duzenler
    5. Onayla -> siparis.is_emirleri + uretim.planlama yazilir,
                 sonrasinda personel atamasi acilir

Veri:
    planlama.gunluk_taslak (tarih, durum=TASLAK/ONAYLI)
    planlama.gunluk_taslak_satir (vardiya, urun, bara, sure, sira)
"""

import math
from datetime import date, datetime, time as _time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QSpinBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


HAT_COLOR = {
    'KATAFOREZ': ('rgba(16,185,129,0.15)', '#6EE7B7', 'KTL'),
    'KTF':       ('rgba(16,185,129,0.15)', '#6EE7B7', 'KTL'),
    'ZN':        ('rgba(59,130,246,0.15)', '#93C5FD', 'ZN'),
    'ZNNI':      ('rgba(59,130,246,0.15)', '#93C5FD', 'ZNNI'),
    'NIKEL':     ('rgba(139,92,246,0.15)', '#C4B5FD', 'NIKEL'),
    'TOZ':       ('rgba(245,158,11,0.15)', '#FCD34D', 'TOZ'),
    'ASITZN':    ('rgba(59,130,246,0.15)', '#93C5FD', 'ZN'),
    'KROM':      ('rgba(239,68,68,0.15)', '#FCA5A5', 'KROM'),
}


def _kap_color(kod: str) -> tuple:
    return HAT_COLOR.get((kod or '').upper(),
                         ('rgba(136,150,166,0.12)', brand.TEXT_DIM, '-'))


class GunlukPlanlamaPage(BasePage):
    """Gunluk Uretim Planlama - Taslak/Onay akisi"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._taslak_id = None
        self._durum = "TASLAK"
        self._satirlar = []   # dict listesi
        self._vardiyalar = []  # [(id, kod, ad, bas, bit)]

        self._load_vardiyalar()
        self._setup_ui()
        self._refresh()

    # ==================================================================
    # DB
    # ==================================================================
    def _load_vardiyalar(self):
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT id, kod, ad, baslangic_saati, bitis_saati
                FROM tanim.vardiyalar WHERE aktif_mi = 1
                ORDER BY baslangic_saati
            """)
            self._vardiyalar = [
                {'id': r[0], 'kod': r[1], 'ad': r[2],
                 'bas': r[3], 'bit': r[4]}
                for r in cur.fetchall()
            ]
            conn.close()
        except Exception as e:
            print(f"[GunlukPlan] vardiya hata: {e}")
            self._vardiyalar = []

    def _load_talepler(self) -> list:
        """Gunluk ihtiyaci dolu olan MAMUL urunleri getirir."""
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT u.id, u.urun_kodu, u.urun_adi,
                       u.cari_id, c.unvan as cari_unvan,
                       u.kaplama_turu_id, kt.kod as kap_kod, kt.ad as kap_ad,
                       u.recete_no,
                       ISNULL(r.toplam_sure_dk, 0) as recete_sure,
                       ISNULL(u.bara_adedi, 0) as bara_adedi,
                       ISNULL(u.gunluk_ihtiyac_adet, 0) as ihtiyac
                FROM stok.urunler u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                LEFT JOIN kaplama.plc_recete_tanimlari r ON TRY_CAST(u.recete_no AS INT) = r.recete_no
                WHERE u.aktif_mi = 1 AND u.urun_tipi = 'MAMUL'
                  AND u.gunluk_ihtiyac_adet IS NOT NULL AND u.gunluk_ihtiyac_adet > 0
                ORDER BY kt.kod, c.unvan, u.urun_kodu
            """)
            talepler = []
            for r in cur.fetchall():
                bara_adedi_kart = int(r[10] or 0)
                ihtiyac = int(r[11] or 0)
                recete_sure = int(r[9] or 0)

                # 1 barada parca sayisi = stok.urunler.bara_adedi
                # Yapilacak bara = ceil(ihtiyac / bara_adedi_kart)
                yapilacak_bara = math.ceil(ihtiyac / bara_adedi_kart) if bara_adedi_kart > 0 else 0
                toplam_dk = yapilacak_bara * recete_sure

                talepler.append({
                    'urun_id': int(r[0]),
                    'urun_kodu': r[1] or '',
                    'urun_adi': r[2] or '',
                    'cari_id': int(r[3]) if r[3] else None,
                    'cari_unvan': r[4] or '',
                    'kaplama_turu_id': int(r[5]) if r[5] else None,
                    'kap_kod': r[6] or '',
                    'kap_ad': r[7] or '',
                    'recete_no': r[8] or '',
                    'recete_sure_dk': recete_sure,
                    'bara_parca': bara_adedi_kart,
                    'ihtiyac_adet': ihtiyac,
                    'yapilacak_bara': yapilacak_bara,
                    'toplam_dk': toplam_dk,
                })
            conn.close()
            return talepler
        except Exception as e:
            print(f"[GunlukPlan] talep yukleme hata: {e}")
            import traceback; traceback.print_exc()
            return []

    def _taslak_bul_veya_olustur(self, tarih: date, olustur_mu: bool) -> int:
        """Verilen tarih icin taslak id doner. yoksa olustur_mu=True ise olusturur."""
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT TOP 1 id, durum FROM planlama.gunluk_taslak
                WHERE tarih = ? AND silindi_mi = 0
                ORDER BY id DESC
            """, (tarih,))
            row = cur.fetchone()
            if row:
                self._durum = row[1] or 'TASLAK'
                conn.close()
                return int(row[0])

            if not olustur_mu:
                conn.close()
                return None

            cur.execute("""
                INSERT INTO planlama.gunluk_taslak (tarih, durum)
                OUTPUT INSERTED.id VALUES (?, 'TASLAK')
            """, (tarih,))
            new_id = int(cur.fetchone()[0])
            conn.commit()
            self._durum = 'TASLAK'
            conn.close()
            return new_id
        except Exception as e:
            print(f"[GunlukPlan] taslak bul/olustur hata: {e}")
            return None

    def _satirlari_yukle(self, taslak_id: int) -> list:
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT s.id, s.vardiya_id, v.kod as vardiya_kod,
                       s.urun_id, u.urun_kodu, u.urun_adi,
                       s.cari_id, c.unvan as cari_unvan,
                       s.kaplama_turu_id, kt.kod as kap_kod,
                       s.recete_no, s.talep_adet, s.bara_adedi,
                       s.bara_parca, s.bara_sure_dk, s.toplam_sure_dk,
                       s.sira_no, s.kaynak
                FROM planlama.gunluk_taslak_satir s
                LEFT JOIN tanim.vardiyalar v ON s.vardiya_id = v.id
                LEFT JOIN stok.urunler u ON s.urun_id = u.id
                LEFT JOIN musteri.cariler c ON s.cari_id = c.id
                LEFT JOIN tanim.kaplama_turleri kt ON s.kaplama_turu_id = kt.id
                WHERE s.taslak_id = ?
                ORDER BY s.sira_no, s.id
            """, (taslak_id,))
            rows = []
            for r in cur.fetchall():
                rows.append({
                    'id': int(r[0]),
                    'vardiya_id': int(r[1]) if r[1] else None,
                    'vardiya_kod': r[2] or '',
                    'urun_id': int(r[3]) if r[3] else None,
                    'urun_kodu': r[4] or '',
                    'urun_adi': r[5] or '',
                    'cari_id': int(r[6]) if r[6] else None,
                    'cari_unvan': r[7] or '',
                    'kaplama_turu_id': int(r[8]) if r[8] else None,
                    'kap_kod': r[9] or '',
                    'recete_no': r[10] or '',
                    'ihtiyac_adet': int(r[11] or 0),
                    'yapilacak_bara': int(r[12] or 0),
                    'bara_parca': int(r[13] or 0),
                    'recete_sure_dk': int(r[14] or 0),
                    'toplam_dk': int(r[15] or 0),
                    'sira_no': int(r[16] or 0),
                    'kaynak': r[17] or 'ANLASMA',
                })
            conn.close()
            return rows
        except Exception as e:
            print(f"[GunlukPlan] satir yukleme hata: {e}")
            return []

    def _satirlari_kaydet(self, taslak_id: int, satirlar: list):
        try:
            conn = get_db_connection(); cur = conn.cursor()
            # onceki satirlari sil
            cur.execute("DELETE FROM planlama.gunluk_taslak_satir WHERE taslak_id = ?", (taslak_id,))
            for i, s in enumerate(satirlar):
                cur.execute("""
                    INSERT INTO planlama.gunluk_taslak_satir
                        (taslak_id, vardiya_id, urun_id, cari_id, kaplama_turu_id,
                         recete_no, talep_adet, bara_adedi, bara_parca,
                         bara_sure_dk, toplam_sure_dk, sira_no, kaynak)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    taslak_id, s.get('vardiya_id'), s.get('urun_id'),
                    s.get('cari_id'), s.get('kaplama_turu_id'),
                    int(s.get('recete_no') or 0) if str(s.get('recete_no', '')).isdigit() else None,
                    int(s.get('ihtiyac_adet', 0)),
                    int(s.get('yapilacak_bara', 0)),
                    int(s.get('bara_parca', 0)),
                    int(s.get('recete_sure_dk', 0)),
                    int(s.get('toplam_dk', 0)),
                    i + 1,
                    s.get('kaynak', 'ANLASMA')
                ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[GunlukPlan] satir kaydet hata: {e}")
            import traceback; traceback.print_exc()
            return False

    def _onay_uygula(self, taslak_id: int, tarih: date) -> tuple:
        """Taslaktan siparis.is_emirleri + uretim.planlama kayitlari uret."""
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT s.id, s.vardiya_id, s.urun_id, s.cari_id, s.kaplama_turu_id,
                       u.urun_kodu, u.urun_adi, s.talep_adet, s.bara_adedi,
                       s.toplam_sure_dk
                FROM planlama.gunluk_taslak_satir s
                LEFT JOIN stok.urunler u ON s.urun_id = u.id
                WHERE s.taslak_id = ?
                  AND s.vardiya_id IS NOT NULL
                ORDER BY s.sira_no
            """, (taslak_id,))
            satirlar = cur.fetchall()
            if not satirlar:
                return (False, "Vardiyaya atanmis satir yok!")

            # her satir icin IS EMRI + PLANLAMA kaydi
            olusan = 0
            for s in satirlar:
                tas_id, v_id, urun_id, cari_id, kap_id = s[0], s[1], s[2], s[3], s[4]
                urun_kod, urun_ad, adet, bara, toplam_dk = s[5], s[6], s[7], s[8], s[9]

                # is emri no uret
                cur.execute("""
                    SELECT ISNULL(MAX(CAST(SUBSTRING(is_emri_no, 4, 8) AS BIGINT)), 0)
                    FROM siparis.is_emirleri
                    WHERE is_emri_no LIKE ?
                """, (f"IE-{tarih.strftime('%Y%m%d')}-%",))
                max_no = int(cur.fetchone()[0] or 0)
                yeni_no = f"IE-{tarih.strftime('%Y%m%d')}-{(max_no % 100000 + 1):04d}"

                # is_emirleri INSERT
                cur.execute("""
                    INSERT INTO siparis.is_emirleri
                        (is_emri_no, tarih, cari_id, urun_id, kaplama_turu_id,
                         planlanan_miktar, oncelik, durum, stok_kodu, stok_adi,
                         bara_adet, toplam_bara, tahmini_sure_dk, olusturma_tarihi)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, 2, N'PLANLANDI', ?, ?, ?, ?, ?, GETDATE())
                """, (
                    yeni_no, tarih, cari_id, urun_id, kap_id,
                    adet, urun_kod, urun_ad, bara, bara, toplam_dk
                ))
                ie_id = int(cur.fetchone()[0])

                # uretim.planlama INSERT
                cur.execute("""
                    INSERT INTO uretim.planlama
                        (tarih, hat_id, vardiya_id, is_emri_id,
                         planlanan_bara, durum, olusturma_tarihi)
                    VALUES (?, NULL, ?, ?, ?, N'PLANLANDI', GETDATE())
                """, (tarih, v_id, ie_id, bara))
                olusan += 1

            # taslagi onaylandi olarak isaretle
            cur.execute("""
                UPDATE planlama.gunluk_taslak
                SET durum = N'ONAYLI', onay_tarihi = GETDATE()
                WHERE id = ?
            """, (taslak_id,))

            conn.commit()
            conn.close()
            return (True, f"{olusan} is emri ve planlama kaydi olusturuldu.")
        except Exception as e:
            import traceback; traceback.print_exc()
            return (False, f"Onay hatasi: {e}")

    # ==================================================================
    # UI
    # ==================================================================
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Header
        h = QHBoxLayout()
        ic = QLabel("📅"); ic.setStyleSheet("font-size: 28px;")
        ts = QVBoxLayout(); ts.setSpacing(2)
        tr = QHBoxLayout(); tr.addWidget(ic)
        tr.addWidget(QLabel("Günlük Üretim Planlama",
            styleSheet=f"color:{brand.TEXT}; font-size:22px; font-weight:600;"))
        tr.addStretch()
        ts.addLayout(tr)
        ts.addWidget(QLabel("Stok kartlarındaki Günlük İhtiyaç'tan otomatik taslak → onay → iş emri",
            styleSheet=f"color:{brand.TEXT_MUTED}; font-size:13px;"))
        h.addLayout(ts); h.addStretch()
        layout.addLayout(h)

        # Filtre + aksiyon bar
        fr = QFrame()
        fr.setStyleSheet(f"QFrame {{ background: {brand.BG_CARD}; "
                         f"border: 1px solid {brand.BORDER}; border-radius: 10px; }}")
        fl = QHBoxLayout(fr); fl.setContentsMargins(16, 12, 16, 12); fl.setSpacing(12)
        ls = f"color: {brand.TEXT_MUTED}; font-size: 12px; font-weight: 500;"
        ins = (f"background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; "
               f"border-radius: 8px; padding: 8px 12px; color: {brand.TEXT}; font-size: 13px;")

        fl.addWidget(QLabel("Tarih:", styleSheet=ls))
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setCalendarPopup(True)
        self.tarih_edit.setDisplayFormat("dd.MM.yyyy")
        # 16:00'dan sonra yarinı plan yapılır — default yarın
        self.tarih_edit.setDate(QDate.currentDate().addDays(1))
        self.tarih_edit.setStyleSheet(f"QDateEdit {{ {ins} }}")
        self.tarih_edit.dateChanged.connect(lambda _: self._refresh())
        fl.addWidget(self.tarih_edit)

        self.durum_lbl = QLabel("TASLAK")
        self.durum_lbl.setStyleSheet(
            f"background: rgba(220,38,38,0.12); color: {brand.PRIMARY}; "
            f"padding: 6px 14px; border-radius: 12px; font-size: 12px; "
            f"font-weight: 700; border: 1px solid {brand.PRIMARY};"
        )
        fl.addWidget(self.durum_lbl)

        fl.addStretch()

        self.olustur_btn = QPushButton("⚡ Otomatik Oluştur")
        self.olustur_btn.setStyleSheet(
            f"QPushButton {{ background: {brand.INFO}; color: white; border: none; "
            f"border-radius: 8px; padding: 10px 18px; font-size: 13px; font-weight: 600; }}"
        )
        self.olustur_btn.clicked.connect(self._on_olustur)
        fl.addWidget(self.olustur_btn)

        self.kaydet_btn = QPushButton("💾 Taslağı Kaydet")
        self.kaydet_btn.setStyleSheet(
            f"QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 8px; "
            f"padding: 10px 18px; font-size: 13px; font-weight: 600; }}"
        )
        self.kaydet_btn.clicked.connect(self._on_taslak_kaydet)
        fl.addWidget(self.kaydet_btn)

        self.onayla_btn = QPushButton("✓ Onayla ve İş Emri Oluştur")
        self.onayla_btn.setStyleSheet(
            f"QPushButton {{ background: {brand.SUCCESS}; color: white; border: none; "
            f"border-radius: 8px; padding: 10px 18px; font-size: 13px; font-weight: 600; }}"
        )
        self.onayla_btn.clicked.connect(self._on_onayla)
        fl.addWidget(self.onayla_btn)
        layout.addWidget(fr)

        # Özet bar
        sf = QFrame()
        sf.setStyleSheet(f"QFrame {{ background: transparent; }}")
        sl = QHBoxLayout(sf); sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(12)
        self.stat_talep = self._mk_stat("Talep Sayısı", "0", brand.PRIMARY)
        self.stat_bara = self._mk_stat("Toplam Bara", "0", brand.INFO)
        self.stat_ktl = self._mk_stat("KTL İş Yükü", "0 dk", brand.SUCCESS)
        self.stat_zn = self._mk_stat("ZN/ZNNI", "0 dk", brand.INFO)
        self.stat_diger = self._mk_stat("Diğer", "0 dk", brand.WARNING)
        for s in (self.stat_talep, self.stat_bara, self.stat_ktl, self.stat_zn, self.stat_diger):
            sl.addWidget(s)
        layout.addWidget(sf)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Müşteri", "Kap.", "Ürün Kodu", "Ürün Adı",
            "İhtiyaç", "Bara/Parça", "Yapılacak Bara",
            "Reçete Süre (dk)", "Toplam (dk)", "Vardiya", "Kaynak"
        ])
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER};
                border-radius: 10px; color: {brand.TEXT}; gridline-color: {brand.BORDER}; }}
            QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {brand.BORDER}; }}
            QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {brand.TEXT_MUTED};
                padding: 10px 8px; border: none; border-bottom: 2px solid {brand.PRIMARY};
                font-weight: 600; font-size: 12px; }}
        """)
        self.table.setColumnWidth(0, 160)   # Müşteri
        self.table.setColumnWidth(1, 70)    # Kap
        self.table.setColumnWidth(2, 110)   # Kod
        self.table.setColumnWidth(4, 90)    # İhtiyaç
        self.table.setColumnWidth(5, 90)    # Bara/Parça
        self.table.setColumnWidth(6, 110)   # Yapılacak Bara
        self.table.setColumnWidth(7, 120)   # Reçete Süre
        self.table.setColumnWidth(8, 110)   # Toplam
        self.table.setColumnWidth(9, 100)   # Vardiya
        self.table.setColumnWidth(10, 90)   # Kaynak
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table, 1)

    def _mk_stat(self, title: str, value: str, color: str) -> QFrame:
        f = QFrame(); f.setFixedHeight(66)
        f.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; "
            f"border-left: 4px solid {color}; border-radius: 10px; }}"
        )
        v = QVBoxLayout(f); v.setContentsMargins(14, 8, 14, 8); v.setSpacing(2)
        v.addWidget(QLabel(title, styleSheet=
            f"color: {brand.TEXT_DIM}; font-size: 11px; font-weight: 500;"))
        val = QLabel(value, styleSheet=
            f"color: {color}; font-size: 18px; font-weight: 700;")
        val.setObjectName("stat_value")
        v.addWidget(val)
        return f

    def _set_stat(self, card, value):
        lbl = card.findChild(QLabel, "stat_value")
        if lbl: lbl.setText(value)

    # ==================================================================
    # IS AKISI
    # ==================================================================
    def _refresh(self):
        tarih = self.tarih_edit.date().toPython()
        taslak_id = self._taslak_bul_veya_olustur(tarih, olustur_mu=False)
        self._taslak_id = taslak_id
        if taslak_id:
            self._satirlar = self._satirlari_yukle(taslak_id)
            self.durum_lbl.setText(self._durum)
            if self._durum == 'ONAYLI':
                self.durum_lbl.setStyleSheet(
                    f"background: rgba(16,185,129,0.15); color: {brand.SUCCESS}; "
                    f"padding: 6px 14px; border-radius: 12px; font-size: 12px; "
                    f"font-weight: 700; border: 1px solid {brand.SUCCESS};"
                )
                self.olustur_btn.setEnabled(False)
                self.kaydet_btn.setEnabled(False)
                self.onayla_btn.setEnabled(False)
            else:
                self.durum_lbl.setStyleSheet(
                    f"background: rgba(220,38,38,0.12); color: {brand.PRIMARY}; "
                    f"padding: 6px 14px; border-radius: 12px; font-size: 12px; "
                    f"font-weight: 700; border: 1px solid {brand.PRIMARY};"
                )
                self.olustur_btn.setEnabled(True)
                self.kaydet_btn.setEnabled(True)
                self.onayla_btn.setEnabled(True)
        else:
            self._satirlar = []
            self.durum_lbl.setText("BOŞ")
            self.olustur_btn.setEnabled(True)
            self.kaydet_btn.setEnabled(False)
            self.onayla_btn.setEnabled(False)

        self._fill_table()

    def _fill_table(self):
        self.table.setRowCount(len(self._satirlar))
        for i, s in enumerate(self._satirlar):
            # 0 Müşteri
            self.table.setItem(i, 0, QTableWidgetItem(s.get('cari_unvan', '') or ''))

            # 1 Kaplama pill
            kap_kod = (s.get('kap_kod') or '').upper()
            bg, fg, short = _kap_color(kap_kod)
            pill = QLabel(short)
            pill.setAlignment(Qt.AlignCenter)
            pill.setStyleSheet(
                f"color: {fg}; background: {bg}; border-radius: 9px; "
                f"padding: 2px 8px; font-size: 11px; font-weight: 700;"
            )
            hb = QWidget(); hh = QHBoxLayout(hb); hh.setContentsMargins(4, 2, 4, 2)
            hh.addWidget(pill); hh.addStretch()
            self.table.setCellWidget(i, 1, hb)

            # 2 Kod, 3 Ad
            self.table.setItem(i, 2, QTableWidgetItem(s.get('urun_kodu', '')))
            ad = QTableWidgetItem(s.get('urun_adi', ''))
            ad.setForeground(QColor(brand.TEXT_DIM))
            self.table.setItem(i, 3, ad)

            # 4 İhtiyaç
            it = QTableWidgetItem(f"{s['ihtiyac_adet']:,}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 4, it)

            # 5 Bara/Parça (stok kartındaki bara_adedi)
            it = QTableWidgetItem(str(s['bara_parca']))
            it.setTextAlignment(Qt.AlignCenter)
            it.setForeground(QColor(brand.TEXT_DIM))
            self.table.setItem(i, 5, it)

            # 6 Yapılacak Bara
            it = QTableWidgetItem(str(s['yapilacak_bara']))
            it.setTextAlignment(Qt.AlignCenter)
            it.setForeground(QColor(brand.INFO))
            it.setFont(self._bold_font())
            self.table.setItem(i, 6, it)

            # 7 Reçete süre
            rs = s['recete_sure_dk']
            it = QTableWidgetItem(f"{rs} dk" if rs else "-")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if rs == 0:
                it.setForeground(QColor(brand.WARNING))
            self.table.setItem(i, 7, it)

            # 8 Toplam
            it = QTableWidgetItem(f"{s['toplam_dk']} dk")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it.setForeground(QColor(brand.SUCCESS))
            it.setFont(self._bold_font())
            self.table.setItem(i, 8, it)

            # 9 Vardiya combo
            vc = QComboBox()
            vc.addItem("— seç —", None)
            for v in self._vardiyalar:
                vc.addItem(v['kod'], v['id'])
            if s.get('vardiya_id'):
                for k in range(vc.count()):
                    if vc.itemData(k) == s['vardiya_id']:
                        vc.setCurrentIndex(k); break
            vc.setStyleSheet(
                f"QComboBox {{ background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; "
                f"color: {brand.TEXT}; padding: 4px 8px; border-radius: 5px; }}"
            )
            vc.currentIndexChanged.connect(lambda _, idx=i, cb=vc: self._on_vardiya_change(idx, cb))
            self.table.setCellWidget(i, 9, vc)

            # 10 Kaynak
            it = QTableWidgetItem(s.get('kaynak', 'ANLASMA'))
            it.setForeground(QColor(brand.TEXT_DIM))
            self.table.setItem(i, 10, it)

            self.table.setRowHeight(i, 42)

        self._update_stats()

    def _bold_font(self):
        from PySide6.QtGui import QFont
        f = QFont(); f.setBold(True); return f

    def _update_stats(self):
        talep = len(self._satirlar)
        toplam_bara = sum(s['yapilacak_bara'] for s in self._satirlar)
        ktl = sum(s['toplam_dk'] for s in self._satirlar if s.get('kap_kod', '').upper() in ('KTF', 'KATAFOREZ'))
        zn = sum(s['toplam_dk'] for s in self._satirlar if s.get('kap_kod', '').upper() in ('ZN', 'ZNNI', 'ASITZN'))
        diger = sum(s['toplam_dk'] for s in self._satirlar) - ktl - zn
        self._set_stat(self.stat_talep, str(talep))
        self._set_stat(self.stat_bara, f"{toplam_bara:,}")
        self._set_stat(self.stat_ktl, f"{ktl:,} dk")
        self._set_stat(self.stat_zn, f"{zn:,} dk")
        self._set_stat(self.stat_diger, f"{diger:,} dk")

    # ==================================================================
    # BUTON HANDLER
    # ==================================================================
    def _on_vardiya_change(self, idx: int, cb: QComboBox):
        if 0 <= idx < len(self._satirlar):
            self._satirlar[idx]['vardiya_id'] = cb.currentData()

    def _on_olustur(self):
        """Stok kartlarindan otomatik taslak olustur."""
        tarih = self.tarih_edit.date().toPython()

        if self._satirlar:
            ret = QMessageBox.question(
                self, "Uyarı",
                "Bu tarih için zaten taslak var. Mevcut satırlar silinip\n"
                "yeniden oluşturulacak. Devam?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret != QMessageBox.Yes:
                return

        taslak_id = self._taslak_bul_veya_olustur(tarih, olustur_mu=True)
        if not taslak_id:
            QMessageBox.critical(self, "Hata", "Taslak oluşturulamadı!")
            return
        self._taslak_id = taslak_id

        # Talepleri çek
        talepler = self._load_talepler()
        if not talepler:
            QMessageBox.warning(
                self, "Uyarı",
                "Günlük ihtiyaç tanımlı ürün bulunamadı.\n\n"
                "Stok kartlarında 'Günlük İhtiyaç (Adet)' alanını dolduran\n"
                "MAMUL ürünler listelenecektir."
            )
            self._satirlar = []
            self._fill_table()
            return

        # Satır yapısına dönüştür + default vardiya ata (V1)
        default_v = self._vardiyalar[0]['id'] if self._vardiyalar else None
        self._satirlar = []
        for t in talepler:
            self._satirlar.append({
                **t,
                'vardiya_id': default_v,
                'vardiya_kod': self._vardiyalar[0]['kod'] if self._vardiyalar else '',
                'kaynak': 'ANLASMA',
            })

        # Kaydet
        if self._satirlari_kaydet(taslak_id, self._satirlar):
            self._fill_table()
            QMessageBox.information(
                self, "Başarılı",
                f"{len(self._satirlar)} talep taslak olarak oluşturuldu.\n\n"
                f"Vardiyaları kontrol edip 'Onayla ve İş Emri Oluştur' deyin."
            )
        else:
            QMessageBox.critical(self, "Hata", "Taslak kaydedilemedi!")

    def _on_taslak_kaydet(self):
        if not self._taslak_id:
            QMessageBox.warning(self, "Uyarı", "Önce taslak oluşturun!")
            return
        if self._satirlari_kaydet(self._taslak_id, self._satirlar):
            QMessageBox.information(self, "Başarılı", "Taslak güncellendi.")
        else:
            QMessageBox.critical(self, "Hata", "Kaydetme hatası!")

    def _on_onayla(self):
        if not self._taslak_id or not self._satirlar:
            QMessageBox.warning(self, "Uyarı", "Onaylanacak taslak yok!")
            return

        # Önce taslağı kaydet
        if not self._satirlari_kaydet(self._taslak_id, self._satirlar):
            QMessageBox.critical(self, "Hata", "Taslak kaydedilemedi!")
            return

        vardiyasi_yok = [s for s in self._satirlar if not s.get('vardiya_id')]
        if vardiyasi_yok:
            ret = QMessageBox.question(
                self, "Uyarı",
                f"{len(vardiyasi_yok)} satırın vardiyası atanmamış.\n"
                f"Bu satırlar onaya dahil EDİLMEYECEK. Devam?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret != QMessageBox.Yes:
                return

        ret = QMessageBox.question(
            self, "Onay",
            "Taslak onaylanıp iş emirleri oluşturulacak.\n"
            "Bu işlem geri alınamaz. Devam?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret != QMessageBox.Yes:
            return

        tarih = self.tarih_edit.date().toPython()
        ok, msg = self._onay_uygula(self._taslak_id, tarih)
        if ok:
            QMessageBox.information(self, "Başarılı", msg)
            self._refresh()
        else:
            QMessageBox.critical(self, "Hata", msg)
