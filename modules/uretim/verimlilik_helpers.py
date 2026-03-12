# -*- coding: utf-8 -*-
"""
NEXOR ERP - Verimlilik Analizi Yardımcı Fonksiyonlar
Ortak kazan tespiti, hat belirleme, grup yönetimi
"""

# Statik banyo grupları - bilinen fiziksel paylaşımlar
BANYO_GRUPLARI_SEED = {
    'AYA': {'tanks': [14, 15], 'hat': 'ORTAK'},
    'SYA': {'tanks': [5, 6, 7, 8], 'hat': 'ORTAK'},
    'FIRIN': {'tanks': [114, 115, 116, 117], 'hat': 'KTL'},
    'YUKLEME_KTL': {'tanks': list(range(131, 141)), 'hat': 'KTL'},
    'ALKALI_CINKO': {'tanks': list(range(210, 215)), 'hat': 'CINKO'},
    'KURUTMA': {'tanks': [235, 237], 'hat': 'CINKO'},
    'YUKLEME_CINKO': {'tanks': list(range(238, 248)), 'hat': 'CINKO'},
}


def get_hat_from_tank(tank_no):
    """Kazan numarasından hat kodunu belirle"""
    if 1 <= tank_no <= 99:
        return 'ON'
    elif 101 <= tank_no <= 143:
        return 'KTL'
    elif 201 <= tank_no <= 247:
        return 'CINKO'
    return 'ORTAK'


def detect_shared_tanks(plc_conn, days=7):
    """
    PLC verisinden ortak kazan gruplarını tespit et.
    Aynı recete + aynı adım = farklı kazanlar -> ortak kazan grubu.
    """
    dynamic_groups = {}
    try:
        cursor = plc_conn.cursor()
        cursor.execute(f"""
            SELECT ReceteNo, ReceteAdim,
                   STRING_AGG(CAST(KznNo AS VARCHAR), ',') WITHIN GROUP (ORDER BY KznNo) as kazanlar,
                   COUNT(DISTINCT KznNo) as kazan_sayisi
            FROM (
                SELECT DISTINCT ReceteNo, ReceteAdim, KznNo
                FROM dbo.data
                WHERE TarihDoldurma >= DATEADD(DAY, -{int(days)}, GETDATE())
                  AND ReceteAdim > 0
            ) sub
            GROUP BY ReceteNo, ReceteAdim
            HAVING COUNT(DISTINCT KznNo) > 1
        """)

        # Aynı kazan setini paylaşan adımları grupla
        kazan_setleri = {}
        for row in cursor.fetchall():
            kazanlar_str = row[2]
            kazan_list = sorted([int(k) for k in kazanlar_str.split(',')])
            kazan_key = tuple(kazan_list)

            if kazan_key not in kazan_setleri:
                kazan_setleri[kazan_key] = {
                    'tanks': kazan_list,
                    'receteler': set(),
                    'adimlar': set()
                }
            kazan_setleri[kazan_key]['receteler'].add(row[0])
            kazan_setleri[kazan_key]['adimlar'].add(row[1])

        # Dinamik grup isimlendirme
        idx = 0
        for kazan_key, info in kazan_setleri.items():
            tanks = info['tanks']
            hat = get_hat_from_tank(tanks[0])

            # Statik grupta zaten var mı kontrol et
            already_in_seed = False
            for seed_name, seed_info in BANYO_GRUPLARI_SEED.items():
                if set(tanks) == set(seed_info['tanks']):
                    already_in_seed = True
                    break
                # Alt küme kontrolü
                if set(tanks).issubset(set(seed_info['tanks'])):
                    already_in_seed = True
                    break

            if not already_in_seed:
                idx += 1
                group_name = f"DYN_GRUP_{idx}"
                dynamic_groups[group_name] = {
                    'tanks': tanks,
                    'hat': hat
                }
    except Exception as e:
        print(f"Dinamik ortak kazan tespiti hatası: {e}")

    return dynamic_groups


def build_combined_groups(plc_conn=None, days=7):
    """Statik + dinamik grupları birleştir"""
    groups = {}

    # Statik grupları ekle
    for name, info in BANYO_GRUPLARI_SEED.items():
        groups[name] = {
            'tanks': list(info['tanks']),
            'hat': info['hat'],
            'source': 'static'
        }

    # Dinamik grupları ekle
    if plc_conn:
        dynamic = detect_shared_tanks(plc_conn, days)
        for name, info in dynamic.items():
            groups[name] = {
                'tanks': info['tanks'],
                'hat': info['hat'],
                'source': 'dynamic'
            }

    return groups


def build_tank_to_group_map(groups):
    """Tank -> grup eşleştirme haritası oluştur"""
    tank_map = {}
    for group_name, info in groups.items():
        for tank in info['tanks']:
            if tank not in tank_map:
                tank_map[tank] = group_name
    return tank_map
