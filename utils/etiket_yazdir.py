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

# Resim DPI düşürme (etiket performansı için)
ETIKET_RESIM_MAX_PX = 300  # Etiket resmi max piksel (genişlik veya yükseklik)

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Etiket boyutu (100x50mm)
ETIKET_GENISLIK = 100 * mm_unit
ETIKET_YUKSEKLIK = 50 * mm_unit

# DİKEY etiket boyutu (50x100mm - Atlas Kataforez için)
DIKEY_ETIKET_GENISLIK = 50 * mm_unit
DIKEY_ETIKET_YUKSEKLIK = 100 * mm_unit

# NAS resim yolu (config.json'dan)
from config import NAS_PATHS
NAS_IMAGE_PATH = NAS_PATHS["image_path"]

# Atlas logo yolu
ATLAS_LOGO_PATH = NAS_PATHS["logo_path"]

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
    """NAS'tan ürün resmini bul ve etiket için DPI düşür"""
    extensions = ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG']

    for ext in extensions:
        path = os.path.join(NAS_IMAGE_PATH, f"{stok_kodu}{ext}")
        if os.path.exists(path):
            return _resim_kucult(path)

    return None


def _resim_kucult(path: str) -> str:
    """Resmi etiket için küçültür (düşük DPI). Küçültülmüş dosyayı temp'e yazar."""
    if not PIL_AVAILABLE:
        return path
    try:
        img = PILImage.open(path)
        w, h = img.size
        if max(w, h) <= ETIKET_RESIM_MAX_PX:
            return path  # Zaten küçük
        ratio = ETIKET_RESIM_MAX_PX / max(w, h)
        new_size = (int(w * ratio), int(h * ratio))
        img = img.resize(new_size, PILImage.LANCZOS)
        # Temp dosyaya kaydet
        tmp = os.path.join(tempfile.gettempdir(), f"nexor_etiket_{os.path.basename(path)}")
        img.save(tmp, quality=75, optimize=True)
        return tmp
    except Exception:
        return path


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

    # Kontrolcü
    kontrolcu = etiket.get('kontrolcu', '')
    if kontrolcu:
        info_y -= 3 * mm_unit
        c.setFont("Helvetica", 6)
        c.drawString(info_x, info_y, f"KONTROL: {str(kontrolcu)[:25]}")

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


def _red_etiket_icerik_ciz(c: canvas.Canvas, etiket: dict):
    """RED etiketi içeriğini çiz - kırmızı çerçeveli, RED damgalı"""

    margin = 3 * mm_unit

    # Kırmızı çerçeve
    c.setStrokeColorRGB(0.93, 0.27, 0.27)
    c.setLineWidth(2)
    c.rect(1 * mm_unit, 1 * mm_unit, ETIKET_GENISLIK - 2 * mm_unit, ETIKET_YUKSEKLIK - 2 * mm_unit)
    c.setLineWidth(0.5)

    # RED damgası (çapraz)
    c.saveState()
    c.setFillColorRGB(0.93, 0.27, 0.27, 0.15)
    c.setFont("Helvetica-Bold", 40)
    c.translate(ETIKET_GENISLIK / 2, ETIKET_YUKSEKLIK / 2)
    c.rotate(30)
    c.drawCentredString(0, -8, "RED")
    c.restoreState()

    # Üst: RED başlığı
    c.setFillColorRGB(0.93, 0.27, 0.27)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(ETIKET_GENISLIK / 2, ETIKET_YUKSEKLIK - 7 * mm_unit, "RED / UYGUNSUZ ÜRÜN")

    c.setStrokeColorRGB(0.93, 0.27, 0.27)
    c.line(margin, ETIKET_YUKSEKLIK - 9 * mm_unit, ETIKET_GENISLIK - margin, ETIKET_YUKSEKLIK - 9 * mm_unit)

    # Bilgiler
    c.setFillColorRGB(0, 0, 0)
    info_y = ETIKET_YUKSEKLIK - 13 * mm_unit
    info_x = margin + 2 * mm_unit

    c.setFont("Helvetica-Bold", 8)
    c.drawString(info_x, info_y, f"Stok: {str(etiket.get('stok_kodu', ''))[:20]}")

    info_y -= 4 * mm_unit
    c.setFont("Helvetica", 7)
    c.drawString(info_x, info_y, f"Ürün: {str(etiket.get('stok_adi', ''))[:30]}")

    info_y -= 3.5 * mm_unit
    c.drawString(info_x, info_y, f"Müşteri: {str(etiket.get('musteri', ''))[:28]}")

    info_y -= 3.5 * mm_unit
    c.setFont("Helvetica-Bold", 8)
    miktar = etiket.get('miktar', 0)
    c.drawString(info_x, info_y, f"Miktar: {miktar:,.0f} {etiket.get('birim', 'ADET')}")

    info_y -= 3.5 * mm_unit
    c.setFont("Helvetica", 7)
    c.drawString(info_x, info_y, f"Lot: {etiket.get('lot_no', '')}")

    info_y -= 3.5 * mm_unit
    kontrolcu = etiket.get('kontrolcu', '')
    if kontrolcu:
        c.drawString(info_x, info_y, f"Kontrol: {str(kontrolcu)[:25]}")

    # Red nedeni
    info_y -= 3.5 * mm_unit
    red_neden = etiket.get('red_neden', etiket.get('aciklama', ''))
    if red_neden:
        c.setFont("Helvetica-Bold", 7)
        c.setFillColorRGB(0.93, 0.27, 0.27)
        c.drawString(info_x, info_y, f"Neden: {str(red_neden)[:35]}")

    # Tarih
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 6)
    tarih = etiket.get('tarih')
    if tarih:
        tarih_str = tarih.strftime("%d.%m.%Y") if hasattr(tarih, 'strftime') else str(tarih)[:10]
        c.drawRightString(ETIKET_GENISLIK - margin, 3 * mm_unit, tarih_str)


def red_etiket_pdf_olustur(output_path: str, etiketler: list) -> str:
    """RED etiketleri A4 PDF'i oluştur"""
    from reportlab.lib.pagesizes import A4

    a4_width, a4_height = A4
    sutun_sayisi = 2
    satir_sayisi = 5
    etiket_w = 100 * mm_unit
    etiket_h = 50 * mm_unit
    margin_x = (a4_width - (sutun_sayisi * etiket_w)) / 2
    margin_y = (a4_height - (satir_sayisi * etiket_h)) / 2

    c = canvas.Canvas(output_path, pagesize=A4)
    etiket_index = 0

    while etiket_index < len(etiketler):
        for satir in range(satir_sayisi):
            for sutun in range(sutun_sayisi):
                if etiket_index >= len(etiketler):
                    break

                etiket = etiketler[etiket_index]
                x = margin_x + (sutun * etiket_w)
                y = a4_height - margin_y - ((satir + 1) * etiket_h)

                c.setStrokeColorRGB(0.8, 0.8, 0.8)
                c.setDash(1, 2)
                c.rect(x, y, etiket_w, etiket_h)
                c.setDash()

                c.saveState()
                c.translate(x, y)
                _red_etiket_icerik_ciz(c, etiket)
                c.restoreState()

                etiket_index += 1

        if etiket_index < len(etiketler):
            c.showPage()

    c.save()
    return output_path


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
    v3.0 tasarım JSON formatını destekler
    
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
        'genislik_mm': json_elem.get('width', None),
        'yukseklik_mm': json_elem.get('height', None),
        'font_adi': 'DejaVuSans',
        'font_boyut': json_elem.get('size', 10),
        'font_kalin': json_elem.get('bold', False),
        'font_italik': json_elem.get('italic', False),
        'metin_hiza': (json_elem.get('align', 'left') or 'left').upper(),
        'veri_alani': None,
        'sabit_metin': None,
        'format_pattern': None,
        'barkod_tipi': 'CODE128',
        'barkod_yukseklik_mm': 8,
        'barkod_metin_goster': True,
        # v3.0 ek alanlar
        'image_data': json_elem.get('image_data', ''),
        'image_ext': json_elem.get('image_ext', ''),
        'image_path': json_elem.get('image_path', ''),
        'keep_aspect': json_elem.get('keep_aspect', True),
        'opacity': json_elem.get('opacity', 100),
        'show_border': json_elem.get('show_border', False),
        'test_stok_kodu': json_elem.get('test_stok_kodu', ''),
        'line_style': json_elem.get('line_style', 'solid'),
        'border_width': json_elem.get('border_width', 0.5),
        'fill': json_elem.get('fill', False),
        'rounded': json_elem.get('rounded', False),
        'direction': json_elem.get('direction', 'Yatay'),
    }
    
    if elem_type == 'TEXT':
        element['sabit_metin'] = json_elem.get('text', '')
    
    elif elem_type == 'FIELD':
        # FIELD tipi — veri alanından çeker
        element['element_tipi'] = 'FIELD'
        field = json_elem.get('field', 'lot_no')
        if field.startswith('{') and field.endswith('}'):
            field = field[1:-1]
        element['veri_alani'] = field
    
    elif elem_type == 'BARCODE':
        element['genislik_mm'] = json_elem.get('width', 25)
        element['yukseklik_mm'] = json_elem.get('height', 25)
        element['barkod_yukseklik_mm'] = json_elem.get('height', 25)
        # kod_tipi >> barcode_type >> default QR (kullanici talep, 2026-04-29)
        element['barkod_tipi'] = (
            json_elem.get('kod_tipi')
            or json_elem.get('barcode_type')
            or 'QR'
        )
        element['barkod_metin_goster'] = json_elem.get('show_text', True)

        field = json_elem.get('field', 'lot_no')
        if field.startswith('{') and field.endswith('}'):
            field = field[1:-1]
        element['veri_alani'] = field
    
    elif elem_type == 'IMAGE':
        element['genislik_mm'] = json_elem.get('width', 25)
        element['yukseklik_mm'] = json_elem.get('height', 20)
    
    elif elem_type == 'PRODUCT_IMAGE':
        element['genislik_mm'] = json_elem.get('width', 60)
        element['yukseklik_mm'] = json_elem.get('height', 50)
    
    elif elem_type == 'LINE':
        element['genislik_mm'] = json_elem.get('length', 50)
        element['yukseklik_mm'] = json_elem.get('width', 0.5)
    
    elif elem_type == 'RECT':
        element['element_tipi'] = 'RECT'
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
        'siparis_no': str(etiket.get('siparis_no', '')),
        'is_emri_no': str(etiket.get('is_emri_no', '')),
        'kontrolcu': str(etiket.get('kontrolcu', '')),
        'kontrol_tarihi': etiket.get('kontrol_tarihi').strftime('%d.%m.%Y %H:%M') if etiket.get('kontrol_tarihi') and hasattr(etiket.get('kontrol_tarihi'), 'strftime') else str(etiket.get('kontrol_tarihi', ''))[:16],
        'saglam_adet': f"{etiket.get('saglam_adet', 0):,.0f}",
        'hatali_adet': f"{etiket.get('hatali_adet', 0):,.0f}",
        'sonuc': str(etiket.get('sonuc', '')),
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
    Şablon elementlerini çiz - v3.0 tasarım JSON formatı desteği
    
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
    
    # Font kayıt (bir kez)
    _register_dejavu_fonts()
    
    for element in sablon['elementler']:
        # Element pozisyonu (şablonda sol üstten tanımlı, PDF'de sol alttan)
        elem_x = base_x + element['x_mm'] * mm_unit
        elem_y = base_y + etiket_h - element['y_mm'] * mm_unit  # Y koordinatı ters çevir
        
        element_tipi = element.get('element_tipi', 'TEXT').upper()
        
        try:
            if element_tipi == 'TEXT':
                _text_element_ciz(c, element, etiket, elem_x, elem_y)
            
            elif element_tipi == 'FIELD':
                _field_element_ciz(c, element, etiket, elem_x, elem_y)
            
            elif element_tipi == 'BARCODE':
                _barcode_element_ciz(c, element, etiket, elem_x, elem_y)
            
            elif element_tipi == 'IMAGE':
                _image_element_ciz(c, element, etiket, elem_x, elem_y)
            
            elif element_tipi == 'PRODUCT_IMAGE':
                _product_image_element_ciz(c, element, etiket, elem_x, elem_y)
            
            elif element_tipi == 'LINE':
                _line_element_ciz(c, element, elem_x, elem_y)
            
            elif element_tipi in ('RECTANGLE', 'RECT'):
                _rectangle_element_ciz(c, element, elem_x, elem_y)
                
        except Exception as e:
            print(f"Element çizim hatası ({element.get('element_adi', '?')}): {e}")
            import traceback
            traceback.print_exc()


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


def _register_dejavu_fonts():
    """DejaVu Sans fontlarını kaydet - Türkçe karakter desteği (İ, Ş, Ğ, Ü, Ö, Ç)"""
    if hasattr(_register_dejavu_fonts, '_done'):
        return _register_dejavu_fonts._done
    
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # utils/ttf dizinini bul
    this_file = os.path.abspath(__file__)
    font_path = None
    check_dir = os.path.dirname(this_file)
    for _ in range(6):
        candidate = os.path.join(check_dir, 'utils', 'ttf')
        if os.path.isdir(candidate):
            font_path = candidate
            break
        check_dir = os.path.dirname(check_dir)
    
    if not font_path:
        # Bilinen yolları dene
        for kp in [r'D:\PROJELER\ALL\NEXOR_CORE_DATA\utils\ttf']:
            if os.path.isdir(kp):
                font_path = kp
                break
    
    if not font_path:
        _register_dejavu_fonts._done = False
        return False
    
    font_map = {
        'NexorFont': 'DejaVuSans.ttf',
        'NexorFont-Bold': 'DejaVuSans-Bold.ttf',
        'NexorFont-Italic': 'DejaVuSans-Oblique.ttf',
        'NexorFont-BoldItalic': 'DejaVuSans-BoldOblique.ttf',
    }
    
    registered = False
    for name, filename in font_map.items():
        fpath = os.path.join(font_path, filename)
        if os.path.exists(fpath):
            try:
                pdfmetrics.registerFont(TTFont(name, fpath))
                registered = True
            except Exception:
                pass
    
    if registered:
        try:
            from reportlab.pdfbase.pdfmetrics import registerFontFamily
            registerFontFamily('NexorFont',
                normal='NexorFont',
                bold='NexorFont-Bold',
                italic='NexorFont-Italic',
                boldItalic='NexorFont-BoldItalic')
        except Exception:
            pass
    
    _register_dejavu_fonts._done = registered
    return registered


def _get_font_name(element: dict) -> str:
    """Element için doğru font adını döndür (DejaVu tabanlı)"""
    bold = element.get('font_kalin', False)
    italic = element.get('font_italik', False)
    
    has_dejavu = getattr(_register_dejavu_fonts, '_done', False)
    
    if has_dejavu:
        if bold and italic:
            return 'NexorFont-BoldItalic'
        elif bold:
            return 'NexorFont-Bold'
        elif italic:
            return 'NexorFont-Italic'
        return 'NexorFont'
    else:
        if bold and italic:
            return 'Helvetica-BoldOblique'
        elif bold:
            return 'Helvetica-Bold'
        elif italic:
            return 'Helvetica-Oblique'
        return 'Helvetica'


def _text_element_ciz(c: canvas.Canvas, element: dict, etiket: dict, x: float, y: float):
    """Sabit metin elementi çiz (v3.0 TEXT tipi)"""
    metin = _veri_alani_deger_al(element, etiket)
    if not metin:
        return
    
    font_name = _get_font_name(element)
    font_boyut = element.get('font_boyut', 10)
    
    try:
        c.setFont(font_name, font_boyut)
    except Exception:
        try:
            c.setFont('NexorFont', font_boyut)
        except Exception:
            c.setFont('Helvetica', font_boyut)
    
    c.setFillColorRGB(0, 0, 0)
    
    # Y pozisyonu: şablonda top-left, PDF'de baseline
    # ascent ≈ font_boyut * 0.75 (pt cinsinden)
    ascent_pt = font_boyut * 0.75
    text_y = y - ascent_pt
    
    metin_hiza = element.get('metin_hiza', 'LEFT').upper()
    genislik = element.get('genislik_mm')
    
    if metin_hiza == 'CENTER' and genislik:
        text_x = x + (genislik * mm_unit) / 2
        c.drawCentredString(text_x, text_y, metin)
    elif metin_hiza == 'RIGHT' and genislik:
        text_x = x + genislik * mm_unit
        c.drawRightString(text_x, text_y, metin)
    else:
        c.drawString(x, text_y, metin)


def _field_element_ciz(c: canvas.Canvas, element: dict, etiket: dict, x: float, y: float):
    """Veri alanı elementi çiz (v3.0 FIELD tipi)"""
    metin = _veri_alani_deger_al(element, etiket)
    if not metin:
        return
    
    font_name = _get_font_name(element)
    font_boyut = element.get('font_boyut', 10)
    
    try:
        c.setFont(font_name, font_boyut)
    except Exception:
        try:
            c.setFont('NexorFont', font_boyut)
        except Exception:
            c.setFont('Helvetica', font_boyut)
    
    c.setFillColorRGB(0, 0, 0)
    
    ascent_pt = font_boyut * 0.75
    text_y = y - ascent_pt
    
    metin_hiza = element.get('metin_hiza', 'LEFT').upper()
    genislik = element.get('genislik_mm')
    
    if metin_hiza == 'CENTER' and genislik:
        text_x = x + (genislik * mm_unit) / 2
        c.drawCentredString(text_x, text_y, metin)
    elif metin_hiza == 'RIGHT' and genislik:
        text_x = x + genislik * mm_unit
        c.drawRightString(text_x, text_y, metin)
    else:
        c.drawString(x, text_y, metin)


def _barcode_element_ciz(c: canvas.Canvas, element: dict, etiket: dict, x: float, y: float):
    """Kod elementi çiz - QR (default) veya Code128"""
    barkod_veri = _veri_alani_deger_al(element, etiket)
    # Fallback: qr_data bossa lot_no'ya dus (kalite disi etiket akislarinda qr_data yok)
    if not barkod_veri:
        if element.get('veri_alani') == 'qr_data':
            barkod_veri = str(etiket.get('lot_no', '') or '')
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
            # QR (default) - kare olmasi icin min(w,h)
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
    """Logo/Resim elementi çiz (v3.0 IMAGE tipi) - dosya yolu veya base64 destekli"""
    import base64
    from io import BytesIO
    
    genislik = (element.get('genislik_mm') or 25) * mm_unit
    yukseklik = (element.get('yukseklik_mm') or 20) * mm_unit
    keep_aspect = element.get('keep_aspect', True)
    opacity = element.get('opacity', 100) / 100.0
    
    img_drawn = False
    
    # 1. Dosya yolundan
    img_path = element.get('image_path', '')
    if img_path and os.path.exists(img_path):
        try:
            if opacity < 1.0:
                c.saveState()
                c.setFillAlpha(opacity)
            
            if keep_aspect:
                c.drawImage(img_path, x, y - yukseklik, width=genislik, height=yukseklik,
                           preserveAspectRatio=True, anchor='c', mask='auto')
            else:
                c.drawImage(img_path, x, y - yukseklik, width=genislik, height=yukseklik, mask='auto')
            
            if opacity < 1.0:
                c.restoreState()
            img_drawn = True
        except Exception as e:
            print(f"Image file render error: {e}")
    
    # 2. Base64'ten
    if not img_drawn and element.get('image_data'):
        try:
            img_bytes = base64.b64decode(element['image_data'])
            img = ImageReader(BytesIO(img_bytes))
            
            if opacity < 1.0:
                c.saveState()
                c.setFillAlpha(opacity)
            
            if keep_aspect:
                iw, ih = img.getSize()
                ratio = min(genislik / iw, yukseklik / ih)
                c.drawImage(img, x, y - yukseklik, iw * ratio, ih * ratio, mask='auto')
            else:
                c.drawImage(img, x, y - yukseklik, genislik, yukseklik, mask='auto')
            
            if opacity < 1.0:
                c.restoreState()
            img_drawn = True
        except Exception as e:
            print(f"Image base64 render error: {e}")
    
    # 3. Eski format: etiket dict'ten resim_path
    if not img_drawn:
        resim_path = etiket.get('resim_path')
        if resim_path and os.path.exists(resim_path):
            try:
                c.drawImage(resim_path, x, y - yukseklik, width=genislik, height=yukseklik,
                           preserveAspectRatio=True, anchor='c', mask='auto')
                img_drawn = True
            except Exception:
                pass
    
    if not img_drawn:
        # Placeholder
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setDash(2, 2)
        c.rect(x, y - yukseklik, genislik, yukseklik)
        c.setDash()


def _product_image_element_ciz(c: canvas.Canvas, element: dict, etiket: dict, x: float, y: float):
    """Ürün görseli elementi çiz (v3.0 PRODUCT_IMAGE tipi) - NAS'tan stok koduna göre çeker"""
    genislik = (element.get('genislik_mm') or 60) * mm_unit
    yukseklik = (element.get('yukseklik_mm') or 50) * mm_unit
    keep_aspect = element.get('keep_aspect', True)
    
    img_path = None
    
    # 1. Etiket verisinden stok_kodu ile NAS'tan bul
    stok_kodu = etiket.get('stok_kodu', '')
    if stok_kodu:
        img_path = urun_resmi_bul(str(stok_kodu))
    
    # 2. Test stok kodu ile dene
    if not img_path and element.get('test_stok_kodu'):
        img_path = urun_resmi_bul(element['test_stok_kodu'])
    
    # 3. Element'te kaydedilmiş image_path
    if not img_path:
        ip = element.get('image_path', '')
        if ip and os.path.exists(ip):
            img_path = ip
    
    # 4. Etiket'ten gelen resim_path (eski format uyumu)
    if not img_path:
        rp = etiket.get('resim_path')
        if rp and os.path.exists(rp):
            img_path = rp
    
    if img_path and os.path.exists(img_path):
        try:
            if keep_aspect:
                c.drawImage(img_path, x, y - yukseklik, width=genislik, height=yukseklik,
                           preserveAspectRatio=True, anchor='c', mask='auto')
            else:
                c.drawImage(img_path, x, y - yukseklik, width=genislik, height=yukseklik, mask='auto')
            
            # Opsiyonel kenarlık
            if element.get('show_border', False):
                c.setStrokeColorRGB(0.4, 0.4, 0.4)
                c.setLineWidth(0.5)
                c.rect(x, y - yukseklik, genislik, yukseklik)
        except Exception as e:
            print(f"Product image render error: {e}")
            _draw_image_placeholder(c, x, y, genislik, yukseklik, stok_kodu)
    else:
        _draw_image_placeholder(c, x, y, genislik, yukseklik, stok_kodu)


def _draw_image_placeholder(c, x, y, w, h, label=''):
    """Resim bulunamadığında placeholder çiz"""
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setDash(3, 2)
    c.rect(x, y - h, w, h)
    c.setDash()
    if label:
        try:
            c.setFont('NexorFont', 7)
        except Exception:
            c.setFont('Helvetica', 7)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(x + w / 2, y - h / 2, f"Görsel: {label}")
        c.setFillColorRGB(0, 0, 0)


def _line_element_ciz(c: canvas.Canvas, element: dict, x: float, y: float):
    """Çizgi elementi çiz (v3.0 LINE tipi)"""
    length = (element.get('genislik_mm') or 50) * mm_unit
    width = element.get('yukseklik_mm') or element.get('border_width', 0.5)
    direction = element.get('direction', 'Yatay')
    line_style = element.get('line_style', 'solid')
    
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(width)
    
    if line_style == 'dashed' or line_style == 'Kesikli':
        c.setDash(4, 2)
    elif line_style == 'dotted' or line_style == 'Noktalı':
        c.setDash(1, 2)
    
    if direction == 'Dikey':
        c.line(x, y, x, y - length)
    else:
        c.line(x, y, x + length, y)
    
    c.setDash()  # Reset


def _rectangle_element_ciz(c: canvas.Canvas, element: dict, x: float, y: float):
    """Dikdörtgen elementi çiz (v3.0 RECT tipi)"""
    genislik = (element.get('genislik_mm') or 30) * mm_unit
    yukseklik = (element.get('yukseklik_mm') or 15) * mm_unit
    border_width = element.get('border_width', 0.5)
    fill = element.get('fill', False)
    rounded = element.get('rounded', False)
    
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(border_width)
    
    if fill:
        c.setFillColorRGB(0.95, 0.95, 0.95)
    
    if rounded:
        c.roundRect(x, y - yukseklik, genislik, yukseklik, 2 * mm_unit, 
                    fill=1 if fill else 0, stroke=1)
    else:
        c.rect(x, y - yukseklik, genislik, yukseklik, 
               fill=1 if fill else 0, stroke=1)
    
    if fill:
        c.setFillColorRGB(0, 0, 0)  # Reset


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


def godex_ezpl_olustur(etiket: dict, etiket_w_mm: int = 100, etiket_h_mm: int = 50, sablon: dict = None) -> str:
    """
    Tek bir etiket için Godex EZPL komutu oluştur
    Şablon varsa tasarım JSON'ından, yoksa hardcoded layout kullanır
    
    EZPL'de Türkçe karakter sınırlı desteğe sahiptir.
    Godex EZPL internal fontları genellikle ASCII-only olduğundan,
    Türkçe özel karakterler (İ,Ş,Ğ,Ü,Ö,Ç) bozuk çıkabilir.
    Mümkünse ZPL+^CI28 tercih edilmeli.
    
    Args:
        etiket: Etiket verileri
        etiket_w_mm: Etiket genişliği (mm)
        etiket_h_mm: Etiket yüksekliği (mm)
        sablon: Şablon bilgileri (elementler dahil)
    
    Returns:
        str: EZPL komut dizisi
    """
    dpi = GODEX_DPI
    
    # EZPL'de ^Q = label uzunluğu (feed yönü), ^W = kafa genişliği
    fiziksel_genislik = etiket_w_mm
    fiziksel_uzunluk = etiket_h_mm
    
    w_dots = mm_to_dots(fiziksel_genislik, dpi)
    h_dots = mm_to_dots(fiziksel_uzunluk, dpi)
    
    ezpl = []
    
    # Başlangıç komutları
    ezpl.append(f"^Q{h_dots},3")   # Label uzunluğu (feed yönü)
    ezpl.append(f"^W{w_dots}")      # Kafa genişliği
    ezpl.append("^H10")             # Isı ayarı
    ezpl.append("^P1")              # 1 adet yazdır
    ezpl.append("^S3")              # Hız
    ezpl.append("^AT")              # Transfer modu
    ezpl.append("^C1")              # Sürekli mod
    ezpl.append("^R0")              # Referans nokta
    ezpl.append("~Q+0")             # Offset
    ezpl.append("^O0")              # Yön
    ezpl.append("^D0")              # Density
    ezpl.append("^E12")             # Uzunluk
    ezpl.append("~R200")            # Referans ayarı
    ezpl.append("^L")               # Label başlangıcı
    
    # Şablon varsa elementlerden üret
    if sablon and sablon.get('elementler'):
        for element in sablon['elementler']:
            elem_tipi = element.get('element_tipi', 'TEXT').upper()
            x_dots = mm_to_dots(element.get('x_mm', 0))
            y_dots = mm_to_dots(element.get('y_mm', 0))
            
            if elem_tipi in ('TEXT', 'FIELD'):
                metin = _veri_alani_deger_al(element, etiket)
                if metin:
                    metin = _ezpl_turkce_temizle(metin)
                    bold = element.get('font_kalin', False)
                    size = element.get('font_boyut', 10)
                    # EZPL font: A=küçük(9pt), B=orta(12pt), C=büyük(15pt), D=çok büyük(24pt)
                    if size >= 20:
                        font = 'D'
                    elif size >= 14:
                        font = 'C'
                    elif size >= 10 or bold:
                        font = 'B'
                    else:
                        font = 'A'
                    ezpl.append(f"A{font},{x_dots},{y_dots},1,1,0,0,{metin}")
            
            elif elem_tipi == 'BARCODE':
                barkod_veri = _veri_alani_deger_al(element, etiket)
                if barkod_veri:
                    h_bc = mm_to_dots(element.get('barkod_yukseklik_mm', 10))
                    show = '1' if element.get('barkod_metin_goster', True) else '0'
                    ezpl.append(f"BA,{x_dots},{y_dots},1,2,{h_bc},0,{show},{barkod_veri}")
            
            elif elem_tipi == 'LINE':
                length = mm_to_dots(element.get('genislik_mm', 50))
                width_dots = max(1, mm_to_dots(element.get('yukseklik_mm', 0.5)))
                direction = element.get('direction', 'Yatay')
                if direction == 'Dikey':
                    ezpl.append(f"LO,{x_dots},{y_dots},{width_dots},{length}")
                else:
                    ezpl.append(f"LO,{x_dots},{y_dots},{length},{width_dots}")
            
            elif elem_tipi in ('RECT', 'RECTANGLE'):
                w = mm_to_dots(element.get('genislik_mm', 30))
                h = mm_to_dots(element.get('yukseklik_mm', 15))
                bw = max(1, mm_to_dots(element.get('border_width', 0.5)))
                ezpl.append(f"LO,{x_dots},{y_dots},{w},{bw}")  # Top
                ezpl.append(f"LO,{x_dots},{y_dots},{bw},{h}")  # Left
                ezpl.append(f"LO,{x_dots + w},{y_dots},{bw},{h}")  # Right
                ezpl.append(f"LO,{x_dots},{y_dots + h},{w},{bw}")  # Bottom
    else:
        # Hardcoded fallback layout
        stok_kodu = str(etiket.get('stok_kodu', ''))[:20]
        stok_adi = _ezpl_turkce_temizle(str(etiket.get('stok_adi', ''))[:35])
        musteri = _ezpl_turkce_temizle(str(etiket.get('musteri', ''))[:30])
        kaplama = _ezpl_turkce_temizle(str(etiket.get('kaplama', ''))[:20])
        miktar = etiket.get('miktar', 0)
        birim = str(etiket.get('birim', 'ADET'))
        palet_no = etiket.get('palet_no', 1)
        toplam_palet = etiket.get('toplam_palet', 1)
        lot_no = str(etiket.get('lot_no', ''))
        irsaliye_no = str(etiket.get('irsaliye_no', ''))
        tarih = etiket.get('tarih')
        tarih_str = tarih.strftime('%d.%m.%Y') if tarih and hasattr(tarih, 'strftime') else str(tarih)[:10] if tarih else ''
        
        ezpl.append(f"AA,{mm_to_dots(3)},{mm_to_dots(3)},1,1,0,0,ATMO MANUFACTURING")
        ezpl.append(f"AA,{mm_to_dots(70)},{mm_to_dots(3)},1,1,0,0,{irsaliye_no}")
        ezpl.append(f"LO,{mm_to_dots(3)},{mm_to_dots(8)},{mm_to_dots(94)},1")
        ezpl.append(f"AB,{mm_to_dots(25)},{mm_to_dots(10)},1,1,0,0,{stok_kodu}")
        ezpl.append(f"AA,{mm_to_dots(25)},{mm_to_dots(16)},1,1,0,0,{stok_adi}")
        ezpl.append(f"AA,{mm_to_dots(25)},{mm_to_dots(21)},1,1,0,0,MUS: {musteri}")
        if kaplama:
            ezpl.append(f"AA,{mm_to_dots(25)},{mm_to_dots(25)},1,1,0,0,KAP: {kaplama}")
        ezpl.append(f"AB,{mm_to_dots(25)},{mm_to_dots(30)},1,1,0,0,MIKTAR: {miktar:,.0f} {birim}")
        ezpl.append(f"AB,{mm_to_dots(70)},{mm_to_dots(30)},1,1,0,0,P:{palet_no:02d}/{toplam_palet:02d}")
        ezpl.append(f"AB,{mm_to_dots(25)},{mm_to_dots(36)},1,1,0,0,LOT: {lot_no}")
        ezpl.append(f"BA,{mm_to_dots(3)},{mm_to_dots(42)},1,2,60,0,2,{lot_no}")
        ezpl.append(f"AA,{mm_to_dots(75)},{mm_to_dots(45)},1,1,0,0,{tarih_str}")
    
    ezpl.append("E")
    return "\n".join(ezpl)


def _ezpl_turkce_temizle(metin: str) -> str:
    """
    EZPL komutu için Türkçe karakter dönüşümü
    EZPL internal fontları genellikle ISO-8859-9 (Latin-5) desteği sınırlıdır.
    Güvenli olması için Türkçe özel karakterleri ASCII karşılıklarına çevirir.
    """
    if not metin:
        return ''
    # Türkçe → ASCII dönüşümü (EZPL internal font uyumu için)
    tr_map = {
        'İ': 'I', 'ı': 'i',
        'Ş': 'S', 'ş': 's',
        'Ğ': 'G', 'ğ': 'g',
        'Ü': 'U', 'ü': 'u',
        'Ö': 'O', 'ö': 'o',
        'Ç': 'C', 'ç': 'c',
    }
    for tr_char, ascii_char in tr_map.items():
        metin = metin.replace(tr_char, ascii_char)
    return metin


def godex_zpl_olustur(etiket: dict, etiket_w_mm: int = 100, etiket_h_mm: int = 50, sablon: dict = None) -> str:
    """
    Tek bir etiket için ZPL komutu oluştur - şablon destekli
    
    Düzeltmeler:
    - ^CI28 ile UTF-8 encoding (Türkçe İ,Ş,Ğ,Ü,Ö,Ç desteği)
    - ^PON ile doğru yazdırma yönü (Normal orientation)  
    - ^PW her zaman fiziksel kağıt genişliği (kısa kenar)
    - ^LL her zaman fiziksel kağıt uzunluğu (uzun kenar / feed yönü)
    
    Args:
        etiket: Etiket verileri
        etiket_w_mm: Etiket genişliği (mm) - tasarımcıdaki W
        etiket_h_mm: Etiket yüksekliği (mm) - tasarımcıdaki H
        sablon: Şablon bilgileri (elementler dahil)
    
    Returns:
        str: ZPL komut dizisi
    """
    zpl = []
    zpl.append("^XA")
    
    # ===== KRİTİK: UTF-8 Encoding - Türkçe karakter desteği =====
    zpl.append("^CI28")  # UTF-8 character set
    
    # ===== Yazdırma yönü =====
    # Godex yazıcılarda etiket kafa altından geçerken:
    #   - Print Width (^PW) = kafa genişliği yönündeki boyut (yazıcıya takılı etiketin EN'i)
    #   - Label Length (^LL) = feed yönündeki boyut (etiketin BOY'u)
    #
    # Dikey etiket (50x100mm): fiziksel olarak 50mm genişlik, 100mm uzunluk 
    # Yatay etiket (100x50mm): fiziksel olarak 100mm genişlik, 50mm uzunluk
    #
    # Tasarımcıdaki genislik_mm = kağıt genişliği (kafa yönü)
    # Tasarımcıdaki yukseklik_mm = kağıt uzunluğu (feed yönü)
    
    fiziksel_genislik = etiket_w_mm  # kafa yönü
    fiziksel_uzunluk = etiket_h_mm   # feed yönü
    
    zpl.append(f"^PW{mm_to_dots(fiziksel_genislik)}")
    zpl.append(f"^LL{mm_to_dots(fiziksel_uzunluk)}")
    
    if sablon and sablon.get('elementler'):
        for element in sablon['elementler']:
            elem_tipi = element.get('element_tipi', 'TEXT').upper()
            x_dots = mm_to_dots(element.get('x_mm', 0))
            y_dots = mm_to_dots(element.get('y_mm', 0))
            
            if elem_tipi in ('TEXT', 'FIELD'):
                metin = _veri_alani_deger_al(element, etiket)
                if metin:
                    # Türkçe karakterleri ZPL-safe yap
                    metin = _zpl_turkce_temizle(metin)
                    
                    size = element.get('font_boyut', 10)
                    bold = element.get('font_kalin', False)
                    # ZPL ^A0 font boyutu (dot cinsinden)
                    # 203 DPI'da 1pt ≈ 2.82 dots
                    h = max(16, int(size * 2.8))
                    w = max(14, int(size * 2.4))
                    if bold:
                        h = int(h * 1.15)
                        w = int(w * 1.1)
                    
                    # Hizalama
                    hiza = element.get('metin_hiza', 'LEFT').upper()
                    genislik_mm = element.get('genislik_mm')
                    
                    if hiza == 'CENTER' and genislik_mm:
                        # ZPL'de ortala: ^FB (field block) kullan
                        fb_w = mm_to_dots(genislik_mm)
                        zpl.append(f"^FO{x_dots},{y_dots}^A0N,{h},{w}^FB{fb_w},1,0,C,0^FD{metin}^FS")
                    elif hiza == 'RIGHT' and genislik_mm:
                        fb_w = mm_to_dots(genislik_mm)
                        zpl.append(f"^FO{x_dots},{y_dots}^A0N,{h},{w}^FB{fb_w},1,0,R,0^FD{metin}^FS")
                    else:
                        zpl.append(f"^FO{x_dots},{y_dots}^A0N,{h},{w}^FD{metin}^FS")
            
            elif elem_tipi == 'BARCODE':
                barkod_veri = _veri_alani_deger_al(element, etiket)
                if barkod_veri:
                    h_bc = mm_to_dots(element.get('barkod_yukseklik_mm', 10))
                    show = 'Y' if element.get('barkod_metin_goster', True) else 'N'
                    zpl.append(f"^FO{x_dots},{y_dots}^BCN,{h_bc},{show},N,N^FD{barkod_veri}^FS")
            
            elif elem_tipi == 'LINE':
                length = mm_to_dots(element.get('genislik_mm', 50))
                width_dots = max(1, mm_to_dots(element.get('yukseklik_mm', 0.5)))
                direction = element.get('direction', 'Yatay')
                if direction == 'Dikey':
                    zpl.append(f"^FO{x_dots},{y_dots}^GB{width_dots},{length},{width_dots}^FS")
                else:
                    zpl.append(f"^FO{x_dots},{y_dots}^GB{length},{width_dots},{width_dots}^FS")
            
            elif elem_tipi in ('RECT', 'RECTANGLE'):
                w = mm_to_dots(element.get('genislik_mm', 30))
                h = mm_to_dots(element.get('yukseklik_mm', 15))
                bw = max(1, mm_to_dots(element.get('border_width', 0.5)))
                zpl.append(f"^FO{x_dots},{y_dots}^GB{w},{h},{bw}^FS")
    else:
        # ===== Hardcoded fallback layout =====
        stok_kodu = str(etiket.get('stok_kodu', ''))[:20]
        stok_adi = _zpl_turkce_temizle(str(etiket.get('stok_adi', ''))[:35])
        musteri = _zpl_turkce_temizle(str(etiket.get('musteri', ''))[:30])
        kaplama = _zpl_turkce_temizle(str(etiket.get('kaplama', ''))[:20])
        miktar = etiket.get('miktar', 0)
        birim = str(etiket.get('birim', 'ADET'))
        palet_no = etiket.get('palet_no', 1)
        toplam_palet = etiket.get('toplam_palet', 1)
        lot_no = str(etiket.get('lot_no', ''))
        irsaliye_no = str(etiket.get('irsaliye_no', ''))
        tarih = etiket.get('tarih')
        tarih_str = tarih.strftime('%d.%m.%Y') if tarih and hasattr(tarih, 'strftime') else str(tarih)[:10] if tarih else ''
        
        zpl.append(f"^FO{mm_to_dots(3)},{mm_to_dots(3)}^A0N,20,20^FDATMO MANUFACTURING^FS")
        zpl.append(f"^FO{mm_to_dots(70)},{mm_to_dots(3)}^A0N,18,18^FD{irsaliye_no}^FS")
        zpl.append(f"^FO{mm_to_dots(3)},{mm_to_dots(8)}^GB{mm_to_dots(94)},1,1^FS")
        zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(10)}^A0N,28,28^FD{stok_kodu}^FS")
        zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(16)}^A0N,20,20^FD{stok_adi}^FS")
        zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(21)}^A0N,18,18^FDMUS: {musteri}^FS")
        if kaplama:
            zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(25)}^A0N,18,18^FDKAP: {kaplama}^FS")
        zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(30)}^A0N,22,22^FDMIKTAR: {miktar:,.0f} {birim}^FS")
        zpl.append(f"^FO{mm_to_dots(70)},{mm_to_dots(30)}^A0N,22,22^FDP:{palet_no:02d}/{toplam_palet:02d}^FS")
        zpl.append(f"^FO{mm_to_dots(25)},{mm_to_dots(36)}^A0N,22,22^FDLOT: {lot_no}^FS")
        zpl.append(f"^FO{mm_to_dots(3)},{mm_to_dots(42)}^BCN,50,Y,N,N^FD{lot_no}^FS")
        zpl.append(f"^FO{mm_to_dots(75)},{mm_to_dots(45)}^A0N,18,18^FD{tarih_str}^FS")
    
    zpl.append("^XZ")
    return "\n".join(zpl)


def _zpl_turkce_temizle(metin: str) -> str:
    """
    ZPL komutları için Türkçe metin temizleme
    ^CI28 aktifken UTF-8 doğrudan gönderilir.
    ZPL özel karakterlerini escape'le (^, ~)
    """
    if not metin:
        return ''
    # ZPL'de ^ ve ~ özel komut karakterleri — metin içindeyse kaldır
    metin = metin.replace('^', '').replace('~', '')
    return metin


def godex_yazdir(etiketler: list, printer_name: str = None, format_type: str = "ZPL") -> bool:
    """
    Etiketleri Godex yazıcıya gönder - şablon destekli
    
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
        
        # Şablon bilgisini yükle (ilk etiketten)
        sablon = None
        sablon_id = etiketler[0].get('sablon_id') if etiketler else None
        if sablon_id:
            try:
                sablon = sablon_bilgilerini_al(sablon_id)
                if sablon:
                    print(f"  Şablon yüklendi: {sablon.get('sablon_adi')}, {len(sablon.get('elementler', []))} element")
            except Exception as e:
                print(f"  Şablon yüklenemedi: {e}")
        
        etiket_w_mm = int(sablon['genislik_mm']) if sablon else GODEX_ETIKET_GENISLIK_MM
        etiket_h_mm = int(sablon['yukseklik_mm']) if sablon else GODEX_ETIKET_YUKSEKLIK_MM
        
        # Tüm etiketler için komut oluştur
        all_commands = []
        for etiket in etiketler:
            if format_type.upper() == "EZPL":
                cmd = godex_ezpl_olustur(etiket, etiket_w_mm, etiket_h_mm, sablon)
            else:
                cmd = godex_zpl_olustur(etiket, etiket_w_mm, etiket_h_mm, sablon)
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


# ============================================================================
# ATLAS KATAFOREZ - DİKEY ETİKET (50x100mm)
# ============================================================================

def atlas_dikey_etiket_pdf(
    output_path: str,
    stok_kodu: str,
    stok_adi: str,
    musteri: str,
    tip: str,
    toplam_miktar: float,
    birim: str,
    palet_sayisi: int,
    irsaliye_no: str,
    tarih: datetime,
    lot_sira: int = 1,
    resim_path: str = None
) -> list:
    """
    Atlas Kataforez dikey etiketleri (50x100mm) PDF'i oluştur
    
    Args:
        output_path: PDF çıktı yolu
        stok_kodu: Stok kodu
        stok_adi: Ürün adı
        musteri: Müşteri adı
        tip: Kaplama tipi (Kataforez, Zinc, vb.)
        toplam_miktar: Toplam miktar
        birim: Birim (ADET, KG, vb.)
        palet_sayisi: Kaç palet
        irsaliye_no: İrsaliye numarası
        tarih: Tarih
        lot_sira: Lot sıra numarası
        resim_path: Ürün resim yolu (opsiyonel)
    
    Returns:
        list: Oluşturulan lot numaraları listesi
    """
    c = canvas.Canvas(output_path, pagesize=(DIKEY_ETIKET_GENISLIK, DIKEY_ETIKET_YUKSEKLIK))
    
    # Resim yolu yoksa NAS'tan bul
    if not resim_path:
        resim_path = urun_resmi_bul(stok_kodu)
    
    # Her palet için miktar
    palet_miktar = toplam_miktar / palet_sayisi
    
    lot_numaralari = []
    
    for palet_no in range(1, palet_sayisi + 1):
        # Lot numarası
        lot_no = lot_no_olustur(tarih, lot_sira, palet_no)
        lot_numaralari.append(lot_no)
        
        # Dikey etiket çiz
        _atlas_dikey_etiket_ciz(
            c=c,
            stok_kodu=stok_kodu,
            stok_adi=stok_adi,
            musteri=musteri,
            tip=tip,
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


def _atlas_dikey_etiket_ciz(
    c: canvas.Canvas,
    stok_kodu: str,
    stok_adi: str,
    musteri: str,
    tip: str,
    miktar: float,
    birim: str,
    palet_no: int,
    toplam_palet: int,
    lot_no: str,
    irsaliye_no: str,
    tarih: datetime,
    resim_path: str = None
):
    """
    Atlas Kataforez dikey etiketi çiz (50x100mm)
    
    Layout:
        ┌──────────────┐
        │    ATLAS     │  ← Header (Logo + İrsaliye)
        ├──────────────┤
        │   [RESİM]    │  ← Ürün resmi (140px yükseklik)
        │  Stok Kodu   │  ← Stok kodu (çerçeveli)
        │  Ürün Adı    │
        │  MÜŞ: ...    │
        │  TİP: ...    │
        │  500 ADET    │  ← Miktar
        │ PALET: 01/03 │
        │     LOT:     │  ← LOT (çerçeveli)
        │ LOT-2502-01  │
        ├──────────────┤
        │   BARKOD     │  ← Barkod + Tarih
        └──────────────┘
    """
    W = DIKEY_ETIKET_GENISLIK
    H = DIKEY_ETIKET_YUKSEKLIK
    m = 3 * mm_unit  # margin
    
    # ===== HEADER: Logo + İrsaliye =====
    header_h = 18 * mm_unit
    
    # Atlas logo veya metin
    logo_y = H - 10 * mm_unit
    if os.path.exists(ATLAS_LOGO_PATH):
        try:
            c.drawImage(
                ATLAS_LOGO_PATH,
                W/2 - 15*mm_unit,  # Ortala
                logo_y,
                width=30*mm_unit,
                height=8*mm_unit,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception:
            # Logo yüklenemezse metin
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(W/2, logo_y + 2*mm_unit, "ATLAS")
    else:
        # Logo yoksa metin
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(W/2, logo_y + 2*mm_unit, "ATLAS")
    
    # İrsaliye no (altında)
    c.setFont("Helvetica", 7)
    c.drawCentredString(W/2, H - 16*mm_unit, irsaliye_no)
    
    # Header çizgisi
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.8*mm_unit)
    c.line(m, H - header_h, W - m, H - header_h)
    
    # ===== CONTENT AREA =====
    content_y = H - header_h - 2*mm_unit
    
    # --- ÜRÜN RESMİ ---
    resim_w = W - 2*m
    resim_h = 52 * mm_unit
    resim_x = m
    resim_y = content_y - resim_h
    
    if resim_path and os.path.exists(resim_path):
        try:
            c.drawImage(
                resim_path,
                resim_x,
                resim_y,
                width=resim_w,
                height=resim_h,
                preserveAspectRatio=True
            )
            # Resim çerçevesi
            c.setStrokeColorRGB(0.3, 0.3, 0.3)
            c.setLineWidth(0.5*mm_unit)
            c.rect(resim_x, resim_y, resim_w, resim_h)
        except Exception:
            # Resim yüklenemezse boş kutu
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            c.setLineWidth(0.5*mm_unit)
            c.rect(resim_x, resim_y, resim_w, resim_h)
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawCentredString(W/2, resim_y + resim_h/2, "Resim Yok")
            c.setFillColorRGB(0, 0, 0)
    else:
        # Resim yok - boş kutu
        c.setStrokeColorRGB(0.6, 0.6, 0.6)
        c.setLineWidth(0.5*mm_unit)
        c.rect(resim_x, resim_y, resim_w, resim_h)
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(W/2, resim_y + resim_h/2, "Resim Yok")
        c.setFillColorRGB(0, 0, 0)
    
    # --- BİLGİ ALANI ---
    info_y = resim_y - 4*mm_unit
    
    # Stok Kodu (çerçeveli, kalın)
    c.setFont("Helvetica-Bold", 11)
    stok_text = stok_kodu[:15]  # Max 15 karakter
    c.setLineWidth(0.6*mm_unit)
    c.setStrokeColorRGB(0, 0, 0)
    # Çerçeve
    text_w = c.stringWidth(stok_text, "Helvetica-Bold", 11)
    box_w = text_w + 4*mm_unit
    box_x = (W - box_w) / 2
    c.rect(box_x, info_y - 1*mm_unit, box_w, 5*mm_unit)
    c.drawCentredString(W/2, info_y, stok_text)
    
    # Ürün Adı (2 satır mümkün)
    info_y -= 8*mm_unit
    c.setFont("Helvetica", 9)
    # Uzun isimleri böl
    if len(stok_adi) > 20:
        # İlk 20 karakter
        satir1 = stok_adi[:20]
        # Kalan kısmı (max 20)
        satir2 = stok_adi[20:40]
        if len(stok_adi) > 40:
            satir2 = satir2[:17] + "..."
        c.drawCentredString(W/2, info_y, satir1)
        c.drawCentredString(W/2, info_y - 3*mm_unit, satir2)
        info_y -= 3*mm_unit
    else:
        c.drawCentredString(W/2, info_y, stok_adi)
    
    # İnce ayırıcı
    info_y -= 3*mm_unit
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(0.3*mm_unit)
    c.line(m + 2*mm_unit, info_y, W - m - 2*mm_unit, info_y)
    
    # Müşteri
    info_y -= 4*mm_unit
    c.setFont("Helvetica", 7)
    musteri_text = musteri[:22] + "..." if len(musteri) > 22 else musteri
    c.drawCentredString(W/2, info_y, f"MÜŞ: {musteri_text}")
    
    # Tip (Kaplama tipi)
    info_y -= 3.5*mm_unit
    if tip:
        tip_text = tip[:20] + "..." if len(tip) > 20 else tip
        c.drawCentredString(W/2, info_y, f"TİP: {tip_text}")
    
    # İnce ayırıcı
    info_y -= 3*mm_unit
    c.line(m + 2*mm_unit, info_y, W - m - 2*mm_unit, info_y)
    
    # Miktar (vurgulu kutu)
    info_y -= 6*mm_unit
    c.setFont("Helvetica-Bold", 10)
    miktar_text = f"{miktar:,.0f} {birim}"
    # Gri arka plan kutusu
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.setStrokeColorRGB(0.6, 0.6, 0.6)
    c.setLineWidth(0.3*mm_unit)
    c.rect(m + 1*mm_unit, info_y - 1*mm_unit, W - 2*m - 2*mm_unit, 5*mm_unit, fill=1, stroke=1)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(W/2, info_y, miktar_text)
    
    # Palet
    info_y -= 5*mm_unit
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(W/2, info_y, f"PALET: {palet_no:02d}/{toplam_palet:02d}")
    
    # LOT Numarası (çerçeveli, vurgulu)
    info_y -= 9*mm_unit
    c.setFont("Helvetica-Bold", 9)
    c.setLineWidth(0.8*mm_unit)
    c.setStrokeColorRGB(0, 0, 0)
    # Çerçeve
    lot_box_h = 10*mm_unit
    c.rect(m + 1*mm_unit, info_y - 2*mm_unit, W - 2*m - 2*mm_unit, lot_box_h)
    # "LOT:" etiketi
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(W/2, info_y + 4*mm_unit, "LOT:")
    # Lot numarası
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(W/2, info_y, lot_no)
    
    # ===== FOOTER: Barkod + Tarih =====
    footer_h = 22 * mm_unit
    footer_y = footer_h
    
    # Üst çizgi
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.8*mm_unit)
    c.line(m, footer_y, W - m, footer_y)
    
    # Barkod
    barcode_y = 8 * mm_unit
    try:
        barcode = code128.Code128(lot_no, barWidth=0.28*mm_unit, barHeight=9*mm_unit)
        # Barkodu ortala
        barcode_w = barcode.width
        barcode_x = (W - barcode_w) / 2
        barcode.drawOn(c, barcode_x, barcode_y)
    except Exception:
        # Barkod oluşturulamazsa metin
        c.setFont("Courier-Bold", 7)
        c.drawCentredString(W/2, barcode_y + 4*mm_unit, f"*{lot_no}*")
    
    # Tarih (en altta)
    c.setFont("Helvetica", 7)
    tarih_str = tarih.strftime("%d.%m.%Y")
    c.drawCentredString(W/2, 2*mm_unit, tarih_str)


def atlas_dikey_etiket_yazdir(
    stok_kodu: str,
    stok_adi: str,
    musteri: str,
    tip: str,
    toplam_miktar: float,
    birim: str,
    palet_sayisi: int,
    irsaliye_no: str,
    tarih: datetime,
    lot_sira: int = 1,
    resim_path: str = None,
    yazdir: bool = True
) -> tuple:
    """
    Atlas dikey etiket oluştur ve yazdır
    
    Returns:
        tuple: (pdf_path, lot_numaralari)
    """
    import tempfile
    
    # Geçici PDF oluştur
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        pdf_path = tmp.name
    
    # PDF oluştur
    lot_numaralari = atlas_dikey_etiket_pdf(
        output_path=pdf_path,
        stok_kodu=stok_kodu,
        stok_adi=stok_adi,
        musteri=musteri,
        tip=tip,
        toplam_miktar=toplam_miktar,
        birim=birim,
        palet_sayisi=palet_sayisi,
        irsaliye_no=irsaliye_no,
        tarih=tarih,
        lot_sira=lot_sira,
        resim_path=resim_path
    )
    
    if yazdir:
        # Godex yazıcıya gönder veya PDF aç
        try:
            pdf_yazdir(pdf_path)
        except Exception as e:
            print(f"Yazdırma hatası: {e}")
            # Hata varsa PDF'i aç
            os.startfile(pdf_path)
    
    return pdf_path, lot_numaralari

