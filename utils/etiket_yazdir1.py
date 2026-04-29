# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Etiket Yazdırma Modülü
Giriş irsaliyesi için palet bölme ve tanım etiketi oluşturma
Godex yazıcı desteği (EZPL/ZPL)
"""
import os
import subprocess
import tempfile
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import mm
from reportlab.lib.units import mm as mm_unit
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.graphics.barcode import code128

# Etiket boyutu (100x50mm)
ETIKET_GENISLIK = 100 * mm_unit
ETIKET_YUKSEKLIK = 50 * mm_unit

# NAS resim yolu (config.json'dan)
from config import NAS_PATHS
NAS_IMAGE_PATH = NAS_PATHS["image_path"]

# ============================================================================
# GODEX YAZICI AYARLARI
# ============================================================================

# Varsayılan Godex yazıcı adı (Windows'ta paylaşılan yazıcı adı)
GODEX_PRINTER_NAME = "GODEX G500"  # Windows yazıcı adı

# Etiket boyutları (mm cinsinden - Godex için)
GODEX_ETIKET_GENISLIK_MM = 100
GODEX_ETIKET_YUKSEKLIK_MM = 50

# DPI ayarı (Godex G500 = 203 DPI, G530 = 300 DPI)
GODEX_DPI = 203

# mm'yi dot'a çevir
def mm_to_dots(mm_val: float, dpi: int = GODEX_DPI) -> int:
    """mm değerini yazıcı dot değerine çevir"""
    return int(mm_val * dpi / 25.4)


def lot_no_olustur(tarih: datetime, sira: int, palet_no: int = None) -> str:
    """
    Lot numarası oluştur
    
    Format:
        Ana lot: LOT-YYMM-SSSS (örn: LOT-2501-0001)
        Palet lot: LOT-YYMM-SSSS-PP (örn: LOT-2501-0001-01)
    """
    yil_ay = tarih.strftime("%y%m")
    
    if palet_no is None:
        # Ana lot
        return f"LOT-{yil_ay}-{sira:04d}"
    else:
        # Palet lot
        return f"LOT-{yil_ay}-{sira:04d}-{palet_no:02d}"


def urun_resmi_bul(stok_kodu: str) -> str:
    """NAS'tan ürün resmini bul"""
    extensions = ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG']
    
    for ext in extensions:
        path = os.path.join(NAS_IMAGE_PATH, f"{stok_kodu}{ext}")
        if os.path.exists(path):
            return path
    
    return None


def etiket_pdf_olustur(
    output_path: str,
    stok_kodu: str,
    stok_adi: str,
    musteri: str,
    kaplama: str,
    toplam_miktar: float,
    birim: str,
    palet_sayisi: int,
    irsaliye_no: str,
    tarih: datetime,
    lot_sira: int = 1
) -> list:
    """
    Palet etiketleri PDF'i oluştur
    
    Returns:
        list: Oluşturulan lot numaraları listesi
    """
    
    # Sayfa boyutu: A4'e 2x5 = 10 etiket sığar (gerçek uygulamada)
    # Şimdilik her etiket ayrı sayfa
    
    c = canvas.Canvas(output_path, pagesize=(ETIKET_GENISLIK, ETIKET_YUKSEKLIK))
    
    # Ürün resmi
    resim_path = urun_resmi_bul(stok_kodu)
    
    # Her palet için miktar
    palet_miktar = toplam_miktar / palet_sayisi
    
    lot_numaralari = []
    
    for palet_no in range(1, palet_sayisi + 1):
        # Lot numarası
        lot_no = lot_no_olustur(tarih, lot_sira, palet_no)
        lot_numaralari.append(lot_no)
        
        # Etiket çiz
        _etiket_ciz(
            c=c,
            stok_kodu=stok_kodu,
            stok_adi=stok_adi,
            musteri=musteri,
            kaplama=kaplama,
            miktar=palet_miktar,
            birim=birim,
            palet_no=palet_no,
            toplam_palet=palet_sayisi,
            lot_no=lot_no,
            irsaliye_no=irsaliye_no,
            tarih=tarih,
            resim_path=resim_path
        )
        
        # Sonraki sayfa (son değilse)
        if palet_no < palet_sayisi:
            c.showPage()
    
    c.save()
    return lot_numaralari


def _etiket_ciz(
    c: canvas.Canvas,
    stok_kodu: str,
    stok_adi: str,
    musteri: str,
    kaplama: str,
    miktar: float,
    birim: str,
    palet_no: int,
    toplam_palet: int,
    lot_no: str,
    irsaliye_no: str,
    tarih: datetime,
    resim_path: str = None
):
    """Tek bir etiket çiz"""
    
    # Koordinatlar (sol alt köşe 0,0)
    margin = 3 * mm_unit
    
    # ===== ÜST KISIM: Logo ve İrsaliye No =====
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, ETIKET_YUKSEKLIK - 6 * mm_unit, "ATMO MANUFACTURING")
    
    c.setFont("Helvetica", 7)
    c.drawRightString(ETIKET_GENISLIK - margin, ETIKET_YUKSEKLIK - 6 * mm_unit, irsaliye_no)
    
    # Çizgi
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.line(margin, ETIKET_YUKSEKLIK - 8 * mm_unit, ETIKET_GENISLIK - margin, ETIKET_YUKSEKLIK - 8 * mm_unit)
    
    # ===== SOL KISIM: Ürün Resmi =====
    resim_x = margin
    resim_y = 14 * mm_unit
    resim_w = 22 * mm_unit
    resim_h = 28 * mm_unit
    
    if resim_path and os.path.exists(resim_path):
        try:
            c.drawImage(resim_path, resim_x, resim_y, width=resim_w, height=resim_h, preserveAspectRatio=True, anchor='c')
        except Exception:
            # Resim yüklenemezse boş kutu
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(resim_x, resim_y, resim_w, resim_h)
            c.setFont("Helvetica", 6)
            c.drawCentredString(resim_x + resim_w/2, resim_y + resim_h/2, "Resim Yok")
    else:
        # Boş kutu
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(resim_x, resim_y, resim_w, resim_h)
        c.setFont("Helvetica", 6)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(resim_x + resim_w/2, resim_y + resim_h/2, "Resim Yok")
        c.setFillColorRGB(0, 0, 0)
    
    # ===== SAĞ KISIM: Ürün Bilgileri =====
    info_x = 28 * mm_unit
    info_y = ETIKET_YUKSEKLIK - 12 * mm_unit
    
    # Stok Kodu (büyük)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(info_x, info_y, stok_kodu[:20])
    
    # Stok Adı
    info_y -= 5 * mm_unit
    c.setFont("Helvetica", 8)
    # Uzun isimleri kısalt
    stok_adi_kisalt = stok_adi[:35] + "..." if len(stok_adi) > 35 else stok_adi
    c.drawString(info_x, info_y, stok_adi_kisalt)
    
    # Müşteri
    info_y -= 4 * mm_unit
    c.setFont("Helvetica", 7)
    musteri_kisalt = musteri[:30] + "..." if len(musteri) > 30 else musteri
    c.drawString(info_x, info_y, f"MÜŞTERİ: {musteri_kisalt}")
    
    # Kaplama
    info_y -= 3.5 * mm_unit
    if kaplama:
        c.drawString(info_x, info_y, f"KAPLAMA: {kaplama}")
    
    # ===== ORTA KISIM: Miktar ve Palet =====
    info_y -= 5 * mm_unit
    c.setFont("Helvetica-Bold", 9)
    c.drawString(info_x, info_y, f"MİKTAR: {miktar:,.0f} {birim}")
    
    # Palet bilgisi
    c.drawString(info_x + 45 * mm_unit, info_y, f"PALET: {palet_no:02d}/{toplam_palet:02d}")
    
    # Lot No
    info_y -= 4 * mm_unit
    c.setFont("Helvetica-Bold", 8)
    c.drawString(info_x, info_y, f"LOT: {lot_no}")
    
    # ===== ALT KISIM: Barkod =====
    barcode_y = 2.5 * mm_unit
    barcode_x = margin
    
    # Code128 barkod
    try:
        barcode = code128.Code128(lot_no, barWidth=0.4 * mm_unit, barHeight=8 * mm_unit)
        barcode.drawOn(c, barcode_x, barcode_y)
    except Exception:
        # Barkod oluşturulamazsa metin yaz
        c.setFont("Helvetica", 8)
        c.drawString(barcode_x, barcode_y + 4 * mm_unit, f"*{lot_no}*")
    
    # Tarih (sağ alt)
    c.setFont("Helvetica", 7)
    tarih_str = tarih.strftime("%d.%m.%Y")
    c.drawRightString(ETIKET_GENISLIK - margin, barcode_y + 2 * mm_unit, f"TARİH: {tarih_str}")


def tek_etiket_pdf_olustur(
    output_path: str,
    etiket: dict,
    etiket_w_mm: float = 100,
    etiket_h_mm: float = 50
) -> str:
    """
    Tanımlanan boyutlarda tek etiket PDF'i oluştur
    
    Args:
        output_path: Çıktı PDF yolu
        etiket: Etiket bilgileri (dict)
        etiket_w_mm: Etiket genişliği (mm)
        etiket_h_mm: Etiket yüksekliği (mm)
    
    Returns:
        str: Oluşturulan PDF yolu
    """
    # Sayfa boyutu = etiket boyutu
    page_w = etiket_w_mm * mm_unit
    page_h = etiket_h_mm * mm_unit
    
    c = canvas.Canvas(output_path, pagesize=(page_w, page_h))
    
    # Etiket içeriğini çiz
    _etiket_icerik_ciz_tam(c, etiket, page_w, page_h)
    
    c.save()
    return output_path


def _etiket_icerik_ciz_tam(c: canvas.Canvas, etiket: dict, page_w: float, page_h: float):
    """Tam sayfa etiket içeriği çiz"""
    
    margin = 3 * mm_unit
    
    # Üst: Logo ve İrsaliye No
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, page_h - 6 * mm_unit, "ATMO MANUFACTURING")
    
    c.setFont("Helvetica", 7)
    c.drawRightString(page_w - margin, page_h - 6 * mm_unit, etiket.get('irsaliye_no', ''))
    
    # Çizgi
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.line(margin, page_h - 8 * mm_unit, page_w - margin, page_h - 8 * mm_unit)
    
    # Sol: Resim
    resim_x = margin
    resim_y = 14 * mm_unit
    resim_w = 22 * mm_unit
    resim_h = 28 * mm_unit
    
    resim_path = etiket.get('resim_path')
    if resim_path and os.path.exists(resim_path):
        try:
            c.drawImage(resim_path, resim_x, resim_y, width=resim_w, height=resim_h, 
                       preserveAspectRatio=True, anchor='c')
        except Exception:
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(resim_x, resim_y, resim_w, resim_h)
    else:
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(resim_x, resim_y, resim_w, resim_h)
    
    # Sağ: Bilgiler
    info_x = 28 * mm_unit
    info_y = page_h - 12 * mm_unit
    
    # Stok Kodu
    c.setFont("Helvetica-Bold", 11)
    c.drawString(info_x, info_y, str(etiket.get('stok_kodu', ''))[:20])
    
    # Stok Adı
    info_y -= 5 * mm_unit
    c.setFont("Helvetica", 8)
    stok_adi = str(etiket.get('stok_adi', ''))[:35]
    c.drawString(info_x, info_y, stok_adi)
    
    # Müşteri
    info_y -= 4 * mm_unit
    c.setFont("Helvetica", 7)
    musteri = str(etiket.get('musteri', ''))[:30]
    c.drawString(info_x, info_y, f"MÜŞTERİ: {musteri}")
    
    # Kaplama
    info_y -= 3.5 * mm_unit
    kaplama = etiket.get('kaplama', '')
    if kaplama:
        c.drawString(info_x, info_y, f"KAPLAMA: {kaplama}")
    
    # Miktar ve Palet
    info_y -= 5 * mm_unit
    c.setFont("Helvetica-Bold", 9)
    miktar = etiket.get('miktar', 0)
    birim = etiket.get('birim', 'ADET')
    c.drawString(info_x, info_y, f"MİKTAR: {miktar:,.0f} {birim}")
    
    palet_no = etiket.get('palet_no', 1)
    toplam_palet = etiket.get('toplam_palet', 1)
    c.drawString(info_x + 45 * mm_unit, info_y, f"PALET: {palet_no:02d}/{toplam_palet:02d}")
    
    # Lot No
    info_y -= 4 * mm_unit
    c.setFont("Helvetica-Bold", 8)
    c.drawString(info_x, info_y, f"LOT: {etiket.get('lot_no', '')}")
    
    # Barkod
    barcode_y = 2.5 * mm_unit
    barcode_x = margin
    
    try:
        lot_no = etiket.get('lot_no', '')
        if lot_no:
            barcode = code128.Code128(lot_no, barWidth=0.4 * mm_unit, barHeight=8 * mm_unit)
            barcode.drawOn(c, barcode_x, barcode_y)
    except Exception:
        c.setFont("Helvetica", 8)
        c.drawString(barcode_x, barcode_y + 4 * mm_unit, f"*{etiket.get('lot_no', '')}*")
    
    # Tarih
    c.setFont("Helvetica", 7)
    tarih = etiket.get('tarih')
    if tarih:
        tarih_str = tarih.strftime("%d.%m.%Y") if hasattr(tarih, 'strftime') else str(tarih)[:10]
        c.drawRightString(page_w - margin, barcode_y + 2 * mm_unit, f"TARİH: {tarih_str}")


def a4_etiket_pdf_olustur(
    output_path: str,
    etiketler: list,
    etiket_per_sayfa: int = 10
) -> str:
    """
    A4 kağıda çoklu etiket yerleştir (2 sütun x 5 satır = 10 etiket)
    
    Args:
        output_path: Çıktı PDF yolu
        etiketler: Etiket bilgileri listesi (dict)
        etiket_per_sayfa: Sayfa başına etiket sayısı
    
    Returns:
        str: Oluşturulan PDF yolu
    """
    from reportlab.lib.pagesizes import A4
    
    a4_width, a4_height = A4
    
    # 2 sütun, 5 satır yerleşim
    sutun_sayisi = 2
    satir_sayisi = 5
    
    # Etiket boyutları
    etiket_w = 100 * mm_unit
    etiket_h = 50 * mm_unit
    
    # Kenar boşlukları (A4 ortala)
    margin_x = (a4_width - (sutun_sayisi * etiket_w)) / 2
    margin_y = (a4_height - (satir_sayisi * etiket_h)) / 2
    
    c = canvas.Canvas(output_path, pagesize=A4)
    
    etiket_index = 0
    
    while etiket_index < len(etiketler):
        # Her sayfa için
        for satir in range(satir_sayisi):
            for sutun in range(sutun_sayisi):
                if etiket_index >= len(etiketler):
                    break
                
                etiket = etiketler[etiket_index]
                
                # Etiket pozisyonu
                x = margin_x + (sutun * etiket_w)
                y = a4_height - margin_y - ((satir + 1) * etiket_h)
                
                # Etiket çerçevesi (kesim çizgisi)
                c.setStrokeColorRGB(0.8, 0.8, 0.8)
                c.setDash(1, 2)
                c.rect(x, y, etiket_w, etiket_h)
                c.setDash()
                
                # Etiket içeriği
                c.saveState()
                c.translate(x, y)
                
                _etiket_icerik_ciz(c, etiket)
                
                c.restoreState()
                
                etiket_index += 1
        
        # Sonraki sayfa (daha etiket varsa)
        if etiket_index < len(etiketler):
            c.showPage()
    
    c.save()
    return output_path


def _etiket_icerik_ciz(c: canvas.Canvas, etiket: dict):
    """Etiket içeriğini çiz (translate edilmiş canvas'a)"""
    
    margin = 3 * mm_unit
    
    # Üst: Logo ve İrsaliye No
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin, ETIKET_YUKSEKLIK - 5 * mm_unit, "ATMO MANUFACTURING")
    
    c.setFont("Helvetica", 6)
    c.drawRightString(ETIKET_GENISLIK - margin, ETIKET_YUKSEKLIK - 5 * mm_unit, etiket.get('irsaliye_no', ''))
    
    # Çizgi
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.line(margin, ETIKET_YUKSEKLIK - 7 * mm_unit, ETIKET_GENISLIK - margin, ETIKET_YUKSEKLIK - 7 * mm_unit)
    
    # Sol: Resim
    resim_x = margin
    resim_y = 12 * mm_unit
    resim_w = 20 * mm_unit
    resim_h = 26 * mm_unit
    
    resim_path = etiket.get('resim_path')
    if resim_path and os.path.exists(resim_path):
        try:
            c.drawImage(resim_path, resim_x, resim_y, width=resim_w, height=resim_h, 
                       preserveAspectRatio=True, anchor='c')
        except Exception:
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(resim_x, resim_y, resim_w, resim_h)
    else:
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(resim_x, resim_y, resim_w, resim_h)
    
    # Sağ: Bilgiler
    info_x = 26 * mm_unit
    info_y = ETIKET_YUKSEKLIK - 11 * mm_unit
    
    # Stok Kodu
    c.setFont("Helvetica-Bold", 10)
    c.drawString(info_x, info_y, str(etiket.get('stok_kodu', ''))[:18])
    
    # Stok Adı
    info_y -= 4 * mm_unit
    c.setFont("Helvetica", 7)
    stok_adi = str(etiket.get('stok_adi', ''))[:32]
    c.drawString(info_x, info_y, stok_adi)
    
    # Müşteri
    info_y -= 3.5 * mm_unit
    c.setFont("Helvetica", 6)
    musteri = str(etiket.get('musteri', ''))[:28]
    c.drawString(info_x, info_y, f"MÜŞ: {musteri}")
    
    # Kaplama
    info_y -= 3 * mm_unit
    kaplama = etiket.get('kaplama', '')
    if kaplama:
        c.drawString(info_x, info_y, f"KAP: {kaplama}")
    
    # Miktar ve Palet
    info_y -= 4 * mm_unit
    c.setFont("Helvetica-Bold", 8)
    miktar = etiket.get('miktar', 0)
    birim = etiket.get('birim', 'ADET')
    c.drawString(info_x, info_y, f"MİKTAR: {miktar:,.0f} {birim}")
    
    palet_no = etiket.get('palet_no', 1)
    toplam_palet = etiket.get('toplam_palet', 1)
    c.drawString(info_x + 40 * mm_unit, info_y, f"P: {palet_no:02d}/{toplam_palet:02d}")
    
    # Lot
    info_y -= 3.5 * mm_unit
    lot_no = etiket.get('lot_no', '')
    c.drawString(info_x, info_y, f"LOT: {lot_no}")
    
    # Barkod
    try:
        barcode = code128.Code128(lot_no, barWidth=0.35 * mm_unit, barHeight=7 * mm_unit)
        barcode.drawOn(c, margin, 2 * mm_unit)
    except Exception:
        pass
    
    # Tarih
    c.setFont("Helvetica", 6)
    tarih = etiket.get('tarih')
    if tarih:
        tarih_str = tarih.strftime("%d.%m.%Y") if hasattr(tarih, 'strftime') else str(tarih)[:10]
        c.drawRightString(ETIKET_GENISLIK - margin, 3 * mm_unit, tarih_str)


# Test
if __name__ == "__main__":
    from datetime import datetime
    
    # Test etiketi
    etiketler = []
    for i in range(1, 11):
        etiketler.append({
            'stok_kodu': '44001500',
            'stok_adi': 'BJA YAN BAŞLIK',
            'musteri': 'TEKNİK MALZEME TİC.SAN.A.Ş.',
            'kaplama': 'KATAFOREZ',
            'miktar': 720,
            'birim': 'ADET',
            'palet_no': i,
            'toplam_palet': 10,
            'lot_no': f'L-250111-0001-{i:02d}',
            'irsaliye_no': 'GRS-202501-0001',
            'tarih': datetime.now(),
            'resim_path': None
        })
    
    a4_etiket_pdf_olustur("test_etiketler.pdf", etiketler)
    print("Test PDF oluşturuldu: test_etiketler.pdf")


# ============================================================================
# ŞABLON DESTEKLİ ETİKET FONKSİYONLARI
# ============================================================================

def sablon_bilgilerini_al(sablon_id: int) -> dict:
    """
    Veritabanından şablon bilgilerini ve elementlerini al
    Önce tasarim_json'dan okur, yoksa etiket_elementleri tablosundan okur
    
    Args:
        sablon_id: Şablon ID'si
    
    Returns:
        dict: Şablon bilgileri ve elementleri veya None
    """
    try:
        from core.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Şablon ana bilgileri
        cursor.execute("""
            SELECT id, sablon_kodu, sablon_adi, sablon_tipi, genislik_mm, yukseklik_mm,
                   sayfa_sutun, sayfa_satir, kenar_bosluk_mm, tasarim_json
            FROM tanim.etiket_sablonlari
            WHERE id = ? AND aktif_mi = 1
        """, (sablon_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        sablon = {
            'id': row[0],
            'sablon_kodu': row[1],
            'sablon_adi': row[2],
            'sablon_tipi': row[3],
            'genislik_mm': float(row[4]) if row[4] else 100,
            'yukseklik_mm': float(row[5]) if row[5] else 50,
            'sayfa_sutun': int(row[6]) if row[6] else 1,  # NULL ise 1 (tek etiket)
            'sayfa_satir': int(row[7]) if row[7] else 1,  # NULL ise 1 (tek etiket)
            'kenar_bosluk_mm': float(row[8]) if row[8] else 5,
            'tasarim_json': row[9],
            'elementler': []
        }
        
        print(f"DEBUG Şablon: {sablon['sablon_adi']}, boyut={sablon['genislik_mm']}x{sablon['yukseklik_mm']}mm, "
              f"sutun={sablon['sayfa_sutun']}, satir={sablon['sayfa_satir']}")
        
        # Önce tasarim_json'dan elementleri yükle
        if sablon['tasarim_json']:
            try:
                import json
                tasarim = json.loads(sablon['tasarim_json'])
                json_elements = tasarim.get('elements', [])
                
                if json_elements:
                    print(f"JSON'dan {len(json_elements)} element yükleniyor...")
                    for idx, elem in enumerate(json_elements):
                        element = _json_element_to_db_format(elem, idx)
                        if element:
                            sablon['elementler'].append(element)
            except Exception as e:
                print(f"JSON parse hatası: {e}, etiket_elementleri tablosuna bakılıyor...")
        
        # JSON'da element yoksa veya hata olduysa, etiket_elementleri tablosundan oku
        if not sablon['elementler']:
            cursor.execute("""
                SELECT id, element_tipi, element_adi, x_mm, y_mm, genislik_mm, yukseklik_mm,
                       font_adi, font_boyut, font_kalin, font_italik, metin_hiza,
                       veri_alani, sabit_metin, format_pattern, barkod_tipi, 
                       barkod_yukseklik_mm, barkod_metin_goster
                FROM tanim.etiket_elementleri
                WHERE sablon_id = ? AND gorunur_mu = 1
                ORDER BY sira_no
            """, (sablon_id,))
            
            for elem_row in cursor.fetchall():
                element = {
                    'id': elem_row[0],
                    'element_tipi': elem_row[1],  # TEXT, BARCODE, IMAGE, LINE, RECTANGLE
                    'element_adi': elem_row[2],
                    'x_mm': float(elem_row[3]) if elem_row[3] else 0,
                    'y_mm': float(elem_row[4]) if elem_row[4] else 0,
                    'genislik_mm': float(elem_row[5]) if elem_row[5] else None,
                    'yukseklik_mm': float(elem_row[6]) if elem_row[6] else None,
                    'font_adi': elem_row[7] or 'Helvetica',
                    'font_boyut': elem_row[8] or 10,
                    'font_kalin': elem_row[9] or False,
                    'font_italik': elem_row[10] or False,
                    'metin_hiza': elem_row[11] or 'LEFT',
                    'veri_alani': elem_row[12],  # stok_kodu, stok_adi, lot_no, miktar, vs.
                    'sabit_metin': elem_row[13],
                    'format_pattern': elem_row[14],
                    'barkod_tipi': elem_row[15] or 'CODE128',
                    'barkod_yukseklik_mm': float(elem_row[16]) if elem_row[16] else 8,
                    'barkod_metin_goster': elem_row[17] if elem_row[17] is not None else True
                }
                sablon['elementler'].append(element)
        
        conn.close()
        print(f"Şablon yüklendi: {sablon['sablon_adi']}, {len(sablon['elementler'])} element")
        return sablon
        
    except Exception as e:
        print(f"Şablon bilgisi alma hatası: {e}")
        import traceback
        traceback.print_exc()
        return None


def _json_element_to_db_format(json_elem: dict, sira: int) -> dict:
    """
    JSON formatındaki elementi veritabanı formatına çevir
    
    Args:
        json_elem: JSON'dan gelen element
        sira: Sıra numarası
    
    Returns:
        dict: Veritabanı formatında element
    """
    elem_type = json_elem.get('type', 'TEXT').upper()
    
    # Temel alanlar
    element = {
        'id': sira,
        'element_tipi': elem_type,
        'element_adi': f"{elem_type}_{sira}",
        'x_mm': float(json_elem.get('x', json_elem.get('x_mm', 0))),
        'y_mm': float(json_elem.get('y', json_elem.get('y_mm', 0))),
        'genislik_mm': None,
        'yukseklik_mm': None,
        'font_adi': 'Helvetica',
        'font_boyut': 10,
        'font_kalin': False,
        'font_italik': False,
        'metin_hiza': 'LEFT',
        'veri_alani': None,
        'sabit_metin': None,
        'format_pattern': None,
        'barkod_tipi': 'CODE128',
        'barkod_yukseklik_mm': 8,
        'barkod_metin_goster': True
    }
    
    if elem_type == 'TEXT':
        text = json_elem.get('text', '')
        # {field} formatında ise veri alanı, değilse sabit metin
        if text.startswith('{') and text.endswith('}'):
            element['veri_alani'] = text[1:-1]  # Süslü parantezleri kaldır
        else:
            element['sabit_metin'] = text
        
        font = json_elem.get('font', 'Helvetica')
        if '-Bold' in font:
            element['font_adi'] = font.replace('-Bold', '')
            element['font_kalin'] = True
        else:
            element['font_adi'] = font
        
        element['font_boyut'] = json_elem.get('size', 10)
    
    elif elem_type == 'BARCODE':
        element['element_tipi'] = 'BARCODE'
        element['genislik_mm'] = json_elem.get('width', 40)
        element['yukseklik_mm'] = json_elem.get('height', 8)
        element['barkod_yukseklik_mm'] = json_elem.get('height', 8)
        element['barkod_tipi'] = json_elem.get('barcode_type', 'CODE128')
        
        field = json_elem.get('field', 'lot_no')
        if field.startswith('{') and field.endswith('}'):
            field = field[1:-1]
        element['veri_alani'] = field
    
    elif elem_type == 'IMAGE':
        element['element_tipi'] = 'IMAGE'
        element['genislik_mm'] = json_elem.get('width', 20)
        element['yukseklik_mm'] = json_elem.get('height', 20)
        element['veri_alani'] = json_elem.get('field', 'resim_path')
    
    elif elem_type == 'LINE':
        element['element_tipi'] = 'LINE'
        x2 = json_elem.get('x2', json_elem.get('x', 0) + 50)
        y2 = json_elem.get('y2', json_elem.get('y', 0))
        element['genislik_mm'] = x2 - element['x_mm']
        element['yukseklik_mm'] = y2 - element['y_mm']
    
    elif elem_type == 'RECT':
        element['element_tipi'] = 'RECTANGLE'
        element['genislik_mm'] = json_elem.get('width', 30)
        element['yukseklik_mm'] = json_elem.get('height', 15)
    
    return element


def _veri_alani_deger_al(element: dict, etiket: dict) -> str:
    """
    Element için veri alanından değeri al veya sabit metindeki placeholder'ları çöz
    
    Args:
        element: Element tanımı
        etiket: Etiket verileri
    
    Returns:
        str: Formatlanmış değer
    """
    # Veri alanı eşleştirmesi
    alan_map = {
        'stok_kodu': str(etiket.get('stok_kodu', '')),
        'stok_adi': str(etiket.get('stok_adi', '')),
        'musteri': str(etiket.get('musteri', '')),
        'cari_unvani': str(etiket.get('musteri', '')),
        'kaplama': str(etiket.get('kaplama', '')),
        'kaplama_tipi': str(etiket.get('kaplama', '')),
        'miktar': f"{etiket.get('miktar', 0):,.0f}",
        'birim': str(etiket.get('birim', 'ADET')),
        'miktar_birim': f"{etiket.get('miktar', 0):,.0f} {etiket.get('birim', 'ADET')}",
        'lot_no': str(etiket.get('lot_no', '')),
        'parent_lot_no': str(etiket.get('parent_lot_no', '')),
        'ana_lot': str(etiket.get('parent_lot_no', '')),
        'palet_no': str(etiket.get('palet_no', '')),
        'toplam_palet': str(etiket.get('toplam_palet', '')),
        'palet_bilgi': f"{etiket.get('palet_no', '')}/{etiket.get('toplam_palet', '')}",
        'palet_info': f"P: {etiket.get('palet_no', 0):02d}/{etiket.get('toplam_palet', 0):02d}",
        'irsaliye_no': str(etiket.get('irsaliye_no', '')),
        'tarih': etiket.get('tarih').strftime('%d.%m.%Y') if etiket.get('tarih') and hasattr(etiket.get('tarih'), 'strftime') else str(etiket.get('tarih', ''))[:10],
        'tarih_saat': etiket.get('tarih').strftime('%d.%m.%Y %H:%M') if etiket.get('tarih') and hasattr(etiket.get('tarih'), 'strftime') else '',
        'firma_adi': 'ATMO MANUFACTURING',
        'logo': 'ATMO MANUFACTURING',
    }
    
    # Sabit metin varsa, içindeki {placeholder}'ları çöz
    sabit_metin = element.get('sabit_metin')
    if sabit_metin:
        sonuc = sabit_metin
        # Tüm {field} formatındaki placeholder'ları değiştir
        for alan, deger in alan_map.items():
            sonuc = sonuc.replace(f'{{{alan}}}', str(deger))
        return sonuc
    
    # Veri alanı varsa doğrudan değeri döndür
    veri_alani = element.get('veri_alani')
    if veri_alani:
        deger = alan_map.get(veri_alani, '')
        
        # Format pattern varsa uygula
        format_pattern = element.get('format_pattern')
        if format_pattern and deger:
            try:
                deger = format_pattern.replace('{value}', str(deger))
                deger = format_pattern.replace('{deger}', str(deger))
            except Exception:
                pass
        
        return str(deger)
    
    return ''


def sablon_ile_etiket_pdf_olustur(output_path: str, etiketler: list, sablon_id: int):
    """
    Veritabanındaki şablon tanımına göre etiket PDF'i oluştur
    
    Args:
        output_path: Çıktı PDF dosya yolu
        etiketler: Etiket verileri listesi
        sablon_id: Şablon ID'si
    """
    from reportlab.lib.pagesizes import A4
    
    print(f"\n{'='*50}")
    print(f"ETIKET PDF OLUSTURULUYOR")
    print(f"Etiket sayısı: {len(etiketler)}")
    print(f"Şablon ID: {sablon_id}")
    print(f"{'='*50}")
    
    # Şablon bilgilerini al
    sablon = sablon_bilgilerini_al(sablon_id)
    
    if not sablon:
        print(f"UYARI: Şablon ID={sablon_id} bulunamadı, varsayılan A4 şablon kullanılıyor")
        a4_etiket_pdf_olustur(output_path, etiketler)
        return
    
    # Şablon boyutları
    etiket_w_mm = sablon['genislik_mm']
    etiket_h_mm = sablon['yukseklik_mm']
    etiket_w = etiket_w_mm * mm_unit
    etiket_h = etiket_h_mm * mm_unit
    sutun_sayisi = sablon['sayfa_sutun']
    satir_sayisi = sablon['sayfa_satir']
    kenar_bosluk = sablon['kenar_bosluk_mm'] * mm_unit
    
    print(f"Şablon: {sablon['sablon_adi']}")
    print(f"Boyut: {etiket_w_mm}x{etiket_h_mm}mm")
    print(f"Sayfa düzeni: {sutun_sayisi} sütun x {satir_sayisi} satır")
    print(f"Element sayısı: {len(sablon.get('elementler', []))}")
    
    # Tek etiket modu kontrolü: sütun=1 VE satır=1 ise her etiket ayrı sayfada
    tek_etiket_modu = (sutun_sayisi == 1 and satir_sayisi == 1)
    
    if tek_etiket_modu:
        # ==================== TEK ETİKET MODU ====================
        # Sayfa boyutu = etiket boyutu, her etiket ayrı sayfada
        page_w = etiket_w
        page_h = etiket_h
        c = canvas.Canvas(output_path, pagesize=(page_w, page_h))
        
        print(f"\n>>> TEK ETİKET MODU: {etiket_w_mm}x{etiket_h_mm}mm sayfa")
        print(f">>> {len(etiketler)} adet etiket yazdırılacak")
        
        for i, etiket in enumerate(etiketler):
            if i > 0:
                c.showPage()
            
            print(f"  [{i+1}/{len(etiketler)}] Lot: {etiket.get('lot_no')}, Palet: {etiket.get('palet_no')}/{etiket.get('toplam_palet')}")
            
            # Elementi çiz (base_x=0, base_y=0 çünkü sayfa=etiket)
            _sablon_elemanlari_ciz(c, sablon, etiket, 0, 0, etiket_w, etiket_h)
        
        c.save()
        print(f"\n✓ PDF oluşturuldu: {output_path}")
        print(f"✓ Toplam {len(etiketler)} sayfa (etiket)")
        return
    
    # ==================== A4 MODU ====================
    # Birden fazla etiket aynı A4 sayfasında
    a4_width, a4_height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    print(f"\n>>> A4 MODU: {sutun_sayisi}x{satir_sayisi} = {sutun_sayisi*satir_sayisi} etiket/sayfa")
    
    # Kenar boşlukları hesapla
    if kenar_bosluk > 0:
        margin_x = kenar_bosluk
        margin_y = kenar_bosluk
    else:
        # A4 ortala
        margin_x = (a4_width - (sutun_sayisi * etiket_w)) / 2
        margin_y = (a4_height - (satir_sayisi * etiket_h)) / 2
    
    etiket_index = 0
    sayfa_no = 1
    
    while etiket_index < len(etiketler):
        print(f"\n  Sayfa {sayfa_no}:")
        
        for satir in range(satir_sayisi):
            for sutun in range(sutun_sayisi):
                if etiket_index >= len(etiketler):
                    break
                
                etiket = etiketler[etiket_index]
                
                # Etiket pozisyonu (sol üstten başla, aşağı doğru)
                x = margin_x + (sutun * etiket_w)
                y = a4_height - margin_y - ((satir + 1) * etiket_h)
                
                print(f"    [{etiket_index+1}] Satır:{satir+1} Sütun:{sutun+1} - Lot: {etiket.get('lot_no')}")
                
                # Kesim çizgisi
                c.setStrokeColorRGB(0.85, 0.85, 0.85)
                c.setLineWidth(0.5)
                c.setDash(1, 2)
                c.rect(x, y, etiket_w, etiket_h)
                c.setDash()
                
                # Etiket içeriğini çiz
                _sablon_elemanlari_ciz(c, sablon, etiket, x, y, etiket_w, etiket_h)
                
                etiket_index += 1
        
        # Sonraki sayfa
        if etiket_index < len(etiketler):
            c.showPage()
            sayfa_no += 1
    
    c.save()
    print(f"\n✓ PDF oluşturuldu: {output_path}")
    print(f"✓ Toplam {sayfa_no} A4 sayfa, {len(etiketler)} etiket")


def _sablon_elemanlari_ciz(c: canvas.Canvas, sablon: dict, etiket: dict, 
                           base_x: float, base_y: float, etiket_w: float, etiket_h: float):
    """
    Şablon elementlerini çiz
    
    Args:
        c: Canvas
        sablon: Şablon bilgileri
        etiket: Etiket verileri
        base_x, base_y: Etiketin sol alt köşesi
        etiket_w, etiket_h: Etiket boyutları (point)
    """
    
    # Element yoksa varsayılan çizimi yap
    if not sablon.get('elementler'):
        print(f"  > Şablonda element yok, varsayılan etiket çiziliyor")
        _varsayilan_etiket_ciz(c, etiket, base_x, base_y, etiket_w, etiket_h)
        return
    
    for element in sablon['elementler']:
        # Element pozisyonu (şablonda sol üstten tanımlı, PDF'de sol alttan)
        elem_x = base_x + element['x_mm'] * mm_unit
        elem_y = base_y + etiket_h - element['y_mm'] * mm_unit  # Y koordinatı ters çevir
        
        element_tipi = element.get('element_tipi', 'TEXT').upper()
        
        try:
            if element_tipi == 'TEXT':
                _text_element_ciz(c, element, etiket, elem_x, elem_y)
            
            elif element_tipi == 'BARCODE':
                _barcode_element_ciz(c, element, etiket, elem_x, elem_y)
            
            elif element_tipi == 'IMAGE':
                _image_element_ciz(c, element, etiket, elem_x, elem_y)
            
            elif element_tipi == 'LINE':
                _line_element_ciz(c, element, elem_x, elem_y)
            
            elif element_tipi in ('RECTANGLE', 'RECT'):
                _rectangle_element_ciz(c, element, elem_x, elem_y)
                
        except Exception as e:
            print(f"Element çizim hatası ({element.get('element_adi', '?')}): {e}")


def _varsayilan_etiket_ciz(c: canvas.Canvas, etiket: dict, base_x: float, base_y: float, 
                           etiket_w: float, etiket_h: float):
    """
    Varsayılan etiket içeriğini çiz - element tanımlanmamışsa kullanılır
    
    Args:
        c: Canvas
        etiket: Etiket verileri
        base_x, base_y: Etiketin sol alt köşesi
        etiket_w, etiket_h: Etiket boyutları (point)
    """
    margin = 3 * mm_unit
    
    # Üst: Logo ve İrsaliye No
    c.setFont("Helvetica-Bold", 7)
    c.drawString(base_x + margin, base_y + etiket_h - 5 * mm_unit, "ATMO MANUFACTURING")
    
    c.setFont("Helvetica", 6)
    c.drawRightString(base_x + etiket_w - margin, base_y + etiket_h - 5 * mm_unit, 
                      str(etiket.get('irsaliye_no', '')))
    
    # Çizgi
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.line(base_x + margin, base_y + etiket_h - 7 * mm_unit, 
           base_x + etiket_w - margin, base_y + etiket_h - 7 * mm_unit)
    
    # Sol: Resim alanı
    resim_x = base_x + margin
    resim_y = base_y + 12 * mm_unit
    resim_w = 20 * mm_unit
    resim_h = 26 * mm_unit
    
    resim_path = etiket.get('resim_path')
    if resim_path and os.path.exists(resim_path):
        try:
            c.drawImage(resim_path, resim_x, resim_y, width=resim_w, height=resim_h, 
                       preserveAspectRatio=True, anchor='c')
        except Exception:
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(resim_x, resim_y, resim_w, resim_h)
    else:
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(resim_x, resim_y, resim_w, resim_h)
    
    # Sağ: Bilgiler
    info_x = base_x + 26 * mm_unit
    info_y = base_y + etiket_h - 11 * mm_unit
    
    # Stok Kodu
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(info_x, info_y, str(etiket.get('stok_kodu', ''))[:18])
    
    # Stok Adı
    info_y -= 4 * mm_unit
    c.setFont("Helvetica", 7)
    stok_adi = str(etiket.get('stok_adi', ''))[:32]
    c.drawString(info_x, info_y, stok_adi)
    
    # Müşteri
    info_y -= 3.5 * mm_unit
    c.setFont("Helvetica", 6)
    musteri = str(etiket.get('musteri', ''))[:28]
    c.drawString(info_x, info_y, f"MÜŞ: {musteri}")
    
    # Kaplama
    info_y -= 3 * mm_unit
    kaplama = etiket.get('kaplama', '')
    if kaplama:
        c.drawString(info_x, info_y, f"KAP: {kaplama}")
    
    # Miktar ve Palet
    info_y -= 4 * mm_unit
    c.setFont("Helvetica-Bold", 8)
    miktar = etiket.get('miktar', 0)
    birim = etiket.get('birim', 'ADET')
    c.drawString(info_x, info_y, f"MİKTAR: {miktar:,.0f} {birim}")
    
    palet_no = etiket.get('palet_no', 1)
    toplam_palet = etiket.get('toplam_palet', 1)
    c.drawString(info_x + 40 * mm_unit, info_y, f"P: {palet_no:02d}/{toplam_palet:02d}")
    
    # Lot
    info_y -= 3.5 * mm_unit
    lot_no = str(etiket.get('lot_no', ''))
    c.drawString(info_x, info_y, f"LOT: {lot_no}")
    
    # Barkod
    if lot_no:
        try:
            barcode = code128.Code128(lot_no, barWidth=0.35 * mm_unit, barHeight=7 * mm_unit)
            barcode.drawOn(c, base_x + margin, base_y + 2 * mm_unit)
        except Exception as e:
            c.setFont("Helvetica", 6)
            c.drawString(base_x + margin, base_y + 5 * mm_unit, f"*{lot_no}*")
    
    # Tarih
    c.setFont("Helvetica", 6)
    tarih = etiket.get('tarih')
    if tarih:
        tarih_str = tarih.strftime("%d.%m.%Y") if hasattr(tarih, 'strftime') else str(tarih)[:10]
        c.drawRightString(base_x + etiket_w - margin, base_y + 3 * mm_unit, tarih_str)


def _text_element_ciz(c: canvas.Canvas, element: dict, etiket: dict, x: float, y: float):
    """Metin elementi çiz"""
    metin = _veri_alani_deger_al(element, etiket)
    if not metin:
        return
    
    # Font ayarları
    font_adi = element.get('font_adi', 'Helvetica')
    font_boyut = element.get('font_boyut', 10)
    font_kalin = element.get('font_kalin', False)
    
    # Helvetica için Bold varyantı
    if font_kalin and 'Helvetica' in font_adi:
        font_adi = 'Helvetica-Bold'
    elif font_kalin:
        font_adi = font_adi + '-Bold' if '-Bold' not in font_adi else font_adi
    
    try:
        c.setFont(font_adi, font_boyut)
    except Exception:
        c.setFont('Helvetica', font_boyut)
    
    c.setFillColorRGB(0, 0, 0)
    
    # Metin hizalama
    metin_hiza = element.get('metin_hiza', 'LEFT').upper()
    genislik = element.get('genislik_mm')
    
    # Y pozisyonunu font boyutuna göre ayarla
    text_y = y - font_boyut
    
    if metin_hiza == 'CENTER' and genislik:
        text_x = x + (genislik * mm_unit) / 2
        c.drawCentredString(text_x, text_y, metin)
    elif metin_hiza == 'RIGHT' and genislik:
        text_x = x + genislik * mm_unit
        c.drawRightString(text_x, text_y, metin)
    else:
        c.drawString(x, text_y, metin)


def _barcode_element_ciz(c: canvas.Canvas, element: dict, etiket: dict, x: float, y: float):
    """Kod elementi - QR (default) veya Code128"""
    barkod_veri = _veri_alani_deger_al(element, etiket)
    if not barkod_veri:
        return

    kod_tipi = (element.get('barkod_tipi') or 'QR').upper()
    show_text = element.get('barkod_metin_goster', True)

    try:
        if kod_tipi == 'CODE128':
            barkod_yukseklik = element.get('barkod_yukseklik_mm', 8) * mm_unit
            barcode = code128.Code128(
                barkod_veri,
                barWidth=0.35 * mm_unit,
                barHeight=barkod_yukseklik,
            )
            barcode.drawOn(c, x, y - barkod_yukseklik)
        else:
            from reportlab.graphics.barcode import qr
            from reportlab.graphics.shapes import Drawing
            from reportlab.graphics import renderPDF

            w_mm = element.get('genislik_mm', 25)
            h_mm = element.get('yukseklik_mm', 25)
            side_mm = min(w_mm, h_mm)
            side_pt = side_mm * mm_unit

            qr_widget = qr.QrCodeWidget(barkod_veri)
            bounds = qr_widget.getBounds()
            qw = bounds[2] - bounds[0]
            qh = bounds[3] - bounds[1]
            d = Drawing(side_pt, side_pt, transform=[
                side_pt / qw, 0, 0, side_pt / qh, 0, 0
            ])
            d.add(qr_widget)
            renderPDF.draw(d, c, x, y - side_pt)

            if show_text:
                c.setFont('Helvetica', 7)
                c.drawCentredString(x + side_pt / 2, y - side_pt - 8, barkod_veri)
    except Exception as e:
        print(f"Kod oluşturma hatası ({kod_tipi}): {e}")
        c.setFont("Helvetica", 7)
        c.drawString(x, y - 10, f"*{barkod_veri}*")


def _image_element_ciz(c: canvas.Canvas, element: dict, etiket: dict, x: float, y: float):
    """Resim elementi çiz"""
    resim_path = etiket.get('resim_path')
    genislik = (element.get('genislik_mm') or 20) * mm_unit
    yukseklik = (element.get('yukseklik_mm') or 20) * mm_unit
    
    if resim_path and os.path.exists(resim_path):
        try:
            c.drawImage(resim_path, x, y - yukseklik, width=genislik, height=yukseklik,
                       preserveAspectRatio=True, anchor='c')
        except Exception:
            # Resim yüklenemezse boş kutu
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(x, y - yukseklik, genislik, yukseklik)
    else:
        # Boş kutu
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(x, y - yukseklik, genislik, yukseklik)


def _line_element_ciz(c: canvas.Canvas, element: dict, x: float, y: float):
    """Çizgi elementi çiz"""
    genislik = (element.get('genislik_mm') or 0) * mm_unit
    yukseklik = (element.get('yukseklik_mm') or 0) * mm_unit
    
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setLineWidth(0.5)
    c.line(x, y, x + genislik, y - yukseklik)


def _rectangle_element_ciz(c: canvas.Canvas, element: dict, x: float, y: float):
    """Dikdörtgen elementi çiz"""
    genislik = (element.get('genislik_mm') or 10) * mm_unit
    yukseklik = (element.get('yukseklik_mm') or 10) * mm_unit
    
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setLineWidth(0.5)
    c.rect(x, y - yukseklik, genislik, yukseklik)


# ============================================================================
# GODEX YAZICI FONKSİYONLARI (EZPL/ZPL)
# ============================================================================

def get_available_printers() -> list:
    """
    Windows'ta mevcut yazıcıları listele
    
    Returns:
        list: Yazıcı adları listesi
    """
    try:
        import win32print
        printers = []
        for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
            printers.append(printer[2])  # Yazıcı adı
        return printers
    except ImportError:
        # win32print yoksa boş döndür
        print("UYARI: win32print modülü bulunamadı. 'pip install pywin32' ile yükleyin.")
        return []
    except Exception as e:
        print(f"Yazıcı listesi alınamadı: {e}")
        return []


def get_godex_printers() -> list:
    """
    Godex yazıcıları filtrele
    
    Returns:
        list: Godex yazıcı adları
    """
    all_printers = get_available_printers()
    godex_printers = [p for p in all_printers if 'GODEX' in p.upper() or 'G500' in p.upper() or 'G530' in p.upper()]
    return godex_printers


def godex_ezpl_olustur(etiket: dict, etiket_w_mm: int = 100, etiket_h_mm: int = 50) -> str:
    """
    Tek bir etiket için Godex EZPL komutu oluştur
    
    Args:
        etiket: Etiket verileri
        etiket_w_mm: Etiket genişliği (mm)
        etiket_h_mm: Etiket yüksekliği (mm)
    
    Returns:
        str: EZPL komut dizisi
    """
    # Değerleri al
    stok_kodu = str(etiket.get('stok_kodu', ''))[:20]
    stok_adi = str(etiket.get('stok_adi', ''))[:35]
    musteri = str(etiket.get('musteri', ''))[:30]
    kaplama = str(etiket.get('kaplama', ''))[:20]
    miktar = etiket.get('miktar', 0)
    birim = str(etiket.get('birim', 'ADET'))
    palet_no = etiket.get('palet_no', 1)
    toplam_palet = etiket.get('toplam_palet', 1)
    lot_no = str(etiket.get('lot_no', ''))
    irsaliye_no = str(etiket.get('irsaliye_no', ''))
    
    tarih = etiket.get('tarih')
    if tarih and hasattr(tarih, 'strftime'):
        tarih_str = tarih.strftime('%d.%m.%Y')
    else:
        tarih_str = str(tarih)[:10] if tarih else ''
    
    # Dot hesaplamaları (203 DPI için)
    dpi = GODEX_DPI
    w_dots = mm_to_dots(etiket_w_mm, dpi)
    h_dots = mm_to_dots(etiket_h_mm, dpi)
    
    # EZPL komutu oluştur
    ezpl = []
    
    # Başlangıç komutları
    ezpl.append(f"^Q{h_dots},3")  # Etiket yüksekliği
    ezpl.append(f"^W{w_dots}")     # Etiket genişliği
    ezpl.append("^H10")            # Isı ayarı
    ezpl.append("^P1")             # 1 adet yazdır
    ezpl.append("^S3")             # Hız
    ezpl.append("^AT")             # Transfer modu
    ezpl.append("^C1")             # Sürekli mod
    ezpl.append("^R0")             # Referans nokta
    ezpl.append("~Q+0")            # Offset
    ezpl.append("^O0")             # Yön
    ezpl.append("^D0")             # Density
    ezpl.append("^E12")            # Uzunluk
    ezpl.append("~R200")           # Referans ayarı
    ezpl.append("^L")              # Label başlangıcı
    
    # ATMO MANUFACTURING başlık
    ezpl.append(f"AA,{mm_to_dots(3)},{mm_to_dots(3)},1,1,0,0,ATMO MANUFACTURING")
    
    # İrsaliye No (sağ üst)
    ezpl.append(f"AA,{mm_to_dots(70)},{mm_to_dots(3)},1,1,0,0,{irsaliye_no}")
    
    # Çizgi
    ezpl.append(f"LO,{mm_to_dots(3)},{mm_to_dots(8)},{mm_to_dots(94)},1")
    
    # Stok Kodu (büyük font)
    ezpl.append(f"AB,{mm_to_dots(25)},{mm_to_dots(10)},1,1,0,0,{stok_kodu}")
    
    # Stok Adı
    ezpl.append(f"AA,{mm_to_dots(25)},{mm_to_dots(16)},1,1,0,0,{stok_adi}")
    
    # Müşteri
    ezpl.append(f"AA,{mm_to_dots(25)},{mm_to_dots(21)},1,1,0,0,MUS: {musteri}")
    
    # Kaplama
    if kaplama:
        ezpl.append(f"AA,{mm_to_dots(25)},{mm_to_dots(25)},1,1,0,0,KAP: {kaplama}")
    
    # Miktar ve Palet
    ezpl.append(f"AB,{mm_to_dots(25)},{mm_to_dots(30)},1,1,0,0,MIKTAR: {miktar:,.0f} {birim}")
    ezpl.append(f"AB,{mm_to_dots(70)},{mm_to_dots(30)},1,1,0,0,P:{palet_no:02d}/{toplam_palet:02d}")
    
    # Lot No
    ezpl.append(f"AB,{mm_to_dots(25)},{mm_to_dots(36)},1,1,0,0,LOT: {lot_no}")
    
    # QR (Code128 yerine - kullanici talep, 2026-04-29)
    # Godex EZPL QR: W{x},{y},{type},{ECC},{cell_size},{mask},{rotation},{data}
    # type=4 (QR), ECC=1 (L low), cell=5 (~20mm kare)
    ezpl.append(f"W{mm_to_dots(3)},{mm_to_dots(28)},4,1,5,0,0,{lot_no}")

    # Tarih (sağ alt)
    ezpl.append(f"AA,{mm_to_dots(75)},{mm_to_dots(45)},1,1,0,0,{tarih_str}")
    
    # Label sonu
    ezpl.append("E")
    
    return "\n".join(ezpl)


def godex_zpl_olustur(etiket: dict, etiket_w_mm: int = 100, etiket_h_mm: int = 50) -> str:
    """
    Tek bir etiket için ZPL komutu oluştur (Godex ZPL uyumlu modeller için)
    
    Args:
        etiket: Etiket verileri
        etiket_w_mm: Etiket genişliği (mm)
        etiket_h_mm: Etiket yüksekliği (mm)
    
    Returns:
        str: ZPL komut dizisi
    """
    # Değerleri al
    stok_kodu = str(etiket.get('stok_kodu', ''))[:20]
    stok_adi = str(etiket.get('stok_adi', ''))[:35]
    musteri = str(etiket.get('musteri', ''))[:30]
    kaplama = str(etiket.get('kaplama', ''))[:20]
    miktar = etiket.get('miktar', 0)
    birim = str(etiket.get('birim', 'ADET'))
    palet_no = etiket.get('palet_no', 1)
    toplam_palet = etiket.get('toplam_palet', 1)
    lot_no = str(etiket.get('lot_no', ''))
    irsaliye_no = str(etiket.get('irsaliye_no', ''))
    
    tarih = etiket.get('tarih')
    if tarih and hasattr(tarih, 'strftime'):
        tarih_str = tarih.strftime('%d.%m.%Y')
    else:
        tarih_str = str(tarih)[:10] if tarih else ''
    
    # ZPL komutu oluştur
    zpl = []
    
    # Başlangıç
    zpl.append("^XA")  # Label başlangıcı
    zpl.append(f"^PW{mm_to_dots(etiket_w_mm)}")  # Print width
    zpl.append(f"^LL{mm_to_dots(etiket_h_mm)}")  # Label length
    
    # ATMO MANUFACTURING başlık
    zpl.append(f"^FO{mm_to_dots(3)},{mm_to_dots(3)}^A0N,20,20^FDATMO MANUFACTURING^FS")
    
    # İrsaliye No (sağ üst)
    zpl.append(f"^FO{mm_to_dots(70)},{mm_to_dots(3)}^A0N,18,18^FD{irsaliye_no}^FS")
    
    # Çizgi
    zpl.append(f"^FO{mm_to_dots(3)},{mm_to_dots(8)}^GB{mm_to_dots(94)},1,1^FS")
    
    # Stok Kodu (büyük font)
    zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(10)}^A0N,28,28^FD{stok_kodu}^FS")
    
    # Stok Adı
    zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(16)}^A0N,20,20^FD{stok_adi}^FS")
    
    # Müşteri
    zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(21)}^A0N,18,18^FDMUS: {musteri}^FS")
    
    # Kaplama
    if kaplama:
        zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(25)}^A0N,18,18^FDKAP: {kaplama}^FS")
    
    # Miktar
    zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(30)}^A0N,22,22^FDMIKTAR: {miktar:,.0f} {birim}^FS")
    
    # Palet
    zpl.append(f"^FO{mm_to_dots(70)},{mm_to_dots(30)}^A0N,22,22^FDP:{palet_no:02d}/{toplam_palet:02d}^FS")
    
    # Lot No
    zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(36)}^A0N,22,22^FDLOT: {lot_no}^FS")
    
    # QR (Code128 yerine - kullanici talep, 2026-04-29)
    # ZPL QR: ^BQa,b,c -> N=normal, model=2, magnification=5
    # ^FD prefix QA = QR Code, M = mask (0 default)
    zpl.append(f"^FO{mm_to_dots(3)},{mm_to_dots(28)}^BQN,2,5^FDQA,{lot_no}^FS")

    # Tarih (sağ alt)
    zpl.append(f"^FO{mm_to_dots(75)},{mm_to_dots(45)}^A0N,18,18^FD{tarih_str}^FS")
    
    # Label sonu
    zpl.append("^XZ")
    
    return "\n".join(zpl)


def godex_yazdir(etiketler: list, printer_name: str = None, format_type: str = "ZPL") -> bool:
    """
    Etiketleri Godex yazıcıya gönder
    
    Args:
        etiketler: Etiket verileri listesi
        printer_name: Yazıcı adı (None ise varsayılan Godex yazıcı)
        format_type: "ZPL" veya "EZPL"
    
    Returns:
        bool: Başarılı ise True
    """
    try:
        import win32print
        import win32api
        
        # Yazıcı adı belirlenmemişse Godex yazıcı bul
        if not printer_name:
            godex_list = get_godex_printers()
            if godex_list:
                printer_name = godex_list[0]
            else:
                printer_name = GODEX_PRINTER_NAME
        
        print(f"Yazıcı: {printer_name}, Format: {format_type}, Etiket sayısı: {len(etiketler)}")
        
        # Tüm etiketler için komut oluştur
        all_commands = []
        for etiket in etiketler:
            if format_type.upper() == "EZPL":
                cmd = godex_ezpl_olustur(etiket)
            else:
                cmd = godex_zpl_olustur(etiket)
            all_commands.append(cmd)
        
        # Komutları birleştir
        full_command = "\n".join(all_commands)
        
        # Yazıcıya gönder
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Etiket", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, full_command.encode('utf-8'))
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
        
        print(f"✅ {len(etiketler)} etiket yazıcıya gönderildi")
        return True
        
    except ImportError:
        print("HATA: win32print modülü bulunamadı!")
        print("Çözüm: pip install pywin32")
        return False
    except Exception as e:
        print(f"Yazdırma hatası: {e}")
        import traceback
        traceback.print_exc()
        return False


def godex_dosyaya_kaydet(etiketler: list, output_path: str, format_type: str = "ZPL") -> str:
    """
    Godex komutlarını dosyaya kaydet (test veya manuel yazdırma için)
    
    Args:
        etiketler: Etiket verileri listesi
        output_path: Çıktı dosya yolu (.prn veya .txt)
        format_type: "ZPL" veya "EZPL"
    
    Returns:
        str: Kaydedilen dosya yolu
    """
    all_commands = []
    for etiket in etiketler:
        if format_type.upper() == "EZPL":
            cmd = godex_ezpl_olustur(etiket)
        else:
            cmd = godex_zpl_olustur(etiket)
        all_commands.append(cmd)
    
    full_command = "\n".join(all_commands)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_command)
    
    print(f"Godex komutları kaydedildi: {output_path}")
    return output_path


def pdf_yazdir(pdf_path: str, printer_name: str = None) -> bool:
    """
    PDF dosyasını belirtilen yazıcıya gönder
    
    Args:
        pdf_path: PDF dosya yolu
        printer_name: Yazıcı adı (None ise varsayılan)
    
    Returns:
        bool: Başarılı ise True
    """
    try:
        import win32print
        import win32api
        
        if not printer_name:
            printer_name = win32print.GetDefaultPrinter()
        
        # PDF'i varsayılan uygulama ile yazdır
        win32api.ShellExecute(
            0,
            "print",
            pdf_path,
            f'/d:"{printer_name}"',
            ".",
            0
        )
        
        print(f"PDF yazıcıya gönderildi: {printer_name}")
        return True
        
    except ImportError:
        # win32api yoksa subprocess ile dene
        try:
            if printer_name:
                subprocess.run([
                    'rundll32', 'mshtml.dll,PrintHTML', 
                    pdf_path, printer_name
                ], check=True)
            else:
                # Varsayılan uygulama ile aç ve yazdır
                os.startfile(pdf_path, 'print')
            return True
        except Exception as e:
            print(f"PDF yazdırma hatası: {e}")
            return False
    except Exception as e:
        print(f"PDF yazdırma hatası: {e}")
        return False


def yazici_sec_dialog(parent=None) -> str:
    """
    Yazıcı seçim dialogu göster
    
    Args:
        parent: Parent widget (PySide6/PyQt)
    
    Returns:
        str: Seçilen yazıcı adı veya None
    """
    try:
        from PySide6.QtWidgets import QInputDialog
        from PySide6.QtCore import Qt
        
        printers = get_available_printers()
        if not printers:
            return None
        
        # Godex yazıcıları öne al
        godex_printers = [p for p in printers if 'GODEX' in p.upper()]
        other_printers = [p for p in printers if 'GODEX' not in p.upper()]
        sorted_printers = godex_printers + other_printers
        
        printer, ok = QInputDialog.getItem(
            parent,
            "Yazıcı Seç",
            "Yazdırılacak yazıcıyı seçin:",
            sorted_printers,
            0,
            False
        )
        
        if ok and printer:
            return printer
        return None
        
    except ImportError:
        print("PySide6 bulunamadı, ilk Godex yazıcı kullanılacak")
        godex_list = get_godex_printers()
        return godex_list[0] if godex_list else None
