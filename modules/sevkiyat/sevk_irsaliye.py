# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - İrsaliye Yönetim Sayfası
Oluşturulan irsaliyeleri listele, düzenle, yazdır
"""
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QMessageBox, QComboBox, QDateEdit,
    QDialog, QGridLayout, QTextBrowser, QSplitter, QWidget,
    QTextEdit, QSpinBox, QCheckBox, QFileDialog, QMenu
)
from PySide6.QtCore import Qt, QTimer, QDate, Signal
from PySide6.QtGui import QColor, QFont, QCursor
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog

from components.base_page import BasePage
from components.dialog_minimize_bar import add_minimize_button
from core.database import get_db_connection


class IrsaliyeOnizlemeDialog(QDialog):
    """İrsaliye önizleme ve yazdırma dialog'u"""
    
    def __init__(self, theme: dict, irsaliye_data: dict, satirlar: list, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.irsaliye = irsaliye_data
        self.satirlar = satirlar
        self.setWindowTitle(f"İrsaliye - {irsaliye_data.get('irsaliye_no', '')}")
        self.setMinimumSize(800, 900)
        self._setup_ui()
        add_minimize_button(self)

    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background: {self.theme.get('bg_main', '#1a1f2e')}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Önizleme alanı
        self.preview = QTextBrowser()
        self.preview.setStyleSheet(f"""
            QTextBrowser {{
                background: white;
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                padding: 20px;
            }}
        """)
        self.preview.setHtml(self._generate_html())
        layout.addWidget(self.preview, 1)
        
        # Yazdırma seçenekleri
        opts_frame = QFrame()
        opts_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px; padding: 10px;")
        opts_layout = QHBoxLayout(opts_frame)
        
        lbl = QLabel("Kopya:")
        lbl.setStyleSheet(f"color: {self.theme.get('text')};")
        opts_layout.addWidget(lbl)
        
        self.kopya_sayisi = QSpinBox()
        self.kopya_sayisi.setRange(1, 5)
        self.kopya_sayisi.setValue(2)
        self.kopya_sayisi.setStyleSheet(f"""
            QSpinBox {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        opts_layout.addWidget(self.kopya_sayisi)
        opts_layout.addStretch()
        layout.addWidget(opts_frame)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        pdf_btn = QPushButton("📥 PDF Kaydet")
        pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 10px 20px;
            }}
        """)
        pdf_btn.clicked.connect(self._pdf_kaydet)
        btn_layout.addWidget(pdf_btn)
        
        btn_layout.addStretch()
        
        kapat_btn = QPushButton("Kapat")
        kapat_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 10px 20px;
            }}
        """)
        kapat_btn.clicked.connect(self.reject)
        btn_layout.addWidget(kapat_btn)
        
        yazdir_btn = QPushButton("🖨️ Yazdır")
        yazdir_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#6366f1')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
        """)
        yazdir_btn.clicked.connect(self._yazdir)
        btn_layout.addWidget(yazdir_btn)
        
        layout.addLayout(btn_layout)
    
    def _generate_html(self) -> str:
        """İrsaliye HTML'i oluştur"""
        irs = self.irsaliye
        
        satirlar_html = ""
        toplam_miktar = 0
        for i, s in enumerate(self.satirlar, 1):
            satirlar_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{i}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{s.get('stok_kodu', '')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{s.get('stok_adi', '')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{s.get('lot_no', '')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{s.get('miktar', 0):,.0f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{s.get('birim', 'AD')}</td>
            </tr>
            """
            toplam_miktar += s.get('miktar', 0)
        
        tarih_str = irs.get('tarih', datetime.now())
        if isinstance(tarih_str, datetime):
            tarih_str = tarih_str.strftime('%d.%m.%Y')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 12px; margin: 0; padding: 20px; }}
                .header {{ display: flex; justify-content: space-between; margin-bottom: 20px; border-bottom: 2px solid #6366f1; padding-bottom: 15px; }}
                .firma {{ font-size: 18px; font-weight: bold; color: #333; }}
                .irsaliye-no {{ font-size: 24px; font-weight: bold; color: #6366f1; }}
                .bilgi-box {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 8px; }}
                .bilgi-row {{ display: flex; margin-bottom: 5px; }}
                .bilgi-label {{ width: 100px; font-weight: bold; color: #666; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background: #f5f5f5; padding: 10px; text-align: left; border-bottom: 2px solid #333; }}
                .toplam {{ font-weight: bold; background: #f5f5f5; }}
                .footer {{ margin-top: 40px; display: flex; justify-content: space-between; }}
                .imza-kutusu {{ width: 200px; text-align: center; }}
                .imza-cizgi {{ border-top: 1px solid #333; margin-top: 50px; padding-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div>
                    <div class="firma">ATMO MANUFACTURİNG</div>
                    <div style="color: #666;">Kaplama ve Yüzey İşlemleri</div>
                </div>
                <div style="text-align: right;">
                    <div class="irsaliye-no">{irs.get('irsaliye_no', '')}</div>
                    <div style="font-size: 14px; color: #6366f1;">SEVK İRSALİYESİ</div>
                </div>
            </div>
            
            <div style="display: flex; gap: 20px;">
                <div class="bilgi-box" style="flex: 1;">
                    <div style="font-weight: bold; margin-bottom: 10px; color: #6366f1;">MÜŞTERİ BİLGİLERİ</div>
                    <div class="bilgi-row"><span class="bilgi-label">Firma:</span><span style="font-weight: bold;">{irs.get('musteri', '')}</span></div>
                    <div class="bilgi-row"><span class="bilgi-label">Adres:</span><span>{irs.get('adres', '-')}</span></div>
                    <div class="bilgi-row"><span class="bilgi-label">Vergi No:</span><span>{irs.get('vergi_no', '-')}</span></div>
                </div>
                <div class="bilgi-box" style="flex: 1;">
                    <div style="font-weight: bold; margin-bottom: 10px; color: #6366f1;">SEVK BİLGİLERİ</div>
                    <div class="bilgi-row"><span class="bilgi-label">Tarih:</span><span>{tarih_str}</span></div>
                    <div class="bilgi-row"><span class="bilgi-label">Araç Plaka:</span><span>{irs.get('plaka', '-')}</span></div>
                    <div class="bilgi-row"><span class="bilgi-label">Şoför:</span><span>{irs.get('sofor', '-')}</span></div>
                    <div class="bilgi-row"><span class="bilgi-label">Taşıyıcı:</span><span>{irs.get('tasiyici', '-')}</span></div>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 40px;">Sıra</th>
                        <th style="width: 100px;">Stok Kodu</th>
                        <th>Ürün Adı</th>
                        <th style="width: 120px;">Lot No</th>
                        <th style="width: 80px; text-align: right;">Miktar</th>
                        <th style="width: 50px; text-align: center;">Birim</th>
                    </tr>
                </thead>
                <tbody>
                    {satirlar_html}
                    <tr class="toplam">
                        <td colspan="4" style="padding: 10px; text-align: right;">TOPLAM:</td>
                        <td style="padding: 10px; text-align: right;">{toplam_miktar:,.0f}</td>
                        <td style="padding: 10px; text-align: center;">AD</td>
                    </tr>
                </tbody>
            </table>
            
            <div style="margin-top: 20px; padding: 10px; background: #f5f5f5; border-radius: 4px;">
                <strong>Not:</strong> {irs.get('notlar', '-')}
            </div>
            
            <div class="footer">
                <div class="imza-kutusu"><div class="imza-cizgi">Teslim Eden</div></div>
                <div class="imza-kutusu"><div class="imza-cizgi">Şoför</div></div>
                <div class="imza-kutusu"><div class="imza-cizgi">Teslim Alan</div></div>
            </div>
            
            <div style="margin-top: 30px; text-align: center; color: #999; font-size: 10px;">
                Bu belge REDLINE NEXOR ERP sistemi tarafından oluşturulmuştur. | {datetime.now().strftime('%d.%m.%Y %H:%M')}
            </div>
        </body>
        </html>
        """
        return html
    
    def _yazdir(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        dialog = QPrintPreviewDialog(printer, self)
        dialog.paintRequested.connect(lambda p: self.preview.print_(p))
        dialog.exec()
    
    def _pdf_kaydet(self):
        dosya_adi = f"Irsaliye_{self.irsaliye.get('irsaliye_no', 'IRS')}.pdf"
        dosya_yolu, _ = QFileDialog.getSaveFileName(self, "PDF Kaydet", dosya_adi, "PDF Dosyaları (*.pdf)")
        if dosya_yolu:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(dosya_yolu)
            self.preview.print_(printer)
            QMessageBox.information(self, "Başarılı", f"PDF kaydedildi:\n{dosya_yolu}")


class IrsaliyeDuzenleDialog(QDialog):
    """İrsaliye düzenleme dialog'u - satır miktar düzeltme dahil"""

    def __init__(self, theme: dict, irsaliye_data: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.irsaliye = irsaliye_data.copy()
        self.satir_degisiklikler = []  # [(satir_id, yeni_miktar), ...]
        self.setWindowTitle(f"İrsaliye Düzenle - {irsaliye_data.get('irsaliye_no', '')}")
        self.setMinimumSize(700, 600)
        self._setup_ui()
        self._load_satirlar()
        add_minimize_button(self)

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('bg_main', '#1a1f2e')}; }}
            QLabel {{ color: {self.theme.get('text', '#fff')}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"✏️ İrsaliye Düzenle: {self.irsaliye.get('irsaliye_no', '')}")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme.get('primary')};")
        layout.addWidget(title)

        input_style = f"""
            QLineEdit, QComboBox, QTextEdit {{
                background: {self.theme.get('bg_input', '#2d3548')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 8px;
                color: {self.theme.get('text', '#fff')};
            }}
        """

        # Üst form - sevk bilgileri
        form_frame = QFrame()
        form_frame.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px; padding: 12px;")
        form = QGridLayout(form_frame)
        form.setSpacing(8)

        form.addWidget(QLabel("Araç Plaka:"), 0, 0)
        self.plaka_input = QLineEdit(self.irsaliye.get('plaka', ''))
        self.plaka_input.setStyleSheet(input_style)
        form.addWidget(self.plaka_input, 0, 1)

        form.addWidget(QLabel("Şoför Adı:"), 0, 2)
        self.sofor_input = QLineEdit(self.irsaliye.get('sofor', ''))
        self.sofor_input.setStyleSheet(input_style)
        form.addWidget(self.sofor_input, 0, 3)

        form.addWidget(QLabel("Taşıyıcı:"), 1, 0)
        self.tasiyici_input = QLineEdit(self.irsaliye.get('tasiyici', ''))
        self.tasiyici_input.setStyleSheet(input_style)
        form.addWidget(self.tasiyici_input, 1, 1)

        form.addWidget(QLabel("Durum:"), 1, 2)
        self.durum_combo = QComboBox()
        self.durum_combo.addItem("📦 Hazırlandı", "HAZIRLANDI")
        self.durum_combo.addItem("🚚 Sevk Edildi", "SEVK_EDILDI")
        self.durum_combo.addItem("✅ Teslim Edildi", "TESLIM_EDILDI")
        self.durum_combo.setStyleSheet(input_style)
        for i in range(self.durum_combo.count()):
            if self.durum_combo.itemData(i) == self.irsaliye.get('durum'):
                self.durum_combo.setCurrentIndex(i)
                break
        form.addWidget(self.durum_combo, 1, 3)

        form.addWidget(QLabel("Notlar:"), 2, 0, Qt.AlignTop)
        self.notlar_input = QTextEdit()
        self.notlar_input.setPlainText(self.irsaliye.get('notlar', ''))
        self.notlar_input.setMaximumHeight(60)
        self.notlar_input.setStyleSheet(input_style)
        form.addWidget(self.notlar_input, 2, 1, 1, 3)

        layout.addWidget(form_frame)

        # Alt - satır düzenleme
        sat_title = QLabel("📦 Satır Miktarları (Fazla/Eksik Düzeltme)")
        sat_title.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold; font-size: 13px;")
        layout.addWidget(sat_title)

        self.satirlar_table = QTableWidget()
        self.satirlar_table.setColumnCount(5)
        self.satirlar_table.setHorizontalHeaderLabels(["ID", "Stok Kodu / Ürün", "Lot No", "Mevcut Miktar", "Yeni Miktar"])
        self.satirlar_table.setColumnHidden(0, True)
        self.satirlar_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.satirlar_table.setColumnWidth(2, 130)
        self.satirlar_table.setColumnWidth(3, 100)
        self.satirlar_table.setColumnWidth(4, 100)
        self.satirlar_table.verticalHeader().setVisible(False)
        self.satirlar_table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.theme.get('bg_card')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border')};
                color: {self.theme.get('text')};
            }}
            QHeaderView::section {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
        """)
        layout.addWidget(self.satirlar_table, 1)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
                border-radius: 6px;
                padding: 10px 20px;
            }}
        """)
        iptal_btn.clicked.connect(self.reject)
        btn_layout.addWidget(iptal_btn)

        kaydet_btn = QPushButton("💾 Kaydet")
        kaydet_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
        """)
        kaydet_btn.clicked.connect(self._kaydet)
        btn_layout.addWidget(kaydet_btn)

        layout.addLayout(btn_layout)

    def _load_satirlar(self):
        """İrsaliye satırlarını tabloya yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cis.id,
                    COALESCE(ie.stok_kodu, u.urun_kodu, '') + ' - ' + COALESCE(ie.stok_adi, u.urun_adi, '') as urun,
                    cis.lot_no, cis.miktar
                FROM siparis.cikis_irsaliye_satirlar cis
                LEFT JOIN siparis.is_emirleri ie ON cis.is_emri_id = ie.id
                LEFT JOIN stok.urunler u ON cis.urun_id = u.id
                WHERE cis.irsaliye_id = ?
                ORDER BY cis.satir_no
            """, (self.irsaliye['id'],))
            rows = cursor.fetchall()
            conn.close()

            self.satirlar_table.setRowCount(0)
            spin_style = f"""
                QDoubleSpinBox {{
                    background: {self.theme.get('bg_input')};
                    border: 1px solid {self.theme.get('border')};
                    border-radius: 4px;
                    padding: 4px;
                    color: {self.theme.get('text')};
                }}
            """
            for row in rows:
                idx = self.satirlar_table.rowCount()
                self.satirlar_table.insertRow(idx)
                self.satirlar_table.setItem(idx, 0, QTableWidgetItem(str(row[0])))
                self.satirlar_table.setItem(idx, 1, QTableWidgetItem(row[1] or ''))
                self.satirlar_table.setItem(idx, 2, QTableWidgetItem(row[2] or ''))

                mevcut = QTableWidgetItem(f"{row[3]:,.0f}")
                mevcut.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.satirlar_table.setItem(idx, 3, mevcut)

                spin = QSpinBox()
                spin.setRange(0, 999999)
                spin.setValue(int(row[3] or 0))
                spin.setStyleSheet(spin_style)
                self.satirlar_table.setCellWidget(idx, 4, spin)

                self.satirlar_table.setRowHeight(idx, 36)

        except Exception as e:
            print(f"Satır yükleme hatası: {e}")

    def _kaydet(self):
        self.irsaliye['plaka'] = self.plaka_input.text().strip()
        self.irsaliye['sofor'] = self.sofor_input.text().strip()
        self.irsaliye['tasiyici'] = self.tasiyici_input.text().strip()
        self.irsaliye['durum'] = self.durum_combo.currentData()
        self.irsaliye['notlar'] = self.notlar_input.toPlainText().strip()

        # Satır miktar değişikliklerini topla
        self.satir_degisiklikler = []
        for i in range(self.satirlar_table.rowCount()):
            satir_id = int(self.satirlar_table.item(i, 0).text())
            spin = self.satirlar_table.cellWidget(i, 4)
            if spin:
                mevcut_text = self.satirlar_table.item(i, 3).text().replace(',', '')
                try:
                    mevcut = int(float(mevcut_text))
                except ValueError:
                    mevcut = 0
                yeni = spin.value()
                if yeni != mevcut:
                    self.satir_degisiklikler.append((satir_id, yeni))

        self.accept()

    def get_data(self):
        return self.irsaliye

    def get_satir_degisiklikler(self):
        return self.satir_degisiklikler


class SevkIrsaliyePage(BasePage):
    """İrsaliye Listesi ve Yönetim Sayfası"""
    
    irsaliye_guncellendi = Signal()
    
    def __init__(self, theme: dict):
        super().__init__(theme)
        self.all_data = []
        self.secili_irsaliye = None
        self.satirlar_data = []
        self._setup_ui()
        QTimer.singleShot(100, self._load_data)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📄 İrsaliye Yönetimi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.theme.get('text', '#fff')};")
        header.addWidget(title)
        
        header.addStretch()
        
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"color: {self.theme.get('text_muted')}; font-size: 12px;")
        header.addWidget(self.stats_label)
        
        header.addSpacing(20)
        
        self.saat_label = QLabel()
        self.saat_label.setStyleSheet(f"color: {self.theme.get('text_muted', '#8a94a6')}; font-size: 18px; font-weight: bold;")
        header.addWidget(self.saat_label)
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(self._button_style())
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Filtre satırı
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background: {self.theme.get('bg_card', '#242938')}; border-radius: 8px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 8, 12, 8)
        
        lbl1 = QLabel("Başlangıç:")
        lbl1.setStyleSheet(f"color: {self.theme.get('text')};")
        filter_layout.addWidget(lbl1)
        self.tarih_bas = QDateEdit()
        self.tarih_bas.setDate(QDate.currentDate().addDays(-30))
        self.tarih_bas.setCalendarPopup(True)
        self.tarih_bas.setStyleSheet(self._input_style())
        self.tarih_bas.dateChanged.connect(self._load_data)
        filter_layout.addWidget(self.tarih_bas)
        
        lbl2 = QLabel("Bitiş:")
        lbl2.setStyleSheet(f"color: {self.theme.get('text')};")
        filter_layout.addWidget(lbl2)
        self.tarih_bit = QDateEdit()
        self.tarih_bit.setDate(QDate.currentDate())
        self.tarih_bit.setCalendarPopup(True)
        self.tarih_bit.setStyleSheet(self._input_style())
        self.tarih_bit.dateChanged.connect(self._load_data)
        filter_layout.addWidget(self.tarih_bit)
        
        filter_layout.addSpacing(20)
        
        lbl3 = QLabel("Durum:")
        lbl3.setStyleSheet(f"color: {self.theme.get('text')};")
        filter_layout.addWidget(lbl3)
        self.durum_filter = QComboBox()
        self.durum_filter.addItem("-- Tümü --", None)
        self.durum_filter.addItem("📦 Hazırlandı", "HAZIRLANDI")
        self.durum_filter.addItem("🚚 Sevk Edildi", "SEVK_EDILDI")
        self.durum_filter.addItem("✅ Teslim Edildi", "TESLIM_EDILDI")
        self.durum_filter.addItem("❌ İptal", "IPTAL")
        self.durum_filter.setStyleSheet(self._input_style())
        self.durum_filter.currentIndexChanged.connect(self._load_data)
        filter_layout.addWidget(self.durum_filter)
        
        filter_layout.addSpacing(20)
        
        lbl4 = QLabel("Ara:")
        lbl4.setStyleSheet(f"color: {self.theme.get('text')};")
        filter_layout.addWidget(lbl4)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("İrsaliye no, müşteri, plaka...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.textChanged.connect(self._apply_search)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        layout.addWidget(filter_frame)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # SOL - Liste
        sol_widget = QWidget()
        sol_layout = QVBoxLayout(sol_widget)
        sol_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "İrsaliye No", "Tarih", "Müşteri", "Paket", "Adet", "Plaka", "Durum", "İşlem"
        ])
        
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 110)
        self.table.setColumnWidth(8, 120)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setStyleSheet(self._table_style())
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._show_detail)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        sol_layout.addWidget(self.table)
        splitter.addWidget(sol_widget)
        
        # SAĞ - Detay
        sag_widget = QFrame()
        sag_widget.setStyleSheet(f"background: {self.theme.get('bg_card')}; border-radius: 8px;")
        sag_layout = QVBoxLayout(sag_widget)
        sag_layout.setContentsMargins(16, 16, 16, 16)
        
        detay_title = QLabel("📋 İRSALİYE DETAYI")
        detay_title.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold; font-size: 14px;")
        sag_layout.addWidget(detay_title)
        
        self.detay_frame = QFrame()
        self.detay_frame.setStyleSheet(f"background: {self.theme.get('bg_main')}; border-radius: 8px; padding: 12px;")
        detay_grid = QGridLayout(self.detay_frame)
        detay_grid.setSpacing(8)
        
        labels = ["İrsaliye No:", "Tarih:", "Müşteri:", "Plaka:", "Şoför:", "Taşıyıcı:", "Durum:"]
        self.detay_labels = {}
        
        for i, lbl in enumerate(labels):
            label = QLabel(lbl)
            label.setStyleSheet(f"color: {self.theme.get('text_muted')};")
            detay_grid.addWidget(label, i, 0)
            
            value = QLabel("-")
            value.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold;")
            detay_grid.addWidget(value, i, 1)
            self.detay_labels[lbl] = value
        
        sag_layout.addWidget(self.detay_frame)
        
        satirlar_title = QLabel("📦 SATIRLAR")
        satirlar_title.setStyleSheet(f"color: {self.theme.get('text')}; font-weight: bold; margin-top: 12px;")
        sag_layout.addWidget(satirlar_title)
        
        self.satirlar_table = QTableWidget()
        self.satirlar_table.setColumnCount(5)
        self.satirlar_table.setHorizontalHeaderLabels(["Stok Kodu", "Ürün Adı", "Lot No", "Miktar", "Birim"])
        self.satirlar_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.satirlar_table.setStyleSheet(self._table_style())
        self.satirlar_table.verticalHeader().setVisible(False)
        sag_layout.addWidget(self.satirlar_table, 1)
        
        toplam_layout = QHBoxLayout()
        toplam_layout.addStretch()
        self.toplam_label = QLabel("Toplam: 0 kalem, 0 adet")
        self.toplam_label.setStyleSheet(f"color: {self.theme.get('primary')}; font-weight: bold;")
        toplam_layout.addWidget(self.toplam_label)
        sag_layout.addLayout(toplam_layout)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.setStyleSheet(self._button_style())
        self.duzenle_btn.clicked.connect(self._duzenle)
        self.duzenle_btn.setEnabled(False)
        btn_layout.addWidget(self.duzenle_btn)
        
        self.sevk_btn = QPushButton("🚚 Sevk Et")
        self.sevk_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('success', '#22c55e')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_muted')};
            }}
        """)
        self.sevk_btn.clicked.connect(self._sevk_et)
        self.sevk_btn.setEnabled(False)
        btn_layout.addWidget(self.sevk_btn)
        
        self.teslim_btn = QPushButton("✅ Teslim")
        self.teslim_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('info', '#3b82f6')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_muted')};
            }}
        """)
        self.teslim_btn.clicked.connect(self._teslim_et)
        self.teslim_btn.setEnabled(False)
        btn_layout.addWidget(self.teslim_btn)
        
        btn_layout.addStretch()
        
        self.iptal_btn = QPushButton("❌ İptal")
        self.iptal_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('danger', '#ef4444')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_muted')};
            }}
        """)
        self.iptal_btn.clicked.connect(self._iptal_et)
        self.iptal_btn.setEnabled(False)
        btn_layout.addWidget(self.iptal_btn)

        self.stok_iade_btn = QPushButton("📦 Stok İade")
        self.stok_iade_btn.setToolTip("İptal edilmiş irsaliyenin stoklarını sevk deposuna geri yükle")
        self.stok_iade_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('warning', '#f59e0b')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_muted')};
            }}
        """)
        self.stok_iade_btn.clicked.connect(self._stok_iade_yap)
        self.stok_iade_btn.setEnabled(False)
        btn_layout.addWidget(self.stok_iade_btn)

        self.zirve_btn = QPushButton("📤 Zirve'ye Aktar")
        self.zirve_btn.setToolTip("İrsaliyeyi Zirve Ticari'ye aktar (e-İrsaliye)")
        self.zirve_btn.setStyleSheet(f"""
            QPushButton {{
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #1d4ed8; }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_muted')};
            }}
        """)
        self.zirve_btn.clicked.connect(self._zirve_aktar)
        self.zirve_btn.setEnabled(False)
        btn_layout.addWidget(self.zirve_btn)

        self.fkr_btn = QPushButton("📋 Final Kalite Raporu")
        self.fkr_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('bg_input', '#2d3548')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {self.theme.get('bg_hover')};
                border-color: {self.theme.get('primary')};
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_muted')};
            }}
        """)
        self.fkr_btn.clicked.connect(self._final_kalite_raporu)
        self.fkr_btn.setEnabled(False)
        btn_layout.addWidget(self.fkr_btn)

        self.yazdir_btn = QPushButton("🖨️ Yazdır")
        self.yazdir_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.get('primary', '#6366f1')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:disabled {{
                background: {self.theme.get('bg_hover')};
                color: {self.theme.get('text_muted')};
            }}
        """)
        self.yazdir_btn.clicked.connect(self._yazdir)
        self.yazdir_btn.setEnabled(False)
        btn_layout.addWidget(self.yazdir_btn)
        
        sag_layout.addLayout(btn_layout)
        
        splitter.addWidget(sag_widget)
        splitter.setSizes([550, 450])
        
        layout.addWidget(splitter, 1)
    
    def _button_style(self):
        return f"""
            QPushButton {{
                background: {self.theme.get('bg_input', '#2d3548')};
                color: {self.theme.get('text', '#fff')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: {self.theme.get('bg_hover', '#3d4454')};
            }}
            QPushButton:disabled {{
                color: {self.theme.get('text_muted')};
            }}
        """
    
    def _input_style(self):
        return f"""
            QLineEdit, QComboBox, QDateEdit {{
                background: {self.theme.get('bg_input', '#2d3548')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 6px;
                padding: 6px 10px;
                color: {self.theme.get('text', '#fff')};
            }}
        """
    
    def _table_style(self):
        return f"""
            QTableWidget {{
                background-color: {self.theme.get('bg_card', '#242938')};
                border: 1px solid {self.theme.get('border', '#3d4454')};
                border-radius: 8px;
                gridline-color: {self.theme.get('border', '#3d4454')};
                color: {self.theme.get('text', '#ffffff')};
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {self.theme.get('border', '#3d4454')};
            }}
            QTableWidget::item:selected {{
                background-color: {self.theme.get('primary', '#6366f1')};
            }}
            QHeaderView::section {{
                background-color: {self.theme.get('bg_input', '#2d3548')};
                color: {self.theme.get('text', '#ffffff')};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {self.theme.get('primary', '#6366f1')};
                font-weight: bold;
            }}
        """
    
    def _update_time(self):
        now = datetime.now()
        self.saat_label.setText(now.strftime("%H:%M:%S"))
    
    def _load_data(self):
        """İrsaliyeleri yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            tarih_bas = self.tarih_bas.date().toPython()
            tarih_bit = self.tarih_bit.date().toPython()
            durum = self.durum_filter.currentData()
            
            query = """
                SELECT 
                    ci.id,
                    ci.irsaliye_no,
                    ci.tarih,
                    COALESCE(c.unvan, c.kisa_ad, 'Tanımsız') as musteri,
                    (SELECT COUNT(*) FROM siparis.cikis_irsaliye_satirlar WHERE irsaliye_id = ci.id) as paket_sayisi,
                    (SELECT SUM(miktar) FROM siparis.cikis_irsaliye_satirlar WHERE irsaliye_id = ci.id) as toplam_adet,
                    ci.arac_plaka,
                    ci.durum,
                    ci.sofor_adi,
                    ci.tasiyici_firma,
                    ci.notlar,
                    ci.cari_id
                FROM siparis.cikis_irsaliyeleri ci
                LEFT JOIN musteri.cariler c ON ci.cari_id = c.id
                WHERE ci.tarih BETWEEN ? AND ?
                  AND (ci.silindi_mi = 0 OR ci.silindi_mi IS NULL)
            """
            
            params = [tarih_bas, tarih_bit]
            
            if durum:
                query += " AND ci.durum = ?"
                params.append(durum)
            
            query += " ORDER BY ci.tarih DESC, ci.id DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            self.all_data = []
            for row in rows:
                self.all_data.append({
                    'id': row[0],
                    'irsaliye_no': row[1],
                    'tarih': row[2],
                    'musteri': row[3],
                    'paket_sayisi': row[4] or 0,
                    'toplam_adet': row[5] or 0,
                    'plaka': row[6] or '',
                    'durum': row[7] or '',
                    'sofor': row[8] or '',
                    'tasiyici': row[9] or '',
                    'notlar': row[10] or '',
                    'cari_id': row[11]
                })
            
            conn.close()
            self._display_data(self.all_data)
            self._update_stats()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenemedi: {e}")
    
    def _update_stats(self):
        """İstatistikleri güncelle"""
        toplam = len(self.all_data)
        hazirlanan = sum(1 for d in self.all_data if d['durum'] == 'HAZIRLANDI')
        sevk_edilen = sum(1 for d in self.all_data if d['durum'] == 'SEVK_EDILDI')
        teslim = sum(1 for d in self.all_data if d['durum'] == 'TESLIM_EDILDI')
        
        self.stats_label.setText(
            f"Toplam: {toplam} | 📦 Hazır: {hazirlanan} | 🚚 Sevk: {sevk_edilen} | ✅ Teslim: {teslim}"
        )
    
    def _display_data(self, data_list):
        """Tabloyu doldur"""
        self.table.setRowCount(0)
        
        for data in data_list:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(data['id'])))
            
            item = QTableWidgetItem(data['irsaliye_no'])
            item.setForeground(QColor(self.theme.get('primary', '#6366f1')))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            self.table.setItem(row_idx, 1, item)
            
            tarih_str = data['tarih'].strftime('%d.%m.%Y') if data['tarih'] else '-'
            self.table.setItem(row_idx, 2, QTableWidgetItem(tarih_str))
            
            self.table.setItem(row_idx, 3, QTableWidgetItem(data['musteri']))
            
            item = QTableWidgetItem(str(data['paket_sayisi']))
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 4, item)
            
            item = QTableWidgetItem(f"{data['toplam_adet']:,.0f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 5, item)
            
            self.table.setItem(row_idx, 6, QTableWidgetItem(data['plaka']))
            
            durum_text = {
                'HAZIRLANDI': '📦 Hazırlandı',
                'SEVK_EDILDI': '🚚 Sevk Edildi',
                'TESLIM_EDILDI': '✅ Teslim Edildi',
                'IPTAL': '❌ İptal'
            }.get(data['durum'], data['durum'])
            
            item = QTableWidgetItem(durum_text)
            if data['durum'] == 'TESLIM_EDILDI':
                item.setForeground(QColor(self.theme.get('success', '#22c55e')))
            elif data['durum'] == 'IPTAL':
                item.setForeground(QColor(self.theme.get('danger', '#ef4444')))
            elif data['durum'] == 'HAZIRLANDI':
                item.setForeground(QColor(self.theme.get('warning', '#f59e0b')))
            elif data['durum'] == 'SEVK_EDILDI':
                item.setForeground(QColor(self.theme.get('info', '#3b82f6')))
            self.table.setItem(row_idx, 7, item)
            
            widget = self.create_action_buttons([
                ("👁", "Detay", lambda checked, rid=data['id']: self._select_row_by_id(rid), "view"),
            ])
            self.table.setCellWidget(row_idx, 8, widget)
            self.table.setRowHeight(row_idx, 42)
    
    def _apply_search(self):
        """Arama filtresi"""
        search = self.search_input.text().lower().strip()
        
        if not search:
            self._display_data(self.all_data)
            return
        
        filtered = []
        for data in self.all_data:
            searchable = f"{data['irsaliye_no']} {data['musteri']} {data['plaka']}".lower()
            if search in searchable:
                filtered.append(data)
        
        self._display_data(filtered)
    
    def _show_context_menu(self, pos):
        """Sağ tık menüsü"""
        item = self.table.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {self.theme.get('bg_card')};
                color: {self.theme.get('text')};
                border: 1px solid {self.theme.get('border')};
            }}
            QMenu::item:selected {{
                background: {self.theme.get('primary')};
            }}
        """)
        
        menu.addAction("🖨️ Yazdır")
        menu.addAction("📋 Final Kalite Raporu")
        menu.addAction("✏️ Düzenle")
        menu.addSeparator()
        
        row = item.row()
        if row < len(self.all_data):
            durum = self.all_data[row]['durum']
            if durum == 'HAZIRLANDI':
                menu.addAction("🚚 Sevk Et")
            elif durum == 'SEVK_EDILDI':
                menu.addAction("✅ Teslim Edildi")
        
        menu.addSeparator()
        menu.addAction("❌ İptal Et")
        
        action = menu.exec_(self.table.mapToGlobal(pos))
        
        if action:
            text = action.text()
            if text == "🖨️ Yazdır":
                self._yazdir()
            elif text == "📋 Final Kalite Raporu":
                self._final_kalite_raporu()
            elif text == "✏️ Düzenle":
                self._duzenle()
            elif text == "🚚 Sevk Et":
                self._sevk_et()
            elif text == "✅ Teslim Edildi":
                self._teslim_et()
            elif text == "❌ İptal Et":
                self._iptal_et()
    
    def _select_row_by_id(self, irsaliye_id):
        """ID'ye göre satırı seç ve detay göster"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == str(irsaliye_id):
                self.table.selectRow(row)
                self._show_detail()
                return

    def _show_detail(self):
        """Seçili irsaliyenin detayını göster"""
        selected = self.table.selectedItems()
        if not selected:
            self._disable_buttons()
            return
        
        row = selected[0].row()
        irsaliye_id = int(self.table.item(row, 0).text())
        
        irsaliye = None
        for data in self.all_data:
            if data['id'] == irsaliye_id:
                irsaliye = data
                break
        
        if not irsaliye:
            return
        
        tarih_str = irsaliye['tarih'].strftime('%d.%m.%Y') if irsaliye['tarih'] else '-'
        
        self.detay_labels["İrsaliye No:"].setText(irsaliye['irsaliye_no'])
        self.detay_labels["Tarih:"].setText(tarih_str)
        self.detay_labels["Müşteri:"].setText(irsaliye['musteri'])
        self.detay_labels["Plaka:"].setText(irsaliye['plaka'] or '-')
        self.detay_labels["Şoför:"].setText(irsaliye['sofor'] or '-')
        self.detay_labels["Taşıyıcı:"].setText(irsaliye['tasiyici'] or '-')
        
        durum_text = {
            'HAZIRLANDI': '📦 Hazırlandı',
            'SEVK_EDILDI': '🚚 Sevk Edildi',
            'TESLIM_EDILDI': '✅ Teslim Edildi',
            'IPTAL': '❌ İptal'
        }.get(irsaliye['durum'], irsaliye['durum'])
        self.detay_labels["Durum:"].setText(durum_text)
        
        self._load_satirlar(irsaliye_id)
        
        self.secili_irsaliye = irsaliye
        self._update_buttons()
    
    def _disable_buttons(self):
        """Butonları devre dışı bırak"""
        self.yazdir_btn.setEnabled(False)
        self.duzenle_btn.setEnabled(False)
        self.sevk_btn.setEnabled(False)
        self.teslim_btn.setEnabled(False)
        self.iptal_btn.setEnabled(False)
        self.stok_iade_btn.setEnabled(False)
        self.zirve_btn.setEnabled(False)
        self.fkr_btn.setEnabled(False)
        self.secili_irsaliye = None
    
    def _update_buttons(self):
        """Butonları duruma göre güncelle"""
        if not self.secili_irsaliye:
            self._disable_buttons()
            return
        
        durum = self.secili_irsaliye.get('durum', '')
        
        self.yazdir_btn.setEnabled(True)
        self.duzenle_btn.setEnabled(durum not in ('IPTAL', 'TESLIM_EDILDI'))
        self.sevk_btn.setEnabled(durum == 'HAZIRLANDI')
        self.teslim_btn.setEnabled(durum == 'SEVK_EDILDI')
        self.iptal_btn.setEnabled(durum not in ('IPTAL', 'TESLIM_EDILDI'))
        # İptal edilmiş irsaliye → stok iade butonu aktif
        self.stok_iade_btn.setEnabled(durum == 'IPTAL')
        # Zirve aktarım: iptal olmayan irsaliyeler için
        self.zirve_btn.setEnabled(durum != 'IPTAL')
        # Final kalite raporu: satır varsa aktif
        self.fkr_btn.setEnabled(durum != 'IPTAL' and len(self.satirlar_data) > 0)
    
    def _load_satirlar(self, irsaliye_id):
        """İrsaliye satırlarını yükle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT
                    cis.lot_no,
                    COALESCE(ie.stok_kodu, u.urun_kodu, '') as stok_kodu,
                    COALESCE(ie.stok_adi, u.urun_adi, '') as stok_adi,
                    cis.miktar,
                    COALESCE(b.kod, 'AD') as birim,
                    cis.urun_id,
                    cis.is_emri_id
                FROM siparis.cikis_irsaliye_satirlar cis
                LEFT JOIN siparis.is_emirleri ie ON cis.is_emri_id = ie.id
                LEFT JOIN stok.urunler u ON cis.urun_id = u.id
                LEFT JOIN tanim.birimler b ON cis.birim_id = b.id
                WHERE cis.irsaliye_id = ?
                ORDER BY cis.satir_no
            """, (irsaliye_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            self.satirlar_table.setRowCount(0)
            self.satirlar_data = []
            
            toplam_miktar = 0
            
            for row in rows:
                satir = {
                    'lot_no': row[0] or '',
                    'stok_kodu': row[1] or '',
                    'stok_adi': row[2] or '',
                    'miktar': row[3] or 0,
                    'birim': row[4] or 'AD',
                    'urun_id': row[5],
                    'is_emri_id': row[6]
                }
                self.satirlar_data.append(satir)
                toplam_miktar += satir['miktar']
                
                row_idx = self.satirlar_table.rowCount()
                self.satirlar_table.insertRow(row_idx)
                
                self.satirlar_table.setItem(row_idx, 0, QTableWidgetItem(satir['stok_kodu']))
                self.satirlar_table.setItem(row_idx, 1, QTableWidgetItem(satir['stok_adi']))
                self.satirlar_table.setItem(row_idx, 2, QTableWidgetItem(satir['lot_no']))
                
                item = QTableWidgetItem(f"{satir['miktar']:,.0f}")
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.satirlar_table.setItem(row_idx, 3, item)
                
                self.satirlar_table.setItem(row_idx, 4, QTableWidgetItem(satir['birim']))
            
            self.toplam_label.setText(f"Toplam: {len(self.satirlar_data)} kalem, {toplam_miktar:,.0f} adet")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Satırlar yüklenemedi: {e}")
    
    def _duzenle(self):
        """İrsaliye düzenle"""
        if not self.secili_irsaliye:
            return
        
        dialog = IrsaliyeDuzenleDialog(self.theme, self.secili_irsaliye, self)
        if dialog.exec() == QDialog.Accepted:
            yeni_veri = dialog.get_data()
            satir_degisiklikler = dialog.get_satir_degisiklikler()
            self._kaydet_degisiklik(yeni_veri, satir_degisiklikler)
    
    def _kaydet_degisiklik(self, veri, satir_degisiklikler=None):
        """Değişiklikleri veritabanına kaydet"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE siparis.cikis_irsaliyeleri
                SET arac_plaka = ?,
                    sofor_adi = ?,
                    tasiyici_firma = ?,
                    durum = ?,
                    notlar = ?,
                    guncelleme_tarihi = GETDATE()
                WHERE id = ?
            """, (
                veri['plaka'],
                veri['sofor'],
                veri['tasiyici'],
                veri['durum'],
                veri['notlar'],
                veri['id']
            ))

            # Satır miktar değişiklikleri
            if satir_degisiklikler:
                for satir_id, yeni_miktar in satir_degisiklikler:
                    cursor.execute("""
                        UPDATE siparis.cikis_irsaliye_satirlar
                        SET miktar = ?
                        WHERE id = ?
                    """, (yeni_miktar, satir_id))

            conn.commit()
            conn.close()

            mesaj = "İrsaliye güncellendi!"
            if satir_degisiklikler:
                mesaj += f"\n{len(satir_degisiklikler)} satırda miktar düzeltildi."

            QMessageBox.information(self, "Başarılı", mesaj)
            self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güncelleme başarısız: {e}")
    
    def _sevk_et(self):
        """İrsaliyeyi sevk edildi olarak işaretle"""
        if not self.secili_irsaliye:
            return
        
        reply = QMessageBox.question(
            self, "Onay",
            f"İrsaliye: {self.secili_irsaliye['irsaliye_no']}\n\n"
            f"Bu irsaliyeyi SEVK EDİLDİ olarak işaretlemek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._durum_guncelle('SEVK_EDILDI')
    
    def _teslim_et(self):
        """İrsaliyeyi teslim edildi olarak işaretle"""
        if not self.secili_irsaliye:
            return
        
        reply = QMessageBox.question(
            self, "Onay",
            f"İrsaliye: {self.secili_irsaliye['irsaliye_no']}\n\n"
            f"Bu irsaliyeyi TESLİM EDİLDİ olarak işaretlemek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._durum_guncelle('TESLIM_EDILDI')
    
    def _iptal_et(self):
        """İrsaliyeyi iptal et"""
        if not self.secili_irsaliye:
            return
        
        reply = QMessageBox.warning(
            self, "⚠️ Dikkat",
            f"İrsaliye: {self.secili_irsaliye['irsaliye_no']}\n\n"
            f"Bu irsaliyeyi İPTAL etmek istiyor musunuz?\n\n"
            f"⚠️ Bu işlem geri alınamaz!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._durum_guncelle('IPTAL')
            self._stok_geri_yukle()

    def _stok_iade_yap(self):
        """Daha önce iptal edilmiş ama stoğu geri gelmemiş irsaliye için stok iadesi"""
        if not self.secili_irsaliye:
            return

        durum = self.secili_irsaliye.get('durum', '')
        if durum != 'IPTAL':
            QMessageBox.warning(self, "Uyarı", "Sadece İPTAL durumundaki irsaliyeler için stok iade yapılabilir!")
            return

        # İade öncesi kontrol: satırların stok durumunu göster
        kontrol_text = ""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            for satir in self.satirlar_data:
                lot_no = satir.get('lot_no', '')
                if lot_no:
                    cursor.execute("""
                        SELECT miktar, kalite_durumu, d.kod as depo_kod
                        FROM stok.stok_bakiye sb
                        LEFT JOIN tanim.depolar d ON sb.depo_id = d.id
                        WHERE sb.lot_no = ?
                    """, (lot_no,))
                    row = cursor.fetchone()
                    if row:
                        kontrol_text += f"  {lot_no}: miktar={row[0]:,.0f}, durum={row[1]}, depo={row[2]}\n"
                    else:
                        kontrol_text += f"  {lot_no}: kayıt yok (yeni oluşturulacak)\n"
            conn.close()
        except Exception:
            pass

        reply = QMessageBox.question(
            self, "Stok İade Onayı",
            f"İrsaliye: {self.secili_irsaliye['irsaliye_no']}\n\n"
            f"Mevcut stok durumu:\n{kontrol_text}\n"
            f"Bu irsaliyenin ürünleri SEVK deposuna geri yüklenecek\n"
            f"ve kalite durumu ONAYLANDI yapılacak.\n\n"
            f"Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._stok_geri_yukle()
            QMessageBox.information(
                self, "Başarılı",
                f"Stok iadesi tamamlandı!\n\n"
                f"İrsaliye: {self.secili_irsaliye['irsaliye_no']}\n"
                f"{len(self.satirlar_data)} kalem ürün SEVK deposuna iade edildi.\n\n"
                f"Sevkiyat listesinden kontrol edebilirsiniz."
            )

    def _zirve_aktar(self):
        """İrsaliyeyi Zirve Ticari'ye aktar"""
        if not self.secili_irsaliye:
            return

        irsaliye_id = self.secili_irsaliye['id']
        irsaliye_no = self.secili_irsaliye.get('irsaliye_no', '')

        # Önce aktarım durumunu kontrol et
        try:
            from core.zirve_entegrasyon import zirve_aktarim_kontrol, irsaliye_aktar
        except ImportError as e:
            QMessageBox.critical(self, "Hata", f"Zirve entegrasyon modülü yüklenemedi:\n{e}")
            return

        kontrol = zirve_aktarim_kontrol(irsaliye_id)
        if kontrol.get('aktarildi'):
            QMessageBox.warning(
                self, "Zaten Aktarılmış",
                f"Bu irsaliye zaten Zirve'ye aktarılmış!\n\n"
                f"Zirve SIRANO: {kontrol.get('zirve_sirano')}\n"
                f"Aktarım Tarihi: {kontrol.get('tarih')}"
            )
            return

        # Onay al
        reply = QMessageBox.question(
            self, "Zirve'ye Aktarım Onayı",
            f"İrsaliye: {irsaliye_no}\n"
            f"Müşteri: {self.secili_irsaliye.get('musteri', '')}\n"
            f"Satır: {len(self.satirlar_data)} kalem\n\n"
            f"Bu irsaliye Zirve Ticari'ye (ATLAS_KATAFOREZ_2026T) aktarılacak.\n\n"
            f"Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Aktarımı yap
        sonuc = irsaliye_aktar(irsaliye_id)

        if sonuc.basarili:
            QMessageBox.information(self, "Zirve Aktarım Başarılı", sonuc.mesaj)
        else:
            QMessageBox.critical(
                self, "Zirve Aktarım Hatası",
                f"İrsaliye Zirve'ye aktarılamadı!\n\n{sonuc.hata}"
            )

    def _durum_guncelle(self, yeni_durum):
        """Durum güncelle"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE siparis.cikis_irsaliyeleri
                SET durum = ?,
                    guncelleme_tarihi = GETDATE()
                WHERE id = ?
            """, (yeni_durum, self.secili_irsaliye['id']))
            
            conn.commit()
            conn.close()
            
            durum_text = {
                'SEVK_EDILDI': 'Sevk Edildi',
                'TESLIM_EDILDI': 'Teslim Edildi',
                'IPTAL': 'İptal Edildi'
            }.get(yeni_durum, yeni_durum)
            
            QMessageBox.information(self, "Başarılı", f"İrsaliye durumu: {durum_text}")
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Durum güncellenemedi: {e}")
    
    def _stok_geri_yukle(self):
        """İptal edilen irsaliyenin stoklarını SEVK deposuna geri yükle

        stok_cikis miktar=0 olunca kalite_durumu='SEVK_EDILDI' yapar.
        stok_giris ise mevcut kayıtta sadece miktar günceller, kalite_durumu'na dokunmaz.
        Bu yüzden stok_giris + kalite_durumu UPDATE birlikte yapılmalı.
        """
        if not self.secili_irsaliye:
            return

        try:
            from core.hareket_motoru import HareketMotoru

            conn = get_db_connection()
            cursor = conn.cursor()
            motor = HareketMotoru(conn)

            # SEVK deposu ID'sini bul
            cursor.execute("""
                SELECT TOP 1 id FROM tanim.depolar
                WHERE kod IN ('SEV-01', 'SEVK', 'SEV', 'MAMUL') AND aktif_mi = 1
                ORDER BY id
            """)
            sevk_depo_row = cursor.fetchone()
            sevk_depo_id = sevk_depo_row[0] if sevk_depo_row else None

            for satir in self.satirlar_data:
                lot_no = satir.get('lot_no')
                miktar = satir.get('miktar', 0)
                urun_id = satir.get('urun_id') or 1
                is_emri_id = satir.get('is_emri_id')

                if lot_no and miktar > 0:
                    # Stok girişi yap (miktar iade)
                    sonuc = motor.stok_giris(
                        urun_id=urun_id,
                        miktar=miktar,
                        lot_no=lot_no,
                        depo_id=sevk_depo_id,
                        kalite_durumu='ONAYLANDI',
                        aciklama=f"İrsaliye iptal - stok iadesi ({self.secili_irsaliye['irsaliye_no']})"
                    )

                    # stok_giris mevcut kayıtta kalite_durumu güncellemez,
                    # stok_cikis SEVK_EDILDI yapmış olabilir → elle düzelt
                    cursor.execute("""
                        UPDATE stok.stok_bakiye
                        SET kalite_durumu = 'ONAYLANDI',
                            son_hareket_tarihi = GETDATE()
                        WHERE lot_no = ? AND miktar > 0
                    """, (lot_no,))

                    if sonuc.basarili:
                        print(f"✓ Stok iadesi: {lot_no}, {miktar} adet → SEVK deposu (kalite=ONAYLANDI)")
                    else:
                        print(f"✗ Stok iadesi hatası: {sonuc.mesaj}")

                # İş emri durumunu SEVK_EDILDI → ONAYLANDI geri al
                if is_emri_id:
                    cursor.execute("""
                        UPDATE siparis.is_emirleri
                        SET durum = 'ONAYLANDI',
                            guncelleme_tarihi = GETDATE()
                        WHERE id = ? AND durum = 'SEVK_EDILDI'
                    """, (is_emri_id,))

            conn.commit()
            conn.close()

            print(f"✓ İrsaliye iptal stok iadesi tamamlandı: {self.secili_irsaliye['irsaliye_no']}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Uyarı", f"Stok iadesi sırasında hata: {e}")
    
    def _yazdir(self):
        """İrsaliye yazdır"""
        if not self.secili_irsaliye:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT adres, vergi_no, vergi_dairesi
                FROM musteri.cariler
                WHERE id = ?
            """, (self.secili_irsaliye.get('cari_id'),))
            row = cursor.fetchone()
            if row:
                self.secili_irsaliye['adres'] = row[0] or '-'
                self.secili_irsaliye['vergi_no'] = f"{row[2] or ''} - {row[1] or ''}"
            conn.close()
        except Exception:
            pass
        
        dialog = IrsaliyeOnizlemeDialog(
            self.theme,
            self.secili_irsaliye,
            self.satirlar_data,
            self
        )
        dialog.exec()

    def _final_kalite_raporu(self):
        """Secili irsaliyedeki her lot icin Final Kalite Raporu PDF olustur."""
        if not self.secili_irsaliye or not self.satirlar_data:
            QMessageBox.warning(self, "Uyari", "Once bir irsaliye secin.")
            return

        irsaliye_id = self.secili_irsaliye.get('id')
        if not irsaliye_id:
            return

        try:
            from utils.final_kalite_raporu_pdf import batch_final_kalite_raporu
            sonuclar = batch_final_kalite_raporu(irsaliye_id)

            if not sonuclar:
                QMessageBox.warning(self, "Uyari", "Rapor olusturulacak lot bulunamadi.")
                return

            basarili = [(lot, path) for lot, path in sonuclar if not str(path).startswith("HATA")]
            hatali = [(lot, path) for lot, path in sonuclar if str(path).startswith("HATA")]

            mesaj = f"{len(basarili)} adet Final Kalite Raporu olusturuldu.\n\n"
            for lot, path in basarili:
                mesaj += f"  {lot}\n"

            if hatali:
                mesaj += f"\n{len(hatali)} lot icin rapor olusturulamadi:\n"
                for lot, err in hatali:
                    mesaj += f"  {lot}: {err}\n"

            QMessageBox.information(self, "Final Kalite Raporu", mesaj)

            # Ilk basarili PDF'i ac
            if basarili:
                os.startfile(basarili[0][1])

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Rapor olusturulurken hata:\n{e}")
