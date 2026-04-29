# -*- coding: utf-8 -*-
"""
ATLAS KATAFOREZ - Şablon Ekleme Fonksiyonu
Bu dosyayı çalıştırarak Atlas dikey etiket şablonunu veritabanına ekleyebilirsiniz
"""

import sys
import os

# Script'in çalıştığı dizine göre import yolunu ayarla
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from core.database import get_db_connection
except ImportError:
    from database import get_db_connection

from datetime import datetime
import json

from config import NAS_PATHS


def atlas_sablon_ekle():
    """Atlas Kataforez dikey etiket şablonunu veritabanına ekle"""

    # Şablon tasarımı (JSON)
    tasarim = {
        "version": "1.0",
        "label_width": 50,
        "label_height": 100,
        "elements": [
            # Logo
            {
                "type": "IMAGE",
                "x": 10,
                "y": 5,
                "width": 30,
                "height": 8,
                "field": "LOGO",
                "name": "Atlas Logo",
                "path": NAS_PATHS["logo_path"],
                "fit_mode": "contain"
            },
            # İrsaliye No
            {
                "type": "TEXT",
                "x": 25,
                "y": 14,
                "content": "{irsaliye_no}",
                "font_name": "Helvetica",
                "font_size": 7,
                "align": "center",
                "name": "İrsaliye No"
            },
            # Header çizgisi
            {
                "type": "LINE",
                "x": 3,
                "y": 18,
                "width": 44,
                "height": 0,
                "thickness": 0.8,
                "color": "#000000",
                "name": "Header Çizgisi"
            },
            # Ürün Resmi
            {
                "type": "IMAGE",
                "x": 3,
                "y": 20,
                "width": 44,
                "height": 52,
                "field": "{resim_path}",
                "name": "Ürün Resmi",
                "border": True,
                "border_width": 0.5,
                "border_color": "#333333"
            },
            # Stok Kodu Çerçevesi
            {
                "type": "RECT",
                "x": 8,
                "y": 74,
                "width": 34,
                "height": 5,
                "border": True,
                "border_width": 0.6,
                "border_color": "#000000",
                "fill": False,
                "name": "Stok Kodu Çerçevesi"
            },
            # Stok Kodu
            {
                "type": "TEXT",
                "x": 25,
                "y": 77,
                "content": "{stok_kodu}",
                "font_name": "Helvetica-Bold",
                "font_size": 11,
                "align": "center",
                "name": "Stok Kodu"
            },
            # Stok Adı
            {
                "type": "TEXT",
                "x": 25,
                "y": 82,
                "content": "{stok_adi}",
                "font_name": "Helvetica",
                "font_size": 9,
                "align": "center",
                "max_width": 44,
                "wrap": True,
                "name": "Stok Adı"
            },
            # Ayırıcı 1
            {
                "type": "LINE",
                "x": 5,
                "y": 88,
                "width": 40,
                "height": 0,
                "thickness": 0.3,
                "color": "#cccccc",
                "name": "Ayırıcı 1"
            },
            # Müşteri
            {
                "type": "TEXT",
                "x": 25,
                "y": 91,
                "content": "MÜŞ: {musteri}",
                "font_name": "Helvetica",
                "font_size": 7,
                "align": "center",
                "name": "Müşteri"
            },
            # Tip (kaplama)
            {
                "type": "TEXT",
                "x": 25,
                "y": 95,
                "content": "TİP: {tip}",
                "font_name": "Helvetica",
                "font_size": 7,
                "align": "center",
                "name": "Tip"
            },
            # Ayırıcı 2
            {
                "type": "LINE",
                "x": 5,
                "y": 99,
                "width": 40,
                "height": 0,
                "thickness": 0.3,
                "color": "#cccccc",
                "name": "Ayırıcı 2"
            },
            # Miktar Kutusu
            {
                "type": "RECT",
                "x": 4,
                "y": 102,
                "width": 42,
                "height": 5,
                "border": True,
                "border_width": 0.3,
                "border_color": "#999999",
                "fill": True,
                "fill_color": "#f5f5f5",
                "name": "Miktar Kutusu"
            },
            # Miktar
            {
                "type": "TEXT",
                "x": 25,
                "y": 105,
                "content": "{miktar} {birim}",
                "font_name": "Helvetica-Bold",
                "font_size": 10,
                "align": "center",
                "name": "Miktar"
            },
            # Palet
            {
                "type": "TEXT",
                "x": 25,
                "y": 110,
                "content": "PALET: {palet_no:02d}/{toplam_palet:02d}",
                "font_name": "Helvetica-Bold",
                "font_size": 8,
                "align": "center",
                "name": "Palet Bilgisi"
            },
            # LOT Çerçevesi
            {
                "type": "RECT",
                "x": 4,
                "y": 114,
                "width": 42,
                "height": 10,
                "border": True,
                "border_width": 0.8,
                "border_color": "#000000",
                "fill": False,
                "name": "LOT Çerçevesi"
            },
            # LOT Etiketi
            {
                "type": "TEXT",
                "x": 25,
                "y": 118,
                "content": "LOT:",
                "font_name": "Helvetica-Bold",
                "font_size": 8,
                "align": "center",
                "name": "LOT Etiketi"
            },
            # LOT Numarası
            {
                "type": "TEXT",
                "x": 25,
                "y": 121,
                "content": "{lot_no}",
                "font_name": "Helvetica-Bold",
                "font_size": 9,
                "align": "center",
                "name": "LOT Numarası"
            },
            # Footer Çizgisi
            {
                "type": "LINE",
                "x": 3,
                "y": 78,
                "width": 44,
                "height": 0,
                "thickness": 0.8,
                "color": "#000000",
                "name": "Footer Üst Çizgisi"
            },
            # QR (sevkte miktar etiketten okunur: lot|miktar)
            {
                "type": "BARCODE",
                "x": 30,
                "y": 80,
                "width": 18,
                "height": 18,
                "w_mm": 18,
                "h_mm": 18,
                "content": "{qr_data}",
                "field": "qr_data",
                "kod_tipi": "QR",
                "show_text": True,
                "align": "center",
                "name": "LOT QR (lot|miktar)"
            },
            # Tarih
            {
                "type": "TEXT",
                "x": 25,
                "y": 96,
                "content": "{tarih:%d.%m.%Y}",
                "font_name": "Helvetica",
                "font_size": 7,
                "align": "center",
                "name": "Tarih"
            }
        ]
    }
    
    # JSON string'e çevir
    tasarim_json = json.dumps(tasarim, ensure_ascii=False, indent=2)
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Önce aynı kodda şablon var mı kontrol et
        cursor.execute("""
            SELECT id FROM tanim.etiket_sablonlari
            WHERE sablon_kodu = ? AND aktif_mi = 1
        """, ('ATLAS_DIKEY_50x100',))

        existing = cursor.fetchone()

        if existing:
            print("Atlas sablonu zaten mevcut!")
            print(f"   Mevcut ID: {existing[0]}")

            cevap = input("   Guncellemek ister misiniz? (E/H): ")
            if cevap.upper() == 'E':
                cursor.execute("""
                    UPDATE tanim.etiket_sablonlari
                    SET sablon_adi = ?,
                        aciklama = ?,
                        genislik_mm = ?,
                        yukseklik_mm = ?,
                        tasarim_json = ?,
                        guncelleme_tarihi = ?
                    WHERE id = ?
                """, (
                    'Atlas Kataforez Dikey Etiket',
                    'Atlas Kataforez için özel dikey etiket tasarımı (50x100mm). Logo, ürün resmi, stok kodu, müşteri, tip, miktar, palet, LOT bilgileri ve barkod içerir.',
                    50,
                    100,
                    tasarim_json,
                    datetime.now(),
                    existing[0]
                ))
                conn.commit()
                print("Sablon guncellendi!")
            else:
                print("Islem iptal edildi.")
                return

        else:
            # Yeni şablon ekle
            cursor.execute("""
                INSERT INTO tanim.etiket_sablonlari (
                    sablon_kodu, sablon_adi, sablon_tipi, aciklama,
                    genislik_mm, yukseklik_mm, sayfa_sutun, sayfa_satir,
                    tasarim_json, varsayilan_mi, aktif_mi,
                    olusturma_tarihi, guncelleme_tarihi
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'ATLAS_DIKEY_50x100',
                'Atlas Kataforez Dikey Etiket',
                'PALET',
                'Atlas Kataforez için özel dikey etiket tasarımı (50x100mm). Logo, ürün resmi, stok kodu, müşteri, tip, miktar, palet, LOT bilgileri ve barkod içerir.',
                50,
                100,
                1,
                1,
                tasarim_json,
                0,
                1,
                datetime.now(),
                datetime.now()
            ))

            conn.commit()

            # Eklenen şablonu göster
            cursor.execute("""
                SELECT id, sablon_kodu, sablon_adi, sablon_tipi
                FROM tanim.etiket_sablonlari
                WHERE sablon_kodu = ?
            """, ('ATLAS_DIKEY_50x100',))

            row = cursor.fetchone()
            if row:
                print("=" * 70)
                print("BASARILI! Atlas Kataforez sablonu eklendi!")
                print("=" * 70)
                print(f"   ID:           {row[0]}")
                print(f"   Kod:          {row[1]}")
                print(f"   Ad:           {row[2]}")
                print(f"   Tip:          {row[3]}")
                print(f"   Boyut:        50mm x 100mm (Dikey)")
                print()

    except Exception as e:
        print(f"HATA: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            try: conn.close()
            except Exception: pass


if __name__ == '__main__':
    print("=" * 70)
    print("🏷️  ATLAS KATAFOREZ - DİKEY ETİKET ŞABLONU EKLEME")
    print("=" * 70)
    print()
    print("Bu script, Atlas Kataforez için özel dikey etiket şablonunu")
    print("veritabanına ekleyecek.")
    print()
    print("Şablon Özellikleri:")
    print("  • Boyut: 50mm x 100mm (Dikey)")
    print("  • Atlas logosu")
    print("  • Ürün resmi (52mm yükseklik)")
    print("  • Stok kodu (çerçeveli)")
    print("  • Müşteri bilgisi")
    print("  • TİP alanı (Kaplama tipi)")
    print("  • Miktar ve birim")
    print("  • Palet numarası")
    print("  • LOT numarası (çerçeveli)")
    print("  • QR kod (lot_no)")
    print("  • Tarih")
    print()
    
    cevap = input("Devam etmek istiyor musunuz? (E/H): ")
    
    if cevap.upper() == 'E':
        atlas_sablon_ekle()
    else:
        print("İşlem iptal edildi.")
