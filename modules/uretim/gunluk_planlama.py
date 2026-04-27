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
    QComboBox, QDateEdit, QTimeEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QSpinBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QDate, QTime
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
    def _load_hat_bara_kapasite(self) -> dict:
        """Kaplama turune gore hat bara stok adedini dondurur.
        Return: {'KTF': 30, 'ZN': 20, ...}
        """
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT kt.kod,
                       ISNULL(SUM(ISNULL(h.bara_stok_adet, 0)), 0) as bara_stok
                FROM tanim.uretim_hatlari h
                LEFT JOIN tanim.kaplama_turleri kt ON h.kaplama_turu_id = kt.id
                WHERE h.aktif_mi = 1 AND (h.silindi_mi IS NULL OR h.silindi_mi = 0)
                  AND kt.kod IS NOT NULL
                GROUP BY kt.kod
            """)
            return {r[0]: int(r[1] or 0) for r in cur.fetchall()}
        except Exception as e:
            print(f"[GunlukPlan] bara kapasite hata: {e}")
            return {}

    def _vardiya_saatleri(self) -> tuple:
        """(baslangic_time, bitis_time, toplam_dk) — filtre bardan oku."""
        if hasattr(self, 'baslangic_time'):
            bas = self.baslangic_time.time().toPython()
            total = self.vardiya_sure_spin.value() if hasattr(self, 'vardiya_sure_spin') else 480
        else:
            bas = _time(7, 30)
            total = 480
        bm = bas.hour * 60 + bas.minute
        em = (bm + total) % (24 * 60)
        bh, bmi = divmod(em, 60)
        bit = _time(bh, bmi)
        return (bas, bit, total)

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
                       ISNULL(u.gunluk_ihtiyac_adet, 0) as ihtiyac,
                       ISNULL(u.stok_aski_adet, 1) as stok_aski,
                       ISNULL(u.aski_adedi, 1) as aski_adedi,
                       ISNULL(u.bara_bosaltma_suresi_dk, 40) as bosaltma_sure,
                       ISNULL(u.bara_aski_suresi_dk, 40) as aski_sure,
                       ISNULL((
                           SELECT SUM(sb.miktar - ISNULL(sb.rezerve_miktar, 0))
                           FROM stok.stok_bakiye sb
                           WHERE sb.urun_id = u.id
                             AND sb.durum_kodu = 'GIRIS_ONAY'
                             AND sb.miktar - ISNULL(sb.rezerve_miktar, 0) > 0
                       ), 0) as stok_adet,
                       ISNULL((
                           SELECT SUM(sb.miktar)
                           FROM stok.stok_bakiye sb
                           WHERE sb.urun_id = u.id
                             AND sb.durum_kodu IN ('KABUL', 'GIRIS_KALITE')
                       ), 0) as stok_bekleyen
                FROM stok.urunler u
                LEFT JOIN musteri.cariler c ON u.cari_id = c.id
                LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                LEFT JOIN kaplama.plc_recete_tanimlari r ON TRY_CAST(u.recete_no AS INT) = r.recete_no
                WHERE u.aktif_mi = 1 AND u.urun_tipi = 'MAMUL'
                  AND u.gunluk_ihtiyac_adet IS NOT NULL AND u.gunluk_ihtiyac_adet > 0
                ORDER BY kt.kod, c.unvan, u.urun_kodu
            """)
            talepler = []
            VARDIYA_DK = 480  # sabit vardiya suresi
            hat_bara_map = self._load_hat_bara_kapasite()  # {kap_kod: bara_stok}
            for r in cur.fetchall():
                bara_adedi_kart = int(r[10] or 0)
                ihtiyac = int(r[11] or 0)
                recete_sure = int(r[9] or 0)
                stok_aski = int(r[12] or 1)
                aski_adedi = int(r[13] or 1)      # 1 barada kac aski
                bosaltma_sure = int(r[14] or 40)
                aski_sure = int(r[15] or 40)
                stok_adet = int(r[16] or 0)
                stok_bekleyen = int(r[17] or 0)

                # Yapilacak bara = ceil(ihtiyac / 1 barada parca)
                yapilacak_bara = math.ceil(ihtiyac / bara_adedi_kart) if bara_adedi_kart > 0 else 0

                # Hat is yuku (bara hat uzerinde kalma toplami)
                toplam_hat_dk = yapilacak_bara * recete_sure

                # Personel is yuku (asma + bosaltma, bara basina)
                personel_dk_per_bara = aski_sure + bosaltma_sure
                toplam_personel_dk = yapilacak_bara * personel_dk_per_bara

                # Aski dongu: asma + hat + bosaltma (1 askinin mesgul suresi)
                aski_dongu_dk = aski_sure + recete_sure + bosaltma_sure
                aski_turnover = (VARDIYA_DK / aski_dongu_dk) if aski_dongu_dk > 0 else 0

                # 1 aski = 1 bara. Paralel bara = min(stok_aski, hat.bara_stok)
                kap_kod = (r[6] or '').upper()
                hat_bara_stok = hat_bara_map.get(kap_kod, 0)
                paralel_bara = min(stok_aski, hat_bara_stok) if hat_bara_stok > 0 else stok_aski
                # Hangi kisit? (darbogaz)
                if hat_bara_stok > 0 and stok_aski > hat_bara_stok:
                    darbogaz = 'BARA'  # hat'ta yeterli bara yok
                elif hat_bara_stok > 0 and stok_aski < hat_bara_stok:
                    darbogaz = 'ASKI'
                else:
                    darbogaz = 'ESIT'
                # Vardiyada toplam bara kapasitesi:
                aski_kapasite = int(paralel_bara * aski_turnover) if aski_turnover else 0
                # Bara sayisi ihtiyaci
                aski_ihtiyaci = yapilacak_bara

                # Staggered scheduling: her askinin giris/cikis zamanlari
                # T=0'da hepsi baslar, dongu sonunda hepsi biter, sonraki grup cikinca baslar
                # batch_count = kac tam grup (ceil)
                batch_count = math.ceil(yapilacak_bara / paralel_bara) if paralel_bara > 0 else 0
                # is_sure_dk = toplam is suresi (grup grup arka arkaya)
                is_sure_dk = batch_count * aski_dongu_dk
                # Ilk bara giris: T=0 (vardiya bas)
                ilk_giris_dk = 0
                # Ilk bara cikis: T=dongu
                ilk_cikis_dk = aski_dongu_dk
                # Son bara cikis: T=is_sure_dk
                son_cikis_dk = is_sure_dk
                # Bir sonraki cevrim (aski bosalip tekrar kullanilir): T=dongu
                sonraki_cevrim_dk = aski_dongu_dk

                # Gerekli personel (vardiya basi)
                gerekli_personel = toplam_personel_dk / VARDIYA_DK if VARDIYA_DK else 0

                # Cevrim tamamlanabilir mi
                aski_yeter = (aski_kapasite >= aski_ihtiyaci) if aski_ihtiyaci else True

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
                    'toplam_dk': toplam_hat_dk,            # geriye uyumluluk icin
                    'toplam_hat_dk': toplam_hat_dk,
                    'toplam_personel_dk': toplam_personel_dk,
                    'stok_aski': stok_aski,
                    'aski_adedi': aski_adedi,
                    'aski_sure_dk': aski_sure,
                    'bosaltma_sure_dk': bosaltma_sure,
                    'aski_dongu_dk': aski_dongu_dk,
                    'aski_turnover': round(aski_turnover, 2),
                    'aski_kapasite': aski_kapasite,
                    'aski_ihtiyaci': aski_ihtiyaci,
                    'aski_yeter': aski_yeter,
                    'hat_bara_stok': hat_bara_stok,
                    'paralel_bara': paralel_bara,
                    'darbogaz': darbogaz,
                    'gerekli_personel': round(gerekli_personel, 2),
                    'batch_count': batch_count,
                    'is_sure_dk': is_sure_dk,
                    'ilk_giris_dk': ilk_giris_dk,
                    'ilk_cikis_dk': ilk_cikis_dk,
                    'son_cikis_dk': son_cikis_dk,
                    'sonraki_cevrim_dk': sonraki_cevrim_dk,
                    'stok_adet': stok_adet,
                    'stok_bekleyen': stok_bekleyen,
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
        """Taslak satirlarini yuklerken canli stok bilgisini de join ile cek."""
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT s.id, s.vardiya_id, v.kod as vardiya_kod,
                       s.urun_id, u.urun_kodu, u.urun_adi,
                       s.cari_id, c.unvan as cari_unvan,
                       s.kaplama_turu_id, kt.kod as kap_kod,
                       s.recete_no, s.talep_adet, s.bara_adedi,
                       s.bara_parca, s.bara_sure_dk, s.toplam_sure_dk,
                       s.sira_no, s.kaynak,
                       ISNULL((SELECT SUM(sb.miktar - ISNULL(sb.rezerve_miktar, 0))
                               FROM stok.stok_bakiye sb
                               WHERE sb.urun_id = s.urun_id
                                 AND sb.durum_kodu = 'GIRIS_ONAY'
                                 AND sb.miktar - ISNULL(sb.rezerve_miktar, 0) > 0), 0) as stok_adet,
                       ISNULL((SELECT SUM(sb.miktar) FROM stok.stok_bakiye sb
                               WHERE sb.urun_id = s.urun_id
                                 AND sb.durum_kodu IN ('KABUL', 'GIRIS_KALITE')), 0) as stok_bekleyen
                FROM planlama.gunluk_taslak_satir s
                LEFT JOIN tanim.vardiyalar v ON s.vardiya_id = v.id
                LEFT JOIN stok.urunler u ON s.urun_id = u.id
                LEFT JOIN musteri.cariler c ON s.cari_id = c.id
                LEFT JOIN tanim.kaplama_turleri kt ON s.kaplama_turu_id = kt.id
                WHERE s.taslak_id = ?
                ORDER BY s.sira_no, s.id
            """, (taslak_id,))
            rows = []
            VARDIYA_DK = 480
            hat_bara_map = self._load_hat_bara_kapasite()
            # Urun id'lerini topla, aski/bosaltma/aski_adedi'ni tek sorgu ile cek
            row_data = cur.fetchall()
            urun_ids = list(set(int(r[3]) for r in row_data if r[3]))
            extras = {}
            if urun_ids:
                ph = ','.join(['?'] * len(urun_ids))
                cur.execute(f"""
                    SELECT id,
                           ISNULL(stok_aski_adet, 1),
                           ISNULL(aski_adedi, 1),
                           ISNULL(bara_aski_suresi_dk, 40),
                           ISNULL(bara_bosaltma_suresi_dk, 40)
                    FROM stok.urunler WHERE id IN ({ph})
                """, urun_ids)
                for er in cur.fetchall():
                    extras[int(er[0])] = {
                        'stok_aski': int(er[1]),
                        'aski_adedi': int(er[2]),
                        'aski_sure': int(er[3]),
                        'bosaltma_sure': int(er[4]),
                    }

            for r in row_data:
                urun_id = int(r[3]) if r[3] else None
                ex = extras.get(urun_id, {'stok_aski': 1, 'aski_adedi': 1, 'aski_sure': 40, 'bosaltma_sure': 40})
                yapilacak_bara = int(r[12] or 0)
                recete_sure = int(r[14] or 0)
                personel_dk_per_bara = ex['aski_sure'] + ex['bosaltma_sure']
                toplam_personel_dk = yapilacak_bara * personel_dk_per_bara
                aski_dongu_dk = ex['aski_sure'] + recete_sure + ex['bosaltma_sure']
                aski_turnover = (VARDIYA_DK / aski_dongu_dk) if aski_dongu_dk > 0 else 0
                # Paralel bara = min(stok_aski, hat.bara_stok) — hat kisidi
                kap_kod = (r[9] or '').upper()
                hat_bara_stok = hat_bara_map.get(kap_kod, 0)
                paralel_bara = min(ex['stok_aski'], hat_bara_stok) if hat_bara_stok > 0 else ex['stok_aski']
                if hat_bara_stok > 0 and ex['stok_aski'] > hat_bara_stok:
                    darbogaz = 'BARA'
                elif hat_bara_stok > 0 and ex['stok_aski'] < hat_bara_stok:
                    darbogaz = 'ASKI'
                else:
                    darbogaz = 'ESIT'
                aski_kapasite = int(paralel_bara * aski_turnover) if aski_turnover else 0
                aski_ihtiyaci = yapilacak_bara
                gerekli_personel = toplam_personel_dk / VARDIYA_DK if VARDIYA_DK else 0
                aski_yeter = (aski_kapasite >= aski_ihtiyaci) if aski_ihtiyaci else True

                rows.append({
                    'id': int(r[0]),
                    'vardiya_id': int(r[1]) if r[1] else None,
                    'vardiya_kod': r[2] or '',
                    'urun_id': urun_id,
                    'urun_kodu': r[4] or '',
                    'urun_adi': r[5] or '',
                    'cari_id': int(r[6]) if r[6] else None,
                    'cari_unvan': r[7] or '',
                    'kaplama_turu_id': int(r[8]) if r[8] else None,
                    'kap_kod': r[9] or '',
                    'recete_no': r[10] or '',
                    'ihtiyac_adet': int(r[11] or 0),
                    'yapilacak_bara': yapilacak_bara,
                    'bara_parca': int(r[13] or 0),
                    'recete_sure_dk': recete_sure,
                    'toplam_dk': int(r[15] or 0),
                    'toplam_hat_dk': int(r[15] or 0),
                    'toplam_personel_dk': toplam_personel_dk,
                    'sira_no': int(r[16] or 0),
                    'kaynak': r[17] or 'ANLASMA',
                    'stok_adet': int(r[18] or 0),
                    'stok_bekleyen': int(r[19] or 0),
                    'stok_aski': ex['stok_aski'],
                    'aski_adedi': ex['aski_adedi'],
                    'aski_sure_dk': ex['aski_sure'],
                    'bosaltma_sure_dk': ex['bosaltma_sure'],
                    'aski_dongu_dk': aski_dongu_dk,
                    'aski_turnover': round(aski_turnover, 2),
                    'aski_kapasite': aski_kapasite,
                    'aski_ihtiyaci': aski_ihtiyaci,
                    'aski_yeter': aski_yeter,
                    'hat_bara_stok': hat_bara_stok,
                    'paralel_bara': paralel_bara,
                    'darbogaz': darbogaz,
                    'gerekli_personel': round(gerekli_personel, 2),
                })
            conn.close()
            return rows
        except Exception as e:
            print(f"[GunlukPlan] satir yukleme hata: {e}")
            import traceback; traceback.print_exc()
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
                from core.yetki_manager import YetkiManager
                _olusturan_id = YetkiManager._current_user_id
                cur.execute("""
                    INSERT INTO uretim.planlama
                        (tarih, hat_id, vardiya_id, is_emri_id,
                         planlanan_bara, durum, olusturan_id, olusturma_tarihi)
                    VALUES (?, NULL, ?, ?, ?, N'PLANLANDI', ?, GETDATE())
                """, (tarih, v_id, ie_id, bara, _olusturan_id))
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

        fl.addWidget(QLabel("Başlangıç:", styleSheet=ls))
        self.baslangic_time = QTimeEdit()
        self.baslangic_time.setDisplayFormat("HH:mm")
        self.baslangic_time.setTime(QTime(7, 30))
        self.baslangic_time.setStyleSheet(f"QTimeEdit {{ {ins} max-width: 85px; }}")
        self.baslangic_time.setToolTip("Vardiya başlangıç saati.\n"
                                        "İşler bu saatten itibaren sıralı olarak planlanır.")
        self.baslangic_time.timeChanged.connect(lambda _: self._fill_table())
        fl.addWidget(self.baslangic_time)

        fl.addWidget(QLabel("Vardiya:", styleSheet=ls))
        self.vardiya_sure_spin = QSpinBox()
        self.vardiya_sure_spin.setRange(60, 1440)
        self.vardiya_sure_spin.setSuffix(" dk")
        self.vardiya_sure_spin.setValue(480)
        self.vardiya_sure_spin.setStyleSheet(f"QSpinBox {{ {ins} max-width: 90px; }}")
        self.vardiya_sure_spin.valueChanged.connect(lambda _: self._fill_table())
        fl.addWidget(self.vardiya_sure_spin)

        self.durum_lbl = QLabel("TASLAK")
        self.durum_lbl.setStyleSheet(
            f"background: rgba(220,38,38,0.12); color: {brand.PRIMARY}; "
            f"padding: 6px 14px; border-radius: 12px; font-size: 12px; "
            f"font-weight: 700; border: 1px solid {brand.PRIMARY};"
        )
        fl.addWidget(self.durum_lbl)

        fl.addWidget(QLabel("Askıcı sayısı:", styleSheet=ls))
        self.askici_spin = QSpinBox()
        self.askici_spin.setRange(0, 99)
        self.askici_spin.setValue(5)
        self.askici_spin.setStyleSheet(f"QSpinBox {{ {ins} max-width: 70px; }}")
        self.askici_spin.setToolTip("Bu vardiyada görevli askılamacı sayısı.\n"
                                     "Planlamanın altında gerekli vs mevcut karşılaştırması gösterilir.")
        self.askici_spin.valueChanged.connect(lambda _: self._fill_table())
        fl.addWidget(self.askici_spin)

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
        self.stat_personel = self._mk_stat("Gerekli / Mevcut Kişi", "0 / 0", brand.WARNING)
        for s in (self.stat_talep, self.stat_bara, self.stat_ktl, self.stat_zn,
                  self.stat_diger, self.stat_personel):
            sl.addWidget(s)
        layout.addWidget(sf)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(16)
        self.table.setHorizontalHeaderLabels([
            "Müşteri", "Kap.", "Ürün Kodu", "Ürün Adı",
            "İhtiyaç", "Onaylı", "Bekleyen", "Bara/Parça", "Yapılacak Bara",
            "Reçete Süre (dk)", "Toplam (dk)",
            "Gerekli Kişi", "Durum", "Saat (giriş→bitiş)",
            "Vardiya", "Kaynak"
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
        self.table.setColumnWidth(4, 80)    # İhtiyaç
        self.table.setColumnWidth(5, 80)    # Onaylı
        self.table.setColumnWidth(6, 80)    # Bekleyen
        self.table.setColumnWidth(7, 80)    # Bara/Parça
        self.table.setColumnWidth(8, 100)   # Yapılacak Bara
        self.table.setColumnWidth(9, 100)   # Reçete Süre
        self.table.setColumnWidth(10, 100)  # Toplam
        self.table.setColumnWidth(11, 90)   # Gerekli Kişi
        self.table.setColumnWidth(12, 120)  # Durum
        self.table.setColumnWidth(13, 140)  # Saat (giriş→bitiş)
        self.table.setColumnWidth(14, 90)   # Vardiya
        self.table.setColumnWidth(15, 80)   # Kaynak
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table, 1)

        # BARA TIMELINE (vardiya bazlı, her bara ayrı satır)
        timeline_lbl = QLabel("📋 Bara Detayı (vardiya × bara) — her bara ayrı satır, giriş/çıkış saatleri")
        timeline_lbl.setStyleSheet(f"color: {brand.TEXT}; font-size: 13px; font-weight: 600; "
                                     f"margin-top: 8px;")
        layout.addWidget(timeline_lbl)

        self.timeline_table = QTableWidget()
        self.timeline_table.setColumnCount(7)
        self.timeline_table.setHorizontalHeaderLabels([
            "Bara #", "Hat", "Giriş Saati", "Ürün", "Müşteri", "Çıkış Saati", "Askı #"
        ])
        self.timeline_table.setStyleSheet(f"""
            QTableWidget {{ background: {brand.BG_CARD}; border: 1px solid {brand.BORDER};
                border-radius: 10px; color: {brand.TEXT}; gridline-color: {brand.BORDER};
                font-size: 12px; }}
            QTableWidget::item {{ padding: 6px 8px; }}
            QHeaderView::section {{ background: rgba(0,0,0,0.3); color: {brand.TEXT_MUTED};
                padding: 8px; border: none; border-bottom: 2px solid {brand.PRIMARY};
                font-weight: 600; font-size: 12px; }}
        """)
        self.timeline_table.verticalHeader().setVisible(False)
        self.timeline_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.timeline_table.setColumnWidth(0, 70)
        self.timeline_table.setColumnWidth(1, 70)
        self.timeline_table.setColumnWidth(2, 100)
        self.timeline_table.setColumnWidth(4, 180)
        self.timeline_table.setColumnWidth(5, 100)
        self.timeline_table.setColumnWidth(6, 70)
        self.timeline_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.timeline_table.setMinimumHeight(260)
        layout.addWidget(self.timeline_table)

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
        # Hat bazinda grupla
        from collections import defaultdict
        gruplar = defaultdict(list)
        for s in self._satirlar:
            key = (s.get('kap_kod') or '').upper() or 'DIGER'
            gruplar[key].append(s)

        # Sira: KTL, ZN/ZNNI, Toz/Nikel, Diger
        oncelik_sira = ['KTF', 'KATAFOREZ', 'ZN', 'ZNNI', 'ASITZN', 'NIKEL', 'KROM', 'TOZ']
        sirali_gruplar = []
        for kod in oncelik_sira:
            if kod in gruplar:
                sirali_gruplar.append((kod, gruplar[kod]))
                del gruplar[kod]
        for kod, items in gruplar.items():
            sirali_gruplar.append((kod, items))

        # Toplam satir sayisi = satir + her grup icin 1 header + 1 altoplam + grandtotal
        grup_sayisi = len(sirali_gruplar)
        total_rows = len(self._satirlar) + (grup_sayisi * 2) + (1 if grup_sayisi > 0 else 0)
        self.table.setRowCount(total_rows)

        # Bara kapasitesi (hat bazli) + vardiya suresi
        bara_kap_map = self._load_hat_bara_kapasite()
        vardiya_dk = 480  # default bir vardiya

        row = 0
        grand_adet = 0; grand_bara = 0; grand_dk = 0
        # Satir -> gercek index esleme (vardiya combo handler icin)
        self._row_to_satir_idx = {}

        for kod, items in sirali_gruplar:
            bg, fg, short = _kap_color(kod)
            grup_bara_ihtiyac = sum(s['yapilacak_bara'] for s in items)
            grup_toplam_dk = sum(s['toplam_dk'] for s in items)
            # Ortalama recete suresi
            avg_recete = (grup_toplam_dk / grup_bara_ihtiyac) if grup_bara_ihtiyac else 0
            # Turnover (1 vardiyada kac kez)
            turnover = (vardiya_dk / avg_recete) if avg_recete else 0
            # Bara kapasitesi
            bara_stok = bara_kap_map.get(kod, 0)
            bara_kapasite = int(bara_stok * turnover) if turnover else 0

            # Uyari metni
            if bara_stok == 0:
                kap_txt = "  ⚠ Bara stok tanımsız"
                kap_color = brand.WARNING
            elif grup_bara_ihtiyac > bara_kapasite and bara_kapasite > 0:
                kap_txt = f"  ⚠ {grup_bara_ihtiyac} bara gerekli / {bara_kapasite} kapasite — YETMEZ"
                kap_color = brand.ERROR
            elif bara_kapasite > 0:
                kap_txt = f"  ✓ {grup_bara_ihtiyac} bara / {bara_kapasite} kapasite"
                kap_color = brand.SUCCESS
            else:
                kap_txt = ""
                kap_color = brand.TEXT_DIM

            # --- Grup Header ---
            hdr = QTableWidgetItem(f"  ▼ {short}  ({len(items)} talep){kap_txt}")
            hdr.setForeground(QColor(kap_color if kap_txt else fg))
            f = self._bold_font(); f.setPointSize(11); hdr.setFont(f)
            hdr.setBackground(QColor(bg.replace('0.15)', '0.25)')) if 'rgba' in bg else QColor(bg))
            self.table.setItem(row, 0, hdr)
            for c in range(1, 16):
                empty = QTableWidgetItem("")
                empty.setBackground(QColor(35, 45, 60))
                self.table.setItem(row, c, empty)
            self.table.setSpan(row, 0, 1, 16)
            self.table.setRowHeight(row, 34)
            row += 1

            grup_adet = 0; grup_bara = 0; grup_dk = 0
            # ÇOK VARDIYALI SCHEDULER: is sigmazsa sonraki vardiyaya tasir
            # tanim.vardiyalar'dan siralanmis vardiya listesi (bas dakika, bit dakika)
            vardiyalar_sorted = sorted(self._vardiyalar, key=lambda v: (
                v['bas'].hour * 60 + v['bas'].minute if isinstance(v['bas'], _time) else 0
            ))
            vardiya_spans = []
            for v in vardiyalar_sorted:
                bm = v['bas'].hour * 60 + v['bas'].minute if isinstance(v['bas'], _time) else 0
                em = v['bit'].hour * 60 + v['bit'].minute if isinstance(v['bit'], _time) else bm + 480
                if em <= bm:  # gece vardiyasi: sonraki gune sar
                    em += 24 * 60
                vardiya_spans.append({'id': v['id'], 'kod': v['kod'], 'bas': bm, 'bit': em})

            # Kullanicinin girdigi baslangic saati — ilk vardiyayi bundan basla
            v_bas_user, _, _ = self._vardiya_saatleri()
            cur_dk = v_bas_user.hour * 60 + v_bas_user.minute
            # Bu dakikaya en yakin/icinde olan vardiyayi bul
            v_idx = 0
            for i, vs in enumerate(vardiya_spans):
                if vs['bas'] <= cur_dk < vs['bit']:
                    v_idx = i; break
            else:
                v_idx = 0

            for s in items:
                is_sure = s.get('is_sure_dk', 0) or 0
                # Mevcut vardiyaya sigar mi?
                while vardiya_spans and cur_dk + is_sure > vardiya_spans[v_idx]['bit']:
                    # Sonraki vardiyaya ge
                    if v_idx + 1 < len(vardiya_spans):
                        v_idx += 1
                        cur_dk = vardiya_spans[v_idx]['bas']
                    else:
                        # Tum vardiyalar doldu — ertesi gunun ilk vardiyasi
                        v_idx = 0
                        cur_dk = vardiya_spans[0]['bas'] + 24 * 60
                        break

                s['sched_giris_dk'] = cur_dk
                s['sched_bitis_dk'] = cur_dk + is_sure
                # Otomatik vardiya ata (kullanici degistirebilir)
                if vardiya_spans and s.get('vardiya_id') is None:
                    s['vardiya_id'] = vardiya_spans[v_idx]['id']
                s['sched_vardiya_kod'] = vardiya_spans[v_idx]['kod'] if vardiya_spans else ''
                cur_dk += is_sure
                self._row_to_satir_idx[row] = self._satirlar.index(s)
                self._fill_data_row(row, s)
                grup_adet += s['ihtiyac_adet']
                grup_bara += s['yapilacak_bara']
                grup_dk += s['toplam_dk']
                row += 1

            # --- Grup altoplami ---
            grup_stok = sum(s.get('stok_adet', 0) or 0 for s in items)
            grup_bek = sum(s.get('stok_bekleyen', 0) or 0 for s in items)
            alt = QTableWidgetItem(f"  ↳ {short} Toplamı")
            alt.setForeground(QColor(brand.TEXT))
            alt.setFont(self._bold_font())
            alt.setBackground(QColor(25, 31, 41))
            self.table.setItem(row, 0, alt)
            for c in range(1, 4):
                e = QTableWidgetItem(""); e.setBackground(QColor(25, 31, 41))
                self.table.setItem(row, c, e)
            # 4 toplam adet
            it = QTableWidgetItem(f"{grup_adet:,}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it.setFont(self._bold_font())
            it.setForeground(QColor(fg))
            it.setBackground(QColor(25, 31, 41))
            self.table.setItem(row, 4, it)
            # 5 toplam onayli stok
            it = QTableWidgetItem(f"{grup_stok:,}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it.setFont(self._bold_font())
            it.setForeground(QColor(brand.SUCCESS if grup_stok >= grup_adet else brand.WARNING))
            it.setBackground(QColor(25, 31, 41))
            self.table.setItem(row, 5, it)
            # 6 toplam bekleyen
            it = QTableWidgetItem(f"{grup_bek:,}" if grup_bek > 0 else "-")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it.setFont(self._bold_font())
            it.setForeground(QColor(brand.WARNING if grup_bek > 0 else brand.TEXT_DIM))
            it.setBackground(QColor(25, 31, 41))
            self.table.setItem(row, 6, it)
            # 7 boş (bara/parça)
            e = QTableWidgetItem(""); e.setBackground(QColor(25, 31, 41))
            self.table.setItem(row, 7, e)
            # 8 toplam bara
            it = QTableWidgetItem(f"{grup_bara:,}")
            it.setTextAlignment(Qt.AlignCenter)
            it.setFont(self._bold_font())
            it.setForeground(QColor(fg))
            it.setBackground(QColor(25, 31, 41))
            self.table.setItem(row, 8, it)
            # 9 boş (reçete)
            e = QTableWidgetItem(""); e.setBackground(QColor(25, 31, 41))
            self.table.setItem(row, 9, e)
            # 10 toplam dk
            it = QTableWidgetItem(f"{grup_dk:,} dk")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it.setFont(self._bold_font())
            it.setForeground(QColor(brand.SUCCESS))
            it.setBackground(QColor(25, 31, 41))
            self.table.setItem(row, 10, it)
            # 11-14 boş (gerekli kişi, durum, vardiya, kaynak)
            for c in (11, 12, 13, 14, 15):
                e = QTableWidgetItem(""); e.setBackground(QColor(25, 31, 41))
                self.table.setItem(row, c, e)
            self.table.setRowHeight(row, 36)
            row += 1

            grand_adet += grup_adet; grand_bara += grup_bara; grand_dk += grup_dk

        # --- Grand Total ---
        if grup_sayisi > 0:
            grand_stok = sum(s.get('stok_adet', 0) or 0 for s in self._satirlar)
            grand_bek = sum(s.get('stok_bekleyen', 0) or 0 for s in self._satirlar)
            gt = QTableWidgetItem("  ═ GENEL TOPLAM ═")
            gt.setForeground(QColor(brand.PRIMARY))
            f = self._bold_font(); f.setPointSize(12); gt.setFont(f)
            gt.setBackground(QColor(45, 15, 20))
            self.table.setItem(row, 0, gt)
            for c in range(1, 4):
                e = QTableWidgetItem(""); e.setBackground(QColor(45, 15, 20))
                self.table.setItem(row, c, e)
            # 4 adet
            it = QTableWidgetItem(f"{grand_adet:,}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it.setFont(f); it.setForeground(QColor(brand.PRIMARY))
            it.setBackground(QColor(45, 15, 20))
            self.table.setItem(row, 4, it)
            # 5 onaylı
            it = QTableWidgetItem(f"{grand_stok:,}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it.setFont(f)
            it.setForeground(QColor(brand.SUCCESS if grand_stok >= grand_adet else brand.WARNING))
            it.setBackground(QColor(45, 15, 20))
            self.table.setItem(row, 5, it)
            # 6 bekleyen
            it = QTableWidgetItem(f"{grand_bek:,}" if grand_bek > 0 else "-")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it.setFont(f)
            it.setForeground(QColor(brand.WARNING if grand_bek > 0 else brand.TEXT_DIM))
            it.setBackground(QColor(45, 15, 20))
            self.table.setItem(row, 6, it)
            # 7 boş (bara/parça)
            e = QTableWidgetItem(""); e.setBackground(QColor(45, 15, 20))
            self.table.setItem(row, 7, e)
            # 8 bara
            it = QTableWidgetItem(f"{grand_bara:,}")
            it.setTextAlignment(Qt.AlignCenter)
            it.setFont(f); it.setForeground(QColor(brand.PRIMARY))
            it.setBackground(QColor(45, 15, 20))
            self.table.setItem(row, 8, it)
            # 9 boş (reçete)
            e = QTableWidgetItem(""); e.setBackground(QColor(45, 15, 20))
            self.table.setItem(row, 9, e)
            # 10 dk
            it = QTableWidgetItem(f"{grand_dk:,} dk")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it.setFont(f); it.setForeground(QColor(brand.PRIMARY))
            it.setBackground(QColor(45, 15, 20))
            self.table.setItem(row, 10, it)
            # 11-14 boş
            for c in (11, 12, 13, 14, 15):
                e = QTableWidgetItem(""); e.setBackground(QColor(45, 15, 20))
                self.table.setItem(row, c, e)
            self.table.setRowHeight(row, 40)

        self._update_stats()
        self._fill_timeline()

    def _fill_timeline(self):
        """Bara bazli timeline: her bara ayri satir, vardiya gruplari ile."""
        if not hasattr(self, 'timeline_table'):
            return

        # Hat bazinda grupla
        from collections import defaultdict
        hat_isleri = defaultdict(list)
        for s in self._satirlar:
            hat = (s.get('kap_kod') or '?').upper()
            hat_isleri[hat].append(s)

        # Vardiya saat bilgileri (dk cinsinden spans)
        vardiya_bas, _, _ = self._vardiya_saatleri()
        baslangic_dk = vardiya_bas.hour * 60 + vardiya_bas.minute
        vardiyalar_sorted = sorted(self._vardiyalar, key=lambda v: (
            v['bas'].hour * 60 + v['bas'].minute if isinstance(v['bas'], _time) else 0
        ))
        v_spans = []  # her vardiya icin (kod, bas_dk, bit_dk) ile +24h offset
        for day_offset in (0, 1):  # bugun + yarin
            for v in vardiyalar_sorted:
                bm = v['bas'].hour * 60 + v['bas'].minute if isinstance(v['bas'], _time) else 0
                em = v['bit'].hour * 60 + v['bit'].minute if isinstance(v['bit'], _time) else bm + 480
                if em <= bm:
                    em += 24 * 60
                v_spans.append({'kod': v['kod'], 'bas': bm + day_offset * 1440,
                                 'bit': em + day_offset * 1440})

        def vardiya_bul(dk):
            for vs in v_spans:
                if vs['bas'] <= dk < vs['bit']:
                    return vs['kod']
            return '?'

        # Her hat için staggered bara üret
        tum_baralar = []  # {bara_no, hat, urun_kodu, urun_adi, musteri, giris_dk, cikis_dk, aski_idx}
        for hat, isler in hat_isleri.items():
            cur_aski_list = None  # Her hat'ta askilar ayri tutulsun
            askici_son = baslangic_dk
            for s in isler:
                paralel = max(s.get('paralel_bara', 1) or 1, 1)
                aski_sure = s.get('aski_sure_dk', 40) or 40
                dongu = s.get('aski_dongu_dk', 180) or 180
                yapilacak = s.get('yapilacak_bara', 0) or 0
                # Askı listesi ilk iş için kurulur
                if cur_aski_list is None:
                    cur_aski_list = [baslangic_dk] * paralel
                # Paralel degisiyorsa genislet
                while len(cur_aski_list) < paralel:
                    cur_aski_list.append(baslangic_dk)

                for bara_no in range(1, yapilacak + 1):
                    # En erken boşalan askı
                    aski_idx = min(range(len(cur_aski_list)), key=lambda i: cur_aski_list[i])
                    aski_bos = cur_aski_list[aski_idx]
                    giris = max(aski_bos, askici_son)
                    cikis = giris + dongu
                    cur_aski_list[aski_idx] = cikis
                    askici_son = giris + aski_sure
                    tum_baralar.append({
                        'bara_no': bara_no,
                        'hat': hat,
                        'urun_kodu': s.get('urun_kodu', ''),
                        'urun_adi': s.get('urun_adi', ''),
                        'musteri': s.get('cari_unvan', ''),
                        'giris_dk': giris,
                        'cikis_dk': cikis,
                        'aski_idx': aski_idx + 1,
                    })

        # Vardiya grupla (giris_dk bazinda)
        from collections import OrderedDict
        v_grup = OrderedDict()
        for b in sorted(tum_baralar, key=lambda x: x['giris_dk']):
            vk = vardiya_bul(b['giris_dk'])
            v_grup.setdefault(vk, []).append(b)

        # Tablo doldur
        total_rows = sum(len(bl) + 1 for bl in v_grup.values())  # +1 header per vardiya
        self.timeline_table.setRowCount(total_rows)
        row = 0
        for vk, baralar in v_grup.items():
            # Vardiya header
            hdr = QTableWidgetItem(f"  ▼ VARDİYA {vk}  ({len(baralar)} bara)")
            hdr.setForeground(QColor(brand.PRIMARY))
            f = self._bold_font(); f.setPointSize(12); hdr.setFont(f)
            hdr.setBackground(QColor(45, 15, 20))
            self.timeline_table.setItem(row, 0, hdr)
            for c in range(1, 7):
                e = QTableWidgetItem(""); e.setBackground(QColor(45, 15, 20))
                self.timeline_table.setItem(row, c, e)
            self.timeline_table.setSpan(row, 0, 1, 7)
            self.timeline_table.setRowHeight(row, 32)
            row += 1

            for b in baralar:
                _, bg, fg = _kap_color(b['hat'])
                # 0 Bara no
                it = QTableWidgetItem(f"#{b['bara_no']}")
                it.setTextAlignment(Qt.AlignCenter)
                it.setForeground(QColor(brand.TEXT_DIM))
                self.timeline_table.setItem(row, 0, it)
                # 1 Hat pill
                _, _, short = _kap_color(b['hat'])
                it = QTableWidgetItem(short)
                it.setTextAlignment(Qt.AlignCenter)
                it.setForeground(QColor(fg))
                it.setFont(self._bold_font())
                self.timeline_table.setItem(row, 1, it)
                # 2 Giris saati
                gh, gm = divmod(b['giris_dk'] % 1440, 60)
                it = QTableWidgetItem(f"{gh:02d}:{gm:02d}")
                it.setTextAlignment(Qt.AlignCenter)
                it.setForeground(QColor(brand.SUCCESS))
                self.timeline_table.setItem(row, 2, it)
                # 3 Urun
                it = QTableWidgetItem(f"{b['urun_kodu']} · {b['urun_adi'][:40]}")
                self.timeline_table.setItem(row, 3, it)
                # 4 Musteri
                it = QTableWidgetItem(b['musteri'][:30])
                it.setForeground(QColor(brand.TEXT_DIM))
                self.timeline_table.setItem(row, 4, it)
                # 5 Cikis saati
                ch, cm = divmod(b['cikis_dk'] % 1440, 60)
                cikis_txt = f"{ch:02d}:{cm:02d}"
                if b['cikis_dk'] >= 1440:
                    cikis_txt += " (+1g)"
                it = QTableWidgetItem(cikis_txt)
                it.setTextAlignment(Qt.AlignCenter)
                it.setForeground(QColor(brand.WARNING))
                self.timeline_table.setItem(row, 5, it)
                # 6 Aski no
                it = QTableWidgetItem(f"A{b['aski_idx']}")
                it.setTextAlignment(Qt.AlignCenter)
                it.setForeground(QColor(brand.INFO))
                self.timeline_table.setItem(row, 6, it)
                self.timeline_table.setRowHeight(row, 28)
                row += 1

    def _fill_data_row(self, row: int, s: dict):
        """Tek bir veri satirini doldur. Satir indeksi satir_idx self._satirlar'daki."""
        satir_idx = self._satirlar.index(s)

        # 0 Müşteri
        self.table.setItem(row, 0, QTableWidgetItem(s.get('cari_unvan', '') or ''))

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
        self.table.setCellWidget(row, 1, hb)

        # 2 Kod, 3 Ad
        self.table.setItem(row, 2, QTableWidgetItem(s.get('urun_kodu', '')))
        ad = QTableWidgetItem(s.get('urun_adi', ''))
        ad.setForeground(QColor(brand.TEXT_DIM))
        self.table.setItem(row, 3, ad)

        # 4 İhtiyaç
        it = QTableWidgetItem(f"{s['ihtiyac_adet']:,}")
        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 4, it)

        # 5 Onayli stok
        stok = s.get('stok_adet', 0) or 0
        bekleyen = s.get('stok_bekleyen', 0) or 0
        ihtiyac = s.get('ihtiyac_adet', 0) or 0
        if stok >= ihtiyac and ihtiyac > 0:
            stok_clr = brand.SUCCESS
        elif stok > 0:
            stok_clr = brand.WARNING
        else:
            stok_clr = brand.ERROR
        it = QTableWidgetItem(f"{stok:,}" if stok > 0 else "0")
        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        it.setForeground(QColor(stok_clr))
        it.setFont(self._bold_font())
        it.setToolTip(
            f"GKK onaylı stok: {stok:,}\n"
            f"GKK bekleyen: {bekleyen:,}\n"
            f"Toplam eldeki: {stok + bekleyen:,}\n"
            f"İhtiyaç: {ihtiyac:,}"
        )
        self.table.setItem(row, 5, it)

        # 6 Bekleyen (GKK'da)
        bek_clr = brand.WARNING if bekleyen > 0 else brand.TEXT_DIM
        it = QTableWidgetItem(f"{bekleyen:,}" if bekleyen > 0 else "-")
        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        it.setForeground(QColor(bek_clr))
        if bekleyen > 0:
            it.setToolTip(f"GKK onayı bekleyen: {bekleyen:,}\nKalite > Giriş Kalite'den onaylayın")
        self.table.setItem(row, 6, it)

        # 7 Bara/Parça
        it = QTableWidgetItem(str(s['bara_parca']))
        it.setTextAlignment(Qt.AlignCenter)
        it.setForeground(QColor(brand.TEXT_DIM))
        self.table.setItem(row, 7, it)

        # 8 Yapılacak Bara
        it = QTableWidgetItem(str(s['yapilacak_bara']))
        it.setTextAlignment(Qt.AlignCenter)
        it.setForeground(QColor(brand.INFO))
        it.setFont(self._bold_font())
        self.table.setItem(row, 8, it)

        # 9 Reçete süre
        rs = s['recete_sure_dk']
        it = QTableWidgetItem(f"{rs} dk" if rs else "-")
        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if rs == 0:
            it.setForeground(QColor(brand.WARNING))
        self.table.setItem(row, 9, it)

        # 10 Toplam
        it = QTableWidgetItem(f"{s['toplam_dk']} dk")
        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        it.setForeground(QColor(brand.SUCCESS))
        it.setFont(self._bold_font())
        self.table.setItem(row, 10, it)

        # 11 Gerekli Kişi
        gp = s.get('gerekli_personel', 0) or 0
        it = QTableWidgetItem(f"{gp:.2f}")
        it.setTextAlignment(Qt.AlignCenter)
        it.setFont(self._bold_font())
        it.setForeground(QColor(brand.INFO))
        it.setToolTip(
            f"Toplam personel iş yükü: {s.get('toplam_personel_dk', 0)} dk\n"
            f"Bara × (asma+boşaltma) = {s['yapilacak_bara']} × "
            f"({s.get('aski_sure_dk', 0)}+{s.get('bosaltma_sure_dk', 0)})\n"
            f"Gerekli = iş/vardiya = {gp:.2f} kişi"
        )
        self.table.setItem(row, 11, it)

        # 12 Durum
        aski_yeter = s.get('aski_yeter', True)
        aski_kap = s.get('aski_kapasite', 0)
        aski_iht = s.get('aski_ihtiyaci', 0)
        if aski_yeter and aski_kap > 0:
            durum_txt = f"✓ OK ({aski_kap}/{aski_iht})"
            durum_clr = brand.SUCCESS
        elif aski_kap == 0 or s.get('stok_aski', 1) < s.get('aski_adedi', 1):
            durum_txt = "⚠ Askı yetmez"
            durum_clr = brand.ERROR
        else:
            durum_txt = f"⚠ {aski_kap}/{aski_iht} bara"
            durum_clr = brand.WARNING
        it = QTableWidgetItem(durum_txt)
        it.setTextAlignment(Qt.AlignCenter)
        it.setForeground(QColor(durum_clr))
        it.setFont(self._bold_font())
        it.setToolTip(
            f"Askı döngüsü: {s.get('aski_dongu_dk', 0)} dk\n"
            f"  (asma {s.get('aski_sure_dk', 0)} + reçete {s.get('recete_sure_dk', 0)} + boşaltma {s.get('bosaltma_sure_dk', 0)})\n"
            f"Vardiyada turn: {s.get('aski_turnover', 0)}\n"
            f"Stok askı: {s.get('stok_aski', 0)}\n"
            f"Hat bara stok: {s.get('hat_bara_stok', 0)}\n"
            f"Paralel bara: {s.get('paralel_bara', 0)} (= min(askı, hat bara))\n"
            f"Darboğaz: {s.get('darbogaz', '-')}\n"
            f"Vardiya kapasitesi (bara): {aski_kap}\n"
            f"İhtiyaç (bara): {aski_iht}"
        )
        self.table.setItem(row, 12, it)

        # 13 Saat (giriş → bitiş) + sonraki çevrim
        sg = s.get('sched_giris_dk')
        sb = s.get('sched_bitis_dk')
        _, vardiya_bitis_t, vardiya_total = self._vardiya_saatleri()
        vardiya_bitis_dk = vardiya_bitis_t.hour * 60 + vardiya_bitis_t.minute
        if sg is not None and sb is not None:
            gh, gm = divmod(sg % (24 * 60), 60)
            bh, bm = divmod(sb % (24 * 60), 60)
            saat_txt = f"{gh:02d}:{gm:02d} → {bh:02d}:{bm:02d}"
            it = QTableWidgetItem(saat_txt)
            it.setTextAlignment(Qt.AlignCenter)
            # Vardiya bitişini aşarsa kırmızı
            if sb > vardiya_bitis_dk:
                it.setForeground(QColor(brand.ERROR))
                saat_txt += " ⚠"
                it.setText(saat_txt)
            else:
                it.setForeground(QColor(brand.TEXT))
            it.setToolTip(
                f"İş süresi: {s.get('is_sure_dk', 0)} dk\n"
                f"Batch sayısı: {s.get('batch_count', 0)} (her batch {s.get('aski_dongu_dk', 0)} dk)\n"
                f"Askı sonraki çevrim: {s.get('sonraki_cevrim_dk', 0)} dk sonra\n"
                f"Vardiya bitişine: {(vardiya_bitis_dk - sg) if vardiya_bitis_dk > sg else 0} dk var"
            )
            self.table.setItem(row, 13, it)
        else:
            self.table.setItem(row, 13, QTableWidgetItem("-"))

        # 14 Vardiya combo
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
        vc.currentIndexChanged.connect(lambda _, idx=satir_idx, cb=vc: self._on_vardiya_change(idx, cb))
        self.table.setCellWidget(row, 14, vc)

        # 15 Kaynak
        it = QTableWidgetItem(s.get('kaynak', 'ANLASMA'))
        it.setForeground(QColor(brand.TEXT_DIM))
        self.table.setItem(row, 15, it)

        self.table.setRowHeight(row, 42)

    def _bold_font(self):
        from PySide6.QtGui import QFont
        f = QFont(); f.setBold(True); return f

    def _update_stats(self):
        talep = len(self._satirlar)
        toplam_bara = sum(s['yapilacak_bara'] for s in self._satirlar)
        ktl = sum(s['toplam_dk'] for s in self._satirlar if s.get('kap_kod', '').upper() in ('KTF', 'KATAFOREZ'))
        zn = sum(s['toplam_dk'] for s in self._satirlar if s.get('kap_kod', '').upper() in ('ZN', 'ZNNI', 'ASITZN'))
        diger = sum(s['toplam_dk'] for s in self._satirlar) - ktl - zn
        gerekli_toplam = sum(s.get('gerekli_personel', 0) or 0 for s in self._satirlar)
        mevcut = self.askici_spin.value() if hasattr(self, 'askici_spin') else 0
        self._set_stat(self.stat_talep, str(talep))
        self._set_stat(self.stat_bara, f"{toplam_bara:,}")
        self._set_stat(self.stat_ktl, f"{ktl:,} dk")
        self._set_stat(self.stat_zn, f"{zn:,} dk")
        self._set_stat(self.stat_diger, f"{diger:,} dk")
        # Personel karsilastirma rengi
        per_lbl = self.stat_personel.findChild(QLabel, "stat_value")
        if per_lbl:
            per_lbl.setText(f"{gerekli_toplam:.1f} / {mevcut}")
            if mevcut == 0:
                per_lbl.setStyleSheet(f"color: {brand.WARNING}; font-size: 18px; font-weight: 700;")
            elif gerekli_toplam <= mevcut:
                per_lbl.setStyleSheet(f"color: {brand.SUCCESS}; font-size: 18px; font-weight: 700;")
            else:
                per_lbl.setStyleSheet(f"color: {brand.ERROR}; font-size: 18px; font-weight: 700;")

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
