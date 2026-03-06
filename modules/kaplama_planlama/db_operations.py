# -*- coding: utf-8 -*-
"""
NEXOR ERP - Kaplama Planlama DB İşlemleri
"""
from datetime import date, datetime
from typing import List, Optional, Dict
from core.database import get_db_connection
from .models import KaplamaUrun, PlanGorev


def ensure_tables():
    """Gerekli tabloları oluştur (yoksa)"""
    sql = """
    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'kaplama')
        EXEC('CREATE SCHEMA kaplama')

    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'plan_haftalik' AND schema_id = SCHEMA_ID('kaplama'))
    BEGIN
        CREATE TABLE kaplama.plan_haftalik (
            id INT IDENTITY(1,1) PRIMARY KEY,
            hafta_baslangic DATE NOT NULL,
            olusturma_tarihi DATETIME DEFAULT GETDATE(),
            durum VARCHAR(20) DEFAULT 'taslak',
            olusturan VARCHAR(50),
            CONSTRAINT uq_hafta UNIQUE(hafta_baslangic)
        )
    END

    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'plan_urunler' AND schema_id = SCHEMA_ID('kaplama'))
    BEGIN
        CREATE TABLE kaplama.plan_urunler (
            id INT IDENTITY(1,1) PRIMARY KEY,
            plan_id INT NOT NULL REFERENCES kaplama.plan_haftalik(id),
            urun_ref VARCHAR(50),
            recete_no VARCHAR(20),
            tip VARCHAR(10),
            aski_tip VARCHAR(20),
            kapasite INT DEFAULT 1,
            cevrim_suresi INT DEFAULT 45,
            stok_aski INT DEFAULT 0,
            bara_aski INT DEFAULT 2,
            haftalik_ihtiyac INT DEFAULT 0,
            oncelik VARCHAR(10) DEFAULT 'normal'
        )
    END

    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'plan_gorevler' AND schema_id = SCHEMA_ID('kaplama'))
    BEGIN
        CREATE TABLE kaplama.plan_gorevler (
            id INT IDENTITY(1,1) PRIMARY KEY,
            plan_id INT NOT NULL REFERENCES kaplama.plan_haftalik(id),
            urun_id INT NOT NULL REFERENCES kaplama.plan_urunler(id),
            bara_no INT,
            gun INT,
            vardiya INT,
            aski_sayisi INT,
            acil BIT DEFAULT 0,
            baslangic_dk INT,
            sure_dk INT
        )
    END


    -- Mevcut tabloya bara_aski kolonu ekle (upgrade)
    IF EXISTS (SELECT * FROM sys.tables WHERE name = 'plan_urunler' AND schema_id = SCHEMA_ID('kaplama'))
       AND NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kaplama.plan_urunler') AND name = 'bara_aski')
    BEGIN
        ALTER TABLE kaplama.plan_urunler ADD bara_aski INT DEFAULT 2
    END

    -- PLC Recete tanimlari tablosu
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'plc_recete_tanimlari' AND schema_id = SCHEMA_ID('kaplama'))
    BEGIN
        CREATE TABLE kaplama.plc_recete_tanimlari (
            id INT IDENTITY(1,1) PRIMARY KEY,
            recete_no INT NOT NULL,
            recete_adi VARCHAR(100),
            recete_aciklama VARCHAR(200),
            hat_tipi VARCHAR(10),
            toplam_sure_dk INT,
            aktif BIT DEFAULT 1,
            guncelleme_tarihi DATETIME DEFAULT GETDATE(),
            CONSTRAINT uq_recete_no UNIQUE(recete_no)
        )
    END
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
        return True
    except Exception as e:
        print(f"[KaplamaPlanlama] Tablo oluşturma hatası: {e}")
        return False


def get_or_create_plan(hafta_baslangic: date) -> Optional[int]:
    """Hafta planını getir veya oluştur, plan_id döndür"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM kaplama.plan_haftalik WHERE hafta_baslangic = ?",
                (hafta_baslangic,)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
            cursor.execute(
                "INSERT INTO kaplama.plan_haftalik (hafta_baslangic, durum) VALUES (?, 'taslak'); SELECT SCOPE_IDENTITY()",
                (hafta_baslangic,)
            )
            cursor.nextset()
            row = cursor.fetchone()
            conn.commit()
            return int(row[0]) if row else None
    except Exception as e:
        print(f"[KaplamaPlanlama] Plan oluşturma hatası: {e}")
        return None


def save_urunler(plan_id: int, urunler: List[KaplamaUrun]):
    """Plan ürünlerini kaydet (önce mevcut sil, sonra yeniden yaz)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Önce görevleri sil (FK constraint)
            cursor.execute("DELETE FROM kaplama.plan_gorevler WHERE plan_id = ?", (plan_id,))
            cursor.execute("DELETE FROM kaplama.plan_urunler WHERE plan_id = ?", (plan_id,))
            for u in urunler:
                cursor.execute("""
                    INSERT INTO kaplama.plan_urunler
                    (plan_id, urun_ref, recete_no, tip, aski_tip, kapasite, cevrim_suresi, stok_aski, bara_aski, haftalik_ihtiyac, oncelik)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (plan_id, u.ref, u.recete_no, u.tip, u.aski_tip,
                      u.kapasite, u.cevrim_suresi, u.stok_aski, u.bara_aski, u.haftalik_ihtiyac, u.oncelik))
            conn.commit()
        return True
    except Exception as e:
        print(f"[KaplamaPlanlama] Ürün kaydetme hatası: {e}")
        return False


def save_gorevler(plan_id: int, urunler: List[KaplamaUrun], gorevler: List[PlanGorev]):
    """Plan görevlerini kaydet"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM kaplama.plan_gorevler WHERE plan_id = ?", (plan_id,))

            # Ürün ref → urun_id eşlemesi
            cursor.execute("SELECT id, urun_ref FROM kaplama.plan_urunler WHERE plan_id = ?", (plan_id,))
            ref_to_id = {row[1]: row[0] for row in cursor.fetchall()}

            for g in gorevler:
                urun_id = ref_to_id.get(g.urun_ref)
                if not urun_id:
                    continue
                cursor.execute("""
                    INSERT INTO kaplama.plan_gorevler
                    (plan_id, urun_id, bara_no, gun, vardiya, aski_sayisi, acil, baslangic_dk, sure_dk)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (plan_id, urun_id, g.bara_no, g.gun, g.vardiya,
                      g.aski_sayisi, 1 if g.acil else 0, g.baslangic_dk, g.sure_dk))
            conn.commit()
        return True
    except Exception as e:
        print(f"[KaplamaPlanlama] Görev kaydetme hatası: {e}")
        return False


def load_urunler(plan_id: int) -> List[KaplamaUrun]:
    """Plan ürünlerini yükle"""
    result = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, urun_ref, recete_no, tip, aski_tip, kapasite,
                       cevrim_suresi, stok_aski, ISNULL(bara_aski, 2) as bara_aski,
                       haftalik_ihtiyac, oncelik
                FROM kaplama.plan_urunler WHERE plan_id = ?
            """, (plan_id,))
            for row in cursor.fetchall():
                result.append(KaplamaUrun(
                    id=row[0], ref=row[1], recete_no=row[2], tip=row[3],
                    aski_tip=row[4], kapasite=row[5], cevrim_suresi=row[6],
                    stok_aski=row[7], bara_aski=row[8],
                    haftalik_ihtiyac=row[9], oncelik=row[10]
                ))
    except Exception as e:
        print(f"[KaplamaPlanlama] Ürün yükleme hatası: {e}")
    return result


def load_gorevler(plan_id: int) -> List[PlanGorev]:
    """Plan görevlerini yükle"""
    result = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT g.id, g.urun_id, g.bara_no, g.gun, g.vardiya,
                       g.aski_sayisi, g.acil, g.baslangic_dk, g.sure_dk,
                       u.urun_ref, u.tip
                FROM kaplama.plan_gorevler g
                JOIN kaplama.plan_urunler u ON g.urun_id = u.id
                WHERE g.plan_id = ?
            """, (plan_id,))
            for row in cursor.fetchall():
                result.append(PlanGorev(
                    id=row[0], urun_id=row[1], bara_no=row[2], gun=row[3],
                    vardiya=row[4], urun_ref=row[9], tip=row[10],
                    aski_sayisi=row[5], acil=bool(row[6]),
                    baslangic_dk=row[7], sure_dk=row[8]
                ))
    except Exception as e:
        print(f"[KaplamaPlanlama] Görev yükleme hatası: {e}")
    return result


def search_stok_kartlari(arama: str) -> List[Dict]:
    """Stok kartlarından ürün ara - askı/bara bilgileriyle birlikte"""
    result = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 30
                    u.id, u.urun_kodu, u.urun_adi,
                    u.aski_adedi, u.bara_adedi, u.recete_no,
                    kt.kod as kaplama_kodu, kt.ad as kaplama_adi,
                    at.kod as aski_tip_kodu, at.ad as aski_tip_adi,
                    u.kaplama_turu_id, u.aski_tipi_id
                FROM stok.urunler u
                LEFT JOIN tanim.kaplama_turleri kt ON u.kaplama_turu_id = kt.id
                LEFT JOIN tanim.aski_tipleri at ON u.aski_tipi_id = at.id
                WHERE u.aktif_mi = 1
                  AND (u.urun_kodu LIKE ? OR u.urun_adi LIKE ? OR u.musteri_parca_no LIKE ?)
                ORDER BY u.urun_kodu
            """, (f"%{arama}%", f"%{arama}%", f"%{arama}%"))
            for row in cursor.fetchall():
                result.append({
                    'id': row[0],
                    'urun_kodu': row[1],
                    'urun_adi': row[2],
                    'aski_adedi': row[3] or 0,
                    'bara_adedi': row[4] or 0,
                    'recete_no': row[5] or '',
                    'kaplama_kodu': row[6] or '',
                    'kaplama_adi': row[7] or '',
                    'aski_tip_kodu': row[8] or '',
                    'aski_tip_adi': row[9] or '',
                })
    except Exception as e:
        print(f"[KaplamaPlanlama] Stok kartı arama hatası: {e}")
    return result


def get_hat_doluluk() -> Dict:
    """PLC cache'den hat/banyo doluluk durumunu getir"""
    result = {
        'aktif_kazanlar': [],      # Aktif durumdaki kazanlar
        'toplam_aktif': 0,
        'ktl_aktif': 0,            # KTL hattı (101-143)
        'cinko_aktif': 0,          # Çinko hattı (201-242)
        'bos_baralar': [],         # Boş (BEKLIYOR/DURDU) baralar
    }
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kazan_no, son_bara, durum, durum_dakika
                FROM uretim.plc_cache
                ORDER BY kazan_no
            """)
            for row in cursor.fetchall():
                kazan_no = row[0]
                durum = row[2] or ''
                if durum == 'AKTIF':
                    result['aktif_kazanlar'].append({
                        'kazan_no': kazan_no,
                        'son_bara': row[1],
                        'durum_dakika': row[3] or 0
                    })
                    result['toplam_aktif'] += 1
                    if 101 <= kazan_no <= 143:
                        result['ktl_aktif'] += 1
                    elif 201 <= kazan_no <= 242:
                        result['cinko_aktif'] += 1

            # Planlama tablosundan mevcut planlanmış iş emirlerini de al
            cursor.execute("""
                SELECT COUNT(*) as plan_count
                FROM siparis.is_emirleri
                WHERE durum IN ('planlandi', 'uretimde') AND silindi_mi = 0
            """)
            row = cursor.fetchone()
            result['planli_is_emri'] = row[0] if row else 0

    except Exception as e:
        print(f"[KaplamaPlanlama] Hat doluluk sorgulama hatası: {e}")
    return result


def get_plan_durum(plan_id: int) -> str:
    """Plan durumunu getir"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT durum FROM kaplama.plan_haftalik WHERE id = ?", (plan_id,))
            row = cursor.fetchone()
            return row[0] if row else "taslak"
    except Exception:
        return "taslak"


def get_plc_canli() -> List[Dict]:
    """PLC cache'den tum kazanlarin canli verisini getir"""
    result = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    pc.kazan_no, pc.hat_kodu, pc.pozisyon_adi,
                    pc.ort_sicaklik, pc.ort_akim, pc.son_bara,
                    pc.recete_no, pc.durum, pc.durum_dakika,
                    pc.islem_sayisi_24s, pc.toplam_miktar_24s,
                    pc.gunluk_bara_adet,
                    COALESCE(pc.pozisyon_adi, 'Kazan ' + CAST(pc.kazan_no AS VARCHAR)) as banyo_adi,
                    bt.sicaklik_min, bt.sicaklik_max, bt.sicaklik_hedef,
                    rt.recete_adi, rt.recete_aciklama, rt.hat_tipi, rt.toplam_sure_dk
                FROM uretim.plc_cache pc
                LEFT JOIN uretim.banyo_tanimlari bt ON pc.pozisyon_adi = bt.ad
                LEFT JOIN kaplama.plc_recete_tanimlari rt ON rt.recete_no = pc.recete_no
                ORDER BY pc.kazan_no
            """)
            for row in cursor.fetchall():
                result.append({
                    'kazan_no': row[0],
                    'hat_kodu': row[1] or '',
                    'pozisyon': row[2] or '',
                    'sicaklik': float(row[3]) if row[3] else 0,
                    'akim': float(row[4]) if row[4] else 0,
                    'son_bara': row[5],
                    'recete_no': row[6],
                    'durum': row[7] or 'BELIRSIZ',
                    'durum_dakika': row[8] or 0,
                    'islem_24s': row[9] or 0,
                    'miktar_24s': float(row[10]) if row[10] else 0,
                    'bara_gun': row[11] or 0,
                    'banyo_adi': row[12] or f'Kazan {row[0]}',
                    'sicaklik_min': float(row[13]) if row[13] else 0,
                    'sicaklik_max': float(row[14]) if row[14] else 100,
                    'sicaklik_hedef': float(row[15]) if row[15] else 0,
                    'recete_adi': row[16] or '',
                    'recete_aciklama': row[17] or '',
                    'recete_hat_tipi': row[18] or '',
                    'recete_sure_dk': row[19],
                })
    except Exception as e:
        print(f"[KaplamaPlanlama] PLC canli veri hatasi: {e}")
    return result


def get_banyo_detay() -> List[Dict]:
    """Banyo tanimlarindan detayli bilgi al"""
    result = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    b.id, b.kod, b.ad, b.hacim_lt,
                    b.sicaklik_min, b.sicaklik_max, b.sicaklik_hedef,
                    b.ph_min, b.ph_max, b.ph_hedef,
                    bt.kod as tip_kodu, bt.ad as tip_adi,
                    h.kod as hat_kodu, h.ad as hat_adi,
                    b.aktif_mi
                FROM uretim.banyo_tanimlari b
                LEFT JOIN tanim.banyo_tipleri bt ON b.banyo_tipi_id = bt.id
                LEFT JOIN tanim.uretim_hatlari h ON b.hat_id = h.id
                WHERE b.aktif_mi = 1
                ORDER BY h.kod, b.kod
            """)
            for row in cursor.fetchall():
                result.append({
                    'id': row[0], 'kod': row[1], 'ad': row[2],
                    'hacim_lt': float(row[3]) if row[3] else 0,
                    'sicaklik_min': float(row[4]) if row[4] else 0,
                    'sicaklik_max': float(row[5]) if row[5] else 100,
                    'sicaklik_hedef': float(row[6]) if row[6] else 0,
                    'ph_min': float(row[7]) if row[7] else 0,
                    'ph_max': float(row[8]) if row[8] else 14,
                    'ph_hedef': float(row[9]) if row[9] else 7,
                    'tip_kodu': row[10] or '', 'tip_adi': row[11] or '',
                    'hat_kodu': row[12] or '', 'hat_adi': row[13] or '',
                })
    except Exception as e:
        print(f"[KaplamaPlanlama] Banyo detay hatasi: {e}")
    return result


def get_urun_recete(urun_kodu: str) -> List[Dict]:
    """Urun recete adimlarini getir - sureler dahil"""
    result = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    r.sira_no, r.islem_adi, r.sure_sn,
                    r.sicaklik_min, r.sicaklik_max, r.sicaklik_hedef,
                    r.akim_min, r.akim_max, r.akim_hedef,
                    bt.kod as banyo_tipi_kodu, bt.ad as banyo_tipi_adi,
                    r.kontrol_noktasi_mi
                FROM stok.urun_recete r
                LEFT JOIN tanim.banyo_tipleri bt ON r.banyo_tipi_id = bt.id
                JOIN stok.urunler u ON r.urun_id = u.id
                WHERE u.urun_kodu = ? AND r.aktif_mi = 1
                ORDER BY r.sira_no
            """, (urun_kodu,))
            for row in cursor.fetchall():
                result.append({
                    'sira': row[0],
                    'islem': row[1] or f'Adim {row[0]}',
                    'sure_sn': row[2] or 0,
                    'sicaklik_min': float(row[3]) if row[3] else None,
                    'sicaklik_max': float(row[4]) if row[4] else None,
                    'sicaklik_hedef': float(row[5]) if row[5] else None,
                    'akim_min': float(row[6]) if row[6] else None,
                    'akim_max': float(row[7]) if row[7] else None,
                    'akim_hedef': float(row[8]) if row[8] else None,
                    'banyo_tipi': row[9] or '',
                    'banyo_tipi_adi': row[10] or '',
                    'kontrol': bool(row[11]),
                })
            # Toplam cevrim suresi hesapla
            if result:
                toplam_sn = sum(a['sure_sn'] for a in result)
                for a in result:
                    a['toplam_cevrim_sn'] = toplam_sn
    except Exception as e:
        print(f"[KaplamaPlanlama] Recete sorgulama hatasi: {e}")
    return result


def get_hat_istatistik() -> Dict:
    """Hat bazli istatistikler (KTL, ZNNI)"""
    result = {
        'KTL': {'aktif': 0, 'bekliyor': 0, 'durdu': 0, 'ort_sicaklik': 0, 'toplam_miktar': 0, 'bara_adet': 0},
        'ZNNI': {'aktif': 0, 'bekliyor': 0, 'durdu': 0, 'ort_sicaklik': 0, 'toplam_miktar': 0, 'bara_adet': 0},
        'DIGER': {'aktif': 0, 'bekliyor': 0, 'durdu': 0, 'ort_sicaklik': 0, 'toplam_miktar': 0, 'bara_adet': 0},
    }
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hat_kodu,
                    SUM(CASE WHEN durum = 'AKTIF' THEN 1 ELSE 0 END) as aktif,
                    SUM(CASE WHEN durum = 'BEKLIYOR' THEN 1 ELSE 0 END) as bekliyor,
                    SUM(CASE WHEN durum = 'DURDU' THEN 1 ELSE 0 END) as durdu,
                    AVG(CASE WHEN ort_sicaklik > 0 THEN ort_sicaklik END) as ort_sicaklik,
                    SUM(ISNULL(toplam_miktar_24s, 0)) as toplam_miktar,
                    SUM(ISNULL(gunluk_bara_adet, 0)) as bara_adet
                FROM uretim.plc_cache
                GROUP BY hat_kodu
            """)
            for row in cursor.fetchall():
                hat = row[0] or 'DIGER'
                if hat in result:
                    result[hat] = {
                        'aktif': row[1] or 0,
                        'bekliyor': row[2] or 0,
                        'durdu': row[3] or 0,
                        'ort_sicaklik': float(row[4]) if row[4] else 0,
                        'toplam_miktar': float(row[5]) if row[5] else 0,
                        'bara_adet': row[6] or 0,
                    }
    except Exception as e:
        print(f"[KaplamaPlanlama] Hat istatistik hatasi: {e}")
    return result


def fix_hat_kodlari():
    """PLC cache'deki hat_kodu alanini kazan numarasina gore otomatik doldur/duzelt"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Tum kayitlari kazan_no'ya gore guncelle
            cursor.execute("""
                UPDATE uretim.plc_cache SET hat_kodu =
                    CASE
                        WHEN kazan_no BETWEEN 1 AND 23 THEN 'ON'
                        WHEN kazan_no BETWEEN 101 AND 143 THEN 'KTL'
                        WHEN kazan_no BETWEEN 201 AND 247 THEN 'ZNNI'
                        ELSE 'DIGER'
                    END
            """)
            updated = cursor.rowcount
            conn.commit()
            print(f"[KaplamaPlanlama] hat_kodu duzeltildi: {updated} kazan")
            return updated
    except Exception as e:
        print(f"[KaplamaPlanlama] hat_kodu duzeltme hatasi: {e}")
        return 0


def seed_recete_tanimlari():
    """SCADA'dan okunan recete tanimlarini DB'ye yaz (ilk kurulum)"""
    RECETELER = [
        # (recete_no, recete_adi, recete_aciklama, hat_tipi)
        # KTL (Kataforez) - 1-19, 30-31
        (1, "KATAFOREZ", "PEDAL-286", "KTL"),
        (2, "KATAFOREZ", "9306-YAY", "KTL"),
        (3, "KATAFOREZ", "ERMETAL", "KTL"),
        (4, "KATAFOREZ", "PROFILSAN", "KTL"),
        (5, "KATAFOREZ", "AKP(1", "KTL"),
        (6, "KATAFOREZ", "ORAU (BC3)", "KTL"),
        (7, "KATAFOREZ", "ORAU (19K)", "KTL"),
        (8, "KATAFOREZ", "ERPEN", "KTL"),
        (9, "KATAFOREZ", "PERNAT", "KTL"),
        (10, "KATAFOREZ", "VALFSAN", "KTL"),
        (11, "KATAFOREZ", "PRS TELESKOP", "KTL"),
        (12, "KATAFOREZ", "LFF CEKIDEMIRI", "KTL"),
        (13, "KATAFOREZ", "EC5", "KTL"),
        (14, "KATAFOREZ", "GRAMMER", "KTL"),
        (15, "KATAFOREZ", "ERMETAL KARTEL KORUMA", "KTL"),
        (16, "KATAFOREZ", "PRS TOZBOYA", "KTL"),
        (17, "KATAFOREZ", "ERMETAL 302", "KTL"),
        (18, "KATAFOREZ", "PRS FOSFAT", "KTL"),
        (19, "KATAFOREZ", "AKDENIZ YAY", "KTL"),
        (30, "KATAFOREZ", "TEKNIK", "KTL"),
        (31, "KATAFOREZ", "TEKNIK SOKME", "KTL"),
        # ZNNI (Cinko-Nikel) - 53-66
        (53, "ORAU NIKEL", "1003-F", "ZNNI"),
        (54, "ORAU NIKEL", "1003-F", "ZNNI"),
        (55, "ORAU NIKEL", "1003-F SOKME", "ZNNI"),
        (56, "ORAU NIKEL", "1003-F", "ZNNI"),
        (57, "ORAU NIKEL", "ERMETAL", "ZNNI"),
        (58, "ORAU NIKEL", "ERMETAL", "ZNNI"),
        (59, "ORAU NIKEL", "16K-22K", "ZNNI"),
        (60, "ORAU NIKEL", "16K-22K", "ZNNI"),
        (61, "NIKEL", "SUMIRIKO UZUN BORU SOKME", "ZNNI"),
        (62, "ORAU NIKEL", "SUMIRIKO UZUN BORU", "ZNNI"),
        (63, "ORAU NIKEL", "SUMIRIKO CIFT ASKI", "ZNNI"),
        (64, "NIKEL", "ORAU", "ZNNI"),
        (65, "SUMIRIKO", "SUMIRIKO", "ZNNI"),
        (66, "NIKEL", "ORAU", "ZNNI"),
        # ON (On Islem / Alkali) - 70-74
        (70, "ORAU ALKALI", "19K BORU", "ON"),
        (71, "19K BORU", "19K SOKME BORU", "ON"),
        (72, "ORAU ALKALI", "19K YENI ASKI", "ON"),
        (73, "ORAU ALKALI", "TANBUR", "ON"),
        (74, "ORAU ALKALI", "TANBUR", "ON"),
        # Kaplama Genel - 75-80
        (75, "KAPLANLAR", "ACIKLAMA", "ZNNI"),
        (76, "KAPLANLAR", "ACIKLAMA", "ZNNI"),
        (77, "KAPLANLAR", "CERCEVE", "ZNNI"),
        (78, "ORAU", "STEPNE CERCEVE", "ZNNI"),
        (80, "KAPLANLAR", "CERCEVE", "ZNNI"),
    ]
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            inserted = 0
            for recete_no, adi, aciklama, hat_tipi in RECETELER:
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM kaplama.plc_recete_tanimlari WHERE recete_no = ?)
                        INSERT INTO kaplama.plc_recete_tanimlari (recete_no, recete_adi, recete_aciklama, hat_tipi)
                        VALUES (?, ?, ?, ?)
                    ELSE
                        UPDATE kaplama.plc_recete_tanimlari
                        SET recete_adi = ?, recete_aciklama = ?, hat_tipi = ?, guncelleme_tarihi = GETDATE()
                        WHERE recete_no = ?
                """, (recete_no, recete_no, adi, aciklama, hat_tipi, adi, aciklama, hat_tipi, recete_no))
                inserted += 1
            conn.commit()
            print(f"[KaplamaPlanlama] {inserted} recete tanimi yazildi")
            return inserted
    except Exception as e:
        print(f"[KaplamaPlanlama] Recete seed hatasi: {e}")
        return 0


def get_recete_tanimlari(hat_tipi: str = None) -> List[Dict]:
    """Recete tanimlarini getir. hat_tipi filtresi opsiyonel."""
    result = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT recete_no, recete_adi, recete_aciklama, hat_tipi, toplam_sure_dk, aktif FROM kaplama.plc_recete_tanimlari"
            params = []
            if hat_tipi:
                sql += " WHERE hat_tipi = ?"
                params.append(hat_tipi)
            sql += " ORDER BY recete_no"
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                result.append({
                    'recete_no': row[0],
                    'recete_adi': row[1],
                    'recete_aciklama': row[2],
                    'hat_tipi': row[3],
                    'toplam_sure_dk': row[4],
                    'aktif': row[5],
                })
    except Exception as e:
        print(f"[KaplamaPlanlama] Recete tanimlari hatasi: {e}")
    return result


def get_recete_by_no(recete_no: int) -> Optional[Dict]:
    """Tek bir recete tanimini getir"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT recete_no, recete_adi, recete_aciklama, hat_tipi, toplam_sure_dk, aktif
                FROM kaplama.plc_recete_tanimlari WHERE recete_no = ?
            """, (recete_no,))
            row = cursor.fetchone()
            if row:
                return {
                    'recete_no': row[0],
                    'recete_adi': row[1],
                    'recete_aciklama': row[2],
                    'hat_tipi': row[3],
                    'toplam_sure_dk': row[4],
                    'aktif': row[5],
                }
    except Exception as e:
        print(f"[KaplamaPlanlama] Recete getirme hatasi: {e}")
    return None


def sync_recete_sureleri():
    """plc_tarihce'den adim surelerini toplayarak recete cevrim surelerini hesapla"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Her recete icin adim bazli sureleri cek (adim 0 = bekleme, atla)
            # Her adimda en cok kullanilan kazanin suresini al
            cursor.execute("""
                SELECT recete_no, recete_adim,
                       MAX(recete_zamani) as adim_suresi_sn
                FROM (
                    SELECT recete_no, recete_adim, kazan_no, recete_zamani,
                           ROW_NUMBER() OVER (
                               PARTITION BY recete_no, recete_adim
                               ORDER BY COUNT(*) DESC
                           ) as rn
                    FROM uretim.plc_tarihce
                    WHERE tarih_doldurma >= DATEADD(DAY, -30, GETDATE())
                      AND recete_no IS NOT NULL AND recete_adim IS NOT NULL
                      AND recete_adim > 0 AND recete_zamani > 0
                    GROUP BY recete_no, recete_adim, kazan_no, recete_zamani
                ) x WHERE rn = 1
                GROUP BY recete_no, recete_adim
                ORDER BY recete_no, recete_adim
            """)
            rows = cursor.fetchall()

            # Recete bazli toplam hesapla
            from collections import defaultdict
            recete_sureler = defaultdict(int)
            for rec_no, adim, sure_sn in rows:
                recete_sureler[rec_no] += (sure_sn or 0)

            updated = 0
            for recete_no, toplam_sn in recete_sureler.items():
                if toplam_sn > 0:
                    sure_dk = max(1, round(toplam_sn / 60))
                    cursor.execute("""
                        UPDATE kaplama.plc_recete_tanimlari
                        SET toplam_sure_dk = ?, guncelleme_tarihi = GETDATE()
                        WHERE recete_no = ?
                    """, (sure_dk, recete_no))
                    if cursor.rowcount > 0:
                        updated += 1
            conn.commit()
            print(f"[KaplamaPlanlama] {updated} recete suresi guncellendi (adim toplami)")
            return updated
    except Exception as e:
        print(f"[KaplamaPlanlama] Recete sure sync hatasi: {e}")
        return 0


def get_recete_adimlari(recete_no: int) -> List[Dict]:
    """Bir recetenin adim adim kazan ve sure detayini getir (PLC tarihcesinden)"""
    result = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.recete_adim, t.kazan_no,
                       AVG(CASE WHEN t.recete_zamani > 0 THEN t.recete_zamani END) as ort_sure_sn,
                       AVG(DATEDIFF(SECOND, t.tarih_doldurma, t.tarih_bosaltma)) as ort_cevrim_sn,
                       COUNT(*) as kayit,
                       AVG(t.sicaklik) as ort_sicaklik,
                       AVG(t.akim) as ort_akim,
                       MAX(pc.pozisyon_adi) as pozisyon_adi
                FROM uretim.plc_tarihce t
                LEFT JOIN uretim.plc_cache pc ON pc.kazan_no = t.kazan_no
                WHERE t.recete_no = ? AND t.recete_adim IS NOT NULL AND t.recete_adim > 0
                  AND t.tarih_doldurma >= DATEADD(DAY, -30, GETDATE())
                GROUP BY t.recete_adim, t.kazan_no
                HAVING COUNT(*) >= 2
                ORDER BY t.recete_adim, COUNT(*) DESC
            """, (recete_no,))
            for row in cursor.fetchall():
                result.append({
                    'adim': row[0],
                    'kazan_no': row[1],
                    'sure_sn': float(row[2]) if row[2] else (float(row[3]) if row[3] else 0),
                    'kayit': row[4],
                    'sicaklik': float(row[5]) if row[5] else 0,
                    'akim': float(row[6]) if row[6] else 0,
                    'pozisyon_adi': row[7] or f'Kazan {row[1]}',
                })
    except Exception as e:
        print(f"[KaplamaPlanlama] Recete adimlari hatasi: {e}")
    return result


def get_ortak_kazanlar() -> List[Dict]:
    """Birden fazla recetede kullanilan ortak kazanlari getir"""
    result = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kazan_no, COUNT(DISTINCT recete_no) as recete_sayisi
                FROM (
                    SELECT DISTINCT kazan_no, recete_no
                    FROM uretim.plc_tarihce
                    WHERE tarih_doldurma >= DATEADD(DAY, -7, GETDATE())
                      AND recete_no IS NOT NULL AND kazan_no IS NOT NULL
                ) sub
                GROUP BY kazan_no
                HAVING COUNT(DISTINCT recete_no) > 1
                ORDER BY COUNT(DISTINCT recete_no) DESC
            """)
            kazan_rows = cursor.fetchall()

            for kzn_row in kazan_rows:
                kazan_no = kzn_row[0]
                recete_sayisi = kzn_row[1]

                # Bu kazanin recetelerini cek
                cursor.execute("""
                    SELECT DISTINCT t.recete_no, rt.recete_adi, rt.recete_aciklama
                    FROM uretim.plc_tarihce t
                    LEFT JOIN kaplama.plc_recete_tanimlari rt ON rt.recete_no = t.recete_no
                    WHERE t.kazan_no = ? AND t.recete_no IS NOT NULL
                      AND t.tarih_doldurma >= DATEADD(DAY, -7, GETDATE())
                    ORDER BY t.recete_no
                """, (kazan_no,))
                receteler = []
                for r in cursor.fetchall():
                    receteler.append({
                        'recete_no': r[0],
                        'recete_adi': r[1] or '',
                        'recete_aciklama': r[2] or '',
                    })

                # Pozisyon adi
                cursor.execute("SELECT pozisyon_adi FROM uretim.plc_cache WHERE kazan_no = ?", (kazan_no,))
                poz = cursor.fetchone()

                result.append({
                    'kazan_no': kazan_no,
                    'pozisyon_adi': (poz[0] if poz and poz[0] else None) or f'Kazan {kazan_no}',
                    'recete_sayisi': recete_sayisi,
                    'receteler': receteler,
                })
    except Exception as e:
        print(f"[KaplamaPlanlama] Ortak kazan hatasi: {e}")
    return result


def update_recete_sure(recete_no: int, toplam_sure_dk: int):
    """Recete toplam suresini guncelle"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE kaplama.plc_recete_tanimlari
                SET toplam_sure_dk = ?, guncelleme_tarihi = GETDATE()
                WHERE recete_no = ?
            """, (toplam_sure_dk, recete_no))
            conn.commit()
    except Exception as e:
        print(f"[KaplamaPlanlama] Recete sure guncelleme hatasi: {e}")


def update_plan_durum(plan_id: int, durum: str):
    """Plan durumunu güncelle"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE kaplama.plan_haftalik SET durum = ? WHERE id = ?",
                (durum, plan_id)
            )
            conn.commit()
    except Exception as e:
        print(f"[KaplamaPlanlama] Durum güncelleme hatası: {e}")
