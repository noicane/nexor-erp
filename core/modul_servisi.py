# -*- coding: utf-8 -*-
"""
NEXOR ERP - Modul Lisans Servisi
Musteri bazli modul aktivasyon durumunu yonetir.

Kullanim:
    from core.modul_servisi import ModulServisi
    servis = ModulServisi.instance()

    if servis.is_aktif('uretim'):
        ...

    # Modul listesi (her biri dict: kod, ad, aktif, zorunlu, bitis_tarihi, ...)
    for mod in servis.tumunu_getir():
        ...

    # DB degisikliginden sonra cache'i yenile
    servis.yenile()

Ozellikler:
- Singleton pattern (tek instance)
- In-memory cache (her is_aktif() cagrisinda DB'ye gitmez)
- gelistirici_modu: config.json'dan okunur, True ise daima True doner
  (gelistirici butun modulleri test edebilmeli)
- Bitis tarihi: aktif=1 olsa bile bitis_tarihi gecmisse pasif sayilir
- Zorunlu moduller: aktif=0 olsa bile True doner (korumali)
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ModulServisi:
    _instance: Optional['ModulServisi'] = None
    _lock = threading.Lock()

    def __init__(self):
        # {modul_kodu: {kod, ad, aktif, zorunlu, bitis, notlar, kategori, ikon, sira}}
        self._cache: Dict[str, dict] = {}
        self._yuklendi = False
        self._gelistirici_modu = self._gelistirici_modu_oku()

    # ---------- Singleton ----------

    @classmethod
    def instance(cls) -> 'ModulServisi':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    cls._instance.yenile()
        return cls._instance

    # ---------- Yardimcilar ----------

    def _gelistirici_modu_oku(self) -> bool:
        """config.json'dan gelistirici_modu bayragini oku"""
        try:
            import json as _json
            from pathlib import Path
            # Uygulama kokunde + C:/NEXOR/
            candidates = [
                Path(__file__).resolve().parent.parent / 'config.json',
                Path('C:/NEXOR/config.json'),
            ]
            for p in candidates:
                if p.exists():
                    data = _json.loads(p.read_text(encoding='utf-8'))
                    if data.get('gelistirici_modu') is True:
                        logger.info("ModulServisi: gelistirici_modu = True (butun moduller aktif)")
                        return True
                    break
        except Exception as e:
            logger.warning("ModulServisi: config.json okuma hatasi: %s", e)
        return False

    def _db_yukle(self) -> Dict[str, dict]:
        """DB'den moduller + durumlari tek sorguda cek"""
        from core.database import get_db_connection
        sonuc: Dict[str, dict] = {}
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    m.modul_kodu, m.modul_adi, m.kategori, m.ikon, m.sira, m.zorunlu,
                    ISNULL(d.aktif, 1) AS aktif,
                    d.bitis_tarihi, d.notlar
                FROM lisans.moduller m
                LEFT JOIN lisans.modul_durumlari d ON m.modul_kodu = d.modul_kodu
                ORDER BY m.sira
            """)
            for row in cur.fetchall():
                kod, ad, kat, ikon, sira, zorunlu, aktif, bitis, notlar = row
                sonuc[kod] = {
                    'kod': kod,
                    'ad': ad,
                    'kategori': kat,
                    'ikon': ikon,
                    'sira': sira,
                    'zorunlu': bool(zorunlu),
                    'aktif': bool(aktif),
                    'bitis_tarihi': bitis,
                    'notlar': notlar,
                }
            conn.close()
        except Exception as e:
            logger.error("ModulServisi: DB yukleme hatasi: %s", e)
            # Hata durumunda bos dict - guard'lar false donecek,
            # ama zorunlu moduller yine de True doner (altta kod sertlestirilecek)
        return sonuc

    # ---------- Public API ----------

    def yenile(self) -> None:
        """Cache'i DB'den yeniden yukle (modul degistiginde cagrilir)"""
        self._cache = self._db_yukle()
        self._yuklendi = True
        logger.info("ModulServisi: %d modul yuklendi", len(self._cache))

    def is_aktif(self, modul_kodu: str) -> bool:
        """
        Modul aktif mi? Guard fonksiyonu.

        Sira:
        1) gelistirici_modu True ise daima True (geliştirici test için)
        2) Modul zorunlu ise daima True (config hatasina karsi koruma)
        3) Bitis tarihi gecmis ise False
        4) aktif bayragina bak
        """
        if self._gelistirici_modu:
            return True

        if not self._yuklendi:
            self.yenile()

        m = self._cache.get(modul_kodu)
        if m is None:
            # Taninmayan kod - hicbir yerde tanimli degilse reddet
            logger.warning("ModulServisi: taninmayan modul kodu '%s'", modul_kodu)
            return False

        if m.get('zorunlu'):
            return True

        bitis = m.get('bitis_tarihi')
        if bitis and isinstance(bitis, datetime) and bitis < datetime.now():
            return False

        return bool(m.get('aktif', False))

    def getir(self, modul_kodu: str) -> Optional[dict]:
        """Tek modulun detayini dondur (None ise tanimli degil)"""
        if not self._yuklendi:
            self.yenile()
        return self._cache.get(modul_kodu)

    def tumunu_getir(self) -> List[dict]:
        """Tum modulleri sira'ya gore dondur"""
        if not self._yuklendi:
            self.yenile()
        return sorted(self._cache.values(), key=lambda m: m.get('sira', 100))

    def aktif_kodlar(self) -> set:
        """is_aktif() True donen kodlarin set'ini dondur (hizli filtre icin)"""
        return {m['kod'] for m in self.tumunu_getir() if self.is_aktif(m['kod'])}

    def durum_guncelle(
        self,
        modul_kodu: str,
        aktif: bool,
        bitis_tarihi: Optional[datetime] = None,
        notlar: Optional[str] = None,
    ) -> bool:
        """
        Modul durumunu DB'de guncelle + cache'i yenile.
        Zorunlu modul ise izin verilmez.
        """
        m = self.getir(modul_kodu)
        if m is None:
            raise ValueError(f"Taninmayan modul: {modul_kodu}")
        if m.get('zorunlu'):
            raise ValueError(f"Zorunlu modul pasiflestirilemez: {modul_kodu}")

        from core.database import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE lisans.modul_durumlari
                SET aktif = ?, bitis_tarihi = ?, notlar = ?
                WHERE modul_kodu = ?
            """, (1 if aktif else 0, bitis_tarihi, notlar, modul_kodu))

            if cur.rowcount == 0:
                # Satir yoksa ekle
                cur.execute("""
                    INSERT INTO lisans.modul_durumlari
                        (modul_kodu, aktif, bitis_tarihi, notlar)
                    VALUES (?, ?, ?, ?)
                """, (modul_kodu, 1 if aktif else 0, bitis_tarihi, notlar))

            conn.commit()
            logger.info(
                "Modul durumu guncellendi: %s aktif=%s bitis=%s",
                modul_kodu, aktif, bitis_tarihi
            )
        finally:
            conn.close()

        self.yenile()
        return True

    @property
    def gelistirici_modu(self) -> bool:
        return self._gelistirici_modu

    def set_gelistirici_modu(self, deger: bool) -> bool:
        """Gelistirici modu bayragini IN-MEMORY ayarla (session-only).

        master/008384 toggle ile cagrilir. Config'e YAZMAZ; NEXOR kapaninca
        kaybolur. Bayi config.json'a elle `"gelistirici_modu": true` yazarak
        persistent yapabilir; bu durumda startup'ta okunur.
        Returns: True her zaman.
        """
        self._gelistirici_modu = bool(deger)
        logger.info("ModulServisi: gelistirici_modu = %s (session-only)", deger)
        return True


# Kullanim kolayligi icin module-level kisayol
def is_aktif(modul_kodu: str) -> bool:
    return ModulServisi.instance().is_aktif(modul_kodu)
