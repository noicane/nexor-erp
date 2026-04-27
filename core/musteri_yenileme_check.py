# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Musteri Yenileme Uyarilari (M2.4)

Aktif profilin anlasma/bakim/lisans bitis tarihlerini kontrol eder ve
60/30/7 gun kala bir kez bildirim olusturur. Gunluk frekans:
profile['raporlama']['son_yenileme_check_tarihi'] cache'i.

Kullanim:
    from core.musteri_yenileme_check import check_renewal_warnings
    check_renewal_warnings()  # main.py startup

Tarih: 2026-04-27
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Uyari esik degerleri (gun)
ESIKLER = [60, 30, 7, 1]


def _str_to_date(s: str) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _kalan_gun(bitis_str: str) -> Optional[int]:
    d = _str_to_date(bitis_str)
    if d is None:
        return None
    return (d - date.today()).days


def _esik_belirle(kalan: int) -> Optional[int]:
    """Verilen kalan gune gore EN UYGUN esigi don. Negatif kalan = -1 (gecmis)."""
    if kalan is None:
        return None
    if kalan < 0:
        return -1  # Gecmis
    for esik in sorted(ESIKLER):  # 1, 7, 30, 60
        if kalan <= esik:
            return esik
    return None  # Henuz uzak


def _bildirim_gonder(baslik: str, mesaj: str, onem: str) -> bool:
    """Aktif kurulumdaki tum 'admin' rollerine bildirim gonder.

    BildirimService DB'ye yazar; DB yoksa sessizce False doner.
    """
    try:
        from core.bildirim_service import BildirimService
        from core.database import execute_query
        # Admin rolundeki kullanicilari bul (tipik isim: 'Admin' / 'Yonetici')
        rows = execute_query("""
            SELECT k.id
            FROM sistem.kullanicilar k
            INNER JOIN sistem.roller r ON r.id = k.rol_id
            WHERE k.aktif_mi = 1 AND k.silindi_mi = 0
              AND (r.kod = 'ADMIN' OR r.ad LIKE N'%dmin%' OR r.ad LIKE N'%onetic%')
        """) or []
        gonderildi = 0
        for r in rows:
            uid = r.get('id') if isinstance(r, dict) else r[0]
            if BildirimService.gonder(
                kullanici_id=uid,
                baslik=baslik,
                mesaj=mesaj,
                modul='SISTEM',
                onem=onem,
                tip='HATIRLATMA',
            ):
                gonderildi += 1
        return gonderildi > 0
    except Exception as e:
        logger.debug("Yenileme bildirimi DB'ye yazilamadi: %s", e)
        return False


def check_renewal_warnings(force: bool = False) -> dict:
    """Aktif profil icin tum bitis tarihlerini kontrol et ve esige takilanlar
    icin bildirim olustur (gun basina 1 kez).

    Returns:
        {'kontrol_edildi': bool, 'uyarilar': [...]}
    """
    try:
        from core.external_config import config_manager
    except Exception as e:
        logger.warning("Yenileme check icin config okunamadi: %s", e)
        return {'kontrol_edildi': False, 'uyarilar': []}

    aktif = config_manager.get_active_profile()
    profil = config_manager.get_profile(aktif) or {}

    # Gunluk cache: gun degismediyse skip (force degilse)
    rep = profil.get('raporlama') or {}
    bugun_str = date.today().strftime("%Y-%m-%d")
    son_check = rep.get('son_yenileme_check_tarihi') or ''
    if not force and son_check == bugun_str:
        logger.debug("Yenileme check bugun zaten yapilmis (%s)", aktif)
        return {'kontrol_edildi': False, 'uyarilar': []}

    musteri_adi = profil.get('musteri_adi') or aktif
    uyarilar: list[dict] = []

    # 1) Anlasma bitis
    a = profil.get('anlasma') or {}
    kalan = _kalan_gun(a.get('bitis_tarihi', ''))
    esik = _esik_belirle(kalan) if kalan is not None else None
    if esik is not None:
        if esik == -1:
            uyarilar.append({
                'tip': 'ANLASMA_GECMIS',
                'baslik': f"Anlasma bitis tarihi GECMIS - {musteri_adi}",
                'mesaj': f"{musteri_adi} musterisinin sozlesme bitis tarihi gecmis ({a.get('bitis_tarihi')}). "
                         f"Yenileme islemi yapilmamis.",
                'onem': 'KRITIK',
                'kalan': kalan,
            })
        else:
            onem = 'KRITIK' if esik <= 7 else ('YUKSEK' if esik <= 30 else 'NORMAL')
            uyarilar.append({
                'tip': f'ANLASMA_{esik}',
                'baslik': f"Sozlesme yenileme yaklasiyor ({kalan} gun) - {musteri_adi}",
                'mesaj': f"{musteri_adi} musterisinin sozlesmesinin bitmesine {kalan} gun kaldi. "
                         f"Bitis tarihi: {a.get('bitis_tarihi')}. "
                         f"Lisans tipi: {a.get('lisans_tipi', 'YILLIK')}, "
                         f"yenileme tipi: {a.get('yenileme_tipi', 'MANUEL')}.",
                'onem': onem,
                'kalan': kalan,
            })

    # 2) Bakim bitis
    b = profil.get('bakim') or {}
    if b.get('var'):
        kalan = _kalan_gun(b.get('bitis_tarihi', ''))
        esik = _esik_belirle(kalan) if kalan is not None else None
        if esik is not None:
            if esik == -1:
                uyarilar.append({
                    'tip': 'BAKIM_GECMIS',
                    'baslik': f"Bakim anlasmasi bitti - {musteri_adi}",
                    'mesaj': f"{musteri_adi} bakim anlasmasi bitis tarihi gecmis ({b.get('bitis_tarihi')}).",
                    'onem': 'YUKSEK',
                    'kalan': kalan,
                })
            else:
                onem = 'KRITIK' if esik <= 7 else ('YUKSEK' if esik <= 30 else 'NORMAL')
                uyarilar.append({
                    'tip': f'BAKIM_{esik}',
                    'baslik': f"Bakim yenileme yaklasiyor ({kalan} gun) - {musteri_adi}",
                    'mesaj': f"{musteri_adi} bakim anlasmasi {kalan} gun icinde bitiyor. "
                             f"Aylik ucret: {b.get('aylik_ucret', 0)}. "
                             f"Bitis tarihi: {b.get('bitis_tarihi')}.",
                    'onem': onem,
                    'kalan': kalan,
                })

    # 3) Sonraki bakim faturasi
    sf_kalan = _kalan_gun((profil.get('bakim') or {}).get('sonraki_fatura_tarihi', ''))
    if sf_kalan is not None and 0 <= sf_kalan <= 7:
        uyarilar.append({
            'tip': f'BAKIM_FATURA_{sf_kalan}',
            'baslik': f"Bakim faturasi yaklasiyor - {musteri_adi}",
            'mesaj': f"{musteri_adi} musterisinin bakim faturasi {sf_kalan} gun icinde kesilmeli.",
            'onem': 'NORMAL',
            'kalan': sf_kalan,
        })

    # 4) Modul lisans bitisleri (modul_durumlari'ndan)
    moduller_aktif = profil.get('moduller_aktif') or {}
    for kod, dur in moduller_aktif.items():
        if not isinstance(dur, dict) or not dur.get('aktif', True):
            continue
        bitis = dur.get('bitis_tarihi') or ''
        if not bitis:
            continue
        kalan = _kalan_gun(bitis)
        esik = _esik_belirle(kalan) if kalan is not None else None
        if esik is None:
            continue
        if esik == -1:
            uyarilar.append({
                'tip': f'MODUL_GECMIS_{kod}',
                'baslik': f"Modul lisansi GECMIS: {kod}",
                'mesaj': f"{musteri_adi} '{kod}' modul lisansi bitis tarihi gecmis ({bitis}).",
                'onem': 'YUKSEK',
                'kalan': kalan,
            })
        else:
            onem = 'KRITIK' if esik <= 7 else ('YUKSEK' if esik <= 30 else 'NORMAL')
            uyarilar.append({
                'tip': f'MODUL_{esik}_{kod}',
                'baslik': f"Modul lisansi yenileme yaklasiyor: {kod} ({kalan} gun)",
                'mesaj': f"{musteri_adi} '{kod}' modul lisansi {kalan} gun icinde bitiyor ({bitis}).",
                'onem': onem,
                'kalan': kalan,
            })

    # Bildirim gonder
    bildirim_yazildi = 0
    for u in uyarilar:
        if _bildirim_gonder(u['baslik'], u['mesaj'], u['onem']):
            bildirim_yazildi += 1

    # Cache: bugun kontrol edildi (1 kez)
    try:
        rep_yeni = dict(rep)
        rep_yeni['son_yenileme_check_tarihi'] = bugun_str
        config_manager.set('raporlama', rep_yeni)
        config_manager.save()
    except Exception as e:
        logger.warning("Yenileme check tarih cache yazilamadi: %s", e)

    if uyarilar:
        logger.info(
            "Yenileme check: %d uyari (%d bildirim DB'ye yazildi) - profil=%s",
            len(uyarilar), bildirim_yazildi, aktif
        )

    return {'kontrol_edildi': True, 'uyarilar': uyarilar}
