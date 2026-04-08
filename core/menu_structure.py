# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Menü Yapısı
Tüm menüler ve alt menüler burada tanımlı
"""

MENU_STRUCTURE = [
    {"id": "dashboard", "icon": "📊", "label": "Dashboard", "children": []},
    
    {"id": "cariler", "icon": "👥", "label": "Cariler", "children": [
        {"id": "cari_liste", "label": "Cari Listesi"},
        {"id": "cari_detay", "label": "Cari Detay"},
        {"id": "cari_bakiye", "label": "Cari Bakiye"},
        {"id": "cari_adresler", "label": "Cari Adresler"},
        {"id": "cari_yetkililer", "label": "Cari Yetkililer"},
        {"id": "cari_spesifikasyonlar", "label": "Cari Spesifikasyonlar"},
    ]},
    
    {"id": "stok", "icon": "📦", "label": "Stok Kartları", "children": [
        {"id": "stok_liste", "label": "Stok Listesi"},
        {"id": "stok_fiyat", "label": "Fiyat Listesi"},
        {"id": "stok_maliyet", "label": "Maliyet Tanımları"},
        {"id": "stok_kimyasal", "label": "Kimyasal Tüketim"},
        {"id": "stok_havuzu", "label": "Stok Havuzu"},
    ]},

    {"id": "teklifler", "icon": "📝", "label": "Teklifler", "children": [
        {"id": "teklif_liste", "label": "Teklif Listesi"},
        {"id": "teklif_sablonlar", "label": "Teklif Şablonları"},
    ]},

    {"id": "is_emirleri", "icon": "📋", "label": "İş Emirleri", "children": [
        {"id": "ie_liste", "label": "İş Emri Listesi"},
        {"id": "ie_yeni", "label": "Yeni İş Emri"},
        {"id": "ie_planlama", "label": "Planlama"},
        {"id": "ie_termin", "label": "Termin Takip"},
    ]},
    
    {"id": "uretim", "icon": "🏭", "label": "Üretim", "children": [
        {"id": "uretim_giris", "label": "Üretim Girişi"},
        {"id": "uretim_hat", "label": "Hat Takip"},
        {"id": "uretim_rework", "label": "Rework (Söküm)"},
        {"id": "uretim_verimlilik", "label": "Verimlilik Analizi"},
        {"id": "uretim_durus", "label": "Duruş Kayıtları"},
        {"id": "uretim_vardiya", "label": "Vardiya Raporu"},
        {"id": "kaplama_planlama", "label": "Kaplama Planlama"},
        {"id": "uretim_bara_dashboard", "label": "Bara Dashboard"},
    ]},
    
    {"id": "kalite", "icon": "✅", "label": "Kalite", "children": [
        {"id": "kalite_giris", "label": "Giriş Kalite"},
        {"id": "kalite_proses", "label": "Proses Kalite"},
        {"id": "kalite_final_kontrol", "label": "Final Kalite Kontrol"},
        {"id": "kalite_red", "label": "Red Kayıtları"},
        {"id": "event_log", "label": "📋 Event Log"},
        {"id": "kalite_8d", "label": "8D / CAPA"},
        {"id": "kalite_ppap", "label": "PPAP"},
        {"id": "kalite_kalibrasyon", "label": "Kalibrasyon"},
        {"id": "kalite_kontrol_plani", "label": "Kontrol Planları"},
        {"id": "kalite_fmea", "label": "FMEA Yönetimi"},
        {"id": "kalite_polivelans", "label": "Polivelans Matrisi"},
        {"id": "dokumantasyon_yonetimi", "label": "Dokümantasyon Yönetimi"},
    ]},
    
    {"id": "laboratuvar", "icon": "🔬", "label": "Laboratuvar", "children": [
        {"id": "lab_dashboard", "label": "📊 Dashboard"},
        {"id": "lab_event_log", "label": "📋 Event Log"},
        {"id": "lab_sonuc", "label": "Analiz Sonuçları"},
        {"id": "lab_analiz", "label": "Banyo Analiz Kayıtları"},
        {"id": "lab_banyo", "label": "Banyo Kartları"},
        {"id": "stok_kimyasal", "label": "Kimyasal Stok"},
        {"id": "lab_tanim", "label": "Test Tanımları"},
        {"id": "lab_kaplama_test", "label": "🔬 Kaplama Test"},
    ]},
    
    {"id": "sevkiyat", "icon": "🚚", "label": "Sevkiyat", "children": [
        {"id": "sevk_liste", "label": "Sevkiyat Listesi"},
        {"id": "sevk_yeni", "label": "Yeni Sevkiyat"},
        {"id": "sevk_irsaliye", "label": "İrsaliye Yazdır"},
        {"id": "sevk_iade", "label": "İade Girişi"},
    ]},
    
    {"id": "satinalma", "icon": "🛒", "label": "Satınalma", "children": [
        {"id": "satinalma_talepler", "label": "Satınalma Talepleri"},
        {"id": "satinalma_siparisler", "label": "Satınalma Siparişleri"},
        {"id": "satinalma_mal_kabul", "label": "Mal Kabul"},
        {"id": "satinalma_anlasmalar", "label": "Tedarikçi Anlaşmaları"},
    ]},
    
    {"id": "depo", "icon": "🏪", "label": "Depo / Emanet", "children": [
        {"id": "depo_takip", "label": "Depo Takip"},
        {"id": "depo_kabul", "label": "Mal Kabul"},
        {"id": "depo_cikis", "label": "Depo Çıkış"},
        {"id": "depo_emanet", "label": "Emanet Stoklar"},
        {"id": "depo_sayim", "label": "Stok Sayım"},
        {"id": "depo_stok_takip", "label": "Stok Takip"},
    ]},
    
    {"id": "ik", "icon": "🧑‍💼", "label": "İnsan Kaynakları", "children": [
        {"id": "ik_personel", "label": "Personel Listesi"},
        {"id": "ik_puantaj", "label": "Puantaj"},
        {"id": "ik_izin", "label": "İzin Yönetimi"},
        {"id": "ik_zimmet", "label": "Zimmet Takip"},
        {"id": "ik_vardiya", "label": "Vardiya Planlama"},
        {"id": "ik_egitim", "label": "Eğitim Takip"},
        # PDKS Alt Menüsü
        {"id": "ik_pdks", "label": "📡 PDKS Canlı Monitör"},
        {"id": "pdks_cihaz_ayarlari", "label": "🔌 Cihaz Ayarları"},
        {"id": "pdks_service_control", "label": "🤖 Okuma Servisi"},
    ]},
    
    {"id": "bakim", "icon": "🔧", "label": "Bakım", "children": [
        {"id": "bakim_durus_talep", "label": "Duruş Talepleri"},
        {"id": "bakim_ekipman", "label": "Ekipman Kartları"},
        {"id": "bakim_plan", "label": "Bakım Planları"},
        {"id": "bakim_ariza", "label": "Arıza Kayıtları"},
        {"id": "bakim_yedek", "label": "Yedek Parça"},
    ]},
    
    {"id": "isg", "icon": "🦺", "label": "İş Sağlığı Güvenliği", "children": [
        {"id": "isg_risk_degerlendirme", "label": "Risk Değerlendirme"},
        {"id": "isg_olay_kayitlari", "label": "Olay Kayıtları"},
        {"id": "isg_kkd_dagitim", "label": "KKD Dağıtım"},
        {"id": "isg_egitimler", "label": "İSG Eğitimleri"},
        {"id": "isg_saglik_gozetimi", "label": "Sağlık Gözetimi"},
        {"id": "isg_denetimler", "label": "Saha Denetimleri"},
        {"id": "isg_acil_durum", "label": "Acil Durum Ekipleri"},
        {"id": "isg_tatbikatlar", "label": "Tatbikatlar"},
        {"id": "isg_yasal_takip", "label": "Yasal Takip"},
        {"id": "isg_gbf", "label": "GBF/MSDS"},
    ]},
    
    {"id": "cevre", "icon": "🌿", "label": "Çevre Yönetimi", "children": [
        {"id": "cevre_atik_yonetimi", "label": "Atık Yönetimi"},
        {"id": "cevre_emisyon", "label": "Emisyon Takibi"},
        {"id": "cevre_izinler", "label": "Çevresel İzinler"},
        {"id": "cevre_yasal_takip", "label": "Yasal Takip"},
        {"id": "cevre_su_enerji", "label": "Su/Enerji Tüketimi"},
        {"id": "cevre_atiksu", "label": "Atıksu Analizleri"},
        {"id": "cevre_denetimler", "label": "Çevre Denetimleri"},
        {"id": "cevre_kimyasal", "label": "Kimyasal Envanter"},
    ]},
    
    {"id": "aksiyonlar", "icon": "📋", "label": "Aksiyonlar", "children": [
        {"id": "aksiyon_dashboard", "label": "Aksiyon Dashboard"},
        {"id": "aksiyon_liste", "label": "Aksiyon Listesi"},
        {"id": "aksiyon_bana_atanan", "label": "Bana Atananlar"},
    ]},

    {"id": "raporlar", "icon": "📈", "label": "Raporlar", "children": [
        {"id": "rapor_uretim", "label": "Üretim Raporları"},
        {"id": "rapor_kalite", "label": "Kalite Raporları"},
        {"id": "rapor_maliyet", "label": "Maliyet Raporları"},
        {"id": "rapor_kpi", "label": "KPI Dashboard"},
        {"id": "urun_izlenebilirlik", "label": "Ürün İzlenebilirlik"},
    ]},

    {"id": "tanimlar", "icon": "⚙️", "label": "Tanımlar", "children": [
        {"id": "tanim_hat", "label": "Üretim Hatları"},
        {"id": "tanim_proses", "label": "Prosesler"},
        {"id": "tanim_rota", "label": "Rotalar"},
        {"id": "tanim_kaplama", "label": "Kaplama Tipleri"},
        {"id": "tanim_malzeme", "label": "Malzeme Grupları"},
        {"id": "tanim_depo", "label": "Depo Tanımları"},
        {"id": "tanim_akis", "label": "Akış Şablonları"},
        {"id": "tanim_hata_turleri", "label": "Hata Türleri"},
        {"id": "tanim_vardiya", "label": "Vardiya Tanımları"},
        {"id": "tanim_izin_turleri", "label": "İzin Türleri"},
        {"id": "tanim_zimmet_turleri", "label": "Zimmet Türleri"},
        {"id": "tanim_organizasyon", "label": "Organizasyon Tanımları"},
        {"id": "tanim_soforler", "label": "Şoför Tanımları"},
        {"id": "tanim_araclar", "label": "Araç Tanımları"},
        {"id": "tanim_numara", "label": "Numara Tanımları"},
        {"id": "tanim_etiket_tasarim", "label": "Etiket Tasarım"},
        {"id": "tanim_giris_kalite_kriterleri", "label": "Giriş Kalite Kriterleri"},
    ]},

    {"id": "yonetim", "icon": "📊", "label": "Yönetim", "password": "Nexor-Atlas2026", "children": [
        {"id": "yonetim_ciro_analiz", "label": "Ciro Analizi"},
        {"id": "yonetim_bara_hesaplama", "label": "Bara Hesaplama"},
        {"id": "tanim_is_merkezi", "label": "İş Merkezi Tanımları"},
        {"id": "maliyet_personel", "label": "Personel Maliyet"},
        {"id": "stok_maliyet", "label": "Ürün Maliyet Tanımları"},
        {"id": "stok_fiyat", "label": "Fiyat Listesi"},
    ]},

    {"id": "sistem", "icon": "🛡️", "label": "Sistem", "children": [
        {"id": "sistem_veritabani", "label": "Veritabanı Bağlantıları"},
        {"id": "bildirim_sistemi", "label": "Bildirimler"},
        {"id": "bildirim_tercihleri", "label": "Bildirim Tercihleri"},
        {"id": "sistem_whatsapp", "label": "WhatsApp Bildirimleri"},
        {"id": "sistem_kullanici", "label": "Kullanıcılar"},
        {"id": "sistem_rol", "label": "Roller"},
        {"id": "sistem_yetki", "label": "İzinler"},
        {"id": "sistem_rol_izin", "label": "Rol İzinleri"},
        {"id": "sistem_kullanici_yetki", "label": "Kullanıcı Yetkileri"},
        {"id": "sistem_firma", "label": "Firma Bilgileri"},
        {"id": "sistem_ayar", "label": "Sistem Ayarları"},
        {"id": "sistem_log", "label": "İşlem Logları"},
        {"id": "sistem_yedekleme", "label": "Yedekleme"},
    ]},
]


def get_page_title(page_id: str) -> str:
    """Sayfa ID'sine göre başlık döndür"""
    for menu in MENU_STRUCTURE:
        if menu['id'] == page_id:
            return menu['label']
        for child in menu.get('children', []):
            if child['id'] == page_id:
                return child['label']
    return page_id


def get_page_icon(page_id: str) -> str:
    """Sayfa ID'sine göre icon döndür"""
    for menu in MENU_STRUCTURE:
        if menu['id'] == page_id:
            return menu['icon']
        for child in menu.get('children', []):
            if child['id'] == page_id:
                return menu['icon']
    return "📄"
