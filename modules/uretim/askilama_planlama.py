# -*- coding: utf-8 -*-
"""
NEXOR ERP - Askilama Personel Planlama

Akis:
    FAZ 1: Tarih + vardiya sec -> kaplama.plan_urunler'den dusen isleri getir ->
           bara / aski suresi duzenle, checkbox ile dahil et
    FAZ 2: Secili isler icin askilamaci (ik.pozisyonlar kod LIKE '%ASK%') chip'leri
           ile coklu atama -> gercek sure = toplam_dk / personel_sayisi

Veri:
    stok.urunler.bara_aski_suresi_dk (snapshot olarak plana yazilir)
    uretim.askilama_plan (1 satir = 1 is)
    uretim.askilama_plan_personel (N-N: 1 is -> cok personel)
"""

import math
from datetime import date, datetime, timedelta, time as _time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QDateEdit, QTimeEdit, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QStackedWidget, QScrollArea, QMessageBox,
    QSpinBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QColor

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


HAT_PILL_COLORS = {
    'KTL':   (brand.SUCCESS, 'rgba(16,185,129,0.15)', '#6EE7B7'),
    'KATAFOREZ': (brand.SUCCESS, 'rgba(16,185,129,0.15)', '#6EE7B7'),
    'ZNNI':  (brand.INFO, 'rgba(59,130,246,0.15)', '#93C5FD'),
    'ZN':    (brand.INFO, 'rgba(59,130,246,0.15)', '#93C5FD'),
    'ZN-NI': (brand.INFO, 'rgba(59,130,246,0.15)', '#93C5FD'),
    'ON':    (brand.WARNING, 'rgba(245,158,11,0.15)', '#FCD34D'),
    'TB':    (brand.WARNING, 'rgba(245,158,11,0.15)', '#FCD34D'),
    'TOZ BOYA': (brand.WARNING, 'rgba(245,158,11,0.15)', '#FCD34D'),
}


def _hat_color(tip: str) -> tuple:
    if not tip:
        return (brand.TEXT_DIM, 'rgba(136,150,166,0.12)', brand.TEXT_DIM)
    key = tip.upper().strip()
    return HAT_PILL_COLORS.get(key, (brand.TEXT_DIM, 'rgba(136,150,166,0.12)', brand.TEXT_DIM))


class AskilamaPlanlamaPage(BasePage):
    """Askılama Personel Planlama - 2 Fazlı"""

    def __init__(self, theme: dict):
        super().__init__(theme)
        self._vardiyalar = []      # [(id, kod, ad, bas, bit)]
        self._jobs = []            # Faz 1'den gelen isler (dict listesi)
        self._personeller = []     # askilamaci listesi (dict)
        self._assignments = {}     # job_idx -> [personel_id, ...]
        self._plan_id = None

        self._load_vardiyalar()
        self._setup_ui()
        self._refresh_plan()

    # ==================================================================
    # VERITABANI
    # ==================================================================
    def _load_vardiyalar(self):
        """Aktif vardiyalari yukle"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
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
            print(f"[AskPlan] Vardiya yukleme hatasi: {e}")
            self._vardiyalar = []

    def _get_selected_vardiya(self) -> dict:
        idx = self.vardiya_combo.currentIndex()
        if 0 <= idx < len(self._vardiyalar):
            return self._vardiyalar[idx]
        return None

    def _vardiya_saatleri(self) -> tuple:
        """Override aktifse oradan, degilse tanimdan doner. -> (bas, bit, toplam_dk)"""
        v = self._get_selected_vardiya()
        if not v:
            return (_time(8, 0), _time(16, 0), 480)

        if self.override_check.isChecked():
            bas = self.override_bas.time().toPython()
            bit = self.override_bit.time().toPython()
        else:
            bas = v['bas'] if isinstance(v['bas'], _time) else _time(8, 0)
            bit = v['bit'] if isinstance(v['bit'], _time) else _time(16, 0)

        # Toplam dk (bitis < bas ise gece vardiyasi)
        bm = bas.hour * 60 + bas.minute
        em = bit.hour * 60 + bit.minute
        total = em - bm if em > bm else (24 * 60 - bm) + em
        return (bas, bit, total)

    def _load_plan_urunler(self, tarih: date, vardiya_id: int,
                            hat_filtre: str = None) -> list:
        """Uretim planlama ekranindaki isleri getirir.

        Kaynak: uretim.planlama + siparis.is_emirleri + stok.urunler
        Filtre: secili tarih + vardiya + iptal edilmemis + opsiyonel hat
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Hat filtresi
            hat_where = ""
            if hat_filtre == "KTL":
                hat_where = "AND h.kod LIKE '%KTL%'"
            elif hat_filtre == "ZNNI":
                hat_where = "AND (h.kod LIKE '%ZN%' OR h.kod LIKE '%ZNNI%')"
            elif hat_filtre == "ON":
                hat_where = "AND h.kod LIKE '%ON%'"

            sql = f"""
                SELECT p.id AS planlama_id,
                       p.tarih, p.vardiya_id, p.hat_id,
                       h.kod AS hat_kod, h.ad AS hat_ad,
                       p.is_emri_id, ie.is_emri_no,
                       ie.urun_id, u.urun_kodu, u.urun_adi,
                       ISNULL(u.bara_aski_suresi_dk, 0) as aski_suresi_dk,
                       ie.kaplama_tipi,
                       p.planlanan_bara,
                       p.baslangic_saat, p.bitis_saat,
                       p.durum, p.sira_no,
                       ie.oncelik
                FROM uretim.planlama p
                LEFT JOIN siparis.is_emirleri ie ON p.is_emri_id = ie.id
                LEFT JOIN stok.urunler u ON ie.urun_id = u.id
                LEFT JOIN tanim.uretim_hatlari h ON p.hat_id = h.id
                WHERE p.tarih = ? AND p.vardiya_id = ?
                  AND (p.durum IS NULL OR p.durum <> 'IPTAL')
                  {hat_where}
                ORDER BY p.sira_no, p.id
            """
            cur.execute(sql, (tarih, vardiya_id))

            jobs = []
            for r in cur.fetchall():
                hat_kod = (r[4] or '').upper()
                # Hat kodundan tipi cikar (E-KTL -> KTL, E-ZNNI -> ZNNI, E-ON -> ON)
                if 'KTL' in hat_kod: tip = 'KTL'
                elif 'ZN' in hat_kod: tip = 'ZNNI'
                elif 'ON' in hat_kod: tip = 'ON'
                else: tip = (r[12] or '').upper() or hat_kod

                jobs.append({
                    'planlama_id': int(r[0]),
                    'is_emri_id': int(r[6]) if r[6] else None,
                    'is_emri_no': r[7] or '',
                    'urun_id': int(r[8]) if r[8] else None,
                    'urun_kodu': r[9] or '-',
                    'urun_adi': r[10] or '',
                    'aski_suresi_dk': int(r[11] or 0),
                    'tip': tip,
                    'hat_kod': r[4] or '',
                    'hat_ad': r[5] or '',
                    'bara_adedi': int(r[13] or 0),
                    'baslangic_saat': r[14],
                    'bitis_saat': r[15],
                    'durum': r[16] or 'PLANLANDI',
                    'sira_no': int(r[17] or 0),
                    'oncelik': str(r[18] or 'normal'),
                    # Editable alanlar - default olarak hepsi secili
                    'secili': True,
                })
            conn.close()
            return jobs
        except Exception as e:
            print(f"[AskPlan] Plan urunler yukleme hatasi: {e}")
            import traceback; traceback.print_exc()
            return []

    def _load_personel(self, tarih: date, vardiya_id: int) -> list:
        """O tarih+vardiyada calisan askilamaci pozisyonundaki personeller."""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # 1) ik.vardiya_planlama'da kayit varsa onu kullan
            cur.execute("""
                SELECT DISTINCT e.id, e.ad, e.soyad, p.kod, p.ad
                FROM ik.personeller e
                LEFT JOIN ik.pozisyonlar p ON e.pozisyon_id = p.id
                LEFT JOIN ik.vardiya_planlama vp ON vp.personel_id = e.id
                     AND vp.tarih = ? AND vp.vardiya_id = ?
                WHERE e.aktif_mi = 1
                  AND (e.silindi_mi IS NULL OR e.silindi_mi = 0)
                  AND (p.kod LIKE '%ASK%' OR p.ad LIKE N'%Ask%')
                  AND (vp.id IS NOT NULL OR e.varsayilan_vardiya_id = ?)
                ORDER BY p.kod, e.ad, e.soyad
            """, (tarih, vardiya_id, vardiya_id))
            personeller = [
                {'id': r[0], 'ad': (r[1] or '').strip(),
                 'soyad': (r[2] or '').strip(),
                 'pozisyon_kod': r[3] or '', 'pozisyon_ad': r[4] or ''}
                for r in cur.fetchall()
            ]
            conn.close()
            return personeller
        except Exception as e:
            print(f"[AskPlan] Personel yukleme hatasi: {e}")
            return []

    def _save_plan(self) -> tuple:
        """(basarili, mesaj) doner"""
        tarih = self.tarih_edit.date().toPython()
        v = self._get_selected_vardiya()
        if not v:
            return (False, "Vardiya secilmedi!")

        bas, bit, toplam_kap = self._vardiya_saatleri()
        override_bas = self.override_bas.time().toPython() if self.override_check.isChecked() else None
        override_bit = self.override_bit.time().toPython() if self.override_check.isChecked() else None

        # Secili isleri topla
        secili_jobs = [j for j in self._jobs if j['secili']]
        if not secili_jobs:
            return (False, "En az bir is secmelisiniz!")

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Onceki planlari temizle (idempotent kayit)
            cur.execute("""
                SELECT id FROM uretim.askilama_plan
                WHERE tarih = ? AND vardiya_id = ? AND (silindi_mi IS NULL OR silindi_mi = 0)
            """, (tarih, v['id']))
            eski_ids = [r[0] for r in cur.fetchall()]
            if eski_ids:
                ph = ','.join(['?'] * len(eski_ids))
                cur.execute(
                    f"DELETE FROM uretim.askilama_plan_personel WHERE plan_id IN ({ph})",
                    eski_ids
                )
                cur.execute(
                    f"UPDATE uretim.askilama_plan SET silindi_mi = 1, silinme_tarihi = GETDATE() WHERE id IN ({ph})",
                    eski_ids
                )

            # Baslangic saati - her is bir oncekinin bitisinde basliyor
            cur_bas = bas
            cur_bas_dk = bas.hour * 60 + bas.minute

            for idx, job in enumerate(secili_jobs):
                personel_ids = self._assignments.get(self._jobs.index(job), [])
                personel_sayisi = max(len(personel_ids), 1)
                toplam_dk = int(job['bara_adedi']) * int(job['aski_suresi_dk'])
                gercek_dk = math.ceil(toplam_dk / personel_sayisi) if toplam_dk else 0

                # Bitis saati
                bit_dk = cur_bas_dk + gercek_dk
                bit_h = (bit_dk // 60) % 24
                bit_m = bit_dk % 60
                bitis_tm = _time(bit_h, bit_m)

                cur.execute("""
                    INSERT INTO uretim.askilama_plan
                        (tarih, vardiya_id, planlama_id, is_emri_id, urun_id,
                         recete_no, hat_tipi,
                         bara_adedi, aski_suresi_dk, toplam_dk, gercek_dk,
                         baslangic, bitis, saat_override_bas, saat_override_bit,
                         oncelik, durum)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, N'ONAYLI')
                """, (
                    tarih, v['id'],
                    job.get('planlama_id'),
                    job.get('is_emri_id'),
                    job.get('urun_id'),
                    job.get('is_emri_no', ''),
                    job['tip'],
                    int(job['bara_adedi']), int(job['aski_suresi_dk']),
                    toplam_dk, gercek_dk,
                    cur_bas, bitis_tm, override_bas, override_bit,
                    job.get('oncelik', 'normal')
                ))
                plan_id = int(cur.fetchone()[0])

                # Personel linkleri
                for pid in personel_ids:
                    try:
                        cur.execute("""
                            INSERT INTO uretim.askilama_plan_personel (plan_id, personel_id)
                            VALUES (?, ?)
                        """, (plan_id, pid))
                    except Exception:
                        pass  # duplicate ise atla

                cur_bas = bitis_tm
                cur_bas_dk = bit_dk

            conn.commit()
            conn.close()
            return (True, f"{len(secili_jobs)} is kaydedildi.")

        except Exception as e:
            import traceback; traceback.print_exc()
            return (False, f"Kayit hatasi:\n{e}")

    # ==================================================================
    # UI
    # ==================================================================
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        layout.addLayout(self._create_header())
        layout.addWidget(self._create_filter_bar())
        layout.addWidget(self._create_phase_indicator())
        layout.addWidget(self._create_summary_bar())

        # Stack: Faz 1 (tablo) + Faz 2 (atama)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_faz1_widget())
        self.stack.addWidget(self._create_faz2_widget())
        layout.addWidget(self.stack, 1)

    def _create_header(self) -> QHBoxLayout:
        h = QHBoxLayout()
        ic = QLabel("📋")
        ic.setStyleSheet("font-size: 28px;")
        t = QLabel("Askılama Personel Planlama")
        t.setStyleSheet(f"color: {brand.TEXT}; font-size: 22px; font-weight: 600;")
        st = QLabel("Vardiya seç → planlamadan düşen işleri seç → personel ata")
        st.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: 13px;")
        left = QVBoxLayout()
        tr = QHBoxLayout(); tr.addWidget(ic); tr.addWidget(t); tr.addStretch()
        left.addLayout(tr); left.addWidget(st)
        h.addLayout(left); h.addStretch()
        return h

    def _create_filter_bar(self) -> QFrame:
        fr = QFrame()
        fr.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 10px; }}"
        )
        v = QVBoxLayout(fr); v.setContentsMargins(16, 12, 16, 12); v.setSpacing(10)

        # Ana satir
        row = QHBoxLayout(); row.setSpacing(12)
        ls = f"color: {brand.TEXT_MUTED}; font-size: 12px; font-weight: 500;"
        ins = (f"background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; "
               f"border-radius: 8px; padding: 8px 12px; color: {brand.TEXT}; font-size: 13px;")

        row.addWidget(QLabel("Tarih:", styleSheet=ls))
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setCalendarPopup(True)
        self.tarih_edit.setDisplayFormat("dd.MM.yyyy")
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setStyleSheet(f"QDateEdit {{ {ins} }}")
        self.tarih_edit.dateChanged.connect(lambda _: self._refresh_plan())
        row.addWidget(self.tarih_edit)

        row.addWidget(QLabel("Vardiya:", styleSheet=ls))
        self.vardiya_combo = QComboBox()
        for vd in self._vardiyalar:
            bas_s = vd['bas'].strftime('%H:%M') if isinstance(vd['bas'], _time) else '?'
            bit_s = vd['bit'].strftime('%H:%M') if isinstance(vd['bit'], _time) else '?'
            self.vardiya_combo.addItem(f"{vd['kod']} · {vd['ad']} ({bas_s}-{bit_s})", vd['id'])
        self.vardiya_combo.setStyleSheet(
            f"QComboBox {{ {ins} min-width: 260px; }}"
            f"QComboBox QAbstractItemView {{ background: {brand.BG_CARD}; "
            f"color: {brand.TEXT}; selection-background-color: {brand.PRIMARY}; }}"
        )
        self.vardiya_combo.currentIndexChanged.connect(self._on_vardiya_changed)
        row.addWidget(self.vardiya_combo)

        row.addWidget(QLabel("Hat:", styleSheet=ls))
        self.hat_combo = QComboBox()
        self.hat_combo.addItem("Tümü", None)
        self.hat_combo.addItem("KTL (Kataforez)", "KTL")
        self.hat_combo.addItem("ZNNI (Çinko-Nikel)", "ZNNI")
        self.hat_combo.addItem("ON İşlem", "ON")
        self.hat_combo.setStyleSheet(
            f"QComboBox {{ {ins} min-width: 150px; }}"
            f"QComboBox QAbstractItemView {{ background: {brand.BG_CARD}; "
            f"color: {brand.TEXT}; selection-background-color: {brand.PRIMARY}; }}"
        )
        self.hat_combo.currentIndexChanged.connect(lambda _: self._refresh_plan())
        row.addWidget(self.hat_combo)

        self.override_check = QCheckBox("Saat Override")
        self.override_check.setStyleSheet(f"color: {brand.WARNING}; font-size: 12px;")
        self.override_check.stateChanged.connect(self._on_override_toggled)
        row.addWidget(self.override_check)

        row.addStretch()

        self.yenile_btn = QPushButton("🔄 Planı Yenile")
        self.yenile_btn.setStyleSheet(
            f"QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 8px; "
            f"padding: 8px 16px; font-size: 13px; font-weight: 500; }}"
            f"QPushButton:hover {{ border-color: {brand.PRIMARY}; }}"
        )
        self.yenile_btn.clicked.connect(self._refresh_plan)
        row.addWidget(self.yenile_btn)

        self.kaydet_btn = QPushButton("💾 Planı Kaydet")
        self.kaydet_btn.setStyleSheet(
            f"QPushButton {{ background: {brand.SUCCESS}; color: white; border: none; "
            f"border-radius: 8px; padding: 9px 20px; font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {brand.SUCCESS}; opacity: 0.9; }}"
        )
        self.kaydet_btn.clicked.connect(self._on_save)
        row.addWidget(self.kaydet_btn)
        v.addLayout(row)

        # Override alanı
        self.override_row = QFrame()
        self.override_row.setStyleSheet(f"QFrame {{ background: transparent; }}")
        ov = QHBoxLayout(self.override_row); ov.setContentsMargins(0, 0, 0, 0); ov.setSpacing(10)
        ov.addWidget(QLabel("⚠ Özel saat:", styleSheet=f"color: {brand.WARNING}; font-size: 12px;"))
        ov.addWidget(QLabel("Başlangıç:", styleSheet=ls))
        self.override_bas = QTimeEdit()
        self.override_bas.setDisplayFormat("HH:mm")
        self.override_bas.setTime(QTime(7, 30))
        self.override_bas.setStyleSheet(f"QTimeEdit {{ {ins} }}")
        ov.addWidget(self.override_bas)
        ov.addWidget(QLabel("Bitiş:", styleSheet=ls))
        self.override_bit = QTimeEdit()
        self.override_bit.setDisplayFormat("HH:mm")
        self.override_bit.setTime(QTime(15, 30))
        self.override_bit.setStyleSheet(f"QTimeEdit {{ {ins} }}")
        ov.addWidget(self.override_bit)
        ov.addStretch()
        self.override_row.setVisible(False)
        v.addWidget(self.override_row)
        return fr

    def _create_phase_indicator(self) -> QFrame:
        fr = QFrame()
        fr.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 10px; }}"
        )
        h = QHBoxLayout(fr); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(0)
        self.phase1_widget = self._make_phase_widget("1", "İş Seçimi",
            "Planlamadan düşen ürünleri seç", active=True)
        self.phase2_widget = self._make_phase_widget("2", "Personel Atama",
            "Her işe askılamacı ata", active=False)
        h.addWidget(self.phase1_widget); h.addWidget(self.phase2_widget)
        return fr

    def _make_phase_widget(self, num: str, title: str, sub: str, active: bool) -> QWidget:
        w = QWidget()
        w.setStyleSheet(
            f"QWidget {{ background: {'rgba(220,38,38,0.08)' if active else 'transparent'}; }}"
        )
        hl = QHBoxLayout(w); hl.setContentsMargins(16, 12, 16, 12); hl.setSpacing(12)
        num_lbl = QLabel(num)
        num_lbl.setFixedSize(28, 28)
        num_lbl.setAlignment(Qt.AlignCenter)
        num_lbl.setStyleSheet(
            f"background: {brand.PRIMARY if active else brand.BG_INPUT}; "
            f"color: {'white' if active else brand.TEXT_DIM}; "
            f"border-radius: 14px; font-weight: 700; font-size: 13px; "
            f"border: 1px solid {brand.PRIMARY if active else brand.BORDER};"
        )
        lbl_box = QVBoxLayout(); lbl_box.setSpacing(0)
        lbl_box.addWidget(QLabel(title, styleSheet=
            f"color: {brand.TEXT if active else brand.TEXT_DIM}; font-size: 13px; font-weight: 600;"))
        lbl_box.addWidget(QLabel(sub, styleSheet=
            f"color: {brand.TEXT_MUTED}; font-size: 11px;"))
        hl.addWidget(num_lbl); hl.addLayout(lbl_box); hl.addStretch()
        w.setProperty('num_lbl', num_lbl)
        w.setProperty('title_active', active)
        return w

    def _set_active_phase(self, phase: int):
        for w, num in [(self.phase1_widget, 1), (self.phase2_widget, 2)]:
            active = (num == phase)
            w.setStyleSheet(
                f"QWidget {{ background: {'rgba(220,38,38,0.08)' if active else 'transparent'}; }}"
            )
            num_lbl = w.property('num_lbl')
            if num_lbl:
                num_lbl.setStyleSheet(
                    f"background: {brand.PRIMARY if active else brand.BG_INPUT}; "
                    f"color: {'white' if active else brand.TEXT_DIM}; "
                    f"border-radius: 14px; font-weight: 700; font-size: 13px; "
                    f"border: 1px solid {brand.PRIMARY if active else brand.BORDER};"
                )
        self.stack.setCurrentIndex(phase - 1)

    def _create_summary_bar(self) -> QFrame:
        fr = QFrame()
        fr.setStyleSheet(f"QFrame {{ background: transparent; }}")
        h = QHBoxLayout(fr); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(12)
        self.stat_toplam = self._mk_stat("Düşen İş", "0", brand.PRIMARY)
        self.stat_secili = self._mk_stat("Seçili", "0", brand.SUCCESS)
        self.stat_sure = self._mk_stat("Toplam Süre (1 kişi)", "0 dk", brand.INFO)
        self.stat_kap = self._mk_stat("Vardiya Kapasite", "480 dk", brand.TEXT_DIM)
        self.stat_bos = self._mk_stat("Boş Kalan", "480 dk", brand.WARNING)
        for s in (self.stat_toplam, self.stat_secili, self.stat_sure, self.stat_kap, self.stat_bos):
            h.addWidget(s)
        return fr

    def _mk_stat(self, title: str, value: str, color: str) -> QFrame:
        f = QFrame(); f.setFixedHeight(70)
        f.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; "
            f"border-left: 4px solid {color}; border-radius: 10px; }}"
        )
        v = QVBoxLayout(f); v.setContentsMargins(14, 8, 14, 8); v.setSpacing(2)
        v.addWidget(QLabel(title, styleSheet=
            f"color: {brand.TEXT_DIM}; font-size: 11px; font-weight: 500;"))
        val = QLabel(value, styleSheet=
            f"color: {color}; font-size: 20px; font-weight: bold;")
        val.setObjectName("stat_value")
        v.addWidget(val)
        return f

    def _set_stat(self, card: QFrame, value: str):
        lbl = card.findChild(QLabel, "stat_value")
        if lbl: lbl.setText(value)

    # ------------------------------------------------------------------
    # FAZ 1: İş Tablosu
    # ------------------------------------------------------------------
    def _create_faz1_widget(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)

        # Tablo
        self.job_table = QTableWidget()
        self.job_table.setColumnCount(11)
        self.job_table.setHorizontalHeaderLabels([
            "Seç", "Hat", "İş Emri", "Ürün Kodu", "Ürün Adı",
            "Bara Adedi", "Askı Süresi (dk)", "Toplam Süre",
            "Başlangıç", "Durum", "Öncelik"
        ])
        self.job_table.setStyleSheet(f"""
            QTableWidget {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER};
                border-radius: 10px; color: {brand.TEXT}; gridline-color: {brand.BORDER}; }}
            QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {brand.BORDER}; }}
            QTableWidget::item:selected {{ background: rgba(220,38,38,0.12); }}
            QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {brand.TEXT_MUTED};
                padding: 10px 8px; border: none; border-bottom: 2px solid {brand.PRIMARY};
                font-weight: 600; font-size: 12px; }}
        """)
        self.job_table.setColumnWidth(0, 45)
        self.job_table.setColumnWidth(1, 70)
        self.job_table.setColumnWidth(2, 160)   # İş Emri
        self.job_table.setColumnWidth(3, 110)   # Ürün Kodu
        self.job_table.setColumnWidth(5, 100)   # Bara Adedi
        self.job_table.setColumnWidth(6, 130)   # Askı Süresi
        self.job_table.setColumnWidth(7, 110)   # Toplam Süre
        self.job_table.setColumnWidth(8, 90)    # Başlangıç
        self.job_table.setColumnWidth(9, 100)   # Durum
        self.job_table.setColumnWidth(10, 80)   # Öncelik
        self.job_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.job_table.verticalHeader().setVisible(False)
        self.job_table.setSelectionMode(QAbstractItemView.NoSelection)
        v.addWidget(self.job_table, 1)

        # Alt: devam butonu
        btn_row = QHBoxLayout()
        self.tum_btn = QPushButton("☑ Tümünü Seç")
        self.tum_btn.setStyleSheet(
            f"QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 8px; padding: 9px 18px; }}"
        )
        self.tum_btn.clicked.connect(self._on_select_all)
        btn_row.addWidget(self.tum_btn)

        btn_row.addStretch()

        self.goto_faz2_btn = QPushButton("Personel Atamaya Geç →")
        self.goto_faz2_btn.setStyleSheet(
            f"QPushButton {{ background: {brand.PRIMARY}; color: white; border: none; "
            f"border-radius: 8px; padding: 11px 24px; font-size: 14px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}"
        )
        self.goto_faz2_btn.clicked.connect(self._on_goto_faz2)
        btn_row.addWidget(self.goto_faz2_btn)
        v.addLayout(btn_row)
        return w

    def _fill_job_table(self):
        self.job_table.setRowCount(len(self._jobs))
        for i, job in enumerate(self._jobs):
            # 0 - Sec
            cb = QCheckBox()
            cb.setChecked(job['secili'])
            cb.stateChanged.connect(lambda s, idx=i: self._on_job_check(idx, s))
            hb = QWidget(); hh = QHBoxLayout(hb); hh.setContentsMargins(0, 0, 0, 0)
            hh.addStretch(); hh.addWidget(cb); hh.addStretch()
            self.job_table.setCellWidget(i, 0, hb)

            # 1 - Hat pill
            tip = (job['tip'] or '').upper()
            _, bg, fg = _hat_color(tip)
            pill = QLabel(tip or '-')
            pill.setAlignment(Qt.AlignCenter)
            pill.setStyleSheet(
                f"color: {fg}; background: {bg}; border-radius: 9px; "
                f"padding: 2px 8px; font-size: 11px; font-weight: 700;"
            )
            hb2 = QWidget(); hh2 = QHBoxLayout(hb2); hh2.setContentsMargins(4, 2, 4, 2)
            hh2.addWidget(pill); hh2.addStretch()
            self.job_table.setCellWidget(i, 1, hb2)

            # 2 - İş Emri No
            ie_item = QTableWidgetItem(job['is_emri_no'])
            ie_item.setForeground(QColor(brand.INFO))
            self.job_table.setItem(i, 2, ie_item)

            # 3 - Ürün Kodu
            self.job_table.setItem(i, 3, QTableWidgetItem(job['urun_kodu']))
            # 4 - Ürün Adı
            ad_item = QTableWidgetItem(job['urun_adi'])
            ad_item.setForeground(QColor(brand.TEXT_DIM))
            self.job_table.setItem(i, 4, ad_item)

            # 5 - Bara adedi (editable)
            bara_sp = QSpinBox(); bara_sp.setMaximum(9999); bara_sp.setValue(job['bara_adedi'])
            bara_sp.setStyleSheet(
                f"QSpinBox {{ background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; "
                f"color: {brand.TEXT}; padding: 4px 6px; border-radius: 5px; }}"
            )
            bara_sp.valueChanged.connect(lambda val, idx=i: self._on_job_bara(idx, val))
            self.job_table.setCellWidget(i, 5, bara_sp)

            # 6 - Aski suresi (editable)
            sure_sp = QSpinBox(); sure_sp.setMaximum(999); sure_sp.setValue(job['aski_suresi_dk'])
            sure_sp.setStyleSheet(
                f"QSpinBox {{ background: {brand.BG_INPUT}; border: 1px solid {brand.BORDER}; "
                f"color: {brand.TEXT}; padding: 4px 6px; border-radius: 5px; }}"
            )
            sure_sp.valueChanged.connect(lambda val, idx=i: self._on_job_sure(idx, val))
            self.job_table.setCellWidget(i, 6, sure_sp)

            # 7 - Toplam sure (calculated)
            toplam = job['bara_adedi'] * job['aski_suresi_dk']
            top_item = QTableWidgetItem(f"{toplam} dk")
            top_item.setForeground(QColor(brand.SUCCESS))
            top_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.job_table.setItem(i, 7, top_item)

            # 8 - Baslangic saati
            bas = job['baslangic_saat']
            bas_str = bas.strftime('%H:%M') if hasattr(bas, 'strftime') else '-'
            self.job_table.setItem(i, 8, QTableWidgetItem(bas_str))

            # 9 - Durum
            durum_item = QTableWidgetItem(job['durum'])
            durum_clr = brand.SUCCESS if job['durum'] == 'PLANLANDI' else brand.TEXT_DIM
            durum_item.setForeground(QColor(durum_clr))
            self.job_table.setItem(i, 9, durum_item)

            # 10 - Oncelik
            self.job_table.setItem(i, 10, QTableWidgetItem(job['oncelik']))

            self.job_table.setRowHeight(i, 42)

        self._update_summary()

    def _update_summary(self):
        _, _, kap = self._vardiya_saatleri()
        toplam = len(self._jobs)
        secili_jobs = [j for j in self._jobs if j['secili']]
        secili = len(secili_jobs)
        toplam_dk = sum(j['bara_adedi'] * j['aski_suresi_dk'] for j in secili_jobs)

        self._set_stat(self.stat_toplam, str(toplam))
        self._set_stat(self.stat_secili, str(secili))
        self._set_stat(self.stat_sure, f"{toplam_dk} dk")
        self._set_stat(self.stat_kap, f"{kap} dk")
        self._set_stat(self.stat_bos, f"{max(kap - toplam_dk, 0)} dk")

    # ------------------------------------------------------------------
    # FAZ 2: Personel Atama
    # ------------------------------------------------------------------
    def _create_faz2_widget(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)

        # Header with back button
        hr = QHBoxLayout()
        back_btn = QPushButton("← İş Seçimine Dön")
        back_btn.setStyleSheet(
            f"QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
            f"border: 1px solid {brand.BORDER}; border-radius: 8px; padding: 8px 16px; }}"
        )
        back_btn.clicked.connect(lambda: self._set_active_phase(1))
        hr.addWidget(back_btn)
        hr.addStretch()
        self.faz2_info = QLabel("")
        self.faz2_info.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 12px;")
        hr.addWidget(self.faz2_info)
        v.addLayout(hr)

        # Scroll area - her is icin bir satir
        self.assign_scroll = QScrollArea()
        self.assign_scroll.setWidgetResizable(True)
        self.assign_scroll.setStyleSheet(
            f"QScrollArea {{ background: transparent; border: none; }}"
        )
        self.assign_container = QWidget()
        self.assign_layout = QVBoxLayout(self.assign_container)
        self.assign_layout.setContentsMargins(0, 0, 0, 0)
        self.assign_layout.setSpacing(8)
        self.assign_scroll.setWidget(self.assign_container)
        v.addWidget(self.assign_scroll, 1)
        return w

    def _build_faz2(self):
        """Faz 2 panelini yeniden insa et."""
        # Mevcut widget'lari temizle
        while self.assign_layout.count():
            child = self.assign_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        secili_jobs = [(idx, j) for idx, j in enumerate(self._jobs) if j['secili']]
        self.faz2_info.setText(
            f"{len(secili_jobs)} iş · {len(self._personeller)} askılamacı bulundu"
        )

        if not secili_jobs:
            info = QLabel("Önce Faz 1'den en az bir iş seçin.")
            info.setAlignment(Qt.AlignCenter)
            info.setStyleSheet(f"color: {brand.TEXT_DIM}; padding: 60px; font-size: 14px;")
            self.assign_layout.addWidget(info)
            return

        if not self._personeller:
            info = QLabel("⚠ Bu vardiyada aktif askılamacı bulunamadı!\n"
                         "ik.vardiya_planlama'ya kayıt girilmiş mi kontrol edin "
                         "veya personelin varsayılan_vardiya_id'si doğru mu bakın.")
            info.setAlignment(Qt.AlignCenter)
            info.setStyleSheet(
                f"color: {brand.WARNING}; padding: 40px; font-size: 13px;"
            )
            self.assign_layout.addWidget(info)

        for idx, job in secili_jobs:
            row = self._make_assign_row(idx, job)
            self.assign_layout.addWidget(row)

        self.assign_layout.addStretch()

    def _make_assign_row(self, job_idx: int, job: dict) -> QFrame:
        tip = (job['tip'] or '').upper()
        _, bg, fg = _hat_color(tip)
        fr = QFrame()
        fr.setStyleSheet(
            f"QFrame {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER}; "
            f"border-left: 3px solid {fg}; border-radius: 8px; }}"
        )
        h = QHBoxLayout(fr); h.setContentsMargins(16, 12, 16, 12); h.setSpacing(14)

        # Sol: is bilgisi
        info_w = QVBoxLayout(); info_w.setSpacing(3)
        t_lbl = QLabel(f"{job['urun_kodu']}")
        t_lbl.setStyleSheet(f"color: {brand.TEXT}; font-size: 13px; font-weight: 700;")
        m_lbl = QLabel(f"{tip} · {job['urun_adi']}")
        m_lbl.setStyleSheet(f"color: {brand.TEXT_DIM}; font-size: 11px;")
        toplam = job['bara_adedi'] * job['aski_suresi_dk']
        s_lbl = QLabel(f"{job['bara_adedi']} bara × {job['aski_suresi_dk']} dk = {toplam} dk iş")
        s_lbl.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: 11px;")
        info_w.addWidget(t_lbl); info_w.addWidget(m_lbl); info_w.addWidget(s_lbl)
        info_container = QWidget()
        info_container.setLayout(info_w)
        info_container.setFixedWidth(280)
        h.addWidget(info_container)

        # Orta: chip'ler
        chips_widget = QWidget()
        chips_layout = QHBoxLayout(chips_widget)
        chips_layout.setContentsMargins(0, 0, 0, 0); chips_layout.setSpacing(6)

        # Initialize assignment if not exists
        if job_idx not in self._assignments:
            self._assignments[job_idx] = []

        calc_lbl = QLabel("-")

        def _toggle(pid, chip):
            if pid in self._assignments[job_idx]:
                self._assignments[job_idx].remove(pid)
                chip.setProperty('selected', False)
            else:
                self._assignments[job_idx].append(pid)
                chip.setProperty('selected', True)
            self._apply_chip_style(chip)
            self._update_calc(calc_lbl, toplam, len(self._assignments[job_idx]))

        from functools import partial
        # Chip wrap
        wrap = QWidget()
        wrap_layout = QHBoxLayout(wrap)
        wrap_layout.setContentsMargins(0, 0, 0, 0)
        wrap_layout.setSpacing(6)

        # Flow layout yok, basit cok satirli icin:
        grid_w = QWidget()
        from PySide6.QtWidgets import QGridLayout
        gl = QGridLayout(grid_w); gl.setContentsMargins(0, 0, 0, 0); gl.setSpacing(6)
        cols_per_row = 5
        for p_idx, p in enumerate(self._personeller):
            pid = p['id']
            chip = QPushButton(f"{p['ad']} {p['soyad'][:1]}.")
            chip.setCheckable(True)
            selected = pid in self._assignments[job_idx]
            chip.setChecked(selected)
            chip.setProperty('selected', selected)
            chip.setProperty('pid', pid)
            self._apply_chip_style(chip)
            chip.clicked.connect(partial(_toggle, pid, chip))
            r, c = divmod(p_idx, cols_per_row)
            gl.addWidget(chip, r, c)
        h.addWidget(grid_w, 1)

        # Sag: hesap
        calc_w = QVBoxLayout(); calc_w.setSpacing(0)
        calc_lbl.setStyleSheet(f"color: {brand.SUCCESS}; font-size: 18px; font-weight: 700;")
        calc_lbl.setAlignment(Qt.AlignRight)
        calc_sub = QLabel("seçim bekleniyor")
        calc_sub.setStyleSheet(f"color: {brand.TEXT_MUTED}; font-size: 10px;")
        calc_sub.setAlignment(Qt.AlignRight)
        calc_lbl.setObjectName(f"calc_{job_idx}")
        calc_sub.setObjectName(f"calc_sub_{job_idx}")
        calc_w.addWidget(calc_lbl); calc_w.addWidget(calc_sub)
        calc_container = QWidget(); calc_container.setLayout(calc_w)
        calc_container.setFixedWidth(110)
        h.addWidget(calc_container)

        # Initial calculation
        self._update_calc(calc_lbl, toplam, len(self._assignments[job_idx]))
        return fr

    def _apply_chip_style(self, chip: QPushButton):
        selected = chip.property('selected')
        if selected:
            chip.setStyleSheet(
                f"QPushButton {{ background: rgba(220,38,38,0.15); color: #F87171; "
                f"border: 1px solid {brand.PRIMARY}; border-radius: 14px; "
                f"padding: 5px 14px; font-size: 12px; font-weight: 600; }}"
            )
        else:
            chip.setStyleSheet(
                f"QPushButton {{ background: {brand.BG_INPUT}; color: {brand.TEXT}; "
                f"border: 1px solid {brand.BORDER}; border-radius: 14px; "
                f"padding: 5px 14px; font-size: 12px; }}"
                f"QPushButton:hover {{ border-color: {brand.PRIMARY}; }}"
            )

    def _update_calc(self, lbl: QLabel, toplam: int, n: int):
        if n == 0:
            lbl.setText("-")
            sub = lbl.parent().findChild(QLabel, lbl.objectName().replace("calc_", "calc_sub_"))
            if sub: sub.setText("seçim bekleniyor")
        else:
            g = math.ceil(toplam / n) if toplam else 0
            lbl.setText(f"{g} dk")
            sub = lbl.parent().findChild(QLabel, lbl.objectName().replace("calc_", "calc_sub_"))
            if sub: sub.setText(f"{n} kişi ile")

    # ==================================================================
    # EVENT HANDLERS
    # ==================================================================
    def _on_vardiya_changed(self):
        self._update_summary()

    def _on_override_toggled(self):
        self.override_row.setVisible(self.override_check.isChecked())
        self._update_summary()

    def _refresh_plan(self):
        tarih = self.tarih_edit.date().toPython()
        v = self._get_selected_vardiya()
        if not v:
            self._jobs = []
        else:
            hat_filtre = self.hat_combo.currentData() if hasattr(self, 'hat_combo') else None
            self._jobs = self._load_plan_urunler(tarih, v['id'], hat_filtre)
        self._assignments = {}
        self._fill_job_table()

    def _on_job_check(self, idx: int, state: int):
        if 0 <= idx < len(self._jobs):
            self._jobs[idx]['secili'] = (state == Qt.Checked.value or state == 2)
            self._update_summary()

    def _on_job_bara(self, idx: int, val: int):
        if 0 <= idx < len(self._jobs):
            self._jobs[idx]['bara_adedi'] = val
            # Toplam sure hucresini guncelle
            toplam = val * self._jobs[idx]['aski_suresi_dk']
            it = QTableWidgetItem(f"{toplam} dk")
            it.setForeground(QColor(brand.SUCCESS))
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.job_table.setItem(idx, 7, it)
            self._update_summary()

    def _on_job_sure(self, idx: int, val: int):
        if 0 <= idx < len(self._jobs):
            self._jobs[idx]['aski_suresi_dk'] = val
            toplam = self._jobs[idx]['bara_adedi'] * val
            it = QTableWidgetItem(f"{toplam} dk")
            it.setForeground(QColor(brand.SUCCESS))
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.job_table.setItem(idx, 7, it)
            self._update_summary()

    def _on_select_all(self):
        all_selected = all(j['secili'] for j in self._jobs)
        new_val = not all_selected
        for i in range(len(self._jobs)):
            self._jobs[i]['secili'] = new_val
            # CheckBox widget'ini guncelle
            container = self.job_table.cellWidget(i, 0)
            if container:
                cb = container.findChild(QCheckBox)
                if cb:
                    cb.blockSignals(True)
                    cb.setChecked(new_val)
                    cb.blockSignals(False)
        self._update_summary()

    def _on_goto_faz2(self):
        secili = [j for j in self._jobs if j['secili']]
        if not secili:
            QMessageBox.warning(self, "Uyarı", "En az bir iş seçmelisiniz!")
            return

        # Her is icin aski suresi dolu mu?
        eksik = [j['urun_kodu'] for j in secili if not j['aski_suresi_dk']]
        if eksik:
            ret = QMessageBox.question(
                self, "Askı Süresi Tanımlanmamış",
                f"Şu ürünlerin askı süresi 0:\n\n{', '.join(eksik[:5])}"
                f"{'...' if len(eksik) > 5 else ''}\n\n"
                f"Yine de devam etmek istiyor musun? (Süre 0 olarak kaydedilir, "
                f"ürün kartlarından bara_aski_suresi_dk tanımla.)",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret != QMessageBox.Yes:
                return

        # Personel listesini yukle
        tarih = self.tarih_edit.date().toPython()
        v = self._get_selected_vardiya()
        if not v:
            QMessageBox.warning(self, "Uyarı", "Vardiya seçilmedi!")
            return
        self._personeller = self._load_personel(tarih, v['id'])

        self._build_faz2()
        self._set_active_phase(2)

    def _on_save(self):
        secili = [j for j in self._jobs if j['secili']]
        if not secili:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek iş yok!")
            return

        # Varsayilan olarak her ise bos personel atamasi da kabul edilir
        # Kullaniciya uyari ver
        bos_atama = [j['urun_kodu'] for idx, j in enumerate(self._jobs)
                     if j['secili'] and not self._assignments.get(idx)]
        if bos_atama:
            ret = QMessageBox.question(
                self, "Personel Atanmamış",
                f"Şu işlere personel atanmamış:\n{', '.join(bos_atama[:5])}"
                f"{'...' if len(bos_atama) > 5 else ''}\n\nYine de kaydedilsin mi?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret != QMessageBox.Yes:
                return

        ok, msg = self._save_plan()
        if ok:
            QMessageBox.information(self, "Başarılı", msg)
        else:
            QMessageBox.critical(self, "Hata", msg)
