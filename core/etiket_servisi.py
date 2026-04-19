# -*- coding: utf-8 -*-
"""
NEXOR ERP - Merkezi Etiket Basim Servisi
=========================================
Tek API: EtiketServisi.bas(kullanim_yeri, etiket_data)

Mimari:
- sistem.etiket_sablon_atamalari (GLOBAL): kullanim_yeri -> sablon + kopya + otomatik_bas
- sistem.pc_yazici_atamalari (PC-BAZLI): bilgisayar_adi + kullanim_yeri -> yazici + format

Akis:
1) Kullanim_yeri'ne gore sablon atamasini oku
2) Bilgisayar adina gore yazici atamasini oku
3) otomatik_bas=1 + yazici tanimli ise -> direkt bas (dialog yok)
4) Aksi halde eski dialog'a fallback (kullanici sececek)

Universal: Her firmada Sistem > Firma Ayarlari > Etiket sekmelerinden konfigure edilir.
"""
import os
from typing import Optional

from core.database import get_db_connection


# ============================================================================
# SABITLER
# ============================================================================

KULLANIM_YERLERI = {
    'kalite_final':    'Kalite Final Kontrol',
    'kalite_giris':    'Kalite Giris Kontrol',
    'depo_giris':      'Depo Giris Etiketi',
    'depo_cikis':      'Depo Cikis Etiketi',
    'sevkiyat':        'Sevkiyat Etiketi',
    'stok_kimyasal':   'Kimyasal Stok Etiketi',
    'satinalma_talep': 'Satinalma Talep Etiketi',
    'uretim_giris':    'Uretim Giris Etiketi',
    'uretim_cikis':    'Uretim Cikis Etiketi',
}

FORMAT_TIPLERI = ['EZPL', 'ZPL', 'PDF']
DEFAULT_FORMAT = 'EZPL'


# ============================================================================
# TABLO OLUSTURMA (LAZY)
# ============================================================================

_TABLES_ENSURED = False


def ensure_tables() -> bool:
    """Etiket sistem tablolarini olustur (yoksa). Tek seferlik calisir."""
    global _TABLES_ENSURED
    if _TABLES_ENSURED:
        return True

    sql = """
    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'sistem')
        EXEC('CREATE SCHEMA sistem')

    IF NOT EXISTS (SELECT * FROM sys.tables
                   WHERE name = 'etiket_sablon_atamalari'
                     AND schema_id = SCHEMA_ID('sistem'))
    BEGIN
        CREATE TABLE sistem.etiket_sablon_atamalari (
            id INT IDENTITY(1,1) PRIMARY KEY,
            kullanim_yeri NVARCHAR(50) NOT NULL,
            sablon_id INT NULL,
            kopya_adedi INT NOT NULL DEFAULT 1,
            otomatik_bas BIT NOT NULL DEFAULT 1,
            aciklama NVARCHAR(200),
            olusturma_tarihi DATETIME DEFAULT GETDATE(),
            guncelleme_tarihi DATETIME DEFAULT GETDATE(),
            CONSTRAINT uq_sablon_kullanim UNIQUE(kullanim_yeri)
        )
    END

    IF NOT EXISTS (SELECT * FROM sys.tables
                   WHERE name = 'pc_yazici_atamalari'
                     AND schema_id = SCHEMA_ID('sistem'))
    BEGIN
        CREATE TABLE sistem.pc_yazici_atamalari (
            id INT IDENTITY(1,1) PRIMARY KEY,
            bilgisayar_adi NVARCHAR(100) NOT NULL,
            pc_aciklama NVARCHAR(200),
            kullanim_yeri NVARCHAR(50) NOT NULL,
            yazici_adi NVARCHAR(200) NOT NULL,
            format_tipi NVARCHAR(10) NOT NULL DEFAULT 'EZPL',
            olusturma_tarihi DATETIME DEFAULT GETDATE(),
            guncelleme_tarihi DATETIME DEFAULT GETDATE(),
            CONSTRAINT uq_pc_kullanim UNIQUE(bilgisayar_adi, kullanim_yeri)
        )
    END
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
        _TABLES_ENSURED = True
        return True
    except Exception as e:
        print(f"[EtiketServisi] Tablo olusturma hatasi: {e}")
        return False


# ============================================================================
# YARDIMCI FONKSIYONLAR
# ============================================================================

def get_pc_adi() -> str:
    """Gecerli bilgisayarin adini al (Windows COMPUTERNAME)"""
    return os.environ.get('COMPUTERNAME', 'BILINMEYEN')


# ============================================================================
# ATAMA OKUMA
# ============================================================================

def get_sablon_atama(kullanim_yeri: str) -> Optional[dict]:
    """Kullanim yeri icin sablon atamasini oku"""
    ensure_tables()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.kullanim_yeri, s.sablon_id, s.kopya_adedi, s.otomatik_bas,
                       s.aciklama, t.sablon_kodu, t.sablon_adi
                FROM sistem.etiket_sablon_atamalari s
                LEFT JOIN tanim.etiket_sablonlari t ON t.id = s.sablon_id
                WHERE s.kullanim_yeri = ?
            """, kullanim_yeri)
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'kullanim_yeri': row[0],
                'sablon_id': row[1],
                'kopya_adedi': row[2] or 1,
                'otomatik_bas': bool(row[3]),
                'aciklama': row[4] or '',
                'sablon_kodu': row[5],
                'sablon_adi': row[6],
            }
    except Exception as e:
        print(f"[EtiketServisi] Sablon atama okuma hatasi: {e}")
        return None


def get_yazici_atama(kullanim_yeri: str, bilgisayar_adi: str = None) -> Optional[dict]:
    """PC + kullanim yerine gore yazici atamasini oku"""
    ensure_tables()
    bilgisayar_adi = bilgisayar_adi or get_pc_adi()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT bilgisayar_adi, pc_aciklama, kullanim_yeri, yazici_adi, format_tipi
                FROM sistem.pc_yazici_atamalari
                WHERE bilgisayar_adi = ? AND kullanim_yeri = ?
            """, bilgisayar_adi, kullanim_yeri)
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'bilgisayar_adi': row[0],
                'pc_aciklama': row[1] or '',
                'kullanim_yeri': row[2],
                'yazici_adi': row[3],
                'format_tipi': (row[4] or DEFAULT_FORMAT).upper(),
            }
    except Exception as e:
        print(f"[EtiketServisi] Yazici atama okuma hatasi: {e}")
        return None


# ============================================================================
# UI ICIN LISTELEME
# ============================================================================

def list_sablon_atamalari() -> list:
    """Tum sablon atamalarini listele (Firma Ayarlari sekmesinde gosterim icin)"""
    ensure_tables()
    rows = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, s.kullanim_yeri, s.sablon_id, s.kopya_adedi,
                       s.otomatik_bas, s.aciklama, t.sablon_adi
                FROM sistem.etiket_sablon_atamalari s
                LEFT JOIN tanim.etiket_sablonlari t ON t.id = s.sablon_id
                ORDER BY s.kullanim_yeri
            """)
            for r in cursor.fetchall():
                rows.append({
                    'id':             r[0],
                    'kullanim_yeri':  r[1],
                    'sablon_id':      r[2],
                    'kopya_adedi':    r[3] or 1,
                    'otomatik_bas':   bool(r[4]),
                    'aciklama':       r[5] or '',
                    'sablon_adi':     r[6] or '(Sablon secilmemis)',
                })
    except Exception as e:
        print(f"[EtiketServisi] Sablon listele hatasi: {e}")
    return rows


def list_pc_yazici_atamalari(bilgisayar_adi: str = None) -> list:
    """PC yazici atamalarini listele (filtreli veya tum)"""
    ensure_tables()
    rows = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if bilgisayar_adi:
                cursor.execute("""
                    SELECT id, bilgisayar_adi, pc_aciklama, kullanim_yeri,
                           yazici_adi, format_tipi
                    FROM sistem.pc_yazici_atamalari
                    WHERE bilgisayar_adi = ?
                    ORDER BY kullanim_yeri
                """, bilgisayar_adi)
            else:
                cursor.execute("""
                    SELECT id, bilgisayar_adi, pc_aciklama, kullanim_yeri,
                           yazici_adi, format_tipi
                    FROM sistem.pc_yazici_atamalari
                    ORDER BY bilgisayar_adi, kullanim_yeri
                """)
            for r in cursor.fetchall():
                rows.append({
                    'id':             r[0],
                    'bilgisayar_adi': r[1],
                    'pc_aciklama':    r[2] or '',
                    'kullanim_yeri':  r[3],
                    'yazici_adi':     r[4],
                    'format_tipi':    (r[5] or DEFAULT_FORMAT).upper(),
                })
    except Exception as e:
        print(f"[EtiketServisi] PC yazici listele hatasi: {e}")
    return rows


def list_distinct_pcler() -> list:
    """Daha once kayit edilmis tum PC adlarini listele (combo icin)"""
    ensure_tables()
    rows = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT bilgisayar_adi, MAX(pc_aciklama) AS aciklama
                FROM sistem.pc_yazici_atamalari
                GROUP BY bilgisayar_adi
                ORDER BY bilgisayar_adi
            """)
            for r in cursor.fetchall():
                rows.append({'bilgisayar_adi': r[0], 'pc_aciklama': r[1] or ''})
    except Exception as e:
        print(f"[EtiketServisi] PC listele hatasi: {e}")
    return rows


# ============================================================================
# UPSERT / DELETE
# ============================================================================

def upsert_sablon_atama(kullanim_yeri: str, sablon_id: Optional[int],
                        kopya_adedi: int = 1, otomatik_bas: bool = True,
                        aciklama: str = '') -> bool:
    """Sablon atamasini ekle veya guncelle (kullanim_yeri unique)"""
    ensure_tables()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                MERGE sistem.etiket_sablon_atamalari AS target
                USING (SELECT ? AS kullanim_yeri) AS src
                ON target.kullanim_yeri = src.kullanim_yeri
                WHEN MATCHED THEN
                    UPDATE SET sablon_id = ?, kopya_adedi = ?, otomatik_bas = ?,
                               aciklama = ?, guncelleme_tarihi = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (kullanim_yeri, sablon_id, kopya_adedi, otomatik_bas, aciklama)
                    VALUES (?, ?, ?, ?, ?);
            """,
                kullanim_yeri,
                sablon_id, kopya_adedi, 1 if otomatik_bas else 0, aciklama,
                kullanim_yeri, sablon_id, kopya_adedi, 1 if otomatik_bas else 0, aciklama,
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"[EtiketServisi] Sablon atama yazma hatasi: {e}")
        return False


def upsert_pc_yazici_atama(bilgisayar_adi: str, kullanim_yeri: str,
                           yazici_adi: str, format_tipi: str = DEFAULT_FORMAT,
                           pc_aciklama: str = '') -> bool:
    """PC yazici atamasini ekle veya guncelle (bilgisayar_adi + kullanim_yeri unique)"""
    ensure_tables()
    format_tipi = (format_tipi or DEFAULT_FORMAT).upper()
    if format_tipi not in FORMAT_TIPLERI:
        format_tipi = DEFAULT_FORMAT
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                MERGE sistem.pc_yazici_atamalari AS target
                USING (SELECT ? AS bilgisayar_adi, ? AS kullanim_yeri) AS src
                ON target.bilgisayar_adi = src.bilgisayar_adi
                   AND target.kullanim_yeri = src.kullanim_yeri
                WHEN MATCHED THEN
                    UPDATE SET yazici_adi = ?, format_tipi = ?, pc_aciklama = ?,
                               guncelleme_tarihi = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (bilgisayar_adi, pc_aciklama, kullanim_yeri,
                            yazici_adi, format_tipi)
                    VALUES (?, ?, ?, ?, ?);
            """,
                bilgisayar_adi, kullanim_yeri,
                yazici_adi, format_tipi, pc_aciklama,
                bilgisayar_adi, pc_aciklama, kullanim_yeri, yazici_adi, format_tipi,
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"[EtiketServisi] PC atama yazma hatasi: {e}")
        return False


def delete_pc_yazici_atama(atama_id: int) -> bool:
    """PC yazici atamasini sil"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sistem.pc_yazici_atamalari WHERE id = ?", atama_id)
            conn.commit()
        return True
    except Exception as e:
        print(f"[EtiketServisi] Silme hatasi: {e}")
        return False


def delete_sablon_atama(atama_id: int) -> bool:
    """Sablon atamasini sil"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sistem.etiket_sablon_atamalari WHERE id = ?", atama_id)
            conn.commit()
        return True
    except Exception as e:
        print(f"[EtiketServisi] Sablon silme hatasi: {e}")
        return False


# ============================================================================
# ANA SERVIS
# ============================================================================

def _normalize_etiket_data(d: dict) -> dict:
    """
    Modullerden gelen farkli field adlarini godex_ezpl_olustur formatina cevir.
    Eski 'urun'/'adet' gibi alanlari 'stok_adi'/'miktar' icin de doldurur.
    Eksik degerler icin makul varsayilanlar koyar.
    """
    if not d:
        return d
    n = dict(d)  # mutate yerine kopya
    # Field aliaslari (caller esit derecede kullanabilsin)
    n.setdefault('stok_adi', n.get('urun', '') or n.get('stok_adi', ''))
    n.setdefault('miktar', n.get('adet', n.get('saglam_adet', n.get('miktar', 0))))
    n.setdefault('birim', n.get('birim', 'ADET'))
    n.setdefault('palet_no', n.get('palet_no', 1))
    n.setdefault('toplam_palet', n.get('toplam_palet', 1))
    n.setdefault('kaplama', n.get('kaplama', ''))
    n.setdefault('irsaliye_no', n.get('irsaliye_no', ''))
    return n


class EtiketServisi:
    """Merkezi etiket basim servisi"""

    @staticmethod
    def bas(kullanim_yeri: str, etiket_data: dict = None,
            parent=None, etiket_listesi: list = None,
            zorla_dialog: bool = False) -> bool:
        """
        Etiket bas - merkezi API.

        Args:
            kullanim_yeri: 'kalite_final', 'depo_giris' vb.
            etiket_data:   Tek etiket icin dict
            parent:        Dialog parent widget (fallback dialog icin)
            etiket_listesi: Coklu etiket icin liste (None ise [etiket_data] kullanilir)
            zorla_dialog:  True ise eski dialog'u zorla ac (manuel kontrol)

        Returns:
            True: Basildi  /  False: Hata veya iptal
        """
        ensure_tables()

        if etiket_listesi is None:
            etiket_listesi = [etiket_data] if etiket_data else []

        if not etiket_listesi:
            print("[EtiketServisi] Bos etiket listesi, basim atlandi")
            return False

        # Field normalization (urun -> stok_adi, adet -> miktar vb.)
        etiket_listesi = [_normalize_etiket_data(e) for e in etiket_listesi]

        if kullanim_yeri not in KULLANIM_YERLERI:
            print(f"[EtiketServisi] UYARI: Tanimsiz kullanim yeri: {kullanim_yeri}")

        # Manuel kontrol istendi mi?
        if zorla_dialog:
            return EtiketServisi._fallback_dialog(kullanim_yeri, etiket_listesi, parent=parent)

        sablon_atama = get_sablon_atama(kullanim_yeri)
        yazici_atama = get_yazici_atama(kullanim_yeri)
        pc_adi = get_pc_adi()

        # Detayli konfig kontrolu
        eksikler = []
        if not sablon_atama:
            eksikler.append("📄 Sablon atamasi yok (Etiket Sablonlari sekmesi)")
        else:
            if not sablon_atama.get('sablon_id'):
                eksikler.append("📄 Sablon secilmemis (Etiket Sablonlari sekmesi)")
            if not sablon_atama.get('otomatik_bas'):
                eksikler.append("📄 'Otomatik Bas' isaretli degil (Etiket Sablonlari sekmesi)")
        if not yazici_atama:
            eksikler.append(f"🖨️  {pc_adi} icin yazici atanmamis (PC Yazici Atamalari sekmesi)")
        elif not yazici_atama.get('yazici_adi'):
            eksikler.append(f"🖨️  {pc_adi} yazici adi bos")

        print(f"\n[EtiketServisi] bas('{kullanim_yeri}') - PC: {pc_adi}")
        print(f"  sablon_atama: {sablon_atama}")
        print(f"  yazici_atama: {yazici_atama}")

        # Tum konfig hazir -> direkt bas, dialog YOK
        if not eksikler:
            print("  -> OTOMATIK BASILIYOR (dialog yok)")
            ok = EtiketServisi._direkt_bas(
                etiket_listesi=etiket_listesi,
                yazici_adi=yazici_atama['yazici_adi'],
                format_tipi=yazici_atama['format_tipi'],
                kopya_adedi=sablon_atama['kopya_adedi'],
                sablon_id=sablon_atama['sablon_id'],
                parent=parent,
            )
            if ok:
                _statusbar_mesaj(parent,
                    f"✅ Etiket basildi: {yazici_atama['yazici_adi']} "
                    f"({sablon_atama['kopya_adedi']}x)")
            return ok

        # Eksik varsa - kullaniciya acikca bildir, sonra fallback dialog
        print("  -> KONFIG EKSIK:")
        for e in eksikler:
            print(f"    - {e}")
        print("  -> Fallback dialog aciliyor")

        if parent is not None:
            try:
                from PySide6.QtWidgets import QMessageBox
                yer_adi = KULLANIM_YERLERI.get(kullanim_yeri, kullanim_yeri)
                msg = (f"'{yer_adi}' icin otomatik basim ayari TAMAMLANMAMIS:\n\n"
                       + "\n".join(f"   • {e}" for e in eksikler)
                       + "\n\nSistem > Firma Ayarlari > Etiket sekmelerinden "
                         "tamamlayin ve 'Tumunu Kaydet'e basin.\n\n"
                         "Simdilik manuel yazdirma penceresi acilacak.")
                QMessageBox.warning(parent, "Etiket Ayari Eksik", msg)
            except Exception as e:
                print(f"[EtiketServisi] Uyari gosterilemedi: {e}")

        return EtiketServisi._fallback_dialog(kullanim_yeri, etiket_listesi, parent=parent)

    @staticmethod
    def _direkt_bas(etiket_listesi: list, yazici_adi: str, format_tipi: str,
                    kopya_adedi: int, sablon_id: Optional[int],
                    parent=None) -> bool:
        """Soru sormadan dogrudan yaziciya gonder"""
        try:
            tum_etiketler = []
            for etiket in etiket_listesi:
                tum_etiketler.extend([etiket] * max(1, kopya_adedi))

            if format_tipi == 'PDF':
                return EtiketServisi._bas_pdf(tum_etiketler, yazici_adi, sablon_id)

            # EZPL veya ZPL -> Godex direkt
            from utils.etiket_yazdir1 import godex_yazdir
            return godex_yazdir(tum_etiketler, yazici_adi, format_tipi)

        except Exception as e:
            print(f"[EtiketServisi] Direkt bas hatasi: {e}")
            import traceback
            traceback.print_exc()
            if parent is not None:
                try:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.critical(parent, "Etiket Hatasi",
                                         f"Etiket basilamadi:\n{e}")
                except Exception:
                    pass
            return False

    @staticmethod
    def _bas_pdf(etiket_listesi: list, yazici_adi: str,
                 sablon_id: Optional[int]) -> bool:
        """Sablon ile PDF uret + Windows print spool"""
        try:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix='.pdf', prefix='nexor_etiket_'
            )
            tmp.close()

            if sablon_id:
                from utils.etiket_yazdir import sablon_ile_etiket_pdf_olustur
                sablon_ile_etiket_pdf_olustur(tmp.name, etiket_listesi, sablon_id)
            else:
                from utils.etiket_yazdir import a4_etiket_pdf_olustur
                a4_etiket_pdf_olustur(tmp.name, etiket_listesi)

            # Windows print spool
            try:
                import win32api
                win32api.ShellExecute(0, "print", tmp.name, f'"{yazici_adi}"', ".", 0)
                return True
            except ImportError:
                # win32 yoksa default uygulama ile ac (kullanici manuel basar)
                import subprocess
                subprocess.Popen(['start', '', tmp.name], shell=True)
                return True
        except Exception as e:
            print(f"[EtiketServisi] PDF bas hatasi: {e}")
            return False

    @staticmethod
    def _fallback_dialog(kullanim_yeri: str, etiket_listesi: list,
                         parent=None) -> bool:
        """Konfig yoksa veya manuel istense eski dialog'u ac"""
        try:
            from modules.kalite.kalite_final_kontrol import EtiketOnizlemeDialog
        except Exception as e:
            print(f"[EtiketServisi] Fallback dialog import hatasi: {e}")
            return False

        try:
            theme = {}
            if parent is not None and hasattr(parent, 'theme'):
                theme = parent.theme

            etiket_data = etiket_listesi[0] if etiket_listesi else {}
            dlg = EtiketOnizlemeDialog(theme, etiket_data, parent=parent)

            if dlg.exec() != dlg.Accepted:
                return False

            sablon_id = dlg.get_sablon_id()
            yazici = dlg.get_yazici()
            mod = (dlg.get_mod() or 'EZPL').upper()

            if mod == 'PDF':
                return EtiketServisi._bas_pdf(etiket_listesi, yazici, sablon_id)

            from utils.etiket_yazdir1 import godex_yazdir
            return godex_yazdir(etiket_listesi, yazici, mod)
        except Exception as e:
            print(f"[EtiketServisi] Fallback dialog hatasi: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def test_yazici(yazici_adi: str, format_tipi: str = DEFAULT_FORMAT) -> bool:
        """Yazici icin test etiketi bas (Firma Ayarlari > Test Et butonu)"""
        from datetime import datetime
        test_etiket = {
            'stok_kodu':    'TEST-001',
            'stok_adi':     'Test Etiket',
            'musteri':      'NEXOR ERP',
            'kaplama':      '',
            'miktar':       1,
            'birim':        'ADET',
            'palet_no':     1,
            'toplam_palet': 1,
            'lot_no':       f'TEST-{datetime.now().strftime("%H%M%S")}',
            'irsaliye_no':  '',
            'tarih':        datetime.now(),
        }
        try:
            if format_tipi.upper() == 'PDF':
                return EtiketServisi._bas_pdf([test_etiket], yazici_adi, None)
            from utils.etiket_yazdir1 import godex_yazdir
            return godex_yazdir([test_etiket], yazici_adi, format_tipi.upper())
        except Exception as e:
            print(f"[EtiketServisi] Test yazici hatasi: {e}")
            return False


# ============================================================================
# YARDIMCI: Statusbar mesaji (parent main window varsa)
# ============================================================================

def _statusbar_mesaj(parent, msg: str, uyari: bool = False, sure_ms: int = 5000):
    """Parent'in main window'unda statusbar varsa mesaj goster (sessiz fail)"""
    if parent is None:
        return
    try:
        # Parent zincirinde main window'u bul
        w = parent
        while w is not None and not hasattr(w, 'statusBar'):
            w = w.parent()
        if w and hasattr(w, 'statusBar'):
            sb = w.statusBar()
            if sb:
                sb.showMessage(msg, sure_ms)
    except Exception:
        pass
