# -*- coding: utf-8 -*-
"""
NEXOR ERP - Merkezi PDF Sablon Motoru
=====================================
Tum PDF ciktilari bu motordan gecir. Firma bilgileri, logo, header/footer,
renkler ve layout tek yerden yonetilir.

TEMA VERSIYONLARI:
  - "kurumsal"  : Koyu header, kirmizi accent (varsayilan — Atlas Kataforez icin)
  - "profesyonel": Mavi ton, daha acik header
  - "minimal"   : Sade siyah-beyaz, ince cizgiler

KULLANIM:
    from utils.pdf_template import PDFTemplate

    tpl = PDFTemplate("Izin Talep Formu", form_no="IZN-00018")
    c = tpl.canvas          # reportlab canvas
    y = tpl.content_top     # header altindan baslayan y

    y = tpl.section("PERSONEL BILGILERI", y)
    tpl.field(x, y, "Ad Soyad", "Ali Yilmaz")
    ...
    tpl.signature_row(y, ["Personel", "Amir", "IK"])
    tpl.finish()            # footer yaz, kaydet, ac
"""
import os
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.pdfgen import canvas as canvas_mod
from reportlab.lib.utils import ImageReader

from core.firma_bilgileri import get_firma_bilgileri, get_firma_logo_path
from config import REPORT_OUTPUT_DIR

# =====================================================================
# Font kayit (bir kere cagrilir)
# =====================================================================
_fonts_registered = False


def _ensure_fonts():
    global _fonts_registered
    if _fonts_registered:
        return
    try:
        from utils.etiket_yazdir import _register_dejavu_fonts
        _register_dejavu_fonts()
    except Exception:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        for name, paths in [
            ("NexorFont", [r"C:\Windows\Fonts\DejaVuSans.ttf",
                           r"C:\Windows\Fonts\calibri.ttf",
                           r"C:\Windows\Fonts\arial.ttf"]),
            ("NexorFont-Bold", [r"C:\Windows\Fonts\DejaVuSans-Bold.ttf",
                                r"C:\Windows\Fonts\calibrib.ttf",
                                r"C:\Windows\Fonts\arialbd.ttf"]),
        ]:
            for fp in paths:
                try:
                    if os.path.exists(fp):
                        pdfmetrics.registerFont(TTFont(name, fp))
                        break
                except Exception:
                    continue
    _fonts_registered = True


# =====================================================================
# TEMA TANIMLARI
# =====================================================================

_THEMES = {
    "kurumsal": {
        "header_bg":    HexColor("#1F2937"),
        "header_text":  white,
        "accent":       HexColor("#C41E1E"),
        "section_bg":   HexColor("#1F2937"),
        "section_text": white,
        "label_color":  HexColor("#6B7280"),
        "value_color":  black,
        "border_color": HexColor("#D1D5DB"),
        "muted":        HexColor("#9CA3AF"),
        "success":      HexColor("#10B981"),
        "warning":      HexColor("#F59E0B"),
        "error":        HexColor("#EF4444"),
        "info":         HexColor("#3B82F6"),
        "bg_light":     HexColor("#F3F4F6"),
        "table_header_bg":   HexColor("#1F2937"),
        "table_header_text": white,
        "table_alt_bg":      HexColor("#F9FAFB"),
        "table_border":      HexColor("#E5E7EB"),
    },
    "profesyonel": {
        "header_bg":    HexColor("#1E3A5F"),
        "header_text":  white,
        "accent":       HexColor("#2563EB"),
        "section_bg":   HexColor("#1E3A5F"),
        "section_text": white,
        "label_color":  HexColor("#64748B"),
        "value_color":  HexColor("#0F172A"),
        "border_color": HexColor("#CBD5E1"),
        "muted":        HexColor("#94A3B8"),
        "success":      HexColor("#059669"),
        "warning":      HexColor("#D97706"),
        "error":        HexColor("#DC2626"),
        "info":         HexColor("#2563EB"),
        "bg_light":     HexColor("#F1F5F9"),
        "table_header_bg":   HexColor("#1E3A5F"),
        "table_header_text": white,
        "table_alt_bg":      HexColor("#F8FAFC"),
        "table_border":      HexColor("#E2E8F0"),
    },
    "minimal": {
        "header_bg":    HexColor("#FFFFFF"),
        "header_text":  HexColor("#111827"),
        "accent":       HexColor("#111827"),
        "section_bg":   HexColor("#F3F4F6"),
        "section_text": HexColor("#111827"),
        "label_color":  HexColor("#6B7280"),
        "value_color":  black,
        "border_color": HexColor("#D1D5DB"),
        "muted":        HexColor("#9CA3AF"),
        "success":      HexColor("#059669"),
        "warning":      HexColor("#D97706"),
        "error":        HexColor("#DC2626"),
        "info":         HexColor("#2563EB"),
        "bg_light":     HexColor("#F9FAFB"),
        "table_header_bg":   HexColor("#F3F4F6"),
        "table_header_text": HexColor("#111827"),
        "table_alt_bg":      HexColor("#F9FAFB"),
        "table_border":      HexColor("#E5E7EB"),
    },
}

# Aktif tema (config'den okunabilir, varsayilan: kurumsal)
_active_theme_name = "kurumsal"


def get_pdf_theme_name() -> str:
    try:
        from core.external_config import config_manager
        return config_manager.get('pdf_theme', _active_theme_name) or _active_theme_name
    except Exception:
        return _active_theme_name


def set_pdf_theme_name(name: str):
    global _active_theme_name
    if name in _THEMES:
        _active_theme_name = name
        try:
            from core.external_config import config_manager
            config_manager.set('pdf_theme', name)
            config_manager.save()
        except Exception:
            pass


def get_available_themes() -> list:
    return list(_THEMES.keys())


# =====================================================================
# YARDIMCILAR
# =====================================================================

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def format_tarih(val) -> str:
    if val is None:
        return "-"
    if isinstance(val, (datetime, date)):
        return val.strftime("%d.%m.%Y")
    return str(val)[:10]


def _rounded_rect(c, x, y, w, h, r, fill_color=None, stroke_color=None, line_width=0.5):
    p = c.beginPath()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.arcTo(x + w - r, y, x + w, y + r, 0)
    p.lineTo(x + w, y + h - r)
    p.arcTo(x + w, y + h - r, x + w - r, y + h, 0)
    p.lineTo(x + r, y + h)
    p.arcTo(x + r, y + h, x, y + h - r, 0)
    p.lineTo(x, y + r)
    p.arcTo(x, y + r, x + r, y, 0)
    p.close()
    c.setLineWidth(line_width)
    if fill_color:
        c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.drawPath(p, fill=1 if fill_color else 0, stroke=1)
    elif fill_color:
        c.drawPath(p, fill=1, stroke=0)


# =====================================================================
# ANA SINIF
# =====================================================================

class PDFTemplate:
    """
    Merkezi PDF sablon motoru.

    Kullanim:
        tpl = PDFTemplate("Izin Talep Formu", form_no="IZN-00018")
        c = tpl.canvas
        y = tpl.content_top

        y = tpl.section("PERSONEL BILGILERI", y)
        tpl.field(MARGIN + 4*mm, y, "Ad Soyad", "Ali Yilmaz")
        y -= 14 * mm
        ...
        tpl.signature_row(y, ["Personel", "Amir", "IK"])
        path = tpl.finish()
    """

    def __init__(self, title: str, form_no: str = "",
                 filename: str = None, theme: str = None,
                 orientation: str = "portrait"):
        """
        Args:
            title: Form basligi (ornek: "IZIN TALEP FORMU")
            form_no: Form numarasi (ornek: "IZN-00018")
            filename: Cikti dosya adi (None ise otomatik)
            theme: "kurumsal", "profesyonel", "minimal" (None ise config'den)
            orientation: "portrait" veya "landscape"
        """
        _ensure_fonts()

        self._title = title
        self._form_no = form_no
        self._theme_name = theme or get_pdf_theme_name()
        self._t = _THEMES.get(self._theme_name, _THEMES["kurumsal"])

        # Firma bilgileri
        self._firma = get_firma_bilgileri()
        self._firma_adi = self._firma.get('name', '') or "NEXOR ERP"
        self._firma_logo = get_firma_logo_path()

        # Sayfa boyutu
        if orientation == "landscape":
            self._page_w, self._page_h = A4[1], A4[0]
        else:
            self._page_w, self._page_h = A4

        self._margin = MARGIN
        self._usable_w = self._page_w - 2 * self._margin

        # Dosya yolu
        REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        if filename:
            self._path = str(REPORT_OUTPUT_DIR / filename)
        else:
            safe_title = "".join(c for c in title if c.isalnum() or c in ' _-').strip().replace(' ', '_')
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._path = str(REPORT_OUTPUT_DIR / f"{safe_title}_{ts}.pdf")

        # Canvas olustur
        self._canvas = canvas_mod.Canvas(self._path, pagesize=(self._page_w, self._page_h))
        self._canvas.setTitle(title)
        self._canvas.setAuthor(self._firma_adi)
        self._canvas.setCreator("NEXOR ERP")

        # Header ciz
        self._content_top = self._draw_header()

    # -- Properties --
    @property
    def canvas(self):
        return self._canvas

    @property
    def content_top(self) -> float:
        return self._content_top

    @property
    def margin(self) -> float:
        return self._margin

    @property
    def usable_w(self) -> float:
        return self._usable_w

    @property
    def page_w(self) -> float:
        return self._page_w

    @property
    def page_h(self) -> float:
        return self._page_h

    @property
    def col_w(self) -> float:
        """Iki kolonlu layout icin tek kolon genisligi"""
        return self._usable_w / 2 - 2 * mm

    @property
    def theme(self) -> dict:
        return self._t

    # ── HEADER ──
    def _draw_header(self) -> float:
        c = self._canvas
        t = self._t
        hdr_margin = 5 * mm   # sayfa kenarinda neredeyse
        y = self._page_h - hdr_margin
        header_h = 26 * mm
        hdr_w = self._page_w - 2 * hdr_margin

        if self._theme_name == "minimal":
            c.setStrokeColor(t["border_color"])
            c.setLineWidth(1)
            c.line(hdr_margin, y - header_h, self._page_w - hdr_margin, y - header_h)
        else:
            _rounded_rect(c, hdr_margin, y - header_h, hdr_w, header_h,
                          3 * mm, fill_color=t["header_bg"])

        # Logo
        logo_w = 0
        if self._firma_logo and os.path.exists(self._firma_logo):
            try:
                logo_w = 20 * mm
                c.drawImage(ImageReader(self._firma_logo),
                            hdr_margin + 5 * mm, y - header_h + 5 * mm,
                            width=16 * mm, height=16 * mm,
                            preserveAspectRatio=True, mask='auto')
            except Exception:
                logo_w = 0

        text_x = hdr_margin + 5 * mm + logo_w
        right_reserved = 45 * mm
        max_text_w = hdr_w - (text_x - hdr_margin) - right_reserved

        from reportlab.pdfbase.pdfmetrics import stringWidth

        # Firma adi (buyuk, ust satir)
        c.setFillColor(t["header_text"])
        firma_text = self._firma_adi
        for fs in (12, 11, 10, 9, 8):
            c.setFont("NexorFont-Bold", fs)
            if stringWidth(firma_text, "NexorFont-Bold", fs) <= max_text_w:
                break
        else:
            while len(firma_text) > 10 and stringWidth(firma_text + "...", "NexorFont-Bold", 8) > max_text_w:
                firma_text = firma_text[:-1]
            firma_text = firma_text.rstrip() + "..."
        c.drawString(text_x, y - 8 * mm, firma_text)

        # Form basligi (kucuk, alt satir)
        title_text = self._title
        for fs in (10, 9, 8):
            c.setFont("NexorFont-Bold", fs)
            if stringWidth(title_text, "NexorFont-Bold", fs) <= max_text_w:
                break
        c.drawString(text_x, y - 15 * mm, title_text)

        # Sag ust: form no + tarih
        if self._theme_name == "minimal":
            c.setFillColor(t["muted"])
        else:
            c.setFillColor(HexColor("#D1D5DB"))
        c.setFont("NexorFont", 7)
        right_x = self._page_w - hdr_margin - 5 * mm
        if self._form_no:
            c.drawRightString(right_x, y - 8 * mm, f"Form No: {self._form_no}")
        c.drawRightString(right_x, y - 15 * mm,
                          f"Basim: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

        return y - header_h - 4 * mm

    # ── SECTION TITLE ──
    def section(self, title: str, y: float) -> float:
        """Bolum basligi ciz. Yeni y dondurur."""
        c = self._canvas
        t = self._t
        _rounded_rect(c, self._margin, y - 0.5 * mm, self._usable_w, 6.5 * mm,
                       2 * mm, fill_color=t["section_bg"])
        c.setFillColor(t["section_text"])
        c.setFont("NexorFont-Bold", 8)
        c.drawString(self._margin + 3 * mm, y + 1 * mm, title)
        return y - 9 * mm

    # ── FIELD (label + value) ──
    def field(self, x: float, y: float, label: str, value, bold: bool = True,
              color=None):
        """Etiket + deger cifti ciz."""
        c = self._canvas
        t = self._t
        c.setFillColor(t["label_color"])
        c.setFont("NexorFont", 7)
        c.drawString(x, y + 1.5 * mm, label)
        c.setFillColor(color or t["value_color"])
        c.setFont("NexorFont-Bold" if bold else "NexorFont", 8.5)
        c.drawString(x, y - 3.5 * mm, str(value) if value else "-")

    # ── FIELD ROW (2 kolon) ──
    def field_row(self, y: float, label1: str, val1, label2: str = None, val2=None,
                  color1=None, color2=None) -> float:
        """Iki kolonlu alan satiri. 11mm asagi kaydirir."""
        x1 = self._margin + 4 * mm
        x2 = self._margin + self.col_w + 4 * mm
        self.field(x1, y, label1, val1, color=color1)
        if label2:
            self.field(x2, y, label2, val2, color=color2)
        return y - 11 * mm

    # ── BIG VALUE ──
    def big_value(self, x: float, y: float, label: str, value, color=None,
                  font_size: int = 16) -> float:
        """Buyuk deger gosterimi (gun sayisi, toplam tutar vs.)"""
        c = self._canvas
        t = self._t
        c.setFillColor(t["label_color"])
        c.setFont("NexorFont", 8)
        c.drawString(x, y + 2 * mm, label)
        c.setFillColor(color or t["accent"])
        c.setFont("NexorFont-Bold", font_size)
        c.drawString(x, y - 6 * mm, str(value))
        return y - 18 * mm

    # ── STATUS BADGE ──
    def status_badge(self, x: float, y: float, label: str, value: str,
                     status: str = "default"):
        """Durum gosterimi (ONAYLANDI, RED, BEKLEMEDE vs.)"""
        color_map = {
            "success": self._t["success"],
            "warning": self._t["warning"],
            "error":   self._t["error"],
            "info":    self._t["info"],
            "default": self._t["value_color"],
        }
        color = color_map.get(status, self._t["value_color"])
        self.field(x, y, label, value, color=color)

    # ── TABLE ──
    def table(self, y: float, headers: List[str], rows: List[List[str]],
              col_widths: List[float] = None, row_height: float = 6 * mm) -> float:
        """Tablo ciz. Yeni y dondurur."""
        c = self._canvas
        t = self._t
        n_cols = len(headers)

        if not col_widths:
            cw = self._usable_w / n_cols
            col_widths = [cw] * n_cols

        x_start = self._margin

        # Header
        hh = 6.5 * mm
        _rounded_rect(c, x_start, y - hh, self._usable_w, hh, 1 * mm,
                       fill_color=t["table_header_bg"])
        c.setFillColor(t["table_header_text"])
        c.setFont("NexorFont-Bold", 7)
        cx = x_start
        for i, h in enumerate(headers):
            c.drawString(cx + 2 * mm, y - hh + 2 * mm, h)
            cx += col_widths[i]
        y -= hh

        # Rows
        c.setFont("NexorFont", 7)
        for ri, row in enumerate(rows):
            # Alternating bg
            if ri % 2 == 1:
                _rounded_rect(c, x_start, y - row_height, self._usable_w, row_height,
                               0, fill_color=t["table_alt_bg"])

            # Border bottom
            c.setStrokeColor(t["table_border"])
            c.setLineWidth(0.3)
            c.line(x_start, y - row_height, x_start + self._usable_w, y - row_height)

            cx = x_start
            c.setFillColor(t["value_color"])
            for i, cell in enumerate(row):
                text = str(cell) if cell else "-"
                # Truncate if too long
                max_chars = int(col_widths[i] / (2 * mm))
                if len(text) > max_chars:
                    text = text[:max_chars - 1] + ".."
                c.drawString(cx + 2 * mm, y - row_height + 1.8 * mm, text)
                cx += col_widths[i]
            y -= row_height

        return y - 4 * mm

    # ── MULTILINE TEXT ──
    def text_block(self, y: float, text: str, max_lines: int = 8) -> float:
        """Cok satirli metin blogu."""
        c = self._canvas
        c.setFillColor(self._t["value_color"])
        c.setFont("NexorFont", 9)
        lines = (text or "").split('\n')
        for line in lines[:max_lines]:
            c.drawString(self._margin + 4 * mm, y, line[:90])
            y -= 5 * mm
        return y - 4 * mm

    # ── SIGNATURE ROW ──
    def signature_row(self, y: float, labels: List[str]) -> float:
        """Imza satiri ciz. Yeni y dondurur."""
        c = self._canvas
        t = self._t
        n = len(labels)
        gap = 4 * mm
        box_w = (self._usable_w - (n - 1) * gap) / n
        box_h = 30 * mm

        for i, label in enumerate(labels):
            x = self._margin + i * (box_w + gap)

            c.setStrokeColor(t["border_color"])
            c.setLineWidth(0.5)
            c.rect(x, y - box_h, box_w, box_h)

            c.setFillColor(t["label_color"])
            c.setFont("NexorFont-Bold", 9)
            c.drawCentredString(x + box_w / 2, y + 2 * mm, label)

            # Imza cizgisi
            line_y = y - box_h + 8 * mm
            c.setStrokeColor(t["border_color"])
            c.line(x + 8 * mm, line_y, x + box_w - 8 * mm, line_y)

            # Tarih yeri
            c.setFillColor(t["muted"])
            c.setFont("NexorFont", 7)
            c.drawCentredString(x + box_w / 2, y - box_h + 2 * mm,
                                "Tarih: ...../...../........")

        return y - box_h - 10 * mm

    # ── HORIZONTAL LINE ──
    def hline(self, y: float, color=None) -> float:
        c = self._canvas
        c.setStrokeColor(color or self._t["border_color"])
        c.setLineWidth(0.5)
        c.line(self._margin, y, self._page_w - self._margin, y)
        return y - 4 * mm

    # ── NEW PAGE ──
    def new_page(self) -> float:
        """Yeni sayfa baslat, header ciz, content_top dondur."""
        self._canvas.showPage()
        self._content_top = self._draw_header()
        return self._content_top

    # ── FOOTER + FINISH ──
    def finish(self, open_file: bool = True) -> str:
        """Footer yaz, PDF'i kaydet. Dosya yolunu dondurur."""
        self._draw_footer()
        self._canvas.save()

        if open_file:
            try:
                os.startfile(self._path)
            except Exception:
                pass

        return self._path

    def _draw_footer(self):
        c = self._canvas
        t = self._t
        c.setFillColor(t["muted"])
        c.setFont("NexorFont", 7)
        c.drawString(self._margin, self._margin - 5 * mm,
                     f"Bu belge {self._firma_adi} tarafindan olusturulmustur.")
        c.drawRightString(self._page_w - self._margin, self._margin - 5 * mm,
                          f"NEXOR ERP - {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    # ── FIRMA INFO BLOCK ──
    def firma_info_block(self, y: float) -> float:
        """Firma bilgi blogu (adres, telefon, email, vergi no)."""
        c = self._canvas
        t = self._t
        c.setFillColor(t["label_color"])
        c.setFont("NexorFont", 8)

        info_lines = []
        if self._firma.get('address'):
            info_lines.append(f"Adres: {self._firma['address']}")
        if self._firma.get('phone'):
            info_lines.append(f"Tel: {self._firma['phone']}")
        if self._firma.get('email'):
            info_lines.append(f"E-posta: {self._firma['email']}")
        if self._firma.get('tax_id'):
            info_lines.append(f"Vergi No: {self._firma['tax_id']}")

        for line in info_lines:
            c.drawString(self._margin + 4 * mm, y, line)
            y -= 4 * mm

        return y - 2 * mm
